# Kana-Refinement-Pattern (bestehende Hiragana-/Katakana-Lektion auf Studio-Qualität heben)

Wiederverwendbares Muster zum **Überarbeiten einer bereits existierenden Kana-Lektion**
(im Gegensatz zum Neu-Generieren via Pipeline). Erprobt an Hiragana 1–5 (Lesson-IDs
146–150, überarbeitet 2026-05-02 — SQL in `scripts/refine_hiragana_*.sql` +
`*_quiz.sql`). Direkt übertragbar auf die Katakana-Lektionen.

**Designprinzip:** Das Pattern gibt **Struktur + Themen** vor, **nicht die Antworten**.
Jede Überarbeitung recherchiert die Inhalte selbst und entscheidet didaktisch — so
entsteht Quellen-Triangulation statt 1:1-Reproduktion von Annahmen aus einer Vorlage.

## Refinement-Pattern (pro Lektion)

1. **Strichfolge** in `kana.stroke_order_info` eintragen. Format-Beispiel: „3 Striche:
   1) waagerechter Strich oben; 2) langer geschwungener Bogen von oben links nach unten
   links; 3) Schleife rechts unten".
2. **Mnemonics-Boxen** pro Reihe (Tofugu-Stil: kompakt, einprägsam).
3. **Aussprache-Anker** mit deutschen Beispielwörtern, Ausnahmen prominent markiert.
   ⚠️ Deutsche Anker **kritisch prüfen** — „u wie Buch" ist falsch (japanisches u ist
   unrundiert). Falsche Anker waren in der ursprünglichen Hiragana-L1 ein realer Mangel.
4. **Vokal-Entstummung (Devoicing)** wo relevant — eigener Block mit Beispielen aus den
   Lektions-Kana.
5. **Etymologie-Hinweis** (woher die Zeichen historisch stammen) — kurz, zur Motivation,
   kein Pflicht-Lernstoff.
6. **Verwechslungs-Paare** mit konkreten Unterschieds-Tipps (ね/れ/わ/ぬ, さ/き/ち, シ/ツ, ソ/ン …).
7. **Mini-Wortliste** mit echten N5-Vokabeln, die mit den bisher gelernten Zeichen lesbar sind.
8. **Quiz** auf 14+ Fragen erweitern: bestehende Lesungs-Fragen behalten, ergänzen um
   mind. 1 Wort-Bedeutungs-Frage und 1 Frage zum neuen Konzept der Lektion
   (Devoicing / Ausnahme / を-Sonderrolle / ん / Yōon-Mora / Dakuten-Mechanik …).

## Recherche-Mandat (Triangulation-Pflicht)

Eigenständig recherchieren — nicht auf Annahmen aus einer Vorlage verlassen. Pflicht-Quellen via WebFetch:

- Tofugu Hiragana/Katakana Guide (tofugu.com/japanese/learn-hiragana/)
- Wikipedia: Hiragana / Katakana / Japanese phonology
- Migaku Hiragana-/Katakana-Chart
- Mind. 1 weitere (NHK World, Genki I Appendix, Minna no Nihongo Furigana-Liste, …)

Bei Widerspruch zweier Quellen (Aussprache, Strichanzahl): in einer kurzen
Recherche-Zwischen-Zusammenfassung notieren und **begründet** entscheiden, welcher Quelle
gefolgt wird. Vor dem Schreiben: 5–10 Bullets „was ist didaktisch wichtig" an Claudio,
auf „ok" warten — erst dann SQL schreiben.

## Themen-Schwerpunkte je Kana-Block (recherchiere Details selbst)

- **T-/H-Reihe:** mehrere Aussprache-Ausnahmen; Devoicing besonders relevant; は-Sonderrolle
  (Partikel) als Grundstein erwähnen, ohne zu überfordern.
- **M/Y/R/W + ん:** Y-/W-Reihe unvollständig (historisch erklären); を-Sonderstatus;
  ん als einziges vokalloses Zeichen mit Aussprache-Varianten; japanisches „r" vs. dt. r/l.
- **Dakuten/Handakuten:** Mechanik (welche Konsonanten wie modifiziert); Homophone +
  Faustregel; regionale/generationelle Variation (JLPT-Hörverstehen); historische Entwicklung.
- **Yōon:** Konzept statt neuer Zeichen; Mora-Zählung; irreführende Romaji (sh/ch/j);
  groß-vs-klein-Verwechslung; Schreibkonvention der Position des kleinen Zeichens.

## Workflow (self-hosted, Stand 2026-05)

1. `/status` für Setup-Check.
2. SQL-Analyse der Ziel-Lesson (Pages, Content, Quiz, betroffene `kana`-IDs).
3. Recherche parallel (Pflicht-Quellen oben) → Zwischen-Zusammenfassung → auf „ok" warten.
4. **Separate SQL-Files pro Lektion** (`scripts/refine_<system>_<n>.sql` +
   `_quiz.sql`) — leichter zu reviewen und rollback-fähig.
5. `UPDATE kana` für die betroffenen IDs mit `stroke_order_info`.
6. **Visual-Test mit Playwright** (alle Pages durchklicken, Karten flippen, eine
   Quiz-Frage einsenden um AJAX-Rendering zu prüfen) — Pflicht vor Commit
   (siehe [improve-jpl Deck-Karussell-Falle]).
7. Commit auf Deutsch + Push. Die SQL schreibt direkt in die lokale Postgres = Produktions-DB
   (kein Cloud-Sync mehr — Cloud SQL ist seit Self-Hosting-Umzug 2026-05-24 abgebaut).
8. Code-Änderungen (z.B. Markdown-Filter) zusätzlich via `/deploy` (Container-Rebuild auf
   hp-ubuntu); reine Content-/DB-Änderungen brauchen keinen Deploy.

## Akzeptanzkriterien (recherchierter Inhalt, nicht vorgegeben)

- Alle Kana der Lektion haben `stroke_order_info`.
- Aussprache-Ausnahmen prominent erklärt (so viele wie es real gibt).
- Devoicing-Block mit lektions-spezifischen Beispielen.
- Mnemonics für alle Zeichen; Verwechslungspaare mit Tipps.
- 5–8+ Mini-Wörter zum Lesen üben.
- Quiz 14+ Fragen (mehr Kana → grösserer Pool), mind. 1 Wort-Bedeutung + 1 Konzept-Frage.
- Live-Preview (`localhost:5000/lessons/<id>`) zeigt alle Änderungen korrekt.

## Parallel-Sessions

Mehrere Lektionen lassen sich in getrennten Sessions parallel überarbeiten. Dann: nur eine
Session startet Flask auf :5000, die anderen testen via `curl`/Playwright gegen die laufende
Instanz. Erst wenn alle lokal fertig + committed sind, in einer Master-Session `git pull`.
