# Installation & Setup

This section guides developers through setting up the project for local development.

## Prerequisites
Ensure the following software is installed on your system:
- **Python**: Version 3.8 or higher.
- **pip**: Python package installer (usually comes with Python).
- **Git**: Version control system for cloning the repository.
- **SQLite 3**: (Optional, but good to have the command-line client for direct database inspection. The Python `sqlite3` module is built-in.)

## Step-by-Step Installation

### 1. Clone the Repository
```bash
git clone <your-repository-url>
cd Japanese_Learning_Website
```
Replace `<your-repository-url>` with the actual URL of the Git repository.

### 2. Create and Activate a Virtual Environment
It's highly recommended to use a virtual environment to manage project dependencies.
```bash
# Create the virtual environment (e.g., named 'venv')
python -m venv venv

# Activate the virtual environment
# On Windows:
# venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
Install all required Python packages listed in `requirements.txt`.
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration (`.env` file)
Create a `.env` file in the root directory of the project. This file stores environment-specific configurations. Add the following essential variables:
```env
# Flask Configuration
FLASK_APP=run.py
FLASK_ENV=development # Use 'production' for production deployments
FLASK_DEBUG=True      # Set to False in production

# Secret Key (Change this to a random, strong string for production)
SECRET_KEY=your-super-secret-and-random-key-here

# Database Configuration
DATABASE_URL=sqlite:///instance/site.db # Path to the SQLite database file

# File Upload Configuration
UPLOAD_FOLDER=app/static/uploads # Default path for storing uploaded files
# ALLOWED_EXTENSIONS are configured in app/__init__.py or instance/config.py
MAX_CONTENT_LENGTH=16777216 # Optional: Max file size for uploads (e.g., 16MB)
```
**Important:**
- The `instance` folder (for `site.db`) will be created automatically by Flask if it doesn't exist when the database is first accessed or initialized.
- Ensure `UPLOAD_FOLDER` (`app/static/uploads`) exists or is created. The application attempts to create subdirectories within this folder.

### 5. Database Initialization and Seeding
For a fresh setup, the project uses a sequence of Python scripts to initialize the database, create an admin user, and seed initial data.

#### a. Initial Database Setup and Admin Creation
This script prepares the database, creates all necessary tables based on the models defined in `app/models.py` (including tables for users, lessons, content, and AI features), and creates a default administrator account.
```bash
python setup_unified_auth.py
```
This will output the default admin credentials (typically `admin@example.com` / `admin123`).

#### b. Seed Initial Lesson Data & Apply Core Migrations
This script populates the database with default lesson categories (e.g., Hiragana Basics, Essential Kanji) and some sample lessons. It also includes necessary data migrations for features like content ordering, page numbers, and the interactive quiz system. This is crucial for having initial content and a correctly structured database.
```bash
python migrate_lesson_system.py
```

#### c. (Optional) Create Additional Admin Users
The `setup_unified_auth.py` script already creates a default admin user. If you need to create more admin users, or if you prefer a separate step for admin creation with specific credentials, you can use:
```bash
python create_admin.py
```
Follow the prompts to set the username, email, and password.

### 6. Run the Development Server
```bash
flask run
# Alternatively, you can use:
# python run.py
```
The application will typically be available at `http://127.0.0.1:5000/` or `http://localhost:5000/`.

### 7. Access the Application
-   **Main Site:** `http://localhost:5000/`
-   **Admin Panel:** `http://localhost:5000/admin` (Login with the admin credentials created by `setup_unified_auth.py` or `create_admin.py`).

## Default Admin Credentials
The `setup_unified_auth.py` script creates an admin user with the following default credentials:
-   **Email:** `admin@example.com`
-   **Password:** `admin123`
-   **Username:** `admin`

If you use `create_admin.py`, it will prompt you for credentials, defaulting to the same if you press Enter.

## Managing Database Migrations with Alembic (for Future Schema Changes)
The initial database schema is created by `setup_unified_auth.py` (`db.create_all()`). Subsequent changes to your database models in `app/models.py` require creating and applying migration scripts using Alembic. The `migrations/` directory and `run_migrations.py` script are configured for this.

**Important:**
- The `setup_unified_auth.py` script should ideally only be run once for a new database to create the initial tables.
- After the initial setup, all schema changes must be managed through Alembic migrations to avoid conflicts and ensure version control of your database structure. Do not run `db.create_all()` again on an existing database that is managed by Alembic.

When you modify your database models (e.g., add a new table, change a column in `app/models.py`):

### 1. Generate a new migration script
Use Alembic to automatically generate a revision script based on the changes detected in your models compared to the current database state (as tracked by Alembic).
```bash
alembic revision -m "Your descriptive message about the changes"
```
For example:
```bash
alembic revision -m "Add last_login_ip to User model"
```

### 2. Review and Edit the generated script
Alembic will create a new file in the `migrations/versions/` directory (e.g., `migrations/versions/xxxx_add_last_login_ip_to_user_model.py`).
- **Crucially, open this script and review it.** Alembic's autogenerate feature is powerful but may not always capture every nuance perfectly, especially for complex changes like constraints, data type changes on certain databases, or custom SQL.
- You might need to manually edit the `upgrade()` and `downgrade()` functions in the script to ensure they accurately reflect the desired schema changes. For example, you might need to add `op.create_index()`, handle data migrations if columns are being dropped or transformed, or specify server defaults.

### 3. Apply the migration to your database
This command applies all pending migrations (those in `migrations/versions/` that haven't been applied yet) to your database.
```bash
python run_migrations.py
```
This script executes `alembic upgrade head`.

### 4. Downgrade a migration (if needed)
To revert the last applied migration:
```bash
alembic downgrade -1
```
To downgrade to a specific migration version:
```bash
alembic downgrade <revision_hash_prefix>
```
**Caution:** Downgrading can be complex, especially if data loss is possible or if subsequent migrations depend on the one being reverted. Always back up your database before performing complex downgrade operations.

### Other useful Alembic commands
- **Show current revision:** `alembic current`
- **Show migration history:** `alembic history`
- **Show details of a revision:** `alembic show <revision>`
- **Stamp the database with a revision (without running migrations):** `alembic stamp head` (useful if migrations were applied manually or out-of-band)

## Troubleshooting Common Setup Issues

### Issue: `ModuleNotFoundError`
**Problem**: Missing Python packages
**Solution**: Ensure virtual environment is activated and run:
```bash
pip install -r requirements.txt
```

### Issue: Database connection errors
**Problem**: Database file doesn't exist, tables not created, or permissions issue.
**Solution**:
1.  Ensure the `instance` directory exists in the project root. If not, create it: `mkdir instance`.
2.  Run the database setup scripts in order:
    ```bash
    python setup_unified_auth.py
    python migrate_lesson_system.py
    ```
3.  Ensure you have write permissions to the `instance` directory and the `site.db` file within it.

### Issue: `SECRET_KEY` not set
**Problem**: Missing or invalid secret key
**Solution**: Ensure `.env` file exists with a proper `SECRET_KEY`:
```env
SECRET_KEY=your-very-long-random-secret-key-here
```

### Issue: File upload errors
**Problem**: Upload directory doesn't exist
**Solution**: Create the upload directory:
```bash
mkdir -p app/static/uploads/lessons/images
mkdir -p app/static/uploads/lessons/audio
mkdir -p app/static/uploads/lessons/documents
```

### Issue: Admin panel access denied
**Problem**: User doesn't have admin privileges
**Solution**: Run the admin creation script:
```bash
python create_admin.py
```

## Development Environment Verification

After setup, verify your installation by:

1. **Starting the development server**:
   ```bash
   flask run
   ```

2. **Accessing the main page**: Navigate to `http://localhost:5000`

3. **Testing admin access**: 
   - Go to `http://localhost:5000/admin`
   - Login with your admin credentials
   - Verify you can access the admin dashboard

4. **Testing user registration**:
   - Go to `http://localhost:5000/register`
   - Create a test user account
   - Login and verify basic functionality

## Next Steps

After successful installation:
1. Review the [System Architecture](03-System-Architecture.md) to understand the codebase.
2. Consult the [User Authentication](07-User-Authentication.md) document for details on auth flows and relevant API endpoints.
3. Explore existing documentation in the `Documentation/` directory for other components as they become available.
  <!--- Check the [API Design](11-API-Design.md) for available endpoints -->
  <!--- Explore the [Admin Content Management](08-Admin-Content-Management.md) features -->
  <!--- Read the [Development Workflow](15-Development-Workflow.md) for best practices -->

## Production Deployment Notes

For production deployment, remember to:
- Set `FLASK_ENV=production` and `FLASK_DEBUG=False`
- Use a strong, unique `SECRET_KEY`
- Configure a production database (PostgreSQL/MySQL)
- Set up proper file upload limits and security
- Configure HTTPS and security headers
- Set up monitoring and logging
