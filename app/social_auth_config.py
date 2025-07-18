# app/social_auth_config.py
from flask_login import login_user
from app.models import User
from app import db
import logging

logger = logging.getLogger(__name__)

def create_user_and_login(strategy, details, backend, user=None, *args, **kwargs):
    """
    Custom pipeline function to create user and log them in with Flask-Login
    """
    if user:
        # User already exists, just log them in
        login_user(user, remember=True)
        logger.info(f"Existing user {user.email} logged in via Google OAuth")
        return {'user': user}
    
    # Create new user
    email = details.get('email')
    username = details.get('username') or email.split('@')[0]
    
    if not email:
        logger.error("No email provided by Google OAuth")
        return None
    
    # Check if user with this email already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        # Link the social account to existing user
        login_user(existing_user, remember=True)
        logger.info(f"Linked Google account to existing user {existing_user.email}")
        return {'user': existing_user}
    
    # Ensure username is unique
    base_username = username
    counter = 1
    while User.query.filter_by(username=username).first():
        username = f"{base_username}{counter}"
        counter += 1
    
    # Create new user
    new_user = User(
        username=username,
        email=email,
        password_hash='',  # No password for OAuth users
        subscription_level='free'
    )
    
    try:
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user, remember=True)
        logger.info(f"Created new user {new_user.email} via Google OAuth")
        return {'user': new_user}
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating user via Google OAuth: {e}")
        return None
