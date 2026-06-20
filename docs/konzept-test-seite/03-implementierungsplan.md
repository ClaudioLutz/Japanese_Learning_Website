# 03 · Implementierungsplan `/pruefen`

_Konzept Test-/Prüfungsseite · Stand 2026-06-20 · für die festgelegte Variante
„integrierte Frage-Seite" (siehe [`01`](01-wireframes-und-flows.md) §1)_

## 1. Scope & Prinzipien (v1)

- **Keine Schema-Änderung.** Nur Lesen aus `QuizQuestion`/`QuizOption`/`UserQuizAnswer`.
- **Test ist risikofrei** — schreibt **nicht** in `UserQuizAnswer`/`UserLessonProgress`,
  berührt SRS nicht. (XP optional, siehe §8.)
- **Maximale Wiederverwendung** der Muster `/practice/kana` (Start→Session→Ergebnis,
  zwei Routen) und `/review` (Client-Loop, X/Y, gesperrte Bühne).
- **Server bewertet, Client peekt nicht** — der Fragen-Pool wird **ohne** Korrekt-Flags
  ausgeliefert; Korrektheit + Erklärung kommen aus einem Check-/Grade-Endpoint. Hält
  den Prüfungsmodus ehrlich und macht den vorhandenen Evaluator wiederverwendbar.
- **Zugriffskontrolle serverseitig** über `Lesson.is_accessible_to_user`
  (`models.py:793-865`); `fill_blank` immer ausgeschlossen.

## 2. Architektur-Überblick

```
 Browser                         Flask (neuer Blueprint pruefen_bp)
 ───────                         ─────────────────────────────────
 /pruefen          ───────────▶  GET  pruefen_start()      → pruefen.html (Start-Screen)
 /pruefen/test?... ───────────▶  GET  pruefen_session()    → pruefen_session.html (locked)
   │ Alpine pruefenGame()
   │  ① Pool laden     ────────▶  GET  /api/pruefen/pool    → Fragen ohne Korrekt-Flags
   │  ② Übung: je Antwort ─────▶  POST /api/pruefen/check   → {is_correct, explanation,…}
   │  ③ Prüfung: am Ende ──────▶  POST /api/pruefen/grade   → {score, sektionen, je Frage}
   └─ Ergebnis-Screen (inline, Score-Ring, „nur Falsche nochmal" rein clientseitig)

 Geteilt:  app/services/pruefen_service.py
            ├─ build_question_pool(user, scope, filters) → [QuizQuestion]
            └─ evaluate_answer(question, payload) → {is_correct, correct, total}
               (auch von routes.submit_quiz_answer genutzt → DRY)
```

## 3. Backend

### 3.1 Neuer Blueprint `pruefen_bp`
Neue Datei `app/pruefen_routes.py` (Muster: `app/srs_routes.py`). Registrieren in
`app/__init__.py` analog zu `srs_bp` (`__init__.py:273-274`), **ohne** `url_prefix`
(Routen tragen `/pruefen` selbst):
```python
from app.pruefen_routes import pruefen_bp
app.register_blueprint(pruefen_bp)
```
CSRF bleibt aktiv (kein `csrf.exempt`); die JSON-POSTs senden den CSRF-Token im Header
`X-CSRFToken` wie die Lektions-Quiz-Calls.

### 3.2 Service-Layer `app/services/pruefen_service.py`

**`build_question_pool(user, scope, filters) -> list[QuizQuestion]`**
- `scope`: `{kind: 'lesson'|'module'|'level'|'all', id?}`.
- Grob-Query in SQL, dann **in Python** pro Lesson `is_accessible_to_user(user)` filtern
  (Methode, kein SQL-Feld) und Ergebnis als `{lesson_id: accessible}`-Map cachen.
- Immer `question_type IN ('multiple_choice','true_false','matching')` (fill_blank raus).
- `filters`: `question_type[]`, `difficulty[min,max]`, `selection ∈ {all, wrong, unseen}`,
  `limit`, `shuffle`.
- **Beziehungskette:** `QuizQuestion.lesson_content_id → LessonContent.lesson_id →
  Lesson` (für Modul `Lesson.category_id` `:857`, für Level `Lesson.jlpt_level` Int=5
  `:714`).
- **Falsch-Filter (B1, Proxy):**
  ```python
  # selection == 'wrong'
  q = q.join(UserQuizAnswer, and_(UserQuizAnswer.question_id == QuizQuestion.id,
                                  UserQuizAnswer.user_id == user.id)) \
       .filter(or_(UserQuizAnswer.is_correct.is_(False), UserQuizAnswer.attempts > 1))
  ```
- **Ungesehen (B2):** `~exists()` auf UserQuizAnswer — **nur** innerhalb zugänglicher
  Lektionen (Premium-Leak vermeiden).

**`evaluate_answer(question, payload) -> dict`** — *reine* Funktion, keine DB-Writes:
| `question_type` | Eingabe | Logik | Rückgabe |
|---|---|---|---|
| multiple_choice / true_false | `selected_option_id` | `QuizOption.is_correct` | `{is_correct, correct:0/1, total:1, correct_option_id}` |
| matching | `pairs:[{prompt,answer}]` | gegen `{option_text: feedback}` (`routes.py:4159`) | `{is_correct(all), correct:n, total:m}` → **Teilpunkte** |

> **Refactor (rückwärtskompatibel):** Die Typ-Auswertung steckt heute inline in
> `submit_quiz_answer` (`routes.py:4116-4183`). Diese Logik in `evaluate_answer`
> herausziehen und **beide** Aufrufer (Lektion + `/pruefen`) darauf zeigen lassen. Die
> Lektion behält ihr UPSERT/XP/`show_solution`-Verhalten; nur die reine Bewertung wird
> geteilt. Bestehende Quiz-Tests decken den Refactor ab.

### 3.3 Endpoints (`pruefen_routes.py`)

| Route | Methode | Auth | Zweck |
|---|---|---|---|
| `/pruefen` | GET | offen (Gast-Teaser) | Start-Screen (`pruefen.html`) |
| `/pruefen/test` | GET | offen* | Gesperrte Session-Bühne (`pruefen_session.html`), liest Query-Params |
| `/api/pruefen/pool` | GET | login* | Fragen-Pool (ohne Korrekt-Flags), access-gefiltert |
| `/api/pruefen/check` | POST | login | Übung: eine Antwort → `is_correct`, `explanation`, `option_feedback`, `correct_option_id`/`correct_pairs` |
| `/api/pruefen/grade` | POST | login | Prüfung: Batch aller Antworten → Gesamt-Score (`points`-gewichtet), Sektions-/Typ-Aufschlüsselung, je-Frage-Korrektheit |

\* Gast: Start-Screen + ggf. 3 Demo-Fragen aus einer Gratis-Lektion ohne Speichern
(Entscheidung §8); voller Pool/Check ist login-pflichtig wie `/review`.

**Pool-Payload pro Frage** (kein Leak):
```json
{ "id": 123, "type": "multiple_choice", "question_text": "…",
  "difficulty": 2, "points": 1, "lesson": {"id":14,"title":"…"},
  "hint": "…",                      // nur wenn mode=uebung
  "options": [{"id":1,"text":"…"}], // KEIN is_correct
  "matching": {"prompts":["水",…], "answers":["みず",…]} } // answers gemischt, ohne Mapping
```

### 3.4 XP (optional, §8)
Falls gewünscht: analog `KanaStormScore`-Logik — Basis + min(correct, N), **UTC-Tages-
Cap**, Anti-Cheat-Clamp, **kein** `update_daily_aggregate`, kein FSRS-Effekt. Sonst gar
kein XP (reiner Selbsttest). Default-Empfehlung: zunächst **ohne** XP.

## 4. Frontend

### 4.1 Templates (Muster: `practice_kana.html` + `practice_kana_game.html`)
- `app/templates/pruefen.html` — **Start-Screen** (nicht gesperrt): Quick-Start-Kacheln
  + Modus-Toggle, Detail-Filter eingeklappt (`x-show`), Gast-Teaser. Erbt `base.html`.
- `app/templates/pruefen_session.html` — **gesperrte Bühne** (`body.pruefung-locked`),
  bindet die Alpine-Komponente, rendert Frage-Screen + Feedback + Ergebnis inline.

### 4.2 Alpine-Komponente `pruefenGame()` (`app/static/js/pruefen.js`)
Muster: `kanaGameView()` (`kana_grid_game.js:1007`) + Review-Loop. Zustände:
```
phase: 'loading' → 'question' → ('feedback' nur Übung) → 'result'
state: questions[], idx, answers[], sessionStats{correct,total,byType,byLesson},
       mode ('uebung'|'pruefung'), timerStart, wrongIds[]
Methoden: loadPool(), choose(optId)/togglePair(), check()/next(), finish()→grade(),
          retryWrong()  // baut Sub-Session nur aus wrongIds, rein clientseitig
```
- **„Weiter" tauscht `idx` in-place** — kein Reload, kein Routing pro Frage (Kern der
  festgelegten Variante).
- Übung: `check()` → POST `/api/pruefen/check`, Feedback-Panel in-place; `next()` weiter.
- Prüfung: `choose()`/`next()` ohne Feedback; `finish()` → POST `/api/pruefen/grade`.

### 4.3 Frage-Typen (Wireframes [`01`](01-wireframes-und-flows.md) §3–6)
- `multiple_choice`: Volle-Breite-Buttons, Tasten 1–4; Auswahl `--kon-300`, kein `--shu`.
- `true_false`: zwei große Buttons, Tasten R/F, farb-neutral bis Commit.
- `matching`: **Tap-to-pair** primär (Mobile+Desktop identisch), Drag nur Desktop-Zusatz,
  Paar-Badges ①②③. Client baut `pairs:[{prompt,answer}]` aus den Pool-`prompts/answers`.

### 4.4 CSS
- `body.pruefung-locked` **1:1** aus `body.review-locked` (overflow:hidden, Footer aus,
  `height:calc(100vh-60px)`). In `custom.css`, gescopt — Deck-Karussell-Invariante
  unberührt (kein Eingriff in `.content-item.in-deck`).
- Tokens & Dark-Mode-Fallen: Mapping in [`02`](02-inspiration-design-microcopy.md) §2
  (nur `var(--…)`, `--color-error` nicht `--danger`, `--shu` bleibt, gewählte Option
  Dark = `--kon-50`).

### 4.5 Ergebnis-Screen
- **Score-Ring** (SVG-Donut), Schwellen ≥80 % `--matcha` / 60–79 % `--kincha` / <60 %
  `--color-error`; `.session-summary`-Klassen wiederverwenden; Fehler-Liste mit
  `explanation`; CTA „🔁 Nur die N Falschen nochmal" (clientseitig `wrongIds`).
- Optionaler Modul-Donut über das schon geladene Chart.js (wie `stats.html`).

### 4.6 Nav-Eintrag (`base.html`)
Neuen Link „Prüfen ✓" rechts neben „Wiederholen" einfügen (Muster der bestehenden
Nav-Links, `aria-current` via `request.endpoint`), **ohne** Due-Badge.

## 5. Tests (Pflicht, `tests/`)

| Test | Prüft |
|---|---|
| `evaluate_answer` Unit | MC/true_false korrekt/falsch; matching all-correct **und** Teilpunkte (n/m); `fill_blank` → unsupported |
| Pool Access-Control | nicht zugängliche Lektionen liefern **keine** Fragen; `fill_blank` nie im Pool |
| Pool Falsch-Filter | nur Fragen mit `is_correct=False OR attempts>1` des Users |
| Pool kein Leak | Payload enthält **kein** `is_correct` / kein Mapping bei matching |
| `/api/pruefen/check` | korrekte Bewertung + `explanation` nur nach Antwort |
| `/api/pruefen/grade` | `points`-gewichteter Score, Sektions-/Typ-Aufschlüsselung |
| Auth/Gast | Pool/Check login-pflichtig; Start-Screen offen |
| Refactor-Regression | bestehende `submit_quiz_answer`-Tests bleiben grün |

`pytest` muss grün sein, `ruff check` sauber, `fail_under` nicht senken. Playwright-
Smoke (Start→Übung→Ergebnis, ein matching mobil) optional.

## 6. Reihenfolge / Aufwand (inkrementell)

1. **Service + Refactor** (`evaluate_answer` extrahieren, `build_question_pool` Rückgrat
   A1/A2/A3/A6) + Unit-Tests. *Größter Wert, kein UI.*
2. **Endpoints** `pool`/`check`/`grade` + CSRF + Access-Tests.
3. **Start-Screen** `pruefen.html` (Quick-Starts + Modus) + Nav-Eintrag.
4. **Session-Bühne** `pruefen_session.html` + `pruefen.js` (Loop, MC/true_false,
   Übung-Feedback, Ergebnis-Ring).
5. **matching** (Tap-to-pair) + Teilpunkte.
6. **Falsch-Filter B1** + Empty-States + „nur Falsche nochmal".
7. **Prüfungsmodus** (Timer, grade, Pass-Schwelle 60 %, Sektions-Aufschlüsselung).
8. Politur: Dark-Mode-Durchsicht, Mobile, a11y (aria-live Feedback, Fokus-Reihenfolge).

## 7. Risiken & Fallstricke

- **N+1 bei `is_accessible_to_user`** — pro Lesson eine Query. Lesson-Zugriff einmal pro
  Pool-Build batch-cachen (`{lesson_id: accessible}`).
- **CSRF** auf den POSTs — Header `X-CSRFToken` mitgeben (wie Lektions-Quiz), Blueprint
  **nicht** exempten.
- **matching-Semantik** — die korrekte Zuordnung steckt im `QuizOption.feedback`
  (`routes.py:4159`), nicht in `is_correct`. Evaluator + Pool müssen das respektieren.
- **Kein Lektions-Fortschritt verfälschen** — `/pruefen` schreibt nicht in
  `UserQuizAnswer` (sonst UPSERT überschreibt `answered_at`/`is_correct` der Lektion).
- **CSS-Invariante** — Eingriffe in `custom.css` gescopt halten; Deck-Karussell danach
  prüfen (Projektregel).
- **FREE_MODE** — aktuell sind alle Lektionen zugänglich → Bundle-Upsell/Locked-States
  erscheinen nicht; trotzdem über `is_accessible_to_user` bauen (reversibel).

## 8. Offene Entscheidungen (vor Start klären)

1. **XP im Test?** Empfehlung v1: nein. (Sonst Kana-Storm-Muster, UTC-Cap.)
2. **Gast-Demo** (3 Fragen ohne Login) ja/nein?
3. **Mock-Sektionen** (Moji-Goi/Bunpō/Dokkai via `content_type`) ab v1 oder gemischt
   starten?
4. **Route-/Label** final: `/pruefen` „Prüfen" (Empfehlung) bestätigen?

> Sind diese vier geklärt, ist Schritt 1–4 (§6) ein klar abgegrenzter erster
> Durchstich ohne Schema-Änderung.
