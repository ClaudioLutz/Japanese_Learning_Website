# Japanese Learning — Design System

A design system for **Japanese Learning** ([japanese-learning.ch](https://japanese-learning.ch)),
a Swiss-made, German-language JLPT N5 platform built by Claudio Lutz from Rorschach SG.
The brand sits at the intersection of **Swiss restraint and Japanese craft**: warm
washi-paper backgrounds, hairline borders, sumi-ink typography, and a single hot
vermillion (朱色) accent for primary action.

The product is a Flask web app that teaches Hiragana → Katakana → Kanji → Vocabulary →
Grammar via structured lessons, an FSRS-backed spaced repetition system, and gamified
streaks/levels. UI is in German throughout. Targeted at adult Swiss-German learners
preparing for JLPT N5.

---

## Sources used

| Source | Path / URL | Access |
| --- | --- | --- |
| Flask templates (Jinja2) | local mount: `templates/` | full read access |
| Backend / static / migrations | GitHub: `ClaudioLutz/Japanese_Learning_Website` (branch `main`) | read |
| Live site | https://japanese-learning.ch | reference |
| Brand stylesheet | `app/static/css/custom.css` (in the repo) | extracted |
| Logo + favicons | `app/static/torii-logo.svg`, `favicon.*`, `apple-touch-icon.png` | copied to `assets/` |
| Marketing imagery | `app/static/images/*.jpg / *.png` | one full-bleed sample copied to `assets/hero-photo.jpg` |

The full-resolution reference photographs (>3MB each) were **not** copied — only one
compressed JPG (`hero-photo.jpg`) is kept as a representative. Reach for the repo if
more imagery is needed.

---

## Index

```
.
├── README.md                 ← you are here
├── SKILL.md                  ← skill manifest (Claude Code compatible)
├── colors_and_type.css       ← every color, type, spacing, shadow token
├── assets/                   ← logos, favicons, OG image, hero photo
│   ├── torii-logo.svg          (single-color hand-drawn torii — currentColor)
│   ├── favicon.svg / *.png     (favicon family)
│   ├── apple-touch-icon.png
│   ├── og-image.png            (1200×630 social card)
│   └── hero-photo.jpg          (Mt. Fuji + pagoda + sakura)
├── preview/                  ← cards rendered in the Design System tab
│   ├── colors-*.html
│   ├── type-*.html
│   ├── spacing-*.html
│   ├── components-*.html
│   └── brand-*.html
├── ui_kits/
│   └── marketing/            ← Compass-Redesign Phase 2 marketing site recreation
│       ├── README.md
│       ├── index.html        ← interactive home + lessons + bundle flow
│       ├── TopNav.jsx
│       ├── Hero.jsx
│       ├── BrowserFrame.jsx
│       ├── ModuleCard.jsx
│       ├── BundleHint.jsx
│       └── Footer.jsx
│   └── learn_app/            ← in-product (logged-in) learning UI
│       ├── README.md
│       ├── index.html        ← review session + lesson view + stats
│       ├── ReviewCard.jsx
│       ├── LessonHeader.jsx
│       ├── KanaCard.jsx
│       ├── ProgressBar.jsx
│       └── StatChip.jsx
```

---

## CONTENT FUNDAMENTALS

The voice is **direct, technically honest, and quietly confident** — written by
someone who actually lerns the thing they're shipping. It reads like a Swiss
solo-dev's product notes, not marketing.

### Tone
- **Honest, never hyped.** "Eine ehrliche Antwort: Eine einzelne Person…" —
  the About page literally opens with that. No "revolutionary", no
  "AI-powered", no "10x your Japanese".
- **Data-credible.** Numbers and concrete claims wherever possible:
  *"~25 % weniger Wiederholungen bei gleicher Retention"*,
  *"261 Vokabeln, 44 Kanji"*, *"30 Tage Geld zurück"*.
- **Cosy when warranted.** Light Japanese flavor — *"Hiragana am Morgen.
  Kanji am Abend."*, occasional *こんにちは, {username}* greeting,
  serif Japanese subtitles in the wordmark.

### Casing
- Headlines: **sentence case** with periods — *"Hiragana am Morgen. Kanji am Abend."*
- Buttons / CTAs: **Sentence-case action verbs**, often with a hairline arrow:
  *"Kostenlos starten"*, *"N5-Pfad starten"*, *"Beginnen →"*, *"Fortfahren →"*.
- Eyebrow chips: **UPPERCASE** with letter-spacing — *"JLPT N5 · auf Deutsch · in der Schweiz gemacht"*.
- Status microcopy: lowercase or sentence-case — *"abgeschlossen"*, *"in Vorbereitung"*.

### Pronouns & address
- **"Du" throughout** — informal singular, never "Sie". The user is a peer.
  *"Wo du aufgehört hast."*, *"Du markierst leicht / gut / schwer / wieder…"*.
- The author is **"ich"** in long-form pages (About, Lernmethode); the product is
  **"wir"/"diese Plattform"** elsewhere. Both feel earned.

### Language layering
- Primary UI: **German (Swiss-German learner audience, but Standard German on screen)**.
- Japanese is reserved for: kana/kanji content, the wordmark tag (日本語), and
  brand color names in technical docs (*shu*, *kon*, *matcha*, *washi*).
- English appears only as a secondary toggle ("Lieber auf Englisch?").
- Swiss spelling: **"ss" not "ß"** — *"musst"*, *"strasse"*, *"grosse"*.

### Emoji usage
- **Sparingly, semantically, never decoratively.** Used as compact icons inside
  navigation pills and status: 🔥 streak, ⚡ level, 🔒 locked, ✅ done,
  📚 path header, 🧠 review, 🇨🇭 / 🇩🇪 / 🇬🇧 language flags, ⚡ N5 bundle CTA.
- Never fluff: no 🎉 / 🚀 / ✨ / 💫. If the meaning isn't load-bearing, drop it.
- Module icons (`m.icon_emoji`) are admin-curated per module — usually a single
  on-topic emoji like 📖 or ✏️.

### Vibe (concrete examples)
- *"Hauptberuflich arbeite ich als Data Scientist… Diese Plattform ist mein Abendprojekt."*
- *"WaniKani? Englisch. Bunpro? Englisch. Anki? Großartiges Tool, aber Karten muss man selbst erstellen."*
- *"keine Firma, kein VC, kein Marketing-Team."*
- *"Pulsierend markiert: dein nächstes Modul."*

The voice **respects the reader**: no condescension, no exaggeration, no fake
urgency. Skeptical-Swiss-engineer with a soft spot for Japanese aesthetics.

---

## VISUAL FOUNDATIONS

### Palette philosophy
The palette is a translation of **traditional Japanese pigment names** into a
modern web palette. Variable names use the Japanese term:

| Token | Hex | Role |
| --- | --- | --- |
| `--washi` | `#FAF7F2` | page background — bone paper |
| `--kinari` | `#F5F0E8` | warmer paper, panels |
| `--sumi` | `#1C1C1C` | ink (primary text) |
| `--kon` | `#1F2A44` | deep navy — headings & brand |
| `--ai` | `#264F7E` | indigo — links |
| `--shu` | `#EB6101` | vermillion — primary CTA, active state |
| `--matcha` | `#7A9033` | tea green — success / completion |
| `--kincha` | `#C7802D` | gold-brown — premium accent |

A warm **ink scale** (`--ink-50` → `--ink-950`) sits over washi instead of pure
gray — every neutral is slightly tinted toward warm beige.

### Type
- **Geist** (510 weight, `letter-spacing: -0.03em`) for all H1–H3.
- **Inter** for body and UI labels at `1.0625rem` / `line-height: 1.7`.
- **Fraunces** (variable, `opsz` 14, weight 600) for the wordmark only.
- **Noto Serif JP** for the *日本語* tag under the wordmark and decorative subtitles.
- **Noto Sans JP** for any kana/kanji in content.
- **Geist Mono** for URLs, code, meta (`Modul 03`), and progress counters.

H1s use a fluid `clamp(2.25rem, 5vw + 1rem, 4.5rem)`. Tracking is
**aggressively negative** at large sizes (`-0.03em`) — Linear-style.

### Spacing
8 px base. Named scale: `--space-1` (4) → `--space-16` (64). Cards use 1–1.2 rem
internal padding; sections breathe with 4–6 rem vertical padding (`--space-12`
to `--space-16`).

### Backgrounds
- Default page: solid `--washi`.
- Hero: a custom 3-layer painterly background (`.hero-bg-jp`):
  ```css
  background:
    radial-gradient(ellipse 80% 50% at 50% -10%, rgba(31,42,68,.18), transparent 60%),
    radial-gradient(ellipse 60% 40% at 85% 10%, rgba(235,97,1,.08), transparent 55%),
    linear-gradient(180deg, #FAF7F2 0%, #F5F0E8 100%);
  ```
  A whisper of kon haze top-left, a vermillion glow top-right, sliding into
  warmer paper at the foot. Never garish.
- Photography (Mt. Fuji + sakura) appears only on legacy welcome screens and
  social cards; **the redesign avoids full-bleed photo heroes** in favor of the
  browser-frame design moment with kana cards.
- No repeating patterns, no textured noise, no SVG flourishes. The palette and
  hairline borders carry the Japanese feel.

### Animation
- **Hover lifts:** `translateY(-1px)` plus a darker gradient or denser shadow.
  Duration `0.15s`. Used on buttons, cards, dropdown items.
- **CTA press:** `transform: scale(0.96)` on `.btn:active`.
- **`is-next` pulse** on the active learning module — a 2.4s cubic ease loop on
  the focus ring (`box-shadow` from `0 0 0 3px rgba(235,97,1,.18)` to
  `0 0 0 5px rgba(235,97,1,.10)`). The system's only continuous animation.
- Brand `あ`-mark rotates `-4deg` and scales `1.06` on hover with a small
  bouncy cubic-bezier — a single playful detail. (Previously applied to the
  torii.)
- Page-level fades and parallax: **none**.
- Always wrapped in `@media (prefers-reduced-motion: reduce)` clamp.

### Hover states
- Ghost surfaces darken: `rgba(28,26,23,.04)` overlay.
- Card borders go from `--ink-200` → `--ink-400`; tiny lift; subtle shadow.
- Primary buttons brighten the gradient (`#EB6101→#D85700` becomes `#F37016→#E25C00`).
- Links: color shifts from `--ai` (indigo) to `--shu` (vermillion).

### Press states
- All `.btn` variants: `scale(0.96)`. No color punch on press — just compression.

### Borders
- **Hairline-first.** `1px solid var(--ink-200)` for cards, panels, nav,
  dropdowns. Borders are the structural element, not shadows.
- **Color-bar accents** appear only on top of cards with semantic meaning
  (`module.color_code`) or as a 3px **left-border on the bundle hint** in
  `--shu`.
- Active states use a 3px outer ring (`box-shadow: 0 0 0 3px rgba(235,97,1,.18)`)
  rather than thicker borders — preserves layout.

### Shadow system
Three named shadows, all warm sumi-tinted (`rgba(28,26,23,...)`), never bluish:
- `--shadow-subtle` — flat-but-not-flat for default cards
- `--shadow-card` — hover state for cards
- `--shadow-lifted` — modals, dropdowns, browser-frame hero
- `--shadow-cta` — inset highlight + 1px outline + drop shadow on the primary
  vermillion button

### Capsules vs gradients
- **Capsules** (pill-shaped, `border-radius: 999px`) are everywhere: eyebrow
  chips, stat pills (`🔥 14`), user-avatar button, module status pills.
- **Gradients** appear only on the primary CTA (top-down 180° shu→shu-deep) and
  the hero background. No purple/blue/pastel gradient backgrounds. No
  text gradients.

### Layout rules
- **Sticky topnav** with backdrop blur (`saturate(180%) blur(14px)`),
  85% white, 1px hairline bottom.
- Max content width: **1152px** centered (`.section-narrow`); prose: `68ch`.
- Auto-fill grid for module cards: `repeat(auto-fill, minmax(280px, 1fr))`.
- Mobile: Topnav collapses to hamburger, a **fixed bottom-nav bar** appears at
  `<992px` with 4 icons (Home / Lektionen / Wiederholen / Profil).

### Transparency & blur
- Used only on the topnav (`rgba(255,255,255,.85)` + `backdrop-filter`) and on
  legacy "modern-welcome-card" frosted-glass panels (`blur(20px)`). Sparingly.

### Imagery vibe
- **Warm, sunlit, never cool.** The reference Mt. Fuji photo is golden-hour with
  cherry blossoms — saturated reds, soft pinks, warm sky. No black-and-white,
  no grain, no desaturation. Imagery is not the carrier of the brand mood;
  paper-and-ink typography is. Photos appear at most once per page.

### Corner radii
- Inputs / chips: `6px` (`--radius-sm`)
- Buttons: `8px` (`--radius-md`)
- Cards / dropdowns / browser frame: `10–12px` (`--radius-lg`)
- Pills / avatar: `9999px` (`--radius-full`)

### Card anatomy
A typical Japanese-Learning card:
- White (`#fff`) on washi
- 1px `--ink-200` hairline border, **no shadow at rest**
- 12px radius
- 1.1–1.2 rem internal padding
- Sometimes a **4px colored top-stripe** (`border-top: 4px solid {{ module.color_code }}`)
  for module identity
- On hover: border darkens, `translateY(-1px)`, `--shadow-card` appears.
- Special states: `is-locked` → opacity 0.55; `is-complete` → matcha tint
  background + matcha border; `is-next` → pulsing shu ring.

---

## ICONOGRAPHY

The brand has **no proprietary icon set**. The codebase uses three layers:

1. **Brand mark — あ-Hiragana glyph (since 2026-04-29).** The current logo is
   the hiragana `あ` rendered in **Klee One** (Google Fonts, weight 600), color
   `var(--kon)`. Wordmark "Japanese Learning" in **Inter** (weight 500); tagline
   "JLPT N5 · auf Deutsch" in **Inter** uppercase, letter-spacing `0.18em`,
   color `#8a7355` (bronze). Reference: `app/templates/base.html` `.topnav-brand`
   block; standalone SVG: `app/static/img/logo-mark.svg`; favicon:
   `app/static/favicon.svg` (navy box, cream `あ`). The previous **hand-drawn
   torii** (`assets/torii-logo.svg`) is **deprecated** — kept in `assets/` for
   historical reference only. Do not reintroduce.

2. **Font Awesome 6 (CDN)** for all UI iconography. Loaded from
   `https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css`.
   Used by tag (`<i class="fas fa-book-open"></i>`). Stroke is medium weight,
   one consistent style (`fas` solid). Common glyphs in the live UI:
   `fa-route`, `fa-book-open`, `fa-brain`, `fa-th-list`, `fa-bolt` (N5 bundle),
   `fa-user-circle`, `fa-shopping-bag`, `fa-graduation-cap`, `fa-chart-bar`,
   `fa-cog`, `fa-sign-out-alt`, `fa-sign-in-alt`, `fa-user-plus`, `fa-bars`,
   `fa-times`, `fa-pencil-alt`, `fa-chevron-down`, `fa-home`, `fa-shopping-bag`.

3. **Emoji as functional icons.** Streak 🔥, level ⚡, lock 🔒, check ✅,
   review 🧠, path 📚, flags 🇨🇭🇩🇪🇬🇧, and per-module icons set in admin
   (`m.icon_emoji`, default `📖`).

### Logos & visual assets
- **Current brand mark:** `あ` in Klee One (no SVG file in `assets/` — see
  `app/static/img/logo-mark.svg` in the live repo)
- `assets/torii-logo.svg` — *deprecated* legacy torii (kept for history)
- `assets/favicon.svg` — *deprecated* torii favicon. Live favicon is now
  `app/static/favicon.svg` (navy box with cream `あ`).
- `assets/favicon-16.png`, `favicon-32.png`, `favicon.png` — raster favicon family
- `assets/apple-touch-icon.png` — iOS home-screen icon
- `assets/og-image.png` — 1200×630 social card

### Recommended approach when designing
- **Brand mark:** the `あ`-Hiragana glyph in Klee One (see Iconography §1).
  Default `color: var(--kon)`. Do not reintroduce the legacy torii.
- **UI icons:** Font Awesome 6 (CDN, `fas` style). For a fresh design that needs
  to feel native, prefer Font Awesome over Lucide/Heroicons — the live product
  is Font Awesome-shaped.
- **Status icons:** the curated emoji vocabulary above. Don't invent new ones.
- **Never:** hand-roll an SVG icon for something Font Awesome already provides;
  use bluish-purple gradient icons; use line-and-fill mixes (the system is solid only).

---

## Design moves you should reach for

- Open with an **eyebrow chip** + **two-line H1 with hard line-break** + sub +
  dual CTA (`btn-shu` primary, `btn-ghost-jp` secondary).
- Below the hero, place a **browser frame** (`.home-browser-frame`) showing
  product content as a "design moment".
- Module / content cards in an auto-fill grid, hairline borders, optional
  4px top-stripe in `module.color_code`.
- **Bundle hint banner**: kon-50 background, 3px shu left-border, inline link
  to detail.
- Sticky topnav, never floating; fixed bottom-nav on mobile.
- Use Japanese pigment names in CSS variable names so future contributors absorb
  the brand language by editing.

---

## How to use this system

The fastest path:
1. `<link rel="stylesheet" href="colors_and_type.css">` — every token + sensible
   element defaults are here.
2. Inline `<svg>` from `assets/torii-logo.svg` for the brand mark.
3. Pull Font Awesome from CDN.
4. Reach for `ui_kits/marketing/index.html` and `ui_kits/learn_app/index.html`
   when you need real component recipes — they are pixel-honest recreations of
   the live product.

For brand questions not covered here, the **About page** (`templates/ueber.html`)
and the **Lernmethode page** (`templates/lernmethode.html`) are the two best
voice references in the codebase.
