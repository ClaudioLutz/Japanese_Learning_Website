"""Testet drei Prompt-Strategien fuer die S-Reihe mit Gemini."""
import os, sys, wave, io
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from google import genai
from google.genai import types

api_key = os.environ.get("GOOGLE_AI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)

OUT = PROJECT_ROOT / "scripts" / "tts_test_output"
OUT.mkdir(exist_ok=True)

strategies = [
    ("A_pause_markup", "さ [short pause] し [short pause] す [short pause] せ [short pause] そ"),
    ("B_japanese_comma", "さ、し、す、せ、そ"),
    ("C_tutor_wrapper", "Read aloud each Japanese hiragana with a brief pause between them: さ。 し。 す。 せ。 そ。"),
    ("D_period_separator", "さ。し。す。せ。そ。"),
]

for label, text in strategies:
    try:
        resp = client.models.generate_content(
            model="gemini-2.5-pro-preview-tts",
            contents=text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Leda")
                    ),
                ),
            ),
        )
        cand = resp.candidates[0] if resp.candidates else None
        if cand and cand.content and cand.content.parts:
            pcm = cand.content.parts[0].inline_data.data
            duration = len(pcm) / (24000 * 2)
            out = OUT / f"sreihe_{label}.wav"
            buf = io.BytesIO()
            with wave.open(buf, "wb") as wf:
                wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(24000)
                wf.writeframes(pcm)
            out.write_bytes(buf.getvalue())
            print(f"  {label}: {len(pcm)} bytes, {duration:.2f}s audio -> {out.name}")
        else:
            print(f"  {label}: LEER (finish={getattr(cand, 'finish_reason', '?')})")
    except Exception as e:
        print(f"  {label}: ERROR {e}")
