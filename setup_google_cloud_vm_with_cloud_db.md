# Comprehensive Flask Deployment Guide for Google Cloud Platform

## Executive summary

This guide provides a **complete production deployment strategy** for your Japanese Learning Website Flask application on Google Cloud Platform. The deployment leverages your existing VM with a fresh Cloud SQL PostgreSQL database, proper security hardening, and production-grade configuration. **Key advantages**: Clean database setup eliminates previous migration issues, Secret Manager provides secure credential storage, Cloud Storage handles file uploads efficiently, and the configuration supports easy SSL setup for future HTTPS implementation.

## Prerequisites and project setup

### Project initialization
```bash
# Authenticate and configure GCP project
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud config set compute/zone europe-west6-c

# Enable required APIs
gcloud services enable sqladmin.googleapis.com
gcloud services enable compute.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable storage.googleapis.com
```

### Environment preparation
Your existing VM specifications are optimal for this deployment:
- **Instance**: japanese-learning-website-neu (e2-micro, 1 vCPU, 1GB RAM)
- **Location**: europe-west6-c (matches optimal Cloud SQL placement)
- **Cost estimate**: ~$20-30/month total (VM + Cloud SQL + storage)

## Step 1: Google Cloud SQL PostgreSQL setup

### Create production database instance
```bash
# Create PostgreSQL 16 instance with production configuration
gcloud sql instances create japanese-learning-db \
    --database-version=POSTGRES_16 \
    --tier=db-f1-micro \
    --region=europe-west6 \
    --storage-type=SSD \
    --storage-size=20GB \
    --storage-auto-increase \
    --backup-start-time=03:00 \
    --enable-point-in-time-recovery \
    --maintenance-window-day=sun \
    --maintenance-window-hour=04 \
    --no-assign-ip \
    --network=default

# Create database and user
gcloud sql databases create japanese_learning --instance=japanese-learning-db
gcloud sql users create app_user --instance=japanese-learning-db --password=SECURE_PASSWORD_HERE
```

### Configure private networking
```bash
# Allocate IP range for private services
gcloud compute addresses create google-managed-services-default \
    --global \
    --purpose=VPC_PEERING \
    --prefix-length=16 \
    --network=default

# Create private connection
gcloud services vpc-peerings connect \
    --service=servicenetworking.googleapis.com \
    --ranges=google-managed-services-default \
    --network=default
```

## Step 2: VM environment configuration

### System preparation and security hardening
```bash
# Connect to your VM
gcloud compute ssh japanese-learning-website-neu --zone=europe-west6-c

# Update system and install packages
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv postgresql-client \
    nginx ufw fail2ban wget curl git htop certbot python3-certbot-nginx \
    build-essential python3-dev libpq-dev

# Configure firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# Enable fail2ban for SSH protection
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### Application directory setup
```bash
# Create application directory structure
sudo mkdir -p /opt/japanese_learning
sudo chown $USER:$USER /opt/japanese_learning
cd /opt/japanese_learning

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install flask==3.0.0 gunicorn==21.2.0 psycopg2-binary==2.9.9 \
    flask-sqlalchemy==3.1.1 alembic==1.13.1 pillow==10.1.0 \
    flask-migrate==4.0.5 python-dotenv==1.0.0 google-cloud-storage==2.9.0 \
    google-cloud-secret-manager==2.16.4 flask-login==0.6.3 flask-wtf==1.2.1
```

## Step 3: Secure credential management with Secret Manager

### Create and configure secrets
```bash
# Create secrets for your application
gcloud secrets create openai-api-key --data-file=- <<< "your-openai-api-key-here"
gcloud secrets create db-password --data-file=- <<< "your-secure-db-password"
gcloud secrets create flask-secret-key --data-file=- <<< "your-flask-secret-key"

# Create service account for the application
gcloud iam service-accounts create japanese-learning-app \
    --display-name="Japanese Learning App Service Account"

# Grant secret access permissions
for secret in openai-api-key db-password flask-secret-key; do
    gcloud secrets add-iam-policy-binding $secret \
        --member="serviceAccount:japanese-learning-app@$(gcloud config get-value project).iam.gserviceaccount.com" \
        --role="roles/secretmanager.secretAccessor"
done
```

### Application configuration with Secret Manager
```python
# config.py - Enhanced configuration for production
import os
from google.cloud import secretmanager

class Config:
    def __init__(self):
        self.client = secretmanager.SecretManagerServiceClient()
        self.project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
    
    def get_secret(self, secret_name, version='latest'):
        """Retrieve secret from Secret Manager"""
        if not self.project_id:
            return os.environ.get(secret_name.upper().replace('-', '_'))
        
        try:
            name = f"projects/{self.project_id}/secrets/{secret_name}/versions/{version}"
            response = self.client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            print(f"Error accessing secret {secret_name}: {e}")
            return None

# Initialize configuration
config = Config()

class ProductionConfig:
    SECRET_KEY = config.get_secret('flask-secret-key')
    OPENAI_API_KEY = config.get_secret('openai-api-key')
    
    # Database configuration for Cloud SQL
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://app_user:{config.get_secret('db-password')}"
        f"@10.x.x.x:5432/japanese_learning"  # Use private IP
    )
    
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 3600,
        "pool_timeout": 30,
        "max_overflow": 10,
    }
    
    UPLOAD_FOLDER = '/opt/japanese_learning/static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
```

## Step 4: Database connection and Alembic configuration

### Cloud SQL connection setup
```bash
# Download and setup Cloud SQL Auth Proxy
cd /opt/japanese_learning
wget https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.2/cloud-sql-proxy.linux.amd64 -O cloud-sql-proxy
chmod +x cloud-sql-proxy

# Create systemd service for Cloud SQL proxy
sudo tee /etc/systemd/system/cloudsql-proxy.service > /dev/null <<EOF
[Unit]
Description=Google Cloud SQL Proxy
After=network.target

[Service]
Type=simple
User=$USER
ExecStart=/opt/japanese_learning/cloud-sql-proxy --private-ip YOUR_PROJECT_ID:europe-west6:japanese-learning-db
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable cloudsql-proxy
sudo systemctl start cloudsql-proxy
```

### Alembic configuration for fresh database
```python
# alembic/env.py - Enhanced for Cloud SQL
import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Import your models
from app import db  # Adjust import path as needed
target_metadata = db.metadata

def get_database_url():
    """Get database URL for Cloud SQL connection"""
    if os.environ.get('GOOGLE_CLOUD_PROJECT'):
        # Production: Use private IP connection
        db_password = get_secret('db-password')  # Implement this function
        return f"postgresql://app_user:{db_password}@127.0.0.1:5432/japanese_learning"
    else:
        # Local development
        return os.environ.get('DATABASE_URL', 'postgresql://localhost/japanese_learning_dev')

def run_migrations_online():
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section)
    configuration['sqlalchemy.url'] = get_database_url()
    
    engine = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### Initialize fresh database schema
```bash
# Initialize Alembic (if not already done)
cd /opt/japanese_learning
source venv/bin/activate
alembic init alembic

# Create initial migration for fresh database
alembic revision --autogenerate -m "Initial schema for Japanese learning app"

# Apply migration to Cloud SQL database
alembic upgrade head

# Verify migration status
alembic current
alembic history --verbose
```

## Step 5: Production Flask application setup

### Gunicorn configuration optimized for e2-micro
```python
# gunicorn.conf.py - Optimized for small VM
bind = "unix:/opt/japanese_learning/japanese_learning.sock"
workers = 1  # Single worker for e2-micro
worker_class = "gevent"  # Async for better concurrency
worker_connections = 100
max_requests = 500
max_requests_jitter = 50
timeout = 60
keepalive = 5
preload_app = True

# Process management
user = "ubuntu"  # Replace with your user
group = "www-data"
pidfile = "/opt/japanese_learning/gunicorn.pid"

# Logging
accesslog = "/var/log/gunicorn_access.log"
errorlog = "/var/log/gunicorn_error.log"
loglevel = "info"
```

### Systemd service configuration
```ini
# /etc/systemd/system/japanese-learning.service
[Unit]
Description=Japanese Learning Website Flask Application
After=network.target cloudsql-proxy.service
Requires=cloudsql-proxy.service

[Service]
Type=notify
User=ubuntu
Group=www-data
WorkingDirectory=/opt/japanese_learning
Environment=PATH=/opt/japanese_learning/venv/bin
Environment=FLASK_ENV=production
Environment=GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
ExecStart=/opt/japanese_learning/venv/bin/gunicorn -c gunicorn.conf.py wsgi:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Install and start the service
sudo systemctl daemon-reload
sudo systemctl enable japanese-learning
sudo systemctl start japanese-learning
sudo systemctl status japanese-learning
```

## Step 6: Nginx reverse proxy configuration

### Production Nginx setup
```nginx
# /etc/nginx/sites-available/japanese-learning
server {
    listen 80;
    server_name your-domain.com www.your-domain.com 34.65.139.79;
    
    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options SAMEORIGIN;
    add_header X-XSS-Protection "1; mode=block";
    
    # File upload size limit
    client_max_body_size 16M;
    
    location / {
        proxy_pass http://unix:/opt/japanese_learning/japanese_learning.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # Timeout settings for large file uploads
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Static files
    location /static {
        alias /opt/japanese_learning/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Health check endpoint
    location = /health {
        access_log off;
        return 200 "OK";
        add_header Content-Type text/plain;
    }
}
```

```bash
# Enable the site
sudo ln -s /etc/nginx/sites-available/japanese-learning /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

## Step 7: Cloud Storage for file uploads

### Setup Google Cloud Storage bucket
```bash
# Create storage bucket for file uploads
gsutil mb -p $(gcloud config get-value project) -c STANDARD -l europe-west6 gs://japanese-learning-uploads

# Set bucket permissions for public read (for served images)
gsutil iam ch allUsers:objectViewer gs://japanese-learning-uploads

# Configure CORS for web uploads
cat > cors.json << EOF
[
  {
    "origin": ["https://your-domain.com", "http://34.65.139.79"],
    "method": ["GET", "POST", "PUT"],
    "responseHeader": ["Content-Type"],
    "maxAgeSeconds": 3600
  }
]
EOF

gsutil cors set cors.json gs://japanese-learning-uploads
```

### Secure file upload implementation
```python
# app/utils/file_upload.py
import os
import uuid
from werkzeug.utils import secure_filename
from google.cloud import storage
from PIL import Image
import io

class SecureFileUploader:
    def __init__(self, bucket_name):
        self.storage_client = storage.Client()
        self.bucket_name = bucket_name
        self.allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        self.max_file_size = 10 * 1024 * 1024  # 10MB
    
    def upload_image(self, file):
        """Upload and process image file"""
        if not self.allowed_file(file.filename):
            raise ValueError("File type not allowed")
        
        # Validate and process image
        image = Image.open(file.stream)
        if image.mode in ('RGBA', 'P'):
            image = image.convert('RGB')
        
        # Resize if needed (max 1920x1080)
        image.thumbnail((1920, 1080), Image.Resampling.LANCZOS)
        
        # Generate secure filename
        filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
        
        # Save optimized image
        output = io.BytesIO()
        image.save(output, format='JPEG', optimize=True, quality=85)
        output.seek(0)
        
        # Upload to Cloud Storage
        bucket = self.storage_client.bucket(self.bucket_name)
        blob = bucket.blob(f"uploads/{filename}")
        blob.upload_from_file(output, content_type='image/jpeg')
        
        return f"https://storage.googleapis.com/{self.bucket_name}/uploads/{filename}"
    
    def allowed_file(self, filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
```

## Step 8: SSL/HTTPS setup preparation

### Domain configuration and SSL certificate
```bash
# After configuring your domain DNS to point to 34.65.139.79
# Install SSL certificate with Let's Encrypt
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Test certificate renewal
sudo certbot renew --dry-run

# Setup automatic renewal
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
```

### Enhanced Nginx configuration with SSL
```nginx
# Updated Nginx configuration with SSL
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;
    
    # SSL certificates (managed by Certbot)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    
    # Security headers for production
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options SAMEORIGIN always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Rest of configuration remains the same...
}
```

## Step 9: Monitoring and troubleshooting

### Log management and monitoring
```bash
# Create log directories
sudo mkdir -p /var/log/japanese-learning
sudo chown $USER:adm /var/log/japanese-learning

# Setup log rotation
sudo tee /etc/logrotate.d/japanese-learning > /dev/null <<EOF
/var/log/gunicorn_*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 ubuntu adm
    postrotate
        systemctl reload japanese-learning
    endscript
}
EOF
```

### Health monitoring script
```bash
#!/bin/bash
# /opt/japanese_learning/monitor.sh
set -e

# Check services
services=("japanese-learning" "nginx" "cloudsql-proxy")
for service in "${services[@]}"; do
    if ! systemctl is-active --quiet $service; then
        echo "$(date): $service is down, restarting..."
        sudo systemctl restart $service
    fi
done

# Check disk space
USAGE=$(df /opt/japanese_learning | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $USAGE -gt 80 ]; then
    echo "$(date): Disk usage high: ${USAGE}%"
    find /var/log -name "*.log" -mtime +7 -delete
fi

# Test database connection
cd /opt/japanese_learning
source venv/bin/activate
python3 -c "
from app import db
try:
    db.engine.execute('SELECT 1')
    print('$(date): Database connection OK')
except Exception as e:
    print('$(date): Database connection failed:', e)
"

# Add to crontab: */5 * * * * /opt/japanese_learning/monitor.sh >> /var/log/monitor.log 2>&1
```

## Common troubleshooting scenarios

### Migration issues resolution
```bash
# If Alembic reports version conflicts
# 1. Check current database state
alembic current

# 2. For fresh start (CAUTION: This drops all tables)
python3 -c "
from app import db
db.drop_all()
db.create_all()
"
alembic stamp head

# 3. Common connection issues
# Check Cloud SQL proxy status
sudo systemctl status cloudsql-proxy

# Test database connection manually
psql -h 127.0.0.1 -U app_user -d japanese_learning
```

### Service debugging commands
```bash
# View service logs
journalctl -u japanese-learning -f --since="1 hour ago"
journalctl -u cloudsql-proxy -f --since="1 hour ago"

# Check Nginx error logs
sudo tail -f /var/log/nginx/error.log

# Test Gunicorn manually
cd /opt/japanese_learning
source venv/bin/activate
gunicorn --check-config -c gunicorn.conf.py wsgi:app

# Validate Nginx configuration
sudo nginx -t
```

## Deployment verification

### Complete deployment test
```bash
# 1. Verify all services are running
sudo systemctl status japanese-learning cloudsql-proxy nginx

# 2. Test application response
curl -H "Host: your-domain.com" http://localhost/
curl -H "Host: your-domain.com" http://localhost/health

# 3. Test database connectivity
cd /opt/japanese_learning && source venv/bin/activate
python3 -c "
from app import app, db
with app.app_context():
    result = db.engine.execute('SELECT version()')
    print('PostgreSQL version:', result.fetchone()[0])
"

# 4. Test file upload functionality (create test script)
# 5. Monitor logs for any errors
```

## Production optimization recommendations

**Performance optimization**: Your e2-micro instance is suitable for moderate traffic (100-500 concurrent users). For higher traffic, consider upgrading to e2-small or implementing autoscaling with Instance Groups.

**Cost optimization**: Current setup costs approximately $25-30/month. Enable committed use discounts for 30% savings if traffic patterns are predictable. Consider Cloud Storage lifecycle policies for uploaded files.

**Security enhancements**: Implement rate limiting with Redis for enhanced protection, enable Cloud Security Command Center for threat monitoring, and consider using Identity-Aware Proxy for additional authentication layers.

**Backup strategy**: Cloud SQL automated backups provide 7-day retention by default. Implement application-level backup scripts for uploaded files and configuration. Test restore procedures quarterly.

This comprehensive deployment plan provides a production-ready Flask application with security best practices, proper credential management, and scalable architecture on Google Cloud Platform. The fresh database approach eliminates previous migration conflicts while maintaining all your current application functionality.