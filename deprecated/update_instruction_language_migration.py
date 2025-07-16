#!/usr/bin/env python3
"""
Migration script to rename language column to instruction_language and update values
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Lesson
from sqlalchemy import text

def update_instruction_language_field():
    """Rename language column to instruction_language and update values"""
    app = create_app()
    
    with app.app_context():
        try:
            with db.engine.connect() as connection:
                # Check if the old language column exists
                result = connection.execute(text("PRAGMA table_info(lesson)"))
                columns = [row[1] for row in result]
                
                if 'instruction_language' in columns:
                    print("instruction_language column already exists in lesson table")
                    return
                
                if 'language' not in columns:
                    print("language column not found, adding instruction_language column...")
                    # Add the instruction_language column with default value
                    connection.execute(text("ALTER TABLE lesson ADD COLUMN instruction_language VARCHAR(10) DEFAULT 'english' NOT NULL"))
                    connection.commit()
                    print("Successfully added instruction_language column to lesson table")
                    return
                
                print("Renaming language column to instruction_language...")
                
                # SQLite doesn't support renaming columns directly, so we need to:
                # 1. Add new column
                # 2. Copy data
                # 3. Drop old column (requires table recreation in SQLite)
                
                # Add new column
                connection.execute(text("ALTER TABLE lesson ADD COLUMN instruction_language VARCHAR(10) DEFAULT 'english' NOT NULL"))
                
                # Update values: change 'japanese' to 'english' since lessons are FOR learning Japanese
                connection.execute(text("UPDATE lesson SET instruction_language = 'english' WHERE language = 'japanese'"))
                connection.execute(text("UPDATE lesson SET instruction_language = language WHERE language != 'japanese'"))
                
                # Note: We can't easily drop the old column in SQLite without recreating the table
                # For now, we'll leave the old column and use the new one
                print("Added instruction_language column and copied data")
                print("Note: Old 'language' column still exists but is not used")
                
                connection.commit()
            
            print("Successfully updated lesson table with instruction_language field")
            print("All lessons now have instruction language set to 'english' by default")
            
        except Exception as e:
            print(f"Error during migration: {e}")
            raise

if __name__ == "__main__":
    update_instruction_language_field()
