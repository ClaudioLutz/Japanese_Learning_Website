"""
Start Flask test server with SQLite database for Playwright E2E tests.
Creates a fresh database with seed data on each run.
"""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set environment variables BEFORE importing the app
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test.db')
if os.path.exists(db_path):
    os.remove(db_path)

os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'
os.environ['SECRET_KEY'] = 'test-secret-key-for-playwright'
os.environ['WTF_CSRF_SECRET_KEY'] = 'test-csrf-key-for-playwright'
os.environ['FLASK_ENV'] = 'testing'
os.environ['TESTING'] = '1'
os.environ['WTF_CSRF_ENABLED'] = '0'
# Disable external services
os.environ['GOOGLE_CLIENT_ID'] = ''
os.environ['GOOGLE_CLIENT_SECRET'] = ''
os.environ['OPENAI_API_KEY'] = ''
os.environ['GOOGLE_AI_API_KEY'] = ''
os.environ['GCS_BUCKET_NAME'] = ''
os.environ['POSTFINANCE_SPACE_ID'] = 'test'
os.environ['POSTFINANCE_USER_ID'] = 'test'
os.environ['POSTFINANCE_API_SECRET'] = 'test'

from app import create_app, db
from app.models import User, Lesson, LessonCategory, Course, LessonContent, LessonPage, QuizQuestion, QuizOption
from werkzeug.security import generate_password_hash
from datetime import datetime

app = create_app()
# Disable CSRF for testing (env var alone doesn't work — must set in Flask config)
app.config['WTF_CSRF_ENABLED'] = False
app.config['WTF_CSRF_CHECK_DEFAULT'] = False

with app.app_context():
    db.create_all()

    # --- Seed Data ---

    # Admin user
    admin = User(
        username='admin',
        email='admin@test.com',
        password_hash=generate_password_hash('Admin123!'),
        is_admin=True,
        subscription_level='premium'
    )
    db.session.add(admin)

    # Regular user
    user = User(
        username='testuser',
        email='test@test.com',
        password_hash=generate_password_hash('Test123!'),
        is_admin=False,
        subscription_level='free'
    )
    db.session.add(user)

    # Premium user
    premium = User(
        username='premiumuser',
        email='premium@test.com',
        password_hash=generate_password_hash('Premium123!'),
        is_admin=False,
        subscription_level='premium'
    )
    db.session.add(premium)

    # Categories
    cat_hiragana = LessonCategory(name='Hiragana', description='Japanese Hiragana characters', color_code='#FF6B6B')
    cat_katakana = LessonCategory(name='Katakana', description='Japanese Katakana characters', color_code='#4ECDC4')
    cat_kanji = LessonCategory(name='Kanji', description='Chinese characters used in Japanese', color_code='#45B7D1')
    db.session.add_all([cat_hiragana, cat_katakana, cat_kanji])
    db.session.flush()

    # Free lesson (guest access)
    lesson_free = Lesson(
        title='Introduction to Hiragana',
        description='Learn the basics of Hiragana, the fundamental Japanese writing system.',
        lesson_type='free',
        category_id=cat_hiragana.id,
        difficulty_level='beginner',
        estimated_duration=30,
        price=0.0,
        is_purchasable=False,
        is_published=True,
        allow_guest_access=True,
        instruction_language='english',
        order_index=1
    )
    db.session.add(lesson_free)

    # Paid lesson
    lesson_paid = Lesson(
        title='Advanced Kanji: JLPT N3',
        description='Master 200+ Kanji characters for JLPT N3 level.',
        lesson_type='paid',
        category_id=cat_kanji.id,
        difficulty_level='intermediate',
        estimated_duration=120,
        price=29.90,
        is_purchasable=True,
        is_published=True,
        allow_guest_access=False,
        instruction_language='english',
        order_index=2
    )
    db.session.add(lesson_paid)

    # Premium lesson
    lesson_premium = Lesson(
        title='Business Japanese Conversation',
        description='Professional Japanese for business meetings and emails.',
        lesson_type='premium',
        category_id=cat_hiragana.id,
        difficulty_level='advanced',
        estimated_duration=90,
        price=0.0,
        is_purchasable=False,
        is_published=True,
        allow_guest_access=False,
        instruction_language='german',
        order_index=3
    )
    db.session.add(lesson_premium)

    # Unpublished lesson
    lesson_draft = Lesson(
        title='Draft Lesson',
        description='This lesson is not yet published.',
        lesson_type='free',
        category_id=cat_katakana.id,
        difficulty_level='beginner',
        estimated_duration=15,
        price=0.0,
        is_purchasable=False,
        is_published=False,
        allow_guest_access=False,
        instruction_language='english',
        order_index=4
    )
    db.session.add(lesson_draft)
    db.session.flush()

    # Lesson content for free lesson
    content_text = LessonContent(
        lesson_id=lesson_free.id,
        content_type='text',
        title='What is Hiragana?',
        content_text='<p>Hiragana is one of the three writing systems used in Japanese. It consists of 46 basic characters.</p>',
        order_index=1,
        page_number=1
    )
    db.session.add(content_text)

    content_kana = LessonContent(
        lesson_id=lesson_free.id,
        content_type='kana',
        title='Basic Vowels',
        content_text='あ い う え お',
        order_index=2,
        page_number=1
    )
    db.session.add(content_kana)

    # Quiz content
    content_quiz = LessonContent(
        lesson_id=lesson_free.id,
        content_type='interactive',
        title='Hiragana Quiz',
        content_text='Test your knowledge of basic Hiragana.',
        order_index=3,
        page_number=2,
        is_interactive=True,
        max_attempts=3,
        passing_score=70
    )
    db.session.add(content_quiz)
    db.session.flush()

    # Quiz questions
    q1 = QuizQuestion(
        lesson_content_id=content_quiz.id,
        question_type='multiple_choice',
        question_text='What is the reading of あ?',
        explanation='あ is pronounced "a" as in "father".',
        points=10,
        order_index=1
    )
    db.session.add(q1)
    db.session.flush()

    # Quiz options
    db.session.add_all([
        QuizOption(question_id=q1.id, option_text='a', is_correct=True, order_index=1, feedback='Correct!'),
        QuizOption(question_id=q1.id, option_text='i', is_correct=False, order_index=2, feedback='That is い (i).'),
        QuizOption(question_id=q1.id, option_text='u', is_correct=False, order_index=3, feedback='That is う (u).'),
        QuizOption(question_id=q1.id, option_text='e', is_correct=False, order_index=4, feedback='That is え (e).'),
    ])

    # Lesson pages
    db.session.add(LessonPage(lesson_id=lesson_free.id, page_number=1))
    db.session.add(LessonPage(lesson_id=lesson_free.id, page_number=2))

    # Course
    course = Course(
        title='Complete Beginner Japanese',
        description='A comprehensive course covering Hiragana, Katakana, and basic Kanji.',
        price=79.90,
        is_purchasable=True,
        is_published=True
    )
    db.session.add(course)
    db.session.flush()

    # Add lessons to course
    course.lessons.append(lesson_free)
    course.lessons.append(lesson_paid)

    db.session.commit()
    print(f"SEED DATA CREATED: 3 users, 4 lessons, 3 categories, 1 course, 1 quiz")

    # Seed Tokyo lesson if the script exists
    try:
        from scripts.seed_tokyo_lesson import (
            get_or_create_category, get_or_create_vocabulary, get_or_create_kanji,
            get_or_create_grammar, create_lesson, create_pages,
            seed_page_1, seed_page_2, seed_page_3, seed_page_4,
            seed_page_5, seed_page_6, seed_page_7
        )
        from app.models import LessonPurchase
        cat = get_or_create_category()
        vocab = get_or_create_vocabulary()
        kanji = get_or_create_kanji()
        grammar = get_or_create_grammar()
        tokyo_lesson = create_lesson(cat)
        create_pages(tokyo_lesson)
        seed_page_1(tokyo_lesson.id, vocab)
        seed_page_2(tokyo_lesson.id, vocab)
        seed_page_3(tokyo_lesson.id, grammar)
        seed_page_4(tokyo_lesson.id)
        seed_page_5(tokyo_lesson.id, kanji)
        seed_page_6(tokyo_lesson.id)
        seed_page_7(tokyo_lesson.id)
        # Give all test users access
        for u in [admin, user, premium]:
            db.session.add(LessonPurchase(
                user_id=u.id, lesson_id=tokyo_lesson.id,
                price_paid=0.0, transaction_state='FULFILL'
            ))
        db.session.commit()
        print(f"TOKYO LESSON SEEDED: ID={tokyo_lesson.id}")
    except Exception as e:
        print(f"TOKYO LESSON SEED SKIPPED: {e}")
        db.session.rollback()

    print(f"SQLite DB: {db_path}")

print("Starting Flask test server on http://127.0.0.1:5000 ...")
app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
