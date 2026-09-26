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

    def test_no_show_when_nothing_to_offer(self, auth_client, monkeypatch):
        """Alles entdeckt + nichts faellig + nichts Neues => kein Dialog, auch beim Rueckkehrer."""
        from app import news_service
        monkeypatch.setattr(news_service, 'load_news', lambda path=None: [])
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


# ── 5. Streak/Freeze wirklich (update_streak) ────────────────────────────

def _ch_days_ago(n):
    from app.time_utils import ch_today
    return ch_today() - timedelta(days=n)


class TestStreakFreezeMechanics:
    """Spiegelt User.update_streak: 1 Freeze, Nachfuellung alle 7 Tage, deckt
    genau EINEN verpassten Tag; die Settings-Zeile entsteht lazy beim ersten
    update_streak (bis 2026-09 hatte kein Nutzer eine → Freeze war wirkungslos)."""

    def test_settings_row_created_on_first_update(self, app_context):
        from app.models import UserSRSSettings
        from tests.factories import UserFactory
        user = UserFactory()
        db.session.commit()
        assert UserSRSSettings.query.filter_by(user_id=user.id).first() is None
        user.update_streak()
        db.session.commit()
        s = UserSRSSettings.query.filter_by(user_id=user.id).first()
        assert s is not None
        assert s.streak_freezes_available == 1
        assert s.daily_review_limit == 100  # Modell-Default, nichts Eigenes

    def test_freeze_rescues_exactly_one_missed_day(self, app_context):
        from tests.factories import UserFactory
        user = UserFactory(current_streak=5, longest_streak=5)
        user.last_activity_date = _ch_days_ago(2)
        db.session.commit()
        assert user.update_streak() == 'frozen'
        assert user.current_streak == 5  # gehalten, kein +1
        assert user.srs_settings.streak_freezes_available == 0

    def test_freeze_does_not_cover_two_missed_days(self, app_context):
        from tests.factories import UserFactory
        user = UserFactory(current_streak=5, longest_streak=5)
        user.last_activity_date = _ch_days_ago(3)
        db.session.commit()
        assert user.update_streak() == 'reset'
        assert user.current_streak == 1

    def test_used_freeze_not_available_within_7_days(self, app_context):
        from app.models import UserSRSSettings
        from tests.factories import UserFactory
        user = UserFactory(current_streak=4, longest_streak=4)
        user.last_activity_date = _ch_days_ago(2)
        db.session.add(UserSRSSettings(user_id=user.id, streak_freezes_available=0,
                                       last_freeze_replenish=_ch_days_ago(3)))
        db.session.commit()
        assert user.update_streak() == 'reset'
        assert user.current_streak == 1

    def test_freeze_replenished_after_7_days(self, app_context):
        from app.models import UserSRSSettings
        from tests.factories import UserFactory
        user = UserFactory(current_streak=4, longest_streak=4)
        user.last_activity_date = _ch_days_ago(1)
        s = UserSRSSettings(user_id=user.id, streak_freezes_available=0,
                            last_freeze_replenish=_ch_days_ago(7))
        db.session.add(s)
        db.session.commit()
        assert user.update_streak() == 'extended'
        assert s.streak_freezes_available == 1
        assert s.last_freeze_replenish == _ch_days_ago(0)


# ── 6. Streak-Hinweis + „morgen faellig" im Dialog ────────────────────────

class TestWelcomeBackStreakAndTomorrow:
    def _get(self, client):
        return client.get('/api/welcome-back').get_json()

    def test_at_risk_when_learned_yesterday(self, auth_client):
        client, user = auth_client
        user.last_activity_date = _ch_days_ago(1)
        user.current_streak = 5
        db.session.commit()
        st = self._get(client)['streak']
        assert st['state'] == 'at_risk'
        assert 'Noch bis Mitternacht' in st['text'] and '5-Tage-Streak' in st['text']

    def test_freeze_pending_when_one_day_missed(self, auth_client):
        client, user = auth_client
        user.last_activity_date = _ch_days_ago(2)
        user.current_streak = 5
        db.session.commit()
        st = self._get(client)['streak']
        assert st['state'] == 'freeze_pending'
        assert 'Freeze' in st['text'] and '5-Tage-Streak' in st['text']

    def test_lost_when_freeze_already_used(self, auth_client):
        from app.models import UserSRSSettings
        client, user = auth_client
        user.last_activity_date = _ch_days_ago(2)
        user.current_streak = 5
        db.session.add(UserSRSSettings(user_id=user.id, streak_freezes_available=0,
                                       last_freeze_replenish=_ch_days_ago(1)))
        db.session.commit()
        st = self._get(client)['streak']
        assert st['state'] == 'lost'
        assert st['streak'] == 0 and st['prev_streak'] == 5
        assert 'gerissen' in st['text']

    def test_lost_when_gap_too_long(self, auth_client):
        client, user = auth_client
        user.last_activity_date = _ch_days_ago(4)
        user.current_streak = 9
        db.session.commit()
        assert self._get(client)['streak']['state'] == 'lost'

    def test_login_rescue_reported_after_fresh_login(self, app, db):
        """Frischer Login rettet per Freeze → Dialog zeigt es UND erscheint
        trotzdem (Stand vor dem Login ist massgeblich)."""
        from tests.factories import UserFactory
        user = UserFactory(email='frz@test.com', current_streak=6, longest_streak=6)
        user.last_activity_date = _ch_days_ago(2)
        db.session.commit()
        client = app.test_client()
        resp = client.post('/login', data={'email': 'frz@test.com', 'password': 'Test123!'})
        assert resp.status_code == 302
        data = client.get('/api/welcome-back').get_json()
        assert data['streak']['state'] == 'frozen'
        assert '6-Tage-Streak' in data['streak']['text']
        assert data['show'] is True

    def test_login_reset_reported_after_fresh_login(self, app, db):
        from tests.factories import UserFactory
        user = UserFactory(email='rst@test.com', current_streak=6, longest_streak=6)
        user.last_activity_date = _ch_days_ago(5)
        db.session.commit()
        client = app.test_client()
        client.post('/login', data={'email': 'rst@test.com', 'password': 'Test123!'})
        st = client.get('/api/welcome-back').get_json()['streak']
        assert st['state'] == 'lost' and st['prev_streak'] == 6

    def test_due_tomorrow_counts_only_upcoming(self, auth_client):
        from datetime import datetime
        client, user = auth_client
        user.last_activity_date = _ch_days_ago(1)
        now = datetime.utcnow()
        for hours in (-2, 20, 24 * 5):
            lc = _vocab_content()
            db.session.add(CardReviewState(user_id=user.id, content_id=lc.id, direction='forward',
                                           fsrs_card_state='{}', due_date=now + timedelta(hours=hours),
                                           status='review'))
        db.session.commit()
        data = self._get(client)
        assert data['due_tomorrow'] == 1
        assert data['due_forward'] == 1

    def test_suspended_not_counted_tomorrow(self, auth_client):
        from datetime import datetime
        client, user = auth_client
        lc = _vocab_content()
        db.session.add(CardReviewState(user_id=user.id, content_id=lc.id, direction='forward',
                                       fsrs_card_state='{}',
                                       due_date=datetime.utcnow() + timedelta(hours=20),
                                       status='suspended'))
        db.session.commit()
        assert self._get(client)['due_tomorrow'] == 0

    def test_mein_lernen_shows_streak_note(self, auth_client):
        client, user = auth_client
        user.last_activity_date = _ch_days_ago(1)
        user.current_streak = 3
        db.session.commit()
        html = client.get('/mein-lernen').get_data(as_text=True)
        assert 'data-streak-state="at_risk"' in html
        assert 'Noch bis Mitternacht' in html
