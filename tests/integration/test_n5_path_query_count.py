"""10.10: Query-Count-Regressionsschutz fuer den N5-Pfad / Modul-Detail.

Vor dem Eager-Loading feuerte module_detail pro Lesson mehrere Lazy-Queries
(Voraussetzungen, prerequisite_lesson, courses) → die Query-Zahl wuchs linear
mit der Lesson-Anzahl (N+1). Dieser Test stellt sicher, dass die Query-Zahl
NICHT linear mit der Anzahl Lessons skaliert.
"""
from contextlib import contextmanager

from sqlalchemy import event

from app import db
from tests.factories import LessonCategoryFactory, LessonFactory


def _make_module(slug, display_order, name):
    return LessonCategoryFactory(
        slug=slug,
        jlpt_level=5,
        display_order=display_order,
        name=name,
        icon_emoji="📖",
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


def _module_with_n_lessons(slug, n):
    mod = _make_module(slug, 1, f"Modul {slug}")
    db.session.commit()
    for i in range(n):
        LessonFactory(
            category_id=mod.id,
            is_published=True,
            instruction_language="german",
            order_index=i,
            price=5.0,
            is_purchasable=True,
        )
    db.session.commit()
    return mod


class TestModuleDetailQueryCount:
    def test_query_count_does_not_scale_linearly_with_lessons(self, client, app_context):
        """module_detail: Query-Zahl bei 6 Lessons darf nicht ~3x der bei 2 sein.

        Mit N+1 (pro Lesson 3 Lazy-Queries) waere der Unterschied 2→6 Lessons
        gross und linear. Mit Eager-Loading bleibt der Zuwachs klein/konstant.
        """
        _module_with_n_lessons("qcount-small", 2)
        _module_with_n_lessons("qcount-large", 6)

        with count_queries() as c_small:
            resp = client.get("/learn/n5/qcount-small")
            assert resp.status_code == 200
        small = c_small["n"]

        with count_queries() as c_large:
            resp = client.get("/learn/n5/qcount-large")
            assert resp.status_code == 200
        large = c_large["n"]

        # Bei N+1 (3 Extra-Queries je Lesson) waere large - small >= ~12.
        # Mit Eager-Loading ist der Zuwachs durch selectin-Batches klein.
        assert large - small <= 6, (
            f"Query-Zahl skaliert verdaechtig mit Lesson-Anzahl "
            f"(2 Lessons: {small}, 6 Lessons: {large}) — N+1-Regression?"
        )
