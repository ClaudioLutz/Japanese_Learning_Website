"""Integration-Tests: Gast sieht Preis + Garantie auf Paywall und Bundle (Task B1).

Belegt, dass der Wert (Preis, Geld-zurück-Garantie, Payment-Signale) NICHT mehr
hinter dem Login versteckt ist, sondern auch ausgeloggten Besuchern angezeigt wird.
"""

from unittest.mock import patch

from app import db
from app.models import Course
from app.services.bundle_service import N5_BUNDLE_TITLE
from tests.factories import LessonFactory, PaidLessonFactory


def _coverage(vocab_pct=33.0, lessons=10, recent=2):
    """Deterministisches Coverage-Dict (analog test_bundle_routes.py)."""
    return {
        "level": 5,
        "vocab_total": 710, "vocab_covered": int(710 * vocab_pct / 100),
        "vocab_pct": vocab_pct,
        "kanji_total": 80, "kanji_covered": 2, "kanji_pct": 2.5,
        "lessons_published_total": lessons,
        "lessons_published_recent_7d": recent,
        "updated_at": None,
    }


def test_guest_paywall_shows_price_and_guarantee(client, app_context):
    """Gast (nicht eingeloggt) auf einer bezahlten Lektion sieht Preis + Garantie.

    Vorher steckte der gesamte Wert im is_authenticated-Zweig; ein Gast sah nur
    'brauchst ein kostenloses Konto'. Jetzt: Wert zuerst, Login zuletzt.
    """
    lesson = PaidLessonFactory(is_published=True, price=5.0, is_purchasable=True)
    db.session.commit()

    # Preis-Lookup deterministisch halten (kein DB-/Datei-Abhaengigkeit)
    with patch(
        "app.services.bundle_service.get_n5_bundle_price",
        return_value=(9.90, "early_bird"),
    ):
        resp = client.get(f"/lessons/{lesson.id}")

    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    # Preis sichtbar (Bundle- und Einzelpreis)
    assert "CHF" in body
    assert "9.90" in body          # Bundle-Preis
    assert "5.00" in body          # Einzel-Lesson-Preis
    # Garantie sichtbar
    assert "Geld zurück" in body
    # CTA zum kostenlosen Konto bleibt vorhanden
    assert "Kostenlos registrieren" in body


def test_guest_bundle_page_shows_price(client):
    """Gast auf /n5-bundle sieht Preis + Payment-/Garantie-Signale."""
    course = Course(
        title=N5_BUNDLE_TITLE, description="Test-Bundle",
        is_published=False, is_purchasable=True, price=14.90,
    )
    db.session.add(course)
    db.session.commit()

    with patch("app.bundle_routes.get_jlpt_coverage", return_value=_coverage(33.0)):
        resp = client.get("/n5-bundle")

    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    # Preis sichtbar fuer Gast
    assert "9.90" in body
    # Payment-/Garantie-Signale auch fuer Gast (B1: aus is_authenticated geloest)
    assert "Geld zurück" in body
    assert "Payrexx" in body


def test_guest_login_required_lesson_redirects_to_login(client, app_context):
    """10.4/10.5 E2E: Gast auf einer login-pflichtigen (gratis, NICHT gast-
    zugaenglichen) Lektion wird auf /login?next=... umgeleitet — NICHT Paywall.

    Sichert die reason-basierte Verzweigung end-to-end ab: access.reason ==
    LOGIN_REQUIRED -> Login-Redirect. Mit dem frueheren fragilen Substring-Match
    auf 'Login required' (jetzt deutsch) wuerde diese Verzweigung still brechen.
    """
    lesson = LessonFactory(
        is_published=True, allow_guest_access=False, price=0.0,
        is_purchasable=False,
    )
    db.session.commit()

    resp = client.get(f"/lessons/{lesson.id}", follow_redirects=False)

    assert resp.status_code == 302
    location = resp.headers["Location"]
    assert "/login" in location
    assert "next=" in location


def test_guest_paid_lesson_shows_paywall_not_login(client, app_context):
    """10.4/10.5 E2E: Gast auf einer bezahlten Lektion sieht die Paywall (200),
    NICHT den Login-Redirect — die paid-Verzweigung kommt VOR LOGIN_REQUIRED.
    """
    lesson = PaidLessonFactory(is_published=True, price=5.0, is_purchasable=True)
    db.session.commit()

    with patch(
        "app.services.bundle_service.get_n5_bundle_price",
        return_value=(9.90, "early_bird"),
    ):
        resp = client.get(f"/lessons/{lesson.id}", follow_redirects=False)

    assert resp.status_code == 200
    # Kein Login-Redirect (200 hat keinen Location-Header; defensiv geprueft)
    assert "/login" not in (resp.headers.get("Location") or "")
