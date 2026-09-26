"""Tests fuer „JLPT N5 komplett": Kennzahlen (coverage_service), Startseiten-Leiste,
/n5-bundle in beiden Modi (FREE_MODE an/aus), Sitemap und Nav-Link.
"""
from unittest.mock import patch

import pytest

from app.services.coverage_service import _load_canonical, get_level_showcase
from tests.factories import (
    KanjiFactory,
    LessonCategoryFactory,
    LessonContentFactory,
    LessonFactory,
    QuizQuestionFactory,
    VocabularyFactory,
)


@pytest.fixture
def free_mode(app):
    prev = app.config.get("FREE_MODE", False)
    app.config["FREE_MODE"] = True
    yield
    app.config["FREE_MODE"] = prev


@pytest.fixture
def n5_data(db):
    """Zwei publizierte N5-Lektionen (2 Module) + eine unpublizierte, die nicht zaehlt."""
    cat_a = LessonCategoryFactory(jlpt_level=5)
    cat_b = LessonCategoryFactory(jlpt_level=5)
    lesson_a = LessonFactory(category_id=None, is_published=True)
    lesson_b = LessonFactory(category_id=None, is_published=True)
    hidden = LessonFactory(category_id=None, is_published=False)
    db.session.flush()
    lesson_a.category_id = cat_a.id
    lesson_b.category_id = cat_b.id
    hidden.category_id = cat_a.id

    v1, v2, v3 = VocabularyFactory(), VocabularyFactory(), VocabularyFactory()
    k_friend = KanjiFactory(character="友")
    k_big = KanjiFactory(character="大")
    db.session.flush()

    for lesson, vocab in ((lesson_a, v1), (lesson_a, v2), (lesson_b, v2)):
        LessonContentFactory(lesson_id=lesson.id, content_type="vocabulary", content_id=vocab.id)
    LessonContentFactory(lesson_id=hidden.id, content_type="vocabulary", content_id=v3.id)
    LessonContentFactory(lesson_id=lesson_a.id, content_type="kanji", content_id=k_friend.id)
    LessonContentFactory(lesson_id=lesson_b.id, content_type="kanji", content_id=k_big.id)
    LessonContentFactory(lesson_id=lesson_a.id, content_type="dialog_slideshow", content_text="{}")
    LessonContentFactory(lesson_id=lesson_b.id, content_type="dialog_slideshow", content_text="{}")
    LessonContentFactory(lesson_id=hidden.id, content_type="dialog_slideshow", content_text="{}")
    quiz = LessonContentFactory(lesson_id=lesson_a.id, content_type="quiz")
    db.session.flush()
    QuizQuestionFactory(lesson_content_id=quiz.id)
    QuizQuestionFactory(lesson_content_id=quiz.id)
    db.session.commit()
    return {"lessons": 2, "modules": 2, "vocab": 2, "kanji": 2, "scenes": 2, "quiz": 2}


class TestShowcase:
    def test_counts_only_published_level_lessons(self, app, n5_data):
        with app.app_context():
            s = get_level_showcase(5)
        assert s["lessons"] == n5_data["lessons"]
        assert s["modules"] == n5_data["modules"]
        assert s["vocab"] == n5_data["vocab"]          # distinct, ohne unpublizierte
        assert s["scenes"] == n5_data["scenes"]
        assert s["quiz_questions"] == n5_data["quiz"]
        assert s["kanji"] == n5_data["kanji"]          # canonical-Kanji in der DB
        assert s["kanji_total"] == 80

    def test_canonical_splits_variants_and_loads_aliases(self):
        canon = _load_canonical(5)
        assert not any(";" in w for w in canon["vocab_set"])
        assert {"足", "脚"} <= canon["vocab_set"]
        assert canon["aliases"].get("脚") == "足"


class TestHomepageBar:
    def test_guest_sees_n5_complete_bar_with_live_numbers(self, client, n5_data):
        body = client.get("/").get_data(as_text=True)
        assert 'class="n5-complete-bar"' in body
        assert "JLPT N5 ist komplett" in body
        assert "<b>2</b> Lektionen" in body
        assert "<b>2</b> Vokabeln" in body
        assert "<b>alle 2</b> N5-Kanji" in body
        assert "<b>2</b> Gesprächsszenen" in body
        assert 'href="/n5-bundle"' in body

    def test_meta_description_mentions_n5_komplett(self, client, db):
        body = client.get("/").get_data(as_text=True)
        assert 'name="description" content="JLPT N5 komplett' in body

    def test_logged_in_has_no_guest_bar(self, auth_client, n5_data):
        client, _ = auth_client
        body = client.get("/").get_data(as_text=True)
        assert 'class="n5-complete-bar"' not in body

    def test_bar_hidden_when_showcase_fails(self, client, db):
        with patch("app.services.coverage_service.get_level_showcase", side_effect=RuntimeError):
            resp = client.get("/")
        assert resp.status_code == 200
        assert 'class="n5-complete-bar"' not in resp.get_data(as_text=True)


class TestBundlePageModes:
    def test_free_mode_renders_complete_page(self, client, free_mode, n5_data):
        resp = client.get("/n5-bundle")
        assert resp.status_code == 200
        body = resp.get_data(as_text=True)
        assert "JLPT N5 komplett." in body
        assert "<title>JLPT N5 komplett auf Deutsch, gratis" in body
        assert 'content="JLPT N5 komplett auf Deutsch, gratis' in body
        assert 'class="bnd-stats"' in body
        assert "Kostenlos starten" in body
        # keine Bezahl-Schicht im FREE_MODE
        assert "CHF" not in body
        assert "buyBtn" not in body
        assert '"@type": "Product"' not in body

    def test_free_mode_logged_in_links_to_lessons(self, auth_client, free_mode, n5_data):
        client, _ = auth_client
        body = client.get("/n5-bundle").get_data(as_text=True)
        assert "Zu den Lektionen" in body
        assert "Kostenlos starten" not in body

    def test_paid_mode_still_renders_sales_page(self, client, db):
        cov = {
            "level": 5, "vocab_total": 723, "vocab_covered": 723, "vocab_pct": 100.0,
            "kanji_total": 80, "kanji_covered": 80, "kanji_pct": 100.0,
            "lessons_published_total": 65, "lessons_published_recent_7d": 7,
            "updated_at": None,
        }
        with patch("app.bundle_routes.get_jlpt_coverage", return_value=cov):
            resp = client.get("/n5-bundle")
        assert resp.status_code == 200
        body = resp.get_data(as_text=True)
        assert "JLPT N5 Komplett." in body
        assert 'class="bnd-stats"' not in body
        assert "Der komplette N5-Wortschatz: 723 Vokabeln, 80 Kanji." in body


class TestSeoAndNav:
    def test_sitemap_lists_bundle_in_free_mode(self, client, free_mode, db):
        body = client.get("/sitemap.xml").get_data(as_text=True)
        assert "/n5-bundle</loc>" in body

    def test_guest_nav_shows_n5_link_in_free_mode(self, client, free_mode, db):
        body = client.get("/lessons").get_data(as_text=True)
        assert "<span>N5 Komplett</span>" in body
        assert "alle Lektionen gratis" in body

    def test_logged_in_nav_hides_n5_link_in_free_mode(self, auth_client, free_mode, db):
        client, _ = auth_client
        body = client.get("/lessons").get_data(as_text=True)
        assert "<span>N5 Komplett</span>" not in body
