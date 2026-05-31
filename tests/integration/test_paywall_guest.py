"""Integration-Tests: Gast sieht Preis + Garantie auf Paywall und Bundle (Task B1).

Belegt, dass der Wert (Preis, Geld-zurück-Garantie, Payment-Signale) NICHT mehr
hinter dem Login versteckt ist, sondern auch ausgeloggten Besuchern angezeigt wird.
"""

from unittest.mock import patch

from app import db
from app.models import Course
from app.services.bundle_service import N5_BUNDLE_TITLE
from tests.factories import PaidLessonFactory


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
