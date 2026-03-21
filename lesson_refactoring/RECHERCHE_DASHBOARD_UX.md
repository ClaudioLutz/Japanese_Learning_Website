# Recherche: State-of-the-Art Dashboard & Lektionsdarstellung

**Erstellt:** 20. März 2026
**Zweck:** Grundlage für das Redesign des Benutzer-Dashboards und der Lektionsdarstellung der Japanisch-Lernplattform.

---

## 1. Analyse der führenden Sprachlern-Plattformen

### 1.1 Duolingo — Der Gamification-König

**Was sie richtig machen:**
- **Streak-System**: Tägliche Serien tracken, wie viele Tage in Folge gelernt wurde. Nutzer mit aktivem Streak kehren 3× häufiger täglich zurück.
- **XP-Punkte & Level**: Erfahrungspunkte bei Lektionsabschluss → automatisches Level-Up → Erfolgserlebnis
- **Progress Bars**: Visuelle Indikatoren für Lektionsfortschritt ermutigen zum Weitermachen
- **Herzen/Leben-System**: 5 Herzen pro Session, Fehler kosten ein Herz → natürliche Engagement-Intervalle
- **Leaderboards**: Ligen mit globalem Ranking, Wettbewerb mit Freunden
- **Farbcodierte Level**: Visuell sofort erkennbar wo man steht
- **Minimalistisches, sauberes Design**: Reduziert kognitive Belastung
- **Maskottchen (Duo-Eule)**: Emotionale Bindung, Celebratory Animations

**Duolingo Demon Mode (2025):** Immersive Hochintensitäts-Variante für Gen Z mit dunklem Theme — zeigt Trend zu Personalisierung.

**Relevanz für uns:** Streak, XP, Progress Bars und Level-System sind die wichtigsten Elemente. Leaderboards erst bei grösserer Nutzerbasis sinnvoll.

### 1.2 WaniKani — Japanisch-spezifisch, SRS-fokussiert

**Dashboard-Elemente:**
- Review-Count prominent im Zentrum ("87 Reviews fällig")
- Level-Anzeige mit Fortschrittsbalken zum nächsten Level
- SRS-Stufen-Übersicht (Apprentice → Guru → Master → Enlightened → Burned)
- Optimale Lernreihenfolge: Kanji werden in logischer Sequenz eingeführt
- Mnemonische Geschichten für jedes Zeichen
- Community-Features: AI-Stories die sich an persönliche Interessen anpassen (2025)

**Relevanz für uns:** SRS-Visualisierung und die klare "Reviews fällig"-Anzeige sind exzellent. Passt perfekt zu unserem Kana/Kanji-System.

### 1.3 Bunpro — Grammatik-SRS

**Dashboard-Features:**
- Study Stats und Fortschritt auf einen Blick
- Organisation nach JLPT-Level (N5–N1)
- Multiple Beispielsätze pro Grammatikpunkt
- Cloze-Format (Lückentext) für Wiederholungen
- Vollständige JLPT-Prüfungstests (25 Stück mit Audio + Feedback)
- Spaced Repetition mit dynamischen Intervallen

**Relevanz für uns:** JLPT-Level-Organisation und das Cloze-Format sind direkt übertragbar. Die Kombination aus SRS und Grammatik ist vorbildlich.

### 1.4 Human Japanese — Unser Vorbild für Inhalt

- 85 tiefgehende Kapitel statt hunderte oberflächliche
- Konversationeller Erklärstil ("wie ein geduldiger Lehrer")
- Jeder Beispielsatz nutzt nur bereits eingeführtes Material
- Kulturelle Einschübe natürlich eingewoben

**Relevanz für uns:** Bereits als Vorbild in KONZEPT_PREMIUM_LEKTIONEN.md definiert. Inhaltlich top, aber UI/Dashboard ist veraltet.

---

## 2. Dashboard-Design: Best Practices 2025/26

### 2.1 Informationshierarchie (Wichtigstes zuerst)

**Regel:** Beginne mit einer High-Level-Übersicht, biete dann einfache Wege zur Detailtiefe.

Für ein Lern-Dashboard bedeutet das:

```
┌─────────────────────────────────────────────────────────────┐
│  EBENE 1 — Sofort sichtbar (above the fold)                 │
│  ─────────────────────────────────────────                   │
│  • Personalisierte Begrüssung ("Willkommen zurück, Max!")   │
│  • Streak-Counter (🔥 12 Tage)                              │
│  • Tages-Ziel-Fortschritt (3/5 Übungen heute)               │
│  • Nächste Aktion: "Weiterlernen" Button (CTA)              │
│  • Fällige Reviews (falls SRS aktiv)                        │
├─────────────────────────────────────────────────────────────┤
│  EBENE 2 — Beim Scrollen sichtbar                           │
│  ─────────────────────────────────────────                   │
│  • Lektionspfad (Story-Modus, lineare Progression)          │
│  • Fortschritts-Statistiken (Kana %, Vokabeln, Level)       │
│  • Aktivitäts-Heatmap (GitHub-Style, letzte 12 Wochen)      │
├─────────────────────────────────────────────────────────────┤
│  EBENE 3 — Bei Bedarf erreichbar                            │
│  ─────────────────────────────────────────                   │
│  • Detaillierte Statistiken (Genauigkeit, schwache Punkte)  │
│  • Errungenschaften/Badges                                  │
│  • Kana/Kanji-Übersicht mit Beherrschungsgrad               │
│  • Einstellungen                                            │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Die 5 Must-Have Dashboard-Metriken

| # | Metrik | Warum | Darstellung |
|---|--------|-------|-------------|
| 1 | **Streak** | Stärkstes Retention-Tool (Duolingo-Beweis) | Flammen-Icon + Tageszahl, prominent |
| 2 | **Tages-Fortschritt** | Micro-Goal, täglich erreichbar | Kreisdiagramm oder Fortschrittsbalken |
| 3 | **Gesamt-Level/Kurs-Fortschritt** | Langzeit-Motivation | Fortschrittsbalken mit %-Angabe |
| 4 | **Fällige Reviews** | SRS-Kern, zeitkritisch | Zahl + "Jetzt wiederholen" CTA |
| 5 | **Quiz-Genauigkeit (letzte 7 Tage)** | Selbsteinschätzung, Schwächen erkennen | Trend-Pfeil (↑↓) + Prozentzahl |

### 2.3 Kernprinzipien für Dashboard-Design

**1. User-Centric Design**
- Das Dashboard ist ein personalisierter Lern-Hub, nicht nur ein Menü
- KI-gestützte Personalisierung: dynamische Anpassung der Startseite an Lernverhalten
- "Was soll ich als Nächstes tun?" muss sofort beantwortet werden

**2. Effizienz**
- Dashboard muss dem User Zeit sparen, nicht kosten
- Ein Klick zum Weiterlernen, nicht drei
- Keine unnötigen Zwischenseiten

**3. Konsistenz**
- Einheitliche Navigation, Buttons, Fonts und Farben reduzieren Verwirrung
- Vorhersagbare Erfahrung über alle Seiten

**4. Visuelle Hierarchie**
- Grösse, Farbe und Typografie lenken den Blick auf Schlüsselelemente
- Primäre CTA ("Weiterlernen") immer sichtbar

**5. Clean Design**
- Sauberes, simples Design reduziert kognitive Belastung
- Lerner sollen sich auf Inhalt konzentrieren, nicht auf Navigation

**6. Microinteractions**
- Button Hover-States, Tooltip bei Charts, Lade-Animationen
- Zeigen, dass das System reagiert und lebt

**7. Mobile-First**
- Responsive Design ist Pflicht, nicht optional
- Touch-freundliche Interfaces, Offline-Zugang

---

## 3. Lektionsdarstellung: Moderne Ansätze

### 3.1 Lektionspfad statt Gitteransicht

**Trend 2025/26:** Lineare Story-Pfade statt Kachel-Grids.

```
Alter Ansatz (Grid):                    Neuer Ansatz (Path):
┌────┐ ┌────┐ ┌────┐                   ○ Lektion 1 ✅
│ L1 │ │ L2 │ │ L3 │                   │
└────┘ └────┘ └────┘                   ○ Lektion 2 ✅
┌────┐ ┌────┐ ┌────┐                   │
│ L4 │ │ L5 │ │ L6 │                   ◉ Lektion 3 ← Du bist hier
└────┘ └────┘ └────┘                   │
                                        ○ Lektion 4 🔒
                                        │
                                        ○ Lektion 5 🔒
```

**Vorteile:**
- Klarer Lernweg, keine Entscheidungsparalyse
- Natürliches Gefühl von Fortschritt
- Passt perfekt zu unserer Story-Progression (Yuki-Geschichte)
- Locked/Unlocked-Status sofort erkennbar
- Duolingo nutzt diesen Ansatz seit dem grossen Redesign 2022

### 3.2 Lektionskarten-Design

Jede Lektion im Pfad braucht:

```
┌──────────────────────────────────────┐
│  🖼️ Stimmungsbild (klein, Anime)     │
│  ──────────────────────────────      │
│  Lektion 3: Das Hotel                │
│  "Yuki checkt ein"                   │
│                                      │
│  ◉◉◉◉○  4/5 Seiten abgeschlossen    │
│  🏆 Quiz: 85%                        │
│                                      │
│  Neue Elemente:                      │
│  🔤 10 Hiragana  📖 3 Vokabeln       │
│  📝 1 Grammatik                      │
│                                      │
│  [ Weiterlernen → ]                  │
└──────────────────────────────────────┘
```

### 3.3 Innerhalb einer Lektion: Seitennavigation

**Best Practice:** Horizontaler Fortschrittsbalken oben + Seitennummerierung.

```
┌──────────────────────────────────────────┐
│  ◉──◉──◉──○──○──○   Seite 3 von 6       │
│  Lektion 1: Willkommen in Japan!         │
│──────────────────────────────────────────│
│                                          │
│  [← Zurück]            [Weiter →]        │
│                                          │
│  SEITE-INHALT                            │
│  ...                                     │
│                                          │
│──────────────────────────────────────────│
│  [← Zurück]            [Weiter →]        │
└──────────────────────────────────────────┘
```

**Wichtig:**
- Fortschrittsbalken immer sichtbar (fixed top oder sticky)
- Vorwärts/Rückwärts-Navigation unten UND oben
- Seitenzahlen sichtbar → gibt Orientierung
- Letzte Seite = Quiz → visuell hervorgehoben

---

## 4. Gamification-Elemente: Was wirklich wirkt

### 4.1 Tier-Liste (Aufwand vs. Wirkung)

| Priorität | Element | Aufwand | Retention-Wirkung | Empfehlung |
|-----------|---------|---------|-------------------|------------|
| 🔴 P1 | **Streak** | Niedrig | Sehr hoch (3× Retention) | Sofort implementieren |
| 🔴 P1 | **XP-System** | Niedrig | Hoch | Sofort implementieren |
| 🔴 P1 | **Fortschrittsbalken** | Niedrig | Hoch | Sofort implementieren |
| 🟡 P2 | **Tages-Ziel** | Mittel | Hoch | Phase 2 |
| 🟡 P2 | **Badges/Errungenschaften** | Mittel | Mittel | Phase 2 |
| 🟡 P2 | **Aktivitäts-Heatmap** | Mittel | Mittel | Phase 2 |
| 🟢 P3 | **Leaderboard** | Hoch | Mittel (braucht User) | Später |
| 🟢 P3 | **Ligen** | Hoch | Mittel | Später |
| 🟢 P3 | **Avatar/Charakter** | Mittel | Niedrig | Optional |

### 4.2 Streak-System: Details

```
┌─────────────────────────────────────┐
│  🔥 12 Tage Streak!                 │
│                                     │
│  Mo Di Mi Do Fr Sa So               │
│  ✅ ✅ ✅ ✅ ✅ ✅ ◉                │
│                                     │
│  Lerne heute, um deinen             │
│  Streak zu behalten!                │
│                                     │
│  🏆 Bester Streak: 23 Tage          │
│  ❄️ Streak-Freeze: 1 verfügbar      │
└─────────────────────────────────────┘
```

- **Streak-Freeze:** 1× vergessen erlaubt (kann "verdient" werden)
- **Wochentage-Visualisierung:** Zeigt die aktuelle Woche
- **Milestone-Celebrations:** Bei 7, 30, 100 Tagen besondere Animation
- **Streak-Repair:** Gegen XP-Kosten vergangene Tage "nachholen"

### 4.3 XP-System: Details

| Aktion | XP |
|--------|----|
| Lektion abschliessen (alle Seiten) | 20 XP |
| Quiz bestanden (≥80%) | 10 XP |
| Quiz perfekt (100%) | 15 XP (Bonus) |
| Tägliche Wiederholung (SRS) | 5 XP |
| Streak-Tag beibehalten | 2 XP |
| Fehler korrigiert (2. Versuch bestanden) | 3 XP |

**Level-Thresholds:**
| Level | Benötigte XP | Titel |
|-------|-------------|-------|
| 1 | 0 | Anfänger (初心者) |
| 2 | 100 | Lernender (学習者) |
| 3 | 300 | Entdecker (探検者) |
| 5 | 800 | Fortgeschritten (中級者) |
| 10 | 3'000 | Japanisch-Kenner (日本通) |
| 20 | 10'000 | Meister (達人) |

---

## 5. Aktivitäts-Heatmap (GitHub-Style)

Wie bei GitHub-Contributions: Eine Heatmap der letzten 12 Wochen zeigt, an welchen Tagen gelernt wurde.

```
        Mo  Di  Mi  Do  Fr  Sa  So
Woche 1  ▓▓  ▓▓  ░░  ▓▓  ▓▓  ░░  ░░
Woche 2  ▓▓  ▓▓  ▓▓  ▓▓  ░░  ▓▓  ░░
Woche 3  ██  ██  ▓▓  ▓▓  ▓▓  ▓▓  ▓▓
Woche 4  ▓▓  ▓▓  ▓▓  ░░  ▓▓  ░░  ░░

░░ = nicht gelernt  ▓▓ = gelernt  ██ = intensiv (>20 XP)
```

**Psychologischer Effekt:** Die "Lücken" motivieren zum Füllen. Nutzer vermeiden es, die Heatmap zu unterbrechen.

---

## 6. Spaced Repetition (SRS) Integration

### 6.1 Review-Dashboard-Bereich

```
┌─────────────────────────────────────────┐
│  📖 Wiederholungen                       │
│  ──────────────────                      │
│  Jetzt fällig: 23 Items                 │
│  Heute noch fällig: 45 Items            │
│                                         │
│  ┌───────────────────────────────┐      │
│  │ Kana:     ████████░░  18/22  │      │
│  │ Vokabeln: ██████░░░░  12/20  │      │
│  │ Grammatik: ████░░░░░░  4/10  │      │
│  └───────────────────────────────┘      │
│                                         │
│  [ Wiederholung starten → ]             │
│                                         │
│  SRS-Stufen:                            │
│  🟡 Lehrling: 34  🟢 Kenner: 67         │
│  🔵 Meister: 23   🟣 Erleuchtet: 12     │
│  ⭐ Verbrannt: 5                         │
└─────────────────────────────────────────┘
```

### 6.2 SRS-Stufen (angelehnt an WaniKani)

| Stufe | Name (DE) | Name (JP) | Intervall |
|-------|-----------|-----------|-----------|
| 1 | Lehrling I | 見習い I | 4 Stunden |
| 2 | Lehrling II | 見習い II | 8 Stunden |
| 3 | Lehrling III | 見習い III | 1 Tag |
| 4 | Kenner I | 達人 I | 3 Tage |
| 5 | Kenner II | 達人 II | 1 Woche |
| 6 | Meister | 師匠 | 2 Wochen |
| 7 | Erleuchtet | 悟り | 1 Monat |
| 8 | Verbrannt | 完了 | 4 Monate (dann entfernt) |

---

## 7. Konkrete Empfehlung: Dashboard-Aufbau für unsere Plattform

### 7.1 Logged-Out Landing Page (existiert bereits — beibehalten)
Die aktuelle index.html mit Sprachauswahl (EN/DE) ist gut. Keine Änderung nötig.

### 7.2 Logged-In Dashboard (NEU)

```
┌──────────────────────────────────────────────────────────┐
│  HEADER (fixed)                                          │
│  Logo  |  Dashboard  |  Lektionen  |  Wörterbuch  |  👤  │
│  ─────────────────────────────────────────────────────── │
│                                                          │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  おかえりなさい、Max!            🔥 12 Tage Streak  │ │
│  │  Level 3: 探検者 (Entdecker)     ████░░ 340/500 XP  │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌──────────────────┐  ┌────────────────────────────────┐│
│  │  📖 Reviews       │  │  📊 Heute                      ││
│  │  23 fällig        │  │  Ziel: ████░░ 3/5 Übungen     ││
│  │  [Jetzt starten]  │  │  XP heute: 18                 ││
│  └──────────────────┘  └────────────────────────────────┘│
│                                                          │
│  ── Dein Lernpfad: Yukis Reise ─────────────────────── │
│                                                          │
│  ✅ L1: Willkommen in Japan!           [Wiederholen]     │
│  │                                                       │
│  ◉  L2: Im Taxi              ← Du bist hier             │
│  │   "Yuki nimmt ein Taxi zum Hotel"                     │
│  │   ◉◉○○○○  2/6 Seiten                                 │
│  │   [Weiterlernen →]                                    │
│  │                                                       │
│  🔒 L3: Das Hotel                                        │
│  │   Voraussetzung: L2 abschliessen                      │
│  │                                                       │
│  🔒 L4: Ein Spaziergang                                  │
│  ⋮                                                       │
│                                                          │
│  ── Statistiken ─────────────────────────────────────── │
│                                                          │
│  Aktivität (letzte 12 Wochen):                           │
│  [░░▓▓▓▓░░▓▓██▓▓▓▓░░▓▓▓▓▓▓▓▓██▓▓▓▓░░▓▓▓▓░░▓▓██▓▓...]  │
│                                                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│  │ Kana     │ │ Vokabeln │ │ Kanji    │ │ Grammatik│    │
│  │ 24/46    │ │ 18/∞     │ │ 0/2136   │ │ 2/∞      │    │
│  │ 52%      │ │ N5: 18%  │ │ --       │ │ N5: 8%   │    │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘    │
│                                                          │
│  ── Errungenschaften ────────────────────────────────── │
│  🏅 Erste Lektion  🏅 7-Tage Streak  ○ Kana-Meister     │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 7.3 Lektionsansicht (REDESIGN)

```
┌──────────────────────────────────────────────────────────┐
│  ← Zurück zum Dashboard                                 │
│  ──────────────────────────────────────────────────────  │
│  Lektion 1: Willkommen in Japan!                         │
│  ◉──◉──◉──○──○──○   Seite 3/6                           │
│  ──────────────────────────────────────────────────────  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │                                                    │  │
│  │         [SEITEN-INHALT]                            │  │
│  │                                                    │  │
│  │  Passt sich an Content-Type an:                    │  │
│  │  • text → Prosa mit Formatierung                   │  │
│  │  • kana → Flip-Karten mit Audio                    │  │
│  │  • vocabulary → Karten mit Merkhilfen              │  │
│  │  • dialogue → Chat-Bubbles mit Audio               │  │
│  │  • image → Grosses Stimmungsbild                   │  │
│  │  • audio → Inline-Player                           │  │
│  │  • interactive → Quiz-Widget                       │  │
│  │                                                    │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌──────────┐                        ┌──────────────┐   │
│  │ ← Zurück │                        │ Weiter →     │   │
│  └──────────┘                        └──────────────┘   │
│                                                          │
│  ──────────────────────────────────────────────────────  │
│  💡 Tipp: Klicke auf japanischen Text für Audio          │
└──────────────────────────────────────────────────────────┘
```

---

## 8. Technische Implikationen

### 8.1 Neue Datenbankfelder (User-Model)

```
User — Erweiterungen:
  + xp_total (Integer): Gesamte Erfahrungspunkte
  + xp_today (Integer): XP heute gesammelt (Reset um Mitternacht)
  + current_streak (Integer): Aktuelle Streak-Länge in Tagen
  + longest_streak (Integer): Längster Streak ever
  + last_activity_date (Date): Letztes aktives Lerndatum
  + daily_goal (Integer): Tägliches Übungsziel (Standard: 5)
  + streak_freeze_count (Integer): Verfügbare Streak-Freezes
  + level (Integer): Berechnetes Level
```

### 8.2 Neue Tabellen

```
UserDailyActivity:
  + id (PK)
  + user_id (FK → User)
  + date (Date)
  + xp_earned (Integer)
  + lessons_completed (Integer)
  + reviews_completed (Integer)
  + quiz_accuracy (Float)
  → Für Heatmap und Statistiken

UserBadge:
  + id (PK)
  + user_id (FK → User)
  + badge_type (String): z.B. "first_lesson", "streak_7", "kana_master"
  + earned_date (DateTime)
  → Für Errungenschaften

SRSItem:
  + id (PK)
  + user_id (FK → User)
  + item_type (String): "kana", "vocabulary", "kanji", "grammar"
  + item_id (Integer): FK zu jeweiliger Tabelle
  + srs_stage (Integer): 1-8
  + next_review (DateTime)
  + last_reviewed (DateTime)
  + correct_count (Integer)
  + incorrect_count (Integer)
  → Für Spaced Repetition
```

### 8.3 Neue API-Endpoints

```
GET  /api/dashboard          → Dashboard-Daten (Streak, XP, Reviews, Fortschritt)
POST /api/xp/award           → XP vergeben nach Aktion
GET  /api/reviews/pending     → Fällige SRS-Reviews
POST /api/reviews/submit      → Review-Ergebnis melden
GET  /api/stats/heatmap       → Aktivitäts-Heatmap-Daten (12 Wochen)
GET  /api/stats/progress      → Kana/Vocab/Kanji Fortschritts-Übersicht
GET  /api/badges              → Errungenschaften des Users
```

---

## 9. Implementierungs-Reihenfolge (Empfehlung)

### Phase 1: Dashboard MVP (Wichtigstes zuerst)
1. ✅ Neues Dashboard-Template (logged-in User)
2. ✅ Lektionspfad statt Grid (lineare Progression mit Yuki-Story)
3. ✅ Streak-System (current_streak, last_activity_date)
4. ✅ XP-System (xp_total, Level-Berechnung)
5. ✅ Fortschrittsbalken in Lektionsansicht

### Phase 2: Engagement-Features
6. Tages-Ziel mit Fortschrittsanzeige
7. Aktivitäts-Heatmap
8. Badge-System (5-10 Starter-Badges)
9. Streak-Freeze-Mechanik
10. Verbessertes Lektions-Seitendesign

### Phase 3: SRS & Fortgeschritten
11. SRS-System für Kana und Vokabeln
12. Review-Dashboard-Bereich
13. Detaillierte Statistiken
14. Kana/Kanji-Übersicht mit Beherrschungsgrad

---

## 10. Quellen

- [How to Design Like Duolingo: Gamification & Engagement](https://www.uinkits.com/blog-post/how-to-design-like-duolingo-gamification-engagement)
- [Duolingo UX Breakdown – Addictive Progress Tracking](https://www.uxsnaps.com/learning-dashboard)
- [UX and Gamification in Duolingo (UX Planet)](https://uxplanet.org/ux-and-gamification-in-duolingo-40d55ee09359)
- [Role of UI/UX Design in Gamification — Duolingo's Success Story](https://produxdesign.studio/thought/role-of-ui-ux-design-in-gamification-exploring-duolingos-success-story/)
- [20 Best Dashboard UI/UX Design Principles 2025](https://medium.com/@allclonescript/20-best-dashboard-ui-ux-design-principles-you-need-in-2025-30b661f2f795)
- [Latest Trends and Best Practices in UI/UX Design for E-Learning (Fram Creative)](https://www.framcreative.com/latest-trends-best-practices-and-top-experiences-in-ui-ux-design-for-e-learning)
- [Language Learning Platform UX/UI Design (Cieden Case Study)](https://cieden.com/language-learning-platform)
- [E-Learning Design: Principles, Prototyping and Examples (Justinmind)](https://www.justinmind.com/ui-design/how-to-design-e-learning-platform)
- [UI/UX Design Trends in Mobile Apps for 2025 (Chop Dawg)](https://www.chopdawg.com/ui-ux-design-trends-in-mobile-apps-for-2025/)
- [9 Best Practices for Online Course Design (LearnWorlds)](https://www.learnworlds.com/blog/elearning/best-practices-online-course-design/)
- [SRS: Spaced Repetition System (WaniKani Knowledge)](https://knowledge.wanikani.com/wanikani/srs/)
- [Bunpro Dashboard](https://bunpro.jp/dashboard)
- [The Ultimate Guide to Japanese Learning Apps 2026 (JLPT Samurai)](https://jlptsamurai.com/2025/12/25/the-ultimate-guide-to-the-best-japanese-learning-apps-in-2026-ranked-and-reviewed/)
