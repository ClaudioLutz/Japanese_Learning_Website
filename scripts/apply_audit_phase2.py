"""Audit Phase 2 (2026-09-24): Rest-Korrekturen aus docs/lektions-audit-report.md anwenden.

Liest scripts/data/audit_phase2_fixes.json (Feld ``ops``). Jede Op ist eine exakte
Vorher/Nachher-Ersetzung auf genau einer Spalte einer Zeile:

  mode=full    DB-Wert muss exakt ``old`` sein  -> wird ``new``
  mode=substr  ``old`` muss genau 1x im DB-Wert vorkommen -> durch ``new`` ersetzt

Selbst-schuetzend: ist ``old`` nicht (mehr) da, aber ``new`` schon, gilt die Op als
bereits angewendet (idempotent). Sonst SKIP mit Grund — nie blind schreiben.
mode=full funktioniert auch fuer Integer-Spalten (z.B. vocabulary.jlpt_level).

Wird ``lesson_content.content_text`` geaendert und hat die Zeile ein vorberechnetes
``ai_generation_details.augmented_html`` (Klick-Audio-HTML), wird dieses im selben
Lauf auf NULL gesetzt, sonst rendert lesson_view.html weiter den alten Text.
Danach pregenerate_inline_audio.py fuer die Lektion nachziehen.
Mehrere Ops auf derselben Zelle werden der Reihe nach im Speicher angewendet und
als EIN UPDATE geschrieben. Alles in EINER Transaktion; bei irgendeinem Mismatch
wird mit --apply nichts geschrieben (ausser --allow-partial).

Im Container ausfuehren (DATABASE_URL zeigt dort auf den Service-Host ``db``):
  sudo docker cp scripts/apply_audit_phase2.py japanese_app:/tmp/
  sudo docker cp scripts/data/audit_phase2_fixes.json japanese_app:/tmp/
  sudo docker exec -w /app japanese_app python /tmp/apply_audit_phase2.py --fixes /tmp/audit_phase2_fixes.json [--apply]
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

ALLOWED = {
    'vocabulary': {'example_sentence_japanese', 'example_sentence_english', 'jlpt_level'},
    'quiz_question': {'question_text', 'explanation', 'hint'},
    'quiz_option': {'option_text', 'feedback'},
    'lesson_content': {'content_text', 'title'},
    'lesson': {'description'},
}


def plan(ops, fetch):
    """Gibt (cells, report) zurueck. cells: {(table, pk, col): (alt, neu)}."""
    cells, report = {}, []
    for op in ops:
        t, pk, col = op['table'], int(op['pk']), op['column']
        if col not in ALLOWED.get(t, set()):
            report.append((op['id'], 'SKIP', f'{t}.{col} nicht erlaubt'))
            continue
        key = (t, pk, col)
        if key in cells:
            orig, cur = cells[key]
        else:
            orig = fetch(t, pk, col)
            if orig is None:
                report.append((op['id'], 'SKIP', f'{t}#{pk} fehlt/NULL'))
                continue
            cur = orig
        old, new = op['old'], op['new']
        if op.get('mode') == 'full':
            if cur == old:
                cur = new
                status = 'OK'
            elif cur == new:
                status = 'SCHON'
            else:
                report.append((op['id'], 'SKIP', f'{t}#{pk}.{col}: Ist-Wert weicht ab'))
                continue
        elif not isinstance(cur, str):
            report.append((op['id'], 'SKIP', f'{t}#{pk}.{col}: substr nur fuer Text'))
            continue
        else:
            n = cur.count(old)
            if new in cur and (old in new or n == 0):
                status = 'SCHON'
            elif n == 1:
                cur = cur.replace(old, new)
                status = 'OK'
            else:
                report.append((op['id'], 'SKIP', f'{t}#{pk}.{col}: old {n}x gefunden'))
                continue
        cells[key] = (orig, cur)
        report.append((op['id'], status, f'{t}#{pk}.{col}'))
    return cells, report


def clear_augmented(details):
    """Gibt (neue_details, geaendert) zurueck; setzt augmented_html auf None."""
    if isinstance(details, str):
        details = json.loads(details) if details else None
    if not isinstance(details, dict) or not details.get('augmented_html'):
        return details, False
    return dict(details, augmented_html=None), True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--fixes', required=True)
    ap.add_argument('--apply', action='store_true', help='wirklich schreiben (sonst DRY-RUN)')
    ap.add_argument('--allow-partial', action='store_true', help='trotz SKIPs schreiben')
    args = ap.parse_args()
    data = json.load(open(args.fixes, encoding='utf-8'))
    ops = data['ops']

    from app import create_app, db

    def fetch(t, pk, col):
        row = db.session.execute(text(f'SELECT {col} FROM {t} WHERE id=:id'), {'id': pk}).fetchone()
        return row[0] if row else None

    app = create_app()
    with app.app_context():
        cells, report = plan(ops, fetch)
        by_id = {o['id']: o for o in ops}
        for oid, st, info in report:
            o = by_id[oid]
            print(f"[{oid}] {st:5} P{o['prio']} {o['audit_ref']:22} {info}")
            if st == 'OK':
                print(f"        ALT: {str(o['old'])[:110]!r}\n        NEU: {str(o['new'])[:110]!r}")
        skips = [r for r in report if r[1] == 'SKIP']
        changed = {k: v for k, v in cells.items() if v[0] != v[1]}
        aug_ids = sorted({pk for (t, pk, col) in changed
                          if t == 'lesson_content' and col == 'content_text'
                          and clear_augmented(fetch(t, pk, 'ai_generation_details'))[1]})
        if aug_ids:
            print(f'augmented_html -> NULL fuer lesson_content {aug_ids}')
        print(f"\n=== {len(ops)} Ops: {sum(r[1] == 'OK' for r in report)} OK, "
              f"{sum(r[1] == 'SCHON' for r in report)} schon angewendet, {len(skips)} SKIP; "
              f"{len(changed)} Zellen zu schreiben ===")

        if not args.apply:
            print('DRY-RUN — nichts geschrieben. Mit --apply ausfuehren.')
            return 0
        if skips and not args.allow_partial:
            print('ABBRUCH: SKIPs vorhanden — nichts geschrieben (--allow-partial erzwingt).')
            return 1
        n = 0
        for (t, pk, col), (orig, new) in changed.items():
            res = db.session.execute(
                text(f'UPDATE {t} SET {col}=:new WHERE id=:id AND {col}=:orig'),
                {'new': new, 'id': pk, 'orig': orig})
            if res.rowcount != 1:
                db.session.rollback()
                print(f'ROLLBACK: {t}#{pk}.{col} hat sich waehrenddessen geaendert.')
                return 1
            n += 1
        for pk in aug_ids:
            details, _ = clear_augmented(fetch('lesson_content', pk, 'ai_generation_details'))
            db.session.execute(
                text('UPDATE lesson_content SET ai_generation_details=:d WHERE id=:id'),
                {'d': json.dumps(details, ensure_ascii=False), 'id': pk})
        db.session.commit()
        print(f'APPLY OK: {n} Zellen committed.')
        return 0


if __name__ == '__main__':
    sys.exit(main())
