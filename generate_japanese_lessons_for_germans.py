#!/usr/bin/env python3
"""
Google Gemini 2.5 Pro Powered Japanese Lesson Script Generator (for German Speakers)

This script reads the japanese_lessons_for_germans.md file and uses Google Gemini 2.5 Pro
to dynamically generate lesson creation scripts for each topic. The generated scripts
will contain Japanese lesson content with explanations in German.
"""

import os
import sys
import re
import json
import time
from datetime import datetime
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("❌ Google Generative AI library not installed. Install with: pip install google-generativeai")

# Configuration
GEMINI_MODEL = "gemini-2.5-pro"
LESSON_TEMPLATE_FILE = "create_onomatopoeia_lesson.py" # Using existing template
TOPICS_FILE = "japanese_lessons_for_germans.md"
OUTPUT_DIR = "lesson_creation_scripts_german"
LOG_FILE = f"japanese_for_germans_generation_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

def setup_logging():
    """Setup logging to both console and file."""
    class Logger:
        def __init__(self, filename):
            self.terminal = sys.stdout
            self.log = open(filename, "w", encoding='utf-8')

        def write(self, message):
            self.terminal.write(message)
            self.log.write(message)
            self.log.flush()

        def flush(self):
            self.terminal.flush()
            self.log.flush()

    sys.stdout = Logger(LOG_FILE)

def load_env():
    """Load environment variables from .env file."""
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    value = value.strip('"\'')
                    os.environ[key] = value

def initialize_gemini():
    """Initialize Google Gemini API."""
    if not GEMINI_AVAILABLE:
        print("❌ Google Generative AI library not available.")
        print("Install with: pip install google-generativeai")
        return None
        
    api_key = os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        print("❌ Error: GOOGLE_API_KEY not found in environment variables.")
        print("Please add your Google Gemini API key to your .env file.")
        return None
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(GEMINI_MODEL)
        print(f"✅ Google Gemini {GEMINI_MODEL} initialized successfully")
        return model
    except Exception as e:
        print(f"❌ Error initializing Gemini: {e}")
        return None

def read_topics_file():
    """Read and parse the japanese_lessons_for_germans.md file."""
    try:
        with open(TOPICS_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        topics = []
        pattern = r'(\d+)\.\s*\*\*(.*?)\*\*\s*\n\s*\*\s*(.*?)(?=\n\n|\n\d+\.|\Z)'
        matches = re.findall(pattern, content, re.DOTALL)
        
        for match in matches:
            topic_id = int(match[0])
            title = match[1].strip()
            description = match[2].strip()
            
            topics.append({
                'id': topic_id,
                'title': title,
                'description': description
            })
        
        print(f"✅ Found {len(topics)} Japanese lessons for Germans to generate.")
        return topics
    
    except Exception as e:
        print(f"❌ Error reading topics file: {e}")
        return []

def read_template_file():
    """Read the template lesson creation script."""
    try:
        with open(LESSON_TEMPLATE_FILE, 'r', encoding='utf-8') as f:
            template_content = f.read()
        print(f"✅ Template file loaded: {LESSON_TEMPLATE_FILE}")
        return template_content
    except Exception as e:
        print(f"❌ Error reading template file: {e}")
        return None

def convert_difficulty_to_int(difficulty_str):
    """Convert difficulty string to integer."""
    difficulty_map = {
        'beginner': 1, 'a1': 1,
        'intermediate': 2, 'a2': 2, 'b1': 2,
        'advanced': 3, 'b2': 3, 'c1': 3,
        'expert': 4, 'c2': 4
    }
    return difficulty_map.get(difficulty_str.lower().strip(), 2)

def generate_lesson_structure(model, topic):
    """Use Gemini to generate lesson structure for a Japanese topic, with German explanations."""
    
    available_categories = [
        "Kultur & Traditionen",
        "Essen & Trinken",
        "Alltag & Gesellschaft",
        "Popkultur & Modernes Japan",
        "Sprache & Kommunikation",
        "Reisen & Geografie",
        "Sprachgrundlagen"
    ]
    
    prompt = f"""
You are an expert Japanese language educator creating content for German-speaking learners. Analyze the following Japanese lesson topic and create a comprehensive lesson structure. The entire output, including titles, descriptions, and keywords, must be in GERMAN.

TOPIC (in German): {topic['title']}
DESCRIPTION (in German): {topic['description']}

Generate a detailed lesson structure in JSON format with the following specifications. ALL TEXT MUST BE IN GERMAN.

1. LESSON METADATA (in German):
   - Determine appropriate difficulty level (Anfänger, Mittelstufe, or Fortgeschritten)
   - Choose the most relevant category from this list: {', '.join(available_categories)}
   - Create comprehensive keywords (10-15 relevant German and Japanese terms)
   - Define cultural focus areas (in German)
   - Write an engaging lesson description for students (2-3 sentences, in German)

2. CONTENT PAGES (Generate exactly 7 content pages, in German):
   - Each page should have a specific theme/focus area
   - Include a German title, followed by the Japanese title with romanization in parentheses. Example: "Seite 1 - Begrüßungen (Aisatsu)"
   - Provide detailed keywords for each page (in German and Japanese)
   - Write content focus description (what students will learn, in German)
   - Create detailed image concept for AI image generation (description in German, style should be "niedlicher Manga/Anime-Stil mit klaren Linien und kultureller Authentizität. WICHTIG: Kein Text, keine Schrift, keine Schilder oder Zeichen sollten im Bild sichtbar sein.")

3. EDUCATIONAL STRUCTURE:
   - Ensure logical progression from basic to advanced concepts
   - Include cultural context and real-world applications
   - Balance vocabulary, grammar, and cultural understanding, all explained in German.

Return ONLY a valid JSON object with this exact structure (all values in German):
{{
  "lesson_title": "Complete lesson title in German",
  "lesson_description": "Detailed description for students in German",
  "difficulty": "Anfänger/Mittelstufe/Fortgeschritten",
  "category_name": "Chosen Category Name in German",
  "keywords": "comma-separated keywords in German/Japanese",
  "cultural_focus": "main cultural aspects covered in German",
  "content_pages": [
    {{
      "title": "Page Title in German - Japanischer Titel (Romanisierung)",
      "keywords": "page-specific keywords in German/Japanese",
      "content_focus": "what this page teaches, in German",
      "image_concept": "detailed image description for AI generation, in German"
    }}
  ]
}}

Make sure the lesson is educationally sound, culturally authentic, and engaging for German speakers learning Japanese.
"""

    try:
        print(f"🤖 Generating lesson structure for: {topic['title']}")
        response = model.generate_content(prompt)
        
        response_text = response.text.strip()
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start != -1 and json_end != -1:
            json_text = response_text[json_start:json_end]
            lesson_structure = json.loads(json_text)
            print(f"✅ Generated structure with {len(lesson_structure.get('content_pages', []))} content pages")
            return lesson_structure
        else:
            print(f"❌ Could not extract JSON from Gemini response")
            return None
            
    except Exception as e:
        print(f"❌ Error generating lesson structure: {e}")
        return None

def create_script_filename(title):
    """Create a valid filename from lesson title."""
    filename = re.sub(r'[^\w\s-]', '', title.lower())
    filename = re.sub(r'[-\s]+', '_', filename)
    return f"create_{filename}_lesson.py"

def truncate_text(text, max_length):
    """Truncate text to fit database constraints."""
    if not text or len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def generate_lesson_script(template_content, topic, lesson_structure):
    """Generate the lesson creation script using the template."""
    try:
        difficulty_int = convert_difficulty_to_int(lesson_structure['difficulty'])
        
        content_pages_start = template_content.find('CONTENT_PAGES = [')
        content_pages_end = template_content.find(']', content_pages_start) + 1
        
        if content_pages_start == -1 or content_pages_end == -1:
            print("❌ Could not find CONTENT_PAGES in template")
            return None
        
        new_content_pages = "CONTENT_PAGES = [\n"
        for i, page in enumerate(lesson_structure['content_pages']):
            new_content_pages += f'    {{\n'
            new_content_pages += f'        "page_number": {i + 2},\n'
            new_content_pages += f'        "title": "{page["title"]}",\n'
            new_content_pages += f'        "keywords": "{truncate_text(page["keywords"], 500)}",\n'
            new_content_pages += f'        "image_concept": "{truncate_text(page["image_concept"], 1000)}",\n'
            new_content_pages += f'        "content_focus": "{truncate_text(page["content_focus"], 500)}"\n'
            new_content_pages += f'    }}'
            if i < len(lesson_structure['content_pages']) - 1:
                new_content_pages += ','
            new_content_pages += '\n'
        new_content_pages += ']'
        
        new_script = template_content
        
        new_path_setup = "# Add the project root directory to Python path\nsys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))"
        new_script = re.sub(r"# Add the app directory to Python path\nsys.path.insert\(0, os.path.dirname\(__file__\)\)", new_path_setup, new_script)

        new_env_path = "env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')"
        new_script = re.sub(r"env_path = os.path.join\(os.path.dirname\(__file__\), '.env'\)", new_env_path, new_script)

        new_script = new_script.replace(
            'LESSON_TITLE = "Onomatopoeia and Mimetic Words in Daily Life"',
            f'LESSON_TITLE = "{lesson_structure["lesson_title"]}"'
        )
        
        new_script = new_script.replace(
            'LESSON_DIFFICULTY = "Intermediate"',
            f'LESSON_DIFFICULTY = "{lesson_structure["difficulty"]}"'
        )
        
        new_script = new_script.replace(
            'LESSON_DESCRIPTION = "Discover the vibrant world of Japanese onomatopoeia and mimetic words used in everyday situations. Learn how sound words and descriptive expressions bring Japanese language to life through daily scenarios."',
            f'LESSON_DESCRIPTION = "{truncate_text(lesson_structure["lesson_description"], 500)}"'
        )
        
        old_content_pages = template_content[content_pages_start:content_pages_end]
        new_script = new_script.replace(old_content_pages, new_content_pages)
        
        new_script = new_script.replace(
            'difficulty_level=2,  # 1=Beginner, 2=Intermediate, 3=Advanced',
            f'difficulty_level={difficulty_int},  # 1=Beginner, 2=Intermediate, 3=Advanced'
        )
        
        category_name = lesson_structure.get("category_name", "Sprachgrundlagen")
        category_logic = f'''
        # Find category
        category = LessonCategory.query.filter_by(name="{category_name}").first()
        if not category:
            print(f"[WARNING] Category '{category_name}' not found. Defaulting to 'Sprachgrundlagen'.")
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
            difficulty_level={difficulty_int},
            is_published=True,
            category_id=category.id if category else None
        )
'''
        lesson_creation_pattern = r'# Create the lesson\n        lesson = Lesson\([\s\S]*?\)'
        new_script = re.sub(lesson_creation_pattern, category_logic, new_script, 1)
        
        new_script = new_script.replace(
            'from app.models import Lesson, LessonContent, QuizQuestion, QuizOption, UserQuizAnswer, UserLessonProgress',
            'from app.models import Lesson, LessonCategory, LessonContent, QuizQuestion, QuizOption, UserQuizAnswer, UserLessonProgress'
        )

        script_title = lesson_structure["lesson_title"]
        new_header = f'#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n"""\nThis script creates a comprehensive Japanese lesson titled \\"{script_title}\\" for German-speaking learners.\n"""'
        old_header_start = new_script.find('"""')
        old_header_end = new_script.find('"""', old_header_start + 3) + 3
        if old_header_start != -1 and old_header_end != -1:
            new_script = new_script[:old_header_start] + new_header + new_script[old_header_end:]
        
        print(f"✅ Generated script for: {script_title}")
        return new_script
        
    except Exception as e:
        print(f"❌ Error generating script: {e}")
        return None

def save_script(script_content, filename):
    """Save the generated script to the output directory."""
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        print(f"✅ Script saved: {filepath}")
        return True
    except Exception as e:
        print(f"❌ Error saving script: {e}")
        return False

def main():
    """Main execution function."""
    print("🚀 Starting Google Gemini 2.5 Pro Japanese Lesson Script Generator (for German Speakers)")
    print("=" * 80)
    
    setup_logging()
    load_env()
    
    model = initialize_gemini()
    if not model:
        return
    
    topics = read_topics_file()
    if not topics:
        return
    
    template_content = read_template_file()
    if not template_content:
        return
    
    successful_generations = 0
    failed_generations = 0
    
    for i, topic in enumerate(topics, 1):
        print(f"\n--- Processing Topic {i}/{len(topics)}: {topic['title']} ---")
        
        lesson_structure = generate_lesson_structure(model, topic)
        if not lesson_structure:
            print(f"❌ Failed to generate structure for: {topic['title']}")
            failed_generations += 1
            continue
        
        script_content = generate_lesson_script(template_content, topic, lesson_structure)
        if not script_content:
            print(f"❌ Failed to generate script for: {topic['title']}")
            failed_generations += 1
            continue
        
        filename = create_script_filename(lesson_structure['lesson_title'])
        if save_script(script_content, filename):
            successful_generations += 1
        else:
            failed_generations += 1
        
        if i < len(topics):
            print("⏳ Waiting 2 seconds before next generation...")
            time.sleep(2)
    
    print("\n" + "=" * 80)
    print("📊 JAPANESE LESSONS FOR GERMANS - GENERATION SUMMARY")
    print("=" * 80)
    print(f"✅ Successfully generated: {successful_generations} scripts")
    print(f"❌ Failed generations: {failed_generations}")
    print(f"📁 Scripts saved to: {OUTPUT_DIR}/")
    print(f"📝 Log saved to: {LOG_FILE}")
    
    if successful_generations > 0:
        print(f"\n🎉 Generation complete! {successful_generations} Japanese lesson scripts for German speakers are ready.")
    else:
        print("\n❌ No scripts were generated successfully. Please check the errors above.")

if __name__ == "__main__":
    main()
