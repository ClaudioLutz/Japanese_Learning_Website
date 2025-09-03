import os

# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True

# Secret key for session management.
SECRET_KEY = os.environ.get('SECRET_KEY') or 'mysecretkey'

# Connect to the database - Use SQLite for local development testing
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///japanese_learning_local.db'
SQLALCHEMY_TRACK_MODIFICATIONS = False

# PostFinance Checkout Configuration
POSTFINANCE_SPACE_ID = os.environ.get('POSTFINANCE_SPACE_ID')
POSTFINANCE_USER_ID = os.environ.get('POSTFINANCE_USER_ID')
POSTFINANCE_API_SECRET = os.environ.get('POSTFINANCE_API_SECRET')

# Payment redirect URLs - Phase 2.5 Configuration
PAYMENT_SUCCESS_URL = os.environ.get('PAYMENT_SUCCESS_URL', 'http://localhost:5000/payment/success')
PAYMENT_FAILURE_URL = os.environ.get('PAYMENT_FAILURE_URL', 'http://localhost:5000/payment/failed')

# Payment system configuration
PAYMENT_TIMEOUT_HOURS = int(os.environ.get('PAYMENT_TIMEOUT_HOURS', 1))
PAYMENT_MAX_ATTEMPTS = int(os.environ.get('PAYMENT_MAX_ATTEMPTS', 3))

# Mock payment configuration for development
MOCK_PAYMENTS_ENABLED = os.environ.get('MOCK_PAYMENTS_ENABLED', 'True').lower() == 'true'

# Basic validation to ensure payment config is loaded (optional for deployment)
if not all([POSTFINANCE_SPACE_ID, POSTFINANCE_USER_ID, POSTFINANCE_API_SECRET]):
    print("⚠️  WARNING: PostFinance Checkout credentials are not configured. Using mock payment system.")
    MOCK_PAYMENTS_ENABLED = True
