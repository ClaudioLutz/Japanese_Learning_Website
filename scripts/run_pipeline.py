#!/usr/bin/env python3
"""
Orchestriert die MNN-Lektions-Pipeline.

Fuehrt fuer jede Lektion die Schritte aus:
  1. JSON validieren (Pydantic-Schema)
  2. In DB importieren (import_mnn.py)
  3. TTS-Audio generieren (generate_tts_audio.py)
  4. Quizzes generieren (generate_quizzes.py)

Nutzung:
    python scripts/run_pipeline.py --lessons 1-25           # Book 1
    python scripts/run_pipeline.py --lessons 1              # Einzelne Lektion
    python scripts/run_pipeline.py --lessons 1-25 --dry-run # Nur anzeigen
    python scripts/run_pipeline.py --lessons 1-25 --skip-tts
    python scripts/run_pipeline.py --lessons 1-50 --only validate
    python scripts/run_pipeline.py --lessons 26-50 --only import,quizzes
"""

import argparse
import subprocess
import sys
import io
import time
from pathlib import Path

if sys.platform == "win32" and "pytest" not in sys.modules:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
DATA_DIR = SCRIPTS_DIR / "mnn_data"

PYTHON = sys.executable


def parse_lesson_range(lesson_str: str) -> list[int]:
    """Parst '1-25' oder '1,3,5' oder '7' zu einer Liste von Lektionsnummern."""
    results = []
    for part in lesson_str.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-", 1)
            results.extend(range(int(start), int(end) + 1))
        else:
            results.append(int(part))
    return sorted(set(results))


def find_json_file(lesson_num: int) -> Path | None:
    """Findet die JSON-Datei fuer eine Lektionsnummer."""
    book = "beginner1" if lesson_num <= 25 else "beginner2"
    primary = DATA_DIR / f"{book}_lesson{lesson_num:02d}.json"
    if primary.exists():
        return primary
    # Fallback: Glob
    candidates = list(DATA_DIR.glob(f"*lesson{lesson_num:02d}*.json"))
    return candidates[0] if candidates else None


def run_step(name: str, cmd: list[str], dry_run: bool = False) -> bool:
    """Fuehrt einen Pipeline-Schritt aus. Gibt True bei Erfolg zurueck."""
    cmd_str = " ".join(cmd)
    print(f"\n  [{name.upper()}] {cmd_str}")

    if dry_run:
        print("  [DRY-RUN] Uebersprungen")
        return True

    start = time.time()
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    elapsed = time.time() - start

    if result.returncode != 0:
        print(f"  FEHLER in '{name}' (Exit Code: {result.returncode}, {elapsed:.1f}s)")
        return False

    print(f"  OK ({elapsed:.1f}s)")
    return True


def run_pipeline(
    lesson_numbers: list[int],
    dry_run: bool = False,
    skip_tts: bool = False,
    only_steps: list[str] | None = None,
    force_quizzes: bool = False,
):
    """Fuehrt die Pipeline fuer alle angegebenen Lektionen aus."""
    total = len(lesson_numbers)
    success = 0
    failed = []

    print(f"\n{'#'*60}")
    print(f"  MNN Pipeline — {total} Lektion(en)")
    print(f"  Modus: {'DRY RUN' if dry_run else 'LIVE'}")
    if skip_tts:
        print("  TTS: Uebersprungen")
    if only_steps:
        print(f"  Nur Schritte: {', '.join(only_steps)}")
    print(f"{'#'*60}")

    for idx, num in enumerate(lesson_numbers, 1):
        print(f"\n{'='*60}")
        print(f"  LEKTION {num} ({idx}/{total})")
        print(f"{'='*60}")

        json_file = find_json_file(num)
        if not json_file:
            print(f"  FEHLER: Keine JSON-Datei fuer Lektion {num}")
            failed.append(num)
            continue

        all_ok = True

        # Schritt 1: Validierung
        if not only_steps or "validate" in only_steps:
            ok = run_step("validate", [
                PYTHON, str(SCRIPTS_DIR / "validate_json.py"),
                "--file", str(json_file),
            ], dry_run)
            if not ok:
                print(f"  ABBRUCH: Validierung fehlgeschlagen fuer Lektion {num}")
                failed.append(num)
                continue

        # Schritt 2: Import
        if not only_steps or "import" in only_steps:
            ok = run_step("import", [
                PYTHON, str(SCRIPTS_DIR / "import_mnn.py"),
                str(json_file.name),
            ], dry_run)
            if not ok:
                all_ok = False

        # Schritt 3: TTS
        if not skip_tts and (not only_steps or "tts" in only_steps):
            ok = run_step("tts", [
                PYTHON, str(SCRIPTS_DIR / "generate_tts_audio.py"),
                "--lesson", str(num),
            ], dry_run)
            if not ok:
                all_ok = False

        # Schritt 4: Quizzes
        if not only_steps or "quizzes" in only_steps:
            quiz_cmd = [
                PYTHON, str(SCRIPTS_DIR / "generate_quizzes.py"),
                "--lesson", str(num),
            ]
            if force_quizzes:
                quiz_cmd.append("--force")
            ok = run_step("quizzes", quiz_cmd, dry_run)
            if not ok:
                all_ok = False

        if all_ok:
            success += 1
        else:
            failed.append(num)

    # Zusammenfassung
    print(f"\n{'#'*60}")
    print(f"  ERGEBNIS: {success}/{total} erfolgreich")
    if failed:
        print(f"  FEHLGESCHLAGEN: Lektionen {failed}")
    print(f"{'#'*60}")

    return len(failed) == 0


def main():
    parser = argparse.ArgumentParser(
        description="MNN Pipeline-Orchestrierung",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python scripts/run_pipeline.py --lessons 1          # Einzelne Lektion
  python scripts/run_pipeline.py --lessons 1-25       # Book 1
  python scripts/run_pipeline.py --lessons 1-50       # Alle
  python scripts/run_pipeline.py --lessons 1-25 --dry-run
  python scripts/run_pipeline.py --lessons 1-25 --skip-tts
  python scripts/run_pipeline.py --lessons 1 --only validate
  python scripts/run_pipeline.py --lessons 1-50 --only validate,import
        """,
    )
    parser.add_argument("--lessons", type=str, required=True,
                        help="Lektionsnummern: '1', '1-25', '1,3,5'")
    parser.add_argument("--dry-run", action="store_true",
                        help="Nichts ausfuehren, nur anzeigen")
    parser.add_argument("--skip-tts", action="store_true",
                        help="TTS-Generierung ueberspringen")
    parser.add_argument("--only", type=str, default=None,
                        help="Nur bestimmte Schritte: validate,import,tts,quizzes")
    parser.add_argument("--force-quizzes", action="store_true",
                        help="Bestehende Quizzes ueberschreiben")
    args = parser.parse_args()

    lesson_numbers = parse_lesson_range(args.lessons)
    only_steps = [s.strip() for s in args.only.split(",")] if args.only else None

    # Validierung der Schritte
    valid_steps = {"validate", "import", "tts", "quizzes"}
    if only_steps:
        invalid = set(only_steps) - valid_steps
        if invalid:
            print(f"FEHLER: Unbekannte Schritte: {invalid}")
            print(f"Erlaubt: {valid_steps}")
            sys.exit(1)

    ok = run_pipeline(
        lesson_numbers=lesson_numbers,
        dry_run=args.dry_run,
        skip_tts=args.skip_tts,
        only_steps=only_steps,
        force_quizzes=args.force_quizzes,
    )
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
