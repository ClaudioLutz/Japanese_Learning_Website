#!/usr/bin/env python3
"""
This script creates a comprehensive Visiting Sacred Spaces: A Guide to Japanese Temples and Shrines lesson organized into pages.
Each content page covers different aspects of the topic with explanations, followed by dedicated quiz pages.
The quizzes are separated from the explanatory content as requested.
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
LESSON_TITLE = "Visiting Sacred Spaces: A Guide to Japanese Temples and Shrines"
LESSON_DIFFICULTY = "Intermediate"
LESSON_DESCRIPTION = "This lesson explores the fascinating world of Japanese temples and shrines, covering essential vocabulary, etiquette, and cultural insights to help you navigate these spiritual places with respect and understanding. Learn how to differentiate between these distinct sacred sites and experience Japanese culture firsthand."

# Lesson content pages configuration (explanation pages only)
CONTENT_PAGES = [
    {
        "page_number": 2,
        "title": "Understanding the Difference - 神社と寺院 (Jinja to Jiin)",
        "keywords": "shrine, temple, Shinto, Buddhism, torii, architecture",
        "image_concept": "A split image showcasing a vibrant red torii gate against a clear blue sky on one side and a serene five-storied pagoda nestled among lush green trees on the other, in a cute manga/anime style with clean lines.",
        "content_focus": "Differentiating between Shinto shrines and Buddhist temples based on architecture, deities, and purposes."
    },
    {
        "page_number": 3,
        "title": "Purifying Before Entry - 参拝前の清め (Sanpai Mae no Kiyome)",
        "keywords": "purification, temizuya, chozuya, ladle, water basin, etiquette",
        "image_concept": "A cute manga/anime style illustration of a temizuya (water basin) with a dipper resting on its edge, surrounded by lush greenery and a peaceful atmosphere. Clean lines, no text.",
        "content_focus": "Learning the proper steps for purification at the temizuya (water basin) before entering a shrine or temple."
    },
    {
        "page_number": 4,
        "title": "Making Offerings and Prayers - お賽銭とお願い (Osaisen to Onegai)",
        "keywords": "offering, prayer, bowing, clapping, etiquette, saisenbako",
        "image_concept": "A person silhouetted against a bright orange glow of a setting sun, performing a deep bow in front of a generic sacred building (no identifiable features). Cute manga/anime style, clean lines.",
        "content_focus": "Understanding the etiquette of making offerings and prayers at shrines and temples, including bowing and clapping."
    },
    {
        "page_number": 5,
        "title": "Ema and Omikuji - 絵馬とおみくじ (Ema to Omikuji)",
        "keywords": "ema, omikuji, fortune, wishes, writing, tying",
        "image_concept": "A collection of colorful ema hanging on a wooden rack, with a few rolled-up omikuji placed gently beside them, depicted in a cute manga/anime style with clean lines.",
        "content_focus": "Learning about ema (wooden prayer plaques) and omikuji (fortune slips), including how to write wishes and interpret fortunes."
    },
    {
        "page_number": 6,
        "title": "Goshuin - 御朱印 (Goshuin)",
        "keywords": "goshuin, calligraphy, stamp, notebook, collecting",
        "image_concept": "Close-up of a hand holding a brush, delicately applying ink to a blank page of a goshuincho (stamp book) open on a wooden table. Cute manga/anime style, clean lines, no actual writing shown on the page.",
        "content_focus": "Introduction to goshuin (red seal stamps) and the practice of collecting them in a dedicated notebook."
    },
    {
        "page_number": 7,
        "title": "Exploring Temple Grounds - 寺院の境内 (Jiin no Keidai)",
        "keywords": "pagoda, main hall, garden, architecture, incense",
        "image_concept": "A serene Japanese garden with a pagoda in the background, surrounded by lush greenery and a pond with koi fish. Cute manga/anime art style, clean lines, no text or signage.",
        "content_focus": "Exploring the various structures and features found within temple grounds, such as pagodas, main halls, and gardens."
    },
    {
        "page_number": 8,
        "title": "Respectful Behavior - 敬意を表す行動 (Keii o Arawasu Koudou)",
        "keywords": "etiquette, photography, clothing, silence, respect",
        "image_concept": "A person dressed respectfully, standing quietly and observing a beautiful natural scene within a temple or shrine ground. Cute manga/anime style, clean lines. No specific religious iconography visible.",
        "content_focus": "Reviewing essential etiquette guidelines for visiting sacred spaces, including photography rules, appropriate attire, and maintaining a respectful atmosphere."
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
        
        print(f"  ✅ Background image saved to: {relative_path}")
        return relative_path, os.path.getsize(final_path)
        
    except Exception as e:
        print(f"  ❌ Error downloading background image: {e}")
        return None, 0

def create_lesson(app):
    """Creates the lesson and its content within the Flask app context."""
    with app.app_context():
        print(f"--- Creating Lesson: {LESSON_TITLE} ---")

        # Check if lesson already exists and delete it
        existing_lesson = Lesson.query.filter_by(title=LESSON_TITLE).first()
        if existing_lesson:
            print(f"Found existing lesson '{LESSON_TITLE}' (ID: {existing_lesson.id}). Deleting it.")
            
            # First, delete all user quiz answers for this lesson to avoid foreign key constraints
            from app.models import UserQuizAnswer
            
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
                    # UserLessonProgress imported at top level
                    deleted_progress = UserLessonProgress.query.filter_by(lesson_id=existing_lesson.id).delete(synchronize_session=False)
                    print(f"  Deleted {deleted_progress} user progress records")
            
            # Now delete the lesson (cascades will handle the rest)
            db.session.delete(existing_lesson)
            db.session.commit()
            print("✅ Existing lesson and all related data deleted.")

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

        # Generate lesson tile background image
        print(f"\n--- Generating Lesson Tile Background ---")
        print(f"🎨 Generating background image for lesson tile...")
        
        background_result = generator.generate_lesson_tile_background(
            LESSON_TITLE,
            LESSON_DESCRIPTION,
            lesson.difficulty_level
        )
        
        if "error" not in background_result:
            background_image_url = background_result['image_url']
            print(f"🖼️ Background image URL generated: {background_image_url}")
            
            # Download the background image
            background_file_path, background_file_size = download_background_image(background_image_url, lesson.id, app)
            
            if background_file_path:
                # Update lesson with background image info
                lesson.background_image_url = background_image_url
                lesson.background_image_path = background_file_path
                
                db.session.commit()
                
                print(f"✅ Background image added to lesson '{LESSON_TITLE}'")
            else:
                print(f"❌ Failed to download background image for lesson '{LESSON_TITLE}'")
        else:
            print(f"❌ Error generating background image: {background_result['error']}")

        # Create Page 1: Lesson Introduction
        print(f"\n--- Creating Introduction Page ---")
        
        content_order_index = 0
        
        # Generate overview image
        print(f"🖼️ Generating lesson overview image...")
        overview_image_concept = "Vibrant overview scene representing Visiting Sacred Spaces: A Guide to Japanese Temples and Shrines - showing the main themes and cultural elements of this lesson in a harmonious composition. Style: cute manga/anime art style with clean lines and cultural authenticity. IMPORTANT: No text, writing, signs, or characters should be visible in the image."
        
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
                    title="Visiting Sacred Spaces: A Guide to Japanese Temples and Shrines - Lesson Overview",
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
        intro_topic = f"Comprehensive introduction to {LESSON_TITLE}. Explain what students will learn in this lesson about visiting japanese temples and shrines, the cultural significance and practical applications. Include learning objectives and how this knowledge will help students understand Japanese culture and daily life better."
        intro_keywords = "temple, shrine, etiquette, worship, Shinto, Buddhism, torii, ema, omikuji, goshuin, purification, offering, prayer, architecture, cultural sensitivity"
        
        intro_result = generator.generate_formatted_explanation(intro_topic, LESSON_DIFFICULTY, intro_keywords)
        
        if "error" not in intro_result:
            intro_content = LessonContent(
                lesson_id=lesson.id,
                content_type="text",
                title="Welcome to Visiting Sacred Spaces: A Guide to Japanese Temples and Shrines",
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
            
            # Generate all quiz questions for this page in one batch session
            print(f"🤖 Generating batch quiz questions for {page_title}...")
            
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
                print(f"✅ Generated {len(questions)} quiz questions in batch for {page_title}")
                
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
                print(f"❌ Error generating batch quiz questions for {page_title}: {batch_quiz_result.get('error', 'Unknown error')}")
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
        conclusion_topic = "Conclusion for Visiting Sacred Spaces: A Guide to Japanese Temples and Shrines lesson. Summarize key learnings from this lesson, their importance in understanding Japanese culture and daily life, and encourage continued practice and application of this knowledge."
        conclusion_keywords = "temple, shrine, etiquette, worship, Shinto, Buddhism, torii, ema, omikuji, goshuin, purification, offering, prayer, architecture, cultural sensitivity, cultural understanding, conclusion"
        
        conclusion_result = generator.generate_formatted_explanation(conclusion_topic, LESSON_DIFFICULTY, conclusion_keywords)
        
        if "error" not in conclusion_result:
            conclusion_content = LessonContent(
                lesson_id=lesson.id,
                content_type="text",
                title="Visiting Sacred Spaces: A Guide to Japanese Temples and Shrines - Lesson Conclusion",
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
                        title="Visiting Sacred Spaces: A Guide to Japanese Temples and Shrines - Comprehensive Final Quiz",
                        content_text="Test your overall knowledge of visiting sacred spaces: a guide to japanese temples and shrines",
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
