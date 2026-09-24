#!/usr/bin/env python
"""Legt die von Claude verfassten, fehlenden N5-Grammatikpunkte in `grammar` an
(たら, と, たり〜たり, ながら, もらう, くれる, んです, でしょう, という).

Quelle: scripts/data/grammar_n5_gaps.json. Fachlich von einem Pruef-Agenten
gegengelesen. Die Punkte werden NUR als grammar-Zeilen angelegt und NICHT in
Lektionen eingehaengt (separate Entscheidung).

Sicherungen:
- Idempotent: existiert der Titel schon, wird die Zeile uebersprungen.
- Validierung: Pflichtfelder, genau 3 Beispielsaetze, tts_example_jp rein
  japanisch (keine lateinischen Buchstaben).
- DRY-RUN per Default; erst `--apply` schreibt.

Aufruf (auf hp-ubuntu, DATABASE_URL-Override auf localhost):
    DATABASE_URL=postgresql://app_user:...@localhost:5432/japanese_learning \\
        venv/bin/python -m scripts.apply_grammar_n5_gaps            # DRY-RUN
    DATABASE_URL=... venv/bin/python -m scripts.apply_grammar_n5_gaps --apply
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

DATA = ROOT / 'scripts' / 'data' / 'grammar_n5_gaps.json'
REQUIRED = ('title', 'structure', 'romaji', 'explanation', 'example_sentences',
            'tts_example_jp', 'nuance')
_LATIN = re.compile(r'[A-Za-z]')

log = logging.getLogger('apply_grammar_n5_gaps')


def load_items(path: Path = DATA) -> list[dict]:
    return json.loads(path.read_text(encoding='utf-8'))


def validate_item(it: dict) -> list[str]:
    """Liste der Validierungsfehler (leer = ok)."""
    errs = [f'Feld fehlt/leer: {k}' for k in REQUIRED if not (it.get(k) or '').strip()]
    if errs:
        return errs
    if len(it['title']) > 200:
        errs.append('Titel > 200 Zeichen')
    if len(it['romaji']) > 500:
        errs.append('romaji > 500 Zeichen')
    lines = [x for x in it['example_sentences'].split('\n') if x.strip()]
    if len(lines) != 3:
        errs.append(f'{len(lines)} statt 3 Beispielsaetze')
    if any(' — ' not in x or '(' not in x for x in lines):
        errs.append('Beispielsatz nicht im Format "JP (Romaji) — DE"')
    if _LATIN.search(it['tts_example_jp']):
        errs.append('tts_example_jp enthaelt lateinische Buchstaben')
    return errs


def apply_grammar(items: list[dict], apply: bool) -> dict:
    from app import db
    from app.models import Grammar

    stats = {'created': 0, 'exists': 0, 'invalid': 0}
    for it in items:
        errs = validate_item(it)
        if errs:
            log.warning('UNGUELTIG %r: %s', it.get('title'), '; '.join(errs))
            stats['invalid'] += 1
            continue
        if Grammar.query.filter_by(title=it['title']).first():
            log.info('EXISTIERT: %s', it['title'])
            stats['exists'] += 1
            continue
        log.info('NEU: %s', it['title'])
        if apply:
            db.session.add(Grammar(
                title=it['title'],
                explanation=it['explanation'],
                structure=it['structure'],
                romaji=it['romaji'],
                jlpt_level=5,
                example_sentences=it['example_sentences'],
                tts_example_jp=it['tts_example_jp'],
                nuance=it['nuance'],
                status='approved',
                created_by_ai=True,
            ))
        stats['created'] += 1

    if apply:
        db.session.commit()
    else:
        db.session.rollback()
    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='Aenderungen schreiben')
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    from app import create_app

    items = load_items()
    app = create_app()
    with app.app_context():
        stats = apply_grammar(items, apply=args.apply)
    mode = 'APPLIED' if args.apply else 'DRY-RUN (nichts geschrieben)'
    log.info('%s: %d neu, %d existierten schon, %d ungueltig.',
             mode, stats['created'], stats['exists'], stats['invalid'])
    return 0 if stats['invalid'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
