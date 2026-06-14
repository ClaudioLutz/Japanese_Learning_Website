# 06 · Authentifizierung & Zugriffskontrolle
_Stand: 2026-06-14 · Commit 2947710 · Teil der Ist-Zustand-Dokumentation_

## Zweck
Dieses Subsystem deckt ab, wie sich Nutzer registrieren, anmelden (lokal mit E-Mail/Passwort oder via Google OAuth), abmelden und ihr Passwort zurücksetzen. Es umfasst die Session-Verwaltung über Flask-Login, die Konto-Schutzmechanismen (Lockout nach Fehlversuchen, Rate-Limiting), die Rollen-/Abo-Felder am User (`is_admin`, `subscription_level`) und die zentrale Zugriffskontroll-Kaskade, die entscheidet, ob ein Nutzer (oder Gast) eine Lektion sehen darf.

## Komponenten
| Datei | Zeilen | Rolle |
|---|---|---|
| `app/routes.py` | 4'863 (gesamt) | Auth-Views (`/register`, `/login`, `/logout`, `/forgot-password`, `/reset-password/<token>`, `/profile`, `/upgrade_to_premium`, `/downgrade_from_premium`) + Decorators `premium_required`/`admin_required` (Z. 37-53) + Nutzung der Zugriffskaskade |
| `app/forms.py` | 67 | WTForms: `RegistrationForm`, `LoginForm`, `RequestPasswordResetForm`, `ResetPasswordForm`, `CSRFTokenForm` |
| `app/auth_tokens.py` | 18 | Reset-Token-Mechanik (signiert + zeitlich befristet via `itsdangerous`) |
| `app/oauth_routes.py` | 114 | Eigener Google-OAuth-Callback (`oauth_bp`, Prefix `/auth`), umgeht die social-auth-Library |
| `app/social_auth_config.py` | 127 | python-social-auth Pipeline-Funktionen: `fix_google_uid`, `create_user_and_login`, `custom_associate_user` |
| `app/models.py` | — | `User`-Modell (Z. 11-134), `load_user` (Z. 1243-1245), `Lesson.is_accessible_to_user` (Z. 793-865) — die zentrale Zugriffsfunktion |
| `app/__init__.py` | — | `LoginManager`-Konfiguration (Z. 23-29), Blueprint-Registrierung, social-auth-Config (Z. 104-122), CSRF/Limiter-Init |
| `app/mail_service.py` | — | `send_password_reset_email` (Z. 11) — versendet Reset-Link (HTML + Text) |
| `app/templates/{login,register,forgot_password,reset_password,user_profile}.html` | — | Benutzersichtbare Auth-Formulare und Profilseite |

---

## Lokale Authentifizierung (app/routes.py)

Alle lokalen Auth-Routen hängen am Haupt-Blueprint `bp = Blueprint('routes', __name__)` (`app/routes.py:34`). Sie sind über Flask-Limiter rate-limited.

| Route | Methode | Formular | Rate-Limit | Was passiert | Redirect |
|---|---|---|---|---|---|
| `/register` (Z. 490) | GET, POST | `RegistrationForm` | 5/min | Legt `User` an, setzt Passwort-Hash, **loggt direkt ein** (`login_user`) | siehe Auto-Login-Logik unten |
| `/login` (Z. 522) | GET, POST | `LoginForm` | 10/min | Prüft Lockout → `check_password` → `record_successful_login` + `login_user(remember=…)`; bei Fehlschlag `record_failed_login` | `next` (relativ) sonst Admin→`admin_index`, User→`index` |
| `/forgot-password` (Z. 556) | GET, POST | `RequestPasswordResetForm` | 3/h | Bei existierendem User: Token erzeugen + Mail; Antwort identisch egal ob User existiert (Enumeration-Schutz) | `login` |
| `/reset-password/<token>` (Z. 578) | GET, POST | `ResetPasswordForm` | 10/h | Token via `verify_reset_token` prüfen → neues Passwort setzen + Lockout aufheben | `login` (bei ungültigem Token: `forgot_password`) |
| `/logout` (Z. 603) | GET | — (`@login_required`) | — | `logout_user()` | `index` |
| `/profile` (Z. 610) | GET | — (`@login_required`) | — | Aggregiert Lektions-Fortschritt, Statistiken, Käufe | rendert `user_profile.html` |
| `/upgrade_to_premium` (Z. 690) | POST | `CSRFTokenForm` (`@login_required`) | — | **Prototyp:** setzt `subscription_level='premium'` ohne Zahlung | `index` |
| `/downgrade_from_premium` (Z. 704) | POST | `CSRFTokenForm` (`@login_required`) | — | **Prototyp:** setzt `subscription_level='free'` | `index` |

### register() — `next`-Param + Auto-Login (Z. 490-520)
- Bei bereits eingeloggtem Nutzer sofort Redirect auf `index`.
- Nach erfolgreicher Validierung: User anlegen → `set_password` → committen → **`login_user(user)`** (kein separater Login-Schritt mehr).
- `next` wird aus `request.values.get('next')` gelesen (Query **oder** Hidden-Field — `register.html:57` rendert `<input type="hidden" name="next">`).
- **Open-Redirect-Schutz:** `next` wird nur akzeptiert, wenn es mit `/` beginnt und **nicht** mit `//` (Z. 508).
- Fallback ohne gültiges `next`: erste Gast-Lektion (`first_guest_lesson` aus `_build_n5_path_context`) → sonst `index#lernpfad`.

### login() — Lockout + Open-Redirect-Schutz (Z. 522-554)
- Vorabprüfung `user.is_locked` → Konto vorübergehend gesperrt, kein Passwort-Check.
- Erfolg: `record_successful_login()` (setzt Fehlerzähler zurück + `update_streak()`), dann `login_user(user, remember=form.remember.data)`.
- Fehlschlag: `record_failed_login()` (zählt hoch, sperrt ab Schwelle).
- `next` aus `request.args.get('next')`, gleicher Open-Redirect-Schutz wie `register()`.

### Konto-Lockout (`app/models.py:40-60`)
- `LOCKOUT_THRESHOLD = 5`, `LOCKOUT_DURATION_MINUTES = 15`.
- `record_failed_login`: erhöht `failed_login_count`; ab 5 wird `locked_until = utcnow() + 15 min` gesetzt.
- `is_locked` (Property): `True`, solange `locked_until > utcnow()`.
- Passwort-Reset hebt Lockout auf (`failed_login_count=0`, `locked_until=None`, `routes.py:595-596`).

### Passwort-Regeln (`app/forms.py`)
- `RegistrationForm`/`ResetPasswordForm`: Länge 8-128, **mind. 1 Grossbuchstabe, 1 Kleinbuchstabe, 1 Ziffer** (Regex-Validator, Z. 16-24 / 55-62).
- `RegistrationForm` prüft Eindeutigkeit von Username und E-Mail gegen die DB (Z. 26-34).

### Reset-Token (`app/auth_tokens.py`)
- `make_reset_token(user_id)`: `URLSafeTimedSerializer(SECRET_KEY, salt='pwd-reset-v1').dumps(user_id)`.
- `verify_reset_token(token, max_age=3600)`: gibt User-ID zurück oder `None` (bei `BadSignature`/`SignatureExpired`/`ValueError`/`TypeError`). **Token läuft nach 1 Stunde ab.** Es wird kein Token in der DB gespeichert — Gültigkeit rein kryptografisch.

---

## Google OAuth

Zwei parallele Mechanismen sind registriert; die App nutzt faktisch den eigenen Callback.

### Login-Einstieg
- Beide Auth-Templates verlinken `url_for('social.auth', backend='google-oauth2')` (`login.html:13`, `register.html:50`) — das ist die social-auth-Standard-Route, registriert via `app.register_blueprint(social_auth, url_prefix='/auth')` (`app/__init__.py:371`).

### Eigener Callback (`app/oauth_routes.py`)
- Blueprint `oauth_bp = Blueprint('oauth', __name__, url_prefix='/auth')` (Z. 11), registriert **vor** social-auth, um dessen Callback zu überschreiben (`__init__.py:260-262`).
- Route `/auth/complete/google-oauth2/` (Z. 13):
  1. Authorization-Code aus Query holen; fehlt er → Redirect `/login?error=oauth_failed`.
  2. Code gegen Token tauschen (`https://oauth2.googleapis.com/token`), `redirect_uri` wird dynamisch aus `request.url_root` + `/auth/complete/google-oauth2/` zusammengesetzt (Z. 34).
  3. Userinfo abrufen, User per E-Mail suchen; falls neu: Username aus E-Mail-Prefix (mit Eindeutigkeits-Suffix), `password_hash=''`, `subscription_level='free'`.
  4. `login_user(user, remember=True)`.
  5. Falls kein `social_auth_usersocialauth`-Eintrag existiert: per Raw-SQL anlegen (uid = Google `id`/`sub`/E-Mail).
  6. Redirect `/`.
- **Redirect-URI-Konvention:** `<scheme://host>/auth/complete/google-oauth2/` **mit Trailing-Slash** (muss so in der Google Cloud Console hinterlegt sein — vgl. CLAUDE.md, offene Baustelle 3).

### social-auth Pipeline (`app/social_auth_config.py`, Konfig in `app/__init__.py:104-122`)
Konfiguriert (zusätzlich zum eigenen Callback) als `SOCIAL_AUTH_PIPELINE`:
- `social_details` → `social_uid` → **`fix_google_uid`** → `auth_allowed` → **`create_user_and_login`** → **`custom_associate_user`**.
- `fix_google_uid` (Z. 9): erzwingt Googles `sub`-Feld als uid statt der E-Mail.
- `create_user_and_login` (Z. 77): bestehenden User einloggen oder neu anlegen (`password_hash=''`, `subscription_level='free'`) + `login_user(remember=True)`.
- `custom_associate_user` (Z. 20): legt fehlenden `social_auth_usersocialauth`-Eintrag per Raw-SQL an.
- Weitere Config: `SOCIAL_AUTH_GOOGLE_OAUTH2_KEY/SECRET` aus `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET`, Scope `['openid','email','profile']`, PKCE aktiv, `USER_ID_KEY='sub'`, Login-Redirect `/`, Error-Redirect `/login`, Storage `social_flask_sqlalchemy.models.FlaskStorage`.

---

## Session-Verwaltung (Flask-Login)
- `login_manager = LoginManager()` (`app/__init__.py:23`), `login_view='routes.login'`, `login_message='Bitte melden Sie sich an, um diese Seite zu sehen.'`, Kategorie `info` (Z. 27-29).
- `@login_manager.user_loader def load_user(user_id)` lädt `User.query.get(int(user_id))` (`app/models.py:1243-1245`).
- `User` erbt von `UserMixin` (`app/models.py:11`).

---

## Decorators

| Decorator | Definition | Prüfung | Bei Fehlschlag |
|---|---|---|---|
| `@login_required` | Flask-Login (importiert `routes.py:7`) | Nutzer authentifiziert? | Redirect auf `login_view` mit `login_message` |
| `@admin_required` | `app/routes.py:46-53` | `current_user.is_authenticated` **und** `current_user.is_admin` | Flash `'Admin access required.'` (danger) → Redirect `index` |
| `@premium_required` | `app/routes.py:37-44` | `current_user.is_authenticated` **und** `subscription_level == 'premium'` | Flash `'Premium membership required…'` (warning) → Redirect `index` |

`@admin_required` wird breit eingesetzt (Admin-Routen ab `routes.py:721` u. v. m.). Die Kern-Lektions-Zugriffslogik selbst läuft jedoch nicht über `@premium_required`, sondern über `Lesson.is_accessible_to_user` (siehe unten).

---

## Zugriffskontroll-Kaskade für Lektionen

Zentrale Funktion: **`Lesson.is_accessible_to_user(self, user)`** (`app/models.py:793-865`). Gibt ein Tupel `(bool, nachricht)` zurück. Aufgerufen an 8 Stellen in `routes.py` (Z. 1076, 1265, 1280, 3038, 3098, 3208, 3293, 3957) — u. a. in `view_lesson` (Z. 1273).

Prüfreihenfolge:
1. **Gast (nicht authentifiziert):** Zugriff nur wenn `price == 0.0` **und** `allow_guest_access` → `(True, "Als Gast zugänglich")`; sonst `(False, "Login required to access this lesson")` (englischer String dient als Trigger für Login-Redirect).
2. **Admin-Bypass:** `is_admin` → `(True, "Admin")`, sieht alles.
3. **Kostenlose Lektion** (`price == 0.0`): nur Voraussetzungen (`get_prerequisites()`) prüfen — jede muss eine **abgeschlossene** `UserLessonProgress` haben, sonst `(False, "Schliesse zuerst „<Titel>" ab")`.
4. **Bezahllektion** (`is_purchasable`): direkter `LessonPurchase` ODER `CoursePurchase` eines Kurses, der die Lektion enthält → danach Voraussetzungen; ohne Kauf `(False, "Kauf erforderlich (CHF <preis>)")`.
5. **Legacy-Premium:** `lesson_type == 'premium'` und `subscription_level != 'premium'` → `(False, "Premium-Abo erforderlich")`.
6. **Restfälle:** Voraussetzungen prüfen → `(True, "Zugänglich")`.

### Verhalten von `view_lesson` bei Verweigerung (`app/routes.py:1281-1322`)
- Bezahllektion + nicht zugänglich → eigene Seite `lesson_paywall.html` (Bundle-CTA + Single-Kauf).
- Login fehlt (`'Login required' in message`) → Redirect `routes.login` mit `next=request.url`.
- Sonst (Voraussetzungen etc.) → Flash + Redirect `routes.lessons`.

### User-Rollen-/Abo-Felder (`app/models.py:11-32`)
- `subscription_level: String(50), default='free'` — Werte `free`/`premium`.
- `is_admin: Boolean, default=False`.
- `password_hash: String(256)` (Werkzeug `generate_password_hash`/`check_password_hash`, `models.py:127-131`). OAuth-Nutzer haben `password_hash=''`.
- Weitere: `failed_login_count`, `locked_until` (Lockout); `current_streak`, `total_xp`, `level` (Gamification, hier nur Kontext).

### ASCII — Entscheidungsbaum Zugriffskontrolle
```
Lesson.is_accessible_to_user(user)
│
├─ user == None / nicht authentifiziert?
│     ├─ price == 0.0 UND allow_guest_access ──────────► (True, "Als Gast zugänglich")
│     └─ sonst ───────────────────────────────────────► (False, "Login required…")  ──► view_lesson: Redirect /login?next=…
│
├─ user.is_admin? ───────────────────────────────────► (True, "Admin")   [Bypass: alles sichtbar]
│
├─ price == 0.0 (kostenlose Lektion)?
│     ├─ alle Voraussetzungen abgeschlossen? ─ ja ────► (True, "Kostenlose Lektion")
│     └─ nein ────────────────────────────────────────► (False, "Schliesse zuerst „X" ab")
│
├─ is_purchasable (Bezahllektion)?
│     ├─ LessonPurchase vorhanden? ─ ja ─► Voraussetzungen ─► (True, "Gekauft")
│     ├─ CoursePurchase deckt Lektion? ─ ja ─► Voraussetzungen ─► (True, "Zugriff über „Kurs"")
│     └─ kein Kauf ───────────────────────────────────► (False, "Kauf erforderlich (CHF n.nn)")
│                                                         └─► view_lesson: lesson_paywall.html
│
├─ lesson_type == 'premium' UND subscription_level != 'premium'?
│     └─ ja ──────────────────────────────────────────► (False, "Premium-Abo erforderlich")
│
└─ Restfall: Voraussetzungen prüfen ─────────────────► (True, "Zugänglich")
```

---

## Templates

| Template | Aufbau (kurz) |
|---|---|
| `login.html` | Erbt `base.html`, `robots=noindex,follow`. Google-Button (`social.auth`), Trenner, E-Mail/Passwort-Formular (`form.hidden_tag()` = CSRF), „Angemeldet bleiben"-Checkbox, „Passwort vergessen?"-Link, Link zur Registrierung. Zeigt `?error=oauth_failed`-Banner. |
| `register.html` | Wie login. Google-Button, Username/E-Mail/Passwort-Formular. **Hidden-Field `next`** aus `request.args` (Z. 57). Zwei Passwort-Felder mit Alpine.js Show/Hide-Toggle + sichtbarer Passwort-Hinweis. |
| `forgot_password.html` | Einfaches E-Mail-Feld + Hinweis „Link 1 Stunde gültig", Link zurück zur Anmeldung. |
| `reset_password.html` | Zwei Passwort-Felder (neu + Wiederholung) mit Hinweis auf Passwort-Regeln. Form-Action ist die `/reset-password/<token>`-URL (token im Pfad). |
| `user_profile.html` | Profil-Header (Gradient-Avatar), Statistik-Karten (gestartete/abgeschlossene Lektionen, Completion-Rate, Zeit), Kategorie-Statistik, letzte Aktivität, Käufe. `robots=noindex,follow`. |

Mail-Versand: `forgot_password` ruft `send_password_reset_email(user.email, link, username)` (`app/mail_service.py:11`); der Link wird via `url_for('routes.reset_password', token=token, _external=True)` erzeugt (HTML + Text-Variante gerendert).

---

## Zusammenspiel
- **Eingehend:** Geschützte Routen im ganzen Projekt nutzen `@login_required`/`@admin_required`/`@premium_required`. Bei fehlendem Login leitet Flask-Login automatisch auf `routes.login` (mit `login_message`). Templates verlinken vielfach `routes.login`/`routes.register` (teils mit `next`-Param aus Paywall/Bundle-CTAs).
- **Zugriffskontrolle als Drehscheibe:** `Lesson.is_accessible_to_user` ist die gemeinsame Gate-Funktion für Lektions-Views, Katalog-Listen und APIs (8 Aufrufstellen). Sie liest `LessonPurchase`/`CoursePurchase` (Payment-Subsystem) und `UserLessonProgress` (Fortschritts-Subsystem).
- **Ausgehend (Redirects):** erfolgreicher Login/Register → `index`, `admin_index`, erste Gast-Lektion oder `next`-Ziel; Logout → `index`; Reset-Flow → `login`/`forgot_password`; verweigerte Bezahllektion → `lesson_paywall.html`; Login-pflichtige Lektion → `/login?next=…`.
- **OAuth:** Google-Callback (`/auth/complete/google-oauth2/`) legt User mit `subscription_level='free'` an und schreibt `social_auth_usersocialauth` — danach Redirect `/`.
- **Payment:** `subscription_level` wird derzeit nur durch die Prototyp-Routen `/upgrade_to_premium` / `/downgrade_from_premium` verändert (kein echter Zahlungs-Trigger an dieser Stelle).
- **Infrastruktur:** CSRF (`csrf`), Rate-Limiting (`limiter`) und Mail (`mail`) werden in `app/__init__.py` initialisiert; SEO-Blueprint ist von CSRF ausgenommen.

## Beobachtungen (Ansatzpunkte)
- Zwei parallele Google-OAuth-Pfade existieren: der eigene `oauth_bp`-Callback (`app/oauth_routes.py`) und die vollständig konfigurierte social-auth-Pipeline (`app/social_auth_config.py`) mit überlappender Logik (User-Anlage, `social_auth_usersocialauth`-Insert per Raw-SQL an zwei Stellen).
- `oauth_routes.py` und `social_auth_config.py` schreiben `social_auth_usersocialauth` mit `text()`-Raw-SQL statt über das ORM-Modell.
- `/upgrade_to_premium` und `/downgrade_from_premium` ändern `subscription_level` ohne jegliche Zahlungsprüfung; im Code als „**PROTOTYPE ONLY**" markiert (`routes.py:695`, `709`).
- Flash-/Rückgabe-Strings sind sprachlich gemischt: die Prototyp-Premium-Routen und der Trigger-String `"Login required to access this lesson"` sind englisch, der Rest der Zugriffskaskade deutsch. Der englische String wird in `view_lesson` per Substring-Match (`'Login required' in message`) als Redirect-Trigger ausgewertet (`routes.py:1318`).
- Reset-Token sind rein kryptografisch (kein DB-Record, keine Einmal-Verwendung/Invalidierung) — ein gültiger Token bleibt innerhalb seiner Stunde mehrfach verwendbar.
- `RegistrationForm` validiert E-Mail-/Username-Eindeutigkeit, der OAuth-Pfad umgeht WTForms komplett und prüft Eindeutigkeit per eigener While-Schleife.
- `is_locked`/`locked_until` arbeiten mit `datetime.utcnow()`, während der Streak (`update_streak`) bewusst `Europe/Zurich` nutzt — gemischte Zeitzonen-Basis im selben Modell.
- `Lesson.is_accessible_to_user` wiederholt den Prerequisite-Prüfblock viermal inline (kostenlos / Kauf / Kurs-Kauf / Restfall).
- `routes.py` ist 4'863 Zeilen lang und vermischt Auth-Views, Decorators, Lektions-Views und APIs in einer Datei.
