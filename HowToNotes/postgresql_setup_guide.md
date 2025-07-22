# PostgreSQL Setup Guide for Japanese Learning Website

## Step 1: Uninstall Existing PostgreSQL (if needed)

1. **Uninstall PostgreSQL via Control Panel:**
   - Go to Control Panel > Programs and Features
   - Find PostgreSQL and uninstall it
   - Also uninstall pgAdmin if present

2. **Clean up remaining files:**
   - Delete `C:\Program Files\PostgreSQL` folder
   - Delete `C:\Users\[username]\AppData\Roaming\postgresql` folder
   - Delete `C:\Users\[username]\AppData\Local\PostgreSQL` folder

## Step 2: Fresh PostgreSQL Installation

1. **Download PostgreSQL:**
   - Go to https://www.postgresql.org/download/windows/
   - Download the latest version (15.x or 16.x recommended)

2. **Installation Process:**
   - Run the installer as Administrator
   - **IMPORTANT:** When prompted for the superuser password, use: `PostgreSQL2025!`
   - Write this password down immediately in a secure location
   - Accept default port (5432)
   - Accept default locale
   - Install pgAdmin when prompted

3. **Verify Installation:**
   - Open pgAdmin
   - Connect using password: `PostgreSQL2025!`

## Step 3: Create Application Database and User

1. **Open pgAdmin and connect to PostgreSQL**

2. **Create the database:**
   ```sql
   CREATE DATABASE japanese_learning;
   ```

3. **Create application user:**
   ```sql
   CREATE USER app_user WITH PASSWORD 'JapaneseApp2025!';
   ```

4. **Grant permissions:**
   ```sql
   GRANT ALL PRIVILEGES ON DATABASE japanese_learning TO app_user;
   \c japanese_learning
   GRANT ALL ON SCHEMA public TO app_user;
   GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO app_user;
   GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO app_user;
   ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO app_user;
   ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO app_user;
   ```

## Step 4: Update Environment Configuration

Update your `.env` file with the new database connection:

```
DATABASE_URL="postgresql://app_user:JapaneseApp2025!@localhost:5432/japanese_learning"
```

## Step 5: Test Connection

Run this command to test the database connection:
```bash
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
import psycopg2
try:
    conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
    print('✅ Database connection successful!')
    conn.close()
except Exception as e:
    print(f'❌ Database connection failed: {e}')
"
```

## Important Passwords to Save:

- **PostgreSQL Superuser (postgres):** `PostgreSQL2025!`
- **Application User (app_user):** `JapaneseApp2025!`

Save these passwords in your password manager immediately!

## Next Steps After Database Setup:

1. Run database migrations: `flask db upgrade`
2. Set up Google OAuth credentials
3. Test the complete authentication flow
