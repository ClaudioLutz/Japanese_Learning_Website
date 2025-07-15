#!/usr/bin/env python3
"""
Migration script to add file-related fields to LessonContent table
"""

import sqlite3
import os

def migrate_lesson_content_table():
    """Add file-related fields to LessonContent table"""
    
    # Database path
    db_path = os.path.join('instance', 'site.db')
    
    if not os.path.exists(db_path):
        print(f"Database not found at: {db_path}")
        return False
    
    print(f"Migrating LessonContent table at: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the new columns already exist
        cursor.execute("PRAGMA table_info(lesson_content)")
        columns = [column[1] for column in cursor.fetchall()]
        
        new_columns = [
            ('file_path', 'VARCHAR(500)'),
            ('file_size', 'INTEGER'),
            ('file_type', 'VARCHAR(50)'),
            ('original_filename', 'VARCHAR(255)')
        ]
        
        for column_name, column_type in new_columns:
            if column_name not in columns:
                print(f"Adding column '{column_name}' to lesson_content table...")
                cursor.execute(f"ALTER TABLE lesson_content ADD COLUMN {column_name} {column_type}")
                print(f"Column '{column_name}' added successfully.")
            else:
                print(f"Column '{column_name}' already exists.")
        
        conn.commit()
        print("LessonContent table migration completed successfully!")
        
        # Verify the changes
        cursor.execute("PRAGMA table_info(lesson_content)")
        columns_after = [column[1] for column in cursor.fetchall()]
        print(f"LessonContent table now has columns: {columns_after}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error during migration: {e}")
        if 'conn' in locals():
            conn.close()
        return False

if __name__ == "__main__":
    success = migrate_lesson_content_table()
    if success:
        print("Migration completed successfully!")
    else:
        print("Migration failed!")
