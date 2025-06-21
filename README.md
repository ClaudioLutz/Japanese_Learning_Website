# Japanese Learning Website - Admin Dashboard MVP

This project is the Minimum Viable Product (MVP) for an admin dashboard designed to allow a non-technical person to add and manage content for a Japanese learning website.

The ideas for the full website are detailed in `brainstorming.md`. This MVP focuses solely on the backend and a simple admin interface for content management.

## Current Features

*   **Content Management for:**
    *   Kana (Hiragana, Katakana)
    *   Kanji
    *   Vocabulary
    *   Grammar Rules
*   **CRUD Operations:** Admins can Create, Read, Update, and Delete entries for each content type.
*   **Admin Dashboard:** A web interface for managing content.
*   **Basic Authentication:** The admin dashboard is protected by a simple username/password login.

## Technology Stack

*   **Backend:** Python (Flask)
*   **Database:** SQLite (file-based, `japanese_learning.db` will be created in the root directory)
*   **Frontend (Admin Interface):** HTML, CSS, JavaScript (served by Flask templates)
*   **ORM:** Flask-SQLAlchemy

## Setup and Running the Application

1.  **Clone the repository (if you haven't already):**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv venv
    ```
    *   On macOS/Linux: `source venv/bin/activate`
    *   On Windows: `venv\Scripts\activate`

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the Flask development server:**
    ```bash
    python app.py
    ```
    The application will start, and the database file (`japanese_learning.db`) will be created if it doesn't exist.

5.  **Access the Admin Dashboard:**
    Open your web browser and go to `http://127.0.0.1:5000/` (it will redirect to `/admin/login`).

6.  **Admin Login:**
    *   **Username:** `admin`
    *   **Password:** `password123`
    (These are hardcoded in `app.py` for this MVP).

    Upon successful login, you will be redirected to the admin dashboard home page (`http://127.0.0.1:5000/admin/`). From there, you can navigate to manage Kana, Kanji, Vocabulary, and Grammar.

## Project Structure

```
├── app.py                  # Main Flask application, includes models, routes, and API logic
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── AGENTS.md               # Instructions for AI agents working on this project
├── brainstorming.md        # Initial ideas for the full learning platform
├── japanese_learning.db    # SQLite database file (created on first run)
├── static/                 # Static assets (CSS, JS - currently minimal)
│   ├── css/
│   └── js/
└── templates/              # HTML templates (Jinja2)
    └── admin/
        ├── base_admin.html         # Base template for admin pages
        ├── admin_index.html        # Admin dashboard home
        ├── login.html              # Admin login page
        ├── manage_kana.html        # Page for managing Kana
        ├── manage_kanji.html       # Page for managing Kanji
        ├── manage_vocabulary.html  # Page for managing Vocabulary
        └── manage_grammar.html     # Page for managing Grammar
```

## For AI Agents

Please refer to `AGENTS.md` for specific instructions and conventions when working on this codebase.

## Future Development (Post-MVP)

This MVP lays the groundwork. Future development could include:
*   Developing the student-facing frontend.
*   Implementing more sophisticated content features (e.g., audio uploads, stroke order diagrams).
*   Adding user accounts for students.
*   Implementing learning features like SRS (Spaced Repetition System).
*   Migrating to a more robust database like PostgreSQL.
*   Enhancing security and authentication.

Refer to `brainstorming.md` for a broader list of potential features.
