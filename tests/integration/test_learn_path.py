"""Integrationstests fuer JLPT-Lernpfad-Route /learn/n<level>.

Mayuko-Direktive 2026-04-25: Lektionen sind in JLPT-Modulen organisiert.
Pfad-Seite zeigt Module mit Fortschritt + Lock-Status.
"""
from app import db
from app.models import LessonCategory, UserLessonProgress
from tests.factories import (
    LessonCategoryFactory, LessonFactory, UserLessonProgressFactory,
)


def _make_module(slug, jlpt_level, display_order, **kwargs):
    """Helper: Pflicht-Module-Felder befuellen."""
    return LessonCategoryFactory(
        slug=slug,
        jlpt_level=jlpt_level,
        display_order=display_order,
        icon_emoji=kwargs.pop("icon_emoji", "📖"),
        **kwargs,
    )


class TestLearnPathRoute:
    """Seit 2026-04-26 redirektet /learn/n5 auf /#lernpfad — der Pfad wird auf der
    Startseite gerendert, nicht mehr in einem separaten Template. Die Pfad-Render-
    Tests laufen daher gegen "/"."""

    def test_learn_default_redirects_to_home(self, client, app_context):
        """/learn (ohne Level) redirektet auf /#lernpfad."""
        resp = client.get("/learn")
        assert resp.status_code == 301
        assert resp.headers["Location"].endswith("#lernpfad")

    def test_learn_n5_redirects_to_home(self, client, app_context):
        """/learn/n5 redirektet 301 auf /#lernpfad — Pfad lebt auf der Startseite."""
        resp = client.get("/learn/n5")
        assert resp.status_code == 301
        assert resp.headers["Location"].endswith("#lernpfad")

    def test_learn_n4_returns_404(self, client, app_context):
        """N4 ist noch nicht inhaltlich vorhanden — 404 statt leere Seite."""
        resp = client.get("/learn/n4")
        assert resp.status_code == 404

    def test_learn_path_invalid_level_404(self, client, app_context):
        """Ungueltige Level (z.B. 6) → 404."""
        resp = client.get("/learn/n6")
        assert resp.status_code == 404

    def test_module_ordering(self, client, app_context):
        """Module werden nach display_order sortiert (gerendert auf der Startseite)."""
        _make_module("zzz-late", jlpt_level=5, display_order=10, name="ZLate Modul")
        _make_module("aaa-early", jlpt_level=5, display_order=1, name="AEarly Modul")
        db.session.commit()
        resp = client.get("/")
        body = resp.data.decode("utf-8")
        assert body.index("AEarly Modul") < body.index("ZLate Modul")

    def test_module_with_lesson_shows_link(self, client, app_context):
        """Modul mit Lektion zeigt Lektions-Link auf der Startseite."""
        mod = _make_module("with-lesson", jlpt_level=5, display_order=1, name="Mit Lektion")
        db.session.flush()
        # CONTENT_LANGUAGES default = ['german'] — Test-Lesson muss German sein
        lesson = LessonFactory(category_id=mod.id, is_published=True,
                                title="Mein Lernstoff", instruction_language="german")
        db.session.commit()
        resp = client.get("/")
        assert b"Mein Lernstoff" in resp.data
        assert f"/lessons/{lesson.id}".encode() in resp.data


class TestModuleUnlockLogic:
    def test_module_without_prereq_always_unlocked(self, app_context):
        """Modul ohne prerequisite ist immer freigeschaltet."""
        m = _make_module("free", jlpt_level=5, display_order=1, name="Frei")
        db.session.commit()
        assert m.is_unlocked_for_user(None) is True

    def test_module_with_unfulfilled_prereq_locked_for_user(self, app_context):
        """Modul mit Voraussetzung ist fuer eingeloggte User gesperrt,
        wenn Vorgaenger nicht ausreichend abgeschlossen."""
        from tests.factories import UserFactory
        m_pre = _make_module("pre", jlpt_level=5, display_order=1, name="Voraussetzung")
        db.session.flush()
        # Vorgaenger hat 2 Lektionen, keine completed
        LessonFactory(category_id=m_pre.id, is_published=True)
        LessonFactory(category_id=m_pre.id, is_published=True)
        m_post = _make_module(
            "post", jlpt_level=5, display_order=2, name="Folgemodul",
            prerequisite_category_id=m_pre.id,
        )
        user = UserFactory()
        db.session.commit()
        assert m_post.is_unlocked_for_user(user) is False

    def test_module_with_fulfilled_prereq_unlocked(self, app_context):
        """Modul wird unlocked, wenn Vorgaenger zu >=80% abgeschlossen."""
        from tests.factories import UserFactory
        m_pre = _make_module("pre2", jlpt_level=5, display_order=1, name="Vor")
        db.session.flush()
        l1 = LessonFactory(category_id=m_pre.id, is_published=True)
        l2 = LessonFactory(category_id=m_pre.id, is_published=True)
        m_post = _make_module(
            "post2", jlpt_level=5, display_order=2, name="Folge",
            prerequisite_category_id=m_pre.id,
        )
        user = UserFactory()
        db.session.flush()
        # Beide Vorgaenger-Lektionen completed → 100% > 80%
        UserLessonProgressFactory(user_id=user.id, lesson_id=l1.id, is_completed=True)
        UserLessonProgressFactory(user_id=user.id, lesson_id=l2.id, is_completed=True)
        db.session.commit()
        assert m_post.is_unlocked_for_user(user) is True

    def test_anonymous_user_sees_all_modules_unlocked(self, app_context):
        """Anonyme User sehen alle Module als unlocked (Detail-Pruefung erst beim Lesson-Zugriff)."""
        m_pre = _make_module("pre3", jlpt_level=5, display_order=1, name="Vor")
        db.session.flush()
        m_post = _make_module(
            "post3", jlpt_level=5, display_order=2, name="Folge",
            prerequisite_category_id=m_pre.id,
        )
        db.session.commit()
        assert m_post.is_unlocked_for_user(None) is True

    def test_completion_percent_calculation(self, app_context):
        """completion_for_user gibt (done, total) korrekt zurueck."""
        from tests.factories import UserFactory
        m = _make_module("counter", jlpt_level=5, display_order=1, name="Zaehler")
        db.session.flush()
        l1 = LessonFactory(category_id=m.id, is_published=True)
        l2 = LessonFactory(category_id=m.id, is_published=True)
        l3_unpub = LessonFactory(category_id=m.id, is_published=False)  # zaehlt nicht
        user = UserFactory()
        db.session.flush()
        UserLessonProgressFactory(user_id=user.id, lesson_id=l1.id, is_completed=True)
        db.session.commit()
        done, total = m.completion_for_user(user)
        assert (done, total) == (1, 2)
