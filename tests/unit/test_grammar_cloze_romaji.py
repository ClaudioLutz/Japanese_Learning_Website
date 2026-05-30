"""Regression: Cloze-Grammatikkarten muessen IMMER eine Romaji-Lesehilfe auf der
Vorderseite zeigen — auch wenn die maskierte Antwort eine Verb-/Kopula-Endung
(ます/です/…) ist, die im Romaji als Wortsuffix steht (nomi|masu, gakusei|desu).

Frueher lieferte ``_mask_romaji`` in diesem Fall '' (strikte Wortgrenze scheitert
am Suffix), wodurch die ganze Romaji-Zeile der Cloze-Karte verschwand — das war
die Ursache fuer die 39 Grammatikkarten ohne Romaji auf der Vorderseite.
"""
from app.models import _mask_romaji, make_grammar_cloze


class TestMaskRomaji:
    def test_particle_standalone_masked(self):
        # Partikel als eigenstaendiges Wort -> strikte Wortgrenze (unveraendert)
        assert _mask_romaji("Kore wa pen desu.", ["wa", "ha"]) == "Kore ＿＿ pen desu."

    def test_verb_ending_suffix_masked(self):
        # ます haengt am Stamm -> Suffix-Masking statt leerem Ergebnis
        assert _mask_romaji("nomimasu", ["masu"]) == "nomi＿＿"

    def test_copula_ending_suffix_masked(self):
        assert _mask_romaji("gakuseidesu", ["desu"]) == "gakusei＿＿"

    def test_standalone_desu_uses_strict_pass(self):
        assert _mask_romaji("gakusei desu", ["desu"]) == "gakusei ＿＿"

    def test_fallback_returns_full_not_empty(self):
        # Antwort-Lesung nicht auffindbar -> lieber volles Romaji als gar keins
        assert _mask_romaji("Tanaka san", ["xyz"]) == "Tanaka san"

    def test_empty_input_stays_empty(self):
        assert _mask_romaji("", ["masu"]) == ""


class TestClozeAlwaysHasRomaji:
    def test_masu_cloze_keeps_romaji(self):
        examples = [{
            "japanese": "毎朝コーヒーを飲みます。",
            "romaji": "Maiasa ko-hi- o nomimasu.",
            "translation": "Jeden Morgen trinke ich Kaffee.",
        }]
        c = make_grammar_cloze(examples, "Vます")
        assert c is not None
        assert c["answer"] == "ます"
        assert c["romaji_masked"]                          # nicht leer
        assert "＿＿" in c["romaji_masked"]
        assert "masu" not in c["romaji_masked"].lower()    # Antwort nicht gespoilert
