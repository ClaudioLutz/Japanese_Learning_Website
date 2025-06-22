# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect # Import CSRFProtect
import os
from werkzeug.utils import secure_filename

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect() # Initialize CSRFProtect

login_manager.login_view = 'routes.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    # Ensure SECRET_KEY is set, otherwise CSRF protection (and sessions) won't work.
    # This is typically loaded from config.py or environment variables.
    # Example: app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'a_default_secret_key'
    # Example: app.config['WTF_CSRF_SECRET_KEY'] = os.environ.get('WTF_CSRF_SECRET_KEY') or 'a_csrf_secret_key'
    app.config.from_pyfile('config.py') # Load config from instance folder

    # File upload configuration
    UPLOAD_FOLDER = os.path.join('app', 'static', 'uploads')
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
    login_manager.init_app(app)
    csrf.init_app(app) # Initialize CSRFProtect with the app

    # Import models and routes here to avoid circular imports
    from app import models
    from app import routes
    from app.utils import convert_to_embed_url

    # Register Jinja filter
    app.jinja_env.filters['to_embed_url'] = convert_to_embed_url

    app.register_blueprint(routes.bp) # Register the blueprint

    with app.app_context():
        db.create_all() # Create database tables for our models

    return app
