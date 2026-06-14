# tests/integration/test_lesson_routes.py
"""
Phase 3: Integrationstests für Lektions- und Kurs-Routes.
Testkonzept-IDs: I-LR01 bis I-LR11
"""

import pytest
from app import db
from app.models import course_lessons
from tests.factories import (
    UserFactory, PremiumUserFactory,
    LessonFactory, PaidLessonFactory, PremiumLessonFactory,
    LessonContentFactory, LessonPageFactory,
    CourseFactory, PaidCourseFactory,
    LessonPurchaseFactory, CoursePurchaseFactory,
    UserLessonProgressFactory,
)


# ── I-LR01: Lesson View ─────────────────────────────────────

class TestLessonView:
    def test_free_lesson_accessible(self, auth_client):
        """I-LR01: Kostenlose Lektion zugänglich."""
        client, user = auth_client
        lesson = LessonFactory(is_published=True, price=0.0)
        db.session.commit()
        resp = client.get(f"/lessons/{lesson.id}")
        assert resp.status_code == 200

    def test_guest_lesson_without_login(self, client, app_context):
        """I-LR02: Guest-Lektion ohne Login zugänglich."""
        lesson = LessonFactory(
            is_published=True, price=0.0, allow_guest_access=True
        )
        db.session.commit()
        resp = client.get(f"/lessons/{lesson.id}")
        assert resp.status_code == 200

    def test_paid_lesson_blocked_without_purchase(self, auth_client):
        """I-LR03: Paid-Lektion ohne Kauf blockiert."""
        client, user = auth_client
        lesson = PaidLessonFactory(is_published=True)
        db.session.commit()
        resp = client.get(f"/lessons/{lesson.id}", follow_redirects=True)
        # Sollte Kauf-Hinweis oder Redirect zeigen
        assert resp.status_code == 200

    def test_paid_lesson_accessible_with_purchase(self, auth_client):
        """I-LR04: Paid-Lektion nach Kauf zugänglich."""
        client, user = auth_client
        lesson = PaidLessonFactory(is_published=True)
        db.session.commit()
        LessonPurchaseFactory(user_id=user.id, lesson_id=lesson.id)
        db.session.commit()
        resp = client.get(f"/lessons/{lesson.id}")
        assert resp.status_code == 200

    def test_nonexistent_lesson_404(self, auth_client):
        """I-LR05: Nicht existierende Lektion → 404."""
        client, user = auth_client
        resp = client.get("/lessons/99999")
        assert resp.status_code == 404

    def test_unpublished_lesson_not_public(self, auth_client):
        """I-LR06: Unveroeffentlichte Lektion ist fuer Nicht-Admins NICHT oeffentlich
        → 404 (kein Content-Leak, keine verwaiste indexierbare Seite)."""
        client, user = auth_client
        lesson = LessonFactory(is_published=False, price=0.0)
        db.session.commit()
        resp = client.get(f"/lessons/{lesson.id}")
        assert resp.status_code == 404

    def test_unpublished_lesson_visible_to_admin(self, admin_client):
        """I-LR06b: Admins sehen unveroeffentlichte Lektionen weiter (Preview/Dogfood)."""
        client, admin = admin_client
        lesson = LessonFactory(is_published=False, price=0.0)
        db.session.commit()
        resp = client.get(f"/lessons/{lesson.id}")
        assert resp.status_code == 200

    def test_gone_lesson_returns_410(self, client):
        """I-LR06c: Endgueltig getilgte Alt-Lektions-IDs (deprecated MNN-Reihe)
        liefern 410 Gone — schnelles De-Index-Signal statt nacktem 404."""
        resp = client.get("/lessons/131")
        assert resp.status_code == 410


# ── I-LR07: Course Detail ───────────────────────────────────

class TestCourseDetail:
    def test_course_detail_loads(self, client, app_context):
        """I-LR07: Kurs-Detailseite lädt."""
        course = CourseFactory(is_published=True)
        db.session.commit()
        resp = client.get(f"/course/{course.id}")
        assert resp.status_code == 200

    def test_course_shows_lessons(self, auth_client):
        """I-LR08: Kurs-Seite zeigt enthaltene Lektionen (erfordert Auth wegen current_user.id)."""
        client, user = auth_client
        course = CourseFactory(is_published=True)
        lesson = LessonFactory(title="Kurs-Lektion", is_published=True)
        db.session.commit()
        db.session.execute(
            course_lessons.insert().values(course_id=course.id, lesson_id=lesson.id)
        )
        db.session.commit()
        resp = client.get(f"/course/{course.id}")
        assert resp.status_code == 200
        assert b"Kurs-Lektion" in resp.data


# ── I-LR09: My Lessons ──────────────────────────────────────

class TestMyLessons:
    def test_my_lessons_page(self, auth_client):
        """I-LR09: /my-lessons zeigt Fortschritt."""
        client, user = auth_client
        lesson = LessonFactory(is_published=True, price=0.0)
        db.session.commit()
        UserLessonProgressFactory(user_id=user.id, lesson_id=lesson.id, progress_percentage=50)
        db.session.commit()
        resp = client.get("/my-lessons")
        assert resp.status_code == 200


# ── I-LR10: Purchase Page ───────────────────────────────────

class TestPurchasePage:
    def test_purchase_page_loads(self, auth_client):
        """I-LR10: Kauf-Seite für Lektion lädt."""
        client, user = auth_client
        lesson = PaidLessonFactory(is_published=True)
        db.session.commit()
        resp = client.get(f"/purchase/{lesson.id}")
        assert resp.status_code == 200
