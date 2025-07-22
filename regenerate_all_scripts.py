#!/usr/bin/env python3
"""
Regenerate all lesson scripts with proper fixes.
This script will delete existing generated scripts and create new ones that work correctly.
"""

import os
import glob
import shutil

def clean_existing_scripts():
    """Remove all existing generated scripts except the original template."""
    scripts_dir = "lesson_creation_scripts"
    
    if not os.path.exists(scripts_dir):
        print(f"❌ Scripts directory not found: {scripts_dir}")
        return
    
    # Find all Python scripts except the ones we want to keep
    pattern = os.path.join(scripts_dir, "create_*_lesson.py")
    scripts = glob.glob(pattern)
    
    # Keep these original scripts
    keep_scripts = [
        "create_comprehensive_kitsune_lesson.py",
        "create_comprehensive_multimedia_lesson.py", 
        "create_japanese_cities_lesson.py",
        "create_japanese_cuisine_lesson.py",
        "create_japanese_festivals_lesson.py",
        "create_travel_japanese_lesson.py"
    ]
    
    deleted_count = 0
    kept_count = 0
    
    for script_path in scripts:
        script_name = os.path.basename(script_path)
        
        if script_name in keep_scripts:
            print(f"   ⏭️  Keeping: {script_name}")
            kept_count += 1
        else:
            try:
                os.remove(script_path)
                print(f"   🗑️  Deleted: {script_name}")
                deleted_count += 1
            except Exception as e:
                print(f"   ❌ Error deleting {script_name}: {e}")
    
    print(f"\n📊 Cleanup Summary:")
    print(f"   🗑️  Deleted: {deleted_count} scripts")
    print(f"   ⏭️  Kept: {kept_count} original scripts")
    
    return deleted_count > 0

def main():
    """Main execution function."""
    print("🧹 Cleaning up existing generated scripts...")
    print("=" * 50)
    
    # Clean existing scripts
    if clean_existing_scripts():
        print(f"\n✅ Cleanup complete!")
        print(f"\n🚀 Now run: python generate_all_lesson_scripts.py")
        print(f"   This will generate new, working scripts for all topics.")
    else:
        print(f"\n⚠️  No scripts were deleted.")

if __name__ == "__main__":
    main()
