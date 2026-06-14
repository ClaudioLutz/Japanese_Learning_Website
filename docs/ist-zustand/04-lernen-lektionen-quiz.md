# 04 · Lernen: Lektionen, Inhalte & Quiz
_Stand: 2026-06-14 · Commit 2947710 · Teil der Ist-Zustand-Dokumentation_

## Zweck

Dieses Subsystem ist der Lern-Kern der Plattform: das Anzeigen einer einzelnen
Lektion (`/lessons/<id>` bzw. `/learn/n<level>/<slug>`), das Rendern aller
Inhaltstypen (Kana/Kanji/Vokabel/Grammatik als Flip-Cards, Text, Bild, Audio,
Video, Dialog-Slideshow, Kana-Grid-Spiel, Quiz), das interaktive Quiz-System
(Antwort absenden, Bewertung, XP), die Fortschritts-Verbuchung pro Content-Item
sowie das Klick-Vorlesen einzelner japanischer/deutscher Textstücke (TTS). Es
greift auf die Datenmodelle aus Doc 03 zu und stösst bei kostenpflichtigen
Lektionen die Paywall (Detail in Doc 07) an.

## Komponenten

| Datei | Zeilen | Rolle |
|---|---|---|
| `app/routes.py` | 4'863 | Alle Views + API-Endpoints (View-Lesson, Progress, Quiz-Answer, Reset, TTS). Mischt benutzersichtbare Routen und JSON-APIs in einer Datei. |
| `app/models.py` | 1'551 | Datenmodelle: `Lesson`, `LessonPage`, `LessonContent`, `QuizQuestion`, `QuizOption`, `UserQuizAnswer`, `UserLessonProgress` inkl. Fortschritts-Logik. |
| `app/templates/lesson_view.html` | 4'772 | Lektions-Viewer: Bootstrap-Carousel (Seiten), Flip-Cards, Quiz-UI, Deck-Karussell, Klick-TTS, sämtliche JS-Funktionen. |
| `app/templates/lesson_paywall.html` | — | Conversion-Seite bei nicht zugänglicher kostenpflichtiger Lektion (Bundle-CTA + Single-Kauf). |
| `app/templates/purchase.html` | — | Kaufseite einer einzelnen Lektion (Detail in Doc 07). |
| `app/content_validator.py` | 610 | KI-gestützte Qualitäts-/Kulturvalidierung von Lektionsinhalten (Offline-Tool, KEIN Typ-Schema; nutzt `ai_services`). |

## Lektions-Anzeige

### Routen

| Route | Funktion (`routes.py`) | Zugriff | Zweck |
|---|---|---|---|
| `/lessons/<int:lesson_id>` | `view_lesson` (`app/routes.py:1273`) | öffentlich (Gast erlaubt) | Rendert `lesson_view.html`. |
| `/learn/n<int:level>/<slug>` | `module_detail` (`app/routes.py:1049`) | öffentlich | Modul-Übersicht; bei nur 1 publizierter Lektion **302-Redirect (Flask-Default, kein `code=301`) direkt in die Lektion** (`app/routes.py:1070-1071`). |
| `/purchase/<int:lesson_id>` | `purchase_lesson_page` (`app/routes.py:1243`) | `@login_required` | Kaufseite (Detail Doc 07). |

`module_detail` ist eine Zwischenseite, die alle Lektionen eines Moduls mit
Zugriffsstatus, Fortschritt und Bundle-CTA listet. Der eigentliche Lern-Einstieg
ist `view_lesson`.

### Ladevorgang in `view_lesson` (`app/routes.py:1273-1386`)

1. `Lesson.query.get_or_404(lesson_id)`.
2. Zugriffsprüfung über `lesson.is_accessible_to_user(user)` — Gast = `current_user`
   nur wenn authentifiziert, sonst `None`.
3. **Paywall-Verzweigung** bei `not accessible` (`app/routes.py:1281-1322`):
   - Wenn `price > 0` **und** `is_purchasable` → `render_template('lesson_paywall.html', …)`
     mit Bundle-Preis (`get_n5_bundle_price`), Regular-/Early-Bird-Preis und Anzahl
     paid-Lektionen im Modul (`paid_total`; bei N5 inkl. anderer N5-Module).
   - Sonst, wenn nicht eingeloggt und Message `'Login required'` → Redirect auf
     `routes.login?next=…`.
   - Restfälle (z.B. Voraussetzungen) → `flash(message)` + Redirect auf `/lessons`.
4. Bei Zugriff: `UserLessonProgress` für (User, Lektion) wird geladen oder angelegt
   (race-sicher mit `IntegrityError`-Rollback, `app/routes.py:1331-1344`). Gäste
   bekommen keinen Progress-Datensatz.
5. Quiz-Fragen werden über alle interaktiven `content_items` eingesammelt
   (`app/routes.py:1346-1350`); bereits gegebene Antworten als Lookup
   `question_id -> UserQuizAnswer` (`app/routes.py:1352-1362`).
6. Internes Linking: vorherige/nächste Lektion im selben Modul (gleiche
   `instruction_language`, sortiert nach `order_index`, `id`) und Parent-Modul
   (`app/routes.py:1364-1380`).
7. `render_template('lesson_view.html', lesson, progress, form, user_quiz_answers, prev_lesson, next_lesson, parent_module)`.

### Zugriffsregeln — `Lesson.is_accessible_to_user` (`app/models.py:793-865`)

```
Gast (nicht eingeloggt):
    price == 0 UND allow_guest_access  → (True, "Als Gast zugänglich")
    sonst                              → (False, "Login required …")  ← Login-Redirect-Trigger
Admin (is_admin)                       → (True, "Admin")  ← Bypass, sieht alles
Eingeloggt, price == 0                 → Voraussetzungen prüfen → (True/False)
Eingeloggt, price > 0 + is_purchasable:
    LessonPurchase vorhanden?          → Voraussetzungen → (True, "Gekauft")
    Lektion in gekauftem Course?       → Voraussetzungen → (True, "Zugriff über …")
    sonst                              → (False, "Kauf erforderlich (CHF …)")
lesson_type == 'premium' ohne Abo      → (False, "Premium-Abo erforderlich")  ← Legacy
```

Voraussetzungen (`get_prerequisites`) blockieren den Zugriff, solange die
Vorgänger-Lektion nicht `is_completed` ist (Message: „Schliesse zuerst „…" ab").

### Seiten-Struktur (Pagination)

Eine Lektion ist in Seiten gegliedert. `Lesson.pages` (`app/models.py:867-892`)
gruppiert alle `LessonContent` nach `page_number` und reichert pro Seite die
Metadaten aus `LessonPage` an (`title`, `description`, `page_type`). Sortierung:
`(page_number, order_index)`. Im Template wird jede Seite als Bootstrap-Carousel-Item
gerendert (`#lessonCarousel`, `app/templates/lesson_view.html:973-976`). Navigation
per Carousel-Controls, Tastatur und URL-Hash; bei `totalPages > 1` wird die
JS-Navigation initialisiert (`lesson_view.html:2337-2350`).

Zwei Render-Pfade pro Seite:
- **Conversation-Page** (`page.metadata.title == 'Conversation'`,
  `lesson_view.html:986-1113`): MNN-Original-Layout — Audio-Block, Rich-Text mit
  „Als erledigt"-Button, Inline-Quiz.
- **Normal-Page** (`lesson_view.html:1115` ff.): Standard-Content-Loop mit
  Flip-Cards, Medien, Slideshow, Quiz.

### Karten-Render-Pfade (Jinja-Flip-Cards)

Für `content_type in ['kana','kanji','vocabulary','grammar']` wird eine Flip-Card
gerendert (`lesson_view.html:1331-1484`): `content.get_content_data()` lädt das
Referenz-Objekt; Vorderseite zeigt Zeichen/Wort/Titel (bei Vokabel optional den
Beispielsatz mit Hervorhebung), Rückseite die Details (Lesung, Bedeutung,
On-/Kun-Lesung, JLPT-Level, Beispiele, Nuance, Bild). Auf der Rückseite ein
`.card-audio-btn` mit `data-tts-text`/`data-tts-lang` (`lesson_view.html:1472-1480`).

Client-seitig werden gleichartige Flip-Cards einer Seite zu einem **Deck-Karussell**
(eine Karte nach der anderen, Confidence-Buttons, Tastatur 1-4) gebündelt:
`createDeck` (`lesson_view.html:3488` ff.) klont die Karten und versteckt die
Originale via `.content-item.in-deck`. (Projektregel: CSS-Syntaxfehler in
`custom.css` würde diese `display:none`-Regel kippen.)

Es existiert ein **zweiter, getrennter Kartenpfad** für die SRS-Wiederholung
(`review.html`, JS-basiert) — nicht Teil dieses Subsystems, siehe Memory
„Karten-Render-Pfade".

### Inhaltstypen

`LessonContent.content_type` ist ein `String(20)` (`app/models.py:962`), kein
DB-Enum. Welcher Typ wie gerendert wird, ergibt sich aus dem Template. Beobachtete
Werte:

| `content_type` | Render im `lesson_view.html` | Datenquelle |
|---|---|---|
| `kana` | Flip-Card (`:1340`), Vorderseite Zeichen, Rückseite Romaji/Typ/Mnemonic/Strichreihenfolge | `Kana` via `get_content_data` |
| `kanji` | Flip-Card (`:1342`), Rückseite Bedeutung/On-/Kun-Lesung/JLPT, optional Bild | `Kanji` |
| `vocabulary` | Flip-Card (`:1344`), Front optional Beispielsatz, Rückseite Wort/Lesung/Bedeutung/Beispiel, optional Bild | `Vocabulary` |
| `grammar` | Flip-Card (`:1361`), Titel/Struktur/Erklärung/Beispiele/Nuance | `Grammar`, `parsed_examples()` |
| `text` | Rich-Text-Block (`:1489`); `augmented_html` aus `ai_generation_details` falls vorhanden, sonst `content_text | markdown_safe`; optionaler Block-Audio-Player | `LessonContent.content_text` |
| `image` | `<img>` (`:1505`); bei `is_optional` rahmenloses Seitenbild ohne Fortschritts-Button (`:1120`) | `file_path`/`media_url` |
| `audio` | `<audio controls>` (`:1511`); ausgeblendet wenn auf derselben Seite ein `dialog_slideshow` liegt | `file_path`/`media_url` |
| `video` | `<iframe>` 16:9 mit `to_embed_url`-Filter (`:1581`) | `media_url` |
| `dialog_slideshow` | Alpine-Komponente `dialogSlideshow` (`:1523`); `content_text` ist JSON mit `slides` (Bild/Speaker/jp/romaji/de), Play/Auto-Advance, eigenes Audio | `content_text` (JSON) |
| `kana_grid_game` | Alpine-Komponente `kanaGridGame` (`:1165`), lädt Daten per API (interaktiv, zählt nicht über passiven Abschluss) | externe API |

Interaktive Items (`is_interactive == True`) rendern zusätzlich/stattdessen das
Quiz-Markup (`lesson_view.html:1593` ff.). `get_content_data` (`app/models.py:1036-1054`)
liefert für `kana/kanji/vocabulary/grammar` das ORM-Objekt, für
`text/image/video/audio` ein Dict (Titel, Text, Medien-URL, Datei-Infos).

## Quiz-System

### Modelle (`app/models.py`)

- `QuizQuestion` (`:1057`): `lesson_content_id`, `question_type` (String(50)),
  `question_text`, `explanation`, `hint`, `difficulty_level`, `points`,
  `order_index`. Beziehungen zu `options` und `user_answers` (cascade delete).
- `QuizOption` (`:1077`): `option_text`, `is_correct`, `order_index`, `feedback`
  (optionspezifisches Feedback; bei `matching` enthält `feedback` die korrekte
  Zuordnung zum `option_text`-Prompt).
- `UserQuizAnswer` (`:1089`): `user_id`, `question_id`, `selected_option_id`,
  `text_answer`, `is_correct`, `answered_at`, `attempts`; UNIQUE(user_id, question_id).

Aufeinanderfolgende Quiz-Items werden **client-seitig** zu einem Quiz-Karussell
gebündelt: ein `DOMContentLoaded`-Handler gruppiert ≥2 benachbarte interaktive
Content-Items (`lesson_view.html:4137-4153`); die Alpine-Komponente `quizCarousel`
(`lesson_view.html:4120`) steuert die Anzeige. (Das Feld `page_type == 'quiz_carousel'`
existiert nur auf dem `LessonPage`-Modell (`models.py:951`) für die Admin-UI und
steuert das Viewer-Rendering NICHT.)

### Antwort-Endpoint

`POST /api/lessons/<lesson_id>/quiz/<question_id>/answer` →
`submit_quiz_answer` (`app/routes.py:3931-4112`), `@login_required`.

Ablauf: CSRF-Header-Validierung → Frage muss zur Lektion gehören
(`question.content.lesson_id == lesson_id`) → Zugriffsprüfung → bestehende
`UserQuizAnswer` finden oder neu anlegen → **Max-Attempts-Prüfung** gegen
`content.max_attempts` (`app/routes.py:3977-3982`) → Bewertung je Typ.

Bewertung pro `question_type`:

| Typ | Bewertung (`routes.py`) |
|---|---|
| `multiple_choice` (`:3996`) | `selected_option.is_correct` |
| `true_false` (`:4021`) | `selected_option.is_correct` (gleiche Radio-Mechanik) |
| `matching` (`:4032`) | Vergleich `submitted_pairs` gegen `{option_text → feedback}`; korrekt nur wenn **alle** Paare stimmen; Antwort als JSON in `text_answer` |
| `fill_blank` (`:4012`) | Text gegen kommaseparierte Korrektantworten in `explanation`, case-insensitive |
| sonst | `400 Unsupported question type` |

**XP/Streak**: bei korrekter Antwort `xp_earned = question.points or 10` →
`current_user.total_xp += xp_earned` + `update_streak()` (`app/routes.py:4067-4072`).
Response enthält `is_correct`, `attempts_remaining`, `xp_earned`, `total_xp`,
`streak`. `option_feedback` wird immer mitgeschickt (Markdown→HTML), die volle
`explanation` (Lösung) nur wenn gelöst oder keine Versuche mehr
(`show_solution`, `app/routes.py:4082-4106`).

Client: `submitQuizAnswer(lessonId, questionId)` (`lesson_view.html:2103`).

**Hinweis zu erlaubten Typen:** Laut CLAUDE.md sind nur `multiple_choice`,
`true_false` und `matching` erlaubt — `fill_in_the_blank` wird nicht mehr
verwendet. Im Code existiert der `fill_blank`-Bewertungszweig dennoch noch
(`app/routes.py:4012-4019`), ebenso wird `fill_blank` in den Model-Kommentaren
(`app/models.py:1061`) und im KI-Generator-Proxy (`app/routes.py:4142-4143`,
`generate_fill_in_the_blank_question`) genannt. Im `lesson_view.html`-Render gibt
es nur Markup für `multiple_choice`, `true_false`, `matching`.

## Fortschritt

`UserLessonProgress` (`app/models.py:1105-1222`) speichert pro (User, Lektion):
`is_completed`, `progress_percentage`, `time_spent`, `last_accessed`,
`content_progress` (JSON-Text, Map `content_id(str) → True`).

### Berechnung

Zentrale Logik ist `update_progress_percentage` (`app/models.py:1177-1204`). Sie
zählt **nur** `progress_visible_content_items` (`app/models.py:769-791`):

```
visible = alle content_items
          OHNE audio-Items auf Seiten mit dialog_slideshow
          OHNE is_optional-Items (z.B. dekorative Seitenbilder)
percentage = int(completed_visible / total_visible * 100)   # Truncation, nicht round (models.py:1200)
total_visible == 0  → percentage = 100
percentage == 100 + nicht completed → is_completed = True, completed_at = now
```

Dieser Nenner-Fix ist dokumentiert: vor der Änderung zählte ein eigener
Raw-SQL-Pfad gegen **alle** `LessonContent`-Zeilen (inkl. optionaler
Seitenbilder), wodurch keine Lektion je 100 % erreichte
(`app/routes.py:3236-3243`).

### Endpoints

| Route | Funktion | Wirkung |
|---|---|---|
| `POST /api/lessons/<id>/progress` | `update_lesson_progress` (`app/routes.py:3191`) | CSRF (Header **oder** Form für `sendBeacon`). Bei `content_id` → `progress.mark_content_completed(id)`; addiert `time_spent`; `update_streak`. Delegiert die Prozent-Berechnung ans Modell. Response inkl. `streak`, `total_xp`. |
| `POST /api/lessons/<id>/complete-remaining` | `complete_remaining_passive` (`app/routes.py:3267`) | Markiert am Lektions-Ende alle sichtbaren **passiven** Items als erledigt (`mark_passive_items_completed`, `app/models.py:1145-1175`). Interaktive (`is_interactive`, `kana_grid_game`) bleiben ausgenommen. Sicherheitsnetz für Slideshow/standalone-Audio/Einzel-Flipcards. |
| `POST /api/lessons/<id>/reset` | `reset_lesson_progress_api` (`app/routes.py:3091`) | JSON-API. Löscht alle `UserQuizAnswer` der Lektion (Raw-SQL) und setzt den Progress zurück. |
| `POST /lessons/<id>/reset` | `reset_lesson_progress` (`app/routes.py:3317`) | Form-POST-Variante (CSRF via `CSRFTokenForm`), Flash + Redirect zurück in die Lektion. |

`mark_content_completed` (`app/models.py:1138`) und
`mark_passive_items_completed` rufen beide `update_progress_percentage` auf.
Letztere ruft auch bei `changed=False` neu durch — Self-Healing für
Altbestand-Zeilen mit altem Nenner-Bug (`app/models.py:1171-1174`).

`_get_or_create_lesson_progress` (`app/routes.py:3160-3188`) legt den
Progress-Datensatz race-sicher via `INSERT … ON CONFLICT DO NOTHING` an.

### Client-Auslöser

- `markContentComplete(contentId)` (`lesson_view.html:2237`) → `POST …/progress`,
  aktualisiert Button/Badge/Progress-Bar, ruft `showLessonComplete()` bei 100 %.
- `completeRemainingPassive()` (`lesson_view.html:2431`) → `POST …/complete-remaining`,
  ausgelöst am Lektions-Ende (`maybeCompleteForUser`, `lesson_view.html:2467`).
- Verlassen der Seite: `navigator.sendBeacon('/api/lessons/<id>/progress', …)` mit
  Zeitmessung (`lesson_view.html:2864`).
- Gäste sind von Progress-Calls ausgenommen (`isGuestUser`, `lesson_view.html:3335`).

## Audio (Klick-TTS)

`POST /api/tts` → `tts_synthesize` (`app/routes.py:176-302`), **CSRF-exempt**,
Rate-Limit `30 per minute`.

- Body: `{ text, lang: 'ja'|'de', model?: 'chirp'|'gemini', speed? }`.
- Server validiert Sprache: `lang=ja` muss japanische Zeichen enthalten, `lang=de`
  darf keine — verhindert Sprach-Mismatch (`app/routes.py:207-211`). Text max 500
  Zeichen.
- `model='gemini'` nur für `lang=ja` (sonst auf `chirp` zurückgestuft). Output:
  Gemini = WAV, Chirp/Neural2 = MP3. Caching unter
  `static/cache/tts/<md5>.{wav,mp3}` (Key inkl. lang+model+voice+speed+text).
- Fallback-Kette: Gemini-Fehler → Chirp; fehlender API-Key → `503 TTS nicht
  konfiguriert`.
- JP-Texte laufen vor der Synthese durch `_maybe_spell_out_kana_row` (Kana-Reihen-
  Pause-Heuristik).

Client: Klick auf Karten-`.card-audio-btn` (globaler Delegator,
`lesson_view.html:3467-3478`) → `playCardAudio` (`:4003`). Reihenfolge: zuerst
vorgerenderte Readout-Dateien (`readoutMap`/`kanjiReadoutMap`/`audioFileMap`,
JP+DE+Beispiel sequenziell), sonst Fallback live über `/api/tts`. Lektions-Absatz-
Klicks (`_playLive`, `:3127`) wählen `model='gemini'` für JP, `chirp` für DE.

Die zugrundeliegende **Audio-Pipeline** (Gemini 2.5 Pro TTS „Leda" für JP,
Neural2-G für DE, Block-Player-WAVs pro `LessonContent`, Quota 2'500 Calls/Tag,
`、`-Pause-Trennung) ist in CLAUDE.md dokumentiert (Abschnitt „Audio-Pipeline")
und nicht Teil dieser Analyse.

## Kaufeinstieg (kurz)

Ist eine kostenpflichtige, nicht zugängliche Lektion betroffen, rendert
`view_lesson` `lesson_paywall.html` (Bundle-CTA + Single-Kauf). Die separate
`/purchase/<id>`-Seite (`purchase.html`) ist `@login_required` und führt den
Kauf-Flow aus. Kauf-Initiierung (`POST /api/lessons/<id>/purchase`,
`app/routes.py:3465`) und Payment-Provider sind in Doc 07 beschrieben.

## Zusammenspiel

**Eingehend:**
- Navigation/Hub-Seiten (Doc 02/05): Startseite, `/lessons`-Dashboard,
  `/learn/n5`-Hub und `module_detail` verlinken auf `/lessons/<id>`.
- Auth (Doc 02): `view_lesson` leitet nicht eingeloggte Gäste bei „Login required"
  auf `routes.login?next=<aktuelle URL>`.
- Datenmodelle (Doc 03): `Lesson`, `LessonContent`, `Kana/Kanji/Vocabulary/Grammar`,
  Quiz- und Progress-Modelle.

**Ausgehend / Links & Redirects:**
- Paywall → `lesson_paywall.html` / `purchase.html` (Doc 07, Payment/Bundle).
- Prev/Next-Lektion + Parent-Modul (internes Linking, Doc 05).
- `module_detail` → 302 in Einzel-Lektion bei nur einer publizierten Lektion.

**API-Calls (vom Client aus `lesson_view.html`):**
- `/api/lessons/<id>/progress`, `/api/lessons/<id>/complete-remaining` →
  Fortschritt (mutiert auch `current_user.total_xp`/`current_streak`, koppelt an
  Gamification, Doc 05/06).
- `/api/lessons/<id>/quiz/<qid>/answer` → Quiz-Bewertung + XP.
- `/api/tts` → Klick-Audio (Google Cloud TTS / Gemini).
- `kana_grid_game` lädt seine Spieldaten über einen separaten API-Endpoint
  (Kana-/SRS-Subsystem).

## Beobachtungen (Ansatzpunkte)

- `app/routes.py` ist 4'863 Zeilen und vermischt benutzersichtbare Views,
  Admin-CRUD-APIs, Quiz-, Progress- und TTS-Endpoints in einer Datei.
- `lesson_view.html` ist 4'772 Zeilen (Markup + CSS + komplettes JS für Carousel,
  Deck, Quiz, TTS, Slideshow in einer Datei).
- Es existieren zwei nahezu identische Reset-Endpoints mit dupliziertem Raw-SQL:
  `reset_lesson_progress_api` (`app/routes.py:3091`, JSON) und
  `reset_lesson_progress` (`app/routes.py:3317`, Form). Beide enthalten denselben
  DELETE/UPDATE-Block; `UserLessonProgress.reset()` (`app/models.py:1206`) ist eine
  dritte, ungenutzte Reset-Implementierung.
- `fill_blank` ist laut CLAUDE.md nicht mehr erlaubt, aber im Code mehrfach präsent:
  Bewertungszweig in `submit_quiz_answer` (`app/routes.py:4012`), Model-Kommentar
  (`app/models.py:1061`) und KI-Generator-Proxy (`app/routes.py:4142`). Das Render-
  Template kennt diesen Typ nicht.
- `content_type` ist ein freier `String(20)` ohne DB-Enum/Validierung; die Menge
  gültiger Werte ist nur implizit über das Template definiert.
- Es gibt zwei getrennte Quiz-Render-Pfade im selben Template (Conversation-Page
  ab `:1027` und Normal-Page ab `:1593`) mit teils dupliziertem Markup.
- Zwei separate Audio-Mechanismen koexistieren: vorgerenderte MP3-Readout-Dateien
  (`readoutMap`/`audioFileMap`) und Live-`/api/tts`-Synthese — die Auswahl erfolgt
  client-seitig in `playCardAudio`.
- `time_spent` wird client-seitig als Differenz `(Date.now() - startTime)` in
  Minuten berechnet und additiv verbucht (`lesson_view.html:2259`); keine
  serverseitige Plausibilitätsprüfung.
- `/api/tts` ist bewusst CSRF-exempt (`@csrf.exempt`) und nur per Rate-Limit
  (30/min) geschützt; bei fehlendem API-Key liefert es `503`.
- `is_accessible_to_user` führt pro Voraussetzung und pro Course einzelne
  `UserLessonProgress`-/`CoursePurchase`-Queries aus (potenzielles N+1 bei vielen
  Voraussetzungen/Kursen).
