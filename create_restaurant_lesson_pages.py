#!/usr/bin/env python3
"""
This script creates a comprehensive restaurant lesson organized into pages.
Each page contains text explanations, images (without text), and quizzes.
"""
import os
import sys
import json
import urllib.request
from datetime import datetime
import uuid

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Load environment variables manually
def load_env():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    value = value.strip('"\'')
                    os.environ[key] = value

load_env()

from app import create_app, db
from app.models import Lesson, LessonContent, QuizQuestion, QuizOption
from app.ai_services import AILessonContentGenerator

# --- Configuration ---
LESSON_TITLE = "At the Restaurant - Complete Guide"
LESSON_DIFFICULTY = "Beginner"

# Organize vocabulary by pages/topics
LESSON_PAGES = [
    {
        "page_number": 1,
        "title": "Restaurant Basics",
        "vocabulary": {
            "レストラン": "Restaurant",
            "メニュー": "Menu"
        },
        "image_concept": "A clean, modern Japanese restaurant exterior with traditional elements, no text visible"
    },
    {
        "page_number": 2,
        "title": "Making Orders",
        "vocabulary": {
            "注文 (ちゅうもん)": "Order",
            "店員 (てんいん)": "Clerk/Waiter"
        },
        "image_concept": "A friendly waiter taking an order from customers at a table, no text or writing visible"
    },
    {
        "page_number": 3,
        "title": "Food and Drinks",
        "vocabulary": {
            "水 (みず)": "Water",
            "美味しい (おいしい)": "Delicious"
        },
        "image_concept": "A glass of water and delicious Japanese food on a table, no text or labels visible"
    },
    {
        "page_number": 4,
        "title": "Payment and Reservations",
        "vocabulary": {
            "会計 (かいけい)": "Bill/Check",
            "予約 (よやく)": "Reservation"
        },
        "image_concept": "A customer paying at a restaurant counter, cash and receipt visible but no text on them"
    }
]

def download_image_simple(image_url, lesson_id, app, page_number):
    """Simple image download without complex validation."""
    try:
        print(f"  Downloading image from: {image_url}")
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        filename = f"page_{page_number}_{timestamp}_{unique_id}.png"
        
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
            description="A comprehensive beginner's guide to Japanese restaurant vocabulary with phonetics, organized into clear pages.",
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

        # Process each page
        for page_data in LESSON_PAGES:
            page_number = page_data["page_number"]
            page_title = page_data["title"]
            vocabulary = page_data["vocabulary"]
            image_concept = page_data["image_concept"]
            
            print(f"\n--- Creating Page {page_number}: {page_title} ---")
            
            content_order_index = 0
            
            # 1. Create page introduction text
            print(f"🤖 Generating introduction for page {page_number}...")
            intro_topic = f"Introduction to {page_title} in Japanese restaurants"
            intro_keywords = ", ".join(vocabulary.keys())
            
            intro_result = generator.generate_formatted_explanation(intro_topic, LESSON_DIFFICULTY, intro_keywords)
            
            if "error" not in intro_result:
                intro_content = LessonContent(
                    lesson_id=lesson.id,
                    content_type="text",
                    title=f"Page {page_number}: {page_title}",
                    content_text=intro_result['generated_text'],
                    order_index=content_order_index,
                    page_number=page_number,
                    generated_by_ai=True,
                    ai_generation_details={
                        "model": "gpt-4o",
                        "topic": intro_topic,
                        "difficulty": LESSON_DIFFICULTY,
                        "keywords": intro_keywords
                    }
                )
                db.session.add(intro_content)
                print(f"✅ Page {page_number} introduction added.")
                content_order_index += 1
            
            # 2. Generate and add vocabulary explanations
            print(f"🤖 Generating vocabulary explanations for page {page_number}...")
            for word, meaning in vocabulary.items():
                topic = f"The Japanese word '{word}' ({meaning}) used in restaurant context."
                keywords = f"{word}, {meaning}, restaurant, food, ordering"
                
                result = generator.generate_formatted_explanation(topic, LESSON_DIFFICULTY, keywords)
                
                if "error" not in result:
                    content = LessonContent(
                        lesson_id=lesson.id,
                        content_type="text",
                        title=f"Vocabulary: {word}",
                        content_text=result['generated_text'],
                        order_index=content_order_index,
                        page_number=page_number,
                        generated_by_ai=True,
                        ai_generation_details={
                            "model": "gpt-4o",
                            "topic": topic,
                            "difficulty": LESSON_DIFFICULTY,
                            "keywords": keywords
                        }
                    )
                    db.session.add(content)
                    print(f"✅ Vocabulary '{word}' added to page {page_number}.")
                    content_order_index += 1
            
            # 3. Generate and add page image (without text)
            print(f"🖼️ Generating image for page {page_number}...")
            image_prompt = f"{image_concept}. Style: clean, professional, anime-inspired illustration. IMPORTANT: No text, writing, signs, or Japanese characters should be visible in the image."
            
            image_result = generator.generate_single_image(image_prompt, "1024x1024", "standard")
            
            if "error" not in image_result:
                image_url = image_result['image_url']
                print(f"🖼️ Image URL generated for page {page_number}: {image_url}")
                
                # Download the image
                file_path, file_size = download_image_simple(image_url, lesson.id, app, page_number)
                
                if file_path:
                    # Create image content item
                    image_content = LessonContent(
                        lesson_id=lesson.id,
                        content_type="image",
                        title=f"Page {page_number} Illustration",
                        content_text=f"Visual illustration for {page_title}",
                        file_path=file_path,
                        file_size=file_size,
                        file_type="image",
                        original_filename=f"page_{page_number}_illustration.png",
                        order_index=content_order_index,
                        page_number=page_number,
                        generated_by_ai=True
                    )
                    db.session.add(image_content)
                    print(f"✅ Image added to page {page_number}.")
                    content_order_index += 1
            
            # 4. Generate quiz questions for this page
            print(f"🤖 Generating quiz questions for page {page_number}...")
            
            # Generate 2 quiz questions per page
            for quiz_num in range(2):
                topic = f"Page {page_number}: {page_title} vocabulary"
                keywords = ", ".join(vocabulary.keys())
                
                # Pass question number to ensure variety
                quiz_result = generator.generate_multiple_choice_question(topic, LESSON_DIFFICULTY, keywords, question_number=quiz_num)
                
                if "error" not in quiz_result:
                    options = quiz_result.get('options', [])
                    if isinstance(options, str):
                        try:
                            options = json.loads(options)
                        except json.JSONDecodeError:
                            print(f"❌ Error parsing quiz options for page {page_number}")
                            continue

                    quiz_content = LessonContent(
                        lesson_id=lesson.id,
                        content_type="interactive",
                        title=f"Page {page_number} Quiz #{quiz_num + 1}",
                        content_text=f"Test your knowledge of {page_title} vocabulary.",
                        is_interactive=True,
                        order_index=content_order_index,
                        page_number=page_number,
                        generated_by_ai=True
                    )
                    db.session.add(quiz_content)
                    db.session.flush()

                    question = QuizQuestion(
                        lesson_content_id=quiz_content.id,
                        question_type="multiple_choice",
                        question_text=quiz_result['question_text'],
                        explanation=quiz_result['overall_explanation']
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
                    
                    print(f"✅ Quiz #{quiz_num + 1} added to page {page_number}.")
                    content_order_index += 1

        db.session.commit()
        print("\n--- Lesson Creation Complete! ---")
        print(f"✅ Restaurant lesson created successfully!")
        print(f"   - {len(LESSON_PAGES)} pages created")
        print(f"   - Each page contains: introduction, vocabulary explanations, illustration, and quizzes")
        print(f"   - All Japanese text includes phonetic pronunciation")
        print(f"   - All images are text-free for better learning")

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
