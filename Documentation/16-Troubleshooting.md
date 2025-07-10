# Troubleshooting Guide

This guide covers common issues you may encounter while developing, deploying, or using the Japanese Learning Website.

## Common Issues

### 1. Template Not Found Errors
```
jinja2.exceptions.TemplateNotFound: admin/admin_index.html
```
**Cause**: Template files are missing or in the wrong location.

**Solution**: 
- Ensure admin templates are in `app/templates/admin/`
- Check template file names match exactly (case-sensitive)
- Verify template inheritance is correct

```bash
# Check template structure
ls -la app/templates/
ls -la app/templates/admin/
```

### 2. Route Building Errors
```
werkzeug.routing.exceptions.BuildError: Could not build url for endpoint 'list_kana'
```
**Cause**: Incorrect route endpoint reference in templates or redirects.

**Solution**: 
- Use correct route format `routes.list_kana` instead of `list_kana`
- Check route definitions in `app/routes.py`
- Verify blueprint registration

```python
# Correct usage in templates
{{ url_for('routes.list_kana') }}

# Correct usage in redirects
return redirect(url_for('routes.admin_index'))
```

### 3. Database Connection Issues
```
sqlite3.OperationalError: no such table: user
```
**Cause**: Database not initialized, tables not created, or migrations not applied.

**Solution**:
1.  Ensure `instance/site.db` (or your configured DB) exists. If not, the setup script should create it.
2.  Run initial setup scripts if this is a fresh installation:
    ```bash
    python setup_unified_auth.py  # Creates initial tables and admin user
    python migrate_lesson_system.py # Seeds data and runs essential data migrations
    ```
3.  If you have made changes to models and have pending Alembic migrations:
    ```bash
    python run_migrations.py      # Applies pending Alembic migrations
    ```
    If you need to generate a new migration because you changed `app/models.py`:
    ```bash
    alembic revision -m "Your migration message"
    # Then review the generated script and run:
    python run_migrations.py
    ```

### 4. Admin Access Denied
**Problem**: Can't access admin panel after login.

**Cause**: User doesn't have admin privileges.

**Solution**: 
```bash
# Create admin user
python create_admin.py

# Or manually set admin flag in database
sqlite3 instance/site.db
UPDATE user SET is_admin = 1 WHERE email = 'your-email@example.com';
```

### 5. Static Files Not Loading
**Problem**: CSS/JS files return 404 or images don't display.

**Cause**: Static file configuration or path issues.

**Solution**:
- For Bootstrap CDN: Check internet connection and CDN links
- For custom static files: Verify `app/static/` directory structure
- For uploaded files: Check `UPLOAD_FOLDER` configuration and file paths

```bash
# Check static file structure
ls -la app/static/
ls -la app/static/css/
ls -la app/static/uploads/

# Verify upload folder permissions
chmod 755 app/static/uploads/
```

### 6. File Upload Errors
**Problem**: File uploads fail or return errors.

**Causes & Solutions**:

#### Upload Directory Missing
```bash
# Create upload directories
mkdir -p app/static/uploads/lessons/images
mkdir -p app/static/uploads/lessons/audio
mkdir -p app/static/uploads/lessons/documents
```

#### File Size Limits
```python
# Check MAX_CONTENT_LENGTH in .env
MAX_CONTENT_LENGTH=16777216  # 16MB

# Or in app configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
```

#### File Type Restrictions
```python
# Check ALLOWED_EXTENSIONS configuration
ALLOWED_EXTENSIONS = {
    'image': {'png', 'jpg', 'jpeg', 'gif'},
    'audio': {'mp3', 'wav', 'ogg'},
    'document': {'pdf', 'doc', 'docx', 'txt'}
}
```

### 7. CSRF Token Errors
```
The CSRF token is missing or invalid
```
**Cause**: CSRF protection failing on form submissions.

**Solution**:
```html
<!-- Ensure CSRF token in forms -->
{{ form.hidden_tag() }}
<!-- or -->
{{ form.csrf_token }}
```

```javascript
// For AJAX requests, include CSRF token
const csrfToken = document.querySelector('meta[name=csrf-token]').getAttribute('content');
fetch('/api/endpoint', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken
    },
    body: JSON.stringify(data)
});
```

### 8. Import Errors
```
ModuleNotFoundError: No module named 'app'
```
**Cause**: Python path or virtual environment issues.

**Solution**:
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Check Python path
python -c "import sys; print(sys.path)"
```

### 9. Database Migration Errors
```
Target database is not up to date
```
**Cause**: Migration conflicts or database state issues. Alembic may detect that the actual database schema doesn't match the migration history.

**Solution**:
1.  **Check current migration status**:
    ```bash
    alembic current
    alembic history
    ```
2.  **Ensure all migrations are applied**:
    ```bash
    python run_migrations.py
    ```
3.  **If the database is truly out of sync with Alembic's history (e.g., manual changes were made, or history is corrupted):**
    - **Option A: Stamp to current head (if DB schema matches models and latest migration)**
      If you are certain your database schema correctly reflects the state after all migrations, you can tell Alembic to consider the database as up-to-date:
      ```bash
      alembic stamp head
      ```
      *Use with caution. This doesn't change the schema; it just updates Alembic's version table.*
    - **Option B: More complex recovery (potentially requires manual intervention)**
      If migrations are genuinely corrupted or the DB is in an unknown state relative to migrations, recovery can be complex. This might involve:
        - Backing up your data.
        - Inspecting the `alembic_version` table in your database.
        - Potentially dropping tables and re-creating from scratch using `setup_unified_auth.py` and `python run_migrations.py` (losing data unless restored).
        - Or, carefully generating new migration scripts and manually adjusting them.
    - **Drastic Reset (Last Resort - Deletes Migration History and Data if not careful):**
      If you intend to start migrations from scratch and your database can be rebuilt (e.g., in development):
      ```bash
      # Warning: This path can lead to data loss if not handled carefully.
      # 1. Ensure your models in app/models.py are correct.
      # 2. Backup your database if it contains valuable data.
      # 3. Delete the migrations/versions/ directory's contents: rm -rf migrations/versions/*
      # 4. Drop all tables from your database (e.g., using a DB browser or `db.drop_all()` temporarily in a script).
      # 5. Run initial setup:
      python setup_unified_auth.py # Recreates tables based on models (like db.create_all())
      # 6. Stamp the database with an initial Alembic state (if `setup_unified_auth.py` doesn't do this):
      #    This might involve creating an initial migration for an empty DB or stamping a base.
      #    Often, the first 'real' migration is generated against the tables created by setup_unified_auth.py.
      # 7. Generate a new "initial" migration if needed, or proceed to generate migrations for model changes.
      #    If `setup_unified_auth.py` creates tables, your first Alembic revision might be empty or reflect those tables.
      #    `alembic revision -m "establish baseline from existing tables"`
      #    You might need to edit this script to reflect the current state if autogenerate doesn't capture it.
      #    Then `python run_migrations.py`
      ```
      *This "drastic reset" is complex and error-prone. It's usually better to fix specific migration issues.*

### 10. Permission Errors
**Problem**: Access denied errors when accessing files or directories.

**Solution**:
```bash
# Fix file permissions
chmod 644 app/static/uploads/lessons/images/*
chmod 755 app/static/uploads/lessons/images/

# Fix directory ownership (if needed)
chown -R www-data:www-data app/static/uploads/
```

## Debug Mode

### Enable Debug Mode
```env
# In .env file
FLASK_DEBUG=True
FLASK_ENV=development
```

### Debug Information
- Detailed error pages with stack traces
- Auto-reload on code changes
- Interactive debugger in browser

**Warning**: Never enable debug mode in production!

## Logging

### Enable Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# In app/__init__.py
if not app.debug:
    # Production logging setup
    import logging
    from logging.handlers import RotatingFileHandler
    
    file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
```

### Check Logs
```bash
# View application logs
tail -f logs/app.log

# View Flask development server logs
# (displayed in terminal where flask run is executed)
```

## Database Issues

### Database Locked
```
sqlite3.OperationalError: database is locked
```
**Solution**:
```bash
# Check for running processes
ps aux | grep python

# Kill any hanging processes
pkill -f "flask run"

# Restart the application
flask run
```

### Database Corruption
```bash
# Check database integrity
sqlite3 instance/site.db "PRAGMA integrity_check;"

# Backup and restore if needed
cp instance/site.db instance/site.db.backup
sqlite3 instance/site.db ".dump" | sqlite3 instance/site_new.db
mv instance/site_new.db instance/site.db
```

## Performance Issues

### Slow Database Queries
```python
# Enable SQL query logging
app.config['SQLALCHEMY_ECHO'] = True

# Add database indexes
class User(db.Model):
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
```

### Memory Issues
```bash
# Monitor memory usage
top -p $(pgrep -f "flask run")

# Check for memory leaks
python -m memory_profiler app.py
```

## Network Issues

### Port Already in Use
```
OSError: [Errno 48] Address already in use
```
**Solution**:
```bash
# Find process using port 5000
lsof -i :5000

# Kill the process
kill -9 <PID>

# Or use a different port
flask run --port 5001
```

### CORS Issues
```javascript
// If making requests from different domains
// Add CORS headers in Flask
from flask_cors import CORS
CORS(app)
```

## Environment Issues

### Wrong Python Version
```bash
# Check Python version
python --version

# Use specific Python version
python3.8 -m venv venv
```

### Missing Environment Variables
```bash
# Check if .env file exists
ls -la .env

# Verify environment variables are loaded
python -c "import os; print(os.environ.get('SECRET_KEY'))"
```

## Production Issues

### 500 Internal Server Error
**Check**:
1. Application logs
2. Web server logs (nginx/apache)
3. Database connectivity
4. File permissions
5. Environment variables

### Static Files Not Served
```nginx
# Nginx configuration for static files
location /static {
    alias /path/to/app/static;
    expires 1y;
    add_header Cache-Control "public, immutable";
}

location /uploads {
    alias /path/to/upload/folder;
    expires 1y;
    add_header Cache-Control "public";
}
```

## Getting Help

### Information to Gather
When reporting issues, include:
1. Error message (full stack trace)
2. Steps to reproduce
3. Environment details (OS, Python version)
4. Configuration files (without secrets)
5. Log files

### Useful Commands
```bash
# System information
python --version
pip list
flask --version

# Application status
flask routes  # Still useful for showing Flask routes
flask shell

# Database information (Alembic)
alembic current
alembic history
# alembic show <revision_id> # To show details of a specific revision
```

### Debug Commands
```bash
# Test database connection
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); print(db.engine.execute('SELECT 1').scalar())"

# Test file upload configuration
python -c "from app import create_app; app = create_app(); print(app.config['UPLOAD_FOLDER'])"

# Test user authentication
python -c "from app.models import User; print(User.query.first())"
```

## Prevention

### Best Practices
1. **Version Control**: Commit working states frequently
2. **Backups**: Regular database and file backups
3. **Testing**: Test changes in development first
4. **Monitoring**: Set up application monitoring
5. **Documentation**: Keep configuration documented

### Health Checks
```python
# Add health check endpoint
@app.route('/health')
def health_check():
    try:
        # Test database
        db.session.execute('SELECT 1')
        
        # Test file system
        upload_folder = app.config['UPLOAD_FOLDER']
        if not os.path.exists(upload_folder):
            return {'status': 'error', 'message': 'Upload folder missing'}, 500
            
        return {'status': 'healthy'}, 200
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500
