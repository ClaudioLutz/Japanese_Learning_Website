# Japanese Learning Website - Data Migration Script (PowerShell)
$ErrorActionPreference = "Stop"

Write-Host "Japanese Learning Website - Data Migration Script"
Write-Host "===================================================="

# Configuration
$PROJECT_ID = "jpl-website-bill-20251130"
$REGION = "europe-west6"
$INSTANCE = "jpl-psql"
$DB = "japanese_learning"
$DB_USER = "app_user"
$BUCKET_NAME = "${PROJECT_ID}-sql-dump"
$DUMP_FILE = "japanese_learning_dump.sql"

# Local Config
$LOCAL_HOST = "localhost"
$LOCAL_PORT = "5432"
$LOCAL_USER = "app_user"
$LOCAL_DB = "japanese_learning"
$LOCAL_DB_PASS = "JapaneseApp2025!"

# Check Docker
Write-Host "Checking Docker..."
if (!(docker ps | Select-String "postgres")) {
    Write-Warning "Docker PostgreSQL container might not be running. Attempting to dump anyway (assuming localhost port 5432 is accessible)..."
}

# Check for existing dump
$EXISTING_DUMP = "database_dump/japanese_learning_dump.sql"
if (Test-Path $EXISTING_DUMP) {
    Write-Host "Found existing database dump: $EXISTING_DUMP"
    Copy-Item $EXISTING_DUMP $DUMP_FILE
} else {
    # Dump Local DB
    Write-Host "Dumping local database..."
    $env:PGPASSWORD = $LOCAL_DB_PASS
    try {
        pg_dump -h $LOCAL_HOST -p $LOCAL_PORT -U $LOCAL_USER -d $LOCAL_DB --no-owner --no-privileges --clean --if-exists -f $DUMP_FILE
        if (!(Test-Path $DUMP_FILE)) {
            throw "Dump file not found after pg_dump."
        }
        Write-Host "Database dump created: $DUMP_FILE"
    }
    catch {
        Write-Error "Failed to dump database and no existing dump found: $_"
        exit 1
    }
}

# Create GCS Bucket if not exists
Write-Host "Checking GCS bucket..."
$bucketExists = $false
try {
    gcloud storage buckets describe gs://$BUCKET_NAME --format="value(name)" --quiet 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $bucketExists = $true
    }
} catch {
    # Ignore error
}

if (!$bucketExists) {
    Write-Host "Creating bucket gs://$BUCKET_NAME..."
    try {
        gcloud storage buckets create gs://$BUCKET_NAME --location=$REGION --project=$PROJECT_ID --quiet
    } catch {
        Write-Error "Failed to create bucket: $_"
        exit 1
    }
} else {
    Write-Host "Bucket gs://$BUCKET_NAME already exists."
}

# Upload Dump
Write-Host "Uploading dump to GCS..."
gcloud storage cp $DUMP_FILE gs://$BUCKET_NAME/

# Grant Service Account Permissions
Write-Host "Granting permissions to Cloud SQL Service Account..."
$SA_EMAIL = gcloud sql instances describe $INSTANCE --project=$PROJECT_ID --format="value(serviceAccountEmailAddress)"
if ($SA_EMAIL) {
    gcloud storage buckets add-iam-policy-binding gs://$BUCKET_NAME --member="serviceAccount:$SA_EMAIL" --role="roles/storage.objectViewer" --project=$PROJECT_ID --quiet
} else {
    Write-Warning "Could not retrieve Cloud SQL Service Account email."
}

# Import to Cloud SQL
Write-Host "Importing to Cloud SQL..."
gcloud sql import sql $INSTANCE gs://$BUCKET_NAME/$DUMP_FILE --database=$DB --project=$PROJECT_ID --user=$DB_USER --quiet

Write-Host "Migration completed successfully!"
Write-Host "You can verify the data by connecting to the Cloud SQL instance or checking the application."

# Cleanup
# Remove-Item $DUMP_FILE
