---
name: improve-jpl
description: Verbessert die Japanese Learning Website (japanese-learning.ch). Auto-aktivieren, wenn Claudio Feature-Ideen zur Seite diskutiert, "was soll ich als nächstes machen" fragt, UI/UX-Reviews wünscht, Bugs auf der Website meldet, Prioritätsfragen stellt oder über den Payrexx-Go-Live spricht. Kennt Vision, Zielgruppe, Alleinstellungsmerkmale, den realen Ist-Zustand des Codes (inkl. technischer Schulden und Zeilenzahlen), aktuelle offene Themen sowie Entscheidungsheuristiken für Verbesserungen.
---

# improve-jpl — Die Japanese Learning Website besser machen

Dieser Skill ist das Produkt-Gehirn der Seite. CLAUDE.md liefert das Tech-Wissen (Stack, Deployment, DB-Sync); hier steht, *warum* es die Seite gibt, *für wen*, und *was als Nächstes* sinnvoll ist.

**Stand: 2026-04-26 abends — Monetarisierungs-Funnel komplett deployed (Revision 00034-ptk + DB-Sync). Bundle CHF 9.90 / Single CHF 5 / 1 Lesson pro Modul gratis. Paywall-Conversion-Seite + Modul-Detail-Seiten + Brand-Refresh (Torii + Fraunces). Wartet nur noch auf Payrexx-KYC fuer echte Zahlungen.**

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

## 3. Aktuell offene Themen (Stand 2026-04-26 abends)

**Payrexx-KYC läuft** (eingereicht 2026-04-25, Antwort ~2026-04-29). Während Wartezeit:

1. **Payrexx-Live-Konfig** (sobald KYC durch ist) — `PAYMENT_PROVIDER=mock` aktuell, akzeptiert Mock-Käufe. Sobald KYC OK: GCP Secrets + `PAYMENT_PROVIDER=payrexx` + Webhook bei Payrexx eintragen. **Konkrete gcloud-Kommandos** in Memory `project_payrexx_kyc_wiedereinreichung.md` Schritt 5+6.
2. **AGB juristisch prüfen lassen** vor erstem echten Kauf (~CHF 100-200 bei gryps.ch / lawbster.ch). §5b Pre-Order-Klausel ist neu, der Rest ist Vorlage.
3. **N5-Inhalte produzieren** — Vokabel-Coverage 33 %, Kanji-Coverage 2.5 % (Engpass). **Kanji-Themen priorisieren.** Pro Generierungs-Sprint: Coverage-Dashboard checken (`pipeline.py coverage 5`), dann gezielt fehlende Vokabeln/Kanji wählen. **Nach jeder neuen Lesson:** `python scripts/setup_n5_bundle.py` + `python scripts/apply_n5_pricing_duolingo.py` ausführen, dann `/sync-cloud-db`.
4. **Mayuko Vor-Live-Review** — Workflow noch nicht etabliert. Pragmatisch: Lesson-URL teilen, Feedback einarbeiten, dann `is_published=True`.
5. **Erste 5 Tester einladen** (Freunde, Mayukos Schülerinnen) — gratis Konto + Bundle-Code als Geschenk → Feedback einarbeiten, bevor öffentlich beworben wird.

**Mittelfristige offene Themen** (nicht akut):
- **Pre-Login-Onboarding-Funnel** — Duolingo-Stil "Wo stehst du? / Tagesziel" vor Sign-Up. Erst sinnvoll wenn N5 ≥ 60 % Coverage.
- **Soft-Paywall nach Aha-Moment** — Banner auf `/lessons/<id>` für nicht-zahlende User mit ≥ 5 abgeschlossenen Lessons (geplante Phase 3 des Funnels). Aktuell zeigt Bundle-Hint-Banner über Lernpfad.
- **Pro-User-Sprach-Setting** statt globalem `CONTENT_LANGUAGES`.
- **N5-Grammar-Liste** noch nicht maschinell importiert.
- **Region-Konsolidierung** Cloud Run nach `europe-west6`.
- **Daten-Bereinigung Vocabulary.romaji** — 13 Vokabeln haben `romaji=None` (z.B. „駅" mit reading=„えき (eki)" statt sauberem Format). Klein, aber Conversion-relevant für Sub-Text-Anzeige.

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

## 3.4 Monetarisierungs-Funnel komplett (Code+DB live, 2026-04-26 abends)

**Verkaufsseite + Paywall + Bundle-Architektur:**
- ✅ **Bundle = Course (Course-ID 7 „JLPT N5 Komplett"):** kein neues Modell, reuset CoursePurchase + Webhook ohne Änderung. Architektur in Memory `project_n5_bundle_implementation.md`.
- ✅ **`/n5-bundle`** Verkaufsseite mit Live-Coverage-Widget, Early-Access-Pill, Vergleichstabelle, FAQ, AGB-Pflicht-Checkbox, 30-Tage-Refund prominent (Quicksprout +21-26 % Conversion-Pattern).
- ✅ **`/api/bundles/n5/purchase`** Buy-API mit dynamischem Preis (CHF 9.90 → 14.90 ab Vokabel-Coverage 80 %).
- ✅ **`/learn/n5/<slug>`** Modul-Detail-Seiten (8 neue indexierbare URLs in Sitemap) — „Beginnen" führt zur Übersicht statt direktem Lesson-Sprung; bei nur 1 Lesson Auto-Redirect.
- ✅ **`lesson_paywall.html`** — Klick auf paid Lesson zeigt Conversion-Seite mit Lesson-Tease + Zwei-CTA (Bundle empfohlen + Single sekundär), kein Browser-Reset/Flash.
- ✅ **Pricing-Migration Duolingo-Style** — 1 Lesson pro Modul gratis, restliche 20 paid à CHF 5. Bundle ab 2 gewollten Single-Lessons günstiger. Konfig + Math in `project_pricing_strategie_n5.md`.
- ✅ **Prerequisites gelockert** — alle 7 Module ohne Vorgänger, kein Korridor mehr (Brilliant/Duolingo-Path-Pattern). `prerequisite_category_id=NULL` via `loosen_n5_prerequisites.py` (mit Backup-JSON für Restore).
- ✅ **Admin-Bypass** in `Lesson.is_accessible_to_user()` + auf Bundle-Seite — Mayuko + Claudio sehen alles frei.
- ✅ **Funnel-Touchpoints überall sichtbar:** Top-Nav-CTA-Outline mit Hover-Tooltip, Hero-Sekundärlink, Bundle-Hint-Banner über Lernpfad (nur für Nicht-Käufer/Nicht-Admins), Bottom-CTA auf Modul-Detail-Seite.
- ✅ **Brand-Refresh:** handgezeichnetes Lila-Torii (`torii-logo.svg`) + Fraunces-Wordmark + Noto Serif JP statt Unicode-Emoji + System-Font. Neuer Favicon mit gleichem Torii.
- ✅ **Review-Karten neu:** Bedeutung gross + zentriert, Lesung+Romaji leise darunter, Beispiel in eigener Section, Pill-Buttons mit Soft-Colors statt grellen Vollflächen, Romaji-Hint-Button für Kana-Karten (Spoiler-Schutz beim Lernen).
- ✅ **Romaji-Bug für Vocabulary gefixt:** SRS-API lieferte `romaji` nie aus → bei Kana-only-Wörtern (かばん) sah man `reading == word` doppelt. Jetzt: bei `word === reading` zeig Romaji als Untertext.
- ✅ **Lernpfad-Konsolidierung:** `/learn/n5` → 301 auf `/#lernpfad` (Single Source of Truth). Modul-Detail-Breadcrumb angepasst.
- ✅ **AGB §5b** „Pre-Order und Bundles im Aufbau" + 6-Monate-Stagnations-Refund-Klausel + Widerruf-Belehrung mit Pre-Order-Spezifikum.
- ✅ **DB-Sync auf Cloud (2026-04-26 abends):** 5557 Upserts, 0 Deletes, User-Daten unangetastet. 892 GCS-Assets synchron.
- ✅ **Live-Verify:** https://japanese-learning.ch/n5-bundle, /learn/n5/n5-hiragana, /lessons/148 alle 200.

**User-bestätigte Patterns** + Anti-Patterns siehe `feedback_funnel_patterns_2026_04_26.md`.

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

**Grosse Dateien sind Warnsignale (Stand 2026-04-26 abends):**
- `app/routes.py` → ca. **4'250 Zeilen** (+ module_detail-Route, paywall-render, show_bundle_hint). Gott-Datei. Wenn Patch hier > 30 Zeilen wird, in Blueprint/Service-Modul abspalten — wie es bei `bundle_routes.py`, `seo_routes.py`, `legal_routes.py` schon vorgemacht ist.
- `app/templates/lesson_view.html` → **3'721 Zeilen**. Grössere Additionen in Partials.
- `app/templates/base.html` → ca. **750 Zeilen** (gewachsen wegen Bundle-CTA-Outline-CSS, Tooltip-Pseudo-Elemente, Brand-Block mit SVG + Custom-Font-Setup). Inline-CSS könnte in `custom.css` ausgelagert werden — niedrige Priorität.
- `app/templates/index.html` → ca. **600 Zeilen** (Hero + Bundle-Hint-Banner + JLPT-Pfad).
- `app/templates/review.html` → ca. **800 Zeilen** (CSS + Card-Render + Pill-Buttons + Stats-Bar + Achievement-Toast).
- `app/templates/bundles/n5_bundle.html` → ca. **300 Zeilen**. Conversion-kritisch — vor jedem Edit kurz überlegen ob du die Conversion brichst.
- `app/templates/lesson_paywall.html` → ca. **270 Zeilen**. Conversion-kritisch (Bundle/Single-Auswahl).
- `app/templates/module_detail.html` → ca. **180 Zeilen**.
- `app/models.py` → ca. **935 Zeilen** (mit Admin-Bypass + deutschen Messages). Akzeptabel.

**Architektur-Patterns die erhalten bleiben müssen:**

- **Lernpfad als Startseite**: `routes.index()` rendert Hero + N5-Pfad-Module. Logik für `next_module_id`, Bundle-Hint-Banner, Auto-Scroll, Pulsation. NIE durch generischen "Lessons"-Browser ersetzen.
- **LessonCategory = Modul-Container**: Felder `slug`, `jlpt_level`, `display_order`, `icon_emoji`, `prerequisite_category_id`. **Stand 2026-04-26: Prerequisites alle NULL — Pfad ist Empfehlung, kein Korridor.** Falls jemand Sperren wieder will: `loosen_n5_prerequisites.py --restore` mit Backup-JSON.
- **Bundle = Course-Pattern**: kein neues Bundle-Modell. Course-ID 7 ist der einzige „is_published=False AND is_purchasable=True"-Course. Pattern in Memory `project_n5_bundle_implementation.md`.
- **`Lesson.is_accessible_to_user()` Cascade**: 1) Admin-Bypass, 2) Free-Lesson, 3) LessonPurchase, 4) **CoursePurchase (Bundle-Mechanismus)**, 5) Premium-Sub. Reihenfolge nicht ändern.
- **`view_lesson()` rendert Paywall, kein Redirect**: Bei `not accessible AND price>0 AND is_purchasable` → `lesson_paywall.html`. Bei `Login required` → Login-Redirect. Bei prerequisite-Fail → Flash + Lessons-Liste.
- **Modul-Detail mit Skip-Optimierung**: `/learn/n5/<slug>` redirected bei `len(published_lessons)<=1` direkt zur Lesson — keine Klick-Friction für Mini-Module.
- **Funnel-Hint-Suppression**: `show_bundle_hint` ist `False` für Admins UND für User mit `CoursePurchase` auf Bundle-Course. Sonst penetriert der Hint Käufer mit „Tipp: kauf das Bundle".
- **CONTENT_LANGUAGES Filter**: default `['german']`. Bilingual via Env.
- **Top-Nav v2 Klassen** (`topnav-*`): `topnav-link-cta` ist Outline-Style mit `data-cta-tooltip` Pseudo-Element. Nicht mit Vollflächen-Buttons mischen.
- **Brand-Block:** SVG-Torii (`/static/torii-logo.svg`) + Fraunces (Wordmark) + Noto Serif JP (Tag). Hover dreht Torii via cubic-bezier. CSP erlaubt `fonts.googleapis.com` + `fonts.gstatic.com`.
- **`/learn/n5` ist 301 auf `/#lernpfad`** — Single Source of Truth ist die Startseite. `/learn/n4` ist 404 (Mayuko-Direktive: erst N5).
- **Snake-Path-Rendering** im Pfad: 3 Gruppen, `repeat(auto-fill, minmax(280px, 1fr))`, `is-next` für Pulsation. Lock-Icon nur falls `prerequisite_category_id` wieder gesetzt würde.

**Testabdeckung:**
- `pyproject.toml` `fail_under = 35`. Aktuell **432 Tests grün** (388 vorher + 15 Bundle-Tests + 7 Modul-/Paywall-Tests + diverse). CLAUDE.md-Regel: Coverage nicht senken.
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
| "Was soll ich als nächstes machen?" | §3 in Reihenfolge. **Wahrscheinlichste Antwort 2026-04-26 abends: Payrexx-KYC abwarten** + parallel **N5-Inhalte (vor allem Kanji 2.5 %)** produzieren. Funnel ist live, jede neue paid Lesson erhöht Bundle-Wert. |
| "Welches Thema generieren?" | Erst `coverage 5 --show-missing 30` laufen lassen, **Kanji priorisieren** (nur 2 von 80). Nach Generierung: `setup_n5_bundle.py` + `apply_n5_pricing_duolingo.py` + `/sync-cloud-db`. |
| "Ich hätte eine Idee: [Feature X]" | Vier Fragen: (a) Verbessert das Bestehendes oder baut Neues? (b) Würde Claudio (oder ein fremder Anfänger) es bemerken/nutzen? (c) Wenn JP-Inhalt: würde Mayuko es freigeben? (d) Hilft es, N5 schneller auf 100 % zu bringen oder ist es Ablenkung davon? |
| "Wie passt der Funnel?" | Touchpoints heute: Top-Nav-CTA, Hero-Sekundärlink, Bundle-Hint-Banner über Pfad, Modul-Detail-Bottom-CTA, Lesson-Paywall. **NICHT mehr addieren ohne A/B-Daten** — Anti-Pattern „Needy Design" laut NN/g. |
| "Pricing ändern?" | Konstanten in `app/services/bundle_service.py` (`SINGLE_LESSON_PRICE_CHF`, `EARLY_BIRD_PRICE_CHF`, `REGULAR_PRICE_CHF`, `EARLY_BIRD_THRESHOLD_PCT`). Math + Strategie in `project_pricing_strategie_n5.md`. **Bundle muss ab 2 Single-Lessons günstiger sein** — sonst Anker kaputt. |
| "Kannst du die UI reviewen?" | Auf Sprach-Konsistenz (CONTENT_LANGUAGES, deutsche Access-Messages), Mobile-Breakpoints (Top-Nav unter 992px, Pfad-Karten 1-Spalter unter 575px), Active-State der Top-Nav, Umlaut-Korrektheit, Pill-Button-Style (kein grelles Vollflächen) achten. |
| "Es gibt einen Bug" | In dieser Reihenfolge ausschliessen: (1) Deck-Karussell-CSS, (2) Dialog-Slideshow Grid-Stacking, (3) DB-Sync-Reihenfolge, (4) Englische Access-Message übersehen, (5) Bundle-Course existiert in Cloud-DB?, (6) GCS-Asset-404, (7) routes.py-Monolith. |
| "Sollen wir das refactoren?" | Nur wenn der Ort sowieso gerade berührt wird. Kandidaten: routes.py (module_detail könnte in eigenes Modul), base.html (Top-Nav-CSS in custom.css), alte `enhanced-navbar-*` Klassen löschen. **`bundle_routes.py` und `module_detail.html` haben Conversion-Wert — vor Refactoring überlegen ob du die Conversion brichst.** |
| "SEO / Google-Sichtbarkeit?" | Setup komplett (§3.6): Search Console verifiziert, Sitemap (jetzt **42 URLs** mit 8 Modul-Detail-Seiten + /n5-bundle), OG-Image live, www-Subdomain konfiguriert. **Hebel #1: N5-Content produzieren.** Bei neuen public Routes: `seo_routes.py::sitemap_xml()` `static_pages` ergänzen. |
| "Wie bekomme ich den ersten Nutzer?" | Erst Payrexx-Live, dann erste 5 Tester (Freunde, Mayukos Schülerinnen) gratis einladen + Bundle gratis freischalten via Admin-Tool oder direkt CoursePurchase-Insert. Feedback einarbeiten, dann öffentlich. |
| "Englisch wieder anschalten?" | `CONTENT_LANGUAGES=german,english` Env-Var. Memory `project_content_languages_filter.md`. |
| "Neue Module / JLPT-Level?" | LessonCategory mit `jlpt_level`, `slug`, `display_order` anlegen. Lessons via `category_id` zuordnen. Sitemap-Modul-Eintrag automatisch. **N4-Bundle:** Pattern duplizieren — neuer Course "JLPT N4 Komplett", neue bundle_service-Funktionen, neue Route `/n4-bundle`. Generalisierung erst bei 3+ Bundles. |
| "Lesson-Paywall stört" | Kann Admin nie sehen (Bypass). Falls echte Anpassung nötig: `app/templates/lesson_paywall.html` (Conversion-kritisch). Layout-Pattern: Tease oben (Lesson-Titel + Beschreibung sichtbar), zwei CTA-Cards nebeneinander (empfohlen + sekundär). |

## 7. Verweise (Wissen, das nicht hier dupliziert wird)

- **Tech-Stack, Deployment, DB-Sync, Migrationen, Cloud SQL** → `CLAUDE.md`
- **Lesson-Generierung (Pipeline, Validator, Coverage)** → `generate-lesson` Skill + `learnings.md`
- **JLPT-Leitprinzip mit harten Regeln** → User-Memory `project_jlpt_leitprinzip.md`
- **Mayuko ist Lehrerin, nicht Lernerin** → User-Memory `user_mayuko_japanisch_lehrerin.md`
- **Payrexx-KYC-Wiedereinreichung 2026-04-25** → `project_payrexx_kyc_wiedereinreichung.md`
- **N5-Bundle Code+DB Architektur** → `project_n5_bundle_implementation.md`
- **N5-Pricing-Strategie (Konstanten + Math)** → `project_pricing_strategie_n5.md`
- **Funnel-Patterns vs. Anti-Patterns** → `feedback_funnel_patterns_2026_04_26.md`
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
