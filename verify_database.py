#!/usr/bin/env python3
"""
Database Verification Script
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def verify_database():
    """Verify the database setup"""
    try:
        from app import create_app, db
        from app.models import User, Lesson, Course
        
        app = create_app()
        with app.app_context():
            user_count = User.query.count()
            lesson_count = Lesson.query.count()
            course_count = Course.query.count()
            
            print('Database verification successful!')
            print(f'   - Users: {user_count}')
            print(f'   - Lessons: {lesson_count}')
            print(f'   - Courses: {course_count}')
            print('Fresh PostgreSQL database setup completed successfully!')
            return True
            
    except Exception as e:
        print(f'Database verification failed: {e}')
        return False

if __name__ == "__main__":
    success = verify_database()
    if success:
        print("\nNext steps:")
        print("1. Create an admin user: python create_admin.py")
        print("2. Set up Google OAuth credentials in .env")
        print("3. Test the application: python run.py")
