# Playwright E2E Test — Findings

**Datum**: 20.03.2026
**Projekt**: Japanese Learning Website
**Testumgebung**: Flask Dev-Server mit SQLite (Test-DB), Chromium Headless
**Playwright Version**: 1.58.2
**Anzahl Tests**: 135

---

## Zusammenfassung

| Kategorie | Anzahl | Status |
|-----------|--------|--------|
| Bestanden | ~110 | OK |
| Fehlgeschlagen | ~25 | Bugs / Timeouts |

---

## Kritische Bugs (Severity: HOCH)

### BUG-001: `/course/<id>` crasht ohne Authentifizierung (500 Internal Server Error)

- **Datei**: `app/routes.py`, Zeile 415-417
- **Fehler**: `'AnonymousUserMixin' object has no attribute 'id'`
- **Ursache**: Die Route `view_course()` greift in der For-Schleife (Zeile 415) auf `current_user.id` zu, ohne vorher zu prüfen ob der User eingeloggt ist. Der Auth-Check (Zeile 402) setzt nur `has_purchased`, aber der Progress-Loop danach nutzt `current_user.id` direkt.
- **Betroffene Zeilen**:
  ```python
  # Zeile 415-417 — KEIN Auth-Check vor current_user.id
  progress = UserLessonProgress.query.filter_by(
      user_id=current_user.id, lesson_id=lesson.id
  ).first()
  ```
- **Impact**: Jeder unauthentifizierte Besucher der eine Kurs-Detailseite öffnet sieht einen 500-Fehler.
- **Fix**: Progress-Loop in `if current_user.is_authenticated:` Block einschliessen, oder Default-Werte für Gäste setzen.

---

### BUG-002: `/course/<id>` crasht bei ungültigen `difficulty_level`-Werten (500)

- **Datei**: `app/routes.py`, Zeile 438
- **Fehler**: `unsupported operand type(s) for +: 'int' and 'str'`
- **Ursache**: `sum(difficulty_levels)` funktioniert nur wenn `difficulty_level` ein Integer ist. Das Model (`models.py:127`) definiert es als `Integer`, aber es gibt keine Validierung beim Erstellen von Lektionen. Wenn ein String gespeichert wird (z.B. via Admin-API), crasht die Kursansicht.
- **Betroffene Zeile**:
  ```python
  # Zeile 438
  average_difficulty = sum(difficulty_levels) / len(difficulty_levels)
  ```
- **Impact**: Crash der Kursansicht wenn auch nur eine Lektion ein ungültiges `difficulty_level` hat.
- **Fix**: Input-Validierung in der Admin-API und/oder `try/except` um die Berechnung.

---

### BUG-003: Premium-Zugriffskontrolle hat Logik-Lücke

- **Datei**: `app/models.py`, Zeile 166-233 (`is_accessible_to_user()`)
- **Ursache**: Die Premium-Prüfung (Zeile 222) kommt erst NACH dem Free-Lesson-Check (Zeile 177). Premium-Lektionen mit `price=0.0` und `is_purchasable=False` werden als "Free lesson" durchgelassen, weil der Premium-Check nie erreicht wird.
- **Logik-Flow**:
  1. Zeile 177: `if self.price == 0.0` → True für Premium-Lektion ohne Preis
  2. Gibt `True, "Free lesson"` zurück
  3. Zeile 222 (Premium-Check) wird NIE erreicht
- **Impact**: Free-User können Premium-Lektionen ohne Abo ansehen, wenn diese keinen Preis haben.
- **Fix**: `lesson_type == 'premium'`-Check VOR den Preis-Check setzen.

---

## Mittlere Bugs (Severity: MITTEL)

### BUG-004: `/courses`-Seite blockiert bei externen Ressourcen (Timeout)

- **Beobachtung**: Die Courses-Seite lädt interne Inhalte korrekt (API-Calls zu `/api/courses` funktionieren), aber `page.goto('/courses')` mit Standard-Wait (`load`) erreicht nie den "load"-Event.
- **Ursache**: Externe CSS/JS-Ressourcen (Bootstrap CDN, FontAwesome CDN etc.) blockieren den Page-Load. In einer Testumgebung ohne schnelle Internet-Verbindung führt dies zu 30s Timeouts.
- **Impact**: Langsame Seitenladung für Nutzer mit schlechter Verbindung. Keine lokale Fallback-Strategie für CDN-Assets.
- **Empfehlung**: CDN-Assets mit `async`/`defer` laden oder lokale Kopien als Fallback bereitstellen.

### BUG-005: Registrierung leitet nicht korrekt weiter

- **Beobachtung**: Nach erfolgreicher Registrierung (`POST /register`) wird der User nicht zuverlässig weitergeleitet. Der Test wartet 11s+ auf einen URL-Wechsel.
- **Mögliche Ursache**: Redirect geht zur Login-Seite, die wiederum externe Ressourcen lädt und den Page-Load blockiert.
- **Impact**: Schlechte UX nach Registrierung — User wartet lange auf die nächste Seite.

### BUG-006: Fehlende statische Datei `Lesson_Background.png`

- **Beobachtung**: Jeder Aufruf von `/lessons` erzeugt einen 404 für `/static/images/Lesson_Background.png`.
- **Impact**: Gebrochenes Hintergrundbild auf der Lektionen-Seite.
- **Fix**: Datei bereitstellen oder Referenz entfernen.

---

## Sicherheits-Findings

### SEC-001: CSRF-Schutz funktioniert korrekt

- Login, Register und alle Formulare enthalten `csrf_token` als Hidden-Field.
- POST-Requests ohne CSRF-Token werden korrekt abgelehnt.
- **Status**: OK

### SEC-002: Admin-Zugriffskontrolle funktioniert

- Alle `/admin/*`-Routen und `/api/admin/*`-Endpoints blockieren Non-Admin-User.
- Redirect zu Login-Seite bei nicht authentifizierten Zugriffen.
- **Status**: OK

### SEC-003: Authentifizierungs-Enforcement funktioniert

- `/profile`, `/my-lessons`, `/purchase/*` leiten korrekt zur Login-Seite weiter.
- **Status**: OK

### SEC-004: Session-Management funktioniert

- Sessions bleiben über Seitennavigation hinweg bestehen.
- Logout zerstört die Session korrekt.
- **Status**: OK

### SEC-005: XSS-Prävention

- Login-Formular: Jinja2 Auto-Escaping verhindert Script-Injection.
- Register-Formular: HTML-Tags werden escaped.
- **Status**: OK

### SEC-006: Input-Validierung

- Duplicate Email/Username bei Registrierung wird korrekt abgelehnt.
- Passwort-Mismatch wird erkannt.
- Ungültige Email-Formate werden abgelehnt.
- **Status**: OK

---

## API-Findings

### API-001: Öffentliche APIs funktionieren

- `GET /api/categories` — Gibt korrektes JSON-Array mit Kategorien zurück.
- `GET /api/courses` — Gibt korrektes JSON-Array mit Kursen zurück.
- **Status**: OK

### API-002: Admin-APIs sind korrekt geschützt

Alle getesteten Admin-Endpoints geben für reguläre User einen 302-Redirect (zur Login-Seite) zurück:
- `/api/admin/kana`, `/api/admin/kanji`, `/api/admin/vocabulary`, `/api/admin/grammar`
- `/api/admin/lessons`, `/api/admin/categories`, `/api/admin/courses`
- `/api/admin/purchases`, `/api/admin/revenue-stats`
- **Status**: OK

### API-003: Admin-APIs funktionieren für Admins

- `GET /api/admin/lessons` — Gibt Lektionen-Liste zurück.
- `GET /api/admin/categories` — Gibt Kategorien zurück (3 Seed-Kategorien).
- `GET /api/admin/courses` — Gibt Kurse zurück.
- `GET /api/admin/purchases` — Gibt Kauf-Liste zurück.
- `GET /api/admin/revenue-stats` — Gibt Umsatzstatistiken zurück.
- `GET /api/admin/content-options/*` — Gibt Optionen für alle Content-Typen zurück.
- **Status**: OK

### API-004: User-APIs funktionieren

- `GET /api/lessons` — Gibt User-Lektionen zurück.
- `GET /api/user/purchases` — Gibt User-Käufe zurück.
- `GET /api/lessons/<id>/purchase-status` — Gibt Kaufstatus zurück.
- **Status**: OK

---

## Feature-Status

| Feature | Status | Anmerkungen |
|---------|--------|-------------|
| Homepage mit Sprachauswahl | OK | English/German Cards funktionieren |
| Benutzer-Registrierung | OK | Validierung funktioniert korrekt |
| Login/Logout | OK | Email/Password funktioniert |
| Google OAuth | Nicht testbar | Externe Abhängigkeit, Link ist vorhanden |
| Lektionen-Katalog | OK | Filter, Kategorien, Sprach-Filter |
| Freie Lektionen (Guest) | OK | Zugriff ohne Login möglich |
| Bezahlte Lektionen | OK | Redirect zu Purchase-Seite |
| Premium-Lektionen | BUG | Zugriffskontrolle hat Logik-Lücke (BUG-003) |
| Kurs-Übersicht | TIMEOUT | CDN-Abhängigkeit blockiert (BUG-004) |
| Kurs-Detailansicht | BUG | 500-Fehler ohne Auth (BUG-001) |
| Profil-Seite | OK | Zeigt User-Info und Stats |
| My Lessons | OK | Zeigt gekaufte Lektionen oder Empty-State |
| Purchase-Flow | OK | Seite lädt, Preis wird angezeigt |
| Payment Success/Failed | OK | Seiten laden korrekt |
| Admin-Dashboard | OK | Zugriff nur für Admins |
| Admin: Kana verwalten | OK | Seite lädt, API funktioniert |
| Admin: Kanji verwalten | OK | Seite lädt |
| Admin: Vocabulary verwalten | OK | Seite lädt |
| Admin: Grammar verwalten | OK | Seite lädt |
| Admin: Lessons verwalten | OK | Seite lädt, API CRUD funktioniert |
| Admin: Categories verwalten | OK | Seite lädt |
| Admin: Courses verwalten | OK | Seite lädt |
| Admin: Approval | OK | Seite lädt |
| Admin: Revenue Stats | OK | API gibt Daten zurück |
| Health Checks | OK | `/healthz` und `/health` antworten |
| 404-Handling | OK | Nicht-existente Seiten geben 404 |

---

## Empfehlungen (Priorisiert)

1. **BUG-001 fixen** (Kurs-Detailseite crasht ohne Auth) — Sofort beheben, betrifft alle Besucher.
2. **BUG-003 fixen** (Premium-Zugriffslücke) — Sicherheitsrelevant, Zugriffskontrolle umgehbar.
3. **BUG-006 fixen** (fehlende Lesson_Background.png) — Einfacher Fix.
4. **BUG-002** (difficulty_level Validierung) — Input-Validierung in Admin-API hinzufügen.
5. **BUG-004/005** (CDN-Timeouts) — Lokale Fallbacks für CSS/JS bereitstellen.
6. **Debug-Logging entfernen** — `__init__.py` gibt Umgebungsvariablen-Namen aus (Zeilen 39-61).
7. **`google.generativeai` deprecation** — Auf `google.genai` migrieren (FutureWarning in `ai_services.py`).

---

## Test-Infrastruktur

Die Playwright-Tests sind unter `tests/` angelegt:

| Datei | Tests | Bereich |
|-------|-------|---------|
| `01-public-routes.spec.js` | 18 | Öffentliche Seiten, Navigation, Health |
| `02-authentication.spec.js` | 15 | Login, Register, Logout, Profil |
| `03-lessons-courses.spec.js` | 18 | Lektionen, Kurse, Zugriff, Progress |
| `04-payment.spec.js` | 12 | Purchase, Payment API, Premium |
| `05-admin.spec.js` | 24 | Admin-Panel, CRUD-APIs, Revenue |
| `06-api-endpoints.spec.js` | 25 | Public/User/Admin APIs, Error Handling |
| `07-security.spec.js` | 23 | CSRF, Auth, XSS, Session, Validation |
| **Total** | **135** | |

**Ausführen**: `npx playwright test`
**Server**: `python tests/start_test_server.py` (automatisch via Playwright webServer config)
