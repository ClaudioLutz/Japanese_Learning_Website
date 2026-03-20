# Japanese Learning Website - Project Guide

## Overview
Flask-based Japanese language learning platform with lesson/course management, user auth, AI content generation, payment integration (PostFinance), and Google Cloud deployment.

## Tech Stack
- **Backend**: Flask 2.0+, SQLAlchemy, Flask-Login, Flask-Migrate, Flask-WTF
- **Database**: PostgreSQL 15 (Cloud SQL in prod, Docker locally)
- **Auth**: Flask-Login (local) + Google OAuth2 (social-auth, Authlib)
- **AI**: OpenAI GPT + Google Gemini for lesson/quiz generation
- **Payments**: PostFinance Checkout (CHF currency)
- **Storage**: Google Cloud Storage (GCS) for media, local fallback
- **Deployment**: Google Cloud Run, Docker, Gunicorn
- **Frontend**: Jinja2 templates, no JS framework

## Project Structure
```
app/
  __init__.py          # App factory (create_app), extensions init
  models.py            # All SQLAlchemy models (~643 lines)
  routes.py            # All routes + API endpoints (~3700 lines)
  utils.py             # FileUploadHandler, URL utils
  forms.py             # WTForms (Registration, Login, CSRF)
  gcs_utils.py         # Google Cloud Storage helpers
  ai_services.py       # AI content generation (OpenAI/Gemini)
  social_auth_config.py # Google OAuth pipeline
  services/
    payment_service.py      # PostFinance integration
    mock_payment_service.py # Dev payment mock
  templates/           # Jinja2 templates
  static/              # CSS, images, uploads/
run.py                 # Entry point
requirements.txt       # Python deps
Dockerfile.cloudrun    # Production container
docker-compose.yml     # Local dev (Flask + PostgreSQL 15)
deploy-to-cloud-run.sh # GCP deployment automation
entrypoint-cloud-run.sh # Cloud Run startup (DB wait + Gunicorn)
```

## Key Commands
```bash
# Local dev
docker-compose up
# Or: pip install -r requirements.txt && python run.py

# Deploy to Cloud Run
./deploy-to-cloud-run.sh

# Migrate data to Cloud SQL
./migrate-to-cloud-sql.sh
```

## Database Models (Key Entities)
- **User** - auth, subscription_level (free/premium), is_admin
- **Lesson** - content unit with pricing, prerequisites, pages, access control
- **Course** - groups lessons, purchasable
- **LessonContent** - content items (kana, kanji, vocab, grammar, text, media, quiz)
- **LessonPage** - page metadata within lessons
- **Kana/Kanji/Vocabulary/Grammar** - Japanese language reference data
- **UserLessonProgress** - tracks completion, time spent, content-level progress (JSON)
- **QuizQuestion/QuizOption/UserQuizAnswer** - quiz system
- **LessonPurchase/CoursePurchase/PaymentTransaction** - payment tracking

## Access Control Pattern
Lesson access: guest (free+allow_guest) > free (check prerequisites) > paid (check purchase or course ownership) > premium (subscription check). Decorators: `@login_required`, `@admin_required`, `@premium_required`.

## Environment Variables (Required)
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY`, `WTF_CSRF_SECRET_KEY` - Flask security keys
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` - OAuth
- `OPENAI_API_KEY`, `GOOGLE_AI_API_KEY` - AI services
- `POSTFINANCE_SPACE_ID`, `POSTFINANCE_USER_ID`, `POSTFINANCE_API_SECRET` - Payments
- `GCS_BUCKET_NAME` - Cloud Storage bucket
- `PAYMENT_SUCCESS_URL`, `PAYMENT_FAILURE_URL` - Payment redirects

## GCP Deployment (OLD project deleted - needs new setup)
- Old Project: jpl-website-bill-20251130 (DELETED)
- Region: europe-west6 (Zurich)
- Cloud SQL instance: jpl-psql
- Cloud Run service: japanese-learning-app
- Port: 8080, 2 Gunicorn workers, 300s timeout

## Important Patterns
- **GCS-aware URLs**: Models resolve file URLs via GCS if bucket configured, else local static
- **AI content approval**: AI-generated items have `generated_by_ai` flag, admin approval workflow
- **Payment mock**: MockPaymentService in dev, real PostFinance in prod
- **App factory**: `create_app()` in `app/__init__.py` with blueprint registration
- **File uploads**: UUID filenames, MIME validation, image resizing (Pillow), max 100MB
- **Lesson type auto-sync**: SQLAlchemy event listener sets lesson_type based on price

## No Test Suite
No automated tests exist. Debug routes available via `debug_routes.py`.

## Documentation
Guides in `HowToNotes/` and `Documentation/` covering OAuth, deployment, monetization, quiz generation, and local DB setup.
