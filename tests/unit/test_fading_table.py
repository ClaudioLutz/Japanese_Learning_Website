"""Tests fuer das Fading-Scaffolding-Mapping (Phase 4)."""
from scripts.update_kana_grid_hints import FADING_TABLE, lesson_number


def test_fading_lesson_number_extraction():
    assert lesson_number('N5 Hiragana 1 — Vokale, K-Reihe und S-Reihe') == 1
    assert lesson_number('N5 Katakana 5 — Yoon und Lehnwoerter') == 5
    assert lesson_number('Vocab Lektion 3') == 0
    assert lesson_number('') == 0


def test_fading_table_monotone_decrease():
    """max_hints muss von Lesson 1 bis 5 monoton fallen (Fading-Scaffolding)."""
    prev = None
    for lesson_n in sorted(FADING_TABLE.keys()):
        max_hints, romaji = FADING_TABLE[lesson_n]
        if prev is not None:
            assert max_hints <= prev, f'Lesson {lesson_n} hat mehr Hints als Vorgaenger ({max_hints} vs {prev})'
        prev = max_hints


def test_fading_table_romaji_only_lesson_1():
    """Romaji-Hint im Pool nur in Lesson 1 (Bjork: Stuetzung beim Einstieg)."""
    for lesson_n, (_max_hints, romaji) in FADING_TABLE.items():
        if lesson_n == 1:
            assert romaji is True, 'Lesson 1 muss Romaji-Hint zeigen'
        else:
            assert romaji is False, f'Lesson {lesson_n} darf keinen Romaji-Hint mehr zeigen'


def test_fading_table_zero_hints_from_lesson_4():
    """Lesson 4 + 5 ohne Hints — volles autonomes Recall (Desirable Difficulty)."""
    assert FADING_TABLE[4][0] == 0
    assert FADING_TABLE[5][0] == 0
