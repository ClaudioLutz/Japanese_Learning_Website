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
- **Database Files**:
  - `instance/site.db` - Main application database
  - `japanese_learning.db` - Legacy database (maintained for compatibility)

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
GET    /api/admin/kana        # List all kana
POST   /api/admin/kana/new    # Create new kana
GET    /api/admin/kana/{id}   # Get specific kana
PUT    /api/admin/kana/{id}/edit # Update kana
DELETE /api/admin/kana/{id}/delete # Delete kana
```

#### Kanji API
```
GET    /api/admin/kanji       # List all kanji
POST   /api/admin/kanji/new   # Create new kanji
GET    /api/admin/kanji/{id}  # Get specific kanji
PUT    /api/admin/kanji/{id}/edit # Update kanji
DELETE /api/admin/kanji/{id}/delete # Delete kanji
```

#### Vocabulary API
```
GET    /api/admin/vocabulary  # List all vocabulary
POST   /api/admin/vocabulary/new # Create new vocabulary
GET    /api/admin/vocabulary/{id} # Get specific vocabulary
PUT    /api/admin/vocabulary/{id}/edit # Update vocabulary
DELETE /api/admin/vocabulary/{id}/delete # Delete vocabulary
```

#### Grammar API
```
GET    /api/admin/grammar     # List all grammar
POST   /api/admin/grammar/new # Create new grammar
GET    /api/admin/grammar/{id} # Get specific grammar
PUT    /api/admin/grammar/{id}/edit # Update grammar
DELETE /api/admin/grammar/{id}/delete # Delete grammar
```

---

## Frontend Components

### Template Structure
```
app/templates/
├── base.html                 # Main layout template
├── index.html               # Homepage
├── login.html               # Login form
├── register.html            # Registration form
├── free_content.html        # Free learning materials
├── premium_content.html     # Premium learning materials
└── admin/                   # Admin panel templates
    ├── base_admin.html      # Admin layout template
    ├── admin_index.html     # Admin dashboard
    ├── manage_kana.html     # Kana management interface
    ├── manage_kanji.html    # Kanji management interface
    ├── manage_vocabulary.html # Vocabulary management interface
    └── manage_grammar.html  # Grammar management interface
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
├── app/                     # Main application package
│   ├── __init__.py         # Flask app factory
│   ├── models.py           # Database models
│   ├── routes.py           # URL routes and view functions
│   ├── forms.py            # WTForms form classes
│   └── templates/          # Jinja2 templates
│       ├── base.html
│       ├── index.html
│       ├── login.html
│       ├── register.html
│       ├── free_content.html
│       ├── premium_content.html
│       └── admin/          # Admin panel templates
├── instance/               # Instance-specific files
│   ├── config.py          # Configuration settings
│   └── site.db            # SQLite database
├── templates/              # Legacy template directory
│   └── admin/             # Legacy admin templates
├── .env                   # Environment variables
├── requirements.txt       # Python dependencies
├── run.py                # Application entry point
├── create_admin.py       # Admin user creation script
├── setup_unified_auth.py # Database setup script
├── migrate_database.py   # Database migration script
├── redirect_old_admin.py # Legacy admin redirect
├── UNIFIED_AUTH_README.md # Authentication system docs
├── ADMIN_CONTENT_CREATION_GUIDE.md # Admin guide
└── Documentation.md      # This file
```

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
- **Models** - Database schema in `app/models.py`
- **Views** - Route handlers in `app/routes.py`
- **Forms** - WTForms classes in `app/forms.py`
- **Templates** - Jinja2 templates in `app/templates/`
- **Static Files** - CSS/JS in `app/static/` (if needed)

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

#### 5. Static Files Not Loading
**Problem**: CSS/JS files return 404
**Solution**: Check Flask static file configuration and file paths

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

## Future Enhancements

### Planned Features

#### 1. Enhanced Learning Tools
- **Progress Tracking** - User learning progress analytics
- **Spaced Repetition** - Intelligent review scheduling
- **Quiz System** - Interactive learning assessments
- **Audio Integration** - Native pronunciation support

#### 2. Content Improvements
- **Rich Media Support** - Images, videos, audio files
- **Content Versioning** - Track content changes over time
- **Bulk Import/Export** - CSV/JSON content management
- **Content Categories** - Organized learning paths

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

*Last Updated: June 21, 2025*
*Version: 1.0.0*
