#!/usr/bin/env python3
"""
Fix lesson purchase cascade deletion issue.

This script fixes the foreign key constraint violation that occurs when deleting lessons
that have associated purchase records. It adds CASCADE deletion to the foreign key
constraint so that when a lesson is deleted, its associated purchase records are also deleted.
"""

import os
import sys
from sqlalchemy import text

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db

def fix_lesson_purchase_cascade():
    """Fix the lesson_purchase foreign key constraint to cascade on delete."""
    app = create_app()
    
    with app.app_context():
        try:
            print("Starting lesson purchase cascade fix...")
            
            # Check if we're using PostgreSQL or SQLite
            engine_name = db.engine.name
            print(f"Database engine: {engine_name}")
            
            if engine_name == 'postgresql':
                # PostgreSQL approach
                print("Applying PostgreSQL-specific fixes...")
                
                # First, check if the constraint exists
                check_constraint_sql = text("""
                    SELECT constraint_name 
                    FROM information_schema.table_constraints 
                    WHERE table_name = 'lesson_purchase' 
                    AND constraint_type = 'FOREIGN KEY'
                    AND constraint_name LIKE '%lesson_id%'
                """)
                
                result = db.session.execute(check_constraint_sql)
                constraints = result.fetchall()
                print(f"Found foreign key constraints: {[c[0] for c in constraints]}")
                
                # Drop the existing foreign key constraint
                for constraint in constraints:
                    constraint_name = constraint[0]
                    if 'lesson_id' in constraint_name.lower():
                        print(f"Dropping constraint: {constraint_name}")
                        drop_constraint_sql = text(f"""
                            ALTER TABLE lesson_purchase 
                            DROP CONSTRAINT IF EXISTS {constraint_name}
                        """)
                        db.session.execute(drop_constraint_sql)
                
                # Add the new foreign key constraint with CASCADE
                print("Adding new foreign key constraint with CASCADE...")
                add_constraint_sql = text("""
                    ALTER TABLE lesson_purchase 
                    ADD CONSTRAINT lesson_purchase_lesson_id_fkey 
                    FOREIGN KEY (lesson_id) REFERENCES lesson(id) ON DELETE CASCADE
                """)
                db.session.execute(add_constraint_sql)
                
            elif engine_name == 'sqlite':
                # SQLite approach - need to recreate the table
                print("Applying SQLite-specific fixes...")
                print("Note: SQLite requires table recreation to modify foreign key constraints")
                
                # Create a backup table
                print("Creating backup table...")
                backup_sql = text("""
                    CREATE TABLE lesson_purchase_backup AS 
                    SELECT * FROM lesson_purchase
                """)
                db.session.execute(backup_sql)
                
                # Drop the original table
                print("Dropping original table...")
                drop_sql = text("DROP TABLE lesson_purchase")
                db.session.execute(drop_sql)
                
                # Recreate the table with proper foreign key constraint
                print("Recreating table with CASCADE constraint...")
                create_sql = text("""
                    CREATE TABLE lesson_purchase (
                        id INTEGER PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        lesson_id INTEGER NOT NULL,
                        price_paid REAL NOT NULL,
                        purchased_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        stripe_payment_intent_id VARCHAR(100),
                        FOREIGN KEY (user_id) REFERENCES user(id),
                        FOREIGN KEY (lesson_id) REFERENCES lesson(id) ON DELETE CASCADE,
                        UNIQUE (user_id, lesson_id)
                    )
                """)
                db.session.execute(create_sql)
                
                # Restore the data
                print("Restoring data...")
                restore_sql = text("""
                    INSERT INTO lesson_purchase 
                    SELECT * FROM lesson_purchase_backup
                """)
                db.session.execute(restore_sql)
                
                # Drop the backup table
                print("Cleaning up backup table...")
                cleanup_sql = text("DROP TABLE lesson_purchase_backup")
                db.session.execute(cleanup_sql)
            
            else:
                print(f"Unsupported database engine: {engine_name}")
                return False
            
            # Commit the changes
            db.session.commit()
            print("Successfully applied lesson purchase cascade fix!")
            
            # Verify the fix
            print("Verifying the fix...")
            if engine_name == 'postgresql':
                verify_sql = text("""
                    SELECT 
                        tc.constraint_name,
                        rc.delete_rule
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.referential_constraints rc 
                        ON tc.constraint_name = rc.constraint_name
                    WHERE tc.table_name = 'lesson_purchase' 
                    AND tc.constraint_type = 'FOREIGN KEY'
                    AND rc.delete_rule = 'CASCADE'
                """)
                result = db.session.execute(verify_sql)
                cascade_constraints = result.fetchall()
                
                if cascade_constraints:
                    print(f"✓ CASCADE constraints found: {[c[0] for c in cascade_constraints]}")
                    return True
                else:
                    print("✗ No CASCADE constraints found")
                    return False
            else:
                # For SQLite, we assume success if we got this far
                print("✓ SQLite table recreated successfully")
                return True
                
        except Exception as e:
            print(f"Error applying fix: {e}")
            db.session.rollback()
            return False

def main():
    """Main function to run the fix."""
    print("=" * 60)
    print("Lesson Purchase Cascade Fix")
    print("=" * 60)
    
    success = fix_lesson_purchase_cascade()
    
    if success:
        print("\n✓ Fix applied successfully!")
        print("You can now delete lessons without foreign key constraint violations.")
    else:
        print("\n✗ Fix failed!")
        print("Please check the error messages above and try again.")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
