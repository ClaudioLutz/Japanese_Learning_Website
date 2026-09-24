#!/usr/bin/env python
"""Schreibt die von Claude verfassten DE->JP-Produktions-Cues fuer den
N5-Bestand (Welle 2, 649 Vokabeln) in Vocabulary.production_cue_de.

Quelle: scripts/data/production_cues_batch_<n>.json (Listen von {id, word, cue}).
Jeder Batch wurde von einem Pruef-Agenten auf Mehrdeutigkeit (mehrere N5-Woerter
passen) und Loesungs-Leaks (Romaji/JP/Lehnwort-Transkription) geprueft.
Muster wie scripts/apply_production_cues.py — KEINE Laufzeit-LLM-Calls.

Sicherungen:
- Nur Zeilen, deren production_cue_de heute NULL/leer ist, werden beschrieben
  (bestehende / parallel gesetzte Cues werden nie ueberschrieben).
- Wort-Abgleich: DB-Vokabel zur id MUSS das erwartete Wort haben (sonst Skip).
- Leak-Guard: Cues mit japanischen Zeichen werden abgelehnt.
- DRY-RUN per Default; erst `--apply` schreibt.

Aufruf (auf hp-ubuntu, DATABASE_URL-Override auf localhost, da .env auf `db` zeigt):
    DATABASE_URL=postgresql://app_user:...@localhost:5432/japanese_learning \\
        venv/bin/python -m scripts.apply_production_cues_batches            # DRY-RUN
    DATABASE_URL=... venv/bin/python -m scripts.apply_production_cues_batches --apply
Vorher Backup: pg_dump -t vocabulary -t grammar.
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DATA_DIR = ROOT / 'scripts' / 'data'
_CJK = re.compile(r'[぀-ヿ㐀-䶿一-鿿ｦ-ﾟ]')

log = logging.getLogger('apply_production_cues_batches')


def load_items(data_dir: Path = DATA_DIR) -> list[dict]:
    """Alle Batch-Dateien in id-Reihenfolge laden; doppelte ids sind ein Fehler."""
    items: list[dict] = []
    for p in sorted(data_dir.glob('production_cues_batch_*.json'),
                    key=lambda x: int(x.stem.rsplit('_', 1)[1])):
        items.extend(json.loads(p.read_text(encoding='utf-8')))
    ids = [it['id'] for it in items]
    if len(ids) != len(set(ids)):
        raise ValueError('Doppelte Vokabel-ids in den Batch-Dateien')
    return items


def validate_cue(cue: str) -> str | None:
    """Fehlertext, falls der Cue unzulaessig ist, sonst None."""
    if not cue.strip():
        return 'leerer Cue'
    if _CJK.search(cue):
        return 'enthaelt japanische Zeichen (Leak)'
    if len(cue) > 120:
        return 'zu lang'
    return None


def apply_cues(items: list[dict], apply: bool) -> dict:
    """Setzt production_cue_de, nur wo er heute leer ist. Gibt Zaehler zurueck."""
    from app import db
    from app.models import Vocabulary

    stats = {'updated': 0, 'already_set': 0, 'skipped': 0, 'rejected': 0}
    for it in items:
        vid, word, cue = it['id'], it['word'], it['cue'].strip()
        err = validate_cue(cue)
        if err:
            log.warning('ABGELEHNT id=%s (%s): %s -> %r', vid, word, err, cue)
            stats['rejected'] += 1
            continue
        v = db.session.get(Vocabulary, vid)
        if v is None:
            log.warning('SKIP id=%s: Vokabel nicht gefunden', vid)
            stats['skipped'] += 1
            continue
        if v.word != word:
            log.warning('SKIP id=%s: Wort weicht ab (DB=%r, erwartet=%r)', vid, v.word, word)
            stats['skipped'] += 1
            continue
        if (v.production_cue_de or '').strip():
            stats['already_set'] += 1
            continue
        log.info('id=%s %s: -> %r', vid, v.word, cue)
        if apply:
            v.production_cue_de = cue
        stats['updated'] += 1

    if apply:
        db.session.commit()
    else:
        db.session.rollback()
    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='Aenderungen schreiben')
    parser.add_argument('-q', '--quiet', action='store_true', help='keine Einzelzeilen')
    args = parser.parse_args()
    logging.basicConfig(level=logging.WARNING if args.quiet else logging.INFO,
                        format='%(message)s')

    from app import create_app

    items = load_items()
    app = create_app()
    with app.app_context():
        stats = apply_cues(items, apply=args.apply)
    mode = 'APPLIED' if args.apply else 'DRY-RUN (nichts geschrieben)'
    logging.getLogger().setLevel(logging.INFO)
    log.info('%s: %d Items, %d aktualisiert, %d bereits gesetzt, %d uebersprungen, '
             '%d abgelehnt.', mode, len(items), stats['updated'], stats['already_set'],
             stats['skipped'], stats['rejected'])
    return 0 if stats['rejected'] == 0 and stats['skipped'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
