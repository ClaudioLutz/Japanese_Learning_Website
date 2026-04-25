# tests/integration/test_public_routes.py
"""
Phase 3: Integrationstests für öffentliche Routes.
Testkonzept-IDs: I-PR01 bis I-PR11
"""

import pytest
from app import db
from tests.factories import LessonFactory, CourseFactory, LessonCategoryFactory


# ── I-PR01: Health-Endpoints ─────────────────────────────────

class TestHealthEndpoints:
    def test_healthz(self, client):
        """I-PR01: /healthz gibt 200."""
        resp = client.get("/healthz")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ok"

    def test_health_check(self, client):
        """I-PR01: /health gibt 200 mit DB-Check."""
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "healthy"


# ── I-PR02: Homepage ────────────────────────────────────────

class TestHomepage:
    def test_index_loads(self, client):
        """I-PR02: Homepage lädt mit 200."""
        resp = client.get("/")
        assert resp.status_code == 200

    def test_home_alias(self, client):
        """I-PR02: /home funktioniert ebenfalls."""
        resp = client.get("/home")
        assert resp.status_code == 200

    def test_homepage_shows_n5_path_section(self, client, app_context):
        """Homepage zeigt JLPT-N5-Lernpfad-Section (Mayuko-Direktive)."""
        from app.models import LessonCategory
        cat = LessonCategoryFactory(
            slug='test-n5-mod-home',
            jlpt_level=5,
            display_order=1,
            name='Test N5 Module',
            icon_emoji='あ',
        )
        db.session.commit()
        resp = client.get("/")
        body = resp.data.decode('utf-8')
        assert 'JLPT N5' in body or 'Lernpfad' in body
        assert 'Test N5 Module' in body

    def test_homepage_guest_shows_signup_cta(self, client):
        """Gast sieht Sign-Up-CTA auf Homepage."""
        resp = client.get("/")
        body = resp.data.decode('utf-8')
        assert 'Kostenlos starten' in body

    def test_homepage_authenticated_shows_continue(self, auth_client):
        """Eingeloggter User sieht Continue-Hero (Greeting oder Weiter-CTA)."""
        client, user = auth_client
        resp = client.get("/")
        body = resp.data.decode('utf-8')
        assert user.username in body or 'Weiter' in body or 'Bereit' in body
        # Sign-Up-CTA verschwindet bei Login
        assert 'Kostenlos starten' not in body

    def test_homepage_includes_lernpfad_nav_link(self, client):
        """Top-Nav enthaelt 'Lernpfad'-Link."""
        resp = client.get("/")
        body = resp.data.decode('utf-8')
        assert 'Lernpfad' in body
        assert '/learn/n5' in body


# ── I-PR03: Lessons-Seite ───────────────────────────────────

class TestLessonsPage:
    def test_lessons_page_loads(self, client):
        """I-PR03: /lessons gibt 200."""
        resp = client.get("/lessons")
        assert resp.status_code == 200

    def test_lessons_page_renders(self, client, app_context):
        """I-PR03: Lessons-Seite rendert (Daten werden per JS geladen)."""
        LessonFactory(title="Published Lesson", is_published=True)
        db.session.commit()
        resp = client.get("/lessons")
        assert resp.status_code == 200


# ── I-PR04: Courses-Seite ───────────────────────────────────

class TestCoursesPage:
    def test_courses_page_loads(self, client):
        """I-PR04: /courses gibt 200."""
        resp = client.get("/courses")
        assert resp.status_code == 200

    def test_courses_page_renders_with_data(self, client, app_context):
        """I-PR04: Courses-Seite rendert (Kurse werden serverseitig an Template übergeben)."""
        CourseFactory(title="Visible Course", is_published=True)
        CourseFactory(title="Hidden Course", is_published=False)
        db.session.commit()
        resp = client.get("/courses")
        assert resp.status_code == 200


# ── I-PR05: Login-Seite ─────────────────────────────────────

class TestLoginPage:
    def test_login_page_loads(self, client):
        """I-PR05: /login gibt 200."""
        resp = client.get("/login")
        assert resp.status_code == 200

    def test_login_page_has_form(self, client):
        """I-PR05: Login-Seite enthält Formular."""
        resp = client.get("/login")
        assert b"Email" in resp.data or b"email" in resp.data


# ── I-PR06: Register-Seite ──────────────────────────────────

class TestRegisterPage:
    def test_register_page_loads(self, client):
        """I-PR06: /register gibt 200."""
        resp = client.get("/register")
        assert resp.status_code == 200


# ── I-PR07: Geschützte Seiten redirect zu Login ─────────────

class TestProtectedRedirects:
    def test_profile_redirects_unauthenticated(self, client):
        """I-PR07: /profile redirect ohne Login."""
        resp = client.get("/profile", follow_redirects=False)
        assert resp.status_code in (302, 308)

    def test_my_lessons_redirects(self, client):
        """I-PR07: /my-lessons redirect ohne Login."""
        resp = client.get("/my-lessons", follow_redirects=False)
        assert resp.status_code in (302, 308)

    def test_admin_redirects(self, client):
        """I-PR07: /admin redirect ohne Login."""
        resp = client.get("/admin", follow_redirects=False)
        assert resp.status_code in (302, 308)
