"""Wärmt den /api/tts-Chirp-Cache für Vokabel-Audio vor.

Karten (Lesson-View) und SRS-Wiederholung sprechen Vokabeln per Klick über
``POST /api/tts`` (Default-Modell **Chirp**, ``speed=0.85``). Antworten werden
unter ``app/static/cache/tts/<md5>.mp3`` gecacht. Dieses Skript erzeugt genau
diese Cache-Dateien VORAB, damit auch der erste Klick sofort spielt.

Damit die Cache-Schlüssel exakt mit den Laufzeit-Anfragen übereinstimmen, wird
dieselbe Endpoint-Logik wiederverwendet (``_maybe_spell_out_kana_row`` +
identische md5-Formel + dieselbe Chirp-Stimme aus ``_TTS_VOICES``).

Vorgewärmt werden je Vokabel (aus PUBLISHED-Lektionen) der Beispielsatz
``example_sentence_japanese`` UND das Wort ``word`` (deckt Karten + SRS ab).

SICHERHEIT: nur Lesen aus DB + Schreiben von Cache-Dateien. Keine DB-Writes.

Aufruf (auf hp-ubuntu, GOOGLE_TTS_API_KEY/GOOGLE_API_KEY + DB erreichbar):
    python -m scripts.prewarm_vocab_tts            # Dry-run (zaehlt nur)
    python -m scripts.prewarm_vocab_tts --apply    # synthetisiert + cached
    python -m scripts.prewarm_vocab_tts --apply --limit 20
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import os
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import create_app  # noqa: E402
from app.models import Vocabulary, Lesson, LessonContent  # noqa: E402
from app.routes import (  # noqa: E402
    _TTS_VOICES,
    _CHIRP_VOICE_PREFIX,
    _contains_japanese,
    _maybe_spell_out_kana_row,
)

SPEED = 0.85
LANG = "ja"


def cache_key_for(text: str, voice_name: str) -> str:
    """Identisch zur Endpoint-Formel (Chirp-Pfad)."""
    transformed = _maybe_spell_out_kana_row(text, model="chirp")
    return hashlib.md5(
        f"{LANG}_chirp_{voice_name}_{SPEED}_{transformed}".encode("utf-8")
    ).hexdigest()


def collect_texts(app) -> list[str]:
    with app.app_context():
        rows = (
            Vocabulary.query
            .join(LessonContent, (LessonContent.content_id == Vocabulary.id)
                  & (LessonContent.content_type == "vocabulary"))
            .join(Lesson, (Lesson.id == LessonContent.lesson_id)
                  & (Lesson.is_published.is_(True)))
            .with_entities(Vocabulary.word, Vocabulary.example_sentence_japanese)
            .distinct()
            .all()
        )
    texts: list[str] = []
    seen: set[str] = set()
    for word, example in rows:
        for raw in (example, word):
            t = (raw or "").strip()
            if not t or len(t) > 500 or not _contains_japanese(t):
                continue
            if t in seen:
                continue
            seen.add(t)
            texts.append(t)
    return texts


def synthesize_chirp(text: str, voice: dict, api_key: str) -> bytes:
    payload = {
        "input": {"text": text},
        "voice": voice,
        "audioConfig": {"audioEncoding": "MP3", "speakingRate": SPEED},
    }
    resp = requests.post(
        f"https://texttospeech.googleapis.com/v1/text:synthesize?key={api_key}",
        json=payload, timeout=15,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"TTS HTTP {resp.status_code}: {resp.text[:160]}")
    return base64.b64decode(resp.json().get("audioContent", ""))


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Synthetisiert + cached (sonst Dry-run)")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--sleep", type=float, default=0.05, help="Pause zwischen Calls (s)")
    args = parser.parse_args()

    app = create_app()
    voice = _TTS_VOICES.get(LANG)
    if not voice or _CHIRP_VOICE_PREFIX not in voice["name"]:
        print(f"FEHLER: ja-Stimme ist nicht Chirp ({voice}). Abbruch.")
        return 1
    voice_name = voice["name"]

    cache_dir = Path(app.static_folder) / "cache" / "tts"
    cache_dir.mkdir(parents=True, exist_ok=True)

    texts = collect_texts(app)
    if args.limit:
        texts = texts[: args.limit]

    todo = []
    already = 0
    for t in texts:
        cf = cache_dir / f"{cache_key_for(t, voice_name)}.mp3"
        if cf.exists():
            already += 1
        else:
            todo.append((t, cf))

    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"=== Vokabel-TTS-Cache vorwaermen ({mode}) ===")
    print(f"Stimme: {voice_name} | Texte gesamt: {len(texts)} | "
          f"bereits gecacht: {already} | zu synthetisieren: {len(todo)}")
    print(f"Cache-Verzeichnis: {cache_dir}")

    if not args.apply:
        print("\nDRY-RUN — nichts synthetisiert. Mit --apply ausfuehren.")
        return 0

    api_key = (app.config.get("GOOGLE_TTS_API_KEY") or os.environ.get("GOOGLE_TTS_API_KEY")
               or os.environ.get("GOOGLE_API_KEY"))
    if not api_key:
        print("FEHLER: kein GOOGLE_TTS_API_KEY / GOOGLE_API_KEY gesetzt.")
        return 1

    ok = 0
    failed = []
    for i, (t, cf) in enumerate(todo, start=1):
        try:
            audio = synthesize_chirp(t, voice, api_key)
            cf.write_bytes(audio)
            ok += 1
        except Exception as e:
            failed.append((t, str(e)[:120]))
        if i % 25 == 0:
            print(f"  ... {i}/{len(todo)} (ok={ok}, fail={len(failed)})", flush=True)
        if args.sleep:
            time.sleep(args.sleep)

    print(f"\nFertig: {ok} synthetisiert, {len(failed)} fehlgeschlagen.")
    for t, err in failed[:15]:
        print(f"  ! {t[:40]!r}: {err}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
