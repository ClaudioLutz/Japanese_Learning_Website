# Production Database Setup Guide

## After Migration: Configure Your Application for PostgreSQL

Once you've successfully migrated your data using the migration scripts, you need to configure your Flask application to use the PostgreSQL database in production.

## ✅ **Good News: Your App is Already Configured!**

Your Flask application in `app/__init__.py` already has the correct logic:

```python
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or \
    'sqlite:///' + os.path.join(app.instance_path, 'site.db')
```

This means:
- **Local Development**: Uses SQLite (when `DATABASE_URL` is not set)
- **Production**: Uses PostgreSQL (when `DATABASE_URL` is set)

## 🚀 **Production Environment Setup**

### **Step 1: Set the DATABASE_URL Environment Variable**

On your production server (VM), set the `DATABASE_URL` environment variable to point to your PostgreSQL database:

```bash
export DATABASE_URL="postgresql://app_user:YOUR_PASSWORD@localhost:5432/japanese_learning"
```

**For your specific setup:**
```bash
export DATABASE_URL="postgresql://app_user:YOUR_PASSWORD@localhost:5432/japanese_learning"
```

### **Step 2: Make the Environment Variable Persistent**

Add the environment variable to your shell profile so it persists across sessions:

```bash
echo 'export DATABASE_URL="postgresql://app_user:YOUR_PASSWORD@localhost:5432/japanese_learning"' >> ~/.bashrc
source ~/.bashrc
```

### **Step 3: Install PostgreSQL Python Driver**

Ensure the PostgreSQL driver is installed in your production environment:

```bash
pip install psycopg2-binary
```

### **Step 4: Start Cloud SQL Auth Proxy (Production)**

In production, you'll need to keep the Cloud SQL Auth Proxy running. You can use a process manager like `systemd` or `supervisor`, or run it in a screen session:

```bash
# Option 1: Run in screen session
screen -S cloudsql-proxy
./cloud_sql_proxy -instances=gen-lang-client-0648546045:europe-west6:japanese-learning-db=tcp:5432

# Option 2: Run as background process with nohup
nohup ./cloud_sql_proxy -instances=gen-lang-client-0648546045:europe-west6:japanese-learning-db=tcp:5432 > cloudsql-proxy.log 2>&1 &
```

### **Step 5: Test the Configuration**

Test that your application can connect to PostgreSQL:

```bash
# Set the environment variable
export DATABASE_URL="postgresql://app_user:YOUR_PASSWORD@localhost:5432/japanese_learning"

# Start your Flask application
python run.py
```

## 🔍 **Verification Steps**

### **1. Check Database Connection**
Your Flask app should start without database connection errors.

### **2. Test Application Functionality**
- Login/Registration should work
- Lessons should load correctly
- Admin panel should function
- All CRUD operations should work

### **3. Monitor Logs**
Check your application logs for any database-related errors:

```bash
tail -f your_app.log
```

## 🛠️ **Alternative: Using a .env File**

Instead of setting environment variables manually, you can use a `.env` file in your project root:

```bash
# Create .env file
cat > .env << EOF
DATABASE_URL=postgresql://app_user:YOUR_PASSWORD@localhost:5432/japanese_learning
FLASK_ENV=production
EOF
```

Your app already loads environment variables using `python-dotenv` in `app/__init__.py`.

## 🔧 **Troubleshooting**

### **Issue: "No module named 'psycopg2'"**
**Solution:** Install the PostgreSQL driver:
```bash
pip install psycopg2-binary
```

### **Issue: "Connection refused"**
**Solution:** Ensure Cloud SQL Auth Proxy is running:
```bash
ps aux | grep cloud_sql_proxy
```

### **Issue: "Database doesn't exist"**
**Solution:** Verify the database name in your connection string matches the actual database name (`japanese_learning`).

### **Issue: Application still uses SQLite**
**Solution:** Verify the `DATABASE_URL` environment variable is set:
```bash
echo $DATABASE_URL
```

## ✅ **Success Indicators**

Your application is successfully using PostgreSQL when:

1. **No SQLite files are created** in the instance folder
2. **Database operations work** (login, lessons, admin functions)
3. **Application logs show PostgreSQL connections**
4. **Data matches what you migrated** from SQLite

## 🎯 **Complete Production Workflow**

```bash
# 1. Ensure Cloud SQL Auth Proxy is running
./cloud_sql_proxy -instances=gen-lang-client-0648546045:europe-west6:japanese-learning-db=tcp:5432 &

# 2. Set database URL
export DATABASE_URL="postgresql://app_user:YOUR_PASSWORD@localhost:5432/japanese_learning"

# 3. Install dependencies (if not already installed)
pip install psycopg2-binary

# 4. Start your Flask application
python run.py
```

Your Flask application will automatically use PostgreSQL instead of SQLite, and all your migrated data will be available!
