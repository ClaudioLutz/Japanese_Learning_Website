"""Tests fuer app.services.kana_rows."""
from app.services.kana_rows import (
    HIRAGANA_ROWS,
    KATAKANA_ROWS,
    ROMAJI_ROWS,
    ROW_KEYS,
    _KANA_ROWS,
    kana_rows_for_lesson,
    row_for_kana,
    row_for_romanization,
)


class TestRowForRomanization:
    def test_vokale(self):
        for r in ['a', 'i', 'u', 'e', 'o']:
            assert row_for_romanization(r) == 'vowels'

    def test_k_reihe(self):
        for r in ['ka', 'ki', 'ku', 'ke', 'ko']:
            assert row_for_romanization(r) == 'k'

    def test_s_reihe_inkl_shi(self):
        assert row_for_romanization('sa') == 's'
        assert row_for_romanization('shi') == 's'

    def test_t_reihe_inkl_chi_tsu(self):
        assert row_for_romanization('chi') == 't'
        assert row_for_romanization('tsu') == 't'

    def test_n_konsonant(self):
        assert row_for_romanization('n') == 'n_kons'

    def test_dakuten_g(self):
        assert row_for_romanization('ga') == 'g'
        assert row_for_romanization('go') == 'g'

    def test_handakuten_p(self):
        assert row_for_romanization('pa') == 'p'

    def test_case_insensitive(self):
        assert row_for_romanization('KA') == 'k'
        assert row_for_romanization(' Shi ') == 's'

    def test_unbekannte_mora(self):
        assert row_for_romanization('xyz') is None
        assert row_for_romanization('') is None
        assert row_for_romanization(None) is None

    def test_yoon_nicht_unterstuetzt(self):
        # Yoon-Kombinationen sind nicht in ROMAJI_ROWS
        assert row_for_romanization('kya') is None
        assert row_for_romanization('sha') is None


class TestRowForKana:
    def test_hiragana_vokale(self):
        assert row_for_kana('あ') == 'vowels'
        assert row_for_kana('お') == 'vowels'

    def test_hiragana_k(self):
        assert row_for_kana('か') == 'k'

    def test_katakana_s(self):
        assert row_for_kana('シ') == 's'

    def test_katakana_p(self):
        assert row_for_kana('パ') == 'p'

    def test_yoon_zwei_zeichen_none(self):
        # Yoon ist 2 Zeichen — wir matchen nur Single-Mora
        assert row_for_kana('きゃ') is None

    def test_unbekanntes_zeichen(self):
        assert row_for_kana('A') is None
        assert row_for_kana('') is None
        assert row_for_kana(None) is None


class TestKanaRowsForLesson:
    class _FakeKana:
        def __init__(self, character, romanization):
            self.character = character
            self.romanization = romanization

    def test_vokale_und_k_reihe(self):
        items = [
            self._FakeKana('あ', 'a'),
            self._FakeKana('い', 'i'),
            self._FakeKana('か', 'ka'),
            self._FakeKana('き', 'ki'),
        ]
        grouped = kana_rows_for_lesson(items)
        keys = [g['key'] for g in grouped]
        assert keys == ['vowels', 'k']
        assert len(grouped[0]['kana']) == 2
        assert len(grouped[1]['kana']) == 2

    def test_reihenfolge_aus_ROW_KEYS(self):
        # K-Reihe vor Vokalen reingegeben — Output muss aber ROW_KEYS-Order folgen
        items = [
            self._FakeKana('か', 'ka'),
            self._FakeKana('あ', 'a'),
        ]
        grouped = kana_rows_for_lesson(items)
        keys = [g['key'] for g in grouped]
        assert keys == ['vowels', 'k']  # vowels kommt vor k in ROW_KEYS

    def test_leere_liste(self):
        assert kana_rows_for_lesson([]) == []

    def test_fallback_other(self):
        items = [self._FakeKana('X', 'xyz')]
        grouped = kana_rows_for_lesson(items)
        assert len(grouped) == 1
        assert grouped[0]['key'] == 'other'
        assert grouped[0]['label'] == 'Sonstige'


class TestDatenstruktur:
    def test_kana_rows_count(self):
        # 30 Reihen: 15 Hiragana + 15 Katakana
        assert len(_KANA_ROWS) == 30

    def test_alle_ROW_KEYS_in_ROMAJI_ROWS(self):
        for key in ROW_KEYS:
            assert key in ROMAJI_ROWS, f'{key} fehlt in ROMAJI_ROWS'

    def test_alle_ROW_KEYS_in_HIRAGANA_ROWS(self):
        for key in ROW_KEYS:
            assert key in HIRAGANA_ROWS, f'{key} fehlt in HIRAGANA_ROWS'

    def test_alle_ROW_KEYS_in_KATAKANA_ROWS(self):
        for key in ROW_KEYS:
            assert key in KATAKANA_ROWS, f'{key} fehlt in KATAKANA_ROWS'

    def test_konsistenz_lengths(self):
        # Pro Reihe muessen Romaji + Hiragana + Katakana gleich lang sein
        for key in ROW_KEYS:
            r = len(ROMAJI_ROWS[key])
            h = len(HIRAGANA_ROWS[key])
            k = len(KATAKANA_ROWS[key])
            assert r == h == k, f'Length mismatch in row {key}: rom={r}, hira={h}, kata={k}'
