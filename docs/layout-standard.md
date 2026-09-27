# Layout-Standard

Stand 2026-09-27. Gilt für alle öffentlichen Seiten (base.html). Grundlage:
Material 3, Refactoring UI, Atlassian, Tailwind UI, NN/g. Umsetzung in
`app/static/css/layout.css` (Tokens + Klassen) und
`app/templates/partials/_page_head.html` (Seitenkopf-Makro). Pilot:
`/practice/kana`.

Ziel: Keine Seite wirkt wie ein schwebender Dialog im leeren Raum. Inhalt beginnt
oben, füllt breite Bildschirme über Spalten statt über gestreckte Zeilen und
sieht auf dem Handy wie eine eigene, gleichwertige Fassung aus.

## 1. Seitenanatomie

```
Header (Top-Nav, 60 px, sticky)
Seitenkopf   Kennzeile · Titel · Untertitel            [Aktionen rechts]
             (optional Tabs direkt darunter)
Inhalt       beginnt direkt unter dem Seitenkopf
Footer       (mobil zusätzlich fixe Bottom-Nav)
```

Vertikal zentriert werden nur Auth-Seiten, Leerzustände und Fehlerseiten.

## 2. Tokens

| Gruppe | Token | Wert | Verwendung |
|---|---|---|---|
| Container | `--container-std` | 1200 px | Übungen, Formulare, Detailseiten |
| | `--container-wide` | 1440 px | Dashboard, Kataloge |
| | `--container-prose` | 680 px | Lesetext |
| | `--container-auth` | 440 px | Login, Registrierung (400–480) |
| Rinne | `--page-gutter` | 16 px | `.page`; auf Desktop +32 px von `main.container` = 48 px |
| Abstand | `--space-1 … -24` | 4 · 8 · 12 · 16 · 24 · 32 · 48 · 64 · 96 | nur diese Stufen (1,2,3,4,6,8,12,16,24) |
| Raster | `--grid-gap` | 16 px mobil, 24 px ab 768 | Kachelabstand; `--grid-gap-dense` 16 px |
| Schrift (×1.25, an 17 px) | `--text-xs` | 12 px | Kennzeile, Badges (Untergrenze) |
| | `--text-sm` | 13.6 px | Hilfstext, Labels |
| | `--text-base` | 17 px | Fliesstext (bestehend, custom.css) |
| | `--text-lg` | 21 px | Karten-Titel |
| | `--text-xl` | 26.6 px | Seitentitel mobil |
| | `--text-2xl` | 33 px | Seitentitel Desktop |
| | `--text-3xl` | 41.5 px | Hero |
| | `--measure` | 68ch | Zeilenlänge Fliesstext (60–80 Zeichen) |
| Flächen | `--surface-0` | Washi / #14120E | Seitenhintergrund |
| | `--surface-1` | #FFF / #1E1B15 | Karten, Paneele |
| | `--surface-2` | #FFF / #28241D | erhöht (Popover, Hervorhebung) |
| | `--surface-inset` | #F1EDE6 / #2A251D | Mulde: Segment-Tracks |
| | `--surface-border(-strong)` | Haarlinie | Rahmen aller Flächen |
| Schatten | `--shadow-1`, `--shadow-2` | dezent im Light, keine im Dark | Dark trennt über Helligkeit |
| Bottom-Nav | `--bottom-nav-h` | 60 px + Safe-Area (< 768), sonst 0 | sticky/fixed Elemente unten |

Breakpoints (in Media-Queries, keine Variablen möglich): **640 / 768 / 1024 /
1280 / 1536**. Mobile-first: Basisregeln gelten fürs Handy, grössere Viewports
kommen per `min-width` dazu. Touch-Ziele mindestens **44 px** hoch.

## 3. Bausteine

| Klasse | Zweck |
|---|---|
| `.page` | Seitenhülle: Standardbreite, Rinne, Inhalt beginnt oben |
| `.page--wide` / `--prose` / `--auth` | Breitenvarianten |
| `.page-head` (+ `__eyebrow`, `__title`, `__sub`, `__sub--desktop`, `__actions`) | Seitenkopf; mobil einspaltig, ab 768 Aktionen rechts |
| `.page-split` (+ `__aside--sticky`, `--aside-w`) | Hauptspalte + Seitenleiste ab 1024, mobil gestapelt |
| `.surface` / `.surface-2` / `.surface-inset` / `--flush` | Flächen, erben Hintergrund, Rahmen, Schatten aus Tokens (beide Themes) |
| `.grid-tiles` (+ `--dense`) | Kachelraster `auto-fill, minmax(280px, 1fr)` |

```jinja
{% from 'partials/_page_head.html' import page_head %}
<div class="page page--wide">
  {% call page_head('Statistik', subtitle='Dein Fortschritt', eyebrow='Fortschritt') %}
    <a class="…" href="…">Exportieren</a>
  {% endcall %}
  <div class="grid-tiles">…</div>
</div>
```

## 4. Sechs Seitenschablonen

Jeweils Desktop (≥ 1024) und Handy (390). Mobil gilt immer: eine Spalte,
16-px-Rinne, Seitenkopf kompakt, primäre Aktion früh und ohne Scrollen
sichtbar (390×844 abzüglich Bottom-Nav), Abstand zur Bottom-Nav, keine Karten
in Karten.

### A. Übungs-Konfiguration (Pilot: /practice/kana) — `.page`

```
Desktop                                      Handy
┌───────────────────────────────────────┐    ┌──────────────┐
│ Kennzeile · Titel · Untertitel        │    │ Kennz.·Titel │
├──────────────────────────┬────────────┤    │ Einstellung 1│
│ Einstellungen            │ Vorschau   │    │ Einstellung 2│
│  Gruppe 1                │ [ Start ]  │    │ Vorschau     │
│  Gruppe 2                │ Schnell…   │    │ [  Start  ]  │
│  Gruppe 3                ├────────────┤    │ Konto-Vorteil│
│                          │ Vorteile   │    │ (Bottom-Nav) │
└──────────────────────────┴────────────┘    └──────────────┘
```
Rechte Spalte 360 px, Start auf 1366×768 im Fold. Mobil folgt der Start direkt
auf die Einstellungen; Einstellungen kompakt (z. B. Chips als eine horizontal
scrollbare Zeile), damit der Start auf 360–414 px im Fold liegt.

### B. Dashboard (/mein-lernen, /review/stats) — `.page--wide`

```
Desktop                                      Handy
┌───────────────────────────────────────┐    ┌──────────────┐
│ Seitenkopf               [Aktion]     │    │ Seitenkopf   │
├────────────────────────┬──────────────┤    │ Hero (Heute) │
│ Hero: nächster Schritt │ Kennzahl     │    │ [ Weiter ]   │
│ [ Weiter ]             │              │    │ Kachel       │
├────────┬────────┬──────┴─┬────────────┤    │ Kachel       │
│ Kachel │ Kachel │ Kachel │ Kachel     │    │ …            │
└────────┴────────┴────────┴────────────┘    └──────────────┘
```
Kacheln über `.grid-tiles`; mobil zuerst Hero mit Aktion, dann Kacheln.

### C. Spiel-/Übungsansicht (/review, laufende Kana-Spiele) — `.page`

```
Desktop                                      Handy
┌───────────────────────────────────────┐    ┌──────────────┐
│ ▬▬▬▬▬▬▬▬▬▬▬▬ Fortschritt   12/40  [⚙] │    │ ▬▬▬▬ 12/40 ⚙ │
├───────────────────────────────────────┤    ├──────────────┤
│                                       │    │              │
│       Arbeitsfläche (sichtbare        │    │ Arbeitsfläche│
│       Kante, beginnt direkt unter     │    │ (Vollhöhe)   │
│       der Leiste)                     │    │ [Antworten]  │
│       [ Antworten ]                   │    ├──────────────┤
└───────────────────────────────────────┘    │ (Bottom-Nav) │
                                             └──────────────┘
```
Keine vertikale Zentrierung im Viewport; mobil darf die Arbeitsfläche einen
Vollhöhen-Lock (100dvh) nutzen, wenn Eingabe/Timer das brauchen.

### D. Lektion (/lessons/&lt;id&gt;, /neu) — `.page--wide` + `.page-split`

```
Desktop                                      Handy
┌───────────────┬────────────────────┬──────┐ ┌──────────────┐
│ Seitenleiste  │ Titel              │      │ │ Titel        │
│ Seiten 1…n    │ Lesespalte 680 px  │      │ │ Seiten ▾     │
│ Fortschritt   │ Text, Karten-Deck  │      │ │ Lesetext     │
│ [Weiter]      │                    │      │ │ [Weiter]     │
└───────────────┴────────────────────┴──────┘ └──────────────┘
```
Fliesstext höchstens `--container-prose`; Medien dürfen breiter sein.

### E. Katalog (/lessons, /sprechen) — `.page--wide`

```
Desktop                                      Handy
┌───────────────────────────────────────┐    ┌──────────────┐
│ Seitenkopf                 [Suche]    │    │ Seitenkopf   │
│ Filterleiste: Chips · Sortierung      │    │ Filter ⇆     │
├─────────┬─────────┬─────────┬─────────┤    │ Kachel       │
│ Kachel  │ Kachel  │ Kachel  │ Kachel  │    │ Kachel       │
│ Kachel  │ Kachel  │ Kachel  │ Kachel  │    │ …            │
└─────────┴─────────┴─────────┴─────────┘    └──────────────┘
```
Raster über die volle Containerbreite; Filterleiste mobil als scrollbare Zeile.

### F. Auth (/login, /register) — `.page--auth`

```
Desktop                                      Handy
┌───────────────────────────────────────┐    ┌──────────────┐
│                                       │    │ Titel        │
│          ┌───────────────┐            │    │ Formular     │
│          │ Titel         │            │    │ [ Anmelden ] │
│          │ Formular      │            │    │ Link         │
│          │ [ Anmelden ]  │            │    │              │
│          └───────────────┘            │    └──────────────┘
└───────────────────────────────────────┘
```
Einzige Schablone mit Zentrierung; Karte 400–480 px. Mobil ohne Karte, volle
Breite mit Rinne.

## 5. Prüfliste (vor jedem Commit einer neuen/umgebauten Seite)

1. Hülle ist `.page` (+ Variante) statt eigener `max-width` im Seiten-Style.
2. Seitenkopf über `page_head` oben; Inhalt beginnt direkt darunter.
3. Keine vertikale Zentrierung ausser Auth, Leerzustand, Fehlerseite.
4. Breite Bildschirme (1920) füllen sich über Spalten/Raster, nicht über
   gestreckte Zeilen oder Leerraum; Fliesstext ≤ 80 Zeichen.
5. Abstände und Schriftgrössen nur aus den Tokens (`--space-*`, `--text-*`).
6. Karten nur für echte Einheiten, keine Karte in einer Karte; Flächen über
   `.surface*` (Dark Mode ohne eigene Hintergrund-Regeln).
7. Primäre Aktion im Fold: 1366×768 und 390×844 (abzüglich Bottom-Nav).
8. Mobil: eine Spalte, 16-px-Rinne, kein horizontaler Seiten-Überlauf,
   Touch-Ziele ≥ 44 px, Abstand zur Bottom-Nav.
9. Hell und dunkel geprüft; Kontrast Text ≥ 4.5:1.
10. Screenshots 1920×1080, 1366×768 und mobil (390, bei Formularen auch 360)
    in beiden Themes; bei CSS in custom.css zusätzlich Deck-Karussell.

## 6. Anti-Muster

- Einzelne Karte vertikal zentriert im Viewport („schwebender Dialog").
- Eigene `.container`-Breiten pro Seite (`max-width: 1800px !important` u. ä.).
- `min-height: 100dvh` + `justify-content: center` auf Desktop.
- Karte in Karte in Karte; Schatten + Rahmen + Hintergrund auf jeder Ebene.
- Pro Seite eigener `[data-theme=dark]`-Block, der nur Flächenfarben nachzieht.
- Freie Pixelwerte für Abstände/Schrift statt Tokens (heute über 60 verschiedene
  `font-size`-Werte in custom.css).
- Mobil: Seitenränder auf 0–8 px, Aktion erst nach mehreren Bildschirmhöhen.

## 7. Bestandsaufnahme 2026-09-27 (Arbeitsplan Schritt 2)

Gemessen lokal gegen die Prod-DB (read-only), eingeloggt als Admin (ausser
Login), Playwright, hell. Inhaltsbeginn = oberste sichtbare Inhaltszeile in px
ab Viewport-Oberkante (Nav endet bei 61). Auf `/`, `/lessons`, `/mein-lernen`
lag beim Messen der Willkommen-Dialog über der Seite.

### Desktop (1920×1080; in Klammern 1366×768)

| Seite | Inhaltsbreite | Beginn | zentriert | Leerraum oben/unten | Spalten | Karte in Karte | Bewertung | Schablone Schritt 2 |
|---|---|---|---|---|---|---|---|---|
| `/` (eingeloggt) | 1104 | 149 | nein | 88 / 0 | 3 | 0 | uneinheitlich: zentrierter Kopf, 1104 statt Containerbreite | B Dashboard |
| `/lessons` | 1104, Chip-Leiste läuft rechts hinaus | 152 | nein | 91 / 0 | 3 | 1 | uneinheitlich: Hero-Karte + Filter + Raster ohne Seitenkopf | E Katalog |
| `/lessons/171` | 1679 (volle 1800) | 126 | nein | 65 / 0 | 2 | 7 | uneinheitlich: Lesetext ~1300 px breit, 7 verschachtelte Karten | D Lektion |
| `/mein-lernen` | 1032 | 120 (98) | nein | 59 / 0 | 2 | 3 | ok, Breite eigen (1032) | B Dashboard (wide) |
| `/review` | 613 (Karte) | 94 | ja (1366) | 33 / 161 | 1 | 0 | schwebend: Karte mittig mit Leerraum ober- und unterhalb | C Spielansicht |
| `/review/stats` | 1120 | 139 | nein | 78 / 0 | 4 | 5 | ok, Breite eigen (1120) | B Dashboard (wide) |
| `/sprechen` | 1072 | 93 | nein | 32 / 0 | 3 | 0 | ok, eigene Schrift (Source Sans) und Breite | E Katalog |
| `/neu` | 728 | 118 | nein | 57 / 0 | 1 | 0 | ok, Lesespalte 728 statt 680 | D (nur Lesespalte, `.page--prose`) |
| `/n5-bundle` | 1104 (Band 1736) | 157 | nein | 96 / 569 | 1 | 0 | schwebend: kurze Besitzer-Karte, 569 px leer | E Katalog (Inhalt als Raster) |
| `/pruefen` | 728 | 109 | nein | 48 / 621 | 3 | 0 | schwebend: schmale Spalte, 621 px leer | A Übungs-Konfiguration |
| `/login` | 418 (Karte) | 175 (150) | nein | 114 / 455 | 1 | 0 | ok (Auth darf mittig) | F Auth |
| `/practice/kana` vorher | 1013 in 1100-Karte | 296 (142) | ja | 235 / 185 | 2 | 2 | schwebend | A (Pilot) |
| `/practice/kana` nachher | 1175 in 1200 | 102 (102) | nein | 41 / – | 2 | 0 | ok | A umgesetzt |

### Handy (390×844)

| Seite | Beginn | Aktion im Fold | Überlauf | Rinne | Befund |
|---|---|---|---|---|---|
| `/` | 109 | nein („Weiterlernen" bei 1265) | nein | 4 px | Rinne zu schmal, Aktion zu tief |
| `/lessons` | 277 (Hero-Bild zuerst) | ja (476) | Chip-Leiste scrollt | 24 px | Bild vor Titel verschiebt Beginn |
| `/lessons/171` | 82 | – | nein | 8 px | Rinne zu schmal, 6 verschachtelte Karten |
| `/mein-lernen` | 85 | ja | nein | 16 px | ok |
| `/review` | 74 | – (Karte = Aktion) | nein | 22/11 px | Rinne asymmetrisch |
| `/review/stats` | 107 | ja (312) | nein | 12 px | 50 verschachtelte Karten |
| `/sprechen` | 69 | knapp (778 von 784) | nein | 16 px | ok |
| `/neu` | 86 | – | nein | 16 px | ok |
| `/n5-bundle` | 109 | ja | nein | 24 px | 297 px leer unten |
| `/pruefen` | 85 | ja | nein | 16 px | ok |
| `/login` | 118 | ja (524) | nein | 37 px | ok (Karte) |
| `/practice/kana` vorher | 88 | ja (Vollhöhen-Lock) | nein | 16 px | Lock auch für Konfiguration |
| `/practice/kana` nachher | 86 | ja (651 auth / 566 Gast; auch 360/414) | nein | 16 px | Lock nur Storm/Schreiben |

Reihenfolge für Schritt 2 (Wirkung/Aufwand): `/pruefen` und `/n5-bundle`
(schwebend, klein) → `/review` (Spielansicht) → `/mein-lernen` + `/review/stats`
(Dashboard-Breite, Rinne, Karten-in-Karten) → `/lessons` + `/sprechen`
(Katalog) → `/` → `/lessons/<id>` (Lesespalte, grösster Umbau, Deck-Karussell
beachten).
