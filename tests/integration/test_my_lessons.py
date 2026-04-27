"""Integration-Tests fuer /my-lessons (Bug 2026-04-27: Course-Lektionen fehlten)."""

from app import db
from app.models import course_lessons
from tests.factories import (
    UserFactory, PaidLessonFactory, PaidCourseFactory,
    LessonPurchaseFactory, CoursePurchaseFactory,
)


def test_my_lessons_includes_lessons_from_purchased_course(app, db):
    """
    Regression: Wer das N5-Bundle (Course) kauft, soll auf /my-lessons alle
    enthaltenen Lektionen sehen — nicht nur direkte LessonPurchases.
    Vor dem Fix erschien "No Purchased Lessons Yet", obwohl der Kurs gekauft war.
    """
    user = UserFactory(password="x")

    course = PaidCourseFactory(title="JLPT N5 Komplett", price=9.90)
    lesson_a = PaidLessonFactory(is_published=True, title="N5 - Hiragana 1")
    lesson_b = PaidLessonFactory(is_published=True, title="N5 - Hiragana 2")
    lesson_c = PaidLessonFactory(is_published=False, title="Unveroeffentlicht")
    db.session.execute(course_lessons.insert().values([
        {"course_id": course.id, "lesson_id": lesson_a.id},
        {"course_id": course.id, "lesson_id": lesson_b.id},
        {"course_id": course.id, "lesson_id": lesson_c.id},
    ]))
    CoursePurchaseFactory(user_id=user.id, course_id=course.id, price_paid=9.90)
    db.session.commit()

    client = app.test_client()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)

    resp = client.get("/my-lessons")
    body = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert "N5 - Hiragana 1" in body
    assert "N5 - Hiragana 2" in body
    assert "Unveroeffentlicht" not in body, "Unveroeffentlichte Lektionen duerfen nicht erscheinen"
    assert "JLPT N5 Komplett" in body
    assert "CHF 9.90" in body or "9.90" in body


def test_my_lessons_lesson_purchase_and_course_purchase_no_duplicate(app, db):
    """Wer eine Lektion einzeln UND ueber den Kurs gekauft hat, sieht sie nur einmal."""
    user = UserFactory(password="x")
    course = PaidCourseFactory(price=9.90)
    lesson = PaidLessonFactory(is_published=True, title="Doppel-Test")
    db.session.execute(course_lessons.insert().values([
        {"course_id": course.id, "lesson_id": lesson.id},
    ]))
    LessonPurchaseFactory(user_id=user.id, lesson_id=lesson.id, price_paid=5.0)
    CoursePurchaseFactory(user_id=user.id, course_id=course.id, price_paid=9.90)
    db.session.commit()

    client = app.test_client()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)
    resp = client.get("/my-lessons")
    body = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert body.count("Doppel-Test") == 1, "Lektion darf nicht doppelt erscheinen"
    # Total = 5.0 (Lesson) + 9.90 (Course) = 14.90
    assert "14.90" in body
