-- Refine N5 Hiragana 2 (Lesson ID 147) — Text-Inhalte + Stroke-Order
-- Erwartete Zeilen pro UPDATE: 1
-- Recherche: Tofugu, Wikipedia (Hiragana, Japanese phonology), Migaku, Web-Search
-- Datum: 2026-05-02
SET client_encoding = 'UTF8';

BEGIN;

-- =====================================================
-- Stroke-Order fuer T-, N-, H-Reihe (kana IDs 16-30)
-- Standard-Strichzahlen (Schreibschule), nicht Tofugu-Variante
-- =====================================================

UPDATE kana SET stroke_order_info='4 Striche: 1) waagerechter Strich oben; 2) diagonaler Strich von oben rechts nach unten links (kreuzt Strich 1); 3) kurzer waagerechter Strich rechts in der Mitte; 4) geschwungener Haken unten' WHERE id=16;
UPDATE kana SET stroke_order_info='2 Striche: 1) kurzer waagerechter Strich oben; 2) langer geschwungener Bogen darunter (links → unten → rechts), aehnlich einer gespiegelten 「さ」' WHERE id=17;
UPDATE kana SET stroke_order_info='1 Strich: ein einziger flacher Bogen von links nach rechts unten — wie eine kleine Welle ohne Haken' WHERE id=18;
UPDATE kana SET stroke_order_info='1 Strich: ein einziger geschwungener Strich von oben rechts nach unten und am Ende leicht nach links zurueck' WHERE id=19;
UPDATE kana SET stroke_order_info='2 Striche: 1) kurzer senkrechter Strich oben links; 2) langer geschwungener Strich rechts daneben (oben → unten)' WHERE id=20;
UPDATE kana SET stroke_order_info='4 Striche: 1) waagerechter Strich oben; 2) langer senkrechter Strich (kreuzt Strich 1); 3) diagonaler Strich von oben rechts nach unten links; 4) kleine Schleife unten rechts' WHERE id=21;
UPDATE kana SET stroke_order_info='3 Striche: 1) langer senkrechter Strich links; 2) kurzer waagerechter Strich rechts oben; 3) kurzer waagerechter Strich rechts unten' WHERE id=22;
UPDATE kana SET stroke_order_info='2 Striche: 1) kurzer waagerechter Strich; 2) langer Strich nach unten mit grosser Schleife (geht durch Strich 1) — sehr aehnlich め und ね, ぬ ist die "glatte" Variante' WHERE id=23;
UPDATE kana SET stroke_order_info='2 Striche: 1) kurzer senkrechter Strich; 2) langer Strich, der unten in eine Schleife laeuft mit kleinem Anhaengsel rechts (der "Schwanz" unterscheidet ね von ぬ, れ und わ)' WHERE id=24;
UPDATE kana SET stroke_order_info='1 Strich: ein einziger geschwungener Strich, der eine geschlossene Schleife bildet (wie eine "9", die im Uhrzeigersinn endet)' WHERE id=25;
UPDATE kana SET stroke_order_info='3 Striche: 1) senkrechter Strich links; 2) waagerechter Strich oben rechts; 3) senkrechter Strich rechts mit Schleife unten — sehr aehnlich ほ (ho), aber は hat oben nur EINEN Strich' WHERE id=26;
UPDATE kana SET stroke_order_info='1 Strich: ein einziger schwingender Strich (oben links → bauchig nach unten → kleines Haekchen rechts)' WHERE id=27;
UPDATE kana SET stroke_order_info='4 Striche: 1) kurzer waagerechter Strich oben; 2) senkrechter Strich; 3) kurzer Strich links unten; 4) kurzer Strich rechts unten — der einzige Hiragana, der aus 4 isolierten Teilen besteht' WHERE id=28;
UPDATE kana SET stroke_order_info='1 Strich: ein einziger Knick (sanft ansteigend nach rechts oben → flacher Bogen nach unten rechts) — sieht aus wie ein flaches Dach' WHERE id=29;
UPDATE kana SET stroke_order_info='4 Striche: 1) senkrechter Strich links; 2) waagerechter Strich oben (kuerzer als bei は!); 3) zweiter waagerechter Strich darunter; 4) senkrechter Strich rechts mit Schleife unten — der ZWEITE Querstrich oben unterscheidet ほ von は' WHERE id=30;

-- =====================================================
-- Text-Bloecke ueberarbeiten
-- =====================================================

-- Page 1, Block 1 (id=6246): Einfuehrung
UPDATE lesson_content SET content_text = $TEXT$## Wo stehst du jetzt?

In **Hiragana 1** hast du bereits 15 Zeichen gelernt: die fünf Vokale 「あいうえお」 (a, i, u, e, o), die K-Reihe 「かきくけこ」 (ka, ki, ku, ke, ko) und die S-Reihe 「さしすせそ」 (sa, shi, su, se, so).

## Was lernst du jetzt?

In dieser Lektion folgen die **nächsten drei Reihen** — also weitere **15 Zeichen**:

1. Die **T-Reihe**: 「たちつてと」 (ta, chi, tsu, te, to)
2. Die **N-Reihe**: 「なにぬねの」 (na, ni, nu, ne, no)
3. Die **H-Reihe**: 「はひふへほ」 (ha, hi, fu, he, ho)

> **Achtung — drei Stolperfallen:** Die T-Reihe enthält 「ち」 (chi statt ti) und 「つ」 (tsu statt tu). Die H-Reihe enthält 「ふ」 (fu statt hu, mit einer ungewöhnlichen Aussprache). Wir gehen die Ausnahmen gleich Schritt für Schritt durch.

## Zwei besondere Hinweise

**1.** 「は」 (ha) hat eine **versteckte Doppelrolle**: als Bestandteil von Wörtern wird es ganz normal "ha" gelesen — aber wenn es als **Partikel** im Satz steht (Themen-Markierung), wird es "wa" gesprochen. Du wirst das später detailliert lernen — merk dir nur: das **Zeichen ist immer は**, die Lautung kann variieren.

**2.** Auch in dieser Lektion gilt die **Vokal-Entstummung** aus Hiragana 1: das "i" und "u" zwischen stimmlosen Konsonanten wird oft fast lautlos. Beispiel: 「ひと」 (hito, "Mensch") klingt wie "h'to". Das ist normal — keine Sorge.

## Was kannst du danach lesen?

Mit deinen bisherigen 15 + diesen 15 = **30 Zeichen** liest du schon Hunderte japanische Wörter, zum Beispiel 「ねこ」 (neko, 'Katze'), 「はな」 (hana, 'Blume') oder 「あなた」 (anata, 'du').

**Tipp:** Sprich jedes neue Zeichen **mehrmals laut aus**, während du es ansiehst. So verknüpfst du Form und Klang im Gedächtnis.$TEXT$
WHERE id = 6246 AND lesson_id = 147;

-- Page 2, Block 1 (id=6247): T-Reihe
UPDATE lesson_content SET content_text = $TEXT$## T-Reihe — mit zwei Ausnahmen

Die T-Reihe folgt dem Muster **T + Vokal**, hat aber **zwei wichtige Ausnahmen**:

- **た (ta)** wie in *Tasche*
- **ち (chi)** ⚠ — nicht 'ti', sondern **'tschi'** wie in *Tschüss*. Die Zungenmitte berührt den Gaumen.
- **つ (tsu)** ⚠ — nicht 'tu', sondern **'tsu'** wie das **ts** in *Katze*. Es ist EIN Laut, kein "t-u".
- **て (te)** wie in *Teller* (kurz, nicht gedehnt wie *Tee*)
- **と (to)** wie in *Tor* (kurz)

> **Phonetik-Hintergrund:** Die Ausnahmen sind keine Willkür — sie entstehen durch die Verschmelzung mit dem nachfolgenden Vokal (Palatalisierung). Vor /i/ wird "t" zu "tsch", vor /u/ wird "t" zu "ts". Das passiert in vielen Sprachen automatisch.

> **Eselsbrücken (Tofugu-Stil):**
> - 「た」 sieht aus wie eine **Gabel** mit einer Limette daneben — Zutaten für einen **Taco**
> - 「ち」 ist ein **gezwungenes Lächeln** beim Foto-Cheese ("tschiise")
> - 「つ」 ist eine **Tsunami-Welle** — ein flacher Bogen
> - 「て」 ist ein **kleines Teleskop**, das du in der Hand (te = japanisch für Hand) hältst
> - 「と」 ist eine **Zehe** mit einem Splitter (toe)

> **Mini-Wörter:** 「たて」 (tate, 'senkrecht'), 「ちち」 (chichi, 'Vater'), 「つき」 (tsuki, 'Mond'), 「て」 (te, 'Hand'), 「とけい」 (tokei, 'Uhr').$TEXT$
WHERE id = 6247 AND lesson_id = 147;

-- Page 2, Block 2 (id=6253): N-Reihe
UPDATE lesson_content SET content_text = $TEXT$## N-Reihe — keine Ausnahmen

Die N-Reihe ist **angenehm regelmässig**. Alle fünf Zeichen folgen dem Muster **N + Vokal**:

- **な (na)** wie in *Name*
- **に (ni)** wie in *nie*
- **ぬ (nu)** wie in *Nudel* (kurz, mit unrundiertem u)
- **ね (ne)** wie in *Nest*
- **の (no)** wie in *Note* (kurz, nicht gedehnt)

> **Gute Nachricht:** Wenn du die fünf Vokale beherrschst, kannst du die N-Reihe sofort. Keine Stolperfallen.

> **Eselsbrücken (Tofugu-Stil):**
> - 「な」 ist eine **Nonne**, die vor einem Kreuz betet und an Nachos denkt
> - 「に」 ist eine **Nadel**, die einen Faden zieht
> - 「ぬ」 sind glatte **Nudeln** mit einer extra Schleife unten — komplett rund, keine scharfen Ecken
> - 「ね」 ist die Katze **Nelly** mit Schwanzschleife — hat scharfe Ecken (Unterschied zu ぬ!)
> - 「の」 ist ein **Schweinerüssel** oder ein "no smoking"-Zeichen — eine einzige geschlossene Schleife

> **Etymologie-Hinweis:** 「ぬ」 (nu) und das spätere 「め」 (me) stammen beide vom Kanji **女** (Frau) — deshalb sehen sie sich so ähnlich. Merke dir: ぬ hat den **extra Schwung unten**.

> **Mini-Wörter:** 「なに」 (nani, 'was?'), 「ねこ」 (neko, 'Katze'), 「いぬ」 (inu, 'Hund'), 「のむ」 (nomu, 'trinken'), 「に」 (ni, Partikel "in/zu").$TEXT$
WHERE id = 6253 AND lesson_id = 147;

-- Page 2, Block 3 (id=6259): H-Reihe
UPDATE lesson_content SET content_text = $TEXT$## H-Reihe — mit einer Ausnahme

Die H-Reihe folgt dem Muster **H + Vokal**, mit **einer wichtigen Ausnahme**:

- **は (ha)** wie in *Hase* (siehe Sonderregel zur Partikel-Aussprache am Ende!)
- **ひ (hi)** wie in *Hilfe*
- **ふ (fu)** ⚠ — **kein deutsches f!** Es ist ein **bilabiales** Geräusch: beide Lippen kommen sich nahe (wie beim Pusten einer Kerze), aber NICHT die Lippe+Zähne wie bei deutschem "f". Klangbild: zwischen "fu" und "hu", ganz weich.
- **へ (he)** wie in *Held* (kurz)
- **ほ (ho)** wie in *hoch* (kurz)

> **Phonetik-Detail zu 「ふ」:** Wenn du "Pf" beim Pusten einer Kerze sagst, aber den "P"-Anteil weglässt — DAS ist der ふ-Laut. Übe es mit ausgestrecktem Handrücken vor dem Mund: bei deutschem "f" spürst du keinen Luftstrom auf der Hand, bei japanischem "fu" einen sanften Hauch.

> **は als Partikel = "wa":** Wenn 「は」 nach einem Wort als **Themenmarker** steht (z.B. 「わたしは…」 watashi wa, "ich..."), wird es **"wa"** gesprochen. In normalen Wörtern (z.B. 「はな」 hana, 'Blume') bleibt es "ha". Diese Ausnahme stammt aus historischer Schreibung — du wirst sie ab den ersten Vokabel-Lektionen täglich hören.

> **Eselsbrücken:**
> - 「は」 = grosses **H** + kleines **a** = "Ha!"
> - 「ひ」 ist **er mit grosser Nase** (he has a big nose)
> - 「ふ」 ist ein **Tanzender** mit Hula-Hoop (fool with a hula hoop)
> - 「へ」 ist der **Berg St. Helens** (kleiner Vulkan)
> - 「ほ」 hat **vier Arme** wie ein chaotischer Weihnachtsmann (ho-ho-ho)

> **Mini-Wörter:** 「はな」 (hana, 'Blume'), 「ひと」 (hito, 'Person' — hier wird das **i** entstummt!), 「ふね」 (fune, 'Boot'), 「へた」 (heta, 'ungeschickt'), 「ほし」 (hoshi, 'Stern').

## Wörter, die du nun lesen kannst

Mit Hiragana 1 + 2 (= 30 Zeichen) liest du schon viele echte japanische Wörter:

- 「たかい」 (takai) — hoch, teuer
- 「ちいさい」 (chiisai) — klein
- 「つき」 (tsuki) — Mond
- 「ねこ」 (neko) — Katze
- 「いぬ」 (inu) — Hund
- 「はな」 (hana) — Blume
- 「ふね」 (fune) — Boot
- 「ほし」 (hoshi) — Stern
- 「ひと」 (hito) — Person/Mensch
- 「あなた」 (anata) — du$TEXT$
WHERE id = 6259 AND lesson_id = 147;

-- Page 3, Block 1 (id=6265): Aussprache & Schreibhinweise
UPDATE lesson_content SET content_text = $TEXT$## Die drei wichtigsten Ausnahmen

In diesen 15 Zeichen stecken **drei Aussprache-Ausnahmen**, die du dir aktiv einprägen musst:

1. **「ち」 (chi)** — nicht 'ti', sondern **'tschi'** wie in *Tschüss*
2. **「つ」 (tsu)** — nicht 'tu', sondern **'ts'** wie in *Katze*
3. **「ふ」 (fu)** — nicht 'hu' und kein deutsches f, sondern ein **bilabiales** Geräusch (beide Lippen, weicher Hauch)

> **Eselsbrücke:** Jede japanische Reihe hat **eine oder zwei Ausnahmen**. Wenn du sie früh erkennst, fallen sie dir nicht mehr auf — sie werden Teil deines Lesens.

## は als Partikel — die wichtigste Ausspracheregel

Das Zeichen 「は」 wird **"ha"** gelesen, **AUSSER** wenn es als **Themen-Partikel** im Satz steht — dann wird es **"wa"** gesprochen, obwohl es weiterhin als 「は」 geschrieben wird.

- 「はな」 (hana, 'Blume') → "**ha**na"
- 「わたしは」 (watashi wa, "ich [bin/mache/...]") → "watashi **wa**"

Du erkennst die Partikel-Rolle daran, dass 「は」 **nach einem Wort** steht (meist nach dem Subjekt). Diese Eigenheit hat **historische Gründe**: in der älteren Kana-Schreibung gab es noch andere wa-Schreibweisen, und 「は」 als Partikel ist ein Überbleibsel davon.

> **Du musst das jetzt nicht aktiv beherrschen.** Es reicht, dass du es **wiedererkennst**, sobald du die ersten Sätze liest. In den N5-Vokabel-Lektionen kommen wir ausführlich darauf zurück.

## Vokal-Entstummung — bleibt aktuell

Die Regel aus Hiragana 1 (entstummte u/i zwischen stimmlosen Konsonanten oder am Wortende) gilt auch hier — und betrifft **viele Wörter aus dieser Lektion**:

- 「ひと」 (hito) klingt wie **"h'to"** — das **i** zwischen "h" und "t" wird fast stumm
- 「した」 (shita, 'unten') klingt wie **"sh'ta"**
- 「ふた」 (futa, 'Deckel') klingt wie **"f'ta"**
- 「とけい」 (tokei, 'Uhr') — das **o** bleibt voll, weil es nicht zwischen stimmlosen Konsonanten steht

> **Faustregel:** Wenn du 「ひ」, 「ふ」, 「し」, 「す」 zwischen *k, s, sh, t, ts, ch, p, h* hörst — oder am Satzende nach diesen Lauten — dann wird der Vokal oft fast stumm.

## Verwechslungsgefahr — sehr ähnliche Zeichen

Diese Paare sehen sich auf den ersten Blick **fast gleich** aus. Schau genau hin:

- **「ね」 (ne) vs. 「れ」 (re) vs. 「わ」 (wa)** — alle drei haben einen senkrechten Strich links und einen Schwung rechts. Re und Wa lernst du erst später, aber merke dir: **ne hat einen Schwanz unten rechts** (kleine Schleife).
- **「ぬ」 (nu) vs. 「ね」 (ne)** — **ぬ ist 100% glatt** (keine scharfen Ecken), **ね hat scharfe Ecken** und den Schwanz.
- **「ぬ」 (nu) vs. 「め」 (me)** — me lernst du erst später; ぬ hat **eine Schleife mehr** unten. Hintergrund: beide stammen vom Kanji **女**.
- **「は」 (ha) vs. 「ほ」 (ho)** — ho hat **zwei Querstriche oben**, ha nur **einen**.
- **「ち」 (chi) vs. 「さ」 (sa)** — chi ist **gespiegelt zu sa**: der Bogen läuft unten in die andere Richtung.
- **「つ」 (tsu) vs. 「う」 (u)** — u hat einen kleinen Strich oben (Hut), tsu ist **eine reine Wellenlinie** ohne Hut.

> **Lerntipp:** Schreibe jedes neue Zeichen **mindestens fünfmal** mit der Hand. Die Hand merkt sich Form und Strichfolge besser als das Auge allein.

## Strichfolge — kurze Wiederholung

Wie in Hiragana 1 gilt: **von oben nach unten, von links nach rechts**. Die Strichanzahl variiert in dieser Lektion stark:

- **1 Strich:** 「つ」 (tsu), 「て」 (te), 「の」 (no), 「ひ」 (hi), 「へ」 (he)
- **2 Striche:** 「ち」 (chi), 「と」 (to), 「ぬ」 (nu), 「ね」 (ne)
- **3 Striche:** 「に」 (ni), 「は」 (ha)
- **4 Striche:** 「た」 (ta), 「な」 (na), 「ふ」 (fu), 「ほ」 (ho)

Detailangaben findest du auf jeder Hiragana-Karte (Karten umdrehen).

## Tipp zum Üben

Lies jeden Tag **drei einfache Wörter laut**, ohne auf die Romaji zu schauen. Schon nach einer Woche wirst du die Zeichen automatisch erkennen — versprochen.$TEXT$
WHERE id = 6265 AND lesson_id = 147;

-- Page 4, Block 1 (id=6266): Quiz-Vorlauf
UPDATE lesson_content SET content_text = $TEXT$## Teste dein Wissen

Gleich kommen **Fragen** zu den 15 neuen Hiragana, die du gerade gelernt hast.

- **Multiple-Choice:** Welche Romaji-Lesung passt zum Zeichen?
- **Richtig/Falsch:** Stimmt die angegebene Lesung?
- **Wort-Lesung & Bedeutung:** Welches Wort siehst du?
- **Matching:** Verbinde Zeichen mit Lesung

> **Tipp:** Konzentriere dich besonders auf die Ausnahmen 「ち」 (chi), 「つ」 (tsu) und 「ふ」 (fu) sowie die は-als-Partikel-Regel. Du kannst die Übung beliebig oft wiederholen.$TEXT$
WHERE id = 6266 AND lesson_id = 147;

-- Page 5, Block 1 (id=6267): Zusammenfassung
UPDATE lesson_content SET content_text = $TEXT$## Geschafft — 30 Hiragana insgesamt

Mit dieser Lektion kennst du nun:

- Aus **Hiragana 1**: Vokale + K-Reihe + S-Reihe (15 Zeichen)
- Aus **Hiragana 2**: T-Reihe + N-Reihe + H-Reihe (15 weitere Zeichen)
- **Insgesamt 30 von 46** Hiragana-Grundzeichen — fast zwei Drittel!

## Die wichtigsten Ausnahmen im Überblick

Diese **vier Stolperfallen** musst du dir besonders merken:

1. **「し」 (shi)** — nicht 'si' (aus Hiragana 1)
2. **「ち」 (chi)** — nicht 'ti'
3. **「つ」 (tsu)** — nicht 'tu' (= "ts" wie in *Katze*)
4. **「ふ」 (fu)** — bilabial, nicht wie deutsches "f"

> **Eselsbrücke:** Alle vier Ausnahmen liegen am **Anfang oder in der Mitte** der jeweiligen Reihe — nie am Ende.

Plus eine **Sonderregel**: 「は」 wird "wa" gesprochen, wenn es als **Themen-Partikel** im Satz steht.

Plus die **Vokal-Entstummung** aus Hiragana 1, die hier viele Wörter betrifft (ひと → "h'to", した → "sh'ta", ふた → "f'ta").

## Wörter, die du jetzt lesen kannst

Mit deinen 30 Zeichen liest du schon viele echte japanische Wörter:

- 「ねこ」 (neko) — Katze
- 「いぬ」 (inu) — Hund
- 「はな」 (hana) — Blume
- 「ふね」 (fune) — Boot
- 「ほし」 (hoshi) — Stern
- 「つき」 (tsuki) — Mond
- 「あなた」 (anata) — du
- 「なに」 (nani) — was?
- 「ちかい」 (chikai) — nah
- 「とけい」 (tokei) — Uhr
- 「ひと」 (hito) — Mensch (gesprochen "h'to")
- 「した」 (shita) — unten (gesprochen "sh'ta")
- 「ふた」 (futa) — Deckel (gesprochen "f'ta")
- 「て」 (te) — Hand
- 「ほん」 (hon) — Buch (kommt mit ん in Hiragana 3 dazu)

> **Probier es:** Lies jedes Wort **laut**, ohne auf die Romaji zu schauen. Schaffst du fünf hintereinander ohne Fehler, sitzt die Lektion.

## Lerntipps für die nächsten Tage

1. **Schreibe jeden Tag** alle 30 Zeichen einmal mit der Hand — zehn Minuten reichen
2. **Lies kurze Wörter laut**, nicht nur einzelne Zeichen
3. **Wiederhole das Quiz**, bis du alle Fragen ohne Hilfe schaffst
4. **Übe gezielt die vier Ausnahmen** (shi, chi, tsu, fu) — sie kommen in fast jedem japanischen Satz vor
5. **Achte beim Hören** auf entstummte Vokale — "h'to" statt "hi-to" ist normal

## Was kommt als Nächstes?

- **Hiragana 3** — die M-Reihe 「まみむめも」, Y-Reihe 「やゆよ」, R-Reihe 「らりるれろ」, W-Reihe 「わを」 und der Sonderling 「ん」
- Danach die **Diakritika** (が/ざ/だ/ば/ぱ) — kleine Striche, die einen Konsonanten weicher oder härter machen
- Und schliesslich die **Yōon** (きゃ/しゃ/…) — kombinierte Silben

Wenn du Hiragana komplett kannst, beginnst du mit den ersten **Vokabel-Lektionen** auf N5-Niveau.$TEXT$
WHERE id = 6267 AND lesson_id = 147;

-- Validierung
SELECT id, page_number, order_index, LEFT(content_text, 60) AS preview, length(content_text) AS chars
FROM lesson_content
WHERE lesson_id = 147 AND content_type = 'text'
ORDER BY page_number, order_index;

SELECT id, character, romanization, LEFT(stroke_order_info, 60) FROM kana WHERE id BETWEEN 16 AND 30 ORDER BY id;

COMMIT;
