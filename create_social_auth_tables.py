#!/usr/bin/env python3
"""
Manual script to create social auth tables
Run this to add the required social auth tables to your database.
"""

from app import create_app, db
from sqlalchemy import text

def create_social_auth_tables():
    """Create the social auth tables manually"""
    
    app = create_app()
    
    with app.app_context():
        print("Creating social auth tables...")
        
        # Create social_auth_association table
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS social_auth_association (
                id SERIAL PRIMARY KEY,
                server_url VARCHAR(255) NOT NULL,
                handle VARCHAR(255) NOT NULL,
                secret VARCHAR(255) NOT NULL,
                issued INTEGER NOT NULL,
                lifetime INTEGER NOT NULL,
                assoc_type VARCHAR(64) NOT NULL
            );
        """))
        
        # Create social_auth_code table
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS social_auth_code (
                id SERIAL PRIMARY KEY,
                email VARCHAR(254) NOT NULL,
                code VARCHAR(32) NOT NULL,
                verified BOOLEAN NOT NULL DEFAULT FALSE,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        # Create social_auth_nonce table
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS social_auth_nonce (
                id SERIAL PRIMARY KEY,
                server_url VARCHAR(255) NOT NULL,
                timestamp INTEGER NOT NULL,
                salt VARCHAR(65) NOT NULL
            );
        """))
        
        # Create social_auth_partial table
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS social_auth_partial (
                id SERIAL PRIMARY KEY,
                token VARCHAR(32) NOT NULL,
                next_step INTEGER NOT NULL DEFAULT 0,
                backend VARCHAR(32) NOT NULL,
                data TEXT NOT NULL DEFAULT '{}',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        # Create social_auth_usersocialauth table
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS social_auth_usersocialauth (
                id SERIAL PRIMARY KEY,
                provider VARCHAR(32) NOT NULL,
                uid VARCHAR(255) NOT NULL,
                extra_data TEXT NOT NULL DEFAULT '{}',
                user_id INTEGER NOT NULL,
                created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES "user" (id) ON DELETE CASCADE,
                UNIQUE (provider, uid)
            );
        """))
        
        # Create indexes for better performance
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS social_auth_usersocialauth_user_id_idx 
            ON social_auth_usersocialauth (user_id);
        """))
        
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS social_auth_usersocialauth_provider_uid_idx 
            ON social_auth_usersocialauth (provider, uid);
        """))
        
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS social_auth_code_email_idx 
            ON social_auth_code (email);
        """))
        
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS social_auth_code_code_idx 
            ON social_auth_code (code);
        """))
        
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS social_auth_partial_token_idx 
            ON social_auth_partial (token);
        """))
        
        # Commit the changes
        db.session.commit()
        
        print("✅ Social auth tables created successfully!")
        
        # Test if we can query the tables
        try:
            result = db.session.execute(text("SELECT COUNT(*) FROM social_auth_usersocialauth"))
            row = result.fetchone()
            count = row[0] if row else 0
            print(f"✅ social_auth_usersocialauth table working (current count: {count})")
        except Exception as e:
            print(f"❌ Error testing tables: {e}")

if __name__ == "__main__":
    create_social_auth_tables()
