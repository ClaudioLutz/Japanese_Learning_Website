# app/social_auth_config.py
from flask_login import login_user
from app.models import User
from app import db
import logging

logger = logging.getLogger(__name__)

def fix_google_uid(strategy, details, backend, uid=None, response=None, *args, **kwargs):
    """
    Fix Google OAuth uid to use the 'sub' field instead of email
    """
    if backend.name == 'google-oauth2' and response and 'sub' in response:
        # Use Google's 'sub' field as the uid instead of email
        fixed_uid = response['sub']
        logger.info(f"PIPELINE DEBUG - fix_google_uid: changing uid from {uid} to {fixed_uid}")
        return {'uid': fixed_uid}
    return {'uid': uid}

def custom_associate_user(strategy, details, backend, user=None, uid=None, *args, **kwargs):
    """
    Custom associate_user function that properly handles the uid parameter
    """
    if user and uid:
        # Import UserSocialAuth model
        from social_flask_sqlalchemy.models import UserSocialAuth
        
        # Check if social auth record already exists using raw SQL
        from sqlalchemy import text
        
        check_sql = text("""
            SELECT COUNT(*) FROM social_auth_usersocialauth 
            WHERE provider = :provider AND uid = :uid
        """)
        
        result = db.session.execute(check_sql, {
            'provider': backend.name,
            'uid': str(uid)
        })
        
        count = result.scalar() or 0
        record_exists = count > 0
        
        if not record_exists:
            # Create new social auth record with correct uid manually
            logger.info(f"PIPELINE DEBUG - custom_associate_user: Creating social auth record with uid={uid}")
            try:
                # Create the UserSocialAuth record using raw SQL to ensure all fields are included
                from sqlalchemy import text
                import json
                
                extra_data_json = json.dumps(kwargs.get('response', {}))
                
                sql = text("""
                    INSERT INTO social_auth_usersocialauth (provider, uid, user_id, extra_data, created, modified)
                    VALUES (:provider, :uid, :user_id, :extra_data, NOW(), NOW())
                """)
                
                db.session.execute(sql, {
                    'provider': backend.name,
                    'uid': uid,
                    'user_id': user.id,
                    'extra_data': extra_data_json
                })
                
                db.session.commit()
                logger.info(f"PIPELINE DEBUG - custom_associate_user: Successfully created social auth record")
            except Exception as e:
                db.session.rollback()
                logger.error(f"PIPELINE DEBUG - custom_associate_user: Error creating social auth: {e}")
                raise
        else:
            logger.info(f"PIPELINE DEBUG - custom_associate_user: Social auth record already exists")
    
    return {'user': user, 'uid': uid, 'details': details, **kwargs}

def create_user_and_login(strategy, details, backend, user=None, uid=None, *args, **kwargs):
    """
    Custom pipeline function to create user and log them in with Flask-Login
    """
    if user:
        # User already exists, just log them in
        login_user(user, remember=True)
        logger.info(f"Existing user {user.email} logged in via Google OAuth")
        return {'user': user, 'uid': uid, 'details': details, **kwargs}
    
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
        return {'user': existing_user, 'uid': uid, 'details': details, **kwargs}
    
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
        return {'user': new_user, 'uid': uid, 'details': details, **kwargs}
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating user via Google OAuth: {e}")
        return None
