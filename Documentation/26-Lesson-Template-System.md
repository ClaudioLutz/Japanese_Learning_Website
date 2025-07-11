# 26. Lesson Template System

The Lesson Template System provides a streamlined process for creating new lessons using predefined JSON templates. This system is designed to accelerate content creation and ensure consistency across lessons of the same type.

## Key Components

- **`lesson_template.py`**: This module contains the `LessonTemplate` class, which is responsible for loading templates and generating lessons from them.
- **`lesson_templates/`**: This directory stores the JSON lesson templates.

## Template Structure

Lesson templates are JSON files that define the structure and content of a lesson. They include placeholders that can be dynamically replaced with specific content.

**Example: `vocabulary_lesson_template.json`**

```json
{
    "lesson": {
        "title": "Vocabulary: {topic}",
        "description": "A lesson on {topic} vocabulary.",
        "lesson_type": "free",
        "difficulty_level": 2,
        "category_id": 1
    },
    "pages": [
        {
            "title": "Introduction to {topic}",
            "content": [
                {
                    "type": "text",
                    "text": "This lesson introduces key vocabulary related to {topic}."
                }
            ]
        },
        {
            "title": "Core Vocabulary",
            "content": [
                {
                    "type": "text",
                    "text": "Here are the core vocabulary words for {topic}:\n\n- {vocab1}\n- {vocab2}\n- {vocab3}"
                }
            ]
        },
        {
            "title": "Quiz",
            "content": [
                {
                    "type": "quiz",
                    "text": "Test your knowledge of {topic} vocabulary."
                }
            ]
        }
    ]
}
```

## Creating a Lesson from a Template

To create a lesson from a template, you can use a script like `create_lesson_from_template.py`. This script loads a template, defines the values for the placeholders, and then creates the lesson.

**Example Usage:**

```python
from lesson_template import LessonTemplate

template_path = 'lesson_templates/vocabulary_lesson_template.json'
lesson_template = LessonTemplate(template_path)

template_vars = {
    'topic': 'Food',
    'vocab1': 'Sushi',
    'vocab2': 'Ramen',
    'vocab3': 'Tempura'
}

lesson = lesson_template.create_lesson_from_template(**template_vars)
