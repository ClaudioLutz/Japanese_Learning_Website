# 24. AI Content Generation Capabilities

This document provides a comprehensive overview of the AI-powered content generation features available in the system. The core of this functionality resides in the `AILessonContentGenerator` class located in `app/ai_services.py`.

## 1. Core Content Generation

### 1.1. Text Explanations

-   **`generate_explanation(topic, difficulty, keywords)`**: Generates a simple, plain-text paragraph explaining a given topic. Ideal for brief introductions or definitions.
-   **`generate_formatted_explanation(topic, difficulty, keywords)`**: Creates a more detailed and structured explanation using HTML tags (`<h2>`, `<p>`, `<strong>`, `<ul>`, etc.). This is suitable for main lesson content. **IMPORTANT**: Always includes both Japanese characters AND their romanized pronunciation in parentheses to help beginners learn proper pronunciation alongside the written form.

### 1.2. Database Entity Generation

The AI can populate the database with foundational Japanese language data:

-   **`generate_kanji_data(kanji_character, jlpt_level)`**: Generates a complete data structure for a single Kanji character, including its meaning, readings (Onyomi, Kunyomi), stroke count, and radical.
-   **`generate_vocabulary_data(word, jlpt_level)`**: Creates a detailed entry for a vocabulary word, including its reading, meaning, and example sentences (both Japanese and English).
-   **`generate_grammar_data(grammar_point, jlpt_level)`**: Generates a comprehensive explanation for a grammar point, including its structure, usage, nuances, and example sentences.

## 2. Quiz Question Generation

The AI can generate a variety of question types, all of which return a structured JSON object ready to be inserted into the database.

### 2.1. Standard Question Types

-   **`generate_true_false_question(topic, difficulty, keywords)`**: Creates a true/false statement with a detailed explanation of the correct answer. Always includes romanization for Japanese terms.
-   **`generate_fill_in_the_blank_question(topic, difficulty, keywords)`**: Generates a sentence with a blank (`___`), the correct answer, and an explanation.
-   **`generate_matching_question(topic, difficulty, keywords)`**: Creates a set of pairs (e.g., Japanese words with romanization and their English meanings) for a matching exercise. Generates 4-6 pairs for optimal matching difficulty.
-   **`generate_multiple_choice_question(topic, difficulty, keywords, question_number=None)`**: Generates a standard multiple-choice question with plausible distractors, feedback for each option, a hint, and a difficulty level. Uses strategic romanization - includes it for context words but not for terms being tested. Supports variety prompts to create unique and varied questions.

### 2.2. Advanced Quiz Generation

-   **`create_adaptive_quiz(topic, difficulty_levels, num_questions_per_level)`**: This is a powerful function that generates a complete quiz with multiple questions across a range of specified difficulty levels. It's the foundation for creating adaptive learning experiences where the quiz difficulty can be tailored to the user's performance.

## 3. Multimedia Content Generation

The system can enhance lessons with AI-generated multimedia content.

### 3.1. Image Generation

-   **`generate_image_prompt(content_text, lesson_topic, difficulty)`**: An internal helper that analyzes lesson text and creates an optimized, detailed prompt for an AI image generation service (DALL-E 3).
-   **`generate_single_image(prompt, size="1024x1024", quality="standard")`**: Generates a single image using DALL-E 3 based on a given prompt. Supports multiple sizes ("1024x1024", "1792x1024", "1024x1792") and quality levels ("standard", "hd").
-   **`generate_lesson_images(lesson_content_list, lesson_topic, difficulty)`**: A higher-level function that iterates through lesson content, generates optimized prompts for each piece of text, and creates a set of images for the lesson using DALL-E 3.

### 3.2. Multimedia Analysis

-   **`analyze_content_for_multimedia_needs(content_text, lesson_topic)`**: This function analyzes a block of text and returns a structured JSON object suggesting where multimedia enhancements (images, audio, video, interactive elements) could be most effective. This can be used to guide the automated or manual enhancement of lessons.

## 4. API Integration

The AI content generation capabilities are exposed through several REST API endpoints:

### 4.1. Content Generation API

-   **`POST /api/admin/generate-ai-content`**: Main endpoint for generating text explanations and quiz content. Supports multiple content types:
    - `explanation`: Simple text explanations
    - `formatted_explanation`: HTML-formatted explanations with romanization
    - `multiple_choice_question`: Multiple choice questions with strategic romanization
    - `true_false_question`: True/false questions with explanations
    - `fill_blank_question`: Fill-in-the-blank questions
    - `matching_question`: Matching exercises with Japanese-English pairs

### 4.2. Image Generation API

-   **`POST /api/admin/generate-ai-image`**: Generates AI images for lesson content using DALL-E 3. Supports:
    - Direct prompt generation with customizable size and quality
    - Content-based image generation that analyzes lesson text and creates optimized prompts
    - Returns image URL, generated prompt, and metadata

### 4.3. Multimedia Analysis API

-   **`POST /api/admin/analyze-multimedia-needs`**: Analyzes lesson content and suggests multimedia enhancements
-   **`POST /api/admin/generate-lesson-images`**: Generates multiple images for lesson content

## 5. Technical Implementation Details

### 5.1. OpenAI Integration

The system uses OpenAI's latest models:
- **Text Generation**: GPT-4.5-preview for content and quiz generation
- **Image Generation**: DALL-E 3 for educational illustrations
- **Response Format**: Supports both text and structured JSON responses

### 5.2. Error Handling and Logging

- Comprehensive error handling for API failures
- Detailed logging for debugging and monitoring
- Graceful fallbacks for service unavailability

### 5.3. Content Quality Features

- **Romanization Strategy**: Strategic inclusion of romanized pronunciation to aid learning without giving away answers
- **Cultural Accuracy**: AI prompts emphasize culturally appropriate and accurate content
- **Educational Focus**: Content is optimized for pedagogical effectiveness at specified difficulty levels
- **Variety Generation**: Multiple question formats and approaches to prevent repetition

## 6. Lesson Creation Scripts

The system includes several enhanced lesson creation scripts that leverage AI capabilities:

-   **Database-Aware Scripts**: Smart integration with existing Kana, Kanji, Vocabulary, and Grammar content
-   **Multimedia Integration**: Automated AI image generation and file management
-   **Base Lesson Creator Framework**: Standardized, reusable lesson creation infrastructure
-   **Content Discovery System**: Automated gap analysis and content suggestions

This comprehensive AI system provides powerful automation for creating rich, interactive, and pedagogically sound Japanese language lessons with minimal manual effort.
