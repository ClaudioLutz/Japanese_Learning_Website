# 23. User Progress and Quiz System

## 1. Overview

The application features a robust system for tracking user progress through lessons and for creating and managing interactive quizzes. This system is essential for providing an engaging and effective learning experience, allowing users to test their knowledge and monitor their advancement through the curriculum.

The core logic is defined by the relationships and methods within the SQLAlchemy models in `app/models.py`.

## 2. User Progress Tracking

User progress is primarily managed by the `UserLessonProgress` model.

### 2.1. `UserLessonProgress` Model

This model creates a unique record for each user for each lesson they have started. It acts as a join table between `User` and `Lesson` but with many additional fields to store detailed progress information.

-   **Key Fields**:
    -   `user_id`: Foreign key to the `User`.
    -   `lesson_id`: Foreign key to the `Lesson`.
    -   `is_completed`: A boolean flag that is set to `True` when the user finishes a lesson.
    -   `progress_percentage`: An integer (0-100) representing the percentage of the lesson's content items the user has completed.
    -   `content_progress`: A JSON text field that stores the completion status of individual `LessonContent` items within the lesson. This provides granular tracking. Example: `{"101": true, "102": true, "103": false}`.
    -   `started_at`, `completed_at`, `last_accessed`: Timestamps to monitor user engagement.

### 2.2. How Progress is Updated

1.  **Starting a Lesson**: When a user accesses a lesson for the first time, a `UserLessonProgress` record is created.
2.  **Completing Content**: As a user moves through a lesson, the application backend calls the `mark_content_completed(content_id)` method on their `UserLessonProgress` instance.
3.  **Calculating Percentage**: The `update_progress_percentage()` method is then called. It calculates the number of completed content items against the total number of items in the lesson to update the `progress_percentage`.
4.  **Completing a Lesson**: When `progress_percentage` reaches 100, the `is_completed` flag is automatically set to `True`, and the `completed_at` timestamp is recorded.

### 2.3. Resetting Progress

The `reset()` method on the `UserLessonProgress` model provides a way to completely reset a user's progress for a specific lesson. It clears all progress fields and, importantly, deletes all of the user's `UserQuizAnswer` records associated with that lesson, allowing them to retake quizzes.

## 3. Interactive Quiz System

The quiz system is designed to be flexible and is built into the `LessonContent` model.

### 3.1. Architecture

A quiz is not a separate model but rather a `LessonContent` item that is marked as interactive.

1.  **`LessonContent` as a Quiz Container**: A `LessonContent` record with `is_interactive` set to `True` serves as the container for a quiz. It can have settings like `max_attempts` and `passing_score`.
2.  **`QuizQuestion` Model**: Each interactive `LessonContent` item can have multiple `QuizQuestion` records associated with it. This model stores the question text, type, and explanation.
3.  **`QuizOption` Model**: For multiple-choice questions, each `QuizQuestion` can have multiple `QuizOption` records. Each option stores its text and whether it is the correct answer.
4.  **`UserQuizAnswer` Model**: This model records a user's specific answer to a question, linking a `User`, a `QuizQuestion`, and the `QuizOption` they selected. It also stores whether their answer was correct and the number of attempts.

This structure allows for quizzes to be placed anywhere within a lesson, just like any other piece of content.

### 3.2. Question Types

The system is designed to support multiple question types, identified by the `question_type` field in the `QuizQuestion` model. The AI generation service can create content for:
-   `multiple_choice`
-   `true_false`
-   `fill_blank`
-   `matching`

### 3.3. Storing and Evaluating Answers

-   When a user submits a quiz, the application logic checks their answers against the `is_correct` flag on the `QuizOption`s.
-   A `UserQuizAnswer` record is created or updated for each question.
-   The user's score is calculated and compared against the `passing_score` on the parent `LessonContent` item.
-   Based on the result, the user either passes and the content item is marked as complete, or they are prompted to try again if they have attempts remaining.

## 4. Implementation in Routes and Templates

### 4.1. Displaying Progress

-   In routes that display lists of lessons, the controller can query the `UserLessonProgress` model to fetch the current user's progress for each lesson.
-   This allows the template to display visual indicators like progress bars, completion checkmarks, or "Start Lesson" vs. "Continue Lesson" buttons.

### 4.2. Rendering a Quiz

-   When rendering a `lesson_view.html` template, the logic checks if a `LessonContent` item is interactive.
-   If it is, the template iterates through the `content.quiz_questions` and their `question.options` to render the quiz form.
-   The form would post to a dedicated route for handling quiz submissions.

### 4.3. Handling a Quiz Submission

-   A route like `/lesson/submit_quiz/<int:content_id>` would receive the form data.
-   The route logic would:
    1.  Validate the submission and protect against CSRF.
    2.  Iterate through the user's answers.
    3.  For each answer, create or update a `UserQuizAnswer` record.
    4.  Calculate the total score.
    5.  If the score meets the `passing_score`, call `mark_content_completed()` on the user's `UserLessonProgress` for the lesson.
    6.  Redirect the user to a results page or the next piece of content.
