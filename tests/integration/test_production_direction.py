# tests/integration/test_production_direction.py
"""Integration-Tests fuer die Produktions-Richtung (DE->JP, reverse-Spur).

Deckt ab: Koexistenz forward/reverse pro (user,content), on-the-fly-Population
der Produktions-Queue (forward-Stage>=3 + meaning_de), Isolation der
Rezeptions-Queue/Zaehler (forward-only) und die direction-Validierung der API.
"""
from datetime import datetime, timedelta

from app import db
from app.models import CardReviewState
from app import srs_service
from tests.factories import (
    LessonFactory, LessonContentFactory, VocabularyFactory, CardReviewStateFactory,
)

# Forward-Stage >= 3 (Stability >= 3 Tage) => produktiv freischaltbar
MATURE_FSRS = ('{"stability":12.0,"difficulty":5.0,"due":"2026-04-20T00:00:00+00:00",'
               '"last_review":"2026-04-13T00:00:00+00:00","reps":4,"lapses":0,"state":2,"step":null}')
# Forward-Stage < 3 (Stability ~1 Tag) => noch nicht produktiv
IMMATURE_FSRS = ('{"stability":1.0,"difficulty":5.0,"due":"2026-04-14T00:00:00+00:00",'
                 '"last_review":"2026-04-13T00:00:00+00:00","reps":1,"lapses":0,"state":2,"step":null}')


def _vocab_content(meaning_de='Wasser', word=None, reading=None):
    """Legt eine Vokabel + zugehoeriges vocabulary-LessonContent an, gibt das LC zurueck."""
    vocab = VocabularyFactory(
        meaning_de=meaning_de,
        **({'word': word} if word else {}),
        **({'reading': reading} if reading else {}),
    )
    lesson = LessonFactory()
    lc = LessonContentFactory(lesson_id=lesson.id, content_type='vocabulary', content_id=vocab.id)
    db.session.flush()
    return lc


def _forward_state(user_id, content_id, fsrs=MATURE_FSRS):
    return CardReviewStateFactory(
        user_id=user_id, content_id=content_id, direction='forward', fsrs_card_state=fsrs)


class TestDirectionCoexistence:
    def test_forward_and_reverse_states_coexist(self, auth_client):
        """rate_card forward + reverse fuer dasselbe content => zwei getrennte States."""
        client, user = auth_client
        lc = _vocab_content()
        srs_service.rate_card(user.id, lc.id, 3, direction='forward')
        srs_service.rate_card(user.id, lc.id, 3, direction='reverse')
        states = CardReviewState.query.filter_by(user_id=user.id, content_id=lc.id).all()
        dirs = sorted(s.direction for s in states)
        assert dirs == ['forward', 'reverse'], 'Beide Richtungen muessen koexistieren'

    def test_reverse_insert_sets_direction_no_unique_crash(self, auth_client):
        """Erstes reverse-Rating darf nicht gegen die forward-Zeile in die Unique laufen."""
        client, user = auth_client
        lc = _vocab_content()
        _forward_state(user.id, lc.id)
        db.session.commit()
        # darf NICHT werfen (uq_user_content_direction)
        srs_service.rate_card(user.id, lc.id, 3, direction='reverse')
        rev = CardReviewState.query.filter_by(
            user_id=user.id, content_id=lc.id, direction='reverse').first()
        assert rev is not None and rev.reps == 1


class TestProductionQueue:
    def test_includes_mature_vocab_with_meaning_de(self, auth_client):
        """Forward-Stage>=3 + meaning_de => taucht als produktiv NEU auf."""
        client, user = auth_client
        lc = _vocab_content(meaning_de='Hund')
        _forward_state(user.id, lc.id)
        db.session.commit()
        new = srs_service.get_production_new_cards(user.id)
        assert lc.id in [c.id for c in new]

    def test_excludes_immature_forward(self, auth_client):
        """Forward-Stage<3 => nicht produktiv freigeschaltet."""
        client, user = auth_client
        lc = _vocab_content()
        _forward_state(user.id, lc.id, fsrs=IMMATURE_FSRS)
        db.session.commit()
        new = srs_service.get_production_new_cards(user.id)
        assert lc.id not in [c.id for c in new]

    def test_excludes_missing_meaning_de(self, auth_client):
        """Reif, aber ohne meaning_de => kein fairer Cue => ausgeschlossen."""
        client, user = auth_client
        lc = _vocab_content(meaning_de='')
        _forward_state(user.id, lc.id)
        db.session.commit()
        new = srs_service.get_production_new_cards(user.id)
        assert lc.id not in [c.id for c in new]

    def test_excludes_already_started_reverse(self, auth_client):
        """Existiert schon eine reverse-Karte, ist es nicht mehr 'neu'."""
        client, user = auth_client
        lc = _vocab_content()
        _forward_state(user.id, lc.id)
        CardReviewStateFactory(user_id=user.id, content_id=lc.id, direction='reverse',
                               fsrs_card_state=MATURE_FSRS)
        db.session.commit()
        new = srs_service.get_production_new_cards(user.id)
        assert lc.id not in [c.id for c in new]

    def test_queue_endpoint_returns_reverse_cards(self, auth_client):
        """/api/srs/production/queue liefert die Vokabel mit direction=reverse + is_new."""
        client, user = auth_client
        lc = _vocab_content(meaning_de='Katze')
        _forward_state(user.id, lc.id)
        db.session.commit()
        resp = client.get('/api/srs/production/queue')
        assert resp.status_code == 200
        data = resp.get_json()
        cards = data['cards']
        assert any(c['content_id'] == lc.id and c['direction'] == 'reverse' and c['is_new']
                   for c in cards)
        assert data['overview']['new_ready'] >= 1


class TestReceptiveIsolation:
    def test_due_queue_forward_only(self, auth_client):
        """Eine faellige REVERSE-Karte darf NICHT in /api/srs/due (forward) erscheinen."""
        client, user = auth_client
        lc = _vocab_content()
        past = datetime.utcnow() - timedelta(days=1)
        CardReviewStateFactory(user_id=user.id, content_id=lc.id, direction='reverse',
                               due_date=past, fsrs_card_state=MATURE_FSRS)
        db.session.commit()
        resp = client.get('/api/srs/due')
        ids = [c['content_id'] for c in resp.get_json()['cards']]
        assert lc.id not in ids
        assert srs_service.get_due_count(user.id) == 0

    def test_user_stats_total_cards_forward_only(self, auth_client):
        """total_cards zaehlt nur forward — eine Vokabel mit beiden Spuren = 1."""
        client, user = auth_client
        lc = _vocab_content()
        _forward_state(user.id, lc.id)
        CardReviewStateFactory(user_id=user.id, content_id=lc.id, direction='reverse',
                               fsrs_card_state=MATURE_FSRS)
        db.session.commit()
        stats = srs_service.get_user_stats(user.id)
        assert stats['total_cards'] == 1

    def test_production_due_count_separate(self, auth_client):
        """Produktion hat einen EIGENEN Faelligkeits-Zaehler."""
        client, user = auth_client
        lc = _vocab_content()
        past = datetime.utcnow() - timedelta(days=1)
        CardReviewStateFactory(user_id=user.id, content_id=lc.id, direction='reverse',
                               due_date=past, fsrs_card_state=MATURE_FSRS)
        db.session.commit()
        assert srs_service.get_production_due_count(user.id) == 1
        assert srs_service.get_due_count(user.id) == 0


class TestRateApi:
    def test_default_direction_forward(self, auth_client):
        """POST /api/srs/rate OHNE direction => forward (Deck/Kana-Kompatibilitaet)."""
        client, user = auth_client
        lc = _vocab_content()
        resp = client.post('/api/srs/rate', json={'content_id': lc.id, 'rating': 3})
        assert resp.status_code == 200
        st = CardReviewState.query.filter_by(user_id=user.id, content_id=lc.id).first()
        assert st.direction == 'forward'

    def test_reverse_rating_creates_reverse_state(self, auth_client):
        """POST mit direction=reverse legt eine reverse-Karte an."""
        client, user = auth_client
        lc = _vocab_content()
        _forward_state(user.id, lc.id)
        db.session.commit()
        resp = client.post('/api/srs/rate',
                           json={'content_id': lc.id, 'rating': 3, 'direction': 'reverse'})
        assert resp.status_code == 200
        assert CardReviewState.query.filter_by(
            user_id=user.id, content_id=lc.id, direction='reverse').count() == 1

    def test_invalid_direction_400(self, auth_client):
        client, user = auth_client
        lc = _vocab_content()
        resp = client.post('/api/srs/rate',
                           json={'content_id': lc.id, 'rating': 3, 'direction': 'sideways'})
        assert resp.status_code == 400


class TestProductionPage:
    def test_page_loads_for_auth(self, auth_client):
        client, user = auth_client
        resp = client.get('/review/produktion')
        assert resp.status_code == 200
        assert b'Produktion' in resp.data or b'produktion' in resp.data

    def test_page_guest_sees_teaser(self, client):
        resp = client.get('/review/produktion')
        # Gast: weiche Teaser-Landing (kein harter Redirect), HTTP 200
        assert resp.status_code == 200
