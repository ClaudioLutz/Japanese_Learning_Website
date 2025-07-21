# System Architecture

## High-Level Architecture Overview
The Japanese Learning Website follows a **layered monolithic architecture** with clear separation of concerns, designed for maintainability and future scalability. The system is built primarily using the **Model-View-Controller (MVC)** pattern, adapted for a Flask environment with modern features including AI integration, social authentication, and a comprehensive lesson management system.

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
│ │  - API Endpoints│   │  - CSRF Protect│ │  - Helpers     │ │
│ └───────┬───────┘   └────────────────┘ └────────────────┘ │
│         │                                ┌────────────────┐ │
│         │                                │ AI Services    │ │
│         │                                │(app/ai_services.py)│
│         │                                │ - Gemini API   │ │
│         │                                │ - OpenAI DALL-E│ │
│         │                                └────────────────┘ │
│         │                                ┌────────────────┐ │
│         │                                │ Social Auth    │ │
│         │                                │(social_auth_   │ │
│         │                                │ config.py)     │ │
│         │                                └────────────────┘ │
│         ▼ (Interacts with Models, Renders Templates)        │
│ ┌───────────────┐     ┌────────────────┐ ┌────────────────┐ │
│ │ Models        │◀─▶ │ Database       │ │ Lesson Exp/Imp │ │
│ │ (app/models.py) │   │ (SQLAlchemy ORM) │ │(app/lesson_export_import.py)│
│ │  - Data Logic   │   │  - PostgreSQL  │ └────────────────┘ │
│ │  - Business Rules│  │  - Migrations  │                    │
│ └───────────────┘   └────────────────┘                    │
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
│  │ PostgreSQL  │   │ Migrations  │   │ File System       │  │
│  │ (Primary DB)│   │ (Alembic)   │   │ (UPLOAD_FOLDER)   │  │
│  └─────────────┘   └─────────────┘   └───────────────────┘  │
│                                                             │
│  ┌─────────────┐   ┌─────────────┐                         │
│  │ External    │   │ Cloud       │                         │
│  │ AI APIs     │   │ Storage     │                         │
│  │ (Optional)  │   │ (Future)    │                         │
│  └─────────────┘   └─────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

## Core Design Principles

### 1. Separation of Concerns
- **Models (`app/models.py`)**: Define the data structure, relationships, and business logic directly related to data entities (e.g., User, Lesson, Kana, Course, LessonPurchase). They interact with the ORM (SQLAlchemy) and include complex business logic for lesson accessibility, progress tracking, and pricing.
- **Views (Templates - `app/templates/`)**: Handle the presentation logic. Jinja2 templates are used to render HTML dynamically based on data passed from controllers. Includes specialized templates for admin interfaces, lesson viewing, and course management.
- **Controllers (Routes - `app/routes.py`)**: Manage the application flow using Flask Blueprints. They handle incoming HTTP requests, interact with models to fetch or modify data, process input (often with the help of forms), and select appropriate templates to render or return JSON responses for comprehensive API endpoints.
- **Forms (`app/forms.py`)**: Manage form data submission, validation (using WTForms and Flask-WTF), and CSRF protection with dedicated forms for registration, login, and CSRF token handling.
- **Utilities (`app/utils.py`)**: Contain helper functions and classes that provide reusable logic across different parts of the application, such as `FileUploadHandler` for managing secure file uploads with MIME validation and `convert_to_embed_url` for YouTube URLs.
- **AI Services (`app/ai_services.py`)**: Comprehensive AI integration service that encapsulates logic for interacting with multiple AI APIs:
  - **Gemini API**: For text generation, explanations, and quiz content
  - **OpenAI DALL-E**: For image generation and visual content creation
  - **Batch Processing**: Advanced quiz generation with context awareness
- **Social Authentication (`app/social_auth_config.py`)**: Handles Google OAuth integration and social login workflows.
- **Lesson Export/Import (`app/lesson_export_import.py`)**: Handles the serialization and deserialization of lesson data for backup, transfer, or bulk creation purposes with ZIP package support.

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
- **Authentication**: Multi-layered authentication system:
  - **Flask-Login**: Traditional email/password authentication
  - **Google OAuth**: Social authentication via `python-social-auth`
  - **Session Management**: Secure session handling with proper logout flows
- **Authorization**: Comprehensive role-based access control (RBAC):
  - Custom decorators (`@admin_required`, `@premium_required`) in `app/routes.py`
  - User attribute checks (`is_admin`, `subscription_level`)
  - Lesson-specific access control with pricing and prerequisite validation
  - Purchase-based access control for paid lessons
- **Input Validation**:
  - **Web Forms**: WTForms validators in `app/forms.py` with email validation
  - **API Endpoints**: Comprehensive JSON payload validation in route handlers
  - **File Uploads**: Multi-layer validation including extension, MIME type, and content validation
- **CSRF Protection**: 
  - Flask-WTF CSRF protection for all form submissions
  - Dedicated `CSRFTokenForm` for AJAX operations
  - CSRF token validation in API endpoints
- **File Upload Security**: Enhanced `FileUploadHandler` in `app/utils.py`:
  - Strict validation of allowed file extensions by type (image, video, audio)
  - MIME type validation using `python-magic` library
  - Secure filename generation with UUID components
  - Image processing and optimization using Pillow
  - Path traversal prevention with absolute path validation
  - Organized storage in type-specific subdirectories
  - Controlled file serving via `/uploads/<path:filename>` route
- **Database Security**:
  - PostgreSQL with proper connection string handling
  - SQLAlchemy ORM preventing SQL injection
  - Environment variable configuration for sensitive data
- **Password Security**: Werkzeug password hashing with PBKDF2
- **XSS Prevention**: Jinja2 auto-escaping with additional input sanitization

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

## Technology Stack

### Backend Framework
- **Flask 2.0+**: Modern Python web framework with Blueprint architecture
- **SQLAlchemy 2.5+**: Advanced ORM with type hints and modern Python features
- **Flask-Login 0.6+**: User session management and authentication
- **Flask-WTF 1.0+**: Form handling and CSRF protection
- **Flask-Migrate 3.1+**: Database migration management via Alembic

### Database
- **PostgreSQL**: Primary production database with advanced features
- **psycopg[binary] 3.0+**: Modern PostgreSQL adapter for Python
- **Alembic**: Database migration and version control

### AI Integration
- **Google Gemini API**: Advanced text generation, explanations, and quiz content
- **OpenAI API 1.0+**: DALL-E image generation and visual content creation
- **Custom AI Service Layer**: Unified interface for multiple AI providers

### Authentication & Security
- **python-social-auth**: Google OAuth and social login integration
- **Authlib 1.2+**: OAuth client implementation
- **PyJWT 2.4+**: JSON Web Token handling
- **Werkzeug 2.0+**: Password hashing and security utilities

### File Processing
- **Pillow 9.0+**: Image processing and optimization
- **python-magic**: MIME type detection and validation
- **Secure file upload system**: Custom implementation with validation

### Development & Deployment
- **python-dotenv**: Environment variable management
- **Gunicorn**: WSGI HTTP Server for production
- **pandas 1.3+**: Data processing and analytics support

## Enhanced Data Models

### Core Entities
- **User**: Enhanced with subscription levels, admin flags, and social auth integration
- **Lesson**: Complex model with pricing, prerequisites, guest access, and multi-language support
- **Course**: Lesson organization and progression tracking
- **LessonContent**: Flexible content system supporting text, media, and interactive elements
- **LessonPurchase**: E-commerce functionality for paid lessons

### Content Management
- **Kana, Kanji, Vocabulary, Grammar**: Structured Japanese language content
- **LessonCategory**: Content organization and visual theming
- **LessonPage**: Multi-page lesson structure with metadata
- **QuizQuestion/QuizOption**: Comprehensive quiz system with multiple question types

### Progress Tracking
- **UserLessonProgress**: Detailed progress tracking with JSON content progress
- **UserQuizAnswer**: Quiz attempt tracking with feedback and scoring

## AI-Powered Features

### Content Generation
- **Automated Explanations**: Context-aware educational content
- **Quiz Generation**: Multiple question types with batch processing
- **Image Creation**: Custom educational illustrations via DALL-E
- **Multimedia Analysis**: Content enhancement suggestions

### Advanced Capabilities
- **Batch Quiz Processing**: Context-aware question generation in single API calls
- **Romanization Integration**: Automatic pronunciation guides
- **Difficulty Adaptation**: Content tailored to learner levels
- **Cultural Context**: Culturally appropriate content generation

## Scalability Considerations
- **Modular Design**: Clear separation allows for future microservice extraction
- **Database Abstraction**: SQLAlchemy ORM enables easy database migration and scaling
- **Stateless Design**: Session-based authentication supports horizontal scaling
- **File Management**: Centralized upload handling supports CDN integration
- **API-First Approach**: Comprehensive RESTful APIs enable frontend flexibility and mobile app development
- **AI Service Abstraction**: Unified AI interface allows for easy provider switching and load balancing
- **Blueprint Architecture**: Flask Blueprints enable modular application structure
- **Environment-Based Configuration**: Supports multiple deployment environments
