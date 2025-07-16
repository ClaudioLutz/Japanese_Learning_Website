#!/usr/bin/env python3
"""
Complete setup script for the unified authentication system.
This script will:
1. Migrate the database (add is_admin column if needed)
2. Create all necessary tables
3. Create an admin user
"""

import sqlite3
import os
from app import create_app, db
from app.models import User

def setup_unified_auth():
    app = create_app()
    
    with app.app_context():
        print("=== Setting up Unified Authentication System ===\n")
        
        # Step 1: Database Migration
        print("Step 1: Database Migration")
        print("-" * 30)
        
        # Get the database path - handle both absolute and relative paths
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        if db_uri.startswith('sqlite:///'):
            db_path = db_uri.replace('sqlite:///', '')
            # If it's a relative path, make it relative to instance folder
            if not os.path.isabs(db_path):
                db_path = os.path.join(app.instance_path, db_path)
        else:
            print(f"Unsupported database URI: {db_uri}")
            return
        
        print(f"Database location: {db_path}")
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Connect directly to SQLite
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Check if user table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user'")
            user_table_exists = cursor.fetchone() is not None
            
            if user_table_exists:
                print("✓ User table exists, checking for is_admin column...")
                # Check if is_admin column already exists
                cursor.execute("PRAGMA table_info(user)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if 'is_admin' in columns:
                    print("✓ Column 'is_admin' already exists in the user table.")
                else:
                    # Add the is_admin column with default value False
                    cursor.execute("ALTER TABLE user ADD COLUMN is_admin BOOLEAN DEFAULT 0 NOT NULL")
                    print("✓ Added 'is_admin' column to user table.")
            else:
                print("ℹ User table doesn't exist. Will create all tables using SQLAlchemy.")
            
            conn.commit()
            
        except sqlite3.Error as e:
            print(f"✗ Error during migration: {e}")
            conn.rollback()
            return
        finally:
            conn.close()
        
        # Step 2: Create all tables
        print("\nStep 2: Creating Tables")
        print("-" * 30)
        try:
            db.create_all()
            print("✓ All tables created/verified.")
        except Exception as e:
            print(f"✗ Error creating tables: {e}")
            return
        
        # Step 3: Create admin user
        print("\nStep 3: Creating Admin User")
        print("-" * 30)
        
        # Check if admin user already exists
        admin_user = User.query.filter_by(email='admin@example.com').first()
        
        if admin_user:
            print("ℹ Admin user already exists!")
            print(f"  Email: {admin_user.email}")
            print(f"  Username: {admin_user.username}")
            print(f"  Is Admin: {admin_user.is_admin}")
            
            # Update existing user to be admin if not already
            if not admin_user.is_admin:
                admin_user.is_admin = True
                admin_user.subscription_level = 'premium'
                db.session.commit()
                print("✓ Updated existing user to admin status.")
        else:
            # Create admin user
            try:
                admin = User(
                    username='admin',
                    email='admin@example.com',
                    is_admin=True,
                    subscription_level='premium'
                )
                admin.set_password('admin123')
                
                db.session.add(admin)
                db.session.commit()
                
                print("✓ Admin user created successfully!")
                print("  Email: admin@example.com")
                print("  Password: admin123")
                print("  Username: admin")
                print("  Is Admin: True")
            except Exception as e:
                print(f"✗ Error creating admin user: {e}")
                return
        
        print("\n=== Setup Complete! ===")
        print("\nNext steps:")
        print("1. Run: python run.py")
        print("2. Go to: http://localhost:5000/login")
        print("3. Login with: admin@example.com / admin123")
        print("4. You'll be redirected to the admin panel automatically")
        print("\nNote: Change the admin password in production!")

if __name__ == '__main__':
    setup_unified_auth()
