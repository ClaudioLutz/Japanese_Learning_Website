"""Bundle 'JLPT N5 Komplett' anlegen und alle veroeffentlichten N5-Lessons einhaengen.

Idempotent: Course wird per Title gefunden oder neu erstellt; bereits eingehaengte
Lessons werden uebersprungen. Der Course bleibt is_published=False (taucht nicht
in /courses-Listing oder Sitemap auf), ist aber is_purchasable=True — Zugriff
erfolgt ueber die Verkaufsseite /n5-bundle und das bestehende CoursePurchase-System.

Usage:
    venv/Scripts/python scripts/setup_n5_bundle.py            # legt an / haelt aktuell
    venv/Scripts/python scripts/setup_n5_bundle.py --dry-run  # nur Vorschau, kein Commit
"""
from __future__ import annotations

import sys
from pathlib import Path

# Windows-Konsolen mit cp1252 stolpern ueber japanische Zeichen — auf UTF-8 zwingen
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app, db  # noqa: E402
from app.models import Course, Lesson, LessonCategory  # noqa: E402


BUNDLE_TITLE = "JLPT N5 Komplett"
BUNDLE_DESCRIPTION = (
    "Alle veroeffentlichten N5-Lektionen als Bundle. Lifetime-Zugriff auf "
    "Vokabeln, Kanji, Grammatik und Schreibsystem nach offiziellen JLPT-N5-"
    "Listen. Spaetere N5-Lektionen werden automatisch freigeschaltet."
)
REGULAR_PRICE_CHF = 14.90  # statischer Anker; dynamischer Preis kommt aus bundle_service.py


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    app = create_app()
    with app.app_context():
        # Course finden oder anlegen
        bundle = db.session.query(Course).filter_by(title=BUNDLE_TITLE).first()
        created = False
        if bundle is None:
            bundle = Course(
                title=BUNDLE_TITLE,
                description=BUNDLE_DESCRIPTION,
                is_published=False,       # NICHT in /courses oder Sitemap
                is_purchasable=True,
                price=REGULAR_PRICE_CHF,
            )
            if not dry_run:
                db.session.add(bundle)
                db.session.flush()
            created = True

        # Alle veroeffentlichten N5-Lessons (ueber LessonCategory.jlpt_level)
        n5_lessons = (
            db.session.query(Lesson)
            .join(LessonCategory, Lesson.category_id == LessonCategory.id)
            .filter(LessonCategory.jlpt_level == 5)
            .filter(Lesson.is_published.is_(True))
            .order_by(Lesson.id)
            .all()
        )

        existing_ids = {lesson.id for lesson in bundle.lessons} if not created else set()
        added: list[Lesson] = []
        skipped: list[Lesson] = []
        for lesson in n5_lessons:
            if lesson.id in existing_ids:
                skipped.append(lesson)
                continue
            if not dry_run:
                bundle.lessons.append(lesson)
            added.append(lesson)

        if not dry_run:
            db.session.commit()

        # Report
        print("=" * 80)
        print(f"  Setup N5-Bundle ({'DRY-RUN' if dry_run else 'COMMIT'})")
        print("=" * 80)
        print(f"  Course        : '{BUNDLE_TITLE}'")
        print(f"  Course-ID     : {bundle.id if not (dry_run and created) else '(neu, dry-run)'}")
        print(f"  Status        : {'NEU angelegt' if created else 'bestand bereits'}")
        print(f"  Preis (Anker) : CHF {REGULAR_PRICE_CHF:.2f}")
        print(f"  is_published  : {bundle.is_published}  (bewusst False — nur via /n5-bundle)")
        print(f"  is_purchasable: {bundle.is_purchasable}")
        print()
        print(f"  N5-Lessons gesamt    : {len(n5_lessons)}")
        print(f"  Hinzugefuegt         : {len(added)}")
        print(f"  Schon im Bundle      : {len(skipped)}")
        if added:
            print()
            print("  Neu hinzugefuegt:")
            for lesson in added:
                print(f"    [{lesson.id:3d}] {lesson.title}")
        print("=" * 80)
        if not n5_lessons:
            print("  WARNUNG: Keine veroeffentlichten N5-Lessons gefunden — Bundle ist leer.")
            print("  Pruefe LessonCategory.jlpt_level=5 und Lesson.is_published=True.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
