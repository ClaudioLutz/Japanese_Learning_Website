# Fresh PostgreSQL Database Setup Guide

This guide will help you create a completely fresh PostgreSQL database for the Japanese Learning Website, replacing the old SQLite database.

## Prerequisites

1. **PostgreSQL installed** (version 12 or higher)
2. **Python environment** with all requirements installed
3. **pgAdmin** (optional but recommended for database management)

## Step 1: Create the PostgreSQL Database

### Option A: Using pgAdmin (Recommended)

1. Open pgAdmin and connect to your PostgreSQL server
2. Right-click on "Databases" and select "Query Tool"
3. Copy and paste the contents of `create_fresh_postgres_db.sql`
4. Execute the script (F5 or click Execute)

### Option B: Using Command Line

```bash
# Connect to PostgreSQL as superuser
psql -U postgres -h localhost

# Run the setup script
\i create_fresh_postgres_db.sql
```

### Option C: Using psql with file

```bash
psql -U postgres -h localhost -f create_fresh_postgres_db.sql
```

## Step 2: Verify Database Creation

After running the script, you should see:
- Database: `japanese_learning_new`
- User: `app_user_new`
- Password: `JapaneseApp2025Fresh!`

## Step 3: Update Environment Configuration

The `.env` file has already been updated with the new database connection:

```
DATABASE_URL="postgresql://app_user_new:JapaneseApp2025Fresh!@localhost:5432/japanese_learning_new"
```

## Step 4: Install Required Python Packages

Make sure you have the PostgreSQL adapter installed:

```bash
pip install psycopg2-binary
```

## Step 5: Run the Database Setup Script

Execute the automated setup script:

```bash
python setup_fresh_database.py
```

This script will:
- Test the PostgreSQL connection
- Initialize Flask-Migrate (if needed)
- Apply all migrations in the correct order
- Verify the database setup

## Step 6: Create an Admin User (Optional)

```bash
python create_admin.py
```

## Database Schema Overview

The fresh database will include all these tables:

### Core Content Tables
- `user` - User accounts and authentication
- `kana` - Hiragana and Katakana characters
- `kanji` - Kanji characters with readings and meanings
- `vocabulary` - Japanese vocabulary words
- `grammar` - Grammar rules and explanations

### Lesson System
- `lesson_category` - Categories for organizing lessons
- `lesson` - Main lesson table with pricing and metadata
- `lesson_content` - Content items within lessons (with AI tracking)
- `lesson_page` - Page metadata for multi-page lessons
- `lesson_prerequisite` - Prerequisites between lessons
- `lesson_purchase` - Purchase records for paid lessons

### Quiz and Progress System
- `quiz_question` - Questions for interactive content
- `quiz_option` - Multiple choice options
- `user_quiz_answer` - User's quiz responses
- `user_lesson_progress` - User progress through lessons

### Course System
- `course` - Course collections
- `course_lessons` - Many-to-many relationship between courses and lessons

### Social Authentication
- `social_auth_association` - OAuth associations
- `social_auth_code` - Verification codes
- `social_auth_nonce` - Security nonces
- `social_auth_usersocialauth` - User social auth records

## Troubleshooting

### Connection Issues

If you get connection errors:

1. **Check PostgreSQL service is running**
   ```bash
   # Windows
   net start postgresql-x64-15
   
   # Linux/Mac
   sudo systemctl start postgresql
   ```

2. **Verify database exists**
   ```bash
   psql -U postgres -h localhost -c "\l"
   ```

3. **Test connection manually**
   ```bash
   psql -U app_user_new -h localhost -d japanese_learning_new
   ```

### Migration Issues

If migrations fail:

1. **Check current migration status**
   ```bash
   flask db current
   ```

2. **Reset migrations (if needed)**
   ```bash
   flask db stamp head
   ```

3. **Force upgrade**
   ```bash
   flask db upgrade
   ```

### Permission Issues

If you get permission errors:

```sql
-- Connect as superuser and run:
GRANT ALL PRIVILEGES ON DATABASE japanese_learning_new TO app_user_new;
\c japanese_learning_new
GRANT ALL ON SCHEMA public TO app_user_new;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO app_user_new;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO app_user_new;
```

## Important Credentials

**Save these credentials securely:**

- **Database**: `japanese_learning_new`
- **Username**: `app_user`
- **Password**: `E8BnuCBpWKP`
- **Host**: `localhost`
- **Port**: `5432`

## Next Steps

After successful database setup:

1. **Create admin user**: `python create_admin.py`
2. **Set up Google OAuth** (update GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env)
3. **Test the application**: `python run.py`
4. **Import existing data** (if you have backups)

## Backup and Maintenance

### Create Backup
```bash
pg_dump -U app_user_new -h localhost japanese_learning_new > backup.sql
```

### Restore Backup
```bash
psql -U app_user_new -h localhost japanese_learning_new < backup.sql
```

### Monitor Database Size
```sql
SELECT pg_size_pretty(pg_database_size('japanese_learning_new'));
```

## Security Notes

- Change default passwords in production
- Use environment variables for sensitive data
- Enable SSL for production deployments
- Regular backups are recommended
- Monitor database logs for suspicious activity
