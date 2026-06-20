# 02 · Inspiration, Design-System & Microcopy

_Konzept Test-/Prüfungsseite · Stand 2026-06-20_

## 1. Wettbewerbs-Inspiration — was wir uns abschauen

Aus etablierten Lern-/Test-Tools, gefiltert auf unseren ruhigen Ink-on-Washi-Ton
(kein Gamification-Casino). Pro Tool: was es gut macht, was übernehmbar ist, was zu
vermeiden ist.

### Anki — Custom Study & Filtered Decks
- **Gut:** „Custom Study" als Menü vordefinierter Sonder-Sessions (forgotten cards,
  by state/tag). „Filtered Decks" = temporäre, ephemere Übungssammlung, die nach der
  Session auflöst und den echten Lernstand **nicht** verändert.
- **Übernehmen:** das Custom-Study-Menü als Layout-Vorbild der Konfig-Seite (ruhige
  Modus-Auswahl). **Ephemere Session** — die Test-Seite verändert SRS/Fortschritt
  nicht (Üben ≠ Lernstand ändern).
- **Vermeiden:** Ankis Optionsdichte & Suchsyntax. Wir brauchen 4–5 Modi, keine
  Query-Sprache.

### Quizlet — Test-Modus & Learn-Modus
- **Gut:** Vor dem Test eine kleine Konfig (Anzahl, welche Fragetypen an/aus), am Ende
  **Score + vollständige Korrektur-Liste** (jede Frage mit richtig/falsch + Lösung).
  „Diese nochmal lernen" für die Falschen.
- **Übernehmen:** **Fragetyp-Filter als Chips** (unser `question_type` hat exakt 3
  Werte). **Ergebnis-Screen mit Korrektur-Liste**, die `question.explanation` +
  `QuizOption.feedback` zeigt — macht den Test direkt zum Lernmoment.
- **Vermeiden:** Quizlets „Schreiben"-Modus (= `fill_blank`, bei uns verboten);
  überladene Resultat-Seite mit Upsell-Bannern.

### Bunpro — Cram & Ghost Reviews
- **Gut:** „Cram" = explizit Üben **ohne** SRS-Konsequenz. „Ghost Reviews" = einmal
  falsche Items kommen als „Geist" zurück, ohne den SRS-Status zu ruinieren.
- **Übernehmen:** die **Cram-vs-Review-Trennung als Kern-Narrativ** — „Prüfen"
  (diese Seite) ist explizit das *Testen ohne SRS-Folgen*-Gegenstück zu „Wiederholen".
  **Ghost-Idee leichtgewichtig:** in EINER Session falsch beantwortete Fragen ans
  Session-Ende re-einreihen, bis korrekt (rein in-memory).
- **Vermeiden:** Bunpros Begriffs-Overload (SRS/Ghost/Cram/Self-Study). Wir labeln
  genau **zwei** Dinge: „Wiederholen" (SRS) vs. „Prüfen" (neu).

### WaniKani — Mastery-Stufen
- **Gut:** ruhige Beherrschungs-Erzählung, ein Balken pro Stufe.
- **Übernehmen:** ein **sanfter Mastery-Indikator pro Lektion/Modul** auf der Konfig-
  Seite, rein aus vorhandenen Daten („Lektion 12 — 8/10 sitzen", Aggregat über
  `UserQuizAnswer.is_correct`). Gibt der Modus-Auswahl Orientierung.
- **Vermeiden:** WaniKanis Gating (alles in Reihenfolge gesperrt) und „Burned"-
  Endgültigkeit — unsere Seite ist frei explorierbar (im Rahmen der Zugriffskontrolle).

### Duolingo — Practice/Mistakes-Hub
- **Gut:** „Mistakes/Personalized Practice" als prominenter Einstieg, der gezielt
  bekannte Fehler sammelt — aber **nie die einzige Option**. Sanfte Empty-States
  (Alternativübung statt leerer Seite). „Test-out" überspringt Bekanntes.
- **Übernehmen:** der **Mistakes-Hub als EIN Quick-Start-Knopf**, nicht als ganze
  Seite (exakt unsere Briefing-Vorgabe). **Duos Empty-State-Handling** direkt klauen —
  überlebenswichtig bei ≈0 Historie. **Test-out-Framing** für den Voll-N5-Mock.
- **Vermeiden:** Herzen/Streak-Strafen/Push-Aggression/XP-Inflation — gegen unseren Ton.

### Kahoot / Quizizz — Game-Show
- **Gut:** sehr niedrige Einstiegshürde („in 2 Sekunden verstehen, was zu tun ist").
- **Warum hier meist NICHT:** Leaderboard/Podium/Buzzer/Punkte-für-Tempo widersprechen
  Ink-on-Washi frontal (User hat Leaderboards bei Kana Storm bereits abgewählt).
  Geschwindigkeits-Scoring **bestraft sorgfältiges Lesen** japanischer Sätze —
  didaktisch schädlich.
- **Übernehmen (nur das):** die niedrige Einstiegshürde (ein dominanter `--shu`-CTA);
  optionaler, dezenter Timer **nur im Mock**, nie pro Frage mit Punktdruck.

### Offizielle JLPT-Mock-Prüfungen
- **Gut:** Sektions-Struktur, feste Zeitfenster, **Pass-Schwelle**, ein
  zusammenhängender Block ohne Zwischenfeedback (Prüfungsrealismus), klares
  Bestanden/Nicht-bestanden.
- **Übernehmen:** der **Voll-N5-Mock** mit echter Prüfungs-Dramaturgie (zusammenhängend,
  Feedback erst am Ende, Punktzahl + Pass-Schwelle 60 %, optionaler Gesamt-Timer).
  **Zugriffskontrolle** ist hier die markierte Sicherheitsgrenze.
- **Vermeiden:** echte Prüfungs-Härte als *Default* — das ist EIN Modus, nicht der
  Standardton.

### „Das übernehmen wir" — priorisiert

| # | Empfehlung | Quelle | Code-Anker | Prio |
|---|---|---|---|---|
| 1 | Konfig-Seite als ruhiges Modus-Menü | Anki Custom Study | spiegelt `practice_kana.html` | P0 |
| 2 | History-unabhängige Modi als Rückgrat, Falsch-Filter = ein Modus | Duolingo Mistakes | `is_correct=F OR attempts>1` | P0 |
| 3 | Session-Loop wie `/review` (X/Y, `body.*-locked`) | review.html | review.html spiegeln | P0 |
| 4 | Ergebnis-Screen mit Korrektur-Liste (`explanation`+`feedback`) | Quizlet | `QuizQuestion.explanation`, `QuizOption.feedback` | P0 |
| 5 | Fragetyp-Filter als Chips | Quizlet | `question_type` (3 Werte) | P1 |
| 6 | „Falsche nochmal"-Button am Ende (clientseitig) | Quizlet / Kana | In-memory, kein Schema | P1 |
| 7 | Üben ≠ SRS klar labeln | Bunpro Cram | Abgrenzung zu `/review` | P1 |
| 8 | Voll-N5-Mock mit Pass-Schwelle + Timer | JLPT + Duolingo | `points`, Zugriffs-Gate | P1 |
| 9 | In-Session-„Ghost" (Falsche ans Ende) | Bunpro Ghost | In-memory | P2 |
| 10 | Sanfter Mastery-Indikator pro Lektion | WaniKani | Aggregat `is_correct` | P2 |
| 11 | Quick-Starts oben | Duolingo + Kana | UI-Muster | P1 |
| 12 | Niedrige Einstiegshürde, kein Casino | Kahoot (gefiltert) | Tokens, Anti-Pattern-Grenze | P0 |

### Drei Leitplanken aus der Analyse
1. **Zwei Wörter, keine vier.** Genau „Wiederholen" (SRS) vs. „Prüfen" (neu). Kein
   Cram/Ghost/Custom/Filtered-Vokabular einführen.
2. **Falsch-Filter ist Topping, nicht Fundament.** Funktioniert nur, wenn er nie die
   einzige Option ist — bei unserer Datenlage Pflicht.
3. **Kahoot-Energie filtern, JLPT-Ernst dosieren.** Vom Game-Pol nur die niedrige
   Einstiegshürde, vom Prüfungs-Pol nur den Mock-Modus. Default-Ton liegt ruhig
   dazwischen.

---

## 2. Design-System — Token-Mapping (Ink-on-Washi)

Alle Werte sind bestehende Tokens aus `app/static/css/custom.css`. **Keine Hex-
Literale in neuem Markup** — nur `var(--…)`, dann erbt Dark Mode automatisch.

### Konfig-/Startseite (Light)

| Element | Token |
|---|---|
| Seiten-Hintergrund | `--washi` |
| Quick-Start-/Modus-Karten (BG) | `--kinari` (wärmer als Washi) |
| Karten-Rahmen | `1px solid var(--ink-200)` (Haarlinie) |
| Karten-Schatten / Radius | `var(--shadow-card)` / `var(--radius-lg)` |
| Kachel-Überschrift | `var(--kon)` |
| Body-/Beschreibungstext | `var(--ink-700)` / `var(--text-color)` |
| Gedämpfter Hinweis („12 Fragen · ~6 Min") | `var(--ink-600)` / `var(--text-muted)` |
| **Primär-CTA „Prüfung starten"** | BG `var(--shu)`, Text `var(--washi)`, Hover `var(--shu-deep)` |
| Sekundär-CTA (Outline) | `border:1px solid var(--ink-200)`, Text `var(--ink-700)`, BG transparent |
| Chip inaktiv | BG `var(--kinari)`, Rahmen `var(--ink-200)`, Text `var(--ink-700)` |
| Chip **aktiv** | BG `var(--kon-50)`, Rahmen `var(--kon-300)`, Text `var(--kon)` (tonal, **nicht** Vermillion) |
| Mock-Kachel / Premium-Touch | Akzentleiste `var(--kincha)` |
| Gesperrt-Marker (Modul) | Schloss + `var(--kincha)` — **nie** `--shu` für „gesperrt" |

### Session-Bühne (`body.pruefung-locked`, analog `body.review-locked`)

| Element | Token |
|---|---|
| Viewport-Sperre | `overflow:hidden`, Footer aus, `height:calc(100vh-60px)` — das `review-locked`-Muster |
| Fortschritts-Track | `.progress` BG `var(--ink-100)`, Rahmen `var(--ink-200)` |
| Fortschritts-Füllung | `.progress-bar` BG `var(--shu)` (Vorwärts-Signal) |
| Zähler „7 / 12" | `var(--ink-600)` |
| Fragen-Karte | BG `var(--kinari)`, Rahmen `var(--ink-200)`, `var(--shadow-card)`, `--radius-lg` |
| Frage-Text | `var(--kon)`, grösser/halbfett |
| Option inaktiv | BG `var(--washi)`, Rahmen `var(--ink-200)`, Text `var(--ink-700)` |
| Option **gewählt** (vor Submit) | Rahmen `var(--kon-300)`, BG `var(--kon-50)` |
| Option **richtig** | Rahmen `var(--matcha-line)`, BG `var(--matcha-bg)`, ✓ `var(--matcha)` |
| Option **falsch** | `var(--color-error)` (Projekt nutzt **`--color-error`**, nicht `--danger`) |
| Erklärungs-Panel | BG `var(--kon-50)`, Text `var(--ink-700)`, linke Akzentkante `var(--kon-300)` |
| Hinweis-Button | Text/Outline `var(--ink-600)`, Glyph 💡 |

### Dark Mode (`data-theme="dark"`)
- **`--shu` bleibt** → CTA & Balken identisch. CTA-Text über die **bestehende** tonale
  Akzent-Button-Regel (`color: var(--washi)`) — nicht neu erfinden.
- **`--kon` kippt auf HELL** → Heading/Aktiv-Farbe, nicht als dunkler Füll-BG nutzbar;
  „gewählte Option" im Dark = `--kon-50` (dunkle Indigo-Tönung).
- Erfolg/Fehler über `--matcha-*` / `--color-error` (haben Dark-Varianten).
- Body-Text im Dark ist bereits `--ink-700 #C7BEAF` (aufgehellt) → nichts extra.

### Score-Ring (Ergebnis)
- **Ring** (SVG-Donut) fürs Endergebnis, **Balken** nur für Verlauf in der Session.
- Ring-Farbschwelle: ≥80 % `--matcha` · 60–79 % `--kincha` · <60 % `--color-error`;
  Track immer `--ink-200`; Prozentzahl `var(--kon)`, Label `var(--ink-600)`.

---

## 3. Wiederverwendbare Komponenten

| Aus Vorlage | Für „Prüfen" |
|---|---|
| `review.html` → `body.review-locked` | 1:1 als `body.pruefung-locked` |
| `review.html` → `.session-progress`/`.progress`/`.progress-bar` | identischer Fortschrittsbalken („X / Y", `aria-valuenow`) |
| `review.html` → `.session-summary`/`.summary-row/-label/-value` | Ergebnis-Tabelle (Richtig/Falsch/Erfolgsrate/Dauer) |
| `review.html` → JS-Session-Loop | Architektur spiegeln: `cards[]`→`questions[]`, `currentIndex`, `sessionStats`; Tasten 1–4 wählen Option statt Rating |
| `practice_kana.html` → Konfig-Chips + Modus-Segment | „WAS/WELCHE/MODUS"-Segmente + Scope-Chips; optional gemeinsamer Alpine-`$store` wie `$store.kanaScope` |
| `practice_kana.html` → Quick-Starts | „Schnellstart"-Reihe (Mock / Letzte Lektion / Falsche / Zufall) |
| `practice_kana.html` → „nur Schwächste üben" (`playWeakOnly`) | „nur falsch beantwortete" (clientseitiger Filter) |
| `stats.html` → fetch-Charts (Chart.js geladen) | optionaler Mini-Donut „Erfolgsrate pro Modul" im Ergebnis |
| site-weite Toasts | statt `alert()` für „Prüfung abgeschlossen" |
| Gast-Conversion-Block (Kana/Lessons) | Gast-State `register(next=/pruefen)` |

---

## 4. Microcopy-Katalog (deutsch, ruhig, ermutigend, Du-Form)

| Kontext | String |
|---|---|
| Seiten-Subline | „Teste dein N5-Wissen erneut — verändert deinen Wiederhol-Plan nicht." |
| Primär-CTA Start | „Prüfung starten" (+ Live-Zähler: „· 20 Fragen") |
| Mock-Kachel | „Voll-N5-Probeprüfung — alle freigeschalteten Fragen" |
| Falsch-Filter | „Nur falsch beantwortete üben" |
| Button bestätigen | „Antwort prüfen" |
| Button weiter | „Weiter" |
| Ergebnis ≥ 80 % | „Bestanden — du bist N5-reif." |
| Ergebnis 60–79 % | „Knapp dran — fast geschafft." |
| Ergebnis < 60 % | „Noch etwas Übung — du kommst hin." |
| Pass-Erklärung (Mock) | „Bestanden ab 60 % — der echte JLPT N5 braucht ~44 %; wir setzen die Latte bewusst höher." |
| Empty Falsch-Filter | „Noch keine falschen Antworten — und das ist gut. Starte eine Prüfung nach Lektion oder Modul, dann sammelt sich hier, was du nochmal anschauen solltest." |
| Empty-CTA | „Erste Prüfung starten" |
| Gast-Hinweis | „Melde dich an, um deine Ergebnisse zu speichern und gezielt deine Schwächen zu üben." |
| Zugriffs-Hinweis Mock | „Diese Prüfung umfasst nur deine freigeschalteten Lektionen." |

**Ton-Leitplanken:** Du-Form (wie `/review`/`/practice`), keine Ausrufezeichen-
Inflation, kein „Super!!!". Ermutigung auch bei < 60 % („du kommst hin"), nie wertend.
„N5-reif" als wiederkehrendes Erfolgs-Vokabular (knüpft an `/review/stats` N5-Mastery
an). **Nie** „Du hast versagt" / nackte Fail-Zahl ohne Handlungsweg — jeder Ergebnis-
Screen endet mit *einer* konkreten nächsten Aktion.
