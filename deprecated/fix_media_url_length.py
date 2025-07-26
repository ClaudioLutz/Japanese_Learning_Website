#!/usr/bin/env python3
"""
Fix Media URL Length Issue

This script fixes the media_url field length constraint in the LessonContent table.
The current limit of 255 characters is too small for AI-generated image URLs.
"""

import os
import sys
from pathlib import Path

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from app import create_app, db
from sqlalchemy import text

def fix_media_url_length():
    """Fix the media_url field length constraint"""
    app = create_app()
    
    with app.app_context():
        print("🔧 Fixing media_url field length constraint...")
        
        try:
            # Check current column definition
            result = db.session.execute(text("""
                SELECT character_maximum_length 
                FROM information_schema.columns 
                WHERE table_name = 'lesson_content' 
                AND column_name = 'media_url'
            """))
            
            current_length = result.fetchone()
            if current_length:
                print(f"Current media_url length limit: {current_length[0]}")
            
            # Alter the column to increase length
            print("Increasing media_url field length to 1000 characters...")
            db.session.execute(text("""
                ALTER TABLE lesson_content 
                ALTER COLUMN media_url TYPE VARCHAR(1000)
            """))
            
            db.session.commit()
            print("✅ Successfully increased media_url field length to 1000 characters")
            
            # Verify the change
            result = db.session.execute(text("""
                SELECT character_maximum_length 
                FROM information_schema.columns 
                WHERE table_name = 'lesson_content' 
                AND column_name = 'media_url'
            """))
            
            new_length = result.fetchone()
            if new_length:
                print(f"New media_url length limit: {new_length[0]}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error fixing media_url length: {e}")
            db.session.rollback()
            return False

def main():
    """Main function"""
    print("🔧 Media URL Length Fixer")
    print("=" * 40)
    print()
    print("This script will increase the media_url field length")
    print("in the lesson_content table from 255 to 1000 characters")
    print("to accommodate longer AI-generated image URLs.")
    print()
    
    if fix_media_url_length():
        print("\n🎉 Media URL length fix completed successfully!")
        print("\nYou can now run lesson scripts that generate images:")
        print("  python lesson_creation_scripts/create_comprehensive_kitsune_lesson.py")
    else:
        print("\n⚠️  Media URL length fix failed. Please check the error messages above.")

if __name__ == "__main__":
    main()
