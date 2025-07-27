#!/usr/bin/env python3
"""
Script to update all lessons to 5.00 CHF and enable individual purchase
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Lesson

def update_lesson_pricing():
    """Update all lessons to 5.00 CHF and enable individual purchase"""
    app = create_app()
    
    with app.app_context():
        try:
            # Get all lessons
            lessons = Lesson.query.all()
            
            if not lessons:
                print("No lessons found in the database.")
                return
            
            print(f"Found {len(lessons)} lessons to update...")
            
            updated_count = 0
            
            for lesson in lessons:
                # Update pricing
                old_price = lesson.price
                old_purchasable = lesson.is_purchasable
                
                lesson.price = 5.00
                lesson.is_purchasable = True
                
                print(f"Lesson '{lesson.title}' (ID: {lesson.id})")
                print(f"  Price: {old_price} CHF -> 5.00 CHF")
                print(f"  Purchasable: {old_purchasable} -> True")
                print()
                
                updated_count += 1
            
            # Commit all changes
            db.session.commit()
            
            print(f"✅ Successfully updated {updated_count} lessons!")
            print("All lessons now have:")
            print("  - Price: 5.00 CHF")
            print("  - Individual Purchase: Enabled")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error updating lessons: {str(e)}")
            return False
    
    return True

if __name__ == "__main__":
    print("🔄 Updating lesson pricing...")
    print("Setting all lessons to 5.00 CHF with individual purchase enabled...")
    print()
    
    success = update_lesson_pricing()
    
    if success:
        print("\n🎉 Lesson pricing update completed successfully!")
    else:
        print("\n💥 Lesson pricing update failed!")
        sys.exit(1)
