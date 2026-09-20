# tests/integration/test_welcome_back.py
"""Integration-Tests fuer den „Willkommen zurück"-Dialog (/api/welcome-back).

Der Dialog ersetzt ein allgemeines Feature-Popup: er zeigt, was JETZT ansteht,
und hoechstens drei Funktionen, die DIESER Nutzer laut Daten noch nie benutzt
hat. Geprueft werden die show-Logik, die Ableitung der unentdeckten Funktionen
und die Einbindung nur auf ruhigen Seiten."""
from datetime import date, timedelta

from app import db, srs_service
from app.models import CardReviewState, KanaStormScore
from tests.factories import (
    LessonContentFactory,
    LessonFactory,
    ReviewLogFactory,
    VocabularyFactory,
)


def _vocab_content(meaning_de='Wasser'):
    """Vokabel + zugehoeriges vocabulary-LessonContent (gibt das LC zurueck)."""
    vocab = VocabularyFactory(meaning_de=meaning_de)
    lesson = LessonFactory()
    lc = LessonContentFactory(lesson_id=lesson.id, content_type='vocabulary', content_id=vocab.id)
    db.session.flush()
    return lc



class TestWelcomeBackApi:
    def test_requires_login(self, client):
        resp = client.get('/api/welcome-back')
        assert resp.status_code in (302, 401)

    def test_no_show_for_brand_new_user(self, auth_client):
        """Frisch registriert (nie aktiv) => kein Dialog."""
        client, user = auth_client
        user.last_activity_date = None
        db.session.commit()
        assert client.get('/api/welcome-back').get_json()['show'] is False

    def test_no_show_when_active_today(self, auth_client):
        """Wer heute schon da war, kehrt nicht zurueck."""
        client, user = auth_client
        user.last_activity_date = date.today()
        db.session.commit()
        assert client.get('/api/welcome-back').get_json()['show'] is False

    def test_show_for_returning_user(self, auth_client):
        client, user = auth_client
        user.last_activity_date = date.today() - timedelta(days=3)
        db.session.commit()
        data = client.get('/api/welcome-back').get_json()
        assert data['show'] is True
        # Nichts benutzt => alle drei ableitbaren Funktionen sind „unentdeckt".
        assert [f['key'] for f in data['undiscovered']] == ['review', 'produktion', 'kana']

    def test_review_first_in_order(self, auth_client):
        client, user = auth_client
        user.last_activity_date = date.today() - timedelta(days=1)
        db.session.commit()
        data = client.get('/api/welcome-back').get_json()
        assert data['undiscovered'][0]['key'] == 'review'
        assert data['undiscovered'][0]['url'] == '/review'

    def test_review_source_marks_review_discovered(self, auth_client):
        client, user = auth_client
        user.last_activity_date = date.today() - timedelta(days=1)
        lc = _vocab_content()
        ReviewLogFactory(user_id=user.id, content_id=lc.id, rating=3, source='review')
        db.session.commit()
        keys = [f['key'] for f in client.get('/api/welcome-back').get_json()['undiscovered']]
        assert 'review' not in keys

    def test_two_logs_on_same_card_count_as_review(self, auth_client):
        """Altdaten haben source=NULL — zwei Logs derselben Karte sind eine Wiederholung."""
        client, user = auth_client
        user.last_activity_date = date.today() - timedelta(days=1)
        lc = _vocab_content()
        ReviewLogFactory(user_id=user.id, content_id=lc.id, rating=3, source=None)
        ReviewLogFactory(user_id=user.id, content_id=lc.id, rating=3, source=None)
        db.session.commit()
        keys = [f['key'] for f in client.get('/api/welcome-back').get_json()['undiscovered']]
        assert 'review' not in keys

    def test_single_deck_log_is_not_a_review(self, auth_client):
        """Genau der Problemfall: einmal im Deck bewertet ist KEINE Wiederholung."""
        client, user = auth_client
        user.last_activity_date = date.today() - timedelta(days=1)
        lc = _vocab_content()
        ReviewLogFactory(user_id=user.id, content_id=lc.id, rating=4, source='deck')
        db.session.commit()
        keys = [f['key'] for f in client.get('/api/welcome-back').get_json()['undiscovered']]
        assert 'review' in keys

    def test_reverse_log_marks_production_discovered(self, auth_client):
        client, user = auth_client
        user.last_activity_date = date.today() - timedelta(days=1)
        lc = _vocab_content()
        ReviewLogFactory(user_id=user.id, content_id=lc.id, rating=3, direction='reverse')
        db.session.commit()
        keys = [f['key'] for f in client.get('/api/welcome-back').get_json()['undiscovered']]
        assert 'produktion' not in keys

    def test_kana_score_marks_kana_discovered(self, auth_client):
        client, user = auth_client
        user.last_activity_date = date.today() - timedelta(days=1)
        db.session.add(KanaStormScore(user_id=user.id, mode='storm', schrift='hiragana'))
        db.session.commit()
        keys = [f['key'] for f in client.get('/api/welcome-back').get_json()['undiscovered']]
        assert 'kana' not in keys

    def test_no_show_when_nothing_to_offer(self, auth_client):
        """Alles entdeckt + nichts faellig => kein Dialog, auch beim Rueckkehrer."""
        client, user = auth_client
        user.last_activity_date = date.today() - timedelta(days=5)
        lc = _vocab_content()
        ReviewLogFactory(user_id=user.id, content_id=lc.id, rating=3, source='review')
        ReviewLogFactory(user_id=user.id, content_id=lc.id, rating=3, direction='reverse')
        db.session.add(KanaStormScore(user_id=user.id, mode='storm', schrift='hiragana'))
        db.session.commit()
        data = client.get('/api/welcome-back').get_json()
        assert data['undiscovered'] == []
        assert data['due_total'] == 0
        assert data['show'] is False

    def test_due_counts_and_next_lesson_present(self, auth_client):
        client, user = auth_client
        user.last_activity_date = date.today() - timedelta(days=1)
        lesson = LessonFactory(title='Lektion Bruecke', is_published=True)
        db.session.commit()
        data = client.get('/api/welcome-back').get_json()
        assert data['due_forward'] == 0 and data['due_reverse'] == 0
        assert data['due_total'] == 0
        assert data['next_lesson'] is not None
        assert str(lesson.id) in data['next_lesson']['url']

    def test_due_total_sums_both_directions(self, auth_client):
        client, user = auth_client
        user.last_activity_date = date.today() - timedelta(days=1)
        lc = _vocab_content()
        srs_service.rate_card(user.id, lc.id, 1, direction='forward', source='review')
        db.session.commit()
        state = CardReviewState.query.filter_by(user_id=user.id, content_id=lc.id).first()
        assert state is not None
        data = client.get('/api/welcome-back').get_json()
        assert data['due_total'] == data['due_forward'] + data['due_reverse']


# ── 4. Dialog-Einbindung + Lektionsabschluss-CTA ─────────────────────────

class TestWelcomeBackDialogPlacement:
    def test_dialog_on_quiet_pages(self, auth_client):
        client, _user = auth_client
        for url in ('/', '/mein-lernen', '/lessons'):
            html = client.get(url).get_data(as_text=True)
            assert 'id="welcomeBack"' in html, f'Dialog fehlt auf {url}'

    def test_no_dialog_for_guests(self, client):
        html = client.get('/').get_data(as_text=True)
        assert 'id="welcomeBack"' not in html

    def test_no_dialog_on_review_page(self, auth_client):
        client, _user = auth_client
        html = client.get('/review').get_data(as_text=True)
        assert 'id="welcomeBack"' not in html
