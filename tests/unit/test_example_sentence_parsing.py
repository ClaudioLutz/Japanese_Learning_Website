# tests/unit/test_example_sentence_parsing.py
"""Sicherstellen, dass Romaji + Uebersetzung sauber aus den existierenden
Feldern extrahiert werden, damit die Karten-Rueckseite eine
Romaji- und Deutsch-Zeile unter dem JP-Beispielsatz zeigen kann.
"""

from __future__ import annotations

from app.models import Grammar, Vocabulary


class TestVocabularyExampleParsing:
    def test_em_dash_separator(self):
        v = Vocabulary(
            word="先生", reading="せんせい", meaning="teacher",
            example_sentence_english="Sensei wa yasashii desu. — Der Lehrer ist nett.",
        )
        assert v.example_sentence_romaji == "Sensei wa yasashii desu."
        assert v.example_sentence_translation == "Der Lehrer ist nett."

    def test_ascii_hyphen_separator(self):
        v = Vocabulary(
            word="x", reading="x", meaning="x",
            example_sentence_english="Watashi wa Rii desu. - Ich heisse Lee.",
        )
        assert v.example_sentence_romaji == "Watashi wa Rii desu."
        assert v.example_sentence_translation == "Ich heisse Lee."

    def test_no_separator_returns_translation_only(self):
        # Floskeln wie "Freut mich, Sie kennenzulernen." haben keinen Romaji-Praefix.
        v = Vocabulary(
            word="x", reading="x", meaning="x",
            example_sentence_english="Freut mich, Sie kennenzulernen.",
        )
        assert v.example_sentence_romaji is None
        assert v.example_sentence_translation == "Freut mich, Sie kennenzulernen."

    def test_empty_returns_none(self):
        v = Vocabulary(
            word="x", reading="x", meaning="x",
            example_sentence_english=None,
        )
        assert v.example_sentence_romaji is None
        assert v.example_sentence_translation is None


class TestGrammarExampleParsing:
    def test_json_examples_with_romanization(self):
        g = Grammar(
            title="x",
            explanation="x",
            tts_example_jp="明治神宮はどこですか？",
            example_sentences=(
                '[{"japanese": "明治神宮はどこですか？",'
                ' "english": "Where is Meiji Shrine?",'
                ' "romanization": "Meiji Jingū wa doko desu ka?"}]'
            ),
        )
        assert g.tts_example_romaji == "Meiji Jingū wa doko desu ka?"
        # Keine 'german'-Spalte in JSON → Fallback auf englisch (besser als nichts).
        assert g.tts_example_translation == "Where is Meiji Shrine?"

    def test_json_with_german_field(self):
        g = Grammar(
            title="x", explanation="x",
            tts_example_jp="きょうは月曜日です。",
            example_sentences=(
                '[{"japanese": "きょうは月曜日です。",'
                ' "german": "Heute ist Montag.",'
                ' "romanization": "Kyō wa getsu-yōbi desu."}]'
            ),
        )
        assert g.tts_example_romaji == "Kyō wa getsu-yōbi desu."
        assert g.tts_example_translation == "Heute ist Montag."

    def test_inline_paren_format(self):
        g = Grammar(
            title="x", explanation="x",
            tts_example_jp="リサさんは がくせいですか。",
            example_sentences=(
                "リサさんは がくせいですか。 (Risa-san wa gakusei desu ka.) -> Ist Lisa Studentin?\n"
                "これは ほんですか。 (Kore wa hon desu ka.) -> Ist das ein Buch?"
            ),
        )
        assert g.tts_example_romaji == "Risa-san wa gakusei desu ka."
        assert g.tts_example_translation == "Ist Lisa Studentin?"

    def test_multiline_paren_dash_format(self):
        g = Grammar(
            title="x", explanation="x",
            tts_example_jp="毎日 勉強します。",
            example_sentences=(
                "③ 毎日 勉強します。\n"
                "  (Mainichi benkyō shimasu.)\n"
                "  — Ich lerne jeden Tag.\n"
            ),
        )
        assert g.tts_example_romaji == "Mainichi benkyō shimasu."
        assert g.tts_example_translation == "Ich lerne jeden Tag."

    def test_no_match_returns_none(self):
        g = Grammar(
            title="x", explanation="x",
            tts_example_jp="きょうは雨です。",
            example_sentences="ぜんぜん anderer Text.",
        )
        assert g.tts_example_romaji is None
        assert g.tts_example_translation is None

    def test_empty_examples_returns_none(self):
        g = Grammar(
            title="x", explanation="x",
            tts_example_jp="きょうは月曜日です。",
            example_sentences=None,
        )
        assert g.tts_example_romaji is None
        assert g.tts_example_translation is None
