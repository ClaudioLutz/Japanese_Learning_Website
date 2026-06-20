"""Tests fuer die FREE_MODE-Schicht ("alles gratis", reversibel).

FREE_MODE ist per Default AUS (app/__init__.py) — die uebrige Suite exerziert
damit weiter den monetarisierten Pfad. Diese Tests schalten das Flag gezielt pro
Test ein und setzen es danach zurueck.
"""
import pytest
from flask_login import AnonymousUserMixin

from app.services.bundle_service import user_needs_bundle_hint
from tests.factories import CourseFactory


@pytest.fixture
def free_mode(app):
    """Aktiviert FREE_MODE fuer die Dauer eines Tests und setzt es zurueck."""
    prev = app.config.get("FREE_MODE", False)
    app.config["FREE_MODE"] = True
    yield
    app.config["FREE_MODE"] = prev


def test_free_mode_default_off(app):
    # Sicherheitsnetz: ohne Env-Override muss das Flag AUS sein, sonst brechen
    # die monetarisierten Tests (Paywall/Bundle-Hint).
    assert app.config.get("FREE_MODE") is False


def test_bundle_hint_off_in_free_mode(app, free_mode):
    with app.test_request_context():
        assert user_needs_bundle_hint(AnonymousUserMixin()) is False


def test_bundle_hint_on_for_guest_when_not_free_mode(app, db):
    with app.test_request_context():
        assert user_needs_bundle_hint(AnonymousUserMixin()) is True


def test_n5_bundle_page_redirects_in_free_mode(client, free_mode):
    resp = client.get("/n5-bundle")
    assert resp.status_code in (301, 302)
    assert "/lessons" in resp.headers.get("Location", "")


def test_bundle_purchase_blocked_in_free_mode(auth_client, app, free_mode):
    client, _user = auth_client
    resp = client.post("/api/bundles/n5/purchase", json={"accepted_terms": True})
    assert resp.status_code == 410
    assert resp.get_json()["error_type"] == "FREE_MODE"


def test_course_price_zero_but_purchasable_still_paywalls(client, db):
    # Regression: die Kurs-Paywall haengt an is_purchasable, NICHT am Preis.
    # price=0 allein gibt einen Kurs NICHT frei -> die Nullung MUSS
    # is_purchasable=False mitsetzen (sonst halb-entfernte Paywall).
    course = CourseFactory(price=0.0, is_purchasable=True, is_published=True)
    db.session.commit()
    resp = client.get(f"/course/{course.id}")
    assert resp.status_code == 200
    assert "Kurs kaufen" in resp.get_data(as_text=True)


def test_course_not_purchasable_has_no_paywall(client, db):
    course = CourseFactory(price=0.0, is_purchasable=False, is_published=True)
    db.session.commit()
    resp = client.get(f"/course/{course.id}")
    assert resp.status_code == 200
    assert "Kurs kaufen" not in resp.get_data(as_text=True)
