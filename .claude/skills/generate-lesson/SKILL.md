---
name: generate-lesson
description: Generiert eine vollständige Japanisch-Lektion (Lesson + LessonPages + LessonContent + QuizQuestions) für japanese-learning.ch. Claudio schreibt die Inhalte (Kana/Kanji/Vokabeln/Grammatik/Quiz) selbst — keine OpenAI/Gemini-API-Aufrufe ausser für Bilder (DALL-E). Auto-aktivieren, wenn Claudio "neue Lektion", "Lektion generieren", "Content für N5/N4", "Mayuko braucht eine Lektion über X", "erstelle eine Lektion zu Thema Y" sagt oder per `/generate-lesson` aufruft. Nutzt JLPT-Vokabellisten und Minna no Nihongo als Ausgangsquellen, schreibt direkt in die lokale Postgres-DB (docker-compose), verifiziert via Playwright, committet via Git.
---

# generate-lesson — Anfänger-Lektionen für japanese-learning.ch

## Auftrag

Erstelle eine **komplette, sofort nutzbare Lektion** für deutschsprachige Anfänger (inkl. Claudio selbst, der die Seite dogfoodet). **Du schreibst den gesamten Text-Content selbst** (keine OpenAI/Gemini-Calls). Der Skill ist der Orchestrator: Er gibt dir Schema, Guardrails und die Persistierungs-/Verifikations-/Git-Schritte vor; du produzierst den japanischen Content als strukturiertes JSON. Mayuko (Claudios Frau, japanische Lehrerin) prüft Inhalte fachlich — sie ist Reviewerin, nicht Lernerin. **Wichtig:** Mayuko wird intern als Fachreviewerin geführt, ist aber **öffentlich nicht erwähnt** (nicht auf der Website, nicht in Marketing-Texten, nicht in PR). Aktuell — kann sich später ändern.

**Einzige Ausnahme: Bilder.** Für `thumbnail_url` und `Vocabulary.image_url` kannst du DALL-E per Script aufrufen (siehe §7).

---

## 1. Start-Check (immer zuerst)

Bevor du überhaupt Content schreibst:

0. **Cloud-Sync-Status prüfen.** Liegt `.last_cloud_sync.json` vor und ist der `taken_at`-Timestamp <12h alt? Wenn nein (oder Datei fehlt): Empfehle dem User vor dem Generieren einen `/sync-cloud-db` Cloud→Lokal-Pull. Grund: Der spätere Push vergleicht den lokalen Stand gegen diesen Snapshot — ohne aktuellen Snapshot scheitert der Push am Drift-Check (seit Audit 2026-04-25). Wenn der User explizit ohne vorherigen Pull arbeiten will, OK — er weiss dann, dass beim Push ein Drift-Fehler kommen kann.
1. **Lies [learnings.md](learnings.md).** Dort steht, was in vorherigen Runs geklappt hat und was nicht. Wende diese Regeln strikt an.
2. **Lies [improve-jpl/SKILL.md](../improve-jpl/SKILL.md).** Die Produkt-Vision (Anfänger-First mit Mayuko-Fachreview, JLPT-Leitprinzip §1.5, Nicht-Ziele) gilt uneingeschränkt.
   - **Coverage prüfen** vor Themen-Wahl: `python .claude/skills/generate-lesson/pipeline.py coverage 5 --show-missing 30` zeigt fehlende N5-Vokabeln/Kanji. Themen so wählen, dass möglichst viele fehlende Items abgedeckt werden, statt schon vorhandene zu doppeln.
   - **Validator ist STRENG** (Mayuko-Direktive 2026-04-25): jedes Vokabel-Wort muss in `sources/jlpt_n5_canonical.json` stehen, sonst ERROR. Eigennamen: `data.is_proper_noun=true`. Bewusste Ausnahmen: `data.is_canonical_override=true` + `data.source_note="…"`. Kanji im `example_sentence_japanese` müssen im N5-Kanji-Set stehen — sonst Hiragana schreiben.
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
| `/generate-lesson Hiragana` / `Katakana` | **Schreibsystem-Lektion** — Draft mit `"kind": "kana"` statt Vocabulary/Grammar. Siehe §2b. |

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

## 2b. Schreibsystem-Lektionen (`kind: "kana"`) — Hiragana / Katakana

Hiragana- und Katakana-Lektionen sind eine **Sonderform**. Statt JLPT-Vokabeln und Grammatik wird das **Schriftsystem selbst** unterrichtet. Die Pipeline kennt dafür den Discriminator `"kind": "kana"` im Draft (Default ist `"vocabulary"`, kann weggelassen werden).

**Was anders ist als bei einer Vocabulary-Lektion:**

| Bereich | Vocabulary-Lektion (Default) | Kana-Lektion (`kind: "kana"`) |
|---|---|---|
| Lesson-`kind`-Feld | `"vocabulary"` (oder weglassen) | `"kana"` (Pflicht!) |
| Vokabel-Einträge | 15–25 Pflicht | **0 erlaubt** (Validator bricht ab) |
| Grammatik-Einträge | 2–4 Pflicht | **0 erlaubt** (Validator bricht ab) |
| Kana-Einträge | 0 (oder optional) | **5–20 Pflicht** |
| Quiz-Fragen | 10–18 | 8–16 |
| Pages | ≥5 | ≥4 |
| Dialog-Page | Pflicht | weggelassen (kein Konversationskontext) |
| Audio-Pipeline | Pflicht | **übersprungen** (keine Dialog-Page) |
| Slideshow-Pipeline | Pflicht | **übersprungen** |
| text-audio | Pflicht für Prosa-Pages | bleibt aktiv für Markdown-Pages |
| Vokabel-Bilder | jede Vokabel | **entfällt** (keine Vokabeln) |
| Thumbnail | Pflicht | Pflicht |
| N5-Canonical-Vokabel-Check | aktiv | übersprungen |
| N5-Kanji-Disziplin-Check | aktiv | übersprungen (Kana-Lektion enthält per Definition keine Kanji-Beispielsätze) |
| Romaji/Umlaut/Markdown-Hierarchie-Check | aktiv | bleibt aktiv |
| Modul-Zuweisung | passendes N5-Themen-Modul | `n5-hiragana` (id=30) bzw. `n5-katakana` (id=31) |

**Page-Struktur einer Kana-Lektion (Zielbild):**

```
Lesson (kind="kana", title="Hiragana 1 — …", jlpt_level=5,
        thumbnail_url=DALL-E-URL)

├─ LessonPage 1: "Einführung" (page_type='normal')
│   └─ LessonContent: text — Was ist Hiragana? Warum lernen? Wie liest man die
│      Tabelle? Markdown-Hierarchie Pflicht (## H2 + **bold** + Liste/Quote).
│
├─ LessonPage 2: "Die Zeichen" (page_type='normal')
│   └─ LessonContent: kana ×N — jede Zeile ein Kana-Element mit
│      character + romanization + type. Optional stroke_order_info /
│      example_sound_url.
│
├─ LessonPage 3: "Aussprache & Schreibhinweise" (page_type='normal')
│   └─ LessonContent: text — Wie spricht man die Vokale? Welche Reihen-
│      Strukturen wiederholen sich? Welche Häkchen unterscheiden は/ほ?
│      Markdown-Hierarchie Pflicht.
│
├─ LessonPage 4: "Übung" (page_type='quiz_carousel')
│   └─ LessonContent mit QuizQuestions ×8-16 — Mix aus
│      multiple_choice (Zeichen → Romaji) + matching (5 Paare Zeichen↔Romaji)
│      + true_false (z.B. "「く」 wird 'ku' gelesen.").
│
└─ LessonPage 5: "Zusammenfassung & nächste Schritte" (page_type='normal')
    └─ LessonContent: text — Wiederholung, Lerntipps, Vorschau auf nächste
       Hiragana-Lektion.
```

**Schema des `kana`-Content-Items im Draft:**

```json
{
  "content_type": "kana",
  "data": {
    "character": "あ",
    "romanization": "a",
    "type": "hiragana",
    "stroke_order_info": null,
    "example_sound_url": null
  }
}
```

**Pipeline-Schritte bei Kana-Lektion:**
1. `validate` — neuer Validator-Pfad (Vocab/Grammar verboten, kana-Budget aktiv).
2. `images` — generiert nur Thumbnail (keine Vokabel-Icons, weil keine Vokabeln).
3. `insert` — `_get_or_create_kana()` deduppt über `character` (UNIQUE-Constraint).
4. `audio` — überspringen (kein Dialog).
5. `text-audio` — laufen lassen für die Prosa-Markdown-Pages.
6. `slideshow` — überspringen.
7. Modul-Zuweisung: `category_id=30` für Hiragana, `31` für Katakana.

**Quiz-Distraktoren bei Kana:** ähnliche Zeichen wählen (ね/れ/わ/ぬ verwechselbar, さ/き/ち, シ/ツ, ソ/ン, etc.) — fördert echtes Lesen, nicht Raten.

**Bestandsschutz:** `Kana.character` ist UNIQUE. Wenn ein Zeichen bereits existiert (z.B. die initialen 10 Hiragana あ-こ in der DB), wird die bestehende ID wiederverwendet — kein Update auf bestehende Eintragsdaten (schützt manuelle Edits).

## 2c. Kanji-Lessons (eigenes Modul `n5-kanji-grundlagen`, seit 2026-04-27)

Kanji-Lessons sind Vocabulary-Lessons (`kind: "vocabulary"`, default), die didaktisch ein **Kanji-Set** in den Mittelpunkt stellen. Sie bekommen aber eine **eigene Modul-Heimat**: `n5-kanji-grundlagen` (id=38, display_order=3, icon=漢) zwischen Katakana (2) und Zahlen-Zeit (4).

**Warum eigenes Modul:**
- Pädagogische Hierarchie: Hiragana → Katakana → **Kanji-Grundlagen** → Themen (Familie, Reise, Alltag, etc.).
- Lerner findet alle Kanji-Karten an einer Stelle, nicht verstreut über Themen-Module.
- Mayuko-Direktive (JLPT-Leitprinzip): Schreibsystem zuerst komplett, dann Themen.

**Bestand 2026-04-27 — 8 Lessons im Modul:**
- 164: Kanji 1 — Zahlen 一-十 (order=1)
- 167: Kanji 2 — Tage und Wochentage 日月火水木金土 (order=2)
- 168: Kanji 3 — Menschen 人男女子友 (order=3)
- 169: Kanji 4 — Natur 山川木雨 (order=4)
- 170: Kanji 5 — Position 大小上下中右左 (order=5)
- 171: Kanji 6 — Familie 父母兄姉弟妹 (order=6)
- 172: Kanji 7 — Grosse Zahlen, Geld & Zeit 百千万円半年時分 (order=7)
- 173: Kanji 8 — Eigenschaften 新古高安長短多少早 (order=8)

**Page-Struktur einer Kanji-Lesson:**

Wie eine Vocabulary-Lesson, aber Vokabel-Pages enthalten **abwechselnd `kanji`- und `vocabulary`-Items**: erst die Kanji-Karte (mit On/Kun/Strichzahl/Bedeutung), dann eine oder mehrere Vokabeln, die das Kanji nutzen. Beispiel aus Lesson 171:

```json
{ "content_type": "kanji",
  "data": {
    "character": "父", "meaning": "Vater / father",
    "onyomi": "フ", "kunyomi": "ちち",
    "jlpt_level": 5, "stroke_count": 4, "radical": "父"
  } },
{ "content_type": "vocabulary",
  "data": { "word": "父", "reading": "ちち", "romaji": "chichi", ... } }
```

**Pipeline-Schritt `_get_or_create_kanji`** (in pipeline.py seit 2026-04-27): deduppt über `character` (UNIQUE), erstellt sonst neuen Kanji-Record mit On/Kun/Strichzahl/Radikal/JLPT/status='approved'/created_by_ai=True. Bestehende Records werden **nicht** überschrieben.

**Coverage-Backfill als schneller Hebel:** Bestehende Kanji-Lessons haben oft 0 Kanji-Items (nur Vocabulary mit Kanji-Word). Ein direkter SQL-INSERT in die `kanji`-Tabelle für die thematisch bereits abgedeckten Zeichen hebt die Coverage sprunghaft, ohne neue Lesson zu schreiben. Vor neuer Kanji-Lesson immer prüfen:
```sql
-- Welche Kanji existieren in der DB als Karteikarten?
SELECT character FROM kanji WHERE jlpt_level=5 ORDER BY character;
-- Welche Kanji werden in Lessons als Vocabulary-Word genutzt, fehlen aber als Kanji-Record?
```

**Modul-Zuweisung:** Nach `insert` IMMER `category_id=38`, nicht in Themen-Module einsortieren. Order-Index = max(order_index)+1 im Modul.

**Override für Kanji ausserhalb elzup-canonical:** Siehe §3 "Lesson-Level-Kanji-Override" — die canonical-Liste fehlt 兄/姉/弟/妹/新/古/安/短/多/少/早, daher `additional_n5_kanji` + Source-Note Pflicht.

## 3. Harte Constraints (Nicht-Verhandelbar)

Verletzung ⇒ sofortiger Abbruch, keine Insertion:

- **Quiz-Typen NUR**: `multiple_choice`, `true_false`, `matching`. **KEIN** `fill_blank` (siehe CLAUDE.md §"Quiz-System").
- **JLPT-Level NUR**: N5 oder N4. Kein N3/N2/N1 (siehe improve-jpl §"Nicht-Ziele").
- **Keine Umlaut-Fallbacks** in **allen** deutschen Texten (Einleitung, Grammar-Explanation, Quiz-Frage/Hint/Explanation/Feedback, Dialog-Übersetzung, Zusammenfassung, Lesson.description/title, LessonPage.title): **immer Ü/Ö/Ä/ß** (oder ss), **niemals UE/OE/AE/SS**. "Schüler" statt "Schueler", "höflich" statt "hoeflich", "Grüße" statt "Gruesse", "für" statt "fuer". UTF-8 durchgängig. Gilt auch in `content_text`, `hint`, `explanation`, `feedback`, `option_text` — überall, wo deutscher Fliesstext steht.
- **Rōmaji NEBEN JEDEM japanischen Zeichen, das der Lerner nicht automatisch lesen kann — überall, ausnahmslos.** Jedes Auftreten von Kanji/Hiragana/Katakana in einem Text-Feld bekommt in derselben Zeile Rōmaji in Klammern `(romaji)`. Folgende Felder sind alle betroffen:
  - **`LessonContent.content_text`** (Einleitung, Grammatik-Erklärung, Dialog, Zusammenfassung): jedes JP-Wort/Phrase mit Rōmaji in Klammern. Beispiel: `Dort begrüßt dich das Personal mit 「いらっしゃいませ」 (irasshaimase, 'Willkommen')`. In jedem Satz neu, nicht nur beim ersten Vorkommen.
  - **`Grammar.title`**: wenn der Titel JP-Zeichen enthält (`〜をください (höfliche Bitte)`), muss Rōmaji dabei sein → `〜をください (~ wo kudasai — höfliche Bitte)`.
  - **`Grammar.structure`**: wenn die Struktur JP-Zeichen enthält (`[Nomen] + を + ください`), muss direkt danach die Rōmaji-Variante stehen. Da das `structure`-Feld nur **einzelne Zeile** ist: Rōmaji in derselben Zeile in Klammern, z.B. `[Nomen] + を + ください  ([noun] + wo + kudasai)`. Zusätzlich bleibt das `Grammar.romaji`-Feld (wird separat gerendert). Beide redundant zu haben ist OK — das Template zeigt mal das eine, mal das andere, der Lerner sieht es so oder so.
  - **`Grammar.explanation`** (DE-Erklärung): jeder JP-Ausdruck in Klammern mit Rōmaji. `「を」 (wo, ausgesprochen 'o')` statt nur `「を」`.
  - **`Grammar.example_sentences`**: jeder JP-Satz JP-Zeile → Rōmaji-Zeile → DE-Zeile (dreizeilig).
  - **`Grammar.tts_example_jp` (PFLICHT seit 2026-04-30)**: genau EIN vollständiger JP-Satz, **rein japanisch** (kein Romaji, keine Übersetzung, keine Klammern mit lateinischer Schrift). Endet mit `。`, `！` oder `？`. Wird vom Audio-Button auf der Grammatik-Karte mit der ja-JP-Stimme vorgelesen — die `/api/tts`-Route lehnt deutschen Text mit lang=ja hart ab (HTTP 400). Beispiele: ✅ `わたしはマイク・ミラーです。` ❌ `Watashi wa Maiku Miraa desu.` ❌ `わたしは学生です。 (Watashi wa gakusei desu.)`. Pflicht-JLPT-Niveau identisch zu `example_sentences` — keine N4+-Kanji in N5-Lektionen.
  - **`QuizQuestion.question_text`, `.hint`, `.explanation`**: wenn JP-Zeichen darin stehen, Rōmaji in Klammern. `Was bedeutet 「水」 (mizu)?` statt `Was bedeutet 「水」?`.
  - **`QuizOption.option_text`, `.feedback`**: wenn JP darin steht, Rōmaji in Klammern. In Matching-Optionen `肉 (niku) | Fleisch` statt `肉 | Fleisch`.
  - **`Vocabulary.romaji`** (Datenbankfeld, eigene Spalte): Hepburn-Rōmaji des Wortes.
  - **`Vocabulary.example_sentence_english`** beginnt mit Rōmaji-Satz, Format `"Romaji — Deutsche Übersetzung"` (Em-Dash). Die Übersetzung steht auf der Karten-Rückseite unter dem japanischen Beispielsatz und ist explizit auf Deutsch (Plattform-Sprache). Englisch ist nur als Übergangs-Fallback erlaubt, wenn alte Daten noch nicht migriert sind.
  - **`Vocabulary.example_sentence_japanese`** bleibt rein JP — dort ist Rōmaji redundant, weil `reading` + `romaji` in derselben Vokabel-Karte stehen.
  - Ziel: Ein deutschsprachiger Anfänger (inkl. Claudio) kann **jeden Satz** überall in der Lektion westlich aussprechen, selbst wenn er ein Kanji nicht kennt.
- **Instruction-Language**: default `'german'` (deutschsprachige Anfänger sind die primäre Zielgruppe). Englisch nur auf explizite User-Anweisung.
- **Beispielsätze dürfen NUR Kanji/Vokabeln des eigenen oder eines niedrigeren JLPT-Levels enthalten.** N5-Lektion darf keine N3-Kanji im Beispielsatz haben. Wenn unvermeidbar: schreibe den Satz in Hiragana.
  - **Bekannte N5-Vokabel-Falle:** Viele „klassische" N5-Familien-Vokabeln (家族, 兄弟, 両親, 子供, 兄, 姉, 弟, 妹, お父さん, お母さん, お兄さん, お姉さん) enthalten Kanji, die NICHT im N5-Kanji-Set (80 Zeichen) stehen — 兄, 姉, 弟, 妹, 家, 族, 親, 供 sind alle erst N4. Validator wirft ERROR. Lösung: in `content_text`, `Grammar.example_sentences` und `LessonContent.text` nur die Hiragana-Variante schreiben (かぞく, きょうだい, りょうしん, あに, あね, おとうと, いもうと, おとうさん, おかあさん, …). Im `Vocabulary.word`-Feld bleibt die Kanji-Form (das ist die Karteikarte selbst). Im N5-Kanji-Set sind aus Familie nur: 人, 子, 女, 男, 父, 母, 友. Auch andere N5-Vokabeln können solche „N4-Kanji-N5-Vokabeln" sein — bei Validator-Hinweis stets Hiragana wählen.
- **`created_by_ai = True`** für alle generierten Kana/Kanji/Vocabulary/Grammar-Einträge. `LessonContent.generated_by_ai = True` ebenfalls.
- **`status = 'approved'`** direkt (User-Entscheidung 2026-04-20).
- **Duplicate-Check**: Vor jedem INSERT in Kana/Kanji/Vocabulary/Grammar prüfen ob `character`/`word`/`title` schon existiert → bestehende ID wiederverwenden, NICHT neue Zeile erzeugen.
- **Markdown JA — KEIN roher HTML in `content_text`** (content_type `text`). Seit 2026-04-25 rendert das Template [lesson_view.html:683/916](../../app/templates/lesson_view.html#L683) mit dem `| markdown_safe`-Filter ([app/__init__.py](../../app/__init__.py)) — Markdown wird zu Bleach-gesäubertem HTML. **Pflicht: visuelle Hierarchie pro Text-Page**, sonst sehen alle Sektionen gleich aus.
  - **Erlaubte Markdown-Bausteine:** `## Headline H2` (Sektions-Titel), `### Headline H3` (Unter-Sektion), `**fett**` (Schlüsselwörter und JP-Begriffe wie `**「ちち」 (chichi)**`), `*kursiv*` (Romaji-Hinweise), `- Liste` und `1. Liste`, `> Blockquote` (Merksatz/Beispiel), `` `code` `` (Strukturen wie `` `[Nomen] + です` ``), `---` (Trennlinie zwischen 2 Themenblöcken), `[Linktext](https://…)`.
  - **Pflicht-Mindestformatierung pro `content_text`-Block:** mind. **1× H2 oder H3** (Sektionstitel) + mind. **2× `**bold**`** für Schlüsselbegriffe + mind. **1× Liste oder Blockquote**, wenn Absatz Aufzählung/Merksatz enthält. Reine Prosa ohne Hervorhebung ist verboten — sieht "alles gleich" aus (User-Feedback 2026-04-25).
  - **NICHT erlaubt:** roher HTML (`<p>`, `<div>`, `<style>`, `<script>`, `onclick=`). Bleach strippt diese — verschwendete Zeichen.
  - **Absätze trennen:** Leerzeile (`\n\n`) wie bisher.
  - Das `| markdown_safe`-Rendering nutzt die `nl2br`-Markdown-Extension, also bleiben einfache Zeilenumbrüche im Dialog-Text-Block erhalten (Konversation rendert wie zuvor).
- **Rōmaji ist PFLICHT** — an vier Stellen:
  1. `Vocabulary.romaji` (neue Spalte seit Migration `a3f5c2d1b8e9`): Hepburn-Transkription des Wortes, z.B. `word="家族", reading="かぞく", romaji="kazoku"`.
  2. `Grammar.romaji` (bestand schon): Struktur in Rōmaji, z.B. `"[noun] + wo + kudasai"`.
  3. `example_sentence_english`: muss mit Rōmaji-Version des Satzes beginnen, Format `"Romaji — English meaning"`, z.B. `"Watashi no kazoku wa yo-nin desu. — My family has four people."`. So sieht der Lerner in JEDER Darstellung die westliche Lesung.
  4. **Quiz-Texte (seit 2026-04-28)** — `quiz_question.question_text` UND `quiz_option.option_text`: Wenn der String japanische Schrift enthaelt, MUSS er Romaji in Klammern fuehren. Pattern: `JP-Text (romaji)` oder `漢字 (kana, romaji)`. Beispiele:
     - ✅ `バスで がっこうに 行きます。 (Basu de gakkou ni ikimasu.)`
     - ✅ `公園 (こうえん, kouen)`
     - ❌ `バスで がっこうに 行きます。` ← Validator schlaegt fehl
     - Ausnahme: 1-2-Zeichen Kana-only Optionen (z.B. `「は」`, `「が」` bei Partikel-Quizzes) brauchen kein Romaji, sie sind selbsterklaerend.
     - Backfill fuer bestehende Lessons: `python scripts/backfill_quiz_romaji.py --jlpt 5 --apply` (idempotent, nutzt pykakasi). Validator (`_needs_romaji_in_quiz` in `pipeline.py`) prueft das automatisch beim `pipeline.py validate`-Schritt.
- **Bilder sind PFLICHT** — `thumbnail_url` muss vor Insert gesetzt sein. Pipeline-Schritt `images` (DALL-E) läuft vor `insert`, NICHT optional. Zusätzlich: **jede Vokabel** muss `image_url` haben (MNN-DE-Standard, siehe §4-Budget). **Auch jedes Kanji** muss `image_url` haben — sonst bleibt die Karten-Rückseite leer (Bug-Klasse 2026-04-28: Kanji-Lessons 171-173 hatten 23 Kanji ohne Bild). Generierungs-Script: `python .claude/skills/generate-lesson/scripts/gen_kanji_images.py --jlpt 5` (idempotent, ueberspringt bestehende). Ablage: `app/static/uploads/kanji_generated/kanji_{id}_{hash}.png`.
- **`Vocabulary.image_url` und `Kanji.image_url` muessen relativ zu `UPLOAD_FOLDER` sein** (= `app/static/uploads/`), NICHT absolut. Das Template [lesson_view.html:859](../../app/templates/lesson_view.html#L859) ruft `url_for('routes.uploaded_file', filename=content_data.image_url)` auf — die Route [routes.py:3973 `/uploads/<path:filename>`](../../app/routes.py#L3973) dient aus `UPLOAD_FOLDER`. Richtige Werte: `vocab_generated/vocab_abc.png`, `kanji_generated/kanji_42_8f3a.png`, `vocabulary/images/vocab_124.png`. **Falsch**: `/static/uploads/vocab_generated/…`, `http://…`, `static/uploads/…`.
- **Audio für die Konversation ist PFLICHT** — jede Dialog-Page bekommt ein eigenes `LessonContent(content_type='audio')` **vor** dem Dialog-Text (`order_index=1`, Text auf `order_index=2`). Der Pipeline-Schritt `audio {lesson_id}` rendert via Google Cloud TTS (Neural2-B, langsam=0.85) eine einzige MP3 mit allen japanischen Sprecher-Zeilen, 700ms-Pausen dazwischen. Speicherort: `app/static/uploads/lessons/audio/lesson_{id}/conversation.mp3`. Felder im LessonContent: `file_path="lessons/audio/lesson_{id}/conversation.mp3"` (relativ zu `UPLOAD_FOLDER`!), `file_type="audio/mpeg"`, `title="Konversation (Audio)"`. Das Template ([lesson_view.html:674](../../app/templates/lesson_view.html#L674)) nutzt `content.get_file_url()` — der GCS-aware Resolver im Model [models.py:463](../../app/models.py#L463). Benötigt `GOOGLE_API_KEY` oder `GOOGLE_TTS_API_KEY` in `.env`.
- **JSON-Quoten-Disziplin im Draft** (Bug 2026-04-26 Lesson 160): NIE deutsche Anführungszeichen `„X"` in Draft-JSON-Strings verwenden. Das Schliesszeichen `"` ist ASCII-`"` und bricht den JSON-Parse mit `Expecting ',' delimiter`. Erlaubte Quoten innerhalb eines JSON-Strings: einfache `'...'`, spitze `«...»`, oder Kana-Eckklammern `「...」` (preferred fuer JP-Zitate). Beispiel-Fix: `"Tanaka sagt: „Yamada"."` → `"Tanaka sagt: 'Yamada'."` oder `"Tanaka sagt: 「Yamada」."`. Validator-Aufruf bricht mit Stack-Trace ab — Zeilennummer im JSONDecodeError nutzen, um die problematische Stelle zu finden.
- **Asset-Pfade NIE mit `/static/uploads/` praefixen** (Bug 2026-04-26): `media_url`, `file_path` und `slide.image`/`slide.audio` in dialog_slideshow-JSON immer mit Prefix `/uploads/` (= uploaded_file-Route) oder ganz ohne Prefix (relativer Pfad, Template loest via `get_file_url()`). `/static/uploads/` funktioniert lokal aber bricht live, weil Cloud Run den Container ohne die generierten Assets ausliefert — kein 302-Fallback wie bei `/uploads/`. Skripte `gen_text_audio.py`, `gen_conversation_audio.py`, `gen_dialog_slideshow.py` sind 2026-04-26 fix; bei neuen Skripten beachten.
- **Lesson-Level-Kanji-Override `additional_n5_kanji`** (seit 2026-04-27): Die canonical-Liste in `sources/jlpt_n5_canonical.json` (von elzup, MIT) hat 80 Kanji, weicht aber an mehreren Stellen vom Tanos/Wikipedia/Anki-N5-Standard ab. **Fehlt in elzup, ist aber Standard-N5:** 兄, 姉, 弟, 妹 (Geschwister), 新, 古, 安, 短, 多, 少, 早 (i-Adjektive). Wenn eine Kanji-Lesson explizit eines dieser Zeichen lehrt, MUSS sie auf Lesson-Header-Ebene zwei Felder setzen:
  ```json
  "additional_n5_kanji": ["兄", "姉", "弟", "妹"],
  "additional_n5_kanji_source_note": "In Tanos-N5 und allen Anki-N5-Decks Standard, in elzup nicht. ..."
  ```
  Der Validator (`pipeline.py` ab Zeile 355) addiert die Liste zum N5-Kanji-Set für die Beispielsatz-Prüfung. Pflicht: ohne `additional_n5_kanji_source_note` schlägt der Validator fehl. **Vor Verwendung prüfen, ob das Kanji wirklich nicht in canonical ist:**
  ```bash
  PYTHONIOENCODING=utf-8 python -c "import json; canon=json.load(open('.claude/skills/generate-lesson/sources/jlpt_n5_canonical.json')); print('兄' in [k['char'] for k in canon['kanji']])"
  ```
  Override-Kanji zaehlen NICHT in der `pipeline.py coverage`-Metrik (die misst gegen canonical), sind aber als Karteikarten in der DB vorhanden und didaktisch korrekt.

## 4. Lektions-Struktur (Zielbild) — erweitert 2026-04-24

Eine Lektion muss substantiell sein, damit der Lerner echten Lernwert hat (und Mayuko sie als Lehrerin guten Gewissens freigibt). Zu dünn ⇒ zurückgeschickt. Jede generierte Lektion enthält **mindestens 5 Seiten**:

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
│   ├─ LessonContent: text — realistischer Mini-Dialog (6–10 Zeilen).
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
│   └─ LessonContent mit QuizQuestions ×3-5 — **Verständnisfragen zum Dialog**
│      (PFLICHT seit 2026-04-25, User-Direktive). Direkt nach dem Dialog-Text
│      auf derselben Page als zweites LessonContent. Page-Type bleibt 'normal',
│      aber das zweite Element ist ein interaktives Quiz. Fragen prüfen
│      Hörverständnis: Wer sagt was, wo passiert es, was ist die Antwort von X?
│      Mix aus multiple_choice + true_false. Mind. eine Frage pro 2 Dialog-
│      Zeilen. Distraktoren aus dem Dialog selbst (z.B. andere Person/Ort/Zahl).
│      Diese Verständnisfragen zählen MIT in den 10-18-Quiz-Budget der Lektion;
│      die Übung-Page (Page 6) bleibt das Haupt-Quiz mit dem Rest.
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
- `word` + `reading` + `romaji` + `meaning` + `meaning_de` + `example_sentence_japanese` sind alle Pflicht.
- `reading` in Hiragana (nie Katakana, ausser bei Lehnwörtern wie `メニュー`).
- `romaji` Hepburn-Transkription des ganzen Wortes, Kleinschreibung, Trennstriche bei zusammengesetzten Lesungen (`yo-nin`, `o-cha`).
- `example_sentence_japanese` ist **PFLICHT-Feld** (analog `Grammar.tts_example_jp`): genau EIN japanischer Satz, der vom Audio-Button auf der Karte mit der ja-JP-Stimme vorgelesen wird. **Validator lehnt ab**, wenn der Satz lateinische Buchstaben enthält oder nicht mit `。`/`！`/`？` endet. Klammer-Romaji am Satzende (`(watashi wa ... desu.)`) ist daher verboten — die `reading`-/`romaji`-Felder der Vokabel decken den Romaji-Bedarf bereits ab.
- `example_sentence_japanese` nutzt Leerzeichen zwischen Wörtern bei N5 (Hiragana-Fokus).
- `example_sentence_english` **muss Format `"Romaji-Satz — Deutsche Übersetzung"` haben** (Em-Dash ` — `). Plattform-Sprache ist Deutsch; die Karten-Rückseite zerlegt diesen String in zwei Zeilen (Romaji-Zeile + Deutsch-Zeile) und zeigt sie unter dem JP-Beispielsatz, der vom Audio-Button vorgelesen wird.
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
- `feedback` pro Option immer füllen — das ist der Lerneffekt für den Anfänger bei Fehlern

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
    {"option_text": "父 (chichi)",  "feedback": "Vater",              "is_correct": true},
    {"option_text": "母 (haha)",    "feedback": "Mutter",             "is_correct": true},
    {"option_text": "姉 (ane)",     "feedback": "ältere Schwester",   "is_correct": true},
    {"option_text": "兄 (ani)",     "feedback": "älterer Bruder",     "is_correct": true}
  ]
}
```

*Matching-Konvention in dieser Codebase* (exakt wie Template [lesson_view.html:744-752](../../app/templates/lesson_view.html#L744) erwartet):
- **`option_text` = linke Seite** (Prompt, z.B. das japanische Wort mit Rōmaji in Klammern — NICHT mit `|`-Trenner).
  - **Romaji-Pflicht im linken Prompt**: jede `option_text`-Zelle, die JP-Zeichen enthält, MUSS Romaji in Klammern haben — auch bei Zahlen-Zählern wie `一人 (hitori)`, `何人 (nan-nin)`. Sonst kann der Anfänger den Prompt nicht lesen, der Dropdown-Match ist Glücksspiel. (Lesson 144 Z.3513-Bug 2026-04-25.)
- **`feedback` = rechte Seite** (die Antwort, die im Dropdown auswählbar erscheint, z.B. die deutsche Übersetzung).
- **`is_correct = true` für alle Optionen** — das Frontend shuffelt die `feedback`-Werte und der User muss jeden `option_text` dem richtigen `feedback`-Wert zuordnen.

**Achtung — häufiger Fehler:** Ein Format wie `option_text="JP | DE"` mit leerem `feedback` führt dazu, dass das Dropdown nur „None" anzeigt. Immer gesplittet speichern.

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

[3a] python .claude/skills/generate-lesson/scripts/gen_kanji_images.py --jlpt 5
    → PFLICHT bei Kanji-Lessons. Generiert Backside-Bilder fuer alle Kanji
       in der DB ohne `image_url`, die in mind. einer Lesson referenziert
       werden. Idempotent (skipped bestehende). Speichert nach
       `app/static/uploads/kanji_generated/`. Ohne diesen Schritt bleibt
       die Karten-Rueckseite leer (Bug 2026-04-28).
    ⚠️ **DALL-E Safety-Filter False-Positives** (Lesson 145, 食べる):
       Vereinzelte Vokabeln (vor allem Verben mit körperlichem Bezug wie
       essen/schlafen/baden) werden vom DALL-E-Filter als "self-harm" o.ä.
       missdeutet (`safety_violations=[self-harm]`, HTTP 400). Pipeline
       laeuft trotzdem weiter und ueberspringt nur dieses eine Bild.
       Workaround nach Pipeline-Ende: `image_url` der betroffenen Vokabel
       manuell mit objekt-fokussiertem Prompt nachgenerieren (z.B. "a bowl
       of warm rice with chopsticks held above it, no people"), Datei in
       `app/static/uploads/vocab_generated/vocab_<hash>.png` speichern und
       im Draft-JSON setzen. Lektion ist mit 19/20 Bildern noch nutzbar.

[4] python .claude/skills/generate-lesson/pipeline.py insert {draft_path}
    → Transaktionaler INSERT in Postgres (docker-compose DB)
    → Bei Fehler: Rollback, keine Teil-Lektion
    → Gibt lesson_id zurück
    → Unterstuetzte content_types: kana, vocabulary, kanji, grammar, text,
       audio, image, video. Insert deduppt via _get_or_create_kana /
       _get_or_create_vocab / _get_or_create_kanji / _get_or_create_grammar
       (alle in pipeline.py) — bestehende Records werden per UNIQUE-Constraint
       (character/word/title) wiederverwendet, NICHT ueberschrieben.

[4b] python .claude/skills/generate-lesson/pipeline.py audio {lesson_id}
    → ⛔ DEPRECATED seit 2026-04-30. Step ist No-Op und legt KEIN
       LessonContent(content_type='audio') mehr an. Begruendung: der
       dialog_slideshow-Player (Step [4c]) hat pro Zeile einen eigenen
       <audio>-Tag — ein zusaetzliches "Konversation (Audio)"-Item rendert
       redundant ueber der Slideshow (User-Direktive 2026-04-30, Lesson 157).
    → Step kann uebersprungen werden. Skript existiert noch, gibt nur eine
       Deprecated-Meldung aus und beendet sich mit exit 0 ohne DB-Insert.
    → ALT-Bestand: Bestehende Lektionen mit redundantem audio-Item werden
       vom Template (lesson_view.html ~Z.1078) automatisch unterdrueckt,
       wenn auf derselben Page ein dialog_slideshow vorhanden ist. DB-Cleanup
       optional, nicht zwingend.

[4b2] python .claude/skills/generate-lesson/pipeline.py text-audio {lesson_id}
    → PFLICHT seit 2026-04-25 fuer jede Lesson mit text-Bloecken >=80 Zeichen.
       Rendert pro `LessonContent.text` eine MP3 (Google Cloud TTS, DE+JA
       gemischt, Sprach-Splitter):
       - JA-Segmente (Hira/Kata/Kanji)  → ja-JP-Neural2-B (weiblich)
       - DE-Segmente (Lateinschrift)    → de-DE-Neural2-G (weiblich)
       ⚠️ **Voice-Namen NIE raten** — Google liefert silently eine Default-
       Voice wenn der `name` nicht existiert (z.B. de-DE-Neural2-F existiert
       nicht, F ist en-US). Vor jedem neuen Voice-Namen:
       `curl 'https://texttospeech.googleapis.com/v1/voices?languageCode=de-DE&key=$GOOGLE_API_KEY'`
       und Existenz prüfen, sonst geistert silent eine andere Stimme rein.
       Markdown wird vor TTS gestrippt: `**bold**`, `## H2`, Listen, `> quote`,
       `code`, `(romaji)` direkt nach JP-Zeichen — Ohren brauchen sie nicht.
       Skip-Heuristik: Dialog-Bloecke (Speaker-Format) werden uebersprungen
       (sind durch `audio` + `slideshow` schon abgedeckt). Idempotent ueber
       SHA1-Hash des content_text in `ai_generation_details.text_hash`.
       MP3-Pfad: `app/static/uploads/lessons/text_audio/lesson_{id}/page_{n}_content_{cid}.mp3`
       (geschrieben in `LessonContent.media_url` + `file_path` + `file_size`).
       Das Template ([lesson_view.html:683/918](../../app/templates/lesson_view.html#L683))
       rendert oberhalb des `rich-text-content` einen `<audio controls>`-Player
       mit Label "🔊 Vorlesen — Deutsch + Japanisch (separate Stimmen)".
       Optionen: `--page N` (nur eine Page rendern), `--force` (existierende
       MP3s neu erzeugen).
       Begruendung (User-Direktive 2026-04-25): Vorher las eine ja-JP-Stimme
       den ganzen Text inkl. Deutsch — klang akzentbehaftet. Splitter loest das.
       Kosten: ~1 Rappen pro Lektion (4 Pages * ~5000 Zeichen Google TTS).
       Dauer: ~30 s pro Lektion (sequenzielle Segment-Calls).

       ⚠️ TEMPLATE-FALLE 2 (lesson_view.html ~Z.683 + Z.918):
       (a) Der Audio-Player hat `<audio src="/static/uploads/...">`. Das CSS
           [.content-item:has(img[src*="uploads"])](app/static/css/custom.css)
           triggert text-align:center wenn der Selector `[src*=...]` zu breit
           ist (audio-Tags matchen auch). Pflicht-Selector: `:has(img[src*=...])`.
           Plus expliziter override:
             .text-audio-player { text-align: left !important; }
             .content-item:has(.text-audio-player) .rich-text-content { text-align: left !important; }
       (b) `MultilingualTextAudioSystem` (lesson_view.html ~Z.2134) macht jeden
           `<p>` in `.rich-text-content` klickbar und ruft `/api/tts` (ja-JP-
           Voice) für den GANZEN Text auf — DE wird mit ja-Voice gesprochen
           ("rassistischer Akzent"-Bug 2026-04-25). `processAllContent` MUSS
           `.rich-text-content`-Elemente skippen, deren Container bereits einen
           `.text-audio-player` enthalten. `.details` (Vocab/Kanji-Karten,
           JP-only) bleiben klickbar. Bei Template-/JS-Aenderungen NIE den
           Skip-Check entfernen.

[4b3] **order_index-Kollision auf Dialog-Page pruefen** (PFLICHT seit 2026-04-25
    nach Lesson 145):
    Nach `insert` nummeriert Pipeline alle Items der Dialog-Page ab `order_index=1`
    (Dialog-Text + Verstaendnis-Intro auf Page 5 -> beide bekommen 1+2). Dann
    setzt `audio` einen LC mit `order_index=1`, `slideshow` einen mit
    `order_index=2`, ohne die bestehenden zu verschieben. Resultat: 4 LCs mit
    oi-Werten 1/1/1/2 -> DB sortiert nicht-deterministisch -> Frontend rendert
    in zufaelliger Reihenfolge (z.B. Verstaendnisfragen vor Dialog-Text).
    Pflicht-Check + Korrektur:
       SELECT id, content_type, order_index, title FROM lesson_content
       WHERE lesson_id=<X> AND page_number=<dialog_page_n> ORDER BY order_index, id;
    Soll-Reihenfolge auf der Dialog-Page:
       audio=1, dialog_slideshow=2, text(dialog)=3, text(verstaendnisfragen)=4
    Korrigieren mit `UPDATE lesson_content SET order_index=N WHERE id=X;`.
    (TODO Skill-Verbesserung: `audio`/`slideshow` sollten bestehende LCs
    automatisch verschieben statt zu ueberschreiben.)

[4c] python .claude/skills/generate-lesson/pipeline.py slideshow {lesson_id}
    → PFLICHT nach audio. Baut pro Dialog-Zeile ein Slide mit:
       - 1 MP3 (Google TTS, Gender-korrekte Voice aus SPEAKER_GENDER)
       - 1 PNG (OpenAI gpt-image-1-mini, Ghibli-Aquarell-Stil, quality='hd',
         STRIKT ohne Text/Kanji/Ziffern — Charakter-Schablone bleibt konstant
         ueber alle Slides).
       Legt LessonContent(content_type='dialog_slideshow') auf order_index=2
       an (audio=1, slideshow=2, text=3). Das Template in lesson_view.html
       (~Zeile 945) rendert einen Alpine.js-Slideshow-Player mit Auto-Advance.
       Idempotent: existierende Zeilen-Assets werden uebersprungen, bestehender
       dialog_slideshow-Eintrag wird aktualisiert.
       Assets unter app/static/uploads/lessons/dialog_slideshow/lesson_{id}/.
       Charaktere werden in scripts/gen_dialog_slideshow.py CHARACTER_SHEETS
       gepflegt — neue Charaktere dort hinzufuegen, sonst generisches
       Portrait-Fallback.
       Kosten: ~50 Rappen pro Lektion (9 HD-Bilder + 9 TTS-Calls).
       Generierung dauert ~5 min (synchron, sequenzielle DALL-E-Calls).
       Bei Background-Run: TaskOutput mit timeout >= 300000ms verwenden.

       ⚠️ SPEAKER-GENDER-FALLE (Bug 2026-04-30, Lesson 174 + 176):
       `gen_dialog_slideshow.py` weist Stimmen via `SPEAKER_GENDER`-Dict
       in `scripts/generate_tts_audio.py` zu. Der Speaker-Name aus dem
       Dialog (z.B. `Lisa:`, `リサ:`, `Mama:`) MUSS dort als Key existieren,
       sonst greift ein **idx-basierter Fallback** (`idx % 2 == 0 ? female
       : male`) — das fuehrt bei Frauen mit ungeraden idx zu einer
       MAENNLICHEN Stimme. Symptom: Lisas/Mamas Dialog-Zeile klingt
       maennlich. Pflicht-Vorlauf vor jeder neuen Lektion mit
       Slideshow:
         a) **Speaker-Namen im Dialog konsistent** halten — entweder
            durchgaengig **Latein** (`Lisa:`, `Yamada:`) ODER konsistent
            **Katakana** (`リサ:`, `ヤマダ:`). Nicht mischen.
         b) **Vor Generierung pruefen:** ist der gewaehlte Speaker-Name
            in `scripts/generate_tts_audio.py::SPEAKER_GENDER`? Wenn nein,
            dort eintragen (mit korrektem Gender) und committen, BEVOR
            du `pipeline.py slideshow {id}` aufrufst.
         c) **Nach Generierung verifizieren:** SELECT der dialog_slideshow-
            JSON, jede Zeile hat `voice` — Mapping pruefen
            (Neural2-B + Wavenet-C = female, Neural2-D + Wavenet-D = male).
       Fix bei falsch generierter Slideshow: SPEAKER_GENDER ergaenzen,
       falsch gerenderte MP3s loeschen
       (`rm app/static/uploads/lessons/dialog_slideshow/lesson_{id}/line_NN.mp3`),
       dann `python .claude/skills/generate-lesson/scripts/gen_dialog_slideshow.py {id}`
       erneut. Dann Asset-Sync GCS + ggf. Deploy.

       ⚠️ TEMPLATE-FALLE (lesson_view.html ~Z.945-961): Die Slides MUESSEN
       per CSS-Grid-Stacking gerendert werden, sonst doppeltes Bild waehrend
       der x-transition.opacity. Pflicht-Pattern:
         <div class="slideshow-stage ..." style="...display:grid;">
           <template x-for="(slide, idx) in slides" :key="idx">
             <div class="slideshow-slide" style="grid-area:1/1;"
                  x-show="idx === current"
                  x-transition.opacity.duration.400ms>...</div>
           </template>
         </div>
       Ohne `display:grid` + `grid-area:1/1` stapeln sich Slides waehrend des
       400ms-Crossfades vertikal (alte fadet aus, neue fadet ein, beide
       gleichzeitig im Block-Flow). Bei Template-Aenderungen NIE entfernen.

[4d] Modul-Zuweisung (PFLICHT vor Verifikation):
    Nach Insert ist die Lesson noch keinem JLPT-Modul zugeordnet (`lesson.category_id` ist möglicherweise NULL).
    Den N5-Modul ermitteln, der thematisch passt (Tabelle `lesson_category`,
    Slugs wie `n5-familie-personen`, `n5-zahlen-zeit`, `n5-alltag-essen`,
    `n5-reise-ort`, `n5-erste-saetze`, `n5-begruessung-hoeflichkeit`,
    `n5-hiragana`, `n5-katakana`):
       SELECT id FROM lesson_category WHERE slug='n5-familie-personen';
    Dann zuweisen + publishen:
       UPDATE lesson SET category_id=<modul_id>, order_index=<n>, is_published=true WHERE id=<lesson_id>;
    Spalte heisst **`order_index`** (NICHT `order_in_module` — gibt es nicht).
    Für `order_index`: kleinste freie Zahl im Modul wählen (siehe MNN-Bestand).

[5] Verifikation — drei Pfade, je nach Verfügbarkeit:

    [5a] Bevorzugt (User-Wunsch 2026-04-25): Playwright MCP direkt aus dieser Conversation.
         - Lokalen Flask-Server prüfen (curl http://localhost:5000/ → 200).
         - Bei MCP-Chrome admin-bereits-eingeloggt nicht erneut /login aufrufen,
           direkt zu /lessons/{id}.
         - Sidebar-Pages haben `data-page` als 0-basierten Index — Page 5 = `data-page="4"`.
           Sidebar-Klicks via document.querySelector('.sidebar-page-item[data-page="N"]').click().
         - Screenshots: lesson{id}_pageN_*.png — fullPage:true für vollständigen Check.
         - Slideshow-Test: button[aria-label="Naechste Zeile"] klicken, Counter "X / 9" prüfen.
         - Console-Log: keine Errors, [Deck] Found N carousel pages, deckCheck > 0.

    [5b] Alt-Pfad: python .claude/skills/generate-lesson/verify.py {lesson_id}
         → Headless-Playwright. Screenshots in verifications/{lesson_id}/.

    [5c] Fallback, wenn beide Browser-Pfade scheitern: HTTP via requests.Session:
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
- **Anfänger-First mit Mayuko-Fachreview + JLPT-Leitprinzip:** [improve-jpl/SKILL.md §1 und §1.5](../improve-jpl/SKILL.md)

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
- **Coverage-Backfill als Hebel** (Lesson Learned 2026-04-27): Bestehende Kanji-Lessons (164/167-170 vor 2026-04-27) hatten 0 Kanji-Items in der `kanji`-Tabelle, obwohl die Zeichen thematisch in den Vocabulary-Words abgedeckt waren. Direkter SQL-INSERT in `kanji` mit On/Kun/Strichzahl ist der schnellste Coverage-Hebel — keine neue Lesson noetig. Vor jeder neuen Kanji-Lesson pruefen:
  ```sql
  -- Welche N5-Kanji existieren als Karteikarten?
  SELECT character FROM kanji WHERE jlpt_level=5 ORDER BY character;
  -- Welche fehlen laut canonical?
  ```
  Plus `python .claude/skills/generate-lesson/pipeline.py coverage 5 --show-missing 30`. Wenn ein Backfill moeglich ist, vor der naechsten Generierung machen — pro Run kann das +30%-Punkte Coverage bringen ohne Mehraufwand.

## 11. Deploy & Live-Schalten

Nach erfolgreicher Verifikation ist die Lektion in der **lokalen** DB. Für Production sind ZWEI Schritte noetig:

### 11a. DB-Sync (Inhalt)
```bash
/sync-cloud-db   # zuerst Cloud→Lokal pruefen, dann Lokal→Cloud
```
Das pusht Lessons/Content/Quiz/Vocabulary auf Cloud SQL. User-Daten
(Progress, Kaeufe, SRS) sind durch 4 Schutzschichten abgesichert (siehe
sync-cloud-db SKILL.md).

### 11a-bis. GCS-Asset-Sync (Bilder, Audios, Slideshows) — PFLICHT
```bash
PYTHONIOENCODING=utf-8 PYTHONPATH=. python scripts/sync_assets_to_gcs.py
```
**Lesson Learned 2026-04-26**: DB-Sync transportiert nur die DB-Felder
(image_url, file_path, media_url). Die referenzierten Dateien (PNG, MP3)
liegen physisch in `app/static/uploads/...` — Production loest die URLs
aber gegen den GCS-Bucket auf. Ohne Asset-Sync: 404 fuer Bilder und
Audios live. `/sync-cloud-db` ruft das mittlerweile selbst auf, aber bei
Manuellem Push immer mit-erinnern. Symptom-Beispiele 2026-04-26:
"die bilder werden auf der webseite nicht angezeigt aber lokal schon"
+ "das audio funktioniert auch nicht auf der deployten webseite".

**Windows-Falle (2026-04-27):** Auf Windows scheitert `scripts/sync_assets_to_gcs.py`
mit `[FEHLER] 'gcloud' nicht im PATH gefunden`, weil `gcloud` als `gcloud.cmd`
installiert ist und Pythons `subprocess.run(["gcloud", ...])` ohne `shell=True`
nur `.exe`-Dateien findet — selbst wenn `which gcloud` in der Bash-Shell den
korrekten Pfad zeigt. Workaround bis Skript gefixt ist: rsync direkt aus
Bash-Loop:
```bash
for src in vocab_generated generated lessons/audio lessons/text_audio lessons/dialog_slideshow; do
  gcloud storage rsync -r "app/static/uploads/$src" "gs://jpl-website-assets/$src" \
    --account=claudio.lutz.cv@gmail.com
done
```
TODO Skript-Fix: `subprocess.run([..."gcloud.cmd", ...], shell=False)` ODER
`shutil.which("gcloud") or shutil.which("gcloud.cmd")` im PATH-Check.

### 11b. Cloud Run Deploy (Code)
**Nur noetig wenn seit dem letzten Deploy Code-Aenderungen gepusht wurden**
(Templates, CSS, JS, Python). Pruefen mit:
```bash
LAST_DEPLOY=$(gcloud run services describe japanese-learning-app \
  --region=europe-west1 --project=healthy-coil-466105-d7 \
  --account=claudio.lutz.cv@gmail.com \
  --format="value(status.conditions[0].lastTransitionTime)")
git log --since="$LAST_DEPLOY" --oneline -- app/ scripts/ run.py
```

Wenn Commits >0:
```bash
/deploy
```
Oder manuell:
```bash
gcloud builds submit --config=cloudbuild.yaml \
  --project=healthy-coil-466105-d7 --account=claudio.lutz.cv@gmail.com .
gcloud run services update japanese-learning-app \
  --image=europe-west6-docker.pkg.dev/healthy-coil-466105-d7/app-images/japanese-learning-app:latest \
  --region=europe-west1 --project=healthy-coil-466105-d7 \
  --account=claudio.lutz.cv@gmail.com
```

**Lesson Learned 2026-04-25**: Nur DB-Sync ohne Cloud-Run-Deploy fuehrt
dazu, dass die Live-Seite die neuen Lessons zwar anzeigt, aber NICHT
mit den aktuellsten Templates/CSS/JS rendert. Wenn das Skill UI-Updates
in den Lessons nutzt (z.B. Markdown-Rendering, text-audio-Player,
neue Templates), MUSS auch deployed werden.

**Lesson Learned 2026-04-26 (Multi-Step-Build-Falle)**: Bei Bug-Fix-Sessions
mit mehreren Edits zuerst ALLE Code-Aenderungen abschliessen (`git status`
clean), DANN ein einziger Build. Wenn ein Build waehrend laufender Edits
gestartet wird, packt er den Code-Stand zum Build-Start in's Image —
nicht den finalen Stand nach allen Edits. Resultat: Re-Build noetig
(~10 min Verlust). Auch fuer Multi-Lesson-Drops gilt: alle Lessons fertig,
DB-Sync, Asset-Sync, GCS pruefen, DANN Build + Deploy.

**Nicht im Skill automatisiert** — Push auf Production bleibt explizite User-Aktion, damit kein Lerner eine halb-fertige Lektion sieht und Mayuko bei Bedarf vor dem Live-Gang ein Fachreview machen kann.

## 12. Aufraeumen / Lesson-Sichtbarkeit (seit 2026-04-26)

**Lessons werden NIE physisch geloescht**, sondern via `is_published=false`
versteckt. Drei Gruende:

1. **User-Fortschritt**: `user_lesson_progress`, `user_quiz_answer`, `card_review_state`
   und `review_log` zeigen auf `lesson_id` / `quiz_question_id`. Loeschen wuerde
   diese Daten ungueltig machen oder per CASCADE mit-loeschen.
2. **Kaeufe**: `lesson_purchase` und `course_purchase` haben FK-RESTRICT (Migration
   `d8e2c1a4f6b3`). DELETE auf einer gekauften Lesson wirft DB-Constraint-Fehler —
   was der Schutz ist, aber zeigt: Loeschen ist sowieso nicht moeglich.
3. **Reversibilitaet**: Wenn der Lerner spaeter wieder Zugang braucht (z.B. Refund-
   Anfrage, Re-Approval einer Lesson nach Mayuko-Review), reicht ein einzelnes
   `UPDATE lesson SET is_published=true WHERE id=X`.

### Aufraeum-Sequenz (lokal + Cloud SYNCHRON)

Aufraeum-Aktionen IMMER in der **gleichen Transaktion** auf lokaler UND Cloud-DB
ausfuehren, sonst Drift beim naechsten Sync (UPSERT bringt Cloud-Stand wieder
zurueck).

```bash
# Lokal
PGPASSWORD="JapaneseApp2025!" psql -h localhost -U app_user -d japanese_learning << 'SQL'
BEGIN;
UPDATE lesson SET is_published=false WHERE <Bedingung>;
UPDATE lesson SET title = '<neuer Titel>' WHERE id=X;
COMMIT;
SQL

# Cloud (gleiche IP autorisieren wie sync-cloud-db)
gcloud sql instances patch jpl-psql --authorized-networks=$(curl -s ifconfig.me)/32 ...
DB_PASS=$(gcloud secrets versions access latest --secret=db-password ...)
PGPASSWORD="$DB_PASS" psql -h 34.65.56.56 -U app_user -d japanese_learning << 'SQL'
BEGIN;
UPDATE lesson SET is_published=false WHERE <Bedingung>;
UPDATE lesson SET title = '<neuer Titel>' WHERE id=X;
COMMIT;
SQL
gcloud sql instances patch jpl-psql --clear-authorized-networks ...
```

### Was waehlen: verstecken vs. umbenennen

- **Verstecken** (`is_published=false`): Lessons, deren Inhalt nicht mehr zum
  aktuellen Skill-Standard passt (z.B. MNN-Imports von 2026-04-24 — andere
  didaktische Linie, alte Charaktere, fehlende Markdown-Hierarchie).
- **Umbenennen** (`title='N5 ' || title`): Lessons, deren Inhalt OK ist, aber
  Titel-Format zur Linie passen muss. Beispiel 2026-04-26: Hiragana 1-5 +
  Katakana 1-5 mit `N5 `-Praefix versehen — Inhalt blieb unveraendert.

### Live-Verifikation

Nach Aufraeum-Sequenz: Browser auf https://japanese-learning.ch/lessons. Versteckte
Lessons antworten auf `/lessons/<id>` mit "nicht verfuegbar". Lessons-Uebersicht
zeigt nur sichtbare Module/Lessons.
