#!/usr/bin/env python3
"""
Fresh Database Setup Script for Japanese Learning Website
This script will:
1. Test PostgreSQL connection
2. Initialize Flask-Migrate
3. Run all migrations to create the complete database schema
"""

import os
import sys
import subprocess
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_postgres_connection():
    """Test if we can connect to PostgreSQL"""
    try:
        import psycopg2
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL not found in environment variables")
            return False
        
        print(f"🔍 Testing connection to: {database_url.split('@')[1] if '@' in database_url else 'database'}")
        conn = psycopg2.connect(database_url)
        conn.close()
        print("✅ PostgreSQL connection successful!")
        return True
    except ImportError:
        print("❌ psycopg2 not installed. Install with: pip install psycopg2-binary")
        return False
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("\n📋 Make sure you have:")
        print("1. Created the PostgreSQL database using create_fresh_postgres_db.sql")
        print("2. Updated the DATABASE_URL in .env file")
        print("3. PostgreSQL service is running")
        return False

def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully!")
        if result.stdout:
            print(f"Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed!")
        print(f"Error: {e.stderr.strip() if e.stderr else str(e)}")
        return False

def setup_database():
    """Set up the database with all migrations"""
    print("🚀 Starting Fresh Database Setup for Japanese Learning Website")
    print("=" * 60)
    
    # Test database connection first
    if not test_postgres_connection():
        return False
    
    # Check if migrations directory exists
    if not os.path.exists('migrations'):
        print("\n📁 Migrations directory not found. Initializing Flask-Migrate...")
        if not run_command('flask db init', 'Initialize Flask-Migrate'):
            return False
    else:
        print("\n📁 Migrations directory found")
    
    # Check if we need to stamp the database
    print("\n🔍 Checking migration status...")
    result = subprocess.run('flask db current', shell=True, capture_output=True, text=True)
    
    if "No current revision" in result.stdout or result.returncode != 0:
        print("📌 Database has no migration history. Applying all migrations...")
        
        # Apply all migrations
        if not run_command('flask db upgrade', 'Apply all migrations'):
            return False
    else:
        print(f"📌 Current migration: {result.stdout.strip()}")
        print("🔄 Ensuring database is up to date...")
        if not run_command('flask db upgrade', 'Update database to latest migration'):
            return False
    
    # Verify the setup
    print("\n🔍 Verifying database setup...")
    try:
        # Import Flask app and test database
        from app import create_app, db
        from app.models import User, Lesson, Course  # Import some key models
        
        app = create_app()
        with app.app_context():
            # Test if we can query the database
            user_count = User.query.count()
            lesson_count = Lesson.query.count()
            course_count = Course.query.count()
            
            print(f"✅ Database verification successful!")
            print(f"   - Users: {user_count}")
            print(f"   - Lessons: {lesson_count}")
            print(f"   - Courses: {course_count}")
            
    except Exception as e:
        print(f"⚠️  Database verification failed: {e}")
        print("   The database was created but there might be an issue with the models.")
        return False
    
    print("\n🎉 Fresh PostgreSQL database setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Create an admin user: python create_admin.py")
    print("2. Set up Google OAuth credentials in .env")
    print("3. Test the application: python run.py")
    
    return True

if __name__ == "__main__":
    success = setup_database()
    sys.exit(0 if success else 1)
