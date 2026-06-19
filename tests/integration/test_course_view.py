"""Regression: /course/<id> darf fuer Gaeste nicht crashen (B0, Design-Review 2026-06-19).

view_course rief frueher UserLessonProgress.filter_by(user_id=current_user.id)
ungated in einer Schleife ueber course.lessons auf → Gaeste (AnonymousUserMixin
ohne .id) bekamen HTTP 500. Der Bug triggert NUR, wenn der Kurs mindestens eine
Lektion hat (sonst laeuft die Fortschritts-Schleife nicht).
"""
import pytest

from tests.factories import CourseFactory, LessonFactory

pytestmark = pytest.mark.integration


def test_guest_can_view_published_course_with_lessons(client, db):
    """Gast oeffnet veroeffentlichten Kurs MIT Lektionen → 200, kein 500 (B0)."""
    course = CourseFactory()
    course.lessons.append(LessonFactory(allow_guest_access=True))
    db.session.commit()

    resp = client.get(f"/course/{course.id}")

    assert resp.status_code == 200, (
        f"/course/{course.id} als Gast ergab {resp.status_code} — "
        "B0-Regression (ungated current_user.id in der Fortschritts-Schleife)"
    )


def test_unpublished_course_stays_404_for_guest(client, db):
    """Unveroeffentlichter Kurs bleibt fuer Gaeste 404 (kein Leak)."""
    course = CourseFactory(is_published=False)
    course.lessons.append(LessonFactory())
    db.session.commit()

    resp = client.get(f"/course/{course.id}")
    assert resp.status_code == 404
