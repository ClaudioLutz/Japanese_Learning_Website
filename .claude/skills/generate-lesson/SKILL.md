---
name: generate-lesson
description: Generiert eine vollständige Japanisch-Lektion (Lesson + LessonPages + LessonContent + QuizQuestions) für japanese-learning.ch. Claudio schreibt die Inhalte (Kana/Kanji/Vokabeln/Grammatik/Quiz) selbst — keine OpenAI/Gemini-API-Aufrufe ausser für Bilder (DALL-E). Auto-aktivieren, wenn Claudio "neue Lektion", "Lektion generieren", "Content für N5/N4", "Mayuko braucht eine Lektion über X", "erstelle eine Lektion zu Thema Y" sagt oder per `/generate-lesson` aufruft. Nutzt JLPT-Vokabellisten und Minna no Nihongo als Ausgangsquellen, schreibt direkt in die lokale Postgres-DB (docker-compose), verifiziert via Playwright, committet via Git.
---

# generate-lesson — Anfänger-Lektionen für japanese-learning.ch

## Auftrag

Erstelle eine **komplette, sofort nutzbare Lektion** für Mayuko und andere deutschsprachige Anfänger. **Du schreibst den gesamten Text-Content selbst** (keine OpenAI/Gemini-Calls). Der Skill ist der Orchestrator: Er gibt dir Schema, Guardrails und die Persistierungs-/Verifikations-/Git-Schritte vor; du produzierst den japanischen Content als strukturiertes JSON.

**Einzige Ausnahme: Bilder.** Für `thumbnail_url` und `Vocabulary.image_url` kannst du DALL-E per Script aufrufen (siehe §7).

---

## 1. Start-Check (immer zuerst)

Bevor du überhaupt Content schreibst:

1. **Lies [learnings.md](learnings.md).** Dort steht, was in vorherigen Runs geklappt hat und was nicht. Wende diese Regeln strikt an.
2. **Lies [improve-jpl/SKILL.md](../improve-jpl/SKILL.md).** Die Produkt-Vision (Mayuko-Lackmustest, Nicht-Ziele) gilt uneingeschränkt.
3. **Docker-Stack muss laufen — zweistufiger Check:**
   - **a) Docker-Desktop-Prozess:** `docker compose ps db` schlägt mit "cannot find the file specified" / "docker daemon not running" fehl, wenn Docker Desktop nicht läuft. In dem Fall: `Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"` (PowerShell) — Start dauert 30–60 s.
   - **b) DB-Container:** Danach `docker compose up db -d` und mit `docker exec postgres_db pg_isready -U app_user -d japanese_learning` warten, bis "accepting connections" erscheint.
4. **DB-Status prüfen:** Führe `python .claude/skills/generate-lesson/pipeline.py status` aus. Das zeigt, welche Themen/JLPT-Level wenig approved Content haben — Grundlage für Vorschlag bei Aufruf ohne Argumente.
5. **Admin-Credentials aus `.env`:** Für alle verifikationsbezogenen Logins gilt `ADMIN_EMAIL` und `ADMIN_PASSWORD` aus der lokalen `.env`. NIEMALS hardcoden. Login-Form-Feld heisst **`email`** (nicht `username`), Post-Login-Redirect ist **`/admin`** (nicht `/dashboard`).

## 2. Input-Modi

| Aufruf | Verhalten |
|---|---|
| `/generate-lesson` (ohne Args) | DB-Gap-Analyse → 3 Themen-Vorschläge mit Begründung → User wählt |
| `/generate-lesson N5 Familie` | Direktes Thema, JLPT-Level N5. Wenn thematisch passendes MNN-Kapitel existiert, **orientiere dich daran** (siehe §2a). |
| `/generate-lesson --from-mnn 3` | Quelle: Minna no Nihongo Kapitel 3 (lies `scripts/mnn_data/beginner1_lesson03.json`). Siehe §2a. |
| `/generate-lesson --from-jlpt N5` | Zufälliges noch nicht abgedecktes N5-Thema |

## 2a. Minna-no-Nihongo-Quellen (WICHTIG)

**Rohdaten liegen vor:** `scripts/mnn_data/beginner1_lesson01.json` … `beginner2_lesson50.json` (50 Lektionen). Jede Datei enthält `vocabulary[]`, `vocabulary_countries[]`, `grammar[]`, `conversation{title, lines[]}` und teils `additional_conversations[]`. Die bestehenden 10 Lektionen in der DB (IDs 131–141, Titel `MNN L1…L5` EN+DE) wurden per `scripts/import_mnn.py` **direkt** importiert, ohne AI, als wörtliche Übernahme.

**Wie Claude MNN nutzt:**
1. **MNN ist Vorlage, nicht Copy-Paste.** Die bestehenden 10 Lektionen sind Wort-für-Wort-Import. Deine Aufgabe: auf derselben thematischen/grammatikalischen/vokabulären **Linie** eine **neue Lektion** schreiben, mit:
   - **Anderen Namen/Personen.** MNN nutzt Mike Miller, Satou Keiko, Guputa-san, Yamada. Du nutzt andere Namen (z.B. Tanaka Haruto, Lisa Weber, Ueno Sensei). Keine MNN-Originalfiguren wiederverwenden.
   - **Leicht anderen Beispielsätzen** — gleiche Grammatik, gleiche Vokabelsätze, aber neu formuliert. Kein Satz wird 1:1 aus der MNN-JSON übernommen.
   - **Gleichem Grammatik-Kern** — wenn MNN-Kapitel 3 Demonstrativpronomen lehrt, lehrst auch du Demonstrativpronomen, mit denselben Strukturen (`これ/それ/あれ + は + N + です`).
2. **Vokabeln übernehmen:** Die Vokabel-Liste aus MNN-JSON darfst du weitgehend übernehmen (Vocabulary-Tabelle ist eh dedupliziert — Wörter wie `わたし` sind schon da). Füge Romaji hinzu, wenn fehlt.
3. **Konversation ist Pflicht** — siehe §4 Page-Struktur "Dialog/Anwendung". Nutze dieselbe `speaker / japanese / romaji / english`-Struktur wie in der MNN-JSON, aber mit deinen neuen Namen und leicht anderem Verlauf.
4. **Zusätzlicher DB-Gap-Check:** Bevor du eine neue Lektion zu MNN-Kapitel N schreibst, prüfe ob `MNN L{N}:` bereits existiert (`Lesson.title` LIKE `MNN L{N}:%`). Wenn ja, wähle einen Titel ohne `MNN L{N}:`-Präfix, damit es keine Kollision mit dem Original-Import gibt (z.B. `N5 Selbstvorstellung — Tanaka trifft Lisa`).

**Konversations-Plaintext-Format** (entspricht `_format_conversation` in `scripts/import_mnn.py:170`):
```
Tanaka: こんにちは。わたしは たなかです。
  (Konnichiwa. Watashi wa Tanaka desu.)
  → Guten Tag. Ich bin Tanaka.

Lisa: はじめまして。リサです。ドイツから きました。
  (Hajimemashite. Risa desu. Doitsu kara kimashita.)
  → Freut mich. Ich bin Lisa. Ich komme aus Deutschland.
```
Leerzeile zwischen Sprechern, Einrückung der Romaji-Zeile mit zwei Leerzeichen, `→` für die deutsche Übersetzung.

## 3. Harte Constraints (Nicht-Verhandelbar)

Verletzung ⇒ sofortiger Abbruch, keine Insertion:

- **Quiz-Typen NUR**: `multiple_choice`, `true_false`, `matching`. **KEIN** `fill_blank` (siehe CLAUDE.md §"Quiz-System").
- **JLPT-Level NUR**: N5 oder N4. Kein N3/N2/N1 (siehe improve-jpl §"Nicht-Ziele").
- **Keine Umlaut-Fallbacks** in **allen** deutschen Texten (Einleitung, Grammar-Explanation, Quiz-Frage/Hint/Explanation/Feedback, Dialog-Übersetzung, Zusammenfassung, Lesson.description/title, LessonPage.title): **immer Ü/Ö/Ä/ß** (oder ss), **niemals UE/OE/AE/SS**. "Schüler" statt "Schueler", "höflich" statt "hoeflich", "Grüße" statt "Gruesse", "für" statt "fuer". UTF-8 durchgängig. Gilt auch in `content_text`, `hint`, `explanation`, `feedback`, `option_text` — überall, wo deutscher Fliesstext steht.
- **Rōmaji NEBEN JEDEM japanischen Zeichen, das der Lerner nicht automatisch lesen kann — überall, ausnahmslos.** Jedes Auftreten von Kanji/Hiragana/Katakana in einem Text-Feld bekommt in derselben Zeile Rōmaji in Klammern `(romaji)`. Folgende Felder sind alle betroffen:
  - **`LessonContent.content_text`** (Einleitung, Grammatik-Erklärung, Dialog, Zusammenfassung): jedes JP-Wort/Phrase mit Rōmaji in Klammern. Beispiel: `Dort begrüßt dich das Personal mit 「いらっしゃいませ」 (irasshaimase, 'Willkommen')`. In jedem Satz neu, nicht nur beim ersten Vorkommen.
  - **`Grammar.title`**: wenn der Titel JP-Zeichen enthält (`〜をください (höfliche Bitte)`), muss Rōmaji dabei sein → `〜をください (~ wo kudasai — höfliche Bitte)`.
  - **`Grammar.structure`**: wenn die Struktur JP-Zeichen enthält (`[Nomen] + を + ください`), muss direkt danach die Rōmaji-Variante stehen. Da das `structure`-Feld nur **einzelne Zeile** ist: Rōmaji in derselben Zeile in Klammern, z.B. `[Nomen] + を + ください  ([noun] + wo + kudasai)`. Zusätzlich bleibt das `Grammar.romaji`-Feld (wird separat gerendert). Beide redundant zu haben ist OK — das Template zeigt mal das eine, mal das andere, Mayuko sieht es so oder so.
  - **`Grammar.explanation`** (DE-Erklärung): jeder JP-Ausdruck in Klammern mit Rōmaji. `「を」 (wo, ausgesprochen 'o')` statt nur `「を」`.
  - **`Grammar.example_sentences`**: jeder JP-Satz JP-Zeile → Rōmaji-Zeile → DE-Zeile (dreizeilig).
  - **`QuizQuestion.question_text`, `.hint`, `.explanation`**: wenn JP-Zeichen darin stehen, Rōmaji in Klammern. `Was bedeutet 「水」 (mizu)?` statt `Was bedeutet 「水」?`.
  - **`QuizOption.option_text`, `.feedback`**: wenn JP darin steht, Rōmaji in Klammern. In Matching-Optionen `肉 (niku) | Fleisch` statt `肉 | Fleisch`.
  - **`Vocabulary.romaji`** (Datenbankfeld, eigene Spalte): Hepburn-Rōmaji des Wortes.
  - **`Vocabulary.example_sentence_english`** beginnt mit Rōmaji-Satz, Format `"Romaji — English"` (bereits in §5 beschrieben).
  - **`Vocabulary.example_sentence_japanese`** bleibt rein JP — dort ist Rōmaji redundant, weil `reading` + `romaji` in derselben Vokabel-Karte stehen.
  - Ziel: Mayuko kann **jeden Satz** überall in der Lektion westlich aussprechen, selbst wenn sie ein Kanji nicht kennt.
- **Instruction-Language**: default `'german'` (Mayuko ist primäre Zielgruppe). Englisch nur auf explizite User-Anweisung.
- **Beispielsätze dürfen NUR Kanji/Vokabeln des eigenen oder eines niedrigeren JLPT-Levels enthalten.** N5-Lektion darf keine N3-Kanji im Beispielsatz haben. Wenn unvermeidbar: schreibe den Satz in Hiragana.
- **`created_by_ai = True`** für alle generierten Kana/Kanji/Vocabulary/Grammar-Einträge. `LessonContent.generated_by_ai = True` ebenfalls.
- **`status = 'approved'`** direkt (User-Entscheidung 2026-04-20).
- **Duplicate-Check**: Vor jedem INSERT in Kana/Kanji/Vocabulary/Grammar prüfen ob `character`/`word`/`title` schon existiert → bestehende ID wiederverwenden, NICHT neue Zeile erzeugen.
- **KEIN HTML in `content_text`** (content_type `text`). Das Template [lesson_view.html:683](../../app/templates/lesson_view.html#L683) rendert mit `| nl2br`, nicht `| safe` — alle Tags erscheinen als Text. Nutze **Plaintext mit `\n\n` für Absätze**, keine `<p>`, `<b>`, `<ul>` usw. Für Hervorhebung: Anführungszeichen 「…」 (japanisch) oder kursiv via Markdown-Konvention im Plaintext.
- **Rōmaji ist PFLICHT** — an drei Stellen:
  1. `Vocabulary.romaji` (neue Spalte seit Migration `a3f5c2d1b8e9`): Hepburn-Transkription des Wortes, z.B. `word="家族", reading="かぞく", romaji="kazoku"`.
  2. `Grammar.romaji` (bestand schon): Struktur in Rōmaji, z.B. `"[noun] + wo + kudasai"`.
  3. `example_sentence_english`: muss mit Rōmaji-Version des Satzes beginnen, Format `"Romaji — English meaning"`, z.B. `"Watashi no kazoku wa yo-nin desu. — My family has four people."`. So sieht Mayuko in JEDER Darstellung die westliche Lesung.
- **Bilder sind PFLICHT** — `thumbnail_url` muss vor Insert gesetzt sein. Pipeline-Schritt `images` (DALL-E) läuft vor `insert`, NICHT optional. Zusätzlich: **jede Vokabel** muss `image_url` haben (MNN-DE-Standard, siehe §4-Budget).
- **`Vocabulary.image_url` muss relativ zu `UPLOAD_FOLDER` sein** (= `app/static/uploads/`), NICHT absolut. Das Template [lesson_view.html:859](../../app/templates/lesson_view.html#L859) ruft `url_for('routes.uploaded_file', filename=content_data.image_url)` auf — die Route [routes.py:3973 `/uploads/<path:filename>`](../../app/routes.py#L3973) dient aus `UPLOAD_FOLDER`. Richtige Werte: `vocab_generated/vocab_abc.png`, `vocabulary/images/vocab_124.png`. **Falsch**: `/static/uploads/vocab_generated/…`, `http://…`, `static/uploads/…`.
- **Audio für die Konversation ist PFLICHT** — jede Dialog-Page bekommt ein eigenes `LessonContent(content_type='audio')` **vor** dem Dialog-Text (`order_index=1`, Text auf `order_index=2`). Der Pipeline-Schritt `audio {lesson_id}` rendert via Google Cloud TTS (Neural2-B, langsam=0.85) eine einzige MP3 mit allen japanischen Sprecher-Zeilen, 700ms-Pausen dazwischen. Speicherort: `app/static/uploads/lessons/audio/lesson_{id}/conversation.mp3`. Felder im LessonContent: `file_path="lessons/audio/lesson_{id}/conversation.mp3"` (relativ zu `UPLOAD_FOLDER`!), `file_type="audio/mpeg"`, `title="Konversation (Audio)"`. Das Template ([lesson_view.html:674](../../app/templates/lesson_view.html#L674)) nutzt `content.get_file_url()` — der GCS-aware Resolver im Model [models.py:463](../../app/models.py#L463). Benötigt `GOOGLE_API_KEY` oder `GOOGLE_TTS_API_KEY` in `.env`.

## 4. Lektions-Struktur (Zielbild) — erweitert 2026-04-24

Eine Lektion muss substantiell sein, damit Mayuko echten Lernwert hat. Zu dünn ⇒ zurückgeschickt. Jede generierte Lektion enthält **mindestens 5 Seiten**:

```
Lesson (title, description, jlpt_level→difficulty_level 1-5, instruction_language='german',
        lesson_type='free', is_published=False (erst nach Sichtung True),
        allow_guest_access=True für erste Lektion pro Thema,
        thumbnail_url=DALL-E-URL (Pflicht!))

├─ LessonPage 1: "Einführung" (page_type='normal')
│   └─ LessonContent: text — DE-Einleitung (4-8 Sätze, Plaintext!),
│      was lernst du, warum ist es im Alltag nützlich, typische Situation.
│
├─ LessonPage 2: "Vokabeln Teil 1" (page_type='normal')
│   └─ LessonContent: vocabulary ×8-12 — erste Hälfte der Wörter,
│      thematisch homogen. Jede Vokabel: word + reading + romaji + meaning_de +
│      example_sentence_japanese + example_sentence_english (mit Romaji-Prefix).
│      Mind. 1 dieser Vokabeln hat image_url (DALL-E).
│
├─ LessonPage 3: "Vokabeln Teil 2" (page_type='normal')
│   └─ LessonContent: vocabulary ×7-13 — zweite Hälfte.
│      Mind. 1-2 weitere image_urls.
│
├─ LessonPage 4: "Grammatik" (page_type='normal')
│   ├─ LessonContent: text — DE-Erklärung des Musters (Plaintext, mehrere Absätze).
│   └─ LessonContent: grammar ×2-4 — mit structure, romaji, 3-4 Beispielsätzen
│      je Eintrag (jeweils JP + Romaji + DE-Übersetzung).
│
├─ LessonPage 5: "Dialog / Konversation" (page_type='normal') — PFLICHT
│   └─ LessonContent: text — realistischer Mini-Dialog (6–10 Zeilen).
│      **KEIN Einleitungs-Absatz vor dem Dialog.** Der `content_text` beginnt
│      unmittelbar mit der ersten Sprecher-Zeile (`Tanaka: ...`), wie bei
│      MNN L1–L5 DE (Lessons 137–141). Szenario/Setting gehören in den
│      LessonContent.title (z.B. "Willkommensparty — Tanaka trifft Lisa"),
│      nicht in einen Prosa-Vorspann. Grund: `| nl2br` rendert nur Zeilen-
│      umbrüche — ein Prosa-Absatz vor dem Dialog lässt das Konversations-
│      Element visuell in einer Textwand verschwinden.
│      Format **exakt wie `_format_conversation()` in scripts/import_mnn.py:170**:
│         Speaker: 日本語テキスト
│           (romaji)
│           -> Deutsche Übersetzung       ← ASCII-Pfeil `->`, NICHT `→`
│         (Leerzeile)
│      **Format muss exakt dem MNN-DE-Standard entsprechen** (Lessons 137–141):
│      `_format_conversation()` in scripts/import_mnn.py:170 nutzt `->`, nicht
│      den Unicode-Pfeil. Templates rendern beide gleich via `| nl2br`, aber die
│      Konsistenz mit den bestehenden DE-Lektionen ist Pflicht.
│      Sprecher sind **eigene Namen** (nicht Miller/Satou aus MNN).
│      Wenn die Lektion thematisch einem MNN-Kapitel entspricht: Dialog-Struktur
│      orientiert sich an der MNN-`conversation`-Vorlage aus `scripts/mnn_data/`,
│      aber Text ist neu formuliert (andere Namen, leichte Variation). Siehe §2a.
│
├─ LessonPage 6: "Übung" (page_type='quiz_carousel')
│   └─ LessonContent mit QuizQuestions ×10-18 — Mix aus
│      multiple_choice / true_false / matching. Mind. 3 Typen, jeder Typ ≥2×.
│      Distraktoren aus derselben semantischen Domäne.
│
└─ LessonPage 7: "Zusammenfassung" (page_type='normal')
    └─ LessonContent: text — Review der Kern-Vokabeln/Grammatik,
       Lerntipps, konkreter Ausblick auf die nächste Lektion.
```

**Budget pro Lektion (hart validiert):**
- Vokabeln: **15–25** (vorher 8–12 war zu wenig).
- Grammatik: **2–4** (vorher 1–2 war zu dünn).
- Quiz: **10–18** (vorher 6–10 war zu wenig Übung).
- Pages: **≥5**.
- Thumbnail-Bild: **1** (Pflicht).
- Vokabel-Bilder: **ALLE Vokabeln** (nicht mehr nur 3 — angehoben 2026-04-24 nach
  Sichtung von MNN L1–L5 DE, wo ausnahmslos jede Vocabulary-Zeile ein `image_url`
  hat). Pipeline-Schritt `images` generiert per `AILessonContentGenerator.
  generate_vocabulary_image()` für jede Vokabel ohne `image_url` ein Icon und
  speichert es unter `app/static/uploads/vocab_generated/vocab_{id}_{hash}.png`.
  Bestehende Vokabeln mit `image_url` werden übersprungen (idempotent).

Die Lektion ist kein 5-Minuten-Happen, sondern eine 20–30-Minuten-Einheit.

## 5. Content-Qualität: Beispiel-Patterns

### Vocabulary-Eintrag (Claude schreibt)

```json
{
  "word": "家族",
  "reading": "かぞく",
  "romaji": "kazoku",
  "meaning": "family",
  "meaning_de": "Familie",
  "jlpt_level": 5,
  "example_sentence_japanese": "わたしの かぞくは よにんです。",
  "example_sentence_english": "Watashi no kazoku wa yo-nin desu. — My family has four people.",
  "image_url": null,
  "status": "approved",
  "created_by_ai": true
}
```

**Regeln:**
- `word` + `reading` + `romaji` + `meaning` + `meaning_de` sind alle Pflicht.
- `reading` in Hiragana (nie Katakana, ausser bei Lehnwörtern wie `メニュー`).
- `romaji` Hepburn-Transkription des ganzen Wortes, Kleinschreibung, Trennstriche bei zusammengesetzten Lesungen (`yo-nin`, `o-cha`).
- `example_sentence_japanese` nutzt Leerzeichen zwischen Wörtern bei N5 (Hiragana-Fokus).
- `example_sentence_english` **muss Format `"Romaji-Satz — English translation"` haben** — so liest Mayuko den Satz auch westlich, nicht nur Hiragana.
- Beispielsatz max ~12 Silben / ca. 8 Wörter.
- `image_url`: Bei Schlüsselvokabeln (≥3 pro Lektion) DALL-E-URL. Sonst null.

### Grammar-Eintrag

```json
{
  "title": "です / ist (Höflichkeitsform)",
  "explanation": "「です」 ist die höfliche Kopula und entspricht dem deutschen 'ist/sind'. Es steht am Satzende nach einem Nomen oder Na-Adjektiv und markiert einen Aussagesatz als formell.",
  "structure": "[Nomen] + です",
  "romaji": "[noun] + desu",
  "jlpt_level": 5,
  "example_sentences": "わたしは がくせいです。 (Watashi wa gakusei desu.) — Ich bin Student/in.\nこれは ほんです。 (Kore wa hon desu.) — Das ist ein Buch.",
  "status": "approved",
  "created_by_ai": true
}
```

**Regeln:**
- `explanation` auf Deutsch, 2-4 Sätze, konkret ohne Linguistik-Jargon
- `structure` kurz und in eckigen Klammern, z.B. `[Nomen] + です`
- `example_sentences` mit 2-3 Beispielen, jeweils Japanisch + Romaji + DE-Übersetzung

### Multiple-Choice-Frage

```json
{
  "question_type": "multiple_choice",
  "question_text": "Was bedeutet 家族 (かぞく)?",
  "difficulty_level": 1,
  "points": 1,
  "hint": "Es geht um Personen, die zusammenleben.",
  "explanation": "家族 (かぞく) heisst 'Familie'. Das erste Kanji 家 bedeutet 'Haus', das zweite 族 'Stamm/Gruppe'.",
  "options": [
    {"option_text": "Familie", "is_correct": true,  "feedback": "Richtig!"},
    {"option_text": "Schule",  "is_correct": false, "feedback": "Das wäre 学校 (がっこう)."},
    {"option_text": "Freund",  "is_correct": false, "feedback": "Das wäre 友達 (ともだち)."},
    {"option_text": "Arbeit",  "is_correct": false, "feedback": "Das wäre 仕事 (しごと)."}
  ]
}
```

**Regeln:**
- Genau 4 Optionen bei `multiple_choice`, davon genau 1 korrekt
- Distraktoren müssen plausibel sein (andere N5-Vokabeln, nicht offensichtlich falsch)
- `feedback` pro Option immer füllen — das ist Mayukos Lerneffekt bei Fehlern

### True-False-Frage

```json
{
  "question_type": "true_false",
  "question_text": "「ともだち」 bedeutet 'Bruder'.",
  "difficulty_level": 1,
  "explanation": "「ともだち」 heisst 'Freund'. 'Bruder' ist 「きょうだい」 (兄弟).",
  "options": [
    {"option_text": "Richtig", "is_correct": false, "feedback": "Ungenau: ともだち = Freund."},
    {"option_text": "Falsch",  "is_correct": true,  "feedback": "Korrekt — ともだち heisst Freund."}
  ]
}
```

### Matching-Frage

```json
{
  "question_type": "matching",
  "question_text": "Verbinde das japanische Wort mit der deutschen Übersetzung.",
  "difficulty_level": 2,
  "options": [
    {"option_text": "父 | Vater",     "is_correct": true},
    {"option_text": "母 | Mutter",    "is_correct": true},
    {"option_text": "姉 | ältere Schwester", "is_correct": true},
    {"option_text": "兄 | älterer Bruder",   "is_correct": true}
  ]
}
```

*Matching-Konvention in dieser Codebase:* `option_text` enthält Pair in Format `"[JP] | [DE]"`, alle Optionen sind `is_correct=true` (das Frontend shuffelt und verifiziert Paarung).

## 6. Pipeline-Ablauf

```
[1] Claude schreibt gesamten Lektions-JSON:
    .claude/skills/generate-lesson/drafts/{timestamp}_{topic}.json

[2] python .claude/skills/generate-lesson/pipeline.py validate {draft_path}
    → prüft Constraints (§3), Schema-Konformität, JLPT-Level-Konsistenz,
       HTML-Tag-Verbot in text-Content, Rōmaji-Pflicht, Thumbnail-Pflicht
    → Fehler = Abbruch mit detaillierter Liste

[3] python .claude/skills/generate-lesson/pipeline.py images {draft_path}
    → PFLICHT (nicht mehr optional). Ruft DALL-E für thumbnail +
       mind. 3 Schlüsselvokabel-Bilder. Ergänzt image_url/thumbnail_url
       im Draft. Bei fehlendem OPENAI_API_KEY: User fragen, NICHT weitermachen.

[4] python .claude/skills/generate-lesson/pipeline.py insert {draft_path}
    → Transaktionaler INSERT in Postgres (docker-compose DB)
    → Bei Fehler: Rollback, keine Teil-Lektion
    → Gibt lesson_id zurück

[4b] python .claude/skills/generate-lesson/pipeline.py audio {lesson_id}
    → PFLICHT nach Insert. Findet die Dialog-Page automatisch (per Titel:
       'Dialog' / 'Konversation' / 'Gespräch' / 'Conversation'), extrahiert
       die japanischen Sprecher-Zeilen aus dem text-Content, rendert EINE
       MP3 via Google Cloud TTS (SSML mit 700ms-Pausen) und legt einen
       LessonContent(content_type='audio') auf order_index=1 vor dem Text
       an. Idempotent: existierendes Audio wird übersprungen.
    → Benoetigt GOOGLE_API_KEY in .env.

[5] Verifikation — zwei Pfade, je nach Verfügbarkeit:

    [5a] Bevorzugt: python .claude/skills/generate-lesson/verify.py {lesson_id}
         → Playwright-Headless-Browser: Login als admin (email/password aus .env!),
           /lessons/{id} öffnen, alle Pages durchklicken, Quiz, Deck-Karussell-CSS-Check.
         → Screenshots in verifications/{lesson_id}/.

    [5b] Fallback, wenn MCP-Chrome besetzt ("Browser is already in use"):
         HTTP-basierte Verifikation via requests.Session:
         - POST /login mit email=ADMIN_EMAIL, password=ADMIN_PASSWORD aus .env (CSRF-Token vorher via GET).
         - GET /lessons/{id} → HTTP 200, Titel + Vokabeln + Grammatik + Umlaute im HTML.
         - GET /api/admin/lessons (JSON!) → Lesson muss in Liste sein.
           ACHTUNG: /admin/manage/lessons ist eine AJAX-Shell; die Titel
           werden client-seitig geladen und stehen NICHT im Server-HTML.
         - Dann: User bitten, /lessons/{id} visuell durchzuklicken (Deck-Karussell).

[6] Git-Commit (automatisch):
    git add .claude/skills/generate-lesson/generated-lessons.jsonl
            .claude/skills/generate-lesson/learnings.md
    git commit -m "Lektion generiert: {title} (JLPT N{n}, ID={lesson_id})"
    git push

[7] learnings.md anhängen:
    Was hat funktioniert? Was war überraschend? Was sollte beim nächsten
    Run anders laufen? (Siehe learnings.md für Format.)
```

**Wichtig:** Kein Schritt 6 ohne erfolgreichen Schritt 5. Bei Verifikations-Fail: Lektion wird als `is_published=False` markiert und User bekommt Issue-Report.

## 7. Bild-Generierung (Ausnahme: externe API)

DALL-E wird **nur** für:
- `Lesson.thumbnail_url` (1 Bild pro Lektion)
- `Vocabulary.image_url` (optional, maximal 3 Schlüssel-Vokabeln pro Lektion)

Prompts immer auf Englisch, Stil: `"minimalist flat illustration, soft pastels, no text, Japanese aesthetic"`. Kein Fotorealismus, kein Text im Bild, keine echten Personen.

Bilder werden in GCS hochgeladen via bestehende `gcs_utils.upload_file()`. Lokal-Mode (wenn `GCS_BUCKET_NAME` nicht gesetzt): Ablage in `app/static/uploads/generated/`.

## 8. Self-Improvement via learnings.md

Nach jedem Run anhängen (siehe [learnings.md](learnings.md) für Template):

```markdown
## 2026-04-20 12:30 — N5 Familie (Lesson ID 47)

### Erfolge
- 8 Vokabeln, Thema homogen, Difficulty einheitlich N5
- Matching-Frage mit 4 Familien-Paaren — Mayuko-testbar
- Beispielsätze nutzten ausschliesslich N5-Kanji ✓

### Probleme / Erkenntnisse
- Distraktor in Q3 war zu offensichtlich ("Auto" bei Familie-Frage) — **Regel für nächstes Mal: Distraktoren MÜSSEN aus derselben semantischen Domäne kommen**
- Grammar-Struktur-Feld enthielt JP-Text ohne Romaji — Frontend zeigt nur struktur, nicht romaji → **Regel: bei strukturbasiertes Grammar-Eintrag auch `romaji` immer füllen**
- Playwright fand Quiz-Carousel-CSS-Problem bei 5. Frage → CLAUDE.md-Regel "Deck-Karussell-CSS prüfen" wurde vergessen → **Pre-Flight-Check in Schritt [2] ergänzen**

### Aktuelle Regeln (Zusammenfassung nach diesem Run)
1. Distraktoren aus selber semantischer Domäne
2. Grammar.romaji immer füllen
3. Deck-Karussell CSS-Test als Validate-Step
```

**Regel-Evolution:** Wenn derselbe Fehler 2× in unterschiedlichen Runs auftritt → **in §3 (harte Constraints) oder §5 (Patterns) dieses Dokuments hochheben**, nicht nur in learnings.md stehen lassen.

## 9. Quellen-Referenzen

- **JLPT N5 Vokabel-Liste (offiziell):** [sources/jlpt-n5-vocab.md](sources/jlpt-n5-vocab.md) — 800 Kernwörter
- **Minna no Nihongo Rohdaten:** `scripts/mnn_data/beginner1_lesson01.json` … `beginner2_lesson50.json` — **50 Lektionen**, Schema `{source, lesson_number, title, jlpt_level, description, vocabulary[], vocabulary_countries[], grammar[{title, structure, jlpt_level, explanation, example_sentences}], conversation{title, lines[{speaker, japanese, romaji, english}]}, additional_conversations[]}`. Standard-Workflow: vor Schreiben einer Lektion MNN-JSON lesen, Vokabeln/Grammatik als thematischen Anker nutzen, eigenen Text + eigene Charaktere schreiben (siehe §2a).
- **MNN-Import-Referenz:** [scripts/import_mnn.py](../../scripts/import_mnn.py) zeigt, wie die 10 Bestandslektionen (IDs 131–141) strukturiert wurden — 5-Seiten-Layout (Vocab → Grammar → Konversation → Übung → Prüfung). Die `_format_conversation()`-Funktion ab Zeile 170 ist die Referenz für das Dialog-Plaintext-Format.
- **Bestehender DB-Content als Referenz:** SELECT in der DB zeigt, was schon da ist. Beispiel:
  ```sql
  SELECT word, reading, meaning_de, jlpt_level FROM vocabulary WHERE jlpt_level = 5;
  ```
- **Mayuko-Lackmustest:** [improve-jpl/SKILL.md §1](../improve-jpl/SKILL.md)

## 10. Technische Referenzen (für den Skill, nicht für Claude's Inhalt)

- DB-Modelle: `app/models.py` (Kana:127, Kanji:142, Vocabulary:162, Grammar:183, Lesson:218, LessonPage:409, LessonContent:423, QuizQuestion:522, QuizOption:542)
- **Verifikations-Endpoints:**
  - `/login` — POST-Felder: `email` (nicht username!) + `password` + `csrf_token`. Erfolg-Redirect für Admin: `/admin`.
  - `/lessons/{id}` — Detailseite (Server-Rendered, gut für Content-Checks).
  - `/api/admin/lessons` — **JSON**-Liste aller Lektionen (für Sichtbarkeits-Check).
  - `/admin/manage/lessons` — **AJAX-Shell**, Daten kommen client-seitig. HTML enthält KEINE Titel, für Verifikation UNGEEIGNET.
- Lokal-DB: `postgresql://app_user:JapaneseApp2025!@localhost:5432/japanese_learning`
- **Admin-Credentials** stehen in `.env` als `ADMIN_EMAIL` (z.B. `admin@example.com`) und `ADMIN_PASSWORD`. Verify-Scripts MÜSSEN diese via `dotenv` laden. Niemals hardcoden.
- **pg_isready-Check:** `docker exec postgres_db pg_isready -U app_user -d japanese_learning` ist der zuverlässigste Readiness-Check.
- **Windows-Shell-Encoding:** Python-Scripts, die japanische Zeichen (Hiragana/Katakana/Kanji) per `print()` ausgeben, brauchen `PYTHONIOENCODING=utf-8` als Env-Variable, sonst `UnicodeEncodeError: cp1252`. Beispiel: `PYTHONIOENCODING=utf-8 python script.py`. Alternativ beim Skript-Start: `sys.stdout.reconfigure(encoding='utf-8')`.
- Bestehende `AILessonContentGenerator` in `app/ai_services.py` — **NICHT NUTZEN** (User-Entscheidung: Claude schreibt selbst)

## 11. Deploy & Live-Schalten

Nach erfolgreicher Verifikation ist die Lektion in der **lokalen** DB. Für Production:

```bash
/sync-cloud-db   # zuerst Cloud→Lokal prüfen, dann Lokal→Cloud
```

**Nicht im Skill automatisiert** — Push auf Production bleibt explizite User-Aktion, damit Mayuko keine halb-fertige Lektion sieht.
