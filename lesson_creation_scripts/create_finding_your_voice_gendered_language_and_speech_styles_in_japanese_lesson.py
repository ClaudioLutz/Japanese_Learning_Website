#!/usr/bin/env python3
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This script creates a comprehensive Finding Your Voice: Gendered Language and Speech Styles in Japanese lesson organized into pages.
Each content page covers different aspects of the topic with explanations, followed by dedicated quiz pages.
The quizzes are separated from the explanatory content as requested.

FIXES APPLIED:
- Correct Python path setup for subdirectory execution
- Consolidated imports to avoid UnboundLocalError
- Proper difficulty level integer conversion
- Database field length constraints handled
- Correct .env file path resolution
- UTF-8 encoding declaration for Unicode support
"""
import os
import sys
import json
import urllib.request
from datetime import datetime
import uuid
import codecs

# Reconfigure stdout to use UTF-8 encoding, especially for Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
        print("Successfully reconfigured stdout and stderr to UTF-8.")
    except Exception as e:
        print(f"Could not reconfigure stdout/stderr to UTF-8: {e}")


# Add the project root directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Load environment variables manually
def load_env():
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    value = value.strip('"\'')
                    os.environ[key] = value

load_env()

from app import create_app, db
from app.models import Lesson, LessonContent, QuizQuestion, QuizOption, UserQuizAnswer, UserLessonProgress
from app.ai_services import AILessonContentGenerator

# --- Configuration ---
LESSON_TITLE = "Finding Your Voice: Gendered Language and Speech Styles in Japanese"
LESSON_DIFFICULTY = "Intermediate"
LESSON_DESCRIPTION = "This lesson explores the fascinating world of traditional masculine (男性語) and feminine (女性語) speech in Japanese. You will learn key vocabulary and grammar differences, understand their use in media, and discover how these styles are evolving in modern Japan. The goal is to build awareness so you can understand native speakers and develop your own comfortable communication style."

# Lesson content pages configuration (explanation pages only)
CONTENT_PAGES = [
    {
        "page_number": 2,
        "title": "1. Introduction to Gendered Speech - はじめに (Hajime ni)",
        "keywords": "男性語 (danseigo), 女性語 (joseigo), 役割語 (yakuwarigo), speech patterns, context",
        "image_concept": "A split-screen style image. On the left, a male anime character with a confident, assertive expression. On the right, a female anime character with a gentle, thoughtful expression. They are looking towards the viewer. The background is a soft, neutral gradient, blending the two sides in the middle. The style is cute manga/anime art with clean lines and cultural authenticity. IMPORTANT: No text, writing, signs, or characters should be visible in the image.",
        "content_focus": "This page introduces the core concepts of 'masculine language' (男性語) and 'feminine language' (女性語). It clarifies that these are traditional patterns, often exaggerated in media as 役割語 (role language), and that real-world usage is much more fluid and context-dependent."
    },
    {
        "page_number": 3,
        "title": "2. Choosing 'I': First-Person Pronouns - 一人称代名詞 (Ichininshou Daimeishi)",
        "keywords": "私 (watashi), 僕 (boku), 俺 (ore), あたし (atashi), 自分 (jibun), pronoun",
        "image_concept": "An anime-style character stands before a large, ornate mirror. In the reflection, several different versions of the character are visible, each with a unique expression: one is professional and serious, one is boyish and friendly, one is tough and confident, and one is playful and cute. This represents the choice of pronoun reflecting one's identity. The style is cute manga/anime art with clean lines and cultural authenticity. IMPORTANT: No text, writing, signs, or characters should be visible in the image.",
        "content_focus": "Learn the most common first-person pronouns and their nuances. This page details the differences between the formal/neutral 私 (watashi), the soft-masculine 僕 (boku), the rough-masculine 俺 (ore), and the informal-feminine あたし (atashi), explaining how they convey personality and politeness."
    },
    {
        "page_number": 4,
        "title": "3. The Final Word: Sentence-Ending Particles - 終助詞 (Shuujoshi)",
        "keywords": "終助詞 (shuujoshi), ～わ (wa), ～の (no), ～かしら (kashira), ～ぜ (ze), ～ぞ (zo), ～よ (yo), ～ね (ne)",
        "image_concept": "Two anime-style friends, one male and one female, are having an animated conversation on a park bench under a large ginkgo tree with yellow leaves. The male character is leaning forward emphatically, as if making a strong point. The female character is listening with a hand to her chin, looking curious and thoughtful. Their speech bubbles are empty. The style is cute manga/anime art with clean lines and cultural authenticity. IMPORTANT: No text, writing, signs, or characters should be visible in the image.",
        "content_focus": "Discover how sentence-ending particles (終助詞) add emotion and nuance. This page contrasts traditionally masculine endings that add assertion (～ぜ, ～ぞ) with traditionally feminine ones that add softness or inquiry (～わ, ～かしら), while also covering more neutral particles like ～よ and ～ね."
    },
    {
        "page_number": 5,
        "title": "4. Vocabulary and Intonation - 言葉遣いとイントネーション (Kotobazukai to Intonēshon)",
        "keywords": "言葉遣い (kotobazukai), 美化語 (bikago), うまい (umai), おいしい (oishii), はら (hara), おなか (onaka)",
        "image_concept": "A vibrant scene at a Japanese food festival stall. A male anime character is taking a large, satisfying bite of takoyaki, with an expression of pure delight. Beside him, a female anime character is gracefully holding a cup of tea, smiling gently. The focus is on their different ways of expressing enjoyment. The style is cute manga/anime art with clean lines and cultural authenticity. IMPORTANT: No text, writing, signs, or characters should be visible in the image.",
        "content_focus": "Explore differences in vocabulary and typical intonation. This page covers word choices like うまい vs. おいしい (delicious) and the use of 美化語 (bikago), or 'beautifying prefixes' like 'o-' and 'go-' (お酒, ご飯), which are often, but not exclusively, associated with feminine speech."
    },
    {
        "page_number": 6,
        "title": "5. Language in Anime & Manga - 役割語 (Yakuwarigo)",
        "keywords": "役割語 (yakuwarigo), anime, manga, stereotypes, character archetypes, わし (washi)",
        "image_concept": "A dynamic group portrait of distinct anime character archetypes. In the group is a wise old martial arts master with a long white beard, a spiky-haired action hero, a gentle princess in an elegant dress, and a tough-looking female warrior with a scar. They are posed together like a team, showcasing a variety of character types. The style is cute manga/anime art with clean lines and cultural authenticity. IMPORTANT: No text, writing, signs, or characters should be visible in the image.",
        "content_focus": "Understand 'role language' (役割語), a key concept for media literacy. Learn how anime and manga use exaggerated speech patterns as a shortcut to define characters: the old master who uses わし (washi), the delinquent who uses 俺 (ore), the refined princess who uses ～わ (wa). This page emphasizes that this is a form of characterization, not a reflection of everyday conversation."
    },
    {
        "page_number": 7,
        "title": "6. Blurring the Lines: Modern Usage - 現代の言葉遣い (Gendai no Kotobazukai)",
        "keywords": "gender neutral, individual choice, fluidity, situational language, work, casual",
        "image_concept": "A scene at a modern, bright co-working space or university cafe in Japan. A diverse group of young adults (male, female, androgynous-presenting) are collaborating on a project with laptops and notebooks. They are dressed in contemporary, stylish clothing and are actively engaged in conversation, laughing and sharing ideas. The atmosphere is dynamic and inclusive. The style is cute manga/anime art with clean lines and cultural authenticity. IMPORTANT: No text, writing, signs, or characters should be visible in the image.",
        "content_focus": "This page explores how gendered language is used in modern Japan. It highlights the trend of women using 'boku,' the prevalence of neutral language (especially in professional settings), and the overall shift towards speech that reflects individual personality and situation over rigid gender norms."
    },
    {
        "page_number": 8,
        "title": "7. Finding Your Own Style - 自分の話し方 (Jibun no Hanashikata)",
        "keywords": "self-expression, awareness, observation, 丁寧語 (teineigo), personal style, natural speech",
        "image_concept": "A friendly, androgynous anime character stands at a crossroads where a path splits into three. One path leads towards a bustling modern cityscape, another towards a serene traditional temple garden, and the third towards a beautiful natural mountain landscape. The character is looking directly at the viewer with a welcoming smile, inviting them to choose their own path. The style is cute manga/anime art with clean lines and cultural authenticity. IMPORTANT: No text, writing, signs, or characters should be visible in the image.",
        "content_focus": "As a learner, what should you do? This summary advises focusing first on mastering standard polite language (丁寧語). It encourages observing how Japanese people speak in real life and consciously choosing a style that feels natural and comfortable for you, rather than trying to imitate stereotypes."
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
        
        print(f"  [OK] Image saved to: {relative_path}")
        return relative_path, os.path.getsize(final_path)
        
    except Exception as e:
        print(f"  [ERROR] Error downloading image: {e}")
        return None, 0

def download_background_image(image_url, lesson_id, app):
    """Download and save background image for a lesson."""
    try:
        print(f"  Downloading background image from: {image_url}")
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        filename = f"lesson_{lesson_id}_background_{timestamp}_{unique_id}.png"
        
        # Create target directory
        upload_folder = app.config.get('UPLOAD_FOLDER', 'app/static/uploads')
        target_dir = os.path.join(upload_folder, 'lessons', 'backgrounds')
        os.makedirs(target_dir, exist_ok=True)
        
        # Save file using urllib
        final_path = os.path.join(target_dir, filename)
        urllib.request.urlretrieve(image_url, final_path)
        
        # Return relative path for database storage
        relative_path = os.path.join('lessons', 'backgrounds', filename).replace('\\', '/')
        
        print(f"  [OK] Background image saved to: {relative_path}")
        return relative_path, os.path.getsize(final_path)
        
    except Exception as e:
        print(f"  [ERROR] Error downloading background image: {e}")
        return None, 0

def create_lesson(app):
    """Creates the lesson and its content within the Flask app context."""
    with app.app_context():
        print("--- Creating Lesson: [Starting] ---")

        # Check if lesson already exists and delete it
        existing_lesson = Lesson.query.filter_by(title=LESSON_TITLE).first()
        if existing_lesson:
            print(f"Found existing lesson [EXISTING] (ID: {existing_lesson.id}). Deleting it.")
            
            # First, delete all user quiz answers for this lesson to avoid foreign key constraints
            
            # Get all content IDs for this lesson
            content_ids = [content.id for content in existing_lesson.content_items if content.is_interactive]
            
            if content_ids:
                # Get all question IDs for this lesson's content
                question_ids = [q.id for q in QuizQuestion.query.filter(QuizQuestion.lesson_content_id.in_(content_ids)).all()]
                
                if question_ids:
                    # Delete all user quiz answers for these questions
                    deleted_answers = UserQuizAnswer.query.filter(UserQuizAnswer.question_id.in_(question_ids)).delete(synchronize_session=False)
                    print(f"  Deleted {deleted_answers} user quiz answers")
                    
                    # Delete all user lesson progress for this lesson
                    deleted_progress = UserLessonProgress.query.filter_by(lesson_id=existing_lesson.id).delete(synchronize_session=False)
                    print(f"  Deleted {deleted_progress} user progress records")
            
            # Now delete the lesson (cascades will handle the rest)
            db.session.delete(existing_lesson)
            db.session.commit()
            print("[OK] Existing lesson and all related data deleted.")

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
        print(f"[OK] Lesson created with ID: {lesson.id}")

        # Initialize AI generator
        print("\n--- Initializing AI Generator ---")
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            print("[ERROR] OPENAI_API_KEY not found in environment variables.")
            return
        
        generator = AILessonContentGenerator()
        if not generator.client:
            print("[ERROR] AI Generator could not be initialized. Check your API key.")
            return
        
        print("[OK] AI Generator Initialized")

        # Generate lesson tile background image
        print(f"\n--- Generating Lesson Tile Background ---")
        print(f"[ART] Generating background image for lesson tile...")
        
        background_result = generator.generate_lesson_tile_background(
            LESSON_TITLE,
            LESSON_DESCRIPTION,
            lesson.difficulty_level
        )
        
        if "error" not in background_result:
            background_image_url = background_result['image_url']
            print(f"[IMG] Background image URL generated: {background_image_url}")
            
            # Download the background image
            background_file_path, background_file_size = download_background_image(background_image_url, lesson.id, app)
            
            if background_file_path:
                # Update lesson with background image info
                lesson.background_image_url = background_image_url
                lesson.background_image_path = background_file_path
                
                db.session.commit()
                
                print(f"[OK] Background image added to lesson '{LESSON_TITLE}'")
            else:
                print(f"[ERROR] Failed to download background image for lesson '{LESSON_TITLE}'")
        else:
            print(f"[ERROR] Error generating background image: {background_result['error']}")

        # Create Page 1: Lesson Introduction
        print(f"\n--- Creating Introduction Page ---")
        
        content_order_index = 0
        
        # Generate overview image
        print(f"[IMG] Generating lesson overview image...")
        overview_image_concept = "Vibrant overview scene representing Finding Your Voice: Gendered Language and Speech Styles in Japanese - showing the main themes and cultural elements of this lesson in a harmonious composition. Style: cute manga/anime art style with clean lines and cultural authenticity. IMPORTANT: No text, writing, signs, or characters should be visible in the image."
        
        image_result = generator.generate_single_image(overview_image_concept, "1024x1024", "hd")
        
        if "error" not in image_result:
            image_url = image_result['image_url']
            print(f"[IMG] Overview image URL generated: {image_url}")
            
            # Download the image
            file_path, file_size = download_image_simple(image_url, lesson.id, app, 1)
            
            if file_path:
                # Create image content item
                image_content = LessonContent(
                    lesson_id=lesson.id,
                    content_type="image",
                    title="Finding Your Voice: Gendered Language and Speech Styles in Japanese - Lesson Overview",
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
                print(f"[OK] Overview image added to introduction page.")
                content_order_index += 1

        # Generate welcoming introduction text
        print(f"[AI] Generating lesson introduction...")
        intro_topic = f"Comprehensive introduction to {LESSON_TITLE}. Explain what students will learn in this lesson about gendered language and speech styles, the cultural significance and practical applications. Include learning objectives and how this knowledge will help students understand Japanese culture and daily life better."
        intro_keywords = "gendered language, speech style, 男性語 (danseigo), 女性語 (joseigo), 役割語 (yakuwarigo), 一人称 (ichininshou), pronouns, 終助詞 (shuujoshi), sentence enders, context, politeness, modern Japanese, cultural nuance, self-expression"
        
        intro_result = generator.generate_formatted_explanation(intro_topic, LESSON_DIFFICULTY, intro_keywords)
        
        if "error" not in intro_result:
            intro_content = LessonContent(
                lesson_id=lesson.id,
                content_type="text",
                title="Welcome to Finding Your Voice: Gendered Language and Speech Styles in Japanese",
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
            print(f"[OK] Introduction text added to page 1.")
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
            print(f"[IMG] Generating scene image for page {content_page_number}...")
            
            image_result = generator.generate_single_image(image_concept, "1024x1024", "hd")
            
            if "error" not in image_result:
                image_url = image_result['image_url']
                print(f"[IMG] Image URL generated for page {content_page_number}: {image_url}")
                
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
                    print(f"[OK] Scene image added to page {content_page_number}.")
                    content_order_index += 1
            
            # 2. Generate comprehensive explanation (no quizzes on this page)
            print(f"[AI] Generating comprehensive explanation for {page_title}...")
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
                print(f"[OK] Page {content_page_number} explanation added.")
                content_order_index += 1

            # Create corresponding quiz page immediately after content page
            quiz_page_number = current_page_number + 1
            print(f"\n--- Creating Quiz Page {quiz_page_number} for {page_title} ---")
            
            quiz_content_order_index = 0
            
            # Generate all quiz questions for this page in one batch session
            print(f"[AI] Generating batch quiz questions for {page_title}...")
            
            # Define quiz specifications for this page (5 quizzes total)
            quiz_specifications = [
                {"type": "multiple_choice", "count": 3},
                {"type": "true_false", "count": 1},
                {"type": "matching", "count": 1}
            ]
            
            # Generate all quizzes in one AI session to ensure variety and avoid duplication
            batch_quiz_result = generator.generate_page_quiz_batch(
                f"{page_title} onomatopoeia and mimetic words. Focus on: {content_focus}",
                LESSON_DIFFICULTY,
                keywords,
                quiz_specifications
            )
            
            if "error" not in batch_quiz_result and "questions" in batch_quiz_result:
                questions = batch_quiz_result["questions"]
                print(f"[OK] Generated {len(questions)} quiz questions in batch for {page_title}")
                
                # Process each question from the batch
                for quiz_num, quiz_data in enumerate(questions):
                    quiz_type = quiz_data.get("question_type", "multiple_choice")
                    quiz_name = quiz_type.replace("_", " ").title()
                    
                    print(f"  Processing {quiz_name} quiz #{quiz_num + 1}...")
                    
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
                        question_text=quiz_data['question_text'],
                        explanation=quiz_data.get('overall_explanation', quiz_data.get('explanation', ''))
                    )
                    db.session.add(question)
                    db.session.flush()

                    # Handle different quiz types with their specific data structures
                    if quiz_type == "multiple_choice":
                        # Multiple choice has 'options' array
                        options = quiz_data.get('options', [])
                        if isinstance(options, str):
                            try:
                                options = json.loads(options)
                            except json.JSONDecodeError:
                                print(f"[ERROR] Error parsing multiple choice options for quiz page {quiz_page_number}")
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
                        correct_answer = quiz_data.get('correct_answer', True)
                        
                        # Create True option
                        true_option = QuizOption(
                            question_id=question.id,
                            option_text="True",
                            is_correct=(correct_answer == True),
                            feedback=quiz_data.get('explanation', '')
                        )
                        db.session.add(true_option)
                        
                        # Create False option
                        false_option = QuizOption(
                            question_id=question.id,
                            option_text="False",
                            is_correct=(correct_answer == False),
                            feedback=quiz_data.get('explanation', '')
                        )
                        db.session.add(false_option)
                    
                    elif quiz_type == "matching":
                        # Matching has 'pairs' array
                        pairs = quiz_data.get('pairs', [])
                        if isinstance(pairs, str):
                            try:
                                pairs = json.loads(pairs)
                            except json.JSONDecodeError:
                                print(f"[ERROR] Error parsing matching pairs for quiz page {quiz_page_number}")
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
                    
                    print(f"[OK] {quiz_name} quiz #{quiz_num + 1} added to quiz page {quiz_page_number}.")
                    quiz_content_order_index += 1
            else:
                print(f"[ERROR] Error generating batch quiz questions for {page_title}: {batch_quiz_result.get('error', 'Unknown error')}")
                # Fallback to individual generation if batch fails
                print("🔄 Falling back to individual quiz generation...")
                
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
                                    print(f"[ERROR] Error parsing multiple choice options for quiz page {quiz_page_number}")
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
                                    print(f"[ERROR] Error parsing matching pairs for quiz page {quiz_page_number}")
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
                        
                        print(f"[OK] {quiz_name} quiz #{quiz_num + 1} added to quiz page {quiz_page_number}.")
                        quiz_content_order_index += 1
                    else:
                        print(f"[ERROR] Error generating {quiz_name} quiz #{quiz_num + 1}: {quiz_result.get('error', 'Unknown error')}")

            # Move to next pair of pages (content + quiz)
            current_page_number += 2

        # Create Final Page: Comprehensive Final Quiz and Conclusion
        final_page_number = current_page_number
        print(f"\n--- Creating Final Page {final_page_number}: Comprehensive Quiz and Conclusion ---")
        
        content_order_index = 0
        
        # Generate conclusion text
        print(f"[AI] Generating lesson conclusion...")
        conclusion_topic = "Conclusion for Finding Your Voice: Gendered Language and Speech Styles in Japanese lesson. Summarize key learnings from this lesson, their importance in understanding Japanese culture and daily life, and encourage continued practice and application of this knowledge."
        conclusion_keywords = "gendered language, speech style, 男性語 (danseigo), 女性語 (joseigo), 役割語 (yakuwarigo), 一人称 (ichininshou), pronouns, 終助詞 (shuujoshi), sentence enders, context, politeness, modern Japanese, cultural nuance, self-expression, cultural understanding, conclusion"
        
        conclusion_result = generator.generate_formatted_explanation(conclusion_topic, LESSON_DIFFICULTY, conclusion_keywords)
        
        if "error" not in conclusion_result:
            conclusion_content = LessonContent(
                lesson_id=lesson.id,
                content_type="text",
                title="Finding Your Voice: Gendered Language and Speech Styles in Japanese - Lesson Conclusion",
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
            print(f"[OK] Conclusion added to final page.")
            content_order_index += 1

        # Generate comprehensive final quiz
        print(f"[AI] Generating comprehensive final quiz...")
        
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
                    print(f"[ERROR] Error parsing final quiz options")
                else:
                    final_quiz_content = LessonContent(
                        lesson_id=lesson.id,
                        content_type="interactive",
                        title="Finding Your Voice: Gendered Language and Speech Styles in Japanese - Comprehensive Final Quiz",
                        content_text="Test your overall knowledge of finding your voice: gendered language and speech styles in japanese",
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
                    
                    print(f"[OK] Comprehensive final quiz added.")

        db.session.commit()
        print(f"\n--- {LESSON_TITLE} Creation Complete! ---")
        print(f"[OK] Onomatopoeia and Mimetic Words lesson created successfully!")
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
        print("[ERROR] Error: OPENAI_API_KEY environment variable not set.")
        print("Please add your OpenAI API key to your .env file.")
        sys.exit(1)

    # Create Flask app
    app = create_app()
    
    # Run the lesson creation
    create_lesson(app)
