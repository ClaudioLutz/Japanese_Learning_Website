# Recherche: Lektions-Abschnitte — Spielerisch & Informativ

**Stand:** März 2026

Ziel: Abwechslungsreiche Abschnitte, die sowohl Spass machen als auch substanziell etwas lehren. Keine trockenen Quizzes, keine Spiele ohne Lerneffekt.

---

## Bewertungssystem

Jeder Abschnitt wird bewertet nach:
- 🎮 **Spielspass** (1-5): Wie unterhaltsam ist die Aktivität?
- 📚 **Lerneffekt** (1-5): Wie viel bleibt hängen?
- 🔧 **Umsetzbarkeit** (1-5): Wie einfach ist die Implementierung? (HTML/CSS/JS)

---

## A. Spielerische Übungstypen

### 1. Tap the Pairs (Memory-Paare)
🎮5 📚3 🔧5

Ein Raster mit 8-12 Karten — halb Japanisch, halb Deutsch. User tippt auf eine japanische Karte, dann auf die passende Übersetzung. Korrekte Paare verschwinden mit Animation. Optionaler Timer für Bestzeit-Challenge.

**Trainiert:** Vokabeln, Kana-Erkennung
**Technik:** CSS Grid, Click-Events, einfache State-Logik

---

### 2. Sentence Builder (Satz-Puzzle)
🎮5 📚5 🔧3

Deutscher Satz oben, darunter japanische Wortblöcke in zufälliger Reihenfolge. User tippt die Blöcke in der richtigen Reihenfolge an. Partikel (は, が, を, に) sind eigene Blöcke. Farbcodierung: Subjekt=blau, Verb=rot, Objekt=grün.

**Trainiert:** Satzstruktur, Partikel, SOV-Reihenfolge
**Technik:** Drag & Drop oder Tap-to-Order, Reihenfolge-Validierung

---

### 3. Speed Review (Blitz-Runde)
🎮4 📚3 🔧4

Flashcard-artige Karten mit 5-Sekunden-Countdown. Japanisches Wort erscheint, 4 Antwortmöglichkeiten. Richtig = Bonuszeit + Combo-Multiplikator. Falsch = Zeit-Abzug. Highscore am Ende.

**Trainiert:** Schnelle Vokabel-Erkennung
**Technik:** Timer, Score-Counter, einfache UI

---

### 4. Partikel-Slot (Partikel einsetzen)
🎮4 📚5 🔧5

Japanischer Satz mit Lücke. Darunter eine Reihe Partikel-Buttons: は が を に で と へ から まで. User tippt auf den richtigen. Bei korrekter Antwort: kurze Erklärung warum. Bei falscher: Erklärung des Unterschieds.

**Trainiert:** Partikel-Grammatik (eines der schwierigsten Themen!)
**Technik:** Button-Reihe, Feedback-Anzeige — sehr einfach

---

### 5. Kana Whack-a-Mole (Hau-den-Maulwurf)
🎮5 📚3 🔧3

Kana-Zeichen "poppen" in zufälligen Feldern auf (3x3 Grid). Oben steht eine Romaji-Lesung ("ka"). User muss schnell auf das richtige Kana (か) klicken. Combo-Multiplikator für Serien.

**Trainiert:** Kana-Erkennung, Reaktionszeit
**Technik:** Timer, zufällige Positionierung, Animations-Management

---

### 6. Falling Words (Fallende Wörter)
🎮5 📚3 🔧3

Japanische Wörter fallen von oben nach unten. User tippt die Bedeutung/Lesung ein, bevor das Wort den Boden erreicht. Korrekte Eingabe "zerstört" das Wort. Geschwindigkeit steigt.

**Trainiert:** Vokabeln, Kanji-Lesung, Tippgeschwindigkeit
**Technik:** Canvas/CSS-Animation, Keyboard-Input

---

### 7. Satz-Auktion (Grammatik-Wette)
🎮4 📚5 🔧4

Mehrere japanische Sätze — einige korrekt, einige mit Fehlern. User hat ein Budget an Münzen und "bietet" auf die Sätze, die er für korrekt hält. Richtig = Gewinn, falsch = Verlust. Erklärt danach jeden Fehler.

**Trainiert:** Grammatik, Fehlererkennung, kritisches Lesen
**Technik:** Einfache Spielökonomie, Bieten-UI

---

### 8. Shiritori (しりとり — Wörter-Kette)
🎮5 📚4 🔧3

Das klassische japanische Wortspiel: Ein Wort wird gezeigt (さくら). User tippt ein Wort das mit der letzten Silbe beginnt (ら → らーめん). Wer ein Wort auf ん enden lässt, verliert. Gegen einen Bot spielbar.

**Trainiert:** Aktiver Wortschatz, Kana-Lesen/Schreiben
**Technik:** Wörterbuch-Validierung, Bot-Logik

---

## B. Informative & Entdeckungs-Abschnitte

### 9. Kanji-Zeitreise (Kanji Evolution)
🎮4 📚5 🔧3

Animierte Timeline: Ein Slider zeigt, wie ein Kanji sich von der Orakelknochen-Schrift (~1400 v.Chr.) zum modernen Zeichen entwickelt hat. 山 war eine Bergzeichnung, 川 fliessendes Wasser, 木 ein Baum. User zieht den Slider und sieht die Transformation.

**Trainiert:** Kanji-Bedeutungen, Radikale, piktographisches Verständnis
**Technik:** SVG-Animationen, Slider-Interaktion
**Besonders wertvoll:** Wenn User sehen, dass 木→林→森 (Baum→Wald→dichter Wald) wirklich zusammengehören

---

### 10. Eselsbrücken-Studio (Mnemonic-Werkstatt)
🎮3 📚5 🔧4

Für jedes Kanji: Zerlegung in Radikale + illustrierte Geschichte. 休 (Ruhe) = 人 (Person) + 木 (Baum) → "Eine Person lehnt sich an einen Baum, um sich auszuruhen." Mit KI-generiertem Bild. User kann auch eigene Eselsbrücken schreiben.

**Trainiert:** Kanji-Radikale, Langzeitgedächtnis
**Technik:** Kanji-Datenbank, Bild-Text-Kombination
**Forschung:** WaniKani zeigt — je verrückter die Geschichte, desto besser die Erinnerung

---

### 11. Kontrast-Brücke (Deutsch ↔ Japanisch)
🎮3 📚5 🔧4

Side-by-Side-Vergleich: Links ein deutscher Satz, rechts das japanische Äquivalent. Farbcodierte Satzglieder zeigen die Umstellung (SOV vs. SVO). Animierte Umordnung: Die deutschen Wörter bewegen sich in die japanische Reihenfolge.

```
Deutsch:    [Ich]  [esse]    [Sushi]
             ↓       ↓         ↓
Japanisch:  [私は]  [寿司を]   [食べます]
            Subj    Objekt    Verb
```

**Trainiert:** Satzstruktur-Verständnis, Partikel-Funktionen
**Technik:** CSS-Animationen, farbcodierte Blöcke

---

### 12. Discovery-Puzzle (Mustererkennung)
🎮4 📚5 🔧4

Mehrere Beispielsätze mit einem gemeinsamen Grammatik-Muster — aber OHNE Erklärung. User muss die Regel selbst entdecken und aus 3-4 Optionen die richtige wählen. Erst danach kommt die Auflösung.

```
① 東京に行きます (Ich gehe nach Tokyo)
② 学校に行きます (Ich gehe zur Schule)
③ 日本に行きます (Ich gehe nach Japan)

Frage: Was macht に in diesen Sätzen?
A) Markiert das Objekt
B) Markiert das Ziel/die Richtung  ← ✓
C) Markiert die Zeit
```

**Trainiert:** Grammatikregeln, analytisches Denken
**Forschung:** "Regeln, die selbst entdeckt werden, werden besser erinnert als erklärte Regeln"
**Technik:** Multiple-Choice mit Beispiel-Sammlung

---

### 13. Sound-Landschaft (Onomatopoesie-Welt)
🎮5 📚4 🔧3

Illustrierte japanische Szene (z.B. Sommerfest, Regenzeit). User klickt auf Elemente und hört den Klang + die japanische Onomatopoesie:
- Regen: ザーザー (zaa-zaa)
- Glocke: カンカン (kan-kan)
- Katze: ニャーニャー (nyaa-nyaa)
- Wind: ビュービュー (byuu-byuu)

**Trainiert:** Onomatopoesie (riesiges System im Japanischen), sensorisches Vokabular
**Technik:** Klickbare Bildbereiche, Audio-Clips

---

### 14. Satz-Röntgen (Sprachforensik)
🎮3 📚5 🔧3

Ein japanischer Satz, den der User Schicht für Schicht "sezieren" kann. Klick auf ein Element zeigt: grammatische Funktion, Herkunft, Alternativen. Verschiedene "Ebenen" umschaltbar:

```
Ebene 1: 私は毎日学校に行きます
Ebene 2: [Subj+は] [Zeit] [Ziel+に] [Verb+ます]
Ebene 3: [Thema] [wann] [wohin] [was tun]
```

**Trainiert:** Tiefes Grammatik-Verständnis, Satzanalyse
**Technik:** Interaktive Ebenen, Klick-Tooltips

---

### 15. Wort-Galaxie (Vokabel-Netzwerk)
🎮3 📚5 🔧3

Interaktives Netzwerk-Diagramm: Verwandte Wörter als verbundene Knoten. Ausgehend von einem Kanji (z.B. 食) verzweigt sich das Netzwerk:

```
        食べる (essen)
       /
食 ── 食事 (Mahlzeit)
       \
        食堂 (Kantine)
         \
          食品 (Lebensmittel)
```

Klick auf einen Knoten zeigt Details, Beispielsatz, Audio.

**Trainiert:** Wortfamilien, Kanji-Zusammensetzungen, semantische Verbindungen
**Technik:** D3.js oder vis.js für Netzwerk-Visualisierung

---

## C. Immersions- & Kultur-Abschnitte

### 16. Visual Novel (Entscheide-dich-Geschichte)
🎮5 📚5 🔧3

Illustrierte Geschichte im Anime-Stil. Am Ende jeder Szene wählt der User eine Antwort auf Japanisch. Die Geschichte verzweigt sich — verschiedene Pfade, verschiedene Enden. Falsche Antworten führen zu lustigen Situationen (nicht zu Game Over).

```
店員: いらっしゃいませ！ご注文は？
→ A) ラーメンをください (Ramen bitte)
→ B) お会計をお願いします (Die Rechnung bitte)
→ C) トイレはどこですか (Wo ist die Toilette?)
```

**Trainiert:** Kontextuelle Grammatik, Höflichkeitsformen, Lesen
**Technik:** Dialogbaum-Datenstruktur, Chat-UI, Branching-Logik

---

### 17. Etikette-Simulator (Die Luft lesen)
🎮5 📚5 🔧3

Animierte Alltagsszenen in Japan. User wählt die sozial korrekte Handlung:
- Wo sitzt man im Taxi? (Hinter dem Fahrer)
- Wie übergibt man eine Visitenkarte? (Mit beiden Händen)
- Wann verbeugt man sich wie tief?
- Darf man im Zug telefonieren? (Nein!)

**Trainiert:** Japanische Umgangsformen, Business-Etikette, Uchi/Soto-Konzept
**Technik:** Illustrierte Szenen, Multiple-Choice mit Erklärung

---

### 18. Interaktive Japan-Karte (Kultur-Explorer)
🎮4 📚5 🔧3

Klickbare Karte Japans mit allen 47 Präfekturen. Jede Region zeigt:
- Lokaler Dialekt (Audio-Sample)
- Regionale Spezialität (Bild + Vokabeln)
- Berühmte Orte
- Mini-Quiz pro Region

**Trainiert:** Geografie, Dialekte, regionale Kultur, thematisches Vokabular
**Technik:** SVG-Karte, Klick-Events, Content pro Region

---

### 19. Koch-Lektion (Rezept auf Japanisch)
🎮4 📚4 🔧4

Step-by-Step japanisches Rezept (z.B. Onigiri). Jeder Schritt: Bild + japanischer Text + Audio + klickbare Vokabeln. Am Ende: Quiz über Zutaten und Verben. User kann es tatsächlich nachkochen!

**Trainiert:** Küchenvokabular, Imperativ-/Te-Form, Mengenangaben
**Technik:** Schritt-für-Schritt-UI, Bilder, Audio

---

### 20. Kultur-Detektiv (Bild-Analyse)
🎮4 📚5 🔧4

Foto/Illustration einer japanischen Szene. User muss kulturelle Details identifizieren:
- "Was bedeutet das Torii?"
- "Warum stehen die Schuhe am Eingang?"
- "Was zeigt die Verbeugung?"

Punkte für korrekte Beobachtungen, dann ausführliche Erklärung.

**Trainiert:** Kulturwissen, visuelles Vokabular, interkulturelle Kompetenz
**Technik:** Klickbare Bildbereiche, Popup-Erklärungen

---

### 21. Hörkino (Audio-Story mit Transkript)
🎮3 📚5 🔧3

Podcast-artiges Hörabenteuer. Synchronisiertes Transkript — jedes Wort leuchtet auf, während es gesprochen wird. Audio verlangsambar. Klickbare Wörter für Sofort-Übersetzung. Danach: Verständnisfragen.

**Trainiert:** Hörverständnis, natürliche Sprachmelodie, Lesen
**Technik:** Audio-Player + Wort-Timing-Synchronisation (Vorbild: Satori Reader)

---

### 22. Minimalpaar-Challenge (Genau hinhören)
🎮4 📚4 🔧4

Audio spielt ein Wort ab. Zwei sehr ähnliche Optionen:
- きって vs. きて (Briefmarke vs. kommend)
- びょういん vs. びよういん (Krankenhaus vs. Schönheitssalon)
- おばさん vs. おばあさん (Tante vs. Grossmutter)

User muss die korrekte Option wählen.

**Trainiert:** Phonetik, Längenunterschiede, Doppelkonsonanten
**Technik:** Audio-Dateien, A/B-Auswahl — sehr einfach

---

### 23. Fehler-Detektiv (Machigai Sagashi)
🎮4 📚5 🔧4

Japanische Sätze mit absichtlichen Fehlern. User muss Fehler finden, markieren und korrigieren. Danach: Erklärung jedes Fehlers.

```
❌ 私はラーメンが食べます → ✓ 私はラーメンを食べます
   (が ist falsch, muss を sein — Objekt-Partikel)
```

**Trainiert:** Grammatik-Nuancen, häufige Lernerfehler
**Technik:** Text-Markierung, Korrektur-Input

---

### 24. Scrollytelling-Infografik (Wissensreise)
🎮3 📚5 🔧3

Visuell reiche, scrollbare Seite zu einem kulturellen Thema — z.B. "Die Reise einer Reisschale: Vom Reisfeld zum Tisch." Mit eingebetteten Mini-Quizzes, klickbaren Vokabeln, animierten Illustrationen.

**Trainiert:** Thematisches Vokabular, Kulturwissen, Leseverständnis
**Technik:** Scroll-basierte Animationen, eingebettete Interaktionen

---

## D. Fortgeschrittene Übungstypen

### 25. Konjugations-Maschine
🎮4 📚5 🔧3

Ein Verb in Grundform (食べる). "Slot-Machine"-Regler: negativ, Vergangenheit, te-Form, höflich. User stellt die gewünschte Kombination ein und tippt das Ergebnis. Visuelle "Maschine" mit Zahnrädern.

**Trainiert:** Verb-Konjugation
**Technik:** State-Management, Konjugations-Regelwerk

---

### 26. Cloze mit Hint-System (Bunpro-Stil)
🎮3 📚5 🔧4

Japanischer Satz mit Lücke. User tippt die Antwort. Hint-System mit 3 Stufen:
1. Grammatikregel
2. Erster Buchstabe
3. Antwort mit Erklärung

**Trainiert:** Aktives Recall, Grammatik, Partikel
**Technik:** Text-Input, String-Matching mit Toleranz
**Forschung:** Texteingabe >> Multiple Choice für echtes Lernen

---

## Empfehlung für Premium-Lektionen

### Must-Have (Phase 1 — in jeder Lektion)

| # | Abschnitt | Funktion in der Lektion |
|---|-----------|------------------------|
| 1 | **Visual Novel / Dialog** (#16) | Narrativer Rahmen — der rote Faden |
| 2 | **Satz-Röntgen** (#14) | Grammatik verstehen |
| 3 | **Sentence Builder** (#2) | Aktiv Sätze bauen |
| 4 | **Partikel-Slot** (#4) | Partikel üben |
| 5 | **Kontrast-Brücke** (#11) | Deutsch ↔ Japanisch verstehen |
| 6 | **Discovery-Puzzle** (#12) | Regeln selbst entdecken |

### Nice-to-Have (Phase 2)

| # | Abschnitt | Funktion |
|---|-----------|----------|
| 7 | **Kanji-Zeitreise** (#9) | Kanji-Lektionen |
| 8 | **Sound-Landschaft** (#13) | Onomatopoesie |
| 9 | **Etikette-Simulator** (#17) | Kulturlektionen |
| 10 | **Hörkino** (#21) | Hörverständnis |
| 11 | **Minimalpaar-Challenge** (#22) | Phonetik |
| 12 | **Shiritori** (#8) | Wortschatz-Spiel |

### Gamification (Phase 3)

| # | Abschnitt | Funktion |
|---|-----------|----------|
| 13 | **Falling Words** (#6) | Arcade-Drill |
| 14 | **Kana Whack-a-Mole** (#5) | Kana-Training |
| 15 | **Speed Review** (#3) | Blitz-Wiederholung |
| 16 | **Wort-Galaxie** (#15) | Wortschatz-Explorer |

---

## Was ein Spiel von einem Quiz unterscheidet

| Quiz (langweilig) | Spiel (engaging) |
|---|---|
| "Wählen Sie die richtige Antwort" | Karten verschwinden mit Animation |
| Richtig/Falsch-Text | Combo-Multiplikator, Sound-Effekte |
| Keine Konsequenz | Münzen gewinnen/verlieren |
| Immer gleich | Steigende Schwierigkeit |
| Passiv klicken | Aktiv bauen, ziehen, tippen |
| Abstrakte Punkte | Sichtbarer Fortschritt (Boxen, Karten, Karte) |

**Kernprinzip:** Die Aktivität selbst muss befriedigend sein — Punkte und Badges allein machen eine langweilige Übung nicht spassig.

---

## Quellen

- [Duolingo Exercise Types](https://duolingo.fandom.com/wiki/Exercise)
- [Bunpro Review — Tofugu](https://www.tofugu.com/reviews/bunpro/)
- [Satori Reader — How It Works](https://www.satorireader.com/how-it-works)
- [LingoDeer Review — Tofugu](https://www.tofugu.com/japanese-learning-resources-database/lingodeer/)
- [Human Japanese — How It Works](https://www.humanjapanese.com/how-it-works)
- [WaniKani — Kanji Radicals](https://www.tofugu.com/japanese/kanji-radicals-mnemonic-method/)
- [Guided Discovery in Grammar — Sanako](https://sanako.com/how-guided-discovery-could-transform-your-grammar-teaching)
- [Visual Novels for Learning — Semantic Scholar](https://www.semanticscholar.org/paper/A-(Visual)-Novel-Route-to-Learning)
- [Gamification in Language Learning — Smartico](https://www.smartico.ai/blog-post/gamification-in-language-learning)
- [BookWidgets: 25 Creative Language Activities](https://www.bookwidgets.com/blog/2025/04/25-creative-ideas-to-make-your-students-fall-in-love-with-learning-languages)
- [Kanji Origins — Kanji Portraits](https://kanjiportraits.wordpress.com/)
- [Uchisen — Learn Japanese Visually](https://uchisen.com/)
- [AnimCJK — Stroke Order SVG](https://github.com/parsimonhi/animCJK)
