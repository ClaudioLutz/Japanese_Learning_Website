#!/usr/bin/env python3
"""
Script to enable guest access for some existing lessons
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Lesson

def enable_guest_access():
    """Enable guest access for the first few lessons"""
    app = create_app()
    
    with app.app_context():
        # Get the first 3 lessons (or however many exist)
        lessons = Lesson.query.order_by(Lesson.order_index.asc()).limit(3).all()
        
        if not lessons:
            print("No lessons found in the database.")
            print("Please create some lessons first using the lesson creation scripts.")
            return
        
        print(f"Found {len(lessons)} lessons to enable guest access for:")
        
        for lesson in lessons:
            lesson.allow_guest_access = True
            print(f"- Enabled guest access for: {lesson.title}")
        
        try:
            db.session.commit()
            print(f"\n✅ Successfully enabled guest access for {len(lessons)} lessons!")
            print("\nGuests can now access these lessons without logging in:")
            for lesson in lessons:
                print(f"  • {lesson.title} (ID: {lesson.id})")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error updating lessons: {e}")

if __name__ == "__main__":
    enable_guest_access()
