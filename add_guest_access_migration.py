#!/usr/bin/env python3
"""
Migration script to add allow_guest_access field to Lesson table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Lesson
from sqlalchemy import text

def add_guest_access_field():
    """Add allow_guest_access field to Lesson table"""
    app = create_app()
    
    with app.app_context():
        try:
            # Check if column already exists
            result = db.session.execute(text("""
                SELECT COUNT(*) as count 
                FROM pragma_table_info('lesson') 
                WHERE name = 'allow_guest_access'
            """)).fetchone()
            
            if result.count > 0:
                print("Column 'allow_guest_access' already exists in lesson table.")
                return
            
            # Add the new column
            print("Adding 'allow_guest_access' column to lesson table...")
            db.session.execute(text("""
                ALTER TABLE lesson 
                ADD COLUMN allow_guest_access BOOLEAN DEFAULT 0 NOT NULL
            """))
            
            # Set some lessons to allow guest access (first 3 free lessons)
            print("Setting guest access for first 3 free lessons...")
            free_lessons = Lesson.query.filter_by(lesson_type='free').order_by(Lesson.order_index).limit(3).all()
            
            for lesson in free_lessons:
                lesson.allow_guest_access = True
                print(f"  - Enabled guest access for lesson: {lesson.title}")
            
            db.session.commit()
            print("Migration completed successfully!")
            print(f"Guest access enabled for {len(free_lessons)} lessons.")
            
        except Exception as e:
            db.session.rollback()
            print(f"Migration failed: {e}")
            raise

if __name__ == "__main__":
    add_guest_access_field()
