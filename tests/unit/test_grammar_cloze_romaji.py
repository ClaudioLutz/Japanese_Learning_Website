"""Regression: Cloze-Grammatikkarten zeigen auf der Vorderseite den Satz als
Romaji-Lesehilfe — der ganze Satz 1:1, NUR die Lücke (die Antwort) wird durch
``＿＿`` ersetzt und NIE gespoilert.

Zwei Bugs, die hier abgesichert sind:
1. Frueher fiel die ganze Romaji-Zeile weg (``''``), wenn die Antwort im Romaji
   nicht als ganzes Wort gefunden wurde (Kanji-Antwort, Suffix-Endung).
2. Der erste Fix gab dann das VOLLE Romaji zurueck → die Loesung stand
   unmaskiert da (z.B. ``Watashi wa Risa desu.`` mit sichtbarem ``wa``).
Korrektes Verhalten: Lücke immer ausblenden, Rest als Romaji erhalten.
"""
from app.models import (
    _answer_romaji_candidates,
    _mask_romaji,
    _romaji_with_gap,
    make_grammar_cloze,
)


class TestMaskRomaji:
    def test_particle_masked_at_word_boundary(self):
        assert _mask_romaji("Watashi wa gakusei desu.", ["wa", "ha"]) == "Watashi ＿＿ gakusei desu."

    def test_space_insensitive_match(self):
        # Antwort 'ですか' = "desuka", Satz-Romaji schreibt "desu ka" → trotzdem Treffer
        assert _mask_romaji("Risa-san wa gakusei desu ka.", ["desuka"]) == "Risa-san wa gakusei ＿＿."

    def test_macron_insensitive_match(self):
        # Makron im Satz (dō) vs. 'dou' in der Kana-Umschrift
        assert _mask_romaji("Kyō no tenki wa dō desu ka.", ["doudesuka"]) == "Kyō no tenki wa ＿＿."

    def test_no_candidate_returns_empty_not_spoiler(self):
        # Kanji-Antwort ohne Umschrift → KEINE volle Zeile (kein Spoiler), sondern ''
        assert _mask_romaji("Ima shichiji desu.", []) == ""

    def test_unfound_candidate_returns_empty_not_spoiler(self):
        assert _mask_romaji("Tanaka san desu.", ["xyz"]) == ""

    def test_empty_sentence_romaji_stays_empty(self):
        assert _mask_romaji("", ["wa"]) == ""


class TestAnswerCandidates:
    def test_topic_particle_variants(self):
        # わたしは → 'watashiwa' (phonetische Partikel) muss dabei sein, damit
        # "Watashi wa" im Satz-Romaji gefunden wird (nicht nur 'watashiha').
        cands = _answer_romaji_candidates("わたしは")
        assert "watashiwa" in cands

    def test_standalone_wa(self):
        assert _answer_romaji_candidates("は") == ["wa", "ha"]

    def test_kanji_yields_no_candidates(self):
        assert _answer_romaji_candidates("今") == []


class TestRomajiWithGap:
    def test_builds_line_from_parts(self):
        # Kanji-Lücke mitten im Satz: Rest als Romaji, Lücke ausgeblendet.
        out = _romaji_with_gap("あの ", "は だれですか。")
        assert "＿＿" in out
        assert "dare" in out.lower()

    def test_empty_when_no_japanese(self):
        assert _romaji_with_gap("", "") == ""


class TestClozeNeverSpoilers:
    def test_topic_particle_gap_not_spoiler(self):
        # Der gemeldete Fall: "Watashi wa Risa desu." darf 'wa' NICHT zeigen.
        examples = [{"japanese": "わたしは リサです。",
                     "romaji": "Watashi wa Risa desu.", "translation": "Ich bin Lisa."}]
        c = make_grammar_cloze(examples, "[A] は (wa) [B] です")
        assert c["answer"] == "は"
        assert c["romaji_masked"] == "Watashi ＿＿ Risa desu."

    def test_kanji_marker_uses_fallback_and_masks(self):
        # Kanji-Lücke (今): Rest als Romaji, heutige Lesung 'Ima' NICHT sichtbar.
        examples = [{"japanese": "今 七時です。",
                     "romaji": "Ima shichiji desu.", "translation": "Es ist jetzt sieben Uhr."}]
        c = make_grammar_cloze(examples, "今 (ima)")
        assert c["answer"] == "今"
        assert "＿＿" in c["romaji_masked"]
        assert "shichiji desu" in c["romaji_masked"].lower()
        assert "ima" not in c["romaji_masked"].lower()   # Lösung nicht gespoilert

    def test_fallback_generates_romaji_without_curated(self):
        # Auch ohne kuratiertes Romaji: aus dem Japanischen erzeugen, Lücke maskiert.
        examples = [{"japanese": "あれも 本です。", "romaji": "", "translation": "x"}]
        c = make_grammar_cloze(examples, "N も (mo)")
        assert c is not None
        assert "＿＿" in c["romaji_masked"]
        assert "mo" not in c["romaji_masked"].lower()
