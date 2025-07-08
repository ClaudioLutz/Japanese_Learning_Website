# Lesson Creation Scripts

This document explains how to use the provided Python scripts to automatically generate lessons with AI-powered content.

## Overview

The following scripts are available to create lessons:

*   `create_technology_lesson.py`: Creates a lesson on "Technology and the Internet."
*   `create_numbers_lesson.py`: Creates a multi-page lesson on "Mastering Japanese Numbers."
*   `create_hiragana_lesson.py`: Creates a comprehensive, 11-page lesson on "Complete Hiragana Mastery."

## Prerequisites

Before running the scripts, ensure you have the following:

1.  **Valid OpenAI API Key**: Your OpenAI API key must be set as an environment variable named `OPENAI_API_KEY`. You can set this in a `.env` file in the root of the project, or directly in your terminal.

2.  **Admin Account**: The scripts assume you have an admin account with the email `admin@example.com` and password `your_password`. If your credentials are different, you will need to update the `test_ai_generation.py` script accordingly.

## How to Run the Scripts

To create a lesson, follow these steps:

1.  **Navigate to the project directory**:
    ```bash
    cd Japanese_Learning_Website
    ```

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

The script will then connect to the database, create the lesson and its pages, and use the AI service to generate and populate the content.

## Important Notes

*   **Existing Lessons**: The scripts are designed to delete any existing lesson with the same title before creating a new one. This ensures you always get a fresh version of the lesson.

*   **API Costs**: Be aware that running these scripts will make calls to the OpenAI API, which may incur costs depending on your usage and plan.

*   **Customization**: You can easily customize the lessons by modifying the configuration at the top of each script. You can change the title, difficulty, and content of each lesson to suit your needs.
