"""Unit-Tests fuer scripts/apply_n5_vocab_fill.py und die Varianten-Logik
des Coverage-Tools (generate-lesson/pipeline.py)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from scripts.apply_n5_vocab_fill import DATA_DIR, DEFAULT_GLOB, load_entries, plan, validate

ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = ROOT / ".claude" / "skills" / "generate-lesson"

spec = importlib.util.spec_from_file_location("_genlesson_pipeline_cov", SKILL_DIR / "pipeline.py")
pipeline = importlib.util.module_from_spec(spec)
sys.modules["_genlesson_pipeline_cov"] = pipeline
spec.loader.exec_module(pipeline)


def _entry(**overrides) -> dict[str, str]:
    data = {
        "word": "熱い",
        "reading": "あつい",
        "romaji": "atsui",
        "meaning": "hot (objects)",
        "meaning_de": "heiss (Gegenstände)",
        "production_cue_de": "heiss (nicht Wetter)",
        "japanese": "熱いおちゃを飲みます。",
        "example_romaji": "Atsui o-cha o nomimasu.",
        "german": "Ich trinke heissen Tee.",
    }
    data.update(overrides)
    return data


def test_validate_builds_card_format():
    values, err = validate(_entry())
    assert err is None
    assert values["example_sentence_english"] == "Atsui o-cha o nomimasu. — Ich trinke heissen Tee."
    assert values["jlpt_level"] == 5
    assert values["status"] == "approved"
    assert values["created_by_ai"] is True


def test_validate_rejects_eszett_and_missing_fields():
    _, err = validate(_entry(german="Das ist heiß."))
    assert err and "ß" in err
    _, err = validate(_entry(production_cue_de=""))
    assert err and "production_cue_de" in err


def test_validate_rejects_romaji_in_sentence():
    _, err = validate(_entry(japanese="熱いおちゃ (atsui ocha) desu"))
    assert err


def test_plan_never_touches_existing_words():
    to_insert, skipped, invalid = plan([_entry(), _entry(word="厚い")], existing_words={"熱い"})
    assert skipped == ["熱い"]
    assert [v["word"] for v in to_insert] == ["厚い"]
    assert invalid == []


def test_plan_flags_duplicates():
    _, _, invalid = plan([_entry(), _entry()], existing_words=set())
    assert invalid and "doppelt" in invalid[0][1]


def test_data_files_are_valid_and_disjoint_from_variants():
    entries = load_entries(sorted(DATA_DIR.glob(DEFAULT_GLOB)))
    assert entries, "keine Batch-Dateien gefunden"
    to_insert, skipped, invalid = plan(entries, existing_words=set())
    assert invalid == []
    variants = json.loads((SKILL_DIR / "sources" / "jlpt_n5_variants.json").read_text(encoding="utf-8"))
    variant_words = {v["canonical"] for v in variants["variants"]}
    assert not variant_words & {v["word"] for v in to_insert}


def test_compute_vocab_coverage_counts_variants():
    canon = {"ある", "有る", "熱い", "零"}
    direct, via, missing = pipeline.compute_vocab_coverage(
        canon, db_words={"ある", "熱い"}, aliases={"有る": "ある", "零": "ゼロ"}
    )
    assert direct == {"ある", "熱い"}
    assert via == {"有る"}
    assert missing == {"零"}  # Alias-Ziel fehlt in der DB -> bleibt fehlend
