# Use Python 3.10 slim base image
FROM python:3.12-slim-bookworm

# Set working directory
WORKDIR /app

# Install system packages (libmagic for python-magic, postgresql-client for database connectivity check, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 build-essential libpq-dev postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . . 

# Copy and set permissions for entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose the Flask port
EXPOSE 5000

# Define environment variables (optional defaults)
ENV FLASK_APP=run.py \
    FLASK_ENV=production

# Use entrypoint script to handle database initialization
ENTRYPOINT ["/entrypoint.sh"]
