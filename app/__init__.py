# app/__init__.py
import logging
logging.basicConfig(level=logging.INFO)
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect # Import CSRFProtect
import os
from werkzeug.utils import secure_filename

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect() # Initialize CSRFProtect

login_manager.login_view = 'routes.login' # type: ignore
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    # Ensure SECRET_KEY is set, otherwise CSRF protection (and sessions) won't work.
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    app.config['WTF_CSRF_SECRET_KEY'] = os.environ.get('WTF_CSRF_SECRET_KEY') or 'dev-csrf-secret-key-change-in-production'
    
    app.config.from_pyfile('config.py', silent=True) # Load config from instance folder
    
    # Force reload environment variables
    from dotenv import load_dotenv
    load_dotenv(override=True)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or \
        'postgresql://postgres:E8BnuCBpWKP@localhost:5433/japanese_learning'
    
    # Debug: Print the actual DATABASE_URI being used
    print(f"DEBUG: Using DATABASE_URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    # Google OAuth Configuration
    app.config.update({
        'SOCIAL_AUTH_GOOGLE_OAUTH2_KEY': os.environ.get('GOOGLE_CLIENT_ID'),
        'SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET': os.environ.get('GOOGLE_CLIENT_SECRET'),
        'SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE': ['openid', 'email', 'profile'],
        'SOCIAL_AUTH_GOOGLE_OAUTH2_USE_PKCE': True,
        'SOCIAL_AUTH_GOOGLE_OAUTH2_USER_ID_KEY': 'sub',  # Use Google's 'sub' field as the uid instead of email
        'SOCIAL_AUTH_LOGIN_REDIRECT_URL': '/',
        'SOCIAL_AUTH_LOGIN_ERROR_URL': '/login',
        'SOCIAL_AUTH_AUTHENTICATION_BACKENDS': [
            'social_core.backends.google.GoogleOAuth2',
        ],
        'SOCIAL_AUTH_USER_MODEL': 'app.models.User',
        'SOCIAL_AUTH_STORAGE': 'social_flask_sqlalchemy.models.FlaskStorage',
        'SOCIAL_AUTH_PIPELINE': (
            'social_core.pipeline.social_auth.social_details',
            'social_core.pipeline.social_auth.social_uid',
            'app.social_auth_config.fix_google_uid',  # Fix Google uid to use 'sub' field
            'social_core.pipeline.social_auth.auth_allowed',
            'app.social_auth_config.create_user_and_login',  # Custom function handles everything
            'app.social_auth_config.custom_associate_user',  # Custom function handles social auth records
        ),
    })
    
    # Get absolute path for the upload folder
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    UPLOAD_FOLDER = os.path.join(project_root, 'app', 'static', 'uploads')
    
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max file size
    ALLOWED_EXTENSIONS = {
        'image': {'png', 'jpg', 'jpeg', 'gif', 'webp'},
        'video': {'mp4', 'webm', 'ogg', 'avi', 'mov'},
        'audio': {'mp3', 'wav', 'ogg', 'aac', 'm4a'}
    }

    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
    app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS

    # Create upload directories if they don't exist
    upload_dirs = [
        os.path.join(UPLOAD_FOLDER, 'lessons', 'images'),
        os.path.join(UPLOAD_FOLDER, 'lessons', 'videos'),
        os.path.join(UPLOAD_FOLDER, 'lessons', 'audio'),
        os.path.join(UPLOAD_FOLDER, 'temp')
    ]
    for directory in upload_dirs:
        os.makedirs(directory, exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app) # Initialize CSRFProtect with the app

    # Import models and routes here to avoid circular imports
    from app import models
    from app.models import Course, User
    
    # Initialize social auth storage after models are imported
    from social_flask_sqlalchemy.models import UserSocialAuth
    UserSocialAuth.app_session = db.session
    from app import routes
    from app.utils import convert_to_embed_url
    
    # Add user to Flask global context for social auth
    @app.before_request
    def load_current_user():
        from flask import g
        from flask_login import current_user
        g.user = current_user if current_user.is_authenticated else None

    # Register Jinja filters
    app.jinja_env.filters['to_embed_url'] = convert_to_embed_url
    
    # Add JSON parsing filter for templates
    import json
    def from_json_filter(value):
        if not value:
            return []
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return []
    
    app.jinja_env.filters['from_json'] = from_json_filter

    # Register blueprints
    app.register_blueprint(routes.bp) # Register the main routes blueprint
    
    # Register custom OAuth blueprint BEFORE social auth to override it
    from app.oauth_routes import oauth_bp
    app.register_blueprint(oauth_bp)
    
    # Register debug routes blueprint for troubleshooting
    from app.debug_routes import debug_bp
    app.register_blueprint(debug_bp)
    
    # Register social auth blueprint (for /auth/login/google-oauth2/ route only)
    from social_flask.routes import social_auth
    app.register_blueprint(social_auth, url_prefix='/auth')

    return app
