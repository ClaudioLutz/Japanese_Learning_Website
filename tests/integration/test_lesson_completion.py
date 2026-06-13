# tests/integration/test_lesson_completion.py
"""Integrationstests fuer den Lektionsabschluss-Fix (2026-06-13).

Kern-Regression: Der Progress-Endpoint rechnete den Prozentsatz frueher mit
einem eigenen Raw-SQL gegen ALLE LessonContent-Zeilen (inkl. is_optional). Seit
dem Lektionsbilder-Rollout hat jede Lektion viele optionale Bilder -> keine
Lektion erreichte je 100% und wurde nie als fertig angezeigt. Der Endpoint
delegiert jetzt an die Modell-Logik (progress_visible_content_items).

Zusaetzlich getestet: der Bulk-Endpoint /complete-remaining (passive Items aller
Typen) und der Lernstatus im /lessons-Katalog (Discoverability).
"""

from __future__ import annotations

import re

from app import db
from app.models import LessonContent
from tests.factories import (
    LessonFactory,
    UserLessonProgressFactory,
)


def _csrf(client):
    """Gueltiges CSRF-Token aus dem gerenderten Meta-Tag holen."""
    page = client.get("/lessons")
    m = re.search(r'name="csrf-token" content="([^"]+)"', page.data.decode())
    return m.group(1) if m else ""


def _content(lesson_id, content_type="text", page_number=1, order_index=0,
             is_optional=False, is_interactive=False, content_id=None, media_url=None):
    lc = LessonContent(
        lesson_id=lesson_id,
        content_type=content_type,
        page_number=page_number,
        order_index=order_index,
        is_optional=is_optional,
        is_interactive=is_interactive,
        content_id=content_id,
        media_url=media_url,
    )
    db.session.add(lc)
    return lc


class TestProgressDenominator:
    def test_optional_items_do_not_block_100(self, auth_client):
        """Regression: 3 sichtbare Items + 5 optionale Bilder. Nach dem Markieren
        der 3 sichtbaren muss progress_percentage 100 / is_completed True sein.
        (Mit dem alten Nenner-Bug waeren es 3/8 = 37%.)"""
        client, user = auth_client
        lesson = LessonFactory(is_published=True, price=0.0, instruction_language="german")
        db.session.flush()
        visible = [
            _content(lesson.id, "text", page_number=1, order_index=i, content_id=i + 1)
            for i in range(3)
        ]
        for j in range(5):  # dekorative optionale Seitenbilder (Lektionsbilder-Rollout)
            _content(lesson.id, "image", page_number=1, order_index=10 + j,
                     is_optional=True, media_url=f"/uploads/p{j}.webp")
        db.session.commit()
        lid = lesson.id
        visible_ids = [c.id for c in visible]

        token = _csrf(client)
        resp = None
        for cid in visible_ids:
            resp = client.post(
                f"/api/lessons/{lid}/progress",
                json={"content_id": cid},
                headers={"X-CSRFToken": token},
            )
            assert resp.status_code == 200, resp.data

        data = resp.get_json()
        assert data["progress_percentage"] == 100, data
        assert data["is_completed"] is True

    def test_partial_progress_is_proportional(self, auth_client):
        """Haelfte der sichtbaren Items -> 50%, nicht durch optionale verwaessert."""
        client, user = auth_client
        lesson = LessonFactory(is_published=True, price=0.0, instruction_language="german")
        db.session.flush()
        items = [
            _content(lesson.id, "text", page_number=1, order_index=i, content_id=i + 1)
            for i in range(4)
        ]
        _content(lesson.id, "image", page_number=1, order_index=20, is_optional=True,
                 media_url="/uploads/x.webp")
        db.session.commit()
        lid = lesson.id
        ids = [c.id for c in items]

        token = _csrf(client)
        for cid in ids[:2]:
            resp = client.post(f"/api/lessons/{lid}/progress",
                               json={"content_id": cid}, headers={"X-CSRFToken": token})
            assert resp.status_code == 200
        assert resp.get_json()["progress_percentage"] == 50


class TestCompleteRemaining:
    def test_marks_passive_not_interactive(self, auth_client):
        """complete-remaining markiert passive Items (Text/Slideshow), laesst das
        interaktive Quiz aber offen -> erst nach dessen Abschluss 100%."""
        client, user = auth_client
        lesson = LessonFactory(is_published=True, price=0.0, instruction_language="german")
        db.session.flush()
        _content(lesson.id, "text", page_number=1, order_index=0, content_id=1)
        _content(lesson.id, "dialog_slideshow", page_number=2, order_index=0, content_id=2)
        quiz = _content(lesson.id, "text", page_number=3, order_index=0, content_id=3,
                        is_interactive=True)
        db.session.commit()
        lid = lesson.id
        quiz_id = quiz.id

        token = _csrf(client)
        resp = client.post(f"/api/lessons/{lid}/complete-remaining",
                           headers={"X-CSRFToken": token})
        assert resp.status_code == 200, resp.data
        data = resp.get_json()
        assert data["is_completed"] is False
        assert data["progress_percentage"] == 66  # 2 von 3 sichtbaren passiv

        # Quiz ueber den regulaeren Pfad abschliessen -> 100%
        resp2 = client.post(f"/api/lessons/{lid}/progress",
                            json={"content_id": quiz_id}, headers={"X-CSRFToken": token})
        data2 = resp2.get_json()
        assert data2["progress_percentage"] == 100
        assert data2["is_completed"] is True

    def test_pure_passive_lesson_completes(self, auth_client):
        """Reine Slideshow/Text-Lektion erreicht ueber complete-remaining 100%."""
        client, user = auth_client
        lesson = LessonFactory(is_published=True, price=0.0, instruction_language="german")
        db.session.flush()
        _content(lesson.id, "dialog_slideshow", page_number=1, order_index=0, content_id=1)
        _content(lesson.id, "text", page_number=1, order_index=1, content_id=2)
        db.session.commit()
        lid = lesson.id

        token = _csrf(client)
        resp = client.post(f"/api/lessons/{lid}/complete-remaining",
                           headers={"X-CSRFToken": token})
        assert resp.status_code == 200, resp.data
        data = resp.get_json()
        assert data["progress_percentage"] == 100
        assert data["is_completed"] is True

    def test_requires_csrf(self, auth_client):
        client, user = auth_client
        lesson = LessonFactory(is_published=True, price=0.0, instruction_language="german")
        db.session.flush()
        _content(lesson.id, "text", page_number=1, content_id=1)
        db.session.commit()
        resp = client.post(f"/api/lessons/{lesson.id}/complete-remaining")
        assert resp.status_code == 400

    def test_inaccessible_paid_lesson_forbidden(self, auth_client):
        """Ein nicht gekauftes Paid-Lesson darf NICHT via complete-remaining
        abgeschlossen werden (sonst Prerequisite-Abuse) -> 403."""
        from tests.factories import PaidLessonFactory
        client, user = auth_client
        lesson = PaidLessonFactory(is_published=True, instruction_language="german")
        db.session.flush()
        _content(lesson.id, "text", page_number=1, content_id=1)
        db.session.commit()
        token = _csrf(client)
        resp = client.post(f"/api/lessons/{lesson.id}/complete-remaining",
                           headers={"X-CSRFToken": token})
        assert resp.status_code == 403


class TestCatalogStatus:
    def test_status_badge_and_filter_for_authenticated(self, auth_client):
        """Eingeloggt: data-status + Status-Badge + 'Noch offen'-Filter sichtbar."""
        client, user = auth_client
        done = LessonFactory(is_published=True, price=0.0, instruction_language="german",
                             title="Fertige Lektion")
        LessonFactory(is_published=True, price=0.0, instruction_language="german",
                      title="Offene Lektion")
        db.session.flush()
        UserLessonProgressFactory(user_id=user.id, lesson_id=done.id,
                                  is_completed=True, progress_percentage=100)
        db.session.commit()

        html = client.get("/lessons").data.decode()
        assert 'data-status="done"' in html
        assert 'data-status="open"' in html
        assert 'aria-label="Lernstatus"' in html  # Status-Filter-Pills sichtbar
        assert "lp-badge-done" in html

    def test_no_status_filter_for_guests(self, client, app_context):
        """Gast: kein Lernstatus-Filter (show_status False)."""
        LessonFactory(is_published=True, price=0.0, instruction_language="german",
                      allow_guest_access=True)
        db.session.commit()
        html = client.get("/lessons").data.decode()
        assert 'aria-label="Lernstatus"' not in html
