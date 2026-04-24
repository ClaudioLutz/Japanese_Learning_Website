# Learnings — generate-lesson

Selbstverbesserndes Log. Wird vor jedem Run gelesen, nach jedem Run angehängt.

## Format

```markdown
## YYYY-MM-DD HH:MM — [JLPT-Level] Thema (Lesson ID X)

### Erfolge
- ...

### Probleme / Erkenntnisse
- Beobachtung → **Regel für nächstes Mal: ...**

### Aktuelle Regeln (kumulativ, wichtigste zuerst)
1. ...
2. ...
```

**Regel-Hochstufung:** Wenn derselbe Fehler 2× in unterschiedlichen Runs auftritt, **in SKILL.md §3 oder §5 hochheben**, nicht nur hier stehen lassen.

---

## Initial-Regeln (vor erstem Run, aus improve-jpl + CLAUDE.md abgeleitet)

1. **Mayuko-First:** Vor jeder Design-Entscheidung: "Würde Mayuko das bemerken, verstehen, wiederkommen?" Wenn nein → zurückstellen.
2. **Anfänger-Only:** N5 und N4. N3+ ist aktuell aus-scope.
3. **Keine `fill_in_the_blank` Quiz-Typen.** Niemals. Auch nicht "nur diesmal".
4. **Instruction-Language default `german`.** Mayukos Sprache.
5. **Beispielsätze dürfen KEINE Kanji/Vokabeln über dem Lektions-Level nutzen.** Wenn unvermeidbar: Hiragana schreiben.
6. **Umlaute echt, nicht ASCII-Fallback.** Schüler, nicht Schueler.
7. **Duplicate-Check vor Kana/Kanji/Vocabulary/Grammar-Insert.** Bestehende ID wiederverwenden.
8. **Atomare Transaktion:** Ganze Lektion oder nichts. Kein halbes Insert.
9. **Verifikation via Playwright ist Pflicht** bevor Git-Commit oder is_published=True.
10. **Mix der Quiz-Typen pro Page:** Nicht 10× multiple_choice. Immer mind. 2 Typen mischen (mc/tf/matching).

---

## Run-Log

<!-- Neuste Einträge oben, älteste unten. -->

## 2026-04-24 21:15 — N5 Zahlen — Von 1 bis 10'000 (Lesson ID 143)

### Erfolge
- 22 Vokabeln (Grundzahlen 0-10, Zehner, 100/1'000/10'000, Yen, sai/nansai, denwa bangou, nanban) — alle N5, thematisch kohärent
- 3 Grammatik-Einträge (Alter 〜さい, Preis 〜円, Telefonnummer) — jeder mit Romaji im `romaji`-Feld UND in `structure` daneben, plus dreizeilig formatierten `example_sentences` (JP / Romaji / DE)
- 14 Quiz-Fragen: 7 MC + 4 TF + 3 Matching — alle 3 erlaubten Typen vertreten
- 7 Pages (Einführung, 2× Vokabeln, Grammatik, Dialog, Quiz, Zusammenfassung) — über Budget-Minimum
- Dialog mit eigenen Charakteren (Tanaka Haruto & Lisa Weber), nicht MNN-Original-Figuren; Format exakt nach `_format_conversation` (speaker: JP / (romaji) / → DE)
- Umlaute durchgängig korrekt (Einführung, nützlich, höflich, wörtlich, Sonderlesung, Fünfzig, überschreibt)
- Romaji in allen Feldern: `content_text` jedes JP-Worts, `Grammar.title/.structure/.explanation/.example_sentences`, `QuizQuestion.hint/.explanation`, `QuizOption.option_text/.feedback`
- Thumbnail via DALL-E (gpt-image-1-mini) generiert, lokal gespeichert, URL gesetzt
- Validator lief sauber durch (nur thumbnail_url-Fehler vor dem images-Step, erwartet)
- Insert-Transaktion atomar, Lesson 143 + 7 Pages + 22 Vocab-Referenzen + 3 Grammar + 14 Questions + 38 Options in einer Transaktion

### Probleme / Erkenntnisse

1. **pipeline.py `generate_single_image(purpose=…)` hatte falsche Signatur** — `AILessonContentGenerator.generate_single_image()` in `app/ai_services.py:333` akzeptiert nur `prompt`, `size`, `quality`. `purpose` war ein halluzinierter Parameter. Zusätzlich: Methode liefert `image_bytes` (PIL + raw bytes) statt direktem URL; Pipeline nutzte aber `result.get("image_url")` was nur ein Platzhalter-String ist. **Fix angewandt**: `pipeline.py` schreibt bytes jetzt lokal nach `app/static/uploads/generated/thumbnail_{slug}_{ts}.png` und setzt relative URL. → **Regel: Wenn Pipeline-Code Services aufruft, periodisch auf Drift prüfen; `gen.generate_single_image()` hat sich seit Stub-Zeit geändert.**

2. **MNN-Import-Altdaten inkonsistent**: 8 bestehende Vokabeln (ひゃく, せん, まん, えん, さい, なんさい, でんわばんごう, なんばん) hatten Romaji in der `reading`-Spalte (Hepburn-Text statt Hiragana) und NULL in `romaji`. Die `_get_or_create_vocab`-Funktion hat sie korrekt dedupliziert — aber die inkonsistenten Daten blieben auf der Karte sichtbar. **Fix angewandt**: UPDATE auf alle 8 Wörter: `reading` → Hiragana, `romaji` → vorheriger Romaji-Wert. → **Regel: Beim Duplicate-Match zusätzlich prüfen, ob die Bestands-Vokabel dem heutigen Schema genügt (`romaji NOT NULL`, `reading matches ^[ぁ-んァ-ヶー]+$`). Wenn nein: opportunistisch backfillen, nicht nur neue Lektion drumrum schreiben.**

3. **DeprecationWarnings für `datetime.utcnow()`** in pipeline.py — niedrigprio, aber jetzt mehrfach gesehen. Python 3.13-ready: `datetime.now(datetime.UTC)`. Kein neuer Fehler, nur Lint.

### Aktuelle Regeln (kumulativ, wichtigste zuerst)

1. **Mayuko-First** vor jeder Design-Entscheidung.
2. **Anfänger-Only (N5/N4)** — N3+ out-of-scope.
3. **Keine `fill_in_the_blank` Quiz-Typen.**
4. **Instruction-Language default `german`.**
5. **Beispielsätze nur mit Vokabeln/Kanji ≤ Lesson-Level.**
6. **Umlaute echt (UTF-8), nie ASCII-Fallback.**
7. **Duplicate-Check via `_get_or_create_*` vor Kana/Kanji/Vocabulary/Grammar-Insert.**
8. **Atomare Transaktion:** Ganze Lektion oder nichts.
9. **Verifikation Pflicht** (DB-Query, Playwright oder HTTP-Fallback) bevor `is_published=True`.
10. **Mind. 2 Quiz-Typen pro Lektion** (Zahlen-Lesson: 3 genutzt).
11. **MC-Distraktoren aus selber semantischer Domäne.**
12. **Grammar-Eintrag: `romaji` immer füllen**, nicht nur `structure`.
13. **Admin-Credentials:** `ADMIN_EMAIL` und `ADMIN_PASSWORD` aus `.env` — nicht hardcoden.
14. **Admin-Lesson-Liste:** `/api/admin/lessons` (JSON), nicht `/admin/manage/lessons` (AJAX-Shell).
15. **Docker-Start-Check:** Docker-Desktop-Prozess prüfen, nicht nur `docker compose ps`.
16. **Rōmaji in ALLEN Textfeldern** (auch content_text, grammar.structure, quiz.hint/explanation, option.feedback).
17. **Umlaute hart validiert** — jedes erkannte `ue/oe/ae/ss` bricht validate ab.
18. **Beim Duplicate-Match Bestands-Vokabel auf aktuelles Schema prüfen** (reading=Hiragana, romaji NOT NULL). Wenn inkonsistent: im selben Run opportunistisch backfillen.
19. **Pipeline-Service-Calls periodisch auf Signatur-Drift prüfen** — `generate_single_image` akzeptiert kein `purpose`-Arg, liefert `image_bytes` statt finalem URL.

## 2026-04-24 21:30 — User-Feedback: Romaji überall, Umlaute statt ASCII

**Claudio nach weiterer Sichtung von Lesson 142 (Grammar-Karte):**
1. Grammar-Karte zeigte `[Nomen] + を + ください` ohne Romaji-Auflösung daneben.
   Romaji war nur separat als `[noun] + wo + kudasai` unten, aber nicht direkt
   neben der JP-Struktur sichtbar.
2. Meine content_text-Plaintexts hatten Umlaut-Fallbacks (ue/oe/ss/ae) statt
   echten Umlauten. "moechtest", "hoeflich", "koestlich", "haengen" usw.

**Actions:**
- SKILL.md §3 "Keine Umlaut-Fallbacks": hart ausformuliert. Gilt in jedem
  DE-Text-Feld — `content_text`, `hint`, `explanation`, `feedback`,
  `option_text`, `Lesson.description`, `LessonPage.title` usw.
- SKILL.md §3 "Rōmaji NEBEN JEDEM japanischen Zeichen": komplett ausgebaut
  mit Liste aller betroffenen Felder: `content_text`, `Grammar.title`,
  `Grammar.structure`, `Grammar.explanation`, `Grammar.example_sentences`,
  `QuizQuestion.question_text/hint/explanation`, `QuizOption.option_text/feedback`,
  `Vocabulary.romaji`, `Vocabulary.example_sentence_english`.
- pipeline.py Validator:
  - **Umlaut-Fallback-Check** ist jetzt HARTER Fehler (vorher nur informativ).
    Erkennt `hoeflich, fuer, Einfuehrung, Getraenk, Schueler, koennen` etc.
  - **Romaji-in-content_text-Check**: wenn `content_text` JP-Zeichen enthält,
    muss mind. eine Klammer-Passage `(romaji)` vorkommen.
- Lesson 142: fix2-Script ausgeführt. 4 content_text neu mit echten Umlauten
  und Romaji-Annotation pro JP-Wort; Grammar #48 (〜をください) mit
  strukturiertem example_sentences (dreizeilig: JP / Romaji / DE),
  angereicherter explanation mit Romaji an jeder JP-Stelle.

**Neue Regel (kumulativ, ab sofort):**
16. **Rōmaji in ALLEN Textfeldern** (nicht nur Vocab/Grammar-Records).
    JP-Zeichen bekommen immer `(romaji)` in Klammern direkt danach.
17. **Umlaute hart validiert** — jedes erkannte `ue/oe/ae/ss` in deutschen
    Wörtern bricht den validate-Schritt ab.

---

## 2026-04-24 21:20 — MNN-Rohdaten-Recherche & Konversations-Pattern

**Recherche-Ergebnis auf Claudios Anfrage:**

1. **MNN-Rohdaten liegen vor**: `scripts/mnn_data/beginner1_lesson01.json` bis `beginner2_lesson50.json` — 50 Lektionen komplett strukturiert (Vocabulary, Grammar, Conversation mit speaker/japanese/romaji/english, teils additional_conversations).

2. **Bestehende 10 MNN-Lektionen in der DB** (IDs 131–141, `MNN L1…L5` EN + DE) wurden via `scripts/import_mnn.py` **direkt importiert** — keine AI. Layout: 5 Seiten (Vokabeln → Grammatik → Konversation → Übung → Prüfung). Konversation liegt als Plaintext in `lesson_content.content_text` auf `page_number=3`, Format: `Speaker: 日本語\n  (romaji)\n  → English/Deutsch`, Leerzeile zwischen Sprechern — erzeugt durch `_format_conversation()` in [scripts/import_mnn.py:170](../../scripts/import_mnn.py#L170).

3. **Konsequenz für generate-lesson:**
   - MNN-JSON dient als **Vorlage**, nicht zur Copy-Paste. Claude schreibt auf Basis der MNN-Grammatik/Vokabeln eine neue Lektion mit **anderen Charakteren** (nicht Miller/Satou/Yamada) und leicht variiertem Dialog-Text.
   - Konversations-Page ist Pflicht und nutzt exakt das `_format_conversation()`-Plaintext-Format.

**Actions:**
- SKILL.md §2a neu: Komplette Sektion zu MNN-Nutzung (Rohdaten-Pfade, Vorlagen-Regel, Konversations-Format).
- SKILL.md §4: Dialog-Page (bisher "A:/B:") durch das `_format_conversation`-Format ersetzt.
- SKILL.md §9: Explizite Pfade zu allen 50 MNN-JSONs und import_mnn.py-Verweis.

---

## 2026-04-24 21:00 — User-Feedback nach visueller Sichtung Lesson 142

**Claudio nach Öffnen von Lesson 142 im Browser:**
1. HTML-Tags erscheinen als Text statt gerendert → **Ursache gefunden:** `lesson_view.html:683` nutzt `{{ content.content_text | nl2br }}`, das escaped HTML. Nur Plaintext wird korrekt dargestellt.
2. Rōmaji fehlt komplett in der Lektion → User verlangt "Oman'sch-japanisch-westliche Schreibweise". `Vocabulary` hatte bisher kein `romaji`-Feld.
3. Bilder fehlen (Thumbnail + Schlüsselvokabeln).
4. Lektion inhaltlich zu dünn: 10 Vokabeln + 1 Grammar + 7 Quiz reichen nicht für einen wertvollen Lernpass.

**Actions (alle in SKILL.md §3, §4, §5 hochgehoben):**
- Neue Migration `a3f5c2d1b8e9`: `Vocabulary.romaji` Spalte (String(200), nullable).
- Neue Regel: **KEIN HTML in `content_text`** (Plaintext + `\n\n`).
- Neue Regel: **Rōmaji ist Pflicht** in `Vocabulary.romaji`, `Grammar.romaji` und am Anfang jedes `example_sentence_english`.
- Neue Regel: **Bilder (Thumbnail + ≥3 Vokabel-Bilder) sind Pflicht**, nicht optional.
- Neues Budget: **15–25 Vokabeln, 2–4 Grammar, 10–18 Quiz, ≥5 Pages** (+ separater Dialog-Page).
- Validator in `pipeline.py` erzwingt alle diese Regeln beim `validate`-Schritt.

---

## 2026-04-24 20:30 — N5 Essen im Restaurant (Lesson ID 142)

### Erfolge
- 10 Vokabeln (レストラン, メニュー, 水, お茶, ご飯, 肉, 魚, 飲み物, 食べ物, 美味しい) — thematisch kohärent, alle N5
- 1 Grammatik (〜をください) — die zentrale Bestell-Formel
- 7 Quiz-Fragen: 4 MC + 2 TF + 1 Matching — 3 Typen, passt zu Regel "mind. 2 verschiedene"
- MC-Distraktoren aus derselben semantischen Domäne (Essens-/Trink-Vokabular), kein offensichtlicher Blindgänger
- Beispielsätze nutzten ausschliesslich N5-Vokabeln und -Kanji, meist Hiragana-fokussiert
- Alle DE-Umlaute korrekt (Einführung, höflich, Getränk, köstlich) — kein ASCII-Fallback im HTML
- DB-Insert atomar, pipeline.py validate+insert klappte auf Anhieb

### Probleme / Erkenntnisse

1. **Docker Desktop war aus.** → **Regel: Start-Check MUSS Docker-Desktop-Prozess prüfen, nicht nur `docker compose ps`. Wenn Docker down: PowerShell-Start, 30-60s warten, dann `docker compose up db -d`.** (In SKILL.md §1 hochgehoben.)

2. **`verify.py` ist zweifach defekt:**
   - Nutzt `username=admin` + `password=admin` → Login-Form braucht `email` + `password`, und Credentials stehen in `.env` als `ADMIN_EMAIL` / `ADMIN_PASSWORD`.
   - Wartet auf `**/dashboard*` Redirect → Admin-Login leitet zu `/admin`, nicht `/dashboard`.
   → **Regel: verify.py muss aus `.env` laden (`ADMIN_EMAIL`, `ADMIN_PASSWORD`), Form-Feld heisst `email`, Post-Login-URL ist `/admin`.** (Pipeline-Fix gehört in SKILL.md §6 und verify.py selbst.)

3. **MCP-Playwright-Browser kann besetzt sein** (parallele User-Chrome-Session). Fehlermeldung: "Browser is already in use". → **Regel: Wenn MCP-Browser geblockt, Fallback auf HTTP-Requests-basierte Verifikation (requests.Session mit CSRF + Login + Content-Check). Der Hauptzweck — Struktur/Content/Umlaut-Korrektheit — ist damit erfüllt; visueller Deck-Karussell-Check muss dann manuell vom User gemacht werden.**

4. **Admin-Lesson-Liste unter `/admin/manage/lessons` ist SPA (AJAX).** Server-side gerenderte HTML enthält KEINE Lesson-Titel; die werden per JS aus `/api/admin/lessons` geladen. → **Regel: Verifikation der Sichtbarkeit muss `/api/admin/lessons` treffen, nicht die HTML-Shell.**

5. **pipeline.py nutzt `datetime.utcnow()`** — Python 3.12 DeprecationWarning. Niederpriorisierter Lint-Fix. → Nur Info, keine neue Regel.

### Aktuelle Regeln (kumulativ, wichtigste zuerst)

1. **Mayuko-First** vor jeder Design-Entscheidung.
2. **Anfänger-Only (N5/N4)** — N3+ out-of-scope.
3. **Keine `fill_in_the_blank` Quiz-Typen.**
4. **Instruction-Language default `german`.**
5. **Beispielsätze nur mit Vokabeln/Kanji ≤ Lesson-Level.**
6. **Umlaute echt (UTF-8), nie ASCII-Fallback.**
7. **Duplicate-Check via `_get_or_create_*` vor Kana/Kanji/Vocabulary/Grammar-Insert.**
8. **Atomare Transaktion:** Ganze Lektion oder nichts.
9. **Verifikation Pflicht** bevor is_published=True. Wenn MCP-Browser blockiert → HTTP-Fallback ausreicht, aber User muss visuell klicken.
10. **Mind. 2 Quiz-Typen pro Lektion.**
11. **MC-Distraktoren aus selber semantischer Domäne.** (validiert im Essen-Run)
12. **Grammar-Eintrag: `romaji` immer füllen**, nicht nur `structure`.
13. **Admin-Credentials:** `ADMIN_EMAIL` und `ADMIN_PASSWORD` aus `.env` — nicht hardcoden.
14. **Admin-Lesson-Liste:** `/api/admin/lessons` (JSON), nicht `/admin/manage/lessons` (AJAX-Shell).
15. **Docker-Start-Check:** Docker-Desktop-Prozess prüfen, nicht nur `docker compose ps`.

