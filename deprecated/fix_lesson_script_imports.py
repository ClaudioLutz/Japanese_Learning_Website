#!/usr/bin/env python3
"""
Fix import issues in lesson creation scripts that cause UnboundLocalError.
The issue is duplicate imports of QuizQuestion and QuizOption causing scoping conflicts.
"""

import os
import glob
import re

def fix_script_imports(script_path):
    """Fix import issues in a single script."""
    print(f"Fixing imports in: {os.path.basename(script_path)}")
    
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if this script has the problematic pattern
    has_top_level_import = 'from app.models import Lesson, LessonContent, QuizQuestion, QuizOption' in content
    has_function_import = 'from app.models import UserQuizAnswer, QuizQuestion, QuizOption' in content
    
    if has_top_level_import and has_function_import:
        print(f"  Found duplicate imports - fixing...")
        
        # Replace the function-level import to only import UserQuizAnswer
        # since QuizQuestion and QuizOption are already imported at the top
        content = content.replace(
            'from app.models import UserQuizAnswer, QuizQuestion, QuizOption',
            'from app.models import UserQuizAnswer'
        )
        
        # Also need to import UserLessonProgress at the top level to avoid similar issues
        if 'from app.models import UserLessonProgress' in content:
            # Remove the function-level import
            content = content.replace(
                'from app.models import UserLessonProgress',
                '# UserLessonProgress imported at top level'
            )
            
            # Add it to the top-level import
            content = content.replace(
                'from app.models import Lesson, LessonContent, QuizQuestion, QuizOption',
                'from app.models import Lesson, LessonContent, QuizQuestion, QuizOption, UserQuizAnswer, UserLessonProgress'
            )
        else:
            # Just add UserQuizAnswer to the top-level import
            content = content.replace(
                'from app.models import Lesson, LessonContent, QuizQuestion, QuizOption',
                'from app.models import Lesson, LessonContent, QuizQuestion, QuizOption, UserQuizAnswer'
            )
        
        # Write the fixed content back
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"  ✅ Fixed imports in {os.path.basename(script_path)}")
        return True
    else:
        print(f"  ✅ No import issues found in {os.path.basename(script_path)}")
        return False

def main():
    """Fix imports in all lesson creation scripts."""
    print("🔧 Fixing import issues in lesson creation scripts...")
    print("=" * 60)
    
    # Find all lesson creation scripts
    scripts_dir = "lesson_creation_scripts"
    if not os.path.exists(scripts_dir):
        print(f"❌ Scripts directory not found: {scripts_dir}")
        return
    
    # Find all Python scripts that start with "create_" and end with "_lesson.py"
    pattern = os.path.join(scripts_dir, "create_*_lesson.py")
    scripts = glob.glob(pattern)
    
    if not scripts:
        print("❌ No lesson creation scripts found.")
        return
    
    print(f"Found {len(scripts)} lesson creation scripts to check.")
    print()
    
    fixed_count = 0
    for script_path in sorted(scripts):
        if fix_script_imports(script_path):
            fixed_count += 1
    
    print()
    print("=" * 60)
    print(f"📊 IMPORT FIX SUMMARY")
    print("=" * 60)
    print(f"✅ Scripts checked: {len(scripts)}")
    print(f"🔧 Scripts fixed: {fixed_count}")
    print(f"✅ Scripts already correct: {len(scripts) - fixed_count}")
    
    if fixed_count > 0:
        print(f"\n🎉 Fixed import issues in {fixed_count} scripts!")
        print("The UnboundLocalError should now be resolved.")
    else:
        print(f"\n✅ All scripts already have correct imports.")

if __name__ == "__main__":
    main()
