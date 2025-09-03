# Cloud Run Deployment Guide
## Japanese Learning Website - Production Deployment

This guide provides step-by-step instructions for deploying your Japanese Learning Website to Google Cloud Run with Cloud SQL PostgreSQL.

## 🚀 Quick Deployment

### Prerequisites
- ✅ GCP project configured: `healthy-coil-466105-d7`
- ✅ Docker containers working locally
- ✅ gcloud CLI installed and authenticated
- ✅ Deployment scripts created and ready

### 1. Deploy Infrastructure and Application

```bash
# Execute the complete deployment script
./deploy-to-cloud-run.sh
```

This script will:
- ✅ Enable required GCP APIs (Cloud SQL, Cloud Run, Secret Manager)
- ✅ Create Cloud SQL PostgreSQL instance (`jpl-psql`)
- ✅ Set up database and user
- ✅ Configure service account permissions
- ✅ Store secrets in Secret Manager
- ✅ Deploy your app to Cloud Run
- ✅ Configure Cloud SQL connection via Unix socket

### 2. Migrate Your Data

```bash
# Migrate data from Docker to Cloud SQL
./migrate-to-cloud-sql.sh
```

This will:
- ✅ Create a backup of your local Docker database
- ✅ Transfer data to Cloud SQL via secure proxy
- ✅ Verify migration success

## 📋 What Gets Created

### Cloud SQL Instance
- **Instance ID:** `jpl-psql`
- **Database:** `japanese_learning`
- **User:** `app_user` (password stored in Secret Manager)
- **Region:** `europe-west6` (Zurich)
- **Size:** 1 CPU, 4GB RAM, 20GB SSD

### Cloud Run Service
- **Service:** `japanese-learning-app`
- **Region:** `europe-west6`
- **Memory:** 1GB
- **CPU:** 1 vCPU
- **Max instances:** 10
- **Database connection:** Unix socket via Cloud SQL Proxy

### Secret Manager Secrets
- `db-password`: Database password
- `flask-secret-key`: Flask session encryption key
- `wtf-csrf-secret-key`: CSRF protection key

## 🔧 Configuration Details

### Database Connection
Your app now uses this connection string format:
```
postgresql+psycopg://app_user:PASSWORD@/japanese_learning?host=/cloudsql/healthy-coil-466105-d7:europe-west6:jpl-psql
```

### Health Check Endpoint
Added `/health` endpoint for Cloud Run health monitoring:
- ✅ Tests database connectivity
- ✅ Returns JSON status response

### Environment Variables
- `DATABASE_URL`: Cloud SQL connection string
- `SECRET_KEY`: From Secret Manager
- `WTF_CSRF_SECRET_KEY`: From Secret Manager  
- `FLASK_ENV`: production

## 🚦 Post-Deployment Steps

### 1. Verify Deployment
After running the deployment script, you'll get a service URL like:
```
https://japanese-learning-app-[hash]-europe-west6.a.run.app
```

Test the deployment:
- Visit the URL to see your app
- Check `/health` endpoint for status
- Test user registration/login
- Verify lessons are accessible

### 2. Update OAuth Configuration
Update your Google OAuth settings:
1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Edit your OAuth 2.0 client ID
3. Add your new Cloud Run URL to authorized redirect URIs:
   - `https://your-service-url.a.run.app/auth/complete/google-oauth2/`

### 3. Update Payment Webhooks
Update PostFinance Checkout webhook URLs:
1. Login to PostFinance merchant portal
2. Update webhook endpoints to your new domain:
   - Success: `https://your-service-url.a.run.app/payment/success`
   - Failed: `https://your-service-url.a.run.app/payment/failed`

## 🌐 Optional: Custom Domain Setup

### 1. Map Custom Domain
```bash
gcloud run domain-mappings create \
    --service japanese-learning-app \
    --domain your-domain.com \
    --region europe-west6
```

### 2. Configure DNS
Add the DNS records provided by Cloud Run to your domain registrar.

### 3. Update OAuth and Webhooks
Repeat steps 2 and 3 above with your custom domain.

## 📊 Monitoring and Maintenance

### View Logs
```bash
gcloud run logs tail japanese-learning-app --region europe-west6
```

### Monitor Resources
```bash
# Service status
gcloud run services describe japanese-learning-app --region europe-west6

# Cloud SQL status  
gcloud sql instances describe jpl-psql
```

### Scale Service
```bash
gcloud run services update japanese-learning-app \
    --region europe-west6 \
    --memory 2Gi \
    --cpu 2 \
    --max-instances 20
```

## 💾 Database Management

### Connect to Cloud SQL
```bash
gcloud sql connect jpl-psql --user=app_user
```

### Backup Database
```bash
gcloud sql export sql jpl-psql gs://your-bucket/backup-$(date +%Y%m%d).sql \
    --database=japanese_learning
```

## 🔒 Security Best Practices

### Service Account Permissions
The deployment script creates minimal required permissions:
- `roles/cloudsql.client` for database access
- `roles/secretmanager.secretAccessor` for secrets

### Network Security
- Cloud Run service uses HTTPS only
- Database accessible only via Unix socket
- No public IP on Cloud SQL instance

## 🚨 Troubleshooting

### Common Issues

**Database Connection Failed**
```bash
# Check service account permissions
gcloud projects get-iam-policy healthy-coil-466105-d7

# Verify Cloud SQL instance
gcloud sql instances describe jpl-psql
```

**Secret Access Denied**
```bash
# Check secret permissions
gcloud secrets get-iam-policy db-password
```

**Service Not Starting**
```bash
# Check logs
gcloud run logs tail japanese-learning-app --region europe-west6

# Check service configuration
gcloud run services describe japanese-learning-app --region europe-west6
```

## 💰 Cost Estimation

### Expected Monthly Costs (EUR)
- **Cloud SQL** (1 CPU, 4GB): ~€25-35/month
- **Cloud Run** (low traffic): ~€5-15/month  
- **Secret Manager**: ~€1/month
- **Data transfer**: ~€2-5/month

**Total estimated**: €33-56/month for production workload

## 📝 Next Steps

1. ✅ **Deploy**: Run `./deploy-to-cloud-run.sh`
2. ✅ **Migrate**: Run `./migrate-to-cloud-sql.sh`  
3. ✅ **Test**: Verify all functionality works
4. ✅ **Configure**: Update OAuth and payment settings
5. ⚠️ **Monitor**: Set up alerting and monitoring
6. ⚠️ **Backup**: Schedule regular database backups

## 📞 Support

If you encounter issues:
1. Check the logs: `gcloud run logs tail`
2. Verify service status: `gcloud run services describe`
3. Test database connectivity via health endpoint
4. Review Cloud SQL connection configuration

---

🎉 **Congratulations!** Your Japanese Learning Website is now running in production on Google Cloud Platform with enterprise-grade reliability, security, and scalability.
