#!/usr/bin/env python3
"""
Database Migration Script: SQLite to Google Cloud SQL PostgreSQL
================================================================

This script migrates all tables from a local SQLite database to a Google Cloud SQL
PostgreSQL instance via the Cloud SQL Auth Proxy.

Author: Expert Python Developer & Google Cloud Specialist
Date: 2025-01-15
"""

import os
import sys
import logging
import pandas as pd
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DatabaseMigrator:
    """Handles the migration of tables from SQLite to PostgreSQL."""
    
    def __init__(self):
        """Initialize the migrator with database connection parameters."""
        self.sqlite_db_path = 'instance/site.db'
        self.postgres_config = {
            'host': 'localhost',
            'port': '5432',
            'database': 'japanese_learning',
            'username': 'app_user',
            'password': os.getenv('DB_PASSWORD')
        }
        
        # Validate environment variables
        if not self.postgres_config['password']:
            logger.error("DB_PASSWORD environment variable is not set!")
            sys.exit(1)
        
        self.sqlite_engine = None
        self.postgres_engine = None
        
    def create_connections(self):
        """Create database connections for both SQLite and PostgreSQL."""
        try:
            # SQLite connection with encoding handling
            sqlite_url = f"sqlite:///{self.sqlite_db_path}"
            # Add connect_args to handle encoding issues
            self.sqlite_engine = create_engine(
                sqlite_url,
                connect_args={
                    'check_same_thread': False,
                },
                # Use text_factory to handle encoding issues
                module=None
            )
            logger.info(f"Connected to SQLite database: {self.sqlite_db_path}")
            
            # PostgreSQL connection via Cloud SQL Auth Proxy
            # URL encode the password to handle special characters
            from urllib.parse import quote_plus
            encoded_password = quote_plus(self.postgres_config['password'])
            
            postgres_url = (
                f"postgresql://{self.postgres_config['username']}:"
                f"{encoded_password}@"
                f"{self.postgres_config['host']}:"
                f"{self.postgres_config['port']}/"
                f"{self.postgres_config['database']}"
                f"?client_encoding=utf8"
            )
            self.postgres_engine = create_engine(
                postgres_url,
                connect_args={
                    "client_encoding": "utf8",
                    "options": "-c client_encoding=utf8"
                }
            )
            logger.info("Connected to local PostgreSQL database")
            
            # Test connections
            with self.sqlite_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("SQLite connection test successful")
            
            try:
                logger.info("Attempting PostgreSQL connection test...")
                with self.postgres_engine.connect() as conn:
                    logger.info("PostgreSQL connection established, executing test query...")
                    result = conn.execute(text("SELECT 1"))
                    logger.info(f"Test query result: {result.fetchone()}")
                logger.info("PostgreSQL connection test successful")
            except Exception as pg_error:
                logger.error(f"PostgreSQL connection test failed: {str(pg_error)}")
                logger.error(f"Error type: {type(pg_error)}")
                import traceback
                logger.error(f"Full traceback: {traceback.format_exc()}")
                raise pg_error
            
        except Exception as e:
            logger.error(f"Failed to create database connections: {str(e)}")
            sys.exit(1)
    
    def get_user_tables(self):
        """
        Discover all user-created tables in the SQLite database.
        Excludes system tables like sqlite_sequence.
        """
        try:
            with self.sqlite_engine.connect() as conn:
                query = text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' 
                    AND name NOT LIKE 'sqlite_%'
                    AND name NOT LIKE 'alembic_%'
                    ORDER BY name
                """)
                result = conn.execute(query)
                tables = [row[0] for row in result.fetchall()]
                
            logger.info(f"Discovered {len(tables)} user tables: {', '.join(tables)}")
            return tables
            
        except Exception as e:
            logger.error(f"Failed to discover tables: {str(e)}")
            return []
    
    def get_table_info(self, table_name):
        """Get information about a table's structure."""
        try:
            inspector = inspect(self.sqlite_engine)
            columns = inspector.get_columns(table_name)
            return columns
        except Exception as e:
            logger.warning(f"Could not get table info for {table_name}: {str(e)}")
            return []
    
    def _safe_read_table(self, table_name):
        """
        Safely read a table from SQLite, handling type mismatches and encoding issues.
        Falls back to string types for INTEGER columns that contain non-numeric data.
        """
        try:
            return pd.read_sql_table(table_name, self.sqlite_engine)
        except (ValueError, UnicodeDecodeError) as e:
            logger.warning(f"Error reading table '{table_name}': {str(e)}")
            
            if "invalid literal for int()" in str(e):
                # Handle type mismatch
                with self.sqlite_engine.connect() as conn:
                    result = conn.execute(text(f"PRAGMA table_info({table_name})"))
                    columns = result.fetchall()
                
                # Find INTEGER columns that might contain string data
                int_cols = [col[1] for col in columns if 'INT' in col[2].upper()]
                dtype_dict = {c: 'string' for c in int_cols}
                
                logger.warning(f"Type mismatch detected in table '{table_name}'. Falling back to string dtypes for INTEGER columns: {int_cols}")
                
                # Re-read using SQL query with explicit string dtypes
                return pd.read_sql_query(f"SELECT * FROM {table_name}", 
                                       self.sqlite_engine, 
                                       dtype=dtype_dict)
            else:
                # Handle encoding issues by reading with raw SQL and manual encoding handling
                return self._read_table_with_encoding_handling(table_name)
    
    def _read_table_with_encoding_handling(self, table_name):
        """
        Read table data with manual encoding handling for problematic characters.
        """
        try:
            logger.info(f"Attempting to read table '{table_name}' with encoding handling...")
            
            # Read data using raw SQL with manual encoding handling
            with self.sqlite_engine.connect() as conn:
                # First, get column names
                result = conn.execute(text(f"PRAGMA table_info({table_name})"))
                columns = [col[1] for col in result.fetchall()]
                
                # Read all data as text to handle encoding issues
                result = conn.execute(text(f"SELECT * FROM {table_name}"))
                rows = result.fetchall()
                
                # Convert to DataFrame with encoding handling
                data = []
                for row in rows:
                    processed_row = []
                    for value in row:
                        if isinstance(value, bytes):
                            # Handle bytes data with multiple encoding attempts
                            try:
                                processed_value = value.decode('utf-8')
                            except UnicodeDecodeError:
                                try:
                                    processed_value = value.decode('latin-1')
                                    logger.debug(f"Decoded bytes using latin-1: {processed_value[:50]}...")
                                except UnicodeDecodeError:
                                    try:
                                        processed_value = value.decode('windows-1252')
                                        logger.debug(f"Decoded bytes using windows-1252: {processed_value[:50]}...")
                                    except UnicodeDecodeError:
                                        # Last resort: replace problematic characters
                                        processed_value = value.decode('utf-8', errors='replace')
                                        logger.warning(f"Used error replacement for problematic bytes")
                        elif isinstance(value, str):
                            # Handle string data that might have encoding issues
                            try:
                                # Try to encode/decode to ensure proper UTF-8
                                processed_value = value.encode('utf-8', errors='replace').decode('utf-8')
                            except (UnicodeEncodeError, UnicodeDecodeError):
                                processed_value = str(value)
                        else:
                            processed_value = value
                        
                        processed_row.append(processed_value)
                    data.append(processed_row)
                
                # Create DataFrame
                df = pd.DataFrame(data, columns=columns)
                logger.info(f"Successfully read table '{table_name}' with encoding handling: {len(df)} rows")
                return df
                
        except Exception as e:
            logger.error(f"Failed to read table '{table_name}' even with encoding handling: {str(e)}")
            # Return empty DataFrame with column structure
            try:
                with self.sqlite_engine.connect() as conn:
                    result = conn.execute(text(f"PRAGMA table_info({table_name})"))
                    columns = [col[1] for col in result.fetchall()]
                return pd.DataFrame(columns=columns)
            except:
                return pd.DataFrame()
    
    def create_table_in_postgres(self, table_name):
        """
        Create a table in PostgreSQL based on the SQLite schema.
        
        Args:
            table_name (str): Name of the table to create
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Creating table '{table_name}' in PostgreSQL...")
            
            # Get SQLite table schema
            with self.sqlite_engine.connect() as conn:
                # Get CREATE TABLE statement from SQLite
                result = conn.execute(text(f"""
                    SELECT sql FROM sqlite_master 
                    WHERE type='table' AND name='{table_name}'
                """))
                create_sql = result.fetchone()
                
                if not create_sql:
                    logger.error(f"Could not find CREATE statement for table '{table_name}'")
                    return False
                
                sqlite_create_sql = create_sql[0]
                logger.debug(f"SQLite CREATE SQL: {sqlite_create_sql}")
                
                # Get column information for type mapping
                result = conn.execute(text(f"PRAGMA table_info({table_name})"))
                columns = result.fetchall()
            
            # Convert SQLite schema to PostgreSQL
            postgres_create_sql = self.convert_sqlite_to_postgres_schema(sqlite_create_sql, columns, table_name)
            logger.debug(f"PostgreSQL CREATE SQL: {postgres_create_sql}")
            
            # Create table in PostgreSQL
            with self.postgres_engine.connect() as conn:
                # Handle reserved words for DROP statement
                reserved_words = {'user', 'order', 'group', 'table', 'column'}
                drop_table_name = f'"{table_name}"' if table_name.lower() in reserved_words else table_name
                
                # Drop table if it exists (for clean migration)
                conn.execute(text(f"DROP TABLE IF EXISTS {drop_table_name} CASCADE"))
                conn.execute(text(postgres_create_sql))
                conn.commit()
            
            logger.info(f"[SUCCESS] Successfully created table '{table_name}' in PostgreSQL")
            return True
            
        except Exception as e:
            logger.error(f"[FAILED] Failed to create table '{table_name}': {str(e)}")
            return False
    
    def convert_sqlite_to_postgres_schema(self, sqlite_sql, columns, table_name):
        """
        Convert SQLite CREATE TABLE statement to PostgreSQL compatible format.
        
        Args:
            sqlite_sql (str): Original SQLite CREATE TABLE statement
            columns (list): Column information from PRAGMA table_info
            table_name (str): Name of the table
            
        Returns:
            str: PostgreSQL compatible CREATE TABLE statement
        """
        # SQLite to PostgreSQL type mapping
        type_mapping = {
            'INTEGER': 'INTEGER',
            'TEXT': 'TEXT',
            'REAL': 'REAL',
            'BLOB': 'BYTEA',
            'NUMERIC': 'NUMERIC',
            'VARCHAR': 'VARCHAR',
            'CHAR': 'CHAR',
            'BOOLEAN': 'BOOLEAN',
            'DATETIME': 'TIMESTAMP',
            'DATE': 'DATE',
            'TIME': 'TIME',
            'JSON': 'JSONB'
        }
        
        # Handle reserved words in PostgreSQL
        reserved_words = {'user', 'order', 'group', 'table', 'column'}
        actual_table_name = f'"{table_name}"' if table_name.lower() in reserved_words else table_name
        
        # Build PostgreSQL CREATE TABLE statement
        postgres_columns = []
        primary_keys = []
        
        for col in columns:
            col_id, col_name, col_type, not_null, default_value, is_pk = col
            
            # Handle reserved column names
            actual_col_name = f'"{col_name}"' if col_name.lower() in reserved_words else col_name
            
            # Map SQLite type to PostgreSQL type
            pg_type = col_type.upper()
            for sqlite_type, postgres_type in type_mapping.items():
                if sqlite_type in pg_type:
                    pg_type = postgres_type
                    break
            
            # Handle special cases for data types
            if col_name == 'ai_generation_details':
                pg_type = 'JSONB'
            elif col_name == 'difficulty_level' and pg_type == 'INTEGER':
                # Keep as INTEGER but handle string values in data preparation
                pass
            
            # Handle SERIAL type for primary keys
            if 'AUTOINCREMENT' in sqlite_sql.upper() and is_pk:
                pg_type = 'SERIAL'
            elif pg_type == 'INTEGER' and is_pk and not any(other_col[5] for other_col in columns if other_col != col):
                # Only use SERIAL if this is the only primary key
                pg_type = 'SERIAL'
            
            # Build column definition
            col_def = f"{actual_col_name} {pg_type}"
            
            # Add constraints
            if not_null and not is_pk:
                col_def += " NOT NULL"
            
            # Handle default values
            if default_value is not None:
                if pg_type in ['TEXT', 'VARCHAR', 'CHAR']:
                    # Fix single quote escaping
                    escaped_default = str(default_value).replace("'", "''")
                    col_def += f" DEFAULT '{escaped_default}'"
                elif pg_type == 'BOOLEAN':
                    # Convert 0/1 to boolean
                    bool_val = 'TRUE' if str(default_value) in ['1', 'true', 'True'] else 'FALSE'
                    col_def += f" DEFAULT {bool_val}"
                else:
                    col_def += f" DEFAULT {default_value}"
            
            # Collect primary keys separately
            if is_pk:
                primary_keys.append(actual_col_name)
            
            postgres_columns.append(col_def)
        
        # Add primary key constraint if there are multiple primary keys
        if len(primary_keys) > 1:
            pk_constraint = f"PRIMARY KEY ({', '.join(primary_keys)})"
            postgres_columns.append(pk_constraint)
        elif len(primary_keys) == 1 and not any('SERIAL' in col for col in postgres_columns):
            # Add PRIMARY KEY to single primary key column if not SERIAL
            for i, col in enumerate(postgres_columns):
                if primary_keys[0] in col and 'PRIMARY KEY' not in col:
                    postgres_columns[i] += " PRIMARY KEY"
        
        # Create the final PostgreSQL CREATE TABLE statement
        postgres_sql = f"CREATE TABLE {actual_table_name} (\n    " + ",\n    ".join(postgres_columns) + "\n)"
        
        return postgres_sql

    def migrate_table(self, table_name):
        """
        Migrate a single table from SQLite to PostgreSQL.
        This includes creating the table structure and copying the data.
        
        Args:
            table_name (str): Name of the table to migrate
            
        Returns:
            tuple: (success: bool, rows_transferred: int, error_message: str)
        """
        logger.info(f"Starting migration for table: '{table_name}'...")
        
        try:
            # Step 1: Create table in PostgreSQL
            if not self.create_table_in_postgres(table_name):
                return False, 0, "Failed to create table in PostgreSQL"
            
            # Step 2: Read table structure info
            table_info = self.get_table_info(table_name)
            if table_info:
                column_names = [col['name'] for col in table_info]
                logger.info(f"Table '{table_name}' has columns: {', '.join(column_names)}")
            
            # Step 3: Read data from SQLite
            logger.info(f"Reading data from SQLite table '{table_name}'...")
            df = self._safe_read_table(table_name)
            row_count = len(df)
            
            if row_count == 0:
                logger.info(f"Table '{table_name}' is empty but structure created successfully")
                return True, 0, None
            
            logger.info(f"Read {row_count} rows from table '{table_name}'")
            
            # Step 4: Handle data type conversions for PostgreSQL compatibility
            df = self.prepare_dataframe_for_postgres(df, table_name)
            
            # Step 5: Write data to PostgreSQL
            logger.info(f"Writing data to PostgreSQL table '{table_name}'...")
            df.to_sql(
                table_name,
                self.postgres_engine,
                if_exists='append',
                index=False,
                method='multi',
                chunksize=1000
            )
            
            # Step 6: Verify the migration
            with self.postgres_engine.connect() as conn:
                # Handle reserved words for verification query
                reserved_words = {'user', 'order', 'group', 'table', 'column'}
                verify_table_name = f'"{table_name}"' if table_name.lower() in reserved_words else table_name
                result = conn.execute(text(f"SELECT COUNT(*) FROM {verify_table_name}"))
                postgres_count = result.fetchone()[0]
            
            if postgres_count == row_count:
                logger.info(f"[SUCCESS] Successfully migrated table '{table_name}': {row_count} rows")
                return True, row_count, None
            else:
                error_msg = f"Row count mismatch: SQLite={row_count}, PostgreSQL={postgres_count}"
                logger.error(f"[FAILED] Migration verification failed for table '{table_name}': {error_msg}")
                return False, row_count, error_msg
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"[FAILED] Failed to migrate table '{table_name}': {error_msg}")
            return False, 0, error_msg
    
    def prepare_dataframe_for_postgres(self, df, table_name):
        """
        Prepare DataFrame for PostgreSQL compatibility.
        Handle common data type issues between SQLite and PostgreSQL.
        """
        try:
            import json
            
            # First, ensure all text data is properly UTF-8 encoded
            for col in df.columns:
                if df[col].dtype == 'object':
                    def clean_text(value):
                        if pd.isna(value) or value is None:
                            return None
                        if isinstance(value, str):
                            # Ensure proper UTF-8 encoding
                            try:
                                # Remove any problematic characters
                                cleaned = value.encode('utf-8', errors='replace').decode('utf-8')
                                return cleaned
                            except (UnicodeEncodeError, UnicodeDecodeError):
                                return str(value)
                        return value
                    
                    df[col] = df[col].apply(clean_text)
            
            # Handle jlpt_level conversion FIRST (before other processing)
            if 'jlpt_level' in df.columns:
                logger.info(f"Converting jlpt_level column for table '{table_name}'")
                def convert_jlpt_level(value):
                    if pd.isna(value) or value is None:
                        return None
                    if isinstance(value, str):
                        # Handle JLPT level strings like "N1", "N2", "N3", "N4", "N5", "NN4", etc.
                        value_clean = value.upper().strip()
                        logger.debug(f"Converting JLPT level: '{value}' -> '{value_clean}'")
                        if value_clean.startswith('N'):
                            # Extract the number part - handle "NN4" by removing all N's
                            number_part = value_clean.lstrip('N')
                            if number_part.isdigit():
                                result = int(number_part)
                                logger.debug(f"JLPT conversion: '{value}' -> {result}")
                                return result
                        # If it's already a number string
                        if value_clean.isdigit():
                            return int(value_clean)
                        # Default to N5 (5) if we can't parse it
                        logger.warning(f"Could not parse JLPT level '{value}', defaulting to 5")
                        return 5
                    try:
                        return int(value)
                    except (ValueError, TypeError):
                        return 5
                
                df['jlpt_level'] = df['jlpt_level'].apply(convert_jlpt_level)
                logger.info(f"JLPT level conversion completed for table '{table_name}'")
            
            # Convert datetime columns properly
            for col in df.columns:
                if df[col].dtype == 'object':
                    # Try to convert datetime strings
                    if any(df[col].astype(str).str.contains(r'\d{4}-\d{2}-\d{2}', na=False)):
                        try:
                            df[col] = pd.to_datetime(df[col], errors='coerce')
                        except:
                            pass
                
                # Handle boolean columns (SQLite stores as 0/1)
                if col.lower() in ['is_active', 'is_admin', 'is_published', 'enabled', 'active', 'allow_guest_access', 'is_optional', 'is_interactive', 'is_correct', 'is_completed', 'generated_by_ai', 'created_by_ai']:
                    if df[col].dtype in ['int64', 'float64']:
                        df[col] = df[col].astype(bool)
                
                # Handle JSON columns
                if col == 'ai_generation_details':
                    def convert_to_json(value):
                        if pd.isna(value) or value is None:
                            return None
                        if isinstance(value, dict):
                            return json.dumps(value)
                        if isinstance(value, str):
                            try:
                                # Try to parse as JSON to validate
                                json.loads(value)
                                return value
                            except:
                                return json.dumps({"raw_value": value})
                        return json.dumps({"raw_value": str(value)})
                    
                    df[col] = df[col].apply(convert_to_json)
                
                # Handle difficulty_level conversion (string to integer)
                if col == 'difficulty_level':
                    def convert_difficulty(value):
                        if pd.isna(value) or value is None:
                            return None
                        if isinstance(value, str):
                            difficulty_map = {
                                'easy': 1,
                                'medium': 2,
                                'hard': 3,
                                'beginner': 1,
                                'intermediate': 2,
                                'advanced': 3
                            }
                            return difficulty_map.get(value.lower(), 1)  # Default to 1 if unknown
                        return int(value) if str(value).isdigit() else 1
                    
                    df[col] = df[col].apply(convert_difficulty)
            
            logger.debug(f"Prepared DataFrame for table '{table_name}' with shape {df.shape}")
            return df
            
        except Exception as e:
            logger.warning(f"Error preparing DataFrame for table '{table_name}': {str(e)}")
            return df
    
    def run_migration(self):
        """Run the complete migration process."""
        logger.info("=" * 60)
        logger.info("STARTING DATABASE MIGRATION")
        logger.info("Source: SQLite (instance/site.db)")
        logger.info("Target: Local PostgreSQL (japanese_learning)")
        logger.info("=" * 60)
        
        start_time = datetime.now()
        
        # Create database connections
        self.create_connections()
        
        # Discover tables
        tables = self.get_user_tables()
        if not tables:
            logger.error("No tables found to migrate!")
            return
        
        # Migration statistics
        total_tables = len(tables)
        successful_migrations = 0
        failed_migrations = 0
        total_rows_migrated = 0
        migration_results = []
        
        # Migrate each table
        for i, table_name in enumerate(tables, 1):
            logger.info(f"\n[{i}/{total_tables}] Processing table: {table_name}")
            
            success, rows_transferred, error_message = self.migrate_table(table_name)
            
            migration_results.append({
                'table': table_name,
                'success': success,
                'rows': rows_transferred,
                'error': error_message
            })
            
            if success:
                successful_migrations += 1
                total_rows_migrated += rows_transferred
            else:
                failed_migrations += 1
            
            # Small delay between tables to avoid overwhelming the database
            time.sleep(0.5)
        
        # Final report
        end_time = datetime.now()
        duration = end_time - start_time
        
        logger.info("\n" + "=" * 60)
        logger.info("MIGRATION COMPLETED")
        logger.info("=" * 60)
        logger.info(f"Duration: {duration}")
        logger.info(f"Total tables processed: {total_tables}")
        logger.info(f"Successful migrations: {successful_migrations}")
        logger.info(f"Failed migrations: {failed_migrations}")
        logger.info(f"Total rows migrated: {total_rows_migrated:,}")
        
        # Detailed results
        logger.info("\nDETAILED RESULTS:")
        logger.info("-" * 40)
        for result in migration_results:
            status = "[SUCCESS]" if result['success'] else "[FAILED]"
            logger.info(f"{result['table']:<20} | {status:<10} | {result['rows']:>8} rows")
            if not result['success'] and result['error']:
                logger.info(f"{'':>20} | Error: {result['error']}")
        
        # Close connections
        if self.sqlite_engine:
            self.sqlite_engine.dispose()
        if self.postgres_engine:
            self.postgres_engine.dispose()
        
        logger.info(f"\nMigration log saved to: migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        
        if failed_migrations > 0:
            logger.warning(f"\n[WARNING] {failed_migrations} table(s) failed to migrate. Check the log for details.")
            sys.exit(1)
        else:
            logger.info("\n[SUCCESS] All tables migrated successfully!")

def main():
    """Main entry point for the migration script."""
    try:
        migrator = DatabaseMigrator()
        migrator.run_migration()
    except KeyboardInterrupt:
        logger.info("\nMigration interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
