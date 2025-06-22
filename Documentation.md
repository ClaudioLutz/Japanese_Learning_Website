# Japanese Learning Website - Complete Project Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture & Technology Stack](#architecture--technology-stack)
3. [Installation & Setup](#installation--setup)
4. [User Authentication System](#user-authentication-system)
5. [Admin Content Management](#admin-content-management)
6. [Database Schema](#database-schema)
7. [API Endpoints](#api-endpoints)
8. [Frontend Components](#frontend-components)
9. [File Structure](#file-structure)
10. [Configuration](#configuration)
11. [Security Features](#security-features)
12. [Development Workflow](#development-workflow)
13. [Troubleshooting](#troubleshooting)
14. [Future Enhancements](#future-enhancements)

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

## Architecture & Technology Stack

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

### Prerequisites
```bash
# Required software
Python 3.8 or higher
pip (Python package installer)
Git (for version control)
```

### Step-by-Step Installation

1. **Clone the Repository**
```bash
git clone <repository-url>
cd Japanese_Learning_Website
```

2. **Create Virtual Environment**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Environment Configuration**
```bash
# Create .env file with:
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///instance/site.db
FLASK_ENV=development
```

5. **Database Setup**
```bash
# Run setup script to create unified authentication
python setup_unified_auth.py

# Create admin user
python create_admin.py
```

6. **Start the Application**
```bash
python run.py
```

7. **Access the Application**
- Main site: `http://localhost:5000`
- Admin panel: `http://localhost:5000/admin`

### Default Credentials
- **Admin**: admin@example.com / admin123
- **Test User**: user@example.com / password123

---

## User Authentication System

### Authentication Flow
1. **Registration** - Users create accounts with email/username/password
2. **Login** - Session-based authentication with Flask-Login
3. **Role Assignment** - Users assigned 'free' or 'premium' subscription levels
4. **Admin Access** - Special `is_admin` flag for administrative privileges

### User Roles & Permissions

#### Free Users
- Access to free content sections
- Basic Japanese learning materials
- Account management (upgrade to premium)

#### Premium Users
- All free user privileges
- Access to premium content sections
- Advanced learning materials
- Account management (downgrade to free)

#### Administrators
- All user privileges
- Content management system access
- User account management
- System configuration access

### Session Management
- **Secure Sessions** - Flask-Login with secure session cookies
- **Remember Me** - Optional persistent login
- **Auto-Logout** - Configurable session timeout
- **CSRF Protection** - Form-based CSRF tokens

---

## Admin Content Management

### Content Types

#### 1. Kana (Hiragana & Katakana)
```python
# Fields
- character: Single Japanese character (あ, ア)
- romanization: Roman alphabet equivalent (a, ka)
- type: hiragana or katakana
- stroke_order_info: Optional stroke order data
- example_sound_url: Optional audio pronunciation
```

#### 2. Kanji (Chinese Characters)
```python
# Fields
- character: Single kanji character (水, 火)
- meaning: English meanings (comma-separated)
- onyomi: Chinese reading (スイ, カ)
- kunyomi: Japanese reading (みず, ひ)
- jlpt_level: JLPT difficulty level (1-5)
- stroke_order_info: Optional stroke information
- radical: Kanji radical component
- stroke_count: Number of strokes
```

#### 3. Vocabulary (Words & Phrases)
```python
# Fields
- word: Japanese word (水, こんにちは)
- reading: Hiragana/katakana reading
- meaning: English translation
- jlpt_level: JLPT difficulty level (1-5)
- example_sentence_japanese: Usage example
- example_sentence_english: Translation
- audio_url: Pronunciation audio link
```

#### 4. Grammar (Rules & Patterns)
```python
# Fields
- title: Grammar point name
- explanation: Detailed rule explanation
- structure: Pattern formula (Verb + た)
- jlpt_level: JLPT difficulty level (1-5)
- example_sentences: JSON array of examples
```

### Content Management Interface

#### Access Methods
1. **Navigation Button** - "Admin Panel" in main navigation (admin users only)
2. **Direct URL** - `/admin` endpoint
3. **Content-Specific URLs**:
   - `/admin/manage/kana`
   - `/admin/manage/kanji`
   - `/admin/manage/vocabulary`
   - `/admin/manage/grammar`

#### CRUD Operations

**Create Content**
1. Click "Add New [Content Type]" button
2. Fill out modal form with required/optional fields
3. Submit form → Content saved to database
4. Table refreshes automatically with new content

**Read Content**
- All content displayed in sortable tables
- Real-time loading via AJAX
- Pagination for large datasets

**Update Content**
1. Click "Edit" link next to any item
2. Modal form pre-populated with existing data
3. Modify fields as needed
4. Submit → Database updated, table refreshed

**Delete Content**
1. Click "Delete" link next to any item
2. Confirmation dialog appears
3. Confirm → Content permanently removed
4. Table refreshed automatically

---

## Database Schema

### User Table
```sql
CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    subscription_level VARCHAR(20) DEFAULT 'free',
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Kana Table
```sql
CREATE TABLE kana (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character VARCHAR(1) UNIQUE NOT NULL,
    romanization VARCHAR(10) NOT NULL,
    type VARCHAR(10) NOT NULL,
    stroke_order_info TEXT,
    example_sound_url VARCHAR(255)
);
```

### Kanji Table
```sql
CREATE TABLE kanji (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character VARCHAR(1) UNIQUE NOT NULL,
    meaning TEXT NOT NULL,
    onyomi VARCHAR(100),
    kunyomi VARCHAR(100),
    jlpt_level INTEGER,
    stroke_order_info TEXT,
    radical VARCHAR(10),
    stroke_count INTEGER
);
```

### Vocabulary Table
```sql
CREATE TABLE vocabulary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word VARCHAR(100) NOT NULL,
    reading VARCHAR(100) NOT NULL,
    meaning TEXT NOT NULL,
    jlpt_level INTEGER,
    example_sentence_japanese TEXT,
    example_sentence_english TEXT,
    audio_url VARCHAR(255)
);
```

### Grammar Table
```sql
CREATE TABLE grammar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(200) NOT NULL,
    explanation TEXT NOT NULL,
    structure VARCHAR(200),
    jlpt_level INTEGER,
    example_sentences TEXT
);
```

---

## API Endpoints

### Authentication Endpoints
```
POST   /login                 # User login
POST   /register              # User registration
GET    /logout                # User logout
POST   /upgrade_to_premium    # Upgrade subscription
POST   /downgrade_from_premium # Downgrade subscription
```

### Content Display Endpoints
```
GET    /                      # Homepage
GET    /free_content          # Free learning materials
GET    /premium_content       # Premium learning materials (auth required)
```

### Admin Panel Endpoints
```
GET    /admin                 # Admin dashboard (admin required)
GET    /admin/manage/kana     # Kana management page
GET    /admin/manage/kanji    # Kanji management page
GET    /admin/manage/vocabulary # Vocabulary management page
GET    /admin/manage/grammar  # Grammar management page
```

### Admin API Endpoints

#### Kana API
```
GET    /api/admin/kana                     # List all kana
POST   /api/admin/kana/new                 # Create new kana
GET    /api/admin/kana/<int:item_id>       # Get specific kana
PUT    /api/admin/kana/<int:item_id>/edit  # Update kana (accepts PUT or PATCH)
DELETE /api/admin/kana/<int:item_id>/delete# Delete kana
```

#### Kanji API
```
GET    /api/admin/kanji                     # List all kanji
POST   /api/admin/kanji/new                 # Create new kanji
GET    /api/admin/kanji/<int:item_id>       # Get specific kanji
PUT    /api/admin/kanji/<int:item_id>/edit  # Update kanji (accepts PUT or PATCH)
DELETE /api/admin/kanji/<int:item_id>/delete# Delete kanji
```

#### Vocabulary API
```
GET    /api/admin/vocabulary                     # List all vocabulary
POST   /api/admin/vocabulary/new                 # Create new vocabulary
GET    /api/admin/vocabulary/<int:item_id>       # Get specific vocabulary
PUT    /api/admin/vocabulary/<int:item_id>/edit  # Update vocabulary (accepts PUT or PATCH)
DELETE /api/admin/vocabulary/<int:item_id>/delete# Delete vocabulary
```

#### Grammar API
```
GET    /api/admin/grammar                     # List all grammar
POST   /api/admin/grammar/new                 # Create new grammar
GET    /api/admin/grammar/<int:item_id>       # Get specific grammar
PUT    /api/admin/grammar/<int:item_id>/edit  # Update grammar (accepts PUT or PATCH)
DELETE /api/admin/grammar/<int:item_id>/delete# Delete grammar
```

---

## Frontend Components

### Template Structure
```
app/templates/
├── base.html                 # Main layout template for user-facing pages
├── index.html                # Homepage
├── login.html                # User login form
├── register.html             # User registration form
├── free_content.html         # Page for free learning materials
├── premium_content.html      # Page for premium learning materials (requires subscription)
├── lessons.html              # Page to browse available lessons
├── lesson_view.html          # Page to view a single lesson's content
└── admin/                    # Admin panel templates
    ├── base_admin.html       # Main layout template for admin pages
    ├── admin_index.html      # Admin dashboard/homepage
    ├── login.html            # Admin login form (may be unified with user login)
    ├── manage_kana.html      # Interface for managing Kana content
    ├── manage_kanji.html     # Interface for managing Kanji content
    ├── manage_vocabulary.html # Interface for managing Vocabulary content
    ├── manage_grammar.html   # Interface for managing Grammar content
    ├── manage_lessons.html   # Interface for managing Lessons
    └── manage_categories.html # Interface for managing Lesson Categories
```

### JavaScript Functionality

#### Modal Management
```javascript
// Open modal dialog
function openModal(modalId) {
    document.getElementById(modalId).style.display = "block";
}

// Close modal dialog
function closeModal(modalId) {
    document.getElementById(modalId).style.display = "none";
}
```

#### AJAX Content Loading
```javascript
// Fetch content from API
async function fetchContent() {
    const response = await fetch('/api/admin/content');
    const data = await response.json();
    updateTable(data);
}

// Submit form data
async function submitForm(data) {
    const response = await fetch('/api/admin/content/new', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    return response.ok;
}
```

### CSS Styling
- **Bootstrap 5.3.3** - Primary UI framework
- **Custom CSS** - Additional styling for admin panels
- **Responsive Design** - Mobile-first approach
- **Color Scheme** - Professional blue/gray palette

---

## File Structure

```
Japanese_Learning_Website/
├── app/                    # Main Flask application package
│   ├── __init__.py         # Application factory, initializes Flask app and extensions
│   ├── forms.py            # WTForms definitions for login, registration, content management
│   ├── models.py           # SQLAlchemy database models for users, content, lessons
│   ├── routes.py           # Flask routes and view functions for user and admin interfaces
│   └── templates/          # Jinja2 templates for rendering HTML pages
│       ├── admin/          # Templates specific to the admin panel (detailed above)
│       │   ├── admin_index.html
│       │   ├── base_admin.html
│       │   ├── login.html
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
├── instance/               # Instance folder (contains database, potentially config files if not using .env)
│   └── site.db             # SQLite database file (primary database)
├── deprecated/             # Older or unused files
│   ├── AGENTS.md           # Deprecated agent instructions
│   ├── README.md           # Deprecated README
│   ├── app_old_backup.py   # Old backup of application logic
│   ├── brainstorming.md    # Deprecated brainstorming document
│   ├── legacy_templates/   # Deprecated templates
│   └── redirect_old_admin.py # Script for redirecting from old admin paths
├── .env                    # Environment variables (recommended for secrets like SECRET_KEY, DATABASE_URL)
├── .gitignore              # Specifies intentionally untracked files that Git should ignore
├── ADMIN_CONTENT_CREATION_GUIDE.md # Guide for admins on creating content
├── Documentation.md        # This detailed project documentation
├── README.md               # Project overview, setup, and quick start guide
├── UNIFIED_AUTH_README.md  # Documentation specific to the authentication system
├── create_admin.py         # Script to create an initial admin user
├── lesson_models.py        # DEPRECATED: All models are consolidated in app/models.py
├── migrate_database.py     # Script for generic database migrations or setup tasks
├── migrate_lesson_system.py # Script to set up or migrate the lesson system database tables
├── requirements.txt        # Python package dependencies
├── run.py                  # Main script to run the Flask application
└── setup_unified_auth.py   # Script to set up the initial database schema for unified authentication
```
*Note: A `static/` directory for custom CSS/JS is not present. Styling is primarily handled by Bootstrap (likely via CDN) and inline styles or script tags within templates.*

---

## Configuration

### Environment Variables (.env)
```bash
# Security
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=sqlite:///instance/site.db

# Flask Settings
FLASK_ENV=development
FLASK_DEBUG=True

# Optional: External Services
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

### Instance Configuration (instance/config.py)
```python
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    
class DevelopmentConfig(Config):
    DEBUG = True
    
class ProductionConfig(Config):
    DEBUG = False
    # Additional production settings
```

### Dependencies (requirements.txt)
```
Flask==2.3.3
Flask-Login==0.6.3
Flask-WTF==1.1.1
Flask-SQLAlchemy==3.0.5
WTForms==3.0.1
Werkzeug==2.3.7
python-dotenv==1.0.0
```

---

## Security Features

### Authentication Security
- **Password Hashing** - Werkzeug PBKDF2 with salt
- **Session Management** - Secure session cookies
- **CSRF Protection** - WTForms CSRF tokens
- **Input Validation** - Server-side form validation

### Authorization Controls
- **Role-Based Access** - User/Admin permission levels
- **Route Protection** - Login required decorators
- **Admin-Only Areas** - Restricted admin panel access
- **API Security** - Admin authentication for content APIs

### Data Protection
- **SQL Injection Prevention** - SQLAlchemy ORM parameterized queries
- **XSS Prevention** - Jinja2 template auto-escaping
- **Secure Headers** - Flask security headers
- **Environment Variables** - Sensitive data in .env files

### Best Practices Implemented
- **Principle of Least Privilege** - Minimal required permissions
- **Defense in Depth** - Multiple security layers
- **Secure by Default** - Safe default configurations
- **Regular Updates** - Keep dependencies current

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
- **Static Files** - Currently, no dedicated `app/static/` or `static/` directory is observed. Static assets like CSS and JavaScript are primarily managed via Bootstrap CDN and potentially inline/internal styles/scripts in templates. If custom static files are added, they would typically reside in `app/static/`.

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
**Problem**: Custom CSS/JS files return 404 (Note: currently, the project doesn't seem to use a local `static` folder; assets are likely CDN-based).
**Solution**: If local static files are added (e.g., in `app/static/`), ensure Flask static file configuration is correct (`static_folder='static'` in Flask app setup or blueprint, and `url_for('static', filename='path/to/file')` in templates). Verify file paths.

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

#### 4. Enhanced Content Builder (Phase 1)
- **Visual Content Type Selector** - Intuitive card-based interface with 8 content types
- **Multi-step Wizard** - Step-by-step content creation process (Type Selection → Configuration → Preview → Save)
- **Dynamic Form Generation** - Forms adapt based on selected content type
- **Content Preview System** - Preview content before saving to lessons
- **Mixed Content Types** - Combine existing content with custom multimedia
- **Content Ordering** - Specify the sequence of content within lessons
- **Optional Content** - Mark content items as optional
- **Rich Media Support** - Text, images, videos, and audio content. Supports both URL-based media and direct file uploads for images, audio, and other supplementary materials. Uploaded files are stored on the server and managed through the lesson builder.

##### Content Types Supported:
- **Existing Content**: Kana, Kanji, Vocabulary, Grammar (dropdown selection from database)
- **Custom Text**: Title and rich text content creation
- **URL-based Media**: Video (YouTube/Vimeo), Audio, and Image content via URLs.
- **File Uploads**: Direct upload for images, audio files, PDFs, or other documents to be associated with `LessonContent`. Admins can upload files during lesson creation/editing. These files are served by the application and can be deleted if no longer needed.

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
);
```

#### Lesson Prerequisites Table
```sql
CREATE TABLE lesson_prerequisite (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson_id INTEGER NOT NULL,
    prerequisite_lesson_id INTEGER NOT NULL,
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
    content_id INTEGER, -- NULL for multimedia content
    title VARCHAR(200),
    content_text TEXT,
    media_url VARCHAR(255),
    order_index INTEGER DEFAULT 0,
    is_optional BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- File-related fields for uploaded content
    file_path VARCHAR(500),      -- Relative path to the uploaded file in the UPLOAD_FOLDER
    file_size INTEGER,           -- File size in bytes
    file_type VARCHAR(50),       -- MIME type of the file
    original_filename VARCHAR(255), -- Original name of the uploaded file
    FOREIGN KEY (lesson_id) REFERENCES lesson (id) ON DELETE CASCADE
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
    content_progress TEXT, -- JSON string of content item completion
    FOREIGN KEY (user_id) REFERENCES user (id) ON DELETE CASCADE,
    FOREIGN KEY (lesson_id) REFERENCES lesson (id) ON DELETE CASCADE,
    UNIQUE(user_id, lesson_id)
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
```

#### File Management API (Admin)
```
POST   /api/admin/upload-file                 # Upload a file, returns file path and info.
                                              # Used by lesson builder for image/audio/document uploads.
DELETE /api/admin/delete-file                 # Delete an uploaded file from the server.
                                              # Expects JSON body with 'file_path'.
POST   /api/admin/lessons/<int:lesson_id>/content/file   # Add file-based content to a lesson.
                                              # Associates an uploaded file (via file_path) with a lesson content item.
```

### Static File Serving
```
GET    /uploads/<path:filename>               # Serves uploaded files.
                                              # <path:filename> is the path relative to the UPLOAD_FOLDER.
```

### User Interface

#### Admin Interface
- **Lesson Management** (`/admin/manage/lessons`) - Create, edit, and manage lessons
- **Category Management** (`/admin/manage/categories`) - Organize lesson categories
- **Content Builder** - Add and organize content within lessons
- **Publishing Controls** - Publish/unpublish lessons

#### User Interface
- **Lesson Browser** (`/lessons`) - Browse and filter available lessons
- **Lesson Viewer** (`/lessons/{id}`) - View lesson content and track progress
- **Progress Tracking** - Visual progress indicators and completion status

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

*Last Updated: October 26, 2023*
*Version: 1.1.0*
