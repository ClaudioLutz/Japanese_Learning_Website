#!/usr/bin/env python3
"""
Fix Lesson Script Errors

This script fixes the two main issues causing lesson script failures:
1. JLPT level type mismatch (string "N4" vs integer 4)
2. Import path issues in lesson creation scripts

The script will:
- Create a utility function to convert JLPT levels
- Update the AI services to handle JLPT level conversion
- Fix import paths in problematic scripts
"""

import os
import sys
import re
from pathlib import Path

def convert_jlpt_level_to_int(jlpt_level):
    """
    Convert JLPT level from string format (N4, N3, etc.) to integer format (4, 3, etc.)
    
    Args:
        jlpt_level: String like "N4", "N3" or integer like 4, 3
    
    Returns:
        Integer representation of JLPT level
    """
    if isinstance(jlpt_level, int):
        return jlpt_level
    
    if isinstance(jlpt_level, str):
        # Handle formats like "N4", "n4", "4"
        jlpt_level = jlpt_level.upper().strip()
        if jlpt_level.startswith('N'):
            try:
                return int(jlpt_level[1:])
            except ValueError:
                pass
        else:
            try:
                return int(jlpt_level)
            except ValueError:
                pass
    
    # Default to N5 (beginner level) if conversion fails
    return 5

def fix_ai_services():
    """Fix the AI services to properly handle JLPT level conversion"""
    ai_services_path = Path("app/ai_services.py")
    
    if not ai_services_path.exists():
        print(f"❌ {ai_services_path} not found")
        return False
    
    print(f"🔧 Fixing JLPT level handling in {ai_services_path}")
    
    # Read the current content
    with open(ai_services_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add the utility function at the top after imports
    utility_function = '''
def convert_jlpt_level_to_int(jlpt_level):
    """
    Convert JLPT level from string format (N4, N3, etc.) to integer format (4, 3, etc.)
    
    Args:
        jlpt_level: String like "N4", "N3" or integer like 4, 3
    
    Returns:
        Integer representation of JLPT level
    """
    if isinstance(jlpt_level, int):
        return jlpt_level
    
    if isinstance(jlpt_level, str):
        # Handle formats like "N4", "n4", "4"
        jlpt_level = jlpt_level.upper().strip()
        if jlpt_level.startswith('N'):
            try:
                return int(jlpt_level[1:])
            except ValueError:
                pass
        else:
            try:
                return int(jlpt_level)
            except ValueError:
                pass
    
    # Default to N5 (beginner level) if conversion fails
    return 5

'''
    
    # Insert the utility function after the imports
    import_end = content.find('class AILessonContentGenerator:')
    if import_end != -1:
        content = content[:import_end] + utility_function + content[import_end:]
    
    # Fix the generate_kanji_data method to use integer JLPT levels
    kanji_method_pattern = r'(def generate_kanji_data\(self, kanji_character, jlpt_level\):.*?)"jlpt_level": (\{jlpt_level\})'
    kanji_replacement = r'\1"jlpt_level": {convert_jlpt_level_to_int(jlpt_level)}'
    content = re.sub(kanji_method_pattern, kanji_replacement, content, flags=re.DOTALL)
    
    # Fix the generate_vocabulary_data method
    vocab_method_pattern = r'(def generate_vocabulary_data\(self, word, jlpt_level\):.*?)"jlpt_level": (\{jlpt_level\})'
    vocab_replacement = r'\1"jlpt_level": {convert_jlpt_level_to_int(jlpt_level)}'
    content = re.sub(vocab_method_pattern, vocab_replacement, content, flags=re.DOTALL)
    
    # Fix the generate_grammar_data method
    grammar_method_pattern = r'(def generate_grammar_data\(self, grammar_point, jlpt_level\):.*?)"jlpt_level": (\{jlpt_level\})'
    grammar_replacement = r'\1"jlpt_level": {convert_jlpt_level_to_int(jlpt_level)}'
    content = re.sub(grammar_method_pattern, grammar_replacement, content, flags=re.DOTALL)
    
    # Write the updated content
    with open(ai_services_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Fixed JLPT level handling in {ai_services_path}")
    return True

def fix_lesson_script_imports():
    """Fix import issues in lesson creation scripts"""
    scripts_dir = Path("lesson_creation_scripts")
    
    if not scripts_dir.exists():
        print(f"❌ {scripts_dir} directory not found")
        return False
    
    # Find all Python scripts in the directory
    script_files = list(scripts_dir.glob("*.py"))
    
    print(f"🔧 Fixing imports in {len(script_files)} lesson creation scripts")
    
    fixed_count = 0
    
    for script_path in script_files:
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Fix common import issues
            
            # Fix: from app import create_app, db
            # Should be: sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
            if 'from app import create_app, db' in content and 'sys.path.insert(0' not in content:
                # Add the path insertion before the app import
                import_fix = '''import os
import sys
from datetime import datetime

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

'''
                # Replace the existing imports
                content = re.sub(r'import os\nimport sys\nfrom datetime import datetime\n\n', '', content)
                content = re.sub(r'from app import', import_fix + 'from app import', content)
            
            # Fix: sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))
            # Should be: sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
            content = re.sub(
                r"sys\.path\.insert\(0, os\.path\.join\(os\.path\.dirname\(__file__\), 'app'\)\)",
                "sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))",
                content
            )
            
            # Fix JLPT level usage in scripts - convert string levels to integers
            # Look for patterns like ('狐', 'N4') and convert to ('狐', 4)
            def convert_jlpt_tuple(match):
                char = match.group(1)
                level = match.group(2)
                if level.startswith('N'):
                    level_int = level[1:]
                    return f"('{char}', {level_int})"
                return match.group(0)
            
            content = re.sub(r"\('([^']+)', 'N(\d)'\)", convert_jlpt_tuple, content)
            
            # Fix direct JLPT level assignments
            content = re.sub(r"jlpt_level='N(\d)'", r"jlpt_level=\1", content)
            content = re.sub(r'jlpt_level="N(\d)"', r"jlpt_level=\1", content)
            
            # Only write if content changed
            if content != original_content:
                with open(script_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"  ✅ Fixed {script_path.name}")
                fixed_count += 1
            
        except Exception as e:
            print(f"  ❌ Error fixing {script_path.name}: {e}")
    
    print(f"✅ Fixed imports in {fixed_count} scripts")
    return True

def create_jlpt_conversion_utility():
    """Create a standalone utility file for JLPT level conversion"""
    utility_path = Path("app/jlpt_utils.py")
    
    utility_content = '''"""
JLPT Level Conversion Utilities

This module provides utilities for converting between different JLPT level formats.
"""

def convert_jlpt_level_to_int(jlpt_level):
    """
    Convert JLPT level from string format (N4, N3, etc.) to integer format (4, 3, etc.)
    
    Args:
        jlpt_level: String like "N4", "N3" or integer like 4, 3
    
    Returns:
        Integer representation of JLPT level
    """
    if isinstance(jlpt_level, int):
        return jlpt_level
    
    if isinstance(jlpt_level, str):
        # Handle formats like "N4", "n4", "4"
        jlpt_level = jlpt_level.upper().strip()
        if jlpt_level.startswith('N'):
            try:
                return int(jlpt_level[1:])
            except ValueError:
                pass
        else:
            try:
                return int(jlpt_level)
            except ValueError:
                pass
    
    # Default to N5 (beginner level) if conversion fails
    return 5

def convert_int_to_jlpt_level(level_int):
    """
    Convert integer JLPT level to string format
    
    Args:
        level_int: Integer like 4, 3, 2, 1
    
    Returns:
        String representation like "N4", "N3", etc.
    """
    if isinstance(level_int, int) and 1 <= level_int <= 5:
        return f"N{level_int}"
    return "N5"  # Default to N5

def validate_jlpt_level(jlpt_level):
    """
    Validate that a JLPT level is valid (N1-N5 or 1-5)
    
    Args:
        jlpt_level: JLPT level in any format
    
    Returns:
        Boolean indicating if the level is valid
    """
    try:
        level_int = convert_jlpt_level_to_int(jlpt_level)
        return 1 <= level_int <= 5
    except:
        return False
'''
    
    with open(utility_path, 'w', encoding='utf-8') as f:
        f.write(utility_content)
    
    print(f"✅ Created JLPT utility file: {utility_path}")
    return True

def main():
    """Main function to fix all lesson script errors"""
    print("🔧 Lesson Script Error Fixer")
    print("=" * 50)
    print()
    print("This script will fix the following issues:")
    print("1. JLPT level type mismatch (string vs integer)")
    print("2. Import path issues in lesson creation scripts")
    print("3. Create utility functions for JLPT level conversion")
    print()
    
    success_count = 0
    total_fixes = 3
    
    # Fix 1: Create JLPT utility functions
    print("🔧 Step 1: Creating JLPT conversion utilities...")
    if create_jlpt_conversion_utility():
        success_count += 1
    
    # Fix 2: Update AI services
    print("\n🔧 Step 2: Fixing AI services JLPT level handling...")
    if fix_ai_services():
        success_count += 1
    
    # Fix 3: Fix lesson script imports
    print("\n🔧 Step 3: Fixing lesson script imports...")
    if fix_lesson_script_imports():
        success_count += 1
    
    print(f"\n{'='*50}")
    print(f"✅ Completed {success_count}/{total_fixes} fixes successfully!")
    
    if success_count == total_fixes:
        print("\n🎉 All fixes applied successfully!")
        print("\nYou can now run the lesson scripts again:")
        print("  python run_all_lesson_scripts.py --skip-existing")
        print("\nThe following issues have been resolved:")
        print("  ✓ JLPT levels now properly convert from 'N4' to integer 4")
        print("  ✓ Import paths fixed for lesson creation scripts")
        print("  ✓ Utility functions created for JLPT level handling")
    else:
        print("\n⚠️  Some fixes failed. Please check the error messages above.")
    
    return success_count == total_fixes

if __name__ == "__main__":
    main()
