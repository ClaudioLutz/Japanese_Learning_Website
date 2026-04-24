"""Generate TTS audio for the dialog page of a lesson (Google Cloud TTS).

Usage:
  python gen_conversation_audio.py <lesson_id>

Findet die Dialog-Page (page_type='normal', Title beginnt mit 'Dialog' oder
enthaelt 'Konversation'), extrahiert die japanischen Zeilen (alles vor
'(romaji)' / '-> Translation'), rendert EINE MP3 via Google Cloud TTS mit
600ms-Pausen zwischen Sprechern, legt ein LessonContent mit
content_type='audio' auf order_index=1 vor dem Text-Content an.

Idempotent: wenn die Dialog-Page bereits ein audio-Content hat, Abbruch.
"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app, db
from app.models import Lesson, LessonPage, LessonContent
from app.ai_services import GoogleCloudTTS


def find_dialog_page(lesson_id: int) -> LessonPage | None:
    pages = (
        db.session.query(LessonPage)
        .filter_by(lesson_id=lesson_id)
        .order_by(LessonPage.page_number)
        .all()
    )
    for p in pages:
        title = (p.title or "").lower()
        if "dialog" in title or "konversation" in title or "gespräch" in title or "conversation" in title:
            return p
    return None


def extract_japanese_lines(content_text: str) -> list[str]:
    """Extract only the Japanese dialogue lines from MNN-style plaintext."""
    lines = []
    for raw in content_text.splitlines():
        line = raw.strip()
        if not line:
            continue
        # Skip romaji block (in parens) and translation block (starts with ->)
        if line.startswith("(") or line.startswith("->"):
            continue
        # Expect "Speaker: 日本語" — split off speaker label
        if ":" in line:
            _, _, jp = line.partition(":")
            jp = jp.strip()
            if jp:
                lines.append(jp)
        else:
            lines.append(line)
    return lines


def build_ssml(jp_lines: list[str], speed: float = 0.85) -> str:
    # Escape XML specials
    def esc(s: str) -> str:
        return (
            s.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

    pause = '<break time="700ms"/>'
    body = pause.join(f'<s>{esc(line)}</s>' for line in jp_lines)
    return f'<speak><prosody rate="{speed}">{body}</prosody></speak>'


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python gen_conversation_audio.py <lesson_id>")
        return 2
    lesson_id = int(sys.argv[1])

    app = create_app()
    with app.app_context():
        lesson = db.session.query(Lesson).get(lesson_id)
        if not lesson:
            print(f"[FEHLER] Lesson {lesson_id} nicht gefunden")
            return 1

        dialog_page = find_dialog_page(lesson_id)
        if not dialog_page:
            print(f"[FEHLER] Keine Dialog-Page in Lesson {lesson_id} gefunden.")
            return 1

        # Idempotency check
        existing_audio = (
            db.session.query(LessonContent)
            .filter_by(
                lesson_id=lesson_id,
                page_number=dialog_page.page_number,
                content_type="audio",
            )
            .first()
        )
        if existing_audio:
            print(f"[SKIP] Audio existiert bereits: LC {existing_audio.id} ({existing_audio.file_path})")
            return 0

        # Find the text content with the dialog
        text_lc = (
            db.session.query(LessonContent)
            .filter_by(
                lesson_id=lesson_id,
                page_number=dialog_page.page_number,
                content_type="text",
            )
            .order_by(LessonContent.order_index)
            .first()
        )
        if not text_lc or not text_lc.content_text:
            print(f"[FEHLER] Kein Dialog-Text auf Page {dialog_page.page_number}.")
            return 1

        jp_lines = extract_japanese_lines(text_lc.content_text)
        if not jp_lines:
            print("[FEHLER] Keine japanischen Zeilen extrahiert.")
            return 1
        print(f"[INFO] {len(jp_lines)} japanische Zeilen extrahiert")
        for line in jp_lines[:3]:
            print(f"       {line}")

        # Generate TTS MP3
        tts = GoogleCloudTTS()
        if not tts.client:
            print("[FEHLER] Google TTS nicht konfiguriert (GOOGLE_API_KEY fehlt).")
            return 1

        out_dir = PROJECT_ROOT / "app" / "static" / "uploads" / "lessons" / "audio" / f"lesson_{lesson_id}"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "conversation.mp3"

        ssml = build_ssml(jp_lines)
        result = tts.generate_audio(
            text=ssml, output_path=str(out_path), voice="female", speed=0.85, use_ssml=True
        )
        if "error" in result:
            print(f"[FEHLER] TTS: {result['error']}")
            return 1

        print(f"[OK] MP3: {out_path} ({result['size_bytes']} bytes)")

        # Create LessonContent row. Relative file_path (like MNN-Import).
        rel_path = f"lessons/audio/lesson_{lesson_id}/conversation.mp3"

        # Move existing text content to order_index=2 if needed
        text_lc.order_index = 2

        audio_lc = LessonContent(
            lesson_id=lesson_id,
            content_type="audio",
            title="Konversation (Audio)",
            page_number=dialog_page.page_number,
            order_index=1,
            file_path=rel_path,
            file_type="audio/mpeg",
            file_size=result.get("size_bytes"),
            media_url=f"/static/uploads/{rel_path}",
            generated_by_ai=True,
            ai_generation_details={
                "generator": "google_cloud_tts",
                "voice": result.get("voice"),
                "speed": result.get("speed"),
                "lines": len(jp_lines),
            },
        )
        db.session.add(audio_lc)
        db.session.commit()
        print(f"[OK] LessonContent {audio_lc.id} angelegt.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
