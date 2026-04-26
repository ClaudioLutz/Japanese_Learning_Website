"""Setzt das Pricing aller veroeffentlichten N5-Lessons nach Duolingo-Style:
die ersten 2 nach order_index pro Modul bleiben gratis, der Rest wird paid.

Idempotent: kann beliebig oft laufen. Bei `--reset` werden ALLE N5-Lessons
wieder auf price=0.0, is_purchasable=False gesetzt (zur Migration zurueck).

Pricing-Default kommt aus app/services/bundle_service.REGULAR_PRICE_CHF, damit
das Lesson-Pricing identisch zum Bundle-Anker bleibt — wer einzeln kauft, zahlt
denselben Preis wie das Bundle. Das macht das Bundle automatisch attraktiver
(20+ Lessons fuer den Preis von einer).

Usage:
    venv/Scripts/python scripts/apply_n5_pricing_duolingo.py            # apply
    venv/Scripts/python scripts/apply_n5_pricing_duolingo.py --dry-run  # preview
    venv/Scripts/python scripts/apply_n5_pricing_duolingo.py --reset    # alles zurueck
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app import create_app, db  # noqa: E402
from app.models import LessonCategory  # noqa: E402
from app.services.bundle_service import REGULAR_PRICE_CHF  # noqa: E402

JLPT_LEVEL = 5
FREE_LESSONS_PER_MODULE = 1  # Duolingo-Style: nur erste 1 pro Modul gratis


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    reset = "--reset" in sys.argv
    app = create_app()
    with app.app_context():
        cats = (
            db.session.query(LessonCategory)
            .filter(LessonCategory.jlpt_level == JLPT_LEVEL)
            .order_by(LessonCategory.display_order)
            .all()
        )

        report: list[tuple[str, int, str, str, str]] = []
        free_count = 0
        paid_count = 0

        for cat in cats:
            published = sorted(
                [lesson for lesson in cat.lessons if lesson.is_published],
                key=lambda x: x.order_index,
            )
            for i, lesson in enumerate(published, start=1):
                if reset:
                    new_price = 0.0
                    new_purchasable = False
                else:
                    if i <= FREE_LESSONS_PER_MODULE:
                        new_price = 0.0
                        new_purchasable = False
                    else:
                        new_price = REGULAR_PRICE_CHF
                        new_purchasable = True

                changed = (lesson.price != new_price) or (lesson.is_purchasable != new_purchasable)

                if changed and not dry_run:
                    lesson.price = new_price
                    lesson.is_purchasable = new_purchasable

                tag = "FREE" if new_price == 0.0 else "PAID"
                if new_price == 0.0:
                    free_count += 1
                else:
                    paid_count += 1
                report.append((
                    cat.slug or cat.name, lesson.id, lesson.title[:55], tag,
                    "GEAENDERT" if changed else "unveraendert",
                ))

        if not dry_run:
            db.session.commit()

        mode = "RESET" if reset else ("DRY-RUN" if dry_run else "COMMIT")
        print("=" * 90)
        print(f"  N5-Pricing Duolingo-Style ({mode})")
        print(f"  Free pro Modul: {FREE_LESSONS_PER_MODULE}, Paid-Preis: CHF {REGULAR_PRICE_CHF:.2f}")
        print("=" * 90)
        last_module = None
        for module, lid, title, tag, changed in report:
            if module != last_module:
                print(f"\n[{module}]")
                last_module = module
            print(f"  {tag:4s} [{lid:3d}] {title:55s}  {changed}")
        print("=" * 90)
        print(f"  Total: {free_count} FREE, {paid_count} PAID")
        print("=" * 90)
        return 0


if __name__ == "__main__":
    sys.exit(main())
