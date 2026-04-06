#!/usr/bin/env python3
"""
Validiert MNN-Lektions-JSON-Dateien gegen das Pydantic-Schema.

Nutzung:
    python scripts/validate_json.py --file scripts/mnn_data/beginner1_lesson01.json
    python scripts/validate_json.py --all          # Alle JSON-Dateien validieren
"""

import argparse
import json
import sys
import io
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.schema import LessonData

DATA_DIR = PROJECT_ROOT / "scripts" / "mnn_data"


def validate_file(filepath: Path) -> bool:
    """Validiert eine einzelne JSON-Datei. Gibt True bei Erfolg zurueck."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except json.JSONDecodeError as e:
        print(f"  FEHLER: Ungültiges JSON — {e}")
        return False

    try:
        data = LessonData.model_validate(raw)
        vocab_count = len(data.vocabulary) + len(data.vocabulary_countries)
        grammar_count = len(data.grammar)
        conv_lines = len(data.conversation.lines)
        print(f"  OK: L{data.lesson_number} — {vocab_count} Vokabeln, {grammar_count} Grammatik, {conv_lines} Dialogzeilen")
        return True
    except Exception as e:
        print(f"  FEHLER: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="MNN JSON-Validierung")
    parser.add_argument("--file", type=str, help="Einzelne JSON-Datei")
    parser.add_argument("--all", action="store_true", help="Alle JSON-Dateien validieren")
    args = parser.parse_args()

    if not args.file and not args.all:
        parser.print_help()
        sys.exit(1)

    if args.file:
        files = [Path(args.file)]
    else:
        files = sorted(DATA_DIR.glob("*.json"))

    if not files:
        print(f"Keine JSON-Dateien gefunden in {DATA_DIR}")
        sys.exit(1)

    ok_count = 0
    fail_count = 0

    for filepath in files:
        print(f"\n--- {filepath.name} ---")
        if not filepath.exists():
            print("  FEHLER: Datei nicht gefunden")
            fail_count += 1
            continue

        if validate_file(filepath):
            ok_count += 1
        else:
            fail_count += 1

    print(f"\n{'='*60}")
    print(f"Ergebnis: {ok_count} OK, {fail_count} FEHLER")
    print(f"{'='*60}")

    sys.exit(1 if fail_count > 0 else 0)


if __name__ == "__main__":
    main()
