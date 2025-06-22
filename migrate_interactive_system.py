from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, upgrade
import os

# Configure the Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with a real secret key
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///../instance/app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Import models to ensure they are registered with SQLAlchemy
from app import models

def run_migration():
    """
    Generates a new migration script and applies it to the database.
    """
    # Set the FLASK_APP environment variable
    os.environ['FLASK_APP'] = 'run.py'

    with app.app_context():
        # Initialize migrations if the directory doesn't exist
        if not os.path.exists('migrations'):
            print("Initializing migrations folder...")
            os.system('flask db init')

        print("Generating migration script...")
        # Generate migration script
        os.system('flask db migrate -m "Add interactive content models"')

        print("\nApplying migration...")
        # Apply the migration
        os.system('flask db upgrade')

        print("\nMigration complete.")

if __name__ == '__main__':
    run_migration()
