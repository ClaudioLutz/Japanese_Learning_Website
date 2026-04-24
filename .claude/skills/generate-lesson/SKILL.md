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
| `/generate-lesson N5 Familie` | Direktes Thema, JLPT-Level N5 |
| `/generate-lesson --from-mnn Kapitel 3` | Quelle: Minna no Nihongo (Daten in `scripts/mnn_data/`) |
| `/generate-lesson --from-jlpt N5` | Zufälliges noch nicht abgedecktes N5-Thema |

## 3. Harte Constraints (Nicht-Verhandelbar)

Verletzung ⇒ sofortiger Abbruch, keine Insertion:

- **Quiz-Typen NUR**: `multiple_choice`, `true_false`, `matching`. **KEIN** `fill_blank` (siehe CLAUDE.md §"Quiz-System").
- **JLPT-Level NUR**: N5 oder N4. Kein N3/N2/N1 (siehe improve-jpl §"Nicht-Ziele").
- **Keine Umlaut-Fallbacks**: "Schüler" statt "Schueler", "Grüße" statt "Gruesse". UTF-8 durchgängig.
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
- **Bilder sind PFLICHT** — `thumbnail_url` muss vor Insert gesetzt sein. Pipeline-Schritt `images` (DALL-E) läuft vor `insert`, NICHT optional. Zusätzlich: **mind. 3 `Vocabulary.image_url`** für zentrale Schlüsselvokabeln der Lektion (die das Thema visuell verankern, z.B. bei "Restaurant" → Menü, Essen, Getränk).

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
├─ LessonPage 5: "Dialog / Anwendung" (page_type='normal')
│   └─ LessonContent: text — ein realistischer Mini-Dialog (Gast ↔ Personal /
│      zwei Freunde / Kunde ↔ Verkäufer), jede Zeile in JP + Romaji + DE.
│      Plaintext, Sprecherrollen als "A:" und "B:" am Zeilenanfang.
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
- Vokabel-Bilder: **≥3** für Schlüsselvokabeln (Pflicht).

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
- **Minna no Nihongo Import-Daten:** `scripts/mnn_data/` (JSON-Files pro Kapitel, bereits im Projekt)
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
