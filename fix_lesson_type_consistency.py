#!/usr/bin/env python3
"""
Fix lesson type consistency issue.
Updates lesson_type field to automatically reflect the actual pricing:
- lesson_type = "free" when price = 0.00
- lesson_type = "paid" when price > 0.00
"""

from app import create_app, db
from app.models import Lesson

def fix_lesson_types():
    """Fix inconsistent lesson types based on pricing"""
    app = create_app()
    
    with app.app_context():
        print("Fixing lesson type consistency...")
        print("=" * 50)
        
        # Get all lessons
        all_lessons = Lesson.query.all()
        print(f"Found {len(all_lessons)} lessons to check")
        
        # Track changes
        changes_made = 0
        free_lessons = 0
        paid_lessons = 0
        
        for lesson in all_lessons:
            old_type = lesson.lesson_type
            
            # Set lesson type based on price
            if lesson.price == 0.0:
                new_type = "free"
                free_lessons += 1
            else:
                new_type = "paid"
                paid_lessons += 1
            
            # Update if needed
            if old_type != new_type:
                lesson.lesson_type = new_type
                changes_made += 1
                print(f"  Updated lesson {lesson.id}: '{lesson.title[:40]}...' from '{old_type}' -> '{new_type}' (price: {lesson.price})")
        
        # Commit changes
        if changes_made > 0:
            try:
                db.session.commit()
                print(f"\n✅ Successfully updated {changes_made} lessons")
            except Exception as e:
                db.session.rollback()
                print(f"\n❌ Error updating lessons: {e}")
                return False
        else:
            print("\n✅ No changes needed - all lesson types are already consistent")
        
        print(f"\nFinal summary:")
        print(f"  - Free lessons (price = 0.00): {free_lessons}")
        print(f"  - Paid lessons (price > 0.00): {paid_lessons}")
        print(f"  - Total lessons: {len(all_lessons)}")
        
        # Verify the fix
        print("\nVerifying fix...")
        inconsistent_count = Lesson.query.filter(
            ((Lesson.lesson_type == 'free') & (Lesson.price > 0)) |
            ((Lesson.lesson_type == 'paid') & (Lesson.price == 0))
        ).count()
        
        if inconsistent_count == 0:
            print("✅ All lesson types are now consistent with pricing!")
        else:
            print(f"❌ Still found {inconsistent_count} inconsistent lessons")
            return False
        
        return True

if __name__ == "__main__":
    success = fix_lesson_types()
    if success:
        print("\n🎉 Lesson type consistency fix completed successfully!")
    else:
        print("\n💥 Lesson type consistency fix failed!")
