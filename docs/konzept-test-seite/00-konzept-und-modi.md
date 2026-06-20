# 00 · Konzept, Datenrealität & Modus-Katalog

_Konzept Test-/Prüfungsseite · Stand 2026-06-20_

## 1. Vision in zwei Sätzen

Eine eigene Seite, auf der Nutzer ihr N5-Wissen **aktiv abrufen** — sie testen die
Quiz-Fragen aus den Lektionen erneut, gezielt nach Lektion / Modul / Level oder als
ganze N5-Probeprüfung, und können dabei **gezielt ihre Fehler nachholen**. Die Seite
ergänzt das bestehende `/review` (SRS-Karten zur Pflege) um das fehlende Gegenstück:
**Selbsttest der Quizfragen** — mit oder ohne Hilfe.

Abgrenzung, die das ganze Konzept trägt:

| | `/review` (existiert) | **Neue Seite** |
|---|---|---|
| Objekt | SRS-Lernkarten (Kana/Kanji/Vokabel/Grammatik) | **Quiz-Fragen** (`QuizQuestion`) |
| Zweck | Langzeit-Gedächtnis pflegen (FSRS, fällige Karten) | Wissen prüfen / Fehler nachholen |
| Verändert Lernstand? | Ja (FSRS-Intervalle, Streak, XP) | **Nein** — Test ist „risikofrei", berührt SRS nicht |
| Nav-Label | „Wiederholen" 🧠 | „Prüfen" ✓ (Vorschlag) |

## 2. Die Datenrealität — und warum „1× falsch beantwortet" heute schon geht

Das Herzstück des User-Wunsches berührt eine bewusste Schema-Entscheidung. Klartext:

### Was im Code steht (verifiziert)

`UserQuizAnswer` (`app/models.py:1310-1321`) ist ein **Upsert**: genau **eine Zeile pro
(User, Frage)** — `UNIQUE(user_id, question_id)` (`:1321`). Es gibt **keine** Append-only-
Historie und **keinen** `times_wrong`-Zähler. Nutzbare Verlaufs-Signale:

| Feld | Bedeutung | Grenze |
|---|---|---|
| `is_correct` (Bool, `:1317`) | Letzter bekannter Zustand der Frage | sagt nichts über frühere Versuche |
| `attempts` (Int, `:1319`) | Wie oft total versucht | `> 1` ⇒ mind. 1× daneben, aber „wie oft" unbekannt |
| `answered_at` (DateTime, `:1318`) | Zeitpunkt der **letzten** Berührung | überschreibt sich (`onupdate`), keine Episoden |

### Die Schlüssel-Erkenntnis

> Die Lektions-UI erlaubt nach einer falschen Antwort weiteres Absenden, bis korrekt
> **oder** Versuche aufgebraucht (`lesson_view.html:1369`; `LessonContent.max_attempts`
> Default = **3**, `models.py:1166`). Darum kommt `attempts > 1` real vor.

Damit ist **„jemals falsch beantwortet" heute ohne jede Migration abfragbar**:

```sql
-- "Fragen, die schon mal daneben gingen" (Proxy, baubar HEUTE)
WHERE a.is_correct = false      -- aktuell offen / zuletzt falsch
   OR a.attempts  > 1           -- mehrfach versucht ⇒ mindestens 1× falsch
```

Für den Nutzer transparent in **zwei Unterfilter** aufteilen (statt vermischt):
- 🔴 **Aktuell offen** = `is_correct = False`
- 🟡 **War mal schwer** = `is_correct = True AND attempts > 1` (saß erst nach Mühe)

### Was der Proxy NICHT kann (und wann man es nachzieht)

Nicht abbildbar ohne Schema-Upgrade: *exakte* Fehlerzahl, „genau 1× vs. ≥2× falsch",
„falsch-dann-richtig über Zeit", echtes Spacing/Leitner. Das ist ein **optionales
Präzisions-Upgrade, keine Voraussetzung** — siehe Roadmap §8. Für v1 reicht der Proxy.

### Konsequenz fürs Produkt: Falsch-Filter ist Kür, nicht Fundament

Memory + Projektrealität: **≈0 externe Nutzer**, fast nur eigene Testkonten → für die
meisten Konten gibt es **wenig bis keine Antwort-Historie**. Eine Seite, die *nur* um
„deine Fehler" gebaut ist, wäre für fast alle leer.

> **Leitsatz:** Das **Rückgrat** sind history-*un*abhängige Modi (Lektion / Modul /
> JLPT-Level / Voll-Mock / Zufall). Der Falsch-Filter ist **ein** Modus mit einem
> aggressiv freundlichen Empty-State, der immer auf ein Rückgrat-Modul zurückleitet.
> **Kein Modus zeigt je einen leeren Bildschirm.**

## 3. Informationsarchitektur

### Route & Nav

Empfehlung: **`/pruefen`**, Nav-Label **„Prüfen"** (deutsches Verb, konsistent mit
„Lernpfad / Wiederholen / Kana üben"; `/test` ist englisch, `/quiz` klingt verspielt —
die Seite soll seriös-prüfend wirken). Alternativen offen (siehe §9).

Nav-Reihenfolge nach Lern-Eskalation **lernen → festigen → prüfen**, neuer Eintrag
direkt neben „Wiederholen" (beide = aktives Abrufen), in `app/templates/base.html`
(Nav ~`:149-280`):

```
Lernpfad | Lektionen | Wiederholen 🧠[•57] | Prüfen ✓ | Kana üben あ | [N5 Bundle]
```

Kein „fällig"-Badge an „Prüfen" (es gibt keine fälligen Prüfungen) — höchstens ein
dezenter Zähler, wenn der Falsch-Filter Treffer hat.

### Seiten-Flow (spiegelt `/practice/kana` + `/review`)

```
/pruefen (schlanker Start-Screen)  →  Frage-Screens             →  Ergebnis-Screen
   Quick-Starts + Modus,               1 Frage = 1 integrierter     wie review-Summary
   Detail-Filter eingeklappt           Vollbild-Screen (Client-
   wie practice_kana.html              Schritt, kein Reload), X/Y
                                       wie review.html
```

> **Festgelegt:** Die Session ist **eine Frage pro integriertem Vollbild-Screen** —
> Frage + Antwort + (in Übung) Feedback an einem Ort, als Client-Schritt ohne
> Seiten-Reload und ohne eigene Route pro Frage. Details + Wireframe-Callout in
> [`01-wireframes-und-flows.md`](01-wireframes-und-flows.md) §1.

Details + Wireframes in [`01-wireframes-und-flows.md`](01-wireframes-und-flows.md).

## 4. Die zwei Modi (der wichtigste Schalter)

Die Seite ist **zwei Produkte**: formativ (lernen *während* des Tests) und summativ
(„bin ich N5-reif?"). Sie dürfen nicht vermischt werden. Ein Segment-Toggle ganz oben
färbt den ganzen Screen um.

| Dimension | **Übung** (Default) | **Prüfung** (Mock) |
|---|---|---|
| Feedback | **sofort** nach jeder Frage | **erst am Ende**, gesammelt |
| Hilfen | `hint` abrufbar, `explanation` nach Antwort | gesperrt |
| Korrigieren | erlaubt (wie Lektion), Zurück erlaubt | eine Antwort, kein Zurück |
| Zeit | offen, kein Druck | **Soft-Timer** sichtbar (Realismus) |
| Reihenfolge | thematisch geblockt ok | **interleaved** (gemischt, Pflicht) |
| Score | informativ, kein Druck | **zentral**: Pass/Fail + Sektionswerte |
| `points`-Gewichtung | egal | ja (schwere Frage zählt mehr) |

Didaktische Begründung: Sofort-Feedback maximiert den Lerngewinn (Korrektur greift im
Arbeitsgedächtnis), zerstört aber die Prüfungs-Aussage — ein Mock mit Hints misst „mit
Hilfe". Der echte JLPT kennt keine Hints, kein Zurück, kein Zwischenfeedback; das muss
einmal erlebbar sein, sonst ist die erste echte Prüfung ein Realitätsschock.

## 5. Modus- & Filter-Katalog

Zwei orthogonale Achsen + Overlays. **A) Quelle/Scope** (welche Fragenmenge) ·
**B) Auswahl-Filter** (welche Teilmenge) · **C) Modus-Overlays** (wie). Die Quick-Start-
Kacheln sind nur Presets, die in dieselben Achsen auflösen — **eine Engine**.

Legende „Heute": ✅ baubar ohne Schema-Änderung · ⚠️ Proxy heute / exakt erst mit
Upgrade · 🔧 neues Feld/Tabelle nötig.

### Gruppe A — Rückgrat (history-unabhängig, immer befüllbar)

| # | Modus | Signal | Heute | Rolle |
|---|---|---|---|---|
| A1 | **Nach Lektion** | `lesson_content_id → lesson_id` | ✅ | Rückgrat |
| A2 | **Nach Modul/Thema** | `→ Lesson.category_id` | ✅ | Rückgrat (Chips wie Kana-Reihen) |
| A3 | **JLPT-Level / Voll-N5-Mock** | `LessonCategory.jlpt_level` (Int, N5 = `5`; `models.py:783`) via `Lesson.category` + Zugriff | ✅ | **Flaggschiff** |
| A4 | **Nach Fragetyp** | `question_type` ∈ {mc, true_false, matching} | ✅ | Facette |
| A5 | **Nach Schwierigkeit** | `difficulty_level` 1–5 | ✅\* | Facette (\*Datenqualität prüfen) |
| A6 | **Gemischt / Zufall** | `ORDER BY random()` + Zugriff | ✅ | Rückgrat (Default-Schnellstart) |

\* `difficulty_level` Default = 1 (`models.py:1286`). Vor UI-Aufnahme einmal
`GROUP BY difficulty_level` zählen — wenn fast alles `1` ist, ist der Filter wertlos.

### Gruppe B — History-Modi (Veredelung, Empty-State Pflicht)

| # | Modus | Signal | Heute | Rolle |
|---|---|---|---|---|
| B1 | **Nur falsch beantwortet** | `is_correct=False OR attempts>1` | ⚠️ Proxy | **Headline-Wunsch** |
| B2 | **Noch nie beantwortet** | `NOT EXISTS answer` + Zugriff | ✅/⚠️ | Lücken (Zugriffsfalle!) |
| B3 | **Leech / Dauer-Fehler** | `attempts >= 3 (+ is_correct=False)` | ⚠️ Proxy | „die Hartnäckigen" |

> **B2-Warnung (Premium-Leak):** „noch nie beantwortet" enthält fast die ganze
> nicht-gekaufte N5-Welt. **Nur** innerhalb zugänglicher Lektionen anbieten.

### Gruppe C — Modus-Overlays (orthogonal, mit A/B kombinierbar)

| # | Overlay | Signal | Heute |
|---|---|---|---|
| C1 | **Prüfung vs. Übung** | Session-Flag (siehe §4) | ✅ |
| C2 | **Zeit-Challenge** | Client-Timer | ✅ |
| C3 | **Spaced-Repetition der Fragen (Leitner-Box)** | neue Tabelle/Spalten | 🔧 Backlog |

> **C3 bewusst NICHT in v1:** Es gibt schon `/review` für SRS — eine zweite SRS-Engine
> verwirrt, bringt bei ≈0 Nutzern keinen Datennutzen und ist teuer. B1+B3 („falsche/
> hartnäckige zuerst") liefern 80 % des Nutzens ohne Schema-Änderung.

### Querschnitt-Regeln für ALLE Modi

- **`fill_blank` immer ausschliessen** — `question_type IN ('multiple_choice','true_false','matching')`. Gilt auch für Altbestand (Legacy/verboten).
- **Zugriff serverseitig, nie clientseitig** — jeder Sammel-/Mock-Modus filtert den Frage-Pool **vor** Auslieferung über `Lesson.is_accessible_to_user` (`models.py:793-865`, eine Python-Methode, kein SQL-Feld → Pool grob in SQL ziehen, in Python pro Lesson filtern, einmal pro Session cachen). Diese Methode ist **die** richtige Schnittstelle, egal wie die Monetarisierung steht (siehe FREE_MODE-Hinweis unten) — sie kapselt Gast/Frei/Bezahlt/Premium an einer Stelle.
- **Ehrliche Zähler** — „Y von ~790 verfügbar" statt „790", damit der Mock keine falsche Vollständigkeit suggeriert und der Bundle-Hinweis ehrlich greift.
- **Test verfälscht Lektions-Fortschritt nicht** — Default: Test-Antworten **nicht** ins `UserQuizAnswer`-Upsert schreiben (sonst überschreibt ein Übungslauf `answered_at`/`is_correct` der Lektion). Bewusste Entscheidung, kein Bug. (→ langfristig saubere Trennung via `source`-Feld, §8.)
- **`matching`-Sonderfall** — die korrekte Zuordnung steckt im `QuizOption.feedback` (`models.py:1305`), nicht in `is_correct`-Optionen. Render- und Auswertungslogik müssen das gesondert behandeln.
- **Empty-State ist Pflicht** — jeder potenziell leere B-Modus leitet aktiv auf ein A-Rückgrat-Modul.

## 6. Der N5-Mock (Flaggschiff-Modus, A3)

Echter JLPT N5 hat drei Sektionen — **Hörverstehen (Chōkai) kann die Plattform per Quiz
nicht abbilden**. Das muss die Seite **ehrlich kommunizieren**, nicht so tun als sei es
ein Voll-JLPT. Sektionen lassen sich am ehrlichsten über den `content_type` der
verknüpften `LessonContent` ableiten:

| Sektion | Inhalt | Ableitung | testbar |
|---|---|---|---|
| **Moji-Goi** 文字・語彙 | Schrift & Wortschatz | content_type kana/kanji/vocabulary | ✅ |
| **Bunpō** 文法 | Grammatik | content_type grammar (+ `matching`) | ✅ |
| **Dokkai** 読解 | Leseverstehen | content_type text | ✅ (begrenzt) |
| **Chōkai** 聴解 | Hörverstehen | — | ❌ nicht via Quiz |

Pragmatischer Start: **gemischter Mock ohne Sektions-Split** (ein Pool), Sektions-
Aufschlüsselung im Ergebnis als Ausbaustufe — **kein Blocker für v1**.

Parameter (an ~790 Fragen kalibriert, je User nur die *zugänglichen*):

| Kennwert | Voll-Mock | Mini-Mock („Schnell-Check") |
|---|---|---|
| Fragenzahl | 40–50 | 15 |
| Soft-Timer | ~45 Min | 15 Min |
| **Pass-Schwelle** | **60 %** | 60 % |

> **Pass-Schwelle 60 % ist die ehrliche Zahl** und wird **transparent begründet**: der
> echte JLPT N5 verlangt ~44 % gesamt plus eine Sektions-Mindestschwelle. 44 % als
> „bestanden" wirkt geschenkt; 60 % ist anspruchsvoll und gibt Puffer für den
> schwereren Realtest. Beschriften: *„Bestanden ab 60 % — der echte JLPT N5 braucht
> ~44 % gesamt, wir setzen die Latte bewusst höher."*

**Zugriffskontrolle macht die Paywall zum Feature:** Der Mock zieht nur Fragen aus
zugänglichen Lektionen → die Mock-Grösse ist pro User verschieden („Dein N5-Mock: 312
verfügbare Fragen"). Wenn der Pool zu klein ist: Mini-Mock + ehrlicher Bundle-Hinweis,
kein Hard-Lock.

> **⚠️ FREE_MODE-Caveat (Stand 2026-06-20, Branch `free-mode-umstellung`):** Die
> Plattform ist aktuell **komplett gratis** (FREE_MODE, reversibel — Preise genullt +
> Flag-gated). Heisst: `is_accessible_to_user` liefert für alle Lektionen „zugänglich",
> der Mock umfasst faktisch **alle ~790 Fragen**, und der Bundle-Upsell (Wireframe W11)
> sowie der `--kincha`-Gesperrt-Marker laufen ins Leere. **Trotzdem über
> `is_accessible_to_user` bauen** — die Methode ist FREE_MODE-agnostisch und bleibt
> korrekt, falls die Bezahl-Schicht reaktiviert wird. Die Upsell-/Locked-States im
> Konzept sind also für den reversiblen Bezahl-Fall vorgesehen; im aktuellen FREE_MODE
> erscheinen sie schlicht nicht. (CHF-130-Prüfungsgebühr bleibt unabhängig bestehen.)

## 7. Didaktische Leitplanken (Kurzfassung)

1. **Modus-Trennung ist nicht verhandelbar** (§4) — ein Schalter oben, der alles umstellt.
2. **Testing-Effekt vor Re-Reading** — `explanation` erscheint **nach** dem Versuch, nie davor.
3. **Spacing > sofortige Wiedervorlage** — falsche Fragen kommen idealerweise verzögert zurück (Leitner 1/3/7 Tage); v1 darf simpel „attempts>1 ∨ is_correct=False" ohne Terminierung sein.
4. **Interleaving erzwingen** — im Mock und im Schwächen-Modus Themen/Typen mischen, nie thematisch blocken.
5. **Ehrliche, transparente Schwellen** — Pass-Schwelle sichtbar + begründet; Score auf `points`-gewichtete, *zugängliche* Fragen; **Teilpunkte bei `matching`** (3/4 Paare = 0,75), nichts schönrechnen.
6. **Gestuftes, distraktorspezifisches Feedback** — Reihenfolge `hint` → `explanation` → `QuizOption.feedback`. Distraktor-Feedback („warum *diese* Wahl falsch ist") ist der grösste ungenutzte Lernhebel im Schema.
7. **Zugriffskontrolle ist Teil der Didaktik** — nie-gesehene Fragen aus nicht gekauften Lektionen sind tabu; der begrenzte Pool wird ehrlich kommuniziert.
8. **History-unabhängige Modi sind das Rückgrat** — jeder potenziell leere Modus leitet auf einen vollen um.

## 8. Roadmap (Phasen)

**Phase 0 — v1, keine Schema-Änderung.** Konfig-Seite + Session-Engine; Modi Übung &
Prüfung; Rückgrat A1–A6; Falsch-Filter B1 via Proxy; Ergebnis-Screen mit Score-Ring;
Wiederverwendung der `/review`- und `/practice/kana`-Muster; Zugriffskontrolle;
clientseitiges „nur Falsche nochmal". Test-Antworten **nicht** persistiert.

**Phase 1 — Präzision (`times_wrong`).** Eine Spalte auf `UserQuizAnswer`:
`times_wrong INT default 0`; bei falscher Antwort `+= 1`. Gewinnt exaktes „wie oft
daneben", saubere Leech-Schwelle, „falsch-dann-richtig". Alembic Add-Column + Backfill
`GREATEST(attempts - is_correct::int, 0)`. Ehrlicher „Deine Fehler"-Zähler in der Nav.

**Phase 2 — Append-only Antwort-Log (`quiz_answer_event`).** Tabelle
`id, user_id, question_id, is_correct, answered_at, source ('lesson'|'test')`. Volle
Fehler-Historie, Fehler-über-Zeit-Charts, **saubere Trennung Lektions- vs. Test-
Antworten**, Datenbasis für echtes SRS. Erst bei realem Nutzervolumen sinnvoll.

**Phase 3 — Leitner/SRS-of-Questions (C3) + Sektions-Mock + adaptive Schwierigkeit.**
Optionale Ausbaustufen, abhängig von echten Nutzern. Stats-Integration (`/review/stats`
Donut „Erfolgsrate pro Modul").

## 9. Offene Entscheidungen (für den Haupt-Thread / Nutzer)

1. **Route/Name:** `/pruefen` „Prüfen" (Empfehlung) vs. `/test` vs. `/quiz`?
2. **Nav-Icon:** `✓` (ruhig) vs. `試` (Kanji, on-brand aber kryptischer)?
3. **XP im Test?** Sparsam wie Kana-Storm (Basis + Bonus, UTC-Tages-Cap, Anti-Cheat) oder gar kein XP (reiner Selbsttest)?
4. **Test-Antworten persistieren?** v1-Empfehlung: nein (risikofrei). Falls „Deine Fehler" *sofort* aus Tests wachsen soll, braucht es Phase 1/2.
5. **Mock-Sektionen** ab v1 (Moji-Goi/Bunpō/Dokkai) oder erst als Ausbau (gemischt starten)?
6. **Gast-Demo:** 3 Demo-Fragen ohne Login (Conversion) ja/nein?

→ Wireframes & Interaktion: [`01-wireframes-und-flows.md`](01-wireframes-und-flows.md) ·
Inspiration, Tokens & Microcopy: [`02-inspiration-design-microcopy.md`](02-inspiration-design-microcopy.md)
