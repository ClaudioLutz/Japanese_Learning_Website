# Konzept: Aufgaben-Freischaltung durch Lektionen

**Erstellt:** 20. März 2026
**Kernidee:** Lektionen erzählen die Geschichte und führen ein. Aber das eigentliche Üben passiert in unabhängigen, thematisch sortierten Übungsbereichen, die durch Lektionsfortschritt freigeschaltet werden.

---

## 1. Das Prinzip

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   LEKTION 1: "Willkommen in Japan!"                             │
│   ════════════════════════════════                               │
│   Yuki landet am Flughafen Narita.                              │
│   Geschichte → Erklärung → Dialog → Quiz                        │
│                                                                 │
│   Schaltet frei:                                                │
│   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│   │🔤 Kana   │ │📖 Vokab  │ │🗣️ Sprech │ │📝 Schreib│          │
│   │あいうえお│ │はじめまし│ │Begrüssung│ │あ い う  │          │
│   │かきくけこ│ │て...     │ │üben      │ │え お ... │          │
│   └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘          │
│        │            │            │            │                  │
│        ▼            ▼            ▼            ▼                  │
│   ┌──────────────────────────────────────────────────────┐      │
│   │         ÜBUNGSBEREICHE (unabhängig von Lektion)      │      │
│   │                                                      │      │
│   │  🔤 Kana-Trainer    │ Alle bisher gelernten Kana     │      │
│   │  📖 Vokabel-Box     │ Alle bisher gelernten Wörter   │      │
│   │  🗣️ Sprech-Übungen  │ Dialoge nachsprechen           │      │
│   │  ✍️ Schreib-Übungen │ Zeichen schreiben üben         │      │
│   │  📝 Grammatik-Übung │ Satzstrukturen üben            │      │
│   │  漢 Kanji-Trainer   │ Ab Lektion 11                  │      │
│   └──────────────────────────────────────────────────────┘      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Der Unterschied zum Status Quo:**
- **Heute:** Lektion lernen → Quiz machen → fertig. Will man üben, muss man die ganze Lektion nochmal durchgehen.
- **Neu:** Lektion lernen → Items werden freigeschaltet → Items erscheinen in thematischen Übungsbereichen → unabhängig und beliebig oft übbar, mit SRS-Wiederholung.

---

## 2. Die Übungsbereiche (Skill-Kategorien)

### Übersicht

| # | Bereich | Icon | Inhalt | Freigeschaltet ab |
|---|---------|------|--------|-------------------|
| 1 | **Kana** | 🔤 | Hiragana & Katakana lesen/erkennen | Lektion 1 |
| 2 | **Schreiben** | ✍️ | Kana & Kanji Strichfolge üben | Lektion 1 |
| 3 | **Vokabular** | 📖 | Wörter & Phrasen (JP↔DE) | Lektion 1 |
| 4 | **Sprechen** | 🗣️ | Audio hören & nachsprechen | Lektion 1 |
| 5 | **Grammatik** | 📝 | Satzstrukturen & Partikel | Lektion 8 |
| 6 | **Kanji** | 漢 | Kanji lesen, Bedeutung, Lesungen | Lektion 11 |
| 7 | **Hörverständnis** | 👂 | Audio verstehen, Fragen beantworten | Lektion 4 |

### 2.1 Kana-Trainer 🔤

**Was wird geübt:** Erkennung und Lesung von Hiragana/Katakana

**Übungstypen:**
- Kana → Romaji (Multiple Choice): "Was ist あ?" → a, i, u, e
- Romaji → Kana (Multiple Choice): "Welches ist 'ka'?" → か, き, く, け
- Audio → Kana: Ton hören, richtiges Zeichen wählen
- Kana → Kana (Hiragana↔Katakana Zuordnung)

**Sortierung/Filter:**
- Nach Gruppe: Vokale (あ行), K-Reihe (か行), S-Reihe (さ行), ...
- Nach Beherrschungsgrad: Schwach → Stark
- Dakuten/Handakuten separat filterbar

**Freischaltung pro Lektion:**
```
L1  → あいうえお かきくけこ (10 Hiragana)
L2  → さしすせそ たちつてと (10 Hiragana)
L3  → なにぬねの はひふへほ (10 Hiragana)
L4  → まみむめも やゆよ らりるれろ わをん + Dakuten (16+)
L5  → Wiederholung (keine neuen, aber "Meister"-Übungen)
L6  → アイウエオ ... ト (20 Katakana)
L7  → ナ ... ン (26 Katakana)
```

### 2.2 Schreiben ✍️

**Was wird geübt:** Strichfolge, Zeichenform, Muskel-Gedächtnis

**Übungstypen:**
- Strichfolge-Animation anschauen → nachzeichnen (Canvas/Touch)
- Romaji vorgegeben → Kana/Kanji schreiben
- Aus dem Gedächtnis schreiben (kein Vorbild)

**Sortierung:**
- Nach Zeichentyp: Hiragana → Katakana → Kanji
- Nach Schwierigkeit: Einfach (wenige Striche) → Komplex
- Nach JLPT-Level (bei Kanji)

### 2.3 Vokabular 📖

**Was wird geübt:** Wortschatz aktiv und passiv

**Übungstypen:**
- Japanisch → Deutsch (Karteikarte mit Audio)
- Deutsch → Japanisch (Rückrichtung)
- Audio → Bedeutung (nur hören)
- Lückentext im Beispielsatz
- Zuordnung (Matching: 5 Wörter ↔ 5 Bedeutungen)

**Sortierung/Filter:**
- Nach Lektion (chronologisch gelernt)
- Nach JLPT-Level (N5, N4, ...)
- Nach Thema (Begrüssung, Restaurant, Einkaufen, ...)
- Nach Beherrschungsgrad (SRS-Stufe)
- Alphabetisch (A-Z / あ-ん)

**Freischaltung pro Lektion:**
```
L1  → はじめまして, おはようございます, こんにちは, こんばんは
L2  → ください, すみません, ありがとう, Zahlen 1-10
L3  → これ, それ, あれ, です, ...
...
```

### 2.4 Sprechen 🗣️

**Was wird geübt:** Aussprache, Intonation, Flüssigkeit

**Übungstypen:**
- Audio hören → nachsprechen (mit TTS-Vergleich)
- Dialog-Zeilen nachsprechen (Rollenspiel)
- Wörter/Phrasen korrekt betonen
- Shadowing: Audio läuft, Lerner spricht gleichzeitig mit

**Sortierung:**
- Nach Lektion/Dialog
- Nach Schwierigkeit (einzelne Wörter → ganze Sätze → Dialoge)
- Nach Situation (Begrüssung, Restaurant, Einkaufen, ...)

### 2.5 Grammatik 📝

**Was wird geübt:** Satzstrukturen, Partikel, Konjugationen

**Übungstypen:**
- Lückentext: "ラーメン ___ ください" → を
- Satzteile ordnen: [を] [ラーメン] [ください] → richtige Reihenfolge
- Übersetzung: DE→JP Satz bilden
- Richtig/Falsch: Ist dieser Satz korrekt?
- Erklärung lesen → Beispielsätze bearbeiten

**Sortierung:**
- Nach Grammatikpunkt (chronologisch eingeführt)
- Nach JLPT-Level
- Nach Kategorie (Partikel, Verbformen, Satzenden, ...)

### 2.6 Kanji 漢

**Was wird geübt:** Erkennung, Bedeutung, On'yomi/Kun'yomi

**Übungstypen:**
- Kanji → Bedeutung (Multiple Choice)
- Bedeutung → Kanji
- Kanji → Lesung (On/Kun)
- Kanji im Kontext (Wort erkennen)
- Radikal-Zerlegung
- Strichfolge schreiben

**Sortierung:**
- Nach Lektion (chronologisch)
- Nach JLPT-Level
- Nach Radikal/Strichzahl
- Nach Themengruppe (日月火水木金土 = Wochentage)
- Nach Beherrschungsgrad

### 2.7 Hörverständnis 👂

**Was wird geübt:** Gesprochenes Japanisch verstehen

**Übungstypen:**
- Satz hören → richtige Übersetzung wählen
- Dialog hören → Fragen beantworten
- Zahlen/Preise hören → eintippen
- Diktat: hören und aufschreiben (Kana)

---

## 3. Freischalt-Mechanik: Wie es funktioniert

### 3.1 Wann werden Items freigeschaltet?

```
Lektion starten
    │
    ├── Seite 1 (Narrativ) besucht
    │   └── Keine Freischaltung (nur Story)
    │
    ├── Seite 2 (Kana einführen) abgeschlossen
    │   └── ✅ Kana-Items freigeschaltet!
    │       → Erscheinen sofort im Kana-Trainer
    │       → Erscheinen im Schreib-Übungen
    │
    ├── Seite 3 (Vokabeln einführen) abgeschlossen
    │   └── ✅ Vokabel-Items freigeschaltet!
    │       → Erscheinen in der Vokabel-Box
    │       → Audio erscheint in Sprech-Übungen
    │
    ├── Seite 4 (Dialog) abgeschlossen
    │   └── ✅ Dialog-Items freigeschaltet!
    │       → Dialog erscheint in Sprech-Übungen
    │       → Audio in Hörverständnis
    │
    └── Seite 5-6 (Quiz) bestanden
        └── ✅ Lektion abgeschlossen!
            → Alle Items der Lektion dauerhaft verfügbar
            → SRS-Wiederholung startet für alle Items
            → Nächste Lektion wird freigeschaltet
```

### 3.2 Zwei Freischalt-Modi

**Option A: Progressiv (empfohlen)**
Items werden freigeschaltet, sobald die entsprechende Seite abgeschlossen ist. Der Lerner kann schon während der Lektion üben.

**Option B: Nach Lektionsabschluss**
Alle Items einer Lektion werden erst nach bestandenem Quiz freigeschaltet. Einfacher zu implementieren, aber weniger flexibel.

**Empfehlung:** Start mit Option B (einfacher), später auf Option A upgraden.

### 3.3 Item-Lifecycle

```
                    ┌──────────────┐
                    │   LOCKED     │  Item existiert in der Lektion,
                    │   (gesperrt) │  aber User hat Lektion noch
                    └──────┬───────┘  nicht abgeschlossen
                           │
                    Lektion abgeschlossen
                           │
                    ┌──────▼───────┐
                    │  UNLOCKED    │  Item erscheint im Übungsbereich
                    │  (neu)       │  → SRS startet bei Stufe 1
                    └──────┬───────┘
                           │
                    Erste Übung korrekt
                           │
                    ┌──────▼───────┐
                    │  LEARNING    │  SRS-Intervalle werden grösser
                    │  (am Lernen) │  bei korrekten Antworten
                    └──────┬───────┘
                           │
                    Mehrfach korrekt über Wochen
                           │
                    ┌──────▼───────┐
                    │  MASTERED    │  Seltene Wiederholung
                    │  (gemeistert)│  (alle 1-4 Monate)
                    └──────┬───────┘
                           │
                    4 Monate ohne Fehler
                           │
                    ┌──────▼───────┐
                    │  BURNED      │  Aus der Wiederholung entfernt
                    │  (verbrannt) │  → "Ich kann das."
                    └──────────────┘

    Bei Fehler: Item wird 1-2 Stufen zurückgesetzt
```

---

## 4. Dashboard-Integration

### 4.1 Übungsbereiche auf dem Dashboard

```
┌──────────────────────────────────────────────────────────────┐
│  ── Deine Übungsbereiche ─────────────────────────────────── │
│                                                              │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐               │
│  │ 🔤 Kana    │ │ 📖 Vokab.  │ │ ✍️ Schreib. │               │
│  │            │ │            │ │            │               │
│  │ 10/46      │ │ 4/∞        │ │ 10 Zeichen │               │
│  │ ██░░░ 22%  │ │ 3 fällig   │ │ 2 fällig   │               │
│  │            │ │            │ │            │               │
│  │ [Üben →]   │ │ [Üben →]   │ │ [Üben →]   │               │
│  └────────────┘ └────────────┘ └────────────┘               │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐               │
│  │ 🗣️ Sprech. │ │ 📝 Gramm.  │ │ 漢 Kanji   │               │
│  │            │ │            │ │            │               │
│  │ 5 Dialoge  │ │ 🔒         │ │ 🔒         │               │
│  │ 1 fällig   │ │ Ab L8      │ │ Ab L11     │               │
│  │            │ │            │ │            │               │
│  │ [Üben →]   │ │ [Gesperrt] │ │ [Gesperrt] │               │
│  └────────────┘ └────────────┘ └────────────┘               │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 4.2 Innerhalb eines Übungsbereichs

Beispiel: Vokabular-Box

```
┌──────────────────────────────────────────────────────────────┐
│  ← Dashboard                                                │
│  📖 Vokabular                                                │
│  ──────────────────────────────────────────────────────────  │
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  🔔 4 Wörter fällig zur Wiederholung                    │ │
│  │  [Wiederholung starten →]                               │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                              │
│  Filter: [Alle ▼] [Nach Lektion ▼] [Nach Thema ▼] [JLPT ▼] │
│  Sortierung: [Chronologisch ▼]                               │
│                                                              │
│  ── Lektion 1: Willkommen in Japan! ────────────────────── │
│                                                              │
│  ┌──────────────────────────────┐  SRS-Stufe    Status      │
│  │ はじめまして                  │  ████░░ Kenner  ✅ Gelernt │
│  │ Freut mich (Sie kennenzulernen) │                        │
│  │ 🔊 [Audio]                    │                          │
│  └──────────────────────────────┘                            │
│                                                              │
│  ┌──────────────────────────────┐                            │
│  │ おはようございます             │  ██░░░░ Lehrling ⚡ Fällig │
│  │ Guten Morgen                  │                           │
│  │ 🔊 [Audio]                    │                          │
│  └──────────────────────────────┘                            │
│                                                              │
│  ┌──────────────────────────────┐                            │
│  │ こんにちは                    │  █████░ Meister  ✅ Gelernt│
│  │ Guten Tag / Hallo             │                           │
│  │ 🔊 [Audio]                    │                          │
│  └──────────────────────────────┘                            │
│                                                              │
│  ── Lektion 2: Im Taxi ──────────── 🔒 Noch nicht gelernt  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 4.3 Übungs-Session

Wenn der User "Üben" oder "Wiederholung starten" klickt:

```
┌──────────────────────────────────────────────────────────────┐
│  📖 Vokabel-Übung          Fortschritt: ███░░░░░ 3/8        │
│  ──────────────────────────────────────────────────────────  │
│                                                              │
│  Was bedeutet:                                               │
│                                                              │
│        ┌──────────────────────────┐                          │
│        │                          │                          │
│        │    おはようございます      │                          │
│        │                          │                          │
│        │    🔊 Audio abspielen     │                          │
│        │                          │                          │
│        └──────────────────────────┘                          │
│                                                              │
│  ┌─────────────────┐  ┌─────────────────┐                   │
│  │  Guten Tag       │  │  Guten Morgen ✓ │                   │
│  └─────────────────┘  └─────────────────┘                   │
│  ┌─────────────────┐  ┌─────────────────┐                   │
│  │  Guten Abend     │  │  Auf Wiedersehen │                   │
│  └─────────────────┘  └─────────────────┘                   │
│                                                              │
│  ──────────────────────────────────────────────────────────  │
│  ✅ Richtig! +5 XP                                           │
│  Nächste Review in: 3 Tage                                   │
│                                                              │
│                               [Weiter →]                     │
└──────────────────────────────────────────────────────────────┘
```

---

## 5. Datenmodell: Was sich ändert

### 5.1 Bestehende Tabellen die wir nutzen

Die folgenden Tabellen existieren bereits und werden als Referenzdaten für die Übungsbereiche verwendet:

| Tabelle | Übungsbereich | Bereits vorhanden |
|---------|--------------|-------------------|
| `Kana` | Kana-Trainer, Schreiben | ✅ character, romanization, type |
| `Kanji` | Kanji-Trainer, Schreiben | ✅ character, meaning, onyomi, kunyomi |
| `Vocabulary` | Vokabular, Sprechen | ✅ word, reading, meaning, audio_url |
| `Grammar` | Grammatik | ✅ title, explanation, structure |
| `LessonContent` | Verknüpfung Lektion↔Item | ✅ content_type, content_id |

### 5.2 Neue Tabelle: `SkillItem` (Kern des Systems)

Verknüpft Items mit Übungsbereichen und definiert, welche Lektion sie freischaltet.

```
SkillItem
─────────
  id                  (PK)
  skill_category      (String)    # 'kana', 'writing', 'vocabulary',
                                  # 'speaking', 'grammar', 'kanji', 'listening'
  item_type           (String)    # 'kana', 'kanji', 'vocabulary', 'grammar',
                                  # 'dialogue', 'audio'
  item_id             (Integer)   # FK → Kana.id / Vocabulary.id / etc.
  unlocked_by_lesson  (FK → Lesson)  # Welche Lektion schaltet frei
  unlocked_at_page    (Integer)      # Optional: ab welcher Seite (für progressive Freischaltung)
  difficulty_order    (Integer)      # Reihenfolge innerhalb des Bereichs
  tags                (JSON)         # z.B. ["grüssung", "höflich", "N5"]
  exercise_types      (JSON)         # z.B. ["mc_jp_de", "mc_de_jp", "audio", "fill_blank"]
  extra_data          (JSON)         # Bereichsspezifische Daten (z.B. Dialog-Text, Schreibanleitung)
```

**Beispiel-Einträge:**

| id | skill_category | item_type | item_id | unlocked_by_lesson | tags |
|----|---------------|-----------|---------|-------------------|------|
| 1 | kana | kana | 1 (あ) | L1 | ["vowel", "hiragana"] |
| 2 | writing | kana | 1 (あ) | L1 | ["hiragana", "3_strokes"] |
| 3 | vocabulary | vocabulary | 5 (はじめまして) | L1 | ["greeting", "N5"] |
| 4 | speaking | vocabulary | 5 (はじめまして) | L1 | ["greeting", "formal"] |
| 5 | grammar | grammar | 1 (を-Partikel) | L8 | ["particle", "N5"] |
| 6 | kanji | kanji | 1 (日) | L11 | ["N5", "time", "1_radical"] |

**Wichtig:** Ein Item kann in MEHREREN Übungsbereichen erscheinen! `はじめまして` ist sowohl ein Vokabel-Item als auch ein Sprech-Item. Das Kana `あ` ist sowohl ein Lese-Item als auch ein Schreib-Item.

### 5.3 Neue Tabelle: `UserSkillProgress` (SRS pro Item)

Trackt den Lernfortschritt jedes Users für jedes freigeschaltete Item.

```
UserSkillProgress
─────────────────
  id                  (PK)
  user_id             (FK → User)
  skill_item_id       (FK → SkillItem)
  status              (String)    # 'locked', 'unlocked', 'learning', 'mastered', 'burned'
  srs_stage           (Integer)   # 0-8 (0=locked, 1=unlocked/new, 2-8=SRS stages)
  next_review_at      (DateTime)  # Wann ist nächste Wiederholung fällig?
  last_reviewed_at    (DateTime)  # Letzte Übung
  correct_count       (Integer)   # Anzahl korrekte Antworten
  incorrect_count     (Integer)   # Anzahl falsche Antworten
  unlocked_at         (DateTime)  # Wann freigeschaltet
  burned_at           (DateTime)  # Wann "verbrannt" (abgeschlossen)

  UNIQUE(user_id, skill_item_id)
```

### 5.4 Neue Tabelle: `SkillCategory` (Metadata für Übungsbereiche)

```
SkillCategory
─────────────
  id                  (PK)
  slug                (String, unique)  # 'kana', 'vocabulary', 'writing', ...
  name_de             (String)          # 'Kana-Trainer'
  name_en             (String)          # 'Kana Trainer'
  icon                (String)          # '🔤' oder Font-Awesome-Class
  description_de      (Text)
  color               (String)          # Hex-Farbe für UI
  order_index         (Integer)         # Anzeigereihenfolge
  min_lesson_required (FK → Lesson)     # Ab welcher Lektion sichtbar
  is_active           (Boolean)         # Feature-Flag
```

### 5.5 Änderungen an bestehenden Tabellen

```
User — Erweiterungen:
  + xp_total            (Integer, default 0)
  + current_streak      (Integer, default 0)
  + longest_streak      (Integer, default 0)
  + last_activity_date  (Date, nullable)
  + daily_goal          (Integer, default 5)   # Übungen pro Tag

UserDailyActivity — Neue Tabelle:
  + id                  (PK)
  + user_id             (FK → User)
  + date                (Date)
  + xp_earned           (Integer)
  + exercises_completed (Integer)
  + reviews_completed   (Integer)
  + lessons_completed   (Integer)
  + accuracy            (Float)   # 0.0 - 1.0
  UNIQUE(user_id, date)
```

---

## 6. Wie die Freischaltung technisch funktioniert

### 6.1 Beim Erstellen einer Lektion (Admin/Script)

Wenn eine Premium-Lektion erstellt wird (z.B. `premium_create_lesson_01_willkommen.py`), werden gleichzeitig die `SkillItem`-Einträge erzeugt:

```python
# Beispiel: Lektion 1 erstellen
lesson = Lesson(title="Willkommen in Japan!", ...)

# Kana あ in der Lektion einführen (wie bisher)
content = LessonContent(lesson=lesson, content_type='kana', content_id=kana_a.id, ...)

# NEU: Skill-Items registrieren
SkillItem(skill_category='kana', item_type='kana', item_id=kana_a.id,
          unlocked_by_lesson=lesson.id, tags=["vowel", "hiragana"],
          exercise_types=["mc_kana_romaji", "mc_romaji_kana", "audio_kana"])

SkillItem(skill_category='writing', item_type='kana', item_id=kana_a.id,
          unlocked_by_lesson=lesson.id, tags=["hiragana", "3_strokes"],
          exercise_types=["stroke_order", "draw_from_memory"])
```

### 6.2 Beim Abschliessen einer Lektion (User)

```python
def on_lesson_completed(user, lesson):
    """Wird aufgerufen wenn ein User eine Lektion abschliesst."""

    # Alle SkillItems finden, die von dieser Lektion freigeschaltet werden
    skill_items = SkillItem.query.filter_by(unlocked_by_lesson=lesson.id).all()

    for item in skill_items:
        # Prüfen ob schon freigeschaltet (Idempotenz)
        existing = UserSkillProgress.query.filter_by(
            user_id=user.id, skill_item_id=item.id
        ).first()

        if not existing:
            progress = UserSkillProgress(
                user_id=user.id,
                skill_item_id=item.id,
                status='unlocked',
                srs_stage=1,
                next_review_at=datetime.utcnow(),  # Sofort übbar
                unlocked_at=datetime.utcnow()
            )
            db.session.add(progress)

    # XP vergeben
    user.xp_total += 20
    # Streak aktualisieren
    update_streak(user)

    db.session.commit()
```

### 6.3 Übungs-Session starten

```python
def get_pending_reviews(user, skill_category=None, limit=10):
    """Holt fällige Reviews für einen Übungsbereich."""

    query = UserSkillProgress.query.filter(
        UserSkillProgress.user_id == user.id,
        UserSkillProgress.status.in_(['unlocked', 'learning']),
        UserSkillProgress.next_review_at <= datetime.utcnow()
    )

    if skill_category:
        query = query.join(SkillItem).filter(
            SkillItem.skill_category == skill_category
        )

    # Priorität: Neue Items (unlocked) zuerst, dann älteste Reviews
    return query.order_by(
        UserSkillProgress.status.desc(),  # 'unlocked' vor 'learning'
        UserSkillProgress.next_review_at.asc()
    ).limit(limit).all()
```

### 6.4 SRS-Update nach Antwort

```python
SRS_INTERVALS = {
    1: timedelta(hours=4),      # Lehrling I
    2: timedelta(hours=8),      # Lehrling II
    3: timedelta(days=1),       # Lehrling III
    4: timedelta(days=3),       # Kenner I
    5: timedelta(weeks=1),      # Kenner II
    6: timedelta(weeks=2),      # Meister
    7: timedelta(days=30),      # Erleuchtet
    8: timedelta(days=120),     # Verbrannt
}

def process_review_answer(user_skill_progress, is_correct):
    """Aktualisiert SRS-Stufe basierend auf Antwort."""

    if is_correct:
        user_skill_progress.correct_count += 1
        user_skill_progress.srs_stage = min(8, user_skill_progress.srs_stage + 1)

        if user_skill_progress.srs_stage >= 8:
            user_skill_progress.status = 'burned'
            user_skill_progress.burned_at = datetime.utcnow()
        elif user_skill_progress.srs_stage >= 4:
            user_skill_progress.status = 'mastered'
        else:
            user_skill_progress.status = 'learning'
    else:
        user_skill_progress.incorrect_count += 1
        # Zurücksetzen: 2 Stufen runter, aber mindestens 1
        user_skill_progress.srs_stage = max(1, user_skill_progress.srs_stage - 2)
        user_skill_progress.status = 'learning'

    # Nächste Review berechnen
    interval = SRS_INTERVALS.get(user_skill_progress.srs_stage, timedelta(hours=4))
    user_skill_progress.next_review_at = datetime.utcnow() + interval
    user_skill_progress.last_reviewed_at = datetime.utcnow()
```

---

## 7. Navigation: Gesamtbild

```
┌──────────────────────────────────────────────────────────┐
│  HAUPTNAVIGATION                                         │
│  ════════════════                                        │
│                                                          │
│  🏠 Dashboard ──────── Übersicht, Streak, nächste Aktion │
│  │                                                       │
│  ├── 📚 Lernpfad ──── Yukis Reise (Lektionen 1-36)      │
│  │   └── Lektion X ── Geschichte + Einführung            │
│  │                                                       │
│  ├── 💪 Übungsbereiche                                   │
│  │   ├── 🔤 Kana ──── Lesen & Erkennen                  │
│  │   ├── ✍️ Schreiben  Strichfolge & Form                │
│  │   ├── 📖 Vokabular  Wörter & Phrasen                 │
│  │   ├── 🗣️ Sprechen   Aussprache & Dialoge             │
│  │   ├── 📝 Grammatik  Satzstrukturen                   │
│  │   ├── 漢 Kanji ──── Zeichen & Lesungen               │
│  │   └── 👂 Hören ──── Hörverständnis                   │
│  │                                                       │
│  ├── 📊 Statistiken ── Detaillierte Fortschrittsanalyse  │
│  │                                                       │
│  └── ⚙️ Einstellungen  Tages-Ziel, Benachrichtigungen   │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## 8. Beispiel: Was passiert nach Lektion 1?

**Vor Lektion 1:** Alle Übungsbereiche sind leer/gesperrt.

**Nach Abschluss von Lektion 1:** Der User sieht auf dem Dashboard:

```
🔤 Kana-Trainer       → 10 neue Items (あいうえお かきくけこ)
✍️ Schreiben          → 10 neue Zeichen zum Üben
📖 Vokabular          → 4 neue Wörter (はじめまして, おはよう..., こんにちは, こんばんは)
🗣️ Sprechen           → 5 Dialog-Zeilen + 4 Begrüssungen zum Nachsprechen
📝 Grammatik          → 🔒 (erst ab L8)
漢 Kanji              → 🔒 (erst ab L11)
👂 Hörverständnis     → 🔒 (erst ab L4)
```

**Am nächsten Tag:** SRS meldet sich:
```
"Du hast 8 fällige Wiederholungen!"
  - 4× Kana (あいうえ → nach 4h schon fällig geworden)
  - 2× Vokabeln
  - 2× Sprechen
```

**Nach 1 Woche (Lektionen 1-3 abgeschlossen):**
```
🔤 Kana-Trainer       → 30 Items (davon 10 auf Stufe "Kenner", 20 "Lehrling")
✍️ Schreiben          → 30 Zeichen
📖 Vokabular          → 18 Wörter (davon 4 "Kenner", 14 "Lehrling")
🗣️ Sprechen           → 15 Phrasen/Dialogzeilen
📝 Grammatik          → 🔒
漢 Kanji              → 🔒
👂 Hörverständnis     → 3 Hörübungen (ab L4 freigeschaltet nach nächster Lektion!)
```

---

## 9. Zusammenfassung: Was macht diesen Ansatz besonders?

| Aspekt | Traditionell | Unser Ansatz |
|--------|-------------|--------------|
| **Lernen** | Lektion durcharbeiten, Quiz, fertig | Lektion führt ein, Übungsbereiche vertiefen |
| **Wiederholung** | Ganze Lektion nochmal | Einzelne Items per SRS, automatisch geplant |
| **Übersicht** | "Lektion 5 abgeschlossen" | "24 Kana gelernt, 18 Vokabeln, 2 Grammatikpunkte" |
| **Motivation** | Lineare Progression | Multi-dimensionaler Fortschritt sichtbar |
| **Flexibilität** | Alles oder nichts | Schwache Bereiche gezielt üben |
| **Langzeit** | Nach 3 Wochen alles vergessen | SRS sorgt für dauerhafte Erinnerung |

**Der Lernzyklus:**
1. 📚 **Lektion** → Geschichte erleben, neues Material kennenlernen
2. 🔓 **Freischaltung** → Items erscheinen in Übungsbereichen
3. 💪 **Üben** → Gezielte Übung nach Kategorie
4. 🔄 **SRS** → Automatische Wiederholung zur richtigen Zeit
5. 🏆 **Meistern** → Item "verbrannt" = dauerhaft gelernt

---

## 10. Implementierungsreihenfolge

### Phase 1: Grundgerüst (Priorität)
1. DB-Tabellen: `SkillItem`, `UserSkillProgress`, `SkillCategory`
2. Migration ausführen
3. Freischalt-Logik in `on_lesson_completed()`
4. Übungsbereich-Seiten (Kana, Vokabular) — nur Auflistung der freigeschalteten Items
5. Einfache MC-Übung pro Bereich

### Phase 2: SRS & Übungen
6. SRS-Algorithmus implementieren
7. Review-Queue ("X fällig")
8. Verschiedene Übungstypen pro Bereich
9. XP-Vergabe bei Übungen
10. Dashboard-Integration (Kacheln mit "fällig"-Zähler)

### Phase 3: Erweiterte Features
11. Schreib-Übungen (Canvas)
12. Sprech-Übungen (Audio-Vergleich)
13. Statistiken pro Bereich
14. Streak-System
15. Heatmap

### Phase 4: Polishing
16. Animationen und Microinteractions
17. Mobile-Optimierung
18. Badges für Bereichs-Meilensteine
19. Offline-Modus
