"""Roll-out: Kana-Grid-Spiel in alle 10 Hiragana/Katakana-Lessons (N5).

Iteriert ueber alle Lessons mit Hiragana/Katakana im Titel und ergaenzt
pro Lesson ein kana_grid_game-Item + KanaGridConfig. Wiederverwendet die
Idempotenz-Logik aus seed_kana_grid_pilot.py.

Verwendung:
    python scripts/seed_kana_grid_all_lessons.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import create_app, db  # noqa: E402
from app.models import Lesson  # noqa: E402
from scripts.seed_kana_grid_pilot import (  # noqa: E402
    find_or_create_config,
    find_or_create_grid_content,
    kana_ids_from_lesson,
)


# Pro Lesson: Default-Modus + Titel-Vorschlag.
LESSON_PRESETS = {
    # Hiragana
    'hiragana 1': {'mode': 'schreiben', 'title': 'Uebung: Hiragana einsortieren (a/k/s)'},
    'hiragana 2': {'mode': 'schreiben', 'title': 'Uebung: Hiragana einsortieren (t/n/h)'},
    'hiragana 3': {'mode': 'schreiben', 'title': 'Uebung: Hiragana einsortieren (m/y/r/w/n)'},
    'hiragana 4': {'mode': 'schreiben', 'title': 'Uebung: Dakuten/Handakuten'},
    'hiragana 5': {'mode': 'lesen',     'title': 'Uebung: Yoon — Hiragana lesen'},
    # Katakana
    'katakana 1': {'mode': 'schreiben', 'title': 'Uebung: Katakana einsortieren (a/k/s)'},
    'katakana 2': {'mode': 'schreiben', 'title': 'Uebung: Katakana einsortieren (t/n/h)'},
    'katakana 3': {'mode': 'schreiben', 'title': 'Uebung: Katakana einsortieren (m/y/r/w/n)'},
    'katakana 4': {'mode': 'lesen',     'title': 'Uebung: Dakuten/Handakuten + Laengungsstrich'},
    'katakana 5': {'mode': 'lesen',     'title': 'Uebung: Yoon und Lehnwoerter'},
}


def preset_for_lesson(title: str):
    t = title.lower()
    for key, preset in LESSON_PRESETS.items():
        if key in t:
            return preset
    return {'mode': 'schreiben', 'title': 'Uebung: Kana einsortieren'}


def main():
    app = create_app()
    with app.app_context():
        lessons = (
            Lesson.query
            .filter(
                db.or_(
                    Lesson.title.ilike('%hiragana%'),
                    Lesson.title.ilike('%katakana%'),
                )
            )
            .order_by(Lesson.order_index.asc(), Lesson.id.asc())
            .all()
        )
        print(f'>> {len(lessons)} Kana-Lessons gefunden')
        affected = 0
        for lesson in lessons:
            preset = preset_for_lesson(lesson.title)
            print(f'\n>> Lesson {lesson.id}: {lesson.title}')

            kana_ids = kana_ids_from_lesson(lesson.id)
            if not kana_ids:
                print('  [skip] Keine Kana-Items in dieser Lesson')
                continue

            content = find_or_create_grid_content(lesson.id, preset['title'])
            cfg = find_or_create_config(content, kana_ids)

            # Modus-Default aktualisieren falls noch nicht passend
            if cfg.default_mode != preset['mode']:
                cfg.default_mode = preset['mode']
                print(f'  [~] default_mode auf "{preset["mode"]}" gesetzt')

            affected += 1

        db.session.commit()
        print(f'\n[OK] Fertig. {affected} Lessons mit kana_grid_game versehen.')


if __name__ == '__main__':
    main()
