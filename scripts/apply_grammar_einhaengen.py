#!/usr/bin/env python
"""Haengt die 9 N5-Grammatikpunkte aus grammar_n5_gaps.json in publizierte Lektionen ein.

Quelle: scripts/data/grammar_n5_einhaengen.json (von Claude verfasst). Pro Lektion
entsteht eine NEUE letzte Seite (LessonPage + Ueberleitungstext + Grammatik-Karten
als LessonContent content_type='grammar' mit content_id=grammar.id).

Sicherungen:
- Nur anhaengen: die neue Seite ist immer max(Seite)+1; weicht das von
  ``expect_new_page`` ab, wird die Lektion uebersprungen. Bestehende Seitenzahlen
  und last_page der Nutzer bleiben unveraendert.
- Pruefungen: Lektion existiert, ist publiziert, gehoert zum erwarteten Modul;
  Grammatik-Titel existiert; hoechstens 3 neue Grammatikpunkte pro Lektion.
- Idempotent: existiert die Extra-Seite (gleicher Titel) schon, werden nur fehlende
  Items ergaenzt; bereits in der Lektion haengende Grammatik wird nicht doppelt angelegt.
- DRY-RUN per Default; erst ``--apply`` schreibt (eine Transaktion, bei SKIP Abbruch).

Aufruf (auf hp-ubuntu, DATABASE_URL-Override auf localhost):
    DATABASE_URL=postgresql://app_user:...@localhost:5432/japanese_learning \\
        venv/bin/python -m scripts.apply_grammar_einhaengen            # DRY-RUN
    DATABASE_URL=... venv/bin/python -m scripts.apply_grammar_einhaengen --apply
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DATA = ROOT / 'scripts' / 'data' / 'grammar_n5_einhaengen.json'
MAX_PER_LESSON = 3
REQUIRED = ('lesson_id', 'category_id', 'expect_new_page', 'page_title',
            'intro_title', 'intro_text', 'grammar_titles')

log = logging.getLogger('apply_grammar_einhaengen')


def load_plan(path: Path = DATA) -> list[dict]:
    return json.loads(path.read_text(encoding='utf-8'))['lessons']


def validate_entry(e: dict) -> list[str]:
    errs = [f'Feld fehlt/leer: {k}' for k in REQUIRED if not e.get(k)]
    if errs:
        return errs
    if len(e['grammar_titles']) > MAX_PER_LESSON:
        errs.append(f'mehr als {MAX_PER_LESSON} Grammatikpunkte')
    if len(set(e['grammar_titles'])) != len(e['grammar_titles']):
        errs.append('Grammatik doppelt')
    if max(len(e['page_title']), len(e['intro_title'])) > 200:
        errs.append('Titel > 200 Zeichen')
    if 'mayuko' in json.dumps(e, ensure_ascii=False).lower():
        errs.append('Name der Fachreviewerin im Inhalt')
    return errs


def plan_lesson(e: dict) -> dict:
    """Ermittelt, was fuer eine Lektion zu tun ist (ohne zu schreiben)."""
    from app.models import Grammar, Lesson, LessonContent, LessonPage

    res = {'lesson_id': e['lesson_id'], 'status': 'OK', 'reason': '', 'page': None,
           'new_page': False, 'add_intro': False, 'add_grammar': [], 'exists': 0}
    errs = validate_entry(e)
    from app import db
    lesson = db.session.get(Lesson, e['lesson_id'])
    if errs:
        res.update(status='SKIP', reason='; '.join(errs))
        return res
    if lesson is None or not lesson.is_published:
        res.update(status='SKIP', reason='Lektion fehlt oder nicht publiziert')
        return res
    if lesson.category_id != e['category_id']:
        res.update(status='SKIP', reason=f'Modul {lesson.category_id} statt {e["category_id"]}')
        return res
    grammars = []
    for t in e['grammar_titles']:
        g = Grammar.query.filter_by(title=t).one_or_none()
        if g is None:
            res.update(status='SKIP', reason=f'Grammatik fehlt: {t}')
            return res
        grammars.append(g)

    items = LessonContent.query.filter_by(lesson_id=lesson.id).all()
    linked = {c.content_id for c in items if c.content_type == 'grammar'}
    page = LessonPage.query.filter_by(lesson_id=lesson.id, title=e['page_title']).first()
    if page is not None:
        res['page'] = page.page_number
        res['add_intro'] = not any(c.content_type == 'text' and c.title == e['intro_title']
                                   and c.page_number == page.page_number for c in items)
    else:
        pages = [c.page_number for c in items]
        pages += [p.page_number for p in LessonPage.query.filter_by(lesson_id=lesson.id)]
        new_no = max(pages, default=0) + 1
        if new_no != e['expect_new_page']:
            res.update(status='SKIP', reason=f'neue Seite waere {new_no}, erwartet {e["expect_new_page"]}')
            return res
        res.update(page=new_no, new_page=True, add_intro=True)
    for g in grammars:
        if g.id in linked:
            res['exists'] += 1
        else:
            res['add_grammar'].append(g.id)
    if not (res['new_page'] or res['add_intro'] or res['add_grammar']):
        res['status'] = 'SCHON'
    return res


def write_lesson(e: dict, res: dict) -> int:
    """Schreibt die geplanten Zeilen in die Session (ohne Commit). Gibt Anzahl Items."""
    from app import db
    from app.models import LessonContent, LessonPage

    page_no = res['page']
    if res['new_page']:
        db.session.add(LessonPage(lesson_id=e['lesson_id'], page_number=page_no,
                                  title=e['page_title'], description=e.get('page_description'),
                                  page_type='normal'))
    existing = LessonContent.query.filter_by(lesson_id=e['lesson_id'], page_number=page_no).all()
    order = max((c.order_index or 0 for c in existing), default=0)
    details = {'generator': 'claude', 'source': 'apply_grammar_einhaengen'}
    n = 0
    if res['add_intro']:
        order += 1
        db.session.add(LessonContent(
            lesson_id=e['lesson_id'], page_number=page_no, order_index=order,
            content_type='text', title=e['intro_title'], content_text=e['intro_text'],
            is_optional=False, generated_by_ai=False, ai_generation_details=details))
        n += 1
    for gid in res['add_grammar']:
        order += 1
        db.session.add(LessonContent(
            lesson_id=e['lesson_id'], page_number=page_no, order_index=order,
            content_type='grammar', content_id=gid, is_optional=False,
            generated_by_ai=False, ai_generation_details=details))
        n += 1
    return n


def apply_plan(entries: list[dict], apply: bool = False, allow_partial: bool = False) -> dict:
    from app import db

    results = [(e, plan_lesson(e)) for e in entries]
    stats = {'lessons': 0, 'items': 0, 'pages': 0, 'skipped': 0, 'already': 0,
             'written': False, 'results': [r for _, r in results]}
    all_titles = [t for e in entries for t in e.get('grammar_titles', [])]
    if len(all_titles) != len(set(all_titles)):
        stats['skipped'] = len(entries)
        log.error('Grammatikpunkt mehreren Lektionen zugeordnet')
        return stats
    for e, r in results:
        log.info('L%s %-5s Seite %s: +%d Grammatik (%d schon da)%s %s', r['lesson_id'], r['status'],
                 r['page'], len(r['add_grammar']), r['exists'],
                 ' +Ueberleitung' if r['add_intro'] else '', r['reason'])
        if r['status'] == 'SKIP':
            stats['skipped'] += 1
        elif r['status'] == 'SCHON':
            stats['already'] += 1
        else:
            stats['lessons'] += 1
            stats['pages'] += int(r['new_page'])
            stats['items'] += int(r['add_intro']) + len(r['add_grammar'])
    if not apply:
        log.info('DRY-RUN — nichts geschrieben. Mit --apply ausfuehren.')
        return stats
    if stats['skipped'] and not allow_partial:
        log.error('ABBRUCH: SKIPs vorhanden — nichts geschrieben (--allow-partial erzwingt).')
        return stats
    for e, r in results:
        if r['status'] == 'OK':
            write_lesson(e, r)
    db.session.commit()
    stats['written'] = True
    log.info('APPLY OK: %d Lektionen, %d Seiten, %d Items.', stats['lessons'], stats['pages'], stats['items'])
    return stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true', help='wirklich schreiben (sonst DRY-RUN)')
    ap.add_argument('--allow-partial', action='store_true', help='trotz SKIPs schreiben')
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    from app import create_app

    app = create_app()
    with app.app_context():
        stats = apply_plan(load_plan(), apply=args.apply, allow_partial=args.allow_partial)
    log.info('=== %d Lektionen zu aendern, %d schon erledigt, %d SKIP; %d Seiten, %d Items ===',
             stats['lessons'], stats['already'], stats['skipped'], stats['pages'], stats['items'])
    return 1 if stats['skipped'] and not args.allow_partial else 0


if __name__ == '__main__':
    sys.exit(main())
