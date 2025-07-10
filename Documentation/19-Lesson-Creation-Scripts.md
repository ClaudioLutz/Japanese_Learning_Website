# Lesson Creation Scripts

This document explains how to use the provided Python scripts to automatically generate lessons with AI-powered content.

## Overview

The following scripts are available to create lessons:

*   `create_technology_lesson.py`: Creates a lesson on "Technology and the Internet."
*   `create_numbers_lesson.py`: Creates a multi-page lesson on "Mastering Japanese Numbers."
*   `create_hiragana_lesson.py`: Creates a comprehensive, 11-page lesson on "Complete Hiragana Mastery."

## Prerequisites

Before running the scripts, ensure you have the following:

1.  **Project Setup**: Ensure the main project is fully set up:
    *   Virtual environment activated.
    *   Dependencies installed (`pip install -r requirements.txt`).
    *   Database initialized (`python setup_unified_auth.py`).
    *   Initial data and migrations applied (`python migrate_lesson_system.py`). This ensures necessary categories and the admin user exist.

2.  **Valid OpenAI API Key**: Your OpenAI API key must be set as an environment variable named `OPENAI_API_KEY`. You can set this in a `.env` file in the project root. Example: `OPENAI_API_KEY="sk-YourActualOpenAIKeyHere"`.

3.  **Admin User**: The scripts typically assign lesson authorship or require an admin user context. They are designed to work with the default admin user created by `setup_unified_auth.py` (email: `admin@example.com`). Ensure this user exists in your database. The scripts themselves generally do not require you to pass password credentials as arguments, as they operate within the application context. The reference to `test_ai_generation.py` concerning passwords might be specific to that test script and not these lesson creation utilities.

## How to Run the Scripts

To create a lesson, follow these steps from the project's root directory:

1.  **Ensure your virtual environment is activated.**

2.  **Run the desired script**:
    *   To create the technology lesson:
        ```bash
        python create_technology_lesson.py
        ```
    *   To create the numbers lesson:
        ```bash
        python create_numbers_lesson.py
        ```
    *   To create the Hiragana lesson:
        ```bash
        python create_hiragana_lesson.py
        ```

The script will connect to the database (using the `DATABASE_URL` from your `.env` file), create the lesson structure, and use the AI service (via `app.ai_services` and your `OPENAI_API_KEY`) to generate and populate the content.

## Important Notes

*   **Existing Lessons**: The scripts are designed to delete any existing lesson with the same title before creating a new one. This ensures you always get a fresh version of the lesson.

*   **API Costs**: Be aware that running these scripts will make calls to the OpenAI API, which may incur costs depending on your usage and plan.

*   **Customization**: You can easily customize the lessons by modifying the configuration at the top of each script. You can change the title, difficulty, and content of each lesson to suit your needs.
