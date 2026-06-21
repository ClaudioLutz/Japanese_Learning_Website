# Konzept: Umkehrbare Vokabel-Lernkarten (Rezeption JP→DE + Produktion DE→JP)

*Stand: 2026-06-21 · Status: FINAL (abgabefertig) · Autor: Produkt-/Lern-Architektur · Review: 3 Linsen (Pädagogik, Engineering/Migration, UX/Leak/Frontend) eingearbeitet*

> **REVISION 2026-06-21:** Alle 8 offenen Fragen sind entschieden und die Datenfragen empirisch gegen die DB geklärt. **Architektur-Pivot:** Produktion läuft über eine **eigene, immer verfügbare Seite `/review/produktion`** (eigene Queue) statt eines Opt-in-Toggles in `/review`. Der Abschnitt **„Entscheidungen — festgelegt 2026-06-21"** (am Ende) ist maßgeblich und hat Vorrang vor dem ursprünglichen Opt-in-Entwurf in 6.5 / 7.1 / 9.4 (die als Begründung/Alternative stehen bleiben).

---

## TL;DR / Empfehlung in 5 Sätzen

1. Wir führen **Produktion (DE→JP)** als **eigenständige FSRS-Spur pro Vokabel** ein (Option A: neue `direction`-Spalte auf `CardReviewState`/`ReviewLog`, Unique von `(user,content)` auf `(user,content,direction)` umgestellt) — nicht als umgedrehte Anzeige, weil FSRS genau eine Gedächtnisspur pro Karte modelliert und Rezeption schneller reift als Produktion.
2. **Primärer Disambiguierer ist der autorierte `production_cue_de`** (Wortart-/Register-/Sinn-Tag), **nicht** der deutsche Lückensatz — denn das deutsche Lemma steht nur in ~70 % der N5-Sätze verbatim und löst die Kern-Härtefälle (私/僕/俺, 行く, 大きい/大きな) gerade *nicht*; der Lückensatz ist nur opportunistischer Zusatz auf einer verifizierten Whitelist.
3. **Leak-Vermeidung ist Frontend-Sache** im `reverse`-Render-Zweig von `review.html`: unterdrückt werden Front die **reading+romaji-Zeile** (der schärfste Leak), der **JP-Beispielsatz** und das **Bild-`alt` wird leer** (ARIA-Leak); der Audio-Button liegt bereits back-only — kein zu lösendes Problem. Das Bild bleibt als sprachneutraler Cue vorne (neu platziert, vergrößert, dekoratives `alt`).
4. **MVP (Phase 1)** = echtes SRS pro Richtung auf einer **eigenen, immer verfügbaren Seite `/review/produktion`** (eigene Queue, **kein** Opt-in-Flag); eine Vokabel erscheint dort automatisch, sobald ihre JP→DE-Karte **Stage ≥ 3** erreicht (Recognition-first). Inklusive kuratierter `production_cue_de` für die **~19 % echten Härtefälle** (Homonyme/Register) + Wortart-Tag für den Rest. *(Revision 2026-06-21 — ersetzt den ursprünglichen per-Lektion-Opt-in.)*
5. Drei Engineering-Blocker sind gelöst: `downgrade()` löscht zuerst die `reverse`-Zeilen (dokumentierter Trade-off: Daten*verlust* beim Downgrade), der INSERT-Pfad in `rate_card` setzt `direction` **explizit** (sonst Unique-Crash bei der ersten Reverse-Bewertung), und die komplette Route-Schicht (`srs_routes.py`) + die dritte Rate-Oberfläche (`kana_grid_game.js`) führen `direction` **default-`forward`** end-to-end.

---

## 1. Ziel & Motivation

Heute prüfen die Vokabel-Karten ausschließlich **Rezeption**: Vorderseite = japanisches Wort (`word`), Rückseite = deutsche Bedeutung + Lesung. Der Lerner trainiert *Wiedererkennen* — er sieht 水 und ruft „Wasser" ab.

Was fehlt, ist **Produktion** (DE→JP): Vorderseite = deutscher Cue, Aufgabe = das japanische Wort + Lesung aktiv erzeugen (みず / 水). Rezeption und Produktion sind nach Nation (2001) **getrennte Wissensdimensionen** — wer ein Wort erkennt, kann es noch lange nicht produzieren. Der produktive Abruf ist die deutlich schwerere Gedächtnisleistung und genau die, die man zum *Sprechen und Schreiben* braucht.

**Warum für dieses Projekt relevant:** Hauptnutzer und Ziel ist Claudio, der selbst N5-Japanisch lernt — es zählt **echte Langzeit-Retention**, nicht Engagement-Metriken. Produktion schließt die Lücke zwischen „ich verstehe es im Text" und „ich kann es selbst sagen". Da die Plattform ein strukturierter, deutschsprachiger N5-Kurs ist (kein reines Immersions-Setup), ist bidirektionales Lernen hier legitim — anders als bei der AJATT/Refold-Schule, die Produktionskarten für reine Immersionslerner ablehnt (Abschnitt 4).

**Ehrliche Reichweiten-Grenze (TAP, vgl. 4.1):** Was wir im MVP liefern, ist **Einzelwort-Produktion** (Lesung erzeugen) — die *unterste* Sprosse produktiver Kompetenz. Nach derselben Transfer-Appropriate-Processing-Logik, die das Konzept anführt, überträgt Einzelwort-Abruf nur begrenzt auf das eigentliche Ziel (Sprechen/Schreiben in Sätzen). Wir erheben hier **nicht** den vollen „sprechen können"-Anspruch; satz-/phrasenproduktive Karten (deutscher Cue → japanischer Mini-Satz) sind die TAP-konsequentere Ausbaustufe für später (Phase 3, offene Frage).

**Scharf gesagt:** Wir ergänzen eine zweite, eigenständige Gedächtnisspur pro Vokabel — nicht eine umgedrehte Anzeige derselben Karte.

---

## 2. Ist-Zustand (Code)

### 2.1 DREI Rating-Oberflächen, ein Daten-Backend

Alle posten an **`POST /api/srs/rate`** (`srs_routes.py:30`, `api_rate_card`) mit `{content_id, rating, time_taken_ms}` und speisen **dasselbe** `CardReviewState`:

| Oberfläche | Datei / Einstieg | Rolle |
|---|---|---|
| **(1) `/review`-Queue** | `review.html`, JS `showCard()`; Queue aus `/api/srs/due` (`api_due_cards`, `srs_routes.py:86` → `get_due_cards`) | Tägliche FSRS-Wiederholung. Flip-Card. 4 Buttons Again/Hard/Good/Easy. Interval-Preview via `/api/srs/preview` (`api_interval_preview`, `srs_routes.py:121`). |
| **(2) Deck-Karussell** | `lesson_view.html`, Jinja-Flip-Cards, `rateCard()` (~Z. 4121) → `fetch /api/srs/rate` (Caller Z. 4136) | **Erst-Begegnung / Lernphase** in der Lektion. Eine Karte sichtbar (`.content-item.in-deck { display:none }`). Ratet **echt** ins SRS. |
| **(3) Kana-Grid-Spiel** | `kana_grid_game.js`, `rateCell()` (~Z. 716) → `/api/srs/rate` mit `grid_context` | Kana-Üben. **Immer forward**, nie reverse — kana hat keine Produktionsrichtung. |

→ **Konsequenz:** `direction` MUSS end-to-end **default-`forward`** sein, sonst brechen Caller (2) und (3). Reverse ist **ausschließlich** für `vocabulary` erlaubt.

### 2.2 SRS-Kern (`app/srs_service.py`, `app/models.py`)

- **`CardReviewState`** (`models.py:1520`): `UNIQUE(user_id, content_id)` → Constraint **`uq_user_content_review`** (`models.py:1548`), plus Index `ix_card_review_due (user_id, due_date, status)`. Spalten: `fsrs_card_state` (TEXT = `Card.to_json()`), `due_date`, `status`, `reps`, `lapses`. **Keine Richtungs-Spalte.**
- **`ReviewLog`** (`models.py:1556`): `rating`, `reviewed_at`, `time_taken_ms`, `fsrs_review_log`, `scheduled_days`, `elapsed_days`, `stage_at_review`. **Keine Richtungs-Spalte.**
- **`rate_card(user_id, content_id, rating_int, time_taken_ms)`** (`srs_service.py:73`): Lookup `filter_by(user_id, content_id)` (Z. 89–91). **INSERT-Pfad (Z. 99–108) konstruiert `CardReviewState(...)` OHNE `direction`.** Existiert kein State, wird ein frischer `Card()` angelegt (Z. 97). Berechnet FSRS-State, XP (`calculate_xp`), Gamification (Stage 0..9, `total_mastered`, `DailyReviewAggregate`), Streak.
- **`migrate_existing_progress`** (`srs_service.py:500`): exakt dasselbe `filter_by(user, content).first()`-Muster — bei der Migration ebenfalls `direction='forward'` mitgeben.
- **Per-`content_id`-gekeyte Touchpoints:** `get_due_cards` (214), `get_due_count` (234), `get_new_cards` (244), `get_user_stats` (301), `get_content_data_for_review` (390), `get_review_forecast` (608), `get_maturity_distribution` (631), `get_leeches` (675), `get_jlpt_progress` (739), `browse_cards` (806), sowie die `.first()`-Einzel-Lookups `get_interval_preview` (259), `get_card_detail` (967), `suspend_card` (1021), `unsuspend_card` (1031), `reset_card` (1042).
- **Mastery-Diskrepanz im Bestand:** `rate_card` zählt `total_mastered` bei **Stage ≥ 9** (Z. 164), `get_jlpt_progress` zählt „mastered" bei **Stage ≥ 5** (Z. 739ff). Bei Richtungs-Einführung explizit zu klären (Abschnitt 9.2).

### 2.3 Weitere Konsumenten von `CardReviewState.content_id` (oft übersehen)

- **`dashboard_service.py`** (gespeist von `/api/dashboard/*`): `_pillar`-Aggregation (Z. 84–90), `_accuracy_by_content`, Accuracy-by-Stage — gruppiert/zählt über `content_id`.
- **`gamification_service.py::compute_kana_mastery_context`**: zählt Karten per `content_id` für Achievement-Schwellen.

→ Sobald Reverse-Karten existieren, **doppelzählen** beide Flächen Vokabeln (Mastery-Pillars, Achievement-Schwellen). Dieselbe Doppelzähl-Gefahr wie bei `get_jlpt_progress`, aber im Original-Entwurf nicht erfasst (Abschnitt 9.2/6.4).

### 2.4 Der Payload hat schon alles

`get_content_data_for_review` (Z. 427–442) liefert für `vocabulary`:

```
front = word (JP)            # nur per KONVENTION das JP-Wort
details = { reading, romaji, meaning(en), meaning_de(de),
            example_jp, example_en, example_romaji, example_translation,
            image_url }
```

**Alle Felder für beide Richtungen sind bereits im Payload** — ein *flacher* Payload. Was fehlt, ist die *Richtungs-Diskriminierung* in Planung, Persistenz und **Darstellung**. Wichtig (Leak, Abschnitt 7.4): Weil der reverse-*Reveal* (Rückseite) `example_jp` + Audio braucht, kann man die Leak-Felder **nicht aus dem Payload strippen** — die Maskierung muss im Frontend-Render-Zweig liegen.

### 2.5 Vorwärts-orientierte Anzeige-Maschinerie

- `Lesson.show_romaji_on_front` (Default `true`) + CSS `html.hide-front-romaji` blenden `.front-romaji` aus (`review.html:38–39`, `lesson_view.html:105`). **Vorwärts gedacht** und greift bei DE→JP falsch herum.
- Konkrete Front-Bausteine in `review.html`: `subText` (Z. 1551, Klasse `front-romaji`, gebaut 1383–1384) = **reading + romaji**; `frontExample` (Z. 1407–1412, eingesetzt 1552) = JP-Beispielsatz + Romaji; Bild aktuell **rückseitig** (`back-image`, Z. 1414–1421, 64×64) mit `alt="${frontText}"` (= JP-Wort).
- **Vorhandener Cloze-Scaffold** (für *Grammatik*): `grammarClozeFront` (Z. 1528–1543) mit `cloze-prompt`, `cloze-gap`-Span, `romaji_masked`, progressivem `cloze-hint-btn`; Handler 1576–1584; gespeist von `models.py::cloze()`/`make_grammar_cloze()` (Z. 768–772). **Die UI-Schicht ist wiederverwendbar** (siehe 5.4).

---

## 3. Die Kernentscheidung: echtes SRS pro Richtung, kein Anzeige-Toggle

### 3.1 Diskriminierende Frage

> Soll DE→JP eine **eigene, separat geplante FSRS-Karte** sein, oder nur eine umgedrehte Darstellung derselben Karte?

Claudios Ziel (selbst lernen, echte Retention) **erzwingt** die erste Antwort. FSRS modelliert **genau eine Gedächtnisspur pro Karte** (DSR: Difficulty, Stability, Retrievability). Rezeption JP→DE und Produktion DE→JP sind verschiedene Spuren mit verschiedener Stabilität. Presst man beide in **eine** `due_date`, muss FSRS **mindestens eine Richtung systematisch fehlplanen**. Das ist auch Ankis Standard: Vorwärts- und Reverse-Karte sind „Siblings" mit je eigener Review-Historie und eigenem Scheduler-State; WaniKani→KameSame führt Produktion als **separate SRS-Spur**.

### 3.2 Die drei Optionen

| | **A — Getrennte Karten + `direction`** (EMPFEHLUNG) | **B — Reiner Display-Flip** | **C — Session-Modus, geteilte Planung** |
|---|---|---|---|
| **FSRS-Korrektheit** | ✅ Eine Spur pro Richtung | ❌ Eine Spur für zwei Skills → Fehlplanung | ❌ Wie B: ein DSR-State kollabiert beide |
| **Pädagogik** | ✅ Rezeption/Produktion getrennt reifbar | ❌ Produktion „erbt" Rezeptions-Reife → Illusion of Competence | ⚠️ Richtung wählbar, Reife nicht getrennt messbar |
| **Mastery-/Stats-Aussage** | ✅ „rezeptiv" ≠ „produktiv" sauber | ❌ Nicht trennbar | ❌ Nicht trennbar |
| **Migrations-Aufwand** | ⚠️ Hoch: `direction`-Spalte, Unique-Umstellung, ~20 Touchpoints | ✅ Minimal (nur UI) | ⚠️ Mittel (Modus-Routing, kein Schema) |
| **Review-Last** | ⚠️ Verdoppelt sich pro Vokabel → Opt-in erzwungen (6.5) | ✅ Keine Zunahme | ✅ Keine Zunahme |
| **Endzustand-tauglich** | ✅ Ja | ❌ Nur Interim | ❌ Nur Interim |

### 3.3 Empfehlung

**Option A.** Pädagogisch *erzwungen* (FSRS-Spur-Argument, bestätigt durch Anki-„Siblings" und WaniKani/KameSame).

**B und C sind ausdrücklich nur Interim** — z.B. ein „DE→JP anschauen"-Vorschau-Toggle ohne eigene Planung, um die UI zu validieren, bevor die Migration gezogen wird. Sie sind **kein Endzustand**, weil sie die FSRS-Spur-Annahme verletzen. Der Phasenplan nutzt B als reversibles MVP-Vorspiel (Phase 0) und zieht A als Zielzustand (Phase 1).

---

## 4. Pädagogik

### 4.1 Rezeption vs. Produktion sind getrennte Skills

- **Nation / Webb:** Rezeptiver und produktiver Wortschatz sind verschiedene Wissensgrade; Rezeption liefert Produktion **nicht** gratis. Die Annahme „wer erkennt, kann produzieren" ist empirisch widerlegt.
- **Transfer-Appropriate Processing (TAP):** Man wird gut in dem, was man *übt*. Wer nur JP→DE übt, wird gut im Erkennen — nicht im Produzieren. **Grenze (siehe 1):** Einzelwort-Produktion ist die *unterste* TAP-Stufe; sie überträgt nur begrenzt auf Satz-/Sprechkompetenz. Bewusste Limitation, nicht verkaufter Vollanspruch.
- **Generation-Effekt / Retrieval Practice:** Aktiver Abruf vor dem Aufdecken festigt stärker als passives Wiedererkennen (Bjork, „desirable difficulties").

### 4.2 Reihenfolge: Recognition-first, Production-later, OPT-IN

Konsens (Anki, WaniKani→KameSame, kognitive Psychologie): **erst Rezeption stabilisieren, dann Produktion** — nie beide Richtungen derselben Vokabel gleichzeitig neu einführen. Gründe: zwei schwere neue Spuren gleichzeitig erzeugen *Raten statt Abruf*; bei gleichzeitigem Start clustern beide Siblings auf benachbarte Tage (Parallel-Drift), der Trenneffekt geht verloren.

→ **Reverse-Karten sind opt-in und werden frühestens freigeschaltet, wenn die Vorwärtskarte eine Mindest-Reife erreicht hat** (Mechanik: 6.5).

### 4.3 Interleaving & Sibling-Burying

Interleaving ist eine belegte „desirable difficulty". **Aber** Vorwärts- und Rückwärtskarte **derselben Vokabel** dürfen **nicht in derselben Session** erscheinen — die zuerst beantwortete verrät die zweite. Anki löst das mit **Sibling-Burying** (Geschwisterkarte für denselben Tag vergraben). **Dieses Muster übernehmen wir** (6.4, „same-day sibling suppression").

---

## 5. Das Homonym-/Mehrdeutigkeits-Problem (Kernrisiko, wasserdicht)

Dies ist **das** Risiko reversierter Karten. Bei JP→DE ist der Cue (das JP-Wort) eindeutig. Bei DE→JP ist der deutsche Cue **oft mehrdeutig** — der Lerner produziert evtl. ein *korrektes* JP-Wort, das nicht das *Zielwort* ist. Ohne wasserdichte Lösung fällt das Feature beim ersten echten DE→JP-Review auseinander (unfaire „Again", verseuchter FSRS-Input, Leeches).

### 5.1 Konkrete Fallen im N5-Bestand

| Deutscher Cue | Mögliche Zielwörter | Problem | Löst Lückensatz das? |
|---|---|---|---|
| „heiß" | 熱い (Objekt) / 暑い (Wetter) | Kontext-Homonym, beide あつい | **Teilweise** („Die Suppe ist ___") |
| „ich" | 私 / 僕 / 俺 | Register | **Nein** — „Ich bin Student" lässt alle drei offen |
| „gehen" | 行く / … | Sinn/Synonym | **Nein** |
| „groß" | 大きい (i-Adj.) / 大きな (attributiv) | Wortart-Variante | **Nein** |

### 5.2 Daten-Befund: Lückensatz ist NICHT der Primär-Disambiguierer (korrigiert)

Code+DB-verifiziert: Im N5-Bestand (799 Vok.) erscheint das deutsche Lemma nur bei **558 (~70 %, großzügig per Substring gezählt** — inkl. Falsch-Treffern wie „ich" in „nicht/sich") überhaupt verbatim im Satz; sauber maskierbar (nach Flexion) sind es real **deutlich weniger**. Beispiele aus der Prod-DB: 置く→„stelle…auf" (Lemma nicht da), 弾く→„spiele" (konjugiert), ぎんこういん→„Bankangestellte" (flektiert), 花→„Blumen". **Schlimmer:** Der Lückensatz löst die selbst genannten Kern-Härtefälle (私/僕/俺, 行く, 大きい/大きな) **gerade nicht** — also genau die Fälle nicht, für die er eingeführt wurde.

→ **Rollen-Tausch (Entscheidung):** Der **autorierte `production_cue_de`** (Wortart-/Register-/Sinn-Tag bzw. Mini-Kontext) ist der **PRIMÄRE** Disambiguierer für alle mehrdeutigen Karten. Der deutsche Lückensatz ist nur ein **opportunistischer Zusatz** dort, wo das Lemma **nachweislich sauber maskiert** — auf einer **verifizierten Whitelist** (nicht Auto-Maskierung zur Anzeigezeit). Konsequenz: `production_cue_de`-Kuratierung für die Homonym-/Register-Härtefälle gehört in **Phase 1 (MVP)**, nicht Phase 2 — sonst startet das Feature ohne funktionierende Disambiguierung für seine schwersten Karten.

### 5.3 Lösungsbaukasten (für Self-Assess-Flip)

1. **`production_cue_de` — PRIMÄR.** Kleines Pill am Cue: „Verb", „i-Adjektiv", „neutral-höflich", „Suppe/Objekt" — disambiguiert ohne die Antwort zu zeigen. **Autorierter Content** (5.5).
2. **Deutscher Lückensatz — SEKUNDÄR/opportunistisch.** Nur auf Whitelist, wo das Zielwort im deutschen `example_translation` sauber maskierbar ist: „Die Suppe ist ___." → erzwingt 熱い.
3. **Bild als sprachneutraler Produktions-Cue.** `image_url` disambiguiert stark (dampfende Suppe → 熱い) und ist ein echter Produktions-Trigger. **Bild bleibt vorne** (7.4).
4. **Synonym-Akzeptanz-Policy (sichtbar an der Karte, nicht nur im Doc).** „Kana gewusst, Kanji noch nicht" oder ein akzeptiertes Synonym = bewusster Teilerfolg. Bestehensregel als kurze, sichtbare Konvention auf der Karte (8.3).
5. **„Welches Wort war gemeint"-Reveal.** Nach dem Flip steht das Zielwort prominent (Kanji + Lesung) plus **akzeptierte Alternativen** — so lernt der Lerner auch dann, wenn er ein gültiges, aber falsches Wort produziert hat.

### 5.4 Wiederverwendung des bestehenden Cloze-Scaffolds (Frontend)

Den **Front-mit-Lücke-/maskierte-Romaji-/progressive-Hinweise**-Mechanismus **nicht neu bauen**: Die UI-Schicht `cloze-prompt`/`cloze-gap`/`cloze-romaji`/`cloze-hint-btn` (`review.html:1528–1543`) ist wiederverwendbar. **Aber klar abgegrenzt:** `make_grammar_cloze` (`models.py:768`) maskiert JP-Partikel/Form und gibt `None` zurück, wenn kein Marker passt — für vocab DE→JP braucht es eine **andere Maskierungsquelle**: das deutsche `example_translation`, in dem das **Zielwort** geblankt wird. Das ist der eigentliche neue Teil; Risiko #4 (13) bezieht sich nur auf diese Maskierung, nicht auf die UI.

### 5.5 Wo der Disambiguierungs-Cue physisch lebt (Daten-Entscheidung)

- **Neue, nullable Spalte `production_cue_de` auf `Vocabulary`.** **Autorierter Content** im bestehenden Human-in-Loop-Muster: Claude verfasst die Cues, ein Skript schreibt nur das fertige, geprüfte Ergebnis in die DB — **keine Laufzeit-LLM-Calls** (analog `scripts/regenerate_vocab_examples.py` + `scripts/data/vocab_example_sentences.json`). Konkret: neues `scripts/data/vocab_production_cues.json` + Applier `scripts/apply_production_cues.py` (DRY-RUN/`--apply`/Backup, Muster „DB-Content Apply").
- **Lückensatz-Whitelist:** ebenfalls kuratiert/verifiziert (nicht Auto-Maskierung zur Anzeigezeit), entweder als Feld im selben JSON oder als separate Whitelist-Tabelle der maskierbaren `content_id`s.
- **Fallback-Kette:** `production_cue_de` → (whitelisted) Lückensatz → nackte `meaning_de`. Wo **alle** fehlen UND die Karte mehrdeutig ist, wird die Reverse-Richtung **gegated**, bis ein Cue gepflegt ist (verhindert unfaire Ratings).

---

## 6. Datenmodell & Migration

### 6.1 Schema-Änderung

```python
# CardReviewState  (models.py:1520)
direction = db.Column(db.String(8), nullable=False, server_default='forward')
#   'forward' (JP→DE, Rezeption) | 'reverse' (DE→JP, Produktion)
# Unique ersetzen:
#   weg:  ('user_id','content_id', name='uq_user_content_review')
#   neu:  ('user_id','content_id','direction', name='uq_user_content_direction')
# Index ix_card_review_due bleibt; optional um direction ergänzen.

# ReviewLog  (models.py:1556)
direction = db.Column(db.String(8), nullable=False, server_default='forward')
direction_idx = db.Index('ix_reviewlog_direction', 'user_id', 'direction')  # für richtungsgetrennte Optimizer-Queries

# Vocabulary  (models.py)
production_cue_de = db.Column(db.Text, nullable=True)   # autorierter Disambig.-Cue (PRIMÄR)
```

### 6.2 Daten-Abhängigkeit `meaning_de` — Coverage VOR Rollout geprüft

DE→JP-Front braucht gepflegtes `meaning_de` (`meaning` ist oft englisches Altdatum).

| Gruppe | Total | ohne `meaning_de` | Coverage |
|---|---|---|---|
| **N5 (level 5)** | 799 | **0** | **100 %** |
| N4 (level 4) | 9 | 6 | 33 % |
| Gesamt | 808 | 6 | 99,3 % |
| *kana-only (`word==reading`)* | 304 | — | — |
| *mit JP-Beispielsatz* | 808 | — | 100 % |

> ⚠️ **Verifikations-Pflicht:** Diese Zahlen sind load-bearing. Coverage-Query **real gegen die Prod-DB** (`/cloud-db`) **erneut vor Phase 1** laufen lassen und im Doc als „verifiziert am `<Datum>`" markieren — der UX-Review konnte sie nicht selbst gegenprüfen. Das `meaning_de`-Gate bleibt unabhängig davon Pflicht-Fallback.

```sql
SELECT COUNT(*) FILTER (WHERE meaning_de IS NULL OR btrim(meaning_de)='') AS ohne_de
FROM vocabulary WHERE jlpt_level = 5;   -- erwartet: 0
```

→ Für N5 ist die Datenabhängigkeit faktisch gelöst. **Gate als Sicherheitsnetz:** Reverse-Karte nur, wenn `meaning_de` nicht leer; sonst Fallback auf `meaning` mit Warn-Log bzw. Skip.

### 6.3 Backfill & Migration (Alembic) — Reversibilität ehrlich

```python
def upgrade():
    op.add_column('card_review_state',
        sa.Column('direction', sa.String(8), nullable=False, server_default='forward'))
    op.add_column('review_log',
        sa.Column('direction', sa.String(8), nullable=False, server_default='forward'))
    op.add_column('vocabulary', sa.Column('production_cue_de', sa.Text(), nullable=True))
    # Altzeilen sind durch server_default bereits 'forward' — kein UPDATE nötig.
    op.drop_constraint('uq_user_content_review', 'card_review_state', type_='unique')
    op.create_unique_constraint('uq_user_content_direction', 'card_review_state',
        ['user_id','content_id','direction'])

def downgrade():
    # BLOCKER-FIX: Reverse-Zeilen MÜSSEN vor dem Recreate der 2-Spalten-Unique weg,
    # sonst Duplicate-Key-Violation (forward+reverse je content_id).
    op.execute("DELETE FROM review_log         WHERE direction = 'reverse'")
    op.execute("DELETE FROM card_review_state  WHERE direction = 'reverse'")
    op.drop_constraint('uq_user_content_direction', 'card_review_state', type_='unique')
    op.create_unique_constraint('uq_user_content_review', 'card_review_state',
        ['user_id','content_id'])
    op.drop_column('vocabulary','production_cue_de')
    op.drop_column('review_log','direction')
    op.drop_column('card_review_state','direction')
```

**Reversibilität — ehrlicher Trade-off (BLOCKER gelöst):** `upgrade` ist additiv und ohne Datenverlust (Altzeilen → `forward`). `downgrade` ist möglich, aber **löscht alle `reverse`-Karten und -Logs** — andernfalls scheitert das Wiederherstellen der 2-Spalten-Unique an Duplicate-Keys. Das ist ein **bewusster, dokumentierter Daten*verlust* des Downgrades**, NICHT „kein Datenverlust". Praktisch unkritisch (Reverse ist additives Opt-in-Feature), aber explizit zu nennen.

⚠️ Test-Suite nutzt `create_all` — Migration **vor Deploy real gegen die Prod-DB** prüfen (bekannte Falle aus dem Forum-Rollout).

### 6.4 Vollständiges Touchpoint-Inventar (`direction` durchziehen)

**Service-Schicht `srs_service.py`:**

| Funktion | Änderung |
|---|---|
| `rate_card` (73) | Signatur `+ direction='forward'`; Lookup `filter_by(... direction=)`; **INSERT-Block Z. 99–108 `direction=direction` EXPLIZIT** (BLOCKER); `Card()`-Pfad pro Richtung; `ReviewLog(direction=)`. |
| `migrate_existing_progress` (500) | `direction='forward'` mitgeben. |
| `get_due_cards` (214) | Filter `direction`; Modus-Param; **Same-day-Sibling-Suppression** (nur die fälligere Richtung pro `content_id` in eine Session). |
| `get_due_count` (234) | pro Richtung — Nav-Badge-Inflation (9.4). |
| `get_new_cards` (244) | **direction-aware:** „neu" = kein State **für DIESE Richtung** (≁exists), sonst tauchen forward-geratete Vokabeln nie für reverse auf. |
| `get_content_data_for_review` (390) | `direction` in den Payload (Frontend braucht es zum Zurückspiegeln); **Leak-Maskierung NICHT hier** (flacher Payload, Reveal braucht JP+Audio) → im Frontend (7.4). |
| `get_user_stats` (301) | speist `/review`-Header + Nav-Badge via `/api/srs/stats` → pro Richtung ausweisen ODER kanonisch `forward` (9.4). |
| `get_interval_preview` (259), `get_card_detail` (967), `suspend_card` (1021), `unsuspend_card` (1031), `reset_card` (1042) | **`.first()`-Lookups um `direction` erweitern** — sonst trifft Suspend/Reset/Preview eine **arbiträre** Richtung (MAJOR). |
| `get_review_forecast` (608), `get_maturity_distribution` (631) | bewusst entscheiden: pro Richtung getrennt ODER kanonisch `forward` (9.4). |
| `get_leeches` (675) | pro Richtung (Produktion erzeugt mehr Leeches → 9.3). |
| `get_jlpt_progress` (739), `total_mastered` | **kanonisch `forward`** filtern → keine Doppelzählung (9.2). |
| `browse_cards` (806) | `direction`-Filter. |

**Route-Schicht `srs_routes.py` (im Original-Entwurf komplett fehlend — BLOCKER):**

| Route | Änderung |
|---|---|
| `api_rate_card` (30) | `data.get('direction','forward')`, **validiert gegen `{'forward','reverse'}`**, an `rate_card` durchreichen. |
| `api_due_cards` (86) | `direction` **pro Karte** mitliefern + Modus-Query-Param akzeptieren. |
| `api_interval_preview` (121) | `direction` annehmen + durchreichen (geteilt mit Deck=forward!). |

→ **`direction` ÜBERALL default-`forward`**, sonst brechen Deck (`lesson_view.html:4136`) und Kana-Grid (`kana_grid_game.js:716`).

**Weitere Konsumenten (vor Reverse-Aktivierung auf `forward` filtern):**

| Modul | Änderung |
|---|---|
| `dashboard_service.py` (`_pillar` 84–90, `_accuracy_by_content`, acc-by-stage) | `direction='forward'` (kanonischer Fortschritt) — sonst Mastery-Pillar-Doppelzählung. |
| `gamification_service.compute_kana_mastery_context` | `direction='forward'` — sonst Achievement-Schwellen doppeln. |

**QA-Verifikation:** Im Gate explizit prüfen, dass **Deck und Kana-Grid weiter `forward` raten** und nur `vocabulary` reverse-fähig ist.

### 6.5 Opt-in & Seeding-Mechanik (Henne-Ei gelöst)

**Problem (MAJOR):** Deck ist forward-only, also kann nur `/review` reverse einführen — aber „lazy create beim ersten reverse-Rating" ist **zirkulär** (man kann keine Karte raten, die nie gezeigt wurde). Zudem ist die `/review`-Queue (`get_due_cards`) **global, nicht lesson-scoped**, während ein `Lesson.production_cards_enabled`-Flag pro Lektion lebt.

**Entscheidung (MVP):** **Expliziter Seeding-Pfad statt lazy-on-rate.** Bei aktivem Opt-in werden die Reverse-Karten als **`new`** angelegt (eigener Seeding-Pfad), damit `get_new_cards` (direction-aware) sie in die Session zieht. Trigger des Seedings:

- **per-Lektion-Opt-in** über `Lesson.production_cards_enabled` (Default `false`), **verdrahtet in die globale Queue** über einen Auto-Anlege-Schritt **beim Lektions-Abschluss** (oder beim Umlegen des Flags) — die Reverse-`new`-Karten der Lektions-Vokabeln werden gesät, danach pullt die globale `get_new_cards` sie regulär unter `daily_new_cards`.
- **Sichtbarer Nudge statt stillem Boolean (MINOR-Fix):** Sobald die Vorwärtskarten einer Lektion Reife erreichen, zeigt die UI einen niedrigschwelligen Aufruf „Diese Lektion sitzt rezeptiv — jetzt produktiv üben?" (gekoppelt an erreichte Vorwärts-Reife). Das nimmt das reife-gesteuerte Auto-Anlegen leichtgewichtig vorweg, ohne die volle Automatik zu bauen — sonst lernt der eine Solo-Nutzer dauerhaft nur rezeptiv und das Feature verpufft.

**Phase-2-Evolution:** Reife-gesteuertes Auto-Anlegen (Vorwärtskarte Stage ≥ 5 → Reverse-`new` automatisch). Das löst Henne-Ei sauberer als jedes MVP-Lazy-Create — ggf. vorziehen, falls der MVP-Nudge zu fragil wirkt.

---

## 7. UI/UX

### 7.1 `/review`: Richtungswahl

Segment-Control „JP→DE · DE→JP · Gemischt" über der Queue (ink-on-washi). **Default „Gemischt"** (Interleaving als belegte desirable difficulty; Sibling-Suppression verhindert Session-Leaks). „nur JP→DE"/„nur DE→JP" für gezieltes Drillen.

**Pro-Karte ein eindeutiges Richtungs-Badge, NICHT allein farblich** (MINOR-Fix): Text + Icon, z.B. „DE → 日本語". **Shu bleibt dem primären Rating-Flow vorbehalten** (Design-System) — das Badge wird tonal + mit Label gelöst. Dark-Parität des Badges **explizit in den Playwright-Visual-Check** aufnehmen.

### 7.2 Karten-Aufbau DE→JP (konkret: was steht wo)

**Vorderseite (Cue, kein JP-Leak):**
- `production_cue_de`-Pill (primär) bzw. whitelisted deutscher Lückensatz; deutsche Bedeutung `meaning_de`.
- **Bild** (`image_url`) — sprachneutraler Cue, **vergrößert** (nicht 64×64), **dekoratives `alt=""`** (siehe 7.4).
- **Aufgaben-Hinweis VOR dem Flip** (MINOR-Fix): „Sprich das Wort / die Lesung" + Bestehensregel-Kurzcopy („Lesung zählt") — das Badge sagt die *Richtung*, der Hinweis sagt die *Aufgabe*.
- **Kein** `example_jp`, **kein** `example_romaji`, **keine** reading/romaji-Zeile, **kein** Audio-Button.

**Rückseite (Reveal):**
- **Zielwort** prominent: Kanji + **Lesung (Kana)** groß.
- Romaji sekundär; JP-Beispielsatz + Romaji + Übersetzung; **Audio-Button** (erst hier); **akzeptierte Synonyme/Alternativen**; 4 Rating-Buttons.

### 7.3 Deck-Karussell (`lesson_view.html`): bleibt vorwärts

**Entscheidung:** Das in-Lektion-Deck bleibt **JP→DE** (Erst-Begegnung; Recognition-first). Produktion gehört in die spätere Wiederholung (`/review`). **Phase 1 fasst KEIN Deck-CSS an** → die `.content-item.in-deck{display:none}`-Invariante ist hier nicht betroffen. Optional Phase 3: separater „Produktions-Durchgang"-Modus im Deck — der würde Deck-CSS + Jinja-Flip-Card anfassen und die Invariante in Reichweite bringen (dann Pflicht-Check, 12).

### 7.4 Leak-Invariante (festgeschrieben, korrigiert)

**Ist-Zustand (kein zu lösendes Problem):** Der **Audio-Button liegt in beiden Oberflächen bereits back-only** (`review.html:1558–1559` im `inert`-Back; `lesson_view.html:1740–1760` im `card-face--back`). Kein Front-Audio-Leak.

**Echte Front-Leaks, die der `reverse`-Render-Zweig hart unterdrücken MUSS:**
1. **`subText` (Z. 1551, reading + romaji)** — die **LESUNG** ist Teil der DE→JP-Antwort, der **schärfste Leak**. Muss hart unterdrückt werden, **unabhängig vom `show_romaji_on_front`/`html.hide-front-romaji`-Toggle** (der Toggle ließe die Zeile bei „an" sichtbar). Es geht um **reading**, nicht nur kosmetisches Romaji.
2. **`frontExample` (Z. 1407–1412, eingesetzt 1552)** — JP-Beispielsatz + Romaji auf der Front.
3. **Bild-`alt` (Z. 1419, aktuell `alt="${frontText}"` = JP-Wort)** — **ARIA-Leak:** ein Screenreader liest die Antwort vor. Für reverse-Front: **`alt=""`** (dekorativ) oder generischer Hinweis, **niemals** das JP-Wort/meaning. `inert` bleibt nach dem Feld-Tausch auf der **antworttragenden (Rück-)Seite**.

**Bild bleibt vorne** (additive **neue Platzierung** in `/review`, nicht „beibehalten" — heute ist es rückseitig). **Maskierung lebt im `review.html`-JS-Render-Zweig für `direction=='reverse'`**, nicht im Payload (flacher Payload, Reveal braucht JP+Audio). Deck ist forward-only → spart sich den Zweig (passt zur bekannten „zwei getrennte Karten-Render-Pfade"-Architektur, verkleinert den Scope).

### 7.5 Design-System, Dark, Mobile, Deck-Invariante

ink-on-washi (warmes Papier, Haarlinien, ein Shu-Akzent nur für Primary Action, deutsche Copy), **Dark-Parität**, mobil + desktop. **Pflicht-Check nach jeder `custom.css`-Änderung:** Deck-Karussell-Invariante.

---

## 8. Antwort bei Produktion & Bewertungs-Kalibrierung (MAJOR)

### 8.1 Maßstab

- **Lesung (Kana) ist der primäre Maßstab.** Für N5 (Kana-lastig) ist die realistische Produktionsleistung: *die richtige Lesung erzeugen*. Kanji steht als **Referenz** daneben, ist nicht das Bestehenskriterium.
- **Kana-only (`word == reading`, 304 Stück):** Produktion = nur Lesung; kein Kanji-Reveal (Special-Case schon im Code).

### 8.2 Das Kalibrierungs-Problem (im Original ungelöst)

Die Produktionsrichtung speist FSRS über **reines Flip-and-Self-Rate**. Selbstbewertung bei Produktion ist **systematisch nach oben verzerrt**: beim Aufdecken „fühlt sich die Lösung richtig an" (Hindsight/Familiarity-Bias). Beim Solo-Lerner (kein externer Korrektor) korrigiert das nichts. Die Synonym-Akzeptanz-Regel **verschärft** es: Um zu beurteilen „ist mein Wort ein akzeptiertes Synonym?", muss man die Lösungsmenge bereits kennen — genau das Wissen, das ein N5-Anfänger noch nicht hat. **Schlechte Ratings untergraben die ganze pädagogische Begründung** (getrennt messbare produktive Reife).

### 8.3 Bewertungs-Disziplin (Fix, sichtbar an der Karte)

- **(a) Maßstab verschärfen:** „Good" **nur, wenn die Lesung VOR dem Aufdecken vollständig im Kopf war** — nicht „kam mir bekannt vor". Als Hinweis im UI. „Kana saß, Kanji nicht" → bewusst **Hard** (Teilerfolg). Komplett daneben → Again.
- **(b) Getippter Kana/Romaji-Modus als Kalibrierungs-Anker FRÜHER erwägen:** Eine objektive Teilprüfung der Lesung neutralisiert den Hindsight-Bias am stärksten. Im Original Phase-3-„Stretch" — hier **mindestens als optionaler Modus diskutiert** (10), nicht ganz nach hinten geschoben. Empfehlung: als optionaler Modus in **Phase 2** verfügbar, damit Claudio die Self-Assess-Spur gegen eine objektive Spur kalibrieren kann.
- **(c) Akzeptierte Synonyme/Alternativen IMMER auf der Rückseite** anzeigen **UND** die Bestehensregel als kurze, sichtbare Konvention **an der Karte** (Badge-/Prompt-Copy), nicht nur im Doc.

---

## 9. Gamification- & Stats-Implikationen

### 9.1 XP

`calculate_xp` ist richtungsagnostisch → **Reverse-Reviews geben XP wie Vorwärts** (erwünscht — Produktion ist härter). Tages-XP-Cap und Variable-Reward (`rate_card` Z. 155ff) unverändert.

### 9.2 Mastery / JLPT-Progress (Doppelzählung auflösen)

**Entscheidung:**
- **Vorwärtskarte definiert den kanonischen JLPT-Fortschritt und `total_mastered`.** `get_jlpt_progress` + `dashboard_service`-Aggregationen + `gamification_service.compute_kana_mastery_context` filtern explizit **`direction='forward'`** → eine Vokabel zählt **nicht doppelt**.
- **Produktion als eigene Spur** („produktiv gemeistert", Stage ≥ 5 der Reverse-Karte) — sichtbar auf `/review/stats`, getrennt vom JLPT-Kern.
- Bestehende **Stage-≥9-vs-≥5-Diskrepanz** (2.2): unverändert lassen, aber bei beiden Stellen `forward` filtern, damit Reverse sie nicht zusätzlich verzerrt.

### 9.3 Leech-Handling: Erkennung MIT Intervention (MINOR-Fix)

Produktion erzeugt mehr Leeches (Mehrdeutigkeit). **Erkennung ist nicht Behandlung.** Pro-Richtung-Leech mit **konkreter Aktion** koppeln:

> **Reverse-Leech über `UserSRSSettings.leech_threshold` → Karte suspendieren UND als Signal „`production_cue_de` fehlt/unzureichend" flaggen** (Kuratier-Backlog), statt sie weiter unfair zu raten.

Das schließt den Kreis zur Disambiguierungs-Lücke (5.2): Reverse-Leeches decken **genau** die Cue-Lücken auf. `get_leeches` wird richtungsfähig (6.4).

### 9.4 Due-Count-/Stats-Inflation (breiter als im Original)

Inflationär bei aktiver Produktion sind **nicht nur** `get_due_count`, sondern auch `get_user_stats` (`total_cards`, `due_count`, `status_counts` → `/review`-Header **und** Nav-Badge via `/api/srs/stats`), `get_review_forecast` (608), `get_maturity_distribution` (631). **Entscheidung:** pro Richtung getrennt ausweisen ODER für die **kanonische** Zahl auf `forward` filtern. **Nav-Badge (`due_count`) darf sich nicht stillschweigend verdoppeln.** Last-Deckel: `daily_review_limit` + Opt-in (6.5) + Same-day-Suppression (6.4).

---

## 10. Grading-Stufen (Scope-Schutz)

- **Default & MVP: Self-Assess-Flip.** Aufdecken → Again/Hard/Good/Easy. Passt zur bestehenden UX, umgeht „synonym hell" (das getippte JP-Tools wie KaniWani plagt; Bunpro nutzt für Vokabeln Selbstbewertung), erlaubt „Kana ja, Kanji nein"-Wertung. **Mit der Kalibrierungs-Disziplin aus 8.3.**
- **Stretch (Phase 2 optional / Phase 3): getippte Kana/Romaji-Eingabe** als **Kalibrierungs-Anker** (8.2b). WanaKana-artige Romaji→Kana-Wandlung, Fuzzy-Match (Levenshtein ≤ 1), Kana-vs-Kanji-Akzeptanz, „War richtig"-Override. **Neuer, eigener Pfad außerhalb des Quiz-Systems** — das Quiz kennt kein `fill_in_the_blank` (nur `multiple_choice`/`true_false`/`matching`), also keine Quiz-Erweiterung. Untermauert, es separat zu halten.

---

## 11. Phasenplan (additiv, reversibel, MVP zuerst)

| Phase | Scope | Aufwand |
|---|---|---|
| **Phase 0 — Display-Vorspiel (Interim, Option B)** | `/review`-Toggle „DE→JP anschauen", **ohne** Schema, Front/Back getauscht + Leak-Maskierung (7.4). Validiert UI/Disambiguierung an echten Karten. Kein eigenes SRS. Vollständig reversibel (nur Frontend). | klein |
| **Phase 1 — MVP: echtes SRS pro Richtung (Option A)** | `direction`-Spalte + Unique-Umstellung + Backfill (6.3, mit ehrlichem Downgrade); `rate_card` INSERT-`direction` + Signatur; Route-Schicht `srs_routes.py` (default-forward, validiert); `get_due_cards`/`get_due_count`/`get_new_cards`/`get_content_data_for_review`/`.first()`-Lookups richtungsfähig; `dashboard_service`/`gamification_service` auf `forward`; **`production_cue_de`-Kuratierung der Homonym-/Register-Härtefälle (vorgezogen!)**; DE→JP-Karte mit Cue + Bild (dekoratives `alt`) + Frontend-Leak-Maskierung; Self-Assess-Flip **mit Kalibrierungs-Copy (8.3)**; Same-day-Sibling-Suppression; `meaning_de`-Gate; **expliziter Seeding-Pfad + sichtbarer Reife-Nudge (6.5)**. **Kleinstes wertvolles Inkrement: Produktion echt geplant für *eine* aktivierte Lektion, mit funktionierender Disambiguierung.** | groß |
| **Phase 2 — Reife-Auto-Anlegen + Kalibrierung + Stats** | Reife-gesteuertes Auto-Anlegen (Stage ≥ 5); **optionaler getippter Kalibrierungs-Modus (8.2b)**; getrennte Produktions-Statistik auf `/review/stats`; Reverse-Leech-Intervention (9.3); `get_leeches`/`get_maturity_distribution`/`browse_cards`/`get_review_forecast`/`get_user_stats` richtungsfähig; Modus-Schalter `/review`. | mittel |
| **Phase 3 — Stretch** | Satz-/phrasenproduktive Karten (deutscher Cue → JP-Mini-Satz, TAP-konsequenter, 1/4.1); optionaler Produktions-Durchgang im Deck nach rezeptivem Erstdurchlauf (**dann Deck-Invariante-Pflicht-Check**, 7.3/12). | mittel–groß |

---

## 12. Tests & QA

**pytest:**
- Migration: upgrade idempotent, Altzeilen → `forward`; **`(user,content,'forward')` und `(user,content,'reverse')` koexistieren, Duplikat je Richtung verboten**; **`downgrade` löscht reverse-Zeilen und stellt 2-Spalten-Unique wieder her** (Trade-off-Test).
- `rate_card(..., direction='reverse')`: **INSERT setzt `direction` explizit** (kein Unique-Crash gegen die forward-Zeile); legt **frischen `Card()`** an (erbt nichts); eigener `due_date`/Stage; `ReviewLog.direction` gesetzt.
- **Default-forward end-to-end:** `api_rate_card` ohne `direction` → forward; **Deck (`lesson_view.html:4136`) und Kana-Grid (`kana_grid_game.js:716`) raten weiter forward**; ungültiger `direction`-Wert wird abgewiesen.
- `get_new_cards` direction-aware: forward-geratete Vokabel taucht für reverse als „neu" auf.
- `get_due_cards`/`get_due_count`: pro Richtung; Same-day-Sibling-Suppression liefert nicht beide Richtungen desselben `content_id` in eine Session.
- `get_jlpt_progress`/`total_mastered`/`dashboard`/`gamification`: zählen **nur forward** → keine Doppelzählung.
- `.first()`-Lookups (`suspend`/`reset`/`preview`/`detail`): treffen die **richtige** Richtung.
- **Leak-Test:** Reverse-Front-Render enthält **kein** reading/romaji, **kein** `example_jp`/`example_romaji`, **kein** Front-Audio; Bild ja, **`alt` leer/dekorativ**; deutscher Cue ja.
- `meaning_de`-Gate: leeres `meaning_de` → keine Reverse-Karte / Fallback + Warn-Log.
- Reverse-Leech über `leech_threshold` → Suspend + Cue-Flag.

**Playwright-Visual (mobil + desktop, light + dark):**
- DE→JP-Karte: Front = Cue + Bild + Aufgaben-Hinweis, **kein JP/Audio/reading**; Back = Lesung prominent + Audio + Synonyme.
- Richtungs-Badge **mit Label** in **beiden Themes** (Dark-Parität, Shu nur Primary).
- **Deck-Karussell-Invariante** nach allen CSS-Änderungen (eine Karte sichtbar, `[Deck]`-Konsole prüfen) — in Phase 1 unberührt, **Pflicht ab Phase 3**.

**ruff** clean. **QA-Gate** (pytest grün + ruff clean + Visual gut) ist Deploy-Voraussetzung.

---

## 13. Risiken & offene Punkte

| Risiko | Schwere | Mitigation |
|---|---|---|
| **Lückensatz-Maskierung** unsauber (nur ~70 % Lemma verbatim; löst Kern-Härtefälle nicht) | **hoch** (hochgestuft) | `production_cue_de` ist **primär**, Lückensatz nur whitelisted/opportunistisch; Cue-Kuratierung in Phase 1 vorgezogen. |
| **Self-Assess-Kalibrierung** (Hindsight-Bias, Synonym-Zirkel) | hoch | Verschärfter Maßstab + sichtbare Copy (8.3); getippter Kalibrierungs-Anker früh (Phase 2). |
| **Review-Last-Explosion** (Verdopplung) | hoch | Opt-in pro Lektion + Reife-Gate; `daily_review_limit`; Same-day-Suppression. |
| **Migrations-Reichweite** (~20 Touchpoints, 3 Rate-Oberflächen, 2 Service-Module, Route-Schicht) | mittel | Vollständiges Inventar (6.4); default-forward end-to-end; real gegen Prod-DB testen. |
| **Downgrade = Reverse-Datenverlust** | gering | bewusst dokumentiert (6.3); Reverse ist additives Opt-in. |
| **Homonym-Restrisiko** trotz Cue | mittel | Cue + whitelisted Lückensatz + Synonym-Reveal; Reverse-Leech-Intervention deckt Lücken auf (9.3). |
| **`meaning_de`-Lücken** | gering (N5: 0) | Gate + Coverage-Query vor Rollout. |
| **ReviewLog richtungsblinde Aggregation** (Optimizer mischt Profile) | gering (kein MVP-Blocker) | `ix_reviewlog_direction`; bei künftiger FSRS-Optimierung **pro Richtung** optimieren; bis dahin dokumentiert. |
| **Solo-Lerner aktiviert Produktion nie** (stilles Flag) | mittel | sichtbarer Reife-Nudge im MVP (6.5), nicht nur Boolean. |
| **TAP-Reichweiten-Grenze** (nur Einzelwort) | gering (ehrlich benannt) | als bewusste Limitation deklariert; Satz-Produktion = Phase 3. |

---

## Entscheidungen — festgelegt 2026-06-21 (lösen die offenen Fragen ab)

Alle vor Phase 1 offenen Punkte sind entschieden; die Datenfragen wurden empirisch gegen die DB (lokale Dev = an diesem Tag aus Prod angeglichen) geklärt. **Dieser Abschnitt ist maßgeblich** und hat bei Konflikten Vorrang vor dem ursprünglichen Entwurf in 6.5 / 7.1 / 9.4.

### A. Architektur-Pivot — eigene Produktions-Seite statt Opt-in-Toggle (löst die frühere „Opt-in-Granularität")

Produktion bekommt eine **eigene, immer verfügbare Seite `/review/produktion`** mit **eigener Queue** — statt eines Richtungs-Toggles in `/review` und statt eines per-Lektion-Opt-in-Flags. **Weiterhin auf Basis der `direction`-Schema-Spalte (Option A bleibt** — die Seite ist eine Darstellungs-/Queue-Wahl, **kein** Ersatz für die getrennte FSRS-Spur).

Damit **entfallen** aus dem ursprünglichen Entwurf:
- per-Lektion-Flag `Lesson.production_cards_enabled` + Reife-Nudge (6.5) → ersetzt durch Auto-Population nach Reife (B).
- Modus-Schalter „JP→DE · DE→JP · Gemischt" in `/review` (7.1) → `/review` bleibt reine Rezeptions-Queue.
- Same-day-Sibling-Suppression + Interleaving (6.4) → **nicht mehr nötig**: beide Richtungen teilen nie eine Session, also kann eine Karte ihre Gegenrichtung nicht innerhalb der Session verraten.
- Due-Count-Verdopplung im `/review`-Badge (9.4) → das `/review`-Badge bleibt **forward-only**; die Produktions-Seite führt einen **eigenen** Zähler. Selbst-getaktete Last (man zieht Produktion, wenn man will).

`lesson_view`-Deck bleibt **forward** (7.3 unverändert). Die Karten-/Rating-Logik der Produktions-Seite teilt sich `showCard()`/Rating-JS mit `review.html` (direction-Param + eigener Queue-Endpoint), kein Voll-Neubau.

### B. Population der Produktions-Queue (Q5): erst bei rezeptiver Festigung

Eine Vokabel betritt die DE→JP-Queue **automatisch, sobald ihre JP→DE-Karte Stage ≥ 3** („Lernphase überstanden") erreicht hat — Recognition-first ohne Opt-in, kein Produzieren gerade erst gesehener Wörter. Schwelle kalibrierbar; Start mit ≥ 3. (Das ist die frühere Phase-2-„Reife-Auto-Anlegen"-Idee, hier zur MVP-Populationsregel der Seite gemacht.)

### C. Daten — verifiziert 2026-06-21 (lokale DB = an diesem Tag aus Prod angeglichen)

| Befund | Wert | Konsequenz |
|---|---|---|
| `meaning_de`-Coverage N5 | **799/799 = 100 %** (N4 33 %, gesamt 99,3 %) | N5 reverse-fähig; N4 zuerst Daten-Pflege |
| Lückensatz-Maskierbarkeit N5 | **64 %** sauber maskierbar (loose 77 %) | besser als befürchtet, **aber** maskierbar ≠ disambiguierend |
| Kollidierende dt. Cues (roh) | 142 Cues / 303 Vok (38 %) | inkl. 76 reiner Kanji/Kana-Dubletten |
| **Echte Homonyme/Synonyme** | **66 Cues / 151 Vok = 19 % von N5** | das ist der sicherheitskritische `production_cue_de`-Backlog |

### D. Restliche Beschlüsse

- **Lückensatz-Whitelist (Q1):** empirisch ermittelt (64 % maskierbar). Whitelisted Cloze nur dort, wo das Zielwort **sauber maskierbar UND disambiguierend** ist (Teilmenge). Bleibt **sekundär** hinter `production_cue_de`.
- **`production_cue_de`-Backlog (Q2): ganzer N5-Bestand**, gestaffelt — die **~19 % echten Härtefälle** (semantischer/Register-Cue) **zwingend in Phase 1**; die übrigen ~81 % bekommen einen leichten **Wortart-Tag** (Verb / i-Adj / na-Adj / Nomen …).
- **Kalibrierung (Q6):** getippter Kana/Romaji-Modus als **Opt-in in Phase 2**; Self-Assess-Flip bleibt Default (mit Disziplin-Copy 8.3).
- **Produktions-Stats (Q7): eigener Block** „Produktiv gemeistert" auf `/review/stats`, getrennt vom JLPT-Kern (forward bleibt kanonisch, keine Doppelzählung — 9.2).
- **Satz-Produktion (Q8):** als **Phase-3-Ziel eingeplant** (deutscher Cue → JP-Mini-Satz, TAP-konsequenter). Einzelwort-Produktion ist der MVP, **nicht** der Endzustand.

### E. Neuer Pre-Phase-1-Task (aus der Analyse aufgetaucht)

Die **76 Kanji/Kana-Dubletten** (dieselbe Vokabel als 時 *und* じ usw., gleiche Lesung) **vor Phase 1 deduplizieren/zusammenführen** — sonst entstehen zwei Reverse-Karten fürs selbe Wort, und der Cue-Backlog wird künstlich aufgebläht.

### F. Verbleibende Mikro-Stellschrauben (nicht blockierend)

- Genaue Reife-Schwelle (Stage ≥ 3 vs. Stabilität-in-Tagen) — Start mit ≥ 3, nach Gefühl justieren.
- Default-Sortierung der Produktions-Queue (fällige zuerst vs. neu-nach-Reife gemischt).

---

## Review-Notiz

Eingearbeitet: **0 Blocker offen** (3 Engineering-Blocker gelöst: `downgrade`-Reverse-Löschung, `rate_card`-INSERT-`direction` explizit, Route-Schicht `srs_routes.py`) + **9 Major gelöst** (Cue-Primat statt Lückensatz, Self-Assess-Kalibrierung, dritte Rate-Oberfläche `kana_grid_game.js`, zwei Service-Module `dashboard_service`/`gamification_service`, Opt-in-Henne-Ei/Seeding, mehrdeutige `.first()`-Lookups, breitere Due-/Stats-Inflation, Leak-Inventar reading/`alt`-ARIA korrigiert, Bild-Cue-Neuplatzierung + Cloze-Scaffold-Wiederverwendung) + **9 Minor** (Leech-Intervention, TAP-Grenze, Deck-Produktions-Nudge, ReviewLog-Index, Leak an Frontend-Schicht, `reading`-Benennung, Badge-Klarheit/Aufgaben-Hinweis, Richtungs-Badge nicht-farblich/Dark-Parität, Deck-Invariante-Phasen-Marker, Coverage-Re-Verifikation). Quer über alle 3 Review-Linsen (Pädagogik 6, Engineering 9, UX/Frontend 7 Findings).