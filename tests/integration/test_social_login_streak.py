"""Google-Login (social_auth_config._login_and_stamp) zaehlt als Aktivitaet —
wie der lokale Login seit eee6c23 (Streak fortschreiben + Stand fuer den
„Willkommen zurück"-Dialog in der Session merken)."""
from datetime import timedelta

from flask import session

from app.dashboard_service import LOGIN_STREAK_SESSION_KEY
from app.social_auth_config import _login_and_stamp
from app.time_utils import ch_today
from tests.factories import UserFactory


def test_google_login_verlaengert_streak(app, db):
    user = UserFactory(email='g1@test.com', current_streak=3, longest_streak=3)
    user.last_activity_date = ch_today() - timedelta(days=1)
    user.last_login = None
    db.session.commit()

    with app.test_request_context('/auth/complete/google-oauth2/'):
        _login_and_stamp(user)
        info = session.get(LOGIN_STREAK_SESSION_KEY)

    db.session.refresh(user)
    assert user.current_streak == 4
    assert user.last_activity_date == ch_today()
    assert user.last_login is not None
    assert info['event'] == 'extended'
    assert info['prev_streak'] == 3
    assert info['day'] == ch_today().isoformat()


def test_google_login_heute_schon_aktiv_aendert_nichts(app, db):
    user = UserFactory(email='g2@test.com', current_streak=5, longest_streak=5)
    user.last_activity_date = ch_today()
    db.session.commit()

    with app.test_request_context('/auth/complete/google-oauth2/'):
        _login_and_stamp(user)
        info = session.get(LOGIN_STREAK_SESSION_KEY)

    db.session.refresh(user)
    assert user.current_streak == 5
    assert info['event'] is None
