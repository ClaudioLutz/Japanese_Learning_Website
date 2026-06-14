# tests/integration/test_public_routes.py
"""
Phase 3: Integrationstests für öffentliche Routes.
Testkonzept-IDs: I-PR01 bis I-PR11
"""

import pytest
from app import db
from tests.factories import (
    LessonFactory, CourseFactory, LessonCategoryFactory, KanaFactory,
)


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

    def test_home_alias_redirects(self, client):
        """I-PR02: /home leitet per 301 auf / (SEO: Duplikat vermeiden)."""
        resp = client.get("/home")
        assert resp.status_code == 301
        assert resp.headers["Location"].endswith("/")

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
        """Top-Nav enthaelt 'Lernpfad'-Link (zeigt seit 2026-04-26 auf /#lernpfad)."""
        resp = client.get("/")
        body = resp.data.decode('utf-8')
        assert 'Lernpfad' in body
        assert '#lernpfad' in body

    def test_homepage_kana_count_is_writing_system_constant(self, client, app_context):
        """10.7 (revertiert): Die Kana-Zahl im Trust-Block ist die Schriftsystem-
        Konstante 92 (46 Grund-Hiragana + 46 Grund-Katakana), NICHT die DB-Zahl.

        Kana.query.count() liefert 200 (Tabelle enthaelt Dakuten/Handakuten/Yoon
        fuer die Spiele) und widerspraeche der H1 ('46 Grund-Hiragana') + meta.
        Es gibt kein sauberes Flag, das exakt die 92 zaehlt → die Zahl bleibt
        literal. Vokabeln/Kanji bleiben live (echt content-variabel).
        """
        from app.models import Kana
        # Selbst mit DB-Kana (z.B. 7) darf NICHT die DB-Zahl erscheinen.
        for _ in range(7):
            KanaFactory()
        db.session.commit()
        assert Kana.query.count() == 7
        resp = client.get("/")
        body = resp.data.decode('utf-8')
        assert '92 Hiragana' in body          # Schriftsystem-Konstante
        assert '7 Hiragana' not in body       # NICHT die DB-Zahl
        assert '200 Hiragana' not in body     # erst recht nicht die volle Tabelle


# ── JLPT-N5-Schweiz SEO-Landingpage ─────────────────────────

class TestJlptN5SchweizLanding:
    def test_page_loads(self, client):
        """SEO-Landing /jlpt-n5-schweiz lädt mit 200."""
        resp = client.get("/jlpt-n5-schweiz")
        assert resp.status_code == 200

    def test_verified_exam_facts_present(self, client):
        """Gegen offizielle UZH-Quelle verifizierte Fakten stehen auf der Seite.

        Schützt die faktischen Kernangaben (Termin, Gebühren, offizielle Quelle)
        vor versehentlicher Regression. Quelle Mai 2026:
        aoi.uzh.ch/de/japanologie/fremdsprache/jlpt.html
        """
        body = client.get("/jlpt-n5-schweiz").data.decode("utf-8")
        # Konkretes Pruefungsdatum bewusst weichgezeichnet (UZH publiziert den
        # Dezember-Termin erst im Jahresverlauf) — nur stabile, verifizierte Fakten pruefen.
        assert "Dezember" in body                       # typisches Pruefungsfenster
        assert "CHF 130" in body                        # N5/N4
        assert "CHF 140" in body                        # N3–N1
        assert "aoi.uzh.ch/de/japanologie/fremdsprache/jlpt.html" in body

    def test_jsonld_is_valid_and_has_faq(self, client):
        """Strukturierte Daten sind valides JSON und enthalten eine FAQPage.

        Die FAQ-Gebührenangabe im JSON-LD muss mit dem sichtbaren Text
        übereinstimmen (Google-Anforderung an FAQ-Rich-Results)."""
        import json
        import re

        body = client.get("/jlpt-n5-schweiz").data.decode("utf-8")
        match = re.search(
            r'<script type="application/ld\+json">\s*(\{.*?\})\s*</script>',
            body, re.DOTALL,
        )
        assert match, "Kein JSON-LD-Block gefunden"
        data = json.loads(match.group(1))  # wirft bei kaputtem JSON
        types = {node.get("@type") for node in data["@graph"]}
        assert "FAQPage" in types
        assert "CHF 130 für N5 und N4" in match.group(1)


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

    def test_courses_page_renders_title_server_side(self, client, app_context):
        """10.1 (SSR): Der Kurstitel steht serverseitig im HTML (kein JS noetig).

        Vor dem SSR-Umbau kamen die Karten per $.get('/api/courses') aus JS —
        der Titel fehlte im initialen HTML. Jetzt rendert Jinja die Karten.
        """
        CourseFactory(title="Mein Sichtbarer Kurs", is_published=True)
        CourseFactory(title="Versteckter Kurs", is_published=False)
        db.session.commit()
        resp = client.get("/courses")
        body = resp.get_data(as_text=True)
        # Publizierter Kurs server-seitig sichtbar
        assert "Mein Sichtbarer Kurs" in body
        # Unpublizierter Kurs darf nicht durchsickern
        assert "Versteckter Kurs" not in body
        # Kein JS-Fetch mehr auf /api/courses
        assert "/api/courses" not in body
        assert "loadCourses" not in body
        # 10.1-Regression: SSR-Karten muessen sichtbar sein. Die CSS-Regel
        # .enhanced-course-card hat opacity:0; erst .animate-in setzt sie auf
        # opacity:1. Frueher per JS gesetzt — beim SSR-Umbau muss die Klasse
        # im Markup stehen, sonst sind die Karten unsichtbar.
        assert "enhanced-course-card animate-in" in body

    def test_courses_noindex_when_empty(self, client, app_context):
        """I-PR04b: Ohne publizierten Kurs ist /courses ein leerer Container
        (Soft-404) → muss noindex tragen, damit Google die inhaltsleere Seite
        nicht als wertlose 200-Seite indexiert."""
        resp = client.get("/courses")
        assert resp.status_code == 200
        assert "noindex" in resp.get_data(as_text=True)

    def test_courses_indexable_with_published_course(self, client, app_context):
        """I-PR04c: Sobald >=1 Kurs publiziert ist, faellt /courses auf den
        index,follow-Default zurueck (kein noindex)."""
        CourseFactory(title="Visible Course", is_published=True)
        db.session.commit()
        resp = client.get("/courses")
        body = resp.get_data(as_text=True)
        # robots-Meta-Tag darf kein noindex enthalten
        import re
        m = re.search(r'<meta name="robots" content="([^"]*)"', body)
        assert m is not None
        assert "noindex" not in m.group(1)


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
