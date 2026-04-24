"""Generate vocab images (DALL-E) for all 22 vocab entries of Lesson 143.

Stores PNGs under app/static/uploads/vocab_generated/ and updates
vocabulary.image_url to the resulting relative URL.

Skips entries that already have a non-NULL image_url (idempotent).
"""
import hashlib
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app, db
from app.models import LessonContent, Vocabulary
from app.ai_services import AILessonContentGenerator

LESSON_ID = 143
OUT_DIR = PROJECT_ROOT / "app" / "static" / "uploads" / "vocab_generated"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def main() -> int:
    app = create_app()
    with app.app_context():
        gen = AILessonContentGenerator()
        if not gen.openai_client:
            print("[FEHLER] OpenAI client nicht initialisiert (OPENAI_API_KEY?)")
            return 1

        vocab_rows = (
            db.session.query(Vocabulary)
            .join(LessonContent, LessonContent.content_id == Vocabulary.id)
            .filter(LessonContent.lesson_id == LESSON_ID)
            .filter(LessonContent.content_type == "vocabulary")
            .all()
        )
        print(f"[INFO] {len(vocab_rows)} Vokabeln fuer Lesson {LESSON_ID}")

        for i, v in enumerate(vocab_rows, start=1):
            if v.image_url:
                print(f"  [{i:2d}/{len(vocab_rows)}] SKIP {v.word} -> bereits {v.image_url[:40]}")
                continue

            meaning = v.meaning or v.meaning_de or v.word
            print(f"  [{i:2d}/{len(vocab_rows)}] GEN  {v.word} / {meaning[:40]} ...")
            result = gen.generate_vocabulary_image(word=v.word, meaning=meaning)
            if not result or "image_bytes" not in result:
                err = (result or {}).get("error", "unbekannt")
                print(f"      [FEHLER] {err}")
                continue

            hash_suffix = hashlib.md5(v.word.encode()).hexdigest()[:8]
            filename = f"vocab_{v.id}_{hash_suffix}.png"
            out_path = OUT_DIR / filename
            out_path.write_bytes(result["image_bytes"])
            # Pfad relativ zu UPLOAD_FOLDER (app/static/uploads/) — das Template
            # ruft url_for('routes.uploaded_file', filename=image_url) auf.
            url = f"vocab_generated/{filename}"
            v.image_url = url
            db.session.commit()
            print(f"      OK -> {url}")

        print("[DONE]")
        return 0


if __name__ == "__main__":
    sys.exit(main())
