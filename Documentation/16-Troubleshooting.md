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
**Cause**: Database not initialized or migration not applied.

**Solution**: 
```bash
# Initialize database
flask db upgrade

# If migrations don't exist, create them
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Alternative: Run setup script
python setup_unified_auth.py
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
**Cause**: Migration conflicts or database state issues.

**Solution**:
```bash
# Check migration status
flask db current
flask db history

# Force migration to head
flask db stamp head
flask db upgrade

# If migrations are corrupted, reset
rm -rf migrations/
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

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
flask routes
flask shell

# Database information
flask db current
flask db show
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
