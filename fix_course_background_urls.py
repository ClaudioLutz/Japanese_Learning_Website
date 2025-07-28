#!/usr/bin/env python3
"""
Script to fix existing course background URLs to use the proper format
that can be served by the uploaded_file route.
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
from app.models import Course
from flask import url_for

def fix_course_background_urls():
    """Fix existing course background URLs to use proper format."""
    app = create_app()
    
    with app.app_context():
        print("--- Fixing Course Background URLs ---")
        
        # Get all courses with background images
        courses = Course.query.filter(
            Course.background_image_url.isnot(None),
            Course.background_image_url != ''
        ).all()
        
        print(f"Found {len(courses)} courses with background images")
        
        fixed_count = 0
        
        for course in courses:
            print(f"\n--- Processing Course: {course.title} (ID: {course.id}) ---")
            print(f"Current background_image_url: {course.background_image_url}")
            
            # Check if the URL is already in the correct format
            if course.background_image_url.startswith('/uploads/'):
                print("✅ URL already in correct format")
                continue
            
            # Check if it's a relative path that needs to be converted
            if course.background_image_url.startswith('courses/backgrounds/'):
                # Convert relative path to proper URL manually
                new_url = f"/uploads/{course.background_image_url}"
                course.background_image_url = new_url
                
                print(f"🔧 Updated URL to: {new_url}")
                fixed_count += 1
            else:
                print(f"⚠️ Unknown URL format, skipping: {course.background_image_url}")
        
        if fixed_count > 0:
            db.session.commit()
            print(f"\n✅ Fixed {fixed_count} course background URLs")
        else:
            print(f"\n✅ No URLs needed fixing")
        
        print("\n--- Final Status ---")
        for course in courses:
            print(f"Course '{course.title}': {course.background_image_url}")

if __name__ == "__main__":
    fix_course_background_urls()
