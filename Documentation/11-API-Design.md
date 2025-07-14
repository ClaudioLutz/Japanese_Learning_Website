# 11. API Design and Endpoints

## 1. Overview

The application's backend is built around a set of routes and a comprehensive RESTful API, all defined within the `app/routes.py` file using a Flask Blueprint. This API powers the dynamic frontend, the admin content management system, and all user interactions.

The design emphasizes a clear separation between user-facing rendered pages and the JSON-based API used for data manipulation.

## 2. Authentication and Authorization

All protected routes and API endpoints use a decorator-based system for access control.

-   **`@login_required`**: Standard Flask-Login decorator. Ensures the user is authenticated. Unauthenticated users are typically redirected to the login page.
-   **`@admin_required`**: A custom decorator that checks if `current_user.is_admin` is `True`. Used to protect all administrative routes and APIs.
-   **`@premium_required`**: A custom decorator that checks if `current_user.subscription_level` is `'premium'`. Used to restrict access to premium content.

## 3. API Endpoint Reference

The API is divided into several logical groups based on functionality.

### 3.1. Public and Authentication Routes

These routes handle user registration, login, and basic page navigation. They primarily render HTML templates.

| Method | Endpoint             | Authentication | Description                                                                 |
| :----- | :------------------- | :------------- | :-------------------------------------------------------------------------- |
| `GET`  | `/` or `/home`       | None           | Renders the main homepage.                                                  |
| `GET/POST`| `/register`          | None           | Renders the registration page and handles new user form submission.         |
| `GET/POST`| `/login`             | None           | Renders the login page and handles user login form submission.              |
| `GET`  | `/logout`            | User           | Logs the current user out and redirects to the homepage.                    |
| `POST` | `/upgrade_to_premium`| User           | (Prototype) Upgrades the current user's subscription level to 'premium'.    |
| `POST` | `/downgrade_from_premium`| User         | (Prototype) Downgrades the current user's subscription level to 'free'.     |

### 3.2. User-Facing Lesson and Course Routes

These routes are for users to view and interact with lesson content and courses.

| Method | Endpoint             | Authentication | Description                                                                 |
| :----- | :------------------- | :------------- | :-------------------------------------------------------------------------- |
| `GET`  | `/lessons`           | None           | Renders the main page for browsing all available lessons.                   |
| `GET`  | `/lessons/<int:id>`  | None/User      | Renders the detailed view for a single lesson. Access depends on lesson settings and user authentication. |
| `POST` | `/lessons/<int:id>/reset`| User         | Resets the current user's progress for the specified lesson.                |
| `GET`  | `/courses`           | None           | Renders the main page for browsing all available courses.                   |
| `GET`  | `/course/<int:id>`   | None/User      | Renders the detailed view for a single course with progress tracking.       |

### 3.3. Admin Panel Routes

These routes serve the HTML pages for the admin content management system. The actual data is loaded into these pages via the REST API endpoints below.

| Method | Endpoint                   | Authentication | Description                                      |
| :----- | :------------------------- | :------------- | :----------------------------------------------- |
| `GET`  | `/admin`                   | Admin          | Renders the main admin dashboard.                |
| `GET`  | `/admin/manage/kana`       | Admin          | Renders the management page for Kana.            |
| `GET`  | `/admin/manage/kanji`      | Admin          | Renders the management page for Kanji.           |
| `GET`  | `/admin/manage/vocabulary` | Admin          | Renders the management page for Vocabulary.      |
| `GET`  | `/admin/manage/grammar`    | Admin          | Renders the management page for Grammar.         |
| `GET`  | `/admin/manage/lessons`    | Admin          | Renders the management page for Lessons.         |
| `GET`  | `/admin/manage/categories` | Admin          | Renders the management page for Categories.      |
| `GET`  | `/admin/manage/courses`    | Admin          | Renders the management page for Courses.         |
| `GET`  | `/admin/manage/approval`   | Admin          | Renders the page for approving AI content.       |

### 3.4. Admin REST API

This is the core JSON-based API for all CRUD (Create, Read, Update, Delete) operations.

#### 3.4.1. Core Content APIs (Kana, Kanji, etc.)
These follow a standard RESTful pattern for each content type.

| Method | Endpoint                               | Description                               |
| :----- | :------------------------------------- | :---------------------------------------- |
| `GET`  | `/api/admin/<type>`                    | Lists all items of the specified type.    |
| `POST` | `/api/admin/<type>/new`                | Creates a new item of the specified type. |
| `GET`  | `/api/admin/<type>/<int:id>`           | Retrieves a single item by its ID.        |
| `PUT/PATCH`| `/api/admin/<type>/<int:id>/edit`  | Updates an existing item by its ID.       |
| `DELETE`| `/api/admin/<type>/<int:id>/delete`| Deletes an item by its ID.                |
_(`type` can be `kana`, `kanji`, `vocabulary`, or `grammar`)_

#### 3.4.2. Lesson, Category, and Course APIs

**Categories:**
| Method | Endpoint                               | Description                                      |
| :----- | :------------------------------------- | :----------------------------------------------- |
| `GET`  | `/api/admin/categories`                | Lists all lesson categories.                     |
| `POST` | `/api/admin/categories/new`            | Creates a new lesson category.                   |
| `GET`  | `/api/admin/categories/<int:id>`       | Retrieves a single category by ID.              |
| `PUT/PATCH`| `/api/admin/categories/<int:id>/edit`| Updates an existing category.                   |
| `DELETE`| `/api/admin/categories/<int:id>/delete`| Deletes a category.                             |

**Lessons:**
| Method | Endpoint                               | Description                                      |
| :----- | :------------------------------------- | :----------------------------------------------- |
| `GET`  | `/api/admin/lessons`                   | Lists all lessons with metadata.                 |
| `POST` | `/api/admin/lessons/new`               | Creates a new lesson.                            |
| `GET`  | `/api/admin/lessons/<int:id>`          | Retrieves a single lesson with all its content.  |
| `PUT/PATCH`| `/api/admin/lessons/<int:id>/edit` | Updates a lesson's metadata.                     |
| `DELETE`| `/api/admin/lessons/<int:id>/delete` | Deletes a lesson and all its content.            |
| `POST` | `/api/admin/lessons/<int:id>/move`     | Moves a lesson up or down in global order.       |
| `POST` | `/api/admin/lessons/reorder`           | Reorders lessons based on provided order.        |

**Courses:**
| Method | Endpoint                               | Description                                      |
| :----- | :------------------------------------- | :----------------------------------------------- |
| `GET`  | `/api/admin/courses`                   | Lists all courses.                               |
| `POST` | `/api/admin/courses/new`               | Creates a new course.                            |
| `GET`  | `/api/admin/courses/<int:id>`          | Retrieves a single course with lessons.          |
| `PUT/PATCH`| `/api/admin/courses/<int:id>/edit`  | Updates a course's metadata.                     |
| `DELETE`| `/api/admin/courses/<int:id>/delete` | Deletes a course.                                |

#### 3.4.3. Lesson Content Management APIs

**Content Items:**
| Method | Endpoint                                               | Description                                                              |
| :----- | :----------------------------------------------------- | :----------------------------------------------------------------------- |
| `GET`  | `/api/admin/lessons/<int:id>/content`                  | Lists all content items for a lesson.                                   |
| `POST` | `/api/admin/lessons/<int:id>/content/new`              | Adds a new content item to a lesson.                                     |
| `POST` | `/api/admin/lessons/<int:id>/content/file`             | Adds file-based content to a lesson.                                     |
| `POST` | `/api/admin/lessons/<int:id>/content/interactive`      | Adds interactive content (quiz) to a lesson.                             |
| `GET`  | `/api/admin/content/<int:id>`                          | Gets full details for a single content item.                             |
| `GET`  | `/api/admin/content/<int:id>/preview`                  | Gets content preview data.                                               |
| `PUT`  | `/api/admin/content/<int:id>/edit`                     | Updates an existing content item.                                        |
| `POST` | `/api/admin/content/<int:id>/duplicate`                | Duplicates a single content item.                                        |
| `DELETE`| `/api/admin/lessons/<int:id>/content/<int:cid>/delete` | Removes a content item from a lesson.                                    |
| `POST` | `/api/admin/lessons/<int:id>/content/<int:cid>/move`   | Moves a content item up or down within its page.                         |

**Bulk Operations:**
| Method | Endpoint                                               | Description                                                              |
| :----- | :----------------------------------------------------- | :----------------------------------------------------------------------- |
| `PUT`  | `/api/admin/lessons/<int:id>/content/bulk-update`      | Bulk update content properties.                                          |
| `POST` | `/api/admin/lessons/<int:id>/content/bulk-duplicate`   | Bulk duplicate content items.                                            |
| `DELETE`| `/api/admin/lessons/<int:id>/content/bulk-delete`     | Bulk delete content items.                                               |
| `POST` | `/api/admin/lessons/<int:id>/content/force-reorder`    | Force reorder all content to fix gaps.                                   |

**Page Management:**
| Method | Endpoint                                               | Description                                                              |
| :----- | :----------------------------------------------------- | :----------------------------------------------------------------------- |
| `PUT`  | `/api/admin/lessons/<int:id>/pages/<int:pnum>`         | Updates a page's metadata (title, description).                          |
| `DELETE`| `/api/admin/lessons/<int:id>/pages/<int:pnum>/delete`  | Deletes an entire page and all its content from a lesson.                |
| `POST` | `/api/admin/lessons/<int:id>/pages/<int:pnum>/reorder` | Reorders content items on a specific page.                               |

**Content Options:**
| Method | Endpoint                                               | Description                                                              |
| :----- | :----------------------------------------------------- | :----------------------------------------------------------------------- |
| `GET`  | `/api/admin/content-options/<type>`                    | Gets available content items for selection (kana, kanji, vocabulary, grammar). |

#### 3.4.4. AI Content Generation APIs

| Method | Endpoint                             | Description                                                              |
| :----- | :----------------------------------- | :----------------------------------------------------------------------- |
| `POST` | `/api/admin/generate-ai-content`     | Generates text explanations and quiz content via AI.                     |
| `POST` | `/api/admin/generate-ai-image`       | Generates images using DALL-E from prompts or content.                   |
| `POST` | `/api/admin/analyze-multimedia-needs`| Analyzes lesson content and suggests multimedia enhancements.            |
| `POST` | `/api/admin/generate-lesson-images`  | Generates multiple images for lesson content.                            |

#### 3.4.5. File Management APIs

| Method | Endpoint                             | Description                                                              |
| :----- | :----------------------------------- | :----------------------------------------------------------------------- |
| `POST` | `/api/admin/upload-file`             | Handles file uploads with validation and processing.                     |
| `DELETE`| `/api/admin/delete-file`             | Deletes a file from the filesystem.                                      |
| `GET`  | `/uploads/<path:filename>`           | Serves uploaded files securely.                                          |

#### 3.4.6. Content Approval APIs

| Method | Endpoint                                               | Description                                                              |
| :----- | :----------------------------------------------------- | :----------------------------------------------------------------------- |
| `POST` | `/api/admin/content/<type>/<int:id>/approve`           | Approves AI-generated content (kanji, vocabulary, grammar).              |
| `POST` | `/api/admin/content/<type>/<int:id>/reject`            | Rejects and deletes AI-generated content.                                |

#### 3.4.7. Export/Import APIs

| Method | Endpoint                                   | Description                                                              |
| :----- | :----------------------------------------- | :----------------------------------------------------------------------- |
| `GET`  | `/api/admin/lessons/<int:id>/export`       | Exports a lesson's data as a JSON file.                                  |
| `POST` | `/api/admin/lessons/<int:id>/export-package`| Exports a lesson and its media files as a single ZIP package.            |
| `POST` | `/api/admin/lessons/export-multiple`       | Exports multiple lessons as a single ZIP package.                        |
| `POST` | `/api/admin/lessons/import`                | Imports a lesson from an uploaded JSON file.                             |
| `POST` | `/api/admin/lessons/import-package`        | Imports a lesson from an uploaded ZIP package.                           |
| `POST` | `/api/admin/lessons/import-info`           | Analyzes an import file without importing to provide a preview.          |

#### 3.4.8. AI Content Generation Services
While not traditional REST endpoints, the following functions in `AILessonContentGenerator` act as a service layer for AI content creation. They are called from scripts and other services.

| Service Function                       | Description                                                              |
| :------------------------------------- | :----------------------------------------------------------------------- |
| `generate_explanation`                 | Generates a simple, plain-text paragraph explanation.                    |
| `generate_formatted_explanation`       | Creates a detailed explanation using HTML tags.                          |
| `generate_kanji_data`                  | Generates a complete data structure for a single Kanji character.        |
| `generate_vocabulary_data`             | Creates a detailed entry for a vocabulary word.                          |
| `generate_grammar_data`                | Generates a comprehensive explanation for a grammar point.               |
| `generate_true_false_question`         | Creates a true/false question with a detailed explanation.               |
| `generate_fill_in_the_blank_question`  | Generates a sentence with a blank, the correct answer, and an explanation. |
| `generate_matching_question`           | Creates a set of pairs for a matching exercise.                          |
| `generate_multiple_choice_question`    | Generates a multiple-choice question with hints and difficulty levels.   |
| `create_adaptive_quiz`                 | Generates a complete quiz with questions of varying difficulty.          |
| `generate_image_prompt`                | Creates an optimized prompt for an AI image generation service.          |
| `generate_single_image`                | Generates a single image based on a given prompt.                        |
| `generate_lesson_images`               | Generates a set of images for a lesson.                                  |
| `analyze_content_for_multimedia_needs` | Analyzes text and suggests multimedia enhancements.                      |

### 3.5. User Data and Quiz APIs

| Method | Endpoint                                           | Authentication | Description                                                              |
| :----- | :------------------------------------------------- | :------------- | :----------------------------------------------------------------------- |
| `GET`  | `/api/lessons`                                     | None/User      | Gets all lessons accessible to the current user or guest, with optional filtering. |
| `GET`  | `/api/courses`                                     | None           | Gets all published courses.                                              |
| `GET`  | `/api/categories`                                  | None           | Gets all lesson categories for public use.                               |
| `POST` | `/api/lessons/<int:id>/progress`                   | User           | Updates the user's progress for a specific content item in a lesson.     |
| `POST` | `/api/lessons/<int:lid>/quiz/<int:qid>/answer`     | User           | Submits a user's answer to a quiz question and returns the result.       |

## 4. Common Response Formats

-   **Success (GET, PUT, POST)**: Returns a `200 OK` or `201 Created` status with a JSON object or array representing the requested/modified resource(s).
-   **Success (DELETE)**: Returns a `200 OK` with a confirmation message, e.g., `{"message": "Item deleted successfully"}`.
-   **Client Error**: Returns a `4xx` status code (e.g., `400 Bad Request`, `404 Not Found`, `403 Forbidden`) with a JSON object describing the error, e.g., `{"error": "Missing required fields"}`.
-   **Server Error**: Returns a `500 Internal Server Error` with a generic error message, e.g., `{"error": "Database error occurred"}`. Specific details are logged on the server but not exposed to the client.
