#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix Japanese Characters in Generated Lesson Scripts

This script fixes the issue where LESSON_TITLE and other variables contain Japanese characters
that cause UnicodeEncodeError when printed to the Windows console.

The fix replaces Japanese characters in string variables with romanized equivalents.
"""

import os
import glob
import re

def romanize_japanese_chars(text):
    """Replace common Japanese characters with romanized equivalents."""
    # Common Japanese character replacements
    replacements = {
        'は': 'wa',
        'が': 'ga', 
        'を': 'wo',
        'に': 'ni',
        'の': 'no',
        'と': 'to',
        'で': 'de',
        'だ': 'da',
        'です': 'desu',
        'ます': 'masu',
        'する': 'suru',
        'した': 'shita',
        'して': 'shite',
        'ある': 'aru',
        'いる': 'iru',
        'こと': 'koto',
        'もの': 'mono',
        'ひと': 'hito',
        'とき': 'toki',
        'ところ': 'tokoro',
        'あげる': 'ageru',
        'くれる': 'kureru', 
        'もらう': 'morau',
        '心': 'kokoro',
        '彩り': 'irodori',
        '微妙': 'bimyou',
        '感情': 'kanjou',
        '表現': 'hyougen',
        '恋': 'koi',
        '日本語': 'nihongo',
        '恋愛': 'renai',
        '人間関係': 'ningen-kankei',
        'ガイド': 'gaido',
        '日本': 'nihon',
        'スポーツ': 'supootsu',
        '文化': 'bunka',
        '相撲': 'sumou',
        '野球': 'yakyuu',
        '武道': 'budou',
        'テクノロジー': 'tekunorojii',
        'イノベーション': 'inobeeshon',
        '住まい': 'sumai',
        '探し': 'sagashi',
        'アパート': 'apaato',
        '契約': 'keiyaku',
        '新生活': 'shin-seikatsu',
        '学校': 'gakkou',
        '生活': 'seikatsu',
        '入学': 'nyuugaku',
        '卒業': 'sotsugyou'
    }
    
    result = text
    for jp_char, romanized in replacements.items():
        result = result.replace(jp_char, romanized)
    
    # Remove any remaining Japanese characters (fallback)
    result = re.sub(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', '', result)
    
    return result

def fix_japanese_characters_in_script(script_path):
    """Fix Japanese characters in a single script."""
    print(f"Fixing Japanese characters in: {os.path.basename(script_path)}")
    
    try:
        # Read the script with UTF-8 encoding
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Find and fix LESSON_TITLE assignments
        lesson_title_pattern = r'LESSON_TITLE = "(.*?)"'
        matches = re.findall(lesson_title_pattern, content)
        
        for match in matches:
            if re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', match):
                # Contains Japanese characters, create a safe version
                safe_title = romanize_japanese_chars(match)
                # Keep the original for database storage, but create a safe version for console
                content = content.replace(
                    f'LESSON_TITLE = "{match}"',
                    f'LESSON_TITLE = "{match}"\nLESSON_TITLE_SAFE = "{safe_title}"'
                )
                
                # Replace all print statements that use LESSON_TITLE with LESSON_TITLE_SAFE
                content = re.sub(
                    r'print\(f"([^"]*){LESSON_TITLE}([^"]*)"',
                    r'print(f"\1{LESSON_TITLE_SAFE}\2"',
                    content
                )
                
                # Also fix any other print statements with LESSON_TITLE
                content = content.replace(
                    'print(f"--- Creating Lesson: {LESSON_TITLE} ---")',
                    'print(f"--- Creating Lesson: {LESSON_TITLE_SAFE} ---")'
                )
                
                content = content.replace(
                    "print(f\"Found existing lesson '{LESSON_TITLE}' (ID: {existing_lesson.id}). Deleting it.\")",
                    "print(f\"Found existing lesson '{LESSON_TITLE_SAFE}' (ID: {existing_lesson.id}). Deleting it.\")"
                )
                
                content = content.replace(
                    "print(f\"[OK] Lesson '{LESSON_TITLE}' created with ID: {lesson.id}\")",
                    "print(f\"[OK] Lesson '{LESSON_TITLE_SAFE}' created with ID: {lesson.id}\")"
                )
                
                content = content.replace(
                    "print(f\"[OK] {LESSON_TITLE} Creation Complete! ---\")",
                    "print(f\"[OK] {LESSON_TITLE_SAFE} Creation Complete! ---\")"
                )
                
                content = content.replace(
                    "print(f\"[OK] {LESSON_TITLE} lesson created successfully!\")",
                    "print(f\"[OK] {LESSON_TITLE_SAFE} lesson created successfully!\")"
                )
        
        # Check if any changes were made
        if content != original_content:
            # Write the fixed content back
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"  [OK] Fixed Japanese characters in {os.path.basename(script_path)}")
            return True
        else:
            print(f"  [OK] No Japanese characters found in {os.path.basename(script_path)}")
            return False
        
    except Exception as e:
        print(f"  [ERROR] Error fixing {os.path.basename(script_path)}: {e}")
        return False

def main():
    """Fix Japanese characters in all lesson creation scripts."""
    print("Fix Japanese Characters in Lesson Creation Scripts")
    print("=" * 70)
    print()
    print("This script replaces Japanese characters in LESSON_TITLE variables")
    print("with romanized equivalents to prevent console encoding errors.")
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
        if fix_japanese_characters_in_script(script_path):
            fixed_count += 1
    
    print()
    print("=" * 70)
    print(f"JAPANESE CHARACTER FIX SUMMARY")
    print("=" * 70)
    print(f"[OK] Scripts checked: {len(scripts)}")
    print(f"[FIX] Scripts fixed: {fixed_count}")
    print(f"[OK] Scripts already correct: {len(scripts) - fixed_count}")
    
    if fixed_count > 0:
        print(f"\n[SUCCESS] Fixed Japanese character issues in {fixed_count} scripts!")
        print("The scripts should now run without Japanese character encoding errors.")
        print("\nYou can now run: python run_all_lesson_scripts.py")
    else:
        print(f"\n[OK] All scripts already have safe character handling.")

if __name__ == "__main__":
    main()
