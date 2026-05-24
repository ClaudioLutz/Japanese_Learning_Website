# tests/unit/test_grammar_examples.py
"""Tests fuer die zentrale Beispielsatz-Normalisierung
``parse_example_sentences`` und ``Grammar.parsed_examples``.

Diese Funktion ist die Grundlage fuer das Rendering mehrerer Beispielsaetze
und den Cloze-Review-Modus, daher werden beide Eingabeformate (JSON +
nummerierter Plaintext) sowie Randfaelle abgedeckt.
"""

from __future__ import annotations

from app.models import Grammar, parse_example_sentences


class TestJsonFormat:
    def test_multiple_entries_preserve_order_and_fields(self):
        raw = (
            '[{"japanese": "わたしは 学生です。", "romanization": "Watashi wa gakusei desu.",'
            ' "german": "Ich bin Student."},'
            ' {"japanese": "あれは 本です。", "romaji": "Are wa hon desu.",'
            ' "english": "That is a book."}]'
        )
        result = parse_example_sentences(raw)
        assert len(result) == 2
        assert result[0] == {
            'japanese': 'わたしは 学生です。',
            'romaji': 'Watashi wa gakusei desu.',
            'translation': 'Ich bin Student.',
        }
        # zweiter Eintrag: kein Deutsch -> Fallback Englisch, romaji-Schluessel.
        assert result[1]['romaji'] == 'Are wa hon desu.'
        assert result[1]['translation'] == 'That is a book.'

    def test_german_preferred_over_english(self):
        raw = ('[{"japanese": "x", "romanization": "r",'
               ' "english": "EN", "german": "DE"}]')
        assert parse_example_sentences(raw)[0]['translation'] == 'DE'

    def test_entries_without_japanese_are_skipped(self):
        raw = '[{"romanization": "r"}, {"japanese": "ある。", "romaji": "aru"}]'
        result = parse_example_sentences(raw)
        assert len(result) == 1
        assert result[0]['japanese'] == 'ある。'


class TestPlaintextFormat:
    def test_numbered_multiline_block_yields_one_per_number(self):
        raw = (
            "① わたしは マイク・ミラーです。\n"
            "  (Watashi wa Maiku Miraa desu.)\n"
            "  — Ich bin Mike Miller.\n"
            "② わたしは エンジニアです。\n"
            "  (Watashi wa enjinia desu.)\n"
            "  — Ich bin Ingenieur.\n"
        )
        result = parse_example_sentences(raw)
        assert len(result) == 2
        assert result[0] == {
            'japanese': 'わたしは マイク・ミラーです。',
            'romaji': 'Watashi wa Maiku Miraa desu.',
            'translation': 'Ich bin Mike Miller.',
        }
        assert result[1]['japanese'] == 'わたしは エンジニアです。'
        assert result[1]['translation'] == 'Ich bin Ingenieur.'

    def test_inline_one_example_per_line(self):
        raw = (
            "リサさんは がくせいですか。 (Risa-san wa gakusei desu ka.) -> Ist Lisa Studentin?\n"
            "これは ほんですか。 (Kore wa hon desu ka.) -> Ist das ein Buch?"
        )
        result = parse_example_sentences(raw)
        assert len(result) == 2
        assert result[0]['japanese'] == 'リサさんは がくせいですか。'
        assert result[0]['translation'] == 'Ist Lisa Studentin?'
        assert result[1]['romaji'] == 'Kore wa hon desu ka.'

    def test_answer_line_becomes_own_entry(self):
        raw = (
            "④ ミラーさんは アメリカ人ですか。\n"
            "  (Miraa-san wa Amerikajin desu ka.)\n"
            "  — Ist Herr Miller Amerikaner?\n"
            "…はい、アメリカ人です。(Hai, Amerikajin desu.) — Ja, ist er.\n"
        )
        result = parse_example_sentences(raw)
        assert len(result) == 2
        assert result[1]['japanese'] == '…はい、アメリカ人です。'
        assert result[1]['romaji'] == 'Hai, Amerikajin desu.'
        assert result[1]['translation'] == 'Ja, ist er.'

    def test_fullwidth_parentheses(self):
        raw = "テストです。（Tesuto desu.）— Es ist ein Test."
        result = parse_example_sentences(raw)
        assert len(result) == 1
        assert result[0]['romaji'] == 'Tesuto desu.'
        assert result[0]['translation'] == 'Es ist ein Test.'

    def test_unbalanced_paren_captures_romaji_without_translation(self):
        raw = "あの方は どなたですか。 (Ano kata wa donata desu ka."
        result = parse_example_sentences(raw)
        assert len(result) == 1
        assert result[0]['japanese'] == 'あの方は どなたですか。'
        assert result[0]['romaji'] == 'Ano kata wa donata desu ka.'
        assert result[0]['translation'] == ''

    def test_sentence_without_paren_is_japanese_only(self):
        result = parse_example_sentences("ぜんぜん anderer Text.")
        assert result == [{'japanese': 'ぜんぜん anderer Text.', 'romaji': '',
                           'translation': ''}]


class TestEdgeCases:
    def test_none_returns_empty_list(self):
        assert parse_example_sentences(None) == []

    def test_blank_returns_empty_list(self):
        assert parse_example_sentences("   \n  ") == []

    def test_broken_json_falls_through_to_plaintext(self):
        # Beginnt mit "[" ist aber kein gueltiges JSON -> Plaintext-Parser.
        result = parse_example_sentences("[kaputt (Romaji) — Uebersetzung")
        assert len(result) == 1
        assert result[0]['romaji'] == 'Romaji'


class TestGrammarMethod:
    def test_parsed_examples_delegates(self):
        g = Grammar(
            title="x", explanation="x",
            example_sentences=(
                "① テスト。\n  (Tesuto.)\n  — Test.\n"
            ),
        )
        examples = g.parsed_examples()
        assert examples == [{'japanese': 'テスト。', 'romaji': 'Tesuto.',
                             'translation': 'Test.'}]

    def test_parsed_examples_empty_when_no_data(self):
        g = Grammar(title="x", explanation="x", example_sentences=None)
        assert g.parsed_examples() == []
