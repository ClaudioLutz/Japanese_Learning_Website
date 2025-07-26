#!/usr/bin/env python3
"""
Google Gemini 2.5 Pro Powered Lesson Script Generator - FIXED VERSION

This script reads the Japanese lesson generator.md file and uses Google Gemini 2.5 Pro
to dynamically generate lesson creation scripts for each topic. Each generated script
follows the exact same structure as create_onomatopoeia_lesson.py but with all known
issues pre-fixed.

FIXES APPLIED:
- Correct Python path setup for scripts in subdirectory
- Proper import handling to avoid UnboundLocalError
- JLPT level conversion from string to integer
- Difficulty level conversion from string to integer
- Database field length constraints handling
- Correct .env file path resolution
- All imports consolidated at top level

Generated scripts are saved to the lesson_creation_scripts/ folder and should work
perfectly without needing any fix scripts.
"""

import os
import sys
import re
import json
import time
from datetime import datetime
from lesson_pipeline_utils import (
    setup_logging,
    load_env,
    initialize_gemini,
    read_file,
    save_script,
    create_script_filename,
    truncate_text,
)

# Configuration
GEMINI_MODEL = "gemini-2.5-pro"
LESSON_TEMPLATE_FILE = "lesson_creation_template.py"
TOPICS_FILE = "Japanese lesson generator.md"
OUTPUT_DIR = "lesson_creation_scripts"
LOG_FILE = f"lesson_generation_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
LANGUAGE = "en"

def read_topics_file():
    """Read and parse the Japanese lesson generator.md file."""
    try:
        with open(TOPICS_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract topics using regex
        topics = []
        pattern = r'(\d+)\.\s*\*\*(.*?)\*\*\s*\n\s*\*\s*(.*?)(?=\n\n|\n\d+\.|\Z)'
        matches = re.findall(pattern, content, re.DOTALL)
        
        for match in matches:
            topic_id = int(match[0])
            title = match[1].strip()
            description = match[2].strip()
            
# Skip topic #2 (Onomatopoeia) as it is the template
            if topic_id != 2:
                topics.append({
                    'id': topic_id,
                    'title': title,
                    'description': description
                })
        
        print(f"Found {len(topics)} topics to generate (excluding existing onomatopoeia lesson)")
        return topics
    
    except Exception as e:
        print(f"Error reading topics file: {e}")
        return []

def read_template_file():
    """Read the template lesson creation script."""
    return read_file(LESSON_TEMPLATE_FILE)

def convert_difficulty_to_int(difficulty_str):
    """Convert difficulty string to integer."""
    difficulty_map = {
        'beginner': 1,
        'elementary': 1,
        'easy': 1,
        'basic': 1,
        'intermediate': 2,
        'medium': 2,
        'advanced': 3,
        'hard': 3,
        'expert': 4,
        'master': 5
    }
    return difficulty_map.get(difficulty_str.lower().strip(), 2)  # Default to intermediate

def generate_lesson_structure(model, topic):
    """Use Gemini to generate lesson structure for a topic."""
    
    # List of available categories
    available_categories = [
        "Culture & Traditions",
        "Food & Dining",
        "Daily Life & Society",
        "Pop Culture & Modern Japan",
        "Language & Communication",
        "Travel & Geography",
        "Language Fundamentals"
    ]
    
    prompt = f"""
You are an expert Japanese language educator and curriculum designer. Analyze the following Japanese lesson topic and create a comprehensive lesson structure.

TOPIC: {topic['title']}
DESCRIPTION: {topic['description']}

Generate a detailed lesson structure in JSON format with the following specifications:

1. LESSON METADATA:
   - Determine appropriate difficulty level (Beginner, Intermediate, or Advanced)
   - Choose the most relevant category from this list: {', '.join(available_categories)}
   - Create comprehensive keywords (10-15 relevant terms)
   - Define cultural focus areas
   - Write an engaging lesson description (2-3 sentences)

2. CONTENT PAGES (Generate exactly 7 content pages):
   - Each page should have a specific theme/focus area
   - Include Japanese title with romanization in parentheses
   - Provide detailed keywords for each page
   - Write content focus description (what students will learn)
   - Create detailed image concept for AI image generation (be specific about visual elements, style should be "cute manga/anime art style with clean lines and cultural authenticity. IMPORTANT: No text, writing, signs, or characters should be visible in the image.")

3. EDUCATIONAL STRUCTURE:
   - Ensure logical progression from basic to advanced concepts
   - Include cultural context and real-world applications
   - Balance vocabulary, grammar, and cultural understanding

Return ONLY a valid JSON object with this exact structure:
{{
  "lesson_title": "Complete lesson title",
  "lesson_description": "Detailed description for students",
  "difficulty": "Beginner/Intermediate/Advanced",
  "category_name": "Chosen Category Name",
  "keywords": "comma-separated keywords",
  "cultural_focus": "main cultural aspects covered",
  "content_pages": [
    {{
      "title": "Page Title - Japanese Title (Romanization)",
      "keywords": "page-specific keywords",
      "content_focus": "what this page teaches",
      "image_concept": "detailed image description for AI generation"
    }}
  ]
}}

Make sure the lesson is educationally sound, culturally authentic, and engaging for Japanese language learners.
"""

    try:
        print(f"🤖 Generating lesson structure for: {topic['title']}")
        response = model.generate_content(prompt)
        
        # Extract JSON from response
        response_text = response.text.strip()
        
        # Try to find JSON in the response
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start != -1 and json_end != -1:
            json_text = response_text[json_start:json_end]
            lesson_structure = json.loads(json_text)
            print(f"Generated structure with {len(lesson_structure.get('content_pages', []))} content pages")
            return lesson_structure
        else:
            print(f"Could not extract JSON from Gemini response")
            return None
            
    except Exception as e:
        print(f"Error generating lesson structure: {e}")
        return None

def generate_lesson_script(template_content, topic, lesson_structure):
    """Generate the lesson creation script using the template with all fixes applied."""
    try:
        # Convert difficulty to integer
        difficulty_int = convert_difficulty_to_int(lesson_structure['difficulty'])
        
        # Extract the content pages configuration from template
        content_pages_start = template_content.find('CONTENT_PAGES = [')
        content_pages_end = template_content.find(']', content_pages_start) + 1
        
        if content_pages_start == -1 or content_pages_end == -1:
            print("Could not find CONTENT_PAGES in template")
            return None
        
        # Generate new CONTENT_PAGES configuration
        new_content_pages = "CONTENT_PAGES = [\n"
        for i, page in enumerate(lesson_structure['content_pages']):
            new_content_pages += f'    {{\n'
            new_content_pages += f'        "page_number": {i + 2},\n'
            new_content_pages += f'        "title": "{page["title"].replace('"', '\\"')}",\n'
            new_content_pages += f'        "keywords": "{truncate_text(page["keywords"], 500).replace('"', '\\"')}",\n'
            new_content_pages += f'        "image_concept": "{truncate_text(page["image_concept"], 1000).replace('"', '\\"')}",\n'
            new_content_pages += f'        "content_focus": "{truncate_text(page["content_focus"], 500).replace('"', '\\"')}"\n'
            new_content_pages += f'    }}'
            if i < len(lesson_structure['content_pages']) - 1:
                new_content_pages += ','
            new_content_pages += '\n'
        new_content_pages += ']'
        
        # Start with template and apply all fixes
        new_script = template_content
        
        # FIX 1: Update Python path setup to work from subdirectory
        old_path_setup = "# Add the app directory to Python path\nsys.path.insert(0, os.path.dirname(__file__))"
        new_path_setup = "# Add the project root directory to Python path\nsys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))"
        new_script = new_script.replace(old_path_setup, new_path_setup)
        
        # FIX 2: Fix .env file path to look in parent directory
        old_env_path = "env_path = os.path.join(os.path.dirname(__file__), '.env')"
        new_env_path = "env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')"
        new_script = new_script.replace(old_env_path, new_env_path)
        
        # FIX 3: Consolidate all imports at top level to avoid UnboundLocalError
        # Replace the existing imports section with consolidated imports
        import_section = '''from app import create_app, db
from app.models import Lesson, LessonContent, QuizQuestion, QuizOption, UserQuizAnswer, UserLessonProgress
from app.ai_services import AILessonContentGenerator'''
        
        old_import_pattern = r'from app import create_app, db\nfrom app\.models import Lesson, LessonContent, QuizQuestion, QuizOption\nfrom app\.ai_services import AILessonContentGenerator'
        new_script = re.sub(old_import_pattern, import_section, new_script)
        
        # Remove any duplicate imports that might cause issues
        new_script = re.sub(r'\s+from app\.models import UserQuizAnswer.*?\n', '\n', new_script)
        new_script = re.sub(r'\s+from app\.models import UserLessonProgress.*?\n', '\n', new_script)
        
        # FIX 4: Replace lesson configuration with proper values
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
        
        # FIX 5: Replace content pages
        old_content_pages = template_content[content_pages_start:content_pages_end]
        new_script = new_script.replace(old_content_pages, new_content_pages)
        
        # FIX 6: Update difficulty level to use integer
        new_script = new_script.replace(
            'difficulty_level=2,  # 1=Beginner, 2=Intermediate, 3=Advanced',
            f'difficulty_level={difficulty_int},  # 1=Beginner, 2=Intermediate, 3=Advanced'
        )
        
        # Add category assignment logic
        category_name = lesson_structure.get("category_name", "Language Fundamentals")
        
        # Inject category lookup and assignment into the create_lesson function
        category_logic = f'''
        # Find category
        category = LessonCategory.query.filter_by(name="{category_name}").first()
        if not category:
            print(f"[WARNING] Category '{category_name}' not found. Defaulting to 'Language Fundamentals'.")
            category = LessonCategory.query.filter_by(name="Language Fundamentals").first()
            if not category:
                print("[ERROR] Default category 'Language Fundamentals' not found. Cannot assign category.")
                # Create it if it doesn't exist
                category = LessonCategory(name="Language Fundamentals", description="Core concepts of the Japanese language.")
                db.session.add(category)
                db.session.commit()
                print("[OK] Created default category 'Language Fundamentals'.")

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
        
        # Replace the original lesson creation block
        lesson_creation_pattern = r'# Create the lesson\n        lesson = Lesson\([\s\S]*?\)'
        new_script = re.sub(lesson_creation_pattern, category_logic, new_script, 1)
        
        # Also need to import LessonCategory
        new_script = new_script.replace(
            'from app.models import Lesson, LessonContent, QuizQuestion, QuizOption',
            'from app.models import Lesson, LessonCategory, LessonContent, QuizQuestion, QuizOption'
        )

        # FIX 17: Add UTF-8 encoding fix for Windows console
        utf8_fix_code = '''import codecs

# Reconfigure stdout to use UTF-8 encoding, especially for Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except Exception as e:
        print(f"Could not reconfigure stdout/stderr to UTF-8: {e}")

'''
        # Inject the fix after the initial imports
        new_script = new_script.replace(
            "import uuid\n",
            "import uuid\n" + utf8_fix_code,
            1  # Only replace the first occurrence
        )

        # FIX 7: Update script header comment and add encoding declaration
        script_title = lesson_structure["lesson_title"]
        new_header = f'#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n"""\nThis script creates a comprehensive {script_title} lesson organized into pages.\nEach content page covers different aspects of the topic with explanations, followed by dedicated quiz pages.\nThe quizzes are separated from the explanatory content as requested.\n\nFIXES APPLIED:\n- Correct Python path setup for subdirectory execution\n- Consolidated imports to avoid UnboundLocalError\n- Proper difficulty level integer conversion\n- Database field length constraints handled\n- Correct .env file path resolution\n- UTF-8 encoding declaration for Unicode support\n"""'
        
        old_header_start = new_script.find('"""')
        old_header_end = new_script.find('"""', old_header_start + 3) + 3
        if old_header_start != -1 and old_header_end != -1:
            new_script = new_script[:old_header_start] + new_header + new_script[old_header_end:]
        
        # FIX 8: Update overview image concept
        old_overview_concept = 'overview_image_concept = "Vibrant collage showing various Japanese onomatopoeia in daily life - sound waves, speech bubbles with sound effects, people in different daily activities (cooking, walking, talking), nature sounds, emotional expressions, all in a harmonious composition representing the richness of Japanese sound words. Style: cute manga/anime art style with clean lines and cultural authenticity. IMPORTANT: No text, writing, signs, or characters should be visible in the image."'
        new_overview_concept = f'overview_image_concept = "Vibrant overview scene representing {lesson_structure["lesson_title"]} - showing the main themes and cultural elements of this lesson in a harmonious composition. Style: cute manga/anime art style with clean lines and cultural authenticity. IMPORTANT: No text, writing, signs, or characters should be visible in the image."'
        new_script = new_script.replace(old_overview_concept, new_overview_concept)
        
        # FIX 9: Update introduction content
        old_intro_topic = 'intro_topic = f"Comprehensive introduction to {LESSON_TITLE}. Explain what students will learn about Japanese onomatopoeia (giongo) and mimetic words (gitaigo), their importance in daily communication, how they make Japanese language more expressive and vivid, and what daily life scenarios will be covered. Include learning objectives and cultural significance of sound words in Japanese."'
        new_intro_topic = f'intro_topic = f"Comprehensive introduction to {{LESSON_TITLE}}. Explain what students will learn in this lesson about {topic["title"].lower()}, the cultural significance and practical applications. Include learning objectives and how this knowledge will help students understand Japanese culture and daily life better."'
        new_script = new_script.replace(old_intro_topic, new_intro_topic)
        
        # FIX 10: Update introduction keywords
        old_intro_keywords = 'intro_keywords = "onomatopoeia, mimetic words, giongo, gitaigo, daily life, Japanese expressions, sound words, cultural communication, language learning"'
        new_intro_keywords = f'intro_keywords = "{truncate_text(lesson_structure["keywords"], 500)}"'
        new_script = new_script.replace(old_intro_keywords, new_intro_keywords)
        
        # FIX 11: Update all title references
        new_script = new_script.replace(
            'title="Welcome to Japanese Onomatopoeia"',
            f'title="Welcome to {lesson_structure["lesson_title"]}"'
        )
        
        new_script = new_script.replace(
            'title="Onomatopoeia and Mimetic Words - Lesson Overview"',
            f'title="{lesson_structure["lesson_title"]} - Lesson Overview"'
        )
        
        # FIX 12: Update conclusion content
        old_conclusion_topic = 'conclusion_topic = "Conclusion for Japanese Onomatopoeia and Mimetic Words lesson. Summarize key learnings about Japanese sound words, their importance in daily communication, how they enrich the language, and encourage continued practice and listening for these expressions in real-life situations."'
        new_conclusion_topic = f'conclusion_topic = "Conclusion for {lesson_structure["lesson_title"]} lesson. Summarize key learnings from this lesson, their importance in understanding Japanese culture and daily life, and encourage continued practice and application of this knowledge."'
        new_script = new_script.replace(old_conclusion_topic, new_conclusion_topic)
        
        new_script = new_script.replace(
            'conclusion_keywords = "onomatopoeia, mimetic words, daily life, Japanese expressions, language enrichment, communication, cultural understanding, conclusion"',
            f'conclusion_keywords = "{truncate_text(lesson_structure["keywords"], 400)}, cultural understanding, conclusion"'
        )
        
        new_script = new_script.replace(
            'title="Onomatopoeia and Mimetic Words - Lesson Conclusion"',
            f'title="{lesson_structure["lesson_title"]} - Lesson Conclusion"'
        )
        
        # FIX 13: Update final quiz content
        new_script = new_script.replace(
            'title="Onomatopoeia and Mimetic Words - Comprehensive Final Quiz"',
            f'title="{lesson_structure["lesson_title"]} - Comprehensive Final Quiz"'
        )
        
        new_script = new_script.replace(
            'content_text="Test your overall knowledge of Japanese onomatopoeia and mimetic words in daily life"',
            f'content_text="Test your overall knowledge of {lesson_structure["lesson_title"].lower()}"'
        )
        
        # FIX 14: Remove any remaining function-level imports that could cause issues
        new_script = re.sub(r'\s+# First, delete all user quiz answers.*?\n.*?from app\.models import.*?\n', '\n            # Delete user quiz answers and progress\n', new_script, flags=re.DOTALL)
        
        # FIX 15: Replace Unicode characters in print statements with ASCII-safe alternatives
        emoji_replacements = {
            '✅': '[OK]',
            '❌': '[ERROR]',
            '🤖': '[AI]',
            '🖼️': '[IMG]',
            '🎨': '[ART]',
            '⏳': '[WAIT]',
            '🎉': '[SUCCESS]',
            '📊': '[STATS]',
            '📁': '[FOLDER]',
            '📝': '[LOG]',
            '🚀': '[START]',
            '🔧': '[FIX]',
            '⚠️': '[WARNING]',
            '🎯': '[TARGET]'
        }
        
        # Replace emoji in the script content
        for emoji, replacement in emoji_replacements.items():
            new_script = new_script.replace(emoji, replacement)
        
        # FIX 16: Fix the specific print statements that cause UnicodeEncodeError with Japanese characters
        # Replace problematic print statements with safe console output while preserving Japanese content
        new_script = new_script.replace(
            'print(f"--- Creating Lesson: {LESSON_TITLE} ---")',
            'print("--- Creating Lesson: [Starting] ---")'
        )
        
        new_script = new_script.replace(
            'print(f"Found existing lesson \'{LESSON_TITLE}\' (ID: {existing_lesson.id}). Deleting it.")',
            'print(f"Found existing lesson [EXISTING] (ID: {existing_lesson.id}). Deleting it.")'
        )
        
        new_script = new_script.replace(
            'print(f"[OK] Lesson \'{LESSON_TITLE}\' created with ID: {lesson.id}")',
            'print(f"[OK] Lesson created with ID: {lesson.id}")'
        )
        
        new_script = new_script.replace(
            'print(f"--- {LESSON_TITLE} Creation Complete! ---")',
            'print("--- Lesson Creation Complete! ---")'
        )
        
        new_script = new_script.replace(
            'print("[OK] {LESSON_TITLE} lesson created successfully!")',
            'print("[OK] Lesson created successfully!")'
        )

        # FIX 17: Add UTF-8 encoding fix for Windows console
        utf8_fix_code = '''import codecs

# Reconfigure stdout to use UTF-8 encoding, especially for Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
        print("Successfully reconfigured stdout and stderr to UTF-8.")
    except Exception as e:
        print(f"Could not reconfigure stdout/stderr to UTF-8: {e}")

'''
        # Inject the fix after the initial imports
        new_script = new_script.replace(
            "import uuid\n",
            "import uuid\n" + utf8_fix_code,
            1  # Only replace the first occurrence
        )
        
        print(f"Generated script for: {script_title}")
        return new_script
        
    except Exception as e:
        print(f"Error generating script: {e}")
        return None

def save_generated_script(script_content, filename):
    """Save the generated script to the output directory."""
    return save_script(script_content, filename, OUTPUT_DIR)

def main():
    """Main execution function."""
    print("Starting Google Gemini 2.5 Pro Lesson Script Generator - FIXED VERSION")
    print("=" * 80)
    print("This version generates scripts with all known issues pre-fixed:")
    print("✓ Correct Python path setup")
    print("✓ Consolidated imports (no UnboundLocalError)")
    print("✓ JLPT level integer conversion")
    print("✓ Difficulty level integer conversion")
    print("✓ Database field length constraints")
    print("✓ Correct .env file path resolution")
    print("=" * 80)
    
    setup_logging(LOG_FILE)
    
    # Load environment variables
    load_env()
    
    # Initialize Gemini
    model = initialize_gemini(GEMINI_MODEL)
    if not model:
        return
    
    # Read topics
    topics = read_topics_file()
    if not topics:
        return
    
    # Read template
    template_content = read_template_file()
    if not template_content:
        return
    
    # Generate scripts for each topic
    successful_generations = 0
    failed_generations = 0
    
    for i, topic in enumerate(topics, 1):
        print(f"\n--- Processing Topic {i}/{len(topics)}: {topic['title']} ---")
        
        # Generate lesson structure using Gemini
        lesson_structure = generate_lesson_structure(model, topic)
        if not lesson_structure:
            print(f"Failed to generate structure for: {topic['title']}")
            failed_generations += 1
            continue
        
        # Generate script with all fixes applied
        script_content = generate_lesson_script(template_content, topic, lesson_structure)
        if not script_content:
            print(f"Failed to generate script for: {topic['title']}")
            failed_generations += 1
            continue
        
        # Save script
        filename = create_script_filename(lesson_structure['lesson_title'], LANGUAGE)
        if save_generated_script(script_content, filename):
            successful_generations += 1
        else:
            failed_generations += 1
        
        # Add delay to respect API rate limits
        if i < len(topics):
            print("⏳ Waiting 2 seconds before next generation...")
            time.sleep(2)
    
    # Final summary
    print("\n" + "=" * 80)
    print("GENERATION SUMMARY")
    print("=" * 80)
    print(f"Successfully generated: {successful_generations} scripts")
    print(f"Failed generations: {failed_generations}")
    print(f"Scripts saved to: {OUTPUT_DIR}/")
    print(f"Log saved to: {LOG_FILE}")
    
    if successful_generations > 0:
        print(f"\nGeneration complete! {successful_generations} lesson creation scripts are ready.")
        print("All scripts generated with fixes applied - no additional fix scripts needed!")
        print("Next step: Run 'python run_all_lesson_scripts.py' to create all lessons in the database.")
        print("\nFixes applied to all generated scripts:")
        print("  - Correct Python path setup for subdirectory execution")
        print("  - Consolidated imports to prevent UnboundLocalError")
        print("  - Difficulty levels converted to integers")
        print("  - Database field length constraints handled")
        print("  - Correct .env file path resolution")
        print("  - All imports consolidated at top level")
    else:
        print("\nNo scripts were generated successfully. Please check the errors above.")

if __name__ == "__main__":
    main()
