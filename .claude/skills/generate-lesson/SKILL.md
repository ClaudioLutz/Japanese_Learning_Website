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
3. **DB-Status prüfen:** Führe `python .claude/skills/generate-lesson/pipeline.py status` aus. Das zeigt, welche Themen/JLPT-Level wenig approved Content haben — Grundlage für Vorschlag bei Aufruf ohne Argumente.
4. **Docker-DB muss laufen:** `docker compose ps db` → wenn nicht up, `docker compose up db -d`.

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

## 4. Lektions-Struktur (Zielbild)

Jede generierte Lektion enthält:

```
Lesson (title, description, jlpt_level→difficulty_level 1-5, instruction_language='german',
        lesson_type='free', is_published=True, allow_guest_access=True für erste Lektion pro Thema)
├─ LessonPage 1: "Einführung & Vokabeln" (page_type='normal')
│   ├─ LessonContent: text (kurze DE-Einleitung, 2-4 Sätze)
│   └─ LessonContent: vocabulary (6-10 Einträge, Referenz auf Vocabulary-Tabelle)
├─ LessonPage 2: "Grammatik" (page_type='normal')
│   ├─ LessonContent: text (DE-Erklärung des Musters)
│   └─ LessonContent: grammar (1-2 Grammar-Einträge)
├─ LessonPage 3: "Übung" (page_type='quiz_carousel')
│   └─ LessonContent mit QuizQuestions (6-10 Fragen, Mix aus multiple_choice / true_false / matching)
└─ LessonPage 4: "Zusammenfassung" (page_type='normal')
    └─ LessonContent: text (Review + Ausblick nächste Lektion)
```

**Minimal-Budget pro Lektion:** 8 Vokabeln + 1 Grammatik + 6 Quiz-Fragen. Maximal: 12/2/10.

## 5. Content-Qualität: Beispiel-Patterns

### Vocabulary-Eintrag (Claude schreibt)

```json
{
  "word": "家族",
  "reading": "かぞく",
  "meaning": "family",
  "meaning_de": "Familie",
  "jlpt_level": 5,
  "example_sentence_japanese": "わたしの かぞくは よにんです。",
  "example_sentence_english": "My family has four people.",
  "status": "approved",
  "created_by_ai": true
}
```

**Regeln:**
- `meaning` (EN) + `meaning_de` (DE) beide Pflicht
- `reading` in Hiragana (nie Katakana, ausser bei Lehnwörtern)
- `example_sentence_japanese` nutzt Leerzeichen zwischen Wörtern wenn N5 (Hiragana-Fokus)
- Beispielsatz max 12 Silben / ca. 8 Wörter

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
    → prüft Constraints (§3), Schema-Konformität, JLPT-Level-Konsistenz
    → Fehler = Abbruch mit detaillierter Liste

[3] (optional) python .claude/skills/generate-lesson/pipeline.py images {draft_path}
    → ruft DALL-E für thumbnail + Vokabel-Bilder
    → ergänzt image_url / thumbnail_url im Draft

[4] python .claude/skills/generate-lesson/pipeline.py insert {draft_path}
    → Transaktionaler INSERT in Postgres (docker-compose DB)
    → Bei Fehler: Rollback, keine Teil-Lektion
    → Gibt lesson_id zurück

[5] python .claude/skills/generate-lesson/verify.py {lesson_id}
    → Playwright: Login als admin, navigiere zu /admin/manage/lessons,
       öffne Lektion, klicke jede Page, checke Quiz
    → Screenshots in verifications/{lesson_id}/
    → Report: OK oder Issue-Liste

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
- Admin-Routen für Verifikation: `/admin/manage/lessons`, `/admin/manage/vocabulary`, `/admin/manage/grammar`
- Lokal-DB: `postgresql://app_user:JapaneseApp2025!@localhost:5432/japanese_learning`
- Bestehende `AILessonContentGenerator` in `app/ai_services.py` — **NICHT NUTZEN** (User-Entscheidung: Claude schreibt selbst)

## 11. Deploy & Live-Schalten

Nach erfolgreicher Verifikation ist die Lektion in der **lokalen** DB. Für Production:

```bash
/sync-cloud-db   # zuerst Cloud→Lokal prüfen, dann Lokal→Cloud
```

**Nicht im Skill automatisiert** — Push auf Production bleibt explizite User-Aktion, damit Mayuko keine halb-fertige Lektion sieht.
