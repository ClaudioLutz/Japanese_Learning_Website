# Lesson System Architecture

## 1. Overview

The Japanese Learning Website features a robust and flexible lesson system designed to deliver structured educational content to users. This system allows administrators to create rich, multi-page lessons combining various types of content, including core Japanese language elements (Kana, Kanji, Vocabulary, Grammar), multimedia (text, images, video, audio), and interactive quizzes. Users can progress through lessons, and their progress is tracked.

## 2. Core Components & Models

The lesson system is primarily built around the following SQLAlchemy models (defined in `app/models.py`):

-   **`LessonCategory`**: Organizes lessons into logical groups (e.g., "Hiragana Basics," "JLPT N5 Grammar").
-   **`Lesson`**: Represents a single unit of learning. It contains metadata like title, description, type (free/premium), difficulty, and links to its content and pages.
-   **`LessonPage`**: Defines individual pages within a lesson, allowing for a multi-page structure. Each page can have an optional title and description.
-   **`LessonContent`**: Represents an individual piece of content displayed on a `LessonPage`. This is a versatile model that can link to core content types (Kana, Kanji, etc.), store custom text, link to media files, or define interactive quizzes.
-   **`LessonPrerequisite`**: Manages dependencies between lessons, requiring users to complete certain lessons before accessing others.
-   **`UserLessonProgress`**: Tracks an individual user's progress through a specific lesson, including completion status, percentage, and progress on individual content items.
-   **`QuizQuestion`**, **`QuizOption`**, **`UserQuizAnswer`**: Support interactive quiz functionality within lessons. (Covered in more detail in quiz-specific documentation, but part of the lesson content).

## 3. Lesson Structure

### 3.1. Categories
- Lessons are grouped into `LessonCategory` instances.
- Categories help users find relevant content and provide organizational structure for administrators.
- Each category can have a name, description, and a color code for UI theming.

### 3.2. Lessons
- Each `Lesson` belongs to a `LessonCategory` (optional, but recommended).
- Key attributes of a `Lesson`:
    - `title`, `description`
    - `lesson_type` ('free' or 'premium'): Controls access based on user subscription.
    - `difficulty_level`, `estimated_duration`
    - `order_index`: For ordering lessons within a category or globally.
    - `is_published`: Controls visibility to end-users.
    - `thumbnail_url`, `video_intro_url`: For presentation.

### 3.3. Lesson Pages
- A `Lesson` is composed of one or more `LessonPage`s.
- The `LessonPage` model stores `page_number`, `title` (optional), and `description` (optional) for each page.
- This allows for content to be broken down into manageable segments.
- The `Lesson.pages` property dynamically groups `LessonContent` items by their `page_number` and associates them with `LessonPage` metadata.

### 3.4. Lesson Content Items
- Each `LessonPage` displays one or more `LessonContent` items.
- `LessonContent` items have an `order_index` to define their sequence on a page.
- A `LessonContent` item can be of various `content_type`s:
    - **Core Content Links**: 'kana', 'kanji', 'vocabulary', 'grammar'. The `content_id` field links to the ID of the respective core content item.
    - **Multimedia/Custom Content**: 'text', 'image', 'video', 'audio'.
        - For 'text', the `content_text` field stores the textual information.
        - For 'image', 'video', 'audio':
            - `media_url` can store an external URL.
            - `file_path` (along with `file_size`, `file_type`, `original_filename`) is used for server-uploaded files. The `get_file_url()` method provides the accessible URL.
    - **Interactive Quiz**: If `is_interactive` is true, this `LessonContent` item acts as a container for `QuizQuestion`s.
- `LessonContent` items can be marked as `is_optional`.
- AI-generated content is tracked via `generated_by_ai` and `ai_generation_details`.

## 4. Content Creation and Management (Admin Flow)

Refer to `08-Admin-Content-Management.md` for detailed UI/UX flows.

1.  **Create/Select Category**: Lessons are typically assigned to a category.
2.  **Create Lesson**: Define lesson metadata (title, type, difficulty, etc.).
3.  **Manage Lesson Pages**:
    - Add new pages to the lesson.
    - Define page numbers (or allow auto-numbering/ordering).
    - Optionally add titles and descriptions to pages via `LessonPage` records.
4.  **Add Content to Pages**:
    - For a selected page, add `LessonContent` items.
    - Choose `content_type`.
    - If linking to existing core content, search and select the item (e.g., a specific Kanji).
    - If adding new text, type it in (possibly with a rich text editor).
    - If adding media, upload the file or provide a URL. The system uses `FileUploadHandler` for secure uploads.
    - If adding a quiz, mark `is_interactive=True` and then add `QuizQuestion`s to this `LessonContent` item.
    - Use the "✨ Generate with AI" feature for text or quiz questions (see `18-AI-Lesson-Creation.md`).
5.  **Order Content**: Arrange `LessonContent` items on a page using `order_index`. Arrange pages within a lesson.
6.  **Set Prerequisites**: Define any `LessonPrerequisite`s for the lesson.
7.  **Publish Lesson**: Set `is_published=True` to make it available to users.

## 5. Lesson Consumption (User Flow)

1.  **Browse Lessons**: Users browse lessons, perhaps filtered by category.
2.  **View Lesson**: When a user selects a lesson:
    - The system checks accessibility (`Lesson.is_accessible_to_user()` method):
        - Verifies subscription level against `Lesson.lesson_type`.
        - Verifies if all prerequisite lessons are completed by checking `UserLessonProgress`.
    - If accessible, the lesson's first page is displayed.
3.  **Navigate Pages**: Users navigate through `LessonPage`s sequentially (e.g., using a carousel or next/previous buttons).
    - The `Lesson.pages` property provides the structure for rendering, grouping content items by page number and including page-specific titles/descriptions.
4.  **Interact with Content**:
    - View text, images, videos.
    - Study linked Kana, Kanji, Vocabulary, Grammar items.
    - Complete interactive quizzes.
5.  **Progress Tracking**:
    - When a user starts a lesson, a `UserLessonProgress` record is created (or retrieved if it exists).
    - As the user interacts with content (e.g., marks items as complete, submits quizzes), the `UserLessonProgress.content_progress` (JSON field) is updated.
    - `UserLessonProgress.progress_percentage` is recalculated.
    - If all non-optional content is completed, `UserLessonProgress.is_completed` is set to `True`, and `completed_at` is timestamped.
    - `UserQuizAnswer` records store attempts and correctness for quiz questions.

## 6. Key Functionalities and Logic

### 6.1. Prerequisites (`Lesson.is_accessible_to_user()`)
- This method in the `Lesson` model checks if a user has completed all lessons listed in its `prerequisites` relationship by looking up the `UserLessonProgress` for that user and each prerequisite lesson.

### 6.2. Content Ordering and Pagination (`Lesson.pages` property)
- This dynamic property on the `Lesson` model is crucial for rendering.
- It fetches all `LessonContent` items for the lesson.
- It also fetches all `LessonPage` metadata entries for the lesson.
- It sorts content items first by `page_number`, then by their `order_index` within that page.
- It groups these sorted content items under their respective page numbers.
- It associates the `LessonPage` metadata (title, description) with each page group.
- The result is a list of page structures, each containing its metadata and an ordered list of its content.

### 6.3. Progress Tracking (`UserLessonProgress` methods)
- `get_content_progress()` / `set_content_progress()`: Manage the JSON dictionary storing completion status of individual `LessonContent` items.
- `mark_content_completed(content_id)`: Updates the JSON and calls `update_progress_percentage()`.
- `update_progress_percentage()`: Calculates overall lesson completion based on the number of completed (non-optional, though this distinction might need explicit handling if not all content counts towards completion) `LessonContent` items. Sets `is_completed` if 100%.
- `reset()`: Clears progress for a lesson, including associated quiz answers.

### 6.4. Serving Uploaded Files (`LessonContent.get_file_url()` and `routes.uploaded_file`)
- Uploaded files are stored relative to `UPLOAD_FOLDER`.
- `LessonContent.file_path` stores this relative path.
- `get_file_url()` generates a URL using `url_for('routes.uploaded_file', filename=self.file_path)`.
- A dedicated route (e.g., `/uploads/<path:filename>`) in `app/routes.py` uses `send_from_directory` to securely serve files from the `UPLOAD_FOLDER`.

## 7. Extensibility

-   **New Content Types**: New `content_type` values can be added to `LessonContent`. The `get_content_data()` method and admin interface would need updates to support linking or displaying these new types.
-   **Advanced Interactivity**: The `QuizQuestion` and `QuizOption` models can be extended or new models created for more complex interactions beyond simple quizzes.
-   **Learning Path Algorithms**: The prerequisite system can be expanded for more dynamic learning path generation.

This system provides a solid foundation for delivering diverse educational content in a structured and trackable manner.
