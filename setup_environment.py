#!/usr/bin/env python3
"""
Environment Setup Script for Japanese Learning Website
This script helps generate secure keys and test database connections.
"""

import os
import secrets
import sys
from dotenv import load_dotenv

def generate_secret_keys():
    """Generate secure secret keys for Flask application"""
    print("🔐 Generating secure secret keys...")
    
    secret_key = secrets.token_urlsafe(32)
    csrf_key = secrets.token_urlsafe(32)
    
    print("\n📋 Add these to your .env file:")
    print(f'SECRET_KEY="{secret_key}"')
    print(f'WTF_CSRF_SECRET_KEY="{csrf_key}"')
    print()

def test_database_connection():
    """Test PostgreSQL database connection"""
    print("🔍 Testing database connection...")
    
    load_dotenv()
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        return False
    
    if 'sqlite' in database_url.lower():
        print("ℹ️  Currently using SQLite database")
        print(f"   Database URL: {database_url}")
        return True
    
    try:
        import psycopg2
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ PostgreSQL connection successful!")
        if version:
            print(f"   Version: {version[0]}")
        cursor.close()
        conn.close()
        return True
    except ImportError:
        print("❌ psycopg2 not installed. Run: pip install psycopg2-binary")
        return False
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("\n💡 Troubleshooting tips:")
        print("   1. Make sure PostgreSQL is running")
        print("   2. Check your DATABASE_URL in .env file")
        print("   3. Verify database and user exist")
        print("   4. Check firewall settings")
        return False

def check_oauth_config():
    """Check Google OAuth configuration"""
    print("🔍 Checking Google OAuth configuration...")
    
    load_dotenv()
    client_id = os.environ.get('GOOGLE_CLIENT_ID')
    client_secret = os.environ.get('GOOGLE_CLIENT_SECRET')
    
    if not client_id or client_id == 'your-google-client-id-here':
        print("⚠️  GOOGLE_CLIENT_ID not configured (using placeholder)")
    else:
        print("✅ GOOGLE_CLIENT_ID configured")
    
    if not client_secret or client_secret == 'your-google-client-secret-here':
        print("⚠️  GOOGLE_CLIENT_SECRET not configured (using placeholder)")
    else:
        print("✅ GOOGLE_CLIENT_SECRET configured")
    
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key or secret_key == 'your-secret-key-here':
        print("⚠️  SECRET_KEY not configured (using placeholder)")
    else:
        print("✅ SECRET_KEY configured")

def check_required_packages():
    """Check if required packages are installed"""
    print("📦 Checking required packages...")
    
    required_packages = [
        'flask',
        'flask_sqlalchemy',
        'flask_login',
        'flask_migrate',
        'social_flask',
        'psycopg2'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n💡 Install missing packages with:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False
    
    return True

def main():
    """Main setup function"""
    print("🚀 Japanese Learning Website - Environment Setup")
    print("=" * 50)
    
    # Generate secret keys
    generate_secret_keys()
    
    # Check packages
    packages_ok = check_required_packages()
    print()
    
    # Test database
    db_ok = test_database_connection()
    print()
    
    # Check OAuth config
    check_oauth_config()
    print()
    
    # Summary
    print("📊 Setup Summary:")
    print(f"   Packages: {'✅' if packages_ok else '❌'}")
    print(f"   Database: {'✅' if db_ok else '❌'}")
    print()
    
    if packages_ok and db_ok:
        print("🎉 Environment setup looks good!")
        print("\n📋 Next steps:")
        print("   1. Update .env with generated secret keys")
        print("   2. Set up Google OAuth credentials (see google_oauth_setup_guide.md)")
        print("   3. Run database migrations: flask db upgrade")
        print("   4. Start the application: python run.py")
    else:
        print("⚠️  Please fix the issues above before proceeding")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
