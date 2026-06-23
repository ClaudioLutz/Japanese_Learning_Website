"""Unit-Tests fuer die Tageszeit- + saisonabhaengige Startseiten-Begruessung
(``app.time_utils.home_greeting``).

Rein datumsbasiert und deterministisch: ``home_greeting`` nimmt ``now`` als
Argument, daher koennen wir feste Zeitpunkte einspeisen, ohne die Uhr zu mocken.
"""
from datetime import datetime

import pytest

from app.time_utils import home_greeting


@pytest.mark.parametrize(
    "hour, expected",
    [
        (5, "おはよう"),    # untere Morgen-Grenze
        (8, "おはよう"),
        (10, "おはよう"),   # letzte Morgen-Stunde
        (11, "こんにちは"),  # Tag beginnt
        (14, "こんにちは"),
        (17, "こんにちは"),  # letzte Tag-Stunde
        (18, "こんばんは"),  # Abend beginnt
        (20, "こんばんは"),
        (23, "こんばんは"),
        (0, "こんばんは"),   # Mitternacht/Nacht
        (4, "こんばんは"),   # letzte Nacht-Stunde vor dem Morgen
    ],
)
def test_tageszeit_waehlt_grussformel(hour, expected):
    now = datetime(2026, 6, 23, hour, 30)
    assert home_greeting(now)["greeting"] == expected


@pytest.mark.parametrize(
    "month, emoji, label",
    [
        (3, "🌸", "Frühling"),
        (4, "🌸", "Frühling"),
        (5, "🌸", "Frühling"),
        (6, "🎐", "Sommer"),
        (7, "🎐", "Sommer"),
        (8, "🎐", "Sommer"),
        (9, "🍁", "Herbst"),
        (10, "🍁", "Herbst"),
        (11, "🍁", "Herbst"),
        (12, "❄️", "Winter"),
        (1, "❄️", "Winter"),
        (2, "❄️", "Winter"),
    ],
)
def test_monat_waehlt_saison(month, emoji, label):
    now = datetime(2026, month, 15, 12, 0)
    result = home_greeting(now)
    assert result["season_emoji"] == emoji
    assert result["season_label"] == label


def test_alle_monate_und_stunden_liefern_gueltige_werte():
    """Vollabdeckung: jede Stunde + jeder Monat ergibt einen der erlaubten Werte
    (keine Luecke faellt durch den if/elif-Baum)."""
    greetings = {"おはよう", "こんにちは", "こんばんは"}
    emojis = {"🌸", "🎐", "🍁", "❄️"}
    for month in range(1, 13):
        for hour in range(24):
            r = home_greeting(datetime(2026, month, 1, hour, 0))
            assert r["greeting"] in greetings
            assert r["season_emoji"] in emojis
            assert r["season_label"]  # nicht leer


def test_default_ohne_argument_nutzt_jetzt():
    """Ohne ``now`` greift ``ch_now()`` (Europe/Zurich) — Ergebnis bleibt gueltig."""
    result = home_greeting()
    assert set(result.keys()) == {"greeting", "season_emoji", "season_label"}
    assert result["greeting"] in {"おはよう", "こんにちは", "こんばんは"}
    assert result["season_emoji"] in {"🌸", "🎐", "🍁", "❄️"}
