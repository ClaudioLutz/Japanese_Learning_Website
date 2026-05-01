# tests/unit/test_vocab_example_backfill.py
"""Unit-Tests fuer scripts/backfill_vocab_examples.py.

Sichert die zwei Kern-Funktionen ab:
  * strip_trailing_romaji  — entfernt "(romaji ...)" Klammer-Block am Satzende
  * is_pure_japanese_sentence — TTS-Tauglichkeit (rein JP, mit Satzende)
"""

from scripts.backfill_vocab_examples import (
    is_pure_japanese_sentence,
    strip_trailing_romaji,
)


class TestStripTrailingRomaji:
    def test_strips_basic_paren(self):
        assert (
            strip_trailing_romaji("駅はどこですか？ (eki wa doko desu ka?)")
            == "駅はどこですか？"
        )

    def test_strips_with_extra_whitespace(self):
        assert (
            strip_trailing_romaji("右に曲がってください。   (migi ni magatte kudasai.)   ")
            == "右に曲がってください。"
        )

    def test_strips_fullwidth_parens(self):
        assert (
            strip_trailing_romaji("こんにちは。（konnichiwa.）")
            == "こんにちは。"
        )

    def test_idempotent(self):
        cleaned = strip_trailing_romaji("駅はどこですか？ (eki wa doko desu ka?)")
        assert strip_trailing_romaji(cleaned) == cleaned

    def test_keeps_japanese_only_text_unchanged(self):
        assert strip_trailing_romaji("わたしは学生です。") == "わたしは学生です。"

    def test_does_not_strip_japanese_paren_content(self):
        # Klammer mit JP-Inhalt darf NICHT entfernt werden — nur Romaji.
        text = "わたしは学生です。（です調）"
        assert strip_trailing_romaji(text) == text

    def test_handles_empty_input(self):
        assert strip_trailing_romaji("") == ""
        assert strip_trailing_romaji(None) is None  # type: ignore[arg-type]


class TestIsPureJapaneseSentence:
    def test_simple_jp_sentence(self):
        assert is_pure_japanese_sentence("わたしは学生です。")

    def test_question_mark_jp_terminator(self):
        assert is_pure_japanese_sentence("これはなんですか？")

    def test_exclamation(self):
        assert is_pure_japanese_sentence("すごい！")

    def test_rejects_romaji_in_text(self):
        assert not is_pure_japanese_sentence("Watashi wa gakusei desu。")

    def test_rejects_no_terminator(self):
        assert not is_pure_japanese_sentence("わたしは学生")

    def test_rejects_german(self):
        assert not is_pure_japanese_sentence("Ich bin Student.")

    def test_rejects_empty(self):
        assert not is_pure_japanese_sentence("")

    def test_rejects_text_with_trailing_romaji_paren(self):
        # Wenn jemand vergisst zu strippen, muss is_pure_japanese_sentence
        # den Mischtext ablehnen — schuetzt /api/tts vor lang=ja Mismatches.
        assert not is_pure_japanese_sentence("駅はどこですか？ (eki wa doko desu ka?)")
