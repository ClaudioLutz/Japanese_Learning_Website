# tests/integration/test_kana_practice_guest.py
"""Integration-Tests fuer den Gast-Modus des Kana-Spiels (ohne Login).

Deckt die public-Session-API, die gast-offenen Spiel-Seiten + das iframe-Embed,
die gast-faehige Tages-Challenge / Verwechslungs-Drill sowie die Absicherung,
dass Score-Speichern (rate) login-pflichtig bleibt und die eingeloggte
Session-API unveraendert funktioniert.
"""
from app.services.kana_rows import HIRAGANA_ROWS, KATAKANA_ROWS
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


def _seed_katakana(db, rows=('vowels', 'k')):
    """Legt echte Gojuon-Katakana an (analog zu _seed_hiragana)."""
    created = []
    for key in rows:
        for ch in KATAKANA_ROWS[key]:
            created.append(KanaFactory(character=ch, romanization='x', type='katakana'))
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

    def test_default_is_hiragana_without_dakuten(self, client, db):
        # Ohne Params bleibt der Endpoint beim Grund-Hiragana (Startseiten-Embed):
        # kein Katakana, keine Dakuten-Reihen — auch wenn beides in der DB liegt.
        _seed_katakana(db, rows=('vowels',))
        _seed_hiragana(db, rows=('vowels', 'g'))
        data = client.get('/api/practice/kana/session/public').get_json()
        chars = {i['character'] for i in data['kana']}
        assert 'あ' in chars
        assert 'ア' not in chars
        assert 'が' not in chars
        assert all(i['type'] == 'hiragana' for i in data['kana'])

    def test_katakana_via_param(self, client, db):
        _seed_hiragana(db, rows=('vowels',))
        _seed_katakana(db, rows=('vowels',))
        data = client.get('/api/practice/kana/session/public?schrift=katakana').get_json()
        chars = {i['character'] for i in data['kana']}
        assert 'ア' in chars
        assert 'あ' not in chars
        assert all(i['type'] == 'katakana' for i in data['kana'])

    def test_both_scripts_via_param(self, client, db):
        _seed_hiragana(db, rows=('vowels',))
        _seed_katakana(db, rows=('vowels',))
        data = client.get('/api/practice/kana/session/public?schrift=both').get_json()
        types = {i['type'] for i in data['kana']}
        assert types == {'hiragana', 'katakana'}

    def test_blind_mode_falls_back_to_schreiben(self, client, db):
        # Blind ist als Practice-Option entfernt — alte URLs/localStorage-Werte
        # fallen serverseitig sauber auf 'schreiben' zurueck.
        _seed_hiragana(db, rows=('vowels',))
        data = client.get('/api/practice/kana/session/public?mode=blind').get_json()
        assert data['mode'] == 'schreiben'

    def test_invalid_schrift_falls_back_to_hiragana(self, client, db):
        _seed_hiragana(db, rows=('vowels',))
        _seed_katakana(db, rows=('vowels',))
        data = client.get('/api/practice/kana/session/public?schrift=klingonisch').get_json()
        assert data['filters']['schrift'] == 'hiragana'
        assert all(i['type'] == 'hiragana' for i in data['kana'])

    def test_rows_filter(self, client, db):
        _seed_hiragana(db, rows=('vowels', 'k', 's'))
        data = client.get('/api/practice/kana/session/public?rows=k').get_json()
        chars = {i['character'] for i in data['kana']}
        assert chars == set(HIRAGANA_ROWS['k'])

    def test_dakuten_param(self, client, db):
        _seed_hiragana(db, rows=('vowels', 'g'))
        data = client.get('/api/practice/kana/session/public?dakuten=true').get_json()
        chars = {i['character'] for i in data['kana']}
        assert 'が' in chars

    def test_unknown_rows_yield_message(self, client, db):
        _seed_hiragana(db, rows=('vowels',))
        data = client.get('/api/practice/kana/session/public?rows=zz').get_json()
        assert data['count'] == 0
        assert 'Auswahl' in data['message']

    def test_limit_subset_keeps_gojuon_order(self, client, db):
        # Zufaelliges Teilset, aber in Gojuon-Reihenfolge (Grid gruppiert nach Reihen).
        _seed_hiragana(db, rows=GRUND_ROWS)
        full = [ch for key in GRUND_ROWS for ch in HIRAGANA_ROWS[key]]
        data = client.get('/api/practice/kana/session/public?limit=10').get_json()
        got = [i['character'] for i in data['kana']]
        assert len(got) == 10
        assert got == sorted(got, key=full.index)

    def test_negative_limit_does_not_crash(self, client, db):
        # Regression: limit<0 lief in random.sample mit negativem k -> 500.
        _seed_hiragana(db, rows=('vowels',))
        resp = client.get('/api/practice/kana/session/public?limit=-1')
        assert resp.status_code == 200
        assert resp.get_json()['count'] > 0

    def test_zero_limit_falls_back_to_default(self, client, db):
        # limit=0 darf weder crashen noch die irrefuehrende Outage-Meldung liefern.
        _seed_hiragana(db, rows=('vowels',))
        data = client.get('/api/practice/kana/session/public?limit=0').get_json()
        assert data['count'] > 0
        assert 'message' not in data

    def test_explicit_dakuten_row_overrides_dakuten_switch(self, client, db):
        # Wer den G-Chip waehlt, will die G-Reihe ueben — auch wenn der
        # Dakuten-Schalter (z.B. aus localStorage) auf aus steht.
        _seed_hiragana(db, rows=('vowels', 'g'))
        data = client.get('/api/practice/kana/session/public?rows=g&dakuten=false').get_json()
        chars = {i['character'] for i in data['kana']}
        assert chars == set(HIRAGANA_ROWS['g'])


class TestFreshAccountFallback:
    """Neukonto (0 abgeschlossene Lessons) bekommt den Gast-Referenz-Scope —
    Registrieren (der Haupt-Conversion-Pfad der Startseite) darf den
    spielbaren Umfang nie verkleinern."""

    def test_session_falls_back_to_guest_scope(self, auth_client, db):
        client, _user = auth_client
        _seed_hiragana(db, rows=('vowels', 'k'))
        data = client.get('/api/practice/kana/session').get_json()
        assert data['count'] > 0
        assert 'message' not in data
        # Kein SRS-Rating fuer Fallback-Karten (kein Unlock dahinter).
        assert all(i['lesson_content_id'] is None for i in data['kana'])

    def test_session_fallback_respects_filters(self, auth_client, db):
        client, _user = auth_client
        _seed_hiragana(db, rows=('vowels',))
        _seed_katakana(db, rows=('vowels',))
        data = client.get('/api/practice/kana/session?schrift=katakana').get_json()
        assert data['count'] > 0
        assert all(i['type'] == 'katakana' for i in data['kana'])

    def test_weak_only_still_explains_itself(self, auth_client, db):
        # weak_only braucht User-State — ohne Reviews gibt es nichts Schwaches.
        client, _user = auth_client
        _seed_hiragana(db, rows=('vowels',))
        data = client.get('/api/practice/kana/session?weak_only=true').get_json()
        assert data['count'] == 0
        assert 'schwachen' in data['message']

    def test_daily_falls_back_without_bonus(self, auth_client, db):
        client, _user = auth_client
        _seed_hiragana(db, rows=GRUND_ROWS)
        data = client.get('/api/practice/kana/daily-challenge').get_json()
        assert data['count'] > 0
        # Bonus-XP waere ein leeres Versprechen (Fallback-Karten haben kein
        # lesson_content_id -> keine Gutschrift moeglich).
        assert data['bonus_xp'] == 0

    def test_no_lesson_content_id_for_guest(self, client, db):
        # Gaeste raten nicht ans SRS -> keine lesson_content_id (rateCell skippt).
        _seed_hiragana(db, rows=('vowels',))
        data = client.get('/api/practice/kana/session/public').get_json()
        assert all(i['lesson_content_id'] is None for i in data['kana'])

    def test_respects_explicit_limit(self, client, db):
        # limit bleibt als optionaler API-Param erhalten (z.B. Deep-Links).
        _seed_hiragana(db, rows=GRUND_ROWS)
        data = client.get('/api/practice/kana/session/public?limit=5').get_json()
        assert data['count'] == 5

    def test_default_returns_full_selection(self, client, db):
        # Kein limit-Param = die Anzahl richtet sich nach der Auswahl:
        # komplettes Grund-Hiragana (46) — es gibt keinen Anzahl-Regler mehr.
        _seed_hiragana(db, rows=GRUND_ROWS)
        data = client.get('/api/practice/kana/session/public').get_json()
        assert data['count'] == 46

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


class TestKanaStorm:
    """Kana Storm — eigenstaendiger Arcade-Modus (inline, kein iframe), ohne Login."""

    def test_storm_page_open_for_guest(self, client, db):
        resp = client.get('/practice/kana/storm')
        assert resp.status_code == 200
        body = resp.get_data(as_text=True)
        # Eigenstaendige Inline-Komponente + Storm-Markup (kein iframe-Embed).
        assert 'kanaStormGame()' in body
        assert 'Kana Storm' in body
        assert 'class="kstorm"' in body
        assert '<iframe' not in body

    def test_settings_page_links_to_storm(self, client, db):
        # Die Einstellungsseite (/practice/kana) verweist auf den Storm-Modus.
        resp = client.get('/practice/kana')
        assert resp.status_code == 200
        assert '/practice/kana/storm' in resp.get_data(as_text=True)

    def test_homepage_shows_storm_card_for_guest(self, client, db):
        # Storm ist der Gast-Hero der Startseite (inline, kein iframe); das
        # Storm-Skript ist global eingebunden, das Matching-Embed ist raus.
        resp = client.get('/')
        assert resp.status_code == 200
        body = resp.get_data(as_text=True)
        assert 'kstorm-hero' in body
        assert 'kanaStormGame()' in body
        assert 'kana_storm.js' in body
        assert 'x-data="kanaEmbedHost(' not in body

    def test_storm_uses_existing_public_api(self, client, db):
        # Kein zweites Kana-Dataset: Storm zieht die Kana ueber den bestehenden
        # Gast-Endpoint (mit echten Gojuon-Hiragana liefert er > 0).
        _seed_hiragana(db, rows=('vowels', 'k'))
        data = client.get('/api/practice/kana/session/public?schrift=hiragana&dakuten=false').get_json()
        assert data['count'] > 0
        assert all(i['type'] == 'hiragana' for i in data['kana'])

    def test_storm_page_has_row_selection(self, client, db):
        # Storm laesst nur die gewaehlten Gojuon-Reihen spielen (z.B. nur
        # あいうえお + K) — die Reihen-Pills sind SSR gerendert.
        body = client.get('/practice/kana/storm').get_data(as_text=True)
        assert 'kstorm__chip' in body
        assert 'toggleRow(' in body
        assert 'selectAllRows()' in body
        assert 'あいうえお' in body  # Vokal-Reihe-Pill

    def test_storm_rows_param_limits_pool(self, client, db):
        # Datenpfad fuer die Reihen-Auswahl: rows=vowels,k liefert NUR diese Reihen.
        _seed_hiragana(db, rows=('vowels', 'k', 's', 't'))
        data = client.get(
            '/api/practice/kana/session/public?schrift=hiragana&dakuten=false&rows=vowels,k'
        ).get_json()
        chars = {i['character'] for i in data['kana']}
        assert chars == set(HIRAGANA_ROWS['vowels']) | set(HIRAGANA_ROWS['k'])
        assert data['count'] == 10


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
