"""Unit-Tests fuer die Vokabel-Deduplizierung beim Lektions-Insert
(generate-lesson/pipeline.py::_get_or_create_vocab).

Pruefen: explizite vocabulary_id wird referenziert (keine zweite Zeile),
Wort-Abgleich schuetzt vor falscher ID, nur leere Felder werden gefuellt.
"""
import importlib.util
import sys
from pathlib import Path

import pytest

SKILL_PIPELINE = (
    Path(__file__).resolve().parents[2]
    / ".claude" / "skills" / "generate-lesson" / "pipeline.py"
)
spec = importlib.util.spec_from_file_location("_genlesson_pipeline_dedup", SKILL_PIPELINE)
pipeline = importlib.util.module_from_spec(spec)
sys.modules["_genlesson_pipeline_dedup"] = pipeline
spec.loader.exec_module(pipeline)


class FakeVocab:
    def __init__(self, id=None, **kw):
        self.id = id
        for f in ("word", "reading", "romaji", "meaning", "meaning_de", "jlpt_level",
                  "example_sentence_japanese", "example_sentence_english", "image_url",
                  "status", "created_by_ai"):
            setattr(self, f, kw.get(f))


class FakeQuery:
    def __init__(self, rows):
        self.rows = rows
        self._word = None

    def filter_by(self, word):
        self._word = word
        return self

    def first(self):
        return next((r for r in self.rows if r.word == self._word), None)


class FakeSession:
    def __init__(self, rows):
        self.rows = rows
        self.added = []

    def get(self, model, pk):
        return next((r for r in self.rows if r.id == pk), None)

    def query(self, model):
        return FakeQuery(self.rows)

    def add(self, obj):
        self.added.append(obj)

    def flush(self):
        for i, obj in enumerate(self.added, start=900):
            if obj.id is None:
                obj.id = i


class FakeDB:
    def __init__(self, rows):
        self.session = FakeSession(rows)


def _data(**kw):
    base = {"word": "財布", "reading": "さいふ", "romaji": "saifu", "meaning": "wallet",
            "meaning_de": "Portemonnaie", "image_url": "vocab_generated/vocab_x.png"}
    base.update(kw)
    return base


def test_vocabulary_id_referenziert_bestehende_zeile_und_fuellt_nur_leere_felder():
    row = FakeVocab(id=1041, word="財布", reading="さいふ", meaning_de="Geldbeutel", image_url=None)
    db = FakeDB([row])
    vid = pipeline._get_or_create_vocab(db, FakeVocab, _data(vocabulary_id=1041))
    assert vid == 1041
    assert db.session.added == []                      # keine zweite Zeile
    assert row.image_url == "vocab_generated/vocab_x.png"  # leeres Feld gefuellt
    assert row.meaning_de == "Geldbeutel"              # bestehender Wert bleibt


def test_vocabulary_id_mit_falschem_wort_bricht_ab():
    db = FakeDB([FakeVocab(id=1041, word="紙")])
    with pytest.raises(ValueError):
        pipeline._get_or_create_vocab(db, FakeVocab, _data(vocabulary_id=1041))


def test_vocabulary_id_unbekannt_bricht_ab():
    db = FakeDB([])
    with pytest.raises(ValueError):
        pipeline._get_or_create_vocab(db, FakeVocab, _data(vocabulary_id=4711))


def test_match_ueber_wort_ohne_id_fuellt_fehlendes_bild():
    row = FakeVocab(id=7, word="財布", image_url=None)
    db = FakeDB([row])
    assert pipeline._get_or_create_vocab(db, FakeVocab, _data()) == 7
    assert db.session.added == []
    assert row.image_url == "vocab_generated/vocab_x.png"
