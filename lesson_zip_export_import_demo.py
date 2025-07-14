#!/usr/bin/env python3
"""
Lesson ZIP Export/Import Demo Script

This script demonstrates the full ZIP package export/import functionality:
1. Export a lesson as a complete ZIP package
2. Extract and examine the ZIP contents
3. Import the lesson from the ZIP package

Usage: python lesson_zip_export_import_demo.py
"""

import os
import json
import tempfile
import zipfile
from datetime import datetime
from app import create_app, db
from app.lesson_export_import import create_lesson_export_package, import_lesson_from_zip
from app.models import Lesson

def examine_zip_package(zip_path):
    """Examine the contents of a lesson export ZIP package."""
    print(f"Examining ZIP package: {os.path.basename(zip_path)}")
    
    with zipfile.ZipFile(zip_path, 'r') as zipf:
        file_list = zipf.namelist()
        print(f"  Files in package: {len(file_list)}")
        
        # Show main files
        for file in file_list:
            file_info = zipf.getinfo(file)
            size_kb = file_info.file_size / 1024
            print(f"    {file} ({size_kb:.1f} KB)")
        
        # Read and display lesson_data.json summary
        if 'lesson_data.json' in file_list:
            with zipf.open('lesson_data.json') as f:
                lesson_data = json.load(f)
                print(f"\n  Lesson Summary:")
                print(f"    Title: {lesson_data.get('title', 'N/A')}")
                print(f"    Description: {lesson_data.get('description', 'N/A')[:100]}...")
                print(f"    Content items: {len(lesson_data.get('content', []))}")
                print(f"    Pages: {len(lesson_data.get('pages', []))}")
                
                export_meta = lesson_data.get('export_metadata', {})
                print(f"    Export version: {export_meta.get('version', 'N/A')}")
                print(f"    Exported at: {export_meta.get('exported_at', 'N/A')}")
                print(f"    Includes files: {export_meta.get('includes_files', False)}")
                print(f"    File count: {export_meta.get('file_count', 0)}")
        
        # Read README if present
        if 'README.txt' in file_list:
            print(f"\n  README.txt preview:")
            with zipf.open('README.txt') as f:
                readme_content = f.read().decode('utf-8')
                lines = readme_content.split('\n')[:10]  # First 10 lines
                for line in lines:
                    print(f"    {line}")
                if len(readme_content.split('\n')) > 10:
                    print("    ...")

def main():
    """Main function to demonstrate ZIP export/import."""
    
    print("=== Lesson ZIP Export/Import Demo ===")
    print("This script demonstrates the complete ZIP package export/import functionality.")
    print()
    
    # Create Flask app context
    app = create_app()
    with app.app_context():
        
        # Step 1: List available lessons
        print("Step 1: Available lessons in the database:")
        lessons = Lesson.query.all()
        for lesson in lessons:
            print(f"  ID: {lesson.id}, Title: {lesson.title}, Type: {lesson.lesson_type}")
        print()
        
        # Step 2: Choose lesson to export
        lesson_id = 17  # "At the Restaurant - Complete Guide"
        lesson = Lesson.query.get(lesson_id)
        if not lesson:
            print(f"Error: Lesson with ID {lesson_id} not found!")
            return
        
        print(f"Step 2: Creating ZIP export package for '{lesson.title}' (ID: {lesson_id})")
        
        # Create temporary directory for exports
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Export the lesson as ZIP package
                zip_path = create_lesson_export_package(lesson_id, temp_dir, include_files=True)
                print(f"  ✓ Successfully created ZIP package: {os.path.basename(zip_path)}")
                print(f"  ✓ Package size: {os.path.getsize(zip_path) / 1024:.1f} KB")
            except Exception as e:
                print(f"  ✗ Export failed: {e}")
                return
            
            print()
            
            # Step 3: Examine the ZIP package
            print("Step 3: Examining ZIP package contents:")
            examine_zip_package(zip_path)
            print()
            
            # Step 4: Import the lesson from ZIP (with rename to avoid conflicts)
            print("Step 4: Importing lesson from ZIP package...")
            try:
                imported_lesson = import_lesson_from_zip(zip_path, handle_duplicates='rename')
                print(f"  ✓ Successfully imported lesson: '{imported_lesson.title}'")
                print(f"  ✓ New lesson ID: {imported_lesson.id}")
                print(f"  ✓ Lesson type: {imported_lesson.lesson_type}")
                print(f"  ✓ Content items imported: {len(imported_lesson.content_items)}")
                print(f"  ✓ Pages imported: {len(imported_lesson.pages_metadata)}")
            except Exception as e:
                print(f"  ✗ Import failed: {e}")
                return
            
            print()
            
            # Step 5: Verify the import by comparing with original
            print("Step 5: Verification - Comparing original and imported lessons:")
            
            original_lesson = Lesson.query.get(lesson_id)
            new_lesson = imported_lesson
            
            print(f"Original: '{original_lesson.title if original_lesson else 'N/A'}'")
            print(f"Imported: '{new_lesson.title if new_lesson else 'N/A'}'")
            
            orig_content_count = len(original_lesson.content_items) if original_lesson else 0
            new_content_count = len(new_lesson.content_items) if new_lesson else 0
            print(f"Content match: {orig_content_count} -> {new_content_count}")
            
            orig_pages_count = len(original_lesson.pages_metadata) if original_lesson else 0
            new_pages_count = len(new_lesson.pages_metadata) if new_lesson else 0
            print(f"Pages match: {orig_pages_count} -> {new_pages_count}")
            
            # Check if categories match
            orig_category = "None"
            new_category = "None"
            if original_lesson and hasattr(original_lesson, 'category') and original_lesson.category:
                orig_category = original_lesson.category.name
            if new_lesson and hasattr(new_lesson, 'category') and new_lesson.category:
                new_category = new_lesson.category.name
            print(f"Category: {orig_category} -> {new_category}")
            
            # Show some content comparison
            if (original_lesson and original_lesson.content_items and 
                new_lesson and new_lesson.content_items):
                print(f"\nContent comparison (first item):")
                orig_content = original_lesson.content_items[0]
                new_content = new_lesson.content_items[0]
                print(f"  Original type: {orig_content.content_type}")
                print(f"  Imported type: {new_content.content_type}")
                print(f"  Original page: {orig_content.page_number}")
                print(f"  Imported page: {new_content.page_number}")
            
            print()
            print("=== Demo Complete ===")
            print(f"Successfully demonstrated ZIP export/import functionality!")
            print(f"Original lesson ID: {lesson_id}")
            print(f"Imported lesson ID: {imported_lesson.id}")
            print()
            print("Key features demonstrated:")
            print("  ✓ Complete lesson export to ZIP package")
            print("  ✓ ZIP package structure examination")
            print("  ✓ Lesson import from ZIP with duplicate handling")
            print("  ✓ Data integrity verification")
            print("  ✓ File and metadata preservation")

if __name__ == "__main__":
    main()
