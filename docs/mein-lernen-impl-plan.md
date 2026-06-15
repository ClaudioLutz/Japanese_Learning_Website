# „Mein Lernen" — Implementierungsplan (maximal parallel)

Integration des Standalone-Prototyps `learner_dashboard_prototype.html` (1625 Z.,
Alpine.js + Chart.js + Ink-on-Washi) als echte Flask-Seite **/mein-lernen**.

Quelle der Analyse: 6 parallele Code-Recherche-Agenten (alle Befunde `file:line`-belegt),
Synthese 2026-06-15. Verwandt: `docs/ist-zustand/` (SRS/Stats-Architektur),
Memory `project_dashboard_hybrid_prototyp`, `project_dashboard_tech_recherche`.

## Leitidee — drei Entkopplungs-Hebel
1. **Spine zuerst** (seriell, klein): Route + Skelett + Nav + technische Stolpersteine
   lösen. Danach schreibt jeder Track in **seine eigene Datei**.
2. **Eingefrorener Daten-Vertrag** (`docs/dashboard_contract.md`): exakte JSON-/Context-
   Form jedes Felds + Mock-Fixture. Ab da arbeiten FE (rendert gegen Mock) und BE
   (baut gegen Vertrag) **unabhängig**.
3. **1 Sektion = 1 Jinja-Partial = 1 Track**, **1 Endpoint = 1 neue Funktion in neuer
   Datei**. Umgeht die Hotspots `base.html`, `srs_routes.py`, `srs_service.py`, `routes.py`.

> Architektur-Entscheid: eigenes `dashboard_bp` (`app/dashboard_routes.py`) +
> `app/dashboard_service.py` statt Anhängen an `srs_bp`. `__init__.py` wird genau
> einmal im Spine angefasst; danach hat jeder Endpoint-Track eine eigene Datei.

## Phase 0 — Spine (seriell) — STATUS: umgesetzt
| ID | Aufgabe | Dateien | Status |
|---|---|---|---|
| S1 | `dashboard_bp` + Route `/mein-lernen` (kein `@login_required`, Gast-Gate) | `app/dashboard_routes.py`, `app/__init__.py` | ✅ |
| S2 | Gast-Teaser-Key `'dashboard'` | `app/templates/review_teaser.html` | ✅ |
| S3 | Template-Orchestrator + 7 Sektions-Partials | `app/templates/learner_dashboard.html`, `app/templates/mein_lernen/_*.html` | ✅ |
| S4 | Nav-Link „Mein Lernen" | `app/templates/base.html` (User-Dropdown) | ✅ |
| S5 | Alpine-Plugin-Ladereihenfolge (collapse+intersect OHNE `defer` vor deferred Core) | `learner_dashboard.html` | ✅ |
| S6 | Kanonischer Reife-Bucket-Mapper `maturity_bucket()` (Single Source) | `app/gamification_service.py` (+ Refactor `srs_service.get_maturity_distribution`) | ✅ |
| S7 | Daten-Vertrag + Plan-Doku + Mock | `docs/dashboard_contract.md`, diese Datei, `app/static/dev/dashboard_mock.json` | ✅ |

**Gelöste Stolpersteine:** Radius-Konflikt (Prototyp 8/12/16 vs. custom.css 12/16/24) →
Tokens hermetisch auf `.mein-lernen` re-deklariert, null globale Wirkung. Token-Namen
(`--error` → vorhanden als hermetischer Wert). Bootstrap-Kollisionen (`.card`/`.modal`/
`.toast`/`.badge`) → alle Selektoren unter `.mein-lernen` gescopt, Dialoge mit eigenem
`.mein-lernen-modal/-toast/-stamp`-Präfix. Chart.js NIE in reaktivem Alpine-State.

## Phase 1 — Parallele Tracks (gegen den eingefrorenen Vertrag)

### Frontend (je eigenes Partial, hängen nur am Skelett + Mock)
`_today_hero` · `_compass` · `_cando` · `_stats_tabs` · `_numbers` · `_dialogs` · `_js_dashboard`
— im Spine als Dummy-Port angelegt; Phase 1 = Dummy → echte Daten verdrahten.

### Backend (je neue Funktion in `dashboard_service.py` + Endpoint in `dashboard_routes.py` + eigene Testdatei)
| ID | Liefert | Status-Mix |
|---|---|---|
| BE-compass | `maturityByType` + Säulen-Totale + Server-Context `pillars[]` | EXTEND |
| BE-glyphs | generischer per-Item-Accuracy-Join → `/api/dashboard/compass-glyphs?type=` | NEW (kana existiert) |
| BE-confusion | `confusionPairs` aus `KanaConfusion` + kuratierte Notes | NEW |
| BE-tempo | `kpi` + `reviewsByWeek`/`accuracyByWeek`/`reviewsByWeekday` | NEW (Datenbasis da) |
| BE-retention | `retention.{neu,jung,reif}` (Reife-Achse) | NEW |
| BE-accstage | `accByStage[5]` | NEW (Entscheidung: Approx. vs. Migration) |
| BE-jlpt-gram | `get_jlpt_progress` + Grammatik | EXTEND (berührt `srs_service.py`) |
| BE-records | `records` (Bester Tag = MAX `DailyReviewAggregate.total_reviews`) | EXTEND |
| BE-resume | Resume/Next-Logik aus `routes.py:944-959` in Helper extrahieren | EXTEND (berührt `routes.py`) |
| BE-plan | adaptiver Plan-Builder (due + resume + weak → 3 Schritte) | NEW (hängt an BE-resume) |
| BE-weekgoal | aktive CH-Tage laufende Woche (`time_utils`) + `freezes` exponieren | NEW |

### EXISTS (nur Frontend-Reshape — kein BE-Code)
`weakKana` (`/api/srs/stats/kana-weak`) · `leeches` (`/leeches`) · `accBySkill` (`/content-type`) ·
`heatmap` · `forecast?days=14` · `kanaRows` (`/kana-heatmap` + Reihen-Gruppierung) ·
JLPT Vokabeln/Kanji (`/api/srs/jlpt-progress`) · `milestones` (`/api/srs/achievements`) ·
Readiness-Ring/Band/Gate/Zonen (clientseitig aus `pillars.dist`) · Item-Dialog (clientseitig).

## Konfliktkarte (geteilte Dateien — minimiert)
| Datei | Wer | Strategie |
|---|---|---|
| `app/__init__.py` | nur S1 | 1× registriert |
| `app/base.html` | nur S4 | Nav-Link klein/früh |
| `app/routes.py` | nur BE-resume | Helper früh + isoliert mergen |
| `app/srs_service.py` | nur BE-jlpt-gram | ans Dateiende |
| `app/gamification_service.py` | nur S6 | Mapper, danach read-only |
| `migrations/` | nur falls accByStage/vocabThemes Migration | genau 1 Alembic-Head |

## Entscheidungspunkte — VERRIEGELT (User, 2026-06-15)
1. **Hören-Säule/listen** → **V1 ausblenden.** `listen` raus aus `pillars`, `listenSkills`,
   maturity-Hören, JLPT-Hören-Balken. Readiness-Mathe anpassen: ohne axisB ist
   `readiness = axisA` (kein `gateWarning`, kein `.3*axisB`-Term). Später eigenes Feature.
2. **vocabThemes** → **aus `LessonCategory` ableiten** (echt, gröber; keine erfundenen Etappenziele).
3. **accByStage** → **Migration: Stufe pro Review mitloggen.** Neue Spalte an `ReviewLog`
   (Stufe zum Review-Zeitpunkt), füllt sich ab jetzt; Altdaten fehlen → Chart zeigt nur
   Daten seit Einführung (entsprechend labeln). = der eine serielle Migrations-Punkt.
4. **canDo** → **kuratierte Claude-Liste + Status aus `UserLessonProgress`** (done/prog/open
   abgeleitet). Kein LLM-API.
5. **freezes** → **Anzeige auf 0/1 cappen** (kein Logik-Umbau).

## Top-Fallstricke
- Alpine-Plugin-Reihenfolge (gelöst, nicht auf `defer` umstellen).
- SQLite-Test vs. Postgres-Prod: neue Aggregate dialektneutral (in Python aggregieren statt `date_trunc`).
- `acc` = historische Accuracy, NICHT FSRS-Retrievability — Begriff im Item-Dialog vor Go-Live klären.
- Eine kanonische Stage→5-Bucket-Funktion (S6) — sonst driften Ring und Reife-Tab.

## Tests/Deploy
Tests laufen **pro Track** (eigene Datei, sonst senkt ein ungetesteter Endpoint die Coverage
`fail_under=35` und blockiert alle Merges). Finales serielles Gate: volle `pytest`-Suite +
`ruff` + Playwright-MCP-Visual (Charts lazy, kein „Max call stack", 0 Console-Errors), dann
Deploy `ssh hp-ubuntu` (`docker compose build web && up -d --no-deps web`) + `curl` 200.
Prod-Stand vorher prüfen (Dev-DB ≠ Prod-DB).
