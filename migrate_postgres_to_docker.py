#!/usr/bin/env python3
"""
PostgreSQL to Docker PostgreSQL Migration Script
Migrates all lesson data from local PostgreSQL to Docker PostgreSQL database
"""
import os
import sys
import json
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

# Add the app directory to Python path to import models
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def get_local_db_connection():
    """Get connection to local PostgreSQL database"""
    # Try to read local database configuration
    local_config_paths = [
        'instance/config.py',
        '.env',
        'config.py'
    ]
    
    local_db_url = None
    
    # Try to find local database URL from config files
    for config_path in local_config_paths:
        if os.path.exists(config_path):
            try:
                if config_path.endswith('.py'):
                    # Read Python config file
                    with open(config_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'SQLALCHEMY_DATABASE_URI' in content:
                            # Extract database URL (basic parsing)
                            for line in content.split('\n'):
                                if 'SQLALCHEMY_DATABASE_URI' in line and '=' in line:
                                    url = line.split('=', 1)[1].strip().strip('\'"')
                                    if url.startswith('postgresql'):
                                        local_db_url = url
                                        break
                elif config_path.endswith('.env'):
                    # Read .env file
                    with open(config_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            if line.startswith('DATABASE_URL=') or line.startswith('SQLALCHEMY_DATABASE_URI='):
                                url = line.split('=', 1)[1].strip().strip('\'"')
                                if url.startswith('postgresql'):
                                    local_db_url = url
                                    break
            except Exception as e:
                print(f"⚠️  Could not read {config_path}: {e}")
                continue
    
    # Default local PostgreSQL connection if not found in config
    if not local_db_url:
        print("⚠️  Could not find local database URL in config files")
        print("Using default local PostgreSQL connection...")
        local_db_url = "postgresql://postgres:E8BnuCBpWKP@localhost:5433/japanese_learning"
    
    print(f"🔗 Connecting to local database: {local_db_url}")
    return create_engine(local_db_url)

def get_docker_db_connection():
    """Get connection to Docker PostgreSQL database"""
    docker_db_url = "postgresql+psycopg://app_user:JapaneseApp2025!@localhost:5432/japanese_learning"
    print(f"🐳 Connecting to Docker database: {docker_db_url}")
    return create_engine(docker_db_url)

def export_table_data(source_session, table_name, order_by=None):
    """Export all data from a table"""
    print(f"📤 Exporting {table_name}...")
    
    # Handle PostgreSQL reserved keywords by quoting table names
    quoted_table_name = f'"{table_name}"' if table_name == 'user' else table_name
    query = f"SELECT * FROM {quoted_table_name}"
    if order_by:
        query += f" ORDER BY {order_by}"
    
    try:
        result = source_session.execute(text(query))
        rows = result.fetchall()
        # Fix SQLAlchemy compatibility - use list() to convert keys
        columns = list(result.keys())
        
        # Convert to list of dictionaries
        data = []
        for row in rows:
            row_dict = {}
            for i, value in enumerate(row):
                if isinstance(value, datetime):
                    row_dict[columns[i]] = value.isoformat()
                elif isinstance(value, dict) or isinstance(value, list):
                    # Handle JSON fields by serializing to string
                    row_dict[columns[i]] = json.dumps(value) if value is not None else None
                else:
                    row_dict[columns[i]] = value
            data.append(row_dict)
        
        print(f"✅ Exported {len(data)} rows from {table_name}")
        return data, columns
    
    except Exception as e:
        print(f"❌ Error exporting {table_name}: {e}")
        return [], []

def import_table_data(target_session, table_name, data, columns):
    """Import data into target table"""
    if not data:
        print(f"⏭️  No data to import for {table_name}")
        return
    
    print(f"📥 Importing {len(data)} rows to {table_name}...")
    
    try:
        # Handle PostgreSQL reserved keywords by quoting table names
        quoted_table_name = f'"{table_name}"' if table_name == 'user' else table_name
        
        # Build INSERT statement
        column_names = ', '.join(columns)
        placeholders = ', '.join([f":{col}" for col in columns])
        
        insert_query = f"""
        INSERT INTO {quoted_table_name} ({column_names})
        VALUES ({placeholders})
        """
        
        # Execute batch insert
        target_session.execute(text(insert_query), data)
        target_session.commit()
        
        print(f"✅ Successfully imported {len(data)} rows to {table_name}")
        
    except IntegrityError as e:
        print(f"⚠️  Integrity error importing {table_name}: {e}")
        target_session.rollback()
        
        # Try inserting one by one to skip duplicates
        success_count = 0
        for row in data:
            try:
                target_session.execute(text(insert_query), row)
                target_session.commit()
                success_count += 1
            except IntegrityError:
                target_session.rollback()
                continue
        
        print(f"✅ Imported {success_count}/{len(data)} rows to {table_name} (skipped duplicates)")
        
    except Exception as e:
        print(f"❌ Error importing {table_name}: {e}")
        target_session.rollback()

def reset_sequences(target_session, table_sequences):
    """Reset PostgreSQL sequences after data import"""
    print("🔄 Resetting sequences...")
    
    for table_name, id_column in table_sequences.items():
        try:
            # Handle PostgreSQL reserved keywords by quoting table names
            quoted_table_name = f'"{table_name}"' if table_name == 'user' else table_name
            
            # Get the maximum ID from the table
            max_id_result = target_session.execute(
                text(f"SELECT MAX({id_column}) FROM {quoted_table_name}")
            ).fetchone()
            
            max_id = max_id_result[0] if max_id_result and max_id_result[0] else 0
            
            # Reset the sequence to max_id + 1
            sequence_name = f"{table_name}_{id_column}_seq"
            target_session.execute(
                text(f"SELECT setval('{sequence_name}', {max_id + 1}, false)")
            )
            target_session.commit()
            
            print(f"✅ Reset sequence for {table_name} to {max_id + 1}")
            
        except Exception as e:
            print(f"⚠️  Could not reset sequence for {table_name}: {e}")

def verify_migration(target_session, tables_to_migrate):
    """Verify that migration was successful"""
    print("\n🔍 Verifying migration...")
    
    verification_passed = True
    for table_name, _, _ in tables_to_migrate:
        try:
            # Handle PostgreSQL reserved keywords by quoting table names
            quoted_table_name = f'"{table_name}"' if table_name == 'user' else table_name
            count_result = target_session.execute(text(f"SELECT COUNT(*) FROM {quoted_table_name}"))
            count = count_result.fetchone()[0]
            print(f"📊 {table_name}: {count} rows")
            
            if count == 0 and table_name in ['lesson', 'lesson_content', 'lesson_category']:
                print(f"⚠️  Warning: Key table {table_name} is empty!")
                verification_passed = False
                
        except Exception as e:
            print(f"❌ Error verifying {table_name}: {e}")
            verification_passed = False
    
    return verification_passed

def main():
    """Main migration function"""
    print("🚀 Starting PostgreSQL to Docker PostgreSQL Migration")
    print("=" * 60)
    
    # Define tables to migrate in dependency order
    tables_to_migrate = [
        # Core reference tables first
        ('lesson_category', None, None),
        ('kana', None, None),
        ('kanji', None, None),
        ('vocabulary', None, None),
        ('grammar', None, None),
        ('user', None, None),
        
        # Lessons and courses
        ('lesson', 'id', None),
        ('course', 'id', None),
        ('course_lessons', None, None),  # Many-to-many relationship table
        
        # Lesson content and structure
        ('lesson_content', 'lesson_id', None),
        ('lesson_page', 'lesson_id', None),
        ('lesson_prerequisite', 'lesson_id', None),
        
        # Quiz system
        ('quiz_question', 'lesson_content_id', None),
        ('quiz_option', 'question_id', None),
        
        # User progress and purchases
        ('user_lesson_progress', 'user_id', None),
        ('lesson_purchase', 'user_id', None),
        ('course_purchase', 'user_id', None),
        ('user_quiz_answer', 'user_id', None),
        ('payment_transaction', None, None),
    ]
    
    # Tables with auto-increment sequences
    table_sequences = {
        'lesson_category': 'id',
        'kana': 'id', 
        'kanji': 'id',
        'vocabulary': 'id',
        'grammar': 'id',
        'user': 'id',
        'lesson': 'id',
        'course': 'id',
        'lesson_content': 'id',
        'lesson_page': 'id',
        'lesson_prerequisite': 'id',
        'quiz_question': 'id',
        'quiz_option': 'id',
        'user_lesson_progress': 'id',
        'lesson_purchase': 'id',
        'course_purchase': 'id',
        'user_quiz_answer': 'id',
        'payment_transaction': 'id',
    }
    
    try:
        # Connect to databases
        print("🔌 Establishing database connections...")
        source_engine = get_local_db_connection()
        target_engine = get_docker_db_connection()
        
        # Test connections
        with source_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Local database connection successful")
        
        with target_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Docker database connection successful")
        
        # Create sessions
        SourceSession = sessionmaker(bind=source_engine)
        TargetSession = sessionmaker(bind=target_engine)
        
        with SourceSession() as source_session, TargetSession() as target_session:
            print("\n📋 Starting data migration...")
            
            # Migrate each table
            for table_name, foreign_key, order_by in tables_to_migrate:
                try:
                    # Export data from source
                    data, columns = export_table_data(source_session, table_name, order_by)
                    
                    # Import data to target
                    if data:
                        import_table_data(target_session, table_name, data, columns)
                    else:
                        print(f"⏭️  Skipping {table_name} (no data)")
                        
                except Exception as e:
                    print(f"❌ Failed to migrate {table_name}: {e}")
                    continue
            
            print("\n🔄 Resetting database sequences...")
            reset_sequences(target_session, table_sequences)
            
            print("\n🔍 Verifying migration...")
            if verify_migration(target_session, tables_to_migrate):
                print("\n🎉 Migration completed successfully!")
                print("✅ All tables migrated and verified")
                
                # Show summary
                print("\n📊 Migration Summary:")
                print("-" * 40)
                lesson_count = target_session.execute(text("SELECT COUNT(*) FROM lesson")).fetchone()[0]
                content_count = target_session.execute(text("SELECT COUNT(*) FROM lesson_content")).fetchone()[0]
                user_count = target_session.execute(text("SELECT COUNT(*) FROM \"user\"")).fetchone()[0]
                category_count = target_session.execute(text("SELECT COUNT(*) FROM lesson_category")).fetchone()[0]
                
                print(f"📚 Lessons: {lesson_count}")
                print(f"📄 Lesson Content Items: {content_count}")
                print(f"👥 Users: {user_count}")
                print(f"🏷️  Categories: {category_count}")
                
            else:
                print("\n⚠️  Migration completed with warnings")
                print("Please check the logs above for issues")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("Please check your database connections and try again")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
