# 24. AI Content Generation Capabilities

This document provides a comprehensive overview of the AI-powered content generation features available in the system. The core of this functionality resides in the `AILessonContentGenerator` class located in `app/ai_services.py`.

## 1. Core Content Generation

### 1.1. Text Explanations

-   **`generate_explanation(topic, difficulty, keywords)`**: Generates a simple, plain-text paragraph explaining a given topic. Ideal for brief introductions or definitions.
-   **`generate_formatted_explanation(topic, difficulty, keywords)`**: Creates a more detailed and structured explanation using HTML tags (`<h2>`, `<p>`, `<strong>`, `<ul>`, etc.). This is suitable for main lesson content.

### 1.2. Database Entity Generation

The AI can populate the database with foundational Japanese language data:

-   **`generate_kanji_data(kanji_character, jlpt_level)`**: Generates a complete data structure for a single Kanji character, including its meaning, readings (Onyomi, Kunyomi), stroke count, and radical.
-   **`generate_vocabulary_data(word, jlpt_level)`**: Creates a detailed entry for a vocabulary word, including its reading, meaning, and example sentences (both Japanese and English).
-   **`generate_grammar_data(grammar_point, jlpt_level)`**: Generates a comprehensive explanation for a grammar point, including its structure, usage, nuances, and example sentences.

## 2. Quiz Question Generation

The AI can generate a variety of question types, all of which return a structured JSON object ready to be inserted into the database.

### 2.1. Standard Question Types

-   **`generate_true_false_question(topic, difficulty, keywords)`**: Creates a true/false statement with a detailed explanation of the correct answer.
-   **`generate_fill_in_the_blank_question(topic, difficulty, keywords)`**: Generates a sentence with a blank (`___`), the correct answer, and an explanation.
-   **`generate_matching_question(topic, difficulty, keywords)`**: Creates a set of pairs (e.g., a word and its meaning) for a matching exercise.
-   **`generate_multiple_choice_question(topic, difficulty, keywords)`**: Generates a standard multiple-choice question with plausible distractors, feedback for each option, a hint, and a difficulty level.

### 2.2. Advanced Quiz Generation

-   **`create_adaptive_quiz(topic, difficulty_levels, num_questions_per_level)`**: This is a powerful function that generates a complete quiz with multiple questions across a range of specified difficulty levels. It's the foundation for creating adaptive learning experiences where the quiz difficulty can be tailored to the user's performance.

## 3. Multimedia Content Generation

The system can enhance lessons with AI-generated multimedia content.

### 3.1. Image Generation

-   **`generate_image_prompt(content_text, lesson_topic, difficulty)`**: An internal helper that analyzes lesson text and creates an optimized, detailed prompt for an AI image generation service (like DALL-E).
-   **`generate_single_image(prompt, size, quality)`**: Generates a single image based on a given prompt.
-   **`generate_lesson_images(lesson_content_list, lesson_topic, difficulty)`**: A higher-level function that iterates through lesson content, generates optimized prompts for each piece of text, and creates a set of images for the lesson.

### 3.2. Multimedia Analysis

-   **`analyze_content_for_multimedia_needs(content_text, lesson_topic)`**: This function analyzes a block of text and returns a structured JSON object suggesting where multimedia enhancements (images, audio, video, interactive elements) could be most effective. This can be used to guide the automated or manual enhancement of lessons.

## 4. Lesson and Lesson Series Generation

While not directly part of the `AILessonContentGenerator`, the following scripts leverage the AI capabilities to build lessons and series:

-   **`create_adaptive_quiz_lesson.py`**: A script that demonstrates how to use `create_adaptive_quiz` to build a complete, interactive, and adaptive quiz lesson.
-   **`lesson_series_generator.py`**: A script that can take a configuration file to generate an entire series of lessons, including setting up prerequisites between them. This allows for the rapid creation of structured learning paths, such as a full JLPT level preparation course.

This suite of AI tools provides a powerful and flexible system for creating rich, interactive, and pedagogically sound Japanese language lessons with a high degree of automation.
