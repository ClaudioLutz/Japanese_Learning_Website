# Security Implementation Details

## 1. Overview

This document outlines the key security measures and practices implemented within the Japanese Learning Website to protect user data, ensure application integrity, and prevent common web vulnerabilities. Security is a multi-layered approach, encompassing authentication, authorization, input validation, data protection, and secure configuration.

*(Many of these aspects are also touched upon in `03-System-Architecture.md` and `07-User-Authentication.md`. This document aims to consolidate and elaborate on them from a security perspective.)*

## 2. Authentication and Session Management

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

## 3. Authorization (Access Control)

-   **Role-Based Access Control (RBAC)**:
    -   `User.is_admin` (Boolean): Differentiates administrators from regular users.
    -   `User.subscription_level` (String: 'free', 'premium'): Controls access to premium content.
-   **Decorators**: Custom decorators are used to protect routes:
    -   `@login_required` (from Flask-Login): Ensures a user is authenticated.
    -   `@admin_required`: Custom decorator checking `current_user.is_admin`.
    -   `@premium_required`: Custom decorator checking `current_user.subscription_level`.
-   **Granular Checks**: Within views and templates, `current_user` attributes are checked to control access to specific features or data.

## 4. Input Validation and Sanitization

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

## 5. CSRF (Cross-Site Request Forgery) Protection

-   **Flask-WTF**: Provides built-in CSRF protection for all forms.
    -   A hidden CSRF token field (`{{ form.csrf_token }}` or `{{ form.hidden_tag() }}`) is included in forms.
    -   This token is validated on the server for all POST, PUT, DELETE requests originating from forms.
-   **AJAX Requests**: For AJAX requests that modify state, the CSRF token must be included in the request headers (e.g., `X-CSRFToken`).
-   **`CSRFTokenForm`**: Used for actions triggered by POST requests that don't have other form fields (e.g., lesson reset, subscription changes) to ensure they are also CSRF-protected.

## 6. Data Protection

-   **Database**:
    -   SQLAlchemy ORM helps prevent SQL injection vulnerabilities by parameterizing queries. Direct construction of SQL queries with user input is avoided.
    -   Sensitive data in the database (beyond passwords) should be encrypted if necessary, though current models do not indicate this for other fields.
-   **Configuration Secrets**:
    -   `SECRET_KEY`, `DATABASE_URL` (with credentials), `OPENAI_API_KEY` are stored in a `.env` file, which is not committed to version control.
    -   These are loaded as environment variables.
-   **File System**:
    -   Uploaded files are stored in a designated `UPLOAD_FOLDER`.
    -   Direct execution of uploaded files is prevented. Files are served via a controlled Flask route (`routes.uploaded_file`) that performs path validation.

## 7. Error Handling and Logging

-   **Debug Mode**: `FLASK_DEBUG=False` in production to prevent exposure of sensitive debug information.
-   **Error Pages**: Custom error pages (e.g., for 404, 500 errors) can be configured to avoid leaking internal details.
-   **Logging**: Comprehensive logging (see `16-Troubleshooting.md`) helps in identifying and diagnosing security incidents or suspicious activity. Sensitive information should be filtered from logs.

## 8. Secure Headers

While not explicitly detailed in `app/__init__.py` setup, for production deployments, consider adding security-related HTTP headers, often via a WSGI middleware or web server configuration (e.g., Nginx):
-   **`X-Content-Type-Options: nosniff`**: Prevents browsers from MIME-sniffing a response away from the declared content type.
-   **`X-Frame-Options: DENY` or `SAMEORIGIN`**: Protects against clickjacking attacks.
-   **`Content-Security-Policy (CSP)`**: A powerful header to control resources the browser is allowed to load, mitigating XSS and data injection attacks.
-   **`HTTP Strict Transport Security (HSTS)`**: Enforces secure (HTTPS) connections to the server.

## 9. Regular Audits and Updates

-   **Dependency Management**: Regularly update dependencies listed in `requirements.txt` to patch known vulnerabilities. Tools like `pip-audit` can help.
-   **Code Reviews**: Security considerations should be part of code reviews.
-   **Security Scans**: Periodically run security scanning tools against the application.

## 10. Specific Feature Security

### 10.1. AI Content Generation (`app/ai_services.py`)
-   **API Key Security**: `OPENAI_API_KEY` is managed as an environment secret.
-   **Input to AI**: Data sent to OpenAI (topic, difficulty, keywords) is based on admin input for content generation and does not include user PII from the application's user base.
-   **Output Handling**: Content received from AI is subject to admin review and editing before being saved and displayed.

*(This document provides a summary of key security implementations. Continuous vigilance and updates are necessary to maintain a secure application.)*
