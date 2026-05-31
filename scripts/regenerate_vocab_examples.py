"""Schreibt kuratierte, level-konforme Beispielsaetze in ``vocabulary``.

Die Saetze werden NICHT zur Laufzeit per LLM erzeugt, sondern stammen aus einer
von Hand/Claude verfassten und gegengeprueften Datendatei
(``scripts/data/vocab_example_sentences.json``). Jeder Satz haelt sich an den
Wortschatz des Karten-Levels (N5-Karte -> nur N5, N4-Karte -> N5+N4; ausgenommen
das Zielwort selbst).

Datenformat (JSON-Array):
    [{"id": 20, "japanese": "...", "romaji": "...", "german": "..."}, ...]

Gespeichert wird im kanonischen Karten-Format:
  * ``example_sentence_japanese`` = reiner JP-Satz (TTS-tauglich, endet auf
    。/！/？, ohne Romaji/Latein)
  * ``example_sentence_english`` = "Romaji — Deutsche Uebersetzung" (em-dash)

SICHERHEIT (Produktions-DB!):
  * Default ist DRY-RUN — es wird nichts geschrieben.
  * ``--apply`` schreibt; davor wird IMMER ein JSON-Backup der betroffenen
    Zeilen unter ``backups/vocab_examples/`` abgelegt.
  * Es werden ausschliesslich die beiden Beispielsatz-Spalten der Tabelle
    ``vocabulary`` angefasst — keine Nutzer-/Zahlungs-/Fortschrittsdaten.
  * Jeder Satz wird vor dem Schreiben validiert; Ungueltiges wird NICHT
    geschrieben, sondern gemeldet.

Aufruf (aus dem Projekt-Root, wo DATABASE_URL erreichbar ist):
    python -m scripts.regenerate_vocab_examples                 # Dry-run, ganze Datendatei
    python -m scripts.regenerate_vocab_examples --level 5       # nur N5-Karten
    python -m scripts.regenerate_vocab_examples --ids 20,21,22  # gezielt
    python -m scripts.regenerate_vocab_examples --limit 10      # Stichprobe
    python -m scripts.regenerate_vocab_examples --apply         # tatsaechlich schreiben
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import create_app, db  # noqa: E402
from app.models import Vocabulary  # noqa: E402
# Validatoren des bestehenden Backfill-Skripts wiederverwenden (DRY).
from scripts.backfill_vocab_examples import (  # noqa: E402
    JAPANESE_RE,
    is_pure_japanese_sentence,
    strip_trailing_romaji,
)

DEFAULT_DATA = ROOT / "scripts" / "data" / "vocab_example_sentences.json"
BACKUP_DIR = ROOT / "backups" / "vocab_examples"


def parse_ids(raw: str | None) -> set[int] | None:
    if not raw:
        return None
    ids: set[int] = set()
    for part in raw.split(","):
        part = part.strip()
        if part:
            ids.add(int(part))
    return ids or None


def load_data(path: Path) -> dict[int, dict[str, str]]:
    """Laedt die Beispielsatz-Datendatei als ``{id: {japanese, romaji, german}}``."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    by_id: dict[int, dict[str, str]] = {}
    for entry in raw:
        by_id[int(entry["id"])] = {
            "japanese": (entry.get("japanese") or "").strip(),
            "romaji": (entry.get("romaji") or "").strip(),
            "german": (entry.get("german") or "").strip(),
        }
    return by_id


def validate_entry(entry: dict[str, str]) -> tuple[str, str] | str:
    """Prueft einen Datensatz und liefert ``(jp, en_field)`` oder einen Fehlertext."""
    jp = strip_trailing_romaji(entry["japanese"])
    romaji = entry["romaji"]
    german = entry["german"]

    if not is_pure_japanese_sentence(jp):
        return f"JP nicht TTS-tauglich/rein: {jp!r}"
    if not romaji:
        return "Romaji fehlt"
    if JAPANESE_RE.search(romaji):
        return f"Romaji enthaelt japanische Zeichen: {romaji!r}"
    if not german:
        return "Deutsche Uebersetzung fehlt"

    return jp, f"{romaji} — {german}"


def write_backup(rows: list[Vocabulary]) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = BACKUP_DIR / f"vocab_examples_backup_{stamp}.json"
    payload = [
        {
            "id": v.id,
            "word": v.word,
            "jlpt_level": v.jlpt_level,
            "example_sentence_japanese": v.example_sentence_japanese,
            "example_sentence_english": v.example_sentence_english,
        }
        for v in rows
    ]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true",
                        help="Schreibt Aenderungen in die DB (sonst nur Dry-run)")
    parser.add_argument("--data", type=str, default=str(DEFAULT_DATA),
                        help="Pfad zur Beispielsatz-Datendatei (JSON-Array)")
    parser.add_argument("--only-missing", action="store_true",
                        help="Nur Karten OHNE japanischen Beispielsatz schreiben")
    parser.add_argument("--level", type=int, default=None,
                        help="Nur Karten dieses JLPT-Levels (5=N5 ... 1=N1)")
    parser.add_argument("--ids", type=str, default=None,
                        help="Komma-Liste von Vocabulary-IDs, z.B. 20,21,22")
    parser.add_argument("--limit", type=int, default=None,
                        help="Maximale Anzahl Karten (Stichprobe)")
    parser.add_argument("--commit-batch", type=int, default=50,
                        help="Commit-Intervall im --apply-Modus")
    args = parser.parse_args()

    data_path = Path(args.data)
    if not data_path.exists():
        print(f"FEHLER: Datendatei nicht gefunden: {data_path}")
        return 1
    data = load_data(data_path)
    ids_filter = parse_ids(args.ids)

    app = create_app()
    with app.app_context():
        query = Vocabulary.query
        if args.level is not None:
            query = query.filter(Vocabulary.jlpt_level == args.level)
        if ids_filter is not None:
            query = query.filter(Vocabulary.id.in_(ids_filter))
        rows = query.order_by(Vocabulary.id).all()

        # Nur Karten, fuer die es einen Datensatz gibt.
        rows = [v for v in rows if v.id in data]

        if args.only_missing:
            rows = [v for v in rows
                    if not (v.example_sentence_japanese or "").strip()]
        if args.limit is not None:
            rows = rows[:args.limit]

        total = len(rows)
        mode = "APPLY" if args.apply else "DRY-RUN"
        print(f"=== Vocabulary-Beispielsatz-Regeneration ({mode}) ===")
        print(f"Datendatei: {data_path} ({len(data)} Eintraege)")
        print(f"Ausgewaehlt: {total} Karten"
              f"{f' | Level=N{args.level}' if args.level else ''}"
              f"{' | nur fehlende' if args.only_missing else ''}")
        if total == 0:
            print("Nichts zu tun.")
            return 0

        if args.apply:
            backup_path = write_backup(rows)
            print(f"Backup geschrieben: {backup_path}")

        ok: list[tuple[int, str, str, str]] = []     # (id, word, jp, en)
        failed: list[tuple[int, str, str]] = []        # (id, word, grund)
        pending = 0

        for idx, v in enumerate(rows, start=1):
            validated = validate_entry(data[v.id])
            if isinstance(validated, str):
                failed.append((v.id, v.word, validated))
                continue
            jp, en = validated
            ok.append((v.id, v.word, jp, en))
            if args.apply:
                v.example_sentence_japanese = jp
                v.example_sentence_english = en
                pending += 1
                if pending >= args.commit_batch:
                    db.session.commit()
                    print(f"  ... committed ({idx}/{total})", flush=True)
                    pending = 0

        if args.apply and pending:
            db.session.commit()

        print()
        print(f"Geschrieben/gueltig: {len(ok)} | Fehlgeschlagen: {len(failed)}")

        if ok[:10]:
            print()
            print("Vorschau (erste 10):")
            for vid, word, jp, en in ok[:10]:
                print(f"  [{vid}] {word}")
                print(f"      JP: {jp}")
                print(f"      EN: {en}")
            if len(ok) > 10:
                print(f"  ... +{len(ok) - 10} weitere")

        if failed:
            print()
            print(f"Fehlgeschlagen ({len(failed)}):")
            for vid, word, grund in failed[:30]:
                print(f"  [{vid}] {word}: {grund}")
            if len(failed) > 30:
                print(f"  ... +{len(failed) - 30} weitere")

        if not args.apply:
            print()
            print("DRY-RUN — es wurde nichts geschrieben. Mit --apply ausfuehren, "
                  "um die Aenderungen zu speichern (Backup erfolgt automatisch).")

        return 0


if __name__ == "__main__":
    sys.exit(main())
