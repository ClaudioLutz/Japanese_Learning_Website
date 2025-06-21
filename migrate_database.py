#!/usr/bin/env python3
"""
Database migration script to add the is_admin column to existing User table.
Run this script before using the unified authentication system.
"""

import sqlite3
import os
from app import create_app, db
from app.models import User

def migrate_database():
    app = create_app()
    
    with app.app_context():
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
        
        print(f"Migrating database at: {db_path}")
        
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
                print("User table exists, checking for is_admin column...")
                # Check if is_admin column already exists
                cursor.execute("PRAGMA table_info(user)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if 'is_admin' in columns:
                    print("Column 'is_admin' already exists in the user table.")
                else:
                    # Add the is_admin column with default value False
                    cursor.execute("ALTER TABLE user ADD COLUMN is_admin BOOLEAN DEFAULT 0 NOT NULL")
                    print("Added 'is_admin' column to user table.")
            else:
                print("User table doesn't exist. Will create all tables using SQLAlchemy.")
            
            conn.commit()
            print("Database migration completed successfully!")
            
        except sqlite3.Error as e:
            print(f"Error during migration: {e}")
            conn.rollback()
        finally:
            conn.close()
        
        # Now create all missing tables using SQLAlchemy
        print("Creating any missing tables...")
        db.create_all()
        print("All tables created/verified.")

if __name__ == '__main__':
    migrate_database()
