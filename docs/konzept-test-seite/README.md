# Konzept: Test-/Prüfungsseite („Prüfen")

_Ideen-, Inspirations- und Wireframe-Sammlung · Stand 2026-06-20 · Branch `free-mode-umstellung`_

Eine neue grosse Seite, auf der Nutzer die **Quiz-Fragen aus den Lektionen erneut
testen** können — nicht die SRS-Lernkarten (dafür gibt es `/review`). Headline-Wunsch:
*„auch nur die Fragen, die schon 1× falsch beantwortet wurden"*.

Dies ist **ein Konzept zum Sammeln von Ideen**, keine fertige Spezifikation und keine
Implementierung. Grundlage: code-verifizierter Ist-Zustand + 5 Fachlinsen
(Datenmodell-Machbarkeit, Wettbewerbs-Inspiration, UX-Flows, Test-Didaktik, visuelle
Konsistenz).

## Dokumente

| Datei | Inhalt |
|---|---|
| [`00-konzept-und-modi.md`](00-konzept-und-modi.md) | Vision, **die Datenrealität** (warum „1× falsch" heute baubar ist), Informationsarchitektur, die **zwei Modi** (Übung/Prüfung), vollständiger **Modus-/Filter-Katalog**, N5-Mock-Design, Zugriffskontrolle, didaktische Leitplanken, Roadmap, offene Entscheidungen |
| [`01-wireframes-und-flows.md`](01-wireframes-und-flows.md) | Der Flow Konfig→Session→Ergebnis + **alle ASCII-Wireframes** (Einstieg, Session pro Fragetyp inkl. `matching` mobil, Sofort-Feedback, Ergebnis-Screen mit Score-Ring, Empty-/Gast-/Locked-States, Mobile, Tastatur, Dark-Mode-Hinweise) |
| [`02-inspiration-design-microcopy.md`](02-inspiration-design-microcopy.md) | Wettbewerbs-Inspiration (Anki · Quizlet · Bunpro · WaniKani · Duolingo · Kahoot · JLPT-Mock) + **„Das übernehmen wir"**, Design-System-Token-Mapping (Wiederverwendung aus `/review`, `/practice/kana`), deutscher Microcopy-Katalog |

## Die drei Kern-Erkenntnisse in einem Absatz

1. **„Schon mal falsch" ist heute ohne Schema-Änderung baubar** — über `UserQuizAnswer.is_correct = False OR attempts > 1`. Exakte Fehler-Historie wäre ein optionales Präzisions-Upgrade, keine Voraussetzung.
2. **Das Rückgrat sind history-*un*abhängige Modi** (nach Lektion / Modul / JLPT-Level / Voll-N5-Mock / Zufall). Bei ≈0 externen Nutzern ist der Falsch-Filter für die meisten Konten leer — er ist *ein* Modus mit starkem Empty-State, nicht das Fundament.
3. **Es sind zwei Produkte in einer Seite:** *Übung* (formativ, Sofort-Feedback + Hinweise) und *Prüfung* (summativ, Score am Ende, kein Zurück) — ein Modus-Schalter ganz oben, der den ganzen Screen umstellt.
