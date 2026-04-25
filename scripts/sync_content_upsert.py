"""
Content-Sync: Lokale DB → Cloud SQL via UPSERT.
Kein TRUNCATE, kein CASCADE, keine User-Daten gehen verloren.

Verwendung:
  PYTHONPATH=. python scripts/sync_content_upsert.py --cloud-host 34.65.56.56 --cloud-password <pw>

Oder mit gcloud:
  DB_PASS=$(gcloud secrets versions access latest --secret=db-password --project=healthy-coil-466105-d7)
  PYTHONPATH=. python scripts/sync_content_upsert.py --cloud-host 34.65.56.56 --cloud-password "$DB_PASS"
"""
import argparse
import sys
import io

# UTF-8 stdout-Wrapping nur beim direkten Script-Aufruf (nicht beim Import in
# Tests, sonst killt es pytest's stdout-Capture).
if __name__ == '__main__':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except (AttributeError, ValueError):
        pass

import psycopg2

from scripts.sync_safety import (
    backup_user_tables,
    collect_snapshot,
    detect_drift,
    find_blocking_user_data,
    load_snapshot,
)

# Content-Tabellen in Reihenfolge (Foreign-Key-Abhängigkeiten beachten)
CONTENT_TABLES = [
    # Unabhängige Tabellen zuerst
    {'name': 'kana', 'pk': 'id'},
    {'name': 'kanji', 'pk': 'id'},
    {'name': 'vocabulary', 'pk': 'id'},
    {'name': 'grammar', 'pk': 'id'},
    {'name': 'lesson_category', 'pk': 'id'},
    # Abhängige Tabellen
    {'name': 'course', 'pk': 'id'},
    {'name': 'lesson', 'pk': 'id'},
    {'name': 'course_lessons', 'pk': ['course_id', 'lesson_id']},  # Composite
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


def sync_table(local_cur, cloud_cur, table_info, allow_user_data_delete=False):
    """Synchronisiert eine Tabelle via UPSERT.

    allow_user_data_delete=False: Wenn ein DELETE auf Cloud-Zeilen User-Daten
    referenziert (siehe DELETION_BLOCKERS), wird ein Fehler geworfen statt
    blind zu loeschen — verhindert stillen Datenverlust bei Race-Conditions.
    """
    table = table_info['name']
    pk = table_info['pk']

    # Spalten ermitteln
    columns = get_columns(local_cur, table)
    if not columns:
        print(f"  {table}: Tabelle nicht gefunden lokal, übersprungen")
        return 0, 0, 0

    # Cloud-Spalten prüfen (Cloud könnte weniger Spalten haben)
    cloud_columns = get_columns(cloud_cur, table)
    if not cloud_columns:
        print(f"  {table}: Tabelle nicht auf Cloud SQL gefunden, übersprungen")
        return 0, 0, 0

    # Nur gemeinsame Spalten synchronisieren
    common_columns = [c for c in columns if c in cloud_columns]
    col_list = ', '.join(f'"{c}"' for c in common_columns)

    # Lokale Daten lesen
    local_cur.execute(f'SELECT {col_list} FROM "{table}"')
    local_rows = local_cur.fetchall()

    if not local_rows:
        print(f"  {table}: 0 Zeilen lokal, übersprungen")
        return 0, 0, 0

    # UPSERT bauen
    if isinstance(pk, list):
        pk_clause = ', '.join(f'"{p}"' for p in pk)
    else:
        pk_clause = f'"{pk}"'

    # Non-PK Spalten für UPDATE SET
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

    # Zeilen auf Cloud einfügen/aktualisieren
    inserted = 0
    for row in local_rows:
        cloud_cur.execute(sql, row)
        if cloud_cur.rowcount > 0:
            inserted += 1

    # Zeilen auf Cloud löschen die lokal nicht mehr existieren
    local_cur.execute(f'SELECT {pk_clause} FROM "{table}"')
    local_pks = set(tuple(row) if isinstance(pk, list) else (row[0],)
                     for row in local_cur.fetchall())

    cloud_cur.execute(f'SELECT {pk_clause} FROM "{table}"')
    cloud_pks = set(tuple(row) if isinstance(pk, list) else (row[0],)
                     for row in cloud_cur.fetchall())

    to_delete = cloud_pks - local_pks
    deleted = 0
    if to_delete:
        # Kaufschutz: Pruefen ob User-Daten auf zu loeschende Cloud-IDs zeigen.
        # Nur fuer Tabellen mit single-column PK (User-FKs zeigen nie auf
        # composite PKs in unserem Schema).
        if not isinstance(pk, list):
            simple_ids = {row[0] for row in to_delete}
            blockers = find_blocking_user_data(cloud_cur, table, simple_ids)
            if blockers and not allow_user_data_delete:
                msg_lines = [
                    f"\nABBRUCH: Lokales Sync wuerde {len(to_delete)} Cloud-Zeile(n) "
                    f"in '{table}' loeschen, auf die User-Daten zeigen:"
                ]
                for user_table, fk_col, ref_id, cnt in blockers:
                    msg_lines.append(
                        f"  - {table}.id={ref_id}: {cnt} Eintrag/Eintraege in "
                        f"{user_table}.{fk_col}"
                    )
                msg_lines.append(
                    "\nMoegliche Ursachen:"
                    "\n  1. Cloud-Admin hat seit dem letzten Pull neue Inhalte angelegt."
                    "\n  2. Lokale Inhalte wurden geloescht, aber Produktion hat User-Daten."
                    "\nAktionen:"
                    "\n  - Erneut /sync-cloud-db (Cloud->Lokal) ausfuehren, dann pushen."
                    "\n  - Oder explizit --force-delete-user-data setzen "
                    "(Datenverlust akzeptiert)."
                )
                raise RuntimeError("\n".join(msg_lines))

        for pk_val in to_delete:
            if isinstance(pk, list):
                where = ' AND '.join(
                    f'"{p}" = %s' for p in pk
                )
            else:
                where = f'"{pk}" = %s'
            cloud_cur.execute(f'DELETE FROM "{table}" WHERE {where}', pk_val)
            deleted += 1

    return len(local_rows), inserted, deleted


def update_sequences(cloud_cur):
    """Aktualisiert Auto-Increment-Sequences."""
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
        cloud_cur.execute(
            f"SELECT setval('{seq}', COALESCE((SELECT MAX(id) FROM \"{table}\"), 1))"
        )


def main():
    parser = argparse.ArgumentParser(description='Content-Sync via UPSERT')
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
    parser.add_argument('--skip-drift-check', action='store_true',
                        help='Drift-Check ueberspringen (NICHT empfohlen)')
    parser.add_argument('--skip-backup', action='store_true',
                        help='User-Daten-Backup ueberspringen (NICHT empfohlen)')
    parser.add_argument('--force-delete-user-data', action='store_true',
                        help='Cloud-Zeilen auch dann loeschen, wenn User-Daten '
                             'darauf zeigen (Datenverlust akzeptiert)')
    args = parser.parse_args()

    print("Verbinde mit lokaler DB...")
    local_conn = psycopg2.connect(
        host=args.local_host, port=args.local_port,
        user=args.local_user, password=args.local_password,
        dbname=args.local_db
    )
    local_cur = local_conn.cursor()

    print("Verbinde mit Cloud SQL...")
    cloud_conn = psycopg2.connect(
        host=args.cloud_host, port=args.cloud_port,
        user=args.cloud_user, password=args.cloud_password,
        dbname=args.cloud_db
    )
    cloud_conn.autocommit = False
    cloud_cur = cloud_conn.cursor()

    # === DRIFT-CHECK ===
    # Vergleicht aktuellen Cloud-Stand mit dem Snapshot vom letzten Pull.
    # Wenn Cloud sich seit dem Pull geaendert hat (Admin-Edit), wuerde der
    # Push diese Aenderungen ueberschreiben oder Loeschen ausloesen.
    if not args.skip_drift_check:
        print("\n--- Drift-Check ---")
        snapshot_data = load_snapshot()
        if not snapshot_data:
            print("  KEIN Cloud-Snapshot gefunden (.last_cloud_sync.json).")
            print("  Bitte erst Cloud->Lokal synchronisieren:")
            print("    python scripts/sync_from_cloud.py --cloud-host ... --cloud-password ...")
            print("  Oder mit --skip-drift-check ueberspringen (NICHT empfohlen).")
            sys.exit(2)

        snap_tables = [t['name'] for t in CONTENT_TABLES]
        current_cloud = collect_snapshot(cloud_cur, snap_tables)
        diffs = detect_drift(snapshot_data['snapshot'], current_cloud)
        if diffs:
            print("  WARNUNG: Cloud hat sich seit dem letzten Pull geaendert!")
            print(f"  Snapshot vom: {snapshot_data['taken_at']}")
            for d in diffs:
                print(d)
            print("\n  Empfehlung: Cloud->Lokal erneut ziehen, dann pushen.")
            print("  Mit --skip-drift-check ueberspringen falls bewusst.")
            sys.exit(2)
        print(f"  OK — Cloud-Stand identisch zum Snapshot vom "
              f"{snapshot_data['taken_at']}")

    # === USER-DATEN-BACKUP ===
    # pg_dump aller User-Tabellen vor jedem Push — Insurance gegen Bugs.
    if not args.skip_backup and not args.dry_run:
        print("\n--- User-Daten-Backup (Cloud) ---")
        backup_user_tables(
            host=args.cloud_host, port=args.cloud_port,
            user=args.cloud_user, password=args.cloud_password,
            db=args.cloud_db, label='cloud_pre_push',
        )

    print("\n--- Content-Sync (UPSERT) ---\n")
    print(f"{'Tabelle':<22} {'Lokal':>6} {'Upsert':>7} {'Gelöscht':>9}")
    print("-" * 48)

    total_upsert = 0
    total_deleted = 0
    try:
        for table_info in CONTENT_TABLES:
            rows, upserted, deleted = sync_table(
                local_cur, cloud_cur, table_info,
                allow_user_data_delete=args.force_delete_user_data,
            )
            total_upsert += upserted
            total_deleted += deleted
            print(f"  {table_info['name']:<20} {rows:>6} {upserted:>7} {deleted:>9}")

        # Sequences aktualisieren
        update_sequences(cloud_cur)

        # Alembic-Version synchronisieren
        local_cur.execute("SELECT version_num FROM alembic_version")
        local_ver = local_cur.fetchone()
        if local_ver:
            cloud_cur.execute("DELETE FROM alembic_version")
            cloud_cur.execute(
                "INSERT INTO alembic_version (version_num) VALUES (%s)",
                (local_ver[0],)
            )
            print(f"\nAlembic: {local_ver[0]}")

        if args.dry_run:
            cloud_conn.rollback()
            print("\n[DRY RUN] Keine Änderungen geschrieben.")
        else:
            cloud_conn.commit()
            print(f"\nErfolgreich: {total_upsert} upserts, {total_deleted} gelöscht.")

    except Exception as e:
        cloud_conn.rollback()
        print(f"\nFEHLER: {e}")
        print("Rollback durchgeführt — keine Änderungen auf Cloud SQL.")
        sys.exit(1)
    finally:
        local_cur.close()
        local_conn.close()
        cloud_cur.close()
        cloud_conn.close()


if __name__ == '__main__':
    main()
