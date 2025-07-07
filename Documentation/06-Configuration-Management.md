# Configuration Management

Application configuration is primarily managed through environment variables loaded from a `.env` file and default values set in `app/__init__.py` or `instance/config.py`.

## 1. Environment Variables (`.env` file)
A `.env` file in the project root is used to store sensitive and environment-specific configurations. This file should **not** be committed to version control. The `python-dotenv` package loads these variables into the environment when the application starts.

### Key Environment Variables

- **`FLASK_APP=run.py`**: Specifies the entry point for the Flask CLI.
- **`FLASK_ENV=development`**: Sets the Flask environment. Can be `development` or `production`.
    - In `development` mode, `FLASK_DEBUG` is often implicitly or explicitly set to `True`, enabling the interactive debugger and auto-reloader.
- **`FLASK_DEBUG=True`**: Enables/disables debug mode (set to `False` in production).
- **`SECRET_KEY`**: A long, random string used for session signing, CSRF token generation, and other security-related cryptographic needs. **Crucial for security and must be kept secret.**
    - Example: `SECRET_KEY=my-very-secret-and-long-random-string-123!@#`
- **`DATABASE_URL`**: Specifies the connection string for the database.
    - Example for SQLite: `DATABASE_URL=sqlite:///instance/site.db`
    - Example for PostgreSQL: `DATABASE_URL=postgresql://user:password@host:port/dbname`
- **`UPLOAD_FOLDER=app/static/uploads`**: The absolute or relative path to the directory where user-uploaded files (for lessons, etc.) will be stored. The application will attempt to create subdirectories within this folder (e.g., `lessons/image`, `lessons/audio`).
- **`MAX_CONTENT_LENGTH=16777216`**: (Optional) Maximum allowed size for file uploads, in bytes (e.g., 16MB). This is a standard Flask configuration.

### Example `.env` file
```env
FLASK_APP=run.py
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-chosen-secret-key-should-be-long-and-random
DATABASE_URL=sqlite:///instance/site.db
UPLOAD_FOLDER=app/static/uploads
# MAX_CONTENT_LENGTH=16777216 # Optional: 16MB
```

## 2. Application Configuration (`app/__init__.py` and `instance/config.py`)

The Flask application factory (`create_app` in `app/__init__.py`) loads configurations.

### Default Configuration
Base configurations are often set directly in `app/__init__.py` or a `config.py` file imported there.
```python
# In app/__init__.py
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['WTF_CSRF_ENABLED'] = True
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', os.path.join(app.root_path, 'static', 'uploads'))
app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)) # Default 16MB

# Configuration for allowed file extensions (example)
app.config['ALLOWED_EXTENSIONS'] = {
    'image': {'png', 'jpg', 'jpeg', 'gif'},
    'audio': {'mp3', 'wav', 'ogg'},
    'document': {'pdf', 'doc', 'docx', 'txt'}
}
# Ensure UPLOAD_FOLDER and its subdirectories exist
# (Code for this is typically in create_app() or FileUploadHandler)
```

### Instance Folder Configuration (`instance/config.py`)
- The `instance/` folder is outside the `app` package and can hold instance-specific configuration that should not be version-controlled (though `.env` is preferred for most secrets).
- Flask can be configured to load a `config.py` file from this folder if it exists: `app.config.from_pyfile('config.py', silent=True)`.
- The current project structure implies primary reliance on `.env` for overriding defaults, but `instance/config.py` could be used for more complex instance-specific settings if needed.

## 3. Configuration Categories

### Development Configuration
```env
FLASK_ENV=development
FLASK_DEBUG=True
DATABASE_URL=sqlite:///instance/site.db
UPLOAD_FOLDER=app/static/uploads
SECRET_KEY=dev-secret-key-change-in-production
```

### Production Configuration
```env
FLASK_ENV=production
FLASK_DEBUG=False
DATABASE_URL=postgresql://user:password@host:port/dbname
UPLOAD_FOLDER=/var/www/uploads
SECRET_KEY=very-long-random-production-secret-key
MAX_CONTENT_LENGTH=52428800  # 50MB
```

### Testing Configuration
```env
FLASK_ENV=testing
FLASK_DEBUG=False
DATABASE_URL=sqlite:///:memory:
UPLOAD_FOLDER=/tmp/test_uploads
SECRET_KEY=test-secret-key
WTF_CSRF_ENABLED=False  # Disable CSRF for testing
```

## 4. Security Considerations

### Secret Key Management
- **Development**: Use a simple key for local development
- **Production**: Generate a cryptographically secure random key
- **Never commit**: Secret keys should never be in version control

```python
# Generate a secure secret key
import secrets
secret_key = secrets.token_hex(32)
print(f"SECRET_KEY={secret_key}")
```

### Database URLs
- **Development**: Local SQLite file
- **Production**: Secure connection strings with proper credentials
- **Environment Variables**: Store sensitive database credentials in environment variables

### File Upload Security
```python
# Secure file upload configuration
UPLOAD_FOLDER = '/secure/upload/path'
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB limit
ALLOWED_EXTENSIONS = {
    'image': {'png', 'jpg', 'jpeg', 'gif'},
    'audio': {'mp3', 'wav', 'ogg'},
    'document': {'pdf', 'txt'}
}
```

## 5. Configuration Loading Order

The application loads configuration in the following order (later values override earlier ones):

1. **Default values** in `app/__init__.py`
2. **Instance configuration** from `instance/config.py` (if exists)
3. **Environment variables** from `.env` file
4. **System environment variables**

## 6. Configuration Validation

### Required Configuration Check
```python
def validate_config(app):
    """Validate that required configuration is present"""
    required_configs = ['SECRET_KEY', 'DATABASE_URL']
    
    for config in required_configs:
        if not app.config.get(config):
            raise ValueError(f"Required configuration {config} is missing")
    
    # Validate SECRET_KEY strength
    if len(app.config['SECRET_KEY']) < 32:
        raise ValueError("SECRET_KEY must be at least 32 characters long")
```

### File Upload Configuration Validation
```python
def validate_upload_config(app):
    """Validate file upload configuration"""
    upload_folder = app.config.get('UPLOAD_FOLDER')
    
    if not upload_folder:
        raise ValueError("UPLOAD_FOLDER must be configured")
    
    # Ensure upload directory exists
    os.makedirs(upload_folder, exist_ok=True)
    
    # Check write permissions
    if not os.access(upload_folder, os.W_OK):
        raise ValueError(f"Upload folder {upload_folder} is not writable")
```

## 7. Environment-Specific Settings

### Development Settings
- Debug mode enabled
- Detailed error pages
- Auto-reload on code changes
- Local SQLite database
- Relaxed security settings

### Production Settings
- Debug mode disabled
- Error logging to files
- Production database (PostgreSQL/MySQL)
- Strict security headers
- Performance optimizations

### Testing Settings
- In-memory database
- CSRF protection disabled
- Simplified authentication
- Mock external services

## 8. Configuration Best Practices

### Security
- Never hardcode secrets in source code
- Use environment variables for sensitive data
- Rotate secrets regularly
- Use different secrets for different environments

### Maintainability
- Document all configuration options
- Use descriptive variable names
- Provide sensible defaults
- Validate configuration on startup

### Deployment
- Use configuration management tools
- Automate environment setup
- Version control configuration templates
- Monitor configuration changes

## 9. Common Configuration Patterns

### Database Configuration
```python
# Support multiple database types
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///instance/site.db')

if DATABASE_URL.startswith('sqlite'):
    # SQLite-specific settings
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
elif DATABASE_URL.startswith('postgresql'):
    # PostgreSQL-specific settings
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
    }
```

### Feature Flags
```python
# Enable/disable features via configuration
FEATURES = {
    'user_registration': os.environ.get('ENABLE_REGISTRATION', 'true').lower() == 'true',
    'premium_content': os.environ.get('ENABLE_PREMIUM', 'true').lower() == 'true',
    'file_uploads': os.environ.get('ENABLE_UPLOADS', 'true').lower() == 'true',
}
```

Configuration values are accessed within the application using `current_app.config['CONFIG_KEY']`.
