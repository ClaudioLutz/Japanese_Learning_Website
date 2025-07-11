# Project File Structure

## 1. Overview

This document outlines the main file and directory structure of the Japanese Learning Website project. A comprehensive understanding of the structure helps in navigating the codebase and locating specific components.

## 2. Root Directory

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

## 3. Key Directories

### 3.1. `app/` - Main Application Package
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

### 3.2. `migrations/` - Alembic Database Migrations
```
migrations/
├── versions/               # Contains individual migration script files generated by Alembic
├── README                  # Information about Alembic setup for this project
├── env.py                  # Alembic environment script, configures how migrations run
└── script.py.mako          # Template for new migration scripts
```

### 3.3. `instance/` - Instance Folder
- Contains configuration files and data that are specific to a particular instance of the application and should not be version-controlled.
- `app.db` or `site.db`: The SQLite database file is typically located here in development.
- `config.py`: Instance-specific Flask configuration.

### 3.4. `Documentation/`
- Contains all project documentation in Markdown format. The documentation is organized into numbered files covering system architecture, setup, features, and development processes. It also includes subdirectories for more detailed topics like `Enhanced-Lesson-Creation-Scripts`.

### 3.5. `deprecated/`
- Contains old files, previous versions of modules, or experimental code that is no longer in active use but kept for historical reference.

## 4. Scripts in Root Directory

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
