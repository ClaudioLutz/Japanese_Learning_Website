# AI Lesson Creation Template

This document provides a comprehensive template and guide for creating AI-powered lesson generation scripts similar to `create_japanese_cuisine_lesson.py`. Use this template to create lessons for any topic, number of pages, and difficulty level.

## Overview

The lesson creation system follows a specific pedagogical structure:
1. **Page 1**: Introduction with overview image and welcoming text
2. **Pages 2-N**: Individual sub-topic pages with images, content, and varied quizzes
3. **Final Page**: Conclusion and comprehensive adaptive quiz

## Template Configuration

### 1. Basic Lesson Configuration

```python
# --- Configuration ---
LESSON_TITLE = "Your Lesson Title Here"
LESSON_DIFFICULTY = "Beginner|Intermediate|Advanced"
LESSON_DESCRIPTION = "Comprehensive description of what the lesson covers and learning objectives."

# Lesson pages configuration
LESSON_PAGES = [
    {
        "page_number": 1,
        "title": "Sub-topic 1 Title",
        "keywords": "keyword1, keyword2, keyword3, related terms",
        "image_concept": "Detailed description for AI image generation. Style: cute manga/anime art style clean lines, and cultural authenticity. IMPORTANT: No text, writing, signs, or characters should be visible in the image."
    },
    {
        "page_number": 2,
        "title": "Sub-topic 2 Title", 
        "keywords": "keyword1, keyword2, keyword3, related terms",
        "image_concept": "Another detailed image description..."
    },
    # Add more pages as needed
]
```

### 2. Customization Guidelines

#### Lesson Title
- Should be descriptive and indicate the target audience level
- Examples: "Beginner's Guide to...", "Advanced Techniques in...", "Complete Introduction to..."

#### Difficulty Levels
- **Beginner**: Basic concepts, simple vocabulary, fundamental principles
- **Intermediate**: More complex topics, cultural context, practical applications  
- **Advanced**: Nuanced understanding, specialized terminology, expert-level content

#### Keywords Selection
- Include 6-10 relevant terms per page
- Mix of basic and specific vocabulary
- Include both English and Japanese terms (for Japanese lessons)
- Consider synonyms and related concepts

#### Image Concepts
- Be specific about visual elements, composition, and style
- Always include: "IMPORTANT: No text, writing, signs, or characters should be visible in the image"
- Describe lighting, atmosphere, and cultural authenticity
- Focus on educational value and visual appeal

## Script Structure Template

### 1. File Header and Imports

```python
#!/usr/bin/env python3
"""
This script creates a comprehensive [TOPIC] lesson organized into pages.
Each page covers a different [SUB-TOPIC] with impressive images, cultural explanations, and varied quizzes.
Based on the configuration provided for [DIFFICULTY]-level [TOPIC] learning.
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
```

### 2. Image Download Function

```python
def download_image_simple(image_url, lesson_id, app, page_number):
    """Simple image download without complex validation."""
    try:
        print(f"  Downloading image from: {image_url}")
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        filename = f"[topic]_page_{page_number}_{timestamp}_{unique_id}.png"
        
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
```

### 3. Main Lesson Creation Function

```python
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
        # [Introduction page creation code - see full template]

        # Process each sub-topic page (Pages 2 through N)
        # [Sub-topic pages creation code - see full template]

        # Create Final Page: Comprehensive Final Quiz
        # [Final page creation code - see full template]

        db.session.commit()
        print(f"\n--- {LESSON_TITLE} Creation Complete! ---")
```

## Quiz Types and Variety

The system supports three quiz types that cycle through each page:

### 1. Multiple Choice Questions
- 4 options with detailed feedback
- Strategic romanization in answer choices
- Varied question approaches (meaning, usage, context)

### 2. True/False Questions
- Clear statements with explanations
- Cultural or factual knowledge testing
- Romanization in explanations

### 3. Matching Questions
- Japanese terms with English meanings
- Cultural concepts with descriptions
- Vocabulary with definitions

## Content Generation Prompts

### Text Content
```python
overview_topic = f"Comprehensive cultural and technical overview of {page_title}. Include history, preparation methods, cultural significance, regional variations, and dining etiquette. Use the keywords: {keywords}"
```

### Quiz Questions
The system automatically generates varied quiz questions using:
- Different question types (multiple choice, true/false, matching)
- Strategic romanization (context words vs. tested terms)
- Cultural and practical knowledge testing

## Customization Examples

### Language Learning Lessons
```python
LESSON_PAGES = [
    {
        "page_number": 1,
        "title": "Basic Greetings (挨拶)",
        "keywords": "ohayo, konnichiwa, konbanwa, arigatou, sumimasen, hajimemashite",
        "image_concept": "People bowing and greeting each other in various Japanese settings - office, street, home. Show different times of day and social contexts. Traditional and modern clothing mix."
    }
]
```

### Cultural Topics
```python
LESSON_PAGES = [
    {
        "page_number": 1,
        "title": "Tea Ceremony Basics",
        "keywords": "chanoyu, matcha, tatami, kimono, wa, omotenashi, seasonal awareness",
        "image_concept": "Elegant tea ceremony setup with traditional utensils, tatami mats, and a person in kimono performing the ceremony. Peaceful, meditative atmosphere with natural lighting."
    }
]
```

### Technical Subjects
```python
LESSON_PAGES = [
    {
        "page_number": 1,
        "title": "Origami Fundamentals",
        "keywords": "kami, ori, valley fold, mountain fold, crane, precision, patience",
        "image_concept": "Hands folding colorful origami paper with various completed models (crane, flower, box) displayed nearby. Clean, well-lit workspace showing the precision and artistry."
    }
]
```

## Best Practices

### Content Quality
1. **Comprehensive Coverage**: Each page should thoroughly cover its sub-topic
2. **Cultural Context**: Include historical background and cultural significance
3. **Progressive Difficulty**: Build complexity throughout the lesson
4. **Practical Application**: Include real-world usage and examples

### Image Generation
1. **Specific Descriptions**: Detailed visual concepts work better than vague descriptions
2. **Cultural Authenticity**: Emphasize accuracy and respectful representation
3. **Educational Value**: Images should support and enhance learning
4. **No Text Rule**: Always specify no text/writing in images

### Quiz Design
1. **Varied Types**: Use all three quiz types for engagement
2. **Strategic Romanization**: Help learners without giving away answers
3. **Cultural Knowledge**: Test understanding, not just memorization
4. **Appropriate Difficulty**: Match quiz complexity to lesson level

## File Naming Convention

Name your lesson creation scripts descriptively:
- `create_[topic]_lesson.py`
- Examples: `create_japanese_tea_ceremony_lesson.py`, `create_business_japanese_lesson.py`

## Running Your Lesson Script

1. Ensure OpenAI API key is set in `.env` file
2. Run the script: `python create_your_lesson.py`
3. Monitor console output for progress and any errors
4. Check the web interface to verify lesson creation

## Troubleshooting

### Common Issues
1. **API Key Missing**: Ensure `OPENAI_API_KEY` is in your `.env` file
2. **Image Download Failures**: Check internet connection and API limits
3. **Database Errors**: Verify database is accessible and models are up to date
4. **Quiz Generation Issues**: Check that keywords are relevant and specific

### Performance Tips
1. **Batch Processing**: The script processes pages sequentially for reliability
2. **Error Handling**: Built-in error handling continues processing if individual items fail
3. **Progress Monitoring**: Console output shows detailed progress for debugging

## Advanced Customization

### Custom Quiz Types
You can modify the quiz generation to focus on specific types:

```python
# Focus on specific quiz types
quiz_types = [
    ("multiple_choice", "Multiple Choice"),
    ("matching", "Matching"),
    ("matching", "Matching")  # More matching questions
]
```

### Specialized Content
For specialized topics, customize the content generation prompts:

```python
overview_topic = f"Technical analysis of {page_title} including scientific principles, practical applications, and industry standards. Use technical terminology: {keywords}"
```

### Different Lesson Structures
Modify the page structure for different educational approaches:
- More pages with focused content
- Fewer pages with comprehensive coverage
- Mixed media approaches
- Assessment-heavy vs. content-heavy lessons

This template provides a complete framework for creating engaging, comprehensive AI-generated lessons for any topic while maintaining educational quality and cultural sensitivity.
