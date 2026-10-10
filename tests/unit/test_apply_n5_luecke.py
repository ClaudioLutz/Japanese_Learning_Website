"""Tests für scripts/apply_n5_luecke.py (N5-Lücke 723/723, 2026-10-10)."""
import json
from pathlib import Path

import pytest

from scripts import apply_n5_luecke as ap

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "scripts" / "data"
KANJI = ap.n5_kanji()


def _update_files():
    drafts = ROOT / ".claude" / "skills" / "generate-lesson" / "drafts"
    return [DATA / "n5_luecke_bestand.json", *sorted(drafts.glob("2026-10-10_*.row_updates.json"))]


def test_neue_werte_sind_gueltig():
    for path in _update_files():
        for u in json.loads(path.read_text(encoding="utf-8"))["updates"]:
            assert u["field"] in ap.ALLOWED_FIELDS, (path.name, u)
            assert ap.check_new_value(u["field"], u["new"], KANJI) == [], (path.name, u)


def test_check_new_value_findet_fehler():
    assert ap.check_new_value("example_sentence_japanese", "お茶を のみます。", KANJI)
    assert ap.check_new_value("example_sentence_japanese", "みずを のみます", KANJI)
    assert ap.check_new_value("example_sentence_japanese", "mizu desu。", KANJI)
    assert ap.check_new_value("example_sentence_english", "Mizu desu. Wasser.", KANJI)
    assert ap.check_new_value("example_sentence_japanese", "水を のみます。", KANJI) == []


def test_plan_updates_ok_schon_skip():
    db = {(1, "romaji"): "a", (2, "romaji"): "neu", (3, "romaji"): "anders"}

    def fetch(vid, field):
        key = (vid, field)
        return (key in db), db.get(key)

    ups = [
        {"vocab_id": 1, "field": "romaji", "old": "a", "new": "neu"},
        {"vocab_id": 2, "field": "romaji", "old": "a", "new": "neu"},
        {"vocab_id": 3, "field": "romaji", "old": "a", "new": "neu"},
        {"vocab_id": 4, "field": "romaji", "old": "a", "new": "neu"},
        {"vocab_id": 1, "field": "word", "old": "a", "new": "neu"},
    ]
    writes, report = ap.plan_updates(ups, fetch, KANJI)
    assert [r[0] for r in report] == ["OK", "SCHON", "SKIP", "SKIP", "SKIP"]
    assert writes == {(1, "romaji"): ("a", "neu")}


def test_plan_page_order_haengt_hinter_anker_und_behaelt_start():
    items = [
        {"id": 10, "order_index": 0, "label": "bild"},
        {"id": 11, "order_index": 1, "label": "kanji 一"},
        {"id": 12, "order_index": 2, "label": "kanji 二"},
        {"id": 13, "order_index": 3, "label": "text"},
    ]
    inserts = [{"after_lc": 11, "vocab_id": 402, "label": "一"},
               {"after_lc": 12, "vocab_id": 403, "label": "二"}]
    plan = ap.plan_page_order(items, inserts)
    assert [it["label"] for it in plan] == ["bild", "kanji 一", "一", "kanji 二", "二", "text"]
    assert [it["new_order"] for it in plan] == [0, 1, 2, 3, 4, 5]


def test_plan_page_order_fehlender_anker():
    with pytest.raises(ValueError):
        ap.plan_page_order([{"id": 1, "order_index": 1, "label": "x"}],
                           [{"after_lc": 99, "vocab_id": 5, "label": "y"}])


def test_bestand_karten_decken_vierzehn_woerter():
    cards = json.loads((DATA / "n5_luecke_bestand.json").read_text(encoding="utf-8"))["cards"]
    assert len({c["vocab_id"] for c in cards}) == 14
    assert {c["lesson_id"] for c in cards} == {143, 164, 169}
