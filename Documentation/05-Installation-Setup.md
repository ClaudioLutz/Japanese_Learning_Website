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

### 5. Database Initialization and Migration
The project uses Flask-Migrate (with Alembic) for managing database schema changes.

#### a. Initialize the Database (First time setup for a new database)
If you are setting up the project with a brand new database (e.g., `instance/site.db` does not exist or is empty and you are not using existing migrations from another source):
```bash
# Create all tables based on models (alternative to migrations for a fresh start)
# flask db_init 
# ^ This command from run.py actually calls db.create_all().
# For a typical Flask-Migrate workflow, you'd initialize migrations first if starting a project from scratch.
# However, given the existing setup, the primary way to set up the DB is via migrations.

# If the 'migrations' folder doesn't exist or you need to set up Flask-Migrate:
# flask db init  (This creates the migrations directory - only needed once per project)

# Stamp the database with the latest migration version (if migrations already exist and you're setting up a new DB)
# flask db stamp head

# Apply all migrations to create the schema:
flask db upgrade
```
*Initial Setup Note:* The project includes several standalone scripts like `setup_unified_auth.py` and `migrate_lesson_system.py`. The most robust way to initialize the database according to current best practices with Flask-Migrate is to ensure all schema definitions in `app/models.py` are comprehensive and then use `flask db upgrade`. If these scripts perform essential seeding or setup not covered by migrations, they should be run *after* `flask db upgrade` or their logic incorporated into migrations. For simplicity, `flask db upgrade` should be the primary command to set up the schema.

#### b. Applying Migrations (If migrations exist)
If the `migrations` folder with version history exists, apply them:
```bash
flask db upgrade
```
This command applies any pending database migrations to create or update the database schema according to `app/models.py` and the migration history.

#### c. Creating an Initial Admin User
After the database schema is set up, create an initial admin user:
```bash
python create_admin.py
```
Follow the prompts to set the admin's username, email, and password.

### 6. Run the Development Server
```bash
flask run
# Alternatively, you can use:
# python run.py
```
The application will typically be available at `http://127.0.0.1:5000/` or `http://localhost:5000/`.

### 7. Access the Application
-   **Main Site:** `http://localhost:5000/`
-   **Admin Panel:** `http://localhost:5000/admin` (Login with the admin credentials created in step 5c).

## Default Credentials (after running `create_admin.py`)
-   **Admin Username:** (As provided during `create_admin.py` execution, e.g., `admin`)
-   **Admin Email:** (As provided, e.g., `admin@example.com`)
-   **Admin Password:** (As provided, e.g., `admin123`)

*Note: The `create_admin.py` script sets default values if you press Enter without typing input, which are `admin`, `admin@example.com`, and `admin123`.*

## Managing Database Migrations
When you change your database models (`app/models.py`):

### 1. Generate a new migration script
```bash
flask db migrate -m "Descriptive message for your changes"
```

### 2. Review the generated script
Check the generated script in the `migrations/versions/` directory to ensure it captures your intended changes correctly.

### 3. Apply the migration to your database
```bash
flask db upgrade
```

### 4. Revert the last migration (if needed)
```bash
flask db downgrade
```

## Troubleshooting Common Setup Issues

### Issue: `ModuleNotFoundError`
**Problem**: Missing Python packages
**Solution**: Ensure virtual environment is activated and run:
```bash
pip install -r requirements.txt
```

### Issue: Database connection errors
**Problem**: Database file doesn't exist or permissions issue
**Solution**: 
```bash
# Ensure instance directory exists
mkdir -p instance
# Run database setup
flask db upgrade
```

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
1. Review the [System Architecture](03-System-Architecture.md) to understand the codebase
2. Check the [API Design](11-API-Design.md) for available endpoints
3. Explore the [Admin Content Management](08-Admin-Content-Management.md) features
4. Read the [Development Workflow](15-Development-Workflow.md) for best practices

## Production Deployment Notes

For production deployment, remember to:
- Set `FLASK_ENV=production` and `FLASK_DEBUG=False`
- Use a strong, unique `SECRET_KEY`
- Configure a production database (PostgreSQL/MySQL)
- Set up proper file upload limits and security
- Configure HTTPS and security headers
- Set up monitoring and logging
