# Cloud Run Deployment Script (PowerShell)
$ErrorActionPreference = "Continue"

Write-Host "Japanese Learning Website - Cloud Run Deployment Script"
Write-Host "=========================================================="

# Configuration variables
$PROJECT_ID = "jpl-website-bill-20251130"
$REGION = "europe-west6"
$INSTANCE = "jpl-psql"
$DB = "japanese_learning"
$DB_USER = "app_user"
$SERVICE = "japanese-learning-app"

# Check for existing secret first
$secretExists = gcloud secrets describe db-password --quiet 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "Fetching existing database password from Secret Manager..."
    $DB_PASS = gcloud secrets versions access latest --secret="db-password"
} else {
    # Generate a strong password
    $DB_PASS = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 24 | ForEach-Object { [char]$_ })
}

Write-Host "Configuration:"
Write-Host "- Project ID: $PROJECT_ID"
Write-Host "- Region: $REGION"
Write-Host "- Cloud SQL Instance: $INSTANCE"
Write-Host "- Database: $DB"
Write-Host "- Database User: $DB_USER"
Write-Host "- Cloud Run Service: $SERVICE"
Write-Host "- Generated DB Password: $DB_PASS"
Write-Host ""

# Set active project
Write-Host "Setting active project..."
gcloud config set project $PROJECT_ID --quiet

# Enable required APIs
Write-Host "Enabling required APIs..."
gcloud services enable sqladmin.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable compute.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# Create Cloud SQL instance (or use existing)
Write-Host "Checking Cloud SQL PostgreSQL instance..."
$instanceExists = gcloud sql instances describe $INSTANCE --quiet 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "Cloud SQL instance '$INSTANCE' already exists. Using existing instance."
} else {
    Write-Host "Creating new Cloud SQL PostgreSQL instance..."
    gcloud sql instances create $INSTANCE `
      --database-version=POSTGRES_15 `
      --cpu=1 `
      --memory=4GiB `
      --region=$REGION `
      --storage-type=SSD `
      --storage-size=20GB `
      --backup-start-time=02:00 `
      --deletion-protection `
      --quiet
    Write-Host "Cloud SQL instance created successfully!"
}

# Create database and user (or use existing)
Write-Host "Setting up database and user..."

# Check if database exists
$dbExists = gcloud sql databases describe $DB --instance=$INSTANCE --quiet 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "Database '$DB' already exists."
} else {
    Write-Host "Creating database '$DB'..."
    gcloud sql databases create $DB --instance=$INSTANCE --quiet
    Write-Host "Database created successfully!"
}

# Check if user exists
$userExists = gcloud sql users describe $DB_USER --instance=$INSTANCE --quiet 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "User '$DB_USER' already exists. You may want to reset the password if needed."
    Write-Host "Using existing user. If you need to reset password, run:"
    Write-Host "   gcloud sql users set-password $DB_USER --instance=$INSTANCE --password=NEW_PASSWORD"
} else {
    Write-Host "Creating user '$DB_USER'..."
    gcloud sql users create $DB_USER --instance=$INSTANCE --password=$DB_PASS --quiet
    Write-Host "User created successfully!"
}

Write-Host "Database setup completed!"

# Get the default Cloud Run service account or create a new one
$SERVICE_ACCOUNT = gcloud iam service-accounts list --filter="displayName~'Compute Engine default service account'" --format="value(email)"

if (-not $SERVICE_ACCOUNT) {
    Write-Host "Default Compute Engine service account not found. Creating a dedicated service account..."
    $SA_NAME = "jpl-app-sa"
    $SA_EMAIL = "$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com"
    
    $saExists = gcloud iam service-accounts describe $SA_EMAIL --quiet 2>$null
    if ($LASTEXITCODE -ne 0) {
        gcloud iam service-accounts create $SA_NAME --display-name="Japanese Learning App Service Account" --quiet
    }
    $SERVICE_ACCOUNT = $SA_EMAIL
}
Write-Host "Service Account: $SERVICE_ACCOUNT"

# Grant Cloud SQL Client role to the service account
Write-Host "Granting Cloud SQL Client role to service account..."
gcloud projects add-iam-policy-binding $PROJECT_ID `
  --member="serviceAccount:$SERVICE_ACCOUNT" `
  --role="roles/cloudsql.client"

# Grant Storage Admin role to service account
Write-Host "Granting Storage Admin role to service account..."
gcloud projects add-iam-policy-binding $PROJECT_ID `
  --member="serviceAccount:$SERVICE_ACCOUNT" `
  --role="roles/storage.admin"

# Create secrets in Secret Manager
Write-Host "Setting up secrets in Secret Manager..."

# Handle database password secret
$secretExists = gcloud secrets describe db-password --quiet 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "Secret 'db-password' already exists."
    Write-Host "Using existing secret. If you need to update it, run:"
    Write-Host "   echo -n 'NEW_PASSWORD' | gcloud secrets versions add db-password --data-file=-"
} else {
    Write-Host "Creating database password secret..."
    $DB_PASS | gcloud secrets create db-password --data-file=-
    Write-Host "Database password secret created!"
}

# Grant secret accessor role to Cloud Run service account
gcloud secrets add-iam-policy-binding db-password `
  --member="serviceAccount:$SERVICE_ACCOUNT" `
  --role="roles/secretmanager.secretAccessor" `
  --quiet 2>$null
if ($LASTEXITCODE -ne 0) { Write-Host "IAM binding already exists for db-password" }

# Generate SECRET_KEY and WTF_CSRF_SECRET_KEY
$SECRET_KEY = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object { [char]$_ })
$WTF_CSRF_SECRET_KEY = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object { [char]$_ })

# Handle Flask secret key
$flaskSecretExists = gcloud secrets describe flask-secret-key --quiet 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "Secret 'flask-secret-key' already exists."
} else {
    Write-Host "Creating Flask secret key..."
    $SECRET_KEY | gcloud secrets create flask-secret-key --data-file=-
    Write-Host "Flask secret key created!"
}

# Handle WTF CSRF secret key
$csrfSecretExists = gcloud secrets describe wtf-csrf-secret-key --quiet 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "Secret 'wtf-csrf-secret-key' already exists."
} else {
    Write-Host "Creating WTF CSRF secret key..."
    $WTF_CSRF_SECRET_KEY | gcloud secrets create wtf-csrf-secret-key --data-file=-
    Write-Host "WTF CSRF secret key created!"
}

# Grant secret accessor roles
gcloud secrets add-iam-policy-binding flask-secret-key `
  --member="serviceAccount:$SERVICE_ACCOUNT" `
  --role="roles/secretmanager.secretAccessor" `
  --quiet 2>$null

gcloud secrets add-iam-policy-binding wtf-csrf-secret-key `
  --member="serviceAccount:$SERVICE_ACCOUNT" `
  --role="roles/secretmanager.secretAccessor" `
  --quiet 2>$null

Write-Host "Secrets setup completed!"

# Create environment variables for deployment  
$DATABASE_URL = "postgresql+psycopg://${DB_USER}:${DB_PASS}@/${DB}?host=/cloudsql/${PROJECT_ID}:${REGION}:${INSTANCE}"

Write-Host "Building and deploying Docker container to Cloud Run..."

# Create Artifact Registry repository
Write-Host "Setting up Artifact Registry..."
$REPO_NAME = "app-images"
# Create Artifact Registry repository (if it doesn't exist)
Write-Host "Setting up Artifact Registry..."
$REPO_NAME = "app-images"
$repoExists = gcloud artifacts repositories describe $REPO_NAME --location=$REGION --quiet 2>$null
if ($LASTEXITCODE -ne 0) {
    gcloud artifacts repositories create $REPO_NAME `
        --repository-format=docker `
        --location=$REGION `
        --description="Docker repository for Japanese Learning App"
}

# Build the container image
Write-Host "Building container image..."
$IMAGE_TAG = "$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/$SERVICE"
gcloud builds submit --tag $IMAGE_TAG . --quiet

# Deploy to Cloud Run
Write-Host "Deploying to Cloud Run..."
gcloud run deploy $SERVICE `
  --image $IMAGE_TAG `
  --region $REGION `
  --allow-unauthenticated `
  --service-account $SERVICE_ACCOUNT `
  --quiet `
  --add-cloudsql-instances "${PROJECT_ID}:${REGION}:${INSTANCE}" `
  --set-env-vars "DATABASE_URL=postgresql+psycopg2://${DB_USER}:${DB_PASS}@/${DB}?host=/cloudsql/${PROJECT_ID}:${REGION}:${INSTANCE}" `
  --set-secrets "SECRET_KEY=flask-secret-key:latest" `
  --set-secrets "WTF_CSRF_SECRET_KEY=wtf-csrf-secret-key:latest" `
  --set-env-vars "FLASK_ENV=production" `
  --set-env-vars "GCS_BUCKET_NAME=jpl-website-assets-${PROJECT_ID}" `
  --memory=2Gi `
  --cpu=2 `
  --max-instances=10 `
  --timeout=900 `
  --port=8080 `
  --execution-environment=gen2

Write-Host ""
Write-Host "Deployment completed successfully!"
Write-Host ""
Write-Host "Important Information:"
Write-Host "========================="
Write-Host "Project ID: $PROJECT_ID"
Write-Host "Cloud SQL Instance: $INSTANCE"
Write-Host "Database: $DB"
Write-Host "Database User: $DB_USER"
Write-Host "Database Password: $DB_PASS"
Write-Host "Service Account: $SERVICE_ACCOUNT"
Write-Host ""
Write-Host "Your service URL:"
gcloud run services describe $SERVICE --region $REGION --format="value(status.url)"
Write-Host ""
Write-Host "IMPORTANT: Save the database password somewhere secure!"
Write-Host "   Database Password: $DB_PASS"
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Run the data migration script: ./migrate-to-cloud-sql.sh"
Write-Host "2. Test your deployment"
Write-Host "3. Configure custom domain (optional)"
Write-Host "4. Update OAuth redirect URIs to your new domain"
