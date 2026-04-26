---
name: improve-jpl
description: Verbessert die Japanese Learning Website (japanese-learning.ch). Auto-aktivieren, wenn Claudio Feature-Ideen zur Seite diskutiert, "was soll ich als nächstes machen" fragt, UI/UX-Reviews wünscht, Bugs auf der Website meldet, Prioritätsfragen stellt oder über den Payrexx-Go-Live spricht. Kennt Vision, Zielgruppe, Alleinstellungsmerkmale, den realen Ist-Zustand des Codes (inkl. technischer Schulden und Zeilenzahlen), aktuelle offene Themen sowie Entscheidungsheuristiken für Verbesserungen.
---

# improve-jpl — Die Japanese Learning Website besser machen

Dieser Skill ist das Produkt-Gehirn der Seite. CLAUDE.md liefert das Tech-Wissen (Stack, Deployment, DB-Sync); hier steht, *warum* es die Seite gibt, *für wen*, und *was als Nächstes* sinnvoll ist.

**Stand: 2026-04-26 (SEO-Setup komplett: Search Console verifiziert, Sitemap eingereicht, OG-Image live, www-Mapping konfiguriert)**

## 1. Warum diese Seite existiert (Hierarchie der Zwecke)

1. **Claudio dogfoodet** — Primärer in-house Nutzer. Claudio lernt selbst Japanisch auf der Seite. Sein Lernerlebnis = wichtigstes Signal für Qualität. Vor jedem Vorschlag: "Würde Claudio das bemerken, verstehen, wiederkommen?"
2. **Mayuko ist Native-Speaker- & Pädagogik-Reviewerin** — Mayuko ist Claudios Frau und **japanische Lehrerin** (NICHT Lernerin!). Sie ist die fachliche Autorität für Korrektheit (JP-Sätze, Grammatik, natürlicher Sprachgebrauch, pädagogische Reihenfolge). Vor neuen Inhalten: "Würde Mayuko das fachlich freigeben?" Bei Zweifel: Mayuko zeigen, bevor live.
3. **Öffentliches Produkt** — Die Seite soll für deutschsprachige Anfänger eine echte Alternative zu Duolingo/WaniKani/Bunpro werden.

Reihenfolge zählt: Wenn eine Idee (3) dient aber (1) nicht, zurückstellen. Wenn (1) gefällt aber (2) sagt "fachlich falsch", zurück zum Reissbrett.

## 1.5 Leitprinzip — Inhalt nach JLPT (Mayuko-Direktive 2026-04-25)

Mayuko (Lehrerin) hat als pädagogische Anweisung gegeben: **„Lektionen nach JLPT machen."** Drei verbindliche harte Regeln:

1. **N5 zuerst komplett, bevor N4 begonnen wird.** Keine N4-Lektionen, solange N5 nicht 100 % abgedeckt. Stand 2026-04-26: N5-Coverage **33.0 % Vokabeln (234/710), 2.5 % Kanji (2/80)** — Vokabel-Drittel da, Kanji ist der Engpass.
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

1. **N5-Inhalte produzieren** — wichtigster Hebel. Vokabel-Coverage 33 %, Kanji-Coverage nur 2.5 %. Kanji-Themen priorisieren. Pro Generierungs-Sprint Coverage-Dashboard checken, dann gezielt fehlende Vokabeln/Kanji als Themen wählen. Validator ist streng (Niveau-Mix-Verbot), Escape-Hatches dokumentiert.
2. **Mayuko Vor-Live-Review** — bevor Lektionen veröffentlicht werden, sollte Mayuko sie durchsehen. Workflow noch nicht etabliert. Pragmatisch: Lesson-URL teilen, Feedback einarbeiten, dann `is_published=True`.
3. **Bestehende Lessons den Modulen feiner zuordnen** — 12 Lessons sind grob gemappt (Skript `scripts/assign_lessons_to_modules.py`), aber `order_in_module` könnte feingetunt werden (Hiragana-Lektion vor erster Vokabel-Lektion).
4. **Hiragana / Katakana / Erste-Sätze-Module sind noch leer** — diese drei Module zeigen "Inhalte in Vorbereitung" auf der Startseite. Höchste Priorität für nächste Generierungen.
5. **Nach Payrexx-KYC-Freigabe:** Live-Konfig durchziehen (Schritt 5 aus Memory `project_payrexx_kyc_wiedereinreichung.md`) — Secrets anlegen, `PAYMENT_PROVIDER=payrexx` setzen, Webhook-URL bei Payrexx eintragen (`/api/payment/webhook/payrexx`).

**Mittelfristige offene Themen** (nicht akut):
- **Pre-Login-Onboarding-Funnel** — Duolingo-Stil "Wo stehst du? / Tagesziel" vor Sign-Up. Gilt als Conversion-Hebel, aber erst sinnvoll wenn N5 substantiell gefüllt.
- **Pro-User-Sprach-Setting** statt globalem `CONTENT_LANGUAGES` — wenn DE+EN parallel angeboten werden sollen.
- **N5-Grammar-Liste** noch nicht maschinell importiert (`canonical.grammar` ist leer). Coverage-Dashboard zeigt deshalb keine Grammar-%.
- **Region-Konsolidierung** Cloud Run nach `europe-west6` (eliminiert 76s-Cold-Start) — nach Payrexx-Live als Performance-Initiative.

## 3.6 SEO — Setup komplett, jetzt liefert Content den Hebel (2026-04-26)

Organischer Traffic ist der einzige nicht-bezahlte Akquisitions-Kanal. Vor Payrexx-Live wichtig, um Aufmerksamkeit aufzubauen.

**Komplett erledigt (2026-04-26):**
- ✅ **Code**: `app/templates/base.html` mit Meta-Description, Canonical, Robots, OpenGraph, Twitter Card, JSON-LD (`EducationalOrganization` + `WebSite` mit SearchAction). Pro-Seite überschreibbar via Jinja-Blocks.
- ✅ **`app/seo_routes.py`**: eigenes Blueprint mit `/robots.txt` (Admin/API/Auth/SRS/Payment ausgeschlossen) und `/sitemap.xml` (dynamisch aus Lesson + Course + statisch, aktuell 34 URLs).
- ✅ **`lesson_view.html`**: `Course`-JSON-LD pro Lektion mit `educationalLevel: "JLPT N5"`.
- ✅ **Pro-Seite Meta-Descriptions**: index, lessons, lesson_view, courses, course_view, learn_path.
- ✅ **Search Console verifiziert**: Domain-Property `japanese-learning.ch` aktiv (TXT bei Hostpoint), 3 Seiten initial indexiert.
- ✅ **Sitemap eingereicht**: `https://japanese-learning.ch/sitemap.xml` in Search Console, 34 URLs erkannt.
- ✅ **OG-Image live**: 1200×630 PNG (`scripts/generate_og_image.py`, Pillow-generiert mit Indigo-Verlauf + 日本語 + URL-Pill) in `gs://jpl-website-assets/og-image.png`. `SEO_DEFAULT_OG_IMAGE` Env-Var in Cloud Run gesetzt (Revision 00029+).
- ✅ **www-Subdomain**: Cloud-Run-Mapping `www.japanese-learning.ch` angelegt, Hostpoint-CNAME `www → ghs.googlehosted.com.` gesetzt. SSL-Zertifikat wird von Google automatisch provisioniert (10–60 min nach DNS-Propagation).
- ✅ **Env-Schalter**: `SITE_URL`, `ROBOTS_INDEX` (Staging→`noindex,nofollow`), `GOOGLE_SITE_VERIFICATION` (Fallback ohne DNS-Zugriff), `SEO_DEFAULT_OG_IMAGE`.

**Wo der Hebel jetzt liegt:**
- **Content**: N5-Vokabel-Coverage 33 % (Kanji 2.5 %) heisst noch wenig öffentlicher Content für Google. Jede neue Lesson = neue indexierbare URL = mehr Long-Tail-Treffer ("hiragana lernen", "japanisch zahlen 1-10"). **Inhalte produzieren ist SEO-Hebel #1.** Sitemap regeneriert sich automatisch (DB-getrieben).
- Lessons-Detailseite zeigt für Gäste nur Marketing-Snippet, Hauptcontent hinter Login/Paywall → niedrige Indexierungs-Tiefe. Bei sehr beliebten Themen (Hiragana-Tabelle) ggf. Teil-Inhalt für Crawler erlauben.
- Keine Blog-/Artikel-Sektion → keine breiten Keyword-Themen. Erst bauen, wenn N5 ≥80 %.

**Monitoring (passiv):**
- Search Console „Leistung": erste Klicks/Impressionen nach 2-4 Wochen.
- Search Console „Seiten": indexierte URLs sollten von 3 → 34 wachsen, Schwellwert ~7 Tage.
- PageSpeed-Check vor grösseren Marketing-Aktionen: https://pagespeed.web.dev/?url=https://japanese-learning.ch
- Social-Share-Vorschau: https://www.opengraph.xyz/url/https%3A%2F%2Fjapanese-learning.ch

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
- ✅ **SEO-Setup komplett (2026-04-26)** — robots.txt, sitemap.xml (34 URLs), Meta-/OG-/JSON-LD-Tags, Search Console verifiziert (Domain-Property `japanese-learning.ch`), Sitemap eingereicht, OG-Image (1200×630 in GCS) live, `SEO_DEFAULT_OG_IMAGE` Env-Var gesetzt. Details in §3.6.
- ✅ **www-Subdomain** — Cloud-Run-Mapping + Hostpoint CNAME `www → ghs.googlehosted.com.` gesetzt 2026-04-26. SSL-Zertifikat von Google in 10-60 min auto-provisioniert.

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
- **JLPT-N5-Coverage** (objektive Metrik): `pipeline.py coverage 5` — ZIEL: 100 %. Stand 2026-04-26: 33.0 % Vokabeln (234/710), 2.5 % Kanji (2/80).
- **Erster fremder Nutzer** registriert sich und loggt am Folgetag wieder ein.
- **Payrexx KYC durch** → erste echte CHF-Zahlung möglich. (Eingereicht 2026-04-25.)
- **Hygiene:** `git status` sauber, alle Tests grün, Inkognito-Startseite fehlerfrei.

## 6. Entscheidungsheuristik (wie dieser Skill im Dialog hilft)

| Claudio fragt / sagt | Reaktion |
|----------------------|----------|
| "Was soll ich als nächstes machen?" | §3 in Reihenfolge. **Wahrscheinlichste Antwort 2026-04: N5-Inhalte produzieren** — Vokabel-Coverage bei 33 %, Kanji aber erst 2.5 % (Engpass), Hiragana-Modul noch leer. |
| "Welches Thema generieren?" | Erst `coverage 5 --show-missing 30` laufen lassen, dann ein Thema mit vielen fehlenden Vokabeln wählen. NIE Bauch-Themen, NIE Wiederholung schon gedeckter Wörter. |
| "Ich hätte eine Idee: [Feature X]" | Vier Fragen: (a) Verbessert das Bestehendes oder baut Neues? (b) Würde Claudio (oder ein fremder Anfänger) es bemerken/nutzen? (c) Wenn JP-Inhalt: würde Mayuko es freigeben? (d) Hilft es, N5 schneller auf 100 % zu bringen oder ist es Ablenkung davon? |
| "Kannst du die UI reviewen?" | Auf Sprach-Konsistenz (CONTENT_LANGUAGES respektiert?), Mobile-Breakpoints (Top-Nav unter 992px, Pfad-Karten 1-Spalter unter 575px), Active-State der Top-Nav, Umlaut-Korrektheit, Pulsation auf nächstem Modul achten. |
| "Es gibt einen Bug" | In dieser Reihenfolge ausschliessen: (1) Deck-Karussell-CSS, (2) Dialog-Slideshow Grid-Stacking, (3) DB-Sync-Reihenfolge, (4) Cloud-Run-Cold-Start, (5) Umlaut/Charset, (6) routes.py-Monolith. |
| "Sollen wir das refactoren?" | Nur wenn der Ort sowieso gerade berührt wird. Kandidaten: routes.py (Lernpfad-Logik in eigenes Modul), base.html (Top-Nav-CSS in custom.css), alte `enhanced-navbar-*` Klassen löschen. |
| "SEO / Google-Sichtbarkeit?" | Setup komplett (§3.6): Search Console verifiziert, Sitemap eingereicht (34 URLs), OG-Image live, www-Subdomain konfiguriert. **Hebel #1 jetzt: N5-Content produzieren** — jede neue Lesson = neue indexierbare URL. Sitemap regeneriert sich automatisch DB-getrieben. Bei neuen public Routes: in `seo_routes.py::sitemap_xml()` `static_pages` ergänzen. |
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
