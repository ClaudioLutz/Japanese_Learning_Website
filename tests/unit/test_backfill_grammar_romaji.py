"""Tests fuer scripts/backfill_grammar_romaji.py — Romaji-Erzeugung aus dem
Grammatik-`structure`-Pattern (Partikel-Norm, Platzhalter-Erhalt, Skip ohne
japanische Schrift)."""
import importlib.util
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "backfill_grammar_romaji.py"
spec = importlib.util.spec_from_file_location("backfill_grammar_romaji", SCRIPT_PATH)
backfill_grammar_romaji = importlib.util.module_from_spec(spec)
sys.modules["backfill_grammar_romaji"] = backfill_grammar_romaji
spec.loader.exec_module(backfill_grammar_romaji)

to_romaji = backfill_grammar_romaji.structure_to_romaji


def test_topic_particle_wa_and_subscripts():
    # は (Themenpartikel) -> wa (nicht ha); Indizes ₁₂ -> 12
    assert to_romaji("N₁ は N₂ です") == "N1 wa N2 desu"


def test_object_particle_o():
    # を -> o (nicht wo); lateinischer Platzhalter N bleibt
    assert to_romaji("N を ください") == "N o kudasai"


def test_direction_particle_e():
    # へ -> e (nicht he); / und 'Place' bleiben erhalten
    assert to_romaji("Place へ/に いきます") == "Place e/ni ikimasu"


def test_kanji_reading():
    # Kanji-Lesungen + ～ und / erhalten
    assert to_romaji("〜が 好き / 嫌い") == "〜ga suki / kirai"


def test_te_form_placeholder_passthrough():
    assert to_romaji("Vて ください") == "V te kudasai"


def test_no_japanese_returns_empty():
    # Rein lateinische Strukturen bekommen kein Romaji
    assert to_romaji("Potential Form") == ""
    assert to_romaji("Adjektiv") == ""
    assert to_romaji("Number + Counter") == ""


def test_empty_and_none_safe():
    assert to_romaji("") == ""
    assert to_romaji(None) == ""
