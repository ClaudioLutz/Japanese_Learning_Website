#!/usr/bin/env python3
"""
Google Gemini 2.5 Pro Powered Lesson Script Generator

This script reads the Japanese lesson generator.md file and uses Google Gemini 2.5 Pro
to dynamically generate lesson creation scripts for each topic. Each generated script
follows the exact same structure as create_onomatopoeia_lesson.py.

The AI analyzes each topic and creates:
- Appropriate lesson structure (6-8 content pages)
- Cultural context and keywords
- Image concepts for each page
- Quiz specifications
- Difficulty levels

Generated scripts are saved to the lesson_creation_scripts/ folder.
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
GEMINI_MODEL = "gemini-1.5-pro"  # Using stable Gemini model
LESSON_TEMPLATE_FILE = "create_onomatopoeia_lesson.py"
TOPICS_FILE = "Japanese lesson generator.md"
OUTPUT_DIR = "lesson_creation_scripts"
LOG_FILE = f"lesson_generation_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

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
            
            # Skip topic #2 (Onomatopoeia) as it already exists
            if topic_id != 2:
                topics.append({
                    'id': topic_id,
                    'title': title,
                    'description': description
                })
        
        print(f"✅ Found {len(topics)} topics to generate (excluding existing onomatopoeia lesson)")
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

def generate_lesson_structure(model, topic):
    """Use Gemini to generate lesson structure for a topic."""
    prompt = f"""
You are an expert Japanese language educator and curriculum designer. Analyze the following Japanese lesson topic and create a comprehensive lesson structure.

TOPIC: {topic['title']}
DESCRIPTION: {topic['description']}

Generate a detailed lesson structure in JSON format with the following specifications:

1. LESSON METADATA:
   - Determine appropriate difficulty level (Beginner=1, Intermediate=2, Advanced=3)
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
  "difficulty_level": 1/2/3,
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
    # Remove special characters and convert to lowercase
    filename = re.sub(r'[^\w\s-]', '', title.lower())
    filename = re.sub(r'[-\s]+', '_', filename)
    return f"create_{filename}_lesson.py"

def generate_lesson_script(template_content, topic, lesson_structure):
    """Generate the lesson creation script using the template."""
    try:
        # Extract the content pages configuration from template
        content_pages_start = template_content.find('CONTENT_PAGES = [')
        content_pages_end = template_content.find(']', content_pages_start) + 1
        
        if content_pages_start == -1 or content_pages_end == -1:
            print("❌ Could not find CONTENT_PAGES in template")
            return None
        
        # Generate new CONTENT_PAGES configuration
        new_content_pages = "CONTENT_PAGES = [\n"
        for i, page in enumerate(lesson_structure['content_pages']):
            new_content_pages += f'    {{\n'
            new_content_pages += f'        "page_number": {i + 2},\n'  # Start from page 2 (page 1 is intro)
            new_content_pages += f'        "title": "{page["title"]}",\n'
            new_content_pages += f'        "keywords": "{page["keywords"]}",\n'
            new_content_pages += f'        "image_concept": "{page["image_concept"]}",\n'
            new_content_pages += f'        "content_focus": "{page["content_focus"]}"\n'
            new_content_pages += f'    }}'
            if i < len(lesson_structure['content_pages']) - 1:
                new_content_pages += ','
            new_content_pages += '\n'
        new_content_pages += ']'
        
        # Replace template variables
        new_script = template_content
        
        # Replace lesson configuration
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
            f'LESSON_DESCRIPTION = "{lesson_structure["lesson_description"]}"'
        )
        
        # Replace content pages
        old_content_pages = template_content[content_pages_start:content_pages_end]
        new_script = new_script.replace(old_content_pages, new_content_pages)
        
        # Update difficulty level in lesson creation
        new_script = new_script.replace(
            'difficulty_level=2,  # 1=Beginner, 2=Intermediate, 3=Advanced',
            f'difficulty_level={lesson_structure["difficulty_level"]},  # 1=Beginner, 2=Intermediate, 3=Advanced'
        )
        
        # Update script header comment and fix Python path
        script_title = lesson_structure["lesson_title"]
        new_header = f'"""\nThis script creates a comprehensive {script_title} lesson organized into pages.\nEach content page covers different aspects of the topic with explanations, followed by dedicated quiz pages.\nThe quizzes are separated from the explanatory content as requested.\n"""'
        
        old_header_start = new_script.find('"""')
        old_header_end = new_script.find('"""', old_header_start + 3) + 3
        if old_header_start != -1 and old_header_end != -1:
            new_script = new_script[:old_header_start] + new_header + new_script[old_header_end:]
        
        # Fix the Python path setup to work from lesson_creation_scripts directory
        old_path_setup = "# Add the app directory to Python path\nsys.path.insert(0, os.path.dirname(__file__))"
        new_path_setup = "# Add the project root directory to Python path\nsys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))"
        new_script = new_script.replace(old_path_setup, new_path_setup)
        
        # Fix the .env path to look in parent directory
        old_env_path = "env_path = os.path.join(os.path.dirname(__file__), '.env')"
        new_env_path = "env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')"
        new_script = new_script.replace(old_env_path, new_env_path)
        
        # Fix the overview image concept to match the actual lesson topic
        old_overview_concept = 'overview_image_concept = "Vibrant collage showing various Japanese onomatopoeia in daily life - sound waves, speech bubbles with sound effects, people in different daily activities (cooking, walking, talking), nature sounds, emotional expressions, all in a harmonious composition representing the richness of Japanese sound words. Style: cute manga/anime art style with clean lines and cultural authenticity. IMPORTANT: No text, writing, signs, or characters should be visible in the image."'
        new_overview_concept = f'overview_image_concept = "Vibrant overview scene representing {lesson_structure["lesson_title"]} - showing the main themes and cultural elements of this lesson in a harmonious composition. Style: cute manga/anime art style with clean lines and cultural authenticity. IMPORTANT: No text, writing, signs, or characters should be visible in the image."'
        new_script = new_script.replace(old_overview_concept, new_overview_concept)
        
        # Fix the introduction content to match the actual lesson
        old_intro_topic = 'intro_topic = f"Comprehensive introduction to {LESSON_TITLE}. Explain what students will learn about Japanese onomatopoeia (giongo) and mimetic words (gitaigo), their importance in daily communication, how they make Japanese language more expressive and vivid, and what daily life scenarios will be covered. Include learning objectives and cultural significance of sound words in Japanese."'
        new_intro_topic = f'intro_topic = f"Comprehensive introduction to {{LESSON_TITLE}}. Explain what students will learn in this lesson about {topic["title"].lower()}, the cultural significance and practical applications. Include learning objectives and how this knowledge will help students understand Japanese culture and daily life better."'
        new_script = new_script.replace(old_intro_topic, new_intro_topic)
        
        # Fix the introduction keywords
        old_intro_keywords = 'intro_keywords = "onomatopoeia, mimetic words, giongo, gitaigo, daily life, Japanese expressions, sound words, cultural communication, language learning"'
        new_intro_keywords = f'intro_keywords = "{lesson_structure["keywords"]}"'
        new_script = new_script.replace(old_intro_keywords, new_intro_keywords)
        
        # Fix the welcome title
        old_welcome_title = 'title="Welcome to Japanese Onomatopoeia"'
        new_welcome_title = f'title="Welcome to {lesson_structure["lesson_title"]}"'
        new_script = new_script.replace(old_welcome_title, new_welcome_title)
        
        # Fix the image content title
        old_image_title = 'title="Onomatopoeia and Mimetic Words - Lesson Overview"'
        new_image_title = f'title="{lesson_structure["lesson_title"]} - Lesson Overview"'
        new_script = new_script.replace(old_image_title, new_image_title)
        
        # Fix the conclusion topic
        old_conclusion_topic = 'conclusion_topic = "Conclusion for Japanese Onomatopoeia and Mimetic Words lesson. Summarize key learnings about Japanese sound words, their importance in daily communication, how they enrich the language, and encourage continued practice and listening for these expressions in real-life situations."'
        new_conclusion_topic = f'conclusion_topic = "Conclusion for {lesson_structure["lesson_title"]} lesson. Summarize key learnings from this lesson, their importance in understanding Japanese culture and daily life, and encourage continued practice and application of this knowledge."'
        new_script = new_script.replace(old_conclusion_topic, new_conclusion_topic)
        
        # Fix the conclusion keywords
        old_conclusion_keywords = 'conclusion_keywords = "onomatopoeia, mimetic words, daily life, Japanese expressions, language enrichment, communication, cultural understanding, conclusion"'
        new_conclusion_keywords = f'conclusion_keywords = "{lesson_structure["keywords"]}, cultural understanding, conclusion"'
        new_script = new_script.replace(old_conclusion_keywords, new_conclusion_keywords)
        
        # Fix the conclusion title
        old_conclusion_title = 'title="Onomatopoeia and Mimetic Words - Lesson Conclusion"'
        new_conclusion_title = f'title="{lesson_structure["lesson_title"]} - Lesson Conclusion"'
        new_script = new_script.replace(old_conclusion_title, new_conclusion_title)
        
        # Fix the final quiz title
        old_final_quiz_title = 'title="Onomatopoeia and Mimetic Words - Comprehensive Final Quiz"'
        new_final_quiz_title = f'title="{lesson_structure["lesson_title"]} - Comprehensive Final Quiz"'
        new_script = new_script.replace(old_final_quiz_title, new_final_quiz_title)
        
        # Fix the final quiz description
        old_final_quiz_desc = 'content_text="Test your overall knowledge of Japanese onomatopoeia and mimetic words in daily life"'
        new_final_quiz_desc = f'content_text="Test your overall knowledge of {lesson_structure["lesson_title"].lower()}"'
        new_script = new_script.replace(old_final_quiz_desc, new_final_quiz_desc)
        
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
    print("🚀 Starting Google Gemini 2.5 Pro Lesson Script Generator")
    print("=" * 60)
    
    setup_logging()
    
    # Load environment variables
    load_env()
    
    # Initialize Gemini
    model = initialize_gemini()
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
            print(f"❌ Failed to generate structure for: {topic['title']}")
            failed_generations += 1
            continue
        
        # Generate script
        script_content = generate_lesson_script(template_content, topic, lesson_structure)
        if not script_content:
            print(f"❌ Failed to generate script for: {topic['title']}")
            failed_generations += 1
            continue
        
        # Save script
        filename = create_script_filename(lesson_structure['lesson_title'])
        if save_script(script_content, filename):
            successful_generations += 1
        else:
            failed_generations += 1
        
        # Add delay to respect API rate limits
        if i < len(topics):
            print("⏳ Waiting 2 seconds before next generation...")
            time.sleep(2)
    
    # Final summary
    print("\n" + "=" * 60)
    print("📊 GENERATION SUMMARY")
    print("=" * 60)
    print(f"✅ Successfully generated: {successful_generations} scripts")
    print(f"❌ Failed generations: {failed_generations}")
    print(f"📁 Scripts saved to: {OUTPUT_DIR}/")
    print(f"📝 Log saved to: {LOG_FILE}")
    
    if successful_generations > 0:
        print(f"\n🎉 Generation complete! {successful_generations} lesson creation scripts are ready.")
        print("Next step: Run 'python run_all_lesson_scripts.py' to create all lessons in the database.")
    else:
        print("\n❌ No scripts were generated successfully. Please check the errors above.")

if __name__ == "__main__":
    main()
