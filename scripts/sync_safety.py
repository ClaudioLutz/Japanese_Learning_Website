"""
Sync-Safety-Helpers: Drift-Detection, Kaufschutz-Check, User-Daten-Backup.

Wird von sync_from_cloud.py und sync_content_upsert.py genutzt, um
Datenverlust auf der Cloud-DB beim Push neuer Lektionen zu verhindern.
"""
from __future__ import annotations

import datetime
import json
import os
import subprocess
from pathlib import Path
from typing import Iterable

# Snapshot-Datei: nach erfolgreichem Cloud->Lokal-Pull geschrieben,
# vor Lokal->Cloud-Push gelesen. Dient als Drift-Detector.
SNAPSHOT_PATH = Path('.last_cloud_sync.json')

# Backup-Verzeichnis fuer User-Daten-Dumps (Cloud).
BACKUP_DIR = Path('backups/user_data')

# User-Tabellen, die NIE synchronisiert werden — vor jedem Push gesichert.
USER_TABLES = [
    'user',
    'user_lesson_progress',
    'user_quiz_answer',
    'card_review_state',
    'review_log',
    'user_srs_settings',
    'user_achievement',
    'daily_review_aggregate',
    'lesson_purchase',
    'course_purchase',
    'payment_transaction',
]

# Tabellen, fuer die ein "deletion-blocker"-Check gemacht wird:
# Wenn lokal eine Zeile fehlt, aber auf Cloud eine User-FK darauf zeigt,
# wird der Sync abgebrochen statt CASCADE-loeschen oder rollbacken.
# Schluessel: zu loeschende Cloud-Tabelle. Wert: Liste von (User-Tabelle, FK-Spalte).
DELETION_BLOCKERS: dict[str, list[tuple[str, str]]] = {
    'lesson': [
        ('user_lesson_progress', 'lesson_id'),
        ('lesson_purchase', 'lesson_id'),
    ],
    'course': [
        ('course_purchase', 'course_id'),
    ],
    'lesson_content': [
        ('card_review_state', 'content_id'),
        ('review_log', 'content_id'),
    ],
    'quiz_question': [
        ('user_quiz_answer', 'question_id'),
    ],
    'quiz_option': [
        ('user_quiz_answer', 'selected_option_id'),
    ],
}


# ---------- Snapshot / Drift-Detection ----------

# Tabellen ohne id-Spalte (Composite PKs etc.) — Drift wird via COUNT(*) erkannt.
_TABLES_WITHOUT_ID = {'course_lessons'}


def _drift_query(table: str) -> str:
    """SQL fuer Drift-Marker pro Tabelle.

    Tabellen mit `updated_at` liefern (count, max(id), max(updated_at)).
    Tabellen ohne `updated_at` liefern (count, max(id), NULL).
    Junction-Tabellen ohne `id`-Spalte liefern (count, 0, NULL).
    """
    if table in _TABLES_WITHOUT_ID:
        return f'SELECT COUNT(*)::bigint, 0::bigint, NULL::timestamp FROM "{table}"'
    if table in ('lesson', 'course', 'card_review_state', 'payment_transaction'):
        return (
            f'SELECT COUNT(*)::bigint, COALESCE(MAX(id),0)::bigint, '
            f'MAX(updated_at) FROM "{table}"'
        )
    return (
        f'SELECT COUNT(*)::bigint, COALESCE(MAX(id),0)::bigint, NULL::timestamp '
        f'FROM "{table}"'
    )


def collect_snapshot(cur, tables: Iterable[str]) -> dict:
    """Sammelt Drift-Marker fuer Liste von Tabellen.

    Nutzt Savepoints, damit ein Fehler bei einer Tabelle nicht die ganze
    Transaktion abortet (Postgres: nach Error muss SAVEPOINT zurueckgerollt
    werden, sonst werden alle weiteren Queries auf der Connection mit
    'current transaction is aborted' abgewiesen).
    """
    snap: dict[str, dict] = {}
    for i, table in enumerate(tables):
        sp_name = f'sp_drift_{i}'
        try:
            cur.execute(f'SAVEPOINT {sp_name}')
            cur.execute(_drift_query(table))
            row = cur.fetchone()
            count, max_id, max_updated = row
            snap[table] = {
                'count': int(count),
                'max_id': int(max_id),
                'max_updated_at': max_updated.isoformat() if max_updated else None,
            }
            cur.execute(f'RELEASE SAVEPOINT {sp_name}')
        except Exception as exc:
            try:
                cur.execute(f'ROLLBACK TO SAVEPOINT {sp_name}')
                cur.execute(f'RELEASE SAVEPOINT {sp_name}')
            except Exception:
                pass
            snap[table] = {'error': str(exc)}
    return snap


def write_snapshot(snap: dict, source_host: str) -> None:
    """Schreibt Cloud-Snapshot in .last_cloud_sync.json."""
    payload = {
        'taken_at': datetime.datetime.utcnow().isoformat() + 'Z',
        'source_host': source_host,
        'snapshot': snap,
    }
    SNAPSHOT_PATH.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding='utf-8',
    )
    print(f"  Snapshot geschrieben: {SNAPSHOT_PATH}")


def load_snapshot() -> dict | None:
    if not SNAPSHOT_PATH.exists():
        return None
    return json.loads(SNAPSHOT_PATH.read_text(encoding='utf-8'))


def detect_drift(saved: dict, current: dict) -> list[str]:
    """Vergleicht gespeicherten Snapshot (vom letzten Pull) mit aktuellem
    Cloud-Stand. Gibt Liste menschenlesbarer Diffs zurueck."""
    diffs: list[str] = []
    for table, current_row in current.items():
        if 'error' in current_row:
            continue
        saved_row = saved.get(table)
        if not saved_row or 'error' in saved_row:
            diffs.append(f"  {table}: kein gespeicherter Snapshot")
            continue
        for key in ('count', 'max_id', 'max_updated_at'):
            if saved_row.get(key) != current_row.get(key):
                diffs.append(
                    f"  {table}.{key}: snapshot={saved_row.get(key)!r} "
                    f"-> jetzt={current_row.get(key)!r}"
                )
    return diffs


# ---------- Kaufschutz / Deletion-Blocker ----------

def find_blocking_user_data(
    cloud_cur, table: str, ids_to_delete: set,
) -> list[tuple[str, str, int, int]]:
    """Prueft fuer eine Liste von zu loeschenden Cloud-IDs, ob User-Daten
    darauf zeigen.

    Liefert Liste von (user_table, fk_column, ref_id, count).
    Nur Tabellen aus DELETION_BLOCKERS werden geprueft.
    """
    if not ids_to_delete:
        return []
    findings: list[tuple[str, str, int, int]] = []
    for user_table, fk_col in DELETION_BLOCKERS.get(table, []):
        try:
            ids_list = list(ids_to_delete)
            cloud_cur.execute(
                f'SELECT "{fk_col}", COUNT(*) FROM "{user_table}" '
                f'WHERE "{fk_col}" = ANY(%s) GROUP BY "{fk_col}"',
                (ids_list,),
            )
            for ref_id, cnt in cloud_cur.fetchall():
                findings.append((user_table, fk_col, int(ref_id), int(cnt)))
        except Exception as exc:
            print(f"  WARN: Kaufschutz-Check fuer {table}->{user_table} "
                  f"fehlgeschlagen: {exc}")
    return findings


# ---------- User-Daten-Backup ----------

def backup_user_tables(
    host: str, port: int, user: str, password: str, db: str,
    label: str = 'cloud',
) -> Path | None:
    """Erstellt pg_dump-Backup nur der User-Tabellen.

    Schreibt nach backups/user_data/{label}_{timestamp}.sql
    Gibt Pfad zurueck, oder None wenn pg_dump nicht verfuegbar.
    """
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    out = BACKUP_DIR / f'{label}_{ts}.sql'

    args = [
        'pg_dump',
        f'--host={host}',
        f'--port={port}',
        f'--username={user}',
        f'--dbname={db}',
        '--data-only',
        '--no-owner',
        '--no-privileges',
        '--column-inserts',
    ]
    for tbl in USER_TABLES:
        args.append(f'--table={tbl}')
    args.append(f'--file={out}')

    env = os.environ.copy()
    env['PGPASSWORD'] = password

    try:
        result = subprocess.run(
            args, env=env, capture_output=True, text=True, timeout=300,
        )
    except FileNotFoundError:
        print("  WARN: pg_dump nicht im PATH — User-Backup uebersprungen.")
        return None
    except subprocess.TimeoutExpired:
        print("  WARN: pg_dump Timeout (5 min) — User-Backup unvollstaendig.")
        return None

    if result.returncode != 0:
        print(f"  WARN: pg_dump returncode={result.returncode}")
        if result.stderr:
            print(f"    stderr: {result.stderr.strip()[:500]}")
        return None

    size_kb = out.stat().st_size / 1024 if out.exists() else 0
    print(f"  User-Daten-Backup: {out} ({size_kb:.1f} KB)")
    return out


# ---------- CLI fuer Tests ----------

if __name__ == '__main__':
    print("Snapshot-Pfad:", SNAPSHOT_PATH.resolve())
    print("Backup-Verzeichnis:", BACKUP_DIR.resolve())
    print("Geschuetzte User-Tabellen:")
    for t in USER_TABLES:
        print(f"  - {t}")
    print("Deletion-Blocker:")
    for tbl, refs in DELETION_BLOCKERS.items():
        for ut, col in refs:
            print(f"  {tbl} <- {ut}.{col}")
