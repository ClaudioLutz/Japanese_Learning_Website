"""Korrigiert augmented_html-URLs: bevorzugt .wav (Gemini) ueber .mp3 (Chirp-Fallback).

Hintergrund: durch Gemini-Quota-Hits wurden viele Audios als Chirp-MP3-Fallback
generiert, aber dieselben Hashes haben oft auch eine Gemini-WAV aus frueheren
Laeufen. Dieses Skript scannt alle augmented_html und ersetzt .mp3-URLs durch
.wav-URLs wenn die WAV-Datei existiert (= Gemini-Studio-Qualitaet).
"""
from __future__ import annotations
import os, sys, re
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://app_user:JapaneseApp2025!@localhost:5432/japanese_learning",
)
os.environ.setdefault("PAYMENT_PROVIDER", "mock")

from sqlalchemy.orm.attributes import flag_modified
from app import create_app, db
from app.models import LessonContent

AUDIO_DIR = PROJECT_ROOT / "app" / "static" / "uploads" / "lessons" / "inline_audio"

# Findet z.B. /static/uploads/lessons/inline_audio/<hash>.mp3
URL_RE = re.compile(r'(/static/uploads/lessons/inline_audio/[a-f0-9]+)\.mp3')


def main():
    app = create_app()
    with app.app_context():
        rows = (
            db.session.query(LessonContent)
            .filter(LessonContent.content_type == "text")
            .all()
        )

        changed_lcs = 0
        changed_urls = 0
        for lc in rows:
            details = lc.ai_generation_details or {}
            html = details.get("augmented_html")
            if not html:
                continue

            def replace(match):
                nonlocal changed_urls
                base = match.group(1)
                hash_ = base.split("/")[-1]
                wav_file = AUDIO_DIR / f"{hash_}.wav"
                if wav_file.exists():
                    changed_urls += 1
                    return f"{base}.wav"
                return match.group(0)

            new_html = URL_RE.sub(replace, html)
            if new_html != html:
                details["augmented_html"] = new_html
                lc.ai_generation_details = details
                # JSONB-Mutation explizit markieren, sonst commit'd SQLAlchemy nichts
                flag_modified(lc, "ai_generation_details")
                changed_lcs += 1

        db.session.commit()
        print(f"=== {changed_lcs} LessonContents aktualisiert, {changed_urls} URLs auf .wav umgestellt ===")


if __name__ == "__main__":
    main()
