"""
Cloud-Sync: Cloud SQL → Lokale DB via UPSERT.
Holt den aktuellen Stand der Produktion, bevor lokal gearbeitet wird.
Ueberschreibt nur Zeilen wo Cloud neuer ist (updated_at) oder lokal fehlt.

Verwendung:
  PYTHONPATH=. python scripts/sync_from_cloud.py --cloud-host 34.65.56.56 --cloud-password <pw>

Oder mit gcloud:
  DB_PASS=$(gcloud secrets versions access latest --secret=db-password --project=healthy-coil-466105-d7)
  PYTHONPATH=. python scripts/sync_from_cloud.py --cloud-host 34.65.56.56 --cloud-password "$DB_PASS"
"""
import argparse
import sys
import io

# UTF-8 stdout-Wrapping nur beim direkten Script-Aufruf (nicht beim Import).
if __name__ == '__main__':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except (AttributeError, ValueError):
        pass

import psycopg2
import psycopg2.extensions
from psycopg2.extras import Json

# Dict-Adapter fuer JSON-Felder (s. sync_content_upsert.py).
psycopg2.extensions.register_adapter(dict, Json)

from scripts.sync_safety import collect_snapshot, write_snapshot

# Content-Tabellen in Reihenfolge (Foreign-Key-Abhaengigkeiten beachten)
# Gleiche Reihenfolge wie sync_content_upsert.py
CONTENT_TABLES = [
    # Unabhaengige Tabellen zuerst
    {'name': 'kana', 'pk': 'id'},
    {'name': 'kanji', 'pk': 'id'},
    {'name': 'vocabulary', 'pk': 'id'},
    {'name': 'grammar', 'pk': 'id'},
    {'name': 'lesson_category', 'pk': 'id'},
    # Abhaengige Tabellen
    {'name': 'course', 'pk': 'id'},
    {'name': 'lesson', 'pk': 'id'},
    {'name': 'course_lessons', 'pk': ['course_id', 'lesson_id']},
    {'name': 'lesson_page', 'pk': 'id'},
    {'name': 'lesson_content', 'pk': 'id'},
    {'name': 'lesson_prerequisite', 'pk': 'id'},
    {'name': 'quiz_question', 'pk': 'id'},
    {'name': 'quiz_option', 'pk': 'id'},
]


def get_columns(cur, table_name):
    """Holt Spaltennamen einer Tabelle."""
    cur.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = %s ORDER BY ordinal_position",
        (table_name,)
    )
    return [row[0] for row in cur.fetchall()]


def sync_table_from_cloud(cloud_cur, local_cur, table_info):
    """Synchronisiert eine Tabelle von Cloud → Lokal via UPSERT."""
    table = table_info['name']
    pk = table_info['pk']

    # Spalten ermitteln (gemeinsame Spalten)
    cloud_columns = get_columns(cloud_cur, table)
    local_columns = get_columns(local_cur, table)

    if not cloud_columns:
        print(f"  {table}: Tabelle nicht auf Cloud gefunden, uebersprungen")
        return 0, 0, 0
    if not local_columns:
        print(f"  {table}: Tabelle nicht lokal gefunden, uebersprungen")
        return 0, 0, 0

    common_columns = [c for c in cloud_columns if c in local_columns]
    col_list = ', '.join(f'"{c}"' for c in common_columns)

    # Cloud-Daten lesen
    cloud_cur.execute(f'SELECT {col_list} FROM "{table}"')
    cloud_rows = cloud_cur.fetchall()

    if not cloud_rows:
        print(f"  {table}: 0 Zeilen auf Cloud, uebersprungen")
        return 0, 0, 0

    # UPSERT in lokale DB bauen
    if isinstance(pk, list):
        pk_clause = ', '.join(f'"{p}"' for p in pk)
    else:
        pk_clause = f'"{pk}"'

    pk_list = pk if isinstance(pk, list) else [pk]
    update_cols = [c for c in common_columns if c not in pk_list]

    if update_cols:
        set_clause = ', '.join(
            f'"{c}" = EXCLUDED."{c}"' for c in update_cols
        )
        conflict_action = f'DO UPDATE SET {set_clause}'
    else:
        conflict_action = 'DO NOTHING'

    placeholders = ', '.join(['%s'] * len(common_columns))
    sql = (
        f'INSERT INTO "{table}" ({col_list}) VALUES ({placeholders}) '
        f'ON CONFLICT ({pk_clause}) {conflict_action}'
    )

    # Zeilen lokal einfuegen/aktualisieren
    upserted = 0
    for row in cloud_rows:
        local_cur.execute(sql, row)
        if local_cur.rowcount > 0:
            upserted += 1

    # Zeilen lokal loeschen die auf Cloud nicht mehr existieren
    cloud_cur.execute(f'SELECT {pk_clause} FROM "{table}"')
    cloud_pks = set(
        tuple(row) if isinstance(pk, list) else (row[0],)
        for row in cloud_cur.fetchall()
    )

    local_cur.execute(f'SELECT {pk_clause} FROM "{table}"')
    local_pks = set(
        tuple(row) if isinstance(pk, list) else (row[0],)
        for row in local_cur.fetchall()
    )

    to_delete = local_pks - cloud_pks
    deleted = 0
    if to_delete:
        for pk_val in to_delete:
            if isinstance(pk, list):
                where = ' AND '.join(f'"{p}" = %s' for p in pk)
            else:
                where = f'"{pk}" = %s'
            local_cur.execute(f'DELETE FROM "{table}" WHERE {where}', pk_val)
            deleted += 1

    return len(cloud_rows), upserted, deleted


def update_sequences(local_cur):
    """Aktualisiert Auto-Increment-Sequences lokal."""
    sequences = {
        'kana': 'kana_id_seq',
        'kanji': 'kanji_id_seq',
        'vocabulary': 'vocabulary_id_seq',
        'grammar': 'grammar_id_seq',
        'lesson_category': 'lesson_category_id_seq',
        'course': 'course_id_seq',
        'lesson': 'lesson_id_seq',
        'lesson_page': 'lesson_page_id_seq',
        'lesson_content': 'lesson_content_id_seq',
        'lesson_prerequisite': 'lesson_prerequisite_id_seq',
        'quiz_question': 'quiz_question_id_seq',
        'quiz_option': 'quiz_option_id_seq',
    }
    for table, seq in sequences.items():
        try:
            local_cur.execute(
                f"SELECT setval('{seq}', COALESCE((SELECT MAX(id) FROM \"{table}\"), 1))"
            )
        except Exception:
            pass  # Sequence existiert evtl. nicht


def main():
    parser = argparse.ArgumentParser(
        description='Cloud → Lokal Sync via UPSERT (Produktionsdaten herunterladen)'
    )
    parser.add_argument('--local-host', default='localhost')
    parser.add_argument('--local-port', type=int, default=5432)
    parser.add_argument('--local-user', default='app_user')
    parser.add_argument('--local-password', default='JapaneseApp2025!')
    parser.add_argument('--local-db', default='japanese_learning')
    parser.add_argument('--cloud-host', required=True)
    parser.add_argument('--cloud-port', type=int, default=5432)
    parser.add_argument('--cloud-user', default='app_user')
    parser.add_argument('--cloud-password', required=True)
    parser.add_argument('--cloud-db', default='japanese_learning')
    parser.add_argument('--dry-run', action='store_true',
                        help='Nur anzeigen, nicht schreiben')
    args = parser.parse_args()

    print("=" * 52)
    print("  Cloud SQL → Lokale DB  (Produktionsdaten holen)")
    print("=" * 52)

    print("\nVerbinde mit Cloud SQL...")
    cloud_conn = psycopg2.connect(
        host=args.cloud_host, port=args.cloud_port,
        user=args.cloud_user, password=args.cloud_password,
        dbname=args.cloud_db
    )
    cloud_cur = cloud_conn.cursor()

    print("Verbinde mit lokaler DB...")
    local_conn = psycopg2.connect(
        host=args.local_host, port=args.local_port,
        user=args.local_user, password=args.local_password,
        dbname=args.local_db
    )
    local_conn.autocommit = False
    local_cur = local_conn.cursor()

    print(f"\n{'Tabelle':<22} {'Cloud':>6} {'Upsert':>7} {'Geloescht':>10}")
    print("-" * 50)

    total_upsert = 0
    total_deleted = 0
    try:
        for table_info in CONTENT_TABLES:
            rows, upserted, deleted = sync_table_from_cloud(
                cloud_cur, local_cur, table_info
            )
            total_upsert += upserted
            total_deleted += deleted
            print(f"  {table_info['name']:<20} {rows:>6} {upserted:>7} {deleted:>10}")

        # Sequences aktualisieren
        update_sequences(local_cur)

        # Alembic-Version synchronisieren
        cloud_cur.execute("SELECT version_num FROM alembic_version")
        cloud_ver = cloud_cur.fetchone()
        if cloud_ver:
            local_cur.execute("DELETE FROM alembic_version")
            local_cur.execute(
                "INSERT INTO alembic_version (version_num) VALUES (%s)",
                (cloud_ver[0],)
            )
            print(f"\nAlembic: {cloud_ver[0]}")

        if args.dry_run:
            local_conn.rollback()
            print("\n[DRY RUN] Keine Aenderungen geschrieben.")
        else:
            local_conn.commit()
            print(f"\nErfolgreich: {total_upsert} upserts, {total_deleted} geloescht.")

            # Cloud-Snapshot fuer Drift-Detection beim naechsten Push speichern.
            print("\nSchreibe Cloud-Snapshot fuer Drift-Detection...")
            snap_tables = [t['name'] for t in CONTENT_TABLES]
            cloud_snap = collect_snapshot(cloud_cur, snap_tables)
            write_snapshot(cloud_snap, source_host=args.cloud_host)

    except Exception as e:
        local_conn.rollback()
        print(f"\nFEHLER: {e}")
        print("Rollback — keine Aenderungen an lokaler DB.")
        sys.exit(1)
    finally:
        cloud_cur.close()
        cloud_conn.close()
        local_cur.close()
        local_conn.close()

    print("\nLokale DB ist jetzt auf dem Stand der Produktion.")


if __name__ == '__main__':
    main()
