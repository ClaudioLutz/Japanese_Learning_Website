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
