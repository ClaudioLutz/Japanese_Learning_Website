# tests/integration/test_srs_undo.py
"""Integration-Tests fuer POST /api/srs/undo (Rueckgaengig der letzten Bewertung).

Geprueft: Vorzustand wird exakt wiederhergestellt (neue und bestehende Karte),
ReviewLog/XP/Zaehler/Tages-Aggregat werden zurueckgenommen, nur die juengste
Bewertung und nur innerhalb von 5 Minuten, content_id-Schutz."""
from datetime import datetime, timedelta

import pytest

from app import db, srs_service
from app.models import CardReviewState, DailyReviewAggregate, ReviewLog, User
from tests.factories import (
    LessonContentFactory,
    LessonFactory,
    UserFactory,
    VocabularyFactory,
)


def _vocab_content(meaning_de='Wasser'):
    vocab = VocabularyFactory(meaning_de=meaning_de)
    lesson = LessonFactory()
    lc = LessonContentFactory(lesson_id=lesson.id, content_type='vocabulary', content_id=vocab.id)
    db.session.flush()
    return lc


def _rate(client, content_id, rating, source='review'):
    resp = client.post('/api/srs/rate',
                       json={'content_id': content_id, 'rating': rating, 'source': source})
    assert resp.status_code == 200
    return resp.get_json()


def _state(user_id, content_id):
    return CardReviewState.query.filter_by(
        user_id=user_id, content_id=content_id, direction='forward').first()


class TestUndo:
    def test_undo_first_rating_removes_new_card_state(self, auth_client):
        """Karte entstand erst durch die Bewertung -> Undo loescht State + Log."""
        client, user = auth_client
        lc = _vocab_content()
        _rate(client, lc.id, 3)
        assert _state(user.id, lc.id) is not None

        resp = client.post('/api/srs/undo', json={'content_id': lc.id})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['content_id'] == lc.id
        assert data['rating'] == 3
        db.session.expire_all()
        assert _state(user.id, lc.id) is None
        assert ReviewLog.query.filter_by(user_id=user.id).count() == 0

    def test_undo_restores_previous_state_exactly(self, auth_client):
        client, user = auth_client
        lc = _vocab_content()
        _rate(client, lc.id, 3)
        db.session.expire_all()
        before = _state(user.id, lc.id)
        snap = (before.fsrs_card_state, before.due_date, before.status, before.reps, before.lapses)

        _rate(client, lc.id, 1)  # Fehlbewertung „Nochmal"
        db.session.expire_all()
        after = _state(user.id, lc.id)
        assert after.lapses == 1

        resp = client.post('/api/srs/undo', json={'content_id': lc.id})
        assert resp.status_code == 200
        db.session.expire_all()
        restored = _state(user.id, lc.id)
        assert (restored.fsrs_card_state, restored.due_date, restored.status,
                restored.reps, restored.lapses) == snap
        assert ReviewLog.query.filter_by(user_id=user.id, content_id=lc.id).count() == 1

    def test_undo_reverts_xp_counters_and_aggregate(self, auth_client):
        client, user = auth_client
        lc = _vocab_content()
        _rate(client, lc.id, 3)
        db.session.expire_all()
        u = db.session.get(User, user.id)
        xp_before, reviews_before = u.total_xp, u.total_reviews
        agg = DailyReviewAggregate.query.filter_by(user_id=user.id).one()
        agg_before = (agg.total_reviews, agg.good_count, agg.correct_reviews, agg.xp_earned)

        res = _rate(client, lc.id, 3)
        resp = client.post('/api/srs/undo', json={'content_id': lc.id})
        assert resp.status_code == 200
        assert resp.get_json()['xp_reverted'] == res['xp_earned']

        db.session.expire_all()
        u = db.session.get(User, user.id)
        assert u.total_xp == xp_before
        assert u.total_reviews == reviews_before
        agg = DailyReviewAggregate.query.filter_by(user_id=user.id).one()
        assert (agg.total_reviews, agg.good_count, agg.correct_reviews, agg.xp_earned) == agg_before

    def test_undo_only_youngest_rating(self, auth_client):
        """content_id einer aelteren Bewertung -> 409, nichts veraendert."""
        client, user = auth_client
        a, b = _vocab_content('A'), _vocab_content('B')
        _rate(client, a.id, 3)
        _rate(client, b.id, 3)
        resp = client.post('/api/srs/undo', json={'content_id': a.id})
        assert resp.status_code == 409
        assert resp.get_json()['code'] == 'mismatch'
        assert ReviewLog.query.filter_by(user_id=user.id).count() == 2

    def test_undo_after_window_refused(self, auth_client):
        client, user = auth_client
        lc = _vocab_content()
        _rate(client, lc.id, 3)
        log = ReviewLog.query.filter_by(user_id=user.id).one()
        log.reviewed_at = datetime.utcnow() - timedelta(minutes=6)
        db.session.commit()

        resp = client.post('/api/srs/undo', json={'content_id': lc.id})
        assert resp.status_code == 410
        assert resp.get_json()['code'] == 'expired'
        db.session.expire_all()
        assert _state(user.id, lc.id) is not None
        assert ReviewLog.query.filter_by(user_id=user.id).count() == 1

    def test_undo_without_ratings_404(self, auth_client):
        client, _user = auth_client
        resp = client.post('/api/srs/undo', json={})
        assert resp.status_code == 404
        assert resp.get_json()['code'] == 'nothing'

    def test_legacy_log_without_snapshot_refused(self, auth_client):
        client, user = auth_client
        lc = _vocab_content()
        _rate(client, lc.id, 3)
        log = ReviewLog.query.filter_by(user_id=user.id).one()
        log.undo_snapshot = None
        db.session.commit()
        resp = client.post('/api/srs/undo', json={'content_id': lc.id})
        assert resp.status_code == 409
        assert resp.get_json()['code'] == 'no_snapshot'

    def test_undo_does_not_touch_other_users(self, auth_client):
        """Service-Ebene: fremde user_id sieht die Bewertung nicht (zwei Test-Clients
        teilen sich current_user ueber g — daher direkt am Service geprueft)."""
        client, user = auth_client
        other = UserFactory()
        db.session.commit()
        lc = _vocab_content()
        _rate(client, lc.id, 3)
        with pytest.raises(srs_service.UndoError) as exc:
            srs_service.undo_last_rating(other.id, content_id=lc.id)
        assert exc.value.code == 'nothing'
        assert ReviewLog.query.filter_by(user_id=user.id).count() == 1

    def test_undo_requires_login(self, client):
        resp = client.post('/api/srs/undo', json={})
        assert resp.status_code in (302, 401)

    def test_invalid_content_id_400(self, auth_client):
        client, _user = auth_client
        resp = client.post('/api/srs/undo', json={'content_id': 'abc'})
        assert resp.status_code == 400

    def test_review_page_has_undo_button(self, auth_client):
        client, _user = auth_client
        html = client.get('/review').get_data(as_text=True)
        assert 'id="reviewUndoBtn"' in html
        assert '/api/srs/undo' in html
