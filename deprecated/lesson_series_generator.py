import os
import sys
import json
from datetime import datetime

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from app import create_app, db
from app.models import Lesson, LessonPrerequisite, LessonCategory
from lesson_creator_base import LessonCreatorBase

class LessonSeriesGenerator:
    """
    Generates a series of interconnected lessons from a configuration file.
    """
    def __init__(self, config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        self.app = create_app()

    def create_series(self):
        """
        Creates the entire lesson series based on the loaded configuration.
        """
        with self.app.app_context():
            print(f"Starting lesson series generation for: {self.config.get('series_title')}")

            # 1. Get or create the category
            category_name = self.config.get('category', 'Uncategorized')
            category = LessonCategory.query.filter_by(name=category_name).first()
            if not category:
                category = LessonCategory(name=category_name, description=self.config.get('category_description', ''))
                db.session.add(category)
                db.session.commit()
                print(f"Created new category: {category_name}")

            # 2. Create each lesson in the series
            created_lessons = {}  # To store created lesson objects for prerequisite mapping
            for i, lesson_config in enumerate(self.config.get('lessons', [])):
                print(f"Creating lesson {i+1}: {lesson_config.get('title')}")

                # Use a base lesson creator or a more specific one if needed
                creator = LessonCreatorBase(
                    title=lesson_config.get('title'),
                    description=lesson_config.get('description'),
                    lesson_type=lesson_config.get('lesson_type', 'free'),
                    difficulty_level=lesson_config.get('difficulty_level', 1),
                    category_id=category.id
                )

                # Add pages and content from the config
                for page_config in lesson_config.get('pages', []):
                    creator.add_page(
                        title=page_config.get('title'),
                        content_list=page_config.get('content', [])
                    )
                
                lesson = creator.create_lesson()
                created_lessons[lesson_config.get('id')] = lesson
                print(f"  - Lesson '{lesson.title}' created with ID {lesson.id}")

            # 3. Set up prerequisites
            print("\nSetting up prerequisites...")
            for lesson_config in self.config.get('lessons', []):
                lesson_id_str = lesson_config.get('id')
                current_lesson = created_lessons.get(lesson_id_str)
                if not current_lesson:
                    continue

                for prereq_id_str in lesson_config.get('prerequisites', []):
                    prereq_lesson = created_lessons.get(prereq_id_str)
                    if prereq_lesson:
                        prerequisite = LessonPrerequisite(
                            lesson_id=current_lesson.id,
                            prerequisite_lesson_id=prereq_lesson.id
                        )
                        db.session.add(prerequisite)
                        print(f"  - '{current_lesson.title}' now requires '{prereq_lesson.title}'")
            
            db.session.commit()
            print("\nLesson series generation complete!")

if __name__ == '__main__':
    # Example usage:
    # Create a sample config file first, then run this script.
    # The config file should be in the same directory as this script.
    
    # Create a sample config for a JLPT N5 series
    jlpt_n5_config = {
        "series_title": "JLPT N5 Prep Series",
        "category": "JLPT N5",
        "category_description": "A complete series to prepare for the JLPT N5 exam.",
        "lessons": [
            {
                "id": "n5_1_hiragana",
                "title": "N5 Hiragana Mastery",
                "description": "Learn all the Hiragana characters.",
                "difficulty_level": 1,
                "pages": [
                    {"title": "Introduction", "content": [{"type": "text", "text": "Let's learn Hiragana!"}]}
                ]
            },
            {
                "id": "n5_2_katakana",
                "title": "N5 Katakana Mastery",
                "description": "Learn all the Katakana characters.",
                "difficulty_level": 1,
                "prerequisites": ["n5_1_hiragana"],
                "pages": [
                    {"title": "Introduction", "content": [{"type": "text", "text": "Let's learn Katakana!"}]}
                ]
            },
            {
                "id": "n5_3_basic_grammar",
                "title": "N5 Basic Grammar",
                "description": "Introduction to fundamental Japanese grammar.",
                "difficulty_level": 2,
                "prerequisites": ["n5_1_hiragana", "n5_2_katakana"],
                "pages": [
                    {"title": "Particles", "content": [{"type": "text", "text": "Grammar about particles..."}]}
                ]
            }
        ]
    }

    config_filename = 'jlpt_n5_series_config.json'
    with open(config_filename, 'w', encoding='utf-8') as f:
        json.dump(jlpt_n5_config, f, indent=2, ensure_ascii=False)
    
    print(f"Created sample config file: {config_filename}")

    # Now, generate the series
    series_generator = LessonSeriesGenerator(config_filename)
    series_generator.create_series()
