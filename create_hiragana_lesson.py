#!/usr/bin/env python3
"""
This script creates a new, comprehensive, multi-page lesson on "Complete Hiragana Mastery"
using the AI content generation feature.
"""
import os
import sys
from dotenv import load_dotenv

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Load environment variables
load_dotenv()

from app import create_app, db
from app.models import Lesson, LessonPage, LessonContent, QuizQuestion, QuizOption
from app.ai_services import AILessonContentGenerator

# --- Configuration ---
LESSON_TITLE = "Complete Hiragana Mastery"
LESSON_DIFFICULTY = "Absolute Beginner"
PAGES = [
    {
        "page_number": 1, "title": "Introduction to Hiragana",
        "content": [
            {"type": "explanation", "topic": "What is Hiragana?", "keywords": "hiragana, japanese, writing system"},
            {"type": "multiple_choice", "topic": "Facts about Hiragana", "keywords": "hiragana, japanese, writing system"}
        ]
    },
    {
        "page_number": 2, "title": "Vowels (a, i, u, e, o)",
        "content": [
            {"type": "explanation", "topic": "Hiragana vowels: あ, い, う, え, お", "keywords": "a, i, u, e, o, vowels"},
            {"type": "multiple_choice", "topic": "Reading Hiragana vowels", "keywords": "あ, い, う, え, お"}
        ]
    },
    {
        "page_number": 3, "title": "K-Line (ka, ki, ku, ke, ko)",
        "content": [
            {"type": "explanation", "topic": "Hiragana K-Line: か, き, く, け, こ", "keywords": "ka, ki, ku, ke, ko"},
            {"type": "multiple_choice", "topic": "Reading Hiragana K-Line", "keywords": "か, き, く, け, こ"}
        ]
    },
    {
        "page_number": 4, "title": "S-Line (sa, shi, su, se, so)",
        "content": [
            {"type": "explanation", "topic": "Hiragana S-Line: さ, し, す, せ, そ", "keywords": "sa, shi, su, se, so"},
            {"type": "multiple_choice", "topic": "Reading Hiragana S-Line", "keywords": "さ, し, す, せ, そ"}
        ]
    },
    {
        "page_number": 5, "title": "T-Line (ta, chi, tsu, te, to)",
        "content": [
            {"type": "explanation", "topic": "Hiragana T-Line: た, ち, つ, て, と", "keywords": "ta, chi, tsu, te, to"},
            {"type": "multiple_choice", "topic": "Reading Hiragana T-Line", "keywords": "た, ち, つ, て, と"}
        ]
    },
    {
        "page_number": 6, "title": "N-Line (na, ni, nu, ne, no)",
        "content": [
            {"type": "explanation", "topic": "Hiragana N-Line: な, に, ぬ, ね, の", "keywords": "na, ni, nu, ne, no"},
            {"type": "multiple_choice", "topic": "Reading Hiragana N-Line", "keywords": "な, に, ぬ, ね, の"}
        ]
    },
    {
        "page_number": 7, "title": "H-Line (ha, hi, fu, he, ho)",
        "content": [
            {"type": "explanation", "topic": "Hiragana H-Line: は, ひ, ふ, へ, ほ", "keywords": "ha, hi, fu, he, ho"},
            {"type": "multiple_choice", "topic": "Reading Hiragana H-Line", "keywords": "は, ひ, ふ, へ, ほ"}
        ]
    },
    {
        "page_number": 8, "title": "M-Line (ma, mi, mu, me, mo)",
        "content": [
            {"type": "explanation", "topic": "Hiragana M-Line: ま, み, む, め, も", "keywords": "ma, mi, mu, me, mo"},
            {"type": "multiple_choice", "topic": "Reading Hiragana M-Line", "keywords": "ま, み, む, め, も"}
        ]
    },
    {
        "page_number": 9, "title": "Y-Line (ya, yu, yo)",
        "content": [
            {"type": "explanation", "topic": "Hiragana Y-Line: や, ゆ, よ", "keywords": "ya, yu, yo"},
            {"type": "multiple_choice", "topic": "Reading Hiragana Y-Line", "keywords": "や, ゆ, よ"}
        ]
    },
    {
        "page_number": 10, "title": "R-Line (ra, ri, ru, re, ro)",
        "content": [
            {"type": "explanation", "topic": "Hiragana R-Line: ら, り, る, れ, ろ", "keywords": "ra, ri, ru, re, ro"},
            {"type": "multiple_choice", "topic": "Reading Hiragana R-Line", "keywords": "ら, り, る, れ, ろ"}
        ]
    },
    {
        "page_number": 11, "title": "W-Line and Final N (wa, wo, n)",
        "content": [
            {"type": "explanation", "topic": "Hiragana W-Line and Final N: わ, を, ん", "keywords": "wa, wo, n"},
            {"type": "multiple_choice", "topic": "Reading Hiragana W-Line and Final N", "keywords": "わ, を, ん"}
        ]
    }
]

def create_lesson(app):
    """Creates the lesson and its content within the Flask app context."""
    with app.app_context():
        print(f"--- Creating Lesson: {LESSON_TITLE} ---")

        # Check if lesson already exists and delete it
        existing_lesson = Lesson.query.filter_by(title=LESSON_TITLE).first()
        if existing_lesson:
            print(f"Found existing lesson '{LESSON_TITLE}' (ID: {existing_lesson.id}). Deleting it.")
            db.session.delete(existing_lesson)
            db.session.commit()
            print("✅ Existing lesson deleted.")

        # Create the lesson
        lesson = Lesson(
            title=LESSON_TITLE,
            description="A comprehensive, multi-page lesson to master all Hiragana characters.",
            lesson_type="free",
            difficulty_level=1, # Absolute Beginner
            is_published=True
        )
        db.session.add(lesson)
        db.session.commit()
        print(f"✅ Lesson '{LESSON_TITLE}' created with ID: {lesson.id}")

        # Initialize AI generator
        generator = AILessonContentGenerator()
        if not generator.client:
            print("❌ AI Generator could not be initialized. Check your API key.")
            return

        # Create pages and content
        for page_info in PAGES:
            print(f"\n--- Creating Page {page_info['page_number']}: {page_info['title']} ---")
            
            # Create LessonPage
            lesson_page = LessonPage(
                lesson_id=lesson.id,
                page_number=page_info['page_number'],
                title=page_info['title'],
                description=f"This page covers: {page_info['title']}"
            )
            db.session.add(lesson_page)
            
            order_index = 0
            for content_info in page_info['content']:
                if content_info['type'] == 'explanation':
                    print(f"🤖 Generating explanation for '{content_info['topic']}'...")
                    result = generator.generate_explanation(content_info['topic'], LESSON_DIFFICULTY, content_info['keywords'])
                    
                    if "error" in result:
                        print(f"❌ Error: {result['error']}")
                        continue

                    content = LessonContent(
                        lesson_id=lesson.id,
                        page_number=page_info['page_number'],
                        content_type="text",
                        title=f"Explanation: {page_info['title']}",
                        content_text=result['generated_text'],
                        order_index=order_index,
                        generated_by_ai=True,
                        ai_generation_details={"model": "gpt-4o", **content_info}
                    )
                    db.session.add(content)
                    print("✅ Explanation added.")

                elif content_info['type'] == 'multiple_choice':
                    print(f"🤖 Generating quiz for '{content_info['topic']}'...")
                    result = generator.generate_multiple_choice_question(content_info['topic'], LESSON_DIFFICULTY, content_info['keywords'])

                    if "error" in result:
                        print(f"❌ Error: {result['error']}")
                        continue
                    
                    quiz_content = LessonContent(
                        lesson_id=lesson.id,
                        page_number=page_info['page_number'],
                        content_type="interactive",
                        title=f"Quiz: {result['question_text'][:30]}...",
                        is_interactive=True,
                        order_index=order_index,
                        generated_by_ai=True,
                        ai_generation_details={"model": "gpt-4o", **content_info}
                    )
                    db.session.add(quiz_content)
                    db.session.flush()

                    question = QuizQuestion(
                        lesson_content_id=quiz_content.id,
                        question_type="multiple_choice",
                        question_text=result['question_text'],
                        explanation=result['overall_explanation']
                    )
                    db.session.add(question)
                    db.session.flush()

                    for option_data in result['options']:
                        option = QuizOption(
                            question_id=question.id,
                            option_text=option_data['text'],
                            is_correct=option_data['is_correct'],
                            feedback=option_data.get('feedback', '')
                        )
                        db.session.add(option)
                    
                    print("✅ Quiz question added.")
                
                order_index += 1

        db.session.commit()
        print("\n--- Lesson Creation Complete! ---")

if __name__ == "__main__":
    if 'OPENAI_API_KEY' not in os.environ:
        print("❌ Error: OPENAI_API_KEY environment variable not set.")
        sys.exit(1)

    app = create_app()
    create_lesson(app)
