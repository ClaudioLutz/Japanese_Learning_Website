#!/bin/bash
# set -e removed - we want to continue despite database connection issues

echo "🚀 Starting Japanese Learning Website on Cloud Run..."

# Cloud Run provides the PORT environment variable
PORT=${PORT:-8080}

echo "Configuration:"
echo "- Port: $PORT"
echo "- Environment: ${FLASK_ENV:-production}"
echo "- Database URL configured: $(echo $DATABASE_URL | cut -c1-50)..."

# Function to wait for database connection
wait_for_database() {
    echo "🔗 Waiting for database connection..."
    for i in {1..30}; do
        if python -c "
import os
from sqlalchemy import create_engine
try:
    engine = create_engine(os.environ['DATABASE_URL'])
    conn = engine.connect()
    conn.close()
    print('✅ Database connection successful!')
    exit(0)
except Exception as e:
    print(f'⚠️  Database connection attempt {i}/30 failed: {e}')
    exit(1)
" 2>/dev/null; then
            echo "✅ Database is ready!"
            return 0
        fi
        echo "⏳ Waiting for database... (attempt $i/30)"
        sleep 2
    done
    echo "⚠️  Database connection timeout - proceeding anyway"
    return 1
}

# Wait for database connection with timeout
wait_for_database

# Initialize database schema if needed (with error handling)
echo "🔧 Attempting database initialization..."
python -c "
import os
import sys
try:
    from app import create_app, db
    app = create_app()
    with app.app_context():
        try:
            # Try to create all tables
            db.create_all()
            print('✅ Database tables created/verified successfully!')
        except Exception as e:
            print(f'⚠️  Database initialization note: {e}')
            print('This may be expected if tables already exist or database is unavailable.')
except ImportError as e:
    print(f'⚠️  Import error during database setup: {e}')
    print('Application will start without database initialization.')
except Exception as e:
    print(f'⚠️  Database setup error: {e}')
    print('Application will start anyway.')
" || echo "⚠️  Database initialization skipped - application will start anyway"

echo "✅ Proceeding to start application!"

# Start the application with Gunicorn (reduced workers for Cloud Run)
echo "🚀 Starting Gunicorn server on port $PORT..."
exec gunicorn \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --worker-class sync \
    --timeout 300 \
    --keep-alive 2 \
    --log-level info \
    --access-logfile - \
    --error-logfile - \
    run:app
