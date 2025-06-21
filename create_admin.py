#!/usr/bin/env python3
"""
Script to create an admin user for the Japanese Learning Website.
Run this script to create an admin account for testing.
"""

from app import create_app, db
from app.models import User

def create_admin_user():
    app = create_app()
    
    with app.app_context():
        # Check if admin user already exists
        admin_user = User.query.filter_by(email='admin@example.com').first()
        
        if admin_user:
            print("Admin user already exists!")
            print(f"Email: {admin_user.email}")
            print(f"Username: {admin_user.username}")
            print(f"Is Admin: {admin_user.is_admin}")
            return
        
        # Create admin user
        admin = User(
            username='admin',
            email='admin@example.com',
            is_admin=True,
            subscription_level='premium'  # Give admin premium access too
        )
        admin.set_password('admin123')  # Change this password in production!
        
        db.session.add(admin)
        db.session.commit()
        
        print("Admin user created successfully!")
        print("Email: admin@example.com")
        print("Password: admin123")
        print("Username: admin")
        print("Is Admin: True")
        print("\nYou can now log in with these credentials to access the admin panel.")

if __name__ == '__main__':
    create_admin_user()
