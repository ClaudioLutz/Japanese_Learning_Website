"""Apply: neue Quiz-Aufgaben (Maßnahme 4 — Übungen diversifizieren).

Fügt von Claude verfasste und geprüfte Aufgaben in bestehende Quiz-Träger
(``lesson_content`` vom Typ ``text``) ein:

* ``matchingQuestions`` — ``matching``-Aufgaben (Theme-Lektionen: Wort↔Bedeutung;
  Kana-Lektionen: Kana-Lesedrill Wort↔Bedeutung). Jedes Paar wird als
  ``quiz_option`` mit ``option_text`` (JP) und ``feedback`` (DE) gespeichert,
  ``is_correct=True`` (Konvention des bestehenden matching-Schemas).
* ``trueFalseQuestions`` — ``true_false``-Aufgaben mit zwei Optionen
  (Wahr/Falsch), ``is_correct`` gemäß ``answer``.

SICHERHEIT (Produktions-DB!):
  * Default DRY-RUN; ``--apply`` schreibt nach Auto-Backup unter
    ``backups/exercises/`` (protokolliert eingefügte Fragen für Rückbau).
  * Nur Content-Tabellen (quiz_question, quiz_option). Keine Nutzerdaten.
  * Idempotent: existiert auf dem Träger bereits eine Frage mit identischem
    ``question_text``, wird übersprungen.
  * ``order_index`` wird je Träger live aus dem aktuellen Maximum fortgezählt.

Aufruf (auf hp-ubuntu, DATABASE_URL erreichbar):
    python -m scripts.apply_exercises            # Dry-run
    python -m scripts.apply_exercises --apply     # schreiben
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import create_app, db  # noqa: E402
from app.models import LessonContent, QuizQuestion, QuizOption  # noqa: E402

DEFAULT_DATA = ROOT / "scripts" / "data" / "exercises_changeset.json"
BACKUP_DIR = ROOT / "backups" / "exercises"


def validate(changeset: dict) -> list[str]:
    errs: list[str] = []
    for q in changeset.get("matchingQuestions", []):
        if not q.get("question_text"):
            errs.append(f"matching carrier={q.get('carrier_lc')}: question_text leer")
        pairs = q.get("pairs", [])
        if len(pairs) < 3:
            errs.append(f"matching carrier={q.get('carrier_lc')}: < 3 Paare")
        for p in pairs:
            if not p.get("jp") or not p.get("de"):
                errs.append(f"matching carrier={q.get('carrier_lc')}: leeres Paar {p!r}")
    for q in changeset.get("trueFalseQuestions", []):
        if not q.get("question_text"):
            errs.append(f"true_false carrier={q.get('carrier_lc')}: question_text leer")
        if not isinstance(q.get("answer"), bool):
            errs.append(f"true_false carrier={q.get('carrier_lc')}: answer kein bool")
    return errs


def write_backup(payload: dict) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = BACKUP_DIR / f"exercises_backup_{stamp}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Schreibt Aenderungen (sonst Dry-run)")
    parser.add_argument("--data", type=str, default=str(DEFAULT_DATA))
    args = parser.parse_args()

    data_path = Path(args.data)
    if not data_path.exists():
        print(f"FEHLER: Datendatei nicht gefunden: {data_path}")
        return 1
    changeset = json.loads(data_path.read_text(encoding="utf-8"))

    errs = validate(changeset)
    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"=== Übungen diversifizieren ({mode}) ===")
    if errs:
        print(f"VALIDIERUNG fehlgeschlagen ({len(errs)}) — nichts geschrieben:")
        for e in errs:
            print(f"  ! {e}")
        return 2
    print("Validierung ok.")

    app = create_app()
    with app.app_context():
        report = {"matching": 0, "true_false": 0, "options": 0, "skipped": 0, "no_carrier": 0}
        added = []
        # laufendes order_index-Maximum je Traeger
        maxord: dict[int, int] = {}

        def next_order(carrier: int) -> int:
            if carrier not in maxord:
                cur = (db.session.query(db.func.max(QuizQuestion.order_index))
                       .filter(QuizQuestion.lesson_content_id == carrier).scalar())
                maxord[carrier] = cur or 0
            maxord[carrier] += 1
            return maxord[carrier]

        def exists(carrier: int, qtext: str) -> bool:
            return db.session.query(QuizQuestion.id).filter(
                QuizQuestion.lesson_content_id == carrier,
                QuizQuestion.question_text == qtext).first() is not None

        def carrier_ok(carrier: int) -> bool:
            return LessonContent.query.get(carrier) is not None

        # 1) matching (Theme + Kana-Drills)
        for q in changeset.get("matchingQuestions", []):
            carrier = q["carrier_lc"]
            if not carrier_ok(carrier):
                print(f"  ? matching: Traeger {carrier} fehlt")
                report["no_carrier"] += 1
                continue
            if exists(carrier, q["question_text"]):
                report["skipped"] += 1
                continue
            report["matching"] += 1
            added.append({"carrier_lc": carrier, "lesson_id": q.get("lesson_id"),
                          "type": "matching", "kind": q.get("kind"), "question_text": q["question_text"]})
            if args.apply:
                qq = QuizQuestion(
                    lesson_content_id=carrier, question_type="matching",
                    question_text=q["question_text"], difficulty_level=1, points=10,
                    order_index=next_order(carrier))
                db.session.add(qq)
                db.session.flush()
                for i, p in enumerate(q["pairs"], start=1):
                    db.session.add(QuizOption(question_id=qq.id, option_text=p["jp"],
                                              feedback=p["de"], is_correct=True, order_index=i))
                    report["options"] += 1
            else:
                report["options"] += len(q["pairs"])

        # 2) true_false
        for q in changeset.get("trueFalseQuestions", []):
            carrier = q["carrier_lc"]
            if not carrier_ok(carrier):
                print(f"  ? true_false: Traeger {carrier} fehlt")
                report["no_carrier"] += 1
                continue
            if exists(carrier, q["question_text"]):
                report["skipped"] += 1
                continue
            report["true_false"] += 1
            added.append({"carrier_lc": carrier, "lesson_id": q.get("lesson_id"),
                          "type": "true_false", "question_text": q["question_text"], "answer": q["answer"]})
            if args.apply:
                qq = QuizQuestion(
                    lesson_content_id=carrier, question_type="true_false",
                    question_text=q["question_text"], explanation=q.get("explanation"),
                    difficulty_level=1, points=10, order_index=next_order(carrier))
                db.session.add(qq)
                db.session.flush()
                db.session.add(QuizOption(question_id=qq.id, option_text="Wahr",
                                          is_correct=bool(q["answer"]), order_index=1))
                db.session.add(QuizOption(question_id=qq.id, option_text="Falsch",
                                          is_correct=not bool(q["answer"]), order_index=2))
                report["options"] += 2
            else:
                report["options"] += 2

        if args.apply:
            backup_path = write_backup({"added": added})
            db.session.commit()
            print(f"Backup (eingefuegte Fragen) geschrieben: {backup_path}")
            print("GESCHRIEBEN.")
        else:
            print("DRY-RUN — nichts geschrieben.")

        print("\nZusammenfassung:")
        for key, val in report.items():
            print(f"  {key:12}: {val}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
