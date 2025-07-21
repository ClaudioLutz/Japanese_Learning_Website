import os

# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True

# Secret key for session management. You should generate a random key in a real application.
SECRET_KEY = 'mysecretkey'

# Connect to the database - Use environment variable if available, otherwise fallback to SQLite
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://postgres:E8BnuCBpWKP@localhost:5433/japanese_learning'

# Turn off the Flask-SQLAlchemy event system and warning
SQLALCHEMY_TRACK_MODIFICATIONS = False
