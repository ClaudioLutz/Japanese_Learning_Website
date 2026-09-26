"""Integration-Tests: oeffentliche Seite /neu + „Seit deinem letzten Besuch neu"
im Willkommen-zurück-Dialog (/api/welcome-back → news)."""
from datetime import date, datetime, timedelta

import pytest

from app import db, news_service
from app.news_service import NewsEntry
from tests.factories import LessonFactory, UserFactory


def _fake_news(monkeypatch, *days):
    entries = [NewsEntry(d, f'Eintrag {i}', 'Text.') for i, d in enumerate(days)]
    monkeypatch.setattr(news_service, 'load_news', lambda path=None: entries)


class TestNeuPage:
    def test_public_ssr(self, client):
        resp = client.get('/neu')
        assert resp.status_code == 200
        html = resp.get_data(as_text=True)
        assert 'Was ist neu?' in html
        # SSR: Eintraege stehen direkt im HTML (kein JS-Nachladen).
        assert 'Hörmodus beim Wiederholen' in html
        assert '24. September 2026' in html
        assert '<meta name="description" content="Was ist neu' in html

    def test_links_rendered(self, client):
        html = client.get('/neu').get_data(as_text=True)
        assert 'class="neu-link" href="/review"' in html

    def test_empty_file(self, client, monkeypatch):
        monkeypatch.setattr(news_service, 'load_news', lambda path=None: [])
        resp = client.get('/neu')
        assert resp.status_code == 200
        assert 'Noch keine Einträge' in resp.get_data(as_text=True)

    def test_in_sitemap(self, client):
        xml = client.get('/sitemap.xml').get_data(as_text=True)
        assert '/neu</loc>' in xml

    def test_footer_link(self, client):
        assert 'href="/neu"' in client.get('/ueber').get_data(as_text=True)

    def test_dropdown_link_for_user(self, auth_client):
        client, _ = auth_client
        html = client.get('/neu').get_data(as_text=True)
        assert 'fa-bullhorn' in html


class TestNewsSince:
    def test_none_reference_gives_zero(self, app_context):
        assert news_service.news_since(None)['total'] == 0

    def test_counts_lessons_and_entries(self, app_context, monkeypatch):
        since = datetime(2026, 9, 21, 12, 0)
        _fake_news(monkeypatch, date(2026, 9, 24), date(2026, 9, 22), date(2026, 9, 21), date(2026, 9, 1))
        LessonFactory(instruction_language='german', created_at=datetime(2026, 9, 23))
        LessonFactory(instruction_language='german', created_at=datetime(2026, 9, 25))
        LessonFactory(instruction_language='german', created_at=datetime(2026, 9, 1))  # alt
        LessonFactory(instruction_language='german', created_at=datetime(2026, 9, 24), is_published=False)
        LessonFactory(instruction_language='english', created_at=datetime(2026, 9, 24))
        db.session.commit()
        res = news_service.news_since(since, ['german'])
        # Eintraege: nur Tage NACH dem CH-Tag des Referenzzeitpunkts (21.09.)
        assert res == {'lessons': 2, 'updates': 2, 'total': 4, 'url': '/neu'}


def _returning(user, days=3):
    user.last_activity_date = date.today() - timedelta(days=days)


class TestWelcomeBackNews:
    def test_news_counts_since_last_login(self, auth_client, monkeypatch):
        client, user = auth_client
        _returning(user)
        user.last_login = datetime.utcnow() - timedelta(days=5)
        _fake_news(monkeypatch, date.today() + timedelta(days=1), date.today() - timedelta(days=30))
        LessonFactory(instruction_language='german', created_at=datetime.utcnow() - timedelta(days=1))
        db.session.commit()
        news = client.get('/api/welcome-back').get_json()['news']
        assert news['lessons'] == 1
        assert news['updates'] == 1
        assert news['url'] == '/neu'

    def test_no_news_when_nothing_new(self, auth_client, monkeypatch):
        client, user = auth_client
        _returning(user)
        user.last_login = datetime.utcnow() - timedelta(days=5)
        _fake_news(monkeypatch, date.today() - timedelta(days=30))
        db.session.commit()
        assert client.get('/api/welcome-back').get_json()['news']['total'] == 0

    def test_last_activity_bounds_stale_login(self, auth_client, monkeypatch):
        """Remember-Cookie: last_login Wochen alt, aber vor 3 Tagen aktiv —
        es zaehlt nur, was seit dem letzten aktiven Tag neu ist."""
        client, user = auth_client
        _returning(user, days=3)
        user.last_login = datetime.utcnow() - timedelta(days=60)
        _fake_news(monkeypatch, date.today() - timedelta(days=20))
        LessonFactory(instruction_language='german', created_at=datetime.utcnow() - timedelta(days=20))
        db.session.commit()
        assert client.get('/api/welcome-back').get_json()['news']['total'] == 0

    def test_news_alone_triggers_show(self, auth_client, monkeypatch):
        """Alles entdeckt + nichts faellig, aber Neues → Dialog erscheint."""
        from app.models import KanaStormScore
        from tests.factories import LessonContentFactory, ReviewLogFactory, VocabularyFactory
        client, user = auth_client
        _returning(user, days=5)
        user.last_login = datetime.utcnow() - timedelta(days=5)
        vocab = VocabularyFactory()
        lesson = LessonFactory(created_at=datetime.utcnow() - timedelta(days=30))
        lc = LessonContentFactory(lesson_id=lesson.id, content_type='vocabulary', content_id=vocab.id)
        db.session.flush()
        ReviewLogFactory(user_id=user.id, content_id=lc.id, rating=3, source='review')
        ReviewLogFactory(user_id=user.id, content_id=lc.id, rating=3, direction='reverse')
        db.session.add(KanaStormScore(user_id=user.id, mode='storm', schrift='hiragana'))
        db.session.commit()
        _fake_news(monkeypatch)
        base = client.get('/api/welcome-back').get_json()
        if base['due_total'] or base['undiscovered']:
            pytest.skip('Ausgangslage hat schon anderen Anzeige-Grund')
        assert base['show'] is False
        _fake_news(monkeypatch, date.today())
        data = client.get('/api/welcome-back').get_json()
        assert data['news']['updates'] == 1
        assert data['show'] is True

    def test_fresh_login_uses_previous_login(self, app, db, monkeypatch):
        """Frischer Login ueberschreibt last_login — Referenz bleibt der Login davor."""
        user = UserFactory(email='neu@test.com')
        user.last_activity_date = date.today() - timedelta(days=4)
        user.last_login = datetime.utcnow() - timedelta(days=4)
        db.session.commit()
        LessonFactory(instruction_language='german', created_at=datetime.utcnow() - timedelta(days=2))
        db.session.commit()
        _fake_news(monkeypatch)
        client = app.test_client()
        client.post('/login', data={'email': 'neu@test.com', 'password': 'Test123!'})
        with client.session_transaction() as sess:
            assert sess.get(news_service.PREV_LOGIN_SESSION_KEY)
        news = client.get('/api/welcome-back').get_json()['news']
        assert news['lessons'] == 1

    def test_dialog_js_renders_news_line(self, auth_client):
        client, user = auth_client
        html = client.get('/mein-lernen').get_data(as_text=True)
        assert 'Seit deinem letzten Besuch neu: ' in html
