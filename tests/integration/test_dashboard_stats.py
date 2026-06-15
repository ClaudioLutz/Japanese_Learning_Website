"""Tests fuer das Statistik-Bundle des Lernenden-Dashboards.

dashboard_service.stats_bundle + Teilfunktionen (tempo/accByStage/retention/
records/confusion_pairs) + Endpoint /api/dashboard/stats.
"""
from datetime import datetime

from app import dashboard_service, db
from app.models import Kana, KanaConfusion
from tests.factories import (
    DailyReviewAggregateFactory,
    LessonContentFactory,
    LessonFactory,
    ReviewLogFactory,
    VocabularyFactory,
)


def _content():
    lesson = LessonFactory()
    vocab = VocabularyFactory()
    content = LessonContentFactory(lesson_id=lesson.id, content_type='vocabulary', content_id=vocab.id)
    db.session.commit()
    return content


class TestTempoStats:
    def test_empty_user_safe(self, auth_client):
        _client, user = auth_client
        t = dashboard_service.tempo_stats(user.id)
        assert len(t['reviewsByWeek']) == 8
        assert len(t['accuracyByWeek']) == 8
        assert len(t['reviewsByWeekday']) == 7
        assert t['kpi']['avgReviews'] == 0

    def test_aggregates_feed_kpi_and_weekday(self, auth_client):
        _client, user = auth_client
        today = datetime.utcnow().date()
        DailyReviewAggregateFactory(user_id=user.id, review_date=today,
                                    total_reviews=20, correct_reviews=16, total_time_ms=600000)
        db.session.commit()
        t = dashboard_service.tempo_stats(user.id)
        assert t['kpi']['avgReviews'] == 20
        # heutiger Wochentag hat den Schnitt 20
        assert t['reviewsByWeekday'][today.weekday()] == 20
        # aktuelle Woche (letzter Eintrag) enthaelt die 20
        assert t['reviewsByWeek'][-1] == 20
        assert t['accuracyByWeek'][-1] == 80


class TestAccByStage:
    def test_buckets_accuracy_by_stage(self, auth_client):
        _client, user = auth_client
        content = _content()
        # Stufe 0 (Neu): 1 richtig (4), 1 falsch (1) -> 50%
        ReviewLogFactory(user_id=user.id, content_id=content.id, rating=4, stage_at_review=0)
        ReviewLogFactory(user_id=user.id, content_id=content.id, rating=1, stage_at_review=0)
        # Stufe 8 (Gemeistert, Bucket 4): 1 richtig -> 100%
        ReviewLogFactory(user_id=user.id, content_id=content.id, rating=3, stage_at_review=8)
        db.session.commit()
        acc = dashboard_service.acc_by_stage(user.id)
        assert len(acc) == 5
        assert acc[0] == 50
        assert acc[4] == 100
        assert acc[2] == 0  # keine Daten in „Jung"


class TestRetention:
    def test_value_and_maturity_split(self, auth_client):
        _client, user = auth_client
        content = _content()
        ReviewLogFactory(user_id=user.id, content_id=content.id, rating=3, stage_at_review=0,
                         reviewed_at=datetime.utcnow())
        ReviewLogFactory(user_id=user.id, content_id=content.id, rating=1, stage_at_review=6,
                         reviewed_at=datetime.utcnow())
        db.session.commit()
        r = dashboard_service.retention_by_maturity(user.id)
        assert set(r.keys()) == {'value', 'neu', 'jung', 'reif'}
        assert r['value'] == 50          # 1 von 2 korrekt (letzte 30 Tage)
        assert r['neu'] == 100           # Stufe 0, rating 3
        assert r['reif'] == 0            # Stufe 6, rating 1


class TestRecords:
    def test_records_shape(self, auth_client):
        _client, user = auth_client
        user.longest_streak = 14
        DailyReviewAggregateFactory(user_id=user.id, review_date=datetime.utcnow().date(), total_reviews=47)
        db.session.commit()
        recs = dashboard_service.records(user.id)
        labels = {r['n']: r['val'] for r in recs}
        assert labels['Längste Serie'] == '14 Tage'
        assert labels['Bester Tag'] == '47 Reviews'


class TestConfusionPairs:
    def test_pair_from_kana_confusion(self, auth_client):
        _client, user = auth_client
        shi = Kana(character='し', romanization='shi', type='hiragana')
        shi_k = Kana(character='シ', romanization='shi', type='katakana')
        db.session.add_all([shi, shi_k])
        db.session.commit()
        db.session.add(KanaConfusion(user_id=user.id, target_kana_id=shi.id,
                                     confused_kana_id=shi_k.id, count=5))
        db.session.commit()
        pairs = dashboard_service.confusion_pairs(user.id)
        assert len(pairs) == 1
        p = pairs[0]
        assert {p['a'], p['b']} == {'し', 'シ'}
        assert 'Strichrichtung' in p['note']  # kuratierte Notiz

    def test_empty_without_confusion(self, auth_client):
        _client, user = auth_client
        assert dashboard_service.confusion_pairs(user.id) == []


class TestStatsBundle:
    def test_bundle_has_all_keys(self, auth_client):
        _client, user = auth_client
        bundle = dashboard_service.stats_bundle(user.id)
        for key in ('kpi', 'reviewsByWeek', 'accuracyByWeek', 'reviewsByWeekday',
                    'accByStage', 'retention', 'accBySkill', 'maturity', 'heatmap',
                    'cumulative', 'weakKana', 'leeches', 'confusionPairs', 'kanaRows',
                    'jlptDetail', 'milestones', 'records'):
            assert key in bundle, f'fehlender Schluessel: {key}'
        assert len(bundle['heatmap']) == 365
        assert len(bundle['accByStage']) == 5

    def test_endpoint_returns_bundle(self, auth_client):
        client, _user = auth_client
        resp = client.get('/api/dashboard/stats')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'kpi' in data and 'records' in data

    def test_endpoint_requires_auth(self, client):
        resp = client.get('/api/dashboard/stats')
        assert resp.status_code in (302, 401)
