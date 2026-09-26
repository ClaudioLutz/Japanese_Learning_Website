"""🔥-Badge in der Navigation zeigt den EFFEKTIVEN Streak.

current_streak wird erst bei der naechsten Aktivitaet verbucht. Liegt der letzte
Aktivitaetstag vor gestern und deckt kein Freeze die Luecke, ist der Streak
faktisch gerissen -> Badge weg. Freeze-gedeckt -> Badge bleibt. Ein GET schreibt
dabei nichts. Ausserdem: jQuery wird nicht mehr global geladen.
"""
from datetime import timedelta

from app import db
from app.dashboard_service import effective_streak
from app.models import User, UserSRSSettings
from app.time_utils import ch_today

_BADGE = 'topnav-stat-streak'


def _set(user, days_ago, streak, freezes=None, replenished_days_ago=0):
    user.last_activity_date = ch_today() - timedelta(days=days_ago)
    user.current_streak = streak
    if freezes is not None:
        db.session.add(UserSRSSettings(
            user_id=user.id, streak_freezes_available=freezes,
            last_freeze_replenish=ch_today() - timedelta(days=replenished_days_ago),
        ))
    db.session.commit()


def _badge_value(html):
    if _BADGE not in html:
        return None
    block = html[html.index(_BADGE):]
    start = block.index('topnav-stat-val')
    seg = block[start:block.index('</span>', start)]
    return int(seg.rsplit('>', 1)[1])


def test_active_yesterday_shows_streak(auth_client):
    client, user = auth_client
    _set(user, 1, 6)
    assert _badge_value(client.get('/lessons').get_data(as_text=True)) == 6


def test_broken_unbooked_streak_hides_badge_without_writing(auth_client):
    client, user = auth_client
    _set(user, 3, 9)
    html = client.get('/lessons').get_data(as_text=True)
    assert _badge_value(html) is None
    db.session.expire_all()
    fresh = db.session.get(User, user.id)
    assert fresh.current_streak == 9          # GET verbucht nichts
    assert fresh.last_activity_date == ch_today() - timedelta(days=3)


def test_missed_one_day_without_freeze_hides_badge(auth_client):
    client, user = auth_client
    # Freeze verbraucht, Nachfuellung erst in 5 Tagen
    _set(user, 2, 4, freezes=0, replenished_days_ago=2)
    assert _badge_value(client.get('/lessons').get_data(as_text=True)) is None


def test_missed_one_day_with_freeze_keeps_badge(auth_client):
    client, user = auth_client
    _set(user, 2, 4, freezes=1)
    assert _badge_value(client.get('/lessons').get_data(as_text=True)) == 4


def test_active_today_shows_streak(auth_client):
    client, user = auth_client
    _set(user, 0, 3)
    assert _badge_value(client.get('/lessons').get_data(as_text=True)) == 3


def test_effective_streak_guest_is_zero(app_context):
    from flask_login import AnonymousUserMixin
    assert effective_streak(AnonymousUserMixin()) == 0
    assert effective_streak(None) == 0


def test_jquery_not_loaded_globally(client):
    html = client.get('/').get_data(as_text=True)
    assert 'jquery' not in html.lower()
