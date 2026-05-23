---
name: japanese-learning-design-system
description: Design system for japanese-learning.ch — a Swiss-made, German-language JLPT N5 platform. Use when designing any new surface (marketing page, lesson, dashboard, email, social card) for this product. Brand language is Japanese ink-on-washi: warm paper backgrounds, hairline borders, sumi-ink text, a single hot vermillion (朱 shu) accent for primary action, and German UI copy throughout.
---

# Japanese Learning — Design System

A complete brand + UI system extracted from the live Flask codebase
(`ClaudioLutz/Japanese_Learning_Website`, Compass-Redesign Phase 2) and the
production site at https://japanese-learning.ch.

## What's in here

```
README.md                   ← read first; full narrative on voice, color,
                              type, spacing, shadows, layout, iconography
SKILL.md                    ← this file (skill manifest)
colors_and_type.css         ← every CSS token + sensible element defaults.
                              link this stylesheet first; everything else
                              composes from it.
assets/                     ← logos, favicons, OG image, hero photo
preview/                    ← small per-token cards for the Design System tab
ui_kits/
  marketing/index.html      ← logged-out site recipes (nav, hero w/ browser
                              frame, module grid, bundle hint, pricing, footer)
  learn_app/index.html      ← in-product recipes (review card, lesson drill,
                              dashboard stats, mobile bottom nav, empty states)
```

## When to use

Reach for this system whenever you are designing for **Japanese Learning**:
- New marketing or landing pages
- New in-product surfaces (lessons, reviews, settings, admin)
- Email or social-card templates
- Slide decks about the product
- Press / about / pricing pages

If you are designing something **for a different brand** that just happens to
teach Japanese — do not use this system. The voice ("ehrliche Antwort…",
informal "du", Swiss-engineer skepticism) and the pigment palette are
brand-specific.

## How to use

1. **Link the stylesheet** — `<link rel="stylesheet" href="colors_and_type.css">`.
   Fonts are imported from Google Fonts at the top; tokens are exposed as CSS
   custom properties (`--washi`, `--kon`, `--shu`, `--ink-200`, `--space-8`,
   `--shadow-card`, etc.). Sensible element defaults (`body`, `h1–h3`, `a`,
   `.eyebrow`, `.brand-wordmark`) are applied.

2. **Use the あ-Hiragana mark** (current logo, since 2026-04-29) — render
   `あ` in **Klee One** (Google Fonts, weight 600), color `var(--kon)`. The
   wordmark "Japanese Learning" uses **Inter** (weight 500). Tagline
   "JLPT N5 · auf Deutsch" uses **Inter** uppercase, letter-spacing `0.18em`,
   color `#8a7355` (bronze).
   Live reference: `app/templates/base.html` (`.topnav-brand` block).
   The legacy hand-drawn torii in `assets/torii-logo.svg` is **deprecated** —
   do not reintroduce it.

3. **Pull Font Awesome 6** for UI icons:
   `<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">`.
   Use `fas` (solid) glyphs only. The live product uses Font Awesome — match
   it; don't substitute Lucide or Heroicons.

4. **Lift recipes from the UI kits** — `ui_kits/marketing/index.html` and
   `ui_kits/learn_app/index.html` are the canonical patterns. Class names
   mirror the live `app/static/css/custom.css` (`btn-shu`, `btn-ghost-jp`,
   `eyebrow-chip`, `home-browser-frame`, `module-card`, `bundle-hint`,
   `kana-card`, `review-card`, `stat-pill`). Copy a block, then adapt the
   copy.

5. **Read the README** for tone, casing, pronouns ("du", never "Sie"),
   Swiss-spelling rules ("ss" not "ß"), emoji policy (semantic only — 🔥 ⚡
   🔒 ✅ 🧠 🇨🇭 🇩🇪 🇬🇧, never decorative 🎉 🚀), and the painterly
   `.hero-bg-jp` background recipe.

## The five rules that prevent this from looking generic

1. **Single hot accent.** Vermillion `--shu` is the only saturated color on
   the page. Everything else is warm neutral. Resist adding teal, purple, or
   pastel gradients.
2. **Hairline first, shadow second.** Every card is a 1px `--ink-200`
   border on white. Shadows appear on hover, not at rest. Never both at full
   strength.
3. **Warm neutrals.** Use the `--ink-*` scale for grays — they are
   washi-tinted (warm beige), never cool. If a UI element looks bluish-gray,
   it's wrong.
4. **Type does the heavy lifting.** Geist 510 with `letter-spacing:-0.03em`
   for H1, Fraunces 600 for the wordmark, Noto Serif/Sans JP for any
   Japanese. No decorative SVG flourishes; the type carries the brand.
5. **Voice is direct, never hyped.** Numbers over adjectives. "261 Vokabeln,
   44 Kanji" beats "comprehensive vocabulary library". Use "du", show
   prices, admit limits.

## Quick reference

- **Primary CTA:** `.btn-shu` — vermillion gradient, white text, soft inset
  highlight, `scale(0.96)` on press.
- **Secondary:** `.btn-ghost-jp` — transparent with `--ink-300` border.
- **Eyebrow chip above H1:** `.eyebrow-chip` — uppercase, tracked, optional
  shu border.
- **Active learning module:** `.module-card.is-next` — pulsing 3px shu ring
  (2.4s cubic ease, the system's only continuous animation).
- **Page background:** solid `var(--washi)` everywhere except hero, which
  uses the `.hero-bg-jp` 3-layer painterly gradient.
- **Max content width:** 1152px centered; prose `68ch`; module grid
  `auto-fill, minmax(280px, 1fr)`.

For everything else, the README is the source of truth.
