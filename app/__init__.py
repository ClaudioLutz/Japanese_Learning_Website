# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect # Import CSRFProtect
import os

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect() # Initialize CSRFProtect

login_manager.login_view = 'routes.login' # Where to redirect if login required

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    # Ensure SECRET_KEY is set, otherwise CSRF protection (and sessions) won't work.
    # This is typically loaded from config.py or environment variables.
    # Example: app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'a_default_secret_key'
    # Example: app.config['WTF_CSRF_SECRET_KEY'] = os.environ.get('WTF_CSRF_SECRET_KEY') or 'a_csrf_secret_key'
    app.config.from_pyfile('config.py') # Load config from instance folder

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app) # Initialize CSRFProtect with the app

    # Import models and routes here to avoid circular imports
    from app import models
    from app import routes

    app.register_blueprint(routes.bp) # Register the blueprint

    with app.app_context():
        db.create_all() # Create database tables for our models

    return app
