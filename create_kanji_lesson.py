#!/usr/bin/env python3
"""
This script creates a beginner-friendly, multi-page lesson on Basic Kanji Numbers (1-10).
The lesson is designed for absolute beginners and includes detailed explanations,
stroke order guidance, and interactive quizzes for each number.
"""
import os
import sys
from dotenv import load_dotenv

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Load environment variables
load_dotenv()

# Ensure you have these models and services in your application structure
# This is a placeholder for your actual application structure.
# You might need to adjust the import paths based on your project setup.
try:
    from app import create_app, db
    from app.models import Lesson, LessonPage, LessonContent, QuizQuestion, QuizOption
    from app.ai_services import AILessonContentGenerator
except ImportError:
    print("="*80)
    print("ERROR: Could not import Flask app components.")
    print("Please ensure you are running this script from the root of your project")
    print("and that your Flask application structure (`app`, `app.models`, etc.) is correct.")
    print("This script is designed to integrate with a specific Flask application.")
    print("="*80)
    sys.exit(1)


# --- Configuration ---
LESSON_TITLE = "Beginner Kanji: Numbers 1-10"
LESSON_DIFFICULTY = "Absolute Beginner"

# --- Kanji Data ---
# Structured data for the Kanji lesson
KANJI_DATA = {
    1: {"kanji": "一", "onyomi": "イチ", "kunyomi": "ひと(つ)", "meaning": "one", "strokes": 1, "stroke_order": "A single horizontal stroke from left to right."},
    2: {"kanji": "二", "onyomi": "ニ", "kunyomi": "ふた(つ)", "meaning": "two", "strokes": 2, "stroke_order": "Two horizontal strokes. The top one is shorter, the bottom one is longer. Both from left to right."},
    3: {"kanji": "三", "onyomi": "サン", "kunyomi": "み(っつ)", "meaning": "three", "strokes": 3, "stroke_order": "Three horizontal strokes from top to bottom. The middle stroke is the shortest, and the bottom stroke is the longest."},
    4: {"kanji": "四", "onyomi": "シ", "kunyomi": "よん, よ(っつ)", "meaning": "four", "strokes": 5, "stroke_order": "A box shape with two strokes inside. Start with the left vertical stroke, then the top and right side as one stroke. Add the two inner strokes, then close the bottom."},
    5: {"kanji": "五", "onyomi": "ゴ", "kunyomi": "いつ(つ)", "meaning": "five", "strokes": 4, "stroke_order": "Start with the top horizontal stroke, then the vertical stroke, followed by the corner stroke, and finally the bottom horizontal stroke."},
    6: {"kanji": "六", "onyomi": "ロク", "kunyomi": "む(っつ)", "meaning": "six", "strokes": 4, "stroke_order": "Start with the top dot, then the horizontal line. Finish with the two dots at the bottom."},
    7: {"kanji": "七", "onyomi": "シチ", "kunyomi": "なな(つ)", "meaning": "seven", "strokes": 2, "stroke_order": "A slightly angled horizontal stroke, followed by a vertical stroke that crosses it and hooks at the end."},
    8: {"kanji": "八", "onyomi": "ハチ", "kunyomi": "や(っつ)", "meaning": "eight", "strokes": 2, "stroke_order": "Two diagonal strokes. Start with the shorter left stroke, then the longer right stroke. They are not connected at the top."},
    9: {"kanji": "九", "onyomi": "キュウ, ク", "kunyomi": "ここの(つ)", "meaning": "nine", "strokes": 2, "stroke_order": "A left-curving stroke, followed by a second stroke that starts horizontally, turns down, and curves to the left."},
    10: {"kanji": "十", "onyomi": "ジュウ", "kunyomi": "とお", "meaning": "ten", "strokes": 2, "stroke_order": "A cross shape. First, the horizontal stroke from left to right, then the vertical stroke from top to bottom crossing it."},
}

def generate_pages():
    """Generate the complete page structure for the Kanji lesson."""
    pages = []
    page_number = 1

    # --- Page 1: Introduction ---
    pages.append({
        "page_number": page_number,
        "title": "Introduction to Kanji",
        "content": [
            {
                "type": "formatted_explanation",
                "topic": "What are Kanji? A brief introduction to Kanji, explaining that they are logographic characters from Chinese, used in the Japanese writing system. Explain why learning numbers 1-10 is a great starting point for beginners.",
                "keywords": "kanji, japanese writing, introduction, numbers, beginner"
            }
        ]
    })
    page_number += 1

    # --- Generate Pages for each Kanji ---
    for num, data in KANJI_DATA.items():
        kanji = data['kanji']
        meaning = data['meaning']
        title = f"Kanji for {num}: {kanji} ({meaning})"

        # --- Presentation Page ---
        pages.append({
            "page_number": page_number,
            "title": f"{title} - Presentation",
            "content": [
                {
                    "type": "formatted_explanation",
                    "topic": f"Detailed presentation of the Kanji '{kanji}'. "
                             f"Meaning: {meaning}. "
                             f"On’yomi (Chinese reading): {data['onyomi']}. "
                             f"Kun’yomi (Japanese reading): {data['kunyomi']}. "
                             f"Number of strokes: {data['strokes']}. "
                             f"Stroke Order: {data['stroke_order']}. "
                             "Provide memory tips and simple example words if possible (e.g., 一月 for January).",
                    "keywords": f"kanji, {kanji}, {meaning}, {data['onyomi']}, {data['kunyomi']}, stroke order"
                }
            ]
        })
        page_number += 1

        # --- Quiz Page ---
        pages.append({
            "page_number": page_number,
            "title": f"{title} - Quiz",
            "content": [
                {
                    "type": "multiple_choice",
                    "topic": f"Quiz: What is a common reading for the Kanji '{kanji}'? Include both On'yomi and Kun'yomi options among distractors.",
                    "keywords": f"kanji quiz, {kanji}, reading, onyomi, kunyomi"
                },
                {
                    "type": "matching",
                    "topic": f"Quiz: Match the Kanji '{kanji}' to its English meaning. Provide other number meanings as distractors.",
                    "keywords": f"kanji quiz, {kanji}, meaning, matching"
                },
                 {
                    "type": "multiple_choice",
                    "topic": f"Quiz: How many strokes are in the Kanji '{kanji}'? Provide other stroke counts as distractors.",
                    "keywords": f"kanji quiz, {kanji}, strokes, stroke count"
                }
            ]
        })
        page_number += 1

    # --- Final Review Page ---
    pages.append({
        "page_number": page_number,
        "title": "Kanji 1-10 Review",
        "content": [
            {
                "type": "formatted_explanation",
                "topic": "A summary of all Kanji from 1 to 10. Recap the importance of stroke order and provide tips for remembering their meanings and readings. Include a chart summarizing all the Kanji.",
                "keywords": "kanji review, summary, 1-10, stroke order, chart"
            },
            {
                "type": "multiple_choice",
                "topic": "Comprehensive quiz: What is the reading of 三?",
                "keywords": "kanji review quiz, reading, comprehensive"
            },
            {
                "type": "matching",
                "topic": "Comprehensive matching quiz: Match the Kanji characters (e.g., 七, 九, 二) to their meanings (seven, nine, two).",
                "keywords": "kanji review quiz, matching, comprehensive"
            }
        ]
    })
    
    # --- Next Steps Page ---
    page_number += 1
    pages.append({
        "page_number": page_number,
        "title": "Next Steps",
        "content": [
            {
                "type": "formatted_explanation",
                "topic": "Suggest next steps for learners, such as learning compound numbers (e.g., 11 is 十一), days of the week (e.g., 月曜日), or other basic foundational Kanji.",
                "keywords": "kanji, next steps, compound numbers, days of the week"
            }
        ]
    })

    return pages

PAGES = generate_pages()

def create_lesson(app):
    """Creates the lesson and its content within the Flask app context."""
    with app.app_context():
        print(f"--- Creating Lesson: {LESSON_TITLE} ---")
        print(f"Total pages to create: {len(PAGES)}")

        # Check if lesson already exists and delete it to ensure a fresh start
        existing_lesson = Lesson.query.filter_by(title=LESSON_TITLE).first()
        if existing_lesson:
            print(f"Found existing lesson '{LESSON_TITLE}' (ID: {existing_lesson.id}). Deleting it.")
            db.session.delete(existing_lesson)
            db.session.commit()
            print("✅ Existing lesson deleted.")

        # Create the main lesson entry
        lesson = Lesson(
            title=LESSON_TITLE,
            description="A beginner-friendly lesson on the basic Kanji for numbers 1 to 10, including readings, meanings, stroke order, and interactive quizzes.",
            lesson_type="free",
            difficulty_level=1, # Corresponds to "Absolute Beginner"
            is_published=True
        )
        db.session.add(lesson)
        db.session.commit()
        print(f"✅ Lesson '{LESSON_TITLE}' created with ID: {lesson.id}")

        # Initialize AI content generator
        generator = AILessonContentGenerator()
        if not generator.client:
            print("❌ AI Generator could not be initialized. Check your API key.")
            return

        # Create all pages and their content
        for page_info in PAGES:
            print(f"\n--- Creating Page {page_info['page_number']}: {page_info['title']} ---")
            
            lesson_page = LessonPage(
                lesson_id=lesson.id,
                page_number=page_info['page_number'],
                title=page_info['title'],
                description=f"This page covers: {page_info['title']}"
            )
            db.session.add(lesson_page)
            
            order_index = 0
            for content_info in page_info['content']:
                content_type = content_info['type']
                topic = content_info['topic']
                keywords = content_info['keywords']
                
                print(f"🤖 Generating {content_type} for '{topic[:60]}...'")
                
                result = None
                # Use the AI generator for each content type
                if content_type == 'formatted_explanation':
                    result = generator.generate_formatted_explanation(topic, LESSON_DIFFICULTY, keywords)
                elif content_type == 'multiple_choice':
                    result = generator.generate_multiple_choice_question(topic, LESSON_DIFFICULTY, keywords)
                elif content_type == 'matching':
                    result = generator.generate_matching_question(topic, LESSON_DIFFICULTY, keywords)

                if not result or "error" in result:
                    print(f"❌ Error generating {content_type}: {result.get('error', 'Unknown error') if result else 'No result returned'}")
                    continue

                # --- Create LessonContent ---
                if content_type == 'formatted_explanation':
                    content = LessonContent(
                        lesson_id=lesson.id,
                        page_number=page_info['page_number'],
                        content_type="text",
                        title=f"Explanation: {page_info['title']}",
                        content_text=result['generated_text'],
                        order_index=order_index,
                        generated_by_ai=True,
                        ai_generation_details={"model": "gpt-4.5-preview", **content_info}
                    )
                    db.session.add(content)
                    print(f"✅ Formatted explanation added.")
                else: # It's a quiz
                    quiz_content = LessonContent(
                        lesson_id=lesson.id,
                        page_number=page_info['page_number'],
                        content_type="interactive",
                        title=f"Quiz: {result.get('question_text', topic)[:40]}...",
                        is_interactive=True,
                        order_index=order_index,
                        generated_by_ai=True,
                        ai_generation_details={"model": "gpt-4.5-preview", **content_info}
                    )
                    db.session.add(quiz_content)
                    db.session.flush() # Flush to get the ID for the quiz question

                    question = None
                    if content_type == 'multiple_choice':
                        question = QuizQuestion(
                            lesson_content_id=quiz_content.id,
                            question_type="multiple_choice",
                            question_text=result['question_text'],
                            explanation=result['overall_explanation']
                        )
                        db.session.add(question)
                        db.session.flush()
                        for option_data in result['options']:
                            db.session.add(QuizOption(question_id=question.id, option_text=option_data['text'], is_correct=option_data['is_correct'], feedback=option_data.get('feedback', '')))
                    
                    elif content_type == 'matching':
                        question = QuizQuestion(
                            lesson_content_id=quiz_content.id,
                            question_type="matching",
                            question_text=result['question_text'],
                            explanation=result.get('explanation', '')
                        )
                        db.session.add(question)
                        db.session.flush()
                        for pair in result['pairs']:
                            db.session.add(QuizOption(question_id=question.id, option_text=pair['prompt'], feedback=pair['answer'], is_correct=True))

                    print(f"✅ {content_type.replace('_', ' ').title()} quiz added.")

                order_index += 1

        db.session.commit()
        print(f"\n--- Lesson Creation Complete! ---")
        print(f"Created {len(PAGES)} pages for the lesson '{LESSON_TITLE}'.")
        print("Each number has a detailed presentation page and an interactive quiz.")

if __name__ == "__main__":
    if 'OPENAI_API_KEY' not in os.environ:
        print("❌ Error: OPENAI_API_KEY environment variable not set.")
        print("Please set this environment variable to use the AI content generator.")
        sys.exit(1)

    # This assumes you have a create_app function for your Flask app
    app = create_app()
    create_lesson(app)
