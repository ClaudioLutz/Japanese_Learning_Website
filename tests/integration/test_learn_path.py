"""Integrationstests fuer JLPT-Lernpfad-Route /learn/n<level>.

Mayuko-Direktive 2026-04-25: Lektionen sind in JLPT-Modulen organisiert.
Pfad-Seite zeigt Module mit Fortschritt + Lock-Status.
"""
from app import db
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
    """Seit H1 (2026-05-31) rendert /learn/n5 eine eigene indexierbare 200-Hub-Seite
    (learn_n5.html) statt 301 auf /#lernpfad — die generischste N5-URL soll eigene
    Ranking-Autoritaet sammeln. Die Modul-Pfad-Logik teilt sie sich mit der Startseite.
    """

    def test_learn_default_renders_n5_hub(self, client, app_context):
        """/learn (ohne Level) rendert die N5-Hub-Seite (Default level=5)."""
        resp = client.get("/learn")
        assert resp.status_code == 200
        body = resp.data.decode("utf-8")
        assert "Lernpfad" in body

    def test_learn_n5_renders_hub_200(self, client, app_context):
        """/learn/n5 ist eine eigene 200-Seite (kein 301 mehr) mit Lernpfad/Modul-Inhalt
        und Self-Canonical auf /learn/n5."""
        resp = client.get("/learn/n5")
        assert resp.status_code == 200
        body = resp.data.decode("utf-8")
        assert "Lernpfad" in body or "JLPT N5" in body
        # Self-Canonical zeigt auf die Hub-URL selbst, nicht auf das Home-Fragment
        assert "/learn/n5" in body

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

    def test_module_with_lesson_links_to_module_detail(self, client, app_context):
        """Modul mit Lektion + slug verlinkt auf der Startseite zur Modul-Detail-
        seite. Architektur seit 2026-04: die Startseite zeigt Modul-Karten, die
        einzelnen Lektionen (Titel + /lessons/<id>) leben auf /learn/n5/<slug>
        (siehe TestModuleDetailRoute)."""
        mod = _make_module("with-lesson", jlpt_level=5, display_order=1, name="Mit Lektion")
        db.session.flush()
        # CONTENT_LANGUAGES default = ['german'] — Test-Lesson muss German sein
        LessonFactory(category_id=mod.id, is_published=True,
                      title="Mein Lernstoff", instruction_language="german")
        db.session.commit()
        body = client.get("/").data.decode("utf-8")
        assert "Mit Lektion" in body                  # Modul-Name auf der Station-Karte
        assert "/learn/n5/with-lesson" in body        # Link zur Modul-Detailseite


class TestModuleDetailRoute:
    """/learn/n<level>/<slug> — Modul-Detailseite. War bis 2026-05 ungetestet;
    Coverage ergänzt, als die veralteten Startseiten-Assertions korrigiert wurden."""

    def test_single_lesson_redirects_to_lesson(self, client, app_context):
        """Skip-Optimierung: Modul mit genau 1 Lektion leitet direkt zur Lektion
        (keine Zwischenseite)."""
        mod = _make_module("solo", jlpt_level=5, display_order=1, name="Solo-Modul")
        db.session.flush()
        lesson = LessonFactory(category_id=mod.id, is_published=True,
                               title="Einzige Lektion", instruction_language="german")
        db.session.commit()
        resp = client.get("/learn/n5/solo")
        assert resp.status_code == 302
        assert resp.headers["Location"].endswith(f"/lessons/{lesson.id}")

    def test_multi_lesson_lists_lesson_links(self, client, app_context):
        """Modul mit mehreren Lektionen rendert die Lektions-Titel + /lessons/<id>."""
        mod = _make_module("multi", jlpt_level=5, display_order=1, name="Multi-Modul")
        db.session.flush()
        l1 = LessonFactory(category_id=mod.id, is_published=True,
                           title="Erste Lektion", instruction_language="german")
        l2 = LessonFactory(category_id=mod.id, is_published=True,
                           title="Zweite Lektion", instruction_language="german")
        db.session.commit()
        body = client.get("/learn/n5/multi").data.decode("utf-8")
        assert "Erste Lektion" in body
        assert "Zweite Lektion" in body
        assert f"/lessons/{l1.id}" in body
        assert f"/lessons/{l2.id}" in body

    def test_unknown_slug_returns_404(self, client, app_context):
        """Unbekannter Slug → 404."""
        assert client.get("/learn/n5/gibt-es-nicht").status_code == 404

    def test_empty_module_shows_empty_state(self, client, app_context):
        """10.11: Modul ohne veroeffentlichte Lektionen → 200 + freundlicher
        Empty-State (KEIN 404, KEINE leere Lektionsliste)."""
        _make_module("leer", jlpt_level=5, display_order=1, name="Leeres Modul")
        db.session.commit()
        resp = client.get("/learn/n5/leer")
        assert resp.status_code == 200
        body = resp.data.decode("utf-8")
        assert "Dieses Modul wird gerade gestaltet" in body
        # Kein Lektions-Listen-Container (leere lesson-list)
        assert 'class="lesson-list"' not in body

    def test_empty_module_admin_hint(self, admin_client):
        """10.11: Admin sieht im Empty-State zusaetzlich den Veroeffentlichungs-Hinweis."""
        client, admin = admin_client
        _make_module("leer-admin", jlpt_level=5, display_order=1, name="Leer Admin")
        db.session.commit()
        body = client.get("/learn/n5/leer-admin").data.decode("utf-8")
        assert "Dieses Modul wird gerade gestaltet" in body
        assert "Du bist Admin" in body


# ── 10.3: Bundle-CTA-Gating in module_detail ────────────────

def _module_with_two_paid(slug):
    """Modul mit 2 paid-Lektionen (>1 → keine Single-Lesson-Weiterleitung)."""
    mod = _make_module(slug, jlpt_level=5, display_order=1, name=f"Modul {slug}")
    db.session.flush()
    LessonFactory(category_id=mod.id, is_published=True,
                  instruction_language="german", price=5.0, is_purchasable=True,
                  order_index=1, title=f"{slug}-1")
    LessonFactory(category_id=mod.id, is_published=True,
                  instruction_language="german", price=5.0, is_purchasable=True,
                  order_index=2, title=f"{slug}-2")
    db.session.commit()
    return mod


def _make_bundle_course():
    from app.models import Course
    from app.services.bundle_service import N5_BUNDLE_TITLE
    course = Course(title=N5_BUNDLE_TITLE, description="x", is_published=False,
                    is_purchasable=True, price=9.90)
    db.session.add(course)
    db.session.commit()
    return course


class TestModuleDetailBundleGating:
    """10.3: Der Bundle-CTA in module_detail haengt an show_bundle_hint —
    Nicht-Besitzer sehen ihn, Besitzer/Admins nicht."""

    def test_guest_sees_bundle_cta(self, client, app_context):
        """Gast (show_bundle_hint=True) sieht den Bundle-CTA bei paid-Lektionen."""
        _module_with_two_paid("paid-mod-guest")
        db.session.commit()
        body = client.get("/learn/n5/paid-mod-guest").data.decode("utf-8")
        assert "Teil von N5 Komplett" in body

    def test_free_user_sees_bundle_cta(self, auth_client):
        """Free-User ohne Bundle-Kauf (show_bundle_hint=True) sieht den CTA."""
        client, user = auth_client
        _module_with_two_paid("paid-mod-free")
        db.session.commit()
        body = client.get("/learn/n5/paid-mod-free").data.decode("utf-8")
        assert "Teil von N5 Komplett" in body

    def test_bundle_owner_does_not_see_cta(self, auth_client):
        """Bundle-Besitzer (show_bundle_hint=False) sieht den CTA NICHT."""
        from tests.factories import CoursePurchaseFactory
        client, user = auth_client
        _module_with_two_paid("paid-mod-owner")
        course = _make_bundle_course()
        CoursePurchaseFactory(user_id=user.id, course_id=course.id)
        db.session.commit()
        body = client.get("/learn/n5/paid-mod-owner").data.decode("utf-8")
        assert "Teil von N5 Komplett" not in body

    def test_admin_does_not_see_cta(self, admin_client):
        """Admin (show_bundle_hint=False) sieht den CTA NICHT."""
        client, admin = admin_client
        _module_with_two_paid("paid-mod-admin")
        db.session.commit()
        body = client.get("/learn/n5/paid-mod-admin").data.decode("utf-8")
        assert "Teil von N5 Komplett" not in body


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
        LessonFactory(category_id=m.id, is_published=True)          # zweite published Lektion
        LessonFactory(category_id=m.id, is_published=False)        # unpubliziert, zaehlt nicht
        user = UserFactory()
        db.session.flush()
        UserLessonProgressFactory(user_id=user.id, lesson_id=l1.id, is_completed=True)
        db.session.commit()
        done, total = m.completion_for_user(user)
        assert (done, total) == (1, 2)
