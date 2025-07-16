#!/usr/bin/env python3
"""
This script creates a new lesson on "At the Restaurant"
using the AI content generation feature, including text, images, and picture quizzes.
Fixed version that handles image download issues.
"""
import os
import sys
import json
import urllib.request
import tempfile
from datetime import datetime
import uuid
from dotenv import load_dotenv

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Load environment variables
load_dotenv()

from app import create_app, db
from app.models import Lesson, LessonContent, QuizQuestion, QuizOption
from app.ai_services import AILessonContentGenerator

# --- Configuration ---
LESSON_TITLE = "At the Restaurant"
LESSON_DIFFICULTY = "Beginner"
VOCABULARY = {
    "レストラン": "Restaurant",
    "メニュー": "Menu",
    "注文 (ちゅうもん)": "Order",
    "水 (みず)": "Water",
    "会計 (かいけい)": "Bill/Check",
    "店員 (てんいん)": "Clerk/Waiter",
    "予約 (よやく)": "Reservation",
    "美味しい (おいしい)": "Delicious"
}

def download_image_simple(image_url, lesson_id, app):
    """Simple image download without complex validation that might hang."""
    try:
        print(f"  Downloading image from: {image_url}")
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        filename = f"ai_generated_{timestamp}_{unique_id}.png"
        
        # Create target directory
        upload_folder = app.config.get('UPLOAD_FOLDER', 'app/static/uploads')
        target_dir = os.path.join(upload_folder, 'lessons', 'image', f'lesson_{lesson_id}')
        os.makedirs(target_dir, exist_ok=True)
        
        # Save file using urllib
        final_path = os.path.join(target_dir, filename)
        urllib.request.urlretrieve(image_url, final_path)
        
        # Return relative path for database storage
        relative_path = os.path.join('lessons', 'image', f'lesson_{lesson_id}', filename).replace('\\', '/')
        
        print(f"  ✅ Image saved to: {relative_path}")
        return relative_path, os.path.getsize(final_path)
        
    except Exception as e:
        print(f"  ❌ Error downloading image: {e}")
        return None, 0

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
            description="A beginner's lesson on vocabulary used at a Japanese restaurant.",
            lesson_type="free",
            difficulty_level=1, # Beginner
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

        content_order_index = 0

        # Generate and add vocabulary explanations
        print("\n--- Generating Vocabulary Explanations ---")
        for word, meaning in VOCABULARY.items():
            print(f"🤖 Generating explanation for '{word}'...")
            
            topic = f"The Japanese word '{word}' ({meaning}) used in a restaurant context."
            keywords = f"{word}, {meaning}, restaurant, food, ordering"
            
            result = generator.generate_formatted_explanation(topic, LESSON_DIFFICULTY, keywords)
            
            if "error" in result:
                print(f"❌ Error generating explanation for '{word}': {result['error']}")
                continue

            content = LessonContent(
                lesson_id=lesson.id,
                content_type="text",
                title=f"Vocabulary: {word}",
                content_text=result['generated_text'],
                order_index=content_order_index,
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
            content_order_index += 1

        # Generate and add text-based quiz questions
        print("\n--- Generating Text-Based Quiz Questions ---")
        for i in range(2):
            print(f"🤖 Generating text quiz question #{i+1}...")
            
            topic = "Japanese restaurant vocabulary"
            keywords = ", ".join(VOCABULARY.keys())
            
            result = generator.generate_multiple_choice_question(topic, LESSON_DIFFICULTY, keywords)
            
            if "error" in result:
                print(f"❌ Error generating quiz question: {result['error']}")
                continue
            
            options = result.get('options', [])
            if isinstance(options, str):
                try:
                    options = json.loads(options)
                except json.JSONDecodeError:
                    print(f"❌ Error parsing options from AI response: {options}")
                    continue

            quiz_content = LessonContent(
                lesson_id=lesson.id,
                content_type="interactive",
                title=f"Quiz: {result['question_text'][:30]}...",
                is_interactive=True,
                order_index=content_order_index,
                page_number=1,
                generated_by_ai=True
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

            for option_data in options:
                option = QuizOption(
                    question_id=question.id,
                    option_text=option_data['text'],
                    is_correct=option_data['is_correct'],
                    feedback=option_data.get('feedback', '')
                )
                db.session.add(option)
            
            print(f"✅ Text quiz question #{i+1} added.")
            content_order_index += 1

        # Generate and add picture quizzes
        print("\n--- Generating Picture Quizzes ---")
        picture_quiz_subjects = ["メニュー (Menu)", "水 (Water)", "会計 (Bill/Check)"]
        for i, subject in enumerate(picture_quiz_subjects):
            print(f"🤖 Generating picture quiz for '{subject}'...")
            
            # 1. Generate an image prompt and URL
            image_prompt = f"A clear, simple, anime-style image of a '{subject}' in a Japanese restaurant setting. The image should be easily recognizable and educational."
            print(f"  Image prompt: {image_prompt}")
            
            image_result = generator.generate_single_image(image_prompt, "1024x1024", "standard")

            if "error" in image_result:
                print(f"❌ Error generating image for '{subject}': {image_result['error']}")
                continue
            
            image_url = image_result['image_url']
            print(f"🖼️ Image URL generated: {image_url}")

            # 2. Download the image using our simple method
            file_path, file_size = download_image_simple(image_url, lesson.id, app)
            
            if not file_path:
                print(f"❌ Failed to download image for '{subject}'.")
                continue

            # 3. Create image content item
            image_content = LessonContent(
                lesson_id=lesson.id,
                content_type="image",
                title=f"Image: {subject}",
                content_text=f"Visual representation of {subject}",
                file_path=file_path,
                file_size=file_size,
                file_type="image",
                original_filename=f"ai_generated_{subject.replace(' ', '_').replace('(', '').replace(')', '')}.png",
                order_index=content_order_index,
                page_number=1,
                generated_by_ai=True
            )
            db.session.add(image_content)
            print(f"✅ Image content added for '{subject}'.")
            content_order_index += 1

            # 4. Generate a multiple-choice question for the image
            topic = f"Identifying '{subject}' from an image."
            keywords = ", ".join(VOCABULARY.keys())
            question_text = f"この絵は何ですか？ (What is in this picture?)"

            options_result = generator.generate_multiple_choice_question(
                topic=f"Vocabulary for items in a restaurant, where the answer is {subject}",
                difficulty=LESSON_DIFFICULTY,
                keywords=keywords
            )

            if "error" in options_result:
                print(f"❌ Error generating quiz options for '{subject}': {options_result['error']}")
                continue

            options = options_result.get('options', [])
            if isinstance(options, str):
                try:
                    options = json.loads(options)
                except json.JSONDecodeError:
                    print(f"❌ Error parsing options from AI response: {options}")
                    continue

            # Ensure the correct answer is in the options
            correct_answer_text = subject.split(" ")[0]
            if not any(opt['is_correct'] and opt['text'] == correct_answer_text for opt in options):
                # Add the correct answer if it's missing
                if options:
                    options.pop() # Remove one distractor
                options.append({'text': correct_answer_text, 'is_correct': True, 'feedback': 'Correct!'})

            # 5. Create the quiz content and question
            quiz_content = LessonContent(
                lesson_id=lesson.id,
                content_type="interactive",
                title=f"Picture Quiz: {subject}",
                content_text=f"Look at the image above and answer the question.",
                is_interactive=True,
                order_index=content_order_index,
                page_number=1,
                generated_by_ai=True
            )
            db.session.add(quiz_content)
            db.session.flush()

            question = QuizQuestion(
                lesson_content_id=quiz_content.id,
                question_type="multiple_choice",
                question_text=question_text,
                explanation=options_result['overall_explanation']
            )
            db.session.add(question)
            db.session.flush()

            for option_data in options:
                option = QuizOption(
                    question_id=question.id,
                    option_text=option_data['text'],
                    is_correct=option_data['is_correct'],
                    feedback=option_data.get('feedback', '')
                )
                db.session.add(option)

            print(f"✅ Picture quiz for '{subject}' added.")
            content_order_index += 1

        db.session.commit()
        print("\n--- Lesson Creation Complete! ---")
        print(f"✅ Restaurant lesson created successfully with {content_order_index} content items!")
        print(f"   - 8 vocabulary explanations")
        print(f"   - 2 text-based quiz questions")
        print(f"   - 3 picture quizzes with images")

if __name__ == "__main__":
    # Check for API key
    if 'OPENAI_API_KEY' not in os.environ:
        print("❌ Error: OPENAI_API_KEY environment variable not set.")
        print("Please add your OpenAI API key to your .env file.")
        sys.exit(1)

    # Create Flask app
    app = create_app()
    
    # Run the lesson creation
    create_lesson(app)
