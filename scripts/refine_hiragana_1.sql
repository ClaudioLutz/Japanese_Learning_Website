-- Refine N5 Hiragana 1 (Lesson ID 146) — Text-Inhalte
-- Erwartete Zeilen pro UPDATE: 1
-- Fachreview: 2026-05-02 (Recherche aus Tofugu, Wikipedia, Japanese Phonology, Migaku)
SET client_encoding = 'UTF8';

BEGIN;

-- Page 1, Block 1 (id=6224): Einführung
UPDATE lesson_content SET content_text = $TEXT$## Was ist Hiragana?

Hiragana ist eine der **drei japanischen Schriften** (neben Katakana und Kanji). Es ist eine **Silbenschrift** — jedes Zeichen steht für eine Silbe, nicht für einen einzelnen Laut wie bei unseren Buchstaben.

- **46 Grundzeichen** insgesamt
- Wird verwendet für **japanische Wörter**, Endungen und Partikel
- Ist die **erste Schrift**, die japanische Kinder lernen — und der natürliche Startpunkt auch für dich

> **Woher kommen die Zeichen?** Hiragana entstand vor über 1'000 Jahren aus chinesischen Schriftzeichen, die in Schreibschrift abgekürzt wurden. 「あ」 zum Beispiel ist eine vereinfachte Form von 安 (Ruhe). Du musst diese Herkunft nicht auswendig lernen, aber sie erklärt, warum die Zeichen so geschwungen aussehen.

## Was lernst du in dieser Lektion?

Die ersten **drei Reihen** der Hiragana-Tabelle, also **15 Zeichen**:

1. Die fünf **Vokale**: 「あいうえお」 (a, i, u, e, o)
2. Die **K-Reihe**: 「かきくけこ」 (ka, ki, ku, ke, ko)
3. Die **S-Reihe**: 「さしすせそ」 (sa, shi, su, se, so)

> **Merke:** Sobald du Vokale + Konsonanten kombinieren kannst, kannst du bereits hunderte japanische Wörter lesen — z.B. 「いえ」 (ie, 'Haus') oder 「すし」 (sushi).

## Wie liest man die Tabelle?

Die Hiragana-Tabelle ist nach einem **Muster** aufgebaut: Konsonant + Vokal. Die Vokal-Reihenfolge **a → i → u → e → o** ist immer gleich. Das macht das Lernen leichter, sobald du die Vokale beherrschst.

**Tipp:** Sprich jedes Zeichen **laut aus**, während du es ansiehst. Das verknüpft Form und Klang im Gedächtnis. Auf den Karten findest du zusätzlich **Mini-Eselsbrücken** — kleine Bilder, die helfen, die Form zu merken.$TEXT$
WHERE id = 6224 AND lesson_id = 146;

-- Page 2, Block 1 (id=6225): Vokale
UPDATE lesson_content SET content_text = $TEXT$## Vokale — die Basis

Die fünf Vokale sind die **wichtigsten Zeichen überhaupt**, weil jede weitere Hiragana-Reihe auf ihnen aufbaut. Japanische Vokale sind **kurz, klar und gleichlang** — kein Dehnen, kein Verschlucken.

- **あ (a)** wie in *Wasser*, *Vater* — ein offenes, kurzes "a"
- **い (i)** wie in *bitte*, *Liebe* — ein kurzes "i"
- **う (u)** ⚠ — wie in *Mutter*, aber **ohne die Lippen zu runden**. Das japanische "u" ist gerade, fast wie ein eingeatmetes "ü" ohne Spitzmund. Nicht wie das deutsche "u" in *Buch* (zu rund).
- **え (e)** wie in *Bett*, *Heft* — ein klares, kurzes "e", weder zu offen noch zu geschlossen
- **お (o)** wie in *Onkel*, *Opa* — ein kurzes "o", **nicht** so lang wie in *Boot*

> **Eselsbrücken zum Merken:**
> - 「あ」 hat ein "**A**" eingebaut — links oben siehst du die Form
> - 「い」 sind zwei stehende "**Stäbchen**" — wie zwei "i" nebeneinander
> - 「う」 ist eine "**U**"-Form mit Hut
> - 「え」 sieht aus wie ein **exotischer Vogel** mit Federhaube
> - 「お」 hat **zwei o-Schleifen** — eine grosse, eine kleine rechts

> **Übung:** Sag 「あいうえお」 (a-i-u-e-o) mehrmals hintereinander, bis es flüssig klingt. Diese Reihenfolge wirst du **überall** wiederfinden.$TEXT$
WHERE id = 6225 AND lesson_id = 146;

-- Page 2, Block 2 (id=6231): K-Reihe
UPDATE lesson_content SET content_text = $TEXT$## K-Reihe — Konsonant K + Vokal

Die K-Reihe folgt dem **Bauplan: K + Vokal**. Du erkennst die fünf Vokal-Endungen wieder. Der K-Laut ist immer **klar und stimmlos**, nie weich wie ein "g".

- **か (ka)** wie in *Karte*
- **き (ki)** wie in *Kiste* — klingt wie das englische Wort *key*
- **く (ku)** wie in *Kuss* (kurz, mit unrundiertem u — also kein deutsches "Kuh")
- **け (ke)** wie in *Kette*
- **こ (ko)** wie in *Korb*

> **Eselsbrücken:**
> - 「か」 sieht aus wie eine **Mücke** (Japanisch *ka* = Mücke!)
> - 「き」 sieht aus wie ein **Schlüssel** ("**k**ey")
> - 「く」 ist der **offene Schnabel** eines Kuckucks: "ku-ku"
> - 「け」 sieht aus wie ein Stengel **Kelp** (Seetang)
> - 「こ」 sind zwei **Kabel** nebeneinander

> **Mini-Wörter zum Lesen:** 「いけ」 (ike, 'Teich'), 「あか」 (aka, 'rot'), 「こえ」 (koe, 'Stimme'), 「えき」 (eki, 'Bahnhof'), 「きく」 (kiku, 'hören' / 'Chrysantheme').$TEXT$
WHERE id = 6231 AND lesson_id = 146;

-- Page 2, Block 3 (id=6237): S-Reihe
UPDATE lesson_content SET content_text = $TEXT$## S-Reihe — mit einer Ausnahme

Die S-Reihe folgt dem Muster **S + Vokal** — **bis auf eine Ausnahme**. Das "s" ist immer **stimmlos** wie im Englischen *snake*, nie weich wie das deutsche "Sonne".

- **さ (sa)** wie in *Sand* — stimmloses s
- **し (shi)** ⚠ — nicht 'si', sondern **'schi'**, wie in *Schiene*. **Wichtigste Eigenheit der ganzen Tabelle.**
- **す (su)** — stimmloses s + unrundiertes u. **In manchen Wörtern wird das u fast verschluckt** (siehe nächste Seite zum Thema "Vokal-Entstummung")
- **せ (se)** wie in *Seele*, *Sektor* — kurz und stimmlos
- **そ (so)** wie in *Sonntag* (mit stimmlosem s)

> **Eselsbrücken:**
> - 「さ」 sind zwei Hände, die **Salsa** in einer Schüssel rühren
> - 「し」 ist ein **Schäferhaken** — ein Schäfer, der "Schafe" hütet (sh!)
> - 「す」 ist eine **Schaukel** mit jemandem oben
> - 「せ」 ist ein Mund mit einem **Vampir-Eckzahn**
> - 「そ」 ist jemand, der **Soda durch einen Strohhalm schlürft**

## Mini-Wörter zum Lesen üben

Schau dir diese Wörter an und versuche sie laut zu lesen:

- 「あおい」 (aoi, 'blau')
- 「いえ」 (ie, 'Haus')
- 「かさ」 (kasa, 'Regenschirm')
- 「すし」 (sushi)
- 「せき」 (seki, 'Sitz/Platz')
- 「あさ」 (asa, 'Morgen')
- 「あし」 (ashi, 'Fuss')
- 「いし」 (ishi, 'Stein')
- 「しお」 (shio, 'Salz')$TEXT$
WHERE id = 6237 AND lesson_id = 146;

-- Page 3, Block 1 (id=6243): Aussprache & Schreibhinweise
UPDATE lesson_content SET content_text = $TEXT$## Aussprache — die wichtigsten Regeln

**Vokale sind kurz und gleichlang.** Anders als im Deutschen werden Einzelvokale **nicht gedehnt**. 「あ」 (a) klingt kurz — nicht 'aaaa'. (Lange Vokale werden später durch zwei Zeichen geschrieben, z.B. 「おお」 = ō.)

**Stimmlose Konsonanten.** Das **s** in 「さ」 (sa), 「す」 (su), 「せ」 (se), 「そ」 (so) ist immer **stimmlos** wie im englischen *snake* — nie weich wie im deutschen *Sonne*.

**Die Ausnahme 「し」 (shi).** Statt 'si' sprichst du **'schi'**. Diese unregelmässige Stelle gibt es in fast jeder Reihe — präge sie dir aktiv ein.

**Japanisches "u" ist nicht wie deutsches "u".** Die Lippen bleiben **flach**, nicht gerundet. Es klingt eher wie ein eingeatmetes "ü" ohne Spitzmund.

## Vokal-Entstummung — warum 「す」 oft fast verschwindet

Eine wichtige Regel, die dich später nicht überraschen soll:

**Die Vokale "u" und "i" werden oft fast lautlos**, wenn sie zwischen zwei stimmlosen Konsonanten stehen oder am Wortende nach einem stimmlosen Konsonanten kommen. Das nennt man **Entstummung** (engl. *devoicing*).

- 「すし」 klingt für viele Ohren nicht wie "su-shi", sondern eher wie **"s'shi"** — das erste "u" wird zu einem hauchigen Atemzug, fast unhörbar.
- 「です」 (desu, 'ist') klingt wie **"des"** — das "u" am Ende wird verschluckt.
- 「ます」 (masu, höfliche Verbendung) klingt wie **"mas"**.

Die Mundform für den Vokal bleibt — aber die Stimme setzt nicht ein. Das ist **kein Faulheits-Effekt**, sondern Standard im Tokyo-Japanisch und gilt auch für JLPT-Hörverstehen.

> **Faustregel:** Wenn du 「す」 oder 「し」 zwischen *k, s, sh, t, ts, ch, p, h* hörst — oder am Satzende nach diesen Lauten — dann wird der Vokal oft fast stumm. Sprich sie selbst kurz, nicht überdeutlich.

## Verwechslungsgefahr

Manche Zeichen sehen sich ähnlich. **Schau genau hin:**

- 「あ」 (a) vs. 「お」 (o) — beide haben einen Querstrich oben, aber **a** hat eine **Schleife** unten links, **o** hat einen **kleinen Tropfen** rechts
- 「い」 (i) vs. 「り」 (ri) — i lernst du jetzt, **i** hat **zwei kurze, gerade Striche**; ri (später) ist geschwungener
- 「う」 (u) vs. 「つ」 (tsu) — u hat einen **Hut oben**, tsu nicht
- 「こ」 (ko) sind **zwei waagerechte Striche** — verwechselbar mit Katakana 「コ」 (auch ko)
- 「さ」 (sa) und 「き」 (ki) haben einen ähnlichen Aufbau — Unterschied: **sa** hat **einen** Querstrich oben, **ki** hat **zwei**

> **Lerntipp:** Schreibe jedes Zeichen mindestens **fünfmal** mit der Hand. Die Bewegung verankert die Form besser als reines Anschauen.

## Strichfolge — kurz erklärt

Jedes Hiragana-Zeichen hat eine **festgelegte Strichfolge** (wie viele Striche, in welcher Reihenfolge, in welche Richtung). Das wirkt am Anfang umständlich, ist aber wichtig:

1. Die Schrift sieht **gleichmässiger** aus
2. Du kannst Zeichen **schneller** schreiben
3. Du erkennst Zeichen **besser wieder**

Faustregel: **von oben nach unten**, **von links nach rechts**. Auf jeder Hiragana-Karte findest du die genaue Strichfolge.$TEXT$
WHERE id = 6243 AND lesson_id = 146;

-- Page 4, Block 1 (id=6244): Quiz-Vorlauf — Anzahl Fragen aktualisieren
UPDATE lesson_content SET content_text = $TEXT$## Teste dein Wissen

Gleich kommen **Fragen** zu den 15 Hiragana, die du gerade gelernt hast.

- **Multiple-Choice:** Welche Romaji-Lesung passt zum Zeichen?
- **Richtig/Falsch:** Stimmt die angegebene Lesung?
- **Wort-Lesung:** Welches Wort siehst du?
- **Matching:** Verbinde Zeichen mit Lesung

> **Tipp:** Wenn du dir unsicher bist, ist das **kein Problem** — du kannst die Übung beliebig oft wiederholen. Das Erkennen kommt mit der Zeit.$TEXT$
WHERE id = 6244 AND lesson_id = 146;

-- Page 5, Block 1 (id=6245): Zusammenfassung
UPDATE lesson_content SET content_text = $TEXT$## Geschafft — die ersten 15 Hiragana

Du hast in dieser Lektion gelernt:

- Die **fünf Vokale** 「あいうえお」 (a, i, u, e, o)
- Die **K-Reihe** 「かきくけこ」 (ka, ki, ku, ke, ko)
- Die **S-Reihe** 「さしすせそ」 (sa, shi, su, se, so)
- Die wichtigste **Ausnahme**: 「し」 (shi statt si)
- Wie die Hiragana-Tabelle **aufgebaut** ist (Konsonant + Vokal, Reihenfolge a-i-u-e-o)
- Dass das **japanische "u"** unrundiert ist und manchmal fast verschluckt wird (Entstummung)

## Wörter, die du jetzt lesen kannst

Mit nur diesen 15 Zeichen liest du schon eine ganze Reihe echter japanischer Wörter:

- 「あおい」 (aoi) — blau
- 「いえ」 (ie) — Haus
- 「かさ」 (kasa) — Regenschirm
- 「すし」 (sushi) — Sushi
- 「せき」 (seki) — Sitz, Platz
- 「あし」 (ashi) — Fuss
- 「あさ」 (asa) — Morgen
- 「こえ」 (koe) — Stimme
- 「いし」 (ishi) — Stein
- 「あき」 (aki) — Herbst
- 「えき」 (eki) — Bahnhof
- 「しお」 (shio) — Salz

> **Probier es:** Lies jedes Wort **laut**, ohne auf die Romaji zu schauen. Wenn das gelingt, ist die Lektion gesessen.

## Lerntipps für die nächsten Tage

1. **Schreibe jeden Tag** alle 15 Zeichen einmal mit der Hand — fünf Minuten reichen
2. **Lies Wörter laut**, nicht nur Zeichen — Wörter geben Bedeutung und festigen besser
3. **Wiederhole das Quiz**, bis du alle Fragen ohne Hilfe schaffst
4. **Achte beim Hören** auf Entstummung: 「です」 = "des", 「すし」 ≈ "s'shi" — das ist normal

## Was kommt als Nächstes?

- **Hiragana 2** — die T-Reihe 「たちつてと」, N-Reihe 「なにぬねの」 und H-Reihe 「はひふへほ」 (15 weitere Zeichen)
- Danach Hiragana 3 (m/y/r/w + ん) und schliesslich Diakritika (が/ざ/だ/ば/ぱ) und Yōon (きゃ/しゃ/…)

Wenn du Hiragana komplett kannst, beginnst du mit den ersten **Vokabel-Lektionen** auf N5-Niveau.$TEXT$
WHERE id = 6245 AND lesson_id = 146;

-- Validierung: Erwartete Anzahl betroffener Zeilen ist 7
SELECT id, page_number, order_index, LEFT(content_text, 60) AS preview, length(content_text) AS chars
FROM lesson_content
WHERE lesson_id = 146 AND content_type = 'text'
ORDER BY page_number, order_index;

COMMIT;
