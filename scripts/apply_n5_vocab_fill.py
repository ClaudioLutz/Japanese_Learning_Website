"""Fuegt fehlende JLPT-N5-Vokabeln als NEUE ``vocabulary``-Zeilen ein.

Die Datensaetze stammen NICHT aus einem Laufzeit-LLM, sondern aus von Claude
verfassten und adversarial gegengeprueften Datendateien
(``scripts/data/n5_vocab_fill_batch_<n>.json``). Jeder Beispielsatz haelt sich an
N5-Wortschatz und -Grammatik (ausgenommen das Zielwort selbst).

Datenformat (JSON-Array):
    [{"word": "熱い", "reading": "あつい", "romaji": "atsui",
      "meaning": "hot (objects)", "meaning_de": "heiss (...)",
      "production_cue_de": "heiss (...)",
      "japanese": "熱いおちゃを飲みます。",
      "example_romaji": "Atsui o-cha o nomimasu.",
      "german": "Ich trinke heissen Tee."}, ...]

Gespeichert wird im kanonischen Karten-Format (wie
``regenerate_vocab_examples.py``):
  * ``example_sentence_japanese`` = reiner JP-Satz
  * ``example_sentence_english``  = "Romaji — Deutsche Uebersetzung"
  * ``jlpt_level=5``, ``status='approved'``, ``created_by_ai=True``
  * kein Bild, kein Audio (Audio laeuft ueber Live-TTS)

SICHERHEIT (Produktions-DB!):
  * Default ist DRY-RUN — es wird nichts geschrieben.
  * ``--apply`` verlangt ``--backup <pfad>`` auf einen existierenden, nicht
    leeren Dump der Tabelle (z.B. ``pg_dump -t vocabulary | gzip``).
  * NUR INSERTs. Existiert ein ``word`` schon, wird es uebersprungen und
    gemeldet — bestehende Zeilen werden NIE veraendert.
  * Vor dem Insert wird ``vocabulary_id_seq`` auf max(id) nachgezogen (nie
    abgesenkt), damit keine ID-Kollision entsteht.
  * Ein einziger Commit am Ende; bei einem Fehler Rollback.

Aufruf (auf hp-ubuntu, Projekt-Root, DATABASE_URL auf localhost:5432):
    python -m scripts.apply_n5_vocab_fill                     # Dry-run, alle Batches
    python -m scripts.apply_n5_vocab_fill --data scripts/data/n5_vocab_fill_batch_1.json
    python -m scripts.apply_n5_vocab_fill --apply --backup /home/hp-ubuntu/jpl-backups/vocab_<ts>.sql.gz
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.backfill_vocab_examples import JAPANESE_RE  # noqa: E402
from scripts.regenerate_vocab_examples import validate_entry  # noqa: E402

DATA_DIR = ROOT / "scripts" / "data"
DEFAULT_GLOB = "n5_vocab_fill_batch_*.json"
REQUIRED = (
    "word", "reading", "romaji", "meaning", "meaning_de",
    "production_cue_de", "japanese", "example_romaji", "german",
)

log = logging.getLogger("apply_n5_vocab_fill")


def load_entries(paths: list[Path]) -> list[dict[str, str]]:
    """Laedt alle Batch-Dateien; Felder werden getrimmt."""
    entries: list[dict[str, str]] = []
    for path in paths:
        for raw in json.loads(path.read_text(encoding="utf-8")):
            entry = {k: str(v).strip() for k, v in raw.items()}
            entry["_source"] = path.name
            entries.append(entry)
    return entries


def validate(entry: dict[str, str]) -> tuple[dict[str, object], None] | tuple[None, str]:
    """Prueft einen Datensatz; liefert (Spaltenwerte, None) oder (None, Fehler)."""
    missing = [k for k in REQUIRED if not entry.get(k)]
    if missing:
        return None, f"Pflichtfeld(er) fehlen: {', '.join(missing)}"
    if not JAPANESE_RE.search(entry["reading"]):
        return None, f"reading ohne Kana: {entry['reading']!r}"
    if JAPANESE_RE.search(entry["romaji"]):
        return None, f"romaji enthaelt japanische Zeichen: {entry['romaji']!r}"
    for field in ("meaning_de", "production_cue_de", "german"):
        if "ß" in entry[field]:
            return None, f"{field} enthaelt ß (Schweizer Schreibweise: ss)"
    checked = validate_entry({
        "japanese": entry["japanese"],
        "romaji": entry["example_romaji"],
        "german": entry["german"],
    })
    if isinstance(checked, str):
        return None, checked
    jp, en = checked
    return {
        "word": entry["word"],
        "reading": entry["reading"],
        "romaji": entry["romaji"],
        "meaning": entry["meaning"],
        "meaning_de": entry["meaning_de"],
        "production_cue_de": entry["production_cue_de"],
        "jlpt_level": 5,
        "example_sentence_japanese": jp,
        "example_sentence_english": en,
        "status": "approved",
        "created_by_ai": True,
    }, None


def plan(entries: list[dict[str, str]], existing_words: set[str]):
    """Teilt in (einzufuegen, schon vorhanden, ungueltig) auf."""
    to_insert: list[dict[str, object]] = []
    skipped: list[str] = []
    invalid: list[tuple[str, str]] = []
    seen: set[str] = set()
    for entry in entries:
        word = entry.get("word", "")
        if word in seen:
            invalid.append((word, "doppelt in den Datendateien"))
            continue
        seen.add(word)
        if word in existing_words:
            skipped.append(word)
            continue
        values, err = validate(entry)
        if err:
            invalid.append((word, err))
            continue
        to_insert.append(values)
    return to_insert, skipped, invalid


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", action="append", default=None,
                        help=f"Batch-Datei(en); Default: scripts/data/{DEFAULT_GLOB}")
    parser.add_argument("--apply", action="store_true", help="Tatsaechlich einfuegen")
    parser.add_argument("--backup", type=str, default=None,
                        help="Pfad zum vorher erstellten Tabellen-Dump (Pflicht bei --apply)")
    args = parser.parse_args()

    paths = [Path(p) for p in args.data] if args.data else sorted(DATA_DIR.glob(DEFAULT_GLOB))
    if not paths:
        log.error("Keine Batch-Dateien gefunden.")
        return 1

    if args.apply:
        backup = Path(args.backup) if args.backup else None
        if backup is None or not backup.is_file() or backup.stat().st_size == 0:
            log.error("--apply verlangt --backup <existierender, nicht leerer Dump>.")
            return 1

    entries = load_entries(paths)

    from app import create_app, db
    from app.models import Vocabulary
    from sqlalchemy import text

    app = create_app()
    with app.app_context():
        existing = {w for (w,) in db.session.query(Vocabulary.word).all()}
        to_insert, skipped, invalid = plan(entries, existing)

        mode = "APPLY" if args.apply else "DRY-RUN"
        log.info("=== N5-Vokabel-Auffuellung (%s) ===", mode)
        log.info("Dateien: %s", ", ".join(p.name for p in paths))
        log.info("Datensaetze: %d | einzufuegen: %d | schon vorhanden: %d | ungueltig: %d",
                 len(entries), len(to_insert), len(skipped), len(invalid))
        for word in skipped:
            log.info("  SKIP (existiert): %s", word)
        for word, err in invalid:
            log.info("  UNGUELTIG: %s — %s", word, err)
        for v in to_insert:
            log.info("  + %s [%s] %s | %s", v["word"], v["reading"], v["meaning_de"],
                     v["example_sentence_japanese"])

        if invalid:
            log.error("Ungueltige Datensaetze — nichts geschrieben.")
            return 1
        if not args.apply or not to_insert:
            log.info("Nichts geschrieben (%s).", "Dry-run" if not args.apply else "nichts zu tun")
            return 0

        try:
            db.session.execute(text(
                "SELECT setval('vocabulary_id_seq', GREATEST("
                "(SELECT COALESCE(MAX(id), 1) FROM vocabulary), "
                "(SELECT last_value FROM vocabulary_id_seq)))"
            ))
            new_rows = [Vocabulary(**values) for values in to_insert]
            db.session.add_all(new_rows)
            db.session.flush()
            ids = [r.id for r in new_rows]
            db.session.commit()
        except Exception:
            db.session.rollback()
            log.exception("Fehler beim Einfuegen — Rollback, nichts geschrieben.")
            return 1
        log.info("Eingefuegt: %d Zeilen, IDs %d–%d", len(ids), min(ids), max(ids))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
