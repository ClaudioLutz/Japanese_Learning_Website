# API Design

## 1. Overview

This document will detail the design principles, conventions, and a comprehensive list of API endpoints for the Japanese Learning Website. The API facilitates interaction between the frontend, administrative tools, and potentially third-party services.

## 2. Design Principles

- **RESTful Architecture**: Adhere to REST principles where appropriate.
- **JSON for Data Interchange**: Use JSON for request and response payloads.
- **Statelessness**: Each API request should contain all information needed to process it.
- **Clear Versioning**: (e.g., `/api/v1/...`) - *To be defined if/when versioning is implemented.*
- **Consistent Naming Conventions**: Use snake_case for keys in JSON payloads and URL parameters.
- **Standard HTTP Status Codes**: Use appropriate HTTP status codes to indicate request outcomes (200 OK, 201 Created, 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 500 Internal Server Error).
- **Authentication & Authorization**: Secure endpoints using Flask-Login sessions and role-based access control (e.g., `@login_required`, `@admin_required`).

## 3. Authentication

- API endpoints requiring authentication expect session cookies managed by Flask-Login.
- Some administrative API endpoints also require CSRF tokens if accessed via AJAX from web forms.

## 4. API Endpoint Categories

*(This section will be populated with details for each endpoint category. Some examples are listed in `07-User-Authentication.md` and `08-Admin-Content-Management.md`)*

### 4.1. User Authentication & Management
- `/login`, `/register`, `/logout` (primarily form-based, but can be considered API interactions)
- `/api/user/profile` (GET, PUT - Example for future user profile management)
- `/api/user/subscription` (GET, POST - Example for managing subscription status)

### 4.2. Admin - Core Content Management (Kana, Kanji, Vocabulary, Grammar)
- Example for Kana:
    - `GET /api/admin/kana`
    - `POST /api/admin/kana/new`
    - `GET /api/admin/kana/<id>`
    - `PUT /api/admin/kana/<id>/edit`
    - `DELETE /api/admin/kana/<id>/delete`
- Similar CRUD endpoints for Kanji, Vocabulary, Grammar.

### 4.3. Admin - Lesson & Category Management
- CRUD for `LessonCategory`.
- CRUD for `Lesson` metadata.
- Endpoints for managing `LessonPage` (add, edit, delete, reorder within a lesson).
- Endpoints for managing `LessonContent` (add, edit, delete, reorder within a page).
    - Specific endpoints for different content types (text, media, links to core content, quizzes).
- Endpoints for managing `LessonPrerequisite`.
- Endpoint for publishing/unpublishing lessons.

### 4.4. Admin - File Uploads
- `POST /api/admin/upload-file`: Handles file uploads for lesson content, returns file path and metadata.

### 4.5. Admin - AI Content Generation
- `POST /api/admin/generate-ai-content`: Generates lesson content (text, quizzes) using AI. (See `18-AI-Lesson-Creation.md`).

### 4.6. User - Lesson Consumption & Progress
- `GET /api/lessons` (Example: list lessons with filtering)
- `GET /api/lessons/<lesson_id>` (Example: get full lesson structure for rendering)
- `POST /api/lessons/<lesson_id>/progress`: Update progress for a content item.
- `POST /api/lessons/<lesson_id>/quiz/<question_id>/answer`: Submit quiz answers.
- `GET /api/user/progress` (Example: get all user progress)

## 5. Common Request/Response Structures

*(Details on standard success and error response formats will be added here.)*

### Example Error Response:
```json
{
  "error": "A brief error message",
  "message": "More detailed explanation of the error.",
  "status_code": 400
}
```

## 6. Rate Limiting

*(Details on rate limiting strategies, if implemented, will be added here.)*

## 7. Future Considerations

- API Versioning
- OAuth2 for third-party access
- Webhooks

*(This document is a placeholder and will be expanded with detailed endpoint specifications.)*
