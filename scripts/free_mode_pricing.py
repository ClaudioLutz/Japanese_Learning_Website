#!/usr/bin/env python
"""Free-Mode-Pricing: Lektions-/Kurs-Preise nullen (alles gratis) + reversibel.

Begleitet das FREE_MODE-Flag (app/__init__.py). Das Flag deckt nur die berechnete
Bezahl-Schicht (Bundle-Verkauf/-Hinweise, hartkodierte CTAs, Rechtstexte, Sitemap);
die eigentliche Lesson-/Course-Freischaltung laeuft ueber price==0 in der DB —
genau das setzt dieses Skript.

WICHTIG: alle Schreibzugriffe laufen ueber das ORM (db.session), damit der
SQLAlchemy-Event `update_lesson_type_on_price_change` feuert und lesson_type
konsistent ('free' bei price==0) bleibt. Raw-SQL wuerde lesson_type stale lassen.

Reversibilitaet: `apply` schreibt VOR dem Nullen automatisch einen Snapshot
(id, price, is_purchasable) je Lesson UND Course. `restore` spielt ihn zurueck.

Verwendung (auf dem Prod-Host hp-ubuntu mit erreichbarer DB):
    # 1. Vorschau (read-only): zeigt, was genullt wuerde, schreibt Snapshot
    python scripts/free_mode_pricing.py apply --dry-run
    # 2. Anwenden (schreibt Snapshot + nullt Preise)
    python scripts/free_mode_pricing.py apply --commit
    # Snapshot separat ziehen:
    python scripts/free_mode_pricing.py snapshot --out scripts/data/monetization_snapshot.json
    # Spaeter Monetarisierung zurueckholen:
    python scripts/free_mode_pricing.py restore --in <snapshot>.json --commit

Hinweis (.env zeigt im Container auf Host 'db'): vom Host aus mit Override laufen:
    DATABASE_URL="postgresql://app_user:...@localhost:5432/japanese_learning" \
        python scripts/free_mode_pricing.py apply --dry-run
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime

# Projekt-Root importierbar machen (scripts/ liegt unter dem Root)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db  # noqa: E402
from app.models import Course, Lesson  # noqa: E402


def _default_snapshot_path() -> str:
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, f"monetization_snapshot_{ts}.json")


def _collect_snapshot() -> dict:
    """Liest (id, price, is_purchasable) je Lesson + Course. lesson_type bewusst
    NICHT mitgespeichert — der Event leitet es beim Restore aus price ab."""
    lessons = [
        {"id": lesson.id, "price": lesson.price, "is_purchasable": bool(lesson.is_purchasable)}
        for lesson in db.session.query(Lesson).order_by(Lesson.id).all()
    ]
    courses = [
        {"id": course.id, "price": course.price, "is_purchasable": bool(course.is_purchasable)}
        for course in db.session.query(Course).order_by(Course.id).all()
    ]
    return {
        "created_at": datetime.utcnow().isoformat(),
        "lessons": lessons,
        "courses": courses,
    }


def cmd_snapshot(args) -> int:
    out = args.out or _default_snapshot_path()
    snap = _collect_snapshot()
    with open(out, "w", encoding="utf-8") as f:
        json.dump(snap, f, ensure_ascii=False, indent=2)
    paid_lessons = sum(1 for x in snap["lessons"] if (x["price"] or 0) > 0 or x["is_purchasable"])
    paid_courses = sum(1 for x in snap["courses"] if (x["price"] or 0) > 0 or x["is_purchasable"])
    print(f"Snapshot geschrieben: {out}")
    print(f"  Lessons gesamt: {len(snap['lessons'])} (davon kostenpflichtig: {paid_lessons})")
    print(f"  Courses gesamt: {len(snap['courses'])} (davon kostenpflichtig: {paid_courses})")
    return 0


def cmd_apply(args) -> int:
    commit = args.commit
    # Immer zuerst Snapshot sichern (auch im Dry-Run) — Reversibilitaet first.
    snap_path = args.snapshot or _default_snapshot_path()
    snap = _collect_snapshot()
    with open(snap_path, "w", encoding="utf-8") as f:
        json.dump(snap, f, ensure_ascii=False, indent=2)
    print(f"Snapshot gesichert: {snap_path}")

    lessons = db.session.query(Lesson).all()
    courses = db.session.query(Course).all()

    to_null_lessons = [x for x in lessons if (x.price or 0) > 0 or x.is_purchasable]
    to_null_courses = [x for x in courses if (x.price or 0) > 0 or x.is_purchasable]

    print(f"\n== {'ANWENDEN' if commit else 'DRY-RUN'} ==")
    print(f"Lessons, die genullt werden (price=0, is_purchasable=False): {len(to_null_lessons)}")
    for lesson in to_null_lessons:
        print(f"  Lesson {lesson.id}: price {lesson.price} -> 0, is_purchasable {lesson.is_purchasable} -> False  ({lesson.title!r})")
    print(f"Courses, die genullt werden: {len(to_null_courses)}")
    for course in to_null_courses:
        print(f"  Course {course.id}: price {course.price} -> 0, is_purchasable {course.is_purchasable} -> False  ({course.title!r})")

    if not commit:
        print("\nDry-Run — keine Aenderung geschrieben. Mit --commit anwenden.")
        return 0

    for lesson in to_null_lessons:
        lesson.price = 0.0
        lesson.is_purchasable = False
    for course in to_null_courses:
        course.price = 0.0
        course.is_purchasable = False
    db.session.commit()
    print(f"\nFertig: {len(to_null_lessons)} Lessons + {len(to_null_courses)} Courses auf gratis gesetzt (per ORM, lesson_type-Event gefeuert).")
    print(f"Reversibel via: python scripts/free_mode_pricing.py restore --in {snap_path} --commit")
    return 0


def cmd_restore(args) -> int:
    with open(args.infile, "r", encoding="utf-8") as f:
        snap = json.load(f)
    commit = args.commit

    lessons_by_id = {x.id: x for x in db.session.query(Lesson).all()}
    courses_by_id = {x.id: x for x in db.session.query(Course).all()}

    changed = 0
    missing = 0
    for rec in snap.get("lessons", []):
        lesson = lessons_by_id.get(rec["id"])
        if lesson is None:
            missing += 1
            continue
        if lesson.price != rec["price"] or bool(lesson.is_purchasable) != bool(rec["is_purchasable"]):
            print(f"  Lesson {lesson.id}: price {lesson.price} -> {rec['price']}, is_purchasable {lesson.is_purchasable} -> {rec['is_purchasable']}")
            if commit:
                lesson.price = rec["price"]
                lesson.is_purchasable = rec["is_purchasable"]
            changed += 1
    for rec in snap.get("courses", []):
        course = courses_by_id.get(rec["id"])
        if course is None:
            missing += 1
            continue
        if course.price != rec["price"] or bool(course.is_purchasable) != bool(rec["is_purchasable"]):
            print(f"  Course {course.id}: price {course.price} -> {rec['price']}, is_purchasable {course.is_purchasable} -> {rec['is_purchasable']}")
            if commit:
                course.price = rec["price"]
                course.is_purchasable = rec["is_purchasable"]
            changed += 1

    if commit:
        db.session.commit()
        print(f"\nRestore angewendet: {changed} Datensaetze zurueckgesetzt ({missing} aus Snapshot nicht mehr in DB).")
        print("Vergiss nicht: FREE_MODE in der .env wieder auf false setzen + Container neu starten.")
    else:
        print(f"\nDry-Run — {changed} Datensaetze wuerden zurueckgesetzt ({missing} fehlen in DB). Mit --commit anwenden.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Free-Mode-Pricing: Preise nullen + reversibel restaurieren.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_snap = sub.add_parser("snapshot", help="Aktuelle Preise als JSON sichern (read-only)")
    p_snap.add_argument("--out", default=None, help="Zielpfad (Default: scripts/data/monetization_snapshot_<ts>.json)")
    p_snap.set_defaults(func=cmd_snapshot)

    p_apply = sub.add_parser("apply", help="Alle Preise auf 0 + is_purchasable=False (schreibt vorher Snapshot)")
    p_apply.add_argument("--commit", action="store_true", help="Tatsaechlich schreiben (sonst Dry-Run)")
    p_apply.add_argument("--snapshot", default=None, help="Snapshot-Zielpfad (Default: auto mit Zeitstempel)")
    p_apply.set_defaults(func=cmd_apply)

    p_restore = sub.add_parser("restore", help="Preise aus Snapshot zurueckspielen")
    p_restore.add_argument("--in", dest="infile", required=True, help="Snapshot-JSON")
    p_restore.add_argument("--commit", action="store_true", help="Tatsaechlich schreiben (sonst Dry-Run)")
    p_restore.set_defaults(func=cmd_restore)

    args = parser.parse_args()
    app = create_app()
    with app.app_context():
        return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
