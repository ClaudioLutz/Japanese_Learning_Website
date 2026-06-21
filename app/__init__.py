# app/__init__.py
import logging
import re
logging.basicConfig(level=logging.INFO)
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
import os
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per hour"])

login_manager.login_view = 'routes.login' # type: ignore
login_manager.login_message = 'Bitte melden Sie sich an, um diese Seite zu sehen.'
login_manager.login_message_category = 'info'

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    # ProxyFix: Cloud Run / Loadbalancer leitet HTTPS-Traffic als HTTP weiter.
    # Ohne ProxyFix sieht Flask nur http:// und OAuth redirect_uri stimmt nicht.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    # SECRET_KEY ist Pflicht — ohne gültigen Key keine Sessions/CSRF
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        raise RuntimeError(
            "SECRET_KEY ist nicht gesetzt! "
            "Bitte in .env definieren: SECRET_KEY=\"<zufälliger Key>\""
        )
    app.config['SECRET_KEY'] = secret_key
    app.config['WTF_CSRF_SECRET_KEY'] = os.environ.get('WTF_CSRF_SECRET_KEY', secret_key)
    app.config['GCS_BUCKET_NAME'] = os.environ.get('GCS_BUCKET_NAME') or None

    # SEO-Konfiguration (von base.html / robots.txt / sitemap.xml gelesen)
    app.config['SITE_URL'] = os.environ.get('SITE_URL', 'https://japanese-learning.ch').rstrip('/')
    app.config['SITE_NAME'] = os.environ.get('SITE_NAME', 'Japanese Learning')
    app.config['SITE_DESCRIPTION'] = os.environ.get(
        'SITE_DESCRIPTION',
        'Japanisch lernen online — JLPT-N5-Kurse mit Hiragana, Katakana, Kanji, Vokabeln, '
        'Grammatik und Spaced-Repetition-Quiz. Strukturierte Lernplattform aus der Schweiz, '
        'auf Deutsch erklärt, kostenlos starten.'
    )
    app.config['SEO_DEFAULT_OG_IMAGE'] = os.environ.get(
        'SEO_DEFAULT_OG_IMAGE',
        '/static/images/og-image.png'
    )
    # Search-Console Meta-Verifikation (Fallback, falls DNS-TXT nicht möglich)
    app.config['GOOGLE_SITE_VERIFICATION'] = os.environ.get('GOOGLE_SITE_VERIFICATION', '')
    # Crawler-Steuerung: in Staging auf "noindex,nofollow" setzen, in Prod leer/Default lassen
    app.config['ROBOTS_INDEX'] = os.environ.get('ROBOTS_INDEX', 'index,follow')
    # Analytics: Plausible (cookieless). Nur wenn gesetzt, laedt base.html das
    # echte Script — sonst bleibt nur der window.plausible()-Stub aktiv (kein Tracking).
    app.config['PLAUSIBLE_DOMAIN'] = os.getenv('PLAUSIBLE_DOMAIN')

    # FREE_MODE: schaltet die berechnete Bezahl-Schicht (Bundle-Verkauf/-Hinweise,
    # hartkodierte CHF-CTAs, Kauf-Rechtstexte, Sitemap-Verkaufsseiten) ab. Die
    # eigentliche Lesson-/Course-Freischaltung laeuft ueber price==0 in der DB;
    # dieses Flag deckt nur die Flaechen, die NICHT aus price abgeleitet sind.
    # Reversibel: Flag aus + Preis-Restore -> Monetarisierung lebt wieder.
    # Default AUS, damit Tests den monetarisierten Pfad weiter exerzieren.
    app.config['FREE_MODE'] = os.environ.get('FREE_MODE', 'false').lower() == 'true'

    app.config.from_pyfile('config.py', silent=True) # Load config from instance folder
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    # Statische Assets 1 Jahr cachen — eigene Dateien sind per static_v() (mtime-?v=)
    # cache-gebustet, daher kein Stale-Risiko (Cloudflare HIT statt REVALIDATED).
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000

    # Session-Cookie-Security
    is_production = (
        os.environ.get('FLASK_ENV') == 'production'
        or os.environ.get('K_SERVICE')  # Cloud Run
        or os.environ.get('GAE_ENV', '').startswith('standard')  # App Engine
    )
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = is_production
    app.config['REMEMBER_COOKIE_HTTPONLY'] = True
    app.config['REMEMBER_COOKIE_SAMESITE'] = 'Lax'
    app.config['REMEMBER_COOKIE_SECURE'] = is_production
    
    # DATABASE_URL ist Pflicht
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        raise RuntimeError(
            "DATABASE_URL ist nicht gesetzt! "
            "Bitte in .env definieren."
        )
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url

    # SQLite: busy timeout setzen um "database is locked" zu vermeiden
    if db_url.startswith('sqlite'):
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'connect_args': {'timeout': 20}
        }

    # Google OAuth Configuration
    app.config.update({
        'SOCIAL_AUTH_GOOGLE_OAUTH2_KEY': os.environ.get('GOOGLE_CLIENT_ID'),
        'SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET': os.environ.get('GOOGLE_CLIENT_SECRET'),
        'SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE': ['openid', 'email', 'profile'],
        'SOCIAL_AUTH_GOOGLE_OAUTH2_USE_PKCE': True,
        'SOCIAL_AUTH_GOOGLE_OAUTH2_USER_ID_KEY': 'sub',  # Use Google's 'sub' field as the uid instead of email
        'SOCIAL_AUTH_LOGIN_REDIRECT_URL': '/mein-lernen',
        'SOCIAL_AUTH_LOGIN_ERROR_URL': '/login',
        'SOCIAL_AUTH_AUTHENTICATION_BACKENDS': [
            'social_core.backends.google.GoogleOAuth2',
        ],
        'SOCIAL_AUTH_USER_MODEL': 'app.models.User',
        'SOCIAL_AUTH_STORAGE': 'social_flask_sqlalchemy.models.FlaskStorage',
        'SOCIAL_AUTH_PIPELINE': (
            'social_core.pipeline.social_auth.social_details',
            'social_core.pipeline.social_auth.social_uid',
            'app.social_auth_config.fix_google_uid',  # Fix Google uid to use 'sub' field
            'social_core.pipeline.social_auth.auth_allowed',
            'app.social_auth_config.create_user_and_login',  # Custom function handles everything
            'app.social_auth_config.custom_associate_user',  # Custom function handles social auth records
        ),
    })
    
    # Get absolute path for the upload folder
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    UPLOAD_FOLDER = os.path.join(project_root, 'app', 'static', 'uploads')
    
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max file size
    ALLOWED_EXTENSIONS = {
        'image': {'png', 'jpg', 'jpeg', 'gif', 'webp'},
        'video': {'mp4', 'webm', 'ogg', 'avi', 'mov'},
        'audio': {'mp3', 'wav', 'ogg', 'aac', 'm4a', 'webm', 'opus'}
    }

    # Mail-Konfiguration (Flask-Mail) — z.B. Hostpoint SMTP
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'asmtp.mail.hostpoint.ch')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', '587'))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', 'false').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get(
        'MAIL_DEFAULT_SENDER',
        'Japanese Learning <info@japanese-learning.ch>',
    )
    app.config['MAIL_SUPPRESS_SEND'] = os.environ.get('MAIL_SUPPRESS_SEND', 'false').lower() == 'true'

    # Payment-Konfiguration (Payrexx)
    app.config['PAYMENT_PROVIDER'] = os.environ.get('PAYMENT_PROVIDER', 'mock')
    app.config['PAYREXX_INSTANCE'] = os.environ.get('PAYREXX_INSTANCE')
    app.config['PAYREXX_API_SECRET'] = os.environ.get('PAYREXX_API_SECRET')
    app.config['PAYREXX_WEBHOOK_SECRET'] = os.environ.get('PAYREXX_WEBHOOK_SECRET')

    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
    app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS

    # Content-Sprachen: welche instruction_language sind oeffentlich sichtbar?
    # Default: nur Deutsch (Mayuko-Direktive: erst N5 DE komplett, dann erweitern).
    # Per Env CONTENT_LANGUAGES=german,english bilingual aktivierbar.
    _langs_env = os.environ.get('CONTENT_LANGUAGES', 'german')
    app.config['CONTENT_LANGUAGES'] = [
        lang.strip() for lang in _langs_env.split(',') if lang.strip()
    ]

    # Create upload directories if they don't exist
    upload_dirs = [
        os.path.join(UPLOAD_FOLDER, 'lessons', 'images'),
        os.path.join(UPLOAD_FOLDER, 'lessons', 'videos'),
        os.path.join(UPLOAD_FOLDER, 'lessons', 'audio'),
        os.path.join(UPLOAD_FOLDER, 'temp')
    ]
    for directory in upload_dirs:
        os.makedirs(directory, exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    from app.mail_service import mail
    mail.init_app(app)

    # Security Headers via Talisman
    csp = {
        'default-src': "'self'",
        'script-src': [
            "'self'",
            "'unsafe-inline'",
            "'unsafe-eval'",
            "cdn.jsdelivr.net",
            "cdn.tailwindcss.com",
            "cdn.tiny.cloud",
            "cdnjs.cloudflare.com",
            "code.jquery.com",
            "unpkg.com",
        ],
        'style-src': [
            "'self'",
            "'unsafe-inline'",
            "cdn.jsdelivr.net",
            "cdn.tailwindcss.com",
            "cdnjs.cloudflare.com",
            "fonts.googleapis.com",
        ],
        'font-src': [
            "'self'",
            "cdnjs.cloudflare.com",
            "fonts.gstatic.com",
        ],
        'img-src': ["'self'", "data:", "blob:", "storage.googleapis.com"],
        'media-src': ["'self'", "blob:", "storage.googleapis.com"],
        'connect-src': ["'self'"],
    }
    Talisman(
        app,
        content_security_policy=csp,
        content_security_policy_nonce_in=[],
        force_https=is_production,
        session_cookie_secure=is_production,
    )

    # Import models and routes here to avoid circular imports
    from app import models
    from app.models import Course, User
    
    # Initialize social auth storage after models are imported
    from social_flask_sqlalchemy.models import UserSocialAuth
    UserSocialAuth.app_session = db.session
    from app import routes
    from app.utils import convert_to_embed_url
    
    # Add user to Flask global context for social auth
    @app.before_request
    def load_current_user():
        from flask import g
        from flask_login import current_user
        g.user = current_user if current_user.is_authenticated else None

    # Register Jinja filters
    app.jinja_env.filters['to_embed_url'] = convert_to_embed_url
    
    # Add JSON parsing filter for templates
    import json
    def from_json_filter(value):
        if not value:
            return []
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return []
    
    app.jinja_env.filters['from_json'] = from_json_filter

    # Register blueprints
    app.register_blueprint(routes.bp) # Register the main routes blueprint
    
    # Register custom OAuth blueprint BEFORE social auth to override it
    from app.oauth_routes import oauth_bp
    app.register_blueprint(oauth_bp)
    
    # Register SRS (Spaced Repetition) blueprint
    from app.srs_routes import srs_bp
    app.register_blueprint(srs_bp)

    # Register Pruefen (Test-/Pruefungsseite) blueprint
    from app.pruefen_routes import pruefen_bp
    app.register_blueprint(pruefen_bp)

    # Register learner dashboard ("Mein Lernen") blueprint
    from app.dashboard_routes import dashboard_bp
    app.register_blueprint(dashboard_bp)

    # Register debug routes blueprint for troubleshooting
    from app.debug_routes import debug_bp
    app.register_blueprint(debug_bp)

    # Legal pages (Impressum, AGB, Datenschutz, Widerruf) — gesetzliche Pflicht
    # vor Live-Schaltung mit echten Zahlungen.
    from app.legal_routes import bp as legal_bp
    app.register_blueprint(legal_bp)

    # SEO: robots.txt + sitemap.xml
    from app.seo_routes import seo_bp
    app.register_blueprint(seo_bp)
    csrf.exempt(seo_bp)

    # Bundle-Verkauf (z.B. /n5-bundle) + Buy-API
    from app.bundle_routes import bundle_bp
    app.register_blueprint(bundle_bp)

    # Benutzer-Forum (/forum) — login-pflichtig zum Lesen, NICHT csrf-exempt.
    from app.forum_routes import forum_bp
    app.register_blueprint(forum_bp)

    # Content-Feedback / Issue-Board (/feedback) — Lesen OEFFENTLICH, Schreiben
    # nur mit Konto. NICHT csrf-exempt. Seiten tragen noindex (kein robots-
    # Disallow, sonst saehe Google das noindex nie).
    from app.issue_routes import issue_bp
    app.register_blueprint(issue_bp)

    # Error-Handler — eigene Templates auf Deutsch (vorher: Default-Flask-HTML in Englisch)
    from flask import render_template
    @app.errorhandler(404)
    def _not_found(_e):
        return render_template('errors/404.html'), 404
    @app.errorhandler(500)
    def _server_error(_e):
        return render_template('errors/500.html'), 500
    @app.errorhandler(410)
    def _gone(_e):
        # 410 Gone fuer endgueltig entfernte URLs (deprecated Alt-Lektionen):
        # praezises De-Index-Signal an Google statt nacktem 404.
        return render_template('errors/410.html'), 410

    # current_year fuer den Footer + SEO-Default-Daten fuer base.html
    from datetime import datetime as _dt
    from flask import request as _flask_request

    @app.context_processor
    def _inject_common_template_vars():
        site_url = app.config['SITE_URL']
        try:
            canonical = site_url + _flask_request.path
        except RuntimeError:
            canonical = site_url
        og_image = app.config['SEO_DEFAULT_OG_IMAGE']
        if og_image and og_image.startswith('/'):
            og_image = site_url + og_image
        # Site-weit konsistente Gratis-Lektionszahl: spiegelt EXAKT die
        # guest_accessible_lessons-Logik der Startseite (routes.py::index) —
        # published + allow_guest_access + lesson_type='free', je Sprache
        # gezaehlt und summiert. Single Source of Truth fuer Marketing-Texte.
        try:
            from app.models import Lesson
            n5_free_lesson_count = (
                Lesson.query.filter_by(
                    is_published=True,
                    allow_guest_access=True,
                    lesson_type='free',
                    instruction_language='english',
                ).count()
                + Lesson.query.filter_by(
                    is_published=True,
                    allow_guest_access=True,
                    lesson_type='free',
                    instruction_language='german',
                ).count()
            )
        except Exception:
            n5_free_lesson_count = 0
        # Navbar: Bundle-Kauf-Link nur fuer Nicht-Besitzer/Nicht-Admins zeigen.
        # Fail-closed auf False: kippt der bundle_service, zeigen wir KEINEN
        # Kauf-CTA — sonst sehen zahlende Bundle-Besitzer weiter den
        # CHF-9.90-Hinweis. Lieber kein Hint als ein falscher.
        try:
            from flask_login import current_user as _cu
            from app.services.bundle_service import user_needs_bundle_hint
            show_bundle_hint = user_needs_bundle_hint(_cu)
        except Exception:
            app.logger.warning("show_bundle_hint fail-closed", exc_info=True)
            show_bundle_hint = False
        # Kurse-Nav-Link nur zeigen, wenn es mind. 1 publizierten Kurs gibt —
        # sonst fuehrt der Link auf eine inhaltsleere /courses-Seite (Soft-404).
        # Fail-open auf True, damit Error-Pages ausserhalb voller Kontexte nicht brechen.
        try:
            from app.models import Course
            has_published_courses = (
                Course.query.filter_by(is_published=True).first() is not None
            )
        except Exception:
            has_published_courses = True
        return {
            'current_year': _dt.utcnow().year,
            'site_url': site_url,
            'site_name': app.config['SITE_NAME'],
            'site_description': app.config['SITE_DESCRIPTION'],
            'default_og_image': og_image,
            'google_site_verification': app.config['GOOGLE_SITE_VERIFICATION'],
            'robots_index': app.config['ROBOTS_INDEX'],
            'default_canonical': canonical,
            'n5_free_lesson_count': n5_free_lesson_count,
            'show_bundle_hint': show_bundle_hint,
            'has_published_courses': has_published_courses,
            'free_mode': app.config.get('FREE_MODE', False),
        }

    # Cache-Busting fuer eigene statische Assets: haengt die Datei-mtime als
    # ?v=<mtime> an die URL. Nach einem Deploy aendert sich die mtime → der
    # Browser laedt die neue Datei statt einer veralteten (Cache-Control:
    # max-age). Busted gezielt nur geaenderte Dateien (mtime pro Datei).
    import os as _os

    @app.template_global()
    def static_v(filename):
        from flask import url_for as _url_for
        try:
            mtime = int(_os.path.getmtime(_os.path.join(app.static_folder, filename)))
        except OSError:
            mtime = 0
        return _url_for('static', filename=filename, v=mtime)

    # Register social auth blueprint (for /auth/login/google-oauth2/ route only)
    from social_flask.routes import social_auth
    app.register_blueprint(social_auth, url_prefix='/auth')

    # Custom Jinja2 Filter: Newlines → <br>
    from markupsafe import Markup, escape
    @app.template_filter('nl2br')
    def nl2br_filter(text):
        if not text:
            return ''
        return Markup(escape(text).replace('\n', Markup('<br>')))

    # Custom Jinja2 Filter: Schweizer Tausendertrennung (1'234'567)
    # Bewusst additiv: nur dort genutzt, wo grosse Zahlen vorkommen (z.B. die
    # Kana-Storm-Kennzahlen). Faellt bei Nicht-Zahlen unveraendert durch.
    @app.template_filter('swiss_num')
    def swiss_num_filter(value):
        # Markup-safe: Ausgabe ist rein aus int abgeleitet (nur Ziffern +
        # Apostroph), damit der Apostroph nicht zu &#39; escaped wird.
        try:
            return Markup(f"{int(value):,}".replace(',', "'"))
        except (ValueError, TypeError):
            return value

    # Custom Jinja2 Filter: JSON-String → dict (for dialog_slideshow content)
    import json as _json
    @app.template_filter('fromjson')
    def fromjson_filter(value):
        if not value:
            return None
        try:
            return _json.loads(value)
        except (ValueError, TypeError):
            return None

    # Custom Jinja2 Filter: Markdown → safe HTML (fuer LessonContent.content_text)
    # Erlaubt Headings/Bold/Italic/Listen/Blockquote/Code → visuelle Hierarchie
    # auf den Lesson-Pages. Bestehende Plain-Text-Inhalte bleiben kompatibel
    # (Markdown ist Obermenge, \n\n bleibt Absatz).
    import markdown as _md
    import bleach as _bleach
    _MD_ALLOWED_TAGS = {
        'h2', 'h3', 'h4', 'p', 'br', 'strong', 'em', 'b', 'i',
        'ul', 'ol', 'li', 'blockquote', 'code', 'pre', 'hr',
        'a', 'span',
    }
    _MD_ALLOWED_ATTRS = {'a': ['href', 'title', 'rel'], 'span': ['class']}
    _MD_INSTANCE = _md.Markdown(extensions=['extra', 'sane_lists', 'nl2br'])

    @app.template_filter('markdown_safe')
    def markdown_safe_filter(text):
        if not text:
            return ''
        _MD_INSTANCE.reset()
        html = _MD_INSTANCE.convert(text)
        cleaned = _bleach.clean(
            html, tags=_MD_ALLOWED_TAGS, attributes=_MD_ALLOWED_ATTRS,
            strip=True,
        )
        # Externe Links absichern
        cleaned = _bleach.linkify(cleaned)
        return Markup(cleaned)

    # Inline-Variante: rendert **fett**, *kursiv*, `code`, Backslash-Escapes
    # ohne Block-Tags (kein <p>, <ul>, <h2>...). Fuer Quiz-Fragen, Antworten,
    # Feedback, Hints — also Texte, die in <h4>/<label>/<div> inline stehen.
    _MD_INLINE_TAGS = {'strong', 'em', 'b', 'i', 'code', 'span', 'br'}
    _MD_INLINE_ATTRS = {'span': ['class']}
    _MD_INLINE_INSTANCE = _md.Markdown(extensions=['extra'])

    @app.template_filter('markdown_inline')
    def markdown_inline_filter(text):
        if not text:
            return ''
        _MD_INLINE_INSTANCE.reset()
        html = _MD_INLINE_INSTANCE.convert(text)
        cleaned = _bleach.clean(
            html, tags=_MD_INLINE_TAGS, attributes=_MD_INLINE_ATTRS,
            strip=True,
        )
        # Markdown wraps single paragraphs in <p>...</p>; strip for inline use
        if cleaned.startswith('<p>') and cleaned.endswith('</p>'):
            cleaned = cleaned[3:-4]
        return Markup(cleaned)

    # Forum-Markdown: eigener, strengerer Filter als markdown_safe.
    # Unterschiede: KEIN <span> (verhindert injizierte CSS-Klassen wie eine
    # gefakte "admin-badge") und linkify mit nofollow + target_blank
    # (Spam-Hygiene; nutzergenerierte Links oeffnen extern, ohne SEO-Wert zu
    # vererben). Bewusst getrennt von markdown_safe, damit das Lesson-Rendering
    # unveraendert bleibt.
    from bleach.callbacks import nofollow as _bleach_nofollow, target_blank as _bleach_target_blank
    _FORUM_ALLOWED_TAGS = _MD_ALLOWED_TAGS - {'span'}
    _FORUM_ALLOWED_ATTRS = {'a': ['href', 'title', 'rel', 'target']}
    _MD_FORUM_INSTANCE = _md.Markdown(extensions=['extra', 'sane_lists', 'nl2br'])

    @app.template_filter('forum_markdown')
    def forum_markdown_filter(text):
        if not text:
            return ''
        _MD_FORUM_INSTANCE.reset()
        html = _MD_FORUM_INSTANCE.convert(text)
        cleaned = _bleach.clean(
            html, tags=_FORUM_ALLOWED_TAGS, attributes=_FORUM_ALLOWED_ATTRS,
            strip=True,
        )
        cleaned = _bleach.linkify(
            cleaned, callbacks=[_bleach_nofollow, _bleach_target_blank],
        )
        return Markup(cleaned)

    # Vocab-Highlight: markiert das Zielwort im Beispielsatz.
    # Strategie (best effort, scheitert leise): word -> reading -> reading[:-1]
    # bei flektierten Verben (会う vs. あいました) bleibt das Highlight oft aus.
    @app.template_filter('highlight_vocab')
    def highlight_vocab_filter(sentence, word=None, reading=None):
        if not sentence:
            return ''
        safe_sentence = escape(sentence)
        candidates = []
        for c in (word, reading):
            if c and len(c) >= 2:
                candidates.append(c)
        if reading and len(reading) >= 3:
            candidates.append(reading[:-1])
        for cand in candidates:
            safe_cand = escape(cand)
            if safe_cand in safe_sentence:
                highlighted = safe_sentence.replace(
                    safe_cand,
                    Markup('<span class="vocab-target-highlight">') + safe_cand + Markup('</span>'),
                    1,
                )
                return Markup(highlighted)
        return Markup(safe_sentence)

    # Romaji-Pendant zu highlight_vocab: markiert das Zielwort-Romaji im
    # Satz-Romaji, damit dasselbe Wort in BEIDEN Schriften (Japanisch +
    # Romaji) hervorgehoben/unterstrichen ist. Case-insensitiv, weil der
    # Satz am Anfang grossgeschrieben ist. Wortgrenzen-Match (\b), damit nicht
    # mitten in einem anderen Wort getroffen wird. Scheitert leise (z.B. bei
    # flektierten Verben: "furu" vs. "furimasu") — dann bleibt der Satz roh,
    # genau wie beim japanischen Highlight.
    @app.template_filter('highlight_romaji')
    def highlight_romaji_filter(sentence, word_romaji=None):
        if not sentence:
            return ''
        safe_sentence = str(escape(sentence))
        word = (word_romaji or '').strip()
        if len(word) < 2:
            return Markup(safe_sentence)
        pattern = r'\b' + re.escape(str(escape(word))) + r'\b'
        m = re.search(pattern, safe_sentence, re.IGNORECASE)
        if not m:
            return Markup(safe_sentence)
        highlighted = (
            safe_sentence[:m.start()]
            + '<span class="vocab-target-highlight">'
            + m.group(0)
            + '</span>'
            + safe_sentence[m.end():]
        )
        return Markup(highlighted)

    # Flask-Admin fuer Standard-CRUD registrieren
    from app.admin_views import init_admin
    init_admin(app, db.session)

    return app
