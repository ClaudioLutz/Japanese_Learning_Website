"""Integration-Tests fuer Practice-Endpoints (Phase 3)."""
from datetime import datetime

from app import db
from app.models import UserLessonProgress
from tests.factories import KanaFactory, LessonContentFactory, LessonFactory


def _setup_user_with_completed_lesson(user, n_kana=5):
    lesson = LessonFactory(allow_guest_access=True)
    kanas = []
    for i, ch in enumerate(['あ', 'い', 'う', 'え', 'お'][:n_kana]):
        kanas.append(KanaFactory(character=ch, romanization=['a','i','u','e','o'][i]))
        LessonContentFactory(
            lesson_id=lesson.id, content_type='kana', content_id=kanas[-1].id, page_number=1
        )
    # Lesson abgeschlossen
    progress = UserLessonProgress(
        user_id=user.id, lesson_id=lesson.id,
        is_completed=True, completed_at=datetime.utcnow(),
        progress_percentage=100,
    )
    db.session.add(progress)
    db.session.commit()
    return lesson


class TestPracticeSession:
    def test_no_completed_lessons_returns_empty(self, auth_client):
        client, user = auth_client
        resp = client.get('/api/practice/kana/session')
        data = resp.get_json()
        assert data['count'] == 0
        assert 'message' in data

    def test_returns_unlocked_kana(self, auth_client):
        client, user = auth_client
        _setup_user_with_completed_lesson(user)
        resp = client.get('/api/practice/kana/session?limit=5')
        data = resp.get_json()
        assert data['count'] == 5
        assert len(data['kana']) == 5

    def test_schrift_filter_hiragana(self, auth_client):
        client, user = auth_client
        _setup_user_with_completed_lesson(user)
        # Katakana hinzufuegen (in NEUER Lesson — sonst counter)
        lesson_k = LessonFactory(allow_guest_access=True)
        kk = KanaFactory(character='カ', romanization='ka', type='katakana')
        LessonContentFactory(
            lesson_id=lesson_k.id, content_type='kana', content_id=kk.id, page_number=1
        )
        db.session.add(UserLessonProgress(
            user_id=user.id, lesson_id=lesson_k.id,
            is_completed=True, completed_at=datetime.utcnow(), progress_percentage=100,
        ))
        db.session.commit()
        data = client.get('/api/practice/kana/session?schrift=hiragana').get_json()
        assert all(k['type'] == 'hiragana' for k in data['kana'])

    def test_explicit_ids(self, auth_client):
        client, user = auth_client
        _setup_user_with_completed_lesson(user, n_kana=5)
        # Hole alle Kana-IDs
        all_data = client.get('/api/practice/kana/session?limit=50').get_json()
        target_ids = [k['kana_id'] for k in all_data['kana'][:2]]
        data = client.get(f'/api/practice/kana/session?ids={target_ids[0]},{target_ids[1]}').get_json()
        assert data['count'] == 2

    def test_limit_capped_at_50(self, auth_client):
        client, user = auth_client
        _setup_user_with_completed_lesson(user)
        data = client.get('/api/practice/kana/session?limit=999').get_json()
        # max 5 Kana vorhanden, also <= 5
        assert data['count'] <= 5


class TestDailyChallenge:
    def test_deterministic_per_user_per_day(self, auth_client):
        client, user = auth_client
        _setup_user_with_completed_lesson(user)
        a = client.get('/api/practice/kana/daily-challenge').get_json()
        b = client.get('/api/practice/kana/daily-challenge').get_json()
        # Gleicher Tag, gleicher User => gleiche Kana-IDs in gleicher Reihenfolge
        a_ids = [k['kana_id'] for k in a['kana']]
        b_ids = [k['kana_id'] for k in b['kana']]
        assert a_ids == b_ids

    def test_bonus_xp_set(self, auth_client):
        client, user = auth_client
        _setup_user_with_completed_lesson(user)
        data = client.get('/api/practice/kana/daily-challenge').get_json()
        assert data['bonus_xp'] == 25

    def test_no_kana_returns_empty(self, auth_client):
        client, user = auth_client
        # Kein User-Progress => keine freigeschalteten Kana
        data = client.get('/api/practice/kana/daily-challenge').get_json()
        assert data['count'] == 0


class TestPushSubscription:
    def test_subscribe_stores_subscription(self, auth_client):
        client, user = auth_client
        resp = client.post(
            '/api/user/push-subscribe',
            json={'subscription': {'endpoint': 'https://x/y', 'keys': {'p256dh': 'a', 'auth': 'b'}}},
        )
        assert resp.status_code == 200
        db.session.refresh(user)
        assert user.push_subscription is not None
        assert user.push_subscription['endpoint'] == 'https://x/y'

    def test_subscribe_rejects_invalid(self, auth_client):
        client, user = auth_client
        resp = client.post('/api/user/push-subscribe', json={})
        assert resp.status_code == 400

    def test_unsubscribe_clears(self, auth_client):
        client, user = auth_client
        user.push_subscription = {'endpoint': 'https://x', 'keys': {}}
        db.session.commit()
        resp = client.post('/api/user/push-unsubscribe')
        assert resp.status_code == 200
        db.session.refresh(user)
        assert user.push_subscription is None
