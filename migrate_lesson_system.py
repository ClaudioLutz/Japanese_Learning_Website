#!/usr/bin/env python3
"""
Database migration script to add lesson system tables to the existing Japanese Learning Website database.
This script adds the new lesson-related tables while preserving existing data.
"""

import os
import sys
from datetime import datetime

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import (
    User, Kana, Kanji, Vocabulary, Grammar,
    LessonCategory, Lesson, LessonPrerequisite, 
    LessonContent, UserLessonProgress
)

def migrate_database():
    """Add lesson system tables to the existing database"""
    app = create_app()
    
    with app.app_context():
        print("Starting lesson system database migration...")
        
        try:
            # Create all new tables
            print("Creating lesson system tables...")
            db.create_all()
            
            # Add some default lesson categories
            print("Adding default lesson categories...")
            default_categories = [
                {
                    'name': 'Hiragana Basics',
                    'description': 'Learn the fundamental Hiragana characters',
                    'color_code': '#FF6B6B'
                },
                {
                    'name': 'Katakana Basics', 
                    'description': 'Learn the fundamental Katakana characters',
                    'color_code': '#4ECDC4'
                },
                {
                    'name': 'Essential Kanji',
                    'description': 'Most important Kanji characters for beginners',
                    'color_code': '#45B7D1'
                },
                {
                    'name': 'Basic Vocabulary',
                    'description': 'Essential Japanese words and phrases',
                    'color_code': '#96CEB4'
                },
                {
                    'name': 'Grammar Fundamentals',
                    'description': 'Core Japanese grammar patterns',
                    'color_code': '#FFEAA7'
                },
                {
                    'name': 'JLPT N5',
                    'description': 'Beginner level Japanese proficiency content',
                    'color_code': '#DDA0DD'
                },
                {
                    'name': 'JLPT N4',
                    'description': 'Elementary level Japanese proficiency content',
                    'color_code': '#98D8C8'
                }
            ]
            
            for cat_data in default_categories:
                existing_category = LessonCategory.query.filter_by(name=cat_data['name']).first()
                if not existing_category:
                    category = LessonCategory(
                        name=cat_data['name'],
                        description=cat_data['description'],
                        color_code=cat_data['color_code']
                    )
                    db.session.add(category)
                    print(f"  Added category: {cat_data['name']}")
                else:
                    print(f"  Category already exists: {cat_data['name']}")
            
            # Create some sample lessons
            print("Creating sample lessons...")
            
            # Get categories for lesson creation
            hiragana_cat = LessonCategory.query.filter_by(name='Hiragana Basics').first()
            vocab_cat = LessonCategory.query.filter_by(name='Basic Vocabulary').first()
            
            sample_lessons = [
                {
                    'title': 'Introduction to Hiragana',
                    'description': 'Learn your first Hiragana characters: あ, い, う, え, お',
                    'lesson_type': 'free',
                    'category_id': hiragana_cat.id if hiragana_cat else None,
                    'difficulty_level': 1,
                    'estimated_duration': 15,
                    'order_index': 1,
                    'is_published': True
                },
                {
                    'title': 'Basic Greetings',
                    'description': 'Essential Japanese greetings and polite expressions',
                    'lesson_type': 'free',
                    'category_id': vocab_cat.id if vocab_cat else None,
                    'difficulty_level': 1,
                    'estimated_duration': 20,
                    'order_index': 1,
                    'is_published': True
                },
                {
                    'title': 'Advanced Hiragana Combinations',
                    'description': 'Complex Hiragana combinations and special characters',
                    'lesson_type': 'premium',
                    'category_id': hiragana_cat.id if hiragana_cat else None,
                    'difficulty_level': 3,
                    'estimated_duration': 30,
                    'order_index': 2,
                    'is_published': True
                }
            ]
            
            for lesson_data in sample_lessons:
                existing_lesson = Lesson.query.filter_by(title=lesson_data['title']).first()
                if not existing_lesson:
                    lesson = Lesson(**lesson_data)
                    db.session.add(lesson)
                    print(f"  Added lesson: {lesson_data['title']}")
                else:
                    print(f"  Lesson already exists: {lesson_data['title']}")
            
            # Commit all changes
            db.session.commit()
            print("✅ Lesson system migration completed successfully!")
            
            # Display summary
            print("\n📊 Migration Summary:")
            print(f"  Categories: {LessonCategory.query.count()}")
            print(f"  Lessons: {Lesson.query.count()}")
            print(f"  Users: {User.query.count()}")
            print(f"  Existing content items:")
            print(f"    Kana: {Kana.query.count()}")
            print(f"    Kanji: {Kanji.query.count()}")
            print(f"    Vocabulary: {Vocabulary.query.count()}")
            print(f"    Grammar: {Grammar.query.count()}")
            
        except Exception as e:
            print(f"❌ Migration failed: {str(e)}")
            db.session.rollback()
            raise
        
        print("\n🎉 Database is ready for the lesson system!")
        print("You can now:")
        print("  1. Access the admin panel to create lessons")
        print("  2. Add content to lessons")
        print("  3. Set up lesson prerequisites")
        print("  4. Users can start taking lessons")

def verify_migration():
    """Verify that the migration was successful"""
    app = create_app()
    
    with app.app_context():
        print("\n🔍 Verifying migration...")
        
        # Check if all tables exist
        tables_to_check = [
            'lesson_category',
            'lesson', 
            'lesson_prerequisite',
            'lesson_content',
            'user_lesson_progress'
        ]
        
        for table_name in tables_to_check:
            try:
                result = db.engine.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';")
                if result.fetchone():
                    print(f"  ✅ Table '{table_name}' exists")
                else:
                    print(f"  ❌ Table '{table_name}' missing")
            except Exception as e:
                print(f"  ❌ Error checking table '{table_name}': {e}")
        
        # Check relationships
        try:
            categories = LessonCategory.query.all()
            lessons = Lesson.query.all()
            print(f"  ✅ Found {len(categories)} categories and {len(lessons)} lessons")
            
            # Test a relationship
            if categories:
                cat_lessons = categories[0].lessons
                print(f"  ✅ Category relationships working")
                
        except Exception as e:
            print(f"  ❌ Relationship test failed: {e}")

if __name__ == '__main__':
    print("🚀 Japanese Learning Website - Lesson System Migration")
    print("=" * 60)
    
    try:
        migrate_database()
        verify_migration()
        
        print("\n" + "=" * 60)
        print("✅ Migration completed successfully!")
        print("You can now run the application with: python run.py")
        
    except Exception as e:
        print(f"\n❌ Migration failed with error: {e}")
        print("Please check the error and try again.")
        sys.exit(1)
