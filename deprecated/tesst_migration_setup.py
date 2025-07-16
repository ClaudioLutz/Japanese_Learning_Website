#!/usr/bin/env python3
"""
Migration Setup Test Script
===========================

This script tests the migration setup before running the full migration.
It verifies database connections, checks table existence, and validates prerequisites.

Usage: python test_migration_setup.py
"""

import os
import sys
import sqlite3
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

def test_environment_variables():
    """Test that required environment variables are set."""
    print("🔍 Testing environment variables...")
    
    db_password = os.getenv('DB_PASSWORD')
    if not db_password:
        print("❌ DB_PASSWORD environment variable is not set!")
        print("   Run: export DB_PASSWORD='your_password'")
        return False
    else:
        print("✅ DB_PASSWORD environment variable is set")
        return True

def test_sqlite_connection():
    """Test SQLite database connection and list tables."""
    print("\n🔍 Testing SQLite connection...")
    
    sqlite_path = 'instance/site.db'
    
    if not os.path.exists(sqlite_path):
        print(f"❌ SQLite database not found at: {sqlite_path}")
        return False, []
    
    try:
        # Test with sqlite3 first
        conn = sqlite3.connect(sqlite_path)
        cursor = conn.cursor()
        
        # Get table list
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            AND name NOT LIKE 'sqlite_%'
            AND name NOT LIKE 'alembic_%'
            ORDER BY name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        # Get row counts
        table_info = []
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            table_info.append((table, count))
        
        conn.close()
        
        print(f"✅ SQLite connection successful")
        print(f"   Database file: {sqlite_path}")
        print(f"   Found {len(tables)} tables:")
        for table, count in table_info:
            print(f"     - {table}: {count:,} rows")
        
        return True, tables
        
    except Exception as e:
        print(f"❌ SQLite connection failed: {str(e)}")
        return False, []

def test_postgresql_connection():
    """Test PostgreSQL connection via Cloud SQL Auth Proxy."""
    print("\n🔍 Testing PostgreSQL connection...")
    
    db_password = os.getenv('DB_PASSWORD')
    if not db_password:
        print("❌ Cannot test PostgreSQL: DB_PASSWORD not set")
        return False, []
    
    try:
        postgres_url = f"postgresql://app_user:{db_password}@localhost:5432/japanese_learning"
        engine = create_engine(postgres_url)
        
        with engine.connect() as conn:
            # Test basic connection
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ PostgreSQL connection successful")
            print(f"   Version: {version}")
            
            # Get table list
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            
            # Get row counts
            table_info = []
            for table in tables:
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.fetchone()[0]
                    table_info.append((table, count))
                except Exception as e:
                    table_info.append((table, f"Error: {str(e)}"))
            
            print(f"   Found {len(tables)} tables:")
            for table, count in table_info:
                if isinstance(count, int):
                    print(f"     - {table}: {count:,} rows")
                else:
                    print(f"     - {table}: {count}")
            
            return True, tables
            
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {str(e)}")
        print("   Common causes:")
        print("   - Cloud SQL Auth Proxy not running")
        print("   - Incorrect password")
        print("   - Wrong instance connection name")
        print("   - Firewall blocking port 5432")
        return False, []

def test_python_dependencies():
    """Test that required Python packages are installed."""
    print("\n🔍 Testing Python dependencies...")
    
    required_packages = [
        'pandas',
        'sqlalchemy',
        'psycopg2'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} is installed")
        except ImportError:
            print(f"❌ {package} is NOT installed")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n   Install missing packages with:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False
    
    return True

def compare_table_structures(sqlite_tables, postgres_tables):
    """Compare table lists between SQLite and PostgreSQL."""
    print("\n🔍 Analyzing table structures...")
    
    sqlite_set = set(sqlite_tables)
    postgres_set = set(postgres_tables)
    
    print(f"✅ SQLite tables to be migrated ({len(sqlite_tables)}):")
    for table in sorted(sqlite_tables):
        print(f"     - {table}")
    
    if postgres_tables:
        print(f"ℹ️  Existing PostgreSQL tables ({len(postgres_tables)}):")
        for table in sorted(postgres_tables):
            print(f"     - {table}")
        
        # Tables that will be recreated
        common_tables = sqlite_set & postgres_set
        if common_tables:
            print(f"⚠️  Tables that will be dropped and recreated ({len(common_tables)}):")
            for table in sorted(common_tables):
                print(f"     - {table}")
    else:
        print("ℹ️  No existing tables in PostgreSQL - all will be created fresh")
    
    print("✅ Migration script will automatically create all required tables")
    return True  # Always return True since we create tables automatically

def main():
    """Run all setup tests."""
    print("=" * 60)
    print("MIGRATION SETUP TEST")
    print("=" * 60)
    
    all_tests_passed = True
    
    # Test 1: Environment variables
    if not test_environment_variables():
        all_tests_passed = False
    
    # Test 2: Python dependencies
    if not test_python_dependencies():
        all_tests_passed = False
    
    # Test 3: SQLite connection
    sqlite_ok, sqlite_tables = test_sqlite_connection()
    if not sqlite_ok:
        all_tests_passed = False
    
    # Test 4: PostgreSQL connection
    postgres_ok, postgres_tables = test_postgresql_connection()
    if not postgres_ok:
        all_tests_passed = False
    
    # Test 5: Compare table structures
    if sqlite_ok and postgres_ok:
        if not compare_table_structures(sqlite_tables, postgres_tables):
            all_tests_passed = False
    
    # Final result
    print("\n" + "=" * 60)
    if all_tests_passed:
        print("🎉 ALL TESTS PASSED - Ready for migration!")
        print("\nNext steps:")
        print("1. Run: python migrate_data.py")
        print("2. Monitor the migration progress")
        print("3. Check the generated log file for details")
    else:
        print("❌ SOME TESTS FAILED - Fix issues before migration")
        print("\nReview the errors above and:")
        print("1. Install missing dependencies")
        print("2. Set required environment variables")
        print("3. Start Cloud SQL Auth Proxy")
        print("4. Run this test script again")
    
    print("=" * 60)
    
    return 0 if all_tests_passed else 1

if __name__ == "__main__":
    sys.exit(main())
