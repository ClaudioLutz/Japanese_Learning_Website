-- Refine N5 Hiragana 3 (Lesson ID 148) — M/Y/R/W + ん
-- Erwartete Zeilen pro UPDATE: 1
-- Recherche: Tofugu, Wikipedia (Hiragana, Japanese phonology), Web-Search
-- Datum: 2026-05-02
SET client_encoding = 'UTF8';

BEGIN;

-- =====================================================
-- Stroke-Order fuer M/Y/R/W + ん (kana IDs 31-46)
-- Standard-Strichzahlen (Schreibschule)
-- =====================================================

UPDATE kana SET stroke_order_info='3 Striche: 1) waagerechter Strich oben; 2) zweiter waagerechter Strich darunter; 3) langer senkrechter Strich, der eine Schleife unten links bildet (geht durch beide Querstriche)' WHERE id=31;
UPDATE kana SET stroke_order_info='2 Striche: 1) langer geschwungener Strich (oben → links unten → wieder hoch, mit kleiner Schleife unten links); 2) kurzer Strich rechts daneben — sieht aus wie eine "21"' WHERE id=32;
UPDATE kana SET stroke_order_info='3 Striche: 1) waagerechter Strich oben; 2) langer senkrechter Strich mit Schleife (geht durch Strich 1); 3) kleiner Tropfen rechts oben — aehnlich す, aber mit Tropfen' WHERE id=33;
UPDATE kana SET stroke_order_info='2 Striche: 1) diagonaler Strich von oben rechts nach unten links; 2) langer Strich, der unten in eine geschlossene Schleife laeuft — wie ぬ, aber OHNE den Schwanz' WHERE id=34;
UPDATE kana SET stroke_order_info='3 Striche: 1) langer senkrechter Strich mit Schleife unten; 2) kurzer waagerechter Strich oben (kreuzt Strich 1); 3) zweiter waagerechter Strich darunter — sieht aus wie eine Wuerm-Angel' WHERE id=35;

UPDATE kana SET stroke_order_info='3 Striche: 1) geschwungener Strich von oben rechts nach unten links mit kleiner Schleife; 2) diagonaler Strich oben; 3) kleiner Strich rechts oben' WHERE id=36;
UPDATE kana SET stroke_order_info='2 Striche: 1) langer geschwungener Strich (links oben → bauchig nach unten → kleiner Haken rechts oben); 2) waagerechter Strich quer durch die Mitte — sieht aus wie ein Auge oder Fisch' WHERE id=37;
UPDATE kana SET stroke_order_info='2 Striche: 1) kurzer waagerechter Strich oben; 2) langer Strich, der unten eine geschlossene Schleife bildet — sieht aus wie die Buchstabenkombination "Y + O"' WHERE id=38;

UPDATE kana SET stroke_order_info='2 Striche: 1) kurzer waagerechter Strich oben; 2) langer geschwungener Strich darunter (oben → unten → leicht nach links zurueck) — Tofugu: stehender Hase' WHERE id=39;
UPDATE kana SET stroke_order_info='2 Striche: 1) langer leicht gebogener Strich links (oben → unten); 2) kurzer Strich rechts daneben — sehr aehnlich い (i), aber り ist meist staerker geschwungen' WHERE id=40;
UPDATE kana SET stroke_order_info='1 Strich: ein einziger Strich (oben → bauchig nach unten → Schleife unten rechts) — Unterschied zu ろ: る hat eine SCHLEIFE am Ende' WHERE id=41;
UPDATE kana SET stroke_order_info='2 Striche: 1) senkrechter Strich links; 2) langer Strich, der einen Bogen rechts oben macht und in einem Haken nach links endet — Tofugu: kniender Mensch' WHERE id=42;
UPDATE kana SET stroke_order_info='1 Strich: ein einziger Strich (oben → bauchig nach unten → endet flach ohne Schleife) — Unterschied zu る: ろ ist OHNE Endschleife' WHERE id=43;

UPDATE kana SET stroke_order_info='2 Striche: 1) senkrechter Strich links; 2) langer Strich, der einen Bogen rechts macht und gerade nach unten verlaeuft (offenes Ende) — sehr aehnlich れ und ね, aber わ hat ein OFFENES gerades Ende' WHERE id=44;
UPDATE kana SET stroke_order_info='3 Striche: 1) waagerechter Strich oben; 2) diagonaler Strich nach unten links (kreuzt Strich 1); 3) geschwungener Strich rechts mit kleinem Haken unten — wird "o" gesprochen, aber als 「を」 geschrieben' WHERE id=45;
UPDATE kana SET stroke_order_info='1 Strich: ein einziger geschwungener Strich (oben → leicht nach links unten → Bogen nach rechts → endet mit kleinem Haken) — sieht aus wie ein lateinisches "h" in Schreibschrift' WHERE id=46;

-- =====================================================
-- Text-Bloecke
-- =====================================================

-- Page 1, Block 1 (id=6268): Einfuehrung
UPDATE lesson_content SET content_text = $TEXT$## Wo stehst du jetzt?

Nach **Hiragana 1** und **Hiragana 2** kennst du bereits **30 Zeichen**: die Vokale, die K-, S-, T-, N- und H-Reihe. In dieser Lektion folgen die **letzten 16 Grundzeichen** — danach hast du das komplette Hiragana-System im Kopf.

## Was lernst du jetzt?

Diese Lektion deckt **vier Reihen plus einen Sonderling** ab:

1. Die **M-Reihe**: 「まみむめも」 (ma, mi, mu, me, mo)
2. Die **Y-Reihe**: 「やゆよ」 (ya, yu, yo) — nur **drei** Zeichen
3. Die **R-Reihe**: 「らりるれろ」 (ra, ri, ru, re, ro)
4. Die **W-Reihe**: 「わを」 (wa, wo) — nur **zwei** Zeichen
5. Der **Sonderling**: 「ん」 (n) — die einzige Hiragana, die **keinen Vokal** trägt

> **Drei Eigenheiten in dieser Lektion:**
>
> - Die **R-Reihe** ist **kein deutsches R**. Es ist ein einzelner kurzer Antipper der Zunge am Gaumen — phonetisch ein "alveolarer Tap" [ɾ], wie das **t** in amerikanischem *butter* oder das **einfache r** im Spanischen *pero*.
> - 「を」 wird heute fast immer als **"o"** gesprochen (nicht "wo") und ist ausschliesslich eine **Objektpartikel**.
> - 「ん」 ist ein **Chamäleon-Zeichen**: es passt seinen Klang an den nächsten Konsonanten an (deshalb klingt es mal wie m, mal wie n, mal wie ng).

## Warum sind Y- und W-Reihe unvollständig?

Im **Altjapanischen** gab es noch **yi/ye** (Y-Reihe) und **wi/wu/we** (W-Reihe). Diese Laute sind in den letzten ~1000 Jahren **verloren gegangen** — sie wurden mit い (i) und え (e) bzw. う (u) und い (i) verschmolzen. Übrig blieben drei Y-Zeichen und zwei W-Zeichen. Du musst dieses Detail nicht aktiv lernen, aber es erklärt die "Lücken" in der Tabelle.

## Was kannst du danach lesen?

Mit allen **46 Grundzeichen** liest du **jedes japanische Wort**, das nur Hiragana verwendet — und das sind sehr viele, vor allem im Anfangsbereich. Beispiele: 「やま」 (yama, 'Berg'), 「みず」 (mizu, 'Wasser'), 「ほん」 (hon, 'Buch'), 「とり」 (tori, 'Vogel'), 「わたし」 (watashi, 'ich').

**Tipp:** Lies in dieser Lektion jedes neue Zeichen **mehrmals laut**. Besonders die R-Reihe und ん-Assimilation brauchen etwas Übung.$TEXT$
WHERE id = 6268 AND lesson_id = 148;

-- Page 2, Block 1 (id=6269): M-Reihe
UPDATE lesson_content SET content_text = $TEXT$## M-Reihe — keine Ausnahmen

Die M-Reihe ist **regelmässig**. Alle fünf Zeichen folgen dem Muster **M + Vokal**:

- **ま (ma)** wie in *Mama*
- **み (mi)** wie in *mit*
- **む (mu)** wie in *Musik* (kurz, mit unrundiertem u)
- **め (me)** wie in *Mensch* (kurz)
- **も (mo)** wie in *Moment* (kurz)

> **Eselsbrücken (Tofugu-Stil):**
> - 「ま」 sieht aus wie eine **bizarre Magier-Figur** mit doppelten Armen — "magic ma!"
> - 「み」 sieht aus wie die **Glückszahl 21** im Blackjack ("twenty-one" → mi)
> - 「む」 ist die **Kuh** mit "muuh!" — der seitliche Strich ist der Schwanz
> - 「め」 ist ein **schönes Auge** mit Make-up
> - 「も」 ist ein **Wurm-Angel-Haken** mit zwei Querstrichen — "more worms"

> **Verwechslungs-Hinweis:** 「め」 (me) und 「ぬ」 (nu) sind sich sehr ähnlich. **me hat KEINEN Schwanz unten**, nu schon. Beide stammen historisch vom Kanji 女 (Frau).

> **Mini-Wörter:** 「みず」 (mizu, 'Wasser'), 「むし」 (mushi, 'Insekt'), 「もも」 (momo, 'Pfirsich'), 「まめ」 (mame, 'Bohne'), 「うみ」 (umi, 'Meer').$TEXT$
WHERE id = 6269 AND lesson_id = 148;

-- Page 2, Block 2 (id=6275): Y-Reihe
UPDATE lesson_content SET content_text = $TEXT$## Y-Reihe — nur drei Zeichen

Die Y-Reihe hat **nur drei Zeichen** statt fünf:

- **や (ya)** — wie englisches **"ya"** in *yacht*, oder wie deutsches **"ja"**
- **ゆ (yu)** — wie englisches **"you"**, oder wie deutsches **"jü"** ohne Lippenrundung
- **よ (yo)** — wie englisches **"yo"** in *yo-yo*, oder wie deutsches **"jo"**

> **Warum nur drei?** Im Altjapanischen gab es 「yi」 und 「ye」, sie sind aber im Mittelalter **mit い und え verschmolzen** — phonetisch nicht mehr unterscheidbar. Die Lücken in der Tabelle sind ein historisches Erbe, kein Versehen.

> **Eselsbrücken:**
> - 「や」 ist eine **Yacht** mit Anker und Flagge
> - 「ゆ」 ist ein **einzigartiger Fisch** oder ein Augapfel, der dich anschaut ("you!")
> - 「よ」 sind die Buchstaben **Y + O** zu einem **Yo-Yo** kombiniert

> **Mini-Wörter:** 「やま」 (yama, 'Berg'), 「ゆき」 (yuki, 'Schnee'), 「よる」 (yoru, 'Nacht'), 「やすい」 (yasui, 'günstig'), 「ゆめ」 (yume, 'Traum').$TEXT$
WHERE id = 6275 AND lesson_id = 148;

-- Page 2, Block 3 (id=6279): R-Reihe
UPDATE lesson_content SET content_text = $TEXT$## R-Reihe — der wichtigste Klang dieser Lektion

Die R-Reihe folgt dem Muster **R + Vokal**, aber das **R ist NICHT wie ein deutsches R**. Es ist phonetisch ein **alveolarer Tap [ɾ]**: die Zungenspitze tippt **einmal ganz kurz** an den Gaumen direkt hinter den oberen Schneidezähnen — kein Rollen, kein Reiben.

- **ら (ra)** — Zungenspitze tippt kurz, dann a
- **り (ri)** — Zungenspitze tippt kurz, dann i
- **る (ru)** — Zungenspitze tippt kurz, dann unrundiertes u
- **れ (re)** — Zungenspitze tippt kurz, dann e
- **ろ (ro)** — Zungenspitze tippt kurz, dann o

> **Vergleichsanker für deutsche Ohren:**
> - **Wie das "t" in amerikanischem *butter*** (klingt fast wie "budder") — das ist ein perfekter Tap
> - **Wie das einfache "r" im Spanischen *pero*** (NICHT das gerollte "rr" in *perro*)
> - Das japanische R liegt phonetisch **zwischen R, L und D** — alle drei Laute sind dem Tap nahe
> - **Faustregel:** Wenn du es zu hart sprichst, klingt es wie ein D. Zu weich, wie ein L. Beides ist verständlich. Je weicher, desto japanischer.

> **Eselsbrücken:**
> - 「ら」 ist ein **Hase** (rabbit) im Sitzen mit Schlappohren
> - 「り」 sind zwei **Schilfhalme** (reeds) im Wind
> - 「る」 ist eine verrückte **Route** (road) mit Schleife am Ende
> - 「れ」 ist ein **kniender Mensch**, der sich übergibt — aufrichtende Knie
> - 「ろ」 ist eine **schlichte Strasse** (road) ohne Schleife — Gegenstück zu る

> **Mini-Wörter:** 「とり」 (tori, 'Vogel'), 「さくら」 (sakura, 'Kirschblüte'), 「るす」 (rusu, 'abwesend'), 「これ」 (kore, 'das hier'), 「ろく」 (roku, 'sechs').$TEXT$
WHERE id = 6279 AND lesson_id = 148;

-- Page 2, Block 4 (id=6285): W-Reihe + ん
UPDATE lesson_content SET content_text = $TEXT$## W-Reihe — nur zwei Zeichen

Die W-Reihe hat **nur zwei Zeichen**:

- **わ (wa)** — wie englisches *what* (kurzes, weiches "wa")
- **を (wo)** ⚠ — heute gesprochen wie **"o"**, NICHT "wo". Es ist eine **reine Objektpartikel**, niemals Teil eines Wortes.

> **Wichtig zu 「を」:**
> - In der **modernen Tokyo-Standardsprache** ist 「を」 phonetisch **identisch mit 「お」** ([o])
> - Du verwendest es **nur als Partikel**, die das **direkte Objekt** im Satz markiert: 「ほんを よむ」 (hon **wo** yomu, 'ein Buch lesen') — gesprochen "hon **o** yomu"
> - Im Altjapanischen wurde es als [wo] gesprochen — daher die Romaji-Schreibweise
> - 「wi」, 「wu」, 「we」 gibt es im modernen Japanisch nicht mehr

> **Eselsbrücken:**
> - 「わ」 ist eine **Wespe**, die senkrecht hochfliegt
> - 「を」 ist ein **Mensch ohne Kinn**, der einen Bumerang in den Mund wirft — "Whoa!"

## Der Sonderling 「ん」

「ん」 ist die **einzige Hiragana ohne Vokal**. Sie steht für ein **n-Geräusch am Silbenende** und kann **nie am Wortanfang** stehen.

Aber: 「ん」 hat **mindestens vier Aussprache-Varianten**, je nachdem, was danach kommt. Diese **Assimilation** passiert automatisch — du musst nichts aktiv tun, aber du solltest die Varianten erkennen:

| Vor diesen Lauten | Klingt wie | Beispiel |
|---|---|---|
| **m, p, b** | **m** | 「さんぽ」 (sampo, 'Spaziergang') → "sampo" |
| **t, d, n, r** | **n** | 「みかん」 (mikan, 'Mandarine') → "mikan" |
| **k, g** | **ng** (wie deutsch *Singer*) | 「りんご」 (ringo, 'Apfel') → "ringo" |
| **s, z, h, j, Vokal** | nasalisiert (vorheriger Vokal mit Nasallaut) | 「ほんや」 (hon'ya, 'Buchhandlung') |
| **am Wortende** | langes nasales **n** im Rachen | 「ほん」 (hon, 'Buch') |

> **Eselsbrücke:** 「ん」 sieht fast aus wie ein lateinisches **"n"** in Schreibschrift — gleicher Klang, fast gleiche Form.

> **Mini-Wörter:** 「わたし」 (watashi, 'ich'), 「ほん」 (hon, 'Buch'), 「みかん」 (mikan, 'Mandarine'), 「りんご」 (ringo, 'Apfel'), 「さんぽ」 (sampo, 'Spaziergang'), 「ぐんま」 (Gunma, Präfekturname → "Gumma").

## Wörter, die du nun lesen kannst

Mit allen 46 Hiragana liest du eine riesige Menge japanischer Alltagswörter:

- 「やま」 (yama) — Berg
- 「みず」 (mizu) — Wasser
- 「ほん」 (hon) — Buch
- 「とり」 (tori) — Vogel
- 「わたし」 (watashi) — ich
- 「さくら」 (sakura) — Kirschblüte
- 「ありがとう」 (arigatou) — danke
- 「おはよう」 (ohayou) — guten Morgen
- 「こんにちは」 (konnichiwa) — guten Tag$TEXT$
WHERE id = 6285 AND lesson_id = 148;

-- Page 3, Block 1 (id=6289): Aussprache & Schreibhinweise
UPDATE lesson_content SET content_text = $TEXT$## Die wichtigsten Aussprache-Regeln dieser Lektion

**Das japanische R ist ein Tap, kein Trill.** Stell dir vor, du sagst ein **D mit einer winzigen Berührung** der Zungenspitze, ohne zu rollen. Phonetisch nennt man das einen **alveolaren Tap [ɾ]**. Die besten Vergleichsanker:

- Das **t** in amerikanischem *butter* (klingt wie "budder")
- Das **einfache r** im Spanischen *pero* (nicht das gerollte *perro*)
- Das R im Japanischen liegt **zwischen R, L und D**

Wenn du nur einen Versuch hast: Sag ein D, aber tippe die Zunge so weit hinten an, wie du kannst. Das kommt sehr nah ran.

**「を」 wird "o" gesprochen.** Im modernen Tokyo-Standard ist 「を」 lautlich **identisch mit 「お」**. Du hörst und sprichst nur "o". Die Romaji-Schreibweise "wo" ist ein historisches Erbe. **Verwendung**: ausschliesslich als Objektpartikel, niemals in Wörtern.

**「ん」 passt sich automatisch an.** Die vier wichtigsten Varianten:

- **vor m/p/b → klingt wie m**: 「さんぽ」 = "sampo"
- **vor n/t/d/r → klingt wie n**: 「みかん」 = "mikan"
- **vor k/g → klingt wie ng**: 「りんご」 = "ringo"
- **am Wortende → langes nasales n im Rachen**: 「ほん」 = "hon" (mit deutlich nasalem Schluss)

Die letzte Variante (Wortende) ist phonetisch **kein deutsches "n"** mehr, sondern wird im Rachen nasalisiert (uvular). Das fällt vielen Lernern erst spät auf — es ist ok, wenn du anfangs ein normales "n" sprichst.

## Verwechslungsgefahr — die kniffligsten Paare

Diese Zeichen sehen sich **sehr ähnlich**. Schau genau hin:

- **「ま」 (ma) vs. 「も」 (mo) vs. 「す」 (su)** — alle haben einen senkrechten Strich mit Schleife.
  * **ma** hat **zwei Querstriche** oben
  * **mo** hat **einen** Querstrich oben + einen geschwungenen Boden
  * **su** hat nur **einen** Querstrich oben (ohne ma's zweiten)
- **「め」 (me) vs. 「ぬ」 (nu) vs. 「あ」 (a)** — alle drei mit "Schleifen-Anteil"
  * **me** hat **keinen Schwanz** unten
  * **nu** hat **eine Schleife** mit Schwanz unten
  * **a** hat einen **Querstrich oben** und einen kleinen Schwung daneben
- **「る」 (ru) vs. 「ろ」 (ro)** — derselbe Bogen, aber **ru hat eine Schleife unten**, **ro NICHT**
- **「れ」 (re) vs. 「ね」 (ne) vs. 「わ」 (wa)** — alle drei haben einen senkrechten Strich links + einen Schwung rechts. **Das rechte Ende** macht den Unterschied:
  * **ne** = kleine **Schleife** unten rechts
  * **re** = kleiner **Haken** nach oben links
  * **wa** = **gerade nach unten, offenes Ende**

> **Lerntipp:** Schreibe diese kniffligen Paare **direkt nebeneinander** auf ein Blatt — der Vergleich macht den Unterschied klar.

## Strichfolge — zur Übersicht

Wie immer gilt: **von oben nach unten, von links nach rechts**. Strichanzahlen in dieser Lektion:

- **1 Strich:** 「る」 (ru), 「ろ」 (ro), 「ん」 (n)
- **2 Striche:** 「み」 (mi), 「め」 (me), 「ゆ」 (yu), 「よ」 (yo), 「ら」 (ra), 「り」 (ri), 「れ」 (re), 「わ」 (wa)
- **3 Striche:** 「ま」 (ma), 「む」 (mu), 「も」 (mo), 「や」 (ya), 「を」 (wo)

Detailangaben findest du auf jeder Hiragana-Karte (Karten umdrehen).

## Tipp zum Üben

**Schreibe die ganze Hiragana-Tabelle** einmal komplett aus dem Kopf auf ein Blatt — alle 46 Zeichen, geordnet nach Reihen. Das ist die beste Übung, um zu prüfen, ob alles sitzt. Mach es einmal pro Tag eine Woche lang.$TEXT$
WHERE id = 6289 AND lesson_id = 148;

-- Page 4, Block 1 (id=6290): Quiz-Vorlauf
UPDATE lesson_content SET content_text = $TEXT$## Teste dein Wissen

Gleich kommen **Fragen** zu den 16 neuen Zeichen.

- **Multiple-Choice:** Welche Romaji-Lesung passt zum Zeichen?
- **Richtig/Falsch:** Stimmt die angegebene Regel?
- **Wort-Lesung & Bedeutung:** Welches Wort siehst du?
- **Matching:** Verbinde Zeichen mit Lesung

> **Tipp:** Konzentriere dich auf die Verwechslungspaare わ/ね/れ und る/ろ. Auch 「を」 (wird "o" gesprochen) und die ん-Assimilation (sampo/ringo/mikan) sind klassische Stolperfallen.$TEXT$
WHERE id = 6290 AND lesson_id = 148;

-- Page 5, Block 1 (id=6291): Zusammenfassung
UPDATE lesson_content SET content_text = $TEXT$## Geschafft — das komplette Hiragana-System

Nach **drei Lektionen** kennst du nun **alle 46 Grundzeichen**:

- **Hiragana 1:** Vokale + K-Reihe + S-Reihe (15 Zeichen)
- **Hiragana 2:** T-Reihe + N-Reihe + H-Reihe (15 Zeichen)
- **Hiragana 3:** M-Reihe + Y-Reihe + R-Reihe + W-Reihe + ん (16 Zeichen)

## Die wichtigsten Stolperfallen im Überblick

Diese Ausnahmen musst du dir besonders merken:

1. **「し」 (shi)** — nicht 'si' (S-Reihe)
2. **「ち」 (chi)** — nicht 'ti' (T-Reihe)
3. **「つ」 (tsu)** — nicht 'tu' (T-Reihe)
4. **「ふ」 (fu)** — bilabial, nicht deutsches "f" (H-Reihe)
5. **「は」** als Partikel = "wa" (H-Reihe)
6. **「を」** = "o" gesprochen, nur Objektpartikel (W-Reihe)
7. **「ん」** — kein eigener Vokal, **vier Klang-Varianten** je nach Kontext
8. **R-Reihe** ist ein **Tap** [ɾ], nicht ein gerolltes deutsches R

## Wörter, die du jetzt lesen kannst

Mit den vollen 46 Zeichen liest du wirklich **jeden** japanischen Text, der nur Hiragana verwendet:

- 「わたし」 (watashi) — ich
- 「あなた」 (anata) — du
- 「やま」 (yama) — Berg
- 「みず」 (mizu) — Wasser
- 「ほん」 (hon) — Buch
- 「とり」 (tori) — Vogel
- 「さくら」 (sakura) — Kirschblüte
- 「ありがとう」 (arigatou) — danke
- 「おはよう」 (ohayou) — guten Morgen
- 「こんにちは」 (konnichiwa) — guten Tag (geschrieben mit は = "wa"!)
- 「みかん」 (mikan) — Mandarine
- 「りんご」 (ringo) — Apfel ("ringo" mit ng-Klang)
- 「さんぽ」 (sampo) — Spaziergang ("sampo" mit m!)

> **Probier es:** Lies jedes Wort **laut**, ohne auf die Romaji zu schauen. Schaffst du alle dreizehn ohne Fehler, sitzt das Hiragana-Grundsystem.

## Lerntipps für die nächsten Tage

1. **Schreibe einmal pro Tag die ganze Hiragana-Tabelle** aus dem Kopf — fünf Minuten
2. **Übe die Verwechslungspaare gezielt**: わ/ね/れ, る/ろ, め/ぬ, ま/も/す
3. **Lies jeden Tag drei kurze Sätze laut** — die Geschwindigkeit kommt mit der Zeit
4. **Achte beim Hören** auf ん-Assimilation: "sampo" statt "sanpo", "ringo" mit ng — das ist Standard
5. **Wiederhole das Quiz**, bis du alle Fragen ohne Hilfe schaffst

## Was kommt als Nächstes?

- **Hiragana 4** — die **Diakritika** (Dakuten 「゛」 und Handakuten 「゜」), die が/ざ/だ/ば/ぱ-Reihen erzeugen (25 weitere Zeichen)
- **Hiragana 5** — die **Yōon** (kombinierte Silben wie きゃ/しゃ/ちゃ)
- Danach **Katakana** — das zweite japanische Schriftsystem, vor allem für Lehnwörter und Eigennamen
- Parallel kannst du mit **Vokabel-Lektionen** auf N5-Niveau beginnen

**Du hast jetzt die Schwelle zu echtem Japanisch überschritten.** Glückwunsch!$TEXT$
WHERE id = 6291 AND lesson_id = 148;

-- Validierung
SELECT id, page_number, order_index, LEFT(content_text, 60) AS preview, length(content_text) AS chars
FROM lesson_content
WHERE lesson_id = 148 AND content_type = 'text'
ORDER BY page_number, order_index;

SELECT id, character, romanization, LEFT(stroke_order_info, 60) FROM kana WHERE id BETWEEN 31 AND 46 ORDER BY id;

COMMIT;
