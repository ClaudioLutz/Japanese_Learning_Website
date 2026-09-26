# tests/integration/test_roleplay_panel_ui.py
"""Lektionsseite: Rollenspiel-Panel am Dialog nur mit roleplay_enabled + Login.

Das Panel (partials/_roleplay_panel.html) haengt ausschliesslich am
dialog_slideshow-Zweig; JS/CSS werden nur dann eingebunden.
"""
import json

import pytest

from app import db
from app.models import LessonContent
from tests.factories import LessonFactory, UserFactory

DIALOG = {"slides": [
    {"speaker": "Kellner", "jp": "いらっしゃいませ。", "de": "Willkommen.", "romaji": "irasshaimase"},
    {"speaker": "Gast", "jp": "コーヒーを ください。", "de": "Einen Kaffee, bitte.", "romaji": "koohii o kudasai"},
]}


@pytest.fixture
def roleplay_on(app, monkeypatch):
    monkeypatch.setitem(app.config, "ROLEPLAY_ENABLED", True)
    monkeypatch.setitem(app.config, "ROLEPLAY_PROVIDER", "bridge")
    monkeypatch.setitem(app.config, "ROLEPLAY_BRIDGE_URL", "http://bridge.test:5077")
    monkeypatch.setenv("ROLEPLAY_BRIDGE_TOKEN", "test-token")
    return app


def _lesson_with(contents):
    lesson = LessonFactory(is_published=True, price=0.0, allow_guest_access=True)
    db.session.flush()
    ids = []
    for idx, (page, kwargs) in enumerate(contents):
        c = LessonContent(lesson_id=lesson.id, order_index=idx, page_number=page, **kwargs)
        db.session.add(c)
        db.session.flush()
        ids.append(c.id)
    db.session.commit()
    return lesson, ids


def _dialog(page=2):
    return (page, {"content_type": "dialog_slideshow", "title": "Im Café", "content_text": json.dumps(DIALOG)})


def _logged_in(app):
    user = UserFactory()
    db.session.commit()
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)
        sess["_fresh"] = True
    return client


def _get(client, lesson_id):
    resp = client.get(f"/lessons/{lesson_id}")
    assert resp.status_code == 200
    return resp.get_data(as_text=True)


def test_panel_rendered_when_enabled_and_logged_in(app, db, roleplay_on):
    with app.app_context():
        lesson, ids = _lesson_with([(1, {"content_type": "text", "title": "T", "content_text": "<p>x</p>"}), _dialog(2)])
        html = _get(_logged_in(app), lesson.id)
    assert f'x-data="roleplayPanel({ids[1]})"' in html
    assert "Rollenspiel starten" in html
    assert "js/romaji_to_kana.js?v=" in html
    assert "js/roleplay_panel.js?v=" in html
    assert "css/roleplay_panel.css?v=" in html
    assert f'data-lesson-id="{lesson.id}"' in html
    assert 'data-page-number="2"' in html
    assert "data-page-numbers='[1, 2]'" in html
    # Slideshow-Player bleibt unveraendert daneben
    assert f'x-data="dialogSlideshow({ids[1]})"' in html
    # Skripte synchron (nicht defer) und vor Alpine-Init verfuegbar
    assert '<script defer src="/static/js/roleplay_panel.js' not in html


def test_panel_suggestion_tools_markup(app, db, roleplay_on):
    """Vorschlags-Chips: Vorlesen, DE, Sofort-Senden (Klick gestoppt), Schalter „Deutsch anzeigen"."""
    with app.app_context():
        lesson, _ = _lesson_with([_dialog(1)])
        html = _get(_logged_in(app), lesson.id)
    assert 'aria-label="Vorschlag vorlesen"' in html
    assert "speak(s.jp, 's' + i, userGender)" in html
    assert '@click.stop="sendSuggestion(s)"' in html
    assert 'aria-label="Vorschlag sofort senden"' in html
    assert '@click.stop="toggleChipGerman(i)"' in html
    assert 'x-show="chipGermanVisible(i)"' in html
    assert "Deutsch anzeigen" in html
    assert 'aria-label="Besseren Satz vorlesen"' in html
    assert 'x-show="showTyping"' in html


def test_panel_hidden_when_disabled(app, db, monkeypatch):
    monkeypatch.setitem(app.config, "ROLEPLAY_ENABLED", False)
    with app.app_context():
        lesson, ids = _lesson_with([_dialog(1)])
        html = _get(_logged_in(app), lesson.id)
    assert f'x-data="dialogSlideshow({ids[0]})"' in html
    assert "roleplayPanel(" not in html
    assert "Rollenspiel starten" not in html
    assert "roleplay_panel.js" not in html
    assert "roleplay_panel.css" not in html


def test_panel_hidden_for_guests(app, db, roleplay_on):
    with app.app_context():
        lesson, _ = _lesson_with([_dialog(1)])
        html = _get(app.test_client(), lesson.id)
    assert "roleplayPanel(" not in html
    assert "roleplay_panel.js" not in html


def test_panel_only_at_dialog(app, db, roleplay_on):
    """Ohne dialog_slideshow kein Panel (Assets duerfen geladen sein, Knopf nicht)."""
    with app.app_context():
        lesson, _ = _lesson_with([(1, {"content_type": "text", "title": "T", "content_text": "<p>x</p>"})])
        html = _get(_logged_in(app), lesson.id)
    assert "roleplayPanel(" not in html
    assert "Rollenspiel starten" not in html
