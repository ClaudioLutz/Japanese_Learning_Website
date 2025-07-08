#!/usr/bin/env python3
"""
This script creates a new lesson on "Technology and the Internet"
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
from app.models import Lesson, LessonContent, QuizQuestion, QuizOption
from app.ai_services import AILessonContentGenerator

# --- Configuration ---
LESSON_TITLE = "Technology and the Internet"
LESSON_DIFFICULTY = "Intermediate"
VOCABULARY = {
    "インターネット": "Internet",
    "ウェブサイト": "Website",
    "メール": "E-mail",
    "ダウンロード": "Download",
    "アップロード": "Upload",
    "パスワード": "Password",
    "ログイン": "Login",
    "ログアウト": "Logout"
}

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
            description="A vocabulary lesson on technology and internet terms.",
            lesson_type="free",
            difficulty_level=3, # Intermediate
            is_published=True
        )
        db.session.add(lesson)
        db.session.commit()
        print(f"✅ Lesson '{LESSON_TITLE}' created with ID: {lesson.id}")

        # Initialize AI generator
        print("\n--- Initializing AI Generator ---")
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            print("❌ OPENAI_API_KEY not found in environment variables.")
            return
        
        print(f"🔑 API Key Found: ...{api_key[-4:]}") # Print last 4 chars for verification
        
        generator = AILessonContentGenerator()
        if not generator.client:
            print("❌ AI Generator could not be initialized. Check your API key.")
            return
        
        print("✅ AI Generator Initialized")

        # Generate and add vocabulary explanations
        print("\n--- Generating Vocabulary Explanations ---")
        for i, (word, meaning) in enumerate(VOCABULARY.items()):
            print(f"🤖 Generating explanation for '{word}'...")
            
            topic = f"The Japanese word '{word}' ({meaning})"
            keywords = f"{word}, {meaning}, technology, internet"
            
            result = generator.generate_explanation(topic, LESSON_DIFFICULTY, keywords)
            
            if "error" in result:
                print(f"❌ Error generating explanation for '{word}': {result['error']}")
                continue

            content = LessonContent(
                lesson_id=lesson.id,
                content_type="text",
                title=f"Vocabulary: {word}",
                content_text=result['generated_text'],
                order_index=i,
                page_number=1,
                generated_by_ai=True,
                ai_generation_details={
                    "model": "gpt-4o",
                    "topic": topic,
                    "difficulty": LESSON_DIFFICULTY,
                    "keywords": keywords
                }
            )
            db.session.add(content)
            print(f"✅ Explanation for '{word}' added to lesson.")

        # Generate and add quiz questions
        print("\n--- Generating Quiz Questions ---")
        for i in range(3):
            print(f"🤖 Generating quiz question #{i+1}...")
            
            topic = "Japanese technology and internet vocabulary"
            keywords = ", ".join(VOCABULARY.keys())
            
            result = generator.generate_multiple_choice_question(topic, LESSON_DIFFICULTY, keywords)
            
            if "error" in result:
                print(f"❌ Error generating quiz question: {result['error']}")
                continue

            # Create the main content item for the quiz
            quiz_content = LessonContent(
                lesson_id=lesson.id,
                content_type="interactive",
                title=f"Quiz: {result['question_text'][:30]}...",
                is_interactive=True,
                order_index=len(VOCABULARY) + i,
                page_number=1,
                generated_by_ai=True,
                ai_generation_details={
                    "model": "gpt-4o",
                    "topic": topic,
                    "difficulty": LESSON_DIFFICULTY,
                    "keywords": keywords
                }
            )
            db.session.add(quiz_content)
            db.session.flush() # Get the ID for the quiz_content

            # Create the quiz question
            question = QuizQuestion(
                lesson_content_id=quiz_content.id,
                question_type="multiple_choice",
                question_text=result['question_text'],
                explanation=result['overall_explanation']
            )
            db.session.add(question)
            db.session.flush() # Get the ID for the question

            # Add the options
            for option_data in result['options']:
                option = QuizOption(
                    question_id=question.id,
                    option_text=option_data['text'],
                    is_correct=option_data['is_correct'],
                    feedback=option_data.get('feedback', '')
                )
                db.session.add(option)
            
            print(f"✅ Quiz question #{i+1} added to lesson.")

        db.session.commit()
        print("\n--- Lesson Creation Complete! ---")

if __name__ == "__main__":
    # Check for OpenAI API key
    if 'OPENAI_API_KEY' not in os.environ:
        print("❌ Error: OPENAI_API_KEY environment variable not set.")
        print("Please add your OpenAI API key to your .env file.")
        sys.exit(1)

    # Create Flask app
    app = create_app()
    
    # Run the lesson creation
    create_lesson(app)
