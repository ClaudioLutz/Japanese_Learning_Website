#!/bin/bash
set -e

echo "🚀 Japanese Learning Website - Cloud Run Deployment Script"
echo "=========================================================="

# Configuration variables
PROJECT_ID="healthy-coil-466105-d7"
REGION="europe-west6"
INSTANCE="jpl-psql"
DB="japanese_learning"
DB_USER="app_user"
SERVICE="japanese-learning-app"

# Generate a strong password (you should replace this with your preferred password)
DB_PASS=$(openssl rand -base64 24 | tr -d "=+/" | cut -c1-24)

echo "Configuration:"
echo "- Project ID: $PROJECT_ID"
echo "- Region: $REGION"
echo "- Cloud SQL Instance: $INSTANCE"
echo "- Database: $DB"
echo "- Database User: $DB_USER"
echo "- Cloud Run Service: $SERVICE"
echo "- Generated DB Password: $DB_PASS"
echo ""

# Set active project
echo "📋 Setting active project..."
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "🔧 Enabling required APIs..."
gcloud services enable sqladmin.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com

# Create Cloud SQL instance (or use existing)
echo "🗄️ Checking Cloud SQL PostgreSQL instance..."
if gcloud sql instances describe $INSTANCE --quiet >/dev/null 2>&1; then
    echo "✅ Cloud SQL instance '$INSTANCE' already exists. Using existing instance."
else
    echo "Creating new Cloud SQL PostgreSQL instance..."
    gcloud sql instances create $INSTANCE \
      --database-version=POSTGRES_15 \
      --cpu=1 \
      --memory=4GiB \
      --region=$REGION \
      --storage-type=SSD \
      --storage-size=20GB \
      --backup-start-time=02:00 \
      --deletion-protection
    echo "✅ Cloud SQL instance created successfully!"
fi

# Create database and user (or use existing)
echo "🔐 Setting up database and user..."

# Check if database exists
if gcloud sql databases describe $DB --instance=$INSTANCE --quiet >/dev/null 2>&1; then
    echo "✅ Database '$DB' already exists."
else
    echo "Creating database '$DB'..."
    gcloud sql databases create $DB --instance=$INSTANCE
    echo "✅ Database created successfully!"
fi

# Check if user exists (this will show an error if user doesn't exist, which is expected)
if gcloud sql users describe $DB_USER --instance=$INSTANCE --quiet >/dev/null 2>&1; then
    echo "✅ User '$DB_USER' already exists. You may want to reset the password if needed."
    echo "⚠️  Using existing user. If you need to reset password, run:"
    echo "   gcloud sql users set-password $DB_USER --instance=$INSTANCE --password=NEW_PASSWORD"
else
    echo "Creating user '$DB_USER'..."
    gcloud sql users create $DB_USER --instance=$INSTANCE --password=$DB_PASS
    echo "✅ User created successfully!"
fi

echo "✅ Database setup completed!"

# Get the default Cloud Run service account
SERVICE_ACCOUNT=$(gcloud iam service-accounts list --filter="displayName~'Compute Engine default service account'" --format="value(email)")

# Grant Cloud SQL Client role to the service account
echo "🔑 Granting Cloud SQL Client role to service account..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/cloudsql.client"

# Create secrets in Secret Manager
echo "🔒 Setting up secrets in Secret Manager..."
gcloud services enable secretmanager.googleapis.com

# Handle database password secret
if gcloud secrets describe db-password --quiet >/dev/null 2>&1; then
    echo "✅ Secret 'db-password' already exists."
    echo "⚠️  Using existing secret. If you need to update it, run:"
    echo "   echo -n 'NEW_PASSWORD' | gcloud secrets versions add db-password --data-file=-"
else
    echo "Creating database password secret..."
    echo -n "$DB_PASS" | gcloud secrets create db-password --data-file=-
    echo "✅ Database password secret created!"
fi

# Grant secret accessor role to Cloud Run service account (idempotent operation)
gcloud secrets add-iam-policy-binding db-password \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor" \
  --quiet 2>/dev/null || echo "✅ IAM binding already exists for db-password"

# Generate SECRET_KEY and WTF_CSRF_SECRET_KEY
SECRET_KEY=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
WTF_CSRF_SECRET_KEY=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)

# Handle Flask secret key
if gcloud secrets describe flask-secret-key --quiet >/dev/null 2>&1; then
    echo "✅ Secret 'flask-secret-key' already exists."
else
    echo "Creating Flask secret key..."
    echo -n "$SECRET_KEY" | gcloud secrets create flask-secret-key --data-file=-
    echo "✅ Flask secret key created!"
fi

# Handle WTF CSRF secret key
if gcloud secrets describe wtf-csrf-secret-key --quiet >/dev/null 2>&1; then
    echo "✅ Secret 'wtf-csrf-secret-key' already exists."
else
    echo "Creating WTF CSRF secret key..."
    echo -n "$WTF_CSRF_SECRET_KEY" | gcloud secrets create wtf-csrf-secret-key --data-file=-
    echo "✅ WTF CSRF secret key created!"
fi

# Grant secret accessor roles (idempotent operations)
gcloud secrets add-iam-policy-binding flask-secret-key \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor" \
  --quiet 2>/dev/null || echo "✅ IAM binding already exists for flask-secret-key"

gcloud secrets add-iam-policy-binding wtf-csrf-secret-key \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor" \
  --quiet 2>/dev/null || echo "✅ IAM binding already exists for wtf-csrf-secret-key"

echo "✅ Secrets setup completed!"

# Create environment variables for deployment  
DATABASE_URL="postgresql+psycopg://${DB_USER}:${DB_PASS}@/${DB}?host=/cloudsql/${PROJECT_ID}:${REGION}:${INSTANCE}"

echo "🚀 Building and deploying Docker container to Cloud Run..."

# Create Artifact Registry repository
echo "📦 Setting up Artifact Registry..."
REPO_NAME="app-images"
gcloud artifacts repositories create $REPO_NAME \
    --repository-format=docker \
    --location=$REGION \
    --description="Japanese Learning Website images" || echo "✅ Repository already exists"

# Build and push Docker image
IMAGE_URI="$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/$SERVICE:latest"

echo "🔑 Configuring Docker authentication for Artifact Registry..."
gcloud auth configure-docker $REGION-docker.pkg.dev --quiet

echo "🔨 Building Docker image..."
docker build -f Dockerfile.cloudrun -t $IMAGE_URI .

echo "📤 Pushing image to Artifact Registry..."
docker push $IMAGE_URI

echo "🚀 Deploying to Cloud Run..."
gcloud run deploy $SERVICE \
  --image $IMAGE_URI \
  --region $REGION \
  --allow-unauthenticated \
  --add-cloudsql-instances "$PROJECT_ID:$REGION:$INSTANCE" \
  --set-env-vars "DATABASE_URL=$DATABASE_URL" \
  --set-secrets "SECRET_KEY=flask-secret-key:latest" \
  --set-secrets "WTF_CSRF_SECRET_KEY=wtf-csrf-secret-key:latest" \
  --set-env-vars "FLASK_ENV=production" \
  --memory=2Gi \
  --cpu=2 \
  --max-instances=10 \
  --timeout=900 \
  --port=8080 \
  --execution-environment=gen2

echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "📋 Important Information:"
echo "========================="
echo "Project ID: $PROJECT_ID"
echo "Cloud SQL Instance: $INSTANCE"
echo "Database: $DB"
echo "Database User: $DB_USER"
echo "Database Password: $DB_PASS"
echo "Service Account: $SERVICE_ACCOUNT"
echo ""
echo "Your service URL:"
gcloud run services describe $SERVICE --region $REGION --format='value(status.url)'
echo ""
echo "⚠️  IMPORTANT: Save the database password somewhere secure!"
echo "   Database Password: $DB_PASS"
echo ""
echo "🔄 Next steps:"
echo "1. Run the data migration script: ./migrate-to-cloud-sql.sh"
echo "2. Test your deployment"
echo "3. Configure custom domain (optional)"
echo "4. Update OAuth redirect URIs to your new domain"
