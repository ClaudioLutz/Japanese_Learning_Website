---
name: improve-jpl
description: Verbessert die Japanese Learning Website (japanese-learning.ch). Auto-aktivieren, wenn Claudio Feature-Ideen zur Seite diskutiert, "was soll ich als nächstes machen" fragt, UI/UX-Reviews wünscht, Bugs auf der Website meldet, Prioritätsfragen stellt oder über den Payrexx-Go-Live spricht. Kennt Vision, Zielgruppe, Alleinstellungsmerkmale, den realen Ist-Zustand des Codes (inkl. technischer Schulden und Zeilenzahlen), aktuelle offene Themen sowie Entscheidungsheuristiken für Verbesserungen.
---

# improve-jpl — Die Japanese Learning Website besser machen

Dieser Skill ist das Produkt-Gehirn der Seite. CLAUDE.md liefert das Tech-Wissen (Stack, Deployment, DB-Sync); hier steht, *warum* es die Seite gibt, *für wen*, und *was als Nächstes* sinnvoll ist.

**Stand: 2026-04-26 (Nach SEO-Basis-Implementierung)**

## 1. Warum diese Seite existiert (Hierarchie der Zwecke)

1. **Claudio dogfoodet** — Primärer in-house Nutzer. Claudio lernt selbst Japanisch auf der Seite. Sein Lernerlebnis = wichtigstes Signal für Qualität. Vor jedem Vorschlag: "Würde Claudio das bemerken, verstehen, wiederkommen?"
2. **Mayuko ist Native-Speaker- & Pädagogik-Reviewerin** — Mayuko ist Claudios Frau und **japanische Lehrerin** (NICHT Lernerin!). Sie ist die fachliche Autorität für Korrektheit (JP-Sätze, Grammatik, natürlicher Sprachgebrauch, pädagogische Reihenfolge). Vor neuen Inhalten: "Würde Mayuko das fachlich freigeben?" Bei Zweifel: Mayuko zeigen, bevor live.
3. **Öffentliches Produkt** — Die Seite soll für deutschsprachige Anfänger eine echte Alternative zu Duolingo/WaniKani/Bunpro werden.

Reihenfolge zählt: Wenn eine Idee (3) dient aber (1) nicht, zurückstellen. Wenn (1) gefällt aber (2) sagt "fachlich falsch", zurück zum Reissbrett.

## 1.5 Leitprinzip — Inhalt nach JLPT (Mayuko-Direktive 2026-04-25)

Mayuko (Lehrerin) hat als pädagogische Anweisung gegeben: **„Lektionen nach JLPT machen."** Drei verbindliche harte Regeln:

1. **N5 zuerst komplett, bevor N4 begonnen wird.** Keine N4-Lektionen, solange N5 nicht 100 % abgedeckt. Stand 2026-04-25: N5-Coverage **7.5 % Vokabeln (53/710), 2.5 % Kanji (2/80)** — viel zu tun.
2. **Offizielle JLPT-Wortlisten als Quelle**, nicht Minna no Nihongo. Canonical-Liste liegt in `.claude/skills/generate-lesson/sources/jlpt_n5_canonical.json` (718 Vokabeln + 80 Kanji, MIT-lizenziert von elzup/AnchorI, von Tanos abgeleitet — keine offizielle Liste seit JLPT-Reform 2010).
3. **Strenger Niveau-Mix-Verbot.** Eine N5-Lektion enthält **null** N4+-Wörter. Validator (`pipeline.py validate`) bricht mit ERROR (nicht Warning) ab. Escape-Hatches: `data.is_proper_noun=true`, `data.is_canonical_override=true`.

**Konsequenzen:**
- Inhalts-Roadmap: Erst N5 sättigen, dann N4. Coverage-Dashboard als Steuerung: `python .claude/skills/generate-lesson/pipeline.py coverage 5 --show-missing 30`
- Marketing-Anker: "N5 Komplett" als verkaufbares Produkt (CHF 14.90 Empfehlung).

**Memory:** [project_jlpt_leitprinzip.md](project_jlpt_leitprinzip.md)

## 2. Das Produktversprechen

**Zielgruppe:** Absolute und frühe Anfänger — Hiragana/Katakana → erste Kanji → Grundvokabular → erste Dialoge. **Aktuell durchgängig Deutsch** (Mayuko-Direktive: erst DE komplett, dann erweitern). Englisch-Inhalte existieren in der DB, sind per `CONTENT_LANGUAGES`-Env-Variable ausgeblendet — Reaktivierung jederzeit möglich (siehe Memory `project_content_languages_filter.md`).

**Was anders ist als Duolingo/WaniKani/Bunpro/Anki:**
- KI-generierte Lektionen, Stimmen (Google TTS) und Konversationen mit Bildern (DALL-E)
- Deck-Karussell-Kartenlernsystem (DB-basiert, gerätübergreifend, eine Karte nach der anderen)
- SRS (Spaced Repetition) mit FSRS-Stufen + XP-Gamification
- **JLPT-Lernpfad als Startseite** — vertikal strukturiert in 3 Gruppen (Schreibsystem / Grundwortschatz / Erste Sätze), 8 N5-Module mit DAG-Voraussetzungen, Pulsation auf nächstem unlocked Modul
- Deutschsprachige Anfänger-Zielgruppe als klare Nische

**Nicht-Ziele:**
- Kein `fill_in_the_blank` (siehe CLAUDE.md — `multiple_choice` / `true_false` / `matching` only)
- Keine JLPT-N2/N1-Features, solange N5 nicht ≥80 % gedeckt
- Keine neuen Frameworks/Abstraktionen "auf Vorrat"
- Keine Features, die nur für Claudio Sinn ergeben, aber nicht für einen fremden deutschsprachigen Anfänger
- Keine Inhalte, die Mayuko (japanische Lehrerin) als fachlich falsch markieren würde

## 3. Aktuell offene Themen (Stand 2026-04-25)

**Payrexx-KYC läuft** (eingereicht 2026-04-25, Antwort in 1-2 Werktagen). Während Wartezeit:

1. **N5-Inhalte produzieren** — wichtigster Hebel. Coverage 7.5 %. Pro Generierungs-Sprint Coverage-Dashboard checken, dann gezielt fehlende Vokabeln/Kanji als Themen wählen. Validator ist streng (Niveau-Mix-Verbot), Escape-Hatches dokumentiert.
2. **Mayuko Vor-Live-Review** — bevor Lektionen veröffentlicht werden, sollte Mayuko sie durchsehen. Workflow noch nicht etabliert. Pragmatisch: Lesson-URL teilen, Feedback einarbeiten, dann `is_published=True`.
3. **Bestehende Lessons den Modulen feiner zuordnen** — 12 Lessons sind grob gemappt (Skript `scripts/assign_lessons_to_modules.py`), aber `order_in_module` könnte feingetunt werden (Hiragana-Lektion vor erster Vokabel-Lektion).
4. **Hiragana / Katakana / Erste-Sätze-Module sind noch leer** — diese drei Module zeigen "Inhalte in Vorbereitung" auf der Startseite. Höchste Priorität für nächste Generierungen.
5. **Nach Payrexx-KYC-Freigabe:** Live-Konfig durchziehen (Schritt 5 aus Memory `project_payrexx_kyc_wiedereinreichung.md`) — Secrets anlegen, `PAYMENT_PROVIDER=payrexx` setzen, Webhook-URL bei Payrexx eintragen (`/api/payment/webhook/payrexx`).

**Mittelfristige offene Themen** (nicht akut):
- **Pre-Login-Onboarding-Funnel** — Duolingo-Stil "Wo stehst du? / Tagesziel" vor Sign-Up. Gilt als Conversion-Hebel, aber erst sinnvoll wenn N5 substantiell gefüllt.
- **Pro-User-Sprach-Setting** statt globalem `CONTENT_LANGUAGES` — wenn DE+EN parallel angeboten werden sollen.
- **N5-Grammar-Liste** noch nicht maschinell importiert (`canonical.grammar` ist leer). Coverage-Dashboard zeigt deshalb keine Grammar-%.
- **Region-Konsolidierung** Cloud Run nach `europe-west6` (eliminiert 76s-Cold-Start) — nach Payrexx-Live als Performance-Initiative.

## 3.6 SEO — Basis ist live, Search Console wartet auf Claudio (2026-04-26)

Erste Google-Sichtbarkeit ist wichtig, weil organischer Traffic der einzige nicht-bezahlte Akquisitions-Kanal ist und vor Payrexx-Live Aufmerksamkeit aufbauen kann.

**Bereits implementiert (2026-04-26):**
- `app/templates/base.html` — `<meta name="description">`, `robots`, `canonical`, OpenGraph, Twitter Card, JSON-LD `EducationalOrganization` + `WebSite` mit SearchAction. Jinja-Blocks `meta_description`, `og_image`, `og_type`, `structured_data` pro-Seite überschreibbar.
- `app/seo_routes.py` — eigenes Blueprint mit `/robots.txt` (Admin/API/Auth/SRS/Payment ausgeschlossen) und `/sitemap.xml` (dynamisch aus Lesson + Course + statisch).
- `lesson_view.html` — `Course`-JSON-LD pro Lektion mit `educationalLevel: "JLPT N5"`.
- Pro-Seite Meta-Descriptions: index, lessons, lesson_view, courses, course_view, learn_path.
- Env-Schalter: `SITE_URL`, `ROBOTS_INDEX` (Staging→`noindex,nofollow`), `GOOGLE_SITE_VERIFICATION` (Fallback ohne DNS-Zugriff), `SEO_DEFAULT_OG_IMAGE`.

**Was Claudio noch tun muss (manuell, einmalig):**
1. **Search Console verifizieren** — Property `japanese-learning.ch` (Domain), TXT-Record bei Hostpoint setzen. Detaillierte Schritte stehen in `CLAUDE.md` unter „SEO & Google Search Console".
2. **Sitemap einreichen** — `https://japanese-learning.ch/sitemap.xml` in Search Console.
3. **OG-Image hochladen** — derzeit nur Favicon als Fallback. Empfehlung: 1200×630 PNG mit Hero-Visual nach GCS, dann `SEO_DEFAULT_OG_IMAGE` in Cloud Run setzen. Wirkt in Social-Shares (LinkedIn/Twitter/WhatsApp).
4. **PageSpeed-Check** — https://pagespeed.web.dev/?url=https://japanese-learning.ch — falls Core Web Vitals rot, vorher Cold-Start-Region-Konsolidierung (`europe-west6`) erwägen.

**Was SEO langfristig bremst:**
- N5-Coverage 7.5 % heisst wenig öffentlicher Content für Google. Jede neue Lesson = neue indexierbare URL = mehr Long-Tail-Treffer ("hiragana lernen", "japanisch zahlen 1-10"). **Inhalte produzieren ist auch SEO-Hebel #1.**
- Lessons-Detailseite zeigt für Gäste nur Marketing-Snippet, Hauptcontent hinter Login/Paywall → niedrige Indexierungs-Tiefe. Bei sehr beliebten Themen (Hiragana-Tabelle) ggf. Teil-Inhalt für Crawler erlauben.
- Keine Blog-/Artikel-Sektion → keine breiten Keyword-Themen. Erst bauen, wenn N5 ≥80 %.

## 3.5 Erledigte Live-Blocker (für Vollständigkeit, 2026-04-23 → 26)

Diese Punkte waren in §3 — sind erledigt:

- ✅ **Container-Uptime** — `--min-instances=1` in Production aktiv (Revision 00023+, 2026-04-25). Cold-Start-Problem gemildert. Hintergrund: `project_cold_start_76_sekunden.md`.
- ✅ **"Prototype" aus Title** — `<title>` ist jetzt `Japanisch lernen · Japanese Learning`.
- ✅ **Sprach-Konsistenz Homepage** — index.html komplett neu gebaut, durchgehend Deutsch (`CONTENT_LANGUAGES=['german']`). Hero, Pfad, Top-Nav alles DE.
- ✅ **Top-Nav v2** — Linear/Notion/Stripe-Pattern: schlanke transparente Bar mit Backdrop-Blur, Active-State, User-Dropdown. Komplett neue `topnav-*` CSS-Klassen in `base.html`. Alte `enhanced-navbar-*` in `custom.css` ungenutzt (kann später aufgeräumt werden).
- ✅ **Umlaute systemisch** — User.level_title liefert "Anfänger"/"Schüler" mit korrekten Umlauten, Tests entsprechend gefixt.
- ✅ **Favicon** — SVG (⛩) und PNG-Fallback in `app/static/`.
- ✅ **Legal-Pages** — `/legal/{impressum,agb,datenschutz,widerruf}` live mit echten Daten (Promenadenstrasse 72, 9400 Rorschach, info@japanese-learning.ch).
- ✅ **info@-Mailbox** — Hostpoint Cloud Office Limited (gratis), Forward auf Gmail. Setup in `reference_hostpoint_info_mailbox.md`.
- ✅ **Payrexx-KYC eingereicht** — 2026-04-25, Antwort erwartet bis ~2026-04-29.
- ✅ **SEO-Basis** — robots.txt, sitemap.xml, Meta-/OG-/JSON-LD-Tags in `base.html`, pro-Seite Descriptions. Search-Console-Verifikation (Hostpoint TXT) noch von Claudio einmalig manuell zu erledigen.

## 4. Leitplanken für "Bestehendes verbessern" (der Dauermodus)

**Grosse Dateien sind Warnsignale (Stand 2026-04-25):**
- `app/routes.py` → **4'207 Zeilen** (+101 seit letzter Aktualisierung). Gott-Datei. Wenn Patch hier > 30 Zeilen wird, in Blueprint/Service-Modul abspalten.
- `app/templates/lesson_view.html` → **3'721 Zeilen**. Wo Claudio tatsächlich lernt. Grössere Additionen in Partials.
- `app/templates/lessons.html` → 845 Zeilen. Beobachten.
- `app/templates/base.html` → ca. 600 Zeilen (gewachsen wegen Top-Nav v2 inline-CSS). Inline-CSS könnte in `custom.css` ausgelagert werden.
- `app/templates/index.html` → 557 Zeilen. Komplett neu seit 2026-04-25 (JLPT-Pfad als Startseite).
- `app/models.py` → 925 Zeilen. Akzeptabel.

**Architektur-Patterns die erhalten bleiben müssen:**

- **Lernpfad als Startseite**: `routes.index()` rendert Hero + N5-Pfad-Module. Logik für `next_module_id` (erstes unlocked + nicht complete + has lessons), Auto-Scroll, Pulsation. NIE durch generischen "Lessons"-Browser ersetzen.
- **LessonCategory = Modul-Container**: Felder `slug`, `jlpt_level`, `display_order`, `icon_emoji`, `prerequisite_category_id`. Methods `completion_for_user(user, languages)`, `is_unlocked_for_user(user)`. DAG via prerequisite, ≥80 %-Schwelle für unlock.
- **CONTENT_LANGUAGES Filter**: `app.config['CONTENT_LANGUAGES']` (default `['german']`). Alle Lesson-Listings filtern. Wenn jemand die englischen Lessons sehen will: Env setzen.
- **Top-Nav v2 Klassen** (`topnav-*`): nicht mit alten `enhanced-navbar-*` mischen.
- **Snake-Path-Rendering** im Pfad: 3 Gruppen mit Section-Headers, Karten in `repeat(auto-fill, minmax(280px, 1fr))`, Pulsation per `is-next`-Klasse, Lock-Icon bei `is-locked`.

**Testabdeckung:**
- `pyproject.toml` `fail_under = 35`. Aktuell **388 Tests grün**. CLAUDE.md-Regel: Coverage nicht senken.
- 8 Playwright-Specs in `tests/` weiterhin **verwaist** (kein CI). Browser-Tests via Playwright MCP ad-hoc.

**CSS-Falle im Deck-Karussell** (unverändert kritisch):
- Regel in `app/static/css/custom.css:1960`: `.content-item.in-deck { display: none !important; }`. Ein CSS-Syntaxfehler bricht das Parsing → alle Karten gleichzeitig sichtbar.
- Nach jeder `custom.css`-Änderung: Browser-Konsole + visuelle Bestätigung (eine Karte sichtbar).

**Dialog-Slideshow CSS-Grid-Stacking** (siehe `generate-lesson/SKILL.md §4c TEMPLATE-FALLE`):
- Stage-Container muss `display:grid`, jede Slide `style="grid-area:1/1;"` haben — sonst doppeltes Bild beim Slide-Wechsel.

**DB-Sync-Reihenfolge:**
- IMMER Cloud→Lokal vor Lokal→Cloud. Admin (Claudio bzw. Mayuko-Review) editiert live. Blindes Push überschreibt Produktionsänderungen.

## 5. Woran "besser" gemessen wird

Kein A/B-Testing und keine Analytics-Obsession. Die Signale:

- **Claudio kommt ohne Aufforderung wieder** und merkt echten Lernfortschritt (Retention ≠ Klickspass). Wichtigster Indikator.
- **Mayuko's fachliches Urteil** — sie würde den Inhalt einer Schülerin guten Gewissens empfehlen.
- **JLPT-N5-Coverage** (objektive Metrik): `pipeline.py coverage 5` — ZIEL: 100 %. Stand 2026-04-25: 7.5 % Vokabeln, 2.5 % Kanji.
- **Erster fremder Nutzer** registriert sich und loggt am Folgetag wieder ein.
- **Payrexx KYC durch** → erste echte CHF-Zahlung möglich. (Eingereicht 2026-04-25.)
- **Hygiene:** `git status` sauber, alle Tests grün, Inkognito-Startseite fehlerfrei.

## 6. Entscheidungsheuristik (wie dieser Skill im Dialog hilft)

| Claudio fragt / sagt | Reaktion |
|----------------------|----------|
| "Was soll ich als nächstes machen?" | §3 in Reihenfolge. **Wahrscheinlichste Antwort 2026-04: N5-Inhalte produzieren** (Hiragana-Modul ist leer, Coverage 7.5 %). |
| "Welches Thema generieren?" | Erst `coverage 5 --show-missing 30` laufen lassen, dann ein Thema mit vielen fehlenden Vokabeln wählen. NIE Bauch-Themen, NIE Wiederholung schon gedeckter Wörter. |
| "Ich hätte eine Idee: [Feature X]" | Vier Fragen: (a) Verbessert das Bestehendes oder baut Neues? (b) Würde Claudio (oder ein fremder Anfänger) es bemerken/nutzen? (c) Wenn JP-Inhalt: würde Mayuko es freigeben? (d) Hilft es, N5 schneller auf 100 % zu bringen oder ist es Ablenkung davon? |
| "Kannst du die UI reviewen?" | Auf Sprach-Konsistenz (CONTENT_LANGUAGES respektiert?), Mobile-Breakpoints (Top-Nav unter 992px, Pfad-Karten 1-Spalter unter 575px), Active-State der Top-Nav, Umlaut-Korrektheit, Pulsation auf nächstem Modul achten. |
| "Es gibt einen Bug" | In dieser Reihenfolge ausschliessen: (1) Deck-Karussell-CSS, (2) Dialog-Slideshow Grid-Stacking, (3) DB-Sync-Reihenfolge, (4) Cloud-Run-Cold-Start, (5) Umlaut/Charset, (6) routes.py-Monolith. |
| "Sollen wir das refactoren?" | Nur wenn der Ort sowieso gerade berührt wird. Kandidaten: routes.py (Lernpfad-Logik in eigenes Modul), base.html (Top-Nav-CSS in custom.css), alte `enhanced-navbar-*` Klassen löschen. |
| "SEO / Google-Sichtbarkeit?" | Basis ist live (siehe §3.6). Nächste Schritte: Claudio muss Search Console mit Hostpoint-TXT verifizieren (Anleitung in CLAUDE.md), dann Sitemap submitten. Inhalte produzieren ist Hebel #1, weil mehr Lessons = mehr indexierbare URLs. Bei neuen public Routes: in `seo_routes.py::sitemap_xml()` `static_pages` ergänzen. |
| "Wie bekomme ich den ersten Nutzer?" | Erst Payrexx-Freigabe abwarten. Dann: Onboarding als Fremder durchspielen (Inkognito), Reibung dokumentieren, ein konkretes Premium-Produkt sichtbar machen ("N5 Komplett" CHF 14.90 — sobald 100 % Coverage). |
| "Englisch wieder anschalten?" | `CONTENT_LANGUAGES=german,english` Env-Var setzen (lokal `.env`, prod via `gcloud run services update --update-env-vars`). Memory `project_content_languages_filter.md`. |
| "Neue Module / JLPT-Level?" | LessonCategory mit `jlpt_level`, `slug`, `display_order` anlegen. Optional `prerequisite_category_id`. Lessons via `category_id` zuordnen. Route `/learn/n4` funktioniert automatisch. |

## 7. Verweise (Wissen, das nicht hier dupliziert wird)

- **Tech-Stack, Deployment, DB-Sync, Migrationen, Cloud SQL** → `CLAUDE.md`
- **Lesson-Generierung (Pipeline, Validator, Coverage)** → `generate-lesson` Skill + `learnings.md`
- **JLPT-Leitprinzip mit harten Regeln** → User-Memory `project_jlpt_leitprinzip.md`
- **Mayuko ist Lehrerin, nicht Lernerin** → User-Memory `user_mayuko_japanisch_lehrerin.md`
- **Payrexx-KYC-Wiedereinreichung 2026-04-25** → `project_payrexx_kyc_wiedereinreichung.md`
- **CONTENT_LANGUAGES-Filter Setup** → `project_content_languages_filter.md`
- **Cloud-Run-Cold-Start-Hintergrund** → `project_cold_start_76_sekunden.md`
- **Hostpoint info@-Mailbox** → `reference_hostpoint_info_mailbox.md`
- **Hostpoint Domain-Registrar** → `reference_hostpoint_domain.md`
- **Cloud-DB-Sync-Reihenfolge** → `feedback_cloud_db_sync_reihenfolge.md`
- **Private Daten (Mayuko, Verträge, Finanzen)** → `knowledge-base` Skill
- **Produktions-SQL-Abfragen** → `cloud-db` Skill
- **Cloud↔Lokal-Synchronisation** → `sync-cloud-db` Skill
- **Projekt-Status-Überblick** → `status` Skill
- **Payrexx-Freischaltungs-Thread** → Gmail, Account `lutz86`, Thread-ID `19db8ef12c10a585`
