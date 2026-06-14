# 00 · Übersicht — Ist-Zustand der Japanese-Learning-Website
_Stand: 2026-06-14 · Commit 2947710 (origin/main) · japanese-learning.ch_

Diese Dokumentensammlung bildet den **technischen Ist-Zustand** der Plattform ab — den Aufbau der einzelnen Seiten und ihr internes Zusammenspiel. Ziel ist eine navigierbare Grundlage, um zu erkennen, **was optimiert werden sollte**. Die Dokumente beschreiben den Code, wie er ist (Commit 2947710), nicht wie er sein sollte; jede Beobachtung ist eine reine Feststellung, kein Lösungsvorschlag.

> **Methodik:** Erstellt durch acht parallele Subsystem-Analysen + einen Navigations-Graph-Scan direkt am Quellcode (Git-Worktree auf origin/main). Routen-, Zeilen- und Dateireferenzen sind als `app/datei.py:zeile` klickbar und stichprobenartig gegen den Code verifiziert.

## Was ist das Produkt?

Eine **Flask-basierte Japanisch-Lernplattform** (JLPT N5, auf Deutsch erklärt, Schweizer Anbieter). Nutzer lernen über strukturierte Lektionen (Kana, Kanji, Vokabeln, Grammatik, Quiz), wiederholen mit einem Spaced-Repetition-System (FSRS), üben Kana in zwei Spielmodi und können einzelne Lektionen oder das „N5 Komplett"-Bundle kaufen (Payrexx). Self-hosted auf einem Heim-Server (Docker + Cloudflare-Tunnel).

## High-Level-Architektur

```
   Internet
      │  HTTPS
      ▼
┌──────────────┐    cloudflared      ┌────────────────────────────────────────────┐
│  Cloudflare  │ ─── (systemd) ────► │  Docker: japanese_app  (Gunicorn, 2 Worker) │
│  Edge/HTTPS  │                     │  ┌──────────────────────────────────────┐  │
└──────────────┘                     │  │ Flask create_app()  (app/__init__.py)│  │
                                     │  │  Extensions: SQLAlchemy · Migrate ·  │  │
                                     │  │  Login · CSRF · Limiter · Talisman ·  │  │
                                     │  │  Mail                                 │  │
                                     │  │  Blueprints: routes · srs · bundle ·  │  │
                                     │  │  legal · seo · oauth · social_auth ·  │  │
                                     │  │  debug  (+ Flask-Admin /admin-panel)  │  │
                                     │  └──────────────────────────────────────┘  │
                                     └───────────┬─────────────────┬──────────────┘
                                                 │ SQLAlchemy      │ Volume-Mount
                                                 ▼                 ▼
                                     ┌────────────────────┐  app/static/uploads/
                                     │ Docker: postgres_db│  (Bilder, Audio, ~4.3 GB)
                                     │  = Produktions-DB  │
                                     └────────────────────┘

   Frontend pro Seite:  Jinja2-Templates  +  Tailwind (Play-CDN)  +  Alpine.js  +  HTMX
                        (teils jQuery-Reste) · viel Inline-CSS/JS in Grosstemplates
```

Tech-Stack im Detail: → [01 · Architektur & Infrastruktur](01-architektur-infrastruktur.md).

## Codebase in Zahlen

| Bereich | Kennzahl |
|---|---|
| Python in `app/` | ~16'663 LOC |
| Grösste Python-Datei | `app/routes.py` — 4'863 Zeilen, 129 Routen (1 Blueprint) |
| Weitere grosse Module | `models.py` 1'551 · `srs_routes.py` 1'480 · `ai_services.py` 1'210 · `srs_service.py` 1'019 |
| SQLAlchemy-Models | 25 (+ Assoziationstabelle `course_lessons`) |
| DB-Migrationen | 30 (Alembic) |
| Jinja2-Templates | 63 HTML-Dateien |
| Grösste Templates | `lesson_view.html` 4'772 · `review.html` 2'000 · `index.html` 1'372 · `stats.html` 934 · `base.html` 756 |
| CSS | `custom.css` 4'585 · `lessons.css` (Altbestand) · `mobile-improvements.css` |
| JS | `kana_grid_game.js` 1'274 · `kana_storm.js` 658 |
| Test-Dateien | 62 (`tests/`) |
| Inhalte (DB, Stand Mai 2026) | 47 Lektionen (36 published) · 3 Kurse · 1'887 Content-Items · 790 Quiz-Fragen · 519 Vokabeln · 200 Kana · 127 Grammatik · 61 Kanji |

## Blueprints (Routing-Karte)

| Blueprint | url_prefix | Datei | ~Routen | Zweck |
|---|---|---|---|---|
| `routes` | — | `app/routes.py` | 129 | Öffentliche Views, Lektionen, Quiz/Progress, **alle** `/api/admin/*`, Payment-APIs — die „Gott-Datei" |
| `srs` | — | `app/srs_routes.py` | 41 | Review/Stats/Browse-Seiten + Kana-Practice/Storm + alle SRS-/Kana-APIs |
| `bundle` | — | `app/bundle_routes.py` | 2 | `/n5-bundle`-Verkaufsseite + Buy-API |
| `legal` | `/legal` | `app/legal_routes.py` | 4 | Impressum, Datenschutz, AGB, Widerruf |
| `seo` | — | `app/seo_routes.py` | 3 | `/robots.txt`, `/sitemap.xml`, `/favicon.ico` (CSRF-exempt) |
| `oauth` | — | `app/oauth_routes.py` | 1 | Eigener Google-OAuth-Callback (`/auth/complete/google-oauth2/`) |
| `social_auth` | `/auth` | (Bibliothek) | — | social-auth-Pipeline (parallel zu `oauth`) |
| `debug` | — | `app/debug_routes.py` | 4 | Admin-only Diagnose-Endpoints |
| Flask-Admin | `/admin-panel` | `app/admin_views.py` | (auto) | Auto-CRUD-Panel für dieselben Models wie das Custom-Admin |

## Dokument-Wegweiser

| # | Dokument | Inhalt |
|---|---|---|
| 00 | **Übersicht** (dieses Dokument) | Architektur, Metriken, Wegweiser, konsolidierte Beobachtungen |
| 01 | [Architektur & Infrastruktur](01-architektur-infrastruktur.md) | App-Factory, Config/Env, Extensions, CSP, Context-Processor, Jinja-Filter, SEO/Debug-Routes, Deployment |
| 02 | [Datenmodell](02-datenmodell.md) | Alle 25 Models, Felder, Beziehungen, Geschäftslogik in `models.py`, ERD |
| 03 | [Öffentliche & Navigations-Seiten](03-oeffentliche-seiten.md) | **Aufbau** jeder Marketing-/Katalog-/Lernpfad-/Rechts-Seite |
| 04 | [Lernen: Lektionen, Inhalte & Quiz](04-lernen-lektionen-quiz.md) | Lektions-Viewer, Inhaltstypen, Quiz, Fortschritt, Klick-TTS |
| 05 | [SRS, Review, Practice & Gamification](05-srs-review-practice.md) | FSRS, Review-Loop, Statistik, Kana-Spiele, XP/Streak/Achievements |
| 06 | [Authentifizierung & Zugriffskontrolle](06-auth-zugriffskontrolle.md) | Login/Register/OAuth/Reset, Decorators, Zugriffskaskade Gast→Paid→Premium |
| 07 | [Zahlungen & Monetarisierung](07-payment-monetarisierung.md) | Payment-Factory, Payrexx/Mock/PostFinance, Bundle, Kauf-Flow, Webhook |
| 08 | [Admin & Content-Pipeline](08-admin-content-pipeline.md) | Custom-Admin + Flask-Admin, Admin-APIs, KI-Generierung, Approval-Queue |
| 09 | [Seiten-Zusammenspiel](09-seiten-zusammenspiel.md) | **Querschnitt:** Navigation, Conversion-Funnel, geteilte Zustände, Datenfluss |

**Leseempfehlung:** Für den Gesamtüberblick 00 → 09 (Zusammenspiel) → 03 (Seiten-Aufbau). Für tiefe Einzelthemen direkt das jeweilige Subsystem-Dokument.

## Konsolidierte Beobachtungen (subsystemübergreifend)

Die folgenden Muster tauchen in **mehreren** Subsystem-Dokumenten auf — sie sind die wiederkehrenden Ansatzpunkte. Jede Zeile verweist auf die Detail-Dokumente.

### A · Grosse, vermischte Dateien („Gott-Dateien")
- `app/routes.py` (4'863 Z., 129 Routen) mischt öffentliche Views, Lektions-Logik, **alle** Admin-APIs, Quiz-, Progress- und Payment-Endpoints in **einem** Blueprint ohne url_prefix. → 01, 03, 04, 06, 07, 08, 09
- `app/srs_routes.py` (1'480 Z.) bündelt 8 Seiten-Views + 33 JSON-/Hilfs-Routen (41 gesamt). → 05, 09
- `app/models.py` (1'551 Z.) vermischt Schema, Geschäftslogik (Zugriffskontrolle, Streak) und Text-Parsing (Romaji/Cloze). → 02
- `lesson_view.html` (4'772 Z.), `review.html` (2'000), `index.html` (1'372) tragen Markup + grosse Inline-CSS/JS-Blöcke. → 04, 05, 09

### B · Toter / verwaister Code
- `learn_path.html` wird von keiner Route gerendert (verifiziert). → 03, 09
- `ContentValidator`, `PersonalizedLessonGenerator`, `UserPerformanceAnalyzer` an keine Route angebunden, instanziieren aber den Gemini-Generator. → 08
- Gemini-**Text**-Content gilt laut CLAUDE.md als tot, aber `/api/admin/generate-ai-content` ruft die Methoden weiter auf. → 08
- Web-Push-Endpoints speichern Subscriptions, ein Versand-Pfad fehlt (toter Code). → 05
- `fill_in_the_blank` ist deprecated, lebt aber in Model-Kommentar, Quiz-Bewertung und KI-Generator weiter. → 02, 04, 08
- `UserLessonProgress.reset()` ist eine dritte, ungenutzte Reset-Implementierung. → 04
- PostFinance-Legacy-Code vollständig vorhanden, `entrypoint.sh` (4 Worker, `db.create_all`) nicht referenziert. → 01, 07

### C · Doppelte / parallele Implementierungen
- **Zwei** Google-OAuth-Pfade: eigener `oauth_bp`-Callback + vollständige social-auth-Pipeline mit überlappender User-Anlage. → 06
- **Drei** Payment-Factory-/`get_payment_service`-Varianten (nur `payment_factory.py` kennt Payrexx). → 07
- **Zwei** Admin-Oberflächen für dieselben Models (Custom `/admin/*` + Flask-Admin `/admin-panel`). → 08
- **Zwei** Lektions-Reset-Endpoints (JSON + Form) mit dupliziertem Raw-SQL. → 04
- **Zwei** TTS-Wege (ai_services `GoogleCloudTTS` Neural2 vs. scripts Gemini-Leda). → 08
- **Zwei** Kana-Spiele (Matching `/practice/kana` + Kana Storm) mit dupliziertem Gast/Login-Filter-Parsing. → 05, 09

### D · GCloud-/Hosting-Altlasten (trotz Self-Hosting-Umzug 2026-05)
- `is_production` prüft `K_SERVICE`/`GAE_ENV`, Dateiname `Dockerfile.cloudrun`, ProxyFix-Kommentar „Cloud Run". → 01
- `docker-compose.yml` enthält DB-Passwort im Klartext + PostFinance-Env-Vars; abweichende DB-Treiber (psycopg vs. psycopg2). → 01, 07
- `gcs_utils` greift nur bei gesetztem `GCS_BUCKET_NAME` (produktiv nicht gesetzt). → 01

### E · Datenintegrität & Modellierung
- `LessonContent.content_id` referenziert Kana/Kanji/Vocab/Grammar **ohne DB-Foreign-Key** (manuelle Typ-Auflösung); ebenso `PaymentTransaction.item_id/item_type`. → 02, 04
- `UserLessonProgress.content_progress` ist JSON in einem **Text**-Feld (kein JSON-Typ, manuelle Serialisierung). → 02, 04
- `content_type` ist ein freier `String(20)` ohne Enum/Validierung; gültige Werte nur implizit über Templates. → 02, 04
- `lesson_type` wird per SQLAlchemy-Event aus `price` abgeleitet (redundant zu price/is_purchasable). → 02, 07
- Zwei Deklarationsstile koexistieren (`Mapped`/`mapped_column` vs. klassisch `db.Column` + `__allow_unmapped__`). → 02

### F · Zeitzonen-Inkonsistenz
- Streak & `DailyReviewAggregate` rechnen in **Europe/Zurich**, `due_date`, Lockout, die Daily-Bretter (`/storm-daily`, `/daily-challenge`) und die meisten Timestamps in **UTC/Server-Zeit** — teils im selben `User`-Modell. → 02, 05, 06

### G · Sicherheit & Robustheit
- CSP enthält `unsafe-inline` + `unsafe-eval` (script-src). → 01
- Payrexx-Webhook überspringt **ohne** `PAYREXX_WEBHOOK_SECRET` die Signaturprüfung und verarbeitet den Payload ungeprüft. → 07
- `/upgrade_to_premium` / `/downgrade_from_premium` ändern `subscription_level` ohne Zahlung (als „PROTOTYPE ONLY" markiert). → 06
- Passwort-Reset-Token rein kryptografisch (kein DB-Record, innerhalb 1h mehrfach verwendbar). → 01, 06
- Social-Auth-Records werden per Raw-SQL-`INSERT` statt über das ORM angelegt. → 01, 06
- `time_spent` wird rein client-seitig berechnet und additiv verbucht (keine Server-Plausibilisierung). → 04
- N+1-Verdacht: `Lesson.is_accessible_to_user` (Query je Voraussetzung/Course), `_build_n5_path_context`. → 03, 04

### H · Sprachmix Deutsch/Englisch im UI
- Englische Flash-/Fehlertexte in `purchase_lesson_page`, `mock_payment_service` und der Login-Trigger „Login required" stehen neben sonst durchgehend deutschem UI; `view_lesson` erkennt den Login-Redirect per **Substring-Match** auf „Login required". → 06, 07

### I · Frontend-Konsistenz & SEO
- Gemischte Frontend-Stacks: `/courses` nutzt jQuery (`$.get('/api/courses')`), neuere Seiten Alpine.js. → 03
- `/courses` rendert das Grid client-seitig (Initial-HTML = Spinner) — Soft-404-/SEO-Muster, während `/lessons` voll SSR ist. → 03

---
_Generiert als Ist-Zustand-Momentaufnahme. Bei Code-Änderungen veralten Zeilenreferenzen — Commit-Stand 2947710 im Kopf jedes Dokuments beachten._
