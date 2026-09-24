"""Kanji 1 (Lektion 164) bekommt eine Rampe — Umbau laut scripts/data/kanji1_rampe.json.

Nur Umsortierung/Aufteilung + neue Kurztexte und Mini-Quizze; nichts wird geloescht,
Bilder bleiben bei ihren Inhalten. Ablauf in EINER Transaktion:
  1. Ist-Zustand exakt pruefen (7 Seiten mit erwarteten IDs, 36 Items auf erwarteten Positionen).
     Schon umgebaut (Draft-Marker vorhanden)? -> nichts tun.
  2. Seiten absteigend verschieben (Unique lesson_id+page_number), neue Seiten 3 und 5 anlegen.
  3. Alle 36 bestehenden Items auf ihre End-Position setzen.
  4. Neue Text-/Quiz-Items + quiz_question/quiz_option einfuegen.

Im Container ausfuehren:
  sudo docker cp scripts/apply_kanji1_rampe.py japanese_app:/tmp/
  sudo docker cp scripts/data/kanji1_rampe.json japanese_app:/tmp/
  sudo docker exec -w /app japanese_app python /tmp/apply_kanji1_rampe.py --spec /tmp/kanji1_rampe.json [--apply]
"""
import argparse
import json
import os
import sys
from pathlib import Path

from sqlalchemy import text

# Repo-Root (bei Aufruf aus scripts/) bzw. Arbeitsverzeichnis (-w /app im Container) importierbar machen
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, os.getcwd())


def q(sql, **params):
    from app import db
    return db.session.execute(text(sql), params)


def check_before(spec):
    lid = spec['lesson_id']
    errors = []
    pages = {str(r.page_number): r.id for r in q(
        'SELECT id, page_number FROM lesson_page WHERE lesson_id=:l', l=lid)}
    if pages != spec['pages_before']:
        errors.append(f'Seiten weichen ab: {pages}')
    content = {str(r.id): [r.page_number, r.order_index] for r in q(
        'SELECT id, page_number, order_index FROM lesson_content WHERE lesson_id=:l', l=lid)}
    if content != spec['content_before']:
        diff = {k: (content.get(k), v) for k, v in spec['content_before'].items() if content.get(k) != v}
        extra = sorted(set(content) - set(spec['content_before']))
        errors.append(f'Items weichen ab: {diff} extra={extra}')
    return errors


def already_done(spec):
    marker = spec['meta']['draft_marker']
    n = q("SELECT count(*) FROM lesson_content WHERE lesson_id=:l "
          "AND ai_generation_details::jsonb->>'draft' = :m", l=spec['lesson_id'], m=marker).scalar()
    return n > 0


def apply(spec):
    lid = spec['lesson_id']
    marker = spec['meta']['draft_marker']
    for page_id, old, new in spec['page_moves']:  # absteigend -> keine Unique-Kollision
        r = q('UPDATE lesson_page SET page_number=:n WHERE id=:i AND lesson_id=:l AND page_number=:o',
              n=new, i=page_id, l=lid, o=old)
        assert r.rowcount == 1, f'lesson_page {page_id} nicht verschoben'
    for p in spec['new_pages']:
        q("INSERT INTO lesson_page (lesson_id, page_number, title, description, page_type) "
          "VALUES (:l, :n, :t, :d, 'normal')", l=lid, n=p['page_number'], t=p['title'], d=p['description'])
    for p in spec['page_updates']:
        r = q('UPDATE lesson_page SET title=:t, description=:d WHERE id=:i AND lesson_id=:l',
              t=p['title'], d=p['description'], i=p['id'], l=lid)
        assert r.rowcount == 1
    for cid, (page, order) in spec['content_layout'].items():
        r = q('UPDATE lesson_content SET page_number=:p, order_index=:o WHERE id=:i AND lesson_id=:l',
              p=page, o=order, i=int(cid), l=lid)
        assert r.rowcount == 1, f'lesson_content {cid} fehlt'
    details = json.dumps({'generator': 'claude', 'draft': marker})
    n_q = 0
    for c in spec['new_content']:
        new_id = q("INSERT INTO lesson_content (lesson_id, content_type, title, content_text, order_index, "
                   "page_number, is_optional, is_interactive, quiz_type, max_attempts, passing_score, "
                   "generated_by_ai, ai_generation_details, created_at) VALUES (:l, 'text', :t, :x, :o, :p, "
                   "false, :ia, 'standard', 3, 70, true, CAST(:d AS json), now()) RETURNING id",
                   l=lid, t=c['title'], x=c['content_text'], o=c['order'], p=c['page'],
                   ia=c['is_interactive'], d=details).scalar()
        print(f"  + lesson_content {new_id} ({c['key']}, Seite {c['page']}, order {c['order']})")
        for qi, qq in enumerate(c['quiz'], start=1):
            qid = q('INSERT INTO quiz_question (lesson_content_id, question_type, question_text, explanation, '
                    'hint, difficulty_level, points, order_index, created_at) VALUES (:c, :ty, :qt, :ex, :h, 1, 1, '
                    ':o, now()) RETURNING id', c=new_id, ty=qq['question_type'], qt=qq['question_text'],
                    ex=qq['explanation'], h=qq['hint'], o=qi).scalar()
            for oi, opt in enumerate(qq['options'], start=1):
                q('INSERT INTO quiz_option (question_id, option_text, is_correct, order_index, feedback) '
                  'VALUES (:q, :t, :c, :o, :f)', q=qid, t=opt['option_text'], c=opt['is_correct'], o=oi,
                  f=opt['feedback'])
            n_q += 1
    return n_q


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--spec', required=True)
    ap.add_argument('--apply', action='store_true', help='wirklich schreiben (sonst DRY-RUN)')
    args = ap.parse_args()
    spec = json.load(open(args.spec, encoding='utf-8'))

    from app import create_app, db
    app = create_app()
    with app.app_context():
        if already_done(spec):
            print('SCHON UMGEBAUT (Draft-Marker vorhanden) — nichts zu tun.')
            return 0
        errors = check_before(spec)
        if errors:
            print('ABBRUCH — Ist-Zustand entspricht nicht der Erwartung:')
            for e in errors:
                print('  ', e)
            return 1
        print('Ist-Zustand OK (7 Seiten, 36 Items wie erwartet).')
        print(f"Plan: {len(spec['page_moves'])} Seiten verschieben, {len(spec['new_pages'])} neue Seiten, "
              f"{len(spec['content_layout'])} Items umsetzen, {len(spec['new_content'])} neue Items, "
              f"{sum(len(c['quiz']) for c in spec['new_content'])} neue Quizfragen.")
        n_q = apply(spec)
        if not args.apply:
            db.session.rollback()
            print(f'DRY-RUN — alles in Transaktion durchgespielt ({n_q} Fragen), ROLLBACK. Mit --apply ausfuehren.')
            return 0
        db.session.commit()
        print(f'APPLY OK: Lektion {spec["lesson_id"]} umgebaut, {n_q} Quizfragen neu.')
        return 0


if __name__ == '__main__':
    sys.exit(main())
