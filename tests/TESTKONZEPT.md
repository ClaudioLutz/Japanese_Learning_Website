# Testkonzept — Japanese Learning Website

## 1. Einleitung

### 1.1 Zweck
Dieses Dokument definiert die Teststrategie, Testbereiche und Testfälle für die Japanese Learning Website. Ziel ist eine systematische Qualitätssicherung aller Funktionen vor dem Produktivgang.

### 1.2 Geltungsbereich
- Flask-Backend (Routes, Models, Services, Utils)
- Payment-Integration (Payrexx, PostFinance Legacy, Mock)
- Authentifizierung (Flask-Login, Google OAuth2)
- KI-Content-Generierung (OpenAI, Gemini)
- Datei-Verwaltung (Lokal + Google Cloud Storage)
- Frontend (Jinja2 Templates via E2E)

### 1.3 Referenzen
- `CLAUDE.md` — Projektdokumentation
- `tests/*.spec.js` — Bestehende Playwright E2E-Tests
- Payrexx API Docs: https://developers.payrexx.com/reference

---

## 2. Teststrategie

### 2.1 Testpyramide

```
          /    E2E    \          ~10%  Playwright (bestehend)
         / Integration \         ~30%  Flask test_client + DB
        /     Unit      \        ~60%  Models, Services, Utils
```

### 2.2 Testarten

| Art | Beschreibung | Tooling |
|-----|-------------|---------|
| **Unit** | Isolierte Logik ohne DB/HTTP | pytest + pytest-mock |
| **Integration** | Routes, DB-Queries, Auth-Flows | pytest-flask + Test-PostgreSQL |
| **E2E** | Browser-basierte User-Journeys | Playwright (bestehend) |
| **Security** | CSRF, Auth-Bypass, Input-Validation | pytest + Playwright |

### 2.3 Testumgebungen

| Umgebung | DB | Externe APIs | Zweck |
|----------|-----|-------------|-------|
| **Lokal (Unit)** | SQLite in-memory | Alle gemockt | Schnelle Entwickler-Tests |
| **Lokal (Integration)** | PostgreSQL (Docker) | Alle gemockt | Realitätsnahe Tests |
| **CI (GitHub Actions)** | PostgreSQL Service | Alle gemockt | Automatisierte Regression |

### 2.4 Entry/Exit-Kriterien

**Entry:** Code kompiliert fehlerfrei, DB-Migrationen laufen durch.
**Exit:** Alle Tests grün, Coverage >= 80%, keine kritischen Bugs offen.

---

## 3. Testumgebung und Tooling

### 3.1 Tech-Stack

```
# requirements-test.txt
pytest>=8.0
pytest-flask>=1.3
pytest-cov>=5.0
pytest-mock>=3.14
factory-boy>=3.3
faker>=28.0
freezegun>=1.4
responses>=0.25
```

### 3.2 Projektstruktur

```
tests/
  conftest.py                    # Globale Fixtures (app, client, db, auth)
  factories.py                   # factory_boy Test-Factories
  unit/
    test_models.py               # Model-Logik, Properties, Validierung
    test_utils.py                # FileUploadHandler, URL-Konvertierung
    test_forms.py                # WTForms Custom-Validators
    test_payment_factory.py      # Provider-Auswahl-Logik
    test_payment_services.py     # Payrexx/Mock Service-Logik
    test_transaction_service.py  # Transaction State Machine
    test_ai_services.py          # KI-Content-Parsing
  integration/
    test_public_routes.py        # Öffentliche Seiten + Health-Checks
    test_auth.py                 # Registration, Login, Logout, OAuth
    test_lesson_routes.py        # Lektions-Zugriff, Progress, Quiz
    test_course_routes.py        # Kurs-Katalog, Kurs-Kauf
    test_payment_routes.py       # Kauf-Flow, Webhooks, Status
    test_admin_api.py            # CRUD für Kana/Kanji/Vocab/Grammar/Lessons/Courses
    test_admin_content.py        # Content-Management, Bulk-Operationen
    test_file_upload.py          # Upload, GCS-Integration
    test_import_export.py        # Lesson Import/Export
  e2e/                           # Bestehende Playwright-Tests (8 Specs)
    01-public-routes.spec.js
    02-authentication.spec.js
    03-lessons-courses.spec.js
    04-payment.spec.js
    05-admin.spec.js
    06-api-endpoints.spec.js
    07-security.spec.js
    08-tokyo-lesson.spec.js
    helpers.js
    start_test_server.py
  TESTKONZEPT.md                 # Dieses Dokument
```

### 3.3 Mocking-Strategie

| Externe Abhängigkeit | Mock-Methode | Library |
|---------------------|--------------|---------|
| Payrexx API | `responses` (HTTP-Level) | responses |
| OpenAI API | `responses` (HTTP-Level) | responses |
| Google Gemini | `pytest-mock` (Methoden-Level) | pytest-mock |
| Google Cloud Storage | `pytest-mock` (Methoden-Level) | pytest-mock |
| Google OAuth2 | `pytest-mock` (Pipeline-Level) | pytest-mock |
| Zeitabhängige Logik | `freezegun` | freezegun |

---

## 4. Testbereiche

### 4.1 Unit-Tests

#### 4.1.1 Models (`test_models.py`)

| # | Testfall | Modul | Priorität |
|---|---------|-------|-----------|
| U-M01 | User.set_password() hasht korrekt | User | Hoch |
| U-M02 | User.check_password() validiert korrekt | User | Hoch |
| U-M03 | User.check_password() lehnt falsches Passwort ab | User | Hoch |
| U-M04 | Lesson.is_accessible_to_user() — Free Lesson für Guest | Lesson | Hoch |
| U-M05 | Lesson.is_accessible_to_user() — Paid Lesson ohne Kauf blockiert | Lesson | Hoch |
| U-M06 | Lesson.is_accessible_to_user() — Paid Lesson mit Kauf erlaubt | Lesson | Hoch |
| U-M07 | Lesson.is_accessible_to_user() — Premium Lesson für Free-User blockiert | Lesson | Hoch |
| U-M08 | Lesson.is_accessible_to_user() — Premium Lesson für Premium-User erlaubt | Lesson | Hoch |
| U-M09 | Lesson.is_accessible_to_user() — Kurs-Kauf gewährt Zugriff auf Kurs-Lektionen | Lesson | Hoch |
| U-M10 | Lesson.is_accessible_to_user() — Voraussetzungen nicht erfüllt blockiert | Lesson | Mittel |
| U-M11 | Lesson.pages Property gruppiert Content nach Seitennummern | Lesson | Mittel |
| U-M12 | Lesson event listener setzt lesson_type basierend auf price | Lesson | Mittel |
| U-M13 | LessonContent.get_content_data() gibt korrektes Objekt zurück (Kana/Kanji/Vocab/Grammar) | LessonContent | Mittel |
| U-M14 | LessonContent.get_file_url() gibt GCS-URL zurück wenn konfiguriert | LessonContent | Mittel |
| U-M15 | UserLessonProgress.get_content_progress() parst JSON korrekt | UserLessonProgress | Mittel |
| U-M16 | UserLessonProgress.mark_content_completed() aktualisiert Progress | UserLessonProgress | Mittel |
| U-M17 | UserLessonProgress.update_progress_percentage() berechnet korrekt | UserLessonProgress | Mittel |
| U-M18 | UserLessonProgress.reset() setzt alles zurück | UserLessonProgress | Mittel |
| U-M19 | PaymentTransaction unique constraint auf transaction_id | PaymentTransaction | Hoch |
| U-M20 | Course-Lesson M:N Beziehung funktioniert | Course | Mittel |

#### 4.1.2 Formulare (`test_forms.py`)

| # | Testfall | Priorität |
|---|---------|-----------|
| U-F01 | RegistrationForm akzeptiert valide Daten | Hoch |
| U-F02 | RegistrationForm lehnt doppelten Username ab | Hoch |
| U-F03 | RegistrationForm lehnt doppelte Email ab | Hoch |
| U-F04 | RegistrationForm lehnt nicht-übereinstimmende Passwörter ab | Hoch |
| U-F05 | RegistrationForm lehnt ungültige Email ab | Mittel |
| U-F06 | LoginForm akzeptiert valide Daten | Mittel |
| U-F07 | LoginForm lehnt leere Felder ab | Mittel |

#### 4.1.3 Utils (`test_utils.py`)

| # | Testfall | Priorität |
|---|---------|-----------|
| U-U01 | convert_to_embed_url() — Standard YouTube URL | Mittel |
| U-U02 | convert_to_embed_url() — youtu.be Kurzlink | Mittel |
| U-U03 | convert_to_embed_url() — Bereits Embed-URL bleibt unverändert | Mittel |
| U-U04 | convert_to_embed_url() — Ungültige URL gibt Original zurück | Mittel |
| U-U05 | FileUploadHandler.allowed_file() — Erlaubte Extensions | Mittel |
| U-U06 | FileUploadHandler.allowed_file() — Verbotene Extensions blockiert | Hoch |
| U-U07 | FileUploadHandler.get_file_type() — Korrekte Typ-Erkennung | Mittel |
| U-U08 | FileUploadHandler.generate_unique_filename() — UUID-Format | Niedrig |
| U-U09 | FileUploadHandler.format_file_size() — KB/MB/GB Formatierung | Niedrig |
| U-U10 | FileUploadHandler.validate_file_content() — MIME-Type Prüfung | Hoch |
| U-U11 | FileUploadHandler.process_image() — Resize funktioniert | Mittel |
| U-U12 | FileUploadHandler.process_image() — RGBA zu RGB Konvertierung | Mittel |

#### 4.1.4 Payment Factory (`test_payment_factory.py`)

| # | Testfall | Priorität |
|---|---------|-----------|
| U-PF01 | MOCK_PAYMENTS_ENABLED=true → MockPaymentService | Hoch |
| U-PF02 | PAYMENT_PROVIDER=payrexx + Credentials → PayrexxPaymentService | Hoch |
| U-PF03 | PAYMENT_PROVIDER=payrexx ohne Credentials → MockPaymentService (Fallback) | Hoch |
| U-PF04 | PAYMENT_PROVIDER=postfinance + Credentials → PostFinanceService | Mittel |
| U-PF05 | PAYMENT_PROVIDER=postfinance ohne Credentials → MockPaymentService | Mittel |
| U-PF06 | Kein Provider konfiguriert → MockPaymentService | Hoch |
| U-PF07 | Payrexx-Init-Fehler → MockPaymentService (Fallback) | Mittel |

#### 4.1.5 Payment Services (`test_payment_services.py`)

| # | Testfall | Priorität |
|---|---------|-----------|
| U-PS01 | MockPaymentService.create_lesson_transaction() erstellt LessonPurchase | Hoch |
| U-PS02 | MockPaymentService.create_lesson_transaction() verhindert Doppelkauf | Hoch |
| U-PS03 | MockPaymentService.create_course_transaction() erstellt CoursePurchase | Hoch |
| U-PS04 | MockPaymentService.get_transaction_status() gibt COMPLETED zurück | Mittel |
| U-PS05 | PayrexxPaymentService.__init__() wirft Fehler ohne Credentials | Hoch |
| U-PS06 | PayrexxPaymentService._map_status() mappt alle Payrexx-Statuswerte korrekt | Hoch |
| U-PS07 | PayrexxPaymentService.verify_webhook_signature() — Gültige Signatur | Hoch |
| U-PS08 | PayrexxPaymentService.verify_webhook_signature() — Ungültige Signatur abgelehnt | Hoch |
| U-PS09 | PayrexxPaymentService.verify_webhook_signature() — Fehlendes Secret | Mittel |
| U-PS10 | PayrexxPaymentService.create_lesson_transaction() baut korrekten Payload | Mittel |
| U-PS11 | PayrexxPaymentService.create_lesson_transaction() Fehlerfall → error dict | Mittel |
| U-PS12 | PayrexxPaymentService._create_gateway() API-Fehler Handling | Mittel |

#### 4.1.6 Transaction Service (`test_transaction_service.py`)

| # | Testfall | Priorität |
|---|---------|-----------|
| U-TS01 | create_payment_transaction() erstellt Record korrekt | Hoch |
| U-TS02 | update_transaction_state() PENDING→COMPLETED erstellt LessonPurchase | Hoch |
| U-TS03 | update_transaction_state() PENDING→COMPLETED erstellt CoursePurchase | Hoch |
| U-TS04 | update_transaction_state() PENDING→FAILED loggt Fehler | Mittel |
| U-TS05 | update_transaction_state() nicht-existierende Transaction gibt False | Mittel |
| U-TS06 | _complete_purchase() verhindert Doppel-Purchase | Hoch |
| U-TS07 | get_user_transactions() gibt sortierte Liste zurück | Niedrig |
| U-TS08 | get_transaction_by_id() findet Transaction | Niedrig |
| U-TS09 | get_transaction_by_id() gibt None für unbekannte ID | Niedrig |

#### 4.1.7 KI-Services (`test_ai_services.py`)

| # | Testfall | Priorität |
|---|---------|-----------|
| U-AI01 | convert_jlpt_level_to_int() N1-N5 korrekt | Niedrig |
| U-AI02 | truncate_field() kürzt korrekt mit "..." | Niedrig |
| U-AI03 | convert_difficulty_to_int() mappt alle Level | Niedrig |
| U-AI04 | generate_kanji_content() parst Gemini-Antwort korrekt | Mittel |
| U-AI05 | generate_vocabulary_content() parst Gemini-Antwort korrekt | Mittel |
| U-AI06 | generate_grammar_content() parst Gemini-Antwort korrekt | Mittel |
| U-AI07 | generate_lesson_image() ruft DALL-E korrekt auf | Mittel |
| U-AI08 | AI-Fehler bei ungültigem JSON-Response | Mittel |

---

### 4.2 Integrationstests

#### 4.2.1 Öffentliche Routes (`test_public_routes.py`)

| # | Testfall | Priorität |
|---|---------|-----------|
| I-PR01 | GET / gibt 200 + Homepage zurück | Hoch |
| I-PR02 | GET /healthz gibt JSON mit status=ok | Hoch |
| I-PR03 | GET /health gibt JSON mit DB-Check | Hoch |
| I-PR04 | GET /health gibt 503 wenn DB nicht erreichbar | Mittel |
| I-PR05 | GET /lessons gibt Lektionskatalog | Hoch |
| I-PR06 | GET /courses gibt Kurskatalog | Hoch |
| I-PR07 | GET /lessons?category=X filtert korrekt | Mittel |
| I-PR08 | GET /lessons/<id> — Free Lesson ohne Login zugänglich | Hoch |
| I-PR09 | GET /lessons/<id> — Paid Lesson ohne Login → Redirect | Hoch |
| I-PR10 | GET /course/<id> zeigt Kursdetails + Lektionsliste | Mittel |
| I-PR11 | GET /nonexistent gibt 404 | Niedrig |

#### 4.2.2 Authentifizierung (`test_auth.py`)

| # | Testfall | Priorität |
|---|---------|-----------|
| I-AU01 | POST /register — Valide Registration erstellt User + Login | Hoch |
| I-AU02 | POST /register — Doppelter Username → Fehler | Hoch |
| I-AU03 | POST /register — Doppelte Email → Fehler | Hoch |
| I-AU04 | POST /register — Nicht-übereinstimmende Passwörter → Fehler | Hoch |
| I-AU05 | POST /login — Valide Credentials → Login + Redirect | Hoch |
| I-AU06 | POST /login — Falsches Passwort → Fehler, bleibt auf /login | Hoch |
| I-AU07 | POST /login — Nicht-existierende Email → Fehler | Mittel |
| I-AU08 | GET /logout — Zerstört Session | Hoch |
| I-AU09 | GET /profile — Ohne Login → Redirect zu /login | Hoch |
| I-AU10 | GET /admin — Ohne Login → Redirect | Hoch |
| I-AU11 | GET /admin — Als normaler User → Redirect/403 | Hoch |
| I-AU12 | GET /admin — Als Admin → 200 | Hoch |
| I-AU13 | POST /login — Admin wird zu /admin weitergeleitet | Mittel |
| I-AU14 | premium_required Decorator blockiert Free-User | Mittel |

#### 4.2.3 Lektions-Routes (`test_lesson_routes.py`)

| # | Testfall | Priorität |
|---|---------|-----------|
| I-LR01 | GET /lessons/<id> — Gekaufte Lektion zeigt Content | Hoch |
| I-LR02 | GET /lessons/<id> — Premium-Lektion für Premium-User zugänglich | Hoch |
| I-LR03 | GET /lessons/<id> — Premium-Lektion für Free-User blockiert | Hoch |
| I-LR04 | GET /lessons/<id> — Voraussetzung nicht erfüllt → Hinweis | Mittel |
| I-LR05 | POST /api/lessons/<id>/progress — Progress speichern | Hoch |
| I-LR06 | POST /api/lessons/<id>/progress — Ohne Auth → 401/302 | Mittel |
| I-LR07 | POST /api/lessons/<id>/reset — Progress zurücksetzen | Mittel |
| I-LR08 | POST /api/lessons/<id>/quiz/<qid>/answer — Quiz-Antwort speichern | Hoch |
| I-LR09 | POST /api/lessons/<id>/quiz/<qid>/answer — Korrekte Antwort markiert | Mittel |
| I-LR10 | GET /my-lessons — Zeigt gekaufte + freie Lektionen | Mittel |
| I-LR11 | GET /my-lessons — Ohne Auth → Redirect | Mittel |

#### 4.2.4 Kurs-Routes (`test_course_routes.py`)

| # | Testfall | Priorität |
|---|---------|-----------|
| I-CR01 | GET /api/courses — Gibt publizierte Kurse | Mittel |
| I-CR02 | GET /course/<id> — Zeigt Kurs mit Lektionen | Mittel |
| I-CR03 | Kurs-Kauf gewährt Zugriff auf alle Kurs-Lektionen | Hoch |

#### 4.2.5 Payment-Routes (`test_payment_routes.py`)

| # | Testfall | Priorität |
|---|---------|-----------|
| I-PA01 | POST /api/lessons/<id>/purchase — Erstellt Transaction (Mock) | Hoch |
| I-PA02 | POST /api/lessons/<id>/purchase — Bereits gekauft → Fehler | Hoch |
| I-PA03 | POST /api/lessons/<id>/purchase — Ohne Auth → Fehler | Hoch |
| I-PA04 | POST /api/lessons/<id>/purchase — Free Lesson → Kein Kauf nötig | Mittel |
| I-PA05 | POST /api/courses/<id>/purchase — Erstellt Course Transaction | Hoch |
| I-PA06 | GET /api/payment/status/<id> — Gibt Transaktionsstatus | Mittel |
| I-PA07 | POST /api/payment/cancel/<id> — Bricht Transaction ab | Mittel |
| I-PA08 | GET /payment/success — Zeigt Erfolgsseite | Niedrig |
| I-PA09 | GET /payment/failed — Zeigt Fehlerseite | Niedrig |
| I-PA10 | POST /api/payment/webhook/payrexx — Gültiger Webhook aktualisiert Transaction | Hoch |
| I-PA11 | POST /api/payment/webhook/payrexx — Ungültige Signatur → 403 | Hoch |
| I-PA12 | POST /api/payment/webhook/payrexx — Webhook COMPLETED → LessonPurchase erstellt | Hoch |
| I-PA13 | GET /api/user/purchases — Gibt alle User-Käufe | Mittel |
| I-PA14 | GET /api/lessons/<id>/purchase-status — Gibt Kaufstatus | Mittel |
| I-PA15 | POST /upgrade_to_premium — Ändert subscription_level | Mittel |
| I-PA16 | POST /downgrade_from_premium — Ändert subscription_level zurück | Mittel |

#### 4.2.6 Admin CRUD API (`test_admin_api.py`)

| # | Testfall | Priorität |
|---|---------|-----------|
| I-AD01 | GET /api/admin/kana — Liste aller Kana (als Admin) | Hoch |
| I-AD02 | POST /api/admin/kana/new — Kana erstellen | Hoch |
| I-AD03 | PUT /api/admin/kana/<id>/edit — Kana aktualisieren | Mittel |
| I-AD04 | DELETE /api/admin/kana/<id>/delete — Kana löschen | Mittel |
| I-AD05 | GET /api/admin/kanji — Liste aller Kanji | Hoch |
| I-AD06 | POST /api/admin/kanji/new — Kanji erstellen (mit AI-Flag) | Hoch |
| I-AD07 | PUT /api/admin/kanji/<id>/edit — Kanji aktualisieren | Mittel |
| I-AD08 | DELETE /api/admin/kanji/<id>/delete — Kanji löschen | Mittel |
| I-AD09 | GET /api/admin/vocabulary — Liste aller Vokabeln | Hoch |
| I-AD10 | POST /api/admin/vocabulary/new — Vokabel erstellen | Mittel |
| I-AD11 | GET /api/admin/grammar — Liste aller Grammatik | Mittel |
| I-AD12 | POST /api/admin/grammar/new — Grammatik erstellen | Mittel |
| I-AD13 | GET /api/admin/categories — Liste aller Kategorien | Mittel |
| I-AD14 | POST /api/admin/categories/new — Kategorie erstellen | Mittel |
| I-AD15 | GET /api/admin/courses — Liste aller Kurse | Mittel |
| I-AD16 | POST /api/admin/courses/new — Kurs erstellen | Mittel |
| I-AD17 | GET /api/admin/lessons — Liste aller Lektionen | Hoch |
| I-AD18 | POST /api/admin/lessons/new — Lektion erstellen | Hoch |
| I-AD19 | PUT /api/admin/lessons/<id>/edit — Lektion aktualisieren | Mittel |
| I-AD20 | DELETE /api/admin/lessons/<id>/delete — Lektion löschen | Mittel |
| I-AD21 | POST /api/admin/lessons/reorder — Reihenfolge ändern | Mittel |
| I-AD22 | POST /api/admin/lessons/<id>/move — Lektion verschieben | Mittel |
| I-AD23 | Alle Admin-APIs als normaler User → 302/403 | Hoch |

#### 4.2.7 Admin Content Management (`test_admin_content.py`)

| # | Testfall | Priorität |
|---|---------|-----------|
| I-AC01 | GET /api/admin/lessons/<id>/content — Content-Liste | Hoch |
| I-AC02 | POST /api/admin/lessons/<id>/content/new — Content hinzufügen | Hoch |
| I-AC03 | DELETE /api/admin/lessons/<id>/content/<cid>/delete — Content löschen | Mittel |
| I-AC04 | POST /api/admin/lessons/<id>/content/<cid>/move — Content verschieben | Mittel |
| I-AC05 | POST /api/admin/lessons/<id>/pages/<pn>/reorder — Seite neu sortieren | Mittel |
| I-AC06 | PUT /api/admin/content/<cid>/edit — Content aktualisieren | Mittel |
| I-AC07 | PUT /api/admin/lessons/<id>/content/bulk-update — Bulk Update | Mittel |
| I-AC08 | POST /api/admin/lessons/<id>/content/bulk-duplicate — Bulk Duplicate | Niedrig |
| I-AC09 | DELETE /api/admin/lessons/<id>/content/bulk-delete — Bulk Delete | Niedrig |
| I-AC10 | POST /api/admin/content/<cid>/duplicate — Einzelnes Content duplizieren | Niedrig |
| I-AC11 | DELETE /api/admin/lessons/<id>/pages/<pn>/delete — Seite löschen | Mittel |
| I-AC12 | PUT /api/admin/lessons/<id>/pages/<pn> — Seite aktualisieren | Niedrig |
| I-AC13 | POST /api/admin/content/<type>/<id>/approve — Content genehmigen | Mittel |
| I-AC14 | POST /api/admin/content/<type>/<id>/reject — Content ablehnen | Mittel |
| I-AC15 | GET /api/admin/content-options/<type> — Verfügbare Items | Mittel |

#### 4.2.8 Datei-Upload (`test_file_upload.py`)

| # | Testfall | Priorität |
|---|---------|-----------|
| I-FU01 | POST /api/admin/upload-file — Bild hochladen (lokal) | Hoch |
| I-FU02 | POST /api/admin/upload-file — Verbotener Dateityp → Fehler | Hoch |
| I-FU03 | POST /api/admin/upload-file — Datei zu gross → Fehler | Mittel |
| I-FU04 | POST /api/admin/lessons/<id>/content/file — Datei als Content | Mittel |
| I-FU05 | DELETE /api/admin/delete-file — Datei löschen | Mittel |
| I-FU06 | GCS-Upload wenn Bucket konfiguriert (gemockt) | Mittel |

#### 4.2.9 Import/Export (`test_import_export.py`)

| # | Testfall | Priorität |
|---|---------|-----------|
| I-IE01 | GET /api/admin/lessons/<id>/export — JSON-Export | Mittel |
| I-IE02 | POST /api/admin/lessons/import — JSON-Import erstellt Lektion | Mittel |
| I-IE03 | POST /api/admin/lessons/<id>/export-package — ZIP-Export | Niedrig |
| I-IE04 | POST /api/admin/lessons/import-package — ZIP-Import | Niedrig |
| I-IE05 | POST /api/admin/lessons/export-multiple — Multi-Export | Niedrig |
| I-IE06 | POST /api/admin/lessons/import-info — Info auslesen | Niedrig |

---

### 4.3 E2E-Tests (Playwright — bestehend)

Die 8 bestehenden Spec-Dateien decken die wichtigsten User-Journeys ab:

| Spec | Beschreibung | Test-Cases |
|------|-------------|------------|
| `01-public-routes.spec.js` | Öffentliche Seiten, Health-Checks, 404 | ~10 |
| `02-authentication.spec.js` | Registration, Login, Logout, Session | ~12 |
| `03-lessons-courses.spec.js` | Lektionskatalog, Zugriff, Progress, Kurse | ~20 |
| `04-payment.spec.js` | Kauf-Flow, Transaktionsstatus, Premium | ~12 |
| `05-admin.spec.js` | Admin-Dashboard, CRUD-UIs, APIs | ~20 |
| `06-api-endpoints.spec.js` | API-Serialisierung, Error-Handling | ~15 |
| `07-security.spec.js` | CSRF, Auth-Enforcement, XSS, Sessions | ~10 |
| `08-tokyo-lesson.spec.js` | Kompletter 7-Seiten-Durchlauf, Quiz, Audio | ~25 |

**Gesamt: ~124 E2E-Tests**

---

### 4.4 Nicht-funktionale Tests

#### 4.4.1 Security (in Integrationstests eingebettet)

| # | Testfall | Priorität |
|---|---------|-----------|
| S-01 | POST ohne CSRF-Token → 400 | Hoch |
| S-02 | Admin-API ohne Auth → 302/403 | Hoch |
| S-03 | Admin-API als normaler User → 302/403 | Hoch |
| S-04 | Payrexx-Webhook ohne/mit falscher Signatur → 403 | Hoch |
| S-05 | SQL-Injection in Suchfeldern hat keine Wirkung | Mittel |
| S-06 | XSS in Registration-Feldern wird escaped | Mittel |
| S-07 | Datei-Upload mit manipulierter Extension wird geprüft | Mittel |
| S-08 | IDOR: User kann fremde Purchases nicht einsehen | Hoch |

---

## 5. Testdaten-Management

### 5.1 Factory-basierte Testdaten (factory_boy)

```python
# tests/factories.py — Hauptfactories

UserFactory          # Standard Free-User
AdminUserFactory     # Admin-User (is_admin=True)
PremiumUserFactory   # Premium-User (subscription_level='premium')
LessonFactory        # Publizierte Free-Lektion
PaidLessonFactory    # Publizierte Paid-Lektion (price=29.00)
CourseFactory        # Publizierter Kurs mit Lektionen
KanaFactory          # Hiragana/Katakana Testdaten
KanjiFactory         # Kanji Testdaten
VocabularyFactory    # Vokabel Testdaten
GrammarFactory       # Grammatik Testdaten
LessonContentFactory # Content-Items
QuizQuestionFactory  # Quiz-Fragen mit Optionen
```

### 5.2 Fixtures (conftest.py)

```python
# Kern-Fixtures
app              # Flask-App mit Test-Konfiguration
client           # Flask Test-Client
db               # Frische DB pro Test (Transaction-Rollback)
auth_client      # Eingeloggter Standard-User
admin_client     # Eingeloggter Admin
premium_client   # Eingeloggter Premium-User
sample_lesson    # Lektion mit Content + Pages
sample_course    # Kurs mit 3 Lektionen
```

---

## 6. Coverage-Ziele

### 6.1 Ziel pro Modul

| Modul | Ziel | Begründung |
|-------|:----:|-----------|
| `models.py` | 90% | Kern-Geschäftslogik |
| `forms.py` | 90% | Validierung, sicherheitskritisch |
| `utils.py` | 90% | Reine Funktionen, einfach testbar |
| `services/payment_factory.py` | 95% | Kritische Provider-Auswahl |
| `services/payrexx_payment_service.py` | 85% | Payment-Logik, extern gemockt |
| `services/mock_payment_service.py` | 90% | Muss korrekt simulieren |
| `services/transaction_service.py` | 90% | State Machine, sicherheitskritisch |
| `routes.py` | 75% | Viele Branches, alle kritischen Pfade |
| `ai_services.py` | 70% | Extern gemockt, Parsing testbar |
| `gcs_utils.py` | 70% | Extern gemockt |
| `social_auth_config.py` | 60% | OAuth-Flows schwer komplett simulierbar |
| **Gesamt** | **80%** | |

### 6.2 Coverage-Reporting

```bash
# Lokal ausführen
pytest tests/unit tests/integration --cov=app --cov-report=term-missing --cov-fail-under=80

# HTML-Report generieren
pytest tests/unit tests/integration --cov=app --cov-report=html
```

---

## 7. CI/CD-Integration

### 7.1 GitHub Actions Pipeline

```yaml
# .github/workflows/tests.yml
name: Tests
on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -r requirements.txt -r requirements-test.txt
      - run: pytest tests/unit --cov=app --cov-fail-under=80

  integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_pass
          POSTGRES_DB: japanese_learning_test
        ports: ['5432:5432']
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -r requirements.txt -r requirements-test.txt
      - run: pytest tests/integration
        env:
          DATABASE_URL: postgresql://test_user:test_pass@localhost:5432/japanese_learning_test

  e2e-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_pass
          POSTGRES_DB: japanese_learning_test
        ports: ['5432:5432']
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: pip install -r requirements.txt
      - run: npm ci && npx playwright install --with-deps chromium
      - run: python tests/start_test_server.py &
      - run: npx playwright test
```

### 7.2 Qualitäts-Gates

| Gate | Kriterium | Blockiert Merge |
|------|-----------|:-:|
| Unit-Tests | Alle grün | Ja |
| Integration-Tests | Alle grün | Ja |
| Coverage | >= 80% | Ja |
| E2E-Tests | Alle grün | Ja (auf main) |

---

## 8. Umsetzungsplan

### Phase 1 — Grundgerüst (Woche 1)
- [ ] `requirements-test.txt` erstellen
- [ ] `conftest.py` mit Basis-Fixtures
- [ ] `factories.py` mit allen Factories
- [ ] `pyproject.toml` pytest-Konfiguration
- [ ] Erste Unit-Tests: Models (U-M01 bis U-M10)

### Phase 2 — Unit-Tests komplett (Woche 2)
- [ ] Forms (U-F01 bis U-F07)
- [ ] Utils (U-U01 bis U-U12)
- [ ] Payment Factory + Services (U-PF01 bis U-PS12)
- [ ] Transaction Service (U-TS01 bis U-TS09)
- [ ] AI Services (U-AI01 bis U-AI08)

### Phase 3 — Integrationstests (Woche 3-4)
- [ ] Public Routes + Auth (I-PR01 bis I-AU14)
- [ ] Lesson + Course Routes (I-LR01 bis I-CR03)
- [ ] Payment Routes + Webhooks (I-PA01 bis I-PA16)
- [ ] Admin CRUD APIs (I-AD01 bis I-AD23)
- [ ] Admin Content + Upload (I-AC01 bis I-FU06)

### Phase 4 — CI/CD + Feinschliff (Woche 5)
- [ ] GitHub Actions Pipeline
- [ ] Coverage auf >= 80% bringen
- [ ] Import/Export Tests (I-IE01 bis I-IE06)
- [ ] Security-Tests (S-01 bis S-08)

---

## 9. Risiken und Einschränkungen

| Risiko | Massnahme |
|--------|-----------|
| Payrexx-API nicht lokal testbar | HTTP-Level-Mocking mit `responses` |
| OpenAI/Gemini API-Kosten | Alle KI-Calls gemockt, keine echten API-Calls |
| Google OAuth schwer simulierbar | Pipeline-Funktionen isoliert testen |
| Grosse `routes.py` (3'679 Zeilen) | Schrittweise nach Funktionsbereich testen |
| PostgreSQL-spezifisches Verhalten | Integrationstests mit echtem PostgreSQL |

---

## Zusammenfassung

| Kennzahl | Wert |
|----------|------|
| **Testfälle Unit** | 67 |
| **Testfälle Integration** | 83 |
| **Testfälle E2E (bestehend)** | ~124 |
| **Testfälle Security** | 8 |
| **Total** | **~282** |
| **Coverage-Ziel** | 80% |
| **Geschätzte Umsetzung** | 5 Wochen |
