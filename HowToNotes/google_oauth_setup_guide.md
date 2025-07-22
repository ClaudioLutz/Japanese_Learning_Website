# Google OAuth Setup Guide for Japanese Learning Website

## Step 1: Create Google Cloud Project

1. **Go to Google Cloud Console:**
   - Visit https://console.cloud.google.com/
   - Sign in with your Google account

2. **Create a new project:**
   - Click "Select a project" dropdown at the top
   - Click "New Project"
   - Project name: `Japanese Learning Website`
   - Click "Create"

## Step 2: Enable Google+ API

1. **Navigate to APIs & Services:**
   - In the left sidebar, click "APIs & Services" > "Library"
   - Search for "Google+ API"
   - Click on "Google+ API" and click "Enable"

2. **Also enable (if not already enabled):**
   - Google Identity and Access Management (IAM) API
   - Google OAuth2 API

## Step 3: Configure OAuth Consent Screen

1. **Go to OAuth consent screen:**
   - Left sidebar: "APIs & Services" > "OAuth consent screen"
   - Choose "External" user type (unless you have a Google Workspace)
   - Click "Create"

2. **Fill out App Information:**
   - App name: `Japanese Learning Website`
   - User support email: Your email address
   - Developer contact information: Your email address
   - Click "Save and Continue"

3. **Scopes (Step 2):**
   - Click "Add or Remove Scopes"
   - Add these scopes:
     - `../auth/userinfo.email`
     - `../auth/userinfo.profile`
     - `openid`
   - Click "Save and Continue"

4. **Test users (Step 3):**
   - Add your email address as a test user
   - Click "Save and Continue"

## Step 4: Create OAuth Credentials

1. **Go to Credentials:**
   - Left sidebar: "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"

2. **Configure OAuth client:**
   - Application type: "Web application"
   - Name: `Japanese Learning Website OAuth`
   
3. **Authorized redirect URIs:**
   Add these URIs (one per line):
   ```
   http://localhost:5000/auth/complete/google-oauth2/
   http://127.0.0.1:5000/auth/complete/google-oauth2/
   ```
   
   For production, also add:
   ```
   https://yourdomain.com/auth/complete/google-oauth2/
   ```

4. **Click "Create"**

## Step 5: Get Your Credentials

1. **Copy the credentials:**
   - Client ID: Copy this long string (ends with `.apps.googleusercontent.com`)
   - Client Secret: Copy this shorter string

2. **Update your .env file:**
   ```
   GOOGLE_CLIENT_ID="your-actual-client-id-here.apps.googleusercontent.com"
   GOOGLE_CLIENT_SECRET="your-actual-client-secret-here"
   ```

## Step 6: Generate Secure Secret Keys

Run these commands to generate secure secret keys:

```bash
python -c "import secrets; print('SECRET_KEY=\"' + secrets.token_urlsafe(32) + '\"')"
python -c "import secrets; print('WTF_CSRF_SECRET_KEY=\"' + secrets.token_urlsafe(32) + '\"')"
```

Update your .env file with these generated keys.

## Step 7: Test OAuth Flow

1. **Start your Flask application:**
   ```bash
   python run.py
   ```

2. **Test the OAuth flow:**
   - Go to http://localhost:5000/login
   - Click "Continue with Google"
   - You should be redirected to Google's OAuth consent screen
   - After authorization, you should be redirected back to your app

## Important Security Notes:

1. **Keep credentials secure:**
   - Never commit real credentials to version control
   - Use environment variables for all sensitive data

2. **Production setup:**
   - Update authorized redirect URIs for your production domain
   - Consider using Google Workspace for internal apps

3. **Testing:**
   - During development, your app will show "This app isn't verified"
   - This is normal for apps in testing mode
   - Click "Advanced" > "Go to [App Name] (unsafe)" to continue testing

## Troubleshooting:

- **"redirect_uri_mismatch" error:** Check that your redirect URI exactly matches what's configured in Google Cloud Console
- **"access_denied" error:** Make sure you're using a test user account that's been added to the OAuth consent screen
- **"invalid_client" error:** Double-check your Client ID and Client Secret in the .env file

## Final .env File Template:

```
# Database Configuration
DATABASE_URL="postgresql://app_user:JapaneseApp2025!@localhost:5432/japanese_learning"

# Google OAuth Configuration
GOOGLE_CLIENT_ID="your-actual-client-id-here.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET="your-actual-client-secret-here"

# Flask Secret Keys (generate new ones!)
SECRET_KEY="your-generated-secret-key-here"
WTF_CSRF_SECRET_KEY="your-generated-csrf-secret-key-here"

# API Keys (keep existing)
OPENAI_API_KEY="your-existing-openai-key"
GOOGLE_AI_API_KEY="your-existing-google-ai-key"
