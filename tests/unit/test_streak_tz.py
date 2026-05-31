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
