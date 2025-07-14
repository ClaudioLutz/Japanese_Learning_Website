#!/usr/bin/env python3
"""
This script creates a comprehensive Japanese Cities lesson organized into pages.
Each page covers a different major Japanese city with impressive images, cultural explanations, and varied quizzes.
Based on the configuration provided for Intermediate-level Japanese Cities learning.
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
LESSON_TITLE = "Japanese Cities - Urban Culture and Geography"
LESSON_DIFFICULTY = "Intermediate"
LESSON_DESCRIPTION = "Explore Japan's major cities through their unique characteristics, cultural significance, historical background, and modern developments. Learn essential vocabulary and cultural insights about urban life in Japan."

# Lesson pages configuration
LESSON_PAGES = [
    {
        "page_number": 1,
        "title": "Tokyo (東京) - The Capital Metropolis",
        "keywords": "Tokyo, capital, metropolis, Shibuya, Shinjuku, Imperial Palace, modern, traditional, population, business district",
        "image_concept": "Stunning aerial view of Tokyo skyline showing the contrast between modern skyscrapers and traditional temples, with Mount Fuji visible in the distance, bustling streets with neon signs, cherry blossoms in foreground. Style: cute manga/anime art style clean lines, and cultural authenticity. IMPORTANT: No text, writing, signs, or characters should be visible in the image."
    },
    {
        "page_number": 2,
        "title": "Osaka (大阪) - The Kitchen of Japan",
        "keywords": "Osaka, kitchen of Japan, takoyaki, okonomiyaki, Dotonbori, Kansai, merchant culture, food culture, comedy, Osaka Castle",
        "image_concept": "Vibrant street scene in Dotonbori district with colorful food stalls, people enjoying street food, traditional lanterns, canal reflections, lively atmosphere showcasing Osaka's famous food culture. Style: cute manga/anime art style clean lines, and cultural authenticity. IMPORTANT: No text, writing, signs, or characters should be visible in the image."
    },
    {
        "page_number": 3,
        "title": "Kyoto (京都) - The Ancient Capital",
        "keywords": "Kyoto, ancient capital, temples, shrines, geisha, traditional architecture, bamboo forest, Fushimi Inari, cultural heritage, UNESCO",
        "image_concept": "Serene view of traditional Kyoto with golden Kinkaku-ji temple reflected in a pond, surrounded by perfectly manicured gardens, traditional architecture, peaceful atmosphere with autumn colors. Style: cute manga/anime art style clean lines, and cultural authenticity. IMPORTANT: No text, writing, signs, or characters should be visible in the image."
    },
    {
        "page_number": 4,
        "title": "Hiroshima (広島) - City of Peace",
        "keywords": "Hiroshima, peace, memorial, atomic bomb, reconstruction, Miyajima, torii gate, resilience, peace park, modern development",
        "image_concept": "Peaceful scene of Hiroshima Peace Memorial Park with the iconic dome structure, cherry blossoms, people walking peacefully, modern city skyline in background, symbol of hope and renewal. Style: cute manga/anime art style clean lines, and cultural authenticity. IMPORTANT: No text, writing, signs, or characters should be visible in the image."
    },
    {
        "page_number": 5,
        "title": "Yokohama (横浜) - International Port City",
        "keywords": "Yokohama, port city, international, Chinatown, Red Brick Warehouse, Minato Mirai, foreign influence, trade, cosmopolitan, harbor",
        "image_concept": "Beautiful harbor view of Yokohama with the iconic Cosmo World ferris wheel, modern waterfront buildings, ships in the harbor, international atmosphere with mix of cultures. Style: cute manga/anime art style clean lines, and cultural authenticity. IMPORTANT: No text, writing, signs, or characters should be visible in the image."
    },
    {
        "page_number": 6,
        "title": "Nagoya (名古屋) - Industrial Heart",
        "keywords": "Nagoya, industrial, manufacturing, Toyota, automotive, castle, miso katsu, central Japan, technology, innovation, transportation hub",
        "image_concept": "Modern industrial cityscape of Nagoya showing the blend of traditional Nagoya Castle with contemporary skyscrapers, busy transportation networks, technological advancement atmosphere. Style: cute manga/anime art style clean lines, and cultural authenticity. IMPORTANT: No text, writing, signs, or characters should be visible in the image."
    },
    {
        "page_number": 7,
        "title": "Sapporo (札幌) - Northern Gateway",
        "keywords": "Sapporo, Hokkaido, snow festival, beer, northern Japan, winter sports, Susukino, clock tower, fresh seafood, cold climate",
        "image_concept": "Winter scene of Sapporo with snow-covered streets, the famous clock tower, people enjoying winter activities, snow sculptures, cozy atmosphere with warm lights from buildings. Style: cute manga/anime art style clean lines, and cultural authenticity. IMPORTANT: No text, writing, signs, or characters should be visible in the image."
    },
    {
        "page_number": 8,
        "title": "Fukuoka (福岡) - Gateway to Asia",
        "keywords": "Fukuoka, Kyushu, gateway to Asia, ramen, yatai food stalls, Hakata, international trade, young population, startup culture, mild climate",
        "image_concept": "Lively evening scene of Fukuoka's famous yatai food stalls along the river, people enjoying ramen and socializing, warm lighting, modern city backdrop, friendly community atmosphere. Style: cute manga/anime art style clean lines, and cultural authenticity. IMPORTANT: No text, writing, signs, or characters should be visible in the image."
    },
    {
        "page_number": 9,
        "title": "Sendai (仙台) - City of Trees",
        "keywords": "Sendai, city of trees, Tohoku, Date Masamune, green city, university town, tanabata festival, reconstruction, natural beauty, education",
        "image_concept": "Beautiful tree-lined streets of Sendai with lush greenery, students walking through the city, mix of modern and traditional architecture, peaceful urban forest atmosphere. Style: cute manga/anime art style clean lines, and cultural authenticity. IMPORTANT: No text, writing, signs, or characters should be visible in the image."
    },
    {
        "page_number": 10,
        "title": "Kobe (神戸) - Cosmopolitan Port",
        "keywords": "Kobe, port city, beef, international, foreign quarter, earthquake recovery, fashion, mountains and sea, multicultural, elegant atmosphere",
        "image_concept": "Elegant view of Kobe with the city nestled between mountains and sea, foreign-influenced architecture, sophisticated urban planning, harbor with ships, cosmopolitan atmosphere. Style: cute manga/anime art style clean lines, and cultural authenticity. IMPORTANT: No text, writing, signs, or characters should be visible in the image."
    },
    {
        "page_number": 11,
        "title": "Nara (奈良) - Ancient Capital and Deer Park",
        "keywords": "Nara, ancient capital, deer park, Todaiji Temple, Great Buddha, historical significance, sacred deer, traditional culture, UNESCO World Heritage",
        "image_concept": "Peaceful scene in Nara Park with sacred deer roaming freely among visitors, the massive Todaiji Temple in the background, people feeding deer, serene natural and cultural harmony. Style: cute manga/anime art style clean lines, and cultural authenticity. IMPORTANT: No text, writing, signs, or characters should be visible in the image."
    },
    {
        "page_number": 12,
        "title": "Japanese Urban Culture - City Life Summary",
        "keywords": "urban culture, city life, transportation, work culture, modern lifestyle, traditional values, population density, technology integration, community, diversity",
        "image_concept": "Collage-style illustration showing various aspects of Japanese city life - busy train stations, office workers, traditional festivals in urban settings, modern technology, community gatherings, representing the diversity of Japanese urban culture. Style: cute manga/anime art style clean lines, and cultural authenticity. IMPORTANT: No text, writing, signs, or characters should be visible in the image."
    }
]

def download_image_simple(image_url, lesson_id, app, page_number):
    """Simple image download without complex validation."""
    try:
        print(f"  Downloading image from: {image_url}")
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        filename = f"cities_page_{page_number}_{timestamp}_{unique_id}.png"
        
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
        overview_image_concept = "Panoramic view showcasing Japan's diverse cities - Tokyo's skyscrapers, Kyoto's temples, Osaka's food culture, Hiroshima's peace memorial, snowy Sapporo, and other major cities in a beautiful composition showing Japan's urban diversity. Style: cute manga/anime art style clean lines, and cultural authenticity. IMPORTANT: No text, writing, signs, or characters should be visible in the image."
        
        image_result = generator.generate_single_image(overview_image_concept, "1024x1024", "hd")
        
        if "error" not in image_result:
            image_url = image_result['image_url']
            print(f"🖼️ Overview image URL generated: {image_url}")
            
            # Download the image
            file_path, file_size = download_image_simple(image_url, lesson.id, app, 0)
            
            if file_path:
                # Create image content item
                image_content = LessonContent(
                    lesson_id=lesson.id,
                    content_type="image",
                    title="Japanese Cities - Lesson Overview",
                    content_text="Welcome to your journey through Japan's major cities",
                    file_path=file_path,
                    file_size=file_size,
                    file_type="image",
                    original_filename="japanese_cities_overview.png",
                    order_index=content_order_index,
                    page_number=1,
                    generated_by_ai=True
                )
                db.session.add(image_content)
                print(f"✅ Overview image added to introduction page.")
                content_order_index += 1

        # Generate welcoming introduction text
        print(f"🤖 Generating lesson introduction...")
        intro_topic = f"Comprehensive introduction to {LESSON_TITLE}. Explain what students will learn about Japanese cities, their cultural significance, geographical diversity, and urban development. Include learning objectives and what makes Japanese cities unique."
        intro_keywords = "Japanese cities, urban culture, geography, cultural significance, modern development, traditional values, city life, transportation, diversity"
        
        intro_result = generator.generate_formatted_explanation(intro_topic, LESSON_DIFFICULTY, intro_keywords)
        
        if "error" not in intro_result:
            intro_content = LessonContent(
                lesson_id=lesson.id,
                content_type="text",
                title="Welcome to Japanese Cities",
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

        # Process each sub-topic page (Pages 2 through N)
        for page_data in LESSON_PAGES:
            page_number = page_data["page_number"] + 1  # Offset by 1 since page 1 is introduction
            page_title = page_data["title"]
            keywords = page_data["keywords"]
            image_concept = page_data["image_concept"]
            
            print(f"\n--- Creating Page {page_number}: {page_title} ---")
            
            content_order_index = 0
            
            # 1. Generate impressive city image
            print(f"🖼️ Generating city image for page {page_number}...")
            
            image_result = generator.generate_single_image(image_concept, "1024x1024", "hd")
            
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
                        title=f"{page_title} - City Image",
                        content_text=f"Visual representation of {page_title}",
                        file_path=file_path,
                        file_size=file_size,
                        file_type="image",
                        original_filename=f"cities_page_{page_number}_illustration.png",
                        order_index=content_order_index,
                        page_number=page_number,
                        generated_by_ai=True
                    )
                    db.session.add(image_content)
                    print(f"✅ City image added to page {page_number}.")
                    content_order_index += 1
            
            # 2. Generate comprehensive city overview
            print(f"🤖 Generating comprehensive overview for {page_title}...")
            overview_topic = f"Comprehensive cultural and geographical overview of {page_title}. Include history, cultural significance, major attractions, local specialties, demographics, economic importance, and what makes this city unique in Japan. Use the keywords: {keywords}"
            
            overview_result = generator.generate_formatted_explanation(overview_topic, LESSON_DIFFICULTY, keywords)
            
            if "error" not in overview_result:
                overview_content = LessonContent(
                    lesson_id=lesson.id,
                    content_type="text",
                    title=f"{page_title} - City Overview",
                    content_text=overview_result['generated_text'],
                    order_index=content_order_index,
                    page_number=page_number,
                    generated_by_ai=True,
                    ai_generation_details={
                        "model": "gpt-4.1",
                        "topic": overview_topic,
                        "difficulty": LESSON_DIFFICULTY,
                        "keywords": keywords
                    }
                )
                db.session.add(overview_content)
                print(f"✅ Page {page_number} city overview added.")
                content_order_index += 1
            
            # 3. Generate varied quiz questions (5 per page)
            print(f"🤖 Generating quiz questions for page {page_number}...")
            
            # Quiz types cycle through different formats - 5 quizzes per page
            quiz_types = [
                ("multiple_choice", "Multiple Choice"),
                ("true_false", "True/False"),
                ("matching", "Matching"),
                ("multiple_choice", "Multiple Choice"),
                ("true_false", "True/False")
            ]
            
            for quiz_num in range(5):  # 5 quizzes per page
                quiz_type, quiz_name = quiz_types[quiz_num]
                
                print(f"  Generating {quiz_name} quiz #{quiz_num + 1}...")
                
                if quiz_type == "multiple_choice":
                    quiz_result = generator.generate_multiple_choice_question(
                        f"{page_title} cultural and geographical knowledge", 
                        LESSON_DIFFICULTY, 
                        keywords,
                        question_number=quiz_num
                    )
                elif quiz_type == "true_false":
                    quiz_result = generator.generate_true_false_question(
                        f"{page_title} facts and cultural information", 
                        LESSON_DIFFICULTY, 
                        keywords
                    )
                else:  # matching
                    quiz_result = generator.generate_matching_question(
                        f"{page_title} vocabulary and cultural concepts", 
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
                        order_index=content_order_index,
                        page_number=page_number,
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
                                print(f"❌ Error parsing multiple choice options for page {page_number}")
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
                                print(f"❌ Error parsing matching pairs for page {page_number}")
                                continue
                        
                        # For matching questions, we create options from the pairs
                        # Each pair becomes two options - one prompt and one answer
                        for i, pair in enumerate(pairs):
                            if isinstance(pair, dict) and 'prompt' in pair and 'answer' in pair:
                                # Create prompt option (not correct by itself)
                                prompt_option = QuizOption(
                                    question_id=question.id,
                                    option_text=f"PROMPT_{i}: {pair['prompt']}",
                                    is_correct=False,
                                    feedback=f"This matches with: {pair['answer']}"
                                )
                                db.session.add(prompt_option)
                                
                                # Create answer option (correct match)
                                answer_option = QuizOption(
                                    question_id=question.id,
                                    option_text=f"ANSWER_{i}: {pair['answer']}",
                                    is_correct=True,
                                    feedback=f"This matches with: {pair['prompt']}"
                                )
                                db.session.add(answer_option)
                    
                    print(f"✅ {quiz_name} quiz #{quiz_num + 1} added to page {page_number}.")
                    content_order_index += 1
                else:
                    print(f"❌ Error generating {quiz_name} quiz #{quiz_num + 1}: {quiz_result.get('error', 'Unknown error')}")

        # Create Final Page: Comprehensive Final Quiz
        final_page_number = len(LESSON_PAGES) + 2
        print(f"\n--- Creating Final Page {final_page_number}: Comprehensive Quiz ---")
        
        content_order_index = 0
        
        # Generate conclusion text
        print(f"🤖 Generating lesson conclusion...")
        conclusion_topic = "Conclusion for Japanese Cities lesson. Summarize key learnings about Japan's major cities, their diversity, cultural significance, and modern development. Encourage continued exploration of Japanese urban culture."
        conclusion_keywords = "Japanese cities, urban diversity, cultural heritage, modern Japan, city characteristics, regional differences, conclusion"
        
        conclusion_result = generator.generate_formatted_explanation(conclusion_topic, LESSON_DIFFICULTY, conclusion_keywords)
        
        if "error" not in conclusion_result:
            conclusion_content = LessonContent(
                lesson_id=lesson.id,
                content_type="text",
                title="Japanese Cities - Lesson Conclusion",
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

        # Generate comprehensive adaptive final quiz
        print(f"🤖 Generating comprehensive final quiz...")
        
        all_keywords = ", ".join([page["keywords"] for page in LESSON_PAGES])
        final_quiz_topic = f"Comprehensive final assessment covering all Japanese cities studied: Tokyo, Osaka, Kyoto, Hiroshima, Yokohama, Nagoya, Sapporo, Fukuoka, Sendai, Kobe, and Nara. Test overall understanding of Japanese urban culture, geography, and city characteristics."
        
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
                        title="Japanese Cities - Comprehensive Final Quiz",
                        content_text="Test your overall knowledge of Japanese cities and urban culture",
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
        print(f"✅ Japanese Cities lesson created successfully!")
        print(f"   - Introduction page with overview image and welcoming text")
        print(f"   - {len(LESSON_PAGES)} city pages covering major Japanese cities")
        print(f"   - Each city page contains: impressive image, comprehensive overview, and varied quizzes")
        print(f"   - Final page with conclusion and comprehensive adaptive quiz")
        print(f"   - Cities covered: Tokyo, Osaka, Kyoto, Hiroshima, Yokohama, Nagoya, Sapporo, Fukuoka, Sendai, Kobe, Nara")
        print(f"   - All content generated with cultural authenticity and educational value")

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
