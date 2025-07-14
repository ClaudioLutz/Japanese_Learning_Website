# Code Examples for Enhanced Lesson Creation Scripts

## 1. Base Lesson Creator Class Implementation

### lesson_creator_base.py
```python
#!/usr/bin/env python3
"""
Base class for lesson creation scripts that eliminates code duplication
and provides a standardized lesson creation workflow.
"""
import os
import sys
from dotenv import load_dotenv
from datetime import datetime

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Load environment variables
load_dotenv()

from app import create_app, db
from app.models import Lesson, LessonPage, LessonContent, QuizQuestion, QuizOption, LessonCategory
from app.ai_services import AILessonContentGenerator

class BaseLessonCreator:
    """Base class for creating lessons with AI-generated content."""
    
    def __init__(self, title, difficulty, lesson_type="free", language="english", category_name=None):
        self.title = title
        self.difficulty = difficulty
        self.lesson_type = lesson_type
        self.language = language
        self.category_name = category_name
        self.pages = []
        self.generator = None
        self.app = None
        
    def add_page(self, title, content_list, description=None):
        """Add a page with content to the lesson."""
        page_number = len(self.pages) + 1
        self.pages.append({
            "page_number": page_number,
            "title": title,
            "description": description or f"This page covers: {title}",
            "content": content_list
        })
        
    def add_content_to_page(self, page_number, content_item):
        """Add content to an existing page."""
        if page_number <= len(self.pages):
            self.pages[page_number - 1]["content"].append(content_item)
        else:
            raise ValueError(f"Page {page_number} does not exist")
    
    def initialize_ai_generator(self):
        """Initialize the AI content generator."""
        self.generator = AILessonContentGenerator()
        if not self.generator.client:
            raise RuntimeError("AI Generator could not be initialized. Check your API key.")
    
    def find_or_create_category(self):
        """Find existing category or create new one."""
        if not self.category_name:
            return None
            
        category = LessonCategory.query.filter_by(name=self.category_name).first()
        if not category:
            category = LessonCategory(
                name=self.category_name,
                description=f"Lessons related to {self.category_name}"
            )
            db.session.add(category)
            db.session.flush()
        return category
    
    def delete_existing_lesson(self):
        """Delete existing lesson with the same title."""
        existing_lesson = Lesson.query.filter_by(title=self.title).first()
        if existing_lesson:
            print(f"Found existing lesson '{self.title}' (ID: {existing_lesson.id}). Deleting it.")
            db.session.delete(existing_lesson)
            db.session.commit()
            print("✅ Existing lesson deleted.")
    
    def create_lesson_record(self):
        """Create the main lesson database record."""
        category = self.find_or_create_category()
        
        lesson = Lesson(
            title=self.title,
            description=f"AI-generated lesson: {self.title}",
            lesson_type=self.lesson_type,
            difficulty_level=self._get_difficulty_level(),
            is_published=True,
            instruction_language=self.language,
            category_id=category.id if category else None
        )
        
        db.session.add(lesson)
        db.session.commit()
        print(f"✅ Lesson '{self.title}' created with ID: {lesson.id}")
        return lesson
    
    def _get_difficulty_level(self):
        """Convert difficulty string to numeric level."""
        difficulty_map = {
            "absolute_beginner": 1,
            "beginner": 2,
            "intermediate": 3,
            "advanced": 4,
            "expert": 5
        }
        return difficulty_map.get(self.difficulty.lower().replace(" ", "_"), 2)
    
    def create_pages_and_content(self, lesson):
        """Create all pages and their content."""
        for page_info in self.pages:
            print(f"\n--- Creating Page {page_info['page_number']}: {page_info['title']} ---")
            
            # Create lesson page metadata
            lesson_page = LessonPage(
                lesson_id=lesson.id,
                page_number=page_info['page_number'],
                title=page_info['title'],
                description=page_info['description']
            )
            db.session.add(lesson_page)
            
            # Create content for this page
            order_index = 0
            for content_info in page_info['content']:
                self.create_content_item(lesson, page_info['page_number'], content_info, order_index)
                order_index += 1
    
    def create_content_item(self, lesson, page_number, content_info, order_index):
        """Create a single content item."""
        content_type = content_info['type']
        
        print(f"🤖 Generating {content_type} for '{content_info.get('topic', 'content')[:60]}...'")
        
        if content_type == 'formatted_explanation':
            self.create_explanation_content(lesson, page_number, content_info, order_index)
        elif content_type in ['multiple_choice', 'true_false', 'fill_in_the_blank', 'matching']:
            self.create_quiz_content(lesson, page_number, content_info, order_index)
        elif content_type in ['kana', 'kanji', 'vocabulary', 'grammar']:
            self.create_reference_content(lesson, page_number, content_info, order_index)
        else:
            print(f"❌ Unknown content type: {content_type}")
    
    def create_explanation_content(self, lesson, page_number, content_info, order_index):
        """Create explanation content using AI."""
        result = self.generator.generate_formatted_explanation(
            content_info['topic'], 
            self.difficulty, 
            content_info['keywords']
        )
        
        if "error" in result:
            print(f"❌ Error generating explanation: {result['error']}")
            return
        
        content = LessonContent(
            lesson_id=lesson.id,
            page_number=page_number,
            content_type="text",
            title=content_info.get('title', f"Explanation: {content_info['topic'][:30]}..."),
            content_text=result['generated_text'],
            order_index=order_index,
            generated_by_ai=True,
            ai_generation_details={
                "model": "gpt-4o",
                "topic": content_info['topic'],
                "difficulty": self.difficulty,
                "keywords": content_info['keywords']
            }
        )
        db.session.add(content)
        print("✅ Explanation content added.")
    
    def create_quiz_content(self, lesson, page_number, content_info, order_index):
        """Create quiz content using AI."""
        content_type = content_info['type']
        
        # Generate quiz content based on type
        if content_type == 'multiple_choice':
            result = self.generator.generate_multiple_choice_question(
                content_info['topic'], self.difficulty, content_info['keywords']
            )
        elif content_type == 'true_false':
            result = self.generator.generate_true_false_question(
                content_info['topic'], self.difficulty, content_info['keywords']
            )
        elif content_type == 'fill_in_the_blank':
            result = self.generator.generate_fill_in_the_blank_question(
                content_info['topic'], self.difficulty, content_info['keywords']
            )
        elif content_type == 'matching':
            result = self.generator.generate_matching_question(
                content_info['topic'], self.difficulty, content_info['keywords']
            )
        else:
            print(f"❌ Unsupported quiz type: {content_type}")
            return
        
        if "error" in result:
            print(f"❌ Error generating {content_type}: {result['error']}")
            return
        
        # Create quiz content record
        quiz_content = LessonContent(
            lesson_id=lesson.id,
            page_number=page_number,
            content_type="interactive",
            title=f"Quiz: {result.get('question_text', content_info['topic'])[:40]}...",
            is_interactive=True,
            order_index=order_index,
            max_attempts=content_info.get('max_attempts', 3),
            passing_score=content_info.get('passing_score', 70),
            generated_by_ai=True,
            ai_generation_details={
                "model": "gpt-4o",
                "type": content_type,
                "topic": content_info['topic'],
                "difficulty": self.difficulty,
                "keywords": content_info['keywords']
            }
        )
        db.session.add(quiz_content)
        db.session.flush()
        
        # Create quiz question and options
        self.create_quiz_question(quiz_content.id, content_type, result)
        print(f"✅ {content_type.replace('_', ' ').title()} quiz added.")
    
    def create_quiz_question(self, content_id, question_type, result):
        """Create quiz question and options."""
        question = QuizQuestion(
            lesson_content_id=content_id,
            question_type=question_type,
            question_text=result['question_text'],
            explanation=result.get('explanation', result.get('overall_explanation', ''))
        )
        db.session.add(question)
        db.session.flush()
        
        # Create options based on question type
        if question_type == 'multiple_choice':
            for option_data in result['options']:
                option = QuizOption(
                    question_id=question.id,
                    option_text=option_data['text'],
                    is_correct=option_data['is_correct'],
                    feedback=option_data.get('feedback', '')
                )
                db.session.add(option)
        
        elif question_type == 'true_false':
            db.session.add(QuizOption(
                question_id=question.id, 
                option_text="True", 
                is_correct=result['is_true']
            ))
            db.session.add(QuizOption(
                question_id=question.id, 
                option_text="False", 
                is_correct=not result['is_true']
            ))
        
        elif question_type == 'fill_in_the_blank':
            db.session.add(QuizOption(
                question_id=question.id,
                option_text=result['correct_answer'],
                is_correct=True
            ))
        
        elif question_type == 'matching':
            for pair in result['pairs']:
                db.session.add(QuizOption(
                    question_id=question.id,
                    option_text=pair['prompt'],
                    feedback=pair['answer'],
                    is_correct=True
                ))
    
    def create_reference_content(self, lesson, page_number, content_info, order_index):
        """Create content that references existing database entries."""
        content = LessonContent(
            lesson_id=lesson.id,
            page_number=page_number,
            content_type=content_info['type'],
            content_id=content_info['content_id'],
            title=content_info.get('title', f"{content_info['type'].title()} Reference"),
            order_index=order_index
        )
        db.session.add(content)
        print(f"✅ {content_info['type'].title()} reference content added.")
    
    def create_lesson(self):
        """Main method to create the complete lesson."""
        if not self.pages:
            raise ValueError("No pages defined. Add pages before creating lesson.")
        
        self.app = create_app()
        
        with self.app.app_context():
            print(f"--- Creating Lesson: {self.title} ---")
            print(f"Total pages to create: {len(self.pages)}")
            
            # Initialize AI generator
            self.initialize_ai_generator()
            
            # Delete existing lesson
            self.delete_existing_lesson()
            
            # Create lesson record
            lesson = self.create_lesson_record()
            
            # Create pages and content
            self.create_pages_and_content(lesson)
            
            # Commit all changes
            db.session.commit()
            
            print(f"\n--- Lesson Creation Complete! ---")
            print(f"Created lesson '{self.title}' with {len(self.pages)} pages")
            
            return lesson

# Utility function for easy script creation
def create_lesson_script(title, difficulty, pages_config, **kwargs):
    """Utility function to create a lesson from configuration."""
    creator = BaseLessonCreator(title, difficulty, **kwargs)
    
    for page_config in pages_config:
        creator.add_page(
            page_config['title'],
            page_config['content'],
            page_config.get('description')
        )
    
    return creator.create_lesson()
```

## 2. Database-Aware Content Script

### create_jlpt_lesson_database_aware.py
```python
#!/usr/bin/env python3
"""
Creates a JLPT N5 lesson by referencing existing vocabulary, kanji, and grammar
from the database, and then generates new quiz content.
"""
from lesson_creator_base import DatabaseAwareLessonCreator

class JLPTExtendedLessonCreator(DatabaseAwareLessonCreator):
    """
    Creates a comprehensive JLPT lesson by finding existing content
    and generating new explanations and quizzes.
    """
    
    def create_lesson_from_db(self, jlpt_level, topic, content_limit=5):
        """
        Creates a full lesson from existing DB content.
        """
        # Find existing content
        vocabulary = self.find_vocabulary_by_topic(jlpt_level, topic, limit=content_limit)
        kanji = self.find_kanji_by_topic(jlpt_level, topic, limit=content_limit)
        grammar = self.find_grammar_by_topic(jlpt_level, topic, limit=content_limit)
        
        if not any([vocabulary, kanji, grammar]):
            print(f"No content found for JLPT N{jlpt_level} on topic '{topic}'.")
            return

        # 1. Introduction Page
        self.add_page("Lesson Introduction", [
            self.generate_ai_explanation(
                f"Introduction to JLPT N{jlpt_level} {topic.title()}",
                f"Overview of vocabulary, kanji, and grammar for {topic} at the JLPT N{jlpt_level} level."
            )
        ])
        
        # 2. Add content pages
        if vocabulary:
            self.add_content_reference_page("Vocabulary", vocabulary)
        if kanji:
            self.add_content_reference_page("Kanji", kanji)
        if grammar:
            self.add_content_reference_page("Grammar", grammar)
            
        # 3. Add practice quizzes
        self.add_practice_page("Practice", vocabulary, kanji, grammar)
        
        # 4. Create the lesson
        return self.create_lesson()

def main():
    """Main function to create the lesson."""
    creator = JLPTExtendedLessonCreator(
        title="JLPT N5 Essentials: Daily Life",
        difficulty="Beginner",
        category_name="JLPT N5",
        language="English"
    )
    creator.create_lesson_from_db(jlpt_level=5, topic="daily life", content_limit=5)

if __name__ == "__main__":
    main()
```

## 3. Multimedia Lesson Creation

### create_comprehensive_multimedia_lesson.py
```python
#!/usr/bin/env python3
"""
Creates a comprehensive, multimedia-rich lesson on a specified topic
using the MultimediaLessonCreator.
"""
from multimedia_lesson_creator import MultimediaLessonCreator

def create_multimedia_lesson():
    """
    Defines and creates a multimedia lesson on 'Japanese Greetings'.
    """
    creator = MultimediaLessonCreator(
        title="Japanese Greetings for Beginners",
        difficulty="Beginner",
        category_name="Conversational Japanese",
        language="English"
    )

    # Page 1: Introduction to Greetings
    creator.add_page("Introduction to Greetings", [
        creator.generate_ai_explanation(
            "Why Greetings are Important in Japan",
            "Cultural significance of greetings, bowing, and politeness levels."
        ),
        creator.generate_ai_image(
            "A friendly meeting in Japan with people bowing respectfully.",
            "Visual representation of Japanese greeting culture."
        )
    ])

    # Page 2: Common Morning Greetings
    creator.add_page("Morning Greetings", [
        creator.generate_ai_explanation(
            "Common Japanese Morning Greetings",
            "おはようございます (Ohayō gozaimasu), おはよう (Ohayō)"
        ),
        creator.generate_ai_audio(
            "おはようございます",
            "Pronunciation of 'Ohayō gozaimasu'."
        ),
        creator.generate_ai_quiz('multiple_choice', 
            "What is the formal morning greeting in Japanese?",
            "Ohayō gozaimasu, Konnichiwa, Sayōnara"
        )
    ])
    
    # ... (additional pages for afternoon, evening, etc.)

    # Create the full lesson
    creator.create_lesson()

if __name__ == "__main__":
    create_multimedia_lesson()
```
