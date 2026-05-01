"""Recompute progress_percentage / is_completed fuer alle UserLessonProgress.

Hintergrund: Bis 2026-05-01 zaehlte `update_progress_percentage` ALLE
LessonContent-Items, auch UI-unsichtbare 'audio'-Eintraege auf Pages mit
dialog_slideshow. Solche Items konnten nie als erledigt markiert werden
und blockierten den 100%-Abschluss (User landete bei z.B. 96%).

Nach dem Code-Fix (Lesson.progress_visible_content_items) muss bestehender
Progress neu berechnet werden, sonst bleibt er auf den alten Werten.

Aufruf:
    python -m scripts.recompute_lesson_progress            # Dry-run, nur Report
    python -m scripts.recompute_lesson_progress --apply    # tatsaechlich schreiben

Das Skript NIEMALS Progress senken — es kann eine Lektion nur von
unter 100% auf 100% (oder 96 -> 100) heben, niemals umgekehrt.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import create_app, db  # noqa: E402
from app.models import UserLessonProgress  # noqa: E402


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true', help='Schreibt Aenderungen in die DB')
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        all_progress = UserLessonProgress.query.order_by(
            UserLessonProgress.user_id, UserLessonProgress.lesson_id
        ).all()

        bumps: list[tuple[int, int, str, int, int, bool, bool]] = []  # (uid, lid, title, before, after, was_completed, now_completed)
        unchanged = 0

        for p in all_progress:
            before_pct = p.progress_percentage or 0
            before_completed = bool(p.is_completed)

            # Zentrale Logik anwenden — aktualisiert p in-place.
            p.update_progress_percentage()

            after_pct = p.progress_percentage or 0
            after_completed = bool(p.is_completed)

            if before_pct != after_pct or before_completed != after_completed:
                # Schutz: niemals SENKEN. Wenn nach Recompute prozentual weniger
                # rauskommt, lassen wir den alten Wert stehen.
                if after_pct < before_pct:
                    p.progress_percentage = before_pct
                    p.is_completed = before_completed
                    continue
                bumps.append((
                    p.user_id, p.lesson_id,
                    (p.lesson.title if p.lesson else '?')[:60],
                    before_pct, after_pct,
                    before_completed, after_completed,
                ))
            else:
                unchanged += 1

        if args.apply:
            db.session.commit()
        else:
            db.session.rollback()

        mode = 'APPLY' if args.apply else 'DRY-RUN'
        print(f"=== Recompute Lesson Progress ({mode}) ===")
        print(f"Total: {len(all_progress)} | unveraendert: {unchanged} | angehoben: {len(bumps)}")

        if bumps:
            print()
            print("Aenderungen (User, Lesson, %, Completed):")
            for uid, lid, title, b_pct, a_pct, b_done, a_done in bumps[:50]:
                done_change = ''
                if not b_done and a_done:
                    done_change = '  -> NEU completed'
                print(f"  user={uid} lesson={lid:>4} {b_pct:>3}% -> {a_pct:>3}%{done_change}  | {title}")
            if len(bumps) > 50:
                print(f"  ... +{len(bumps) - 50} weitere")

        return 0


if __name__ == '__main__':
    sys.exit(main())
