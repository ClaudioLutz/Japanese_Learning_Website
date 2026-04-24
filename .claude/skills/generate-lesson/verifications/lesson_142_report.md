# Verification Report — Lesson 142 "Essen im Restaurant"

**Status:** PASS
**Datum:** 2026-04-24
**JLPT:** N5 (difficulty_level=1)

## DB-Struktur (via psql)

| Prüfung | Ergebnis |
|---|---|
| Lesson 142 existiert | ✓ title="Essen im Restaurant", instruction_language=german |
| is_published | false (korrekt — erst nach Mayuko-Sichtung publizieren) |
| 4 Pages | ✓ (3 normal + 1 quiz_carousel) |
| 10 Vocabulary-Items | ✓ (alle N5) |
| 1 Grammar-Item | ✓ (〜をください) |
| 7 Quiz-Fragen | ✓ (4 MC + 2 TF + 1 Matching — 3 Typen gemischt) |
| MC-Fragen korrekt | ✓ jeweils 4 Optionen, genau 1 richtig |

## HTTP-Rendering (authentifiziert als admin)

| Endpoint | HTTP | Inhalt |
|---|---|---|
| `/lessons/142` | 200 | Titel, Vokabeln (メニュー, みず, おいしい), ください, Umlaute (Einführung, Getränk, höflich) alle vorhanden |
| `/api/admin/lessons` | 200 | Lesson "Essen im Restaurant" enthalten |

## Umlaut-Check

Kein ASCII-Fallback: "Einfuehrung", "Hoeflich", "Getraenk", "Koestlich" → 0 Treffer. ✓

## Bekannte Limitierungen dieses Verification-Runs

- **Kein Playwright-Headless-Browser:** MCP-Chrome-Instanz belegt (parallele User-Session). Visuelle Kontrolle inklusive CSS-Deck-Karussell-Check noch offen. Empfehlung: Claudio öffnet `http://localhost:5000/lessons/142` kurz im Browser und klickt durch.
- **is_published=False bis zur manuellen Sichtung** — Standard-Verhalten.

## Nächste Schritte

1. Claudio: Lesson 142 im Browser durchklicken (Quiz-Page 3 testen!)
2. Wenn ok → `is_published=True` setzen und via `/sync-cloud-db` auf Produktion pushen
3. Mayuko kann dann die Lektion nutzen
