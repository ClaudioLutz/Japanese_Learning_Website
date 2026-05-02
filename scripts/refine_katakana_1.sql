-- Refine N5 Katakana 1 (Lesson ID 151) — Text-Inhalte + Strichfolge
-- Erwartete Zeilen pro UPDATE: 1 (Text) bzw. 1 pro Kana (15x)
-- Recherche: 2026-05-02 (Tofugu, Wikipedia, Wiktionary EN, Migaku, Japanese Phonology)
SET client_encoding = 'UTF8';

BEGIN;

-- =====================================================
-- TEIL A: Text-Bloecke (7 Updates)
-- =====================================================

-- Page 1, Block 1 (id=6367): Einfuehrung — Was ist Katakana?
UPDATE lesson_content SET content_text = $TEXT$## Was ist Katakana?

Katakana ist die **zweite** der drei japanischen Schriften (neben Hiragana und Kanji). Wie Hiragana ist es eine **Silbenschrift** mit **46 Grundzeichen** — und sie steht für **dieselben Silben** wie Hiragana. Wenn du Hiragana schon kannst, lernst du hier nur **neue Formen für bekannte Klänge**.

## Wofür wird Katakana verwendet?

Katakana hat einen **klaren Zweck** — sobald du das siehst, weisst du fast immer, worum es geht:

- **Lehnwörter** aus anderen Sprachen (*gairaigo*): 「コーヒー」 (kōhī, 'Kaffee'), 「コンピューター」 (konpyūtā, 'Computer')
- **Eigennamen** ausländischer Personen, Länder, Marken: 「ドイツ」 (Doitsu, 'Deutschland'), 「クラウディオ」 (Kuraudio, 'Claudio')
- **Onomatopöie** (Lautmalerei): 「ワンワン」 (wanwan, 'Wuff-Wuff')
- **Tier- und Pflanzennamen** in wissenschaftlichen Texten: 「サクラ」 (sakura, 'Kirschblüte')
- **Hervorhebung** wie Kursivschrift im Deutschen — wenn ein Wort betont werden soll

> **Wichtig:** Wenn du in einem japanischen Text ein Wort siehst, das nach **'ausländisch'** klingt, ist es fast sicher in Katakana geschrieben.

## Woher kommen die Zeichen?

Katakana entstand vor über 1'000 Jahren in der **Heian-Zeit** (9. Jahrhundert). Buddhistische Mönche in Nara brauchten eine schnelle Kurzschrift, um chinesische Texte mit japanischer Aussprache zu annotieren. Sie nahmen **Fragmente** von Kanji-Zeichen — daher der Name *kata-kana* (片仮名), wörtlich **"Bruchstück-Schrift"**. Beispiel: 「カ」 (ka) ist die linke Hälfte von 加 (ka, 'hinzufügen'). Du musst die Herkunft nicht auswendig lernen, aber sie erklärt, warum Katakana **eckig und scharfkantig** wirkt — ganz im Gegensatz zur fliessenden, weichen Hiragana.

## Was lernst du in dieser Lektion?

Die ersten **drei Reihen** der Katakana-Tabelle, also **15 Zeichen**:

1. Die fünf **Vokale**: 「アイウエオ」 (a, i, u, e, o)
2. Die **K-Reihe**: 「カキクケコ」 (ka, ki, ku, ke, ko)
3. Die **S-Reihe**: 「サシスセソ」 (sa, shi, su, se, so)

## Hiragana vs. Katakana — gleicher Klang, andere Form

Dieselben Silben gibt es in beiden Schriften:

- 「あ」 (Hiragana a) ↔ 「ア」 (Katakana a)
- 「か」 (Hiragana ka) ↔ 「カ」 (Katakana ka)
- 「し」 (Hiragana shi) ↔ 「シ」 (Katakana shi)

> **Charakteristisch:** Katakana wirkt **eckig** und **scharfkantig**, Hiragana **rund** und **fliessend**. Das ist der schnellste Weg, sie auf einen Blick zu unterscheiden.

**Tipp:** Sprich jedes Zeichen **laut aus**, während du es ansiehst. Auf den Karten findest du zusätzlich **Mini-Eselsbrücken** und die genaue Strichfolge.$TEXT$
WHERE id = 6367 AND lesson_id = 151;

-- Page 2, Block 1 (id=6368): Vokale
UPDATE lesson_content SET content_text = $TEXT$## Vokale — die Basis

Die fünf Vokale sind die **wichtigsten Zeichen überhaupt**, weil jede weitere Reihe auf ihnen aufbaut. Sie klingen **exakt** wie ihre Hiragana-Gegenstücke — nur die Form ist neu.

- **ア (a)** wie in *Wasser*, *Vater* — ein offenes, kurzes "a"
- **イ (i)** wie in *bitte*, *Liebe* — ein kurzes "i"
- **ウ (u)** ⚠ — wie in *Mutter*, aber **ohne die Lippen zu runden**. Das japanische "u" ist gerade, fast wie ein eingeatmetes "ü" ohne Spitzmund. Nicht wie das deutsche "u" in *Buch* (zu rund).
- **エ (e)** wie in *Bett*, *Heft* — ein klares, kurzes "e"
- **オ (o)** wie in *Onkel*, *Opa* — ein kurzes "o", **nicht** so lang wie in *Boot*

> **Eselsbrücken zum Merken:**
> - 「ア」 sieht aus wie ein **gespiegeltes "A"** mit Knick — der Querstrich ist noch da
> - 「イ」 ist ein **stehender Adler** auf dem Boden (wie der englische *eagle*)
> - 「ウ」 ähnelt **stark** der Hiragana 「う」 — gleicher Klang, gleiche Grundform, nur eckiger
> - 「エ」 ist ein **Träger**, wie ihn ein Ingenieur (engl. *engineer*) im Bau nutzt
> - 「オ」 ist ein **Opernsänger**, der den Mund weit zum "O" formt

> **Mini-Übung:** Sag 「アイウエオ」 (a-i-u-e-o) mehrmals hintereinander. Diese Reihenfolge wirst du **überall** in der Tabelle wiederfinden.$TEXT$
WHERE id = 6368 AND lesson_id = 151;

-- Page 2, Block 7 (id=6374): K-Reihe
UPDATE lesson_content SET content_text = $TEXT$## K-Reihe — Konsonant K + Vokal

Die K-Reihe folgt dem **Bauplan: K + Vokal**. Du erkennst die fünf Vokal-Endungen wieder. Der K-Laut ist immer **klar und stimmlos**, nie weich wie ein "g".

- **カ (ka)** wie in *Karte*
- **キ (ki)** wie in *Kiste* — klingt wie das englische Wort *key*
- **ク (ku)** wie in *Kuss* (kurz, mit unrundiertem u — also kein deutsches "Kuh")
- **ケ (ke)** wie in *Kette*
- **コ (ko)** wie in *Korb*

> **Eselsbrücken:**
> - 「カ」 ähnelt **stark** der Hiragana 「か」 — gleicher Klang, derselbe Grundbauplan
> - 「キ」 sieht aus wie ein **seltsamer Schlüssel** — englisch *key* (ki!)
> - 「ク」 ist eine lange, schräge **Kochmütze** (engl. *cook* → ku)
> - 「ケ」 sieht aus wie der **Buchstabe K** — direkt zum Merken
> - 「コ」 sind **zwei rechte Winkel** gegenüber — wie ein offenes Tor

> **Verwechslungsgefahr:** 「カ」 (ka) und 「ク」 (ku) sind ähnlich. **Ka** hat oben einen kleinen Extra-Strich, **ku** läuft glatt durch. Mehr dazu auf der nächsten Seite.

**Mini-Wörter:** 「カメラ」 (kamera, 'Kamera'), 「ケーキ」 (kēki, 'Kuchen'), 「コーラ」 (kōra, 'Cola'), 「カキ」 (kaki, 'Auster' — ja, mit Katakana, weil Tierart).$TEXT$
WHERE id = 6374 AND lesson_id = 151;

-- Page 2, Block 13 (id=6380): S-Reihe
UPDATE lesson_content SET content_text = $TEXT$## S-Reihe — mit derselben Ausnahme wie Hiragana

Die S-Reihe folgt dem Muster **S + Vokal** — **mit derselben Ausnahme wie bei Hiragana**. Das "s" ist immer **stimmlos** wie im Englischen *snake*, nie weich wie das deutsche "Sonne".

- **サ (sa)** wie in *Sand* — stimmloses s
- **シ (shi)** ⚠ — nicht 'si', sondern **'schi'**, wie in *Schiene*. **Wichtigste Eigenheit der ganzen Tabelle.**
- **ス (su)** — stimmloses s + unrundiertes u. **In manchen Wörtern wird das u fast verschluckt** (siehe nächste Seite zum Thema "Vokal-Entstummung")
- **セ (se)** wie in *Seele*, *Sektor* — kurz und stimmlos
- **ソ (so)** wie in *Sonntag* (mit stimmlosem s)

> **Eselsbrücken:**
> - 「サ」 sind **zwei Fische auf einem Spiess** — *Sardine* und *Salmon*
> - 「シ」 ist ein **Smiley auf der Seite** mit zwei gestapelten Augen ("schi" mit Lächeln)
> - 「ス」 ist **Supermans schwebender Anzug** — der "S"-Anzug, abgelegt
> - 「セ」 ähnelt **stark** der Hiragana 「せ」 — wieder gleiche Grundform
> - 「ソ」 sind **Nadel und Faden** zum *Sewing* (Nähen): "so"

> **⚠ Achtung — die berüchtigten Verwechslungspaare:**
> - 「シ」 (shi) und 「ツ」 (tsu, kommt in Katakana 2) — **Strichrichtung**: シ ist eher **vertikal** ausgerichtet (Striche gehen nach **rechts oben** zum Hauptstrich), ツ ist eher **horizontal** (Striche gehen nach **unten** zum Hauptstrich).
> - 「ソ」 (so) und 「ン」 (n, kommt in Katakana 3) — **Strichwinkel**: ソ läuft **steil von oben nach unten rechts** ("so" geht **runter**), ン läuft **flach von oben nach unten** ("n" geht **hoch**).

**Mini-Wörter:** 「サラダ」 (sarada, 'Salat'), 「スシ」 (sushi), 「セット」 (setto, 'Set'), 「ソース」 (sōsu, 'Soße').$TEXT$
WHERE id = 6380 AND lesson_id = 151;

-- Page 3, Block 1 (id=6386): Aussprache & Schreibhinweise
UPDATE lesson_content SET content_text = $TEXT$## Aussprache — die wichtigsten Regeln

**Wichtig vorab:** Katakana **klingt genauso** wie Hiragana. Jede Katakana-Silbe hat eine exakte Hiragana-Entsprechung. Es gibt **keine** zusätzlichen Klänge — nur andere Formen.

**Vokale sind kurz und gleichlang.** 「ア」 (a) wird kurz gesprochen, nicht 'aaaa'. Lange Vokale haben eine **eigene Schreibweise** — den Längungsstrich (siehe unten).

**Stimmlose Konsonanten.** Das **s** in 「サ」 (sa), 「ス」 (su), 「セ」 (se), 「ソ」 (so) ist immer **stimmlos** wie im englischen *snake* — nie weich wie im deutschen *Sonne*.

**Die Ausnahme 「シ」 (shi).** Statt 'si' sprichst du **'schi'**. Diese unregelmässige Stelle gibt es in fast jeder Reihe — präge sie dir aktiv ein.

**Japanisches "u" ist nicht wie deutsches "u".** Die Lippen bleiben **flach**, nicht gerundet. Es klingt eher wie ein eingeatmetes "ü" ohne Spitzmund.

## Vokal-Entstummung — warum manche Vokale verschwinden

Eine wichtige Regel, die auch in Katakana-Wörtern auftaucht:

**Die Vokale "u" und "i" werden oft fast lautlos**, wenn sie zwischen zwei stimmlosen Konsonanten stehen oder am Wortende nach einem stimmlosen Konsonanten kommen. Das nennt man **Entstummung** (engl. *devoicing*).

- 「スキ」 (suki, 'Ski') klingt fast wie **"ski"** — das u zwischen s und k wird hauchig
- 「キス」 (kisu, 'Kuss') klingt wie **"kis"** — das u am Ende verschluckt
- 「クス」 (kusu, 'Kichern') klingt wie **"k'su"** — das erste u kaum hörbar

Die Mundform für den Vokal bleibt — aber die Stimme setzt nicht ein. Das ist **kein Faulheits-Effekt**, sondern Standard im Tokyo-Japanisch und gilt auch für JLPT-Hörverstehen.

> **Faustregel:** Wenn du 「ス」 oder 「シ」 zwischen *k, s, sh, t, ts, ch, p, h* hörst — oder am Wortende nach diesen Lauten — dann wird der Vokal oft fast stumm.

## Der Längungsstrich 「ー」

Katakana kennt eine Eigenheit, die Hiragana **nicht** hat: den **Längungsstrich** 「ー」 (chōonpu, ein einfacher waagerechter Strich). Er **verlängert den vorherigen Vokal** auf das Doppelte — eine zweite Mora, ohne ein neues Zeichen schreiben zu müssen.

- 「コーヒー」 (kōhī, 'Kaffee') — das 「ー」 verlängert das o **und** das i
- 「ケーキ」 (kēki, 'Kuchen') — verlängert das e
- 「カレー」 (karē, 'Curry') — verlängert das e am Ende
- 「コーラ」 (kōra, 'Cola') — verlängert das o

> **Merke:** In Lehnwörtern siehst du 「ー」 sehr oft, weil viele Fremdwörter lange Vokale haben (engl. *coffee* → kōhī, dt. *Kuchen* → kēki).

## Verwechslungsgefahr — die Katakana-Klassiker

Katakana hat **vier berüchtigte Verwechslungspaare**, die du am ersten Tag bewusst angehen solltest:

- **「シ」 (shi) vs. 「ツ」 (tsu, in K2)** — Strichrichtung: シ ist **vertikal** orientiert (Striche zeigen Richtung **rechts oben**), ツ ist **horizontal** (Striche zeigen nach **unten**).
- **「ソ」 (so) vs. 「ン」 (n, in K3)** — Strichwinkel: ソ läuft **steil nach unten** (von oben nach unten rechts), ン läuft **flach nach oben** (von oben nach unten links).
- **「カ」 (ka) vs. 「ク」 (ku)** — ka hat einen **zusätzlichen kurzen Strich** oben, ku läuft glatt durch.
- **「コ」 (ko) vs. 「ユ」 (yu, in K3)** — ko hat oben **und** unten einen Querstrich, yu hat den Querstrich nur **unten**.

> **Tipp:** Wenn du dir bei einem Zeichen nicht sicher bist, **schreib es mit dem Finger in die Luft**. Die Strich-Richtung wird klarer, wenn du die Bewegung nachfühlst.

## Strichfolge — kurz erklärt

Jedes Katakana-Zeichen hat eine **festgelegte Strichfolge**. Faustregel: **von oben nach unten**, **von links nach rechts**. Katakana hat tendenziell **weniger und geradere Striche** als Hiragana — das macht das Schreiben tatsächlich einfacher. Auf jeder Karte findest du die genaue Schritt-für-Schritt-Anleitung.$TEXT$
WHERE id = 6386 AND lesson_id = 151;

-- Page 4, Block 1 (id=6387): Quiz-Vorlauf
UPDATE lesson_content SET content_text = $TEXT$## Teste dein Wissen

Gleich kommen **Fragen** zu den 15 Katakana, die du gerade gelernt hast.

- **Multiple-Choice:** Welche Romaji-Lesung passt zum Zeichen?
- **Richtig/Falsch:** Stimmt die angegebene Lesung?
- **Wort-Lesung:** Welches Lehnwort siehst du?
- **Matching:** Verbinde Zeichen mit Lesung

> **Tipp:** Achte besonders auf die Verwechslungspaare 「シ」 (shi) vs. 「ツ」 (tsu) und 「カ」 (ka) vs. 「ク」 (ku) — und vergiss den Längungsstrich 「ー」 nicht.$TEXT$
WHERE id = 6387 AND lesson_id = 151;

-- Page 5, Block 1 (id=6388): Zusammenfassung
UPDATE lesson_content SET content_text = $TEXT$## Geschafft — die ersten 15 Katakana

Du hast in dieser Lektion gelernt:

- Die **fünf Vokale** 「アイウエオ」 (a, i, u, e, o)
- Die **K-Reihe** 「カキクケコ」 (ka, ki, ku, ke, ko)
- Die **S-Reihe** 「サシスセソ」 (sa, shi, su, se, so)
- **Wofür** Katakana genutzt wird (Lehnwörter, Eigennamen, Onomatopöie, Hervorhebung)
- Den **Längungsstrich** 「ー」 (verlängert den vorherigen Vokal — Katakana-spezifisch)
- Die wichtigste **Ausnahme**: 「シ」 (shi statt si)
- Dass das **japanische "u"** unrundiert ist und manchmal fast verschluckt wird (Entstummung)
- Die ersten Verwechslungspaare (シ/ツ, ソ/ン, カ/ク, コ/ユ)

## Lehnwörter, die du jetzt lesen kannst

Mit deinen 15 Katakana liest du schon eine Reihe echter Lehnwörter:

- 「アイス」 (aisu) — Eis
- 「カメラ」 (kamera) — Kamera
- 「ケーキ」 (kēki) — Kuchen
- 「コーラ」 (kōra) — Cola
- 「サラダ」 (sarada) — Salat
- 「スキー」 (sukī) — Ski (mit Längungsstrich!)
- 「スシ」 (sushi) — Sushi
- 「セット」 (setto) — Set
- 「ソース」 (sōsu) — Soße
- 「カキ」 (kaki) — Auster

> **Probier es:** Lies jedes Wort **laut**, ohne auf die Romaji zu schauen. Wenn du den Ursprung erkennst (englisch, deutsch, französisch), sitzt das Lesen.

## Lerntipps für die nächsten Tage

1. **Schreibe jeden Tag** alle 15 Zeichen einmal mit der Hand — fünf Minuten reichen, mit korrekter Strichfolge
2. **Lies Lehnwörter laut** — Speisekarten und Werbung sind ideale Übungstexte
3. **Wiederhole das Quiz**, bis du alle Fragen ohne Hilfe schaffst
4. **Achte auf die Verwechslungspaare** — Strich-Richtung und -Winkel sind der Schlüssel
5. **Hör beim Sprechen auf Entstummung** — 「スキ」 klingt wie "ski", nicht "su-ki"

## Was kommt als Nächstes?

- **Katakana 2** — die T-Reihe 「タチツテト」, N-Reihe 「ナニヌネノ」 und H-Reihe 「ハヒフヘホ」 (15 weitere Zeichen, inkl. der gefürchteten Paare ツ/シ und ソ/ン!)
- Danach Katakana 3 (M/Y/R/W + ン), Katakana 4 (Diakritika + Längungsstrich vertieft) und Katakana 5 (Yōon + Lehnwort-Spezialitäten wie ティ, ファ, ヴ)

Wenn du Katakana komplett kannst, kannst du **jeden** japanischen Text mit Hiragana + Katakana lesen — das deckt einen Grossteil des N5-Materials ab.$TEXT$
WHERE id = 6388 AND lesson_id = 151;

-- =====================================================
-- TEIL B: Strichfolge (15 Updates auf kana.stroke_order_info)
-- Quellen: Wiktionary EN (Strichanzahl pro Zeichen verifiziert), Tofugu, Wikipedia
-- =====================================================

-- Vokale (aus 阿, 伊, 宇, 江, 於 vereinfacht)
UPDATE kana SET stroke_order_info='2 Striche: 1) kurzer waagerechter Strich oben, leicht nach rechts unten; 2) langer geschwungener Strich von oben rechts nach unten links, kreuzt Strich 1' WHERE id=105;
UPDATE kana SET stroke_order_info='2 Striche: 1) kurzer diagonaler Strich von oben links nach unten rechts; 2) langer senkrechter Strich rechts daneben (von oben nach unten) — wie ein stehender Adler' WHERE id=106;
UPDATE kana SET stroke_order_info='3 Striche: 1) kurzer senkrechter Strich oben Mitte; 2) waagerechter Strich darunter; 3) langer senkrechter Strich rechts mit kleinem Haken nach links unten' WHERE id=107;
UPDATE kana SET stroke_order_info='3 Striche: 1) waagerechter Strich oben; 2) senkrechter Strich in der Mitte; 3) langer waagerechter Strich unten — wie ein Träger im Bau (engineer)' WHERE id=108;
UPDATE kana SET stroke_order_info='3 Striche: 1) waagerechter Strich oben; 2) langer senkrechter Strich (kreuzt Strich 1) mit Haken unten links; 3) kurzer diagonaler Strich oben links nach unten rechts' WHERE id=109;

-- K-Reihe (aus 加, 幾, 久, 介, 己 vereinfacht)
UPDATE kana SET stroke_order_info='2 Striche: 1) waagerechter Strich, der nach rechts in einen langen geschwungenen Bogen übergeht; 2) kurzer diagonaler Strich von oben rechts nach unten links, kreuzt Strich 1 — ähnlich der Hiragana か' WHERE id=110;
UPDATE kana SET stroke_order_info='3 Striche: 1) kurzer diagonaler Strich oben rechts nach links unten; 2) waagerechter Strich darunter; 3) langer senkrechter Strich durch Striche 1 und 2 — sieht aus wie ein seltsamer Schlüssel (key)' WHERE id=111;
UPDATE kana SET stroke_order_info='2 Striche: 1) kurzer diagonaler Strich von oben links nach rechts; 2) langer geschwungener Strich von oben rechts nach unten links — wie eine lange Kochmütze' WHERE id=112;
UPDATE kana SET stroke_order_info='3 Striche: 1) kurzer Strich oben (von links unten nach rechts oben); 2) langer geschwungener Strich oben nach unten rechts, kreuzt Strich 1; 3) kurzer diagonaler Strich rechts unten — wie ein lateinisches K' WHERE id=113;
UPDATE kana SET stroke_order_info='2 Striche: 1) kurzer waagerechter Strich oben; 2) waagerechter Strich darunter, der rechts in einen langen senkrechten Strich übergeht — zwei rechte Winkel wie ein offenes Tor' WHERE id=114;

-- S-Reihe (aus 散, 之, 須, 世, 曽 vereinfacht)
UPDATE kana SET stroke_order_info='3 Striche: 1) kurzer waagerechter Strich oben; 2) zweiter waagerechter Strich darunter (etwas länger); 3) langer senkrechter Strich kreuzt beide Querstriche und biegt nach links — wie zwei Fische auf einem Spiess' WHERE id=115;
UPDATE kana SET stroke_order_info='3 Striche: 1) kurzer Strich oben links; 2) zweiter kurzer Strich darunter; 3) langer geschwungener Strich von unten links nach oben rechts. WICHTIG: Striche zeigen RECHTS OBEN — Verwechslung mit ツ (tsu) vermeiden!' WHERE id=116;
UPDATE kana SET stroke_order_info='2 Striche: 1) kurzer Strich oben, der nach rechts unten in einen Diagonalstrich übergeht; 2) langer geschwungener Strich von oben rechts nach unten links, kreuzt Strich 1 — wie Supermans schwebender Anzug' WHERE id=117;
UPDATE kana SET stroke_order_info='2 Striche: 1) langer waagerechter Strich oben mit kurzem senkrechtem Strich nach unten rechts; 2) langer senkrechter Strich kreuzt Strich 1 und biegt unten nach links — ähnlich der Hiragana せ' WHERE id=118;
UPDATE kana SET stroke_order_info='2 Striche: 1) kurzer Strich oben (von links unten nach rechts oben); 2) langer geschwungener Strich oben nach unten rechts (STEILER Winkel). WICHTIG: Verwechslung mit ン (n, flacher Winkel) vermeiden!' WHERE id=119;

-- Validierung Strichfolge
SELECT id, character, romanization, LEFT(stroke_order_info, 70) AS preview
FROM kana
WHERE id BETWEEN 105 AND 119
ORDER BY id;

-- Validierung Texte
SELECT id, page_number, order_index, LEFT(content_text, 60) AS preview, length(content_text) AS chars
FROM lesson_content
WHERE lesson_id = 151 AND content_type = 'text'
ORDER BY page_number, order_index;

COMMIT;
