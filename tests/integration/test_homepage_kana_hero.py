# tests/integration/test_homepage_kana_hero.py
"""Integration-Tests fuer den Gast-Hero der Startseite (Spiel-Launcher).

Stand 2026-06-17 (Redesign): Der Gast-Hero ist ein editorialer Split — links
Pitch + nummerierte Bruecken-Rail, rechts eine Spiel-Launcher-Karte mit
GETEILTEM Scope ($store.kanaScope) und einem Umschalter [Zuordnung | Kana Storm].
Beide Spiele starten im VOLLBILD (kein Inline-Spiel mehr im Hero): Zuordnung ueber
kanaSettings().startGame() -> /practice/kana/spiel, Storm ueber startStorm() ->
/practice/kana/storm. Das fruehere iframe-Embed (kanaEmbedHost) bleibt raus.
Pitch/USP/Trust sind SSR in der Sektion "Vom Spiel zum System". Eingeloggte
behalten ihren personalisierten Hero ohne Spiel-Embed.
"""


class TestGuestHero:
    def test_index_renders_for_guest(self, client, db):
        resp = client.get('/')
        assert resp.status_code == 200

    def test_guest_hero_has_game_launcher(self, client, db):
        body = client.get('/').get_data(as_text=True)
        # Gast-Hero = editorialer Split mit einer Spiel-Launcher-Karte (KEIN
        # Inline-Spiel mehr): geteilter Scope + Umschalter [Zuordnung | Kana Storm].
        assert 'home-hero-inner--split' in body
        assert 'kana-hero-card' in body
        # Geteilter Scope (Schrift-Chips + Reihen-Pills), an den Store gebunden.
        assert 'kana-hero-scope' in body
        assert '$store.kanaScope.setSchrift(' in body
        assert '$store.kanaScope.toggleRow(' in body
        assert 'kana_scope_store.js' in body
        # Spiel-Umschalter + beide Spiele.
        assert 'kana-hero-tabs' in body
        assert 'kana-hero-match' in body      # Zuordnung-Launcher
        assert 'kanaSettings()' in body
        assert 'Kana Storm' in body
        # Storm-Launcher (Vollbild) statt Inline-Storm-Engine im Hero.
        assert 'startStorm()' in body
        assert 'class="kstorm-hero"' not in body
        assert 'scopeExternal: true' not in body

    def test_hero_switcher_no_inline_storm(self, client, db):
        # Umschalter [Zuordnung | Kana Storm] im Hero; KEIN Inline-Storm mehr,
        # daher auch kein Storm-Daily-Tab-Markup auf der Startseite.
        body = client.get('/').get_data(as_text=True)
        assert 'kana-hero-tabs' in body
        assert 'Zuordnung' in body
        assert 'Kana Storm' in body
        # H1 traegt weiter den Query-Match "Hiragana lernen".
        assert 'Hiragana lernen' in body
        # Kein Inline-Storm → kein Storm-Tab-/Daily-Markup im Hero.
        assert 'kstorm__tabs' not in body
        assert 'Daily-Karte' not in body
        assert "goTab('daily')" not in body
        # Das fruehere Zuordnungs-iframe-Embed bleibt RAUS.
        assert 'x-data="kanaEmbedHost(' not in body
        assert '/practice/kana/embed' not in body

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

    def test_storm_launcher_targets_fullscreen(self, client, db):
        # Der Storm-Tab im Hero ist ein Launcher: startStorm() navigiert in die
        # Vollbild-Storm-Seite (kein Inline-Spiel, keine Matching-Ergebnis-Weiche).
        body = client.get('/').get_data(as_text=True)
        assert '/practice/kana/storm' in body
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
