"""Unit-Tests fuer `pipeline.py insert --into-lesson` (generate-lesson-Skill).

Eine bestehende, unveroeffentlichte Lektion ohne Nutzerdaten wird neu befuellt:
Seiten, Inhalte und Quizfragen weg, Kopfdaten aus dem Draft, ID/Modul/Reihenfolge
bleiben. Sobald Nutzerdaten daran haengen oder die Lektion veroeffentlicht ist,
wird nichts angefasst.
"""
import importlib.util
import sys
from pathlib import Path

import pytest

from app.models import Lesson, LessonContent, LessonPage, QuizOption, QuizQuestion
from tests.factories import (
    LessonCategoryFactory,
    LessonContentFactory,
    LessonFactory,
    LessonPageFactory,
    QuizOptionFactory,
    QuizQuestionFactory,
    UserFactory,
    UserLessonProgressFactory,
)

SKILL_PIPELINE = (
    Path(__file__).resolve().parents[2]
    / ".claude" / "skills" / "generate-lesson" / "pipeline.py"
)
spec = importlib.util.spec_from_file_location("_genlesson_pipeline_refill", SKILL_PIPELINE)
pipeline = importlib.util.module_from_spec(spec)
sys.modules["_genlesson_pipeline_refill"] = pipeline
spec.loader.exec_module(pipeline)

DRAFT = {
    "title": "N5 Neu — Titel",
    "description": "Neue Beschreibung",
    "allow_guest_access": True,
    "instruction_language": "german",
    "thumbnail_url": "generated/thumbnail_neu.png",
}


def _old_lesson(db, published=False):
    cat = LessonCategoryFactory()
    lesson = LessonFactory(title="Alt", is_published=published, order_index=7,
                           allow_guest_access=False, instruction_language="english")
    lesson.category_id = cat.id
    for n in (1, 2):
        LessonPageFactory(lesson_id=lesson.id, page_number=n)
    LessonContentFactory(lesson_id=lesson.id, page_number=1)
    quiz = LessonContentFactory(lesson_id=lesson.id, page_number=2, content_type="text")
    question = QuizQuestionFactory(lesson_content_id=quiz.id)
    QuizOptionFactory(question_id=question.id, is_correct=True)
    db.session.commit()
    return lesson


def test_refill_leert_lektion_und_uebernimmt_kopfdaten(app_context, db):
    lesson = _old_lesson(db)
    lesson_id, cat_id = lesson.id, lesson.category_id

    pipeline.prepare_lesson_for_refill(db, Lesson, lesson_id, DRAFT, difficulty_level=1)
    db.session.commit()

    assert LessonPage.query.filter_by(lesson_id=lesson_id).count() == 0
    assert LessonContent.query.filter_by(lesson_id=lesson_id).count() == 0
    assert QuizQuestion.query.count() == 0
    assert QuizOption.query.count() == 0
    lesson = db.session.get(Lesson, lesson_id)
    assert lesson.title == "N5 Neu — Titel"
    assert lesson.description == "Neue Beschreibung"
    assert lesson.allow_guest_access is True
    assert lesson.instruction_language == "german"
    assert lesson.thumbnail_url == "generated/thumbnail_neu.png"
    assert lesson.is_published is False
    assert lesson.category_id == cat_id and lesson.order_index == 7


def test_refill_verweigert_veroeffentlichte_lektion(app_context, db):
    lesson = _old_lesson(db, published=True)
    with pytest.raises(ValueError, match="veroeffentlicht"):
        pipeline.prepare_lesson_for_refill(db, Lesson, lesson.id, DRAFT, difficulty_level=1)
    db.session.rollback()
    assert LessonContent.query.filter_by(lesson_id=lesson.id).count() == 2


def test_refill_verweigert_lektion_mit_fortschritt(app_context, db):
    lesson = _old_lesson(db)
    user = UserFactory()
    UserLessonProgressFactory(user_id=user.id, lesson_id=lesson.id)
    db.session.commit()
    assert pipeline.refill_blockers(db, lesson) == [
        "user_lesson_progress: 1 Zeile(n) haengen an der Lektion"
    ]
    with pytest.raises(ValueError, match="user_lesson_progress"):
        pipeline.prepare_lesson_for_refill(db, Lesson, lesson.id, DRAFT, difficulty_level=1)
    db.session.rollback()
    assert LessonPage.query.filter_by(lesson_id=lesson.id).count() == 2


def test_refill_unbekannte_lektion(app_context, db):
    with pytest.raises(ValueError, match="existiert nicht"):
        pipeline.prepare_lesson_for_refill(db, Lesson, 999999, DRAFT, difficulty_level=1)
