#!/usr/bin/env python3
"""
Fix Unicode Encoding Issues in Generated Lesson Scripts

This script fixes the Unicode encoding issues in the generated lesson creation scripts
by adding the proper UTF-8 encoding declaration at the top of each file.

The issue occurs when scripts contain Japanese characters or emoji and are run on
Windows systems with cp1252 encoding.
"""

import os
import glob
import re

def fix_unicode_encoding_in_script(script_path):
    """Fix Unicode encoding in a single script by adding UTF-8 declaration."""
    print(f"Fixing Unicode encoding in: {os.path.basename(script_path)}")
    
    try:
        # Read the script with UTF-8 encoding
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if it already has UTF-8 encoding declaration
        if '# -*- coding: utf-8 -*-' in content:
            print(f"  ✅ Already has UTF-8 encoding declaration: {os.path.basename(script_path)}")
            return False
        
        # Add UTF-8 encoding declaration after the shebang line
        lines = content.split('\n')
        
        # Find the shebang line
        shebang_index = -1
        for i, line in enumerate(lines):
            if line.startswith('#!'):
                shebang_index = i
                break
        
        if shebang_index != -1:
            # Insert encoding declaration after shebang
            lines.insert(shebang_index + 1, '# -*- coding: utf-8 -*-')
        else:
            # No shebang found, add at the beginning
            lines.insert(0, '#!/usr/bin/env python3')
            lines.insert(1, '# -*- coding: utf-8 -*-')
        
        # Write the fixed content back
        fixed_content = '\n'.join(lines)
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        print(f"  ✅ Fixed Unicode encoding in {os.path.basename(script_path)}")
        return True
        
    except Exception as e:
        print(f"  ❌ Error fixing {os.path.basename(script_path)}: {e}")
        return False

def main():
    """Fix Unicode encoding in all lesson creation scripts."""
    print("🔧 Fixing Unicode Encoding Issues in Lesson Creation Scripts")
    print("=" * 70)
    print()
    print("This script adds UTF-8 encoding declarations to fix Unicode issues")
    print("that occur when scripts contain Japanese characters or emoji.")
    print()
    
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
        if fix_unicode_encoding_in_script(script_path):
            fixed_count += 1
    
    print()
    print("=" * 70)
    print(f"📊 UNICODE ENCODING FIX SUMMARY")
    print("=" * 70)
    print(f"✅ Scripts checked: {len(scripts)}")
    print(f"🔧 Scripts fixed: {fixed_count}")
    print(f"✅ Scripts already correct: {len(scripts) - fixed_count}")
    
    if fixed_count > 0:
        print(f"\n🎉 Fixed Unicode encoding issues in {fixed_count} scripts!")
        print("The scripts should now run without Unicode encoding errors.")
        print("\nYou can now run: python run_all_lesson_scripts.py")
    else:
        print(f"\n✅ All scripts already have correct Unicode encoding declarations.")

if __name__ == "__main__":
    main()
