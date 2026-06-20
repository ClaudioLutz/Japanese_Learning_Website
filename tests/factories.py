# tests/factories.py
"""
factory_boy Factories für alle SQLAlchemy-Models.
Erzeugt realistische Testdaten ohne manuelle DB-Inserts.
"""

import factory
from factory import Sequence, LazyAttribute, SubFactory, LazyFunction
from datetime import datetime
from app import db
from app.models import (
    User, Kana, Kanji, Vocabulary, Grammar,
    LessonCategory, Lesson, LessonContent, LessonPage,
    LessonPrerequisite, Course, LessonPurchase, CoursePurchase,
    PaymentTransaction, QuizQuestion, QuizOption, UserLessonProgress,
    UserQuizAnswer, CardReviewState, ReviewLog, UserSRSSettings,
    UserAchievement, DailyReviewAggregate,
    ForumCategory, ForumTopic, ForumPost,
)


class BaseFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        abstract = True
        sqlalchemy_session = None  # Wird dynamisch gesetzt

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override um die aktuelle DB-Session zu verwenden."""
        obj = model_class(**kwargs)
        db.session.add(obj)
        db.session.flush()
        return obj


# ── User Factories ────────────────────────────────────────

class UserFactory(BaseFactory):
    class Meta:
        model = User

    username = Sequence(lambda n: f"testuser_{n}")
    email = LazyAttribute(lambda o: f"{o.username}@test.com")
    password_hash = "set_via_post_generation"
    subscription_level = "free"
    is_admin = False

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        password = kwargs.pop("password", "Test123!")
        obj = super()._create(model_class, *args, **kwargs)
        obj.set_password(password)
        return obj


class AdminUserFactory(UserFactory):
    username = Sequence(lambda n: f"admin_{n}")
    is_admin = True


class PremiumUserFactory(UserFactory):
    username = Sequence(lambda n: f"premium_{n}")
    subscription_level = "premium"


# ── Content Factories ─────────────────────────────────────

class KanaFactory(BaseFactory):
    class Meta:
        model = Kana

    character = Sequence(lambda n: chr(0x3042 + n))  # あ, い, う, ...
    romanization = Sequence(lambda n: ["a", "i", "u", "e", "o"][n % 5])
    type = "hiragana"


class KanjiFactory(BaseFactory):
    class Meta:
        model = Kanji

    character = Sequence(lambda n: chr(0x4E00 + n))  # 一, 丁, 丂, ...
    meaning = Sequence(lambda n: f"meaning_{n}")
    onyomi = Sequence(lambda n: f"onyomi_{n}")
    kunyomi = Sequence(lambda n: f"kunyomi_{n}")
    jlpt_level = "N5"
    stroke_count = 5
    status = "approved"


class VocabularyFactory(BaseFactory):
    class Meta:
        model = Vocabulary

    word = Sequence(lambda n: f"単語{n}")
    reading = Sequence(lambda n: f"たんご{n}")
    meaning = Sequence(lambda n: f"word_{n}")
    jlpt_level = "N5"
    status = "approved"


class GrammarFactory(BaseFactory):
    class Meta:
        model = Grammar

    title = Sequence(lambda n: f"Grammar Rule {n}")
    explanation = "Test grammar explanation"
    structure = "Subject + は + Predicate"
    jlpt_level = "N5"
    status = "approved"


# ── Lesson Factories ──────────────────────────────────────

class LessonCategoryFactory(BaseFactory):
    class Meta:
        model = LessonCategory

    name = Sequence(lambda n: f"Category {n}")
    description = "Test category"
    color_code = "#007bff"


class LessonFactory(BaseFactory):
    class Meta:
        model = Lesson

    title = Sequence(lambda n: f"Test Lesson {n}")
    description = "A test lesson"
    lesson_type = "free"
    difficulty_level = 1
    order_index = Sequence(lambda n: n)
    is_published = True
    allow_guest_access = False
    instruction_language = "english"
    price = 0.0
    is_purchasable = False


class PaidLessonFactory(LessonFactory):
    lesson_type = "paid"
    price = 29.0
    is_purchasable = True


class PremiumLessonFactory(LessonFactory):
    lesson_type = "premium"
    price = 0.0
    is_purchasable = False


class LessonPageFactory(BaseFactory):
    class Meta:
        model = LessonPage

    lesson_id = None  # Muss explizit gesetzt werden
    page_number = Sequence(lambda n: n + 1)
    title = Sequence(lambda n: f"Page {n + 1}")


class LessonContentFactory(BaseFactory):
    class Meta:
        model = LessonContent

    lesson_id = None  # Muss explizit gesetzt werden
    content_type = "text"
    title = Sequence(lambda n: f"Content Item {n}")
    content_text = "Test content text"
    order_index = Sequence(lambda n: n)
    page_number = 1


# ── Course Factories ──────────────────────────────────────

class CourseFactory(BaseFactory):
    class Meta:
        model = Course

    title = Sequence(lambda n: f"Test Course {n}")
    description = "A test course"
    is_published = True
    price = 0.0
    is_purchasable = False


class PaidCourseFactory(CourseFactory):
    price = 99.0
    is_purchasable = True


# ── Purchase Factories ────────────────────────────────────

class LessonPurchaseFactory(BaseFactory):
    class Meta:
        model = LessonPurchase

    user_id = None
    lesson_id = None
    price_paid = 29.0
    provider_transaction_id = Sequence(lambda n: 1000000 + n)
    transaction_state = "COMPLETED"


class CoursePurchaseFactory(BaseFactory):
    class Meta:
        model = CoursePurchase

    user_id = None
    course_id = None
    price_paid = 99.0
    provider_transaction_id = Sequence(lambda n: 2000000 + n)
    transaction_state = "COMPLETED"


class PaymentTransactionFactory(BaseFactory):
    class Meta:
        model = PaymentTransaction

    transaction_id = Sequence(lambda n: 9000000 + n)
    user_id = None
    item_type = "lesson"
    item_id = 1
    amount = 29.0
    currency = "CHF"
    state = "PENDING"


# ── Quiz Factories ────────────────────────────────────────

class QuizQuestionFactory(BaseFactory):
    class Meta:
        model = QuizQuestion

    lesson_content_id = None
    question_type = "multiple_choice"
    question_text = Sequence(lambda n: f"Question {n}?")
    explanation = "Test explanation"
    points = 1
    order_index = Sequence(lambda n: n)


class QuizOptionFactory(BaseFactory):
    class Meta:
        model = QuizOption

    question_id = None
    option_text = Sequence(lambda n: f"Option {n}")
    is_correct = False
    order_index = Sequence(lambda n: n)


# ── Progress Factories ────────────────────────────────────

class UserLessonProgressFactory(BaseFactory):
    class Meta:
        model = UserLessonProgress

    user_id = None
    lesson_id = None
    is_completed = False
    progress_percentage = 0
    time_spent = 0


# ── SRS Factories ────────────────────────────────────────


class CardReviewStateFactory(BaseFactory):
    class Meta:
        model = CardReviewState

    user_id = None
    content_id = None
    fsrs_card_state = LazyFunction(lambda: '{"stability":1.0,"difficulty":5.0,"due":"2026-04-14T00:00:00+00:00","last_review":"2026-04-13T00:00:00+00:00","reps":1,"lapses":0,"state":2,"step":null}')
    due_date = LazyFunction(datetime.utcnow)
    status = 'review'
    reps = 1
    lapses = 0


class ReviewLogFactory(BaseFactory):
    class Meta:
        model = ReviewLog

    user_id = None
    content_id = None
    rating = 3
    reviewed_at = LazyFunction(datetime.utcnow)
    time_taken_ms = 5000
    scheduled_days = 1
    elapsed_days = 0


class UserSRSSettingsFactory(BaseFactory):
    class Meta:
        model = UserSRSSettings

    user_id = None
    desired_retention = 0.9
    daily_new_cards = 20
    daily_review_limit = 100


class UserAchievementFactory(BaseFactory):
    class Meta:
        model = UserAchievement

    user_id = None
    achievement_key = 'streak_7'
    notified = False


class DailyReviewAggregateFactory(BaseFactory):
    class Meta:
        model = DailyReviewAggregate

    user_id = None
    review_date = LazyFunction(lambda: datetime.utcnow().date())
    total_reviews = 0
    correct_reviews = 0


# ── Forum Factories ───────────────────────────────────────

class ForumCategoryFactory(BaseFactory):
    class Meta:
        model = ForumCategory

    name = Sequence(lambda n: f"Kategorie {n}")
    slug = Sequence(lambda n: f"kategorie-{n}")
    description = "Testkategorie"
    icon = "fa-comments"
    display_order = Sequence(lambda n: n)
    admin_only_post = False
    is_active = True


class ForumTopicFactory(BaseFactory):
    class Meta:
        model = ForumTopic

    category_id = None
    author_id = None
    title = Sequence(lambda n: f"Testthema {n}")
    slug = Sequence(lambda n: f"testthema-{n}")
    is_pinned = False
    is_locked = False
    is_deleted = False
    reply_count = 0
    view_count = 0


class ForumPostFactory(BaseFactory):
    class Meta:
        model = ForumPost

    topic_id = None
    author_id = None
    body = Sequence(lambda n: f"Beitragstext {n} mit genug Inhalt.")
    is_op = False
    is_deleted = False
