-- Refine N5 Katakana 3 (Lesson ID 153) — Text-Inhalte + Strichfolge
-- M-Reihe (マミムメモ), Y-Reihe (ヤユヨ), R-Reihe (ラリルレロ), W-Reihe (ワヲ), ン
-- Recherche: 2026-05-02 (Tofugu, Wiktionary EN — Strichanzahl + Kanji-Herkunft pro Zeichen)
SET client_encoding = 'UTF8';

BEGIN;

-- =====================================================
-- TEIL A: Text-Bloecke (8 Updates)
-- =====================================================

-- Page 1, Block 1 (id=6411): Einfuehrung
UPDATE lesson_content SET content_text = $TEXT$## Wo stehst du jetzt?

Nach **Katakana 1** und **Katakana 2** kennst du bereits **30 Katakana-Zeichen**. In dieser Lektion folgen die **letzten 16 Grundzeichen** — danach hast du das komplette Katakana-Grundsystem im Kopf.

## Was lernst du jetzt?

Diese Lektion deckt **vier Reihen plus einen Sonderling** ab:

1. Die **M-Reihe**: 「マミムメモ」 (ma, mi, mu, me, mo)
2. Die **Y-Reihe**: 「ヤユヨ」 (ya, yu, yo) — wie bei Hiragana **nur drei** Zeichen
3. Die **R-Reihe**: 「ラリルレロ」 (ra, ri, ru, re, ro) — der weiche japanische R-Klang
4. Die **W-Reihe**: 「ワヲ」 (wa, wo) — nur **zwei** Zeichen, ヲ ist quasi tot
5. Der **Sonderling**: 「ン」 (n) — die einzige Katakana ohne Vokal, mit **sechs** Aussprache-Varianten!

## Achtung — die zweite grosse Verwechslungsfalle

Nachdem du in Katakana 2 das シ/ツ-Paar gemeistert hast, kommt jetzt **ハer Twin-Falle Nr. 2**: 「ン」 (n) und 「ソ」 (so, aus K1) sehen sich extrem ähnlich. Strich-Winkel ist der Schlüssel — flach für n, steil für so.

## Was kannst du danach lesen?

Mit allen **46 Grundzeichen** liest du jeden Lehnwort-Text:

- 「ラジオ」 (rajio, 'Radio')
- 「マイク」 (maiku, 'Mikrofon')
- 「ワイン」 (wain, 'Wein')
- 「レストラン」 (resutoran, 'Restaurant')
- 「コンピューター」 (konpyūtā, 'Computer')

> **Tipp:** Wie bei Hiragana ist die R-Reihe **kein deutsches R**. Es bleibt der weiche Klang zwischen R, L und D — exakt wie in 「ら」 (ra) bei Hiragana.$TEXT$
WHERE id = 6411 AND lesson_id = 153;

-- Page 2, Block 1 (id=6412): M-Reihe
UPDATE lesson_content SET content_text = $TEXT$## M-Reihe — keine Ausnahmen

Die M-Reihe ist **regelmässig**. Alle fünf Zeichen folgen **M + Vokal**, ohne Stolperstellen.

- **マ (ma)** wie in *Mama*
- **ミ (mi)** wie in *mit*
- **ム (mu)** wie in *Musik* (kurz, mit unrundiertem u)
- **メ (me)** wie in *Mensch*
- **モ (mo)** wie in *Moment*

> **Eselsbrücken (Tofugu-Stil):**
> - 「マ」 ist voller Winkel und Längen — **Mathematik** (math)
> - 「ミ」 sind **drei Raketen**, die auf dich zufliegen — drei Striche für 三 (drei)
> - 「ム」 sieht aus wie ein **freundliches Kuhgesicht**: "**Moo**"
> - 「メ」 ist ein **'X' über einem Auge** — Auge heisst auf Japanisch *me*
> - 「モ」 ähnelt **stark** der Hiragana 「も」 — gleiche Idee, eckiger

> **Bonus-Etymologie:** 「ミ」 kommt von 三 (der Zahl 3) — daher hat es exakt **drei** Striche! Und 「メ」 stammt von 女 (Frau), 「マ」 ist eine Mischung aus 末 und 万.

**Mini-Wörter:** 「マイク」 (maiku, 'Mikrofon'), 「メニュー」 (menyū, 'Menü'), 「モーター」 (mōtā, 'Motor'), 「ミルク」 (miruku, 'Milch').$TEXT$
WHERE id = 6412 AND lesson_id = 153;

-- Page 2, Block 7 (id=6418): Y-Reihe
UPDATE lesson_content SET content_text = $TEXT$## Y-Reihe — nur drei Zeichen

Wie bei Hiragana hat die Y-Reihe **nur drei Zeichen** — *yi* und *ye* existieren im modernen Japanisch nicht. Das "y" ist immer ein klares englisches **y** (wie in *yes*), nie das deutsche "j" mit Reibung.

- **ヤ (ya)** wie in englischem *yes*, *yard*
- **ユ (yu)** wie in englischem *you*
- **ヨ (yo)** wie in englischem *yoga*, *yo*

> **Eselsbrücken (Tofugu-Stil):**
> - 「ヤ」 sieht **stark** wie die Hiragana 「や」 aus — minus ein kleiner Strich
> - 「ユ」 ist ein **Pirat mit Haken-Hand** — "**you**, what are you?"
> - 「ヨ」 ist ein **Yogi in einer Yoga-Pose** — eckige Position, drei Schenkel

> **Verwechslungsgefahr:** 「ユ」 (yu) sieht aus wie ein offenes 'U' mit Querstrich. Verwechselbar mit 「コ」 (ko, aus K1) — **ko ist eckig geschlossen** (zwei rechte Winkel), **yu** hat einen **Querstrich quer durch** in der Mitte.

**Mini-Wörter:** 「ヤフー」 (yafū, Yahoo), 「ユニーク」 (yunīku, 'einzigartig'), 「ヨガ」 (yoga, 'Yoga'), 「ユーモア」 (yūmoa, 'Humor').$TEXT$
WHERE id = 6418 AND lesson_id = 153;

-- Page 2, Block 11 (id=6422): R-Reihe
UPDATE lesson_content SET content_text = $TEXT$## R-Reihe — der weiche Klang zwischen R, L und D

Die R-Reihe folgt **R + Vokal**, mit dem **berühmt-schwierigen weichen R**. Die Zungenspitze tippt **kurz** an den Gaumen — kein deutsches R, kein gerolltes R, kein L. Englische Muttersprachler hören es oft als L oder D, deutsche oft als L.

- **ラ (ra)** — weiches r, fast l
- **リ (ri)** — weiches r mit i
- **ル (ru)** — weiches r mit unrundiertem u
- **レ (re)** — weiches r mit e
- **ロ (ro)** — weiches r mit o

> **Aussprache-Tipp:** Sag das englische **"l"** wie in *little*, aber **kürzer** und mit der Zungenspitze nur **antippend**, nicht haftend. Das ist sehr nah am japanischen R.

> **Eselsbrücken (Tofugu-Stil):**
> - 「ラ」 ist ein **Raptor mit cooler Sonnenbrille** ("**rap**per")
> - 「リ」 ähnelt **stark** der Hiragana 「り」 — gleicher Klang, gleiche Form
> - 「ル」 hat **zwei Wege** ("**rou**tes"), die du nehmen kannst
> - 「レ」 ist eine Person namens **Rei mit rotem Haar** ("**re**d hair")
> - 「ロ」 ist eine **quadratische Strasse** ("**ro**ad"), die im Kreis läuft

> **Verwechslungsfalle:** 「ル」 (ru) und 「レ」 (re) sehen sich ähnlich. **Ru** hat einen **Schwung** mit Haken nach oben rechts, **re** ist ein einfacher eckiger Knick.

**Mini-Wörter:** 「ラジオ」 (rajio, 'Radio'), 「リング」 (ringu, 'Ring'), 「レストラン」 (resutoran, 'Restaurant'), 「ロボット」 (robotto, 'Roboter'), 「ルール」 (rūru, 'Regel').$TEXT$
WHERE id = 6422 AND lesson_id = 153;

-- Page 2, Block 17 (id=6428): W-Reihe + ン
UPDATE lesson_content SET content_text = $TEXT$## W-Reihe — nur zwei Zeichen

Die W-Reihe hat **nur zwei Zeichen**, weil *wi/wu/we* im modernen Japanisch nicht mehr existieren:

- **ワ (wa)** wie in englischem *what* (kurzes w, Lippen leicht gerundet)
- **ヲ (wo)** ⚠ — gesprochen wie **'o'**, NICHT 'wo'! In Katakana **extrem selten**

> **Wichtig zu 「ヲ」:** Du siehst es in modernem Katakana **fast nie** — vielleicht in alten Texten, in Liedtiteln oder in stilisierten Schildern. In Hiragana ist 「を」 die wichtige Akkusativ-Partikel; in Katakana hat es keine reguläre Funktion mehr. Du solltest es **lesen können**, musst es aber nicht aktiv schreiben.

> **Eselsbrücken (Tofugu-Stil):**
> - 「ワ」 ist eine Frage, die mit "**what**" beginnt
> - 「ヲ」 ist ein **Hund, der so kräftig "woofed"**, dass die Zunge rausfliegt

## Der Sonderling 「ン」 (n)

「ン」 ist die **einzige Katakana ohne Vokal** — wie 「ん」 bei Hiragana. Es kommt **nie am Wortanfang**.

> **Eselsbrücke (Tofugu):** 「ン」 ist ein **Mann mit nur einem Auge** ("**n** = m**a****n**, **on**e eye").

**Sechs Aussprache-Varianten** je nach Folgekonsonant — passt sich an wie ein Chamäleon:

- vor **t, d, n, r, s, ts, z** → klingt wie **n** (z.B. ホンダ honda)
- vor **m, p, b** → klingt wie **m** (z.B. コンビニ konbini ≈ "kombini")
- vor **k, g** → klingt wie **ng** (z.B. リンゴ ringo ≈ "ring-go")
- vor **ch, j, ny** → klingt wie weiches **n+y** (ɲ)
- am **Wortende** → klingt wie ein nasaliertes **N** im Rachen (z.B. パン pan)
- vor **w, y, Vokalen, Frikativen** → wird zu einem **nasalierten Approximanten**

> **Beruhigung:** Du musst diese sechs Varianten **nicht aktiv lernen**. Dein Mund passt sich automatisch an, wenn du den nächsten Konsonanten ansetzt. Wichtig ist nur, dass du **nicht überdeutlich "n"** sprichst, wo das Japanische "m" oder "ng" hört.

> **⚠ Verwechslungsfalle Nr. 2 in Katakana:** 「ン」 (n) und 「ソ」 (so, aus K1) sehen sich extrem ähnlich. **Strich-Winkel** entscheidet:
> - 「ン」 (n) — Strich läuft **flach** von oben nach unten links (fast waagerecht zum Hauptstrich)
> - 「ソ」 (so) — Strich läuft **steil** von oben nach unten rechts (fast senkrecht)

**Mini-Wörter:** 「ワイン」 (wain, 'Wein'), 「コンビニ」 (konbini, 'Convenience-Store'), 「マンション」 (manshon, 'Apartment-Hochhaus'), 「リンゴ」 (ringo, 'Apfel').$TEXT$
WHERE id = 6428 AND lesson_id = 153;

-- Page 3, Block 1 (id=6432): Aussprache & Schreibhinweise
UPDATE lesson_content SET content_text = $TEXT$## Die wichtigsten Regeln dieser Lektion

**Das R bleibt weich.** Wie bei Hiragana — Zungenspitze tippt kurz an den Gaumen, kein deutsches R, kein L, kein gerolltes R. Es ist ein eigener Laut zwischen den drei.

**「ヲ」 (wo) ist quasi tot.** In modernen Katakana-Texten siehst du es fast nie. Es ist hauptsächlich aus historischen Gründen in der Tabelle. Erkennen ja, schreiben fast nie.

**「ン」 (n) ist ein Chamäleon.** Sechs Aussprache-Varianten, je nach Folgelaut. Du musst sie nicht bewusst lernen — dein Mund macht das automatisch, sobald du den nächsten Konsonanten ansetzt.

**「ン」 nie am Wortanfang.** Japanische Wörter beginnen nie mit ン (oder ん). Wenn du ein Wort siehst, das damit anfängt, ist es wahrscheinlich Lautmalerei oder ein Fremdwort.

## Verwechslungsgefahr — die Katakana-Klassiker

Diese Paare musst du sicher unterscheiden können:

- **「ン」 (n) vs. 「ソ」 (so, K1)** — Strich-Winkel: **flach** für n, **steil** für so
- **「シ」 (shi, K1) vs. 「ツ」 (tsu, K2)** — Strich-Richtung (oben rechts vs. unten)
- **「ラ」 (ra) vs. 「ヲ」 (wo)** — wo hat einen **extra Querstrich oben**
- **「ル」 (ru) vs. 「レ」 (re)** — ru hat einen **Schwung mit Haken**, re ist ein einfacher Knick
- **「ロ」 (ro) vs. 「コ」 (ko, K1)** — ro ist quadratisch **geschlossen**, ko ist **rechts offen**
- **「マ」 (ma) vs. 「ア」 (a, K1)** — ma hat einen **unteren Schwung** mit Punkt, a einen Knick
- **「ユ」 (yu) vs. 「コ」 (ko, K1)** — yu hat einen **Querstrich quer durch**, ko nicht

> **Lerntipp:** Schreibe die häufigsten Verwechslungspaare nebeneinander auf ein Blatt: シ/ツ, ン/ソ, ル/レ, ラ/ヲ. Das 'Cheat-Sheet' rettet dich beim Lesen.

## Etymologie — Strichanzahl ist kein Zufall

Ein paar interessante Verbindungen zur Kanji-Herkunft:

- 「ミ」 (mi) kommt von **三** (der Zahl 3) — daher exakt **drei** Striche!
- 「メ」 (me) kommt von **女** (Frau) — daher die Idee mit dem Auge (*me*)
- 「ロ」 (ro) kommt von **呂** — die quadratische Form ist nahezu unverändert
- 「ヨ」 (yo) kommt von **與** — die drei Querstriche stammen direkt aus dem Original
- 「レ」 (re) ist mit **einem einzigen Strich** das einfachste Zeichen dieser Lektion

## Strichfolge

**Von oben nach unten, von links nach rechts.** Spezialfälle:

- 「ン」 (n) und 「ノ」 (no, K2) — **ein Strich** (no), **zwei Striche** (n)
- 「レ」 (re) — nur **ein Strich**, einfach durchgezogen
- 「ル」 (ru) — **zwei Striche** (Trennung in der Mitte)
- 「ヤ」 (ya) — **zwei Striche** (achte auf den geraden Hauptstrich)

## Tipp zum Üben

**Lies eine Restaurant-Speisekarte.** Lehnwörter wie 「ラーメン」 (rāmen), 「ワイン」 (wain), 「メニュー」 (menyū), 「ハンバーガー」 (hanbāgā) erscheinen ständig. Wenn du fünf Wörter pro Karte sicher liest, sitzt Katakana.$TEXT$
WHERE id = 6432 AND lesson_id = 153;

-- Page 4, Block 1 (id=6433): Quiz-Vorlauf
UPDATE lesson_content SET content_text = $TEXT$## Teste dein Wissen

Gleich kommen **Fragen** zu den 16 neuen Katakana.

- **Multiple-Choice:** Welche Romaji-Lesung passt?
- **Richtig/Falsch:** Stimmt die angegebene Lesung?
- **Wort-Lesung:** Welches Lehnwort siehst du?
- **Matching:** Verbinde Zeichen mit Lesung

> **Tipp:** Achte besonders auf 「ン」 (n) vs. 「ソ」 (so) — Strich-Winkel ist der Schlüssel — und auf die ン-Varianten (mb-Klang in コンビニ, ng-Klang in リンゴ).$TEXT$
WHERE id = 6433 AND lesson_id = 153;

-- Page 5, Block 1 (id=6434): Zusammenfassung
UPDATE lesson_content SET content_text = $TEXT$## Geschafft — alle 46 Katakana-Grundzeichen!

Nach **drei Lektionen** kennst du nun **das komplette Katakana-Grundsystem**:

- **Katakana 1:** Vokale + K-Reihe + S-Reihe (15 Zeichen)
- **Katakana 2:** T-Reihe + N-Reihe + H-Reihe (15 Zeichen)
- **Katakana 3:** M-Reihe + Y-Reihe + R-Reihe + W-Reihe + ン (16 Zeichen)

**Insgesamt 46 Zeichen — die Basis ist gelegt.**

## Die wichtigsten Stolperfallen im Überblick

1. **「シ」 (shi) vs. 「ツ」 (tsu)** — Strich-Richtung (Falle Nr. 1)
2. **「ン」 (n) vs. 「ソ」 (so)** — Strich-Winkel (Falle Nr. 2)
3. **「チ」 (chi)** — nicht 'ti', sondern 'tschi'
4. **「ツ」 (tsu)** — nicht 'tu', sondern 'tsu' mit Zungen-Klick
5. **「フ」 (fu)** — nicht 'hu', weiches fu mit flachen Lippen
6. **「ヲ」 (wo)** — gesprochen 'o', in Katakana extrem selten
7. **「ン」 (n)** — sechs Aussprache-Varianten, nie am Wortanfang
8. **R-Reihe** — weiches r zwischen r/l/d, keine deutsche Aussprache

## Lehnwörter, die du jetzt sicher liest

- 「ラジオ」 (rajio) — Radio
- 「マイク」 (maiku) — Mikrofon
- 「ワイン」 (wain) — Wein
- 「レストラン」 (resutoran) — Restaurant
- 「メニュー」 (menyū) — Menü
- 「ヨガ」 (yoga) — Yoga
- 「コンビニ」 (konbini) — Convenience-Store
- 「マンション」 (manshon) — Apartment-Hochhaus
- 「リンゴ」 (ringo) — Apfel
- 「ロボット」 (robotto) — Roboter
- 「ルール」 (rūru) — Regel
- 「ミルク」 (miruku) — Milch

> **Probier es:** Lies alle zwölf Wörter laut. Schaffst du es ohne Stockung, ist Katakana gefestigt.

## Lerntipps

1. **Schreibe einmal pro Tag die ganze Katakana-Tabelle** aus dem Kopf — fünf Minuten
2. **Übe die Verwechslungspaare gezielt**: シ/ツ, ン/ソ, ラ/ヲ, ル/レ
3. **Lies Speisekarten und Werbung** — Lehnwörter sind die natürliche Übungsumgebung
4. **Höre auf den ン-Chamäleon-Effekt** — リンゴ ≈ "ringo", コンビニ ≈ "kombini"
5. **Wiederhole das Quiz**, bis alle Fragen sitzen

## Was kommt als Nächstes?

- **Katakana 4** — die **Diakritika** (Dakuten + Handakuten + **Längungsstrich** ー), die ガ/ザ/ダ/バ/パ-Reihen erzeugen — kein Auswendiglernen neuer Formen, nur ein paar Striche!
- **Katakana 5** — die **Yōon** (kombinierte Silben キャ/シャ/チャ) plus **Lehnwort-Spezialitäten** wie 「ティ」 (ti), 「ファ」 (fa), 「ウィ」 (wi), 「ヴ」 (vu) — der Schlüssel zu modernen Lehnwörtern wie パーティ (party).

Danach hast du **Hiragana und Katakana komplett** im Griff — dein Lese-Werkzeugkasten ist dann vollständig, und du kannst dich auf Vokabeln und Kanji konzentrieren.$TEXT$
WHERE id = 6434 AND lesson_id = 153;

-- =====================================================
-- TEIL B: Strichfolge (16 Updates auf kana.stroke_order_info)
-- =====================================================

-- M-Reihe (aus 末/万, 三, 牟, 女, 毛 vereinfacht)
UPDATE kana SET stroke_order_info='2 Striche: 1) waagerechter Strich oben, der nach rechts unten in einen diagonalen Strich übergeht; 2) langer geschwungener Strich von oben nach unten links (kreuzt Strich 1) — voller Winkel und Längen wie Mathematik' WHERE id=135;
UPDATE kana SET stroke_order_info='3 Striche: drei kurze diagonale Striche untereinander, jeweils von oben rechts nach unten links — wie drei fliegende Raketen. Aus 三 (Zahl 3) — daher exakt 3 Striche!' WHERE id=136;
UPDATE kana SET stroke_order_info='2 Striche: 1) kurzer diagonaler Strich oben rechts nach links; 2) langer geschwungener Strich rechts unten (Bogen abwärts und nach rechts) — wie ein freundliches Kuhgesicht "Moo"' WHERE id=137;
UPDATE kana SET stroke_order_info='2 Striche: 1) kurzer diagonaler Strich von oben rechts nach unten links; 2) langer Strich von oben links nach unten rechts (kreuzt Strich 1) — wie ein "X" über einem Auge (me = Auge auf Japanisch)' WHERE id=138;
UPDATE kana SET stroke_order_info='3 Striche: 1) kurzer diagonaler Strich oben rechts nach links unten; 2) langer waagerechter Strich darunter; 3) langer senkrechter Strich, kreuzt Strich 2 und biegt unten links ab — ähnlich der Hiragana も' WHERE id=139;

-- Y-Reihe (aus 也, 由, 與 vereinfacht)
UPDATE kana SET stroke_order_info='2 Striche: 1) kurzer diagonaler Strich oben (von links unten nach rechts oben); 2) langer senkrechter Strich rechts daneben (kreuzt Strich 1 leicht) mit kleinem Haken unten — ähnlich der Hiragana や' WHERE id=140;
UPDATE kana SET stroke_order_info='2 Striche: 1) kurzer waagerechter Strich oben Mitte, der nach unten in einen Senkrechten übergeht und unten in einen waagerechten Strich endet (Bogen-Form); 2) waagerechter Strich quer durch die Mitte — wie ein Pirat mit Haken-Hand' WHERE id=141;
UPDATE kana SET stroke_order_info='3 Striche: 1) waagerechter Strich oben (mit kurzem senkrechtem Strich rechts unten); 2) waagerechter Strich in der Mitte (kürzer); 3) waagerechter Strich unten — wie ein Yogi in Yoga-Pose. Drei Querstriche aus 與' WHERE id=142;

-- R-Reihe (aus 良, 利, 流, 礼, 呂 vereinfacht)
UPDATE kana SET stroke_order_info='2 Striche: 1) kurzer waagerechter Strich oben; 2) langer Bogen darunter (von links nach rechts unten, wie eine flache Schale) — wie ein Raptor mit cooler Sonnenbrille (rapper)' WHERE id=143;
UPDATE kana SET stroke_order_info='2 Striche: 1) kurzer senkrechter Strich links; 2) langer senkrechter Strich rechts daneben (mit kleinem Haken unten) — fast identisch zur Hiragana り' WHERE id=144;
UPDATE kana SET stroke_order_info='2 Striche: 1) kurzer senkrechter Strich links (von oben nach unten, mit kleinem Bogen am Ende nach rechts); 2) langer senkrechter Strich rechts (von oben nach unten, mit Schwung nach oben rechts am Ende) — wie zwei Wege (routes)' WHERE id=145;
UPDATE kana SET stroke_order_info='1 Strich: ein einziger Strich, der oben links beginnt, kurz waagerecht nach rechts, dann lang nach unten links und am Ende mit Schwung nach oben rechts — Person mit rotem Haar (Rei)' WHERE id=146;
UPDATE kana SET stroke_order_info='3 Striche: 1) kurzer senkrechter Strich links; 2) waagerechter Strich oben nach rechts, der unten in einen senkrechten Strich übergeht; 3) waagerechter Strich unten verbindet beide Seiten — quadratisch geschlossen wie eine Strasse (road)' WHERE id=147;

-- W-Reihe (aus 和, 乎 vereinfacht)
UPDATE kana SET stroke_order_info='2 Striche: 1) kurzer waagerechter Strich oben; 2) langer Strich darunter (von links nach rechts, dann nach unten und unten rechts mit Schwung) — Frage beginnt mit "what". Aus 和 (Harmonie)' WHERE id=148;
UPDATE kana SET stroke_order_info='3 Striche: 1) kurzer waagerechter Strich oben; 2) zweiter waagerechter Strich darunter; 3) langer Strich biegt rechts ab nach unten und endet mit Schwung — wie ein Hund mit "woofender" Zunge. In modernem Katakana SELTEN!' WHERE id=149;
UPDATE kana SET stroke_order_info='2 Striche: 1) kurzer Strich oben (diagonal von links unten nach rechts oben); 2) langer Strich von Strich 1 nach unten links (FLACHER Winkel, fast waagerecht). WICHTIG: Verwechslung mit ソ (so, steiler Winkel) vermeiden!' WHERE id=150;

-- Validierung
SELECT id, character, romanization, LEFT(stroke_order_info, 70) AS preview
FROM kana
WHERE id BETWEEN 135 AND 150
ORDER BY id;

SELECT id, page_number, order_index, LEFT(content_text, 60) AS preview, length(content_text) AS chars
FROM lesson_content
WHERE lesson_id = 153 AND content_type = 'text'
ORDER BY page_number, order_index;

COMMIT;
