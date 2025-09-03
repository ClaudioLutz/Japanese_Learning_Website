#!/bin/bash
set -e

echo "🔄 Japanese Learning Website - Data Migration Script"
echo "===================================================="
echo "This script migrates data from your local Docker PostgreSQL to Cloud SQL"
echo ""

# Configuration variables (should match deploy script)
PROJECT_ID="healthy-coil-466105-d7"
REGION="europe-west6"
INSTANCE="jpl-psql"
DB="japanese_learning"
DB_USER="app_user"

# Local Docker database configuration
LOCAL_HOST="localhost"
LOCAL_PORT="5432"
LOCAL_USER="app_user"
LOCAL_DB="japanese_learning"

echo "Configuration:"
echo "- Source (Docker): $LOCAL_HOST:$LOCAL_PORT/$LOCAL_DB"
echo "- Target (Cloud SQL): $PROJECT_ID:$REGION:$INSTANCE/$DB"
echo ""

# Check if Docker container is running
echo "🔍 Checking if Docker PostgreSQL is running..."
if ! docker ps | grep -q postgres; then
    echo "❌ Docker PostgreSQL container is not running!"
    echo "   Please start your Docker container first:"
    echo "   docker-compose up -d"
    exit 1
fi

echo "✅ Docker PostgreSQL container is running"

# Prompt for database password (from Cloud SQL setup)
read -s -p "🔐 Enter the Cloud SQL database password: " CLOUD_DB_PASS
echo ""

# Prompt for local database password
read -s -p "🔐 Enter the local Docker database password: " LOCAL_DB_PASS
echo ""

# Create dump directory
DUMP_DIR="./database_dump"
mkdir -p $DUMP_DIR

# Dump local database
echo "📦 Creating database dump from local PostgreSQL..."
PGPASSWORD="$LOCAL_DB_PASS" pg_dump \
  -h $LOCAL_HOST \
  -p $LOCAL_PORT \
  -U $LOCAL_USER \
  -d $LOCAL_DB \
  --verbose \
  --no-owner \
  --no-privileges \
  --clean \
  --if-exists \
  -f "$DUMP_DIR/japanese_learning_dump.sql"

echo "✅ Database dump created successfully!"

# Connect to Cloud SQL and restore
echo "🚀 Restoring data to Cloud SQL..."

# Use Cloud SQL Proxy for secure connection
echo "Starting Cloud SQL Proxy..."
cloud_sql_proxy "$PROJECT_ID:$REGION:$INSTANCE" &
PROXY_PID=$!

# Wait for proxy to be ready
sleep 5

# Restore database
echo "📥 Restoring database to Cloud SQL..."
PGPASSWORD="$CLOUD_DB_PASS" psql \
  -h 127.0.0.1 \
  -p 5432 \
  -U $DB_USER \
  -d $DB \
  -f "$DUMP_DIR/japanese_learning_dump.sql"

echo "✅ Database restored successfully!"

# Clean up
kill $PROXY_PID 2>/dev/null || true
echo "🧹 Cleaned up Cloud SQL Proxy"

echo ""
echo "🎉 Migration completed successfully!"
echo ""
echo "📋 Summary:"
echo "- Source database backed up to: $DUMP_DIR/japanese_learning_dump.sql"
echo "- Data migrated to Cloud SQL instance: $INSTANCE"
echo "- Database: $DB"
echo ""
echo "⚠️  IMPORTANT:"
echo "1. Keep the database dump file as backup"
echo "2. Test your Cloud Run application to ensure data is accessible"
echo "3. You can now stop your local Docker containers if desired"
echo ""
echo "🔄 Next steps:"
echo "1. Test your Cloud Run deployment"
echo "2. Verify all data has been migrated correctly"
echo "3. Update any local development connections if needed"
