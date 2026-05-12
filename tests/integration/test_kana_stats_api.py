"""Integration-Tests fuer Phase-2 Kana-Stats-Endpoints."""
from app import db
from app.models import CardReviewState, ReviewLog
from tests.factories import KanaFactory, LessonContentFactory, LessonFactory


def _setup_user_with_kana_reviews(user):
    """Erstellt einen User mit 3 Kana, 1 davon mit Reviews/Lapses."""
    lesson = LessonFactory(allow_guest_access=True)
    kana_a = KanaFactory(character='あ', romanization='a')
    kana_ka = KanaFactory(character='か', romanization='ka')
    kana_sa = KanaFactory(character='さ', romanization='sa')

    lc_a = LessonContentFactory(
        lesson_id=lesson.id, content_type='kana', content_id=kana_a.id, page_number=1
    )
    lc_ka = LessonContentFactory(
        lesson_id=lesson.id, content_type='kana', content_id=kana_ka.id, page_number=1
    )
    lc_sa = LessonContentFactory(
        lesson_id=lesson.id, content_type='kana', content_id=kana_sa.id, page_number=1
    )

    # State + Reviews fuer a: 5 reps, 1 lapse
    state_a = CardReviewState(
        user_id=user.id, content_id=lc_a.id,
        fsrs_card_state='{"stability":1,"difficulty":5}',
        due_date=__import__('datetime').datetime.utcnow(),
        status='review', reps=5, lapses=1,
    )
    db.session.add(state_a)
    for r in [3, 3, 3, 1, 4]:
        db.session.add(ReviewLog(user_id=user.id, content_id=lc_a.id, rating=r))

    # State + Reviews fuer ka: 2 reps, 0 lapse
    state_ka = CardReviewState(
        user_id=user.id, content_id=lc_ka.id,
        fsrs_card_state='{"stability":5,"difficulty":4}',
        due_date=__import__('datetime').datetime.utcnow(),
        status='review', reps=2, lapses=0,
    )
    db.session.add(state_ka)
    for r in [3, 4]:
        db.session.add(ReviewLog(user_id=user.id, content_id=lc_ka.id, rating=r))

    # sa: kein State (User hat es noch nie gesehen) — soll nicht erscheinen

    db.session.commit()
    return lesson, [lc_a, lc_ka, lc_sa]


class TestKanaHeatmapAPI:
    def test_returns_only_seen_kana(self, auth_client):
        client, user = auth_client
        _setup_user_with_kana_reviews(user)
        resp = client.get('/api/srs/stats/kana-heatmap')
        assert resp.status_code == 200
        data = resp.get_json()
        # Nur kana mit Reviews -> 2 Eintraege (a, ka)
        assert data['count'] == 2
        chars = sorted([k['character'] for k in data['data']])
        assert chars == ['あ', 'か']

    def test_response_shape(self, auth_client):
        client, user = auth_client
        _setup_user_with_kana_reviews(user)
        data = client.get('/api/srs/stats/kana-heatmap').get_json()['data']
        for k in data:
            for field in ('kana_id', 'character', 'romanization', 'type', 'row',
                          'stage_idx', 'stage_name', 'accuracy', 'total_reps', 'lapses'):
                assert field in k, f'{field} fehlt'

    def test_accuracy_computed(self, auth_client):
        client, user = auth_client
        _setup_user_with_kana_reviews(user)
        data = client.get('/api/srs/stats/kana-heatmap').get_json()['data']
        # a: 4 von 5 korrekt = 80%
        a_item = next(k for k in data if k['character'] == 'あ')
        assert a_item['accuracy'] == 80.0
        # ka: 2 von 2 korrekt = 100%
        ka_item = next(k for k in data if k['character'] == 'か')
        assert ka_item['accuracy'] == 100.0


class TestKanaWeakAPI:
    def test_weakest_first(self, auth_client):
        client, user = auth_client
        _setup_user_with_kana_reviews(user)
        resp = client.get('/api/srs/stats/kana-weak?limit=5')
        assert resp.status_code == 200
        data = resp.get_json()['data']
        # a (1 lapse) muss vor ka (0 lapses) kommen
        assert data[0]['character'] == 'あ'

    def test_respect_limit(self, auth_client):
        client, user = auth_client
        _setup_user_with_kana_reviews(user)
        data = client.get('/api/srs/stats/kana-weak?limit=1').get_json()['data']
        assert len(data) == 1
