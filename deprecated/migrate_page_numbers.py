#!/usr/bin/env python3
"""
Migration script to add page_number field to existing lesson content.
This script adds the page_number column to the lesson_content table and sets default values.
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import LessonContent

def migrate_page_numbers():
    """Add page_number column and set default values for existing content."""
    
    app = create_app()
    
    with app.app_context():
        try:
            # Check if page_number column already exists
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('lesson_content')]
            
            if 'page_number' in columns:
                print("✓ page_number column already exists")
            else:
                print("Adding page_number column to lesson_content table...")
                
                # Add the column with a default value
                with db.engine.connect() as conn:
                    conn.execute(text("""
                        ALTER TABLE lesson_content 
                        ADD COLUMN page_number INTEGER NOT NULL DEFAULT 1
                    """))
                    conn.commit()
                
                print("✓ page_number column added successfully")
            
            # Update existing content to have page_number = 1 if it's NULL or 0
            print("Updating existing content with default page numbers...")
            
            result = db.session.execute(text("""
                UPDATE lesson_content 
                SET page_number = 1 
                WHERE page_number IS NULL OR page_number = 0
            """))
            
            db.session.commit()
            
            print(f"✓ Updated existing content items with default page number")
            
            # Verify the migration
            total_content = db.session.execute(text("SELECT COUNT(*) FROM lesson_content")).scalar()
            content_with_pages = db.session.execute(text("SELECT COUNT(*) FROM lesson_content WHERE page_number >= 1")).scalar()
            
            print(f"\nMigration Summary:")
            print(f"- Total content items: {total_content}")
            print(f"- Content items with page numbers: {content_with_pages}")
            
            if total_content == content_with_pages:
                print("✓ All content items have valid page numbers")
            else:
                print("⚠ Some content items may still need page numbers")
            
            return True
            
        except SQLAlchemyError as e:
            print(f"❌ Database error during migration: {e}")
            db.session.rollback()
            return False
        except Exception as e:
            print(f"❌ Unexpected error during migration: {e}")
            db.session.rollback()
            return False

def main():
    """Main function to run the migration."""
    print("Starting page number migration...")
    print("=" * 50)
    
    success = migrate_page_numbers()
    
    print("=" * 50)
    if success:
        print("✓ Page number migration completed successfully!")
        print("\nNext steps:")
        print("1. Test the lesson content management in the admin panel")
        print("2. Verify that lessons display correctly with the new page structure")
        print("3. Create some test content with different page numbers")
    else:
        print("❌ Page number migration failed!")
        print("Please check the error messages above and try again.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
