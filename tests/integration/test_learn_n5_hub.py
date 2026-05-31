# tests/integration/test_learn_n5_hub.py
"""Integrationstests fuer H1: /learn/n5 ist eine eigene indexierbare 200-Hub-Seite
(learn_n5.html) statt eines 301-Fragments auf /#lernpfad.

Ziel: die generischste N5-URL sammelt eigene Ranking-Autoritaet. Self-Canonical
auf /learn/n5; die Modul-/Lernpfad-Logik teilt sie sich mit der Startseite.
"""
from app import db
from tests.factories import LessonCategoryFactory, LessonFactory


def _make_module(slug, display_order, name):
    return LessonCategoryFactory(
        slug=slug, jlpt_level=5, display_order=display_order,
        name=name, icon_emoji="📖",
    )


class TestLearnN5Hub:
    def test_returns_200_not_301(self, client, app_context):
        """GET /learn/n5 → 200 (kein Redirect mehr)."""
        resp = client.get("/learn/n5", follow_redirects=False)
        assert resp.status_code == 200

    def test_renders_lernpfad_content(self, client, app_context):
        """Die Hub-Seite enthaelt Lernpfad-/Modul-Inhalt."""
        mod = _make_module("n5-hiragana", display_order=1, name="Hiragana")
        db.session.flush()
        LessonFactory(category_id=mod.id, is_published=True,
                      title="Hiragana 1", instruction_language="german",
                      price=0.0, allow_guest_access=True)
        db.session.commit()

        body = client.get("/learn/n5").data.decode("utf-8")
        assert "Lernpfad" in body or "JLPT N5" in body
        assert "Hiragana" in body

    def test_self_canonical_points_to_hub(self, client, app_context):
        """Self-Canonical zeigt auf /learn/n5 (nicht auf das Home-Fragment)."""
        body = client.get("/learn/n5").data.decode("utf-8")
        assert 'rel="canonical"' in body
        assert "/learn/n5" in body
        # Kein 301-Fragment-Redirect-Verhalten mehr
        assert "#lernpfad" not in body or "/learn/n5" in body

    def test_guest_module_cta_links_into_guest_lesson(self, client, app_context):
        """D4-Konsistenz: fuer Gaeste verlinkt der Modul-CTA in die erste
        gratis+guest Lektion, nicht in eine gesperrte erste Lektion."""
        mod = _make_module("n5-hiragana", display_order=1, name="Hiragana")
        db.session.flush()
        # Erste Lektion gesperrt (paid), zweite gratis+guest
        LessonFactory(category_id=mod.id, is_published=True, order_index=0,
                      title="Gesperrt", instruction_language="german",
                      price=5.0, allow_guest_access=False)
        guest = LessonFactory(category_id=mod.id, is_published=True, order_index=1,
                              title="Gratis Gast", instruction_language="german",
                              price=0.0, allow_guest_access=True)
        db.session.commit()

        body = client.get("/learn/n5").data.decode("utf-8")
        assert f"/lessons/{guest.id}" in body

    def test_n4_still_404(self, client, app_context):
        """Andere Level behalten ihr Verhalten (N4 → 404, noch kein Content)."""
        assert client.get("/learn/n4").status_code == 404
