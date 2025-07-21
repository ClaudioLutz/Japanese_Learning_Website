#!/usr/bin/env python3
"""
Data Migration Script
Transfer existing data from local SQLite to Google Cloud PostgreSQL
"""

import os
import sys
import sqlite3
import psycopg
import json
import logging
from datetime import datetime
from werkzeug.security import generate_password_hash

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_migration.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DataMigrator:
    def __init__(self, sqlite_path, postgres_config):
        self.sqlite_path = sqlite_path
        self.postgres_config = postgres_config
        self.sqlite_conn = None
        self.postgres_conn = None
        self.postgres_cursor = None
        
    def connect_databases(self):
        """Connect to both SQLite and PostgreSQL databases"""
        try:
            # Connect to SQLite
            self.sqlite_conn = sqlite3.connect(self.sqlite_path)
            self.sqlite_conn.row_factory = sqlite3.Row  # Enable column access by name
            logger.info(f"✓ Connected to SQLite database: {self.sqlite_path}")
            
            # Connect to PostgreSQL
            postgres_config = self.postgres_config.copy()
            if 'database' in postgres_config:
                postgres_config['dbname'] = postgres_config.pop('database')
            self.postgres_conn = psycopg.connect(**postgres_config)
            self.postgres_cursor = self.postgres_conn.cursor()
            logger.info(f"✓ Connected to PostgreSQL database")
            
            return True
        except Exception as e:
            logger.error(f"Failed to connect to databases: {e}")
            return False
    
    def get_sqlite_table_data(self, table_name):
        """Get all data from SQLite table"""
        if not self.sqlite_conn:
            logger.error("No SQLite connection available")
            return []
        try:
            cursor = self.sqlite_conn.cursor()
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            logger.info(f"✓ Retrieved {len(rows)} records from SQLite table '{table_name}'")
            return rows
        except sqlite3.OperationalError as e:
            if "no such table" in str(e):
                logger.warning(f"⚠️  Table '{table_name}' does not exist in SQLite database")
                return []
            else:
                logger.error(f"Error reading from SQLite table '{table_name}': {e}")
                return []
    
    def migrate_users(self):
        """Migrate user data"""
        if not self.postgres_cursor or not self.postgres_conn:
            logger.error("No PostgreSQL connection available")
            return False
            
        logger.info("Migrating users...")
        rows = self.get_sqlite_table_data('user')
        
        if not rows:
            return True
        
        # Skip admin user (already created by database creation script)
        migrated_count = 0
        for row in rows:
            if row['username'] == 'admin':
                continue
                
            try:
                sql = """
                INSERT INTO "user" (username, email, password_hash, subscription_level, is_admin)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (username) DO UPDATE SET
                    email = EXCLUDED.email,
                    subscription_level = EXCLUDED.subscription_level,
                    is_admin = EXCLUDED.is_admin;
                """
                self.postgres_cursor.execute(sql, (
                    row['username'],
                    row['email'],
                    row['password_hash'],
                    row['subscription_level'] or 'free',
                    row['is_admin'] or False
                ))
                migrated_count += 1
            except Exception as e:
                logger.error(f"Failed to migrate user {row['username']}: {e}")
        
        self.postgres_conn.commit()
        logger.info(f"✓ Migrated {migrated_count} users")
        return True
    
    def migrate_content_table(self, table_name, columns):
        """Generic method to migrate content tables"""
        if not self.postgres_cursor or not self.postgres_conn:
            logger.error("No PostgreSQL connection available")
            return False
            
        logger.info(f"Migrating {table_name}...")
        rows = self.get_sqlite_table_data(table_name)
        
        if not rows:
            return True
        
        migrated_count = 0
        placeholders = ', '.join(['%s'] * len(columns))
        column_names = ', '.join(columns)
        
        for row in rows:
            try:
                values = [row[col] if col in row.keys() else None for col in columns]
                sql = f"""
                INSERT INTO {table_name} ({column_names})
                VALUES ({placeholders})
                ON CONFLICT DO NOTHING;
                """
                self.postgres_cursor.execute(sql, values)
                migrated_count += 1
            except Exception as e:
                logger.error(f"Failed to migrate {table_name} record: {e}")
        
        self.postgres_conn.commit()
        logger.info(f"✓ Migrated {migrated_count} {table_name} records")
        return True
    
    def migrate_lessons(self):
        """Migrate lesson data with special handling"""
        if not self.postgres_cursor or not self.postgres_conn:
            logger.error("No PostgreSQL connection available")
            return False
            
        logger.info("Migrating lessons...")
        rows = self.get_sqlite_table_data('lesson')
        
        if not rows:
            return True
        
        migrated_count = 0
        for row in rows:
            try:
                sql = """
                INSERT INTO lesson (
                    title, description, lesson_type, category_id, difficulty_level,
                    estimated_duration, order_index, is_published, allow_guest_access,
                    instruction_language, thumbnail_url, background_image_url,
                    background_image_path, video_intro_url, created_at, updated_at,
                    price, is_purchasable
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING;
                """
                
                # Handle datetime fields
                created_at = row.get('created_at')
                updated_at = row.get('updated_at')
                if isinstance(created_at, str):
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                if isinstance(updated_at, str):
                    updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                
                self.postgres_cursor.execute(sql, (
                    row['title'],
                    row.get('description'),
                    row['lesson_type'],
                    row.get('category_id'),
                    row.get('difficulty_level'),
                    row.get('estimated_duration'),
                    row.get('order_index', 0),
                    row.get('is_published', False),
                    row.get('allow_guest_access', False),
                    row.get('instruction_language', 'english'),
                    row.get('thumbnail_url'),
                    row.get('background_image_url'),
                    row.get('background_image_path'),
                    row.get('video_intro_url'),
                    created_at or datetime.utcnow(),
                    updated_at or datetime.utcnow(),
                    row.get('price', 0.0),
                    row.get('is_purchasable', False)
                ))
                migrated_count += 1
            except Exception as e:
                logger.error(f"Failed to migrate lesson '{row['title']}': {e}")
        
        self.postgres_conn.commit()
        logger.info(f"✓ Migrated {migrated_count} lessons")
        return True
    
    def migrate_lesson_content(self):
        """Migrate lesson content with JSON handling"""
        if not self.postgres_cursor or not self.postgres_conn:
            logger.error("No PostgreSQL connection available")
            return False
            
        logger.info("Migrating lesson content...")
        rows = self.get_sqlite_table_data('lesson_content')
        
        if not rows:
            return True
        
        migrated_count = 0
        for row in rows:
            try:
                # Handle JSON field
                ai_details = row.get('ai_generation_details')
                if ai_details and isinstance(ai_details, str):
                    try:
                        ai_details = json.loads(ai_details)
                    except json.JSONDecodeError:
                        ai_details = None
                
                sql = """
                INSERT INTO lesson_content (
                    lesson_id, content_type, content_id, title, content_text,
                    media_url, order_index, page_number, is_optional, created_at,
                    file_path, file_size, file_type, original_filename,
                    is_interactive, quiz_type, max_attempts, passing_score,
                    generated_by_ai, ai_generation_details
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING;
                """
                
                created_at = row.get('created_at')
                if isinstance(created_at, str):
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                
                self.postgres_cursor.execute(sql, (
                    row['lesson_id'],
                    row['content_type'],
                    row.get('content_id'),
                    row.get('title'),
                    row.get('content_text'),
                    row.get('media_url'),
                    row.get('order_index', 0),
                    row.get('page_number', 1),
                    row.get('is_optional', False),
                    created_at or datetime.utcnow(),
                    row.get('file_path'),
                    row.get('file_size'),
                    row.get('file_type'),
                    row.get('original_filename'),
                    row.get('is_interactive', False),
                    row.get('quiz_type', 'standard'),
                    row.get('max_attempts', 3),
                    row.get('passing_score', 70),
                    row.get('generated_by_ai', False),
                    json.dumps(ai_details) if ai_details else None
                ))
                migrated_count += 1
            except Exception as e:
                logger.error(f"Failed to migrate lesson content: {e}")
        
        self.postgres_conn.commit()
        logger.info(f"✓ Migrated {migrated_count} lesson content items")
        return True
    
    def migrate_all_data(self):
        """Migrate all data from SQLite to PostgreSQL"""
        logger.info("Starting data migration process...")
        
        if not self.connect_databases():
            return False
        
        try:
            # Migration order is important due to foreign key constraints
            migrations = [
                # Content tables (no foreign keys)
                (self.migrate_content_table, 'kana', ['character', 'romanization', 'type', 'stroke_order_info', 'example_sound_url']),
                (self.migrate_content_table, 'kanji', ['character', 'meaning', 'onyomi', 'kunyomi', 'jlpt_level', 'stroke_order_info', 'radical', 'stroke_count', 'status', 'created_by_ai']),
                (self.migrate_content_table, 'vocabulary', ['word', 'reading', 'meaning', 'jlpt_level', 'example_sentence_japanese', 'example_sentence_english', 'audio_url', 'status', 'created_by_ai']),
                (self.migrate_content_table, 'grammar', ['title', 'explanation', 'structure', 'jlpt_level', 'example_sentences', 'status', 'created_by_ai']),
                
                # Users
                (self.migrate_users,),
                
                # Lesson categories (already created by database script, but migrate any custom ones)
                (self.migrate_content_table, 'lesson_category', ['name', 'description', 'color_code']),
                
                # Lessons
                (self.migrate_lessons,),
                
                # Lesson-related tables
                (self.migrate_content_table, 'lesson_prerequisite', ['lesson_id', 'prerequisite_lesson_id']),
                (self.migrate_content_table, 'lesson_page', ['lesson_id', 'page_number', 'title', 'description']),
                (self.migrate_lesson_content,),
                
                # Quiz system
                (self.migrate_content_table, 'quiz_question', ['lesson_content_id', 'question_type', 'question_text', 'explanation', 'hint', 'difficulty_level', 'points', 'order_index']),
                (self.migrate_content_table, 'quiz_option', ['question_id', 'option_text', 'is_correct', 'order_index', 'feedback']),
                
                # User progress and purchases
                (self.migrate_content_table, 'user_lesson_progress', ['user_id', 'lesson_id', 'started_at', 'completed_at', 'is_completed', 'progress_percentage', 'time_spent', 'last_accessed', 'content_progress']),
                (self.migrate_content_table, 'user_quiz_answer', ['user_id', 'question_id', 'selected_option_id', 'text_answer', 'is_correct', 'answered_at', 'attempts']),
                (self.migrate_content_table, 'lesson_purchase', ['user_id', 'lesson_id', 'price_paid', 'purchased_at', 'stripe_payment_intent_id']),
                
                # Course system
                (self.migrate_content_table, 'course', ['title', 'description', 'background_image_url', 'is_published']),
                (self.migrate_content_table, 'course_lessons', ['course_id', 'lesson_id']),
            ]
            
            success_count = 0
            for migration in migrations:
                try:
                    if len(migration) == 1:
                        # Single function call
                        if migration[0]():
                            success_count += 1
                    else:
                        # Function with parameters
                        if migration[0](migration[1], migration[2]):
                            success_count += 1
                except Exception as e:
                    logger.error(f"Migration failed: {e}")
            
            logger.info(f"✅ Migration completed! {success_count}/{len(migrations)} migrations successful")
            return success_count == len(migrations)
            
        except Exception as e:
            logger.error(f"Migration process failed: {e}")
            return False
        finally:
            if self.sqlite_conn:
                self.sqlite_conn.close()
            if self.postgres_conn:
                self.postgres_conn.close()
            logger.info("Database connections closed")

def main():
    """Main execution function"""
    print("🔄 Japanese Learning Website - Data Migrator")
    print("=" * 50)
    
    # SQLite database path
    sqlite_path = input("Enter path to your SQLite database (e.g., instance/site.db): ").strip()
    if not sqlite_path:
        sqlite_path = "instance/site.db"
    
    if not os.path.exists(sqlite_path):
        print(f"❌ SQLite database not found: {sqlite_path}")
        sys.exit(1)
    
    # PostgreSQL configuration
    postgres_config = {
        'host': '34.65.227.94',
        'database': 'japanese_learning',
        'user': 'app_user',
        'password': 'Dg34.67MDt',
        'port': 5432
    }
    
    print(f"SQLite source: {sqlite_path}")
    print(f"PostgreSQL target: {postgres_config['host']}:{postgres_config['port']}/{postgres_config['database']}")
    
    confirm = input("\n🚀 Start data migration? (y/N): ").lower().strip()
    if confirm != 'y':
        print("Migration cancelled.")
        return
    
    # Run migration
    migrator = DataMigrator(sqlite_path, postgres_config)
    success = migrator.migrate_all_data()
    
    if success:
        print("\n✅ Data migration completed successfully!")
        print("\nNext steps:")
        print("1. Verify your data in the PostgreSQL database")
        print("2. Test your Flask application with the new database")
        print("3. Update your production configuration")
    else:
        print("\n❌ Data migration failed. Check the logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
