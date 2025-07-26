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
LOG_FILE = f"logs/japanese_for_germans_generation_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
LANGUAGE = "de"

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
        
        print(f"Found {len(topics)} Japanese lessons for Germans to generate.")
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
Du bist ein Experte für japanische Sprache und erstellst Inhalte für deutschsprachige Lernende. Analysiere das folgende japanische Lektionsthema und erstelle eine umfassende Lektionsstruktur. Die gesamte Ausgabe, einschließlich Titel, Beschreibungen und Schlüsselwörter, muss auf DEUTSCH sein.

THEMA (auf Deutsch): {topic['title']}
BESCHREIBUNG (auf Deutsch): {topic['description']}

Erstelle eine detaillierte Lektionsstruktur im JSON-Format mit den folgenden Spezifikationen. ALLER TEXT MUSS AUF DEUTSCH SEIN.

1. LEKTIONS-METADATEN (auf Deutsch):
   - Bestimme das angemessene Schwierigkeitsniveau (Anfänger, Mittelstufe oder Fortgeschritten)
   - Wähle die relevanteste Kategorie aus dieser Liste: {', '.join(available_categories)}
   - Erstelle umfassende Schlüsselwörter (10-15 relevante deutsche und japanische Begriffe)
   - Definiere kulturelle Schwerpunktbereiche (auf Deutsch)
   - Schreibe eine ansprechende Lektionsbeschreibung für Studenten (2-3 Sätze, auf Deutsch)

2. INHALTSSEITEN (Erstelle genau 7 Inhaltsseiten, auf Deutsch):
   - Jede Seite sollte ein spezifisches Thema/Schwerpunktbereich haben
   - Füge einen deutschen Titel hinzu, gefolgt vom japanischen Titel mit Romanisierung in Klammern. Beispiel: "Seite 1 - Begrüßungen (Aisatsu - あいさつ)"
   - Gib detaillierte Schlüsselwörter für jede Seite an (auf Deutsch und Japanisch)
   - Schreibe eine Beschreibung des Inhaltsschwerpunkts (was die Studenten lernen werden, auf Deutsch)
   - Erstelle ein detailliertes Bildkonzept für die KI-Bildgenerierung (Beschreibung auf Deutsch, Stil sollte sein: "Niedlicher Manga/Anime-Stil mit klaren Linien, kawaii-Ästhetik, hellen Farben und kultureller Authentizität. WICHTIG: Kein Text, keine Schrift, keine Schilder oder Zeichen sollten im Bild sichtbar sein.")

3. BILDUNGSSTRUKTUR:
   - Stelle eine logische Progression von grundlegenden zu fortgeschrittenen Konzepten sicher
   - Füge kulturellen Kontext und reale Anwendungen hinzu
   - Balanciere Vokabeln, Grammatik und kulturelles Verständnis, alles auf Deutsch erklärt

Gib NUR ein gültiges JSON-Objekt mit dieser exakten Struktur zurück (alle Werte auf Deutsch):
{{
  "lesson_title": "Vollständiger Lektionstitel auf Deutsch",
  "lesson_description": "Detaillierte Beschreibung für Studenten auf Deutsch",
  "difficulty": "Anfänger/Mittelstufe/Fortgeschritten",
  "category_name": "Gewählter Kategoriename auf Deutsch",
  "keywords": "kommagetrennte Schlüsselwörter auf Deutsch/Japanisch",
  "cultural_focus": "hauptsächliche kulturelle Aspekte auf Deutsch",
  "content_pages": [
    {{
      "title": "Seitentitel auf Deutsch - Japanischer Titel (Romanisierung - 日本語)",
      "keywords": "seitenspezifische Schlüsselwörter auf Deutsch/Japanisch",
      "content_focus": "was diese Seite lehrt, auf Deutsch",
      "image_concept": "detaillierte Bildbeschreibung für KI-Generierung, auf Deutsch, mit niedlichem Manga/Anime-Stil"
    }}
  ]
}}

Stelle sicher, dass die Lektion pädagogisch fundiert, kulturell authentisch und ansprechend für deutschsprachige Japanisch-Lernende ist.
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
            print(f"Generated structure with {len(lesson_structure.get('content_pages', []))} content pages")
            return lesson_structure
        else:
            print(f"Could not extract JSON from Gemini response")
            return None
            
    except Exception as e:
        print(f"Error generating lesson structure: {e}")
        return None

def generate_lesson_script(template_content, topic, lesson_structure):
    """Generate the lesson creation script using the template."""
    try:
        difficulty_int = convert_difficulty_to_int(lesson_structure['difficulty'])
        
        content_pages_start = template_content.find('CONTENT_PAGES = [')
        content_pages_end = template_content.find(']', content_pages_start) + 1
        
        if content_pages_start == -1 or content_pages_end == -1:
            print("Could not find CONTENT_PAGES in template")
            return None
        
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
            category_id=category.id if category else None,
            instruction_language='german'
        )
'''
        lesson_creation_pattern = r'# Create the lesson\n        lesson = Lesson\([\s\S]*?\)'
        new_script = re.sub(lesson_creation_pattern, category_logic, new_script, 1)
        

        # Add UTF-8 encoding fix for Windows console
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

        script_title = lesson_structure["lesson_title"]
        new_header = f'#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n"""\nThis script creates a comprehensive Japanese lesson titled \\"{script_title}\\" for German-speaking learners.\n"""'
        old_header_start = new_script.find('"""')
        old_header_end = new_script.find('"""', old_header_start + 3) + 3
        if old_header_start != -1 and old_header_end != -1:
            new_script = new_script[:old_header_start] + new_header + new_script[old_header_end:]
        
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
    print("Starting Google Gemini 2.5 Pro Japanese Lesson Script Generator (for German Speakers)")
    print("=" * 80)
    
    setup_logging(LOG_FILE)
    load_env()
    
    model = initialize_gemini(GEMINI_MODEL)
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
            print(f"Failed to generate structure for: {topic['title']}")
            failed_generations += 1
            continue
        
        script_content = generate_lesson_script(template_content, topic, lesson_structure)
        if not script_content:
            print(f"Failed to generate script for: {topic['title']}")
            failed_generations += 1
            continue
        
        filename = create_script_filename(lesson_structure['lesson_title'], LANGUAGE)
        if save_generated_script(script_content, filename):
            successful_generations += 1
        else:
            failed_generations += 1
        
        if i < len(topics):
            print("⏳ Waiting 2 seconds before next generation...")
            time.sleep(2)
    
    print("\n" + "=" * 80)
    print("JAPANESE LESSONS FOR GERMANS - GENERATION SUMMARY")
    print("=" * 80)
    print(f"Successfully generated: {successful_generations} scripts")
    print(f"Failed generations: {failed_generations}")
    print(f"Scripts saved to: {OUTPUT_DIR}/")
    print(f"Log saved to: {LOG_FILE}")
    
    if successful_generations > 0:
        print(f"\nGeneration complete! {successful_generations} Japanese lesson scripts for German speakers are ready.")
    else:
        print("\nNo scripts were generated successfully. Please check the errors above.")

if __name__ == "__main__":
    main()
