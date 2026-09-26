# tests/unit/test_generate_lesson_vocab_backfill.py
"""Unit-Tests fuer den Vokabel-Dedup mit Feld-Backfill in generate-lesson/pipeline.py.

`_get_or_create_vocab` matcht ueber `word`. Existiert die Vokabel bereits, wird
KEINE zweite Zeile angelegt; leere Felder (z.B. image_url) werden aus dem Draft
gefuellt, befuellte Felder bleiben unveraendert.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

SKILL_PIPELINE = (
    Path(__file__).resolve().parents[2]
    / ".claude" / "skills" / "generate-lesson" / "pipeline.py"
)
spec = importlib.util.spec_from_file_location("_genlesson_pipeline_backfill", SKILL_PIPELINE)
pipeline = importlib.util.module_from_spec(spec)
sys.modules["_genlesson_pipeline_backfill"] = pipeline
spec.loader.exec_module(pipeline)


class _FakeVocab:
    def __init__(self, **kw):
        self.id = kw.pop("id", None)
        for k, v in kw.items():
            setattr(self, k, v)


class _FakeSession:
    def __init__(self, rows):
        self.rows = rows
        self.added = []

    def query(self, _model):
        session = self

        class _Q:
            def filter_by(self, word):
                match = [r for r in session.rows if r.word == word]
                return SimpleNamespace(first=lambda: match[0] if match else None)

        return _Q()

    def add(self, obj):
        self.added.append(obj)

    def flush(self):
        for obj in self.added:
            if obj.id is None:
                obj.id = 999


def _db(rows):
    return SimpleNamespace(session=_FakeSession(rows))


def test_existing_word_reuses_id_and_fills_empty_fields():
    row = _FakeVocab(id=1058, word="おじいさん", image_url=None, romaji="ojiisan",
                     meaning_de="Grossvater", example_sentence_japanese="x。",
                     example_sentence_english=None)
    db = _db([row])
    vid = pipeline._get_or_create_vocab(db, _FakeVocab, {
        "word": "おじいさん", "reading": "おじいさん", "meaning": "grandfather",
        "romaji": "OTHER", "image_url": "vocab_generated/vocab_abc.png",
        "example_sentence_english": "Ojiisan — Grossvater",
    })
    assert vid == 1058
    assert db.session.added == []  # keine zweite Zeile
    assert row.image_url == "vocab_generated/vocab_abc.png"
    assert row.example_sentence_english == "Ojiisan — Grossvater"
    assert row.romaji == "ojiisan"  # befuellt -> nicht ueberschrieben


def test_existing_image_is_not_overwritten():
    row = _FakeVocab(id=12, word="駅", image_url="vocab_generated/old.png", romaji="eki",
                     meaning_de="Bahnhof", example_sentence_japanese="a。",
                     example_sentence_english="a — b")
    db = _db([row])
    pipeline._get_or_create_vocab(db, _FakeVocab, {
        "word": "駅", "reading": "えき", "meaning": "station",
        "image_url": "vocab_generated/new.png",
    })
    assert row.image_url == "vocab_generated/old.png"
