# Unified Authentication System

This Japanese Learning Website now has a **unified authentication system** where both regular users and administrators use the same login form and system.

## How It Works

### Single Login System
- All users (regular users and admins) use the same `/login` route
- The system automatically redirects users based on their role after login:
  - **Regular users** → Home page (`/`)
  - **Admin users** → Admin panel (`/admin`)

### User Roles
Users have an `is_admin` field in the database:
- `is_admin = False` → Regular user (default)
- `is_admin = True` → Administrator

### Access Control
- **Regular users** can access:
  - Free content (after login)
  - Premium content (if subscription_level = 'premium')
  
- **Admin users** can access:
  - All regular user content
  - Admin panel (`/admin`)
  - Content management pages (`/admin/manage/*`)
  - API endpoints for CRUD operations (`/api/admin/*`)

## Getting Started

### Quick Setup (Recommended)
Run the complete setup script:
```bash
python setup_unified_auth.py
```

This will:
1. Migrate the database (add `is_admin` column if needed)
2. Create all necessary tables
3. Create an admin user with credentials:
   - **Email**: admin@example.com
   - **Password**: admin123
   - **Username**: admin
   - **Role**: Administrator

### Manual Setup (Alternative)
If you prefer to run each step manually:

1. **Migrate the Database**:
   ```bash
   python migrate_database.py
   ```

2. **Create an Admin User**:
   ```bash
   python create_admin.py
   ```

### Start the Application
```bash
python run.py
```

### Login
- Go to `http://localhost:5000/login`
- Use the admin credentials above, or register as a regular user
- The system will automatically redirect you to the appropriate dashboard

## Key Features

### For Regular Users
- User registration and login
- Free and premium content access
- Subscription management (upgrade/downgrade)

### For Administrators
- Full content management system
- CRUD operations for:
  - Kana characters
  - Kanji characters
  - Vocabulary words
  - Grammar points
- API endpoints for all content types
- Role-based access control

## API Endpoints (Admin Only)

All API endpoints require admin authentication:

### Kana
- `GET /api/admin/kana` - List all kana
- `POST /api/admin/kana/new` - Create new kana
- `GET /api/admin/kana/<id>` - Get specific kana
- `PUT /api/admin/kana/<id>/edit` - Update kana
- `DELETE /api/admin/kana/<id>/delete` - Delete kana

### Kanji
- `GET /api/admin/kanji` - List all kanji
- `POST /api/admin/kanji/new` - Create new kanji
- `GET /api/admin/kanji/<id>` - Get specific kanji
- `PUT /api/admin/kanji/<id>/edit` - Update kanji
- `DELETE /api/admin/kanji/<id>/delete` - Delete kanji

### Vocabulary
- `GET /api/admin/vocabulary` - List all vocabulary
- `POST /api/admin/vocabulary/new` - Create new vocabulary
- `GET /api/admin/vocabulary/<id>` - Get specific vocabulary
- `PUT /api/admin/vocabulary/<id>/edit` - Update vocabulary
- `DELETE /api/admin/vocabulary/<id>/delete` - Delete vocabulary

### Grammar
- `GET /api/admin/grammar` - List all grammar
- `POST /api/admin/grammar/new` - Create new grammar
- `GET /api/admin/grammar/<id>` - Get specific grammar
- `PUT /api/admin/grammar/<id>/edit` - Update grammar
- `DELETE /api/admin/grammar/<id>/delete` - Delete grammar

## Database Schema

### User Model
```python
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    subscription_level = db.Column(db.String(50), default='free')
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
```

### Content Models
- **Kana**: Japanese syllabary characters (hiragana/katakana)
- **Kanji**: Chinese characters used in Japanese
- **Vocabulary**: Japanese words with readings and meanings
- **Grammar**: Grammar points with explanations and examples

## Security Notes

- All admin routes are protected with `@admin_required` decorator
- All API endpoints require both login and admin privileges
- Passwords are hashed using Werkzeug's security functions
- Session-based authentication using Flask-Login

## Migration from Dual System

The previous system had two separate authentication mechanisms:
1. User system (Flask-Login based)
2. Admin system (session-based with hardcoded credentials)

This has been consolidated into a single, role-based system where:
- All authentication goes through Flask-Login
- Role-based access control determines what users can access
- No more hardcoded admin credentials
- Unified user management in the database
