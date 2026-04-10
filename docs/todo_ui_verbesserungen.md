# UI-Verbesserungen -- TODO & Konzept

**Datum:** 2026-04-10
**Status:** In Arbeit

---

## TODO-Liste

### Bugs (Prioritaet 1)
- [ ] **"Unable to Load Courses" fixen** -- `/api/courses` hat kein Error-Handling und stuerzt bei DB-Fehler ab (fehlende Spalte `failed_login_count`). Sofort-Fix: try-except + DB-Migration ausfuehren.
- [ ] **CSP-Nonce-Konflikt mit Talisman** -- `content_security_policy_nonce_in` blockiert alle Inline-Scripts. Fix: auf `[]` gesetzt, muss bei naechstem Commit mit eingecheckt werden.

### Admin-Edit-Button verfeinern (Prioritaet 2)
- [ ] **`?edit=ID` statt `?focus=ID`** -- Der Floating-Button soll direkt den Edit-Modal oeffnen, nicht nur zur Zeile scrollen. Erfordert `autoEditFromUrl()`-Funktion in `_js_core.html` und `manage_courses.html`.
- [ ] **Seiten-spezifischer Kontext** -- Bei Lektionsansicht mit Seiten (z.B. "Seite 2 von 5") koennte der Link die aktuelle Seite mit uebergeben: `?edit=131&page=2`.

### Audio-Player aufwerten (Prioritaet 3)
- [ ] **Custom Audio Player** -- Nativen `<audio controls>` durch eigenen Player ersetzen mit:
  - Grosser runder Play-Button (Duolingo-Stil, 80px)
  - Puls-Animation waehrend Wiedergabe
  - Wellenform-Animation (5 animierte Balken)
  - Fortschrittsbalken mit Zeitanzeige
  - Geschwindigkeitsregler (0.75x / 1x / 1.25x)
- [ ] **"Vorlesen"-Buttons aufwerten** -- Dezenter Unterstrich + Speaker-Icon neben klickbaren japanischen Texten

### Farbpalette & Visuelle Konsistenz (Prioritaet 4)
- [ ] **"Zen Learning" Farbpalette einfuehren** -- Japanisch inspirierte Farben statt generisches Bootstrap-Blau
- [ ] **CSS Custom Properties konsolidieren** -- Hardcodierte Werte durch Tokens ersetzen
- [ ] **Typografie-Hierarchie festlegen** -- Max. 4 Schriftgroessen pro Seite

### Mobile-Optimierung (Prioritaet 5)
- [ ] **Bottom Navigation Bar** -- Fixierte Leiste unten: Zurueck, Seitenzahl, Weiter
- [ ] **Sidebar als Drawer** -- Slide-In von links statt fester Sidebar
- [ ] **Touch-Targets** -- Alle interaktiven Elemente auf min. 44x44px
- [ ] **Content-Breite** -- Lektions-Content auf max. 900px (Lesebreite)

### Micro-Interactions & Polish (Prioritaet 6)
- [ ] **Button-Feedback** -- `transform: scale(0.96)` beim Klick
- [ ] **Quiz-Animationen** -- Shake bei falsch, Pulse bei richtig
- [ ] **Fortschrittsbalken-Shimmer** -- Schimmer-Effekt auf Progress-Bars
- [ ] **prefers-reduced-motion** -- Animationen respektieren
- [ ] **Seiten-Uebergaenge** -- Sanftes Fade-In beim Seitenwechsel

---

## Detaillierte Vorschlaege

### 1. Audio Player -- Custom Design

**Problem:** Nativer `<audio controls class="w-100">` sieht in jedem Browser anders aus, wirkt technisch und langweilig. Fuer eine Lernplattform, wo Audio zentral ist, unzureichend.

**Loesung -- Duolingo-Inspirierter Speaker-Button:**

```html
<div class="audio-exercise">
    <button class="audio-speaker-btn" onclick="playAudio(this, 'audio_url')">
        <i class="fas fa-volume-up"></i>
        <div class="audio-wave">
            <span></span><span></span><span></span><span></span><span></span>
        </div>
    </button>
    <div class="audio-progress">
        <div class="audio-progress-bar"></div>
    </div>
    <span class="audio-time">0:00 / 0:37</span>
</div>
```

```css
.audio-exercise {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--space-4);
    padding: var(--space-8) var(--space-6);
    background: var(--color-surface);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-sm);
}

.audio-speaker-btn {
    width: 80px; height: 80px;
    border-radius: 50%;
    background: var(--color-primary);
    border: none; color: white;
    font-size: 2rem;
    cursor: pointer;
    transition: transform 0.2s, box-shadow 0.2s;
    position: relative;
}
.audio-speaker-btn:hover { transform: scale(1.08); }
.audio-speaker-btn.is-playing {
    animation: pulse-ring 1.5s ease-out infinite;
}
.audio-speaker-btn.is-playing .fa-volume-up { display: none; }
.audio-speaker-btn .audio-wave { display: none; }
.audio-speaker-btn.is-playing .audio-wave { display: flex; }

@keyframes pulse-ring {
    0% { box-shadow: 0 0 0 0 rgba(74,144,226,0.4); }
    70% { box-shadow: 0 0 0 15px rgba(74,144,226,0); }
}

/* Wellenform */
.audio-wave {
    gap: 3px; align-items: center; height: 30px;
    justify-content: center;
}
.audio-wave span {
    width: 4px; background: white;
    border-radius: 2px; animation: wave 1s ease-in-out infinite;
}
.audio-wave span:nth-child(2) { animation-delay: 0.15s; }
.audio-wave span:nth-child(3) { animation-delay: 0.3s; }
.audio-wave span:nth-child(4) { animation-delay: 0.45s; }
.audio-wave span:nth-child(5) { animation-delay: 0.6s; }
@keyframes wave {
    0%, 100% { height: 8px; }
    50% { height: 24px; }
}

/* Fortschritt */
.audio-progress {
    width: 100%; max-width: 300px;
    height: 4px; background: var(--color-border);
    border-radius: var(--radius-full);
    overflow: hidden;
}
.audio-progress-bar {
    height: 100%; width: 0%;
    background: var(--color-primary);
    transition: width 0.1s linear;
}
```

**Geschwindigkeitsregler (optional):**
```html
<div class="audio-speed-controls">
    <button class="speed-btn" data-speed="0.75">0.75x</button>
    <button class="speed-btn active" data-speed="1">1x</button>
    <button class="speed-btn" data-speed="1.25">1.25x</button>
</div>
```

---

### 2. Farbpalette -- "Zen Learning"

**Problem:** `#4a90e2` (generisches Blau) + `#50e3c2` (Mint) + Bootstrap-Defaults wirken zusammengewuerfelt. Kein thematischer Bezug zu Japan.

**Vorschlag -- Japanisch inspirierte Farben:**

```css
:root {
    /* Primaerfarben -- Ai-Iro (Indigo) */
    --zen-indigo: #2B4C7E;        /* Navigation, Primaer-Buttons */
    --zen-indigo-light: #3D6098;  /* Hover-States */
    --zen-indigo-dark: #1E3A5F;   /* Active-States */

    /* Akzentfarben */
    --zen-sakura: #E8A0B4;        /* Highlights, Badges, Premium */
    --zen-matcha: #7A9A5A;        /* Erfolg, Fortschritt, korrekt */
    --zen-matcha-light: #C5D5A8;  /* Erfolgs-Hintergrund */
    --zen-vermillion: #D14B3D;    /* Torii-Rot -- Fehler, Warnungen */

    /* Neutrale Toene */
    --zen-washi: #F5F0E8;         /* Hintergrund (warmes Off-White) */
    --zen-sumi: #2C2C2C;          /* Haupttext (Sumi-Tinte) */
    --zen-sumi-light: #5A5A5A;    /* Sekundaertext */
    --zen-stone: #D4CFC5;         /* Rahmen, Trennlinien */

    /* Funktionale Zuordnung */
    --color-primary: var(--zen-indigo);
    --color-primary-hover: var(--zen-indigo-light);
    --color-success: var(--zen-matcha);
    --color-error: var(--zen-vermillion);
    --color-highlight: var(--zen-sakura);
    --color-bg: var(--zen-washi);
    --color-surface: #FFFFFF;
    --color-text: var(--zen-sumi);
    --color-text-secondary: var(--zen-sumi-light);
    --color-border: var(--zen-stone);
}
```

**Warum diese Palette:**
- Warmes Off-White (`#F5F0E8`, Washi-Papier) statt kaltes `#f8f9fa` -- einladender
- Indigo = kultureller Bezug (Ai-Zome-Faerbetechnik), serioes fuer Lernplattform
- Matcha-Gruen fuer Erfolg schafft thematische Kohaerenz
- Sakura fuer Premium/Highlights = sofortige Japan-Assoziation
- Kontrast Sumi auf Washi: ~12:1 (weit ueber WCAG AAA)

**Migration:** Schrittweise -- zuerst `:root`-Variablen definieren, dann Seite fuer Seite hardcodierte Werte ersetzen.

---

### 3. Visuelle Konsistenz -- Design Tokens

**Problem:** Hardcodierte Farbwerte (`#4a90e2`, `#50e3c2`, `#e9ecef`, `#6c757d`, `#495057`) stehen neben CSS-Variablen. Bootstrap-Defaults, Custom CSS und Tailwind (Admin) erzeugen Stilbruch.

**Loesung -- Einheitliches Token-System:**

```css
:root {
    /* Spacing (8px-Basis) */
    --space-1: 0.25rem;  --space-2: 0.5rem;
    --space-3: 0.75rem;  --space-4: 1rem;
    --space-6: 1.5rem;   --space-8: 2rem;
    --space-12: 3rem;    --space-16: 4rem;

    /* Border Radius */
    --radius-sm: 6px;  --radius-md: 12px;
    --radius-lg: 16px; --radius-xl: 24px;
    --radius-full: 9999px;

    /* Shadows (3-stufig) */
    --shadow-sm: 0 1px 3px rgba(0,0,0,0.08);
    --shadow-md: 0 4px 12px rgba(0,0,0,0.1);
    --shadow-lg: 0 12px 40px rgba(0,0,0,0.12);

    /* Typografie */
    --text-xs: 0.75rem; --text-sm: 0.875rem;
    --text-base: 1rem;  --text-lg: 1.125rem;
    --text-xl: 1.25rem; --text-2xl: 1.5rem;
    --text-3xl: 2rem;   --text-4xl: 2.5rem;
}
```

**Regel:** Jede Karte, jeder Button, jedes Badge verwendet die gleichen Token-Werte fuer `border-radius`, `shadow` und `padding`.

---

### 4. Mobile-Optimierung

**Bottom Navigation Bar (statt Sidebar-Navigation auf Mobile):**

```css
@media (max-width: 768px) {
    .mobile-bottom-nav {
        position: fixed; bottom: 0; left: 0; right: 0;
        height: 64px; background: white;
        display: flex; align-items: center;
        justify-content: space-between;
        padding: 0 1rem;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
        z-index: 100;
    }
    body { padding-bottom: 72px; }
}
```

**Sidebar als Drawer:**

```css
@media (max-width: 768px) {
    .lesson-sidebar {
        position: fixed; left: -100%; top: 0;
        width: 85vw; max-width: 320px;
        height: 100vh;
        transition: left 0.3s ease;
        z-index: 1000;
        background: white;
    }
    .lesson-sidebar.is-open { left: 0; }
}
```

**Content-Breite:** `max-width: 900px` fuer Lektions-Content (optimal fuer 65-75 Zeichen Lesebreite).

**Responsive Schriftgroessen:**
```css
:root {
    --text-base: clamp(0.9375rem, 0.5vw + 0.875rem, 1.0625rem);
    --text-xl: clamp(1.25rem, 1vw + 1rem, 1.75rem);
    --text-3xl: clamp(1.75rem, 2vw + 1.25rem, 2.5rem);
}
```

---

### 5. Micro-Interactions

**Button-Feedback (global):**
```css
.btn { transition: transform 0.15s, box-shadow 0.15s; }
.btn:active { transform: scale(0.96); }
```

**Quiz -- Korrekt/Falsch:**
```css
.quiz-option.correct {
    animation: correctPulse 0.4s ease;
    background: #dcfce7; border-color: #22c55e;
}
.quiz-option.incorrect {
    animation: shake 0.4s ease;
    background: #fef2f2; border-color: #ef4444;
}
@keyframes shake {
    0%, 100% { transform: translateX(0); }
    25% { transform: translateX(-6px); }
    75% { transform: translateX(6px); }
}
```

**Fortschrittsbalken-Shimmer:**
```css
.progress-fill::after {
    content: ''; position: absolute; inset: 0;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
    animation: shimmer 2s infinite;
}
@keyframes shimmer { from { transform: translateX(-100%); } to { transform: translateX(100%); } }
```

**Reduced Motion respektieren:**
```css
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: 0.01ms !important;
        transition-duration: 0.01ms !important;
    }
}
```

---

### 6. Fortschrittsanzeigen modernisieren

- **Inchstones:** Kleine Erfolgsmeldungen nach jeder Seite ("3 von 8 Seiten geschafft")
- **XP-Animation** nach Quiz: Punkte fliegen in die Fortschrittsleiste
- **Animierter Fortschrittsbalken** mit Gradient + Shimmer-Effekt
- **Streak-Anzeige:** Tages-Streak mit Flammen-Icon

---

## Umsetzungs-Reihenfolge (Empfehlung)

| Schritt | Massnahme | Aufwand | Wirkung |
|---------|-----------|---------|---------|
| 1 | Courses-Bug fixen | Gering | Kritisch |
| 2 | Admin-Edit-Button -> `?edit=ID` | Gering | Hoch |
| 3 | Zen-Farbpalette + Design Tokens | Mittel | Hoch |
| 4 | Custom Audio Player | Mittel | Hoch |
| 5 | Mobile Bottom-Nav + Drawer | Mittel | Mittel |
| 6 | Micro-Interactions | Gering | Mittel |
| 7 | Fortschritts-Animationen | Hoch | Mittel |
| 8 | Content-Breite + Typografie | Gering | Mittel |

---

## Quellen & Inspiration

- [Tubik Studio -- UI Design Trends 2026](https://blog.tubikstudio.com/)
- [Fireart Studio -- Japanese Minimalism in UI Design](https://fireart.studio/blog/)
- [Hue Atlas -- Japanese Color Palette Guide](https://hueatlas.com/)
- [Beta Soft Technology -- Motion UI Trends 2025](https://www.betasofttechnology.com/)
- [UserGuiding -- Progress Trackers](https://userguiding.com/blog/)
- [Duolingo Micro-Interactions](https://medium.com/@Bundu/) -- Vorbild fuer Lern-App UX
- [Netwise Tokyo -- Web Design Trends Japan 2025](https://www.netwise.jp/blog/)
