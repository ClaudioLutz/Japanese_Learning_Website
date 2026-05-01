"""Exportiert alle aktiv genutzten Vokabel-Saetze mit englischer Translation
zu einem JSON-Block, den Claude einmal manuell ins Deutsche uebersetzt und
zurueck als Hand-Override in scripts/translate_english_to_german.py einsetzt.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app import create_app, db  # noqa: E402
from app.models import Vocabulary  # noqa: E402

EN = re.compile(r'\b(the|is|are|am|my|your|he|she|we|they|that|this|will|have|has|with|from|for)\b', re.I)
DE = re.compile(r'\b(ich|du|er|sie|wir|ein|eine|der|die|das|ist|sind|bin|bist|nicht|nach|von|mit|fuer|für|aus)\b', re.I)
UML = re.compile(r'[äöüÄÖÜß]')


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    app = create_app()
    with app.app_context():
        rows = db.session.execute(db.text('''
            SELECT DISTINCT lc.content_id FROM lesson_content lc
            JOIN lesson l ON l.id = lc.lesson_id AND l.is_published = true
            WHERE lc.content_type = 'vocabulary'
        ''')).fetchall()
        active = {r[0] for r in rows}

        items = []
        for v in Vocabulary.query.order_by(Vocabulary.id).all():
            if v.id not in active:
                continue
            text = (v.example_sentence_english or '').strip()
            if not text:
                continue
            translation = text.split(' — ', 1)[1] if ' — ' in text else text
            if EN.search(translation) and not (DE.search(translation) or UML.search(translation)):
                items.append({
                    'id': v.id,
                    'word': v.word,
                    'jp': v.example_sentence_japanese,
                    'current_en': text,
                })
        print(json.dumps(items, ensure_ascii=False, indent=2))
        print(f'\n# TOTAL: {len(items)}', file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main())
