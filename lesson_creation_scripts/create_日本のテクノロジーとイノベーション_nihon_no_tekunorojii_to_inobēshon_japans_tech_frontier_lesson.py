#!/usr/bin/env python3
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This script creates a comprehensive 日本のテクノロジーとイノベーション (Nihon no Tekunorojii to Inobēshon) - Japan's Tech Frontier lesson organized into pages.
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
LESSON_TITLE = "日本のテクノロジーとイノベーション (Nihon no Tekunorojii to Inobēshon) - Japan's Tech Frontier"
LESSON_DIFFICULTY = "Intermediate"
LESSON_DESCRIPTION = "Explore the cutting edge of Japan's technological landscape, from advanced robotics to unique digital trends. This lesson equips you with the essential vocabulary and cultural context to discuss innovations that shape modern Japanese society."

# Lesson content pages configuration (explanation pages only)
CONTENT_PAGES = [
    {
        "page_number": 2,
        "title": "1. Everyday Tech - 日常のテクノロジー (Nichijō no Tekunorojii)",
        "keywords": "スマートフォン (smartphone), パソコン (PC), アプリ (app), インターネット (internet), 充電する (jūden suru - to charge), ダウンロードする (daunrōdo suru - to download)",
        "image_concept": "A cheerful young woman with trendy glasses sits at a clean, minimalist wooden desk in a bright, modern room. She is smiling as she plugs a charger into her sleek smartphone. A stylish laptop is open on the desk next to a small, cute succulent plant. The style is cute manga/anime with clean lines and soft, natural lighting. No text or logos are visible on any devices.",
        "content_focus": "This page introduces fundamental vocabulary for personal technology. Students will learn to identify common devices and describe basic actions like charging a phone or downloading an app, forming a foundation for more complex topics."
    },
    {
        "page_number": 3,
        "title": "2. Automation & Robotics - ロボットの世界 (Robotto no Sekai)",
        "keywords": "ロボット (robot), 人工知能 (jinkō chinō - AI), 自動化 (jidōka - automation), 産業用ロボット (sangyōyō robotto - industrial robot), 介護ロボット (kaigo robotto - care robot)",
        "image_concept": "A friendly, white-and-blue service robot with a cute, simple digital face is carefully placing a book on a shelf for an elderly man in a cozy library. The man is smiling warmly at the robot. The robot is humanoid but has a smooth, non-threatening design. The style is a gentle, heartwarming manga/anime art style with warm lighting. All book spines are blank.",
        "content_focus": "Students will explore Japan's famous robotics industry. This section covers vocabulary to distinguish between different types of robots (industrial, service, care) and introduces the key term for Artificial Intelligence (AI), a driving force behind automation."
    },
    {
        "page_number": 4,
        "title": "3. Japan on the Move - 高速の日本 (Kōsoku no Nihon)",
        "keywords": "新幹線 (Shinkansen), リニアモーターカー (rinia mōtā kā - maglev train), 自動運転 (jidō unten - self-driving), ICカード (IC kādo - IC card), 改札口 (kaisatsuguchi - ticket gate)",
        "image_concept": "A sleek, futuristic Shinkansen train with a long nose glides past a platform. A young boy and his father stand on the platform, looking at the train with expressions of awe and excitement. The father has his hand on the boy's shoulder. The station is clean, modern, and empty except for them, emphasizing the train's speed. The art style is dynamic and clean manga/anime. The train has no logos or writing.",
        "content_focus": "This page focuses on the technology of transportation in Japan. Students will learn the names for the famous bullet train, the next-generation maglev, and understand the concepts of self-driving technology and the ubiquitous IC card system for seamless travel."
    },
    {
        "page_number": 5,
        "title": "4. The Cashless Society - キャッシュレス生活 (Kyasshuresu Seikatsu)",
        "keywords": "電子決済 (denshi kessai - electronic payment), QRコード決済 (QR kōdo kessai - QR code payment), スマホ決済 (sumaho kessai - smartphone payment), コンビニ (konbini), 自動販売機 (jidō hanbaiki - vending machine)",
        "image_concept": "A close-up view of a person's hand holding a smartphone in front of a generic payment terminal at a convenience store counter. A bright, abstract glow emanates from the phone's screen, indicating a successful transaction. The background is a soft-focus view of colorful but unidentifiable products on shelves. The art style is modern and clean manga/anime, focusing on the ease of the action.",
        "content_focus": "Learn about the rapid shift towards a cashless society in Japan. This section provides vocabulary for various electronic payment methods, enabling students to discuss paying with a smartphone or QR code in common situations like at a convenience store or vending machine."
    },
    {
        "page_number": 6,
        "title": "5. Digital Entertainment - デジタル文化 (Dejitaru Bunka)",
        "keywords": "バーチャルユーチューバー (VTuber), eスポーツ (e-supōtsu), ソーシャルメディア (sōsharu media), 動画配信 (dōga haishin - video streaming), アバター (abatā - avatar)",
        "image_concept": "A teenage girl sits in a cool gaming chair in a dimly lit room, illuminated by the glow of her large computer monitor. She wears headphones and has an excited expression. On the screen, a vibrant and stylish female anime avatar (a VTuber) is waving cheerfully. The avatar is generic, with colorful hair and a futuristic outfit. The art style is energetic and colorful manga/anime.",
        "content_focus": "Dive into Japan's unique digital and internet culture. Students will learn the terminology for modern entertainment phenomena like Virtual YouTubers (VTubers) and eSports, as well as general terms for social media and video streaming."
    },
    {
        "page_number": 7,
        "title": "6. Emerging Technology - 近未来のテクノロジー (Kinmirai no Tekunorojii)",
        "keywords": "仮想現実 (kasō genjitsu - VR), 拡張現実 (kakuchō genjitsu - AR), ドローン (dorōn - drone), スマートホーム (sumāto hōmu - smart home), 遠隔操作 (enkaku sōsa - remote control)",
        "image_concept": "A person wearing a sleek, white, minimalist VR headset stands in an empty, brightly lit room. They are reaching out with both hands, and translucent, glowing blue geometric shapes and light particles are swirling around their hands, suggesting interaction with a virtual world. The style is futuristic and clean sci-fi manga/anime.",
        "content_focus": "Look to the future with vocabulary for emerging technologies. This page introduces the concepts of Virtual and Augmented Reality, drones, smart homes, and remote operation, preparing students to discuss next-generation innovations."
    },
    {
        "page_number": 8,
        "title": "7. Society & Impact - 社会とテクノロジー (Shakai to Tekunorojii)",
        "keywords": "便利 (benri - convenient), 不便 (fuben - inconvenient), 影響 (eikyō - influence/impact), 問題点 (mondaiten - problems/issues), 進化する (shinka suru - to evolve), 未来 (mirai - future)",
        "image_concept": "A diverse group of four young adults are sitting around a low table in a bright, modern cafe, engaged in a lively but friendly debate. One person is gesturing expressively, another is listening thoughtfully, and a third is smiling. A generic, blank-screen tablet sits in the center of the table. The background shows a clean, slightly futuristic city street through the cafe window. The style is cute manga/anime, emphasizing communication and ideas.",
        "content_focus": "This final page equips students with the language to analyze and discuss the societal role of technology. They will learn vocabulary to express opinions, weigh pros and cons (convenience vs. issues), and speculate on the future evolution and impact of technology on Japanese society."
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
        overview_image_concept = "Vibrant overview scene representing 日本のテクノロジーとイノベーション (Nihon no Tekunorojii to Inobēshon) - Japan's Tech Frontier - showing the main themes and cultural elements of this lesson in a harmonious composition. Style: cute manga/anime art style with clean lines and cultural authenticity. IMPORTANT: No text, writing, signs, or characters should be visible in the image."
        
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
                    title="日本のテクノロジーとイノベーション (Nihon no Tekunorojii to Inobēshon) - Japan's Tech Frontier - Lesson Overview",
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
        intro_topic = f"Comprehensive introduction to {LESSON_TITLE}. Explain what students will learn in this lesson about technology and innovation in japan, the cultural significance and practical applications. Include learning objectives and how this knowledge will help students understand Japanese culture and daily life better."
        intro_keywords = "テクノロジー, イノベーション, ロボット, AI, 人工知能, デジタル文化, スマートフォン, アプリ, 新幹線, 自動化, 仮想現実, 電子決済, 未来"
        
        intro_result = generator.generate_formatted_explanation(intro_topic, LESSON_DIFFICULTY, intro_keywords)
        
        if "error" not in intro_result:
            intro_content = LessonContent(
                lesson_id=lesson.id,
                content_type="text",
                title="Welcome to 日本のテクノロジーとイノベーション (Nihon no Tekunorojii to Inobēshon) - Japan's Tech Frontier",
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
        conclusion_topic = "Conclusion for 日本のテクノロジーとイノベーション (Nihon no Tekunorojii to Inobēshon) - Japan's Tech Frontier lesson. Summarize key learnings from this lesson, their importance in understanding Japanese culture and daily life, and encourage continued practice and application of this knowledge."
        conclusion_keywords = "テクノロジー, イノベーション, ロボット, AI, 人工知能, デジタル文化, スマートフォン, アプリ, 新幹線, 自動化, 仮想現実, 電子決済, 未来, cultural understanding, conclusion"
        
        conclusion_result = generator.generate_formatted_explanation(conclusion_topic, LESSON_DIFFICULTY, conclusion_keywords)
        
        if "error" not in conclusion_result:
            conclusion_content = LessonContent(
                lesson_id=lesson.id,
                content_type="text",
                title="日本のテクノロジーとイノベーション (Nihon no Tekunorojii to Inobēshon) - Japan's Tech Frontier - Lesson Conclusion",
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
                        title="日本のテクノロジーとイノベーション (Nihon no Tekunorojii to Inobēshon) - Japan's Tech Frontier - Comprehensive Final Quiz",
                        content_text="Test your overall knowledge of 日本のテクノロジーとイノベーション (nihon no tekunorojii to inobēshon) - japan's tech frontier",
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
