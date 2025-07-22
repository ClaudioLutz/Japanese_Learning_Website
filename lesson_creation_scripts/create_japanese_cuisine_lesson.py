#!/usr/bin/env python3
"""
This script creates a comprehensive Japanese Cuisine lesson organized into pages.
Each page covers a different dish/cuisine type with impressive images, cultural explanations, and varied quizzes.
Based on the configuration provided for intermediate-level Japanese cuisine learning.
"""
import os
import sys
import json
import urllib.request
from datetime import datetime
import uuid

# Add the project root directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

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
LESSON_TITLE = "An Intermediate Guide to Japanese Cuisine"
LESSON_DIFFICULTY = "Intermediate"
LESSON_DESCRIPTION = "Explore the rich diversity of Japanese food, from iconic dishes like sushi and ramen to the elegant art of kaiseki dining. This lesson covers key vocabulary, preparation styles, and cultural context."

# Lesson pages configuration based on the provided structure
LESSON_PAGES = [
    {
        "page_number": 1,
        "title": "Sushi & Sashimi (寿司と刺身)",
        "keywords": "sushi, sashimi, nigiri, maki, wasabi, shari (sushi rice), neta (topping), shoyu (soy sauce)",
        "image_concept": "A beautiful, high-end wooden sushi geta (platter) with a variety of vibrant nigiri sushi and glistening sashimi. Focus on the fresh textures of tuna, salmon, and shrimp. A small dish of soy sauce and a mound of wasabi are on the side. Cinematic, dramatic lighting."
    },
    {
        "page_number": 2,
        "title": "Ramen (ラーメン)",
        "keywords": "ramen, chashu (braised pork), menma (bamboo shoots), ajitama (seasoned egg), nori, tonkotsu (pork broth), shio (salt), miso",
        "image_concept": "A steaming, rich bowl of tonkotsu ramen in a traditional ceramic bowl. The noodles are perfectly arranged, topped with slices of tender chashu pork, a glistening soft-boiled egg cut in half, and bright green onions. Steam is rising from the bowl, creating a cozy atmosphere."
    },
    {
        "page_number": 3,
        "title": "Tempura (天ぷら)",
        "keywords": "tempura, ebi (shrimp), nasu (eggplant), kabocha (pumpkin), tentsuyu (dipping sauce), daikon oroshi (grated radish), koromo (batter)",
        "image_concept": "A light and crispy assortment of shrimp and vegetable tempura artistically arranged on a bamboo mat. The batter is golden and delicate. A dipping sauce is nearby. The image should convey a sense of lightness and expert frying technique."
    },
    {
        "page_number": 4,
        "title": "Yakitori (焼き鳥)",
        "keywords": "yakitori, kushi (skewer), momo (thigh), negima (scallion and chicken), tare (sauce), shio (salt), izakaya (Japanese pub)",
        "image_concept": "Several skewers of yakitori grilling over glowing charcoal on a traditional Japanese grill. The chicken is glistening with a sweet tare sauce, and some skewers have slight char marks. The atmosphere is reminiscent of a bustling, friendly izakaya at night."
    },
    {
        "page_number": 5,
        "title": "Kaiseki Ryori (懐石料理)",
        "keywords": "kaiseki, hassun (seasonal appetizer), mukozuke (sashimi dish), wanmono (lidded bowl dish), shun (seasonality), omotenashi (hospitality)",
        "image_concept": "An elegant and minimalist arrangement of a kaiseki course. A small, beautifully crafted ceramic dish holds a delicate seasonal appetizer. The focus is on balance, color, and the artistry of the presentation. The background is a serene, traditional Japanese room."
    },
    {
        "page_number": 6,
        "title": "Tonkatsu (豚カツ)",
        "keywords": "tonkatsu, panko (breadcrumbs), buta (pork), katsu sando (cutlet sandwich), karashi (mustard), kyabetsu (cabbage)",
        "image_concept": "A perfectly golden-brown, crispy panko-breaded tonkatsu pork cutlet, sliced to show the juicy interior. It is served alongside a mound of finely shredded raw cabbage and a bowl of rice. The image should look hearty, satisfying, and delicious."
    },
    {
        "page_number": 7,
        "title": "Udon & Soba (うどん・そば)",
        "keywords": "udon (wheat noodles), soba (buckwheat noodles), kakejiru (hot broth), zaru soba (cold noodles), kitsune udon (with fried tofu), tempura soba",
        "image_concept": "A side-by-side comparison. On the left, a bowl of thick, white udon noodles in a steaming hot broth. On the right, a traditional zaru tray with elegant, thin soba noodles, ready for dipping into a small cup of tsuyu sauce. The contrast between hot/hearty and cold/refined should be clear."
    },
    {
        "page_number": 8,
        "title": "Okonomiyaki & Takoyaki (お好み焼き・たこ焼き)",
        "keywords": "okonomiyaki (savory pancake), takoyaki (octopus balls), katsuobushi (bonito flakes), aonori (seaweed powder), teppan (iron griddle), tako (octopus)",
        "image_concept": "A dynamic street food scene. In the foreground, a vendor is flipping golden-brown takoyaki balls in a special molded pan. In the background, a large, sizzling okonomiyaki pancake is being topped with sauces and dancing katsuobushi flakes on a teppan grill."
    },
    {
        "page_number": 9,
        "title": "Donburi (丼)",
        "keywords": "donburi (rice bowl), gyudon (beef bowl), oyakodon (chicken and egg bowl), katsudon (pork cutlet bowl), unadon (eel bowl), gohan (rice)",
        "image_concept": "A birds-eye view of three different donburi bowls, showcasing the variety. One bowl of gyudon with tender beef and onions, one oyakodon with fluffy egg, and one katsudon with a crispy pork cutlet. The colorful toppings on the white rice make for a vibrant image."
    },
    {
        "page_number": 10,
        "title": "Japanese Curry (カレーライス)",
        "keywords": "kare raisu (curry rice), yoshoku (Western-style food), fukujinzuke (pickles), rakkyo (pickled shallots), roux (curry base)",
        "image_concept": "A comforting plate of Japanese curry rice. A pool of thick, dark brown curry sauce with chunks of potato, carrot, and beef sits next to a neat portion of white rice. A sprinkle of bright red fukujinzuke pickles adds a pop of color to the plate."
    }
]

def download_image_simple(image_url, lesson_id, app, page_number):
    """Simple image download without complex validation."""
    try:
        print(f"  Downloading image from: {image_url}")
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        filename = f"cuisine_page_{page_number}_{timestamp}_{unique_id}.png"
        
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
            description=LESSON_DESCRIPTION,
            lesson_type="free",
            difficulty_level=2,  # Intermediate
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
        
        print(f"🔑 API Key Found: ...{api_key[-4:]}")  # Print last 4 chars for verification
        
        generator = AILessonContentGenerator()
        if not generator.client:
            print("❌ AI Generator could not be initialized. Check your API key.")
            return
        
        print("✅ AI Generator Initialized")

        # Create Page 1: Lesson Introduction
        print(f"\n--- Creating Page 1: Lesson Introduction ---")
        
        content_order_index = 0
        
        # Generate introduction image
        print(f"🖼️ Generating lesson introduction image...")
        intro_image_concept = f"A beautiful overview of Japanese cuisine featuring various iconic dishes arranged elegantly. Include sushi, ramen, tempura, and other traditional foods in an artistic composition. Style: manga/anime art style, vibrant colors, clean lines, and cultural authenticity. IMPORTANT: No text, writing, signs, or Japanese characters should be visible in the image."
        
        intro_image_result = generator.generate_single_image(intro_image_concept, "1024x1024", "hd")
        
        if "error" not in intro_image_result:
            image_url = intro_image_result['image_url']
            print(f"🖼️ Introduction image URL generated: {image_url}")
            
            # Download the image
            file_path, file_size = download_image_simple(image_url, lesson.id, app, 1)
            
            if file_path:
                # Create image content item
                image_content = LessonContent(
                    lesson_id=lesson.id,
                    content_type="image",
                    title=f"{LESSON_TITLE} - Introduction",
                    content_text=f"Visual representation of {LESSON_TITLE}",
                    file_path=file_path,
                    file_size=file_size,
                    file_type="image",
                    original_filename=f"cuisine_introduction.png",
                    order_index=content_order_index,
                    page_number=1,
                    generated_by_ai=True
                )
                db.session.add(image_content)
                print(f"✅ Introduction image added to page 1.")
                content_order_index += 1

        # Generate introduction text
        print(f"🤖 Generating lesson introduction text...")
        intro_topic = f"Introduction to {LESSON_TITLE}. Provide a welcoming overview of Japanese cuisine, its cultural significance, and what students will learn in this lesson."
        intro_keywords = "Japanese cuisine, food culture, sushi, ramen, traditional cooking, culinary arts"
        
        intro_result = generator.generate_formatted_explanation(intro_topic, LESSON_DIFFICULTY, intro_keywords)
        
        if "error" not in intro_result:
            intro_content = LessonContent(
                lesson_id=lesson.id,
                content_type="text",
                title=f"Welcome to {LESSON_TITLE}",
                content_text=intro_result['generated_text'],
                order_index=content_order_index,
                page_number=1,
                generated_by_ai=True,
                ai_generation_details={
                    "model": "gpt-4.5-preview",
                    "topic": intro_topic,
                    "difficulty": LESSON_DIFFICULTY,
                    "keywords": intro_keywords
                }
            )
            db.session.add(intro_content)
            print(f"✅ Introduction text added to page 1.")
            content_order_index += 1

        # Process each sub-topic page (Pages 2 through N)
        for page_data in LESSON_PAGES:
            page_number = page_data["page_number"] + 1  # Add 1 because page 1 is introduction
            page_title = page_data["title"]
            keywords = page_data["keywords"]
            image_concept = page_data["image_concept"]
            
            print(f"\n--- Creating Page {page_number}: {page_title} ---")
            
            content_order_index = 0
            
            # 1. Generate dish image
            print(f"🖼️ Generating image for {page_title}...")
            image_prompt = f"{image_concept}. Style: simple cute manga/anime art style, vibrant colors, clean lines, and cultural authenticity. IMPORTANT: No text, writing, signs, or Japanese characters should be visible in the image. Focus on visual storytelling and culinary presentation."
            
            image_result = generator.generate_single_image(image_prompt, "1024x1024", "hd")
            
            if "error" not in image_result:
                image_url = image_result['image_url']
                print(f"🖼️ Image URL generated for {page_title}: {image_url}")
                
                # Download the image
                file_path, file_size = download_image_simple(image_url, lesson.id, app, page_number)
                
                if file_path:
                    # Create image content item
                    image_content = LessonContent(
                        lesson_id=lesson.id,
                        content_type="image",
                        title=f"{page_title} - Dish Image",
                        content_text=f"Visual representation of {page_title}",
                        file_path=file_path,
                        file_size=file_size,
                        file_type="image",
                        original_filename=f"cuisine_page_{page_number}_illustration.png",
                        order_index=content_order_index,
                        page_number=page_number,
                        generated_by_ai=True
                    )
                    db.session.add(image_content)
                    print(f"✅ Image added to page {page_number}.")
                    content_order_index += 1
            
            # 2. Generate cultural/technical overview
            print(f"🤖 Generating cultural overview for {page_title}...")
            overview_topic = f"Comprehensive cultural and technical overview of {page_title}. Include history, preparation methods, cultural significance, regional variations, and dining etiquette. Use the keywords: {keywords}"
            
            overview_result = generator.generate_formatted_explanation(overview_topic, LESSON_DIFFICULTY, keywords)
            
            if "error" not in overview_result:
                overview_content = LessonContent(
                    lesson_id=lesson.id,
                    content_type="text",
                    title=f"{page_title} - Cultural/Technical Overview",
                    content_text=overview_result['generated_text'],
                    order_index=content_order_index,
                    page_number=page_number,
                    generated_by_ai=True,
                    ai_generation_details={
                        "model": "gpt-4.5-preview",
                        "topic": overview_topic,
                        "difficulty": LESSON_DIFFICULTY,
                        "keywords": keywords
                    }
                )
                db.session.add(overview_content)
                print(f"✅ Cultural overview added to page {page_number}.")
                content_order_index += 1
            
            # 3. Generate three varied quiz questions (different types)
            print(f"🤖 Generating varied quiz questions for {page_title}...")
            
            # Define quiz types to cycle through
            quiz_types = [
                ("multiple_choice", "Multiple Choice"),
                ("true_false", "True/False"),
                ("matching", "Matching")
            ]
            
            for quiz_num in range(3):
                quiz_type, quiz_type_name = quiz_types[quiz_num % len(quiz_types)]
                topic = f"{page_title} - {quiz_type_name} question about the content presented on this page"
                
                # Generate different types of quiz questions
                if quiz_type == "multiple_choice":
                    quiz_result = generator.generate_multiple_choice_question(topic, LESSON_DIFFICULTY, keywords)
                elif quiz_type == "true_false":
                    quiz_result = generator.generate_true_false_question(topic, LESSON_DIFFICULTY, keywords)
                elif quiz_type == "matching":
                    quiz_result = generator.generate_matching_question(topic, LESSON_DIFFICULTY, keywords)
                
                if quiz_result and "error" not in quiz_result:
                    quiz_content = LessonContent(
                        lesson_id=lesson.id,
                        content_type="interactive",
                        title=f"{page_title} Quiz #{quiz_num + 1} ({quiz_type_name})",
                        content_text=f"Test your knowledge of {page_title} with this {quiz_type_name.lower()} question.",
                        is_interactive=True,
                        order_index=content_order_index,
                        page_number=page_number,
                        generated_by_ai=True
                    )
                    db.session.add(quiz_content)
                    db.session.flush()

                    if quiz_type == "multiple_choice":
                        # Handle multiple choice questions
                        options = quiz_result.get('options', [])
                        if isinstance(options, str):
                            try:
                                options = json.loads(options)
                            except json.JSONDecodeError:
                                print(f"❌ Error parsing quiz options for page {page_number}")
                                continue

                        question = QuizQuestion(
                            lesson_content_id=quiz_content.id,
                            question_type="multiple_choice",
                            question_text=quiz_result['question_text'],
                            explanation=quiz_result.get('overall_explanation', '')
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
                    
                    elif quiz_type == "true_false":
                        # Handle true/false questions
                        question = QuizQuestion(
                            lesson_content_id=quiz_content.id,
                            question_type="true_false",
                            question_text=quiz_result['question_text'],
                            explanation=quiz_result.get('explanation', '')
                        )
                        db.session.add(question)
                        db.session.flush()

                        # Create True and False options
                        correct_answer = quiz_result.get('correct_answer', True)
                        
                        true_option = QuizOption(
                            question_id=question.id,
                            option_text="True",
                            is_correct=(correct_answer == True),
                            feedback=quiz_result.get('explanation', '')
                        )
                        db.session.add(true_option)
                        
                        false_option = QuizOption(
                            question_id=question.id,
                            option_text="False",
                            is_correct=(correct_answer == False),
                            feedback=quiz_result.get('explanation', '')
                        )
                        db.session.add(false_option)
                    
                    elif quiz_type == "matching":
                        # Handle matching questions
                        question = QuizQuestion(
                            lesson_content_id=quiz_content.id,
                            question_type="matching",
                            question_text=quiz_result.get('question_text', 'Match the following items:'),
                            explanation=quiz_result.get('explanation', '')
                        )
                        db.session.add(question)
                        db.session.flush()

                        # Create options from the pairs - store prompts and answers separately
                        pairs = quiz_result.get('pairs', [])
                        if isinstance(pairs, list):
                            for i, pair_data in enumerate(pairs):
                                if isinstance(pair_data, dict):
                                    # Store prompt in option_text and answer in feedback
                                    # This allows the frontend to separate them properly
                                    option = QuizOption(
                                        question_id=question.id,
                                        option_text=pair_data.get('prompt', ''),
                                        is_correct=True,  # All pairs are correct matches
                                        feedback=pair_data.get('answer', ''),  # Store answer in feedback field
                                        order_index=i
                                    )
                                    db.session.add(option)
                    
                    print(f"✅ {quiz_type_name} Quiz #{quiz_num + 1} added to page {page_number}.")
                    content_order_index += 1
                else:
                    print(f"❌ Failed to generate {quiz_type_name} quiz for page {page_number}")

        # Create Final Page (N+1): Comprehensive Final Quiz
        final_page_number = len(LESSON_PAGES) + 2  # +1 for intro page, +1 for final page
        print(f"\n--- Creating Final Page {final_page_number}: Comprehensive Final Quiz ---")
        
        content_order_index = 0
        
        # Generate concluding text
        print(f"🤖 Generating lesson conclusion...")
        conclusion_topic = f"Conclusion for {LESSON_TITLE}. Summarize what students have learned and encourage continued exploration of Japanese cuisine."
        conclusion_keywords = "Japanese cuisine, culinary journey, cultural appreciation, food traditions"
        
        conclusion_result = generator.generate_formatted_explanation(conclusion_topic, LESSON_DIFFICULTY, conclusion_keywords)
        
        if "error" not in conclusion_result:
            conclusion_content = LessonContent(
                lesson_id=lesson.id,
                content_type="text",
                title="Lesson Conclusion",
                content_text=conclusion_result['generated_text'],
                order_index=content_order_index,
                page_number=final_page_number,
                generated_by_ai=True,
                ai_generation_details={
                    "model": "gpt-4.5-preview",
                    "topic": conclusion_topic,
                    "difficulty": LESSON_DIFFICULTY,
                    "keywords": conclusion_keywords
                }
            )
            db.session.add(conclusion_content)
            print(f"✅ Conclusion text added to final page.")
            content_order_index += 1

        # Generate comprehensive adaptive quiz
        print(f"🤖 Generating comprehensive final quiz...")
        
        quiz_topic = f"Overall Knowledge of {LESSON_TITLE}"
        difficulty_levels = [1, 2, 3]  # Use numeric difficulty levels like in the working example
        num_questions_per_level = 2
        
        adaptive_quiz_result = generator.create_adaptive_quiz(quiz_topic, difficulty_levels, num_questions_per_level)
        
        if adaptive_quiz_result and "error" not in adaptive_quiz_result and "questions" in adaptive_quiz_result:
            quiz_content = LessonContent(
                lesson_id=lesson.id,
                content_type="interactive",
                title="Comprehensive Final Quiz",
                content_text="Test your overall knowledge of Japanese cuisine from this lesson.",
                is_interactive=True,
                order_index=content_order_index,
                page_number=final_page_number,
                generated_by_ai=True
            )
            db.session.add(quiz_content)
            db.session.flush()

            # Process the adaptive quiz questions
            questions_data = adaptive_quiz_result.get('questions', [])
            if isinstance(questions_data, list):
                for q_data in questions_data:
                    if isinstance(q_data, dict):
                        question = QuizQuestion(
                            lesson_content_id=quiz_content.id,
                            question_type="multiple_choice",
                            question_text=q_data.get('question_text', ''),
                            explanation=q_data.get('overall_explanation', ''),
                            difficulty_level=q_data.get('difficulty_level', 2)
                        )
                        db.session.add(question)
                        db.session.flush()

                        options_data = q_data.get('options', [])
                        if isinstance(options_data, list):
                            for option_data in options_data:
                                if isinstance(option_data, dict):
                                    option = QuizOption(
                                        question_id=question.id,
                                        option_text=option_data.get('text', ''),
                                        is_correct=option_data.get('is_correct', False),
                                        feedback=option_data.get('feedback', '')
                                    )
                                    db.session.add(option)
                
                print(f"✅ Comprehensive final quiz added to final page.")
            else:
                print(f"❌ Invalid questions data format in adaptive quiz result.")
        else:
            print(f"❌ Failed to generate adaptive quiz: {adaptive_quiz_result.get('error', 'Unknown error') if adaptive_quiz_result else 'No result'}")

        db.session.commit()
        print("\n--- Japanese Cuisine Lesson Creation Complete! ---")
        print(f"✅ {LESSON_TITLE} lesson created successfully!")
        print(f"   - 1 introduction page with overview image and text")
        print(f"   - {len(LESSON_PAGES)} sub-topic pages covering different Japanese dishes")
        print(f"   - Each sub-topic page contains: dish image, cultural/technical overview, and 3 varied quiz questions (Multiple Choice, True/False, Matching)")
        print(f"   - 1 final page with conclusion and comprehensive adaptive quiz")
        print(f"   - Total pages: {final_page_number}")
        print(f"   - Covers: Sushi & Sashimi, Ramen, Tempura, Yakitori, Kaiseki, Tonkatsu, Udon & Soba, Okonomiyaki & Takoyaki, Donburi, Japanese Curry")

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
