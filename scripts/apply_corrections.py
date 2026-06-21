"""Wendet verifizierte Audit-Korrektur-Specs sicher auf die DB an.

Selbst-schuetzend: holt den aktuellen DB-Wert und entscheidet pro Spec:
  - Spalte enthaelt Komma  -> MULTI-Spalten-Modus (new_value = JSON), Ist via JSON-current verifizieren.
  - sonst SINGLE-Spalte: DB==current_value -> Voll-Ersatz; current_value genau 1x als Substring -> ersetzen;
    sonst SKIP (Mismatch -> nie blind schreiben).
Dedupe ueber (table, pk, column). --dry-run zeigt alt->neu; --apply schreibt in EINER Transaktion.

Im Container ausfuehren:
  sudo docker cp scripts/apply_corrections.py japanese_app:/tmp/
  sudo docker cp scripts/data/lesson_audit/correction_specs.json japanese_app:/tmp/
  sudo docker exec japanese_app python /tmp/apply_corrections.py --specs /tmp/correction_specs.json [--apply]
"""
import argparse
import json
import re
import sys

from sqlalchemy import text

from app import create_app, db

ALLOWED = {
    'vocabulary': {'word', 'reading', 'romaji', 'meaning', 'meaning_de', 'jlpt_level',
                   'example_sentence_japanese', 'example_sentence_english'},
    'quiz_question': {'question_text', 'explanation', 'hint'},
    'quiz_option': {'option_text', 'is_correct', 'feedback'},
    'kanji': {'jlpt_level', 'meaning', 'onyomi', 'kunyomi'},
    'grammar': {'explanation', 'example_sentences', 'structure', 'nuance', 'title'},
    'lesson_content': {'content_text', 'title'},
    'lesson': {'description', 'title'},
}
INT_COLS = {'jlpt_level'}
BOOL_COLS = {'is_correct'}


def pk_int(pk):
    m = re.findall(r'\d+', str(pk))
    return int(m[-1]) if m else None


def coerce(col, val):
    if col in INT_COLS and val is not None:
        return int(val)
    if col in BOOL_COLS and val is not None:
        return bool(val)
    return val


def fetch(table, pk, cols):
    sel = ', '.join(cols)
    row = db.session.execute(text(f"SELECT {sel} FROM {table} WHERE id=:id"), {'id': pk}).fetchone()
    return dict(zip(cols, row)) if row else None


def update(table, pk, newvals):
    sets = ', '.join(f"{c}=:{c}" for c in newvals)
    params = {c: coerce(c, v) for c, v in newvals.items()}
    params['id'] = pk
    res = db.session.execute(text(f"UPDATE {table} SET {sets} WHERE id=:id"), params)
    return res.rowcount


def plan_one(s):
    """Gibt (status, table, pk, {col: (old, new)}) zurueck; status: ok|skip:<grund>."""
    table, col_spec = s['table'], s.get('column', '')
    pk = pk_int(s.get('pk'))
    if table not in ALLOWED or pk is None or not col_spec:
        return ('skip:unlokalisierbar', table, pk, {})
    cols = [c.strip() for c in col_spec.split(',')]
    for c in cols:
        if c not in ALLOWED[table]:
            return (f'skip:spalte_{c}_nicht_erlaubt', table, pk, {})

    if len(cols) > 1:  # MULTI-Spalte: new_value = JSON
        try:
            newj = json.loads(s['new_value'])
            curj = json.loads(s['current_value'])
        except Exception:
            return ('skip:multi_kein_json', table, pk, {})
        dbrow = fetch(table, pk, cols)
        if dbrow is None:
            return ('skip:zeile_fehlt', table, pk, {})
        # Verifikation: jede in current angegebene Spalte muss dem DB-Ist entsprechen
        for c in cols:
            if c in curj and curj[c] is not None and str(dbrow.get(c)) != str(curj[c]):
                return (f'skip:mismatch_{c}', table, pk, {})
        changes = {c: (dbrow.get(c), newj[c]) for c in cols if c in newj and str(dbrow.get(c)) != str(newj[c])}
        return ('ok', table, pk, changes) if changes else ('skip:keine_aenderung', table, pk, {})

    # SINGLE-Spalte: adaptiv
    col = cols[0]
    dbrow = fetch(table, pk, [col])
    if dbrow is None:
        return ('skip:zeile_fehlt', table, pk, {})
    cur = dbrow[col]
    cur_s = '' if cur is None else str(cur)
    want = str(s['current_value'])
    new = str(s['new_value'])
    if cur_s.strip() == want.strip():
        return ('ok', table, pk, {col: (cur, new)})
    if want and cur_s.count(want) == 1:
        return ('ok', table, pk, {col: (cur, cur_s.replace(want, new))})
    return ('skip:ist_nicht_gefunden', table, pk, {})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--specs', required=True)
    ap.add_argument('--apply', action='store_true', help='wirklich schreiben (sonst DRY-RUN)')
    args = ap.parse_args()
    specs = [s for s in json.load(open(args.specs, encoding='utf-8'))
             if s.get('apply') and s.get('verified')]

    app = create_app()
    with app.app_context():
        seen, ok, skipped = set(), [], []
        for s in specs:
            status, table, pk, changes = plan_one(s)
            key = (table, pk, s.get('column'))
            if status == 'ok' and key in seen:
                status = 'skip:dublette'
            if status == 'ok':
                seen.add(key)
                ok.append((s['finding'], table, pk, changes))
            else:
                skipped.append((s['finding'], status, table, pk))

        print(f"=== PLAN: {len(ok)} anwendbar, {len(skipped)} uebersprungen ===\n")
        for finding, table, pk, changes in ok:
            print(f"[{finding}] {table}#{pk}")
            for c, (old, new) in changes.items():
                os_, ns = (str(old) or '')[:70].replace('\n', ' '), str(new)[:70].replace('\n', ' ')
                print(f"    {c}:\n      ALT: {os_}\n      NEU: {ns}")
        if skipped:
            print("\n--- UEBERSPRUNGEN ---")
            for finding, status, table, pk in skipped:
                print(f"  [{finding}] {status} ({table}#{pk})")

        if not args.apply:
            print("\nDRY-RUN — nichts geschrieben. Mit --apply ausfuehren.")
            return 0

        n = 0
        for finding, table, pk, changes in ok:
            newvals = {c: new for c, (old, new) in changes.items()}
            n += update(table, pk, newvals)
        db.session.commit()
        print(f"\nAPPLY OK: {len(ok)} Specs, {n} Zeilen-Updates committed.")
        return 0


if __name__ == '__main__':
    sys.exit(main())
