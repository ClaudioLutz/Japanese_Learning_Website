#!/usr/bin/env python3
"""
This script creates a new, multi-page lesson on "Mastering Japanese Numbers"
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
LESSON_TITLE = "Mastering Japanese Numbers"
LESSON_DIFFICULTY = "Beginner"
PAGES = [
    {
        "page_number": 1,
        "title": "Numbers 1-10",
        "description": "Learn the basic numbers from 1 to 10.",
        "content": [
            {"type": "explanation", "topic": "Japanese numbers 1-10", "keywords": "ichi, ni, san, yon, go, roku, nana, hachi, kyu, ju"},
            {"type": "multiple_choice", "topic": "Reading numbers 1-10", "keywords": "ichi, ni, san, yon, go, roku, nana, hachi, kyu, ju"}
        ]
    },
    {
        "page_number": 2,
        "title": "Numbers 11-100",
        "description": "Learn how to form numbers from 11 to 100.",
        "content": [
            {"type": "explanation", "topic": "Forming Japanese numbers 11-100", "keywords": "juuichi, nijuu, sanjuu, hyaku"},
            {"type": "multiple_choice", "topic": "Reading numbers 11-100", "keywords": "juuichi, nijuu, sanjuu, hyaku"}
        ]
    },
    {
        "page_number": 3,
        "title": "Large Numbers",
        "description": "Learn about hundreds, thousands, and myriads.",
        "content": [
            {"type": "explanation", "topic": "Large Japanese numbers", "keywords": "hyaku, sen, man, oku"},
            {"type": "multiple_choice", "topic": "Reading large numbers", "keywords": "hyaku, sen, man, oku"}
        ]
    },
    {
        "page_number": 4,
        "title": "Japanese Counters",
        "description": "Learn about common counters for objects and people.",
        "content": [
            {"type": "explanation", "topic": "Japanese counters", "keywords": "-tsu, -nin, -hon, -mai, counters"},
            {"type": "multiple_choice", "topic": "Using Japanese counters", "keywords": "-tsu, -nin, -hon, -mai, counters"}
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
            description="A comprehensive guide to Japanese numbers and counting.",
            lesson_type="free",
            difficulty_level=2, # Beginner to Intermediate
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
                description=page_info['description']
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
