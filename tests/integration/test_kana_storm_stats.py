# tests/integration/test_kana_storm_stats.py
"""Integration-Tests fuer die Kana-Storm-Server-Statistik + XP.

Deckt ab: Speicher-Endpoint /api/practice/kana/storm-finish (Persistenz,
Anti-Cheat-Clamping, grind-sichere XP mit Tages-Cap, Login-Pflicht), die
Aggregat-Funktion get_kana_storm_stats, die Storm-Sektion auf /review/stats und
den Login-Gate-Fix im Storm-Partial (kein Konto-Upsell fuer Eingeloggte).
"""
from datetime import date

from app.models import KanaStormScore, DailyReviewAggregate, User
from app.gamification_service import (
    XP_STORM_BASE, XP_STORM_RUN_BONUS_CAP, XP_STORM_DAILY_CAP,
)
from app.srs_service import get_kana_storm_stats
from tests.factories import (
    UserFactory, CardReviewStateFactory, LessonFactory, LessonContentFactory,
)


class TestStormFinishEndpoint:
    """POST /api/practice/kana/storm-finish."""

    def test_saves_round_and_awards_xp(self, auth_client, db):
        client, user = auth_client
        resp = client.post('/api/practice/kana/storm-finish', json={
            'mode': 'storm', 'schrift': 'hiragana', 'duration': 60,
            'score': 240, 'best_combo': 12, 'correct': 18, 'misses': 2,
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['saved'] is True
        # XP = Basis + min(correct, RunCap) = 3 + min(18, 15) = 18
        assert data['xp_awarded'] == XP_STORM_BASE + XP_STORM_RUN_BONUS_CAP
        assert data['best_score'] == 240
        # KPM = 18 richtige / 60s * 60 = 18 (dauer-unabhaengig vergleichbar).
        assert data['best_kpm'] == 18
        assert data['games'] == 1
        # Persistiert + XP auf dem User.
        row = KanaStormScore.query.filter_by(user_id=user.id).first()
        assert row is not None
        assert row.score == 240
        assert row.correct_count == 18 and row.miss_count == 2
        assert db.session.get(User, user.id).total_xp == data['xp_awarded']

    def test_requires_login(self, client, db):
        resp = client.post('/api/practice/kana/storm-finish', json={
            'mode': 'storm', 'score': 100, 'correct': 10,
        })
        assert resp.status_code in (301, 302, 401)
        assert KanaStormScore.query.count() == 0

    def test_clamps_cheated_values(self, auth_client, db):
        client, user = auth_client
        resp = client.post('/api/practice/kana/storm-finish', json={
            'mode': 'storm', 'schrift': 'bogus', 'duration': 999999,
            'score': 10 ** 9, 'best_combo': 99999, 'correct': 5, 'misses': -3,
        })
        assert resp.status_code == 200
        row = KanaStormScore.query.filter_by(user_id=user.id).first()
        assert row.score == 100000              # auf Max geclamped
        assert row.schrift == 'hiragana'        # unbekannte Schrift -> Default
        assert row.duration == 7200             # auf Max geclamped
        assert row.miss_count == 0              # negativ -> 0
        assert row.best_combo == row.correct_count + 1  # Combo <= Treffer + 1

    def test_daily_xp_cap(self, auth_client, db):
        client, user = auth_client
        # Jede Runde gibt 3 + min(30, 15) = 18 XP; Tages-Cap 60 -> danach 0.
        granted = []
        for _ in range(6):
            d = client.post('/api/practice/kana/storm-finish', json={
                'mode': 'storm', 'score': 500, 'correct': 30, 'misses': 0,
                'best_combo': 10,
            }).get_json()
            granted.append(d['xp_awarded'])
        assert sum(granted) == XP_STORM_DAILY_CAP
        assert db.session.get(User, user.id).total_xp == XP_STORM_DAILY_CAP
        assert granted[-1] == 0  # Runde ueber dem Cap -> keine XP mehr

    def test_daily_mode_persists_and_excluded_from_storm_stats(self, auth_client, db):
        client, user = auth_client
        resp = client.post('/api/practice/kana/storm-finish', json={
            'mode': 'daily', 'schrift': 'hiragana', 'daily_date': '2026-06-14',
            'score': 0, 'best_combo': 6, 'correct': 8, 'misses': 2,
        })
        assert resp.status_code == 200
        assert resp.get_json()['xp_awarded'] > 0          # 3 + min(8, 15) = 11
        row = KanaStormScore.query.filter_by(user_id=user.id, mode='daily').first()
        assert row is not None
        assert row.daily_date == date(2026, 6, 14)
        # Daily zaehlt NICHT ins Storm-Aggregat.
        assert get_kana_storm_stats(user.id)['games'] == 0

    def test_daily_date_fallback_on_bad_input(self, auth_client, db):
        client, user = auth_client
        for bad in ('not-a-date', ''):
            client.post('/api/practice/kana/storm-finish', json={
                'mode': 'daily', 'daily_date': bad, 'correct': 3,
            })
        rows = KanaStormScore.query.filter_by(user_id=user.id, mode='daily').all()
        assert len(rows) == 2
        assert all(r.daily_date == date.today() for r in rows)

    def test_does_not_pollute_review_aggregate(self, auth_client, db):
        client, user = auth_client
        client.post('/api/practice/kana/storm-finish', json={
            'mode': 'storm', 'score': 200, 'correct': 15, 'misses': 1,
            'best_combo': 9,
        })
        # Bewusste Trennung: Storm-Runden duerfen die review-semantischen
        # Zaehler (Heatmap/Accuracy) NICHT anfassen.
        assert DailyReviewAggregate.query.count() == 0


class TestGetKanaStormStats:
    """srs_service.get_kana_storm_stats — Aggregat (nur mode='storm')."""

    def test_aggregates_storm_only(self, app_context, db):
        user = UserFactory()
        db.session.commit()
        db.session.add_all([
            KanaStormScore(user_id=user.id, mode='storm', score=100,
                           best_combo=10, correct_count=20, miss_count=5,
                           duration=60),
            KanaStormScore(user_id=user.id, mode='storm', score=250,
                           best_combo=15, correct_count=30, miss_count=0,
                           duration=120),
            # Daily wird NICHT mitgezaehlt.
            KanaStormScore(user_id=user.id, mode='daily', score=0,
                           best_combo=8, correct_count=10, miss_count=0,
                           duration=60),
        ])
        db.session.commit()
        s = get_kana_storm_stats(user.id)
        assert s['games'] == 2
        assert s['best_score'] == 250
        assert s['best_combo'] == 15
        assert s['kana_typed'] == 55            # (20+5) + (30+0)
        assert s['accuracy'] == round(50 / 55 * 100)
        # KPM: 20/60*60 = 20 vs. 30/120*60 = 15 -> beste KPM = 20 (Daily zaehlt nicht).
        assert s['best_kpm'] == 20

    def test_best_kpm_duration_normalized(self, app_context, db):
        # KPM macht 60- und 120-Sek-Runden vergleichbar: die Runde mit dem
        # HOEHEREN rohen Score kann die NIEDRIGERE KPM haben.
        user = UserFactory()
        db.session.commit()
        db.session.add_all([
            # 30 richtige in 60s = 30 KPM
            KanaStormScore(user_id=user.id, mode='storm', score=300,
                           best_combo=10, correct_count=30, miss_count=0,
                           duration=60),
            # 40 richtige in 120s = 20 KPM (hoeherer Score, langsameres Tempo)
            KanaStormScore(user_id=user.id, mode='storm', score=500,
                           best_combo=12, correct_count=40, miss_count=0,
                           duration=120),
            # Alt-Runde ohne Dauer (duration=0) darf NICHT durch 0 teilen.
            KanaStormScore(user_id=user.id, mode='storm', score=80,
                           best_combo=4, correct_count=10, miss_count=0,
                           duration=0),
        ])
        db.session.commit()
        s = get_kana_storm_stats(user.id)
        assert s['best_score'] == 500           # roher Hoechstwert
        assert s['best_kpm'] == 30              # bestes Tempo (60-Sek-Runde)

    def test_empty(self, app_context, db):
        user = UserFactory()
        db.session.commit()
        assert get_kana_storm_stats(user.id) == {
            'games': 0, 'best_score': 0, 'best_combo': 0,
            'accuracy': 0, 'kana_typed': 0, 'best_kpm': 0,
        }


class TestStatsPageStormSection:
    """/review/stats zeigt die Storm-Sektion (server-gerendert) inkl. Swiss-Format."""

    def test_section_shown_with_swiss_format(self, auth_client, db):
        client, user = auth_client
        # Inhalt der Seite erscheint nur bei >= 1 SRS-Karte (else-Zweig).
        lesson = LessonFactory()
        content = LessonContentFactory(lesson_id=lesson.id)
        CardReviewStateFactory(user_id=user.id, content_id=content.id)
        db.session.add(KanaStormScore(
            user_id=user.id, mode='storm', score=1240,
            best_combo=24, correct_count=50, miss_count=4, duration=60,
        ))
        db.session.commit()
        body = client.get('/review/stats').get_data(as_text=True)
        assert 'Kana Storm' in body
        assert 'Bester Score' in body
        assert "1'240" in body                  # swiss_num-Filter angewandt
        # Vergleichbare Tempo-Kennzahl (Kana/min) als eigene Karte sichtbar.
        assert 'Schnellste' in body
        assert 'Kana/min' in body
        assert '>50<' in body                    # best_kpm = 50/60*60 = 50

    def test_section_shown_for_storm_only_player(self, auth_client, db):
        # Reiner Storm-Spieler OHNE SRS-Karten (total_cards==0) muss die
        # Storm-Sektion trotzdem sehen — sonst Sackgasse vom End-Screen-Link.
        client, user = auth_client
        db.session.add(KanaStormScore(
            user_id=user.id, mode='storm', score=80,
            best_combo=6, correct_count=12, miss_count=3,
        ))
        db.session.commit()
        resp = client.get('/review/stats')
        assert resp.status_code == 200
        # 'Kana Storm' steht NUR im else-Zweig -> beweist: kein Empty-State.
        assert 'Kana Storm' in resp.get_data(as_text=True)


class TestStormLoginGate:
    """Gemeldeter Bug: End-/Start-Screen forderte 'kostenlosem Konto' auch fuer
    bereits eingeloggte Nutzer. Jetzt per current_user.is_authenticated gegated."""

    def test_guest_sees_account_upsell(self, client, db):
        body = client.get('/practice/kana/storm').get_data(as_text=True)
        assert 'kostenlosem Konto' in body
        assert 'loggedIn: false' in body

    def test_logged_in_no_account_upsell(self, auth_client, db):
        client, _user = auth_client
        body = client.get('/practice/kana/storm').get_data(as_text=True)
        assert 'kostenlosem Konto' not in body
        assert 'loggedIn: true' in body
        assert 'Deine Storm-Statistik' in body
