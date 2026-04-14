# Phase 6: Erweiterte Statistiken, Gamification & Karten-Browser

> **Erstellt:** 12. April 2026
> **Basis:** [implementierungsplan.md](implementierungsplan.md) (Schritte 1–5)
> **Voraussetzung:** Phasen 1–5 sind abgeschlossen und produktiv
> **Scope:** Alles nach dem MVP — die Features, die das Lernerlebnis von "funktioniert" zu "macht suechtig" heben

---

## Inhaltsverzeichnis

1. [Erweiterte Statistiken](#1-erweiterte-statistiken)
   - 1.1 Review-Heatmap
   - 1.2 Retention-Kurve
   - 1.3 Review-Forecast
   - 1.4 Card-Maturity-Verteilung
   - 1.5 Performance nach Content-Typ
   - 1.6 Leech-Erkennung
   - 1.7 Antwortzeit-Analyse
   - 1.8 Technische Umsetzung (Charting-Libraries)
2. [Gamification](#2-gamification)
   - 2.1 XP-System
   - 2.2 Karten-Level-Progression (WaniKani-Modell)
   - 2.3 Achievement/Badge-System
   - 2.4 Streak-Erweiterungen
   - 2.5 Session-Gamification
   - 2.6 JLPT-Meilensteine
   - 2.7 Psychologische Grundlagen & Anti-Patterns
3. [Karten-Browser](#3-karten-browser)
   - 3.1 Layout & Navigation
   - 3.2 Filter & Suche
   - 3.3 Sortierung
   - 3.4 Bulk-Aktionen
   - 3.5 Responsive Design
   - 3.6 Keyboard-Navigation
4. [Datenmodell-Erweiterungen](#4-datenmodell-erweiterungen)
5. [API-Endpoints](#5-api-endpoints)
6. [Technologie-Entscheidungen](#6-technologie-entscheidungen)
7. [Implementierungs-Reihenfolge](#7-implementierungs-reihenfolge)
8. [Risiken & Anti-Patterns](#8-risiken--anti-patterns)
9. [Quellen](#9-quellen)

---

## 1. Erweiterte Statistiken

### 1.1 Review-Heatmap (GitHub-Contribution-Stil)

**Was:** Ein Kalender-Grid, das zeigt, an welchen Tagen wie viel gelernt wurde. Jedes Quadrat = ein Tag, Farbintensitaet = Anzahl Reviews.

**Referenz:** Anki Review Heatmap Add-on (700'000+ Downloads), GitHub Contribution Graph

**Datenquelle:** `review_log.reviewed_at` gruppiert nach Datum

```sql
SELECT DATE(reviewed_at) as review_date, COUNT(*) as review_count
FROM review_log
WHERE user_id = :uid AND reviewed_at >= :start
GROUP BY DATE(reviewed_at)
ORDER BY review_date
```

**Intensitaetsstufen:**

| Stufe | Reviews/Tag | Farbe |
|-------|------------|-------|
| 0 | Keine | `#ebedf0` (grau) |
| 1 | 1–10 | `#9be9a8` (hellgruen) |
| 2 | 11–30 | `#40c463` (gruen) |
| 3 | 31–60 | `#30a14e` (dunkelgruen) |
| 4 | 61+ | `#216e39` (sehr dunkelgruen) |

**Berechnung:** Quantil-basiertes Bucketing auf Basis der eigenen Daten (nicht absolute Werte). So sieht auch ein User mit 5 Reviews/Tag Variation.

**Zusaetzliche Informationen im Heatmap:**
- Tooltip bei Hover: "12. April: 42 Reviews, 15 Minuten"
- Streak-Anzeige: Aktuelle Streak-Tage hervorgehoben
- Monatsgrenzen sichtbar
- Zeitraum: Letzten 365 Tage (scrollbar)

**Layout:**
```
          Jan    Feb    Mar    Apr    Mai    Jun    Jul
  Mo  ■ ■ ■ ■  ■ ■ ■ ■  □ □ □ ■  ■ ■ ■ ■  ...
  Di  ■ ■ ■ ■  □ ■ ■ ■  ■ ■ □ ■  ■ ■ ■ ■  ...
  Mi  ■ ■ ■ □  ■ ■ ■ ■  ■ ■ ■ ■  ■ ■ □ ■  ...
  Do  □ ■ ■ ■  ■ □ ■ ■  ■ ■ ■ ■  ■ ■ ■ ■  ...
  Fr  ■ ■ ■ ■  ■ ■ ■ ■  ■ ■ ■ ■  □ ■ ■ ■  ...
  Sa  ■ □ ■ ■  ■ ■ □ ■  ■ ■ ■ ■  ■ ■ ■ ■  ...
  So  □ □ ■ ■  ■ ■ ■ □  □ ■ ■ ■  ■ □ ■ ■  ...

  Weniger ■ □ □ □ □ ■ Mehr        842 Reviews in 2026
```

---

### 1.2 Retention-Kurve (Vergessenskurve)

**Was:** Zeigt dem User, wie gut sein Gedaechtnis ueber die Zeit funktioniert. Vergleich: Ebbinghaus-Theorie vs. eigene Performance.

**Metriken:**

| Metrik | Berechnung | Zweck |
|--------|-----------|-------|
| **True Retention** | `COUNT(rating >= 2) / COUNT(*)` bei Reviews | Tatsaechliche Erfolgsrate |
| **Desired Retention** | `user_srs_settings.desired_retention` (Standard: 90%) | Zielwert |
| **Retention nach Intervall** | Erfolgsrate gruppiert nach `elapsed_days`-Bereichen | Wie gut bei kurzen vs. langen Intervallen? |

**Retention nach Intervall-Bereichen:**

```sql
SELECT
    CASE
        WHEN elapsed_days <= 1 THEN '1 Tag'
        WHEN elapsed_days <= 7 THEN '2-7 Tage'
        WHEN elapsed_days <= 30 THEN '8-30 Tage'
        WHEN elapsed_days <= 90 THEN '1-3 Monate'
        ELSE '3+ Monate'
    END as interval_range,
    ROUND(
        SUM(CASE WHEN rating >= 2 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1
    ) as retention_percent,
    COUNT(*) as total_reviews
FROM review_log
WHERE user_id = :uid
GROUP BY interval_range
```

**Visualisierung:**
- **X-Achse:** Intervall-Bereich (1 Tag → 3+ Monate)
- **Y-Achse:** Retention-Rate (0–100%)
- **Grüne Linie:** Eigene Retention
- **Gestrichelte Linie:** Desired Retention (90%)
- **Graue Kurve:** Ebbinghaus-Referenz (ohne SRS)

**Interpretation fuer den User:**
- True > Desired: "Deine Intervalle koennten laenger sein — du wiederholst mehr als noetig."
- True < Desired: "Deine Intervalle sind etwas zu lang — erhoehe die Wiederholungsfrequenz."
- True ≈ Desired: "Perfekt kalibriert!"

---

### 1.3 Review-Forecast

**Was:** Voraussichtliche Anzahl Reviews pro Tag fuer die naechsten 30 Tage.

**Berechnung:**
```python
def get_review_forecast(user_id, days=30):
    """Projiziert faellige Reviews basierend auf aktuellen due_dates."""
    today = datetime.utcnow().date()
    forecast = {}
    
    for day_offset in range(days):
        target_date = today + timedelta(days=day_offset)
        start = datetime.combine(target_date, time.min)
        end = datetime.combine(target_date, time.max)
        
        count = CardReviewState.query.filter(
            CardReviewState.user_id == user_id,
            CardReviewState.due_date >= start,
            CardReviewState.due_date <= end,
            CardReviewState.status != 'suspended',
        ).count()
        
        forecast[target_date.isoformat()] = count
    
    return forecast
```

**Limitierungen (transparent kommunizieren):**
- Zaehlt nur bereits geplante Reviews
- Beruecksichtigt keine zukuenftigen Fehler (Again-Bewertungen erzeugen Extra-Reviews)
- Keine neuen Karten eingerechnet
- Genauigkeit nimmt mit Entfernung ab

**Visualisierung:** Bar Chart mit 30 Balken (ein Balken pro Tag)
- **Farbe:** Gruen wenn < Tageslimit, Orange wenn nahe Limit, Rot wenn ueber Limit
- **Horizontale Linie:** `daily_review_limit` aus UserSRSSettings
- **Heute hervorgehoben**

---

### 1.4 Card-Maturity-Verteilung

**Was:** Pie/Donut-Chart das zeigt, wie viele Karten in welchem Lernstadium sind.

**Kategorien:**

| Kategorie | Kriterium | Farbe | Icon |
|-----------|----------|-------|------|
| **Neu** | Kein `CardReviewState` vorhanden | `#6c757d` (grau) | ○ |
| **Lernen** | status = `learning` oder `relearning` | `#dc3545` (rot) | ◐ |
| **Jung** | status = `review`, scheduled_days ≤ 21 | `#fd7e14` (orange) | ◑ |
| **Reif** | status = `review`, scheduled_days 22–90 | `#28a745` (gruen) | ● |
| **Gemeistert** | status = `review`, scheduled_days > 90 | `#ffc107` (gold) | ★ |
| **Suspendiert** | status = `suspended` | `#adb5bd` (hellgrau) | ⊘ |

**Berechnung von scheduled_days:**
Da `CardReviewState` den FSRS-State als JSON speichert, koennen wir `stability` extrahieren:
```python
import json
state = json.loads(card_review_state.fsrs_card_state)
stability = state.get('stability', 0)  # Naehe zu scheduled_days
```

Alternativ: `scheduled_days` aus dem letzten `ReviewLog` lesen.

**Ansichten:**
1. **Gesamt-Donut:** Alle Karten des Users
2. **Pro Lektion:** Dropdown-Auswahl der Lektion
3. **Pro Content-Typ:** Kana | Kanji | Vocabulary | Grammar
4. **Zeitverlauf:** Stacked Area Chart — wie sich die Verteilung ueber Wochen/Monate aendert

---

### 1.5 Performance nach Content-Typ

**Was:** Balkendiagramm das zeigt, wie gut der User bei verschiedenen Content-Typen abschneidet.

**Metriken pro Typ:**

| Content-Typ | Typische Retention | Typische Antwortzeit |
|------------|-------------------|---------------------|
| Kana (ひらがな/カタカナ) | 95%+ | <2 Sek |
| Kanji (漢字) | 80–90% | 3–8 Sek |
| Vocabulary (語彙) | 85–95% | 2–5 Sek |
| Grammar (文法) | 80–90% | 3–10 Sek |

**SQL-Query:**
```sql
SELECT
    lc.content_type,
    COUNT(*) as total_reviews,
    ROUND(SUM(CASE WHEN rl.rating >= 2 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as retention,
    ROUND(AVG(rl.time_taken_ms) / 1000.0, 1) as avg_seconds,
    SUM(CASE WHEN rl.rating = 1 THEN 1 ELSE 0 END) as lapses
FROM review_log rl
JOIN lesson_content lc ON rl.content_id = lc.id
WHERE rl.user_id = :uid
GROUP BY lc.content_type
```

**Visualisierung:**
- Horizontal Bar Chart
- Jeder Balken = ein Content-Typ
- Balkenlaenge = Retention-Rate
- Farbe: Gruen (>90%), Orange (80-90%), Rot (<80%)
- Rechts daneben: Durchschnittliche Antwortzeit

**Actionable Insights:**
- "Deine Kanji-Retention ist 78% — unter deinem Ziel von 90%. Erhoehe die Wiederholungsfrequenz oder vereinfache schwierige Kanji."
- "Deine Kana sind bei 97% — du koenntest die Desired Retention fuer Kana senken, um Reviews zu sparen."

---

### 1.6 Leech-Erkennung

**Was:** Karten, die trotz vieler Wiederholungen nicht gelernt werden ("Blutegel" — sie saugen Zeit ohne Fortschritt).

**Definition eines Leechs:**
```
Leech = Karte mit lapses >= 8 (konfigurierbar)
```

**Leech-Score-Berechnung:**
```python
def leech_score(card_state):
    """Hoeher = problematischer."""
    if card_state.reps == 0:
        return 0
    return card_state.lapses / max(card_state.reps, 1) * card_state.lapses
```

Gewichtet sowohl die absolute Anzahl Fehler als auch die Fehlerquote. Eine Karte mit 20 Lapses bei 25 Reviews (80% Fehler) ist schlimmer als eine mit 20 Lapses bei 200 Reviews (10% Fehler).

**Leech-Tabelle:**

```
┌──────────────────────────────────────────────────────────┐
│  Problematische Karten (8+ Fehler)            15 Leeches │
├──────────────────────────────────────────────────────────┤
│  駅 (えき) — Bahnhof        │ 12 Fehler │ 62% Quote     │
│  食べる (たべる) — essen     │ 10 Fehler │ 55% Quote     │
│  ～ている — Progressive      │  9 Fehler │ 50% Quote     │
│  ...                                                     │
├──────────────────────────────────────────────────────────┤
│  Aktionen: [Suspendieren] [Zuruecksetzen] [In Lektion]  │
└──────────────────────────────────────────────────────────┘
```

**Empfohlene Aktionen:**
1. **Suspendieren:** Karte pausieren und spaeter manuell bearbeiten
2. **Zuruecksetzen:** FSRS-State loeschen, von vorne lernen
3. **Bearbeiten:** In der Lektion oeffen und Inhalt verbessern (klarere Eselsbruecke, besseres Beispiel)

**Automatische Leech-Warnung:**
Wenn eine Karte zum Leech wird (Lapse #8), wird nach dem Rating eine Warnung angezeigt:
```
⚠️ Diese Karte bereitet dir Schwierigkeiten (8× vergessen).
Tipp: Versuche eine Eselsbruecke zu bilden, oder suspendiere die Karte fuer spaeter.
[Weiterlernen] [Suspendieren]
```

---

### 1.7 Antwortzeit-Analyse

**Was:** Wie lange braucht der User durchschnittlich zum Antworten, und was sagt das ueber sein Lernen aus?

**Metriken:**

| Metrik | Berechnung | Bedeutung |
|--------|-----------|-----------|
| Durchschnitt | `AVG(time_taken_ms)` | Allgemeine Geschwindigkeit |
| Median | `PERCENTILE_CONT(0.5)` | Robuster als Durchschnitt (Ausreisser-resistent) |
| p90 | `PERCENTILE_CONT(0.9)` | Wie lange bei schwierigen Karten |
| Trend | Gleitender Durchschnitt ueber 7 Tage | Verbesserung oder Verschlechterung? |

**Antwortzeit-Kategorien:**

| Bereich | Bedeutung |
|---------|-----------|
| < 2 Sek | Sofort gewusst (Automatisiert) |
| 2–5 Sek | Normal (Aktives Erinnern) |
| 5–15 Sek | Schwierig (Muehsames Erinnern) |
| > 15 Sek | Zu lange (Wahrscheinlich geraten oder abgelenkt) |

**Visualisierung:** Histogramm der Antwortzeiten
- X-Achse: Zeit in Sekunden (0, 2, 5, 10, 15, 30+)
- Y-Achse: Anzahl Reviews
- Farblich getrennt nach Rating (Again/Hard/Good/Easy)

**Burnout-Indikatoren:**
- Durchschnittliche Antwortzeit steigt ueber mehrere Tage → User wird muede
- Viele Reviews > 15 Sek → Konzentration laesst nach
- Anzahl Reviews/Tag faellt ploetzlich → moeglicher Motivationsverlust

---

### 1.8 Technische Umsetzung: Charting-Libraries

#### Empfehlung fuer Flask + Jinja2 (ohne React)

| Library | Zweck | Groesse | Empfehlung |
|---------|-------|---------|-----------|
| **Chart.js** | Balken, Linien, Pie, Donut | ~50 KB | Haupt-Library fuer alle Charts |
| **Cal-HeatMap** | Review-Heatmap | ~30 KB | Nur fuer die Heatmap |

**Warum Chart.js?**
- Leichtgewichtig (~50 KB gzipped)
- 2M+ Downloads/Woche auf npm
- Einfache API, perfekt fuer Jinja2-Templates
- Keine Framework-Abhaengigkeit (Vanilla JS)
- Responsive out of the box

**Warum NICHT ApexCharts/Plotly/D3?**
- ApexCharts (~100 KB): Mehr Features, aber unnoetige Komplexitaet
- Plotly.js (~3 MB): Viel zu gross fuer unseren Anwendungsfall
- D3.js: Steile Lernkurve, nur sinnvoll fuer hochgradig individuelle Visualisierungen

**Warum Cal-HeatMap separat?**
- Chart.js hat keinen nativen Heatmap-Typ
- Cal-HeatMap ist spezialisiert auf Kalender-Heatmaps
- Leichtgewichtig, Vanilla JS, gute Dokumentation

#### Integration in Flask/Jinja2

```html
<!-- stats.html -->
{% block extra_css %}
<link rel="stylesheet" href="https://unpkg.com/cal-heatmap/cal-heatmap.css">
{% endblock %}

{% block extra_js %}
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<script src="https://unpkg.com/cal-heatmap/cal-heatmap.min.js"></script>

<script>
// Daten vom Backend (via Jinja2)
const reviewData = {{ review_data | tojson }};
const retentionData = {{ retention_data | tojson }};

// Chart.js: Retention-Kurve
new Chart(document.getElementById('retentionChart'), {
    type: 'line',
    data: retentionData,
    options: {
        responsive: true,
        plugins: { legend: { position: 'top' } },
        scales: { y: { min: 0, max: 100, title: { text: 'Retention %' } } }
    }
});

// Cal-HeatMap: Review-Aktivitaet
const cal = new CalHeatmap();
cal.paint({
    data: { source: reviewData, x: 'date', y: 'count' },
    range: 12,
    domain: { type: 'month' },
    subDomain: { type: 'day', radius: 2 },
    scale: { color: { range: ['#ebedf0', '#9be9a8', '#40c463', '#30a14e', '#216e39'], type: 'quantize' } }
});
</script>
{% endblock %}
```

#### Daten-Loading-Pattern

**Option A: Jinja2-Inline (fuer initiale Daten)**
```python
@app.route('/review/stats')
def review_stats():
    data = SRSService.get_extended_stats(current_user.id)
    return render_template('review_stats.html', **data)
```

**Option B: AJAX (fuer interaktive Filter)**
```javascript
// User aendert Zeitraum → neuer Fetch
async function loadStats(period) {
    const resp = await fetch(`/api/srs/stats/extended?period=${period}`);
    const data = await resp.json();
    updateCharts(data);
}
```

**Empfehlung:** Kombination. Initiale Daten via Jinja2 (kein extra Request), interaktive Updates via AJAX.

#### Performance-Ueberlegungen

| Massnahme | Grund |
|-----------|-------|
| **Server-seitiges Caching** | Stats-Berechnung ist teuer bei vielen ReviewLogs. Redis oder `@lru_cache` mit TTL von 5 Minuten |
| **Aggregat-Tabelle** | Fuer Heatmap: Taeglich aggregierte Review-Counts statt Einzel-Queries auf Millionen ReviewLogs |
| **Lazy Loading** | Charts erst laden wenn sichtbar (Intersection Observer) |
| **Date-Range begrenzen** | Default: Letzte 30 Tage. Laengere Zeitraeume nur auf Klick |

---

## 2. Gamification

### Psychologische Grundlage: Self-Determination Theory (SDT)

Bevor wir Features definieren: Gamification ist nur dann effektiv, wenn sie die drei psychologischen Grundbeduerfnisse nach Deci & Ryan unterstuetzt:

| Beduerfnis | Was es bedeutet | Wie wir es bedienen |
|-----------|----------------|---------------------|
| **Autonomie** | User hat Kontrolle ueber sein Lernen | Lernmodi waehlen, Desired Retention anpassen, Karten suspendieren |
| **Kompetenz** | User erlebt Fortschritt und Meisterschaft | Level-System, Badges, SRS-Level-Progression |
| **Verbundenheit** | User fuehlt sich als Teil einer Gemeinschaft | Streak-Anzeige, Achievement-Sharing (spaeter) |

**WICHTIG:** Jedes Gamification-Feature muss mindestens eines dieser Beduerfnisse bedienen. Features die nur "Dopamin-Kicks" erzeugen ohne echten Lernfortschritt zu spiegeln → loeschen.

---

### 2.1 XP-System

#### XP-Quellen

| Aktion | XP | Grund |
|--------|-----|-------|
| Review mit Again | 2 XP | Immerhin versucht |
| Review mit Hard | 5 XP | Erinnert, aber schwierig |
| Review mit Good | 10 XP | Standard-Lernerfolg |
| Review mit Easy | 12 XP | Sofort gewusst |
| Neue Karte erstmals gelernt | 15 XP | Neues Material |
| Streak-Tag | 20 XP | Konsistenz belohnen |
| Lektion abgeschlossen | 50 XP | Meilenstein |

**Anti-Pattern: XP-Farming vermeiden**
- Duolingo hatte das Problem, dass User sinnlos Lektionen wiederholten nur fuer XP
- **Loesung:** XP-Cap pro Tag (z.B. 500 XP) oder abnehmende XP nach dem 100. Review

#### XP-to-Level-Kurve

**Polynomiale Kurve (empfohlen):**
```python
def xp_for_level(level):
    """XP benoetigt fuer ein bestimmtes Level."""
    return int(100 * (level ** 1.5))

# Level 1: 100 XP   (~ 10 Reviews)
# Level 5: 1'118 XP  (~ 112 Reviews)
# Level 10: 3'162 XP (~ 316 Reviews)
# Level 20: 8'944 XP (~ 894 Reviews)
# Level 50: 35'355 XP
```

**Warum polynomial statt exponentiell?**
- Exponentiell (× 1.2 pro Level): Spaetere Levels werden unbezwingbar → Frustration
- Linear (+100 pro Level): Kein Erfolgsgefuehl, immer gleich
- Polynomial (^1.5): Frueher sichtbarer Fortschritt, spaeter anspruchsvoller aber machbar

#### Level-Anzeige

```
┌──────────────────────────────────────┐
│  Level 12 — Lehrling                 │
│  ████████████░░░░░░░  2'480 / 4'157  │
│                         XP           │
└──────────────────────────────────────┘
```

**Level-Titel (Japanisch-thematisch):**

| Level | Titel (DE) | Titel (JP) |
|-------|-----------|-----------|
| 1–5 | Anfaenger | 初心者 (Shoshinsha) |
| 6–10 | Schueler | 学生 (Gakusei) |
| 11–15 | Lehrling | 見習い (Minarai) |
| 16–25 | Fortgeschritten | 上級者 (Joukyuusha) |
| 26–40 | Experte | 達人 (Tatsujin) |
| 41–50 | Meister | 師匠 (Shishou) |
| 50+ | Grossmeister | 名人 (Meijin) |

---

### 2.2 Karten-Level-Progression (WaniKani-Modell)

Jede einzelne Karte durchlaeuft sichtbare Stufen — das ist DAS Kern-Gamification-Element bei WaniKani.

#### SRS-Stufen (erweitert gegenueber Phase 5)

| Stufe | Name | Intervall-Bereich | Farbe | Icon |
|-------|------|------------------|-------|------|
| 0 | **Neu** | Noch nie gesehen | `#6c757d` | ○ |
| 1 | **Anfaenger 1** | < 4 Stunden | `#ff6b6b` | ◔ |
| 2 | **Anfaenger 2** | 4h – 1 Tag | `#ee5a24` | ◑ |
| 3 | **Anfaenger 3** | 1 – 3 Tage | `#f0932b` | ◕ |
| 4 | **Anfaenger 4** | 3 – 7 Tage | `#ffbe76` | ● |
| 5 | **Vertraut 1** | 1 – 2 Wochen | `#6ab04c` | ◆ |
| 6 | **Vertraut 2** | 2 – 4 Wochen | `#009432` | ◆◆ |
| 7 | **Meister** | 1 – 3 Monate | `#9b59b6` | ★ |
| 8 | **Erleuchtet** | 3 – 6 Monate | `#f1c40f` | ✦ |
| 9 | **Gemeistert** | 6+ Monate | `#2ecc71` | ✧ |

**Stufen-Berechnung:**
```python
def get_srs_stage(stability_days):
    """Bestimmt die SRS-Stufe basierend auf FSRS Stability."""
    thresholds = [0, 0.17, 1, 3, 7, 14, 30, 90, 180]
    stage_names = [
        'Neu', 'Anfaenger 1', 'Anfaenger 2', 'Anfaenger 3', 'Anfaenger 4',
        'Vertraut 1', 'Vertraut 2', 'Meister', 'Erleuchtet', 'Gemeistert'
    ]
    for i, threshold in enumerate(reversed(thresholds)):
        if stability_days >= threshold:
            return len(thresholds) - i - 1, stage_names[len(thresholds) - i - 1]
    return 0, 'Neu'
```

**Visuelle Darstellung auf der Karte:**
- Kleiner farbiger Punkt oben rechts (wie in Phase 5)
- Zusaetzlich: Stufen-Name im Tooltip bei Hover
- In der Review-Session: Mini-Badge neben Lektion/Typ-Info

**Stufen-Up/Down Animation:**
- Karte steigt eine Stufe auf → kurze Glow-Animation + Sound
- Karte faellt ab (Again bei hoher Stufe) → Kurzes Rot-Blinken

---

### 2.3 Achievement/Badge-System

#### Design-Prinzipien (aus Forschung)
1. **Nur echte Meilensteine** — keine "Du hast die App geoeffnet"-Badges
2. **Max. 4–5 aktive Kategorien** — mehr fuehrt zu Badge Fatigue
3. **Progressive Narrative** — Badges erzaehlen eine Geschichte des Lernfortschritts
4. **Seltene Badges sind wertvoller** — nicht zu viele vergeben

#### Badge-Kategorien

**Kategorie 1: Konsistenz (Streak-basiert)**

| Badge | Bedingung | Icon | Seltenheit |
|-------|----------|------|-----------|
| Erste Schritte | 3 Tage Streak | 🌱 | Common |
| Bestaendig | 7 Tage Streak | 🌿 | Common |
| Unaufhaltsam | 30 Tage Streak | 🌳 | Uncommon |
| Ausdauer-Meister | 100 Tage Streak | 🏔️ | Rare |
| Unerschuetterlich | 365 Tage Streak | 🌋 | Legendary |

**Kategorie 2: Volumen (Karten-Meilensteine)**

| Badge | Bedingung | Icon | Seltenheit |
|-------|----------|------|-----------|
| Erster Review | 1 Review abgeschlossen | 📖 | Common |
| Fleissig | 100 Reviews gesamt | 📚 | Common |
| Review-Maschine | 1'000 Reviews gesamt | ⚡ | Uncommon |
| Unersaettlich | 5'000 Reviews gesamt | 🔥 | Rare |
| Lernlegende | 10'000 Reviews gesamt | 💎 | Legendary |

**Kategorie 3: Meisterschaft (SRS-Level)**

| Badge | Bedingung | Icon | Seltenheit |
|-------|----------|------|-----------|
| Erste Meisterung | 1 Karte auf "Gemeistert" (Stufe 9) | ⭐ | Common |
| Zehn Gemeistert | 10 Karten gemeistert | 🌟 | Uncommon |
| Hundert Gemeistert | 100 Karten gemeistert | 💫 | Rare |
| Kana-Meister | Alle Hiragana + Katakana gemeistert | あ | Rare |
| Kanji-Kenner | 100 Kanji gemeistert | 漢 | Rare |

**Kategorie 4: JLPT-Meilensteine**

| Badge | Bedingung | Icon | Seltenheit |
|-------|----------|------|-----------|
| JLPT N5 Bereit | Alle N5-Vokabeln "Vertraut" oder hoeher | N5 | Uncommon |
| JLPT N4 Bereit | Alle N4-Vokabeln "Vertraut" oder hoeher | N4 | Rare |
| JLPT N3 Bereit | Alle N3-Vokabeln "Vertraut" oder hoeher | N3 | Epic |
| JLPT N2 Bereit | ... | N2 | Legendary |
| JLPT N1 Bereit | ... | N1 | Mythic |

#### Badge-UI

**Badge-Vergabe (Toast-Notification):**
```
┌───────────────────────────────────────┐
│  🏆 Neues Achievement!               │
│                                       │
│  📚 Fleissig                         │
│  "100 Reviews abgeschlossen"         │
│                                       │
│  [Anzeigen]            [Schliessen]  │
└───────────────────────────────────────┘
```

**Badge-Galerie (eigene Seite oder Modal):**
```
┌───────────────────────────────────────────────┐
│  Achievements           12 / 28 freigeschaltet│
├───────────────────────────────────────────────┤
│  Konsistenz                                   │
│  [🌱✓] [🌿✓] [🌳✓] [🏔️○] [🌋○]              │
│                                               │
│  Volumen                                      │
│  [📖✓] [📚✓] [⚡○] [🔥○] [💎○]                │
│                                               │
│  Meisterschaft                                │
│  [⭐✓] [🌟✓] [💫○] [あ○] [漢○]                │
│                                               │
│  JLPT                                         │
│  [N5✓] [N4✓] [N3○] [N2○] [N1○]              │
└───────────────────────────────────────────────┘
```

- Freigeschaltete Badges: Voll-Farbe mit Checkmark
- Gesperrte Badges: Ausgegraut mit Fortschritts-Info bei Hover
- Hover-Info: "Noch 37 Reviews bis zum naechsten Badge"

#### Datenmodell

```python
class UserAchievement(db.Model):
    """Freigeschaltete Achievements pro User."""
    __tablename__ = 'user_achievement'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    achievement_key = db.Column(db.String(50), nullable=False)  # z.B. 'streak_7'
    unlocked_at = db.Column(db.DateTime, default=datetime.utcnow)
    notified = db.Column(db.Boolean, default=False)  # Wurde die Toast-Notification gezeigt?
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'achievement_key', name='uq_user_achievement'),
    )
```

**Achievement-Definitionen in Code (nicht DB):**
```python
# app/achievements.py
ACHIEVEMENTS = {
    'streak_3': {'name': 'Erste Schritte', 'icon': '🌱', 'desc': '3 Tage Streak', 'check': lambda u: u.current_streak >= 3},
    'streak_7': {'name': 'Bestaendig', 'icon': '🌿', 'desc': '7 Tage Streak', 'check': lambda u: u.current_streak >= 7},
    'reviews_100': {'name': 'Fleissig', 'icon': '📚', 'desc': '100 Reviews', 'check': lambda u: u.total_reviews >= 100},
    # ...
}
```

#### Achievement-Check: Wann pruefen?

**Nach jedem Review** (in `SRSService.rate_card()`):
```python
def check_achievements(user_id):
    """Prueft und vergibt neue Achievements nach einem Review."""
    user = User.query.get(user_id)
    existing = {a.achievement_key for a in UserAchievement.query.filter_by(user_id=user_id).all()}
    
    new_achievements = []
    for key, definition in ACHIEVEMENTS.items():
        if key not in existing and definition['check'](user):
            achievement = UserAchievement(user_id=user_id, achievement_key=key)
            db.session.add(achievement)
            new_achievements.append(definition)
    
    if new_achievements:
        db.session.commit()
    
    return new_achievements  # Werden als Teil der /api/srs/rate-Response zurueckgegeben
```

---

### 2.4 Streak-Erweiterungen

Phase 5 integriert bereits das bestehende `User.update_streak()`. Phase 6 erweitert es:

#### Streak Freeze

**Was:** Ein "Freipass" der den Streak schuetzt, wenn der User einen Tag verpasst.

**Regeln:**
- Jeder User bekommt **1 Streak Freeze pro Woche** (gratis, automatisch am Montag)
- Streak Freeze wird **automatisch** aktiviert, wenn ein Tag ohne Review vergeht
- Kein Kauf/Premium noetig (kleines User-Base, kein Monetarisierungsdruck)

**Datenmodell-Erweiterung:**
```python
# In UserSRSSettings (bestehend):
streak_freezes_available = db.Column(db.Integer, default=1)
last_freeze_replenish = db.Column(db.Date)  # Letzter Montag an dem Freeze aufgefuellt wurde
```

**Streak Freeze in update_streak() integrieren:**
```python
def update_streak(self):
    today = date.today()
    if self.last_study_date == today:
        return  # Schon heute gelernt
    
    if self.last_study_date == today - timedelta(days=1):
        # Gestern gelernt → Streak weiter
        self.current_streak += 1
    elif self.srs_settings and self.srs_settings.streak_freezes_available > 0:
        # Gestern nicht gelernt, aber Freeze verfuegbar
        self.srs_settings.streak_freezes_available -= 1
        # Streak bleibt (kein +1, aber auch kein Reset)
    else:
        # Streak verloren
        self.current_streak = 1
    
    self.last_study_date = today
    self.longest_streak = max(self.longest_streak, self.current_streak)
```

#### Streak-Meilensteine

Bei bestimmten Streak-Laengen: besondere Celebration-Animationen

| Streak | Celebration |
|--------|-----------|
| 7 Tage | Confetti + "1 Woche!" Badge |
| 30 Tage | Groessere Animation + "1 Monat!" Badge |
| 100 Tage | Feuerwerk + "Unglaublich!" Badge |
| 365 Tage | Epische Animation + "1 Jahr!" Badge |

#### Streak-Gefahr-Warnung

Auf der Startseite, wenn der User heute noch nicht gelernt hat:
```
⚠️ Dein Streak (23 Tage) ist in Gefahr!
Du hast heute noch keine Karten wiederholt.
[Jetzt 5 Minuten lernen]
```

**Wichtig: Kein aggressives Pushing.** Keine Push-Notifications, keine E-Mails, kein trauriger Eule. Nur eine dezente Warnung auf der Startseite.

---

### 2.5 Session-Gamification

#### Perfekte Session

Wenn alle Karten einer Session mit Good/Easy bewertet werden:
```
🎯 Perfekte Session!
Alle 15 Karten beim ersten Versuch gewusst.
+50 Bonus-XP
```

#### Speed-Bonus

Wenn die durchschnittliche Antwortzeit unter 3 Sekunden liegt:
```
⚡ Schnell wie der Blitz!
Durchschnittliche Antwortzeit: 2.1 Sekunden
```

**Kein Extra-XP dafuer** — Geschwindigkeit soll nicht ueber Gruendlichkeit belohnt werden.

#### Session-Zusammenfassung erweitern (gegenueber Phase 4)

```
┌─────────────────────────────────────────────┐
│  Session beendet!                           │
│                                             │
│  ✅ 25 Karten wiederholt       +250 XP      │
│  ⏱  8 Minuten                              │
│  📈 Erfolgsrate: 92%          🎯 Perfekt!   │
│  🔥 Streak: 24 Tage                        │
│                                             │
│  Stufen-Aenderungen:                        │
│  ↑ 3 Karten aufgestiegen                   │
│  ↓ 1 Karte zurueckgefallen                 │
│  ★ 2 Karten neu gemeistert                 │
│                                             │
│  🏆 Neues Badge: "Review-Maschine"         │
│     1'000 Reviews abgeschlossen!            │
│                                             │
│  [Weiter lernen]  [Statistiken]  [Fertig]  │
└─────────────────────────────────────────────┘
```

---

### 2.6 JLPT-Meilensteine

**Was:** Der User sieht, wie weit er auf dem Weg zu den offiziellen JLPT-Pruefungen ist.

**Voraussetzung:** Lektionen/Content-Items muessen mit JLPT-Level getaggt sein. Das ist teilweise schon der Fall (Vocabulary-Modell hat ein `jlpt_level`-Feld).

**Anzeige auf der Stats-Seite:**

```
JLPT-Fortschritt
┌─────────────────────────────────────────┐
│  N5  ████████████████████░░  89%        │
│       Vokabeln: 720/800  Kanji: 95/103  │
│                                          │
│  N4  ████████░░░░░░░░░░░░░  42%        │
│       Vokabeln: 340/800  Kanji: 78/181  │
│                                          │
│  N3  ██░░░░░░░░░░░░░░░░░░░  11%        │
│       Vokabeln: 180/1'600  Kanji: 33/350│
└─────────────────────────────────────────┘
```

**Berechnung:**
- Zaehlt nur Karten auf SRS-Stufe "Vertraut 1" (Stufe 5) oder hoeher
- Getrennt nach Vokabeln und Kanji
- Prozent = (Vertraute Karten) / (Gesamt-Karten auf diesem JLPT-Level)

---

### 2.7 Anti-Patterns: Was wir NICHT implementieren

Basierend auf der Forschung zu kontraproduktiver Gamification:

| Anti-Pattern | Warum nicht | Quelle |
|-------------|------------|--------|
| **Leaderboards** | Negative Sozialvergleiche, User-Base zu klein, Competitive = weniger Learning-Fokus | Koivisto & Hamari 2019 |
| **Push-Notifications** | Anxiety, Habituation nach 2 Wochen, kein nachhaltiger Effekt | Customer.io Research |
| **XP-Multiplier** | Fuehrt zu XP-Farming statt echtem Lernen | Duolingo's eigener Rueckbau 2024 |
| **Paid Streak Freezes** | Monetarisierung von Lernangst = ethisch fragwuerdig | Deceptive Patterns Analyse |
| **Trauriges Maskottchen** | Guilt-based Motivation = unsustainable, erhoehte App-Deinstallation | Growth Engineering |
| **Zu viele Badges** | Badge Fatigue ab >20 sichtbare Badges. Koivisto & Hamari: Badge-Komplexitaet korreliert positiv mit Burnout | Springer 2024 |
| **Taegl. Pflicht-Aufgaben** | "Daily Quests" erzwingen Verhalten → unterminierten Autonomie (SDT) | Deci & Ryan, SDT Framework |

**Kern-Regel:** Gamification soll echten Lernfortschritt spiegeln, nicht kuenstlich Engagement erzeugen.

---

## 3. Karten-Browser

### 3.1 Layout & Navigation

**Route:** `/review/browse`

**Desktop-Layout:**
```
┌──────────────────────────────────────────────────────────────────┐
│  Karten-Browser                                     1'247 Karten │
├────────────┬─────────────────────────────────────────────────────┤
│ FILTER     │  [Suche: 駅, Bahnhof, えき...]           [⚙ Filter]│
│            │                                                     │
│ Status     │  ┌─────┬────────┬────────┬────────┬──────┬────────┐│
│ ☑ Neu (42) │  │ Karte│ Typ    │ Lektion│ Stufe  │ Naech│Lapses ││
│ ☑ Lernen   │  ├─────┼────────┼────────┼────────┼──────┼────────┤│
│ ☑ Jung     │  │ 駅   │ Vocab  │ L12    │ ◆ Vert.│ 3 T  │ 2     ││
│ ☑ Reif     │  │ あ   │ Kana   │ L1     │ ★ Meis.│ 45 T │ 0     ││
│ ☐ Susp.    │  │ 食べる│ Vocab  │ L8     │ ◔ Anf.1│ 4 Std│ 8 ⚠  ││
│            │  │ ...  │        │        │        │      │        ││
│ Typ        │  ├─────┴────────┴────────┴────────┴──────┴────────┤│
│ ☑ Kana     │  │  ☐ Alle    [Suspendieren] [Zuruecksetzen]      ││
│ ☑ Kanji    │  │             [Exportieren]                       ││
│ ☑ Vocab    │  ├─────────────────────────────────────────────────┤│
│ ☑ Grammar  │  │  ← 1 2 3 ... 25 →     50 pro Seite            ││
│            │  └─────────────────────────────────────────────────┘│
│ Lektion    │                                                     │
│ [Alle ▼]   │                                                     │
│            │                                                     │
│ JLPT       │                                                     │
│ [Alle ▼]   │                                                     │
└────────────┴─────────────────────────────────────────────────────┘
```

**Mobile-Layout (< 768px):**
- Filter-Sidebar wird zu Collapsible-Panel oben
- Tabelle wird zu Card-Liste:
```
┌──────────────────────────────────┐
│  🔍 [Suche...]     [Filter ▼]   │
├──────────────────────────────────┤
│  ┌──────────────────────────┐   │
│  │ 駅 (えき)                │   │
│  │ Bahnhof                  │   │
│  │ Vocab · L12 · ◆ Vertraut │   │
│  │ Naechster Review: 3 Tage │   │
│  └──────────────────────────┘   │
│  ┌──────────────────────────┐   │
│  │ あ                       │   │
│  │ a (Hiragana)             │   │
│  │ Kana · L1 · ★ Gemeistert │   │
│  │ Naechster Review: 45 Tage│   │
│  └──────────────────────────┘   │
│  ...                             │
└──────────────────────────────────┘
```

### 3.2 Filter & Suche

#### Textsuche

Sucht gleichzeitig in:
- Japanischem Text (Kana, Kanji, Woerter)
- Romanisierung/Lesung
- Bedeutung (Deutsch/Englisch)
- Lektionsname

**Implementierung:**
```python
@srs_bp.route('/api/srs/browse')
@login_required
def browse_cards():
    q = request.args.get('q', '').strip()
    
    query = db.session.query(CardReviewState, LessonContent).join(
        LessonContent, CardReviewState.content_id == LessonContent.id
    ).filter(CardReviewState.user_id == current_user.id)
    
    if q:
        # Suche in referenzierten Tabellen (Vocabulary, Kana, Kanji, Grammar)
        query = query.filter(db.or_(
            LessonContent.detail_text.ilike(f'%{q}%'),
            # Erweiterte Suche per Subquery auf Vocabulary/Kana/etc.
        ))
    
    # ... Filter, Sortierung, Pagination
```

**HTMX-Live-Suche (Debounced):**
```html
<input type="search"
       name="q"
       hx-get="/api/srs/browse"
       hx-trigger="input changed delay:300ms"
       hx-target="#card-table-body"
       hx-include="[name='status'], [name='type'], [name='lesson']"
       placeholder="Suche: 駅, Bahnhof, えき...">
```

#### Filter-Optionen

| Filter | Optionen | Implementierung |
|--------|---------|----------------|
| **Status** | Neu, Lernen, Jung, Reif, Gemeistert, Suspendiert | Checkboxes (Mehrfachauswahl) |
| **Content-Typ** | Kana, Kanji, Vocabulary, Grammar | Checkboxes |
| **Lektion** | Dropdown mit allen Lektionen | `<select>` mit Suche |
| **JLPT-Level** | N5, N4, N3, N2, N1 | Checkboxes |
| **Leech** | Nur Leeches anzeigen (lapses >= 8) | Toggle |
| **Faellig** | Nur heute faellige Karten | Toggle |

#### Filter-Persistenz
Filter-Status wird in URL-Query-Parametern gespeichert, sodass:
- Browser-Zurueck funktioniert
- Links geteilt werden koennen
- Seiten-Reload den Filter behaelt

```
/review/browse?status=learning,young&type=vocabulary&lesson=12&q=essen
```

### 3.3 Sortierung

| Spalte | Sortierrichtung | Standard |
|--------|----------------|----------|
| Naechster Review | Aufsteigend (faelligste zuerst) | **Default** |
| Lapses | Absteigend (problematischste zuerst) | |
| SRS-Stufe | Auf-/Absteigend | |
| Erstellungsdatum | Neueste/Aelteste | |
| Lektion | Alphabetisch | |

**Server-seitige Sortierung** (nicht client-seitig), da Pagination server-seitig ist.

### 3.4 Bulk-Aktionen

#### Auswahl-Mechanik

```html
<!-- Select-All Checkbox im Tabellenkopf -->
<th><input type="checkbox" id="select-all" onchange="toggleAllCards(this)"></th>

<!-- Einzelne Checkboxes pro Zeile -->
<td><input type="checkbox" name="card_ids" value="{{ state.id }}" class="card-checkbox"></td>
```

#### Verfuegbare Aktionen

| Aktion | Beschreibung | Bestaetigung? |
|--------|-------------|--------------|
| **Suspendieren** | Karten pausieren (keine Reviews mehr) | Nein (reversibel) |
| **Aktivieren** | Suspendierte Karten reaktivieren | Nein |
| **Zuruecksetzen** | FSRS-State loeschen, Karte wird "Neu" | **Ja** (Modal: "X Karten zuruecksetzen?") |
| **Exportieren** | Ausgewaehlte Karten als CSV/JSON herunterladen | Nein |

**Bulk-API:**
```
POST /api/srs/bulk
Body: {
    action: "suspend" | "unsuspend" | "reset",
    card_state_ids: [1, 2, 3, ...]
}
Response: { affected: 3, errors: [] }
```

**Sicherheit:**
- CSRF-Token (wie bei allen POST-Requests)
- Server-seitige Validierung: Nur eigene Karten (user_id check)
- Max. 100 Karten pro Bulk-Aktion
- `reset` erfordert Bestaetigung im Frontend

#### Floating Action Bar

Erscheint wenn mindestens 1 Karte ausgewaehlt ist:

```
┌───────────────────────────────────────────────────────────────┐
│  3 Karten ausgewaehlt    [Suspendieren] [Aktivieren]         │
│                          [Zuruecksetzen] [Exportieren]        │
└───────────────────────────────────────────────────────────────┘
```

Position: Fixed am unteren Bildschirmrand, mit Slide-up-Animation.

### 3.5 Responsive Design

**Bestehende Admin-Patterns wiederverwenden:**

Aus dem Codebase-Analyse sind folgende Patterns bereits etabliert:
- Tailwind `flex-col sm:flex-row` fuer responsive Layouts (manage_vocabulary.html)
- Alpine.js `x-data` fuer Filter-Tabs (manage_kana.html)
- Counter-Badges fuer Statistiken (manage_kana.html)
- Client-seitige Filterung via `oninput="filterVocab()"` (manage_vocabulary.html)

**Fuer den Karten-Browser adaptieren:**
```css
/* Desktop: Sidebar + Tabelle */
@media (min-width: 768px) {
    .browse-layout { display: grid; grid-template-columns: 220px 1fr; gap: 1rem; }
}

/* Mobile: Collapsible Filter + Card-Liste */
@media (max-width: 767px) {
    .browse-layout { display: block; }
    .browse-sidebar { display: none; }
    .browse-sidebar.active { display: block; }
    
    /* Tabelle → Card-Layout */
    .card-table { display: block; }
    .card-table tr { display: block; border: 1px solid #e5e7eb; border-radius: 8px; margin-bottom: 0.5rem; padding: 0.75rem; }
    .card-table td { display: block; text-align: left; }
    .card-table td::before { content: attr(data-label); font-weight: 600; margin-right: 0.5rem; }
}
```

### 3.6 Keyboard-Navigation

| Taste | Aktion |
|-------|--------|
| `/` | Fokus auf Suchfeld |
| `Tab` | Durch Filter navigieren |
| `↑↓` | Durch Kartenzeilen navigieren |
| `Space` | Karte auswaehlen/abwaehlen |
| `Enter` | Karten-Detail oeffnen |
| `Ctrl+A` | Alle Karten der aktuellen Seite auswaehlen |
| `Escape` | Auswahl aufheben / Filter schliessen |

### 3.7 Karten-Detail-Modal

Klick auf eine Karte oeffnet ein Modal mit:

```
┌──────────────────────────────────────────┐
│  駅 (えき) — Bahnhof              [✕]   │
├──────────────────────────────────────────┤
│                                          │
│  Typ: Vocabulary                         │
│  Lektion: L12 - Wegbeschreibung          │
│  JLPT: N5                               │
│                                          │
│  SRS-Status                              │
│  ◆ Vertraut 2 (Stufe 6)                 │
│  Naechster Review: 14. April (2 Tage)    │
│  Stability: 12.4 Tage                   │
│  Difficulty: 4.2 / 10                   │
│                                          │
│  Statistiken                             │
│  Reviews: 18                             │
│  Lapses: 2                               │
│  Erfolgsrate: 89%                        │
│  Letzte Bewertung: Good (12. April)      │
│                                          │
│  Review-Verlauf                          │
│  12.04 Good  │  10.04 Good  │  06.04 Again│
│  03.04 Hard  │  02.04 Good  │  01.04 Good │
│                                          │
│  [In Lektion oeffnen] [Suspendieren]     │
│  [Zuruecksetzen]                         │
└──────────────────────────────────────────┘
```

---

## 4. Datenmodell-Erweiterungen

### Neue Modelle (zusaetzlich zu Phase 1–5)

```python
class UserAchievement(db.Model):
    """Freigeschaltete Achievements pro User."""
    __tablename__ = 'user_achievement'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    achievement_key = db.Column(db.String(50), nullable=False)
    unlocked_at = db.Column(db.DateTime, default=datetime.utcnow)
    notified = db.Column(db.Boolean, default=False)
    
    user = db.relationship('User', backref=db.backref('achievements', lazy='dynamic'))
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'achievement_key', name='uq_user_achievement'),
    )


class DailyReviewAggregate(db.Model):
    """Taeglich aggregierte Review-Statistiken (fuer Heatmap + Performance)."""
    __tablename__ = 'daily_review_aggregate'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    review_date = db.Column(db.Date, nullable=False, index=True)
    
    total_reviews = db.Column(db.Integer, default=0)
    correct_reviews = db.Column(db.Integer, default=0)   # rating >= 2
    again_count = db.Column(db.Integer, default=0)
    hard_count = db.Column(db.Integer, default=0)
    good_count = db.Column(db.Integer, default=0)
    easy_count = db.Column(db.Integer, default=0)
    total_time_ms = db.Column(db.BigInteger, default=0)
    xp_earned = db.Column(db.Integer, default=0)
    new_cards_learned = db.Column(db.Integer, default=0)
    cards_leveled_up = db.Column(db.Integer, default=0)
    cards_leveled_down = db.Column(db.Integer, default=0)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'review_date', name='uq_user_daily_agg'),
    )
```

### Erweiterungen bestehender Modelle

```python
# User-Modell (bestehend, erweitern):
class User(db.Model):
    # ... bestehende Felder ...
    total_xp = db.Column(db.Integer, default=0)          # Bereits vorhanden
    level = db.Column(db.Integer, default=1)              # NEU
    total_reviews = db.Column(db.Integer, default=0)      # NEU (Cache fuer Achievement-Checks)
    total_mastered = db.Column(db.Integer, default=0)     # NEU

# UserSRSSettings (bestehend, erweitern):
class UserSRSSettings(db.Model):
    # ... bestehende Felder ...
    streak_freezes_available = db.Column(db.Integer, default=1)  # NEU
    last_freeze_replenish = db.Column(db.Date)                   # NEU
    leech_threshold = db.Column(db.Integer, default=8)           # NEU
```

---

## 5. API-Endpoints

### Statistik-Endpoints

```
GET /api/srs/stats/extended
  Query: ?period=30d|90d|365d|all
  Response: {
    heatmap_data: [{ date: "2026-04-12", count: 42 }, ...],
    retention_by_interval: [{ range: "1-7d", retention: 92.1, count: 150 }, ...],
    forecast: { "2026-04-13": 25, "2026-04-14": 18, ... },
    maturity_distribution: { new: 42, learning: 15, young: 120, mature: 380, mastered: 95, suspended: 5 },
    performance_by_type: [{ type: "vocabulary", retention: 88.5, avg_time: 3.2, lapses: 45 }, ...],
    leeches: [{ content_id: 42, word: "駅", lapses: 12, failure_rate: 62.5 }, ...],
    true_retention: 91.2,
    desired_retention: 90.0
  }

GET /api/srs/stats/heatmap
  Query: ?year=2026
  Response: [{ date: "2026-01-01", count: 0 }, { date: "2026-01-02", count: 15 }, ...]

GET /api/srs/stats/forecast
  Query: ?days=30
  Response: [{ date: "2026-04-13", due_count: 25 }, ...]
```

### Gamification-Endpoints

```
GET /api/srs/achievements
  Response: {
    unlocked: [{ key: "streak_7", name: "Bestaendig", icon: "🌿", unlocked_at: "..." }, ...],
    available: [{ key: "streak_30", name: "Unaufhaltsam", icon: "🌳", progress: 23, target: 30 }, ...],
    new_achievements: [...]  // Noch nicht angezeigte (notified=false)
  }

POST /api/srs/achievements/acknowledge
  Body: { achievement_keys: ["streak_7", "reviews_100"] }
  → Setzt notified=true

GET /api/srs/xp
  Response: {
    total_xp: 2480,
    level: 12,
    level_name: "Lehrling",
    xp_current_level: 480,
    xp_next_level: 4157,
    xp_today: 120
  }
```

### Browse-Endpoints

```
GET /api/srs/browse
  Query: ?q=駅&status=learning,young&type=vocabulary&lesson_id=12&jlpt=N5
         &sort=due_date&order=asc&page=1&per_page=50&leech=true
  Response: {
    cards: [{ 
        state_id: 1, content_id: 42, content_type: "vocabulary",
        word: "駅", reading: "えき", meaning: "Bahnhof",
        lesson_title: "Wegbeschreibung", jlpt: "N5",
        srs_stage: 6, srs_stage_name: "Vertraut 2", srs_color: "#009432",
        due_date: "2026-04-14", lapses: 2, reps: 18,
        is_leech: false
    }, ...],
    total: 1247,
    page: 1,
    pages: 25
  }

GET /api/srs/browse/:state_id
  Response: { ... detaillierte Karten-Info inkl. Review-Verlauf ... }

POST /api/srs/bulk
  Body: { action: "suspend"|"unsuspend"|"reset", card_state_ids: [1, 2, 3] }
  Response: { affected: 3, errors: [] }

GET /api/srs/export
  Query: ?card_state_ids=1,2,3&format=csv|json
  Response: CSV/JSON Download
```

---

## 6. Technologie-Entscheidungen

| Entscheidung | Wahl | Grund |
|-------------|------|-------|
| **Charting** | Chart.js + Cal-HeatMap | Leichtgewichtig, kein Framework noetig, ~80 KB total |
| **Filter-UI** | HTMX + Alpine.js | Bereits im Projekt (admin_views), Server-seitiges Rendering |
| **Pagination** | Server-side Limit-Offset | Datenmenge <100K Karten, einfach, ausreichend performant |
| **Stats-Caching** | DailyReviewAggregate-Tabelle | Taeglich aggregieren statt jedes Mal Millionen ReviewLogs scannen |
| **Achievement-Logik** | Python-Code, nicht DB | Definitionen aenderbar ohne Migration, Checks in `rate_card()` |
| **XP-Berechnung** | In `SRSService.rate_card()` | Inline, kein Extra-Service noetig |
| **Mobile Tables** | CSS Card-Layout (<768px) | Bewaehertes Pattern aus manage_vocabulary.html |

---

## 7. Implementierungs-Reihenfolge

Phase 6 ist modular — die Sub-Features koennen unabhaengig voneinander implementiert werden.

### 6a: Karten-Browser (~3 Tage)

**Warum zuerst:** Gibt den Usern sofort Kontrolle ueber ihre Karten (Autonomie/SDT). Baut auf bestehenden Admin-Patterns auf.

| Tag | Was |
|-----|-----|
| 1 | API: `/api/srs/browse` mit Filter/Suche/Pagination + `/api/srs/bulk` |
| 2 | Template: `review_browse.html` — Tabelle, Filter-Sidebar, Suche |
| 3 | Mobile-Layout, Bulk-Aktionen, Karten-Detail-Modal, Tests |

### 6b: Erweiterte Statistiken (~4 Tage)

**Warum als zweites:** Gibt Usern Einblick in ihr Lernen (Kompetenz/SDT). Benoetigt ReviewLog-Daten aus den ersten Wochen mit SRS.

| Tag | Was |
|-----|-----|
| 1 | `DailyReviewAggregate`-Modell + Migration + Aggregations-Job |
| 2 | API: `/api/srs/stats/extended` — alle Metriken berechnen |
| 3 | Template: `review_stats.html` — Chart.js Integration (Retention, Performance, Forecast) |
| 4 | Cal-HeatMap Integration, Leech-Tabelle, Mobile-Optimierung, Tests |

### 6c: Gamification (~3 Tage)

**Warum zuletzt:** Baut auf Statistiken auf, braucht Daten aus mehreren Wochen SRS-Nutzung.

| Tag | Was |
|-----|-----|
| 1 | `UserAchievement`-Modell + Migration + Achievement-Definitionen + XP-Logik |
| 2 | Achievement-Check in `rate_card()`, Badge-Galerie-UI, Toast-Notifications |
| 3 | Streak-Freeze, Session-Zusammenfassung erweitern, JLPT-Fortschritt, Tests |

### Gesamt-Timeline: ~10 Tage

```
Woche 1: 6a (Browser) + 6b Start (Backend)
Woche 2: 6b (Stats-Frontend) + 6c (Gamification)
```

---

## 8. Risiken & Anti-Patterns

### Technische Risiken

| Risiko | Massnahme |
|--------|-----------|
| **Stats-Queries zu langsam** | DailyReviewAggregate als Materialized View. Cronjob oder nach jedem Review inkrementell updaten |
| **Chart.js zu gross** | Tree-shaking: Nur benoetigte Module importieren (`import { Chart } from 'chart.js/auto'`) |
| **Heatmap kaputt auf Safari** | Cal-HeatMap Safari-Kompatibilitaet testen. Fallback: einfache Tabelle |
| **Bulk-Aktionen Race Condition** | Optimistic Locking via `updated_at`. Bei Konflikt: Retry oder Fehlermeldung |
| **Achievement-Spam** | Max. 1 Achievement-Toast gleichzeitig. Queue fuer mehrere |

### Psychologische Risiken

| Risiko | Massnahme |
|--------|-----------|
| **Gamification verdraengt intrinsische Motivation** | XP/Badges nur fuer echte Lernfortschritte, nicht fuer App-Nutzung |
| **Badge Fatigue** | Max. 28 Badges total, 4 Kategorien, keine trivialen Badges |
| **Streak Anxiety** | Gratis Streak Freeze, keine Push-Notifications, kein trauriges Maskottchen |
| **Leech-Frustration** | Leech-Warnung als Hilfe formulieren, nicht als Kritik. Actionable Tipps anbieten |
| **Stats-Obsession** | Stats-Seite nicht als Default-Landingpage. Review-Seite bleibt primaer |

### Was wir bewusst NICHT bauen

| Feature | Grund |
|---------|-------|
| Leaderboards | User-Base zu klein, negative Sozialvergleiche |
| Social Features | Scope-Creep, keinen Server fuer Real-time |
| Push-Notifications | Anxiety, kurzfristiger Effekt |
| Premium-Only Features | Keine Monetarisierung geplant |
| FSRS Optimizer UI | Zu technisch, automatisch nach 1'000 Reviews besser |
| Kartenerstellung im Browser | Admin-only Feature, nicht User-facing |

---

## 9. Quellen

### Gamification & Psychologie
- Deci & Ryan (2000): Self-Determination Theory — Autonomy, Competence, Relatedness
- Koivisto & Hamari (2019): Badge complexity correlates with gamification burnout (Springer)
- Duolingo Blog (2024): Streak-System als groesster Wachstumstreiber, 3× Daily Return Rate
- TalentLMS Survey (2024): 83% der Nutzer mit Badges fuehlen sich motivierter
- Growth Engineering: Dark Side of Gamification — Overjustification Effect
- Duolingo (2024): XP-Reduktion "fuer meaningful learning" — Rueckbau des XP-Multipliers

### Lern-Apps als Referenz
- WaniKani: 60-Level Kanji-System (Apprentice → Burned), SRS-Stufen als Gamification
- Anki: Review Heatmap Add-on (600K Downloads), FSRS seit v23.10
- Bunpro: Grammatik-SRS mit JLPT-Alignment
- Memrise: 90% Vocabulary Retention nach 4 Wochen konsistenter Nutzung

### Statistiken & Visualisierung
- Anki Manual: Statistics Page — Review Count, Card Maturity, Ease Factors, Forecast
- Expertium (2025): FSRS Retention-Analyse — True vs. Desired Retention
- Cal-HeatMap: Kalender-Heatmap Library (cal-heatmap.com)
- Chart.js: Leichtgewichtige Charting-Library (chartjs.org)

### Karten-Browser
- Anki Manual: Browsing & Searching — Filter-Syntax, Bulk-Aktionen
- WaniKani Open Framework: Client-seitiges Item-Filtering
- PatternFly: Bulk Selection Design Pattern
- Eleken: 8 Design Guidelines fuer Bulk Actions UX

### Forschung (Primaerquellen)
- Gamification Meta-Analysis: 35 Interventionen, 2'500 Teilnehmer (Springer Nature 2023)
- Counterproductive Effects of Gamification (ScienceDirect 2018)
- Competitive vs. Cooperative Gamification: Kein signifikanter Unterschied (ScienceDirect 2025)
- Notification Frequency: Habituation nach 2 Wochen (PMC/PLOS 2017)
- S-Curve Pattern: Feature Richness vs. Engagement (Springer 2024)
