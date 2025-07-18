#!/usr/bin/env python3
"""
Fix duplicate UserLessonProgress records in the database.

This script identifies and removes duplicate records in the user_lesson_progress table,
keeping only the most recent record for each (user_id, lesson_id) combination.
"""

import sys
import os
from datetime import datetime
from sqlalchemy import func, and_

# Add the app directory to the path so we can import our models
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import UserLessonProgress

def find_duplicates():
    """Find all duplicate (user_id, lesson_id) combinations."""
    print("Searching for duplicate UserLessonProgress records...")
    
    # Query to find user_id, lesson_id combinations that have more than one record
    duplicates = db.session.query(
        UserLessonProgress.user_id,
        UserLessonProgress.lesson_id,
        func.count(UserLessonProgress.id).label('count')
    ).group_by(
        UserLessonProgress.user_id,
        UserLessonProgress.lesson_id
    ).having(func.count(UserLessonProgress.id) > 1).all()
    
    print(f"Found {len(duplicates)} duplicate combinations:")
    for user_id, lesson_id, count in duplicates:
        print(f"  User {user_id}, Lesson {lesson_id}: {count} records")
    
    return duplicates

def fix_duplicates(duplicates, dry_run=True):
    """Fix duplicate records by keeping the most recent one."""
    if not duplicates:
        print("No duplicates to fix.")
        return
    
    print(f"\n{'DRY RUN: ' if dry_run else ''}Fixing duplicate records...")
    
    total_removed = 0
    
    for user_id, lesson_id, count in duplicates:
        print(f"\nProcessing User {user_id}, Lesson {lesson_id} ({count} records):")
        
        # Get all records for this combination, ordered by most recent first
        records = UserLessonProgress.query.filter(
            and_(
                UserLessonProgress.user_id == user_id,
                UserLessonProgress.lesson_id == lesson_id
            )
        ).order_by(
            UserLessonProgress.last_accessed.desc().nullslast(),
            UserLessonProgress.started_at.desc().nullslast(),
            UserLessonProgress.id.desc()
        ).all()
        
        if len(records) <= 1:
            print(f"  Only {len(records)} record found, skipping.")
            continue
        
        # Keep the first (most recent) record
        keep_record = records[0]
        remove_records = records[1:]
        
        print(f"  Keeping record ID {keep_record.id} (last_accessed: {keep_record.last_accessed}, progress: {keep_record.progress_percentage}%)")
        
        for record in remove_records:
            print(f"  {'Would remove' if dry_run else 'Removing'} record ID {record.id} (last_accessed: {record.last_accessed}, progress: {record.progress_percentage}%)")
            
            if not dry_run:
                db.session.delete(record)
                total_removed += 1
    
    if not dry_run:
        try:
            db.session.commit()
            print(f"\nSuccessfully removed {total_removed} duplicate records.")
        except Exception as e:
            db.session.rollback()
            print(f"\nError committing changes: {e}")
            raise
    else:
        print(f"\nDRY RUN: Would remove {len([r for _, _, count in duplicates for r in range(count - 1)])} duplicate records.")

def verify_fix():
    """Verify that no duplicates remain."""
    print("\nVerifying fix...")
    duplicates = find_duplicates()
    
    if not duplicates:
        print("✅ No duplicate records found. Fix successful!")
        return True
    else:
        print("❌ Duplicates still exist. Fix may have failed.")
        return False

def main():
    """Main function to fix duplicate progress records."""
    app = create_app()
    
    with app.app_context():
        print("=== UserLessonProgress Duplicate Fix Tool ===")
        print(f"Database: {app.config.get('SQLALCHEMY_DATABASE_URI', 'Unknown')}")
        print(f"Timestamp: {datetime.now()}")
        
        # Find duplicates
        duplicates = find_duplicates()
        
        if not duplicates:
            print("\n✅ No duplicate records found. Database is clean!")
            return
        
        # Show what would be done
        print("\n" + "="*50)
        print("DRY RUN - Showing what would be changed:")
        print("="*50)
        fix_duplicates(duplicates, dry_run=True)
        
        # Ask for confirmation
        print("\n" + "="*50)
        response = input("Do you want to proceed with fixing these duplicates? (yes/no): ").strip().lower()
        
        if response in ['yes', 'y']:
            print("\nProceeding with fix...")
            fix_duplicates(duplicates, dry_run=False)
            verify_fix()
        else:
            print("Operation cancelled.")

if __name__ == "__main__":
    main()
