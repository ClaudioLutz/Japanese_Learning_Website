#!/usr/bin/env python3
"""
This script creates 2 courses with 4 lessons each:
1. German-Japanese Course (instruction_language='german')
2. English-Japanese Course (instruction_language='english')

It selects existing lessons from the database and organizes them into courses.
"""
import os
import sys
from datetime import datetime

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
from app.models import Course, Lesson

def create_courses():
    """Create courses from existing lessons."""
    app = create_app()
    
    with app.app_context():
        print("--- Creating Courses from Existing Lessons ---")
        
        # Get existing lessons by instruction language
        german_lessons = Lesson.query.filter_by(instruction_language='german', is_published=True).order_by(Lesson.id).all()
        english_lessons = Lesson.query.filter_by(instruction_language='english', is_published=True).order_by(Lesson.id).all()
        
        print(f"Found {len(german_lessons)} German lessons")
        print(f"Found {len(english_lessons)} English lessons")
        
        # Create German-Japanese Course
        if len(german_lessons) >= 4:
            # Check if course already exists
            existing_german_course = Course.query.filter_by(title="Japanisch für Deutsche - Grundkurs").first()
            if existing_german_course:
                print(f"German course already exists (ID: {existing_german_course.id}). Deleting it.")
                db.session.delete(existing_german_course)
                db.session.commit()
            
            german_course = Course(
                title="Japanisch für Deutsche - Grundkurs",
                description="Ein umfassender Grundkurs für deutschsprachige Lernende, die Japanisch lernen möchten. Dieser Kurs deckt wichtige Aspekte der japanischen Sprache und Kultur ab, von grundlegenden Ausdrücken bis hin zu alltäglichen Situationen.",
                is_published=True,
                created_at=datetime.utcnow()
            )
            db.session.add(german_course)
            db.session.flush()
            
            # Select 4 diverse German lessons for the course
            selected_german_lessons = [
                # Lesson 1: Basic greetings and introductions
                next((l for l in german_lessons if "Begrüßung" in l.title), german_lessons[0]),
                # Lesson 2: Family structure and relationships  
                next((l for l in german_lessons if "Familie" in l.title), german_lessons[1]),
                # Lesson 3: Shopping and daily activities
                next((l for l in german_lessons if "Einkaufen" in l.title), german_lessons[2]),
                # Lesson 4: Food culture and dining
                next((l for l in german_lessons if "Esskultur" in l.title), german_lessons[3])
            ]
            
            for lesson in selected_german_lessons:
                german_course.lessons.append(lesson)
            
            db.session.commit()
            
            print(f"✅ Created German-Japanese course with lessons:")
            for i, lesson in enumerate(selected_german_lessons, 1):
                print(f"   {i}. {lesson.title} (ID: {lesson.id})")
        else:
            print(f"❌ Not enough German lessons found ({len(german_lessons)} < 4)")
        
        # Create English-Japanese Course
        if len(english_lessons) >= 4:
            # Check if course already exists
            existing_english_course = Course.query.filter_by(title="Japanese for English Speakers - Foundation Course").first()
            if existing_english_course:
                print(f"English course already exists (ID: {existing_english_course.id}). Deleting it.")
                db.session.delete(existing_english_course)
                db.session.commit()
            
            english_course = Course(
                title="Japanese for English Speakers - Foundation Course",
                description="A comprehensive foundation course for English speakers learning Japanese. This course covers essential aspects of Japanese language and culture, from basic expressions to everyday situations and cultural understanding.",
                is_published=True,
                created_at=datetime.utcnow()
            )
            db.session.add(english_course)
            db.session.flush()
            
            # Select 4 diverse English lessons for the course
            selected_english_lessons = [
                # Lesson 1: Daily routines and basic activities
                next((l for l in english_lessons if "Daily" in l.title), english_lessons[0]),
                # Lesson 2: Japanese particles (grammar foundation)
                next((l for l in english_lessons if "Particles" in l.title), english_lessons[1]),
                # Lesson 3: Food culture and dining
                next((l for l in english_lessons if "Cuisine" in l.title or "Food" in l.title), english_lessons[2]),
                # Lesson 4: Transportation and travel
                next((l for l in english_lessons if "Transport" in l.title or "Travel" in l.title), english_lessons[3])
            ]
            
            for lesson in selected_english_lessons:
                english_course.lessons.append(lesson)
            
            db.session.commit()
            
            print(f"✅ Created English-Japanese course with lessons:")
            for i, lesson in enumerate(selected_english_lessons, 1):
                print(f"   {i}. {lesson.title} (ID: {lesson.id})")
        else:
            print(f"❌ Not enough English lessons found ({len(english_lessons)} < 4)")
        
        print("\n--- Course Creation Summary ---")
        
        # Display final course information
        all_courses = Course.query.filter_by(is_published=True).all()
        print(f"Total published courses: {len(all_courses)}")
        
        for course in all_courses:
            print(f"\n📚 Course: {course.title}")
            print(f"   Description: {course.description[:100]}...")
            print(f"   Lessons ({len(course.lessons)}):")
            for i, lesson in enumerate(course.lessons, 1):
                print(f"     {i}. {lesson.title}")

if __name__ == "__main__":
    create_courses()
