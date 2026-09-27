# tests/integration/test_layout_standard.py
"""Layout-Standard (docs/layout-standard.md): Fundament + Kana-Pilot.

- base.html lädt layout.css nach custom.css/mobile-improvements.css.
- layout.css ist additiv: definiert die neuen Tokens/Klassen und überschreibt
  keine bestehenden Tokens (Garant für pixelgleiche Altseiten).
- Seitenkopf-Makro partials/_page_head.html rendert Titel/Untertitel/Kennzeile
  und optional Aktionen.
- /practice/kana nutzt die Schablone „Übungs-Konfiguration": .page-Hülle,
  Seitenkopf oben, keine vertikale Zentrierung, Vollhöhen-Lock nur für
  Storm/Schreiben.
"""
import re
from pathlib import Path

from flask import render_template_string

LAYOUT_CSS = Path(__file__).resolve().parents[2] / 'app' / 'static' / 'css' / 'layout.css'


class TestLayoutCssLoaded:
    def test_base_links_layout_css_after_custom(self, client, db):
        html = client.get('/login').get_data(as_text=True)
        assert 'css/layout.css?v=' in html
        # Reihenfolge: nach custom.css und mobile-improvements.css
        assert html.index('css/custom.css') < html.index('css/mobile-improvements.css') < html.index('css/layout.css')

    def test_layout_css_served(self, client, db):
        resp = client.get('/static/css/layout.css')
        assert resp.status_code == 200
        assert b'.page-head' in resp.data
        resp.close()


class TestLayoutCssIsAdditive:
    # Kommentare entfernen: dort dürfen bestehende Tokens erwähnt werden
    css = re.sub(r'/\*.*?\*/', '', LAYOUT_CSS.read_text(encoding='utf-8'), flags=re.S)

    def test_defines_standard_tokens(self):
        for token in ('--container-std:', '--container-wide:', '--container-prose:',
                      '--text-xs:', '--text-3xl:', '--surface-0:', '--surface-1:',
                      '--surface-2:', '--shadow-1:', '--space-24:'):
            assert token in self.css, token

    def test_does_not_redefine_existing_tokens(self):
        # --text-base und --space-1..16 gehören custom.css; eine Umdefinition
        # würde alle .redesign-page-Seiten verschieben.
        assert not re.search(r'--text-base\s*:', self.css)
        assert not re.search(r'--space-(1|2|3|4|6|8|12|16)\s*:', self.css)

    def test_no_global_element_selectors(self):
        # Additiv heisst: keine Regeln auf html/body/.container/main.
        assert not re.search(r'(^|[\s,}])(html|body|main|\.container)\s*[{,]', self.css)

    def test_mobile_first_breakpoints(self):
        # Basis = Handy; grössere Viewports nur per min-width (Ausnahme: Token
        # für die Bottom-Nav, die nur unter 768 px existiert).
        max_queries = re.findall(r'@media\s*\(max-width:\s*(\d+)px\)', self.css)
        assert max_queries == ['767']


class TestPageHeadMacro:
    def test_renders_title_subtitle_eyebrow(self, app):
        with app.test_request_context():
            html = render_template_string(
                "{% from 'partials/_page_head.html' import page_head %}"
                "{{ page_head('Statistik', subtitle='Dein Fortschritt', eyebrow='Übung', eyebrow_jp='かな') }}"
            )
        assert 'class="page-head"' in html
        assert '<h1 class="page-head__title" id="page-title">Statistik</h1>' in html
        assert 'page-head__sub' in html and 'Dein Fortschritt' in html
        assert '<span class="jp" lang="ja">かな</span>' in html
        assert 'page-head__actions' not in html

    def test_renders_actions_via_call(self, app):
        with app.test_request_context():
            html = render_template_string(
                "{% from 'partials/_page_head.html' import page_head %}"
                "{% call page_head('Karten') %}<a href='/x'>Export</a>{% endcall %}"
            )
        assert 'page-head__actions' in html
        assert "<a href='/x'>Export</a>" in html

    def test_subtitle_is_escaped_unless_markup(self, app):
        with app.test_request_context():
            html = render_template_string(
                "{% from 'partials/_page_head.html' import page_head %}"
                "{{ page_head('T', subtitle='<b>x</b>', subtitle_mobile=False) }}"
            )
        assert '&lt;b&gt;x&lt;/b&gt;' in html
        assert 'page-head__sub--desktop' in html


class TestKanaPilot:
    def test_uses_page_shell_and_head(self, client, db):
        html = client.get('/practice/kana').get_data(as_text=True)
        assert 'class="page kana-page"' in html
        assert 'class="page-head"' in html
        assert '<h1 class="page-head__title" id="page-title">Kana üben</h1>' in html
        # Kopf wird im laufenden Spiel ausgeblendet (Alpine)
        assert 'x-show="!hideChrome"' in html.split('class="page-head"')[1][:40]

    def test_no_vertical_centering(self, client, db):
        html = client.get('/practice/kana').get_data(as_text=True)
        # Der alte Desktop-Block zentrierte die Karte vertikal im Viewport.
        assert 'justify-content: center; padding: 2rem 1rem' not in html
        assert 'min-height: calc(100dvh - 60px)' not in html

    def test_lock_only_for_storm_and_spell(self, client, db):
        def body_class(url):
            html = client.get(url).get_data(as_text=True)
            return re.search(r'<body[^>]*class="([^"]*)"', html).group(1)

        assert 'kana-lock' not in body_class('/practice/kana')
        assert 'kana-lock' in body_class('/practice/kana?tab=storm')
        assert 'kana-lock' in body_class('/practice/kana?tab=spell')

    def test_settings_and_start_in_two_regions(self, client, db):
        html = client.get('/practice/kana').get_data(as_text=True)
        assert 'class="kana-aside"' in html
        assert 'kana-start surface' in html
        # Einstellungen stehen im Markup vor dem Start-Bereich (mobile Reihenfolge)
        assert html.index('kana-setup__scope"') < html.index('class="kana-aside"')

    def test_guest_sees_account_benefits_as_surface(self, client, db):
        html = client.get('/practice/kana').get_data(as_text=True)
        assert 'kana-setup__unlock surface' in html


class TestPruefenLayout:
    """/pruefen: Schablone A (Auswahl links, Start rechts), Session Schablone C."""

    def test_guest_uses_page_shell_and_head(self, client, db):
        html = client.get('/pruefen').get_data(as_text=True)
        assert 'class="page pruefen-page"' in html
        assert '<h1 class="page-head__title" id="page-title">Prüfen</h1>' in html
        assert 'page-split pruefen-split' in html
        assert 'surface pruefen-guest' in html
        # alte schmale Spalte weg
        assert 'max-width: 760px' not in html

    def test_logged_in_selection_left_start_right(self, auth_client):
        client, _ = auth_client
        html = client.get('/pruefen').get_data(as_text=True)
        assert 'pruefen-config surface' in html
        assert 'pruefen-summary' in html and 'data-primary' in html
        # Auswahl steht im Markup vor dem Start (mobile Reihenfolge)
        assert html.index('pruefen-config surface') < html.index('class="pruefen-aside')
        # Auswahl ist nicht mehr eingeklappt
        assert 'pruefen-config-toggle' not in html

    def test_session_is_page_with_surface(self, auth_client):
        client, _ = auth_client
        html = client.get('/pruefen/test?scope=all').get_data(as_text=True)
        assert 'class="page pf-stage"' in html
        assert 'pf-card surface' in html
        # Aktion sitzt in der Arbeitsfläche (vor deren Ende)
        card = html.split('pf-card surface')[1].split('</section>')[0]
        assert 'class="pf-actions"' in card
        assert 'pf-result-score surface' in html


class TestN5BundleLayout:
    def test_free_page_wide_shell_head_and_columns(self, client, db, app):
        app.config['FREE_MODE'] = True
        try:
            html = client.get('/n5-bundle').get_data(as_text=True)
        finally:
            app.config['FREE_MODE'] = False
        assert 'class="page page--wide bnd-page"' in html
        assert '<h1 class="page-head__title" id="page-title">JLPT N5 komplett.</h1>' in html
        # Kennzahlen direkt nach dem Seitenkopf, vor den Spalten
        assert html.index('class="page-head"') < html.index('class="bnd-stats"') < html.index('class="bnd-cols"')
        assert 'class="bnd-faq"' in html
        # kein Hero-Band mit schmaler Mittelspalte mehr
        assert 'hero-bg-jp' not in html and 'section-narrow' not in html


class TestNeuLayout:
    def test_prose_shell_and_head(self, client, db):
        html = client.get('/neu').get_data(as_text=True)
        assert 'class="page page--prose neu-page"' in html
        assert '<h1 class="page-head__title" id="page-title">Was ist neu?</h1>' in html
        assert 'neu-item surface' in html
        assert 'max-width: 760px' not in html


class TestLessonsKatalog:
    def test_guest_page_head_and_wide_shell(self, client, db):
        html = client.get('/lessons').get_data(as_text=True)
        assert 'class="page page--wide lessons-page"' in html
        assert '<h1 class="page-head__title" id="page-title">Japanisch lernen — der N5-Lehrplan</h1>' in html
        # Gratis-Start als Aktion im Seitenkopf
        assert 'lp-continue-cta' in html.split('page-head__actions')[1][:400]

    def test_css_uses_tokens_no_own_width(self, client, db):
        html = client.get('/lessons').get_data(as_text=True)
        assert 'max-width: 1152px' not in html
        # Modul-Leiste randlos über die Rinne, nicht über .page hinaus
        assert 'margin: 0 calc(-1 * var(--page-gutter)) var(--space-4)' in html


class TestStartseiteGast:
    """/ (Gast): .page--wide-Hülle, Hero-Band + Abschnitte mit Überschrift."""

    def test_wide_shell_and_sections(self, client, db):
        html = client.get('/').get_data(as_text=True)
        assert 'class="page page--wide home-page"' in html
        assert 'class="home-section vom-spiel-section"' in html
        assert 'class="lernpfad-section"' in html
        assert html.count('<h1') == 1
        # eigene Breiten + Voll-Bleed-Hülle entfallen
        assert 'max-width: 1152px' not in html
        assert '.home-wrapper' not in html and 'class="home-wrapper"' not in html

    def test_lernpfad_as_tile_grid(self, client, db):
        html = client.get('/').get_data(as_text=True)
        assert 'repeat(auto-fill, minmax(min(280px, 100%), 1fr))' in html
        # alter Zickzack-Pfad (SVG-Stationen) ist weg
        assert 'path-svg' not in html and 'station-node' not in html

    def test_dark_mode_only_token_exceptions(self, client, db):
        html = client.get('/').get_data(as_text=True)
        # Flächen laufen über --surface-*; keine Dark-Regeln für Trust/Brücke/Chips mehr
        assert '[data-theme="dark"] .trust-block' not in html
        assert '[data-theme="dark"] .kana-bridge' not in html
        assert '[data-theme="dark"] .kana-chip,' not in html
        assert '[data-theme="dark"] .lp-modnum' not in html


class TestStartseiteEingeloggt:
    """/ (eingeloggt): Schablone Dashboard-Einstieg — Seitenkopf mit Aktion, Kacheln."""

    def test_page_head_with_primary_action(self, auth_client):
        client, user = auth_client
        html = client.get('/').get_data(as_text=True)
        assert 'class="page page--wide home-page home-page--auth"' in html
        assert '<h1 class="page-head__title" id="page-title">Bereit für deine erste Lektion?</h1>' in html
        actions = html.split('page-head__actions')[1][:600]
        assert 'data-primary' in actions and 'href="#lernpfad"' in actions
        # Begrüssung steht im Seitenkopf (Untertitel)
        assert user.username in html.split('page-head__sub')[1][:400]

    def test_entry_tiles(self, auth_client):
        client, _ = auth_client
        html = client.get('/').get_data(as_text=True)
        tiles = html.split('grid-tiles home-tiles')[1].split('</section>')[0]
        assert 'id="homeReviewLink"' in tiles and '/review' in tiles
        assert '/mein-lernen' in tiles
        assert '/neu' in tiles  # neuester Eintrag aus neuigkeiten.md

    def test_no_auto_scroll_away_from_action(self, auth_client):
        client, _ = auth_client
        html = client.get('/').get_data(as_text=True)
        assert 'scrollIntoView' not in html.split('grid-tiles home-tiles')[1]
