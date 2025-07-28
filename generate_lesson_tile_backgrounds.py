#!/usr/bin/env python3
"""
Script to generate background images for lesson tiles and course tiles using DALL-E.
Only generates backgrounds for lessons and courses that don't already have them.
"""
import os
import sys
import urllib.request
from datetime import datetime
import uuid

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
from app.models import Lesson, Course
from app.ai_services import AILessonContentGenerator

def download_background_image(image_url, item_id, app, item_type="lesson"):
    """Download and save background image for a lesson or course."""
    try:
        print(f"  Downloading background image from: {image_url}")
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        filename = f"{item_type}_{item_id}_background_{timestamp}_{unique_id}.png"
        
        # Create target directory
        upload_folder = app.config.get('UPLOAD_FOLDER', 'app/static/uploads')
        if item_type == "course":
            target_dir = os.path.join(upload_folder, 'courses', 'backgrounds')
        else:
            target_dir = os.path.join(upload_folder, 'lessons', 'backgrounds')
        os.makedirs(target_dir, exist_ok=True)
        
        # Save file using urllib
        final_path = os.path.join(target_dir, filename)
        urllib.request.urlretrieve(image_url, final_path)
        
        # Return relative path for database storage
        if item_type == "course":
            relative_path = os.path.join('courses', 'backgrounds', filename).replace('\\', '/')
        else:
            relative_path = os.path.join('lessons', 'backgrounds', filename).replace('\\', '/')
        
        print(f"  ✅ Background image saved to: {relative_path}")
        return relative_path, os.path.getsize(final_path)
        
    except Exception as e:
        print(f"  ❌ Error downloading background image: {e}")
        return None, 0

def get_lessons_without_backgrounds():
    """Get all lessons that don't have background images."""
    return Lesson.query.filter(
        (Lesson.background_image_url.is_(None)) | 
        (Lesson.background_image_url == '') |
        (Lesson.background_image_path.is_(None)) | 
        (Lesson.background_image_path == '')
    ).all()

def get_courses_without_backgrounds():
    """Get all courses that don't have background images."""
    return Course.query.filter(
        (Course.background_image_url.is_(None)) | 
        (Course.background_image_url == '')
    ).all()

def generate_backgrounds_for_lessons(app):
    """Generate background images for lessons that don't have them."""
    with app.app_context():
        print("--- Generating Lesson Tile Background Images ---")
        
        # Check for API key
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            print("❌ OPENAI_API_KEY not found in environment variables.")
            return 0, 1
        
        # Initialize AI generator
        generator = AILessonContentGenerator()
        if not generator.client:
            print("❌ AI Generator could not be initialized. Check your API key.")
            return 0, 1
        
        print("✅ AI Generator Initialized")
        
        # Get lessons without backgrounds
        lessons_without_backgrounds = get_lessons_without_backgrounds()
        
        if not lessons_without_backgrounds:
            print("✅ All lessons already have background images!")
            return 0, 0
        
        print(f"Found {len(lessons_without_backgrounds)} lessons without background images.")
        
        success_count = 0
        error_count = 0
        
        for lesson in lessons_without_backgrounds:
            print(f"\n--- Processing Lesson: {lesson.title} (ID: {lesson.id}) ---")
            
            try:
                # Generate background image
                print(f"🎨 Generating background image...")
                
                background_result = generator.generate_lesson_tile_background(
                    lesson.title,
                    lesson.description or "Japanese language lesson",
                    lesson.difficulty_level or 1
                )
                
                if "error" in background_result:
                    print(f"❌ Error generating background: {background_result['error']}")
                    error_count += 1
                    continue
                
                image_url = background_result['image_url']
                print(f"🖼️ Background image URL generated: {image_url}")
                
                # Download the background image
                file_path, file_size = download_background_image(image_url, lesson.id, app)
                
                if file_path:
                    # Update lesson with background image info
                    lesson.background_image_url = image_url
                    lesson.background_image_path = file_path
                    
                    db.session.commit()
                    
                    print(f"✅ Background image added to lesson '{lesson.title}'")
                    success_count += 1
                else:
                    print(f"❌ Failed to download background image for lesson '{lesson.title}'")
                    error_count += 1
                    
            except Exception as e:
                print(f"❌ Error processing lesson '{lesson.title}': {e}")
                error_count += 1
                db.session.rollback()
        
        print(f"\n--- Background Generation Complete ---")
        print(f"✅ Successfully generated backgrounds for {success_count} lessons")
        if error_count > 0:
            print(f"❌ Failed to generate backgrounds for {error_count} lessons")
        
        # Show final status
        remaining_lessons = get_lessons_without_backgrounds()
        if not remaining_lessons:
            print("🎉 All lessons now have background images!")
        else:
            print(f"📝 {len(remaining_lessons)} lessons still need background images")
        
        return success_count, error_count

def generate_backgrounds_for_courses(app):
    """Generate background images for courses that don't have them."""
    with app.app_context():
        print("\n--- Generating Course Background Images ---")
        
        # Check for API key
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            print("❌ OPENAI_API_KEY not found in environment variables.")
            return 0, 1
        
        # Initialize AI generator
        generator = AILessonContentGenerator()
        if not generator.client:
            print("❌ AI Generator could not be initialized. Check your API key.")
            return 0, 1
        
        print("✅ AI Generator Initialized")
        
        # Get courses without backgrounds
        courses_without_backgrounds = get_courses_without_backgrounds()
        
        if not courses_without_backgrounds:
            print("✅ All courses already have background images!")
            return 0, 0
        
        print(f"Found {len(courses_without_backgrounds)} courses without background images.")
        
        success_count = 0
        error_count = 0
        
        for course in courses_without_backgrounds:
            print(f"\n--- Processing Course: {course.title} (ID: {course.id}) ---")
            
            try:
                # Generate background image for course
                print(f"🎨 Generating course background image...")
                
                # Create a course-specific description for background generation
                course_description = f"Japanese language course: {course.title}. {course.description or 'Comprehensive Japanese learning course'}"
                
                background_result = generator.generate_lesson_tile_background(
                    course.title,
                    course_description,
                    2  # Default difficulty level for courses
                )
                
                if "error" in background_result:
                    print(f"❌ Error generating background: {background_result['error']}")
                    error_count += 1
                    continue
                
                image_url = background_result['image_url']
                print(f"🖼️ Background image URL generated: {image_url}")
                
                # Download the background image
                file_path, file_size = download_background_image(image_url, course.id, app, "course")
                
                if file_path:
                    # Update course with background image info
                    # For courses, we need to store the URL that can be served by the uploaded_file route
                    course.background_image_url = f"/uploads/{file_path}"
                    
                    db.session.commit()
                    
                    print(f"✅ Background image added to course '{course.title}'")
                    success_count += 1
                else:
                    print(f"❌ Failed to download background image for course '{course.title}'")
                    error_count += 1
                    
            except Exception as e:
                print(f"❌ Error processing course '{course.title}': {e}")
                error_count += 1
                db.session.rollback()
        
        print(f"\n--- Course Background Generation Complete ---")
        print(f"✅ Successfully generated backgrounds for {success_count} courses")
        if error_count > 0:
            print(f"❌ Failed to generate backgrounds for {error_count} courses")
        
        # Show final status
        remaining_courses = get_courses_without_backgrounds()
        if not remaining_courses:
            print("🎉 All courses now have background images!")
        else:
            print(f"📝 {len(remaining_courses)} courses still need background images")
        
        return success_count, error_count

def main():
    """Main function to run the background generation."""
    # Check for API key
    if 'OPENAI_API_KEY' not in os.environ:
        print("❌ Error: OPENAI_API_KEY environment variable not set.")
        print("Please add your OpenAI API key to your .env file.")
        sys.exit(1)
    
    # Create Flask app
    app = create_app()
    
    print("=== Background Image Generation for Lessons and Courses ===")
    
    # Run the background generation for lessons
    lesson_success, lesson_errors = generate_backgrounds_for_lessons(app)
    
    # Run the background generation for courses
    course_success, course_errors = generate_backgrounds_for_courses(app)
    
    # Final summary
    print(f"\n=== Final Summary ===")
    print(f"✅ Lessons: {lesson_success} backgrounds generated successfully")
    print(f"✅ Courses: {course_success} backgrounds generated successfully")
    if lesson_errors > 0 or course_errors > 0:
        print(f"❌ Total errors: {lesson_errors + course_errors}")
    print("🎉 Background generation complete!")

if __name__ == "__main__":
    main()
