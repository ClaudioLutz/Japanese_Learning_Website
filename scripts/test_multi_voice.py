#!/usr/bin/env python3
"""Testscript: Generiert nur die Konversation mit Multi-Voice."""
import json
import os
import sys
import io
from pathlib import Path

if sys.platform == "win32" and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

os.environ.setdefault("DATABASE_URL", "postgresql://app_user:JapaneseApp2025!@localhost:5432/japanese_learning")

from scripts.generate_tts_audio import (
    get_google_tts_client, generate_conversation_audio, AUDIO_BASE
)

with open(PROJECT_ROOT / "scripts/mnn_data/beginner1_lesson01.json", "r", encoding="utf-8") as f:
    data = json.load(f)

conv_lines = data["conversation"]["lines"]
audio_dir = AUDIO_BASE / "mnn_lesson_01"
out_path = audio_dir / "lesson01_conversation.mp3"

print("Generiere Multi-Voice Konversation...")
client = get_google_tts_client()
generate_conversation_audio(client, conv_lines, out_path)
print("Fertig!")
