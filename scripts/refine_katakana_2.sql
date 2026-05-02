-- Refine N5 Katakana 2 (Lesson ID 152) — Text-Inhalte + Strichfolge
-- T-Reihe (タチツテト), N-Reihe (ナニヌネノ), H-Reihe (ハヒフヘホ)
-- Recherche: 2026-05-02 (Tofugu, Wiktionary EN — Strichanzahl + Kanji-Herkunft pro Zeichen)
SET client_encoding = 'UTF8';

BEGIN;

-- =====================================================
-- TEIL A: Text-Bloecke (7 Updates)
-- =====================================================

-- Page 1, Block 1 (id=6389): Einfuehrung
UPDATE lesson_content SET content_text = $TEXT$## Wo stehst du jetzt?

In **Katakana 1** hast du die Vokale 「アイウエオ」 (a, i, u, e, o), die K-Reihe 「カキクケコ」 (ka, ki, ku, ke, ko) und die S-Reihe 「サシスセソ」 (sa, shi, su, se, so) gelernt — insgesamt 15 Zeichen.

## Was lernst du jetzt?

In dieser Lektion folgen die **nächsten drei Reihen** — also weitere **15 Zeichen**:

1. Die **T-Reihe**: 「タチツテト」 (ta, chi, tsu, te, to)
2. Die **N-Reihe**: 「ナニヌネノ」 (na, ni, nu, ne, no)
3. Die **H-Reihe**: 「ハヒフヘホ」 (ha, hi, fu, he, ho)

## Achtung — drei Ausnahmen und der berüchtigste Verwechslungsfall überhaupt

- **Drei Aussprache-Ausnahmen** (gleiche wie in Hiragana): 「チ」 (chi statt ti), 「ツ」 (tsu statt tu), 「フ」 (fu statt hu).
- **「シ」 (shi)** aus Katakana 1 vs. **「ツ」 (tsu)** aus dieser Lektion — die **berühmteste Verwechslungsfalle** der ganzen Katakana-Tabelle. Beide bestehen aus drei Strichen. Nur die **Strich-Richtung** entscheidet.
- Ein Bonus: **「ヘ」 (he)** sieht in Hiragana und Katakana **identisch** aus — eines der wenigen Zeichen, das du nicht doppelt lernen musst.

## Was kannst du danach lesen?

Mit Katakana 1 + 2 (= 30 Zeichen) liest du schon viele Lehnwörter:

- 「タクシー」 (takushī, 'Taxi')
- 「ノート」 (nōto, 'Notizbuch')
- 「ハム」 (hamu, 'Schinken')
- 「ホテル」 (hoteru, 'Hotel')
- 「テレビ」 (terebi, 'Fernseher')

> **Tipp:** Sprich jedes neue Zeichen **mehrmals laut**. Achte besonders auf シ und ツ — die Strich-Richtung entscheidet, nicht die Form.$TEXT$
WHERE id = 6389 AND lesson_id = 152;

-- Page 2, Block 1 (id=6390): T-Reihe
UPDATE lesson_content SET content_text = $TEXT$## T-Reihe — mit zwei Ausnahmen

Wie bei Hiragana folgt die T-Reihe dem Muster **T + Vokal**, mit **zwei Ausnahmen** in der Mitte. Das "t" ist klar und scharf, nie weich wie ein "d".

- **タ (ta)** wie in *Tasche*
- **チ (chi)** ⚠ — nicht 'ti', sondern **'tschi'**, wie in *Tschüss*
- **ツ (tsu)** ⚠ — nicht 'tu', sondern **'tsu'** — Zungenspitze klickt kurz an die Zähne (wie das "z" in *Zacke*)
- **テ (te)** wie in *Tee*
- **ト (to)** wie in *Tor*

> **Eselsbrücken (Tofugu-Stil):**
> - 「タ」 ist ein **Drachen** (Drachen heissen auf Japanisch *tako* — taco-Drachen!)
> - 「チ」 ist ein **Cheerleader**, der einen Cheer macht ("**chee**r")
> - 「ツ」 sind **zwei Nadeln und Faden** zum Nähen — *tsu* erinnert an das *t-su* beim Stechen
> - 「テ」 ist ein **Telefonmast** ("**te**lephone pole")
> - 「ト」 ist ein **Totempfahl**

> **⚠ Die berüchtigtste Verwechslungsfalle in ganz Katakana:** 「シ」 (shi, aus K1) und 「ツ」 (tsu) sehen sich **fast identisch** aus. Beide haben drei Striche. Schau auf die **Strich-Richtung**:
> - 「シ」 (shi) — Striche zeigen **schräg nach OBEN RECHTS** (zum Hauptstrich), Hauptstrich wird **von unten nach oben** gezogen
> - 「ツ」 (tsu) — Striche zeigen **schräg nach UNTEN** (vom Hauptstrich weg), Hauptstrich wird **von oben nach unten** gezogen

**Mini-Wörter:** 「タクシー」 (takushī, 'Taxi'), 「チケット」 (chiketto, 'Ticket'), 「テスト」 (tesuto, 'Test'), 「ツナ」 (tsuna, 'Thunfisch'), 「トイレ」 (toire, 'Toilette').$TEXT$
WHERE id = 6390 AND lesson_id = 152;

-- Page 2, Block 7 (id=6396): N-Reihe
UPDATE lesson_content SET content_text = $TEXT$## N-Reihe — angenehm regelmässig

Die N-Reihe folgt **N + Vokal** ohne jede Ausnahme. Atemholen — nach den T-Reihen-Stolpern ist das die einfachste Reihe der Lektion.

- **ナ (na)** wie in *Name*
- **ニ (ni)** wie in *nie*
- **ヌ (nu)** wie in *Nudel* (kurz, mit unrundiertem u)
- **ネ (ne)** wie in *Nest*
- **ノ (no)** wie in *Note* (kurz, nicht so lang wie *no* im Englischen)

> **Eselsbrücken (Tofugu-Stil):**
> - 「ナ」 ist ein **Narwal**, der majestätisch zur Oberfläche aufsteigt
> - 「ニ」 sind **zwei Nadeln nebeneinander** — schlicht und perfekt: 2 Striche für "ni"
> - 「ヌ」 sind **Stäbchen, die Nudeln** greifen ("**noo**dles")
> - 「ネ」 ist ein **Pferd, das über eine Hürde springt** und "**neigh**!" ruft
> - 「ノ」 ist eine **lange Nase** ("**no**se") — ein einziger Strich

> **Verwechslungsgefahr:** 「ヌ」 (nu) und 「ス」 (su, aus K1) sehen sich ähnlich. **Su** hat einen klaren waagerechten Strich oben mit Knick; **nu** hat einen kurzen diagonalen Strich oben — und der untere Strich ist **gerade durchgezogen**, ohne Knick.

**Mini-Wörter:** 「ナイフ」 (naifu, 'Messer'), 「ノート」 (nōto, 'Notizbuch'), 「ネクタイ」 (nekutai, 'Krawatte'), 「ニュース」 (nyūsu, 'Nachrichten').$TEXT$
WHERE id = 6396 AND lesson_id = 152;

-- Page 2, Block 13 (id=6402): H-Reihe
UPDATE lesson_content SET content_text = $TEXT$## H-Reihe — mit einer Ausnahme

Wie bei Hiragana folgt die H-Reihe dem Muster **H + Vokal**, mit derselben **einen Ausnahme**: Der "u"-Vokal wird zum "fu". Das "h" ist immer ein klarer, hauchiger Konsonant.

- **ハ (ha)** wie in *Hase*
- **ヒ (hi)** wie in *Hilfe*
- **フ (fu)** ⚠ — nicht 'hu', sondern weiches **'fu'** (Lippen flach, wie wenn du eine Kerze ausbläst — kein deutsches "f"!)
- **ヘ (he)** wie in *Held*
- **ホ (ho)** wie in *Hose*

> **Eselsbrücken (Tofugu-Stil):**
> - 「ハ」 ist ein **Reisfeld-Hut** (japanischer "**ha**t") — zwei Schenkel wie ein Spitzdach
> - 「ヒ」 ist ein **Mensch mit verschmitztem Grinsen** ("**hee** hee")
> - 「フ」 ist eine **dreieckige Fahne** ("**f**lag") — ein einziger Strich
> - 「ヘ」 ist **identisch zur Hiragana 「へ」** — kein neues Zeichen zu lernen!
> - 「ホ」 ist ein **heiliges Kreuz** ("**ho**ly cross") mit zwei kleinen Schenkeln unten

> **Wichtig:** 「ヘ」 ist eines von **nur zwei Zeichen**, die in Hiragana und Katakana exakt gleich aussehen. (Das andere ist「リ」 vs.「り」 — sehr ähnlich, nicht ganz identisch.)

> **Verwechslungsgefahr:** 「ホ」 (ho) und 「ネ」 (ne) sehen sich auf den ersten Blick ähnlich (beide haben ein "T"-artiges Element). Unterschied: **Ho** hat **vier Schenkel** unten (zwei oben, zwei unten), **ne** hat unten einen markanten **Schwung mit Haken**.

**Mini-Wörter:** 「ハム」 (hamu, 'Schinken'), 「ホテル」 (hoteru, 'Hotel'), 「ヒーター」 (hītā, 'Heizung'), 「フォーク」 (fōku, 'Gabel').$TEXT$
WHERE id = 6402 AND lesson_id = 152;

-- Page 3, Block 1 (id=6408): Aussprache & Schreibhinweise
UPDATE lesson_content SET content_text = $TEXT$## Die drei Ausnahmen — exakt wie in Hiragana

Da Katakana **dieselben Klänge** wie Hiragana hat, sind auch die Aussprache-Ausnahmen identisch:

1. **「チ」 (chi)** — nicht 'ti', sondern **'tschi'** wie in *Tschüss*
2. **「ツ」 (tsu)** — nicht 'tu', sondern **'tsu'** mit Zungen-Klick (wie das "z" in *Zacke*)
3. **「フ」 (fu)** — nicht 'hu', sondern weiches **'fu'** (Lippen flach, kein deutsches "f")

> **Merke:** Diese drei Stellen sind **die einzigen Stolperfallen** in den ersten 30 Katakana. Wenn du sie automatisch richtig liest, sitzt der grösste Teil.

## Vokal-Entstummung in dieser Lektion

Die **Entstummung von u und i** (siehe Katakana 1) ist auch hier sehr aktiv:

- 「テスト」 (tesuto, 'Test') klingt wie **"tes'to"** — das u nach s wird hauchig
- 「フタ」 (futa, 'Deckel') — das fu wird oft fast zu **"fta"**
- 「ヒト」 (hito, 'Mensch') klingt wie **"hto"** — das i zwischen h und t entstummt

> **Faustregel (Wiederholung aus K1):** Wenn ein "u" oder "i" zwischen zwei stimmlosen Konsonanten (k, s, sh, t, ts, ch, p, h, f) steht oder am Wortende danach kommt, wird es im Tokyo-Standard fast unhörbar.

## Verwechslungsgefahr — die Katakana-Klassiker

Diese Paare sind das **grösste Stolperthema** beim Katakana-Lesen:

- **「シ」 (shi) vs. 「ツ」 (tsu)** — Strich-Richtung beachten:
  - **Shi**: Striche schräg nach **OBEN RECHTS**, Hauptstrich von **unten nach oben**
  - **Tsu**: Striche schräg nach **UNTEN**, Hauptstrich von **oben nach unten**
- **「ン」 (n, kommt in Katakana 3) vs. 「ソ」 (so, aus K1)** — Strich-Winkel:
  - **N**: **flacher** Winkel, Strich fast waagerecht
  - **So**: **steiler** Winkel, Strich fast senkrecht
- **「ヌ」 (nu) vs. 「ス」 (su, aus K1)** — su hat einen klaren Knick oben, nu ist runder und durchgezogen
- **「ネ」 (ne) vs. 「ホ」 (ho)** — Ne hat unten einen markanten **Schwung**, ho hat **vier gerade Schenkel** (zwei oben, zwei unten)

> **Lerntipp:** Schreibe シ und ツ **direkt nebeneinander** auf ein Blatt, dann ソ und ン. Der Vergleich macht den Unterschied klar.

## Etymologie — ein interessanter Bonus

Die Strichanzahl-Mysterien lösen sich, wenn du die Kanji-Herkunft kennst:

- 「ハ」 (ha) kommt von **八** (der Zahl 8) — daher die zwei schrägen Striche!
- 「ノ」 (no) ist nur **ein** Strich, vereinfacht aus **乃** (no)
- 「テ」 (te) kommt von **天** (Himmel)
- 「ト」 (to) kommt von **止** (stoppen)

Du musst diese Herkunft nicht auswendig lernen, aber sie hilft dir zu verstehen, warum **「ノ」 (no)** das einfachste Katakana ist (1 Strich) und 「ホ」 (ho) das komplexeste in dieser Lektion (4 Striche).

## Ein praktisches Detail: 「ヘ」 ist Hiragana und Katakana gleich

In Hiragana: 「へ」 (he). In Katakana: 「ヘ」 (he). **Identisch im Druckbild.** Das ist eine kleine, aber willkommene Ausnahme — du musst dir nichts Neues merken.

## Strichfolge

**Von oben nach unten, von links nach rechts.** Spezialfälle in dieser Lektion:

- 「ツ」 (tsu) und 「シ」 (shi) — drei Striche, **Reihenfolge ist wichtig** (sie unterscheidet die Zeichen)
- 「ノ」 (no), 「フ」 (fu), 「ヘ」 (he) — nur **ein Strich**
- 「ホ」 (ho) und 「ネ」 (ne) — **vier Striche**, die komplexesten der Lektion

## Tipp zum Üben

Lies **Speisekarten und Werbungen**. Lehnwörter wie 「テレビ」 (terebi), 「タクシー」 (takushī), 「ホテル」 (hoteru), 「ノート」 (nōto) erscheinen ständig. Wenn du einen englischen Ursprung erkennst, sitzt das Lesen.$TEXT$
WHERE id = 6408 AND lesson_id = 152;

-- Page 4, Block 1 (id=6409): Quiz-Vorlauf
UPDATE lesson_content SET content_text = $TEXT$## Teste dein Wissen

Gleich kommen **Fragen** zu den 15 neuen Katakana.

- **Multiple-Choice:** Welche Romaji-Lesung passt?
- **Richtig/Falsch:** Stimmt die angegebene Lesung?
- **Wort-Lesung:** Welches Lehnwort siehst du?
- **Matching:** Verbinde Zeichen mit Lesung

> **Tipp:** Achte besonders auf 「シ」 (shi) vs. 「ツ」 (tsu) und auf die drei Ausnahmen 「チ」 (chi), 「ツ」 (tsu), 「フ」 (fu).$TEXT$
WHERE id = 6409 AND lesson_id = 152;

-- Page 5, Block 1 (id=6410): Zusammenfassung
UPDATE lesson_content SET content_text = $TEXT$## Geschafft — 30 Katakana insgesamt

Mit dieser Lektion kennst du nun:

- Aus **Katakana 1**: Vokale + K-Reihe + S-Reihe (15 Zeichen)
- Aus **Katakana 2**: T-Reihe + N-Reihe + H-Reihe (15 weitere Zeichen)
- **Insgesamt 30 von 46** Katakana-Grundzeichen — mehr als die Hälfte

## Die wichtigsten Stolperfallen im Überblick

1. **「シ」 (shi) vs. 「ツ」 (tsu)** — Strich-Richtung (shi nach oben, tsu nach unten)
2. **「チ」 (chi)** — nicht 'ti', sondern 'tschi'
3. **「ツ」 (tsu)** — nicht 'tu', sondern 'tsu' mit Zungen-Klick
4. **「フ」 (fu)** — nicht 'hu', sondern weiches fu mit flachen Lippen
5. **「ヘ」 (he)** — identisch zu Hiragana 「へ」 (praktisch — kein neues Zeichen!)
6. **「ヌ」 (nu) vs. 「ス」 (su)** — Knick oben (su) vs. durchgezogen (nu)
7. **「ネ」 (ne) vs. 「ホ」 (ho)** — Schwung unten (ne) vs. vier Schenkel (ho)

## Lehnwörter, die du jetzt lesen kannst

- 「タクシー」 (takushī) — Taxi
- 「テレビ」 (terebi) — Fernseher
- 「テスト」 (tesuto) — Test
- 「チケット」 (chiketto) — Ticket
- 「ツナ」 (tsuna) — Thunfisch
- 「トイレ」 (toire) — Toilette
- 「ノート」 (nōto) — Notizbuch
- 「ナイフ」 (naifu) — Messer
- 「ハム」 (hamu) — Schinken
- 「ホテル」 (hoteru) — Hotel
- 「ヒーター」 (hītā) — Heizung
- 「フォーク」 (fōku) — Gabel
- 「ネクタイ」 (nekutai) — Krawatte

> **Probier es:** Lies jedes Wort **laut** und versuche den Ursprung zu erraten (englisch, deutsch, französisch). Wenn du 10 von 13 schaffst, sitzt die Lektion.

## Lerntipps

1. **Schreibe jeden Tag** alle 30 Zeichen einmal mit der Hand — mit korrekter Strichfolge
2. **Übe gezielt 「シ」 und 「ツ」** nebeneinander — Strich-Richtung verinnerlichen
3. **Lies kurze Lehnwörter laut** — Speisekarten, Werbung, Logos
4. **Achte auf Entstummung** — テスト ≈ "tes'to", ヒト ≈ "hto"
5. **Wiederhole das Quiz**, bis alle Fragen ohne Hilfe sitzen

## Was kommt als Nächstes?

- **Katakana 3** — die M-Reihe 「マミムメモ」, Y-Reihe 「ヤユヨ」, R-Reihe 「ラリルレロ」, W-Reihe 「ワヲ」 und der Sonderling 「ン」 (n) — dann hast du alle 46 Grundzeichen!
- Danach Katakana 4 (Diakritika + Längungsstrich vertieft) und Katakana 5 (Yōon + Lehnwort-Spezialitäten wie 「ティ」, 「ファ」, 「ウィ」)$TEXT$
WHERE id = 6410 AND lesson_id = 152;

-- =====================================================
-- TEIL B: Strichfolge (15 Updates auf kana.stroke_order_info)
-- Quellen: Wiktionary EN (Strichanzahl + Kanji-Herkunft pro Zeichen verifiziert)
-- =====================================================

-- T-Reihe (aus 多, 千, ?, 天, 止)
UPDATE kana SET stroke_order_info='3 Striche: 1) kurzer diagonaler Strich oben links nach unten rechts; 2) langer geschwungener Strich oben rechts nach unten links; 3) kurzer Strich in der Mitte rechts (innerhalb des Bogens) — wie ein Drachen (kite)' WHERE id=120;
UPDATE kana SET stroke_order_info='3 Striche: 1) kurzer waagerechter Strich oben (leicht schräg); 2) langer waagerechter Strich darunter; 3) langer senkrechter Strich, kreuzt beide und biegt unten leicht nach links — wie ein Cheerleader' WHERE id=121;
UPDATE kana SET stroke_order_info='3 Striche: 1) kurzer Strich oben links (nach unten); 2) zweiter kurzer Strich rechts daneben (gleiche Richtung); 3) langer geschwungener Strich oben nach unten links. WICHTIG: Striche zeigen NACH UNTEN — Verwechslung mit シ (shi, nach oben) vermeiden!' WHERE id=122;
UPDATE kana SET stroke_order_info='3 Striche: 1) kurzer waagerechter Strich oben; 2) langer waagerechter Strich darunter; 3) geschwungener Strich von oben rechts nach unten links (kreuzt Strich 2) — wie ein Telefonmast' WHERE id=123;
UPDATE kana SET stroke_order_info='2 Striche: 1) langer senkrechter Strich (von oben nach unten); 2) kurzer waagerechter Strich rechts in der Mitte (vom Hauptstrich nach rechts) — wie ein Totempfahl mit einem Querbalken' WHERE id=124;

-- N-Reihe (aus 奈, 仁, 奴, 祢, 乃)
UPDATE kana SET stroke_order_info='2 Striche: 1) langer waagerechter Strich oben (leicht schräg); 2) langer senkrechter Strich, kreuzt Strich 1 leicht rechts der Mitte und biegt unten links — wie ein aufsteigender Narwal' WHERE id=125;
UPDATE kana SET stroke_order_info='2 Striche: zwei waagerechte Striche übereinander, der obere kürzer als der untere — wie zwei liegende Nadeln. Aus 仁 vereinfacht' WHERE id=126;
UPDATE kana SET stroke_order_info='2 Striche: 1) kurzer diagonaler Strich oben rechts nach links unten; 2) langer geschwungener Strich kreuzt Strich 1 und biegt unten weit nach rechts — wie Stäbchen, die Nudeln greifen. Aus 奴 vereinfacht' WHERE id=127;
UPDATE kana SET stroke_order_info='4 Striche: 1) kurzer Strich oben (diagonal); 2) langer waagerechter Strich darunter; 3) langer senkrechter Strich kreuzt Strich 2; 4) kurzer Strich rechts unten (Schwung) — wie ein Pferd, das über eine Hürde springt' WHERE id=128;
UPDATE kana SET stroke_order_info='1 Strich: ein einziger geschwungener Strich von oben rechts nach unten links (sanfter Bogen) — wie eine lange Nase. Einfachstes Katakana-Zeichen, aus 乃 vereinfacht' WHERE id=129;

-- H-Reihe (aus 八, 比, 不, 部, 保)
UPDATE kana SET stroke_order_info='2 Striche: 1) kurzer diagonaler Strich oben links nach unten links; 2) zweiter kurzer Strich rechts daneben (von oben Mitte nach unten rechts) — wie ein Reisfeld-Hut. Aus 八 (Zahl 8) vereinfacht' WHERE id=130;
UPDATE kana SET stroke_order_info='2 Striche: 1) kurzer diagonaler Strich oben links (von oben nach unten); 2) langer Strich daneben (von oben nach unten und am unteren Ende nach rechts mit kleinem Haken) — wie ein Mensch mit verschmitztem Grinsen' WHERE id=131;
UPDATE kana SET stroke_order_info='1 Strich: ein einziger Strich, der oben links beginnt, waagerecht nach rechts läuft, dann diagonal nach unten links abbiegt — wie eine dreieckige Fahne. Aus 不 vereinfacht' WHERE id=132;
UPDATE kana SET stroke_order_info='1 Strich: ein einziger flacher Knick — sanft ansteigend nach rechts oben, dann flacher Bogen nach unten rechts. IDENTISCH zur Hiragana へ. Aus 部 vereinfacht' WHERE id=133;
UPDATE kana SET stroke_order_info='4 Striche: 1) kurzer waagerechter Strich oben; 2) langer senkrechter Strich, kreuzt Strich 1; 3) kurzer diagonaler Strich links unten; 4) kurzer diagonaler Strich rechts unten — wie ein heiliges Kreuz. Aus 保 vereinfacht' WHERE id=134;

-- Validierung
SELECT id, character, romanization, LEFT(stroke_order_info, 70) AS preview
FROM kana
WHERE id BETWEEN 120 AND 134
ORDER BY id;

SELECT id, page_number, order_index, LEFT(content_text, 60) AS preview, length(content_text) AS chars
FROM lesson_content
WHERE lesson_id = 152 AND content_type = 'text'
ORDER BY page_number, order_index;

COMMIT;
