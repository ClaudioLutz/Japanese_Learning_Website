"""Korrigiert verfrueht abgeschlossene Quiz-Items in UserLessonProgress.

Hintergrund (Bug 2026-06-14): Das Frontend markierte ein ganzes Quiz-Content-Item
schon nach der ERSTEN richtig/aufgebraucht beantworteten Frage als erledigt. Ein
mehrfragiges Quiz (z.B. 14-Fragen-Uebung) galt damit nach einer Antwort als
fertig -> die Lektion sprang verfrueht auf 100% und wurde faelschlich als
abgeschlossen gefuehrt.

Der Code-Fix (LessonContent.is_quiz_fully_resolved + content_completed) verhindert
das kuenftig. Dieses Skript korrigiert EINMALIG die bereits verfaelschten
Bestandsdaten:

  Fuer jede UserLessonProgress-Zeile wird jedes als erledigt markierte
  INTERAKTIVE Quiz-Item geprueft. Ist NICHT jede seiner Fragen aufgeloest
  (korrekt beantwortet ODER alle Versuche aufgebraucht), wird die Markierung
  entfernt und progress_percentage / is_completed neu berechnet.

Dies ist der EINZIGE legitime Fall, in dem Progress gesenkt werden darf — die
bisherige 100% waren faktisch falsch (User hatte das Quiz nicht durchgearbeitet).

Aufruf (auf hp-ubuntu gegen die Produktions-DB):
    sudo docker compose exec -T web python -m scripts.correct_premature_quiz_completion
    sudo docker compose exec -T web python -m scripts.correct_premature_quiz_completion --apply

Vorher Backup ziehen:  sudo /usr/local/bin/jpl-db-backup.sh

Die Aufloesungs-Logik ist hier bewusst INLINE dupliziert (statt
LessonContent.is_quiz_fully_resolved zu importieren), damit das Skript auch gegen
eine noch nicht deployte App-Version korrekt laeuft.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import create_app, db  # noqa: E402
from app.models import (  # noqa: E402
    LessonContent,
    QuizQuestion,
    UserLessonProgress,
    UserQuizAnswer,
)


def _quiz_fully_resolved(content: LessonContent, user_id: int) -> bool:
    """True, wenn jede Frage dieses Quiz-Items fuer den User aufgeloest ist
    (korrekt ODER Versuche aufgebraucht). Ohne Fragen: True."""
    question_ids = [q.id for q in QuizQuestion.query.filter_by(
        lesson_content_id=content.id).all()]
    if not question_ids:
        return True
    max_attempts = content.max_attempts or 0  # 0/None => unbegrenzt
    answers = {
        a.question_id: a
        for a in UserQuizAnswer.query.filter(
            UserQuizAnswer.user_id == user_id,
            UserQuizAnswer.question_id.in_(question_ids),
        ).all()
    }
    for qid in question_ids:
        a = answers.get(qid)
        if a is None:
            return False
        if a.is_correct:
            continue
        if max_attempts and a.attempts >= max_attempts:
            continue
        return False
    return True


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

        # (uid, lid, title, [content_ids unmarked], before_pct, after_pct, before_done, after_done)
        corrections: list[tuple] = []
        unchanged = 0

        for p in all_progress:
            cp = p.get_content_progress()
            if not cp:
                unchanged += 1
                continue

            before_pct = p.progress_percentage or 0
            before_done = bool(p.is_completed)

            unmarked: list[int] = []
            for cid_str, done in list(cp.items()):
                if not done:
                    continue
                try:
                    cid = int(cid_str)
                except (TypeError, ValueError):
                    continue
                content = LessonContent.query.get(cid)
                # Nur interaktive Quiz-Items pruefen (passive Items bleiben unberuehrt)
                if not content or not content.is_interactive:
                    continue
                if not _quiz_fully_resolved(content, p.user_id):
                    cp.pop(cid_str, None)
                    unmarked.append(cid)

            if not unmarked:
                unchanged += 1
                continue

            p.set_content_progress(cp)
            p.update_progress_percentage()
            # update_progress_percentage hebt is_completed nur an. Verfrueht gesetztes
            # is_completed muss bei nun <100% zurueckgenommen werden.
            if (p.progress_percentage or 0) < 100 and p.is_completed:
                p.is_completed = False
                p.completed_at = None

            corrections.append((
                p.user_id, p.lesson_id,
                (p.lesson.title if p.lesson else '?')[:55],
                unmarked, before_pct, p.progress_percentage or 0,
                before_done, bool(p.is_completed),
            ))

        if args.apply:
            db.session.commit()
        else:
            db.session.rollback()

        mode = 'APPLY' if args.apply else 'DRY-RUN'
        print(f"=== Korrektur verfruehter Quiz-Abschluesse ({mode}) ===")
        print(f"Total: {len(all_progress)} | unveraendert: {unchanged} | korrigiert: {len(corrections)}")
        if corrections:
            print()
            print("Korrekturen (User, Lesson, %, Completed, entmarkierte Quiz-Items):")
            for uid, lid, title, items, b_pct, a_pct, b_done, a_done in corrections[:80]:
                done_change = ''
                if b_done and not a_done:
                    done_change = '  -> NICHT mehr completed'
                print(f"  user={uid} lesson={lid:>4} {b_pct:>3}% -> {a_pct:>3}%{done_change}"
                      f"  items={items}  | {title}")
            if len(corrections) > 80:
                print(f"  ... +{len(corrections) - 80} weitere")

        return 0


if __name__ == '__main__':
    sys.exit(main())
