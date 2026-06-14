# tests/integration/test_homepage_kana_hero.py
"""Integration-Tests fuer den Gast-Hero der Startseite (Kana-Spiel als Hero).

Stand 2026-06-13: **Kana Storm** (inline, KEIN iframe) ist fuer Gaeste das
Hero-Spiel — es hat das fruehere Zuordnungs-Embed (kanaEmbedHost/iframe) als
Hero ersetzt. Das Zuordnungs-Spiel bleibt unter /practice/kana erreichbar
(Tages-Challenge / Lesen-Modus dort). Pitch/USP/Trust sind SSR in die Sektion
"Vom Spiel zum System" gewandert. Eingeloggte behalten ihren personalisierten
Hero ohne Spiel-Embed.
"""


class TestGuestHero:
    def test_index_renders_for_guest(self, client, db):
        resp = client.get('/')
        assert resp.status_code == 200

    def test_storm_is_hero_element(self, client, db):
        body = client.get('/').get_data(as_text=True)
        # Kana Storm ist der Gast-Hero — inline (kein iframe), eigene Komponente.
        # Die Komponente bekommt jetzt Optionen (initialTab) → 'kanaStormGame(' statt '()'.
        assert 'kanaStormGame(' in body
        assert 'class="kstorm-hero"' in body
        assert 'kana_storm.js' in body
        # Storm-Steuerung im Hero: glyph-forward Schrift-Picker + Reihen-Pills (SSR)
        assert 'setSchrift(' in body
        assert 'kstorm__pick' in body          # Glyph-Picker (あ/ア/あア)
        assert 'kstorm__chip' in body
        assert "toggleRow('k')" in body
        # Optionen sind hinter einem Disclosure eingeklappt
        assert 'kstorm__opt-toggle' in body

    def test_daily_tab_in_hero(self, client, db):
        # Der Daily-Tab (Wordle-artige Tageschallenge) ist im Hero erreichbar (SSR).
        body = client.get('/').get_data(as_text=True)
        assert 'kstorm__tabs' in body
        assert 'Daily-Karte' in body
        assert "goTab('daily')" in body
        assert 'startDaily(' in body
        # Storm bleibt der initial sichtbare Tab auf der Startseite.
        assert 'Kana Storm' in body
        # Das fruehere Zuordnungs-Embed ist als Hero RAUS
        assert 'x-data="kanaEmbedHost(' not in body
        assert '/practice/kana/embed' not in body
        # Zuordnungs-Spiel bleibt vom Hero aus verlinkt
        assert 'Zum Zuordnungs-Spiel' in body
        # H1 traegt weiter den Query-Match "Hiragana lernen"
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
        # 10.3: Bundle-Link aus der Hero-Aktionszeile entfernt (Dublette des
        # Bundle-Banners weiter unten) — Hero traegt nur noch den Gratis-Einstieg.
        assert 'Kostenlos starten' in body                    # Aktionszeile (Gratis-CTA)
        # NEGATIV: die entfernte Hero-Dublette darf NICHT mehr da sein. Der exakte
        # Link-Text "N5 Komplett · CHF 9.90" stand nur in der Hero-Aktionszeile
        # (das Bundle-Banner weiter unten formuliert anders), ebenso die direkt
        # daran haengende "30 Tage Geld zurück · Lifetime"-Note (<p home-bundle-note>).
        assert 'N5 Komplett · CHF 9.90' not in body
        assert '<p class="home-bundle-note">' not in body

    def test_meta_description_hat_spiel_hook(self, client, db):
        body = client.get('/').get_data(as_text=True)
        assert 'Spiel dich durch alle 46 Hiragana' in body
        # Head-Term muss in der Description bleiben (SERP-Bolding fuer die
        # Haupt-Query "Japanisch lernen", Pos.-Experiment laeuft ueber die H1).
        assert 'Japanisch lernen' in body

    def test_practice_kana_in_sitemap_und_robots(self, client, db):
        # /practice/kana ist seit dem Gast-Scope oeffentliches Feature und
        # prominent vom Hero verlinkt — crawlbar + gelistet, das Spiel selbst
        # (/practice/kana/spiel) bleibt gesperrt.
        robots = client.get('/robots.txt').get_data(as_text=True)
        assert 'Allow: /practice/kana$' in robots
        assert 'Disallow: /practice' in robots
        sitemap = client.get('/sitemap.xml').get_data(as_text=True)
        assert '/practice/kana</loc>' in sitemap

    def test_storm_hero_register_cta(self, client, db):
        # Storm-Hero hat keine A/B/C-Ergebnis-Weiche mehr (matching-spezifisch);
        # die Konto-CTA fuehrt nach der Registrierung in die Storm-Seite.
        body = client.get('/').get_data(as_text=True)
        assert ('next=/practice/kana/storm' in body
                or 'next=%2Fpractice%2Fkana%2Fstorm' in body)
        # Die alte Matching-Ergebnis-Weiche ist nicht mehr auf der Startseite.
        assert "branch() === 'A'" not in body


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
