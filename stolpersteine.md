# Stolpersteine & Lösungen — MNN 50-Lektionen-Pipeline

> Recherche-Dokument zur Vorbereitung der Generierung aller 50 Minna No Nihongo Lektionen.
> Stand: 2026-04-06

---

## Inhaltsverzeichnis

1. [Copyright & Rechtslage](#1-copyright--rechtslage)
2. [JSON-Datenqualität & Schema-Evolution](#2-json-datenqualität--schema-evolution)
3. [MNN-Lektionsstruktur (alle 50 Lektionen)](#3-mnn-lektionsstruktur-alle-50-lektionen)
4. [Pipeline-Robustheit & Idempotenz](#4-pipeline-robustheit--idempotenz)
5. [Japanische Textqualität & Keigo-Validierung](#5-japanische-textqualität--keigo-validierung)
6. [KI-generierte Quiz-Qualität](#6-ki-generierte-quiz-qualität)
7. [TTS-Audio: Kosten, Qualität & Batch-Optimierung](#7-tts-audio-kosten-qualität--batch-optimierung)
8. [Template & Frontend-Skalierung](#8-template--frontend-skalierung)
9. [Testabdeckung & Qualitätssicherung](#9-testabdeckung--qualitätssicherung)
10. [Review-Workflow für KI-Inhalte](#10-review-workflow-für-ki-inhalte)
11. [Spaced Repetition als Erweiterung](#11-spaced-repetition-als-erweiterung)
12. [Pipeline-Orchestrierung](#12-pipeline-orchestrierung)
13. [Open-Source MNN-Datenquellen](#13-open-source-mnn-datenquellen)
14. [Zusammenfassung: Entscheidungsmatrix](#14-zusammenfassung-entscheidungsmatrix)

---

## 1. Copyright & Rechtslage

### Problem
3A Corporation hält das vollständige Copyright an allen Minna No Nihongo-Materialien. Die offizielle Klausel verbietet jede Reproduktion ohne schriftliche Genehmigung.

### Recherche-Ergebnisse
- **Vokabellisten**: Reine Wortlisten (z.B. "tabemasu = essen") sind faktische Daten und grundsätzlich nicht urheberrechtlich schützbar. Die spezifische *Auswahl und Anordnung* pro Lektion könnte jedoch als kreative Zusammenstellung geschützt sein.
- **Grammatik-Erklärungen**: Eigene Erklärungen sind unproblematisch; das direkte Kopieren der 3A-Texte nicht.
- **Dialoge und Beispielsätze**: Klar geschützt als kreative Werke.
- **Lektionsstruktur**: Die Zuordnung "Lektion 14 = て-Form" nachzubilden ist eine Idee/Methode und typischerweise nicht schützbar.
- **Durchsetzung**: Es wurden KEINE dokumentierten DMCA-Takedowns durch 3A Corporation gefunden. Mehrere GitHub-Repos mit MNN-Vokabeldaten existieren seit Jahren (MinnaNoDS, ryu2gaku/minna-no-nihongo). Das bedeutet aber nicht, dass 3A nicht jederzeit aktiv werden könnte.
- **3. Auflage**: Wurde Herbst 2025 veröffentlicht (Book 1), Book 2 kommt April 2026. Grammatik-Lehrplan bleibt identisch, einige Konversationsszenen wurden modernisiert.

### Beste Lösung
| Inhalt | Empfehlung | Risiko |
|--------|------------|--------|
| Vokabellisten | Eigene Zusammenstellung, MNN-Reihenfolge als Orientierung | Gering |
| Grammatik-Erklärungen | **Eigene Texte schreiben**, MNN-Curriculum als Leitfaden | Sehr gering |
| Konversationen/Dialoge | **Eigene Dialoge erstellen** (NICHT aus MNN kopieren) | Kein Risiko |
| Beispielsätze | Eigene Sätze, die gleiche Grammatik demonstrieren | Gering |
| Lektionsreihenfolge | MNN-Grammatik-Progression nachbilden | Kein Risiko |

**Konkrete Empfehlung**: Für die Konversationen (aktuell aus MNN kopiert!) eigene Dialoge erstellen lassen, die die gleichen Grammatikpunkte und Vokabeln verwenden, aber andere Situationen/Sprecher haben. Das eliminiert sowohl das Copyright-Risiko als auch das Keigo-Risiko (da wir die Dialoge von Grund auf kontrollieren).

---

## 2. JSON-Datenqualität & Schema-Evolution

### Problem
Das aktuelle JSON-Schema (`beginner1_lesson01.json`) deckt nur Lektion 1 ab. Spätere Lektionen führen Verben, Adjektive, Konjugationen und komplexere Grammatik ein. Es gibt keine Schema-Validierung.

### Aktuelles Schema (Lektion 1)
```json
{
  "source": "Minna No Nihongo Beginner I",
  "lesson_number": 1,
  "title": "Lesson 1 – Self-Introduction",
  "title_ja": "第1課",
  "jlpt_level": 5,
  "description": "...",
  "vocabulary": [
    {"word": "わたし", "reading": "watashi", "meaning": "I", "kanji": null}
  ],
  "vocabulary_countries": [
    {"word": "アメリカ", "reading": "Amerika", "meaning": "U.S.A."}
  ],
  "grammar": [
    {
      "title": "N は N です",
      "structure": "N₁ は N₂ です",
      "jlpt_level": 5,
      "explanation": "...",
      "example_sentences": "..."
    }
  ],
  "conversation": {
    "title": "How do you do?",
    "title_ja": "はじめまして",
    "lines": [
      {"speaker": "Sato", "japanese": "...", "romaji": "...", "english": "..."}
    ]
  }
}
```

### Schema-Anforderungen nach Lektions-Progression

| Ab Lektion | Neuer Inhalt | Benötigte Felder |
|------------|-------------|------------------|
| 1-3 | Kopula, Demonstrativpronomen, Partikel | `word`, `reading`, `meaning`, `kanji` (bestehend) |
| 4-6 | Verben (ます-Form), Zeitangaben | `part_of_speech`, `verb_group` (I/II/III) |
| 7-8 | あげる/もらう, Adjektive (い/な) | `adjective_type` (i/na) |
| 14 | **て-Form** (Fundament!) | `conjugation_forms` (te, ta, nai, dict) |
| 17 | ない-Form | — (conjugation_forms deckt ab) |
| 20 | Plain Form / Casual Speech | `formality_level` |
| 26 | ～んです, Erklärungsform | — |
| 27 | **Potential-Form** | — (conjugation_forms) |
| 37 | **Passiv** | — (conjugation_forms) |
| 48 | **Kausativ** | — (conjugation_forms) |
| 49-50 | **Keigo** (尊敬語 + 謙譲語) | `keigo_type`, `keigo_equivalent` |

### Beste Lösung: Pydantic-Validierung

**Bibliothek**: `pydantic>=2.11` (Rust-basierter Core, schnellste Validierung, native Python Type Hints)

```python
# scripts/schema.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional

class VocabularyItem(BaseModel):
    word: str = Field(..., min_length=1)
    reading: str = Field(..., min_length=1)
    meaning: str = Field(..., min_length=1)
    kanji: Optional[str] = None
    part_of_speech: Optional[str] = Field(
        None, pattern=r"^(noun|verb|i-adjective|na-adjective|adverb|particle|expression|counter|conjunction)$"
    )
    verb_group: Optional[int] = Field(None, ge=1, le=3)  # Verb-Gruppe I/II/III
    adjective_type: Optional[str] = Field(None, pattern=r"^(i|na)$")

    @field_validator("verb_group")
    @classmethod
    def verb_group_needs_verb(cls, v, info):
        if v is not None and info.data.get("part_of_speech") != "verb":
            raise ValueError("verb_group nur bei part_of_speech='verb'")
        return v

class GrammarPoint(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    structure: str = Field(..., min_length=1)
    jlpt_level: int = Field(..., ge=1, le=5)
    explanation: str = Field(..., min_length=10)
    example_sentences: str = Field(..., min_length=5)

class ConversationLine(BaseModel):
    speaker: str = Field(..., min_length=1)
    japanese: str = Field(..., min_length=1)
    romaji: str = Field(..., min_length=1)
    english: str = Field(..., min_length=1)

class Conversation(BaseModel):
    title: str
    title_ja: str
    lines: list[ConversationLine] = Field(..., min_length=2)

class LessonData(BaseModel):
    source: str
    lesson_number: int = Field(..., ge=1, le=50)
    title: str
    title_ja: str
    jlpt_level: int = Field(..., ge=1, le=5)
    description: str
    vocabulary: list[VocabularyItem] = Field(..., min_length=1)
    vocabulary_countries: list[VocabularyItem] = Field(default_factory=list)
    grammar: list[GrammarPoint] = Field(..., min_length=1)
    conversation: Conversation

# Nutzung vor Import:
# data = LessonData.model_validate(json.load(open("lesson01.json")))
```

**Warum Pydantic statt jsonschema oder cerberus:**
- 3.5x schneller (Rust-Core)
- Vollständige IDE-Unterstützung (Autocomplete, Type Checking)
- Fehlermeldungen sind strukturiert und präzise
- Kann automatisch JSON Schema exportieren (für Dokumentation)

### Alternatives: Ein Schema für alle 50 Lektionen
Die optionalen Felder (`verb_group`, `adjective_type`, `part_of_speech`) machen das Schema abwärtskompatibel. Lektion 1 muss diese nicht füllen, Lektion 14+ nutzt sie. **Ein Schema für alle 50 Lektionen ist die richtige Wahl.**

---

## 3. MNN-Lektionsstruktur (alle 50 Lektionen)

### Seitenstruktur (identisch für alle 50 Lektionen)

Jede MNN-Lektion folgt **exakt der gleichen Struktur**:

1. **語彙 (Goi)** — Vokabeln/Wortliste
2. **文型 (Bunkei)** — Satzmuster (Grundgrammatik-Strukturen)
3. **例文 (Reibun)** — Beispielsätze
4. **会話 (Kaiwa)** — Konversation/Dialog
5. **練習 A-C (Renshuu)** — Übungen (strukturiert → frei)
6. **問題 (Mondai)** — Testfragen

Es gibt **KEINE Änderung dieser Struktur** zwischen Book 1 und Book 2. Lese-/Schreibübungen sind separate Zusatzbücher.

### Unser 5-Seiten-Mapping

| Unsere Seite | MNN-Entsprechung | Inhalt |
|-------------|-------------------|--------|
| Page 1: Vocabulary | 語彙 | Vokabelliste + Audio |
| Page 2: Grammar | 文型 + 例文 | Grammatikpunkte + Beispielsätze + Audio |
| Page 3: Conversation | 会話 | Dialog + Multi-Voice Audio + Quiz |
| Page 4: Practice | 練習 A-C | Formatives Quiz (unbegrenzt) |
| Page 5: Test | 問題 | Summatives Quiz (3 Versuche, 70% Pass) |

**Dieses Mapping funktioniert für alle 50 Lektionen** ohne Anpassung.

### Grammatik-Progression (komplett)

<details>
<summary><strong>Book 1 — Lektionen 1-25 (JLPT N5) — 79 Satzmuster</strong></summary>

| L | Grammatikpunkte |
|---|----------------|
| 1 | N₁はN₂です, じゃありません, ですか, N₁もN₂です, N₁のN₂です |
| 2 | これ/それ/あれ, この/その/あの, N₁ですかN₂ですか |
| 3 | ここ/そこ/あそこ, NはPlaceです, どこ, いくら |
| 4 | 時間表現, ～に起きます/寝ます, ～から～まで, ～ました |
| 5 | Placeへ行きます, 乗り物で, PersonとVます, いつ |
| 6 | NをVます, PlaceでVます, ～ませんか, ～ましょう |
| 7 | 道具でVます, あげます/もらいます, もう～ました |
| 8 | **な-Adj, い-Adj**, どう/どんな |
| 9 | Nが好き/上手/わかります, ～から (Grund) |
| 10 | あります/います (Existenz), NやN |
| 11 | **Zählwörter** (ひとつ...とお, ～人, ～枚, ～台 etc.) |
| 12 | Adj Vergangenheit/Verneinung, Vergleich (より), いちばん |
| 13 | ほしいです, Vたいです, Vに行きます |
| **14** | **Verb-Gruppen I/II/III, て-Form**, ～てください, ～ています |
| 15 | ～てもいいです, ～てはいけません, ～ています (Zustand) |
| 16 | V₁てV₂て (Verkettung), い-Adj→くて, な-Adj→で, Vてから |
| **17** | **ない-Form**, ～ないでください, ～なければなりません |
| **18** | **辞書形 (Dictionary Form)**, ～ことができます |
| **19** | **た-Form**, ～たことがあります, ～たり～たりします |
| **20** | **Plain/Casual Form** (alle Wortarten) |
| 21 | ～と思います, ～と言います, ～でしょう？ |
| 22 | Nebensatz-Nomenmodifikation (Relativsätze) |
| 23 | ～とき (wenn), V-dict/た + と (wenn/falls) |
| 24 | くれます, ～てあげます/もらいます/くれます |
| 25 | ～たら (Konditional), ～ても (obwohl) |

</details>

<details>
<summary><strong>Book 2 — Lektionen 26-50 (JLPT N4) — 73 Satzmuster</strong></summary>

| L | Grammatikpunkte |
|---|----------------|
| 26 | ～んです (Erklärung), ～ていただけませんか (höfliche Bitte) |
| **27** | **Potential-Form** (～られる/～える), 見えます/聞こえます |
| 28 | ～ながら (gleichzeitig), ～し (mehrere Gründe) |
| 29 | ～てしまいます (Bedauern/Abschluss) |
| 30 | ～てあります (absichtlicher Zustand), ～ておきます (Vorbereitung) |
| 31 | **Volitional Form** (～よう), ～つもりです (Plan) |
| 32 | ～たほうがいい (Ratschlag), ～かもしれません (vielleicht) |
| 33 | **Imperativ/Prohibitiv**, indirekte Rede |
| 34 | ～とおりに (gemäss), ～あとで (nachdem) |
| **35** | **ば-Form** (Konditional), ～ば～ほど |
| 36 | ～ように (Zweck), ～ようになりました (Veränderung) |
| **37** | **Passiv** (受身), NはNに passive |
| 38 | Nominalisierung mit の, ～のはAdjです |
| 39 | ～ので (weil, objektiv), 途中で |
| 40 | Eingebettete Fragen (～か), ～てみます (ausprobieren) |
| 41 | やります/さしあげます/いただきます/くださいます (Keigo-Verben) |
| 42 | ～ために (Zweck), ～のに (für/zum) |
| 43 | ～そうです (Anschein), ～てきます |
| 44 | ～すぎます (zu viel), ～やすい/にくい |
| 45 | ～ばあいは (falls), ～のに (obwohl) |
| 46 | ～ところです (gerade dabei), ～たばかりです, ～はずです |
| 47 | ～そうです (Hörensagen), ～ようです (scheint) |
| **48** | **Kausativ** (使役, ～させます) |
| **49** | **尊敬語** (Honorific Speech): お～になります, spezielle Verben |
| **50** | **謙譲語** (Humble Speech): お/ご～します, spezielle Verben |

</details>

### Vokabelzahlen pro Lektion

Die Verteilung ist **nicht gleichmässig** — sie schwankt stark:

| Bereich | Min | Max | Durchschnitt |
|---------|-----|-----|-------------|
| Book 1 (L1-25) | 23 (L22/L24) | 74 (L11) | ~39 |
| Book 2 (L26-50) | ~25 | ~55 | ~36 |
| **Gesamt** | | | **~1'960 Wörter** |

Book 1: 1'060 Vokabeln, 79 Satzmuster. Book 2: 900 Vokabeln, 73 Satzmuster.

### Konversations-Struktur

- **Jede Lektion hat GENAU EINE Konversation** (会話/Kaiwa)
- **Typisch 2-4 Sprecher**, situativ (Vorstellung, Einkaufen, Telefonieren, Restaurant, Arzt etc.)
- **8-14 Zeilen** pro Dialog
- Jede Konversation hat einen japanischen Titel (z.B. "はじめまして", "いっしょに行きませんか")

---

## 4. Pipeline-Robustheit & Idempotenz

### Aktuelle Pipeline: 3 Schritte

```
beginner1_lesson01.json → import_mnn.py → generate_tts_audio.py → generate_quizzes.py
```

### Analyse der Idempotenz

| Script | Idempotent? | Details |
|--------|-------------|---------|
| `import_mnn.py` | **Ja (teilweise)** | Vocabulary: Skip bei existierendem `word` (UNIQUE). Grammar: Skip bei existierendem `title` (UNIQUE). Lesson: Skip wenn `title` existiert. **Problem**: Wenn Lektion existiert, wird NICHTS aktualisiert — kein Update möglich. |
| `generate_tts_audio.py` | **Ja (destruktiv)** | Löscht ALLE bestehenden Audio-Einträge der Lektion aus der DB, generiert neu. Audio-Dateien werden überschrieben. |
| `generate_quizzes.py` | **Nein** | Keine Duplikat-Prüfung. Zweimaliges Ausführen erzeugt doppelte Quizzes. |

### Risiken bei 50-Lektionen-Batch

1. **Kein Rollback bei Teilfehlern**: `import_mnn.py` verwendet `flush()` + finales `commit()`. Wenn der Import bei Lektion 23 abbricht, sind Lektionen 1-22 committed, 23 ist inkonsistent.
2. **Quiz-Duplikate**: `generate_quizzes.py` hat keine Prüfung — bei erneutem Lauf entstehen doppelte Fragen.
3. **Hardcodierte Audio-Pfade**: `D:/Media/Language/...` in `import_mnn.py` (Zeile 48-53) — existiert nur lokal.
4. **Kein Update-Modus**: `import_mnn.py` kann bestehende Lektionen nicht aktualisieren, nur neue erstellen.

### Beste Lösung

```python
# 1. Quiz-Duplikat-Schutz in generate_quizzes.py hinzufügen:
existing_quizzes = LessonContent.query.filter_by(
    lesson_id=lesson.id,
    is_interactive=True,
    page_number=page_number,
).all()
if existing_quizzes:
    print(f"  [SKIP] Seite {page_number} hat bereits {len(existing_quizzes)} Quizzes")
    # Optional: --force Flag zum Überschreiben

# 2. Transaction-Safety verbessern:
try:
    import_lesson(data)
    db.session.commit()
except Exception as e:
    db.session.rollback()
    print(f"FEHLER bei Lektion {data['lesson_number']}: {e}")

# 3. Update-Modus für import_mnn.py:
# --update Flag: Bestehende Inhalte aktualisieren statt skippen
```

**Priorität**: Quiz-Duplikat-Schutz ist kritisch vor dem 50-Lektionen-Batch.

---

## 5. Japanische Textqualität & Keigo-Validierung

### Problem (Auslöser dieses Dokuments)
KI-generierte Konversation enthielt Keigo-Fehler: Lehrer Suzuki sagte "日本語の先生です" über sich selbst — 先生 ist ein Ehrentitel, den man nie für sich selbst verwendet (korrekt: 教師/kyōshi).

### Keigo-System: 3 Ebenen

| Ebene | Japanisch | Verwendung | Beispiel |
|-------|-----------|------------|---------|
| 丁寧語 (Teineigo) | Höfliche Sprache | Standard-Höflichkeit | ～です, ～ます |
| 尊敬語 (Sonkeigo) | Respektsprache | Für Handlungen ANDERER | いらっしゃる, おっしゃる |
| 謙譲語 (Kenjōgo) | Bescheidene Sprache | Für EIGENE Handlungen | おる, 申す, 参る |

### Verfügbare NLP-Tools für Japanisch

| Tool | Was es kann | Was es NICHT kann |
|------|------------|-------------------|
| **fugashi** (MeCab-Wrapper) | Morphologische Analyse, POS-Tagging, Konjugationsformen erkennen | Partikel-Korrektheit beurteilen |
| **spaCy ja_core_news_lg** | Dependency Parsing, NER, Tokenisierung | Keigo-Konsistenz prüfen |
| **JLPT Kanji-Datenbanken** | Kanji nach JLPT-Level filtern | Kontextuelle Angemessenheit |

### Beste Lösung: 3-Stufen-Validierung

**Stufe 1 — Automatisch (regelbasiert, 100% zuverlässig):**
```python
# JLPT-Kanji-Level-Prüfung mit fugashi + Kanji-DB
import fugashi
# pip install fugashi[unidic]

# Kanji-DB: github.com/davidluzgouveia/kanji-data (JSON mit JLPT-Levels)
def check_kanji_level(text: str, max_jlpt: int) -> list[dict]:
    violations = []
    for char in text:
        if '\u4e00' <= char <= '\u9fff':  # CJK Unified Ideographs
            level = jlpt_kanji_db.get(char)
            if level and level < max_jlpt:  # Niedrigere Zahl = höheres Level
                violations.append({"kanji": char, "expected": f"N{max_jlpt}", "actual": f"N{level}"})
    return violations
```

**Stufe 2 — Automatisch (LLM-basiert, ~85% zuverlässig):**
```python
# LLM-Validierung für Partikel, Keigo, Natürlichkeit
def validate_japanese_with_llm(text: str, jlpt_level: str, context: str) -> dict:
    prompt = f"""Du bist ein erfahrener Japanisch-Lehrer. Prüfe diesen Text auf:
    1. Korrekte Partikelverwendung (は/が, に/で, を/が)
    2. Konsistentes Keigo-Niveau (passend für JLPT {jlpt_level})
    3. Natürlichkeit (kein 'Lehrbuch-Japanisch')
    4. Ob Ehrentitel korrekt verwendet werden (先生 nur für andere, nicht für sich selbst)
    Kontext: {context}
    Text: {text}
    Antworte als JSON: {{"ok": bool, "issues": [...], "naturalness": 1-5}}"""
    # → Gemini oder GPT-4o aufrufen
```

**Stufe 3 — Manuell (100% zuverlässig):**
- Export der generierten Quizzes als lesbares Dokument
- Review durch japanische Muttersprachlerin (Ihre Frau)
- Fokus auf: Keigo-Konsistenz, Partikel, kulturelle Angemessenheit

### Realistische Einschätzung

| Validierungsaspekt | Automatisierbar? | Zuverlässigkeit |
|-------------------|------------------|-----------------|
| JLPT-Kanji-Level | Ja (regelbasiert) | 95%+ |
| Morphologie/POS | Ja (fugashi) | 98% |
| Partikel-Korrektheit | Nur mit LLM | 80-90% |
| Keigo-Konsistenz | Teilweise (Endungen erkennen), vollständig nur LLM | 70% (Regeln) / 85% (LLM) |
| Natürlichkeit | Nur mit LLM | 80-85% |
| **Kulturelle Angemessenheit** | **Nur manuell** | **Muttersprachler nötig** |

**Fazit**: Für die Konversationen ist manuelles Review unersetzbar. Für Quizfragen reicht die LLM-Stufe in Kombination mit dem Admin-Approval-System (Flag `generated_by_ai` + `review_status`).

---

## 6. KI-generierte Quiz-Qualität

### Aktuelle Implementierung

- **AI-Provider**: Google Gemini (`gemini-3-flash-preview`)
- **Methode**: Batch-Generierung — alle Fragen einer Seite in EINEM API-Call (`generate_page_quiz_batch()`)
- **Prompt-Strategie**: System-Prompt als "Expert Japanese quiz designer", User-Prompt mit Keywords aus JSON

### Quiz-Verteilung pro Lektion (aktuell)

| Seite | Fragen | Typen | Einstellung |
|-------|--------|-------|-------------|
| 1: Vocabulary | 3 | 3× MC | max_attempts=3, pass=70% |
| 2: Grammar | 3 | 2× T/F + 1× MC | max_attempts=3, pass=70% |
| 3: Conversation | 1+ | 1× MC pro Konversation | max_attempts=3, pass=70% |
| 4: Practice | 9 | 5× MC + 3× T/F + 1× Matching | **Unbegrenzt**, kein Score |
| 5: Test | 9 | 5× MC + 3× T/F + 1× Matching | max_attempts=3, pass=70% |
| **Total** | **~25** | | |

### Bekannte Probleme mit KI-generierten japanischen Quizzes

1. **Partikel-Fehler**: は vs. が Verwechslungen in Antwortoptionen
2. **Keigo-Inkonsistenz**: Mischung von 尊敬語 und 謙譲語 in einem Quiz
3. **Kanji-Level-Verstösse**: N3-Kanji in N5-Quizfragen
4. **Unnatürliche Formulierungen**: LLMs generieren manchmal zu explizite Sätze (Japanisch lässt Subjekte weg)
5. **Romanisierungs-Fehler**: Inkonsistente Umschrift (si vs. shi, tu vs. tsu)

### Beste Lösung

**A) Prompt-Verbesserung** (sofort umsetzbar):
```
Zusätzliche Constraints im Quiz-Prompt:
- "Verwende NUR Kanji bis JLPT N{level}"
- "Alle Optionen müssen das gleiche Keigo-Niveau haben"
- "Verwende Modified Hepburn-Romanisierung (し=shi, つ=tsu, ふ=fu)"
- "Gib keine Hints im Fragetext, die die Antwort verraten"
```

**B) Post-Generation-Validierung** (vor DB-Speicherung):
```python
def validate_quiz_question(question: dict, jlpt_level: int) -> list[str]:
    issues = []
    # 1. Kanji-Level prüfen
    for text in [question["question_text"]] + [o["text"] for o in question.get("options", [])]:
        kanji_issues = check_kanji_level(text, jlpt_level)
        if kanji_issues:
            issues.append(f"Kanji-Level-Verstoss: {kanji_issues}")
    
    # 2. Mindestens 1 korrekte Antwort
    if question.get("question_type") == "multiple_choice":
        correct = [o for o in question["options"] if o["is_correct"]]
        if len(correct) != 1:
            issues.append(f"Erwartet 1 korrekte Antwort, gefunden: {len(correct)}")
    
    # 3. Romanisierung vorhanden
    for opt in question.get("options", []):
        if any('\u3040' <= c <= '\u309f' or '\u30a0' <= c <= '\u30ff' for c in opt["text"]):
            if not any(c.isascii() and c.isalpha() for c in opt.get("feedback", "")):
                issues.append(f"Fehlende Romanisierung in Option: {opt['text'][:20]}")
    
    return issues
```

**C) Dry-Run + Review** (vor Produktion):
```bash
# Generiere Quizzes als JSON (nicht in DB speichern)
python scripts/generate_quizzes.py --lesson 1 --dry-run > review/lesson01_quizzes.json

# Manuelles Review oder automatische Validierung
python scripts/validate_quizzes.py review/lesson01_quizzes.json
```

### Kosten-Schätzung für 50 Lektionen

- Gemini Flash: ~0.075$/M Input, ~0.3$/M Output
- ~2'000 Tokens pro Lektion × 50 = ~100'000 Tokens
- **Geschätzte Kosten: ~$0.03-0.05** (vernachlässigbar)

---

## 7. TTS-Audio: Kosten, Qualität & Batch-Optimierung

### Aktueller Provider: Google Cloud TTS (Neural2)

| Einstellung | Wert |
|-------------|------|
| Stimmen | ja-JP-Neural2-B (weiblich), Neural2-C (männlich 1), Neural2-D (männlich 2) |
| Geschwindigkeit | 0.85x (verlangsamt für Lerner) |
| Sprecher-Mapping | 21 hardcodierte Charaktere (Sato→weiblich, Miller→männlich etc.) |
| Multi-Voice | Jede Zeile einzeln → ffmpeg-Concat mit 0.7s Pause |

### Provider-Vergleich

| Provider | Stimmen (ja) | Preis/1M Zeichen | Qualität | Free Tier |
|----------|-------------|------------------|----------|-----------|
| **Google Cloud TTS** | Neural2: 3 Stimmen | $16 (Neural2) | Sehr gut | 1M chars/Monat gratis |
| **OpenAI TTS** | 13 (multilingual) | $15 (Std), $30 (HD) | Gut, natürlich | Keine |
| **Amazon Polly** | 4 dedizierte ja-Stimmen | $16 (Neural) | Gut | 1M chars/12 Monate |
| **ElevenLabs** | Multilingual v2 | ~$30+ | Beste Prosodie | Sehr begrenzt |

**Empfehlung**: Google Cloud TTS beibehalten — bestes Preis-Leistungs-Verhältnis, grosszügiger Free Tier, gute japanische Qualität.

### Kosten-Schätzung für 50 Lektionen

| Komponente | Zeichen/Lektion | × 50 Lektionen | Kosten |
|-----------|-----------------|-----------------|--------|
| Vokabeln | ~1'500 | 75'000 | ~$1.20 |
| Grammatik + Beispiele | ~1'200 | 60'000 | ~$0.96 |
| Konversation (Multi-Voice) | ~800 | 40'000 | ~$0.64 |
| **Total** | ~3'500 | **175'000** | **~$2.80** |

Im Free Tier (1M chars/Monat) wäre der gesamte Batch **kostenlos**.

### Batch-Optimierung

**Problem**: Aktuell wird für jede Konversationszeile ein separater API-Call + ffmpeg-Subprocess ausgeführt. Bei 50 Lektionen: ~250+ API-Calls + ~250 ffmpeg-Aufrufe.

**Lösung: Parallelisierung mit asyncio + Content-Cache:**

```python
# Content-basierter Cache (MD5-Hash des Textes)
import hashlib
from pathlib import Path

CACHE_DIR = Path("audio_cache")

def get_cache_path(text: str, voice: str) -> Path:
    key = hashlib.md5(f"{text}:{voice}".encode()).hexdigest()
    return CACHE_DIR / f"{key}.mp3"

# Vor Synthese prüfen:
cache = get_cache_path(text, voice_name)
if cache.exists():
    return cache  # Cache-Hit, kein API-Call nötig
```

**SSML Best Practices für Japanisch:**
```xml
<!-- Pausen zwischen Sätzen -->
<speak>
  <s>おはようございます。</s>
  <break time="500ms"/>
  <s>今日はいい天気ですね。</s>
</speak>

<!-- Langsameres Tempo für schwierige Wörter -->
<speak>
  <prosody rate="slow">きゅうきゅうしゃ</prosody>
</speak>
```

### Zeichenlimit beachten
Google TTS hat ein Limit von **5'000 Bytes pro Request**. Japanische Zeichen = 3 Bytes UTF-8 → maximal **~1'600 japanische Zeichen pro Request**. Bei langen Vokabellisten muss aufgeteilt werden.

---

## 8. Template & Frontend-Skalierung

### Aktuelle Template-Analyse (`lesson_view.html`)

- **Dynamische Seitenanzahl**: Template iteriert über `lesson.pages` — kein Hardcoded-Limit
- **Content-Type-Handling**: Erkennt `page.metadata.title == 'Conversation'` für Spezialbehandlung
- **Quiz-Rendering**: Unterstützt `multiple_choice`, `true_false`, `matching`
- **Sidebar**: Dynamische Seitenliste mit Fortschritts-Badge
- **Progress-Tracking**: Pro Seite, basierend auf `completed_content_count / page_content_count`

### Risiken

| Risiko | Wahrscheinlichkeit | Impact |
|--------|-------------------|--------|
| Langsame Sidebar bei 50 Lektionen im Kurs | Mittel | Gering (Seitenliste ist pro Lektion, nicht pro Kurs) |
| Lange Vokabelseite bei 74 Wörtern (L11) | Hoch | Mittel (Scrolling nötig) |
| Conversation-Page Fallback-Titel | Gering | Gering |

### Beste Lösung

Kein Template-Umbau nötig. Das Template ist bereits generisch genug. Einzige Empfehlung:

- **Lange Vokabelseiten**: Lazy-Loading oder Accordion-Gruppierung für Lektionen mit 50+ Vokabeln erwägen (nice-to-have, nicht blockierend)
- **Kursübersicht**: 50 Lektionen in der Kurs-Ansicht brauchen evtl. Paginierung oder Gruppierung (Book 1 / Book 2)

---

## 9. Testabdeckung & Qualitätssicherung

### Aktuelle Coverage

- **fail_under**: 35% (pyproject.toml)
- **204 Tests bestanden** (Stand: letzter Commit)
- **Getestet**: User-Model, Lesson-Access-Control, Auth, Payment, Forms, Admin-API
- **NICHT getestet**: Quiz-Generierung, Quiz-Submission, Progress-Update, Import-Script, TTS-Script, Content-Validator

### Kritische Testlücken für 50-Lektionen-Skalierung

| Lücke | Risiko | Priorität |
|-------|--------|-----------|
| `import_mnn.py` — Duplikat-Handling | Doppelte Einträge bei Re-Import | **Hoch** |
| `generate_quizzes.py` — Duplikat-Schutz | Doppelte Quizzes | **Hoch** |
| Quiz-Submission-Route | Falsche Bewertung | Mittel |
| Progress-Update-Route | Fortschritt geht verloren | Mittel |
| JSON-Schema-Validierung | Ungültige Daten importiert | Mittel |

### Beste Lösung

**Vor dem 50-Lektionen-Batch mindestens diese Tests ergänzen:**

```python
# tests/unit/test_import_mnn.py
def test_import_idempotent(db, sample_lesson_json):
    """Zweimaliger Import erzeugt keine Duplikate."""
    from scripts.import_mnn import import_lesson
    import_lesson(sample_lesson_json)
    import_lesson(sample_lesson_json)  # Zweiter Lauf
    assert Lesson.query.count() == 1
    assert Vocabulary.query.count() == len(sample_lesson_json["vocabulary"])

def test_import_vocabulary_unique_constraint(db):
    """Gleiche Vokabel in zwei Lektionen wird nur einmal angelegt."""
    ...

# tests/unit/test_generate_quizzes.py
def test_quiz_no_duplicates(db, sample_lesson):
    """Zweimalige Quiz-Generierung erzeugt keine doppelten Fragen."""
    ...

def test_quiz_kanji_level(sample_quiz_output):
    """Quiz-Fragen verwenden nur Kanji des richtigen JLPT-Levels."""
    ...
```

---

## 10. Review-Workflow für KI-Inhalte

### Problem
KI-generierte Inhalte (Quizzes, evtl. zukünftig Konversationen) können subtile Fehler enthalten, die nur Muttersprachler erkennen.

### Wie Duolingo es macht

1. **Curriculum Design** (100% menschlich): Thema, Grammatik-Fokus, Vokabelziele definieren
2. **Prompt + Generation**: LLM generiert mehrere Varianten mit Templates
3. **Human Review**: Experten wählen die besten Optionen, verfeinern für Natürlichkeit

Ergebnis: 148 neue Kurse in einem Jahr (vorher: 12 Jahre für 100 Kurse).

### Beste Lösung für unser Projekt

**Bestehende Infrastruktur nutzen:**
- `generated_by_ai` Flag existiert bereits auf LessonContent
- `content_validator.py` existiert (aber nicht in Pipeline integriert)
- Admin-Bereich existiert

**Erweiterung: Review-Status-Feld:**
```python
# In LessonContent (models.py) hinzufügen:
review_status = db.Column(db.String(20), default="draft")
# Werte: draft → review → approved / rejected
review_notes = db.Column(db.Text)  # Kommentare der Reviewerin
```

**Pragmatischer 3-Schritt-Workflow:**

```
1. generate_quizzes.py --dry-run → JSON-Datei
2. validate_quizzes.py → Automatische Prüfung (Kanji-Level, Struktur)
3. Export als lesbares Dokument → Manuelle Prüfung durch Muttersprachlerin
   → Bei OK: generate_quizzes.py (ohne --dry-run)
   → Bei Problemen: Prompt anpassen, Schritt 1 wiederholen
```

**Für 50 Lektionen realistisch:** Manuelles Review aller 50 × 25 = 1'250 Quizfragen ist aufwändig (~5-8 Stunden). Strategie: Automatische Validierung filtert offensichtliche Fehler, manuelles Review konzentriert sich auf Stichproben (z.B. jede 5. Lektion vollständig + alle Keigo-relevanten Lektionen 41, 49, 50).

---

## 11. Spaced Repetition als Erweiterung

### Empfehlung: FSRS-Algorithmus (`py-fsrs>=6.3.1`)

FSRS (Free Spaced Repetition Scheduler) ist dem klassischen SM-2 empirisch überlegen und wird seit 2024 auch von Anki als Standard verwendet.

### Datenmodell

```python
class UserVocabCard(db.Model):
    """Spaced-Repetition-Karte für einzelne Vokabeln/Kanji."""
    __tablename__ = 'user_vocab_cards'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    content_id = db.Column(db.Integer, db.ForeignKey('lesson_content.id'))
    card_state = db.Column(db.JSON)          # FSRS Card-State
    due_date = db.Column(db.DateTime)        # Nächster Review-Zeitpunkt
    stability = db.Column(db.Float, default=0.0)
    difficulty = db.Column(db.Float, default=0.0)
    reps = db.Column(db.Integer, default=0)
    lapses = db.Column(db.Integer, default=0)
```

### Integration mit bestehendem System

Das bestehende `UserLessonProgress`-Model speichert bereits JSON für Content-Progress. SRS könnte als **eigenes Feature** neben dem bestehenden Lektionsfortschritt laufen:

- **Lektionsfortschritt** (bestehend): Linear, Seite für Seite, Quiz am Ende
- **SRS-Review** (neu): Vokabel-/Kanji-Karten aus abgeschlossenen Lektionen, täglich reviewen

**Aufwand**: Neues Model + Migration, Service-Klasse (~100 Zeilen), 2-3 neue Routes, 1 Template. Geschätzt: 1-2 Tage Implementierung.

**Empfehlung**: Erst nach dem 50-Lektionen-Batch implementieren. Kein Blocker.

---

## 12. Pipeline-Orchestrierung

### Empfehlung: Einfaches Python-Skript (`run_pipeline.py`)

Für einen einzelnen Entwickler mit manueller Pipeline sind Airflow, Prefect und Luigi massiver Overkill.

### Konkreter Entwurf

```python
# scripts/run_pipeline.py
"""
Orchestriert die MNN-Lektions-Pipeline.

Nutzung:
  python scripts/run_pipeline.py --lessons 1-25          # Book 1
  python scripts/run_pipeline.py --lessons 1             # Einzelne Lektion
  python scripts/run_pipeline.py --lessons 1-25 --dry-run
  python scripts/run_pipeline.py --lessons 1-25 --skip-tts
  python scripts/run_pipeline.py --lessons 1-25 --only validate
"""

import argparse
import subprocess
import sys
from pathlib import Path

STEPS = {
    "validate": "python scripts/validate_json.py --file {json_file}",
    "import":   "python scripts/import_mnn.py --file {json_file}",
    "tts":      "python scripts/generate_tts_audio.py --lesson {lesson_num}",
    "quizzes":  "python scripts/generate_quizzes.py --lesson {lesson_num}",
}

def run_step(name: str, cmd: str, dry_run: bool = False) -> bool:
    print(f"\n{'='*60}")
    print(f"  SCHRITT: {name}")
    print(f"  CMD: {cmd}")
    print(f"{'='*60}")
    if dry_run:
        print("  [DRY-RUN] Übersprungen")
        return True
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"  FEHLER in Schritt '{name}' (Exit Code: {result.returncode})")
        return False
    return True

def run_pipeline(lesson_numbers: list[int], dry_run: bool, skip_tts: bool):
    for num in lesson_numbers:
        json_file = f"scripts/mnn_data/beginner{'1' if num <= 25 else '2'}_lesson{num:02d}.json"
        print(f"\n{'#'*60}")
        print(f"  LEKTION {num}")
        print(f"{'#'*60}")
        
        if not run_step("validate", STEPS["validate"].format(json_file=json_file), dry_run):
            print(f"Abbruch bei Lektion {num} (Validierung fehlgeschlagen)")
            return False
        if not run_step("import", STEPS["import"].format(json_file=json_file), dry_run):
            return False
        if not skip_tts:
            if not run_step("tts", STEPS["tts"].format(lesson_num=num), dry_run):
                return False
        if not run_step("quizzes", STEPS["quizzes"].format(lesson_num=num), dry_run):
            return False
    
    print(f"\n{'='*60}")
    print(f"  FERTIG: {len(lesson_numbers)} Lektionen verarbeitet")
    print(f"{'='*60}")
    return True
```

**Warum nicht Invoke/Makefile**: Das Projekt ist Python-basiert, ein einfaches Script mit `subprocess` ist am transparentesten und hat keine zusätzliche Dependency.

---

## 13. Open-Source MNN-Datenquellen

### Nützliche Repositories

| Repository | Inhalt | Lektionen | Nutzbar für |
|-----------|--------|-----------|-------------|
| **vitto4/MinnaNoDS** | Vokabeln (YAML) mit id, kanji, kana, romaji, meaning | 1-50 | Vokabellisten als Referenz |
| **ryu2gaku/minna-no-nihongo** | Vokabeln + Grammatik + Erklärungen (Markdown) | 1-10 | Grammatik-Strukturen als Referenz |
| **Amarthgul/Minna-No-Nihongo-Kaiwa** | Konversationstexte + Audio MP3 | 1-30 | **Nur als Referenz** (Copyright!) |
| **davidluzgouveia/kanji-data** | Kanji mit JLPT-Levels, Stroke Count, Radical | Alle | JLPT-Kanji-Validierung |
| **AnchorI/jlpt-kanji-dictionary** | Nach JLPT-Level strukturiert | Alle | Kanji-Level-Filter |

### Empfehlung
- **MinnaNoDS** als Referenz für Vokabellisten verwenden (Struktur, nicht 1:1 kopieren)
- **Kanji-Data** für die automatische JLPT-Level-Validierung einsetzen
- **KEINE Konversationstexte** aus Open-Source-Repos übernehmen (Copyright-Risiko)

---

## 14. Zusammenfassung: Entscheidungsmatrix

### Vor dem 50-Lektionen-Batch (Blocker)

| # | Aufgabe | Aufwand | Priorität | Status |
|---|---------|---------|-----------|--------|
| 1 | **Pydantic-Schema** für JSON-Validierung erstellen | 2-3h | Hoch | Offen |
| 2 | **Quiz-Duplikat-Schutz** in `generate_quizzes.py` | 30min | Hoch | Offen |
| 3 | **JSON-Dateien für L1-50** erstellen (Vokabeln + Grammatik + Konversationen) | 20-40h | Hoch | Offen |
| 4 | **Eigene Konversationen** statt MNN-Originale (Copyright + Kontrolle) | Teil von #3 | Hoch | Offen |
| 5 | **run_pipeline.py** erstellen | 2-3h | Mittel | Offen |
| 6 | **Import-Tests** ergänzen (Idempotenz) | 2-3h | Mittel | Offen |

### Nach dem Batch (Erweiterungen)

| # | Aufgabe | Aufwand | Priorität |
|---|---------|---------|-----------|
| 7 | Content-Validator in Pipeline integrieren | 3-4h | Mittel |
| 8 | JLPT-Kanji-Level-Prüfung (fugashi + DB) | 4-6h | Mittel |
| 9 | LLM-basierte Japanisch-Validierung | 4-6h | Niedrig |
| 10 | SRS (Spaced Repetition) Feature | 1-2 Tage | Niedrig |
| 11 | Kursübersicht-Paginierung (Book 1/2) | 2-3h | Niedrig |
| 12 | TTS Batch-Optimierung (asyncio + Cache) | 4-6h | Niedrig |

### Kernentscheidung: Woher kommen die Daten?

**Empfohlener Hybrid-Ansatz:**
1. **Vokabeln**: KI-generiert anhand MNN-Curriculum (welche Grammatik/Themen pro Lektion), validiert gegen MinnaNoDS
2. **Grammatik-Erklärungen**: KI-generiert (eigene Texte), da Erklärungen nicht geschützt sind
3. **Konversationen**: KI-generiert mit strikten Constraints (Sprecher, Situation, Grammatik-Fokus, Keigo-Level) → **manuelles Review durch Muttersprachlerin**
4. **Quizzes**: KI-generiert (Gemini), automatisch validiert (Kanji-Level, Struktur), Stichproben-Review

Dieser Ansatz balanciert Geschwindigkeit, Qualität und Rechtssicherheit.

---

## Quellen

### Online-Recherche
- [3A Corporation Official](https://www.3anet.co.jp/en/)
- [MNN Grammar — learnjapaneseaz.com](https://learnjapaneseaz.com/50-lessons-of-grammar-in-minna-no-nihongo.html)
- [MNN Vocabulary Counts — jpdb.io](https://jpdb.io/textbook/9/minna-no-nihongo-i)
- [Google Cloud TTS Pricing](https://cloud.google.com/text-to-speech/pricing)
- [Google Cloud TTS Quotas](https://docs.cloud.google.com/text-to-speech/quotas)
- [Pydantic JSON Schema Docs](https://docs.pydantic.dev/latest/concepts/json_schema/)
- [py-fsrs (PyPI)](https://pypi.org/project/fsrs/)
- [fugashi (MeCab Wrapper)](https://github.com/polm/fugashi)
- [kanji-data (JLPT-Levels)](https://github.com/davidluzgouveia/kanji-data)
- [MinnaNoDS (GitHub)](https://github.com/vitto4/MinnaNoDS)
- [Duolingo AI Pipeline (ZenML)](https://www.zenml.io/llmops-database/ai-powered-lesson-generation-system-for-language-learning)
- [awesome-japanese-nlp-resources](https://github.com/taishi-i/awesome-japanese-nlp-resources)

### Codebase-Analyse
- `scripts/import_mnn.py` — Idempotenz-Check, Seiten-Erstellung, order_index-Logik
- `scripts/generate_tts_audio.py` — Voice-Mapping, ffmpeg-Concat, File-Naming
- `scripts/generate_quizzes.py` — Quiz-Spezifikation pro Seite, Keyword-Extraktion, Dry-Run
- `app/ai_services.py` — Batch-Quiz-Generierung, Prompt-Struktur, Romanisierung
- `app/models.py` — Alle Modelle, Constraints, Relationships
- `app/content_validator.py` — Existierende Validierungslogik (nicht integriert)
- `app/routes.py` — Quiz-Submission, Progress-Tracking, Content-Completion
