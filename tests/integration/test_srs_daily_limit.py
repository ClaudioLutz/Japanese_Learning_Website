# tests/integration/test_srs_daily_limit.py
"""Integration-Tests fuer das Tageslimit der /review-Queue (/api/srs/due).

UserSRSSettings.daily_review_limit / daily_new_cards wurden bis 2026-09-24 nirgends
gelesen. Geprueft: Defaults (100/20) ohne Settings-Zeile, Limit greift, heute
erledigte Bewertungen zaehlen, Wiederholungen vor neuen Karten, ignore_limit,
Filter-Aufrufe (lesson_id) bleiben unlimitiert."""
from datetime import datetime, timedelta

from app import db, srs_service
from app.models import UserSRSSettings
from tests.factories import (
    CardReviewStateFactory,
    LessonContentFactory,
    LessonFactory,
    VocabularyFactory,
)


def _cards(user_id, n, reps=1, lesson=None, hours_ago_start=1):
    lesson = lesson or LessonFactory()
    ids = []
    for i in range(n):
        vocab = VocabularyFactory()
        lc = LessonContentFactory(lesson_id=lesson.id, content_type='vocabulary', content_id=vocab.id)
        db.session.flush()
        CardReviewStateFactory(
            user_id=user_id, content_id=lc.id, reps=reps,
            status='review' if reps else 'new',
            due_date=datetime.utcnow() - timedelta(hours=hours_ago_start + i))
        ids.append(lc.id)
    db.session.commit()
    return ids


def _settings(user_id, review_limit, new_limit):
    db.session.add(UserSRSSettings(user_id=user_id, daily_review_limit=review_limit,
                                   daily_new_cards=new_limit))
    db.session.commit()


class TestDailyLimit:
    def test_defaults_without_settings_row(self, auth_client):
        client, user = auth_client
        _cards(user.id, 3)
        data = client.get('/api/srs/due?limit=200').get_json()
        assert data['daily']['review_limit'] == srs_service.DEFAULT_DAILY_REVIEW_LIMIT == 100
        assert data['daily']['new_limit'] == srs_service.DEFAULT_DAILY_NEW_CARDS == 20
        assert len(data['cards']) == 3
        assert data['daily']['remaining_today'] == 3
        assert data['daily']['limited'] is False

    def test_review_limit_caps_queue(self, auth_client):
        client, user = auth_client
        _settings(user.id, 2, 20)
        _cards(user.id, 5)
        data = client.get('/api/srs/due?limit=200').get_json()
        assert len(data['cards']) == 2
        assert data['total_due'] == 5
        assert data['daily']['remaining_today'] == 2
        assert data['daily']['limited'] is True

    def test_done_today_counts_against_limit(self, auth_client):
        client, user = auth_client
        _settings(user.id, 3, 20)
        ids = _cards(user.id, 5)
        for cid in ids[:2]:
            client.post('/api/srs/rate', json={'content_id': cid, 'rating': 3, 'source': 'review'})
        data = client.get('/api/srs/due?limit=200').get_json()
        assert data['daily']['reviews_done'] == 2
        assert len(data['cards']) == 1

    def test_again_on_same_card_counts_once(self, auth_client):
        client, user = auth_client
        _settings(user.id, 3, 20)
        ids = _cards(user.id, 5)
        for _ in range(3):
            client.post('/api/srs/rate', json={'content_id': ids[0], 'rating': 1, 'source': 'review'})
        daily = srs_service.get_daily_status(user.id)
        assert daily['reviews_done'] == 1

    def test_deck_ratings_do_not_count(self, auth_client):
        client, user = auth_client
        _settings(user.id, 2, 20)
        ids = _cards(user.id, 4)
        client.post('/api/srs/rate', json={'content_id': ids[0], 'rating': 3, 'source': 'deck'})
        assert srs_service.get_daily_status(user.id)['reviews_done'] == 0

    def test_limit_reached_returns_empty_but_total_due(self, auth_client):
        client, user = auth_client
        _settings(user.id, 1, 0)
        ids = _cards(user.id, 3)
        client.post('/api/srs/rate', json={'content_id': ids[0], 'rating': 3, 'source': 'review'})
        data = client.get('/api/srs/due?limit=200').get_json()
        assert data['cards'] == []
        assert data['total_due'] >= 2
        assert data['daily']['remaining_today'] == 0

    def test_ignore_limit(self, auth_client):
        client, user = auth_client
        _settings(user.id, 1, 0)
        _cards(user.id, 4)
        data = client.get('/api/srs/due?limit=200&ignore_limit=1').get_json()
        assert len(data['cards']) == 4

    def test_reviews_before_new_cards(self, auth_client):
        client, user = auth_client
        lesson = LessonFactory()
        # neue Karten sind AELTER faellig als die Wiederholungen — trotzdem hinten
        new_ids = _cards(user.id, 2, reps=0, lesson=lesson, hours_ago_start=50)
        rev_ids = _cards(user.id, 3, reps=2, lesson=lesson, hours_ago_start=1)
        data = client.get('/api/srs/due?limit=200').get_json()
        order = [c['content_id'] for c in data['cards']]
        assert set(order[:3]) == set(rev_ids)
        assert set(order[3:]) == set(new_ids)
        assert [c['is_new'] for c in data['cards']] == [False] * 3 + [True] * 2

    def test_new_card_limit(self, auth_client):
        client, user = auth_client
        _settings(user.id, 100, 1)
        _cards(user.id, 3, reps=0)
        _cards(user.id, 2, reps=2)
        data = client.get('/api/srs/due?limit=200').get_json()
        assert sum(1 for c in data['cards'] if c['is_new']) == 1
        assert len(data['cards']) == 3

    def test_new_card_rated_today_counts_as_new(self, auth_client):
        client, user = auth_client
        _settings(user.id, 100, 1)
        ids = _cards(user.id, 2, reps=0)
        client.post('/api/srs/rate', json={'content_id': ids[0], 'rating': 3, 'source': 'review'})
        daily = srs_service.get_daily_status(user.id)
        assert daily['new_done'] == 1 and daily['reviews_done'] == 0
        assert daily['new_remaining'] == 0

    def test_batch_limit_param_still_respected(self, auth_client):
        client, user = auth_client
        _cards(user.id, 5)
        data = client.get('/api/srs/due?limit=2').get_json()
        assert len(data['cards']) == 2

    def test_lesson_filter_unlimited_and_without_daily(self, auth_client):
        client, user = auth_client
        _settings(user.id, 1, 0)
        lesson = LessonFactory()
        _cards(user.id, 3, lesson=lesson)
        data = client.get(f'/api/srs/due?lesson_id={lesson.id}').get_json()
        assert len(data['cards']) == 3
        assert 'daily' not in data

    def test_stats_include_daily(self, auth_client):
        client, _user = auth_client
        data = client.get('/api/srs/stats').get_json()
        assert 'remaining_today' in data['daily']

    def test_review_page_has_quota_element(self, auth_client):
        client, _user = auth_client
        html = client.get('/review').get_data(as_text=True)
        assert 'id="dailyQuota"' in html
        assert 'ignore_limit' in html
