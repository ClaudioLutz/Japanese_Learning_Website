# Local PostgreSQL Database Setup Guide

This guide will help you set up a complete local PostgreSQL database for the Japanese Learning Website with all required tables and initial data.

## 🎯 What This Creates

- **Complete Database Schema**: All 21 tables with proper relationships
- **Initial Data**: Admin user and lesson categories
- **Performance Indexes**: Optimized for fast queries
- **Social Authentication**: Google OAuth support tables
- **Monetization System**: Lesson purchase tracking

## 📋 Prerequisites

### 1. Install PostgreSQL

**Windows:**
- Download from [postgresql.org](https://www.postgresql.org/download/windows/)
- Run the installer and remember your postgres user password
- Default port: 5432

**macOS:**
```bash
# Using Homebrew
brew install postgresql
brew services start postgresql

# Or using Postgres.app
# Download from https://postgresapp.com/
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 2. Install Python Dependencies

```bash
# Install required packages
pip install psycopg[binary] werkzeug python-dotenv
```

## 🚀 Quick Start

### Step 1: Test Your PostgreSQL Connection

```bash
python test_local_db_connection.py
```

**Expected Output:**
```
🔍 Testing Local PostgreSQL Connection
========================================
Please provide your local PostgreSQL connection details:
Host (default: localhost): 
Port (default: 5432): 
Username (default: postgres): 
Password: [your_password]

Testing connection to: localhost:5432
Username: postgres
----------------------------------------
Connecting to PostgreSQL server...
✓ Connection successful!
✓ PostgreSQL Version: PostgreSQL 15.x...
ℹ Database 'japanese_learning' does not exist yet (will be created)
✓ Write permissions confirmed (test records: 1)

🎉 Database connection test completed successfully!

You can now run: python create_local_database.py
```

### Step 2: Create the Database

```bash
python create_local_database.py
```

**Sample Interaction:**
```
🚀 Japanese Learning Website - Local Database Creator
=======================================================
Please provide your local PostgreSQL connection details:
Host (default: localhost): 
Port (default: 5432): 
Database name (default: japanese_learning): 
Username (default: postgres): 
Password: [your_password]

Connecting to: localhost:5432/japanese_learning
Username: postgres

⚠️  Drop existing tables? (y/N): N

Starting local database creation process...
Created database: japanese_learning
Successfully connected to local database japanese_learning
Executing: Creating User table
✓ Success: Creating User table
...
✓ Created admin user: admin
✓ Created category: Hiragana
...
✓ Database verification complete:
  - All 21 tables created successfully
  - 1 users created
  - 6 lesson categories created
🎉 Local database creation completed successfully!
```

### Step 3: Configure Your Flask Application

Add to your `.env` file:
```bash
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/japanese_learning
```

Or set environment variable:
```bash
export DATABASE_URL="postgresql://postgres:your_password@localhost:5432/japanese_learning"
```

### Step 4: Run Your Application

```bash
python run.py
```

## 📊 Database Structure Created

### Core Tables (21 total)

1. **User Management**
   - `user` - User accounts and authentication
   - `user_lesson_progress` - Progress tracking per lesson
   - `user_quiz_answer` - Quiz responses and scores

2. **Content Tables**
   - `kana` - Hiragana/Katakana characters
   - `kanji` - Kanji with readings and meanings
   - `vocabulary` - Japanese vocabulary words
   - `grammar` - Grammar rules and explanations

3. **Lesson System**
   - `lesson_category` - Lesson organization categories
   - `lesson` - Main lesson table with metadata
   - `lesson_content` - Individual content items within lessons
   - `lesson_page` - Page organization within lessons
   - `lesson_prerequisite` - Lesson dependency relationships

4. **Interactive System**
   - `quiz_question` - Quiz questions for lessons
   - `quiz_option` - Multiple choice options

5. **Course System**
   - `course` - Course collections
   - `course_lessons` - Many-to-many course-lesson relationships

6. **Monetization**
   - `lesson_purchase` - Individual lesson purchase tracking

7. **Social Authentication**
   - `social_auth_usersocialauth` - Social account links
   - `social_auth_nonce` - OAuth security
   - `social_auth_association` - OpenID associations
   - `social_auth_code` - Email verification codes

### Initial Data Created

- **Admin User**: `admin` / `admin123`
- **6 Lesson Categories**:
  - Hiragana (#FF6B6B)
  - Katakana (#4ECDC4)
  - Kanji (#45B7D1)
  - Vocabulary (#96CEB4)
  - Grammar (#FFEAA7)
  - Culture (#DDA0DD)

### Performance Indexes

- User progress lookups
- Lesson content queries
- Quiz relationships
- Category filtering
- Purchase tracking
- Social authentication

## 🔧 Configuration Options

### Using Environment Variables

Create a `.env` file in your project root:
```bash
# Database Configuration
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/japanese_learning

# Flask Configuration
SECRET_KEY=your-secret-key-here
WTF_CSRF_SECRET_KEY=your-csrf-secret-key

# Google OAuth (optional)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

### Custom Database Configuration

You can modify the database name, user, or other settings when running the script:

```bash
python create_local_database.py
```

Then enter your custom values when prompted.

## 🔄 Usage Scenarios

### Scenario 1: Fresh Setup (Recommended)

```bash
# Test connection first
python test_local_db_connection.py

# Create database
python create_local_database.py
# Choose 'N' when asked about dropping tables
```

### Scenario 2: Reset Existing Database

```bash
python create_local_database.py
# Choose 'y' when asked about dropping tables
# Type 'DELETE' to confirm
```

### Scenario 3: Verify Existing Setup

```bash
python test_local_db_connection.py
```

## 🛠️ Troubleshooting

### Connection Issues

**Error**: `psycopg.OperationalError: connection to server failed`

**Solutions**:
1. **Check PostgreSQL is running**:
   ```bash
   # Windows (if installed as service)
   net start postgresql-x64-15
   
   # macOS with Homebrew
   brew services start postgresql
   
   # Linux
   sudo systemctl start postgresql
   ```

2. **Verify connection details**:
   - Host: Usually `localhost`
   - Port: Usually `5432`
   - Username: Usually `postgres`
   - Password: Set during PostgreSQL installation

3. **Check PostgreSQL configuration**:
   ```bash
   # Find PostgreSQL config
   sudo -u postgres psql -c "SHOW config_file;"
   
   # Edit postgresql.conf to allow connections
   listen_addresses = 'localhost'
   port = 5432
   ```

### Permission Issues

**Error**: `permission denied for database`

**Solutions**:
1. **Connect as postgres user**:
   ```bash
   sudo -u postgres psql
   ```

2. **Create user with proper permissions**:
   ```sql
   CREATE USER your_username WITH PASSWORD 'your_password';
   ALTER USER your_username CREATEDB;
   GRANT ALL PRIVILEGES ON DATABASE japanese_learning TO your_username;
   ```

### Module Import Errors

**Error**: `ModuleNotFoundError: No module named 'psycopg'`

**Solution**:
```bash
pip install psycopg[binary]
```

**Error**: `ModuleNotFoundError: No module named 'werkzeug'`

**Solution**:
```bash
pip install werkzeug
```

### Database Already Exists

**Error**: `database "japanese_learning" already exists`

**Solutions**:
1. **Use existing database**: Choose 'N' when asked to drop tables
2. **Reset database**: Choose 'y' and type 'DELETE' to confirm
3. **Manual cleanup**:
   ```bash
   sudo -u postgres psql
   DROP DATABASE japanese_learning;
   ```

## 📝 Verification Queries

After creation, you can verify your database using psql:

```bash
# Connect to your database
psql -h localhost -U postgres -d japanese_learning

# Check all tables exist
\dt

# Verify admin user
SELECT username, email, is_admin FROM "user" WHERE is_admin = true;

# Check lesson categories
SELECT name, description, color_code FROM lesson_category;

# Count tables
SELECT COUNT(*) FROM information_schema.tables 
WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
```

Expected output: 21 tables total.

## 🎉 Success!

Once completed, your local PostgreSQL database will have:

- ✅ All 21 tables with proper relationships
- ✅ Performance indexes for fast queries
- ✅ Admin user ready for first login
- ✅ Sample lesson categories
- ✅ Production-ready schema

Your Flask application can now connect to this database and all features will work locally!

## 📞 Next Steps

1. **Start your Flask application**: `python run.py`
2. **Login as admin**: Username `admin`, Password `admin123`
3. **Change admin password**: Go to user settings
4. **Create your first lesson**: Use the admin panel
5. **Test the application**: Create users, lessons, and quizzes

## 🔗 Related Files

- `create_local_database.py` - Main database creation script
- `test_local_db_connection.py` - Connection testing script
- `app/models.py` - SQLAlchemy model definitions
- `Documentation/10-Database-Schema.md` - Detailed schema documentation

The database structure exactly matches the production schema, so your local development environment will behave identically to production!
