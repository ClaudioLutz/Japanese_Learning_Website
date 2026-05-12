"""Fading-Scaffolding: max_hints + Romaji-Hint pro Lesson setzen.

Bjork (Desirable Difficulties) + van de Pol (Fading Scaffolding): in der ersten
Lesson viel Stuetzung, dann systematisch zurueckfahren — der Lerner geht aktiv
in den Recall, mit nachvollziehbarer Hilfe nur dort wo noetig.

Heuristik (Hiragana 1-5, Katakana 1-5):
    Lesson 1 → max_hints=3, romaji_hint=True   (sanfter Einstieg)
    Lesson 2 → max_hints=2, romaji_hint=False  (Romaji-Pool-Hint weg)
    Lesson 3 → max_hints=1, romaji_hint=False
    Lesson 4 → max_hints=0, romaji_hint=False  (volles Recall)
    Lesson 5 → max_hints=0, romaji_hint=False

Verwendung:
    python scripts/update_kana_grid_hints.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import create_app, db  # noqa: E402
from app.models import KanaGridConfig, Lesson, LessonContent  # noqa: E402


# Mapping (Hiragana/Katakana N) → (max_hints, show_romaji_hint_on_pool)
FADING_TABLE = {
    1: (3, True),
    2: (2, False),
    3: (1, False),
    4: (0, False),
    5: (0, False),
}


def lesson_number(title: str) -> int:
    """Extrahiert die Zahl hinter Hiragana/Katakana aus dem Lesson-Titel."""
    m = re.search(r'(?:Hiragana|Katakana)\s+(\d+)', title, flags=re.I)
    return int(m.group(1)) if m else 0


def main():
    app = create_app()
    with app.app_context():
        # Alle kana_grid_game-LessonContents finden
        contents = (
            db.session.query(LessonContent, Lesson, KanaGridConfig)
            .join(Lesson, LessonContent.lesson_id == Lesson.id)
            .join(KanaGridConfig, KanaGridConfig.lesson_content_id == LessonContent.id)
            .filter(LessonContent.content_type == 'kana_grid_game')
            .all()
        )
        if not contents:
            print('[WARN] Keine kana_grid_game-Configs gefunden.')
            return

        updated = 0
        for lc, lesson, cfg in contents:
            num = lesson_number(lesson.title)
            if num not in FADING_TABLE:
                print(f'  [skip] Lesson {lesson.id} "{lesson.title}" — keine Hiragana/Katakana-N-Zuordnung')
                continue
            max_hints, romaji_hint = FADING_TABLE[num]
            changed = False
            if cfg.max_hints != max_hints:
                print(f'  [~] Lesson {lesson.id} "{lesson.title}" → max_hints {cfg.max_hints} -> {max_hints}')
                cfg.max_hints = max_hints
                changed = True
            if cfg.show_romaji_hint_on_pool != romaji_hint:
                print(f'  [~] Lesson {lesson.id} "{lesson.title}" → romaji_hint {cfg.show_romaji_hint_on_pool} -> {romaji_hint}')
                cfg.show_romaji_hint_on_pool = romaji_hint
                changed = True
            if changed:
                updated += 1
        db.session.commit()
        print(f'[OK] {updated} Configs aktualisiert.')


if __name__ == '__main__':
    main()
