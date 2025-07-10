# Japanese Learning Website - Complete Learning Platform

A comprehensive web-based Japanese learning platform featuring structured lessons, content management, user authentication, and progress tracking. The platform supports both free and premium content with a complete lesson system.

## 🌟 Key Features

The platform boasts a rich set of features designed for effective Japanese language learning:

### 📚 **Comprehensive Lesson System**
- **Structured Lessons:** Create and manage lessons combining Kana, Kanji, Vocabulary, Grammar, and multimedia content.
- **Paginated Content:** Organize lesson material into multiple pages for a structured and digestible learning experience.
- **Carousel Navigation:** User-friendly, swipe-enabled navigation through lesson pages with manual controls (no auto-scrolling).
- **Interactive Content Types:** Engage learners with multiple-choice, fill-in-the-blank, and true/false questions integrated within lessons.
- **Categories & Organization:** Group lessons into color-coded categories for easy browsing and identification.
- **Lesson Prerequisites:** Define dependencies between lessons to guide students through a logical learning path.
- **Content Ordering:** Flexible ordering of content items (text, images, videos, interactive elements) within each lesson page.

### 👥 **User Management & Authentication**
- **Unified User Authentication:** Single, secure login system for both regular users and administrators using Flask-Login.
- **User Registration:** Easy self-service registration for new learners.
- **Subscription Tiers:** Support for Free and Premium content access levels.
- **Admin Panel:** A comprehensive administrative interface for managing all aspects of the platform, including users, lessons, and site content.
- **Role-Based Access Control (RBAC):** Distinct permissions and capabilities for users and administrators.

### 📖 **Content Management (Admin)**
- **Full CRUD Operations:** Admins can Create, Read, Update, and Delete all types of learning content:
    - **Kana (Hiragana & Katakana):** Manage characters, romanization, and associated media.
    - **Kanji:** Manage characters, readings (Onyomi, Kunyomi), meanings, JLPT levels, and example usage.
    - **Vocabulary:** Manage words, readings, meanings, parts of speech, and example sentences.
    - **Grammar:** Manage grammar rules, explanations, and illustrative examples.
- **Multimedia Integration:** Support for text, images, videos, and audio content. Content can be linked via URLs or uploaded directly to the server.
- **File Upload System:** Secure handling and storage of uploaded media files.

### 📊 **Learning & Engagement Features**
- **Interactive Lesson Experience:** Step-by-step progression through lessons with integrated interactive elements.
- **Page-by-Page Content Delivery:** Content is organized into distinct pages within each lesson, allowing for focused learning.
- **User Progress Tracking:** Detailed tracking of individual user progress, including completion status for lessons and individual content items/pages.
- **Time Monitoring:** Track time spent by users on lessons to gauge engagement.
- **Visual Completion Indicators:** Clear visual cues (e.g., "Completion Certificates" or badges) to mark lesson completion.
- **Lesson Filtering & Search:** Allow users to find lessons based on category, difficulty level, and content type.
- **Manual Navigation Control:** Users have full control over page transitions; no automatic scrolling or advancement.
- **AI-Powered Lesson Creation Assistance:** Tools to help administrators generate lesson content using AI (details in `Documentation/18-AI-Lesson-Creation.md`).
- **Scripted Lesson Creation:** Utility scripts for bulk creation of certain types of lessons (e.g., Hiragana, numbers - see `Documentation/19-Lesson-Creation-Scripts.md`).

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
   # This step also includes migrations for content ordering, page numbers, and interactive elements.
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
│   ├── ai_services.py      # Services for AI-powered content generation
│   ├── forms.py            # WTForms definitions for login, registration, content management
│   ├── lesson_export_import.py # Handles export and import of lesson data
│   ├── models.py           # SQLAlchemy database models for users, content, lessons
│   ├── routes.py           # Flask routes and view functions for user and admin interfaces
│   ├── static/             # Static files (CSS, JS, images)
│   │   ├── css/
│   │   ├── images/
│   │   └── uploads/        # Default folder for user-uploaded lesson content (can be configured)
│   ├── templates/          # Jinja2 templates for rendering HTML pages
│   │   ├── admin/          # Templates specific to the admin panel
│   │   │   ├── admin_index.html
│   │   │   ├── base_admin.html
│   │   │   ├── login.html      # Admin login (unified with user login)
│   │   │   ├── manage_categories.html
│   │   │   ├── manage_grammar.html
│   │   │   ├── manage_kana.html
│   │   │   ├── manage_kanji.html
│   │   │   ├── manage_lessons.html
│   │   │   └── manage_vocabulary.html
│   │   ├── base.html       # Base template for user-facing pages
│   │   ├── index.html      # Homepage
│   │   ├── lesson_view.html  # Displays a single lesson with its pages
│   │   ├── lessons.html    # Lists available lessons
│   │   ├── login.html      # User login page
│   │   └── register.html   # User registration page
│   └── utils.py            # Utility functions
├── instance/               # Instance folder (contains database, config files like config.py if used)
│   └── site.db             # SQLite database file (primary database)
├── migrations/             # Alembic migration scripts
│   ├── versions/           # Migration files
│   ├── README              # Information about migrations
│   ├── alembic.ini         # Alembic configuration
│   └── env.py              # Alembic environment setup
├── Documentation/          # Detailed project documentation files
│   └── ...                 # Various .md files as listed in Documentation/README.md
├── deprecated/             # Older or unused files
│   ├── AGENTS.md           # Deprecated agent instructions
│   ├── README.md           # Deprecated README
│   └── ...                 # Other deprecated files and templates
├── .gitignore              # Specifies intentionally untracked files that Git should ignore
├── create_admin.py         # Script to create additional admin users
├── create_hiragana_lesson.py # Utility script to create Hiragana lessons
├── create_numbers_lesson.py  # Utility script to create Numbers lessons
├── create_technology_lesson.py # Utility script to create a sample Technology lesson
├── curl_examples.md        # Examples of using cURL for API testing (if applicable)
├── fix_content_order.py    # Script for data migration related to content ordering
├── inspect_db.py           # Utility to inspect database contents
├── lesson_models.py        # DEPRECATED: All models are consolidated in app/models.py
├── manual_migration.py     # Script for manual data migration tasks
├── migrate_database.py     # General purpose database migration script (likely for Alembic)
├── migrate_file_fields.py  # Script for migrating file field data
├── migrate_interactive_system.py # Script for migrating to the new interactive system
├── migrate_lesson_system.py # Script to seed initial data and run various lesson-related migrations
├── migrate_page_numbers.py # Script for migrating page number data
├── possible_next_steps.md  # Document outlining potential future work
├── requirements.txt        # Python package dependencies
├── run.py                  # Main script to run the Flask application
├── run_migrations.py       # Script to apply Alembic database migrations
└── setup_unified_auth.py   # Script to set up the initial database schema and default admin user
```
*Note: The `app/static/uploads/` directory is the default location for user-uploaded files (images, audio for lessons). Ensure this directory is writable by the application.*

## Documentation

For comprehensive information about the project, including detailed setup, architecture, and component guides, please see the [**Full Project Documentation in the Documentation/ directory**](Documentation/README.md).
The `Documentation.md` file in the root also serves as a quick pointer to this directory.

## For AI Agents

Please refer to `AGENTS.md` (if a current one exists at the root level) or general best practices for AI agent collaboration. The `deprecated/AGENTS.md` may contain outdated information.

## Future Development

Many features from the initial "Post-MVP" list have been implemented or are in progress. Current areas for future development include:
*   **Advanced Frontend UX/UI:** Continuously refine the student-facing interface for better engagement and usability.
*   **Sophisticated Interactive Content:** Expand beyond current quiz types to include features like stroke order diagrams for Kanji, matching games, etc.
*   **Enhanced Analytics & Reporting:** Improve student progress tracking with more detailed analytics for both students and administrators.
*   **Spaced Repetition System (SRS):** Implement SRS for vocabulary and Kanji review to optimize learning.
*   **Production Deployment Enhancements:**
    *   Migrate to a more robust database (e.g., PostgreSQL) for production environments.
    *   Implement comprehensive logging and monitoring.
    *   Containerization (e.g., Docker) for easier deployment.
*   **Security Hardening:** Regularly review and enhance security mechanisms, including input validation, output encoding, and dependency management.
*   **API Expansion:** Develop more extensive API capabilities for potential third-party integrations or mobile applications.
*   **Accessibility (a11y):** Ensure the platform is accessible to users with disabilities by following WCAG guidelines.
*   **Internationalization (i18n) & Localization (l10n):** Prepare the platform for translation into other languages.

Refer to `possible_next_steps.md` and `deprecated/brainstorming.md` for a broader list of potential features and historical ideas.
