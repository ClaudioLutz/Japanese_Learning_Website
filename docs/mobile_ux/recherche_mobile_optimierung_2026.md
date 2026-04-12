# Mobile-Optimierung — Recherche & Umsetzungsplan

**Datum:** 2026-04-12
**Kontext:** Japanese Learning Website — Mobile UX auf japanese-learning.ch
**Ziel:** Web App mobil-freundlicher machen: Swipe-Bug fixen, Filter-UX ueberarbeiten, Auto-Load, allgemeine Mobile-Verbesserungen.

---

## 1. Gemeldete Bugs

### 1.1 Swipe-Navigation springt nach oben

**Problem:** Wischt man auf Mobile nach links/rechts, um innerhalb einer Lektion zur naechsten Seite zu wechseln, scrollt die Seite nach oben — der User verliert seine Position.

**Ursache:** In `lesson_view.html` rufen die Navigationsfunktionen explizit `window.scrollTo({ top: 0 })` auf:

| Funktion | Zeile | Code |
|---|---|---|
| `previousPage()` | 1729 | `window.scrollTo({ top: 0, behavior: 'smooth' })` |
| `nextPage()` | 1738 | `window.scrollTo({ top: 0, behavior: 'smooth' })` |
| `goToPage()` | 1752 | `window.scrollTo({ top: 0, behavior: 'smooth' })` |

Der Swipe-Handler (`handleSwipe()`, Zeile 1824-1837) ruft `previousPage()` / `nextPage()` auf, die dann das scrollTo ausfuehren.

**Loesung:** `window.scrollTo({ top: 0 })` aus `previousPage()` und `nextPage()` **entfernen**. In `goToPage()` beibehalten (dort macht es Sinn — der User klickt bewusst in der Sidebar auf eine bestimmte Seite, da will er oben anfangen). Zusaetzlich: Swipe-Threshold von 50px auf 80px erhoehen und eine Y-Achsen-Pruefung (`touchStartY` vs `touchEndY`) einbauen, damit vertikales Scrollen nicht faelschlicherweise als Swipe erkannt wird.

### 1.2 Lektionen erst nach "Apply Filter" sichtbar

**Problem:** Wenn man `/lessons` oeffnet (besonders mit `?language=german`), sieht man nur Kategorien-Cards + den Filter-Bereich. Die eigentlichen Lektionen erscheinen erst, nachdem man eine Kategorie anklickt ODER "Apply Filters" drueckt.

**Ursache:** `lessons.html` zeigt im Default-View die Kategorien-Ansicht (`currentView = 'categories'`). Der User muss entweder:
- Auf eine Kategorie-Card klicken → `showCategoryLessons()` → wechselt zu `currentView = 'lessons'`
- Oder "Apply Filters" klicken → `applyFilters()` → filtert und zeigt Lektionen

**Loesung:** Zwei Aenderungen:
1. **Auto-Submit bei Filter-Aenderung** — Jede Aenderung an den Dropdowns (`change`-Event) loest automatisch `applyFilters()` aus. Der "Apply Filters"-Button wird zum visuellen Indikator reduziert oder ganz entfernt.
2. **Lektionen initial anzeigen** — Bei Seitenaufruf (besonders mit `?language=`-Parameter) die Lektionen direkt als Liste anzeigen UND die Kategorien als optionalen Filter oben belassen.

### 1.3 Mobile-Filter verdecken den Inhalt

**Problem:** Die Filter-Card (4 Selects + Button) ist auf Mobile immer sichtbar und nimmt ~40% des Viewports ein. Der eigentliche Inhalt (Kategorien, Lektionen) wird weit nach unten gedrueckt.

**Ursache:** `filter-card` ist ein statisches `div.card` mit `col-md-*`-Layout. Auf Mobile stapled es alle Filter vertikal (100% Breite pro Select) — ~300px Hoehe.

**Loesung:** Auf Mobile (< 768px) die Filter in ein **collapsibles Akkordeon** oder einen **Bottom-Sheet-Trigger** umbauen:
- **Empfehlung: Akkordeon** (weniger komplex, passt zum bestehenden Stack)
- Ein Button "Filter" mit Badge (Anzahl aktiver Filter) — Klick oeffnet/schliesst den Filter-Bereich
- Default: Collapsed (geschlossen)
- Active-Filter-Chips unter dem Button sichtbar (immer)
- Desktop: Wie bisher, keine Aenderung

---

## 2. Recherche: Mobile Web App Best Practices 2026

### 2.1 Swipe & Gestures — State of the Art

**Quellen:**
- [Mobile Navigation UX Best Practices 2026](https://www.designstudiouiux.com/blog/mobile-navigation-ux/)
- [Mobile-First UX Patterns 2026](https://tensorblue.com/blog/mobile-first-ux-patterns-driving-engagement-design-strategies-for-2026/)

**Best Practices:**
- Swipe fuer Navigation nur bei linearem Content (z.B. Karussell, Seiten)
- **Immer sichtbare Backup-Navigation** (Buttons, Tabs) — nicht alle User entdecken Gesten
- Swipe-Threshold: **80-100px** horizontal, Winkel-Check (< 30 Grad zur Horizontale)
- Y-Achsen-Sperre: Vertikales Scrollen darf Swipe NICHT ausloesen
- Kein Zwangs-Scroll nach Transition — User bleibt wo er ist
- **Haptic Feedback** (optional, via `navigator.vibrate(10)`) bei Seitenwechsel

### 2.2 Filter-Patterns — State of the Art

**Quellen:**
- [NNG: Bottom Sheets Guidelines](https://www.nngroup.com/articles/bottom-sheet/)
- [NNG: Accordions on Mobile](https://www.nngroup.com/articles/mobile-accordions/)
- [Filter UI Examples 2026](https://arounda.agency/blog/filter-ui-examples)
- [Mobbin: Bottom Sheet Patterns](https://mobbin.com/glossary/bottom-sheet)

**Best Practices:**
- **Bottom Sheet** ist 2026 Standard fuer sekundaere Inhalte (Filter, Settings, Sharing)
- Fuer wenige Filter (< 6): **Collapsible Akkordeon** reicht
- Fuer viele Filter: **Bottom Sheet** mit eigenem Scroll
- **Active-Filter-Chips** immer sichtbar (zeigen was aktiv ist ohne oeffnen)
- **Auto-Apply** statt expliziter "Apply"-Button — sofortiges Feedback
- **"Reset"** als Link, nicht als Button (weniger visuelles Gewicht)
- **Scrollbare Pill-Navigation** fuer Kategorien (horizontal, wie Instagram Stories)

### 2.3 Allgemeine Mobile-Optimierung

**Quellen:**
- [Top 10 Mobile App Design Best Practices 2026](https://uiuxdesigning.com/mobile-app-design-best-practices/)
- [Enterprise UX Guide 2026](https://fuselabcreative.com/enterprise-ux-design-guide-2026-best-practices/)

**Best Practices:**
- **Tap-Target-Groesse**: Minimum 44x44px (Apple/Google Empfehlung)
- **Bottom Navigation** fuer primaere Aktionen (Thumb-Zone)
- **Skeleton-Loader** statt Spinner beim Laden
- **Pull-to-Refresh** fuer Listen (optional, bei Web eher untypisch)
- **Progressive Disclosure**: Weniger sofort zeigen, mehr auf Interaktion
- **One-Handed Use**: Wichtige Buttons und Aktionen in der unteren Haelfte
- **System Font Stack** fuer optimale Lesbarkeit
- **Reduced Motion** (`prefers-reduced-motion`) respektieren

---

## 3. Weitere Findings aus Code-Analyse

### 3.1 Swipe-Handler hat kein Y-Achsen-Guard

Der aktuelle Handler (`handleSwipe()`) speichert nur `screenX` — keine Y-Koordinate. Das bedeutet: Scrollt ein User diagonal, wird das als Swipe erkannt und die Seite wechselt ungewollt.

```javascript
// IST: Nur X gespeichert
touchStartX = event.changedTouches[0].screenX;
touchEndX = event.changedTouches[0].screenX;

// SOLL: Auch Y speichern, Winkel pruefen
touchStartY = event.changedTouches[0].screenY;
touchEndY = event.changedTouches[0].screenY;
// → abs(deltaY) < abs(deltaX) als Bedingung
```

### 3.2 Lektionen-Seite: Race Condition bei Initialisierung

`loadLessons()` und `loadCategories()` werden parallel aufgerufen (Zeile 152-155). `displayCategories()` wird in beiden aufgerufen — aber wenn `loadLessons()` fertig ist und `categories` noch leer, passiert nichts. Erst wenn `loadCategories()` fertig wird, zeigt es die Kategorien. Das ist fragil.

### 3.3 Fehlende Touch-Feedback auf Karten

Die Kategorie-Cards haben `hover`-Effekte (`translateY(-2px)`, Shadow), aber keine `:active`-Styles fuer Touch. Auf Mobile sieht ein Tap "leblos" aus. Fix: `:active { transform: scale(0.97); transition: 0.1s; }`.

### 3.4 Back-to-Top Button blockiert Inhalt

Der `#backToTop`-Button ist `position: fixed` unten rechts — kann auf Mobile andere Elemente ueberdecken (FAB-Collision mit ggf. vorhandenem Chat-Widget oder Admin-Button).

### 3.5 Filter-Card benutzt Bootstrap Grid (`col-md-*`)

Auf Screens < 768px stapeln die Filter vertikal. Jeder Select nimmt 100% Breite ein. Das ist 4 × volle Zeile + Button = ~320px Hoehe vor dem eigentlichen Inhalt.

---

## 4. Konkreter Umsetzungsplan

### Phase 1: Bug-Fixes (sofort)

| # | Fix | Datei | Aufwand |
|---|---|---|---|
| 1a | `scrollTo(top:0)` aus `previousPage()` und `nextPage()` entfernen | `lesson_view.html:1729, 1738` | 2 min |
| 1b | Y-Achsen-Guard im Swipe-Handler + Threshold auf 80px erhoehen | `lesson_view.html:1811-1837` | 10 min |
| 1c | Auto-Apply bei Filter-Aenderung (alle Selects → `applyFilters()`) | `lessons.html:587+` | 5 min |
| 1d | Lektionen initial anzeigen statt nur Kategorien | `lessons.html:131-157, 175-213` | 10 min |

### Phase 2: Mobile-Filter Redesign

| # | Fix | Datei | Aufwand |
|---|---|---|---|
| 2a | Filter-Card auf Mobile collapsible (Akkordeon, default collapsed) | `lessons.html:29-78`, `lessons.css` | 30 min |
| 2b | Filter-Toggle-Button mit Active-Filter-Badge | `lessons.html` | 15 min |
| 2c | Active-Filter-Chips (immer sichtbar, klickbar zum Entfernen) | `lessons.html`, `lessons.css` | 20 min |
| 2d | "Apply Filters" Button entfernen (Auto-Apply) | `lessons.html:66` | 5 min |

### Phase 3: Allgemeine Mobile-Verbesserungen

| # | Fix | Datei | Aufwand |
|---|---|---|---|
| 3a | `:active`-Styles fuer Kategorie-Cards + Lesson-Cards | `lessons.css` | 5 min |
| 3b | Tap-Targets >= 44px pruefen (Buttons, Links) | `custom.css` | 10 min |
| 3c | `scrollIntoView` statt `scrollTo(0,0)` bei `goToPage()` (optional) | `lesson_view.html:1752` | 5 min |

---

## 5. Quellen

### Mobile UX
- [Mobile Navigation UX Best Practices 2026](https://www.designstudiouiux.com/blog/mobile-navigation-ux/)
- [Mobile-First UX Patterns 2026](https://tensorblue.com/blog/mobile-first-ux-patterns-driving-engagement-design-strategies-for-2026/)
- [Top 10 Mobile App Design Best Practices 2026](https://uiuxdesigning.com/mobile-app-design-best-practices/)
- [Mobile-First UX Design: Best Practices 2026](https://www.trinergydigital.com/news/mobile-first-ux-design-best-practices-in-2026)

### Filter-Patterns
- [NNG: Bottom Sheets Guidelines](https://www.nngroup.com/articles/bottom-sheet/)
- [NNG: Accordions on Mobile](https://www.nngroup.com/articles/mobile-accordions/)
- [Filter UI Examples for SaaS 2026](https://arounda.agency/blog/filter-ui-examples)
- [Filter UI Patterns That Work 2025](https://bricxlabs.com/blogs/universal-search-and-filters-ui)
- [Mobbin: Bottom Sheet Patterns](https://mobbin.com/glossary/bottom-sheet)

### Accordion
- [Shopify: Accordion UI Design 2026](https://www.shopify.com/blog/accordion-ui-design)
- [Eleken: Accordion UI Examples](https://www.eleken.co/blog-posts/accordion-ui)
- [Cieden: Accordion UI Design](https://cieden.com/book/atoms/accordion/accordion-ui-design)
