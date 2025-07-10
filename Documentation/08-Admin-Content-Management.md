# Admin Content Management

## 1. Overview

The Japanese Learning Website provides a comprehensive Admin Panel for managing all aspects of the learning content. Administrators can perform Create, Read, Update, and Delete (CRUD) operations on various content types, organize lessons, and manage learning pathways.

The Admin Panel is typically accessible via the `/admin` route after an administrator logs in.

## 2. Accessing the Admin Panel

1.  Navigate to the website's login page (e.g., `/login`).
2.  Log in using an account with administrator privileges (`is_admin=True`).
3.  Upon successful login, administrators are usually redirected to the Admin Dashboard (`/admin` or `/admin/dashboard`).
    - If not redirected automatically, navigate manually to `/admin`.

Access to all admin functionalities is protected by the `@admin_required` decorator, ensuring only authorized users can make changes.

## 3. Core Content Management Sections

The Admin Panel is typically organized into sections for managing different types of content:

### 3.1. Managing Kana (Hiragana & Katakana)

-   **View Kana**: Lists all existing Hiragana and Katakana characters, showing the character, romanization, and type.
-   **Add New Kana**:
    -   Fields: Character, Romanization, Type (Hiragana/Katakana), Stroke Order Info (URL/text), Example Sound URL.
    -   Validation: Ensures character is unique.
-   **Edit Kana**: Modify details of an existing Kana character.
-   **Delete Kana**: Remove a Kana character.
    -   *Consideration*: Deleting Kana used in lessons might require a warning or a way to update affected lessons.

**Associated API Endpoints (example):**
- `GET /api/admin/kana`
- `POST /api/admin/kana/new`
- `GET /api/admin/kana/<id>`
- `PUT /api/admin/kana/<id>/edit`
- `DELETE /api/admin/kana/<id>/delete`

### 3.2. Managing Kanji

-   **View Kanji**: Lists all existing Kanji characters, showing the character, meaning, readings, and JLPT level.
-   **Add New Kanji**:
    -   Fields: Character, Meaning, On'yomi, Kun'yomi, JLPT Level, Stroke Order Info, Radical, Stroke Count.
    -   Validation: Ensures character is unique.
-   **Edit Kanji**: Modify details of an existing Kanji character.
-   **Delete Kanji**: Remove a Kanji character.
    -   *Consideration*: Impact on lessons using this Kanji.

**Associated API Endpoints (example):**
- `GET /api/admin/kanji`
- `POST /api/admin/kanji/new`
- `GET /api/admin/kanji/<id>`
- `PUT /api/admin/kanji/<id>/edit`
- `DELETE /api/admin/kanji/<id>/delete`

### 3.3. Managing Vocabulary

-   **View Vocabulary**: Lists all vocabulary items, showing the word, reading, meaning, and JLPT level.
-   **Add New Vocabulary**:
    -   Fields: Word (Japanese), Reading (Hiragana/Katakana), Meaning (English), JLPT Level, Example Sentence (Japanese), Example Sentence (English), Audio URL.
    -   Validation: Ensures word is unique.
-   **Edit Vocabulary**: Modify details of an existing vocabulary item.
-   **Delete Vocabulary**: Remove a vocabulary item.
    -   *Consideration*: Impact on lessons.

**Associated API Endpoints (example):**
- `GET /api/admin/vocabulary`
- `POST /api/admin/vocabulary/new`
- `GET /api/admin/vocabulary/<id>`
- `PUT /api/admin/vocabulary/<id>/edit`
- `DELETE /api/admin/vocabulary/<id>/delete`

### 3.4. Managing Grammar

-   **View Grammar**: Lists all grammar points, showing the title and JLPT level.
-   **Add New Grammar**:
    -   Fields: Title, Explanation, Structure, JLPT Level, Example Sentences (Text).
    -   Validation: Ensures title is unique.
-   **Edit Grammar**: Modify details of an existing grammar point.
-   **Delete Grammar**: Remove a grammar point.
    -   *Consideration*: Impact on lessons.

**Associated API Endpoints (example):**
- `GET /api/admin/grammar`
- `POST /api/admin/grammar/new`
- `GET /api/admin/grammar/<id>`
- `PUT /api/admin/grammar/<id>/edit`
- `DELETE /api/admin/grammar/<id>/delete`

## 4. Lesson Organization and Management

### 4.1. Managing Lesson Categories

-   **View Categories**: Lists all lesson categories, showing name, description, and color code.
-   **Add New Category**:
    -   Fields: Name, Description, Color Code (e.g., using a color picker).
    -   Validation: Ensures category name is unique.
-   **Edit Category**: Modify details of an existing category.
-   **Delete Category**: Remove a category.
    -   *Consideration*: What happens to lessons in this category? They might become uncategorized or deletion might be prevented if lessons exist.

**Associated API Endpoints (example - may vary based on implementation):**
- `GET /api/admin/categories`
- `POST /api/admin/categories/new`
- `PUT /api/admin/categories/<id>/edit`
- `DELETE /api/admin/categories/<id>/delete`

### 4.2. Managing Lessons

This is a central part of the admin panel.

-   **View Lessons**: Lists all lessons, possibly filterable by category. Shows title, category, type (free/premium), published status.
-   **Create New Lesson**:
    -   Initial fields: Title, Description, Lesson Type (Free/Premium), Category, Difficulty Level, Estimated Duration, Order Index, Thumbnail URL, Video Intro URL.
    -   After creation, the admin can add content to pages within the lesson.
-   **Edit Lesson Settings**: Modify the metadata of an existing lesson (fields listed above).
-   **Publish/Unpublish Lesson**: Toggle the `is_published` status.
-   **Delete Lesson**: Remove an entire lesson, including its pages and content. This is a destructive action.
-   **Manage Lesson Prerequisites**: Interface to select other lessons that must be completed before starting the current lesson.

#### 4.2.1. Managing Lesson Pages and Content

Once a lesson is created or selected for editing, administrators manage its structure:

-   **Add Pages**: Create new pages within a lesson.
    -   Fields: Page Number (often auto-incremented or orderable), Page Title (optional), Page Description (optional).
-   **Order Pages**: Drag-and-drop interface to reorder pages.
-   **Edit Page Metadata**: Update title and description for a specific page.
-   **Delete Pages**: Remove a page and its associated content from the lesson.

-   **Adding Content to a Page**:
    -   Select content type to add:
        -   **Reference Existing Content**: Kana, Kanji, Vocabulary, Grammar (search/select from existing items).
        -   **New Multimedia Content**:
            -   **Text**: Add formatted text (potentially using a Rich Text Editor).
            -   **Image**: Upload an image or provide a URL. Include alt text and optional title.
            -   **Video**: Provide a video URL (e.g., YouTube, Vimeo - system may convert to embeddable format) or upload a video file.
            -   **Audio**: Upload an audio file or provide a URL.
        -   **Interactive Content (Quiz)**:
            -   Define the quiz container (e.g., max attempts, passing score).
            -   Add questions to the quiz (see section 4.2.2).
    -   **AI Content Generation**: For text content or quiz questions, an option to "✨ Generate with AI" is available.
        -   Prompts for topic, difficulty, keywords.
        -   Generated content can be reviewed and edited before being added.
        -   See `18-AI-Lesson-Creation.md` for details.
-   **Ordering Content on a Page**: Drag-and-drop interface to arrange content items within a page.
-   **Edit Content Item**: Modify an existing content item on a page.
-   **Remove Content Item from Page**: Delete a content item from a page.

#### 4.2.2. Managing Interactive Quiz Content (within a Lesson Content item)

When a `LessonContent` item is designated as `is_interactive` (a quiz):

-   **Add Quiz Questions**:
    -   Fields: Question Type (Multiple Choice, Fill-in-the-Blank, True/False), Question Text, Explanation (for after answer), Points.
-   **For Multiple Choice Questions**:
    -   Add Options: Text for each option, mark correct answer(s), provide specific feedback per option.
-   **Order Quiz Questions**: Arrange questions within the quiz.
-   **Edit Quiz Question/Options**: Modify existing questions or their options.
-   **Delete Quiz Question**: Remove a question from the quiz.

**Associated API Endpoints (examples for lessons and content - likely more granular):**
- `GET /api/admin/lessons`
- `POST /api/admin/lessons/new`
- `GET /api/admin/lessons/<id>`
- `PUT /api/admin/lessons/<id>/edit`
- `DELETE /api/admin/lessons/<id>/delete`
- `POST /api/admin/lessons/<id>/publish`
- `POST /api/admin/lessons/<id>/unpublish`
- `GET /api/admin/lessons/<id>/pages`
- `POST /api/admin/lessons/<lesson_id>/pages/new`
- `PUT /api/admin/lessons/<lesson_id>/pages/<page_id>/edit`
- `POST /api/admin/lessons/<lesson_id>/pages/<page_id>/content/add` (complex, depends on content type)
- `PUT /api/admin/lesson_content/<content_id>/edit`
- `DELETE /api/admin/lesson_content/<content_id>/delete`
- `POST /api/admin/lesson_content/<content_id>/questions/new` (for quiz questions)
- ... and many more for specific content interactions.

## 5. File Upload Management

-   Integrated into the lesson content creation process for images, audio, and video files.
-   Utilizes `FileUploadHandler` (from `app/utils.py`) for:
    -   Validation (allowed extensions, MIME types via `python-magic`).
    -   Secure filename generation.
    -   Image processing (resizing, optimization via Pillow).
    -   Storage in the configured `UPLOAD_FOLDER` (e.g., `app/static/uploads/lessons/<file_type>/`).
-   An API endpoint like `POST /api/admin/upload-file` likely handles asynchronous file uploads, returning a path to be associated with the lesson content item.

## 6. User Management (Potential Future Area)

While not explicitly detailed as fully implemented in existing admin routes, typical admin user management features would include:
-   **View Users**: List all registered users.
-   **Edit User Details**: Modify user's username, email (with caution), subscription level, admin status.
-   **Delete User**: Remove a user account.
-   **Impersonate User**: (Advanced, for troubleshooting) Log in as a specific user.

## 7. Admin Dashboard

The main landing page for the admin panel (`/admin`) typically provides:
-   Summary statistics (e.g., number of users, lessons, content items).
-   Quick links to common management sections.
-   Recent activity or notifications.

## 8. UI/UX Considerations

-   **Clear Navigation**: Easy-to-understand menu structure.
-   **Intuitive Forms**: Well-labeled fields and clear instructions for adding/editing content.
-   **Feedback Mechanisms**: Success and error messages for operations.
-   **Responsive Design**: Usable on various screen sizes, though primarily desktop-focused for admin tasks.
-   **Confirmation Dialogs**: For destructive actions like deletion.

This document provides a general overview. Specific implementation details for forms, tables, and workflows would be visible in the admin panel's HTML templates (e.g., `app/templates/admin/manage_lessons.html`) and corresponding JavaScript files.
