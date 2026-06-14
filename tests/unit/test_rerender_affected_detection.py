# -*- coding: utf-8 -*-
"""Unit-Tests fuer die Betroffenheits-Detektion in
scripts/rerender_affected_block_audio.py (TTS-Re-Render nach dem Fix 2026-06-15)."""
import importlib.util
from pathlib import Path

import pytest

_SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "rerender_affected_block_audio.py"
)
_spec = importlib.util.spec_from_file_location("rerender_affected", _SCRIPT)
rerender_affected = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rerender_affected)
block_is_affected = rerender_affected.block_is_affected


class TestBlockIsAffected:
    @pytest.mark.parametrize(
        "text,expect_reason",
        [
            # --- Romaji nach JP-Satzzeichen ---
            ("今 七時です。 (Ima shichi-ji desu.) — Es ist sieben.", "romaji-nach-satzzeichen"),
            ("おきますか。 (Risa-san, okimasu ka.)", "romaji-nach-satzzeichen"),
            ("いきます！ (ikimasu!)", "romaji-nach-satzzeichen"),
            # --- Tilde-Platzhalter ---
            ("### 1. Uhrzeit nennen — 今 ～時 ～分 です", "tilde"),
            ("enden auf ～ます", "tilde"),
            ("von ~ bis ~", "tilde"),
        ],
    )
    def test_affected(self, text, expect_reason):
        reason = block_is_affected(text)
        assert reason is not None
        assert expect_reason in reason

    @pytest.mark.parametrize(
        "text",
        [
            "",
            "Ein ganz normaler deutscher Satz ohne Besonderheiten.",
            "これはペンです。",                              # JP ohne Romaji-Klammer
            "**fett** und ~~durchgestrichen~~",            # ~~strike~~ wird von strip_markdown entfernt
            "家族 (kazoku) — Familie",                       # Romaji nach JP-SCHRIFT (nicht Satzzeichen) → ok
        ],
    )
    def test_not_affected(self, text):
        assert block_is_affected(text) is None

    def test_combined_reasons(self):
        text = "今 ～時 です。 (Ima ji desu.)"
        reason = block_is_affected(text)
        assert "tilde" in reason and "romaji-nach-satzzeichen" in reason
