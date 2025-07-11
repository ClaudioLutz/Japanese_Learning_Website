# 18. AI Content Generation System

## 1. Overview

The AI Content Generation system is a core feature of the project, designed to automate and assist in the creation of high-quality, diverse educational content. It is built around the `AILessonContentGenerator` service class, which interfaces with OpenAI's API (including GPT-4 and DALL-E 3) to produce everything from text explanations and quiz questions to structured database entries and multimedia assets.

This system is integral to the lesson creation scripts and can be leveraged for future admin-facing tools.

## 2. Architecture

The system is designed with a clear separation of concerns, ensuring that AI logic is centralized and reusable.

```
+---------------------------+      +--------------------------------+      +-----------------+
|   Lesson Creation Script  |----->|   AILessonContentGenerator     |----->|   OpenAI API    |
| (e.g., create_kanji.py)   |      |   (in app/ai_services.py)      |      | (GPT-4, DALL-E) |
+---------------------------+      +--------------------------------+      +-----------------+
             |                                  |                                  ^
             |                                  v                                  |
             |                     +--------------------------+                     |
             +-------------------->|   Database Models        |<--------------------+
                                   |   (e.g., Kanji, Lesson)  |
                                   +--------------------------+
```

-   **Lesson Creation Scripts**: Act as clients, requesting specific content from the AI service.
-   **AI Service (`AILessonContentGenerator`)**: The central component. It contains all the logic for prompt engineering, interacting with the OpenAI API, and formatting the responses.
-   **OpenAI API**: The external service that performs the actual generation.
-   **Database Models**: The generated content is ultimately stored in the application's database.

## 3. The `AILessonContentGenerator` Service

The heart of the system is the `AILessonContentGenerator` class located in `app/ai_services.py`.

### 3.1. Initialization

The class is initialized without arguments. It automatically retrieves the `OPENAI_API_KEY` from the environment variables and sets up the OpenAI client.

```python
from app.ai_services import AILessonContentGenerator

# The generator is ready to use upon instantiation
generator = AILessonContentGenerator()
```

### 3.2. Core Generation Methods

The service provides a comprehensive suite of methods for generating various types of content. Each method is designed for a specific purpose and returns a structured dictionary or JSON object.

| Method                                     | Description                                                                                                 | Output Type |
| ------------------------------------------ | ----------------------------------------------------------------------------------------------------------- | ----------- |
| `generate_explanation(...)`                | Generates a simple, plain-text explanation on a given topic.                                                | `dict`      |
| `generate_formatted_explanation(...)`      | Generates an explanation using basic HTML tags (`<h2>`, `<p>`, `<strong>`, `<ul>`) for rich text formatting.     | `dict`      |
| `generate_true_false_question(...)`        | Creates a true/false question with the question, the correct boolean answer, and a detailed explanation.      | `JSON`      |
| `generate_fill_in_the_blank_question(...)` | Creates a fill-in-the-blank question with the gapped sentence, the correct answer, and an explanation.        | `JSON`      |
| `generate_multiple_choice_question(...)`   | Creates a multiple-choice question with 4 options, feedback for each, and an overall explanation.           | `JSON`      |
| `generate_matching_question(...)`          | Creates a matching question with a set of prompt/answer pairs and a general explanation.                      | `JSON`      |
| `generate_kanji_data(...)`                 | Generates a structured data object for a single Kanji character (meaning, readings, stroke count, etc.).      | `JSON`      |
| `generate_vocabulary_data(...)`            | Generates a structured data object for a vocabulary word (reading, meaning, example sentences, etc.).         | `JSON`      |
| `generate_grammar_data(...)`               | Generates a structured data object for a grammar point (explanation, structure, example sentences, etc.).     | `JSON`      |
| `generate_image_prompt(...)`               | Takes lesson context and generates an optimized, detailed prompt suitable for an image generation model.      | `dict`      |
| `generate_single_image(...)`               | Generates a single image using DALL-E 3 from a given prompt.                                                | `dict`      |
| `generate_lesson_images(...)`              | Generates multiple images for a list of lesson content items.                                               | `dict`      |
| `analyze_content_for_multimedia_needs(...)`| Analyzes a block of text and suggests potential multimedia enhancements (images, audio, video, etc.).         | `JSON`      |

### 3.3. Prompt Engineering and JSON Mode

-   **System Prompts**: Each method uses a carefully crafted "system prompt" to instruct the AI on its role (e.g., "You are an expert Japanese language teacher"), tone, and output format.
-   **JSON Mode**: For methods that need structured data (like quizzes and database entries), the service instructs the OpenAI API to use `json_object` mode. This ensures the AI's response is a valid, parsable JSON string, which the service then decodes before returning. This greatly improves reliability.

## 4. Content Generation Capabilities

### 4.1. Text and HTML Content

-   **Plain Text**: `generate_explanation` is used for simple text blocks.
-   **Rich Text (HTML)**: `generate_formatted_explanation` is used to create content with headings, lists, and bold text, which can be rendered directly in the frontend.

### 4.2. Quiz and Interactive Content

The service can generate a variety of question types, all in a structured JSON format ready to be parsed and stored in the `QuizQuestion` and `QuizOption` database models.

-   **Multiple Choice**: The most detailed, with per-option feedback.
-   **True/False**: Simple and effective for checking knowledge.
-   **Fill-in-the-Blank**: Ideal for vocabulary and grammar practice.
-   **Matching**: Good for connecting concepts (e.g., Kanji to meanings).

### 4.3. Database Content Population

A key capability is generating structured data that directly maps to the project's core content models. This is heavily used by the `_database_aware` creation scripts.

-   `generate_kanji_data` -> Populates the `Kanji` model.
-   `generate_vocabulary_data` -> Populates the `Vocabulary` model.
-   `generate_grammar_data` -> Populates the `Grammar` model.

### 4.4. Image and Multimedia Content

The system integrates with DALL-E 3 for image generation.

-   **Prompt Generation**: `generate_image_prompt` acts as a "prompt engineer," converting simple lesson text into a detailed, effective prompt for the image model.
-   **Image Generation**: `generate_single_image` and `generate_lesson_images` handle the actual calls to the DALL-E API and return the URL of the generated image.
-   **Needs Analysis**: `analyze_content_for_multimedia_needs` can be used to programmatically suggest where images or other media would be most beneficial.

## 5. Configuration

### 5.1. Environment Variables

The only required configuration is the OpenAI API key, which must be set in the `.env` file in the project root:

```env
OPENAI_API_KEY="sk-YourSecretKeyHere"
```

### 5.2. Dependencies

The service relies on the `openai` Python package.

```
# In requirements.txt
openai>=1.0.0
```

## 6. Security and Error Handling

-   **API Key Security**: The API key is loaded from an environment variable and is never exposed to the client-side or committed to version control.
-   **Error Handling**: The internal `_generate_content` method includes a `try...except` block to catch and log any errors during the API call (e.g., network issues, authentication failures, rate limits). Methods return an `error` key in their response dictionary if something goes wrong.
-   **JSON Parsing**: Methods expecting JSON responses include an additional `try...except` block to handle cases where the AI returns a malformed or non-JSON response, preventing crashes.
