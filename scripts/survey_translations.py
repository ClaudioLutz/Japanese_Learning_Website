"""Survey: welche example_sentence_english-Eintraege sind Englisch vs Deutsch?

Zaehlt Heuristik-basiert:
  - looks_english: enthaelt typisches englisches Funktionswort (the, is, my, you, ...)
  - looks_german: enthaelt typisches deutsches Funktionswort (ich, ist, der, ein, ...)
  - has_umlaut: enthaelt aeoeueAOEUess (deutscher Indikator)
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import create_app  # noqa: E402
from app.models import Vocabulary  # noqa: E402

EN_TOKENS = re.compile(r'\b(the|is|are|am|my|your|he|she|we|they|that|this|will|have|has|with|from|for)\b', re.I)
DE_TOKENS = re.compile(r'\b(ich|du|er|sie|wir|ein|eine|der|die|das|ist|sind|bin|bist|nicht|nach|von|mit|fuer|für|aus|hat|haben|wird|werden|wurde|sehe|gehe|nehme)\b', re.I)
UMLAUT = re.compile(r'[äöüÄÖÜß]')


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    app = create_app()
    with app.app_context():
        all_vocab = (Vocabulary.query
                     .filter(Vocabulary.example_sentence_english.isnot(None))
                     .order_by(Vocabulary.id)
                     .all())

        total = 0
        looks_en = 0
        looks_de = 0
        has_umlaut = 0
        only_en = []
        for v in all_vocab:
            text = (v.example_sentence_english or '').strip()
            if not text:
                continue
            total += 1
            translation = text.split(' — ', 1)[1] if ' — ' in text else text
            is_en = bool(EN_TOKENS.search(translation))
            is_de = bool(DE_TOKENS.search(translation)) or bool(UMLAUT.search(translation))
            if UMLAUT.search(translation):
                has_umlaut += 1
            if is_en:
                looks_en += 1
            if is_de:
                looks_de += 1
            if is_en and not is_de:
                only_en.append((v.id, v.word, text[:80]))

        print(f"Total mit example_sentence_english: {total}")
        print(f"  looks_english:  {looks_en}")
        print(f"  looks_german:   {looks_de}")
        print(f"  has_umlaut:     {has_umlaut}")
        print(f"  only_english (kein DE-Marker): {len(only_en)}")
        print()
        print("Stichprobe only_english (erste 30):")
        for vid, word, t in only_en[:30]:
            print(f"  [{vid}] {word:14} {t}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
