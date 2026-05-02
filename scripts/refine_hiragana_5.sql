-- Refine N5 Hiragana 5 (Lesson ID 150) — Yoon
-- Erwartete Zeilen pro UPDATE: 1
-- Recherche: Tofugu, Wikipedia (Yōon, Japanese phonology)
-- Datum: 2026-05-02
SET client_encoding = 'UTF8';

BEGIN;

-- =====================================================
-- Stroke-Order fuer Yoon (kana IDs 72-104, 33 Kombinationen)
-- Format: "Strichanzahl X-Zeichen + Strich des kleinen ya/yu/yo"
-- Schreibreihenfolge: zuerst i-Zeichen komplett, dann kleines ya/yu/yo
-- =====================================================

-- K-Yoon (き + kleines ya/yu/yo)
UPDATE kana SET stroke_order_info='Schreib-Reihenfolge: zuerst alle 4 Striche von 「き」 (ki), dann das kleine 「ゃ」 (3 Striche). Das kleine ゃ steht **rechts unten** vom ki, etwa halb so gross wie ein normales や' WHERE id=72;
UPDATE kana SET stroke_order_info='Schreib-Reihenfolge: zuerst alle 4 Striche von 「き」 (ki), dann das kleine 「ゅ」 (2 Striche). Das kleine ゅ steht rechts unten, halb so gross wie ein normales ゆ' WHERE id=73;
UPDATE kana SET stroke_order_info='Schreib-Reihenfolge: zuerst alle 4 Striche von 「き」 (ki), dann das kleine 「ょ」 (2 Striche). Das kleine ょ steht rechts unten, halb so gross wie ein normales よ' WHERE id=74;

-- G-Yoon (ぎ + kleines ya/yu/yo)
UPDATE kana SET stroke_order_info='Schreib-Reihenfolge: zuerst alle 4 Striche von 「き」 + 2 Dakuten = 「ぎ」, dann das kleine 「ゃ」 (3 Striche). Total 9 Strichelemente, alle in einem Zeichen-Quadrat' WHERE id=75;
UPDATE kana SET stroke_order_info='Schreib-Reihenfolge: zuerst 「ぎ」 (gi mit Dakuten), dann das kleine 「ゅ」' WHERE id=76;
UPDATE kana SET stroke_order_info='Schreib-Reihenfolge: zuerst 「ぎ」 (gi mit Dakuten), dann das kleine 「ょ」' WHERE id=77;

-- S-Yoon (し + kleines ya/yu/yo) — Romaji ist sha/shu/sho, NICHT shya
UPDATE kana SET stroke_order_info='Schreib-Reihenfolge: zuerst der einzelne Strich von 「し」 (shi), dann das kleine 「ゃ」 (3 Striche). Klingt "scha" — Romaji "sha" ist die Hepburn-Schreibung, nicht "shya"' WHERE id=78;
UPDATE kana SET stroke_order_info='Schreib-Reihenfolge: zuerst 「し」 (shi), dann das kleine 「ゅ」. Klingt "schu" — Romaji "shu"' WHERE id=79;
UPDATE kana SET stroke_order_info='Schreib-Reihenfolge: zuerst 「し」 (shi), dann das kleine 「ょ」. Klingt "scho" — Romaji "sho"' WHERE id=80;

-- J-Yoon (じ + kleines ya/yu/yo)
UPDATE kana SET stroke_order_info='Schreib-Reihenfolge: zuerst 「し」 + 2 Dakuten = 「じ」 (ji), dann das kleine 「ゃ」. Klingt "dscha" wie englisch "ja" in *jam*. Romaji "ja", nicht "jya"' WHERE id=81;
UPDATE kana SET stroke_order_info='Schreib-Reihenfolge: zuerst 「じ」 (ji), dann das kleine 「ゅ」. Klingt "dschu" wie englisch "ju" in *jewel*' WHERE id=82;
UPDATE kana SET stroke_order_info='Schreib-Reihenfolge: zuerst 「じ」 (ji), dann das kleine 「ょ」. Klingt "dscho" wie deutsch "Joghurt"' WHERE id=83;

-- T-Yoon (ち + kleines ya/yu/yo) — Romaji cha/chu/cho
UPDATE kana SET stroke_order_info='Schreib-Reihenfolge: zuerst alle 2 Striche von 「ち」 (chi), dann das kleine 「ゃ」. Klingt "tscha" — Romaji "cha", nicht "chya"' WHERE id=84;
UPDATE kana SET stroke_order_info='Schreib-Reihenfolge: zuerst 「ち」 (chi), dann das kleine 「ゅ」. Klingt "tschu" — Romaji "chu"' WHERE id=85;
UPDATE kana SET stroke_order_info='Schreib-Reihenfolge: zuerst 「ち」 (chi), dann das kleine 「ょ」. Klingt "tscho" — Romaji "cho"' WHERE id=86;

-- N-Yoon (に + kleines ya/yu/yo)
UPDATE kana SET stroke_order_info='Schreib-Reihenfolge: zuerst alle 3 Striche von 「に」 (ni), dann das kleine 「ゃ」. Klingt "nja" — eine palatalisierte Silbe' WHERE id=87;
UPDATE kana SET stroke_order_info='Schreib-Reihenfolge: zuerst 「に」 (ni), dann das kleine 「ゅ」' WHERE id=88;
UPDATE kana SET stroke_order_info='Schreib-Reihenfolge: zuerst 「に」 (ni), dann das kleine 「ょ」' WHERE id=89;

-- H-Yoon (ひ + kleines ya/yu/yo)
UPDATE kana SET stroke_order_info='Schreib-Reihenfolge: zuerst der einzelne Strich von 「ひ」 (hi), dann das kleine 「ゃ」' WHERE id=90;
UPDATE kana SET stroke_order_info='Schreib-Reihenfolge: zuerst 「ひ」 (hi), dann das kleine 「ゅ」' WHERE id=91;
UPDATE kana SET stroke_order_info='Schreib-Reihenfolge: zuerst 「ひ」 (hi), dann das kleine 「ょ」' WHERE id=92;

-- B-Yoon (び + kleines ya/yu/yo)
UPDATE kana SET stroke_order_info='Schreib-Reihenfolge: zuerst 「ひ」 + 2 Dakuten = 「び」 (bi), dann das kleine 「ゃ」' WHERE id=93;
UPDATE kana SET stroke_order_info='Schreib-Reihenfolge: zuerst 「び」 (bi mit Dakuten), dann das kleine 「ゅ」' WHERE id=94;
UPDATE kana SET stroke_order_info='Schreib-Reihenfolge: zuerst 「び」 (bi mit Dakuten), dann das kleine 「ょ」' WHERE id=95;

-- P-Yoon (ぴ + kleines ya/yu/yo)
UPDATE kana SET stroke_order_info='Schreib-Reihenfolge: zuerst 「ひ」 + Handakuten-Kreis = 「ぴ」 (pi), dann das kleine 「ゃ」' WHERE id=96;
UPDATE kana SET stroke_order_info='Schreib-Reihenfolge: zuerst 「ぴ」 (pi mit Handakuten), dann das kleine 「ゅ」' WHERE id=97;
UPDATE kana SET stroke_order_info='Schreib-Reihenfolge: zuerst 「ぴ」 (pi mit Handakuten), dann das kleine 「ょ」' WHERE id=98;

-- M-Yoon (み + kleines ya/yu/yo)
UPDATE kana SET stroke_order_info='Schreib-Reihenfolge: zuerst alle 2 Striche von 「み」 (mi), dann das kleine 「ゃ」' WHERE id=99;
UPDATE kana SET stroke_order_info='Schreib-Reihenfolge: zuerst 「み」 (mi), dann das kleine 「ゅ」' WHERE id=100;
UPDATE kana SET stroke_order_info='Schreib-Reihenfolge: zuerst 「み」 (mi), dann das kleine 「ょ」' WHERE id=101;

-- R-Yoon (り + kleines ya/yu/yo)
UPDATE kana SET stroke_order_info='Schreib-Reihenfolge: zuerst alle 2 Striche von 「り」 (ri), dann das kleine 「ゃ」. R wird als Tap [ɾ] gesprochen' WHERE id=102;
UPDATE kana SET stroke_order_info='Schreib-Reihenfolge: zuerst 「り」 (ri), dann das kleine 「ゅ」' WHERE id=103;
UPDATE kana SET stroke_order_info='Schreib-Reihenfolge: zuerst 「り」 (ri), dann das kleine 「ょ」' WHERE id=104;

-- =====================================================
-- Text-Bloecke
-- =====================================================

-- Page 1, Block 1 (id=6326): Einfuehrung
UPDATE lesson_content SET content_text = $TEXT$## Wo stehst du jetzt?

Nach **vier Hiragana-Lektionen** kennst du:

- **46 Grundzeichen** (Hiragana 1, 2, 3)
- **25 modifizierte Zeichen** mit Dakuten und Handakuten (Hiragana 4)
- **= 71 Hiragana** insgesamt

In dieser **letzten Hiragana-Lektion** lernst du den letzten Baustein: **Yōon** — das sind **kombinierte Silben** aus zwei Zeichen, die als **eine Mora** zählen.

## Was ist ein Yōon?

Ein Yōon entsteht, wenn ein **i-Zeichen** (z.B. き, し, ち, に, ひ, み, り) mit einem **kleinen や/ゆ/よ** kombiniert wird. Phonetisch nennt man das **Palatalisierung** — der Konsonant wird mit einem y-Gleitlaut "weicher gemacht":

- **き** (ki) + **ゃ** (kleines ya) = **きゃ** (kya, klingt wie [kʲa])
- **し** (shi) + **ゅ** (kleines yu) = **しゅ** (shu)
- **ち** (chi) + **ょ** (kleines yo) = **ちょ** (cho)

> **Tofugu-Faustregel:** "**Drop the i-sound.**" Du nimmst das i-Zeichen, lässt das "i" weg, und hängst direkt das ya/yu/yo dran. ki → k(i) → k+ya = kya. Funktioniert für alle Yōon.

> **Wichtig — Mora statt Silbe:** Ein Yōon ist **eine Mora**, nicht zwei. Das ist mehr als ein technisches Detail: Mora ist die japanische Zähleinheit für **Sprachrhythmus, Pitch-Accent und Haiku** (das berühmte 5-7-5-Schema zählt Mora, nicht Silben). Vergleich:
>
> - 「きや」 = ki + ya = **2 Mora** (z.B. ein Mädchenname)
> - 「きゃ」 = kya = **1 Mora** (Anfang von "kyaku" = Gast)

## Wie viele Yōon gibt es?

**Sieben Konsonantenpaare** können Yōon bilden: K, S, T, N, H, M, R. Jeder wird mit ya/yu/yo kombiniert — das macht **21 Grund-Yōon**. Dazu kommen:

- **Dakuten-Varianten**: ぎ/じ/び + ya/yu/yo → 9 weitere
- **Handakuten-Variante**: ぴ + ya/yu/yo → 3 weitere

Gesamt: **33 Yōon** in der Standard-Tabelle.

> **Theoretisch existieren noch:** ぢゃ/ぢゅ/ぢょ (D-Reihe-Yōon, klingen identisch wie じゃ/じゅ/じょ wegen Yotsugana). Du wirst sie fast nie sehen — wenn doch, gilt dieselbe じ/ず-Standardregel wie in Hiragana 4.

## Was kannst du danach?

Mit Yōon liest du Wörter wie:

- 「きょう」 (kyou, 'heute')
- 「しゃしん」 (shashin, 'Foto')
- 「ちゅうごく」 (chuugoku, 'China')
- 「びょういん」 (byouin, 'Krankenhaus')
- 「りょこう」 (ryokou, 'Reise')

Danach hast du **Hiragana komplett im Griff** — bereit für echtes Japanisch.$TEXT$
WHERE id = 6326 AND lesson_id = 150;

-- Page 2, Block 1 (id=6327): K- + G-Yoon
UPDATE lesson_content SET content_text = $TEXT$## K-Yōon — kya, kyu, kyo

Entsteht aus **き** (ki) + kleinem ya/yu/yo. Phonetisch eine **palatalisierte K-Silbe** — die Zungenmitte wird zum Gaumen angehoben:

- **きゃ (kya)** — wie "kja" mit weichem k, eine Silbe (1 Mora)
- **きゅ (kyu)** — wie "kjü" ohne Lippenrundung
- **きょ (kyo)** — wie "kjo", endet das Wort *Tokyo* (toh-**kyoh**)

> **Mini-Wörter:** 「きょう」 (kyou, 'heute'), 「きゃく」 (kyaku, 'Gast'), 「きゅう」 (kyuu, '9' / 'plötzlich'), 「とうきょう」 (toukyou, 'Tokyo').

## Dakuten-Variante: G-Yōon (gya, gyu, gyo)

Mit Dakuten auf き → ぎ:

- **ぎゃ (gya)** — wie "gja" mit weichem g
- **ぎゅ (gyu)** — wie "gjü"
- **ぎょ (gyo)** — wie "gjo"

> **Beispiele:** 「ぎゅうにゅう」 (gyuunyuu, 'Milch'), 「ぎゃく」 (gyaku, 'Gegenteil'), 「ぎょうざ」 (gyouza, 'Teigtaschen').$TEXT$
WHERE id = 6327 AND lesson_id = 150;

-- Page 2, Block 2 (id=6334): S- + J-Yoon
UPDATE lesson_content SET content_text = $TEXT$## S-Yōon — sha, shu, sho

Entsteht aus **し** (shi) + kleinem ya/yu/yo. **Wichtig:** Romaji ist **sha/shu/sho**, NICHT 'shya/shyu/shyo' — die Hepburn-Schreibung lässt das y weg, weil "sh" schon palatalisiert ist:

- **しゃ (sha)** wie deutsch *Schale* — ein einzelner sch-Laut + a, EINE Silbe
- **しゅ (shu)** wie deutsch *Schule* (kurz, mit unrundiertem u)
- **しょ (sho)** wie deutsch *schon*

> **Mini-Wörter:** 「しゃしん」 (shashin, 'Foto'), 「しゅくだい」 (shukudai, 'Hausaufgabe'), 「じしょ」 (jisho, 'Wörterbuch').

## Dakuten-Variante: J-Yōon — ja, ju, jo

Aus **じ** (ji) + ya/yu/yo. Romaji ist **ja/ju/jo**, nicht 'jya/jyu/jyo':

- **じゃ (ja)** — wie englisches *jam* — ein dsch-Laut, EINE Silbe
- **じゅ (ju)** — wie englisches *jewel*
- **じょ (jo)** — wie deutsch *Joghurt*

> **Phonetik-Hinweis:** Genauso wie じ allein ist じゃ am Wortanfang ein **Affrikat** [d͡ʑa], in Wortmitte mehr Frikativ [ʑa]. Du musst diesen Unterschied nicht aktiv lernen, aber er erklärt das natürliche Klanggefühl.

> **Mini-Wörter:** 「じゃあ」 (jaa, 'also dann'), 「じゅう」 (juu, '10'), 「じょうず」 (jouzu, 'geschickt'), 「じゅぎょう」 (jugyou, 'Unterricht').$TEXT$
WHERE id = 6334 AND lesson_id = 150;

-- Page 2, Block 3 (id=6341): T-Yoon
UPDATE lesson_content SET content_text = $TEXT$## T-Yōon — cha, chu, cho

Entsteht aus **ち** (chi) + kleinem ya/yu/yo. Romaji ist **cha/chu/cho**, nicht 'chya/chyu/chyo' (gleiche Hepburn-Logik wie sha):

- **ちゃ (cha)** wie englisch *chair* — ein tsch-Laut + a, EINE Silbe
- **ちゅ (chu)** wie englisch *choose* (kurz)
- **ちょ (cho)** wie *Tschechien* (etwa)

> **Mini-Wörter:** 「おちゃ」 (ocha, 'Tee'), 「ちゅうごく」 (chuugoku, 'China'), 「ちょっと」 (chotto, 'ein bisschen'), 「ちゃいろ」 (chairo, 'braun').

> **Achtung:** ぢゃ/ぢゅ/ぢょ existieren theoretisch (Dakuten auf ち), kommen aber **fast nie** vor — du kannst sie ignorieren. In den seltenen Fällen klingen sie identisch wie じゃ/じゅ/じょ (Yotsugana-Phänomen aus Hiragana 4).$TEXT$
WHERE id = 6341 AND lesson_id = 150;

-- Page 2, Block 4 (id=6345): N/H/B/P/M/R-Yoon
UPDATE lesson_content SET content_text = $TEXT$## Die restlichen Yōon-Gruppen

Gleiches Muster — i-Zeichen + kleines ya/yu/yo (immer "drop the i-sound"):

- **に (ni)** → **にゃ/にゅ/にょ** (nya/nyu/nyo) — palatalisiertes n
- **ひ (hi)** → **ひゃ/ひゅ/ひょ** (hya/hyu/hyo) — palatalisiertes h
- **び (bi)** → **びゃ/びゅ/びょ** (bya/byu/byo) — palatalisiertes b
- **ぴ (pi)** → **ぴゃ/ぴゅ/ぴょ** (pya/pyu/pyo) — palatalisiertes p (selten)
- **み (mi)** → **みゃ/みゅ/みょ** (mya/myu/myo) — palatalisiertes m
- **り (ri)** → **りゃ/りゅ/りょ** (rya/ryu/ryo) — palatalisierter Tap

> **Mini-Wörter:**
> - 「びょういん」 (byouin, 'Krankenhaus')
> - 「りょこう」 (ryokou, 'Reise')
> - 「ひゃく」 (hyaku, '100')
> - 「みょうじ」 (myouji, 'Nachname')
> - 「にゅうがく」 (nyuugaku, 'Eintritt in eine Schule')
> - 「ぴょんぴょん」 (pyonpyon, 'hüpfend' — Onomatopoetikum)

## Was du dir merken musst

Nicht alle Yōon kommen gleich häufig vor. **Häufigste in N5/N4-Texten** sind:

- **Sehr häufig**: きゃ/きゅ/きょ, しゃ/しゅ/しょ, じゃ/じゅ/じょ, ちゃ/ちゅ/ちょ
- **Häufig**: ひゃ, ひょ, びょ, りょ, ぎゅ, ぎょ
- **Seltener**: にゃ/にゅ/にょ, ぴゃ/ぴゅ/ぴょ (oft nur in Lehnwörtern oder Onomatopoetika), みゃ/みゅ (sehr selten)

Konzentriere dich beim Lernen auf die häufigen — die seltenen sitzen mit der Zeit von selbst, sobald du Vokabeln liest.$TEXT$
WHERE id = 6345 AND lesson_id = 150;

-- Page 3, Block 1 (id=6364): Aussprache & Schreibhinweise
UPDATE lesson_content SET content_text = $TEXT$## Die wichtigsten Regeln

**Yōon = EINE Mora.** Wenn du 「きゃ」 (kya) siehst, sprichst du **eine Zähleinheit** — nicht "ki-ya". Diese Mora-Zählung ist **nicht** dasselbe wie westliche Silben. Sie ist die Basis für:

- **Pitch-Accent** im Japanischen (welche Mora ist hoch/tief)
- **Haiku** (klassisches 5-7-5-Schema zählt Mora, nicht Silben)
- **Sprachrhythmus** beim Hören und Lesen

Faustregel: Yōon zählt wie ein Grundzeichen. 「きょう」 (kyou) hat **2 Mora** (kyo + u), nicht 3.

**Das kleine や/ゆ/よ ist sichtbar kleiner.** In gedruckten Texten steht es klar als kleineres Zeichen rechts unten neben dem i-Zeichen — ungefähr **halb so gross** wie ein normales や/ゆ/よ. In Handschrift kann der Grössenunterschied subtil sein — pass auf.

**Romaji-Schreibweise (Hepburn):** Yōon werden **kompakt** geschrieben:

- き + ゃ → **kya** (nicht 'kiya' und nicht 'kyya')
- し + ゃ → **sha** (nicht 'shya' — das y ist im "sh" schon eingebaut)
- ち + ゃ → **cha** (nicht 'chya' — gleicher Grund)
- じ + ゃ → **ja** (nicht 'jya')

Tofugu nennt das die "**drop-the-i-sound**"-Regel: ki + ya → k + ya = kya.

## Phonetisch: Was passiert beim Yōon?

Beim Yōon wird der vorhergehende Konsonant **palatalisiert** — die Zungenmitte hebt sich zum harten Gaumen. In IPA:

- /kj/ → [kʲ] (palatalisiertes k, wie in きゃ)
- /nj/ → [ɲ] (palatales n, ähnlich wie spanisches ñ in *señor*)
- /rj/ → [ɾʲ] (palatalisierter Tap)

Du musst diese phonetische Theorie nicht aktiv lernen — sie erklärt nur, warum Yōon nicht einfach "ki + ya" sind, sondern als eine zusammenhängende, weiche Silbe klingen.

## Verwechslungsgefahr — gross vs. klein

Das grösste Stolperthema bei Yōon ist die **Grössenunterscheidung**. Und es ist **nicht nur Kosmetik** — die Bedeutung ändert sich:

| Schreibweise | Lesung | Mora | Bedeutung |
|---|---|---|---|
| 「きや」 | ki-ya | 2 | Mädchenname, oder "(Schreib-)Tisch" |
| 「きゃ」 | kya | 1 | Anfang von "kyaku" (Gast) |
| 「びよういん」 | bi-you-in | 4 | Schönheitssalon (美容院) |
| 「びょういん」 | byou-in | 3 | Krankenhaus (病院) |
| 「じゆう」 | ji-yuu | 3 | Freiheit (自由) |
| 「じゅう」 | juu | 2 | Zehn (十) |

> **Praktischer Tipp:** Wenn der Sinn nicht passt, prüfe, ob da ein **kleines** や/ゆ/よ stehen sollte. Computer-Schriften machen den Unterschied klar — Handschrift kann tückisch sein. Bei Lehrtexten wird das kleine ゃ/ゅ/ょ oft zusätzlich tiefer gestellt.

## Welche Konsonanten machen Yōon?

Nur **i-Zeichen** können Yōon bilden:

- **K-Gruppe**: き → きゃ/きゅ/きょ
- **G-Gruppe**: ぎ → ぎゃ/ぎゅ/ぎょ
- **S-Gruppe**: し → しゃ/しゅ/しょ
- **J-Gruppe**: じ → じゃ/じゅ/じょ
- **CH-Gruppe**: ち → ちゃ/ちゅ/ちょ
- **N-Gruppe**: に → にゃ/にゅ/にょ
- **H-Gruppe**: ひ → ひゃ/ひゅ/ひょ
- **B-Gruppe**: び → びゃ/びゅ/びょ
- **P-Gruppe**: ぴ → ぴゃ/ぴゅ/ぴょ
- **M-Gruppe**: み → みゃ/みゅ/みょ
- **R-Gruppe**: り → りゃ/りゅ/りょ

**Andere Vokale** (a, u, e, o, ya, yu, yo, wa, wo, n) **können kein Yōon bilden** — nur die i-Zeichen. Das liegt an der Phonologie: nur i-Vokale assimilieren natürlich mit dem y-Gleitlaut.

## Strichfolge

Beim Schreiben gilt: **zuerst das i-Zeichen vollständig, dann das kleine ya/yu/yo daneben**. Keine Querstriche zwischen den beiden — sie bleiben optisch zwei Zeichen, die zusammen eine Silbe bilden.

Beispiel きゃ:
1. Alle 4 Striche von 「き」 (ki)
2. Die 3 Striche des kleinen 「ゃ」 (rechts unten, halb so gross)

## Tipp zum Üben

**Lies kurze Wörter mit Yōon laut:**

- 「きょう」 (kyou) — heute
- 「ぎゅうにゅう」 (gyuunyuu) — Milch
- 「しゃしん」 (shashin) — Foto
- 「じゃあ」 (jaa) — also dann
- 「ちゃいろ」 (chairo) — braun
- 「ひゃく」 (hyaku) — 100
- 「びょういん」 (byouin) — Krankenhaus
- 「りょうり」 (ryouri) — Kochen, Gericht

Wenn du diese acht Wörter flüssig liest, beherrschst du den Kern der Yōon. Die seltenen Yōon (にゃ, みょ, ぴゅ, etc.) lernst du ganz natürlich, wenn du sie in Vokabeln triffst.$TEXT$
WHERE id = 6364 AND lesson_id = 150;

-- Page 4, Block 1 (id=6365): Quiz-Vorlauf
UPDATE lesson_content SET content_text = $TEXT$## Teste dein Wissen

Gleich kommen **Fragen** zu den Yōon-Silben.

- **Multiple-Choice:** Welche Romaji passt?
- **Richtig/Falsch:** Stimmt die Aussage zu Yōon?
- **Wort-Lesung & Bedeutung:** Welches Wort siehst du?
- **Matching:** Verbinde Yōon mit Lesung

> **Tipp:** Achte auf den Unterschied **gross** 「や」 (ya) / 「ゆ」 (yu) / 「よ」 (yo) vs. **klein** 「ゃ」 (kleines ya) / 「ゅ」 (kleines yu) / 「ょ」 (kleines yo). Yōon = 1 Mora, gross ya/yu/yo = 2 Mora — das macht oft den Bedeutungsunterschied (びょういん vs びよういん).$TEXT$
WHERE id = 6365 AND lesson_id = 150;

-- Page 5, Block 1 (id=6366): Zusammenfassung
UPDATE lesson_content SET content_text = $TEXT$## Geschafft — Hiragana ist KOMPLETT

Nach **fünf Lektionen** beherrschst du das gesamte Hiragana-System:

- **Hiragana 1:** Vokale + K-Reihe + S-Reihe (15 Zeichen)
- **Hiragana 2:** T-Reihe + N-Reihe + H-Reihe (15 Zeichen)
- **Hiragana 3:** M-Reihe + Y-Reihe + R-Reihe + W-Reihe + ん (16 Zeichen)
- **Hiragana 4:** Diakritika — G/Z/D/B/P-Reihen (25 Zeichen)
- **Hiragana 5:** Yōon — kombinierte Silben (33 Yōon)

Insgesamt: **104 Hiragana-Zeichen/-Kombinationen**, alle Mora-zählend.

## Die wichtigsten Punkte aus dieser Lektion

1. **Yōon = 1 Mora**, nicht 2. Wichtig für Pitch-Accent und Haiku.
2. **Drop-the-i-sound**: ki + ya → kya (Tofugu-Regel).
3. **Romaji**: Hepburn lässt das y weg bei sh/ch/j (sha, cha, ja — nicht shya, chya, jya).
4. **Klein vs. gross** verändert Bedeutung: びょういん (Krankenhaus) ≠ びよういん (Schönheitssalon).
5. **Nur i-Zeichen** bilden Yōon (k/g/s/j/ch/n/h/b/p/m/r — die i-Form jeder Reihe).
6. **Phonetisch**: palatalisierte Konsonanten ([kʲ], [ɲ], [ɾʲ]).

## Was bedeutet das konkret?

Du kannst jetzt **jeden** japanischen Text lesen, der nur Hiragana verwendet — und das ist die übliche Lehrform für Anfänger. Kinderbücher, einfache Lehrtexte, Übungen — alles offen.

## Alltagswörter, die du jetzt sicher liest

- 「ありがとう」 (arigatou) — danke
- 「おはよう」 (ohayou) — guten Morgen
- 「こんにちは」 (konnichiwa) — guten Tag
- 「すみません」 (sumimasen) — Entschuldigung
- 「がっこう」 (gakkou) — Schule
- 「だいがく」 (daigaku) — Universität
- 「びょういん」 (byouin) — Krankenhaus (Yōon!)
- 「ぎゅうにゅう」 (gyuunyuu) — Milch (Yōon!)
- 「しゃしん」 (shashin) — Foto (Yōon!)
- 「ちゅうごく」 (chuugoku) — China (Yōon!)
- 「りょこう」 (ryokou) — Reise (Yōon!)
- 「きょう」 (kyou) — heute (Yōon!)

> **Probier es:** Lies alle zwölf Wörter laut, ohne Romaji. Schaffst du es ohne Stockung, ist Hiragana gefestigt.

## Lerntipps für die nächsten Wochen

1. **Lies jeden Tag einen kurzen Hiragana-Text laut** — Kinderlieder oder einfache Mangas eignen sich gut
2. **Schreibe einmal pro Woche die ganze Tabelle** mit allen 71 Grund- und Diakritika-Zeichen + häufigen Yōon — als Selbstcheck
3. **Übe gezielt die Verwechslungspaare**: わ/ね/れ, め/ぬ, は/ば/ぱ, きゃ/きや
4. **Lies Wörter, nicht Zeichen** — Geschwindigkeit kommt durch Wort-Wiedererkennung, nicht durch Buchstabieren
5. **Achte auf Mora-Zählung** beim Hören — じゅう (juu, 10) ist 2 Mora, じゆう (jiyuu, Freiheit) ist 3

## Was kommt als Nächstes?

- **Katakana** — das **zweite** japanische Schriftsystem. Wird vor allem für **Lehnwörter** (Kaffee, Computer, Deutschland), **Eigennamen** und **Tier-/Pflanzennamen** verwendet. Fünf Lektionen mit derselben Struktur wie bei Hiragana.
- **Vokabel-Lektionen** auf N5-Niveau — Familie, Tagesablauf, Restaurant, Zahlen, Reise. Du kannst direkt mit ihnen anfangen, da sie nun lesbar werden.
- Später: erste **Kanji** (die chinesischen Schriftzeichen) — N5-Liste hat ca. 80 Stück.

**Du hast den ersten echten Meilenstein erreicht.** Hiragana ist die wichtigste Grundlage für alles, was kommt — und du beherrschst sie jetzt. **Glückwunsch!**$TEXT$
WHERE id = 6366 AND lesson_id = 150;

-- Validierung
SELECT id, page_number, order_index, LEFT(content_text, 60) AS preview, length(content_text) AS chars
FROM lesson_content WHERE lesson_id = 150 AND content_type = 'text' ORDER BY page_number, order_index;
SELECT COUNT(*) FROM kana WHERE id BETWEEN 72 AND 104 AND stroke_order_info IS NOT NULL;

COMMIT;
