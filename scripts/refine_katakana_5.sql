-- Refine N5 Katakana 5 (Lesson ID 155) — Yōon + Lehnwort-Spezialitäten
-- 12 Standard-Yōon (kya/sha/ja/cha + Familien) + 13 Lehnwort-Specials (ti/di/fa-fo/wi-wo/va-vo)
-- Recherche: 2026-05-02 (Wikipedia Yōon, Wikipedia Katakana, Tofugu)
SET client_encoding = 'UTF8';

BEGIN;

-- =====================================================
-- TEIL A: Text-Bloecke (6 Updates)
-- =====================================================

-- Page 1, Block 1 (id=6469): Einfuehrung
UPDATE lesson_content SET content_text = $TEXT$## Wo stehst du jetzt?

Nach **vier Katakana-Lektionen** kennst du:

- **46 Grundzeichen** (Katakana 1, 2, 3)
- **25 modifizierte Zeichen** mit Dakuten und Handakuten (Katakana 4)
- Den **Längungsstrich** 「ー」
- **= 71 Katakana**

## Was lernst du jetzt?

Die **letzte** Katakana-Lektion deckt zwei wichtige Themen ab:

1. **Yōon** (拗音, "verdrehter Klang") — kombinierte Silben aus i-Zeichen + kleinem ャ/ュ/ョ. **Genau wie bei Hiragana**, nur mit Katakana-Formen:
   - 「キ」 (ki) + 「ャ」 (kleines ya) = 「キャ」 (kya, **eine** Silbe!)
   - 「シ」 (shi) + 「ャ」 = 「シャ」 (sha)
   - 「ジ」 (ji) + 「ャ」 = 「ジャ」 (ja)
2. **Lehnwort-Spezialitäten** — Sondersilben, die **nur in Katakana** vorkommen, weil moderne Lehnwörter Klänge brauchen, die das alte Japanisch nicht hatte:
   - 「ティ」 (ti) — z.B. 「パーティー」 (pātī, 'Party')
   - 「ディ」 (di) — z.B. 「ディズニー」 (Dizunī, 'Disney')
   - 「ファ」 (fa), 「フィ」 (fi), 「フェ」 (fe), 「フォ」 (fo) — z.B. 「ファイル」 (fairu, 'Datei'), 「カフェ」 (kafe, 'Café')
   - 「ウィ」 (wi), 「ウェ」 (we), 「ウォ」 (wo) — z.B. 「ウィーン」 (Wīn, 'Wien')
   - 「ヴ」 (vu) und 「ヴァ」/「ヴィ」/「ヴェ」/「ヴォ」 — selten, für 'v' wie in 'ヴァイオリン' (vaiorin, 'Violine')

## Mora-Konzept — wichtig fürs Hörverstehen

Eine **Mora** ist die kleinste Klangeinheit im Japanischen — kürzer als eine Silbe, aber länger als ein Einzellaut. Jedes normale Kana (アイウ, カキク, etc.) ist **eine** Mora. Auch 「ー」 ist **eine** Mora.

**Yōon ist auch genau eine Mora** — obwohl sie aus zwei Zeichen besteht:

- 「キャ」 (kya) = 1 Mora (nicht "ki-ya"!)
- 「キヤ」 (ki-ya) = 2 Moren (zwei volle Zeichen)

Das hört man im Sprechen: kya wird **kurz und schnell** gesprochen, ki-ya **deutlich getrennt** in zwei Schlägen. Mora-Zählung ist später wichtig für Aussprache, Akzent und Versmasse.

## Was kannst du danach lesen?

Mit diesen Sondersilben werden moderne Lehnwörter zugänglich:

- 「パーティー」 (pātī) — Party
- 「ファイル」 (fairu) — Datei
- 「カフェ」 (kafe) — Café
- 「ディズニー」 (Dizunī) — Disney
- 「ウィーン」 (Wīn) — Wien
- 「シェフ」 (shefu) — Chef (aus dem Französischen)
- 「コーヒーショップ」 (kōhī shoppu) — Coffee-Shop

Danach hast du **Katakana komplett** — bereit für jeden Lehnwort-Text.$TEXT$
WHERE id = 6469 AND lesson_id = 155;

-- Page 2, Block 1 (id=6470): Standard-Yōon
UPDATE lesson_content SET content_text = $TEXT$## Yōon — wie bei Hiragana, mit Katakana-Formen

Die **i-Zeichen** kombinieren mit kleinem ャ/ュ/ョ zu einer einzelnen Silbe (Mora). Das kleine Zeichen sitzt **rechts unten** vom Hauptzeichen — etwa **halb so gross** wie das normale Kana.

Standard-Familien (in dieser Lektion zum Üben):

- **K-Yōon**: 「キャ」 (kya), 「キュ」 (kyu), 「キョ」 (kyo) — aus キ + kleines ヤ/ユ/ヨ
- **S-Yōon**: 「シャ」 (sha), 「シュ」 (shu), 「ショ」 (sho) — aus シ + kleines ヤ/ユ/ヨ
- **J-Yōon (S + Dakuten)**: 「ジャ」 (ja), 「ジュ」 (ju), 「ジョ」 (jo) — aus ジ + kleines ヤ/ユ/ヨ
- **CH-Yōon**: 「チャ」 (cha), 「チュ」 (chu), 「チョ」 (cho) — aus チ + kleines ヤ/ユ/ヨ

Weitere Familien existieren ebenfalls, kommen in N5 aber selten vor:

- M-Yōon (ミャ, ミュ, ミョ), R-Yōon (リャ, リュ, リョ)
- N-Yōon (ニャ, ニュ, ニョ), H-Yōon (ヒャ, ヒュ, ヒョ)
- G-/B-/P-Yōon (ギャ ギュ ギョ, ビャ ビュ ビョ, ピャ ピュ ピョ)

> **Wichtig — gross vs. klein:** Das kleine ャ/ュ/ョ ist **physisch kleiner** als ヤ/ユ/ヨ. Schau genau hin:
> - 「キヤ」 (ki-ya, **zwei** Silben, 2 Moren)
> - 「キャ」 (kya, **eine** Silbe, 1 Mora)
>
> Wenn du dir unsicher bist, hilft die Position: Das **kleine** Zeichen sitzt am **rechten unteren Rand** des Schreibfelds, das **grosse** in der **Mitte**.

> **Etymologie-Bonus:** Yōon entstand durch den massiven Import chinesischer Wörter ab dem 8. Jahrhundert. Chinesisch hat viele palatalisierte Laute (ki+a → kya), die das alte Japanisch nicht kannte. Yōon ist also **die Chinesisch-Brücke** im Japanischen — und genau deshalb tauchen Yōon häufig in Sino-Japanischen Komposita auf (kyū, jūsho, shōsetsu).

> **Romaji-Stolperfalle:** Das System ist kompakt — nicht *kyya/shya/chya/jya*, sondern **kya/sha/cha/ja**. Ein Buchstabe für die Palatalisierung, einer für den Vokal. Wenn du Romaji liest, sieh "ja", "sha", "cha", "kya" als **eine** Mora.

**Mini-Wörter:** 「シャツ」 (shatsu, 'Hemd'), 「ジュース」 (jūsu, 'Saft'), 「チョコ」 (choko, 'Schokolade'), 「キャベツ」 (kyabetsu, 'Kohl').$TEXT$
WHERE id = 6470 AND lesson_id = 155;

-- Page 2, Block 14 (id=6483): Lehnwort-Spezialitaeten
UPDATE lesson_content SET content_text = $TEXT$## Lehnwort-Spezialitäten — was es nur in Katakana gibt

Diese Kombinationen existieren **nur in Katakana**, weil moderne Lehnwörter Klänge brauchen, die das alte Japanisch nicht kannte. Sie entstehen durch ein **kleines Vokal-Zeichen** (ァ/ィ/ェ/ォ) nach einer i- oder u-Silbe.

### T-Familie — für englisches /t/ und /d/ vor i

- **「ティ」** (ti) = テ + kleines イ. Beispiel: 「パーティー」 (pātī, 'Party')
- **「ディ」** (di) = デ + kleines イ. Beispiel: 「ディズニー」 (Dizunī, 'Disney')

> Vor dieser Schreibweise nutzte Japanisch 「チ」 (chi) für ti — daher heisst Team noch heute oft 「チーム」 (chīmu). Die Form 「ティ」 ist die moderne Präzisierung.

### F-Familie — für englisches /f/

Früher gab es nur 「フ」 (fu). Mit kleinem Vokal entstehen alle f-Klänge:

- **「ファ」** (fa) = フ + kleines ア. Beispiel: 「ファイル」 (fairu, 'Datei')
- **「フィ」** (fi) = フ + kleines イ. Beispiel: 「フィッシュ」 (fisshu, 'Fisch')
- **「フェ」** (fe) = フ + kleines エ. Beispiel: 「カフェ」 (kafe, 'Café')
- **「フォ」** (fo) = フ + kleines オ. Beispiel: 「フォーク」 (fōku, 'Gabel')

### W-Familie — für moderne /w/-Klänge

Früher gab es nur 「ワ」 (wa) und das fast tote 「ヲ」. Mit ウ + kleinem Vokal entstehen die W-Klänge moderner Lehnwörter:

- **「ウィ」** (wi) = ウ + kleines イ. Beispiel: 「ウィーン」 (Wīn, 'Wien')
- **「ウェ」** (we) = ウ + kleines エ. Beispiel: 「ウェブ」 (webu, 'Web')
- **「ウォ」** (wo) = ウ + kleines オ. Beispiel: 「ウォーター」 (wōtā, 'Water'), 「ウォッカ」 (wokka, 'Wodka')

### V-Familie — der Sonderfall

Das japanische 'v' ist ein echter Sonderfall. Es nutzt 「ヴ」 — ein **U mit Dakuten** (von フ + ゛ inspiriert) — plus Vokale:

- **「ヴァ」** (va), **「ヴィ」** (vi), **「ヴ」** (vu), **「ヴェ」** (ve), **「ヴォ」** (vo)
- Beispiel: 「ヴァイオリン」 (vaiorin, 'Violine')

> **Praxis-Hinweis:** 「ヴ」 wird oft durch die **B-Reihe** ersetzt, weil viele Japaner v und b nicht unterscheiden. 「ヴァイオリン」 schreibt man heute oft als 「バイオリン」 (baiorin), 「ヴェネチア」 oft als 「ベネチア」 (Benechia, 'Venedig'). Tofugu sagt: *Du musst diese Sondersilben lesen können — aktiv schreiben musst du sie selten.*

> **Position des kleinen Zeichens:** In horizontalem Text sitzt das kleine ャ/ュ/ョ/ァ/ィ/ェ/ォ **rechts unten**. In vertikalem Text sitzt es **unten** (entsprechend "rechts" der Zeilenrichtung).

### Übersicht — was bedeutet was?

| Kombination | Lesung | Warum nötig? | Beispiel |
|---|---|---|---|
| ティ | ti | Englisch t vor i | パーティー |
| ディ | di | Englisch d vor i | ディズニー |
| ファ–フォ | fa, fi, fe, fo | Echtes f | ファイル, カフェ |
| ウィ–ウォ | wi, we, wo | Moderne w-Klänge | ウィーン, ウェブ |
| ヴァ–ヴォ | va–vo | Echtes v | ヴァイオリン |$TEXT$
WHERE id = 6483 AND lesson_id = 155;

-- Page 3, Block 1 (id=6497): Aussprache & Schreibhinweise
UPDATE lesson_content SET content_text = $TEXT$## Yōon — die wichtigsten Regeln

Die Yōon-Regeln gelten in Katakana exakt wie bei Hiragana:

1. **Eine Silbe (Mora), nicht zwei**: 「キャ」 (kya) ist eine schnelle Silbe, kein "ki-ya". Beim Sprechen darf das kleine ャ keinen eigenen Schlag bekommen.
2. **Kleines vs. grosses ャ/ヤ**: Genau auf die Grösse achten. 「キヤ」 = ki-ya (2 Moren), 「キャ」 = kya (1 Mora).
3. **Hepburn-Romaji ist kompakt**: kya/sha/cha/ja, **nicht** kyya/shya/chya/jya. Ein Konsonantenblock + ein Vokal.
4. **Mora-Zählung**: Yōon zählen als **eine** Mora. Das ist wichtig fürs Hörverstehen und später für Aussprache-Akzente.

## Lehnwort-Spezialitäten — wann nutzt man was?

**Die F-Familie 「ファ」 「フィ」 「フェ」 「フォ」** ist heute **Standard** für englische Wörter mit f:

- 「コーヒー」 (kōhī, 'Coffee') nutzt 「ヒ」 (hi), aber 「カフェ」 (kafe, 'Café') nutzt 「フェ」
- Faustregel: Wenn das Original wirklich ein 'f' hat, nutzt Modern-Japanisch die F-Familie

**「ティ」 / 「ディ」** ersetzen das alte 「チ」 (chi) und 「ジ」 (ji) für ti/di:

- Alt: 「チーム」 (chīmu, 'Team') — gibt's noch heute
- Neu: 「ティー」 (tī, 'Tee') — wenn das Original ein klares 't' hat

**「ヴ」** ist selten und wird oft umgangen. Beispiele: 「ヴァイオリン」 (vaiorin) wird in der Praxis oft als 「バイオリン」 (baiorin) geschrieben. Du musst ヴ **lesen** können, **aktives Schreiben** ist optional.

## Verwechslungsgefahr — gross vs. klein

Das ist der **zentrale Stolperstein** dieser Lektion:

- **Gross vs. klein bei ya/yu/yo**: 「キヤ」 (ki-ya, 2 Moren) vs. 「キャ」 (kya, 1 Mora)
- **Gross vs. klein bei a/i/u/e/o**: Bei Lehnwort-Spezialitäten ist das **kleine** ァ/ィ/ゥ/ェ/ォ kleiner als das normale ア/イ/ウ/エ/オ. Beispiel: 「フア」 (fu-a, 2 Moren) vs. 「ファ」 (fa, 1 Mora)
- **「シ」 (shi)-Yōon vs. 「ジ」 (ji)-Yōon**: Dakuten beachten — シャ ist *sha*, ジャ ist *ja*

> **Praxis-Tipp:** Wenn du dir unsicher bist, hilft die **Position** und **Grösse**. Das kleine Zeichen sitzt **rechts unten** und ist **etwa halb so gross** wie das normale.

## Geschichte — warum gibt es das alles?

- **Yōon** entstand durch chinesische Lehnwörter im 8.-9. Jahrhundert. Chinesisch hatte palatalisierte Laute (ki+a → kya), die das alte Japanisch nicht kannte.
- **Lehnwort-Spezialitäten** entstanden im 19.-20. Jahrhundert mit dem massiven Import europäischer Wörter (Englisch, Deutsch, Französisch, Portugiesisch). Davor gab es kein eindeutiges 'f', 'ti', 'wi' im Japanischen.

So ist Katakana eine **lebendige Schrift**, die immer noch wächst — neue Lehnwörter erfinden notfalls neue Kombinationen.

## Tipp zum Üben

**Lies eine moderne Werbung oder einen Café-Speiseplan.** Wörter wie 「カフェ」, 「パーティー」, 「ファイル」, 「コーヒー」 erscheinen überall. Wenn du fünf Wörter pro Werbung sicher liest, ist Katakana definitiv durch.$TEXT$
WHERE id = 6497 AND lesson_id = 155;

-- Page 4, Block 1 (id=6498): Quiz-Vorlauf
UPDATE lesson_content SET content_text = $TEXT$## Teste dein Wissen

Gleich kommen **Fragen** zu Yōon und Lehnwort-Spezialitäten.

- **Multiple-Choice:** Welche Romaji passt?
- **Richtig/Falsch:** Stimmt die Aussage?
- **Wort-Lesung:** Welches Lehnwort siehst du?
- **Matching:** Verbinde Zeichen mit Lesung

> **Tipp:** Achte auf das **kleine** ア (a) / イ (i) / ウ (u) / エ (e) / オ (o) bei den Lehnwort-Spezialitäten. 「フ」 (fu) + 「ァ」 (kleines a) = 「ファ」 (fa) — eine Silbe, eine Mora. Und denk an: Yōon ist **eine** Mora, nicht zwei!$TEXT$
WHERE id = 6498 AND lesson_id = 155;

-- Page 5, Block 1 (id=6499): Zusammenfassung
UPDATE lesson_content SET content_text = $TEXT$## Geschafft — Katakana ist KOMPLETT

Nach **fünf Lektionen** beherrschst du das gesamte Katakana-System:

- **Katakana 1:** Vokale + K-Reihe + S-Reihe (15 Zeichen)
- **Katakana 2:** T-Reihe + N-Reihe + H-Reihe (15 Zeichen)
- **Katakana 3:** M-Reihe + Y-Reihe + R-Reihe + W-Reihe + ン (16 Zeichen)
- **Katakana 4:** Diakritika + Längungsstrich (25 Zeichen + ー)
- **Katakana 5:** Yōon + Lehnwort-Spezialitäten (12 Standard-Yōon + 13 Specials)

## Was bedeutet das?

Du kannst nun **jedes** moderne Lehnwort lesen — von Café-Speisekarten über Werbung bis zu Marken-Namen. Zusammen mit den fünf Hiragana-Lektionen hast du den **kompletten Lese-Werkzeugkasten** für N5-Japanisch (ohne Kanji).

## Die zentralen Konzepte zum Mitnehmen

1. **Yōon = eine Mora** (nicht zwei) — kya, sha, ja, cha sind kompakt
2. **Klein vs. gross** entscheidet alles: 「キヤ」 vs. 「キャ」, 「フア」 vs. 「ファ」
3. **F-Familie ist Standard** für /f/-Lehnwörter
4. **「ティ」/「ディ」** sind moderne Präzisierungen für ti/di
5. **「ヴ」** ist selten — meist durch B-Reihe ersetzt
6. **Lehnwort-Spezialitäten** entstanden im 19.-20. Jh. mit dem Import europäischer Wörter

## Lehnwörter, die du jetzt sicher liest

- 「コーヒー」 (kōhī) — Kaffee
- 「ビール」 (bīru) — Bier
- 「ピザ」 (piza) — Pizza
- 「カフェ」 (kafe) — Café
- 「パーティー」 (pātī) — Party
- 「ファイル」 (fairu) — Datei
- 「ディズニー」 (Dizunī) — Disney
- 「ウィーン」 (Wīn) — Wien
- 「ジュース」 (jūsu) — Saft
- 「シェフ」 (shefu) — Chef
- 「コンピューター」 (konpyūtā) — Computer
- 「レストラン」 (resutoran) — Restaurant
- 「キャベツ」 (kyabetsu) — Kohl
- 「シャツ」 (shatsu) — Hemd

> **Probier es:** Lies alle vierzehn Wörter laut. Schaffst du es ohne Stockung, ist Katakana gefestigt.

## Hiragana und Katakana — Gesamtbilanz

| Schrift | Grundzeichen | Diakritika | Yōon / Specials | **Total** |
|---|---|---|---|---|
| **Hiragana** | 46 | 25 | 33 | **104** |
| **Katakana** | 46 | 25 + ー | 12 + 13 Specials | **96** |

**Insgesamt etwa 200 Kana-Zeichen** im Kopf — plus die Fähigkeit zu erkennen, welche Schrift wann verwendet wird (japanische Wörter → Hiragana, Lehnwörter/Eigennamen → Katakana, chinesische Konzepte → Kanji).

## Lerntipps für die nächsten Wochen

1. **Lies jeden Tag einen kurzen gemischten Text** — Hiragana und Katakana zusammen, wie sie in der Realität auftreten
2. **Schreibe einmal pro Woche beide Tabellen** aus dem Kopf — als Selbstcheck
3. **Gezielt Verwechslungspaare üben**: シ/ツ, ン/ソ (Katakana), わ/ね/れ, ぬ/め (Hiragana)
4. **Speisekarten und Werbung lesen** — die natürliche Übungsumgebung für gemischtes Material
5. **Achte auf Yōon im Hörverstehen** — kya, sha, cha sind schnell, dürfen nicht in zwei Schläge zerfallen

## Was kommt als Nächstes?

- **Vokabel-Lektionen** auf N5-Niveau (Familie, Tagesablauf, Restaurant, Zahlen, Reise) — du kannst direkt anfangen, da die Schriften jetzt lesbar sind
- **Erste Kanji** (chinesische Schriftzeichen) — N5-Liste hat ca. 80 Stück
- **Grammatik-Lektionen** — die Strukturen, die japanische Sätze zusammenhalten

**Du hast den ersten grossen Schwellenwert für japanisches Lesen erreicht. Hiragana und Katakana sind die Fundamente — und sie sind jetzt gelegt.** Glückwunsch!$TEXT$
WHERE id = 6499 AND lesson_id = 155;

-- =====================================================
-- TEIL B: Strichfolge fuer 25 Yōon/Special-Eintraege (kana 176-200)
-- Pattern: Grundzeichen + kleines Zeichen rechts unten
-- =====================================================

-- Standard-Yōon (kana 176-187)
UPDATE kana SET stroke_order_info='Yōon: キ (ki) + kleines ャ (ya) rechts unten. EINE Mora — als ein einziger Klang sprechen. Klein vs. gross: キャ (kya, 1 Mora) ≠ キヤ (ki-ya, 2 Moren).' WHERE id=176;
UPDATE kana SET stroke_order_info='Yōon: キ (ki) + kleines ュ (yu) rechts unten. EINE Mora.' WHERE id=177;
UPDATE kana SET stroke_order_info='Yōon: キ (ki) + kleines ョ (yo) rechts unten. EINE Mora.' WHERE id=178;
UPDATE kana SET stroke_order_info='Yōon: シ (shi) + kleines ャ (ya) rechts unten. EINE Mora — kompakt sha, nicht shi-ya.' WHERE id=179;
UPDATE kana SET stroke_order_info='Yōon: シ (shi) + kleines ュ (yu) rechts unten. EINE Mora — shu.' WHERE id=180;
UPDATE kana SET stroke_order_info='Yōon: シ (shi) + kleines ョ (yo) rechts unten. EINE Mora — sho.' WHERE id=181;
UPDATE kana SET stroke_order_info='Yōon: ジ (ji) + kleines ャ (ya) rechts unten. EINE Mora — ja. シ + Dakuten + kleines ya.' WHERE id=182;
UPDATE kana SET stroke_order_info='Yōon: ジ (ji) + kleines ュ (yu) rechts unten. EINE Mora — ju.' WHERE id=183;
UPDATE kana SET stroke_order_info='Yōon: ジ (ji) + kleines ョ (yo) rechts unten. EINE Mora — jo.' WHERE id=184;
UPDATE kana SET stroke_order_info='Yōon: チ (chi) + kleines ャ (ya) rechts unten. EINE Mora — cha (wie in Tee/chai).' WHERE id=185;
UPDATE kana SET stroke_order_info='Yōon: チ (chi) + kleines ュ (yu) rechts unten. EINE Mora — chu.' WHERE id=186;
UPDATE kana SET stroke_order_info='Yōon: チ (chi) + kleines ョ (yo) rechts unten. EINE Mora — cho (z.B. チョコ choko).' WHERE id=187;

-- Lehnwort-Spezialitaeten (kana 188-200)
UPDATE kana SET stroke_order_info='Lehnwort-Spezial: テ (te) + kleines ィ (i) rechts unten = ti. Ersetzt das alte チ (chi) fuer englisches t vor i. Beispiel: パーティー (party).' WHERE id=188;
UPDATE kana SET stroke_order_info='Lehnwort-Spezial: デ (de) + kleines ィ (i) rechts unten = di. Beispiel: ディズニー (Disney).' WHERE id=189;
UPDATE kana SET stroke_order_info='Lehnwort-Spezial: フ (fu) + kleines ァ (a) rechts unten = fa. Echtes /f/ aus Lehnwoertern. Beispiel: ファイル (file).' WHERE id=190;
UPDATE kana SET stroke_order_info='Lehnwort-Spezial: フ (fu) + kleines ィ (i) rechts unten = fi. Beispiel: フィッシュ (fish).' WHERE id=191;
UPDATE kana SET stroke_order_info='Lehnwort-Spezial: フ (fu) + kleines ェ (e) rechts unten = fe. Beispiel: カフェ (café).' WHERE id=192;
UPDATE kana SET stroke_order_info='Lehnwort-Spezial: フ (fu) + kleines ォ (o) rechts unten = fo. Beispiel: フォーク (fork).' WHERE id=193;
UPDATE kana SET stroke_order_info='Lehnwort-Spezial: ウ (u) + kleines ィ (i) rechts unten = wi. Moderner w-Klang. Beispiel: ウィーン (Wien).' WHERE id=194;
UPDATE kana SET stroke_order_info='Lehnwort-Spezial: ウ (u) + kleines ェ (e) rechts unten = we. Beispiel: ウェブ (web).' WHERE id=195;
UPDATE kana SET stroke_order_info='Lehnwort-Spezial: ウ (u) + kleines ォ (o) rechts unten = wo (NICHT die alte Partikel ヲ!). Beispiel: ウォーター (water), ウォッカ (Wodka).' WHERE id=196;
UPDATE kana SET stroke_order_info='Lehnwort-Spezial: ヴ (vu = ウ + Dakuten) + kleines ァ (a) rechts unten = va. Selten, oft durch バ (ba) ersetzt. Beispiel: ヴァイオリン (Violine).' WHERE id=197;
UPDATE kana SET stroke_order_info='Lehnwort-Spezial: ヴ + kleines ィ (i) = vi. Selten, oft durch ビ (bi) ersetzt.' WHERE id=198;
UPDATE kana SET stroke_order_info='Lehnwort-Spezial: ヴ + kleines ェ (e) = ve. Selten, oft durch ベ (be) ersetzt.' WHERE id=199;
UPDATE kana SET stroke_order_info='Lehnwort-Spezial: ヴ + kleines ォ (o) = vo. Selten, oft durch ボ (bo) ersetzt.' WHERE id=200;

-- Validierung
SELECT id, character, romanization, LEFT(stroke_order_info, 70) AS preview
FROM kana
WHERE id BETWEEN 176 AND 200
ORDER BY id;

SELECT id, page_number, order_index, LEFT(content_text, 60) AS preview, length(content_text) AS chars
FROM lesson_content
WHERE lesson_id = 155 AND content_type = 'text'
ORDER BY page_number, order_index;

COMMIT;
