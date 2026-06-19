# Design-Bug-Report japanese-learning.ch — Dark Mode + Frontend-Redesign

> Erstellt 2026-06-19 via Multi-Agent-Review (visuelle Multi-Theme/Viewport-Captures gegen lokal gerenderten Live-Stand `origin/main` 19e68a5, statischer CSS/Template-Audit, computed-WCAG-Kontrast, adversarial verifiziert). 131 Roh-Funde → **112 bestätigt** (19 als Artefakt/False-Positive verworfen). ~30 distinkte Ursachen. Screenshots unter `_shots/`.
>
> **B0 (Gast-Crash) wurde unabhängig per `curl` reproduziert** (HTTP 500 + `AttributeError: 'AnonymousUserMixin' object has no attribute 'id'`). Hinweis zur Prod-Wirkung: der **sichtbare Stacktrace** ist ein Dev-Modus-Artefakt (`debug=True` lokal) — in Produktion (`debug=False`) leakt nichts, aber **der 500-Crash für jeden Gast besteht auch in Prod** (UX/SEO).

## 1. Kurzfazit

Dominantes Grundmuster: **fehlende `[data-theme="dark"]`-Gegenparts**. Dutzende Flächen sind mit hartem `#fff`/Hex gebaut und bleiben im Dark Mode grellweiss, während der Token-Text via `--kon` ins Helle kippt → wiederkehrende „weisse Karte + unlesbarer hell-auf-hell-Titel"-Falle (Dashboard, N5-Hub, Modul-Detail, Paywall, Checkout, Lernmethode, Kana-Setup). Drei weitere Querschnitt-Muster: `--kon`-Flip-Falle, seitenweite Bootstrap-Defaults ohne Theming (`#0d6efd`-Footer-Links, bare `.card`, `.alert`, `btn-outline-primary`), flächiger sub-AA-Akzenttext (`--shu`/`--shu-deep`, `--ink-500`-Labels). Ein Befund ist kein CSS-Bug: Gast-Crash auf `/course/<id>`.

**Severity (bestätigt):** Blocker ≈ 14 · Major ≈ 45 · Minor ≈ 40 · Nit ≈ 12.

---

## 2. Blocker & Major

### B0 — Kursseite crasht für Gäste (AttributeError) — `/course/<id>`
- **Falsch:** `view_course` ohne `@login_required`; Kauf-Check ist mit `if current_user.is_authenticated:` gegated, aber die folgende Fortschritts-Schleife ruft ungated `UserLessonProgress.query.filter_by(user_id=current_user.id, …)` → Gast = `AnonymousUserMixin` ohne `.id` → HTTP 500.
- **Beleg:** `app/routes.py:1255-1256` (kein Guard), Crash ~Z. 1283; live-reproduziert `curl /course/4` → 500.
- **Fix:** Fortschritts-Berechnung (`app/routes.py:1280-1294`) hinter denselben `if current_user.is_authenticated:`-Guard. Reiner Backend-Fix.

### B1 — `/mein-lernen`-Dashboard ignoriert Dark Mode komplett
- `_ml_styles.html` re-deklariert den **gesamten** Token-Satz hermetisch in Light-Literalen auf `.mein-lernen` + 30+ hartes `background:#fff`; **kein** `[data-theme=dark]` im `mein_lernen/`-Verzeichnis. Karten reinweiss (18.7:1 grell); Begrüssungs-H1 in `--kon`-Navy auf dunklem Body → **1.31:1 unlesbar**.
- **Beleg:** `_ml_styles.html:12-37` (Tokens), `:39` (h1=`--kon`), `:74` (`.card`=#fff).
- **Fix:** `[data-theme=dark] .mein-lernen{…}`-Block der nur Farb-Tokens flippt + Hardcodes `#fff`→`var(--card-background)`. Hermetische Re-Deklaration ⇒ globaler Token-Flip greift hier NICHT.

### B2 — `/learn/n5`-Hub: Modulkarten un-dark, Titel/Icons unlesbar
- `.n5hub-module{background:#fff}` ohne Override; `h3` erbt `--kon` → 1.55:1, Icons 1.24:1. Totes `--ink-soft` (nirgends definiert) → harter Fallback.
- **Beleg:** `learn_n5.html:181/184/187`.
- **Fix:** `[data-theme=dark] .n5hub-module{background:var(--card-background);border-color:var(--hairline)}` + `--ink-soft`→`var(--ink-500)`.

### B3 — `/learn/n5/<slug>` Modul-Detail un-dark
- `.mod-header`/`.lesson-row`/`.mod-empty`=`#fff`; Titel via `--kon` → hell-auf-hell 1.55:1, Beschreibung 1.84:1.
- **Beleg:** `module_detail.html:19/61/125/33/88`.
- **Fix:** Dark-Override auf Karten + Titel auf `var(--text-color)`.

### B4 — Paywall un-dark (konversionskritisch)
- `.lesson-tease`/`.opt-card`/`.auth-required`=`#fff`; Preise/Titel/Features fahl bis unsichtbar; Shu-CTA + grüne Haken bleiben korrekt.
- **Beleg:** `lesson_paywall.html:22/62/173`.
- **Fix:** `#fff`→`var(--card-background)`, Titel via `--kon-100`.

### B5 — `/lernmethode`-Prosa im Dark unsichtbar
- Karten gehen korrekt dunkel, aber `h2{color:#1a1a1a}` (**1.01:1**) und `p/li/strong{color:#2c3e50}` (1.56:1) hartcodiert → ganze Prosa unlesbar. Hero-/CTA-Box bleiben off-theme hell.
- **Beleg:** `lernmethode.html:115/140-148/149`.
- **Fix:** Textfarben auf `var(--text-color)`; Hero/CTA themen.

### B6 — `/practice/kana`-Setup: aktive Tabs/Chips/CTA unlesbar
- **0** `[data-theme=dark]`-Regeln. Aktiver Tab `#fff`+`--kon` → 1.55:1; CTA `background:var(--kon);color:#fff` → Flip-Falle 1.55:1; Chips 2.52, Sub 2.78.
- **Beleg:** `practice_kana.html:103/151/231/135/143/157/166/193/58`.
- **Fix:** Dark-Block; `#fff`→`var(--card-background)`, Tab-Text `--text-color`/`--shu`, CTA `--kon-100` oder `--shu`+`color:var(--washi)`.

### B7 — `/practice/kana/storm`-Setup: aktive Tabs/Chips/Ghost unlesbar
- `_kana_storm_styles.html` hat **0** `[data-theme=dark]`-Regeln. `.kstorm__tab.is-active`=`#fff`+`--kon` 1.55:1; Chip/Ghost weisse Inseln mit hell-auf-weiss-Text; `.kstorm__chip--all.is-active`=`--kon` weisser Text unsichtbar.
- **Beleg:** `_kana_storm_styles.html:66/75/82/101/305/322/357`.
- **Fix:** Literale `#fff`→`var(--card-bg,#FFFDF7)`; Selektion via Shu-Border statt heller Füllung.

### B8 — Bare Bootstrap `.card` un-dark (Payment-Success/-Failed u.a.)
- `custom.css .card` setzt nur Radius/Border, kein bg/color; kein globaler Dark-Override → weisse Karte mit Bootstrap-Dunkeltext auf Sumi.
- **Beleg:** `custom.css:1097-1100`; `payment_success.html:12-13`, `payment_failed.html:12-13`.
- **Fix:** Global `[data-theme=dark] .card{background-color:var(--card-background);color:var(--text-color);border-color:var(--border-color)}` (erschlägt alle bare-`.card`-Seiten; `.lesson-content-card`-Scope kann entfallen).

### B9 — Lektions-Header-Body (`.card-text`) im Dark unsichtbar
- Der Dark-Textfix deckt nur `.lesson-content-card`, nicht `.lesson-header-card`. Beschreibung `p.card-text` behält Bootstrap-`#212529` → **1.11:1**.
- **Beleg:** `lesson_view.html:845/1158-1163`.
- **Fix:** Selektor (`:845`) um `.lesson-header-card` erweitern.

### Major (gruppiert)
- **Über-uns** `ueber.html:181-186/232` — Hero/CTA-Kästen un-dark + `--kon`-CTA-Falle.
- **Courses-Hero** `custom.css:2466/2469/152` — heller Pink/Indigo-Gradient bleibt im Dark (`--secondary-color`/Sakura nie überschrieben), weisser Text 2.14–2.52:1, Stat-Zahlen 1.16–1.40:1.
- **My-Lessons** `my_lessons.html:10/30/36/220-222/468` — durchgängig off-brand Periwinkle `#667eea` statt Shu; Button 3.66:1.
- **Review-Seite** `review.html:250/262-266/379/402/420-424/707` — Doppel-Akzent Indigo statt Shu, Audio-`.playing` 2.29:1, Nuance-Label `#b45309` 3.42:1, blauer Puls-Ring.
- **User-Profile** `user_profile.html:44/77/180/186/133/206` — `#666` (2.99–3.26:1), Link-Blau `#0d6efd`, off-palette `#28a745`/`#667eea`.
- **Stats-Seite** `stats.html:94/193/225/232/235` — `--ink-500` 4.06:1 (40+ Knoten), `.streak-keep` 3.29:1, Heatmap-Glyph `--kon` unlesbar.
- **Lessons-Dashboard-Filter** `lessons.html:499-502/642-646` — Label 2.13:1, `%`-Badge weisse Insel 3.36:1.
- **/review/browse** `browse.html:27/44/20` — `.filter-btn` 1.7–2.29:1, native UA-Controls ungethemt.
- **Error-Pages 500/410** `:22` — weisser Sekundär-Button mit near-white Text (404 ist bereits korrekt).
- **Kana-Hero-Launcher (Startseite)** `index.html:1366ff` — Reihen-Chips verschmelzen (1.13/1.39:1), aktiver Tab 1.55:1, Registrieren-CTA Flip-Falle.
- **Kana-Spielfeld** `practice_kana_game.html:104/193/245/248` — Hover/Selected/Ghost `#fff` mit hellem Text 1.84:1.
- **Sitewide sub-AA-Akzenttext** — Shu/Shu-deep klein bzw. weiss-auf-Shu ~3.0–3.6:1 (Startseite, N5-Hub, Bundle).
- **ARIA-Tablist ohne Tabs** `stats.html:497` — `role=tablist` ohne `role=tab`/`aria-selected` (WCAG 4.1.2).

---

## 3. Minor & Nits

- **Footer-Links → Bootstrap-Blau `#0d6efd`** (EIN Root-Cause, seitenweit) `base.html:828-844` — klassenlose `<a>`, 3.82–4.21:1. Sammel-Fix: `.site-footer a` themen + `--bs-link-color` in `:root`.
- **Bootstrap-Alerts un-dark** `.alert-*` Pastelle auf Sumi (lesbar, off-theme).
- **`btn-outline-primary` Bootstrap-Blau** Sekundär-CTAs.
- **iframe-Embed setzt nie `data-theme`** `_kana_game_embed_layout.html` (Route verwaist, latent).
- **`--secondary-color` (Sakura) im Dark nicht überschrieben** (Token-Lücke) + totes `.japanese-audio-text.playing-audio` `custom.css:3096-3117`.
- **Stats-Toggle `<div>` ohne `role=button`** `_kana_game_stage.html:125`.
- **Quiz-Dot zwei Grüntöne** (nur Light) `--zen-matcha` vs `--matcha`.
- **Lesson-View Cross-Viewport-Inkonsistenzen** — totes `.next-up-bundle-cta`-Override, mobiles Sheet/FAB behalten Indigo statt Shu.
- **Status-Hex auf Review-Stat-Items** (Bootstrap-Hues, Marken-Hygiene).
- **Token-Disziplin-Nits Startseiten-Launcher** `--card-bg`-Fallback `#FFFDF7` ≠ Nachbarn; tote Fallbacks.
- **Badges/Counter knapp unter AA** `.lp-badge-free` 3.58, diverse `--ink-500` ~4.0–4.4, Streak `--kincha` 4.48.
- **Touch-Targets <44px** Burger 38px, Theme-Toggle 36px, Kana-Script-Toggle 38px (AA bereits erfüllt).
- **Dead-Code-Hygiene** toter alter Lernpfad `index.html:902-1039`, `.welcome-card`/`.modern-welcome-card`, Admin-`!important`-Block `custom.css:1204-1282`. (`[F60]`-Duplikate sind legitime `@media`-Overrides — kein Eingriff.)

---

## 4. Querschnitt-Muster (Sammel-Fixes)

**Muster 1 — Fehlende `[data-theme=dark]`-Gegenparts + hartcodiertes `#fff`/Hex.** Häufigste Ursache (B1–B9, F2/F3, F46, F88…). Sammel-Fix: literale `#fff`→`var(--card-background)`; je Partial mit eigenem `<style>`-Scope einen `[data-theme=dark]`-Block; **ein** globaler `[data-theme=dark] .card{…}` (B8) deckt alle bare-`.card`-Seiten. Achtung: hermetische Token-Re-Deklaration (`_ml_styles.html`) braucht expliziten Dark-Tokensatz.

**Muster 2 — `--kon`-Flip-Falle.** `--kon` kippt Dark Navy→hell. (a) Weisser Text auf `--kon`-Fläche (Primär-CTAs) → `var(--kon-100)` navy oder `var(--shu)`+`color:var(--washi)`. (b) `--kon`-Text auf heller Fläche (Tab-/Kartentitel, Heatmap) → `var(--text-color)`/`var(--kon-100)`.

**Muster 3 — Bootstrap-Defaults nie ge-dark-themed.** `#0d6efd`-Links, bare `.card`, `.alert`, `btn-outline-primary`, native Controls. Sammel-Fix: `--bs-link-color`/`--bs-link-hover-color` zentral auf Tokens + `.site-footer a`/`.card`/`.alert-*`/`.btn-outline-primary` gescopt themen (Light + Dark).

**Muster 4 — sub-AA-Akzent/Muted-Text.** Shu-Text-auf-hell→`--shu-deep`; Shu-Text-auf-dunkel→helleres Shu/`--shu-on-dark`; weiss-auf-Shu→`--shu-deep`-Füllung; Muted-Labels eine `--ink`-Stufe heben (gescopt, nicht globales Token verschieben). Nach jeder Anpassung `contrast.py` in beiden Themes gegen 4.5:1 laufen lassen.

**Reihenfolge:** B0 (Crash) sofort → Muster-1-Sammel-Fix → Muster 3 (ein zentraler Bootstrap-Block) → Muster 2/4 gezielt.
