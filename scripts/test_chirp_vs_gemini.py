"""A/B-Test: Chirp 3 HD Leda vs. Gemini 2.5 Pro TTS Leda.

Generiert MP3s/WAVs fuer Hiragana-Reihen, Woerter und Saetze, damit
manuell entschieden werden kann ob Gemini den Wechsel wert ist.

Output: scripts/tts_test_output/ab_<modell>_<voice>_<case>.<ext>
"""
from __future__ import annotations

import io
import os
import sys
import wave
from pathlib import Path

if sys.platform == "win32" and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

OUT_DIR = PROJECT_ROOT / "scripts" / "tts_test_output"
OUT_DIR.mkdir(exist_ok=True)
VOICE = "Leda"  # gleiche Stimme bei beiden, damit Modell-Unterschied isoliert ist

# (key, label, chirp_text, gemini_text)
# Bei Chirp greift unsere Server-Heuristik (Komma-Trenner). Hier replizieren
# wir das fuer Reihen explizit. Gemini bekommt das native Markup [short pause].
CASES = [
    ("01_kana_a",       "Hiragana A-Reihe (Vokale)",
        "あ、い、う、え、お",
        "あ [short pause] い [short pause] う [short pause] え [short pause] お"),
    ("02_kana_s",       "Hiragana S-Reihe",
        "さ、し、す、せ、そ",
        "さ [short pause] し [short pause] す [short pause] せ [short pause] そ"),
    ("03_kana_t",       "Hiragana T-Reihe (Devoicing-Test ち つ)",
        "た、ち、つ、て、と",
        "た [short pause] ち [short pause] つ [short pause] て [short pause] と"),

    ("10_word_sushi",       "Wort: すし",                    "すし", "すし"),
    ("11_word_sakura",      "Wort: さくら (Pitch HLL)",      "さくら", "さくら"),
    ("12_word_arigatou",    "Wort: ありがとう (Pitch LHHHL)", "ありがとう", "ありがとう"),
    ("13_word_gakusei",     "Wort: 学生 (gakusei)",          "学生", "学生"),
    ("14_word_hashi_chop",  "Wort: 箸 (Stäbchen, HL)",       "箸", "箸"),
    ("15_word_hashi_bridge","Wort: 橋 (Brücke, LH)",         "橋", "橋"),

    ("20_sentence_intro",   "Satz: わたしはマイクです。",
        "わたしはマイクです。", "わたしはマイクです。"),
    ("21_sentence_weather", "Satz: 今日はいい天気ですね。",
        "今日はいい天気ですね。", "今日はいい天気ですね。"),
    ("22_sentence_station", "Satz: すみません、駅はどこですか。",
        "すみません、駅はどこですか。", "すみません、駅はどこですか。"),
    ("23_sentence_learn",   "Satz (langer): 日本語を勉強しています。",
        "日本語を勉強しています。", "日本語を勉強しています。"),
]


def synth_chirp(text: str, out: Path) -> None:
    from google.cloud import texttospeech
    api_key = os.environ.get("GOOGLE_TTS_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    client = texttospeech.TextToSpeechClient(client_options={"api_key": api_key})
    voice = texttospeech.VoiceSelectionParams(language_code="ja-JP", name=f"ja-JP-Chirp3-HD-{VOICE}")
    config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=0.85,
    )
    resp = client.synthesize_speech(
        input=texttospeech.SynthesisInput(text=text),
        voice=voice,
        audio_config=config,
    )
    out.write_bytes(resp.audio_content)


def synth_gemini(text: str, out: Path) -> None:
    """Gemini 2.5 Pro TTS via google-genai (Google AI Studio).

    Prompt-Strategie: KEIN englisches Vorwort (sonst wird es vorgelesen oder
    fuehrt zu leerer Antwort bei kurzem Text). Nur Style-Marker + Text.
    """
    from google import genai
    from google.genai import types

    api_key = os.environ.get("GOOGLE_AI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    client = genai.Client(api_key=api_key)

    prompt = f"[slow][clear] {text}"

    resp = client.models.generate_content(
        model="gemini-2.5-pro-preview-tts",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=VOICE)
                ),
            ),
        ),
    )
    cand = resp.candidates[0] if resp.candidates else None
    if cand is None or cand.content is None or not cand.content.parts:
        raise RuntimeError(f"Leere Antwort (finish={getattr(cand, 'finish_reason', '?')})")
    pcm = cand.content.parts[0].inline_data.data
    # Gemini liefert 24kHz 16-bit mono PCM — als WAV speichern
    with wave.open(str(out), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)
        wf.writeframes(pcm)


def main():
    print(f"A/B-Test: Chirp 3 HD vs Gemini 2.5 Pro TTS — Voice: {VOICE}")
    print(f"Output: {OUT_DIR}\n")

    chirp_ok = gemini_ok = 0
    chirp_err = gemini_err = 0

    for key, label, chirp_text, gemini_text in CASES:
        print(f"[{key}] {label}")
        print(f"    Chirp:  {chirp_text!r}")
        chirp_out = OUT_DIR / f"ab_{key}_chirp.mp3"
        try:
            synth_chirp(chirp_text, chirp_out)
            kb = chirp_out.stat().st_size // 1024
            print(f"      -> {chirp_out.name} ({kb} KB)")
            chirp_ok += 1
        except Exception as e:
            print(f"      Chirp FEHLER: {e}")
            chirp_err += 1

        print(f"    Gemini: {gemini_text!r}")
        gem_out = OUT_DIR / f"ab_{key}_gemini.wav"
        try:
            synth_gemini(gemini_text, gem_out)
            kb = gem_out.stat().st_size // 1024
            print(f"      -> {gem_out.name} ({kb} KB)")
            gemini_ok += 1
        except Exception as e:
            print(f"      Gemini FEHLER: {e}")
            gemini_err += 1

    print(f"\nFertig. Chirp: {chirp_ok} ok / {chirp_err} Fehler. "
          f"Gemini: {gemini_ok} ok / {gemini_err} Fehler.")
    print(f"\nHoere paarweise an:")
    print(f"  ab_<key>_chirp.mp3  vs  ab_<key>_gemini.wav")


if __name__ == "__main__":
    main()
