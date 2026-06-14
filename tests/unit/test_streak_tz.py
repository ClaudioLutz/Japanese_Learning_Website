# tests/unit/test_streak_tz.py
"""Unit-Tests fuer G2: User.update_streak nutzt die CH-Lokal-Tagesgrenze
(Europe/Zurich), nicht UTC.

Bug vorher: update_streak verwendete datetime.utcnow().date(). In der Schweiz
(UTC+1/+2) faellt eine spaetabendliche Session kurz nach Mitternacht CH noch auf
den UTC-Vortag — damit zaehlt der Streak auf den falschen Kalendertag und kann
faelschlich brechen (oder doppelt zaehlen). Erwartet: der Tag, den der Nutzer in
CH sieht, ist massgeblich.
"""
from datetime import datetime, date, timezone
from zoneinfo import ZoneInfo

from app import db
from tests.factories import UserFactory


class _FrozenDatetime:
    """Ersetzt datetime in app.models, sodass `now(tz)` und `utcnow()` an einem
    Zeitpunkt liegen, an dem CH-Datum und UTC-Datum auseinanderfallen:
    00:30 Uhr CH am 2. Tag = 23:30 UTC am 1. Tag (Winter, UTC+1).
    """
    # CH-Wandzeit: 2. Juni 2026, 00:30 (Sommerzeit UTC+2 → UTC = 1. Juni 22:30)
    _ch = datetime(2026, 6, 2, 0, 30, tzinfo=ZoneInfo("Europe/Zurich"))

    @classmethod
    def now(cls, tz=None):
        if tz is not None:
            return cls._ch.astimezone(tz)
        return cls._ch.replace(tzinfo=None)

    @classmethod
    def utcnow(cls):
        # Naives UTC — wie datetime.utcnow() es liefert (hier: 1. Juni)
        return cls._ch.astimezone(timezone.utc).replace(tzinfo=None)


class TestStreakTimezone:
    def test_utc_and_ch_date_differ_in_fixture(self):
        """Sanity: Die Fixture stellt wirklich einen Tagesgrenzen-Konflikt her."""
        ch_date = _FrozenDatetime.now(ZoneInfo("Europe/Zurich")).date()
        utc_date = _FrozenDatetime.utcnow().date()
        assert ch_date == date(2026, 6, 2)
        assert utc_date == date(2026, 6, 1)
        assert ch_date != utc_date

    def test_late_evening_session_counts_for_ch_day(self, app_context, monkeypatch):
        """Eine 00:30-CH-Session, deren Vortag (CH) bereits aktiv war, fuehrt den
        Streak fort — sie darf NICHT auf den UTC-Vortag fallen (sonst 'bereits
        heute aktiv' am falschen Tag bzw. Fehlinterpretation)."""
        import app.models as models
        monkeypatch.setattr(models, "datetime", _FrozenDatetime)

        user = UserFactory()
        # CH-gestern (1. Juni) war aktiv, current_streak = 5
        user.last_activity_date = date(2026, 6, 1)
        user.current_streak = 5
        db.session.commit()

        user.update_streak()

        # CH-heute ist der 2. Juni → gestern (1.6.) aktiv → Streak +1 = 6
        assert user.last_activity_date == date(2026, 6, 2)
        assert user.current_streak == 6

    def test_uses_zurich_today_not_utc_today(self, app_context, monkeypatch):
        """last_activity_date wird auf das CH-Datum (2. Juni) gesetzt, nicht auf
        das UTC-Datum (1. Juni)."""
        import app.models as models
        monkeypatch.setattr(models, "datetime", _FrozenDatetime)

        user = UserFactory()
        user.last_activity_date = None
        user.current_streak = 0
        db.session.commit()

        user.update_streak()

        assert user.last_activity_date == date(2026, 6, 2)
        assert user.last_activity_date != _FrozenDatetime.utcnow().date()
        assert user.current_streak == 1

    def test_real_zoneinfo_is_used(self, app_context, monkeypatch):
        """Ohne Patch: update_streak ruft datetime.now(ZoneInfo('Europe/Zurich')).
        Verifiziert, dass das gesetzte Datum dem aktuellen CH-Datum entspricht."""
        user = UserFactory()
        user.last_activity_date = None
        db.session.commit()

        user.update_streak()

        expected = datetime.now(ZoneInfo("Europe/Zurich")).date()
        assert user.last_activity_date == expected


# ── 10.8: Tagesgrenzen-Vereinheitlichung (Strategie C) ──────────

class _FrozenLateEvening(datetime):
    """Frozen-Clock fuer time_utils: 23:30 CH am 2. Juni 2026 (Sommer, UTC+2)
    = 21:30 UTC am 2. Juni. CH-Datum und UTC-Datum sind hier GLEICH (2. Juni) —
    die Tageskonsistenz muss trotzdem zwischen allen Grenzen halten. Zusaetzlich
    deckt _FrozenDatetime (00:30 CH) den Fall ab, wo die Daten auseinanderfallen.

    Subklasse von datetime, damit Konstruktor-Aufrufe (datetime(...)) in
    ch_day_start_utc weiterhin funktionieren — nur now() ist eingefroren.
    """
    _ch = datetime(2026, 6, 2, 23, 30, tzinfo=ZoneInfo("Europe/Zurich"))

    @classmethod
    def now(cls, tz=None):
        if tz is not None:
            return cls._ch.astimezone(tz)
        return cls._ch.replace(tzinfo=None)


class _FrozenCrossMidnight(datetime):
    """time_utils-Clock fuer 00:30 CH (3. Juni) = 22:30 UTC (2. Juni) — CH- und
    UTC-Kalendertag fallen auseinander. ch_today muss den CH-Tag (3.) liefern."""
    _ch = datetime(2026, 6, 3, 0, 30, tzinfo=ZoneInfo("Europe/Zurich"))

    @classmethod
    def now(cls, tz=None):
        if tz is not None:
            return cls._ch.astimezone(tz)
        return cls._ch.replace(tzinfo=None)


class TestTimeUtils:
    def test_ch_today_uses_zurich_calendar_day(self, monkeypatch):
        """ch_today liefert den CH-Kalendertag, auch wenn UTC schon/noch
        auf einem anderen Tag steht."""
        import app.time_utils as tu
        monkeypatch.setattr(tu, "datetime", _FrozenCrossMidnight)
        # 00:30 CH am 3.6. (= 22:30 UTC am 2.6.) → CH-Tag ist der 3.
        assert tu.ch_today() == date(2026, 6, 3)

    def test_ch_day_start_utc_is_ch_midnight_in_utc(self, monkeypatch):
        """ch_day_start_utc liefert CH-Mitternacht als naiven UTC-Zeitstempel.
        Sommer (UTC+2): CH-Mitternacht 3.6. = 1.6.→ 2.6. 22:00 UTC."""
        import app.time_utils as tu
        monkeypatch.setattr(tu, "datetime", _FrozenCrossMidnight)
        start = tu.ch_day_start_utc()
        # CH-Mitternacht des 3. Juni = 2. Juni 22:00 UTC (Sommerzeit UTC+2), naiv
        assert start == datetime(2026, 6, 2, 22, 0)
        assert start.tzinfo is None


class TestDailyBoundaryConsistency:
    """10.8: Streak, Daily-Challenge-Seed, Storm-Daily-Seed und XP-Cap-Fenster
    nutzen an einem CH-Spaetabend-Zeitpunkt denselben Kalendertag."""

    def test_all_daily_boundaries_agree_on_ch_day(self, app_context, monkeypatch):
        import app.time_utils as tu
        import app.models as models

        # time_utils + models auf denselben CH-Spaetabend (23:30 CH, 2. Juni) frieren.
        monkeypatch.setattr(tu, "datetime", _FrozenLateEvening)
        monkeypatch.setattr(models, "datetime", _FrozenLateEvening)

        expected_day = date(2026, 6, 2)

        # 1) Streak (models.update_streak nutzt models.datetime.now(ZoneInfo))
        user = UserFactory()
        user.last_activity_date = None
        db.session.commit()
        user.update_streak()
        assert user.last_activity_date == expected_day

        # 2) Daily-Challenge-Seed + 3) Storm-Daily-Seed nutzen ch_today()
        assert tu.ch_today() == expected_day

        # 4) XP-Cap-Fenster = Beginn des CH-Tages, in UTC. Liegt auf demselben
        #    Kalendertag-Anker (2. Juni) — 21:30 UTC liegt nach dem Tagesbeginn.
        cap_start = tu.ch_day_start_utc()
        # CH-Mitternacht 2.6. (Sommer UTC+2) = 1.6. 22:00 UTC
        assert cap_start == datetime(2026, 6, 1, 22, 0)
        # Der aktuelle Moment (21:30 UTC am 2.6.) liegt nach dem Cap-Fensterbeginn.
        now_utc = _FrozenLateEvening.now(ZoneInfo("UTC")).replace(tzinfo=None)
        assert now_utc >= cap_start
        # Und der Cap-Fensterbeginn gehoert zum erwarteten CH-Tag.
        assert tu.ch_day_start_utc(expected_day) == cap_start
