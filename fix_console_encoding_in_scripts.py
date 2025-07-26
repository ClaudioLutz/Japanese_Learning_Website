#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix Console Encoding Issues in Generated Lesson Scripts

This script fixes the console encoding issues in the generated lesson creation scripts
by replacing Unicode characters (emoji and Japanese characters) in print statements
with ASCII-safe alternatives.

The issue occurs when scripts contain Unicode characters in print statements and are run on
Windows systems where the console uses cp1252 encoding.
"""

import os
import glob
import re

def fix_console_encoding_in_script(script_path):
    """Fix console encoding in a single script by replacing Unicode characters in print statements."""
    print(f"Fixing console encoding in: {os.path.basename(script_path)}")
    
    try:
        # Read the script with UTF-8 encoding
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Replace Unicode emoji with ASCII alternatives in print statements
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
        
        # Replace emoji in the content
        for emoji, replacement in emoji_replacements.items():
            content = content.replace(emoji, replacement)
        
        # Also replace any remaining Unicode characters in print statements with safe alternatives
        # This is a more aggressive approach for any missed characters
        def replace_unicode_in_print(match):
            print_content = match.group(1)
            # Replace any non-ASCII characters with a placeholder
            safe_content = print_content.encode('ascii', 'replace').decode('ascii')
            return f'print({safe_content})'
        
        # Use regex to find print statements and replace Unicode characters
        content = re.sub(r'print\(([^)]+)\)', replace_unicode_in_print, content)
        
        # Check if any changes were made
        if content != original_content:
            # Write the fixed content back
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"  [OK] Fixed console encoding in {os.path.basename(script_path)}")
            return True
        else:
            print(f"  [OK] No console encoding issues found in {os.path.basename(script_path)}")
            return False
        
    except Exception as e:
        print(f"  [ERROR] Error fixing {os.path.basename(script_path)}: {e}")
        return False

def main():
    """Fix console encoding in all lesson creation scripts."""
    print("Fix Console Encoding Issues in Lesson Creation Scripts")
    print("=" * 70)
    print()
    print("This script replaces Unicode characters in print statements")
    print("with ASCII-safe alternatives to prevent console encoding errors.")
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
        if fix_console_encoding_in_script(script_path):
            fixed_count += 1
    
    print()
    print("=" * 70)
    print(f"CONSOLE ENCODING FIX SUMMARY")
    print("=" * 70)
    print(f"[OK] Scripts checked: {len(scripts)}")
    print(f"[FIX] Scripts fixed: {fixed_count}")
    print(f"[OK] Scripts already correct: {len(scripts) - fixed_count}")
    
    if fixed_count > 0:
        print(f"\n[SUCCESS] Fixed console encoding issues in {fixed_count} scripts!")
        print("The scripts should now run without console encoding errors.")
        print("\nYou can now run: python run_all_lesson_scripts.py")
    else:
        print(f"\n[OK] All scripts already have safe console output.")

if __name__ == "__main__":
    main()
