# 03 · Öffentliche & Navigations-Seiten
_Stand: 2026-06-14 · Commit 2947710 · Teil der Ist-Zustand-Dokumentation_

## Zweck

Dieses Subsystem umfasst alle benutzersichtbaren Marketing-, Katalog-, Lernpfad- und Rechts-Seiten der Plattform — also alles, was ein Besucher vor und neben dem eigentlichen Lektions-Viewer (Doc 04) und dem SRS-/Practice-Bereich (Doc 05) sieht. Schwerpunkte sind die rollenbasierte Startseite (Gast = Kana-Storm-Hero, eingeloggt = Weiterlern-Hero), der N5-Lernpfad (`/learn/n5` + Modul-Detailseiten), der nach Kategorien gruppierte Lektions-Katalog (`/lessons`), Kurs-Übersichten sowie SEO-Landingpages und die rechtlichen Pflichtseiten. Alle Seiten teilen sich `base.html` (Top-Nav, Footer, Meta-Tags).

## Komponenten

| Datei | Zeilen | Rolle |
|---|---|---|
| `app/routes.py` | 4'863 | Enthält die meisten öffentlichen Views (zeilengenau referenziert unten); vermischt Views + APIs + Admin |
| `app/legal_routes.py` | 58 | Blueprint `legal` (`url_prefix=/legal`) für Impressum/Datenschutz/AGB/Widerruf |
| `app/__init__.py` | — | Error-Handler (404/500), Context-Processor (`n5_free_lesson_count`, `show_bundle_hint`, SEO-Defaults) |
| `app/templates/base.html` | 756 | Layout: Top-Nav, Mobile-Bottom-Nav, Footer, SEO-Meta/JSON-LD-Blocks |
| `app/templates/index.html` | — | Startseite, rollenbasiert (Gast-Spiel-Hero / eingeloggt-Hero) |
| `app/templates/learn_n5.html` | 212 | N5-Hub-Seite (`/learn/n5`) |
| `app/templates/module_detail.html` | 240 | Modul-Übersicht (`/learn/n5/<slug>`) |
| `app/templates/learn_path.html` | — | **Verwaiste Vorlage** — von keiner Route gerendert (zu prüfen) |
| `app/templates/lessons.html` | — | Lektions-Katalog, rollenbasiert + nach Kategorie gruppiert |
| `app/templates/courses.html` | 252 | Kurs-Übersicht (JS-befüllt via `/api/courses`) |
| `app/templates/course_view.html` | 435 | Einzelkurs-Detail |
| `app/templates/my_lessons.html` | 485 | Gekaufte Lektionen (login-pflichtig) |
| `app/templates/ueber.html` | 238 | About / Founder-Story (E-E-A-T) |
| `app/templates/lernmethode.html` | 155 | SRS/FSRS-Erklärseite |
| `app/templates/jlpt_n5_schweiz.html` | 770 | SEO-Landing „JLPT N5 Schweiz" |
| `app/templates/legal/{impressum,datenschutz,agb,widerruf}.html` | — | Rechtstexte |
| `app/templates/errors/{404,500}.html` | 27/27 | Fehlerseiten (deutsch) |

## Seiten-Inventar

### Startseite & Redirect

| Seite | Route + Zeile | Template | Zielgruppe | Zweck |
|---|---|---|---|---|
| Startseite | `/` · `app/routes.py:405` | `index.html` | beide (verzweigt) | Hero + N5-Lernpfad + Marketing |
| /home | `/home` · `app/routes.py:305` | — (301-Redirect) | beide | 301 auf `/` (`url_for('routes.index')`) — bündelt Ranking-Signale, behebt GSC-Duplikat |

**`/` — rollenbasierte Verzweigung** (`index.html`):
- **Gast** (`not current_user.is_authenticated`): Hero ist die **Kana-Storm-Spielbühne** — inline (kein iframe) via `{% include '_kana_storm_stage.html' %}` + `_kana_storm_styles.html`. H1 „Hiragana lernen — fang mit einer Runde an." Darunter: Brücken-Leiste (3 Schritte: Spielen → Hiragana-Lektion gratis → N5-Pfad), Aktionszeile mit „Kostenlos starten" + „N5 Komplett · CHF 9.90", Geld-zurück-Note, „Alle Lektionen ansehen". Danach eine „Vom Spiel zum System"-Sektion (Pitch/USP/Trust-Block, nur Gast). Link unter dem Spiel führt zum Matching-Spiel (`srs.practice_kana_page`).
- **Eingeloggt**: personalisierter Hero. Bei vorhandener letzter Lektion (`last_lesson`) H1 „Weiter lernen." + Button „▶ {Titel}"; sonst „Bereit für deine erste Lektion?" + „Dein Start"-Strip. Begrüssung mit Username + Streak. Versteckter „N Karten wiederholen"-Link (per JS eingeblendet).
- **Gemeinsame Sektion (beide)**: `#lernpfad` — vertikaler Sumi-Pfad aus 3 didaktischen Gruppen (Schreibsystem / Grundwortschatz / Erste Sätze) mit Modul-Stationen, Donut-Fortschritt, Hanko-Markierung des empfohlenen nächsten Moduls (`next_module_id`). Bundle-Hinweis erscheint, wenn `show_bundle_hint`.

**Gelesene Daten (`index`, `app/routes.py:405-488`)**: `Lesson`-Counts je Sprache (published / guest+free), `Course`-Count, letzter `UserLessonProgress` (für `last_lesson`), `_build_n5_path_context()` (`app/routes.py:328` — baut Module aus `LessonCategory.query.filter_by(jlpt_level=5)`, pro Modul `completion_for_user`/`is_unlocked_for_user`), `Vocabulary`/`Kanji`-Counts (jlpt_level=5), `coverage_service.get_jlpt_coverage(5)`.

**Haupt-CTAs**: `guest_lesson_url` (= erste gratis+guest Lektion via `_first_guest_lesson`, sonst `routes.lessons?access=free`), `bundle.n5_bundle`, `#lernpfad`, `routes.ueber`, eingeloggt: `routes.view_lesson`, `srs.review_page`.

### Lernpfad

| Seite | Route + Zeile | Template | Zielgruppe | Zweck |
|---|---|---|---|---|
| Lernpfad-Hub | `/learn` + `/learn/n<level>` · `app/routes.py:999` | `learn_n5.html` | beide | Indexierbare N5-Hub-Seite (Module + Pfad + Bundle-CTA) |
| Modul-Detail | `/learn/n<level>/<slug>` · `app/routes.py:1049` | `module_detail.html` | beide | Modul-Übersicht: Lessons mit Status/Coverage/Direktstart |

- **`learn_path()`** (`app/routes.py:999`): Nur `level==5` rendert `learn_n5.html` (mit `_build_n5_path_context` + Coverage). `level in (1,2,3,4)` → `abort(404)` (N4+ inhaltlich noch nicht vorhanden); jeder andere Level ebenfalls 404. **Hinweis:** Die Funktion heisst `learn_path`, rendert aber `learn_n5.html`, nicht das Template `learn_path.html`.
- **`module_detail()`** (`app/routes.py:1049`): Lädt `LessonCategory` per `(jlpt_level, slug)` (`first_or_404`). Bei genau 1 publishter Lektion → direkter Redirect auf `routes.view_lesson` (Klick-Friction sparen). Sonst Übersicht mit `is_accessible_to_user`, `UserLessonProgress`, Bundle-Besitzstatus (`bundle_service.get_n5_bundle_course` + `CoursePurchase`), `completion_for_user`. CTAs: `routes.view_lesson`, `bundle.n5_bundle`, Breadcrumb zu `/` + `/#lernpfad`.

### Katalog

| Seite | Route + Zeile | Template | Zielgruppe | Zweck |
|---|---|---|---|---|
| Lektions-Katalog | `/lessons` · `app/routes.py:782` | `lessons.html` | beide (verzweigt) | Rollenbasiert: Weiterlern-Dashboard (eingeloggt) / Gast-Hero + gruppierter Browse |
| Kurse | `/courses` · `app/routes.py:1120` | `courses.html` | beide | Kurs-Übersicht |
| Einzelkurs | `/course/<id>` · `app/routes.py:1184` | `course_view.html` | beide | Kurs-Detail mit Lektionen + Kauf-Status |
| Meine Lektionen | `/my-lessons` · `app/routes.py:1126` | `my_lessons.html` | eingeloggt (`@login_required`) | Gekaufte/freigeschaltete Lektionen + Statistik |

**`/lessons` — Verzweigung + Gruppierungslogik** (`app/routes.py:782-964`):
- **Vollständig server-gerendert** (SSR): Alle publishten Lektionen in `visible_langs` werden vorgeladen; Filtern/Sortieren/View-Toggle macht der Client per JS (`x-data="lessonsPage()"`) auf den bereits gerenderten Karten — kein Folge-Fetch.
- **`lp-cat-group` (Gruppierung)**: `all_categories` werden nach `jlpt_level desc, display_order asc, id asc` sortiert. Pro Kategorie werden die publishten Lektionen (in `visible_langs`) nach `(order_index, id)` = Lehrplan-Reihenfolge sortiert und als `lesson_dict` aufbereitet. Pro Gruppe `lesson_count`, `free_count`, `done_count`. Im Template ist jede Gruppe ein `<section class="lp-cat-group">` mit Kopf (Icon/Name/Beschreibung) + Meta-Zähler (`{{ cat.done_count }}/{{ cat.lesson_count }} fertig` bzw. `… · {{ cat.free_count }} gratis`). Lektionen **ohne sichtbare Kategorie** landen als Auffanggruppe „Weitere Lektionen" (id 0) am Ende, damit keine Lektion aus dem Katalog fällt.
- **Eingeloggt** (`show_status`): Oben ein Weiterlern-Dashboard (`lp-continue`). `continue_lesson` = zuletzt begonnene, nicht abgeschlossene Lektion (`status=='started'`, neuestes `last_accessed`); Fallback erste offene im Pfad (`nxt`). Stat-Schiene: `total_done`/Lektionen, Streak (`current_user.current_streak`), fällige Karten (`srs_service.get_due_count`).
- **Gast**: Hero `lp-hero` mit Titel + Lektions-/Themen-Zähler. CTA „Gratis starten — {total_free} Lektionen" → `first_free_lesson` (erste gratis+guest), sonst → `routes.register`. Sekundär „Alles freischalten · CHF 9.90" → `bundle.n5_bundle`.
- **`status`-Logik je Lektion**: `done` (Progress completed) / `started` (pct>0) / `open`. Gäste bekommen leere Progress-Map → alles `open`.
- **Gelesene Daten**: `UserLessonProgress` (alle des Users in einer Query), `LessonCategory` + deren `lessons`, `Lesson` (Orphan-Auffang), `srs_service.get_due_count`. JSON-LD: `ItemList` (alle `page_lessons` als `Course`) + `BreadcrumbList`.

**`/courses`** (`app/routes.py:1120`): Route lädt `Course.query.filter_by(is_published=True)` und übergibt `courses` an `courses.html`. **Das Template nutzt diese Variable jedoch nicht**, sondern befüllt das Grid per jQuery `$.get('/api/courses')` (`courses.html:112`) — der initiale Hero zeigt Lade-Spinner, Stat-Zahlen stehen auf „-". CTAs ergeben sich aus den JS-Karten (Kurs-Detail). `/api/courses` (`app/routes.py:3062`) liefert publishte Kurse inkl. `lessons`-Liste + `is_purchased`.

**`/course/<id>`** (`app/routes.py:1184`): Lädt `Course` (`get_or_404`), Kaufstatus (`CoursePurchase`), pro Lektion `UserLessonProgress` (Fortschritt/Abschluss), Gesamt-Fortschritt %, Ø-Schwierigkeit, Gesamtdauer. CTA: Start in erste Lektion (`routes.view_lesson`), Lektions-Links nur wenn `not is_purchasable or has_purchased`.

**`/my-lessons`** (`app/routes.py:1126`, `@login_required`): Aggregiert `LessonPurchase` (Einzelkäufe) + `CoursePurchase` (kursweise freigeschaltete Lektionen, dedupliziert via `seen_lesson_ids`). Berechnet `total_spent`, `completed_count`, `completion_rate`, `total_time_spent` aus `UserLessonProgress`. CTAs: `routes.view_lesson` je Lektion, „Lektionen entdecken" → `routes.lessons`.

### Marketing / SEO-Landings

| Seite | Route + Zeile | Template | Zielgruppe | Zweck |
|---|---|---|---|---|
| Über uns | `/ueber` · `app/routes.py:967` | `ueber.html` | beide | Founder-Story, „Warum Deutsch", E-E-A-T |
| Lernmethode | `/lernmethode` · `app/routes.py:978` | `lernmethode.html` | beide | SRS/FSRS erklärt (vs. Anki SM-2) |
| JLPT N5 Schweiz | `/jlpt-n5-schweiz` · `app/routes.py:988` | `jlpt_n5_schweiz.html` | beide | SEO-Landing: Prüfungs-Infos (UZH) + Curriculum |

Alle drei Routen sind reine `render_template`-Aufrufe ohne DB-Query im View; `n5_free_lesson_count` kommt aus dem Context-Processor.

- **`ueber.html`** (238 Z.): Sektionen Gründer-Story, „Data Science + Sprachenlernen", „Warum Deutsch?", „Wie ich Inhalte baue", „Was als Nächstes". CTAs: `/#lernpfad`, `bundle.n5_bundle`, `routes.lernmethode`. Gratis-CTA nutzt `n5_free_lesson_count`.
- **`lernmethode.html`** (155 Z.): Sektionen „Was ist Spaced Repetition", „FSRS vs. SM-2", „Wie es hier funktioniert", „Selbst testen". CTAs: `/#lernpfad`, `bundle.n5_bundle`. „N Gratis-Lektionen starten" via `n5_free_lesson_count`.
- **`jlpt_n5_schweiz.html`** (770 Z.): Breadcrumb + H1 + Hero-CTAs, Sektionen „Was ist JLPT N5", „JLPT in der Schweiz (Termine/Ort/Anmeldung)", „Wie wir vorbereiten", „Dein Lernpfad", FAQ, „Wer steht dahinter". Strukturierte Daten: Course + FAQPage + BreadcrumbList. CTAs: `routes.lessons?access=free`, `bundle.n5_bundle`, `routes.lernmethode`, `routes.ueber`.

### Rechtliches (Blueprint `legal`)

| Seite | Route | Template | Zielgruppe |
|---|---|---|---|
| Impressum | `/legal/impressum` · `app/legal_routes.py:41` | `legal/impressum.html` | beide |
| Datenschutz | `/legal/datenschutz` · `app/legal_routes.py:46` | `legal/datenschutz.html` | beide |
| AGB | `/legal/agb` · `app/legal_routes.py:51` | `legal/agb.html` | beide |
| Widerruf | `/legal/widerruf` · `app/legal_routes.py:56` | `legal/widerruf.html` | beide |

Alle vier rendern mit gemeinsamem `_ctx()` (`app/legal_routes.py:24`): Anbieter-Daten aus Env-Variablen mit Defaults (`LEGAL_OWNER_NAME`=„Claudio Lutz", Strasse „Promenadenstrasse 72", PLZ „9400", Ort „Rorschach", `LEGAL_EMAIL`=„info@japanese-learning.ch", optional `LEGAL_UID`) + deutsches Datum `today_de`.

### Fehlerseiten

| Seite | Registrierung | Template | robots-Block |
|---|---|---|---|
| 404 | `@app.errorhandler(404)` · `app/__init__.py:288` | `errors/404.html` | `noindex,follow` |
| 500 | `@app.errorhandler(500)` · `app/__init__.py:291` | `errors/500.html` | `noindex,nofollow` |

Beide erben `base.html`, im Ink-on-Washi-Stil (404: Kanji 迷, 500: 壊). CTAs: „Zur Startseite", 404 zusätzlich „Alle Lektionen" (`routes.lessons`), 500 zusätzlich „Problem melden" (mailto info@).

## Navigation (`base.html`)

**Top-Nav** (`base.html:124`): Brand → `routes.index`. Links: „Lernpfad" (`/#lernpfad`), „Wiederholen" (`srs.review_page`, mit `nav-due-badge`), „Kana üben" (`srs.practice_kana_page`), „Lektionen" (`routes.lessons`), „N5 Komplett" (`bundle.n5_bundle`). Eingeloggt: User-Dropdown (`routes.user_profile`, `routes.my_lessons`, `routes.courses`, `srs.stats_page`, `srs.browse_page`, ggf. `routes.admin_index`, `routes.logout`). Gast: „Anmelden" (`routes.login`) + „Kostenlos starten" (`routes.lessons?access=free`).

**Mobile-Bottom-Nav** (`base.html:630`): Start, Lektionen, Wiederholen (Badge), Kana üben, Profil/Anmelden/Registrieren.

**Footer** (`base.html:736`): `routes.ueber`, `routes.lernmethode`, `routes.jlpt_n5_schweiz`, `legal.impressum`, `legal.datenschutz`, `legal.agb`, `legal.widerruf`, Kontakt-Mailto, Copyright.

## Zusammenspiel

```
                 base.html (Top-Nav · Bottom-Nav · Footer · SEO-Meta/JSON-LD)
                 Context-Processor (__init__.py): site_url, n5_free_lesson_count,
                 show_bundle_hint, canonical, og_image
                                      │  (geerbt von allen Seiten)
   ┌──────────────────────────────────┼───────────────────────────────────┐
   │                                   │                                    │
  /  (index) ──CTA──► guest_lesson  /lessons ──gruppiert──► Lektionen   /learn/n5
   │  │                              │  │                                  │ (learn_n5)
   │  ├─ #lernpfad (Module)          │  ├─ Gast: register / view_lesson    └─► /learn/n5/<slug>
   │  └─ Kana-Storm-Hero             │  └─ eingeloggt: view_lesson /          (module_detail) ──►
   │     └─► srs.practice_kana_page  │     srs.review_page                    view_lesson (Doc 04)
   │                                 │
   └───────── alle "N5 Komplett"-CTAs ──────► bundle.n5_bundle (Doc Bundle/Payment)
```

**Eingehend**: Top-Nav/Bottom-Nav/Footer (aus `base.html`, also von jeder Seite) verlinken auf dieses Subsystem. SEO: `seo_routes.py::sitemap_xml()` listet diese öffentlichen Routen + publishte Lessons/Courses (zu prüfen, ob alle hier dokumentierten statisch eingetragen sind).

**Ausgehend / Übergänge**:
- → **Lektions-Viewer (Doc 04)**: nahezu alle „Start/Weiter"-CTAs zielen auf `routes.view_lesson` (`/lessons/<id>`). `module_detail` redirected bei 1 Lektion direkt dorthin.
- → **SRS/Practice (Doc 05)**: `srs.review_page`, `srs.practice_kana_page`, `srs.stats_page`, `srs.browse_page`; Gast-Hero bettet die Kana-Storm-Stage inline ein.
- → **Bundle/Payment**: `bundle.n5_bundle` (durchgängiger „CHF 9.90"-CTA), `routes.purchase_lesson_page`, `routes.view_course`.
- → **Auth**: Gast-CTAs auf `routes.register` / `routes.login`.

**API-Aufrufe von diesen Seiten**:
- `courses.html` → `GET /api/courses` (`app/routes.py:3062`) — Kurs-Grid client-seitig (jQuery).
- Startseite (Gast) → `GET /api/practice/kana/session/public` (laut Template-Kommentar; Endpoint im SRS-Subsystem, Doc 05) für das Kana-Storm-Spiel.
- `/lessons` lädt **keine** zusätzliche API (alles SSR, JS filtert nur lokal).

## Beobachtungen (Ansatzpunkte)

- `app/routes.py` umfasst 4'863 Zeilen und vermischt öffentliche Views, JSON-APIs und Admin-Endpoints in einer Datei.
- `app/templates/learn_path.html` existiert, wird aber von keiner Route gerendert (kein Treffer auf `learn_path.html` in `app/`); die Route `learn_path()` rendert `learn_n5.html`. Verwaiste Vorlage — Zugehörigkeit zu prüfen.
- `/courses` ist inkonsistent zu `/lessons`: Die Route übergibt `courses` server-seitig, das Template ignoriert das und lädt stattdessen per `$.get('/api/courses')` (`courses.html:112`) — der Initial-HTML zeigt nur Spinner + „-"-Zähler (Soft-404-/SEO-Muster, da Inhalt erst per JS erscheint). `/lessons` und der Lernpfad sind dagegen voll SSR.
- `courses.html` nutzt jQuery (`$.get`), während andere neue Seiten Alpine.js (`x-data`) verwenden — gemischte Frontend-Stacks.
- `module_detail()` redirected bei genau 1 publishter Lektion direkt zum Viewer; bei 0 Lektionen wird die Übersicht ohne Redirect mit leerer Liste gerendert (Zustand „leeres Modul" möglich).
- Die Gratis-Lektions-Zählung (`n5_free_lesson_count`, `__init__.py:315`) summiert `english` + `german` separat — bei aktivem CONTENT_LANGUAGES=nur-Deutsch zählt der englische Teil 0, der Wert spiegelt die Hero-Logik in `index` (guest+free+published je Sprache).
- `index`-View berechnet `n5_modules`/`n5_groups` über `_build_n5_path_context`, das pro Modul `completion_for_user` + `is_unlocked_for_user` aufruft → potenziell viele Einzel-Queries pro Seitenaufruf (N+1-Verdacht, zu prüfen).
- `_build_n5_path_context` enthält fest verdrahtete Slug-Mengen (`SCHREIB_SLUGS`, `GRAMMATIK_SLUGS`) zur Gruppenzuordnung — Kategorien ohne passenden Slug landen automatisch in „Grundwortschatz".
- Marketing-Texte enthalten teils hartkodierte Fallback-Zahlen (`n5_vocab_count or 510`, `n5_kanji_count or 55`, `92 Hiragana & Katakana` in `index.html`), die von den DB-Live-Werten abweichen können.
- `/learn/n<level>` für N1-N4 liefert bewusst 404 (Content fehlt) — die Route ist aber bereits angelegt.
