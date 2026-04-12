# Konzept: Persistentes Kartenlernsystem mit Spaced Repetition

> **Erstellt:** 12. April 2026
> **Status:** Konzeptphase — Recherche & Optionen
> **Ziel:** Kartenfortschritt persistent in der DB speichern und ein wissenschaftlich fundiertes Wiederholungssystem einführen

---

## 1. Ist-Zustand: Aktuelle Implementierung

### Wie funktioniert das Kartensystem heute?

Das Deck-Karussell in `lesson_view.html` (Zeilen 2416–2892) erkennt automatisch Seiten mit 2+ Flip-Cards und aktiviert den Deck-Modus.

**Fortschritts-Speicherung: nur `localStorage`**
```javascript
// Key: deck_{lessonId}_page{pageIndex}
{
    total: 39,
    pending: [3, 7, 12, ...],   // Indizes noch zu lernender Karten
    learned: 14,
    timestamp: 1712920000000
}
```

**Bewertung: 3 Stufen**
| Button     | Aktion                                          |
|------------|------------------------------------------------|
| Nochmal    | Karte bleibt im Deck, wird 2–5 Positionen weiter hinten eingefügt |
| Schwer     | Karte wird entfernt, `markContentComplete()` aufgerufen |
| Gewusst    | Identisch mit "Schwer" — kein Unterschied im Verhalten |

### Probleme des aktuellen Systems

| Problem | Auswirkung |
|---------|-----------|
| **Kein persistenter Fortschritt** | Browser-Cache löschen = alles verloren |
| **Kein SRS-Algorithmus** | Keine intelligente Wiederholung nach Tagen/Wochen |
| **"Schwer" = "Gewusst"** | Bewertung hat keinen echten Einfluss auf Wiederholung |
| **Kein geräteübergreifendes Lernen** | Fortschritt nur im aktuellen Browser |
| **Kein Review-System** | Keine Möglichkeit, vergessene Karten gezielt aufzufrischen |
| **Keine Lernstatistiken** | User sieht nicht, wie gut er langfristig lernt |

### Bestehende DB-Infrastruktur

Das `UserLessonProgress`-Modell (`models.py:518–589`) speichert bereits:
- `content_progress` (JSON): `{"content_id": true/false}`
- `progress_percentage`, `time_spent`, `last_accessed`

Allerdings: Nur ein binärer Zustand (gelernt/nicht gelernt), keine SRS-Daten.

---

## 2. Algorithmen-Vergleich

### Option A: Leitner-System (Boxen-Prinzip)

```
Box 1: jeden Tag    → Box 2: alle 2 Tage → Box 3: alle 4 Tage → ...
Falsch → zurück zu Box 1
```

| Pro | Contra |
|-----|--------|
| Extrem einfach zu implementieren | Fixe Intervalle, keine Personalisierung |
| Intuitiv verständlich für User | Ineffizient bei vielen Karten |
| Kein ML/Optimizer nötig | Nicht State of the Art |

**Aufwand:** ~2–3 Tage Implementierung
**Empfehlung:** Nur als Fallback oder für MVP

---

### Option B: SM-2 (SuperMemo-2)

Der klassische Algorithmus seit 1987 — Basis von Anki.

**Funktionsweise:**
```
Nach jeder Bewertung (0–5):
  - quality < 3: Karte zurücksetzen (Interval = 1)
  - quality >= 3: neues Interval berechnen
    - Interval(1) = 1 Tag
    - Interval(2) = 6 Tage
    - Interval(n) = Interval(n-1) × EF

EF (Easiness Factor) wird pro Karte angepasst:
  EF' = EF + (0.1 - (5 - quality) × (0.08 + (5 - quality) × 0.02))
  Minimum: 1.3
```

**Datenmodell pro Karte:**
```python
easiness_factor: float  # [1.3, ∞], Start: 2.5
interval: int           # Tage bis nächste Review
repetitions: int        # Erfolgreiche Wiederholungen in Folge
next_review: datetime   # Fälligkeitsdatum
```

| Pro | Contra |
|-----|--------|
| Bewährt seit 35+ Jahren | EF ist schlechter Schwierigkeitsindikator |
| Einfach zu implementieren | Keine Personalisierung auf User-Ebene |
| Python-Libs verfügbar (`supermemo2`) | 20–30% mehr Reviews nötig als FSRS |
| Anki-kompatibel | Keine Parameter-Optimierung |

**Aufwand:** ~3–5 Tage Implementierung
**Python-Bibliothek:** `supermemo2` auf PyPI

---

### Option C: FSRS (Free Spaced Repetition Scheduler) — EMPFOHLEN

Der modernste Algorithmus (2022–2026), basiert auf dem DSR-Gedächtnismodell.

**Drei Kernvariablen pro Karte (DSR-Modell):**

| Variable | Bedeutung | Wertebereich |
|----------|-----------|-------------|
| **D** (Difficulty) | Wie schwer die Karte ist | [1, 10] |
| **S** (Stability) | Zeit in Tagen bis Erinnerungswahrscheinlichkeit auf 90% fällt | [0, ∞] |
| **R** (Retrievability) | Aktuelle Wahrscheinlichkeit sich zu erinnern | [0, 1] |

**Bewertungsstufen:**
```
1 = Again  (Vergessen)
2 = Hard   (Schwer, aber erinnert)
3 = Good   (Korrekt mit normalem Aufwand)
4 = Easy   (Sofort gewusst)
```

**Intervall-Berechnung:**
```python
next_interval = (stability / FACTOR) * ((desired_retention ** (1/DECAY)) - 1)
# desired_retention: Standard 90% — User kann 80–95% wählen
```

**Parameter-Optimierung:**
- FSRS nutzt 21 trainierbare Parameter
- Nach ~1'000 Reviews: Optimizer kann Parameter auf individuelles Lernverhalten anpassen
- Ergebnis: 20–30% weniger Reviews für gleiche Retention gegenüber SM-2

| Pro | Contra |
|-----|--------|
| State of the Art (2024–2026) | Komplexer zu implementieren |
| 20–30% effizienter als SM-2 | Optimizer braucht ~1'000 Reviews |
| Personalisierbar pro User | Mehr Speicherplatz pro Karte |
| `desired_retention` einstellbar | |
| Python-Lib verfügbar (`fsrs`) | |
| Von Anki offiziell übernommen | |

**Aufwand:** ~5–8 Tage Implementierung
**Python-Bibliothek:** `fsrs` auf PyPI (v6.3.1, aktuell)

---

### Vergleichstabelle

| Kriterium | Leitner | SM-2 | FSRS |
|-----------|---------|------|------|
| Effizienz | ★★☆ | ★★★ | ★★★★★ |
| Implementierungsaufwand | ★★★★★ | ★★★★ | ★★★ |
| Personalisierung | ✗ | ✗ | ✓ |
| Python-Library | Manuell | `supermemo2` | `fsrs` |
| State of the Art | ✗ | ✗ | ✓ |
| Wissenschaftliche Basis | Gering | Mittel | Hoch |

**Empfehlung: FSRS** — Der Mehraufwand gegenüber SM-2 ist durch die `fsrs`-Bibliothek minimal, die Vorteile sind erheblich.

---

## 3. Datenmodell-Entwurf

### Neue Modelle

```python
class CardReviewState(db.Model):
    """SRS-Zustand pro User + Content-Item"""
    __tablename__ = 'card_review_state'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content_id = db.Column(db.Integer, db.ForeignKey('lesson_content.id'), nullable=False)
    
    # FSRS-Kernfelder (DSR-Modell)
    difficulty = db.Column(db.Float, default=5.0)       # [1, 10]
    stability = db.Column(db.Float, default=0.0)        # Tage
    retrievability = db.Column(db.Float, default=1.0)   # [0, 1]
    
    # Scheduling
    status = db.Column(db.String(20), default='new')    # new, learning, review, relearning
    due_date = db.Column(db.DateTime)                   # Nächste Wiederholung
    last_reviewed = db.Column(db.DateTime)
    
    # Statistiken
    reps = db.Column(db.Integer, default=0)             # Erfolgreiche Reviews
    lapses = db.Column(db.Integer, default=0)           # Vergessen-Count
    
    # FSRS-State (JSON für Bibliotheks-Kompatibilität)
    fsrs_state = db.Column(db.Text)                     # Serialisierter FSRS-Card-State
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'content_id', name='uq_user_content_review'),
    )


class ReviewLog(db.Model):
    """Protokoll jeder einzelnen Bewertung — Basis für Optimizer"""
    __tablename__ = 'review_log'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content_id = db.Column(db.Integer, db.ForeignKey('lesson_content.id'), nullable=False)
    
    rating = db.Column(db.Integer, nullable=False)      # 1=Again, 2=Hard, 3=Good, 4=Easy
    reviewed_at = db.Column(db.DateTime, default=datetime.utcnow)
    time_taken_ms = db.Column(db.Integer)               # Antwortzeit in Millisekunden
    
    # Snapshot vor dem Review (für Optimizer)
    previous_stability = db.Column(db.Float)
    previous_difficulty = db.Column(db.Float)
    previous_interval = db.Column(db.Integer)            # Tage seit letztem Review
    new_interval = db.Column(db.Integer)                 # Berechnetes neues Intervall


class UserSRSSettings(db.Model):
    """Persönliche SRS-Einstellungen pro User"""
    __tablename__ = 'user_srs_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    
    desired_retention = db.Column(db.Float, default=0.9)  # 90% Standard
    daily_new_cards = db.Column(db.Integer, default=20)    # Neue Karten pro Tag
    daily_review_limit = db.Column(db.Integer, default=100) # Max Reviews pro Tag
    
    # FSRS Optimizer Parameters (JSON, 21 Parameter)
    fsrs_parameters = db.Column(db.Text)                   # Nach 1000 Reviews optimierbar
    
    # Streak-Tracking
    current_streak = db.Column(db.Integer, default=0)
    longest_streak = db.Column(db.Integer, default=0)
    last_study_date = db.Column(db.Date)
```

### Erweiterung bestehender Modelle

```python
# User-Modell erweitern:
class User(db.Model):
    # ... bestehende Felder ...
    srs_settings = db.relationship('UserSRSSettings', uselist=False, backref='user')
    card_states = db.relationship('CardReviewState', backref='user', lazy='dynamic')
    review_logs = db.relationship('ReviewLog', backref='user', lazy='dynamic')
```

---

## 4. Feature-Konzept: Review-Seite

### 4.1 Neue Route: `/review` — Tägliche Wiederholung

Eine zentrale Seite, auf der der User alle fälligen Karten aus allen Lektionen wiederholt.

**Mockup-Beschreibung:**

```
┌──────────────────────────────────────────────────┐
│  Tägliche Wiederholung          📊 Statistiken   │
├──────────────────────────────────────────────────┤
│                                                  │
│  🔥 Streak: 7 Tage     ⏱ Heute: 12 min         │
│  📦 Fällig: 25          ✅ Erledigt: 18/43       │
│                                                  │
│  ┌────────────────────────────────────────────┐  │
│  │                                            │  │
│  │              あ                            │  │
│  │                                            │  │
│  │         Click to flip                      │  │
│  └────────────────────────────────────────────┘  │
│                                                  │
│   [Again 1]   [Hard 2]   [Good 3]   [Easy 4]    │
│    <1 Min      <10 Min     4 Tage     12 Tage    │
│                                                  │
│  Lektion: Hiragana Basics  │  Typ: Kana          │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  42%           │
└──────────────────────────────────────────────────┘
```

**Kernfunktionen:**
1. **Gemischte Karten** aus allen gelernten Lektionen
2. **4-Stufen-Bewertung** mit angezeigtem nächsten Intervall
3. **Fortschrittsbalken** für aktuelle Session
4. **Streak-Anzeige** (Gamification)
5. **Kontext-Info**: Aus welcher Lektion stammt die Karte?
6. **Audio-Button** für Aussprache (TTS)

### 4.2 Neue Route: `/review/stats` — Lernstatistiken

**Dashboard mit:**
- **Heatmap**: Tägliche Review-Aktivität (wie GitHub Contributions)
- **Retention-Graph**: Wie gut erinnert der User über die Zeit?
- **Schwierigste Karten**: Top 10 mit höchstem Lapse-Count
- **Forecast**: Wie viele Reviews kommen in den nächsten 7 Tagen?
- **Verteilung**: Pie-Chart der Karten nach Status (new/learning/review/mature)

### 4.3 Neue Route: `/review/browse` — Karten durchsuchen

**Funktionen:**
- Alle Karten nach Lektion/Typ filtern
- Sortieren nach: Schwierigkeit, nächstes Review, Lapses
- Karten manuell suspendieren/reaktivieren
- Bulk-Aktionen: "Alle Karten dieser Lektion zurücksetzen"

### 4.4 Integration in bestehende Lektion

Das bestehende Deck-Karussell in `lesson_view.html` wird erweitert:
- Bewertung wird an Backend gesendet (nicht nur localStorage)
- 4 Bewertungsstufen statt 3 (Again/Hard/Good/Easy)
- Nächstes Intervall unter jedem Button anzeigen
- "Schwer" und "Gewusst" bekommen unterschiedliches Verhalten

---

## 5. API-Endpoints

```
POST /api/review/rate
  Body: { content_id, rating (1-4), time_taken_ms }
  → Berechnet neuen FSRS-State, speichert ReviewLog
  → Returns: { next_interval, new_due_date, cards_remaining }

GET  /api/review/due
  Query: ?limit=50&lesson_id=X&content_type=vocabulary
  → Returns: Liste fälliger Karten mit Content-Daten

GET  /api/review/stats
  Query: ?period=30d
  → Returns: Streak, Reviews/Tag, Retention-Rate, Forecast

POST /api/review/settings
  Body: { desired_retention, daily_new_cards, daily_review_limit }
  → Aktualisiert UserSRSSettings

GET  /api/review/forecast
  → Returns: Voraussichtliche Reviews pro Tag für nächste 30 Tage

POST /api/review/suspend
  Body: { content_ids: [...] }
  → Setzt Karten auf "suspended"
```

---

## 6. Migrations-Strategie: localStorage → DB

### Phase 1: Dual-Write (Rückwärtskompatibel)
1. Beim Bewerten wird **sowohl** localStorage **als auch** API beschrieben
2. Bestehende localStorage-Daten werden beim nächsten Login migriert
3. Alte Browser-Sessions funktionieren weiter

### Phase 2: DB-First
1. Beim Laden einer Lektion wird der FSRS-State aus der DB geholt
2. localStorage dient nur noch als Offline-Cache
3. Sync beim nächsten Online-Zugang

### Phase 3: Cleanup
1. localStorage-Fallback entfernen
2. Alle Karten-States sind in der DB

### Migrationsskript für bestehende Daten

```python
def migrate_content_progress_to_srs(user_id):
    """Migriert bestehenden content_progress zu CardReviewState"""
    progress_records = UserLessonProgress.query.filter_by(user_id=user_id).all()
    
    for progress in progress_records:
        content_progress = progress.get_content_progress()
        for content_id, completed in content_progress.items():
            if completed:
                # Bereits gelernte Karten: Status "review", initiales Interval
                state = CardReviewState(
                    user_id=user_id,
                    content_id=int(content_id),
                    status='review',
                    difficulty=5.0,
                    stability=1.0,
                    reps=1,
                    due_date=datetime.utcnow(),  # Sofort fällig für erste echte Review
                )
                db.session.add(state)
    
    db.session.commit()
```

---

## 7. UX-Verbesserungen & Gamification

### 7.1 Streak-System

```
🔥 Streak: 7 Tage
```

- **Regel**: Mindestens 1 Review pro Tag = Streak gehalten
- **Visualisierung**: Feuer-Emoji mit Zähler, Animation bei neuem Rekord
- **Freeze**: 1 "Streak Freeze" pro Woche (Kulanz-Tag)
- **Motivation**: Duolingo-Studie zeigt 55% höhere Retention durch Streak-Wetten

### 7.2 Fortschritts-Levels pro Karte

Visuell dargestellt mit Farben/Icons:

| Level | Status | Interval | Farbe |
|-------|--------|----------|-------|
| Neu | Noch nie gesehen | — | Grau |
| Lernen | In Erstlernphase | < 1 Tag | Rot |
| Jung | Erste Reviews bestanden | 1–21 Tage | Orange |
| Reif | Langzeitgedächtnis | > 21 Tage | Grün |
| Gemeistert | Sehr stabil | > 90 Tage | Gold |

### 7.3 Session-Zusammenfassung

Nach jeder Review-Session:
```
┌─────────────────────────────────────┐
│  Session beendet! 🎉               │
│                                     │
│  ✅ 25 Karten wiederholt            │
│  ⏱  8 Minuten                      │
│  📈 Erfolgsrate: 84%               │
│  🔥 Streak: 8 Tage (neuer Rekord!) │
│                                     │
│  Schwierigste Karten:              │
│  • 食べる (taberu) — 3× vergessen   │
│  • 飲む (nomu) — 2× vergessen      │
│                                     │
│  [Weiter lernen]  [Fertig]         │
└─────────────────────────────────────┘
```

### 7.4 Motivierende Benachrichtigungen

- "Du hast 15 Karten fällig — nur 5 Minuten!"
- "Dein Streak ist in Gefahr! Noch 2 Stunden."
- "Glückwunsch! 100 Karten gemeistert."

### 7.5 Lernmodi

| Modus | Beschreibung |
|-------|-------------|
| **Tägliche Review** | Alle fälligen Karten, gemischt |
| **Lektion wiederholen** | Nur Karten einer bestimmten Lektion |
| **Schwierige Karten** | Nur Karten mit Lapses > 2 |
| **Cram Mode** | Alle Karten einer Lektion, ohne SRS (vor Prüfung) |
| **Neue Karten** | Nur noch nie gesehene Karten |

---

## 8. Vergleich: Bekannte Apps als Referenz

### Was wir von Anki lernen können
- 4-Stufen-Bewertung mit angezeigten Intervallen
- Review-Statistiken und Forecast
- FSRS als Standardalgorithmus
- Parameter-Optimizer nach genug Reviews

### Was wir von WaniKani lernen können
- Klare Level-Progression (Apprentice → Guru → Master → Enlightened → Burned)
- Gamification durch sichtbaren Fortschritt
- Japanisch-spezifische UX (Furigana, Audio)

### Was wir von Duolingo lernen können
- Streaks als Hauptmotivator
- Session-Zusammenfassungen
- Tägliche Erinnerungen
- Leichte, spielerische UI

### Was wir BESSER machen können
- **Kontextbezogen**: Karten sind in Lektionen eingebettet, nicht isoliert
- **Japanisch-optimiert**: Kana, Kanji, Vokabeln, Grammatik — jeweils eigene Kartentypen
- **Audio integriert**: TTS bereits vorhanden
- **Quiz-Integration**: SRS + Quiz als Lernzyklus

---

## 9. Implementierungs-Roadmap

### Phase 1: Foundation (MVP) — ~5 Tage
- [ ] DB-Modelle erstellen (`CardReviewState`, `ReviewLog`, `UserSRSSettings`)
- [ ] Alembic-Migration
- [ ] `fsrs`-Bibliothek integrieren
- [ ] API-Endpoint: `POST /api/review/rate`
- [ ] API-Endpoint: `GET /api/review/due`
- [ ] Bestehendes Deck-Karussell: Bewertung an Backend senden
- [ ] 4-Stufen-Bewertung (Again/Hard/Good/Easy) statt 3

### Phase 2: Review-Seite — ~5 Tage
- [ ] Route `/review` mit eigener Review-UI
- [ ] Gemischte Karten aus allen Lektionen
- [ ] Intervall-Anzeige unter Buttons
- [ ] Session-Fortschrittsbalken
- [ ] Session-Zusammenfassung am Ende

### Phase 3: Statistiken & Gamification — ~3 Tage
- [ ] Streak-System implementieren
- [ ] Route `/review/stats` mit Dashboard
- [ ] Heatmap, Retention-Graph, Forecast
- [ ] Karten-Level-Anzeige (Neu → Gemeistert)

### Phase 4: Migration & Polish — ~2 Tage
- [ ] localStorage → DB Migration
- [ ] Bestehende `content_progress`-Daten migrieren
- [ ] Offline-Fallback
- [ ] Mobile-Optimierung der Review-Seite

### Phase 5: Fortgeschritten (Optional) — ~3 Tage
- [ ] FSRS-Parameter-Optimizer (nach 1'000 Reviews)
- [ ] Cram-Modus
- [ ] Karten-Browser (`/review/browse`)
- [ ] `desired_retention` in User-Settings einstellbar

---

## 10. Technische Entscheidungen

### Warum FSRS statt SM-2?
1. **Effizienz**: 20–30% weniger Reviews bei gleicher Erinnerungsrate
2. **Personalisierung**: Parameter passen sich dem User an
3. **Modernität**: Von Anki offiziell übernommen, aktive Entwicklung
4. **Python-Bibliothek**: `fsrs` v6.3.1 — gut gepflegt, einfache API

### Warum nicht Leitner?
- Fixe Intervalle sind ineffizient
- Keine Personalisierung möglich
- Nicht kompetitiv mit modernen Apps

### Warum 4 Bewertungsstufen statt 3?
Das aktuelle System hat 3 Stufen, wobei "Schwer" und "Gewusst" identisch sind. FSRS arbeitet mit 4 Stufen:
- **Again** (1): Vergessen → Karte zurück in Lernphase
- **Hard** (2): Erinnert, aber mit Mühe → kürzeres Intervall
- **Good** (3): Normal erinnert → Standard-Intervall
- **Easy** (4): Sofort gewusst → längeres Intervall

### Wo wird der FSRS-State berechnet?
**Backend (Python)** — nicht im Frontend. Gründe:
- Konsistenz über Geräte hinweg
- Sicherheit (keine Manipulation möglich)
- Optimizer braucht DB-Zugriff
- `fsrs`-Bibliothek ist Python-nativ

---

## 11. Referenzen & Quellen

### Algorithmen
- [FSRS GitHub](https://github.com/open-spaced-repetition/free-spaced-repetition-scheduler)
- [py-fsrs auf PyPI](https://pypi.org/project/fsrs/) — Python-Bibliothek
- [FSRS technische Erklärung](https://expertium.github.io/Algorithm.html)
- [FSRS in 100 Zeilen implementieren](https://borretti.me/article/implementing-fsrs-in-100-lines)
- [SM-2 Algorithmus erklärt](https://tegaru.app/en/blog/sm2-algorithm-explained)

### UX & Gamification
- [Anki FSRS Integration](https://faqs.ankiweb.net/what-spaced-repetition-algorithm)
- [WaniKani SRS-System](https://knowledge.wanikani.com/wanikani/srs/)
- [Duolingo Streak-Studie](https://designlab.com/blog/gamification-in-ux-enhancing-engagement-and-interaction/)

### Python-Bibliotheken
- `fsrs` v6.3.1 — FSRS-Implementierung
- `supermemo2` — SM-2-Implementierung (als Fallback)
