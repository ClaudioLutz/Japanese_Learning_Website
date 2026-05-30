"""Regeneriert `vocabulary.example_sentence_*` mit level-konformem Wortschatz.

Ziel: Jeder Beispielsatz einer Vokabelkarte soll ausser dem Zielwort selbst nur
Wortschatz UND Grammatik bis zum JLPT-Level der Karte verwenden (N5-Karte -> nur
N5, N4-Karte -> N5+N4, usw. — siehe ``app.ai_services.build_jlpt_vocab_constraint``).

Die Saetze werden per Gemini neu erzeugt (``AILessonContentGenerator
.generate_vocabulary_example_sentence``) und im kanonischen Karten-Format
gespeichert:
  * ``example_sentence_japanese`` = reiner JP-Satz (TTS-tauglich, endet auf
    。/！/？, ohne Romaji/Latein)
  * ``example_sentence_english`` = "Romaji — Deutsche Uebersetzung" (em-dash)

SICHERHEIT (Produktions-DB!):
  * Default ist DRY-RUN — es wird nichts geschrieben.
  * ``--apply`` schreibt; davor wird IMMER ein JSON-Backup der betroffenen
    Zeilen unter ``backups/vocab_examples/`` abgelegt.
  * Es werden ausschliesslich die beiden Beispielsatz-Spalten der Tabelle
    ``vocabulary`` angefasst — keine Nutzer-/Zahlungs-/Fortschrittsdaten.
  * Vor dem Schreiben wird jeder generierte Satz validiert; ungueltige Saetze
    werden NICHT geschrieben, sondern als Fehler gemeldet.

Aufruf (aus dem Projekt-Root, wo DATABASE_URL erreichbar ist):
    python -m scripts.regenerate_vocab_examples                 # Dry-run, ganzer Bestand
    python -m scripts.regenerate_vocab_examples --level 5       # nur N5-Karten
    python -m scripts.regenerate_vocab_examples --ids 20,21,22  # gezielt
    python -m scripts.regenerate_vocab_examples --limit 10      # erste 10 (Stichprobe)
    python -m scripts.regenerate_vocab_examples --only-missing  # nur leere Felder fuellen
    python -m scripts.regenerate_vocab_examples --apply         # tatsaechlich schreiben
    python -m scripts.regenerate_vocab_examples --apply --sleep 0.3   # mit Rate-Limit
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import create_app, db  # noqa: E402
from app.models import Vocabulary  # noqa: E402
from app.ai_services import AILessonContentGenerator  # noqa: E402
# Validatoren des bestehenden Backfill-Skripts wiederverwenden (DRY).
from scripts.backfill_vocab_examples import (  # noqa: E402
    JAPANESE_RE,
    is_pure_japanese_sentence,
    strip_trailing_romaji,
)

BACKUP_DIR = ROOT / "backups" / "vocab_examples"


def parse_ids(raw: str | None) -> set[int] | None:
    """Zerlegt "20,21, 22" -> {20, 21, 22}. None/leer -> None (kein Filter)."""
    if not raw:
        return None
    ids: set[int] = set()
    for part in raw.split(","):
        part = part.strip()
        if part:
            ids.add(int(part))
    return ids or None


def select_vocab(only_missing: bool, include_missing: bool,
                 level: int | None, ids: set[int] | None,
                 limit: int | None) -> list[Vocabulary]:
    """Waehlt die zu verarbeitenden Vokabeln gemaess Filtern aus.

    Default (ohne Flags): der bestehende Bestand = Karten mit bereits gesetztem
    japanischem Beispielsatz (diese werden level-konform neu geschrieben).
    """
    query = Vocabulary.query
    if level is not None:
        query = query.filter(Vocabulary.jlpt_level == level)
    if ids is not None:
        query = query.filter(Vocabulary.id.in_(ids))

    has_jp = (Vocabulary.example_sentence_japanese.isnot(None)) & \
             (Vocabulary.example_sentence_japanese != "")
    if only_missing:
        query = query.filter(~has_jp)
    elif not include_missing and ids is None:
        # Default: nur vorhandenen Bestand regenerieren (gezielte --ids
        # bleiben unangetastet von diesem Filter).
        query = query.filter(has_jp)

    query = query.order_by(Vocabulary.id)
    if limit is not None:
        query = query.limit(limit)
    return query.all()


def write_backup(rows: list[Vocabulary]) -> Path:
    """Schreibt ein JSON-Backup der betroffenen Beispielsatz-Felder."""
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


def validate_result(result: dict) -> tuple[str, str] | str:
    """Prueft ein Generator-Ergebnis und liefert ``(jp, en_field)`` bei Erfolg
    oder einen Fehlertext (str) bei Ungueltigkeit.

    * ``jp`` wird von trailing Klammer-Romaji bereinigt und muss ein reiner,
      TTS-tauglicher JP-Satz sein.
    * ``romaji`` darf keine japanischen Zeichen enthalten.
    * ``german`` darf nicht leer sein.
    * ``en_field`` = "Romaji — Deutsch" (em-dash).
    """
    if "error" in result:
        return f"AI-Fehler: {result['error']}"

    jp = strip_trailing_romaji((result.get("japanese") or "").strip())
    romaji = (result.get("romaji") or "").strip()
    german = (result.get("german") or "").strip()

    if not is_pure_japanese_sentence(jp):
        return f"JP nicht TTS-tauglich/rein: {jp!r}"
    if not romaji:
        return "Romaji fehlt"
    if JAPANESE_RE.search(romaji):
        return f"Romaji enthaelt japanische Zeichen: {romaji!r}"
    if not german:
        return "Deutsche Uebersetzung fehlt"

    return jp, f"{romaji} — {german}"


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true",
                        help="Schreibt Aenderungen in die DB (sonst nur Dry-run)")
    parser.add_argument("--only-missing", action="store_true",
                        help="Nur Karten OHNE japanischen Beispielsatz befuellen")
    parser.add_argument("--include-missing", action="store_true",
                        help="Bestand UND leere Felder verarbeiten")
    parser.add_argument("--level", type=int, default=None,
                        help="Nur Karten dieses JLPT-Levels (5=N5 ... 1=N1)")
    parser.add_argument("--ids", type=str, default=None,
                        help="Komma-Liste von Vocabulary-IDs, z.B. 20,21,22")
    parser.add_argument("--limit", type=int, default=None,
                        help="Maximale Anzahl Karten (Stichprobe)")
    parser.add_argument("--sleep", type=float, default=0.0,
                        help="Pause in Sekunden zwischen AI-Aufrufen (Rate-Limit)")
    parser.add_argument("--commit-batch", type=int, default=20,
                        help="Commit-Intervall im --apply-Modus")
    args = parser.parse_args()

    ids = parse_ids(args.ids)

    app = create_app()
    with app.app_context():
        rows = select_vocab(
            only_missing=args.only_missing,
            include_missing=args.include_missing,
            level=args.level,
            ids=ids,
            limit=args.limit,
        )
        total = len(rows)
        mode = "APPLY" if args.apply else "DRY-RUN"

        print(f"=== Vocabulary-Beispielsatz-Regeneration ({mode}) ===")
        print(f"Ausgewaehlt: {total} Karten"
              f"{f' | Level=N{args.level}' if args.level else ''}"
              f"{' | nur fehlende' if args.only_missing else ''}")
        if total == 0:
            print("Nichts zu tun.")
            return 0

        backup_path: Path | None = None
        if args.apply:
            backup_path = write_backup(rows)
            print(f"Backup geschrieben: {backup_path}")

        generator = AILessonContentGenerator()

        ok: list[tuple[int, str, str, str]] = []      # (id, word, jp, en)
        failed: list[tuple[int, str, str]] = []        # (id, word, grund)
        pending = 0

        for idx, v in enumerate(rows, start=1):
            level = v.jlpt_level or 5
            result = generator.generate_vocabulary_example_sentence(
                word=v.word,
                reading=v.reading,
                meaning_de=v.meaning_de or v.meaning,
                jlpt_level=level,
            )
            validated = validate_result(result)
            if isinstance(validated, str):
                failed.append((v.id, v.word, validated))
            else:
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

            if args.sleep:
                time.sleep(args.sleep)

        if args.apply and pending:
            db.session.commit()

        # --- Report ---
        print()
        print(f"Erfolgreich generiert: {len(ok)} | Fehlgeschlagen/uebersprungen: {len(failed)}")

        preview = ok[:10]
        if preview:
            print()
            print("Vorschau (erste 10):")
            for vid, word, jp, en in preview:
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
