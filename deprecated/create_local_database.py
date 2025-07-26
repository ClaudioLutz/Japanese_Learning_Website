#!/usr/bin/env python3
"""
Local PostgreSQL Database Creation Script for Japanese Learning Website
Creates a complete local database with all tables and initial data
"""

import os
import sys
import psycopg
from psycopg import sql
import logging
from datetime import datetime
from werkzeug.security import generate_password_hash

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('local_database_creation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class LocalDatabaseCreator:
    def __init__(self, host='localhost', database='japanese_learning', username='postgres', password='', port=5432):
        self.host = host
        self.database = database
        self.username = username
        self.password = password
        self.port = port
        self.connection = None
        self.cursor = None
    
    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            self.connection = psycopg.connect(
                host=self.host,
                dbname=self.database,
                user=self.username,
                password=self.password,
                port=self.port,
                autocommit=True
            )
            self.cursor = self.connection.cursor()
            logger.info(f"Successfully connected to local database {self.database}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return False
    
    def create_database_if_not_exists(self):
        """Create the database if it doesn't exist"""
        try:
            # Connect to postgres database to create our target database
            conn = psycopg.connect(
                host=self.host,
                dbname='postgres',
                user=self.username,
                password=self.password,
                port=self.port,
                autocommit=True
            )
            cursor = conn.cursor()
            
            # Check if database exists
            cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (self.database,))
            exists = cursor.fetchone()
            
            if not exists:
                cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(self.database)))
                logger.info(f"Created database: {self.database}")
            else:
                logger.info(f"Database {self.database} already exists")
            
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Failed to create database: {e}")
            return False
    
    def execute_sql(self, sql_query, description=""):
        """Execute SQL with error handling"""
        if not self.cursor:
            logger.error("No database cursor available")
            return False
        try:
            logger.info(f"Executing: {description}")
            self.cursor.execute(sql_query)
            logger.info(f"✓ Success: {description}")
            return True
        except Exception as e:
            logger.error(f"✗ Failed: {description} - {e}")
            return False
    
    def table_exists(self, table_name):
        """Check if table exists"""
        if not self.cursor:
            return False
        try:
            self.cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                );
            """, (table_name,))
            result = self.cursor.fetchone()
            return result[0] if result else False
        except:
            return False
    
    def drop_all_tables(self):
        """Drop all existing tables (use with caution)"""
        if not self.cursor:
            logger.error("No database cursor available")
            return
            
        logger.warning("Dropping all existing tables...")
        
        # Get all table names
        self.cursor.execute("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public' 
            AND tablename NOT LIKE 'pg_%' 
            AND tablename NOT LIKE 'sql_%'
        """)
        
        tables = [row[0] for row in self.cursor.fetchall()]
        
        if tables:
            # Drop tables with CASCADE to handle foreign keys
            for table in tables:
                self.execute_sql(f"DROP TABLE IF EXISTS {table} CASCADE", f"Dropping table {table}")
        
        logger.info("All tables dropped successfully")
    
    def create_user_table(self):
        """Create User table"""
        sql_query = """
        CREATE TABLE IF NOT EXISTS "user" (
            id SERIAL PRIMARY KEY,
            username VARCHAR(80) UNIQUE NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            password_hash VARCHAR(256) NOT NULL,
            subscription_level VARCHAR(50) DEFAULT 'free',
            is_admin BOOLEAN DEFAULT FALSE NOT NULL
        );
        """
        return self.execute_sql(sql_query, "Creating User table")
    
    def create_kana_table(self):
        """Create Kana table"""
        sql_query = """
        CREATE TABLE IF NOT EXISTS kana (
            id SERIAL PRIMARY KEY,
            character VARCHAR(5) UNIQUE NOT NULL,
            romanization VARCHAR(10) NOT NULL,
            type VARCHAR(10) NOT NULL,
            stroke_order_info VARCHAR(255),
            example_sound_url VARCHAR(255)
        );
        """
        return self.execute_sql(sql_query, "Creating Kana table")
    
    def create_kanji_table(self):
        """Create Kanji table"""
        sql_query = """
        CREATE TABLE IF NOT EXISTS kanji (
            id SERIAL PRIMARY KEY,
            character VARCHAR(5) UNIQUE NOT NULL,
            meaning TEXT NOT NULL,
            onyomi VARCHAR(100),
            kunyomi VARCHAR(100),
            jlpt_level INTEGER,
            stroke_order_info VARCHAR(255),
            radical VARCHAR(10),
            stroke_count INTEGER,
            status VARCHAR(20) DEFAULT 'approved' NOT NULL,
            created_by_ai BOOLEAN DEFAULT FALSE NOT NULL
        );
        """
        return self.execute_sql(sql_query, "Creating Kanji table")
    
    def create_vocabulary_table(self):
        """Create Vocabulary table"""
        sql_query = """
        CREATE TABLE IF NOT EXISTS vocabulary (
            id SERIAL PRIMARY KEY,
            word VARCHAR(100) UNIQUE NOT NULL,
            reading VARCHAR(100) NOT NULL,
            meaning TEXT NOT NULL,
            jlpt_level INTEGER,
            example_sentence_japanese TEXT,
            example_sentence_english TEXT,
            audio_url VARCHAR(255),
            status VARCHAR(20) DEFAULT 'approved' NOT NULL,
            created_by_ai BOOLEAN DEFAULT FALSE NOT NULL
        );
        """
        return self.execute_sql(sql_query, "Creating Vocabulary table")
    
    def create_grammar_table(self):
        """Create Grammar table"""
        sql_query = """
        CREATE TABLE IF NOT EXISTS grammar (
            id SERIAL PRIMARY KEY,
            title VARCHAR(200) UNIQUE NOT NULL,
            explanation TEXT NOT NULL,
            structure VARCHAR(255),
            jlpt_level INTEGER,
            example_sentences TEXT,
            status VARCHAR(20) DEFAULT 'approved' NOT NULL,
            created_by_ai BOOLEAN DEFAULT FALSE NOT NULL
        );
        """
        return self.execute_sql(sql_query, "Creating Grammar table")
    
    def create_lesson_category_table(self):
        """Create LessonCategory table"""
        sql_query = """
        CREATE TABLE IF NOT EXISTS lesson_category (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) UNIQUE NOT NULL,
            description TEXT,
            color_code VARCHAR(7) DEFAULT '#007bff',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        return self.execute_sql(sql_query, "Creating LessonCategory table")
    
    def create_lesson_table(self):
        """Create Lesson table"""
        sql_query = """
        CREATE TABLE IF NOT EXISTS lesson (
            id SERIAL PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            lesson_type VARCHAR(20) NOT NULL,
            category_id INTEGER REFERENCES lesson_category(id),
            difficulty_level INTEGER,
            estimated_duration INTEGER,
            order_index INTEGER DEFAULT 0,
            is_published BOOLEAN DEFAULT FALSE,
            allow_guest_access BOOLEAN DEFAULT FALSE NOT NULL,
            instruction_language VARCHAR(10) DEFAULT 'english' NOT NULL,
            thumbnail_url VARCHAR(255),
            background_image_url VARCHAR(1000),
            background_image_path VARCHAR(500),
            video_intro_url VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            price REAL DEFAULT 0.0 NOT NULL,
            is_purchasable BOOLEAN DEFAULT FALSE NOT NULL
        );
        """
        return self.execute_sql(sql_query, "Creating Lesson table")
    
    def create_lesson_prerequisite_table(self):
        """Create LessonPrerequisite table"""
        sql_query = """
        CREATE TABLE IF NOT EXISTS lesson_prerequisite (
            id SERIAL PRIMARY KEY,
            lesson_id INTEGER NOT NULL REFERENCES lesson(id),
            prerequisite_lesson_id INTEGER NOT NULL REFERENCES lesson(id),
            UNIQUE(lesson_id, prerequisite_lesson_id)
        );
        """
        return self.execute_sql(sql_query, "Creating LessonPrerequisite table")
    
    def create_lesson_page_table(self):
        """Create LessonPage table"""
        sql_query = """
        CREATE TABLE IF NOT EXISTS lesson_page (
            id SERIAL PRIMARY KEY,
            lesson_id INTEGER NOT NULL REFERENCES lesson(id),
            page_number INTEGER NOT NULL,
            title VARCHAR(200),
            description TEXT,
            UNIQUE(lesson_id, page_number)
        );
        """
        return self.execute_sql(sql_query, "Creating LessonPage table")
    
    def create_lesson_content_table(self):
        """Create LessonContent table"""
        sql_query = """
        CREATE TABLE IF NOT EXISTS lesson_content (
            id SERIAL PRIMARY KEY,
            lesson_id INTEGER NOT NULL REFERENCES lesson(id),
            content_type VARCHAR(20) NOT NULL,
            content_id INTEGER,
            title VARCHAR(200),
            content_text TEXT,
            media_url VARCHAR(255),
            order_index INTEGER DEFAULT 0,
            page_number INTEGER DEFAULT 1 NOT NULL,
            is_optional BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            file_path VARCHAR(500),
            file_size INTEGER,
            file_type VARCHAR(50),
            original_filename VARCHAR(255),
            is_interactive BOOLEAN DEFAULT FALSE,
            quiz_type VARCHAR(50) DEFAULT 'standard',
            max_attempts INTEGER DEFAULT 3,
            passing_score INTEGER DEFAULT 70,
            generated_by_ai BOOLEAN DEFAULT FALSE NOT NULL,
            ai_generation_details JSONB
        );
        """
        return self.execute_sql(sql_query, "Creating LessonContent table")
    
    def create_quiz_question_table(self):
        """Create QuizQuestion table"""
        sql_query = """
        CREATE TABLE IF NOT EXISTS quiz_question (
            id SERIAL PRIMARY KEY,
            lesson_content_id INTEGER NOT NULL REFERENCES lesson_content(id),
            question_type VARCHAR(50) NOT NULL,
            question_text TEXT NOT NULL,
            explanation TEXT,
            hint TEXT,
            difficulty_level INTEGER DEFAULT 1,
            points INTEGER DEFAULT 1,
            order_index INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        return self.execute_sql(sql_query, "Creating QuizQuestion table")
    
    def create_quiz_option_table(self):
        """Create QuizOption table"""
        sql_query = """
        CREATE TABLE IF NOT EXISTS quiz_option (
            id SERIAL PRIMARY KEY,
            question_id INTEGER NOT NULL REFERENCES quiz_question(id),
            option_text TEXT NOT NULL,
            is_correct BOOLEAN DEFAULT FALSE,
            order_index INTEGER DEFAULT 0,
            feedback TEXT
        );
        """
        return self.execute_sql(sql_query, "Creating QuizOption table")
    
    def create_user_quiz_answer_table(self):
        """Create UserQuizAnswer table"""
        sql_query = """
        CREATE TABLE IF NOT EXISTS user_quiz_answer (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES "user"(id),
            question_id INTEGER NOT NULL REFERENCES quiz_question(id),
            selected_option_id INTEGER REFERENCES quiz_option(id),
            text_answer TEXT,
            is_correct BOOLEAN DEFAULT FALSE,
            answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            attempts INTEGER DEFAULT 0 NOT NULL,
            UNIQUE(user_id, question_id)
        );
        """
        return self.execute_sql(sql_query, "Creating UserQuizAnswer table")
    
    def create_user_lesson_progress_table(self):
        """Create UserLessonProgress table"""
        sql_query = """
        CREATE TABLE IF NOT EXISTS user_lesson_progress (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES "user"(id),
            lesson_id INTEGER NOT NULL REFERENCES lesson(id),
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            is_completed BOOLEAN DEFAULT FALSE,
            progress_percentage INTEGER DEFAULT 0,
            time_spent INTEGER DEFAULT 0,
            last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            content_progress TEXT,
            UNIQUE(user_id, lesson_id)
        );
        """
        return self.execute_sql(sql_query, "Creating UserLessonProgress table")
    
    def create_lesson_purchase_table(self):
        """Create LessonPurchase table"""
        sql_query = """
        CREATE TABLE IF NOT EXISTS lesson_purchase (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES "user"(id),
            lesson_id INTEGER NOT NULL REFERENCES lesson(id),
            price_paid REAL NOT NULL,
            purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            stripe_payment_intent_id VARCHAR(100),
            UNIQUE(user_id, lesson_id)
        );
        """
        return self.execute_sql(sql_query, "Creating LessonPurchase table")
    
    def create_course_table(self):
        """Create Course table"""
        sql_query = """
        CREATE TABLE IF NOT EXISTS course (
            id SERIAL PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            background_image_url VARCHAR(255),
            is_published BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        return self.execute_sql(sql_query, "Creating Course table")
    
    def create_course_lessons_table(self):
        """Create course_lessons association table"""
        sql_query = """
        CREATE TABLE IF NOT EXISTS course_lessons (
            course_id INTEGER NOT NULL REFERENCES course(id),
            lesson_id INTEGER NOT NULL REFERENCES lesson(id),
            PRIMARY KEY (course_id, lesson_id)
        );
        """
        return self.execute_sql(sql_query, "Creating course_lessons association table")
    
    def create_social_auth_tables(self):
        """Create social authentication tables"""
        tables = [
            ("""
            CREATE TABLE IF NOT EXISTS social_auth_usersocialauth (
                id SERIAL PRIMARY KEY,
                provider VARCHAR(32) NOT NULL,
                uid VARCHAR(255) NOT NULL,
                extra_data TEXT,
                user_id INTEGER NOT NULL REFERENCES "user"(id),
                created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                modified TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(provider, uid)
            );
            """, "Creating social_auth_usersocialauth table"),
            
            ("""
            CREATE TABLE IF NOT EXISTS social_auth_nonce (
                id SERIAL PRIMARY KEY,
                server_url VARCHAR(255) NOT NULL,
                timestamp INTEGER NOT NULL,
                salt VARCHAR(65) NOT NULL,
                UNIQUE(server_url, timestamp, salt)
            );
            """, "Creating social_auth_nonce table"),
            
            ("""
            CREATE TABLE IF NOT EXISTS social_auth_association (
                id SERIAL PRIMARY KEY,
                server_url VARCHAR(255) NOT NULL,
                handle VARCHAR(255) NOT NULL,
                secret VARCHAR(255) NOT NULL,
                issued INTEGER NOT NULL,
                lifetime INTEGER NOT NULL,
                assoc_type VARCHAR(64) NOT NULL,
                UNIQUE(server_url, handle)
            );
            """, "Creating social_auth_association table"),
            
            ("""
            CREATE TABLE IF NOT EXISTS social_auth_code (
                id SERIAL PRIMARY KEY,
                email VARCHAR(254) NOT NULL,
                code VARCHAR(32) NOT NULL,
                verified BOOLEAN NOT NULL DEFAULT FALSE,
                timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(email, code)
            );
            """, "Creating social_auth_code table")
        ]
        
        success = True
        for sql_query, description in tables:
            if not self.execute_sql(sql_query, description):
                success = False
        return success
    
    def create_indexes(self):
        """Create performance indexes"""
        indexes = [
            ("CREATE INDEX IF NOT EXISTS idx_lesson_category ON lesson(category_id)", "lesson category index"),
            ("CREATE INDEX IF NOT EXISTS idx_lesson_content_lesson ON lesson_content(lesson_id)", "lesson content lesson index"),
            ("CREATE INDEX IF NOT EXISTS idx_lesson_content_page ON lesson_content(page_number)", "lesson content page index"),
            ("CREATE INDEX IF NOT EXISTS idx_quiz_question_content ON quiz_question(lesson_content_id)", "quiz question content index"),
            ("CREATE INDEX IF NOT EXISTS idx_quiz_option_question ON quiz_option(question_id)", "quiz option question index"),
            ("CREATE INDEX IF NOT EXISTS idx_user_progress_user ON user_lesson_progress(user_id)", "user progress user index"),
            ("CREATE INDEX IF NOT EXISTS idx_user_progress_lesson ON user_lesson_progress(lesson_id)", "user progress lesson index"),
            ("CREATE INDEX IF NOT EXISTS idx_lesson_purchase_user ON lesson_purchase(user_id)", "lesson purchase user index"),
            ("CREATE INDEX IF NOT EXISTS idx_lesson_prerequisite_lesson ON lesson_prerequisite(lesson_id)", "lesson prerequisite lesson index"),
            ("CREATE INDEX IF NOT EXISTS idx_lesson_prerequisite_prereq ON lesson_prerequisite(prerequisite_lesson_id)", "lesson prerequisite prereq index"),
            ("CREATE INDEX IF NOT EXISTS idx_social_auth_user ON social_auth_usersocialauth(user_id)", "social auth user index"),
        ]
        
        for sql_query, description in indexes:
            self.execute_sql(sql_query, f"Creating {description}")
    
    def create_admin_user(self, username="admin", email="admin@example.com", password="admin123"):
        """Create initial admin user"""
        if not self.cursor:
            logger.error("No database cursor available")
            return False
            
        password_hash = generate_password_hash(password)
        sql_query = """
        INSERT INTO "user" (username, email, password_hash, subscription_level, is_admin)
        VALUES (%s, %s, %s, 'premium', TRUE)
        ON CONFLICT (username) DO NOTHING;
        """
        try:
            self.cursor.execute(sql_query, (username, email, password_hash))
            logger.info(f"✓ Created admin user: {username}")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to create admin user: {e}")
            return False
    
    def create_sample_categories(self):
        """Create sample lesson categories"""
        if not self.cursor:
            logger.error("No database cursor available")
            return
            
        categories = [
            ("Hiragana", "Learn Japanese Hiragana characters", "#FF6B6B"),
            ("Katakana", "Learn Japanese Katakana characters", "#4ECDC4"),
            ("Kanji", "Learn Japanese Kanji characters", "#45B7D1"),
            ("Vocabulary", "Build your Japanese vocabulary", "#96CEB4"),
            ("Grammar", "Master Japanese grammar rules", "#FFEAA7"),
            ("Culture", "Explore Japanese culture", "#DDA0DD"),
        ]
        
        for name, description, color in categories:
            sql_query = """
            INSERT INTO lesson_category (name, description, color_code)
            VALUES (%s, %s, %s)
            ON CONFLICT (name) DO NOTHING;
            """
            try:
                self.cursor.execute(sql_query, (name, description, color))
                logger.info(f"✓ Created category: {name}")
            except Exception as e:
                logger.error(f"✗ Failed to create category {name}: {e}")
    
    def verify_database(self):
        """Verify database creation was successful"""
        logger.info("Verifying database structure...")
        
        # Check all tables exist
        expected_tables = [
            'user', 'kana', 'kanji', 'vocabulary', 'grammar', 'lesson_category',
            'lesson', 'lesson_prerequisite', 'lesson_page', 'lesson_content',
            'quiz_question', 'quiz_option', 'user_quiz_answer', 'user_lesson_progress',
            'lesson_purchase', 'course', 'course_lessons',
            'social_auth_usersocialauth', 'social_auth_nonce', 'social_auth_association', 'social_auth_code'
        ]
        
        missing_tables = []
        for table in expected_tables:
            if not self.table_exists(table):
                missing_tables.append(table)
        
        if missing_tables:
            logger.error(f"Missing tables: {missing_tables}")
            return False
        
        # Check record counts
        if not self.cursor:
            logger.error("No database cursor available for verification")
            return False
            
        self.cursor.execute("SELECT COUNT(*) FROM \"user\"")
        user_result = self.cursor.fetchone()
        user_count = user_result[0] if user_result else 0
        
        self.cursor.execute("SELECT COUNT(*) FROM lesson_category")
        category_result = self.cursor.fetchone()
        category_count = category_result[0] if category_result else 0
        
        logger.info(f"✓ Database verification complete:")
        logger.info(f"  - All {len(expected_tables)} tables created successfully")
        logger.info(f"  - {user_count} users created")
        logger.info(f"  - {category_count} lesson categories created")
        
        return True
    
    def create_database(self, drop_existing=False):
        """Main method to create the complete database"""
        logger.info("Starting local database creation process...")
        
        # Create database if it doesn't exist
        if not self.create_database_if_not_exists():
            return False
        
        if not self.connect():
            return False
        
        try:
            # Drop existing tables if requested
            if drop_existing:
                self.drop_all_tables()
            
            # Create all tables in correct order (respecting foreign keys)
            success = all([
                self.create_user_table(),
                self.create_kana_table(),
                self.create_kanji_table(),
                self.create_vocabulary_table(),
                self.create_grammar_table(),
                self.create_lesson_category_table(),
                self.create_lesson_table(),
                self.create_lesson_prerequisite_table(),
                self.create_lesson_page_table(),
                self.create_lesson_content_table(),
                self.create_quiz_question_table(),
                self.create_quiz_option_table(),
                self.create_user_quiz_answer_table(),
                self.create_user_lesson_progress_table(),
                self.create_lesson_purchase_table(),
                self.create_course_table(),
                self.create_course_lessons_table(),
                self.create_social_auth_tables(),
            ])
            
            if not success:
                logger.error("Failed to create some tables")
                return False
            
            # Create indexes for performance
            self.create_indexes()
            
            # Create initial data
            self.create_admin_user()
            self.create_sample_categories()
            
            # Verify everything was created correctly
            if self.verify_database():
                logger.info("🎉 Local database creation completed successfully!")
                return True
            else:
                logger.error("Database verification failed")
                return False
                
        except Exception as e:
            logger.error(f"Database creation failed: {e}")
            return False
        finally:
            if self.connection:
                self.connection.close()
                logger.info("Database connection closed")

def main():
    """Main execution function"""
    print("🚀 Japanese Learning Website - Local Database Creator")
    print("=" * 55)
    
    # Get database configuration from user
    print("Please provide your local PostgreSQL connection details:")
    host = input("Host (default: localhost): ").strip() or "localhost"
    port = input("Port (default: 5432): ").strip() or "5432"
    database = input("Database name (default: japanese_learning): ").strip() or "japanese_learning"
    username = input("Username (default: postgres): ").strip() or "postgres"
    password = input("Password: ").strip()
    
    try:
        port = int(port)
    except ValueError:
        print("Invalid port number. Using default 5432.")
        port = 5432
    
    DB_CONFIG = {
        'host': host,
        'database': database,
        'username': username,
        'password': password,
        'port': port
    }
    
    print(f"\nConnecting to: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    print(f"Username: {DB_CONFIG['username']}")
    
    # Ask user if they want to drop existing tables
    drop_existing = input("\n⚠️  Drop existing tables? (y/N): ").lower().strip() == 'y'
    
    if drop_existing:
        confirm = input("⚠️  This will DELETE ALL DATA. Are you sure? Type 'DELETE' to confirm: ")
        if confirm != 'DELETE':
            print("Operation cancelled.")
            return
    
    # Create database
    creator = LocalDatabaseCreator(**DB_CONFIG)
    success = creator.create_database(drop_existing=drop_existing)
    
    if success:
        print("\n✅ Local database creation completed successfully!")
        print("\nNext steps:")
        print("1. Set your DATABASE_URL environment variable:")
        print(f"   export DATABASE_URL=\"postgresql://{DB_CONFIG['username']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}\"")
        print("2. Or add to your .env file:")
        print(f"   DATABASE_URL=postgresql://{DB_CONFIG['username']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
        print("3. Run your Flask application:")
        print("   python run.py")
        print("\nAdmin user created:")
        print("  Username: admin")
        print("  Password: admin123")
        print("  (Please change this password after first login)")
    else:
        print("\n❌ Database creation failed. Check the logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
