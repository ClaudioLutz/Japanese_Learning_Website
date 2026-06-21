# Konzept: Navigation entrümpeln — Übersicht durch Führung, nicht durch Einschränkung

**Stand:** 2026-06-21 · **Status:** Vorschlag (noch nicht umgesetzt) · **Betrifft:** v. a. `app/templates/base.html` (stark geteilte Datei)

## Leitprinzip (harte Vorgabe)

> **Übersicht entsteht durch Organisation und Führung — niemals durch Einschränkung.**
> Jedes Feature bleibt für **jeden** Nutzer jederzeit voll und direkt erreichbar (≤ 2 Taps).
> Kein Progress-Gating, kein Verstecken. Es wird **re-homed, nicht gelöscht**.

Die Reduktion der Überflutung läuft ausschliesslich über drei nicht-einschränkende Mittel:
1. **Eine Eingangstür** statt fünf gleichwertiger Buttons (Hub + ein hervorgehobener Tages-CTA).
2. **Gruppieren** der flachen Liste in wenige Verben (Lernen · Üben · Mein Lernen).
3. **Duplikate entfernen** (reine Aufräumarbeit, null Funktionsverlust).

---

## Diagnose — die Überflutung hat zwei Gesichter

Datengrundlage: vollständiges Inventar von **93 Einstiegspunkten** (Routen + alle Nav-Flächen), code-genau erfasst.

### 1. Die Primär-Navigation zeigt 5 parallele „Lernmodi" als Gleichrangige
Ein eingeloggter Nutzer sieht oben (`base.html`):

| # | Item | Quelle |
|---|------|--------|
| 1 | **Wiederholen** [JP→DE \| DE→JP] (Segmented Control, 2 Ziele + Badges) | base.html:175–192 |
| 2 | **Prüfen** | base.html:194 |
| 3 | **Kana üben** | base.html:199 |
| 4 | **Lektionen** | base.html:205 |
| 5 | *(N5 Komplett — gegatet, Commerce)* | base.html:214 |

→ Es gibt **keine Eingangstür**. Fünf Modi konkurrieren, keiner sagt „fang hier an". Ein neuer Nutzer mit 0 Karten weiss nicht, was der Unterschied zwischen *Wiederholen*, *Prüfen* und *Kana* ist und wo er startet.

### 2. Der „Mein Lernen"-Hub ist begraben, das Dropdown ist eine Rumpelkammer
Der eigentliche Orchestrierungs-Ort — das **„Mein Lernen"-Dashboard mit adaptivem Heute-Plan** (`dashboard_routes.py:26`) — liegt **nur im User-Dropdown** (base.html:261). Und der **Login landet auf der Startseite `/`, nicht auf dem Hub** (`routes.py:589`, OAuth `__init__.py:117`).

Das Dropdown selbst hat **12 Einträge** mit **echten Duplikaten**:
- **Produktion (DE→JP)** steht doppelt (Segmented Control + Dropdown 286).
- **Prüfen** steht doppelt (Primär-Nav + Dropdown 267).
- **Meine Lektionen** (base.html:274) ist im Free-Mode entwertet (Prod-DB: 0 Lektions-Käufe).

---

## Ziel-Navigation (Vorher / Nachher)

### Primär-Nav (Desktop, eingeloggt)

**Vorher (5 Lernmodi flach):**
`Wiederholen[JP→DE|DE→JP]` · `Prüfen` · `Kana üben` · `Lektionen` · *(N5 Komplett)*

**Nachher (3 Verben + Hub als Eingangstür):**

| Item | Inhalt | Icon |
|------|--------|------|
| **Mein Lernen** *(Standard-Landing nach Login)* | Hub: Heute-Plan (1 CTA) + N5-Kompass + Einstieg in alle Modi | fa-compass |
| **Lernen** *(= Lektionen)* | Katalog + Lernpfad (bereits fusioniert) + Filter „Begonnen" | fa-book-open |
| **Üben** | Wiederholen (JP↔DE), Kana, Prüfen — gebündelt | fa-brain |
| *(N5 Komplett)* | unverändert, gegatet | fa-bolt |

### User-Dropdown

**Vorher (12, mit Duplikaten):** Mein Lernen · Prüfen · Profil · Meine Lektionen · Kurse · Statistik · Produktion · Stöbern · Forum · Hinweise · Admin · Abmelden

**Nachher (8, dedupliziert):** Profil · Statistik · Stöbern (Karten verwalten) · Kurse *(gegatet)* · Forum · Hinweise & Korrekturen · Admin *(gegatet)* · Abmelden
*(entfernt: Mein Lernen→Primär-Nav · Prüfen→Üben · Produktion→Üben/Wiederholen · Meine Lektionen→Katalog-Filter)*

### Bottom-Nav (Mobile)
**Vorher:** Home · Lektionen · Wiederholen · Kana · Profil
**Nachher:** Mein Lernen · Lernen · Üben · Profil *(Wiederholen-Fälligkeits-Badge wandert auf „Üben")*

> **Nichts verschwindet** — alles bleibt ≤ 2 Taps erreichbar. Die Nav wird nur ruhiger und bekommt eine klare Hierarchie.

---

## Die Änderungen im Detail (adversarial geprüft)

Jede Zeile wurde gegen „Wo geht die Funktion hin? In wie vielen Taps? Was geht verloren?" getestet.

| # | Änderung | Funktion erhalten | Taps | Risiko | Nötige Zusatzarbeit |
|---|----------|:---:|:---:|:---:|---|
| **A** | **Login → „Mein Lernen"-Hub** statt Startseite; Hub setzt EINEN Tages-CTA | ✅ ja | 1 | niedrig | 2 Redirect-Ziele (`routes.py:589`, `__init__.py:117`) auf `dashboard.index` (Admin weiter auf Admin; `next`-Param hat Vorrang). Test `login_redirect_for_normal_user` anpassen. |
| **B** | **Produktion-Dropdown-Dublette entfernen** (Segmented Control bleibt) | ✅ ja | 2 | niedrig | Nur `base.html:286–288` löschen. Segmented Control MUSS bleiben. |
| **C** | **„Meine Lektionen" → Katalog-Filter** „Begonnen"; Dropdown-Item raus | ✅ ja | 2 | niedrig | Filter-Pill `status==='started'` im Katalog (Daten liegen schon vor, `routes.py:854`). Route `/my-lessons` bleibt (von `payment_success` verlinkt). |
| **D** | **Prüfen in „Üben"-Hub** bündeln (eigene Examens-Identität behalten) | ✅ ja | 2 | mittel | Hub MUSS in Primär- **und** Bottom-Nav. Stärkster Hebel: `/pruefen` von der CHF-130-Seite `jlpt_n5_schweiz.html` und `learn_n5.html` verlinken (heute **nicht** verlinkt!). |
| **E** | **Stöbern** im Dropdown lassen + **zusätzlich** im Hub als „Karten verwalten" verlinken | ✅ ja | 2→1 | niedrig | Additiver Hub-Link (Deck-Verwaltung = Lernverwaltung). Dropdown bleibt. |
| **F** | **Statistik in Hub-Disclosure falten** | ⚠️ **nur mit Zusatzarbeit** | 3 | mittel | Dashboard-Bundle deckt Heatmap/Retention/Reife/Leeches/JLPT/Forecast ab — **fehlt:** Kana-Storm-Stats, Produktion-DE→JP-Stats, Antwortzeiten-Chart + volle Achievement-Galerie. Storm-End-Screen verlinkt 2× direkt auf die Statistik-Seite (`_kana_storm_stage.html:143,426`) → würde tote Links. |

**Empfehlung zu F:** **Statistik-Seite NICHT löschen.** Sie liegt ohnehin nur im Dropdown (trägt nicht zur Primär-Nav-Überflutung bei). Den vollen Merge zurückstellen; stattdessen optional eine Stats-Zusammenfassung im Hub anbieten, die auf die bestehende Seite tieflinkt. So: null Funktionsverlust.

---

## Funktions-Erhaltungs-Tabelle (Rückgrat „ohne Funktionsverlust")

| Heutiger Einstieg | Neues Zuhause | Erreichbar in | Verlust? |
|---|---|:--:|---|
| Wiederholen JP→DE (Primär) | Üben → Wiederholen (Segmented) | 1–2 Taps | nein |
| Produktion DE→JP (Primär + Dropdown ×2) | Üben → Wiederholen (Segmented), Dropdown-Dublette weg | 1–2 Taps | nein (nur Redundanz weg) |
| Prüfen (Primär + Dropdown ×2) | Üben → Prüfen (+ Links von CHF-130-Seite) | 1–2 Taps | nein (Sichtbarkeit via Cross-Links sogar besser) |
| Kana üben (Primär) | Üben → Kana | 1–2 Taps | nein |
| Lektionen (Primär) | Lernen (Primär) | 1 Tap | nein |
| Mein Lernen (Dropdown) | **Primär-Nav + Standard-Landing** | 0–1 Tap | nein (besser auffindbar) |
| Statistik (Dropdown) | Dropdown (bleibt) + optional Hub-Disclosure | 2 Taps | nein, wenn Seite bleibt |
| Stöbern / Deck-Verwaltung (Dropdown) | Dropdown + Hub-Link | 1–2 Taps | nein |
| Meine Lektionen (Dropdown) | Katalog-Filter „Begonnen" | 2 Taps | nur entwertetes Commerce-Aggregat (Free-Mode) |
| Forum / Hinweise / Kurse / Admin | Dropdown (unverändert) | 2 Taps | nein |

---

## Empfohlener phasenweiser Rollout

- **Phase 0 — Aufräumen (geringes Risiko, ~80 % der Wirkung):** B + C + Prüfen-Dedupe. Reine Duplikat-Entfernung, keine neuen Seiten.
- **Phase 1 — Eingangstür:** A (Login → Hub, ein Tages-CTA, Hub in Primär-Nav). Grösster Einzel-Hebel gegen „überflutet".
- **Phase 2 — „Üben"-Dach:** D + E (Bündelung + Cross-Links zur Examens-Seite). Bottom-Nav anpassen.
- **Phase 3 — optional:** F sauber (Storm/Produktion/Antwortzeiten ins Bundle ziehen) ODER Statistik-Seite einfach belassen.

Jede Phase ist eigenständig deploybar und reversibel. QA-Gate pro Phase: pytest + ruff + Playwright (mobil/desktop, light/dark, Deck-Karussell-Invariante).
