# Japanese Learning Website - Complete Project Documentation

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Project Overview](#project-overview)
3. [System Architecture](#system-architecture)
4. [Technology Stack & Design Decisions](#technology-stack--design-decisions)
5. [Installation & Setup](#installation--setup)
6. [User Authentication System](#user-authentication-system)
7. [Admin Content Management](#admin-content-management)
8. [Lesson System Architecture](#lesson-system-architecture)
9. [Database Schema](#database-schema)
10. [API Design & Endpoints](#api-design--endpoints)
11. [Frontend Architecture](#frontend-architecture)
12. [File Structure & Organization](#file-structure--organization)
13. [Configuration Management](#configuration-management)
14. [Security Implementation](#security-implementation)
15. [Development Workflow & Best Practices](#development-workflow--best-practices)
16. [Performance Considerations](#performance-considerations)
17. [Deployment Strategy](#deployment-strategy)
18. [Monitoring & Analytics](#monitoring--analytics)
19. [Troubleshooting Guide](#troubleshooting-guide)
20. [Future Roadmap](#future-roadmap)
21. [Technical Debt & Refactoring Opportunities](#technical-debt--refactoring-opportunities)

---

## Executive Summary

### Project Vision
The Japanese Learning Website represents a sophisticated, full-stack educational platform designed to democratize Japanese language learning through technology. Built with modern web technologies and pedagogical best practices, it serves as both a learning management system and a comprehensive content delivery platform.

### Business Value Proposition
- **Scalable Education Platform**: Supports unlimited users with tiered subscription model
- **Content Management Excellence**: Comprehensive admin tools for educators and content creators
- **Progressive Learning Path**: Structured curriculum with prerequisite-based advancement
- **Multi-Modal Learning**: Combines traditional content with interactive multimedia experiences
- **Data-Driven Insights**: Built-in progress tracking and analytics capabilities

### Technical Excellence
- **Modern Architecture**: Flask-based microservice-ready design with clear separation of concerns
- **Security-First Approach**: Comprehensive authentication, authorization, and data protection
- **Performance Optimized**: Efficient database design with relationship optimization
- **Maintainable Codebase**: Clean architecture with extensive documentation and migration tools
- **Deployment Ready**: Environment-agnostic configuration with production considerations

### Key Metrics & Capabilities
- **Content Types**: 4 core Japanese learning content categories (Kana, Kanji, Vocabulary, Grammar)
- **User Management**: Role-based access control with subscription tiers
- **Lesson System**: Paginated, interactive lessons with progress tracking
- **File Management**: Comprehensive upload system with validation and security
- **API Coverage**: 40+ RESTful endpoints for complete system control
- **Database Efficiency**: 12 optimized tables with proper indexing and relationships

---

## Project Overview

### Purpose
A comprehensive web-based Japanese learning platform that provides structured lessons for learning Hiragana, Katakana, Kanji, vocabulary, and grammar. The platform features a tiered subscription model with free and premium content access.

### Key Features
- **Unified Authentication System** - Single login for both users and administrators
- **Subscription Management** - Free and Premium tiers with upgrade/downgrade functionality
- **Content Management System** - Full CRUD operations for all learning materials
- **Role-Based Access Control** - Separate permissions for users and administrators
- **Responsive Design** - Works on desktop and mobile devices
- **Real-Time Interface** - Dynamic content loading without page refreshes

### Target Users
- **Students** - Individuals learning Japanese language
- **Educators** - Teachers managing Japanese learning content
- **Administrators** - System managers overseeing platform operations

---

## System Architecture

### High-Level Architecture Overview
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
│         │                                                   │
│         ▼ (Interacts with Models, Renders Templates)        │
│ ┌───────────────┐     ┌────────────────┐                    │
│ │ Models        │◀─▶ │ Database       │                    │
│ │ (app/models.py) │   │ (SQLAlchemy ORM) │                  │
│ │  - Data Logic   │   │  - SQLite      │                    │
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
│  │ (site.db)   │   │ (Flask-Migrate)│   │ (UPLOAD_FOLDER)│  │
│  └─────────────┘   └─────────────┘   └───────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Core Design Principles

#### 1. **Separation of Concerns**
- **Models (`app/models.py`)**: Define the data structure, relationships, and business logic directly related to data entities (e.g., User, Lesson, Kana). They interact with the ORM (SQLAlchemy).
- **Views (Templates - `app/templates/`)**: Handle the presentation logic. Jinja2 templates are used to render HTML dynamically based on data passed from controllers.
- **Controllers (Routes - `app/routes.py`)**: Manage the application flow. They handle incoming HTTP requests, interact with models to fetch or modify data, process input (often with the help of forms), and select appropriate templates to render or return JSON responses for API calls.
- **Forms (`app/forms.py`)**: Manage form data submission, validation (using WTForms and Flask-WTF), and CSRF protection.
- **Utilities (`app/utils.py`)**: Contain helper functions and classes that provide reusable logic across different parts of the application, such as `FileUploadHandler` for managing file uploads and `convert_to_embed_url` for YouTube URLs.

#### 2. **Single Responsibility Principle**
- Each Python module (e.g., `models.py`, `routes.py`, `forms.py`, `utils.py`) has a distinct area of responsibility.
- Database models are focused on data representation and data-related operations.
- Route handlers in `app/routes.py` are responsible for the request-response cycle of specific URLs.
- `FileUploadHandler` in `app/utils.py` centralizes all file upload processing and validation logic.

#### 3. **Dependency Management & Application Factory**
- The application uses an **application factory pattern** (`create_app` function in `app/__init__.py`). This approach allows for:
    - Easier configuration management (e.g., different configs for development, testing, production).
    - Delayed initialization of Flask extensions until the app object is created.
    - Improved testability by creating multiple app instances.
- Python package dependencies are managed in `requirements.txt` and isolated using virtual environments.

#### 4. **Security by Design**
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

### Data Flow Architecture

#### User Request Flow (Typical Web Page Interaction)
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

#### Admin API Request Flow (e.g., Content Management via AJAX)
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

#### File Upload Process Flow
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

#### Lesson Progress Tracking Flow (User Interacting with Lesson Content)
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

---

## Technology Stack & Design Decisions

This section outlines the key technologies used in the project and the rationale behind their selection.

### Core Backend Technologies

| Technology        | Version (from `requirements.txt`) | Purpose                                       | Design Rationale                                                                                                                               |
|-------------------|-----------------------------------|-----------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------|
| **Python**        | 3.8+ (Implied)                    | Core programming language                     | Widely adopted, large ecosystem, strong for web development, readability.                                                                      |
| **Flask**         | >=2.0                             | Web framework                                 | Lightweight, flexible microframework allowing for custom component choices. Good for rapid development and clear structure.                    |
| **SQLAlchemy**    | >=2.5                             | Object-Relational Mapper (ORM)                | Powerful ORM for database interaction, database agnostic (SQLite for dev), handles complex relationships, migrations via Flask-Migrate.          |
| **Flask-SQLAlchemy**| >=2.5                             | Flask integration for SQLAlchemy              | Simplifies SQLAlchemy setup and session management within a Flask application.                                                                 |
| **Flask-Login**   | >=0.6.0                           | User session management, authentication       | Handles user login, logout, session tracking, and provides decorators like `@login_required`.                                                    |
| **Flask-WTF**     | >=1.0.0                           | Form handling, CSRF protection                | Integrates WTForms with Flask, providing easy form creation, validation, and crucial CSRF protection.                                          |
| **WTForms**       | >=3.0.0                           | Form creation and validation library          | Flexible library for defining form fields and validation rules.                                                                                |
| **Werkzeug**      | >=2.0.0                           | WSGI utility library (Flask dependency)       | Provides password hashing (`generate_password_hash`, `check_password_hash`), routing, and other WSGI utilities used by Flask.                    |
| **Flask-Migrate** | >=3.1.0                           | SQLAlchemy database migrations (Alembic)      | Manages database schema changes over time, allowing for versioning and incremental updates to the database structure.                            |
| **python-dotenv** | >=0.19.0                          | Environment variable management               | Loads environment variables from a `.env` file for configuration (e.g., `SECRET_KEY`, `DATABASE_URL`).                                       |

### Core Frontend Technologies

| Technology            | Version         | Purpose                                     | Design Rationale                                                                                                                            |
|-----------------------|-----------------|---------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| **HTML5**             | N/A             | Structure of web pages                      | Standard markup language for web content.                                                                                                   |
| **CSS3**              | N/A             | Styling of web pages                        | Standard for styling, used in conjunction with Bootstrap. Custom CSS in `app/static/css/custom.css`.                                        |
| **JavaScript (ES6+)** | N/A             | Client-side interactivity, AJAX             | Used for dynamic UI updates, modal handling, AJAX requests to API endpoints, and managing interactive lesson components. No large JS framework. |
| **Bootstrap**         | 5.3.3 (CDN)     | Responsive UI framework, pre-built components | Provides a responsive grid system, styling for common UI elements (forms, buttons, modals), accelerating frontend development.              |
| **Jinja2**            | (Flask default) | Templating engine                           | Server-side template rendering, allows embedding Python logic in HTML, provides template inheritance, auto-escaping for XSS protection.       |

### File Handling & Processing

| Technology        | Version (from `requirements.txt`) | Purpose                                     | Design Rationale                                                                                                                        |
|-------------------|-----------------------------------|---------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------|
| **Pillow**        | >=9.0.0                           | Image processing                            | Used by `FileUploadHandler` for opening, resizing, and optimizing uploaded images (e.g., converting format, creating thumbnails).        |
| **python-magic**  | >=0.4.24                          | File type identification (MIME types)       | Used by `FileUploadHandler` to validate file content by checking its actual MIME type, rather than relying solely on file extension.     |
| **python-magic-bin**| >=0.4.14                          | Windows binaries for python-magic           | Dependency for `python-magic` to work correctly on Windows environments.                                                                |

### Database

| Technology        | Version         | Purpose                                     | Design Rationale                                                                                                                            |
|-------------------|-----------------|---------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| **SQLite**        | (Python default)| Development and default production database | Simple, file-based database, zero-configuration, suitable for development and small to medium-scale applications. Easy to set up and manage. |
| **Alembic**       | (via Flask-Migrate) | Database schema migration tool              | Used by Flask-Migrate to handle versioning of the database schema, allowing for controlled evolution of table structures.                   |

### Design Choices & Justifications

#### Backend Architecture
- **Monolithic Application**: Chosen for simplicity in development and deployment for the current scale. The structure (using Blueprints and an app factory) allows for potential future separation into microservices if needed.
- **Application Factory (`create_app`)**: Enhances testability and allows for multiple configurations (e.g., development, production, testing).
- **SQLAlchemy ORM**: Provides a high-level abstraction for database interactions, improving developer productivity and making it easier to switch database backends if necessary.
- **Flask-Login for Authentication**: Standard Flask extension for robust session-based authentication.
- **Flask-WTF for Forms & CSRF**: Ensures secure form handling and protects against Cross-Site Request Forgery attacks.

#### Frontend Architecture
- **Server-Side Rendering with Jinja2**: Traditional approach suitable for content-heavy pages and simplifies initial development.
- **Vanilla JavaScript for Interactivity**: Keeps the frontend lightweight and avoids dependency on large JavaScript frameworks for current needs. AJAX is used for dynamic updates and API interactions.
- **Bootstrap for UI**: Accelerates frontend development with a responsive design and pre-styled components, ensuring a consistent look and feel.

#### Database Design
- **Normalized Relational Schema**: Designed to reduce data redundancy and improve data integrity using foreign keys and relationships (primarily aiming for Third Normal Form - 3NF).
- **SQLite as Default**: Chosen for ease of setup and development. The use of SQLAlchemy allows for a straightforward migration to more robust databases like PostgreSQL or MySQL for production scaling.
- **Flask-Migrate with Alembic**: Ensures that database schema changes are version-controlled and can be applied systematically across different environments.

#### Security
- **Defense in Depth**: Multiple layers of security are employed:
    - Input validation (client-side via JS, server-side via WTForms and API checks).
    - CSRF protection on all state-changing form submissions.
    - Secure password hashing.
    - Role-Based Access Control (RBAC) for different user types.
    - Secure file handling (extension and content validation, secure filenames).
    - Auto-escaping in Jinja2 to prevent XSS.
- **Principle of Least Privilege**: Users and admins are granted only the permissions necessary for their roles.

#### File Uploads (`FileUploadHandler`)
- **Centralized Logic**: All file upload operations (validation, processing, storage, metadata extraction) are handled by the `FileUploadHandler` class in `app/utils.py`, promoting code reuse and maintainability.
- **Security Focus**: Includes multiple validation steps (extension, MIME type), secure filename generation, and image processing to mitigate risks associated with user-uploaded files.
- **Organized Storage**: Files are stored in a structured way within the `UPLOAD_FOLDER` (e.g., `app/static/uploads/lessons/<file_type>/<filename>`), making them manageable and servable via a dedicated route.

---


### Backend Framework
- **Flask** - Python web framework
- **Flask-Login** - User session management
- **Flask-WTF** - Form handling and CSRF protection
- **SQLAlchemy** - Database ORM
- **Werkzeug** - Password hashing and security utilities

### Frontend Technologies
- **HTML5** - Semantic markup
- **CSS3** - Styling with Bootstrap framework
- **JavaScript (ES6+)** - Dynamic interactions and AJAX
- **Bootstrap 5.3.3** - Responsive UI framework

### Database
- **SQLite** - Development database (easily replaceable with PostgreSQL/MySQL)
- **Database File**:
  - `instance/site.db` - Main application database. (Note: `japanese_learning.db` is a legacy database file found in the `deprecated/` directory and is not used by the current application.)

### Development Tools
- **Python 3.8+** - Programming language
- **pip** - Package management
- **Virtual Environment** - Dependency isolation

---

## Installation & Setup

This section guides developers through setting up the project for local development.

### Prerequisites
Ensure the following software is installed on your system:
- **Python**: Version 3.8 or higher.
- **pip**: Python package installer (usually comes with Python).
- **Git**: Version control system for cloning the repository.
- **SQLite 3**: (Optional, but good to have the command-line client for direct database inspection. The Python `sqlite3` module is built-in.)

### Step-by-Step Installation

1.  **Clone the Repository:**
    ```bash
    git clone <your-repository-url>
    cd Japanese_Learning_Website
    ```
    Replace `<your-repository-url>` with the actual URL of the Git repository.

2.  **Create and Activate a Virtual Environment:**
    It's highly recommended to use a virtual environment to manage project dependencies.
    ```bash
    # Create the virtual environment (e.g., named 'venv')
    python -m venv venv

    # Activate the virtual environment
    # On Windows:
    # venv\Scripts\activate
    # On macOS/Linux:
    source venv/bin/activate
    ```

3.  **Install Dependencies:**
    Install all required Python packages listed in `requirements.txt`.
    ```bash
    pip install -r requirements.txt
    ```

4.  **Environment Configuration (`.env` file):**
    Create a `.env` file in the root directory of the project. This file stores environment-specific configurations. Add the following essential variables:
    ```env
    # Flask Configuration
    FLASK_APP=run.py
    FLASK_ENV=development # Use 'production' for production deployments
    FLASK_DEBUG=True      # Set to False in production

    # Secret Key (Change this to a random, strong string for production)
    SECRET_KEY=your-super-secret-and-random-key-here

    # Database Configuration
    DATABASE_URL=sqlite:///instance/site.db # Path to the SQLite database file

    # File Upload Configuration
    UPLOAD_FOLDER=app/static/uploads # Default path for storing uploaded files
    # ALLOWED_EXTENSIONS are configured in app/__init__.py or instance/config.py
    MAX_CONTENT_LENGTH=16777216 # Optional: Max file size for uploads (e.g., 16MB)
    ```
    **Important:**
    - The `instance` folder (for `site.db`) will be created automatically by Flask if it doesn't exist when the database is first accessed or initialized.
    - Ensure `UPLOAD_FOLDER` (`app/static/uploads`) exists or is created. The application attempts to create subdirectories within this folder.

5.  **Database Initialization and Migration:**
    The project uses Flask-Migrate (with Alembic) for managing database schema changes.
    
    a.  **Initialize the Database (First time setup for a new database):**
        If you are setting up the project with a brand new database (e.g., `instance/site.db` does not exist or is empty and you are not using existing migrations from another source):
        ```bash
        # Create all tables based on models (alternative to migrations for a fresh start)
        # flask db_init 
        # ^ This command from run.py actually calls db.create_all().
        # For a typical Flask-Migrate workflow, you'd initialize migrations first if starting a project from scratch.
        # However, given the existing setup, the primary way to set up the DB is via migrations.
        
        # If the 'migrations' folder doesn't exist or you need to set up Flask-Migrate:
        # flask db init  (This creates the migrations directory - only needed once per project)
        
        # Stamp the database with the latest migration version (if migrations already exist and you're setting up a new DB)
        # flask db stamp head
        
        # Apply all migrations to create the schema:
        flask db upgrade
        ```
        *Initial Setup Note:* The project includes several standalone scripts like `setup_unified_auth.py` and `migrate_lesson_system.py`. The most robust way to initialize the database according to current best practices with Flask-Migrate is to ensure all schema definitions in `app/models.py` are comprehensive and then use `flask db upgrade`. If these scripts perform essential seeding or setup not covered by migrations, they should be run *after* `flask db upgrade` or their logic incorporated into migrations. For simplicity, `flask db upgrade` should be the primary command to set up the schema.

    b.  **Applying Migrations (If migrations exist):**
        If the `migrations` folder with version history exists, apply them:
        ```bash
        flask db upgrade
        ```
        This command applies any pending database migrations to create or update the database schema according to `app/models.py` and the migration history.

    c.  **Creating an Initial Admin User:**
        After the database schema is set up, create an initial admin user:
        ```bash
        python create_admin.py
        ```
        Follow the prompts to set the admin's username, email, and password.

6.  **Run the Development Server:**
    ```bash
    flask run
    # Alternatively, you can use:
    # python run.py
    ```
    The application will typically be available at `http://127.0.0.1:5000/` or `http://localhost:5000/`.

7.  **Access the Application:**
    -   **Main Site:** `http://localhost:5000/`
    -   **Admin Panel:** `http://localhost:5000/admin` (Login with the admin credentials created in step 5c).

### Default Credentials (after running `create_admin.py`)
-   **Admin Username:** (As provided during `create_admin.py` execution, e.g., `admin`)
-   **Admin Email:** (As provided, e.g., `admin@example.com`)
-   **Admin Password:** (As provided, e.g., `admin123`)

*Note: The `create_admin.py` script sets default values if you press Enter without typing input, which are `admin`, `admin@example.com`, and `admin123`.*

### Managing Database Migrations
When you change your database models (`app/models.py`):
1.  **Generate a new migration script:**
    ```bash
    flask db migrate -m "Descriptive message for your changes"
    ```
2.  **Review the generated script** in the `migrations/versions/` directory.
3.  **Apply the migration to your database:**
    ```bash
    flask db upgrade
    ```
To revert the last migration:
```bash
flask db downgrade
```

---

## User Authentication System

The Japanese Learning Website employs a unified authentication system for both regular users and administrators, leveraging Flask-Login for session management and custom logic for role-based access control.

### Authentication Flow

1.  **User Registration (`/register` route, `RegistrationForm`):**
    *   New users provide a username, email, and password.
    *   The system checks for unique username and email (`User.validate_username`, `User.validate_email`).
    *   Passwords are securely hashed using `werkzeug.security.generate_password_hash` (PBKDF2) before being stored in the `user.password_hash` field.
    *   Upon successful registration, a new `User` record is created with `subscription_level` defaulting to 'free' and `is_admin` defaulting to `False`.

2.  **User Login (`/login` route, `LoginForm`):**
    *   Users log in with their email and password.
    *   The system retrieves the user by email and verifies the password using `user.check_password(password)`.
    *   If credentials are valid, `flask_login.login_user(user)` is called, establishing a secure session.
    *   A "Remember Me" option allows for persistent sessions.
    *   Upon successful login, users are redirected:
        *   Administrators (`user.is_admin == True`) are redirected to the admin dashboard (`/admin`).
        *   Regular users are redirected to the homepage (`/`) or their intended page (`next_page`).

3.  **Session Management (Flask-Login):**
    *   Flask-Login handles user sessions using secure cookies.
    *   The `@login_required` decorator protects routes that require an authenticated user.
    *   The `current_user` proxy from Flask-Login provides access to the logged-in user object in views and templates.
    *   A user loader function (`load_user(user_id)` in `app/models.py`) is registered with Flask-Login to reload the user object from the user ID stored in the session.

4.  **Logout (`/logout` route):**
    *   `flask_login.logout_user()` clears the user session and removes the user from being logged in.

5.  **Role Assignment and Access Control:**
    *   **User Roles:**
        *   `User.subscription_level`: Determines content access ('free' or 'premium').
        *   `User.is_admin`: A boolean flag (`True`/`False`) grants administrative privileges.
    *   **Access Control Decorators (`app/routes.py`):**
        *   `@login_required`: Ensures the user is logged in.
        *   `@admin_required`: Ensures `current_user.is_admin` is `True`.
        *   `@premium_required`: Ensures `current_user.subscription_level` is 'premium'. (Currently, subscription changes are simulated via prototype routes `/upgrade_to_premium` and `/downgrade_from_premium`).
    *   Content and feature access within routes and templates is further controlled by checking `current_user.is_admin` and `current_user.subscription_level`.

### User Roles & Permissions Summary

#### 1. Standard Users (Free Tier - `subscription_level='free'`)
- **Authentication**: Can register and log in.
- **Content Access**: Access to lessons and content marked as 'free'.
- **Account Management**: Can potentially upgrade to premium (prototype functionality).
- **Permissions**: Cannot access admin panel or premium content.

#### 2. Premium Users (Premium Tier - `subscription_level='premium'`)
- **Authentication**: Can register and log in.
- **Content Access**: Access to both 'free' and 'premium' lessons and content.
- **Account Management**: Can potentially downgrade to free (prototype functionality).
- **Permissions**: Cannot access admin panel.

#### 3. Administrators (`is_admin=True`)
- **Authentication**: Log in via the standard `/login` route.
- **Content Access**: Full access to all user-facing content (implicitly, as admin checks often supersede subscription checks for admin panel functionality).
- **Admin Panel Access**: Full access to the admin panel (`/admin` and its sub-routes) for managing:
    - Kana, Kanji, Vocabulary, Grammar content.
    - Lesson Categories.
    - Lessons (including creating pages, adding/ordering content, managing prerequisites, publishing).
    - Uploading files for lessons.
    - Creating interactive quiz content.
- **Permissions**: Can perform all CRUD operations on content and lessons. User management capabilities (e.g., directly modifying other users' roles or details) are not explicitly detailed in the current admin routes but could be a future enhancement.

### Security Aspects

-   **Password Hashing**: Werkzeug's `generate_password_hash` (PBKDF2 with salt) is used to securely store passwords.
-   **Session Cookies**: Flask-Login uses cryptographically signed cookies to maintain session integrity. The `SECRET_KEY` from the application configuration is crucial for this.
-   **CSRF Protection**: Flask-WTF is integrated, providing CSRF protection for all form submissions.
    -   Standard forms (`RegistrationForm`, `LoginForm`) automatically include CSRF tokens.
    -   Actions like subscription changes (`/upgrade_to_premium`, `/downgrade_from_premium`) and lesson progress reset (`/lessons/<id>/reset`) use a `CSRFTokenForm` to ensure these POST requests are protected even without other form data.
-   **Route Protection**: Decorators (`@login_required`, `@admin_required`, `@premium_required`) prevent unauthorized access to routes.

---

## Admin Content Management

Administrators have access to a dedicated panel for managing all learning content within the application. This includes core Japanese language elements (Kana, Kanji, Vocabulary, Grammar) and the structured Lesson System (Categories, Lessons, Lesson Content including pages, files, and quizzes).

### Accessing the Admin Panel
-   **URL**: `/admin`
-   **Authentication**: Requires an authenticated user with `is_admin=True`.
-   The admin panel provides navigation to different management sections.

### Core Content Types & Management

The following core content types can be managed via dedicated pages within the admin panel, typically involving modal forms for creating/editing and dynamic tables for display. Operations are performed via AJAX calls to their respective API endpoints (e.g., `/api/admin/kana`).

#### 1. Kana Management (`/admin/manage/kana`)
   - **Model**: `app.models.Kana`
   - **Fields Managed**:
     - `character`: The Kana character (e.g., "あ", "ア"). (String, Unique)
     - `romanization`: Romanized reading (e.g., "a", "ka"). (String)
     - `type`: Type of Kana ('hiragana' or 'katakana'). (String)
     - `stroke_order_info`: Textual or link to stroke order information. (String, Optional)
     - `example_sound_url`: URL to an audio pronunciation example. (String, Optional)
   - **API Endpoints**:
     - `GET /api/admin/kana`: List all Kana.
     - `POST /api/admin/kana/new`: Create new Kana.
     - `GET /api/admin/kana/<id>`: Get specific Kana.
     - `PUT /api/admin/kana/<id>/edit`: Update Kana.
     - `DELETE /api/admin/kana/<id>/delete`: Delete Kana.

#### 2. Kanji Management (`/admin/manage/kanji`)
   - **Model**: `app.models.Kanji`
   - **Fields Managed**:
     - `character`: The Kanji character (e.g., "水"). (String, Unique)
     - `meaning`: English meaning(s). (Text)
     - `onyomi`: On'yomi reading(s). (String, Optional)
     - `kunyomi`: Kun'yomi reading(s). (String, Optional)
     - `jlpt_level`: JLPT proficiency level (e.g., 1-5). (Integer, Optional)
     - `stroke_order_info`: Textual or link to stroke order. (String, Optional)
     - `radical`: Main radical of the Kanji. (String, Optional)
     - `stroke_count`: Number of strokes. (Integer, Optional)
   - **API Endpoints**: Similar CRUD structure as Kana (e.g., `/api/admin/kanji`).

#### 3. Vocabulary Management (`/admin/manage/vocabulary`)
   - **Model**: `app.models.Vocabulary`
   - **Fields Managed**:
     - `word`: The vocabulary word in Japanese (e.g., "こんにちは"). (String, Unique)
     - `reading`: Hiragana/Katakana reading (e.g., "こんにちは"). (String)
     - `meaning`: English translation(s). (Text)
     - `jlpt_level`: JLPT proficiency level. (Integer, Optional)
     - `example_sentence_japanese`: Example sentence in Japanese. (Text, Optional)
     - `example_sentence_english`: English translation of the example. (Text, Optional)
     - `audio_url`: URL to an audio pronunciation. (String, Optional)
   - **API Endpoints**: Similar CRUD structure as Kana (e.g., `/api/admin/vocabulary`).

#### 4. Grammar Management (`/admin/manage/grammar`)
   - **Model**: `app.models.Grammar`
   - **Fields Managed**:
     - `title`: Title of the grammar point (e.g., "Verb Conjugation - Past Tense"). (String, Unique)
     - `explanation`: Detailed explanation of the grammar rule. (Text)
     - `structure`: Formula or pattern (e.g., "Verb-ますform + ました"). (String, Optional)
     - `jlpt_level`: JLPT proficiency level. (Integer, Optional)
     - `example_sentences`: JSON string or Text field storing example sentences (structure needs to be defined, e.g., array of objects with `jp` and `en` keys). (Text, Optional)
   - **API Endpoints**: Similar CRUD structure as Kana (e.g., `/api/admin/grammar`).

### Lesson System Management

Management of the lesson system is more complex and involves several interconnected components, primarily managed through the `/admin/manage/lessons` interface, with categories managed at `/admin/manage/categories`.

#### 1. Lesson Category Management (`/admin/manage/categories`)
   - **Model**: `app.models.LessonCategory`
   - **Purpose**: To group lessons thematically (e.g., "Hiragana Basics", "JLPT N5 Grammar").
   - **Fields Managed**:
     - `name`: Name of the category (e.g., "Beginner Kanji"). (String, Unique)
     - `description`: A brief description of the category. (Text, Optional)
     - `color_code`: Hex color code for UI display (e.g., "#007bff"). (String, Optional, Defaults to '#007bff')
   - **API Endpoints**:
     - `GET /api/admin/categories`: List all categories.
     - `POST /api/admin/categories/new`: Create new category.
     - `GET /api/admin/categories/<id>`: Get specific category.
     - `PUT /api/admin/categories/<id>/edit`: Update category.
     - `DELETE /api/admin/categories/<id>/delete`: Delete category.

#### 2. Lesson Management (`/admin/manage/lessons`)
   - **Model**: `app.models.Lesson`
   - **Purpose**: To create structured learning modules composed of various content items organized into pages.
   - **Key Fields Managed (Lesson Level)**:
     - `title`: Title of the lesson. (String)
     - `description`: Overview of the lesson. (Text, Optional)
     - `lesson_type`: 'free' or 'premium'. (String)
     - `category_id`: Associates the lesson with a `LessonCategory`. (ForeignKey)
     - `difficulty_level`: Numerical difficulty (e.g., 1-5). (Integer, Optional)
     - `estimated_duration`: Estimated time to complete in minutes. (Integer, Optional)
     - `order_index`: For ordering lessons within a category/listing. (Integer, Optional)
     - `is_published`: Boolean flag to make the lesson visible to users. (Boolean)
     - `thumbnail_url`: URL for a lesson cover image. (String, Optional)
     - `video_intro_url`: URL for an introductory video. (String, Optional)
     - **Prerequisites**: Admins can define other lessons that must be completed before this lesson can be accessed. Managed via associations in the `LessonPrerequisite` table.
   - **Lesson Content & Page Management (within a specific lesson's edit interface)**:
     - **Pages (`app.models.LessonPage`)**:
       - Lessons are structured into one or more pages.
       - Admins can create new pages, define page titles and descriptions (`LessonPage.title`, `LessonPage.description`).
       - Pages are ordered by their `page_number`.
       - API: `PUT /api/admin/lessons/<lesson_id>/pages/<page_num>` (update/create), `DELETE /api/admin/lessons/<lesson_id>/pages/<page_num>/delete`.
     - **Content Items (`app.models.LessonContent`)**:
       - Within each page, admins can add various types of content.
       - **Content Types Supported**:
         - **Existing Content**: Select from existing Kana, Kanji, Vocabulary, or Grammar items. (`content_type` = 'kana', 'kanji', etc.; `content_id` links to the item).
         - **Custom Text**: Add formatted text directly. (`content_type` = 'text'; `content_text` stores the text).
         - **Media (URL-based)**: Embed images, videos (e.g., YouTube via `convert_to_embed_url`), or audio using URLs. (`content_type` = 'image'/'video'/'audio'; `media_url` stores the URL).
         - **Media (File Upload)**: Upload images, audio files, or documents.
           - Files are first uploaded via `POST /api/admin/upload-file`.
           - The returned `dbPath` is then stored in `LessonContent.file_path`.
           - Other metadata like `file_size`, `original_filename`, `file_type` are also stored.
           - (`content_type` = 'image'/'audio'/'document', etc.)
         - **Interactive Content (Quizzes)**: Create quiz questions.
           - (`content_type` = 'interactive', `is_interactive` = True).
           - Associated `QuizQuestion` and `QuizOption` records are created/managed.
           - Types: Multiple Choice, Fill-in-the-Blank, True/False.
       - **Fields for `LessonContent`**: `title` (optional), `content_text` (for text type), `media_url` (for URL media), `file_path` (for uploaded files), `order_index` (for ordering within a page), `page_number`, `is_optional`.
       - **API Endpoints for Lesson Content**:
         - `POST /api/admin/lessons/<lesson_id>/content/new`: Add new content item to a page.
         - `PUT /api/admin/content/<content_id>/edit`: Update existing content item.
         - `DELETE /api/admin/lessons/<lesson_id>/content/<content_id>/delete`: Remove content item (also deletes associated file if `file_path` exists).
         - `POST /api/admin/lessons/<lesson_id>/content/interactive`: Add new interactive (quiz) content.
         - `POST /api/admin/lessons/<lesson_id>/content/file`: Add new file-based content (associates an uploaded file).
         - Ordering: `POST /api/admin/lessons/<lesson_id>/content/<content_id>/move`, `POST /api/admin/lessons/<lesson_id>/pages/<page_number>/reorder`.
         - Bulk Operations: `PUT /bulk-update`, `POST /bulk-duplicate`, `DELETE /bulk-delete`.
         - Preview: `GET /api/admin/content/<content_id>/preview`.
   - **API Endpoints for Lessons**:
     - `GET /api/admin/lessons`: List all lessons.
     - `POST /api/admin/lessons/new`: Create new lesson shell.
     - `GET /api/admin/lessons/<id>`: Get specific lesson details (including its pages and content).
     - `PUT /api/admin/lessons/<id>/edit`: Update lesson metadata.
     - `DELETE /api/admin/lessons/<id>/delete`: Delete lesson (cascades to its pages and content).

### General CRUD Operations Flow (Admin Panel)

1.  **Read**: Content items (Kana, Kanji, Lessons, etc.) are typically listed in dynamic HTML tables, populated via AJAX calls to `GET` API endpoints (e.g., `GET /api/admin/kana`).
2.  **Create**:
    *   Admin clicks an "Add New..." button.
    *   A modal form appears.
    *   Admin fills in the details.
    *   On submission, an AJAX `POST` request is sent to the relevant `/new` API endpoint (e.g., `POST /api/admin/kana/new`) with the data as a JSON payload.
    *   The API creates the new item in the database.
    *   The table in the UI refreshes to show the new item.
3.  **Update**:
    *   Admin clicks an "Edit" button/link next to an item.
    *   A modal form appears, pre-populated with the item's existing data (fetched via a `GET /api/admin/<content_type>/<id>` request).
    *   Admin modifies the details.
    *   On submission, an AJAX `PUT` (or `PATCH`) request is sent to the relevant `/<id>/edit` API endpoint (e.g., `PUT /api/admin/kana/<id>/edit`).
    *   The API updates the item in the database.
    *   The table in the UI refreshes.
4.  **Delete**:
    *   Admin clicks a "Delete" button/link next to an item.
    *   A confirmation dialog appears.
    *   On confirmation, an AJAX `DELETE` request is sent to the relevant `/<id>/delete` API endpoint (e.g., `DELETE /api/admin/kana/<id>/delete`).
    *   The API deletes the item from the database (and any associated files for `LessonContent`).
    *   The item is removed from the table in the UI.

### Publishing Content
-   **Lessons**: For a lesson to be visible to users on the main `/lessons` page, its `is_published` flag must be set to `True`. This is typically done through the lesson editing interface.
-   Other content types (Kana, Kanji, etc.) are generally available for inclusion in lessons as soon as they are created.

---

## Database Schema

The application uses SQLAlchemy as its ORM and SQLite as the default database. The schema is designed to support user authentication, content management for Japanese language elements, and a comprehensive lesson system with progress tracking and interactive quizzes. All models are defined in `app/models.py`.

**Note on SQL Syntax:** The `CREATE TABLE` statements below are representative of the schema defined by the SQLAlchemy models. Actual SQLite syntax might vary slightly (e.g., `BOOLEAN` often stored as `INTEGER` 0 or 1). Foreign key constraints with `ON DELETE CASCADE` are implemented via SQLAlchemy relationships with `cascade='all, delete-orphan'`.

### 1. `user` Table
Stores user account information.
```sql
CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL, -- Stores hashed passwords (PBKDF2)
    subscription_level VARCHAR(50) DEFAULT 'free' NOT NULL, -- e.g., 'free', 'premium'
    is_admin BOOLEAN DEFAULT FALSE NOT NULL,
    -- created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Implicitly handled by SQLAlchemy/model if default=datetime.utcnow
);
-- Relationships:
--   - One-to-Many with UserLessonProgress (user.lesson_progress)
--   - One-to-Many with UserQuizAnswer (user.quiz_answers - if added, currently UserQuizAnswer links to user)
```

### 2. `kana` Table
Stores Hiragana and Katakana characters.
```sql
CREATE TABLE kana (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character VARCHAR(5) UNIQUE NOT NULL,
    romanization VARCHAR(10) NOT NULL,
    type VARCHAR(10) NOT NULL, -- 'hiragana' or 'katakana'
    stroke_order_info VARCHAR(255), -- Text or link
    example_sound_url VARCHAR(255)  -- URL to audio
);
```

### 3. `kanji` Table
Stores Kanji characters and their details.
```sql
CREATE TABLE kanji (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character VARCHAR(5) UNIQUE NOT NULL,
    meaning TEXT NOT NULL,
    onyomi VARCHAR(100),
    kunyomi VARCHAR(100),
    jlpt_level INTEGER,
    stroke_order_info VARCHAR(255), -- Text or link
    radical VARCHAR(10),
    stroke_count INTEGER
);
```

### 4. `vocabulary` Table
Stores vocabulary words and phrases.
```sql
CREATE TABLE vocabulary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word VARCHAR(100) UNIQUE NOT NULL,
    reading VARCHAR(100) NOT NULL, -- Hiragana/Katakana reading
    meaning TEXT NOT NULL,
    jlpt_level INTEGER,
    example_sentence_japanese TEXT,
    example_sentence_english TEXT,
    audio_url VARCHAR(255) -- URL to audio
);
```

### 5. `grammar` Table
Stores grammar rules and patterns.
```sql
CREATE TABLE grammar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(200) UNIQUE NOT NULL,
    explanation TEXT NOT NULL,
    structure VARCHAR(255), -- e.g., "Verb-ますform + ました"
    jlpt_level INTEGER,
    example_sentences TEXT -- Stores JSON string of examples
);
```

### 6. `lesson_category` Table
Organizes lessons into categories.
```sql
CREATE TABLE lesson_category (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    color_code VARCHAR(7) DEFAULT '#007bff', -- Hex color for UI
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- Relationships:
--   - One-to-Many with Lesson (lesson_category.lessons)
```

### 7. `lesson` Table
Defines individual lessons.
```sql
CREATE TABLE lesson (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    lesson_type VARCHAR(20) NOT NULL, -- 'free' or 'premium'
    category_id INTEGER,
    difficulty_level INTEGER, -- e.g., 1-5
    estimated_duration INTEGER, -- In minutes
    order_index INTEGER DEFAULT 0,
    is_published BOOLEAN DEFAULT FALSE NOT NULL,
    thumbnail_url VARCHAR(255),
    video_intro_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- onupdate=datetime.utcnow
    FOREIGN KEY (category_id) REFERENCES lesson_category (id)
);
-- Relationships:
--   - One-to-Many with LessonContent (lesson.content_items)
--   - One-to-Many with LessonPrerequisite (lesson.prerequisites - lessons this lesson requires)
--   - One-to-Many with LessonPrerequisite (lesson.required_by - lessons that require this one)
--   - One-to-Many with UserLessonProgress (lesson.user_progress)
--   - One-to-Many with LessonPage (lesson.pages_metadata)
```

### 8. `lesson_prerequisite` Table
Junction table for lesson dependencies (many-to-many relationship for lessons).
```sql
CREATE TABLE lesson_prerequisite (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson_id INTEGER NOT NULL,          -- The lesson that has prerequisites
    prerequisite_lesson_id INTEGER NOT NULL, -- The lesson that must be completed first
    FOREIGN KEY (lesson_id) REFERENCES lesson (id) ON DELETE CASCADE,
    FOREIGN KEY (prerequisite_lesson_id) REFERENCES lesson (id) ON DELETE CASCADE,
    UNIQUE (lesson_id, prerequisite_lesson_id)
);
```

### 9. `lesson_page` Table
Stores metadata for individual pages within a lesson.
```sql
CREATE TABLE lesson_page (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson_id INTEGER NOT NULL,
    page_number INTEGER NOT NULL,
    title VARCHAR(200),
    description TEXT,
    FOREIGN KEY (lesson_id) REFERENCES lesson (id) ON DELETE CASCADE,
    UNIQUE (lesson_id, page_number)
);
-- Relationships:
--   - Many-to-One with Lesson (lesson_page.lesson)
--   - Content items are linked via LessonContent.page_number and LessonContent.lesson_id
```

### 10. `lesson_content` Table
Stores individual content items within a lesson page.
```sql
CREATE TABLE lesson_content (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson_id INTEGER NOT NULL,
    content_type VARCHAR(20) NOT NULL, -- e.g., 'kana', 'text', 'image', 'interactive'
    content_id INTEGER,                -- FK to Kana, Kanji, etc., if applicable
    title VARCHAR(200),                -- For custom text, media titles
    content_text TEXT,                 -- For custom text content
    media_url VARCHAR(255),            -- URL for external media (YouTube, etc.)
    order_index INTEGER DEFAULT 0 NOT NULL,
    page_number INTEGER DEFAULT 1 NOT NULL, -- Associates content with a LessonPage
    is_optional BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- File upload fields
    file_path VARCHAR(500),            -- Relative path within UPLOAD_FOLDER
    file_size INTEGER,                 -- File size in bytes
    file_type VARCHAR(50),             -- Detected MIME type or category like 'image', 'audio'
    original_filename VARCHAR(255),    -- Original name of the uploaded file
    -- Interactive content fields
    is_interactive BOOLEAN DEFAULT FALSE NOT NULL,
    max_attempts INTEGER DEFAULT 3,
    passing_score INTEGER DEFAULT 70,  -- Percentage
    FOREIGN KEY (lesson_id) REFERENCES lesson (id) ON DELETE CASCADE
    -- Note: content_id can refer to Kana.id, Kanji.id, etc. This is a polymorphic association conceptually.
);
-- Relationships:
--   - Many-to-One with Lesson (lesson_content.lesson)
--   - One-to-Many with QuizQuestion (lesson_content.quiz_questions)
```

### 11. `quiz_question` Table
Stores questions for interactive `LessonContent`.
```sql
CREATE TABLE quiz_question (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson_content_id INTEGER NOT NULL, -- Links to the 'interactive' LessonContent item
    question_type VARCHAR(50) NOT NULL, -- 'multiple_choice', 'fill_blank', 'true_false'
    question_text TEXT NOT NULL,
    explanation TEXT,                   -- Explanation for the correct answer
    points INTEGER DEFAULT 1,
    order_index INTEGER DEFAULT 0 NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (lesson_content_id) REFERENCES lesson_content (id) ON DELETE CASCADE
);
-- Relationships:
--   - Many-to-One with LessonContent (quiz_question.content)
--   - One-to-Many with QuizOption (quiz_question.options)
--   - One-to-Many with UserQuizAnswer (quiz_question.user_answers)
```

### 12. `quiz_option` Table
Stores options for `QuizQuestion` (e.g., choices for multiple-choice).
```sql
CREATE TABLE quiz_option (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER NOT NULL,
    option_text TEXT NOT NULL,
    is_correct BOOLEAN DEFAULT FALSE NOT NULL,
    order_index INTEGER DEFAULT 0 NOT NULL,
    feedback TEXT, -- Specific feedback if this option is chosen
    FOREIGN KEY (question_id) REFERENCES quiz_question (id) ON DELETE CASCADE
);
-- Relationships:
--   - Many-to-One with QuizQuestion (quiz_option.question)
```

### 13. `user_quiz_answer` Table
Records users' answers to quiz questions.
```sql
CREATE TABLE user_quiz_answer (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    selected_option_id INTEGER,        -- FK to QuizOption, for multiple_choice/true_false
    text_answer TEXT,                  -- For fill_blank type questions
    is_correct BOOLEAN DEFAULT FALSE NOT NULL,
    answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- onupdate=datetime.utcnow
    attempts INTEGER DEFAULT 0 NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user (id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES quiz_question (id) ON DELETE CASCADE,
    FOREIGN KEY (selected_option_id) REFERENCES quiz_option (id), -- Can be NULL
    UNIQUE (user_id, question_id) -- A user has one answer record per question (attempts are tracked within)
);
-- Relationships:
--   - Many-to-One with User
--   - Many-to-One with QuizQuestion (user_quiz_answer.question)
```

### 14. `user_lesson_progress` Table
Tracks users' progress through lessons.
```sql
CREATE TABLE user_lesson_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    lesson_id INTEGER NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,             -- Timestamp when lesson is fully completed
    is_completed BOOLEAN DEFAULT FALSE NOT NULL,
    progress_percentage INTEGER DEFAULT 0 NOT NULL, -- Overall completion percentage (0-100)
    time_spent INTEGER DEFAULT 0 NOT NULL,          -- Time spent in minutes
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- onupdate=datetime.utcnow
    content_progress TEXT,             -- JSON string: {"content_id_1": true, "content_id_2": false}
    FOREIGN KEY (user_id) REFERENCES user (id) ON DELETE CASCADE,
    FOREIGN KEY (lesson_id) REFERENCES lesson (id) ON DELETE CASCADE,
    UNIQUE (user_id, lesson_id)
);
-- Relationships:
--   - Many-to-One with User (user_lesson_progress.user)
--   - Many-to-One with Lesson (user_lesson_progress.lesson)
```

---

## API Design & Endpoints

The application exposes several API endpoints for client-side interactions, primarily for admin content management, lesson progression, and file handling. All API endpoints are defined in `app/routes.py`.

**General API Conventions:**
-   **Authentication**: Most admin and user-specific APIs require authentication (`@login_required`). Admin APIs further require `@admin_required`.
-   **Request/Response Format**: APIs generally consume and produce JSON.
-   **Error Handling**: Standard HTTP status codes are used (e.g., 200 OK, 201 Created, 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 409 Conflict, 500 Internal Server Error). Error responses include a JSON object like `{"error": "Error message"}`.
-   **CSRF Protection**: API endpoints intended for AJAX calls from authenticated sessions typically rely on the browser's same-origin policy and session cookie handling. Flask-WTF's CSRF protection is primarily for HTML form submissions.

---
### Authentication & User Routes (HTML Pages, not strictly APIs)
These routes handle user session and basic page navigation. While they render HTML, some involve POST requests and form handling critical to the system.

-   **`POST /register`**
    -   Purpose: User registration.
    -   Request: Form data from `RegistrationForm`.
    -   Response: Redirects or re-renders registration page with errors.
-   **`POST /login`**
    -   Purpose: User login.
    -   Request: Form data from `LoginForm`.
    -   Response: Redirects or re-renders login page with errors.
-   **`GET /logout`**
    -   Purpose: User logout.
    -   Auth: `@login_required`.
    -   Response: Redirects to homepage.
-   **`POST /upgrade_to_premium`**
    -   Purpose: (Prototype) Upgrades user to premium.
    -   Auth: `@login_required`.
    -   Request: `CSRFTokenForm` data.
    -   Response: Redirects.
-   **`POST /downgrade_from_premium`**
    -   Purpose: (Prototype) Downgrades user to free.
    -   Auth: `@login_required`.
    -   Request: `CSRFTokenForm` data.
    -   Response: Redirects.

---
### Admin API Endpoints
All endpoints under `/api/admin/` require admin privileges (`@login_required`, `@admin_required`).

#### Core Content Management (Kana, Kanji, Vocabulary, Grammar)
These follow a standard RESTful CRUD pattern. Example using Kana (Kanji, Vocabulary, Grammar are analogous):

-   **`GET /api/admin/kana`**
    -   Purpose: List all Kana items.
    -   Response: JSON array of Kana objects. `[{"id": 1, "character": "あ", ...}, ...]`
-   **`POST /api/admin/kana/new`**
    -   Purpose: Create a new Kana item.
    -   Request: JSON payload with Kana fields (e.g., `{"character": "い", "romanization": "i", "type": "hiragana"}`).
        - Required: `character`, `romanization`, `type`.
    -   Response: 201 Created with JSON of the new Kana object, or 400/409 error.
-   **`GET /api/admin/kana/<int:item_id>`**
    -   Purpose: Get a specific Kana item.
    -   Response: JSON of the Kana object, or 404 error.
-   **`PUT /api/admin/kana/<int:item_id>/edit`** (also accepts PATCH)
    -   Purpose: Update an existing Kana item.
    -   Request: JSON payload with fields to update.
    -   Response: JSON of the updated Kana object, or 400/404 error.
-   **`DELETE /api/admin/kana/<int:item_id>/delete`**
    -   Purpose: Delete a Kana item.
    -   Response: 200 OK with `{"message": "Kana deleted successfully"}`, or 404 error.

*(Similar endpoints exist for `/api/admin/kanji/`, `/api/admin/vocabulary/`, `/api/admin/grammar/`)*

#### Lesson Category Management

-   **`GET /api/admin/categories`**: List all lesson categories.
-   **`POST /api/admin/categories/new`**: Create a new category.
    -   Request: `{"name": "Category Name", "description": "...", "color_code": "#RRGGBB"}`. Required: `name`.
-   **`GET /api/admin/categories/<int:item_id>`**: Get a specific category.
-   **`PUT /api/admin/categories/<int:item_id>/edit`**: Update a category.
-   **`DELETE /api/admin/categories/<int:item_id>/delete`**: Delete a category.

#### Lesson Management

-   **`GET /api/admin/lessons`**: List all lessons (includes `category_name`, `content_count`).
-   **`POST /api/admin/lessons/new`**: Create a new lesson shell.
    -   Request: `{"title": "Lesson Title", "lesson_type": "free/premium", ...}`. Required: `title`, `lesson_type`.
-   **`GET /api/admin/lessons/<int:item_id>`**: Get specific lesson details.
    -   Response includes `category_name`, `pages` (array of page objects, each with `metadata` and `content` items), `prerequisites` (array of lesson objects), and flat `content_items` list.
-   **`PUT /api/admin/lessons/<int:item_id>/edit`**: Update lesson metadata.
-   **`DELETE /api/admin/lessons/<int:item_id>/delete`**: Delete a lesson (cascades to its content and pages).

#### Lesson Page Management (within a Lesson)

-   **`PUT /api/admin/lessons/<int:lesson_id>/pages/<int:page_num>`**
    -   Purpose: Update or create metadata for a lesson page (title, description).
    -   Request: `{"title": "Page Title", "description": "..."}`.
    -   Response: JSON of the `LessonPage` object.
-   **`DELETE /api/admin/lessons/<int:lesson_id>/pages/<int:page_num>/delete`**
    -   Purpose: Delete a lesson page and all its content items.
    -   Response: 200 OK with success message, or 404/500 error.

#### Lesson Content Management (within a Lesson Page)

-   **`GET /api/admin/content-options/<content_type>`**
    -   Purpose: Get existing Kana, Kanji, Vocabulary, or Grammar items for selection in the lesson builder.
    -   `<content_type>` can be `kana`, `kanji`, `vocabulary`, `grammar`.
    -   Response: JSON array of the respective content items.
-   **`GET /api/admin/lessons/<int:lesson_id>/content`**
    -   Purpose: List all content items for a lesson (ordered by `order_index`).
    -   Response: JSON array of `LessonContent` objects.
-   **`POST /api/admin/lessons/<int:lesson_id>/content/new`**
    -   Purpose: Add a new content item to a specific page within a lesson.
    -   Request: JSON payload including `content_type`, `page_number`, and type-specific fields (e.g., `content_id` for existing items, `content_text` for text, `media_url` for URLs).
        - Required: `content_type`. `page_number` defaults to 1 if not provided.
    -   Response: 201 Created with JSON of the new `LessonContent` object.
-   **`PUT /api/admin/content/<int:content_id>/edit`**
    -   Purpose: Update an existing `LessonContent` item (including its type, text, associated content_id, media_url, file_path, page_number, order_index, or interactive quiz details).
    -   Request: JSON payload with fields to update.
    -   Response: JSON of the updated `LessonContent` object.
-   **`DELETE /api/admin/lessons/<int:lesson_id>/content/<int:content_id>/delete`**
    -   Purpose: Remove a `LessonContent` item from a lesson. Deletes associated file if `file_path` exists. Reorders remaining content on the page.
    -   Response: 200 OK with success message, or 404/500 error.
-   **`POST /api/admin/lessons/<int:lesson_id>/content/<int:content_id>/move`**
    -   Purpose: Move a `LessonContent` item up or down within its page.
    -   Request: `{"direction": "up" | "down"}`.
    -   Response: 200 OK with success message.
-   **`POST /api/admin/lessons/<int:lesson_id>/pages/<int:page_number>/reorder`**
    -   Purpose: Reorder `LessonContent` items on a specific page based on a provided list of `content_ids`.
    -   Request: `{"content_ids": [id1, id2, ...]}`.
    -   Response: 200 OK with success message.
-   **`GET /api/admin/content/<int:content_id>/preview`**
    -   Purpose: Get data for previewing a `LessonContent` item, including related data (e.g., Kana object details, quiz questions).
    -   Response: JSON of the `LessonContent` object with additional preview data.
-   **`GET /api/admin/content/<int:content_id>`**
    -   Purpose: Get full details of a single `LessonContent` item for editing, especially for interactive content (includes quiz question text, type, options, etc.).
    -   Response: JSON of the `LessonContent` object with detailed fields.
-   **`POST /api/admin/lessons/<int:lesson_id>/content/interactive`**
    -   Purpose: Add new interactive (quiz) content to a lesson page. Creates `LessonContent` of type 'interactive' and associated `QuizQuestion` / `QuizOption` records.
    -   Request: JSON payload detailing `interactive_type` (e.g., 'multiple_choice'), `question_text`, `options` (for multiple choice/true-false), `correct_answers` (for fill-in-the-blank), `page_number`, etc.
    -   Response: 201 Created with JSON of the new interactive `LessonContent` object.
-   **Bulk Operations for Lesson Content:**
    -   **`PUT /api/admin/lessons/<int:lesson_id>/content/bulk-update`**: Updates properties for multiple `LessonContent` items.
        -   Request: `{"content_ids": [...], "updates": {"field_to_update": "new_value"}}`.
    -   **`POST /api/admin/lessons/<int:lesson_id>/content/bulk-duplicate`**: Duplicates multiple `LessonContent` items.
        -   Request: `{"content_ids": [...]}`.
    -   **`DELETE /api/admin/lessons/<int:lesson_id>/content/bulk-delete`**: Deletes multiple `LessonContent` items.
        -   Request: `{"content_ids": [...]}`.
    -   **`POST /api/admin/lessons/<int:lesson_id>/content/force-reorder`**: Forces reordering of all content items in a lesson to fix index gaps.
    -   **`POST /api/admin/content/<int:content_id>/duplicate`**: Duplicates a single `LessonContent` item.

#### File Management API (Admin)

-   **`POST /api/admin/upload-file`**
    -   Purpose: Upload a file (image, audio, document) for use in lessons.
    -   Request: Multipart form data with `file` part. Optional `lesson_id` in form data (currently not used for directory structure).
    -   Process: Validates file type/extension/content, generates unique filename, processes images (resize/optimize), saves to `UPLOAD_FOLDER/lessons/<file_type>/<unique_filename>`.
    -   Response: JSON object with `success` status, `filePath` (URL for `url_for`), `dbPath` (relative path for DB storage, e.g., `lessons/<file_type>/filename.jpg`), `fileName`, `originalFilename`, `fileType`, `fileSize`, `mimeType`, `dimensions` (for images).
-   **`POST /api/admin/lessons/<int:lesson_id>/content/file`**
    -   Purpose: Create a `LessonContent` item of type image, audio, or document, associating an *already uploaded file* with it.
    -   Request: JSON payload including `content_type`, `title`, `description`, `file_path` (this should be the `dbPath` from the upload response), `file_size`, `file_type`, `original_filename`, `page_number`.
    -   Response: 201 Created with JSON of the new `LessonContent` object.
-   **`DELETE /api/admin/delete-file`**
    -   Purpose: Delete an uploaded file from the server. If `content_id` is provided and matches the `file_path`, the `LessonContent` database record is also deleted.
    -   Request: JSON payload `{"file_path": "path/relative/to/UPLOAD_FOLDER", "content_id": <optional_id>}`.
    -   Response: 200 OK with success message, or 400/404/500 error. Can return 207 Multi-Status if DB record deleted but file system deletion had issues.

---
### User API Endpoints
These endpoints are used by authenticated users interacting with lessons. All require `@login_required`.

-   **`GET /api/lessons`**
    -   Purpose: Get a list of all published lessons accessible to the current user.
    -   Response: JSON array of lesson objects, each including `accessible` status, `access_message`, `category_name`, and user's `progress` if any.
-   **`POST /api/lessons/<int:lesson_id>/progress`**
    -   Purpose: Update the current user's progress for a specific lesson. Used to mark content items as completed or log time spent.
    -   Request: JSON payload, e.g., `{"content_id": <id_of_completed_item>}` or `{"time_spent": <minutes>}`.
    -   Response: JSON of the updated `UserLessonProgress` object.
-   **`POST /api/lessons/<int:lesson_id>/quiz/<int:question_id>/answer`**
    -   Purpose: Submit the current user's answer to a quiz question within a lesson.
    -   Request: JSON payload, e.g., `{"selected_option_id": <id>}` for multiple choice, or `{"text_answer": "user's answer"}` for fill-in-the-blank.
    -   Response: JSON object with `is_correct` (boolean), `explanation` (for the question), `attempts_remaining`, and `option_feedback` (if applicable).

---
### Public File Serving Route

-   **`GET /uploads/<path:filename>`**
    -   Purpose: Serves uploaded files (images, audio, documents) stored within the application's `UPLOAD_FOLDER`.
    -   `<path:filename>` is the path relative to `UPLOAD_FOLDER` (e.g., `lessons/images/my_image.png`).
    -   Used by `LessonContent.get_file_url()` to generate accessible URLs.
    -   Includes security check to prevent access outside `UPLOAD_FOLDER`.
    -   Auth: None (publicly accessible if the path is known, but paths are typically not guessable and only exposed through lessons the user has access to).

---

## Frontend Architecture

The frontend of the Japanese Learning Website is built using a combination of server-side rendered Jinja2 templates, Bootstrap for styling and layout, and vanilla JavaScript for client-side interactivity and API communication.

### 1. Templating (Jinja2)
-   **Engine**: Jinja2, integrated seamlessly with Flask.
-   **Structure (`app/templates/`)**:
    -   `base.html`: Main layout template for user-facing pages. Defines common structure (navbar, footer, main content block). Other user templates extend this.
    -   `admin/base_admin.html`: Main layout template for the admin panel. Provides admin-specific navigation and structure. Admin page templates extend this.
    -   **User-facing pages**:
        -   `index.html`: Homepage.
        -   `login.html`: User login form.
        -   `register.html`: User registration form.
        -   `lessons.html`: Page to browse available lessons. Dynamically loads and filters lessons using JavaScript and API calls to `/api/lessons`.
        -   `lesson_view.html`: Page to view a single lesson's content. Features paginated content display (carousel-like structure), interactive quiz elements, and progress tracking updates, all managed with JavaScript interacting with endpoints like `/api/lessons/<lesson_id>/progress` and `/api/lessons/<lesson_id>/quiz/<question_id>/answer`.
    -   **Admin panel pages (`app/templates/admin/`)**:
        -   `admin_index.html`: Admin dashboard.
        -   `manage_kana.html`, `manage_kanji.html`, `manage_vocabulary.html`, `manage_grammar.html`: Interfaces for managing core Japanese content types. These typically include modals for adding/editing items and tables for displaying content, populated via AJAX calls to their respective `/api/admin/<content_type>` endpoints.
        -   `manage_categories.html`: Interface for managing lesson categories, interacting with `/api/admin/categories` endpoints.
        -   `manage_lessons.html`: Interface for managing lessons. This page includes the sophisticated lesson content builder, allowing admins to add/edit/order pages and various content types (text, media, files, quizzes) within each page. It heavily relies on JavaScript to interact with various `/api/admin/lessons/...` and `/api/admin/content/...` endpoints.
    -   **Common Elements**: Templates make use of Jinja2 features like template inheritance (`{% extends %}`), blocks (`{% block content %}`), includes (`{% include %}`), loops (`{% for %}`), conditionals (`{% if %}`), and URL generation (`url_for()`).
    -   **CSRF Tokens**: Forms rendered via Flask-WTF (e.g., login, registration) automatically include CSRF tokens (e.g., `{{ form.hidden_tag() }}` or `{{ form.csrf_token }}`). For AJAX requests that modify data (POST, PUT, DELETE) and are session-authenticated, the CSRF token is typically fetched from a meta tag or a hidden input on the page and included in the request headers (e.g., `X-CSRFToken`). The `CSRFTokenForm` is used in routes like `/upgrade_to_premium` for this purpose.

### 2. Styling (Bootstrap & Custom CSS)
-   **Primary Framework**: Bootstrap 5.3.3 (loaded via CDN as per current project setup).
    -   Used for responsive layout (grid system), pre-styled components (buttons, forms, modals, navigation bars, cards, carousels for lesson pages), and utility classes.
    -   Ensures a consistent look and feel and mobile-first design.
-   **Custom CSS (`app/static/css/custom.css`)**:
    -   Contains additional styles to override or augment Bootstrap defaults, and for specific application elements not covered by Bootstrap.
    -   This includes styling for the admin panel interface, lesson viewer enhancements, custom content elements, and potentially specific branding.
-   **Static Assets**:
    -   Custom CSS is served from the `app/static/css/` directory.
    -   Site-specific images (like backgrounds or logos, e.g., `japan_welcome_page.png`) are in `app/static/images/`.
    -   User-uploaded files (lesson content like images, audio) are stored in the `UPLOAD_FOLDER` (configured, e.g., `app/static/uploads/`) and served via the `/uploads/<path:filename>` route.

### 3. Client-Side JavaScript (Vanilla ES6+)
Vanilla JavaScript is used for enhancing user experience with dynamic interactions, without relying on a large frontend framework. Key functionalities are typically found within `<script>` tags in the HTML templates themselves or could be organized into separate `.js` files under `app/static/js/` (though not extensively used currently).

-   **DOM Manipulation**: Selecting elements (e.g., `document.getElementById`, `document.querySelector`), updating content (`.innerHTML`, `.textContent`), modifying styles and attributes.
-   **Event Handling**: Listening for user actions like clicks (`addEventListener`), form submissions (`submit` event), input changes (`input` or `change` event).
-   **AJAX (Asynchronous JavaScript and XML) using `fetch` API**:
    -   **Admin Panel**:
        -   Fetching lists of content (Kana, Kanji, Lessons, Categories, etc.) to populate HTML tables dynamically (e.g., on page load for `manage_kana.html`).
        -   Submitting form data from modals (for creating/updating content) to the respective API endpoints (e.g., `POST /api/admin/kana/new`) and handling JSON responses to update the UI or show messages.
        -   Triggering delete operations via API calls (e.g., `DELETE /api/admin/kana/<id>/delete`) and updating the UI upon success.
        -   Loading content options (e.g., existing Kanji from `/api/admin/content-options/kanji`) for the lesson builder dropdowns.
        -   **File Uploads**: Managing the file input, using `FormData` to send files to `/api/admin/upload-file`, and handling the server's response (e.g., getting the `dbPath` to store with lesson content).
        -   **Lesson Content Builder (`manage_lessons.html`)**: This is the most JavaScript-heavy part of the admin section. It involves:
            - Dynamically adding/removing/reordering content items and pages.
            - Showing different forms based on selected content type.
            - Configuring interactive quiz elements (questions, options, correct answers).
            - Saving all lesson structure changes via various API calls (e.g., `/api/admin/lessons/<id>/content/new`, `/api/admin/content/<id>/edit`, `/api/admin/lessons/<id>/pages/<num>/reorder`).
    -   **User-Facing Lesson Viewer (`lesson_view.html`)**:
        -   Managing navigation between lesson pages (e.g., updating the content displayed in a Bootstrap carousel or custom slider).
        -   Submitting quiz answers to `/api/lessons/<lesson_id>/quiz/<question_id>/answer` and displaying feedback/results.
        -   Sending lesson progress updates (e.g., marking a content item as complete by interacting with a checkbox/button that triggers a call to `/api/lessons/<lesson_id>/progress`).
-   **Modal Management**:
    -   Showing and hiding modal dialogs (primarily Bootstrap modals) for forms (e.g., "Add New Kana" modal in `manage_kana.html`) or confirmation dialogs (e.g., before deleting an item).
    -   Dynamically populating modal content, for example, loading data into an "Edit" form by fetching it from an API endpoint (e.g., `GET /api/admin/kana/<id>`).
-   **Dynamic Form Handling (especially in Lesson Builder)**:
    -   Showing or hiding specific form fields based on user selections (e.g., if "Interactive" content type is chosen, display fields for question type, text, options).
    -   Populating select dropdowns with data fetched from APIs (e.g., list of available Kanji to link in a lesson, fetched from `/api/admin/content-options/kanji`).
-   **CSRF Token Handling for AJAX**:
    -   For AJAX POST/PUT/DELETE requests that modify data and rely on session-based authentication, CSRF tokens are necessary. These are typically obtained from a hidden input field (rendered by Flask-WTF, often `{{ form.csrf_token }}` if a `CSRFTokenForm` is passed to the template, or from a specific meta tag) and included as a custom header (e.g., `X-CSRFToken`) in the `fetch` request.

**Example JavaScript Snippets (Conceptual - reflecting actual usage patterns):**

-   **Opening/Closing Bootstrap Modals**:
    ```javascript
    // Assuming 'editItemModal' is the ID of a Bootstrap modal element
    const editModalEl = document.getElementById('editItemModal');
    const editModal = new bootstrap.Modal(editModalEl);
    // To show:
    // editModal.show();
    // To hide:
    // editModal.hide();
    ```
-   **Fetching Content via AJAX (e.g., for an admin table)**:
    ```javascript
    async function loadTableData(apiUrl, tableBodyId) {
        try {
            const response = await fetch(apiUrl, { 
                headers: { 'X-Requested-With': 'XMLHttpRequest' } // Often used to indicate AJAX
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();
            const tableBody = document.getElementById(tableBodyId);
            tableBody.innerHTML = ''; // Clear existing rows
            data.forEach(item => {
                const row = tableBody.insertRow();
                // ... populate row cells with item data, add edit/delete buttons ...
            });
        } catch (error) {
            console.error('Error fetching table data:', error);
            // Display error to user
        }
    }
    ```
-   **Submitting JSON Data via AJAX (e.g., creating a new item from a modal)**:
    ```javascript
    // Assuming 'addItemForm' is the ID of the form in the modal
    document.getElementById('addItemForm').addEventListener('submit', async function(event) {
        event.preventDefault();
        const formData = new FormData(this);
        const itemData = Object.fromEntries(formData.entries());
        const csrfToken = formData.get('csrf_token'); // Assuming CSRF token is in the form
        
        try {
            const response = await fetch('/api/admin/items/new', { // Replace with actual API URL
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify(itemData)
            });
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }
            const result = await response.json();
            // ... handle success, e.g., close modal, refresh table ...
        } catch (error) {
            console.error('Error creating item:', error);
            // Display error to user in the modal
        }
    });
    ```

This frontend architecture allows for a responsive and interactive user experience, especially in the admin panel for content creation and in the user-facing lesson viewer for learning activities, while keeping the client-side codebase relatively simple by leveraging server-side rendering for the main page structures.

---

## File Structure & Organization

The project is organized into several key directories and files:

```
Japanese_Learning_Website/
├── app/                    # Main Flask application package
│   ├── __init__.py         # Application factory (create_app), initializes Flask app and extensions (db, login_manager, etc.)
│   ├── forms.py            # WTForms definitions for user registration, login, and other forms (e.g., CSRFTokenForm).
│   ├── models.py           # SQLAlchemy database models (User, Kana, Kanji, Lesson, LessonContent, etc.).
│   ├── routes.py           # Flask routes and view functions for both user-facing pages and API endpoints.
│   ├── static/             # Static files served directly to the client.
│   │   ├── css/            # Custom CSS files (e.g., custom.css).
│   │   ├── images/         # Static images used in the site's design (e.g., backgrounds, logos).
│   │   └── uploads/        # Default parent directory for user-uploaded files (UPLOAD_FOLDER).
│   │       ├── lessons/    # Subdirectory for lesson-specific uploads.
│   │       │   ├── image/  # Uploaded images for lessons.
│   │       │   ├── audio/  # Uploaded audio files for lessons.
│   │       │   └── document/ # Uploaded documents for lessons.
│   │       └── temp/       # Temporary directory for file uploads before processing and final placement.
│   ├── templates/          # Jinja2 templates for rendering HTML pages.
│   │   ├── admin/          # Templates specific to the admin panel.
│   │   │   ├── admin_index.html
│   │   │   ├── base_admin.html (Base layout for admin pages)
│   │   │   ├── login.html (Note: Admin login uses the main login.html)
│   │   │   ├── manage_categories.html
│   │   │   ├── manage_grammar.html
│   │   │   ├── manage_kana.html
│   │   │   ├── manage_kanji.html
│   │   │   ├── manage_lessons.html
│   │   │   └── manage_vocabulary.html
│   │   ├── base.html       # Base layout template for user-facing pages.
│   │   ├── index.html      # Homepage template.
│   │   ├── lesson_view.html # Template for viewing a single lesson.
│   │   ├── lessons.html    # Template for browsing all lessons.
│   │   ├── login.html      # User login page template.
│   │   └── register.html   # User registration page template.
│   └── utils.py            # Utility functions and classes (e.g., FileUploadHandler, convert_to_embed_url).
│
├── instance/               # Instance folder (not usually version-controlled).
│   ├── site.db             # SQLite database file (if using SQLite).
│   └── config.py           # Optional: Instance-specific configuration (not used if all config is in .env).
│
├── migrations/             # Flask-Migrate (Alembic) migration scripts.
│   ├── versions/           # Individual migration files.
│   ├── alembic.ini         # Alembic configuration.
│   └── env.py              # Alembic environment setup.
│
├── deprecated/             # Older or unused files, kept for historical reference.
│   ├── ADMIN_CONTENT_CREATION_GUIDE.md
│   ├── AGENTS.md
│   ├── README.md
│   ├── app_old_backup.py
│   ├── brainstorming.md
│   ├── legacy_templates/
│   └── redirect_old_admin.py
│
├── lesson_enhancement_plan/ # Planning documents for lesson system features.
│   └── (various .md files)
│
├── .env                    # Environment variables (SECRET_KEY, DATABASE_URL, UPLOAD_FOLDER, etc.). Not version-controlled.
├── .gitignore              # Specifies intentionally untracked files for Git.
├── ADMIN_CONTENT_CREATION_GUIDE.md # Guide for admins on creating various content types.
├── Documentation.md        # This main project documentation file.
├── README.md               # Project overview, setup instructions, and quick start guide.
├── UNIFIED_AUTH_README.md  # Specific documentation for the unified authentication system.
├── create_admin.py         # Script to create an initial admin user.
├── fix_content_order.py    # Utility script (purpose to be verified - likely for data migration/fixing).
├── inspect_db.py           # Utility script for inspecting the database.
├── lesson_models.py        # DEPRECATED: Models are now consolidated in app/models.py.
├── manual_migration.py     # Utility script (purpose to be verified).
├── migrate_database.py     # Utility script (purpose to be verified - potentially older migration helper).
├── migrate_file_fields.py  # Utility script for migrating file path data in DB.
├── migrate_interactive_system.py # Utility script for setting up interactive system tables.
├── migrate_lesson_system.py # Utility script for setting up/migrating lesson system tables.
├── migrate_page_numbers.py # Utility script for migrating page number data.
├── possible_next_steps.md  # Document outlining potential future development tasks.
├── requirements.txt        # Python package dependencies for pip.
├── run.py                  # Main script to run the Flask application and Flask-Migrate CLI commands.
├── run_migrations.py       # Utility script (purpose to be verified - likely for running specific migrations).
└── setup_unified_auth.py   # Script to set up initial database schema (potentially legacy or for specific auth setup).
```

**Key Directory Explanations:**

-   **`app/`**: The main application package.
    -   **`static/`**: Contains static assets like CSS, JavaScript (if any project-specific JS files are added), and images directly used by templates.
        -   **`static/uploads/`**: This is the crucial `UPLOAD_FOLDER` where user-uploaded content (lesson images, audio, documents) is stored. It's further organized by `lessons/<file_type>`. The application's `FileUploadHandler` manages writing to and `routes.uploaded_file` serves files from this directory.
    -   **`templates/`**: Contains all Jinja2 HTML templates. The `admin/` subdirectory holds templates for the admin interface.
-   **`instance/`**: Designed to hold instance-specific files that should not be version-controlled, such as the development database (`site.db`) or secret configuration files.
-   **`migrations/`**: Stores database migration scripts generated by Flask-Migrate (Alembic). This allows for version control of database schema changes.
-   **`deprecated/`**: Contains files that are no longer in active use but are kept for reference.
-   **`lesson_enhancement_plan/`**: Contains markdown files related to planning the lesson system enhancements.
-   **Root Directory**: Contains project-level files, configuration (`.env`), run scripts (`run.py`), documentation, and various utility/migration scripts. The presence of multiple migration-related Python scripts (`migrate_*.py`, `setup_unified_auth.py`) alongside Flask-Migrate suggests a history of different database setup approaches; current best practice relies on Flask-Migrate.

This structure promotes a clear separation of concerns, making the application easier to understand, maintain, and scale.

---

## Configuration Management

Application configuration is primarily managed through environment variables loaded from a `.env` file and default values set in `app/__init__.py` or `instance/config.py`.

### 1. Environment Variables (`.env` file)
A `.env` file in the project root is used to store sensitive and environment-specific configurations. This file should **not** be committed to version control. The `python-dotenv` package loads these variables into the environment when the application starts.

**Key Environment Variables:**

-   **`FLASK_APP=run.py`**: Specifies the entry point for the Flask CLI.
-   **`FLASK_ENV=development`**: Sets the Flask environment. Can be `development` or `production`.
    -   In `development` mode, `FLASK_DEBUG` is often implicitly or explicitly set to `True`, enabling the interactive debugger and auto-reloader.
-   **`FLASK_DEBUG=True`**: Enables/disables debug mode (set to `False` in production).
-   **`SECRET_KEY`**: A long, random string used for session signing, CSRF token generation, and other security-related cryptographic needs. **Crucial for security and must be kept secret.**
    -   Example: `SECRET_KEY=my-very-secret-and-long-random-string-123!@#`
-   **`DATABASE_URL`**: Specifies the connection string for the database.
    -   Example for SQLite: `DATABASE_URL=sqlite:///instance/site.db`
    -   Example for PostgreSQL: `DATABASE_URL=postgresql://user:password@host:port/dbname`
-   **`UPLOAD_FOLDER=app/static/uploads`**: The absolute or relative path to the directory where user-uploaded files (for lessons, etc.) will be stored. The application will attempt to create subdirectories within this folder (e.g., `lessons/image`, `lessons/audio`).
-   **`MAX_CONTENT_LENGTH=16777216`**: (Optional) Maximum allowed size for file uploads, in bytes (e.g., 16MB). This is a standard Flask configuration.

**Example `.env` file:**
```env
FLASK_APP=run.py
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-chosen-secret-key-should-be-long-and-random
DATABASE_URL=sqlite:///instance/site.db
UPLOAD_FOLDER=app/static/uploads
# MAX_CONTENT_LENGTH=16777216 # Optional: 16MB
```

### 2. Application Configuration (`app/__init__.py` and `instance/config.py`)

The Flask application factory (`create_app` in `app/__init__.py`) loads configurations.

-   **Default Configuration**: Base configurations are often set directly in `app/__init__.py` or a `config.py` file imported there.
    ```python
    # In app/__init__.py
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', os.path.join(app.root_path, 'static', 'uploads'))
    app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)) # Default 16MB

    # Configuration for allowed file extensions (example)
    app.config['ALLOWED_EXTENSIONS'] = {
        'image': {'png', 'jpg', 'jpeg', 'gif'},
        'audio': {'mp3', 'wav', 'ogg'},
        'document': {'pdf', 'doc', 'docx', 'txt'}
    }
    # Ensure UPLOAD_FOLDER and its subdirectories exist
    # (Code for this is typically in create_app() or FileUploadHandler)
    ```
-   **Instance Folder Configuration (`instance/config.py`)**:
    -   The `instance/` folder is outside the `app` package and can hold instance-specific configuration that should not be version-controlled (though `.env` is preferred for most secrets).
    -   Flask can be configured to load a `config.py` file from this folder if it exists: `app.config.from_pyfile('config.py', silent=True)`.
    -   The current project structure implies primary reliance on `.env` for overriding defaults, but `instance/config.py` could be used for more complex instance-specific settings if needed. The provided `Documentation.md` includes an example `instance/config.py` structure, but its actual usage in the current codebase needs to be verified against `app/__init__.py`.

### 3. Key Dependencies (`requirements.txt`)
The `requirements.txt` file lists all Python packages required for the project to run. Key packages influencing configuration and core functionality include:
-   `Flask`: The web framework itself.
-   `Flask-SQLAlchemy`: For database ORM.
-   `Flask-Login`: For user authentication and session management.
-   `Flask-WTF`: For web forms and CSRF protection.
-   `Flask-Migrate`: For database schema migrations.
-   `python-dotenv`: For loading `.env` files.
-   `Pillow`: For image processing in file uploads.
-   `python-magic`: For MIME type detection in file uploads.

Configuration values are accessed within the application using `current_app.config['CONFIG_KEY']`.

---

## Security Implementation

The application incorporates several security measures to protect user data, ensure authorized access, and prevent common web vulnerabilities.

### 1. Authentication Security
-   **Password Hashing**:
    -   User passwords are not stored in plaintext. Instead, they are hashed using `werkzeug.security.generate_password_hash`, which implements PBKDF2 with a salt.
    -   Password verification is done using `werkzeug.security.check_password_hash`.
    -   The `User.password_hash` field in the database stores these hashes (VARCHAR 256).
-   **Session Management**:
    -   Flask-Login is used for managing user sessions.
    -   Sessions are maintained using secure, cryptographically signed cookies. The application's `SECRET_KEY` (configured via environment variable) is crucial for this signing process.
    -   The "Remember Me" functionality allows for persistent sessions if selected by the user during login.
-   **Input Validation (Login/Registration)**:
    -   `LoginForm` and `RegistrationForm` in `app/forms.py` use WTForms validators (e.g., `DataRequired`, `Email`, `EqualTo`) to ensure that submitted data for login and registration meets basic format requirements before processing.
    -   Custom validators (`validate_username`, `validate_email` in `RegistrationForm`) check for uniqueness to prevent duplicate accounts.

### 2. Authorization Controls
-   **Role-Based Access Control (RBAC)**:
    -   The `User` model has an `is_admin` boolean field and a `subscription_level` string field ('free', 'premium').
    -   These attributes are used to control access to specific routes and features.
-   **Route Protection Decorators**:
    -   `@login_required` (from Flask-Login): Ensures that a route can only be accessed by authenticated users.
    -   `@admin_required` (custom decorator in `app/routes.py`): Restricts access to users where `current_user.is_admin` is `True`. Used for all admin panel pages and admin API endpoints.
    -   `@premium_required` (custom decorator in `app/routes.py`): Restricts access to users where `current_user.subscription_level` is 'premium'. Used for premium content/features.
-   **Admin-Only Areas**: The entire admin panel (routes starting with `/admin/` and APIs under `/api/admin/`) is protected by the `@admin_required` decorator.
-   **API Security**: Admin API endpoints require admin authentication. User-specific API endpoints (like lesson progress) require standard user authentication.

### 3. Data Protection
-   **SQL Injection Prevention**:
    -   The use of SQLAlchemy ORM for database interactions helps prevent SQL injection vulnerabilities, as queries are generally constructed using parameterized statements or object-relational mappings rather than raw SQL string concatenation.
-   **Cross-Site Scripting (XSS) Prevention**:
    -   Jinja2, the templating engine used by Flask, auto-escapes variables by default when rendering HTML. This significantly reduces the risk of XSS attacks from data displayed in templates.
    -   Content input by administrators (e.g., lesson text, grammar explanations) should be handled carefully if it's intended to include HTML. If rich text editing is allowed, it should be sanitized on the server-side before storage or display if not rendered through a trusted mechanism.
-   **Secure Headers**:
    -   While not explicitly detailed as custom-set in the provided codebase snippets, Flask and common deployment setups (like using Gunicorn with a reverse proxy like Nginx) often provide some default security headers (e.g., `X-Content-Type-Options`, `X-Frame-Options`). For production, explicitly setting headers like `Content-Security-Policy` (CSP), `Strict-Transport-Security` (HSTS), etc., is recommended.
-   **Environment Variables for Secrets**:
    -   Sensitive configurations like `SECRET_KEY` and `DATABASE_URL` (which might contain passwords) are managed using environment variables, typically loaded from a `.env` file (which is not version-controlled). This prevents hardcoding secrets into the codebase.

### 4. CSRF Protection
-   **Flask-WTF Integration**: The application uses Flask-WTF, which provides built-in Cross-Site Request Forgery (CSRF) protection for all forms created using it.
-   **Mechanism**:
    -   A unique CSRF token is generated for each user session.
    -   This token is embedded as a hidden field in forms (`{{ form.csrf_token }}` or `{{ form.hidden_tag() }}`).
    -   On form submission, Flask-WTF validates this token. If the token is missing or invalid, the request is rejected.
-   **Stateless Actions**: For POST requests that don't involve traditional forms but still modify state (e.g., `/upgrade_to_premium`, `/lessons/<id>/reset`), a `CSRFTokenForm` is used to ensure these actions are also protected.
-   **AJAX Requests**: For AJAX requests that modify data (POST, PUT, DELETE), if they rely on session cookie authentication, the CSRF token must be included in the request, typically as a custom header (e.g., `X-CSRFToken`). Client-side JavaScript is responsible for fetching this token from the page (e.g., from a meta tag or a hidden input in a main form) and adding it to AJAX requests.

### 5. File Upload Security (`FileUploadHandler` in `app/utils.py`)
The `FileUploadHandler` class implements several measures to secure file uploads:
-   **Extension Validation**: Uses a pre-defined list of allowed extensions per file type (`app.config['ALLOWED_EXTENSIONS']`) via `FileUploadHandler.allowed_file()`.
-   **MIME Type Validation**: Uses `python-magic` (`FileUploadHandler.validate_file_content()`) to verify the actual content type of the file against its extension, helping to prevent users from uploading malicious files disguised with a benign extension.
-   **Secure Filenames**: `werkzeug.utils.secure_filename` is used within `FileUploadHandler.generate_unique_filename()` to sanitize filenames, removing directory traversal characters (like `../`) and other potentially harmful characters. A UUID snippet is added to ensure uniqueness.
-   **Image Processing**: Uploaded images are processed using Pillow (`FileUploadHandler.process_image()`):
    -   They are converted to RGB (handling transparency by pasting on a white background).
    -   Resized if they exceed maximum dimensions.
    -   Re-saved (typically as JPEG) with optimization, which can help strip potentially malicious metadata or payloads from images.
-   **Storage Location**: Files are saved to a configured `UPLOAD_FOLDER`, and the serving route (`/uploads/<path:filename>`) includes checks to prevent access outside this designated folder.
-   **File Size Limits**: The `MAX_CONTENT_LENGTH` Flask configuration can be used to limit the maximum size of uploaded files, preventing denial-of-service attacks through overly large files.

### 6. General Best Practices Implemented
-   **Principle of Least Privilege**: User roles (free, premium, admin) ensure users only have access to the functionalities and data necessary for their role.
-   **Regular Updates**: Keeping dependencies (listed in `requirements.txt`) up-to-date is crucial for patching known vulnerabilities (developer responsibility).
-   **Debug Mode**: `FLASK_DEBUG=True` should only be used in development, as it can expose sensitive information if enabled in production.

This multi-layered approach to security aims to create a robust and resilient application.

---

## Development Workflow

### Local Development Setup
1. **Environment Preparation**
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

2. **Database Initialization**
   ```bash
   python setup_unified_auth.py
   python create_admin.py
   ```

3. **Development Server**
   ```bash
   python run.py
   # Server runs on http://localhost:5000
   ```

### Code Organization
- **Models** - Database schema in `app/models.py` (all models, including lesson system, are consolidated here).
- **Views** - Route handlers in `app/routes.py`.
- **Forms** - WTForms classes in `app/forms.py`.
- **Templates** - Jinja2 templates in `app/templates/`.
- **Static Files** - General project static assets (CSS, JavaScript) are primarily handled via Bootstrap CDN. The application uses an `UPLOAD_FOLDER` (defaulting to `app/static/uploads/`) for user-uploaded content, which is served via specific application routes. If custom non-uploaded static files are added, they would typically reside in a conventional `app/static/` directory and be configured accordingly.

### Database Management
```bash
# Create new migration
python migrate_database.py

# Reset database (development only)
rm instance/site.db
python setup_unified_auth.py

# Create admin user
python create_admin.py
```

### Testing Procedures
1. **Manual Testing**
   - User registration/login flow
   - Content creation/editing
   - Permission verification
   - Cross-browser compatibility

2. **API Testing**
   - Use browser developer tools
   - Test CRUD operations
   - Verify error handling
   - Check authentication

---

## Troubleshooting

### Common Issues

#### 1. Template Not Found Errors
```
jinja2.exceptions.TemplateNotFound: admin/admin_index.html
```
**Solution**: Ensure admin templates are in `app/templates/admin/`

#### 2. Route Building Errors
```
werkzeug.routing.exceptions.BuildError: Could not build url for endpoint 'list_kana'
```
**Solution**: Use correct route format `routes.list_kana` instead of `list_kana`

#### 3. Database Connection Issues
```
sqlite3.OperationalError: no such table: user
```
**Solution**: Run database setup script
```bash
python setup_unified_auth.py
```

#### 4. Admin Access Denied
**Problem**: Can't access admin panel after login
**Solution**: Verify admin user has `is_admin = True`
```bash
python create_admin.py
```

#### 5. Static Files Not Loading (If Applicable)
**Problem**: Custom CSS/JS files return 404.
**Solution**: 
    - For general site assets, ensure Bootstrap CDN links are correct if used. If using local custom CSS/JS (e.g., in a project `app/static/css` folder), ensure Flask static file configuration is correct (`static_folder='static'` in Flask app setup or blueprint, and `url_for('static', filename='path/to/file')` in templates). Verify file paths.
    - For user-uploaded files (e.g., images in lessons), ensure the `UPLOAD_FOLDER` is correctly configured and files are being served through the `/uploads/<path:filename>` route. Check that `LessonContent.file_path` stores the correct relative path to the file within `UPLOAD_FOLDER`.

### Debug Mode
Enable debug mode for detailed error messages:
```python
# In run.py or .env
FLASK_DEBUG=True
```

### Logging
Add logging for troubleshooting:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## Lesson System

### Overview
The lesson system provides a comprehensive way for administrators to create structured learning experiences that combine existing content (Kana, Kanji, Vocabulary, Grammar) with custom multimedia content. Users can browse, access, and track their progress through lessons based on their subscription level and completed prerequisites.

### Key Features

#### 1. Lesson Categories
- **Category Management** - Create and organize lessons into categories
- **Color Coding** - Visual categorization with custom colors
- **Category Filtering** - Users can filter lessons by category

#### 2. Lesson Types
- **Free Lessons** - Available to all logged-in users
- **Premium Lessons** - Restricted to premium subscribers
- **Access Control** - Automatic enforcement based on subscription level

#### 3. Prerequisites System
- **Lesson Dependencies** - Lessons can require completion of other lessons
- **Progressive Learning** - Ensures users follow a structured learning path
- **Access Validation** - Automatic checking of prerequisite completion

#### 4. Enhanced Content Builder with Paginated Structure
- **Visual Content Type Selector** - Intuitive card-based interface with 9 content types including interactive quizzes
- **Multi-step Wizard** - Step-by-step content creation process (Type Selection → Configuration → Preview → Save)
- **Dynamic Form Generation** - Forms adapt based on selected content type
- **Content Preview System** - Preview content before saving to lessons
- **Mixed Content Types** - Combine existing content with custom multimedia and interactive elements
- **Paginated Lesson Structure** - Organize lesson content into multiple pages for better learning flow
- **Page Management** - Create, edit, and delete individual pages within lessons
- **Content Ordering** - Specify the sequence of content within lessons and pages
- **Optional Content** - Mark content items as optional
- **Rich Media Support** - Text, images, videos, and audio content. Supports URL-based media. For direct file uploads (images, audio, documents): files are first uploaded via a dedicated mechanism (see `/api/admin/upload-file`), and then the returned file path is associated with a lesson content item. Uploaded files are stored on the server (typically in a subdirectory of `UPLOAD_FOLDER` like `app/static/uploads/lessons/images/`) and managed through the lesson builder.
- **Interactive Content** - Quiz questions with multiple choice, fill-in-the-blank, and true/false formats

##### Content Types Supported:
- **Existing Content**: Kana, Kanji, Vocabulary, Grammar (dropdown selection from database)
- **Custom Text**: Title and rich text content creation
- **URL-based Media**: Video (YouTube/Vimeo), Audio, and Image content via URLs.
- **File Uploads**: Upload of images, audio files, PDFs, or other documents. The process involves:
    1. Admin uploads a file using the file upload API endpoint.
    2. The system returns a `file_path` for the stored file.
    3. Admin then creates/edits a `LessonContent` item, associating it with this `file_path`.
    These files are served by the application and can be deleted (which also removes the physical file).

#### 5. Progress Tracking
- **Individual Progress** - Track completion of each content item
- **Overall Progress** - Calculate lesson completion percentage
- **Time Tracking** - Monitor time spent on lessons
- **Completion Status** - Mark lessons as completed

### Database Schema

#### Lesson Category Table
```sql
CREATE TABLE lesson_category (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    color_code VARCHAR(7) DEFAULT '#007bff',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Lesson Table
```sql
CREATE TABLE lesson (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    lesson_type VARCHAR(20) NOT NULL, -- 'free' or 'premium'
    category_id INTEGER,
    difficulty_level INTEGER, -- 1-5
    estimated_duration INTEGER, -- minutes
    order_index INTEGER DEFAULT 0,
    is_published BOOLEAN DEFAULT FALSE,
    thumbnail_url VARCHAR(255),
    video_intro_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES lesson_category (id)
    -- Note: SQLAlchemy relationships exist for:
    -- `content_items` (One-to-Many: Lesson -> LessonContent)
    -- `prerequisites` (One-to-Many: Lesson -> LessonPrerequisite, current lesson's prereqs)
    -- `required_by` (One-to-Many: Lesson -> LessonPrerequisite, lessons that require current lesson)
    -- `user_progress` (One-to-Many: Lesson -> UserLessonProgress)
    --
    -- Helper methods:
    -- `get_prerequisites()`: Returns a list of prerequisite Lesson objects.
    -- `is_accessible_to_user(user)`: Checks if the user can access the lesson based on subscription and prerequisites.
);
```

#### Lesson Prerequisites Table
```sql
CREATE TABLE lesson_prerequisite (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson_id INTEGER NOT NULL,          -- The lesson that has prerequisites
    prerequisite_lesson_id INTEGER NOT NULL, -- The lesson that must be completed first
    FOREIGN KEY (lesson_id) REFERENCES lesson (id) ON DELETE CASCADE,
    FOREIGN KEY (prerequisite_lesson_id) REFERENCES lesson (id) ON DELETE CASCADE,
    UNIQUE(lesson_id, prerequisite_lesson_id)
);
```

#### Lesson Content Table
```sql
CREATE TABLE lesson_content (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson_id INTEGER NOT NULL,
    content_type VARCHAR(20) NOT NULL, -- 'kana', 'kanji', 'vocabulary', 'grammar', 'text', 'image', 'video', 'audio'
    content_id INTEGER, -- ID of existing content (e.g., Kana.id), NULL for custom/multimedia
    title VARCHAR(200), -- For custom text, media titles
    content_text TEXT,  -- For custom text content
    media_url VARCHAR(255), -- URL for external media (YouTube, etc.)
    order_index INTEGER DEFAULT 0,
    is_optional BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- File-related fields for uploaded content
    file_path VARCHAR(500),      -- Relative path to the uploaded file (e.g., within UPLOAD_FOLDER)
    file_size INTEGER,           -- File size in bytes
    file_type VARCHAR(50),       -- MIME type of the file
    original_filename VARCHAR(255), -- Original name of the uploaded file
    -- Interactive content fields
    is_interactive BOOLEAN DEFAULT FALSE,
    max_attempts INTEGER DEFAULT 3,
    passing_score INTEGER DEFAULT 70, -- Percentage
    FOREIGN KEY (lesson_id) REFERENCES lesson (id) ON DELETE CASCADE
    -- Note: SQLAlchemy relationships exist for:
    -- `quiz_questions` (One-to-Many: LessonContent -> QuizQuestion)
    -- Note: SQLAlchemy helper methods:
    -- `get_file_url()`: Returns a serveable URL for the uploaded file or the media_url.
    -- `delete_file()`: Deletes the associated physical file if one exists.
    -- `get_content_data()`: Fetches the related content (e.g., Kana object) or a dict for custom content.
);
```

#### Quiz Question Table
```sql
CREATE TABLE quiz_question (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson_content_id INTEGER NOT NULL,
    question_type VARCHAR(50) NOT NULL, -- 'multiple_choice', 'fill_blank', 'true_false', 'matching'
    question_text TEXT NOT NULL,
    explanation TEXT, -- Explanation for the answer
    points INTEGER DEFAULT 1,
    order_index INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (lesson_content_id) REFERENCES lesson_content (id) ON DELETE CASCADE
    -- Note: SQLAlchemy relationships exist for:
    -- `options` (One-to-Many: QuizQuestion -> QuizOption)
    -- `user_answers` (One-to-Many: QuizQuestion -> UserQuizAnswer)
);
```

#### Quiz Option Table
```sql
CREATE TABLE quiz_option (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER NOT NULL,
    option_text TEXT NOT NULL,
    is_correct BOOLEAN DEFAULT FALSE,
    order_index INTEGER DEFAULT 0,
    feedback TEXT, -- Specific feedback for this option
    FOREIGN KEY (question_id) REFERENCES quiz_question (id) ON DELETE CASCADE
);
```

#### User Quiz Answer Table
```sql
CREATE TABLE user_quiz_answer (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    selected_option_id INTEGER,
    text_answer TEXT, -- For fill-in-the-blank questions
    is_correct BOOLEAN DEFAULT FALSE,
    answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    attempts INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES user (id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES quiz_question (id) ON DELETE CASCADE,
    FOREIGN KEY (selected_option_id) REFERENCES quiz_option (id),
    UNIQUE (user_id, question_id)
);
```

#### User Lesson Progress Table
```sql
CREATE TABLE user_lesson_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    lesson_id INTEGER NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    is_completed BOOLEAN DEFAULT FALSE,
    progress_percentage INTEGER DEFAULT 0, -- 0-100
    time_spent INTEGER DEFAULT 0, -- minutes
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    content_progress TEXT, -- JSON string mapping content_item_id to completion status (e.g., {"1": true, "2": false})
    FOREIGN KEY (user_id) REFERENCES user (id) ON DELETE CASCADE,
    FOREIGN KEY (lesson_id) REFERENCES lesson (id) ON DELETE CASCADE,
    UNIQUE(user_id, lesson_id)
    -- Note: SQLAlchemy helper methods:
    -- `get_content_progress()`: Parses `content_progress` JSON into a Python dict.
    -- `set_content_progress(dict)`: Serializes a Python dict to `content_progress` JSON.
    -- `mark_content_completed(content_id)`: Marks a specific content item as complete and updates overall progress.
    -- `update_progress_percentage()`: Recalculates `progress_percentage` based on completed content items.
);
```

### API Endpoints

#### Lesson Management (Admin)
```
GET    /api/admin/lessons                          # List all lessons
POST   /api/admin/lessons/new                      # Create new lesson
GET    /api/admin/lessons/<int:item_id>            # Get specific lesson
PUT    /api/admin/lessons/<int:item_id>/edit       # Update lesson (accepts PUT or PATCH)
DELETE /api/admin/lessons/<int:item_id>/delete     # Delete lesson
```

#### Category Management (Admin)
```
GET    /api/admin/categories                       # List all categories
POST   /api/admin/categories/new                   # Create new category
GET    /api/admin/categories/<int:item_id>         # Get specific category
PUT    /api/admin/categories/<int:item_id>/edit    # Update category (accepts PUT or PATCH)
DELETE /api/admin/categories/<int:item_id>/delete  # Delete category
```

#### Content Options API (Admin)
```
GET    /api/admin/content-options/<content_type>   # Get available content for lesson builder
                                                 # <content_type>: kana, kanji, vocabulary, grammar
```

#### Lesson Content Management (Admin)
```
GET    /api/admin/lessons/<int:lesson_id>/content                     # List lesson content
POST   /api/admin/lessons/<int:lesson_id>/content/new                 # Add content to lesson
DELETE /api/admin/lessons/<int:lesson_id>/content/<int:content_id>/delete # Remove content
```

#### User Lesson Access
```
GET    /api/lessons                    # Get accessible lessons for user
POST   /api/lessons/{id}/progress      # Update lesson progress
POST   /lessons/{id}/reset             # Reset lesson progress
```

#### File Management API (Admin)
```
POST   /api/admin/upload-file                 # Uploads a file to a subdirectory within the `UPLOAD_FOLDER` (e.g., `app/static/uploads/lessons/images/`).
                                              # Current Implementation Returns: JSON object including `filePath`.
                                              # The `filePath` returned is a URL generated by `url_for('static', filename=RELATIVE_PATH_WITHIN_STATIC)`,
                                              # e.g., `/static/uploads/lessons/images/filename.jpg` if `UPLOAD_FOLDER` is `app/static/uploads/`.
                                              # Note on Usage: For the `uploaded_file` serving route to function correctly, the path stored
                                              # in `LessonContent.file_path` should be relative to `UPLOAD_FOLDER` (e.g., `lessons/images/filename.jpg`).
                                              # The client-side JavaScript that calls `/api/admin/lessons/<id>/content/file` is responsible for
                                              # transforming the `filePath` from this endpoint into the correct relative path before submission.
DELETE /api/admin/delete-file                 # Delete an uploaded file from the server and potentially its LessonContent DB record.
                                              # Expects JSON body with 'file_path'. The 'file_path' should be the path relative to UPLOAD_FOLDER.
                                              # If 'content_id' is also provided and matches, the LessonContent record is deleted.
POST   /api/admin/lessons/<int:lesson_id>/content/file   # Add file-based content to a lesson.
                                              # Associates an *already uploaded file* with a lesson content item.
                                              # Expects 'file_path' in the JSON body to be the path relative to UPLOAD_FOLDER
                                              # (e.g., 'lessons/images/filename.jpg'). Takes other details like title, description.
```

#### Interactive Content (Quiz) API (Admin & User)
```
POST   /api/admin/lessons/<int:lesson_id>/content/interactive # Add interactive content (quiz question) to a lesson content item.
                                              # Creates a LessonContent of type 'interactive' and associated QuizQuestion/QuizOption records.
POST   /api/lessons/<int:lesson_id>/quiz/<int:question_id>/answer # User submits an answer to a quiz question.
                                              # Records the answer and returns correctness and feedback.
```

### Static File Serving
```
GET    /uploads/<path:filename>               # Serves uploaded files stored within the application's `UPLOAD_FOLDER`.
                                              # The `<path:filename>` part of the URL should be the path of the file
                                              # relative to the `UPLOAD_FOLDER`.
                                              # For example, if `UPLOAD_FOLDER` is 'app/static/uploads' and a file is stored as
                                              # 'app/static/uploads/lessons/images/my_image.png', then the URL would be
                                              # `/uploads/lessons/images/my_image.png`.
                                              # This route is used by `LessonContent.get_file_url()` to generate accessible URLs
                                              # for files whose relative paths are stored in `LessonContent.file_path`.
```
*Note on API Error Handling: Common HTTP status codes are used: 200 (OK), 201 (Created), 400 (Bad Request), 401 (Unauthorized), 403 (Forbidden), 404 (Not Found), 409 (Conflict), 500 (Internal Server Error).*

### User Interface

#### Admin Interface
- **Lesson Management** (`/admin/manage/lessons`) - Create, edit, and manage lessons
- **Category Management** (`/admin/manage/categories`) - Organize lesson categories
- **Content Builder** - Add and organize content within lessons
- **Publishing Controls** - Publish/unpublish lessons

#### User Interface
- **Lesson Browser** (`/lessons`) - Browse and filter available lessons
- **Lesson Viewer** (`/lessons/{id}`) - View lesson content in a paginated carousel format
- **Carousel Navigation** - Swipe-friendly page navigation with previous/next controls
- **Page Indicators** - Clear indication of current page and total pages
- **Progress Tracking** - Visual progress indicators and completion status
- **Reset Progress** - Users can reset their progress for a lesson
- **Non-Auto-Scrolling** - Manual navigation only, no automatic page transitions

### Migration and Setup

#### Database Migration
Run the lesson system migration script:
```bash
python migrate_lesson_system.py
```

This script will:
- Create all lesson-related database tables
- Add default lesson categories
- Create sample lessons for testing

#### Default Categories
The migration creates these default categories:
- Hiragana Basics
- Katakana Basics
- Essential Kanji
- Basic Vocabulary
- Grammar Fundamentals
- JLPT N5
- JLPT N4

## Future Enhancements

### Planned Features

#### 1. Enhanced Learning Tools
- **Spaced Repetition** - Intelligent review scheduling
- **Quiz System** - Interactive learning assessments
- **Audio Integration** - Native pronunciation support
- **Lesson Analytics** - Detailed learning analytics

#### 2. Content Improvements
- **Content Versioning** - Track content changes over time
- **Bulk Import/Export** - CSV/JSON content management
- **Advanced Prerequisites** - Complex prerequisite logic
- **Lesson Templates** - Reusable lesson structures

#### 3. User Experience
- **Mobile App** - Native iOS/Android applications
- **Offline Mode** - Download content for offline study
- **Dark Mode** - Alternative UI theme
- **Accessibility** - WCAG compliance improvements

#### 4. Administrative Features
- **User Management** - Admin user account controls
- **Analytics Dashboard** - Usage statistics and insights
- **Content Moderation** - Review and approval workflows
- **Backup/Restore** - Automated data backup systems

#### 5. Technical Improvements
- **API Documentation** - Swagger/OpenAPI integration
- **Automated Testing** - Unit and integration test suites
- **CI/CD Pipeline** - Automated deployment workflows
- **Performance Optimization** - Caching and database optimization

### Scalability Considerations
- **Database Migration** - PostgreSQL for production
- **Caching Layer** - Redis for session and content caching
- **CDN Integration** - Static asset delivery optimization
- **Load Balancing** - Multiple server instance support

### Integration Opportunities
- **External APIs** - Dictionary and translation services
- **Social Features** - User communities and sharing
- **Payment Processing** - Subscription billing automation
- **Email Services** - Automated notifications and newsletters

---

## Contributing

### Development Guidelines
1. **Code Style** - Follow PEP 8 Python style guide
2. **Documentation** - Update docs for new features
3. **Testing** - Include tests for new functionality
4. **Security** - Follow security best practices

### Pull Request Process
1. Fork the repository
2. Create feature branch
3. Implement changes with tests
4. Update documentation
5. Submit pull request

### Issue Reporting
- Use GitHub issues for bug reports
- Include detailed reproduction steps
- Provide environment information
- Attach relevant log files

---

## License & Support

### License
This project is licensed under the MIT License. See LICENSE file for details.

### Support
- **Documentation**: This file and related guides
- **Issues**: GitHub issue tracker
- **Community**: Project discussions and forums

### Acknowledgments
- Flask framework and community
- Bootstrap UI framework
- SQLAlchemy ORM
- All contributors and testers

---
