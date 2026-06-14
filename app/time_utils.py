"""Zentrale Tagesgrenzen-Helfer (10.8).

EINE gemeinsame Quelle dafuer, welcher Kalendertag "heute" ist, fuer alle
*taeglichen* Grenzen: Streak, DailyReviewAggregate, Daily-Challenge-Seed,
Storm-Daily-Board, XP-Tages-Cap und "heute reviewt"-Zaehlungen.

Strategie C: alle "taeglichen" Grenzen laufen in **Europe/Zurich** (der Tag,
den der Nutzer sieht). Das FSRS-Scheduling bleibt davon unberuehrt: due_date,
reviewed_at und due-Vergleiche (`due <= now`) bleiben in UTC — das ist die
Frage "WANN ist eine Karte faellig", nicht "welcher Kalendertag ist heute".
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

CH_TZ = ZoneInfo("Europe/Zurich")


def ch_now() -> datetime:
    """Aktuelle Wandzeit in Europe/Zurich (tz-aware)."""
    return datetime.now(CH_TZ)


def ch_today() -> date:
    """Der Kalendertag, den ein Nutzer in der Schweiz gerade sieht.

    Konsistent mit User.update_streak und DailyReviewAggregate (beide nutzen
    bereits datetime.now(ZoneInfo('Europe/Zurich')).date()).
    """
    return ch_now().date()


def ch_day_start_utc(day: date | None = None) -> datetime:
    """UTC-Zeitpunkt (naiv) des Beginns eines CH-Kalendertags.

    Fuer Vergleiche gegen in UTC gespeicherte Zeitstempel (z.B.
    ReviewLog.reviewed_at, KanaStormScore.created_at): "seit Beginn des
    heutigen CH-Tages" = CH-Mitternacht, in UTC umgerechnet. Rueckgabe ist
    naiv (tzinfo entfernt), passend zu datetime.utcnow()-gespeicherten Werten.

    `day` default = ch_today().
    """
    if day is None:
        day = ch_today()
    ch_midnight = datetime(day.year, day.month, day.day, tzinfo=CH_TZ)
    return ch_midnight.astimezone(timezone.utc).replace(tzinfo=None)
