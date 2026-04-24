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

