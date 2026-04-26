"""Integration-Tests fuer /n5-bundle Verkaufsseite + Buy-API."""

from unittest.mock import patch

from app import db
from app.models import Course, CoursePurchase
from app.services.bundle_service import N5_BUNDLE_TITLE


def _make_bundle_course():
    course = Course(
        title=N5_BUNDLE_TITLE, description="Test-Bundle",
        is_published=False, is_purchasable=True, price=14.90,
    )
    db.session.add(course)
    db.session.commit()
    return course


def _coverage(vocab_pct=33.0, lessons=10, recent=2):
    return {
        "level": 5,
        "vocab_total": 710, "vocab_covered": int(710 * vocab_pct / 100),
        "vocab_pct": vocab_pct,
        "kanji_total": 80, "kanji_covered": 2, "kanji_pct": 2.5,
        "lessons_published_total": lessons,
        "lessons_published_recent_7d": recent,
        "updated_at": None,
    }


def test_get_bundle_page_anonymous_renders_with_coverage(client):
    """Anon-User sieht Verkaufsseite mit Coverage und Early-Bird-Preis."""
    _make_bundle_course()
    with patch("app.bundle_routes.get_jlpt_coverage", return_value=_coverage(33.0)):
        resp = client.get("/n5-bundle")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "JLPT N5 Komplett" in body
    assert "33" in body  # Coverage-Wert
    assert "9.90" in body  # Early-Bird-Preis
    assert "Kostenlos registrieren" in body  # Anon-CTA


def test_get_bundle_page_when_bundle_not_configured(client):
    """Ohne Setup-Course-Eintrag zeigt die Seite den 'in Vorbereitung'-Hinweis."""
    with patch("app.bundle_routes.get_jlpt_coverage", return_value=_coverage(33.0)):
        resp = client.get("/n5-bundle")
    assert resp.status_code == 200
    assert "wird gerade vorbereitet" in resp.get_data(as_text=True)


def test_get_bundle_page_already_owned(auth_client):
    """Eingeloggter User mit CoursePurchase sieht 'bereits gekauft'-Banner."""
    client, user = auth_client
    course = _make_bundle_course()
    db.session.add(CoursePurchase(
        user_id=user.id, course_id=course.id, price_paid=9.90,
        provider_transaction_id=12345, transaction_state="COMPLETED",
    ))
    db.session.commit()

    with patch("app.bundle_routes.get_jlpt_coverage", return_value=_coverage(33.0)):
        resp = client.get("/n5-bundle")
    assert resp.status_code == 200
    assert "Du besitzt das Bundle bereits" in resp.get_data(as_text=True)


def test_purchase_requires_accepted_terms(auth_client):
    """POST ohne accepted_terms wird mit 400 abgewiesen."""
    client, _ = auth_client
    _make_bundle_course()
    resp = client.post("/api/bundles/n5/purchase", json={})
    assert resp.status_code == 400
    assert resp.get_json()["error_type"] == "TERMS_NOT_ACCEPTED"


def test_purchase_returns_503_when_bundle_missing(auth_client):
    """Ohne Bundle-Course liefert die API 503."""
    client, _ = auth_client
    resp = client.post(
        "/api/bundles/n5/purchase",
        json={"accepted_terms": True},
    )
    assert resp.status_code == 503
    assert resp.get_json()["error_type"] == "BUNDLE_NOT_CONFIGURED"


def test_purchase_blocks_double_purchase(auth_client):
    """Doppelkauf liefert 400."""
    client, user = auth_client
    course = _make_bundle_course()
    db.session.add(CoursePurchase(
        user_id=user.id, course_id=course.id, price_paid=9.90,
        provider_transaction_id=99999, transaction_state="COMPLETED",
    ))
    db.session.commit()

    resp = client.post(
        "/api/bundles/n5/purchase",
        json={"accepted_terms": True},
    )
    assert resp.status_code == 400
    assert "bereits" in resp.get_json()["error"].lower()


def test_purchase_happy_path_with_mock_provider(auth_client):
    """Erfolgreiche Buy-Initiierung mit MockPayment liefert payment_url."""
    client, _ = auth_client
    _make_bundle_course()

    with patch(
        "app.bundle_routes.get_n5_bundle_price",
        return_value=(9.90, "early_bird"),
    ):
        resp = client.post(
            "/api/bundles/n5/purchase",
            json={"accepted_terms": True},
        )
    assert resp.status_code == 201, resp.get_data(as_text=True)
    data = resp.get_json()
    assert data["success"] is True
    assert data["amount"] == 9.90
    assert data["price_label"] == "early_bird"
    assert data["currency"] == "CHF"
    assert "payment_url" in data
