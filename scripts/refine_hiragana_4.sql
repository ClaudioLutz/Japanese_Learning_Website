-- Refine N5 Hiragana 4 (Lesson ID 149) — Dakuten/Handakuten
-- Erwartete Zeilen pro UPDATE: 1
-- Recherche: Tofugu, Wikipedia (Dakuten and handakuten, Hiragana, Yotsugana, Rendaku),
-- portugiesische Jesuiten (Rakuyōshū 1598), japanische Phonologie
-- Datum: 2026-05-02
SET client_encoding = 'UTF8';

BEGIN;

-- =====================================================
-- Stroke-Order fuer Dakuten/Handakuten (kana IDs 47-71)
-- Strichzahl = Grundzeichen + 2 (Dakuten) bzw. + 1 (Handakuten)
-- =====================================================

-- G-Reihe (K + Dakuten ゛)
UPDATE kana SET stroke_order_info='5 Striche: alle 3 Striche von 「か」 (ka) + 2 kleine Striche oben rechts (Dakuten). Die Dakuten-Striche werden ZULETZT geschrieben, im 45-Grad-Winkel von links unten nach rechts oben' WHERE id=47;
UPDATE kana SET stroke_order_info='6 Striche: alle 4 Striche von 「き」 (ki) + 2 Dakuten-Striche oben rechts (45-Grad-Winkel)' WHERE id=48;
UPDATE kana SET stroke_order_info='3 Striche: alle 1 Strich von 「く」 (ku) + 2 Dakuten-Striche oben rechts' WHERE id=49;
UPDATE kana SET stroke_order_info='5 Striche: alle 3 Striche von 「け」 (ke) + 2 Dakuten-Striche oben rechts' WHERE id=50;
UPDATE kana SET stroke_order_info='4 Striche: alle 2 Striche von 「こ」 (ko) + 2 Dakuten-Striche oben rechts' WHERE id=51;

-- Z-Reihe (S + Dakuten)
UPDATE kana SET stroke_order_info='5 Striche: alle 3 Striche von 「さ」 (sa) + 2 Dakuten-Striche oben rechts' WHERE id=52;
UPDATE kana SET stroke_order_info='3 Striche: 1 Strich von 「し」 (shi) + 2 Dakuten-Striche oben rechts. Aussprache: Affrikat [d͡ʑi] am Wortanfang, Frikativ [ʑi] in Wortmitte' WHERE id=53;
UPDATE kana SET stroke_order_info='4 Striche: alle 2 Striche von 「す」 (su) + 2 Dakuten-Striche oben rechts. Aussprache: Affrikat [d͡zu] am Wortanfang, Frikativ [zu] in Wortmitte' WHERE id=54;
UPDATE kana SET stroke_order_info='5 Striche: alle 3 Striche von 「せ」 (se) + 2 Dakuten-Striche oben rechts' WHERE id=55;
UPDATE kana SET stroke_order_info='3 Striche: 1 Strich von 「そ」 (so) + 2 Dakuten-Striche oben rechts' WHERE id=56;

-- D-Reihe (T + Dakuten) — Achtung: ぢ und づ
UPDATE kana SET stroke_order_info='6 Striche: alle 4 Striche von 「た」 (ta) + 2 Dakuten-Striche oben rechts' WHERE id=57;
UPDATE kana SET stroke_order_info='4 Striche: alle 2 Striche von 「ち」 (chi) + 2 Dakuten-Striche oben rechts. Aussprache: identisch mit 「じ」 (ji), aber nur in Rendaku-Komposita verwendet (z.B. 「はなぢ」 hanaji "Nasenbluten")' WHERE id=58;
UPDATE kana SET stroke_order_info='3 Striche: 1 Strich von 「つ」 (tsu) + 2 Dakuten-Striche oben rechts. Aussprache: identisch mit 「ず」 (zu), aber nur in Rendaku-Komposita (z.B. 「つづく」 tsuzuku "fortsetzen")' WHERE id=59;
UPDATE kana SET stroke_order_info='3 Striche: 1 Strich von 「て」 (te) + 2 Dakuten-Striche oben rechts' WHERE id=60;
UPDATE kana SET stroke_order_info='4 Striche: alle 2 Striche von 「と」 (to) + 2 Dakuten-Striche oben rechts' WHERE id=61;

-- B-Reihe (H + Dakuten)
UPDATE kana SET stroke_order_info='5 Striche: alle 3 Striche von 「は」 (ha) + 2 Dakuten-Striche oben rechts. Achtung: は/ば/ぱ unterscheiden sich NUR durch das Diakritikum oben rechts!' WHERE id=62;
UPDATE kana SET stroke_order_info='3 Striche: 1 Strich von 「ひ」 (hi) + 2 Dakuten-Striche oben rechts' WHERE id=63;
UPDATE kana SET stroke_order_info='6 Striche: alle 4 Striche von 「ふ」 (fu) + 2 Dakuten-Striche oben rechts. Aussprache: ふ ist bilabial weich, ぶ ist klares b' WHERE id=64;
UPDATE kana SET stroke_order_info='3 Striche: 1 Strich von 「へ」 (he) + 2 Dakuten-Striche oben rechts' WHERE id=65;
UPDATE kana SET stroke_order_info='6 Striche: alle 4 Striche von 「ほ」 (ho) + 2 Dakuten-Striche oben rechts' WHERE id=66;

-- P-Reihe (H + Handakuten ゜)
UPDATE kana SET stroke_order_info='4 Striche: alle 3 Striche von 「は」 (ha) + 1 kleiner Kreis oben rechts (Handakuten). Der Kreis wird als letzter Strich gemalt — eine geschlossene runde Form' WHERE id=67;
UPDATE kana SET stroke_order_info='2 Striche: 1 Strich von 「ひ」 (hi) + 1 Handakuten-Kreis oben rechts' WHERE id=68;
UPDATE kana SET stroke_order_info='5 Striche: alle 4 Striche von 「ふ」 (fu) + 1 Handakuten-Kreis oben rechts' WHERE id=69;
UPDATE kana SET stroke_order_info='2 Striche: 1 Strich von 「へ」 (he) + 1 Handakuten-Kreis oben rechts' WHERE id=70;
UPDATE kana SET stroke_order_info='5 Striche: alle 4 Striche von 「ほ」 (ho) + 1 Handakuten-Kreis oben rechts' WHERE id=71;

-- =====================================================
-- Text-Bloecke
-- =====================================================

-- Page 1, Block 1 (id=6292): Einfuehrung
UPDATE lesson_content SET content_text = $TEXT$## Wo stehst du jetzt?

Nach **Hiragana 1, 2 und 3** kennst du alle **46 Grundzeichen**. Doch das ist erst der erste Teil — die japanische Schrift kennt noch **Diakritika**, also kleine Markierungen, die einen Konsonanten **härter oder weicher** machen.

## Was lernst du jetzt?

In dieser Lektion lernst du **zwei Markierungen**:

1. **Dakuten** 「゛」 — zwei kleine Striche oben rechts. Macht stimmlose Konsonanten **stimmhaft**:
   - **K → G**: 「か」 (ka) → 「が」 (ga)
   - **S → Z**: 「さ」 (sa) → 「ざ」 (za)
   - **T → D**: 「た」 (ta) → 「だ」 (da)
   - **H → B**: 「は」 (ha) → 「ば」 (ba)
2. **Handakuten** 「゜」 — ein kleiner Kreis oben rechts. Wirkt nur auf die **H-Reihe** und macht daraus die **P-Reihe**:
   - **H → P**: 「は」 (ha) → 「ぱ」 (pa)

## Wie viele neue Zeichen?

Dakuten erzeugt **20 neue Zeichen** (4 Reihen × 5), Handakuten **5 neue Zeichen** (1 Reihe × 5) — zusammen **25 modifizierte Hiragana**.

> **Gute Nachricht:** Du musst keine **neuen Formen** lernen. Die Grundzeichen kennst du schon — es kommen nur die kleinen Markierungen dazu. Wenn du 「か」 (ka) liest, liest du auch 「が」 (ga) sofort.

## Geschichtlicher Hintergrund

**Dakuten** existieren seit dem **9. Jahrhundert** — sie entstanden aus chinesischen Tonzeichen und wurden über buddhistische Texte verbreitet. **Handakuten** dagegen sind eine **Erfindung portugiesischer Jesuiten**, die im Wörterbuch *Rakuyōshū* (1598) erstmals den kleinen Kreis einführten — um in christlichen Texten den **/p/-Laut** klar zu markieren. Bis dahin musste man aus dem Kontext erschliessen, ob ein は als "ha", "ba" oder "pa" zu lesen war.

## Was kannst du danach?

Mit Diakritika liest du Wörter wie:

- 「がっこう」 (gakkou, 'Schule')
- 「ぞう」 (zou, 'Elefant')
- 「だいがく」 (daigaku, 'Universität')
- 「ばんごう」 (bangou, 'Nummer')
- 「ぱん」 (pan, 'Brot')

Die meisten alltäglichen Vokabeln nutzen Diakritika — sie sind also **unverzichtbar**.$TEXT$
WHERE id = 6292 AND lesson_id = 149;

-- Page 2, Block 1 (id=6293): G-Reihe
UPDATE lesson_content SET content_text = $TEXT$## G-Reihe — K mit Dakuten

Die K-Reihe wird mit zwei kleinen Strichen 「゛」 zur G-Reihe. **Stimmhaftes** g wie im Deutschen:

- **が (ga)** wie in *Gabel*
- **ぎ (gi)** wie in *Gips*
- **ぐ (gu)** wie in *Gurke* (kurz, mit unrundiertem u)
- **げ (ge)** wie in *Geld*
- **ご (go)** wie in *Gott*

> **Phonetik-Detail — Nasalierung:** Im **älteren Tokyo-Standard** wird die G-Reihe **in Wortmitte oft nasaliert** zu einem **velaren Nasal [ŋ]** (wie das deutsche "ng" in *Singer*). Beispiele: 「かぎ」 (kagi, 'Schlüssel') klingt für ältere Sprecher wie "ka-**ngi**", 「ありがとう」 wie "ari-**ngat**ou". Bei jüngeren Sprechern und in formellen Medien hört man heute meist das normale [g]. **Lerner müssen die Nasalierung nicht produzieren — aber sie sollten sie wiedererkennen** im JLPT-Hörverstehen.

> **Mini-Wörter:** 「がっこう」 (gakkou, 'Schule'), 「ぎんこう」 (ginkou, 'Bank'), 「ごはん」 (gohan, 'Reis/Mahlzeit'), 「げつようび」 (getsuyoubi, 'Montag'), 「ぐち」 (guchi, 'Klage').$TEXT$
WHERE id = 6293 AND lesson_id = 149;

-- Page 2, Block 2 (id=6299): Z-Reihe
UPDATE lesson_content SET content_text = $TEXT$## Z-Reihe — S mit Dakuten

Die S-Reihe wird zur Z-Reihe — **stimmhafter** s-Laut. Aber Achtung: Die Aussprache hängt von der **Position im Wort** ab.

- **ざ (za)** — am Wortanfang **Affrikat [d͡za]** (wie "ds" in *abds-Pause* mit a), in Wortmitte Frikativ [za] (wie englisches *zap*)
- **じ (ji)** ⚠ — die berühmte Ausnahme! 「し」 (shi) → 「じ」 (ji), gesprochen **"dschi"** wie in *Jeans* (am Wortanfang Affrikat [d͡ʑi], in Wortmitte [ʑi]). NICHT wie deutsches "zi".
- **ず (zu)** — am Wortanfang Affrikat **[d͡zu]** (wie "ds-u"), in Wortmitte [zu]. Auch hier mit unrundiertem u.
- **ぜ (ze)** wie in englischem *zebra*
- **ぞ (zo)** wie in englischem *zone*

> **Affrikat vs. Frikativ — was heisst das?**
> - **Affrikat**: zwei Laute werden zu einem verschmolzen (z.B. "ds" am Wortanfang)
> - **Frikativ**: ein gleitender Reibelaut (z.B. nur "z" zwischen Vokalen)
>
> Du musst diese Unterscheidung nicht aktiv lernen — aber sie erklärt, warum sich 「じかん」 (jikan, "Zeit") am Anfang anders anfühlt als 「みじかい」 (mijikai, "kurz") in der Mitte.

> **Mini-Wörter:** 「ぞう」 (zou, 'Elefant'), 「じかん」 (jikan, 'Zeit'), 「みず」 (mizu, 'Wasser'), 「ぜんぶ」 (zenbu, 'alles'), 「かぞく」 (kazoku, 'Familie').$TEXT$
WHERE id = 6299 AND lesson_id = 149;

-- Page 2, Block 3 (id=6305): D-Reihe
UPDATE lesson_content SET content_text = $TEXT$## D-Reihe — T mit Dakuten

Die T-Reihe wird zur D-Reihe. Aber **Achtung** — diese Reihe enthält die **zwei Yotsugana-Doppelgänger**:

- **だ (da)** wie in *Dame*
- **ぢ (ji)** ⚠ — klingt **identisch** wie 「じ」 (Z-Reihe). Sehr selten.
- **づ (zu)** ⚠ — klingt **identisch** wie 「ず」 (Z-Reihe). Sehr selten.
- **で (de)** wie in *Decke*
- **ど (do)** wie in *Dose*

## Wann benutzt man ぢ und づ?

「ぢ」 und 「づ」 klingen genau wie 「じ」 und 「ず」 — sie kommen aber **nur in zwei Spezialfällen** vor. Das ist die Standard-Regel der modernen Rechtschreibung (1946):

**1. Rendaku — sequenzielle Stimmhaftmachung in Komposita:**
Wenn das **zweite Morphem** eines zusammengesetzten Wortes mit 「ち」 (chi) oder 「つ」 (tsu) beginnt und durch die Komposition stimmhaft wird, schreibt man **ぢ** bzw. **づ** statt じ/ず — um die etymologische Herkunft zu bewahren.

- 「はな」 (hana, "Nase") + 「ち」 (chi, "Blut") → 「はなぢ」 (hanaji, "Nasenbluten") — **nicht** はなじ
- 「みかづき」 (mikazuki, "Halbmond") = み + か + 月 (tsuki → づき)

**2. Wiederholung von ち/つ im selben Wort:**
- 「つづく」 (tsuzuku, "fortsetzen") — kommt von つ-つく, wird beim zweiten つ stimmhaft
- 「ちぢむ」 (chijimu, "schrumpfen") — selber Mechanismus mit ち

> **Faustregel:** **Schreibe immer じ und ず**, AUSSER du erkennst eines der beiden Muster oben. In ~98% der Fälle ist じ/ず richtig. Wenn du unsicher bist, ist じ/ず die sichere Wahl.

> **Mini-Wörter:** 「だいがく」 (daigaku, 'Universität'), 「でんわ」 (denwa, 'Telefon'), 「どこ」 (doko, 'wo?'), 「だれ」 (dare, 'wer?'), 「はなぢ」 (hanaji, 'Nasenbluten' — Rendaku!), 「つづく」 (tsuzuku, 'fortsetzen' — Wiederholung).$TEXT$
WHERE id = 6305 AND lesson_id = 149;

-- Page 2, Block 4 (id=6311): B-Reihe
UPDATE lesson_content SET content_text = $TEXT$## B-Reihe — H mit Dakuten

Die H-Reihe wird zur B-Reihe. **Regelmässig**, ohne Ausnahmen — und phonetisch eine Erleichterung:

- **ば (ba)** wie in *Ball*
- **び (bi)** wie in *Biene*
- **ぶ (bu)** wie in *Buch* (kurz, mit unrundiertem u)
- **べ (be)** wie in *Bett*
- **ぼ (bo)** wie in *Boot* (kurz)

> **Wichtig:** Die H-Reihe hatte mit 「ふ」 (fu) eine bilabiale Ausnahme. **Mit Dakuten verschwindet diese Eigenheit:** 「ぶ」 (bu) ist ein **klares deutsches "b"**, also bilabial gestoppt — kein bilabialer Frikativ mehr wie ふ.

> **Etymologie-Hinweis:** Historisch war die H-Reihe einmal die "P-Reihe" — vor ca. 1500 Jahren wurde *pa, pi, pu, pe, po* zu *ha, hi, fu, he, ho*. Deshalb wirkt das **B-zu-H-zu-P-Trio** so eng zusammen: alle drei haben einen gemeinsamen Ursprung. Mit Dakuten machst du gewissermassen den Lautwandel rückgängig.

> **Mini-Wörter:** 「ばんごう」 (bangou, 'Nummer'), 「びょういん」 (byouin, 'Krankenhaus'), 「ぶた」 (buta, 'Schwein'), 「べんとう」 (bentou, 'Lunchbox'), 「ぼく」 (boku, 'ich' — männlich-informell).$TEXT$
WHERE id = 6311 AND lesson_id = 149;

-- Page 2, Block 5 (id=6317): P-Reihe
UPDATE lesson_content SET content_text = $TEXT$## P-Reihe — H mit Handakuten

Die **einzige Reihe**, die **Handakuten** 「゜」 (kleiner Kreis) bekommt: die H-Reihe wird zur P-Reihe. **Regelmässig**:

- **ぱ (pa)** wie in *Papa*
- **ぴ (pi)** wie in *Pizza*
- **ぷ (pu)** wie in *Puppe* (kurz, unrundiertes u)
- **ぺ (pe)** wie in *Peter*
- **ぽ (po)** wie in *Post*

> **Aussprache-Hinweis:** Anders als 「ふ」 (fu, bilabialer Frikativ) ist 「ぷ」 (pu) ein **klarer Plosivlaut** — wie deutsches "p". Beide Lippen schliessen kurz, dann öffnen sie sich mit einem kleinen Knall. **Glasklar im Vergleich zu fast allen anderen japanischen Lauten** — deshalb klingt P im Japanischen oft besonders kräftig.

> **Wann erscheint P im Japanischen?**
> Die P-Reihe ist im **alltäglichen Wortschatz selten**, weil das ursprüngliche japanische *pa, pi, pu, pe, po* zu *ha, hi, fu, he, ho* wurde (siehe B-Reihe). Heute findet man P vor allem in:
> - **Lehnwörtern** (Gairaigo): ぱん (pan, von portug. *pão*), ぴあの (piano), ぱそこん (pasokon, "PC")
> - **Onomatopoetika**: ぴかぴか (pikapika, "glitzernd"), ぽんぽん (ponpon)
> - **Konsonant-Verdopplung** mit 「っ」: いっぽん (ippon, "ein Stab"), きっぷ (kippu, "Ticket")

> **Eselsbrücke:** Dakuten = **zwei Striche** (゛). Handakuten = **ein Kreis** (゜) — wie ein Punkt für "P" oder eine kleine "0" zwischen den Strichen.

> **Mini-Wörter:** 「ぱん」 (pan, 'Brot'), 「ぴあの」 (piano, 'Klavier'), 「ぷろ」 (puro, 'Profi'), 「ぺん」 (pen, 'Stift'), 「ぽけっと」 (poketto, 'Tasche').$TEXT$
WHERE id = 6317 AND lesson_id = 149;

-- Page 3, Block 1 (id=6323): Aussprache & Schreibhinweise
UPDATE lesson_content SET content_text = $TEXT$## Die wichtigsten Regeln

**Dakuten 「゛」 = stimmhafter Konsonant.** Stell dir vor, dein Kehlkopf vibriert beim Sprechen — bei k/s/t/h vibriert er nicht, bei g/z/d/b schon. Die zwei kleinen Striche oben rechts sind das visuelle Signal "Stimme hinzufügen".

**Handakuten 「゜」 = explosiver P-Laut.** Wirkt nur auf die H-Reihe. P ist im Japanischen weniger häufig als im Deutschen — kommt vor allem bei Lehnwörtern und in Kombination mit Konsonant-Verdopplung vor.

## Welche Reihen bekommen welche Diakritika?

Nicht jede Reihe kann beide:

- **Dakuten** 「゛」: nur **K, S, T, H**
- **Handakuten** 「゜」: nur **H**

> Das heisst: K, S, T, N, M, Y, R, W, ん bekommen **keine** Handakuten — das wäre falsch geschrieben. Die H-Reihe ist die einzige, die mit beiden Markierungen vorkommt: ば (b) und ぱ (p).

## Position der Markierung

Die Markierungen stehen **immer oben rechts** vom Grundzeichen:

- か + 「゛」 → が
- は + 「゛」 → ば
- は + 「゜」 → ぱ

Nicht oben links, nicht unten — **immer oben rechts**. Beim Schreiben sind die Diakritika immer **die letzten Striche** des Zeichens.

## Yotsugana — die vier Doppelgänger

Im modernen Standard-Japanisch klingen **vier Zeichen identisch in zwei Paaren**:

- 「じ」 (Z-Reihe) ≡ 「ぢ」 (D-Reihe) — beide klingen wie "dschi"
- 「ず」 (Z-Reihe) ≡ 「づ」 (D-Reihe) — beide klingen wie "dsu"

Historisch (vor ca. 400 Jahren) waren das **vier verschiedene Laute** — daher der Name "**Yotsugana**" (四つ仮名, "vier Kana"). In manchen südlichen Dialekten (z.B. Kyushu) werden sie noch unterschieden.

> **Praxis-Regel:** Schreibe **immer じ und ず**, AUSSER:
> 1. **Rendaku** (Komposita-Voicing): wenn ein Wort, das mit ち/つ beginnt, in einem Kompositum stimmhaft wird → ぢ/づ. Beispiel: 「はな」 + 「ち」 → 「はなぢ」 (hanaji, "Nasenbluten").
> 2. **Wiederholung**: wenn ち/つ direkt in der gleichen Silbe verdoppelt wird → ぢ/づ. Beispiel: 「つづく」 (tsuzuku, "fortsetzen").
>
> In ~98% der Fälle ist じ/ず richtig. Im Zweifelsfall: じ/ず.

## Verwechslungsgefahr

- **「ば」 (ba) vs. 「ぱ」 (pa)** — der einzige Unterschied ist **zwei Striche vs. ein Kreis**. Bei kleiner Schrift schwer zu unterscheiden, bei Handschrift noch heikler.
- **「じ」 (ji) vs. 「ぢ」 (ji)** — klingen gleich, kommen aber in unterschiedlichen Wörtern vor. Lerne 「じ」 als Standard, 「ぢ」 nur als Sonderfall.
- **「ず」 (zu) vs. 「づ」 (zu)** — gleiche Logik wie ji/ji.
- **「べ」 (be) vs. 「ぺ」 (pe)** — derselbe Unterschied wie ば/ぱ — Striche vs. Kreis.

## Eine Bonus-Eigenheit: Nasalierung der G-Reihe

Im **älteren Tokyo-Standard** wird die G-Reihe **in Wortmitte oft nasaliert**: 「かぎ」 (kagi, "Schlüssel") klingt wie "ka-**ngi**" mit ng-Laut. Diese Aussprache hörst du noch in:

- formellen Nachrichtensendern (NHK)
- bei älteren Sprechern
- in traditioneller Bühnensprache

Bei jüngeren Sprechern und in Anime/Pop-Kultur dominiert das normale [g]. **Lerner müssen die Nasalierung nicht produzieren** — aber sie sollten sie wiedererkennen, wenn sie ihnen begegnet.

## Tipp zum Üben

Nimm jedes Wort, das du bisher gelernt hast, und probiere es mit Dakuten oder Handakuten:

- 「かさ」 (kasa, 'Regenschirm') → 「がさ」? — ergibt **kein** Wort, aber zeigt dir die Klangveränderung
- 「ほん」 (hon, 'Buch') → 「ぼん」 (bon) → 「ぽん」 (pon) — drei verschiedene Klänge

**Schreibe jeden Tag** alle 25 modifizierten Zeichen einmal mit der Hand. Nach einer Woche sitzt es.$TEXT$
WHERE id = 6323 AND lesson_id = 149;

-- Page 4, Block 1 (id=6324): Quiz-Vorlauf
UPDATE lesson_content SET content_text = $TEXT$## Teste dein Wissen

Gleich kommen **Fragen** zu den 25 modifizierten Hiragana.

- **Multiple-Choice:** Welche Romaji-Lesung passt?
- **Richtig/Falsch:** Stimmt die Aussage über Dakuten/Handakuten?
- **Wort-Lesung & Bedeutung:** Welches Wort siehst du?
- **Matching:** Verbinde Zeichen mit Lesung

> **Tipp:** Konzentriere dich auf 「じ」 (ji aus shi) und die Yotsugana-Regel (ぢ/づ nur in Rendaku-Komposita). Das sind die häufigsten Stolperfallen.$TEXT$
WHERE id = 6324 AND lesson_id = 149;

-- Page 5, Block 1 (id=6325): Zusammenfassung
UPDATE lesson_content SET content_text = $TEXT$## Geschafft — alle Diakritika

Mit dieser Lektion kennst du **alle 25 modifizierten Hiragana**:

- **G-Reihe**: が ぎ ぐ げ ご (K + Dakuten)
- **Z-Reihe**: ざ じ ず ぜ ぞ (S + Dakuten — じ ist 'dschi'!)
- **D-Reihe**: だ ぢ づ で ど (T + Dakuten — ぢ/づ nur Rendaku/Wiederholung)
- **B-Reihe**: ば び ぶ べ ぼ (H + Dakuten)
- **P-Reihe**: ぱ ぴ ぷ ぺ ぽ (H + Handakuten)

Zusammen mit den **46 Grundzeichen** beherrschst du nun **71 Hiragana**.

## Die wichtigsten Punkte im Überblick

1. **Dakuten** ゛: K→G, S→Z, T→D, H→B
2. **Handakuten** ゜: nur H→P
3. **じ ist "dschi"** (Affrikat am Wortanfang, Frikativ in Wortmitte)
4. **Yotsugana**: じ/ぢ und ず/づ klingen gleich. Schreibe **immer じ/ず**, AUSSER bei Rendaku oder Wiederholung von ち/つ
5. **G-Reihe in Wortmitte** kann nasaliert klingen ([ŋ] wie "ng") — ältere Sprecher / NHK-Standard
6. **P-Reihe** ist klares deutsches "p" — kommt v.a. in Lehnwörtern und Onomatopoetika vor

## Alltagswörter, die du jetzt lesen kannst

Mit Diakritika öffnen sich alltägliche Vokabeln:

- 「がっこう」 (gakkou) — Schule
- 「ぎんこう」 (ginkou) — Bank (mit ng-Klang in der Mitte!)
- 「ごはん」 (gohan) — Reis, Mahlzeit
- 「ぞう」 (zou) — Elefant
- 「じかん」 (jikan) — Zeit
- 「だいがく」 (daigaku) — Universität
- 「でんわ」 (denwa) — Telefon
- 「どこ」 (doko) — wo?
- 「ばんごう」 (bangou) — Nummer
- 「ぱん」 (pan) — Brot
- 「ぶた」 (buta) — Schwein
- 「ぴあの」 (piano) — Klavier
- 「べんとう」 (bentou) — Lunchbox
- 「はなぢ」 (hanaji) — Nasenbluten (Rendaku-Beispiel mit ぢ!)

> **Probier es:** Lies alle vierzehn Wörter laut, ohne die Romaji zu nutzen. Schaffst du es? Dann sitzt die Lektion.

## Lerntipps

1. **Schreibe alle 25 Diakritika-Zeichen einmal pro Tag** mit der Hand
2. **Übe gezielt 「じ」 (ji)** — die einzige Aussprache-Ausnahme
3. **Vergleiche** Wörter mit/ohne Diakritika: 「は」 (ha) vs. 「ば」 (ba) vs. 「ぱ」 (pa)
4. **Achte beim Hören** auf Nasalierung in der G-Reihe (kagi → ka-ngi)
5. **Wiederhole das Quiz**, bis alle Fragen ohne Hilfe sitzen

## Was kommt als Nächstes?

- **Hiragana 5** — die letzte Hiragana-Lektion: **Yōon** (kombinierte Silben wie きゃ/しゃ/ちゃ). Damit ist Hiragana **vollständig** abgeschlossen.
- Danach beginnt **Katakana** — das zweite Schriftsystem für Lehnwörter und Eigennamen.
- Parallel kannst du mit den **Vokabel-Lektionen** auf N5-Niveau starten.

**Du hast den schwierigsten Teil hinter dir — Diakritika sind Mayukos Geheimtipp für 'wann ist Japanisch wirklich gelernt'.** Glückwunsch!$TEXT$
WHERE id = 6325 AND lesson_id = 149;

-- Validierung
SELECT id, page_number, order_index, LEFT(content_text, 60) AS preview, length(content_text) AS chars
FROM lesson_content WHERE lesson_id = 149 AND content_type = 'text' ORDER BY page_number, order_index;
SELECT id, character, romanization, LEFT(stroke_order_info, 70) FROM kana WHERE id BETWEEN 47 AND 71 ORDER BY id;

COMMIT;
