# tests/integration/test_layout_review_stats.py
"""Layout-Standard Schritt 2 (docs/layout-standard.md): Mobile-Sticky-Fix,
/review (Schablone Spielansicht) und /review/stats (Schablone Dashboard).
"""
import re
from pathlib import Path

CSS_DIR = Path(__file__).resolve().parents[2] / 'app' / 'static' / 'css'


def _strip_comments(css):
    return re.sub(r'/\*.*?\*/', '', css, flags=re.S)


class TestMobileStickyFix:
    css = _strip_comments((CSS_DIR / 'mobile-improvements.css').read_text(encoding='utf-8'))

    def test_clip_overrides_hidden_where_supported(self):
        # overflow-x:hidden auf html+body macht body zum Scroll-Container,
        # dann klebt position:sticky mobil nicht. clip schneidet ohne das.
        block = re.search(r'@supports\s*\(overflow-x:\s*clip\)\s*\{(.*?)\}\s*\}', self.css, flags=re.S)
        assert block, 'clip-Regel fehlt'
        assert re.search(r'html,\s*body\s*\{\s*overflow-x:\s*clip\s*!important', block.group(1))

    def test_hidden_remains_as_fallback(self):
        # Browser ohne clip-Unterstützung behalten das bisherige Verhalten.
        assert self.css.count('overflow-x: hidden !important') == 2


class TestReviewPlayView:
    """/review + /review/produktion: Schablone C (Spielansicht)."""

    def _html(self, client, url):
        resp = client.get(url)
        assert resp.status_code == 200
        return resp.get_data(as_text=True)

    def test_review_uses_play_shell(self, auth_client):
        client, _user = auth_client
        html = self._html(client, '/review')
        assert 'class="page play-view review-screen"' in html
        assert 'class="play-bar review-topbar"' in html
        assert 'class="play-stage review-card-area" id="reviewCardArea"' in html
        assert 'class="play-actions review-buttons" id="reviewButtons"' in html
        # Tageslimit sitzt in der Leiste unter dem Fortschrittsbalken
        bar = html.split('class="play-bar review-topbar"')[1].split('play-stage')[0]
        assert 'id="dailyQuota"' in bar and 'id="sessionProgress"' in bar

    def test_review_states_share_surface(self, auth_client):
        client, _user = auth_client
        html = self._html(client, '/review')
        assert 'class="play-state review-empty" id="reviewEmpty"' in html
        assert 'class="play-state review-complete" id="reviewComplete"' in html

    def test_review_no_vertical_centering(self, auth_client):
        client, _user = auth_client
        html = self._html(client, '/review')
        assert 'margin-top: auto; }' not in html
        assert 'height: min(640px, 64dvh)' not in html

    def test_all_modes_still_wired(self, auth_client):
        client, _user = auth_client
        html = self._html(client, '/review')
        for marker in ('id="reviewUndoBtn"', 'id="reviewListenToggle"', 'toggleFrontRomaji()',
                       'id="nextRoundBtn"', 'id="sessionSummary"'):
            assert marker in html, marker

    def test_produktion_uses_play_shell(self, auth_client):
        client, _user = auth_client
        html = self._html(client, '/review/produktion')
        assert 'class="page play-view prod-stage"' in html
        assert 'class="play-bar prod-top"' in html
        assert 'class="play-stage prod-card-area" id="prodCardArea"' in html
        assert 'class="play-actions prod-buttons" id="prodButtons"' in html
        assert 'class="play-state prod-msg"' in html
