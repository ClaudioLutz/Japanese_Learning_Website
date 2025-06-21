# Japanese Learning Website - Complete Learning Platform

A comprehensive web-based Japanese learning platform featuring structured lessons, content management, user authentication, and progress tracking. The platform supports both free and premium content with a complete lesson system.

## 🌟 Key Features

### 📚 **Comprehensive Lesson System**
- **Structured Lessons** - Create lessons combining Kana, Kanji, Vocabulary, Grammar, and multimedia content
- **Categories & Organization** - Organize lessons into color-coded categories
- **Prerequisites** - Set lesson dependencies for progressive learning
- **Free & Premium Content** - Subscription-based access control
- **Progress Tracking** - Detailed user progress with completion percentages

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
- **Multimedia Support** - Text, images, videos, and audio content

### 📊 **Learning Features**
- **Interactive Lessons** - Step-by-step lesson progression
- **Progress Tracking** - Individual content completion tracking
- **Time Monitoring** - Track time spent on lessons
- **Completion Certificates** - Visual completion indicators
- **Filtering & Search** - Find lessons by category, difficulty, and type

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

4. **Set up the database:**
   ```bash
   # Initialize the main database
   python setup_unified_auth.py
   
   # Set up the lesson system
   python migrate_lesson_system.py
   
   # Create admin user
   python create_admin.py
   ```

5. **Run the application:**
   ```bash
   python run.py
   ```

6. **Access the application:**
   - **Main Site:** http://localhost:5000
   - **Admin Panel:** http://localhost:5000/admin

### Default Credentials
- **Admin:** admin@example.com / admin123
- **Test User:** user@example.com / password123

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
