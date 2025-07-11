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

### 3.2. User-Facing Lesson Routes

These routes are for users to view and interact with lesson content.

| Method | Endpoint             | Authentication | Description                                                                 |
| :----- | :------------------- | :------------- | :-------------------------------------------------------------------------- |
| `GET`  | `/lessons`           | User           | Renders the main page for browsing all available lessons.                   |
| `GET`  | `/lessons/<int:id>`  | User           | Renders the detailed view for a single lesson, including all its content.   |
| `POST` | `/lessons/<int:id>/reset`| User         | Resets the current user's progress for the specified lesson.                |

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

#### 3.4.2. Lesson and Category APIs

| Method | Endpoint                               | Description                                      |
| :----- | :------------------------------------- | :----------------------------------------------- |
| `GET`  | `/api/admin/categories`                | Lists all lesson categories.                     |
| `POST` | `/api/admin/categories/new`            | Creates a new lesson category.                   |
| `...`  | `...`                                  | (Standard GET, PUT, DELETE for categories)       |
| `GET`  | `/api/admin/lessons`                   | Lists all lessons.                               |
| `POST` | `/api/admin/lessons/new`               | Creates a new lesson.                            |
| `GET`  | `/api/admin/lessons/<int:id>`          | Retrieves a single lesson with all its content.  |
| `PUT/PATCH`| `/api/admin/lessons/<int:id>/edit` | Updates a lesson's metadata.                     |
| `DELETE`| `/api/admin/lessons/<int:id>/delete` | Deletes a lesson and all its content.            |
| `POST` | `/api/admin/lessons/reorder`           | Reorders a list of lessons based on an array of IDs. |

#### 3.4.3. Lesson Structure APIs

| Method | Endpoint                                               | Description                                                              |
| :----- | :----------------------------------------------------- | :----------------------------------------------------------------------- |
| `POST` | `/api/admin/lessons/<int:id>/content/new`              | Adds a new content item to a lesson.                                     |
| `DELETE`| `/api/admin/lessons/<int:id>/content/<int:cid>/delete` | Removes a content item from a lesson.                                    |
| `PUT`  | `/api/admin/lessons/<int:id>/content/<int:cid>/edit`   | Updates an existing content item.                                        |
| `POST` | `/api/admin/lessons/<int:id>/content/<int:cid>/move`   | Moves a content item up or down within its page.                         |
| `DELETE`| `/api/admin/lessons/<int:id>/pages/<int:pnum>/delete`  | Deletes an entire page and all its content from a lesson.                |
| `PUT`  | `/api/admin/lessons/<int:id>/pages/<int:pnum>`         | Updates a page's metadata (title, description).                          |

#### 3.4.4. AI and File Management APIs

| Method | Endpoint                             | Description                                                              |
| :----- | :----------------------------------- | :----------------------------------------------------------------------- |
| `POST` | `/api/admin/generate-ai-content`     | The main endpoint for generating text and quiz content via AI.           |
| `POST` | `/api/admin/generate-ai-image`       | Generates an image using DALL-E from a prompt.                           |
| `POST` | `/api/admin/upload-file`             | Handles file uploads, returning a secure path and file metadata.         |
| `DELETE`| `/api/admin/delete-file`             | Deletes a file from the filesystem.                                      |

#### 3.4.5. Export/Import APIs

| Method | Endpoint                                   | Description                                                              |
| :----- | :----------------------------------------- | :----------------------------------------------------------------------- |
| `GET`  | `/api/admin/lessons/<int:id>/export`       | Exports a lesson's data as a JSON file.                                  |
| `POST` | `/api/admin/lessons/<int:id>/export-package`| Exports a lesson and its media files as a single ZIP package.            |
| `POST` | `/api/admin/lessons/import`                | Imports a lesson from an uploaded JSON file.                             |
| `POST` | `/api/admin/lessons/import-package`        | Imports a lesson from an uploaded ZIP package.                           |
| `POST` | `/api/admin/lessons/import-info`           | Analyzes an import file without importing to provide a preview.          |

#### 3.4.6. AI Content Generation Services
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
| `GET`  | `/api/lessons`                                     | User           | Gets all lessons accessible to the current user, including their progress. |
| `POST` | `/api/lessons/<int:id>/progress`                   | User           | Updates the user's progress for a specific content item in a lesson.     |
| `POST` | `/api/lessons/<int:lid>/quiz/<int:qid>/answer`     | User           | Submits a user's answer to a quiz question and returns the result.       |

## 4. Common Response Formats

-   **Success (GET, PUT, POST)**: Returns a `200 OK` or `201 Created` status with a JSON object or array representing the requested/modified resource(s).
-   **Success (DELETE)**: Returns a `200 OK` with a confirmation message, e.g., `{"message": "Item deleted successfully"}`.
-   **Client Error**: Returns a `4xx` status code (e.g., `400 Bad Request`, `404 Not Found`, `403 Forbidden`) with a JSON object describing the error, e.g., `{"error": "Missing required fields"}`.
-   **Server Error**: Returns a `500 Internal Server Error` with a generic error message, e.g., `{"error": "Database error occurred"}`. Specific details are logged on the server but not exposed to the client.
