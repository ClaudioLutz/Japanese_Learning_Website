#!/usr/bin/env python3
"""
Migration script to add language field to lessons table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Lesson
from sqlalchemy import text

def add_language_field():
    """Add language field to lessons table"""
    app = create_app()
    
    with app.app_context():
        try:
            # Check if column already exists
            with db.engine.connect() as connection:
                result = connection.execute(text("PRAGMA table_info(lesson)"))
                columns = [row[1] for row in result]
                
                if 'language' in columns:
                    print("Language column already exists in lesson table")
                    return
                
                print("Adding language column to lesson table...")
                
                # Add the language column with default value
                connection.execute(text("ALTER TABLE lesson ADD COLUMN language VARCHAR(10) DEFAULT 'japanese' NOT NULL"))
                
                # Update existing lessons to have 'japanese' as default language
                connection.execute(text("UPDATE lesson SET language = 'japanese' WHERE language IS NULL"))
                
                connection.commit()
            
            print("Successfully added language column to lesson table")
            print("All existing lessons have been set to 'japanese' language")
            
        except Exception as e:
            print(f"Error during migration: {e}")
            raise

if __name__ == "__main__":
    add_language_field()
