#!/usr/bin/env python3
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This script creates a comprehensive Japanese lesson titled \"Karriere in Japan: Von der Bewerbung zum Berufsalltag\" for German-speaking learners.
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
    except Exception as e:
        print(f"Could not reconfigure stdout/stderr to UTF-8: {e}")


# Store the original print function before any modifications
import builtins
_original_print = builtins.print

# Force immediate output flushing for real-time console updates
def print_and_flush(*args, **kwargs):
    """Print with immediate flush for real-time output."""
    _original_print(*args, **kwargs)
    sys.stdout.flush()

# Override the built-in print function for real-time output
builtins.print = print_and_flush

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
from app.models import Lesson, LessonCategory, LessonContent, QuizQuestion, QuizOption
from app.ai_services import AILessonContentGenerator

# --- Configuration ---
LESSON_TITLE = "Karriere in Japan: Von der Bewerbung zum Berufsalltag"
LESSON_DIFFICULTY = "Mittelstufe"
LESSON_DESCRIPTION = "Tauche ein in die Welt der japanischen Arbeitskultur! Diese Lektion bereitet dich mit essentiellem Vokabular und kulturellem Wissen auf den japanischen Berufsalltag vor, von der Bewerbung bis zum ersten Tag im Büro. Lerne, wie du im Bewerbungsgespräch überzeugst und dich souverän in der japanischen Unternehmenshierarchie bewegst."

# Lesson content pages configuration (explanation pages only)
CONTENT_PAGES = [
    {
        "page_number": 2,
        "title": "Seite 1 - Die Jobsuche in Japan (Shūshoku Katsudō - 就職活動)",
        "keywords": "Jobsuche, 就活, Shūkatsu, Recruit Suit, リクルートスーツ, Einstellungsprüfung, 採用試験, Unternehmen, 企業",
        "image_concept": "Eine junge japanische Frau und ein junger japanischer Mann stehen nebeneinander. Beide tragen die typische schwarze 'Recruit Suit' (Bewerbungsanzug). Sie blicken hoffnungsvoll und entschlossen auf eine stilisierte Skyline von Tokio mit blühenden Kirschblüten im Vordergrund. Niedlicher Manga/Anime-Stil mit klaren Linien, kawaii-Ästhetik, hellen Farben und kultureller Authentizität. WICHTIG: Kein Text, keine Schrift, keine Schilder oder Zeichen sollten im Bild sichtbar sein.",
        "content_focus": "Diese Seite erklärt den einzigartigen und stark ritualisierten Prozess der Jobsuche für Hochschulabsolventen in Japan, bekannt als 'Shūkatsu'. Die Lernenden lernen das Vokabular für die verschiedenen Phasen der Jobsuche, von Unternehmens-Briefings bis hin zu den ersten Auswahltests."
    },
    {
        "page_number": 3,
        "title": "Seite 2 - Der japanische Lebenslauf (Rirekisho - 履歴書)",
        "keywords": "Lebenslauf, 履歴書, Rirekisho, Bewerbungsfoto, 証明写真, Ausbildung, 学歴, Berufserfahrung, 職歴, Selbst-PR, 自己PR",
        "image_concept": "Ein Charakter sitzt an einem sauberen Schreibtisch und füllt konzentriert ein Dokument aus, das die gitterartige Struktur eines 'Rirekisho' hat, aber keine sichtbaren Schriftzeichen enthält. Neben dem Schreibtisch steht eine Tasse grüner Tee. Die Szene ist ruhig und fokussiert. Niedlicher Manga/Anime-Stil mit klaren Linien, kawaii-Ästhetik, hellen Farben und kultureller Authentizität. WICHTIG: Kein Text, keine Schrift, keine Schilder oder Zeichen sollten im Bild sichtbar sein.",
        "content_focus": "Die Lernenden erfahren, wie man einen japanischen Lebenslauf ('Rirekisho') korrekt ausfüllt. Der Fokus liegt auf dem standardisierten Format, den erforderlichen Informationen (inklusive Passfoto) und wichtigen Vokabeln, um die eigene Ausbildung und Fähigkeiten zu beschreiben."
    },
    {
        "page_number": 4,
        "title": "Seite 3 - Das Bewerbungsgespräch (Mensetsu - 面接)",
        "keywords": "Bewerbungsgespräch, 面接, Mensetsu, Selbstvorstellung, 自己紹介, Stärken und Schwächen, 長所と短所, Interviewer, 面接官, Verbeugung, お辞儀",
        "image_concept": "Ein nervöser, aber gut vorbereiteter Bewerber sitzt aufrecht auf einem Stuhl gegenüber von zwei Interviewern, die von der Seite oder von hinten zu sehen sind. Der Raum ist ein minimalistisches, modernes Büro. Der Bewerber hat die Hände formell auf den Knien liegen. Niedlicher Manga/Anime-Stil mit klaren Linien, kawaii-Ästhetik, hellen Farben und kultureller Authentizität. WICHTIG: Kein Text, keine Schrift, keine Schilder oder Zeichen sollten im Bild sichtbar sein.",
        "content_focus": "Diese Seite bereitet auf das japanische Bewerbungsgespräch ('Mensetsu') vor. Es werden typische Fragen, wichtige Redewendungen für die Selbstvorstellung ('Jikoshōkai') und die richtige Körpersprache, wie das Sitzen und Verbeugen, behandelt."
    },
    {
        "page_number": 5,
        "title": "Seite 4 - Geschäftsetikette und erster Kontakt (Bijinesu Manā - ビジネス・マナー)",
        "keywords": "Geschäftsetikette, ビジネスマナー, Visitenkartentausch, 名刺交換, Meishi Kōkan, Vorstellung, 挨拶, Höflichkeit, 丁寧",
        "image_concept": "Zwei Personen in Business-Kleidung tauschen respektvoll kleine Kärtchen (als Visitenkarten erkennbar) aus. Beide halten die Karte des anderen mit beiden Händen und verbeugen sich leicht. Die Szene findet in einer hellen, modernen Büro-Lobby statt. Niedlicher Manga/Anime-Stil mit klaren Linien, kawaii-Ästhetik, hellen Farben und kultureller Authentizität. WICHTIG: Kein Text, keine Schrift, keine Schilder oder Zeichen sollten im Bild sichtbar sein.",
        "content_focus": "Hier lernen die Studierenden die Grundlagen der japanischen Geschäftsetikette. Der Schwerpunkt liegt auf dem korrekten Austausch von Visitenkarten ('Meishi Kōkan') – ein entscheidender erster Eindruck – sowie auf angemessenen Begrüßungsfloskeln im beruflichen Kontext."
    },
    {
        "page_number": 6,
        "title": "Seite 5 - Die Sprache des Respekts (Keigo - 敬語)",
        "keywords": "Höflichkeitssprache, 敬語, Keigo, Respektvolle Sprache, 尊敬語, Bescheidene Sprache, 謙譲語, Formelle Sprache, 丁寧語, Chef, 上司",
        "image_concept": "Eine jüngere Mitarbeiterin (Kōhai) spricht respektvoll mit einem älteren, erfahrenen Kollegen (Senpai) am Schreibtisch. Der Senpai lächelt freundlich und gibt ihr einen Rat, indem er auf einen leeren Computerbildschirm zeigt. Die Körperhaltung der Kōhai drückt Respekt aus. Niedlicher Manga/Anime-Stil mit klaren Linien, kawaii-Ästhetik, hellen Farben und kultureller Authentizität. WICHTIG: Kein Text, keine Schrift, keine Schilder oder Zeichen sollten im Bild sichtbar sein.",
        "content_focus": "Diese Seite bietet eine praxisorientierte Einführung in 'Keigo', die japanische Höflichkeitssprache. Die Lernenden verstehen den Unterschied zwischen den drei Hauptformen und lernen einfache, aber essenzielle Phrasen für die Kommunikation mit Vorgesetzten und Kunden."
    },
    {
        "page_number": 7,
        "title": "Seite 6 - Hierarchie und Teamgeist (Senpai-Kōhai to Chīmuwāku - 先輩・後輩とチームワーク)",
        "keywords": "Senior-Junior-Beziehung, 先輩・後輩, Teamarbeit, チームワーク, Harmonie, 和, Bericht, 報告, Kontakt, 連絡, Beratung, 相談, Hōrensō",
        "image_concept": "Eine Gruppe von vier Büroangestellten arbeitet fröhlich an einem gemeinsamen Projekt an einem großen Tisch. Ein Charakter, der als Senpai erkennbar ist, erklärt etwas, während die anderen aufmerksam zuhören. Die Atmosphäre ist kollaborativ und positiv. Niedlicher Manga/Anime-Stil mit klaren Linien, kawaii-Ästhetik, hellen Farben und kultureller Authentizität. WICHTIG: Kein Text, keine Schrift, keine Schilder oder Zeichen sollten im Bild sichtbar sein.",
        "content_focus": "Die Lernenden tauchen in die sozialen Strukturen des japanischen Arbeitsplatzes ein. Themen sind die wichtige Senpai-Kōhai-Beziehung, das Streben nach Gruppenharmonie ('Wa') und das Kommunikationsprinzip 'Hōrensō' (Berichten, Informieren, Beraten)."
    },
    {
        "page_number": 8,
        "title": "Seite 7 - Nach der Arbeit (Zangyō to Nominikēshon - 残業と飲みニケーション)",
        "keywords": "Überstunden, 残業, Zangyō, Feierabend, 仕事終わり, Trinken mit Kollegen, 飲み会, Kommunikation durch Trinken, 飲みニケーション, Prost, 乾杯",
        "image_concept": "Eine Gruppe von Kollegen in legerer Kleidung sitzt fröhlich in einer Izakaya (japanische Kneipe). Sie erheben ihre Gläser zu einem Toast ('Kanpai'). Im Hintergrund sind traditionelle japanische Laternen und Holzelemente zu sehen. Die Stimmung ist ausgelassen und kameradschaftlich. Niedlicher Manga/Anime-Stil mit klaren Linien, kawaii-Ästhetik, hellen Farben und kultureller Authentizität. WICHTIG: Kein Text, keine Schrift, keine Schilder oder Zeichen sollten im Bild sichtbar sein.",
        "content_focus": "Diese Seite beleuchtet zwei wesentliche Aspekte des japanischen Arbeitslebens nach Feierabend: die Kultur der Überstunden ('Zangyō') und die Bedeutung von 'Nominikēshon' – dem Aufbau von Beziehungen durch gemeinsames Trinken mit Kollegen und dem Chef."
    }
]

def download_image_simple(image_result, lesson_id, app, page_number):
    """Simple image download supporting OpenAI gpt-image-1 and legacy formats."""
    try:
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        filename = f"lesson_page_{page_number}_{timestamp}_{unique_id}.png"
        
        # Create target directory
        upload_folder = app.config.get('UPLOAD_FOLDER', 'app/static/uploads')
        target_dir = os.path.join(upload_folder, 'lessons', 'image', f'lesson_{lesson_id}')
        os.makedirs(target_dir, exist_ok=True)
        
        final_path = os.path.join(target_dir, filename)
        
        # Handle different image sources
        if isinstance(image_result, dict):
            if image_result.get('model') == 'openai-gpt-image-1' and 'image_bytes' in image_result:
                # OpenAI gpt-image-1 with base64 data
                print(f"  Saving OpenAI gpt-image-1 generated image...")
                image_bytes = image_result['image_bytes']
                # Save the raw bytes directly
                with open(final_path, 'wb') as f:
                    f.write(image_bytes)
                print(f"  ✅ OpenAI gpt-image-1 image saved to: {final_path}")
            elif 'image_url' in image_result and image_result['image_url'] not in ['openai_gpt_image_1_generated', 'vertexai_generated_image']:
                # OpenAI image URL (DALL-E)
                image_url = image_result['image_url']
                print(f"  Downloading OpenAI image from: {image_url}")
                urllib.request.urlretrieve(image_url, final_path)
                print(f"  ✅ OpenAI image saved to: {final_path}")
            elif image_result.get('image_url') in ['openai_gpt_image_1_generated', 'vertexai_generated_image']:
                # This is a placeholder URL but missing actual image data - this is an error case
                print(f"  ❌ Image result has placeholder URL but missing image data")
                return None, 0
            else:
                print(f"  ❌ Invalid image result format: {image_result}")
                return None, 0
        else:
            # Legacy: direct URL string
            print(f"  Downloading image from URL: {image_result}")
            urllib.request.urlretrieve(image_result, final_path)
            print(f"  ✅ Image saved to: {final_path}")
        
        # Return relative path for database storage
        relative_path = os.path.join('lessons', 'image', f'lesson_{lesson_id}', filename).replace('\\', '/')
        
        return relative_path, os.path.getsize(final_path)
        
    except Exception as e:
        print(f"  ❌ Error saving image: {e}")
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
                    from app.models import UserLessonProgress
                    deleted_progress = UserLessonProgress.query.filter_by(lesson_id=existing_lesson.id).delete(synchronize_session=False)
                    print(f"  Deleted {deleted_progress} user progress records")
            
            # Now delete the lesson (cascades will handle the rest)
            db.session.delete(existing_lesson)
            db.session.commit()
            print("✅ Existing lesson and all related data deleted.")

        
        # Find category
        category = LessonCategory.query.filter_by(name="Alltag & Gesellschaft").first()
        if not category:
            print(f"[WARNING] Category 'Alltag & Gesellschaft' not found. Defaulting to 'Sprachgrundlagen'.")
            category = LessonCategory.query.filter_by(name="Sprachgrundlagen").first()
            if not category:
                print("[ERROR] Default category 'Sprachgrundlagen' not found. Creating it.")
                category = LessonCategory(name="Sprachgrundlagen", description="Grundlagen der japanischen Sprache.")
                db.session.add(category)
                db.session.commit()
                print("[OK] Created default category 'Sprachgrundlagen'.")

        # Create the lesson
        lesson = Lesson(
            title=LESSON_TITLE,
            description=LESSON_DESCRIPTION,
            lesson_type="free",
            difficulty_level=2,
            is_published=True,
            category_id=category.id if category else None,
            instruction_language='german'
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
        overview_image_concept = f"Lebendige Collage, die verschiedene Aspekte des Lektionsthemas '{LESSON_TITLE}' zeigt - Menschen in alltäglichen japanischen Situationen, kulturelle Elemente, harmonische Komposition, die den Reichtum der japanischen Kultur und Sprache repräsentiert. Niedlicher Manga/Anime-Stil mit klaren Linien, kawaii-Ästhetik, hellen Farben und kultureller Authentizität. WICHTIG: Kein Text, keine Schrift, keine Schilder oder Zeichen sollten im Bild sichtbar sein."
        
        image_result = generator.generate_single_image(overview_image_concept, "1536x1024", "hd")
        
        if "error" not in image_result:
            image_url = image_result['image_url']
            print(f"🖼️ Overview image URL generated: {image_url}")
            
            # Download the image
            file_path, file_size = download_image_simple(image_result, lesson.id, app, 1)
            
            if file_path:
                # Create image content item
                image_content = LessonContent(
                    lesson_id=lesson.id,
                    content_type="image",
                    title=f"{LESSON_TITLE} - Lektionsübersicht",
                    content_text=f"Willkommen zur Lektion: {LESSON_TITLE}",
                    file_path=file_path,
                    file_size=file_size,
                    file_type="image",
                    original_filename="lesson_overview.png",
                    order_index=content_order_index,
                    page_number=1,
                    generated_by_ai=True
                )
                db.session.add(image_content)
                print(f"✅ Overview image added to introduction page.")
                content_order_index += 1

        # Generate welcoming introduction text
        print(f"🤖 Generating lesson introduction...")
        intro_topic = f"Umfassende Einführung in {LESSON_TITLE}. Erkläre, was die Studenten lernen werden, die Bedeutung des Themas in der japanischen Kultur und Sprache, wie es das Verständnis der japanischen Gesellschaft bereichert, und welche Aspekte in dieser Lektion behandelt werden. Füge Lernziele und kulturelle Bedeutung hinzu. Schreibe auf Deutsch für deutschsprachige Lernende."
        intro_keywords = f"Japanisch lernen, japanische Kultur, Sprache, Kommunikation, kulturelles Verständnis, {LESSON_TITLE}"
        
        intro_result = generator.generate_formatted_explanation(intro_topic, LESSON_DIFFICULTY, intro_keywords)
        
        if "error" not in intro_result:
            intro_content = LessonContent(
                lesson_id=lesson.id,
                content_type="text",
                title=f"Willkommen zu: {LESSON_TITLE}",
                content_text=intro_result['generated_text'],
                order_index=content_order_index,
                page_number=1,
                generated_by_ai=True,
                ai_generation_details={
                    "model": "gemini-2.5-pro",
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
            
            image_result = generator.generate_single_image(image_concept, "1536x1024", "hd")
            
            if "error" not in image_result:
                image_url = image_result['image_url']
                print(f"🖼️ Image URL generated for page {content_page_number}: {image_url}")
                
                # Download the image
                file_path, file_size = download_image_simple(image_result, lesson.id, app, content_page_number)
                
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
