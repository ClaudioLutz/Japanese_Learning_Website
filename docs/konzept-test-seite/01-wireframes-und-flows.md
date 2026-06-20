# 01 · Flows & Wireframes

_Konzept Test-/Prüfungsseite · Stand 2026-06-20 · alle Wireframes aus einer Hand_

Notation: `(•)` gewählter Radio · `[ … ]` Button/Chip · `[✓]` aktiver Chip ·
`░▓` Fortschritt · `--shu` = Primär-CTA (Vermillion). Skizzen sind Layout-Absicht,
keine pixelgenauen Mockups. Token-Mapping pro Element in
[`02-inspiration-design-microcopy.md`](02-inspiration-design-microcopy.md) §2.

---

## 1. Der Flow in einem Bild

```
   ┌─────────────┐      ┌──────────────────────────┐      ┌──────────────┐
   │  /pruefen   │  ──▶ │   Frage-Screens          │ ──▶ │  Ergebnis-   │
   │ Start-Screen│      │   1 Frage = 1 Screen      │      │  Screen      │
   │ + Quick-Start│     │   (Client-Schritt, kein   │      │  Score-Ring  │
   │             │      │    Reload), X/Y, Tasten   │      │              │
   └─────────────┘      └──────────────────────────┘      └──────┬───────┘
        ▲   wie practice_kana.html    wie review.html            │
        └──────────────── „Nur Falsche nochmal" / „Neuer Test" ──┘
```

Drei Bildschirme, beide Übergänge spiegeln bestehende Muster:
`/practice/kana` (Start→Spiel→Ergebnis) und `/review` (Session-Loop X/Y + Summary).

> **🔒 Festgelegt (Variante „integrierte Frage-Seite", entschieden 2026-06-20):**
> Die Test-Session ist **eine Frage pro integriertem Vollbild-Screen** — Frage,
> Antwortoptionen und (im Übungsmodus) das Feedback/die Erklärung liegen alle auf
> *demselben* Screen, kein Sprung auf eine separate Auflösungs-Seite. Technisch ist
> jeder Frage-Screen ein **Client-Schritt innerhalb einer gesperrten Bühne**
> (`body.pruefung-locked`), **kein** echter Seiten-Reload und **keine** eigene Route
> pro Frage. Begründung: behält Timer, Fortschritt „X / Y", Tastatur-Steuerung und die
> bereits gegebenen Antworten; vermeidet Flash/verlorene Antworten bei Reload; ist
> exakt das Muster von `review.html` und `practice_kana_game.html`. Der große
> Konfigurations-Block wird dadurch zu einem **schlanken Start-Screen** (siehe §2):
> Quick-Starts + minimale Auswahl, Detail-Filter eingeklappt.
>
> **Verworfen:** eigene URL + Reload pro Frage (`/pruefen/frage/<id>`) — bricht
> Timer/Fortschritt/Antwort-State bei jedem Reload, fühlt sich stockend an.
> Banner-/Horizontal-Scroll-Layout ist damit ebenfalls vom Tisch: der Einstieg ist
> ein Start-Screen, nicht ein Banner oder Scroll-Streifen (ein Banner bleibt nur als
> optionaler *Zubringer* von Startseite/Lektionsende denkbar, §11).

---

## 2. Schlanker Start-Screen `/pruefen` (Desktop, Light)

Da die Session jetzt „eine Frage = ein Screen" ist (§1), ist der Einstieg **kein
großer Konfigurator**, sondern ein schlanker Start-Screen: **Quick-Starts oben**
(1-Tap, sofort in den ersten Frage-Screen) plus der **Modus-Toggle**. Die detaillierte
Auswahl („Gezielt prüfen": Scope-/Typ-/Schwierigkeits-Chips) ist **standardmäßig
eingeklappt** hinter `▸ aufklappen` — wer einfach loslegen will, tippt eine Kachel und
ist in der ersten Frage; wer feinjustieren will, klappt auf. So bleibt der Start-Screen
ruhig und der Detail-Filter trotzdem erreichbar.

```
┌──────────────────────────────────────────────────────────────┐
│  ✓  Prüfen                                         [ ☾ Dark ] │
│  Teste dein N5-Wissen erneut — verändert deinen                │
│  Wiederhol-Plan nicht.                                         │
│                                                                │
│  ┌─ SCHNELLSTART ───────────────────────────────────────────┐ │
│  │ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐       │ │
│  │ │ 🎯 Voll-N5-  │ │ 📘 Letzte    │ │ 🎲 Zufalls-  │       │ │
│  │ │   Probe-     │ │   Lektion    │ │   mix        │       │ │
│  │ │   prüfung    │ │   prüfen     │ │   20 Fragen  │       │ │
│  │ │ 312 verfügb. │ │ Lektion 14   │ │              │       │ │
│  │ └──────────────┘ └──────────────┘ └──────────────┘       │ │
│  │ ┌──────────────────────────────────────────────┐         │ │
│  │ │ 🔁 Nur falsch beantwortete · 12              │ ◀ Badge │ │
│  │ └──────────────────────────────────────────────┘         │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ── Gezielt prüfen ──────────────────────  [ ▸ aufklappen ]   │ ◀ eingeklappt
│  WAS?      [ Lektion ] [•Modul ] [ JLPT-Level ] [ Alles ]      │
│   ▲ erst nach Aufklappen sichtbar:                             │
│  Auswahl:  [✓ Familie] [ Restaurant ] [ Zahlen ] [ Zeit ] …   │  ◀ Chips wie Kana-Reihen
│  WELCHE?   [•Alle ] [ Nur falsche · 12 ] [ Nur neue ]         │
│  TYP:      [✓ Multiple Choice] [✓ Wahr/Falsch] [✓ Zuordnung]  │
│  SCHWERE:  [ 1 ][ 2 ][✓3 ][✓4 ][✓5 ]                          │
│                                                                │
│  MODUS:    [ ● Übung · Sofort-Feedback ] [ ○ Prüfung · Score ]│  ◀ färbt Screen um
│  ANZAHL:   [ 10 ] [•20 ] [ Alle · 47 ]    Zeitlimit [ aus ▾ ] │
│                                                                │
│            ╔══════════════════════════════════════╗            │
│            ║   ▶  Prüfung starten · 20 Fragen      ║   --shu    │
│            ╚══════════════════════════════════════╝            │
└──────────────────────────────────────────────────────────────┘
```

**Quick-Start-Verhalten** (history-unabhängige Kacheln sind bewusst die Mehrheit):

| Kachel | Inhalt | Modus | Empty-Verhalten |
|---|---|---|---|
| 🎯 Voll-N5-Mock | alle *zugänglichen* N5-Fragen | Prüfung | immer da (Rückgrat) |
| 📘 Letzte Lektion | Fragen der zuletzt besuchten Lektion | Übung | Fallback: erste zugängliche Lektion |
| 🎲 Zufallsmix | 20 zufällige zugängliche Fragen | Übung | immer da |
| 🔁 Nur falsche | `is_correct=F OR attempts>1` | Übung | bei 0 → **ausgegraut** + Untertitel (siehe §9) |

> **Wichtig:** Die 🔁-Kachel wird bei `0` **ausgegraut, nicht weggeblendet**
> (Discoverability bleibt) — mit dem Empty-Text als Untertitel.

---

## 3. Frage-Screen — Multiple Choice (Übungsmodus, vor Antwort)

**Ein** integrierter Vollbild-Screen pro Frage (Client-Schritt, siehe §1-Callout),
viewport-gesperrt (`body.pruefung-locked`, 1:1 wie `body.review-locked`), Chrome aus,
Fortschritt „X / Y" oben, Tastatur-Steuerung. „Weiter" tauscht den Frage-Inhalt
in-place gegen die nächste Frage — **kein Seiten-Reload**.

```
┌──────────────────────────────────────────────────────────────┐
│  ✕ Beenden        ▓▓▓▓▓▓░░░░░░░░░░░░  7 / 20                   │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│   Lektion 14 · Multiple Choice · Schwierigkeit ⭐⭐            │
│                                                                │
│        Wie liest man  水曜日 ?                                 │
│                                                                │
│   ┌────────────────────────────────────────────────────┐     │
│   │  1   すいようび                                      │     │
│   ├────────────────────────────────────────────────────┤     │
│   │  2   もくようび                                      │     │
│   ├────────────────────────────────────────────────────┤     │
│   │  3   きんようび                                      │     │
│   ├────────────────────────────────────────────────────┤     │
│   │  4   どようび                                        │     │
│   └────────────────────────────────────────────────────┘     │
│                                                                │
│   💡 Hinweis anzeigen          (nur Übung · question.hint)    │
│                                                                │
│                    [  Antwort prüfen  ]            --shu       │
│                                                                │
│   Tasten: 1–4 wählen · Enter prüfen · → weiter · H Hinweis    │
└──────────────────────────────────────────────────────────────┘
```

Gewählte Option (vor Submit): Rahmen tonal-indigo (`--kon-300`), **nicht** Vermillion
— Akzent bleibt der Aktion („Antwort prüfen") vorbehalten.

---

## 4. Sofort-Feedback — gleicher Screen wie §3 (Übung, nach „Antwort prüfen")

**Kein Screen-Wechsel:** das Feedback expandiert **in-place** unter den Optionen
desselben Frage-Screens — das ist der Kern der „integrierte Frage-Seite"-Idee (Frage +
Auflösung an einem Ort). Richtige Option grün (`--matcha`), gewählte falsche rot
(`--color-error`), darunter `question.explanation` + (falls vorhanden)
`QuizOption.feedback` der gewählten Antwort — der distraktorspezifische Lernmoment.

```
┌──────────────────────────────────────────────────────────────┐
│  ✕ Beenden        ▓▓▓▓▓▓░░░░░░░░░░░░  7 / 20                   │
├──────────────────────────────────────────────────────────────┤
│        Wie liest man  水曜日 ?                                 │
│                                                                │
│   ┌────────────────────────────────────────────────────┐     │
│   │  ✓ 2   もくようび          ← richtig    (matcha)    │     │
│   ├────────────────────────────────────────────────────┤     │
│   │  ✗ 1   すいようび          ← deine Wahl (rot)       │     │
│   └────────────────────────────────────────────────────┘     │
│                                                                │
│   ┌─ 💬 Erklärung ─────────────────────────────────────┐     │
│   │ 水 heisst „Wasser", aber 水曜日 = Mittwoch.         │     │
│   │ Lesung すい (on) + よう + び.                        │     │
│   │  (question.explanation + gewählte option.feedback)  │     │
│   └────────────────────────────────────────────────────┘     │
│                                                                │
│                       [  Weiter →  ]      (Enter / Leertaste)  │
└──────────────────────────────────────────────────────────────┘
```

---

## 5. Frage-Screen — Wahr/Falsch (`true_false`)

Zwei grosse Buttons, farb-neutral bis zur Wahl (kein Bias). Auf Mobile side-by-side,
daumenfreundlich.

```
┌──────────────────────────────────────────────────────────────┐
│  ✕ Beenden        ▓▓▓▓▓▓▓▓░░░░░░░░░  9 / 20                    │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│   Wahr oder Falsch?                                            │
│                                                                │
│   「ありがとう」bedeutet „Entschuldigung".                    │
│                                                                │
│   ┌──────────────────────┐    ┌──────────────────────┐       │
│   │         ✓            │    │         ✗            │       │
│   │      Richtig         │    │      Falsch          │       │
│   │     (Taste R)        │    │     (Taste F)        │       │
│   └──────────────────────┘    └──────────────────────┘       │
└──────────────────────────────────────────────────────────────┘
```

---

## 6. Frage-Screen — Zuordnung (`matching`)

**Empfehlung: Tap-to-pair als Primär-Interaktion** (funktioniert identisch auf
Mobile & Desktop), Drag nur als Desktop-Zusatz. Begründung: Drag ist auf Mobile heikel
(Scroll-Konflikt, kleine Ziele, bekannte Trägheit), Tap-to-pair ist robust und
barrierearm (Tab+Enter mappt sauber). Die korrekte Zuordnung steckt im
`QuizOption.feedback` — der Client baut daraus die Paar-Logik.

**Mechanik:** Tap links (wird aktiv markiert) → Tap rechts (Paar gebildet, beide
bekommen dasselbe Nummer-Badge ①②③) → erneuter Tap löst das Paar.

```
 DESKTOP (zwei Spalten):              MOBILE (gestapelt, gleiche Logik):
┌──────────────────────────────┐    ┌──────────────────────────────┐
│  ▓▓▓▓░░░░░  4 / 12            │    │  ▓▓▓░░░░  4 / 12              │
│  Ordne Kanji ↔ Lesung zu      │    │  Ordne Kanji ↔ Lesung         │
│                               │    │                               │
│  Kanji          Lesung        │    │  Kanji:                       │
│  ┌──────┐     ┌──────┐        │    │  [ ① 水 ] [ 火 •aktiv] [ ② 木]│
│  │① 水  │────▶│ みず①│        │    │                               │
│  ├──────┤     ├──────┤        │    │  Lesung:                      │
│  │ 火   │aktiv│ ひ    │        │    │  [ みず ① ] [ ひ ] [ き ② ]   │
│  ├──────┤     ├──────┤        │    │                               │
│  │② 木  │────▶│ き ②  │        │    │  Tippe oben, dann unten zum   │
│  └──────┘     └──────┘        │    │  Verbinden. Re-Tap = lösen.   │
│  Tippe links, dann rechts.    │    │                               │
│            [ Antwort prüfen ] │    │         [ Antwort prüfen ]    │
└──────────────────────────────┘    └──────────────────────────────┘
```

> **Teilpunkte:** 3 von 4 Paaren richtig = 0,75 Punkte (didaktische Leitplanke 5),
> nicht alles-oder-nichts.

---

## 7. Frage-Screen — Prüfungsmodus (kein Feedback, Soft-Timer)

Identisches Frage-Markup wie Übung, aber: **kein** „Hinweis", **kein** Zwischen-
Feedback, **kein** Zurück, Soft-Timer läuft mit. „Weiter" committet direkt.

```
┌──────────────────────────────────────────────────────────────┐
│  ✕ Beenden    ▓▓▓▓▓▓▓░░░░░░░░  11 / 40        ⏱ 18:42         │
├──────────────────────────────────────────────────────────────┤
│   N5-Probeprüfung · Multiple Choice                            │
│                                                                │
│        ___ を たべます。                                       │
│                                                                │
│   ┌──────────────┐ ┌──────────────┐                          │
│   │ 1  ごはん     │ │ 2  みず       │                          │
│   ├──────────────┤ ├──────────────┤                          │
│   │ 3  ほん       │ │ 4  くるま     │                          │
│   └──────────────┘ └──────────────┘                          │
│                                                                │
│   (keine Hinweise · keine Auflösung · kein Zurück)            │
│                          [  Weiter →  ]                        │
└──────────────────────────────────────────────────────────────┘
```

---

## 8. Ergebnis-Screen

Drei Zonen. **Score-Ring** (SVG-Donut) für das Endergebnis (ruhige, fokussierte
„Note"), **Balken** nur für den Verlauf *in* der Session — klare Rollentrennung.
Ring-Farbschwelle: ≥80 % `--matcha` · 60–79 % `--kincha` · <60 % `--color-error`.

### 8a. Übungsmodus (warm, kein Pass/Fail)

```
┌──────────────────────────────────────────────────────────────┐
│                    Gut gemacht — 17 von 20                     │
│                                                                │
│                       ╭───────────╮                            │
│                       │    85 %    │      Score-Ring (matcha)  │
│                       ╰───────────╯                            │
│                                                                │
│   ┌─ Überblick ────────────────────────────────────────┐     │
│   │  Richtig        17 / 20                              │     │
│   │  Erfolgsrate    85 %                                 │     │
│   │  Dauer          6 Min        +18 XP   🔥 Streak 4    │     │
│   └────────────────────────────────────────────────────┘     │
│                                                                │
│   ┌─ Zum Nachlesen (3 Fehler) ─ aufklappbar ──────────┐      │
│   │ ▸ 水曜日 lesen — du: もくようび · richtig: すいようび │      │
│   │     💬 水曜日 = Mittwoch …            (explanation)  │      │
│   │ ▸ … は ___ です — du: たかい · richtig: あたらしい   │      │
│   └────────────────────────────────────────────────────┘     │
│                                                                │
│   ╔═══════════════════════════╗  ┌──────────────────────┐    │
│   ║ 🔁 Nur die 3 Falschen     ║  │ ↻ Gleichen Test       │    │
│   ║    nochmal       --shu    ║  │   wiederholen Outline │    │
│   ╚═══════════════════════════╝  └──────────────────────┘    │
│   [ Zur Lektion 14 → ]   [ Neuen Test konfigurieren ]        │
└──────────────────────────────────────────────────────────────┘
```

### 8b. Prüfungsmodus / Mock (Pass-Schwelle + Sektionen)

```
┌──────────────────────────────────────────────────────────────┐
│                  N5-Probeprüfung — Ergebnis                    │
│                                                                │
│                       ╭───────────╮                            │
│                       │    72 %    │   Ring (kincha, 60–79 %)  │
│                       ╰───────────╯                            │
│              ✓ Bestanden  (Schwelle 60 %)                      │
│   „Bestanden ab 60 % — der echte JLPT N5 braucht ~44 %;        │
│    wir setzen die Latte bewusst höher."                        │
│                                                                │
│   Moji-Goi (Wortschatz)  ▓▓▓▓▓▓▓▓░░  81 %                      │
│   Bunpō (Grammatik)      ▓▓▓▓▓▓░░░░  64 %                      │
│   Dokkai (Lesen)         ▓▓▓▓▓░░░░░  58 %  ◀ deine Baustelle   │
│                                                                │
│   „Solide N5-Basis. Grammatik und Lesen brauchen noch ein      │
│    paar Runden — leg dort den Fokus hin."                      │
│                                                                │
│   [ 11 falsche Fragen ansehen ]   [ 🔁 Schwächste üben → ]    │
└──────────────────────────────────────────────────────────────┘
```

**CTA-Priorität:** ① `--shu` „Nur die N Falschen nochmal" (die Kern-Schleife,
clientseitiges Fehler-Array wie Kana `playWeakOnly`) · ② Outline „Gleichen Test
wiederholen" · ③ Links „Zur Lektion X" / „Neuen Test konfigurieren".

---

## 9. Empty-State — Falsch-Filter ohne Historie (der wichtigste!)

Bei ≈0 externen Nutzern ist das für fast alle Konten Realität. **Niemals leerer
Bildschirm** — immer auf ein Rückgrat-Modul umleiten.

```
┌──────────────────────────────────────────────────────────────┐
│                  🎯  Noch keine falschen Antworten             │
│                                                                │
│   Du hast bisher keine Quizfrage falsch beantwortet — oder     │
│   schon alles korrigiert. Stark. Sobald du Lektions-Quizze     │
│   machst, sammeln sich hier deine Stolpersteine.               │
│                                                                │
│   Trotzdem testen:                                             │
│   [ 🎯 Voll-N5-Probeprüfung ]   [ 🎲 Zufallsmix 20 ]          │
│   [ 📘 Eine Lektion wählen ]                                   │
└──────────────────────────────────────────────────────────────┘
```

Variante (Filter „Nur falsche" für eine Lektion = 0): inline-Hinweis im Konfig-Block,
Filter springt zurück auf „Alle" → *„In dieser Lektion noch keine falschen Antworten —
zeige alle 12 Fragen."*

---

## 10. Gast-State (nicht eingeloggt)

Test-Ergebnisse speichern braucht Login (wie `/review`). Aber: Gast steht nie vor
verschlossener Tür — optional 3 spielbare Demo-Fragen, CTA `register(next=/pruefen)`
(Funnel-Bug behoben → Auto-Login + Rücksprung).

```
┌──────────────────────────────────────────────────────────────┐
│                  Teste dein N5-Wissen                          │
│   Quizfragen aus den Lektionen — Sofort-Feedback & Score.      │
│                                                                │
│   [ Kostenlos anmelden & loslegen ]   --shu                    │
│   Schon dabei?  [ Einloggen ]                                  │
│                                                                │
│   ┌─ Zum Reinschnuppern (3 Demo-Fragen, ohne Speichern) ─┐    │
│   │  [ Demo starten → ]                                   │    │
│   └───────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

---

## 11. Locked / Zugriffskontrolle im Mock (Bundle als Feature)

Nicht zugängliche Lektionen werden **stillschweigend ausgefiltert** (keine gesperrten
Geister-Fragen), der Zähler passt sich an. Wird der Pool dadurch klein: dezenter
Hinweis + Bundle-Upsell (`--kincha`-Gold), **kein Blocker**.

```
┌──────────────────────────────────────────────────────────────┐
│  🎯 Probeprüfung: 312 von ~790 Fragen verfügbar.              │
│  Die übrigen stecken in Lektionen, die du noch nicht hast.    │
│                                                                │
│  [ Mock mit 312 starten ]   --shu    ·   [ N5 Bundle → ] gold │
└──────────────────────────────────────────────────────────────┘
```

---

## 12. Tastatur-Steuerung (spiegelt `/review` Tasten 1–4)

| Taste | Aktion |
|---|---|
| `1`–`4` / `A`–`D` | Multiple-Choice-Option wählen |
| `R` / `F` (oder `←`/`→`) | Wahr / Falsch |
| `Enter` / `Leertaste` | „Antwort prüfen" → dann „Weiter" |
| `H` | Hinweis (nur Übung) |
| `Esc` | Beenden (mit Bestätigung, Fortschritt geht verloren) |

---

## 13. Dark-Mode-Hinweise (kein eigener Redraw nötig)

Alle Flächen tokenbasiert → erbt automatisch den Dark-Satz (`data-theme="dark"`).
Drei Fallen aus früheren Dark-Fixes beachten:

- **`--shu` bleibt** #EB6101 → Primär-CTA & Verlaufsbalken sehen identisch aus. CTA-
  Text über die **bestehende** tonale Akzent-Button-Regel (`color: var(--washi)`)
  laufen lassen, nicht neu erfinden.
- **`--kon` kippt im Dark auf HELL** → wird Heading-/Aktiv-Farbe, **nicht** mehr als
  dunkler Füll-Hintergrund nutzbar. „Gewählte Option" im Dark = `--kon-50` (dunkle
  Indigo-Tönung) als BG.
- Erfolg/Fehler über `--matcha-*` / `--color-error` (haben Dark-Varianten; Projekt
  nutzt `--color-error`, **nicht** `--danger`).

→ Vollständiges Token-Mapping pro Element:
[`02-inspiration-design-microcopy.md`](02-inspiration-design-microcopy.md) §2.
