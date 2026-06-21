# Didaktischer Audit — N5-Lektionen japanese-learning.ch

_Automatisierter Mehr-Agenten-Audit aller **58 publizierten N5-Lektionen**, 2026-06-21. Jede Findung wurde von einem zweiten, unabhängigen Agenten adversarial gegengeprüft; nur bestätigte Findungen stehen hier._

## Executive Summary

Geprüft wurden **58 Lektionen** (15 Module) in zwei Dimensionen: **Korrektheit** (Lesungen, Übersetzungen, Quiz-Logik, Level-Treue, Konsistenz) und **Natürlichkeit** (klingen die japanischen Beispielsätze wie echtes Japanisch oder steif/unnatürlich?). Ergebnis: **57 bestätigte Korrektheits-Findungen** und **23 bestätigte Natürlichkeits-Findungen**, verteilt auf **42 der 58 Lektionen**.

- **Kein einziger kritischer/funktionsbrechender Fehler.** Schwere der Korrektheits-Findungen: **16 mittel, 41 gering**. Die Plattform ist inhaltlich solide.
- **Schwerpunkt Korrektheit:** 29× interne **Konsistenz-Widersprüche** (eine Lektion sagt an zwei Stellen Verschiedenes), 9× Klarheits-/Erklärungsfehler, 5× **Quiz-Defekte**, 6× faktische Fehler, 5× Vorwissen-Sprung, 1× Level-Verstoss, 2× Progression.
- **Natürlichkeit:** 7 hoch, 9 mittel, 7 gering. Wiederkehrendes Muster: deutsch-/englisch-geprägte **Calques** (来ます statt 戻る/行ってくる beim Weggehen), unjapanische **Pronomen** (あなたの + Verwandtschaftswort), **fehlende Zähler** (本が十 statt 十冊) und semantisch schiefe Lehr-Beispielsätze (Schüler sind 「大きい」).

## Methodik

1. **Snapshot:** Alle 58 Lektionen wurden aus der Produktions-DB als voll aufgelöstes JSON gedumpt (Vokabeln mit Lesung/Romaji/Bedeutung, Kanji, Grammatik, Quiz inkl. markierter korrekter Antwort). Vollständigkeit gegen die DB verifiziert (2040 Inhalte = DB-Zahl, 0 Verlust).
2. **Deterministische Vorab-Pässe** (was eine Stichproben-Prüfung nicht sieht): globaler **Konsistenz-Diff** über alle Lektionen (gleiches Wort/Kanji mit abweichender Lesung/Bedeutung) → **0 Divergenzen**; **`fill_blank`-Scan** (laut Projektregel verbotener Quiz-Typ) → **0 Vorkommen**.
3. **Korrektheits-Audit:** 26 Agenten (1 je 2-3 Lektionen, modulkohärent) mit JLPT-Curriculum-Karte und Kanji-/Grammatik-Einführungsindex; jede Findung adversarial gegengeprüft.
4. **Natürlichkeits-Recherche:** 1 Muttersprachler-Agent je Modul, mit **Web-Recherche** zum Thema als Vergleichsmassstab; jede Unnatürlich-/Steif-Markierung von einem strengen zweiten Muttersprachler gegengeprüft (Alternative muss N5-Niveau bleiben).

> Hinweis: Findungen sind **Vorschläge zur Sichtung**, noch nicht angewendet. Der Korrektur-Schritt (das Anwenden der Fixes) ist bewusst Phase 2 nach deiner Freigabe.

## Systematische Muster (zuerst angehen)

Diese Punkte wiederholen sich über mehrere Lektionen — ein Fix-Prinzip löst jeweils mehrere Stellen:

1. **Single-Select-Quiz mit zwei richtigen Antworten — i-Adjektiv-Verneinung** (L156 おもしろい, L170 大きい): Gefragt wird nach der Verneinung; als richtig markiert ist nur die Plain-Form 〜くない, die ebenfalls korrekte höfliche Form 〜くありません gilt als falsch. → Entweder Distraktoren eindeutig falsch machen, oder Frage auf die einfache Form einschränken.
2. **Kardinalzahl ohne Zähler** (L192 本が十, L206 本が十あります): 「十 + Nomen + あります」 ist ungrammatisch/idiomatisch unvollständig — Bücher brauchen den Zähler 冊 (十冊, N5). → Zähler ergänzen; generell Zahl-am-Nomen-Konstruktionen prüfen.
3. **Unjapanische Pronomen / Calques aus dem Deutschen** (L171 あなたの お母さん, weitere mit わたしは / あなた): Muttersprachler nennen den Namen + さん oder lassen das Pronomen weg. Teils widerspricht es der eigenen uchi/soto-Lehre derselben Lektion. → Pronomen streichen / durch Namen ersetzen.
4. **Herbst 寒い statt 涼しい** (L204): Beispielsatz nennt den Herbst als kalt (Winterkälte) — widerspricht der eigenen Lektion, die 涼しい (kühl) als Herbst-Wort lehrt. → 涼しい verwenden.
5. **Mora-Zählung ohne ん** (L150): Lehrtabelle zählt びょういん/びよういん um eine Mora zu niedrig (ん wird unterschlagen), während das Quiz derselben Lektion korrekt zählt. → Tabelle korrigieren.

---

## Teil A — Korrektheit (57 Findungen)

Sortiert nach Kategorie (Quiz-Defekte & faktische Fehler zuerst), innerhalb nach Schwere.

### Quiz-Defekt

- **L156 · N5 Familie & Personen 2 — Berufe und Charakter** — 🟠 mittel  
  _Fundstelle:_ page_number 6, order_index 1, Quiz-Frage 'Wie sagt man Dieses Buch ist nicht interessant auf Japanisch?', Option 'この ほんは おもしろくありません (Kono hon wa omoshiroku arimasen)' (is_correct=false), Feedback: 'Diese Form ist im N4-Bereich höflicher, im N5 nutzen wir くないです.'  
  _Problem:_ Die Frage hat zwei korrekte Antworten. 「おもしろくありません」 ist vollkommen korrektes, standard-N5-Japanisch für 'ist nicht interessant' — die höfliche い-Adjektiv-Negation wird im N5 regulär gelehrt (Minna no Nihongo Lektion 8, Genki Lektion 5), gleichberechtigt neben 「おもしろくないです」. Sie ist also genauso richtig wie die als korrekt markierte Option. Zusätzlich enthält das Distraktor-Feedback eine sachlich falsche Behauptung: 〜くありません ist NICHT 'im N4-Bereich', sondern Kern-N5.  
  _Korrektur:_ Den Distraktor 「おもしろくありません」 durch eine echte Falschform ersetzen, z.B. 「おもしろいくないです」 (ungrammatisch, weil das い nicht entfällt) oder 「おもしろじゃありません」. Falls beide höflichen Negationen bewusst gelehrt werden sollen, die Frage so umformulieren, dass nur EINE Antwort eindeutig korrekt ist. Das Feedback 'im N4-Bereich' streichen.
- **L170 · N5 Kanji 5 — Position und Grösse (大小上下中右左)** — 🟠 mittel  
  _Fundstelle:_ page_number 6, order_index 1, Frage "Wie negierst du 大きい (gross)?" — Option "大きくありません (ookiku arimasen)" (is_correct: false)  
  _Problem:_ Single-Select-Frage mit zwei faktisch richtigen Antworten. Als korrekt markiert ist nur "大きくない (ookikunai)". Die als falsch markierte Option "大きくありません" ist aber ebenfalls eine grammatisch korrekte (höfliche) Verneinung von 大きい. Das eigene Feedback gibt das sogar zu: "Das ist die höfliche Form — ist auch korrekt, aber die Standardform ist 大きくない." Eine als falsch gewertete, aber faktisch richtige Antwort macht die Frage defekt.  
  _Korrektur:_ Entweder die Option "大きくありません" durch einen eindeutig falschen Distraktor ersetzen (z.B. 大きいくない), oder den Fragetext auf die schlichte/Plain-Form einschränken ("Wie negierst du 大きい in der einfachen Form?") und das Feedback der Option entsprechend anpassen, sodass nur eine Antwort richtig ist.
- **L176 · N5 Begrüssung 2 — Alltagsgrüsse rund um den Tag** — 🟠 mittel  
  _Fundstelle:_ page_number 6, order_index 1, Quiz-Frage 14: "Welche Form benutzt du gegenüber deinem Chef abends beim Verlassen des Büros?" — korrekte Option "おさきに しつれいします。 (Osaki ni shitsurei shimasu.)"  
  _Problem:_ Die als korrekt markierte Antwort 「おさきに しつれいします」 (Osaki ni shitsurei shimasu) wird in der gesamten Lektion an keiner Stelle eingeführt oder erklärt. Die in der Lektion gelehrten Abschieds-/Tagesgrüsse sind さようなら, また あした, おやすみ(なさい). Die Frage prüft damit Stoff, der nie vermittelt wurde — ein Lerner kann sie nur raten.  
  _Korrektur:_ Frage entfernen oder so umformulieren, dass sie auf gelehrtem Stoff basiert (z.B. abfragen, dass 「おやすみなさい」 hier falsch wäre, weil es Gute Nacht zu Hause ist, ohne eine nie gelehrte Büro-Floskel als korrekte Lösung zu verlangen). Falls 「おさきにしつれいします」 gewünscht ist, müsste es vorher als Vokabel/Floskel eingeführt werden.
- **L170 · N5 Kanji 5 — Position und Grösse (大小上下中右左)** — 🟡 gering  
  _Fundstelle:_ page_number 6, order_index 1, Frage "Wie liest man 「じょうず」 (gut können)?" — korrekte Option "じょうず (jouzu)"  
  _Problem:_ Die Frage enthält die korrekte Antwort bereits wörtlich im Fragetext. Es wird nach der Lesung von 「じょうず」 gefragt, und die richtige Antwortoption lautet exakt じょうず (jouzu). Damit prüft die Frage nicht die Lesung des Kanji-Kompositums 上手, sondern lässt sich durch reines Abschreiben aus der Frage lösen.  
  _Korrektur:_ Im Fragetext das Kanji-Kompositum statt der Lesung zeigen: "Wie liest man 「上手」 (gut können)?" — so wird tatsächlich die Lesung じょうず geprüft.
- **L176 · N5 Begrüssung 2 — Alltagsgrüsse rund um den Tag** — 🟡 gering  
  _Fundstelle:_ page_number 5, order_index 4, Quiz-Frage 4: "Warum nutzt Yuki gegenüber Mama 「おはよう」 (kurz), aber gegenüber dem Vater abends 「おやすみなさい」 (lang)?" — korrekte Option "Höherer Respekt gegenüber dem Vater (Familienoberhaupt)"  
  _Problem:_ Die Frage verlangt vom Lerner, eine Status-Hierarchie (Vater höflicher als Mutter) aus dem Dialog abzuleiten, doch der Dialog stützt diesen Schluss nicht: Yuki sagt zur Mutter ausschliesslich am Morgen (おはよう) und zum Vater ausschliesslich am Abend (おやすみなさい). Adressat und Tageszeit sind konfundiert — die kurze Form gegenüber der Mutter MORGENS und die lange Form gegenüber dem Vater ABENDS lassen sich nicht eindeutig auf einen Status-Unterschied zurückführen. Es gibt im Dialog keine Stelle, an der Yuki Mutter und Vater zur gleichen Tageszeit unterschiedlich höflich anspricht. Der als 'falsch' verworfene Distraktor "Weil es Abend ist" ist somit nicht sauber ausgeschlossen.  
  _Korrektur:_ Frage entschärfen: entweder den Dialog so ergänzen, dass Yuki dieselbe Person/Tageszeit unterschiedlich höflich anspricht (sodass der Status-Schluss belegbar wird), oder die Frage in eine reine Faktfrage umbauen (z.B. "Welche Form ist höflicher: おやすみ oder おやすみなさい?"), die nicht auf einer aus dem Dialog nicht ableitbaren Hierarchie-Behauptung beruht.

### Faktischer Fehler

- **L150 · N5 Hiragana 5 — Yōon (kombinierte Silben きゃ/しゃ/ちゃ ...)** — 🟠 mittel  
  _Fundstelle:_ Seite 3, order_index 1 (Text "Worauf du achten musst"), Mora-Tabelle: Zeile "| 「びよういん」 | bi-you-in | 4 | Schönheitssalon (美容院) |" und Zeile "| 「びょういん」 | byou-in | 3 | Krankenhaus (病院) |"  
  _Problem:_ Die Mora-Zahlen in beiden Zeilen sind um eins zu niedrig. びよういん hat 5 Mora (bi-yo-u-i-n), nicht 4. びょういん hat 4 Mora (byo-u-i-n), nicht 3. Der finale Moraic Nasal ん wird in der Tabelle offenbar nicht mitgezählt, obwohl er eine eigene Mora ist.  
  _Korrektur:_ びよういん auf 5 Mora korrigieren, びょういん auf 4 Mora korrigieren (analog wie die Zeilen じゆう=3 / じゅう=2 vollständig zählen).
- **L151 · N5 Katakana 1 — Vokale, K-Reihe und S-Reihe** — 🟠 mittel  
  _Fundstelle:_ Seite 3 (page_number 3), order_index 1, Abschnitt 'Vokal-Entstummung': «「スキ」 (suki, 'Ski') klingt fast wie "ski"». Dieselbe Gleichsetzung wiederholt sich auf Seite 4 (quiz true_false: «In 「スキ」 (suki, "Ski")…») und Seite 5 (Lerntipp: «「スキ」 klingt wie "ski"»).  
  _Problem:_ 「スキ」 (suki) wird durchgehend als das Wort für 'Ski' ausgegeben. Das ist falsch: Das japanische Wort für Ski ist 「スキー」 (sukī) MIT Längungsstrich. 「スキ」 ohne ー ist ein anderes, real existierendes Wort — 好き (suki, 'mögen/Vorliebe'). Das stiftet doppelte Verwirrung, zumal dieselbe Lektion an anderer Stelle (Seite 5 Vokabelliste + Matching-Quiz) korrekt 「スキー」 (sukī) als 'Ski' führt.  
  _Korrektur:_ In allen Entstummungs-Beispielen 「スキ」 durch ein wirklich mit スキ beginnendes, devoicing-taugliches Wort ersetzen oder das Beispiel auf 「スキー」 (sukī, 'Ski') umstellen und klarstellen, dass das u zwischen s und k entstummt. Auf keinen Fall 「スキ」 (ohne ー) als 'Ski' glossieren.
- **L206 · Wohnen — Haus & "es gibt"** — 🟠 mittel  
  _Fundstelle:_ Seite 3 (Vokabeln Teil 2), order_index 7 — Vokabel 本棚 (ほんだな), example_sentence_japanese: "ほんだなに本が十あります。" / example_sentence_english: "hondana ni hon ga juu arimasu. — Im Bücherregal stehen zehn Bücher."  
  _Problem:_ Der Beispielsatz "本が十あります" ist ungrammatisches Japanisch. Eine blosse Kardinalzahl (十) kann im Japanischen nicht direkt mit einem Nomen + あります eine Anzahl ausdrücken — zum Zählen von Büchern ist der Zähler 〜冊 (satsu) zwingend. Korrekt muss es 本が十冊あります heissen. Auch das Romaji "juu" steht ohne Zähler da.  
  _Korrektur:_ Satz zu "ほんだなに本が十冊あります。" ändern, Romaji "hondana ni hon ga jussatsu arimasu.", Übersetzung "Im Bücherregal stehen zehn Bücher." bleibt. Alternativ den Satz vereinfachen: "ほんだなに本があります。" (Im Bücherregal stehen Bücher.), wenn der Zähler 冊 hier didaktisch vermieden werden soll.
- **L145 · N5 Tagesablauf — Wann stehst du auf?** — 🟡 gering  
  _Fundstelle:_ Seite 3 (page_number 3), order_index 9, Vokabel: word '終る', reading 'おわる', meaning_de 'enden, aufhören'; Beispielsatz '映画は十時に終ります。'  
  _Problem:_ Die Kanji-Schreibung 終る mit Okurigana ist nicht die moderne Standard-Orthografie. Standardmässig wird das Verb owaru als 終わる geschrieben (Okurigana わ + る). 終る ist eine veraltete/verkürzte Schreibweise. Da N5-Lerner gerade die korrekte Schreibung einprägen, sollte hier die Standardform stehen.  
  _Korrektur:_ word auf '終わる' und example_sentence_japanese auf '映画は十時に終わります。' korrigieren (reading おわる und Bedeutung bleiben unverändert).
- **L150 · N5 Hiragana 5 — Yōon (kombinierte Silben きゃ/しゃ/ちゃ ...)** — 🟡 gering  
  _Fundstelle:_ Seite 3, order_index 1 (Text "Worauf du achten musst"), Mora-Tabelle, Zeile: "| 「きや」 | ki-ya | 2 | Mädchenname, oder \"(Schreib-)Tisch\" |"  
  _Problem:_ Die Glosse "(Schreib-)Tisch" für 「きや」 ist sachlich falsch. Das japanische Wort für (Schreib-)Tisch ist つくえ (机). きや ist kein gebräuchliches Standardwort mit dieser Bedeutung.  
  _Korrektur:_ Die Bedeutungs-Glosse "(Schreib-)Tisch" streichen; es genügt der Kontrast kya (1 Mora) vs. ki-ya (2 Mora). Falls ein Beispiel gewünscht ist, ein klar belegbares 2-Mora-Wort wählen.
- **L201 · Adjektive 1 — i-Adjektive & Gegensätze** — 🟡 gering  
  _Fundstelle:_ Seite 3 (Vokabeln Teil 2 — Wetter, Gefühl, Zeit), order_index 5: Vokabel 早い / はやい / hayai, meaning_de = 'früh, schnell (i-Adj.)'  
  _Problem:_ Das Kanji 早い (はやい) bedeutet 'früh' (zeitlich). Die Bedeutung 'schnell' (Geschwindigkeit) wird im Japanischen mit dem gleich gelesenen, aber anders geschriebenen 速い (はやい) ausgedrückt. Die meaning_de '...schnell' vermischt die beiden Homophone — bei der Schreibung 早い ist 'schnell' im Sinne von Geschwindigkeit nicht die übliche Bedeutung. Der Beispielsatz selbst nutzt das Wort korrekt zeitlich ('Heute bist du früh dran').  
  _Korrektur:_ meaning_de auf 'früh (i-Adj.)' beschränken (ggf. mit Hinweis, dass 'schnell' i.S.v. Geschwindigkeit als 速い geschrieben wird), um die Verwechslung 早い (früh/zeitlich) vs. 速い (schnell/Geschwindigkeit) zu vermeiden.

### Level-Verstoss (N4+ in N5)

- **L169 · N5 Kanji 4 — Natur (山川木雨) und Wetter** — 🟡 gering  
  _Fundstelle:_ page_number 3, order_index 4, Kanji-Karte "雪" (Schnee), Feld "jlpt_level": 4  
  _Problem:_ In einer als N5 deklarierten Lektion (category_jlpt_level 5) erscheint die Kanji-Karte 雪 mit dem eigenen Metadaten-Feld jlpt_level: 4. Das Zeichen 雪 ist tatsächlich kein offizielles N5-Kanji. Es wird hier ungekennzeichnet als reguläre Lernkarte präsentiert (anders als 田/空, die im Lauftext ausdrücklich als Bonus markiert sind), obwohl das Wort ゆき (Schnee) selbst N5 ist.  
  _Korrektur:_ 雪 entweder ausdrücklich als Bonus/N4-Kanji kennzeichnen (wie bei 田 und 空 im Lauftext) und das Vokabel ゆき in Kana belassen, oder die Kanji-Karte entfernen und nur die Kana-Form ゆき lehren.

### Vorwissen-Sprung

- **L153 · N5 Katakana 3 — M-Reihe, Y-Reihe, R-Reihe, W-Reihe und ン** — 🟠 mittel  
  _Fundstelle:_ Seite 4 (page_number 4), order_index 1, zwei Quiz-Fragen: «Wie liest man das Wort 「ラジオ」?» (verlangt 「ジ」, ji) und «Wie liest man 「ヨガ」?» (verlangt 「ガ」, ga). Die explanations sagen selbst «Dakuten-Form aus Katakana 4».  
  _Problem:_ Das Quiz testet das Lesen von Dakuten-Zeichen (ジ in ラジオ, ガ in ヨガ), die laut Curriculum erst in der NÄCHSTEN Lektion 154 ('N5 Katakana 4 — Dakuten, Handakuten und Längungsstrich') eingeführt werden. Die Erklärungen verweisen ausdrücklich nach vorne auf 'Katakana 4' — die Lektion gibt damit selbst zu, hier noch nicht gelehrten Stoff abzuprüfen. Die Lernenden können ジ/ガ an dieser Stelle noch nicht regelkonform lesen.  
  _Korrektur:_ ラジオ und ヨガ durch Lehnwörter ersetzen, die nur aus den in K1–K3 (Lektionen 151–153) bereits gelehrten, dakuten-freien Grundzeichen bestehen (z.B. メニュー, マイク, レストラン, ミルク, ロボット). Dakuten-Wörter erst im Quiz von Lektion 154 verwenden.
- **L166 · N5 Wegbeschreibung — Rechts, links, geradeaus** — 🟠 mittel  
  _Fundstelle:_ page_number 4, order_index 4 (Grammatik-Karte 'Te-Form-Verkettung für Wegbeschreibungen') + order_index 1 ('Drei Bausteine für jede Wegbeschreibung', Zitat: 'Du hast die Te-Form bereits in Lektion 4 gelernt.')  
  _Problem:_ Lektion 166 lehrt die Te-Form-Verkettung als eigene Kern-Grammatik und benutzt durchgehend 〜てください (まがってください, わたってください, 行ってください). Laut Einführungsindex wird die Te-Form aber erst in L161 ('Te-Form bilden — drei Gruppen') und 〜てください erst in L160 eingeführt. Im Curriculum (Header: 'in Lernreihenfolge') steht 166 im Modul 'Reise & Ort' VOR dem Modul 'Erste Sätze (Grammatik)' mit L160/L161. Damit wird die Te-Form genutzt und unterrichtet, bevor sie laut Reihenfolge eingeführt wurde. (Die Lektion verweist intern auf 'Lektion 4', was zur tatsächlichen Reihenfolge im Curriculum nicht passt.)  
  _Korrektur:_ Reihenfolge prüfen: Entweder die Te-Form-Lektionen (L160/L161) im Curriculum VOR die Wegbeschreibungs-Lektion 166 ziehen, oder die internen Querverweise ('bereits in Lektion 4 gelernt') und die Te-Form-Voraussetzung explizit korrekt verlinken. Voraussetzungskette (prerequisites) in der Lektion auf die Te-Form-Lektion setzen.
- **L165 · N5 Hobbys & Freizeit — Was machst du gerne?** — 🟡 gering  
  _Fundstelle:_ page_number 5, order_index 2, dialog_slideshow, Slide 8 (Lisa): 'いっしょに スポーツを しましょうか。' (Issho ni supootsu o shimashou ka.)  
  _Problem:_ Die Grammatik 〜ましょうか ('Wollen wir ...?') wird laut Einführungsindex erst in L210 ('〜ましょう / 〜ましょうか') eingeführt, die im selben Modul N5 · Familie & Personen NACH L165 kommt. Der Dialog verwendet die Form also vor ihrer Einführung. Mildernd: Es handelt sich um einen Hör-/Lese-Dialog (rezeptiver Input, nicht prüfungsrelevanter Lehrstoff), und Dialoge greifen didaktisch oft leicht vor.  
  _Korrektur:_ Entweder eine kurze Randglosse zur しましょうか-Form ergänzen (so dass der Lerner die Wendung als Chunk versteht) oder den Vorschlag-Satz auf bereits eingeführte Mittel umformulieren. Da rein rezeptiv im Dialog, ist eine Glosse ausreichend.
- **L190 · N5 Kanji 9 — Verben des Alltags (行来入出見食休)** — 🟡 gering  
  _Fundstelle:_ Seite 2, order_index 2, Beispielsatz "あした、わたしは東京へ行きます。" und Seite 2, order_index 4, Beispielsatz "ともだちがうちへ来ました。" (Partikel へ)  
  _Problem:_ Die Richtungspartikel へ (e) wird laut Einführungsindex erst in L194 eingeführt ('L194: Richtungspartikel へ (e) — das Ziel angeben'). In L190 (order 9) taucht sie unerklärt in zwei Vokabel-Beispielsätzen auf, während die Lektion selbst nur に für Bewegungsziele lehrt. Der Lerner sieht ein noch nicht eingeführtes Zeichen/eine Partikel ohne Erklärung.  
  _Korrektur:_ へ in den Beispielsätzen durch das in dieser Lektion gelehrte に ersetzen (東京に行きます / うちに来ました). Damit löst sich zugleich der Konsistenz-Konflikt auf.
- **L197 · N5 Kleidung & Anziehen — Was ziehst du an?** — 🟡 gering  
  _Fundstelle:_ page_number 4, order_index 3, Grammatik-Karte '～を きています — was jemand gerade trägt (Verlaufsform ています)': 'Mit der Form 「～ています」 (~te imasu) beschreibst du einen andauernden Zustand. … Genauso: 「はいています」 (haite imasu) für unten und 「かぶっています」 (kabutte imasu) für den Kopf.'  
  _Problem:_ Die Lektion benutzt und konjugiert die ています-Verlaufsform (きています / はいています / かぶっています) als bekannten Baustein, obwohl die eigentliche te-Form-Bildung (drei Verbgruppen) sowie die ています-Verlaufsform erst in L161 ('Te-Form bilden — drei Gruppen', '〜ています (te imasu) — Verlaufsform') eingeführt werden. Laut _curriculum.md steht L197 in Sektion 'N5 · Alltag & Essen', L161 jedoch in der späteren Sektion 'N5 · Erste Sätze (Grammatik)' — die Verlaufsform/te-Form-Konjugation wird hier also vor ihrer regulären Einführung verwendet. (Konfidenz nur mittel, da L197 im Einführungsindex selbst als Einführer von ています gelistet ist und das Muster inline mit Beispielen erklärt, also als Chunk self-contained lernbar wäre.)  
  _Korrektur:_ Entweder einen kurzen Hinweis ergänzen, dass die te-Form/ています ausführlich in einer späteren Grammatik-Lektion (L161) behandelt wird und hier nur als feste Wendung pro Kleidungs-Verb gelernt werden soll, oder die konjugierten Nebenformen はいています/かぶっています entschlacken und den Fokus auf die im Index zugewiesene ています-Einführung legen, damit kein unausgesprochener Vorgriff auf die te-Form-Bildung entsteht.

### Konsistenz-Widerspruch

- **L150 · N5 Hiragana 5 — Yōon (kombinierte Silben きゃ/しゃ/ちゃ ...)** — 🟠 mittel  
  _Fundstelle:_ Widerspruch innerhalb L150: Seite 3 (Mora-Tabelle, びょういん=3, びよういん=4) vs. Seite 4, order_index 1, letzte true_false-Frage: "Das Wort 「びょういん」 (byouin, \"Krankenhaus\") besteht aus 4 Mora — und ist damit ein Mora kürzer als 「びよういん」 (biyouin, \"Schönheitssalon\", 5 Mora)."  
  _Problem:_ Die Quiz-Frage auf Seite 4 nennt die KORREKTEN Mora-Zahlen (びょういん=4, びよういん=5), während die Lehrtabelle auf Seite 3 dieselben Wörter mit 3 bzw. 4 angibt. Die Lektion widerspricht sich also selbst — ein Lerner, der beide Stellen vergleicht, wird verwirrt.  
  _Korrektur:_ Seite-3-Tabelle an die korrekten Werte der Seite-4-Frage angleichen (byouin=4, biyouin=5).
- **L177 · N5 Erste Sätze 2 — これ・それ・あれ・どれ und das Partikel の** — 🟠 mittel  
  _Fundstelle:_ Seite 5 (page_number 5), order_index 2 (dialog_slideshow) sowie identisch order_index 3 (Text-Transkript), Slide 2 / 2. Zeile: Sprecher = "Yamada", jp = "それは ぼくの かばんじゃ ありません。やまださんの ですか。" (de: "Das ist nicht meine Tasche. Ist das deine, Yamada?")  
  _Problem:_ Diese Zeile ist im JSON dem Sprecher "Yamada" zugeordnet, der Inhalt fragt aber "やまださんの ですか" (= "Ist das Yamadas (Tasche)?") und die deutsche Übersetzung lautet "Ist das deine, Yamada?". Yamada spricht sich also selbst in der dritten Person an und fragt, ob die Tasche ihm (Yamada) gehört — das ist inhaltlich/erzählerisch unmöglich. Die Zeile muss von Lisa gesprochen werden (sie fragt Yamada), oder der genannte Name ist falsch. Im selben Dialog gibt es nur zwei Sprecher (Lisa, Yamada), aber drei genannte Personen (Yamada, Yuki, Tanaka); die Sprecher-Zuordnung von Slide 2 ist in sich widersprüchlich.  
  _Korrektur:_ Slide 2 dem Sprecher "Lisa" zuweisen (Lisa: "それは わたしの かばんじゃ ありません。やまださんの ですか。") ODER, wenn Yamada sprechen soll, den Namen ändern, sodass er nach einer dritten Person fragt (z. B. "ゆきさんの ですか"). Slideshow-JSON und Text-Transkript (order_index 3) müssen identisch korrigiert werden; auch das line_02-Audio passt nicht zur logischen Sprecherrolle.  
  ⚠️ _Gegenprüfer: Befund stimmt, aber der Auditor-Vorschlag ist fehlerhaft — siehe Begründung._
- **L178 · N5 Uhrzeit — Wie spät ist es?** — 🟠 mittel  
  _Fundstelle:_ Seite 6 (page_number 6), order_index 1, letzte Quiz-Frage (true_false): Frage 'Der Minutenzähler 分 wird immer „ふん“ gelesen, niemals „ぷん“.' — im explanation-Feld: 'aber よんふん (4 Minuten)'  
  _Problem:_ Die explanation der letzten True/False-Frage gibt 4 Minuten als 「よんふん」 (yonfun) an. Das ist falsch und widerspricht direkt dem, was dieselbe Lektion an drei anderen Stellen lehrt: Einführung (S.1) '4 Minuten → よんぷん (yonpun)', Grammatik (S.4) '4分 → よんぷん (yonpun)' und Zusammenfassung (S.7) '4=よんぷん'. Innerhalb der Lektion entsteht so ein direkter Widerspruch, und der Lerner erhält im Quiz-Feedback eine falsche Lesung.  
  _Korrektur:_ In der explanation 「よんふん」 durch 「よんぷん」 ersetzen, z.B.: 'z.B. さんぷん (3 Minuten) oder ろっぷん (6 Minuten), aber にふん (2 Minuten) bzw. ごふん (5 Minuten).' (ein echtes ふん-Beispiel wählen, da 4分 gerade KEIN ふん-Fall ist).
- **L190 · N5 Kanji 9 — Verben des Alltags (行来入出見食休)** — 🟠 mittel  
  _Fundstelle:_ Seite 4 (Grammatik), order_index 1, Text: "Bei Bewegungsverben wie 行く (iku) und 来る (kuru) benutzt du に für den Zielort." — im Widerspruch zu Seite 2, order_index 2 Beispielsatz "あした、わたしは東京へ行きます。" und Seite 2, order_index 4 Beispielsatz "ともだちがうちへ来ました。"  
  _Problem:_ Die Lektion lehrt explizit, dass man bei den Bewegungsverben 行く und 来る die Partikel に für den Zielort benutzt (Grammatikpunkt 'Ziel mit に' ist der einzige zu Bewegungszielen). Genau diese beiden Verben werden in ihren Vokabel-Beispielsätzen aber mit へ konstruiert (東京へ行きます, うちへ来ました), während andere Beispiele derselben Lektion に nutzen (来月日本に行く, 来年大学に行く, 学校に行く). Für einen N5-Anfänger ist dieser unkommentierte Wechsel zwischen に und へ genau bei den gerade gelehrten Verben verwirrend und steht im direkten Widerspruch zur eigenen Erklärung.  
  _Korrektur:_ Entweder die beiden へ-Beispielsätze auf に umstellen (東京に行きます / うちに来ました), um zur Lektions-Grammatik konsistent zu sein, oder im Grammatik-Text einen kurzen Satz ergänzen, dass へ und に bei Bewegungszielen austauschbar sind (へ wird aber erst L194 eingeführt — daher ist Vereinheitlichen auf に hier didaktisch sauberer).
- **L198 · N5 Farben & Beschreiben — Rot, Blau, Gelb und mehr** — 🟠 mittel  
  _Fundstelle:_ Seite 4 (Grammatik), order_index 3, grammar-Item «Farb-Nomen + の + Nomen — あおの ぼうし», im explanation-Feld: «Bei 「ちゃいろ」 (chairo) und 「みどり」 (midori) geht nur dieser Weg, denn sie haben keine i-Form.»  
  _Problem:_ Die Erklärung behauptet, 茶色 (ちゃいろ) habe keine i-Adjektiv-Form. Das ist sachlich falsch: 茶色い (ちゃいろい) ist ein gängiges, reguläres i-Adjektiv (z.B. 茶色い かみ 'braune Haare', 茶色い ふく 'braune Kleidung'). Verschärfend widerspricht sich die Lektion selbst: Genau die parallele 〜色い-Bildung wird eine Seite vorher gelehrt — Seite 2, order_index 8 lehrt 黄色 → 黄色い (きいろい). 黄色→黄色い und 茶色→茶色い sind dieselbe Wortbildung; die Pauschalaussage «keine i-Form» trifft auf 茶色 also nicht zu. (Nur für みどり stimmt die Aussage; 緑い existiert nicht standardsprachlich.)  
  _Korrektur:_ Aussage trennen, statt 茶色 und みどり in einen Topf zu werfen. Z.B.: «Bei 「みどり」 (midori) geht nur dieser Weg, denn es hat keine i-Form.» — und 茶色 entweder weglassen oder korrekt einordnen («茶色 hat zwar auch die Form 茶色い, wird aber als Farbe oft als Nomen mit の verwendet»). So bleibt es konsistent mit dem auf Seite 2 gelehrten 黄色い.
- **L204 · Wetter & Jahreszeiten** — 🟠 mittel  
  _Fundstelle:_ Seite 3 (Vokabeln Teil 2), order_index 8, Vokabel 秋 (あき): example_sentence_japanese "秋は寒いです。秋が好きです。" / example_sentence_english "Aki wa samui desu. Aki ga suki desu. — Der Herbst ist kalt. Ich mag den Herbst."  
  _Problem:_ Der Beispielsatz beschreibt den Herbst als 寒い (samui = kalt, Winterkälte). Das widerspricht der eigenen Lehre derselben Lektion: Auf Seite 4 (Grammatik 〜くなる) heisst es "あきは すずしくなります" (im Herbst wird es kühl), auf Seite 6 (Übung) wird per True/False explizit gelehrt "あきは すずしいです" = "Im Herbst ist es kühl", und die Lektion vermittelt gezielt die Unterscheidung すずしい (kühl) vs. さむい (kalt). Den Herbst hier als 寒い/kalt zu bezeichnen ist sowohl sachlich unpassend (Herbst = すずしい) als auch ein interner Widerspruch, der die zentrale すずしい/さむい-Lektion für Anfänger untergräbt.  
  _Korrektur:_ Beispielsatz ändern zu "秋は涼しいです。秋が好きです。" (Aki wa suzushii desu. Aki ga suki desu. — Der Herbst ist kühl. Ich mag den Herbst.). Damit stimmt das Beispiel mit der Grammatik- und Quiz-Aussage der Lektion überein.
- **L144 · N5 Familie — Wer gehört zu dir?** — 🟡 gering  
  _Fundstelle:_ description ('... 14 interaktiven Quiz-Fragen') und page_number 6, order_index 1, Text 'Teste dein Familien-Wissen' ('**Vierzehn Fragen** zu Familienvokabeln ...') vs. tatsächliche Anzahl der Quiz-Items auf page_number 6  
  _Problem:_ Die Lektionsbeschreibung und das Übungs-Intro sprechen von 14 Fragen, doch die Übungsseite (page 6) enthält tatsächlich 16 Quiz-Items (7 multiple_choice, 4 true_false, 4 matching, plus die abschliessende uchi/soto-true_false-Frage). Die angegebene Zahl stimmt nicht mit dem Inhalt überein. Zusätzlich dupliziert die letzte true_false-Frage (uchi/soto, 父=ちち / 母=はは) thematisch bereits abgedeckten Stoff (vgl. Quiz-Frage 2).  
  _Korrektur:_ Die Zahl im Intro und in der Lektionsbeschreibung an die tatsächliche Anzahl anpassen (16), oder den Fragenkatalog auf 14 kürzen (z.B. die redundante abschliessende uchi/soto-Frage entfernen).
- **L146 · N5 Hiragana 1 — Vokale, K-Reihe und S-Reihe** — 🟡 gering  
  _Fundstelle:_ Seite 2, order_index 1 (Text 'Die Vokale'): '**お (o)** wie in *Onkel*, *Opa* — ein kurzes "o", **nicht** so lang wie in *Boot*' VS. Seite 4, order_index 1, Quiz-Frage 'Welche Romaji-Lesung passt zu 「お」?', explanation: '「お」 ist der Vokal **o**, ähnlich wie 'Boot' (kurz).'  
  _Problem:_ Dasselbe Wort 'Boot' wird innerhalb derselben Lektion einmal als Gegenbeispiel ('nicht so lang wie in Boot') und einmal als positives Aussprache-Beispiel ('ähnlich wie Boot (kurz)') für den Vokal お verwendet. Das widerspricht sich und verwirrt den Lerner. Sachlich ist die Lehrtext-Aussage richtig (das deutsche 'oo' in Boot ist lang, das japanische お kurz), die Quiz-Erklärung untergräbt sie.  
  _Korrektur:_ In der Quiz-Erklärung das Beispiel 'Boot' streichen und an die Lehrtext-Linie angleichen, z.B. '「お」 ist der kurze Vokal o (wie in 'Onkel', nicht gedehnt wie in 'Boot').'
- **L148 · N5 Hiragana 3 — M-Reihe, Y-Reihe, R-Reihe, W-Reihe und ん** — 🟡 gering  
  _Fundstelle:_ Seite 3, order_index 1 (Text 'Verwechslungsgefahr'): 're = kleiner **Haken** nach oben links' VS. Seite 4, order_index 1, Quiz-Frage 'Welches Zeichen ist **wa**?', Feedback zur Option 「れ」: '「れ」 ist re — hat einen Haken nach oben rechts.'  
  _Problem:_ Die Richtung des Hakens von 「れ」 (re) wird innerhalb derselben Lektion einmal als 'nach oben links' und einmal als 'nach oben rechts' beschrieben. Da das Zeichen gerade als Verwechslungs-Unterscheidungsmerkmal gegen ね/わ dienen soll, ist die widersprüchliche Richtungsangabe didaktisch schädlich.  
  _Korrektur:_ Beide Stellen auf dieselbe Richtungsangabe vereinheitlichen. (Der nach rechts auslaufende, leicht hochgezogene Schlussstrich von れ ist die geläufigere Beschreibung — beide Stellen entsprechend angleichen.)
- **L150 · N5 Hiragana 5 — Yōon (kombinierte Silben きゃ/しゃ/ちゃ ...)** — 🟡 gering  
  _Fundstelle:_ Seite 4, order_index 1, multiple_choice "Was bedeutet 「ぎゅうにゅう」?", Feld hint: "Fünf Schriftzeichen, zwei davon Yōon: ぎゅう + にゅう. Hochfrequentes Alltagswort."  
  _Problem:_ ぎゅうにゅう besteht aus 6 Kana-Zeichen (ぎ・ゅ・う・に・ゅ・う), nicht aus fünf. Der Hint sagt "Fünf Schriftzeichen", die Erklärung derselben Frage sagt korrekt, es seien "4 Mora ... nicht 6" (und zählt damit implizit 6 Zeichen).  
  _Korrektur:_ Im Hint "Fünf" auf "Sechs" ändern (sechs Kana, davon zwei Yōon-Paare = 4 Mora).
- **L151 · N5 Katakana 1 — Vokale, K-Reihe und S-Reihe** — 🟡 gering  
  _Fundstelle:_ Seite 4 (page_number 4), order_index 1, Quiz-Frage «Welche Romaji-Lesung passt zu 「オ」?», explanation: «「オ」 ist der Vokal o, kurz wie in 'Boot'.»  
  _Problem:_ Die Quiz-Erklärung sagt, das o sei 'kurz wie in Boot'. Das widerspricht direkt dem Lehrtext derselben Lektion auf Seite 2 (order_index 1), wo ausdrücklich steht: «オ (o) … ein kurzes 'o', NICHT so lang wie in Boot». Zudem ist es phonetisch irreführend, weil das deutsche 'Boot' ein langes o [oː] hat — kein Vorbild für das kurze japanische o.  
  _Korrektur:_ explanation angleichen, z.B.: «「オ」 ist der Vokal o, kurz wie in 'Onkel'/'Opa' — nicht so lang wie in 'Boot'.»
- **L154 · N5 Katakana 4 — Dakuten, Handakuten und Längungsstrich (ガ, ザ, ダ, バ, パ, ー)** — 🟡 gering  
  _Fundstelle:_ Widerspruch zwischen page_number 2, order_index 7 (Z-Reihe-Text, Tofugu-Stolperfalle) und page_number 4, order_index 1, Quiz-Frage 2 ('Wie liest man 「ジ」?') explanation  
  _Problem:_ Der Lektionstext warnt ausdrücklich, 「ジ」 (ji) NICHT mit dem englischen 'j' gleichzusetzen ('Verwechsle 「ジ」 (ji) nicht mit dem englischen "j" wie in jet — das japanische ji ist weicher, fast wie Dschungel'). Die Quiz-Erklärung zu derselben Silbe sagt aber genau das Gegenteil: '「ジ」 (ji), wie englisches j in Jeans'. Das ist ein interner Widerspruch in der Lernanweisung innerhalb derselben Lektion und verwirrt Lernende.  
  _Korrektur:_ Quiz-Erklärung an die Lektion angleichen, z.B. '「ジ」 (ji), gesprochen wie ein weiches dsch in Dschungel' — nicht 'wie englisches j in Jeans'.
- **L154 · N5 Katakana 4 — Dakuten, Handakuten und Längungsstrich (ガ, ザ, ダ, バ, パ, ー)** — 🟡 gering  
  _Fundstelle:_ description (Lektions-Beschreibung): "Lerne die 25 Katakana mit Diakritika (ガ-ぱ-Reihen) ..."  
  _Problem:_ In der Reihen-Spanne '(ガ-ぱ-Reihen)' ist das letzte Zeichen 「ぱ」 ein HIRAGANA-pa, nicht das Katakana 「パ」. In einer reinen Katakana-Lektion sollte hier das Katakana stehen (der Titel verwendet korrekt 「パ」).  
  _Korrektur:_ '(ガ-ぱ-Reihen)' korrigieren zu '(ガ–パ-Reihen)'.
- **L158 · N5 Begrüssung & Höflichkeit 3 — Am Telefon** — 🟡 gering  
  _Fundstelle:_ page_number 4, order_index 1, Text 'Drei Bausteine für jedes Telefongespräch': "Bei Gegenständen wird stattdessen 「あります」 (arimasu) verwendet — das siehst du in der nächsten Lektion." (auch im Grammatik-Item order_index 2 wiederholt)  
  _Problem:_ Der Vorwärtsverweis ist sachlich falsch. Die laut Curriculum unmittelbar nächste Lektion ist L159 (Entschuldigen & Geschenke übergeben), die あります nicht behandelt (Themen: Adverb-Form, どうぞ-Geschenkübergabe, もう/まだ). あります wird erst in L160 (Erste Sätze 3 — 'Existenz: ～が あります') eingeführt. Der Lerner sucht den Inhalt also in der falschen Lektion.  
  _Korrektur:_ Formulierung neutralisieren, z.B. 'das lernst du in einer späteren Lektion' statt 'in der nächsten Lektion' — oder konkret auf die Existenz-Lektion (L160) verweisen.
- **L158 · N5 Begrüssung & Höflichkeit 3 — Am Telefon** — 🟡 gering  
  _Fundstelle:_ page_number 1, order_index 1, Text 'Willkommen', Abschnitt 'Was du nach dieser Lektion kannst': "Höflich um Wiederholung bitten: 「もう いちど おねがいします」 (mō ichido onegai shimasu — Bitte noch einmal)." sowie der Lerntipp zu Telefonnummern (「ーの」, ぜろ/まる)  
  _Problem:_ Die Einführung verspricht zwei Lernergebnisse, die im Lektionskörper nie gelehrt werden: (1) 「もう いちど おねがいします」 als Wiederholungsbitte taucht im gesamten Stoff (Vokabeln, Grammatik, Dialog) nicht auf — nur als Quiz-DISTRAKTOR 「もう いちど」 (p5 Q2, p6 Q7), wo es als FALSCH markiert ist, ohne je eingeführt worden zu sein. (2) Das Lesen/Sprechen von Telefonnummern im Telefon-Stil (「ーの」, ぜろ/まる für 0) wird im Lerntipp und in der Beschreibung angekündigt, aber nirgends vermittelt. Versprechen und Inhalt klaffen auseinander.  
  _Korrektur:_ Entweder ein kurzes Vokabel-/Grammatik-Element zu 「もう いちど おねがいします」 und zur Telefonnummern-Lesung ergänzen, oder beide Versprechen aus der Einführung/Beschreibung streichen, damit der angekündigte Lernumfang dem tatsächlichen Inhalt entspricht.
- **L159 · N5 Begrüssung & Höflichkeit 4 — Entschuldigen und Geschenke übergeben** — 🟡 gering  
  _Fundstelle:_ Seite 7, order_index 1 (Text 'Geschafft!'): "In der nächsten Lektion (N5 Erste Sätze 3) lernst du die wichtigsten Verb-Formen: ます/ました/ません/ませんでした (Gegenwart, Vergangenheit, Negation) und die Existenz-Verben います/あります."  
  _Problem:_ Der 'Was kommt als Nächstes?'-Verweis nennt 'N5 Erste Sätze 3' (= Lektion 160) als nächste Lektion. Laut Curriculum ist nach L159 (Begrüssung & Höflichkeit 4) jedoch NICHT L160 die nächste Lektion — L160 'Erste Sätze 3' steht im Modul 'Erste Sätze (Grammatik)' weit später in der Lernreihenfolge, nach Familie/Alltag/Reise. Der Ausblick führt den Lernenden auf eine falsche Folge-Lektion.  
  _Korrektur:_ Verweis an die tatsächliche Curriculum-Reihenfolge anpassen (nach L159 folgt das Modul 'Familie & Personen', beginnend mit L144 'N5 Familie — Wer gehört zu dir?'), oder den konkreten Lektionsnamen entfernen und neutral auf 'die nächste Lektion' verweisen.
- **L162 · N5 Reise & Ort — In der Stadt: Bahnhof, Bank, Park** — 🟡 gering  
  _Fundstelle:_ page_number 1, order_index 1 ('Orientierung in der Stadt'), Zitat: '18 Stadt-Vokabeln — von 「えき」 (eki, Bahnhof) bis 「こうさてん」 (kousaten, Kreuzung).'  
  _Problem:_ Die Einführung verspricht 18 Stadt-Vokabeln 'bis こうさてん (kousaten, Kreuzung)'. こうさてん (交差点) kommt in Lektion 162 jedoch gar nicht vor — das Wort wird erst in Lektion 166 (Wegbeschreibung) eingeführt. Der Lerner sucht das angekündigte Wort vergeblich.  
  _Korrektur:_ Ankündigung korrigieren: das Bis-Beispiel auf ein tatsächlich in 162 enthaltenes Wort ändern (z.B. '… bis 「ちかく」 (chikaku, Nähe)' oder '… bis 「びょういん」 (byouin, Krankenhaus)').
- **L165 · N5 Hobbys & Freizeit — Was machst du gerne?** — 🟡 gering  
  _Fundstelle:_ page_number 1, order_index 1, Text 'Hobbys sind die schnellste Brücke...' — Aufzählung 'Sportarten: やきゅう (yakyuu, Baseball), サッカー (sakkaa), ダンス (dansu).' vs. page_number 3 (Vokabelkarten ゲーム, カラオケ statt ダンス) vs. page_number 7, order_index 1, Zusammenfassung 'Sportarten: やきゅう, サッカー, ゲーム, カラオケ.'  
  _Problem:_ Innerer Widerspruch in der Lektion: Die Einführung (Seite 1) kündigt ダンス (Tanz) als zu lernende Sportart an, doch ダンス kommt nirgends als Vokabelkarte vor. Stattdessen werden auf Seite 3 ゲーム (Videospiel) und カラオケ (Karaoke) gelehrt. Die Zusammenfassung (Seite 7) etikettiert ゲーム und カラオケ wiederum als 'Sportarten', was sachlich unzutreffend ist (Videospiel und Karaoke sind keine Sportarten).  
  _Korrektur:_ Seite-1-Ankündigung an die tatsächlich gelehrten Vokabeln angleichen (ダンス durch ゲーム/カラオケ ersetzen oder die Aufzählung neutral als 'Freizeitaktivitäten' fassen). In der Seite-7-Zusammenfassung ゲーム/カラオケ nicht unter 'Sportarten' führen, sondern z.B. unter 'Freizeitaktivitäten / Spiele'.
- **L166 · N5 Wegbeschreibung — Rechts, links, geradeaus** — 🟡 gering  
  _Fundstelle:_ page_number 2 — Vokabel-Karten order_index 6 (信号/しんごう), order_index 7 (交差点/こうさてん), order_index 8 (橋/はし)  
  _Problem:_ In einer als N5 deklarierten Lektion (category_jlpt_level 5, jede Vokabel sonst jlpt_level 5) tragen drei Vokabeln im Datenfeld explizit jlpt_level 4: 信号 (しんごう), 交差点 (こうさてん) und 橋 (はし). Das ist ein interner Widerspruch zwischen dem jlpt_level-Feld der Items und der N5-Einstufung der Lektion/Plattform. 信号 und 交差点 sind in den Standard-JLPT-Listen tatsächlich N4 — die Lektion stuft sie selbst (Feld) ebenfalls als 4 ein.  
  _Korrektur:_ jlpt_level der drei Items auf den korrekten Wert vereinheitlichen bzw. konsistent zur Lektion machen. Wenn die Wörter thematisch nötig sind (Wegbeschreibung), als 'über-N5-Hilfsvokabel' kennzeichnen, statt sie widersprüchlich mal als 4, mal implizit als N5-Lektionsinhalt zu führen.
- **L168 · N5 Kanji 3 — Menschen (人男女子友) und Familie** — 🟡 gering  
  _Fundstelle:_ Seite 1, order_index 1, Text 'Sieben Kanji über Menschen', Abschnitt 'Warum Menschen-Kanji als dritter Block?': 'Wenig Striche: 人 (2), 子 (3), 女 (3), 大 (3) — alle sehr machbar.'  
  _Problem:_ In der Strichzahl-Aufzählung der Lektions-Kanji wird 大 mitgezählt, obwohl 大 KEIN Kanji dieser Lektion ist. Die sieben Kanji der Lektion sind laut Titel/Einführung 人, 男, 女, 子, 友, 父, 母. 大 erscheint hier nirgends als Kanji-Karte und wird laut Einführungsindex erst in L170 eingeführt. Das verwirrt den Lerner, weil 大 wie ein zu lernendes Lektions-Kanji wirkt.  
  _Korrektur:_ 大 (3) aus der Strichzahl-Aufzählung streichen und stattdessen ein tatsächliches Lektions-Kanji nennen (z.B. 友 (4)) oder die Liste auf die sieben Lektions-Kanji beschränken.
- **L169 · N5 Kanji 4 — Natur (山川木雨) und Wetter** — 🟡 gering  
  _Fundstelle:_ page_number 1, order_index 1 ("「た」 (ta) — Reisfeld (Bonus, Kanji ist eigentlich N4 ...") + page_number 7, order_index 1 ("そら (sora, Himmel) — N4-Kanji") vs. Kanji-Karten page_number 2: 田 (order_index 6) und 空 (order_index 5), beide "jlpt_level": 5  
  _Problem:_ Innerer Widerspruch zwischen Lauftext und Kanji-Metadaten. Der Einführungstext (Seite 1) und die Zusammenfassung (Seite 7) bezeichnen 田 und そら/空 als N4-Kanji, während die zugehörigen Kanji-Karten auf Seite 2 beide jlpt_level: 5 tragen. Zusätzlich ist die Sachaussage falsch: 空 (sora) ist ein offizielles N5-Kanji, nicht N4 — hier ist die Karte richtig und der Lauftext falsch. (田 wird je nach Liste N4/N5 geführt; der Widerspruch zur Karte bleibt.)  
  _Korrektur:_ Lauftext und Karten-Metadaten angleichen: 空 als N5 darstellen (Aussage "N4-Kanji" auf Seite 1 und 7 streichen). Für 田 eine einheitliche Level-Angabe in Karte und Text festlegen.  
  ⚠️ _Gegenprüfer: Befund stimmt, aber der Auditor-Vorschlag ist fehlerhaft — siehe Begründung._
- **L172 · N5 Kanji 7 — Grosse Zahlen, Geld & Zeit (百千万円半年時分)** — 🟡 gering  
  _Fundstelle:_ Seite 7 (Zusammenfassung & Ausblick), order_index 1, Abschnitt 'Wie es weitergeht': "Lesson 8 — N5 Kanji 8: Eigenschaften — neun i-Adjektiv-Kanji (gross, klein, neu, alt, hoch, günstig, lang, kurz, früh)"  
  _Problem:_ Die Vorschau auf die Folgelektion (L173) listet die abgedeckten Kanji-Bedeutungen falsch auf: Sie nennt 'gross, klein' (= 大小), L173 deckt laut Titel und Inhalt aber 多少 (viel/wenig) ab, NICHT 大小. Die tatsächlichen fünf Gegensatzpaare von L173 sind neu/alt, hoch/günstig, lang/kurz, viel/wenig, früh — die Vorschau ersetzt 'viel/wenig' irrtümlich durch 'gross/klein'.  
  _Korrektur:_ Liste korrigieren zu: 'neu, alt, hoch, günstig, lang, kurz, viel, wenig, früh' (entsprechend 新古高安長短多少早).
- **L174 · N5 Begrüssung 1 — Selbstvorstellung** — 🟡 gering  
  _Fundstelle:_ page_number 3, order_index 1 (Text 'Berufe und Länder'), unter der Überschrift '### Länder': '- **にほんじん (Nihon-jin)** — *Japaner/in*' — und ebenso page_number 7, order_index 1 (Zusammenfassung) unter 'Länder:' 'にほん (Nihon), にほんじん (Nihon-jin), ...'  
  _Problem:_ にほんじん (Japaner/in) wird unter der Rubrik 'Länder' aufgeführt, obwohl es eine Nationalitäts-/Personenbezeichnung ist, kein Land. Das Land ist にほん (steht in derselben Liste). Dadurch stehen Land (にほん) und Bewohner (にほんじん) vermischt unter einer falschen Überschrift; die Vokabelkarte selbst ist korrekt mit 'Japaner(in)' beschriftet, nur die Sektions-Überschrift kategorisiert falsch.  
  _Korrektur:_ にほんじん entweder unter eine eigene Rubrik 'Nationalitäten/Personen' verschieben oder die Überschrift zu 'Länder & Nationalitäten' erweitern. In der Zusammenfassung (Seite 7) konsequent gleich behandeln. Alternativ direkt nach にほん als Beispiel für das じん-Muster ausweisen statt als Länder-Eintrag.
- **L175 · N5 Erste Sätze 1 — です-Form und Partikel は** — 🟡 gering  
  _Fundstelle:_ Seite 1 (page_number 1), order_index 1 (text, "Die fünf Bausteine"): aufgezählt werden です, は, じゃ ありません, ですか, も — im Vergleich zu Seite 4 (order_index 1, "Fünf Muster"), Seite 6 (order_index 1) und Seite 7 (order_index 1), die jeweils です, じゃ ありません, でした, ですか, も auflisten.  
  _Problem:_ Die Lektion definiert die "fünf Bausteine" auf der Einführungsseite anders als auf allen späteren Seiten. Seite 1 nennt 「は」 als Baustein und lässt 「でした」 (Vergangenheit) weg; Seiten 4/6/7 nennen 「でした」 und lassen 「は」 weg. 「でした」 wird tatsächlich gelehrt (Vokabel Seite 2, Grammatik-Pattern Seite 4 #3, zwei Quizfragen auf Seite 6) — es als Kern-Baustein auf der Einführungsseite zu unterschlagen ist inkonsistent und irritiert beim Wiedererkennen.  
  _Korrektur:_ Die fünf Bausteine über alle Seiten vereinheitlichen. Empfohlen: です, じゃ ありません, でした, ですか, も (deckt die vier auf Seite 4 gezeigten Muster + も ab), und 「は」 separat als Themen-Partikel beschreiben statt es als einen der fünf Bausteine zu zählen — so wie es Seiten 4/6/7 bereits handhaben.
- **L176 · N5 Begrüssung 2 — Alltagsgrüsse rund um den Tag** — 🟡 gering  
  _Fundstelle:_ page_number 6, order_index 1, Einleitungstext "Übung": "Die vierzehn folgenden Fragen testen alle vier Tageszeit-Grüsse ..."  
  _Problem:_ Der Text kündigt "vierzehn" Fragen an, tatsächlich enthält die Übungsseite 16 Quizfragen (10 multiple_choice, 3 true_false zusätzlich zu den hier nicht gezählten, 3 matching). Die Zahl stimmt nicht mit dem tatsächlichen Quiz überein.  
  _Korrektur:_ Zahl auf "sechzehn" korrigieren oder die generische Formulierung "Die folgenden Fragen ..." ohne Zahl verwenden, damit der Text robust gegen spätere Änderungen der Fragenzahl ist.
- **L190 · N5 Kanji 9 — Verben des Alltags (行来入出見食休)** — 🟡 gering  
  _Fundstelle:_ Seite 3 (Die Kanji — Teil 2), order_index 3, Vokabel 出口: "reading": "でぐち (deguchi)", "romaji": null, "meaning_de": null, "jlpt_level": 4  
  _Problem:_ Der Vokabeleintrag 出口 ist gegenüber allen anderen Vokabeln dieser Lektion defekt/inkonsistent angelegt: jlpt_level steht auf 4 (alle anderen Einträge und die gesamte Lektion sind N5), meaning_de ist null (Bedeutung steht nur im englischen Feld), romaji ist null, und das Romaji '(deguchi)' ist zusätzlich ins reading-Feld gequetscht. Das Gegenstück 入口 (order_index 11 auf Seite 2) ist dagegen vollständig und korrekt mit jlpt_level 5 erfasst. 出口 ist echtes N5-Vokabular — der Fehler ist das Datenschema des Eintrags, NICHT das Wort selbst.  
  _Korrektur:_ Eintrag normalisieren: jlpt_level auf 5 setzen, reading auf 'でぐち', romaji auf 'deguchi', meaning_de auf 'Ausgang' — analog zum korrekt erfassten 入口-Eintrag.
- **L203 · Tagesablauf — Verben (ます-Form, masu-kei)** — 🟡 gering  
  _Fundstelle:_ Seite 2 (Vokabeln Teil 1), order_index 11, Vokabel 出かける: example_sentence_japanese "母は今出かける。" / example_sentence_english "Haha wa ima dekakeru. — Meine Mutter geht jetzt aus."  
  _Problem:_ Diese Lektion lehrt durchgehend die höfliche ます-Form (masu-kei) und ALLE übrigen ~23 Vokabel-Beispielsätze stehen konsequent in der höflichen Form (起きます, 寝ました, 食べました, 飲みます, 行きます, 来ました, 帰ります, 歩きます, 待ちます ...). Nur dieses eine Beispiel steht in der schlichten Wörterbuch-/Plain-Form (出かける statt 出かけます). Das widerspricht dem Lernziel der Lektion und wirkt für den Lernenden, der gerade die ます-Form übt, inkonsistent und verwirrend.  
  _Korrektur:_ Beispielsatz an die ます-Form angleichen, z. B. "母は今出かけます。" (Haha wa ima dekakemasu. — Meine Mutter geht jetzt aus.). Optional ein alltagsnäheres Subjekt/Adverb (z. B. これから), aber zentral ist die Vereinheitlichung auf 出かけます.
- **L205 · Körper & Gesundheit — Beim Arzt** — 🟡 gering  
  _Fundstelle:_ page_number 7, order_index 1, Text 'Das hast du gelernt' / Abschnitt 'Lerntipp & Ausblick': "In der nächsten Lektion geht es um das Wetter und die Jahreszeiten — perfekt, um zu verstehen, warum man sich manchmal eine かぜ (kaze, Erkältung) holt."  
  _Problem:_ Die Zusammenfassung kündigt als 'nächste Lektion' das Thema Wetter & Jahreszeiten an. Laut Curriculum (_curriculum.md, ausdrücklich 'in Lernreihenfolge') steht die Lektion 'N5 · Wetter & Jahreszeiten' (L204) jedoch VOR L205 'Körper & Gesundheit — Beim Arzt'. Der Ausblick verweist damit auf eine Lektion, die in der Lernreihenfolge bereits davor liegt, statt auf die tatsächlich folgende.  
  _Korrektur:_ Den Ausblick auf die tatsächlich nachfolgende Lektion korrigieren (laut Curriculum-Reihenfolge L206 'Wohnen — Haus & es gibt') oder den thematischen Vorwärtsverweis ganz entfernen, damit die Lernenden nicht auf eine bereits absolvierte Lektion verwiesen werden.
- **L206 · Wohnen — Haus & "es gibt"** — 🟡 gering  
  _Fundstelle:_ Seite 3 (Vokabeln Teil 2), order_index 3 — Vokabel 机 (つくえ), example_sentence: "机の上に本があります。 — Auf dem Tisch liegt ein Buch." vs. Seite 4 (Grammatik), order_index 1+2 — derselbe Satz "つくえの うえに ほんが あります。 — Auf dem Schreibtisch liegt ein Buch."  
  _Problem:_ Derselbe Beispielsatz (つくえの うえに ほんが あります) wird innerhalb der Lektion zweimal unterschiedlich übersetzt: einmal als 'Tisch' (Vokabelkarte 机), einmal als 'Schreibtisch' (Grammatik-Text und Grammatik-Karte). 机 ist spezifisch der Schreibtisch; die Zusammenfassung (Seite 7) listet 机 ebenfalls nur als 'Schreibtisch'. Die uneinheitliche Übersetzung kann Lernende verwirren.  
  _Korrektur:_ Übersetzung vereinheitlichen — durchgehend 'Schreibtisch' verwenden (oder die Vokabel-meaning_de auf 'Schreibtisch (auch: Tisch)' präzisieren) und den Vokabel-Beispielsatz auf "Auf dem Schreibtisch liegt ein Buch." angleichen.

### Progression

- **L147 · N5 Hiragana 2 — T-Reihe, N-Reihe und H-Reihe** — 🟡 gering  
  _Fundstelle:_ Seite 2, order_index 7 (Text 'Die N-Reihe (na, ni, nu, ne, no)'), Abschnitt 'Mini-Wörter': 「のむ」 (nomu, 'trinken')  
  _Problem:_ Das Beispielwort 「のむ」 enthält das Zeichen 「む」 (mu) aus der M-Reihe, die erst in Lektion 148 (Hiragana 3) eingeführt wird. Die Lektion präsentiert es jedoch als Wort, das der Lerner mit dem bisher Gelernten (Vokale + K/S/T/N/H) bereits lesen können soll — das kann er nicht. Im selben Lektionskontext wird 「ほん」 korrekt als 'kommt mit ん in Hiragana 3 dazu' gekennzeichnet, 「のむ」 ist also ein Versehen, kein Konzept.  
  _Korrektur:_ 「のむ」 entfernen oder durch ein Wort ersetzen, das nur aus bereits eingeführten Zeichen (Vokale, K-, S-, T-, N-, H-Reihe) besteht, z.B. 「ぬの」 (nuno, 'Stoff/Tuch') oder 「にく」 (niku, 'Fleisch').
- **L155 · N5 Katakana 5 — Yōon und Lehnwort-Spezialitäten (キャ, ティ, ファ ...)** — 🟡 gering  
  _Fundstelle:_ page_number 4, order_index 1, Quiz-Frage 'Wie liest man 「シェフ」?' (Antwort 'shefu')  
  _Problem:_ Die Frage prüft die Spezialsilbe 「シェ」 (she). Diese Kombination wird im Lektionstext (page 2 order_index 14, page 3 order_index 1) nirgends eingeführt oder erklärt — die Lehnwort-Spezialitäten-Übersicht listet T-/F-/W-/V-Familie, aber nicht die SH-/CH-/J-Vokal-Specials (シェ/チェ/ジェ). Das Quiz testet damit Stoff, der nicht explizit gelehrt wurde.  
  _Korrektur:_ Entweder 「シェ」 (und ggf. 「チェ」/「ジェ」) kurz in der Lehnwort-Spezialitäten-Übersicht ergänzen, oder die Frage durch eine ersetzen, die eine im Text behandelte Silbe (ティ/ファ/ウィ ...) prüft.

### Klarheit / Erklärung

- **L155 · N5 Katakana 5 — Yōon und Lehnwort-Spezialitäten (キャ, ティ, ファ ...)** — 🟠 mittel  
  _Fundstelle:_ page_number 2, order_index 14, Text 'Lehnwort-Spezialitäten — was es nur in Katakana gibt', Abschnitt 'V-Familie — der Sonderfall': "Es nutzt 「ヴ」 — ein U mit Dakuten (von フ + ゛ inspiriert) — plus Vokale"  
  _Problem:_ Der Klammerzusatz '(von フ + ゛ inspiriert)' ist sachlich falsch und widerspricht der Aussage im selben Satz. Korrekt ist 「ヴ」 = ウ (u) + Dakuten. フ (fu) + Dakuten ergibt 「ブ」 (bu), NICHT 「ヴ」 (vu). Der Satz nennt zuerst richtig 'ein U mit Dakuten', leitet dann aber fälschlich von フ ab — das verwechselt vu mit bu und untergräbt genau die Unterscheidung, die die Lektion lehren will.  
  _Korrektur:_ Klammer korrigieren zu '(ウ + ゛, also U mit Dakuten)' bzw. den falschen Hinweis 'von フ + ゛ inspiriert' streichen.
- **L191 · N5 Kanji 10 — Sprechen, Lesen und Schreiben (話聞読書語名何)** — 🟠 mittel  
  _Fundstelle:_ Lektion 191, Seite 4 (Grammatik), order_index 4, Grammatik-Item Titel: "～が + できます / Verb der Fähigkeit (ga)" — explanation: "Um zu sagen, was man kann, markierst du das Können mit が (ga). Sehr häufig ist 日本語が分かります (nihongo ga wakarimasu, ich verstehe Japanisch)." example_sentences: "日本語が分かります。 ... えいごが分かりますか。"  
  _Problem:_ Der Titel kündigt できます (Potential-/Fähigkeitsform) an, doch im gesamten Grammatik-Item taucht できます kein einziges Mal auf — gelehrt wird ausschliesslich 分かります (wakarimasu = verstehen). 分かる ist KEIN Fähigkeitsverb/Potentialverb, sondern bedeutet 'verstehen'. Die Gleichsetzung von 「日本語が分かります」mit dem Muster '～が + できます / Verb der Fähigkeit' vermischt zwei verschiedene N5-Grammatikpunkte (Potential できる vs. 分かる) und ist sachlich irreführend.  
  _Korrektur:_ Entweder den Titel auf das tatsächlich gelehrte Muster korrigieren (z. B. "～が + 分かります (ga — etwas verstehen)"), oder mindestens ein echtes できます-Beispiel ergänzen (z. B. 日本語が話せます / 日本語ができます) und 分かります nicht als 'Verb der Fähigkeit' bezeichnen.
- **L143 · N5 Zahlen — Von 1 bis 10'000** — 🟡 gering  
  _Fundstelle:_ Seite 1 (page_number 1), order_index 1, Text 'Warum Zahlen zuerst?': 'Am Ende der Lektion wirst du verstehen, wieso vier verschiedene Aussprachen für die Ziffer 4 existieren (よん / yon und し / shi) und wann du welche nutzt.'  
  _Problem:_ Der Text behauptet 'vier verschiedene Aussprachen für die Ziffer 4', nennt in der Klammer aber nur ZWEI (よん und し). Die Zahl 'vier' ist sachlich nicht gedeckt — die Ziffer 4 hat im N5-Kontext drei relevante Lesungen (よん, し und よ wie in よじ/よっつ), nicht vier. Die genannte Zahl widerspricht der eigenen Aufzählung und verwirrt.  
  _Korrektur:_ Auf 'mehrere verschiedene Aussprachen' oder konkret 'die Lesungen よん (yon), し (shi) und よ (yo, z.B. in よじ)' korrigieren — die Zahl 'vier' streichen, da sie nicht stimmt und nicht belegt wird.
- **L153 · N5 Katakana 3 — M-Reihe, Y-Reihe, R-Reihe, W-Reihe und ン** — 🟡 gering  
  _Fundstelle:_ Seite 1 (page_number 1), order_index 1, Abschnitt 'Achtung — die zweite grosse Verwechslungsfalle': «… kommt jetzt **ハer Twin-Falle Nr. 2**: 「ン」 (n) und 「ソ」 (so, aus K1) …»  
  _Problem:_ Im Fliesstext steht das fehlplatzierte Katakana-Zeichen 「ハ」 mitten im deutschen Wort ('ハer' statt 'der') und das englische 'Twin-Falle' mischt sich unmotiviert ein. Der Satz ist dadurch sprachlich defekt und für Anfänger irritierend (ausgerechnet in einer Kana-Lektion, wo 「ハ」 als Glyphe verwirrt).  
  _Korrektur:_ Korrigieren zu: «… kommt jetzt die zweite Verwechslungsfalle: 「ン」 (n) und 「ソ」 (so, aus K1) sehen sich extrem ähnlich.»
- **L157 · N5 Alltag & Essen 2 — Was möchtest du essen?** — 🟡 gering  
  _Fundstelle:_ page_number 2, order_index 1, Text 'Lebensmittel und Getränke': Abschnitt 'Und fünf **Getränke und kleine Gerichte**:' mit Aufzählung ぎゅうにゅう / こうちゃ / コーヒー / カレー / ちゃわん (chawan) — *Reisschale*  
  _Problem:_ ちゃわん (chawan) wird im einleitenden Text unter der Überschrift 'fünf Getränke und kleine Gerichte' aufgezählt, zusammen mit Milch, Schwarztee, Kaffee und Curry. ちゃわん ist aber weder ein Getränk noch ein Gericht, sondern Geschirr (Reis-/Teeschale). Die Vokabelkarte selbst (order_index 11) übersetzt es korrekt als 'Reisschale' — der einleitende Text kategorisiert das Wort jedoch sachlich falsch und ist für Lernende irreführend.  
  _Korrektur:_ ちゃわん aus der Kategorie 'Getränke und kleine Gerichte' herausnehmen und separat als Geschirr/Esswerkzeug einordnen (z.B. zusammen mit はし auf der nächsten Seite), oder die Überschrift so anpassen, dass Geschirr klar abgegrenzt ist. Die Zählung 'fünf' entsprechend korrigieren.
- **L160 · N5 Erste Sätze 3 — Vergangenheit, Existenz und höfliche Bitten** — 🟡 gering  
  _Fundstelle:_ Seite 4 (page_number 4), order_index 2 (grammar, Titel "Vier Tempus-Formen: ます / ました / ません / ませんでした"), explanation: "Diese Formen entstehen vom Verb-Stamm (z.B. たべ aus たべる, der die Endung 「る」 wegnimmt)."  
  _Problem:_ Die Stammbildung wird mit der ichidan-Regel "die Endung 「る」 wegnehmen" als allgemeine Regel dargestellt. Für die godan-Verben derselben Lektion (よむ→よみます, かく→かきます, いく→いきます, あう→あいます) stimmt das nicht: deren ます-Stamm endet auf einen i-Laut (よみ, かき, いき, あい), und mehrere dieser Verben enden nicht einmal auf る. Ein Lernender, der "る wegnehmen" auf よむ anwendet, kommt zu einem falschen Ergebnis. Die Lektion mischt ichidan- und godan-Verben, gibt aber nur die ichidan-Stammregel.  
  _Korrektur:_ Formulierung relativieren, z. B.: "... vom Verb-Stamm (bei る-Verben wie たべる fällt る weg → たべ; bei u-Verben wie よむ ändert sich der Endvokal zu i → よみ). Die genauen Verbgruppen lernst du in der nächsten Lektion." Alternativ den Halbsatz "der die Endung 「る」 wegnimmt" streichen, da die Lektion die Konjugationsregeln ohnehin auf später verschiebt.
- **L167 · N5 Kanji 2 — Tage und Wochentage (日月火水木金土)** — 🟡 gering  
  _Fundstelle:_ Seite 4, order_index 3, Grammatik 'On- und Kun-Lesung am Beispiel 月 (Mond, Monat)', im explanation-Feld: 'In Mengenangaben für Monate ist es 「げつ」 (kagetsu = ein Monat).'  
  _Problem:_ Die Glosse 'kagetsu = ein Monat' ist irreführend/sachlich ungenau. かげつ (〜か月) ist ein Zähl-Suffix für eine Anzahl von Monaten und steht NIE allein für 'ein Monat'; es braucht zwingend eine Zahl davor. 'Ein Monat' heisst 一か月 (いっかげつ, ikkagetsu), nicht 'kagetsu'. Das eigene Beispiel der Lektion (三か月, san-kagetsu = drei Monate) widerspricht der Glosse sogar.  
  _Korrektur:_ Formulierung korrigieren, z.B.: 'In Mengenangaben für Monate ist es 「げつ」 (z.B. 一か月 = いっかげつ, ein Monat; 三か月 = さんかげつ, drei Monate).'
- **L170 · N5 Kanji 5 — Position und Grösse (大小上下中右左)** — 🟡 gering  
  _Fundstelle:_ page_number 4, order_index 4, Grammar "Wegfrage 「どこですか」", example_sentences: "あの ドアの 中に あります。 (Ano doa no naka ni arimasu.) — Hinter dieser Tür."  
  _Problem:_ Die deutsche Übersetzung untergräbt das gerade gelehrte Kanji. 中 (なか) bedeutet "in/innen", und der Satz heisst wörtlich "Es ist in/hinter dieser Tür" im Sinne von "hinter der Tür (drinnen)". Übersetzt wird er aber mit "Hinter dieser Tür" — "hinter" entspricht im Japanischen うしろ, nicht 中. In einer Lektion, die 中 = Mitte/innen einführt, verwirrt die Übersetzung die Kanji-Bedeutung.  
  _Korrektur:_ Übersetzung an 中 angleichen, z.B. "Drinnen hinter dieser Tür" bzw. "In dem Raum hinter dieser Tür" — oder ein eindeutigeres Beispiel mit klarer "in"-Bedeutung wählen (z.B. "In diesem Raum").
- **L191 · N5 Kanji 10 — Sprechen, Lesen und Schreiben (話聞読書語名何)** — 🟡 gering  
  _Fundstelle:_ Lektion 191, Seite 3 (Die Kanji — Teil 2), order_index 3, Vokabel "～語" (～ご): example_sentence_japanese "日本語は何語ですか。", example_sentence_english "Nihongo wa nanigo desu ka. — Welche Sprache ist Japanisch?"  
  _Problem:_ Der Beispielsatz ist semantisch zirkulär/sinnlos: 日本語 IST bereits die japanische Sprache, daher beantwortet die Frage 'Japanisch ist welche Sprache?' sich selbst. Ein natürlicher Gebrauch von 何語 (welche/was für eine Sprache) verlangt ein noch unbestimmtes Objekt (z. B. einen Text/eine Schrift), nicht 日本語 selbst.  
  _Korrektur:_ Beispiel durch einen sinnvollen 何語-Satz ersetzen, z. B. 「これは何語ですか。」(Kore wa nanigo desu ka. — In welcher Sprache ist das?) oder 「あの本は何語で書いてありますか。」

---

## Teil B — Natürlichkeit der Beispielsätze (23 Findungen)

Sätze, die ein Muttersprachler als steif/unnatürlich empfindet. Sortiert nach Schwere. Jede Alternative bleibt auf N5-Niveau.

- **L143 · N5 Zahlen — Von 1 bis 10'000** — 🔴 hoch (unnatuerlich)  
  _Satz:_ 「あには二十さい です。」 — vocabulary / page 3, order_index 2 (Vokabel にじゅう, example_sentence_japanese)  
  _Problem:_ Für das Alter '20 Jahre' einer Person sagt man はたち, nicht にじゅっさい. Das ist nicht nur unnatürlich, sondern auch selbstwidersprüchlich: Die Grammatik-Seite 4 derselben Lektion lehrt はたち ausdrücklich als Sonderlesung für 20. Ein Muttersprachler würde 「あには二十さいです」 sofort als Lehrbuch-Fehler hören.  
  _Natürlicher:_ 「あにははたちです。」
- **L164 · N5 Kanji 1 — Zahlen lesen und schreiben (一 bis 十)** — 🔴 hoch (unnatuerlich)  
  _Satz:_ 「あ、すみません、五分後に 来ます。トイレに 行きます。」 — text/dialog_slideshow (Im Restaurant, Tanaka), page_number 5, order_index 2 (auch order_index 3 im Lese-Text)  
  _Problem:_ 「五分後に来ます」 für 'ich bin in fünf Minuten zurück' ist ein Calque aus dem Deutschen/Englischen: 来ます heisst 'kommen/herkommen' — ein Muttersprachler sagt beim Weggehen 戻ります oder 行ってきます, nicht 来ます (man 'kommt' nicht zu sich selbst zurück). Auch 「五分後に」 ('in genau fünf Minuten') und der getrennte Satz 「トイレに行きます」 wirken roboterhaft präzise und gestelzt; für einen kurzen Toilettengang sagt niemand eine exakte Minutenangabe an.  
  _Natürlicher:_ 「あ、すみません、ちょっとトイレに行ってきます。」
- **L171 · N5 Kanji 6 — Familie (父母兄姉弟妹)** — 🔴 hoch (unnatuerlich)  
  _Satz:_ 「あなたのお母さんは やさしいですか。」 — vocab (お母さん), page_number 3, order_index 3  
  _Problem:_ Gleiches Problem wie beim お父さん-Satz: 「あなたの」 + höfliches Verwandtschaftswort ist kein natürliches Japanisch, sondern ein Kalk aus dem Deutschen ('Ihre Mutter'). Muttersprachler nennen den Namen (リサさんの お母さんは…) oder lassen das Pronomen weg.  
  _Natürlicher:_ 「リサさんの お母さんは やさしいですか。 (deckt sich 1:1 mit dem Vorbildsatz der Grammatik-Sektion derselben Lektion); ebenso natürlich und N5: お母さんは やさしいですか。」
- **L178 · N5 Uhrzeit — Wie spät ist es?** — 🔴 hoch (unnatuerlich)  
  _Satz:_ 「いちじ にじゅうごふんからです。じゅうごふんあとです。」 — text / page 5, order_index 2 (Dialog-Slideshow, Lisa, line_04)  
  _Problem:_ 「じゅうごふんあとです」 (15-Minuten-danach) hat falsche Wortstellung. Kein Muttersprachler stellt 「あと」 hinter die Zeitangabe. Natürlich ist 「あと15分です」 (あと vorangestellt) für 'in 15 Minuten'. Die jetzige Form klingt wie wörtlich aus dem Deutschen ('15 Minuten später/danach') übersetzt.  
  _Natürlicher:_ 「いちじ にじゅうごふんからです。あと じゅうごふんです。」
- **L192 · N5 Kanji 11 — Schule und Lernen (学校生先本白)** — 🔴 hoch (unnatuerlich)  
  _Satz:_ 「この学校のせいとは大きいです。」 — vocab (生徒), page_number 2, order_index 8  
  _Problem:_ Kein Muttersprachler beschreibt Schueler mit 大きい — das klaenge, als waeren die Kinder koerperlich gross gewachsen. Es ist eine Wort-fuer-Wort-Konstruktion ('die Schueler sind gross'), die im Japanischen keinen sinnvollen Inhalt traegt. Wenn ueberhaupt, meint man 'es gibt viele Schueler', und das sagt man ganz anders.  
  _Natürlicher:_ 「この学校は生徒が多いです。」
- **L204 · Wetter & Jahreszeiten** — 🔴 hoch (unnatuerlich)  
  _Satz:_ 「秋は寒いです。秋が好きです。」 — vocab (秋/aki), page_number 3, order_index 8  
  _Problem:_ Doppelter Fehler. (1) Falsche Kollokation: Für den Herbst sagt ein Muttersprachler 秋は涼しい (kühl/angenehm), NICHT 秋は寒い — 寒い gehört zum Winter. 秋＝涼しい ist das feststehende Sprachbild (auch die Lektion selbst lehrt 涼しい für den Herbst). (2) Die zwei kurzen Sätze 「秋は…。秋が…。」 mit zweimal 秋 am Satzanfang klingen roboterhaft/lehrbuchhaft aneinandergereiht, so spricht niemand.  
  _Natürlicher:_ 「秋は涼しいです。秋が好きです。 (Vorschlag des Auditors ist bereits gut und strikt N5. Eine flüssigere, aber leicht über reinem N5 liegende Variante wäre 秋は涼しくて好きです — wegen der て-Form des i-Adjektivs hier NICHT bevorzugt.)」
- **L206 · Wohnen — Haus & "es gibt"** — 🔴 hoch (unnatuerlich)  
  _Satz:_ 「ほんだなに本が十あります。」 — vocab (本棚/ほんだな), page_number 3, order_index 7  
  _Problem:_ Bücher werden im Japanischen nicht als nacktes 十 gezählt — sie brauchen zwingend den Zähler 冊 (satsu). 「本が十あります」 ohne Zählwort klingt für einen Muttersprachler wie fehlerhaftes Lerner-/Kinderjapanisch. So sagt das niemand. (Per Web verifiziert: Bücher = 冊, nicht zählerlos.)  
  _Natürlicher:_ 「ほんだなに本が十冊（じっさつ）あります。」
- **L144 · N5 Familie — Wer gehört zu dir?** — 🟠 mittel (unnatuerlich)  
  _Satz:_ 「あなたのお父さんは どこに いますか。」 — vocab (お父さん), page_number 3, order_index 1  
  _Problem:_ あなた wird im natürlichen Japanisch fast nie verwendet, um das Gegenüber direkt anzusprechen — besonders nicht in Verbindung mit Familienmitgliedern. Es ist eine Wort-für-Wort-Übersetzung des deutschen 'Ihr Vater'. Ein Muttersprachler sagt entweder den Namen (z.B. 田中さんの) oder lässt das Pronomen ganz weg, weil der Bezug aus dem Kontext klar ist. Beweis in derselben Lektion: order_index 3 macht es richtig (たなかさんのお兄さんは…), und der Dialog auf Seite 5 sagt 'おとうさんと おかあさんは どこに いますか' OHNE あなた.  
  _Natürlicher:_ 「お父さんは どこに いますか。」
- **L144 · N5 Familie — Wer gehört zu dir?** — 🟠 mittel (unnatuerlich)  
  _Satz:_ 「あなたのお母さんは やさしいですか。」 — vocab (お母さん), page_number 3, order_index 2  
  _Problem:_ Gleiches Muster: あなたの als direkte Anrede klingt wie aus dem Deutschen übersetzt ('Ist Ihre Mutter nett?'). Kein Muttersprachler stellt diese Frage mit あなたの; das Pronomen entfällt oder wird durch einen Namen ersetzt. Die höfliche Form おかあさん signalisiert ohnehin schon, dass es um die Familie des Gegenübers geht — あなたの ist redundant und wirkt steif/lehrbuchhaft.  
  _Natürlicher:_ 「お母さんは やさしいですか。」
- **L162 · N5 Reise & Ort — In der Stadt: Bahnhof, Bank, Park** — 🟠 mittel (unnatuerlich)  
  _Satz:_ 「わたしは銀行へお金を取りに行きます。」 — vocab (銀行), page_number 2, order_index 2  
  _Problem:_ 「お金を取りに行く」 ist eine Wort-für-Wort-Übersetzung von dt. 'Geld holen/abheben'. Für einen Muttersprachler klingt 取りに行く so, als ginge man Geld abholen, das irgendwo für einen bereitliegt (z.B. das man jemandem geliehen hat) — NICHT 'eigenes Geld vom Konto abheben'. Für Abheben sagt man おろす / 引き出す. Eine Vokabelkarte sollte nicht die falsche Kollokation einprägen.  
  _Natürlicher:_ 「銀行でお金をおろします。(おろす = das natürliche Verb für "abheben") — falls strikt N5 verlangt: 銀行へお金を出しに行きます。(出す bleibt N5; mit へ行く als Wegbewegung wie im Original, aber ohne die falsche 取りに行く-Kollokation). Der Auditor-Vorschlag 銀行でお金を出します ist akzeptabel, aber お金を出す ist etwas mehrdeutig (kann auch "bezahlen/herausnehmen" heissen); im Bankkontext mit 銀行で wird es aber hinreichend eindeutig auf "abheben" gelesen.」
- **L170 · N5 Kanji 5 — Position und Grösse (大小上下中右左)** — 🟠 mittel (unnatuerlich)  
  _Satz:_ 「あの 右に あります。」 — text (Grammatik-Prosa 'Wegfrage', Beispielantwort), page_number 4, order_index 1  
  _Problem:_ 「あの 右」 ist grammatisch/idiomatisch schief: 「あの」 ist ein vorangestelltes Demonstrativ und braucht ein Substantiv dahinter (あの しんごうの 右…). Allein stehend sagt das kein Muttersprachler; für 'rechts da drüben' nutzt man 「あちらの ほう」 oder bezieht sich auf einen Landmark. (Die spätere Grammatik-Karte macht es mit 「あの しんごうの 右に あります」 korrekt — die Prosa-Antwort hier ist die unsaubere Variante.)  
  _Natürlicher:_ 「あの しんごうの 右に あります。 — beste Wahl, da sie den Landmark しんごう aus dem unmittelbaren Lektionskontext aufgreift und wortgleich mit der Grammatik-Karte und dem Dialog derselben Lektion ist (Konsistenz). Strikt N5. Alternativ ebenfalls korrekt und N5: 「みぎの ほうに あります。」 oder 「あちらに あります。」」
- **L191 · N5 Kanji 10 — Sprechen, Lesen und Schreiben (話聞読書語名何)** — 🟠 mittel (unnatuerlich)  
  _Satz:_ 「日本語は何語ですか。」 — vocab (～語), page_number 3, order_index 3  
  _Problem:_ Der Satz ist zirkulaer und sinnlos: Japanisch IST eine Sprache, die Frage 'welche Sprache ist Japanisch?' hat keine sinnvolle Antwort ausser 日本語. Niemand wuerde das real fragen — es untergraebt sogar seinen eigenen Lehrzweck (das Suffix ～語 'erfragen').  
  _Natürlicher:_ 「これは何語ですか。 (Welche Sprache ist das? — z.B. auf einen Text gezeigt.) Bleibt N5 und demonstriert ～語 sinnvoll.」
- **L192 · N5 Kanji 11 — Schule und Lernen (学校生先本白)** — 🟠 mittel (steif)  
  _Satz:_ 「ほんだなに本が十あります。」 — vocab (本棚), page_number 3, order_index 8  
  _Problem:_ Buecher zaehlt man im Japanischen mit dem Zaehler 冊 (satsu). Eine blanke Zahl 十 ohne Zaehler direkt am Verあります wirkt hoelzern/unvollstaendig, fast wie eine Auslassung. Ein Muttersprachler sagt automatisch 十冊.  
  _Natürlicher:_ 「ほんだなに本が十冊あります。 (冊 ist ein N5-Zaehler und gehoert hier zwingend dazu.)」
- **L192 · N5 Kanji 11 — Schule und Lernen (学校生先本白)** — 🟠 mittel (unnatuerlich)  
  _Satz:_ 「父は北で生まれました。」 — grammar (～で生まれる), page_number 4, order_index 3  
  _Problem:_ 北 (Norden) ist eine Himmelsrichtung, kein Geburtsort. 'Im Norden geboren' klingt als Wort-fuer-Wort-Uebertragung gekuenstelt; ein Muttersprachler nennt einen konkreten Ort (Stadt/Land) oder formuliert anders. Als Lehrbeispiel fuer で生まれる ist es ein unidiomatischer Fueller.  
  _Natürlicher:_ 「父は日本で生まれました。（chichi wa nihon de umaremashita.）— alternativ ebenso gut: 父は北海道で生まれました。 (konkreter, falls man bei 北 bleiben will).」
- **L192 · N5 Kanji 11 — Schule und Lernen (学校生先本白)** — 🟠 mittel (unnatuerlich)  
  _Satz:_ 「川に木が六本あります。」 — grammar (Zaehler ～本), page_number 4, order_index 4  
  _Problem:_ 川に木があります klingt, als staenden die Baeume IM Wasser. Baeume wachsen am Ufer (川岸/川沿い), nicht 'im Fluss'. Die Szene ist unstimmig, und die deutsche Glosse verraet die Verwirrung sogar (uebersetzt 木 'Baum' faelschlich als 'Baumstaemme'). Ein Muttersprachler waehlt einen klaren Ort.  
  _Natürlicher:_ 「公園に木が六本あります。 (Im Park stehen sechs Bäume.) — Alternativ ebenfalls natürlich und N5: 道に車が三本… nein; bei 木 ist 公園 die klarste Wahl. Falls Flussszene erwünscht: 川の近くに木が六本あります (近く ist N5), aber 公園 bleibt die einfachste, reibungslose Lösung.」
- **L197 · N5 Kleidung & Anziehen — Was ziehst du an?** — 🟠 mittel (unnatuerlich)  
  _Satz:_ 「せびろを きて、かいしゃへ いきます。」 — vocab (背広/せびろ), page_number 2, order_index 11  
  _Problem:_ Grammatik und das Verb 着る sind korrekt, aber 背広 (sebiro) ist veraltetes Showa-Zeit-Vokabular. Moderne Muttersprachler — und erst recht die junge Lernzielgruppe — sagen heute fast ausschliesslich スーツ. Viele junge Japaner kennen 背広 kaum noch oder benutzen es nie. Der Satz klingt dadurch altmodisch, wie aus einem alten Salaryman-Kontext.  
  _Natürlicher:_ 「スーツを きて、かいしゃへ いきます。」
- **L157 · N5 Alltag & Essen 2 — Was möchtest du essen?** — 🟡 gering (unnatuerlich)  
  _Satz:_ 「いいですね。わたしは つめたい ぎゅうにゅうと カレーが たべたいです。」 — dialog_slideshow / Dialog-Text (Im Cafe bestellen), page_number 5, order_index 2 und 3 (Tanakas Zeile 3)  
  _Problem:_ つめたい ぎゅうにゅうと カレーが たべたいです koppelt Milch und Curry an EIN たべたい (essen). Milch trinkt man (飲む), man isst sie nicht — durch das gemeinsame 食べたい wird die kalte Milch mit ins Essen gezogen, was schief klingt. Ein Muttersprachler wuerde Getraenk und Speise trennen oder fuer die Milch のみたい sagen.  
  _Natürlicher:_ 「いいですね。わたしは つめたい ぎゅうにゅうが のみたいです。カレーも たべたいです。」
- **L159 · N5 Begrüssung & Höflichkeit 4 — Entschuldigen und Geschenke übergeben** — 🟡 gering (steif)  
  _Satz:_ 「まいにち やすく かいます。」 — grammar (Adverb-Form い→く), page_number 4, order_index 2 — aus dem Feld example_sentences des Grammatik-Items (3. Beispielsatz)  
  _Problem:_ Inhaltsleerer Lehrbuch-Satz, der nur die Adverb-Form 「やすく」 vorführt, ohne etwas Reales zu kommunizieren. Was kauft man bitte 'jeden Tag günstig'? Ein Muttersprachler merkt sofort, dass der Satz konstruiert ist — gerade weil die beiden anderen Beispiele desselben Items (おそく なりました / はやく きて ください) echte Aussagen sind, die jemand wirklich sagen würde. 安く買う als Kollokation ist korrekt, aber die まいにち-Rahmung macht ihn künstlich.  
  _Natürlicher:_ 「この本を やすく かいました。 (Kono hon o yasuku kaimashita.) — passt; alternativ noch konkreter/idiomatischer: このシャツを やすく かいました。 — beide bleiben strikt N5.」
- **L160 · N5 Erste Sätze 3 — Vergangenheit, Existenz und höfliche Bitten** — 🟡 gering (unnatuerlich)  
  _Satz:_ 「きのうは でませんでした。」 — grammar (Vier Tempus-Formen), page_number 4, order_index 2 (im Feld example_sentences)  
  _Problem:_ 出る allein für 'gestern bin ich nicht ausgegangen / war nicht draussen' ist eine unidiomatische Kollokation. 出る heisst 'hinausgehen/austreten' (aus einem Raum/Ort) — für 'ausgehen / das Haus für den Tag verlassen' benutzt ein Muttersprachler 出かける. So wie es steht (きのうは でませんでした) klingt es unvollständig/seltsam, weil das Ziel oder der Ort fehlt und でる nicht den gemeinten Alltagssinn trägt.  
  _Natürlicher:_ 「Da 出かける zwar N5 ist, aber in dieser Lektion nicht eingeführt wurde, ist sauberer ein Beispiel, das das gelernte でる korrekt mit Bezugspunkt zeigt ODER ein anderes Lektionsverb nutzt: 「きのうは いえに いました。」 (Gestern war ich zu Hause — verwendet います aus derselben Lektion) oder, wenn でる erhalten bleiben soll, mit Ort: 「きのうは いえを でませんでした。」 (Gestern habe ich das Haus nicht verlassen — idiomatisch korrekt, でる + を + いえ, alles N5 und alles in der Lektion vorhanden). Letzteres ist die beste Lösung, weil es den Tempus-Punkt ませんでした demonstriert UND das Lektionsvokabular でる korrekt einbettet, ohne neues Vokabel (でかける) einzuführen.」
- **L165 · N5 Hobbys & Freizeit — Was machst du gerne?** — 🟡 gering (steif)  
  _Satz:_ 「とても いいおんがくが すきです。」 — text (Grammatik 'Vier Muster für Hobby-Gespräche', Antwortbeispiel zu どんな), page_number 4, order_index 1  
  _Problem:_ Als reale Antwort auf 'Was für Musik magst du?' ist 'Ich mag sehr gute Musik' inhaltlich leer und klingt künstlich — niemand antwortet so auf eine Genre-Frage. Es ist ein konstruierter Lehrbuchsatz, der nur existiert, um とても + いい zu zeigen, aber als echte Gesprächsäusserung hölzern wirkt. (Der Text rahmt es zwar als 'breite Antwort', der Satz selbst bleibt aber unidiomatisch.)  
  _Natürlicher:_ 「しずかな おんがくが すきです。 (alternativ ebenso gut und passender als 'breite' Antwort: いろいろな おんがくが すきです。 oder あかるい おんがくが すきです。) — alle strikt N5.」
- **L176 · N5 Begrüssung 2 — Alltagsgrüsse rund um den Tag** — 🟡 gering (steif)  
  _Satz:_ 「おかえり、ごはんを食べますか。」 — vocab (おかえり), page_number 3, order_index 5  
  _Problem:_ Register-Bruch: Das beilaeufige, familieninterne おかえり steht direkt neben der hoeflich-distanzierten Lehrbuchform 〜を食べますか (mit explizitem を-Partikel). Eine Mutter/ein Familienmitglied, das おかえり sagt, wuerde nie im selben Atemzug so foermlich 食べますか fragen — das klingt wie zwei zusammengeklebte Lehrbuchbausteine, nicht wie eine echte Aeusserung an der Tuer.  
  _Natürlicher:_ 「おかえり。ごはん食べる?」
- **L197 · N5 Kleidung & Anziehen — Was ziehst du an?** — 🟡 gering (steif)  
  _Satz:_ 「ちちは ワイシャツを きます。」 — vocab (ワイシャツ/waishatsu), page_number 2, order_index 7  
  _Problem:_ Die deutsche Übersetzung ('Mein Vater trägt ein Business-Hemd') meint eine Beschreibung/Gewohnheit, aber das schlichte 着ます (Nicht-Vergangenheit) liest sich als zukünftige/einmalige Handlung ('wird anziehen'). Zur Beschreibung dessen, was jemand gewöhnlich/gerade trägt, verwenden Muttersprachler 着ています — was die Lektion auf Seite 4 selbst lehrt. So wie es steht, wirkt der Satz lehrbuchhaft-mechanisch zur gemeinten Bedeutung.  
  _Natürlicher:_ 「ちちは ワイシャツを きています。 (Chichi wa waishatsu wo kite imasu.) — ています-Form für 'trägt (gerade/gewohnheitsmässig)', identisch zur in der Lektion gelehrten Verlaufsform.」
- **L207 · Schule & Lernen — Im Unterricht** — 🟡 gering (unnatuerlich)  
  _Satz:_ 「わたしの クラスは大きいです。」 — vocab (クラス), page_number 2, order_index 3  
  _Problem:_ クラスが大きい klingt nach einer Wort-für-Wort-Übersetzung aus dem Deutschen ('Klasse ist gross'). Eine Schulklasse beschreibt ein Muttersprachler nicht mit 大きい, sondern über die Personenzahl. 大きいクラス hört man höchstens für einen grossen Raum/eine Abteilung, aber 'meine Klasse ist gross' im Sinne von 'wir sind viele' sagt man so nicht.  
  _Natürlicher:_ 「わたしの クラスは ひとが おおいです。 (Die Auditor-Alternative ist bereits ideal — natürliches XはYが-Muster, 人 und 多い beide N5, idiomatisch.)」

---

## Anhang — Abdeckung

- **42 von 58 Lektionen** haben mindestens eine Findung.
- **16 Lektionen ohne jede Findung** (sauber): L149, L152, L161, L163, L173, L193, L194, L195, L196, L199, L200, L202, L208, L209, L210, L211.
