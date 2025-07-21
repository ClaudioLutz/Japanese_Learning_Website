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
        'SOCIAL_AUTH_LOGIN_REDIRECT_URL': '/',
        'SOCIAL_AUTH_LOGIN_ERROR_URL': '/login',
        'SOCIAL_AUTH_PIPELINE': (
            'social_core.pipeline.social_auth.social_details',
            'social_core.pipeline.social_auth.social_uid',
            'social_core.pipeline.social_auth.auth_allowed',
            'social_core.pipeline.social_auth.social_user',
            'social_core.pipeline.user.get_username',
            'app.social_auth_config.create_user_and_login',
            'social_core.pipeline.social_auth.associate_user',
            'social_core.pipeline.social_auth.load_extra_data',
            'social_core.pipeline.user.user_details',
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
    from app.models import Course
    from app import routes
    from app.utils import convert_to_embed_url

    # Register Jinja filter
    app.jinja_env.filters['to_embed_url'] = convert_to_embed_url

    # Register blueprints
    app.register_blueprint(routes.bp) # Register the main routes blueprint
    
    # Register social auth blueprint
    from social_flask.routes import social_auth
    app.register_blueprint(social_auth, url_prefix='/auth')

    return app
