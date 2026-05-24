# Japanese Learning Website — Projektanleitung

## Überblick
Flask-basierte Japanisch-Lernplattform mit Lektions-/Kursverwaltung, Benutzerauthentifizierung, KI-generiertem Inhalt (OpenAI/Gemini), Payrexx-Zahlungsintegration. **Self-hosted** auf einem Heim-Server (Docker + Cloudflare Tunnel) — kein GCloud-Hosting mehr (seit 2026-05-24).

## Tech-Stack
- **Backend**: Flask 2.0+, SQLAlchemy, Flask-Login, Flask-Migrate, Flask-WTF
- **Datenbank**: PostgreSQL 15 (Docker) — die lokale Postgres ist die Produktions-DB (self-hosted)
- **Auth**: Flask-Login (lokal) + Google OAuth2 (social-auth, Authlib)
- **KI**: OpenAI GPT + Google Gemini für Lektions-/Quiz-Generierung
- **Zahlungen**: Payrexx Checkout (CHF) — **noch nicht produktiv, MockPayment aktiv**
- **Storage**: lokales Volume `app/static/uploads` (GCS-Bucket `jpl-website-assets` nur noch als Offsite-Backup)
- **Deployment**: Self-hosted (Docker + Gunicorn), öffentlich erreichbar via Cloudflare Tunnel
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
  gcs_utils.py           # Google Cloud Storage Helpers (nur noch fuer Backup-Bucket relevant)
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
  static/                # CSS, Bilder, Uploads (uploads/ ist Docker-Volume-gemountet)
tests/                   # pytest Unit/Integration + Playwright E2E
migrations/              # Alembic DB-Migrationen
run.py                   # Entry Point (Dev-Server)
admin_dashboard.py       # Streamlit Analytics-Dashboard (Port 8501)
.streamlit/              # Streamlit-Konfiguration
requirements.txt         # Python Dependencies
Dockerfile.cloudrun      # Produktions-Container (vom Heim-Server via docker compose gebaut)
docker-compose.yml       # Basis-Compose (Flask + PostgreSQL 15)
docker-compose.override.yml  # Heim-Server-Config (Dockerfile.cloudrun, .env, uploads-Volume, restart)
deploy-to-cloud-run.sh   # OBSOLET (GCloud abgebaut)
deploy-to-cloud-run.ps1  # OBSOLET (GCloud abgebaut)
```

## Lokale Entwicklung / Betrieb

### Produktion (Heim-Server) läuft via Docker Compose
```bash
cd /home/hp-ubuntu/git/Japanese_Learning_Website
sudo docker compose up -d        # startet web (japanese_app) + db (postgres_db)
# → öffentlich über https://japanese-learning.ch (Cloudflare-Tunnel)
# → lokal über http://localhost:5000
```
Container haben `restart: unless-stopped` + Docker-Autostart → überstehen Reboots.

### Dev-Server (optional, ohne Container)
```bash
docker compose up db -d                  # nur PostgreSQL
source venv/bin/activate                 # venv aktivieren
python run.py                            # → http://localhost:5000
streamlit run admin_dashboard.py         # (Optional) Analytics → http://localhost:8501
```

### .env (Pflichtfelder + Produktions-Werte)
```
DATABASE_URL="postgresql://app_user:JapaneseApp2025!@localhost:5432/japanese_learning"
SECRET_KEY="<zufälliger Key>"
WTF_CSRF_SECRET_KEY="<zufälliger Key>"
OPENAI_API_KEY="<OpenAI Key>"
GOOGLE_AI_API_KEY="<Gemini Key>"
GOOGLE_CLIENT_ID="<OAuth Client ID>"
GOOGLE_CLIENT_SECRET="<OAuth Secret>"
# Produktion (Heim-Server):
SITE_URL="https://japanese-learning.ch"
FLASK_ENV="production"
ROBOTS_INDEX="index,follow"
# GCS_BUCKET_NAME ist NICHT gesetzt → Medien werden lokal ausgeliefert (kein GCS-Fallback)
## Payment (Payrexx)
PAYMENT_PROVIDER="payrexx"              # payrexx | postfinance | mock
PAYREXX_INSTANCE="<instanzname>"
PAYREXX_API_SECRET="<api-secret>"
PAYREXX_WEBHOOK_SECRET="<webhook-signing-key>"
```
**Wichtig:** `DATABASE_URL` ist Pflicht — es gibt keinen Fallback mehr in `__init__.py`.
(`docker-compose.override.yml` setzt für den Container `DATABASE_URL` auf den Service-Host `db`.)

## Datenbank

### Postgres (Docker-Container `postgres_db`) = Produktions-DB
- **User**: `app_user` / **Passwort**: `JapaneseApp2025!`
- **Port**: 5432 (Host-gemappt)
- **DB**: `japanese_learning`
- **Daten** (Stand Mai 2026, = ehemalige Produktion, lokal eingespielt): 9 User, 47 Lektionen (36 published), 3 Kurse, 1887 Content-Items, 790 Quiz-Fragen, 519 Vokabeln, 200 Kana, 127 Grammatik, 61 Kanji — inkl. Nutzer-Fortschritt/SRS/Käufe.
- Query-Helfer: `/cloud-db` Skill (Name historisch — verbindet zur lokalen DB).

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
source venv/bin/activate
flask db migrate -m "Beschreibung"
flask db upgrade
```
Im Container läuft `flask db upgrade` automatisch beim Start (Entrypoint).

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
Lektion-Zugriff: Guest (kostenlos+allow_guest_access) → Free (Voraussetzungen prüfen) → Paid (Kauf prüfen) → Premium (Abo prüfen).
Decorators: `@login_required`, `@admin_required`, `@premium_required`.

## Wichtige Muster
- **Medien-URLs**: `/uploads/<path>`-Route (`routes.py:4530`) liefert lokale Dateien aus `app/static/uploads/`; nur falls `GCS_BUCKET_NAME` gesetzt ist (aktuell NICHT) gibt es einen GCS-Redirect-Fallback. Uploads sind als Docker-Volume gemountet (persistent, kein Image-Rebuild bei neuen Medien).
- **KI-Genehmigung**: KI-generierte Items haben `generated_by_ai`-Flag, Admin-Genehmigung erforderlich
- **Payment Factory**: `PAYMENT_PROVIDER` Env-Variable steuert Provider (payrexx/postfinance/mock)
- **App Factory**: `create_app()` in `app/__init__.py`
- **File Uploads**: UUID-Dateinamen, MIME-Validierung, Bildverkleinerung (Pillow), max 100MB
- **Admin-UI Architektur**: base_admin.html (Tailwind+Alpine+HTMX) → Child-Templates nutzen Blocks (`page_header`, `page_actions`, `content`, `extra_css`, `extra_js`)
- **Lektions-Editor Partials**: manage_lessons.html ist ein 67-Zeilen-Orchestrator der 11 Partials aus `lessons/` inkludiert. Jedes Partial ist eigenständig testbar.
- **Inline Reference Editing**: Content-Editor lädt referenzierte Daten (Vocabulary/Kanji/etc.) per API und speichert Änderungen beim Save zurück — Änderungen wirken global.
- **Playwright MCP**: Konfiguriert in `.mcp.json` für Browser-basierte UI-Tests via Claude Code

## Audio-Pipeline (Stand 2026-05-12)

Zwei separate Audio-Systeme mit gemeinsamem Voice-Stack: **Gemini 2.5 Pro TTS Leda** für Japanisch, **Neural2-G** für Deutsch.

### Zwei Systeme
| System | Trigger | Output | Speicherort |
|---|---|---|---|
| **Inline-Audio** (Klick-Audio) | Klick auf `<p>`/`<li>` in `.rich-text-content` | WAV (Gemini) oder MP3 (Chirp-Fallback), Hash-basierter Dateiname | `app/static/uploads/lessons/inline_audio/<hash>.{wav,mp3}` |
| **Block-Player** (▶ über Lesson) | `<audio>`-Element rendert `LessonContent.media_url` | WAV (24kHz PCM, DE+JP concatenated) | `app/static/uploads/lessons/text_audio/lesson_<id>/page_<n>_content_<cid>.wav` |

### Voice-Stack
- **JA**: `gemini-2.5-pro-preview-tts` Voice `Leda` — studio-nahe Qualität via `google-genai` SDK
- **DE**: `de-DE-Neural2-G` Voice — via Cloud TTS REST API (Gemini hat keine deutsche Stimme)
- **Fallback** bei Gemini-Safety-Block / Quota-Hit: `ja-JP-Chirp3-HD-Leda` (gleiche Stimm-Persönlichkeit, andere Engine)

### Kana-Reihen-Pause-Heuristik (`app/routes.py::_maybe_spell_out_kana_row`)
Findet Hiragana/Katakana-Sequenzen (4-7 Mora) und trennt sie mit `、` wenn alle Mora **EINER Reihe** angehören. Beispiele:
- `さしすせそ` → `さ、し、す、せ、そ` ✓ getrennt (alle s-Reihe)
- `あいうえお` → `あ、い、う、え、お` ✓ getrennt (alle Vokale)
- `あおい` (blau, 3 Vokale) → `あおい` ✓ unverändert (Schwelle 4)
- `こんにちは` → unverändert (gemischte Reihen)

**Wichtig:** Trennzeichen ist `、` (japanisches Komma), NICHT `[short pause]`-Markup — letzteres führt bei Gemini zu Truncation (`さしすせそ`-Bug 2026-05-11: nur erste Mora gesprochen). Audio-Probe-validiert.

### Skripte
| Skript | Zweck |
|---|---|
| `scripts/pregenerate_inline_audio.py [lesson_id] [--all] [--force]` | Inline-Audio pro `<p>`/`<li>` rendern, augmented_html in DB schreiben |
| `.claude/skills/generate-lesson/scripts/gen_text_audio.py <lesson_id>` | Block-Player pro LessonContent (DE+JP segmentiert) |
| `scripts/regenerate_block_audio_all.py` | Bulk-Wrapper: ruft gen_text_audio für alle published Lessons mit Skip-Filter |
| `scripts/prefer_wav_over_mp3.py` | Repariert augmented_html nach Quota-Hit-Phase (.mp3 → .wav wo verfügbar) |

### Quota-Limit
- **Gemini 2.5 Pro TTS**: 2'500 Calls/Tag (PaidTier2). Reset täglich um Pacific Midnight (= morgens ~09:00 CET).
- Bei Hit: Chirp-Fallback greift automatisch. **Aber** Chirp-Output ist MP3 (kein WAV), Hash-basierte URLs zeigen dann auf `.mp3` statt `.wav` — nach Quota-Reset mit `prefer_wav_over_mp3.py` re-runnen.

### Medien-Speicherung
Audio + Bilder liegen **lokal** unter `app/static/uploads/` (als Docker-Volume gemountet) und werden direkt ausgeliefert. Der GCS-Bucket `jpl-website-assets` ist nur noch ein Offsite-Backup (Snapshot). WAV→MP3-Konvertierung ist nicht mehr zwingend (lokale Platte hat reichlich Platz; ~4.3 GB Medien total).

### Disclaimer auf Lesson-Pages
Unter jedem Block-Player steht: *"🤖 KI-Stimmen, wir verbessern laufend · Feedback: info@japanese-learning.ch"*. Zwei Stellen in `lesson_view.html` (Standard-Lesson + Conversation-Variante).

## Produktion — Self-Hosting (Heim-Server, seit 2026-05-24)

Die Seite läuft **self-hosted** auf diesem Rechner (`hp-ubuntu`). **Kein GCloud-Hosting mehr.**

### Architektur
```
Internet → Cloudflare (Edge Zürich, HTTPS) → cloudflared-Tunnel (systemd-Dienst)
         → Docker-Container japanese_app (Gunicorn :5000)
         → Docker-Container postgres_db (lokale Postgres = Produktions-DB)
         → Medien: Volume-Mount app/static/uploads
```

### Komponenten
- **App + DB**: `docker compose` (Basis + `docker-compose.override.yml` mit Heim-Config: Dockerfile.cloudrun, `.env`, uploads-Volume, `restart: unless-stopped`).
- **Tunnel**: `cloudflared` als systemd-Dienst (`/etc/cloudflared/config.yml`, Tunnel-UUID `1e02e58b-7c6a-45c7-87d7-ccbd5e685937`). Routet `japanese-learning.ch` + `www` → `localhost:5000`. Autostart, 4 Edge-Verbindungen. Status: `systemctl status cloudflared`.
- **DNS**: läuft über **Cloudflare** (Nameserver `kip`/`noor.ns.cloudflare.com`; Domain bleibt bei Hostpoint registriert). Apex+www → Tunnel (proxied). MX/SPF/DMARC zeigen weiter auf Hostpoint-Mail → **E-Mail unverändert**. DNSSEC ist aus.
- **HTTPS**: automatisch von Cloudflare (Universal SSL).

### Deploy (Code live bringen) — `/deploy` Skill
```bash
cd /home/hp-ubuntu/git/Japanese_Learning_Website
sudo docker compose build web              # Image mit neuem Code bauen
sudo docker compose up -d --no-deps web    # Container neu starten (Entrypoint: flask db upgrade + Gunicorn)
curl -s -o /dev/null -w "%{http_code}\n" https://japanese-learning.ch/   # 200 erwarten
```
DB-Daten + Medien (Volumes) bleiben beim Rebuild erhalten.

### Datenbank-Backups
- **Täglich** via systemd-Timer `jpl-db-backup.timer` (03:30) → `/usr/local/bin/jpl-db-backup.sh` → `/home/hp-ubuntu/jpl-backups/jpl_<ts>.sql.gz` (14 Stück Rotation, Persistent).
- Manuell: `sudo /usr/local/bin/jpl-db-backup.sh`
- Restore: `gunzip -c <dump>.gz | sudo docker exec -i postgres_db psql -U app_user -d japanese_learning`
- ⚠️ **Medien** (`app/static/uploads`, ~4.3 GB) sind NICHT im DB-Backup — Offsite-Kopie liegt im GCS-Bucket `jpl-website-assets`. Bei viel neuen Medien manuell nachsichern.

### GCS-Bucket (nur noch Backup)
- `jpl-website-assets` (public) — seit dem Umzug **nur noch Offsite-Medien-Backup** (Snapshot). App liefert Medien lokal aus.
- Zugriff: `gcloud storage ... --account=claudio.lutz.cv@gmail.com` (Default-Konto ist `billwilson...` und NICHT projektberechtigt → `--account` zwingend).

### 2026-05-24 GELÖSCHT (existiert nicht mehr)
- ❌ **Cloud Run** `japanese-learning-app` (`deploy-to-cloud-run.sh/.ps1`, `cloudbuild.yaml` obsolet)
- ❌ **Cloud SQL** `jpl-psql` (Produktions-DB ist jetzt lokal)
- ❌ **Secret Manager** (Secrets leben in `.env`)
- GCP-Projekt `healthy-coil-466105-d7` bleibt nur für den Backup-Bucket.

## SEO & Google Search Console

### Implementierte Basis (im Code)
- **Meta-Tags** in `app/templates/base.html`: `description`, `robots`, `canonical`, OpenGraph, Twitter Card. Pro-Seite überschreibbar via Jinja-Blocks (`meta_description`, `og_image`, `og_type`, `structured_data`).
- **JSON-LD** in `base.html`: `EducationalOrganization` + `WebSite` mit SearchAction. `lesson_view.html` ergänzt `Course`-Schema pro Lektion.
- **`/robots.txt`** und **`/sitemap.xml`** als Routes in `app/seo_routes.py` (eigenes Blueprint, von CSRF exempt). Sitemap pullt alle `is_published` Lessons + Courses + statische Seiten dynamisch aus der DB.
- **Steuer-Env-Variablen** (`__init__.py`):
  - `SITE_URL` (Default `https://japanese-learning.ch`)
  - `ROBOTS_INDEX` — auf Staging/Preview auf `noindex,nofollow` setzen, dann sperrt robots.txt automatisch alles (Produktion: `index,follow`)
  - `GOOGLE_SITE_VERIFICATION` — optionaler Meta-Tag-Fallback, falls DNS-TXT nicht möglich
  - `SEO_DEFAULT_OG_IMAGE` — 1200×630 PNG (liegt lokal unter `app/static/uploads/`, URL hier eintragen)

### Google Search Console — Setup-Schritte
1. **Search Console öffnen**: https://search.google.com/search-console — mit `claudio.lutz.cv@gmail.com` einloggen.
2. **Property anlegen** → **Domain** (nicht URL-Prefix), Eingabe: `japanese-learning.ch`. Domain-Property erfasst beide Schemas (https/www) auf einmal.
3. **Verifikations-TXT-Record** kopieren (Format `google-site-verification=…`).
4. **DNS jetzt bei Cloudflare** (Nameserver `kip`/`noor.ns.cloudflare.com`): im Cloudflare-Dashboard → DNS → neuer **TXT-Record** mit Name `@`, Wert `google-site-verification=…`, DNS only. Propagation meist <1h.
5. **In Search Console** "Verify" klicken. (TXT-Record drinlassen — entfernen invalidiert.)
6. **Sitemap einreichen**: in Search Console links **Sitemaps** → URL `https://japanese-learning.ch/sitemap.xml`.
7. **Indexing anfordern**: rechts oben "URL inspection" für `/`, `/learn/n5`, `/lessons` — "Request Indexing" (initial einmalig).

**Fallback ohne DNS-Zugriff**: Env-Variable `GOOGLE_SITE_VERIFICATION=<token>` in `.env` setzen + Container neu starten → `<meta name="google-site-verification">` rendert automatisch. Dann in Search Console "HTML tag"-Methode wählen.

### Verification & Monitoring
```bash
# Lokal verifizieren:
curl -s http://localhost:5000/robots.txt | head -20
curl -s http://localhost:5000/sitemap.xml | head -40
# Live verifizieren:
curl -sI https://japanese-learning.ch/sitemap.xml
curl -s https://japanese-learning.ch/sitemap.xml | grep -c '<loc>'
```
- **Rich-Results-Test**: https://search.google.com/test/rich-results (JSON-LD validieren)
- **PageSpeed / Core Web Vitals**: https://pagespeed.web.dev/?url=https://japanese-learning.ch

### Wenn neue oeffentliche Routen dazukommen
Statische Seiten in `app/seo_routes.py::sitemap_xml()` ergänzen (`static_pages`-Liste). Lessons/Courses laufen automatisch mit, sobald `is_published=True`.

## Datenbank — lokale Produktions-DB (kein Cloud-Sync mehr)
- Die lokale Postgres (`postgres_db`-Container) ist seit dem Self-Hosting-Umzug die **einzige produktive Datenquelle**. Es gibt **kein Cloud SQL und keinen Cloud-Sync mehr**.
- ⚠️ Alte Sync-Skripte (`scripts/sync_from_cloud.py`, `scripts/sync_content_upsert.py`, `scripts/sync_assets_to_gcs.py`, `scripts/sync_safety.py`) sind **obsolet** (zielen auf gelöschtes Cloud SQL) — nicht mehr ausführen. (Bleiben als Dead-Code, da Tests sie referenzieren.)
- Sicherung: täglicher `pg_dump` via systemd-Timer (siehe Produktions-Sektion).

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
4. **DNSSEC** — bei der Cloudflare-Migration deaktiviert; optional via Cloudflare wieder aktivierbar (Sicherheits-Plus)
5. **Medien-Offsite-Backup** — `app/static/uploads` (~4.3 GB) wird nicht vom DB-Backup erfasst; GCS-Bucket ist Snapshot-Stand. Für echtes laufendes Offsite-Backup ggf. periodisch nachsichern (externe Platte/NAS).
