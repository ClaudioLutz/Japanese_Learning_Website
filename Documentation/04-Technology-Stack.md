# Technology Stack & Design Decisions

This section outlines the key technologies used in the project and the rationale behind their selection.

## Core Backend Technologies

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
| **Alembic**       | >=1.7.0 (Typical)                 | SQLAlchemy database migrations                | Manages database schema changes over time, allowing for versioning and incremental updates to the database structure. Direct usage.        |
| **python-dotenv** | >=0.19.0                          | Environment variable management               | Loads environment variables from a `.env` file for configuration (e.g., `SECRET_KEY`, `DATABASE_URL`).                                       |
| **OpenAI**        | >=0.27.0 (Example, check reqs)    | AI API Interaction                            | Used by `app/ai_services.py` to connect to OpenAI's API for features like AI-assisted lesson content generation.                             |

## Core Frontend Technologies

| Technology            | Version         | Purpose                                     | Design Rationale                                                                                                                            |
|-----------------------|-----------------|---------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| **HTML5**             | N/A             | Structure of web pages                      | Standard markup language for web content.                                                                                                   |
| **CSS3**              | N/A             | Styling of web pages                        | Standard for styling, used in conjunction with Bootstrap. Custom CSS in `app/static/css/custom.css`.                                        |
| **JavaScript (ES6+)** | N/A             | Client-side interactivity, AJAX             | Used for dynamic UI updates, modal handling, AJAX requests to API endpoints, and managing interactive lesson components. No large JS framework. |
| **Bootstrap**         | 5.3.3 (CDN)     | Responsive UI framework, pre-built components | Provides a responsive grid system, styling for common UI elements (forms, buttons, modals), accelerating frontend development.              |
| **Jinja2**            | (Flask default) | Templating engine                           | Server-side template rendering, allows embedding Python logic in HTML, provides template inheritance, auto-escaping for XSS protection.       |

## File Handling & Processing

| Technology        | Version (from `requirements.txt`) | Purpose                                     | Design Rationale                                                                                                                        |
|-------------------|-----------------------------------|---------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------|
| **Pillow**        | >=9.0.0                           | Image processing                            | Used by `FileUploadHandler` for opening, resizing, and optimizing uploaded images (e.g., converting format, creating thumbnails).        |
| **python-magic**  | >=0.4.24                          | File type identification (MIME types)       | Used by `FileUploadHandler` to validate file content by checking its actual MIME type, rather than relying solely on file extension.     |
| **python-magic-bin**| >=0.4.14                          | Windows binaries for python-magic           | Dependency for `python-magic` to work correctly on Windows environments.                                                                |

## Database

| Technology        | Version         | Purpose                                     | Design Rationale                                                                                                                            |
|-------------------|-----------------|---------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| **SQLite**        | (Python default)| Development and default production database | Simple, file-based database, zero-configuration, suitable for development and small to medium-scale applications. Easy to set up and manage. |
| **Alembic**       | Direct Usage    | Database schema migration tool              | Handles versioning of the database schema, allowing for controlled evolution of table structures. Integrated via `migrations/` directory.   |

## Design Choices & Justifications

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
