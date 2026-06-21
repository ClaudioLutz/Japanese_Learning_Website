# tests/unit/test_generate_lesson_word_reuse.py
"""Unit-Tests fuer den Wort-Wiederverwendungs-Check in generate-lesson/pipeline.py.

Deckt den reinen Kern `compute_reused_words` ab (ohne DB):
  * Inhaltswoerter, die bereits in anderen Lektionen vorkommen, werden gemeldet
  * Kern-Funktionswoerter (CORE_FUNCTION_WORDS) sind ausgenommen
  * Draft-interne Dubletten zaehlen nur einmal
  * Sortierung absteigend nach Lektions-Zahl
  * Robustheit gegen int-Form der used_map und fehlende/leere Eintraege

User-Direktive 2026-06-21: neue Lektionen sollen primaer NEUE Lern-Vokabeln
einfuehren statt schon vorhandene zu doppeln.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SKILL_PIPELINE = (
    Path(__file__).resolve().parents[2]
    / ".claude" / "skills" / "generate-lesson" / "pipeline.py"
)
spec = importlib.util.spec_from_file_location("_genlesson_pipeline_reuse", SKILL_PIPELINE)
pipeline = importlib.util.module_from_spec(spec)
sys.modules["_genlesson_pipeline_reuse"] = pipeline
spec.loader.exec_module(pipeline)


def _draft(words: list[str]) -> dict:
    """Minimaler Draft mit einer Vokabel-Page (nur `word` relevant)."""
    contents = [{"content_type": "vocabulary", "data": {"word": w}} for w in words]
    contents.append({"content_type": "text", "data": {"content_text": "x"}})
    return {"pages": [{"contents": contents}]}


def test_content_words_already_used_are_reported():
    draft = _draft(["いぬ", "ねこ"])
    used = {
        "いぬ": {"lessons": {1, 2, 3}, "published": {1}},
        "ねこ": {"lessons": {5}, "published": set()},
    }
    reused, distinct = pipeline.compute_reused_words(draft, used)
    assert distinct == ["いぬ", "ねこ"]
    # absteigend nach Lektions-Zahl
    assert reused == [("いぬ", 3), ("ねこ", 1)]


def test_core_function_words_are_exempt():
    # これ/です stehen in CORE_FUNCTION_WORDS -> keine Warnung, auch wenn benutzt
    draft = _draft(["これ", "です", "いぬ"])
    used = {
        "これ": {"lessons": {1, 2, 3, 4}, "published": {1}},
        "です": {"lessons": {1, 2}, "published": {1}},
        "いぬ": {"lessons": {7}, "published": set()},
    }
    reused, distinct = pipeline.compute_reused_words(draft, used)
    assert distinct == ["これ", "です", "いぬ"]
    assert reused == [("いぬ", 1)]


def test_draft_internal_duplicate_counts_once():
    draft = _draft(["いぬ", "いぬ", "ねこ"])
    used = {"いぬ": {"lessons": {1}}, "ねこ": {"lessons": {2}}}
    reused, distinct = pipeline.compute_reused_words(draft, used)
    assert distinct == ["いぬ", "ねこ"]
    assert [w for w, _ in reused] == ["いぬ", "ねこ"]


def test_new_words_produce_empty_reused():
    draft = _draft(["とり", "うま"])
    used = {"いぬ": {"lessons": {1}}}  # keine Ueberschneidung
    reused, distinct = pipeline.compute_reused_words(draft, used)
    assert distinct == ["とり", "うま"]
    assert reused == []


def test_used_map_int_form_is_supported():
    # _load_used_vocab_map liefert dict-Form; der Kern toleriert auch int-Counts.
    draft = _draft(["いぬ"])
    reused, _ = pipeline.compute_reused_words(draft, {"いぬ": 2})
    assert reused == [("いぬ", 2)]


def test_allowlist_contains_expected_core_words():
    for w in ("これ", "それ", "あれ", "です", "ます", "わたし"):
        assert w in pipeline.CORE_FUNCTION_WORDS
    # Inhaltswoerter duerfen NICHT in der Allowlist sein
    for w in ("いぬ", "ねこ", "がっこう"):
        assert w not in pipeline.CORE_FUNCTION_WORDS
