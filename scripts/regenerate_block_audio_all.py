"""Bulk-Wrapper: ruft gen_text_audio.py fuer jede published Lesson auf.

Renderiert die Block-Player-Audios mit der neuen Gemini-Pipeline.
Idempotent ueber den `tts_generator` Marker — Lessons die bereits auf
"gemini_ja_neural2_de_split" stehen werden uebersprungen.
"""
from __future__ import annotations
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://app_user:JapaneseApp2025!@localhost:5432/japanese_learning",
)
os.environ.setdefault("PAYMENT_PROVIDER", "mock")

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from app import create_app, db
from app.models import Lesson, LessonContent

GEN_SCRIPT = PROJECT_ROOT / ".claude" / "skills" / "generate-lesson" / "scripts" / "gen_text_audio.py"
NEW_GENERATOR_TAG = "gemini_ja_neural2_de_split"


def main():
    app = create_app()
    with app.app_context():
        lessons = (
            db.session.query(Lesson)
            .filter_by(is_published=True)
            .order_by(Lesson.id)
            .all()
        )

        # Filter: nur Lessons die NICHT bereits Gemini-Pipeline durchliefen
        todo = []
        skipped = 0
        for lesson in lessons:
            text_blocks = (
                db.session.query(LessonContent)
                .filter_by(lesson_id=lesson.id, content_type="text")
                .all()
            )
            if not text_blocks:
                continue
            already_done = all(
                (lc.ai_generation_details or {}).get("tts_generator") == NEW_GENERATOR_TAG
                for lc in text_blocks
                if (lc.content_text or "").strip() and len(lc.content_text or "") >= 80
            )
            if already_done:
                skipped += 1
                print(f"[SKIP Lesson {lesson.id}] {lesson.title} — schon Gemini-Pipeline")
                continue
            todo.append(lesson)

        print(f"\n=== {len(todo)} Lessons zu rendern, {skipped} bereits Gemini ===\n")

        for i, lesson in enumerate(todo, start=1):
            print(f"\n[{i}/{len(todo)}] === Lesson {lesson.id}: {lesson.title} ===")
            try:
                result = subprocess.run(
                    [sys.executable, str(GEN_SCRIPT), str(lesson.id), "--force"],
                    cwd=str(PROJECT_ROOT),
                    timeout=900,  # 15 min hart-cap pro Lesson
                )
                if result.returncode != 0:
                    print(f"  [FEHLER] gen_text_audio Exit {result.returncode}")
            except subprocess.TimeoutExpired:
                print(f"  [TIMEOUT] Lesson {lesson.id} nach 15 min abgebrochen")
            except Exception as e:
                print(f"  [EXC] {e}")

        print(f"\n=== ALLE {len(todo)} Lessons fertig ===")


if __name__ == "__main__":
    main()
