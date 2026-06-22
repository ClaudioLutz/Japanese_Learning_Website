"""Tests fuer "Weiter lernen springt an die zuletzt gelesene Stelle" (2026-06-22).

UserLessonProgress.last_page merkt sich die zuletzt besuchte Carousel-Seite
(1-basiert, gleiche Einheit wie der #page-N-Deep-Link in lesson_view.html). Alle
drei "Weiter lernen"-Flaechen haengen sie als #page-N an den Lektions-Link:
  - /lessons "Weiter lernen"-Block (continue_lesson)
  - Startseiten-Hero "Weiter lernen. Wo du aufgehört hast." (last_lesson)
  - /mein-lernen Tagesplan-Schritt "Da wo du aufgehört hast" (build_plan resume)
Katalog-/Direktaufrufe und die "naechste" Lektion starten bewusst auf Seite 1.

Abgedeckt: der Persist-Endpoint, die last_page-Loeschung beim Reset (Modell UND
HTTP-Endpunkt — Regression: raw-SQL umging frueher das Modell-reset()), und die
gerenderten Resume-Links aller drei Flaechen.
"""

from __future__ import annotations

import re
from datetime import datetime

from app import db, dashboard_service
from app.models import UserLessonProgress
from tests.factories import (
    LessonCategoryFactory,
    LessonFactory,
    UserFactory,
    UserLessonProgressFactory,
)


def _csrf(client):
    page = client.get("/lessons")
    m = re.search(r'name="csrf-token" content="([^"]+)"', page.data.decode())
    return m.group(1) if m else ""


class TestLastPageEndpoint:
    def test_updates_last_page(self, auth_client):
        client, user = auth_client
        lesson = LessonFactory(is_published=True, price=0.0, instruction_language="german")
        db.session.flush()
        UserLessonProgressFactory(user_id=user.id, lesson_id=lesson.id, progress_percentage=20)
        db.session.commit()
        lid = lesson.id

        token = _csrf(client)
        resp = client.post(
            f"/api/lessons/{lid}/last-page",
            json={"page": 4},
            headers={"X-CSRFToken": token},
        )
        assert resp.status_code == 204, resp.data

        # expire_all erzwingt ein Neuladen aus der DB -> ein gedroppter commit
        # wuerde hier auffliegen (nicht nur das In-Memory-Attribut pruefen).
        db.session.expire_all()
        pr = UserLessonProgress.query.filter_by(user_id=user.id, lesson_id=lid).first()
        assert pr.last_page == 4

    def test_boundary_pages_succeed(self, auth_client):
        client, user = auth_client
        lesson = LessonFactory(is_published=True, price=0.0, instruction_language="german")
        db.session.flush()
        UserLessonProgressFactory(user_id=user.id, lesson_id=lesson.id, progress_percentage=20)
        db.session.commit()
        lid = lesson.id
        token = _csrf(client)

        for good in (1, 500):
            resp = client.post(
                f"/api/lessons/{lid}/last-page",
                json={"page": good},
                headers={"X-CSRFToken": token},
            )
            assert resp.status_code == 204, (good, resp.data)
            db.session.expire_all()
            pr = UserLessonProgress.query.filter_by(user_id=user.id, lesson_id=lid).first()
            assert pr.last_page == good

    def test_invalid_page_rejected(self, auth_client):
        client, user = auth_client
        lesson = LessonFactory(is_published=True, price=0.0, instruction_language="german")
        db.session.flush()
        UserLessonProgressFactory(user_id=user.id, lesson_id=lesson.id, progress_percentage=20)
        db.session.commit()
        lid = lesson.id
        token = _csrf(client)

        for bad in (0, -1, "x", 1.5, True, 501, 9999):
            resp = client.post(
                f"/api/lessons/{lid}/last-page",
                json={"page": bad},
                headers={"X-CSRFToken": token},
            )
            assert resp.status_code == 400, (bad, resp.data)
        db.session.expire_all()
        pr = UserLessonProgress.query.filter_by(user_id=user.id, lesson_id=lid).first()
        assert pr.last_page is None

    def test_no_progress_returns_404(self, auth_client):
        client, user = auth_client
        lesson = LessonFactory(is_published=True, price=0.0, instruction_language="german")
        db.session.commit()
        token = _csrf(client)
        resp = client.post(
            f"/api/lessons/{lesson.id}/last-page",
            json={"page": 2},
            headers={"X-CSRFToken": token},
        )
        assert resp.status_code == 404, resp.data

    def test_csrf_missing(self, auth_client):
        client, user = auth_client
        lesson = LessonFactory(is_published=True, price=0.0, instruction_language="german")
        db.session.flush()
        UserLessonProgressFactory(user_id=user.id, lesson_id=lesson.id, progress_percentage=20)
        db.session.commit()
        resp = client.post(f"/api/lessons/{lesson.id}/last-page", json={"page": 2})
        assert resp.status_code == 400, resp.data

    def test_csrf_invalid(self, auth_client):
        client, user = auth_client
        lesson = LessonFactory(is_published=True, price=0.0, instruction_language="german")
        db.session.flush()
        UserLessonProgressFactory(user_id=user.id, lesson_id=lesson.id, progress_percentage=20)
        db.session.commit()
        resp = client.post(
            f"/api/lessons/{lesson.id}/last-page",
            json={"page": 2},
            headers={"X-CSRFToken": "definitiv-unguelig"},
        )
        assert resp.status_code == 400, resp.data

    def test_anonymous_redirected(self, client):
        resp = client.post("/api/lessons/1/last-page", json={"page": 2})
        assert resp.status_code in (301, 302, 401), resp.status_code

    def test_cross_user_isolation(self, auth_client):
        """Ein zweiter User kann die last_page-Zeile des ersten nicht ueberschreiben
        (Endpoint filtert auf user_id=current_user.id)."""
        client_a, user_a = auth_client
        lesson = LessonFactory(is_published=True, price=0.0, instruction_language="german")
        db.session.flush()
        UserLessonProgressFactory(user_id=user_a.id, lesson_id=lesson.id, progress_percentage=20)
        pr_a = UserLessonProgress.query.filter_by(user_id=user_a.id, lesson_id=lesson.id).first()
        pr_a.last_page = 3
        db.session.commit()
        lid = lesson.id

        # Zweiter User, eigener Client
        from flask import current_app
        user_b = UserFactory()
        db.session.commit()
        client_b = current_app.test_client()
        with client_b.session_transaction() as sess:
            sess["_user_id"] = str(user_b.id)
            sess["_fresh"] = True

        token_b = _csrf(client_b)
        resp = client_b.post(
            f"/api/lessons/{lid}/last-page",
            json={"page": 9},
            headers={"X-CSRFToken": token_b},
        )
        # User B hat keine Progress-Zeile fuer diese Lektion -> 404, nichts geschrieben.
        assert resp.status_code == 404, resp.data
        db.session.expire_all()
        pr_a = UserLessonProgress.query.filter_by(user_id=user_a.id, lesson_id=lid).first()
        assert pr_a.last_page == 3  # unveraendert


class TestResetClearsLastPage:
    def test_model_reset_nulls_last_page(self, auth_client):
        _client, user = auth_client
        lesson = LessonFactory(is_published=True, price=0.0, instruction_language="german")
        db.session.flush()
        pr = UserLessonProgressFactory(
            user_id=user.id, lesson_id=lesson.id, progress_percentage=50
        )
        pr.last_page = 7
        db.session.commit()

        pr.reset()
        db.session.commit()
        assert pr.last_page is None

    def test_http_reset_endpoint_nulls_last_page(self, auth_client):
        """Regression: die raw-SQL-Reset-Endpunkte umgingen frueher das Modell-
        reset() und liessen last_page stehen -> nach Reset sprang "Weiter lernen"
        mit altem #page-N mitten in die zurueckgesetzte Lektion."""
        client, user = auth_client
        lesson = LessonFactory(is_published=True, price=0.0, instruction_language="german")
        db.session.flush()
        UserLessonProgressFactory(
            user_id=user.id, lesson_id=lesson.id, progress_percentage=80
        )
        pr = UserLessonProgress.query.filter_by(user_id=user.id, lesson_id=lesson.id).first()
        pr.last_page = 8
        db.session.commit()
        lid = lesson.id

        token = _csrf(client)
        resp = client.post(
            f"/api/lessons/{lid}/reset",
            headers={"X-CSRFToken": token},
        )
        assert resp.status_code in (200, 204, 302), resp.data

        db.session.expire_all()
        pr = UserLessonProgress.query.filter_by(user_id=user.id, lesson_id=lid).first()
        assert pr.last_page is None


class TestContinueLinkHash:
    """`/lessons` "Weiter lernen"-Block."""

    def _started_lesson_with_page(self, user, last_page):
        cat = LessonCategoryFactory(name="Begrüssungen", jlpt_level=5)
        lesson = LessonFactory(
            is_published=True, price=0.0, instruction_language="german",
            category_id=cat.id, title="Wo war ich",
        )
        db.session.flush()
        UserLessonProgressFactory(
            user_id=user.id, lesson_id=lesson.id,
            progress_percentage=40, is_completed=False,
        )
        pr = UserLessonProgress.query.filter_by(user_id=user.id, lesson_id=lesson.id).first()
        pr.last_page = last_page
        pr.last_accessed = datetime.utcnow()
        db.session.commit()
        return lesson

    def test_link_carries_page_hash(self, auth_client):
        client, user = auth_client
        lesson = self._started_lesson_with_page(user, last_page=4)
        html = client.get("/lessons").data.decode()
        assert f"/lessons/{lesson.id}#page-4" in html

    def test_no_hash_on_first_page(self, auth_client):
        client, user = auth_client
        lesson = self._started_lesson_with_page(user, last_page=1)
        html = client.get("/lessons").data.decode()
        assert f"/lessons/{lesson.id}#page-" not in html


class TestHomepageHeroHash:
    """Startseiten-Hero "Weiter lernen. Wo du aufgehört hast."."""

    def _last_lesson_with_page(self, user, last_page):
        lesson = LessonFactory(
            is_published=True, price=0.0, instruction_language="german",
            title="Letzte Lektion",
        )
        db.session.flush()
        UserLessonProgressFactory(
            user_id=user.id, lesson_id=lesson.id, progress_percentage=30,
        )
        pr = UserLessonProgress.query.filter_by(user_id=user.id, lesson_id=lesson.id).first()
        pr.last_page = last_page
        pr.last_accessed = datetime.utcnow()
        db.session.commit()
        return lesson

    def test_hero_carries_page_hash(self, auth_client):
        client, user = auth_client
        lesson = self._last_lesson_with_page(user, last_page=4)
        html = client.get("/").data.decode()
        assert f"/lessons/{lesson.id}#page-4" in html

    def test_hero_no_hash_on_first_page(self, auth_client):
        client, user = auth_client
        lesson = self._last_lesson_with_page(user, last_page=1)
        html = client.get("/").data.decode()
        assert f"/lessons/{lesson.id}#page-" not in html


class TestDashboardResumeHash:
    """/mein-lernen Tagesplan-Schritt "Da wo du aufgehört hast" (build_plan)."""

    def _lesson_step(self, plan):
        return next((s for s in plan if s.get("kind") == "lesson"), None)

    def test_resume_step_carries_page_hash(self, app, auth_client):
        _client, user = auth_client
        lesson = LessonFactory(is_published=True, instruction_language="german", title="Resume mich")
        db.session.flush()
        UserLessonProgressFactory(
            user_id=user.id, lesson_id=lesson.id, progress_percentage=40, is_completed=False,
        )
        pr = UserLessonProgress.query.filter_by(user_id=user.id, lesson_id=lesson.id).first()
        pr.last_page = 5
        pr.last_accessed = datetime.utcnow()
        db.session.commit()

        with app.test_request_context():
            plan, _minutes = dashboard_service.build_plan(user.id, 0)
        step = self._lesson_step(plan)
        assert step is not None
        assert step["desc"] == "Da wo du aufgehört hast"
        assert step["href"].endswith(f"/lessons/{lesson.id}#page-5")

    def test_resume_step_no_hash_on_first_page(self, app, auth_client):
        _client, user = auth_client
        lesson = LessonFactory(is_published=True, instruction_language="german")
        db.session.flush()
        UserLessonProgressFactory(
            user_id=user.id, lesson_id=lesson.id, progress_percentage=40, is_completed=False,
        )
        pr = UserLessonProgress.query.filter_by(user_id=user.id, lesson_id=lesson.id).first()
        pr.last_page = 1
        pr.last_accessed = datetime.utcnow()
        db.session.commit()

        with app.test_request_context():
            plan, _minutes = dashboard_service.build_plan(user.id, 0)
        step = self._lesson_step(plan)
        assert step is not None
        assert "#page-" not in step["href"]

    def test_next_lesson_step_has_no_hash(self, app, auth_client):
        """Frische (noch nicht begonnene) Lektion startet auf Seite 1 — kein Hash."""
        _client, user = auth_client
        LessonFactory(is_published=True, instruction_language="german", order_index=0)
        db.session.commit()

        with app.test_request_context():
            plan, _minutes = dashboard_service.build_plan(user.id, 0)
        step = self._lesson_step(plan)
        assert step is not None
        assert step["desc"] == "Nächste im Lehrplan"
        assert "#page-" not in step["href"]
