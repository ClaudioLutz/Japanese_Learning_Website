import os

# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True

# Secret key for session management.
SECRET_KEY = os.environ.get('SECRET_KEY') or 'mysecretkey'

# Connect to the database
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://postgres:E8BnuCBpWKP@localhost:5433/japanese_learning'
SQLALCHEMY_TRACK_MODIFICATIONS = False

# PostFinance Checkout Configuration
POSTFINANCE_SPACE_ID = os.environ.get('POSTFINANCE_SPACE_ID')
POSTFINANCE_USER_ID = os.environ.get('POSTFINANCE_USER_ID')
POSTFINANCE_API_SECRET = os.environ.get('POSTFINANCE_API_SECRET')
PAYMENT_SUCCESS_URL = os.environ.get('PAYMENT_SUCCESS_URL')
PAYMENT_FAILURE_URL = os.environ.get('PAYMENT_FAILURE_URL')

# Basic validation to ensure payment config is loaded
if not all([POSTFINANCE_SPACE_ID, POSTFINANCE_USER_ID, POSTFINANCE_API_SECRET]):
    raise ValueError("PostFinance Checkout credentials are not fully configured in the environment.")
