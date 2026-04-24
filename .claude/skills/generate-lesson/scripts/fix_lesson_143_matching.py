"""Fix Matching-Options in Lesson 143.

Hintergrund: Template lesson_view.html:744ff erwartet
  option.option_text = LEFT side (prompt, z.B. japanisches Wort)
  option.feedback    = RIGHT side (answer, z.B. Uebersetzung)
  is_correct         = true fuer alle (Paar-Match)

Die Claude-generierten Optionen haben stattdessen das Format
  option_text = "JP | DE", feedback = NULL
— dadurch zeigt das Dropdown nur 'None'.

Dieses Skript splittet alle Matching-Options von Lesson 143 am ersten
' | ', schreibt den linken Teil in option_text und den rechten in feedback.
Idempotent: Eintraege, bei denen feedback schon gesetzt ist, bleiben.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app, db
from app.models import LessonContent, QuizQuestion, QuizOption


def main() -> int:
    lesson_id = 143
    app = create_app()
    with app.app_context():
        options = (
            db.session.query(QuizOption)
            .join(QuizQuestion, QuizQuestion.id == QuizOption.question_id)
            .join(LessonContent, LessonContent.id == QuizQuestion.lesson_content_id)
            .filter(LessonContent.lesson_id == lesson_id)
            .filter(QuizQuestion.question_type == "matching")
            .all()
        )
        print(f"[INFO] {len(options)} Matching-Optionen in Lesson {lesson_id}")

        fixed = 0
        for o in options:
            if o.feedback:
                continue  # already split
            if " | " not in (o.option_text or ""):
                print(f"  [WARN] Option {o.id} hat kein ' | ' — skip: {o.option_text!r}")
                continue
            left, _, right = o.option_text.partition(" | ")
            o.option_text = left.strip()
            o.feedback = right.strip()
            fixed += 1
            print(f"  Option {o.id}: '{left.strip()}'  ->  '{right.strip()}'")

        db.session.commit()
        print(f"[OK] {fixed} Optionen gesplittet.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
