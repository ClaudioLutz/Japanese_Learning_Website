# 01 · Architektur & Infrastruktur
_Stand: 2026-06-14 · Commit 2947710 · Teil der Ist-Zustand-Dokumentation_

## Zweck
Dieses Subsystem deckt das Fundament der Flask-Anwendung ab: die App-Factory `create_app()` mit ihrer gesamten Konfiguration (Env-Variablen, Extensions, Security-Header, Blueprint-Registrierung, Jinja-Filter und global an Templates injizierte Variablen), die Querschnitts-Hilfsmodule (Mail, Auth-Tokens, JLPT-Konvertierung, GCS, Datei-Upload) sowie die Deployment-Topologie (Docker, Gunicorn, Entrypoint, self-hosted hinter Cloudflare-Tunnel). Es beschreibt, wie die App gebaut, gestartet und verdrahtet wird — nicht die fachlichen Routen selbst.

## Komponenten

| Datei | Zeilen | Rolle |
|---|---|---|
| `app/__init__.py` | 499 | App-Factory `create_app()`: Config, Extensions, CSP, Blueprints, Context-Processor, Jinja-Filter |
| `app/seo_routes.py` | 178 | Blueprint `seo`: `/favicon.ico`, `/robots.txt`, `/sitemap.xml` |
| `app/debug_routes.py` | 187 | Blueprint `debug` (`/debug`): Admin-only Diagnose-Endpoints (Payment/DB/Env) |
| `app/mail_service.py` | 39 | Flask-Mail-Instanz + `send_password_reset_email()` |
| `app/auth_tokens.py` | 18 | Signierte Passwort-Reset-Tokens (itsdangerous) |
| `app/jlpt_utils.py` | 152 | JLPT-/Difficulty-Level-Konvertierung + `truncate_field()` |
| `app/gcs_utils.py` | 74 | Google-Cloud-Storage-Helfer (Upload/Delete/Exists) |
| `app/utils.py` | 308 | `FileUploadHandler` (Upload/Validierung/Bildverkleinerung) + `convert_to_embed_url()` |
| `app/social_auth_config.py` | 127 | Google-OAuth-Pipeline-Funktionen (uid-Fix, User-Anlage, Login) |
| `run.py` | 41 | Entry Point: `app = create_app()`, Dev-Server + `flask db_*`-CLI-Befehle |
| `Dockerfile.cloudrun` | 44 | Produktions-Image (python:3.12-slim, Gunicorn) |
| `docker-compose.yml` | 43 | Basis-Compose (web + db PostgreSQL 15) |
| `docker-compose.override.yml` | 28 | Heim-Server-Overrides (Dockerfile.cloudrun, `.env`, Volumes, restart) |
| `entrypoint-cloud-run.sh` | 86 | Aktiver Entrypoint: DB-Warteschleife, `flask db upgrade`, Gunicorn |
| `entrypoint.sh` | 33 | Alternativer/älterer Entrypoint (`db.create_all` + `db stamp head`) |

---

## App-Factory `create_app()` (`app/__init__.py:31`)

### Pflicht-Env (Abbruch beim Start, wenn fehlend)
- **`SECRET_KEY`** (`app/__init__.py:37-42`): ohne gültigen Key `RuntimeError`. Dient Sessions, CSRF und den Reset-Tokens.
- **`DATABASE_URL`** (`app/__init__.py:88-94`): ohne URL `RuntimeError`. Kein Fallback. Bei `sqlite`-URLs wird `connect_args.timeout=20` gesetzt (`:97-100`).

### Modul-globale Extensions (`app/__init__.py:21-25`)
Die Extension-Objekte werden auf Modulebene angelegt und in der Factory via `init_app(app)` gebunden (`:178-184`):

| Extension | Objekt | Konfig | Init |
|---|---|---|---|
| SQLAlchemy | `db` | `SQLALCHEMY_DATABASE_URI` | `db.init_app(app)` |
| Flask-Migrate | `migrate` | — | `migrate.init_app(app, db)` |
| Flask-Login | `login_manager` | `login_view='routes.login'`, deutsche Login-Message | `login_manager.init_app(app)` |
| Flask-WTF CSRF | `csrf` | `WTF_CSRF_SECRET_KEY` | `csrf.init_app(app)` |
| Flask-Limiter | `limiter` | Key=`get_remote_address`, Default-Limit `200 per hour` | `limiter.init_app(app)` |
| Flask-Mail | `mail` (aus `mail_service`) | MAIL_*-Keys | `mail.init_app(app)` |
| Flask-Talisman | (lokal in Factory) | CSP, `force_https=is_production` | `Talisman(app, ...)` (`:217-223`) |

### ProxyFix (`app/__init__.py:35`)
`ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)` — vertraut den Forwarded-Headern des vorgelagerten Proxys (Cloudflare/Loadbalancer), damit Flask HTTPS und korrekte `redirect_uri` für OAuth sieht.

### `is_production`-Erkennung (`app/__init__.py:75-79`)
Wahr, wenn eine der Bedingungen zutrifft: `FLASK_ENV == 'production'` ODER `K_SERVICE` gesetzt (Cloud Run) ODER `GAE_ENV` beginnt mit `standard`. Steuert: Session-/Remember-Cookie `Secure`, Talisman `force_https`, Talisman `session_cookie_secure`.

### Alle `app.config`-Keys

| Config-Key | Quelle / Env | Default | Zeile |
|---|---|---|---|
| `SECRET_KEY` | `SECRET_KEY` | (Pflicht) | `:43` |
| `WTF_CSRF_SECRET_KEY` | `WTF_CSRF_SECRET_KEY` | = `SECRET_KEY` | `:44` |
| `GCS_BUCKET_NAME` | `GCS_BUCKET_NAME` | `None` | `:45` |
| `SITE_URL` | `SITE_URL` | `https://japanese-learning.ch` (rstrip `/`) | `:48` |
| `SITE_NAME` | `SITE_NAME` | `Japanese Learning` | `:49` |
| `SITE_DESCRIPTION` | `SITE_DESCRIPTION` | langer Default-Marketingtext | `:50-55` |
| `SEO_DEFAULT_OG_IMAGE` | `SEO_DEFAULT_OG_IMAGE` | `/static/images/og-image.png` | `:56-59` |
| `GOOGLE_SITE_VERIFICATION` | `GOOGLE_SITE_VERIFICATION` | `''` | `:61` |
| `ROBOTS_INDEX` | `ROBOTS_INDEX` | `index,follow` | `:63` |
| `PLAUSIBLE_DOMAIN` | `PLAUSIBLE_DOMAIN` | `None` | `:66` |
| `TEMPLATES_AUTO_RELOAD` | hardcoded | `True` | `:69` |
| `SEND_FILE_MAX_AGE_DEFAULT` | hardcoded | `31536000` (1 Jahr) | `:72` |
| `SESSION_COOKIE_HTTPONLY` | hardcoded | `True` | `:80` |
| `SESSION_COOKIE_SAMESITE` | hardcoded | `Lax` | `:81` |
| `SESSION_COOKIE_SECURE` | abgeleitet | `is_production` | `:82` |
| `REMEMBER_COOKIE_HTTPONLY` | hardcoded | `True` | `:83` |
| `REMEMBER_COOKIE_SAMESITE` | hardcoded | `Lax` | `:84` |
| `REMEMBER_COOKIE_SECURE` | abgeleitet | `is_production` | `:85` |
| `SQLALCHEMY_DATABASE_URI` | `DATABASE_URL` | (Pflicht) | `:94` |
| `SQLALCHEMY_ENGINE_OPTIONS` | nur bei SQLite | `{connect_args:{timeout:20}}` | `:98-100` |
| `SOCIAL_AUTH_GOOGLE_OAUTH2_KEY` | `GOOGLE_CLIENT_ID` | — | `:104` |
| `SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET` | `GOOGLE_CLIENT_SECRET` | — | `:105` |
| `SOCIAL_AUTH_*` (Scope, PKCE, Pipeline …) | hardcoded | s. Social-Auth-Abschnitt | `:103-124` |
| `MAIL_SERVER` | `MAIL_SERVER` | `asmtp.mail.hostpoint.ch` | `:138` |
| `MAIL_PORT` | `MAIL_PORT` | `587` | `:139` |
| `MAIL_USE_TLS` | `MAIL_USE_TLS` | `true` | `:140` |
| `MAIL_USE_SSL` | `MAIL_USE_SSL` | `false` | `:141` |
| `MAIL_USERNAME` | `MAIL_USERNAME` | — | `:142` |
| `MAIL_PASSWORD` | `MAIL_PASSWORD` | — | `:143` |
| `MAIL_DEFAULT_SENDER` | `MAIL_DEFAULT_SENDER` | `Japanese Learning <info@japanese-learning.ch>` | `:144-147` |
| `MAIL_SUPPRESS_SEND` | `MAIL_SUPPRESS_SEND` | `false` | `:148` |
| `PAYMENT_PROVIDER` | `PAYMENT_PROVIDER` | `mock` | `:151` |
| `PAYREXX_INSTANCE` | `PAYREXX_INSTANCE` | — | `:152` |
| `PAYREXX_API_SECRET` | `PAYREXX_API_SECRET` | — | `:153` |
| `PAYREXX_WEBHOOK_SECRET` | `PAYREXX_WEBHOOK_SECRET` | — | `:154` |
| `UPLOAD_FOLDER` | abgeleitet (`<root>/app/static/uploads`) | — | `:127-128`, `:156` |
| `MAX_CONTENT_LENGTH` | hardcoded | `100 * 1024 * 1024` (100 MB) | `:130`, `:157` |
| `ALLOWED_EXTENSIONS` | hardcoded | image/video/audio-Mengen | `:131-135`, `:158` |
| `CONTENT_LANGUAGES` | `CONTENT_LANGUAGES` | `['german']` (CSV-Split) | `:163-166` |

Zusätzlich wird `config.py` aus dem Instance-Ordner mit `from_pyfile('config.py', silent=True)` geladen (`:68`) — überschreibt ggf. obige Werte, falls vorhanden.

### Upload-Verzeichnisse
`UPLOAD_FOLDER` = `<project_root>/app/static/uploads`. Beim Start werden die Unterordner `lessons/images`, `lessons/videos`, `lessons/audio`, `temp` per `os.makedirs(..., exist_ok=True)` angelegt (`app/__init__.py:168-176`).

### CSP-Policy (Talisman, `app/__init__.py:187-223`)
`content_security_policy_nonce_in=[]` (keine Nonces). Erlaubte externe Hosts:

| Direktive | Erlaubte Quellen |
|---|---|
| `default-src` | `'self'` |
| `script-src` | `'self'`, `'unsafe-inline'`, `'unsafe-eval'`, `cdn.jsdelivr.net`, `cdn.tailwindcss.com`, `cdn.tiny.cloud`, `cdnjs.cloudflare.com`, `code.jquery.com`, `unpkg.com` |
| `style-src` | `'self'`, `'unsafe-inline'`, `cdn.jsdelivr.net`, `cdn.tailwindcss.com`, `cdnjs.cloudflare.com`, `fonts.googleapis.com` |
| `font-src` | `'self'`, `cdnjs.cloudflare.com`, `fonts.gstatic.com` |
| `img-src` | `'self'`, `data:`, `blob:`, `storage.googleapis.com` |
| `media-src` | `'self'`, `blob:`, `storage.googleapis.com` |
| `connect-src` | `'self'` |

### Blueprint-Registrierung (Reihenfolge wie im Code)
Registriert in `create_app()` zwischen `:258` und `:371`:

1. `routes.bp` (`:258`)
2. `oauth_bp` (`:262`) — bewusst **vor** social-auth, um dessen Callback zu überschreiben
3. `srs_bp` (`:266`)
4. `debug_bp` (`:270`)
5. `legal_bp` (`:275`)
6. `seo_bp` (`:279`) + `csrf.exempt(seo_bp)` (`:280`)
7. `bundle_bp` (`:284`)
8. `social_auth` (aus `social_flask.routes`) mit `url_prefix='/auth'` (`:371`)

Error-Handler für 404/500 rendern eigene deutsche Templates (`errors/404.html`, `errors/500.html`; `:288-293`). Flask-Admin wird ganz am Ende via `init_admin(app, db.session)` registriert (`:496-497`).

### Blueprint-Übersicht

| Blueprint | url_prefix | Datei | Routen | Zweck |
|---|---|---|---|---|
| `routes` (`bp`) | — | `app/routes.py` | 129 | Haupt-Views + die meisten API-Endpoints (Gott-Datei, 4'863 Zeilen) |
| `srs` (`srs_bp`) | — (Pfade selbst `/api/srs/…`, `/review`) | `app/srs_routes.py` | 41 | Spaced-Repetition-System: Bewertungen, Fälligkeiten, Stats, Heatmap, Retention |
| `oauth` (`oauth_bp`) | `/auth` | `app/oauth_routes.py` | 1 | Eigener Google-OAuth-Callback `/auth/complete/google-oauth2/` |
| `debug` (`debug_bp`) | `/debug` | `app/debug_routes.py` | 4 | Admin-only Diagnose (Payment-Config, Mock-/Factory-Purchase, Env-Info) |
| `legal` (`legal_bp` als `bp`) | `/legal` | `app/legal_routes.py` | 4 | Impressum, Datenschutz, AGB, Widerruf |
| `seo` (`seo_bp`) | — | `app/seo_routes.py` | 3 | favicon.ico, robots.txt, sitemap.xml (CSRF-exempt) |
| `bundle` (`bundle_bp`) | — | `app/bundle_routes.py` | 2 | N5-Bundle-Verkaufsseite (`/n5-bundle`) + Buy-API |
| `social_auth` (extern) | `/auth` | `social_flask.routes` | — | social-auth-app-django/-flask Standard-Login-Route |

(Routen-Anzahl = Anzahl `@<bp>.route`-Dekoratoren je Datei.)

### Context-Processor `_inject_common_template_vars` (`app/__init__.py:299-352`)
Liefert global an **alle** Templates folgende Variablen:

| Variable | Bedeutung |
|---|---|
| `current_year` | `datetime.utcnow().year` — Footer-Copyright |
| `site_url` | `app.config['SITE_URL']` |
| `site_name` | `app.config['SITE_NAME']` |
| `site_description` | `app.config['SITE_DESCRIPTION']` |
| `default_og_image` | OG-Bild-URL; relative `/`-Pfade werden mit `site_url` zur Vollurl gemacht |
| `google_site_verification` | Search-Console-Meta-Token (oder leer) |
| `robots_index` | `index,follow` bzw. `noindex,nofollow` |
| `default_canonical` | `site_url + request.path` (Fallback `site_url` ausserhalb Request-Kontext) |
| `n5_free_lesson_count` | Zahl gratis Gast-Lektionen: `is_published & allow_guest_access & lesson_type='free'`, Summe über `instruction_language` `english` + `german`. Bei Fehler `0`. Single Source für Marketing-Texte |
| `show_bundle_hint` | `user_needs_bundle_hint(current_user)` aus `bundle_service`; **fail-open auf `True`** bei jeder Exception (Error-Pages brechen nicht) |

### Jinja-Filter / -Globals

| Name | Typ | Definition | Zweck |
|---|---|---|---|
| `to_embed_url` | Filter | `:243` (→ `utils.convert_to_embed_url`) | YouTube-URL → Embed-URL |
| `from_json` | Filter | `:247-255` | JSON-String → Liste (`[]` bei Fehler) |
| `nl2br` | Filter | `:375-379` | Newlines → `<br>` (escaped) |
| `fromjson` | Filter | `:383-390` | JSON-String → dict/`None` (für dialog_slideshow) |
| `markdown_safe` | Filter | `:406-418` | Markdown → bereinigtes Block-HTML (bleach-Whitelist, linkify) |
| `markdown_inline` | Filter | `:427-440` | Markdown inline (nur `strong/em/b/i/code/span/br`, `<p>` gestrippt) |
| `highlight_vocab` | Filter | `:445-465` | Markiert Zielwort im JP-Beispielsatz (`word`→`reading`→`reading[:-1]`) |
| `highlight_romaji` | Filter | `:474-493` | Markiert Zielwort-Romaji im Satz-Romaji (`\b`-Match, case-insensitiv) |
| `static_v` | Global | `:360-367` | Cache-Busting: hängt Datei-mtime als `?v=<mtime>` an statische URLs |

Markdown-Filter nutzen zwei separate `markdown.Markdown`-Instanzen: Block (`extra`, `sane_lists`, `nl2br`; Whitelist u.a. `h2-h4`, `p`, `ul/ol/li`, `blockquote`, `code`, `a`) und Inline (`extra`).

### Social-Auth-Pipeline (`app/__init__.py:116-123`, Logik in `app/social_auth_config.py`)
Reihenfolge:
1. `social_core.pipeline.social_auth.social_details`
2. `social_core.pipeline.social_auth.social_uid`
3. `app.social_auth_config.fix_google_uid` — setzt uid auf Googles `sub`-Feld statt E-Mail (`social_auth_config.py:9-18`)
4. `social_core.pipeline.social_auth.auth_allowed`
5. `app.social_auth_config.create_user_and_login` — loggt bestehenden User ein, verknüpft per E-Mail oder legt neuen `User` an (`subscription_level='free'`, `password_hash=''`), garantiert eindeutigen Username (`:77-127`)
6. `app.social_auth_config.custom_associate_user` — legt `social_auth_usersocialauth`-Record per **Raw-SQL-INSERT** an, falls noch nicht vorhanden (`:20-75`)

Konfig: Backend `GoogleOAuth2`, Scope `openid/email/profile`, PKCE aktiv, `USER_ID_KEY='sub'`, Storage `social_flask_sqlalchemy.models.FlaskStorage`. In der Factory wird zudem `UserSocialAuth.app_session = db.session` gesetzt (`:230-231`). Eine `before_request`-Funktion legt `g.user = current_user` (oder `None`) für die social-auth-Integration ab (`:236-240`).

---

## SEO-Routes (`app/seo_routes.py`)

| Route | Funktion | Inhalt |
|---|---|---|
| `/favicon.ico` | `favicon_ico` (`:21`) | liefert `favicon.ico` aus dem static-Ordner (Bots fragen Root-Pfad ab) |
| `/robots.txt` | `robots_txt` (`:33`) | Crawl-Direktiven, von `ROBOTS_INDEX` gesteuert |
| `/sitemap.xml` | `sitemap_xml` (`:89`) | dynamische Sitemap aus DB |

**robots.txt-Steuerung** (`:34-72`): Enthält `ROBOTS_INDEX` (lowercase) den String `noindex`, wird stur `User-agent: *\nDisallow: /` zurückgegeben (Staging-Sperre). Sonst Disallow für `/admin`, `/admin-panel`, `/api/`, `/auth/`, `/logout`, `/profile`, `/my-lessons`, `/review`, `/practice`, `/payment/`, `/purchase/`, `/debug/`, `/healthz`, `/health`; explizit `Allow: /practice/kana$` (nur exakt diese Seite, nicht `/practice/kana/spiel`) und `Allow: /`. Sitemap-Verweis am Ende.

**sitemap.xml** (`:89-178`): liest `CONTENT_LANGUAGES`. Enthält:
- Statische Seiten (Prioritäten 0.2–1.0): `/`, `/n5-bundle`, `/jlpt-n5-schweiz`, `/lessons`, `/practice/kana`, optional `/courses` (nur wenn ≥1 publizierter Kurs), `/ueber`, `/lernmethode`, die vier `/legal/*`-Seiten.
- Publizierte Lessons mit `is_published & allow_guest_access` in aktivierter Sprache → `/lessons/<id>` (Paid-Lessons werden bewusst **nicht** gelistet).
- JLPT-Modul-Detailseiten `/learn/n<level>/<slug>` nur für Module mit ≥2 publizierten Lessons in sichtbaren Sprachen.
- Publizierte Courses → `/course/<id>`.

---

## Debug-Routes (`app/debug_routes.py`, Prefix `/debug`)
Alle vier Endpoints sind `@login_required` UND prüfen `current_user.is_admin` (sonst `403`). Sie geben Diagnose-JSON aus:

| Route | Preisgegebene Information |
|---|---|
| `/debug/payment-config` (`:13`) | Env-Vars als `SET`/`NOT_SET` (Werte werden maskiert ausser `MOCK_PAYMENTS_ENABLED`, `FLASK_ENV`), Flask-Config-Status, Payment-Service-Klasse, DB-Connectivity-Test, User-ID/Admin-Flag |
| `/debug/test-mock-purchase/<lesson_id>` (`:89`) | führt `MockPaymentService.create_lesson_transaction` aus, gibt Ergebnis zurück |
| `/debug/test-factory-purchase/<lesson_id>` (`:127`) | wie oben, aber über die Payment-Factory |
| `/debug/environment-info` (`:166`) | Python-Version, Plattform, CWD, Anzahl Env-Vars, **vollständige Liste aller Flask-Config-Keys**, instance/root-path |

Sensible Werte (Secrets, Connection-Strings) werden konsequent als `SET`/`NOT_SET` ausgegeben, nicht im Klartext.

---

## Querschnitts-Hilfsmodule

### `app/mail_service.py`
Stellt die `Mail`-Instanz bereit (in Factory `init_app`'d). Einzige Funktion: `send_password_reset_email(to_email, reset_link, username)` (`:11`) — rendert `email/reset_password.html` + `.txt`, sendet via Flask-Mail. Fängt alle Exceptions ab, loggt und gibt `False` zurück (Enumeration-Schutz: kein Leak an den Benutzer).

### `app/auth_tokens.py`
Signierte, zeitbegrenzte Passwort-Reset-Tokens via `itsdangerous.URLSafeTimedSerializer` mit Salt `pwd-reset-v1` und `SECRET_KEY`. `make_reset_token(user_id)` (`:8`) und `verify_reset_token(token, max_age=3600)` (`:13`, Default 1 h; gibt `None` bei ungültig/abgelaufen).

### `app/jlpt_utils.py`
Reine Konvertierungs-/Validierungshelfer ohne DB-Zugriff: `convert_jlpt_level_to_int` (`N4`→`4`, Fallback `5`), `convert_int_to_jlpt_level` (`4`→`N4`, Fallback `N5`), `validate_jlpt_level`, `convert_difficulty_to_int`/`convert_int_to_difficulty_level` (Beginner↔1 … Expert↔5), `validate_difficulty_level`, `truncate_field(text, max_length)` (mit `...`-Ellipse für DB-Feldlängen).

### `app/gcs_utils.py`
Google-Cloud-Storage-Wrapper. Bucket aus `current_app.config['GCS_BUCKET_NAME']`. Funktionen: `get_gcs_client`, `get_bucket_name`, `upload_file_to_gcs` (gibt Public-URL `https://storage.googleapis.com/<bucket>/<blob>` zurück), `delete_file_from_gcs`, `file_exists_in_gcs`. Laut CLAUDE.md ist `GCS_BUCKET_NAME` in Produktion **nicht** gesetzt → diese Pfade greifen aktuell nicht (Bucket nur Offsite-Backup).

### `app/utils.py`
Zwei Bestandteile:
- `convert_to_embed_url(youtube_url)` (`:9`): YouTube watch/youtu.be → Embed-URL (best effort, gibt Original bei Fehler).
- `FileUploadHandler` (`:44`, Static-Methoden): `allowed_file`/`get_file_type` (gegen `ALLOWED_EXTENSIONS`), `generate_unique_filename` (UUID-8-Suffix), `create_lesson_directory`, `validate_file_content` (python-magic MIME-Check mit Extension-Fallback), `process_image` (Pillow: RGB-Konvert, Resize max 1920×1080, JPEG q85), `get_file_info`, `format_file_size`, `delete_file`, `get_supported_formats`, `save_file` (Temp→Validierung→Bildverarbeitung→GCS *falls* Bucket gesetzt, sonst lokal verschieben; gibt relativen Pfad zurück).

---

## Deployment-Topologie

### Image-Build (`Dockerfile.cloudrun`)
`python:3.12-slim-bookworm`, WORKDIR `/app`. System-Pakete: `libmagic1`, `build-essential`, `libpq-dev`, `postgresql-client`. Installiert `requirements.txt`. Kopiert Code, entfernt CRLF aus `entrypoint-cloud-run.sh` (`sed -i 's/\r$//'`), macht es ausführbar. Legt Non-Root-User `app` an. Setzt `PORT=8080`, `FLASK_APP=run.py`, `FLASK_ENV=production`. `ENTRYPOINT ["/entrypoint-cloud-run.sh"]`.

### Aktiver Entrypoint (`entrypoint-cloud-run.sh`)
1. liest `PORT` (Default `8080`).
2. **DB-Warteschleife** (30 Versuche × 2 s): testet `psycopg2.connect`, entfernt vorher das SQLAlchemy-Treiber-Suffix `postgresql+psycopg2://` → `postgresql://`. Läuft bei Timeout trotzdem weiter (`set -e` ist deaktiviert).
3. **Migrationen**: `flask_migrate.upgrade()` in App-Context; bei Fehler Fallback `db.create_all()`.
4. Startet Gunicorn: `--workers 2 --worker-class sync --timeout 300 --keep-alive 2`, bindet `0.0.0.0:$PORT`, Access-/Error-Log nach stdout, `run:app`.

### Alternativer Entrypoint (`entrypoint.sh`)
Älterer/abweichender Pfad: wartet via `psql` auf `db`, ruft `db.create_all()` und `flask db stamp head`, startet `gunicorn -w 4 -b 0.0.0.0:5000 run:app`. Wird vom Dockerfile.cloudrun nicht referenziert.

### Compose
- **`docker-compose.yml`**: Service `web` (`build: .`, Container `japanese_app`, DATABASE_URL mit `psycopg`-Treiber auf Host `db`, Port `5000:5000`, `depends_on: db healthy`) und `db` (`postgres:15-alpine`, Container `postgres_db`, Volume `postgres_data`, Healthcheck `pg_isready`, Port `5432:5432`).
- **`docker-compose.override.yml`** (auto-geladen, Heim-Server): überschreibt `web` auf `Dockerfile.cloudrun`, lädt `.env` via `env_file`, setzt `PORT=5000` und **`DATABASE_URL` auf `psycopg2`-Treiber** (Override, da `requirements.txt` `psycopg2-binary` statt psycopg v3 hat), `restart: unless-stopped`, Volume-Mounts für `app/static/uploads` und `app/static/cache/tts`. `db` ebenfalls `restart: unless-stopped`.

### Dev-Server (`run.py`)
`app = create_app()`, `Migrate(app, db)`, CLI-Befehle `db_init/db_migrate/db_upgrade/db_downgrade`. `app.run(debug=True, use_reloader=True, reloader_type='stat')` für den lokalen Betrieb.

### Self-Hosting (Quelle: CLAUDE.md, nicht im Code dieses Subsystems)
Produktiv läuft die App self-hosted auf dem Heim-Server (`hp-ubuntu`): `Internet → Cloudflare (HTTPS-Edge) → cloudflared-Tunnel (systemd) → Container japanese_app (Gunicorn :5000) → postgres_db`. Kein GCloud-Hosting mehr. Container haben `restart: unless-stopped` + Docker-Autostart.

---

## Zusammenspiel
- **Eingang**: Sämtliche Requests laufen durch `ProxyFix` → Talisman (Security-Header/CSP) → das passende Blueprint. Alle anderen Subsysteme (Lessons, Review/SRS, Bundle, Legal, Auth) sind als Blueprints in `create_app()` registriert; ihre Routen werden hier verdrahtet.
- **Templates**: Jedes gerenderte Template bezieht die Context-Processor-Variablen (`site_url`, `robots_index`, `n5_free_lesson_count`, `show_bundle_hint` …) und die Jinja-Filter (`markdown_safe`, `highlight_vocab`, `static_v` …) aus diesem Subsystem. `base.html` lädt darüber Meta-Tags, JSON-LD und das Plausible-Script (nur wenn `PLAUSIBLE_DOMAIN` gesetzt).
- **Auth**: Google-OAuth nutzt die Pipeline (`social_auth_config`) + den eigenen `oauth_bp`-Callback. Passwort-Reset nutzt `auth_tokens` (Token) + `mail_service` (Versand) — beide hängen am `SECRET_KEY` bzw. den MAIL_*-Configs.
- **Payment**: `PAYMENT_PROVIDER`/`PAYREXX_*`-Configs werden von der Payment-Factory und `bundle_bp` gelesen; `debug_bp` inspiziert dieselbe Factory.
- **SEO**: `seo_bp` zieht Lessons/Courses/Module direkt aus der DB (Models `Lesson`, `Course`, `LessonCategory`) und spiegelt die `CONTENT_LANGUAGES`-/`ROBOTS_INDEX`-Config.
- **Ausgehend**: CSP erlaubt externe CDNs (jsDelivr, Tailwind, TinyMCE, Cloudflare, jQuery, unpkg, Google Fonts) sowie Medien/Bilder von `storage.googleapis.com`. GCS-Helper können (bei gesetztem Bucket) zu Google Cloud Storage hoch-/runterladen.

---

## Beobachtungen (Ansatzpunkte)
- `app/routes.py` ist 4'863 Zeilen lang und bündelt 129 Routen (Views + die meisten API-Endpoints) in einem Blueprint; mehrere Kommentare in `seo_routes.py`/`bundle_routes.py` bezeichnen es ausdrücklich als „Gott-Datei".
- Die App enthält zwei Entrypoint-Skripte (`entrypoint-cloud-run.sh` aktiv, `entrypoint.sh` mit abweichender DB-Init-Logik und 4 statt 2 Workern); nur das erste wird vom `Dockerfile.cloudrun` referenziert.
- `docker-compose.yml` und der Override setzen unterschiedliche `DATABASE_URL`-Treiber (`postgresql+psycopg://` vs. `postgresql+psycopg2://`); der Override existiert genau, um diese Diskrepanz zu korrigieren.
- Diverse Konfiguration referenziert noch gelöschte GCloud-Infrastruktur: `is_production` prüft `K_SERVICE`/`GAE_ENV` (Cloud Run / App Engine), Dateiname `Dockerfile.cloudrun`, ProxyFix-Kommentar „Cloud Run / Loadbalancer", obwohl laut CLAUDE.md self-hosted.
- `debug_routes` referenziert PostFinance-Env-Vars (`POSTFINANCE_*`), obwohl der Provider laut CLAUDE.md auf Payrexx umgestellt ist; `docker-compose.yml` enthält Platzhalter-PostFinance-Credentials. (`social_auth_config` betrifft ausschliesslich Google-OAuth, kein Payment.)
- `/debug/environment-info` listet die vollständige Liste aller Flask-Config-Schlüssel (nur Schlüssel, keine Werte) — Endpoint ist Admin-geschützt und in robots.txt unter `/debug/` gesperrt.
- CSP enthält `'unsafe-inline'` und `'unsafe-eval'` in `script-src` sowie `'unsafe-inline'` in `style-src`.
- `show_bundle_hint` und `n5_free_lesson_count` im Context-Processor sind fail-safe: bei jeder Exception wird `True` bzw. `0` zurückgegeben, damit Renders ausserhalb voller Request-Kontexte (Error-Pages) nicht brechen.
- `custom_associate_user` (`social_auth_config.py`) legt Social-Auth-Records per Raw-SQL-INSERT statt über das ORM an.
- `docker-compose.yml` enthält im Klartext das DB-Passwort `JapaneseApp2025!` (gleiches Passwort auch in CLAUDE.md dokumentiert).
- `gcs_utils.py` und der GCS-Pfad in `utils.save_file` bleiben im Code, greifen aber nur bei gesetztem `GCS_BUCKET_NAME` — laut CLAUDE.md produktiv nicht gesetzt.
