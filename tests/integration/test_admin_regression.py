# tests/integration/test_admin_regression.py
"""
Umfassender Regressionstest fuer alle Admin-Funktionen.
Testet Template-Rendering, CRUD-APIs, Spezial-Endpunkte und Zugriffsschutz.
"""

from app import db
from app.models import (
    Kanji, Vocabulary, Grammar,
    LessonContent, LessonPage, Course,
)
from tests.factories import (
    KanaFactory, KanjiFactory, VocabularyFactory, GrammarFactory,
    LessonCategoryFactory, LessonFactory, CourseFactory,
    LessonContentFactory, LessonPageFactory,
    QuizQuestionFactory, QuizOptionFactory,
    LessonPurchaseFactory, PaidLessonFactory,
)


# ══════════════════════════════════════════════════════════════
# 1) ADMIN-TEMPLATE-RENDERING (alle 9 Seiten)
# ══════════════════════════════════════════════════════════════

class TestAdminTemplateRendering:
    """Alle Admin-Seiten muessen als eingeloggter Admin ladbar sein."""

    def test_admin_index(self, admin_client):
        client, _ = admin_client
        resp = client.get("/admin")
        assert resp.status_code == 200

    def test_manage_kana(self, admin_client):
        client, _ = admin_client
        resp = client.get("/admin/manage/kana")
        assert resp.status_code == 200

    def test_manage_kanji(self, admin_client):
        client, _ = admin_client
        resp = client.get("/admin/manage/kanji")
        assert resp.status_code == 200

    def test_manage_vocabulary(self, admin_client):
        client, _ = admin_client
        resp = client.get("/admin/manage/vocabulary")
        assert resp.status_code == 200

    def test_manage_grammar(self, admin_client):
        client, _ = admin_client
        resp = client.get("/admin/manage/grammar")
        assert resp.status_code == 200

    def test_manage_lessons(self, admin_client):
        client, _ = admin_client
        resp = client.get("/admin/manage/lessons")
        assert resp.status_code == 200

    def test_manage_categories(self, admin_client):
        client, _ = admin_client
        resp = client.get("/admin/manage/categories")
        assert resp.status_code == 200

    def test_manage_courses(self, admin_client):
        client, _ = admin_client
        resp = client.get("/admin/manage/courses")
        assert resp.status_code == 200

    def test_manage_approval(self, admin_client):
        client, _ = admin_client
        resp = client.get("/admin/manage/approval")
        assert resp.status_code == 200

    def test_manage_approval_with_pending_items(self, admin_client):
        """Approval-Seite zeigt pending Content korrekt an."""
        client, _ = admin_client
        KanjiFactory(character='試', status='pending_approval', created_by_ai=True)
        VocabularyFactory(word='テスト', status='pending_approval', created_by_ai=True)
        GrammarFactory(title='Test Grammar', status='pending_approval', created_by_ai=True)
        db.session.commit()

        resp = client.get("/admin/manage/approval")
        assert resp.status_code == 200


class TestAdminTemplateAuthGuard:
    """Nicht-Admins werden von allen Admin-Seiten abgewiesen."""

    ADMIN_PAGES = [
        "/admin",
        "/admin/manage/kana",
        "/admin/manage/kanji",
        "/admin/manage/vocabulary",
        "/admin/manage/grammar",
        "/admin/manage/lessons",
        "/admin/manage/categories",
        "/admin/manage/courses",
        "/admin/manage/approval",
    ]

    def test_anonymous_redirected(self, client):
        for page in self.ADMIN_PAGES:
            resp = client.get(page, follow_redirects=False)
            assert resp.status_code == 302, f"Anonymer Zugriff auf {page} nicht blockiert"

    def test_non_admin_redirected(self, auth_client):
        client, _ = auth_client
        for page in self.ADMIN_PAGES:
            resp = client.get(page, follow_redirects=False)
            assert resp.status_code == 302, f"Nicht-Admin auf {page} nicht blockiert"


# ══════════════════════════════════════════════════════════════
# 2) CONTENT APPROVAL / REJECTION
# ══════════════════════════════════════════════════════════════

class TestContentApproval:
    def test_approve_kanji(self, admin_client):
        client, _ = admin_client
        k = KanjiFactory(status='pending_approval', created_by_ai=True)
        db.session.commit()
        resp = client.post(f"/api/admin/content/kanji/{k.id}/approve")
        assert resp.status_code == 200
        db.session.refresh(k)
        assert k.status == 'approved'

    def test_approve_vocabulary(self, admin_client):
        client, _ = admin_client
        v = VocabularyFactory(status='pending_approval', created_by_ai=True)
        db.session.commit()
        resp = client.post(f"/api/admin/content/vocabulary/{v.id}/approve")
        assert resp.status_code == 200
        db.session.refresh(v)
        assert v.status == 'approved'

    def test_approve_grammar(self, admin_client):
        client, _ = admin_client
        g = GrammarFactory(status='pending_approval', created_by_ai=True)
        db.session.commit()
        resp = client.post(f"/api/admin/content/grammar/{g.id}/approve")
        assert resp.status_code == 200
        db.session.refresh(g)
        assert g.status == 'approved'

    def test_reject_kanji_deletes(self, admin_client):
        client, _ = admin_client
        k = KanjiFactory(status='pending_approval', created_by_ai=True)
        db.session.commit()
        kid = k.id
        resp = client.post(f"/api/admin/content/kanji/{kid}/reject")
        assert resp.status_code == 200
        assert Kanji.query.get(kid) is None

    def test_reject_vocabulary_deletes(self, admin_client):
        client, _ = admin_client
        v = VocabularyFactory(status='pending_approval', created_by_ai=True)
        db.session.commit()
        vid = v.id
        resp = client.post(f"/api/admin/content/vocabulary/{vid}/reject")
        assert resp.status_code == 200
        assert Vocabulary.query.get(vid) is None

    def test_invalid_content_type(self, admin_client):
        client, _ = admin_client
        resp = client.post("/api/admin/content/invalid/1/approve")
        assert resp.status_code == 400

    def test_nonexistent_item_404(self, admin_client):
        client, _ = admin_client
        resp = client.post("/api/admin/content/kanji/99999/approve")
        assert resp.status_code == 404


# ══════════════════════════════════════════════════════════════
# 3) CRUD VOLLSTAENDIGKEIT — Fehlende Endpunkte
# ══════════════════════════════════════════════════════════════

class TestKanjiCRUDComplete:
    """Vollstaendiger CRUD-Test fuer Kanji (GET, UPDATE, DELETE einzeln)."""

    def test_get_single_kanji(self, admin_client):
        client, _ = admin_client
        k = KanjiFactory(character='水')
        db.session.commit()
        resp = client.get(f"/api/admin/kanji/{k.id}")
        assert resp.status_code == 200
        assert resp.get_json()["character"] == "水"

    def test_update_kanji(self, admin_client):
        client, _ = admin_client
        k = KanjiFactory(meaning="old")
        db.session.commit()
        resp = client.put(f"/api/admin/kanji/{k.id}/edit", json={"meaning": "new"})
        assert resp.status_code == 200
        db.session.refresh(k)
        assert k.meaning == "new"

    def test_delete_kanji(self, admin_client):
        client, _ = admin_client
        k = KanjiFactory()
        db.session.commit()
        kid = k.id
        resp = client.delete(f"/api/admin/kanji/{kid}/delete")
        assert resp.status_code == 200
        assert Kanji.query.get(kid) is None


class TestVocabularyCRUDComplete:
    def test_get_single_vocabulary(self, admin_client):
        client, _ = admin_client
        v = VocabularyFactory(word='犬', meaning='dog')
        db.session.commit()
        resp = client.get(f"/api/admin/vocabulary/{v.id}")
        assert resp.status_code == 200

    def test_update_vocabulary(self, admin_client):
        client, _ = admin_client
        v = VocabularyFactory(meaning="old")
        db.session.commit()
        resp = client.put(f"/api/admin/vocabulary/{v.id}/edit", json={"meaning": "new"})
        assert resp.status_code == 200
        db.session.refresh(v)
        assert v.meaning == "new"

    def test_delete_vocabulary(self, admin_client):
        client, _ = admin_client
        v = VocabularyFactory()
        db.session.commit()
        vid = v.id
        resp = client.delete(f"/api/admin/vocabulary/{vid}/delete")
        assert resp.status_code == 200
        assert Vocabulary.query.get(vid) is None


class TestGrammarCRUDComplete:
    def test_get_single_grammar(self, admin_client):
        client, _ = admin_client
        g = GrammarFactory(title='Test')
        db.session.commit()
        resp = client.get(f"/api/admin/grammar/{g.id}")
        assert resp.status_code == 200

    def test_update_grammar(self, admin_client):
        client, _ = admin_client
        g = GrammarFactory()
        db.session.commit()
        resp = client.put(f"/api/admin/grammar/{g.id}/edit", json={"explanation": "Updated"})
        assert resp.status_code == 200
        db.session.refresh(g)
        assert g.explanation == "Updated"

    def test_delete_grammar(self, admin_client):
        client, _ = admin_client
        g = GrammarFactory()
        db.session.commit()
        gid = g.id
        resp = client.delete(f"/api/admin/grammar/{gid}/delete")
        assert resp.status_code == 200
        assert Grammar.query.get(gid) is None


class TestCategoryCRUDComplete:
    def test_get_single_category(self, admin_client):
        client, _ = admin_client
        cat = LessonCategoryFactory()
        db.session.commit()
        resp = client.get(f"/api/admin/categories/{cat.id}")
        assert resp.status_code == 200

    def test_update_category(self, admin_client):
        client, _ = admin_client
        cat = LessonCategoryFactory()
        db.session.commit()
        resp = client.put(f"/api/admin/categories/{cat.id}/edit",
                          json={"name": "Updated Name"})
        assert resp.status_code == 200
        db.session.refresh(cat)
        assert cat.name == "Updated Name"

    def test_create_duplicate_category_fails(self, admin_client):
        client, _ = admin_client
        LessonCategoryFactory(name="Duplicate")
        db.session.commit()
        resp = client.post("/api/admin/categories/new",
                           json={"name": "Duplicate"})
        assert resp.status_code == 400


class TestCourseCRUDComplete:
    def test_get_single_course(self, admin_client):
        client, _ = admin_client
        c = CourseFactory()
        db.session.commit()
        resp = client.get(f"/api/admin/courses/{c.id}")
        assert resp.status_code == 200

    def test_update_course(self, admin_client):
        client, _ = admin_client
        c = CourseFactory()
        db.session.commit()
        resp = client.put(f"/api/admin/courses/{c.id}/edit",
                          json={"title": "Updated"})
        assert resp.status_code == 200

    def test_delete_course(self, admin_client):
        client, _ = admin_client
        c = CourseFactory()
        db.session.commit()
        cid = c.id
        resp = client.delete(f"/api/admin/courses/{cid}/delete")
        assert resp.status_code == 200
        assert Course.query.get(cid) is None


# ══════════════════════════════════════════════════════════════
# 4) LESSON CONTENT MANIPULATION
# ══════════════════════════════════════════════════════════════

class TestLessonContentMove:
    def test_move_content_down(self, admin_client):
        client, _ = admin_client
        lesson = LessonFactory()
        db.session.commit()
        first = LessonContentFactory(lesson_id=lesson.id, order_index=0, page_number=1)
        LessonContentFactory(lesson_id=lesson.id, order_index=1, page_number=1)
        db.session.commit()

        resp = client.post(
            f"/api/admin/lessons/{lesson.id}/content/{first.id}/move",
            json={"direction": "down"},
        )
        assert resp.status_code == 200

    def test_move_content_up(self, admin_client):
        client, _ = admin_client
        lesson = LessonFactory()
        db.session.commit()
        LessonContentFactory(lesson_id=lesson.id, order_index=0, page_number=1)
        c2 = LessonContentFactory(lesson_id=lesson.id, order_index=1, page_number=1)
        db.session.commit()

        resp = client.post(
            f"/api/admin/lessons/{lesson.id}/content/{c2.id}/move",
            json={"direction": "up"},
        )
        assert resp.status_code == 200

    def test_move_content_invalid_direction(self, admin_client):
        client, _ = admin_client
        lesson = LessonFactory()
        db.session.commit()
        c = LessonContentFactory(lesson_id=lesson.id)
        db.session.commit()

        resp = client.post(
            f"/api/admin/lessons/{lesson.id}/content/{c.id}/move",
            json={"direction": "left"},
        )
        assert resp.status_code == 400

    def test_move_first_item_up_fails(self, admin_client):
        client, _ = admin_client
        lesson = LessonFactory()
        db.session.commit()
        c = LessonContentFactory(lesson_id=lesson.id, order_index=0, page_number=1)
        db.session.commit()

        resp = client.post(
            f"/api/admin/lessons/{lesson.id}/content/{c.id}/move",
            json={"direction": "up"},
        )
        assert resp.status_code == 400


class TestLessonContentReorder:
    def test_reorder_page_content(self, admin_client):
        client, _ = admin_client
        lesson = LessonFactory()
        db.session.commit()
        c1 = LessonContentFactory(lesson_id=lesson.id, order_index=0, page_number=1)
        c2 = LessonContentFactory(lesson_id=lesson.id, order_index=1, page_number=1)
        c3 = LessonContentFactory(lesson_id=lesson.id, order_index=2, page_number=1)
        db.session.commit()

        resp = client.post(
            f"/api/admin/lessons/{lesson.id}/pages/1/reorder",
            json={"content_ids": [c3.id, c1.id, c2.id]},
        )
        assert resp.status_code == 200

    def test_reorder_missing_ids(self, admin_client):
        client, _ = admin_client
        lesson = LessonFactory()
        db.session.commit()

        resp = client.post(
            f"/api/admin/lessons/{lesson.id}/pages/1/reorder",
            json={"content_ids": []},
        )
        assert resp.status_code == 400

    def test_force_reorder(self, admin_client):
        client, _ = admin_client
        lesson = LessonFactory()
        db.session.commit()
        LessonContentFactory(lesson_id=lesson.id, order_index=0, page_number=1)
        LessonContentFactory(lesson_id=lesson.id, order_index=5, page_number=1)
        db.session.commit()

        resp = client.post(f"/api/admin/lessons/{lesson.id}/content/force-reorder")
        assert resp.status_code == 200


class TestLessonContentDuplicate:
    def test_duplicate_text_content(self, admin_client):
        client, _ = admin_client
        lesson = LessonFactory()
        db.session.commit()
        c = LessonContentFactory(
            lesson_id=lesson.id, content_type="text",
            title="Original", content_text="Hello",
        )
        db.session.commit()

        resp = client.post(f"/api/admin/content/{c.id}/duplicate")
        assert resp.status_code == 201
        data = resp.get_json()
        assert "Copy" in (data.get("title") or "")

    def test_duplicate_interactive_content(self, admin_client):
        client, _ = admin_client
        lesson = LessonFactory()
        db.session.commit()
        c = LessonContentFactory(
            lesson_id=lesson.id, content_type="text",
            is_interactive=True, title="Quiz Block",
        )
        db.session.commit()
        q = QuizQuestionFactory(lesson_content_id=c.id)
        db.session.commit()
        QuizOptionFactory(question_id=q.id, option_text="A", is_correct=True)
        QuizOptionFactory(question_id=q.id, option_text="B")
        db.session.commit()

        resp = client.post(f"/api/admin/content/{c.id}/duplicate")
        assert resp.status_code == 201
        # Pruefen dass Quiz-Fragen dupliziert wurden
        new_id = resp.get_json()["id"]
        new_content = LessonContent.query.get(new_id)
        assert len(new_content.quiz_questions) == 1
        assert len(new_content.quiz_questions[0].options) == 2


class TestContentPreviewAndDetails:
    def test_content_preview_text(self, admin_client):
        client, _ = admin_client
        lesson = LessonFactory()
        db.session.commit()
        c = LessonContentFactory(lesson_id=lesson.id, content_type="text")
        db.session.commit()

        resp = client.get(f"/api/admin/content/{c.id}/preview")
        assert resp.status_code == 200

    def test_content_preview_with_reference(self, admin_client):
        client, _ = admin_client
        kana = KanaFactory(character='あ')
        lesson = LessonFactory()
        db.session.commit()
        c = LessonContentFactory(
            lesson_id=lesson.id, content_type="kana", content_id=kana.id,
        )
        db.session.commit()

        resp = client.get(f"/api/admin/content/{c.id}/preview")
        assert resp.status_code == 200

    def test_content_details(self, admin_client):
        client, _ = admin_client
        lesson = LessonFactory()
        db.session.commit()
        c = LessonContentFactory(lesson_id=lesson.id)
        db.session.commit()

        resp = client.get(f"/api/admin/content/{c.id}")
        assert resp.status_code == 200

    def test_content_update(self, admin_client):
        client, _ = admin_client
        lesson = LessonFactory()
        db.session.commit()
        c = LessonContentFactory(
            lesson_id=lesson.id, content_type="text", content_text="old",
        )
        db.session.commit()

        resp = client.put(
            f"/api/admin/content/{c.id}/edit",
            json={"content_text": "new text"},
        )
        assert resp.status_code == 200


class TestContentOptions:
    def test_kana_options(self, admin_client):
        client, _ = admin_client
        KanaFactory()
        db.session.commit()
        resp = client.get("/api/admin/content-options/kana")
        assert resp.status_code == 200
        assert len(resp.get_json()) >= 1

    def test_kanji_options(self, admin_client):
        client, _ = admin_client
        KanjiFactory()
        db.session.commit()
        resp = client.get("/api/admin/content-options/kanji")
        assert resp.status_code == 200

    def test_vocabulary_options(self, admin_client):
        client, _ = admin_client
        VocabularyFactory()
        db.session.commit()
        resp = client.get("/api/admin/content-options/vocabulary")
        assert resp.status_code == 200

    def test_grammar_options(self, admin_client):
        client, _ = admin_client
        GrammarFactory()
        db.session.commit()
        resp = client.get("/api/admin/content-options/grammar")
        assert resp.status_code == 200

    def test_invalid_type(self, admin_client):
        client, _ = admin_client
        resp = client.get("/api/admin/content-options/invalid")
        assert resp.status_code == 400


# ══════════════════════════════════════════════════════════════
# 5) LESSON MANAGEMENT (Move, Reorder)
# ══════════════════════════════════════════════════════════════

class TestLessonMove:
    def test_move_lesson_down(self, admin_client):
        client, _ = admin_client
        first = LessonFactory(order_index=0)
        LessonFactory(order_index=1)
        db.session.commit()

        resp = client.post(
            f"/api/admin/lessons/{first.id}/move",
            json={"direction": "down"},
        )
        assert resp.status_code == 200

    def test_move_lesson_up(self, admin_client):
        client, _ = admin_client
        LessonFactory(order_index=0)
        second = LessonFactory(order_index=1)
        db.session.commit()

        resp = client.post(
            f"/api/admin/lessons/{second.id}/move",
            json={"direction": "up"},
        )
        assert resp.status_code == 200

    def test_move_first_up_fails(self, admin_client):
        client, _ = admin_client
        lesson = LessonFactory(order_index=0)
        db.session.commit()

        resp = client.post(
            f"/api/admin/lessons/{lesson.id}/move",
            json={"direction": "up"},
        )
        assert resp.status_code == 400

    def test_reorder_lessons(self, admin_client):
        client, _ = admin_client
        l1 = LessonFactory(order_index=0)
        l2 = LessonFactory(order_index=1)
        l3 = LessonFactory(order_index=2)
        db.session.commit()

        resp = client.post(
            "/api/admin/lessons/reorder",
            json={"lesson_ids": [l3.id, l1.id, l2.id]},
        )
        assert resp.status_code == 200
        db.session.refresh(l3)
        assert l3.order_index == 0


# ══════════════════════════════════════════════════════════════
# 6) LESSON PAGE MANAGEMENT
# ══════════════════════════════════════════════════════════════

class TestLessonPageManagement:
    def test_update_page(self, admin_client):
        client, _ = admin_client
        lesson = LessonFactory()
        db.session.commit()
        LessonPageFactory(lesson_id=lesson.id, page_number=1, title="Old")
        db.session.commit()

        resp = client.put(
            f"/api/admin/lessons/{lesson.id}/pages/1",
            json={"title": "New Title", "description": "Desc"},
        )
        assert resp.status_code == 200

    def test_update_nonexistent_page_creates_it(self, admin_client):
        client, _ = admin_client
        lesson = LessonFactory()
        db.session.commit()

        resp = client.put(
            f"/api/admin/lessons/{lesson.id}/pages/5",
            json={"title": "New Page 5"},
        )
        assert resp.status_code == 200
        assert LessonPage.query.filter_by(
            lesson_id=lesson.id, page_number=5
        ).first() is not None

    def test_delete_page(self, admin_client):
        client, _ = admin_client
        lesson = LessonFactory()
        db.session.commit()
        LessonPageFactory(lesson_id=lesson.id, page_number=2)
        LessonContentFactory(lesson_id=lesson.id, page_number=2)
        db.session.commit()

        resp = client.delete(f"/api/admin/lessons/{lesson.id}/pages/2/delete")
        assert resp.status_code == 200
        assert LessonPage.query.filter_by(
            lesson_id=lesson.id, page_number=2
        ).first() is None

    def test_delete_nonexistent_page_404(self, admin_client):
        client, _ = admin_client
        lesson = LessonFactory()
        db.session.commit()

        resp = client.delete(f"/api/admin/lessons/{lesson.id}/pages/99/delete")
        assert resp.status_code == 404


# ══════════════════════════════════════════════════════════════
# 7) INTERACTIVE CONTENT (Quiz)
# ══════════════════════════════════════════════════════════════

class TestInteractiveContent:
    def test_add_quiz_content(self, admin_client):
        client, _ = admin_client
        lesson = LessonFactory()
        db.session.commit()

        resp = client.post(
            f"/api/admin/lessons/{lesson.id}/content/interactive",
            json={
                "interactive_type": "multiple_choice",
                "title": "Vocabulary Quiz",
                "page_number": 1,
                "question_text": "What is 犬?",
                "explanation": "犬 means dog",
                "options": [
                    {"text": "dog", "is_correct": True},
                    {"text": "cat", "is_correct": False},
                ],
            },
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data.get("is_interactive") is True

    def test_add_quiz_missing_type_fails(self, admin_client):
        client, _ = admin_client
        lesson = LessonFactory()
        db.session.commit()

        resp = client.post(
            f"/api/admin/lessons/{lesson.id}/content/interactive",
            json={},
        )
        assert resp.status_code == 400


# ══════════════════════════════════════════════════════════════
# 8) REVENUE & PURCHASE STATS
# ══════════════════════════════════════════════════════════════

class TestRevenueStats:
    def test_revenue_stats_empty(self, admin_client):
        client, _ = admin_client
        resp = client.get("/api/admin/revenue-stats")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total_revenue"] == 0
        assert data["total_purchases"] == 0

    def test_revenue_stats_with_purchases(self, admin_client):
        client, admin = admin_client
        lesson = PaidLessonFactory()
        db.session.commit()
        LessonPurchaseFactory(user_id=admin.id, lesson_id=lesson.id, price_paid=29.0)
        db.session.commit()

        resp = client.get("/api/admin/revenue-stats")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total_revenue"] == 29.0
        assert data["total_purchases"] == 1

    def test_list_all_purchases(self, admin_client):
        client, admin = admin_client
        lesson = PaidLessonFactory()
        db.session.commit()
        LessonPurchaseFactory(user_id=admin.id, lesson_id=lesson.id)
        db.session.commit()

        resp = client.get("/api/admin/purchases")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] >= 1

    def test_list_lesson_purchases(self, admin_client):
        client, admin = admin_client
        lesson = PaidLessonFactory()
        db.session.commit()
        LessonPurchaseFactory(user_id=admin.id, lesson_id=lesson.id)
        db.session.commit()

        resp = client.get(f"/api/admin/lessons/{lesson.id}/purchases")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total_purchases"] >= 1


# ══════════════════════════════════════════════════════════════
# 9) LESSON EXPORT/IMPORT
# ══════════════════════════════════════════════════════════════

class TestLessonExport:
    def test_export_lesson_json(self, admin_client):
        client, _ = admin_client
        lesson = LessonFactory(title="Export Test")
        db.session.commit()
        LessonContentFactory(lesson_id=lesson.id, content_type="text", content_text="Hello")
        db.session.commit()

        resp = client.get(f"/api/admin/lessons/{lesson.id}/export")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["title"] == "Export Test"

    def test_export_nonexistent_lesson_404(self, admin_client):
        client, _ = admin_client
        resp = client.get("/api/admin/lessons/99999/export")
        assert resp.status_code == 404


class TestLessonImport:
    def test_import_lesson_json(self, admin_client):
        import io
        import json as json_mod

        client, _ = admin_client
        # Zuerst eine Lektion exportieren
        lesson = LessonFactory(title="To Export")
        db.session.commit()
        LessonContentFactory(lesson_id=lesson.id, content_type="text")
        db.session.commit()

        export_resp = client.get(f"/api/admin/lessons/{lesson.id}/export")
        assert export_resp.status_code == 200
        export_data = export_resp.get_json()

        # Import erwartet Datei-Upload (multipart/form-data)
        json_bytes = json_mod.dumps(export_data).encode("utf-8")
        import_resp = client.post(
            "/api/admin/lessons/import",
            data={
                "file": (io.BytesIO(json_bytes), "lesson_export.json"),
            },
            content_type="multipart/form-data",
        )
        assert import_resp.status_code in (200, 201)


# ══════════════════════════════════════════════════════════════
# 10) BULK OPERATIONS
# ══════════════════════════════════════════════════════════════

class TestBulkOperations:
    def test_bulk_delete_content(self, admin_client):
        client, _ = admin_client
        lesson = LessonFactory()
        db.session.commit()
        c1 = LessonContentFactory(lesson_id=lesson.id, page_number=1)
        c2 = LessonContentFactory(lesson_id=lesson.id, page_number=1)
        db.session.commit()

        resp = client.delete(
            f"/api/admin/lessons/{lesson.id}/content/bulk-delete",
            json={"content_ids": [c1.id, c2.id]},
        )
        assert resp.status_code == 200

    def test_bulk_duplicate_content(self, admin_client):
        client, _ = admin_client
        lesson = LessonFactory()
        db.session.commit()
        c1 = LessonContentFactory(lesson_id=lesson.id, content_type="text", title="A")
        db.session.commit()

        resp = client.post(
            f"/api/admin/lessons/{lesson.id}/content/bulk-duplicate",
            json={"content_ids": [c1.id]},
        )
        assert resp.status_code in (200, 201)


# ══════════════════════════════════════════════════════════════
# 11) FLASK-ADMIN CRUD-PANEL REGRESSION
# ══════════════════════════════════════════════════════════════

class TestFlaskAdminCRUDRegression:
    """Prueft alle Flask-Admin Views auf Erreichbarkeit und Basisfunktionen."""

    VIEWS = [
        "/admin-panel/",
        "/admin-panel/admin_kana/",
        "/admin-panel/admin_kanji/",
        "/admin-panel/admin_vocabulary/",
        "/admin-panel/admin_grammar/",
        "/admin-panel/admin_categories/",
        "/admin-panel/admin_lessons/",
        "/admin-panel/admin_courses/",
        "/admin-panel/admin_users/",
    ]

    def test_all_views_accessible(self, admin_client):
        client, _ = admin_client
        for view_url in self.VIEWS:
            resp = client.get(view_url)
            assert resp.status_code == 200, f"Flask-Admin View {view_url} nicht erreichbar"

    def test_all_views_blocked_for_non_admin(self, auth_client):
        client, _ = auth_client
        for view_url in self.VIEWS:
            resp = client.get(view_url, follow_redirects=False)
            assert resp.status_code == 302, f"Flask-Admin {view_url} nicht geschuetzt"

    def test_edit_vocabulary_via_flask_admin(self, admin_client):
        """Flask-Admin Edit-View fuer Vocabulary erreichbar."""
        client, _ = admin_client
        v = VocabularyFactory()
        db.session.commit()
        resp = client.get(f"/admin-panel/admin_vocabulary/edit/?id={v.id}")
        assert resp.status_code == 200

    def test_detail_kanji_via_flask_admin(self, admin_client):
        """Flask-Admin Detail-View fuer Kanji."""
        client, _ = admin_client
        k = KanjiFactory()
        db.session.commit()
        resp = client.get(f"/admin-panel/admin_kanji/details/?id={k.id}")
        assert resp.status_code == 200

    def test_flask_admin_create_grammar(self, admin_client):
        """Grammatik-Eintrag ueber Flask-Admin erstellen."""
        client, _ = admin_client
        resp = client.post("/admin-panel/admin_grammar/new/", data={
            "title": "Flask-Admin Grammar Test",
            "explanation": "Test explanation",
            "structure": "N + は",
            "jlpt_level": "5",
            "status": "approved",
            "created_by_ai": "y",
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert Grammar.query.filter_by(title="Flask-Admin Grammar Test").first() is not None


# ══════════════════════════════════════════════════════════════
# 12) SIDEBAR-NAVIGATION & CROSS-LINKS
# ══════════════════════════════════════════════════════════════

class TestSidebarNavigation:
    """Prueft dass alle Sidebar-Links im Admin-Template gueltig sind."""

    def test_sidebar_contains_crud_panel_link(self, admin_client):
        client, _ = admin_client
        resp = client.get("/admin")
        html = resp.data.decode()
        assert "admin_panel" in html or "CRUD-Panel" in html

    def test_flask_admin_index_contains_custom_admin_link(self, admin_client):
        client, _ = admin_client
        resp = client.get("/admin-panel/")
        html = resp.data.decode()
        assert "/admin" in html


# ══════════════════════════════════════════════════════════════
# 13) API AUTH GUARD — Nicht-Admins
# ══════════════════════════════════════════════════════════════

class TestAPIAuthGuard:
    """Stellt sicher, dass alle Admin-APIs fuer Nicht-Admins blockiert sind."""

    API_ENDPOINTS = [
        ("GET", "/api/admin/kana"),
        ("GET", "/api/admin/kanji"),
        ("GET", "/api/admin/vocabulary"),
        ("GET", "/api/admin/grammar"),
        ("GET", "/api/admin/categories"),
        ("GET", "/api/admin/courses"),
        ("GET", "/api/admin/lessons"),
        ("GET", "/api/admin/purchases"),
        ("GET", "/api/admin/revenue-stats"),
        ("GET", "/api/admin/content-options/kana"),
    ]

    def test_non_admin_blocked_from_all_apis(self, auth_client):
        client, _ = auth_client
        for method, url in self.API_ENDPOINTS:
            if method == "GET":
                resp = client.get(url, follow_redirects=False)
            else:
                resp = client.post(url, json={}, follow_redirects=False)
            assert resp.status_code in (302, 403), \
                f"Nicht-Admin auf {method} {url} nicht blockiert (Status {resp.status_code})"

    def test_anonymous_blocked_from_all_apis(self, client):
        for method, url in self.API_ENDPOINTS:
            if method == "GET":
                resp = client.get(url, follow_redirects=False)
            else:
                resp = client.post(url, json={}, follow_redirects=False)
            assert resp.status_code in (302, 401), \
                f"Anonym auf {method} {url} nicht blockiert (Status {resp.status_code})"
