# tests/unit/test_generate_lesson_vocab_image_scene.py
"""Unit-Tests fuer die Szenen-Extraktion der Vokabel-Karten-Bilder.

Direktive 2026-06-21: Das Karten-Bild wird zum BEISPIELSATZ generiert, nicht
zum Wort. `_scene_from_vocab` zieht die deutsche Uebersetzung aus
`example_sentence_english` (Format 'Romaji — Deutsche Uebersetzung').
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SKILL_PIPELINE = (
    Path(__file__).resolve().parents[2]
    / ".claude" / "skills" / "generate-lesson" / "pipeline.py"
)
spec = importlib.util.spec_from_file_location("_genlesson_pipeline_scene", SKILL_PIPELINE)
pipeline = importlib.util.module_from_spec(spec)
sys.modules["_genlesson_pipeline_scene"] = pipeline
spec.loader.exec_module(pipeline)


def test_scene_takes_german_side_of_em_dash():
    data = {"example_sentence_english": "Rouka o souji shimasu. — Ich putze den Flur."}
    assert pipeline._scene_from_vocab(data) == "Ich putze den Flur."


def test_scene_handles_extra_em_dash_in_translation():
    # split mit maxsplit=1: nur am ersten Em-Dash trennen
    data = {"example_sentence_english": "Romaji. — Es ist kalt — sehr kalt."}
    assert pipeline._scene_from_vocab(data) == "Es ist kalt — sehr kalt."


def test_scene_none_without_em_dash():
    data = {"example_sentence_english": "Nur Romaji ohne Trenner."}
    assert pipeline._scene_from_vocab(data) is None


def test_scene_none_when_missing_or_empty():
    assert pipeline._scene_from_vocab({}) is None
    assert pipeline._scene_from_vocab({"example_sentence_english": ""}) is None
    assert pipeline._scene_from_vocab({"example_sentence_english": "Romaji. —   "}) is None
