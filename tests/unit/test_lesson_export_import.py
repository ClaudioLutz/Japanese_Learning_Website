"""Round-Trip-Tests fuer den Lektions-Export/Import (Dev->Prod-Migration).

Verifiziert das Mechanismus gegen die Test-DB (sqlite in-memory): eine Lektion
mit Vokabel-, Text- und Quiz-Content wird importiert, exportiert, erneut
importiert und exportiert — die Struktur muss idempotent erhalten bleiben.

Hinweis: deckt den Mechanismus ab, nicht jede Real-Daten-Eigenheit. Vor einem
echten Prod-Publish trotzdem an einer realen Lektion gegenpruefen.
"""
import importlib.util
from pathlib import Path

import pytest

_PIPELINE_PATH = (
    Path(__file__).resolve().parents[2]
    / ".claude" / "skills" / "generate-lesson" / "pipeline.py"
)


def _load_pipeline():
    spec = importlib.util.spec_from_file_location("gl_pipeline", _PIPELINE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


pipeline = _load_pipeline()


def _sample_lesson():
    return {
        "schema": "jpl-lesson-export/1",
        "title": "Export-Test N5 Farben",
        "description": "Round-trip Testlektion",
        "jlpt_level": 5,
        "thumbnail_url": "generated/thumb_test.png",
        "allow_guest_access": True,
        "instruction_language": "german",
        "lesson_type": "free",
        "category_slug": None,
        "pages": [
            {"title": "Vokabeln", "page_type": "normal", "contents": [
                {"content_type": "vocabulary", "is_interactive": False, "data": {
                    "word": "青", "reading": "あお", "romaji": "ao", "meaning": "blue",
                    "meaning_de": "blau", "jlpt_level": 5,
                    "example_sentence_japanese": "そらは あおいです。",
                    "example_sentence_english": "Sora wa aoi desu. — Der Himmel ist blau.",
                    "image_url": "vocab_generated/vocab_ao.png"}},
                {"content_type": "text", "is_interactive": False, "data": {
                    "title": "Hinweis", "content_text": "## Farben\n**青** (ao) = blau."}},
            ]},
            {"title": "Übung", "page_type": "quiz_carousel", "contents": [
                {"content_type": "text", "is_interactive": True,
                 "data": {"title": None, "content_text": None},
                 "quiz_questions": [
                     {"question_type": "multiple_choice", "question_text": "青 (ao)?",
                      "explanation": "青 = blau", "hint": None,
                      "difficulty_level": 1, "points": 1, "options": [
                          {"option_text": "blau", "is_correct": True, "feedback": "Richtig!"},
                          {"option_text": "rot", "is_correct": False, "feedback": "Nein, 赤."},
                      ]},
                 ]},
            ]},
        ],
    }


def test_export_import_roundtrip(app_context):
    data_in = _sample_lesson()
    lid = pipeline.import_lesson(data_in)
    assert isinstance(lid, int)

    exported = pipeline.export_lesson(lid)
    assert exported["schema"] == "jpl-lesson-export/1"
    assert exported["title"] == data_in["title"]
    assert exported["jlpt_level"] == 5
    assert exported["allow_guest_access"] is True
    assert len(exported["pages"]) == 2

    vocab = exported["pages"][0]["contents"][0]
    assert vocab["content_type"] == "vocabulary"
    assert vocab["data"]["word"] == "青"
    assert vocab["data"]["romaji"] == "ao"
    assert vocab["data"]["image_url"] == "vocab_generated/vocab_ao.png"

    text = exported["pages"][0]["contents"][1]
    assert text["content_type"] == "text"
    assert "Farben" in text["data"]["content_text"]

    quiz_item = exported["pages"][1]["contents"][0]
    q0 = quiz_item["quiz_questions"][0]
    assert q0["question_text"] == "青 (ao)?"
    assert q0["options"][0] == {"option_text": "blau", "is_correct": True, "feedback": "Richtig!"}

    # Idempotenz: re-import + re-export liefert dieselbe Struktur (neue lesson_id).
    lid2 = pipeline.import_lesson(exported)
    assert lid2 != lid
    re_exported = pipeline.export_lesson(lid2)
    assert re_exported["pages"] == exported["pages"]


def test_export_missing_lesson_raises(app_context):
    with pytest.raises(ValueError):
        pipeline.export_lesson(999999)
