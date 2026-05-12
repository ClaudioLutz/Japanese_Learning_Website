"""Pilot-Seed: Drag-Drop-Spiel in N5 Hiragana 1 (Lesson 146).

Erstellt einen neuen LessonContent vom Typ 'kana_grid_game' plus zugehoerige
KanaGridConfig. Idempotent — bei wiederholtem Lauf wird nichts dupliziert.

Verwendung:
    python scripts/seed_kana_grid_pilot.py
    python scripts/seed_kana_grid_pilot.py --lesson-id 147  # andere Lesson
"""
import argparse
import sys
from pathlib import Path

# Repo-Root in sys.path aufnehmen
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import create_app, db  # noqa: E402
from app.models import KanaGridConfig, Kana, Lesson, LessonContent  # noqa: E402


DEFAULT_LESSON_ID = 146  # N5 Hiragana 1 — Vokale, K-Reihe, S-Reihe
DEFAULT_TITLE = 'Übung: Hiragana einsortieren'


def find_or_create_grid_content(lesson_id: int, title: str) -> LessonContent:
    """Sucht existierenden kana_grid_game-Content oder erstellt einen neuen."""
    existing = LessonContent.query.filter_by(
        lesson_id=lesson_id, content_type='kana_grid_game'
    ).first()
    if existing:
        print(f'  [i] Bestehender kana_grid_game-Content gefunden (id={existing.id})')
        return existing

    lesson = Lesson.query.get(lesson_id)
    if not lesson:
        raise SystemExit(f'ERROR:Lesson {lesson_id} nicht gefunden')

    # Hoechsten order_index + page_number der existierenden Kana-Items finden
    kana_items = (
        LessonContent.query
        .filter_by(lesson_id=lesson_id, content_type='kana')
        .order_by(LessonContent.page_number.asc(), LessonContent.order_index.desc())
        .all()
    )
    if not kana_items:
        raise SystemExit(f'ERROR:Lesson {lesson_id} hat keine Kana-Items')

    last_kana = kana_items[-1]  # letztes Kana-Item (hoechster order_index)
    page = last_kana.page_number
    next_order = max(c.order_index for c in kana_items if c.page_number == page) + 1

    content = LessonContent(
        lesson_id=lesson_id,
        content_type='kana_grid_game',
        title=title,
        page_number=page,
        order_index=next_order,
        is_optional=False,
    )
    db.session.add(content)
    db.session.flush()  # ID erzeugen, damit FK-Verknuepfung moeglich
    print(f'  [OK] Neuer kana_grid_game-Content erstellt (id={content.id}, page={page}, order={next_order})')
    return content


def find_or_create_config(content: LessonContent, kana_ids: list[int]) -> KanaGridConfig:
    """Sucht existierende Config oder legt neue an."""
    existing = KanaGridConfig.query.filter_by(lesson_content_id=content.id).first()
    if existing:
        # Aktualisiere kana_ids falls sich Lesson-Inhalt geaendert hat
        if existing.kana_ids != kana_ids:
            existing.kana_ids = kana_ids
            print(f'  [~] KanaGridConfig (id={existing.id}) kana_ids aktualisiert')
        else:
            print(f'  [i] KanaGridConfig (id={existing.id}) bereits aktuell')
        return existing

    config = KanaGridConfig(
        lesson_content_id=content.id,
        kana_ids=kana_ids,
        default_mode='schreiben',
        allow_mode_switch=True,
        grid_layout='rows',
        shuffle_pool=True,
        timer_enabled=False,
    )
    db.session.add(config)
    print(f'  [OK] KanaGridConfig neu angelegt (kana_ids={len(kana_ids)} Eintraege)')
    return config


def kana_ids_from_lesson(lesson_id: int) -> list[int]:
    """Extrahiert Kana-IDs aus den Kana-Content-Items der Lesson, in Reihenfolge."""
    kana_contents = (
        LessonContent.query
        .filter_by(lesson_id=lesson_id, content_type='kana')
        .order_by(LessonContent.page_number.asc(), LessonContent.order_index.asc())
        .all()
    )
    ids = []
    for c in kana_contents:
        if c.content_id and c.content_id not in ids:
            # Doppelte vermeiden (z.B. wenn Kana in mehreren Pages auftaucht)
            if Kana.query.get(c.content_id):
                ids.append(c.content_id)
    return ids


def main():
    parser = argparse.ArgumentParser(description='Seed Kana-Grid-Pilot')
    parser.add_argument('--lesson-id', type=int, default=DEFAULT_LESSON_ID)
    parser.add_argument('--title', type=str, default=DEFAULT_TITLE)
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        lesson = Lesson.query.get(args.lesson_id)
        if not lesson:
            raise SystemExit(f'ERROR:Lesson {args.lesson_id} nicht gefunden')

        print(f'>>Pilot-Seed fuer Lesson {args.lesson_id}: "{lesson.title}"')

        kana_ids = kana_ids_from_lesson(args.lesson_id)
        if not kana_ids:
            raise SystemExit('ERROR:Keine Kana-IDs in dieser Lesson gefunden')
        print(f'  -{len(kana_ids)} Kana-IDs gefunden')

        content = find_or_create_grid_content(args.lesson_id, args.title)
        find_or_create_config(content, kana_ids)

        db.session.commit()
        print('[OK] Fertig.')


if __name__ == '__main__':
    main()
