# tests/unit/test_ai_services.py
"""
Phase 2: Unit-Tests für AI Services (Hilfsfunktionen + Generator mit Mocks).
Testkonzept-IDs: U-AI01 bis U-AI08
"""

import pytest
from unittest.mock import patch, MagicMock
from app.ai_services import (
    convert_jlpt_level_to_int,
    truncate_field,
    convert_difficulty_to_int,
)


# ── U-AI01: convert_jlpt_level_to_int ───────────────────────

class TestConvertJlptLevel:
    def test_string_n4(self):
        """U-AI01: 'N4' → 4."""
        assert convert_jlpt_level_to_int("N4") == 4

    def test_string_lowercase(self):
        """U-AI01: 'n3' → 3."""
        assert convert_jlpt_level_to_int("n3") == 3

    def test_string_number_only(self):
        """U-AI01: '2' → 2."""
        assert convert_jlpt_level_to_int("2") == 2

    def test_integer_input(self):
        """U-AI01: Integer 1 → 1."""
        assert convert_jlpt_level_to_int(1) == 1

    def test_invalid_string(self):
        """U-AI01: Ungültiger String → 5 (Default)."""
        assert convert_jlpt_level_to_int("invalid") == 5

    def test_none_input(self):
        """U-AI01: None → 5 (Default)."""
        assert convert_jlpt_level_to_int(None) == 5


# ── U-AI02: truncate_field ──────────────────────────────────

class TestTruncateField:
    def test_short_text_unchanged(self):
        """U-AI02: Kurzer Text bleibt unverändert."""
        assert truncate_field("Hallo", 100) == "Hallo"

    def test_long_text_truncated(self):
        """U-AI02: Langer Text wird gekürzt mit '...'."""
        text = "A" * 200
        result = truncate_field(text, 100)
        assert len(result) == 100
        assert result.endswith("...")

    def test_none_input(self):
        """U-AI02: None bleibt None."""
        assert truncate_field(None, 100) is None

    def test_empty_string(self):
        """U-AI02: Leerer String bleibt leer."""
        assert truncate_field("", 100) == ""

    def test_exact_length(self):
        """U-AI02: Exakte Länge bleibt unverändert."""
        text = "A" * 100
        assert truncate_field(text, 100) == text


# ── U-AI03: convert_difficulty_to_int ────────────────────────

class TestConvertDifficulty:
    def test_easy(self):
        """U-AI03: 'easy' → 1."""
        assert convert_difficulty_to_int("easy") == 1

    def test_medium(self):
        """U-AI03: 'medium' → 3."""
        assert convert_difficulty_to_int("medium") == 3

    def test_hard(self):
        """U-AI03: 'hard' → 4."""
        assert convert_difficulty_to_int("hard") == 4

    def test_expert(self):
        """U-AI03: 'expert' → 5."""
        assert convert_difficulty_to_int("expert") == 5

    def test_integer_clamped(self):
        """U-AI03: Integer wird auf 1-5 begrenzt."""
        assert convert_difficulty_to_int(10) == 5
        assert convert_difficulty_to_int(-1) == 1

    def test_integer_passthrough(self):
        """U-AI03: Integer 3 → 3."""
        assert convert_difficulty_to_int(3) == 3

    def test_unknown_string(self):
        """U-AI03: Unbekannter String → 3 (Default)."""
        assert convert_difficulty_to_int("unknown") == 3

    def test_none_default(self):
        """U-AI03: None → 3 (Default)."""
        assert convert_difficulty_to_int(None) == 3


# ── U-AI04-08: AILessonContentGenerator mit Mocks ───────────

class TestAILessonContentGenerator:
    @patch("app.ai_services.genai")
    @patch("app.ai_services.OpenAI")
    def test_generator_initialization_without_keys(self, mock_openai, mock_genai, app):
        """U-AI04: Generator initialisiert ohne API-Keys (graceful degradation)."""
        with app.app_context():
            with patch.dict("os.environ", {
                "OPENAI_API_KEY": "",
                "GEMINI_API_KEY": "",
                "GOOGLE_AI_API_KEY": "",
            }):
                from app.ai_services import AILessonContentGenerator
                gen = AILessonContentGenerator()
                assert gen.openai_client is None

    @patch("app.ai_services.genai")
    @patch("app.ai_services.OpenAI")
    def test_generate_content_without_gemini(self, mock_openai, mock_genai, app):
        """U-AI05: _generate_content ohne Gemini-Client gibt Fehler."""
        with app.app_context():
            with patch.dict("os.environ", {
                "OPENAI_API_KEY": "",
                "GEMINI_API_KEY": "",
                "GOOGLE_AI_API_KEY": "",
            }):
                from app.ai_services import AILessonContentGenerator
                gen = AILessonContentGenerator()
                gen.gemini_client = None
                content, error = gen._generate_content("system", "user")
                assert content is None
                assert "not initialized" in error

    @patch("app.ai_services.genai")
    @patch("app.ai_services.OpenAI")
    def test_generate_explanation_success(self, mock_openai, mock_genai, app):
        """U-AI06: generate_explanation mit Mock-Gemini."""
        with app.app_context():
            with patch.dict("os.environ", {
                "OPENAI_API_KEY": "fake",
                "GEMINI_API_KEY": "fake",
            }):
                from app.ai_services import AILessonContentGenerator
                gen = AILessonContentGenerator()
                # Mock die _generate_content Methode
                gen._generate_content = MagicMock(
                    return_value=("Dies ist eine Erklärung.", None)
                )
                result = gen.generate_explanation("Hiragana", "easy", "あ, い, う")
                assert "generated_text" in result
                assert "Erklärung" in result["generated_text"]

    @patch("app.ai_services.genai")
    @patch("app.ai_services.OpenAI")
    def test_generate_explanation_error(self, mock_openai, mock_genai, app):
        """U-AI07: generate_explanation bei API-Fehler."""
        with app.app_context():
            with patch.dict("os.environ", {
                "OPENAI_API_KEY": "fake",
                "GEMINI_API_KEY": "fake",
            }):
                from app.ai_services import AILessonContentGenerator
                gen = AILessonContentGenerator()
                gen._generate_content = MagicMock(
                    return_value=(None, "API error")
                )
                result = gen.generate_explanation("Hiragana", "easy", "あ")
                assert "error" in result
