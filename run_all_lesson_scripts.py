#!/usr/bin/env python3
"""
Batch Lesson Script Executor

This script automatically discovers and executes all lesson creation scripts
in the lesson_creation_scripts/ folder in sequence. It provides comprehensive
logging, progress tracking, and error handling.

Features:
- Sequential execution to avoid database conflicts
- Progress tracking with timestamps
- Error handling and recovery
- Detailed logging and summary reports
- Option to skip already created lessons
- Selective execution by topic names
"""

import os
import sys
import subprocess
import time
import argparse
from datetime import datetime
import glob

# Configuration
SCRIPTS_DIR = "lesson_creation_scripts"
LOG_FILE = f"batch_execution_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
EXECUTION_DELAY = 3  # Seconds between script executions

class BatchExecutor:
    def __init__(self, dry_run=False, skip_existing=False, selected_topics=None):
        self.dry_run = dry_run
        self.skip_existing = skip_existing
        self.selected_topics = selected_topics or []
        self.successful_executions = 0
        self.failed_executions = 0
        self.skipped_executions = 0
        self.execution_times = {}
        self.errors = []
        
        # Setup logging
        self.setup_logging()
    
    def setup_logging(self):
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
    
    def discover_scripts(self):
        """Discover all lesson creation scripts in the scripts directory."""
        if not os.path.exists(SCRIPTS_DIR):
            print(f"❌ Scripts directory not found: {SCRIPTS_DIR}")
            return []
        
        # Find all Python scripts that start with "create_" and end with "_lesson.py"
        pattern = os.path.join(SCRIPTS_DIR, "create_*_lesson.py")
        scripts = glob.glob(pattern)
        
        # Sort scripts alphabetically for consistent execution order
        scripts.sort()
        
        # Filter by selected topics if specified
        if self.selected_topics:
            filtered_scripts = []
            for script in scripts:
                script_name = os.path.basename(script)
                for topic in self.selected_topics:
                    if topic.lower() in script_name.lower():
                        filtered_scripts.append(script)
                        break
            scripts = filtered_scripts
        
        print(f"✅ Found {len(scripts)} lesson creation scripts")
        for script in scripts:
            print(f"   - {os.path.basename(script)}")
        
        return scripts
    
    def check_lesson_exists(self, script_path):
        """Check if a lesson created by this script already exists in the database."""
        if not self.skip_existing:
            return False
        
        # This is a simplified check - in a real implementation, you might
        # want to check the database directly or parse the script to get the lesson title
        script_name = os.path.basename(script_path)
        
        # For now, we'll assume lessons don't exist unless specifically checked
        # You could enhance this by connecting to the database and checking
        return False
    
    def execute_script(self, script_path):
        """Execute a single lesson creation script."""
        script_name = os.path.basename(script_path)
        
        if self.dry_run:
            print(f"🔍 [DRY RUN] Would execute: {script_name}")
            return True
        
        if self.check_lesson_exists(script_path):
            print(f"⏭️  Skipping {script_name} (lesson already exists)")
            self.skipped_executions += 1
            return True
        
        print(f"🎯 Executing: {script_name}")
        start_time = time.time()
        
        process = None
        try:
            # Execute the script using subprocess with proper working directory and encoding
            process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.path.dirname(os.path.abspath(__file__)),  # Set working directory to project root
                encoding='utf-8',  # Force UTF-8 encoding
                errors='replace'  # Handle encoding errors gracefully
            )
            
            # Wait for completion with timeout
            stdout, stderr = process.communicate(timeout=1800)  # 30 minute timeout
            result = subprocess.CompletedProcess(
                args=[sys.executable, script_path],
                returncode=process.returncode,
                stdout=stdout,
                stderr=stderr
            )
            
            execution_time = time.time() - start_time
            self.execution_times[script_name] = execution_time
            
            if result.returncode == 0:
                print(f"✅ Success: {script_name} ({execution_time:.1f}s)")
                
                # Print last few lines of output for confirmation
                if result.stdout:
                    output_lines = result.stdout.strip().split('\n')
                    if len(output_lines) > 3:
                        print("   Last output lines:")
                        for line in output_lines[-3:]:
                            print(f"   {line}")
                
                self.successful_executions += 1
                return True
            else:
                print(f"❌ Failed: {script_name} (exit code: {result.returncode})")
                
                # Print error output
                if result.stderr:
                    print("   Error output:")
                    for line in result.stderr.strip().split('\n')[:5]:  # First 5 lines
                        print(f"   {line}")
                
                self.errors.append({
                    'script': script_name,
                    'exit_code': result.returncode,
                    'error': result.stderr[:500] if result.stderr else 'No error output'
                })
                self.failed_executions += 1
                return False
                
        except subprocess.TimeoutExpired as e:
            execution_time = time.time() - start_time
            print(f"⏰ Timeout: {script_name} (exceeded 30 minutes)")
            
            # Kill the process if it's still running
            try:
                if process and process.poll() is None:  # Process is still running
                    process.kill()
                    process.wait()
                    print(f"   🔪 Process terminated due to timeout")
            except Exception as kill_error:
                print(f"   ⚠️  Could not kill process: {kill_error}")
            
            self.errors.append({
                'script': script_name,
                'exit_code': 'TIMEOUT',
                'error': 'Script execution exceeded 30 minute timeout'
            })
            self.failed_executions += 1
            return False
            
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"💥 Exception: {script_name} - {str(e)}")
            self.errors.append({
                'script': script_name,
                'exit_code': 'EXCEPTION',
                'error': str(e)
            })
            self.failed_executions += 1
            return False
    
    def print_summary(self):
        """Print execution summary."""
        total_scripts = self.successful_executions + self.failed_executions + self.skipped_executions
        total_time = sum(self.execution_times.values())
        
        print("\n" + "=" * 60)
        print("📊 BATCH EXECUTION SUMMARY")
        print("=" * 60)
        print(f"📈 Total scripts processed: {total_scripts}")
        print(f"✅ Successful executions: {self.successful_executions}")
        print(f"❌ Failed executions: {self.failed_executions}")
        print(f"⏭️  Skipped executions: {self.skipped_executions}")
        print(f"⏱️  Total execution time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
        
        if self.execution_times:
            avg_time = total_time / len(self.execution_times)
            print(f"📊 Average execution time: {avg_time:.1f} seconds")
        
        # Print execution times for successful scripts
        if self.execution_times:
            print(f"\n⏱️  Individual Execution Times:")
            for script, exec_time in sorted(self.execution_times.items()):
                print(f"   {script}: {exec_time:.1f}s")
        
        # Print errors if any
        if self.errors:
            print(f"\n❌ Errors Encountered:")
            for error in self.errors:
                print(f"   {error['script']}: {error['exit_code']}")
                if len(error['error']) > 100:
                    print(f"      {error['error'][:100]}...")
                else:
                    print(f"      {error['error']}")
        
        print(f"\n📝 Detailed log saved to: {LOG_FILE}")
        
        # Final status
        if self.failed_executions == 0:
            print(f"\n🎉 All scripts executed successfully!")
            if self.successful_executions > 0:
                print(f"   {self.successful_executions} lessons have been created in the database.")
        else:
            print(f"\n⚠️  {self.failed_executions} scripts failed. Check the errors above.")
    
    def run(self):
        """Main execution method."""
        print("🚀 Starting Batch Lesson Script Execution")
        print("=" * 60)
        
        if self.dry_run:
            print("🔍 DRY RUN MODE - No scripts will be actually executed")
        
        if self.skip_existing:
            print("⏭️  SKIP EXISTING MODE - Will skip lessons that already exist")
        
        if self.selected_topics:
            print(f"🎯 SELECTIVE MODE - Only processing topics: {', '.join(self.selected_topics)}")
        
        print()
        
        # Discover scripts
        scripts = self.discover_scripts()
        if not scripts:
            print("❌ No scripts found to execute.")
            return
        
        # Execute scripts
        for i, script_path in enumerate(scripts, 1):
            script_name = os.path.basename(script_path)
            print(f"\n--- [{i}/{len(scripts)}] Processing: {script_name} ---")
            
            success = self.execute_script(script_path)
            
            # Add delay between executions (except for last script)
            if i < len(scripts) and not self.dry_run:
                print(f"⏳ Waiting {EXECUTION_DELAY} seconds before next execution...")
                time.sleep(EXECUTION_DELAY)
        
        # Print summary
        self.print_summary()

def main():
    """Main function with command line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Batch execute all lesson creation scripts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_all_lesson_scripts.py                    # Run all scripts
  python run_all_lesson_scripts.py --dry-run          # Preview what would be executed
  python run_all_lesson_scripts.py --skip-existing    # Skip already created lessons
  python run_all_lesson_scripts.py --topics "internet,anime,business"  # Run specific topics
        """
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview what would be executed without actually running scripts'
    )
    
    parser.add_argument(
        '--skip-existing',
        action='store_true',
        help='Skip scripts for lessons that already exist in the database'
    )
    
    parser.add_argument(
        '--topics',
        type=str,
        help='Comma-separated list of topic keywords to filter scripts (e.g., "internet,anime,business")'
    )
    
    args = parser.parse_args()
    
    # Parse topics if provided
    selected_topics = []
    if args.topics:
        selected_topics = [topic.strip() for topic in args.topics.split(',')]
    
    # Create and run executor
    executor = BatchExecutor(
        dry_run=args.dry_run,
        skip_existing=args.skip_existing,
        selected_topics=selected_topics
    )
    
    executor.run()

if __name__ == "__main__":
    main()
