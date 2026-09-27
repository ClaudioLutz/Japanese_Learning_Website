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
