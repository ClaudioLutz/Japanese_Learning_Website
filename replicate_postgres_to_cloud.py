#!/usr/bin/env python3
"""
PostgreSQL to Google Cloud PostgreSQL Replication Script
Replicates your existing local PostgreSQL database structure and data to Google Cloud
"""

import os
import sys
import psycopg
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('postgres_replication.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class PostgreSQLReplicator:
    def __init__(self, source_config, target_config):
        self.source_config = source_config
        self.target_config = target_config
        self.source_conn = None
        self.target_conn = None
        self.source_cursor = None
        self.target_cursor = None
    
    def connect_databases(self):
        """Connect to both source and target PostgreSQL databases"""
        try:
            # Connect to source (local) PostgreSQL
            source_config = self.source_config.copy()
            if 'database' in source_config:
                source_config['dbname'] = source_config.pop('database')
            self.source_conn = psycopg.connect(**source_config)
            self.source_cursor = self.source_conn.cursor()
            logger.info(f"✓ Connected to source PostgreSQL: {self.source_config['host']}")
            
            # Connect to target (Google Cloud) PostgreSQL
            target_config = self.target_config.copy()
            if 'database' in target_config:
                target_config['dbname'] = target_config.pop('database')
            self.target_conn = psycopg.connect(**target_config)
            self.target_cursor = self.target_conn.cursor()
            logger.info(f"✓ Connected to target PostgreSQL: {self.target_config['host']}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to connect to databases: {e}")
            return False
    
    def get_database_schema(self):
        """Extract complete database schema from source"""
        if not self.source_cursor:
            return None, None
            
        try:
            # Get all tables
            query = """
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public' 
                AND tablename NOT LIKE 'alembic%'
                ORDER BY tablename
            """
            self.source_cursor.execute(query)
            tables = [row[0] for row in self.source_cursor.fetchall()]
            logger.info(f"✓ Found {len(tables)} tables in source database")
            
            schema_info = {}
            
            for table in tables:
                # Get table structure
                query = """
                    SELECT column_name, data_type, is_nullable, column_default, character_maximum_length
                    FROM information_schema.columns 
                    WHERE table_name = %s AND table_schema = 'public'
                    ORDER BY ordinal_position
                """
                self.source_cursor.execute(query, (table,))
                columns = self.source_cursor.fetchall()
                
                # Get constraints
                query = """
                    SELECT tc.constraint_name, tc.constraint_type, kcu.column_name,
                           ccu.table_name AS foreign_table_name, ccu.column_name AS foreign_column_name
                    FROM information_schema.table_constraints AS tc 
                    JOIN information_schema.key_column_usage AS kcu
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    LEFT JOIN information_schema.constraint_column_usage AS ccu
                        ON ccu.constraint_name = tc.constraint_name
                        AND ccu.table_schema = tc.table_schema
                    WHERE tc.table_name = %s AND tc.table_schema = 'public'
                """
                self.source_cursor.execute(query, (table,))
                constraints = self.source_cursor.fetchall()
                
                # Get indexes
                query = """
                    SELECT indexname, indexdef 
                    FROM pg_indexes 
                    WHERE tablename = %s AND schemaname = 'public'
                    AND indexname NOT LIKE '%_pkey'
                """
                self.source_cursor.execute(query, (table,))
                indexes = self.source_cursor.fetchall()
                
                schema_info[table] = {
                    'columns': columns,
                    'constraints': constraints,
                    'indexes': indexes
                }
            
            return schema_info, tables
            
        except Exception as e:
            logger.error(f"Failed to extract schema: {e}")
            return None, None
    
    def create_table_ddl(self, table_name, table_info):
        """Generate CREATE TABLE DDL from table info"""
        columns = table_info['columns']
        constraints = table_info['constraints']
        
        # Build column definitions
        column_defs = []
        for col in columns:
            col_name, data_type, is_nullable, default, max_length = col
            
            # Handle data type
            if data_type == 'character varying' and max_length:
                col_type = f"VARCHAR({max_length})"
            elif data_type == 'integer':
                col_type = "INTEGER"
            elif data_type == 'bigint':
                col_type = "BIGINT"
            elif data_type == 'boolean':
                col_type = "BOOLEAN"
            elif data_type == 'text':
                col_type = "TEXT"
            elif data_type == 'timestamp without time zone':
                col_type = "TIMESTAMP"
            elif data_type == 'double precision':
                col_type = "DOUBLE PRECISION"
            elif data_type == 'real':
                col_type = "REAL"
            elif data_type == 'jsonb':
                col_type = "JSONB"
            else:
                col_type = data_type.upper()
            
            # Build column definition
            col_def = f"{col_name} {col_type}"
            
            # Handle nullable
            if is_nullable == 'NO':
                col_def += " NOT NULL"
            
            # Handle default
            if default:
                if 'nextval' in default:
                    col_def = col_def.replace('INTEGER', 'SERIAL').replace('BIGINT', 'BIGSERIAL')
                elif default not in ['NULL', 'null']:
                    col_def += f" DEFAULT {default}"
            
            column_defs.append(col_def)
        
        # Add primary key and unique constraints
        constraint_defs = []
        for constraint in constraints:
            constraint_name, constraint_type, column_name, foreign_table, foreign_column = constraint
            
            if constraint_type == 'PRIMARY KEY':
                constraint_defs.append(f"PRIMARY KEY ({column_name})")
            elif constraint_type == 'UNIQUE':
                constraint_defs.append(f"UNIQUE ({column_name})")
        
        # Combine all definitions
        all_defs = column_defs + constraint_defs
        
        ddl = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            {',\n            '.join(all_defs)}
        );
        """
        
        return ddl
    
    def add_foreign_keys(self, table_name, table_info):
        """Add foreign key constraints after all tables are created"""
        constraints = table_info['constraints']
        fk_statements = []
        
        for constraint in constraints:
            constraint_name, constraint_type, column_name, foreign_table, foreign_column = constraint
            
            if constraint_type == 'FOREIGN KEY' and foreign_table and foreign_column:
                fk_sql = f"""
                ALTER TABLE {table_name} 
                ADD CONSTRAINT {constraint_name} 
                FOREIGN KEY ({column_name}) 
                REFERENCES {foreign_table}({foreign_column});
                """
                fk_statements.append(fk_sql)
        
        return fk_statements
    
    def create_indexes(self, table_name, table_info):
        """Create indexes for the table"""
        indexes = table_info['indexes']
        index_statements = []
        
        for index_name, index_def in indexes:
            # Modify index definition to use IF NOT EXISTS
            modified_def = index_def.replace('CREATE INDEX', 'CREATE INDEX IF NOT EXISTS')
            index_statements.append(modified_def)
        
        return index_statements
    
    def copy_table_data(self, table_name):
        """Copy data from source table to target table"""
        if not self.source_cursor or not self.target_cursor or not self.target_conn:
            return False
            
        try:
            # Get all data from source
            query = f"SELECT * FROM {table_name}"
            self.source_cursor.execute(query)
            rows = self.source_cursor.fetchall()
            
            if not rows:
                logger.info(f"✓ Table {table_name} is empty, skipping data copy")
                return True
            
            # Get column names
            query = """
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = %s AND table_schema = 'public'
                ORDER BY ordinal_position
            """
            self.source_cursor.execute(query, (table_name,))
            columns = [row[0] for row in self.source_cursor.fetchall()]
            
            # Prepare insert statement
            placeholders = ', '.join(['%s'] * len(columns))
            column_names = ', '.join(columns)
            
            insert_sql = f"""
            INSERT INTO {table_name} ({column_names})
            VALUES ({placeholders})
            ON CONFLICT DO NOTHING;
            """
            
            # Insert data in batches
            batch_size = 1000
            inserted_count = 0
            
            for i in range(0, len(rows), batch_size):
                batch = rows[i:i + batch_size]
                self.target_cursor.executemany(insert_sql, batch)
                inserted_count += len(batch)
            
            self.target_conn.commit()
            logger.info(f"✓ Copied {inserted_count} records to {table_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to copy data for table {table_name}: {e}")
            return False
    
    def replicate_database(self, copy_data=True):
        """Main method to replicate the entire database"""
        logger.info("Starting PostgreSQL database replication...")
        
        if not self.connect_databases():
            return False
        
        if not self.target_cursor or not self.target_conn:
            logger.error("No target database connection available")
            return False
        
        try:
            # Extract schema
            schema_info, tables = self.get_database_schema()
            if not schema_info or not tables:
                return False
            
            # Create tables (without foreign keys first)
            logger.info("Creating tables...")
            for table_name in tables:
                ddl = self.create_table_ddl(table_name, schema_info[table_name])
                try:
                    self.target_cursor.execute(ddl)
                    logger.info(f"✓ Created table: {table_name}")
                except Exception as e:
                    logger.error(f"Failed to create table {table_name}: {e}")
            
            self.target_conn.commit()
            
            # Add foreign key constraints
            logger.info("Adding foreign key constraints...")
            all_fk_statements = []
            for table_name in tables:
                fk_statements = self.add_foreign_keys(table_name, schema_info[table_name])
                if fk_statements:
                    all_fk_statements.extend(fk_statements)
            
            for fk_sql in all_fk_statements:
                try:
                    self.target_cursor.execute(fk_sql)
                except Exception as e:
                    logger.warning(f"Foreign key constraint failed (may already exist): {e}")
            
            self.target_conn.commit()
            
            # Create indexes
            logger.info("Creating indexes...")
            for table_name in tables:
                index_statements = self.create_indexes(table_name, schema_info[table_name])
                if index_statements:
                    for index_sql in index_statements:
                        try:
                            self.target_cursor.execute(index_sql)
                        except Exception as e:
                            logger.warning(f"Index creation failed (may already exist): {e}")
            
            self.target_conn.commit()
            
            # Copy data if requested
            if copy_data and tables:
                logger.info("Copying data...")
                for table_name in tables:
                    self.copy_table_data(table_name)
            
            logger.info("🎉 Database replication completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Database replication failed: {e}")
            return False
        finally:
            if self.source_conn:
                self.source_conn.close()
            if self.target_conn:
                self.target_conn.close()
            logger.info("Database connections closed")

def main():
    """Main execution function"""
    print("🔄 PostgreSQL to Google Cloud Replication")
    print("=" * 50)
    
    # Source PostgreSQL configuration (your local database)
    print("Source Database Configuration:")
    source_host = input("Local PostgreSQL host (default: localhost): ").strip() or "localhost"
    source_port = input("Local PostgreSQL port (default: 5432): ").strip() or "5432"
    source_db = input("Local database name: ").strip()
    source_user = input("Local database user: ").strip()
    source_password = input("Local database password: ").strip()
    
    source_config = {
        'host': source_host,
        'port': int(source_port),
        'database': source_db,
        'user': source_user,
        'password': source_password
    }
    
    # Target PostgreSQL configuration (Google Cloud)
    target_config = {
        'host': '34.65.227.94',
        'port': 5432,
        'database': 'japanese_learning',
        'user': 'app_user',
        'password': 'Dg34.67MDt'
    }
    
    print(f"\nSource: {source_config['host']}:{source_config['port']}/{source_config['database']}")
    print(f"Target: {target_config['host']}:{target_config['port']}/{target_config['database']}")
    
    copy_data = input("\nCopy data as well? (Y/n): ").lower().strip() != 'n'
    
    confirm = input("\n🚀 Start replication? (y/N): ").lower().strip()
    if confirm != 'y':
        print("Replication cancelled.")
        return
    
    # Run replication
    replicator = PostgreSQLReplicator(source_config, target_config)
    success = replicator.replicate_database(copy_data=copy_data)
    
    if success:
        print("\n✅ Database replication completed successfully!")
        print("\nNext steps:")
        print("1. Update your Flask app's DATABASE_URL to point to Google Cloud")
        print("2. Test your application with the new database")
        print("3. Deploy to your Google Cloud VM")
    else:
        print("\n❌ Database replication failed. Check the logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
