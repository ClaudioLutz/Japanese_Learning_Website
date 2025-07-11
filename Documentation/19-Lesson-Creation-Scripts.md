# 19. Lesson Creation Scripts

## 1. Overview

The project includes a powerful suite of Python scripts designed to automate the creation of lessons. These scripts leverage AI services (like OpenAI) to generate rich, structured, and often multimedia-enhanced content, which is then saved directly into the application's database.

This system is built on a class-based inheritance model to maximize code reuse and simplify the creation of new scripts.

## 2. Core Infrastructure

The foundation of the lesson creation system consists of two base classes:

-   **`lesson_creator_base.py`**: This is the fundamental base class. It handles the core logic of interacting with the database, creating the main `Lesson` object, and managing the overall creation process. It includes methods for adding content pages and ensuring lessons are created idempotently (deleting old versions before creating new ones).
-   **`multimedia_lesson_creator.py`**: This class inherits from `LessonCreatorBase` and extends its functionality to handle multimedia content. It provides methods for generating and downloading images and audio files from AI services and associating them with lesson content.

All specific lesson creation scripts inherit from one of these two base classes.

## 3. Types of Creation Scripts

The scripts can be broadly categorized based on their functionality and awareness of the existing database content.

### 3.1. Standalone Lesson Scripts

These scripts are designed to create a specific, self-contained lesson. They are generally idempotent, meaning they will delete and recreate the lesson each time they are run.

-   **`create_hiragana_lesson.py`**: Creates a comprehensive, 11-page lesson titled "Complete Hiragana Mastery."
-   **`create_hiragana_lesson_german.py`**: Creates the same Hiragana lesson but with all instructions and explanations in German.
-   **`create_kanji_lesson.py`**: Creates a lesson focused on a specific set of Kanji characters.
-   **`create_numbers_lesson.py`**: Creates a multi-page lesson on "Mastering Japanese Numbers."
-   **`create_numbers_lesson_enhanced.py`**: An improved version of the numbers lesson script with more detailed content.
-   **`create_technology_lesson.py`**: Creates a lesson on vocabulary related to "Technology and the Internet."
-   **`create_travel_japanese_lesson.py`**: Creates a lesson covering essential phrases for traveling in Japan.

### 3.2. Database-Aware Scripts

These advanced scripts check the database for existing content (like Kanji or Vocabulary) before creating new entries. This is crucial for building a clean, non-redundant library of core content that can be reused across multiple lessons.

-   **`create_jlpt_lesson_database_aware.py`**: Generates lessons for specific JLPT levels. It queries the database for existing Kanji, Vocabulary, and Grammar items corresponding to that level and adds them to the lesson, only creating new entries if they don't already exist.
-   **`create_kana_lesson_database_aware.py`**: Creates lessons for Hiragana and Katakana, checking for existing character entries before adding new ones.

### 3.3. Comprehensive Multimedia Scripts

This script is a prime example of using the `MultimediaLessonCreator` to build a lesson that integrates various types of media.

-   **`create_comprehensive_multimedia_lesson.py`**: Creates a rich lesson that includes not only text but also AI-generated images and audio files, demonstrating the full capabilities of the system.

## 4. How to Use the Scripts

### 4.1. Prerequisites

1.  **Project Setup**:
    -   Activate the Python virtual environment.
    -   Install all dependencies: `pip install -r requirements.txt`.
    -   Initialize the database and create the admin user: `python setup_unified_auth.py`.
    -   **Crucially**, run the initial data migration to seed necessary categories: `python migrate_lesson_system.py`.

2.  **Environment Variables**:
    -   Create a `.env` file in the project root.
    -   Add your OpenAI API key to this file: `OPENAI_API_KEY="sk-YourActualOpenAIKeyHere"`.

### 4.2. Running a Script

To generate a lesson, execute the desired script from the project's root directory:

```bash
# Ensure your virtual environment is activated
source venv/bin/activate  # Or .\venv\Scripts\activate on Windows

# Run the script
python create_travel_japanese_lesson.py
```

The script will provide console output indicating its progress as it generates content and saves it to the database.

## 5. Important Considerations

-   **Idempotency**: Most standalone scripts are idempotent. They will find and delete a lesson with the same title before running to ensure a clean slate. Database-aware scripts, however, are designed to add to existing content.
-   **API Costs**: Running these scripts makes calls to the OpenAI API, which will incur costs based on your usage.
-   **Customization**: The scripts are highly customizable. You can change the lesson topics, content, and structure by modifying the configuration variables found at the top of each script file.
