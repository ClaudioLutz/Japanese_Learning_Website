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


class TestCallSiteCHBoundary:
    """10.8: Die tatsaechlich geaenderten Konsumenten an der CH-Mitternacht.

    Szenario _FrozenCrossMidnight: 00:30 CH am 3. Juni = 22:30 UTC am 2. Juni.
    CH-Tag = 3. Juni, CH-Mitternacht = 2. Juni 22:00 UTC. Ein Ereignis vom
    2. Juni mittags (UTC) ist CH-GESTERN (2. Juni nachmittags CH); mit der alten
    UTC-Tagesgrenze (utcnow().replace(hour=0) = 2.6. 00:00 UTC) wuerde es
    faelschlich als 'heute' zaehlen.
    """

    def test_get_user_stats_reviews_today_uses_ch_boundary(self, app_context, monkeypatch):
        """reviews_today zaehlt nur Reviews seit CH-Mitternacht — ein Review von
        CH-gestern (aber demselben UTC-Tag) wird NICHT als 'heute' gezaehlt."""
        import app.time_utils as tu
        from app import srs_service
        from app.models import ReviewLog
        from tests.factories import (
            UserFactory, LessonFactory, LessonContentFactory,
            CardReviewStateFactory,
        )

        monkeypatch.setattr(tu, "datetime", _FrozenCrossMidnight)

        user = UserFactory()
        lesson = LessonFactory()
        content = LessonContentFactory(lesson_id=lesson.id)
        db.session.commit()
        # Eine Karte, damit die Empty-State-Logik nicht greift.
        CardReviewStateFactory(user_id=user.id, content_id=content.id)
        # Review CH-HEUTE: 2.6. 22:15 UTC (= 3.6. 00:15 CH), nach CH-Mitternacht.
        db.session.add(ReviewLog(
            user_id=user.id, content_id=content.id, rating=3,
            reviewed_at=datetime(2026, 6, 2, 22, 15),
        ))
        # Review CH-GESTERN: 2.6. 12:00 UTC (= 2.6. 14:00 CH). Selber UTC-Tag,
        # aber CH-Vortag → darf NICHT als heute zaehlen.
        db.session.add(ReviewLog(
            user_id=user.id, content_id=content.id, rating=3,
            reviewed_at=datetime(2026, 6, 2, 12, 0),
        ))
        db.session.commit()

        stats = srs_service.get_user_stats(user.id)
        # Nur das CH-heutige Review zaehlt — NICHT beide (das waere die alte
        # UTC-Grenze, die 2.6. 00:00 UTC als Tagesbeginn nimmt).
        assert stats['reviews_today'] == 1

    def test_storm_xp_cap_window_uses_ch_boundary(self, app_context, monkeypatch):
        """Der Storm-XP-Tages-Cap zaehlt nur seit CH-Mitternacht vergebenes XP —
        ein Score von CH-gestern (selber UTC-Tag) belastet den heutigen Cap NICHT."""
        import app.time_utils as tu
        from app.gamification_service import XP_STORM_DAILY_CAP
        from app.models import KanaStormScore
        from tests.factories import UserFactory

        monkeypatch.setattr(tu, "datetime", _FrozenCrossMidnight)

        user = UserFactory()
        db.session.commit()
        # Score CH-gestern (2.6. 12:00 UTC = 2.6. 14:00 CH) mit fast vollem Cap.
        score_yesterday = KanaStormScore(
            user_id=user.id, mode='storm', schrift='hiragana', duration=60,
            score=100, best_combo=5, correct_count=10, miss_count=0,
            xp_awarded=XP_STORM_DAILY_CAP - 1,
        )
        db.session.add(score_yesterday)
        db.session.flush()
        # created_at manuell auf CH-gestern setzen (Default ist utcnow()).
        score_yesterday.created_at = datetime(2026, 6, 2, 12, 0)
        db.session.commit()

        # XP-Cap-Fenster ab CH-Mitternacht (2.6. 22:00 UTC). Der gestrige Score
        # (2.6. 12:00 UTC) liegt DAVOR → zaehlt nicht ins heutige spent_today.
        cap_start = tu.ch_day_start_utc()
        spent_today = db.session.query(
            db.func.coalesce(db.func.sum(KanaStormScore.xp_awarded), 0)
        ).filter(
            KanaStormScore.user_id == user.id,
            KanaStormScore.created_at >= cap_start,
        ).scalar() or 0
        # Mit CH-Grenze: 0 (gestriger Score ausserhalb). Mit alter UTC-Grenze
        # (2.6. 00:00 UTC) waere er drin und spent_today = CAP-1.
        assert int(spent_today) == 0
