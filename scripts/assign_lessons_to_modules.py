"""Best-Effort-Zuordnung bestehender Lessons zu N5-Modulen per Title-Keyword-Match.

Idempotent: setzt category_id nur wenn aktuell None ODER --force gesetzt.
Zeigt am Ende eine Mapping-Tabelle und welche Lessons unzugewiesen bleiben.

Usage:
    venv/Scripts/python scripts/assign_lessons_to_modules.py            # nur unzugewiesene
    venv/Scripts/python scripts/assign_lessons_to_modules.py --force    # ueberschreibt
    venv/Scripts/python scripts/assign_lessons_to_modules.py --dry-run  # nur Vorschau
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app, db  # noqa: E402
from app.models import Lesson, LessonCategory  # noqa: E402


# Reihenfolge ist wichtig: spezifischere Keywords zuerst.
KEYWORD_TO_SLUG: list[tuple[str, str]] = [
    # Schreibsystem
    ("hiragana", "n5-hiragana"),
    ("katakana", "n5-katakana"),
    # Zahlen / Zeit
    ("zahlen", "n5-zahlen-zeit"),
    ("uhrzeit", "n5-zahlen-zeit"),
    ("datum", "n5-zahlen-zeit"),
    ("alter", "n5-zahlen-zeit"),
    ("telefon", "n5-zahlen-zeit"),
    ("wochentag", "n5-zahlen-zeit"),
    ("monat", "n5-zahlen-zeit"),
    ("time", "n5-zahlen-zeit"),
    ("schedule", "n5-zahlen-zeit"),
    ("daily", "n5-zahlen-zeit"),
    ("tagesablauf", "n5-zahlen-zeit"),
    # Begruessung / Hoeflichkeit
    ("begrüss", "n5-begruessung-hoeflichkeit"),
    ("begruess", "n5-begruessung-hoeflichkeit"),
    ("greetings", "n5-begruessung-hoeflichkeit"),
    ("höflich", "n5-begruessung-hoeflichkeit"),
    ("hoeflich", "n5-begruessung-hoeflichkeit"),
    ("vorstell", "n5-begruessung-hoeflichkeit"),
    ("introduction", "n5-begruessung-hoeflichkeit"),
    # Familie / Personen
    ("famil", "n5-familie-personen"),
    ("person", "n5-familie-personen"),
    ("beruf", "n5-familie-personen"),
    # Alltag / Essen
    ("essen", "n5-alltag-essen"),
    ("food", "n5-alltag-essen"),
    ("restaurant", "n5-alltag-essen"),
    ("alltag", "n5-alltag-essen"),
    ("lebensmittel", "n5-alltag-essen"),
    ("getränk", "n5-alltag-essen"),
    ("getraenk", "n5-alltag-essen"),
    # Reise / Ort
    ("reise", "n5-reise-ort"),
    ("transport", "n5-reise-ort"),
    ("verkehr", "n5-reise-ort"),
    ("bahnhof", "n5-reise-ort"),
    ("station", "n5-reise-ort"),
    ("ort", "n5-reise-ort"),
    ("place", "n5-reise-ort"),
    # Reise: Bewegungs-Verben (gehen/kommen) sind Reise-orientiert
    ("going", "n5-reise-ort"),
    ("coming", "n5-reise-ort"),
    ("gehen und kommen", "n5-reise-ort"),
    # Grammatik / Erste Saetze
    ("grammatik", "n5-erste-saetze"),
    ("grammar", "n5-erste-saetze"),
    ("partikel", "n5-erste-saetze"),
    ("verb", "n5-erste-saetze"),
    ("desu", "n5-erste-saetze"),
    ("masu", "n5-erste-saetze"),
    ("satz", "n5-erste-saetze"),
    ("sentence", "n5-erste-saetze"),
    ("demonstrativ", "n5-erste-saetze"),
    ("demonstrative", "n5-erste-saetze"),
    ("pronoun", "n5-erste-saetze"),
    ("pronomen", "n5-erste-saetze"),
]


def best_module_for_lesson(title: str) -> str | None:
    """Liefert besten passenden Modul-Slug per Substring-Match. None wenn nichts passt."""
    title_lower = title.lower()
    for keyword, slug in KEYWORD_TO_SLUG:
        if keyword in title_lower:
            return slug
    return None


def main():
    force = "--force" in sys.argv
    dry_run = "--dry-run" in sys.argv
    app = create_app()
    with app.app_context():
        # Slug → Category-ID Map
        slug_to_id: dict[str, int] = {}
        for cat in db.session.query(LessonCategory).filter(
            LessonCategory.slug.isnot(None)
        ).all():
            slug_to_id[cat.slug] = cat.id

        # Alle N5-Lessons (difficulty_level 1 oder 2 = N5)
        lessons = (
            db.session.query(Lesson)
            .filter(Lesson.difficulty_level <= 2)
            .order_by(Lesson.id)
            .all()
        )

        assigned = 0
        skipped_existing = 0
        unmatched: list[Lesson] = []
        report: list[tuple[Lesson, str | None, str]] = []

        for lesson in lessons:
            current_cat_id = lesson.category_id
            target_slug = best_module_for_lesson(lesson.title)
            target_id = slug_to_id.get(target_slug) if target_slug else None

            if target_id is None:
                unmatched.append(lesson)
                report.append((lesson, None, "kein Match"))
                continue

            if current_cat_id and not force:
                skipped_existing += 1
                # Wenn bereits einem N5-Modul zugewiesen, OK
                current_cat = db.session.get(LessonCategory, current_cat_id)
                report.append((lesson, target_slug, f"unveraendert ({current_cat.slug or current_cat.name})"))
                continue

            if not dry_run:
                lesson.category_id = target_id
            assigned += 1
            report.append((lesson, target_slug, "ZUGEWIESEN"))

        if not dry_run:
            db.session.commit()

        print("=" * 80)
        print(f"  Lesson → Modul Auto-Zuordnung "
              f"({'DRY-RUN' if dry_run else ('FORCE' if force else 'NORMAL')})")
        print("=" * 80)
        for lesson, slug, status in report:
            print(f"  [{lesson.id:3d}] {lesson.title[:55]:55s}  → {slug or '-':28s} [{status}]")
        print()
        print(f"  Zugewiesen / aktualisiert : {assigned}")
        print(f"  Uebersprungen (bestand)   : {skipped_existing}")
        print(f"  Ohne Match                : {len(unmatched)}")
        if unmatched:
            print()
            print("  Lessons ohne Match — bitte manuell im Admin-Panel zuordnen:")
            for lesson in unmatched:
                print(f"    [{lesson.id:3d}] {lesson.title}")
        print("=" * 80)


if __name__ == "__main__":
    main()
