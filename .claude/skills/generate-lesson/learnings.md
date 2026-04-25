# Learnings — generate-lesson

Selbstverbesserndes Log. Wird vor jedem Run gelesen, nach jedem Run angehängt.

## Format

```markdown
## YYYY-MM-DD HH:MM — [JLPT-Level] Thema (Lesson ID X)

### Erfolge
- ...

### Probleme / Erkenntnisse
- Beobachtung → **Regel für nächstes Mal: ...**

### Aktuelle Regeln (kumulativ, wichtigste zuerst)
1. ...
2. ...
```

**Regel-Hochstufung:** Wenn derselbe Fehler 2× in unterschiedlichen Runs auftritt, **in SKILL.md §3 oder §5 hochheben**, nicht nur hier stehen lassen.

---

## Initial-Regeln (vor erstem Run, aus improve-jpl + CLAUDE.md abgeleitet)

1. **Anfänger-First (Claudio dogfoodet):** Vor jeder Design-Entscheidung: "Würde Claudio bzw. ein deutschsprachiger Anfänger das bemerken, verstehen, wiederkommen?" Wenn nein → zurückstellen.
1b. **Mayuko-Fachreview:** Mayuko (Japanisch-Lehrerin, Native Speaker, NICHT Lernerin) prüft fachliche Korrektheit. Bei JP-Inhalt: "Würde sie das freigeben?" Bei Zweifel zeigen, bevor live.
1c. **JLPT-Leitprinzip (Mayuko-Direktive 2026-04-25, präzisiert mit harten Regeln):**
   - **N5 zuerst komplett, bevor N4** — keine N4-Lektionen, solange N5 < 100% Coverage.
   - **Offizielle JLPT-Wortlisten als Quelle**, nicht Minna no Nihongo. MNN ergänzend OK, JLPT entscheidet über Scope.
   - **STRENG: kein Niveau-Mix.** N5-Lektion enthält null N4+-Wörter. Validator MUSS bei Cross-Level-Wort mit ERROR abbrechen, nicht warnen. Keine „Bonus"-Vokabeln, kein „nur dieses Mal".
   - Siehe [improve-jpl §1.5](../improve-jpl/SKILL.md) und Memory `project_jlpt_leitprinzip.md`.
2. **Anfänger-Only:** N5 und N4. N3+ ist aktuell aus-scope.
3. **Keine `fill_in_the_blank` Quiz-Typen.** Niemals. Auch nicht "nur diesmal".
4. **Instruction-Language default `german`.** Sprache der primären Zielgruppe.
5. **Beispielsätze dürfen KEINE Kanji/Vokabeln über dem Lektions-Level nutzen.** Wenn unvermeidbar: Hiragana schreiben.
6. **Umlaute echt, nicht ASCII-Fallback.** Schüler, nicht Schueler.
7. **Duplicate-Check vor Kana/Kanji/Vocabulary/Grammar-Insert.** Bestehende ID wiederverwenden.
8. **Atomare Transaktion:** Ganze Lektion oder nichts. Kein halbes Insert.
9. **Verifikation via Playwright ist Pflicht** bevor Git-Commit oder is_published=True.
10. **Mix der Quiz-Typen pro Page:** Nicht 10× multiple_choice. Immer mind. 2 Typen mischen (mc/tf/matching).

---

## Run-Log

<!-- Neuste Einträge oben, älteste unten. -->

## 2026-04-25 22:35 — Katakana 1-5 — komplette Katakana-Serie (Lesson IDs 151-155)

### Erfolge — Schreibsystem komplett

- **Fünf Katakana-Lektionen** in einem Schwung erstellt: K1 (Vokale+K+S, 15 Zeichen), K2 (T+N+H, 15), K3 (M/Y/R/W+ン, 16), K4 (Diakritika 25 + Längungsstrich), K5 (Yōon 12 + Lehnwort-Spezialitäten 13).
- **96 Katakana-Einträge** in der DB (deutlich weniger als die 104 Hiragana, weil Yōon/Spezialitäten kompakter behandelt wurden — eigene Lektion K5 deckt nur K/S/J/CH-Yōon plus die wichtigsten Lehnwort-Sondersilben ab).
- **Modul `n5-katakana` (id=31)** komplett: 5 Lektionen, order_index 1-5, alle published.
- **Pipeline lief in einem Rutsch durch:** Validator akzeptierte alle 5 Drafts beim ersten Mal (nur thumbnail_url-Fehler vor `images`-Schritt — erwartet). Keine Korrekturschleifen.
- **Lehnwort-Spezialitäten als didaktisches Highlight:** K5 deckt 「ティ」, 「ディ」, 「ファ」, 「フィ」, 「フェ」, 「フォ」, 「ウィ」, 「ウェ」, 「ウォ」, 「ヴァ」, 「ヴィ」, 「ヴェ」, 「ヴォ」 ab — Klänge, die nur in Katakana existieren. Diese sind in Hiragana nicht gelernt worden.

### Probleme / Erkenntnisse

1. **Vorlagen-Pattern skaliert linear:** Hiragana-Vorlagen direkt für Katakana wiederverwendbar — gleiche 5-Page-Struktur, gleicher Quiz-Mix, gleiche Validator-Regeln. Pro Lektion ca. 3-4 Minuten Generierungszeit (validate + images + insert + text-audio + Modul-Update + Verify).
2. **Bestandsschutz greift auch bei Yōon:** UNIQUE-Constraint auf `Kana.character` matcht auch zweistellige Strings wie 「キャ」 korrekt — keine Kollisionen mit den gleichlautenden Hiragana-Yōon (verschiedene Unicode-Codepoints).
3. **Längungsstrich 「ー」 als didaktischer Mehrwert:** K4 hebt diese Katakana-spezifische Eigenheit explizit hervor. Kein eigenes Kana-Item (es ist ein Modifier, kein Buchstabe), aber zentral für jedes Lehnwort-Lesen.
4. **Schreibsystem-Modul-Pattern stabil:** Hiragana (Modul 30, 5 Lektionen) und Katakana (Modul 31, 5 Lektionen) haben jetzt dieselbe Struktur — als Vorlage für jedes weitere Schreibsystem (theoretisch könnte man dasselbe für Kanji-Reihen machen, ist aber didaktisch anders zu strukturieren).
5. **Kosten:** 5 DALL-E-Thumbnails (~25 Rappen) + ~35 TTS-MP3s (~5 Rappen) = ~30 Rappen für die ganze Serie. Bei 5 Schreibsystem-Lektionen sehr günstig.

### Aktuelle Regeln (Ergänzung ab diesem Run)

37. **Katakana-Lektionsschablone ist identisch zu Hiragana** — gleiche Page-Struktur, Quiz-Mix, Modul-Pattern. Folge-Schreibsystem-Lektionen (theoretisch z.B. Kanji-Klassiker) können direkt nach diesem Muster generiert werden.
38. **K5 (Yōon) deckt nur die häufigsten Yōon ab** (K, S, J, CH = 12 Zeichen) plus die 13 Lehnwort-Spezialitäten (ティ/ディ/ファ etc.). Im Gegensatz zu H5 (33 Yōon) ist das pragmatisch — Katakana-Yōon kommen seltener vor als Hiragana-Yōon, weil Lehnwörter andere Klänge bevorzugen.

---

## 2026-04-25 22:15 — Hiragana 3, 4 und 5 — komplette Hiragana-Serie (Lesson IDs 148, 149, 150)

### Erfolge — Hiragana ist komplett

- **Drei Lektionen in Folge** generiert: Hiragana 3 (M/Y/R/W + ん, 16 Zeichen), Hiragana 4 (Diakritika が/ざ/だ/ば/ぱ, 25 Zeichen), Hiragana 5 (Yōon, 33 Zeichen). Damit sind alle 5 Hiragana-Lektionen (146-150) im Modul `n5-hiragana` (order_index 1-5).
- **Pipeline-Vorlage skaliert sauber:** Jede Lektion folgte derselben 5-Page-Struktur (Einführung / Zeichen / Aussprache / Übung / Zusammenfassung). Quiz-Mix konstant 7-8 MC + 3-4 TF + 2 Matching.
- **Bestandsschutz funktioniert auch bei Yōon:** UNIQUE-Constraint auf `Kana.character` matchte alle 33 Yōon (zweistellige Strings wie 「きゃ」, 「ぎゅ」) korrekt — keine Kollisionen.
- **Validator-Limit angehoben:** kana-Count-Limit von 20 auf 35 erhöht (`pipeline.py` §3 Validator), damit Diakritika- (25) und Yōon-Lektionen (33) durchgehen. Kana-Lektion ist die einzige Sonderform mit grösseren Kana-Mengen.
- **Playwright-Verifikation aller drei Lektionen:** 0 Console-Errors, jeweils 5 Pages, alle Audios geladen, keine broken Images. Yōon-Deck zeigt korrekt 33 flip cards auf Page 1.

### Probleme / Erkenntnisse

1. **Kana-Limit war zu niedrig für Diakritika/Yōon-Lektionen.** §3 Validator hatte `5 <= kana_count <= 20`. 25 Diakritika und 33 Yōon brachen ab. Limit auf `35` erhöht — Begründung: Diakritika und Yōon sind die einzigen Lektionstypen, die so viele Kana haben, und sie sind didaktisch begründet (komplette Reihen statt willkürliche Auswahl).
2. **Quiz-Intro-Text muss Romaji haben — gilt auch bei Erklärungen über kleine Zeichen.** Lesson 150 brach beim Insert ab, weil der Quiz-Intro die ya/ゆ/yo-Vergleichslogik ohne Romaji-Klammern beschrieb. Fix: `「や」 (ya) / 「ゆ」 (yu) / ...` Pattern auch in Vergleichs-Tabellen anwenden, nicht nur bei einzelnen Wörtern.
3. **Yōon brauchen längere text-audio-Generierung:** ~3 Minuten für 8 MP3s mit insgesamt mehr Segmenten als typische Lektion (Erklärungen über kleine Zeichen sind länger). Innerhalb 240s-Timeout aber problemlos.
4. **Vorlagen-Pattern stabil über 5 Hiragana-Lektionen:** Selbe Page-Struktur, selber Quiz-Mix, selbes Modul. Pro Lektion ca. 5-10 Minuten Generierungszeit (validate + images + insert + text-audio + Verify) — schnell genug für Batch-Generierung.

### Aktuelle Regeln (Ergänzung ab diesem Run)

35. **Kana-Count-Limit ist 35** (nicht mehr 20) — Diakritika- und Yōon-Lektionen brauchen vollständige Reihen.
36. **Quiz-Intro-Text mit JP-Vergleichen muss Romaji-Annotationen enthalten**, auch bei Erklärungen über kleine ゃ/ゅ/ょ vs. grosse や/ゆ/よ. Validator fängt das, aber besser direkt sauber schreiben.

---

## 2026-04-25 21:55 — Hiragana 2 — T-Reihe, N-Reihe und H-Reihe (Lesson ID 147)

### Erfolge — zweite Schreibsystem-Lektion, Pipeline ohne Korrekturschleifen

- **5 Pages** (Einführung / Die 15 neuen Zeichen / Aussprache & Schreibhinweise / Übung / Zusammenfassung), **15 neue Hiragana** (T-Reihe + N-Reihe + H-Reihe = たちつてと + なにぬねの + はひふへほ), **12 Quiz-Fragen** (7 MC + 3 TF + 2 Matching) — alle 3 erlaubten Typen, jeder ≥2×.
- **Bestandsschutz griff sofort:** UNIQUE-Constraint auf `Kana.character` deduppte bei den 15 neuen Zeichen — keine bestehende ID wurde überschrieben.
- **Pipeline lief in einem Rutsch durch:** validate → images (1 Thumb, 0 Vokabel-Icons) → insert (atomar, Lesson 147) → text-audio (7 MP3s für alle Prosa-Pages). Keine Korrekturschleife nötig — die §2b-Regeln und §3-Constraints sind nach Lesson 146 stabil.
- **Modul-Zuweisung:** `category_id=30` (`n5-hiragana`), `order_index=2` (direkt hinter Hiragana 1), `is_published=true`.
- **Playwright-Verifikation:** 0 Console-Errors, 5 Pages in Sidebar, 7 Audio-Player (für alle 7 Prosa-text-Blöcke), `[Deck] Found 5 carousel pages` + `Page 1: 15 flip cards`. Page 2 zeigt das Deck-Karussell korrekt (eine Karte sichtbar, Counter "0/15 gelernt, 15 verbleibend"). Page 4 Quiz-Intro mit Markdown-Hierarchie + Login-Gate (Guest erwartet).
- **Drei didaktische Audio-Player auf Page 2** — jede Reihe (T/N/H) hat ihren eigenen text-Block mit eigenem MP3, was die Aussprache-Erklärung pro Reihe direkt anhörbar macht. User-Aufwand pro Reihe: ein Klick.

### Probleme / Erkenntnisse

1. **Kana-Pipeline ist nach Lesson 146 produktionsreif.** Lesson 147 lief ohne einzige manuelle Korrektur durch — Validator akzeptierte den Draft beim ersten Mal (nur thumbnail_url-Fehler vor `images`-Schritt, das ist erwartetes Verhalten). Beweist die §2b-Vergleichstabelle als belastbare Spezifikation.
2. **Zwei Pages als didaktischer Multi-Audio-Block** funktioniert sauber — drei text-Blöcke auf Page 2 (T-Reihe / N-Reihe / H-Reihe) bekommen drei separate text-audio-MP3s, jeder Block ist einzeln anhörbar. Das skaliert für Hiragana 3 (M/Y/R/W + ん) genauso, oder sogar für Katakana-Lektionen mit 5 Reihen pro Lektion.
3. **Wiederverwendbares Pattern:** Hiragana-Lektionen folgen einem strikten Schablonen-Format (1 Einführungs-Page + 1 Zeichen-Page mit verschachtelten text+kana-Blöcken + 1 Schreib/Aussprache-Page + 1 Quiz + 1 Zusammenfassung). Hiragana 3 kann praktisch durch Variabel-Substitution (Reihen-Namen + Ausnahmen + neue Beispielwörter) aus dem 147-Draft generiert werden — minimaler kognitiver Aufwand pro Folge-Lektion.
4. **Kosten pro Kana-Lektion:** 1 DALL-E-Thumbnail (~5 Rappen) + 7 TTS-MP3s (~1 Rappen) = ~6 Rappen total. Vocabulary-Lektion zum Vergleich: ~50 Rappen (Slideshow + Vocab-Icons). Kana-Lektionen sind die billigsten in der Pipeline.
5. **Quiz-Mix bestätigt sich als robust** — die 12 Fragen (7 MC + 3 TF + 2 Matching) decken Lesen einzelner Zeichen, Erkennen von Ausnahmen, und Lesen kompletter Wörter ab. Selbe Verteilung wie Lesson 146 → Vorlage etabliert.

### Aktuelle Regeln (Ergänzung ab diesem Run)

33. **Schreibsystem-Lektionen mit didaktischer Reihen-Aufteilung sollten pro Reihe einen eigenen text-Block haben** (Mini-Erklärung + Mini-Übung). Vorteile: pro-Reihe-Audio via text-audio, kürzere Einzelblöcke (besser scannbar), klare visuelle Trennung. Pattern: text(Reihe1-Erklärung) → kana×5 (Reihe1) → text(Reihe2) → kana×5 (Reihe2) → text(Reihe3) → kana×5 (Reihe3).
34. **Die Hiragana-Lektionsschablone ist stabil** — gleiche Page-Struktur, gleicher Quiz-Mix, gleiches Modul (n5-hiragana). Folge-Lektionen Hiragana 3 (M/Y/R/W + ん), Diakritika und Yōon können direkt nach diesem Muster generiert werden.

---

## 2026-04-25 21:40 — Hiragana 1 — Vokale, K-Reihe und S-Reihe (Lesson ID 146)

### Erfolge — erste Schreibsystem-Lektion

- **Skill-Erweiterung `kind="kana"`** in einem Run umgesetzt: Validator + Insert + Image-Skip getrennt vom Vocabulary-Pfad. SKILL.md §2b dokumentiert die Sonderform mit Vergleichstabelle und Page-Struktur-Zielbild.
- **5 Pages** (Einführung / Die 15 Zeichen / Aussprache & Schreibhinweise / Übung / Zusammenfassung), **15 Hiragana** (Vokale + K-Reihe + S-Reihe), **12 Quiz-Fragen** (8 MC + 2 TF + 2 Matching) — alle 3 erlaubten Typen.
- **Bestandsschutz:** die initialen 10 Hiragana あいうえおかきくけこ (DB-IDs 1-10) wurden via UNIQUE-Constraint dedupliziert; nur die 5 neuen Zeichen さしすせそ (IDs 11-15) wurden eingefügt.
- **Pipeline-Schritte:** validate → images (1 Thumb, 0 Vocab-Icons übersprungen) → insert (Lesson 146 atomar) → text-audio (7 MP3s für alle Prosa-Pages, DE+JA-Splitter sauber) → audio/slideshow übersprungen (kein Dialog).
- **Modul-Zuweisung:** `category_id=30` (`n5-hiragana`), `order_index=1`, `is_published=true`.
- **Playwright-Verifikation:** 5 Pages in Sidebar, 7 Audio-Player, 0 broken Images, 0 Console-Errors. Page 2 zeigt das Deck-Karussell korrekt (eine Karte sichtbar, Counter "0/15 gelernt"). Page 4 Quiz-Intro mit Markdown-Hierarchie + Login-Gate für Guests (erwartet).

### Probleme / Erkenntnisse

1. **Validator akzeptiert `kind=kana` und überspringt Vocabulary/Grammar/N5-Canonical-Checks korrekt.** Einziger initialer Fehler war die Thumbnail-Pflicht (wird durch images-Schritt erfüllt) — passt 1:1 zum Vocabulary-Workflow. Keine Sonderbehandlung für den User nötig.
2. **Kana-Lektion läuft komplett ohne Slideshow/Audio-Konversation** — die generischen Pipeline-Steps für Dialog gibt es bei kind=kana schlicht nicht. 5 Pipeline-Schritte (validate, images, insert, text-audio, modul-zuweisung) statt 8 — schneller und billiger pro Lektion.
3. **Bilder-Aufwand minimal:** nur 1 Thumbnail-DALL-E-Call pro kana-Lektion (statt 1 Thumb + N Vokabel-Icons). Spart ca. 90 % der OpenAI-Kosten gegenüber Vocabulary-Lektion.
4. **Initiale 10 Hiragana waren bereits in der DB** — `_get_or_create_kana()` Duplicate-Check via `character`-UNIQUE funktionierte fehlerfrei; bestehende IDs wurden wiederverwendet, kein Override.
5. **Markdown-Hierarchie-Validator triggerte bei keinem text-Block** — die Pflicht (## H2 + 2× **bold** + Liste/Quote) wurde in allen 7 Prosa-Texten von Anfang an erfüllt. Kein Korrektur-Loop nötig.
6. **Kein N5-Kanji-Disziplin-Check nötig** — eine Hiragana-Lektion enthält per Definition keine Kanji-Beispielsätze. Validator-Skip via `kind != "kana"` ist sauber.

### Aktuelle Regeln (Ergänzung ab diesem Run)

30. **Kana-Lektion = Sonderform mit `kind: "kana"` im Draft.** Validator-Pfad, Page-Struktur und Pipeline-Steps sind in SKILL.md §2b vollständig spezifiziert. Vocabulary/Grammar = 0, Kana = 5-20, Quiz = 8-16, Pages ≥ 4. Audio/Slideshow überspringen.
31. **Kana-Lektionen brauchen eigene Modul-Slugs:** `n5-hiragana` (id=30) und `n5-katakana` (id=31). Zuweisung via UPDATE wie bei Vocabulary-Lektionen.
32. **Bestandsschutz bei Kana ist UNIQUE-Constraint-getrieben** — `_get_or_create_kana()` matcht nur über `character`, modifiziert nichts an bestehenden Eintraegen. Sicher gegen versehentliches Überschreiben manueller Edits.

---

## 2026-04-25 20:30 — N5 Tagesablauf — Wann stehst du auf? (Lesson ID 145)

### Erfolge
- 20 N5-Vokabeln aus dem Tagesablauf-Cluster (おきる/ねる/たべる/のむ/はたらく/
  やすむ/べんきょう/はじまる/おわる/かえる + Tagesabschnitte 朝/昼/夜/今/午前/
  午後/半/毎日/今日/明日). Alle in `vocab`-Key der canonical N5-Liste.
- 3 Grammatikkarten: Uhrzeit (今 ～時 ～分 です), ます-Form (mit allen 4 Tempora),
  ～から ～まで. Volle Romaji-Annotation.
- 15 Quiz-Fragen total: 4 Verständnisfragen auf der Dialog-Page (3 MC + 1 TF) +
  11 Übungsfragen (7 MC + 2 TF + 2 Matching).
- 7 Pages mit Markdown-Hierarchie (## H2 + ### H3 + Bold + Listen + Blockquote)
  in allen 3 Prosa-Seiten (Einführung, Grammatik-Erklärung, Zusammenfassung).
- Pipeline lief vollständig: validate → images (1 Thumb + 19/20 Vocab-Icons) →
  insert (Lesson 145) → audio (1 MP3, 8 Sprecher-Zeilen, ~30s) → text-audio
  (5 MP3s für Prosa-Pages) → slideshow (8 PNGs + 8 MP3s, ~5 min).
- Modul-Zuweisung: `n5-zahlen-zeit` (category_id=32, order_index=8, published).
- Playwright-Verifikation: Page 1 Markdown-Hierarchie sauber, Page 2 Deck-
  Karussell zeigt eine Karte, Page 5 Audio + Slideshow + Dialog + Quiz in
  korrekter didaktischer Reihenfolge, Page 6 alle 11 Quiz-Fragen renderten.

### Probleme / Erkenntnisse

1. **Slideshow-Skript pickte falschen text-LC** — `gen_dialog_slideshow.py`
   nutzte `.first()` ohne `order_by` und ohne Speaker-Format-Check. Auf der
   Dialog-Page liegen seit dem 2026-04-25 Verständnisfragen-Update ZWEI text-
   LCs (Dialog selbst + Verständnis-Intro). DB-Reihenfolge ist nicht garantiert
   → Slideshow griff oft den Verständnis-Intro-Text und brach mit "Keine
   Dialog-Zeilen extrahiert" ab.
   - **Fix:** im Skript ALLE text-LCs holen (sortiert nach order_index, id),
     den ersten mit gültigem Speaker-Format (`Name: ...`) auswählen.
   - **Regel:** Wenn auf einer Page mehrere LCs gleichen content_types liegen
     können, NIE `.first()` ohne explizites `order_by` UND ohne semantischen
     Filter (hier: parse_dialog_triplets() muss > 0 Triplets liefern).

2. **Order-Index-Kollision bei nachträglichen audio/slideshow-Inserts** —
   `pipeline.py insert` nummeriert alle Items der Dialog-Page ab `order_index=1`
   (Dialog-Text + Verständnis-Intro). Dann setzt `audio` einen LC auf
   `order_index=1` und `slideshow` einen auf `order_index=2`, ohne die
   bestehenden zu verschieben. Resultat: 4 LCs mit oi-Werten 1/1/1/2 → DB
   sortiert nicht-deterministisch → Frontend rendert in falscher Reihenfolge
   (Verständnisfragen vor Dialog-Text).
   - **Workaround diesmal:** manuell per SQL `UPDATE lesson_content SET
     order_index=N WHERE id=X` korrigiert (audio=1, slideshow=2, dialog-text=3,
     verstaendnisfragen=4).
   - **Regel für nächstes Mal:** Nach `audio` + `slideshow` immer `SELECT id,
     content_type, order_index FROM lesson_content WHERE lesson_id=X AND
     page_number=5 ORDER BY order_index, id;` ausführen und Kollisionen
     manuell fixen — oder Skill so umbauen, dass `audio`/`slideshow` die
     bestehenden LCs verschieben statt zu ueberschreiben.

3. **OpenAI DALL-E lehnt "to eat" als Safety-Violation (self-harm) ab** —
   das Vocab-Prompt-Template enthielt vermutlich Worte, die der DALL-E-Filter
   als selbstverletzendes Verhalten missdeutete. 19/20 Bilder OK, nur 食べる
   blockiert.
   - **Workaround:** manuell mit explizitem, harmlosem Prompt erzeugt
     ("a bowl of warm rice with chopsticks held above it, no people").
   - **Regel:** DALL-E-Safety-Reject auf Vocab-Bilder ist gelegentlich
     unvermeidbar. Pipeline weitermachen lassen, am Ende geblockte Vokabeln
     mit Fallback-Prompt nachgenerieren. Lektion ist mit fehlendem Bild
     (1 von 20) noch fully usable.

4. **Anzahl der Quiz-Fragen:** 11 Übungs-Fragen lagen knapp unter dem
   Skill-Budget von 10-18 — passte aber. Mit den 4 Verständnisfragen kommt
   die Lektion auf 15 total, was komfortabel im Korridor liegt.

5. **N5-Verben mit N4-Kanji-Falle (Wiederholung von Lesson 144):** 起 (起きる),
   寝 (寝る), 仕 (仕事), 帰 (帰る), 事 (仕事), 遊 (遊ぶ) sind alle KEINE N5-
   Kanji — Validator fing 5 Fälle in meinen content_text-Blöcken.
   Hiragana-Lösung wie gewohnt: おきる, ねる, しごと, かえる, あそぶ.
   - **Bestaetigung Regel 20** (Familie-Kanji-Falle gilt analog für ALLE
     Themen, nicht nur Familie). SKILL.md §3 wurde fuer Familie geschrieben,
     gilt aber Tagesablauf, Hobbys, Restaurant — überall wo N5-Vokabeln
     N4-Kanji haben.

### Aktuelle Regeln (Ergänzung ab diesem Run)

26. **Slideshow-Skript: `.first()` durch `order_by + semantic filter` ersetzen.**
    Wenn mehrere LCs gleichen Typs auf einer Page liegen koennen, immer den
    semantisch richtigen finden (hier: Speaker-Format-Check).
27. **Nach `audio`/`slideshow` order_index-Kollision pruefen** und ggf.
    Dialog-Text/Verstaendnis-Intro per SQL nachsortieren, sonst rendert
    Page 5 in zufaelliger Reihenfolge. Reihenfolge-Standard: audio=1,
    slideshow=2, dialog-text=3, verstaendnisfragen=4.
28. **DALL-E Safety-Reject ist normal** — bei einzelnen Vokabeln (oft Verben)
    schlagen Generierungen fehl. Pipeline weiterlaufen lassen, am Schluss
    nur die geblockten Vokabeln manuell nachgenerieren mit harmlosem,
    objekt-fokussiertem Prompt (statt verb-fokussiert).
29. **N4-Kanji-Falle gilt ueber alle Themen** (Familie, Tagesablauf, Hobbys, …)
    — N5-Vokabeln mit N4-Kanji im Beispielsatz immer in Hiragana schreiben.
    SKILL.md §3 ist generell, nicht thema-spezifisch.

---

## 2026-04-25 20:15 — text-audio Bugs (Lesson 144 nach Live-Check)

### User-Feedback wörtlich
> "die formatierung ist abgefucked alles center ausserdem ist immer noch
> die japanische stimme die deutsch spricht!! das toent ultra rassistisch!!"

### Bug A — Center-Alignment im Markdown-Block
- **Ursache:** CSS-Selector `.content-item:has([src*="uploads"])` (custom.css
  Z.2303) sollte ursprünglich Bild-Content erkennen, mached aber auch
  `<audio src="/static/uploads/…">`. Der ganze Block wurde zentriert.
- **Fix:** Selector verschärft auf `:has(img[src*="uploads"])` + expliziter
  text-align:left override fuer `.text-audio-player` und seine Container.
- **Regel für nächstes Mal:** `:has([src*=...])` ohne Tag-Qualifier sind
  fragil — sobald ein neues Element-Typ mit `src=` auftaucht (audio, video,
  iframe, source), greift die Regel mit. **`:has()`-Selektoren immer mit
  Tag-Name qualifizieren** (`:has(img[src...])`, nicht `:has([src...])`).

### Bug B — Ja-Voice spricht Deutsch ("rassistischer Akzent")
- **Ursache:** Bestehendes `MultilingualTextAudioSystem` (lesson_view.html
  Z.2134) macht jeden `<p>` in `.rich-text-content` klickbar und ruft
  `/api/tts` auf — der Endpoint nutzt fest ja-JP-Voice. Mein neuer
  text-audio-Player war zwar korrekt (DE+JA-Splitter), aber der parallel
  laufende Klick-Handler überschrieb beim Klicken auf den Text die
  Wiedergabe mit ja-Voice für DE.
- **Fix:** `processAllContent` skipt `.rich-text-content`/`.text-content-container`
  Elemente, deren Container bereits `.text-audio-player` enthalten.
  `.details` (Vocab/Kanji-Karten, JP-only) bleiben klickbar.
- **Regel für nächstes Mal:** **Bevor neuer TTS-Player im Template
  eingehängt wird, alle bestehenden Speech-Synthesis-Mechanismen
  identifizieren** (`grep speechSynthesis`, `grep /api/tts`, `grep
  SpeechSynthesisUtterance`). Wenn parallel laufend → Sieger im Conflict
  definieren oder den alten Mechanismus für betroffene Container
  deaktivieren.

### Bug C — Voice-Name ohne Existenzcheck (silent fallback)
- **Ursache:** `de-DE-Neural2-F` existiert nicht (nur G/H bei Neural2 für
  de-DE — F ist en-US). Google liefert silently eine andere Voice ohne
  Fehlermeldung — verhalten ist undokumentiert und kann sich ändern.
- **Fix:** auf `de-DE-Neural2-G` korrigiert.
- **Regel für nächstes Mal:** **Voice-Namen NIE raten.** Vor jeder
  Verwendung gegen die voices-API prüfen:
  `curl 'https://texttospeech.googleapis.com/v1/voices?languageCode=<LANG>&key=$KEY'`
  und nur dort gelistete Namen verwenden.

### Aktuelle Regeln (Ergänzung)
23. **`:has()`-CSS-Selektoren immer Tag-qualifiziert** (`:has(img[src...])`,
    nie nur `:has([src...])`).
24. **Vor neuem TTS-Player alle bestehenden Speech-Mechanismen mappen** und
    Konflikte explizit auflösen (siehe Bug B oben).
25. **TTS Voice-Namen IMMER gegen voices-API verifizieren** vor
    Verwendung — Google macht silent fallback statt zu fehlern.

---

## 2026-04-25 18:30 — N5 Familie — Wer gehört zu dir? (Lesson ID 144)

### Erfolge
- 23 Familienvokabeln (alle in N5 canonical via `vocab`-Key, keine ERROR-Treffer)
  — eigene-Familie-Reihe (ちち/はは/あに/あね/おとうと/いもうと) + höfliche Reihe
  (おとうさん/おかあさん/おにいさん/おねえさん) + Sammelbegriffe (家族/兄弟/両親) +
  Personenwörter (人/男/女/男の子/女の子/友達/子供) + Zähler (一人/二人) + 私.
- 3 Grammatikkarten (uchi/soto, Possessiv の, います für Personen) — alle mit
  Romaji-Annotation in `title/structure/explanation`, dreizeiligen
  example_sentences (JP / Romaji / DE).
- 14 Quizfragen: 7 MC + 4 TF + 3 Matching — alle 3 erlaubten Typen, jeder ≥2×.
  Distraktoren aus selber semantischer Domäne (Familienbegriffe).
- 7 Pages (Einführung, Vokabeln 1+2, Grammatik, Dialog, Quiz, Zusammenfassung).
- Dialog mit eigenen Charakteren (Tanaka & Lisa), Format korrekt nach
  `_format_conversation` (`speaker: JP / (romaji) / -> DE`).
- Pipeline lief vollständig: validate → images (1 Thumb + 23 Vocab-Icons) →
  insert (Lesson 144, Trans atomar) → audio (1 MP3, 9 Sprecherzeilen, 34s) →
  slideshow (9 PNGs + 9 MP3s, ~5 min Generierung).
- Modul-Zuweisung: `category_id=34` (N5 Familie & Personen),
  `order_index=0`, `is_published=true`.
- Playwright-MCP-Verifikation: alle 7 Pages durchgeklickt, Slideshow-Wechsel
  ohne doppelte Bilder (Grid-Stacking funktioniert), Quiz rendert, keine
  Console-Errors, [Deck] Page-Verteilung 0/10/13/3/0/0/0 korrekt, 0 broken
  images, 35 Bilder geladen.

### Probleme / Erkenntnisse

1. **Familien-Kanji-Falle** — die "klassischen" N5-Familien-Vokabeln (家族, 兄弟,
   両親, 兄, 姉, 弟, 妹, お父さん, お母さん, お兄さん, お姉さん, 子供) enthalten
   alle Kanji, die im N5-Kanji-Set (80 Zeichen) FEHLEN: 兄/姉/弟/妹/家/族/親/供
   sind alle erst N4. Validator wirft 5× ERROR auf meinen ersten Draft. Aus
   N5-Familie-Kanji sind nur 人, 子, 女, 男, 父, 母, 友 erlaubt. **→ Regel: in
   `content_text`, `Grammar.example_sentences`, `LessonContent.text` Familie-
   Wörter mit N4-Kanji immer als Hiragana (かぞく, きょうだい, りょうしん,
   あに, あね, おとうと, いもうと) schreiben. Im `Vocabulary.word`-Feld bleibt
   die Kanji-Form, weil das die Karteikarte selbst ist.** SKILL.md §3 ergänzt.

2. **Quiz-Intro-Page (`page_type='quiz_carousel'`) ist auch ein content_text** —
   ich hatte „ます-Form von います" ohne Romaji-Klammern geschrieben. Validator
   fing es korrekt. **→ Regel: die einleitende `text`-Zelle vor den
   quiz_questions zählt voll als content_text mit Romaji-Pflicht.** Bereits
   in §3-Regel "Rōmaji NEBEN JEDEM JP-Zeichen — überall" enthalten, aber wert
   sich zu erinnern, dass auch Quiz-Intro dazu gehört.

3. **Modul-Zuweisung war kein Pipeline-Step** — nach `insert` ist die Lesson
   `category_id=NULL` und `is_published=False`. Manuelles `UPDATE lesson SET
   category_id=N, order_index=M, is_published=true WHERE id=X;` nötig, sonst
   taucht die Lesson nicht im Lernpfad auf. **→ Regel: nach `insert` IMMER
   die Modul-Zuweisung machen, basierend auf Thema → Slug-Mapping (siehe
   `lesson_category` Tabelle).** SKILL.md §6 mit Schritt [4d] ergänzt.

4. **Spalte heisst `order_index`, NICHT `order_in_module`** — kostete 1 Versuch.
   In SKILL.md §6 [4d] explizit dokumentiert.

5. **Slideshow-Generierung dauert ~5 Minuten und ist sequenziell** — 9 DALL-E-
   HD-Bilder + 9 TTS. Background-Run mit `TaskOutput timeout >= 300000ms`. Wenn
   man parallel an anderem arbeitet (z.B. Modul-Zuweisung), kein Problem.

6. **Bekannte Limitation gpt-image-1-mini**: die generierten "Tanaka"-Bilder
   wirken eher westlich-asiatisch, nicht spezifisch japanisch — gut genug für
   die Lektion, aber wenn man explizit japanische Charaktere bräuchte, müsste
   der Prompt expliziter sein. Akzeptabel als "stilisierte Charaktere".

### Aktuelle Regeln (kumulativ, Ergänzungen ab diesem Run)

20. **Familie-Kanji-Falle:** N5-Vokabeln können N4-Kanji enthalten — Hiragana
    in Beispielsätzen + Fliesstext nutzen (siehe SKILL.md §3 "Bekannte N5-
    Vokabel-Falle"-Block).
21. **Modul-Zuweisung nach Insert ist Pflicht** (`UPDATE lesson SET
    category_id=N, order_index=M, is_published=true`). Spalte heisst
    `order_index`, nicht `order_in_module`.
22. **Quiz-Intro-text-Cell wird wie content_text validiert** — Romaji-Pflicht
    gilt auch dort.

---

## 2026-04-25 — Slideshow-Render-Bug (Lesson ID 143, betrifft alle dialog_slideshow-Lektionen)

### Problem (vom User auf Production gemeldet)
Beim Slide-Wechsel in der Konversations-Slideshow waren kurzzeitig zwei Slides gleichzeitig sichtbar — die alte fadete unten weiter, die neue erschien oben darüber, sodass die Stage-Höhe verdoppelt wurde während der 400ms-Crossfade-Transition.

### Ursache
In [app/templates/lesson_view.html:945-961](app/templates/lesson_view.html#L945-L961) waren die Slides als normale Block-Geschwister im Stage-Container gerendert. Während Alpine `x-transition.opacity.duration.400ms` die alte ausblendet UND die neue einblendet, sind beide gleichzeitig `display:block` — und stapeln sich vertikal im Block-Flow.

### Fix
CSS-Grid-Stacking: `slideshow-stage` auf `display:grid`, jede `slideshow-slide` auf `style="grid-area:1/1;"`. Alle Slides belegen dieselbe Grid-Zelle, also überlappen sie statt sich vertikal zu stapeln. Stage-Höhe = grösster Slide; Crossfade läuft sauber.

### Regel für nächstes Mal
**Wenn das Slideshow-Template in `lesson_view.html` jemals umgeschrieben wird, MUSS das Grid-Stacking erhalten bleiben.** Die Pflicht-Struktur ist in SKILL.md §4c als „TEMPLATE-FALLE" dokumentiert. Verifikation nach Template-Change: in der gerenderten Lektion zwischen 2 Slides hin- und herklicken — wenn die Stage-Höhe „springt" oder doppelte Bilder erscheinen, ist das Grid-Stacking verloren gegangen.

### Aktualisierte Aktuelle Regeln (Ergaenzung zu den 10 Initial-Regeln)
11. **Slideshow-Template Grid-Stacking-Pattern** ([SKILL.md §4c TEMPLATE-FALLE](SKILL.md)) NIE entfernen, sonst doppeltes Bild beim Slide-Wechsel.

---

## 2026-04-24 21:15 — N5 Zahlen — Von 1 bis 10'000 (Lesson ID 143)

### Erfolge
- 22 Vokabeln (Grundzahlen 0-10, Zehner, 100/1'000/10'000, Yen, sai/nansai, denwa bangou, nanban) — alle N5, thematisch kohärent
- 3 Grammatik-Einträge (Alter 〜さい, Preis 〜円, Telefonnummer) — jeder mit Romaji im `romaji`-Feld UND in `structure` daneben, plus dreizeilig formatierten `example_sentences` (JP / Romaji / DE)
- 14 Quiz-Fragen: 7 MC + 4 TF + 3 Matching — alle 3 erlaubten Typen vertreten
- 7 Pages (Einführung, 2× Vokabeln, Grammatik, Dialog, Quiz, Zusammenfassung) — über Budget-Minimum
- Dialog mit eigenen Charakteren (Tanaka Haruto & Lisa Weber), nicht MNN-Original-Figuren; Format exakt nach `_format_conversation` (speaker: JP / (romaji) / → DE)
- Umlaute durchgängig korrekt (Einführung, nützlich, höflich, wörtlich, Sonderlesung, Fünfzig, überschreibt)
- Romaji in allen Feldern: `content_text` jedes JP-Worts, `Grammar.title/.structure/.explanation/.example_sentences`, `QuizQuestion.hint/.explanation`, `QuizOption.option_text/.feedback`
- Thumbnail via DALL-E (gpt-image-1-mini) generiert, lokal gespeichert, URL gesetzt
- Validator lief sauber durch (nur thumbnail_url-Fehler vor dem images-Step, erwartet)
- Insert-Transaktion atomar, Lesson 143 + 7 Pages + 22 Vocab-Referenzen + 3 Grammar + 14 Questions + 38 Options in einer Transaktion

### Probleme / Erkenntnisse

1. **pipeline.py `generate_single_image(purpose=…)` hatte falsche Signatur** — `AILessonContentGenerator.generate_single_image()` in `app/ai_services.py:333` akzeptiert nur `prompt`, `size`, `quality`. `purpose` war ein halluzinierter Parameter. Zusätzlich: Methode liefert `image_bytes` (PIL + raw bytes) statt direktem URL; Pipeline nutzte aber `result.get("image_url")` was nur ein Platzhalter-String ist. **Fix angewandt**: `pipeline.py` schreibt bytes jetzt lokal nach `app/static/uploads/generated/thumbnail_{slug}_{ts}.png` und setzt relative URL. → **Regel: Wenn Pipeline-Code Services aufruft, periodisch auf Drift prüfen; `gen.generate_single_image()` hat sich seit Stub-Zeit geändert.**

2. **MNN-Import-Altdaten inkonsistent**: 8 bestehende Vokabeln (ひゃく, せん, まん, えん, さい, なんさい, でんわばんごう, なんばん) hatten Romaji in der `reading`-Spalte (Hepburn-Text statt Hiragana) und NULL in `romaji`. Die `_get_or_create_vocab`-Funktion hat sie korrekt dedupliziert — aber die inkonsistenten Daten blieben auf der Karte sichtbar. **Fix angewandt**: UPDATE auf alle 8 Wörter: `reading` → Hiragana, `romaji` → vorheriger Romaji-Wert. → **Regel: Beim Duplicate-Match zusätzlich prüfen, ob die Bestands-Vokabel dem heutigen Schema genügt (`romaji NOT NULL`, `reading matches ^[ぁ-んァ-ヶー]+$`). Wenn nein: opportunistisch backfillen, nicht nur neue Lektion drumrum schreiben.**

3. **DeprecationWarnings für `datetime.utcnow()`** in pipeline.py — niedrigprio, aber jetzt mehrfach gesehen. Python 3.13-ready: `datetime.now(datetime.UTC)`. Kein neuer Fehler, nur Lint.

### Aktuelle Regeln (kumulativ, wichtigste zuerst)

1. **Anfänger-First (Claudio dogfoodet)** + **Mayuko-Fachreview** (Lehrerin gibt JP-Inhalt frei) + **JLPT-Leitprinzip** (Niveau-Disziplin, Vollständigkeit, offizielle Listen).
2. **Anfänger-Only (N5/N4)** — N3+ out-of-scope.
3. **Keine `fill_in_the_blank` Quiz-Typen.**
4. **Instruction-Language default `german`.**
5. **Beispielsätze nur mit Vokabeln/Kanji ≤ Lesson-Level.**
6. **Umlaute echt (UTF-8), nie ASCII-Fallback.**
7. **Duplicate-Check via `_get_or_create_*` vor Kana/Kanji/Vocabulary/Grammar-Insert.**
8. **Atomare Transaktion:** Ganze Lektion oder nichts.
9. **Verifikation Pflicht** (DB-Query, Playwright oder HTTP-Fallback) bevor `is_published=True`.
10. **Mind. 2 Quiz-Typen pro Lektion** (Zahlen-Lesson: 3 genutzt).
11. **MC-Distraktoren aus selber semantischer Domäne.**
12. **Grammar-Eintrag: `romaji` immer füllen**, nicht nur `structure`.
13. **Admin-Credentials:** `ADMIN_EMAIL` und `ADMIN_PASSWORD` aus `.env` — nicht hardcoden.
14. **Admin-Lesson-Liste:** `/api/admin/lessons` (JSON), nicht `/admin/manage/lessons` (AJAX-Shell).
15. **Docker-Start-Check:** Docker-Desktop-Prozess prüfen, nicht nur `docker compose ps`.
16. **Rōmaji in ALLEN Textfeldern** (auch content_text, grammar.structure, quiz.hint/explanation, option.feedback).
17. **Umlaute hart validiert** — jedes erkannte `ue/oe/ae/ss` bricht validate ab.
18. **Beim Duplicate-Match Bestands-Vokabel auf aktuelles Schema prüfen** (reading=Hiragana, romaji NOT NULL). Wenn inkonsistent: im selben Run opportunistisch backfillen.
19. **Pipeline-Service-Calls periodisch auf Signatur-Drift prüfen** — `generate_single_image` akzeptiert kein `purpose`-Arg, liefert `image_bytes` statt finalem URL.

## 2026-04-24 21:30 — User-Feedback: Romaji überall, Umlaute statt ASCII

**Claudio nach weiterer Sichtung von Lesson 142 (Grammar-Karte):**
1. Grammar-Karte zeigte `[Nomen] + を + ください` ohne Romaji-Auflösung daneben.
   Romaji war nur separat als `[noun] + wo + kudasai` unten, aber nicht direkt
   neben der JP-Struktur sichtbar.
2. Meine content_text-Plaintexts hatten Umlaut-Fallbacks (ue/oe/ss/ae) statt
   echten Umlauten. "moechtest", "hoeflich", "koestlich", "haengen" usw.

**Actions:**
- SKILL.md §3 "Keine Umlaut-Fallbacks": hart ausformuliert. Gilt in jedem
  DE-Text-Feld — `content_text`, `hint`, `explanation`, `feedback`,
  `option_text`, `Lesson.description`, `LessonPage.title` usw.
- SKILL.md §3 "Rōmaji NEBEN JEDEM japanischen Zeichen": komplett ausgebaut
  mit Liste aller betroffenen Felder: `content_text`, `Grammar.title`,
  `Grammar.structure`, `Grammar.explanation`, `Grammar.example_sentences`,
  `QuizQuestion.question_text/hint/explanation`, `QuizOption.option_text/feedback`,
  `Vocabulary.romaji`, `Vocabulary.example_sentence_english`.
- pipeline.py Validator:
  - **Umlaut-Fallback-Check** ist jetzt HARTER Fehler (vorher nur informativ).
    Erkennt `hoeflich, fuer, Einfuehrung, Getraenk, Schueler, koennen` etc.
  - **Romaji-in-content_text-Check**: wenn `content_text` JP-Zeichen enthält,
    muss mind. eine Klammer-Passage `(romaji)` vorkommen.
- Lesson 142: fix2-Script ausgeführt. 4 content_text neu mit echten Umlauten
  und Romaji-Annotation pro JP-Wort; Grammar #48 (〜をください) mit
  strukturiertem example_sentences (dreizeilig: JP / Romaji / DE),
  angereicherter explanation mit Romaji an jeder JP-Stelle.

**Neue Regel (kumulativ, ab sofort):**
16. **Rōmaji in ALLEN Textfeldern** (nicht nur Vocab/Grammar-Records).
    JP-Zeichen bekommen immer `(romaji)` in Klammern direkt danach.
17. **Umlaute hart validiert** — jedes erkannte `ue/oe/ae/ss` in deutschen
    Wörtern bricht den validate-Schritt ab.

---

## 2026-04-24 21:20 — MNN-Rohdaten-Recherche & Konversations-Pattern

**Recherche-Ergebnis auf Claudios Anfrage:**

1. **MNN-Rohdaten liegen vor**: `scripts/mnn_data/beginner1_lesson01.json` bis `beginner2_lesson50.json` — 50 Lektionen komplett strukturiert (Vocabulary, Grammar, Conversation mit speaker/japanese/romaji/english, teils additional_conversations).

2. **Bestehende 10 MNN-Lektionen in der DB** (IDs 131–141, `MNN L1…L5` EN + DE) wurden via `scripts/import_mnn.py` **direkt importiert** — keine AI. Layout: 5 Seiten (Vokabeln → Grammatik → Konversation → Übung → Prüfung). Konversation liegt als Plaintext in `lesson_content.content_text` auf `page_number=3`, Format: `Speaker: 日本語\n  (romaji)\n  → English/Deutsch`, Leerzeile zwischen Sprechern — erzeugt durch `_format_conversation()` in [scripts/import_mnn.py:170](../../scripts/import_mnn.py#L170).

3. **Konsequenz für generate-lesson:**
   - MNN-JSON dient als **Vorlage**, nicht zur Copy-Paste. Claude schreibt auf Basis der MNN-Grammatik/Vokabeln eine neue Lektion mit **anderen Charakteren** (nicht Miller/Satou/Yamada) und leicht variiertem Dialog-Text.
   - Konversations-Page ist Pflicht und nutzt exakt das `_format_conversation()`-Plaintext-Format.

**Actions:**
- SKILL.md §2a neu: Komplette Sektion zu MNN-Nutzung (Rohdaten-Pfade, Vorlagen-Regel, Konversations-Format).
- SKILL.md §4: Dialog-Page (bisher "A:/B:") durch das `_format_conversation`-Format ersetzt.
- SKILL.md §9: Explizite Pfade zu allen 50 MNN-JSONs und import_mnn.py-Verweis.

---

## 2026-04-24 21:00 — User-Feedback nach visueller Sichtung Lesson 142

**Claudio nach Öffnen von Lesson 142 im Browser:**
1. HTML-Tags erscheinen als Text statt gerendert → **Ursache gefunden:** `lesson_view.html:683` nutzt `{{ content.content_text | nl2br }}`, das escaped HTML. Nur Plaintext wird korrekt dargestellt.
2. Rōmaji fehlt komplett in der Lektion → User verlangt "Oman'sch-japanisch-westliche Schreibweise". `Vocabulary` hatte bisher kein `romaji`-Feld.
3. Bilder fehlen (Thumbnail + Schlüsselvokabeln).
4. Lektion inhaltlich zu dünn: 10 Vokabeln + 1 Grammar + 7 Quiz reichen nicht für einen wertvollen Lernpass.

**Actions (alle in SKILL.md §3, §4, §5 hochgehoben):**
- Neue Migration `a3f5c2d1b8e9`: `Vocabulary.romaji` Spalte (String(200), nullable).
- Neue Regel: **KEIN HTML in `content_text`** (Plaintext + `\n\n`).
- Neue Regel: **Rōmaji ist Pflicht** in `Vocabulary.romaji`, `Grammar.romaji` und am Anfang jedes `example_sentence_english`.
- Neue Regel: **Bilder (Thumbnail + ≥3 Vokabel-Bilder) sind Pflicht**, nicht optional.
- Neues Budget: **15–25 Vokabeln, 2–4 Grammar, 10–18 Quiz, ≥5 Pages** (+ separater Dialog-Page).
- Validator in `pipeline.py` erzwingt alle diese Regeln beim `validate`-Schritt.

---

## 2026-04-24 20:30 — N5 Essen im Restaurant (Lesson ID 142)

### Erfolge
- 10 Vokabeln (レストラン, メニュー, 水, お茶, ご飯, 肉, 魚, 飲み物, 食べ物, 美味しい) — thematisch kohärent, alle N5
- 1 Grammatik (〜をください) — die zentrale Bestell-Formel
- 7 Quiz-Fragen: 4 MC + 2 TF + 1 Matching — 3 Typen, passt zu Regel "mind. 2 verschiedene"
- MC-Distraktoren aus derselben semantischen Domäne (Essens-/Trink-Vokabular), kein offensichtlicher Blindgänger
- Beispielsätze nutzten ausschliesslich N5-Vokabeln und -Kanji, meist Hiragana-fokussiert
- Alle DE-Umlaute korrekt (Einführung, höflich, Getränk, köstlich) — kein ASCII-Fallback im HTML
- DB-Insert atomar, pipeline.py validate+insert klappte auf Anhieb

### Probleme / Erkenntnisse

1. **Docker Desktop war aus.** → **Regel: Start-Check MUSS Docker-Desktop-Prozess prüfen, nicht nur `docker compose ps`. Wenn Docker down: PowerShell-Start, 30-60s warten, dann `docker compose up db -d`.** (In SKILL.md §1 hochgehoben.)

2. **`verify.py` ist zweifach defekt:**
   - Nutzt `username=admin` + `password=admin` → Login-Form braucht `email` + `password`, und Credentials stehen in `.env` als `ADMIN_EMAIL` / `ADMIN_PASSWORD`.
   - Wartet auf `**/dashboard*` Redirect → Admin-Login leitet zu `/admin`, nicht `/dashboard`.
   → **Regel: verify.py muss aus `.env` laden (`ADMIN_EMAIL`, `ADMIN_PASSWORD`), Form-Feld heisst `email`, Post-Login-URL ist `/admin`.** (Pipeline-Fix gehört in SKILL.md §6 und verify.py selbst.)

3. **MCP-Playwright-Browser kann besetzt sein** (parallele User-Chrome-Session). Fehlermeldung: "Browser is already in use". → **Regel: Wenn MCP-Browser geblockt, Fallback auf HTTP-Requests-basierte Verifikation (requests.Session mit CSRF + Login + Content-Check). Der Hauptzweck — Struktur/Content/Umlaut-Korrektheit — ist damit erfüllt; visueller Deck-Karussell-Check muss dann manuell vom User gemacht werden.**

4. **Admin-Lesson-Liste unter `/admin/manage/lessons` ist SPA (AJAX).** Server-side gerenderte HTML enthält KEINE Lesson-Titel; die werden per JS aus `/api/admin/lessons` geladen. → **Regel: Verifikation der Sichtbarkeit muss `/api/admin/lessons` treffen, nicht die HTML-Shell.**

5. **pipeline.py nutzt `datetime.utcnow()`** — Python 3.12 DeprecationWarning. Niederpriorisierter Lint-Fix. → Nur Info, keine neue Regel.

### Aktuelle Regeln (kumulativ, wichtigste zuerst)

1. **Anfänger-First (Claudio dogfoodet)** + **Mayuko-Fachreview** (Lehrerin gibt JP-Inhalt frei) + **JLPT-Leitprinzip** (Niveau-Disziplin, Vollständigkeit, offizielle Listen).
2. **Anfänger-Only (N5/N4)** — N3+ out-of-scope.
3. **Keine `fill_in_the_blank` Quiz-Typen.**
4. **Instruction-Language default `german`.**
5. **Beispielsätze nur mit Vokabeln/Kanji ≤ Lesson-Level.**
6. **Umlaute echt (UTF-8), nie ASCII-Fallback.**
7. **Duplicate-Check via `_get_or_create_*` vor Kana/Kanji/Vocabulary/Grammar-Insert.**
8. **Atomare Transaktion:** Ganze Lektion oder nichts.
9. **Verifikation Pflicht** bevor is_published=True. Wenn MCP-Browser blockiert → HTTP-Fallback ausreicht, aber User muss visuell klicken.
10. **Mind. 2 Quiz-Typen pro Lektion.**
11. **MC-Distraktoren aus selber semantischer Domäne.** (validiert im Essen-Run)
12. **Grammar-Eintrag: `romaji` immer füllen**, nicht nur `structure`.
13. **Admin-Credentials:** `ADMIN_EMAIL` und `ADMIN_PASSWORD` aus `.env` — nicht hardcoden.
14. **Admin-Lesson-Liste:** `/api/admin/lessons` (JSON), nicht `/admin/manage/lessons` (AJAX-Shell).
15. **Docker-Start-Check:** Docker-Desktop-Prozess prüfen, nicht nur `docker compose ps`.

