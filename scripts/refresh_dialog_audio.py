"""Frischt das Dialog-Slideshow-Audio der angegebenen Lektionen aus dem AKTUELLEN
(korrigierten) Slide-JSON auf — überschreibt nur die MP3-Dateien, JSON + Bilder
bleiben unangetastet. Nötig, weil Textkorrekturen die vorgerenderten Slide-Audios
stale gemacht haben. Nutzt die je Slide gespeicherte Cloud-TTS-Voice (gleicher
Stack wie die Original-Generierung).

Usage (im Container): python refresh_dialog_audio.py 157 164 177 178
"""
import base64
import json
import os
import sys
from pathlib import Path

import requests
from app import create_app, db
from sqlalchemy import text

app = create_app()


def tts_mp3(jp: str, voice: str, api_key: str, speed: float = 0.85) -> bytes | None:
    lang = "-".join(voice.split("-")[:2])  # ja-JP-Neural2-B -> ja-JP
    payload = {
        "input": {"text": jp},
        "voice": {"languageCode": lang, "name": voice},
        "audioConfig": {"audioEncoding": "MP3", "speakingRate": speed},
    }
    r = requests.post(
        f"https://texttospeech.googleapis.com/v1/text:synthesize?key={api_key}",
        json=payload, timeout=30)
    if r.status_code != 200:
        print(f"      [TTS {r.status_code}] {r.text[:120]}")
        return None
    b64 = r.json().get("audioContent")
    return base64.b64decode(b64) if b64 else None


def main(lesson_ids):
    with app.app_context():
        api_key = (app.config.get("GOOGLE_TTS_API_KEY") or os.environ.get("GOOGLE_TTS_API_KEY")
                   or os.environ.get("GOOGLE_API_KEY"))
        static = Path(app.static_folder)
        total_ok = total_fail = 0
        for lid in lesson_ids:
            rows = db.session.execute(text(
                "SELECT id, content_text FROM lesson_content "
                "WHERE lesson_id=:l AND content_type='dialog_slideshow'"), {"l": lid}).fetchall()
            for cid, ct in rows:
                slides = json.loads(ct)
                slides = slides if isinstance(slides, list) else slides.get("slides", [])
                ok = fail = 0
                for s in slides:
                    jp, voice, audio = s.get("jp"), s.get("voice"), s.get("audio")
                    if not (jp and voice and audio):
                        continue
                    disk = static / audio.lstrip("/")
                    mp3 = tts_mp3(jp, voice, api_key)
                    if mp3:
                        disk.parent.mkdir(parents=True, exist_ok=True)
                        disk.write_bytes(mp3)
                        ok += 1
                    else:
                        fail += 1
                        print(f"      FAIL L{lid} {audio}: {jp[:30]}")
                print(f"L{lid} content {cid}: {ok} Audios neu, {fail} Fehler")
                total_ok += ok
                total_fail += fail
        print(f"FERTIG: {total_ok} Audios aufgefrischt, {total_fail} Fehler")


if __name__ == "__main__":
    ids = [int(x) for x in sys.argv[1:]] or [157, 164, 177, 178]
    main(ids)
