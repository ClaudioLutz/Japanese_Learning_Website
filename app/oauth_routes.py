# app/oauth_routes.py
from flask import Blueprint, request, redirect, url_for, session, current_app
from flask_login import login_user
import requests
import logging
from app.models import User
from app import db

logger = logging.getLogger(__name__)

oauth_bp = Blueprint('oauth', __name__, url_prefix='/auth')

@oauth_bp.route('/complete/google-oauth2/')
def complete_google_oauth():
    """
    Custom Google OAuth completion handler that bypasses the problematic social auth library
    """
    try:
        # Get the authorization code from the callback
        code = request.args.get('code')
        state = request.args.get('state')
        
        if not code:
            logger.error("No authorization code received from Google")
            return redirect('/login?error=oauth_failed')
        
        # Exchange authorization code for access token
        token_url = 'https://oauth2.googleapis.com/token'
        token_data = {
            'client_id': current_app.config['SOCIAL_AUTH_GOOGLE_OAUTH2_KEY'],
            'client_secret': current_app.config['SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET'],
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': request.url_root.rstrip('/') + '/auth/complete/google-oauth2/'
        }
        
        token_response = requests.post(token_url, data=token_data)
        token_json = token_response.json()
        
        if 'access_token' not in token_json:
            logger.error(f"Failed to get access token: {token_json}")
            return redirect('/login?error=oauth_failed')
        
        # Get user info from Google
        user_info_url = f"https://www.googleapis.com/oauth2/v2/userinfo?access_token={token_json['access_token']}"
        user_response = requests.get(user_info_url)
        user_data = user_response.json()
        
        if 'email' not in user_data:
            logger.error(f"Failed to get user email: {user_data}")
            return redirect('/login?error=oauth_failed')
        
        # Find or create user
        email = user_data['email']
        user = User.query.filter_by(email=email).first()
        
        if not user:
            # Create new user
            username = email.split('@')[0]
            # Ensure username is unique
            base_username = username
            counter = 1
            while User.query.filter_by(username=username).first():
                username = f"{base_username}{counter}"
                counter += 1
            
            user = User(
                username=username,
                email=email,
                password_hash='',  # No password for OAuth users
                subscription_level='free'
            )
            db.session.add(user)
            db.session.commit()
            logger.info(f"Created new user {email} via Google OAuth")
        
        # Log the user in
        login_user(user, remember=True)
        logger.info(f"User {email} logged in via Google OAuth")
        
        # Create social auth record if it doesn't exist
        from sqlalchemy import text
        import json
        
        check_sql = text("""
            SELECT COUNT(*) FROM social_auth_usersocialauth 
            WHERE provider = 'google-oauth2' AND uid = :uid
        """)
        
        google_uid = user_data.get('id', user_data.get('sub', email))
        result = db.session.execute(check_sql, {'uid': str(google_uid)})
        
        if result.scalar() == 0:
            # Create social auth record
            extra_data = json.dumps(user_data)
            sql = text("""
                INSERT INTO social_auth_usersocialauth (provider, uid, user_id, extra_data, created, modified)
                VALUES ('google-oauth2', :uid, :user_id, :extra_data, NOW(), NOW())
            """)
            
            db.session.execute(sql, {
                'uid': str(google_uid),
                'user_id': user.id,
                'extra_data': extra_data
            })
            db.session.commit()
            logger.info(f"Created social auth record for user {email}")
        
        # Redirect to homepage
        return redirect('/')
        
    except Exception as e:
        logger.error(f"Error in Google OAuth completion: {e}")
        return redirect('/login?error=oauth_failed')
