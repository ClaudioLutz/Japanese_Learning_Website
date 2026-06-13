"""Der ``highlight_romaji``-Jinja-Filter markiert das Zielwort im Satz-Romaji —
das Pendant zu ``highlight_vocab`` fuer den japanischen Satz. So ist das zu
lernende Wort auf der Karten-Vorderseite in BEIDEN Schriften (Japanisch +
Romaji) mit ``vocab-target-highlight`` hervorgehoben/unterstrichen.

Verhalten: case-insensitiv (Satzanfang ist gross), Wortgrenzen-Match (kein
Treffer mitten in einem anderen Wort), nur erstes Vorkommen, scheitert leise
(z.B. bei Flexion: 'furu' steht nicht als ganzes Wort in 'furimasu').
"""
import pytest


@pytest.fixture
def highlight_romaji(app):
    return app.jinja_env.filters["highlight_romaji"]


class TestHighlightRomaji:
    def test_marks_word_in_sentence(self, highlight_romaji):
        out = highlight_romaji("Kono heya wa atatakai desu.", "atatakai")
        assert '<span class="vocab-target-highlight">atatakai</span>' in out

    def test_case_insensitive_at_sentence_start(self, highlight_romaji):
        # Wort am Satzanfang ist grossgeschrieben -> Treffer, Original-Schreibung bleibt.
        out = highlight_romaji("Fuyu wa takusan yuki ga furimasu.", "fuyu")
        assert '<span class="vocab-target-highlight">Fuyu</span>' in out

    def test_only_first_occurrence(self, highlight_romaji):
        out = highlight_romaji("Aki wa samui desu. Aki ga suki desu.", "aki")
        assert out.count("vocab-target-highlight") == 1
        assert out.startswith('<span class="vocab-target-highlight">Aki</span>')

    def test_word_boundary_no_partial_match(self, highlight_romaji):
        # 'yuki' darf NICHT als Praefix von 'Yukidaruma' getroffen werden.
        out = highlight_romaji("Yukidaruma o tsukurimasu.", "yuki")
        assert "vocab-target-highlight" not in out

    def test_conjugated_verb_no_match_graceful(self, highlight_romaji):
        # 'furu' steht nicht als ganzes Wort in 'furimasu' -> kein Highlight, Satz roh.
        out = highlight_romaji("Fuyu wa takusan yuki ga furimasu.", "furu")
        assert "vocab-target-highlight" not in out
        assert out == "Fuyu wa takusan yuki ga furimasu."

    def test_empty_word_returns_plain(self, highlight_romaji):
        out = highlight_romaji("Kono heya wa atatakai desu.", "")
        assert "vocab-target-highlight" not in out
        assert out == "Kono heya wa atatakai desu."

    def test_none_word_returns_plain(self, highlight_romaji):
        out = highlight_romaji("Kono heya wa atatakai desu.", None)
        assert "vocab-target-highlight" not in out

    def test_empty_sentence_returns_empty(self, highlight_romaji):
        assert highlight_romaji("", "atatakai") == ""

    def test_html_is_escaped(self, highlight_romaji):
        # Defensive: HTML im Satz wird escaped (keine Injection), Wort trotzdem markiert.
        out = highlight_romaji("a <b> yuki desu.", "yuki")
        assert "<b>" not in out
        assert "&lt;b&gt;" in out
        assert '<span class="vocab-target-highlight">yuki</span>' in out
