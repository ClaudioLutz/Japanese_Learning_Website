-- Refine N5 Katakana 4 (Lesson ID 154) — Dakuten, Handakuten, Längungsstrich
-- 25 modifizierte Zeichen (G/Z/D/B/P-Reihen) + Längungsstrich ー
-- Recherche: 2026-05-02 (Tofugu, Wikipedia Yotsugana, Wikipedia Dakuten/Handakuten, Wikipedia Chōonpu)
SET client_encoding = 'UTF8';

BEGIN;

-- =====================================================
-- TEIL A: Text-Bloecke (9 Updates)
-- =====================================================

-- Page 1, Block 1 (id=6435): Einfuehrung
UPDATE lesson_content SET content_text = $TEXT$## Wo stehst du jetzt?

Nach **Katakana 1, 2 und 3** kennst du alle **46 Grundzeichen**. Diese Lektion fügt **25 modifizierte Zeichen** und ein wichtiges Sonderzeichen hinzu — und macht dich fit fürs Lesen aller Alltags-Lehnwörter.

## Was lernst du jetzt?

Wie bei Hiragana gibt es zwei diakritische Markierungen — **keine neuen Formen**, nur kleine Zusatzzeichen oben rechts:

1. **Dakuten** 「゛」 — zwei kleine Striche oben rechts. Macht stimmlose Konsonanten **stimmhaft**:
   - **K → G**: 「カ」 (ka) → 「ガ」 (ga)
   - **S → Z**: 「サ」 (sa) → 「ザ」 (za)
   - **T → D**: 「タ」 (ta) → 「ダ」 (da)
   - **H → B**: 「ハ」 (ha) → 「バ」 (ba)
2. **Handakuten** 「゜」 — kleiner Kreis oben rechts, **nur** auf der H-Reihe:
   - **H → P**: 「ハ」 (ha) → 「パ」 (pa)

Zusätzlich kommt **eine Katakana-spezifische Eigenheit**:

3. **Längungsstrich** 「ー」 — ein einfacher waagerechter Strich. Verlängert den vorherigen Vokal um **eine zweite Mora**. Kommt **fast in jedem** Lehnwort vor.

## Geschichte — wer hat das erfunden?

- **Dakuten** entstand im späten 9. Jahrhundert aus chinesischen Tonzeichen, die in Japan importiert und stilisiert wurden.
- **Handakuten** ist deutlich jünger und eine **Erfindung portugiesischer Jesuiten** (16. Jh.) — sie brauchten ein eindeutiges Zeichen für /p/ und /f/, um europäische Wörter und Namen zu transliterieren. Das ist passend, denn in modernem Katakana-Lehnwort-Text wirst du Handakuten **viel häufiger** sehen als in Hiragana.

## Längungsstrich — was bedeutet das?

「ー」 macht den **vorherigen Vokal länger** (zwei Moren statt einer):

- 「コーヒー」 (kōhī, 'Kaffee') — verlängert o **und** i
- 「ケーキ」 (kēki, 'Kuchen') — verlängert e
- 「カレー」 (karē, 'Curry') — verlängert e am Ende
- 「スーパー」 (sūpā, 'Supermarkt') — verlängert u **und** a

> **Wichtig:** In Hiragana wird Längung durch einen **zusätzlichen Vokal** angezeigt (おう, ええ, おお). In Katakana **immer** durch 「ー」. Das ist ein echter Unterschied der beiden Schriften.

## Was kannst du danach?

Die meisten alltäglichen Katakana-Lehnwörter werden lesbar:

- 「コーヒー」 (kōhī) — Kaffee
- 「ビール」 (bīru) — Bier
- 「ピザ」 (piza) — Pizza
- 「パソコン」 (pasokon) — Computer (von 'personal computer')
- 「ゲーム」 (gēmu) — Spiel
- 「デザイン」 (dezain) — Design$TEXT$
WHERE id = 6435 AND lesson_id = 154;

-- Page 2, Block 1 (id=6436): G-Reihe
UPDATE lesson_content SET content_text = $TEXT$## G-Reihe — K + Dakuten

Wie bei Hiragana wird die K-Reihe zur G-Reihe. **Stimmhaftes** g — beim Sprechen vibriert dein Kehlkopf.

- **ガ (ga)** wie in *Gabel*
- **ギ (gi)** wie in *Gips*
- **グ (gu)** wie in *Gurke* (kurz, mit unrundiertem u)
- **ゲ (ge)** wie in *Geld*
- **ゴ (go)** wie in *Gott*

> **Etymologie:** Schau dir 「ガ」 an — es ist exakt 「カ」 (ka) plus zwei Striche oben rechts. Du musst keine neue Form lernen, nur die Markierung wahrnehmen.

> **Bonus für Hörverstehen:** In manchen japanischen Dialekten (besonders bei älteren Tokyo-Sprechern) klingt das **g in der Wortmitte wie ein nasalisiertes "ng"** — so ist 「アゲ」 (age) bei manchen wie *"a-nge"*. Dieses Phänomen heisst *bidakuon* (鼻濁音). Du musst das nicht selbst sprechen, aber dich nicht wundern, wenn du es im Hörverstehen hörst.

**Mini-Wörter:** 「ガス」 (gasu, 'Gas'), 「ゲーム」 (gēmu, 'Spiel'), 「ゴール」 (gōru, 'Tor/Ziel'), 「ギター」 (gitā, 'Gitarre'), 「グラス」 (gurasu, 'Glas').$TEXT$
WHERE id = 6436 AND lesson_id = 154;

-- Page 2, Block 7 (id=6442): Z-Reihe
UPDATE lesson_content SET content_text = $TEXT$## Z-Reihe — S + Dakuten

Die S-Reihe wird zur Z-Reihe — mit der bekannten Ausnahme bei *ji*:

- **ザ (za)** wie in englischem *zap* — am Wortanfang als hartes [dz], in der Mitte als weiches [z]
- **ジ (ji)** ⚠ — die Ausnahme! 「シ」 (shi) → 「ジ」 (ji), gesprochen **'dschi'** wie in *Dschungel*
- **ズ (zu)** wie in englischem *zoom* — am Anfang [dzu], in der Mitte [zu]
- **ゼ (ze)** wie in englischem *zebra*
- **ゾ (zo)** wie in englischem *zone*

> **Phonetik-Detail:** Japanisches **z am Wortanfang** ist eigentlich ein **[dz]** mit kurzem Verschluss — fast wie in *Pizza* (das doppelte z). In der Wortmitte wird es zum klaren **[z]**. Du musst nicht beides bewusst lernen, dein Mund macht das automatisch.

> **Tofugu-Stolperfalle:** Verwechsle 「ジ」 (ji) nicht mit dem englischen "j" wie in *jet* — das japanische ji ist weicher, fast wie *Dschungel* in Tempo statt *jet*.

**Mini-Wörter:** 「ピザ」 (piza, 'Pizza'), 「ジュース」 (jūsu, 'Saft'), 「サイズ」 (saizu, 'Grösse'), 「ゼロ」 (zero, 'Null'), 「ゾーン」 (zōn, 'Zone').$TEXT$
WHERE id = 6442 AND lesson_id = 154;

-- Page 2, Block 13 (id=6448): D-Reihe + Yotsugana
UPDATE lesson_content SET content_text = $TEXT$## D-Reihe — T + Dakuten (mit Yotsugana-Stolperstein)

- **ダ (da)** wie in *Dame*
- **ヂ (ji)** ⚠ — klingt **identisch** zu 「ジ」 (ji aus Z-Reihe), in Katakana **extrem selten**
- **ヅ (zu)** ⚠ — klingt **identisch** zu 「ズ」 (zu aus Z-Reihe), in Katakana **extrem selten**
- **デ (de)** wie in *Decke*
- **ド (do)** wie in *Dose*

## Yotsugana — vier Zeichen, zwei Klänge

Historisch hatten 「ジ」 (zi), 「ヂ」 (di), 「ズ」 (zu), 「ヅ」 (du) **vier verschiedene Aussprachen**. Heute sind im Standard-Japanisch nur noch **zwei** Laute übrig — *ji* und *zu*. Dieses Phänomen heisst **Yotsugana** (四つ仮名 'vier Kana').

> **Faustregel seit der Rechtschreibreform 1946:** Verwende **immer 「ジ」 (ji) und 「ズ」 (zu)** — nicht ヂ/ヅ. Es gibt nur **zwei Ausnahmen** (Rendaku und doppelter stimmhafter Konsonant), die du in Katakana praktisch nie brauchst, weil sie fast nur in nativen japanischen Wörtern auftauchen.

**Praxis:** In modernen Katakana-Lehnwörtern siehst du 「ヂ」 und 「ヅ」 fast nie. Lerne sie zur Vollständigkeit, im Alltag schreibst du fast immer 「ジ」/「ズ」.

**Mini-Wörter:** 「ドア」 (doa, 'Tür'), 「デザイン」 (dezain, 'Design'), 「ダンス」 (dansu, 'Tanz'), 「サンドイッチ」 (sandoitchi, 'Sandwich').$TEXT$
WHERE id = 6448 AND lesson_id = 154;

-- Page 2, Block 19 (id=6454): B-Reihe
UPDATE lesson_content SET content_text = $TEXT$## B-Reihe — H + Dakuten

Die H-Reihe wird zur B-Reihe. **Regelmässig**, ohne Ausnahmen — die einfachste Diakritika-Reihe.

- **バ (ba)** wie in *Ball*
- **ビ (bi)** wie in *Biene*
- **ブ (bu)** wie in *Buch* (kurz, mit unrundiertem u)
- **ベ (be)** wie in *Bett*
- **ボ (bo)** wie in *Boot*

> **Logik der Mechanik:** Auf den ersten Blick wirkt H → B seltsam (im Deutschen sind das ganz verschiedene Konsonanten). Historisch war das japanische "h" aber ein **bilabialer Laut** (mit beiden Lippen, ähnlich [ɸ]). Wenn man das stimmhaft macht, kommt **[b]** heraus — phonetisch logisch. Daher heute der Sprung von H zu B mit nur zwei kleinen Strichen.

**Mini-Wörter:** 「バス」 (basu, 'Bus'), 「ビール」 (bīru, 'Bier'), 「ボール」 (bōru, 'Ball'), 「ブラシ」 (burashi, 'Bürste'), 「ベル」 (beru, 'Glocke').$TEXT$
WHERE id = 6454 AND lesson_id = 154;

-- Page 2, Block 25 (id=6460): P-Reihe
UPDATE lesson_content SET content_text = $TEXT$## P-Reihe — H + Handakuten

Die **einzige Reihe** mit Handakuten 「゜」. Wie bei Hiragana macht der kleine Kreis aus H → P:

- **パ (pa)** wie in *Papa*
- **ピ (pi)** wie in *Pizza*
- **プ (pu)** wie in *Puppe* (kurz)
- **ペ (pe)** wie in *Peter*
- **ポ (po)** wie in *Post*

> **Geschichte:** Handakuten wurde **erst im 16. Jahrhundert** von portugiesischen Jesuiten eingeführt, um europäische /p/-Laute eindeutig zu schreiben. Vorher gab es kein klares Zeichen für P. Das ist der Grund, warum **P-Klänge in Lehnwörtern so häufig sind** — die Handakuten ist quasi für genau diesen Zweck erfunden worden.

> **Wichtig in Katakana:** Handakuten ist in Lehnwörtern **sehr häufig** (Pizza, Pasta, Park, Papier, Pen). In Hiragana siehst du P selten — aber in Katakana ständig.

**Mini-Wörter:** 「ピザ」 (piza, 'Pizza'), 「パン」 (pan, 'Brot' — vom portugiesischen *pão*!), 「ポスト」 (posuto, 'Briefkasten'), 「プール」 (pūru, 'Schwimmbad'), 「ペン」 (pen, 'Stift').$TEXT$
WHERE id = 6460 AND lesson_id = 154;

-- Page 3, Block 1 (id=6466): Längungsstrich Detail
UPDATE lesson_content SET content_text = $TEXT$## Längungsstrich 「ー」 — die Katakana-Eigenheit im Detail

Der Längungsstrich (japanisch *chōonpu*, 長音符) verdoppelt die Vokal-Länge. Er ist **kein eigener Buchstabe**, sondern wirkt auf das vorherige Zeichen.

## So funktioniert er

- 「カ」 (ka) + 「ー」 = 「カー」 (kā, langes 'kaa') — z.B. 「カード」 (kādo, 'Karte')
- 「コ」 (ko) + 「ー」 = 「コー」 (kō, langes 'koo') — z.B. 「コーヒー」 (kōhī, 'Kaffee')
- 「メ」 (me) + 「ー」 = 「メー」 (mē) — z.B. 「メール」 (mēru, 'E-Mail')
- 「ビ」 (bi) + 「ー」 = 「ビー」 (bī) — z.B. 「ビール」 (bīru, 'Bier')

> **Der Strich zählt als eigene Mora.** Beim Sprechen klingt der Vokal exakt **doppelt so lang**: 「カド」 (kado, 'Ecke', 2 Moren) vs. 「カード」 (kādo, 'Karte', 3 Moren).

## Schreibrichtung

- **In horizontalem Text** (links nach rechts): waagerechter Strich `ー`
- **In vertikalem Text** (oben nach unten, z.B. Buchspalten): **senkrechter** Strich, gleicher Schriftraum

## Wichtigste Regel: Längungsstrich nur in Katakana

In **Hiragana** wird Längung anders ausgedrückt:

- Hiragana: 「おかあさん」 (okāsan, 'Mutter') — das zweite あ verlängert das a
- Katakana: 「カード」 (kādo, 'Karte') — der Längungsstrich verlängert das a

Du wirst 「ー」 fast nur in **Katakana** sehen. Selten taucht er auch in Hiragana auf — z.B. auf Ramen-Schildern als stilisiertes 「らーめん」, aber das ist eine Ausnahme.

## Aussprache der Diakritika-Reihen — Faustregel

**Dakuten = stimmhaft:** Beim Sprechen vibriert dein Kehlkopf. Bei k/s/t/h vibriert er nicht, bei g/z/d/b schon. Leg die Hand an den Hals — der Unterschied ist spürbar.

**Handakuten = explosiver P-Laut:** Wie ein kurzer 'Druck' der Lippen. Das deutsche "p" trifft es genau.

**Yotsugana-Faustregel:** ジ und ズ sind Standard. ヂ und ヅ siehst du in modernem Katakana fast nie.

## Verwechslungsgefahr

- **「バ」 (ba) vs. 「パ」 (pa)** — zwei Striche vs. ein Kreis (B oder P?)
- **「ジ」 (ji) vs. 「ヂ」 (ji)** — klingen identisch, 「ジ」 ist Standard
- **「ズ」 (zu) vs. 「ヅ」 (zu)** — gleiche Logik, 「ズ」 ist Standard
- **「ベ」 (be) vs. 「ペ」 (pe)** — Striche vs. Kreis

> **Lerntipp:** Wenn du dir bei der Schreibung unsicher bist (ji/zu), nimm **immer die Standard-Form** ジ/ズ. Du wirst zu 99% richtig liegen.

## Tipp zum Üben

**Lies eine Speisekarte mit europäischer Küche.** Pizza, Pasta, Burger, Coffee, Wine — alle Wörter haben Diakritika UND Längungsstriche. Wenn du fünf Speisen sicher liest, sitzt diese Lektion.$TEXT$
WHERE id = 6466 AND lesson_id = 154;

-- Page 4, Block 1 (id=6467): Quiz-Vorlauf
UPDATE lesson_content SET content_text = $TEXT$## Teste dein Wissen

Gleich kommen **Fragen** zu den 25 modifizierten Katakana und dem Längungsstrich.

- **Multiple-Choice:** Welche Romaji-Lesung passt?
- **Richtig/Falsch:** Stimmt die Aussage?
- **Wort-Lesung:** Welches Lehnwort siehst du?
- **Matching:** Verbinde Zeichen mit Lesung

> **Tipp:** Konzentriere dich auf 「ジ」 (ji) und den Längungsstrich 「ー」 — beide kommen in fast jedem Lehnwort vor. Und denk an Yotsugana: ジ/ズ sind Standard, ヂ/ヅ sind selten.$TEXT$
WHERE id = 6467 AND lesson_id = 154;

-- Page 5, Block 1 (id=6468): Zusammenfassung
UPDATE lesson_content SET content_text = $TEXT$## Geschafft — alle Diakritika und der Längungsstrich

Mit dieser Lektion kennst du **alle 25 modifizierten Katakana**:

- **G-Reihe**: ガ ギ グ ゲ ゴ (K + Dakuten)
- **Z-Reihe**: ザ ジ ズ ゼ ゾ (S + Dakuten — ジ ist 'ji', am Anfang [dz], in der Mitte [z])
- **D-Reihe**: ダ ヂ ヅ デ ド (T + Dakuten — ヂ/ヅ selten, **Yotsugana**!)
- **B-Reihe**: バ ビ ブ ベ ボ (H + Dakuten — H war historisch bilabial → daher B logisch)
- **P-Reihe**: パ ピ プ ペ ポ (H + Handakuten — Jesuiten-Erfindung des 16. Jh.)

Plus den **Längungsstrich** 「ー」, der den vorherigen Vokal verdoppelt.

**Insgesamt** beherrschst du nun **71 Katakana** — und kannst Längungen lesen.

## Die wichtigsten Konzepte zum Mitnehmen

1. **Dakuten = stimmhaft** (Kehlkopf vibriert: k/s/t/h → g/z/d/b)
2. **Handakuten = nur H → P** (von Jesuiten erfunden für /p/)
3. **「ジ」 ist Standard für *ji*** — ヂ ist Yotsugana-Doppelgänger, fast nie verwendet
4. **「ズ」 ist Standard für *zu*** — ヅ ebenso selten
5. **Längungsstrich 「ー」** ist Katakana-spezifisch — in Hiragana nutzt man wiederholten Vokal
6. **P-Klänge sind in Katakana sehr häufig** — wegen Lehnwörtern aus Englisch/Portugiesisch/Deutsch

## Lehnwörter, die du jetzt lesen kannst

Die typischen Alltagsbegriffe sind nun zugänglich:

- 「コーヒー」 (kōhī) — Kaffee
- 「ビール」 (bīru) — Bier
- 「ピザ」 (piza) — Pizza
- 「パン」 (pan) — Brot (aus dem Portugiesischen!)
- 「ガス」 (gasu) — Gas
- 「ゲーム」 (gēmu) — Spiel
- 「バス」 (basu) — Bus
- 「デザイン」 (dezain) — Design
- 「サイズ」 (saizu) — Grösse
- 「ダンス」 (dansu) — Tanz
- 「ボール」 (bōru) — Ball
- 「ポスト」 (posuto) — Briefkasten
- 「ジュース」 (jūsu) — Saft
- 「ギター」 (gitā) — Gitarre
- 「プール」 (pūru) — Schwimmbad

> **Probier es:** Lies alle Wörter laut. Achte auf die Längungsstriche und die korrekte stimmhafte Aussprache.

## Lerntipps

1. **Schreibe alle 25 Diakritika-Zeichen einmal pro Tag** mit der Hand
2. **Übe gezielt 「ジ」 (ji)** — die einzige echte Ausnahme
3. **Vergleiche** Wörter mit/ohne Längung: 「カド」 (kado, 'Ecke') vs. 「カード」 (kādo, 'Karte')
4. **Lies Speisekarten** — italienische, französische, amerikanische Küche sind ideal
5. **Achte auf den ng-Klang in der G-Reihe** — JLPT-Hörverstehen-Detail

## Was kommt als Nächstes?

- **Katakana 5** — die letzte Katakana-Lektion: **Yōon** (kombinierte Silben キャ/シャ/チャ) plus **Lehnwort-Spezialitäten** wie 「ティ」 (ti, in 'パーティー' pātī = Party), 「ファ」 (fa, in 'ファイル' fairu = Datei), 「ウィ」 (wi, in 'ウィーン' Wīn = Wien) und 「ヴ」 (vu, das Tofugu-Sonderzeichen). Damit ist Katakana **vollständig**.

Danach hast du **alle Hiragana und Katakana** im Griff — der komplette Lese-Werkzeugkasten für Japanisch.$TEXT$
WHERE id = 6468 AND lesson_id = 154;

-- =====================================================
-- TEIL B: Strichfolge fuer 25 Diakritika-Zeichen
-- Pattern: Grundzeichen + Dakuten/Handakuten oben rechts
-- =====================================================

-- G-Reihe (K + Dakuten ゛)
UPDATE kana SET stroke_order_info='Wie カ (ka) + Dakuten 「゛」 (zwei kleine diagonale Striche oben rechts). Striche zuerst die Grundform (2 Striche), dann die zwei Dakuten-Striche oben rechts.' WHERE id=151;
UPDATE kana SET stroke_order_info='Wie キ (ki) + Dakuten 「゛」 (zwei kleine Striche oben rechts). Erst die 3 Striche der Grundform, dann die zwei Dakuten-Striche.' WHERE id=152;
UPDATE kana SET stroke_order_info='Wie ク (ku) + Dakuten 「゛」 (zwei kleine Striche oben rechts). Erst die 2 Striche der Grundform, dann die zwei Dakuten-Striche.' WHERE id=153;
UPDATE kana SET stroke_order_info='Wie ケ (ke) + Dakuten 「゛」 (zwei kleine Striche oben rechts). Erst die 3 Striche der Grundform, dann die zwei Dakuten-Striche.' WHERE id=154;
UPDATE kana SET stroke_order_info='Wie コ (ko) + Dakuten 「゛」 (zwei kleine Striche oben rechts). Erst die 2 Striche der Grundform, dann die zwei Dakuten-Striche.' WHERE id=155;

-- Z-Reihe (S + Dakuten ゛)
UPDATE kana SET stroke_order_info='Wie サ (sa) + Dakuten 「゛」 (zwei kleine Striche oben rechts). Erst die 3 Striche der Grundform, dann die zwei Dakuten-Striche.' WHERE id=156;
UPDATE kana SET stroke_order_info='Wie シ (shi) + Dakuten 「゛」 (zwei kleine Striche oben rechts). Erst die 3 Striche der Grundform (Striche zeigen RECHTS OBEN), dann die zwei Dakuten-Striche.' WHERE id=157;
UPDATE kana SET stroke_order_info='Wie ス (su) + Dakuten 「゛」 (zwei kleine Striche oben rechts). Erst die 2 Striche der Grundform, dann die zwei Dakuten-Striche.' WHERE id=158;
UPDATE kana SET stroke_order_info='Wie セ (se) + Dakuten 「゛」 (zwei kleine Striche oben rechts). Erst die 2 Striche der Grundform, dann die zwei Dakuten-Striche.' WHERE id=159;
UPDATE kana SET stroke_order_info='Wie ソ (so) + Dakuten 「゛」 (zwei kleine Striche oben rechts). Erst die 2 Striche der Grundform (Strich STEIL nach unten), dann die zwei Dakuten-Striche.' WHERE id=160;

-- D-Reihe (T + Dakuten ゛)
UPDATE kana SET stroke_order_info='Wie タ (ta) + Dakuten 「゛」 (zwei kleine Striche oben rechts). Erst die 3 Striche der Grundform, dann die zwei Dakuten-Striche.' WHERE id=161;
UPDATE kana SET stroke_order_info='Wie チ (chi) + Dakuten 「゛」. Klingt identisch zu ジ (Yotsugana — in Katakana SELTEN). Erst die 3 Striche der Grundform, dann die zwei Dakuten-Striche.' WHERE id=162;
UPDATE kana SET stroke_order_info='Wie ツ (tsu) + Dakuten 「゛」. Klingt identisch zu ズ (Yotsugana — in Katakana SELTEN). Erst die 3 Striche der Grundform (NACH UNTEN!), dann die zwei Dakuten-Striche.' WHERE id=163;
UPDATE kana SET stroke_order_info='Wie テ (te) + Dakuten 「゛」 (zwei kleine Striche oben rechts). Erst die 3 Striche der Grundform, dann die zwei Dakuten-Striche.' WHERE id=164;
UPDATE kana SET stroke_order_info='Wie ト (to) + Dakuten 「゛」 (zwei kleine Striche oben rechts). Erst die 2 Striche der Grundform, dann die zwei Dakuten-Striche.' WHERE id=165;

-- B-Reihe (H + Dakuten ゛)
UPDATE kana SET stroke_order_info='Wie ハ (ha) + Dakuten 「゛」 (zwei kleine Striche oben rechts). Erst die 2 Striche der Grundform, dann die zwei Dakuten-Striche.' WHERE id=166;
UPDATE kana SET stroke_order_info='Wie ヒ (hi) + Dakuten 「゛」 (zwei kleine Striche oben rechts). Erst die 2 Striche der Grundform, dann die zwei Dakuten-Striche.' WHERE id=167;
UPDATE kana SET stroke_order_info='Wie フ (fu) + Dakuten 「゛」 (zwei kleine Striche oben rechts). Erst der EINE Strich der Grundform (Knick), dann die zwei Dakuten-Striche.' WHERE id=168;
UPDATE kana SET stroke_order_info='Wie ヘ (he) + Dakuten 「゛」 (zwei kleine Striche oben rechts). Erst der EINE Strich der Grundform, dann die zwei Dakuten-Striche.' WHERE id=169;
UPDATE kana SET stroke_order_info='Wie ホ (ho) + Dakuten 「゛」 (zwei kleine Striche oben rechts). Erst die 4 Striche der Grundform, dann die zwei Dakuten-Striche.' WHERE id=170;

-- P-Reihe (H + Handakuten ゜)
UPDATE kana SET stroke_order_info='Wie ハ (ha) + Handakuten 「゜」 (kleiner Kreis oben rechts). Erst die 2 Striche der Grundform, dann der kleine Kreis. Jesuiten-Erfindung des 16. Jh. fuer /p/.' WHERE id=171;
UPDATE kana SET stroke_order_info='Wie ヒ (hi) + Handakuten 「゜」 (kleiner Kreis oben rechts). Erst die 2 Striche der Grundform, dann der kleine Kreis.' WHERE id=172;
UPDATE kana SET stroke_order_info='Wie フ (fu) + Handakuten 「゜」 (kleiner Kreis oben rechts). Erst der EINE Strich der Grundform, dann der kleine Kreis.' WHERE id=173;
UPDATE kana SET stroke_order_info='Wie ヘ (he) + Handakuten 「゜」 (kleiner Kreis oben rechts). Erst der EINE Strich der Grundform, dann der kleine Kreis.' WHERE id=174;
UPDATE kana SET stroke_order_info='Wie ホ (ho) + Handakuten 「゜」 (kleiner Kreis oben rechts). Erst die 4 Striche der Grundform, dann der kleine Kreis.' WHERE id=175;

-- Validierung
SELECT id, character, romanization, LEFT(stroke_order_info, 70) AS preview
FROM kana
WHERE id BETWEEN 151 AND 175
ORDER BY id;

SELECT id, page_number, order_index, LEFT(content_text, 60) AS preview, length(content_text) AS chars
FROM lesson_content
WHERE lesson_id = 154 AND content_type = 'text'
ORDER BY page_number, order_index;

COMMIT;
