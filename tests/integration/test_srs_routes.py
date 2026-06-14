# tests/integration/test_srs_routes.py
"""Integration-Tests fuer SRS-Endpoints (Phase 5 + Phase 6)."""
from app import db
from app.models import CardReviewState, UserAchievement
from tests.factories import (
    CardReviewStateFactory, LessonContentFactory, LessonFactory,
    VocabularyFactory,
)


class TestSRSStatsEndpoints:
    """I-SRS01 – I-SRS07: Statistik-Endpoints."""

    def test_stats_basic(self, auth_client):
        """I-SRS01: GET /api/srs/stats gibt Basis-Statistiken zurueck."""
        client, user = auth_client
        resp = client.get('/api/srs/stats')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'total_cards' in data
        assert 'due_count' in data
        assert 'current_streak' in data

    def test_stats_heatmap(self, auth_client):
        """I-SRS02: GET /api/srs/stats/heatmap gibt Heatmap-Daten zurueck."""
        client, user = auth_client
        resp = client.get('/api/srs/stats/heatmap')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'data' in data
        assert isinstance(data['data'], list)

    def test_stats_retention(self, auth_client):
        """I-SRS03: GET /api/srs/stats/retention gibt Retention-Daten zurueck."""
        client, user = auth_client
        resp = client.get('/api/srs/stats/retention')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'data' in data
        assert 'desired_retention' in data

    def test_stats_forecast(self, auth_client):
        """I-SRS04: GET /api/srs/stats/forecast gibt Forecast-Daten zurueck."""
        client, user = auth_client
        resp = client.get('/api/srs/stats/forecast')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'data' in data
        assert isinstance(data['data'], list)

    def test_stats_maturity(self, auth_client):
        """I-SRS05: GET /api/srs/stats/maturity gibt Verteilung zurueck."""
        client, user = auth_client
        resp = client.get('/api/srs/stats/maturity')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'Neu' in data

    def test_stats_content_type(self, auth_client):
        """I-SRS06: GET /api/srs/stats/content-type gibt Typ-Performance zurueck."""
        client, user = auth_client
        resp = client.get('/api/srs/stats/content-type')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'data' in data

    def test_stats_response_times(self, auth_client):
        """I-SRS07: GET /api/srs/stats/response-times gibt Histogramm zurueck."""
        client, user = auth_client
        resp = client.get('/api/srs/stats/response-times')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'data' in data

    def test_stats_leeches(self, auth_client):
        """I-SRS08: GET /api/srs/stats/leeches gibt Leech-Liste zurueck."""
        client, user = auth_client
        resp = client.get('/api/srs/stats/leeches')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'data' in data


class TestSRSBrowseEndpoints:
    """I-SRS10 – I-SRS16: Karten-Browser-Endpoints."""

    def test_browse_empty(self, auth_client):
        """I-SRS10: Browse ohne Karten gibt leere Liste zurueck."""
        client, user = auth_client
        resp = client.get('/api/srs/browse')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['cards'] == []
        assert data['total'] == 0

    def test_browse_with_cards(self, auth_client):
        """I-SRS11: Browse mit Karten gibt paginierte Ergebnisse zurueck."""
        client, user = auth_client
        lesson = LessonFactory()
        vocab = VocabularyFactory()
        content = LessonContentFactory(lesson_id=lesson.id, content_type='vocabulary', content_id=vocab.id)
        CardReviewStateFactory(user_id=user.id, content_id=content.id)
        db.session.commit()

        resp = client.get('/api/srs/browse')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['total'] == 1
        assert len(data['cards']) == 1
        assert data['cards'][0]['content_type'] == 'vocabulary'

    def test_browse_search(self, auth_client):
        """I-SRS12: Browse-Suche filtert nach Suchbegriff."""
        client, user = auth_client
        lesson = LessonFactory()
        vocab = VocabularyFactory(word='駅', reading='えき', meaning='station')
        content = LessonContentFactory(lesson_id=lesson.id, content_type='vocabulary', content_id=vocab.id)
        CardReviewStateFactory(user_id=user.id, content_id=content.id)
        db.session.commit()

        resp = client.get('/api/srs/browse?q=station')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['total'] == 1

    def test_browse_pagination(self, auth_client):
        """I-SRS13: Browse-Pagination funktioniert."""
        client, user = auth_client
        resp = client.get('/api/srs/browse?page=1&per_page=10')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'page' in data
        assert 'pages' in data

    def test_card_detail(self, auth_client):
        """I-SRS14: Karten-Detail gibt vollstaendige Info zurueck."""
        client, user = auth_client
        lesson = LessonFactory()
        vocab = VocabularyFactory()
        content = LessonContentFactory(lesson_id=lesson.id, content_type='vocabulary', content_id=vocab.id)
        CardReviewStateFactory(user_id=user.id, content_id=content.id)
        db.session.commit()

        resp = client.get(f'/api/srs/card/{content.id}/detail')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'srs_stage' in data
        assert 'stability' in data
        assert 'review_history' in data

    def test_card_detail_not_found(self, auth_client):
        """I-SRS15: Karten-Detail fuer unbekannte Karte gibt 404."""
        client, user = auth_client
        resp = client.get('/api/srs/card/99999/detail')
        assert resp.status_code == 404

    def test_bulk_suspend(self, auth_client):
        """I-SRS16: Bulk-Suspend aendert Status."""
        client, user = auth_client
        lesson = LessonFactory()
        vocab = VocabularyFactory()
        content = LessonContentFactory(lesson_id=lesson.id, content_type='vocabulary', content_id=vocab.id)
        state = CardReviewStateFactory(user_id=user.id, content_id=content.id, status='review')
        db.session.commit()

        resp = client.post('/api/srs/bulk-action', json={
            'action': 'suspend',
            'content_ids': [content.id],
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['affected'] == 1

        updated = CardReviewState.query.get(state.id)
        assert updated.status == 'suspended'


class TestSRSCardActions:
    """I-SRS20 – I-SRS22: Einzelkarten-Aktionen."""

    def test_suspend_card(self, auth_client):
        """I-SRS20: POST /api/srs/card/suspend."""
        client, user = auth_client
        lesson = LessonFactory()
        vocab = VocabularyFactory()
        content = LessonContentFactory(lesson_id=lesson.id, content_type='vocabulary', content_id=vocab.id)
        CardReviewStateFactory(user_id=user.id, content_id=content.id)
        db.session.commit()

        resp = client.post('/api/srs/card/suspend', json={'content_id': content.id})
        assert resp.status_code == 200
        assert resp.get_json()['success'] is True

    def test_reset_card(self, auth_client):
        """I-SRS21: POST /api/srs/card/reset setzt FSRS zurueck."""
        client, user = auth_client
        lesson = LessonFactory()
        vocab = VocabularyFactory()
        content = LessonContentFactory(lesson_id=lesson.id, content_type='vocabulary', content_id=vocab.id)
        CardReviewStateFactory(user_id=user.id, content_id=content.id, reps=10, lapses=5)
        db.session.commit()

        resp = client.post('/api/srs/card/reset', json={'content_id': content.id})
        assert resp.status_code == 200

        state = CardReviewState.query.filter_by(user_id=user.id, content_id=content.id).first()
        assert state.reps == 0
        assert state.lapses == 0
        assert state.status == 'new'


class TestSRSGamification:
    """I-SRS30 – I-SRS35: Gamification-Endpoints."""

    def test_rate_card_returns_xp(self, auth_client):
        """I-SRS30: POST /api/srs/rate gibt xp_earned zurueck."""
        client, user = auth_client
        lesson = LessonFactory()
        vocab = VocabularyFactory()
        content = LessonContentFactory(lesson_id=lesson.id, content_type='vocabulary', content_id=vocab.id)
        db.session.commit()

        resp = client.post('/api/srs/rate', json={
            'content_id': content.id,
            'rating': 3,
            'time_taken_ms': 5000,
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'xp_earned' in data
        assert data['xp_earned'] > 0
        assert 'level' in data
        assert 'card_stage' in data

    def test_rate_card_new_card_bonus(self, auth_client):
        """I-SRS31: Neue Karte gibt Bonus-XP."""
        client, user = auth_client
        lesson = LessonFactory()
        vocab = VocabularyFactory()
        content = LessonContentFactory(lesson_id=lesson.id, content_type='vocabulary', content_id=vocab.id)
        db.session.commit()

        resp = client.post('/api/srs/rate', json={
            'content_id': content.id,
            'rating': 3,
        })
        data = resp.get_json()
        # Good (10) + New Card Bonus (15) = 25
        assert data['xp_earned'] == 25

    def test_achievements_endpoint(self, auth_client):
        """I-SRS32: GET /api/srs/achievements gibt Achievements zurueck."""
        client, user = auth_client
        resp = client.get('/api/srs/achievements')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'unlocked' in data
        assert 'locked' in data

    def test_achievements_notify(self, auth_client):
        """I-SRS33: POST /api/srs/achievements/notify markiert als gesehen."""
        client, user = auth_client
        ach = UserAchievement(user_id=user.id, achievement_key='streak_3', notified=False)
        db.session.add(ach)
        db.session.commit()

        resp = client.post('/api/srs/achievements/notify', json={
            'achievement_keys': ['streak_3'],
        })
        assert resp.status_code == 200
        assert resp.get_json()['updated'] == 1

        updated = UserAchievement.query.filter_by(user_id=user.id, achievement_key='streak_3').first()
        assert updated.notified is True

    def test_jlpt_progress(self, auth_client):
        """I-SRS34: GET /api/srs/jlpt-progress gibt JLPT-Fortschritt zurueck."""
        client, user = auth_client
        resp = client.get('/api/srs/jlpt-progress')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'N5' in data
        assert 'percent' in data['N5']


class TestSRSPages:
    """I-SRS40 – I-SRS42: Seiten-Routen."""

    def test_review_page(self, auth_client):
        """I-SRS40: GET /review rendert Seite."""
        client, user = auth_client
        resp = client.get('/review')
        assert resp.status_code == 200

    def test_stats_page(self, auth_client):
        """I-SRS41: GET /review/stats rendert Statistik-Seite."""
        client, user = auth_client
        resp = client.get('/review/stats')
        assert resp.status_code == 200
        assert b'Statistiken' in resp.data

    def test_browse_page(self, auth_client):
        """I-SRS42: GET /review/browse rendert Browser-Seite."""
        client, user = auth_client
        resp = client.get('/review/browse')
        assert resp.status_code == 200
        assert b'Karten-Browser' in resp.data

    def test_kana_settings_page(self, auth_client):
        """I-SRS43: GET /practice/kana rendert die Einstellungs-Seite (Schritt 1).

        Viewport-gesperrt, mit kanaSettings()-Komponente und Start-CTA, die zur
        Spiel-Seite verlinkt.
        """
        client, user = auth_client
        resp = client.get('/practice/kana')
        assert resp.status_code == 200
        html = resp.get_data(as_text=True)
        assert 'kana-setup-locked' in html        # Viewport-Lock scharf
        assert '100dvh' in html
        assert 'kanaSettings()' in html            # Einstellungs-Komponente
        assert 'Spiel starten' in html             # Haupt-CTA
        assert '/practice/kana/spiel' not in html  # Navigation passiert via JS, nicht als statischer Link
        # Cache-Busting: das JS, das kanaSettings() definiert, MUSS versioniert
        # eingebunden sein — sonst servieren Browser nach einem Deploy die alte
        # Datei (ohne kanaSettings) und die Seite ist tot.
        assert 'kana_grid_game.js?v=' in html

    def test_kana_game_page(self, auth_client):
        """I-SRS44: GET /practice/kana/spiel rendert die Spiel-Seite (Schritt 2).

        Viewport-gesperrt, mit sichtbarem Timer (kgame__timer), kanaGameView()-
        Komponente und dem geerbten Kana-Gitter.
        """
        client, user = auth_client
        resp = client.get('/practice/kana/spiel')
        assert resp.status_code == 200
        html = resp.get_data(as_text=True)
        assert 'kana-game-locked' in html          # Viewport-Lock scharf
        assert '100dvh' in html
        assert 'kanaGameView()' in html            # Spiel-Komponente
        assert 'kgame__timer' in html              # sichtbarer Timer
        assert 'kana-grid-game__grid' in html      # geerbtes Gitter


class TestSRSAuth:
    """I-SRS50: Unauthentifizierte Zugriffe werden abgelehnt."""

    def test_stats_requires_auth(self, client):
        """I-SRS50: Stats-/Browse-API-Endpoints erfordern Login.

        Hinweis: /practice/kana(/spiel) sind seit dem Gast-Modus BEWUSST ohne
        Login erreichbar (Kana-Spiel fuer alle, Score-Speichern bleibt aber
        login-pflichtig) — sie stehen daher nicht mehr in dieser Liste.
        Abgedeckt in tests/integration/test_kana_practice_guest.py.
        Die 3 SEITEN /review, /review/stats, /review/browse zeigen Gaesten seit
        10.6 eine weiche Teaser-Landing (200) statt 302 — siehe TestReviewTeaser;
        nur die /api/srs/...-Endpoints bleiben hart login-pflichtig.
        """
        endpoints = [
            '/api/srs/stats', '/api/srs/stats/heatmap', '/api/srs/stats/retention',
            '/api/srs/stats/forecast', '/api/srs/stats/maturity',
            '/api/srs/browse', '/api/srs/achievements',
        ]
        for ep in endpoints:
            resp = client.get(ep)
            assert resp.status_code in (302, 401), f'{ep} should require auth, got {resp.status_code}'


class TestReviewTeaser:
    """10.6: Gaeste sehen auf den 3 Review-SEITEN eine weiche Teaser-Landing
    (200 + Register-CTA) statt eines harten Login-Redirects."""

    PAGES = ['/review', '/review/stats', '/review/browse']

    def test_guest_gets_teaser_not_redirect(self, client):
        """Gast → HTTP 200 mit Teaser-Text + Register-CTA (kein 302 auf /login)."""
        for path in self.PAGES:
            resp = client.get(path)
            assert resp.status_code == 200, f'{path} should be 200 for guest'
            body = resp.get_data(as_text=True)
            # Teaser-Nutzentext + kostenloses-Konto-Hinweis
            assert 'kostenlosen Konto' in body or 'kostenloses Konto' in body
            # Register-CTA fuehrt mit next zurueck auf die jeweilige Seite
            assert 'Kostenlos Konto erstellen' in body
            assert f'next={path}' in body
            # noindex (Thin-Content)
            assert 'noindex' in body

    def test_teaser_shows_no_user_data(self, client):
        """Teaser zeigt KEINE echten Nutzerdaten (kein Streak-/Stats-Zahlenblock)."""
        body = client.get('/review/stats').get_data(as_text=True)
        # Die echte stats.html-Seite haette die Storm-/Level-Sektion; der Teaser nicht.
        assert 'Konto erstellen' in body

    def test_authenticated_user_gets_real_page(self, auth_client):
        """Eingeloggt → unveraenderte echte Seite (kein Teaser)."""
        client, user = auth_client
        for path in self.PAGES:
            resp = client.get(path)
            assert resp.status_code == 200, f'{path} should be 200 for user'
            body = resp.get_data(as_text=True)
            assert 'Kostenlos Konto erstellen' not in body

    def test_api_endpoint_still_requires_auth(self, client):
        """Die /api/srs/...-Endpoints bleiben hart login-pflichtig (302/401)."""
        resp = client.get('/api/srs/stats')
        assert resp.status_code in (302, 401)
