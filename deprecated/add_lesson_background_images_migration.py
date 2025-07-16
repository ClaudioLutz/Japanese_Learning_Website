#!/usr/bin/env python3
"""
Migration script to add background image fields to the Lesson model.
This adds background_image_url and background_image_path fields for lesson tile backgrounds.
"""
import os
import sys

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Load environment variables manually
def load_env():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    value = value.strip('"\'')
                    os.environ[key] = value

load_env()

from app import create_app, db
from sqlalchemy import text

def run_migration():
    """Add background image fields to the Lesson table."""
    app = create_app()
    
    with app.app_context():
        print("--- Adding Background Image Fields to Lesson Model ---")
        
        try:
            # Check if columns already exist
            result = db.session.execute(text("PRAGMA table_info(lesson)"))
            columns = [row[1] for row in result.fetchall()]
            
            migrations_needed = []
            
            if 'background_image_url' not in columns:
                migrations_needed.append("ALTER TABLE lesson ADD COLUMN background_image_url VARCHAR(255)")
                
            if 'background_image_path' not in columns:
                migrations_needed.append("ALTER TABLE lesson ADD COLUMN background_image_path VARCHAR(500)")
            
            if not migrations_needed:
                print("✅ Background image fields already exist in the Lesson table.")
                return
            
            # Execute migrations
            for migration in migrations_needed:
                print(f"Executing: {migration}")
                db.session.execute(text(migration))
            
            db.session.commit()
            print("✅ Successfully added background image fields to Lesson table.")
            
            # Verify the changes
            result = db.session.execute(text("PRAGMA table_info(lesson)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'background_image_url' in columns and 'background_image_path' in columns:
                print("✅ Migration verified: Both background image fields are now present.")
            else:
                print("❌ Migration verification failed.")
                
        except Exception as e:
            print(f"❌ Error during migration: {e}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    run_migration()
