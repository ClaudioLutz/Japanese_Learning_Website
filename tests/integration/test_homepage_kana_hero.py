# tests/integration/test_homepage_kana_hero.py
"""Integration-Tests fuer den Gast-Hero der Startseite (Kana-Spiel als Hero).

Der Umbau 2026-06: Das Kana-Spiel (iframe-Embed) ist fuer Gaeste das
Hero-Element; die fruehere Vokal-Probe (5 Flip-Karten) ist entfernt.
Pitch/USP/Trust sind SSR in die Sektion "Vom Spiel zum System" gewandert.
Eingeloggte behalten ihren personalisierten Hero ohne Spiel-Embed.
"""


class TestGuestHero:
    def test_index_renders_for_guest(self, client, db):
        resp = client.get('/')
        assert resp.status_code == 200

    def test_game_is_hero_element(self, client, db):
        body = client.get('/').get_data(as_text=True)
        # Host-Komponente + Embed-Route im Gast-Zweig
        assert 'kanaEmbedHost' in body
        assert '/practice/kana/embed' in body
        # Spielart-Chips (einzige Steuer-Ebene auf der Startseite)
        assert 'kana-chip-row' in body
        assert 'Tages-Challenge' in body
        # H1 traegt den Query-Match "Hiragana lernen"
        assert 'Hiragana lernen' in body

    def test_vokal_probe_removed(self, client, db):
        body = client.get('/').get_data(as_text=True)
        assert 'kanaStage' not in body
        assert 'home-browser-frame' not in body
        assert 'vowel_demo_played' not in body.replace(
            '(ersetzt vowel_demo_played', '').replace('ersetzt vowel_demo_played.)', '')

    def test_ssr_substanz_bleibt(self, client, db):
        # SEO: Pitch/USP/Trust + Bruecken-Leiste muessen serverseitig im HTML stehen
        # (Soft-404-Lehre: kein JS-only-Content fuer die Kern-Botschaft).
        body = client.get('/').get_data(as_text=True)
        assert 'Japanisch lernen mit System' in body          # H2 der Vom-Spiel-Sektion
        assert 'Strikt nach offizieller JLPT-N5-Liste' in body  # Trust-Block
        assert 'Dein Weg in 3 Schritten' in body              # Bruecken-Leiste
        assert 'N5 Komplett · CHF 9.90' in body               # Aktionszeile

    def test_meta_description_hat_spiel_hook(self, client, db):
        body = client.get('/').get_data(as_text=True)
        assert 'Spiel dich durch alle 46 Hiragana' in body

    def test_result_card_branches_vorhanden(self, client, db):
        # Ergebnis-Weiche: alle drei Branch-Templates muessen im Markup liegen.
        body = client.get('/').get_data(as_text=True)
        assert "branch() === 'A'" in body
        assert "branch() === 'B'" in body
        assert "branch() === 'C'" in body
        # Konto-CTA fuehrt nach der Registrierung in die Spiel-Seite (next-Param;
        # Flask laesst '/' im Query-String unkodiert).
        assert ('next=/practice/kana/spiel' in body
                or 'next=%2Fpractice%2Fkana%2Fspiel' in body)


class TestAuthenticatedHero:
    def test_no_game_embed_for_logged_in(self, auth_client, db):
        client, _user = auth_client
        body = client.get('/').get_data(as_text=True)
        # Eingeloggte behalten ihren personalisierten Hero ohne Spiel-iframe
        # (strukturelle Marker pruefen, keine blossen Woerter in Kommentaren).
        assert 'x-data="kanaEmbedHost(' not in body
        assert '/practice/kana/embed' not in body

    def test_start_strip_references_kana_game(self, auth_client, db):
        client, _user = auth_client
        body = client.get('/').get_data(as_text=True)
        # Der "Dein Start"-Strip verweist aufs Kana-Spiel (nicht mehr auf die
        # geloeschte Vokal-Probe).
        assert 'Vokal-Probe' not in body
        assert 'Kana-Spiel ausprobieren' in body
