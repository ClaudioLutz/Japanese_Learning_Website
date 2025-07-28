#!/usr/bin/env python3
"""
This script extracts all lesson topics from the database to see what lessons are available
for creating courses.
"""
import os
import sys

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
from app.models import Lesson

def extract_lesson_topics():
    """Extract all lesson topics from the database."""
    app = create_app()
    
    with app.app_context():
        print("--- Extracting Lesson Topics from Database ---")
        
        # Get all lessons
        all_lessons = Lesson.query.all()
        
        print(f"Total lessons found: {len(all_lessons)}")
        print()
        
        # Group by instruction language
        german_lessons = []
        english_lessons = []
        other_lessons = []
        
        for lesson in all_lessons:
            if lesson.instruction_language == 'german':
                german_lessons.append(lesson)
            elif lesson.instruction_language == 'english':
                english_lessons.append(lesson)
            else:
                other_lessons.append(lesson)
        
        print(f"=== GERMAN LESSONS ({len(german_lessons)}) ===")
        for i, lesson in enumerate(german_lessons, 1):
            status = "✅ Published" if lesson.is_published else "❌ Unpublished"
            difficulty = f"Level {lesson.difficulty_level}" if lesson.difficulty_level else "No level"
            print(f"{i:2d}. {lesson.title}")
            print(f"    ID: {lesson.id} | {status} | {difficulty}")
            if lesson.description:
                print(f"    Description: {lesson.description[:100]}...")
            print()
        
        print(f"=== ENGLISH LESSONS ({len(english_lessons)}) ===")
        for i, lesson in enumerate(english_lessons, 1):
            status = "✅ Published" if lesson.is_published else "❌ Unpublished"
            difficulty = f"Level {lesson.difficulty_level}" if lesson.difficulty_level else "No level"
            print(f"{i:2d}. {lesson.title}")
            print(f"    ID: {lesson.id} | {status} | {difficulty}")
            if lesson.description:
                print(f"    Description: {lesson.description[:100]}...")
            print()
        
        if other_lessons:
            print(f"=== OTHER LESSONS ({len(other_lessons)}) ===")
            for i, lesson in enumerate(other_lessons, 1):
                status = "✅ Published" if lesson.is_published else "❌ Unpublished"
                difficulty = f"Level {lesson.difficulty_level}" if lesson.difficulty_level else "No level"
                lang = lesson.instruction_language or "Unknown"
                print(f"{i:2d}. {lesson.title}")
                print(f"    ID: {lesson.id} | {status} | {difficulty} | Language: {lang}")
                if lesson.description:
                    print(f"    Description: {lesson.description[:100]}...")
                print()
        
        print("--- Summary ---")
        print(f"German lessons: {len(german_lessons)}")
        print(f"English lessons: {len(english_lessons)}")
        print(f"Other lessons: {len(other_lessons)}")
        print(f"Total lessons: {len(all_lessons)}")

if __name__ == "__main__":
    extract_lesson_topics()
