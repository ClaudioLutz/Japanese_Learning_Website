# tests/unit/test_seed_grammar_nuance.py
"""Tests für die Matching-Logik der kuratierten Nuance-Notizen
(``scripts.seed_grammar_nuance.nuance_for``)."""

from __future__ import annotations

from scripts.seed_grammar_nuance import CURATED, nuance_for


class TestNuanceFor:
    def test_matches_german_card_by_title(self):
        note = nuance_for(
            "これ/それ/あれ (Demonstrativpronomen)",
            "Die Partikel-losen Wörter これ/それ/あれ werden allein verwendet.",
        )
        assert note is not None
        assert "allein" in note.lower()

    def test_skips_english_track_card(self):
        # Gleicher Titel-Treffer, aber ENGLISCHE Erklärung → kein deutscher Hinweis.
        assert nuance_for(
            "これ/それ/あれ (Demonstrative Pronouns)",
            "These are used to point at things near or far.",
        ) is None

    def test_none_when_title_does_not_match(self):
        assert nuance_for("〜たい (Wunsch ausdrücken)",
                          "Die Form drückt einen eigenen Wunsch aus.") is None

    def test_none_for_empty_inputs(self):
        assert nuance_for(None, None) is None
        assert nuance_for("これ/それ/あれ", None) is None

    def test_curated_set_is_wellformed(self):
        assert len(CURATED) >= 5
        seen = set()
        for needle, note in CURATED:
            assert needle and needle not in seen, f"leerer/doppelter Marker: {needle!r}"
            seen.add(needle)
            assert len(note) > 30  # echte Notiz, kein Platzhalter
