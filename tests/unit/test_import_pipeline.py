# tests/unit/test_import_pipeline.py
"""
Tests fuer Import-Pipeline: Schema-Validierung, Import-Idempotenz, Quiz-Duplikate.
"""

import json
import pytest
from pathlib import Path

# Beispiel-JSON fuer Tests (minimale gueltige Lektion)
SAMPLE_LESSON = {
    "source": "Minna No Nihongo Beginner I",
    "lesson_number": 1,
    "title": "Lesson 1 – Self-Introduction",
    "title_ja": "第1課",
    "jlpt_level": 5,
    "description": "Selbstvorstellung: Grundlegende Partikel.",
    "vocabulary": [
        {"word": "わたし", "reading": "watashi", "meaning": "I", "kanji": None},
        {"word": "あなた", "reading": "anata", "meaning": "you", "kanji": None},
    ],
    "vocabulary_countries": [
        {"word": "日本", "reading": "Nihon", "meaning": "Japan"},
    ],
    "grammar": [
        {
            "title": "N は N です (Topic Particle は + です)",
            "structure": "N₁ は N₂ です",
            "jlpt_level": 5,
            "explanation": "The particle は indicates the topic of the sentence.",
            "example_sentences": "わたしは エンジニアです。\n(Watashi wa enjinia desu.)",
        },
    ],
    "conversation": {
        "title": "How do you do?",
        "title_ja": "はじめまして",
        "lines": [
            {"speaker": "Sato", "japanese": "おはようございます。", "romaji": "Ohayou gozaimasu.", "english": "Good morning."},
            {"speaker": "Miller", "japanese": "はじめまして。", "romaji": "Hajimemashite.", "english": "How do you do?"},
        ],
    },
}


# ============================================================
# Pydantic-Schema-Tests
# ============================================================

class TestPydanticSchema:
    """Tests fuer scripts/schema.py"""

    def test_valid_lesson(self):
        """Gueltige Lektion wird akzeptiert."""
        from scripts.schema import LessonData
        data = LessonData.model_validate(SAMPLE_LESSON)
        assert data.lesson_number == 1
        assert len(data.vocabulary) == 2
        assert len(data.grammar) == 1
        assert len(data.conversation.lines) == 2

    def test_empty_vocabulary_rejected(self):
        """Lektion ohne Vokabeln wird abgelehnt."""
        from scripts.schema import LessonData
        invalid = {**SAMPLE_LESSON, "vocabulary": []}
        with pytest.raises(Exception):
            LessonData.model_validate(invalid)

    def test_empty_grammar_rejected(self):
        """Lektion ohne Grammatik wird abgelehnt."""
        from scripts.schema import LessonData
        invalid = {**SAMPLE_LESSON, "grammar": []}
        with pytest.raises(Exception):
            LessonData.model_validate(invalid)

    def test_invalid_lesson_number(self):
        """Lektionsnummer > 50 wird abgelehnt."""
        from scripts.schema import LessonData
        invalid = {**SAMPLE_LESSON, "lesson_number": 51}
        with pytest.raises(Exception):
            LessonData.model_validate(invalid)

    def test_jlpt_mismatch_book1(self):
        """JLPT N4 bei Lektion 1-25 wird abgelehnt."""
        from scripts.schema import LessonData
        invalid = {**SAMPLE_LESSON, "jlpt_level": 4}
        with pytest.raises(Exception, match="JLPT N5"):
            LessonData.model_validate(invalid)

    def test_jlpt_mismatch_book2(self):
        """JLPT N5 bei Lektion 26-50 wird abgelehnt."""
        from scripts.schema import LessonData
        invalid = {**SAMPLE_LESSON, "lesson_number": 26, "jlpt_level": 5}
        with pytest.raises(Exception, match="JLPT N4"):
            LessonData.model_validate(invalid)

    def test_duplicate_vocabulary_rejected(self):
        """Doppelte Vokabeln in einer Lektion werden abgelehnt."""
        from scripts.schema import LessonData
        invalid = {**SAMPLE_LESSON, "vocabulary": [
            {"word": "わたし", "reading": "watashi", "meaning": "I"},
            {"word": "わたし", "reading": "watashi", "meaning": "I (duplicate)"},
        ]}
        with pytest.raises(Exception, match="Doppelte Vokabeln"):
            LessonData.model_validate(invalid)

    def test_conversation_needs_two_speakers(self):
        """Konversation mit nur einem Sprecher wird abgelehnt."""
        from scripts.schema import LessonData
        invalid = {**SAMPLE_LESSON, "conversation": {
            "title": "Monolog", "title_ja": "独り言",
            "lines": [
                {"speaker": "Sato", "japanese": "はい。", "romaji": "Hai.", "english": "Yes."},
                {"speaker": "Sato", "japanese": "いいえ。", "romaji": "Iie.", "english": "No."},
            ],
        }}
        with pytest.raises(Exception, match="2 Sprecher"):
            LessonData.model_validate(invalid)

    def test_verb_group_without_verb_rejected(self):
        """verb_group bei Nicht-Verb wird abgelehnt."""
        from scripts.schema import LessonData
        invalid = {**SAMPLE_LESSON, "vocabulary": [
            {"word": "わたし", "reading": "watashi", "meaning": "I", "part_of_speech": "noun", "verb_group": 1},
            {"word": "あなた", "reading": "anata", "meaning": "you"},
        ]}
        with pytest.raises(Exception, match="verb_group"):
            LessonData.model_validate(invalid)

    def test_verb_group_with_verb_accepted(self):
        """verb_group bei Verb wird akzeptiert."""
        from scripts.schema import LessonData
        valid = {**SAMPLE_LESSON, "vocabulary": [
            {"word": "たべます", "reading": "tabemasu", "meaning": "to eat", "part_of_speech": "verb", "verb_group": 2},
            {"word": "あなた", "reading": "anata", "meaning": "you"},
        ]}
        data = LessonData.model_validate(valid)
        assert data.vocabulary[0].verb_group == 2

    def test_optional_fields_default_none(self):
        """Optionale Felder sind standardmaessig None."""
        from scripts.schema import LessonData
        data = LessonData.model_validate(SAMPLE_LESSON)
        assert data.vocabulary[0].part_of_speech is None
        assert data.vocabulary[0].verb_group is None
        assert data.vocabulary[0].adjective_type is None

    def test_existing_lesson01_json(self):
        """Die existierende beginner1_lesson01.json ist gueltig."""
        from scripts.schema import LessonData
        json_path = Path(__file__).resolve().parent.parent.parent / "scripts" / "mnn_data" / "beginner1_lesson01.json"
        if not json_path.exists():
            pytest.skip("beginner1_lesson01.json nicht vorhanden")
        with open(json_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        data = LessonData.model_validate(raw)
        assert data.lesson_number == 1
        assert len(data.vocabulary) >= 20


# ============================================================
# Import-Idempotenz-Tests
# ============================================================

class TestImportIdempotency:
    """Tests fuer idempotenten Import via import_mnn.py"""

    def test_vocabulary_import_idempotent(self, app_context):
        """Zweimaliger Import erzeugt keine doppelten Vokabeln."""
        from app import db
        from app.models import Vocabulary
        from scripts.import_mnn import import_vocabulary

        count_before = Vocabulary.query.count()
        import_vocabulary(SAMPLE_LESSON, dry_run=False)
        db.session.flush()
        count_first = Vocabulary.query.count()

        # Zweiter Import — gleiche Daten
        import_vocabulary(SAMPLE_LESSON, dry_run=False)
        db.session.flush()
        count_second = Vocabulary.query.count()

        assert count_first == count_before + 3  # 2 vocab + 1 country
        assert count_second == count_first  # Keine Duplikate

    def test_grammar_import_idempotent(self, app_context):
        """Zweimaliger Import erzeugt keine doppelte Grammatik."""
        from app import db
        from app.models import Grammar
        from scripts.import_mnn import import_grammar

        import_grammar(SAMPLE_LESSON, dry_run=False)
        db.session.flush()
        count_first = Grammar.query.count()

        import_grammar(SAMPLE_LESSON, dry_run=False)
        db.session.flush()
        count_second = Grammar.query.count()

        assert count_first == 1
        assert count_second == 1

    def test_lesson_import_idempotent(self, app_context):
        """Zweimaliger Lektions-Import erzeugt keine Duplikate."""
        from app import db
        from app.models import Lesson, LessonCategory
        from scripts.import_mnn import import_vocabulary, import_grammar, create_lesson

        category = LessonCategory(name="Test MNN", description="Test", color_code="#000")
        db.session.add(category)
        db.session.flush()

        vocab = import_vocabulary(SAMPLE_LESSON, dry_run=False)
        grammar = import_grammar(SAMPLE_LESSON, dry_run=False)

        lesson1 = create_lesson(SAMPLE_LESSON, vocab, grammar, category, dry_run=False)
        db.session.flush()

        lesson2 = create_lesson(SAMPLE_LESSON, vocab, grammar, category, dry_run=False)
        db.session.flush()

        assert Lesson.query.count() == 1
        assert lesson1.id == lesson2.id  # Gleiche Lektion zurueckgegeben


# ============================================================
# Quiz-Duplikat-Schutz-Tests
# ============================================================

class TestQuizDuplicateProtection:
    """Tests fuer den Quiz-Duplikat-Schutz in generate_quizzes.py"""

    def test_check_existing_quizzes_empty(self, app_context):
        """Leere Seite hat 0 Quizzes."""
        from app import db
        from app.models import Lesson
        from scripts.generate_quizzes import check_existing_quizzes

        lesson = Lesson(
            title="Test Lesson",
            lesson_type="free",
            is_published=True,
            order_index=1,
        )
        db.session.add(lesson)
        db.session.flush()

        assert check_existing_quizzes(lesson, page_number=1) == 0

    def test_check_existing_quizzes_with_data(self, app_context):
        """Seite mit Quizzes wird korrekt gezaehlt."""
        from app import db
        from app.models import Lesson, LessonContent
        from scripts.generate_quizzes import check_existing_quizzes

        lesson = Lesson(
            title="Test Lesson Quiz",
            lesson_type="free",
            is_published=True,
            order_index=1,
        )
        db.session.add(lesson)
        db.session.flush()

        # 3 Quiz-Eintraege auf Seite 1
        for i in range(3):
            content = LessonContent(
                lesson_id=lesson.id,
                content_type="interactive",
                title=f"Quiz {i}",
                is_interactive=True,
                page_number=1,
                order_index=900 + i,
            )
            db.session.add(content)
        db.session.flush()

        assert check_existing_quizzes(lesson, page_number=1) == 3
        assert check_existing_quizzes(lesson, page_number=2) == 0


# ============================================================
# Pipeline-Hilfsfunktionen
# ============================================================

class TestPipelineUtils:
    """Tests fuer run_pipeline.py Hilfsfunktionen."""

    def test_parse_lesson_range_single(self):
        from scripts.run_pipeline import parse_lesson_range
        assert parse_lesson_range("1") == [1]

    def test_parse_lesson_range_range(self):
        from scripts.run_pipeline import parse_lesson_range
        assert parse_lesson_range("1-5") == [1, 2, 3, 4, 5]

    def test_parse_lesson_range_comma(self):
        from scripts.run_pipeline import parse_lesson_range
        assert parse_lesson_range("1,3,5") == [1, 3, 5]

    def test_parse_lesson_range_mixed(self):
        from scripts.run_pipeline import parse_lesson_range
        assert parse_lesson_range("1-3,7,10-12") == [1, 2, 3, 7, 10, 11, 12]

    def test_parse_lesson_range_dedup(self):
        from scripts.run_pipeline import parse_lesson_range
        assert parse_lesson_range("1-3,2-4") == [1, 2, 3, 4]
