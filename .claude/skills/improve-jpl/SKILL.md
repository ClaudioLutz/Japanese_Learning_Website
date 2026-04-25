---
name: improve-jpl
description: Verbessert die Japanese Learning Website (japanese-learning.ch). Auto-aktivieren, wenn Claudio Feature-Ideen zur Seite diskutiert, "was soll ich als nächstes machen" fragt, UI/UX-Reviews wünscht, Bugs auf der Website meldet, Prioritätsfragen stellt oder über den Payrexx-Go-Live spricht. Kennt Vision, Zielgruppe, Alleinstellungsmerkmale, den realen Ist-Zustand des Codes (inkl. technischer Schulden und Zeilenzahlen), harte Blocker für den Live-Gang sowie Entscheidungsheuristiken für Verbesserungen.
---

# improve-jpl — Die Japanese Learning Website besser machen

Dieser Skill ist das Produkt-Gehirn der Seite. CLAUDE.md liefert das Tech-Wissen (Stack, Deployment, DB-Sync); hier steht, *warum* es die Seite gibt, *für wen*, und *was als Nächstes* sinnvoll ist.

## 1. Warum diese Seite existiert (Hierarchie der Zwecke)

1. **Mayuko-Lackmustest** — Primärer Zweck ist, Claudios Frau Mayuko beim Lernen zu unterstützen. Sie ist die wichtigste Nutzerin. Vor jedem Vorschlag: "Würde Mayuko das bemerken, verstehen, wiederkommen?"
2. **Claudio dogfoodet** — Er lernt selbst Japanisch auf der Seite. Eigenes Lernerlebnis ist ein sekundäres Signal für Qualität.
3. **Öffentliches Produkt** — Die Seite soll für deutschsprachige Anfänger eine echte Alternative zu Duolingo/WaniKani/Bunpro werden.

Reihenfolge zählt: Wenn eine Idee (3) dient aber (1) nicht, zurückstellen.

## 2. Das Produktversprechen

**Zielgruppe (Stand heute):** Absolute und frühe Anfänger — Hiragana/Katakana → erste Kanji → Grundvokabular → erste Dialoge. Deutschsprachig ist die Leitspur; Englisch existiert parallel.

**Was anders ist als Duolingo/WaniKani/Bunpro/Anki:**
- KI-generierte Lektionen, Stimmen und Konversationen (OpenAI + Gemini)
- Deck-Karussell-Kartenlernsystem (DB-basiert, gerätübergreifend, eine Karte nach der anderen)
- Gamification: Streak, Level (z.B. "Lv.10 Schüler 学生"), XP, Anzahl fälliger Karten
- Deutschsprachige Anfänger-Zielgruppe als klare Nische

**Nicht-Ziele:**
- Kein `fill_in_the_blank` (siehe CLAUDE.md — `multiple_choice` / `true_false` / `matching` only)
- Keine JLPT-N2/N1-Features, solange die Anfänger-Basis nicht rund ist
- Keine neuen Frameworks/Abstraktionen "auf Vorrat"
- Keine Features, die nur für Claudio Sinn ergeben, aber nicht für Mayuko oder einen fremden Anfänger

## 3. Harte Blocker für den Live-Gang (Reihenfolge)

1. **Container-Uptime fixen (#1, akut)** — Cloud Run läuft mit Default `--min-instances=0`, schläft ein. Payrexx hat am 2026-04-23 die KYC-Freischaltung abgelehnt, weil "der angegebene Website-Link nicht eingesehen werden kann" (E-Mail-Thread `19db8ef12c10a585`, Account lutz86). Fix: `--min-instances=1` in `deploy-to-cloud-run.*` bzw. `cloudbuild.yaml` setzen. Kosten: geschätzt +5–8 CHF/Monat. Ohne diesen Fix → keine echten Zahlungen, keine ersten Kunden. **Per 2026-04-24 in `deploy-to-cloud-run.sh` + `.ps1` committet (commit `5bab7e2`)** — beim nächsten Deploy aktiv. **UptimeRobot-Ping alle 5 Min auf `/health` läuft parallel und reicht NICHT** als Ersatz: er hält nur eine Instance warm (Skalierung erzeugt neue kalte Instanzen), nach jedem Re-Deploy ist die neue Revision kalt, und der eigentliche Kaltstart dauert wegen Region-Mismatch 76 s — siehe Memory `project_cold_start_76_sekunden.md` für Details. Echte Lösung wäre Region-Konsolidierung (Cloud Run nach `europe-west6`, Load Balancer für Domain-Mapping), das ist ein eigenes Vorhaben nach Payrexx-Live.
2. **"Prototype" aus dem Seitentitel raus** — HTML-`<title>` lautet heute `Japanese Website Prototype - Home`. Für Payrexx-Prüfer und erste Besucher ist das das allererste Signal. Unfertig ist ok, "Prototyp" nicht.
3. **Sprach-Konsistenz der Homepage** — Heute gemischt: Hero auf EN ("Begin Your Japanese Journey / Choose your instruction language"), Navigation und Progress-Karten auf DE ("Weiter lernen", "Karten fällig", "Tage Streak"). Entweder durchgängig DE (empfohlen, Zielgruppe) mit Sprach-Toggle oder sauber zweisprachig per i18n. Kein wildes Durcheinander.
4. **Umlaute systemisch prüfen** — "Schueler" statt "Schüler" im Level-Badge. Irgendwo in der Generierungs- oder Template-Kette wird ASCII-fallback statt UTF-8 verwendet. Nicht nur die eine Stelle patchen, Ursache finden.
5. **Favicon** — `/favicon.ico` liefert 404. Trivial, aber sichtbar in der Browser-Konsole.

## 4. Leitplanken für "Bestehendes verbessern" (der Dauermodus)

Claudio will: *alles was besteht verbessern, UI verbessern, Bugs fixen, ersten fremden Nutzer anwerben.* Dafür gelten:

**Grosse Dateien sind Warnsignale, keine Normalität:**
- `app/routes.py` → **4'106 Zeilen**. Gott-Datei. Nichts Neues reinstopfen. Wenn ein Patch hier grösser als ~30 Zeilen wird, ist das der Moment, einen Blueprint oder ein Service-Modul abzuspalten.
- `app/templates/lesson_view.html` → **3'602 Zeilen**. Genau der Ort, wo Mayuko tatsächlich lernt. Änderungen hier brauchen besondere Sorgfalt; grössere Additionen in Partials auslagern, analog zum bereits modularisierten `manage_lessons.html`.
- `app/templates/lessons.html` → 845 Zeilen. Beobachten.
- `app/models.py` → 877 Zeilen. Akzeptabel, aber bei neuen Entities prüfen, ob eigenes Modul-File sinnvoll ist.

**Testabdeckung darf nur steigen:**
- `pyproject.toml` hat `fail_under = 35` — das ist niedrig, aber die Linie. CLAUDE.md-Regel "Coverage nicht senken" gilt. Neue Features brauchen Tests.
- 8 Playwright-Specs in `tests/` gelten als **verwaist** (CLAUDE.md: "benötigen `npm install` und laufenden Test-Server"). Nicht als Sicherheitsnetz betrachten, bis sie in CI laufen.

**CSS-Falle im Deck-Karussell:**
- Regel in [app/static/css/custom.css:1960](app/static/css/custom.css#L1960): `.content-item.in-deck { display: none !important; }` — diese Regel MUSS wirksam bleiben.
- Ein CSS-Syntaxfehler (fehlende `}`, doppelter Selektor) bricht das Parsing ab → alle Karten werden gleichzeitig sichtbar.
- Nach jeder `custom.css`-Änderung: Browser-Konsole auf `[Deck]`-Meldungen prüfen, visuell bestätigen, dass nur eine Karte sichtbar ist.

**DB-Sync-Reihenfolge:**
- IMMER Cloud→Lokal vor Lokal→Cloud. Mayuko/Admin editiert live. Blindes Push überschreibt Produktionsänderungen. Siehe Memory + CLAUDE.md.

## 5. Woran "besser" gemessen wird

Kein A/B-Testing und keine Analytics-Obsession. Die Signale:

- **Mayuko kommt ohne Aufforderung wieder.** Wichtigster Indikator.
- **Erster fremder Nutzer** registriert sich und loggt am Folgetag wieder ein.
- **Payrexx KYC durch** → erste echte CHF-Zahlung möglich.
- **Claudio selbst** merkt echten Lernfortschritt (Retention ≠ Klickspass).
- **Hygiene:** `git status` sauber, Tests grün, Coverage nicht gefallen, Inkognito-Startseite fehlerfrei.

## 6. Entscheidungsheuristik (wie dieser Skill im Dialog hilft)

| Claudio fragt / sagt | Reaktion |
|----------------------|----------|
| "Was soll ich als nächstes machen?" | Blocker aus §3 in Reihenfolge durchgehen, bis Payrexx live ist. |
| "Ich hätte eine Idee: [Feature X]" | Zwei Fragen: (a) Verbessert das Bestehendes, oder baut es Neues? (b) Würde Mayuko es bemerken? Beide "nein" → zurückstellen. |
| "Kannst du die UI reviewen?" | Auf Sprach-Konsistenz, Mobile-Breakpoints, Dark-Mode-Konsistenz, Umlaut-Korrektheit achten. Nicht nur Desktop. |
| "Es gibt einen Bug" | In dieser Reihenfolge ausschliessen: (1) Deck-Karussell-CSS, (2) DB-Sync-Reihenfolge, (3) Cloud-Run-Cold-Start, (4) Umlaut/Charset, (5) routes.py-Monolith. |
| "Sollen wir das refactoren?" | Nur wenn der Ort sowieso gerade berührt wird. Keine Refactor-Marathons. Grosse Dateien aus §4 sind legitime Ziele bei Gelegenheit. |
| "Wie bekomme ich den ersten Nutzer?" | Zuerst §3 abarbeiten. Dann: Titel, Homepage, Onboarding-Pfad bis zur ersten erfolgreichen Lektion durchspielen wie ein Fremder. |

## 7. Verweise (Wissen, das nicht hier dupliziert wird)

- **Tech-Stack, Deployment, DB-Sync, Migrationen** → `CLAUDE.md`
- **Private Daten (Mayuko, Verträge, Finanzen)** → `knowledge-base` Skill
- **Produktions-SQL-Abfragen** → `cloud-db` Skill
- **Cloud↔Lokal-Synchronisation** → `sync-cloud-db` Skill
- **Projekt-Status-Überblick** → `status` Skill
- **Payrexx-Freischaltungs-Thread** → Gmail, Account `lutz86`, Thread-ID `19db8ef12c10a585`
