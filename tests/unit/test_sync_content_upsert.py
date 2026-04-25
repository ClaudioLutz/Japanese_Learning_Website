"""
Unit-Tests fuer scripts/sync_content_upsert.py — Kernlogik der Schutzmechanismen.

Verifiziert insbesondere, dass:
  - sync_table() abbricht, wenn ein DELETE auf eine Cloud-Lesson User-Daten
    zerstoeren wuerde (Kaufschutz)
  - --force-delete-user-data den Schutz bewusst aushebelt
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from scripts import sync_content_upsert


def _setup_cursors(local_rows, local_pks, cloud_pks,
                   columns=('id', 'title'),
                   blocking_findings=None):
    """Erstellt local_cur + cloud_cur Mocks mit bestimmten Antworten.

    blocking_findings: Liste von (user_table, fk_col, ref_id, count)-Tupeln
                       fuer find_blocking_user_data.
    """
    local_cur = MagicMock()
    cloud_cur = MagicMock()

    # get_columns wird zweimal pro Tabelle aufgerufen (lokal + cloud).
    local_cur.fetchall.side_effect = [
        [(c,) for c in columns],   # get_columns(local_cur)
        local_rows,                # SELECT * FROM lesson lokal
        [(p,) for p in local_pks], # SELECT id FROM lesson lokal
    ]
    cloud_cur.fetchall.side_effect = [
        [(c,) for c in columns],   # get_columns(cloud_cur)
        [(p,) for p in cloud_pks], # SELECT id FROM lesson cloud
    ]
    return local_cur, cloud_cur


class TestKaufschutz:
    """Pruef, dass User-Daten beim Sync nicht stillschweigend zerstoert werden."""

    def test_blocks_delete_when_user_progress_exists(self, monkeypatch):
        """Cloud-Lesson 99 hat user_lesson_progress → Sync muss abbrechen."""
        local_cur, cloud_cur = _setup_cursors(
            local_rows=[(1, 'A'), (2, 'B')],
            local_pks=[1, 2],
            cloud_pks=[1, 2, 99],   # 99 lokal nicht da → wuerde geloescht
        )
        cloud_cur.rowcount = 1  # UPSERT-Loop liest rowcount > 0

        def fake_blockers(cur, table, ids):
            return [('user_lesson_progress', 'lesson_id', 99, 5)]

        monkeypatch.setattr(sync_content_upsert,
                            'find_blocking_user_data', fake_blockers)

        with pytest.raises(RuntimeError, match='ABBRUCH'):
            sync_content_upsert.sync_table(
                local_cur, cloud_cur,
                {'name': 'lesson', 'pk': 'id'},
                allow_user_data_delete=False,
            )

    def test_blocks_delete_when_lesson_purchase_exists(self, monkeypatch):
        """LessonPurchase auf zu loeschende Lesson → Abbruch (kein CASCADE-Verlust)."""
        local_cur, cloud_cur = _setup_cursors(
            local_rows=[(1, 'A')],
            local_pks=[1],
            cloud_pks=[1, 50],
        )
        cloud_cur.rowcount = 1
        monkeypatch.setattr(
            sync_content_upsert, 'find_blocking_user_data',
            lambda cur, table, ids: [
                ('lesson_purchase', 'lesson_id', 50, 2)
            ],
        )

        with pytest.raises(RuntimeError, match='lesson_purchase'):
            sync_content_upsert.sync_table(
                local_cur, cloud_cur,
                {'name': 'lesson', 'pk': 'id'},
                allow_user_data_delete=False,
            )

    def test_force_flag_bypasses_blocker(self, monkeypatch):
        """Mit --force-delete-user-data wird trotz Findings geloescht."""
        local_cur, cloud_cur = _setup_cursors(
            local_rows=[(1, 'A')],
            local_pks=[1],
            cloud_pks=[1, 99],
        )
        monkeypatch.setattr(
            sync_content_upsert, 'find_blocking_user_data',
            lambda cur, table, ids: [
                ('user_lesson_progress', 'lesson_id', 99, 1)
            ],
        )

        # rowcount > 0 fuer den UPSERT-Loop
        cloud_cur.rowcount = 1

        rows, upserted, deleted = sync_content_upsert.sync_table(
            local_cur, cloud_cur,
            {'name': 'lesson', 'pk': 'id'},
            allow_user_data_delete=True,
        )

        assert deleted == 1
        # DELETE wurde tatsaechlich abgesetzt (am cloud_cur).
        delete_calls = [
            c for c in cloud_cur.execute.call_args_list
            if 'DELETE FROM' in c.args[0]
        ]
        assert len(delete_calls) == 1

    def test_no_blockers_proceeds_normally(self, monkeypatch):
        """Wenn keine User-Daten betroffen → DELETE laeuft durch."""
        local_cur, cloud_cur = _setup_cursors(
            local_rows=[(1, 'A')],
            local_pks=[1],
            cloud_pks=[1, 77],
        )
        monkeypatch.setattr(
            sync_content_upsert, 'find_blocking_user_data',
            lambda cur, table, ids: [],
        )
        cloud_cur.rowcount = 1

        rows, upserted, deleted = sync_content_upsert.sync_table(
            local_cur, cloud_cur,
            {'name': 'lesson', 'pk': 'id'},
            allow_user_data_delete=False,
        )

        assert deleted == 1

    def test_kana_table_not_checked_for_blockers(self, monkeypatch):
        """Tabelle ausserhalb DELETION_BLOCKERS (z.B. kana) wird normal geloescht."""
        local_cur, cloud_cur = _setup_cursors(
            local_rows=[(1, 'a')],
            local_pks=[1],
            cloud_pks=[1, 10],
        )
        # find_blocking_user_data wird mit 'kana' aufgerufen, liefert leer
        # (weil 'kana' nicht in DELETION_BLOCKERS).
        cloud_cur.rowcount = 1

        rows, upserted, deleted = sync_content_upsert.sync_table(
            local_cur, cloud_cur,
            {'name': 'kana', 'pk': 'id'},
            allow_user_data_delete=False,
        )

        assert deleted == 1


class TestNoDeletes:
    def test_skips_blocker_check_without_deletes(self, monkeypatch):
        """Wenn lokal == cloud, werden keine DELETEs faellig — kein Check noetig."""
        local_cur, cloud_cur = _setup_cursors(
            local_rows=[(1, 'A'), (2, 'B')],
            local_pks=[1, 2],
            cloud_pks=[1, 2],
        )
        called = {'count': 0}

        def fake_blockers(cur, table, ids):
            called['count'] += 1
            return []

        monkeypatch.setattr(sync_content_upsert,
                            'find_blocking_user_data', fake_blockers)
        cloud_cur.rowcount = 1

        rows, upserted, deleted = sync_content_upsert.sync_table(
            local_cur, cloud_cur,
            {'name': 'lesson', 'pk': 'id'},
            allow_user_data_delete=False,
        )

        assert deleted == 0
        # Wenn cloud_pks == local_pks, ist to_delete leer und der Check wird
        # nicht aufgerufen.
        assert called['count'] == 0
