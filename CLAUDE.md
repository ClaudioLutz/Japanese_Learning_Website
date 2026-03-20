# Japanese Learning Website — Projektanleitung

## Überblick
Flask-basierte Japanisch-Lernplattform mit Lektions-/Kursverwaltung, Benutzerauthentifizierung, KI-generiertem Inhalt (OpenAI/Gemini), PostFinance-Zahlungsintegration und Google Cloud Deployment.

## Tech-Stack
- **Backend**: Flask 2.0+, SQLAlchemy, Flask-Login, Flask-Migrate, Flask-WTF
- **Datenbank**: PostgreSQL 15 (Docker lokal, Cloud SQL in Produktion)
- **Auth**: Flask-Login (lokal) + Google OAuth2 (social-auth, Authlib)
- **KI**: OpenAI GPT + Google Gemini für Lektions-/Quiz-Generierung
- **Zahlungen**: PostFinance Checkout (CHF) — **noch nicht produktiv, MockPayment aktiv**
- **Storage**: Google Cloud Storage (GCS) für Medien, lokaler Fallback
- **Deployment**: Google Cloud Run, Docker, Gunicorn
- **Frontend**: Jinja2 Templates, kein JS-Framework

## Projektstruktur
```
app/
  __init__.py          # App Factory (create_app), Extensions
  models.py            # SQLAlchemy Models (~643 Zeilen)
  routes.py            # Alle Routen + API-Endpoints (~3'722 Zeilen)
  utils.py             # FileUploadHandler, URL-Utils (~307 Zeilen)
  forms.py             # WTForms (Registration, Login, CSRF)
  gcs_utils.py         # Google Cloud Storage Helpers
  ai_services.py       # KI-Content-Generierung (OpenAI/Gemini)
  social_auth_config.py # Google OAuth Pipeline
  services/
    payment_service.py      # PostFinance Integration
    mock_payment_service.py # Dev Payment Mock
    payment_factory.py      # Wählt Mock/Real basierend auf Umgebung
  templates/           # Jinja2 Templates
  static/              # CSS, Bilder, Uploads
run.py                 # Entry Point
requirements.txt       # Python Dependencies
Dockerfile.cloudrun    # Produktions-Container
docker-compose.yml     # Lokale Entwicklung (Flask + PostgreSQL 15)
deploy-to-cloud-run.sh # GCP Deployment-Automatisierung
deploy-to-cloud-run.ps1 # PowerShell-Variante
```

## Lokale Entwicklung

### Voraussetzungen
- Python 3.12+
- Docker Desktop (für PostgreSQL)
- `.env`-Datei im Projektroot (nicht im Git, siehe Vorlage unten)

### Starten
```bash
# 1. PostgreSQL starten
docker compose up db -d

# 2. Python venv aktivieren
source venv/Scripts/activate   # Windows/Git Bash
# oder: venv\Scripts\activate  # Windows CMD

# 3. App starten
python run.py
# → http://localhost:5000
```

### .env Vorlage (Pflichtfelder)
```
DATABASE_URL="postgresql://app_user:JapaneseApp2025!@localhost:5432/japanese_learning"
SECRET_KEY="<zufälliger Key>"
WTF_CSRF_SECRET_KEY="<zufälliger Key>"
OPENAI_API_KEY="<OpenAI Key>"
GOOGLE_AI_API_KEY="<Gemini Key>"
GOOGLE_CLIENT_ID="<OAuth Client ID>"
GOOGLE_CLIENT_SECRET="<OAuth Secret>"
POSTFINANCE_SPACE_ID="<Space ID>"
POSTFINANCE_USER_ID="<User ID>"
POSTFINANCE_API_SECRET="<API Secret>"
```

**Wichtig:** `DATABASE_URL` ist Pflicht — es gibt keinen Fallback mehr in `__init__.py`.

## Datenbank

### Lokale Docker-DB
- **User**: `app_user` / **Passwort**: `JapaneseApp2025!`
- **Port**: 5432
- **DB**: `japanese_learning`
- **Daten**: 4 User, 80 Lektionen, 3 Kurse, 4'184 Content-Items (Stand März 2026)

### Modelle (Hauptentitäten)
- **User** — Auth, subscription_level (free/premium), is_admin
- **Lesson** — Lerneinheit mit Preisen, Voraussetzungen, Seiten, Zugriffskontrolle
- **Course** — Gruppiert Lektionen, einzeln kaufbar
- **LessonContent** — Inhalts-Items (Kana, Kanji, Vokabeln, Grammatik, Text, Medien, Quiz)
- **LessonPage** — Seiten innerhalb von Lektionen
- **Kana/Kanji/Vocabulary/Grammar** — Japanische Referenzdaten
- **UserLessonProgress** — Fortschritt pro User/Lektion (JSON)
- **QuizQuestion/QuizOption/UserQuizAnswer** — Quiz-System
- **LessonPurchase/CoursePurchase/PaymentTransaction** — Zahlungs-Tracking

### Migrationen
```bash
source venv/Scripts/activate
flask db migrate -m "Beschreibung"
flask db upgrade
```

## Zugriffskontrolle
Lektion-Zugriff: Guest (kostenlos+allow_guest) → Free (Voraussetzungen prüfen) → Paid (Kauf prüfen) → Premium (Abo prüfen).
Decorators: `@login_required`, `@admin_required`, `@premium_required`.

## Wichtige Muster
- **GCS-aware URLs**: Models lösen Datei-URLs via GCS auf wenn Bucket konfiguriert, sonst lokal
- **KI-Genehmigung**: KI-generierte Items haben `generated_by_ai`-Flag, Admin-Genehmigung erforderlich
- **Payment Mock**: `MockPaymentService` in Dev, echte PostFinance in Prod
- **App Factory**: `create_app()` in `app/__init__.py`
- **File Uploads**: UUID-Dateinamen, MIME-Validierung, Bildverkleinerung (Pillow), max 100MB

## GCP Deployment
- **Projekt**: `jpl-website-bill-20251130` — **Status unklar, möglicherweise gelöscht**
- **Region**: europe-west6 (Zürich)
- **Cloud SQL**: `jpl-psql` (PostgreSQL, 1 CPU, 4GB RAM)
- **Cloud Run**: `japanese-learning-app` (Port 8080, 2 Gunicorn Workers)
- **Deployment**: `./deploy-to-cloud-run.sh` oder `./deploy-to-cloud-run.ps1`

## Bekannte offene Baustellen
1. **PostFinance-Zahlung nicht produktiv** — Letzte Commits zeigen "payment not yet working", MockPayment aktiv
2. **GCP-Projekt-Status unklar** — Muss geprüft werden ob das Projekt noch existiert
3. **Keine automatisierten Tests** — Playwright-Config existiert, aber keine aktiven Tests
4. **Debug-Logging in __init__.py** — Gibt Umgebungsvariablen aus, sollte vor Produktion entfernt werden

## Dokumentation
Guides in `HowToNotes/` zu: OAuth-Setup, Deployment, Monetarisierung, Quiz-Generierung, lokales DB-Setup, GCP VM SSH.
