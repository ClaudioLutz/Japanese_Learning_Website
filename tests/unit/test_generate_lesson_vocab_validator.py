# tests/unit/test_generate_lesson_vocab_validator.py
"""Unit-Tests fuer generate-lesson/pipeline.py Vocabulary-TTS-Validierung.

Sichert ab, dass der Validator Vokabel-Saetze ablehnt, die der Audio-Button
auf der Karte nicht sauber an /api/tts mit lang=ja schicken kann:
  * keine japanischen Zeichen
  * lateinische Buchstaben (Romaji/Uebersetzung)
  * fehlendes Satzende
  * fehlendes Pflicht-Feld

Identische Regel wie bei `Grammar.tts_example_jp` (Commit e644bda).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

# Pipeline ist im skill-Ordner, nicht auf sys.path. Direkt laden.
SKILL_PIPELINE = Path(__file__).resolve().parents[2] / ".claude" / "skills" / "generate-lesson" / "pipeline.py"
spec = importlib.util.spec_from_file_location("_genlesson_pipeline", SKILL_PIPELINE)
pipeline = importlib.util.module_from_spec(spec)
sys.modules["_genlesson_pipeline"] = pipeline
spec.loader.exec_module(pipeline)


def _vocab_item(**overrides) -> dict:
    """Minimaler Vocab-Eintrag mit allen Pflichtfeldern. Override gezielt fuer Test."""
    data = {
        "word": "わたし",
        "reading": "わたし",
        "romaji": "watashi",
        "meaning": "I",
        "meaning_de": "ich",
        "jlpt_level": 5,
        "example_sentence_japanese": "わたしは がくせいです。",
    }
    data.update(overrides)
    return {"content_type": "vocabulary", "data": data}


def _draft(vocab_item: dict) -> dict:
    """Minimaler Lesson-Draft mit einer Vokabel-Page.

    Hinweis: validate_draft iteriert ueber `contents` (plural). Lesson-Level-Errors
    (zu wenige Pages, kein Quiz-Carousel) sind fuer diesen Test irrelevant —
    er filtert gezielt nach den Vocab-spezifischen Errors.
    """
    return {
        "title": "Test",
        "description": "Test-Lektion fuer Validator",
        "jlpt_level": 5,
        "topic": "test",
        "pages": [{
            "page_number": 1,
            "title": "Vokabeln",
            "page_type": "normal",
            "contents": [vocab_item],
        }],
    }


def _vocab_errors(item: dict) -> list[str]:
    """Validate ein Draft mit genau einer Vokabel und gib alle Fehler-Messages zurueck."""
    return pipeline.validate_draft(_draft(item))


class TestRequiredField:
    def test_missing_example_sentence_is_error(self):
        item = _vocab_item()
        del item["data"]["example_sentence_japanese"]
        errors = _vocab_errors(item)
        assert any("example_sentence_japanese" in e and "fehlt" in e for e in errors)

    def test_present_example_sentence_no_error(self):
        # Sauberer Satz, わたし ist in N5 canonical -> sollte ohne TTS-Fehler durchgehen.
        errors = _vocab_errors(_vocab_item())
        tts_errors = [e for e in errors if "example_sentence_japanese" in e]
        assert tts_errors == [], f"unerwartete Errors: {tts_errors}"


class TestTTSValidation:
    def test_rejects_latin_in_sentence(self):
        item = _vocab_item(example_sentence_japanese="わたしは gakusei です。")
        errors = _vocab_errors(item)
        assert any("lateinische Buchstaben" in e for e in errors)

    def test_rejects_trailing_paren_romaji(self):
        # Klassischer Anti-Pattern: Klammer-Romaji am Satzende.
        item = _vocab_item(
            example_sentence_japanese="わたしは がくせいです。 (watashi wa gakusei desu.)"
        )
        errors = _vocab_errors(item)
        assert any("lateinische Buchstaben" in e for e in errors)

    def test_rejects_missing_terminator(self):
        item = _vocab_item(example_sentence_japanese="わたしは がくせい")
        errors = _vocab_errors(item)
        assert any("。" in e and "enden" in e for e in errors)

    def test_rejects_no_japanese_chars(self):
        # Nur lateinisch -> doppelter Trigger: keine JP-Zeichen + Romaji.
        item = _vocab_item(example_sentence_japanese="Watashi wa gakusei desu.")
        errors = _vocab_errors(item)
        assert any("keine japanischen Zeichen" in e for e in errors)

    @pytest.mark.parametrize("terminator", ["。", "！", "？"])
    def test_accepts_all_three_jp_terminators(self, terminator):
        sent = f"これは ほんです{terminator}"
        item = _vocab_item(example_sentence_japanese=sent)
        errors = _vocab_errors(item)
        tts_errors = [e for e in errors if "example_sentence_japanese" in e]
        assert tts_errors == [], f"Terminator '{terminator}' sollte ok sein: {tts_errors}"
