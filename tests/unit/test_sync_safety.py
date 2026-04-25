"""
Unit-Tests fuer scripts/sync_safety.py.

Verifiziert die Schutzmechanismen, die User-Daten beim Cloud-Sync vor
Datenverlust bewahren:
  - Drift-Detection (Snapshot vs. aktueller Cloud-Stand)
  - Kaufschutz-Check (find_blocking_user_data)
  - Snapshot-Persistenz (write/load)
  - Konstanten USER_TABLES und DELETION_BLOCKERS sind vollstaendig
"""
from __future__ import annotations

import datetime
from unittest.mock import MagicMock


from scripts import sync_safety


# ---------- Konstanten-Konsistenz ----------

class TestConstants:
    """Stellt sicher, dass die Schutz-Listen vollstaendig sind."""

    def test_user_tables_list_is_complete(self):
        """Alle bekannten User-Tabellen muessen geschuetzt sein."""
        expected = {
            'user', 'user_lesson_progress', 'user_quiz_answer',
            'card_review_state', 'review_log', 'user_srs_settings',
            'user_achievement', 'daily_review_aggregate',
            'lesson_purchase', 'course_purchase', 'payment_transaction',
        }
        assert expected.issubset(set(sync_safety.USER_TABLES))

    def test_deletion_blockers_cover_purchase_tables(self):
        """Lesson und Course muessen Kaufschutz haben — sonst CASCADE-Risiko."""
        assert ('lesson_purchase', 'lesson_id') in \
               sync_safety.DELETION_BLOCKERS['lesson']
        assert ('course_purchase', 'course_id') in \
               sync_safety.DELETION_BLOCKERS['course']

    def test_deletion_blockers_cover_progress(self):
        """User-Lernfortschritt muss vor Lesson-Loeschung schuetzen."""
        assert ('user_lesson_progress', 'lesson_id') in \
               sync_safety.DELETION_BLOCKERS['lesson']

    def test_deletion_blockers_cover_quiz(self):
        """User-Quiz-Antworten muessen vor Question/Option-Loeschung schuetzen."""
        assert ('user_quiz_answer', 'question_id') in \
               sync_safety.DELETION_BLOCKERS['quiz_question']
        assert ('user_quiz_answer', 'selected_option_id') in \
               sync_safety.DELETION_BLOCKERS['quiz_option']

    def test_deletion_blockers_cover_srs(self):
        """SRS-Daten muessen vor Content-Loeschung schuetzen."""
        assert ('card_review_state', 'content_id') in \
               sync_safety.DELETION_BLOCKERS['lesson_content']
        assert ('review_log', 'content_id') in \
               sync_safety.DELETION_BLOCKERS['lesson_content']


# ---------- Snapshot ----------

class TestSnapshot:
    def test_collect_snapshot_with_updated_at(self):
        """Tabellen mit updated_at liefern Timestamp."""
        cur = MagicMock()
        ts = datetime.datetime(2026, 4, 25, 12, 0, 0)
        cur.fetchone.return_value = (10, 100, ts)

        snap = sync_safety.collect_snapshot(cur, ['lesson'])

        assert snap['lesson']['count'] == 10
        assert snap['lesson']['max_id'] == 100
        assert snap['lesson']['max_updated_at'] == ts.isoformat()

    def test_collect_snapshot_without_updated_at(self):
        """Tabellen ohne updated_at liefern NULL als max_updated_at."""
        cur = MagicMock()
        cur.fetchone.return_value = (5, 50, None)

        snap = sync_safety.collect_snapshot(cur, ['quiz_question'])

        assert snap['quiz_question']['count'] == 5
        assert snap['quiz_question']['max_id'] == 50
        assert snap['quiz_question']['max_updated_at'] is None

    def test_collect_snapshot_handles_missing_table(self):
        """Fehler bei einzelnen Tabellen unterbrechen den Sync nicht."""
        cur = MagicMock()
        cur.execute.side_effect = Exception("table missing")

        snap = sync_safety.collect_snapshot(cur, ['nonexistent'])

        assert 'error' in snap['nonexistent']

    def test_write_and_load_snapshot_roundtrip(self, tmp_path, monkeypatch):
        """Snapshot kann geschrieben und wieder gelesen werden."""
        target = tmp_path / 'snap.json'
        monkeypatch.setattr(sync_safety, 'SNAPSHOT_PATH', target)

        snap_data = {'lesson': {'count': 10, 'max_id': 100,
                                'max_updated_at': '2026-04-25T12:00:00'}}
        sync_safety.write_snapshot(snap_data, source_host='cloud.example')
        loaded = sync_safety.load_snapshot()

        assert loaded is not None
        assert loaded['source_host'] == 'cloud.example'
        assert loaded['snapshot'] == snap_data
        assert 'taken_at' in loaded

    def test_load_snapshot_returns_none_when_missing(self, tmp_path, monkeypatch):
        """Fehlende Snapshot-Datei liefert None, kein Crash."""
        monkeypatch.setattr(sync_safety, 'SNAPSHOT_PATH',
                            tmp_path / 'nonexistent.json')
        assert sync_safety.load_snapshot() is None


# ---------- Drift-Detection ----------

class TestDriftDetection:
    def test_no_drift_when_identical(self):
        """Identische Snapshots → keine Diffs."""
        snap = {'lesson': {'count': 10, 'max_id': 100,
                           'max_updated_at': '2026-04-25T12:00:00'}}
        assert sync_safety.detect_drift(snap, snap) == []

    def test_drift_on_count_change(self):
        """Andere Zeilenzahl → Drift erkannt."""
        saved = {'lesson': {'count': 10, 'max_id': 100, 'max_updated_at': None}}
        current = {'lesson': {'count': 11, 'max_id': 100, 'max_updated_at': None}}
        diffs = sync_safety.detect_drift(saved, current)
        assert any('count' in d for d in diffs)

    def test_drift_on_max_id_change(self):
        """Neue Cloud-ID seit Snapshot → Drift erkannt."""
        saved = {'lesson': {'count': 10, 'max_id': 100, 'max_updated_at': None}}
        current = {'lesson': {'count': 10, 'max_id': 101, 'max_updated_at': None}}
        diffs = sync_safety.detect_drift(saved, current)
        assert any('max_id' in d for d in diffs)

    def test_drift_on_updated_at_change(self):
        """Cloud-Edit (updated_at gewachsen) → Drift erkannt."""
        saved = {'lesson': {'count': 10, 'max_id': 100,
                            'max_updated_at': '2026-04-25T12:00:00'}}
        current = {'lesson': {'count': 10, 'max_id': 100,
                              'max_updated_at': '2026-04-25T13:00:00'}}
        diffs = sync_safety.detect_drift(saved, current)
        assert any('updated_at' in d for d in diffs)

    def test_drift_with_missing_saved_table(self):
        """Tabelle ist neu (nicht im alten Snapshot) → wird als Drift gemeldet."""
        saved = {}
        current = {'lesson': {'count': 1, 'max_id': 1, 'max_updated_at': None}}
        diffs = sync_safety.detect_drift(saved, current)
        assert len(diffs) == 1

    def test_error_entries_skip_drift(self):
        """Fehler beim Sammeln eines Tabellen-Snapshots wird ignoriert."""
        saved = {'lesson': {'error': 'x'}}
        current = {'lesson': {'error': 'x'}}
        assert sync_safety.detect_drift(saved, current) == []


# ---------- Kaufschutz-Check ----------

class TestFindBlockingUserData:
    def test_no_ids_returns_empty(self):
        """Leere ID-Menge → kein DB-Call, keine Findings."""
        cur = MagicMock()
        result = sync_safety.find_blocking_user_data(cur, 'lesson', set())
        assert result == []
        cur.execute.assert_not_called()

    def test_unmonitored_table_returns_empty(self):
        """Tabelle ohne Eintraege in DELETION_BLOCKERS → keine Pruefung."""
        cur = MagicMock()
        result = sync_safety.find_blocking_user_data(cur, 'kana', {1, 2, 3})
        assert result == []

    def test_lesson_purchase_blocks_lesson_delete(self):
        """LessonPurchase auf zu loeschende Lesson → Finding."""
        cur = MagicMock()
        # Erste Pruefung: user_lesson_progress (leer), zweite: lesson_purchase (Treffer).
        cur.fetchall.side_effect = [[], [(42, 1)]]

        result = sync_safety.find_blocking_user_data(cur, 'lesson', {42})

        assert ('lesson_purchase', 'lesson_id', 42, 1) in result

    def test_user_progress_blocks_lesson_delete(self):
        """UserLessonProgress auf zu loeschende Lesson → Finding."""
        cur = MagicMock()
        cur.fetchall.side_effect = [[(7, 3)], []]  # progress trifft, purchase leer

        result = sync_safety.find_blocking_user_data(cur, 'lesson', {7})

        assert ('user_lesson_progress', 'lesson_id', 7, 3) in result

    def test_course_purchase_blocks_course_delete(self):
        """CoursePurchase auf zu loeschende Course → Finding."""
        cur = MagicMock()
        cur.fetchall.side_effect = [[(5, 2)]]

        result = sync_safety.find_blocking_user_data(cur, 'course', {5})

        assert ('course_purchase', 'course_id', 5, 2) in result

    def test_quiz_question_blocks_lesson_content_delete(self):
        """UserQuizAnswer auf zu loeschende QuizQuestion → Finding."""
        cur = MagicMock()
        cur.fetchall.side_effect = [[(99, 1)]]

        result = sync_safety.find_blocking_user_data(cur, 'quiz_question', {99})

        assert ('user_quiz_answer', 'question_id', 99, 1) in result

    def test_failed_query_logs_warning_does_not_crash(self, capsys):
        """DB-Fehler bei Pruefung → Warnung, weiterlaufen, keine Findings."""
        cur = MagicMock()
        cur.execute.side_effect = Exception("connection lost")

        result = sync_safety.find_blocking_user_data(cur, 'lesson', {1})

        captured = capsys.readouterr()
        assert 'WARN' in captured.out
        assert result == []
