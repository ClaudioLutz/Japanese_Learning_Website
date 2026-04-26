"""Tests fuer Bundle-Service: dynamische Preis-Logik + Course-Lookup."""

from unittest.mock import patch

import pytest

from app.services.bundle_service import (
    EARLY_BIRD_PRICE_CHF,
    EARLY_BIRD_THRESHOLD_PCT,
    N5_BUNDLE_TITLE,
    REGULAR_PRICE_CHF,
    get_n5_bundle_course,
    get_n5_bundle_price,
)


def _coverage_stub(vocab_pct: float) -> dict:
    return {
        "level": 5,
        "vocab_total": 710,
        "vocab_covered": int(710 * vocab_pct / 100),
        "vocab_pct": vocab_pct,
        "kanji_total": 80,
        "kanji_covered": 0,
        "kanji_pct": 0.0,
        "lessons_published_total": 0,
        "lessons_published_recent_7d": 0,
        "updated_at": None,
    }


@pytest.mark.parametrize(
    "vocab_pct,expected_price,expected_label",
    [
        (0.0, EARLY_BIRD_PRICE_CHF, "early_bird"),
        (33.0, EARLY_BIRD_PRICE_CHF, "early_bird"),
        (79.9, EARLY_BIRD_PRICE_CHF, "early_bird"),
        (EARLY_BIRD_THRESHOLD_PCT, REGULAR_PRICE_CHF, "regular"),
        (95.0, REGULAR_PRICE_CHF, "regular"),
        (100.0, REGULAR_PRICE_CHF, "regular"),
    ],
)
def test_price_threshold(app_context, vocab_pct, expected_price, expected_label):
    """Early-Bird gilt unter Threshold, Regulaer ab Threshold (inklusiv)."""
    with patch(
        "app.services.bundle_service.get_jlpt_coverage",
        return_value=_coverage_stub(vocab_pct),
    ):
        price, label = get_n5_bundle_price()
    assert price == expected_price
    assert label == expected_label


def test_get_bundle_course_returns_none_when_missing(app_context):
    """Wenn setup_n5_bundle.py noch nicht lief, ist der Course None."""
    assert get_n5_bundle_course() is None


def test_get_bundle_course_finds_existing(app_context):
    """Existierender Course wird per Title gefunden."""
    from app import db
    from app.models import Course

    course = Course(title=N5_BUNDLE_TITLE, description="x", is_published=False,
                    is_purchasable=True, price=14.90)
    db.session.add(course)
    db.session.commit()

    found = get_n5_bundle_course()
    assert found is not None
    assert found.id == course.id
    assert found.title == N5_BUNDLE_TITLE
