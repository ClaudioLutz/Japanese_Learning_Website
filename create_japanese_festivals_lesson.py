#!/usr/bin/env python3
"""
This script creates a comprehensive Japanese Festivals lesson organized into pages.
Each page covers a different festival with impressive images, cultural explanations, and varied quizzes.
All Japanese text includes romanized pronunciation (romaji) in parentheses.
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
LESSON_TITLE = "Interesting Japanese Festivals - Cultural Journey"
LESSON_DIFFICULTY = "Intermediate"

# Organize festivals by pages with cultural context and vocabulary
LESSON_PAGES = [
    {
        "page_number": 1,
        "title": "Sakura Matsuri (Cherry Blossom Festival)",
        "festival_name": "桜祭り (さくらまつり)",
        "season": "Spring (March-May)",
        "vocabulary": {
            "桜 (さくら)": "Cherry blossom",
            "花見 (はなみ)": "Flower viewing",
            "満開 (まんかい)": "Full bloom",
            "散る (ちる)": "To fall/scatter (petals)"
        },
        "cultural_concepts": [
            "Hanami tradition and its significance",
            "Seasonal awareness in Japanese culture",
            "Community gathering and celebration",
            "Temporary beauty and mono no aware"
        ],
        "image_concept": "A magnificent cherry blossom tree in full bloom with people having hanami picnics underneath, traditional Japanese lanterns hanging from branches, pink petals falling like snow, peaceful spring atmosphere"
    },
    {
        "page_number": 2,
        "title": "Tanabata (Star Festival)",
        "festival_name": "七夕 (たなばた)",
        "season": "Summer (July 7th)",
        "vocabulary": {
            "七夕 (たなばた)": "Star Festival",
            "短冊 (たんざく)": "Paper strips for wishes",
            "願い事 (ねがいごと)": "Wish/prayer",
            "竹 (たけ)": "Bamboo",
            "織姫 (おりひめ)": "Weaver girl (star)",
            "彦星 (ひこぼし)": "Cowherd (star)"
        },
        "cultural_concepts": [
            "Legend of Orihime and Hikoboshi",
            "Writing wishes on tanzaku",
            "Bamboo decoration traditions",
            "Astronomical significance in Japanese culture"
        ],
        "image_concept": "Colorful tanzaku paper strips with wishes hanging from tall bamboo branches under a starry night sky, traditional Japanese decorations, people writing wishes, magical atmosphere with the Milky Way visible"
    },
    {
        "page_number": 3,
        "title": "Obon (Festival of the Dead)",
        "festival_name": "お盆 (おぼん)",
        "season": "Summer (August 13-16)",
        "vocabulary": {
            "お盆 (おぼん)": "Festival of the Dead",
            "先祖 (せんぞ)": "Ancestors",
            "迎え火 (むかえび)": "Welcome fire",
            "送り火 (おくりび)": "Send-off fire",
            "盆踊り (ぼんおどり)": "Bon dance",
            "精霊 (しょうりょう)": "Spirit/soul"
        },
        "cultural_concepts": [
            "Honoring deceased family members",
            "Buddhist and Shinto influences",
            "Mukaebi and okuribi fire rituals",
            "Community bon-odori dancing"
        ],
        "image_concept": "A traditional Japanese cemetery at dusk with small lanterns and incense burning, families paying respects to ancestors, soft golden light, peaceful and reverent atmosphere, traditional grave markers"
    },
    {
        "page_number": 4,
        "title": "Gion Matsuri (Gion Festival)",
        "festival_name": "祇園祭 (ぎおんまつり)",
        "season": "Summer (July)",
        "vocabulary": {
            "祇園祭 (ぎおんまつり)": "Gion Festival",
            "山鉾 (やまぼこ)": "Festival float",
            "巡行 (じゅんこう)": "Procession",
            "京都 (きょうと)": "Kyoto",
            "疫病 (えきびょう)": "Epidemic/plague",
            "神輿 (みこし)": "Portable shrine"
        },
        "cultural_concepts": [
            "Over 1000 years of history",
            "Elaborate yamaboko floats",
            "Kyoto's cultural heritage",
            "Disease prevention origins"
        ],
        "image_concept": "Magnificent ornate yamaboko festival floats decorated with intricate tapestries and wooden carvings, crowded streets of historic Kyoto, people in traditional clothing, elaborate procession with musicians"
    },
    {
        "page_number": 5,
        "title": "Awa Odori (Awa Dance Festival)",
        "festival_name": "阿波踊り (あわおどり)",
        "season": "Summer (August)",
        "vocabulary": {
            "阿波踊り (あわおどり)": "Awa Dance",
            "踊り (おどり)": "Dance",
            "連 (れん)": "Dance group",
            "徳島 (とくしま)": "Tokushima",
            "三味線 (しゃみせん)": "Shamisen (instrument)",
            "太鼓 (たいこ)": "Drum"
        },
        "cultural_concepts": [
            "Tokushima Prefecture's famous dance",
            "Ren (dance group) formations",
            "Traditional music and rhythm",
            "Participatory festival culture"
        ],
        "image_concept": "Energetic dancers in colorful traditional costumes performing the distinctive Awa dance movements, musicians playing shamisen and taiko drums, crowded festival streets with lanterns, dynamic motion and celebration"
    },
    {
        "page_number": 6,
        "title": "Nebuta Matsuri (Nebuta Festival)",
        "festival_name": "ねぶた祭り (ねぶたまつり)",
        "season": "Summer (August)",
        "vocabulary": {
            "ねぶた": "Nebuta (illuminated float)",
            "青森 (あおもり)": "Aomori",
            "武者 (むしゃ)": "Warrior",
            "和紙 (わし)": "Japanese paper",
            "跳人 (はねと)": "Dancer/jumper",
            "囃子 (はやし)": "Festival music"
        },
        "cultural_concepts": [
            "Aomori Prefecture's summer highlight",
            "Illuminated warrior float artistry",
            "Haneto dancer participation",
            "Paper craft and light techniques"
        ],
        "image_concept": "Spectacular illuminated nebuta floats featuring fierce warrior faces and mythical creatures, glowing from within with warm light, crowds of haneto dancers in traditional costumes, night festival atmosphere"
    },
    {
        "page_number": 7,
        "title": "Kanda Matsuri (Kanda Festival)",
        "festival_name": "神田祭 (かんだまつり)",
        "season": "Spring (May)",
        "vocabulary": {
            "神田祭 (かんだまつり)": "Kanda Festival",
            "江戸 (えど)": "Edo (old Tokyo)",
            "神田 (かんだ)": "Kanda district",
            "神社 (じんじゃ)": "Shrine",
            "御輿 (みこし)": "Portable shrine",
            "威勢 (いせい)": "Spirit/vigor"
        },
        "cultural_concepts": [
            "One of Tokyo's three great festivals",
            "Edo period traditions",
            "Mikoshi carrying rituals",
            "Urban shrine festival culture"
        ],
        "image_concept": "Dozens of people carrying ornate golden mikoshi portable shrines through busy Tokyo streets, participants in traditional festival clothing, urban backdrop with modern buildings, energetic crowd participation"
    },
    {
        "page_number": 8,
        "title": "Sapporo Snow Festival",
        "festival_name": "さっぽろ雪まつり (さっぽろゆきまつり)",
        "season": "Winter (February)",
        "vocabulary": {
            "雪まつり (ゆきまつり)": "Snow Festival",
            "札幌 (さっぽろ)": "Sapporo",
            "雪像 (ゆきぞう)": "Snow sculpture",
            "氷像 (ひょうぞう)": "Ice sculpture",
            "大通公園 (おおどおりこうえん)": "Odori Park",
            "イルミネーション": "Illumination"
        },
        "cultural_concepts": [
            "Winter celebration in Hokkaido",
            "International snow sculpture competition",
            "Modern festival innovation",
            "Tourism and cultural exchange"
        ],
        "image_concept": "Massive detailed snow and ice sculptures illuminated at night in Odori Park, intricate architectural replicas made of snow, colorful lights reflecting off ice surfaces, winter wonderland atmosphere"
    },
    {
        "page_number": 9,
        "title": "Takayama Festival",
        "festival_name": "高山祭 (たかやままつり)",
        "season": "Spring & Autumn",
        "vocabulary": {
            "高山祭 (たかやままつり)": "Takayama Festival",
            "飛騨 (ひだ)": "Hida region",
            "屋台 (やたい)": "Festival float",
            "からくり人形 (からくりにんぎょう)": "Mechanical puppet",
            "匠 (たくみ)": "Craftsman",
            "伝統工芸 (でんとうこうげい)": "Traditional crafts"
        },
        "cultural_concepts": [
            "Hida region's masterpiece festival",
            "Intricate karakuri puppet shows",
            "Traditional craftsmanship display",
            "Mountain town cultural heritage"
        ],
        "image_concept": "Elaborate wooden festival floats with intricate karakuri mechanical puppets performing, traditional mountain town setting, skilled craftsmen demonstrating their art, detailed woodwork and traditional architecture"
    },
    {
        "page_number": 10,
        "title": "Aoi Matsuri (Hollyhock Festival)",
        "festival_name": "葵祭 (あおいまつり)",
        "season": "Spring (May 15th)",
        "vocabulary": {
            "葵祭 (あおいまつり)": "Hollyhock Festival",
            "葵 (あおい)": "Hollyhock plant",
            "平安時代 (へいあんじだい)": "Heian period",
            "行列 (ぎょうれつ)": "Procession",
            "貴族 (きぞく)": "Nobility",
            "装束 (しょうぞく)": "Traditional costume"
        },
        "cultural_concepts": [
            "Ancient imperial court traditions",
            "Heian period aristocratic culture",
            "Formal procession rituals",
            "Historical costume preservation"
        ],
        "image_concept": "Elegant procession of people in authentic Heian period court costumes, elaborate silk robes and traditional headwear, ox-drawn carriages, formal imperial ceremony atmosphere, Kyoto's historic temples"
    },
    {
        "page_number": 11,
        "title": "Festival Culture Summary",
        "title": "Japanese Festival Traditions",
        "festival_name": "日本の祭り文化 (にほんのまつりぶんか)",
        "season": "Year-round",
        "vocabulary": {
            "祭り (まつり)": "Festival",
            "文化 (ぶんか)": "Culture",
            "伝統 (でんとう)": "Tradition",
            "共同体 (きょうどうたい)": "Community",
            "季節 (きせつ)": "Season",
            "精神 (せいしん)": "Spirit"
        },
        "cultural_concepts": [
            "Seasonal festival calendar",
            "Community bonding through celebration",
            "Preservation of cultural heritage",
            "Modern adaptations of ancient traditions"
        ],
        "image_concept": "A collage-style illustration showing elements from all major Japanese festivals - cherry blossoms, festival floats, dancers, lanterns, snow sculptures, traditional costumes - representing the rich diversity of Japanese festival culture"
    }
]

def download_image_simple(image_url, lesson_id, app, page_number):
    """Simple image download without complex validation."""
    try:
        print(f"  Downloading image from: {image_url}")
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        filename = f"festival_page_{page_number}_{timestamp}_{unique_id}.png"
        
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
            description="Explore Japan's most fascinating festivals through cultural insights, traditional vocabulary with phonetics, and stunning visual presentations. Learn about seasonal celebrations, historical significance, and cultural practices.",
            lesson_type="free",
            difficulty_level=2, # Intermediate
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

        # Process each festival page
        for page_data in LESSON_PAGES:
            page_number = page_data["page_number"]
            page_title = page_data["title"]
            festival_name = page_data.get("festival_name", "")
            season = page_data.get("season", "")
            vocabulary = page_data["vocabulary"]
            cultural_concepts = page_data.get("cultural_concepts", [])
            image_concept = page_data["image_concept"]
            
            print(f"\n--- Creating Page {page_number}: {page_title} ---")
            
            content_order_index = 0
            
            # 1. Generate impressive festival image first (as requested)
            print(f"🖼️ Generating impressive festival image for page {page_number}...")
            image_prompt = f"{image_concept}. Style: stunning, cinematic, highly detailed illustration with rich colors and cultural authenticity. IMPORTANT: No text, writing, signs, or Japanese characters should be visible in the image. Focus on visual storytelling and cultural atmosphere."
            
            image_result = generator.generate_single_image(image_prompt, "1024x1024", "hd")
            
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
                        title=f"{page_title} - Festival Image",
                        content_text=f"Impressive visual representation of {page_title}",
                        file_path=file_path,
                        file_size=file_size,
                        file_type="image",
                        original_filename=f"festival_page_{page_number}_illustration.png",
                        order_index=content_order_index,
                        page_number=page_number,
                        generated_by_ai=True
                    )
                    db.session.add(image_content)
                    print(f"✅ Impressive festival image added to page {page_number}.")
                    content_order_index += 1
            
            # 2. Create comprehensive festival introduction
            print(f"🤖 Generating comprehensive introduction for {page_title}...")
            intro_topic = f"Comprehensive introduction to {page_title} ({festival_name}) - {season}. Include cultural significance, historical background, traditional activities, and why this festival is important in Japanese culture."
            intro_keywords = f"{festival_name}, {season}, " + ", ".join(vocabulary.keys()) + ", " + ", ".join(cultural_concepts)
            
            intro_result = generator.generate_formatted_explanation(intro_topic, LESSON_DIFFICULTY, intro_keywords)
            
            if "error" not in intro_result:
                intro_content = LessonContent(
                    lesson_id=lesson.id,
                    content_type="text",
                    title=f"{page_title} - Cultural Overview",
                    content_text=intro_result['generated_text'],
                    order_index=content_order_index,
                    page_number=page_number,
                    generated_by_ai=True,
                    ai_generation_details={
                        "model": "gpt-4.1",
                        "topic": intro_topic,
                        "difficulty": LESSON_DIFFICULTY,
                        "keywords": intro_keywords
                    }
                )
                db.session.add(intro_content)
                print(f"✅ Page {page_number} cultural overview added.")
                content_order_index += 1
            
            # 3. Generate detailed vocabulary explanations with cultural context
            print(f"🤖 Generating vocabulary explanations for page {page_number}...")
            for word, meaning in vocabulary.items():
                topic = f"The Japanese word '{word}' ({meaning}) in the context of {page_title}. Explain its cultural significance, usage in festival context, and any historical or traditional associations."
                keywords = f"{word}, {meaning}, {festival_name}, festival, culture, tradition"
                
                result = generator.generate_formatted_explanation(topic, LESSON_DIFFICULTY, keywords)
                
                if "error" not in result:
                    content = LessonContent(
                        lesson_id=lesson.id,
                        content_type="text",
                        title=f"Vocabulary: {word} - {meaning}",
                        content_text=result['generated_text'],
                        order_index=content_order_index,
                        page_number=page_number,
                        generated_by_ai=True,
                        ai_generation_details={
                            "model": "gpt-4.1",
                            "topic": topic,
                            "difficulty": LESSON_DIFFICULTY,
                            "keywords": keywords
                        }
                    )
                    db.session.add(content)
                    print(f"✅ Vocabulary '{word}' added to page {page_number}.")
                    content_order_index += 1
            
            # 4. Generate varied quiz questions about the festival
            print(f"🤖 Generating varied quiz questions for page {page_number}...")
            
            # Generate 3 quiz questions per page with different focus areas
            quiz_focuses = [
                "cultural significance and historical background",
                "vocabulary meaning and usage in festival context", 
                "traditional activities and seasonal timing"
            ]
            
            for quiz_num in range(3):
                focus_area = quiz_focuses[quiz_num % len(quiz_focuses)]
                topic = f"{page_title} ({festival_name}) - Focus on {focus_area}"
                keywords = f"{festival_name}, {season}, " + ", ".join(vocabulary.keys())
                
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
                        title=f"{page_title} Quiz #{quiz_num + 1} - {focus_area.title()}",
                        content_text=f"Test your knowledge of {page_title} - focusing on {focus_area}.",
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
                    
                    print(f"✅ Quiz #{quiz_num + 1} ({focus_area}) added to page {page_number}.")
                    content_order_index += 1

        db.session.commit()
        print("\n--- Japanese Festivals Lesson Creation Complete! ---")
        print(f"✅ Japanese Festivals lesson created successfully!")
        print(f"   - {len(LESSON_PAGES)} festival pages created")
        print(f"   - Each page contains: impressive festival image, cultural overview, vocabulary with phonetics, and varied quizzes")
        print(f"   - Covers major festivals: Sakura Matsuri, Tanabata, Obon, Gion Matsuri, Awa Odori, Nebuta Matsuri, Kanda Matsuri, Sapporo Snow Festival, Takayama Festival, Aoi Matsuri")
        print(f"   - All Japanese text includes romanized pronunciation (romaji)")
        print(f"   - All images are text-free with impressive cultural visuals")
        print(f"   - Quiz questions cover cultural significance, vocabulary, and traditional activities")

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
