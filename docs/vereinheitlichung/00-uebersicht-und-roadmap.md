# 00 · Vereinheitlichung — Übersicht & Roadmap

_Stand: 2026-06-20 · Branch `free-mode-umstellung` · japanese-learning.ch_
_Quelle: Multi-Agent-Workflow `vereinheitlichung-plan` (Run `wf_7f2820ea-119`) — 9 Agenten, 5 parallele Inventar-Slices → Synthese → 3 adversariale Completeness-Prüfer. Alle Befunde am Code verifiziert; Critic-Korrekturen eingearbeitet._

## Auftrag

> „Orchestriere dieses Projekt und plane die Umsetzung — **ohne Features zu verlieren**, sondern sie zu **konsolidieren** und die Website zu **vereinheitlichen**."

Deliverable ist **dieser Plan** (kein deployter Code). Drei Dokumente:
- **00** (dies) — Lage, Ziel, Oberflächen-Konsolidierung, 6-Phasen-Roadmap, offene Entscheidungen, QA-Gate.
- **[01 · Feature-Erhaltungs-Matrix](01-feature-erhaltungs-matrix.md)** — das No-Loss-Rückgrat: 103 Feature-Zeilen → je genau eine Ziel-Fläche.
- **[02 · Inkonsistenz-Katalog + Ziel-Designsystem](02-inkonsistenz-katalog.md)** — 16 Inkonsistenzen + die Soll-Spezifikation.

## Die Diagnose: kein fehlendes Design, sondern gewachsene Patches

Die **Ink-on-Washi-Designsprache steht fest und ist vollständig kodifiziert** (Skill `japanese-learning-design-system` mit `colors_and_type.css`, UI-Kits, „5 Regeln"; Font Awesome 6 solid; あ-Klee-One-Logo). Der „Fleckenteppich" entstand **nicht** aus fehlender Sprache, sondern weil **jede Erneuerung als eigener Patch** kam — Dark Mode, Mein-Lernen-Dashboard, Stats-/Lessons-Redesign, Kana-Storm/Daily, /pruefen, Free Mode — und dabei eigene Token-Dialekte, halbe Dark-Mode-Abdeckung und überlappende Oberflächen hinterliess.

**Konsequenz für den Plan:** Er **erfindet kein neues Design** — er **kodifiziert + migriert** in die bestehende Sprache. Kein Design-Tournament.

Die vier strukturellen Fleckenteppich-Muster:
1. **Token-Fragmentierung** — Doppel-`:root` in custom.css (Z. 11 + 62); ein Partial (`_ml_styles.html`) re-deklariert hermetisch den ganzen Token-Satz; 3 untracked Prototypen mit 3 Vokabularen (nur `learner_dashboard` = on-system).
2. **Dark-Mode-Lückenhaftigkeit** — `docs/design-review-darkmode-2026-06-19.md` ist ein 112-Funde-Katalog: Dutzende Flächen hartcodieren `#fff`/Hex ohne `[data-theme=dark]`-Pendant.
3. **Bootstrap-Defaults & Off-Brand-Akzente** sickern durch — Periwinkle `#667eea`, Indigo, Blau `#0d6efd` statt der einen Akzentfarbe Shu.
4. **Oberflächen-/IA-Überlappung** — 6 Lektions-/Katalog-Flächen, 3+ Kana-Flächen, drei redundante eingeloggte „Lern-Heimaten" (index-Hero / /lessons / /mein-lernen).

## Ziel-Designsystem (Kurzfassung)

Vollständige Spec → [02](02-inkonsistenz-katalog.md#ziel-designsystem--spezifikation-critic-korrigiert). Kern:
- **Eine Token-Quelle:** ein zusammengeführtes `:root` in custom.css; `colors_and_type.css` als Spiegel. Lint: kein Partial deklariert Brand-Tokens neu.
- **Eine Dark-Regel (strukturell):** „keine Hardcodes, nur Tokens" → der **eine** globale `[data-theme=dark]`-Flip deckt alles automatisch. Per-Block-Dark nur als schmale Ausnahme (nicht als Gesetz).
- **Eine Akzentfarbe:** Vermillion (Shu) als einziger gesättigter Brennpunkt; alles andere warme Neutrale.
- **Eine Icon-Quelle:** Font Awesome 6 solid; Tabler raus.
- **Geteilte Komponenten** statt Pro-Seite-Duplikate (Pfad-Makro, Bundle-CTA-Makro, Matching-Partial, Quiz-Partial, Kana-Engine, Flip-/Review-Karten mit geschützter Deck-Invariante).

## Oberflächen-Konsolidierung (Ziel-IA)

| Cluster | Heute | Aktion | Ziel |
|---|---|---|---|
| **Lektions-/Katalog (6)** | `/ #lernpfad`, `/learn/n5`, `/learn/n5/<slug>`, `/lessons`, `/courses`, `/course/<id>` | klar trennen | `/` = Marketing+Pfad-Teaser · `/learn/n5` = SEO-Hub · `/lessons` = **reiner Katalog** (Dashboard-Rolle wandert weg) · `/courses` = Kurs-Ebene. **Ein** geteiltes Pfad-/Modul-Makro. |
| **Kana (3+)** | `/practice/kana`, `/practice/kana/spiel`, `/practice/kana/storm`, `/daily`, `/embed` (tot), Lektions-Grid | **merge** | **Ein** „Kana üben"-Dach unter `/practice/kana` mit Segment-Tabs [Zuordnung \| Storm]; geteilte Spiel-Engine; `/embed` retire. |
| **review / stats / mein-lernen** | `/review`, `/review/stats`, `/review/browse`, `/mein-lernen` | keep-distinct | `/mein-lernen` = **kanonische Lern-Heimat** · `/review` = SRS-Loop · `/review/stats` = Deep-Dive · `/review/browse` = Karten-Verwaltung. Stat-Logik **einmal** (Helper, kein Drift). |
| **courses** | `/courses`, `/course/<id>` | keep-distinct | Voll SSR (Doku-Drift „jQuery $.get" ist veraltet — verifiziert SSR). Hero-Gradient dark-themen, englische Labels → Deutsch. |
| **/pruefen** | `/pruefen`, `/pruefen/test` (auf main, **nicht** auf Branch) | keep-distinct | Eigenständige öffentliche Prüfungs-Fläche; in IA/Sitemap/Nav aufnehmen; teilt `evaluate_answer` + Tap-to-pair-Matching mit dem Lektions-Quiz. |

## Roadmap (6 Phasen, jede deploybar)

Reihenfolge nach Abhängigkeit: erst gemeinsame Baseline, dann Fundament (Tokens + Dark), dann Komponenten, dann IA, dann Politur, dann (optional) Backend. Feature-IDs verweisen auf [01](01-feature-erhaltungs-matrix.md).

### P0 · Baseline-Reconcile (Rebase auf main)
**Ziel:** gemeinsame Baseline, damit `/pruefen` + `evaluate_answer` vorhanden sind und nicht doppelt gebaut werden.
**Stand verifiziert:** Branch ist **11 hinter / 4 vor** `origin/main`; `/pruefen` (`pruefen_routes.py`, `pruefen.html`, `pruefen_session.html`) liegt auf main, fehlt auf dem Branch.
⚠ **Korrektur:** Der globale `[data-theme=dark] .card`-Fix (B8) ist **bereits auf dem Branch** (`custom.css:4859`) — Rebase-Begründung ist allein `/pruefen` + die übrigen main-Commits, **nicht** dieser Fix.
**Gate:** pytest grün · ruff clean · Playwright-Smoke (`/`, `/lessons`, `/lessons/<id>`, `/review`, `/pruefen`) mobil+desktop, light+dark.

### P1 · Fundament: eine Token-Quelle + Dark-Sammel-Fix + Deck-Invariante
**Ziel:** Token-Fragmentierung beenden, Dark-Blocker schliessen, Deck-Karussell absichern — ohne Feature-Verlust.
**Workstreams:** Doppel-`:root` → ein `:root` (IC-01, `--zen-*`-Kette **re-ankern** statt löschen) · `_ml_styles.html` ent-hermetisieren (IC-02) · Dark-Sammel-Fix B2/B3/B5/B6/B7/B9 + `register.html` (IC-06) · zentraler Bootstrap-Bridge-Block (IC-05, baut auf bestehendem B8-`.card` auf) · `--color-*` aufgespalten mappen (IC-03: Prototyp-Tokens killen, `--color-success/-error` behalten) · **mobile-improvements.css kartieren** (heben/entfernen) · Deck-Invariante `.in-deck{display:none}` als getestete Komponente **vor/während** CSS-Merge sichern.
**Features:** FM-tokens, FM-deck-carousel, FM-darkmode, FM-dashboard-*, FM-stats-deepdive, FM-kana-*, FM-lernmethode, FM-module-detail, FM-n5-path, FM-buttons, FM-footer.
**Gate:** + Playwright-Visual aller Hauptseiten (mobil+desktop, light+dark, AA-Spot) + **Deck-Karussell-Pflichtcheck** (`[Deck]`-Konsole, nur eine Karte sichtbar).

### P2 · Komponenten-Konsolidierung + Akzent-Sanierung
**Ziel:** doppelte/divergente UI-Komponenten zu geteilten Partials/Makros; eine Akzentfarbe (Shu).
**Workstreams:** `_bundle_cta`-Makro (Gating `show_bundle_hint AND not free_mode`) ersetzt >10 Streuorte + schliesst FREE_MODE-Gating-Lücken · `_n5_path`-Pfad-/Modul-Makro · Matching → kanonisch Tap-to-pair `_matching`-Partial (auch in lesson_view) · geteiltes Quiz-Render-Partial (Normal/Conversation/pruefen) · geteilte Kana-Spiel-Engine (Practice + Lektions-Grid = Adapter) · `_kana_storm_stage` aus index-Inline lösen · geteilte Flip-/Review-Karten + ein Front-Romaji-Toggle · Off-Brand-Akzente (#667eea/Indigo/#0d6efd → Shu/--ink-*, IC-04) · Reset-Endpoints → eine ORM-Methode.
**Gate:** + Playwright-Visual (Deck + Matching mobil + Kana-Spiele + Bundle-CTA in FREE_MODE on/off) light+dark.

### P3 · IA-/Oberflächen-Fusion
**Ziel:** redundante Weiterlern-Flächen auflösen, `/mein-lernen` sichtbar machen, `/pruefen` in die IA aufnehmen.
**Workstreams:** `/mein-lernen` = kanonische Lern-Heimat (eine Resume-Quelle); index-Hero + `/lessons` lp-continue → Teaser, die dorthin verlinken (FM-resume — ⚠ Neu-Nutzer-Empty-State + Username/Streak-Begrüssung **bleiben erhalten**) · `/lessons` → reiner Katalog (Orphan-Auffanggruppe bleibt) · `/mein-lernen` in Primary-+Bottom-Nav heben · Stat-Logik in **einen** Helper, Dashboard-Tabs = Kurzform → /review/stats · `/pruefen` in IA/Sitemap/Nav · „Login required"-Substring → Reason-Code (IC-12) · a11y (role=tab/aria-selected, role=button, Touch-Targets ≥44px, IC-13).
**Gate:** + a11y-Audit (Rollen/Kontrast) + Gast-Teaser-Gating-Check.

### P4 · Politur + Dead-Code-Cleanup + Prototyp-Einarbeitung
**Ziel:** letzte Inkonsistenzen schliessen, toten Frontend-Code entfernen, sauberer Git-Status.
**Workstreams:** `learner_dashboard`-Prototyp-Ideen (Reife-Skala `--mat-*`, Audio-Player) in /mein-lernen einarbeiten; `lesson_card_states` + `kana-storm`-Prototyp nur **nach** Token-/FA-/Schrift-Übersetzung (1:1: `--color-*`→Pigment, `ti`→`fas`, `--cream`→`--washi`, `--orange`→`--shu`, Iowan→Geist/Fraunces) · Dead-Code (lessons.css, /embed, learn_path.html, index:902-1039, .welcome-card, fill_blank, Web-Push-Stub) entfernen · 3 untracked Prototypen löschen · Sub-AA-Kontrast-Resterunde (IC-07) · Sprachmix-Reste → Deutsch (IC-12) · Inline-Monolith-Diät + Lint (IC-11) · Klee-One-Import.
**Gate:** + Playwright-Vollrundgang (~16 Seiten light+dark) + `git status` sauber.

### P5 · Backend-Schuld (separat, optional, am Ende — nach Freigabe)
**Ziel:** benannte Backend-/Sicherheitsschuld abbauen, Frontend unverändert. Siehe offene Entscheidung 1.
**Reihenfolge:** (1) **Sicherheit zuerst** — Payrexx-Webhook fail-closed (IC-16), premium-up/downgrade-Proto entfernen, Reset-Token-Einmal-Invalidierung; (2) Doppelpfade — OAuth (zwei → einer, ORM statt Raw-SQL), drei Payment-Factories → eine, PostFinance-Legacy raus; (3) `evaluate_answer` als alleinige Quelle; (4) Gott-Dateien per Blueprint/Service-Schicht entzerren, N+1; (5) Zeitzonen vereinheitlichen, CSP härten, Tailwind-Build statt Play-CDN.
**Gate:** pytest grün · ruff clean · (bei Payment-Reaktivierung) Webhook-Signaturtest · keine Frontend-Visual-Regression.

## Offene Entscheidungen (User)

| # | Frage | Empfehlung |
|---|---|---|
| 1 | **Backend-Schuld in Scope?** | **Separat/später (P5 optional)** — Frontend/UX/IA im Kern. **Ausnahme:** die 3 reinen Sicherheitspunkte (Webhook fail-closed, Reset-Token, premium-Proto) vorziehen — billig + vor jeder Payment-Reaktivierung Pflicht. |
| 2 | **Kanonische eingeloggte Lern-Heimat?** | **`/mein-lernen`** = Lern-Heimat (eine Resume-Quelle), `/lessons` = reiner Katalog, index-Hero/`/lessons`-lp-continue → Teaser. `/mein-lernen` in Primary-/Bottom-Nav heben. Alle 3 Render-Inhalte bleiben erhalten. |
| 3 | **/pruefen eigenständig oder in /review?** | **Eigenständig** (risikofreier Zweck: Fragen erneut testen ohne `UserQuizAnswer`-Schreibung), aber prominent von /review + /mein-lernen verlinkt; teilt Matching + `evaluate_answer`. |
| 4 | **Bezahl-Flächen unter FREE_MODE pflegen?** | **Latent markieren, nicht löschen** (reversibel). Token-Migration mitnehmen (billig), aber **kein** dedizierter Dark-Audit solange FREE_MODE aktiv; vor Reaktivierung nachholen. |
| 5 | **Prototyp-Ideen übernehmen?** | `learner_dashboard` (on-system) in /mein-lernen einarbeiten; aus `lesson_card_states`+`kana-storm` nur **Ideen** nach 1:1-Token-Übersetzung; danach alle 3 untracked Dateien löschen. |

## QA-Gate (gilt pro Phase, CLAUDE.md-konform)

Jede Phase ist erst „fertig", wenn **alle** gelten: **pytest grün** · **ruff clean** · **Playwright-Visual** (mobil+desktop, light+dark, wo relevant) · bei CSS-Änderungen **Deck-Karussell-Pflichtcheck**. Erst dann Deploy via `ssh hp-ubuntu` (`docker compose build web && up -d --no-deps web` + `curl` 200). Prod-Stand vorher prüfen (Dev-DB ≠ Prod-DB).

## Methodik & Vertrauensgrad

5 parallele Inventar-Slices (Marketing/IA · Lektion/Quiz · SRS/Practice/Dashboard · Design-System · Backend) ingestierten die vorhandene Doku (`docs/ist-zustand/`, `dashboard_contract`, `mein-lernen-impl-plan`, `design-review-darkmode`, Design-Skill) und verifizierten Lücken am Code. **199 Roh-Features → 103 konsolidierte Zeilen.** 3 adversariale Prüfer (Feature-Verlust / IA-Vollständigkeit / Design-Kohärenz): alle **pass-with-fixes**; die 4 must-fix + 6 should-fix sind in 00/01/02 eingearbeitet und am Code gegengeprüft (B8 vorhanden, mobile-improvements.css live, `--color-success/-error` live, Branch 11/4 zu main).
