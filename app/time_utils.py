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


def home_greeting(now: datetime | None = None) -> dict[str, str]:
    """Tageszeit- + saisonabhaengige Begruessung fuer den Startseiten-Hero.

    Rein datumsbasiert (kein Wetter-API, kein Standort): die Tageszeit waehlt
    die japanische Grussformel — おはよう (Morgen) / こんにちは (Tag) /
    こんばんは (Abend & Nacht), allesamt N5-Stoff, das der Lerner so zur
    passenden Zeit nebenbei erlebt. Der Monat waehlt ein dezentes Saison-Emoji
    (四季: 桜 / 風鈴 / 紅葉 / 雪). Zeit + Saison laufen in Europe/Zurich (CH-Ziel-
    gruppe; die Nordhalbkugel-Saison deckt sich ohnehin mit Japan).

    Rueckgabe: ``{"greeting", "season_emoji", "season_label"}`` — season_label
    ist deutsch fuer aria-label/title, das Emoji bleibt rein dekorativ.
    """
    if now is None:
        now = ch_now()

    hour = now.hour
    if 5 <= hour < 11:
        greeting = "おはよう"        # Guten Morgen
    elif 11 <= hour < 18:
        greeting = "こんにちは"      # Guten Tag
    else:
        greeting = "こんばんは"      # Guten Abend / Nacht (18–4 Uhr)

    # Meteorologische Jahreszeiten -> japanisches Saison-Emoji (Nordhalbkugel).
    month = now.month
    if month in (3, 4, 5):
        season_emoji, season_label = "🌸", "Frühling"   # 桜 Kirschblüte
    elif month in (6, 7, 8):
        season_emoji, season_label = "🎐", "Sommer"     # 風鈴 Sommer-Windglocke
    elif month in (9, 10, 11):
        season_emoji, season_label = "🍁", "Herbst"     # 紅葉 Herbstlaub
    else:
        season_emoji, season_label = "❄️", "Winter"     # 雪 Schnee

    return {
        "greeting": greeting,
        "season_emoji": season_emoji,
        "season_label": season_label,
    }
