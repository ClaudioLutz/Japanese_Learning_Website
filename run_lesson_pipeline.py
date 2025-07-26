#!/usr/bin/env python3
"""
Full Lesson Pipeline Executor

This script orchestrates the entire lesson creation process:
1. Generates lesson scripts for English-speaking learners.
2. Generates lesson scripts for German-speaking learners.
3. Executes all generated lesson scripts to populate the database.
"""

import subprocess
import sys
import os
from datetime import datetime
import argparse

LOG_FILE = f"logs/pipeline_execution_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

def setup_logging():
    """Setup logging to both console and file."""
    class Logger:
        def __init__(self, filename):
            self.terminal = sys.stdout
            self.log = open(filename, "w", encoding='utf-8')

        def write(self, message):
            self.terminal.write(message)
            self.log.write(message)
            self.log.flush()

        def flush(self):
            self.terminal.flush()
            self.log.flush()

    sys.stdout = Logger(LOG_FILE)

def run_script(script_name, args=None):
    """Run a Python script and handle its output with real-time streaming."""
    if not os.path.exists(script_name):
        print(f"\nError: Script not found: {script_name}")
        return False

    command = [sys.executable, script_name]
    if args:
        command.extend(args)

    print(f"\n{'='*60}")
    print(f"Executing: {' '.join(command)}")
    print(f"{'='*60}")
    sys.stdout.flush()  # Ensure the header is printed immediately
    
    try:
        # Use unbuffered output and force real-time streaming
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace',
            bufsize=0,  # Unbuffered
            universal_newlines=True,
            env={**os.environ, 'PYTHONUNBUFFERED': '1'}  # Force Python to be unbuffered
        )

        if process.stdout:
            for line in iter(process.stdout.readline, ''):
                print(line, end='')
                sys.stdout.flush()  # Force immediate output
        
        process.wait()

        if process.returncode == 0:
            print(f"\nSuccess: {script_name} finished successfully.")
            sys.stdout.flush()
            return True
        else:
            print(f"\nError: {script_name} failed with exit code {process.returncode}.")
            sys.stdout.flush()
            return False
    except Exception as e:
        print(f"\nException occurred while running {script_name}: {e}")
        sys.stdout.flush()
        return False

def main():
    """Main pipeline execution function."""
    parser = argparse.ArgumentParser(description="Full Lesson Pipeline Executor")
    parser.add_argument(
        '--language',
        type=str,
        default='both',
        choices=['english', 'german', 'both'],
        help='Specify which language lessons to generate: english, german, or both.'
    )
    parser.add_argument(
        '--skip-generation',
        action='store_true',
        help='Skip the lesson generation step.'
    )
    parser.add_argument(
        '--skip-execution',
        action='store_true',
        help='Skip the lesson execution step.'
    )
    parser.add_argument(
        '--include-existing',
        action='store_true',
        help='Execute scripts for lessons that already exist in the database.'
    )
    args = parser.parse_args()

    setup_logging()
    
    print("Starting Full Lesson Pipeline")
    
    scripts_to_run = []
    if not args.skip_generation:
        if args.language in ['english', 'both']:
            scripts_to_run.append("generate_all_lesson_scripts.py")
        if args.language in ['german', 'both']:
            scripts_to_run.append("generate_japanese_lessons_for_germans.py")
            
    if not args.skip_execution:
        scripts_to_run.append("run_all_lesson_scripts.py")

    if not scripts_to_run:
        print("No scripts to run based on the provided arguments.")
        return

    all_successful = True
    language_map = {
        'english': 'en',
        'german': 'de'
    }
    for script in scripts_to_run:
        script_args = []
        if script == "run_all_lesson_scripts.py":
            if not args.include_existing:
                script_args.append("--skip-existing")
            if args.language != 'both':
                script_args.append(f"--language={language_map.get(args.language)}")
            
        if not run_script(script, script_args):
            all_successful = False
            print(f"Pipeline stopped due to failure in {script}.")
            break
    
    print(f"\n{'='*60}")
    if all_successful:
        print("Full lesson pipeline completed successfully!")
    else:
        print("Full lesson pipeline failed.")
    print(f"Detailed log saved to: {LOG_FILE}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
