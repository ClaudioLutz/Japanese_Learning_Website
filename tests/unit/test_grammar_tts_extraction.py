# tests/unit/test_grammar_tts_extraction.py
"""Unit-Tests fuer den Backfill-Extraktor in scripts/backfill_grammar_tts.py.

Stellt sicher, dass aus den existierenden `example_sentences` zuverlaessig
genau ein vollstaendiger japanischer Satz extrahiert wird — keine Romaji,
keine Uebersetzung, kein deutscher Text.
"""

from scripts.backfill_grammar_tts import (
    is_pure_japanese_sentence,
    extract_from_json,
    extract_from_plain,
)


class TestIsPureJapaneseSentence:
    def test_simple_jp_sentence(self):
        assert is_pure_japanese_sentence("わたしは学生です。")

    def test_with_question_mark(self):
        assert is_pure_japanese_sentence("これは何ですか？")

    def test_no_japanese_chars(self):
        assert not is_pure_japanese_sentence("This is English.")

    def test_no_terminator(self):
        assert not is_pure_japanese_sentence("わたしは学生")

    def test_too_short(self):
        assert not is_pure_japanese_sentence("。")

    def test_empty(self):
        assert not is_pure_japanese_sentence("")


class TestExtractFromJson:
    def test_picks_first_japanese_field(self):
        raw = '[{"japanese": "今日は寒いです。", "english": "It is cold today."}]'
        assert extract_from_json(raw) == "今日は寒いです。"

    def test_skips_invalid_first_picks_valid(self):
        raw = '[{"japanese": ""}, {"japanese": "明日は月曜日です。"}]'
        assert extract_from_json(raw) == "明日は月曜日です。"

    def test_invalid_json_returns_none(self):
        assert extract_from_json("not json") is None

    def test_empty_list_returns_none(self):
        assert extract_from_json("[]") is None

    def test_truncates_at_first_terminator(self):
        raw = '[{"japanese": "猫です。犬もいます。"}]'
        assert extract_from_json(raw) == "猫です。"


class TestExtractFromPlain:
    def test_numbered_minna_format(self):
        raw = "① わたしは マイク・ミラーです。\n  (Watashi wa Maiku Miraa desu.)\n  — Ich bin Mike Miller."
        assert extract_from_plain(raw) == "わたしは マイク・ミラーです。"

    def test_skips_romaji_in_parentheses(self):
        raw = "(Watashi wa gakusei desu.)\n学生です。"
        assert extract_from_plain(raw) == "学生です。"

    def test_skips_pure_german(self):
        raw = "Ich bin Student.\n学生です。"
        assert extract_from_plain(raw) == "学生です。"

    def test_dash_bullet_marker_stripped(self):
        raw = "- 今日は雨です。"
        assert extract_from_plain(raw) == "今日は雨です。"

    def test_no_japanese_returns_none(self):
        assert extract_from_plain("Just English text. No Japanese.") is None

    def test_empty_returns_none(self):
        assert extract_from_plain("") is None
