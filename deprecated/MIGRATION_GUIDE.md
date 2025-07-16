# Database Migration Guide: SQLite to Google Cloud SQL PostgreSQL

## Pre-Migration Checklist

Before running the migration, ensure the following prerequisites are met:

### ✅ **1. Database Preparation**
- [ ] Ensure the PostgreSQL database (`japanese_learning`) exists and is accessible
- [ ] **Note**: The script will automatically create all tables based on SQLite schema
- [ ] Ensure the PostgreSQL user `app_user` has the necessary permissions:
  - `CREATE`, `SELECT`, `INSERT`, `UPDATE`, `DELETE` on the database
  - `USAGE` and `CREATE` on the database schema

### ✅ **2. Code Repository**
- [ ] Confirm the migration script has been pulled to the VM via `git pull`
- [ ] Verify that `migrate_data.py` exists in the project root directory
- [ ] Ensure the SQLite database file `instance/site.db` exists and is accessible

### ✅ **3. Cloud SQL Auth Proxy**
- [ ] Download the Cloud SQL Auth Proxy binary to your VM
- [ ] Make the proxy executable: `chmod +x cloud_sql_proxy`
- [ ] Have your **Instance Connection Name** ready (format: `PROJECT_ID:REGION:INSTANCE_NAME`)
  - Find this in Google Cloud Console → SQL → Your Instance → Overview → Connection name
  - Example: `my-project:us-central1:japanese-learning-db`

### ✅ **4. Authentication**
- [ ] Ensure your VM has the necessary IAM permissions for Cloud SQL
- [ ] Verify that the service account or user has `Cloud SQL Client` role
- [ ] Test that you can connect to the Cloud SQL instance

### ✅ **5. Environment Setup**
- [ ] Confirm Python 3.7+ is installed
- [ ] Verify that you're in the correct project directory

---

## Terminal Commands Sequence

Execute these commands **in order** on your VM:

### **Step 1: Install Required Python Libraries**
```bash
pip install pandas sqlalchemy psycopg2-binary google-auth-oauthlib
```

### **Step 2: Start Cloud SQL Auth Proxy**
Replace `<INSTANCE_CONNECTION_NAME>` with your actual instance connection name:

```bash
./cloud_sql_proxy -instances=<INSTANCE_CONNECTION_NAME>=tcp:5432 &
```

**For your specific project:**
```bash
./cloud_sql_proxy -instances=gen-lang-client-0648546045:europe-west6:japanese-learning-db=tcp:5432 &
```

**Note:** The `&` runs the proxy in the background. You should see output like:
```
2025/01/15 15:42:00 Listening on 127.0.0.1:5432 for gen-lang-client-0648546045:europe-west6:japanese-learning-db
2025/01/15 15:42:00 Ready for new connections
```

### **Step 3: Set Database Password Environment Variable**
Replace `<YOUR_ACTUAL_PASSWORD>` with the actual password for the `app_user`:

```bash
export DB_PASSWORD="<YOUR_ACTUAL_PASSWORD>"
```

**Verify the environment variable is set:**
```bash
echo $DB_PASSWORD
```

### **Step 4: Run the Migration Script**
```bash
python migrate_data.py
```

### **Step 5: Monitor Progress**
The script will:
- Display real-time progress in the terminal
- Create a detailed log file named `migration_YYYYMMDD_HHMMSS.log`
- Show a final summary with success/failure statistics

### **Step 6: Stop the Cloud SQL Auth Proxy (After Migration)**
```bash
pkill -f cloud_sql_proxy
```

---

## Expected Output

### **Successful Migration Output:**
```
============================================================
STARTING DATABASE MIGRATION
Source: SQLite (instance/site.db)
Target: Google Cloud SQL PostgreSQL (japanese_learning)
============================================================
2025-01-15 15:42:05,123 - INFO - Connected to SQLite database: instance/site.db
2025-01-15 15:42:05,456 - INFO - Connected to PostgreSQL database via Cloud SQL Auth Proxy
2025-01-15 15:42:05,789 - INFO - SQLite connection test successful
2025-01-15 15:42:06,012 - INFO - PostgreSQL connection test successful
2025-01-15 15:42:06,234 - INFO - Discovered 8 user tables: users, lessons, courses, vocabulary, grammar, kana, kanji, user_progress

[1/8] Processing table: courses
2025-01-15 15:42:06,456 - INFO - Starting migration for table: 'courses'...
2025-01-15 15:42:06,567 - INFO - Table 'courses' has columns: id, title, description, created_at
2025-01-15 15:42:06,678 - INFO - Reading data from SQLite table 'courses'...
2025-01-15 15:42:06,789 - INFO - Read 15 rows from table 'courses'
2025-01-15 15:42:06,890 - INFO - Writing data to PostgreSQL table 'courses'...
2025-01-15 15:42:07,123 - INFO - ✅ Successfully migrated table 'courses': 15 rows

[2/8] Processing table: grammar
...

============================================================
MIGRATION COMPLETED
============================================================
Duration: 0:02:34.567890
Total tables processed: 8
Successful migrations: 8
Failed migrations: 0
Total rows migrated: 1,234

DETAILED RESULTS:
----------------------------------------
courses              | ✅ SUCCESS  |       15 rows
grammar              | ✅ SUCCESS  |      234 rows
kana                 | ✅ SUCCESS  |       92 rows
kanji                | ✅ SUCCESS  |      156 rows
lessons              | ✅ SUCCESS  |       45 rows
user_progress        | ✅ SUCCESS  |      567 rows
users                | ✅ SUCCESS  |       23 rows
vocabulary           | ✅ SUCCESS  |      102 rows

Migration log saved to: migration_20250115_154207.log

🎉 All tables migrated successfully!
```

---

## Troubleshooting

### **Common Issues and Solutions:**

#### **1. "DB_PASSWORD environment variable is not set!"**
- **Solution:** Run `export DB_PASSWORD="your_password"` before running the script
- **Verify:** Run `echo $DB_PASSWORD` to confirm it's set

#### **2. "Failed to create database connections"**
- **Check:** Is the Cloud SQL Auth Proxy running? Look for the "Ready for new connections" message
- **Check:** Is the proxy listening on the correct port (5432)?
- **Solution:** Restart the proxy with the correct instance connection name

#### **3. "No tables found to migrate!"**
- **Check:** Does `instance/site.db` exist in the current directory?
- **Check:** Is the SQLite database file readable?
- **Solution:** Verify the file path and permissions

#### **4. "Connection refused" or "Connection timeout"**
- **Check:** Is your VM's firewall blocking port 5432?
- **Check:** Are you using the correct instance connection name?
- **Check:** Does your service account have Cloud SQL Client permissions?

#### **5. Individual table migration failures**
- **Check:** Are there data type incompatibilities?
- **Check:** Does the user have sufficient permissions (CREATE, INSERT, etc.)?
- **Solution:** Review the detailed error message in the log file for specific details

### **Verification Commands:**

#### **Check if Cloud SQL Auth Proxy is running:**
```bash
ps aux | grep cloud_sql_proxy
```

#### **Test PostgreSQL connection manually:**
```bash
psql -h localhost -p 5432 -U app_user -d japanese_learning
```

#### **Check table counts in PostgreSQL after migration:**

**Method 1: Direct count (most accurate):**
```sql
-- Replace 'table_name' with actual table names from your migration
SELECT 'users' as table_name, COUNT(*) as row_count FROM users
UNION ALL
SELECT 'lessons', COUNT(*) FROM lessons
UNION ALL
SELECT 'courses', COUNT(*) FROM courses
UNION ALL
SELECT 'vocabulary', COUNT(*) FROM vocabulary
UNION ALL
SELECT 'grammar', COUNT(*) FROM grammar
UNION ALL
SELECT 'kana', COUNT(*) FROM kana
UNION ALL
SELECT 'kanji', COUNT(*) FROM kanji
UNION ALL
SELECT 'user_progress', COUNT(*) FROM user_progress
ORDER BY table_name;
```

**Method 2: Using table statistics (may have minor delays):**
```sql
SELECT 
    schemaname,
    tablename,
    n_tup_ins as row_count
FROM pg_stat_user_tables 
ORDER BY tablename;
```

---

## Post-Migration Steps

### **1. Verify Data Integrity**
- [ ] Compare row counts between source and destination
- [ ] Spot-check critical data records
- [ ] Test application functionality with the new database

### **2. Update Application Configuration**
- [ ] Update database connection strings in your application
- [ ] Test all database-dependent features
- [ ] Update any hardcoded references to SQLite

### **3. Backup and Cleanup**
- [ ] Create a backup of the PostgreSQL database
- [ ] Archive the original SQLite database file
- [ ] Clean up temporary migration files if desired

### **4. Monitor Performance**
- [ ] Monitor database performance after migration
- [ ] Check for any slow queries that may need optimization
- [ ] Verify that indexes are properly created in PostgreSQL

---

## Security Notes

- **Never commit passwords to version control**
- **Use environment variables for sensitive configuration**
- **Ensure the Cloud SQL Auth Proxy connection is secure**
- **Regularly rotate database passwords**
- **Monitor database access logs**

---

## Support

If you encounter issues during migration:

1. **Check the detailed log file** created by the script
2. **Review the troubleshooting section** above
3. **Verify all prerequisites** in the checklist
4. **Test connections manually** using the verification commands

The migration script includes comprehensive error handling and logging to help diagnose any issues that may arise during the process.
