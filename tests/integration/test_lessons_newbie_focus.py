# tests/integration/test_lessons_newbie_focus.py
"""/lessons fuer Neulinge: bei hoechstens EINER abgeschlossenen Lektion ist nur
das Modul mit der naechsten Lektion aufgeklappt (Rest eingeklappt, aber
vollstaendig im HTML). Ab 2 fertigen Lektionen und fuer Gaeste gilt die
bisherige Heuristik unveraendert."""
import re
from datetime import datetime, timedelta

from app import db
from app.routes import NEWBIE_FOCUS_MAX_DONE
from tests.factories import (
    LessonCategoryFactory,
    LessonFactory,
    UserLessonProgressFactory,
)

_OPEN_RE = re.compile(r'data-cat-id="(\d+)"\s+data-open-default="([01])"')


def _catalog():
    """3 Module a 2 deutsche Lektionen, in Lehrplan-Reihenfolge."""
    cats, lessons = [], []
    for i in range(3):
        cat = LessonCategoryFactory(name=f'Modul {i}', display_order=i)
        db.session.flush()
        cats.append(cat)
        for j in range(2):
            lessons.append(LessonFactory(category_id=cat.id, instruction_language='german',
                                         is_published=True, order_index=i * 10 + j,
                                         title=f'L{i}{j}'))
    db.session.flush()
    return cats, lessons


def _progress(user, lesson, done=False, minutes_ago=0):
    UserLessonProgressFactory(
        user_id=user.id, lesson_id=lesson.id, is_completed=done,
        progress_percentage=100 if done else 40,
        last_accessed=datetime.utcnow() - timedelta(minutes=minutes_ago),
    )


def _open_cats(html):
    return {int(cid) for cid, flag in _OPEN_RE.findall(html) if flag == '1'}


def _all_cats(html):
    return {int(cid) for cid, _ in _OPEN_RE.findall(html)}


def test_threshold_is_one():
    assert NEWBIE_FOCUS_MAX_DONE == 1


def test_zero_done_only_next_module_open(auth_client):
    client, user = auth_client
    cats, lessons = _catalog()
    # Zuletzt in Modul 2 gestoebert, frueher Modul 0 begonnen → naechste = Modul 2
    _progress(user, lessons[0], minutes_ago=60)
    _progress(user, lessons[4], minutes_ago=1)
    db.session.commit()
    html = client.get('/lessons').get_data(as_text=True)
    assert _open_cats(html) == {cats[2].id}
    assert 'data-newbie-focus="1"' in html
    assert f'data-focus-cat="{cats[2].id}"' in html
    # SEO/SSR: alle Module + Lektionen stehen trotzdem im HTML
    assert _all_cats(html) == {c.id for c in cats}
    for lsn in lessons:
        assert f'/lessons/{lsn.id}"' in html
    assert 'Alle 3 Module anzeigen' in html


def test_fresh_account_opens_first_module(auth_client):
    client, _user = auth_client
    cats, _lessons = _catalog()
    db.session.commit()
    html = client.get('/lessons').get_data(as_text=True)
    assert _open_cats(html) == {cats[0].id}


def test_one_done_still_newbie(auth_client):
    client, user = auth_client
    cats, lessons = _catalog()
    _progress(user, lessons[2], done=True, minutes_ago=120)   # Modul 1 teilweise fertig
    _progress(user, lessons[0], minutes_ago=5)                 # Modul 0 begonnen
    db.session.commit()
    html = client.get('/lessons').get_data(as_text=True)
    # Alte Heuristik haette Modul 0 UND Modul 1 (teilweise) geoeffnet.
    assert _open_cats(html) == {cats[0].id}
    assert 'data-newbie-focus="1"' in html


def test_two_done_keeps_old_heuristic(auth_client):
    client, user = auth_client
    cats, lessons = _catalog()
    _progress(user, lessons[2], done=True, minutes_ago=200)   # Modul 1 teilweise
    _progress(user, lessons[4], done=True, minutes_ago=100)   # Modul 2 teilweise
    _progress(user, lessons[0], minutes_ago=5)                 # Modul 0 begonnen
    db.session.commit()
    html = client.get('/lessons').get_data(as_text=True)
    assert _open_cats(html) == {c.id for c in cats}
    assert 'data-newbie-focus' not in html
    assert 'Module anzeigen' not in html


def test_guest_view_unchanged(client):
    cats, _lessons = _catalog()
    db.session.commit()
    html = client.get('/lessons').get_data(as_text=True)
    assert 'data-newbie-focus' not in html
    assert _open_cats(html) == {cats[0].id, cats[1].id}
