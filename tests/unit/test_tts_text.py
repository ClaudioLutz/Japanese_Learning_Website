# -*- coding: utf-8 -*-
"""Unit-Tests für app/services/tts_text.py — die DE/JP-TTS-Text-Aufbereitung.

Regressions-Schutz für den „Minus"-Bug (2026-06-14): die japanische Stimme las
einen Trennstrich am Segment-Rand (``じ —``) als „Minus" vor, die deutsche
Stimme einen führenden Pfeil (``→ Ab wann ...``) als „Pfeil nach rechts".
"""
import pytest

from app.services.tts_text import (
    clean_tts_segment,
    segment_by_language,
    strip_markdown,
    strip_romaji_after_jp,
)


class TestCleanTtsSegment:
    @pytest.mark.parametrize(
        "text,lang,expected",
        [
            # --- Der gemeldete „Minus"-Bug: Strich am JP-Segment-Rand ---
            ("じ —", "ja", "じ"),
            ("ふん —", "ja", "ふん"),
            ("はん —", "ja", "はん"),
            ("ごぜん -", "ja", "ごぜん"),
            # --- DE-Segment: führender / nachgestellter Pfeil ---
            ("→ Ab wann ist die Mittagspause?", "de", "Ab wann ist die Mittagspause?"),
            ("Mond →", "de", "Mond"),
            # --- Interner, von Spaces umgebener Trenner → Pause ---
            ("あめ / かさ / みず", "ja", "あめ、かさ、みず"),
            ("links → rechts", "de", "links, rechts"),
            ("H → B", "de", "H, B"),
            ("gut — schön", "de", "gut, schön"),
            # --- Japanische Anführungsklammern global entfernt ---
            ("「さしすせそ」", "ja", "さしすせそ"),
            ("『ほん』", "ja", "ほん"),
            ("Die S-Reihe:", "de", "Die S-Reihe"),
            # --- Reine Satzzeichen-Reste → verworfen (leerer String) ---
            ("—", "ja", ""),
            ("「", "ja", ""),
            ("/", "de", ""),
            ("  →  ", "de", ""),
            # --- REGRESSION-GUARD: sprechbare JP-Zeichen bleiben ---
            ("コーヒー —", "ja", "コーヒー"),   # Chōon ー bleibt, nur Rand-Strich weg
            ("コーヒー", "ja", "コーヒー"),
            ("ラーメン", "ja", "ラーメン"),
            ("11:59", "ja", "11:59"),           # interner Doppelpunkt (Uhrzeit) bleibt
            ("T-Reihe", "de", "T-Reihe"),       # Kompositum-Bindestrich (ohne Spaces) bleibt
            ("Stunde", "de", "Stunde"),
            ("おねえさん", "ja", "おねえさん"),
        ],
    )
    def test_clean(self, text, lang, expected):
        assert clean_tts_segment(text, lang) == expected

    def test_empty(self):
        assert clean_tts_segment("", "ja") == ""
        assert clean_tts_segment("   ", "de") == ""


class TestSegmentByLanguage:
    def test_reported_minus_bug(self):
        # „じ (ji) — Stunde" → nach Romaji-Strip „じ — Stunde" → kein Strich an die Stimme
        text = strip_romaji_after_jp(strip_markdown("じ (ji) — Stunde"))
        assert segment_by_language(text) == [("ja", "じ"), ("de", "Stunde")]

    def test_choon_preserved(self):
        text = strip_romaji_after_jp(strip_markdown("コーヒー — Kaffee"))
        assert segment_by_language(text) == [("ja", "コーヒー"), ("de", "Kaffee")]

    def test_quote_brackets_split_and_removed(self):
        # „Die S-Reihe: 「さしすせそ」" — 「 landete bei DE, 」 bei JP; beide weg
        assert segment_by_language("Die S-Reihe: 「さしすせそ」") == [
            ("de", "Die S-Reihe"),
            ("ja", "さしすせそ"),
        ]

    def test_arrow_de_to_jp(self):
        # Pfeil zwischen JP-Wort und deutscher Übersetzung verschwindet auf beiden Seiten
        assert segment_by_language("おねえさん → ältere Schwester") == [
            ("ja", "おねえさん"),
            ("de", "ältere Schwester"),
        ]

    def test_no_punctuation_only_segment(self):
        # Der freistehende „—" erzeugt kein eigenes Segment
        assert segment_by_language("あ — A") == [("ja", "あ"), ("de", "A")]

    def test_plain_japanese_unchanged(self):
        assert segment_by_language("これはペンです") == [("ja", "これはペンです")]


class TestStripMarkdown:
    def test_link_url_not_spoken(self):
        # Markdown-Link: nur der Text bleibt, die URL wird NICHT vorgelesen
        assert strip_markdown("[Lektion](https://x.ch) über") == "Lektion über"

    def test_image_removed(self):
        assert strip_markdown("![alt](https://x.ch/a.png) Text").strip() == "Text"

    def test_bold_italic_strike(self):
        assert strip_markdown("**fett** und *kursiv* und ~~weg~~") == "fett und kursiv und weg"
