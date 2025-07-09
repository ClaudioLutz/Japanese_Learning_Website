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
            {"type": "formatted_explanation", "topic": "What is Hiragana? Its history and purpose.", "keywords": "hiragana, japanese, writing system, history"},
            {"type": "multiple_choice", "topic": "Facts about Hiragana", "keywords": "hiragana, history, characters"},
            {"type": "true_false", "topic": "Hiragana is used for foreign loanwords.", "keywords": "hiragana, katakana, loanwords"},
            {"type": "fill_in_the_blank", "topic": "The purpose of Hiragana", "keywords": "hiragana, grammar, particles"},
            {"type": "matching", "topic": "Basic Japanese Greetings", "keywords": "hiragana, greetings, ohayou, konnichiwa"}
        ]
    },
    {
        "page_number": 2, "title": "Vowels (a, i, u, e, o)",
        "content": [
            {"type": "formatted_explanation", "topic": "The five fundamental Hiragana vowels: あ, い, う, え, お", "keywords": "a, i, u, e, o, vowels, pronunciation"},
            {"type": "multiple_choice", "topic": "Reading Hiragana vowels", "keywords": "あ, い, う, え, お, reading"},
            {"type": "true_false", "topic": "The character 'う' (u) is pronounced like the 'oo' in 'moon'.", "keywords": "u, う, pronunciation"},
            {"type": "fill_in_the_blank", "topic": "Complete the word for 'love'", "keywords": "ai, あい, love"},
            {"type": "matching", "topic": "Matching Vowels to Romaji", "keywords": "vowels, romaji, あ, い, う, え, お"}
        ]
    },
    # Reduced for brevity, can be expanded later
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
            description="A comprehensive, multi-page lesson to master all Hiragana characters with interactive quizzes.",
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
                
                print(f"🤖 Generating {content_type} for '{topic}'...")
                
                result = None
                if content_type == 'formatted_explanation':
                    result = generator.generate_formatted_explanation(topic, LESSON_DIFFICULTY, keywords)
                elif content_type == 'multiple_choice':
                    result = generator.generate_multiple_choice_question(topic, LESSON_DIFFICULTY, keywords)
                elif content_type == 'true_false':
                    result = generator.generate_true_false_question(topic, LESSON_DIFFICULTY, keywords)
                elif content_type == 'fill_in_the_blank':
                    result = generator.generate_fill_in_the_blank_question(topic, LESSON_DIFFICULTY, keywords)
                elif content_type == 'matching':
                    result = generator.generate_matching_question(topic, LESSON_DIFFICULTY, keywords)

                if not result or "error" in result:
                    print(f"❌ Error generating {content_type}: {result.get('error', 'Unknown error')}")
                    continue

                # --- Create LessonContent ---
                if content_type == 'formatted_explanation':
                    content = LessonContent(
                        lesson_id=lesson.id,
                        page_number=page_info['page_number'],
                        content_type="text",
                        title=f"Explanation: {topic}",
                        content_text=result['generated_text'],
                        order_index=order_index,
                        generated_by_ai=True,
                        ai_generation_details={"model": "gpt-4o", **content_info}
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
                        ai_generation_details={"model": "gpt-4o", **content_info}
                    )
                    db.session.add(quiz_content)
                    db.session.flush()

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
                    
                    elif content_type == 'true_false':
                        question = QuizQuestion(
                            lesson_content_id=quiz_content.id,
                            question_type="true_false",
                            question_text=result['question_text'],
                            explanation=result['explanation']
                        )
                        db.session.add(question)
                        db.session.flush()
                        db.session.add(QuizOption(question_id=question.id, option_text="True", is_correct=result['is_true']))
                        db.session.add(QuizOption(question_id=question.id, option_text="False", is_correct=not result['is_true']))

                    elif content_type == 'fill_in_the_blank':
                        question = QuizQuestion(
                            lesson_content_id=quiz_content.id,
                            question_type="fill_blank",
                            question_text=result['question_text'],
                            explanation=result['explanation']
                        )
                        db.session.add(question)
                        db.session.flush()
                        db.session.add(QuizOption(question_id=question.id, option_text=result['correct_answer'], is_correct=True))

                    elif content_type == 'matching':
                        # For matching, we store the pairs as JSON in the explanation field
                        question = QuizQuestion(
                            lesson_content_id=quiz_content.id,
                            question_type="matching",
                            question_text=result['question_text'],
                            explanation=result.get('explanation', ''),
                            # Storing pairs in the question_text as a fallback if frontend needs it directly
                            # A better approach is for the frontend to parse the options
                        )
                        db.session.add(question)
                        db.session.flush()
                        # Store pairs in QuizOptions. Prompt in option_text, Answer in feedback.
                        for pair in result['pairs']:
                            db.session.add(QuizOption(question_id=question.id, option_text=pair['prompt'], feedback=pair['answer'], is_correct=True))

                    print(f"✅ {content_type.replace('_', ' ').title()} quiz added.")

                order_index += 1

        db.session.commit()
        print("\n--- Lesson Creation Complete! ---")

if __name__ == "__main__":
    if 'OPENAI_API_KEY' not in os.environ:
        print("❌ Error: OPENAI_API_KEY environment variable not set.")
        sys.exit(1)

    app = create_app()
    create_lesson(app)
