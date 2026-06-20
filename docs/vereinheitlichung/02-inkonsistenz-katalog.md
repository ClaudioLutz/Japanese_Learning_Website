# 02 · Inkonsistenz-Katalog + Ziel-Designsystem
_Aus Workflow `vereinheitlichung-plan` · 16 konsolidierte Inkonsistenzen über 11 Dimensionen · Critic-Korrekturen eingearbeitet._

> **Leitsatz:** Die Ink-on-Washi-Designsprache **steht fest und ist kodifiziert** (Skill `japanese-learning-design-system`, `colors_and_type.css`, UI-Kits). Dieser Plan **erfindet kein neues Design** — er **kodifiziert + migriert** die gewachsenen Patches in die bestehende Sprache.

**Schweregrad:** blocker 2 · major 11 · minor 3

## Katalog

### Dimension: tokens

**[IC-01] (blocker)** Doppel-:root in custom.css (Z.11 + Z.62) = zwei Token-Quellen in einer Datei; colors_and_type.css (Skill) ist eine dritte (Soll-)Spiegelung. --zen-*-Legacy in Z.11 teils direkt genutzt.
- *Betrifft:* app/static/css/custom.css, colors_and_type.css
- *Sammel-Fix:* Zu EINEM :root mergen; colors_and_type.css als generierten/synchronisierten Spiegel definieren, nicht als zweite manuelle Quelle. --zen-*-Direktnutzungen auf Kanon-Tokens umstellen. VORHER Deck-Invariante absichern (B0-Crash-Risiko: Merge kann CSS-Parsing brechen).

**[IC-02] (major)** _ml_styles.html re-deklariert den GANZEN Brand-Token-Satz hermetisch auf .mein-lernen (--washi:# Grep = genau 1 Treffer) — einziges Template das so verfaehrt. Schaerfste Einzel-Anomalie; bricht den globalen [data-theme=dark]-Flip (musste deshalb manuell ein zweites Dark-Set bei Z.422 mitfuehren).
- *Betrifft:* app/templates/mein_lernen/_ml_styles.html
- *Sammel-Fix:* Lokale :root-/Token-Re-Deklaration entfernen, von globalen Tokens erben; nur surface-spezifische Aliase behalten. Damit entfaellt das duplizierte Dark-Set. Generelle Regel + Lint: KEIN Partial deklariert Brand-Tokens neu. (Live-Defekt bereits gemildert durch das zweite Dark-Set bei Z.422 — verbleibend ist die Anti-Pattern-Schuld, deshalb tokens statt dark-mode.)

### Dimension: dark-mode

**[IC-06] (blocker)** Dark-Mode-Luecken in Flaechen mit hartem #fff/Hex ohne [data-theme=dark]-Gegenpart: learn_n5 .n5hub-module=#fff (B2); module_detail .mod-header/.lesson-row=#fff (B3); lernmethode h2{#1a1a1a}/Prosa-Hex (B5); practice_kana Setup 0 Dark-Regeln (B6); kana_storm 0 wirksame Dark-Regeln (B7). lesson_view .lesson-header-card .card-text Bootstrap-#212529 1.11:1 (B9).
- *Betrifft:* learn_n5.html, module_detail.html, lernmethode.html, practice_kana.html, practice_kana_game.html, _kana_storm_styles.html, lesson_view.html
- *Sammel-Fix:* Pro <style>-Block eigenen [data-theme=dark]-Gegenpart liefern ODER hartes #fff→var(--card-background). Sammel-Fix pro Seite; --kon-Flip-Falle (Navy→hell, weisser Text via --kon-100). Lint-Regel: jeder verbleibende <style>-Block liefert sein Dark-Pendant.

**[IC-07] (major)** Sub-AA-Kontraste sitewide (auch im Light): --ink-500 Labels 4.06:1 (40+ Knoten in stats), Shu/Shu-deep-Akzenttext ~3.0-3.6:1 (Bundle/global), Nuance-Label #b45309 3.42:1, .filter-btn 1.7-2.29:1, .streak-keep 3.29:1, aktiver Tab/CTA --kon+#fff 1.55:1 (Flip-Falle).
- *Betrifft:* stats.html, review.html, browse.html, practice_kana.html, _kana_storm_styles.html, bundles/n5_bundle.html
- *Sammel-Fix:* Kontrast-Audit gegen WCAG AA; Label-Ton auf --ink-600/700 anheben; Akzenttext nur auf ausreichend dunklem Grund; --kon-Fuellungen mit weissem Text via --kon-100 im Dark absichern.

### Dimension: off-brand-accent

**[IC-03] (major)** Konkurrierendes --color-*-Token-Vokabular (5 Streu-Refs live + lesson_card_states-Prototyp komplett + todo_ui zen-*-Vorschlag) parallel zu --washi/--shu/--ink-*.
- *Betrifft:* custom.css (5 Streu-Refs), lesson_card_states_redesign.html
- *Sammel-Fix:* --color-* NICHT zum System erheben; die 5 Streu-Refs auf Pigment-Tokens mappen (1:1-Mapping-Tabelle); Prototyp vor jeder Idee-Adoption uebersetzen.

**[IC-04] (major)** Off-brand-Akzentfarben streuen sitewide: my_lessons durchgaengig Periwinkle #667eea statt Shu; user_profile #666/#0d6efd/#28a745/#667eea; review.html Doppel-Akzent Indigo statt Shu + blauer Puls-Ring; mobiles Audio-Sheet/FAB Indigo.
- *Betrifft:* my_lessons.html, user_profile.html, review.html, lesson_view.html
- *Sammel-Fix:* Auf EINE Akzentfarbe (Shu) migrieren; Indigo/Periwinkle/Bootstrap-Hues durch --shu/--ink-* ersetzen. Shu-Diaet-Regel (nur ein gesaettigter Brennpunkt) durchsetzen.

### Dimension: bootstrap-bleed

**[IC-05] (major)** Ungethemte Bootstrap-Defaults konkurrieren sitewide: Footer-Links klassenlos → #0d6efd (Root-Cause); bare .card ohne bg/color (B8); btn-outline-primary; .alert nie dark-themed; me-1-Utilities in courses; Bootstrap-Modal-Markup in purchase.
- *Betrifft:* base.html, custom.css, payment_success.html, payment_failed.html, courses.html, purchase.html
- *Sammel-Fix:* EIN zentraler Bootstrap-Bridge-Block in custom.css: --bs-link-color/-hover auf Tokens; .site-footer a / .card / .alert-* / .btn-outline-primary gescopt themen (Light+Dark). Globaler [data-theme=dark] .card-Fix (B8) auf diese Branch bringen (fehlt — auf main vorhanden).

### Dimension: icons

**[IC-08] (minor)** Tabler-Icons (ti ti-*) im Prototyp lesson_card_states (6 Treffer) konkurrieren mit kanonischem FA6 solid (44 Templates). Klee One Brand-Font nur im Prototyp importiert, nicht im Skill-CSS.
- *Betrifft:* lesson_card_states_redesign.html, colors_and_type.css
- *Sammel-Fix:* ti→fas 1:1-Mapping vor jeder Idee-Adoption; FA6 solid als einzige Icon-Quelle festschreiben. Klee One in colors_and_type.css/base.html importieren (Font-Lade-Luecke).

### Dimension: ia-overlap

**[IC-09] (major)** Drei eingeloggte Lern-Heimaten zeigen redundant 'weiter lernen/faellig/Streak': index-Hero, /lessons lp-continue, /mein-lernen Heute-Hero. /mein-lernen ist zudem nur im Dropdown, nicht in Primary-/Bottom-Nav sichtbar.
- *Betrifft:* index.html, lessons.html, learner_dashboard.html, base.html
- *Sammel-Fix:* /mein-lernen als kanonische eingeloggte Lern-Heimat etablieren (EINE Resume-Quelle dashboard_service); index + /lessons auf Teaser reduzieren; /mein-lernen in Primary-/Bottom-Nav heben.

**[IC-10] (major)** /lessons traegt Doppelrolle (Gast-Marketing-Hero UND eingeloggtes Weiterlern-Dashboard). Stat-Tabs in /review/stats UND /mein-lernen aus denselben Endpoints (doppelte Level/XP-Berechnung stats_page vs dashboard_routes.index). Drei Matching-Interaktionen, zwei Kana-Spiel-Engines, zwei Daily-Mechaniken.
- *Betrifft:* lessons.html, stats.html, learner_dashboard.html, lesson_view.html, pruefen_session.html, kana_grid_game.js
- *Sammel-Fix:* /lessons = reiner Katalog. Stat-Logik in einen Helper (Drift vermeiden), Dashboard-Tabs = Kurzform, /review/stats = Deep-Dive. Matching → kanonisch Tap-to-pair. Kana-Engine extrahieren (Lektion/Practice = Adapter). Daily-Tagesgrenzen vereinheitlichen (Europe/Zurich).

### Dimension: inline-monolith

**[IC-11] (major)** 39 <style>-Bloecke in 31 Templates (lesson_view 5 + ~2100 Z. Inline-JS, base 3, index 2). Pro-Surface-Inline statt zentraler Klassen → Dark-Luecken entstehen genau dort. lesson_view.html (4'900 Z.) groesster Monolith (Markup+CSS+JS).
- *Betrifft:* lesson_view.html, index.html, base.html, review.html, stats.html
- *Sammel-Fix:* Wiederkehrende Muster nach custom.css heben; Stage-Stil (Kana-Storm) aus index in Partial/custom.css; verbleibende <style>-Bloecke MUESSEN eigenen [data-theme=dark]-Block mitliefern (Lint-Regel). lesson_view schrittweise entflechten (Frontend-Kern).

### Dimension: copy-language

**[IC-12] (minor)** Sprachmix: englische Service-Fehlertexte (mock_payment_service, purchase_lesson_page Flash), englische Labels in courses, englischer Trigger-String 'Login required' als Kontrollfluss-Schluessel, englische Auth-Flash-Texte.
- *Betrifft:* mock_payment_service.py, routes.py, courses.html, login.html, register.html
- *Sammel-Fix:* Alle UI-/Flash-Strings durchgehend Deutsch; 'Login required'-Substring-Match durch strukturierten Reason-Code/Enum ersetzen (entkoppelt Datenstring vom Kontrollfluss).

### Dimension: a11y

**[IC-13] (major)** role=tablist ohne role=tab/aria-selected in stats (WCAG 4.1.2); Stats-Toggle <div> ohne role=button; doppeltes aria-label am Mobile-Burger; Dark-Mode-Toggle + Burger Touch-Target <44px.
- *Betrifft:* stats.html, _kana_game_stage.html, base.html
- *Sammel-Fix:* ARIA-Rollen korrekt setzen (role=tab/aria-selected, role=button); doppeltes aria-label entfernen; Touch-Targets auf ≥44px.

### Dimension: dead-code

**[IC-14] (minor)** Frontend-Dead-Code: lessons.css (tot seit /lessons-Redesign), _kana_game_embed_layout.html + /practice/kana/embed (verwaist, kein iframe in index), learn_path.html (von keiner Route gerendert), toter alter Lernpfad index.html:902-1039, .welcome-card/.modern-welcome-card, fill_blank-Code, Web-Push ohne Versand-Pfad.
- *Betrifft:* lessons.css, _kana_game_embed_layout.html, learn_path.html, index.html, routes.py, ai_services.py
- *Sammel-Fix:* Nach Verifikation entfernen. lessons.css-Referenzen (Tests) vorher pruefen. Untracked Prototypen einarbeiten dann loeschen (sauberer Git-Status).

### Dimension: backend-debt

**[IC-15] (major)** Gott-Dateien (routes.py 4'863 Z./129 Routen, srs_routes.py 1480, models.py 1551); Doppel-OAuth (oauth_bp + social-auth, beide Raw-SQL-Insert); drei Payment-Factories + PostFinance-Legacy; drei Reset-Implementierungen; zwei Admin-Oberflaechen (Custom + Flask-Admin); Zeitzonen-Split (UTC Lockout/due vs Europe/Zurich Streak); CSP unsafe-inline/eval; Tailwind Play-CDN nicht prod-tauglich; premium-up/downgrade ohne Zahlung; Reset-Token 1h mehrfach verwendbar.
- *Betrifft:* routes.py, srs_routes.py, models.py, oauth_routes.py, social_auth_config.py, payment_service.py, admin_views.py, admin/base_admin.html
- *Sammel-Fix:* SEPARATER, nur katalogisierter Track (nicht im Frontend-Kern ausplanen). Reihenfolge nach Risiko: (1) Sicherheit (Webhook-Secret erzwingen, premium-Proto entfernen, Reset-Token-Invalidierung), (2) Doppelpfade aufloesen (OAuth, Factories, Reset), (3) Gott-Dateien per Blueprint/Service-Schichtung entzerren, (4) Tailwind-Build-Pipeline. Optional, am Ende.

**[IC-16] (major)** Payrexx-Webhook ueberspringt HMAC-Signaturpruefung wenn PAYREXX_WEBHOOK_SECRET fehlt → ungeprueftes Payload verarbeitet. CSRF-exempte /api/tts + Webhook. Mock-Payment doppelte transaction_id (gespeicherter ≠ zurueckgegebener Wert).
- *Betrifft:* routes.py, payrexx_payment_service.py, mock_payment_service.py
- *Sammel-Fix:* Backend-Track, Sicherheits-Prio: Webhook fail-closed (ohne Secret ablehnen statt ueberspringen); transaction_id-Bug fixen. Vor jeder Payment-Reaktivierung (FREE_MODE aus) Pflicht.


---

## Ziel-Designsystem — Spezifikation (Critic-korrigiert)

Dies ist der **Soll-Zustand**, in den migriert wird. Korrekturen aus der adversarialen Prüfung sind eingearbeitet (siehe ⚠).

### Token-Quelle (eine einzige)
- **EIN** `:root` in `app/static/css/custom.css` — heute Doppel-`:root` (Z. 11 + Z. 62) zusammenführen (IC-01).
- `.claude/skills/japanese-learning-design-system/colors_and_type.css` = **gespiegelte/synchronisierte** Quelle des `:root`, **nicht** zweite manuelle Quelle.
- **Lint-Regel:** Kein Template/Partial deklariert Brand-Tokens neu. Heute einzig verletzt durch `mein_lernen/_ml_styles.html` (IC-02).
- ⚠ **`--zen-*` ist Re-Anchoring, kein Löschen:** `--zen-*` wird **38× in custom.css referenziert** und der Semantik-Layer löst **durch** es auf (`--color-success: var(--zen-matcha)`, `--color-error: var(--zen-vermillion)`) + Direktnutzung in `lesson_view.html`/`review.html`. Beim Merge die `--zen-* → Semantik-Alias`-Kette **erhalten** (auf Kanon-Pigmente re-ankern), nicht naiv entfernen. Eigener verifizierter Sub-Schritt.

### Dark-Mode-Paritäts-Regel (⚠ Priorität invertiert)
Ein einziger globaler `[data-theme="dark"]`-Token-Flip in custom.css (`--ink`-Skala umgekehrt, warmes Sumi-Dunkel, Shu bleibt) trägt Dark Mode.
1. **Primärregel (strukturell):** *Keine hartcodierten Farben in `<style>`-Blöcken — nur Tokens (`var(--…)`).* Dann deckt der **eine** globale Flip Dark automatisch; die Per-Block-Dark-Pflichten sinken gegen null. **(Das ist die Regel, die die 112 Dark-Funde strukturell erschlägt — statt das One-by-one-Muster zu institutionalisieren, das sie erzeugt hat.)**
2. **Schmale Ausnahme:** Ein eigener `[data-theme="dark"]`-Gegenpart pro `<style>`-Block nur dort, wo nötig (z. B. `--kon`-Flip-Falle), **nicht** als Gesetz.
3. **`--kon`-Flip-Falle:** Navy kippt im Dark auf hell → Füllungen mit weissem Text via `--kon-100` navy halten; `--kon`-Text auf hellem Grund → `var(--text-color)`.
4. **Bootstrap-Bridge-Block** (IC-05) themt `.card`/`.alert`/`.btn-outline-primary`/`--bs-link-color` in Light+Dark.
   - ⚠ **Der globale `[data-theme="dark"] .card`-Fix (B8) existiert bereits** auf diesem Branch (`custom.css:4859-4867`, Kommentar nennt „B8" + Payment-Success/-Failed). Der Bridge-Block **baut darauf auf** (Footer-Links `#0d6efd` ab Z. 4869, `.alert`, `btn-outline-primary`), führt ihn **nicht neu ein**.

### Icon-Regel
- **Font Awesome 6 Solid (`fas`) = einzige UI-Icon-Quelle** (44 Templates). Tabler (`ti ti-*`) eliminieren/mappen (nur im Off-System-Prototyp, 0 Live-Treffer).
- Funktionale Emoji (Flaggen, 🔥 ⚡ 🔒 ✅ 🧠 📚) als bewusste semantische Ausnahme.
- **Klee One** (Brand-あ) + Schrift-Stacks aus colors_and_type.css importieren (Font-Lade-Lücke schliessen).

### Geteilte Komponenten-Bibliothek (erhalten + kanonisch)
`btn-shu` (Primär-CTA) · `btn-ghost-jp` (Sekundär) · `eyebrow`/`eyebrow-chip` · Modul-Karte (locked/complete/next + `is-next`-Puls, geteiltes Makro) · `_n5_path` Pfad-Makro (index/learn_n5/module_detail) · `_bundle_cta` Makro (Gating `show_bundle_hint AND not free_mode`) · `_module_banner` (16:9, bewusst bunt) · geteilte Flip-/Review-Karten-Komponente (**Deck-Invariante `.in-deck{display:none}` geschützt + getestet**, ein Front-Romaji-Toggle) · `_matching`-Partial (Tap-to-pair, kanonisch) · geteiltes Quiz-Render-Partial (Normal/Conversation/pruefen) · `_kana_storm_stage` (Hero/Storm/Daily) + geteilte Kana-Spiel-Engine · Stat-Pill / nav-due-badge · Score-Ring / XP-Balken / Reife-Skala (`--mat-*`) · Audio-Player (Block + Inline, Disclaimer) · `review_teaser` (Gast-Gating) · zentraler Bootstrap-Bridge-Block · `prefers-reduced-motion`-Clamp.

### Kill-Liste (⚠ `--color-*` aufgespalten)
- ⚠ **KILL nur die Prototyp-Tokens:** `--color-primary / -surface / -text / -border` (**0 Live-Treffer**, nur in `lesson_card_states_redesign.html`).
- ⚠ **KEEP** `--color-success` / `--color-error` — **live genutzt** (custom.css Z. 39/40 + 165/167, konsumiert Z. 4902 `[data-theme=dark] .alert-danger`). Optional zu `--success`/`--danger` umbenennen, **nicht** eliminieren.
- Tabler-Icons (`ti ti-*`) · Off-System-Vokabulare `--cream`/`--orange`, Serif Iowan Old Style · Off-Brand-Akzente: Periwinkle `#667eea`, Indigo, `#0d6efd`-Links, `#28a745`, `#666`, `#b45309`, harte `#fff`/`#212529`/`#1a1a1a`.
- Toter Frontend-Code: `lessons.css` · `_kana_game_embed_layout.html` + `/practice/kana/embed` · `learn_path.html` · toter Lernpfad `index.html:902-1039` + `.welcome-card`/`.modern-welcome-card` · `fill_blank`-Code · Web-Push-Stub.
- 3 untracked Repo-Root-Prototypen (nach Idee-Einarbeitung löschen).

### ⚠ `mobile-improvements.css` — explizit kartiert (Critic-Lücke geschlossen)
Inventarisiert als **live** (3. CSS-Datei). Verifiziert: **ist eingebunden** (`base.html:81`) und hat **globale Nebenwirkung** (`.container > * { padding-inline: … }`, referenziert in `practice_kana.html:245`). → **Nicht ignorierbar.** Vorgehen: (a) Inhalt prüfen; (b) lebende Regeln/Tokens nach `custom.css` heben (Single-Source); (c) Rest mit verifiziertem Verhalten entfernen. Verortet in **P1** (Token-Fundament) bzw. **P4** (Dead-Code). Sonst bliebe „EINE Token-Quelle" unbelegt.

### ⚠ `register.html` — Dark-Lücke + Sprachmix terminiert
Eigener `<style>`-Block mit `--ink-*`, aber **kein** `[data-theme=dark]`-Pendant + englische Flash-Texte. → In **P1** (Dark, gleiche Mechanik wie B2/B3/B5) bzw. **P4** (Sprachmix IC-12) eingeplant.
