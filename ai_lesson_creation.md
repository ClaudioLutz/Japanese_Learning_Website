# AI-Assisted Lesson Content Generation Plan

## 1. Introduction

This document outlines a plan to integrate Artificial Intelligence, specifically OpenAI language models, into the lesson creation process of this Japanese learning platform. The primary goal is to leverage AI to assist administrators in generating various types of lesson content more efficiently.

**Benefits:**

*   **Accelerated Content Creation:** Reduce the time and effort required to draft lesson materials.
*   **Diverse Content Generation:** Easily create a wider range of examples, explanations, and questions.
*   **Scalability:** Facilitate the expansion of the lesson library.
*   **Inspiration:** Provide admins with starting points and ideas for content.

## 2. Prerequisites

*   **OpenAI API Key:** A valid API key for accessing OpenAI models (e.g., GPT-3.5 Turbo, GPT-4).
*   **Python Libraries:** The `openai` Python library installed in the application environment.
*   **Lesson System Foundation:** Completion of the `lesson_enhancement_plan` (Phases 1-6). This existing plan details the creation of a robust system for managing lessons with various content types (`LessonContent`, `QuizQuestion`, etc.), which is crucial for storing and organizing AI-generated materials.

## 3. Core Idea: AI-Assisted Content Blocks

The AI integration will primarily focus on assisting with the creation of individual `LessonContent` items.

*   **Textual Content:** For `LessonContent` items where `content_type = 'text'`, AI can generate:
    *   Explanations of grammar points, vocabulary, or cultural concepts.
    *   Example sentences or short dialogues.
    *   Instructions or introductory text.
*   **Interactive Content:** For `LessonContent` items where `content_type = 'interactive'`, AI can help generate components for `QuizQuestion` and `QuizOption` models:
    *   Multiple-choice questions (question stem, correct answer, plausible distractors, feedback).
    *   Fill-in-the-blank questions (sentence with a blank, correct answer(s)).
    *   True/False statements and their veracity.
    *   Explanations for correct answers.
*   **Media Descriptions/Scripts:**
    *   For `image` content, AI can generate descriptive text or titles.
    *   For `audio` or `video` content, AI can help draft scripts or summaries.

## 4. Proposed Workflow Integration

The AI generation capabilities will be embedded within the existing admin content creation interface.

### 4.1. Admin Interface Enhancement

*   **Location:** Within the "Add Content" modal (developed in Phase 1 of `lesson_enhancement_plan`).
*   **Trigger:** For relevant `LessonContent` types (e.g., "Text", "Multiple Choice Question"), an "✨ Generate with AI" button will be added.

### 4.2. AI Generation Modal/Section

Clicking "✨ Generate with AI" will reveal a dedicated section or open a new modal with the following input fields:

*   **`Lesson Context/Topic`**: A brief description of the current lesson or specific learning objective (e.g., "Explaining the particle 'は'", "Practicing verb conjugation for '食べる'"). This could be partially pre-filled from the current lesson's title or description.
*   **`Target Audience/Difficulty`**: (e.g., "Absolute Beginner", "JLPT N4 Level", "Intermediate"). This can be pre-filled from `Lesson.difficulty_level`.
*   **`Content Type to Generate`**: A dropdown to specify the desired output:
    *   "Explanation Paragraph"
    *   "Example Sentences (Set of 3)"
    *   "Short Dialogue"
    *   "Multiple Choice Question (with 4 options)"
    *   "Fill-in-the-Blank Exercise"
    *   "True/False Statement"
*   **`Keywords/Key Concepts (Optional)`**: Specific terms or ideas the AI should focus on or include (e.g., "politeness", "past tense", "contrastive 'wa'").
*   **`Desired Length/Format (Optional)`**: Guidance for the AI (e.g., "1 short paragraph", "List of 5 items", "A question about usage").
*   **`Tone (Optional)`**: (e.g., "Formal", "Casual", "Encouraging").

### 4.3. AI Interaction and Content Population

*   **API Call:** Based on the inputs, the backend will construct a detailed prompt and make a call to the OpenAI API.
*   **Displaying Results:** The AI-generated content will be displayed in the modal (e.g., in a textarea for text, or a structured preview for quizzes).
*   **Admin Actions:**
    *   **"Use This Content"**: Populates the relevant fields in the main "Add Content" form with the AI-generated text/data.
    *   **"Regenerate"**: Calls the API again, possibly with minor variations in the prompt or a request for a different response.
    *   **"Refine/Edit"**: Allows the admin to directly edit the AI-generated content within the AI modal before using it.
    *   **"Cancel"**: Closes the AI generation modal.
*   **Final Review:** Once content is populated into the main form, the admin can perform final reviews and edits before saving the `LessonContent` item.

## 5. Backend Implementation

### 5.1. New API Endpoint

*   **Endpoint:** `/api/admin/generate-ai-content` (Method: `POST`)
*   **Request Body:** JSON payload containing parameters from the AI Generation Modal (topic, audience, content type, keywords, etc.).
*   **Processing:**
    1.  Receive request.
    2.  Construct a suitable prompt for the OpenAI API based on the input parameters and the selected `Content Type to Generate`.
    3.  Retrieve the OpenAI API key securely (e.g., from an environment variable).
    4.  Call the OpenAI API (e.g., `client.chat.completions.create` with `gpt-3.5-turbo` or a more advanced model).
    5.  Process the API response.
    6.  Return the generated content (e.g., as a JSON object `{ "generated_text": "..." }` or a structured JSON for quizzes).
*   **Error Handling:** Implement robust error handling for API call failures, timeouts, or invalid responses.

### 5.2. Prompt Engineering

Developing effective prompts is crucial for getting high-quality results. Prompts should be clear, specific, and provide context.

**Example Prompt - Text Explanation:**

```
System: You are an expert Japanese language teacher and content creator for an online learning platform. Your tone should be clear, encouraging, and accurate.

User:
Lesson Topic/Objective: {lesson_topic}
Target Audience/Difficulty: {target_audience}
Content Type to Generate: Explanation Paragraph
Keywords/Key Concepts: {keywords}
Desired Length/Format: {desired_length}

Please generate an explanation paragraph for the lesson.
```

**Example Prompt - Multiple Choice Question:**

```
System: You are an expert Japanese language teacher designing quiz questions. Ensure questions are unambiguous and distractors are plausible.

User:
Lesson Topic/Objective: {lesson_topic}
Target Audience/Difficulty: {target_audience}
Content Type to Generate: Multiple Choice Question
Keywords/Key Concepts: {key_concept_to_test}

Generate a multiple-choice question.
Provide one correct answer and three plausible incorrect distractors.
Include brief feedback for each option (why it's correct or incorrect).
Format the output as a single JSON object with the following structure:
{
  "question_text": "The question text...",
  "options": [
    {"text": "Option A text...", "is_correct": false, "feedback": "Feedback for A..."},
    {"text": "Option B text...", "is_correct": true, "feedback": "Feedback for B..."},
    {"text": "Option C text...", "is_correct": false, "feedback": "Feedback for C..."},
    {"text": "Option D text...", "is_correct": false, "feedback": "Feedback for D..."}
  ],
  "overall_explanation": "General explanation for the correct answer if needed..."
}
```

## 6. Database Model Considerations

*   The existing models (`LessonContent`, `QuizQuestion`, `QuizOption`) from `app/models.py` (as per the `lesson_enhancement_plan`) are largely sufficient for storing AI-generated content.
    *   `LessonContent.content_text` will store generated textual explanations.
    *   `QuizQuestion.question_text`, `QuizQuestion.explanation`, `QuizOption.option_text`, `QuizOption.is_correct`, `QuizOption.feedback` will store components of generated interactive questions.
*   **Optional Enhancement:** Consider adding a field to `LessonContent` to track AI usage:
    *   `generated_by_ai (Boolean, default=False)`: A simple flag.
    *   `ai_generation_details (JSON, nullable=True)`: To store metadata like the model used, prompt snippet, or generation timestamp. This can be useful for auditing and improving prompts.

## 7. Specific Content Type Examples & Integration Points

### 7.1. Text Content (`LessonContent.content_type = 'text'`)

*   **Use Cases:** Generating explanations, example dialogues, cultural insights, instructions.
*   **Integration:** "✨ Generate with AI" button in the text content creation form. Generated text populates `LessonContent.content_text`.

### 7.2. Interactive Content (`LessonContent.content_type = 'interactive'`)

*   **Use Cases:**
    *   **Multiple Choice:** Generating question, options, correct answer designation, and feedback.
    *   **Fill-in-the-Blank:** Generating a sentence with a `[BLANK]` placeholder and the expected answer(s).
    *   **True/False:** Generating a statement and determining its truth value.
*   **Integration:** "✨ Generate with AI" button in the interactive content creation form. Generated data (likely JSON) is parsed to populate fields in `QuizQuestion` and its associated `QuizOption` objects.

### 7.3. Assisting Core Data Models (`Kana`, `Kanji`, `Vocabulary`, `Grammar`)

While these models represent factual data and have their own admin management interfaces, AI can still assist:

*   **Vocabulary:**
    *   Generate `example_sentence_japanese` and `example_sentence_english`.
    *   Suggest related vocabulary items.
*   **Kanji:**
    *   Draft initial `meaning` descriptions.
    *   Generate example words using the Kanji (though verification is critical).
*   **Grammar:**
    *   Draft `explanation` text.
    *   Generate `example_sentences`.
*   **Integration:** Instead of a full "Generate Content" block, this might involve smaller "AI Assist" icons next to specific fields (e.g., next to "Example Sentence" in the Vocabulary form). Clicking this would make a targeted API call.

## 8. Human Review and Oversight - CRITICAL

**AI-generated content must ALWAYS be thoroughly reviewed, edited, and validated by a human administrator or subject matter expert before being saved and published.**

*   AI is a powerful assistant, but it can make mistakes, generate subtly incorrect information, or produce content that doesn't perfectly align with the pedagogical goals.
*   The admin retains full control and responsibility for the final content.
*   The AI's role is to accelerate the drafting process, not to replace human expertise.

## 9. Future Possibilities

*   **Image Generation Prompts:** For `LessonContent` of type `image`, AI could generate descriptive prompts that can be fed into AI image generation tools (e.g., DALL-E, Stable Diffusion).
*   **Audio Script Generation:** For `LessonContent` of type `audio`, AI can generate scripts, which can then be recorded by a human or used with Text-to-Speech (TTS) services.
*   **Video Script Outlines:** For `video` content, AI can help outline scripts or talking points.
*   **Personalized Content Variations:** Explore generating slight variations of explanations or examples tailored to different user learning styles or proficiency levels (a more advanced feature).
*   **Automated Lesson Structuring:** Based on a high-level topic (e.g., "JLPT N5 Grammar Review"), AI could suggest a sequence of `LessonContent` items or subtopics.
*   **Content Idea Generation:** An "Ideation" tool where admins can input a theme and get AI suggestions for lesson topics or content types.

## 10. Conclusion

Integrating AI into the lesson creation workflow offers significant potential to enhance productivity and content diversity. By thoughtfully embedding AI assistance within the well-structured `lesson_enhancement_plan`, the platform can empower administrators to build engaging and comprehensive Japanese lessons more effectively. The key to success lies in treating AI as a collaborative tool, always coupled with rigorous human oversight and quality control.
