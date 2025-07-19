#!/usr/bin/env python3
"""
This script creates a comprehensive Japanese Onomatopoeia and Mimetic Words lesson organized into pages.
Each content page covers different daily life scenarios with onomatopoeia, followed by dedicated quiz pages.
The quizzes are separated from the explanatory content as requested.
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
LESSON_TITLE = "Onomatopoeia and Mimetic Words in Daily Life"
LESSON_DIFFICULTY = "Intermediate"
LESSON_DESCRIPTION = "Discover the vibrant world of Japanese onomatopoeia and mimetic words used in everyday situations. Learn how sound words and descriptive expressions bring Japanese language to life through daily scenarios."

# Lesson content pages configuration (explanation pages only)
CONTENT_PAGES = [
    {
        "page_number": 2,
        "title": "Morning Routines - 朝の音 (Asa no Oto)",
        "keywords": "morning, alarm, water, brushing teeth, shower, wake up sounds, りんりん, ざあざあ, しゃかしゃか, ぴちゃぴちゃ, daily routine",
        "image_concept": "Peaceful morning scene showing various morning routine activities with visual sound effects - alarm clock ringing, water flowing from tap, toothbrush sounds, shower running, birds chirping outside window. Style: cute manga/anime art style with clean lines and cultural authenticity. IMPORTANT: No text, writing, signs, or characters should be visible in the image.",
        "content_focus": "Common morning sounds and activities: alarm clocks (りんりん), water sounds (ざあざあ, ぴちゃぴちゃ), brushing teeth (しゃかしゃか), and other morning routine onomatopoeia."
    },
    {
        "page_number": 3,
        "title": "Cooking and Eating - 料理の音 (Ryouri no Oto)",
        "keywords": "cooking, eating, sizzling, chopping, slurping, ジュージュー, トントン, ずるずる, ぺろぺろ, kitchen sounds, food preparation",
        "image_concept": "Lively kitchen scene with someone cooking - sizzling pan, chopping vegetables, boiling water, eating noodles with chopsticks, various cooking activities with sound effect visualizations. Style: cute manga/anime art style with clean lines and cultural authenticity. IMPORTANT: No text, writing, signs, or characters should be visible in the image.",
        "content_focus": "Kitchen and eating sounds: sizzling (ジュージュー), chopping (トントン), slurping noodles (ずるずる), licking (ぺろぺろ), and cooking-related onomatopoeia."
    },
    {
        "page_number": 4,
        "title": "Weather and Nature - 天気と自然の音 (Tenki to Shizen no Oto)",
        "keywords": "weather, nature, rain, wind, thunder, animals, ざあざあ, ごろごろ, ひゅうひゅう, ちゅんちゅん, わんわん, にゃあにゃあ",
        "image_concept": "Beautiful nature scene showing different weather conditions and animals - rain falling, wind blowing trees, thunder clouds, birds singing, dogs barking, cats meowing, seasonal atmosphere. Style: cute manga/anime art style with clean lines and cultural authenticity. IMPORTANT: No text, writing, signs, or characters should be visible in the image.",
        "content_focus": "Natural sounds and weather: heavy rain (ざあざあ), thunder (ごろごろ), wind (ひゅうひゅう), bird songs (ちゅんちゅん), and animal sounds (わんわん, にゃあにゃあ)."
    },
    {
        "page_number": 5,
        "title": "Emotions and Feelings - 感情の表現 (Kanjou no Hyougen)",
        "keywords": "emotions, feelings, heart beating, sighing, laughing, どきどき, はあはあ, あはは, えーん, うるうる, excitement, sadness",
        "image_concept": "Expressive scene showing various emotional states - person with racing heart, sighing, laughing with friends, crying, sparkling eyes with emotion, emotional expressions in daily life. Style: cute manga/anime art style with clean lines and cultural authenticity. IMPORTANT: No text, writing, signs, or characters should be visible in the image.",
        "content_focus": "Emotional expressions: heart racing (どきどき), heavy breathing (はあはあ), laughter (あはは), crying (えーん), teary eyes (うるうる), and feeling-related mimetic words."
    },
    {
        "page_number": 6,
        "title": "Movement and Actions - 動きの音 (Ugoki no Oto)",
        "keywords": "movement, walking, running, falling, jumping, てくてく, だだだ, どすん, ぴょんぴょん, するする, physical actions",
        "image_concept": "Dynamic scene showing various movements and actions - people walking, running, jumping, something falling, smooth sliding motions, active daily life movements. Style: cute manga/anime art style with clean lines and cultural authenticity. IMPORTANT: No text, writing, signs, or characters should be visible in the image.",
        "content_focus": "Movement sounds: walking (てくてく), running (だだだ), falling (どすん), jumping (ぴょんぴょん), sliding smoothly (するする), and action-related onomatopoeia."
    },
    {
        "page_number": 7,
        "title": "Communication Sounds - コミュニケーションの音 (Communication no Oto)",
        "keywords": "communication, phone, knocking, typing, doorbell, りんりん, こんこん, かたかた, ぴんぽん, がちゃがちゃ, daily communication",
        "image_concept": "Communication scene showing phone ringing, someone knocking on door, typing on keyboard, doorbell, various communication devices and interactions in daily life. Style: cute manga/anime art style with clean lines and cultural authenticity. IMPORTANT: No text, writing, signs, or characters should be visible in the image.",
        "content_focus": "Communication sounds: phone ringing (りんりん), knocking (こんこん), typing (かたかた), doorbell (ぴんぽん), rattling (がちゃがちゃ), and interaction-related sounds."
    },
    {
        "page_number": 8,
        "title": "Household Activities - 家事の音 (Kaji no Oto)",
        "keywords": "household, cleaning, washing, opening, closing, ごしごし, じゃぶじゃぶ, がらがら, ぱたん, きゅっきゅっ, domestic activities",
        "image_concept": "Busy household scene with cleaning activities - scrubbing, washing dishes, opening/closing doors and windows, squeaky clean sounds, domestic life activities. Style: cute manga/anime art style with clean lines and cultural authenticity. IMPORTANT: No text, writing, signs, or characters should be visible in the image.",
        "content_focus": "Household sounds: scrubbing (ごしごし), washing (じゃぶじゃぶ), rattling (がらがら), closing gently (ぱたん), squeaky clean (きゅっきゅっ), and cleaning-related onomatopoeia."
    },
    {
        "page_number": 9,
        "title": "Transportation - 交通の音 (Koutsu no Oto)",
        "keywords": "transportation, car, train, bicycle, ブーブー, がたんごとん, りんりん, ぶるるん, vehicle sounds, travel, movement",
        "image_concept": "Transportation scene showing various vehicles - cars driving, trains on tracks, bicycles with bells, engines starting, busy transportation hub with different vehicle sounds. Style: cute manga/anime art style with clean lines and cultural authenticity. IMPORTANT: No text, writing, signs, or characters should be visible in the image.",
        "content_focus": "Transportation sounds: car engine (ブーブー), train on tracks (がたんごとん), bicycle bell (りんりん), engine revving (ぶるるん), and vehicle-related onomatopoeia."
    }
]

def download_image_simple(image_url, lesson_id, app, page_number):
    """Simple image download without complex validation."""
    try:
        print(f"  Downloading image from: {image_url}")
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        filename = f"onomatopoeia_page_{page_number}_{timestamp}_{unique_id}.png"
        
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
            lesson_type="free",  # or "premium"
            difficulty_level=2,  # 1=Beginner, 2=Intermediate, 3=Advanced
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
        
        generator = AILessonContentGenerator()
        if not generator.client:
            print("❌ AI Generator could not be initialized. Check your API key.")
            return
        
        print("✅ AI Generator Initialized")

        # Create Page 1: Lesson Introduction
        print(f"\n--- Creating Introduction Page ---")
        
        content_order_index = 0
        
        # Generate overview image
        print(f"🖼️ Generating lesson overview image...")
        overview_image_concept = "Vibrant collage showing various Japanese onomatopoeia in daily life - sound waves, speech bubbles with sound effects, people in different daily activities (cooking, walking, talking), nature sounds, emotional expressions, all in a harmonious composition representing the richness of Japanese sound words. Style: cute manga/anime art style with clean lines and cultural authenticity. IMPORTANT: No text, writing, signs, or characters should be visible in the image."
        
        image_result = generator.generate_single_image(overview_image_concept, "1024x1024", "hd")
        
        if "error" not in image_result:
            image_url = image_result['image_url']
            print(f"🖼️ Overview image URL generated: {image_url}")
            
            # Download the image
            file_path, file_size = download_image_simple(image_url, lesson.id, app, 1)
            
            if file_path:
                # Create image content item
                image_content = LessonContent(
                    lesson_id=lesson.id,
                    content_type="image",
                    title="Onomatopoeia and Mimetic Words - Lesson Overview",
                    content_text="Welcome to the vibrant world of Japanese sound words",
                    file_path=file_path,
                    file_size=file_size,
                    file_type="image",
                    original_filename="onomatopoeia_overview.png",
                    order_index=content_order_index,
                    page_number=1,
                    generated_by_ai=True
                )
                db.session.add(image_content)
                print(f"✅ Overview image added to introduction page.")
                content_order_index += 1

        # Generate welcoming introduction text
        print(f"🤖 Generating lesson introduction...")
        intro_topic = f"Comprehensive introduction to {LESSON_TITLE}. Explain what students will learn about Japanese onomatopoeia (giongo) and mimetic words (gitaigo), their importance in daily communication, how they make Japanese language more expressive and vivid, and what daily life scenarios will be covered. Include learning objectives and cultural significance of sound words in Japanese."
        intro_keywords = "onomatopoeia, mimetic words, giongo, gitaigo, daily life, Japanese expressions, sound words, cultural communication, language learning"
        
        intro_result = generator.generate_formatted_explanation(intro_topic, LESSON_DIFFICULTY, intro_keywords)
        
        if "error" not in intro_result:
            intro_content = LessonContent(
                lesson_id=lesson.id,
                content_type="text",
                title="Welcome to Japanese Onomatopoeia",
                content_text=intro_result['generated_text'],
                order_index=content_order_index,
                page_number=1,
                generated_by_ai=True,
                ai_generation_details={
                    "model": "gpt-4.1",
                    "topic": intro_topic,
                    "difficulty": LESSON_DIFFICULTY,
                    "keywords": intro_keywords
                }
            )
            db.session.add(intro_content)
            print(f"✅ Introduction text added to page 1.")
            content_order_index += 1

        # Process each content page with its corresponding quiz page in sequence
        current_page_number = 2  # Start after introduction page
        
        for page_data in CONTENT_PAGES:
            page_title = page_data["title"]
            keywords = page_data["keywords"]
            image_concept = page_data["image_concept"]
            content_focus = page_data["content_focus"]
            
            # Create content page (explanation page)
            content_page_number = current_page_number
            print(f"\n--- Creating Content Page {content_page_number}: {page_title} ---")
            
            content_order_index = 0
            
            # 1. Generate scene image
            print(f"🖼️ Generating scene image for page {content_page_number}...")
            
            image_result = generator.generate_single_image(image_concept, "1024x1024", "hd")
            
            if "error" not in image_result:
                image_url = image_result['image_url']
                print(f"🖼️ Image URL generated for page {content_page_number}: {image_url}")
                
                # Download the image
                file_path, file_size = download_image_simple(image_url, lesson.id, app, content_page_number)
                
                if file_path:
                    # Create image content item
                    image_content = LessonContent(
                        lesson_id=lesson.id,
                        content_type="image",
                        title=f"{page_title} - Scene Image",
                        content_text=f"Visual representation of {page_title}",
                        file_path=file_path,
                        file_size=file_size,
                        file_type="image",
                        original_filename=f"onomatopoeia_page_{content_page_number}_illustration.png",
                        order_index=content_order_index,
                        page_number=content_page_number,
                        generated_by_ai=True
                    )
                    db.session.add(image_content)
                    print(f"✅ Scene image added to page {content_page_number}.")
                    content_order_index += 1
            
            # 2. Generate comprehensive explanation (no quizzes on this page)
            print(f"🤖 Generating comprehensive explanation for {page_title}...")
            explanation_topic = f"Comprehensive explanation of {page_title}. Focus on: {content_focus}. Include detailed explanations of each onomatopoeia word, how they're used in context, cultural significance, pronunciation tips, and practical examples in daily life situations. Make it engaging and educational for intermediate learners. Keywords: {keywords}"
            
            explanation_result = generator.generate_formatted_explanation(explanation_topic, LESSON_DIFFICULTY, keywords)
            
            if "error" not in explanation_result:
                explanation_content = LessonContent(
                    lesson_id=lesson.id,
                    content_type="text",
                    title=f"{page_title} - Detailed Explanation",
                    content_text=explanation_result['generated_text'],
                    order_index=content_order_index,
                    page_number=content_page_number,
                    generated_by_ai=True,
                    ai_generation_details={
                        "model": "gpt-4.1",
                        "topic": explanation_topic,
                        "difficulty": LESSON_DIFFICULTY,
                        "keywords": keywords
                    }
                )
                db.session.add(explanation_content)
                print(f"✅ Page {content_page_number} explanation added.")
                content_order_index += 1

            # Create corresponding quiz page immediately after content page
            quiz_page_number = current_page_number + 1
            print(f"\n--- Creating Quiz Page {quiz_page_number} for {page_title} ---")
            
            quiz_content_order_index = 0
            
            # Generate varied quiz questions (4 per quiz page)
            print(f"🤖 Generating quiz questions for {page_title}...")
            
            # Quiz types cycle through different formats - 4 quizzes per page
            quiz_types = [
                ("multiple_choice", "Multiple Choice"),
                ("true_false", "True/False"),
                ("matching", "Matching"),
                ("multiple_choice", "Multiple Choice")
            ]
            
            for quiz_num in range(4):  # 4 quizzes per quiz page
                quiz_type, quiz_name = quiz_types[quiz_num]
                
                print(f"  Generating {quiz_name} quiz #{quiz_num + 1}...")
                
                if quiz_type == "multiple_choice":
                    quiz_result = generator.generate_multiple_choice_question(
                        f"{page_title} onomatopoeia and mimetic words knowledge. Focus on: {content_focus}", 
                        LESSON_DIFFICULTY, 
                        keywords,
                        question_number=quiz_num
                    )
                elif quiz_type == "true_false":
                    quiz_result = generator.generate_true_false_question(
                        f"{page_title} onomatopoeia facts and usage. Focus on: {content_focus}", 
                        LESSON_DIFFICULTY, 
                        keywords
                    )
                else:  # matching
                    quiz_result = generator.generate_matching_question(
                        f"{page_title} onomatopoeia vocabulary and meanings. Focus on: {content_focus}", 
                        LESSON_DIFFICULTY, 
                        keywords
                    )
                
                if "error" not in quiz_result:
                    # Create quiz content
                    quiz_content = LessonContent(
                        lesson_id=lesson.id,
                        content_type="interactive",
                        title=f"{page_title} - {quiz_name} Quiz #{quiz_num + 1}",
                        content_text=f"Test your knowledge about {page_title}",
                        is_interactive=True,
                        order_index=quiz_content_order_index,
                        page_number=quiz_page_number,
                        generated_by_ai=True
                    )
                    db.session.add(quiz_content)
                    db.session.flush()

                    # Create question
                    question = QuizQuestion(
                        lesson_content_id=quiz_content.id,
                        question_type=quiz_type,
                        question_text=quiz_result['question_text'],
                        explanation=quiz_result.get('overall_explanation', quiz_result.get('explanation', ''))
                    )
                    db.session.add(question)
                    db.session.flush()

                    # Handle different quiz types with their specific data structures
                    if quiz_type == "multiple_choice":
                        # Multiple choice has 'options' array
                        options = quiz_result.get('options', [])
                        if isinstance(options, str):
                            try:
                                options = json.loads(options)
                            except json.JSONDecodeError:
                                print(f"❌ Error parsing multiple choice options for quiz page {quiz_page_number}")
                                continue

                        for option_data in options:
                            option = QuizOption(
                                question_id=question.id,
                                option_text=option_data['text'],
                                is_correct=option_data['is_correct'],
                                feedback=option_data.get('feedback', '')
                            )
                            db.session.add(option)
                    
                    elif quiz_type == "true_false":
                        # True/false has 'correct_answer' boolean
                        correct_answer = quiz_result.get('correct_answer', True)
                        
                        # Create True option
                        true_option = QuizOption(
                            question_id=question.id,
                            option_text="True",
                            is_correct=(correct_answer == True),
                            feedback=quiz_result.get('explanation', '')
                        )
                        db.session.add(true_option)
                        
                        # Create False option
                        false_option = QuizOption(
                            question_id=question.id,
                            option_text="False",
                            is_correct=(correct_answer == False),
                            feedback=quiz_result.get('explanation', '')
                        )
                        db.session.add(false_option)
                    
                    elif quiz_type == "matching":
                        # Matching has 'pairs' array
                        pairs = quiz_result.get('pairs', [])
                        if isinstance(pairs, str):
                            try:
                                pairs = json.loads(pairs)
                            except json.JSONDecodeError:
                                print(f"❌ Error parsing matching pairs for quiz page {quiz_page_number}")
                                continue
                        
                        # For matching questions, we create options where:
                        # - option_text contains the prompt (Japanese onomatopoeia)
                        # - feedback contains the correct answer (English meaning/description)
                        # - is_correct is always True for matching (since each has its correct pair)
                        for i, pair in enumerate(pairs):
                            if isinstance(pair, dict) and 'prompt' in pair and 'answer' in pair:
                                # Create one option per pair with prompt as option_text and answer as feedback
                                matching_option = QuizOption(
                                    question_id=question.id,
                                    option_text=pair['prompt'],  # Japanese onomatopoeia with romanization
                                    is_correct=True,  # All matching options are "correct" in their pairing
                                    feedback=pair['answer'],  # English meaning/description
                                    order_index=i
                                )
                                db.session.add(matching_option)
                    
                    print(f"✅ {quiz_name} quiz #{quiz_num + 1} added to quiz page {quiz_page_number}.")
                    quiz_content_order_index += 1
                else:
                    print(f"❌ Error generating {quiz_name} quiz #{quiz_num + 1}: {quiz_result.get('error', 'Unknown error')}")

            # Move to next pair of pages (content + quiz)
            current_page_number += 2

        # Create Final Page: Comprehensive Final Quiz and Conclusion
        final_page_number = current_page_number
        print(f"\n--- Creating Final Page {final_page_number}: Comprehensive Quiz and Conclusion ---")
        
        content_order_index = 0
        
        # Generate conclusion text
        print(f"🤖 Generating lesson conclusion...")
        conclusion_topic = "Conclusion for Japanese Onomatopoeia and Mimetic Words lesson. Summarize key learnings about Japanese sound words, their importance in daily communication, how they enrich the language, and encourage continued practice and listening for these expressions in real-life situations."
        conclusion_keywords = "onomatopoeia, mimetic words, daily life, Japanese expressions, language enrichment, communication, cultural understanding, conclusion"
        
        conclusion_result = generator.generate_formatted_explanation(conclusion_topic, LESSON_DIFFICULTY, conclusion_keywords)
        
        if "error" not in conclusion_result:
            conclusion_content = LessonContent(
                lesson_id=lesson.id,
                content_type="text",
                title="Onomatopoeia and Mimetic Words - Lesson Conclusion",
                content_text=conclusion_result['generated_text'],
                order_index=content_order_index,
                page_number=final_page_number,
                generated_by_ai=True,
                ai_generation_details={
                    "model": "gpt-4.1",
                    "topic": conclusion_topic,
                    "difficulty": LESSON_DIFFICULTY,
                    "keywords": conclusion_keywords
                }
            )
            db.session.add(conclusion_content)
            print(f"✅ Conclusion added to final page.")
            content_order_index += 1

        # Generate comprehensive final quiz
        print(f"🤖 Generating comprehensive final quiz...")
        
        all_keywords = ", ".join([page["keywords"] for page in CONTENT_PAGES])
        final_quiz_topic = f"Comprehensive final assessment covering all onomatopoeia and mimetic words studied: morning routines, cooking/eating, weather/nature, emotions, movement, communication, household activities, and transportation. Test overall understanding of Japanese sound words and their usage in daily life."
        
        final_quiz_result = generator.generate_multiple_choice_question(
            final_quiz_topic, 
            LESSON_DIFFICULTY, 
            all_keywords,
            question_number=0
        )
        
        if "error" not in final_quiz_result:
            options = final_quiz_result.get('options', [])
            if isinstance(options, str):
                try:
                    options = json.loads(options)
                except json.JSONDecodeError:
                    print(f"❌ Error parsing final quiz options")
                else:
                    final_quiz_content = LessonContent(
                        lesson_id=lesson.id,
                        content_type="interactive",
                        title="Onomatopoeia and Mimetic Words - Comprehensive Final Quiz",
                        content_text="Test your overall knowledge of Japanese onomatopoeia and mimetic words in daily life",
                        is_interactive=True,
                        order_index=content_order_index,
                        page_number=final_page_number,
                        generated_by_ai=True
                    )
                    db.session.add(final_quiz_content)
                    db.session.flush()

                    final_question = QuizQuestion(
                        lesson_content_id=final_quiz_content.id,
                        question_type="multiple_choice",
                        question_text=final_quiz_result['question_text'],
                        explanation=final_quiz_result['overall_explanation']
                    )
                    db.session.add(final_question)
                    db.session.flush()

                    for option_data in options:
                        option = QuizOption(
                            question_id=final_question.id,
                            option_text=option_data['text'],
                            is_correct=option_data['is_correct'],
                            feedback=option_data.get('feedback', '')
                        )
                        db.session.add(option)
                    
                    print(f"✅ Comprehensive final quiz added.")

        db.session.commit()
        print(f"\n--- {LESSON_TITLE} Creation Complete! ---")
        print(f"✅ Onomatopoeia and Mimetic Words lesson created successfully!")
        print(f"   - Introduction page with overview image and welcoming text")
        print(f"   - {len(CONTENT_PAGES)} content pages covering different daily life scenarios")
        print(f"   - {len(CONTENT_PAGES)} dedicated quiz pages (one after each content page)")
        print(f"   - Each content page contains: scene image and comprehensive explanation")
        print(f"   - Each quiz page contains: 4 varied quiz questions")
        print(f"   - Final page with conclusion and comprehensive quiz")
        print(f"   - Topics covered: Morning routines, Cooking/eating, Weather/nature, Emotions, Movement, Communication, Household activities, Transportation")
        print(f"   - Quizzes are now separated from explanatory content as requested")

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
