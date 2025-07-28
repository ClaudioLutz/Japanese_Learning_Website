# Complete Google OAuth Setup Guide for Japanese Learning Website

## Current Issue
You're getting a `KeyError: 'google-oauth2'` error because your Google OAuth credentials are not properly configured.

## Step-by-Step Setup Process

### 1. Google Cloud Console Setup

#### A. Create/Select Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select an existing project or create a new one
3. Note your project ID for reference

#### B. Enable Required APIs
1. Navigate to **"APIs & Services"** > **"Library"**
2. Search for and enable these APIs:
   - **Google+ API** (for social login)
   - **People API** (recommended for profile access)

#### C. Configure OAuth Consent Screen
1. Go to **"APIs & Services"** > **"OAuth consent screen"**
2. Select **"External"** user type (for testing)
3. Fill in required fields:
   - App name: "Japanese Learning Website"
   - User support email: Your email
   - Developer contact information: Your email
4. **Add scopes**: 
   - `../auth/userinfo.email`
   - `../auth/userinfo.profile`
   - `openid`
5. **Add test users** (your email and any other testing emails)
6. Save and continue

#### D. Create OAuth 2.0 Credentials
1. Go to **"APIs & Services"** > **"Credentials"**
2. Click **"+ CREATE CREDENTIALS"** > **"OAuth 2.0 Client IDs"**
3. Select **"Web application"**
4. Configure:
   - **Name**: "Japanese Learning Website OAuth"
   - **Authorized JavaScript origins**:
     - `http://localhost:5000`
     - `http://127.0.0.1:5000`
   - **Authorized redirect URIs**:
     - `http://localhost:5000/auth/complete/google-oauth2/`
     - `http://127.0.0.1:5000/auth/complete/google-oauth2/`
5. Click **"Create"**
6. **IMPORTANT**: Copy the Client ID and Client Secret immediately

### 2. Update Your Environment File

Replace the placeholder values in your `.env` file:

```bash
# Replace these with your actual values from Google Console
GOOGLE_CLIENT_ID="your-actual-client-id-from-google-console"
GOOGLE_CLIENT_SECRET="your-actual-client-secret-from-google-console"
```

### 3. Current Configuration Status

✅ **Already Fixed**: 
- Added `SOCIAL_AUTH_AUTHENTICATION_BACKENDS` to app configuration
- Proper pipeline configuration
- Social auth blueprint registration

❌ **Still Need**:
- Real Google OAuth credentials in `.env` file

### 4. Testing Localhost Development

**Yes, this works perfectly for localhost development!**

Your current setup supports:
- `http://localhost:5000` - Your Flask dev server
- `http://127.0.0.1:5000` - Alternative localhost address

### 5. Testing the Setup

After updating your credentials:

1. **Restart your Flask server**:
   ```bash
   python run.py
   ```

2. **Test the OAuth flow**:
   - Navigate to `http://localhost:5000`
   - Click on Google login button
   - Should redirect to Google's OAuth consent screen
   - After authorization, should redirect back to your app

### 6. Common Development Issues & Solutions

#### Issue: "Error 400: redirect_uri_mismatch"
**Solution**: Ensure your redirect URIs in Google Console exactly match:
- `http://localhost:5000/auth/complete/google-oauth2/`

#### Issue: "This app isn't verified"
**Solution**: During development, click "Advanced" → "Go to [App Name] (unsafe)"

#### Issue: "Access blocked: This app's request is invalid"
**Solution**: Check that your OAuth consent screen is properly configured

### 7. Security Notes for Development

- Your current `.env` credentials are for development only
- For production, you'll need:
  - Production domain in OAuth settings
  - Proper HTTPS redirect URIs
  - App verification if serving external users

### 8. Next Steps After Setup

1. **Update credentials in `.env`**
2. **Restart Flask server**
3. **Test login flow**
4. **Check console logs for any remaining errors**

### 9. Troubleshooting Commands

If you encounter issues, check:

```bash
# Check if environment variables are loaded
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('Client ID:', os.environ.get('GOOGLE_CLIENT_ID', 'NOT SET'))"

# Check Flask configuration
python -c "from app import create_app; app = create_app(); print('OAuth Key:', app.config.get('SOCIAL_AUTH_GOOGLE_OAUTH2_KEY', 'NOT SET'))"
```

## Current Project Structure

Your OAuth implementation includes:
- ✅ Custom user creation pipeline (`app/social_auth_config.py`)
- ✅ Proper Flask-Login integration
- ✅ User model with OAuth support
- ✅ Social auth blueprints registration

**The only missing piece is the actual Google OAuth credentials!**
