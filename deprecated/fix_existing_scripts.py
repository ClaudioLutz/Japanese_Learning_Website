#!/usr/bin/env python3
"""
Fix existing lesson creation scripts to have correct Python path setup.
This script updates all scripts in lesson_creation_scripts/ to properly import the app module.
"""

import os
import glob

def fix_script_imports():
    """Fix Python path imports in all existing lesson creation scripts."""
    scripts_dir = "lesson_creation_scripts"
    
    if not os.path.exists(scripts_dir):
        print(f"❌ Scripts directory not found: {scripts_dir}")
        return
    
    # Find all Python scripts
    pattern = os.path.join(scripts_dir, "create_*_lesson.py")
    scripts = glob.glob(pattern)
    
    print(f"🔧 Found {len(scripts)} scripts to fix")
    
    fixed_count = 0
    error_count = 0
    
    for script_path in scripts:
        script_name = os.path.basename(script_path)
        print(f"   Fixing: {script_name}")
        
        try:
            # Read the script
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Fix the Python path setup
            old_path_setup = "# Add the app directory to Python path\nsys.path.insert(0, os.path.dirname(__file__))"
            new_path_setup = "# Add the project root directory to Python path\nsys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))"
            
            if old_path_setup in content:
                content = content.replace(old_path_setup, new_path_setup)
                
                # Write the fixed script back
                with open(script_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"   ✅ Fixed: {script_name}")
                fixed_count += 1
            else:
                print(f"   ⏭️  Skipped: {script_name} (already fixed or different format)")
                
        except Exception as e:
            print(f"   ❌ Error fixing {script_name}: {e}")
            error_count += 1
    
    print(f"\n📊 Summary:")
    print(f"   ✅ Fixed: {fixed_count} scripts")
    print(f"   ❌ Errors: {error_count} scripts")
    print(f"   📁 Total processed: {len(scripts)} scripts")
    
    if fixed_count > 0:
        print(f"\n🎉 Scripts fixed! You can now run: python run_all_lesson_scripts.py")

if __name__ == "__main__":
    fix_script_imports()
