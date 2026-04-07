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
  __init__.py            # App Factory (create_app), Extensions
  models.py              # SQLAlchemy Models
  routes.py              # Alle Routen + API-Endpoints
  utils.py               # FileUploadHandler, URL-Utils
  forms.py               # WTForms (Registration, Login, CSRF)
  gcs_utils.py           # Google Cloud Storage Helpers
  ai_services.py         # KI-Content-Generierung (OpenAI/Gemini)
  social_auth_config.py  # Google OAuth Pipeline
  services/
    payrexx_payment_service.py  # Payrexx Integration (aktiv)
    payment_service.py          # PostFinance Integration (Legacy)
    mock_payment_service.py     # Dev Payment Mock
    payment_factory.py          # Wählt Provider: payrexx/postfinance/mock
  admin_views.py         # Flask-Admin ModelViews (CRUD-Panel)
  templates/             # Jinja2 Templates
  static/                # CSS, Bilder, Uploads
tests/                   # Playwright E2E-Tests
migrations/              # Alembic DB-Migrationen
run.py                   # Entry Point
admin_dashboard.py       # Streamlit Analytics-Dashboard (Port 8501)
.streamlit/              # Streamlit-Konfiguration
requirements.txt         # Python Dependencies
Dockerfile.cloudrun      # Produktions-Container
docker-compose.yml       # Lokale Entwicklung (Flask + PostgreSQL 15)
deploy-to-cloud-run.sh   # GCP Deployment-Automatisierung
deploy-to-cloud-run.ps1  # PowerShell-Variante
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

# 4. (Optional) Analytics-Dashboard starten
streamlit run admin_dashboard.py
# → http://localhost:8501
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
## Payment (Payrexx)
PAYMENT_PROVIDER="payrexx"              # payrexx | postfinance | mock
PAYREXX_INSTANCE="<instanzname>"        # z.B. "meinshop" bei meinshop.payrexx.com
PAYREXX_API_SECRET="<api-secret>"
PAYREXX_WEBHOOK_SECRET="<webhook-signing-key>"

## Legacy (PostFinance, nicht mehr aktiv)
# POSTFINANCE_SPACE_ID="<Space ID>"
# POSTFINANCE_USER_ID="<User ID>"
# POSTFINANCE_API_SECRET="<API Secret>"
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

## Admin-Interfaces
- **Custom Admin** (`/admin`) — Lektions-Editor, KI-Approval, Import/Export (bestehend)
- **Flask-Admin CRUD-Panel** (`/admin-panel`) — Auto-CRUD für Kana, Kanji, Vokabeln, Grammatik, Kategorien, Kurse, Lektionen, Benutzer
- **Streamlit Dashboard** (`localhost:8501`) — Analytics: Benutzer, Lektionen, Content, Umsatz

## Zugriffskontrolle
Lektion-Zugriff: Guest (kostenlos+allow_guest) → Free (Voraussetzungen prüfen) → Paid (Kauf prüfen) → Premium (Abo prüfen).
Decorators: `@login_required`, `@admin_required`, `@premium_required`.

## Wichtige Muster
- **GCS-aware URLs**: Models lösen Datei-URLs via GCS auf wenn Bucket konfiguriert, sonst lokal
- **KI-Genehmigung**: KI-generierte Items haben `generated_by_ai`-Flag, Admin-Genehmigung erforderlich
- **Payment Factory**: `PAYMENT_PROVIDER` Env-Variable steuert Provider (payrexx/postfinance/mock)
- **App Factory**: `create_app()` in `app/__init__.py`
- **File Uploads**: UUID-Dateinamen, MIME-Validierung, Bildverkleinerung (Pillow), max 100MB

## GCP Deployment
- **Projekt**: `jpl-website-bill-20251130` — **Status unklar, möglicherweise gelöscht**
- **Region**: europe-west6 (Zürich)
- **Cloud SQL**: `jpl-psql` (PostgreSQL, 1 CPU, 4GB RAM)
- **Cloud Run**: `japanese-learning-app` (Port 8080, 2 Gunicorn Workers)
- **Deployment**: `./deploy-to-cloud-run.sh` oder `./deploy-to-cloud-run.ps1`

## Arbeitsweise — Sauberer Git-Status
- **Jede Änderung sofort committen und pushen** — nach jeder abgeschlossenen Teilaufgabe wird ein Git-Commit erstellt und auf den Remote gepusht. Das verbessert die Nachvollziehbarkeit und schützt vor Datenverlust.
- **Keine losen Dateien** — am Ende jeder Session muss `git status` sauber sein. Jede Datei muss entweder committed+gepusht, in `.gitignore` eingetragen, oder gelöscht werden falls nicht mehr gebraucht.
- Commit-Messages auf Deutsch, aussagekräftig.

## Qualitätssicherung — Pflichtregeln
- **Tests aktualisieren und ausführen** — Bei jeder Code-Änderung müssen betroffene Tests angepasst und alle Tests mit `pytest` ausgeführt werden. Kein Commit mit fehlschlagenden Tests.
- **Coverage nicht senken** — `fail_under` in pyproject.toml darf nur erhöht, nie gesenkt werden.
- **Neue Features brauchen Tests** — Neue Routen, Services oder Models werden nicht ohne zugehörige Unit-/Integrationstests committed.
- **Linting** — Nach Python-Änderungen `ruff check` ausführen und Fehler beheben.

## Quiz-System — Einschränkungen
- **Kein `fill_in_the_blank`** — Dieser Fragetyp wird nicht mehr verwendet. Nur `multiple_choice`, `true_false` und `matching` sind erlaubt.

## Bekannte offene Baustellen
1. **Payrexx-Zahlung integriert, noch nicht produktiv** — PayrexxPaymentService erstellt, Payrexx-Konto und API-Keys noch einzurichten
2. **GCP-Projekt-Status unklar** — Muss geprüft werden ob das Projekt noch existiert
3. **Playwright E2E-Tests** — 8 Spec-Dateien in `tests/`, benötigen `npm install` und laufenden Test-Server
4. **Debug-Logging in __init__.py** — Gibt Umgebungsvariablen aus, sollte vor Produktion entfernt werden
