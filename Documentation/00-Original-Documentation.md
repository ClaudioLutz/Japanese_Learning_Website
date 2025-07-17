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
The Japanese Learning Website represents a sophisticated, full-stack educational platform designed to democratize Japanese language learning through technology. Built with modern web technologies and pedagogical best practices, it serves as both a learning management system and a comprehensive content delivery platform with advanced AI-powered features.

### Business Value Proposition
- **Scalable Education Platform**: Supports unlimited users with tiered subscription model (free/premium)
- **Content Management Excellence**: Comprehensive admin tools for educators and content creators
- **Progressive Learning Path**: Structured curriculum with prerequisite-based advancement and course organization
- **Multi-Modal Learning**: Combines traditional content with interactive multimedia experiences
- **Data-Driven Insights**: Built-in progress tracking and analytics capabilities
- **AI-Powered Content Generation**: Advanced AI services for lesson creation, image generation, and content validation
- **Guest Access Support**: Allows non-authenticated users to access selected free content
- **Export/Import System**: Complete lesson portability with ZIP packaging for content sharing

### Technical Excellence
- **Modern Architecture**: Flask-based microservice-ready design with clear separation of concerns
- **Security-First Approach**: Comprehensive authentication, authorization, CSRF protection, and data validation
- **Performance Optimized**: Efficient database design with relationship optimization and file handling
- **Maintainable Codebase**: Clean architecture with extensive documentation and migration tools
- **Deployment Ready**: Environment-agnostic configuration with production considerations
- **AI Integration**: OpenAI API integration for content generation and educational enhancement

### Key Metrics & Capabilities
- **Content Types**: 4 core Japanese learning content categories (Kana, Kanji, Vocabulary, Grammar)
- **User Management**: Role-based access control with subscription tiers and guest access
- **Lesson System**: Multi-page lessons with interactive quizzes, progress tracking, and multimedia support
- **Course System**: Organized lesson collections with progress tracking and structured learning paths
- **File Management**: Comprehensive upload system with validation, processing, and security
- **API Coverage**: 80+ RESTful endpoints for complete system control
- **Database Efficiency**: 15 optimized tables with proper indexing and relationships
- **AI-Powered Features**: Content generation, image creation, quiz generation, and adaptive learning
- **Interactive Elements**: Multiple quiz types (multiple choice, fill-in-blank, true/false, matching)

### Advanced Features
- **AI Content Generation**: Automated lesson content, explanations, and quiz creation
- **Image Generation**: AI-powered educational image creation using DALL-E
- **Lesson Export/Import**: Complete lesson packaging with files for content sharing
- **File Upload System**: Secure multimedia file handling with validation and processing
- **Progress Tracking**: Detailed user progress monitoring with completion tracking
- **Adaptive Quizzes**: AI-powered quiz generation with difficulty adjustment
- **Content Approval Workflow**: AI-generated content review and approval system

### Strategic Impact
This platform positions itself as a comprehensive solution for Japanese language education, combining the flexibility of modern web technologies with proven educational methodologies and cutting-edge AI capabilities. The system's architecture supports both immediate deployment and future scalability, making it suitable for individual educators, educational institutions, and commercial language learning services.

### Success Metrics
- User engagement through comprehensive progress tracking
- Content accessibility across subscription tiers with guest support
- Administrative efficiency through comprehensive management tools and AI assistance
- System reliability through robust error handling and security measures
- Scalability through modular architecture and optimized database design
- Content quality through AI-powered generation and validation systems

---

## Project Overview

### Purpose
A comprehensive web-based Japanese learning platform that provides structured lessons for learning Hiragana, Katakana, Kanji, vocabulary, and grammar. The platform features a tiered subscription model with free and premium content access.

### Key Features
- **Unified Authentication System:** Single, secure login for users and administrators with guest access support.
- **Subscription Management:** Supports Free and Premium content access tiers with upgrade/downgrade functionality.
- **Comprehensive Content Management System (CMS):** Full CRUD operations for Kana, Kanji, Vocabulary, and Grammar with AI-powered content generation.
- **Role-Based Access Control (RBAC):** Distinct permissions for student and administrator roles with CSRF protection.
- **Interactive Lesson System:** Multi-page lessons with multimedia, interactive quizzes (multiple choice, fill-in-the-blank, true/false, matching), and flexible content ordering.
- **Course Organization System:** Structured course collections with lesson groupings and progress tracking.
- **User Progress Tracking:** Comprehensive monitoring of lesson completion, quiz performance, and individual content progress.
- **AI-Powered Content Generation:** Advanced AI services for lesson content, explanations, quiz creation, and educational image generation.
- **Lesson Export/Import System:** Complete lesson portability with ZIP packaging for content sharing and backup.
- **File Upload System:** Secure multimedia file handling with validation, processing, and organized storage.
- **Guest Access Support:** Allows non-authenticated users to access selected free content.
- **Content Approval Workflow:** Review and approval system for AI-generated content.
- **Responsive Design:** Optimized experience across desktop, tablet, and mobile devices.

### Target Users

#### Students
- **Primary Users**: Individuals learning Japanese language
- **Access Levels**: Free and Premium subscription tiers
- **Features**: 
  - Browse and access lessons based on subscription level
  - Track learning progress through lessons
  - Interactive quiz participation
  - Prerequisite-based learning progression

#### Educators
- **Role**: Teachers managing Japanese learning content
- **Capabilities**:
  - Create and manage learning content (Kana, Kanji, Vocabulary, Grammar)
  - Design structured lessons with multimedia content
  - Organize content into categories and learning paths
  - Set lesson prerequisites and difficulty levels

#### Administrators
- **Role**: System managers overseeing platform operations
- **Full Access**: Complete administrative control
- **Responsibilities**:
  - User management and role assignment
  - Content moderation and publishing
  - System configuration and maintenance
  - Analytics and performance monitoring

### Core Learning Content Types

#### 1. Kana (Hiragana & Katakana)
- Character recognition and pronunciation
- Stroke order information
- Audio pronunciation examples
- Practice exercises and quizzes

#### 2. Kanji
- Character meanings and readings (On'yomi, Kun'yomi)
- JLPT level classification
- Stroke order and radical information
- Example usage in context

#### 3. Vocabulary
- Japanese words with readings and meanings
- JLPT level organization
- Example sentences in Japanese and English
- Audio pronunciation support

#### 4. Grammar
- Grammar rules and patterns
- Detailed explanations and structures
- Example sentences demonstrating usage
- JLPT level categorization

### System Capabilities

#### Content Management
- **CRUD Operations:** Full Create, Read, Update, Delete capabilities for all content types (Kana, Kanji, Vocabulary, Grammar).
- **Multimedia Support:** Integration of text, images, videos, and audio via URLs or direct file uploads with comprehensive validation.
- **File Upload System:** Secure handling, storage, and serving of uploaded media files with MIME type validation and image processing.
- **Content Validation:** Advanced validation for uploaded content including file type verification and security checks.
- **AI-Assisted Content Generation:** Comprehensive AI tools for generating lesson content, explanations, quizzes, and educational images.
- **Content Approval Workflow:** Review and approval system for AI-generated content with status tracking.
- **Bulk Operations:** Support for bulk content creation, editing, and deletion operations.
- **Export/Import System:** Complete lesson export to JSON/ZIP format with file packaging for content sharing.

#### Lesson System
- **Multi-Page Structure:** Lessons organized into pages with metadata support for titles and descriptions.
- **Flexible Content Ordering:** Drag-and-drop reordering of content within pages and across lesson structure.
- **Interactive Elements:** Multiple quiz types (multiple choice, fill-in-blank, true/false, matching) with adaptive scoring.
- **Progress Tracking:** Detailed monitoring of user progress through lessons, pages, and individual content items.
- **Prerequisites & Categories:** Define lesson dependencies and organize content into color-coded categories.
- **Course Organization:** Group lessons into structured courses with progress tracking and completion metrics.
- **Guest Access:** Configurable guest access for selected free content without authentication.

#### Quiz System
- **Multiple Question Types:** Support for multiple choice, fill-in-the-blank, true/false, and matching questions.
- **Adaptive Scoring:** Configurable attempts, passing scores, and progressive hints.
- **Detailed Feedback:** Question-specific explanations and option-level feedback.
- **Progress Integration:** Quiz results integrated with overall lesson progress tracking.
- **AI-Generated Questions:** Automated quiz creation with difficulty adjustment and variety.

#### User Experience
- **Responsive Design:** Optimized for seamless experience across desktop, tablet, and mobile devices.
- **Intuitive Navigation:** Clear pathways for lesson discovery, progression, and content interaction.
- **Progress Visualization:** Comprehensive indicators of lesson completion, quiz performance, and overall progress.
- **Guest Support:** Non-authenticated access to selected free content for trial and accessibility.
- **Subscription Management:** Easy upgrade/downgrade between free and premium tiers.

### Technical Architecture
- **Backend Framework:** Python with Flask.
- **Database & ORM:** SQLAlchemy with Flask-SQLAlchemy, using SQLite for development and Alembic for migrations. Production environments can use PostgreSQL/MySQL.
- **Frontend Technologies:** HTML5, CSS3, JavaScript (ES6+), Bootstrap 5.3.3.
- **Authentication:** Flask-Login for secure session management.
- **Forms:** Flask-WTF with CSRF protection.
- **File Handling:** Pillow for image processing, python-magic for file type identification.

### Deployment Flexibility
- **Development Environment:** Easy local setup using Python virtual environments and SQLite.
- **Production Readiness:** Designed for deployment on various platforms, with considerations for more robust databases like PostgreSQL or MySQL.
- **Configuration:** Managed via environment variables or configuration files.
- **Database Migrations:** Alembic for smooth schema evolution.

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

### Core Design Principles

#### 1. **Separation of Concerns**
- **Models (`app/models.py`)**: Define the data structure, relationships, and business logic directly related to data entities (e.g., User, Lesson, Kana). They interact with the ORM (SQLAlchemy).
- **Views (Templates - `app/templates/`)**: Handle the presentation logic. Jinja2 templates are used to render HTML dynamically based on data passed from controllers.
- **Controllers (Routes - `app/routes.py`)**: Manage the application flow. They handle incoming HTTP requests, interact with models to fetch or modify data, process input (often with the help of forms), and select appropriate templates to render or return JSON responses for API calls.
- **Forms (`app/forms.py`)**: Manage form data submission, validation (using WTForms and Flask-WTF), and CSRF protection.
- **Utilities (`app/utils.py`)**: Contain helper functions and classes that provide reusable logic across different parts of the application, such as `FileUploadHandler` for managing file uploads and `convert_to_embed_url` for YouTube URLs.
- **AI Services (`app/ai_services.py`)**: Encapsulate logic for interacting with external AI APIs (e.g., OpenAI) for features like content generation.
- **User Performance Analyzer (`app/user_performance_analyzer.py`)**: Analyzes user performance data to identify weaknesses and suggest remediation.
- **Content Validator (`app/content_validator.py`)**: Validates content accuracy, cultural context, and educational effectiveness.
- **Personalized Lesson Generator (`app/personalized_lesson_generator.py`)**: Generates adaptive lessons based on user performance analysis.
- **Lesson Template (`lesson_template.py`)**: Creates lessons from predefined JSON templates.
- **Multi-Modal Generator (`multi_modal_generator.py`)**: Generates visual and auditory content for lessons.
- **Lesson Export/Import (`app/lesson_export_import.py`)**: Handles the serialization and deserialization of lesson data for backup, transfer, or bulk creation purposes.

#### 2. **Single Responsibility Principle**
- Each Python module (e.g., `models.py`, `routes.py`, `forms.py`, `utils.py`, `ai_services.py`, `lesson_export_import.py`) has a distinct area of responsibility.
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
| **Flask-Migrate** | >=3.1.0                           | SQLAlchemy database migrations via Alembic    | Manages database schema changes over time using Alembic, allowing for versioning and incremental updates to the database structure.            |
| **Flask-Login**   | >=0.6.0                           | User session management, authentication       | Handles user login, logout, session tracking, and provides decorators like `@login_required`.                                                    |
| **Flask-WTF**     | >=1.0.0                           | Form handling, CSRF protection                | Integrates WTForms with Flask, providing easy form creation, validation, and crucial CSRF protection.                                          |
| **WTForms**       | >=3.0.0                           | Form creation and validation library          | Flexible library for defining form fields and validation rules.                                                                                |
| **Werkzeug**      | >=2.0.0                           | WSGI utility library (Flask dependency)       | Provides password hashing (`generate_password_hash`, `check_password_hash`), routing, and other WSGI utilities used by Flask.                    |
| **python-dotenv** | >=0.19.0                          | Environment variable management               | Loads environment variables from a `.env` file for configuration (e.g., `SECRET_KEY`, `DATABASE_URL`).                                       |
| **OpenAI**        | >=1.0.0                           | AI API Interaction                            | Used by `app/ai_services.py` to connect to OpenAI's API for comprehensive AI content generation, image creation, and educational enhancement.   |
| **requests**      | >=2.28.0                          | HTTP Requests                                 | Used for making HTTP requests, for example to download media files generated by AI services.                                                   |
| **email-validator**| >=2.0.0                          | Email validation                              | Validates email addresses in user registration and forms.                                                                                      |
| **gunicorn**      | Latest                            | WSGI HTTP Server                              | Production-ready Python WSGI HTTP Server for UNIX systems.                                                                                     |
| **psycopg2-binary**| >=2.9.0                          | PostgreSQL adapter                            | PostgreSQL database adapter for production deployments.                                                                                        |
| **pandas**        | >=1.3.0                           | Data analysis and manipulation                | Used for data processing and analysis in user performance tracking and content analytics.                                                      |

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
| **Alembic**       | Direct Usage    | Database schema migration tool              | Handles versioning of the database schema, allowing for controlled evolution of table structures. Integrated via `migrations/` directory.   |

### Design Choices & Justifications

### Backend Architecture
- **Monolithic Application**: Chosen for simplicity in development and deployment for the current scale. The structure (using Blueprints and an app factory) allows for potential future separation into microservices if needed.
- **Application Factory (`create_app`)**: Enhances testability and allows for multiple configurations (e.g., development, production, testing).
- **SQLAlchemy ORM**: Provides a high-level abstraction for database interactions, improving developer productivity and making it easier to switch database backends if necessary.
- **Flask-Login for Authentication**: Standard Flask extension for robust session-based authentication.
- **Flask-WTF for Forms & CSRF**: Ensures secure form handling and protects against Cross-Site Request Forgery attacks.

### Frontend Architecture
- **Server-Side Rendering with Jinja2**: Traditional approach suitable for content-heavy pages and simplifies initial development.
- **Vanilla JavaScript for Interactivity**: Keeps the frontend lightweight and avoids dependency on large JavaScript frameworks for current needs. AJAX is used for dynamic updates and API interactions.
- **Bootstrap for UI**: Accelerates frontend development with a responsive design and pre-styled components, ensuring a consistent look and feel.

### Database Design
- **Normalized Relational Schema**: Designed to reduce data redundancy and improve data integrity using foreign keys and relationships (primarily aiming for Third Normal Form - 3NF).
- **SQLite as Default**: Chosen for ease of setup and development. The use of SQLAlchemy allows for a straightforward migration to more robust databases like PostgreSQL or MySQL for production scaling.
- **Alembic for Migrations**: Ensures that database schema changes are version-controlled (via `migrations/` directory) and can be applied systematically across different environments using `run_migrations.py`.

### Security
- **Defense in Depth**: Multiple layers of security are employed:
    - Input validation (client-side via JS, server-side via WTForms and API checks).
    - CSRF protection on all state-changing form submissions.
    - Secure password hashing.
    - Role-Based Access Control (RBAC) for different user types.
    - Secure file handling (extension and content validation, secure filenames).
    - Auto-escaping in Jinja2 to prevent XSS.
- **Principle of Least Privilege**: Users and admins are granted only the permissions necessary for their roles.

### File Uploads (`FileUploadHandler`)
- **Centralized Logic**: All file upload operations (validation, processing, storage, metadata extraction) are handled by the `FileUploadHandler` class in `app/utils.py`, promoting code reuse and maintainability.
- **Security Focus**: Includes multiple validation steps (extension, MIME type), secure filename generation, and image processing to mitigate risks associated with user-uploaded files.
- **Organized Storage**: Files are stored in a structured way within the `UPLOAD_FOLDER` (e.g., `app/static/uploads/lessons/<file_type>/<filename>`), making them manageable and servable via a dedicated route.

### AI Services Integration
- **OpenAI API Integration**: Comprehensive integration with OpenAI's GPT-4.1 and DALL-E 3 models for content generation and image creation.
- **Content Generation**: Automated creation of lesson explanations, quiz questions, and educational content with proper romanization.
- **Image Generation**: AI-powered creation of educational images, lesson backgrounds, and visual content optimized for learning.
- **Content Approval Workflow**: Built-in review system for AI-generated content with approval/rejection capabilities.

### Lesson Export/Import System
- **JSON Export**: Complete lesson data export with structured JSON format including content, quizzes, and metadata.
- **ZIP Packaging**: Full lesson packages with associated files for easy sharing and backup.
- **Import Validation**: Comprehensive validation and duplicate handling during lesson import process.
- **File Management**: Automatic file handling during export/import operations with integrity checks.

### Course Management System
- **Structured Learning Paths**: Organization of lessons into courses with progress tracking and completion metrics.
- **Many-to-Many Relationships**: Flexible association between courses and lessons allowing for complex curriculum design.
- **Progress Analytics**: Detailed tracking of user progress through courses with completion percentages and time tracking.

## Technology Summary

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

## Production Considerations

### Database Migration
For production deployments, consider migrating from SQLite to:
- **PostgreSQL**: Recommended for high-concurrency applications
- **MySQL**: Alternative relational database option
- **Cloud Databases**: AWS RDS, Google Cloud SQL, Azure Database

### Performance Optimization
- **Caching**: Redis or Memcached for session and content caching
- **CDN**: Content Delivery Network for static assets
- **Load Balancing**: Multiple application instances
- **Database Optimization**: Indexing and query optimization

### Security Enhancements
- **HTTPS**: SSL/TLS encryption for all communications
- **Security Headers**: CSP, HSTS, X-Frame-Options
- **Rate Limiting**: API request throttling
- **Monitoring**: Application and security monitoring tools

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

#### 1. Clone the Repository
```bash
git clone <your-repository-url>
cd Japanese_Learning_Website
```
Replace `<your-repository-url>` with the actual URL of the Git repository.

#### 2. Create and Activate a Virtual Environment
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

#### 3. Install Dependencies
Install all required Python packages listed in `requirements.txt`.
```bash
pip install -r requirements.txt
```

#### 4. Environment Configuration (`.env` file)
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

#### 5. Database Initialization and Seeding
For a fresh setup, the project uses a sequence of Python scripts to initialize the database, create an admin user, and seed initial data.

##### a. Initial Database Setup and Admin Creation
This script prepares the database, creates all necessary tables based on the models defined in `app/models.py` (including tables for users, lessons, content, and AI features), and creates a default administrator account.
```bash
python setup_unified_auth.py
```
This will output the default admin credentials (typically `admin@example.com` / `admin123`).

##### b. Seed Initial Lesson Data & Apply Core Migrations
This script populates the database with default lesson categories (e.g., Hiragana Basics, Essential Kanji) and some sample lessons. It also includes necessary data migrations for features like content ordering, page numbers, and the interactive quiz system. This is crucial for having initial content and a correctly structured database.
```bash
python migrate_lesson_system.py
```

##### c. (Optional) Create Additional Admin Users
The `setup_unified_auth.py` script already creates a default admin user. If you need to create more admin users, or if you prefer a separate step for admin creation with specific credentials, you can use:
```bash
python create_admin.py
```
Follow the prompts to set the username, email, and password.

### 6. Run the Development Server
```bash
flask run
# Alternatively, you can use:
# python run.py
```
The application will typically be available at `http://127.0.0.1:5000/` or `http://localhost:5000/`.

### 7. Access the Application
-   **Main Site:** `http://localhost:5000/`
-   **Admin Panel:** `http://localhost:5000/admin` (Login with the admin credentials created by `setup_unified_auth.py` or `create_admin.py`).

## Default Admin Credentials
The `setup_unified_auth.py` script creates an admin user with the following default credentials:
-   **Email:** `admin@example.com`
-   **Password:** `admin123`
-   **Username:** `admin`

If you use `create_admin.py`, it will prompt you for credentials, defaulting to the same if you press Enter.

## Managing Database Migrations with Alembic (for Future Schema Changes)
The initial database schema is created by `setup_unified_auth.py` (`db.create_all()`). Subsequent changes to your database models in `app/models.py` require creating and applying migration scripts using Alembic. The `migrations/` directory and `run_migrations.py` script are configured for this.

**Important:**
- The `setup_unified_auth.py` script should ideally only be run once for a new database to create the initial tables.
- After the initial setup, all schema changes must be managed through Alembic migrations to avoid conflicts and ensure version control of your database structure. Do not run `db.create_all()` again on an existing database that is managed by Alembic.

When you modify your database models (e.g., add a new table, change a column in `app/models.py`):

### 1. Generate a new migration script
Use Alembic to automatically generate a revision script based on the changes detected in your models compared to the current database state (as tracked by Alembic).
```bash
alembic revision -m "Your descriptive message about the changes"
```
For example:
```bash
alembic revision -m "Add last_login_ip to User model"
```

### 2. Review and Edit the generated script
Alembic will create a new file in the `migrations/versions/` directory (e.g., `migrations/versions/xxxx_add_last_login_ip_to_user_model.py`).
- **Crucially, open this script and review it.** Alembic's autogenerate feature is powerful but may not always capture every nuance perfectly, especially for complex changes like constraints, data type changes on certain databases, or custom SQL.
- You might need to manually edit the `upgrade()` and `downgrade()` functions in the script to ensure they accurately reflect the desired schema changes. For example, you might need to add `op.create_index()`, handle data migrations if columns are being dropped or transformed, or specify server defaults.

### 3. Apply the migration to your database
This command applies all pending migrations (those in `migrations/versions/` that haven't been applied yet) to your database.
```bash
python run_migrations.py
```
This script executes `alembic upgrade head`.

### 4. Downgrade a migration (if needed)
To revert the last applied migration:
```bash
alembic downgrade -1
```
To downgrade to a specific migration version:
```bash
alembic downgrade <revision_hash_prefix>
```
**Caution:** Downgrading can be complex, especially if data loss is possible or if subsequent migrations depend on the one being reverted. Always back up your database before performing complex downgrade operations.

### Other useful Alembic commands
- **Show current revision:** `alembic current`
- **Show migration history:** `alembic history`
- **Show details of a revision:** `alembic show <revision>`
- **Stamp the database with a revision (without running migrations):** `alembic stamp head` (useful if migrations were applied manually or out-of-band)

## Troubleshooting Common Setup Issues

### Issue: `ModuleNotFoundError`
**Problem**: Missing Python packages
**Solution**: Ensure virtual environment is activated and run:
```bash
pip install -r requirements.txt
```

### Issue: Database connection errors
**Problem**: Database file doesn't exist, tables not created, or permissions issue.
**Solution**:
1.  Ensure the `instance` directory exists in the project root. If not, create it: `mkdir instance`.
2.  Run the database setup scripts in order:
    ```bash
    python setup_unified_auth.py
    python migrate_lesson_system.py
    ```
3.  Ensure you have write permissions to the `instance` directory and the `site.db` file within it.

### Issue: `SECRET_KEY` not set
**Problem**: Missing or invalid secret key
**Solution**: Ensure `.env` file exists with a proper `SECRET_KEY`:
```env
SECRET_KEY=your-very-long-random-secret-key-here
```

### Issue: File upload errors
**Problem**: Upload directory doesn't exist
**Solution**: Create the upload directory:
```bash
mkdir -p app/static/uploads/lessons/images
mkdir -p app/static/uploads/lessons/audio
mkdir -p app/static/uploads/lessons/documents
```

### Issue: Admin panel access denied
**Problem**: User doesn't have admin privileges
**Solution**: Run the admin creation script:
```bash
python create_admin.py
```

## Development Environment Verification

After setup, verify your installation by:

1. **Starting the development server**:
   ```bash
   flask run
   ```

2. **Accessing the main page**: Navigate to `http://localhost:5000`

3. **Testing admin access**: 
   - Go to `http://localhost:5000/admin`
   - Login with your admin credentials
   - Verify you can access the admin dashboard

4. **Testing user registration**:
   - Go to `http://localhost:5000/register`
   - Create a test user account
   - Login and verify basic functionality

## Next Steps

After successful installation:
1. Review the [System Architecture](03-System-Architecture.md) to understand the codebase.
2. Consult the [User Authentication](07-User-Authentication.md) document for details on auth flows and relevant API endpoints.
3. Explore existing documentation in the `Documentation/` directory for other components as they become available.
  <!--- Check the [API Design](11-API-Design.md) for available endpoints -->
  <!--- Explore the [Admin Content Management](08-Admin-Content-Management.md) features -->
  <!--- Read the [Development Workflow](15-Development-Workflow.md) for best practices -->

## Production Deployment Notes

For production deployment, remember to:
- Set `FLASK_ENV=production` and `FLASK_DEBUG=False`
- Use a strong, unique `SECRET_KEY`
- Configure a production database (PostgreSQL/MySQL)
- Set up proper file upload limits and security
- Configure HTTPS and security headers
- Set up monitoring and logging

---

## User Authentication System

The Japanese Learning Website employs a unified authentication system for both regular users and administrators, leveraging Flask-Login for session management and custom logic for role-based access control.

### Authentication Flow

#### 1. User Registration (`/register` route, `RegistrationForm`)
- New users provide a username, email, and password.
- The system checks for unique username and email (`User.validate_username`, `User.validate_email`).
- Passwords are securely hashed using `werkzeug.security.generate_password_hash` (PBKDF2) before being stored in the `user.password_hash` field.
- Upon successful registration, a new `User` record is created with `subscription_level` defaulting to 'free' and `is_admin` defaulting to `False`.

#### 2. User Login (`/login` route, `LoginForm`)
- Users log in with their email and password.
- The system retrieves the user by email and verifies the password using `user.check_password(password)`.
- If credentials are valid, `flask_login.login_user(user)` is called, establishing a secure session.
- A "Remember Me" option allows for persistent sessions.
- Upon successful login, users are redirected:
    - Administrators (`user.is_admin == True`) are redirected to the admin dashboard (`/admin`).
    - Regular users are redirected to the homepage (`/`) or their intended page (`next_page`).

#### 3. Session Management (Flask-Login)
- Flask-Login handles user sessions using secure cookies.
- The `@login_required` decorator protects routes that require an authenticated user.
- The `current_user` proxy from Flask-Login provides access to the logged-in user object in views and templates.
- A user loader function (`load_user(user_id)` in `app/models.py`) is registered with Flask-Login to reload the user object from the user ID stored in the session.

#### 4. Logout (`/logout` route)
- `flask_login.logout_user()` clears the user session and removes the user from being logged in.

#### 5. Role Assignment and Access Control
- **User Roles:**
    - `User.subscription_level`: Determines content access ('free' or 'premium').
    - `User.is_admin`: A boolean flag (`True`/`False`) grants administrative privileges.
- **Access Control Decorators (`app/routes.py`):**
    - `@login_required`: Ensures the user is logged in.
    - `@admin_required`: Ensures `current_user.is_admin` is `True`.
    - `@premium_required`: Ensures `current_user.subscription_level` is 'premium'. (Currently, subscription changes are simulated via prototype routes `/upgrade_to_premium` and `/downgrade_from_premium`).
- Content and feature access within routes and templates is further controlled by checking `current_user.is_admin` and `current_user.subscription_level`.

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

#### Password Hashing
- Werkzeug's `generate_password_hash` (PBKDF2 with salt) is used to securely store passwords.
- Password verification uses `check_password_hash` for secure comparison.
- Passwords are never stored in plaintext.

#### Session Cookies
- Flask-Login uses cryptographically signed cookies to maintain session integrity.
- The `SECRET_KEY` from the application configuration is crucial for this.
- Sessions can be configured for different lifetimes and security levels.

#### CSRF Protection
- Flask-WTF is integrated, providing CSRF protection for all form submissions.
- Standard forms (`RegistrationForm`, `LoginForm`) automatically include CSRF tokens.
- Actions like subscription changes (`/upgrade_to_premium`, `/downgrade_from_premium`) and lesson progress reset (`/lessons/<id>/reset`) use a `CSRFTokenForm` to ensure these POST requests are protected even without other form data.

#### Route Protection
- Decorators (`@login_required`, `@admin_required`, `@premium_required`) prevent unauthorized access to routes.
- Custom decorators provide fine-grained access control based on user attributes.

### Authentication Implementation Details

#### User Model (`app/models.py`)
The `User` model includes fields for authentication and role management.
```python
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False) # Increased length for stronger hash algorithms
    subscription_level = db.Column(db.String(50), default='free', nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    # ... other fields like progress, etc. ...
    
    def set_password(self, password):
        """Hash and set the user's password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches the hash."""
        return check_password_hash(self.password_hash, password)

# User Loader for Flask-Login (typically in app/models.py or app/__init__.py)
# This function is registered with the LoginManager instance.
# from . import login_manager # Assuming login_manager is initialized in app/__init__.py
# @login_manager.user_loader
# def load_user(user_id):
#     return User.query.get(int(user_id))
```
**Note on `load_user`**: The `load_user` function is essential for Flask-Login. It's typically defined at the module level (e.g., in `app/models.py` or where your `LoginManager` is initialized) and decorated with `@login_manager.user_loader`. It should not be a static method of the `User` class itself if it's to be registered directly with Flask-Login this way. The snippet above shows the typical structure.

#### Access Control Decorators
```python
def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access required.', 'error')
            return redirect(url_for('routes.login'))
        return f(*args, **kwargs)
    return decorated_function

def premium_required(f):
    """Decorator to require premium subscription"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('routes.login'))
        if current_user.subscription_level != 'premium':
            flash('Premium subscription required.', 'error')
            return redirect(url_for('routes.upgrade_to_premium'))
        return f(*args, **kwargs)
    return decorated_function
```

#### Form Validation
```python
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(), 
        Length(min=4, max=20)
    ])
    email = StringField('Email', validators=[
        DataRequired(), 
        Email()
    ])
    password = PasswordField('Password', validators=[
        DataRequired(), 
        Length(min=6)
    ])
    password2 = PasswordField('Repeat Password', validators=[
        DataRequired(), 
        EqualTo('password')
    ])
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Username already exists.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Email already registered.')
```

### Session Management

#### Session Configuration
- **Session Lifetime**: Configurable session timeout
- **Remember Me**: Optional persistent sessions
- **Security**: Secure cookie flags in production
- **Cross-Site Protection**: SameSite cookie attributes

#### Session Security
```python
# Production session configuration
app.config.update(
    SESSION_COOKIE_SECURE=True,      # HTTPS only
    SESSION_COOKIE_HTTPONLY=True,    # No JavaScript access
    SESSION_COOKIE_SAMESITE='Lax',   # CSRF protection
    PERMANENT_SESSION_LIFETIME=timedelta(hours=24)
)
```

### User Management Features

#### Account Creation
- Email validation and uniqueness checking
- Username validation and uniqueness checking
- Password strength requirements
- Automatic role assignment (default: free user)

#### Profile Management
- Users can update their profile information
- Password change functionality
- Email verification (future enhancement)
- Account deletion (future enhancement)

#### Subscription Management
- Upgrade to premium subscription
- Downgrade to free subscription
- Subscription status tracking
- Access level enforcement

### Unified Login Flow
The system utilizes a single login point for all users (standard users and administrators) via the `/login` route. After successful authentication, users are redirected based on their role:
- Administrators (`user.is_admin == True`) are directed to the admin dashboard (`/admin`).
- Regular users are directed to the main homepage (`/`) or their originally intended page.

### Authentication API Endpoints

#### User-Facing Authentication Endpoints
These endpoints are primarily for user session management:
- `GET /login` - Display login form.
- `POST /login` - Process login credentials.
- `GET /register` - Display registration form.
- `POST /register` - Process user registration.
- `GET /logout` - Log out current user.

#### User Subscription Endpoints (Protected)
These endpoints require user login:
- `POST /upgrade_to_premium` - Allows a logged-in user to upgrade their subscription to 'premium'.
- `POST /downgrade_from_premium` - Allows a logged-in user to downgrade their subscription to 'free'.

#### Admin API Endpoints (Admin Only)
These RESTful API endpoints are for content management and require administrator privileges (`@admin_required`). They are typically accessed by the admin frontend or other administrative tools.

##### Kana Management (`/api/admin/kana`)
- `GET /api/admin/kana` - List all Kana characters.
- `POST /api/admin/kana/new` - Create a new Kana character.
- `GET /api/admin/kana/<id>` - Retrieve a specific Kana character by ID.
- `PUT /api/admin/kana/<id>/edit` - Update a specific Kana character.
- `DELETE /api/admin/kana/<id>/delete` - Delete a specific Kana character.

##### Kanji Management (`/api/admin/kanji`)
- `GET /api/admin/kanji` - List all Kanji characters.
- `POST /api/admin/kanji/new` - Create a new Kanji character.
- `GET /api/admin/kanji/<id>` - Retrieve a specific Kanji character by ID.
- `PUT /api/admin/kanji/<id>/edit` - Update a specific Kanji character.
- `DELETE /api/admin/kanji/<id>/delete` - Delete a specific Kanji character.

##### Vocabulary Management (`/api/admin/vocabulary`)
- `GET /api/admin/vocabulary` - List all vocabulary items.
- `POST /api/admin/vocabulary/new` - Create a new vocabulary item.
- `GET /api/admin/vocabulary/<id>` - Retrieve a specific vocabulary item by ID.
- `PUT /api/admin/vocabulary/<id>/edit` - Update a specific vocabulary item.
- `DELETE /api/admin/vocabulary/<id>/delete` - Delete a specific vocabulary item.

##### Grammar Management (`/api/admin/grammar`)
- `GET /api/admin/grammar` - List all grammar points.
- `POST /api/admin/grammar/new` - Create a new grammar point.
- `GET /api/admin/grammar/<id>` - Retrieve a specific grammar point by ID.
- `PUT /api/admin/grammar/<id>/edit` - Update a specific grammar point.
- `DELETE /api/admin/grammar/<id>/delete` - Delete a specific grammar point.

### Historical Context: Migration from Dual System
Previously, the platform had separate authentication mechanisms for users and administrators. This has been consolidated into the current single, role-based system where all authentication is managed by Flask-Login, and access control is determined by user roles (specifically the `is_admin` flag and `subscription_level`). This unified approach simplifies user management and enhances security by eliminating hardcoded admin credentials.

### Security Best Practices

#### Password Security
- Minimum password length requirements
- Password hashing with salt
- Protection against timing attacks
- Password change functionality

#### Session Security
- Secure session cookie configuration
- Session timeout management
- Protection against session fixation
- CSRF token validation

#### Access Control
- Role-based access control (RBAC)
- Principle of least privilege
- Route-level protection
- Template-level access control

### Future Enhancements

#### Planned Authentication Features
- **Two-Factor Authentication**: SMS or app-based 2FA
- **Social Login**: OAuth integration (Google, Facebook)
- **Email Verification**: Account activation via email
- **Password Reset**: Secure password recovery
- **Account Lockout**: Protection against brute force attacks
- **Audit Logging**: Track authentication events
- **Advanced Roles**: More granular permission system

#### Security Improvements
- **Rate Limiting**: Login attempt throttling
- **IP Whitelisting**: Admin access restrictions
- **Device Management**: Trusted device tracking
- **Session Analytics**: Login pattern analysis

---

## Admin Content Management

### 1. Overview

The Japanese Learning Website provides a comprehensive Admin Panel for managing all aspects of the learning content. Administrators can perform Create, Read, Update, and Delete (CRUD) operations on various content types, organize lessons, and manage learning pathways.

The Admin Panel is typically accessible via the `/admin` route after an administrator logs in.

### 2. Accessing the Admin Panel

1.  Navigate to the website's login page (e.g., `/login`).
2.  Log in using an account with administrator privileges (`is_admin=True`).
3.  Upon successful login, administrators are usually redirected to the Admin Dashboard (`/admin` or `/admin/dashboard`).
    - If not redirected automatically, navigate manually to `/admin`.

Access to all admin functionalities is protected by the `@admin_required` decorator, ensuring only authorized users can make changes.

### 3. Core Content Management Sections

The Admin Panel is typically organized into sections for managing different types of content:

#### 3.1. Managing Kana (Hiragana & Katakana)

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

#### 3.2. Managing Kanji

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

#### 3.3. Managing Vocabulary

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

#### 3.4. Managing Grammar

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

### 4. Lesson Organization and Management

#### 4.1. Managing Lesson Categories

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

#### 4.2. Managing Lessons

This is a central part of the admin panel.

-   **View Lessons**: Lists all lessons, possibly filterable by category. Shows title, category, type (free/premium), published status.
-   **Create New Lesson**:
    -   Initial fields: Title, Description, Lesson Type (Free/Premium), Category, Difficulty Level, Estimated Duration, Order Index, Thumbnail URL, Video Intro URL.
    -   After creation, the admin can add content to pages within the lesson.
-   **Edit Lesson Settings**: Modify the metadata of an existing lesson (fields listed above).
-   **Publish/Unpublish Lesson**: Toggle the `is_published` status.
-   **Delete Lesson**: Remove an entire lesson, including its pages and content. This is a destructive action.
-   **Manage Lesson Prerequisites**: Interface to select other lessons that must be completed before starting the current lesson.

##### 4.2.1. Managing Lesson Pages and Content

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

##### 4.2.2. Managing Interactive Quiz Content (within a Lesson Content item)

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

### 5. File Upload Management

-   Integrated into the lesson content creation process for images, audio, and video files.
-   Utilizes `FileUploadHandler` (from `app/utils.py`) for:
    -   Validation (allowed extensions, MIME types via `python-magic`).
    -   Secure filename generation.
    -   Image processing (resizing, optimization via Pillow).
    -   Storage in the configured `UPLOAD_FOLDER` (e.g., `app/static/uploads/lessons/<file_type>/`).
-   An API endpoint like `POST /api/admin/upload-file` likely handles asynchronous file uploads, returning a path to be associated with the lesson content item.

### 6. User Management (Potential Future Area)

While not explicitly detailed as fully implemented in existing admin routes, typical admin user management features would include:
-   **View Users**: List all registered users.
-   **Edit User Details**: Modify user's username, email (with caution), subscription level, admin status.
-   **Delete User**: Remove a user account.
-   **Impersonate User**: (Advanced, for troubleshooting) Log in as a specific user.

### 7. Admin Dashboard

The main landing page for the admin panel (`/admin`) typically provides:
-   Summary statistics (e.g., number of users, lessons, content items).
-   Quick links to common management sections.
-   Recent activity or notifications.

### 8. UI/UX Considerations

-   **Clear Navigation**: Easy-to-understand menu structure.
-   **Intuitive Forms**: Well-labeled fields and clear instructions for adding/editing content.
-   **Feedback Mechanisms**: Success and error messages for operations.
-   **Responsive Design**: Usable on various screen sizes, though primarily desktop-focused for admin tasks.
-   **Confirmation Dialogs**: For destructive actions like deletion.

This document provides a general overview. Specific implementation details for forms, tables, and workflows would be visible in the admin panel's HTML templates (e.g., `app/templates/admin/manage_lessons.html`) and corresponding JavaScript files.

---

## Database Schema

### 1. Introduction

The Japanese Learning Website utilizes a relational database managed by SQLAlchemy ORM. The schema is designed to support user management, content organization (Kana, Kanji, Vocabulary, Grammar), a comprehensive lesson system with progress tracking, and interactive quiz functionalities. Database migrations are handled by Alembic.

This document outlines the structure of each table (model) in the database.

### 2. Core Models

#### 2.1. `User`

Stores information about registered users, including authentication details, subscription level, and admin status.

| Column             | Type          | Constraints                                  | Description                                                                 |
|--------------------|---------------|----------------------------------------------|-----------------------------------------------------------------------------|
| `id`               | Integer       | Primary Key                                  | Unique identifier for the user.                                             |
| `username`         | String(80)    | Unique, Not Nullable                         | User's chosen username.                                                     |
| `email`            | String(120)   | Unique, Not Nullable                         | User's email address, used for login.                                       |
| `password_hash`    | String(256)   | Not Nullable                                 | Hashed password for secure authentication.                                  |
| `subscription_level`| String(50)    | Default: 'free'                              | User's subscription tier (e.g., 'free', 'premium').                           |
| `is_admin`         | Boolean       | Not Nullable, Default: False                 | Flag indicating if the user has administrative privileges.                  |

**Relationships:**
- `lesson_progress`: One-to-Many with `UserLessonProgress`. Each user can have progress records for multiple lessons.

---

#### 2.2. `Kana`

Stores individual Hiragana and Katakana characters.

| Column              | Type        | Constraints                                  | Description                                                              |
|---------------------|-------------|----------------------------------------------|--------------------------------------------------------------------------|
| `id`                | Integer     | Primary Key                                  | Unique identifier for the Kana character.                                |
| `character`         | String(5)   | Not Nullable, Unique                         | The Kana character itself (e.g., "あ", "カ").                               |
| `romanization`      | String(10)  | Not Nullable                                 | Romanized representation (e.g., "a", "ka").                              |
| `type`              | String(10)  | Not Nullable                                 | Type of Kana: 'hiragana' or 'katakana'.                                  |
| `stroke_order_info` | String(255) | Nullable                                     | Information or link to stroke order diagram/animation.                   |
| `example_sound_url` | String(255) | Nullable                                     | URL to an audio file demonstrating pronunciation.                        |

---

#### 2.3. `Kanji`

Stores individual Kanji characters with their meanings, readings, and other relevant information.

| Column              | Type        | Constraints                                  | Description                                                              |
|---------------------|-------------|----------------------------------------------|--------------------------------------------------------------------------|
| `id`                | Integer     | Primary Key                                  | Unique identifier for the Kanji character.                               |
| `character`         | String(5)   | Not Nullable, Unique                         | The Kanji character itself (e.g., "日", "本").                               |
| `meaning`           | Text        | Not Nullable                                 | English meaning(s) of the Kanji.                                         |
| `onyomi`            | String(100) | Nullable                                     | On'yomi (Chinese reading) of the Kanji.                                  |
| `kunyomi`           | String(100) | Nullable                                     | Kun'yomi (Japanese reading) of the Kanji.                                |
| `jlpt_level`        | Integer     | Nullable                                     | JLPT level associated with the Kanji (e.g., 5 for N5, 1 for N1).         |
| `stroke_order_info` | String(255) | Nullable                                     | Information or link to stroke order diagram/animation.                   |
| `radical`           | String(10)  | Nullable                                     | The main radical of the Kanji.                                           |
| `stroke_count`      | Integer     | Nullable                                     | Number of strokes in the Kanji.                                          |
| `status`            | String(20)  | Not Nullable, Default: 'approved'            | Approval status: 'approved' or 'pending_approval'.                       |
| `created_by_ai`     | Boolean     | Not Nullable, Default: False                 | Flag indicating if the entry was generated by AI.                        |

---

#### 2.4. `Vocabulary`

Stores vocabulary words, including readings, meanings, and example sentences.

| Column                      | Type        | Constraints                                  | Description                                                              |
|-----------------------------|-------------|----------------------------------------------|--------------------------------------------------------------------------|
| `id`                        | Integer     | Primary Key                                  | Unique identifier for the vocabulary item.                               |
| `word`                      | String(100) | Not Nullable, Unique                         | The vocabulary word in Japanese (e.g., "猫", "食べる").                      |
| `reading`                   | String(100) | Not Nullable                                 | Hiragana/Katakana reading of the word (e.g., "ねこ", "たべる").              |
| `meaning`                   | Text        | Not Nullable                                 | English meaning(s) of the word.                                          |
| `jlpt_level`                | Integer     | Nullable                                     | JLPT level associated with the vocabulary.                               |
| `example_sentence_japanese` | Text        | Nullable                                     | Example sentence in Japanese using the word.                             |
| `example_sentence_english`  | Text        | Nullable                                     | English translation of the example sentence.                             |
| `audio_url`                 | String(255) | Nullable                                     | URL to an audio file for the word's pronunciation.                       |
| `status`                    | String(20)  | Not Nullable, Default: 'approved'            | Approval status: 'approved' or 'pending_approval'.                       |
| `created_by_ai`             | Boolean     | Not Nullable, Default: False                 | Flag indicating if the entry was generated by AI.                        |

---

#### 2.5. `Grammar`

Stores grammar points, explanations, and example structures.

| Column            | Type        | Constraints                                  | Description                                                                 |
|-------------------|-------------|----------------------------------------------|-----------------------------------------------------------------------------|
| `id`              | Integer     | Primary Key                                  | Unique identifier for the grammar point.                                    |
| `title`           | String(200) | Not Nullable, Unique                         | Title of the grammar point (e.g., "Usage of Particle は").                  |
| `explanation`     | Text        | Not Nullable                                 | Detailed explanation of the grammar rule.                                   |
| `structure`       | String(255) | Nullable                                     | Common structure or pattern for the grammar point (e.g., "Noun + は..."). |
| `jlpt_level`      | Integer     | Nullable                                     | JLPT level associated with the grammar point.                               |
| `example_sentences`| Text        | Nullable                                     | Example sentences demonstrating the grammar point (could be JSON/CSV text). |
| `status`            | String(20)  | Not Nullable, Default: 'approved'            | Approval status: 'approved' or 'pending_approval'.                       |
| `created_by_ai`     | Boolean     | Not Nullable, Default: False                 | Flag indicating if the entry was generated by AI.                        |

---

### 3. Lesson System Models

#### 3.1. `LessonCategory`

Defines categories for organizing lessons.

| Column      | Type        | Constraints                               | Description                                                        |
|-------------|-------------|-------------------------------------------|--------------------------------------------------------------------|
| `id`        | Integer     | Primary Key                               | Unique identifier for the lesson category.                         |
| `name`      | String(100) | Not Nullable, Unique                      | Name of the category (e.g., "Hiragana Basics", "Kanji N5").        |
| `description`| Text        | Nullable                                  | A brief description of the category.                               |
| `color_code`| String(7)   | Default: '#007bff'                        | Hex color code for UI representation of the category.              |
| `created_at`| DateTime    | Default: `datetime.utcnow`                | Timestamp of when the category was created.                        |

**Relationships:**
- `lessons`: One-to-Many with `Lesson`. Each category can have multiple lessons.

---

#### 3.2. `Lesson`

Represents a single lesson, containing various content items and metadata.

| Column               | Type        | Constraints                                     | Description                                                               |
|----------------------|-------------|-------------------------------------------------|---------------------------------------------------------------------------|
| `id`                 | Integer     | Primary Key                                     | Unique identifier for the lesson.                                         |
| `title`              | String(200) | Not Nullable                                    | Title of the lesson.                                                      |
| `description`        | Text        | Nullable                                        | A brief description of the lesson.                                        |
| `lesson_type`        | String(20)  | Not Nullable                                    | Type of lesson: 'free' or 'premium'.                                      |
| `category_id`        | Integer     | Foreign Key (`lesson_category.id`), Nullable   | ID of the `LessonCategory` this lesson belongs to.                        |
| `difficulty_level`   | Integer     | Nullable                                        | Difficulty rating (e.g., 1-5).                                            |
| `estimated_duration` | Integer     | Nullable                                        | Estimated time to complete the lesson in minutes.                         |
| `order_index`        | Integer     | Default: 0                                      | Order of the lesson within its category or overall list.                  |
| `is_published`       | Boolean     | Default: False                                  | Flag indicating if the lesson is visible to users.                        |
| `allow_guest_access` | Boolean     | Not Nullable, Default: False                    | Flag indicating if guests can access this lesson without authentication.  |
| `instruction_language`| String(10)  | Not Nullable, Default: 'english'              | Language for explanations/instructions (e.g., 'english', 'german').       |
| `thumbnail_url`      | String(255) | Nullable                                        | URL for a lesson cover image.                                             |
| `background_image_url`| String(255) | Nullable                                       | URL for a lesson background image.                                        |
| `background_image_path`| String(500) | Nullable                                      | File path for uploaded background image.                                  |
| `video_intro_url`    | String(255) | Nullable                                        | URL for an optional introductory video for the lesson.                    |
| `created_at`         | DateTime    | Default: `datetime.utcnow`                      | Timestamp of when the lesson was created.                                 |
| `updated_at`         | DateTime    | Default: `datetime.utcnow`, OnUpdate: `datetime.utcnow` | Timestamp of the last update.                                       |

**Relationships:**
- `category`: Many-to-One with `LessonCategory`.
- `content_items`: One-to-Many with `LessonContent`. A lesson can have multiple content items.
- `prerequisites`: One-to-Many with `LessonPrerequisite` (identifies lessons that must be completed before this one).
- `required_by`: One-to-Many with `LessonPrerequisite` (identifies lessons that have this lesson as a prerequisite).
- `user_progress`: One-to-Many with `UserLessonProgress`. Tracks progress for multiple users on this lesson.
- `pages_metadata`: One-to-Many with `LessonPage`. Stores metadata for each page within the lesson.
- `courses`: Many-to-Many with `Course` through `course_lessons` association table.

---

#### 3.3. `LessonPrerequisite`

Defines prerequisite relationships between lessons (join table for a self-referential many-to-many on `Lesson`).

| Column                 | Type    | Constraints                                                              | Description                                                        |
|------------------------|---------|--------------------------------------------------------------------------|--------------------------------------------------------------------|
| `id`                   | Integer | Primary Key                                                              | Unique identifier for the prerequisite relationship.               |
| `lesson_id`            | Integer | Foreign Key (`lesson.id`), Not Nullable                                  | ID of the lesson that has a prerequisite.                          |
| `prerequisite_lesson_id`| Integer | Foreign Key (`lesson.id`), Not Nullable                                  | ID of the lesson that must be completed first.                     |
|                        |         | Unique Constraint (`lesson_id`, `prerequisite_lesson_id`)                  | Ensures a prerequisite is not duplicated for the same lesson.    |

**Relationships:**
- `lesson`: Many-to-One with `Lesson` (the lesson that has prerequisites).
- `prerequisite_lesson`: Many-to-One with `Lesson` (the lesson that is a prerequisite).

---

#### 3.4. `LessonPage`

Stores metadata for individual pages within a lesson, allowing for titles and descriptions per page.

| Column        | Type        | Constraints                                           | Description                                            |
|---------------|-------------|-------------------------------------------------------|--------------------------------------------------------|
| `id`          | Integer     | Primary Key                                           | Unique identifier for the lesson page metadata.        |
| `lesson_id`   | Integer     | Foreign Key (`lesson.id`), Not Nullable               | ID of the `Lesson` this page belongs to.               |
| `page_number` | Integer     | Not Nullable                                          | The page number within the lesson.                     |
| `title`       | String(200) | Nullable                                              | Optional title for this page.                          |
| `description` | Text        | Nullable                                              | Optional description for this page.                    |
|               |             | Unique Constraint (`lesson_id`, `page_number`)        | Ensures page numbers are unique within a lesson.       |

**Relationships:**
- `lesson`: Many-to-One with `Lesson`.

---

#### 3.5. `LessonContent`

Represents an individual piece of content within a lesson page (e.g., a text block, an image, a specific Kana character, a quiz).

| Column                  | Type        | Constraints                                    | Description                                                                    |
|-------------------------|-------------|------------------------------------------------|--------------------------------------------------------------------------------|
| `id`                    | Integer     | Primary Key                                    | Unique identifier for the lesson content item.                                 |
| `lesson_id`             | Integer     | Foreign Key (`lesson.id`), Not Nullable        | ID of the `Lesson` this content item belongs to.                               |
| `content_type`          | String(20)  | Not Nullable                                   | Type of content ('kana', 'kanji', 'vocabulary', 'grammar', 'text', 'image', 'video', 'audio'). |
| `content_id`            | Integer     | Nullable                                       | Foreign key to `Kana`, `Kanji`, `Vocabulary`, or `Grammar` tables if applicable. |
| `title`                 | String(200) | Nullable                                       | Title for multimedia content (e.g., image caption).                            |
| `content_text`          | Text        | Nullable                                       | Text for 'text' type content.                                                  |
| `media_url`             | String(255) | Nullable                                       | URL for 'image', 'video', 'audio' if not using direct file upload.             |
| `order_index`           | Integer     | Default: 0                                     | Order of this content item within its lesson page.                             |
| `page_number`           | Integer     | Not Nullable, Default: 1                       | The page number within the lesson this content belongs to.                     |
| `is_optional`           | Boolean     | Default: False                                 | Flag indicating if this content item is optional for lesson completion.        |
| `created_at`            | DateTime    | Default: `datetime.utcnow`                     | Timestamp of when the content item was created.                                |
| `file_path`             | String(500) | Nullable                                       | Relative path to an uploaded file (stored in `UPLOAD_FOLDER`).                 |
| `file_size`             | Integer     | Nullable                                       | Size of the uploaded file in bytes.                                            |
| `file_type`             | String(50)  | Nullable                                       | MIME type of the uploaded file.                                                |
| `original_filename`     | String(255) | Nullable                                       | Original name of the uploaded file.                                            |
| `is_interactive`        | Boolean     | Default: False                                 | Flag indicating if this content is an interactive element (e.g., a quiz).      |
| `quiz_type`             | String(50)  | Default: 'standard'                            | Type of quiz ('standard', 'adaptive').                                         |
| `max_attempts`          | Integer     | Default: 3                                     | Maximum attempts allowed for an interactive element.                           |
| `passing_score`         | Integer     | Default: 70                                    | Passing score (percentage) for an interactive element.                         |
| `generated_by_ai`       | Boolean     | Not Nullable, Default: False                   | Flag indicating if this content was generated by AI.                           |
| `ai_generation_details` | JSON        | Nullable                                       | Metadata about the AI generation process (model, timestamp, prompts).          |

**Relationships:**
- `lesson`: Many-to-One with `Lesson`.
- `quiz_questions`: One-to-Many with `QuizQuestion`. If `is_interactive` is true and it's a quiz, this links to its questions.

---

### 4. Quiz System Models

#### 4.1. `QuizQuestion`

Stores a single question that can be part of a `LessonContent` item marked as interactive.

| Column            | Type        | Constraints                                          | Description                                                               |
|-------------------|-------------|------------------------------------------------------|---------------------------------------------------------------------------|
| `id`              | Integer     | Primary Key                                          | Unique identifier for the quiz question.                                  |
| `lesson_content_id`| Integer     | Foreign Key (`lesson_content.id`), Not Nullable    | ID of the `LessonContent` item this question belongs to.                  |
| `question_type`   | String(50)  | Not Nullable                                         | Type of question (e.g., 'multiple_choice', 'fill_blank', 'true_false', 'matching').   |
| `question_text`   | Text        | Not Nullable                                         | The text of the question.                                                 |
| `explanation`     | Text        | Nullable                                             | Explanation for the correct answer, shown after attempting.               |
| `hint`            | Text        | Nullable                                             | A hint to help the user solve the question.                               |
| `difficulty_level`| Integer     | Default: 1                                           | Difficulty level of the question (1-5), used for adaptive quizzes.        |
| `points`          | Integer     | Default: 1                                           | Points awarded for a correct answer.                                      |
| `order_index`     | Integer     | Default: 0                                           | Order of this question within its parent `LessonContent` quiz.            |
| `created_at`      | DateTime    | Default: `datetime.utcnow`                           | Timestamp of when the question was created.                               |

**Relationships:**
- `content`: Many-to-One with `LessonContent`.
- `options`: One-to-Many with `QuizOption`. A question can have multiple options (for multiple choice).
- `user_answers`: One-to-Many with `UserQuizAnswer`. Tracks answers from multiple users to this question.

---

#### 4.2. `QuizOption`

Stores a single option for a `QuizQuestion` (primarily for multiple-choice types).

| Column      | Type    | Constraints                                       | Description                                                      |
|-------------|---------|---------------------------------------------------|------------------------------------------------------------------|
| `id`        | Integer | Primary Key                                       | Unique identifier for the quiz option.                           |
| `question_id`| Integer | Foreign Key (`quiz_question.id`), Not Nullable  | ID of the `QuizQuestion` this option belongs to.                 |
| `option_text`| Text    | Not Nullable                                      | The text of the option.                                          |
| `is_correct`| Boolean | Default: False                                    | Flag indicating if this is the correct option.                   |
| `order_index`| Integer | Default: 0                                        | Order of this option within its question.                        |
| `feedback`  | Text    | Nullable                                          | Specific feedback to show if this option is selected.            |

**Relationships:**
- `question`: Many-to-One with `QuizQuestion`.

---

#### 4.3. `UserQuizAnswer`

Records a user's answer to a specific `QuizQuestion`.

| Column               | Type     | Constraints                                                       | Description                                                                 |
|----------------------|----------|-------------------------------------------------------------------|-----------------------------------------------------------------------------|
| `id`                 | Integer  | Primary Key                                                       | Unique identifier for the user's answer.                                    |
| `user_id`            | Integer  | Foreign Key (`user.id`), Not Nullable                             | ID of the `User` who answered.                                              |
| `question_id`        | Integer  | Foreign Key (`quiz_question.id`), Not Nullable                    | ID of the `QuizQuestion` being answered.                                    |
| `selected_option_id` | Integer  | Foreign Key (`quiz_option.id`), Nullable                          | ID of the `QuizOption` selected by the user (for multiple choice).          |
| `text_answer`        | Text     | Nullable                                                          | User's text input (for fill-in-the-blank type questions).                   |
| `is_correct`         | Boolean  | Default: False                                                    | Flag indicating if the user's answer was correct.                           |
| `answered_at`        | DateTime | Default: `datetime.utcnow`, OnUpdate: `datetime.utcnow`         | Timestamp of when the answer was last submitted/updated.                    |
| `attempts`           | Integer  | Not Nullable, Default: 0                                          | Number of attempts the user made on this question.                          |
|                      |          | Unique Constraint (`user_id`, `question_id`)                      | Ensures a user has only one answer record per question (updated on new attempt). |

**Relationships:**
- `user`: Many-to-One with `User`.
- `question`: Many-to-One with `QuizQuestion`.
- `selected_option`: Many-to-One with `QuizOption`.

---

### 5. User Progress Models

#### 5.1. `UserLessonProgress`

Tracks a user's progress through a specific lesson.

| Column                | Type     | Constraints                                           | Description                                                                     |
|-----------------------|----------|-------------------------------------------------------|---------------------------------------------------------------------------------|
| `id`                  | Integer  | Primary Key                                           | Unique identifier for the progress record.                                      |
| `user_id`             | Integer  | Foreign Key (`user.id`), Not Nullable                 | ID of the `User`.                                                               |
| `lesson_id`           | Integer  | Foreign Key (`lesson.id`), Not Nullable               | ID of the `Lesson`.                                                             |
| `started_at`          | DateTime | Default: `datetime.utcnow`                            | Timestamp when the user first started the lesson.                               |
| `completed_at`        | DateTime | Nullable                                              | Timestamp when the user completed the lesson.                                   |
| `is_completed`        | Boolean  | Default: False                                        | Flag indicating if the user has completed the lesson.                           |
| `progress_percentage` | Integer  | Default: 0                                            | Overall progress percentage (0-100).                                            |
| `time_spent`          | Integer  | Default: 0                                            | Estimated time spent by the user on the lesson in minutes.                      |
| `last_accessed`       | DateTime | Default: `datetime.utcnow`                            | Timestamp of the user's last interaction with the lesson.                       |
| `content_progress`    | Text     | Nullable                                              | JSON string storing completion status of individual `LessonContent` items. Example: `{"content_id_1": true, "content_id_2": false}` |
|                       |          | Unique Constraint (`user_id`, `lesson_id`)            | Ensures one progress record per user per lesson.                                |

**Relationships:**
- `user`: Many-to-One with `User`.
- `lesson`: Many-to-One with `Lesson`.

---

### 6. Course System Models

#### 6.1. `Course`

Represents a collection of lessons organized into a structured learning path.

| Column                | Type        | Constraints                                     | Description                                                               |
|-----------------------|-------------|-------------------------------------------------|---------------------------------------------------------------------------|
| `id`                  | Integer     | Primary Key                                     | Unique identifier for the course.                                         |
| `title`               | String(200) | Not Nullable                                    | Title of the course.                                                      |
| `description`         | Text        | Nullable                                        | A detailed description of the course.                                     |
| `background_image_url`| String(255) | Nullable                                        | URL for a course background/cover image.                                 |
| `is_published`        | Boolean     | Default: False                                  | Flag indicating if the course is visible to users.                       |
| `created_at`          | DateTime    | Default: `datetime.utcnow`                      | Timestamp of when the course was created.                                |
| `updated_at`          | DateTime    | Default: `datetime.utcnow`, OnUpdate: `datetime.utcnow` | Timestamp of the last update.                           |

**Relationships:**
- `lessons`: Many-to-Many with `Lesson` through `course_lessons` association table.

---

#### 6.2. `course_lessons` (Association Table)

Association table for the many-to-many relationship between `Course` and `Lesson`.

| Column      | Type    | Constraints                                    | Description                                      |
|-------------|---------|------------------------------------------------|--------------------------------------------------|
| `course_id` | Integer | Foreign Key (`course.id`), Primary Key        | ID of the `Course`.                              |
| `lesson_id` | Integer | Foreign Key (`lesson.id`), Primary Key        | ID of the `Lesson`.                              |

This table enables courses to contain multiple lessons and lessons to belong to multiple courses.

---

### 7. Database Migrations

Database schema changes are managed using Alembic. Migration scripts are located in the `migrations/versions/` directory.
- To generate a new migration after model changes: `alembic revision -m "description_of_changes"`
- To apply pending migrations: `python run_migrations.py` (which typically runs `alembic upgrade head`)

The initial schema is created by `db.create_all()` (called via `python setup_unified_auth.py`). Subsequent changes rely on Alembic migrations.

---

## API Design & Endpoints

### 1. Overview

The application's backend is built around a set of routes and a comprehensive RESTful API, all defined within the `app/routes.py` file using a Flask Blueprint. This API powers the dynamic frontend, the admin content management system, and all user interactions.

The design emphasizes a clear separation between user-facing rendered pages and the JSON-based API used for data manipulation.

### 2. Authentication and Authorization

All protected routes and API endpoints use a decorator-based system for access control.

-   **`@login_required`**: Standard Flask-Login decorator. Ensures the user is authenticated. Unauthenticated users are typically redirected to the login page.
-   **`@admin_required`**: A custom decorator that checks if `current_user.is_admin` is `True`. Used to protect all administrative routes and APIs.
-   **`@premium_required`**: A custom decorator that checks if `current_user.subscription_level` is `'premium'`. Used to restrict access to premium content.

### 3. API Endpoint Reference

The API is divided into several logical groups based on functionality.

#### 3.1. Public and Authentication Routes

These routes handle user registration, login, and basic page navigation. They primarily render HTML templates.

| Method | Endpoint             | Authentication | Description                                                                 |
| :----- | :------------------- | :------------- | :-------------------------------------------------------------------------- |
| `GET`  | `/` or `/home`       | None           | Renders the main homepage.                                                  |
| `GET/POST`| `/register`          | None           | Renders the registration page and handles new user form submission.         |
| `GET/POST`| `/login`             | None           | Renders the login page and handles user login form submission.              |
| `GET`  | `/logout`            | User           | Logs the current user out and redirects to the homepage.                    |
| `POST` | `/upgrade_to_premium`| User           | (Prototype) Upgrades the current user's subscription level to 'premium'.    |
| `POST` | `/downgrade_from_premium`| User         | (Prototype) Downgrades the current user's subscription level to 'free'.     |

#### 3.2. User-Facing Lesson and Course Routes

These routes are for users to view and interact with lesson content and courses.

| Method | Endpoint             | Authentication | Description                                                                 |
| :----- | :------------------- | :------------- | :-------------------------------------------------------------------------- |
| `GET`  | `/lessons`           | None           | Renders the main page for browsing all available lessons.                   |
| `GET`  | `/lessons/<int:id>`  | None/User      | Renders the detailed view for a single lesson. Access depends on lesson settings and user authentication. |
| `POST` | `/lessons/<int:id>/reset`| User         | Resets the current user's progress for the specified lesson.                |
| `GET`  | `/courses`           | None           | Renders the main page for browsing all available courses.                   |
| `GET`  | `/course/<int:id>`   | None/User      | Renders the detailed view for a single course with progress tracking.       |

#### 3.3. Admin Panel Routes

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

#### 3.4. Admin REST API

This is the core JSON-based API for all CRUD (Create, Read, Update, Delete) operations.

##### 3.4.1. Core Content APIs (Kana, Kanji, etc.)
These follow a standard RESTful pattern for each content type.

| Method | Endpoint                               | Description                               |
| :----- | :------------------------------------- | :---------------------------------------- |
| `GET`  | `/api/admin/<type>`                    | Lists all items of the specified type.    |
| `POST` | `/api/admin/<type>/new`                | Creates a new item of the specified type. |
| `GET`  | `/api/admin/<type>/<int:id>`           | Retrieves a single item by its ID.        |
| `PUT/PATCH`| `/api/admin/<type>/<int:id>/edit`  | Updates an existing item by its ID.       |
| `DELETE`| `/api/admin/<type>/<int:id>/delete`| Deletes an item by its ID.                |
_(`type` can be `kana`, `kanji`, `vocabulary`, or `grammar`)_

##### 3.4.2. Lesson, Category, and Course APIs

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

##### 3.4.3. Lesson Content Management APIs

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

##### 3.4.4. AI Content Generation APIs

| Method | Endpoint                             | Description                                                              |
| :----- | :----------------------------------- | :----------------------------------------------------------------------- |
| `POST` | `/api/admin/generate-ai-content`     | Generates text explanations and quiz content via AI.                     |
| `POST` | `/api/admin/generate-ai-image`       | Generates images using DALL-E from prompts or content.                   |
| `POST` | `/api/admin/analyze-multimedia-needs`| Analyzes lesson content and suggests multimedia enhancements.            |
| `POST` | `/api/admin/generate-lesson-images`  | Generates multiple images for lesson content.                            |

##### 3.4.5. File Management APIs

| Method | Endpoint                             | Description                                                              |
| :----- | :----------------------------------- | :----------------------------------------------------------------------- |
| `POST` | `/api/admin/upload-file`             | Handles file uploads with validation and processing.                     |
| `DELETE`| `/api/admin/delete-file`             | Deletes a file from the filesystem.                                      |
| `GET`  | `/uploads/<path:filename>`           | Serves uploaded files securely.                                          |

##### 3.4.6. Content Approval APIs

| Method | Endpoint                                               | Description                                                              |
| :----- | :----------------------------------------------------- | :----------------------------------------------------------------------- |
| `POST` | `/api/admin/content/<type>/<int:id>/approve`           | Approves AI-generated content (kanji, vocabulary, grammar).              |
| `POST` | `/api/admin/content/<type>/<int:id>/reject`            | Rejects and deletes AI-generated content.                                |

##### 3.4.7. Export/Import APIs

| Method | Endpoint                                   | Description                                                              |
| :----- | :----------------------------------------- | :----------------------------------------------------------------------- |
| `GET`  | `/api/admin/lessons/<int:id>/export`       | Exports a lesson's data as a JSON file.                                  |
| `POST` | `/api/admin/lessons/<int:id>/export-package`| Exports a lesson and its media files as a single ZIP package.            |
| `POST` | `/api/admin/lessons/export-multiple`       | Exports multiple lessons as a single ZIP package.                        |
| `POST` | `/api/admin/lessons/import`                | Imports a lesson from an uploaded JSON file.                             |
| `POST` | `/api/admin/lessons/import-package`        | Imports a lesson from an uploaded ZIP package.                           |
| `POST` | `/api/admin/lessons/import-info`           | Analyzes an import file without importing to provide a preview.          |

##### 3.4.8. AI Content Generation Services
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

#### 3.5. User Data and Quiz APIs

| Method | Endpoint                                           | Authentication | Description                                                              |
| :----- | :------------------------------------------------- | :------------- | :----------------------------------------------------------------------- |
| `GET`  | `/api/lessons`                                     | None/User      | Gets all lessons accessible to the current user or guest, with optional filtering. |
| `GET`  | `/api/courses`                                     | None           | Gets all published courses.                                              |
| `GET`  | `/api/categories`                                  | None           | Gets all lesson categories for public use.                               |
| `POST` | `/api/lessons/<int:id>/progress`                   | User           | Updates the user's progress for a specific content item in a lesson.     |
| `POST` | `/api/lessons/<int:lid>/quiz/<int:qid>/answer`     | User           | Submits a user's answer to a quiz question and returns the result.       |

### 4. Common Response Formats

-   **Success (GET, PUT, POST)**: Returns a `200 OK` or `201 Created` status with a JSON object or array representing the requested/modified resource(s).
-   **Success (DELETE)**: Returns a `200 OK` with a confirmation message, e.g., `{"message": "Item deleted successfully"}`.
-   **Client Error**: Returns a `4xx` status code (e.g., `400 Bad Request`, `404 Not Found`, `403 Forbidden`) with a JSON object describing the error, e.g., `{"error": "Missing required fields"}`.
-   **Server Error**: Returns a `500 Internal Server Error` with a generic error message, e.g., `{"error": "Database error occurred"}`. Specific details are logged on the server but not exposed to the client.

---

## Frontend Architecture

### 1. Overview

The frontend of the Japanese Learning Website is primarily built using server-side rendered HTML templates via Jinja2, styled with Bootstrap 5.3.3, and enhanced with vanilla JavaScript for client-side interactivity and AJAX calls.

### 2. Core Technologies

-   **HTML5**: Semantic markup for structuring content.
-   **CSS3**: Custom styling in conjunction with Bootstrap.
    -   Custom styles are located in `app/static/css/custom.css`.
-   **Bootstrap 5.3.3**: Responsive CSS framework for layout, components (modals, carousels, forms), and overall styling. Typically loaded via CDN.
-   **Jinja2**: Python templating engine used by Flask to render dynamic HTML pages by embedding data from the backend into templates.
-   **JavaScript (ES6+)**: Vanilla JavaScript is used for:
    -   Client-side form validation (though primarily handled server-side by WTForms).
    -   DOM manipulation for UI updates without full page reloads.
    -   AJAX requests to backend API endpoints (e.g., for submitting quiz answers, updating progress, AI content generation in admin panel).
    -   Event handling (e.g., button clicks, carousel interactions).

### 3. Template Structure (`app/templates/`)

-   **Base Templates**:
    -   `base.html`: Main base template for user-facing pages. Includes common structure like navbar, footer, and blocks for content, scripts, and styles.
    -   `admin/base_admin.html`: Base template for admin panel pages, extending `base.html` or providing its own structure with admin-specific navigation.
-   **Layout Inheritance**: Jinja2's template inheritance (`{% extends %}`, `{% block %}`) is used extensively to maintain a consistent layout and reduce code duplication.
-   **User-Facing Pages**:
    -   `index.html`: Homepage.
    -   `lessons.html`: Lists available lessons.
    -   `lesson_view.html`: Displays a single lesson with its paginated content (often using a carousel).
    -   `login.html`, `register.html`: Authentication pages.
-   **Admin Pages (`app/templates/admin/`)**:
    -   `admin_index.html`: Admin dashboard.
    -   `manage_lessons.html`, `manage_categories.html`, etc.: Pages for CRUD operations on different content types.
    -   Forms for creating and editing content are rendered here.
-   **Includes/Macros**: Reusable template snippets (e.g., for rendering a single lesson card, a form field) might be defined using `{% include %}` or Jinja2 macros.

### 4. Static Assets (`app/static/`)

-   **CSS (`app/static/css/`)**: Contains custom stylesheets like `custom.css` that override or supplement Bootstrap styles.
-   **JavaScript (`app/static/js/`)**: (If any custom global JS files exist, they would be here). Much of the JS might be inline in templates or specific to admin panel sections.
-   **Images (`app/static/images/`)**: Site-wide images like logos, backgrounds.
-   **Uploads (`app/static/uploads/`)**: Default directory for user-uploaded content (lesson images, audio). This path is configurable. Files here are served via a dedicated route.

### 5. Key Frontend Components & Interactions

#### 5.1. Lesson Display (`lesson_view.html`)
-   Often uses a Bootstrap Carousel component to display lesson pages.
-   JavaScript handles navigation between pages (next/previous buttons, possibly swipe gestures if a library is used).
-   Content items within a page are rendered based on their type.
-   Interactive elements (quizzes) use JavaScript to handle answer submission via AJAX and display feedback.

#### 5.2. Admin Panel Forms
-   Forms are generated using Flask-WTF and rendered by Jinja2.
-   Client-side JavaScript might be used for:
    -   Dynamic form elements (e.g., adding more options to a quiz question).
    -   AJAX submissions for parts of the form (e.g., AI content generation, file uploads).
    -   Rich Text Editors (if integrated) for text content.

#### 5.3. AJAX Communication
-   Vanilla JavaScript's `fetch` API is used for making asynchronous requests to backend API endpoints.
-   Requests typically send/receive JSON data.
-   CSRF tokens (if required by the endpoint) are included in request headers.
-   Responses are used to update the DOM dynamically (e.g., show success/error messages, refresh parts of a page).

### 6. State Management

-   Primarily stateless from the frontend perspective for page loads (data comes from the backend with each request).
-   Client-side JavaScript may hold temporary UI state (e.g., current page in a lesson carousel, form data before submission).
-   User session state is managed server-side by Flask-Login.

### 7. Build Process / Dependencies

-   No complex frontend build process (e.g., Webpack, Parcel) is implied by the current structure.
-   Frontend dependencies (like Bootstrap) are mainly included via CDNs or are simple static files.

### 8. Future Considerations / Potential Enhancements

-   **JavaScript Framework/Library**: For more complex client-side interactions or a Single Page Application (SPA) feel, a framework like Vue.js, React, or a library like HTMX could be introduced.
-   **Frontend Build Tools**: If JS/CSS complexity grows, tools like Webpack or Parcel could be added for bundling, minification, and transpilation.
-   **State Management Libraries**: For SPAs, client-side state management libraries (e.g., Pinia for Vue, Redux for React) might become necessary.
-   **Improved Asset Management**: More sophisticated handling of static assets.

*(This document is a placeholder and provides a high-level overview based on common Flask frontend practices and inferred project structure. It will be expanded as more specific frontend details are defined or implemented.)*

---

## File Structure & Organization

### 1. Overview

This document outlines the main file and directory structure of the Japanese Learning Website project. A comprehensive understanding of the structure helps in navigating the codebase and locating specific components.

### 2. Root Directory

```
Japanese_Learning_Website/
├── .env                            # Environment variables (local, not version-controlled)
├── .gitignore                      # Specifies intentionally untracked files for Git
├── add_language_field_migration.py # Migration script to add language field to models
├── ai_image_downloader.py          # Script to download images for lessons from AI services
├── app/                            # Main Flask application package
├── Archive/                        # Contains older, archived versions of the project
├── content_discovery.py            # Script for content discovery and analysis
├── create_admin.py                 # Script to create additional admin users
├── create_comprehensive_multimedia_lesson.py # AI-powered script to generate lessons with multimedia
├── create_hiragana_lesson.py       # Utility script for lesson creation
├── create_hiragana_lesson_german.py # Utility script for lesson creation (German instructions)
├── create_jlpt_lesson_database_aware.py # AI-powered script for JLPT lessons, aware of existing content
├── create_kana_lesson_database_aware.py # AI-powered script for Kana lessons, aware of existing content
├── create_kanji_lesson.py          # Utility script for lesson creation
├── create_numbers_lesson.py        # Utility script for lesson creation
├── create_numbers_lesson_enhanced.py # Enhanced script for creating lessons on numbers
├── create_technology_lesson.py     # Utility script for lesson creation
├── create_travel_japanese_lesson.py # Utility script for lesson creation
├── curl_examples.md                # cURL examples for API testing
├── deprecated/                     # Older or unused files and directories
├── Documentation/                  # Project documentation files
├── Documentation.md                # Top-level documentation file
├── fix_content_order.py            # Data migration script
├── instance/                       # Instance folder (e.g., for SQLite DB, instance-specific config)
├── inspect_db.py                   # Utility to inspect database contents
├── lesson_creator_base.py          # Base class for lesson creation scripts
├── lesson_template.py              # Class for creating lessons from templates
├── lesson_templates/               # Directory for lesson templates
├── multi_modal_generator.py        # Class for generating multi-modal content
├── manual_migration.py             # Script for manual data migration tasks
├── migrate_database.py             # General purpose database migration script
├── migrate_file_fields.py          # Data migration script
├── migrate_interactive_system.py   # Data migration script
├── migrate_lesson_system.py        # Script for initial data seeding and core migrations
├── migrate_page_numbers.py         # Data migration script
├── migrations/                     # Alembic database migration scripts
├── multimedia_lesson_creator.py    # Creator class for multimedia lessons
├── PHASE3_IMPLEMENTATION_SUMMARY.md # Summary of Phase 3 implementation
├── populate_sample_database.py     # Script to populate the database with sample data
├── possible_next_steps.md          # Document outlining potential future work
├── README.md                       # Main project README file
├── requirements.txt                # Python package dependencies
├── run.py                          # Main script to run the Flask application
├── run_migrations.py               # Script to apply Alembic database migrations
├── setup_unified_auth.py           # Script for initial database schema setup and default admin
└── update_instruction_language_migration.py # Migration script for instruction language
```

### 3. Key Directories

#### 3.1. `app/` - Main Application Package
```
app/
├── __init__.py             # Application factory (create_app), initializes Flask app and extensions
├── ai_services.py          # Services for AI-powered content generation (e.g., OpenAI integration)
├── forms.py                # WTForms definitions for login, registration, content management, etc.
├── lesson_export_import.py # Logic for exporting and importing lesson data
├── models.py               # SQLAlchemy database models
├── routes.py               # Flask routes and view functions (controllers)
├── static/                 # Static files (CSS, JavaScript, images, user uploads)
│   ├── css/                # Custom CSS files (e.g., custom.css)
│   ├── images/             # Site-specific images (logos, backgrounds)
│   └── uploads/            # Default directory for user-uploaded files (images, audio for lessons)
├── templates/              # Jinja2 HTML templates
│   ├── admin/              # Templates specific to the admin panel
│   │   ├── admin_index.html
│   │   ├── base_admin.html
│   │   ├── login.html
│   │   ├── manage_approval.html
│   │   ├── manage_categories.html
│   │   ├── manage_grammar.html
│   │   ├── manage_kana.html
│   │   ├── manage_kanji.html
│   │   ├── manage_lessons.html
│   │   └── manage_vocabulary.html
│   ├── base.html           # Base template for user-facing pages
│   ├── index.html          # Homepage template
│   ├── lessons.html        # Template for listing lessons
│   ├── lesson_view.html    # Template for displaying a single lesson
│   ├── login.html          # User login page template
│   └── register.html       # User registration page template
└── utils.py                # Utility functions and helper classes (e.g., FileUploadHandler)
```

#### 3.2. `migrations/` - Alembic Database Migrations
```
migrations/
├── versions/               # Contains individual migration script files generated by Alembic
├── README                  # Information about Alembic setup for this project
├── env.py                  # Alembic environment script, configures how migrations run
└── script.py.mako          # Template for new migration scripts
```

#### 3.3. `instance/` - Instance Folder
- Contains configuration files and data that are specific to a particular instance of the application and should not be version-controlled.
- `app.db` or `site.db`: The SQLite database file is typically located here in development.
- `config.py`: Instance-specific Flask configuration.

#### 3.4. `Documentation/`
- Contains all project documentation in Markdown format. The documentation is organized into numbered files covering system architecture, setup, features, and development processes. It also includes subdirectories for more detailed topics like `Enhanced-Lesson-Creation-Scripts`.

#### 3.5. `deprecated/`
- Contains old files, previous versions of modules, or experimental code that is no longer in active use but kept for historical reference.

### 4. Scripts in Root Directory

-   **`run.py`**: Entry point to start the Flask development server.
-   **`setup_unified_auth.py`**: Initializes the database schema (`db.create_all()`) and creates a default admin user. Intended for first-time setup.
-   **`run_migrations.py`**: Applies pending Alembic database migrations (`alembic upgrade head`).
-   **`create_admin.py`**: Allows creation of additional administrator accounts.
-   **`create_*.py`**: A suite of utility scripts to populate the database with specific predefined lessons, often using AI services. These scripts are highly specialized for different types of content (e.g., Hiragana, Kanji, JLPT levels).
-   **`lesson_creator_base.py` / `multimedia_lesson_creator.py`**: Base classes that provide foundational logic for the various `create_*.py` scripts, promoting code reuse.
-   **`migrate_*.py`**: Scripts for initial data seeding or specific data migration tasks that might be too complex for a standard Alembic data migration.
-   **`add_*.py` / `update_*.py`**: One-off migration scripts for specific database schema changes.
-   **`inspect_db.py`**: A utility script for developers to query or inspect the database contents directly.
-   **`ai_image_downloader.py`**: A script to fetch and save images related to lesson content using AI services.
-   **`content_discovery.py`**: A utility for analyzing the existing content in the database.

---

## Configuration Management

Application configuration is primarily managed through environment variables loaded from a `.env` file and default values set in `app/__init__.py` or `instance/config.py`.

## 1. Environment Variables (`.env` file)
A `.env` file in the project root is used to store sensitive and environment-specific configurations. This file should **not** be committed to version control. The `python-dotenv` package loads these variables into the environment when the application starts.

### Key Environment Variables

- **`FLASK_APP=run.py`**: Specifies the entry point for the Flask CLI.
- **`FLASK_ENV=development`**: Sets the Flask environment. Can be `development` or `production`.
    - In `development` mode, `FLASK_DEBUG` is often implicitly or explicitly set to `True`, enabling the interactive debugger and auto-reloader.
- **`FLASK_DEBUG=True`**: Enables/disables debug mode (set to `False` in production).
- **`SECRET_KEY`**: A long, random string used for session signing, CSRF token generation, and other security-related cryptographic needs. **Crucial for security and must be kept secret.**
    - Example: `SECRET_KEY=my-very-secret-and-long-random-string-123!@#`
- **`DATABASE_URL`**: Specifies the connection string for the database.
    - Example for SQLite: `DATABASE_URL=sqlite:///instance/site.db`
    - Example for PostgreSQL: `DATABASE_URL=postgresql://user:password@host:port/dbname`
- **`UPLOAD_FOLDER=app/static/uploads`**: The absolute or relative path to the directory where user-uploaded files (for lessons, etc.) will be stored. The application will attempt to create subdirectories within this folder (e.g., `lessons/image`, `lessons/audio`).
- **`MAX_CONTENT_LENGTH=16777216`**: (Optional) Maximum allowed size for file uploads, in bytes (e.g., 16MB). This is a standard Flask configuration.
- **`OPENAI_API_KEY`**: (Required if using AI features) Your API key for OpenAI services, used by `app/ai_services.py` for generating lesson content.
    - Example: `OPENAI_API_KEY=sk-YourActualOpenAIKeyHere`

### Example `.env` file
```env
FLASK_APP=run.py
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-chosen-secret-key-should-be-long-and-random
DATABASE_URL=sqlite:///instance/site.db
UPLOAD_FOLDER=app/static/uploads
# MAX_CONTENT_LENGTH=16777216 # Optional: 16MB
# OPENAI_API_KEY=sk-YourActualOpenAIKeyHere # Required for AI features
```

## 2. Application Configuration (`app/__init__.py` and `instance/config.py`)

The Flask application factory (`create_app` in `app/__init__.py`) loads configurations.

### Default Configuration
Base configurations are often set directly in `app/__init__.py` or a `config.py` file imported there.
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

### Instance Folder Configuration (`instance/config.py`)
- The `instance/` folder is outside the `app` package and can hold instance-specific configuration that should not be version-controlled (though `.env` is preferred for most secrets).
- Flask can be configured to load a `config.py` file from this folder if it exists: `app.config.from_pyfile('config.py', silent=True)`.
- The current project structure implies primary reliance on `.env` for overriding defaults, but `instance/config.py` could be used for more complex instance-specific settings if needed.

## 3. Configuration Categories

### Development Configuration
```env
FLASK_ENV=development
FLASK_DEBUG=True
DATABASE_URL=sqlite:///instance/site.db
UPLOAD_FOLDER=app/static/uploads
SECRET_KEY=dev-secret-key-change-in-production
```

### Production Configuration
```env
FLASK_ENV=production
FLASK_DEBUG=False
DATABASE_URL=postgresql://user:password@host:port/dbname
UPLOAD_FOLDER=/var/www/uploads
SECRET_KEY=very-long-random-production-secret-key
MAX_CONTENT_LENGTH=52428800  # 50MB
```

### Testing Configuration
```env
FLASK_ENV=testing
FLASK_DEBUG=False
DATABASE_URL=sqlite:///:memory:
UPLOAD_FOLDER=/tmp/test_uploads
SECRET_KEY=test-secret-key
WTF_CSRF_ENABLED=False  # Disable CSRF for testing
```

## 4. Security Considerations

### Secret Key Management
- **Development**: Use a simple key for local development
- **Production**: Generate a cryptographically secure random key
- **Never commit**: Secret keys should never be in version control

```python
# Generate a secure secret key
import secrets
secret_key = secrets.token_hex(32)
print(f"SECRET_KEY={secret_key}")
```

### Database URLs
- **Development**: Local SQLite file
- **Production**: Secure connection strings with proper credentials
- **Environment Variables**: Store sensitive database credentials in environment variables

### File Upload Security
```python
# Secure file upload configuration
UPLOAD_FOLDER = '/secure/upload/path'
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB limit
ALLOWED_EXTENSIONS = {
    'image': {'png', 'jpg', 'jpeg', 'gif'},
    'audio': {'mp3', 'wav', 'ogg'},
    'document': {'pdf', 'txt'}
}
```

## 5. Configuration Loading Order

The application loads configuration in the following order (later values override earlier ones):

1. **Default values** in `app/__init__.py`
2. **Instance configuration** from `instance/config.py` (if exists)
3. **Environment variables** from `.env` file
4. **System environment variables**

## 6. Configuration Validation

### Required Configuration Check
```python
def validate_config(app):
    """Validate that required configuration is present"""
    required_configs = ['SECRET_KEY', 'DATABASE_URL']
    
    for config in required_configs:
        if not app.config.get(config):
            raise ValueError(f"Required configuration {config} is missing")
    
    # Validate SECRET_KEY strength
    if len(app.config['SECRET_KEY']) < 32:
        raise ValueError("SECRET_KEY must be at least 32 characters long")
```

### File Upload Configuration Validation
```python
def validate_upload_config(app):
    """Validate file upload configuration"""
    upload_folder = app.config.get('UPLOAD_FOLDER')
    
    if not upload_folder:
        raise ValueError("UPLOAD_FOLDER must be configured")
    
    # Ensure upload directory exists
    os.makedirs(upload_folder, exist_ok=True)
    
    # Check write permissions
    if not os.access(upload_folder, os.W_OK):
        raise ValueError(f"Upload folder {upload_folder} is not writable")
```

## 7. Environment-Specific Settings

### Development Settings
- Debug mode enabled
- Detailed error pages
- Auto-reload on code changes
- Local SQLite database
- Relaxed security settings

### Production Settings
- Debug mode disabled
- Error logging to files
- Production database (PostgreSQL/MySQL)
- Strict security headers
- Performance optimizations

### Testing Settings
- In-memory database
- CSRF protection disabled
- Simplified authentication
- Mock external services

## 8. Configuration Best Practices

### Security
- Never hardcode secrets in source code
- Use environment variables for sensitive data
- Rotate secrets regularly
- Use different secrets for different environments

### Maintainability
- Document all configuration options
- Use descriptive variable names
- Provide sensible defaults
- Validate configuration on startup

### Deployment
- Use configuration management tools
- Automate environment setup
- Version control configuration templates
- Monitor configuration changes

## 9. Common Configuration Patterns

### Database Configuration
```python
# Support multiple database types
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///instance/site.db')

if DATABASE_URL.startswith('sqlite'):
    # SQLite-specific settings
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
elif DATABASE_URL.startswith('postgresql'):
    # PostgreSQL-specific settings
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
    }
```

### Feature Flags
```python
# Enable/disable features via configuration
FEATURES = {
    'user_registration': os.environ.get('ENABLE_REGISTRATION', 'true').lower() == 'true',
    'premium_content': os.environ.get('ENABLE_PREMIUM', 'true').lower() == 'true',
    'file_uploads': os.environ.get('ENABLE_UPLOADS', 'true').lower() == 'true',
}
```

Configuration values are accessed within the application using `current_app.config['CONFIG_KEY']`.

---

## Security Implementation

### 1. Overview

This document outlines the key security measures and practices implemented within the Japanese Learning Website to protect user data, ensure application integrity, and prevent common web vulnerabilities. Security is a multi-layered approach, encompassing authentication, authorization, input validation, data protection, and secure configuration.

*(Many of these aspects are also touched upon in `03-System-Architecture.md` and `07-User-Authentication.md`. This document aims to consolidate and elaborate on them from a security perspective.)*

### 2. Authentication and Session Management

-   **Framework**: Flask-Login is used for managing user sessions.
-   **Password Hashing**:
    -   Passwords are never stored in plaintext.
    -   `werkzeug.security.generate_password_hash` (PBKDF2 with salt and multiple iterations by default) is used to hash passwords upon registration and password changes.
    -   `werkzeug.security.check_password_hash` is used for verifying passwords during login.
-   **Session Cookies**:
    -   Flask-Login uses cryptographically signed cookies to maintain session integrity. The application's `SECRET_KEY` is vital for this.
    -   **Production Configuration**:
        -   `SESSION_COOKIE_SECURE=True`: Ensures cookies are only sent over HTTPS.
        -   `SESSION_COOKIE_HTTPONLY=True`: Prevents client-side JavaScript access to session cookies, mitigating XSS impact.
        -   `SESSION_COOKIE_SAMESITE='Lax'` (or `'Strict'`): Provides protection against CSRF attacks.
        -   `PERMANENT_SESSION_LIFETIME`: Configured to manage session duration.
-   **User Loader**: A `@login_manager.user_loader` function is implemented to reload the user object from the session on each request.
-   **Logout**: `flask_login.logout_user()` securely clears the session.

### 3. Authorization (Access Control)

-   **Role-Based Access Control (RBAC)**:
    -   `User.is_admin` (Boolean): Differentiates administrators from regular users.
    -   `User.subscription_level` (String: 'free', 'premium'): Controls access to premium content.
-   **Decorators**: Custom decorators are used to protect routes:
    -   `@login_required` (from Flask-Login): Ensures a user is authenticated.
    -   `@admin_required`: Custom decorator checking `current_user.is_admin`.
    -   `@premium_required`: Custom decorator checking `current_user.subscription_level`.
-   **Granular Checks**: Within views and templates, `current_user` attributes are checked to control access to specific features or data.

### 4. Input Validation and Sanitization

-   **Form Validation (Flask-WTF & WTForms)**:
    -   All forms (`app/forms.py`) define validators for each field (e.g., `DataRequired`, `Length`, `Email`, `EqualTo`).
    -   Server-side validation is performed upon form submission.
-   **API Endpoint Validation**:
    -   JSON payloads received by API endpoints are explicitly validated within the route handlers in `app/routes.py` (checking for required fields, data types, and value constraints).
-   **File Upload Validation (`app/utils.py -> FileUploadHandler`)**:
    -   **Allowed Extensions**: Strict validation against a predefined set of allowed file extensions (`app.config['ALLOWED_EXTENSIONS']`).
    -   **MIME Type Validation**: `python-magic` is used to verify the actual content type of the file, preventing type confusion attacks (e.g., an executable renamed to `.jpg`).
    -   **Secure Filenames**: `werkzeug.utils.secure_filename` is used as a base, and unique filenames are generated to prevent directory traversal or overwriting issues.
    -   **Max Content Length**: `app.config['MAX_CONTENT_LENGTH']` limits the size of uploaded files.
-   **Output Encoding (XSS Prevention)**:
    -   Jinja2, the templating engine used by Flask, auto-escapes variables by default when rendering HTML. This is a primary defense against Cross-Site Scripting (XSS).
    -   Care is taken to avoid disabling auto-escaping (e.g., using `|safe` filter) unless the content is known to be secure or is explicitly sanitized.

### 5. CSRF (Cross-Site Request Forgery) Protection

-   **Flask-WTF**: Provides built-in CSRF protection for all forms.
    -   A hidden CSRF token field (`{{ form.csrf_token }}` or `{{ form.hidden_tag() }}`) is included in forms.
    -   This token is validated on the server for all POST, PUT, DELETE requests originating from forms.
-   **AJAX Requests**: For AJAX requests that modify state, the CSRF token must be included in the request headers (e.g., `X-CSRFToken`).
-   **`CSRFTokenForm`**: Used for actions triggered by POST requests that don't have other form fields (e.g., lesson reset, subscription changes) to ensure they are also CSRF-protected.

### 6. Data Protection

-   **Database**:
    -   SQLAlchemy ORM helps prevent SQL injection vulnerabilities by parameterizing queries. Direct construction of SQL queries with user input is avoided.
    -   Sensitive data in the database (beyond passwords) should be encrypted if necessary, though current models do not indicate this for other fields.
-   **Configuration Secrets**:
    -   `SECRET_KEY`, `DATABASE_URL` (with credentials), `OPENAI_API_KEY` are stored in a `.env` file, which is not committed to version control.
    -   These are loaded as environment variables.
-   **File System**:
    -   Uploaded files are stored in a designated `UPLOAD_FOLDER`.
    -   Direct execution of uploaded files is prevented. Files are served via a controlled Flask route (`routes.uploaded_file`) that performs path validation.

### 7. Error Handling and Logging

-   **Debug Mode**: `FLASK_DEBUG=False` in production to prevent exposure of sensitive debug information.
-   **Error Pages**: Custom error pages (e.g., for 404, 500 errors) can be configured to avoid leaking internal details.
-   **Logging**: Comprehensive logging (see `16-Troubleshooting.md`) helps in identifying and diagnosing security incidents or suspicious activity. Sensitive information should be filtered from logs.

### 8. Secure Headers

While not explicitly detailed in `app/__init__.py` setup, for production deployments, consider adding security-related HTTP headers, often via a WSGI middleware or web server configuration (e.g., Nginx):
-   **`X-Content-Type-Options: nosniff`**: Prevents browsers from MIME-sniffing a response away from the declared content type.
-   **`X-Frame-Options: DENY` or `SAMEORIGIN`**: Protects against clickjacking attacks.
-   **`Content-Security-Policy (CSP)`**: A powerful header to control resources the browser is allowed to load, mitigating XSS and data injection attacks.
-   **`HTTP Strict Transport Security (HSTS)`**: Enforces secure (HTTPS) connections to the server.

### 9. Regular Audits and Updates

-   **Dependency Management**: Regularly update dependencies listed in `requirements.txt` to patch known vulnerabilities. Tools like `pip-audit` can help.
-   **Code Reviews**: Security considerations should be part of code reviews.
-   **Security Scans**: Periodically run security scanning tools against the application.

### 10. Specific Feature Security

#### 10.1. AI Content Generation (`app/ai_services.py`)
-   **API Key Security**: `OPENAI_API_KEY` is managed as an environment secret.
-   **Input to AI**: Data sent to OpenAI (topic, difficulty, keywords) is based on admin input for content generation and does not include user PII from the application's user base.
-   **Output Handling**: Content received from AI is subject to admin review and editing before being saved and displayed.

*(This document provides a summary of key security implementations. Continuous vigilance and updates are necessary to maintain a secure application.)*

---

## Development Workflow

### 1. Overview

This document outlines the recommended development workflow for contributing to the Japanese Learning Website project. Following these guidelines helps maintain code quality, consistency, and collaboration efficiency.

### 2. Environment Setup

1.  **Prerequisites**: Ensure Python 3.8+, pip, Git, and virtual environment tools are installed.
2.  **Clone Repository**: `git clone <repository-url>`
3.  **Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # macOS/Linux
    # venv\Scripts\activate    # Windows
    ```
4.  **Install Dependencies**: `pip install -r requirements.txt`
5.  **Configuration**: Create a `.env` file in the project root with necessary environment variables (see `06-Configuration-Management.md`).
    ```env
    FLASK_APP=run.py
    FLASK_ENV=development
    FLASK_DEBUG=True
    SECRET_KEY=your-dev-secret-key
    DATABASE_URL=sqlite:///instance/site.db
    UPLOAD_FOLDER=app/static/uploads
    OPENAI_API_KEY=your-openai-api-key # If working on AI features
    ```
6.  **Database Setup**:
    ```bash
    python setup_unified_auth.py   # Initializes DB schema and default admin
    python migrate_lesson_system.py # Seeds initial data and runs core data migrations
    # python run_migrations.py     # Apply any pending Alembic migrations if updating an existing setup
    ```

### 3. Version Control (Git)

-   **Branching Strategy**:
    -   `main` (or `master`): Stable, production-ready code. Direct commits are generally disallowed.
    -   `develop`: Integration branch for features that are ready for the next release.
    -   **Feature Branches**: Create new branches from `develop` for each new feature or bugfix (e.g., `feature/new-quiz-type`, `bugfix/login-error`).
        -   Naming: `feature/<short-description>`, `bugfix/<short-description>`, `chore/<task-description>`.
-   **Commits**:
    -   Make small, logical commits.
    -   Write clear and concise commit messages (e.g., imperative mood: "Add user profile page", "Fix validation for email field").
    -   Reference issue numbers if applicable (e.g., "Fix #123: Resolve login redirect loop").
-   **Pull Requests (PRs)**:
    -   When a feature/bugfix is complete, push the branch to the remote repository and open a PR against `develop`.
    -   Provide a clear description of the changes in the PR.
    -   Ensure any relevant tests pass (see Section 5).
    -   Code review by at least one other developer is recommended before merging.
-   **Keeping Up-to-Date**: Regularly pull changes from the remote `develop` branch into your feature branch to avoid large merge conflicts:
    ```bash
    git checkout develop
    git pull origin develop
    git checkout your-feature-branch
    git merge develop
    ```
    Or, use `git rebase develop` for a cleaner history (advanced).

### 4. Coding Standards & Conventions

-   **Python**: Follow PEP 8 style guidelines.
    -   Use a linter (e.g., Flake8, Pylint) and a formatter (e.g., Black, autopep8) to maintain consistency.
-   **Flask**: Adhere to Flask best practices (e.g., using Blueprints for route organization if the app grows, application factory pattern).
-   **HTML/CSS/JavaScript**: Maintain readability and consistency. Comment complex code.
-   **Documentation**:
    -   Add/update relevant project documentation in the `Documentation/` folder for new features or significant changes.
    -   Write clear docstrings for Python functions, classes, and modules.
    -   Comment code where the logic is not immediately obvious.

### 5. Testing

*(While specific test files were not detailed in the initial exploration, a testing strategy is crucial.)*

-   **Unit Tests**:
    -   Focus on testing individual functions, methods, and classes in isolation.
    -   Use a testing framework like `pytest` or Python's built-in `unittest`.
    -   Mock external dependencies (e.g., database, OpenAI API) where appropriate.
    -   Aim for good code coverage.
-   **Integration Tests**:
    -   Test interactions between different components (e.g., route handlers interacting with database models).
    -   Can also use `pytest` or `unittest` with Flask's test client.
-   **End-to-End (E2E) Tests**: (Optional, for larger features)
    -   Use tools like Selenium or Playwright to simulate user interactions in a browser.
-   **Running Tests**:
    -   Establish a command to run all tests (e.g., `pytest`, `python -m unittest discover`).
    -   Tests should be runnable locally and in CI/CD pipelines.
-   **Test-Driven Development (TDD)**: Consider writing tests before writing implementation code, especially for new features.

### 6. Database Migrations (Alembic)

-   When making changes to SQLAlchemy models in `app/models.py` that affect the database schema:
    1.  **Generate a new migration script**:
        ```bash
        alembic revision -m "Descriptive message for schema changes"
        ```
    2.  **Review and Edit**: Carefully inspect the generated script in `migrations/versions/`. Manually adjust if Alembic's autogenerate didn't capture the intent perfectly (especially for constraints, data type changes, or data migrations).
    3.  **Apply the migration locally**:
        ```bash
        python run_migrations.py
        ```
    4.  **Commit the migration script** along with your model changes.
-   **Never manually edit the database schema** in a development or production environment that is managed by Alembic. All changes should go through migration scripts.

### 7. Debugging

-   Utilize Flask's built-in debugger (enabled when `FLASK_DEBUG=True`).
-   Use `print()` statements or Python's `logging` module for more persistent debugging information.
-   Use your IDE's debugging tools.
-   Inspect database state directly using `sqlite3 instance/site.db` or a DB browser.

### 8. Dependency Management

-   Add new Python dependencies to `requirements.txt`.
    ```bash
    pip freeze > requirements.txt # After installing a new package
    ```
-   Regularly review and update dependencies to their latest stable versions to incorporate security patches and improvements.

### 9. Contribution Workflow Summary

1.  Ensure your local `develop` branch is up-to-date: `git checkout develop && git pull origin develop`.
2.  Create a new feature branch: `git checkout -b feature/my-new-feature develop`.
3.  Implement changes, write tests, and add/update documentation.
4.  Commit changes frequently with clear messages.
5.  If database models changed, create and commit Alembic migration scripts.
6.  Run tests locally to ensure they pass.
7.  Push your feature branch to the remote: `git push origin feature/my-new-feature`.
8.  Open a Pull Request against the `develop` branch.
9.  Participate in code review and address feedback.
10. Once approved and tests pass in CI (if applicable), the PR is merged into `develop`.

### 10. Communication

-   Use project management tools (e.g., Jira, Trello, GitHub Issues) to track tasks and bugs.
-   Communicate with team members about ongoing work, potential blockers, and design decisions.

*(This document provides general guidelines. Specific project teams may have additional or slightly different conventions.)*

---

## Troubleshooting

This guide covers common issues you may encounter while developing, deploying, or using the Japanese Learning Website.

### Common Issues

#### 1. Template Not Found Errors
```
jinja2.exceptions.TemplateNotFound: admin/admin_index.html
```
**Cause**: Template files are missing or in the wrong location.

**Solution**: 
- Ensure admin templates are in `app/templates/admin/`
- Check template file names match exactly (case-sensitive)
- Verify template inheritance is correct

```bash
# Check template structure
ls -la app/templates/
ls -la app/templates/admin/
```

#### 2. Route Building Errors
```
werkzeug.routing.exceptions.BuildError: Could not build url for endpoint 'list_kana'
```
**Cause**: Incorrect route endpoint reference in templates or redirects.

**Solution**: 
- Use correct route format `routes.list_kana` instead of `list_kana`
- Check route definitions in `app/routes.py`
- Verify blueprint registration

```python
# Correct usage in templates
{{ url_for('routes.list_kana') }}

# Correct usage in redirects
return redirect(url_for('routes.admin_index'))
```

#### 3. Database Connection Issues
```
sqlite3.OperationalError: no such table: user
```
**Cause**: Database not initialized, tables not created, or migrations not applied.

**Solution**:
1.  Ensure `instance/site.db` (or your configured DB) exists. If not, the setup script should create it.
2.  Run initial setup scripts if this is a fresh installation:
    ```bash
    python setup_unified_auth.py  # Creates initial tables and admin user
    python migrate_lesson_system.py # Seeds data and runs essential data migrations
    ```
3.  If you have made changes to models and have pending Alembic migrations:
    ```bash
    python run_migrations.py      # Applies pending Alembic migrations
    ```
    If you need to generate a new migration because you changed `app/models.py`:
    ```bash
    alembic revision -m "Your migration message"
    # Then review the generated script and run:
    python run_migrations.py
    ```

#### 4. Admin Access Denied
**Problem**: Can't access admin panel after login.

**Cause**: User doesn't have admin privileges.

**Solution**: 
```bash
# Create admin user
python create_admin.py

# Or manually set admin flag in database
sqlite3 instance/site.db
UPDATE user SET is_admin = 1 WHERE email = 'your-email@example.com';
```

#### 5. Static Files Not Loading
**Problem**: CSS/JS files return 404 or images don't display.

**Cause**: Static file configuration or path issues.

**Solution**:
- For Bootstrap CDN: Check internet connection and CDN links
- For custom static files: Verify `app/static/` directory structure
- For uploaded files: Check `UPLOAD_FOLDER` configuration and file paths

```bash
# Check static file structure
ls -la app/static/
ls -la app/static/css/
ls -la app/static/uploads/

# Verify upload folder permissions
chmod 755 app/static/uploads/
```

#### 6. File Upload Errors
**Problem**: File uploads fail or return errors.

**Causes & Solutions**:

##### Upload Directory Missing
```bash
# Create upload directories
mkdir -p app/static/uploads/lessons/images
mkdir -p app/static/uploads/lessons/audio
mkdir -p app/static/uploads/lessons/documents
```

##### File Size Limits
```python
# Check MAX_CONTENT_LENGTH in .env
MAX_CONTENT_LENGTH=16777216  # 16MB

# Or in app configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
```

##### File Type Restrictions
```python
# Check ALLOWED_EXTENSIONS configuration
ALLOWED_EXTENSIONS = {
    'image': {'png', 'jpg', 'jpeg', 'gif'},
    'audio': {'mp3', 'wav', 'ogg'},
    'document': {'pdf', 'doc', 'docx', 'txt'}
}
```

#### 7. CSRF Token Errors
```
The CSRF token is missing or invalid
```
**Cause**: CSRF protection failing on form submissions.

**Solution**:
```html
<!-- Ensure CSRF token in forms -->
{{ form.hidden_tag() }}
<!-- or -->
{{ form.csrf_token }}
```

```javascript
// For AJAX requests, include CSRF token
const csrfToken = document.querySelector('meta[name=csrf-token]').getAttribute('content');
fetch('/api/endpoint', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken
    },
    body: JSON.stringify(data)
});
```

#### 8. Import Errors
```
ModuleNotFoundError: No module named 'app'
```
**Cause**: Python path or virtual environment issues.

**Solution**:
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Check Python path
python -c "import sys; print(sys.path)"
```

#### 9. Database Migration Errors
```
Target database is not up to date
```
**Cause**: Migration conflicts or database state issues. Alembic may detect that the actual database schema doesn't match the migration history.

**Solution**:
1.  **Check current migration status**:
    ```bash
    alembic current
    alembic history
    ```
2.  **Ensure all migrations are applied**:
    ```bash
    python run_migrations.py
    ```
3.  **If the database is truly out of sync with Alembic's history (e.g., manual changes were made, or history is corrupted):**
    - **Option A: Stamp to current head (if DB schema matches models and latest migration)**
      If you are certain your database schema correctly reflects the state after all migrations, you can tell Alembic to consider the database as up-to-date:
      ```bash
      alembic stamp head
      ```
      *Use with caution. This doesn't change the schema; it just updates Alembic's version table.*
    - **Option B: More complex recovery (potentially requires manual intervention)**
      If migrations are genuinely corrupted or the DB is in an unknown state relative to migrations, recovery can be complex. This might involve:
        - Backing up your data.
        - Inspecting the `alembic_version` table in your database.
        - Potentially dropping tables and re-creating from scratch using `setup_unified_auth.py` and `python run_migrations.py` (losing data unless restored).
        - Or, carefully generating new migration scripts and manually adjusting them.
    - **Drastic Reset (Last Resort - Deletes Migration History and Data if not careful):**
      If you intend to start migrations from scratch and your database can be rebuilt (e.g., in development):
      ```bash
      # Warning: This path can lead to data loss if not handled carefully.
      # 1. Ensure your models in app/models.py are correct.
      # 2. Backup your database if it contains valuable data.
      # 3. Delete the migrations/versions/ directory's contents: rm -rf migrations/versions/*
      # 4. Drop all tables from your database (e.g., using a DB browser or `db.drop_all()` temporarily in a script).
      # 5. Run initial setup:
      python setup_unified_auth.py # Recreates tables based on models (like db.create_all())
      # 6. Stamp the database with an initial Alembic state (if `setup_unified_auth.py` doesn't do this):
      #    This might involve creating an initial migration for an empty DB or stamping a base.
      #    Often, the first 'real' migration is generated against the tables created by setup_unified_auth.py.
      # 7. Generate a new "initial" migration if needed, or proceed to generate migrations for model changes.
      #    If `setup_unified_auth.py` creates tables, your first Alembic revision might be empty or reflect those tables.
      #    `alembic revision -m "establish baseline from existing tables"`
      #    You might need to edit this script to reflect the current state if autogenerate doesn't capture it.
      #    Then `python run_migrations.py`
      ```
      *This "drastic reset" is complex and error-prone. It's usually better to fix specific migration issues.*

#### 10. Permission Errors
**Problem**: Access denied errors when accessing files or directories.

**Solution**:
```bash
# Fix file permissions
chmod 644 app/static/uploads/lessons/images/*
chmod 755 app/static/uploads/lessons/images/

# Fix directory ownership (if needed)
chown -R www-data:www-data app/static/uploads/
```

### Debug Mode

#### Enable Debug Mode
```env
# In .env file
FLASK_DEBUG=True
FLASK_ENV=development
```

#### Debug Information
- Detailed error pages with stack traces
- Auto-reload on code changes
- Interactive debugger in browser

**Warning**: Never enable debug mode in production!

### Logging

#### Enable Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# In app/__init__.py
if not app.debug:
    # Production logging setup
    import logging
    from logging.handlers import RotatingFileHandler
    
    file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
```

#### Check Logs
```bash
# View application logs
tail -f logs/app.log

# View Flask development server logs
# (displayed in terminal where flask run is executed)
```

### Database Issues

#### Database Locked
```
sqlite3.OperationalError: database is locked
```
**Solution**:
```bash
# Check for running processes
ps aux | grep python

# Kill any hanging processes
pkill -f "flask run"

# Restart the application
flask run
```

#### Database Corruption
```bash
# Check database integrity
sqlite3 instance/site.db "PRAGMA integrity_check;"

# Backup and restore if needed
cp instance/site.db instance/site.db.backup
sqlite3 instance/site.db ".dump" | sqlite3 instance/site_new.db
mv instance/site_new.db instance/site.db
```

### Performance Issues

#### Slow Database Queries
```python
# Enable SQL query logging
app.config['SQLALCHEMY_ECHO'] = True

# Add database indexes
class User(db.Model):
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
```

#### Memory Issues
```bash
# Monitor memory usage
top -p $(pgrep -f "flask run")

# Check for memory leaks
python -m memory_profiler app.py
```

### Network Issues

#### Port Already in Use
```
OSError: [Errno 48] Address already in use
```
**Solution**:
```bash
# Find process using port 5000
lsof -i :5000

# Kill the process
kill -9 <PID>

# Or use a different port
flask run --port 5001
```

#### CORS Issues
```javascript
// If making requests from different domains
// Add CORS headers in Flask
from flask_cors import CORS
CORS(app)
```

### Environment Issues

#### Wrong Python Version
```bash
# Check Python version
python --version

# Use specific Python version
python3.8 -m venv venv
```

#### Missing Environment Variables
```bash
# Check if .env file exists
ls -la .env

# Verify environment variables are loaded
python -c "import os; print(os.environ.get('SECRET_KEY'))"
```

### Production Issues

#### 500 Internal Server Error
**Check**:
1. Application logs
2. Web server logs (nginx/apache)
3. Database connectivity
4. File permissions
5. Environment variables

#### Static Files Not Served
```nginx
# Nginx configuration for static files
location /static {
    alias /path/to/app/static;
    expires 1y;
    add_header Cache-Control "public, immutable";
}

location /uploads {
    alias /path/to/upload/folder;
    expires 1y;
    add_header Cache-Control "public";
}
```

### Getting Help

#### Information to Gather
When reporting issues, include:
1. Error message (full stack trace)
2. Steps to reproduce
3. Environment details (OS, Python version)
4. Configuration files (without secrets)
5. Log files

#### Useful Commands
```bash
# System information
python --version
pip list
flask --version

# Application status
flask routes  # Still useful for showing Flask routes
flask shell

# Database information (Alembic)
alembic current
alembic history
# alembic show <revision_id> # To show details of a specific revision
```

### Debug Commands
```bash
# Test database connection
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); print(db.engine.execute('SELECT 1').scalar())"

# Test file upload configuration
python -c "from app import create_app; app = create_app(); print(app.config['UPLOAD_FOLDER'])"

# Test user authentication
python -c "from app.models import User; print(User.query.first())"
```

### Prevention

#### Best Practices
1. **Version Control**: Commit working states frequently
2. **Backups**: Regular database and file backups
3. **Testing**: Test changes in development first
4. **Monitoring**: Set up application monitoring
5. **Documentation**: Keep configuration documented

#### Health Checks
```python
# Add health check endpoint
@app.route('/health')
def health_check():
    try:
        # Test database
        db.session.execute('SELECT 1')
        
        # Test file system
        upload_folder = app.config['UPLOAD_FOLDER']
        if not os.path.exists(upload_folder):
            return {'status': 'error', 'message': 'Upload folder missing'}, 500
            
        return {'status': 'healthy'}, 200
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500

---

## Lesson System Architecture

### 1. Overview

The Japanese Learning Website features a robust and flexible lesson system designed to deliver structured educational content to users. This system allows administrators to create rich, multi-page lessons combining various types of content, including core Japanese language elements (Kana, Kanji, Vocabulary, Grammar), multimedia (text, images, video, audio), and interactive quizzes. Users can progress through lessons, and their progress is tracked.

### 2. Core Components & Models

The lesson system is primarily built around the following SQLAlchemy models (defined in `app/models.py`):

-   **`LessonCategory`**: Organizes lessons into logical groups (e.g., "Hiragana Basics," "JLPT N5 Grammar").
-   **`Lesson`**: Represents a single unit of learning. It contains metadata like title, description, type (free/premium), difficulty, and links to its content and pages.
-   **`LessonPage`**: Defines individual pages within a lesson, allowing for a multi-page structure. Each page can have an optional title and description.
-   **`LessonContent`**: Represents an individual piece of content displayed on a `LessonPage`. This is a versatile model that can link to core content types (Kana, Kanji, etc.), store custom text, link to media files, or define interactive quizzes.
-   **`LessonPrerequisite`**: Manages dependencies between lessons, requiring users to complete certain lessons before accessing others.
-   **`UserLessonProgress`**: Tracks an individual user's progress through a specific lesson, including completion status, percentage, and progress on individual content items.
-   **`QuizQuestion`**, **`QuizOption`**, **`UserQuizAnswer`**: Support interactive quiz functionality within lessons. (Covered in more detail in quiz-specific documentation, but part of the lesson content).

### 3. Lesson Structure

#### 3.1. Categories
- Lessons are grouped into `LessonCategory` instances.
- Categories help users find relevant content and provide organizational structure for administrators.
- Each category can have a name, description, and a color code for UI theming.

#### 3.2. Lessons
- Each `Lesson` belongs to a `LessonCategory` (optional, but recommended).
- Key attributes of a `Lesson`:
    - `title`, `description`
    - `lesson_type` ('free' or 'premium'): Controls access based on user subscription.
    - `difficulty_level`, `estimated_duration`
    - `order_index`: For ordering lessons within a category or globally.
    - `is_published`: Controls visibility to end-users.
    - `thumbnail_url`, `video_intro_url`: For presentation.

#### 3.3. Lesson Pages
- A `Lesson` is composed of one or more `LessonPage`s.
- The `LessonPage` model stores `page_number`, `title` (optional), and `description` (optional) for each page.
- This allows for content to be broken down into manageable segments.
- The `Lesson.pages` property dynamically groups `LessonContent` items by their `page_number` and associates them with `LessonPage` metadata.

#### 3.4. Lesson Content Items
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

### 4. Content Creation and Management (Admin Flow)

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

### 5. Lesson Consumption (User Flow)

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

### 6. Key Functionalities and Logic

#### 6.1. Prerequisites (`Lesson.is_accessible_to_user()`)
- This method in the `Lesson` model checks if a user has completed all lessons listed in its `prerequisites` relationship by looking up the `UserLessonProgress` for that user and each prerequisite lesson.

#### 6.2. Content Ordering and Pagination (`Lesson.pages` property)
- This dynamic property on the `Lesson` model is crucial for rendering.
- It fetches all `LessonContent` items for the lesson.
- It also fetches all `LessonPage` metadata entries for the lesson.
- It sorts content items first by `page_number`, then by their `order_index` within that page.
- It groups these sorted content items under their respective page numbers.
- It associates the `LessonPage` metadata (title, description) with each page group.
- The result is a list of page structures, each containing its metadata and an ordered list of its content.

#### 6.3. Progress Tracking (`UserLessonProgress` methods)
- `get_content_progress()` / `set_content_progress()`: Manage the JSON dictionary storing completion status of individual `LessonContent` items.
- `mark_content_completed(content_id)`: Updates the JSON and calls `update_progress_percentage()`.
- `update_progress_percentage()`: Calculates overall lesson completion based on the number of completed (non-optional, though this distinction might need explicit handling if not all content counts towards completion) `LessonContent` items. Sets `is_completed` if 100%.
- `reset()`: Clears progress for a lesson, including associated quiz answers.

#### 6.4. Serving Uploaded Files (`LessonContent.get_file_url()` and `routes.uploaded_file`)
- Uploaded files are stored relative to `UPLOAD_FOLDER`.
- `LessonContent.file_path` stores this relative path.
- `get_file_url()` generates a URL using `url_for('routes.uploaded_file', filename=self.file_path)`.
- A dedicated route (e.g., `/uploads/<path:filename>`) in `app/routes.py` uses `send_from_directory` to securely serve files from the `UPLOAD_FOLDER`.

### 7. Extensibility

-   **New Content Types**: New `content_type` values can be added to `LessonContent`. The `get_content_data()` method and admin interface would need updates to support linking or displaying these new types.
-   **Advanced Interactivity**: The `QuizQuestion` and `QuizOption` models can be extended or new models created for more complex interactions beyond simple quizzes.
-   **Learning Path Algorithms**: The prerequisite system can be expanded for more dynamic learning path generation.

This system provides a solid foundation for delivering diverse educational content in a structured and trackable manner.

## Future Roadmap

This document outlines planned features, enhancements, and technical improvements for the Japanese Learning Website.

### Planned Features

#### 1. Enhanced Learning Tools

##### Spaced Repetition System (SRS)
- **Intelligent Review Scheduling**: Implement algorithms to optimize review timing based on user performance.
- **Forgetting Curve Integration**: Use Ebbinghaus forgetting curve principles for optimal retention.
- **Adaptive Difficulty**: Adjust review frequency based on individual learning patterns.
- **Progress Analytics**: Track long-term retention and learning efficiency.

##### Advanced Quiz System & Interactive Content
- **Current Implementation**: The platform already supports interactive quiz questions within lessons, including:
    - Multiple Choice
    - Fill-in-the-Blank
    - True/False
- **Future Enhancements**:
    - Additional Question Types: Drag and drop exercises, audio recognition quizzes, handwriting practice (stroke order), matching exercises.
    - Adaptive Testing: Questions adjust difficulty based on performance.
    - Detailed Analytics: Performance tracking across different question types.
    - Timed Challenges: Speed-based learning exercises.

##### Audio Integration
- **Current Implementation**: Supports uploading and embedding audio files in lessons.
- **Future Enhancements**:
    - Native Pronunciation Support: Library of high-quality audio for core content.
    - Speech Recognition: User pronunciation assessment.
    - Audio Lessons: Dedicated listening comprehension exercises.
    - Pronunciation Scoring: AI-powered pronunciation feedback.

##### Lesson Analytics
- **Detailed Learning Analytics**: Comprehensive progress tracking
- **Learning Path Optimization**: AI-suggested learning sequences
- **Performance Insights**: Identify strengths and weaknesses
- **Study Recommendations**: Personalized study suggestions
- **Adaptive Learning System**: AI-powered analysis of user performance to generate personalized lessons and study plans.
- **Content Validation Framework**: Automated validation of content for linguistic accuracy, cultural context, and educational effectiveness.

#### 2. Content Improvements

##### Content Versioning
- **Version Control**: Track content changes over time.
- **Rollback Capability**: Revert to previous content versions.
- **Change History**: Audit trail for all content modifications.
- **Collaborative Editing**: Features to support multiple administrators creating and editing content.

##### Bulk Import/Export
- **Current Status**: Functionality for lesson export and import (likely JSON-based) is available via `app/lesson_export_import.py`.
- **Future Enhancements**:
    - Broader CSV/JSON support for various content types beyond full lessons.
    - Content templates for standardized bulk creation.
    - Batch operations for efficient bulk updates across multiple content items.
    - Robust data migration tools for transferring content between different system instances or versions.

##### Advanced Prerequisites
- **Current Implementation**: Basic lesson prerequisites are supported (one lesson depending on another).
- **Future Enhancements**:
    - Complex Logic: AND/OR prerequisite combinations.
- **Skill-Based Prerequisites**: Requirements based on demonstrated skills
- **Adaptive Pathways**: Dynamic learning path adjustments
- **Prerequisite Recommendations**: AI-suggested learning sequences

##### Lesson Templates
- **Reusable Structures**: Standardized lesson formats
- **Template Library**: Collection of proven lesson patterns
- **Custom Templates**: Admin-created lesson structures
- **Template Sharing**: Community template exchange

#### 3. User Experience Enhancements

##### Mobile Application
- **Native iOS App**: Full-featured iPhone/iPad application
- **Native Android App**: Optimized Android experience
- **Cross-Platform Sync**: Seamless progress synchronization
- **Offline Capabilities**: Download content for offline study

##### Offline Mode
- **Content Download**: Cache lessons for offline access
- **Progress Sync**: Automatic sync when connection restored
- **Offline Analytics**: Track offline learning progress
- **Smart Caching**: Intelligent content pre-loading

##### Dark Mode
- **Alternative UI Theme**: Eye-friendly dark interface
- **Automatic Switching**: Time-based or system preference
- **Customizable Themes**: User-selectable color schemes
- **Accessibility Compliance**: Enhanced readability options

##### Accessibility Improvements
- **WCAG Compliance**: Full accessibility standard compliance
- **Screen Reader Support**: Enhanced assistive technology support
- **Keyboard Navigation**: Complete keyboard accessibility
- **High Contrast Mode**: Improved visibility options
- **Font Size Controls**: User-adjustable text sizing

#### 4. Administrative Features

##### User Management
- **Admin User Controls**: Comprehensive user account management
- **Role Management**: Granular permission system
- **User Analytics**: Detailed user behavior insights
- **Bulk User Operations**: Efficient user management tools

##### Analytics Dashboard
- **Usage Statistics**: Comprehensive platform analytics
- **Learning Insights**: Educational effectiveness metrics
- **Performance Monitoring**: System health and performance
- **Custom Reports**: Configurable analytics reports

##### Content Moderation
- **Review Workflows**: Content approval processes
- **Quality Assurance**: Automated content validation
- **Community Contributions**: User-generated content management
- **Moderation Tools**: Efficient content review interfaces

##### Backup/Restore
- **Automated Backups**: Scheduled data protection
- **Point-in-Time Recovery**: Restore to specific timestamps
- **Cloud Backup Integration**: External backup storage
- **Disaster Recovery**: Comprehensive recovery procedures

#### 5. Technical Improvements

##### API Documentation
- **Swagger/OpenAPI Integration**: Implement interactive API documentation using tools like Swagger or OpenAPI.
- **Code Examples**: Provide comprehensive usage examples for all API endpoints.
- **SDK Development**: Consider developing client libraries for common languages to facilitate API integration.
- **API Versioning**: Establish a strategy for backward-compatible API evolution.

##### Automated Testing
- **Unit Test Suite**: Develop a comprehensive suite of unit tests to ensure code correctness and maintainability. Aim for high code coverage.
- **Integration Tests**: Implement integration tests to verify end-to-end functionality of key application flows.
- **Performance Tests**: Conduct load and stress testing to identify and address performance bottlenecks.
- **Automated QA**: Integrate automated quality assurance checks into the development lifecycle.

##### CI/CD Pipeline
- **Automated Deployment**: Establish a CI/CD pipeline for streamlined and automated releases to various environments (staging, production).
- **Environment Management**: Ensure consistent and reproducible deployment environments.
- **Rollback Capabilities**: Implement mechanisms for quick reversion of deployments in case of issues.
- **Quality Gates**: Incorporate automated quality checks (e.g., running tests, linters) into the pipeline before deployment.

##### Performance Optimization
- **Caching Layer**: Explore and implement caching strategies (e.g., using Redis) for frequently accessed data, sessions, and content.
- **Database Optimization**: Continuously monitor and optimize database queries, ensure proper indexing, and consider connection pooling.
- **CDN Integration**: Utilize a Content Delivery Network (CDN) for serving static assets (CSS, JS, images) to improve load times for global users.
- **Load Balancing**: Design the application to support horizontal scaling with load balancers for high availability and performance.

### Scalability Considerations

#### Database Migration & Scaling
- **PostgreSQL/MySQL Transition**: Plan and execute migration from SQLite to a more robust relational database like PostgreSQL or MySQL for production environments. Alembic is already in use, facilitating this.
- **Database Clustering**: For very high availability, explore database clustering solutions.
- **Read Replicas**: Implement read replicas to offload read-heavy queries and improve performance.
- **Sharding Strategy**: For extreme scale, investigate database sharding strategies.

#### Caching Layer
- **Redis Implementation**: Implement Redis for session management and application-level caching.
- **Cache Strategies**: Define intelligent caching policies (e.g., cache-aside, write-through) based on data access patterns.
- **Cache Invalidation**: Develop robust mechanisms for cache invalidation to ensure data consistency.
- **Distributed Caching**: For multi-server deployments, use a distributed caching solution.

#### CDN Integration
- **Static Asset Delivery**: Serve all static assets (CSS, JavaScript, images, non-dynamic uploaded files) via a CDN.
- **Image Optimization**: Leverage CDN features for automatic image optimization and format conversion.
- **Video Streaming**: If video content is significant, use CDN capabilities for efficient video streaming.
- **Edge Computing**: Explore using edge servers for computations closer to the user to reduce latency.

#### Load Balancing
- **Multiple Server Instances**: Deploy the application across multiple server instances.
- **Health Monitoring**: Implement health checks for application instances to enable automatic failover.
- **Session Affinity**: Configure session affinity (sticky sessions) if necessary, though stateless design is preferred.
- **Auto-scaling**: Implement auto-scaling based on traffic load to dynamically adjust resource allocation.

### Integration Opportunities

#### External APIs
- **Dictionary Services**: Integrate with established Japanese dictionary APIs (e.g., Jisho.org API if available, or other services).
- **Translation APIs**: Incorporate machine translation services for helper text or content localization.
- **Speech APIs**: Utilize advanced third-party speech recognition and synthesis APIs.
- **AI Services for Content Enhancement**:
    - **Current Implementation**: The platform uses `app/ai_services.py` to integrate with OpenAI for AI-assisted lesson content generation (e.g., example sentences, explanations).
    - **Future Enhancements**: Expand AI integration for more sophisticated features like automated question generation, personalized feedback, or adaptive learning path suggestions.

#### Social Features
- **User Communities**: Learning groups and forums
- **Progress Sharing**: Social learning motivation
- **Collaborative Learning**: Peer-to-peer learning features
- **Leaderboards**: Gamification elements

#### Payment Processing
- **Subscription Billing**: Automated payment processing
- **Multiple Payment Methods**: Flexible payment options
- **Billing Analytics**: Revenue and subscription insights
- **Promotional Codes**: Marketing and discount capabilities

#### Email Services
- **Automated Notifications**: Learning reminders and updates
- **Newsletter System**: Educational content delivery
- **Transactional Emails**: Account and progress notifications
- **Email Templates**: Professional communication design

### Implementation Timeline

#### Phase 1: Foundation (Months 1-3)
- Enhanced quiz system implementation
- Basic analytics dashboard
- Mobile-responsive improvements
- API documentation

#### Phase 2: Core Features (Months 4-6)
- Spaced repetition system
- Audio integration basics
- User management enhancements
- Performance optimizations

#### Phase 3: Advanced Features (Months 7-9)
- Mobile application development
- Advanced analytics
- Content versioning system
- Automated testing implementation

#### Phase 4: Scale & Polish (Months 10-12)
- Production database migration
- CDN integration
- Advanced accessibility features
- Comprehensive security audit

### Success Metrics

#### User Engagement
- **Daily Active Users**: Consistent platform usage
- **Session Duration**: Extended learning sessions
- **Lesson Completion Rate**: High completion percentages
- **User Retention**: Long-term user engagement

#### Educational Effectiveness
- **Learning Progress**: Measurable skill improvement
- **Knowledge Retention**: Long-term learning success
- **User Satisfaction**: Positive feedback and ratings
- **Achievement Rates**: Goal completion statistics

#### Technical Performance
- **System Uptime**: 99.9% availability target
- **Response Times**: Sub-second page loads
- **Error Rates**: Minimal system errors
- **Scalability**: Support for growing user base

### Business Metrics
- **User Growth**: Steady user acquisition
- **Subscription Conversion**: Free to premium upgrades
- **Revenue Growth**: Sustainable business model
- **Market Position**: Competitive advantage

### Risk Mitigation

#### Technical Risks
- **Scalability Challenges**: Proactive performance monitoring
- **Security Vulnerabilities**: Regular security audits
- **Data Loss**: Comprehensive backup strategies
- **Integration Failures**: Thorough testing procedures

#### Business Risks
- **Market Competition**: Continuous feature innovation
- **User Churn**: Engagement optimization
- **Revenue Sustainability**: Diversified monetization
- **Regulatory Compliance**: Proactive compliance monitoring

### Community Involvement

#### Open Source Contributions
- **Community Feedback**: User-driven feature development
- **Beta Testing Programs**: Early feature validation
- **Documentation Contributions**: Community-maintained docs
- **Feature Requests**: User-prioritized development

#### Educational Partnerships
- **Academic Institutions**: Educational content collaboration
- **Language Schools**: Professional educator input
- **Cultural Organizations**: Authentic content sources
- **Technology Partners**: Integration opportunities

This roadmap represents our vision for the future of the Japanese Learning Website. Priorities may shift based on user feedback, market conditions, and technical considerations. Regular roadmap reviews ensure alignment with user needs and business objectives.

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
