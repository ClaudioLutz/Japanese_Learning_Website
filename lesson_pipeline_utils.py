#!/usr/bin/env python3
"""
Shared utility functions for the lesson generation and execution pipeline.
"""

import os
import sys
import re
import json
import time
from datetime import datetime
import codecs

# Reconfigure stdout to use UTF-8 encoding, especially for Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except Exception as e:
        print(f"Could not reconfigure stdout/stderr to UTF-8: {e}")

# Store the original print function before any modifications
import builtins
_original_print = builtins.print

# Force immediate output flushing for real-time console updates
def print_and_flush(*args, **kwargs):
    """Print with immediate flush for real-time output."""
    _original_print(*args, **kwargs)
    sys.stdout.flush()

# Override the built-in print function for this module
builtins.print = print_and_flush

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

class Logger:
    """Logs output to both the console and a file."""
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

def setup_logging(log_file):
    """Setup logging to both console and file."""
    # Ensure the logs directory exists
    log_dir = os.path.dirname(log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    sys.stdout = Logger(log_file)

def load_env():
    """Load environment variables from .env file."""
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    value = value.strip('"\'')
                    os.environ[key] = value

def initialize_gemini(model_name="gemini-2.5-pro"):
    """Initialize Google Gemini API."""
    if not GEMINI_AVAILABLE:
        print("Google Generative AI library not available.")
        print("Install with: pip install google-generativeai")
        return None
        
    api_key = os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        print("Error: GOOGLE_API_KEY not found in environment variables.")
        print("Please add your Google Gemini API key to your .env file.")
        return None
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        print(f"Google Gemini {model_name} initialized successfully")
        return model
    except Exception as e:
        print(f"Error initializing Gemini: {e}")
        return None

def read_file(file_path):
    """Read content from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"File loaded: {file_path}")
        return content
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None

def save_script(script_content, filename, output_dir):
    """Save the generated script to the output directory."""
    try:
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        print(f"Script saved: {filepath}")
        return True
    except Exception as e:
        print(f"Error saving script: {e}")
        return False

def create_script_filename(title, language='en'):
    """Create a valid filename from lesson title with language prefix."""
    filename = re.sub(r'[^\w\s-]', '', title.lower())
    filename = re.sub(r'[-\s]+', '_', filename)
    return f"{language}_create_{filename}_lesson.py"

def truncate_text(text, max_length):
    """Truncate text to fit database constraints."""
    if not text or len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."
