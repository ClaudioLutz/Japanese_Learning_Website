# Implementierungsplan: Spaced Repetition System (FSRS)

> **Erstellt:** 12. April 2026
> **Basis:** [konzept_spaced_repetition.md](konzept_spaced_repetition.md)
> **Scope:** Schritte 1–5 (Foundation bis Basis-Statistiken)

---

## Bestandsaufnahme: Was existiert bereits?

Bevor wir bauen, muessen wir wissen, was da ist — und was wir wiederverwenden koennen.

### Datenbank-Modelle (models.py)

| Modell | Relevante Felder | Wiederverwendbar? |
|--------|-----------------|-------------------|
| `User` | `current_streak`, `longest_streak`, `last_activity_date`, `total_xp` | **Ja** — Streak-Felder existieren bereits, `update_streak()` Methode auch |
| `LessonContent` | `id`, `lesson_id`, `content_type`, `content_id`, `page_number` | **Ja** — Jedes Content-Item wird eine SRS-Karte |
| `UserLessonProgress` | `content_progress` (JSON: `{content_id: true/false}`) | **Teilweise** — Binaerer Fortschritt bleibt parallel bestehen |

### Frontend: Deck-Karussell (lesson_view.html)

| Komponente | Zeilen | Zustand |
|-----------|--------|---------|
| `createDeck()` | 2500–2716 | 3 Buttons: `again`/`hard`/`good` — hard und good sind identisch |
| `rateCard(rating)` | 2638–2687 | `again` → reinsert, `hard`/`good` → remove + `markContentComplete()` |
| `saveProgress()` | 2535–2541 | Nur localStorage: `deck_{lessonId}_page{pageIdx}` |
| `showCard(idx)` | 2587–2628 | Klon + Event-Listener-Reattach |

### Backend: Progress-API (routes.py)

| Endpoint | Methode | Funktion |
|----------|---------|----------|
| `/api/lessons/<id>/progress` | POST | `markContentComplete()` — setzt `content_progress[content_id] = true` |

**Wichtig:** Die bestehende API kennt nur *binaer* (gelernt/nicht gelernt). Das SRS-System braucht *Bewertungsstufen* und *Scheduling*.

---

## Architektur-Entscheidungen

### 1. FSRS-State: Nur `fsrs_state` JSON, keine redundanten Spalten

Das Konzept-Dokument schlug separate Spalten fuer `difficulty`, `stability`, `retrievability` vor. Stattdessen:

```
card_review_state.fsrs_card_state  →  Card.to_json() / Card.from_json()
```

**Grund:** Die `fsrs`-Bibliothek verwaltet den kompletten State intern. Redundante Spalten driften auseinander und muessen synchron gehalten werden. `Card.to_json()` serialisiert alles:

```python
from fsrs import Card
card = Card()
json_str = card.to_json()   # → '{"due": "2026-04-12T...", "stability": 0.0, "difficulty": 5.0, ...}'
card = Card.from_json(json_str)
```

Fuer Queries (z.B. "alle faelligen Karten") nutzen wir die `due_date`-Spalte — die wird bei jedem Review aus dem FSRS-Card-State synchronisiert.

### 2. Backend-only FSRS-Berechnung

Der FSRS-Algorithmus laeuft **ausschliesslich im Python-Backend**. Das Frontend sendet nur `{content_id, rating, time_taken_ms}` und bekommt `{next_interval, due_date, cards_remaining}` zurueck.

**Gruende:**
- Konsistenz ueber Geraete
- `fsrs`-Bibliothek ist Python-nativ
- Keine Manipulation durch Client moeglich

### 3. Bestehende `markContentComplete()` bleibt bestehen

Das SRS-System laeuft **parallel** zum binaeren Fortschrittssystem. Wenn eine Karte mindestens einmal mit Good/Easy bewertet wird, gilt sie auch als `content_complete`. So bleibt die Lektions-Fortschrittsanzeige (Prozentbalken) kompatibel.

### 4. Kein Offline-Fallback

localStorage-Persistenz wird in Phase 1 beibehalten (Dual-Write), aber kein Offline-Sync gebaut. Die Userbase ist klein, die App ist web-only.

### 5. Review-Seite nutzt bestehendes Flip-Card-Template

Die `/review`-Seite rendert Karten mit dem **gleichen HTML/CSS** wie `lesson_view.html`. Kein neues Karten-Layout, sondern Wiederverwendung der bestehenden `.flip-card`/`.card-scene`/`.card-flipper`-Struktur.

---

## Schritt 1: DB-Modelle + Migration + fsrs-Lib (~1 Tag)

### 1.1 `fsrs` zu requirements.txt hinzufuegen

```
fsrs>=6.3.0
```

### 1.2 Neue Modelle in models.py

```python
class CardReviewState(db.Model):
    """SRS-Zustand pro User + Content-Item.
    
    Speichert den FSRS-Card-State als JSON. Die due_date-Spalte
    ist ein denormalisierter Index fuer effiziente "faellige Karten"-Queries.
    """
    __tablename__ = 'card_review_state'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    content_id = db.Column(db.Integer, db.ForeignKey('lesson_content.id'), nullable=False)
    
    # FSRS Card State (kompletter State als JSON)
    fsrs_card_state = db.Column(db.Text, nullable=False)
    
    # Denormalisierte Felder fuer Queries
    due_date = db.Column(db.DateTime, nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default='new')
    # Moegliche Werte: 'new', 'learning', 'review', 'relearning', 'suspended'
    
    # Statistiken (nicht in fsrs-State enthalten)
    reps = db.Column(db.Integer, default=0)
    lapses = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Beziehungen
    user = db.relationship('User', backref=db.backref('card_states', lazy='dynamic'))
    content = db.relationship('LessonContent', backref=db.backref('review_states', lazy='dynamic'))
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'content_id', name='uq_user_content_review'),
        db.Index('ix_card_review_due', 'user_id', 'due_date', 'status'),
    )
```

```python
class ReviewLog(db.Model):
    """Protokoll jeder Bewertung — Basis fuer FSRS-Optimizer.
    
    Speichert den FSRS ReviewLog als JSON plus denormalisierte
    Felder fuer schnelle Statistik-Queries.
    """
    __tablename__ = 'review_log'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    content_id = db.Column(db.Integer, db.ForeignKey('lesson_content.id'), nullable=False)
    
    # Bewertung
    rating = db.Column(db.Integer, nullable=False)  # 1=Again, 2=Hard, 3=Good, 4=Easy
    reviewed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    time_taken_ms = db.Column(db.Integer)
    
    # FSRS ReviewLog State (fuer Optimizer)
    fsrs_review_log = db.Column(db.Text)
    
    # Denormalisiert fuer Statistiken
    scheduled_days = db.Column(db.Integer)  # Neues Intervall in Tagen
    elapsed_days = db.Column(db.Integer)    # Tage seit letztem Review
    
    # Beziehungen
    user = db.relationship('User', backref=db.backref('review_logs', lazy='dynamic'))
    content = db.relationship('LessonContent')
```

```python
class UserSRSSettings(db.Model):
    """Persoenliche SRS-Einstellungen pro User."""
    __tablename__ = 'user_srs_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    
    desired_retention = db.Column(db.Float, default=0.9)     # 80-95%
    daily_new_cards = db.Column(db.Integer, default=20)
    daily_review_limit = db.Column(db.Integer, default=100)
    
    # FSRS Optimizer Parameters (21 Floats als JSON, nach ~1000 Reviews)
    fsrs_parameters = db.Column(db.Text)
    
    # Beziehung
    user = db.relationship('User', backref=db.backref('srs_settings', uselist=False))
```

### 1.3 Alembic-Migration erzeugen

```bash
flask db migrate -m "SRS-Modelle: CardReviewState, ReviewLog, UserSRSSettings"
flask db upgrade
```

### 1.4 SRS-Service (neuer File: app/srs_service.py)

Kapselt die gesamte FSRS-Logik in einem Service — kein FSRS-Import in routes.py oder models.py.

```python
# app/srs_service.py
from fsrs import Scheduler, Card, Rating, State
from datetime import datetime, timezone
from app import db
from app.models import CardReviewState, ReviewLog, UserSRSSettings, LessonContent

class SRSService:
    """Service-Klasse fuer alle SRS-Operationen."""
    
    # Rating-Mapping: Frontend-String → FSRS Rating
    RATING_MAP = {
        1: Rating.Again,
        2: Rating.Hard,
        3: Rating.Good,
        4: Rating.Easy,
    }
    
    # State-Mapping: FSRS State → DB-String
    STATE_MAP = {
        State.Learning: 'learning',
        State.Review: 'review',
        State.Relearning: 'relearning',
    }
    
    @staticmethod
    def get_scheduler(user_id):
        """Erstellt einen FSRS-Scheduler mit User-spezifischen Parametern."""
        settings = UserSRSSettings.query.filter_by(user_id=user_id).first()
        
        kwargs = {
            'desired_retention': settings.desired_retention if settings else 0.9,
            'enable_fuzzing': True,
        }
        
        if settings and settings.fsrs_parameters:
            import json
            kwargs['parameters'] = tuple(json.loads(settings.fsrs_parameters))
        
        return Scheduler(**kwargs)
    
    @classmethod
    def rate_card(cls, user_id, content_id, rating_int, time_taken_ms=None):
        """
        Bewertet eine Karte und berechnet den neuen FSRS-State.
        
        Returns: dict mit next_interval, due_date, status, cards_remaining
        """
        scheduler = cls.get_scheduler(user_id)
        rating = cls.RATING_MAP[rating_int]
        
        # CardReviewState laden oder erstellen
        state = CardReviewState.query.filter_by(
            user_id=user_id, content_id=content_id
        ).first()
        
        if state:
            card = Card.from_json(state.fsrs_card_state)
        else:
            card = Card()
            state = CardReviewState(
                user_id=user_id,
                content_id=content_id,
                fsrs_card_state=card.to_json(),
                due_date=card.due.replace(tzinfo=None),
                status='new',
            )
            db.session.add(state)
        
        # FSRS-Berechnung
        new_card, fsrs_log = scheduler.review_card(card, rating)
        
        # State aktualisieren
        state.fsrs_card_state = new_card.to_json()
        state.due_date = new_card.due.replace(tzinfo=None)  # UTC ohne tzinfo fuer DB
        state.status = cls.STATE_MAP.get(new_card.state, 'review')
        state.reps += 1
        if rating_int == 1:  # Again
            state.lapses += 1
        state.updated_at = datetime.utcnow()
        
        # ReviewLog erstellen
        log = ReviewLog(
            user_id=user_id,
            content_id=content_id,
            rating=rating_int,
            reviewed_at=datetime.utcnow(),
            time_taken_ms=time_taken_ms,
            fsrs_review_log=fsrs_log.to_json(),
            scheduled_days=fsrs_log.scheduled_days,
            elapsed_days=fsrs_log.elapsed_days,
        )
        db.session.add(log)
        db.session.commit()
        
        return {
            'next_interval': fsrs_log.scheduled_days,
            'due_date': state.due_date.isoformat(),
            'status': state.status,
            'reps': state.reps,
            'lapses': state.lapses,
        }
    
    @staticmethod
    def get_due_cards(user_id, limit=50, lesson_id=None, content_type=None):
        """
        Holt alle faelligen Karten fuer einen User.
        
        Reihenfolge: Ueberfaellige zuerst (aeltestes due_date), dann neue.
        """
        now = datetime.utcnow()
        
        query = CardReviewState.query.filter(
            CardReviewState.user_id == user_id,
            CardReviewState.due_date <= now,
            CardReviewState.status != 'suspended',
        )
        
        if lesson_id or content_type:
            query = query.join(LessonContent)
            if lesson_id:
                query = query.filter(LessonContent.lesson_id == lesson_id)
            if content_type:
                query = query.filter(LessonContent.content_type == content_type)
        
        return query.order_by(CardReviewState.due_date.asc()).limit(limit).all()
    
    @staticmethod
    def get_new_cards(user_id, lesson_id, limit=20):
        """
        Holt Content-Items einer Lektion, die der User noch nie bewertet hat.
        
        Nur Karten-Typen (kana, kanji, vocabulary, grammar), keine Medien/Text.
        """
        from sqlalchemy import and_, not_, exists
        
        card_types = ['kana', 'kanji', 'vocabulary', 'grammar']
        
        # Subquery: Content-IDs die der User bereits hat
        existing = db.session.query(CardReviewState.content_id).filter(
            CardReviewState.user_id == user_id
        ).subquery()
        
        return LessonContent.query.filter(
            LessonContent.lesson_id == lesson_id,
            LessonContent.content_type.in_(card_types),
            ~LessonContent.id.in_(existing),
        ).order_by(LessonContent.page_number, LessonContent.order_index).limit(limit).all()
    
    @staticmethod
    def get_user_stats(user_id):
        """Basis-Statistiken fuer einen User."""
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        total_cards = CardReviewState.query.filter_by(user_id=user_id).count()
        due_count = CardReviewState.query.filter(
            CardReviewState.user_id == user_id,
            CardReviewState.due_date <= now,
            CardReviewState.status != 'suspended',
        ).count()
        
        reviews_today = ReviewLog.query.filter(
            ReviewLog.user_id == user_id,
            ReviewLog.reviewed_at >= today_start,
        ).count()
        
        # Mature cards: status == 'review' und Intervall > 21 Tage
        mature_count = CardReviewState.query.filter(
            CardReviewState.user_id == user_id,
            CardReviewState.status == 'review',
            CardReviewState.due_date > now + db.text("INTERVAL '21 days'"),
        ).count() if total_cards > 0 else 0
        
        return {
            'total_cards': total_cards,
            'due_count': due_count,
            'reviews_today': reviews_today,
            'mature_count': mature_count,
        }
    
    @staticmethod
    def get_interval_preview(user_id, content_id):
        """
        Zeigt die voraussichtlichen Intervalle fuer alle 4 Ratings.
        Wird im Frontend unter den Buttons angezeigt.
        """
        scheduler = SRSService.get_scheduler(user_id)
        
        state = CardReviewState.query.filter_by(
            user_id=user_id, content_id=content_id
        ).first()
        
        if state:
            card = Card.from_json(state.fsrs_card_state)
        else:
            card = Card()
        
        previews = {}
        for rating_int, rating_enum in SRSService.RATING_MAP.items():
            preview_card, preview_log = scheduler.review_card(card, rating_enum)
            days = preview_log.scheduled_days
            
            if days == 0:
                # Learning-Phase: Minuten anzeigen
                minutes = max(1, int((preview_card.due - card.due).total_seconds() / 60))
                label = f"<{minutes} Min" if minutes < 60 else f"{minutes // 60} Std"
            elif days == 1:
                label = "1 Tag"
            else:
                label = f"{days} Tage"
            
            previews[rating_int] = label
        
        return previews
```

### 1.5 Warum dieser Aufbau erweiterbar ist

| Zukuenftige Erweiterung | Wie anknuepfen |
|--------------------------|----------------|
| FSRS-Optimizer (Phase 5) | `UserSRSSettings.fsrs_parameters` fuellen, `SRSService.get_scheduler()` liest sie automatisch |
| Cram-Modus | Neuer Status `'cramming'` — `get_due_cards()` kann Filter erweitern |
| Karten suspendieren | `status = 'suspended'` setzen — Queries filtern bereits danach |
| Karten-Browser | `CardReviewState` join `LessonContent` join `Lesson` — alle Daten da |
| Statistik-Heatmap | `ReviewLog.reviewed_at` gruppiert nach Datum |
| desired_retention pro User | `UserSRSSettings.desired_retention` ist bereits Feld |

---

## Schritt 2: API-Endpoints (~1 Tag)

### 2.1 Neuer Blueprint: app/srs_routes.py

Eigener Blueprint statt Erweiterung von routes.py — haelt den Code getrennt und uebersichtlich.

```python
# app/srs_routes.py
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.srs_service import SRSService

srs_bp = Blueprint('srs', __name__, url_prefix='/api/srs')
```

### 2.2 Endpoints

#### POST /api/srs/rate — Karte bewerten

```
Request:  { content_id: int, rating: 1-4, time_taken_ms: int? }
Response: { next_interval: int, due_date: str, status: str,
            reps: int, lapses: int, cards_remaining: int }
```

Ablauf:
1. `SRSService.rate_card(user_id, content_id, rating, time_taken_ms)`
2. Wenn rating >= 3 (Good/Easy): Auch `markContentComplete` ausfuehren (Dual-Write)
3. `cards_remaining` = Anzahl verbleibende faellige Karten im aktuellen Kontext
4. `User.update_streak()` aufrufen (Streak-System existiert bereits)

#### GET /api/srs/due — Faellige Karten abrufen

```
Request:  ?limit=50&lesson_id=X&content_type=vocabulary
Response: { cards: [{ content_id, content_type, content_data, due_date, status, reps, lapses }], 
            total_due: int }
```

Ablauf:
1. `SRSService.get_due_cards(user_id, limit, lesson_id, content_type)`
2. Fuer jede Karte: `LessonContent.get_content_data()` aufrufen um den Inhalt zu laden
3. `total_due` = Gesamtanzahl faelliger Karten (ohne Limit)

#### GET /api/srs/preview — Intervall-Vorschau

```
Request:  ?content_id=X
Response: { 1: "<1 Min", 2: "<10 Min", 3: "4 Tage", 4: "12 Tage" }
```

Ablauf:
1. `SRSService.get_interval_preview(user_id, content_id)`
2. Wird beim Umdrehen der Karte aufgerufen (unter den Buttons anzeigen)

#### GET /api/srs/stats — Basis-Statistiken

```
Response: { total_cards, due_count, reviews_today, mature_count,
            current_streak, longest_streak }
```

### 2.3 Blueprint registrieren in __init__.py

```python
from app.srs_routes import srs_bp
app.register_blueprint(srs_bp)
```

---

## Schritt 3: Deck-Karussell umbauen (~2 Tage)

Das ist der groesste und sensibelste Schritt — hier aendert sich, was der User sieht und fuehlt.

### 3.1 Buttons: 3 → 4 Stufen

**Vorher (lesson_view.html, Zeile 2558):**
```html
<div class="confidence-buttons">
    <button data-rating="again">Nochmal</button>
    <button data-rating="hard">Schwer</button>
    <button data-rating="good">Gewusst</button>
</div>
```

**Nachher:**
```html
<div class="confidence-buttons">
    <button data-rating="1" class="btn-again">
        <i class="fas fa-redo"></i> Nochmal
        <span class="interval-hint"></span>
        <span class="kbd-hint">1</span>
    </button>
    <button data-rating="2" class="btn-hard">
        <i class="fas fa-brain"></i> Schwer
        <span class="interval-hint"></span>
        <span class="kbd-hint">2</span>
    </button>
    <button data-rating="3" class="btn-good">
        <i class="fas fa-check"></i> Gut
        <span class="interval-hint"></span>
        <span class="kbd-hint">3</span>
    </button>
    <button data-rating="4" class="btn-easy">
        <i class="fas fa-bolt"></i> Einfach
        <span class="interval-hint"></span>
        <span class="kbd-hint">4</span>
    </button>
</div>
```

### 3.2 Intervall-Vorschau unter Buttons

Beim Umdrehen der Karte (Flip) wird `/api/srs/preview?content_id=X` aufgerufen. Die Antwort fuellt die `.interval-hint`-Spans:

```
[Nochmal]   [Schwer]    [Gut]      [Einfach]
  <1 Min     <10 Min    4 Tage     12 Tage
```

**Timing:** Der Fetch wird beim Flip ausgeloest (nicht beim Laden), um die API nicht unnoetig zu belasten. Cache pro Karte in der Session.

### 3.3 rateCard() → Backend-Anbindung

**Vorher:**
```javascript
function rateCard(rating) {
    if (rating === 'again') { /* reinsert */ }
    else { markContentComplete(contentId); /* remove */ }
}
```

**Nachher:**
```javascript
async function rateCard(ratingInt) {
    const contentId = getCurrentContentId();
    const timeTaken = Date.now() - cardFlipTime;  // Zeit seit Flip
    
    // 1. Backend-Bewertung (FSRS)
    const response = await fetch('/api/srs/rate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
        body: JSON.stringify({ content_id: contentId, rating: ratingInt, time_taken_ms: timeTaken })
    });
    const result = await response.json();
    
    // 2. Kartenanimation
    if (ratingInt === 1) {
        // Again: Shake + Reinsert (wie bisher)
        reinsertCard();
    } else {
        // Hard/Good/Easy: Slide out
        removeCard();
        // Bei Good/Easy: Auch markContentComplete (Dual-Write)
        if (ratingInt >= 3) {
            markContentComplete(contentId);
        }
    }
    
    // 3. localStorage-Update (Dual-Write, wird spaeter entfernt)
    saveProgress();
}
```

### 3.4 Verhalten pro Rating im Deck

| Rating | Animation | Deck-Effekt | Backend |
|--------|-----------|-------------|---------|
| 1 (Again) | Shake | Karte bleibt im Deck, 2-5 Positionen spaeter | FSRS: Lapse, kurzes Intervall |
| 2 (Hard) | Slide left (langsam) | Karte wird entfernt | FSRS: Kuerzeres Intervall |
| 3 (Good) | Slide right | Karte wird entfernt + markContentComplete | FSRS: Standard-Intervall |
| 4 (Easy) | Slide right (schnell) | Karte wird entfernt + markContentComplete | FSRS: Langes Intervall |

### 3.5 Nicht-eingeloggte User (Gaeste)

Wenn der User nicht eingeloggt ist, werden die SRS-API-Calls uebersprungen. Das Deck funktioniert wie bisher (nur localStorage). Die Buttons zeigen keine Intervalle, nur die Labels.

```javascript
const isAuthenticated = {{ 'true' if current_user.is_authenticated else 'false' }};
```

### 3.6 Keyboard-Shortcuts aktualisieren

Bestehende Shortcuts (Zeile 2690+) von `again`/`hard`/`good` auf `1`/`2`/`3`/`4` umstellen:

| Taste | Aktion |
|-------|--------|
| 1 | Again |
| 2 | Hard |
| 3 | Good |
| 4 | Easy |
| Leertaste | Karte umdrehen |
| ← → | Vorherige/Naechste Karte (im Review-Modus) |

### 3.7 CSS: 4 Buttons statt 3

Die `.confidence-buttons` muessen auf 4 Buttons passen, auch mobil. Jeder Button bekommt eine Farbe:

| Button | Farbe | Hover |
|--------|-------|-------|
| Again | `#dc3545` (rot) | Dunkler |
| Hard | `#fd7e14` (orange) | Dunkler |
| Good | `#28a745` (gruen) | Dunkler |
| Easy | `#007bff` (blau) | Dunkler |

Mobil: Buttons etwas schmaler, Schrift kleiner, Intervall-Hint unter dem Label.

---

## Schritt 4: Review-Seite /review (~2-3 Tage)

### 4.1 Neue Route: /review

```python
@bp.route('/review')
@login_required
def review():
    """Taegliche Wiederholungs-Seite — zeigt alle faelligen Karten."""
    stats = SRSService.get_user_stats(current_user.id)
    return render_template('review.html', stats=stats)
```

Die Karten werden **nicht** serverseitig gerendert, sondern per JavaScript via `/api/srs/due` geladen. Grund: Wir muessen nach jeder Bewertung die naechste Karte laden — das geht nur per AJAX.

### 4.2 Template: review.html

```
┌──────────────────────────────────────────────────┐
│  Taegliche Wiederholung           🔥 Streak: 7   │
│  📦 Faellig: 25    ✅ Erledigt: 0/25   ⏱ 0 min  │
├──────────────────────────────────────────────────┤
│                                                  │
│  ┌──── Flip-Card (gleiche Struktur) ────────┐   │
│  │  (Vorderseite: Japanisch)                │   │
│  │  (Rueckseite: Bedeutung + Details)       │   │
│  └──────────────────────────────────────────┘   │
│                                                  │
│  [Again]   [Hard]    [Good]     [Easy]           │
│   <1 Min    <10 Min   4 Tage    12 Tage          │
│                                                  │
│  Lektion: Hiragana Basics  │  Typ: Kana          │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  42%           │
└──────────────────────────────────────────────────┘
```

### 4.3 JavaScript-Ablauf

```
1. Seite laden → GET /api/srs/due?limit=50
2. Kartenqueue erstellen (gemischt aus allen Lektionen)
3. Erste Karte anzeigen (als Flip-Card rendern)
4. User flipt → GET /api/srs/preview?content_id=X → Intervalle anzeigen
5. User bewertet → POST /api/srs/rate → naechste Karte
6. Queue leer → Session-Zusammenfassung anzeigen
```

### 4.4 Karten-Rendering (clientseitig)

Jede Karte vom Backend kommt als JSON mit allen Daten:

```json
{
  "content_id": 42,
  "content_type": "vocabulary",
  "lesson_title": "Wegbeschreibung",
  "content_data": {
    "word": "駅",
    "reading": "えき",
    "meaning": "Station, Bahnhof",
    "example_sentence_japanese": "駅はどこですか？",
    "example_sentence_english": "Where is the station?",
    "image_url": "/uploads/lessons/images/..."
  }
}
```

Das Frontend baut daraus die gleiche `.flip-card`-Struktur wie in `lesson_view.html`:
- Vorderseite: Japanisches Zeichen/Wort (gross)
- Rueckseite: Details (Lesung, Bedeutung, Beispiel, Bild)

**Wiederverwendung:** Die Card-Rendering-Logik wird als JavaScript-Funktion `renderFlipCard(data)` extrahiert, die sowohl in `lesson_view.html` als auch in `review.html` genutzt wird.

### 4.5 Session-Zusammenfassung

Nach allen Karten:

```
┌─────────────────────────────────────┐
│  Session beendet!                   │
│                                     │
│  ✅ 25 Karten wiederholt            │
│  ⏱  8 Minuten                      │
│  📈 Erfolgsrate: 84%               │
│  🔥 Streak: 8 Tage                 │
│                                     │
│  [Weiter lernen]  [Fertig]         │
└─────────────────────────────────────┘
```

"Erfolgsrate" = Anteil Karten mit Rating >= 3 (Good/Easy).

### 4.6 Navigation

- Link in der Bottom-Nav: "Review" mit Badge fuer faellige Karten
- Link auf der Startseite (index.html): "X Karten faellig" neben "Weiter lernen"

### 4.7 Leere States

| Zustand | Anzeige |
|---------|---------|
| Keine faelligen Karten | "Alles erledigt! Naechste Review in X Stunden." |
| Noch nie Karten gelernt | "Starte eine Lektion, um Karten zu sammeln." mit Link zu /lessons |
| Nicht eingeloggt | Redirect zu /login |

---

## Schritt 5: Basis-Statistiken (~1 Tag)

### 5.1 Review-Header (in review.html)

Oben auf der Review-Seite, immer sichtbar:

```
🔥 Streak: 7 Tage     ⏱ Heute: 12 min     📦 Faellig: 25     ✅ Gemeistert: 142
```

Daten kommen aus `GET /api/srs/stats`.

### 5.2 Karten-Level-Farben (ueberall)

In Lektionen und auf der Review-Seite zeigen Karten ihren SRS-Status:

| Level | Kriterium | Farbe | CSS-Klasse |
|-------|-----------|-------|------------|
| Neu | Noch nie bewertet | Grau `#6c757d` | `.srs-new` |
| Lernen | status = learning/relearning | Rot `#dc3545` | `.srs-learning` |
| Jung | status = review, Intervall ≤ 21d | Orange `#fd7e14` | `.srs-young` |
| Reif | status = review, Intervall > 21d | Gruen `#28a745` | `.srs-mature` |

Anzeige: Kleiner farbiger Punkt auf der Karten-Vorderseite (oben rechts).

### 5.3 Streak-Verbesserung

Das bestehende `User.update_streak()` wird bei jedem `POST /api/srs/rate` aufgerufen. Die Streak-Anzeige kommt:
- In den Review-Header
- Auf die Startseite (neben "Weiter lernen")
- In die Session-Zusammenfassung

### 5.4 Bottom-Nav Badge

Die Bottom-Navigation zeigt ein Badge mit der Anzahl faelliger Karten:

```html
<a href="/review">
    <i class="fas fa-brain"></i>
    <span>Review</span>
    <span class="badge">25</span>
</a>
```

Der Badge-Count wird beim Seitenladen per AJAX aktualisiert (`GET /api/srs/stats`).

---

## Migrations-Strategie: localStorage → DB

### Phase 1 (Schritt 3): Dual-Write

- Beim Bewerten: **Backend (FSRS) + localStorage** werden beide aktualisiert
- Bestehende localStorage-Daten funktionieren weiter
- Neue Bewertungen haben SRS-State in der DB

### Phase 2 (nach Schritt 5): DB-First

- Beim Laden einer Lektion: DB-State hat Prioritaet
- localStorage nur noch als Fallback fuer nicht-eingeloggte User
- Migrationsskript: `content_progress` → `CardReviewState` fuer bestehende User

### Migrationsskript

```python
# In srs_service.py oder als Flask-CLI-Command
def migrate_existing_progress():
    """Migriert bestehenden content_progress zu CardReviewState."""
    from app.models import UserLessonProgress
    
    progress_records = UserLessonProgress.query.filter(
        UserLessonProgress.content_progress.isnot(None)
    ).all()
    
    for progress in progress_records:
        content_progress = progress.get_content_progress()
        for content_id_str, completed in content_progress.items():
            if not completed:
                continue
            
            content_id = int(content_id_str)
            existing = CardReviewState.query.filter_by(
                user_id=progress.user_id, content_id=content_id
            ).first()
            
            if existing:
                continue
            
            # Neue Karte: Als "gelernt" einstufen mit initialem Review-State
            card = Card()
            # Einen Good-Review simulieren
            scheduler = Scheduler(desired_retention=0.9)
            card, _ = scheduler.review_card(card, Rating.Good)
            
            state = CardReviewState(
                user_id=progress.user_id,
                content_id=content_id,
                fsrs_card_state=card.to_json(),
                due_date=card.due.replace(tzinfo=None),
                status='review',
                reps=1,
            )
            db.session.add(state)
    
    db.session.commit()
```

---

## Datei-Uebersicht: Was wird erstellt/geaendert?

### Neue Dateien

| Datei | Zweck |
|-------|-------|
| `app/srs_service.py` | FSRS-Logik, komplett gekapselt |
| `app/srs_routes.py` | API-Endpoints (Blueprint) |
| `app/templates/review.html` | Taegliche Review-Seite |
| `migrations/versions/xxx_srs_modelle.py` | Alembic-Migration (auto-generiert) |

### Geaenderte Dateien

| Datei | Aenderung |
|-------|-----------|
| `requirements.txt` | `fsrs>=6.3.0` hinzufuegen |
| `app/models.py` | 3 neue Modelle (CardReviewState, ReviewLog, UserSRSSettings) |
| `app/__init__.py` | `srs_bp` Blueprint registrieren |
| `app/templates/lesson_view.html` | Deck-Buttons (3→4), Intervall-Hints, Backend-Anbindung |
| `app/static/css/custom.css` | Button-Farben, Intervall-Hints, SRS-Level-Dots |
| `app/templates/base.html` | Bottom-Nav: "Review" Link mit Badge |
| `app/templates/index.html` | "X Karten faellig" Anzeige, Streak |

### Unveraendert

| Datei | Grund |
|-------|-------|
| `app/routes.py` | Bestehende Progress-API bleibt, SRS ist eigener Blueprint |
| `app/models.py` (User) | Streak-Felder existieren bereits |
| Alle Admin-Templates | SRS betrifft nur die Lern-UI |

---

## Test-Strategie

### Unit-Tests (pytest)

| Test | Prueft |
|------|--------|
| `test_srs_service_rate_card` | FSRS-Berechnung: Karte bewerten, State pruefen |
| `test_srs_service_new_card` | Erste Bewertung erstellt CardReviewState |
| `test_srs_service_due_cards` | Query gibt faellige Karten zurueck |
| `test_srs_service_interval_preview` | Vorschau liefert 4 Intervalle |
| `test_srs_api_rate` | POST /api/srs/rate mit gueltigem CSRF |
| `test_srs_api_rate_unauthenticated` | 401 fuer nicht-eingeloggte User |
| `test_srs_api_due` | GET /api/srs/due liefert Karten |
| `test_srs_migration` | Migrationsskript konvertiert content_progress korrekt |

### Manuelle Tests (Browser)

| Szenario | Pruefung |
|----------|----------|
| Lektion oeffnen, Karte bewerten | 4 Buttons sichtbar, Intervalle unter Buttons |
| "Again" druecken | Karte bleibt im Deck, Shake-Animation |
| "Good" druecken | Karte verschwindet, Progress-Bar aktualisiert |
| /review oeffnen | Faellige Karten aus allen Lektionen gemischt |
| Alle Karten durcharbeiten | Session-Zusammenfassung erscheint |
| Nicht eingeloggt | Deck funktioniert wie bisher (ohne SRS) |
| Keyboard 1-4 | Rating-Shortcuts funktionieren |

---

## Risiken und Gegenmassnahmen

| Risiko | Massnahme |
|--------|-----------|
| `fsrs`-Lib aendert API | Version pinnen (`fsrs>=6.3.0,<7.0`), `to_json()`/`from_json()` kapseln |
| Performance bei vielen Karten | `ix_card_review_due` Index, Limit-Parameter, Pagination |
| Card-State korrupt | `try/except` um `Card.from_json()`, Fallback: neue Card() erstellen |
| Bestehendes Deck bricht | Dual-Write: localStorage bleibt als Fallback, Feature-Flag moeglich |
| Mobile 4 Buttons zu eng | Responsive CSS: auf kleinen Screens Icons only oder 2x2 Grid |

---

## Reihenfolge der Implementierung

```
Tag 1:  Schritt 1 — DB-Modelle, Migration, srs_service.py
        Schritt 2 — API-Endpoints, Blueprint
        → Tests schreiben und ausfuehren
        → Commit: "SRS-Backend: FSRS-Modelle, Service, API-Endpoints"

Tag 2:  Schritt 3 — Deck-Karussell umbauen
        → 4 Buttons, Intervall-Hints, Backend-Anbindung
        → Manuell testen im Browser
        → Commit: "SRS-Frontend: 4-Stufen-Bewertung im Deck-Karussell"

Tag 3:  Schritt 4 — Review-Seite /review
        → Template, JS-Logik, Session-Zusammenfassung
        → Manuell testen
        → Commit: "Review-Seite: Taegliche Wiederholung mit FSRS"

Tag 4:  Schritt 5 — Statistiken, Badges, Streak-Integration
        → Bottom-Nav Badge, Startseite, Level-Dots
        → Alle Tests ausfuehren
        → Commit: "SRS-Statistiken: Streak, faellige Karten, Level-Anzeige"
        → Deploy (grosse Aenderung!)
```
