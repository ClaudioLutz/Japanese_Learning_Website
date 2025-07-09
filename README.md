# Japanese Learning Website - Complete Learning Platform

A comprehensive web-based Japanese learning platform featuring structured lessons, content management, user authentication, and progress tracking. The platform supports both free and premium content with a complete lesson system.

## 🌟 Key Features

### 📚 **Comprehensive Lesson System**
- **Structured Lessons** - Create lessons combining Kana, Kanji, Vocabulary, Grammar, and multimedia content
- **Paginated Content** - Organize lesson content into multiple pages for better learning flow
- **Carousel Navigation** - Swipe-friendly page navigation with manual controls (no auto-scrolling)
- **Categories & Organization** - Organize lessons into color-coded categories
- **Prerequisites** - Set lesson dependencies for progressive learning
- **Free & Premium Content** - Subscription-based access control
- **Progress Tracking** - Detailed user progress with completion percentages
- **Interactive Content** - Quiz questions with multiple choice, fill-in-the-blank, and true/false formats

### 👥 **User Management**
- **User Registration & Authentication** - Secure user accounts with Flask-Login
- **Subscription Tiers** - Free and Premium user levels
- **Admin Panel** - Complete administrative interface for content management
- **Role-Based Access** - Different permissions for users and administrators

### 📖 **Content Management**
- **Kana (Hiragana & Katakana)** - Character learning with romanization
- **Kanji** - Chinese characters with readings, meanings, and JLPT levels
- **Vocabulary** - Words with readings, meanings, and example sentences
- **Grammar** - Grammar rules with explanations and examples
- **Multimedia Support** - Text, images, videos, and audio content (URL-based and direct file uploads)

### 📊 **Learning Features**
- **Interactive Lessons** - Step-by-step lesson progression with paginated content
- **Carousel Interface** - Swipe through lesson pages with intuitive navigation controls
- **Page Management** - Organize content into logical pages for better learning flow
- **Progress Tracking** - Individual content completion tracking across all pages
- **Time Monitoring** - Track time spent on lessons
- **Completion Certificates** - Visual completion indicators
- **Filtering & Search** - Find lessons by category, difficulty, and type
- **Manual Navigation** - User-controlled page transitions (no auto-scrolling)

## 🛠️ Technology Stack

- **Backend:** Python (Flask)
- **Database:** SQLite (easily upgradeable to PostgreSQL/MySQL)
- **Frontend:** HTML5, CSS3, JavaScript (ES6+), Bootstrap 5.3.3
- **Authentication:** Flask-Login with secure session management
- **ORM:** SQLAlchemy with Flask-SQLAlchemy
- **Forms:** Flask-WTF with CSRF protection

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)
- Git

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd Japanese_Learning_Website
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up the database and initial content:**
   ```bash
   # Initialize database, create tables, and set up default admin user
   python setup_unified_auth.py
   
   # Seed database with initial lesson categories and sample lessons
   python migrate_lesson_system.py
   ```
   *The `setup_unified_auth.py` script will create a default admin user (admin@example.com / admin123). You can use `python create_admin.py` if you need to create additional admin users.*

5. **Run the application:**
   ```bash
   python run.py
   ```

6. **Access the application:**
   - **Main Site:** http://localhost:5000
   - **Admin Panel:** http://localhost:5000/admin (Login with default admin credentials)

### Default Admin Credentials
- **Email:** admin@example.com
- **Password:** admin123
- **Username:** admin
   *(A test user `user@example.com` / `password123` can be registered through the website's registration page.)*

## Project Structure

```
├── app/                    # Main Flask application package
│   ├── __init__.py         # Application factory, initializes Flask app and extensions
│   ├── forms.py            # WTForms definitions for login, registration, content management
│   ├── models.py           # SQLAlchemy database models for users, content, lessons
│   ├── routes.py           # Flask routes and view functions for user and admin interfaces
│   ├── utils.py            # Utility functions
│   └── templates/          # Jinja2 templates for rendering HTML pages
│       ├── admin/          # Templates specific to the admin panel
│       │   ├── admin_index.html
│       │   ├── base_admin.html
│       │   ├── login.html (Note: admin login might be unified or separate)
│       │   ├── manage_categories.html
│       │   ├── manage_grammar.html
│       │   ├── manage_kana.html
│       │   ├── manage_kanji.html
│       │   ├── manage_lessons.html
│       │   └── manage_vocabulary.html
│       ├── base.html       # Base template for user-facing pages
│       ├── free_content.html
│       ├── index.html      # Homepage
│       ├── lesson_view.html
│       ├── lessons.html
│       ├── login.html      # User login page
│       ├── premium_content.html
│       └── register.html   # User registration page
├── instance/               # Instance folder (typically contains database, config files)
│   └── site.db             # SQLite database file (primary database)
├── deprecated/             # Older or unused files
│   ├── AGENTS.md           # Deprecated agent instructions
│   ├── README.md           # Deprecated README
│   └── ...                 # Other deprecated files and templates
├── .gitignore              # Specifies intentionally untracked files that Git should ignore
├── ADMIN_CONTENT_CREATION_GUIDE.md # Guide for admins on creating content
├── Documentation.md        # Brief pointer to the Documentation/ directory (see below)
├── README.md               # This file - overview, setup, and quick start
├── create_admin.py         # Script to create additional admin users
├── lesson_models.py        # DEPRECATED: All models are consolidated in app/models.py
├── migrate_lesson_system.py # Script to seed initial lesson categories and sample lessons
├── requirements.txt        # Python package dependencies
├── run.py                  # Main script to run the Flask application
└── setup_unified_auth.py   # Script to set up the initial database schema and default admin user
```
*Note: While a general `app/static/` directory for project-wide CSS/JS might not be the primary focus (styling is largely handled by Bootstrap CDN), the application utilizes an `UPLOAD_FOLDER` (defaulting to `app/static/uploads/`) for storing and serving user-uploaded files (e.g., images, audio for lessons). These uploaded files are accessible via application routes.*

## Documentation

For comprehensive information about the project, including detailed setup, architecture, and component guides, please see the [**Full Project Documentation in the Documentation/ directory**](Documentation/README.md).

## For AI Agents

Please refer to `AGENTS.md` (if a current one exists at the root level) or general best practices for AI agent collaboration. The `deprecated/AGENTS.md` may contain outdated information.

## Future Development (Post-MVP)

This version includes foundational content management, a lesson system with file uploads, and user progress tracking. Future development could include:
*   Further developing the student-facing frontend and user experience.
*   Implementing more sophisticated content features (e.g., interactive quizzes, stroke order diagrams).
*   Enhancing the existing student progress tracking with more detailed analytics and reporting.
*   Implementing advanced learning features like Spaced Repetition Systems (SRS).
*   Migrating to a more robust database (e.g., PostgreSQL) for production environments.
*   Continuously enhancing security and authentication mechanisms.
*   Expanding API capabilities for potential third-party integrations or mobile applications.

Refer to `deprecated/brainstorming.md` for a broader list of potential features from earlier project phases.
