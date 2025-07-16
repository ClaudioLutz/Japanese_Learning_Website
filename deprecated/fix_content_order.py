#!/usr/bin/env python3
"""
Script to fix all content order indices in the database.
This will reorder all content items to have sequential order indices starting from 0.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import LessonContent

def fix_all_content_order():
    """Fix order indices for all lessons and pages"""
    app = create_app()
    
    with app.app_context():
        print("Starting content order fix...")
        
        # Get all unique lesson_id and page_number combinations
        lesson_pages = db.session.query(
            LessonContent.lesson_id, 
            LessonContent.page_number
        ).distinct().all()
        
        total_fixed = 0
        
        for lesson_id, page_number in lesson_pages:
            print(f"Fixing lesson {lesson_id}, page {page_number}...")
            
            # Get all content items for this lesson/page, ordered by current order_index
            content_items = LessonContent.query.filter(
                LessonContent.lesson_id == lesson_id,
                LessonContent.page_number == page_number
            ).order_by(LessonContent.order_index).all()
            
            # Reassign order indices starting from 0
            for index, content_item in enumerate(content_items):
                old_order = content_item.order_index
                content_item.order_index = index
                if old_order != index:
                    print(f"  Content {content_item.id}: {old_order} -> {index}")
                    total_fixed += 1
        
        # Commit all changes
        db.session.commit()
        print(f"\nFixed {total_fixed} content items across {len(lesson_pages)} lesson pages.")
        print("Content order fix completed successfully!")

if __name__ == "__main__":
    fix_all_content_order()
