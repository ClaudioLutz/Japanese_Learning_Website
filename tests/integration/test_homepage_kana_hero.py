# tests/integration/test_homepage_kana_hero.py
"""Integration-Tests fuer den Gast-Hero der Startseite (Kana-Spiele als Hero).

Stand 2026-06-14: Der Gast-Hero bietet BEIDE Kana-Spiele (inline, KEIN iframe)
ueber einen Umschalter [Kana Storm | Zuordnung] mit GETEILTEM Scope
($store.kanaScope), genau wie /practice/kana. Storm spielt inline; Zuordnung
zeigt ein kompaktes Setup und startet das Spiel im Vollbild (/practice/kana/spiel).
Das fruehere iframe-Embed (kanaEmbedHost) ist raus. Pitch/USP/Trust sind SSR in
die Sektion "Vom Spiel zum System" gewandert. Eingeloggte behalten ihren
personalisierten Hero ohne Spiel-Embed.
"""


class TestGuestHero:
    def test_index_renders_for_guest(self, client, db):
        resp = client.get('/')
        assert resp.status_code == 200

    def test_storm_is_hero_element(self, client, db):
        body = client.get('/').get_data(as_text=True)
        # Der Gast-Hero bietet BEIDE Kana-Spiele ueber einen Umschalter
        # [Kana Storm | Zuordnung] mit GETEILTEM Scope ($store.kanaScope),
        # genau wie /practice/kana. Storm spielt inline (kein iframe).
        assert 'kanaStormGame(' in body
        assert 'class="kstorm-hero"' in body
        assert 'kana_storm.js' in body
        # Geteilter Scope (Schrift-Chips + Reihen-Pills), an den Store gebunden.
        assert 'kana-hero-scope' in body
        assert '$store.kanaScope.setSchrift(' in body
        assert '$store.kanaScope.toggleRow(' in body
        assert 'kana_scope_store.js' in body
        # Spiel-Umschalter + kompaktes Matching-Setup (startet das Spiel im Vollbild).
        assert 'kana-hero-tabs' in body
        assert 'kana-hero-match' in body
        assert 'kanaSettings()' in body
        # Storm liest den geteilten Scope (interne Picker ausgeblendet).
        assert 'scopeExternal: true' in body

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
        # Das Zuordnungs-Spiel ist jetzt ein gleichwertiger Tab im Hero (kein
        # blosser "Zum Zuordnungs-Spiel"-Link mehr).
        assert 'Zum Zuordnungs-Spiel' not in body
        assert 'kana-hero-tabs' in body
        assert 'Zuordnung' in body
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
