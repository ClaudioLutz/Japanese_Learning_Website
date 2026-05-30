"""Regression: Cloze-Grammatikkarten muessen IMMER eine Romaji-Lesehilfe auf der
Vorderseite zeigen, sobald der Beispielsatz ueberhaupt ein Romaji hat.

Frueher lieferte ``_mask_romaji`` '' (und damit eine leere Romaji-Zeile), wenn
die maskierte Antwort im Satz-Romaji nicht als ganzes Wort auffindbar war —
typisch bei Kanji-Antworten ohne Kana-Umschrift (今/時/分) oder bei Endungen wie
ます/です, die im Romaji als Wortsuffix stehen. Das war die Ursache fuer die ~40
Grammatikkarten ohne Romaji auf der Vorderseite im SRS-Review.
"""
from app.models import _mask_romaji, make_grammar_cloze


class TestMaskRomajiFallback:
    def test_particle_masked_at_word_boundary(self):
        # Auffindbare Partikel werden weiterhin sauber maskiert (keine Regression)
        assert _mask_romaji("Watashi wa gakusei desu.", ["wa", "ha"]) == "Watashi ＿＿ gakusei desu."

    def test_kanji_answer_without_candidates_returns_full(self):
        # Kanji-Antwort -> keine Romaji-Kandidaten -> volles Romaji statt leer
        assert _mask_romaji("Ima shichiji desu.", []) == "Ima shichiji desu."

    def test_suffix_ending_not_word_bounded_returns_full(self):
        # 'masu' steckt in 'nomimasu' (keine linke Wortgrenze) -> voll statt leer
        assert _mask_romaji("Maiasa o nomimasu.", ["masu"]) == "Maiasa o nomimasu."

    def test_empty_sentence_romaji_stays_empty(self):
        # Ohne jedes Satz-Romaji bleibt es leer (nichts anzuzeigen)
        assert _mask_romaji("", ["masu"]) == ""


class TestClozeKeepsRomaji:
    def test_kanji_marker_cloze_keeps_romaji(self):
        examples = [{
            "japanese": "今 七時です。",
            "romaji": "Ima shichiji desu.",
            "translation": "Es ist jetzt sieben Uhr.",
        }]
        cz = make_grammar_cloze(examples, "今 ～時 です")
        assert cz is not None
        assert cz["romaji_masked"]                       # nicht leer
        assert cz["romaji_masked"] == "Ima shichiji desu."

    def test_no_romaji_when_example_has_no_romaji(self):
        # Beispielsatz ganz ohne Romaji -> weiterhin leer (kein erfundenes Romaji)
        examples = [{"japanese": "あれも 本です。", "romaji": "", "translation": "x"}]
        cz = make_grammar_cloze(examples, "N も (mo)")
        assert cz is not None
        assert cz["romaji_masked"] == ""
