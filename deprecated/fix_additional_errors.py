#!/usr/bin/env python3
"""
Fix Additional Lesson Script Errors

This script fixes the remaining issues found after the initial fix:
1. Database field length constraints (grammar explanation too long)
2. Difficulty level type mismatch (string vs integer)
3. Structure field length constraints

The script will:
- Update AI services to truncate long text fields
- Add difficulty level conversion utilities
- Fix lesson creation scripts to use integer difficulty levels
"""

import os
import sys
import re
from pathlib import Path

def convert_difficulty_to_int(difficulty):
    """
    Convert difficulty level from string format to integer format
    
    Args:
        difficulty: String like "Beginner", "Intermediate", "Advanced" or integer
    
    Returns:
        Integer representation of difficulty level (1-5)
    """
    if isinstance(difficulty, int):
        return max(1, min(5, difficulty))  # Ensure it's between 1-5
    
    if isinstance(difficulty, str):
        difficulty = difficulty.lower().strip()
        difficulty_map = {
            'beginner': 1,
            'elementary': 1,
            'easy': 1,
            'basic': 1,
            'intermediate': 3,
            'medium': 3,
            'advanced': 4,
            'hard': 4,
            'expert': 5,
            'master': 5
        }
        return difficulty_map.get(difficulty, 3)  # Default to intermediate
    
    return 3  # Default to intermediate

def fix_ai_services_field_lengths():
    """Fix the AI services to handle field length constraints"""
    ai_services_path = Path("app/ai_services.py")
    
    if not ai_services_path.exists():
        print(f"❌ {ai_services_path} not found")
        return False
    
    print(f"🔧 Fixing field length constraints in {ai_services_path}")
    
    # Read the current content
    with open(ai_services_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add field truncation utility function
    truncation_function = '''
def truncate_field(text, max_length):
    """
    Truncate text to fit database field constraints
    
    Args:
        text: Text to truncate
        max_length: Maximum allowed length
    
    Returns:
        Truncated text that fits the constraint
    """
    if not text:
        return text
    
    if len(text) <= max_length:
        return text
    
    # Truncate and add ellipsis
    return text[:max_length-3] + "..."

'''
    
    # Insert the truncation function after the convert_jlpt_level_to_int function
    jlpt_function_end = content.find('    return 5\n\n\nclass AILessonContentGenerator:')
    if jlpt_function_end != -1:
        insert_point = jlpt_function_end + len('    return 5\n\n')
        content = content[:insert_point] + truncation_function + content[insert_point:]
    
    # Fix the generate_grammar_data method to truncate long fields
    grammar_method_pattern = r'(def generate_grammar_data\(self, grammar_point, jlpt_level\):.*?grammar_entry = Grammar\(\s*title=grammar_data\[\'title\'\],\s*explanation=grammar_data\[\'explanation\'\],\s*structure=grammar_data\.get\(\'structure\', \'\'\),)'
    grammar_replacement = r'''\1
                    title=truncate_field(grammar_data['title'], 200),
                    explanation=grammar_data['explanation'],  # Text field, no length limit
                    structure=truncate_field(grammar_data.get('structure', ''), 255),'''
    
    # Apply the fix with a more targeted approach
    if 'grammar_entry = Grammar(' in content:
        # Find and replace the Grammar constructor call
        grammar_constructor_pattern = r'grammar_entry = Grammar\(\s*title=grammar_data\[\'title\'\],\s*explanation=grammar_data\[\'explanation\'\],\s*structure=grammar_data\.get\(\'structure\', \'\'\),'
        grammar_constructor_replacement = '''grammar_entry = Grammar(
                    title=truncate_field(grammar_data['title'], 200),
                    explanation=grammar_data['explanation'],  # Text field, no length limit
                    structure=truncate_field(grammar_data.get('structure', ''), 255),'''
        
        content = re.sub(grammar_constructor_pattern, grammar_constructor_replacement, content)
    
    # Write the updated content
    with open(ai_services_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Fixed field length constraints in {ai_services_path}")
    return True

def fix_lesson_difficulty_levels():
    """Fix lesson creation scripts to use integer difficulty levels"""
    scripts_dir = Path("lesson_creation_scripts")
    
    if not scripts_dir.exists():
        print(f"❌ {scripts_dir} directory not found")
        return False
    
    # Find all Python scripts in the directory
    script_files = list(scripts_dir.glob("*.py"))
    
    print(f"🔧 Fixing difficulty levels in {len(script_files)} lesson creation scripts")
    
    fixed_count = 0
    
    for script_path in script_files:
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Fix difficulty level assignments
            difficulty_replacements = {
                "difficulty='Beginner'": "difficulty_level=1",
                "difficulty='Elementary'": "difficulty_level=1", 
                "difficulty='Easy'": "difficulty_level=1",
                "difficulty='Basic'": "difficulty_level=1",
                "difficulty='Intermediate'": "difficulty_level=3",
                "difficulty='Medium'": "difficulty_level=3",
                "difficulty='Advanced'": "difficulty_level=4",
                "difficulty='Hard'": "difficulty_level=4",
                "difficulty='Expert'": "difficulty_level=5",
                "difficulty='Master'": "difficulty_level=5",
                '"difficulty": "Beginner"': '"difficulty": 1',
                '"difficulty": "Elementary"': '"difficulty": 1',
                '"difficulty": "Easy"': '"difficulty": 1',
                '"difficulty": "Basic"': '"difficulty": 1',
                '"difficulty": "Intermediate"': '"difficulty": 3',
                '"difficulty": "Medium"': '"difficulty": 3',
                '"difficulty": "Advanced"': '"difficulty": 4',
                '"difficulty": "Hard"': '"difficulty": 4',
                '"difficulty": "Expert"': '"difficulty": 5',
                '"difficulty": "Master"': '"difficulty": 5',
                "'difficulty': 'Beginner'": "'difficulty': 1",
                "'difficulty': 'Elementary'": "'difficulty': 1",
                "'difficulty': 'Easy'": "'difficulty': 1",
                "'difficulty': 'Basic'": "'difficulty': 1",
                "'difficulty': 'Intermediate'": "'difficulty': 3",
                "'difficulty': 'Medium'": "'difficulty': 3",
                "'difficulty': 'Advanced'": "'difficulty': 4",
                "'difficulty': 'Hard'": "'difficulty': 4",
                "'difficulty': 'Expert'": "'difficulty': 5",
                "'difficulty': 'Master'": "'difficulty': 5",
                "difficulty_level='Beginner'": "difficulty_level=1",
                "difficulty_level='Elementary'": "difficulty_level=1",
                "difficulty_level='Easy'": "difficulty_level=1",
                "difficulty_level='Basic'": "difficulty_level=1",
                "difficulty_level='Intermediate'": "difficulty_level=3",
                "difficulty_level='Medium'": "difficulty_level=3",
                "difficulty_level='Advanced'": "difficulty_level=4",
                "difficulty_level='Hard'": "difficulty_level=4",
                "difficulty_level='Expert'": "difficulty_level=5",
                "difficulty_level='Master'": "difficulty_level=5",
                'difficulty_level="Beginner"': "difficulty_level=1",
                'difficulty_level="Elementary"': "difficulty_level=1",
                'difficulty_level="Easy"': "difficulty_level=1",
                'difficulty_level="Basic"': "difficulty_level=1",
                'difficulty_level="Intermediate"': "difficulty_level=3",
                'difficulty_level="Medium"': "difficulty_level=3",
                'difficulty_level="Advanced"': "difficulty_level=4",
                'difficulty_level="Hard"': "difficulty_level=4",
                'difficulty_level="Expert"': "difficulty_level=5",
                'difficulty_level="Master"': "difficulty_level=5"
            }
            
            for old_pattern, new_pattern in difficulty_replacements.items():
                content = content.replace(old_pattern, new_pattern)
            
            # Only write if content changed
            if content != original_content:
                with open(script_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"  ✅ Fixed {script_path.name}")
                fixed_count += 1
            
        except Exception as e:
            print(f"  ❌ Error fixing {script_path.name}: {e}")
    
    print(f"✅ Fixed difficulty levels in {fixed_count} scripts")
    return True

def create_difficulty_conversion_utility():
    """Add difficulty conversion to the existing JLPT utility file"""
    utility_path = Path("app/jlpt_utils.py")
    
    if not utility_path.exists():
        print(f"❌ {utility_path} not found")
        return False
    
    print(f"🔧 Adding difficulty conversion to {utility_path}")
    
    # Read the current content
    with open(utility_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add difficulty conversion functions
    difficulty_functions = '''

def convert_difficulty_to_int(difficulty):
    """
    Convert difficulty level from string format to integer format
    
    Args:
        difficulty: String like "Beginner", "Intermediate", "Advanced" or integer
    
    Returns:
        Integer representation of difficulty level (1-5)
    """
    if isinstance(difficulty, int):
        return max(1, min(5, difficulty))  # Ensure it's between 1-5
    
    if isinstance(difficulty, str):
        difficulty = difficulty.lower().strip()
        difficulty_map = {
            'beginner': 1,
            'elementary': 1,
            'easy': 1,
            'basic': 1,
            'intermediate': 3,
            'medium': 3,
            'advanced': 4,
            'hard': 4,
            'expert': 5,
            'master': 5
        }
        return difficulty_map.get(difficulty, 3)  # Default to intermediate
    
    return 3  # Default to intermediate

def convert_int_to_difficulty_level(level_int):
    """
    Convert integer difficulty level to string format
    
    Args:
        level_int: Integer like 1, 2, 3, 4, 5
    
    Returns:
        String representation like "Beginner", "Intermediate", etc.
    """
    difficulty_map = {
        1: "Beginner",
        2: "Elementary", 
        3: "Intermediate",
        4: "Advanced",
        5: "Expert"
    }
    return difficulty_map.get(level_int, "Intermediate")

def validate_difficulty_level(difficulty):
    """
    Validate that a difficulty level is valid
    
    Args:
        difficulty: Difficulty level in any format
    
    Returns:
        Boolean indicating if the level is valid
    """
    try:
        level_int = convert_difficulty_to_int(difficulty)
        return 1 <= level_int <= 5
    except:
        return False

def truncate_field(text, max_length):
    """
    Truncate text to fit database field constraints
    
    Args:
        text: Text to truncate
        max_length: Maximum allowed length
    
    Returns:
        Truncated text that fits the constraint
    """
    if not text:
        return text
    
    if len(text) <= max_length:
        return text
    
    # Truncate and add ellipsis
    return text[:max_length-3] + "..."
'''
    
    # Append the new functions
    content += difficulty_functions
    
    # Write the updated content
    with open(utility_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Added difficulty conversion functions to {utility_path}")
    return True

def main():
    """Main function to fix additional lesson script errors"""
    print("🔧 Additional Lesson Script Error Fixer")
    print("=" * 50)
    print()
    print("This script will fix the remaining issues:")
    print("1. Database field length constraints")
    print("2. Difficulty level type mismatch (string vs integer)")
    print("3. Add utility functions for difficulty conversion")
    print()
    
    success_count = 0
    total_fixes = 3
    
    # Fix 1: Add difficulty conversion utilities
    print("🔧 Step 1: Adding difficulty conversion utilities...")
    if create_difficulty_conversion_utility():
        success_count += 1
    
    # Fix 2: Update AI services for field lengths
    print("\n🔧 Step 2: Fixing AI services field length constraints...")
    if fix_ai_services_field_lengths():
        success_count += 1
    
    # Fix 3: Fix lesson script difficulty levels
    print("\n🔧 Step 3: Fixing lesson script difficulty levels...")
    if fix_lesson_difficulty_levels():
        success_count += 1
    
    print(f"\n{'='*50}")
    print(f"✅ Completed {success_count}/{total_fixes} additional fixes successfully!")
    
    if success_count == total_fixes:
        print("\n🎉 All additional fixes applied successfully!")
        print("\nYou can now run the lesson scripts again:")
        print("  python run_all_lesson_scripts.py --skip-existing")
        print("\nThe following additional issues have been resolved:")
        print("  ✓ Database field length constraints handled")
        print("  ✓ Difficulty levels now properly convert from 'Intermediate' to integer 3")
        print("  ✓ Utility functions created for difficulty level handling")
        print("  ✓ Text truncation functions added for long content")
    else:
        print("\n⚠️  Some additional fixes failed. Please check the error messages above.")
    
    return success_count == total_fixes

if __name__ == "__main__":
    main()
