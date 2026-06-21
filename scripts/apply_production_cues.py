#!/usr/bin/env python
"""Schreibt die von Claude verfassten Produktions-Cues (DE->JP-Disambiguierung)
in Vocabulary.production_cue_de.

Quelle: scripts/data/vocab_production_cues.json (Liste von {id, word, cue}).
Muster wie scripts/regenerate_vocab_examples.py: Claude verfasst den Inhalt,
dieses Skript schreibt nur das fertige, geprüfte Ergebnis in die DB —
KEINE Laufzeit-LLM-Calls.

Sicherungen:
- Wort-Abgleich: die DB-Vokabel zur id MUSS das erwartete Wort haben (sonst Skip).
- Leak-Guard: ein Cue mit japanischen Zeichen wird ABGELEHNT (er steht auf der
  Karten-Vorderseite und darf die Antwort nicht verraten).
- DRY-RUN per Default; erst `--apply` schreibt. Vorher-Werte werden geloggt.

Aufruf (auf hp-ubuntu mit DATABASE_URL-Override auf localhost, da .env auf `db` zeigt):
    DATABASE_URL=postgresql://app_user:...@localhost:5432/japanese_learning \\
        python scripts/apply_production_cues.py            # DRY-RUN
    DATABASE_URL=... python scripts/apply_production_cues.py --apply
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app, db  # noqa: E402
from app.models import Vocabulary  # noqa: E402

_CJK = re.compile(r'[぀-ヿ㐀-䶿一-鿿ｦ-ﾟ]')
DATA = Path(__file__).parent / 'data' / 'vocab_production_cues.json'


def main():
    apply = '--apply' in sys.argv
    items = json.loads(DATA.read_text(encoding='utf-8'))

    app = create_app()
    with app.app_context():
        updated = skipped = rejected = unchanged = 0
        for it in items:
            vid, word, cue = it['id'], it['word'], it['cue'].strip()
            if _CJK.search(cue):
                print(f'  LEAK-ABLEHNUNG id={vid} ({word}): Cue enthält japanische Zeichen -> {cue!r}')
                rejected += 1
                continue
            v = db.session.get(Vocabulary, vid)
            if not v:
                print(f'  SKIP id={vid}: Vokabel nicht gefunden')
                skipped += 1
                continue
            if v.word != word:
                print(f'  SKIP id={vid}: Wort weicht ab (DB={v.word!r} != erwartet={word!r})')
                skipped += 1
                continue
            if (v.production_cue_de or '') == cue:
                unchanged += 1
                continue
            print(f'  id={vid} {v.word}: {v.production_cue_de!r} -> {cue!r}')
            if apply:
                v.production_cue_de = cue
            updated += 1

        if apply:
            db.session.commit()
            print(f'\nAPPLIED: {updated} aktualisiert, {unchanged} unverändert, '
                  f'{skipped} übersprungen, {rejected} abgelehnt.')
        else:
            db.session.rollback()
            print(f'\nDRY-RUN: {updated} würden aktualisiert, {unchanged} unverändert, '
                  f'{skipped} übersprungen, {rejected} abgelehnt. '
                  f'Mit --apply ausführen, um zu schreiben.')


if __name__ == '__main__':
    main()
