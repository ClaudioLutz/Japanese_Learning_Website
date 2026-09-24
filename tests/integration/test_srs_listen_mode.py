# tests/integration/test_srs_listen_mode.py
"""Hoermodus in /review: source='review_listen' (Whitelist) + Seiten-Markup."""
from app import db, srs_service
from app.models import ReviewLog
from app.srs_routes import RATE_SOURCES
from tests.factories import LessonContentFactory, LessonFactory, VocabularyFactory


def _vocab_content():
    vocab = VocabularyFactory()
    lesson = LessonFactory()
    lc = LessonContentFactory(lesson_id=lesson.id, content_type='vocabulary', content_id=vocab.id)
    db.session.flush()
    return lc


class TestListenSource:
    def test_review_listen_whitelisted(self):
        assert 'review_listen' in RATE_SOURCES

    def test_review_listen_is_stored(self, auth_client):
        client, user = auth_client
        lc = _vocab_content()
        resp = client.post('/api/srs/rate',
                           json={'content_id': lc.id, 'rating': 3, 'source': 'review_listen'})
        assert resp.status_code == 200
        log = ReviewLog.query.filter_by(user_id=user.id, content_id=lc.id).one()
        assert log.source == 'review_listen'

    def test_review_listen_fits_column(self):
        assert len('review_listen') <= ReviewLog.source.property.columns[0].type.length

    def test_listen_ratings_count_against_daily_limit(self, auth_client):
        client, user = auth_client
        lc = _vocab_content()
        client.post('/api/srs/rate', json={'content_id': lc.id, 'rating': 3, 'source': 'deck'})
        client.post('/api/srs/rate', json={'content_id': lc.id, 'rating': 3, 'source': 'review_listen'})
        daily = srs_service.get_daily_status(user.id)
        assert daily['reviews_done'] == 1

    def test_listen_rating_can_be_undone(self, auth_client):
        client, user = auth_client
        lc = _vocab_content()
        client.post('/api/srs/rate', json={'content_id': lc.id, 'rating': 2, 'source': 'review_listen'})
        resp = client.post('/api/srs/undo', json={'content_id': lc.id})
        assert resp.status_code == 200
        assert resp.get_json()['source'] == 'review_listen'


class TestListenMarkup:
    def test_review_page_has_listen_toggle(self, auth_client):
        client, _user = auth_client
        html = client.get('/review').get_data(as_text=True)
        assert 'id="reviewListenToggle"' in html
        assert "'review_listen'" in html
        assert 'jpl_review_mode' in html            # Modus in localStorage
        assert 'prefers-reduced-motion' in html     # Autoplay-Fallback
