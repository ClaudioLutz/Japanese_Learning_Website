#!/usr/bin/env python3
"""Generiert Hiragana-Einzelaussprache-MP3s mit Google Chirp 3 HD.

Lesson 146 ("N5 Hiragana 1 — Vokale, K-Reihe und S-Reihe") deckt Kana-IDs 1-15
ab (あ-そ). Skript erzeugt pro Mora eine MP3, laedt sie in den GCS-Bucket
`jpl-website-assets/kana/hiragana/<romaji>.mp3` und setzt `kana.example_sound_url`.

    python scripts/generate_hiragana_audio.py            # IDs 1-15 (Lesson 1)
    python scripts/generate_hiragana_audio.py --all      # alle 46 Basis-Hiragana
    python scripts/generate_hiragana_audio.py --dry-run  # nur generieren, kein DB-Update
"""
from __future__ import annotations

import argparse
import io
import os
import sys
from pathlib import Path

if sys.platform == "win32" and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

# DB-URL fuer App-Import
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://app_user:JapaneseApp2025!@localhost:5432/japanese_learning",
)
os.environ.setdefault("PAYMENT_PROVIDER", "mock")
os.environ.setdefault("MOCK_PAYMENTS_ENABLED", "true")

from google.cloud import texttospeech
from google.cloud import storage

from app import create_app, db
from app.models import Kana

VOICE_NAME = "ja-JP-Chirp3-HD-Leda"   # weiblich, klar, neutral
SPEAKING_RATE = 0.85
GCS_BUCKET = os.environ.get("GCS_BUCKET_NAME", "jpl-website-assets")
GCS_PREFIX = "kana/hiragana"
LOCAL_OUT = PROJECT_ROOT / "app" / "static" / "uploads" / "kana" / "hiragana"


def get_tts_client() -> texttospeech.TextToSpeechClient:
    api_key = os.environ.get("GOOGLE_TTS_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if api_key:
        return texttospeech.TextToSpeechClient(client_options={"api_key": api_key})
    return texttospeech.TextToSpeechClient()


def synthesize(client: texttospeech.TextToSpeechClient, text: str) -> bytes:
    voice = texttospeech.VoiceSelectionParams(language_code="ja-JP", name=VOICE_NAME)
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=SPEAKING_RATE,
    )
    resp = client.synthesize_speech(
        input=texttospeech.SynthesisInput(text=text),
        voice=voice,
        audio_config=audio_config,
    )
    return resp.audio_content


def upload_to_gcs(local_path: Path, dest_blob: str) -> str | None:
    try:
        bucket = storage.Client().bucket(GCS_BUCKET)
        blob = bucket.blob(dest_blob)
        blob.upload_from_filename(str(local_path), content_type="audio/mpeg")
        return f"https://storage.googleapis.com/{GCS_BUCKET}/{dest_blob}"
    except Exception as e:
        print(f"  GCS-Upload fehlgeschlagen ({dest_blob}): {e}")
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="Alle 46 Basis-Hiragana (IDs 1-46)")
    parser.add_argument("--dry-run", action="store_true", help="Nur Audio generieren, kein GCS/DB")
    parser.add_argument("--skip-gcs", action="store_true", help="Kein GCS-Upload")
    args = parser.parse_args()

    LOCAL_OUT.mkdir(parents=True, exist_ok=True)

    id_range = (1, 46) if args.all else (1, 15)
    app = create_app()
    with app.app_context():
        kana_rows = (
            Kana.query.filter(Kana.type == "hiragana")
            .filter(Kana.id >= id_range[0])
            .filter(Kana.id <= id_range[1])
            .order_by(Kana.id)
            .all()
        )

        print(f"Generiere {len(kana_rows)} Hiragana mit {VOICE_NAME} (rate={SPEAKING_RATE})")
        print(f"Lokal: {LOCAL_OUT}")
        if not args.skip_gcs and not args.dry_run:
            print(f"GCS:   gs://{GCS_BUCKET}/{GCS_PREFIX}/")
        print("-" * 60)

        client = get_tts_client()
        updates: list[tuple[int, str]] = []

        for k in kana_rows:
            local_file = LOCAL_OUT / f"{k.romanization}.mp3"
            try:
                audio = synthesize(client, k.character)
                local_file.write_bytes(audio)
                size_kb = local_file.stat().st_size // 1024
                print(f"  [{k.id:3d}] {k.character} ({k.romanization:>3s}) -> {local_file.name} ({size_kb} KB)")
            except Exception as e:
                print(f"  [{k.id:3d}] {k.character} FEHLER: {e}")
                continue

            if args.dry_run:
                continue

            url: str | None = None
            if not args.skip_gcs:
                dest = f"{GCS_PREFIX}/{k.romanization}.mp3"
                url = upload_to_gcs(local_file, dest)
            if url is None:
                url = f"/static/uploads/kana/hiragana/{k.romanization}.mp3"
            updates.append((k.id, url))

        if args.dry_run:
            print("\nDRY-RUN: keine DB-Updates.")
            return

        for kid, url in updates:
            db.session.execute(
                db.text("UPDATE kana SET example_sound_url = :u WHERE id = :i"),
                {"u": url, "i": kid},
            )
        db.session.commit()
        print(f"\n{len(updates)} kana.example_sound_url aktualisiert.")


if __name__ == "__main__":
    main()
