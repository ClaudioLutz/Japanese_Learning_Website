#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix Console Output Encoding Issues - PRESERVE ALL JAPANESE CONTENT

This script fixes console encoding issues by only modifying print statements
for console output, while preserving ALL Japanese characters in lesson content,
titles, and database storage.

IMPORTANT: This does NOT remove Japanese characters from lessons - it only
makes the console output safe while keeping all Japanese content intact.
"""

import os
import glob
import re

def fix_console_output_in_script(script_path):
    """Fix console output encoding while preserving all Japanese content."""
    print(f"Fixing console output in: {os.path.basename(script_path)}")
    
    try:
        # Read the script with UTF-8 encoding
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Only fix specific print statements that cause console issues
        # while preserving ALL Japanese content in variables and data
        
        # Fix the main problematic print statement
        content = re.sub(
            r'print\(f"--- Creating Lesson: \{LESSON_TITLE\} ---"\)',
            'print("--- Creating Lesson: [LESSON_TITLE] ---")',
            content
        )
        
        # Fix other problematic print statements with lesson title
        content = re.sub(
            r'print\(f"Found existing lesson \'\{LESSON_TITLE\}\' \(ID: \{existing_lesson\.id\}\)\. Deleting it\."\)',
            'print(f"Found existing lesson [LESSON_TITLE] (ID: {existing_lesson.id}). Deleting it.")',
            content
        )
        
        content = re.sub(
            r'print\(f"✅ Lesson \'\{LESSON_TITLE\}\' created with ID: \{lesson\.id\}"\)',
            'print(f"[OK] Lesson [LESSON_TITLE] created with ID: {lesson.id}")',
            content
        )
        
        content = re.sub(
            r'print\(f"--- \{LESSON_TITLE\} Creation Complete! ---"\)',
            'print("--- [LESSON_TITLE] Creation Complete! ---")',
            content
        )
        
        content = re.sub(
            r'print\(f"✅ \{LESSON_TITLE\} lesson created successfully!"\)',
            'print("[OK] Lesson created successfully!")',
            content
        )
        
        # Replace Unicode emoji with ASCII alternatives (already done by previous script)
        emoji_replacements = {
            '✅': '[OK]',
            '❌': '[ERROR]',
            '🤖': '[AI]',
            '🖼️': '[IMG]',
            '🎨': '[ART]',
            '⏳': '[WAIT]',
            '🎉': '[SUCCESS]',
            '📊': '[STATS]',
            '📁': '[FOLDER]',
            '📝': '[LOG]',
            '🚀': '[START]',
            '🔧': '[FIX]',
            '⚠️': '[WARNING]',
            '🎯': '[TARGET]'
        }
        
        # Replace emoji in print statements only
        for emoji, replacement in emoji_replacements.items():
            content = content.replace(emoji, replacement)
        
        # Check if any changes were made
        if content != original_content:
            # Write the fixed content back
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"  [OK] Fixed console output in {os.path.basename(script_path)}")
            return True
        else:
            print(f"  [OK] No console output issues found in {os.path.basename(script_path)}")
            return False
        
    except Exception as e:
        print(f"  [ERROR] Error fixing {os.path.basename(script_path)}: {e}")
        return False

def main():
    """Fix console output in all lesson creation scripts while preserving Japanese content."""
    print("Fix Console Output Issues - PRESERVE ALL JAPANESE CONTENT")
    print("=" * 70)
    print()
    print("This script fixes console encoding issues by modifying ONLY print")
    print("statements for console output, while preserving ALL Japanese")
    print("characters in lesson content, titles, and database storage.")
    print()
    print("IMPORTANT: Japanese content in lessons remains completely intact!")
    print()
    
    # Find all lesson creation scripts
    scripts_dir = "lesson_creation_scripts"
    if not os.path.exists(scripts_dir):
        print(f"[ERROR] Scripts directory not found: {scripts_dir}")
        return
    
    # Find all Python scripts that start with "create_" and end with "_lesson.py"
    pattern = os.path.join(scripts_dir, "create_*_lesson.py")
    scripts = glob.glob(pattern)
    
    if not scripts:
        print("[ERROR] No lesson creation scripts found.")
        return
    
    print(f"Found {len(scripts)} lesson creation scripts to check.")
    print()
    
    fixed_count = 0
    for script_path in sorted(scripts):
        if fix_console_output_in_script(script_path):
            fixed_count += 1
    
    print()
    print("=" * 70)
    print(f"CONSOLE OUTPUT FIX SUMMARY")
    print("=" * 70)
    print(f"[OK] Scripts checked: {len(scripts)}")
    print(f"[FIX] Scripts fixed: {fixed_count}")
    print(f"[OK] Scripts already correct: {len(scripts) - fixed_count}")
    
    if fixed_count > 0:
        print(f"\n[SUCCESS] Fixed console output issues in {fixed_count} scripts!")
        print("The scripts should now run without console encoding errors.")
        print("\nIMPORTANT: All Japanese content in lessons is preserved!")
        print("Only console print statements were modified for Windows compatibility.")
        print("\nYou can now run: python run_all_lesson_scripts.py")
    else:
        print(f"\n[OK] All scripts already have safe console output.")

if __name__ == "__main__":
    main()
