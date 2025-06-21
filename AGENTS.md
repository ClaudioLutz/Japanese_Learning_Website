## Agent Instructions for Japanese Learning Website

This document provides guidance for AI agents working on this project.

### Project Overview

This project is a Japanese learning website. The current focus is on building an admin dashboard that allows a non-technical person to easily add and manage learning content (Kana, Kanji, Vocabulary, Grammar).

### Technology Stack

*   **Backend:** Python (Flask)
*   **Database:** SQLite (initially, with plans to migrate to PostgreSQL)
*   **Frontend (Admin):** HTML, CSS, JavaScript (served by Flask templates)
*   **Key Libraries:** Flask-SQLAlchemy

### Running the Application

1.  **Set up a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run the Flask development server:**
    ```bash
    python app.py
    ```
    The application will typically be available at `http://127.0.0.1:5000/`.
    The admin panel is at `http://127.0.0.1:5000/admin/`.
    Admin login credentials (hardcoded for now):
    *   Username: `admin`
    *   Password: `password123`

### Development Conventions

*   **Database Models:** Defined in `app.py` using Flask-SQLAlchemy.
*   **Admin Routes (HTML):**
    *   Located in `app.py` under the "Admin Panel HTML Routes" section.
    *   Protected by the `@login_required` decorator.
    *   Templates are in `templates/admin/`.
*   **API Routes (JSON):**
    *   Located in `app.py` under the "API Routes (JSON)" section.
    *   Prefixed with `/api/admin/`. For example, `/api/admin/kana`.
    *   These are used by the JavaScript in the admin panel templates to perform CRUD operations.
    *   Currently, these API endpoints are not directly protected by the session-based login but rely on the admin pages that consume them being protected. For future development, consider adding token-based authentication to these APIs if they need to be accessed by other clients.
*   **Templates:** Use Jinja2 templating within Flask. Admin templates are in `templates/admin/` and inherit from `templates/admin/base_admin.html`.
*   **Static Files:** Located in the `static/` directory (e.g., `static/css`, `static/js`).
*   **Error Handling:** Basic error handling is in place for API routes (returning JSON errors) and Flask's flash messaging for UI feedback.
*   **Adding New Content Types:**
    1.  Define the new model in `app.py`.
    2.  Add CRUD API endpoints for the new model under the `/api/admin/` prefix.
    3.  Create a new HTML template in `templates/admin/` (e.g., `manage_newcontent.html`) similar to the existing ones, with JavaScript to interact with the new APIs.
    4.  Add a Flask route in `app.py` to serve this new HTML template, protecting it with `@login_required`.
    5.  Add a link to the new management page in `templates/admin/base_admin.html`.
    6.  Remember to run `db.create_all()` (implicitly done when `python app.py` is run if tables don't exist) or use Flask-Migrate (if integrated later) to update the database schema.

### Code Style & Quality

*   Follow PEP 8 for Python code.
*   Write clear and concise HTML, CSS, and JavaScript.
*   Comment complex logic.
*   Ensure forms are user-friendly, especially for non-technical users.

### Future Considerations (from brainstorming.md)

*   Migration to PostgreSQL.
*   More robust authentication (e.g., OAuth, proper password hashing).
*   Student-facing frontend (potentially with React/Vue).
*   Spaced Repetition System (SRS) integration.
*   Much more detailed content features (audio, stroke orders, etc.).

This `AGENTS.md` should be updated as the project evolves.Tool output for `create_file_with_block`:
