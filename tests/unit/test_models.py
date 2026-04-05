# tests/unit/test_models.py
"""
Phase 1: Unit-Tests für alle SQLAlchemy-Models.
Testkonzept-IDs: U-M01 bis U-M20
"""

import json
import pytest
from app import db
from app.models import (
    User, Kana, Kanji, Vocabulary, Grammar,
    LessonCategory, Lesson, LessonContent, LessonPage,
    LessonPrerequisite, Course, LessonPurchase, CoursePurchase,
    PaymentTransaction, QuizQuestion, QuizOption, UserLessonProgress,
    UserQuizAnswer, course_lessons,
)
from tests.factories import (
    UserFactory, AdminUserFactory, PremiumUserFactory,
    KanaFactory, KanjiFactory, VocabularyFactory, GrammarFactory,
    LessonCategoryFactory, LessonFactory, PaidLessonFactory, PremiumLessonFactory,
    LessonPageFactory, LessonContentFactory,
    CourseFactory, PaidCourseFactory,
    LessonPurchaseFactory, CoursePurchaseFactory, PaymentTransactionFactory,
    QuizQuestionFactory, QuizOptionFactory, UserLessonProgressFactory,
)


# ── U-M01: User – Passwort-Hashing ──────────────────────────

class TestUserPasswordHashing:
    def test_set_password_hashes(self, app_context):
        """U-M01: set_password erzeugt einen Hash, nicht den Klartext."""
        user = UserFactory(password="Geheim123!")
        assert user.password_hash != "Geheim123!"
        assert user.password_hash is not None

    def test_check_password_correct(self, app_context):
        """U-M01: check_password gibt True für korrektes Passwort."""
        user = UserFactory(password="Geheim123!")
        assert user.check_password("Geheim123!") is True

    def test_check_password_wrong(self, app_context):
        """U-M01: check_password gibt False für falsches Passwort."""
        user = UserFactory(password="Geheim123!")
        assert user.check_password("Falsch!") is False

    def test_different_users_different_hashes(self, app_context):
        """Zwei User mit gleichem Passwort haben verschiedene Hashes."""
        u1 = UserFactory(password="Same123!")
        u2 = UserFactory(password="Same123!")
        assert u1.password_hash != u2.password_hash


# ── U-M02: User – Standardwerte ─────────────────────────────

class TestUserDefaults:
    def test_default_subscription_level(self, app_context):
        """U-M02: Neuer User hat subscription_level='free'."""
        user = UserFactory()
        assert user.subscription_level == "free"

    def test_default_is_admin(self, app_context):
        """U-M02: Neuer User ist kein Admin."""
        user = UserFactory()
        assert user.is_admin is False

    def test_admin_factory(self, app_context):
        """AdminUserFactory erzeugt Admin."""
        admin = AdminUserFactory()
        assert admin.is_admin is True

    def test_premium_factory(self, app_context):
        """PremiumUserFactory erzeugt Premium-User."""
        premium = PremiumUserFactory()
        assert premium.subscription_level == "premium"

    def test_user_repr(self, app_context):
        """User __repr__ enthält Username."""
        user = UserFactory(username="testuser_repr")
        assert "testuser_repr" in repr(user)


# ── U-M03: User – Unique Constraints ────────────────────────

class TestUserUniqueConstraints:
    def test_duplicate_username_raises(self, app_context):
        """U-M03: Doppelter Username wirft IntegrityError."""
        UserFactory(username="duplicate")
        db.session.commit()
        with pytest.raises(Exception):
            UserFactory(username="duplicate")
            db.session.commit()

    def test_duplicate_email_raises(self, app_context):
        """U-M03: Doppelte Email wirft IntegrityError."""
        UserFactory(email="same@test.com")
        db.session.commit()
        with pytest.raises(Exception):
            UserFactory(email="same@test.com")
            db.session.commit()


# ── U-M04 bis U-M07: Kana, Kanji, Vocabulary, Grammar ──────

class TestContentModels:
    def test_kana_creation(self, app_context):
        """U-M04: Kana-Erstellung mit Grundfeldern."""
        kana = KanaFactory(character="あ", romanization="a", type="hiragana")
        assert kana.character == "あ"
        assert kana.romanization == "a"
        assert kana.type == "hiragana"

    def test_kanji_creation(self, app_context):
        """U-M05: Kanji-Erstellung mit AI-Flag."""
        kanji = KanjiFactory(created_by_ai=True, status="pending_approval")
        assert kanji.created_by_ai is True
        assert kanji.status == "pending_approval"

    def test_vocabulary_creation(self, app_context):
        """U-M06: Vocabulary-Erstellung."""
        vocab = VocabularyFactory()
        assert vocab.word is not None
        assert vocab.reading is not None
        assert vocab.status == "approved"

    def test_grammar_creation(self, app_context):
        """U-M07: Grammar-Erstellung."""
        grammar = GrammarFactory()
        assert grammar.title is not None
        assert grammar.structure == "Subject + は + Predicate"


# ── U-M08: Lesson – Zugriffskontrolle (is_accessible_to_user) ──

class TestLessonAccessControl:
    def test_guest_access_free_lesson_with_guest_flag(self, app_context):
        """U-M08: Gast kann kostenlose Lektion mit allow_guest_access öffnen."""
        lesson = LessonFactory(price=0.0, allow_guest_access=True)
        db.session.commit()
        accessible, msg = lesson.is_accessible_to_user(None)
        assert accessible is True

    def test_guest_blocked_without_guest_flag(self, app_context):
        """U-M08: Gast wird ohne allow_guest_access blockiert."""
        lesson = LessonFactory(price=0.0, allow_guest_access=False)
        db.session.commit()
        accessible, msg = lesson.is_accessible_to_user(None)
        assert accessible is False
        assert "Login required" in msg

    def test_free_lesson_accessible_to_authenticated(self, app_context):
        """U-M08: Eingeloggter User kann kostenlose Lektion öffnen."""
        user = UserFactory()
        lesson = LessonFactory(price=0.0)
        db.session.commit()
        accessible, msg = lesson.is_accessible_to_user(user)
        assert accessible is True

    def test_paid_lesson_blocked_without_purchase(self, app_context):
        """U-M08: Kostenpflichtige Lektion blockiert ohne Kauf."""
        user = UserFactory()
        lesson = PaidLessonFactory()
        db.session.commit()
        accessible, msg = lesson.is_accessible_to_user(user)
        assert accessible is False
        assert "Purchase required" in msg

    def test_paid_lesson_accessible_with_purchase(self, app_context):
        """U-M08: Kostenpflichtige Lektion zugänglich nach Kauf."""
        user = UserFactory()
        lesson = PaidLessonFactory()
        db.session.commit()
        LessonPurchaseFactory(user_id=user.id, lesson_id=lesson.id)
        db.session.commit()
        accessible, msg = lesson.is_accessible_to_user(user)
        assert accessible is True

    def test_paid_lesson_accessible_via_course_purchase(self, app_context):
        """U-M08: Kostenpflichtige Lektion zugänglich via Kurs-Kauf."""
        user = UserFactory()
        lesson = PaidLessonFactory()
        course = PaidCourseFactory()
        db.session.commit()
        # Lektion dem Kurs zuordnen
        db.session.execute(
            course_lessons.insert().values(course_id=course.id, lesson_id=lesson.id)
        )
        CoursePurchaseFactory(user_id=user.id, course_id=course.id)
        db.session.commit()
        accessible, msg = lesson.is_accessible_to_user(user)
        assert accessible is True
        assert "course" in msg.lower()

    def test_premium_lesson_blocked_for_free_user(self, app_context):
        """U-M08: Premium-Lektion blockiert für Free-User.
        Hinweis: Der Legacy-Premium-Check (lesson_type='premium') wird nur
        erreicht wenn price>0 und is_purchasable=False. Event Listener setzt
        lesson_type='paid' bei price>0, daher manuell auf 'premium' setzen.
        """
        user = UserFactory(subscription_level="free")
        # price>0 + is_purchasable=False → Code erreicht den Premium-Check
        lesson = LessonFactory(price=10.0, is_purchasable=False)
        db.session.flush()
        from sqlalchemy import update
        db.session.execute(
            update(Lesson).where(Lesson.id == lesson.id).values(lesson_type="premium")
        )
        db.session.expire(lesson)
        db.session.commit()
        accessible, msg = lesson.is_accessible_to_user(user)
        assert accessible is False
        assert "Premium" in msg

    def test_premium_lesson_accessible_for_premium_user(self, app_context):
        """U-M08: Premium-Lektion zugänglich für Premium-User."""
        user = PremiumUserFactory()
        lesson = LessonFactory(price=10.0, is_purchasable=False)
        db.session.flush()
        from sqlalchemy import update
        db.session.execute(
            update(Lesson).where(Lesson.id == lesson.id).values(lesson_type="premium")
        )
        db.session.expire(lesson)
        db.session.commit()
        accessible, msg = lesson.is_accessible_to_user(user)
        assert accessible is True


# ── U-M09: Lesson – Voraussetzungen ─────────────────────────

class TestLessonPrerequisites:
    def test_prerequisite_blocks_access(self, app_context):
        """U-M09: Voraussetzung blockiert Zugang."""
        user = UserFactory()
        prereq = LessonFactory(price=0.0)
        lesson = LessonFactory(price=0.0)
        db.session.commit()
        prereq_rel = LessonPrerequisite(lesson_id=lesson.id, prerequisite_lesson_id=prereq.id)
        db.session.add(prereq_rel)
        db.session.commit()
        # Lesson-Objekt neu laden damit prerequisites geladen werden
        db.session.expire(lesson)
        accessible, msg = lesson.is_accessible_to_user(user)
        assert accessible is False
        assert "Must complete" in msg

    def test_prerequisite_fulfilled(self, app_context):
        """U-M09: Erfüllte Voraussetzung erlaubt Zugang."""
        user = UserFactory()
        prereq = LessonFactory(price=0.0)
        lesson = LessonFactory(price=0.0)
        db.session.commit()
        LessonPrerequisite(lesson_id=lesson.id, prerequisite_lesson_id=prereq.id)
        db.session.flush()
        # Voraussetzung als erledigt markieren
        progress = UserLessonProgressFactory(
            user_id=user.id, lesson_id=prereq.id, is_completed=True
        )
        db.session.commit()
        accessible, msg = lesson.is_accessible_to_user(user)
        assert accessible is True


# ── U-M10: LessonContent – get_content_data ─────────────────

class TestLessonContentData:
    def test_get_content_data_kana(self, app_context):
        """U-M10: get_content_data liefert Kana-Objekt."""
        kana = KanaFactory()
        lesson = LessonFactory()
        db.session.commit()
        content = LessonContentFactory(
            lesson_id=lesson.id, content_type="kana", content_id=kana.id
        )
        db.session.commit()
        result = content.get_content_data()
        assert result is not None
        assert result.character == kana.character

    def test_get_content_data_text(self, app_context):
        """U-M10: get_content_data liefert Dict für Text-Inhalte."""
        lesson = LessonFactory()
        db.session.commit()
        content = LessonContentFactory(
            lesson_id=lesson.id,
            content_type="text",
            title="Test Title",
            content_text="Test Text",
        )
        db.session.commit()
        result = content.get_content_data()
        assert isinstance(result, dict)
        assert result["title"] == "Test Title"
        assert result["content_text"] == "Test Text"

    def test_get_content_data_none_for_unknown(self, app_context):
        """U-M10: get_content_data gibt None für unbekannten Typ."""
        lesson = LessonFactory()
        db.session.commit()
        content = LessonContentFactory(
            lesson_id=lesson.id, content_type="kana", content_id=99999
        )
        db.session.commit()
        result = content.get_content_data()
        assert result is None


# ── U-M11: UserLessonProgress – JSON-Content-Progress ───────

class TestUserLessonProgress:
    def test_get_set_content_progress(self, app_context):
        """U-M11: Content-Progress kann als Dict gesetzt/gelesen werden."""
        user = UserFactory()
        lesson = LessonFactory()
        db.session.commit()
        progress = UserLessonProgressFactory(user_id=user.id, lesson_id=lesson.id)
        db.session.commit()

        progress.set_content_progress({"1": True, "2": False})
        result = progress.get_content_progress()
        assert result["1"] is True
        assert result["2"] is False

    def test_empty_content_progress(self, app_context):
        """U-M11: Leerer Progress gibt leeres Dict."""
        user = UserFactory()
        lesson = LessonFactory()
        db.session.commit()
        progress = UserLessonProgressFactory(user_id=user.id, lesson_id=lesson.id)
        assert progress.get_content_progress() == {}

    def test_mark_content_completed(self, app_context):
        """U-M11: mark_content_completed setzt Content auf True."""
        user = UserFactory()
        lesson = LessonFactory()
        db.session.commit()
        # Einen Content-Item erstellen
        content = LessonContentFactory(lesson_id=lesson.id)
        db.session.commit()
        progress = UserLessonProgressFactory(user_id=user.id, lesson_id=lesson.id)
        db.session.commit()

        progress.mark_content_completed(content.id)
        cp = progress.get_content_progress()
        assert cp[str(content.id)] is True

    def test_update_progress_percentage(self, app_context):
        """U-M12: Fortschritts-Prozent wird korrekt berechnet."""
        user = UserFactory()
        lesson = LessonFactory()
        db.session.commit()
        c1 = LessonContentFactory(lesson_id=lesson.id)
        c2 = LessonContentFactory(lesson_id=lesson.id)
        db.session.commit()
        progress = UserLessonProgressFactory(user_id=user.id, lesson_id=lesson.id)
        db.session.commit()

        progress.mark_content_completed(c1.id)
        assert progress.progress_percentage == 50

        progress.mark_content_completed(c2.id)
        assert progress.progress_percentage == 100
        assert progress.is_completed is True

    def test_reset_progress(self, app_context):
        """U-M13: reset() setzt allen Fortschritt zurück."""
        user = UserFactory()
        lesson = LessonFactory()
        db.session.commit()
        content = LessonContentFactory(lesson_id=lesson.id, is_interactive=True)
        db.session.commit()
        progress = UserLessonProgressFactory(
            user_id=user.id, lesson_id=lesson.id,
            is_completed=True, progress_percentage=100
        )
        db.session.commit()

        progress.reset()
        assert progress.is_completed is False
        assert progress.progress_percentage == 0
        assert progress.get_content_progress() == {}


# ── U-M14: Lesson-Type Event Listener ───────────────────────

class TestLessonTypeEventListener:
    def test_free_lesson_type_on_zero_price(self, app_context):
        """U-M14: Preis=0 → lesson_type='free'."""
        lesson = LessonFactory(price=0.0)
        db.session.commit()
        assert lesson.lesson_type == "free"

    def test_paid_lesson_type_on_positive_price(self, app_context):
        """U-M14: Preis>0 → lesson_type='paid'."""
        lesson = LessonFactory(price=29.0)
        db.session.commit()
        assert lesson.lesson_type == "paid"

    def test_lesson_type_updates_on_price_change(self, app_context):
        """U-M14: Preisänderung aktualisiert lesson_type."""
        lesson = LessonFactory(price=0.0)
        db.session.commit()
        assert lesson.lesson_type == "free"
        lesson.price = 15.0
        db.session.flush()
        assert lesson.lesson_type == "paid"


# ── U-M15: Course – Lesson M:N ──────────────────────────────

class TestCourseLessonRelationship:
    def test_course_lessons_m2m(self, app_context):
        """U-M15: Course ↔ Lesson M:N-Beziehung funktioniert."""
        course = CourseFactory()
        l1 = LessonFactory()
        l2 = LessonFactory()
        db.session.commit()
        db.session.execute(
            course_lessons.insert().values(course_id=course.id, lesson_id=l1.id)
        )
        db.session.execute(
            course_lessons.insert().values(course_id=course.id, lesson_id=l2.id)
        )
        db.session.commit()
        assert len(course.lessons) == 2
        assert l1 in course.lessons


# ── U-M16: LessonPurchase / CoursePurchase Constraints ──────

class TestPurchaseConstraints:
    def test_duplicate_lesson_purchase_raises(self, app_context):
        """U-M16: Doppelter Lektions-Kauf wirft Fehler."""
        user = UserFactory()
        lesson = PaidLessonFactory()
        db.session.commit()
        LessonPurchaseFactory(user_id=user.id, lesson_id=lesson.id)
        db.session.commit()
        with pytest.raises(Exception):
            LessonPurchaseFactory(user_id=user.id, lesson_id=lesson.id)
            db.session.commit()

    def test_duplicate_course_purchase_raises(self, app_context):
        """U-M16: Doppelter Kurs-Kauf wirft Fehler."""
        user = UserFactory()
        course = PaidCourseFactory()
        db.session.commit()
        CoursePurchaseFactory(user_id=user.id, course_id=course.id)
        db.session.commit()
        with pytest.raises(Exception):
            CoursePurchaseFactory(user_id=user.id, course_id=course.id)
            db.session.commit()


# ── U-M17: Quiz-System ──────────────────────────────────────

class TestQuizSystem:
    def test_quiz_question_with_options(self, app_context):
        """U-M17: QuizQuestion mit Optionen erstellen."""
        lesson = LessonFactory()
        db.session.commit()
        content = LessonContentFactory(lesson_id=lesson.id, is_interactive=True)
        db.session.commit()
        question = QuizQuestionFactory(lesson_content_id=content.id)
        db.session.commit()
        QuizOptionFactory(question_id=question.id, option_text="Richtig", is_correct=True)
        QuizOptionFactory(question_id=question.id, option_text="Falsch", is_correct=False)
        db.session.commit()
        assert len(question.options) == 2
        correct = [o for o in question.options if o.is_correct]
        assert len(correct) == 1

    def test_user_quiz_answer_unique(self, app_context):
        """U-M17: Unique-Constraint auf user_id + question_id."""
        user = UserFactory()
        lesson = LessonFactory()
        db.session.commit()
        content = LessonContentFactory(lesson_id=lesson.id, is_interactive=True)
        db.session.commit()
        question = QuizQuestionFactory(lesson_content_id=content.id)
        db.session.commit()
        answer = UserQuizAnswer(user_id=user.id, question_id=question.id, is_correct=True)
        db.session.add(answer)
        db.session.commit()
        with pytest.raises(Exception):
            answer2 = UserQuizAnswer(user_id=user.id, question_id=question.id, is_correct=False)
            db.session.add(answer2)
            db.session.commit()


# ── U-M18: Lesson Pages Property ────────────────────────────

class TestLessonPages:
    def test_pages_property_groups_content(self, app_context):
        """U-M18: Lesson.pages gruppiert Content nach Seitennummer."""
        lesson = LessonFactory()
        db.session.commit()
        LessonContentFactory(lesson_id=lesson.id, page_number=1, order_index=0)
        LessonContentFactory(lesson_id=lesson.id, page_number=1, order_index=1)
        LessonContentFactory(lesson_id=lesson.id, page_number=2, order_index=0)
        db.session.commit()
        pages = lesson.pages
        assert len(pages) == 2
        assert len(pages[0]["content"]) == 2
        assert len(pages[1]["content"]) == 1

    def test_empty_lesson_has_no_pages(self, app_context):
        """U-M18: Lektion ohne Content hat leere Pages."""
        lesson = LessonFactory()
        db.session.commit()
        assert lesson.pages == []


# ── U-M19: PaymentTransaction ───────────────────────────────

class TestPaymentTransaction:
    def test_transaction_creation(self, app_context):
        """U-M19: PaymentTransaction mit allen Feldern."""
        user = UserFactory()
        db.session.commit()
        tx = PaymentTransactionFactory(user_id=user.id, item_type="lesson", item_id=1)
        db.session.commit()
        assert tx.state == "PENDING"
        assert tx.currency == "CHF"

    def test_transaction_unique_id(self, app_context):
        """U-M19: transaction_id muss unique sein."""
        user = UserFactory()
        db.session.commit()
        PaymentTransactionFactory(user_id=user.id, transaction_id=12345)
        db.session.commit()
        with pytest.raises(Exception):
            PaymentTransactionFactory(user_id=user.id, transaction_id=12345)
            db.session.commit()


# ── U-M20: LessonCategory ───────────────────────────────────

class TestLessonCategory:
    def test_category_creation(self, app_context):
        """U-M20: Kategorie erstellen und Lektion zuordnen."""
        cat = LessonCategoryFactory(name="Hiragana")
        db.session.commit()
        lesson = LessonFactory(category_id=cat.id)
        db.session.commit()
        assert lesson.category.name == "Hiragana"
        assert lesson in cat.lessons
