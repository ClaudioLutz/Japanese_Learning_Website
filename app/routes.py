# app/routes.py
import json
import os
import re
from datetime import datetime
from flask import Blueprint, render_template, render_template_string, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy.exc import IntegrityError, SQLAlchemyError # Import specific exceptions
from app import db, csrf, limiter, srs_service
from app.models import User, Kana, Kanji, Vocabulary, Grammar, LessonCategory, Lesson, LessonContent, LessonPrerequisite, UserLessonProgress, QuizQuestion, QuizOption, UserQuizAnswer, LessonPage, Course, LessonPurchase, CoursePurchase
from app.forms import RegistrationForm, LoginForm, CSRFTokenForm, RequestPasswordResetForm, ResetPasswordForm
from app.auth_tokens import make_reset_token, verify_reset_token
from app.mail_service import send_password_reset_email
from app.ai_services import AILessonContentGenerator
from app.lesson_export_import import (
    export_lesson_to_json, import_lesson_from_json, 
    create_lesson_export_package, import_lesson_from_zip
)
from functools import wraps # For custom decorators

# Helper function for JSON serialization
def model_to_dict(model_instance):
    """Converts a SQLAlchemy model instance to a dictionary."""
    d = {}
    for column in model_instance.__table__.columns:
        value = getattr(model_instance, column.name)
        # Handle datetime objects for JSON serialization
        if isinstance(value, datetime):
            d[column.name] = value.isoformat()
        else:
            d[column.name] = value
    return d

bp = Blueprint('routes', __name__)

# --- Custom Decorators for Content Access ---
def premium_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.subscription_level != 'premium':
            flash('Premium membership required to access this content.', 'warning')
            return redirect(url_for('routes.index')) # Or a subscribe page
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access required.', 'danger')
            return redirect(url_for('routes.index'))
        return f(*args, **kwargs)
    return decorated_function

# --- Public Routes ---
@bp.route('/healthz')
def healthz():
    """Simple health check for Cloud Run startup probe"""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Japanese Learning Website"
    }), 200

@bp.route('/health')
def health_check():
    """Full health check endpoint with database connectivity check"""
    try:
        # Basic database connectivity check
        db.session.execute(db.text('SELECT 1'))
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "Japanese Learning Website"
        }), 200
    except Exception as e:
        current_app.logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "unhealthy", 
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 503

# Unicode-Range fuer japanische Schrift (Hiragana, Katakana, CJK, Halfwidth Katakana)
_JAPANESE_CHAR_RE = re.compile(r'[぀-ゟ゠-ヿ一-鿿ｦ-ﾟ]')

# Pro Sprache eine fest verdrahtete Stimme — keine multilingualen Voices,
# damit nie eine japanische Stimme deutschen Text liest oder umgekehrt.
_TTS_VOICES = {
    'ja': {'languageCode': 'ja-JP', 'name': 'ja-JP-Chirp3-HD-Leda'},
    'de': {'languageCode': 'de-DE', 'name': 'de-DE-Neural2-F'},
}
# Chirp 3 HD unterstuetzt kein SSML — nur 'text' Input + speakingRate via audioConfig.
_CHIRP_VOICE_PREFIX = 'Chirp3-HD'

# Kana-Reihen-Mapping ist in app/services/kana_rows.py zentralisiert (wird auch
# vom Kana-Grid-Spiel verwendet). Hier nur re-importieren fuer die TTS-Pause-
# Heuristik unten.
from app.services.kana_rows import _KANA_ROWS, _KANA_BLOCK_RE  # noqa: E402
from app.services.tts_text import clean_tts_segment  # noqa: E402


def _maybe_spell_out_kana_row(text: str, model: str = 'chirp') -> str:
    """Trennt Kana-Reihen mit `、` (japanisches Komma) als Pause-Trennzeichen.

    Findet zusammenhaengende Hiragana/Katakana-Sequenzen (4-7 Mora) im Text
    und ersetzt sie durch eine mit `、` getrennte Version, sofern alle Mora
    einer Reihe angehoeren. Funktioniert auch bei eingebettetem Kontext wie
    `Die S-Reihe: 「さしすせそ」`. Woerter mit gemischten Konsonanten
    (こんにちは, さくら) bleiben unangetastet.

    Audio-Probe (2026-05): `、` funktioniert bei BEIDEN Modellen — Chirp wie
    Gemini machen damit deutliche Pausen. `[short pause]`-Markup von Gemini
    fuehrte sogar zu Truncation (nur erste Mora gesprochen). `model`-Parameter
    bleibt fuer API-Kompatibilitaet, hat aber keinen Effekt mehr.
    """
    sep = '、'

    def replace(match: re.Match) -> str:
        block = match.group(0)
        chars = set(block)
        for row in _KANA_ROWS:
            if chars.issubset(row):
                return sep.join(block)
        return block

    return _KANA_BLOCK_RE.sub(replace, text)


def _contains_japanese(text: str) -> bool:
    return bool(_JAPANESE_CHAR_RE.search(text))


_GEMINI_TTS_MODEL = 'gemini-2.5-pro-preview-tts'
_GEMINI_TTS_VOICE = 'Leda'  # gleiche Persoenlichkeit wie ja-JP-Chirp3-HD-Leda


def _synthesize_gemini(text: str) -> bytes:
    """Generiert WAV-Bytes (24kHz mono PCM mit WAV-Header) via Gemini 2.5 Pro TTS."""
    import io
    import wave
    from google import genai
    from google.genai import types

    api_key = (
        current_app.config.get('GOOGLE_AI_API_KEY')
        or os.environ.get('GOOGLE_AI_API_KEY')
        or os.environ.get('GOOGLE_API_KEY')
    )
    client = genai.Client(api_key=api_key)
    resp = client.models.generate_content(
        model=_GEMINI_TTS_MODEL,
        contents=text,
        config=types.GenerateContentConfig(
            response_modalities=['AUDIO'],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=_GEMINI_TTS_VOICE)
                ),
            ),
        ),
    )
    cand = resp.candidates[0] if resp.candidates else None
    if cand is None or cand.content is None or not cand.content.parts:
        raise RuntimeError(f"Gemini TTS leer (finish={getattr(cand, 'finish_reason', '?')})")
    pcm = cand.content.parts[0].inline_data.data

    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)
        wf.writeframes(pcm)
    return buf.getvalue()


@bp.route('/api/tts', methods=['POST'])
@csrf.exempt
@limiter.limit("30 per minute")
def tts_synthesize():
    """TTS-Endpoint mit zwei Modellen.

    Body: { text, lang: 'ja'|'de', model?: 'chirp'|'gemini', speed? }
    - model='chirp' (Default): Chirp 3 HD Leda — schnell (~300ms), MP3
    - model='gemini': Gemini 2.5 Pro TTS Leda — studio-qualitaet (~3-5s), WAV
      Nur fuer japanisch (lang=ja). Bei lang=de faellt es auf Chirp zurueck.

    Server validiert das Skript: lang=ja muss japanische Zeichen enthalten,
    lang=de darf keine enthalten. Verhindert Sprach-Mismatches.
    """
    import base64
    import hashlib
    import requests as http_requests
    from pathlib import Path

    data = request.get_json(silent=True) or {}
    text = (data.get('text') or '').strip()
    lang = (data.get('lang') or '').strip().lower()
    model = (data.get('model') or 'chirp').strip().lower()
    if model not in ('chirp', 'gemini'):
        model = 'chirp'

    if not text or len(text) > 500:
        return jsonify({"error": "Text fehlt oder zu lang (max 500 Zeichen)"}), 400
    if lang not in _TTS_VOICES:
        return jsonify({"error": "lang muss 'ja' oder 'de' sein"}), 400

    has_jp = _contains_japanese(text)
    if lang == 'ja' and not has_jp:
        return jsonify({"error": "lang=ja, aber Text enthaelt keine japanischen Zeichen"}), 400
    if lang == 'de' and has_jp:
        return jsonify({"error": "lang=de, aber Text enthaelt japanische Zeichen"}), 400

    # Gemini ist nur fuer Japanisch sinnvoll — fuer Deutsch immer Chirp/Neural2.
    if model == 'gemini' and lang != 'ja':
        model = 'chirp'

    voice = _TTS_VOICES[lang]
    speed = float(data.get('speed', 0.85))
    speed = max(0.5, min(speed, 1.5))

    # Nicht-sprechbare Trenn-/Klammerzeichen entfernen (siehe app/services/tts_text.py),
    # damit die Stimme keine Striche/Pfeile/Klammern mitliest.
    cleaned = clean_tts_segment(text, lang)
    if cleaned:
        text = cleaned

    if lang == 'ja':
        text = _maybe_spell_out_kana_row(text, model=model)

    # Cache-Key inkl. lang + model + voice — sonst koennten alte Chirp-Audios
    # statt neuer Gemini-Audios ausgeliefert werden (oder umgekehrt).
    voice_id = _GEMINI_TTS_VOICE if model == 'gemini' else voice['name']
    cache_key = hashlib.md5(f"{lang}_{model}_{voice_id}_{speed}_{text}".encode('utf-8')).hexdigest()
    cache_dir = Path(current_app.static_folder) / 'cache' / 'tts'
    cache_dir.mkdir(parents=True, exist_ok=True)
    ext = 'wav' if model == 'gemini' else 'mp3'
    mime = 'audio/wav' if model == 'gemini' else 'audio/mpeg'
    cache_file = cache_dir / f"{cache_key}.{ext}"

    if cache_file.exists():
        from flask import send_file
        return send_file(str(cache_file), mimetype=mime, conditional=True)

    # Gemini-Pfad ueber google-genai SDK
    if model == 'gemini':
        try:
            audio_bytes = _synthesize_gemini(text)
            cache_file.write_bytes(audio_bytes)
            from flask import make_response
            response = make_response(audio_bytes)
            response.headers['Content-Type'] = mime
            response.headers['Cache-Control'] = 'public, max-age=86400'
            return response
        except Exception as e:
            current_app.logger.warning(f"Gemini TTS fehlgeschlagen, Fallback Chirp: {e}")
            # Fallback auf Chirp damit der User trotzdem Audio hoert
            model = 'chirp'
            raw = (data.get('text') or '').strip()
            raw = clean_tts_segment(raw, lang) or raw
            text = _maybe_spell_out_kana_row(raw, model='chirp') if lang == 'ja' else text
            cache_key = hashlib.md5(
                f"{lang}_chirp_{voice['name']}_{speed}_{text}".encode('utf-8')
            ).hexdigest()
            cache_file = cache_dir / f"{cache_key}.mp3"
            mime = 'audio/mpeg'
            if cache_file.exists():
                from flask import send_file
                return send_file(str(cache_file), mimetype=mime, conditional=True)

    # Chirp-Pfad (Default oder Gemini-Fallback) ueber Cloud TTS REST-API
    api_key = current_app.config.get('GOOGLE_TTS_API_KEY') or os.environ.get('GOOGLE_TTS_API_KEY') or os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        return jsonify({"error": "TTS nicht konfiguriert"}), 503

    is_chirp = _CHIRP_VOICE_PREFIX in voice['name']
    if is_chirp:
        payload = {
            "input": {"text": text},
            "voice": voice,
            "audioConfig": {"audioEncoding": "MP3", "speakingRate": speed},
        }
    else:
        payload = {
            "input": {"ssml": f'<speak><prosody rate="{speed}">{text}</prosody></speak>'},
            "voice": voice,
            "audioConfig": {"audioEncoding": "MP3"},
        }

    try:
        resp = http_requests.post(
            f"https://texttospeech.googleapis.com/v1/text:synthesize?key={api_key}",
            json=payload, timeout=10,
        )
        if resp.status_code != 200:
            return jsonify({"error": "TTS API Fehler"}), 502

        audio_b64 = resp.json().get("audioContent", "")
        audio_bytes = base64.b64decode(audio_b64)
        cache_file.write_bytes(audio_bytes)

        from flask import make_response
        response = make_response(audio_bytes)
        response.headers['Content-Type'] = mime
        response.headers['Cache-Control'] = 'public, max-age=86400'
        return response
    except Exception:
        return jsonify({"error": "TTS Fehler"}), 502


@bp.route('/home')
def home_redirect():
    # /home rendert frueher dieselbe Seite wie / → fuer Google ein Duplikat,
    # das die Ranking-Signale der Startseite auf zwei URLs aufsplittete
    # (GSC: / 72 Impr., /home 40 Impr.). 301 buendelt die Autoritaet auf der
    # kanonischen Startseite (/).
    return redirect(url_for('routes.index'), code=301)


def _first_guest_lesson(lessons):
    """Erste gast-zugaengliche Gratis-Lektion aus einer (sortierten) Lesson-Liste.

    Kriterium: price == 0 UND allow_guest_access == True. Wird fuer Deep-Link-CTAs
    genutzt (Home/index, Modul-CTA, register-Fallback, /learn/n5-Hub), damit
    "Kostenlos starten" direkt in Inhalt statt in eine Liste/Paywall fuehrt.
    Erwartet bereits gefilterte/sortierte Lektionen; gibt None zurueck wenn keine passt.
    """
    for l in lessons:
        if (l.price or 0) == 0 and l.allow_guest_access:
            return l
    return None


def _build_n5_path_context(user, visible_langs):
    """Baut die N5-Lernpfad-Struktur (Module + 3 didaktische Gruppen).

    Gekapselt, weil sowohl die Startseite (index) als auch der /learn/n5-Hub (H1)
    dieselbe Pfad-Logik rendern. Liefert (n5_modules, n5_groups, next_module_id,
    first_guest_lesson) — pro Modul ist 'first_guest_lesson' die erste gratis+guest
    Lektion (sonst die bisherige first_lesson als Fallback fuer den CTA).
    """
    n5_modules_raw = (
        LessonCategory.query.filter_by(jlpt_level=5)
        .order_by(LessonCategory.display_order.asc(), LessonCategory.id.asc())
        .all()
    )
    n5_modules = []
    next_module_id = None  # erstes nicht-vollendetes Modul fuer Auto-Scroll/Pulsation
    for m in n5_modules_raw:
        done, total = m.completion_for_user(user, languages=visible_langs)
        unlocked = m.is_unlocked_for_user(user)
        published_lessons = sorted(
            [l for l in m.lessons
             if l.is_published and l.instruction_language in visible_langs],
            key=lambda l: (l.order_index or 0, l.id),
        )
        is_complete = total > 0 and done == total
        if next_module_id is None and unlocked and total > 0 and not is_complete:
            next_module_id = m.id
        first_lesson = published_lessons[0] if published_lessons else None
        # D4: CTA-Ziel fuer GAESTE = erste gratis+guest Lektion des Moduls (gegen
        # Paywall-Sackgasse, z.B. wenn die erste Lektion paid ist). Bewusst KEIN
        # first_lesson-Fallback: das Template nutzt 'first_guest_lesson' als Bedingung,
        # ob ein Gast-Direktlink gerendert wird — hat das Modul keine echte Gast-Lektion,
        # bleibt es None und der bisherige Modul-Detail-/first_lesson-Zweig greift.
        module_guest_lesson = _first_guest_lesson(published_lessons)
        n5_modules.append({
            "module": m,
            "done": done,
            "total": total,
            "percent": round(100.0 * done / total) if total else 0,
            "unlocked": unlocked,
            "is_complete": is_complete,
            "is_next": False,  # gesetzt nach Loop
            "lessons": published_lessons,
            # Erste Lektion fuer Direkt-CTA
            "first_lesson": first_lesson,
            # D4: erste gratis+guest Lektion (sonst first_lesson) fuer den CTA
            "first_guest_lesson": module_guest_lesson,
        })
    for entry in n5_modules:
        if entry["module"].id == next_module_id:
            entry["is_next"] = True

    # Pfad in 3 didaktische Gruppen aufteilen (Schreibsystem / Wortschatz / Grammatik)
    SCHREIB_SLUGS = {"n5-hiragana", "n5-katakana"}
    GRAMMATIK_SLUGS = {"n5-erste-saetze"}
    n5_groups = [
        {"title": "1. Schreibsystem", "subtitle": "Hiragana und Katakana — Pflicht vor allem anderen.",
         "modules": [e for e in n5_modules if e["module"].slug in SCHREIB_SLUGS]},
        {"title": "2. Grundwortschatz", "subtitle": "Themen-Module mit Vokabeln, Beispielsätzen und Dialogen.",
         "modules": [e for e in n5_modules
                     if e["module"].slug not in SCHREIB_SLUGS
                     and e["module"].slug not in GRAMMATIK_SLUGS]},
        {"title": "3. Erste Sätze", "subtitle": "Grammatik, die alles zusammenbringt.",
         "modules": [e for e in n5_modules if e["module"].slug in GRAMMATIK_SLUGS]},
    ]

    # Globale erste Gast-Lektion fuer den Top-of-Funnel "Kostenlos starten"-CTA:
    # erste gratis+guest Lektion ueber alle N5-Module hinweg (i.d.R. Hiragana 1).
    first_guest_lesson = None
    for entry in n5_modules:
        cand = _first_guest_lesson(entry["lessons"])
        if cand is not None:
            first_guest_lesson = cand
            break

    return n5_modules, n5_groups, next_module_id, first_guest_lesson


@bp.route('/')
def index():
    # Get language-specific lesson counts
    english_lessons = Lesson.query.filter_by(is_published=True, instruction_language='english').count()
    german_lessons = Lesson.query.filter_by(is_published=True, instruction_language='german').count()
    
    # Get guest accessible lessons by language
    english_guest_lessons = Lesson.query.filter_by(
        is_published=True, 
        allow_guest_access=True, 
        lesson_type='free',
        instruction_language='english'
    ).count()
    
    german_guest_lessons = Lesson.query.filter_by(
        is_published=True, 
        allow_guest_access=True, 
        lesson_type='free',
        instruction_language='german'
    ).count()
    
    # Get total counts for backward compatibility
    total_lessons = english_lessons + german_lessons
    total_courses = Course.query.filter_by(is_published=True).count()
    guest_accessible_lessons = english_guest_lessons + german_guest_lessons
    
    # Letzte bearbeitete Lektion fuer eingeloggte User
    last_lesson = None
    if current_user.is_authenticated:
        last_progress = UserLessonProgress.query.filter_by(
            user_id=current_user.id
        ).order_by(UserLessonProgress.last_accessed.desc()).first()
        if last_progress:
            last_lesson = Lesson.query.get(last_progress.lesson_id)

    # JLPT-Lernpfad-Daten (Mayuko-Direktive 2026-04-25): Pfad als Startseiten-Inhalt
    visible_langs = current_app.config.get('CONTENT_LANGUAGES', ['german'])
    user = current_user if current_user.is_authenticated else None
    n5_modules, n5_groups, next_module_id, first_guest_lesson = _build_n5_path_context(
        user, visible_langs
    )

    # Bundle-Hinweis (show_bundle_hint) kommt jetzt site-weit aus dem
    # Context-Processor (__init__.py → bundle_service.user_needs_bundle_hint).

    # Live-Stats fuer Hero — gibt Konkretheit + Aktivitaetssignal
    n5_vocab_count = Vocabulary.query.filter_by(jlpt_level=5).count()
    n5_kanji_count = Kanji.query.filter_by(jlpt_level=5).count()

    # E4-Support: Coverage als einheitliche "heute X von Ziel Y"-Sprache fuer Home/Bundle.
    # coverage_service liefert vocab_covered/vocab_total/kanji_covered/kanji_total/vocab_pct
    # — hier auf den Kontrakt have/target gemappt, den index.html erwartet.
    n5_coverage = None
    try:
        from app.services.coverage_service import get_jlpt_coverage
        cov = get_jlpt_coverage(5)
        n5_coverage = {
            "vocab_have": cov["vocab_covered"],
            "vocab_target": cov["vocab_total"],
            "kanji_have": cov["kanji_covered"],
            "kanji_target": cov["kanji_total"],
            "vocab_pct": cov["vocab_pct"],
        }
    except Exception:
        # Coverage darf die Startseite nie blockieren (z.B. fehlende canonical-Liste)
        current_app.logger.warning("N5-Coverage konnte nicht geladen werden", exc_info=True)

    return render_template('index.html',
                         total_lessons=total_lessons,
                         total_courses=total_courses,
                         guest_accessible_lessons=guest_accessible_lessons,
                         english_lessons=english_lessons,
                         german_lessons=german_lessons,
                         english_guest_lessons=english_guest_lessons,
                         german_guest_lessons=german_guest_lessons,
                         last_lesson=last_lesson,
                         n5_modules=n5_modules,
                         n5_groups=n5_groups,
                         next_module_id=next_module_id,
                         visible_languages=visible_langs,
                         n5_vocab_count=n5_vocab_count,
                         n5_kanji_count=n5_kanji_count,
                         first_guest_lesson=first_guest_lesson,
                         n5_coverage=n5_coverage)

@bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def register():
    if current_user.is_authenticated:
        return redirect(url_for('routes.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        # D1: direkt einloggen statt auf /login zu schicken — kein Doppel-Login mehr,
        # damit eine Registrierung von einer Paywall/Bundle-Seite eingeloggt zurueck
        # auf das gewuenschte Ziel fuehrt.
        login_user(user)
        # next aus Query ODER Formular (hidden field) — Template liefert name="next".
        next_page = request.values.get('next')
        # Open-Redirect-Schutz, identisch zu login(): nur relative URLs, kein "//".
        if next_page and next_page.startswith('/') and not next_page.startswith('//'):
            flash('Willkommen — dein Konto ist erstellt und du bist angemeldet.', 'success')
            return redirect(next_page)
        # Fallback: direkt in die erste Gast-Lektion (Aha-Moment statt Liste);
        # sonst auf den Lernpfad der Startseite.
        visible_langs = current_app.config.get('CONTENT_LANGUAGES', ['german'])
        _, _, _, first_guest_lesson = _build_n5_path_context(user, visible_langs)
        if first_guest_lesson is not None:
            flash('Willkommen — los geht\'s mit deiner ersten Lektion!', 'success')
            return redirect(url_for('routes.view_lesson', lesson_id=first_guest_lesson.id))
        flash('Willkommen — dein Konto ist erstellt und du bist angemeldet.', 'success')
        return redirect(url_for('routes.index') + '#lernpfad')
    return render_template('register.html', form=form)

@bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        # Redirect based on user role
        if current_user.is_admin:
            return redirect(url_for('routes.admin_index'))
        else:
            return redirect(url_for('routes.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.is_locked:
            flash('Konto vorübergehend gesperrt (zu viele Fehlversuche). Bitte später erneut versuchen.', 'danger')
        elif user and user.check_password(form.password.data):
            user.record_successful_login()
            db.session.commit()
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash('Erfolgreich angemeldet.', 'success')
            # Open-Redirect-Schutz: nur relative URLs erlauben
            if not next_page or not next_page.startswith('/') or next_page.startswith('//'):
                if user.is_admin:
                    return redirect(url_for('routes.admin_index'))
                else:
                    return redirect(url_for('routes.index'))
            return redirect(next_page)
        else:
            if user:
                user.record_failed_login()
                db.session.commit()
            flash('Anmeldung fehlgeschlagen. Bitte E-Mail und Passwort prüfen.', 'danger')
    return render_template('login.html', form=form)

@bp.route('/forgot-password', methods=['GET', 'POST'])
@limiter.limit("3 per hour")
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('routes.index'))
    form = RequestPasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if user:
            token = make_reset_token(user.id)
            link = url_for('routes.reset_password', token=token, _external=True)
            send_password_reset_email(user.email, link, username=user.username)
        # Gleiche Antwort, egal ob User existiert (Enumeration-Schutz)
        flash(
            'Falls ein Konto mit dieser E-Mail existiert, wurde ein Reset-Link versendet. '
            'Pruefen Sie bitte auch Ihren Spam-Ordner.',
            'info',
        )
        return redirect(url_for('routes.login'))
    return render_template('forgot_password.html', form=form)


@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
@limiter.limit("10 per hour")
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('routes.index'))
    user_id = verify_reset_token(token)
    if not user_id:
        flash('Der Reset-Link ist ungueltig oder abgelaufen. Bitte fordern Sie einen neuen an.', 'danger')
        return redirect(url_for('routes.forgot_password'))
    user = User.query.get(user_id)
    if not user:
        flash('Der Reset-Link ist ungueltig.', 'danger')
        return redirect(url_for('routes.forgot_password'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        # Lockout aufheben, falls aktiv
        user.failed_login_count = 0
        user.locked_until = None
        db.session.commit()
        flash('Passwort wurde erfolgreich gesetzt. Sie koennen sich jetzt anmelden.', 'success')
        return redirect(url_for('routes.login'))
    return render_template('reset_password.html', form=form)


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sie wurden abgemeldet.', 'info')
    return redirect(url_for('routes.index'))

@bp.route('/profile')
@login_required
def user_profile():
    """Display user profile with lesson progress and statistics"""
    from sqlalchemy import func, desc
    
    # Get user's lesson progress
    user_progress = UserLessonProgress.query.filter_by(user_id=current_user.id).all()
    
    # Separate started and completed lessons
    started_lessons = []
    completed_lessons = []
    
    for progress in user_progress:
        lesson_data = {
            'lesson': progress.lesson,
            'progress': progress,
            'category_name': progress.lesson.category.name if progress.lesson.category else 'Uncategorized'
        }
        
        if progress.is_completed:
            completed_lessons.append(lesson_data)
        else:
            started_lessons.append(lesson_data)
    
    # Sort lessons by progress percentage (descending - highest progress first)
    started_lessons.sort(key=lambda x: x['progress'].progress_percentage, reverse=True)
    completed_lessons.sort(key=lambda x: x['progress'].completed_at or x['progress'].last_accessed, reverse=True)
    
    # Calculate statistics
    total_lessons_started = len(user_progress)
    total_lessons_completed = len(completed_lessons)
    completion_rate = (total_lessons_completed / total_lessons_started * 100) if total_lessons_started > 0 else 0
    total_time_spent = sum(progress.time_spent for progress in user_progress)
    
    # Get progress by category
    category_stats = {}
    for progress in user_progress:
        category_name = progress.lesson.category.name if progress.lesson.category else 'Uncategorized'
        if category_name not in category_stats:
            category_stats[category_name] = {
                'total': 0,
                'completed': 0,
                'time_spent': 0
            }
        
        category_stats[category_name]['total'] += 1
        category_stats[category_name]['time_spent'] += progress.time_spent
        if progress.is_completed:
            category_stats[category_name]['completed'] += 1
    
    # Calculate completion rate for each category
    for category in category_stats:
        total = category_stats[category]['total']
        completed = category_stats[category]['completed']
        category_stats[category]['completion_rate'] = (completed / total * 100) if total > 0 else 0
    
    # Get recent activity (last 10 lessons accessed)
    recent_activity = UserLessonProgress.query.filter_by(user_id=current_user.id)\
        .order_by(desc(UserLessonProgress.last_accessed))\
        .limit(10).all()
    
    # Get user's purchases if any
    user_purchases = LessonPurchase.query.filter_by(user_id=current_user.id).all()
    total_spent = sum(purchase.price_paid for purchase in user_purchases)
    
    return render_template('user_profile.html',
                         started_lessons=started_lessons,
                         completed_lessons=completed_lessons,
                         total_lessons_started=total_lessons_started,
                         total_lessons_completed=total_lessons_completed,
                         completion_rate=completion_rate,
                         total_time_spent=total_time_spent,
                         category_stats=category_stats,
                         recent_activity=recent_activity,
                         user_purchases=user_purchases,
                         total_spent=total_spent)

# --- Member Routes (Simulated Premium) ---

@bp.route('/upgrade_to_premium', methods=['POST']) # Changed to POST
@login_required
def upgrade_to_premium():
    form = CSRFTokenForm()
    if form.validate_on_submit(): # Added CSRF validation
        # **PROTOTYPE ONLY**: Manually change subscription for testing
        current_user.subscription_level = 'premium'
        db.session.commit()
        flash('Congratulations! Your account has been upgraded to Premium.', 'success')
        return redirect(url_for('routes.index')) # Changed to a valid route
    else:
        flash('Invalid request for upgrade.', 'danger')
        return redirect(url_for('routes.index')) # Or a relevant page

@bp.route('/downgrade_from_premium', methods=['POST']) # Changed to POST
@login_required
def downgrade_from_premium():
    form = CSRFTokenForm()
    if form.validate_on_submit(): # Added CSRF validation
        # **PROTOTYPE ONLY**: Manually change subscription for testing
        current_user.subscription_level = 'free'
        db.session.commit()
        flash('Your account has been downgraded to Free.', 'info')
        return redirect(url_for('routes.index')) # Changed to a valid route
    else:
        flash('Invalid request for downgrade.', 'danger')
        return redirect(url_for('routes.index')) # Or a relevant page

# --- Admin Routes ---
@bp.route('/admin')
@login_required
@admin_required
def admin_index():
    return render_template('admin/admin_index.html')

@bp.route('/admin/manage/kana')
@login_required
@admin_required
def admin_manage_kana():
    return render_template('admin/manage_kana.html')

@bp.route('/admin/manage/kanji')
@login_required
@admin_required
def admin_manage_kanji():
    return render_template('admin/manage_kanji.html')

@bp.route('/admin/manage/vocabulary')
@login_required
@admin_required
def admin_manage_vocabulary():
    return render_template('admin/manage_vocabulary.html')

@bp.route('/admin/manage/grammar')
@login_required
@admin_required
def admin_manage_grammar():
    return render_template('admin/manage_grammar.html')

@bp.route('/admin/manage/lessons')
@login_required
@admin_required
def admin_manage_lessons():
    form = CSRFTokenForm()
    return render_template('admin/manage_lessons.html', form=form)

@bp.route('/admin/manage/categories')
@login_required
@admin_required
def admin_manage_categories():
    return render_template('admin/manage_categories.html')

@bp.route('/admin/manage/courses')
@login_required
@admin_required
def admin_manage_courses():
    form = CSRFTokenForm()
    return render_template('admin/manage_courses.html', form=form)

@bp.route('/admin/manage/approval')
@login_required
@admin_required
def admin_manage_approval():
    pending_kanji = Kanji.query.filter_by(status='pending_approval').all()
    pending_vocabulary = Vocabulary.query.filter_by(status='pending_approval').all()
    pending_grammar = Grammar.query.filter_by(status='pending_approval').all()
    return render_template('admin/manage_approval.html',
                           pending_kanji=pending_kanji,
                           pending_vocabulary=pending_vocabulary,
                           pending_grammar=pending_grammar)

# --- Lesson Routes for Users ---
@bp.route('/lessons')
def lessons():
    """Browse available lessons.

    Server-rendert Kategorien (mit Lektions-Anzahl) + alle publishten Lektionen
    in voller Form. Der Client filtert/sortiert/toggled View-Modi rein per JS
    auf den bereits gerenderten Cards (kein zusaetzlicher Fetch). Vorteile:
    - SEO: alle Lessons + Categories sind im initialen HTML
    - UX: instant filtern, keine Roundtrips
    """
    visible_langs = current_app.config.get('CONTENT_LANGUAGES', ['german'])

    # Fortschritt des eingeloggten Nutzers fuer alle Lektionen in EINER Query laden
    # -> erlaubt Status-Badge, "Noch offen"-Filter und den "Weiter lernen"-Block.
    # Gaeste: leere Map -> Status 'open'.
    progress_map = {}
    show_status = bool(getattr(current_user, 'is_authenticated', False))
    if show_status:
        for pr in UserLessonProgress.query.filter_by(user_id=current_user.id).all():
            progress_map[pr.lesson_id] = pr

    def _lesson_dict(lsn):
        is_free = (lsn.price or 0) == 0
        pr = progress_map.get(lsn.id)
        pct = (pr.progress_percentage or 0) if pr else 0
        if pr and pr.is_completed:
            status = 'done'
        elif pct > 0:
            status = 'started'
        else:
            status = 'open'
        return {
            'id': lsn.id,
            'title': lsn.title,
            'description': lsn.description or '',
            'thumbnail_url': lsn.get_thumbnail_url() if hasattr(lsn, 'get_thumbnail_url') else None,
            'difficulty_level': lsn.difficulty_level,
            'estimated_duration': lsn.estimated_duration,
            'is_free': is_free,
            'price': lsn.price or 0,
            'allow_guest_access': lsn.allow_guest_access,
            'category_id': lsn.category_id,
            'category_name': lsn.category.name if lsn.category else None,
            'category_jlpt_level': lsn.category.jlpt_level if lsn.category else None,
            'created_at': lsn.created_at,
            'status': status,
            'progress_percentage': pct,
            'last_accessed': pr.last_accessed if pr else None,
        }

    # Kategorien als Lehrplan-Rueckgrat: jede Kategorie traegt ihre Lektionen
    # in Lehrplan-Reihenfolge (order_index). Ein einziges Browse-System statt
    # zweier paralleler Grids.
    all_categories = (
        LessonCategory.query
        .order_by(
            LessonCategory.jlpt_level.desc().nullslast(),
            LessonCategory.display_order.asc(),
            LessonCategory.id.asc(),
        )
        .all()
    )
    page_categories = []
    page_lessons = []  # flach, in Lehrplan-Reihenfolge (fuer JSON-LD + JS-Zaehler)
    for cat in all_categories:
        visible_lessons = sorted(
            [lsn for lsn in cat.lessons
             if lsn.is_published and lsn.instruction_language in visible_langs],
            key=lambda lsn: (lsn.order_index or 0, lsn.id),
        )
        if not visible_lessons:
            continue
        lesson_dicts = [_lesson_dict(lsn) for lsn in visible_lessons]
        free_count = sum(1 for d in lesson_dicts if d['is_free'])
        done_count = sum(1 for d in lesson_dicts if d['status'] == 'done')
        page_categories.append({
            'id': cat.id,
            'name': cat.name,
            'description': cat.description,
            'icon_emoji': cat.icon_emoji,
            'color_code': cat.color_code,
            'jlpt_level': cat.jlpt_level,
            'lesson_count': len(lesson_dicts),
            'free_count': free_count,
            'done_count': done_count,
            'slug': cat.slug,
            'lessons': lesson_dicts,
        })
        page_lessons.extend(lesson_dicts)

    # Auffang: publishte Lektionen ohne (sichtbare) Kategorie nicht verschlucken
    # -> eigene Gruppe ans Ende, damit keine Lektion aus dem Katalog faellt.
    seen_ids = {d['id'] for d in page_lessons}
    orphan_lessons = sorted(
        [lsn for lsn in Lesson.query.filter(
            Lesson.is_published == True,  # noqa: E712
            Lesson.instruction_language.in_(visible_langs),
         ).all()
         if lsn.id not in seen_ids],
        key=lambda lsn: (lsn.order_index or 0, lsn.id),
    )
    if orphan_lessons:
        orphan_dicts = [_lesson_dict(lsn) for lsn in orphan_lessons]
        page_categories.append({
            'id': 0,
            'name': 'Weitere Lektionen',
            'description': None,
            'icon_emoji': '📚',
            'color_code': None,
            'jlpt_level': None,
            'lesson_count': len(orphan_dicts),
            'free_count': sum(1 for d in orphan_dicts if d['is_free']),
            'done_count': sum(1 for d in orphan_dicts if d['status'] == 'done'),
            'slug': None,
            'lessons': orphan_dicts,
        })
        page_lessons.extend(orphan_dicts)

    # JLPT-Levels die in den Kategorien tatsaechlich vorkommen — fuer Filter-Pills.
    # Bei nur einem Level (aktuell nur N5) blendet das Template die Pills aus.
    jlpt_levels = sorted(
        {c['jlpt_level'] for c in page_categories if c['jlpt_level']},
        reverse=True,
    )

    total_free = sum(1 for d in page_lessons if d['is_free'])
    total_paid = len(page_lessons) - total_free
    total_done = sum(1 for d in page_lessons if d['status'] == 'done')
    total_open = len(page_lessons) - total_done

    # ── Weiter-lernen-Dashboard (nur eingeloggt) ──────────────────────────
    # "Mach weiter, wo du warst": bevorzugt die zuletzt begonnene, noch nicht
    # abgeschlossene Lektion; sonst die naechste offene Lektion im Lehrplan.
    continue_lesson = None
    continue_category = None
    due_count = 0
    current_streak = 0
    if show_status:
        due_count = srs_service.get_due_count(current_user.id)
        current_streak = current_user.current_streak or 0
        resume = None  # (last_accessed, lesson_dict, category_name)
        nxt = None      # (lesson_dict, category_name) — erste offene im Pfad
        for cat in page_categories:
            for d in cat['lessons']:
                if d['status'] == 'done':
                    continue
                if d['status'] == 'started':
                    la = d['last_accessed'] or datetime.min
                    if resume is None or la > resume[0]:
                        resume = (la, d, cat['name'])
                if nxt is None:
                    nxt = (d, cat['name'])
        if resume is not None:
            continue_lesson, continue_category = resume[1], resume[2]
        elif nxt is not None:
            continue_lesson, continue_category = nxt[0], nxt[1]

    # Erste gratis + gastzugaengliche Lektion — Einstieg fuer Gaeste ("Gratis starten")
    first_free_lesson = None
    for cat in page_categories:
        for d in cat['lessons']:
            if d['is_free'] and d['allow_guest_access']:
                first_free_lesson = d
                break
        if first_free_lesson:
            break

    return render_template(
        'lessons.html',
        page_categories=page_categories,
        page_lessons=page_lessons,
        jlpt_levels=jlpt_levels,
        total_free=total_free,
        total_paid=total_paid,
        show_status=show_status,
        total_open=total_open,
        total_done=total_done,
        continue_lesson=continue_lesson,
        continue_category=continue_category,
        due_count=due_count,
        current_streak=current_streak,
        first_free_lesson=first_free_lesson,
    )


@bp.route('/ueber')
def ueber():
    """About-Seite — Founder-Story, Team, Begründung 'Warum Deutsch'.

    Wichtig fuer Google E-E-A-T (Experience/Expertise/Authoritativeness/Trust)
    bei einem bezahlten Bildungsprodukt. Stellt Autor + Motivation + Standort
    transparent dar.
    """
    return render_template('ueber.html')


@bp.route('/lernmethode')
def lernmethode():
    """SRS-/FSRS-Erklärseite — Differenzierungsfeature gegenüber Anki/Wettbewerb.

    Rankt mittelfristig fuer 'Spaced Repetition Deutsch' und 'FSRS deutsch',
    beides mit niedrigem Wettbewerb auf Deutsch.
    """
    return render_template('lernmethode.html')


@bp.route('/jlpt-n5-schweiz')
def jlpt_n5_schweiz():
    """SEO-Landing fuer "JLPT N5 Schweiz" — Schweiz-spezifische Pruefungs-Infos
    (UZH-Termin, Gebuehr, Anmeldung) gebuendelt mit Curriculum-Vorstellung.

    Ziel-Keywords: "JLPT N5 Schweiz", "JLPT Zürich", "Japanisch Prüfung Schweiz".
    Strukturierte Daten: Course + FAQPage + BreadcrumbList.
    """
    return render_template('jlpt_n5_schweiz.html')


@bp.route('/learn')
@bp.route('/learn/n<int:level>')
def learn_path(level: int = 5):
    """JLPT-Lernpfad.

    H1: /learn/n5 rendert eine eigene indexierbare 200-Hub-Seite (Module +
    Lernpfad-Uebersicht + Bundle-CTA) mit Self-Canonical statt das alte
    301-Fragment auf die Startseite — die generischste N5-URL soll eigene
    Ranking-Autoritaet sammeln (war Pos. ~31).
    Andere Levels (N4+) sind noch nicht inhaltlich vorhanden — 404.
    """
    if level not in (1, 2, 3, 4, 5):
        from flask import abort
        abort(404)
    if level == 5:
        visible_langs = current_app.config.get('CONTENT_LANGUAGES', ['german'])
        user = current_user if current_user.is_authenticated else None
        n5_modules, n5_groups, next_module_id, first_guest_lesson = _build_n5_path_context(
            user, visible_langs
        )

        # Coverage fuer die "heute X von Ziel Y"-Sprache (gleicher Mapping-Kontrakt wie index).
        n5_coverage = None
        try:
            from app.services.coverage_service import get_jlpt_coverage
            cov = get_jlpt_coverage(5)
            n5_coverage = {
                "vocab_have": cov["vocab_covered"],
                "vocab_target": cov["vocab_total"],
                "kanji_have": cov["kanji_covered"],
                "kanji_target": cov["kanji_total"],
                "vocab_pct": cov["vocab_pct"],
            }
        except Exception:
            current_app.logger.warning("N5-Coverage konnte nicht geladen werden", exc_info=True)

        # Bundle-CTA (show_bundle_hint) kommt site-weit aus dem Context-Processor.
        return render_template(
            'learn_n5.html',
            n5_modules=n5_modules,
            n5_groups=n5_groups,
            next_module_id=next_module_id,
            first_guest_lesson=first_guest_lesson,
            n5_coverage=n5_coverage,
            visible_languages=visible_langs,
        )
    # Andere Levels haben noch keinen Content — Mayuko-Direktive: erst N5 komplett.
    from flask import abort
    abort(404)

@bp.route('/learn/n<int:level>/<slug>')
def module_detail(level: int, slug: str):
    """Modul-Uebersicht: alle Lessons des Moduls mit Status, Coverage und Direkt-Start.

    Bei nur einer Lesson redirect direkt zur Lesson — keine Klick-Friction.
    Sonst rendert eine eigene Uebersichtsseite (auch SEO-Vorteil: eigene URL pro Modul).
    """
    if level not in (1, 2, 3, 4, 5):
        from flask import abort
        abort(404)
    visible_langs = current_app.config.get('CONTENT_LANGUAGES', ['german'])
    module = LessonCategory.query.filter_by(jlpt_level=level, slug=slug).first_or_404()
    user = current_user if current_user.is_authenticated else None

    published_lessons = sorted(
        [l for l in module.lessons
         if l.is_published and l.instruction_language in visible_langs],
        key=lambda l: (l.order_index or 0, l.id),
    )

    # Skip-Optimierung: bei nur 1 Lesson direkt rein, keine Zwischenseite
    if len(published_lessons) <= 1 and published_lessons:
        return redirect(url_for('routes.view_lesson', lesson_id=published_lessons[0].id))

    # Lesson-Status anreichern
    lesson_entries = []
    for lesson in published_lessons:
        accessible, msg = lesson.is_accessible_to_user(user)
        progress = None
        if user:
            progress = UserLessonProgress.query.filter_by(
                user_id=user.id, lesson_id=lesson.id
            ).first()
        lesson_entries.append({
            'lesson': lesson,
            'accessible': accessible,
            'access_msg': msg,
            'progress': progress,
            'is_paid': (lesson.price or 0) > 0,
        })

    done, total = module.completion_for_user(user, languages=visible_langs)
    percent = round(100.0 * done / total) if total else 0

    # Bundle-Status fuer den CTA-Banner unten (wer hat schon, wer nicht)
    bundle_owned = False
    if user and not getattr(user, 'is_admin', False):
        from app.services.bundle_service import get_n5_bundle_course
        bundle = get_n5_bundle_course()
        if bundle:
            bundle_owned = CoursePurchase.query.filter_by(
                user_id=user.id, course_id=bundle.id
            ).first() is not None
    elif user and getattr(user, 'is_admin', False):
        bundle_owned = True

    paid_count = sum(1 for e in lesson_entries if e['is_paid'])

    return render_template(
        'module_detail.html',
        level=level,
        module=module,
        lesson_entries=lesson_entries,
        done=done,
        total=total,
        percent=percent,
        paid_count=paid_count,
        bundle_owned=bundle_owned,
    )


@bp.route('/courses')
def courses():
    """Browse available courses"""
    courses = Course.query.filter_by(is_published=True).all()
    return render_template('courses.html', courses=courses)

@bp.route('/my-lessons')
@login_required
def my_lessons():
    """Display all bought lessons for the current user (incl. lessons unlocked via course purchases)."""
    user_purchases = LessonPurchase.query.filter_by(user_id=current_user.id).order_by(LessonPurchase.purchased_at.desc()).all()
    course_purchases = CoursePurchase.query.filter_by(user_id=current_user.id).order_by(CoursePurchase.purchased_at.desc()).all()

    purchased_lessons = []
    total_spent = 0.0
    completed_count = 0
    total_time_spent = 0
    seen_lesson_ids: set[int] = set()

    def _attach(lesson, purchase=None, via_course=None):
        if lesson.id in seen_lesson_ids:
            return
        seen_lesson_ids.add(lesson.id)
        progress = UserLessonProgress.query.filter_by(
            user_id=current_user.id,
            lesson_id=lesson.id,
        ).first()
        nonlocal completed_count, total_time_spent
        if progress and progress.is_completed:
            completed_count += 1
        if progress:
            total_time_spent += progress.time_spent or 0
        purchased_lessons.append({
            'lesson': lesson,
            'purchase': purchase,
            'progress': progress,
            'category_name': lesson.category.name if lesson.category else 'Uncategorized',
            'accessible': True,
            'access_message': f"Im Kurs '{via_course.title}'" if via_course else 'Purchased',
            'via_course': via_course,
        })

    for purchase in user_purchases:
        total_spent += purchase.price_paid or 0
        _attach(purchase.lesson, purchase=purchase)

    for cp in course_purchases:
        total_spent += cp.price_paid or 0
        for lesson in cp.course.lessons:
            if not lesson.is_published:
                continue
            _attach(lesson, via_course=cp.course)

    completion_rate = (completed_count / len(purchased_lessons) * 100) if purchased_lessons else 0

    return render_template('my_lessons.html',
                         purchased_lessons=purchased_lessons,
                         purchased_courses=course_purchases,
                         total_spent=total_spent,
                         total_purchased_lessons=len(purchased_lessons),
                         completed_count=completed_count,
                         completion_rate=completion_rate,
                         total_time_spent=total_time_spent)

@bp.route('/course/<int:course_id>')
def view_course(course_id):
    """View a specific course"""
    course = Course.query.get_or_404(course_id)
    
    # Check if the user has purchased the course
    has_purchased = False
    if current_user.is_authenticated:
        purchase = CoursePurchase.query.filter_by(user_id=current_user.id, course_id=course.id).first()
        if purchase:
            has_purchased = True

    # Get user progress for all lessons in this course
    lesson_progress = {}
    total_lessons = len(course.lessons)
    completed_lessons = 0
    total_duration = 0
    
    for lesson in course.lessons:
        # Get user progress for this lesson
        progress = UserLessonProgress.query.filter_by(
            user_id=current_user.id, lesson_id=lesson.id
        ).first()
        
        lesson_progress[lesson.id] = progress
        
        # Count completed lessons for course progress
        if progress and progress.is_completed:
            completed_lessons += 1
            
        # Add to total duration
        if lesson.estimated_duration:
            total_duration += lesson.estimated_duration
    
    # Calculate overall course progress percentage
    course_progress_percentage = 0
    if total_lessons > 0:
        course_progress_percentage = int((completed_lessons / total_lessons) * 100)
    
    # Calculate average difficulty level
    difficulty_levels = [lesson.difficulty_level for lesson in course.lessons if lesson.difficulty_level]
    average_difficulty = 0
    if difficulty_levels:
        average_difficulty = sum(difficulty_levels) / len(difficulty_levels)
    
    # Determine if user has started the course
    has_started = any(progress for progress in lesson_progress.values())
    
    return render_template('course_view.html', 
                         course=course,
                         lesson_progress=lesson_progress,
                         course_progress_percentage=course_progress_percentage,
                         total_lessons=total_lessons,
                         completed_lessons=completed_lessons,
                         total_duration=total_duration,
                         average_difficulty=average_difficulty,
                         has_started=has_started,
                         has_purchased=has_purchased)

@bp.route('/purchase/<int:lesson_id>')
@login_required
def purchase_lesson_page(lesson_id):
    """Display the purchase page for a lesson"""
    lesson = Lesson.query.get_or_404(lesson_id)
    
    # Check if lesson is purchasable
    if not lesson.is_purchasable or lesson.price <= 0:
        flash('This lesson is not available for purchase.', 'warning')
        return redirect(url_for('routes.lessons'))
    
    # Check if user already owns this lesson
    existing_purchase = LessonPurchase.query.filter_by(
        user_id=current_user.id, 
        lesson_id=lesson_id
    ).first()
    
    if existing_purchase:
        flash('You already own this lesson!', 'info')
        return redirect(url_for('routes.view_lesson', lesson_id=lesson_id))
    
    # Check if user can access this lesson for free (shouldn't happen, but safety check)
    accessible, message = lesson.is_accessible_to_user(current_user)
    if accessible:
        flash('This lesson is already accessible to you.', 'info')
        return redirect(url_for('routes.view_lesson', lesson_id=lesson_id))
    
    form = CSRFTokenForm()
    return render_template('purchase.html', lesson=lesson, form=form)

@bp.route('/lessons/<int:lesson_id>')
def view_lesson(lesson_id):
    """View a specific lesson — bei Paywall-Trigger eigene Conversion-Seite statt Redirect."""
    lesson = Lesson.query.get_or_404(lesson_id)

    # Check if user can access this lesson (supports both authenticated and guest users)
    user = current_user if current_user.is_authenticated else None
    accessible, message = lesson.is_accessible_to_user(user)
    if not accessible:
        # Paid Lesson + nicht zugaenglich → Paywall-Seite (Bundle-CTA + Single-Kauf)
        # statt Flash-Redirect, das Frust ohne Aktion erzeugte.
        if (lesson.price or 0) > 0 and lesson.is_purchasable:
            from app.services.bundle_service import (
                get_n5_bundle_price, EARLY_BIRD_PRICE_CHF, REGULAR_PRICE_CHF,
            )
            bundle_price, _ = get_n5_bundle_price()
            # Anzahl paid Lessons im Modul (fuer Bundle-Tease)
            paid_total = 0
            if lesson.category:
                paid_total = sum(
                    1 for sibling in lesson.category.lessons
                    if sibling.is_published and (sibling.price or 0) > 0
                    and sibling.id != lesson.id
                )
                # Plus paid Lessons in anderen N5-Modulen — Bundle deckt N5 komplett
                if lesson.category.jlpt_level == 5:
                    other_paid = (
                        db.session.query(Lesson)
                        .join(LessonCategory, Lesson.category_id == LessonCategory.id)
                        .filter(LessonCategory.jlpt_level == 5)
                        .filter(LessonCategory.id != lesson.category.id)
                        .filter(Lesson.is_published.is_(True))
                        .filter(Lesson.price > 0)
                        .count()
                    )
                    paid_total += other_paid
            return render_template(
                'lesson_paywall.html',
                lesson=lesson,
                bundle_price=bundle_price,
                bundle_regular_price=REGULAR_PRICE_CHF,
                bundle_early_bird_price=EARLY_BIRD_PRICE_CHF,
                paid_total=paid_total,
            )
        # Login fehlt
        if not current_user.is_authenticated and 'Login required' in message:
            return redirect(url_for('routes.login', next=request.url))
        # Restfaelle (Voraussetzungen, etc.) — Flash bleibt
        flash(message, 'warning')
        return redirect(url_for('routes.lessons'))
    
    # Get or create user progress (only for authenticated users)
    progress = None
    if current_user.is_authenticated:
        progress = UserLessonProgress.query.filter_by(
            user_id=current_user.id, lesson_id=lesson_id
        ).first()
        
        if not progress:
            try:
                progress = UserLessonProgress(user_id=current_user.id, lesson_id=lesson_id)
                db.session.add(progress)
                db.session.commit()
            except IntegrityError:
                # Another request might have created the record, rollback and try again
                db.session.rollback()
                progress = UserLessonProgress.query.filter_by(
                    user_id=current_user.id, lesson_id=lesson_id
                ).first()
                # If still not found, log the issue but continue without progress tracking
                if not progress:
                    current_app.logger.error(f"Failed to create or find progress record for user {current_user.id}, lesson {lesson_id}")
    
    # Get all quiz questions for this lesson
    quiz_questions = []
    for content in lesson.content_items:
        if content.is_interactive:
            quiz_questions.extend(content.quiz_questions)
    
    # Get user's existing quiz answers (only for authenticated users)
    user_quiz_answers = {}
    if current_user.is_authenticated and quiz_questions:
        question_ids = [q.id for q in quiz_questions]
        answers = UserQuizAnswer.query.filter(
            UserQuizAnswer.user_id == current_user.id,
            UserQuizAnswer.question_id.in_(question_ids)
        ).all()
        
        # Create a lookup dictionary: question_id -> UserQuizAnswer
        user_quiz_answers = {answer.question_id: answer for answer in answers}
    
    # Internal Linking: vorherige + naechste Lesson im selben Modul finden,
    # plus uebergeordnetes Modul. Boostet Topic-Cluster + UX (klickbar weiter).
    prev_lesson = None
    next_lesson = None
    parent_module = lesson.category if lesson.category else None
    if parent_module:
        siblings = sorted(
            [l for l in parent_module.lessons
             if l.is_published and l.instruction_language == lesson.instruction_language],
            key=lambda l: (l.order_index or 0, l.id)
        )
        try:
            idx = siblings.index(lesson)
            prev_lesson = siblings[idx - 1] if idx > 0 else None
            next_lesson = siblings[idx + 1] if idx + 1 < len(siblings) else None
        except ValueError:
            pass

    form = CSRFTokenForm()
    return render_template('lesson_view.html', lesson=lesson, progress=progress, form=form,
                           user_quiz_answers=user_quiz_answers,
                           prev_lesson=prev_lesson, next_lesson=next_lesson,
                           parent_module=parent_module)

# --- API Routes for Content Management ---

# == KANA CRUD API ==
@bp.route('/api/admin/kana', methods=['GET'])
@login_required
@admin_required
def list_kana():
    items = Kana.query.all()
    return jsonify([model_to_dict(item) for item in items])

@bp.route('/api/admin/kana/new', methods=['POST'])
@login_required
@admin_required
def create_kana():
    data = request.json
    if not data or not data.get('character') or not data.get('romanization') or not data.get('type'):
        return jsonify({"error": "Missing required fields"}), 400

    existing_kana = Kana.query.filter_by(character=data['character']).first()
    if existing_kana:
        return jsonify({"error": "Kana character already exists"}), 400

    new_item = Kana(
        character=data['character'],
        romanization=data['romanization'],
        type=data['type'],
        stroke_order_info=data.get('stroke_order_info'),
        example_sound_url=data.get('example_sound_url'),
        mnemonic=data.get('mnemonic')
    )
    try:
        db.session.add(new_item)
        db.session.commit()
        return jsonify(model_to_dict(new_item)), 201
    except IntegrityError: # Handles unique constraint violations
        db.session.rollback()
        # This specific error for character uniqueness is already checked above,
        # but this handles it at the DB level just in case or for other integrity issues.
        return jsonify({"error": "Database integrity error. This item might already exist or violate other constraints."}), 409
    except SQLAlchemyError as e: # Handles other SQLAlchemy errors
        db.session.rollback()
        # Log the error e for debugging: app.logger.error(f"Database error: {e}")
        return jsonify({"error": "Database error occurred."}), 500

@bp.route('/api/admin/kana/<int:item_id>', methods=['GET'])
@login_required
@admin_required
def get_kana(item_id):
    item = Kana.query.get_or_404(item_id)
    return jsonify(model_to_dict(item))

@bp.route('/api/admin/kana/<int:item_id>/edit', methods=['PUT', 'PATCH'])
@login_required
@admin_required
def update_kana(item_id):
    item = Kana.query.get_or_404(item_id)
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    item.character = data.get('character', item.character)
    item.romanization = data.get('romanization', item.romanization)
    item.type = data.get('type', item.type)
    item.stroke_order_info = data.get('stroke_order_info', item.stroke_order_info)
    item.example_sound_url = data.get('example_sound_url', item.example_sound_url)
    item.mnemonic = data.get('mnemonic', item.mnemonic)

    db.session.commit()
    return jsonify(model_to_dict(item))

@bp.route('/api/admin/kana/<int:item_id>/delete', methods=['DELETE'])
@login_required
@admin_required
def delete_kana(item_id):
    item = Kana.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Kana deleted successfully"}), 200

# == KANJI CRUD API ==
@bp.route('/api/admin/kanji', methods=['GET'])
@login_required
@admin_required
def list_kanji():
    items = Kanji.query.all()
    return jsonify([model_to_dict(item) for item in items])

@bp.route('/api/admin/kanji/new', methods=['POST'])
@login_required
@admin_required
def create_kanji():
    data = request.json
    if not data or not data.get('character') or not data.get('meaning'):
        return jsonify({"error": "Missing required fields: character, meaning"}), 400

    existing_kanji = Kanji.query.filter_by(character=data['character']).first()
    if existing_kanji:
        return jsonify({"error": "Kanji character already exists"}), 400

    new_item = Kanji(
        character=data['character'],
        meaning=data['meaning'],
        onyomi=data.get('onyomi'),
        kunyomi=data.get('kunyomi'),
        jlpt_level=data.get('jlpt_level'),
        stroke_order_info=data.get('stroke_order_info'),
        radical=data.get('radical'),
        stroke_count=data.get('stroke_count')
    )
    try:
        db.session.add(new_item)
        db.session.commit()
        return jsonify(model_to_dict(new_item)), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Database integrity error. This item might already exist or violate other constraints."}), 409
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": "Database error occurred."}), 500

@bp.route('/api/admin/kanji/<int:item_id>', methods=['GET'])
@login_required
@admin_required
def get_kanji(item_id):
    item = Kanji.query.get_or_404(item_id)
    return jsonify(model_to_dict(item))

@bp.route('/api/admin/kanji/<int:item_id>/edit', methods=['PUT', 'PATCH'])
@login_required
@admin_required
def update_kanji(item_id):
    item = Kanji.query.get_or_404(item_id)
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    item.character = data.get('character', item.character)
    item.meaning = data.get('meaning', item.meaning)
    item.onyomi = data.get('onyomi', item.onyomi)
    item.kunyomi = data.get('kunyomi', item.kunyomi)
    item.jlpt_level = data.get('jlpt_level', item.jlpt_level)
    item.stroke_order_info = data.get('stroke_order_info', item.stroke_order_info)
    item.radical = data.get('radical', item.radical)
    item.stroke_count = data.get('stroke_count', item.stroke_count)

    db.session.commit()
    return jsonify(model_to_dict(item))

@bp.route('/api/admin/kanji/<int:item_id>/delete', methods=['DELETE'])
@login_required
@admin_required
def delete_kanji(item_id):
    item = Kanji.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Kanji deleted successfully"}), 200

# == VOCABULARY CRUD API ==
@bp.route('/api/admin/vocabulary', methods=['GET'])
@login_required
@admin_required
def list_vocabulary():
    items = Vocabulary.query.all()
    return jsonify([model_to_dict(item) for item in items])

@bp.route('/api/admin/vocabulary/new', methods=['POST'])
@login_required
@admin_required
def create_vocabulary():
    data = request.json
    if not data or not data.get('word') or not data.get('reading') or not data.get('meaning'):
        return jsonify({"error": "Missing required fields: word, reading, meaning"}), 400

    existing_vocab = Vocabulary.query.filter_by(word=data['word']).first()
    if existing_vocab:
        return jsonify({"error": "Vocabulary word already exists"}), 400

    new_item = Vocabulary(
        word=data['word'],
        reading=data['reading'],
        meaning=data['meaning'],
        jlpt_level=data.get('jlpt_level'),
        example_sentence_japanese=data.get('example_sentence_japanese'),
        example_sentence_english=data.get('example_sentence_english'),
        audio_url=data.get('audio_url')
    )
    try:
        db.session.add(new_item)
        db.session.commit()
        return jsonify(model_to_dict(new_item)), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Database integrity error. This item might already exist or violate other constraints."}), 409
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": "Database error occurred."}), 500

@bp.route('/api/admin/vocabulary/<int:item_id>', methods=['GET'])
@login_required
@admin_required
def get_vocabulary(item_id):
    item = Vocabulary.query.get_or_404(item_id)
    return jsonify(model_to_dict(item))

@bp.route('/api/admin/vocabulary/<int:item_id>/edit', methods=['PUT', 'PATCH'])
@login_required
@admin_required
def update_vocabulary(item_id):
    item = Vocabulary.query.get_or_404(item_id)
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    item.word = data.get('word', item.word)
    item.reading = data.get('reading', item.reading)
    item.meaning = data.get('meaning', item.meaning)
    item.jlpt_level = data.get('jlpt_level', item.jlpt_level)
    item.example_sentence_japanese = data.get('example_sentence_japanese', item.example_sentence_japanese)
    item.example_sentence_english = data.get('example_sentence_english', item.example_sentence_english)
    item.audio_url = data.get('audio_url', item.audio_url)

    db.session.commit()
    return jsonify(model_to_dict(item))

@bp.route('/api/admin/vocabulary/<int:item_id>/delete', methods=['DELETE'])
@login_required
@admin_required
def delete_vocabulary(item_id):
    item = Vocabulary.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Vocabulary item deleted successfully"}), 200

# == GRAMMAR CRUD API ==
@bp.route('/api/admin/grammar', methods=['GET'])
@login_required
@admin_required
def list_grammar():
    items = Grammar.query.all()
    return jsonify([model_to_dict(item) for item in items])

@bp.route('/api/admin/grammar/new', methods=['POST'])
@login_required
@admin_required
def create_grammar():
    data = request.json
    if not data or not data.get('title') or not data.get('explanation'):
        return jsonify({"error": "Missing required fields: title, explanation"}), 400

    existing_grammar = Grammar.query.filter_by(title=data['title']).first()
    if existing_grammar:
        return jsonify({"error": "Grammar title already exists"}), 400

    new_item = Grammar(
        title=data['title'],
        explanation=data['explanation'],
        structure=data.get('structure'),
        romaji=data.get('romaji'),
        jlpt_level=data.get('jlpt_level'),
        example_sentences=data.get('example_sentences')
    )
    try:
        db.session.add(new_item)
        db.session.commit()
        return jsonify(model_to_dict(new_item)), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Database integrity error. This item might already exist or violate other constraints."}), 409
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": "Database error occurred."}), 500

@bp.route('/api/admin/grammar/<int:item_id>', methods=['GET'])
@login_required
@admin_required
def get_grammar(item_id):
    item = Grammar.query.get_or_404(item_id)
    return jsonify(model_to_dict(item))

@bp.route('/api/admin/grammar/<int:item_id>/edit', methods=['PUT', 'PATCH'])
@login_required
@admin_required
def update_grammar(item_id):
    item = Grammar.query.get_or_404(item_id)
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    item.title = data.get('title', item.title)
    item.explanation = data.get('explanation', item.explanation)
    item.structure = data.get('structure', item.structure)
    item.romaji = data.get('romaji', item.romaji)
    item.jlpt_level = data.get('jlpt_level', item.jlpt_level)
    item.example_sentences = data.get('example_sentences', item.example_sentences)

    db.session.commit()
    return jsonify(model_to_dict(item))

@bp.route('/api/admin/grammar/<int:item_id>/delete', methods=['DELETE'])
@login_required
@admin_required
def delete_grammar(item_id):
    item = Grammar.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Grammar point deleted successfully"}), 200

# == CONTENT APPROVAL API ==
@bp.route('/api/admin/content/<content_type>/<int:item_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_content(content_type, item_id):
    model = {'kanji': Kanji, 'vocabulary': Vocabulary, 'grammar': Grammar}.get(content_type)
    if not model:
        return jsonify({"error": "Invalid content type"}), 400
    
    item = model.query.get_or_404(item_id)
    item.status = 'approved'
    db.session.commit()
    return jsonify({"message": f"{content_type.capitalize()} item approved successfully"}), 200

@bp.route('/api/admin/content/<content_type>/<int:item_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_content(content_type, item_id):
    model = {'kanji': Kanji, 'vocabulary': Vocabulary, 'grammar': Grammar}.get(content_type)
    if not model:
        return jsonify({"error": "Invalid content type"}), 400
    
    item = model.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": f"{content_type.capitalize()} item rejected and deleted successfully"}), 200

# == LESSON CATEGORY CRUD API ==
@bp.route('/api/admin/categories', methods=['GET'])
@login_required
@admin_required
def list_categories():
    items = LessonCategory.query.all()
    return jsonify([model_to_dict(item) for item in items])

@bp.route('/api/admin/categories/new', methods=['POST'])
@login_required
@admin_required
def create_category():
    data = request.json
    if not data or not data.get('name'):
        return jsonify({"error": "Missing required field: name"}), 400

    existing_category = LessonCategory.query.filter_by(name=data['name']).first()
    if existing_category:
        return jsonify({"error": "Category name already exists"}), 400

    new_item = LessonCategory(
        name=data['name'],
        description=data.get('description'),
        color_code=data.get('color_code', '#007bff')
    )
    try:
        db.session.add(new_item)
        db.session.commit()
        return jsonify(model_to_dict(new_item)), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Database integrity error."}), 409
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Database error occurred."}), 500

@bp.route('/api/admin/categories/<int:item_id>', methods=['GET'])
@login_required
@admin_required
def get_category(item_id):
    item = LessonCategory.query.get_or_404(item_id)
    return jsonify(model_to_dict(item))

@bp.route('/api/admin/categories/<int:item_id>/edit', methods=['PUT', 'PATCH'])
@login_required
@admin_required
def update_category(item_id):
    item = LessonCategory.query.get_or_404(item_id)
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    item.name = data.get('name', item.name)
    item.description = data.get('description', item.description)
    item.color_code = data.get('color_code', item.color_code)

    db.session.commit()
    return jsonify(model_to_dict(item))

@bp.route('/api/admin/categories/<int:item_id>/delete', methods=['DELETE'])
@login_required
@admin_required
def delete_category(item_id):
    item = LessonCategory.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Category deleted successfully"}), 200

# == COURSE CRUD API ==
@bp.route('/api/admin/courses', methods=['GET'])
@login_required
@admin_required
def list_courses():
    items = Course.query.all()
    return jsonify([model_to_dict(item) for item in items])

@bp.route('/api/admin/courses/new', methods=['POST'])
@login_required
@admin_required
def create_course():
    # Validate CSRF token from header
    from flask_wtf.csrf import validate_csrf
    try:
        csrf_token = request.headers.get('X-CSRFToken')
        if not csrf_token:
            return jsonify({"error": "CSRF token missing"}), 400
        validate_csrf(csrf_token)
    except Exception as e:
        return jsonify({"error": "CSRF token invalid"}), 400
    
    data = request.json
    if not data or not data.get('title'):
        return jsonify({"error": "Missing required field: title"}), 400

    new_item = Course(
        title=data['title'],
        description=data.get('description'),
        background_image_url=data.get('background_image_url'),
        is_published=data.get('is_published', False)
    )
    
    # Handle lesson assignments
    if 'lessons' in data:
        lesson_ids = data['lessons']
        for lesson_id in lesson_ids:
            lesson = Lesson.query.get(lesson_id)
            if lesson:
                new_item.lessons.append(lesson)
    
    try:
        db.session.add(new_item)
        db.session.commit()
        return jsonify(model_to_dict(new_item)), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Database integrity error."}), 409
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Database error occurred."}), 500

@bp.route('/api/admin/courses/<int:item_id>', methods=['GET'])
@login_required
@admin_required
def get_course(item_id):
    item = Course.query.get_or_404(item_id)
    course_dict = model_to_dict(item)
    course_dict['lessons'] = [model_to_dict(lesson) for lesson in item.lessons]
    return jsonify(course_dict)

@bp.route('/api/admin/courses/<int:item_id>/edit', methods=['PUT', 'PATCH'])
@login_required
@admin_required
def update_course(item_id):
    item = Course.query.get_or_404(item_id)
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    item.title = data.get('title', item.title)
    item.description = data.get('description', item.description)
    item.background_image_url = data.get('background_image_url', item.background_image_url)
    item.is_published = data.get('is_published', item.is_published)
    item.price = data.get('price', item.price)
    item.is_purchasable = data.get('is_purchasable', item.is_purchasable)

    if 'lessons' in data:
        item.lessons = []
        for lesson_id in data['lessons']:
            lesson = Lesson.query.get(lesson_id)
            if lesson:
                item.lessons.append(lesson)

    db.session.commit()
    return jsonify(model_to_dict(item))

@bp.route('/api/admin/courses/<int:item_id>/delete', methods=['DELETE'])
@login_required
@admin_required
def delete_course(item_id):
    item = Course.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Course deleted successfully"}), 200

# == LESSON CRUD API ==
@bp.route('/api/admin/lessons', methods=['GET'])
@login_required
@admin_required
def list_lessons():
    items = Lesson.query.order_by(Lesson.order_index.asc(), Lesson.id.asc()).all()
    lessons_data = []
    for item in items:
        lesson_dict = model_to_dict(item)
        lesson_dict['category_name'] = item.category.name if item.category else None
        lesson_dict['content_count'] = len(item.content_items)
        lessons_data.append(lesson_dict)
    return jsonify(lessons_data)

@bp.route('/api/admin/lessons/new', methods=['POST'])
@login_required
@admin_required
def create_lesson():
    data = request.json
    if not data or not data.get('title') or not data.get('lesson_type'):
        return jsonify({"error": "Missing required fields: title, lesson_type"}), 400

    existing_lesson = Lesson.query.filter_by(title=data['title']).first()
    if existing_lesson:
        return jsonify({"error": "Lesson title already exists"}), 400

    new_item = Lesson(
        title=data['title'],
        description=data.get('description'),
        lesson_type=data['lesson_type'],
        category_id=data.get('category_id'),
        difficulty_level=data.get('difficulty_level'),
        estimated_duration=data.get('estimated_duration'),
        order_index=data.get('order_index', 0),
        is_published=data.get('is_published', False),
        allow_guest_access=data.get('allow_guest_access', False),
        instruction_language=data.get('instruction_language', 'english'),
        show_romaji_on_front=data.get('show_romaji_on_front', True),
        thumbnail_url=data.get('thumbnail_url'),
        video_intro_url=data.get('video_intro_url')
    )
    try:
        db.session.add(new_item)
        db.session.commit()
        return jsonify(model_to_dict(new_item)), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Database integrity error."}), 409
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Database error occurred."}), 500

@bp.route('/api/admin/lessons/<int:item_id>', methods=['GET'])
@login_required
@admin_required
def get_lesson(item_id):
    item = Lesson.query.get_or_404(item_id)
    lesson_dict = model_to_dict(item)
    lesson_dict['background_image_url'] = item.get_background_url()
    lesson_dict['thumbnail_url'] = item.get_thumbnail_url()
    lesson_dict['category_name'] = item.category.name if item.category else None
    
    # Build pages from content items (pages with content)
    pages_data = []
    seen_page_numbers = set()
    for page in item.pages:
        content_dicts = []
        for c in page['content']:
            cd = model_to_dict(c)
            # Add detail_text summary for display in page editor
            ref = c.get_content_data()
            if c.content_type == 'kana' and ref:
                cd['detail_text'] = f"{ref.character} ({ref.romanization}) — {ref.type}"
            elif c.content_type == 'kanji' and ref:
                cd['detail_text'] = f"{ref.character} — {ref.meaning}"
                if ref.onyomi:
                    cd['detail_text'] += f" | On: {ref.onyomi}"
                if ref.kunyomi:
                    cd['detail_text'] += f" | Kun: {ref.kunyomi}"
            elif c.content_type == 'vocabulary' and ref:
                cd['detail_text'] = f"{ref.word} ({ref.reading}) — {ref.meaning}"
            elif c.content_type == 'grammar' and ref:
                cd['detail_text'] = f"{ref.title}"
                if ref.structure:
                    cd['detail_text'] += f" | {ref.structure}"
            content_dicts.append(cd)
        page_num = page['content'][0].page_number if page['content'] else None
        if page_num is not None:
            seen_page_numbers.add(page_num)
            page_info = {
                'page_number': page_num,
                'content': content_dicts,
                'metadata': model_to_dict(page['metadata']) if page['metadata'] else None
            }
            pages_data.append(page_info)

    # Also include empty LessonPage entries (pages with metadata but no content)
    for lp in item.pages_metadata:
        if lp.page_number not in seen_page_numbers:
            pages_data.append({
                'page_number': lp.page_number,
                'content': [],
                'metadata': model_to_dict(lp)
            })

    lesson_dict['pages'] = sorted(pages_data, key=lambda p: p['page_number'])
    lesson_dict['prerequisites'] = [model_to_dict(prereq.prerequisite_lesson) for prereq in item.prerequisites]
    
    # For backward compatibility or other uses, you might still want a flat list of content_items
    lesson_dict['content_items'] = [model_to_dict(content) for content in item.content_items]

    return jsonify(lesson_dict)

@bp.route('/api/admin/lessons/<int:item_id>/edit', methods=['PUT', 'PATCH'])
@login_required
@admin_required
def update_lesson(item_id):
    item = Lesson.query.get_or_404(item_id)
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    item.title = data.get('title', item.title)
    item.description = data.get('description', item.description)
    item.lesson_type = data.get('lesson_type', item.lesson_type)
    item.category_id = data.get('category_id', item.category_id)
    item.difficulty_level = data.get('difficulty_level', item.difficulty_level)
    item.estimated_duration = data.get('estimated_duration', item.estimated_duration)
    item.order_index = data.get('order_index', item.order_index)
    item.is_published = data.get('is_published', item.is_published)
    # Convert string 'on' to boolean for allow_guest_access
    allow_guest_access = data.get('allow_guest_access', item.allow_guest_access)
    if isinstance(allow_guest_access, str):
        item.allow_guest_access = allow_guest_access.lower() in ['true', 'on', '1', 'yes']
    else:
        item.allow_guest_access = bool(allow_guest_access) if allow_guest_access is not None else item.allow_guest_access
    item.instruction_language = data.get('instruction_language', item.instruction_language)
    show_romaji_on_front = data.get('show_romaji_on_front', item.show_romaji_on_front)
    if isinstance(show_romaji_on_front, str):
        item.show_romaji_on_front = show_romaji_on_front.lower() in ['true', 'on', '1', 'yes']
    else:
        item.show_romaji_on_front = bool(show_romaji_on_front) if show_romaji_on_front is not None else item.show_romaji_on_front
    item.thumbnail_url = data.get('thumbnail_url', item.thumbnail_url)
    item.video_intro_url = data.get('video_intro_url', item.video_intro_url)

    # Handle pricing fields
    if 'price' in data:
        try:
            price = float(data['price'])
            if price < 0:
                return jsonify({"error": "Price cannot be negative"}), 400
            item.price = price
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid price format"}), 400
    
    # Handle is_purchasable field
    is_purchasable = data.get('is_purchasable', item.is_purchasable)
    if isinstance(is_purchasable, str):
        item.is_purchasable = is_purchasable.lower() in ['true', 'on', '1', 'yes']
    else:
        item.is_purchasable = bool(is_purchasable) if is_purchasable is not None else item.is_purchasable

    # Handle course assignment
    if 'course_ids' in data:
        # Clear existing course relationships
        item.courses = []
        # Add new course relationships
        for course_id in data['course_ids']:
            course = Course.query.get(course_id)
            if course:
                item.courses.append(course)

    db.session.commit()
    return jsonify(model_to_dict(item))

@bp.route('/api/admin/lessons/<int:item_id>/delete', methods=['DELETE'])
@login_required
@admin_required
def delete_lesson(item_id):
    item = Lesson.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Lesson deleted successfully"}), 200

@bp.route('/api/admin/lessons/<int:lesson_id>/move', methods=['POST'])
@login_required
@admin_required
def move_lesson(lesson_id):
    """Move a lesson up or down in order globally across all categories."""
    data = request.json
    direction = data.get('direction')
    if direction not in ['up', 'down']:
        return jsonify({"error": "Invalid direction specified"}), 400

    lesson_to_move = Lesson.query.get_or_404(lesson_id)
    
    # Get all lessons ordered by order_index globally (not by category)
    lessons = Lesson.query.order_by(Lesson.order_index, Lesson.id).all()
    
    # Find the current position of the lesson to move
    current_position = None
    for i, lesson in enumerate(lessons):
        if lesson.id == lesson_id:
            current_position = i
            break
    
    if current_position is None:
        return jsonify({"error": "Lesson not found"}), 404
    
    # Calculate new position
    if direction == 'up':
        if current_position == 0:
            return jsonify({"error": "Cannot move lesson further up"}), 400
        new_position = current_position - 1
    else:  # direction == 'down'
        if current_position == len(lessons) - 1:
            return jsonify({"error": "Cannot move lesson further down"}), 400
        new_position = current_position + 1
    
    # Reorder the list
    lesson_to_move_obj = lessons.pop(current_position)
    lessons.insert(new_position, lesson_to_move_obj)
    
    # Update order indices for all lessons globally
    try:
        for index, lesson in enumerate(lessons):
            lesson.order_index = index
        
        db.session.commit()
        current_app.logger.info(f"Lesson {lesson_id} moved {direction} globally")
        return jsonify({"message": "Lesson moved successfully"}), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error moving lesson: {e}")
        return jsonify({"error": "Database error occurred"}), 500

@bp.route('/api/admin/lessons/reorder', methods=['POST'])
@login_required
@admin_required
def reorder_lessons():
    """Reorder lessons based on provided order."""
    data = request.json
    lesson_ids = data.get('lesson_ids', [])
    category_id = data.get('category_id')  # Optional: reorder within specific category
    
    if not lesson_ids:
        return jsonify({"error": "No lesson IDs provided"}), 400
    
    try:
        # Get all lessons to reorder
        if category_id:
            lessons = Lesson.query.filter(
                Lesson.category_id == category_id,
                Lesson.id.in_(lesson_ids)
            ).all()
        else:
            lessons = Lesson.query.filter(Lesson.id.in_(lesson_ids)).all()
        
        # Create a mapping of ID to lesson
        lesson_map = {lesson.id: lesson for lesson in lessons}
        
        # Verify all provided IDs exist
        if len(lesson_map) != len(lesson_ids):
            return jsonify({"error": "Some lesson IDs not found"}), 404
        
        # Update order indices based on the provided order
        for index, lesson_id in enumerate(lesson_ids):
            lesson_map[lesson_id].order_index = index
        
        db.session.commit()
        current_app.logger.info(f"Reordered {len(lesson_ids)} lessons in category {category_id or 'All'}")
        return jsonify({"message": "Lessons reordered successfully"}), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error reordering lessons: {e}")
        return jsonify({"error": "Database error occurred"}), 500

# == CONTENT OPTIONS API ==
@bp.route('/api/admin/content-options/<content_type>', methods=['GET'])
@login_required
@admin_required
def get_content_options(content_type):
    """Get available content items for selection in lesson builder"""
    try:
        if content_type == 'kana':
            items = Kana.query.all()
        elif content_type == 'kanji':
            items = Kanji.query.all()
        elif content_type == 'vocabulary':
            items = Vocabulary.query.all()
        elif content_type == 'grammar':
            items = Grammar.query.all()
        else:
            return jsonify({"error": "Invalid content type"}), 400
        
        return jsonify([model_to_dict(item) for item in items])
    except Exception as e:
        return jsonify({"error": "Failed to load content options"}), 500

# == LESSON CONTENT API ==
@bp.route('/api/admin/lessons/<int:lesson_id>/content', methods=['GET'])
@login_required
@admin_required
def list_lesson_content(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    content_items = LessonContent.query.filter_by(lesson_id=lesson_id).order_by(LessonContent.order_index).all()
    return jsonify([model_to_dict(item) for item in content_items])

@bp.route('/api/admin/lessons/<int:lesson_id>/content/new', methods=['POST'])
@login_required
@admin_required
def add_lesson_content(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    data = request.json
    if not data or not data.get('content_type'):
        return jsonify({"error": "Missing required field: content_type"}), 400

    page_number = data.get('page_number', 1)

    # Ensure a LessonPage entry exists for this page
    lesson_page = LessonPage.query.filter_by(lesson_id=lesson_id, page_number=page_number).first()
    if not lesson_page:
        lesson_page = LessonPage(
            lesson_id=lesson_id, 
            page_number=page_number,
            title=f"Page {page_number}" # Default title
        )
        db.session.add(lesson_page)

    # Convert string 'false'/'true' to boolean for is_optional
    is_optional = data.get('is_optional', False)
    if isinstance(is_optional, str):
        is_optional = is_optional.lower() == 'true'

    # Determine the next order index for the given page
    last_content_on_page = LessonContent.query.filter_by(lesson_id=lesson_id, page_number=page_number).order_by(LessonContent.order_index.desc()).first()
    next_order_index = (last_content_on_page.order_index + 1) if last_content_on_page else 0

    new_content = LessonContent(
        lesson_id=lesson_id,
        content_type=data['content_type'],
        content_id=data.get('content_id'),
        title=data.get('title'),
        content_text=data.get('content_text'),
        media_url=data.get('media_url'),
        order_index=next_order_index,
        page_number=page_number,
        is_optional=is_optional
    )
    try:
        db.session.add(new_content)
        db.session.commit()
        return jsonify(model_to_dict(new_content)), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": f"Database error occurred: {str(e)}"}), 500

def reorder_page_content(lesson_id, page_number):
    """Reorder all content items on a specific page to maintain sequential order indices"""
    try:
        # Get all content items on the page, ordered by current order_index
        content_items = LessonContent.query.filter(
            LessonContent.lesson_id == lesson_id,
            LessonContent.page_number == page_number
        ).order_by(LessonContent.order_index, LessonContent.id).all()
        
        # Reassign order indices starting from 0
        for index, content_item in enumerate(content_items):
            old_order = content_item.order_index
            content_item.order_index = index
            current_app.logger.debug(f"Content {content_item.id}: {old_order} -> {index}")
        
        db.session.commit()
        current_app.logger.info(f"Reordered {len(content_items)} content items on page {page_number} to sequential indices 0-{len(content_items)-1}")
        
    except Exception as e:
        current_app.logger.error(f"Error reordering content on page {page_number}: {e}")
        db.session.rollback()
        raise e

def force_reorder_all_lesson_content(lesson_id):
    """Force reorder all content in a lesson to fix any gaps in order indices"""
    try:
        # Get all pages with content
        pages_with_content = db.session.query(LessonContent.page_number).filter(
            LessonContent.lesson_id == lesson_id
        ).distinct().all()
        
        for (page_number,) in pages_with_content:
            reorder_page_content(lesson_id, page_number)
        
        current_app.logger.info(f"Force reordered all content for lesson {lesson_id}")
        
    except Exception as e:
        current_app.logger.error(f"Error force reordering lesson {lesson_id}: {e}")

@bp.route('/api/admin/lessons/<int:lesson_id>/content/<int:content_id>/delete', methods=['DELETE'])
@login_required
@admin_required
def remove_lesson_content(lesson_id, content_id):
    content = LessonContent.query.filter_by(lesson_id=lesson_id, id=content_id).first_or_404()

    # Store content info for reordering before deletion
    content_page = content.page_number
    content_order = content.order_index

    try:
        # Delete file from disk if it exists
        file_deletion_success = True
        if content.file_path:
            try:
                content.delete_file()
                current_app.logger.info(f"File deleted successfully for content {content_id}")
            except Exception as file_error:
                current_app.logger.error(f"Failed to delete file for content {content_id}: {file_error}")
                file_deletion_success = False

        # Delete the content record from database
        db.session.delete(content)
        db.session.commit()
        
        current_app.logger.info(f"Content {content_id} deleted from lesson {lesson_id}, page {content_page}, order {content_order}")
        
        # Force complete reordering of the page to ensure sequential indices
        try:
            reorder_page_content(lesson_id, content_page)
            current_app.logger.info(f"Page {content_page} reordered after deletion")
        except Exception as reorder_error:
            current_app.logger.error(f"Error reordering page {content_page} after deletion: {reorder_error}")
            # Return an error to the client so the UI can show a proper message
            return jsonify({"error": f"Content was deleted, but reordering the page failed: {reorder_error}. Please refresh."}), 500
        
        if file_deletion_success:
            return jsonify({"message": "Content removed from lesson successfully"}), 200
        else:
            return jsonify({"message": "Content removed from lesson, but file deletion failed"}), 200
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error removing lesson content {content_id} from lesson {lesson_id}: {e}", exc_info=True)
        return jsonify({"error": f"Failed to remove lesson content: {str(e)}"}), 500

@bp.route('/api/admin/lessons/<int:lesson_id>/content/<int:content_id>/move', methods=['POST'])
@login_required
@admin_required
def move_lesson_content(lesson_id, content_id):
    """Move a lesson content item up or down in order."""
    data = request.json
    direction = data.get('direction')
    if direction not in ['up', 'down']:
        return jsonify({"error": "Invalid direction specified"}), 400

    content_to_move = LessonContent.query.filter_by(id=content_id, lesson_id=lesson_id).first_or_404()
    page_number = content_to_move.page_number
    
    # Get all content items on the same page, ordered by current order_index
    content_items = LessonContent.query.filter(
        LessonContent.lesson_id == lesson_id,
        LessonContent.page_number == page_number
    ).order_by(LessonContent.order_index, LessonContent.id).all()
    
    # Find the current position of the item to move
    current_position = None
    for i, item in enumerate(content_items):
        if item.id == content_id:
            current_position = i
            break
    
    if current_position is None:
        return jsonify({"error": "Content item not found"}), 404
    
    # Calculate new position
    if direction == 'up':
        if current_position == 0:
            return jsonify({"error": "Cannot move item further up"}), 400
        new_position = current_position - 1
    else:  # direction == 'down'
        if current_position == len(content_items) - 1:
            return jsonify({"error": "Cannot move item further down"}), 400
        new_position = current_position + 1
    
    # Reorder the list
    item_to_move = content_items.pop(current_position)
    content_items.insert(new_position, item_to_move)
    
    # Update order indices for all items
    try:
        for index, item in enumerate(content_items):
            item.order_index = index
        
        db.session.commit()
        current_app.logger.info(f"Content {content_id} moved {direction} on page {page_number}")
        return jsonify({"message": "Content moved successfully"}), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error moving content: {e}")
        return jsonify({"error": "Database error occurred"}), 500

@bp.route('/api/admin/lessons/<int:lesson_id>/pages/<int:page_number>/reorder', methods=['POST'])
@login_required
@admin_required
def reorder_page_content_api(lesson_id, page_number):
    """Reorder content items on a page based on provided order."""
    data = request.json
    content_ids = data.get('content_ids', [])
    
    if not content_ids:
        return jsonify({"error": "No content IDs provided"}), 400
    
    try:
        # Get all content items for this page
        content_items = LessonContent.query.filter(
            LessonContent.lesson_id == lesson_id,
            LessonContent.page_number == page_number,
            LessonContent.id.in_(content_ids)
        ).all()
        
        # Create a mapping of ID to content item
        content_map = {item.id: item for item in content_items}
        
        # Verify all provided IDs exist
        if len(content_map) != len(content_ids):
            return jsonify({"error": "Some content IDs not found"}), 404
        
        # Update order indices based on the provided order
        for index, content_id in enumerate(content_ids):
            content_map[content_id].order_index = index
        
        db.session.commit()
        current_app.logger.info(f"Reordered {len(content_ids)} items on page {page_number} of lesson {lesson_id}")
        return jsonify({"message": "Content reordered successfully"}), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error reordering content: {e}")
        return jsonify({"error": "Database error occurred"}), 500

@bp.route('/api/admin/lessons/<int:item_id>/patch', methods=['PATCH'])
@login_required
@admin_required
def patch_lesson(item_id):
    """Partial update of a lesson — used for inline-edit of single fields."""
    item = Lesson.query.get_or_404(item_id)
    data = request.json or {}
    allowed = {'title', 'description', 'is_published', 'lesson_type', 'order_index',
               'instruction_language', 'difficulty_level', 'estimated_duration'}
    for key, value in data.items():
        if key in allowed:
            setattr(item, key, value)
    try:
        db.session.commit()
        return jsonify(model_to_dict(item)), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error patching lesson: {e}")
        return jsonify({"error": "Database error"}), 500


@bp.route('/api/admin/lessons/<int:lesson_id>/pages/reorder', methods=['POST'])
@login_required
@admin_required
def reorder_lesson_pages(lesson_id):
    """Reorder pages inside a lesson by renumbering page_number based on provided list."""
    Lesson.query.get_or_404(lesson_id)
    data = request.json or {}
    ordered_old_numbers = data.get('page_numbers', [])
    if not ordered_old_numbers:
        return jsonify({"error": "No page_numbers provided"}), 400

    try:
        # Temporary shift to avoid unique-constraint clashes on (lesson_id, page_number)
        OFFSET = 10000
        pages_map = {}
        for old_num in ordered_old_numbers:
            page = LessonPage.query.filter_by(lesson_id=lesson_id, page_number=old_num).first()
            if page:
                pages_map[old_num] = page
                page.page_number = old_num + OFFSET
        db.session.flush()

        # Also shift content items
        content_items = LessonContent.query.filter_by(lesson_id=lesson_id).all()
        for item in content_items:
            item.page_number = item.page_number + OFFSET
        db.session.flush()

        # Now assign new sequential numbers (1..N)
        for new_idx, old_num in enumerate(ordered_old_numbers, start=1):
            page = pages_map.get(old_num)
            if page:
                page.page_number = new_idx
            # Update all content on that old_num to new_idx
            shifted_old = old_num + OFFSET
            LessonContent.query.filter_by(
                lesson_id=lesson_id, page_number=shifted_old
            ).update({LessonContent.page_number: new_idx}, synchronize_session=False)

        db.session.commit()
        return jsonify({"message": "Pages reordered successfully"}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error reordering pages: {e}")
        return jsonify({"error": "Database error occurred"}), 500


@bp.route('/api/admin/lessons/<int:lesson_id>/content/<int:content_id>/move-to-page', methods=['POST'])
@login_required
@admin_required
def move_content_to_page(lesson_id, content_id):
    """Move a content item to a different page, inserted at given position."""
    data = request.json or {}
    target_page = data.get('target_page')
    target_index = data.get('target_index', 0)
    if target_page is None:
        return jsonify({"error": "target_page required"}), 400

    content = LessonContent.query.filter_by(id=content_id, lesson_id=lesson_id).first_or_404()
    old_page = content.page_number

    # Ensure target page exists
    lesson_page = LessonPage.query.filter_by(lesson_id=lesson_id, page_number=target_page).first()
    if not lesson_page:
        lesson_page = LessonPage(lesson_id=lesson_id, page_number=target_page, title=f"Page {target_page}")
        db.session.add(lesson_page)

    try:
        content.page_number = target_page
        db.session.flush()

        # Insert at target_index on target page
        target_items = LessonContent.query.filter_by(
            lesson_id=lesson_id, page_number=target_page
        ).filter(LessonContent.id != content_id).order_by(LessonContent.order_index, LessonContent.id).all()
        target_items.insert(max(0, min(int(target_index), len(target_items))), content)
        for idx, item in enumerate(target_items):
            item.order_index = idx

        # Close gaps on old page
        if old_page != target_page:
            reorder_page_content(lesson_id, old_page)

        db.session.commit()
        return jsonify({"message": "Content moved", "page_number": target_page}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error moving content to page: {e}")
        return jsonify({"error": "Database error occurred"}), 500


@bp.route('/api/admin/audio/record-upload', methods=['POST'])
@login_required
@admin_required
def upload_audio_recording():
    """Accept a MediaRecorder Blob (audio/webm) from the admin recording widget."""
    import os
    import uuid

    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No audio blob in request'}), 400
    blob = request.files['file']
    if not blob or not blob.filename:
        blob.filename = f'recording_{uuid.uuid4().hex}.webm'

    # Force audio type, ensure extension is one of the allowed set
    _, ext = os.path.splitext(blob.filename)
    if ext.lower().lstrip('.') not in current_app.config['ALLOWED_EXTENSIONS']['audio']:
        blob.filename = f'recording_{uuid.uuid4().hex}.webm'

    lesson_id_str = request.form.get('lesson_id')
    lesson_id = int(lesson_id_str) if lesson_id_str and lesson_id_str.isdigit() else None

    try:
        relative_file_path, file_info, error = FileUploadHandler.save_file(blob, 'audio', lesson_id)
        if error:
            return jsonify({'success': False, 'error': error}), 500
        bucket_name = current_app.config.get('GCS_BUCKET_NAME')
        if bucket_name:
            clean_path = relative_file_path.lstrip('/')
            file_url = f"https://storage.googleapis.com/{bucket_name}/{clean_path}"
        else:
            file_url = url_for('routes.uploaded_file', filename=relative_file_path, _external=False)
        return jsonify({
            'success': True,
            'filePath': file_url,
            'dbPath': relative_file_path,
            'fileName': os.path.basename(relative_file_path),
            'originalFilename': blob.filename,
            'fileType': 'audio',
            'fileSize': file_info.get('size'),
            'mimeType': file_info.get('mime_type'),
        }), 200
    except Exception as e:
        current_app.logger.error(f"Audio recording upload failed: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Upload failed'}), 500


@bp.route('/api/admin/content/<int:content_id>/preview', methods=['GET'])
@login_required
@admin_required
def preview_content(content_id):
    """Get content preview data"""
    content = LessonContent.query.get_or_404(content_id)
    
    preview_data = model_to_dict(content)
    
    # Add related data based on content type
    if content.content_type in ['kana', 'kanji', 'vocabulary', 'grammar']:
        content_data = content.get_content_data()
        if content_data:
            preview_data['content_data'] = model_to_dict(content_data)
    
    # Add quiz questions (with options) for interactive content
    if content.is_interactive:
        questions_out = []
        for q in content.quiz_questions:
            qd = model_to_dict(q)
            qd['options'] = [model_to_dict(opt) for opt in q.options]
            questions_out.append(qd)
        preview_data['quiz_questions'] = questions_out

    return jsonify(preview_data)

@bp.route('/api/admin/content/<int:content_id>', methods=['GET'])
@login_required
@admin_required
def get_content_details(content_id):
    """Get full details for a single content item for editing."""
    content = LessonContent.query.get_or_404(content_id)
    content_dict = model_to_dict(content)

    if content.is_interactive:
        question = QuizQuestion.query.filter_by(lesson_content_id=content.id).first()
        if question:
            content_dict['interactive_type'] = question.question_type
            content_dict['question_text'] = question.question_text
            content_dict['explanation'] = question.explanation
            
            if question.question_type == 'multiple_choice':
                options = QuizOption.query.filter_by(question_id=question.id).all()
                content_dict['options'] = [model_to_dict(opt) for opt in options]
            elif question.question_type == 'fill_blank':
                # The correct answers are stored in the explanation field for fill_blank
                content_dict['correct_answers'] = question.explanation
            elif question.question_type == 'true_false':
                true_option = QuizOption.query.filter_by(question_id=question.id, option_text='True').first()
                if true_option:
                    content_dict['correct_answer'] = true_option.is_correct

    return jsonify(content_dict)

@bp.route('/api/admin/content/<int:content_id>/edit', methods=['PUT'])
@login_required
@admin_required
def update_lesson_content(content_id):
    """Update an existing lesson content item."""
    content = LessonContent.query.get_or_404(content_id)
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    try:
        # Common fields
        content.title = data.get('title', content.title)
        content.order_index = int(data.get('order_index', content.order_index))
        content.page_number = int(data.get('page_number', content.page_number))  # Handle page number
        is_optional = data.get('is_optional', content.is_optional)
        if isinstance(is_optional, str):
            content.is_optional = is_optional.lower() == 'true'
        else:
            content.is_optional = is_optional

        # Type-specific fields
        content.content_type = data.get('content_type', content.content_type)
        if content.content_type in ['kana', 'kanji', 'vocabulary', 'grammar']:
            content.content_id = data.get('content_id', content.content_id)
        elif content.content_type == 'text':
            content.content_text = data.get('content_text', content.content_text)
        elif content.content_type in ['video', 'audio', 'image']:
            content.media_url = data.get('media_url', content.media_url)
            content.file_path = data.get('file_path', content.file_path)
            content.content_text = data.get('description', content.content_text)
        elif content.content_type == 'interactive':
            content.is_interactive = True
            interactive_type = data.get('interactive_type')

            # Use a query to get the question, which is more explicit for static analysis
            question = QuizQuestion.query.filter_by(lesson_content_id=content.id).first()
            if not question:
                question = QuizQuestion(lesson_content_id=content.id)
                db.session.add(question)

            if interactive_type:
                question.question_type = interactive_type
            question.question_text = data.get('question_text', question.question_text)
            question.explanation = data.get('explanation', question.explanation)

            # Use a bulk delete for efficiency and to resolve Pylance errors
            QuizOption.query.filter_by(question_id=question.id).delete()

            if question.question_type == 'multiple_choice':
                options_data = data.get('options', [])
                for i, option_data in enumerate(options_data):
                    new_option = QuizOption(
                        question_id=question.id,
                        option_text=option_data['text'],
                        is_correct=option_data.get('is_correct', False),
                        order_index=i,
                        feedback=option_data.get('feedback', '')
                    )
                    db.session.add(new_option)
            
            elif question.question_type == 'fill_blank':
                question.explanation = data.get('correct_answers', question.explanation)

            elif question.question_type == 'true_false':
                correct_answer = data.get('correct_answer')
                options_data = [
                    {'text': 'True', 'is_correct': correct_answer is True},
                    {'text': 'False', 'is_correct': correct_answer is False}
                ]
                for i, option_data in enumerate(options_data):
                    new_option = QuizOption(
                        question_id=question.id,
                        option_text=option_data['text'],
                        is_correct=option_data.get('is_correct', False),
                        order_index=i
                    )
                    db.session.add(new_option)

        db.session.commit()
        return jsonify(model_to_dict(content)), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": f"Database error occurred: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

@bp.route('/api/admin/lessons/<int:lesson_id>/content/bulk-update', methods=['PUT'])
@login_required
@admin_required
def bulk_update_content(lesson_id):
    """Bulk update content properties"""
    lesson = Lesson.query.get_or_404(lesson_id)
    data = request.json
    
    if not data or 'content_ids' not in data or 'updates' not in data:
        return jsonify({"error": "Missing required data"}), 400
    
    try:
        content_items = LessonContent.query.filter(
            LessonContent.lesson_id == lesson_id,
            LessonContent.id.in_(data['content_ids'])
        ).all()
        
        for content in content_items:
            for key, value in data['updates'].items():
                if hasattr(content, key):
                    setattr(content, key, value)
        
        db.session.commit()
        return jsonify({"message": f"Updated {len(content_items)} content items"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update content"}), 500

@bp.route('/api/admin/lessons/<int:lesson_id>/content/bulk-duplicate', methods=['POST'])
@login_required
@admin_required
def bulk_duplicate_content(lesson_id):
    """Bulk duplicate content items"""
    lesson = Lesson.query.get_or_404(lesson_id)
    data = request.json
    
    if not data or 'content_ids' not in data:
        return jsonify({"error": "Missing content IDs"}), 400
    
    try:
        duplicated_count = 0
        
        for content_id in data['content_ids']:
            original = LessonContent.query.filter_by(
                lesson_id=lesson_id, 
                id=content_id
            ).first()
            
            if original:
                # Create duplicate
                duplicate = LessonContent(
                    lesson_id=lesson_id,
                    content_type=original.content_type,
                    content_id=original.content_id,
                    title=f"{original.title} (Copy)" if original.title else None,
                    content_text=original.content_text,
                    media_url=original.media_url,
                    file_path=original.file_path,
                    order_index=original.order_index + 1000,  # Place at end
                    is_optional=original.is_optional,
                    is_interactive=original.is_interactive,
                    max_attempts=original.max_attempts,
                    passing_score=original.passing_score
                )
                
                db.session.add(duplicate)
                db.session.flush()  # Get the new ID
                
                # Duplicate quiz questions if interactive
                if original.is_interactive:
                    for question in original.quiz_questions:
                        new_question = QuizQuestion(
                            lesson_content_id=duplicate.id,
                            question_type=question.question_type,
                            question_text=question.question_text,
                            explanation=question.explanation,
                            points=question.points,
                            order_index=question.order_index
                        )
                        db.session.add(new_question)
                        db.session.flush()
                        
                        # Duplicate options
                        for option in question.options:
                            new_option = QuizOption(
                                question_id=new_question.id,
                                option_text=option.option_text,
                                is_correct=option.is_correct,
                                order_index=option.order_index,
                                feedback=option.feedback
                            )
                            db.session.add(new_option)
                
                duplicated_count += 1
        
        db.session.commit()
        return jsonify({"message": f"Duplicated {duplicated_count} content items"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to duplicate content"}), 500

@bp.route('/api/admin/lessons/<int:lesson_id>/content/bulk-delete', methods=['DELETE'])
@login_required
@admin_required
def bulk_delete_content(lesson_id):
    """Bulk delete content items"""
    lesson = Lesson.query.get_or_404(lesson_id)
    data = request.json
    
    if not data or 'content_ids' not in data:
        return jsonify({"error": "Missing content IDs"}), 400
    
    try:
        content_items = LessonContent.query.filter(
            LessonContent.lesson_id == lesson_id,
            LessonContent.id.in_(data['content_ids'])
        ).all()
        
        deleted_count = len(content_items)
        
        # Group content by page for reordering
        pages_to_reorder = set()
        
        for content in content_items:
            pages_to_reorder.add(content.page_number)
            # Delete associated files if any
            if hasattr(content, 'delete_file'):
                content.delete_file()
            db.session.delete(content)
        
        db.session.commit()
        
        # Reorder content on affected pages
        for page_number in pages_to_reorder:
            reorder_page_content(lesson_id, page_number)
        
        return jsonify({"message": f"Deleted {deleted_count} content items"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to delete content"}), 500

@bp.route('/api/admin/lessons/<int:lesson_id>/content/force-reorder', methods=['POST'])
@login_required
@admin_required
def force_reorder_lesson_content(lesson_id):
    """Force reorder all content in a lesson to fix gaps in order indices"""
    lesson = Lesson.query.get_or_404(lesson_id)
    
    try:
        force_reorder_all_lesson_content(lesson_id)
        return jsonify({"message": "All content reordered successfully"}), 200
        
    except Exception as e:
        current_app.logger.error(f"Error force reordering lesson {lesson_id}: {e}")
        return jsonify({"error": "Failed to reorder content"}), 500

@bp.route('/api/admin/content/<int:content_id>/duplicate', methods=['POST'])
@login_required
@admin_required
def duplicate_single_content(content_id):
    """Duplicate a single content item"""
    original = LessonContent.query.get_or_404(content_id)
    
    try:
        # Create duplicate (same logic as bulk duplicate)
        duplicate = LessonContent(
            lesson_id=original.lesson_id,
            content_type=original.content_type,
            content_id=original.content_id,
            title=f"{original.title} (Copy)" if original.title else None,
            content_text=original.content_text,
            media_url=original.media_url,
            file_path=original.file_path,
            order_index=original.order_index + 1,
            is_optional=original.is_optional,
            is_interactive=original.is_interactive,
            max_attempts=original.max_attempts,
            passing_score=original.passing_score
        )
        
        db.session.add(duplicate)
        db.session.flush()
        
        # Duplicate quiz questions if interactive
        if original.is_interactive:
            for question in original.quiz_questions:
                new_question = QuizQuestion(
                    lesson_content_id=duplicate.id,
                    question_type=question.question_type,
                    question_text=question.question_text,
                    explanation=question.explanation,
                    points=question.points,
                    order_index=question.order_index
                )
                db.session.add(new_question)
                db.session.flush()
                
                for option in question.options:
                    new_option = QuizOption(
                        question_id=new_question.id,
                        option_text=option.option_text,
                        is_correct=option.is_correct,
                        order_index=option.order_index,
                        feedback=option.feedback
                    )
                    db.session.add(new_option)
        
        db.session.commit()
        return jsonify(model_to_dict(duplicate)), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to duplicate content"}), 500

# Add new route for deleting a page
@bp.route('/api/admin/lessons/<int:lesson_id>/pages/<int:page_num>/delete', methods=['DELETE'])
@login_required
@admin_required
def delete_lesson_page(lesson_id, page_num):
    """Deletes a page, its metadata, and all its content items from a lesson."""
    # Also delete the page metadata
    page_metadata = LessonPage.query.filter_by(lesson_id=lesson_id, page_number=page_num).first()
    if page_metadata:
        db.session.delete(page_metadata)

    content_to_delete = LessonContent.query.filter_by(lesson_id=lesson_id, page_number=page_num).all()
    
    if not content_to_delete and not page_metadata:
        return jsonify({"error": "Page not found"}), 404
    
    try:
        for content in content_to_delete:
            if content.file_path:
                content.delete_file()
            db.session.delete(content)
        
        db.session.commit()
        return jsonify({"message": f"Page {page_num} and its content deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting page {page_num} from lesson {lesson_id}: {e}")
        return jsonify({"error": "Failed to delete page"}), 500

@bp.route('/api/admin/lessons/<int:lesson_id>/pages/<int:page_num>', methods=['PUT'])
@login_required
@admin_required
def update_lesson_page(lesson_id, page_num):
    """Update page title and description."""
    data = request.json
    current_app.logger.info(f"Updating page {page_num} for lesson {lesson_id} with data: {data}")
    
    page = LessonPage.query.filter_by(lesson_id=lesson_id, page_number=page_num).first()
    
    if not page:
        current_app.logger.error(f"Page {page_num} not found for lesson {lesson_id}")
        # If page doesn't exist, create it
        page = LessonPage(
            lesson_id=lesson_id,
            page_number=page_num,
            title=data.get('title', f'Page {page_num}'),
            description=data.get('description', ''),
            page_type=data.get('page_type', 'normal')
        )
        db.session.add(page)
        current_app.logger.info(f"Created new page {page_num} for lesson {lesson_id}")
    else:
        if data:
            page.title = data.get('title', page.title)
            page.description = data.get('description', page.description)
            if 'page_type' in data:
                page.page_type = data['page_type']
            current_app.logger.info(f"Updating existing page {page_num} for lesson {lesson_id}")

    try:
        db.session.commit()
        current_app.logger.info(f"Successfully committed changes for page {page_num}")
        return jsonify(model_to_dict(page)), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error occurred while updating page {page_num}: {str(e)}", exc_info=True)
        return jsonify({"error": f"Database error occurred: {str(e)}"}), 500
    except Exception as e:
        current_app.logger.error(f"An unexpected error occurred: {str(e)}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred"}), 500

# == USER LESSON API ==
@bp.route('/api/lessons', methods=['GET'])
def get_user_lessons():
    """Get lessons accessible to the current user or guest, with optional filtering."""
    instruction_language = request.args.get('instruction_language')
    visible_langs = current_app.config.get('CONTENT_LANGUAGES', ['german'])

    query = Lesson.query.filter_by(is_published=True)

    if instruction_language and instruction_language.lower() != 'all':
        # Explizite Sprachwahl muss in den global sichtbaren Sprachen liegen
        if instruction_language not in visible_langs:
            return jsonify({"lessons": []})
        query = query.filter(Lesson.instruction_language == instruction_language)
    else:
        # Default: nur global sichtbare Sprachen (Mayuko-Direktive: erst DE komplett)
        query = query.filter(Lesson.instruction_language.in_(visible_langs))

    lessons = query.order_by(Lesson.order_index.asc(), Lesson.id.asc()).all()
    
    accessible_lessons = []
    user = current_user if current_user.is_authenticated else None
    
    for lesson in lessons:
        accessible, message = lesson.is_accessible_to_user(user)
        lesson_dict = model_to_dict(lesson)
        lesson_dict['thumbnail_url'] = lesson.get_thumbnail_url()
        lesson_dict['accessible'] = accessible
        lesson_dict['access_message'] = message
        lesson_dict['category_name'] = lesson.category.name if lesson.category else None
        
        # Add background image information
        lesson_dict['background_image_url'] = lesson.get_background_url()
        # Clear the path so frontend doesn't try to use it with hardcoded /static/uploads/
        lesson_dict['background_image_path'] = None
        
        # Get user progress if exists (only for authenticated users)
        progress = None
        if current_user.is_authenticated:
            progress = UserLessonProgress.query.filter_by(
                user_id=current_user.id, lesson_id=lesson.id
            ).first()
        lesson_dict['progress'] = model_to_dict(progress) if progress else None
        
        accessible_lessons.append(lesson_dict)
    
    return jsonify(accessible_lessons)

@bp.route('/api/courses', methods=['GET'])
def get_courses():
    """Get all courses"""
    try:
        courses = Course.query.filter_by(is_published=True).all()
        courses_data = []
        for course in courses:
            course_dict = model_to_dict(course)
            course_dict['lessons'] = [{'id': l.id, 'title': l.title} for l in course.lessons]
            if current_user.is_authenticated:
                course_dict['is_purchased'] = CoursePurchase.query.filter_by(user_id=current_user.id, course_id=course.id).first() is not None
            else:
                course_dict['is_purchased'] = False
            courses_data.append(course_dict)
        return jsonify(courses_data)
    except Exception as e:
        current_app.logger.error(f"Error fetching courses: {e}")
        return jsonify([]), 200

@bp.route('/api/categories', methods=['GET'])
def get_public_categories():
    """Get categories for public use (no admin required)"""
    try:
        categories = LessonCategory.query.all()
        return jsonify([model_to_dict(category) for category in categories])
    except Exception as e:
        current_app.logger.error(f"Error fetching public categories: {e}")
        return jsonify([]), 200  # Return empty array on error

@bp.route('/api/lessons/<int:lesson_id>/reset', methods=['POST'])
@login_required
def reset_lesson_progress_api(lesson_id):
    """Reset user progress for a lesson via API"""
    lesson = Lesson.query.get_or_404(lesson_id)
    
    # Check access
    accessible, message = lesson.is_accessible_to_user(current_user)
    if not accessible:
        return jsonify({"error": message}), 403
    
    try:
        from sqlalchemy import text

        current_app.logger.info(f"API reset starting for user {current_user.id}, lesson {lesson_id}")

        # Delete all quiz answers for this user + lesson in one query
        delete_answers_sql = text("""
            DELETE FROM user_quiz_answer
            WHERE user_id = :user_id
              AND question_id IN (
                  SELECT qq.id FROM quiz_question qq
                  JOIN lesson_content lc ON qq.lesson_content_id = lc.id
                  WHERE lc.lesson_id = :lesson_id
              )
        """)
        result = db.session.execute(delete_answers_sql, {
            'user_id': current_user.id,
            'lesson_id': lesson_id
        })
        current_app.logger.info(f"Deleted {result.rowcount} quiz answers")

        # Reset progress
        reset_progress_sql = text("""
            UPDATE user_lesson_progress
            SET completed_at = NULL,
                is_completed = false,
                progress_percentage = 0,
                time_spent = 0,
                content_progress = '{}'
            WHERE user_id = :user_id AND lesson_id = :lesson_id
        """)
        result = db.session.execute(reset_progress_sql, {
            'user_id': current_user.id,
            'lesson_id': lesson_id
        })
        current_app.logger.info(f"Updated {result.rowcount} progress records")

        db.session.commit()
        current_app.logger.info(f"Successfully reset progress for user {current_user.id}, lesson {lesson_id}")

        progress = UserLessonProgress.query.filter_by(
            user_id=current_user.id, lesson_id=lesson_id
        ).first()
        return jsonify({
            "success": True,
            "message": "Progress reset successfully",
            "progress": model_to_dict(progress) if progress else None
        })

    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"SQLAlchemy error resetting lesson progress for user {current_user.id}, lesson {lesson_id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to reset progress. Please try again."}), 500
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Unexpected error resetting lesson progress for user {current_user.id}, lesson {lesson_id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to reset progress. Please try again."}), 500

def _get_or_create_lesson_progress(user_id, lesson_id):
    """Liefert den UserLessonProgress-Datensatz fuer (user, lesson) — race-sicher.

    Verwendet INSERT ... ON CONFLICT DO NOTHING, damit zwei gleichzeitige Requests
    (z.B. zwei Progress-Posts beim schnellen Durchklicken) nicht an der
    UNIQUE(user_id, lesson_id)-Constraint scheitern. Gibt das frisch geladene
    ORM-Objekt zurueck (oder None, falls es trotz Insert nicht gefunden wird).
    """
    progress = UserLessonProgress.query.filter_by(
        user_id=user_id, lesson_id=lesson_id
    ).first()
    if progress:
        return progress

    from sqlalchemy import text
    insert_sql = text("""
        INSERT INTO user_lesson_progress (user_id, lesson_id, started_at, last_accessed, progress_percentage, time_spent, content_progress, is_completed)
        VALUES (:user_id, :lesson_id, :now, :now, 0, 0, '{}', false)
        ON CONFLICT (user_id, lesson_id) DO NOTHING
    """)
    db.session.execute(insert_sql, {
        'user_id': user_id,
        'lesson_id': lesson_id,
        'now': datetime.utcnow(),
    })
    db.session.commit()
    return UserLessonProgress.query.filter_by(
        user_id=user_id, lesson_id=lesson_id
    ).first()


@bp.route('/api/lessons/<int:lesson_id>/progress', methods=['POST'])
@login_required
def update_lesson_progress(lesson_id):
    """Update user progress for a lesson"""
    # Validate CSRF token from header (for JSON requests) or form data (for sendBeacon)
    from flask_wtf.csrf import validate_csrf
    try:
        csrf_token = request.headers.get('X-CSRFToken') or request.form.get('csrf_token')
        if not csrf_token:
            return jsonify({"error": "CSRF token missing"}), 400
        validate_csrf(csrf_token)
    except Exception as e:
        return jsonify({"error": "CSRF token invalid"}), 400
    
    lesson = Lesson.query.get_or_404(lesson_id)
    
    # Check access
    accessible, message = lesson.is_accessible_to_user(current_user)
    if not accessible:
        return jsonify({"error": message}), 403
    
    # Handle both JSON and form data
    if request.is_json:
        data = request.json
    else:
        # Convert form data to dict for consistent handling
        data = request.form.to_dict()
        # Convert string numbers to integers where appropriate
        if 'content_id' in data:
            try:
                data['content_id'] = int(data['content_id'])
            except (ValueError, TypeError):
                pass
        if 'time_spent' in data:
            try:
                data['time_spent'] = int(data['time_spent'])
            except (ValueError, TypeError):
                pass
    
    try:
        progress = _get_or_create_lesson_progress(current_user.id, lesson_id)
        if not progress:
            return jsonify({"error": "Failed to create or find progress record"}), 500

        # Fortschritt aktualisieren ueber die Modell-Logik (Single Source of Truth).
        # WICHTIG: Frueher rechnete diese Route den Prozentsatz mit eigenem Raw-SQL
        # gegen ALLE LessonContent-Zeilen (inkl. is_optional / Audio auf
        # Slideshow-Pages). Seit dem Lektionsbilder-Rollout hat jede Lektion viele
        # is_optional-Bilder -> der Nenner war zu gross, keine Lektion erreichte je
        # 100%, is_completed wurde nie gesetzt und nichts wurde als "fertig" angezeigt.
        # mark_content_completed()/update_progress_percentage() zaehlen dagegen nur
        # progress_visible_content_items (optionale + Slideshow-Audio ausgeschlossen)
        # und sind unit-getestet -> hier delegieren statt die Logik zu duplizieren.
        additional_time = (data.get('time_spent', 0) if data else 0) or 0
        if data and 'content_id' in data:
            progress.mark_content_completed(data['content_id'])
            progress.time_spent = (progress.time_spent or 0) + additional_time
        elif additional_time:
            progress.time_spent = (progress.time_spent or 0) + additional_time
        progress.last_accessed = datetime.utcnow()

        # Streak bei Lernaktivitaet aktualisieren
        current_user.update_streak()

        db.session.commit()

        result = model_to_dict(progress)
        result['streak'] = current_user.current_streak or 0
        result['total_xp'] = current_user.total_xp or 0
        return jsonify(result)

    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating lesson progress for user {current_user.id}, lesson {lesson_id}: {e}")
        return jsonify({"error": "Failed to update progress"}), 500

@bp.route('/api/lessons/<int:lesson_id>/complete-remaining', methods=['POST'])
@login_required
def complete_remaining_passive(lesson_id):
    """Markiert am Lektions-Ende alle sichtbaren passiven Items als erledigt.

    Robustes Sicherheitsnetz, damit "Lektion durchgearbeitet" zuverlaessig zu
    is_completed=True fuehrt — unabhaengig davon, welche Content-Typen die Lektion
    enthaelt. Deckt insbesondere Typen ab, die im Frontend keinen eigenen
    "Als erledigt"-Button haben und sich darum bisher nie selbst meldeten
    (dialog_slideshow, standalone audio, isolierte Einzel-Flipcards) und macht den
    Abschluss zukunftssicher gegenueber neuen passiven Content-Typen.

    Interaktive Items (Quiz, kana_grid_game) bleiben ausgenommen und muessen weiter
    aktiv geloest werden (siehe UserLessonProgress.mark_passive_items_completed).
    """
    from flask_wtf.csrf import validate_csrf
    try:
        csrf_token = request.headers.get('X-CSRFToken') or request.form.get('csrf_token')
        if not csrf_token:
            return jsonify({"error": "CSRF token missing"}), 400
        validate_csrf(csrf_token)
    except Exception:
        return jsonify({"error": "CSRF token invalid"}), 400

    lesson = Lesson.query.get_or_404(lesson_id)

    accessible, message = lesson.is_accessible_to_user(current_user)
    if not accessible:
        return jsonify({"error": message}), 403

    try:
        progress = _get_or_create_lesson_progress(current_user.id, lesson_id)
        if not progress:
            return jsonify({"error": "Failed to create or find progress record"}), 500

        progress.mark_passive_items_completed()
        progress.last_accessed = datetime.utcnow()
        current_user.update_streak()
        db.session.commit()

        result = model_to_dict(progress)
        result['streak'] = current_user.current_streak or 0
        result['total_xp'] = current_user.total_xp or 0
        return jsonify(result)

    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error completing passive items for user {current_user.id}, lesson {lesson_id}: {e}")
        return jsonify({"error": "Failed to update progress"}), 500

@bp.route('/lessons/<int:lesson_id>/reset', methods=['POST'])
@login_required
def reset_lesson_progress(lesson_id):
    """Reset user progress for a specific lesson."""
    form = CSRFTokenForm()
    if form.validate_on_submit():
        try:
            from sqlalchemy import text

            # Delete all quiz answers for this user + lesson in one query
            delete_answers_sql = text("""
                DELETE FROM user_quiz_answer
                WHERE user_id = :user_id
                  AND question_id IN (
                      SELECT qq.id FROM quiz_question qq
                      JOIN lesson_content lc ON qq.lesson_content_id = lc.id
                      WHERE lc.lesson_id = :lesson_id
                  )
            """)
            result = db.session.execute(delete_answers_sql, {
                'user_id': current_user.id,
                'lesson_id': lesson_id
            })
            current_app.logger.info(f"Deleted {result.rowcount} quiz answers for user {current_user.id}, lesson {lesson_id}")

            # Reset progress
            reset_progress_sql = text("""
                UPDATE user_lesson_progress
                SET completed_at = NULL,
                    is_completed = false,
                    progress_percentage = 0,
                    time_spent = 0,
                    content_progress = '{}'
                WHERE user_id = :user_id AND lesson_id = :lesson_id
            """)
            result = db.session.execute(reset_progress_sql, {
                'user_id': current_user.id,
                'lesson_id': lesson_id
            })
            current_app.logger.info(f"Reset progress for user {current_user.id}, lesson {lesson_id} ({result.rowcount} rows)")

            db.session.commit()
            flash('Fortschritt wurde zurückgesetzt.', 'success')

        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error resetting progress for user {current_user.id}, lesson {lesson_id}: {e}", exc_info=True)
            flash('Fehler beim Zurücksetzen. Bitte erneut versuchen.', 'danger')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error resetting progress: {e}", exc_info=True)
            flash('Fehler beim Zurücksetzen. Bitte erneut versuchen.', 'danger')
    else:
        current_app.logger.error(f"CSRF validation failed for reset request from user {current_user.id}, lesson {lesson_id}")
        flash('Ungültige Anfrage.', 'danger')

    return redirect(url_for('routes.view_lesson', lesson_id=lesson_id))

# == LESSON PRICING AND PURCHASE API ==
@bp.route('/api/courses/<int:course_id>/purchase', methods=['POST'])
@login_required
def purchase_course(course_id):
    """
    Initiate course purchase with PostFinance Checkout
    
    Flow:
    1. Validate course and user eligibility
    2. Create PostFinance transaction
    3. Store transaction in database
    4. Return payment URL for redirect
    """
    from app.services.payment_factory import get_payment_service
    from app.services.transaction_service import PaymentTransactionService
    
    # Validate CSRF token
    from flask_wtf.csrf import validate_csrf
    try:
        csrf_token = request.headers.get('X-CSRFToken')
        if not csrf_token:
            return jsonify({"error": "CSRF token missing"}), 400
        validate_csrf(csrf_token)
    except Exception:
        return jsonify({"error": "CSRF token invalid"}), 400
    
    course = Course.query.get_or_404(course_id)
    
    # Validate course is purchasable
    if not course.is_purchasable or course.price <= 0:
        return jsonify({"error": "This course is not available for purchase"}), 400
    
    # Check if user already owns this course
    existing_purchase = CoursePurchase.query.filter_by(
        user_id=current_user.id, 
        course_id=course_id
    ).first()
    
    if existing_purchase:
        return jsonify({"error": "You already own this course"}), 400
    
    try:
        # Initialize services
        payment_service = get_payment_service()
        transaction_service = PaymentTransactionService()
        
        # Create PostFinance transaction
        result = payment_service.create_course_transaction(current_user, course)
        
        if not result['success']:
            return jsonify({
                "error": result['error'],
                "error_type": result.get('error_type')
            }), 400
        
        transaction_id = result['transaction_id']
        
        # Store transaction in database
        payment_transaction = transaction_service.create_payment_transaction(
            transaction_id=transaction_id,
            user=current_user,
            item_type='course',
            item_id=course_id,
            amount=course.price
        )
        
        # Generate payment URL
        url_result = payment_service.generate_payment_page_url(transaction_id)
        
        if not url_result['success']:
            return jsonify({
                "error": "Failed to generate payment URL",
                "error_details": url_result['error']
            }), 500
        
        current_app.logger.info(f"Course purchase initiated: User {current_user.id}, Course {course_id}, Transaction {transaction_id}")
        
        return jsonify({
            "success": True,
            "transaction_id": transaction_id,
            "payment_url": url_result['payment_url'],
            "course_title": course.title,
            "amount": course.price,
            "currency": "CHF"
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Error initiating course purchase: {e}")
        return jsonify({"error": "Purchase initiation failed"}), 500

@bp.route('/api/lessons/<int:lesson_id>/purchase', methods=['POST'])
@login_required
def purchase_lesson(lesson_id):
    """
    Initiate lesson purchase with PostFinance Checkout
    
    Flow:
    1. Validate lesson and user eligibility
    2. Create PostFinance transaction
    3. Store transaction in database
    4. Return payment URL for redirect
    """
    from app.services.payment_factory import get_payment_service
    from app.services.transaction_service import PaymentTransactionService
    
    # Validate CSRF token
    from flask_wtf.csrf import validate_csrf
    try:
        csrf_token = request.headers.get('X-CSRFToken')
        if not csrf_token:
            return jsonify({"error": "CSRF token missing"}), 400
        validate_csrf(csrf_token)
    except Exception:
        return jsonify({"error": "CSRF token invalid"}), 400
    
    lesson = Lesson.query.get_or_404(lesson_id)
    
    # Validate lesson is purchasable
    if not lesson.is_purchasable or lesson.price <= 0:
        return jsonify({"error": "This lesson is not available for purchase"}), 400
    
    # Check if user already owns this lesson
    existing_purchase = LessonPurchase.query.filter_by(
        user_id=current_user.id, 
        lesson_id=lesson_id
    ).first()
    
    if existing_purchase:
        return jsonify({"error": "You already own this lesson"}), 400
    
    try:
        # Initialize services
        payment_service = get_payment_service()
        transaction_service = PaymentTransactionService()
        
        # Create PostFinance transaction
        result = payment_service.create_lesson_transaction(current_user, lesson)
        
        if not result['success']:
            return jsonify({
                "error": result['error'],
                "error_type": result.get('error_type')
            }), 400
        
        transaction_id = result['transaction_id']
        
        # Store transaction in database
        payment_transaction = transaction_service.create_payment_transaction(
            transaction_id=transaction_id,
            user=current_user,
            item_type='lesson',
            item_id=lesson_id,
            amount=lesson.price
        )
        
        # Generate payment URL
        url_result = payment_service.generate_payment_page_url(transaction_id)
        
        if not url_result['success']:
            return jsonify({
                "error": "Failed to generate payment URL",
                "error_details": url_result['error']
            }), 500
        
        current_app.logger.info(f"Lesson purchase initiated: User {current_user.id}, Lesson {lesson_id}, Transaction {transaction_id}")
        
        return jsonify({
            "success": True,
            "transaction_id": transaction_id,
            "payment_url": url_result['payment_url'],
            "lesson_title": lesson.title,
            "amount": lesson.price,
            "currency": "CHF"
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Error initiating lesson purchase: {e}")
        return jsonify({"error": "Purchase initiation failed"}), 500

@bp.route('/api/payment/status/<int:transaction_id>', methods=['GET'])
@login_required
def get_payment_status(transaction_id):
    """
    Check payment status for a transaction
    
    Returns current transaction state and details
    """
    from app.services.payment_factory import get_payment_service
    from app.services.transaction_service import PaymentTransactionService
    from app.models import PaymentTransaction
    
    # Verify user owns this transaction
    payment_transaction = PaymentTransaction.query.filter_by(
        transaction_id=transaction_id,
        user_id=current_user.id
    ).first_or_404()
    
    try:
        payment_service = get_payment_service()
        result = payment_service.get_transaction_status(transaction_id)
        
        if result['success']:
            # Update local state if different
            if result['state'] != payment_transaction.state:
                transaction_service = PaymentTransactionService()
                transaction_service.update_transaction_state(
                    transaction_id, 
                    result['state']
                )
            
            return jsonify({
                "success": True,
                "transaction_id": transaction_id,
                "state": result['state'],
                "item_type": payment_transaction.item_type,
                "item_id": payment_transaction.item_id,
                "amount": payment_transaction.amount
            })
        else:
            return jsonify({
                "error": result['error']
            }), 400
            
    except Exception as e:
        current_app.logger.error(f"Error checking payment status: {e}")
        return jsonify({"error": "Status check failed"}), 500

@bp.route('/api/payment/cancel/<int:transaction_id>', methods=['POST'])
@login_required
def cancel_payment(transaction_id):
    """
    Cancel a pending payment transaction
    
    Note: This is for user-initiated cancellation
    PostFinance handles timeout cancellation automatically
    """
    from app.services.transaction_service import PaymentTransactionService
    from app.models import PaymentTransaction
    
    # Validate CSRF token
    from flask_wtf.csrf import validate_csrf
    try:
        csrf_token = request.headers.get('X-CSRFToken')
        if not csrf_token:
            return jsonify({"error": "CSRF token missing"}), 400
        validate_csrf(csrf_token)
    except Exception:
        return jsonify({"error": "CSRF token invalid"}), 400
    
    # Verify user owns this transaction
    payment_transaction = PaymentTransaction.query.filter_by(
        transaction_id=transaction_id,
        user_id=current_user.id,
        state='PENDING'
    ).first_or_404()
    
    try:
        transaction_service = PaymentTransactionService()
        success = transaction_service.update_transaction_state(
            transaction_id, 
            'CANCELLED'
        )
        
        if success:
            return jsonify({
                "success": True,
                "message": "Payment cancelled successfully"
            })
        else:
            return jsonify({"error": "Failed to cancel payment"}), 500
            
    except Exception as e:
        current_app.logger.error(f"Error cancelling payment: {e}")
        return jsonify({"error": "Cancellation failed"}), 500

@bp.route('/payment/success')
def payment_success():
    """Handle successful payment redirect"""
    return render_template('payment_success.html')

@bp.route('/payment/failed')
def payment_failed():
    """Handle failed payment redirect"""
    return render_template('payment_failed.html')

@bp.route('/api/payment/webhook/payrexx', methods=['POST'])
@csrf.exempt
def payrexx_webhook():
    """
    Payrexx Webhook-Endpoint für Transaktions-Updates.
    Empfängt POST-Requests von Payrexx bei Statusänderungen.
    Muss innerhalb von 20 Sekunden antworten.
    """
    from app.services.transaction_service import PaymentTransactionService
    from app.models import PaymentTransaction

    # Signatur prüfen
    signature = request.headers.get('X-Webhook-Signature', '')
    payload = request.get_data()

    payrexx_webhook_secret = current_app.config.get('PAYREXX_WEBHOOK_SECRET') or os.environ.get('PAYREXX_WEBHOOK_SECRET')
    if payrexx_webhook_secret:
        import hmac as hmac_mod
        import hashlib
        computed = hmac_mod.new(
            payrexx_webhook_secret.encode('utf-8'),
            payload,
            hashlib.sha256,
        ).hexdigest()
        if not hmac_mod.compare_digest(computed, signature):
            current_app.logger.warning("Payrexx Webhook: Ungültige Signatur")
            return jsonify({"error": "Invalid signature"}), 403

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "No payload"}), 400

    # Transaktionsdaten extrahieren
    transaction = data.get('transaction', {})
    txn_status = transaction.get('status', '')
    reference_id = transaction.get('referenceId', '')
    invoice = transaction.get('invoice', {}) or {}
    # Unsere payment_transaction.transaction_id == Payrexx Gateway-/PaymentRequest-ID.
    # transaction.id ist eine *Transaktions*-Instanz-ID, NICHT die Gateway-ID — daher zuletzt als Fallback.
    gateway_id = (
        invoice.get('paymentRequestId')
        or invoice.get('paymentLinkId')
        or transaction.get('paymentRequestId')
        or transaction.get('id')
    )

    current_app.logger.info(
        f"Payrexx Webhook: Gateway {gateway_id}, Status '{txn_status}', "
        f"Ref '{reference_id}', TxnId '{transaction.get('id')}'"
    )

    # Status mappen
    from app.services.payrexx_payment_service import PayrexxPaymentService
    internal_state = PayrexxPaymentService._map_status(txn_status)

    # PaymentTransaction in DB suchen und updaten
    if gateway_id:
        transaction_service = PaymentTransactionService()
        transaction_service.update_transaction_state(
            transaction_id=int(gateway_id),
            new_state=internal_state,
            webhook_data=data,
        )

    return jsonify({"status": "ok"}), 200

@bp.route('/api/user/purchases', methods=['GET'])
@login_required
def get_user_purchases():
    """Get all purchases for the current user"""
    purchases = LessonPurchase.query.filter_by(user_id=current_user.id).all()
    
    purchases_data = []
    for purchase in purchases:
        purchase_dict = model_to_dict(purchase)
        purchase_dict['lesson_title'] = purchase.lesson.title
        purchase_dict['lesson_description'] = purchase.lesson.description
        purchases_data.append(purchase_dict)
    
    return jsonify(purchases_data)

@bp.route('/api/lessons/<int:lesson_id>/purchase-status', methods=['GET'])
@login_required
def get_lesson_purchase_status(lesson_id):
    """Check if user has purchased a specific lesson"""
    lesson = Lesson.query.get_or_404(lesson_id)
    
    purchase = LessonPurchase.query.filter_by(
        user_id=current_user.id, 
        lesson_id=lesson_id
    ).first()
    
    return jsonify({
        "lesson_id": lesson_id,
        "is_purchased": purchase is not None,
        "purchase_date": purchase.purchased_at.isoformat() if purchase else None,
        "price_paid": purchase.price_paid if purchase else None,
        "current_price": lesson.price,
        "is_purchasable": lesson.is_purchasable
    })

# == ADMIN PURCHASE MANAGEMENT API ==
@bp.route('/api/admin/purchases', methods=['GET'])
@login_required
@admin_required
def list_all_purchases():
    """Get all purchases for admin review"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    purchases = LessonPurchase.query.order_by(LessonPurchase.purchased_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    purchases_data = []
    for purchase in purchases.items:
        purchase_dict = model_to_dict(purchase)
        purchase_dict['user_username'] = purchase.user.username
        purchase_dict['user_email'] = purchase.user.email
        purchase_dict['lesson_title'] = purchase.lesson.title
        purchases_data.append(purchase_dict)
    
    return jsonify({
        "purchases": purchases_data,
        "total": purchases.total,
        "pages": purchases.pages,
        "current_page": purchases.page,
        "per_page": purchases.per_page
    })

@bp.route('/api/admin/lessons/<int:lesson_id>/purchases', methods=['GET'])
@login_required
@admin_required
def get_lesson_purchases(lesson_id):
    """Get all purchases for a specific lesson"""
    lesson = Lesson.query.get_or_404(lesson_id)
    
    purchases = LessonPurchase.query.filter_by(lesson_id=lesson_id).order_by(
        LessonPurchase.purchased_at.desc()
    ).all()
    
    purchases_data = []
    for purchase in purchases:
        purchase_dict = model_to_dict(purchase)
        purchase_dict['user_username'] = purchase.user.username
        purchase_dict['user_email'] = purchase.user.email
        purchases_data.append(purchase_dict)
    
    return jsonify({
        "lesson_id": lesson_id,
        "lesson_title": lesson.title,
        "total_purchases": len(purchases),
        "total_revenue": sum(p.price_paid for p in purchases),
        "purchases": purchases_data
    })

@bp.route('/api/admin/revenue-stats', methods=['GET'])
@login_required
@admin_required
def get_revenue_stats():
    """Get revenue statistics for admin dashboard"""
    from sqlalchemy import func
    
    # Total revenue
    total_revenue = db.session.query(func.sum(LessonPurchase.price_paid)).scalar() or 0
    
    # Total purchases
    total_purchases = LessonPurchase.query.count()
    
    # Revenue by lesson
    lesson_revenue = db.session.query(
        Lesson.title,
        Lesson.id,
        func.count(LessonPurchase.id).label('purchase_count'),
        func.sum(LessonPurchase.price_paid).label('revenue')
    ).join(LessonPurchase).group_by(Lesson.id, Lesson.title).all()
    
    # Recent purchases (last 30 days)
    from datetime import timedelta
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_revenue = db.session.query(func.sum(LessonPurchase.price_paid)).filter(
        LessonPurchase.purchased_at >= thirty_days_ago
    ).scalar() or 0
    
    recent_purchases = LessonPurchase.query.filter(
        LessonPurchase.purchased_at >= thirty_days_ago
    ).count()
    
    return jsonify({
        "total_revenue": float(total_revenue),
        "total_purchases": total_purchases,
        "recent_revenue_30d": float(recent_revenue),
        "recent_purchases_30d": recent_purchases,
        "average_price": float(total_revenue / total_purchases) if total_purchases > 0 else 0,
        "lesson_revenue": [
            {
                "lesson_id": lesson_id,
                "lesson_title": title,
                "purchase_count": purchase_count,
                "revenue": float(revenue)
            }
            for title, lesson_id, purchase_count, revenue in lesson_revenue
        ]
    })

@bp.route('/api/admin/lessons/<int:lesson_id>/content/interactive', methods=['POST'])
@login_required
@admin_required
def add_interactive_content(lesson_id):
    """Add interactive content (quiz questions) to lesson"""
    lesson = Lesson.query.get_or_404(lesson_id)
    data = request.json
    
    if not data or not data.get('interactive_type'):
        return jsonify({"error": "Missing interactive type"}), 400
    
    # Create lesson content
    # Determine the next order index
    last_content = LessonContent.query.filter_by(lesson_id=lesson_id).order_by(LessonContent.order_index.desc()).first()
    next_order_index = (last_content.order_index + 1) if last_content else 0

    content = LessonContent(
        lesson_id=lesson_id,
        content_type='interactive',
        title=data.get('title'),
        is_interactive=True,
        max_attempts=data.get('max_attempts', 3),
        passing_score=data.get('passing_score', 70),
        order_index=next_order_index,
        page_number=data.get('page_number', 1)  # Add page number handling
    )
    
    db.session.add(content)
    db.session.flush()  # Get the content ID
    
    # Create quiz question
    question = QuizQuestion(
        lesson_content_id=content.id,
        question_type=data['interactive_type'],
        question_text=data.get('question_text'),
        explanation=data.get('explanation'),
        points=data.get('points', 1)
    )
    
    db.session.add(question)
    db.session.flush()  # Get the question ID
    
    # Add options for multiple choice and true/false
    if data['interactive_type'] in ['multiple_choice', 'true_false']:
        options_data = data.get('options', [])
        if data['interactive_type'] == 'true_false':
            options_data = [
                {'text': 'True', 'is_correct': data.get('correct_answer') is True},
                {'text': 'False', 'is_correct': data.get('correct_answer') is False}
            ]

        for i, option_data in enumerate(options_data):
            option = QuizOption(
                question_id=question.id,
                option_text=option_data['text'],
                is_correct=option_data.get('is_correct', False),
                order_index=i,
                feedback=option_data.get('feedback', '')
            )
            db.session.add(option)
    
    db.session.commit()
    return jsonify(model_to_dict(content)), 201

from sqlalchemy.orm import joinedload

@bp.route('/api/lessons/<int:lesson_id>/quiz/<int:question_id>/answer', methods=['POST'])
@login_required
def submit_quiz_answer(lesson_id, question_id):
    """Submit answer to quiz question"""
    # Validate CSRF token from header
    from flask_wtf.csrf import validate_csrf
    try:
        csrf_token = request.headers.get('X-CSRFToken')
        if not csrf_token:
            return jsonify({"error": "CSRF token missing"}), 400
        validate_csrf(csrf_token)
    except Exception as e:
        return jsonify({"error": "CSRF token invalid"}), 400
    
    try:
        lesson = Lesson.query.get_or_404(lesson_id)
        question = QuizQuestion.query.filter_by(id=question_id).first()

        if not question:
            return jsonify({"error": "Question not found"}), 404
        
        # Check if question belongs to lesson through its content
        if not question.content or question.content.lesson_id != lesson_id:
            return jsonify({"error": "Question not found in this lesson"}), 404
        
        # Check lesson access
        accessible, message = lesson.is_accessible_to_user(current_user)
        if not accessible:
            current_app.logger.warning(f"User {current_user.id} access denied for lesson {lesson_id}: {message}")
            return jsonify({"error": message}), 403
        
        data = request.json
        if not data:
            return jsonify({"error": "Invalid request. Must be JSON."}), 400
        current_app.logger.info(f"Received answer for question {question_id} from user {current_user.id}: {data}")
        
        # Find existing answer or create a new one
        answer = UserQuizAnswer.query.filter_by(
            user_id=current_user.id, question_id=question_id
        ).first()

        # If an answer exists, check attempts
        if answer:
            if not question.content:
                return jsonify({"error": "Associated content for this question not found."}), 500
            
            max_attempts = question.content.max_attempts or float('inf')

            if answer.attempts >= max_attempts:
                current_app.logger.warning(f"User {current_user.id} exceeded max attempts for question {question_id}")
                return jsonify({"error": "Maximum attempts exceeded"}), 400
            answer.attempts += 1
        else:
            # No existing answer, create a new one
            answer = UserQuizAnswer(
                user_id=current_user.id,
                question_id=question_id,
                attempts=1
            )
            db.session.add(answer)

        # Process answer based on question type
        is_correct = False
        selected_option = None

        if question.question_type == 'multiple_choice':
            selected_option_id = data.get('selected_option_id')
            current_app.logger.info(f"Selected option ID from request: {selected_option_id}")
            if not selected_option_id:
                return jsonify({"error": "selected_option_id is required"}), 400
            
            selected_option = QuizOption.query.get(int(selected_option_id))
            current_app.logger.info(f"Selected option from DB: {selected_option}")
            
            is_correct = selected_option and selected_option.is_correct
            current_app.logger.info(f"Is correct: {is_correct}")

            answer.selected_option_id = selected_option_id
            answer.is_correct = is_correct
            answer.text_answer = None
        
        elif question.question_type == 'fill_blank':
            text_answer = data.get('text_answer', '').strip()
            correct_answers = [ans.strip().lower() for ans in (question.explanation or "").split(',')]
            is_correct = text_answer.lower() in correct_answers
            
            answer.text_answer = text_answer
            answer.is_correct = is_correct
            answer.selected_option_id = None

        elif question.question_type == 'true_false':
            selected_option_id = data.get('selected_option_id')
            if not selected_option_id:
                return jsonify({"error": "selected_option_id is required"}), 400
            selected_option = QuizOption.query.get(int(selected_option_id))
            is_correct = selected_option and selected_option.is_correct

            answer.selected_option_id = selected_option_id
            answer.is_correct = is_correct
            answer.text_answer = None

        elif question.question_type == 'matching':
            submitted_pairs = data.get('pairs', [])
            if not submitted_pairs:
                return jsonify({"error": "No pairs submitted for matching question"}), 400

            # Build correct answers mapping from question options
            # option_text contains the prompt, feedback contains the correct answer
            correct_options = {opt.option_text: opt.feedback for opt in question.options}
            
            correct_matches = 0
            total_pairs = len(correct_options)
            
            # Check each submitted pair against correct answers
            for pair in submitted_pairs:
                prompt = pair.get('prompt')
                user_answer = pair.get('answer')
                correct_answer = correct_options.get(prompt)
                
                current_app.logger.info(f"Checking pair - Prompt: '{prompt}', User Answer: '{user_answer}', Correct Answer: '{correct_answer}'")
                
                if correct_answer and user_answer == correct_answer:
                    correct_matches += 1
            
            # All pairs must be correct for the answer to be marked as correct
            is_correct = correct_matches == total_pairs
            answer.is_correct = is_correct
            answer.text_answer = json.dumps(submitted_pairs)  # Store user's answer
            
            current_app.logger.info(f"Matching question result - Correct matches: {correct_matches}/{total_pairs}, Is correct: {is_correct}")

        else:
            return jsonify({"error": "Unsupported question type"}), 400

        answer.answered_at = db.func.now()

        # XP vergeben bei korrekter Antwort
        xp_earned = 0
        if is_correct:
            xp_earned = question.points or 10
            current_user.total_xp = (current_user.total_xp or 0) + xp_earned
            current_user.update_streak()

        db.session.commit()

        # Return result with feedback
        # Calculate remaining attempts safely
        attempts_remaining = 'Unlimited'
        if question.content and question.content.max_attempts:
            attempts_remaining = question.content.max_attempts - answer.attempts

        # Only reveal explanation and correct answer when:
        # - Answer is correct, OR
        # - No attempts remaining (last attempt used)
        show_solution = is_correct or attempts_remaining == 0

        result = {
            'is_correct': is_correct,
            'attempts_remaining': attempts_remaining,
            'xp_earned': xp_earned,
            'total_xp': current_user.total_xp or 0,
            'streak': current_user.current_streak or 0
        }

        # Always show why the selected option is wrong/right
        # Render Markdown to HTML so **bold**, *italic* etc. display correctly
        if selected_option and selected_option.feedback:
            result['option_feedback'] = render_template_string(
                '{{ text | markdown_inline }}', text=selected_option.feedback
            )

        # Only reveal the full explanation (correct answer) when solved
        if show_solution:
            result['explanation'] = render_template_string(
                '{{ text | markdown_safe }}', text=question.explanation
            )
        
        current_app.logger.info(f"Answer for question {question_id} processed. Result: {result}")
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Error submitting quiz answer for question {question_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500

# == AI CONTENT GENERATION API ==
@bp.route('/api/admin/generate-ai-content', methods=['POST'])
@login_required
@admin_required
def generate_ai_content():
    """
    Handles requests for AI-generated lesson content.
    This is a proxy to the AILessonContentGenerator service.
    """
    data = request.json
    if not data or 'content_type' not in data:
        return jsonify({"error": "Missing 'content_type' in request"}), 400

    generator = AILessonContentGenerator()
    content_type = data.get('content_type')
    topic = data.get('topic', 'General Japanese')
    difficulty = data.get('difficulty', 'Beginner')
    keywords = data.get('keywords', 'N/A')

    result = None
    if content_type == "explanation":
        result = generator.generate_explanation(topic, difficulty, keywords)
    elif content_type == "formatted_explanation":
        result = generator.generate_formatted_explanation(topic, difficulty, keywords)
    elif content_type == "multiple_choice_question":
        result = generator.generate_multiple_choice_question(topic, difficulty, keywords)
    elif content_type == "true_false_question":
        result = generator.generate_true_false_question(topic, difficulty, keywords)
    elif content_type == "fill_blank_question":
        result = generator.generate_fill_in_the_blank_question(topic, difficulty, keywords)
    elif content_type == "matching_question":
        result = generator.generate_matching_question(topic, difficulty, keywords)
    else:
        return jsonify({"error": "Unsupported content type"}), 400

    if "error" in result:
        return jsonify(result), 500

    return jsonify(result)

@bp.route('/api/admin/generate-ai-image', methods=['POST'])
@login_required
@admin_required
def generate_ai_image():
    """Generate AI images for lesson content using DALL-E."""
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    generator = AILessonContentGenerator()
    
    # Handle different types of image generation requests
    if 'prompt' in data:
        # Direct prompt generation
        result = generator.generate_single_image(
            prompt=data['prompt'],
            size=data.get('size', '1024x1024'),
            quality=data.get('quality', 'standard')
        )
    elif 'content_text' in data:
        # Generate prompt from content, then generate image
        lesson_topic = data.get('lesson_topic', 'Japanese Language Learning')
        difficulty = data.get('difficulty', 'Beginner')
        
        # First generate optimized prompt
        prompt_result = generator.generate_image_prompt(
            data['content_text'], lesson_topic, difficulty
        )
        
        if 'error' in prompt_result:
            return jsonify(prompt_result), 500
        
        # Then generate image
        result = generator.generate_single_image(
            prompt=prompt_result['image_prompt'],
            size=data.get('size', '1024x1024'),
            quality=data.get('quality', 'standard')
        )
        result['generated_prompt'] = prompt_result['image_prompt']
    else:
        return jsonify({"error": "Either 'prompt' or 'content_text' must be provided"}), 400

    if "error" in result:
        return jsonify(result), 500

    return jsonify(result)

@bp.route('/api/admin/analyze-multimedia-needs', methods=['POST'])
@login_required
@admin_required
def analyze_multimedia_needs():
    """Analyze lesson content and suggest multimedia enhancements."""
    data = request.json
    if not data or 'content_text' not in data:
        return jsonify({"error": "Missing 'content_text' in request"}), 400

    generator = AILessonContentGenerator()
    lesson_topic = data.get('lesson_topic', 'Japanese Language Learning')
    
    result = generator.analyze_content_for_multimedia_needs(
        data['content_text'], lesson_topic
    )

    if "error" in result:
        return jsonify(result), 500

    return jsonify(result)

@bp.route('/api/admin/generate-lesson-images', methods=['POST'])
@login_required
@admin_required
def generate_lesson_images():
    """Generate multiple images for lesson content."""
    data = request.json
    if not data or 'lesson_content' not in data:
        return jsonify({"error": "Missing 'lesson_content' in request"}), 400

    generator = AILessonContentGenerator()
    lesson_topic = data.get('lesson_topic', 'Japanese Language Learning')
    difficulty = data.get('difficulty', 'Beginner')
    
    result = generator.generate_lesson_images(
        data['lesson_content'], lesson_topic, difficulty
    )

    if "error" in result:
        return jsonify(result), 500

    return jsonify(result)

# == VOCABULARY IMAGE GENERATION API ==
@bp.route('/api/admin/vocabulary/generate-images', methods=['POST'])
@login_required
@admin_required
def generate_vocabulary_images():
    """Batch-generate simple icon images for vocabulary items without images."""
    import uuid

    data = request.json or {}
    vocab_ids = data.get('vocabulary_ids')  # Optional: specific IDs, otherwise all without image

    if vocab_ids:
        vocabs = Vocabulary.query.filter(Vocabulary.id.in_(vocab_ids)).all()
    else:
        vocabs = Vocabulary.query.filter(
            (Vocabulary.image_url.is_(None)) | (Vocabulary.image_url == '')
        ).all()

    if not vocabs:
        return jsonify({"message": "Keine Vokabeln ohne Bild gefunden.", "generated": 0}), 200

    generator = AILessonContentGenerator()
    generated = []
    errors = []
    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'vocabulary', 'images')
    os.makedirs(upload_dir, exist_ok=True)

    for vocab in vocabs:
        result = generator.generate_vocabulary_image(vocab.word, vocab.meaning)
        if 'error' in result:
            errors.append({"id": vocab.id, "word": vocab.word, "error": result['error']})
            continue

        filename = f"vocab_{vocab.id}_{uuid.uuid4().hex[:8]}.png"
        relative_path = f"vocabulary/images/{filename}"
        save_path = os.path.join(upload_dir, filename)

        try:
            result['image'].save(save_path, 'PNG')
            vocab.image_url = relative_path
            generated.append({"id": vocab.id, "word": vocab.word, "image_url": relative_path})
        except Exception as e:
            errors.append({"id": vocab.id, "word": vocab.word, "error": str(e)})

    db.session.commit()
    return jsonify({
        "generated": len(generated),
        "errors": len(errors),
        "details": generated,
        "error_details": errors
    }), 200


# == FILE UPLOAD API ==
from app.utils import FileUploadHandler # Import FileUploadHandler

# == FILE UPLOAD API ==
@bp.route('/api/admin/upload-file', methods=['POST'])
@login_required
@admin_required
def upload_file():
    """Handle file upload, validate, process, and return file information"""
    import os
    from app.utils import FileUploadHandler

    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file part in the request'}), 400

    file_storage = request.files['file']
    lesson_id_str = request.form.get('lesson_id') # Optional: for organizing files by lesson
    lesson_id = int(lesson_id_str) if lesson_id_str and lesson_id_str.isdigit() else None

    if not file_storage or not file_storage.filename:
        return jsonify({'success': False, 'error': 'No file selected'}), 400

    original_filename = file_storage.filename

    # Check allowed extensions (basic check)
    file_type_from_ext = FileUploadHandler.get_file_type(original_filename)
    if not file_type_from_ext:
        return jsonify({'success': False, 'error': 'File type not allowed by extension.'}), 415

    if not FileUploadHandler.allowed_file(original_filename, file_type_from_ext):
        return jsonify({'success': False, 'error': f"File extension for '{file_type_from_ext}' not allowed."}), 415

    try:
        # Use the new save_file method which handles local/GCS storage
        relative_file_path, file_info, error = FileUploadHandler.save_file(
            file_storage, 
            file_type_from_ext, 
            lesson_id
        )
        
        if error:
            return jsonify({'success': False, 'error': error}), 500
            
        # Construct the full URL
        # We can use a dummy LessonContent to leverage the get_file_url logic
        # or just replicate it here for the response
        bucket_name = current_app.config.get('GCS_BUCKET_NAME')
        if bucket_name:
            clean_path = relative_file_path.lstrip('/')
            file_url = f"https://storage.googleapis.com/{bucket_name}/{clean_path}"
        else:
            file_url = url_for('routes.uploaded_file', filename=relative_file_path, _external=False)

        return jsonify({
            'success': True,
            'filePath': file_url,
            'dbPath': relative_file_path, # Path to store in DB
            'fileName': os.path.basename(relative_file_path),
            'originalFilename': original_filename,
            'fileType': file_type_from_ext,
            'fileSize': file_info.get('size'),
            'mimeType': file_info.get('mime_type'),
            'dimensions': file_info.get('dimensions')
        }), 200

    except Exception as e:
        current_app.logger.error(f"File upload failed: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'An server error occurred during file upload.'}), 500


@bp.route('/api/admin/lessons/<int:lesson_id>/content/file', methods=['POST'])
@login_required
@admin_required
def add_file_content(lesson_id):
    """Add file-based content to lesson"""
    lesson = Lesson.query.get_or_404(lesson_id)
    data = request.json
    
    if not data or not data.get('content_type') or not data.get('file_path'):
        return jsonify({"error": "Missing required fields: content_type, file_path"}), 400
    
    # Convert string 'false'/'true' to boolean for is_optional
    is_optional = data.get('is_optional', False)
    if isinstance(is_optional, str):
        is_optional = is_optional.lower() == 'true'
    
    # Determine the next order index
    last_content = LessonContent.query.filter_by(lesson_id=lesson_id).order_by(LessonContent.order_index.desc()).first()
    next_order_index = (last_content.order_index + 1) if last_content else 0

    new_content = LessonContent(
        lesson_id=lesson_id,
        content_type=data['content_type'],
        title=data.get('title'),
        content_text=data.get('description'),
        file_path=data['file_path'],
        file_size=data.get('file_size'),
        file_type=data.get('file_type'),
        original_filename=data.get('original_filename'),
        order_index=next_order_index,
        is_optional=is_optional
    )
    
    try:
        db.session.add(new_content)
        db.session.commit()
        return jsonify(model_to_dict(new_content)), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": f"Database error occurred: {str(e)}"}), 500


@bp.route('/api/admin/delete-file', methods=['DELETE'])
@login_required
@admin_required
def delete_file():
    """Delete uploaded file"""
    from app.utils import FileUploadHandler
    import os
    
    data = request.json
    if not data or not data.get('file_path'):
        return jsonify({"error": "File path required"}), 400
    
    file_path_from_request = data['file_path'] # Renamed for clarity
    content_id = data.get('content_id')

    # Path validation against UPLOAD_FOLDER
    full_request_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file_path_from_request)
    if not os.path.abspath(full_request_path).startswith(os.path.abspath(current_app.config['UPLOAD_FOLDER'])):
        return jsonify({"error": "Access denied: Invalid file path."}), 403

    file_system_deleted = False
    database_record_deleted = False
    message = ""

    if content_id:
        content = LessonContent.query.get(content_id)
        if not content:
            return jsonify({"error": f"Content with ID {content_id} not found."}), 404

        # If content_id is given, we primarily care about its associated file.
        if content.file_path:
            # Validate that the file_path from request (if provided) matches the content's file_path
            # This is an important security/consistency check.
            if file_path_from_request != content.file_path:
                return jsonify({"error": "File path mismatch. The provided file_path does not match the file associated with the content ID."}), 400

            # Attempt to delete the file associated with the content record
            if content.delete_file(): # This now returns True/False
                file_system_deleted = True
                current_app.logger.info(f"File {content.file_path} for content ID {content_id} deleted from filesystem by content.delete_file().")
            else:
                # content.delete_file() failed (e.g., os.remove error)
                # Check if the file still exists; it might have been deleted by another process or never existed
                content_file_full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], content.file_path)
                if not os.path.exists(content_file_full_path):
                    file_system_deleted = True # File is gone, treat as success for this part
                    current_app.logger.info(f"File {content.file_path} for content ID {content_id} was already absent from filesystem.")
                else:
                    current_app.logger.error(f"Failed to delete file {content.file_path} for content ID {content_id} from filesystem.")
        else:
            # Content exists but has no associated file_path in DB.
            # This means there's nothing to delete from the filesystem for this content.
            # If file_path_from_request was provided, it's an orphaned file or incorrect request.
            # We will not delete file_path_from_request in this case to avoid accidental deletion.
            current_app.logger.info(f"Content ID {content_id} has no associated file_path in DB. No file system deletion attempted for this content object.")
            # Consider file_system_deleted as true in the sense that there's no file to delete for this content.
            file_system_deleted = True # Or specific message indicating no file was associated.

        # Delete the content database record
        db.session.delete(content)
        db.session.commit()
        database_record_deleted = True
        message = f"Content ID {content_id} and its associations deleted from database. "

        if file_system_deleted:
            message += "Associated file handled successfully."
            return jsonify({"message": message}), 200
        else:
            message += "Associated file could not be deleted from filesystem or was not found."
            return jsonify({"message": message}), 207 # Multi-Status: DB deleted, file system issue

    else:
        # No content_id provided, this is a request to delete a file directly by its path.
        # This case should be used cautiously. Ensure the file is not still referenced by any LessonContent.
        # For now, we will proceed with deleting the file if it exists.
        # A more robust system might check if this file_path_from_request is referenced in any LessonContent.file_path.
        if not os.path.exists(full_request_path):
            return jsonify({"error": "File not found at the specified path."}), 404

        if FileUploadHandler.delete_file(full_request_path): # This is app.utils.FileUploadHandler.delete_file
            file_system_deleted = True
            message = f"File {file_path_from_request} deleted successfully from filesystem."
            return jsonify({"message": message}), 200
        else:
            message = f"Failed to delete file {file_path_from_request} from filesystem."
            return jsonify({"error": message}), 500

# == LESSON EXPORT/IMPORT API ==
@bp.route('/api/admin/lessons/<int:lesson_id>/export', methods=['GET'])
@login_required
@admin_required
def export_lesson(lesson_id):
    """Export a lesson to JSON format"""
    try:
        include_files = request.args.get('include_files', 'true').lower() == 'true'
        lesson_data = export_lesson_to_json(lesson_id, include_files)
        
        # Set appropriate headers for download
        from flask import make_response
        response = make_response(jsonify(lesson_data))
        response.headers['Content-Disposition'] = f'attachment; filename=lesson_{lesson_id}_export.json'
        response.headers['Content-Type'] = 'application/json'
        
        return response
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        current_app.logger.error(f"Error exporting lesson {lesson_id}: {e}")
        return jsonify({"error": "Failed to export lesson"}), 500

@bp.route('/api/admin/lessons/<int:lesson_id>/export-package', methods=['POST'])
@login_required
@admin_required
def export_lesson_package(lesson_id):
    """Create a complete export package as ZIP file"""
    try:
        data = request.json or {}
        include_files = data.get('include_files', True)
        
        # Create temporary export directory
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = create_lesson_export_package(lesson_id, temp_dir, include_files)
            
            # Read the ZIP file and return it
            with open(zip_path, 'rb') as f:
                zip_data = f.read()
            
            from flask import make_response
            response = make_response(zip_data)
            response.headers['Content-Type'] = 'application/zip'
            response.headers['Content-Disposition'] = f'attachment; filename={os.path.basename(zip_path)}'
            
            return response
            
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        current_app.logger.error(f"Error creating export package for lesson {lesson_id}: {e}")
        return jsonify({"error": "Failed to create export package"}), 500

@bp.route('/api/admin/lessons/import', methods=['POST'])
@login_required
@admin_required
def import_lesson():
    """Import a lesson from a JSON file."""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files['file']
        if not file.filename or not file.filename.endswith('.json'):
            return jsonify({"error": "Please provide a JSON file"}), 400

        try:
            lesson_data = json.load(file.stream)
        except json.JSONDecodeError:
            return jsonify({"error": "Invalid JSON format"}), 400

        handle_duplicates = request.form.get('handle_duplicates', 'rename')
        if handle_duplicates not in ['rename', 'replace', 'skip']:
            return jsonify({"error": "Invalid handle_duplicates option"}), 400

        imported_lesson = import_lesson_from_json(
            lesson_data,
            handle_duplicates=handle_duplicates,
            import_files=False
        )

        return jsonify({
            "success": True,
            "message": "Lesson imported successfully",
            "imported_count": 1,
            "lesson_id": imported_lesson.id,
            "lesson_title": imported_lesson.title
        }), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error importing lesson: {e}", exc_info=True)
        return jsonify({"error": "Failed to import lesson"}), 500

@bp.route('/api/admin/lessons/import-package', methods=['POST'])
@login_required
@admin_required
def import_lesson_package():
    """Import a lesson from ZIP package"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if not file.filename or not file.filename.endswith('.zip'):
            return jsonify({"error": "Please provide a ZIP file"}), 400
        
        # Get import options
        handle_duplicates = request.form.get('handle_duplicates', 'rename')
        if handle_duplicates not in ['rename', 'replace', 'skip']:
            return jsonify({"error": "Invalid handle_duplicates option"}), 400
        
        # Save uploaded file temporarily
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_file:
            file.save(temp_file.name)
            temp_zip_path = temp_file.name
        
        try:
            # Import the lesson
            imported_lesson = import_lesson_from_zip(temp_zip_path, handle_duplicates)
            
            return jsonify({
                "success": True,
                "message": "Lesson package imported successfully",
                "lesson_id": imported_lesson.id,
                "lesson_title": imported_lesson.title,
                "imported_count": 1
            }), 201
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_zip_path):
                os.unlink(temp_zip_path)
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error importing lesson package: {e}")
        return jsonify({"error": "Failed to import lesson package"}), 500

@bp.route('/api/admin/lessons/export-multiple', methods=['POST'])
@login_required
@admin_required
def export_multiple_lessons():
    """Export multiple lessons as a single ZIP package"""
    try:
        data = request.json
        if not data or 'lesson_ids' not in data:
            return jsonify({"error": "No lesson IDs provided"}), 400
        
        lesson_ids = data['lesson_ids']
        include_files = data.get('include_files', True)
        
        if not lesson_ids:
            return jsonify({"error": "Empty lesson IDs list"}), 400
        
        # Create temporary directory for export
        import tempfile
        import os
        import zipfile
        from datetime import datetime
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create main ZIP file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            main_zip_path = os.path.join(temp_dir, f"lessons_export_{timestamp}.zip")
            
            with zipfile.ZipFile(main_zip_path, 'w', zipfile.ZIP_DEFLATED) as main_zipf:
                exported_lessons = []
                
                for lesson_id in lesson_ids:
                    try:
                        # Export individual lesson
                        lesson_zip_path = create_lesson_export_package(
                            lesson_id, temp_dir, include_files
                        )
                        
                        # Add to main ZIP
                        lesson_zip_name = os.path.basename(lesson_zip_path)
                        main_zipf.write(lesson_zip_path, lesson_zip_name)
                        
                        # Track successful exports
                        lesson = Lesson.query.get(lesson_id)
                        if lesson:
                            exported_lessons.append({
                                'id': lesson_id,
                                'title': lesson.title,
                                'filename': lesson_zip_name
                            })
                        
                        # Clean up individual ZIP
                        os.unlink(lesson_zip_path)
                        
                    except Exception as e:
                        current_app.logger.error(f"Error exporting lesson {lesson_id}: {e}")
                        continue
                
                # Add manifest file
                manifest = {
                    'export_info': {
                        'version': '1.0',
                        'exported_at': datetime.utcnow().isoformat(),
                        'total_lessons': len(exported_lessons),
                        'includes_files': include_files
                    },
                    'lessons': exported_lessons
                }
                
                manifest_json = json.dumps(manifest, indent=2, ensure_ascii=False)
                main_zipf.writestr('export_manifest.json', manifest_json)
            
            # Return the ZIP file
            with open(main_zip_path, 'rb') as f:
                zip_data = f.read()
            
            from flask import make_response
            response = make_response(zip_data)
            response.headers['Content-Type'] = 'application/zip'
            response.headers['Content-Disposition'] = f'attachment; filename={os.path.basename(main_zip_path)}'
            
            return response
            
    except Exception as e:
        current_app.logger.error(f"Error exporting multiple lessons: {e}")
        return jsonify({"error": "Failed to export lessons"}), 500

@bp.route('/uploads/<path:filename>')
@limiter.exempt
def uploaded_file(filename):
    """Serve uploaded files — lokal oder via GCS-Redirect"""
    import os
    from flask import send_from_directory

    upload_folder = current_app.config['UPLOAD_FOLDER']
    file_path = os.path.join(upload_folder, filename)

    # Security check - ensure file is within upload folder
    if not os.path.abspath(file_path).startswith(os.path.abspath(upload_folder)):
        return jsonify({"error": "Access denied"}), 403

    # Lokal vorhanden? Direkt ausliefern
    if os.path.exists(file_path):
        directory = os.path.dirname(file_path)
        basename = os.path.basename(file_path)
        return send_from_directory(directory, basename)

    # Fallback: GCS-Redirect wenn Bucket konfiguriert
    bucket_name = current_app.config.get('GCS_BUCKET_NAME')
    if bucket_name:
        gcs_url = f"https://storage.googleapis.com/{bucket_name}/{filename}"
        return redirect(gcs_url)

    return jsonify({"error": "File not found"}), 404

@bp.route('/api/admin/lessons/import-info', methods=['POST'])
@login_required
@admin_required
def get_import_info():
    """Get information about a lesson import file without importing"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files['file']
        if not file.filename:
            return jsonify({"error": "No file selected"}), 400

        if file.filename.endswith('.json'):
            # Handle JSON file upload
            try:
                lesson_data = json.load(file.stream)
            except json.JSONDecodeError:
                return jsonify({"error": "Invalid JSON format"}), 400
            
            existing_lesson = Lesson.query.filter_by(title=lesson_data['title']).first()
            
            return jsonify({
                "success": True,
                "info": {
                    "file_type": "json",
                    "lesson_count": 1,
                    "lessons": [{
                        "title": lesson_data['title'],
                        "difficulty": lesson_data.get('difficulty_level'),
                        "pages": len(lesson_data.get('pages', [])),
                        "content_count": len(lesson_data.get('content', [])),
                        "files": [item.get('file_info') for item in lesson_data.get('content', []) if item.get('file_info')]
                    }],
                    "warnings": ["A lesson with this title already exists."] if existing_lesson else []
                }
            })

        elif file.filename.endswith('.zip'):
            # Handle ZIP file
            import tempfile
            import zipfile
            
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_file:
                file.save(temp_file.name)
                temp_zip_path = temp_file.name
            
            try:
                with zipfile.ZipFile(temp_zip_path, 'r') as zipf:
                    if 'lesson_data.json' in zipf.namelist():
                        lesson_json = zipf.read('lesson_data.json').decode('utf-8')
                        lesson_data = json.loads(lesson_json)
                        existing_lesson = Lesson.query.filter_by(title=lesson_data['title']).first()
                        
                        return jsonify({
                            "success": True,
                            "info": {
                                "file_type": "single_lesson_zip",
                                "lesson_count": 1,
                                "lessons": [{
                                    "title": lesson_data['title'],
                                    "difficulty": lesson_data.get('difficulty_level'),
                                    "pages": len(lesson_data.get('pages', [])),
                                    "content_count": len(lesson_data.get('content', [])),
                                    "files": [item.get('file_info') for item in lesson_data.get('content', []) if item.get('file_info')]
                                }],
                                "warnings": ["A lesson with this title already exists."] if existing_lesson else []
                            }
                        })
                    
                    elif 'export_manifest.json' in zipf.namelist():
                        manifest_json = zipf.read('export_manifest.json').decode('utf-8')
                        manifest = json.loads(manifest_json)
                        
                        lessons_info = []
                        for lesson_info in manifest.get('lessons', []):
                            existing_lesson = Lesson.query.filter_by(title=lesson_info['title']).first()
                            lessons_info.append({
                                **lesson_info,
                                "duplicate_exists": existing_lesson is not None,
                                "duplicate_id": existing_lesson.id if existing_lesson else None
                            })
                        
                        return jsonify({
                            "success": True,
                            "info": {
                                "file_type": "multiple_lessons_zip",
                                "lesson_count": len(lessons_info),
                                "lessons": lessons_info
                            }
                        })
                    
                    else:
                        return jsonify({"success": False, "error": "Invalid ZIP package format"}), 400
            
            finally:
                import os
                if os.path.exists(temp_zip_path):
                    os.unlink(temp_zip_path)
        
        else:
            return jsonify({"success": False, "error": "Unsupported file format"}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error getting import info: {e}")
        return jsonify({"success": False, "error": "Failed to analyze import file"}), 500
