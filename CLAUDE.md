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
- **Frontend**: Jinja2 Templates, Tailwind CSS (Play CDN), Alpine.js 3.14, HTMX 2.0
- **Admin-UI**: Modulare Partials, Dark Mode, Command Palette (Ctrl+K), Toast-Notifications

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
  templates/
    admin/
      base_admin.html    # Admin-Base: Tailwind, Alpine.js, HTMX, Dark Mode, Command Palette
      manage_lessons.html # Orchestrator (67 Zeilen, inkludiert Partials)
      lessons/           # 11 modulare Partials fuer den Lektions-Editor
        _lesson_modals.html    # Add/Edit Lesson Modals
        _content_modal.html    # Content Manager, Preview, Page Editor
        _content_wizard.html   # 3-Step Content Wizard (9 Content-Typen)
        _import_export.html    # Import/Export Modals
        _styles.html           # CSS + Quill Editor
        _js_core.html          # CSRF, Lesson CRUD, Categories, escapeHtml
        _js_content.html       # Content Load, Bulk Ops, Preview
        _js_editor.html        # Quill, Wizard, Inline-Editing, Save
        _js_file_upload.html   # Drag & Drop, Upload, Progress
        _js_pages.html         # Page CRUD, Page Content Editor
        _js_import_export.html # Export/Import Logik
      manage_kana.html   # Kana-Verwaltung (modernisiert)
      manage_kanji.html  # Kanji-Verwaltung (modernisiert)
      manage_vocabulary.html  # Vocabulary-Verwaltung (modernisiert)
      manage_grammar.html     # Grammar-Verwaltung (modernisiert)
      manage_categories.html  # Kategorien-Verwaltung (modernisiert)
      manage_courses.html     # Kurse-Verwaltung (modernisiert)
      manage_approval.html    # KI-Approval Queue (modernisiert)
      admin_index.html        # Dashboard mit Statistiken
  static/                # CSS, Bilder, Uploads
tests/                   # pytest Unit/Integration + Playwright E2E
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
- **Daten**: 8 User, 10 Lektionen (5 EN + 5 DE), 1 Kurs, 802 Content-Items, 250 Quiz-Fragen (Stand April 2026)

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
- **Custom Admin** (`/admin`) — Modernisiert mit Tailwind CSS, Alpine.js, HTMX
  - Dark Mode (Toggle in Sidebar, localStorage-Persistenz)
  - Command Palette (Ctrl+K) mit Navigation + Aktionen
  - Toast-Notifications statt alert()-Dialoge
  - Lektions-Editor: 11 modulare Partials statt 4'342-Zeilen-Monolith
  - Inline-Editing: Vocabulary/Kanji/Kana/Grammar-Details direkt im Content-Editor bearbeitbar
  - detail_text: Japanische Inhalte (Wort, Lesung, Bedeutung) direkt in der Content-Tabelle sichtbar
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
- **Admin-UI Architektur**: base_admin.html (Tailwind+Alpine+HTMX) → Child-Templates nutzen Blocks (`page_header`, `page_actions`, `content`, `extra_css`, `extra_js`)
- **Lektions-Editor Partials**: manage_lessons.html ist ein 67-Zeilen-Orchestrator der 11 Partials aus `lessons/` inkludiert. Jedes Partial ist eigenständig testbar.
- **Inline Reference Editing**: Content-Editor lädt referenzierte Daten (Vocabulary/Kanji/etc.) per API und speichert Änderungen beim Save zurück — Änderungen wirken global.
- **Playwright MCP**: Konfiguriert in `.mcp.json` für Browser-basierte UI-Tests via Claude Code

## GCP Deployment & Produktion

### Infrastruktur
- **Projekt-ID**: `healthy-coil-466105-d7` (Name: "Japanese-Learning-Website")
- **Account**: `claudio.lutz.cv@gmail.com`
- **Domain**: https://japanese-learning.ch (SSL via Google-managed Zertifikat)
- **Domain-Registrar**: Hostpoint (DNS-Zone dort verwaltet)

### Cloud Run
- **Service**: `japanese-learning-app`
- **Region**: `europe-west1` (Belgien — Zürich unterstützt kein Domain Mapping)
- **Image**: `europe-west6-docker.pkg.dev/healthy-coil-466105-d7/app-images/japanese-learning-app:latest`
- **Ressourcen**: 1 CPU, 1Gi RAM, max 5 Instanzen, Timeout 300s
- **Port**: 8080 (Gunicorn, 2 Workers)
- **Build-Config**: `cloudbuild.yaml` (referenziert `Dockerfile.cloudrun`)

### Cloud SQL
- **Instanz**: `jpl-psql` (PostgreSQL 15, db-f1-micro, europe-west6)
- **IP**: `34.65.56.56` (Public IP, standardmässig keine autorisierten Netzwerke)
- **DB**: `japanese_learning`, User: `app_user`
- **Passwort**: in Secret Manager unter `db-password`
- **Verbindung von Cloud Run**: Unix Socket `/cloudsql/healthy-coil-466105-d7:europe-west6:jpl-psql`

### Cloud SQL Zugriff (lokal)
```bash
# Option A: Temporär IP autorisieren
gcloud sql instances patch jpl-psql \
  --authorized-networks=$(curl -s ifconfig.me)/32 \
  --project=healthy-coil-466105-d7 --quiet
DB_PASS=$(gcloud secrets versions access latest --secret=db-password --project=healthy-coil-466105-d7)
PGPASSWORD="$DB_PASS" psql -h 34.65.56.56 -U app_user -d japanese_learning
# WICHTIG: Danach wieder sperren!
gcloud sql instances patch jpl-psql --clear-authorized-networks \
  --project=healthy-coil-466105-d7 --quiet

# Option B: Cloud SQL Proxy (sicherer, kein IP-Freigabe nötig)
cloud-sql-proxy healthy-coil-466105-d7:europe-west6:jpl-psql --port=5433
# Dann: psql -h localhost -p 5433 -U app_user -d japanese_learning
```

### Secret Manager
- `db-password` — Cloud SQL Passwort
- `flask-secret-key` — Flask SECRET_KEY
- `wtf-csrf-secret-key` — CSRF Secret

### GCS (Google Cloud Storage)
- **Bucket**: `jpl-website-assets` (öffentlich lesbar)
- **Inhalt**: Audio-Dateien (144 MP3s, ~12 MB), Bilder
- **Pfadstruktur**: `gs://jpl-website-assets/lessons/audio/{lektion}/datei.mp3`
- **URL-Muster**: `https://storage.googleapis.com/jpl-website-assets/lessons/audio/...`
- App nutzt `GCS_BUCKET_NAME` Env-Variable; Models lösen URLs via `get_file_url()` auf

### Deployment (Slash-Command)
```
/deploy
```
Oder manuell:
```bash
# 1. Image bauen
gcloud builds submit --config=cloudbuild.yaml --project=healthy-coil-466105-d7 \
  --account=claudio.lutz.cv@gmail.com .
# 2. Deployen
gcloud run services update japanese-learning-app \
  --image=europe-west6-docker.pkg.dev/healthy-coil-466105-d7/app-images/japanese-learning-app:latest \
  --region=europe-west1 --project=healthy-coil-466105-d7 \
  --account=claudio.lutz.cv@gmail.com
# 3. Verifizieren
curl -s -o /dev/null -w "%{http_code}" https://japanese-learning.ch/
```

### Geschätzte Kosten (~12-15 CHF/Monat)
- Cloud SQL db-f1-micro: ~8 CHF
- Cloud Run (pay-per-use): ~2-5 CHF
- Artifact Registry + Secrets: ~1 CHF
- Domain (japanese-learning.ch): ~15 CHF/Jahr

## Datenbank-Sync — Pflicht-Reihenfolge
- **IMMER Cloud→Lokal ZUERST** — Vor jedem Lokal→Cloud-Push muss der aktuelle Produktionsstand heruntergeladen werden. Der Admin kann auf japanese-learning.ch jederzeit Inhalte bearbeiten. Ein blindes Lokal→Cloud überschreibt diese Änderungen.
- **Ablauf**: `/sync-cloud-db` Skill ausführen — der macht automatisch: (A) Cloud→Lokal, dann (B) Lokal→Cloud.
- **Scripts**: `scripts/sync_from_cloud.py` (Cloud→Lokal) und `scripts/sync_content_upsert.py` (Lokal→Cloud)
- **Geschützte Tabellen**: User-Daten, Fortschritt, SRS-States, Käufe werden NIEMALS synchronisiert.

## Arbeitsweise — Sauberer Git-Status
- **Jede Änderung sofort committen und pushen** — nach jeder abgeschlossenen Teilaufgabe wird ein Git-Commit erstellt und auf den Remote gepusht. Das verbessert die Nachvollziehbarkeit und schützt vor Datenverlust.
- **Keine losen Dateien** — am Ende jeder Session muss `git status` sauber sein. Jede Datei muss entweder committed+gepusht, in `.gitignore` eingetragen, oder gelöscht werden falls nicht mehr gebraucht.
- Commit-Messages auf Deutsch, aussagekräftig.

## Qualitätssicherung — Pflichtregeln
- **Tests aktualisieren und ausführen** — Bei jeder Code-Änderung müssen betroffene Tests angepasst und alle Tests mit `pytest` ausgeführt werden. Kein Commit mit fehlschlagenden Tests.
- **Coverage nicht senken** — `fail_under` in pyproject.toml darf nur erhöht, nie gesenkt werden.
- **Neue Features brauchen Tests** — Neue Routen, Services oder Models werden nicht ohne zugehörige Unit-/Integrationstests committed.
- **Linting** — Nach Python-Änderungen `ruff check` ausführen und Fehler beheben.
- **CSS-Änderungen: Deck-Karussell prüfen** — Nach jeder Änderung an `custom.css` (besonders im Flip-Card-Bereich) MUSS geprüft werden, dass die Lernkarten im Deck-Karussell korrekt angezeigt werden (eine Karte nach der anderen, nicht alle untereinander). Ein CSS-Syntaxfehler (z.B. fehlende `}`, doppelter Selektor) bricht das gesamte CSS-Parsing ab und deaktiviert die `.content-item.in-deck { display: none }` Regel — dann werden alle Karten gleichzeitig sichtbar. **Prüfung:** Browser-Konsole öffnen, nach `[Deck]`-Meldungen suchen, und visuell bestätigen dass nur eine Karte sichtbar ist.

## Quiz-System — Einschränkungen
- **Kein `fill_in_the_blank`** — Dieser Fragetyp wird nicht mehr verwendet. Nur `multiple_choice`, `true_false` und `matching` sind erlaubt.

## Bekannte offene Baustellen
1. **Payrexx-Zahlung integriert, noch nicht produktiv** — PayrexxPaymentService erstellt, Payrexx-Konto und API-Keys noch einzurichten
2. **Playwright E2E-Tests** — 8 Spec-Dateien in `tests/`, benötigen `npm install` und laufenden Test-Server
3. **Google OAuth Redirect-URI** — `https://japanese-learning.ch/auth/complete/google-oauth2/` muss in Google Cloud Console als Redirect-URI eingetragen sein (mit Trailing-Slash!)
4. **Docker-Container `japanese_app`** — Alter Container belegt Port 5000 wenn Docker Desktop läuft. `docker stop japanese_app` vor lokalem Start nötig.
