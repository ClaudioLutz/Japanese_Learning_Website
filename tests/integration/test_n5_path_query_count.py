"""10.10: Query-Count-Regressionsschutz fuer module_detail (eingeloggter Pfad).

Die echte, lesson-skalierende N+1 trat fuer EINGELOGGTE User auf: access_check
feuerte pro Lesson eine LessonPurchase-, ggf. CoursePurchase- (je Course) und
UserLessonProgress-Query (Voraussetzungen) plus module_detail eine
Fortschritts-Query je Lesson. Als Gast existiert diese N+1 gar nicht — darum
laeuft dieser Test bewusst als eingeloggter User mit paid-Lessons, Kauf,
Voraussetzung und Course, sodass access_check tief laeuft.

Assertion: der Query-Zuwachs darf NICHT mit der Lesson-Anzahl skalieren.
"""
from contextlib import contextmanager

from sqlalchemy import event

from app import db
from tests.factories import (
    CourseFactory,
    LessonCategoryFactory,
    LessonFactory,
    LessonPurchaseFactory,
    UserFactory,
    UserLessonProgressFactory,
)
from app.models import LessonPrerequisite, course_lessons


def _make_module(slug, name):
    return LessonCategoryFactory(
        slug=slug, jlpt_level=5, display_order=1, name=name, icon_emoji="📖",
    )


@contextmanager
def count_queries():
    """Zaehlt ausgefuehrte SQL-Statements auf der aktuellen Engine."""
    counter = {"n": 0}
    engine = db.engine

    def _before(conn, cursor, statement, params, context, executemany):
        counter["n"] += 1

    event.listen(engine, "before_cursor_execute", _before)
    try:
        yield counter
    finally:
        event.remove(engine, "before_cursor_execute", _before)


def _module_with_n_paid_lessons(slug, n, user):
    """Modul mit n paid-Lessons, jeweils mit Voraussetzung + Course-Zuordnung.

    Damit access_check pro Lesson wirklich tief laeuft: LessonPurchase-Check
    (eine Lesson gekauft), Course-Loop mit CoursePurchase-Check, und
    Voraussetzungs-Completion-Check.
    """
    mod = _make_module(slug, f"Modul {slug}")
    # Gemeinsame Voraussetzung (eine kostenlose Lesson), vom User abgeschlossen.
    prereq = LessonFactory(
        category_id=mod.id, is_published=True, instruction_language="german",
        price=0.0, order_index=0, title=f"{slug}-prereq",
    )
    db.session.commit()
    UserLessonProgressFactory(user_id=user.id, lesson_id=prereq.id, is_completed=True)
    course = CourseFactory(title=f"{slug}-course", is_published=True)
    db.session.commit()
    for i in range(n):
        lesson = LessonFactory(
            category_id=mod.id, is_published=True, instruction_language="german",
            order_index=i + 1, price=5.0, is_purchasable=True,
            title=f"{slug}-paid-{i}",
        )
        db.session.commit()
        # Voraussetzung verknuepfen
        db.session.add(LessonPrerequisite(
            lesson_id=lesson.id, prerequisite_lesson_id=prereq.id,
        ))
        # Lesson dem Course zuordnen (Course-Kauf-Zweig)
        db.session.execute(
            course_lessons.insert().values(course_id=course.id, lesson_id=lesson.id)
        )
        # Genau die erste paid-Lesson kaufen (LessonPurchase-Zweig aktiv)
        if i == 0:
            LessonPurchaseFactory(user_id=user.id, lesson_id=lesson.id)
    db.session.commit()
    return mod


def _login(app, user):
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)
        sess["_fresh"] = True
    return client


class TestModuleDetailQueryCount:
    def test_query_count_does_not_scale_with_lessons_logged_in(self, app, db):
        """module_detail (eingeloggt): Query-Zuwachs 2→6 paid-Lessons bleibt klein.

        Mit der frueheren Per-Row-N+1 (pro Lesson mind. LessonPurchase +
        UserLessonProgress, fuer nicht-gekaufte zusaetzlich CoursePurchase)
        waere der Zuwachs gross und linear (gemessen +8 bei +4 Lessons). Mit der
        AccessContext-Batch-Optimierung ist er klein/konstant.
        """
        with app.app_context():
            user = UserFactory()
            db.session.commit()
            _module_with_n_paid_lessons("qc-small", 2, user)
            _module_with_n_paid_lessons("qc-large", 6, user)

            client = _login(app, user)

            with count_queries() as c_small:
                resp = client.get("/learn/n5/qc-small")
                assert resp.status_code == 200
            small = c_small["n"]

            with count_queries() as c_large:
                resp = client.get("/learn/n5/qc-large")
                assert resp.status_code == 200
            large = c_large["n"]

            # 4 zusaetzliche Lessons. Mit Per-Row-N+1 (>=2-3 Queries je Lesson)
            # waere large-small >= ~10. Mit Batch bleibt der Zuwachs klein
            # (Schwelle bewusst grosszuegig gegen Plattform-Rauschen, aber weit
            # unter der linearen N+1-Groesse).
            assert large - small <= 4, (
                f"Query-Zahl skaliert mit Lesson-Anzahl trotz Batch "
                f"(2 paid: {small}, 6 paid: {large}, delta {large - small}) "
                f"— N+1-Regression im eingeloggten module_detail-Pfad?"
            )
