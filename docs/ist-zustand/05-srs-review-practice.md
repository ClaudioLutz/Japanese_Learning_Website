# 05 · SRS, Review, Practice & Gamification
_Stand: 2026-06-14 · Commit 2947710 · Teil der Ist-Zustand-Dokumentation_

## Zweck

Dieses Subsystem deckt das Spaced-Repetition-System (FSRS), die tägliche Wiederholungs-Seite, die erweiterte Statistik-Seite, alle Kana-Übungsmodi (Matching-Grid, Tages-Challenge, Lese-Modus, Verwechslungs-Drill, Kana-Storm-Arcade) sowie die Gamification-Schicht (XP, Level, Streak, Achievements) ab. Es kapselt den Lern-Loop NACH dem Lektions-Konsum: Karten werden geplant, bewertet, statistisch ausgewertet und spielerisch verstärkt. Alle benutzersichtbaren Routen liegen im Blueprint `srs_bp` (`app/srs_routes.py`), registriert ohne URL-Prefix in `app/__init__.py:265`.

## Komponenten

| Datei | Zeilen | Rolle |
|---|---|---|
| `app/srs_routes.py` | 1'480 | Blueprint `srs_bp`: 8 Seiten (render_template) + 33 JSON-/Hilfs-Routen (41 Routen gesamt) + Gast-Helfer |
| `app/srs_service.py` | 1'019 | FSRS-Algorithmus, Due-Berechnung, Statistik-Aggregationen, Karten-Browser |
| `app/gamification_service.py` | 190 | XP-Tabelle, Karten-Stufen (Stability→Stage), DailyAggregate, Variable-Reward |
| `app/achievements.py` | 257 | 24 Achievement-Definitionen (im Code, nicht DB) + `check_achievements` |
| `app/services/kana_rows.py` | 189 | Gojuon-Reihen-Mapping (Hiragana/Katakana, Romaji, Reihen-Keys/-Labels) |
| `app/services/kana_confusion.py` | 82 | Kanonische Verwechslungs-Cluster (visuell ähnliche Kana) |
| `app/templates/review.html` | 2'000 | SRS-Karten-Loop (JS-getrieben), Gamification-Feedback |
| `app/templates/stats.html` | 934 | Statistik-Seite `/review/stats` (Charts via fetch) |
| `app/templates/browse.html` | 398 | Karten-Browser `/review/browse` |
| `app/templates/practice_kana.html` | 400 | Kana-Spiel-Einstellung (Matching) + Quick-Starts |
| `app/templates/practice_kana_game.html` | 222 | Vollbild-Spielseite (Matching-Grid) |
| `app/templates/practice_kana_storm.html` | 60 | Kana-Storm-Arcade-Vollbildseite + `/daily` |
| `app/templates/_kana_game_stage.html` | 218 | Geteiltes Markup der Matching-Bühne (`kanaGameView`) |
| `app/templates/_kana_game_embed_layout.html` | 211 | Schlankes iframe-Embed des Matching-Spiels (Startseite) |
| `app/templates/_kana_storm_stage.html` | 297 | Geteiltes Storm-Markup (Tabs Storm/Daily, `kanaStormGame`) |
| `app/templates/_kana_storm_styles.html` | 283 | Storm-CSS (namespaced `.kstorm`) |
| `app/static/js/kana_grid_game.js` | 1'274 | Alpine-Komponenten `kanaGridGame`, `kanaSettings`, `kanaGameView` |
| `app/static/js/kana_storm.js` | 658 | Alpine-Komponente `kanaStormGame` (Arcade + Daily) |

User-Modell-Felder für dieses Subsystem (`app/models.py:23-35`): `current_streak`, `longest_streak`, `last_activity_date`, `total_xp`, `level`, `total_reviews`, `total_mastered`, `push_subscription`. Methoden: `update_streak()` (`app/models.py:63`), `add_xp()` (`app/models.py:98`), Properties `xp_for_next_level` (`:104`) und `level_title` (`:109`).

## Routen-Übersicht (`srs_bp`)

### Seiten (render_template)

| Pfad · Zeile | Methode | Template | Zweck |
|---|---|---|---|
| `/review` · `app/srs_routes.py:157` | GET | `review.html` | Tägliche Wiederholungs-Seite (login_required) |
| `/review/stats` · `app/srs_routes.py:231` | GET | `stats.html` | Erweiterte Statistiken (Level/XP-Aufbereitung im View) |
| `/review/browse` · `app/srs_routes.py:406` | GET | `browse.html` | Karten-Browser (übergibt published Lessons) |
| `/practice/kana` · `app/srs_routes.py:825` | GET | `practice_kana.html` | Matching-Einstellung (auch für Gäste) |
| `/practice/kana/spiel` · `app/srs_routes.py:836` | GET | `practice_kana_game.html` | Matching-Spielseite (auch für Gäste) |
| `/practice/kana/storm` · `app/srs_routes.py:847` | GET | `practice_kana_storm.html` | Kana-Storm-Arcade (inline, kein iframe) |
| `/daily` · `app/srs_routes.py:861` | GET | `practice_kana_storm.html` | Kurz-URL → Storm-Seite mit `kstorm_initial_tab='daily'` |
| `/practice/kana/embed` · `app/srs_routes.py:871` | GET | `_kana_game_embed_layout.html` | iframe-Embed (Startseite, ohne base.html-Chrome) |

### JSON-APIs — SRS-Kern

| Pfad · Zeile | Methode | Zweck |
|---|---|---|
| `/api/srs/rate` · `:23` | POST | Karte bewerten (1-4), FSRS-State + XP + Streak + Achievements (login_required) |
| `/api/srs/due` · `:79` | GET | Fällige Karten (Filter: limit/lesson_id/content_type) |
| `/api/srs/preview` · `:114` | GET | Voraussichtliche Intervalle für alle 4 Ratings |
| `/api/srs/reviewed-ids` · `:126` | GET | Bereits bewertete content_ids (Deck-Init) |
| `/api/srs/stats` · `:144` | GET | Basis-Statistiken + Streak |

### JSON-APIs — Statistik (Phase 6 / Kana)

| Pfad · Zeile | Methode | Zweck |
|---|---|---|
| `/api/srs/stats/heatmap` · `:170` | GET | 365-Tage Review-Heatmap |
| `/api/srs/stats/retention` · `:178` | GET | Retention nach Intervall-Bereich + desired_retention |
| `/api/srs/stats/forecast` · `:188` | GET | Review-Forecast (Default 30 Tage, max 90) |
| `/api/srs/stats/maturity` · `:197` | GET | Karten-Verteilung nach Reifestufe |
| `/api/srs/stats/content-type` · `:205` | GET | Performance je Content-Typ |
| `/api/srs/stats/leeches` · `:213` | GET | Problematische Karten (Leeches, threshold aus Settings) |
| `/api/srs/stats/response-times` · `:223` | GET | Antwortzeit-Histogramm |
| `/api/srs/jlpt-progress` · `:467` | GET | JLPT N5-N1 Fortschritt |
| `/api/srs/stats/kana-heatmap` · `:478` | GET | Pro-Zeichen-Statistik Hiragana/Katakana (Stage+Accuracy) |
| `/api/srs/stats/kana-weak` · `:541` | GET | Top-N schwächste Kana (lapses DESC, accuracy ASC) |

### JSON-APIs — Karten-Browser & Gamification

| Pfad · Zeile | Methode | Zweck |
|---|---|---|
| `/api/srs/browse` · `:261` | GET | Karten-Browser (Filter/Suche/Pagination) |
| `/api/srs/card/<id>/detail` · `:281` | GET | Karten-Detail inkl. Review-History |
| `/api/srs/card/suspend` · `:291` | POST | Karte suspendieren |
| `/api/srs/card/unsuspend` · `:303` | POST | Karte reaktivieren |
| `/api/srs/card/reset` · `:315` | POST | FSRS-State zurücksetzen |
| `/api/srs/bulk-action` · `:327` | POST | Bulk suspend/unsuspend/reset (1-100 Karten) |
| `/api/srs/browse/export` · `:354` | GET | Karten-CSV-Export |
| `/api/srs/achievements` · `:418` | GET | Alle Achievements mit Unlock-Status |
| `/api/srs/achievements/notify` · `:447` | POST | Achievements als gesehen markieren |
| `/api/user/push-subscribe` · `:606` | POST | Web-Push-Subscription speichern (opt-in) |
| `/api/user/push-unsubscribe` · `:619` | POST | Web-Push-Subscription löschen |

### JSON-APIs — Kana-Practice (teils ohne Login)

| Pfad · Zeile | Methode | Login | Zweck |
|---|---|---|---|
| `/api/practice/kana/session` · `:884` | GET | ja | Matching-Session aus Filtern (freigeschaltete Kana + SRS-Sortierung) |
| `/api/practice/kana/session/public` · `:1032` | GET | nein | Gast-Session (voller Gojuon-Scope, kein User-State) |
| `/api/practice/kana/daily-challenge` · `:1068` | GET | optional | 10 Kana deterministisch pro Tag (eingeloggt personalisiert + Bonus-XP, Gast global) |
| `/api/practice/kana/storm-daily` · `:1138` | GET | nein | Globales Tagesbrett (10 Kana, für ALLE identisch, day_number) |
| `/api/srs/kana-confusion` · `:1219` | POST | ja | Fehl-Drops (Verwechslungs-Paare) loggen |
| `/api/practice/kana/confusion` · `:1262` | GET | optional | Verwechslungs-Drill-Cluster (eingeloggt per-User priorisiert) |
| `/api/kana-grid/<id>/config` · `:1396` | GET | nein* | Konfiguration eines Lektions-internen Kana-Grid-Spiels (*Zugriff via `Lesson.is_accessible_to_user`) |

Interne Helfer (keine Routen): `_user_unlocked_kana_ids` (`:631`), `_guest_kana_chars` (`:675`), `_guest_kana_rows` (`:706`), `_kana_item` (`:739`), `_parse_limit` (`:761`), `_subset_in_order` (`:774`), `_guest_scope_payload` (`:789`), `_record_kana_confusions` (`:1184`).

## Seiten im Detail

### `/review` — `review.html` (2'000 Zeilen)
Viewport-gesperrte Karten-Bühne (`body.review-locked`, Footer/Bottom-Nav ausgeblendet). Der View (`app/srs_routes.py:157`) übergibt nur `stats` (Basis-Statistik + Streak); alles Weitere wird client-seitig per fetch geladen:
- `fetch('/api/srs/due?limit=50')` baut den Karten-Stapel (`review.html:1133`).
- Jede Bewertung geht an `POST /api/srs/rate` (`:1767`); die Antwort liefert XP, Level-Up, Stufen-Wechsel, neuen Streak und `new_achievements`, die als Toasts angezeigt werden (`:1786-1799`).
- Front-Romaji-Toggle wird VOR Body-Render aus `localStorage` gesetzt (`:7-30`), um Flash zu vermeiden.
- `/api/srs/preview` liefert die Intervall-Labels pro Rating-Button (`:1730`), `/api/srs/stats` + `/api/srs/stats/forecast?days=3` füttern die Kopf-Zahlen (`:1934`, `:1951`), `/api/srs/achievements/notify` markiert gesehene Achievements (`:1989`). Audio läuft über `/api/tts` (`:1624`, ausserhalb dieses Subsystems).

### `/review/stats` — `stats.html` (934 Zeilen)
Der View (`app/srs_routes.py:231`) berechnet die Level-Progress-Anteile serverseitig: `total_xp` ist kumulativ, `xp_for_next_level` ist die absolute Schwelle; für einen Pro-Level-Balken wird der Level-Boden `int(100*((level-1)**1.5))` abgezogen (`:248-254`). Die Charts werden client-seitig parallel geladen (`stats.html:602-612`) aus elf Endpoints: heatmap, retention, forecast(14), maturity, content-type, response-times, leeches, jlpt-progress, achievements, kana-heatmap, kana-weak(5). Karten-Aktionen (`/api/srs/card/suspend`, `/api/srs/card/reset`) werden direkt von hier ausgelöst (`:915`, `:925`).

### `/practice/kana` — `practice_kana.html` (400 Zeilen)
Einstellungs-Seite des Matching-Spiels, Alpine-Komponente `kanaSettings()` (`practice_kana.html:248`). Steuerflächen: Schrift (Hiragana/Katakana/beide), Modus (Schreiben = Romaji→Kana / Lesen = Kana→Romaji), Reihen-Chips (aus `availableRows`), Optionen (Dakuten-Schalter; „Nur schwache Karten" nur eingeloggt). Kein Anzahl-Slider mehr — gespielt wird die Auswahl, Vorschau zählt live. Quick-Starts: „Tages-Challenge" (`startDaily`), „Schwache Karten" (`startWeak`, login-gated), „Ähnliche" (`startConfusion`). Für Gäste ein Conversion-Teaser mit Registrieren-CTA (`:269-281`). Verlinkt unten auf Kana Storm (`:386`). Die Vorschau-Zählung ruft je nach Login `/api/practice/kana/session` oder `.../session/public` (`kana_grid_game.js:960`).

### `/practice/kana/spiel` — `practice_kana_game.html` (222 Zeilen)
Vollbild-Spielbühne (`body.kana-game-locked`). Bindet `_kana_game_stage.html` mit `kgame_embed=false` ein (`:216-217`); das Markup ist mit dem iframe-Embed geteilt. Die Alpine-Komponente `kanaGameView()` (`kana_grid_game.js:1007`) liest die Filter aus den Query-Params und wählt den Endpoint (`:1037-1067`): Confusion-Drill → `/api/practice/kana/confusion`, Daily → `/api/practice/kana/daily-challenge`, sonst Gast/Login-Session. Ratings (nur eingeloggt, mit echtem `lesson_content_id`) gehen an `/api/srs/rate` (`:639`), Fehl-Drops an `/api/srs/kana-confusion` (`:593`).

### `/practice/kana/storm` + `/daily` — `practice_kana_storm.html` (60 Zeilen)
Schlanke Hülle (`body.kstorm-locked`), bindet `_kana_storm_styles.html` und `_kana_storm_stage.html` ein. `/daily` rendert dasselbe Template mit `kstorm_initial_tab='daily'`. Die Komponente `kanaStormGame()` (`kana_storm.js:89`) läuft inline (kein iframe). Zwei Modi in einer Karte (Tabs, `_kana_storm_stage.html:45-56`):
- **Kana Storm**: endloser Romaji-Tipp-Loop gegen die Uhr, Daten aus `/api/practice/kana/session/public` (`kana_storm.js:245`). Scoring (`KANA_STORM_SCORING`) mit Tempo-Bonus + Combo-Faktor; Bestscore lebt im `localStorage` (`:174-175`), kein DB-Write.
- **Daily-Karte**: Wordle-Mechanik, globales Tagesbrett aus `/api/practice/kana/storm-daily` (`kana_storm.js:529`), teilbarer Emoji-Block.

### `/practice/kana/embed` — `_kana_game_embed_layout.html` (211 Zeilen)
Eigenständiges HTML-Dokument ohne base.html-Chrome (`:1-23`), für das `<iframe>` der Startseite. Setzt `kgame_embed=true` und bindet dasselbe `_kana_game_stage.html` ein. Läuft immer im Gast-Modus; die Spielart wird per Query-Param gewählt (`?schrift=…` / `?challenge=daily`). Die Konto-CTA nach dem Spiel steuert die Eltern-Seite per `postMessage`.

## SRS-Algorithmus (`app/srs_service.py`)

Aufbauend auf der Python-Library `fsrs` (Card/Rating/Scheduler/State). Rating-Mapping `1=Again, 2=Hard, 3=Good, 4=Easy` (`:24-29`).

- **Scheduler** (`_get_scheduler`, `:47`): pro User aus `UserSRSSettings` (`desired_retention`, Default 0.9; optionale gewichtete `fsrs_parameters`), `enable_fuzzing=True`.
- **`rate_card`** (`:71`) ist die Kern-Operation: lädt/erstellt `CardReviewState`, ruft `scheduler.review_card`, schreibt neuen FSRS-Card-State + `due_date` (UTC, naiv gespeichert), erhöht `reps`, bei Rating 1 `lapses`. Berechnet Stufenwechsel via `get_card_stage` (vor/nach), vergibt XP (`calculate_xp` + evtl. Variable-Reward-Boost), aktualisiert `total_reviews`/`total_mastered` (Stage-Index 9 = gemeistert), schreibt `DailyReviewAggregate` und `ReviewLog`, committet. Rückgabe enthält `next_interval`, `due_date`, XP/Level/Stage-Felder.
- **Due-Berechnung**: `get_due_cards` (`:211`) und `get_due_count` (`:231`) filtern `due_date <= utcnow()` und `status != 'suspended'`, sortiert nach `due_date` aufsteigend.
- **Review-Queue/Neue Karten**: `get_new_cards` (`:241`) liefert noch nie bewertete Lektions-Items (Typen kana/kanji/vocabulary/grammar).
- **Intervall-Vorschau**: `get_interval_preview` (`:256`) berechnet für alle 4 Ratings ein Label (<N Min / N Std / N Tage).
- **Content-Aufbereitung**: `get_content_data_for_review` (`:346`) baut Vorder-/Rückseiten-Daten je Content-Typ (inkl. Cloze, Beispielsätze, TTS-Felder, Mnemonic).
- **Statistik-Aggregationen** (`:490-768`): heatmap (365 Tage), retention-by-interval, forecast, maturity-distribution, performance-by-type, leeches, response-time-histogram, jlpt-progress.
- **Browser & Karten-Verwaltung** (`:771-1018`): `browse_cards` (Filter/Suche/Pagination), `get_card_detail`, `suspend_card`/`unsuspend_card`/`reset_card`. Migrations-Helfer `migrate_existing_progress` (`:425`).

## Kana-Reihen & Verwechslung

- **`app/services/kana_rows.py`**: zentrales Gojuon-Mapping (30 Reihen-Sets, 16 Reihen-Keys `vowels,k,s,…,p`). Tabellen `HIRAGANA_ROWS`/`KATAKANA_ROWS`/`ROMAJI_ROWS`/`ROW_LABELS`. Funktionen `row_for_kana` (Zeichen→Reihe), `row_for_romanization` (Romaji→Reihe), `kana_rows_for_lesson` (gruppiert Kana-Objekte für das Lektions-Grid). Wird sowohl vom Kana-Spiel als auch von der TTS-Pause-Heuristik in `routes.py` genutzt.
- **`app/services/kana_confusion.py`**: `CONFUSION_SETS` = 22 kanonische Cluster optisch ähnlicher Kana (Kaltstart-Quelle). `confusion_clusters(available_chars)` schneidet auf verfügbare Zeichen zu (min. 2 Mitglieder). Speist `/api/practice/kana/confusion`; ist bei eingeloggten Usern durch das echte Per-User-Signal (`KanaConfusion`) überlagert (Priorisierung in `app/srs_routes.py:1330-1365`). Hinweis im Modul: fachlich durch Mayuko gegenzulesen.

## Gamification (`app/gamification_service.py`, `app/achievements.py`)

- **XP** (`gamification_service.py:23-26`): `XP_PER_RATING = {1:2, 2:5, 3:10, 4:12}`, `XP_NEW_CARD_BONUS=15`, `XP_STREAK_DAY=20`, `XP_PERFECT_SESSION=50`. `calculate_xp` (`:47`) addiert Neu-Karten-Bonus.
- **Variable Reward**: `maybe_grant_random_xp_boost` (`:99`) gibt mit 8 % Wahrscheinlichkeit (`XP_BOOST_PROBABILITY`, in Tests via App-Config überschreibbar) +5..25 XP; in `rate_card` eingebunden (`srs_service.py:154`).
- **Karten-Stufen** (`CARD_STAGES`, `:30-42`): 10 Stufen, Schwellen über FSRS-Stability in Tagen (0 = „Neu" bis 365 = „Gemeistert"). `get_card_stage` (`:124`) bildet Stability → (Index 0-9, Name, Farbe).
- **Kana-Mastery-Kontext**: `compute_kana_mastery_context` (`:55`) liefert die Flags für die kana-spezifischen Achievements (5 Vokale ≥ Meister, 50 Hiragana/Katakana ≥ „Vertraut 1").
- **DailyAggregate**: `update_daily_aggregate` (`:156`) führt pro Tag (Tagesgrenze Europe/Zurich, konsistent mit Streak) Reviews/Korrekt/Rating-Counts/Zeit/XP/Level-Ups.
- **Streak & Level** (`app/models.py`): `update_streak` (`:63`) mit Streak-Freeze (1× pro Woche, aus `UserSRSSettings`), Tagesgrenze Europe/Zurich. `add_xp` (`:98`) erhöht `total_xp` und levelt hoch, solange `total_xp >= xp_for_next_level` (polynomial `100*level**1.5`). `level_title` liefert japanisch-thematische Titel.
- **Achievements** (`achievements.py`): 24 Definitionen im Code (Kategorien konsistenz/volumen/meisterschaft/session/level), je mit `check`-Lambda. `check_achievements(user, context)` (`:223`) prüft alle nicht freigeschalteten und legt neue `UserAchievement`-Zeilen an. Aufruf zentral in `/api/srs/rate` (`srs_routes.py:66`).

## JavaScript

- **`app/static/js/kana_grid_game.js`** (1'274 Zeilen): drei global definierte Alpine-Builder. `kanaGridGame(contentId)` (`:4`) ist das Lektions-interne Drag-/Tap-Spiel (lädt `/api/kana-grid/<id>/config`, TTS, Confusion-Logging, Rating). `kanaSettings()` (`:869`) treibt die Einstellungs-Seite und die Live-Vorschau-Zählung. `kanaGameView()` (`:1007`) treibt die geteilte Spiel-Bühne (`_kana_game_stage.html`) — wählt Endpoint je Modus (session/public/confusion/daily-challenge), zeigt Timer/Sterne/Hints und korrektives Fehler-Feedback. Exporte am Ende (`:1273-1274`).
- **`app/static/js/kana_storm.js`** (658 Zeilen): `kanaStormGame(opts)` (`:89`) — Arcade-Loop + Daily-Karte. Datenquelle `/api/practice/kana/session/public` (Storm) bzw. `/api/practice/kana/storm-daily` (Daily). Romaji-Akzeptanz-Schicht (`KANA_STORM_ROMAJI_VARIANTS`) über die einwertige DB-`romanization`. Bestscore/Statistik nur im `localStorage` (Privatmodus-sicher), keine DB-Persistenz.

## Zusammenspiel

ASCII-Skizze der wichtigsten Aufruf-Beziehungen:

```
  Seite (Template/JS)                  →  srs_bp-Endpoint                       →  Service
  ─────────────────────────────────────────────────────────────────────────────────────
  review.html (JS-Loop)                →  /api/srs/due, /api/srs/rate           →  srs_service.rate_card
                                          /api/srs/preview, /api/srs/stats          + gamification + achievements
  stats.html (11 fetch parallel)       →  /api/srs/stats/*, /jlpt-progress,     →  srs_service.get_* / get_jlpt_progress
                                          /achievements, card/suspend|reset
  browse.html                          →  /api/srs/browse, /card/<id>/detail,   →  srs_service.browse_cards / get_card_detail
                                          /bulk-action, /browse/export
  practice_kana.html (kanaSettings)    →  /api/practice/kana/session[/public]   →  _guest_scope_payload / freigeschaltete Kana
  practice_kana_game.html (kanaGameView) → /confusion, /daily-challenge,        →  kana_confusion / kana_rows + _kana_item
                                           /session[/public], /api/srs/rate,        srs_service.rate_card
                                           /api/srs/kana-confusion
  practice_kana_storm.html (storm)     →  /session/public, /storm-daily         →  _guest_kana_rows (global, kein User)
  _kana_game_embed_layout.html (iframe)→  /session/public (+ challenge=daily)   →  Gast-Scope
  lesson_view.html (kanaGridGame)      →  /api/kana-grid/<id>/config,           →  KanaGridConfig + Lesson.is_accessible_to_user
                                          /api/srs/rate
```

Eingehende Daten/Aufrufe:
- **Lesson-/Content-Subsystem**: `LessonContent` (Typen kana/kanji/vocabulary/grammar) ist die Karten-Quelle; `Lesson.is_accessible_to_user` regelt den Zugriff aufs Lektions-Grid; `UserLessonProgress.is_completed` bestimmt freigeschaltete Kana (`_user_unlocked_kana_ids`).
- **Referenzdaten**: `Kana`, `Kanji`, `Vocabulary`, `Grammar` liefern Vorder-/Rückseiten-Inhalt.
- **TTS-Subsystem**: Karten- und Spiel-Audio über `/api/tts` (in `routes.py`, ausserhalb dieses Docs).

Ausgehende Links/Redirects:
- Navigation aus `practice_kana.html` → `/practice/kana/storm` (CTA) und Registrierung `routes.register?next=…`.
- `/daily` als teilbare Kurz-URL auf die Storm-Seite (Daily-Tab).
- Startseite (`index.html`) bindet `_kana_storm_stage.html` inline ein und nutzt das iframe-Embed `/practice/kana/embed` (Gast-Hero).
- Streak/XP/Level wirken auf das User-Modell zurück und werden in der Top-Nav (Due-Badge) und auf `/review/stats` sichtbar.

## Beobachtungen (Ansatzpunkte)

- `app/srs_routes.py` ist 1'480 Zeilen und vermischt 8 render_template-Seiten, 33 JSON-/Hilfs-Routen, mehrere Gast-Helfer (`_guest_*`) und SQL-Aggregationen in einer Datei.
- Mehrere Statistik-Routen enthalten ihre SQLAlchemy-Query-Logik direkt im View statt im Service (z. B. `/api/srs/stats/kana-heatmap` `:478-538`, `/api/srs/stats/kana-weak` `:541-600`), während andere Statistik-Routen an `srs_service` delegieren — uneinheitliche Schichtung.
- Imports erfolgen vielfach funktionslokal (z. B. `from app.models import …` innerhalb der Route-Funktionen), nicht auf Modulebene.
- Die Tagesgrenze ist nicht einheitlich: Streak und `DailyReviewAggregate` nutzen Europe/Zurich (`models.py:70`, `gamification_service.py:163`), während `due_date` (`srs_service.py`) und die Daily-Bretter (`/storm-daily`, `/daily-challenge`) `datetime.utcnow()`/`date.today()` in Server-Zeit verwenden (Kommentar `:1147` weist explizit auf UTC-Tagesgrenze hin).
- `get_card_stage` definiert 10 Stufen (Index 0-9) mit je eigener Stability-Schwelle (0 bis 365 Tage, jede Schwelle genau einmal); `mastered` ist Stage-Index 9 (Schwelle 365 Tage), gesetzt in `rate_card` (`srs_service.py:162`).
- `practice_kana.html` (400) und `practice_kana_game.html` (222) tragen umfangreiches Inline-CSS im `styles`-Block; `review.html` (2'000) und `stats.html` (934) sind grosse Templates mit eingebettetem JS.
- Achievements sind im Code definiert (kein DB-Schema) — Änderungen ohne Migration, aber auch ohne Admin-UI; die DB hält nur freigeschaltete Keys.
- Web-Push-Endpoints (`/api/user/push-(un)subscribe`) speichern/löschen nur die Subscription; ein Versand-Pfad ist in diesem Subsystem nicht vorhanden (laut Projekt-Memory toter Code).
- `KanaGridConfig.kana_ids`-Reihenfolge wird im View manuell rekonstruiert, weil die DB-Reihenfolge nicht garantiert ist (`srs_routes.py:1429-1431`).
- Gast- und Login-Sessions duplizieren Filter-Parsing (`mode`/`schrift`/`rows`/`dakuten`) in `/api/practice/kana/session` und `.../session/public`.
