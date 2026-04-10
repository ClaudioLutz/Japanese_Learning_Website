# Quiz-Validierung: Inline-Warnung statt Browser-Alert

## Problem

Beim Klick auf "Submit Answer" ohne ausgewaehlte Antwort erschien ein nativer Browser-Alert (`alert('Please select an answer')`). Das war:

- Visuell unschoen (Browser-Modal mit URL-Anzeige)
- Nicht auf Deutsch
- Inkonsistent mit dem restlichen UI-Design

![Screenshot: Browser-Alert bei fehlender Antwort](../lesson_view_debug.png)

## Loesung

Alle `alert()`-Aufrufe in der Quiz-Validierung wurden durch eine inline Bootstrap-Warnung im bestehenden Feedback-Bereich ersetzt.

### Neue Funktion: `showQuizWarning(questionId, message)`

- Zeigt eine gelbe Bootstrap-Alert-Box (`alert-warning`) im Feedback-Div der jeweiligen Frage
- Verschwindet automatisch nach 3 Sekunden
- Einheitliches Design mit Icon (`fa-exclamation-triangle`)
- Alle Meldungen auf Deutsch

### Ersetzte Meldungen

| Vorher (alert) | Nachher (inline) |
|---|---|
| `Please select an answer` | `Bitte waehle eine Antwort aus.` |
| `Please provide an answer` | `Bitte gib eine Antwort ein.` |
| `Please match all items.` | `Bitte ordne alle Begriffe zu.` |

### Betroffene Datei

- `app/templates/lesson_view.html` — Funktion `submitQuizAnswer()` (3 Stellen) + neue Funktion `showQuizWarning()`

## Nicht geaendert

Error-Alerts fuer echte Fehler (Netzwerk, CSRF-Token, Server-Fehler) bleiben als `alert()` bestehen, da diese selten auftreten und auf technische Probleme hinweisen.
