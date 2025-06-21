# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'routes.login' # Where to redirect if login required

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_pyfile('config.py') # Load config from instance folder

    db.init_app(app)
    login_manager.init_app(app)

    # Import models and routes here to avoid circular imports
    from app import models
    from app import routes

    app.register_blueprint(routes.bp) # Register the blueprint

    with app.app_context():
        db.create_all() # Create database tables for our models

    return app
