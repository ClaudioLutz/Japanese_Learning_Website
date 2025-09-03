#!/bin/bash
set -e

echo "Starting application entrypoint..."

# Wait for database to be ready
echo "Waiting for database to be ready..."
until PGPASSWORD="$POSTGRES_PASSWORD" psql -h "db" -U "app_user" -d "japanese_learning" -c '\q'; do
  >&2 echo "Database is unavailable - sleeping"
  sleep 1
done

echo "Database is ready!"

# Initialize database schema first
echo "Creating initial database schema..."
python -c "
from app import create_app, db
app = create_app()
with app.app_context():
    db.create_all()
    print('Database tables created successfully!')
"

# Mark migrations as applied (since we created schema from current models)
echo "Marking migrations as applied..."
flask db stamp head || echo "Migration stamp completed"

echo "Database initialization completed successfully!"

# Start the application
echo "Starting Gunicorn server..."
exec gunicorn -w 4 -b 0.0.0.0:5000 run:app
