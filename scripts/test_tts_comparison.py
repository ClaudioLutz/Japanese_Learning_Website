"""
TTS-Vergleichstest: OpenAI gpt-4o-mini-tts vs Google Cloud TTS Neural2
Generiert Testdateien mit japanischem Text, um die Qualität zu vergleichen.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Projekt-Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

OUTPUT_DIR = PROJECT_ROOT / "scripts" / "tts_test_output"
OUTPUT_DIR.mkdir(exist_ok=True)

# --- Testtexte (aus Lektion 1) ---

# 1) Einzelne Vokabeln mit Pause
VOCAB_TEXT = (
    "わたし。\n"
    "あなた。\n"
    "せんせい。\n"
    "がくせい。\n"
    "かいしゃいん。\n"
    "いしゃ。\n"
    "エンジニア。\n"
    "だいがく。\n"
    "びょういん。"
)

# 2) Grammatik-Beispielsätze
GRAMMAR_TEXT = (
    "わたしは マイク・ミラーです。\n"
    "わたしは エンジニアです。\n"
    "サントスさんは 学生じゃ ありません。\n"
    "ミラーさんは アメリカ人ですか。\n"
    "はい、アメリカ人です。\n"
    "あの方は どなたですか。"
)

# 3) Konversation
CONVERSATION_TEXT = (
    "おはようございます。\n"
    "おはようございます。佐藤さん、こちらは ミラーさんです。\n"
    "はじめまして。マイク・ミラーです。"
    "アメリカから きました。どうぞ よろしく おねがいします。\n"
    "佐藤 けいこです。どうぞ よろしく。"
)

TEST_CASES = [
    ("vocabulary", VOCAB_TEXT),
    ("grammar", GRAMMAR_TEXT),
    ("conversation", CONVERSATION_TEXT),
]


def generate_openai(text: str, output_path: Path, voice: str = "coral"):
    """OpenAI gpt-4o-mini-tts mit instructions-Parameter."""
    from openai import OpenAI

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    response = client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice=voice,
        input=text,
        instructions=(
            "Speak in natural, native Japanese with correct pitch accent. "
            "Speak slowly and clearly, as this is for language learners. "
            "Add a brief pause between each sentence or vocabulary word."
        ),
        response_format="mp3",
    )

    response.stream_to_file(str(output_path))
    print(f"  [OpenAI {voice}] -> {output_path.name} ({output_path.stat().st_size // 1024} KB)")


def generate_google(text: str, output_path: Path, voice_name: str = "ja-JP-Neural2-B"):
    """Google Cloud TTS Neural2 mit SSML für Pausen."""
    from google.cloud import texttospeech

    # Google Cloud TTS braucht entweder Service Account oder API Key
    # Wir versuchen es zuerst mit API Key
    api_key = os.environ.get("GOOGLE_TTS_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    if api_key:
        client = texttospeech.TextToSpeechClient(
            client_options={"api_key": api_key}
        )
    else:
        # Fallback: Service Account (GOOGLE_APPLICATION_CREDENTIALS)
        client = texttospeech.TextToSpeechClient()

    # SSML mit Pausen zwischen Sätzen/Wörtern
    lines = text.strip().split("\n")
    ssml_lines = []
    for line in lines:
        ssml_lines.append(f"<s>{line.strip()}</s><break time='800ms'/>")
    ssml = f"<speak>{''.join(ssml_lines)}</speak>"

    synthesis_input = texttospeech.SynthesisInput(ssml=ssml)

    voice = texttospeech.VoiceSelectionParams(
        language_code="ja-JP",
        name=voice_name,
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=0.85,  # Etwas langsamer für Lernende
        pitch=0.0,
    )

    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config,
    )

    output_path.write_bytes(response.audio_content)
    print(f"  [Google {voice_name}] -> {output_path.name} ({output_path.stat().st_size // 1024} KB)")


def main():
    print("=" * 60)
    print("TTS-Vergleichstest: OpenAI vs Google Cloud")
    print(f"Output-Verzeichnis: {OUTPUT_DIR}")
    print("=" * 60)

    # --- OpenAI Tests ---
    print("\n--- OpenAI gpt-4o-mini-tts ---")
    openai_key = os.environ.get("OPENAI_API_KEY")
    if not openai_key:
        print("  WARNUNG: OPENAI_API_KEY nicht gesetzt, überspringe OpenAI.")
    else:
        # Teste mehrere Stimmen
        for voice in ["coral", "nova", "sage"]:
            for name, text in TEST_CASES:
                out = OUTPUT_DIR / f"openai_{voice}_{name}.mp3"
                try:
                    generate_openai(text, out, voice=voice)
                except Exception as e:
                    print(f"  FEHLER [{voice}/{name}]: {e}")

    # --- Google Cloud TTS Tests ---
    print("\n--- Google Cloud TTS Neural2 ---")
    google_key = os.environ.get("GOOGLE_TTS_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    google_creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not google_key and not google_creds:
        print("  WARNUNG: Weder GOOGLE_TTS_API_KEY noch GOOGLE_APPLICATION_CREDENTIALS gesetzt.")
        print("  Überspringe Google Cloud TTS.")
    else:
        # Teste verschiedene japanische Stimmen
        google_voices = [
            "ja-JP-Neural2-B",  # Männlich
            "ja-JP-Neural2-C",  # Weiblich
            "ja-JP-Neural2-D",  # Männlich 2
        ]
        for voice_name in google_voices:
            for name, text in TEST_CASES:
                out = OUTPUT_DIR / f"google_{voice_name}_{name}.mp3"
                try:
                    generate_google(text, out, voice_name=voice_name)
                except Exception as e:
                    print(f"  FEHLER [{voice_name}/{name}]: {e}")

    # --- Zusammenfassung ---
    files = sorted(OUTPUT_DIR.glob("*.mp3"))
    print(f"\n{'=' * 60}")
    print(f"Fertig! {len(files)} Dateien generiert in:")
    print(f"  {OUTPUT_DIR}")
    print()
    for f in files:
        print(f"  {f.name:50s} {f.stat().st_size // 1024:>5d} KB")
    print(f"\nBitte die Dateien anhören und Qualität vergleichen!")


if __name__ == "__main__":
    main()
