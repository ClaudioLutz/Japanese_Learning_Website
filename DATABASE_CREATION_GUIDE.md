# Google Cloud PostgreSQL Database Creation Guide

This guide will help you create your Japanese Learning Website database on Google Cloud PostgreSQL, bypassing all Alembic migration issues.

## 🎯 What This Solves

- **Alembic Migration Conflicts**: Bypasses all migration version conflicts
- **Clean Database Setup**: Creates exact replica of your local database structure
- **Production Ready**: Includes proper indexes, constraints, and initial data
- **No Manual SQL**: Automated creation of all 17 tables with relationships

## 📋 Prerequisites

1. **Google Cloud SQL Instance**: Your PostgreSQL instance should be running
2. **Network Access**: Your IP must be authorized to connect
3. **Python Environment**: Python 3.7+ with pip

## 🚀 Quick Start

### Step 1: Install Dependencies

```bash
# Install required packages
pip install -r requirements_db_creator.txt
```

### Step 2: Test Connection

```bash
# Test your database connection first
python test_db_connection.py
```

**Expected Output:**
```
🔍 Testing connection to Google Cloud PostgreSQL...
Host: 34.65.227.94:5432
Database: japanese_learning
User: app_user
--------------------------------------------------
Connecting...
✓ Connection successful!
✓ PostgreSQL Version: PostgreSQL 17.x...
✓ Current tables in database: 0
✓ Write permissions confirmed (test records: 1)

🎉 Database connection test completed successfully!
```

### Step 3: Create Database

```bash
# Run the database creation script
python create_cloud_database.py
```

## 📊 What Gets Created

### Database Tables (17 total)

1. **User Management**
   - `user` - User accounts with authentication
   - `user_lesson_progress` - Progress tracking
   - `user_quiz_answer` - Quiz responses

2. **Content Tables**
   - `kana` - Hiragana/Katakana characters
   - `kanji` - Kanji characters with readings
   - `vocabulary` - Japanese vocabulary words
   - `grammar` - Grammar rules and explanations

3. **Lesson System**
   - `lesson_category` - Lesson categories
   - `lesson` - Main lesson table
   - `lesson_content` - Lesson content items
   - `lesson_page` - Page organization
   - `lesson_prerequisite` - Lesson dependencies

4. **Quiz System**
   - `quiz_question` - Quiz questions
   - `quiz_option` - Multiple choice options

5. **Commerce**
   - `lesson_purchase` - Paid lesson tracking

6. **Course System**
   - `course` - Course collections
   - `course_lessons` - Course-lesson relationships

### Performance Indexes

- User progress lookups
- Lesson content queries
- Quiz question relationships
- Category filtering
- Purchase tracking

### Initial Data

- **Admin User**: `admin` / `admin123` (change after first login)
- **6 Lesson Categories**: Hiragana, Katakana, Kanji, Vocabulary, Grammar, Culture

## 🔧 Configuration Options

### Environment Variables (Recommended for Production)

```bash
export DB_HOST="34.65.227.94"
export DB_NAME="japanese_learning"
export DB_USER="app_user"
export DB_PASSWORD="your_secure_password"
export DB_PORT="5432"
```

Then modify the script to use environment variables:

```python
DB_CONFIG = {
    'host': os.getenv('DB_HOST', '34.65.227.94'),
    'database': os.getenv('DB_NAME', 'japanese_learning'),
    'username': os.getenv('DB_USER', 'app_user'),
    'password': os.getenv('DB_PASSWORD', 'Dg34.67MDt'),
    'port': int(os.getenv('DB_PORT', 5432))
}
```

## 🔄 Usage Scenarios

### Scenario 1: Fresh Database (Recommended)

```bash
python create_cloud_database.py
# Choose 'N' when asked about dropping tables
```

### Scenario 2: Reset Existing Database

```bash
python create_cloud_database.py
# Choose 'y' when asked about dropping tables
# Type 'DELETE' to confirm
```

### Scenario 3: Verify Existing Database

```bash
python test_db_connection.py
```

## 📝 Sample Output

```
🚀 Japanese Learning Website - Database Creator
==================================================
Connecting to: 34.65.227.94:5432/japanese_learning
Username: app_user

⚠️  Drop existing tables? (y/N): N

2025-01-20 19:30:00,123 - INFO - Starting database creation process...
2025-01-20 19:30:00,456 - INFO - Successfully connected to database japanese_learning
2025-01-20 19:30:00,789 - INFO - Executing: Creating User table
2025-01-20 19:30:00,890 - INFO - ✓ Success: Creating User table
...
2025-01-20 19:30:15,123 - INFO - ✓ Created admin user: admin
2025-01-20 19:30:15,234 - INFO - ✓ Created category: Hiragana
...
2025-01-20 19:30:16,345 - INFO - ✓ Database verification complete:
2025-01-20 19:30:16,345 - INFO -   - All 17 tables created successfully
2025-01-20 19:30:16,345 - INFO -   - 1 users created
2025-01-20 19:30:16,345 - INFO -   - 6 lesson categories created
2025-01-20 19:30:16,456 - INFO - 🎉 Database creation completed successfully!

✅ Database creation completed successfully!

Next steps:
1. Update your Flask app's DATABASE_URL to point to this database
2. Test your application connection
3. Import any existing data if needed

Admin user created:
  Username: admin
  Password: admin123
  (Please change this password after first login)
```

## 🔗 Update Your Flask Application

After successful database creation, update your Flask app configuration:

### Option 1: Environment Variable

```bash
export DATABASE_URL="postgresql://app_user:Dg34.67MDt@34.65.227.94:5432/japanese_learning"
```

### Option 2: Direct Configuration

```python
# In your Flask app configuration
SQLALCHEMY_DATABASE_URI = "postgresql://app_user:Dg34.67MDt@34.65.227.94:5432/japanese_learning"
```

### Option 3: Using Google Cloud SQL Proxy (Recommended for Production)

```python
# For production with Cloud SQL Proxy
SQLALCHEMY_DATABASE_URI = "postgresql://app_user:Dg34.67MDt@127.0.0.1:5432/japanese_learning"
```

## 🛠️ Troubleshooting

### Connection Issues

**Error**: `psycopg2.OperationalError: could not connect to server`

**Solutions**:
1. Check if your IP is authorized in Google Cloud SQL
2. Verify the instance is running
3. Confirm firewall rules allow port 5432

### Permission Issues

**Error**: `permission denied for table`

**Solutions**:
1. Verify user `app_user` has correct permissions
2. Check if user exists: `SELECT * FROM pg_user WHERE usename = 'app_user';`
3. Grant permissions: `GRANT ALL PRIVILEGES ON DATABASE japanese_learning TO app_user;`

### Table Already Exists

**Error**: `relation "table_name" already exists`

**Solutions**:
1. Run with drop tables option: Choose 'y' when prompted
2. Or manually drop specific tables if needed

### Import Errors

**Error**: `ModuleNotFoundError: No module named 'psycopg2'`

**Solution**:
```bash
pip install psycopg2-binary
```

## 📊 Verification Queries

After creation, you can verify your database:

```sql
-- Check all tables exist
SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;

-- Verify admin user
SELECT username, email, is_admin FROM "user" WHERE is_admin = true;

-- Check lesson categories
SELECT name, description, color_code FROM lesson_category;

-- Verify foreign key relationships
SELECT 
    tc.table_name, 
    kcu.column_name, 
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name 
FROM information_schema.table_constraints AS tc 
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY' 
ORDER BY tc.table_name;
```

## 🎉 Success!

Once completed, your Google Cloud PostgreSQL database will have:

- ✅ All 17 tables with proper relationships
- ✅ Performance indexes for fast queries
- ✅ Admin user ready for first login
- ✅ Sample lesson categories
- ✅ Production-ready schema matching your local database

Your Flask application can now connect directly to this database without any Alembic migration issues!

## 📞 Support

If you encounter any issues:

1. Check the `database_creation.log` file for detailed error messages
2. Run `python test_db_connection.py` to isolate connection issues
3. Verify your Google Cloud SQL instance settings
4. Ensure your IP is whitelisted in Google Cloud Console

The database structure exactly matches your local SQLite database, so your existing Flask application code will work without any modifications!
