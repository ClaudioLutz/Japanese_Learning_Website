# System Architecture

## High-Level Architecture Overview
The Japanese Learning Website follows a **layered monolithic architecture** with clear separation of concerns, designed for maintainability and future scalability. The system is built primarily using the **Model-View-Controller (MVC)** pattern, adapted for a Flask environment.

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                       │
│  (User Interface - Web Browser)                             │
├─────────────────────────────────────────────────────────────┤
│  HTML (Rendered by Jinja2) │ CSS (Bootstrap) │ JS (Vanilla) │
└─────────────────────────────────────────────────────────────┘
                              ▲ │
                              │ ▼ (HTTP Requests/Responses)
┌─────────────────────────────────────────────────────────────┐
│                     Application Server Layer (Flask)        │
├─────────────────────────────────────────────────────────────┤
│ ┌───────────────┐   ┌────────────────┐   ┌────────────────┐ │
│ │ Routes        │◀─▶│ Forms          │  │ Utilities      │ │
│ │ (app/routes.py) │   │ (app/forms.py) │ │(app/utils.py)  │ │
│ │  - Controller   │   │  - Validation  │ │  - FileUpload  │ │
│ │  - API Endpoints│   └────────────────┘ │  - Helpers     │ │
│ └───────┬───────┘                        └────────────────┘ │
│         │                                ┌────────────────┐ │
│         │                                │ AI Services    │ │
│         │                                │(app/ai_services.py)│
│         │                                └────────────────┘ │
│         ▼ (Interacts with Models, Renders Templates)        │
│ ┌───────────────┐     ┌────────────────┐ ┌────────────────┐ │
│ │ Models        │◀─▶ │ Database       │ │ Lesson Exp/Imp │ │
│ │ (app/models.py) │   │ (SQLAlchemy ORM) │ │(app/lesson_export_import.py)│
│ │  - Data Logic   │   │  - SQLite      │ └────────────────┘ │
│ │  - Business Rules│  └────────────────┘                    │
│ └───────────────┘                                           │
│         │                                                   │
│         ▼ (Renders)                                         │
│ ┌───────────────┐                                           │
│ │ Templates     │                                           │
│ │ (app/templates)│                                          │
│ │  - Jinja2       │                                         │
│ └───────────────┘                                           │
└─────────────────────────────────────────────────────────────┘
                              ▲ │
                              │ ▼ (File I/O for Uploads)
┌─────────────────────────────────────────────────────────────┐
│                     Data Storage Layer                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐   ┌─────────────┐   ┌───────────────────┐  │
│  │   SQLite    │   │ Migrations  │   │ File System       │  │
│  │ (site.db)   │   │ (Alembic)   │   │ (UPLOAD_FOLDER)   │  │
│  └─────────────┘   └─────────────┘   └───────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Core Design Principles

### 1. Separation of Concerns
- **Models (`app/models.py`)**: Define the data structure, relationships, and business logic directly related to data entities (e.g., User, Lesson, Kana). They interact with the ORM (SQLAlchemy).
- **Views (Templates - `app/templates/`)**: Handle the presentation logic. Jinja2 templates are used to render HTML dynamically based on data passed from controllers.
- **Controllers (Routes - `app/routes.py`)**: Manage the application flow. They handle incoming HTTP requests, interact with models to fetch or modify data, process input (often with the help of forms), and select appropriate templates to render or return JSON responses for API calls.
- **Forms (`app/forms.py`)**: Manage form data submission, validation (using WTForms and Flask-WTF), and CSRF protection.
- **Utilities (`app/utils.py`)**: Contain helper functions and classes that provide reusable logic across different parts of the application, such as `FileUploadHandler` for managing file uploads and `convert_to_embed_url` for YouTube URLs.
- **AI Services (`app/ai_services.py`)**: Encapsulate logic for interacting with external AI APIs (e.g., OpenAI) for features like content generation.
- **User Performance Analyzer (`app/user_performance_analyzer.py`)**: Analyzes user performance data to identify weaknesses and suggest remediation.
- **Content Validator (`app/content_validator.py`)**: Validates content accuracy, cultural context, and educational effectiveness.
- **Personalized Lesson Generator (`app/personalized_lesson_generator.py`)**: Generates adaptive lessons based on user performance analysis.
- **Lesson Export/Import (`app/lesson_export_import.py`)**: Handles the serialization and deserialization of lesson data for backup, transfer, or bulk creation purposes.

### 2. Single Responsibility Principle
- Each Python module (e.g., `models.py`, `routes.py`, `forms.py`, `utils.py`, `ai_services.py`, `lesson_export_import.py`) has a distinct area of responsibility.
- Database models are focused on data representation and data-related operations.
- Route handlers in `app/routes.py` are responsible for the request-response cycle of specific URLs.
- `FileUploadHandler` in `app/utils.py` centralizes all file upload processing and validation logic.

### 3. Dependency Management & Application Factory
- The application uses an **application factory pattern** (`create_app` function in `app/__init__.py`). This approach allows for:
    - Easier configuration management (e.g., different configs for development, testing, production).
    - Delayed initialization of Flask extensions until the app object is created.
    - Improved testability by creating multiple app instances.
- Python package dependencies are managed in `requirements.txt` and isolated using virtual environments.

### 4. Security by Design
- **Authentication**: Managed by Flask-Login, ensuring users are authenticated for protected routes.
- **Authorization**: Implemented via custom decorators (`@admin_required`, `@premium_required`) in `app/routes.py` and checks on `current_user` attributes (e.g., `is_admin`, `subscription_level`) to enforce role-based access control (RBAC).
- **Input Validation**:
    - For web forms: Handled by WTForms validators defined in `app/forms.py`.
    - For API endpoints: Explicit checks on JSON payload data within the route handlers in `app/routes.py`.
- **CSRF Protection**: Provided by Flask-WTF for all form submissions. A dedicated `CSRFTokenForm` is used for actions (like lesson reset or subscription changes) that are triggered by POST requests but don't have other form fields.
- **File Upload Security**: The `FileUploadHandler` in `app/utils.py` implements several security measures:
    - Strict validation of allowed file extensions (`ALLOWED_EXTENSIONS` configuration).
    - MIME type validation of file content using `python-magic` to prevent type confusion.
    - Generation of secure, unique filenames to prevent directory traversal or overwriting issues.
    - Image processing (resizing, conversion) to mitigate risks from malformed image files.
    - Uploaded files are stored in a designated `UPLOAD_FOLDER`, and served via a controlled route (`/uploads/<path:filename>`) that includes path validation.
- **Password Security**: Passwords are hashed using `generate_password_hash` (PBKDF2) from Werkzeug.
- **XSS Prevention**: Jinja2 templating engine auto-escapes variables by default, mitigating Cross-Site Scripting risks.

## Data Flow Architecture

### User Request Flow (Typical Web Page Interaction)
```
1. User Action (e.g., navigates to URL, submits a form via browser).
   │
   ▼
2. HTTP Request (GET for page load, POST for form submission) sent to Flask Web Server.
   │
   ▼
3. Flask Routing (`app/routes.py`) matches the requested URL to a specific route handler function.
   │
   ▼
4. Decorators on the route handler execute sequentially (e.g., `@login_required`, `@admin_required`).
   │  └─ If authentication/authorization fails, the user is redirected (e.g., to login page) or an error is flashed.
   ▼
5. Route Handler Function in `app/routes.py` executes:
   │  a. For POST requests with forms:
   │     │  i. Instantiate the corresponding WTForm from `app/forms.py`.
   │     │  ii. Validate the form data (including CSRF token).
   │     │  └─ If validation fails, re-render the template, passing the form with error messages.
   │  b. Interact with Database Models (`app/models.py`) via SQLAlchemy sessions:
   │     │  - Query data needed for the page.
   │     │  - Create, update, or delete records based on user input.
   │  c. Perform other business logic, potentially using helper functions from `app/utils.py`.
   │  d. Prepare a context dictionary containing data to be displayed on the page.
   ▼
6. Render Jinja2 Template from `app/templates/` using the prepared context data.
   │
   ▼
7. Flask sends the generated HTML as an HTTP Response back to the user's browser.
```

### Admin API Request Flow (e.g., Content Management via AJAX)
```
1. Admin Action in the frontend UI (e.g., clicking "Save" for a new Kana character) triggers a client-side JavaScript function.
   │
   ▼
2. Client-side JavaScript constructs an HTTP Request (e.g., POST, PUT, DELETE) with a JSON payload and sends it to a specific API endpoint (e.g., `/api/admin/kana/new`).
   │
   ▼
3. Flask Routing (`app/routes.py`) matches the API endpoint URL to its handler function.
   │
   ▼
4. Decorators (`@login_required`, `@admin_required`) execute.
   │  └─ If authentication/authorization fails, a JSON error response (e.g., HTTP 401 or 403) is returned.
   ▼
5. API Route Handler Function in `app/routes.py` executes:
   │  a. Parse and validate the incoming JSON payload (e.g., check for required fields, data types).
   │     │  └─ If validation fails, return a JSON error response (e.g., HTTP 400).
   │  b. Interact with Database Models (`app/models.py`) to perform CRUD operations.
   │  c. If the operation involves files (e.g., creating lesson content with an image):
   │     │  - File upload might have occurred via a separate `/api/admin/upload-file` request.
   │     │  - The current request associates the `file_path` (from the upload response) with the new database record.
   │  d. Prepare a response dictionary (e.g., newly created object data, success message).
   ▼
6. Serialize the response dictionary to JSON using `jsonify()`.
   │
   ▼
7. Flask sends the HTTP Response (JSON) back to the client-side JavaScript.
   │
   ▼
8. Client-side JavaScript processes the JSON response and updates the UI accordingly (e.g., adds new item to a table, shows a success/error message).
```

### File Upload Process Flow
```
1. Admin selects a file in the lesson content builder UI.
   │
   ▼
2. Client-side JavaScript sends a POST request to `/api/admin/upload-file` with the file data (multipart/form-data).
   │
   ▼
3. `upload_file` route handler in `app/routes.py` receives the request.
   │  a. `FileUploadHandler.get_file_type()` determines type from extension.
   │  b. `FileUploadHandler.allowed_file()` validates extension against `ALLOWED_EXTENSIONS`.
   │  c. `FileUploadHandler.generate_unique_filename()` creates a secure, unique filename.
   │  d. File is saved to a temporary location.
   │  e. `FileUploadHandler.validate_file_content()` checks MIME type using `python-magic`.
   │  f. If image, `FileUploadHandler.process_image()` resizes and optimizes it.
   │  g. Validated/processed file is moved to its final destination within `UPLOAD_FOLDER` (e.g., `app/static/uploads/lessons/<file_type>/<unique_filename>`).
   │  h. `FileUploadHandler.get_file_info()` gathers metadata.
   ▼
4. `/api/admin/upload-file` returns a JSON response with:
   │  - `filePath`: URL for `url_for` (e.g., `/static/uploads/lessons/...`).
   │  - `dbPath`: Relative path to store in `LessonContent.file_path` (e.g., `lessons/...`).
   │  - Other file metadata.
   ▼
5. Client-side JavaScript receives the response. The `dbPath` is stored and used when creating/updating the `LessonContent` item.
   │
   ▼
6. When creating/updating `LessonContent` (e.g., via `/api/admin/lessons/<id>/content/file` or `/api/admin/content/<id>/edit`):
   │  - The `dbPath` is sent in the JSON payload and stored in `LessonContent.file_path`.
   ▼
7. When serving the file (e.g., in a lesson):
   │  - `LessonContent.get_file_url()` uses `url_for('routes.uploaded_file', filename=self.file_path)`.
   │  - This resolves to the `/uploads/<path:filename>` route.
   │  - The `uploaded_file` route handler in `app/routes.py` serves the file from `UPLOAD_FOLDER` using `send_from_directory`, after path validation.
```

### Lesson Progress Tracking Flow (User Interacting with Lesson Content)
```
1. User views a lesson page (`/lessons/<lesson_id>`).
   │  - `view_lesson` route handler checks accessibility (`lesson.is_accessible_to_user()`).
   │  - Gets or creates `UserLessonProgress` for the user and lesson.
   │  - Renders `lesson_view.html` with lesson data and progress.
   ▼
2. User interacts with a content item (e.g., clicks "Mark as Complete" or submits a quiz answer).
   │
   ▼
3. Client-side JavaScript sends an AJAX POST request:
   │  a. For general content completion: to `/api/lessons/<lesson_id>/progress`
   │     - Payload: `{ "content_id": <id_of_completed_item> }`
   │  b. For quiz answer submission: to `/api/lessons/<lesson_id>/quiz/<question_id>/answer`
   │     - Payload: `{ "selected_option_id": <id> }` or `{ "text_answer": "..." }`
   ▼
4. Respective API route handler in `app/routes.py` (`update_lesson_progress` or `submit_quiz_answer`) executes:
   │  a. Authenticates user (`@login_required`).
   │  b. Validates lesson accessibility.
   │  c. Retrieves the `UserLessonProgress` record or `UserQuizAnswer` record (or creates if new attempt for quiz).
   │  d. Updates the record:
   │     - `UserLessonProgress.mark_content_completed(content_id)` updates JSON progress and recalculates overall percentage.
   │     - For quizzes, checks answer correctness, updates attempts, stores answer.
   │  e. Commits changes to the database.
   │  f. Returns a JSON response (e.g., updated progress object, quiz feedback).
   ▼
5. Client-side JavaScript receives the JSON response and updates the UI (e.g., shows a checkmark, displays quiz result, updates progress bar).
```

## Scalability Considerations
- **Modular Design**: Clear separation allows for future microservice extraction
- **Database Abstraction**: SQLAlchemy ORM enables easy database migration
- **Stateless Design**: Session-based authentication supports horizontal scaling
- **File Management**: Centralized upload handling supports CDN integration
- **API-First Approach**: RESTful APIs enable frontend flexibility and mobile app development
