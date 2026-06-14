# 08 · Admin & Content-Pipeline
_Stand: 2026-06-14 · Commit 2947710 · Teil der Ist-Zustand-Dokumentation_

## Zweck
Dieses Subsystem umfasst alle administrativen Oberflächen der Plattform sowie die Code-seitige Content-Pipeline. Dazu gehören zwei Admin-UIs (eine selbstgebaute `/admin/*`-Oberfläche und ein automatisch generiertes Flask-Admin-CRUD-Panel unter `/admin-panel`), der modulare Lektions-Editor, die rund 60 `/api/admin/*`-Endpoints (CRUD, Bulk-Operationen, Datei-Upload, Export/Import, KI-Generierung, Umsatz) und die Python-Module für KI-Generierung, Content-Validierung, Export/Import und personalisierte Lektionen. Alle Routen sind durch `@login_required` + `@admin_required` geschützt.

## Komponenten
| Datei | Zeilen | Rolle |
|---|---|---|
| `app/routes.py` | 4'863 | Enthält die `/admin/*`-Views (Zeile 719-779) und alle `/api/admin/*`-Endpoints; mischt User-Views und Admin-APIs in einer Datei |
| `app/admin_views.py` | 274 | Flask-Admin-Integration (`/admin-panel`): SecureModelViews + `init_admin()`-Factory |
| `app/ai_services.py` | 1'210 | KI-Content-Klasse `AILessonContentGenerator` (Gemini-Text + OpenAI-Bilder) und `GoogleCloudTTS` |
| `app/content_validator.py` | 610 | `ContentValidator` — KI-gestützte Lektions-Validierung (nicht an Routen angebunden) |
| `app/lesson_export_import.py` | 560 | `LessonExporter` / `LessonImporter` — JSON/ZIP-Export und -Import von Lektionen |
| `app/personalized_lesson_generator.py` | 595 | `PersonalizedLessonGenerator` — adaptive Lektionen (nicht an Routen angebunden) |
| `app/user_performance_analyzer.py` | 480 | `UserPerformanceAnalyzer` — Schwächen-Analyse (nur von `PersonalizedLessonGenerator` genutzt) |
| `app/templates/admin/base_admin.html` | ~49 KB | Admin-Basis-Template: Tailwind, Alpine.js, HTMX, Dark Mode, Command Palette, Toasts |
| `app/templates/admin/manage_lessons.html` | 76 | Orchestrator-Template, inkludiert 11 Partials aus `lessons/` |
| `app/templates/admin/lessons/*.html` | 11 Dateien | Modulare Partials des Lektions-Editors (Modals + JS) |
| `app/templates/admin/manage_*.html` + `admin_index.html` | 9 Dateien | Custom-Admin-Seiten (Kana/Kanji/Vocab/Grammar/Lessons/Categories/Courses/Approval/Dashboard) |

## Custom Admin (`/admin/*`)

Alle Views in `app/routes.py:719-779`, jeweils `@login_required` + `@admin_required`. Die `manage_*`-Seiten rendern überwiegend leere Templates, die ihren Inhalt per JavaScript über die `/api/admin/*`-Endpoints nachladen (Ausnahme: Approval-Seite, die server-seitig pending-Items übergibt).

| Route | View-Funktion | Template | Zweck |
|---|---|---|---|
| `/admin` | `admin_index` (`:719`) | `admin/admin_index.html` | Dashboard / Einstieg ins Custom-Admin |
| `/admin/manage/kana` | `admin_manage_kana` (`:725`) | `manage_kana.html` | Kana-Verwaltung (Liste/CRUD via JS) |
| `/admin/manage/kanji` | `admin_manage_kanji` (`:731`) | `manage_kanji.html` | Kanji-Verwaltung |
| `/admin/manage/vocabulary` | `admin_manage_vocabulary` (`:737`) | `manage_vocabulary.html` | Vokabel-Verwaltung |
| `/admin/manage/grammar` | `admin_manage_grammar` (`:743`) | `manage_grammar.html` | Grammatik-Verwaltung |
| `/admin/manage/lessons` | `admin_manage_lessons` (`:749`) | `manage_lessons.html` | Lektions-Editor (Orchestrator, CSRF-Form übergeben) |
| `/admin/manage/categories` | `admin_manage_categories` (`:756`) | `manage_categories.html` | Lektions-Kategorien |
| `/admin/manage/courses` | `admin_manage_courses` (`:762`) | `manage_courses.html` | Kurs-Verwaltung (CSRF-Form übergeben) |
| `/admin/manage/approval` | `admin_manage_approval` (`:769`) | `manage_approval.html` | KI-Approval-Queue; lädt server-seitig `Kanji/Vocabulary/Grammar` mit `status='pending_approval'` |

### base_admin.html (gemeinsames Layout)
- **Tailwind CSS** via Play-CDN (`base_admin.html:10`), `darkMode: 'class'`.
- **Alpine.js 3.14.8** (`:35`) + **HTMX 2.0.4** (`:38`).
- **Dark Mode**: Alpine-Store `darkMode` (`:51`), in `localStorage` persistiert; Toggle in der Sidebar (`:460`); `<html>` erhält `dark`-Klasse.
- **Command Palette (Ctrl+K)**: Trigger-Button (`:483`), Overlay-Komponente `commandPalette()` (`:509`) für Navigation + Aktionen.
- **Toast-Notifications**: `showToast()` (`:606`), CSS-Klassen `.toast-success/-error/-info`; HTMX-`after-swap`-Hook wertet `HX-Trigger`-Header aus (`:627`).
- Kind-Templates füllen Blocks `page_header`, `page_actions`, `content`, `extra_css`, `extra_js`.

## Lektions-Editor (Orchestrator + 11 Partials)

`manage_lessons.html` (76 Zeilen) erbt von `base_admin.html`, rendert die Lessons-Tabelle (per JS befüllt) + eine Bulk-Action-Bar und inkludiert die Partials aus `app/templates/admin/lessons/`:

| Partial | Rolle (eine Zeile) |
|---|---|
| `_styles.html` | CSS für den Editor + Quill-Editor-Styling |
| `_lesson_modals.html` | Add-/Edit-Lesson-Modals |
| `_content_modal.html` | Content-Manager, Preview, Seiten-Editor (Modal) |
| `_content_wizard.html` | 3-Schritt-Content-Wizard für die verschiedenen Content-Typen |
| `_import_export.html` | Import-/Export-Modals |
| `_js_core.html` | CSRF, Lesson-CRUD, Kategorien, `escapeHtml` |
| `_js_content.html` | Content laden, Bulk-Operationen, Preview |
| `_js_file_upload.html` | Drag & Drop, Upload, Fortschrittsanzeige |
| `_js_editor.html` | Quill-Editor, Wizard-Logik, Inline-Editing, Speichern (grösstes Partial, ~55 KB) |
| `_js_pages.html` | Seiten-CRUD, Seiten-Content-Editor |
| `_js_import_export.html` | Export-/Import-Logik (Frontend) |

Hinweis: Der Orchestrator inkludiert im `extra_js`-Block alle 6 `_js_*`-Partials; `_content_wizard.html` ist ein Markup-Partial (kein JS). Die Reihenfolge der `include`-Statements ist in `manage_lessons.html:62-75` festgelegt.

## Admin-APIs (`/api/admin/*` in `app/routes.py`)

Rund 60 Endpoints, alle mit `@login_required` + `@admin_required`. Gruppiert (Zeilenbereiche als Anker):

| Gruppe | Endpoints (Methoden) | Bereich |
|---|---|---|
| Referenzdaten-CRUD: Kana | list / new / get / edit / delete | `:1391-1466` |
| Referenzdaten-CRUD: Kanji | list / new / get / edit / delete | `:1468-1544` |
| Referenzdaten-CRUD: Vocabulary | list / new / get / edit / delete | `:1546-1620` |
| Referenzdaten-CRUD: Grammar | list / new / get / edit / delete | `:1622-1694` |
| KI-Approval | `content/<type>/<id>/approve`, `.../reject` | `:1696-1720` |
| Kategorien-CRUD | list / new / get / edit / delete | `:1723-1789` |
| Kurse-CRUD | list / new / get / edit / delete | `:1791-1885` |
| Lektionen-CRUD | list / new / get / edit / delete | `:1887-2069` |
| Lektions-Struktur | `move`, `reorder`, `content-options/<type>` (`:2070-2186`); `patch` (`:2426`) | gemischt |
| Content-CRUD | content list / new / delete / move; pages-reorder / move-to-page; pages `<n>` reorder | `:2188-2537` |
| Content (Einzel) | preview, get, edit, duplicate | `:2585-2943` |
| Content (Bulk) | bulk-update / bulk-duplicate / bulk-delete / force-reorder | `:2726-2884` |
| Pages | page delete / page PUT | `:2944-3010` |
| Audio | `audio/record-upload` (MediaRecorder-Blob → Datei) | `:2538` |
| Interaktiv | `content/interactive` (Quiz-Content anlegen) | `:3865` |
| Umsatz/Käufe | `purchases`, `lessons/<id>/purchases`, `revenue-stats` | `:3762-3816` |
| KI-Generierung | `generate-ai-content`, `generate-ai-image`, `analyze-multimedia-needs`, `generate-lesson-images`, `vocabulary/generate-images` | `:4115-4294` |
| Datei | `upload-file`, `lessons/<id>/content/file`, `delete-file` | `:4301-4409` |
| Export/Import | `lessons/<id>/export`, `export-package`, `lessons/import`, `import-package`, `export-multiple`, `import-info` | `:4497-4758` |

### KI-Approval-Mechanik
- `approve_content` (`:1696`): setzt `item.status = 'approved'` für `kanji`/`vocabulary`/`grammar`.
- `reject_content` (`:1709`): **löscht** das Item aus der DB (`db.session.delete`).
- Frontend: `manage_approval.html:160` `handleApproval()` ruft `/api/admin/content/<type>/<id>/<approve|reject>` per POST mit CSRF-Token.

## Flask-Admin CRUD-Panel (`/admin-panel`)

`app/admin_views.py` registriert via `init_admin(app, db.session)` (aufgerufen in `app/__init__.py:496-497`). Index-View `SecureAdminIndexView` an URL `/admin-panel` mit einem Statistik-Dashboard (`admin/flask_admin_index.html`). Zugriffsschutz über `AuthMixin.is_accessible()` (`current_user.is_admin`); nicht-Admins werden auf den Login umgeleitet.

| ModelView | Model | Kategorie | Besonderheiten |
|---|---|---|---|
| `KanaAdmin` | `Kana` | Japanisch | inline-editierbar (romanization/type) |
| `KanjiAdmin` | `Kanji` | Japanisch | Filter jlpt/status/created_by_ai, status inline editierbar |
| `VocabularyAdmin` | `Vocabulary` | Japanisch | wie Kanji |
| `GrammarAdmin` | `Grammar` | Japanisch | wie Kanji |
| `LessonCategoryAdmin` | `LessonCategory` | Lektionen | Sortierung jlpt+display_order |
| `LessonAdmin` | `Lesson` | Lektionen | nur Liste/Basisdaten, `can_delete=False` (voller Editor bleibt custom) |
| `CourseAdmin` | `Course` | Lektionen | is_published/price inline editierbar |
| `UserAdmin` | `User` | System | `can_create=False`, `can_delete=False`, Passwort-Hash ausgeblendet |

`SecureModelView`-Defaults: `page_size=50`, CSV-Export aktiv, Detailansicht aktiv.

## Content-Pipeline-Module

### `ai_services.py` — `AILessonContentGenerator`
Klassen-Docstring (`:133`): „Gemini für Text, OpenAI für alle Bilder“. Im Konstruktor (`:136`): OpenAI-Client aus `OPENAI_API_KEY`; Gemini-Client aus `GEMINI_API_KEY`/`GOOGLE_AI_API_KEY`, Modell `gemini-3-flash-preview` (`:155`). Textgenerierung läuft über `_generate_content()` (`:164`), das die **Gemini**-API aufruft.

Methoden (alle vorhanden im Code):

| Methode | Engine | Soll-Zustand laut CLAUDE.md |
|---|---|---|
| `generate_explanation` (`:200`) | Gemini-Text | TOT für Content (Text muss von Claude kommen) |
| `generate_formatted_explanation` (`:210`) | Gemini-Text | TOT für Content |
| `generate_true_false_question` (`:240`) | Gemini-Text | TOT für Content |
| `generate_fill_in_the_blank_question` (`:584`) | Gemini-Text | TOT (Quiz-Typ `fill_in_the_blank` laut CLAUDE.md ohnehin nicht mehr verwendet) |
| `generate_matching_question` (`:617`) | Gemini-Text | TOT für Content |
| `generate_page_quiz_batch` (`:679`) | Gemini-Text | TOT für Content |
| `generate_multiple_choice_question` (`:809`) | Gemini-Text | TOT für Content |
| `create_adaptive_quiz` (`:891`) | Gemini-Text | TOT für Content |
| `generate_kanji_data` (`:946`) | Gemini-Text | TOT für Content |
| `generate_vocabulary_data` (`:979`) | Gemini-Text | TOT für Content |
| `generate_vocabulary_example_sentence` (`:1014`) | Gemini-Text | TOT für Content |
| `generate_grammar_data` (`:1066`) | Gemini-Text | TOT für Content |
| `generate_image_prompt` (`:288`) | Gemini-Text (Prompt-Text) | Hilfsmethode für Bildpfad |
| `analyze_content_for_multimedia_needs` (`:542`) | Gemini-Text | Analyse, kein Content |
| `generate_single_image` (`:365`) | **OpenAI** `gpt-image-1-mini` | ERLAUBT (Bilder) |
| `generate_lesson_images` (`:316`) | OpenAI (über `generate_single_image`) | ERLAUBT (Bilder) |
| `generate_vocabulary_image` (`:414`) | OpenAI | ERLAUBT (Bilder) |
| `generate_lesson_tile_background` (`:456`) | OpenAI | ERLAUBT (Bilder) |

`GoogleCloudTTS` (`:1111`): TTS via Google-Cloud-REST-API (API-Key), Stimmen `ja-JP-Neural2-B/-D`, Methoden `generate_audio`, `generate_kana_audio`, `generate_vocabulary_audio`, `generate_dialogue_audio`. ERLAUBT (Audio). Hinweis: Diese REST-Variante unterscheidet sich vom in CLAUDE.md beschriebenen Gemini-2.5-Pro-TTS-Pfad der Audio-Skripte.

### Soll-Zustand vs. real vorhandener Code (toter Gemini-Content-Code)
Laut `CLAUDE.md` (Abschnitt „Content-Generierung: immer Claude“) dürfen die `generate_*`-Methoden für **Text-/Sprach-Content** nicht mehr aufgerufen werden; neuer Content wird von Claude verfasst und per Skript in die DB geschrieben. Real vorhandener Code:
- Die HTTP-Endpoints `generate-ai-content` (`:4115`) und `generate-ai-image` (`:4154`) existieren weiterhin und rufen die Gemini-Text-/OpenAI-Bild-Methoden auf. `generate-ai-content` (Text) widerspricht damit dem dokumentierten Soll-Zustand; `generate-ai-image` (Bild) ist konform.
- `ContentValidator` (`content_validator.py:25`) und `PersonalizedLessonGenerator` (`personalized_lesson_generator.py:32`) instanziieren `AILessonContentGenerator` und nutzen Gemini-Text-Methoden, sind aber **an keine Route angebunden** (grep über `app/*.py` findet keinen Aufrufer ausserhalb der Module selbst) — toter/nicht erreichbarer Code.
- `UserPerformanceAnalyzer` wird nur von `PersonalizedLessonGenerator` referenziert; da dieser nicht angebunden ist, ist auch der Analyzer praktisch ungenutzt.

### `content_validator.py`, `lesson_export_import.py`, `personalized_lesson_generator.py`, `user_performance_analyzer.py`
- `ContentValidator.validate_lesson()` (`:27`) bewertet Lektionen samt Content/Quiz per KI — kein Routen-Aufrufer.
- `LessonExporter`/`LessonImporter` (`:23` / `:270`) — **aktiv** über die Export/Import-Endpoints (`routes.py:4497-4758`), die die Wrapper-Funktionen `export_lesson_to_json` / `import_lesson_from_json` / `create_lesson_export_package` nutzen.
- `PersonalizedLessonGenerator.generate_personalized_lesson()` (`:34`) erzeugt remedial/advancement/review-Lektionen aus der Schwächen-Analyse — kein Routen-Aufrufer.
- `UserPerformanceAnalyzer.analyze_weaknesses()` (`:30`) liest `UserLessonProgress`/`UserQuizAnswer` — nur intern genutzt.

## Zusammenspiel
- **Eingehend**: Admin-Nutzer rufen `/admin/*` (Custom-UI) und `/admin-panel` (Flask-Admin) auf; beide setzen `@admin_required` bzw. `is_admin` voraus. `init_admin()` wird beim App-Start in `app/__init__.py:496` registriert.
- **Datenfluss**: Die `manage_*`-Seiten laden ihre Daten asynchron über die `/api/admin/*`-Endpoints; diese lesen/schreiben direkt die SQLAlchemy-Models (`Kana`, `Kanji`, `Vocabulary`, `Grammar`, `Lesson`, `LessonPage`, `LessonContent`, `LessonCategory`, `Course`, `QuizQuestion`/`QuizOption`, `LessonPurchase`).
- **Datei-Uploads** gehen über `FileUploadHandler` (`app/utils.py`) in `app/static/uploads/`; die URL-Bildung berücksichtigt einen optionalen `GCS_BUCKET_NAME` (aktuell nicht gesetzt → lokale Auslieferung über `routes.uploaded_file`).
- **Ausgehend (extern)**: KI-Bild-Endpoints rufen OpenAI (`gpt-image-1-mini`); `GoogleCloudTTS` ruft die Google-TTS-REST-API; die (für Content tot gelegten) Text-Methoden rufen die Gemini-API.
- **Approval-Queue**: hängt am `status`-Feld (`pending_approval` → `approved`) bzw. dem `created_by_ai`/`generated_by_ai`-Flag der Models; bedient durch `manage_approval.html` + `approve_content`/`reject_content`.
- **Umsatz-Endpoints** (`purchases`, `revenue-stats`) lesen das Zahlungs-Tracking (`LessonPurchase`), das vom Payment-Subsystem befüllt wird.

## Beobachtungen (Ansatzpunkte)
- `app/routes.py` ist 4'863 Zeilen lang und vermischt öffentliche User-Views, SRS-/Review-Routen und sämtliche `/api/admin/*`-Endpoints in einer Datei.
- Es existieren zwei parallele Admin-Oberflächen für teils dieselben Models: das Custom-Admin (`/admin/*`, eigene `/api/admin/*`-CRUD-Endpoints) und das Flask-Admin-Panel (`/admin-panel`, auto-generiertes CRUD). Kana/Kanji/Vocab/Grammar/Categories/Courses/Lessons/User sind in beiden bearbeitbar.
- Der HTTP-Endpoint `generate-ai-content` (`:4115`) ruft weiterhin Gemini-Text-Methoden auf und steht damit im Widerspruch zum in `CLAUDE.md` dokumentierten Soll-Zustand „Text-Content nur von Claude, keine Laufzeit-LLM-Calls für Content“.
- `ContentValidator`, `PersonalizedLessonGenerator` und (transitiv) `UserPerformanceAnalyzer` sind im Code vorhanden, aber an keine Route angebunden — nicht erreichbarer Code, der dennoch `AILessonContentGenerator` (Gemini) instanziiert.
- Die in `ai_services.py` enthaltene `GoogleCloudTTS`-Klasse nutzt `ja-JP-Neural2-B/-D` über die REST-API; das weicht vom in `CLAUDE.md` beschriebenen Audio-Pfad (Gemini 2.5 Pro TTS „Leda“ in den `scripts/`) ab — zwei verschiedene TTS-Wege existieren parallel.
- `reject_content` löscht das Item hart aus der DB (kein Soft-Delete / keine Wiederherstellung).
- Mehrere KI-Methoden referenzieren `fill_in_the_blank` (`generate_fill_in_the_blank_question`), obwohl dieser Quiz-Typ laut `CLAUDE.md` nicht mehr verwendet wird.
- Das Modell-Statusfeld heisst `status` mit Wert `pending_approval`/`approved`, daneben existieren Flags `created_by_ai` (Models) bzw. `generated_by_ai` (in CLAUDE.md erwähnt) — die genaue Feld-Benennung pro Model wäre zu prüfen.
- `manage_lessons.html` inkludiert 6 JS-Partials; `_js_editor.html` ist mit ~55 KB das mit Abstand grösste Partial und konzentriert Quill/Wizard/Inline-Editing/Save.
