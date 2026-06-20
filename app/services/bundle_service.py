"""Bundle-Service: dynamische Preis-Logik + Course-Lookup fuer das N5-Bundle.

Das Bundle ist ein Course namens "JLPT N5 Komplett", angelegt via
scripts/setup_n5_bundle.py. Zugriffslogik laeuft ueber das bestehende
CoursePurchase-System (Lesson.is_accessible_to_user).

Preis ist dynamisch: Early-Bird CHF 9.90 solange Vokabel-Coverage < 80%,
danach Regulaerer Preis CHF 14.90. Threshold ist bewusst auf Vokabeln (nicht
Kanji), damit der Wechsel passiert wenn das Bundle substantiell gefuellt ist —
Kanji haben weniger Items absolut, sind aber trotzdem essenziell.
"""
from __future__ import annotations

from app import db
from app.models import Course
from app.services.coverage_service import get_jlpt_coverage


N5_BUNDLE_TITLE = "JLPT N5 Komplett"

EARLY_BIRD_PRICE_CHF = 9.90
REGULAR_PRICE_CHF = 14.90
EARLY_BIRD_THRESHOLD_PCT = 80.0  # ab Vokabel-Coverage >= 80% faellt Early-Bird

# Einzel-Lesson-Preis: bewusst niedrig gehalten, damit das Bundle sofort als
# No-Brainer wirkt — wer 2+ Lessons kaufen will, hat das Bundle (CHF 9.90)
# ohnehin guenstiger als 2 Einzelkaeufe (2x CHF 5 = CHF 10).
SINGLE_LESSON_PRICE_CHF = 5.00


def get_n5_bundle_price() -> tuple[float, str]:
    """Liefert (price_chf, label) wo label in {'early_bird', 'regular'}.

    Wechsel passiert anhand der Vokabel-Coverage. Wirft FileNotFoundError
    durch, wenn die canonical Liste fehlt.
    """
    coverage = get_jlpt_coverage(5)
    if coverage["vocab_pct"] < EARLY_BIRD_THRESHOLD_PCT:
        return EARLY_BIRD_PRICE_CHF, "early_bird"
    return REGULAR_PRICE_CHF, "regular"


def get_n5_bundle_course() -> Course | None:
    """Findet den Bundle-Course per Title. None wenn Setup-Skript noch nicht lief."""
    return db.session.query(Course).filter_by(title=N5_BUNDLE_TITLE).first()


def user_needs_bundle_hint(user) -> bool:
    """True, wenn dem User Bundle-Werbung gezeigt werden soll.

    False fuer Admins (sehen ohnehin alles frei) und fuer User, die das
    Bundle bereits gekauft haben — sonst penetriert der Hint Kaeufer mit
    "Tipp: kauf das Bundle". Gaeste und alle anderen: True.

    Single Source of Truth fuer Navbar (Context-Processor in __init__.py),
    Startseiten-Banner und /learn/n5 — vorher duplizierte Logik in routes.py.

    FREE_MODE: Ist die Plattform auf "alles gratis" geschaltet, gibt es kein
    Bundle zu bewerben — hart False (Single Source, schaltet Navbar/Startseite/
    /lessons/module_detail in einem Zug ab).
    """
    from flask import current_app
    if current_app.config.get("FREE_MODE"):
        return False
    if not getattr(user, "is_authenticated", False):
        return True
    if getattr(user, "is_admin", False):
        return False
    bundle = get_n5_bundle_course()
    if bundle is None:
        return True
    from app.models import CoursePurchase
    already = CoursePurchase.query.filter_by(
        user_id=user.id, course_id=bundle.id
    ).first()
    return already is None
