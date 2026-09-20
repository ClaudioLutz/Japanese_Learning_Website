# tests/integration/test_review_source_and_cap.py
"""Integration-Tests fuer ReviewLog.source und die Deckelung der ersten
Deck-Bewertung (2026-09-20).

Hintergrund: ein echter Nutzer bewertete Karten nur EINMAL im Lektions-Deck
(fast immer „Einfach"=4 -> FSRS schob sie 8-11 Tage weg) und fand /review nie.
Geprueft werden (1) die Herkunft einer Bewertung inkl. Whitelist, (2) die
Deckelung Deck+Erstkontakt+Rating 4 -> 3 und (3) der Abschluss-CTA der Lektion."""
from app import db, srs_service
from app.models import ReviewLog
from tests.factories import (
    LessonContentFactory,
    LessonFactory,
    LessonPageFactory,
    VocabularyFactory,
)


def _vocab_content(meaning_de='Wasser'):
    """Vokabel + zugehoeriges vocabulary-LessonContent (gibt das LC zurueck)."""
    vocab = VocabularyFactory(meaning_de=meaning_de)
    lesson = LessonFactory()
    lc = LessonContentFactory(lesson_id=lesson.id, content_type='vocabulary', content_id=vocab.id)
    db.session.flush()
    return lc


def _log(user_id, content_id):
    return (ReviewLog.query.filter_by(user_id=user_id, content_id=content_id)
            .order_by(ReviewLog.id.desc()).first())


# ── 1. ReviewLog.source ──────────────────────────────────────────────────

class TestRateSource:
    def test_source_is_stored(self, auth_client):
        client, user = auth_client
        lc = _vocab_content()
        resp = client.post('/api/srs/rate',
                           json={'content_id': lc.id, 'rating': 3, 'source': 'review'})
        assert resp.status_code == 200
        assert _log(user.id, lc.id).source == 'review'

    def test_all_whitelisted_sources_accepted(self, auth_client):
        client, user = auth_client
        for src in ('deck', 'review', 'produktion', 'kana_grid', 'dashboard'):
            lc = _vocab_content(meaning_de=f'W-{src}')
            resp = client.post('/api/srs/rate',
                               json={'content_id': lc.id, 'rating': 3, 'source': src})
            assert resp.status_code == 200
            assert _log(user.id, lc.id).source == src

    def test_unknown_source_becomes_null_not_400(self, auth_client):
        """Abwaertskompatibilitaet: unbekannte Werte werden still zu NULL."""
        client, user = auth_client
        lc = _vocab_content()
        resp = client.post('/api/srs/rate',
                           json={'content_id': lc.id, 'rating': 3, 'source': 'hackerman'})
        assert resp.status_code == 200
        assert _log(user.id, lc.id).source is None

    def test_missing_source_becomes_null(self, auth_client):
        """Gecachte alte Clients senden kein source-Feld -> NULL, kein Fehler."""
        client, user = auth_client
        lc = _vocab_content()
        resp = client.post('/api/srs/rate', json={'content_id': lc.id, 'rating': 3})
        assert resp.status_code == 200
        assert _log(user.id, lc.id).source is None


# ── 2. Deckelung der ersten Deck-Bewertung ───────────────────────────────

class TestFirstDeckRatingCap:
    def test_first_deck_easy_is_capped_to_good(self, auth_client):
        """Deck + Erstkontakt + „Einfach" (4) => effektiv „Gut" (3)."""
        client, user = auth_client
        lc = _vocab_content()
        resp = client.post('/api/srs/rate',
                           json={'content_id': lc.id, 'rating': 4, 'source': 'deck'})
        assert resp.status_code == 200
        assert _log(user.id, lc.id).rating == 3, 'Erste Deck-4 muss als 3 protokolliert werden'

    def test_response_shape_unchanged(self, auth_client):
        """Die Deckelung darf die Antwort nicht veraendern (kein neues Feld noetig)."""
        client, _user = auth_client
        lc = _vocab_content()
        data = client.post('/api/srs/rate',
                           json={'content_id': lc.id, 'rating': 4, 'source': 'deck'}).get_json()
        for key in ('next_interval', 'due_date', 'status', 'reps', 'lapses', 'xp_earned'):
            assert key in data

    def test_second_deck_easy_stays_four(self, auth_client):
        """Nur der ERSTKONTAKT wird gedeckelt — Folge-Bewertungen bleiben 4."""
        client, user = auth_client
        lc = _vocab_content()
        client.post('/api/srs/rate', json={'content_id': lc.id, 'rating': 3, 'source': 'deck'})
        client.post('/api/srs/rate', json={'content_id': lc.id, 'rating': 4, 'source': 'deck'})
        assert _log(user.id, lc.id).rating == 4

    def test_review_easy_never_capped(self, auth_client):
        """In /review ist „Einfach" eine echte Aussage — nie deckeln."""
        client, user = auth_client
        lc = _vocab_content()
        client.post('/api/srs/rate', json={'content_id': lc.id, 'rating': 4, 'source': 'review'})
        assert _log(user.id, lc.id).rating == 4

    def test_deck_ratings_one_to_three_untouched(self, auth_client):
        client, user = auth_client
        for rating in (1, 2, 3):
            lc = _vocab_content(meaning_de=f'R{rating}')
            client.post('/api/srs/rate',
                        json={'content_id': lc.id, 'rating': rating, 'source': 'deck'})
            assert _log(user.id, lc.id).rating == rating

    def test_capped_rating_shortens_interval(self, auth_client):
        """Wirkungsnachweis: gedeckelt geplantes Intervall < ungedeckeltes."""
        client, _user = auth_client
        capped = client.post('/api/srs/rate', json={
            'content_id': _vocab_content(meaning_de='A').id, 'rating': 4, 'source': 'deck',
        }).get_json()['next_interval']
        raw = client.post('/api/srs/rate', json={
            'content_id': _vocab_content(meaning_de='B').id, 'rating': 4, 'source': 'review',
        }).get_json()['next_interval']
        assert capped < raw

    def test_reverse_direction_first_deck_is_independent(self, auth_client):
        """Die Deckelung haengt an (user, content, direction) — nicht global."""
        client, user = auth_client
        lc = _vocab_content()
        srs_service.rate_card(user.id, lc.id, 3, direction='forward', source='deck')
        srs_service.rate_card(user.id, lc.id, 4, direction='reverse', source='deck')
        rev = ReviewLog.query.filter_by(
            user_id=user.id, content_id=lc.id, direction='reverse').first()
        assert rev.rating == 3, 'Auch reverse ist beim Erstkontakt ein Startwert'


class TestLessonCompletionCta:
    def _guest_lesson(self):
        lesson = LessonFactory(is_published=True, price=0.0, allow_guest_access=True)
        LessonPageFactory(lesson_id=lesson.id, page_number=1)
        db.session.commit()
        return lesson

    def test_cta_rendered_for_logged_in_user(self, auth_client):
        client, _user = auth_client
        lesson = self._guest_lesson()
        html = client.get(f'/lessons/{lesson.id}').get_data(as_text=True)
        assert 'id="completionReviewCta"' in html
        assert 'Jetzt wiederholen' in html
        assert 'Üben → Wiederholen' in html

    def test_no_cta_for_guests(self, client, app_context):
        lesson = self._guest_lesson()
        html = client.get(f'/lessons/{lesson.id}').get_data(as_text=True)
        assert 'id="completionReviewCta"' not in html

    def test_deck_sends_source_and_shows_first_hint(self, auth_client):
        """Deck-Rating traegt source='deck' und der Erstkontakt-Hinweis ist da."""
        client, _user = auth_client
        lesson = self._guest_lesson()
        html = client.get(f'/lessons/{lesson.id}').get_data(as_text=True)
        assert "source: 'deck'" in html
        assert 'deck-first-hint' in html
        assert 'Erste Einschätzung = Startwert' in html
