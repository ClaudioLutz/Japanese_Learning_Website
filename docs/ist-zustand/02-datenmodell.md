# 02 · Datenmodell
_Stand: 2026-06-14 · Commit 2947710 · Teil der Ist-Zustand-Dokumentation_

## Zweck

Dieses Subsystem ist das vollständige SQLAlchemy-Datenmodell der Plattform und liegt komplett in einer einzigen Datei (`app/models.py`, 1'551 Zeilen). Es definiert 25 Model-Klassen, eine Assoziationstabelle (`course_lessons`) und einen Event-Listener. Abgedeckt sind: Benutzer + Gamification (User), japanische Referenzdaten (Kana/Kanji/Vocabulary/Grammar), Lektions-/Kursstruktur (Lesson/Course/LessonPage/LessonContent), Quiz, Fortschritts-Tracking, das FSRS-Spaced-Repetition-System (CardReviewState/ReviewLog u.a.), das Kana-Grid-Spiel sowie Zahlungs-Tracking. Neben reinen Schemafeldern enthält die Datei umfangreiche Geschäftslogik (Zugriffskontrolle, Streak-Berechnung, Cloze-Erzeugung, Romaji-Parsing).

## Komponenten

| Datei | Zeilen | Rolle |
|---|---|---|
| `app/models.py` | 1'551 | Einzige Datei dieses Subsystems. Alle ORM-Models, Assoziationstabelle, `load_user`-Callback, Modul-Hilfsfunktionen (Romaji/Cloze-Parsing), Lesson-Event-Listener. |

Innerhalb der Datei lassen sich grob diese Blöcke unterscheiden:

| Block | Zeilen | Inhalt |
|---|---|---|
| Auth + Gamification | `app/models.py:11`–`134` | `User` |
| Referenzdaten | `app/models.py:136`–`657` | `Kana`, `Kanji`, `Vocabulary`, `Grammar` + Romaji-/Cloze-Hilfsfunktionen |
| Lektions-/Kursstruktur | `app/models.py:659`–`1055` | `LessonCategory`, `Lesson`, `LessonPrerequisite`, `LessonPage`, `LessonContent` |
| Quiz + Fortschritt | `app/models.py:1057`–`1222` | `QuizQuestion`, `QuizOption`, `UserQuizAnswer`, `UserLessonProgress` |
| Käufe + Kurse | `app/models.py:1224`–`1286` | `LessonPurchase`, `course_lessons`, `Course`, `CoursePurchase` |
| SRS + Gamification-Detail | `app/models.py:1289`–`1514` | `CardReviewState`, `ReviewLog`, `KanaConfusion`, `UserSRSSettings`, `UserAchievement`, `DailyReviewAggregate`, `KanaGridConfig` |
| Zahlung | `app/models.py:1517`–`1534` | `PaymentTransaction` |
| Event-Listener | `app/models.py:1538`–`1551` | automatische `lesson_type`-Konsistenz |

Hinweis zur Schreibweise: Ältere Modelle nutzen den klassischen `db.Column`-Stil mit `__allow_unmapped__ = True`; neuere (`User`, `Lesson`, `LessonPrerequisite`, `LessonPurchase`, `Course`, `CoursePurchase`, `PaymentTransaction`, teilw. `UserLessonProgress`) nutzen den typisierten `Mapped[...] / mapped_column(...)`-Stil. Beide koexistieren in derselben Datei.

---

## Modelle im Detail

### User — `app/models.py:11`
Erbt von `UserMixin` (Flask-Login). Auth, Subscription, Streak und Gamification in einer Tabelle.

| Feld | Typ | Constraints/Default | Bedeutung |
|---|---|---|---|
| id | Integer | PK | |
| username | String(80) | **unique**, not null | Anmeldename |
| email | String(120) | **unique**, not null | E-Mail |
| password_hash | String(256) | not null | Werkzeug-Hash |
| subscription_level | String(50) | default `'free'` | `free` / `premium` |
| is_admin | Boolean | default False, not null | Admin-Flag |
| failed_login_count | Integer | default 0, server_default `'0'` | Lockout-Zähler |
| locked_until | DateTime | nullable | Sperre bis (UTC) |
| current_streak | Integer | default 0, not null | aktueller Tages-Streak |
| longest_streak | Integer | default 0, not null | längster Streak |
| last_activity_date | Date | nullable | letzter Aktivitätstag |
| total_xp | Integer | default 0, not null | Erfahrungspunkte |
| level | Integer | default 1, not null | Level |
| total_reviews | Integer | default 0, not null | Anzahl SRS-Reviews |
| total_mastered | Integer | default 0, not null | gemeisterte Karten |
| push_subscription | **JSON** | nullable | Web-Push-Subscription (opt-in) |

Beziehungen (alle ausgehend von User, 1:n sofern nicht anders vermerkt):
- `lesson_progress` → `UserLessonProgress` (backref `user`, cascade delete-orphan)
- `course_purchases` → `CoursePurchase` (backref `user`, cascade delete-orphan)
- `lesson_purchases` → `LessonPurchase` (backref via `LessonPurchase.user`)
- `card_states` → `CardReviewState` (lazy='dynamic')
- `review_logs` → `ReviewLog` (lazy='dynamic')
- `achievements` → `UserAchievement` (lazy='dynamic')
- `daily_aggregates` → `DailyReviewAggregate` (lazy='dynamic')
- `srs_settings` → `UserSRSSettings` (**1:1**, `uselist=False`)

Konstanten: `LOCKOUT_THRESHOLD = 5`, `LOCKOUT_DURATION_MINUTES = 15` (`app/models.py:40`).

Wichtige Properties/Methoden:
- `is_locked` (`:46`) — True, wenn `locked_until` in der Zukunft liegt (UTC-Vergleich).
- `record_failed_login()` / `record_successful_login()` (`:52`/`:58`) — Zähler hochsetzen bzw. zurücksetzen; bei Erfolg wird `update_streak()` gerufen.
- `update_streak()` (`:63`) — Tagesgrenze in **Europe/Zurich** (nicht UTC). Logik: heute schon aktiv → nichts; gestern aktiv → Streak +1; vorgestern aktiv + gestern verpasst + Freeze verfügbar → Freeze verbraucht, Streak bleibt; sonst Reset auf 1. Streak-Freeze wird wöchentlich via `srs_settings` aufgefüllt.
- `add_xp(amount)` (`:98`) — addiert XP, Level-Up solange `total_xp >= xp_for_next_level`.
- `xp_for_next_level` (`:104`) — `int(100 * level**1.5)` (polynomiale Kurve).
- `level_title` (`:109`) — japanisch-thematischer Titel je Levelbereich (z.B. „Anfänger (初心者)" bis „Grossmeister (名人)").
- `set_password()` / `check_password()` (`:127`/`:130`) — Hashing.

### Kana — `app/models.py:136`
Hiragana/Katakana-Referenzdaten.

| Feld | Typ | Constraints/Default | Bedeutung |
|---|---|---|---|
| id | Integer | PK | |
| character | String(5) | **unique**, not null | Kana-Zeichen |
| romanization | String(10) | not null | Romaji |
| type | String(10) | not null | `'hiragana'` / `'katakana'` |
| stroke_order_info | String(255) | nullable | Strichfolge-Info |
| example_sound_url | String(255) | nullable | Audio-URL |
| mnemonic | Text | nullable | Merkhilfe |

Wird per `KanaConfusion`, `KanaGridConfig.kana_ids` (JSON-IDs) und `LessonContent.content_id` referenziert.

### Kanji — `app/models.py:152`

| Feld | Typ | Constraints/Default | Bedeutung |
|---|---|---|---|
| id | Integer | PK | |
| character | String(5) | **unique**, not null | Kanji |
| meaning | Text | not null | Bedeutung |
| onyomi | String(100) | nullable | On-Lesung |
| kunyomi | String(100) | nullable | Kun-Lesung |
| jlpt_level | Integer | nullable | JLPT-Stufe |
| stroke_order_info | String(255) | nullable | Strichfolge |
| radical | String(10) | nullable | Radikal |
| stroke_count | Integer | nullable | Strichzahl |
| image_url | String(500) | nullable | Bild-URL |
| status | String(20) | default `'approved'`, not null | `approved` / `pending_approval` |
| created_by_ai | Boolean | default False, not null | KI-Generierungs-Flag |

### Vocabulary — `app/models.py:173`

| Feld | Typ | Constraints/Default | Bedeutung |
|---|---|---|---|
| id | Integer | PK | |
| word | String(100) | **unique**, not null | Vokabel |
| reading | String(100) | not null | Lesung |
| romaji | String(200) | nullable | Romaji |
| meaning | Text | not null | Bedeutung (legacy/englisch) |
| meaning_de | Text | nullable | deutsche Bedeutung |
| jlpt_level | Integer | nullable | JLPT-Stufe |
| example_sentence_japanese | Text | nullable | Beispielsatz JP |
| example_sentence_english | Text | nullable | Format „Romaji — Übersetzung" |
| audio_url | String(255) | nullable | Audio-URL |
| image_url | String(500) | nullable | Bild-URL |
| status | String(20) | default `'approved'`, not null | Approval-Status |
| created_by_ai | Boolean | default False, not null | KI-Flag |

Methoden/Properties:
- `_split_example_translation()` (`:199`) — zerlegt `example_sentence_english` an `—`/`–`/`-` in (Romaji, Übersetzung).
- `example_sentence_romaji` / `example_sentence_translation` (`:217`/`:221`) — die beiden Teile als Properties.

### Grammar — `app/models.py:594`

| Feld | Typ | Constraints/Default | Bedeutung |
|---|---|---|---|
| id | Integer | PK | |
| title | String(200) | **unique**, not null | Grammatik-Titel |
| explanation | Text | not null | Erklärung |
| structure | Text | nullable | Strukturmuster (Quelle der Cloze-Marker) |
| romaji | String(500) | nullable | Romaji |
| jlpt_level | Integer | nullable | JLPT-Stufe |
| example_sentences | Text | nullable | Beispiele (JSON-Liste **oder** nummerierter Plaintext) |
| tts_example_jp | Text | nullable | genau EIN rein-japanischer Satz für den Audio-Button |
| status | String(20) | default `'approved'`, not null | Approval-Status |
| created_by_ai | Boolean | default False, not null | KI-Flag |
| nuance | Text | nullable | didaktische Notiz (Nuance/Formalität) |

Methoden/Properties:
- `parsed_examples()` (`:639`) — normalisiert `example_sentences` über die Modulfunktion `parse_example_sentences()` zu `[{japanese, romaji, translation}]`.
- `cloze()` (`:645`) — erzeugt via `make_grammar_cloze()` eine Lückentext-Karte (Marker aus `structure` im ersten passenden Beispiel ausgeblendet); `None`, wenn kein Marker passt.
- `_extract_tts_example_parts()` (`:620`) + `tts_example_romaji` / `tts_example_translation` (`:651`/`:655`) — Romaji+Übersetzung zum TTS-Satz aus den geparsten Beispielen ziehen.

**Modul-Hilfsfunktionen rund um Grammar/Vocabulary** (kein eigenes Model, aber zentrale Logik in `app/models.py`):
- `parse_example_sentences()` (`:235`) — versteht JSON-Liste und nummerierten Plaintext.
- `_romanize_kana()`, `_expand_macrons()`, `_answer_romaji_candidates()`, `_mask_romaji()`, `_pyk_romaji()` (optional pykakasi), `_romaji_with_gap()` (`:364`–`534`) — Romaji-Umschrift + spoilerfreie Lücken-Maskierung für Cloze.
- `make_grammar_cloze()` (`:537`) — die eigentliche Cloze-Erzeugung.

### LessonCategory — `app/models.py:659`
Kategorie = Modul innerhalb eines JLPT-Levels (Lernpfad).

| Feld | Typ | Constraints/Default | Bedeutung |
|---|---|---|---|
| id | Integer | PK | |
| name | String(100) | **unique**, not null | Modulname |
| description | Text | nullable | Beschreibung |
| color_code | String(7) | default `'#007bff'` | UI-Farbe |
| created_at | DateTime | default utcnow | |
| slug | String(80) | **unique**, nullable | z.B. `'n5-hiragana'` |
| jlpt_level | Integer | nullable | 5/4/3/2/1 |
| display_order | Integer | default 0, not null | Reihenfolge im Level |
| icon_emoji | String(8) | nullable | Icon |
| prerequisite_category_id | Integer | **FK → lesson_category.id**, nullable | Voraussetzungs-Modul (Self-Reference) |

Beziehungen:
- `lessons` → `Lesson` (backref `category`, **1:n**).
- `prerequisite` → `LessonCategory` (Self-Reference via `remote_side=[id]`, **1:1** auf Vorgänger).

Methoden:
- `completion_for_user(user, languages=None)` (`:689`) — `(abgeschlossene, gesamt-veröffentlichte)` Lessons; optional gefiltert nach `instruction_language`.
- `is_unlocked_for_user(user, threshold=0.8)` (`:710`) — Modul freigeschaltet, wenn Vorgänger-Modul ≥ 80% complete; ohne Voraussetzung oder für anonyme User immer freigeschaltet.

### Lesson — `app/models.py:723`
Zentrale Lerneinheit. Typisierter `Mapped`-Stil.

| Feld | Typ | Constraints/Default | Bedeutung |
|---|---|---|---|
| id | Integer | PK | |
| title | String(200) | not null | Titel |
| description | Text | nullable | Beschreibung |
| lesson_type | String(20) | not null | wird per Event aus `price` gesetzt (`free`/`paid`) |
| category_id | Integer | **FK → lesson_category.id**, nullable | Kategorie/Modul |
| difficulty_level | Integer | nullable | Schwierigkeit |
| estimated_duration | Integer | nullable | Minuten |
| order_index | Integer | default 0 | Reihenfolge |
| is_published | Boolean | default False | veröffentlicht |
| allow_guest_access | Boolean | default False, not null | Gastzugriff |
| instruction_language | String(10) | default `'english'`, not null | Sprache (`german`/`english`) |
| show_romaji_on_front | Boolean | default True, server_default true | Romaji auf Kartenvorderseite |
| thumbnail_url | String(255) | nullable | Vorschaubild |
| background_image_url | String(1000) | nullable | Hintergrundbild-URL |
| background_image_path | String(500) | nullable | Hintergrundbild-Pfad |
| video_intro_url | String(255) | nullable | Intro-Video |
| created_at / updated_at | DateTime | default utcnow / onupdate | |
| price | Float | not null, default 0.0 | Preis CHF |
| is_purchasable | Boolean | not null, default False | kaufbar |

Beziehungen:
- `content_items` → `LessonContent` (backref `lesson`, **1:n**, cascade delete-orphan)
- `prerequisites` → `LessonPrerequisite` (über `lesson_id`, backref `lesson`, cascade)
- `required_by` → `LessonPrerequisite` (über `prerequisite_lesson_id`)
- `user_progress` → `UserLessonProgress` (**1:n**, cascade)
- `pages_metadata` → `LessonPage` (backref `lesson`, **1:n**, cascade)
- `courses` → `Course` (**n:m** via `course_lessons`, `back_populates='courses'`)
- backref `purchases` → `LessonPurchase`

Wichtige Properties/Methoden:
- `get_prerequisites()` (`:765`) — Liste der Voraussetzungs-Lessons.
- `progress_visible_content_items` (`:769`) — Content-Items, die fortschrittsrelevant sind: blendet `audio`-Items auf Slideshow-Pages aus und ignoriert `is_optional`-Items. **Zentral** für die Fortschritts-Prozentberechnung.
- `is_accessible_to_user(user)` (`:793`) — die Kern-Zugriffslogik (Gibt `(bool, Meldung)` zurück): Gast (nur gratis + `allow_guest_access`) → Admin-Bypass → kostenlos (nur Voraussetzungen) → kaufbar (eigener Kauf oder Kauf über Kurs) → Legacy-Premium-Abo → Voraussetzungen. Meldungen grösstenteils auf Deutsch (Login-Trigger bewusst englisch).
- `pages` (`:867`) — gruppiert Content-Items nach `page_number` (+ `LessonPage`-Metadaten), sortiert nach `(page_number, order_index)`.
- `get_background_url()` / `get_thumbnail_url()` (`:894`/`:913`) — URL-Auflösung mit GCS-Fallback (nur wenn `GCS_BUCKET_NAME` gesetzt; sonst lokale `routes.uploaded_file`-Route).

### LessonPrerequisite — `app/models.py:932`
Voraussetzungs-Verknüpfung zwischen zwei Lessons (Self-Referencing n:m über zwei FKs).

| Feld | Typ | Constraints/Default | Bedeutung |
|---|---|---|---|
| id | Integer | PK | |
| lesson_id | Integer | **FK → lesson.id**, not null | abhängige Lektion |
| prerequisite_lesson_id | Integer | **FK → lesson.id**, not null | Voraussetzungs-Lektion |

`__table_args__`: **UniqueConstraint(lesson_id, prerequisite_lesson_id)**. Beziehung `prerequisite_lesson` → `Lesson` (overlaps `required_by`).

### LessonPage — `app/models.py:944`
Seiten-Metadaten innerhalb einer Lektion.

| Feld | Typ | Constraints/Default | Bedeutung |
|---|---|---|---|
| id | Integer | PK | |
| lesson_id | Integer | **FK → lesson.id**, not null | zugehörige Lektion |
| page_number | Integer | not null | Seitennummer |
| title | String(200) | nullable | Seitentitel |
| description | Text | nullable | Beschreibung |
| page_type | String(20) | default `'normal'`, not null | `normal` / `quiz_carousel` |

`__table_args__`: **UniqueConstraint(lesson_id, page_number)**.

### LessonContent — `app/models.py:958`
Einzelnes Inhalts-Item einer Lektion (Referenz auf Kana/Kanji/Vocab/Grammar **oder** eigenständiger Text/Medien/Quiz-Inhalt).

| Feld | Typ | Constraints/Default | Bedeutung |
|---|---|---|---|
| id | Integer | PK | |
| lesson_id | Integer | **FK → lesson.id**, not null | Lektion |
| content_type | String(20) | not null | `kana`/`kanji`/`vocabulary`/`grammar`/`text`/`image`/`video`/`audio` (auch `dialog_slideshow`, `kana_grid_game` in Code referenziert) |
| content_id | Integer | nullable | FK-artige Referenz (kein DB-FK!) auf Kana/Kanji/Vocabulary/Grammar je nach `content_type`; NULL bei Multimedia |
| title | String(200) | nullable | Titel (Multimedia) |
| content_text | Text | nullable | Textinhalt |
| media_url | String(255) | nullable | Medien-URL |
| order_index | Integer | default 0 | Reihenfolge in der Lektion |
| page_number | Integer | default 1, not null | Seite |
| is_optional | Boolean | default False | optional (zählt nicht zum Fortschritt) |
| created_at | DateTime | default utcnow | |
| file_path | String(500) | nullable | rel. Pfad zur Upload-Datei |
| file_size | Integer | nullable | Bytes |
| file_type | String(50) | nullable | MIME |
| original_filename | String(255) | nullable | Originalname |
| is_interactive | Boolean | default False | interaktiv (Quiz) |
| quiz_type | String(50) | default `'standard'` | `standard` / `adaptive` |
| max_attempts | Integer | default 3 | Versuche |
| passing_score | Integer | default 70 | Bestehensgrenze (%) |
| generated_by_ai | Boolean | default False, not null | KI-Flag |
| ai_generation_details | **JSON** | nullable | KI-Generierungsdetails |

Beziehungen:
- `quiz_questions` → `QuizQuestion` (backref `content`, **1:n**, cascade)
- `review_states` → `CardReviewState` (backref, lazy='dynamic')
- `kana_grid_config` → `KanaGridConfig` (**1:1**, `uselist=False`, cascade delete-orphan)
- (passiv) referenziert von `ReviewLog`

Methoden:
- `get_file_url()` (`:997`) — URL für hochgeladene Datei (http-Passthrough, GCS-URL oder lokale `routes.uploaded_file`-Route, sonst `media_url`).
- `delete_file()` (`:1021`) — entfernt die zugehörige Datei vom Dateisystem.
- `get_content_data()` (`:1036`) — lädt je nach `content_type` das referenzierte Model (`Kana/Kanji/Vocabulary/Grammar` via `content_id`) oder gibt bei Multimedia ein Dict zurück. **Hinweis:** `content_id` ist KEIN echter DB-FK, sondern eine typabhängige manuelle Referenz.

### QuizQuestion — `app/models.py:1057`

| Feld | Typ | Constraints/Default | Bedeutung |
|---|---|---|---|
| id | Integer | PK | |
| lesson_content_id | Integer | **FK → lesson_content.id**, not null | zugehöriges Content-Item |
| question_type | String(50) | not null | `multiple_choice`/`fill_blank`/`true_false`/`matching` (laut CLAUDE.md ist `fill_in_the_blank` deprecated) |
| question_text | Text | not null | Frage |
| explanation | Text | nullable | Erklärung der Antwort |
| hint | Text | nullable | progressiver Hinweis |
| difficulty_level | Integer | default 1 | 1–5 (adaptive) |
| points | Integer | default 1 | Punkte |
| order_index | Integer | default 0 | Reihenfolge |
| created_at | DateTime | default utcnow | |

Beziehungen: `options` → `QuizOption` (backref `question`, **1:n**, cascade); `user_answers` → `UserQuizAnswer` (backref `question`, **1:n**, cascade).

### QuizOption — `app/models.py:1077`

| Feld | Typ | Constraints/Default | Bedeutung |
|---|---|---|---|
| id | Integer | PK | |
| question_id | Integer | **FK → quiz_question.id**, not null | Frage |
| option_text | Text | not null | Antworttext |
| is_correct | Boolean | default False | korrekt |
| order_index | Integer | default 0 | Reihenfolge |
| feedback | Text | nullable | optionsspezifisches Feedback |

### UserQuizAnswer — `app/models.py:1089`

| Feld | Typ | Constraints/Default | Bedeutung |
|---|---|---|---|
| id | Integer | PK | |
| user_id | Integer | **FK → user.id**, not null | User |
| question_id | Integer | **FK → quiz_question.id**, not null | Frage |
| selected_option_id | Integer | **FK → quiz_option.id**, nullable | gewählte Option |
| text_answer | Text | nullable | Freitext-Antwort |
| is_correct | Boolean | default False | korrekt |
| answered_at | DateTime | default utcnow, onupdate | |
| attempts | Integer | default 0, not null | Versuche |

`__table_args__`: **UniqueConstraint(user_id, question_id)** — eine Antwort pro User+Frage.

### UserLessonProgress — `app/models.py:1105`
Fortschritt pro User+Lektion. Speichert Detail-Fortschritt als JSON-Text.

| Feld | Typ | Constraints/Default | Bedeutung |
|---|---|---|---|
| id | Integer | PK | |
| user_id | Integer | **FK → user.id**, not null | User |
| lesson_id | Integer | **FK → lesson.id**, not null | Lektion |
| started_at | DateTime | default utcnow | |
| completed_at | DateTime | nullable | |
| is_completed | Boolean | default False | abgeschlossen |
| progress_percentage | Integer | default 0 | Fortschritt % |
| time_spent | Integer | default 0 | Sekunden |
| last_accessed | DateTime | default utcnow | |
| content_progress | Text | nullable | **JSON-Text** `{content_id: bool}` |

`__table_args__`: **UniqueConstraint(user_id, lesson_id)**. Beziehung `lesson` → `Lesson` (overlaps `user_progress`); backref `user` von User.

Methoden:
- `get_content_progress()` / `set_content_progress(dict)` (`:1128`/`:1134`) — JSON-(De)Serialisierung des `content_progress`.
- `mark_content_completed(content_id)` (`:1138`) — markiert ein Item erledigt + Neuberechnung.
- `mark_passive_items_completed()` (`:1145`) — Sicherheitsnetz am Lektionsende: markiert alle sichtbaren NICHT-interaktiven Items als erledigt (ausgenommen `is_interactive` und `kana_grid_game`); ruft danach immer `update_progress_percentage()` (Self-Healing für Altbestand).
- `update_progress_percentage()` (`:1177`) — berechnet % nur über `lesson.progress_visible_content_items`; bei 0 sichtbaren Items → 100%; setzt `is_completed`+`completed_at` bei 100%.
- `reset()` (`:1206`) — setzt Fortschritt zurück und löscht alle zugehörigen `UserQuizAnswer` des Users für interaktive Inhalte dieser Lektion.

### LessonPurchase — `app/models.py:1224`

| Feld | Typ | Constraints/Default | Bedeutung |
|---|---|---|---|
| id | Integer | PK | |
| user_id | Integer | **FK → user.id**, not null | Käufer |
| lesson_id | Integer | **FK → lesson.id (ondelete RESTRICT)**, not null | Lektion (Löschen geblockt) |
| price_paid | Float | not null | gezahlter Preis |
| purchased_at | DateTime | default utcnow | |
| provider_transaction_id | BigInteger | nullable, **index** | Zahlungs-Transaktions-ID |
| transaction_state | String(50) | nullable | Status |

`__table_args__`: **UniqueConstraint(user_id, lesson_id)**. Beziehungen: `user` → `User` (backref `lesson_purchases`); `lesson` → `Lesson` (backref `purchases`). ORM-Cascade bewusst entfernt, da DB-FK = RESTRICT.

### course_lessons (Assoziationstabelle) — `app/models.py:1247`
n:m zwischen `Course` und `Lesson`. Spalten: `course_id` (FK → course.id, PK), `lesson_id` (FK → lesson.id, PK).

### Course — `app/models.py:1252`

| Feld | Typ | Constraints/Default | Bedeutung |
|---|---|---|---|
| id | Integer | PK | |
| title | String(200) | not null | Titel |
| description | Text | nullable | Beschreibung |
| background_image_url | String(255) | nullable | Hintergrundbild |
| is_published | Boolean | default False | veröffentlicht |
| created_at / updated_at | DateTime | default utcnow / onupdate | |
| price | Float | not null, default 0.0 | Preis CHF |
| is_purchasable | Boolean | not null, default False | kaufbar |

Beziehung: `lessons` → `Lesson` (**n:m** via `course_lessons`, lazy='subquery', `back_populates='courses'`); backref `purchases` → `CoursePurchase`.

### CoursePurchase — `app/models.py:1271`

| Feld | Typ | Constraints/Default | Bedeutung |
|---|---|---|---|
| id | Integer | PK | |
| user_id | Integer | **FK → user.id**, not null | Käufer |
| course_id | Integer | **FK → course.id (ondelete RESTRICT)**, not null | Kurs |
| price_paid | Float | not null | gezahlter Preis |
| purchased_at | DateTime | default utcnow | |
| provider_transaction_id | BigInteger | nullable, **index** | Transaktions-ID |
| transaction_state | String(50) | nullable | Status |

`__table_args__`: **UniqueConstraint(user_id, course_id)**. Beziehungen: backref `user` von User; `course` → `Course` (backref `purchases`).

### CardReviewState — `app/models.py:1289` (Tabelle `card_review_state`)
SRS-Zustand pro User+Content-Item (FSRS-Algorithmus).

| Feld | Typ | Constraints/Default | Bedeutung |
|---|---|---|---|
| id | Integer | PK | |
| user_id | Integer | **FK → user.id**, not null, **index** | User |
| content_id | Integer | **FK → lesson_content.id**, not null | Content-Item |
| fsrs_card_state | Text | not null | kompletter FSRS-Card-State (JSON via `Card.to_json()`) |
| due_date | DateTime | not null, **index** | Fälligkeitsdatum (denormalisiert) |
| status | String(20) | not null, default `'new'` | `new`/`learning`/`review`/`relearning`/`suspended` |
| reps | Integer | default 0, not null | Wiederholungen |
| lapses | Integer | default 0, not null | Lapses |
| created_at / updated_at | DateTime | default utcnow / onupdate | |

`__table_args__`: **UniqueConstraint(user_id, content_id)** (`uq_user_content_review`) + **Index(user_id, due_date, status)** (`ix_card_review_due`). Beziehungen: `user` → User (backref `card_states`, lazy='dynamic'); `content` → `LessonContent` (backref `review_states`, lazy='dynamic').

### ReviewLog — `app/models.py:1325` (Tabelle `review_log`)
Protokoll jeder Bewertung (Basis für FSRS-Optimizer).

| Feld | Typ | Constraints/Default | Bedeutung |
|---|---|---|---|
| id | Integer | PK | |
| user_id | Integer | **FK → user.id**, not null, **index** | User |
| content_id | Integer | **FK → lesson_content.id**, not null | Content-Item |
| rating | Integer | not null | 1=Again, 2=Hard, 3=Good, 4=Easy |
| reviewed_at | DateTime | default utcnow, not null, **index** | Zeitpunkt |
| time_taken_ms | Integer | nullable | Antwortdauer |
| fsrs_review_log | Text | nullable | FSRS-ReviewLog-State |
| scheduled_days | Integer | nullable | geplante Tage (denorm.) |
| elapsed_days | Integer | nullable | vergangene Tage (denorm.) |

Beziehungen: `user` → User (backref `review_logs`, lazy='dynamic'); `content` → `LessonContent`.

### KanaConfusion — `app/models.py:1352` (Tabelle `kana_confusion`)
Per-User-Verwechslungssignal: welches falsche Kana wurde für ein Ziel-Kana platziert.

| Feld | Typ | Constraints/Default | Bedeutung |
|---|---|---|---|
| id | Integer | PK | |
| user_id | Integer | **FK → user.id**, not null, **index** | User |
| target_kana_id | Integer | **FK → kana.id**, not null | Ziel-Kana |
| confused_kana_id | Integer | **FK → kana.id**, not null | fälschlich abgelegtes Kana |
| count | Integer | not null, default 1, server_default `'1'` | Häufigkeit |
| last_seen | DateTime | default utcnow, onupdate | |

`__table_args__`: **UniqueConstraint(user_id, target_kana_id, confused_kana_id)** (`uq_kana_confusion`).

### UserSRSSettings — `app/models.py:1381` (Tabelle `user_srs_settings`)
Persönliche SRS-Einstellungen pro User (1:1 zu User).

| Feld | Typ | Constraints/Default | Bedeutung |
|---|---|---|---|
| id | Integer | PK | |
| user_id | Integer | **FK → user.id**, **unique**, not null | User (1:1) |
| desired_retention | Float | default 0.9 | Zielretention |
| daily_new_cards | Integer | default 20 | neue Karten/Tag |
| daily_review_limit | Integer | default 100 | Reviews/Tag |
| fsrs_parameters | Text | nullable | 21 Optimizer-Floats als JSON |
| streak_freezes_available | Integer | default 1, not null | verfügbare Streak-Freezes |
| last_freeze_replenish | Date | nullable | letzte Freeze-Auffüllung |
| leech_threshold | Integer | default 8, not null | Leech-Schwelle |

Beziehung: `user` → User (backref `srs_settings`, `uselist=False` = **1:1**). Wird von `User.update_streak()` für die Freeze-Logik genutzt.

### UserAchievement — `app/models.py:1406` (Tabelle `user_achievement`)

| Feld | Typ | Constraints/Default | Bedeutung |
|---|---|---|---|
| id | Integer | PK | |
| user_id | Integer | **FK → user.id**, not null, **index** | User |
| achievement_key | String(50) | not null | Achievement-Schlüssel |
| unlocked_at | DateTime | default utcnow | freigeschaltet |
| notified | Boolean | default False, not null | benachrichtigt |

`__table_args__`: **UniqueConstraint(user_id, achievement_key)** (`uq_user_achievement`). Beziehung `user` → User (backref `achievements`, lazy='dynamic').

### DailyReviewAggregate — `app/models.py:1426` (Tabelle `daily_review_aggregate`)
Täglich aggregierte Review-Statistiken (Heatmap/Performance).

| Feld | Typ | Constraints/Default | Bedeutung |
|---|---|---|---|
| id | Integer | PK | |
| user_id | Integer | **FK → user.id**, not null, **index** | User |
| review_date | Date | not null, **index** | Tag |
| total_reviews | Integer | default 0, not null | Reviews gesamt |
| correct_reviews | Integer | default 0, not null | korrekt |
| again_count / hard_count / good_count / easy_count | Integer | default 0, not null | Rating-Verteilung |
| total_time_ms | BigInteger | default 0, not null | Gesamtzeit |
| xp_earned | Integer | default 0, not null | XP des Tages |
| new_cards_learned | Integer | default 0, not null | neue Karten |
| cards_leveled_up / cards_leveled_down | Integer | default 0, not null | Auf-/Abstufungen |

`__table_args__`: **UniqueConstraint(user_id, review_date)** (`uq_user_daily_agg`). Beziehung `user` → User (backref `daily_aggregates`, lazy='dynamic').

### KanaGridConfig — `app/models.py:1456` (Tabelle `kana_grid_config`)
Konfiguration eines Kana-Grid-Spiels, **1:1** an einen `LessonContent` (mit `content_type='kana_grid_game'`).

| Feld | Typ | Constraints/Default | Bedeutung |
|---|---|---|---|
| id | Integer | PK | |
| lesson_content_id | Integer | **FK → lesson_content.id (ondelete CASCADE)**, **unique**, not null | gekoppelter Content (1:1) |
| kana_ids | **JSON** | not null | Array von `Kana.id` |
| default_mode | String(20) | not null, default `'schreiben'` | `schreiben`/`lesen`/`blind` |
| allow_mode_switch | Boolean | not null, default True | Modus-Wechsel erlaubt |
| grid_layout | String(20) | not null, default `'rows'` | `rows`/`free` |
| shuffle_pool | Boolean | not null, default True | Pool mischen |
| timer_enabled | Boolean | not null, default False | Timer |
| max_hints | Integer | not null, default 0 | Hint-Klicks (Fading-Scaffolding) |
| show_romaji_hint_on_pool | Boolean | not null, default False | Romaji auf Pool-Karten |
| created_at / updated_at | DateTime | default utcnow / onupdate | |

Beziehung: `content` → `LessonContent` (backref `kana_grid_config`, `uselist=False` = **1:1**, cascade delete-orphan).

### PaymentTransaction — `app/models.py:1517`
Zahlungs-Transaktions-Tracking (Payrexx/Provider).

| Feld | Typ | Constraints/Default | Bedeutung |
|---|---|---|---|
| id | Integer | PK | |
| transaction_id | BigInteger | **unique**, not null, **index** | Provider-Transaktions-ID |
| user_id | Integer | **FK → user.id**, nullable | User |
| item_type | String(20) | not null | `lesson` / `course` |
| item_id | Integer | not null | ID des gekauften Items (kein DB-FK) |
| amount | Float | not null | Betrag |
| currency | String(3) | default `'CHF'` | Währung |
| state | String(50) | not null, **index** | Transaktionsstatus |
| created_at / updated_at | DateTime | default utcnow / onupdate | |
| webhook_data | **JSON** | nullable | Webhook-Rohdaten |
| transaction_metadata | **JSON** | nullable | Metadaten |

Keine ORM-Beziehung zu `User`/`Lesson`/`Course` definiert; `item_id`/`item_type` sind lose Referenzen.

### Event-Listener: lesson_type-Konsistenz — `app/models.py:1538`
`@event.listens_for(Lesson, 'before_insert'/'before_update')` — setzt `lesson_type` automatisch: `price == 0.0` → `"free"`, sonst `"paid"`. Hält `lesson_type` und `price` synchron.

### login_manager.user_loader — `app/models.py:1243`
`load_user(user_id)` lädt `User.query.get(int(user_id))` für Flask-Login.

---

## Beziehungs-Diagramm (Kernentitäten)

```
                          course_lessons (n:m)
        Course <-------------------------------> Lesson
          |                                       |  |  |
          | 1:n                              1:n  |  |  | 1:n
          v                                       |  |  v
     CoursePurchase                               |  | LessonPage (UQ lesson+page_no)
          ^                                       |  |
          | n:1                                   |  | 1:n (self, via LessonPrerequisite)
          |                                       |  +--> LessonPrerequisite (lesson_id / prerequisite_lesson_id)
    +-----+--------------------- User             |
    |     |          (1:n)        |  |            | 1:n
    |     | 1:n                   |  | 1:n        v
    |     v                       |  |        LessonContent ---- content_id (lose Ref, kein FK) ----> Kana / Kanji / Vocabulary / Grammar
    | LessonPurchase --- n:1 --> Lesson           |  |  |
    |                                              |  |  | 1:n
    | (UserLessonProgress: User n:1 / Lesson n:1)  |  |  v
    +--> UserLessonProgress <----------------------+  | QuizQuestion (FK lesson_content_id)
              content_progress = JSON {content_id}    |    |  |
                                                       |    |  | 1:n
   LessonCategory 1:n Lesson                           |    |  +--> QuizOption
   LessonCategory --(self FK prerequisite)--> LessonCategory
                                                       |    | 1:n
   --- SRS / Gamification (alle hängen an User) ---    |    +--> UserQuizAnswer (User n:1, UQ user+question)
                                                       |
   User 1:n  CardReviewState  --- content_id n:1 --> LessonContent   (UQ user+content)
   User 1:n  ReviewLog        --- content_id n:1 --> LessonContent
   User 1:n  DailyReviewAggregate   (UQ user+date)
   User 1:n  UserAchievement        (UQ user+key)
   User 1:n  KanaConfusion --- target/confused n:1 --> Kana   (UQ user+target+confused)
   User 1:1  UserSRSSettings        (UQ user_id)
   LessonContent 1:1 KanaGridConfig --- kana_ids = JSON[Kana.id]

   PaymentTransaction --- user_id n:1 --> User ; item_type/item_id lose Ref auf Lesson/Course
```

---

## Zusammenspiel

Eingehend:
- Das Modell wird ausschliesslich über `from app import db` initialisiert (`app/models.py:2`) und von praktisch allen anderen Modulen importiert — primär `app/routes.py` (Views + API), `app/admin_views.py` (Flask-Admin-CRUD), `app/seo_routes.py` (Sitemap zieht `is_published`-Lessons/Courses), `app/ai_services.py` und diverse `scripts/`.
- `login_manager.user_loader` (`:1243`) bindet das `User`-Model an Flask-Login.

Ausgehend (Abhängigkeiten, die das Modell zur Laufzeit aufruft):
- `flask.url_for('routes.uploaded_file', ...)` in `Lesson.get_background_url/get_thumbnail_url` und `LessonContent.get_file_url/delete_file` — Medien-Auflösung, optionaler GCS-Redirect über `current_app.config['GCS_BUCKET_NAME']` (aktuell nicht gesetzt → lokale Auslieferung).
- `current_app.config['UPLOAD_FOLDER']` in `LessonContent.delete_file()`.
- Optionaler Import von `pykakasi` in `_pyk_romaji()` (Cloze-Fallback; bei Fehlen → leeres Romaji).
- `zoneinfo.ZoneInfo("Europe/Zurich")` in `User.update_streak()`.

Welche Tabellen welche Benutzer-Seiten füttern (grobe Zuordnung):

| Tabelle(n) | Benutzer-Seite (grob) |
|---|---|
| `Lesson`, `LessonCategory`, `UserLessonProgress` | Lektions-Katalog / `/lessons`-Dashboard, Lernpfad-Hubs (`/learn/n5`) |
| `Lesson`, `LessonPage`, `LessonContent` (+ `Kana/Kanji/Vocabulary/Grammar` via `content_id`) | Lektionsansicht (`lesson_view`), Flip-Karten |
| `QuizQuestion`, `QuizOption`, `UserQuizAnswer` | Quiz innerhalb von Lektionen |
| `CardReviewState`, `ReviewLog`, `UserSRSSettings`, `KanaConfusion` | `/review` (SRS), Kana-Drills |
| `DailyReviewAggregate`, `User` (XP/Level/Streak), `UserAchievement` | `/review/stats` (Statistik/Heatmap), Gamification-Anzeigen, Top-Nav-Badges |
| `Kana`, `KanaGridConfig`, `KanaConfusion` | Kana-Spiel / Kana Storm / `/practice/kana` |
| `Lesson.price`, `Course`, `LessonPurchase`, `CoursePurchase`, `PaymentTransaction` | Kauf-/Bundle-Funnel, Zugriffskontrolle |
| `User` | Login/Registrierung, Account-Lockout, Profil |

## Beobachtungen (Ansatzpunkte)

- `app/models.py` umfasst 1'551 Zeilen und vermischt reines Schema, umfangreiche Geschäftslogik (Zugriffskontrolle in `Lesson.is_accessible_to_user`, Streak-Berechnung) und Text-Parsing-Hilfsfunktionen (Romaji-Umschrift, Cloze-Erzeugung, `parse_example_sentences`) in einer Datei.
- Zwei Deklarationsstile koexistieren: typisiertes `Mapped[...] / mapped_column` (neuere Models) und klassisches `db.Column` mit `__allow_unmapped__ = True` (ältere Models).
- `LessonContent.content_id` ist eine typabhängige manuelle Referenz auf `Kana/Kanji/Vocabulary/Grammar` ohne DB-Foreign-Key; die Auflösung passiert in `get_content_data()`. Ebenso sind `PaymentTransaction.item_id`/`item_type` lose Referenzen ohne FK.
- `UserLessonProgress.content_progress` speichert Detail-Fortschritt als JSON-String in einem `Text`-Feld (nicht als JSON-Spaltentyp), die (De)Serialisierung erfolgt manuell.
- `QuizQuestion.question_type` listet im Kommentar `fill_blank` und `UserQuizAnswer.text_answer` ist für Fill-in-the-blank vorhanden; laut Projekt-CLAUDE.md ist `fill_in_the_blank` jedoch deprecated.
- `Vocabulary` trägt zwei parallele Bedeutungsfelder (`meaning` legacy/englisch + `meaning_de`) und ein gemischt-formatiertes `example_sentence_english` (Format „Romaji — Übersetzung"), das per Property zerlegt wird.
- `Grammar.example_sentences` akzeptiert zwei Formate (JSON-Liste und nummerierter Plaintext), die durch `parse_example_sentences()` toleriert werden.
- Streak-Berechnung nutzt `Europe/Zurich` als Tagesgrenze (`User.update_streak`), während Lockout/`is_locked` und die meisten Timestamps in UTC (`datetime.utcnow`) gehalten werden — gemischte Zeitzonen-Semantik.
- `User.update_streak()` greift schreibend auf das `srs_settings`-Objekt zu (Freeze-Auffüllung), koppelt also Streak-Logik (User) und SRS-Settings.
- `LessonPurchase`/`CoursePurchase` haben `ondelete='RESTRICT'` auf der DB-FK und die ORM-Cascade wurde bewusst entfernt → das Löschen einer gekauften Lektion/eines Kurses wird auf DB-Ebene blockiert.
- Mehrere Code-referenzierte `content_type`-Werte (`dialog_slideshow`, `kana_grid_game`) tauchen in der Logik auf (`Lesson.progress_visible_content_items`, `mark_passive_items_completed`), sind aber im Spalten-Kommentar von `LessonContent.content_type` nicht aufgelistet.
- `lesson_type` wird nicht von der Anwendung gesetzt, sondern per SQLAlchemy-Event aus `price` abgeleitet (`free`/`paid`) — die Spalte ist faktisch redundant zu `price`/`is_purchasable`.
