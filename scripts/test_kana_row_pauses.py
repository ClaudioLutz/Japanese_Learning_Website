"""Verifiziert die Kana-Reihen-Pausen-Logik.

1. Unit-Tests fuer `_maybe_spell_out_kana_row` — Reihen werden getrennt,
   Woerter nicht.
2. Live-Probe mit Chirp 3 HD: generiert MP3s ohne und mit `、`-Pausen,
   damit man manuell bestaetigen kann ob Chirp die Pause hoerbar macht.
"""
from __future__ import annotations

import io
import os
import sys
from pathlib import Path

if sys.platform == "win32" and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://app_user:JapaneseApp2025!@localhost:5432/japanese_learning",
)
os.environ.setdefault("PAYMENT_PROVIDER", "mock")
os.environ.setdefault("MOCK_PAYMENTS_ENABLED", "true")

from app.routes import _maybe_spell_out_kana_row

CASES = [
    ("さしすせそ",                         "さ、し、す、せ、そ"),
    ("あいうえお",                         "あ、い、う、え、お"),
    ("がぎぐげご",                         "が、ぎ、ぐ、げ、ご"),
    ("Die S-Reihe: 「さしすせそ」",        "Die S-Reihe: 「さ、し、す、せ、そ」"),
    ("すし",                                "すし"),                # zu kurz
    ("こんにちは",                         "こんにちは"),           # gemischte Reihen
    ("さくら",                              "さくら"),               # gemischte Reihen
    ("わたしは学生です",                   "わたしは学生です"),     # Kanji + gemischt
]

def test_logic():
    print("=== Unit-Test ===")
    fails = 0
    for src, expected in CASES:
        got = _maybe_spell_out_kana_row(src)
        ok = got == expected
        if not ok:
            fails += 1
        marker = "OK" if ok else "FAIL"
        print(f"  [{marker}] {src!r}")
        if not ok:
            print(f"         erwartet: {expected!r}")
            print(f"         erhalten: {got!r}")
    print(f"{len(CASES) - fails}/{len(CASES)} Tests bestanden\n")
    return fails == 0


def generate_probe():
    """Erzeugt MP3s zum manuellen Vergleich."""
    from google.cloud import texttospeech

    api_key = os.environ.get("GOOGLE_TTS_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("Kein GOOGLE_TTS_API_KEY — ueberspringe Audio-Probe.")
        return

    client = texttospeech.TextToSpeechClient(client_options={"api_key": api_key})
    voice = texttospeech.VoiceSelectionParams(language_code="ja-JP", name="ja-JP-Chirp3-HD-Leda")
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=0.85,
    )

    out_dir = PROJECT_ROOT / "scripts" / "tts_test_output"
    out_dir.mkdir(exist_ok=True)

    samples = {
        "s_row_no_pause":      "さしすせそ",
        "s_row_comma":         "さ、し、す、せ、そ",
        "s_row_comma_spaced":  "さ 、 し 、 す 、 せ 、 そ",
        "s_row_period":        "さ。し。す。せ。そ",
    }

    print("=== Audio-Probe ===")
    for name, text in samples.items():
        try:
            resp = client.synthesize_speech(
                input=texttospeech.SynthesisInput(text=text),
                voice=voice,
                audio_config=audio_config,
            )
            out = out_dir / f"chirp_{name}.mp3"
            out.write_bytes(resp.audio_content)
            kb = out.stat().st_size // 1024
            print(f"  {name:25s} -> {out.name} ({kb} KB)  [{text}]")
        except Exception as e:
            print(f"  {name}: FEHLER {e}")

    print(f"\nDateien in: {out_dir}")
    print("Hoere die 4 MP3s — die mit deutlichen Pausen waehlen.")


if __name__ == "__main__":
    ok = test_logic()
    generate_probe()
    sys.exit(0 if ok else 1)
