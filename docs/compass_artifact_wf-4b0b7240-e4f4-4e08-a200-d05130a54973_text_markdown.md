# A design playbook for japanese-learning.ch

**Six references, one palette, one priority order.** Build a cream-and-vermillion learning site with Linear's structural discipline, Stripe's single-price pricing card, Things 3's indie restraint, and Tella's warm gradient skin — rendered in Geist + Inter + Noto Sans JP on a 1152-pixel grid. The research below pins every recommendation to a URL you can open in another tab and a Tailwind token you can paste tonight.

The strategic gap is real: **neither Bunpro nor WaniKani — your two direct competitors — looks designed.** Bunpro feels like a 2018 SaaS dashboard from Osaka; WaniKani is openly described in reviews as "dated and overwhelming," with magenta-and-cyan colors stuck in 2014. There is no Japanese-learning platform that *looks Japanese-thoughtful* (paper-warm, vermillion-accented, bilingually typeset). That's the visual position japanese-learning.ch can occupy on day one — and being the German-speaking option for serious JLPT learners makes the positioning defensible without any feature-race against your competitors.

The rest of this guide is structured for direct execution: six reference sites with concrete patterns, a verified palette in hex, a copy-pasteable `tailwind.config.js`, four CSS gradient recipes, a logo evolution path, and a four-week build order.

---

## The shortlist: six references, ranked by relevance

The picks below are intentionally split across three lanes — **structural** (Linear, Stripe, Vercel set the grammar), **tonal** (Things 3, Readwise, Tella give you warmth and pacing), and **specialist** (Mercari, Nendo, Brilliant inform individual decisions). Open all six in tabs before sketching.

### 1. Linear — linear.app (the structural backbone)

Linear's homepage is the cleanest **hero grammar** on the modern web: an eyebrow announcement chip, a tightly tracked H1 in Inter Display at ~48px weight 510, an 18px subhead with 1.6 line-height, a dual CTA row (filled primary + ghost secondary), and a polished product visual below — all on a single-column, center-aligned layout. Open `linear.app/pricing` to see the same restraint applied to commerce, and `linear.app/brand` for their published tokens. **What to copy:** the eyebrow→H1→subhead→dual-CTA→visual sequence (replace eyebrow with "JLPT N5 · auf Deutsch"), the 5-step neutral gray ramp, the 4px spacing base with 8px primary rhythm, the 8–12px card border radii, and the 1.5px stroke icons (use **Lucide** as the free equivalent of their custom set). **What to skip:** Linear's dark-first canvas, their `#5E6AD2` indigo (it screams Silicon Valley, not Japan), and their "Most popular" tier framing — you have one product. Their unusual font-weight choice of **510** instead of 500 is worth borrowing exactly: it's the secret to why their typography reads as more refined than Inter Medium elsewhere.

### 2. Stripe — stripe.com/pricing (the single-price template)

Stripe's pricing page is **the most directly applicable model for a CHF 9.90 product** — they too sell one transactional concept ("2.9% + $0.30") rendered as a poster-headline figure, supported by a "no setup fees · no monthly fees · no hidden fees" trust triplet. Adopt this verbatim: render **CHF 9.90** at hero scale (~80px), set "einmalig · lebenslang · ohne Abo" as a three-part trust line, and use a single bordered card on whitespace instead of a tier comparison. Stripe's **card chrome** — 1px `#E0E6EB` border + the subtle compound shadow `0 1px 1px rgba(0,0,0,.03), 0 3px 6px rgba(18,42,66,.02)` — is the most "polished but humble" pattern of the three structural references; use it for your nine homepage module cards. **What to skip:** their full WebGL animated gradient (excessive for an indie site — replace with a static CSS conic-gradient), their licensed Söhne typeface (a five-figure license — Geist is the free near-equivalent), and any "Contact sales" framing.

### 3. Vercel — vercel.com (the typography donor)

Vercel matters less for layout copying and more because **Geist Sans landed on Google Fonts in November 2024** as a free, variable, 9-weight family with full Latin Extended (so your `ä ö ü ß` are covered). Geist was explicitly designed as Vercel's reading of Inter / Suisse Int'l / SF Pro — the exact lineage you want — and pairs with **Geist Mono** for romaji and code-style accents. Open `vercel.com/geist/typography` for the published 72/64/56/48/40/32/24/20/16/14 type scale and **`vercel.com/geist/colors`** for their 10-step gray ramp; both are token systems you can lift wholesale. Their "monochrome canvas + one moment of color" pattern (a single animated gradient button against pure black) is exactly the **register** to adopt — but invert it to your washi-cream canvas. **Skip** the pure-black aesthetic and the developer-tools framing; both are wrong for a learning brand.

### 4. Things 3 — culturedcode.com/things (the indie soul-mate)

This is the highest-relevance lateral reference in the entire research. **Cultured Code is a Stuttgart-based indie team** selling premium one-time-payment software with a website that looks like the Platonic ideal of "calm, paid, indie, designed" — essentially Swiss-Japanese sensibility applied to productivity software. The off-white `#F5F5F7`-ish background, the single accent (Things blue ~`#2998FF`), the press-quote pattern rendered as **typography-only** (no logo wall, no photo grid — just the quote and the source name in small caps below) is the most dignified social-proof pattern available, and works for an indie product that doesn't yet have enterprise customers to flex. Their honest "no subscription, one-time price" framing maps 1:1 onto your CHF 9.90 model. **What to copy:** the wide 24–32px gutters, the typography-only testimonials, the single-accent discipline, and the App Store-link prominence repurposed as a "Jetzt kaufen" anchor button. **Skip:** their App Store-only distribution (you need an in-browser checkout) and their pure-prestige refusal to show numerical metrics — you do need a small reassurance line ("über 500 Lernende" or a Trustpilot badge) at CHF 9.90.

### 5. Readwise — readwise.io (the learning narrative)

Readwise targets adult lifelong learners who already use spaced repetition — **the same audience profile as JLPT/Anki users.** Their narrative arc is directly liftable: a three-step "how it works" panel labeled **Sync → Review → Remember**, which translates to **Lernen → Wiederholen → Behalten** without losing meaning. Their **tweet-as-testimonial cards** (rendered as Twitter-screenshot frames with avatar, handle, and quote) are far warmer than enterprise logo walls and are achievable for an indie product without big-name customers. Their pricing copy — "for the same cost as two cups of coffee per month" — should be culturally relocalized: **"CHF 9.90 ist weniger als ein Kaffee in Zürich"** is concrete, Swiss-specific, and lowers the purchase barrier in a way only a local would write. **What to copy:** the three-step panel, the tweet-card testimonials (cap at 4–6 to maintain calm), the device-screenshot hero showing the bundle materials in context, and the single filled CTA in the hero. **Skip:** their slightly dated 2020-era hero illustrations.

### 6. Tella — tella.com (the gradient warmth donor)

Tella is a small founder team running a screen-recording product with a **light-first cream canvas, multi-stop pastel gradients (peach → lilac → mint → soft yellow), and a polished-but-warm vibe** that walks the exact line you need: premium without being corporate, warm without being childish, indie without looking unfinished. Open `tella.com` and notice how a single subtle horizontal gradient band turns a cream page into something that feels deliberate and modern. Their floating "browser-chrome" frame for product previews is ideal for showing PDF workbook pages, Anki deck exports, or audio-player UI as hero/feature visuals. **What to copy:** the gradient band as hero atmosphere (your variant: `linear-gradient(135deg, #FCE4EC 0%, #FFF5E6 35%, #E8F0E3 70%, #F5F2EB 100%)` over the washi base, or a more disciplined indigo-vermillion wash — see the gradient recipes below), the two-line "X in the morning / Y in the afternoon" headline structure (**"Hiragana am Morgen. Kanji am Abend."**), and the customer-quote scrolling marquee. **Skip:** their dense in-page video showcases (too heavy for one indie product) and their navigation depth (you have one product — collapse to three pages max).

### Three supporting references worth opening once

Three more sites earn a mention without making the main shortlist. **Mercari** (`design.mercari.com`) is the canonical reference for **bilingual Japanese-Latin typography** — their custom Mercari Sans was explicitly designed by Monotype's Akira Kobayashi to harmonize with Tazugane Gothic at matched x-height, and the principle (treat JP as equal-hierarchy, not as a translation afterthought) is exactly what your kana-and-kanji-mixed lessons need. **Nendo** (`nendo.jp/en/`) is the *ma* (間, negative space) masterclass — open it once, observe what discipline at the extreme looks like, then dial back 30% for your own use. **Brilliant.org** post-2023 is the closest premium-learning tonal reference, with a clean 3-tier pricing comparison and the CoFo Robert + CoFo Sans pairing as inspiration for your Geist + Inter system; just resist their "Koji" mascot illustrations, which drift toward Duolingo territory.

---

## The aesthetic system: typography, color, spacing

### Typography pairing (verified on Google Fonts, April 2026)

The recommended **primary stack** is `'Inter', 'Noto Sans JP', system-ui, sans-serif` for body and `'Geist', 'Inter', system-ui, sans-serif` for display headings. This is not a guess — it's how browser per-glyph fallback actually works: Inter is tried first for Latin including ß/ä/ö/ü, and any Japanese characters in the same string silently fall through to Noto Sans JP. **Critical implementation detail:** declare `<html lang="de">` and wrap inline Japanese in `<span lang="ja">…</span>` — without it, Firefox and Chrome sometimes pick Chinese fallback fonts that render kanji incorrectly (食 looks visibly wrong).

Use the Google Fonts version of **Noto Sans JP**, not the desktop CJK JP bundle — Google Fonts auto-slices Noto Sans JP into ~120 unicode-range chunks so the browser only downloads the kana slice (~30KB) plus the kanji slices that actually appear on the rendered page. Self-hosting Noto Sans CJK JP would ship 5–20MB. The single `<link>` tag below covers Geist + Inter + Geist Mono + Noto Sans JP at the four weights you'll need:

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&family=Inter:wght@400;500;600;700&family=Geist+Mono:wght@400;500&family=Noto+Sans+JP:wght@400;500;700&display=swap">
```

For long-form grammar essays where you want a more literary register, the **alternate stack** is Newsreader + Source Serif 4 + Shippori Mincho — useful for individual lesson pages but not for the marketing landing.

### Color palette: washi cream + sumi ink + shu vermillion

The palette below combines minimalist-tech discipline with culturally accurate Japanese references. The traditional shu-iro hex you guessed (`#E94E3B`) reads slightly pink on a warm background; the **canonically attested digital equivalent is `#EB6101`** (cited by Wikipedia's traditional Japanese colors, the Sanzō Wada / DIC reference, and noborimaker.com). It matches the actual Fushimi Inari torii-gate red and reads as confident, not shouting.

| Token | Japanese name | Hex | Purpose |
|---|---|---|---|
| `washi` | 和紙 (paper) | **`#FAF7F2`** | Page background — warm, paper-like |
| `kinari` | 生成 (unbleached) | `#F5F0E8` | Alternate sections, panel backgrounds |
| `white` | — | `#FFFFFF` | Cards on washi, modals (so they pop) |
| `sumi` | 墨 (ink) | **`#1C1C1C`** | Primary text, primary buttons |
| `tetsu` | 鉄黒 (iron) | `#2C2C2C` | Body text (slightly softer than sumi) |
| `kon` | 紺 (deep indigo) | **`#1F2A44`** | Primary accent — restrained, ink-navy |
| `ai` | 藍 (indigo) | `#264F7E` | Links, focus rings |
| `shu` | 朱色 (vermillion) | **`#EB6101`** | CTA, JLPT badge, focused state — one accent per viewport |
| `kincha` | 金茶 (golden brown) | `#C7802D` | Premium tertiary, "early bird" badges |
| `matcha` | 抹茶 | `#7A9033` | Optional success / "answer correct" |

The grayscale ramp (50–950) is **warm-tinted** to harmonize with washi: `#FAF7F2 / #F1EDE6 / #E4DED4 / #D4CCBE / #A8A095 / #7A7368 / #5C564D / #403B34 / #2C2924 / #1C1A17 / #0F0E0C`. These avoid the cool-blue cast of Tailwind's default `slate` and `gray` scales.

The **culturally specific moves** that distinguish this from yet-another-tech-startup palette are: ink-navy (`kon`) instead of pure blue, vermillion as a *single* accent rather than a multi-hue gradient, and warm grays instead of cool slate. Reserve the vermillion for **one element per viewport** — a primary CTA, an active-state indicator, or a JLPT-level badge. Restraint reads as premium; profligacy reads as cheap.

### Spacing, radii, type scale

Standardize on **`max-w-6xl` (1152px)** as the default container width — narrower than 1280px, calmer for a content-heavy reading site, and aligned with how Stripe (1080px) and Goodpatch (~1100px) constrain attention. Reserve `max-w-7xl` for the marketing landing only and `max-w-prose` (68ch) for long-form grammar articles. Use **`rounded-lg` standardized to 12px** for cards (Linear and Vercel both sit in the 8–12px range; 16px starts to feel consumer-y), `rounded-md` 8px for buttons and inputs, and `rounded-2xl` 20px reserved for hero containers.

Bump body text to **17px (`1.0625rem`) at 1.7 line-height** rather than the 16px Tailwind default — Japanese kana renders worse than Latin at small sizes, and the extra pixel makes inline `食べる` significantly more legible next to German prose. Tofugu and Bunpro both use ≥17px effective body size for the same reason. Section vertical padding should be **96px desktop / 64px mobile minimum** — generous spacing is what gives you the Nendo *ma* feeling without literal Japanese ornament.

### The complete `tailwind.config.js` snippet

```js
module.exports = {
  content: ['./templates/**/*.html', './app/**/*.py', './static/js/**/*.js'],
  theme: {
    extend: {
      colors: {
        washi:  '#FAF7F2',
        kinari: '#F5F0E8',
        sumi:   '#1C1C1C',
        tetsu:  '#2C2C2C',
        kon:    { DEFAULT: '#1F2A44', 50:'#F2F4F8', 100:'#E1E5EE', 300:'#9AA6BD', 500:'#3F4E72', 700:'#1F2A44', 900:'#121828' },
        ai:     '#264F7E',
        shu:    { DEFAULT: '#EB6101', soft:'#F4D9C7', deep:'#B84A00' },
        kincha: '#C7802D',
        matcha: '#7A9033',
        ink: { 50:'#FAF7F2', 100:'#F1EDE6', 200:'#E4DED4', 300:'#D4CCBE', 400:'#A8A095', 500:'#7A7368', 600:'#5C564D', 700:'#403B34', 800:'#2C2924', 900:'#1C1A17', 950:'#0F0E0C' },
      },
      fontFamily: {
        sans:   ['Geist', 'Inter', 'system-ui', 'sans-serif'],
        body:   ['Inter', 'Noto Sans JP', 'system-ui', 'sans-serif'],
        jp:     ['"Noto Sans JP"', '"Hiragino Sans"', '"Yu Gothic"', 'sans-serif'],
        mono:   ['"Geist Mono"', 'ui-monospace', 'monospace'],
      },
      fontSize: {
        base:   ['1.0625rem', { lineHeight: '1.7' }],
        '5xl':  ['3.75rem',   { lineHeight: '1.05', letterSpacing: '-0.02em' }],
        hero:   ['4.5rem',    { lineHeight: '1.0',  letterSpacing: '-0.03em' }],
      },
      borderRadius: { DEFAULT: '0.5rem', lg: '0.75rem', xl: '1rem', '2xl': '1.25rem' },
      boxShadow: {
        subtle: '0 1px 2px 0 rgba(28,26,23,.04), 0 1px 3px 0 rgba(28,26,23,.06)',
        card:   '0 2px 4px -1px rgba(28,26,23,.06), 0 4px 12px -2px rgba(28,26,23,.08)',
        lifted: '0 8px 24px -4px rgba(28,26,23,.10), 0 2px 6px -2px rgba(28,26,23,.06)',
      },
    },
  },
};
```

### Four gradient recipes you can paste tonight

The hero atmospheric wash is a Linear-style radial in `kon` ink-navy with a faint `shu` vermillion bloom, layered over a vertical washi-to-kinari fade — atmospheric without being theatrical:

```css
.hero-bg {
  background:
    radial-gradient(ellipse 80% 50% at 50% -10%, rgba(31,42,68,.18), transparent 60%),
    radial-gradient(ellipse 60% 40% at 85% 10%, rgba(235,97,1,.08), transparent 55%),
    linear-gradient(180deg, #FAF7F2 0%, #F5F0E8 100%);
}
.btn-primary {
  background: linear-gradient(180deg, #EB6101, #D85700);
  color: #fff;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.15), 0 1px 2px rgba(184,74,0,.30), 0 0 0 1px rgba(184,74,0,.40);
}
.btn-primary:hover {
  background: linear-gradient(180deg, #F37016, #E25C00);
  transform: translateY(-1px);
}
.section-divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(28,26,23,.18) 50%, transparent);
}
.card-vocab:hover::before {
  background: linear-gradient(135deg, transparent 70%, rgba(199,128,45,.06));
}
```

---

## Page-by-page adaptation strategy

### The hero (homepage)

Adopt **Linear's structural sequence** with **Tella's gradient warmth** and **Things 3's restraint**. Eyebrow chip in 12px Geist 510 small caps reading "JLPT N5 · auf Deutsch · in der Schweiz gemacht"; H1 in 60–72px Geist 510 with -0.03em tracking, two lines maximum (e.g. "Bestehe den JLPT N5 — auf Deutsch erklärt." or the Tella-style two-beat "Hiragana am Morgen. Kanji am Abend."); 18–20px Inter 400 subhead at 1.6 line-height giving the concrete proof point ("31 Lektionen, 261 Vokabeln, 44 Kanji — wöchentlich neu"); dual CTA row with **filled `shu` primary** ("Bundle für CHF 9.90 kaufen") and **ghost secondary** ("Erste Lektion ansehen"); floating product visual below in a Tella-style browser-chrome frame showing a real lesson page. Background: the four-layer hero gradient above. Resist the urge to add a third CTA, a logo wall, or a video autoplay.

### The pricing page (/n5-bundle)

This is the easiest win and should ship first. **Steal Stripe's pricing structure verbatim:** one massive transactional figure ("CHF 9.90" at ~80px Geist 600), one trust triplet ("einmalig · lebenslang · ohne Abo"), one bordered card on whitespace, one filled vermillion CTA. Above the price, a small `kincha`-gold "Early-Bird" badge if the CHF 14.90 reference price is shown. Below the CTA, a Reflect-style three-line reassurance: "Sicher bezahlen mit Stripe · Sofortzugang per E-Mail · 14 Tage Geld-zurück". The "what's included" section is a Linear-style checklist with Lucide check icons in `matcha` green: "9 Module · 31+ Lektionen · 261 Vokabeln · 44 Kanji · Quizze · Audio-Beispiele · lebenslange Updates · Lerngemeinschaft". Add the Readwise-style cultural localization: **"CHF 9.90 ist weniger als ein Kaffee in Zürich"** as a quiet line below the card. No tier comparison. No "Most popular" badge. You have one product.

### The lessons catalog (/lessons)

Synthesize **Bunpro's curriculum-tree IA** (group by JLPT level → Lektion → grammar/vocab point — don't reinvent it; it works), **Maven's card density** (3 cards per row desktop, 1 per row mobile, 32px padding), and **Nendo's restraint** (1px hairline borders in `ink-200` `#E4DED4`, no shadows, no hover-zoom — just a 200ms color-shift on the title to `shu`). Card anatomy: small-caps level label ("N5 · LEKTION 1") in `ink-500` 12px → JP headline in 28px Noto Sans JP ("だ・です") → German gloss in 18px Inter ("Sein, ist") → metadata row ("12 Punkte · ~25 Min") in `ink-500` 14px → arrow-only affordance, no button chrome. White card on the washi page background with a single 1px hairline border is the most "Japanese paper" thing you can do in CSS — and it's free.

### Individual lesson pages (/lessons/:id)

Constrain prose to `max-w-prose` (68ch) — the right line length for German-plus-kana mixed text. Vocab cards use the gradient corner-accent treatment from recipe C, with the JP term in 32px Noto Sans JP, romaji in 14px Geist Mono in `ink-500`, and the German gloss in 17px Inter. Grammar explanations use the editorial alternate stack (Newsreader + Shippori Mincho) for body if you want the literary register, sans-serif if you want consistency with the rest of the site — pick one and commit. Quiz UI: filled `shu` for the active answer, `matcha` for confirmed-correct, `ink-300` borders elsewhere. Furigana rides above kanji at 60% opacity in Noto Sans JP — the standard Japanese-publishing treatment.

### The torii logo: evolve, don't replace

Three directions emerged from the research, ranked by risk. **Direction A (recommended): a monoline torii** — reduce the current logo to a single 1.5–2px stroke at 24px, two horizontal beams (kasagi + nuki) over two columns (hashira), rendered in `currentColor` SVG so it inherits whatever text color the surrounding context uses (the same trick Linear's chevron and Vercel's triangle rely on). This preserves brand equity with existing users while gaining tech-minimal rigor. The exact SVG is six paths in a 24×24 viewBox. **Direction B (12-18 months out):** abstract the torii to a "Π" sigil placed inside a soft 12px-radius `sumi` chip with the glyph in `shu` — this is the Linear/Vercel/Raycast school where the mark stops being illustration and becomes typography. **Direction C** (torii + 学 hybrid) is too detail-dependent for favicon scale; skip it.

---

## Build order: what to ship in what order

Ship the **pricing page first**. It's structurally the simplest, requires only the type system and one card pattern, will validate the palette and gradient against real conversion behavior, and is the page closest to revenue. Two days of work, including the Stripe-style "CHF 9.90" hero figure and the trust triplet. **Second**, the homepage hero — same primitives plus the gradient atmosphere and the dual CTA. Three days. **Third**, the lessons catalog: build one card component well, repeat it 31 times, ship the filter chrome later. Three days. **Fourth and last**, the individual lesson pages: most of the long-tail content effort lives here, but visually you're now just applying the system you've already built.

Defer entirely until v1.1: dark mode (a Swiss-Japanese paper aesthetic *lives* in light mode — a half-baked dark mode will weaken the brand), animated WebGL anything (use static CSS gradients), and any logo wall or enterprise-style social proof. The Things 3 and Readwise references give you typography-only quotes and tweet-card testimonials that work without a single Fortune 500 customer.

---

## Don't import: the anti-patterns

Three families of patterns appear across the references but **must not** be copied to a CHF 9.90 indie learning product. **Enterprise framing:** Linear/Stripe/Vercel all use "Contact sales", "Enterprise tier", and customer-logo strips — wrong register entirely. **Mascot illustration:** Brilliant's Koji blob, Duolingo's owl, WaniKani's crab — all signal "kids' product." Your audience is adult JLPT-aspiring hobbyists; trust them with restraint. **Calligraphy or washi-texture imagery:** the paper feeling must come from the cream hex and the spacing rhythm, never from a noisy texture image or a brushed-script font. Calligraphy executed badly is the single biggest tell of a Western-built "Japanese-themed" product, and a JPG of washi paper as a background asset is the design crime equivalent of a stock photo of a sushi roll. Stick to clean gothics and warm hex codes — that's where the cultural specificity actually lives.

## Conclusion: the playbook in one sentence

Build **Linear's hero structure** with **Stripe's single-price card** and **Things 3's typographic restraint**, render it in **Geist + Inter + Noto Sans JP** on a **`#FAF7F2` washi canvas** with a **single `#EB6101` vermillion accent** and **`#1F2A44` ink-navy headers**, ship the pricing page first, defer dark mode, simplify the torii to a monoline currentColor SVG, and use the Readwise three-step "Lernen → Wiederholen → Behalten" to give German-speaking JLPT learners a reason to believe this is the first Japanese-learning platform that *looks* designed. The visual position is unclaimed, the technical implementation is two weeks of focused work, and every recommendation above resolves to a URL, a hex code, or a Tailwind class you can act on tonight.