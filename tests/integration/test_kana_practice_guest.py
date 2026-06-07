# tests/integration/test_kana_practice_guest.py
"""Integration-Tests fuer den Gast-Modus des Kana-Spiels (ohne Login).

Deckt die public-Session-API, die gast-offenen Spiel-Seiten + das iframe-Embed,
die gast-faehige Tages-Challenge / Verwechslungs-Drill sowie die Absicherung,
dass Score-Speichern (rate) login-pflichtig bleibt und die eingeloggte
Session-API unveraendert funktioniert.
"""
from app.services.kana_rows import HIRAGANA_ROWS
from tests.factories import KanaFactory

GRUND_ROWS = tuple(HIRAGANA_ROWS.keys())[:11]  # vowels..n_kons (ohne Dakuten)


def _seed_hiragana(db, rows=('vowels', 'k', 's', 't')):
    """Legt echte Gojuon-Hiragana an.

    Die KanaFactory-Sequence (chr(0x3042 + n)) trifft die sauberen Gojuon-Zeichen
    nicht, daher legen wir sie hier explizit anhand der kanonischen Reihen an.
    """
    created = []
    for key in rows:
        for ch in HIRAGANA_ROWS[key]:
            created.append(KanaFactory(character=ch, romanization='x', type='hiragana'))
    db.session.commit()
    return created


class TestGuestPublicSession:
    """Die gast-offene Session-API (Startseiten-Embed)."""

    def test_no_login_required(self, client, db):
        _seed_hiragana(db)
        resp = client.get('/api/practice/kana/session/public')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['guest'] is True
        assert data['count'] > 0

    def test_only_hiragana_returned(self, client, db):
        # Auch wenn Katakana existiert: der Gast-Endpoint liefert nur Hiragana.
        KanaFactory(character='ア', romanization='a', type='katakana')
        _seed_hiragana(db, rows=('vowels',))
        data = client.get('/api/practice/kana/session/public').get_json()
        chars = {i['character'] for i in data['kana']}
        assert 'あ' in chars
        assert 'ア' not in chars
        assert all(i['type'] == 'hiragana' for i in data['kana'])

    def test_no_lesson_content_id_for_guest(self, client, db):
        # Gaeste raten nicht ans SRS -> keine lesson_content_id (rateCell skippt).
        _seed_hiragana(db, rows=('vowels',))
        data = client.get('/api/practice/kana/session/public').get_json()
        assert all(i['lesson_content_id'] is None for i in data['kana'])

    def test_respects_limit(self, client, db):
        _seed_hiragana(db, rows=GRUND_ROWS)
        data = client.get('/api/practice/kana/session/public?limit=5').get_json()
        assert data['count'] == 5

    def test_limit_capped_at_50(self, client, db):
        _seed_hiragana(db, rows=GRUND_ROWS)
        data = client.get('/api/practice/kana/session/public?limit=999').get_json()
        assert data['count'] <= 50

    def test_does_not_write_to_db(self, client, db):
        from app.models import CardReviewState
        _seed_hiragana(db, rows=('vowels',))
        before = CardReviewState.query.count()
        client.get('/api/practice/kana/session/public')
        assert CardReviewState.query.count() == before


class TestGuestPages:
    """Die Spiel-Seiten sind ohne Login erreichbar (vorher login-gated)."""

    def test_settings_page_open_for_guest(self, client, db):
        resp = client.get('/practice/kana')
        assert resp.status_code == 200

    def test_game_page_open_for_guest(self, client, db):
        resp = client.get('/practice/kana/spiel')
        assert resp.status_code == 200

    def test_embed_layout_renders(self, client, db):
        resp = client.get('/practice/kana/embed')
        assert resp.status_code == 200
        body = resp.get_data(as_text=True)
        assert 'window.kgameEmbed = true' in body
        # Embed laeuft immer als Gast.
        assert 'window.currentUser = null' in body


class TestGuestDailyConfusion:
    """Tages-Challenge + Verwechslungs-Drill sind gast-faehig (Scope 'Voll')."""

    def test_daily_challenge_guest(self, client, db):
        _seed_hiragana(db, rows=GRUND_ROWS)
        resp = client.get('/api/practice/kana/daily-challenge')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['count'] > 0
        # Gaeste bekommen keine Bonus-XP (kein Konto zum Gutschreiben).
        assert data['bonus_xp'] == 0

    def test_daily_challenge_deterministic_per_day(self, client, db):
        _seed_hiragana(db, rows=GRUND_ROWS)
        a = client.get('/api/practice/kana/daily-challenge').get_json()
        b = client.get('/api/practice/kana/daily-challenge').get_json()
        assert [k['character'] for k in a['kana']] == [k['character'] for k in b['kana']]

    def test_confusion_guest_generic_clusters(self, client, db):
        # き/さ und さ/ち sind kanonische Verwechslungs-Cluster.
        _seed_hiragana(db, rows=('vowels', 'k', 's', 't'))
        resp = client.get('/api/practice/kana/confusion')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['count'] > 0
        assert data.get('layout') == 'confusion'


class TestScoreStillProtected:
    """Score-Speichern bleibt login-pflichtig; eingeloggte API unveraendert."""

    def test_rate_requires_login(self, client, db):
        resp = client.post('/api/srs/rate', json={'content_id': 1, 'rating': 3})
        assert resp.status_code in (401, 302)

    def test_authenticated_session_still_works(self, auth_client, db):
        client, _user = auth_client
        resp = client.get('/api/practice/kana/session')
        assert resp.status_code == 200
