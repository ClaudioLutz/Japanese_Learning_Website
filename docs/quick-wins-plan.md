# Quick-Wins-Umsetzungsplan — japanese-learning.ch

**Erstellt:** 2026-05-31 · **Quelle:** Agent-Team-Audit (`quick-wins-audit`, 9 Opus-4.8-Teammates, je 1 Teilbereich)
**Status:** übergabefertig für ein Implementierungs-Team · **Diese Datei ist das einzige Schreib-Ergebnis der Analyse-Runde.**

---

## 1. Auswahl-Logik & Methodik

- Jeder der 9 Audit-Teammates hat seinen Teilbereich gegen den **Code** (exakte `Datei:Zeile`-Belege) geprüft; Live-Verifikation lief über **curl mit Browser-User-Agent**, weil WebFetch von **Cloudflare mit HTTP 403** geblockt wird (Bot-Schutz). Visuelle/JS-Punkte, die ohne Browser nicht final prüfbar waren, sind als „(visuell zu verifizieren)" markiert. Playwright-MCP wurde bewusst nicht genutzt (geteiltes Browser-Profil, Lock-Risiko bei 9 Parallel-Sessions).
- Ausgewählt sind **3 Quick Wins pro Teammitglied** (= 27 Picks). Durch Auflösung von 3 echten Cross-Member-Duplikaten und Bündelung ergeben sich **29 distinkte, deduplizierte Tasks** (inkl. 2 Bonus-Items, die je 2 Teammates gemeldet hatten).
- **Quick-Win-Filter (hart):** klein & lokal, risikoarm, keine DB-Migration, keine neuen Dependencies, kein größeres Refactoring, keine Laufzeit-LLM-Calls für Content. Faustregel ≤ 1 h. Alles Größere steht unter „Später / bewusst nicht gewählt" (Abschnitt 6).
- **DB-Lese-Checks** (z. B. tatsächliche Gratis-Lektions-Zahl, `fill_blank`-Bestand) sind **read-only Vorbedingungen**, KEINE Schreibzugriffe auf die Produktions-DB.

### Aufgelöste Duplikate (je nur 1× im Plan)
| Thema | Gemeldet von | Gewählter Task | Owner-Lane |
|---|---|---|---|
| Skip-Link + `<main>`-Landmark | layout-legal F2 **≡** tech-crosscut QW5 | **B-1** | Lane B |
| `defer` für Sortable + kana_grid_game.js | layout-legal F3 **≡** tech-crosscut QW3 | **B-4** | Lane B |
| OG-Image 1200×630 (statt Favicon) | marketing #4 **≡** tech-crosscut QW6 | **B-5** | Lane B |

---

## 2. Top 10 Quick Wins (höchster Nutzen / kleinster Aufwand zuerst)

| # | Task | Bereich | Aufwand | Warum zuerst |
|---|---|---|---|---|
| 1 | **C-1** Datenschutz: realen Hoster + Cloudflare nennen | Legal | S | Rechtliches Risiko (DSG/DSGVO Art. 13): nennt gelöschtes GCP-Hosting, Cloudflare als Auftragsverarbeiter fehlt ganz |
| 2 | **C-2** `/ueber`: „Google Cloud Run" → self-hosted | Marketing | S | Falsche Tatsachenbehauptung auf der Trust-/E-E-A-T-Seite; gehört mit #1 zusammen |
| 3 | **G-1** SRS: Doppel-Rating-Guard | SRS | S | Datenkorruption: Doppeltipp = doppelte XP + verfälschter FSRS-State + doppelter ReviewLog |
| 4 | **H-2** Kana: Hint-Timer-Race entschärfen | Kana-Spiel | S | Geister-`setTimeout` mutiert nach Restart die frische Runde (falscher Score / vorzeitiges Complete) |
| 5 | **C-6** Bundle-Hero „710/80" als Ziel framen | Pricing | S | Hero verspricht 710 Vok./80 Kanji, Coverage-Balken zeigt 273/710 → Refund-/Glaubwürdigkeitsrisiko |
| 6 | **A-2** Paid-Lessons aus Sitemap filtern | Tech/SEO | S | ~½ der gelisteten Lessons rendern `noindex` → Sitemap↔noindex-Konflikt, verbranntes Crawl-Budget (Hebel = Ranking) |
| 7 | **B-1** Skip-Link + `<main>`-Landmark | Layout/A11y | S | WCAG 2.4.1 global; betrifft jede Seite, 2 Teammates gemeldet |
| 8 | **E-1** OAuth-Fehler sichtbar machen | Auth | S | Google-Login-Fehler landen wortlos auf `/login` → stiller Funnel-Abbruch beim einzigen Social-Login |
| 9 | **D-2** `/purchase`: Widerruf(sverzicht) ergänzen | Pricing/Legal | S | Single-Kauf-Seite ohne Widerrufsbelehrung/-verzicht, die das Bundle bereits korrekt hat (Sofort-Freischaltung digital) |
| 10 | **F-1** `fill_blank`-Dead-Code entfernen | Lektion | S | CLAUDE.md verbietet `fill_in_the_blank`; voll funktionsfähiger Render-/JS-/Backend-Zweig unterläuft das Verbot (Read-only-DB-Check zuerst) |

---

## 3. Umsetzungs-Lanes für das Folge-Team (konfliktfrei partitioniert)

9 Lanes ≈ 9 Implementer. Lanes sind **nach Datei/Domäne disjunkt** geschnitten, damit parallele Sessions sich nicht überschreiben. **Hot-Files** mit Mehrfach-Zugriff sind unten gesondert markiert.

| Lane | Domäne | Hauptdateien | Tasks |
|---|---|---|---|
| **A** | SEO & Crawling | `app/seo_routes.py` | A-1, A-2, A-3 |
| **B** | Globales Layout, `<head>`, Perf-Config | `app/templates/base.html`, `app/__init__.py`, `.env` + Asset | B-1, B-2, B-3, B-4, B-5 |
| **C** | Marketing- & Legal-Texte | `ueber.html`, `legal/datenschutz.html`, `legal/agb.html`, `jlpt_n5_schweiz.html`, `lernmethode.html`, `bundles/n5_bundle.html` | C-1…C-6 |
| **D** | Kauf-Funnel (Single) | `app/templates/purchase.html` | D-1, D-2 |
| **E** | Auth | `login.html`, `register.html`, `app/routes.py` (Flash-Region), `app/__init__.py` | E-1, E-2, E-3 |
| **F** | Lektions-Detail & Quiz | `lesson_view.html`, `app/routes.py` (Quiz-Region), `app/static/css/custom.css` | F-1, F-2, F-3 |
| **G** | SRS-Review | `app/templates/review.html` | G-1, G-2 |
| **H** | Kana-Spiel | `practice_kana_game.html`, `app/static/js/kana_grid_game.js` | H-1, H-2, H-3 |
| **I** | Kurs-Übersicht | `courses.html`, `course_view.html` | I-1, I-2 |

### ⚠ Hot-File-Koordination (Pflicht beim parallelen Arbeiten — vgl. CLAUDE.md „Multi-Session")
- **`app/seo_routes.py`** — A-1, A-2, A-3 ändern alle dieselbe Datei (Sitemap- bzw. robots-Funktion). → **Nur EIN Implementer für ganz Lane A.**
- **`app/templates/base.html`** — B-1, B-2, B-4 ändern dieselbe Datei. → **Nur EIN Implementer für Lane B.**
- **`app/routes.py`** — E-3 (Flash-Region ~448–537) und F-1 (Quiz-Region ~3820/3950) berühren verschiedene Regionen derselben Datei. → **Lanes E und F sequenzieren oder eng abstimmen; klein committen + pushen.**
- **`app/static/css/custom.css`** — nur F-3 ändert CSS. **Nach JEDER custom.css-Änderung Deck-Karussell prüfen** (Browser-Konsole `[Deck]`-Logs, nur EINE Karte sichtbar) — ein Syntaxfehler bricht `.content-item.in-deck{display:none}` und macht alle Karten gleichzeitig sichtbar.

---

## 4. Task-Katalog (dedupliziert, übergabefertig)

> Format je Task: **Ort · Problem · Fix · Aufwand · Risiko · Akzeptanz · Abhängigkeiten · Dimension · Herkunft (Audit-Member)**

### Lane A — SEO & Crawling (`app/seo_routes.py`)

**A-1 · `/courses` nur bei ≥ 1 published Course in die Sitemap**
- Ort: `app/seo_routes.py` (sitemap_xml, `static_pages`) · Problem: `/courses` steht in der Sitemap, aber `/api/courses` liefert live `[]` (0 published Kurse) und die Seite rendert nur einen leeren Container → Soft-404-Signal an Google. · Fix: In `sitemap_xml()` `/courses` nur aufnehmen, wenn `Course.query.filter_by(is_published=True).count() > 0`. · Aufwand: S · Risiko: niedrig · Akzeptanz: `curl .../sitemap.xml` enthält `/courses` nur bei ≥ 1 Kurs. · Abh.: keine · Dim.: SEO · Herkunft: catalog QW2

**A-2 · Paid-Lessons (noindex) aus der Sitemap filtern**
- Ort: `app/seo_routes.py:110-122` ↔ `lesson_paywall.html:8` (`noindex,follow`) · Problem: Sitemap listet alle published Lessons inkl. Paid; für Gäste/Googlebot rendert `/lessons/<id>` bei Paid die Paywall mit `noindex` → ~½ der gelisteten URLs sind noindex (Stichprobe live: 167/168/169/148/149/145 = noindex). Widersprüchliches Signal, verbranntes Crawl-Budget. · Fix: In der Lesson-Schleife nur Lessons listen, die `index,follow` rendern (`if lesson.allow_guest_access` bzw. Gratis-Bedingung), sonst skip. · Aufwand: S · Risiko: niedrig · Akzeptanz: jede gelistete Lesson-URL liefert `index,follow`. · Abh.: keine · Dim.: SEO · Herkunft: tech-crosscut QW1

**A-3 · robots.txt: `/review` + `/practice` disallow, totes `/srs/` entfernen**
- Ort: `app/seo_routes.py:33-65` · Problem: robots.txt hat `Disallow: /srs/`, aber das Blueprint hat kein `/srs`-Prefix — die echten Routen sind `/review`, `/review/stats`, `/review/browse`, `/practice/kana(/spiel)` und sind NICHT disallowed. · Fix: `Disallow: /srs/` ersetzen durch `Disallow: /review` und `Disallow: /practice`. · Aufwand: S · Risiko: niedrig · Akzeptanz: `curl .../robots.txt` zeigt `/review` + `/practice`, kein `/srs/`. · Abh.: keine · Dim.: SEO · Herkunft: srs-review QW3

### Lane B — Globales Layout, `<head>` & Performance-Config

**B-1 · Skip-Link + `<main>`-Landmark** *(2× gemeldet)*
- Ort: `app/templates/base.html:540` (`<div class="container mt-4">`) · Problem: Content-Wrapper ist ein generisches `<div>`, kein `<main>`; kein Skip-Link → Tastatur-/Screenreader-Nutzer müssen sich durch 3 `<nav>`-Blöcke tabben (WCAG 2.4.1). · Fix: `<div class="container mt-4">` → `<main id="main-content" class="container mt-4">` (+ `</main>`), direkt nach `<body>` `<a href="#main-content" class="visually-hidden-focusable">Zum Inhalt springen</a>` (Bootstrap-Klasse vorhanden). · Aufwand: S · Risiko: niedrig · Akzeptanz: Tab zeigt zuerst Skip-Link; axe/Lighthouse meldet main-Landmark + Bypass nicht mehr. · Abh.: keine · Dim.: A11y · Herkunft: layout-legal F2 ≡ tech-crosscut QW5

**B-2 · Totes SearchAction-Target aus WebSite-JSON-LD entfernen**
- Ort: `app/templates/base.html:97-101` ↔ `app/routes.py:712` · Problem: JSON-LD `potentialAction` verspricht Sitesuche unter `/lessons?q=…`, aber `lessons()` liest keinen `q`-Parameter → totes Target, potenzieller Rich-Results-Fehler. · Fix: `potentialAction`-Block aus dem JSON-LD entfernen (sauberster Quick Win). · Aufwand: S · Risiko: niedrig · Akzeptanz: Rich-Results-Test zeigt keinen SearchAction-Fehler. · Abh.: keine · Dim.: SEO · Herkunft: tech-crosscut QW2

**B-3 · Statische Assets 1 Jahr cachen (`SEND_FILE_MAX_AGE_DEFAULT`)**
- Ort: `app/__init__.py` (create_app) · Problem: Eigene Assets sind per `static_v()` (mtime-`?v=`) versioniert, werden aber nur 4 h gecacht (`max-age=14400`); Cloudflare zeigt REVALIDATED statt HIT. · Fix: `app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000`. Stale-Risiko ~0 wegen Cache-Busting. · Aufwand: S · Risiko: niedrig · Akzeptanz: `curl -D-` auf `/static/css/custom.css` zeigt `max-age=31536000`; nach Edit ändert sich `?v=`. · Abh.: keine · Dim.: Performance · Herkunft: tech-crosscut QW4

**B-4 · `defer` für Render-Blocking-Skripte** *(2× gemeldet)* — Bonus
- Ort: `app/templates/base.html:51-52` · Problem: `Sortable.min.js` + `kana_grid_game.js` laden synchron im `<head>` → render-blocking auf JEDER Seite, obwohl nur fürs Kana-Spiel/Admin-DnD gebraucht (Alpine/confetti darunter haben korrekt `defer`). · Fix: beiden `defer` geben; `kana_grid_game.js` auf DOMContentLoaded-Sicherheit prüfen. · Aufwand: S · Risiko: niedrig (Kana-Spiel + Admin-Sortier gegentesten) · Akzeptanz: Lighthouse „render-blocking" verbessert; Spiel + Sortier funktionieren. · Abh.: keine · Dim.: Performance · Herkunft: layout-legal F3 ≡ tech-crosscut QW3

**B-5 · 1200×630-OG-Image statt Favicon** *(2× gemeldet)* — Bonus
- Ort: `app/__init__.py:55-58` (`SEO_DEFAULT_OG_IMAGE` Default `/static/favicon.png`) → `base.html:25` og:image + `base.html:79` JSON-LD logo · Problem: `twitter:card=summary_large_image` erwartet ein großes Bild, ausgeliefert wird das 2-KB-Favicon → winzige/verzerrte Social-Vorschau. · Fix: 1200×630-PNG (Brand: washi-Hintergrund + 朱-Akzent, Bilderzeugung via OpenAI Images laut CLAUDE.md erlaubt) nach `app/static/uploads/` legen, `SEO_DEFAULT_OG_IMAGE` in `.env` darauf setzen — kein Code-Change. · Aufwand: S · Risiko: niedrig · Akzeptanz: FB/LinkedIn-Sharing-Debugger zeigt große Karte. · Abh.: Bild-Asset (Design abstimmen) · Dim.: SEO/Social · Herkunft: marketing #4 ≡ tech-crosscut QW6

### Lane C — Marketing- & Legal-Texte

**C-1 · Datenschutz: realen Hoster + Cloudflare nennen** — [LEGAL, Top-Prio]
- Ort: `app/templates/legal/datenschutz.html:46-50` · Problem: nennt „Google Cloud Platform (Hosting, Datenbank, Cloud Storage) — Server in der EU" — seit 2026-05-24 self-hosted; Postgres lokal, GCS nur Offsite-Backup. **Cloudflare** (verarbeitet IP-Adressen, Edge Zürich) ist als Auftragsverarbeiter gar nicht genannt → DSG/DSGVO-Art.-13-Risiko. · Fix: Abschnitt umschreiben: GCP nur noch „Offsite-Backup (GCS, EU)"; **Cloudflare Inc. (CDN/Proxy, IP-Verarbeitung)** ergänzen; Hosting = „self-hosted Server, Schweiz". · Aufwand: S · Risiko: niedrig · Akzeptanz: `/legal/datenschutz` rendert Cloudflare + korrekten Hoster. · Abh.: keine · Dim.: Copy/Legal · Herkunft: layout-legal F1 · **Begleit-Konsistenz:** IP-Aufbewahrung §2 (datenschutz.html:27-28) zugleich präzisieren (App-Logs vs. Cloudflare-Edge-Logs) — layout-legal F7.

**C-2 · `/ueber`: „Google Cloud Run" → self-hosted** — [gemeinsam mit C-1]
- Ort: `app/templates/ueber.html:134` · Problem: „…Hosting in der Schweiz/EU bei **Google Cloud Run**." — Cloud Run wurde 2026-05-24 gelöscht; falsche Aussage auf der Datenschutz-/Trust-Seite. · Fix: z. B. „Self-hosted in der Schweiz, ausgeliefert über Cloudflare." (Wortlaut mit Claudio abstimmen, da Datenschutz-Aussage). · Aufwand: S · Risiko: niedrig · Akzeptanz: keine „Cloud Run"-Erwähnung mehr (`grep`). · Abh.: keine · Dim.: Copy/Korrektheit · Herkunft: marketing #1

**C-3 · AGB §8: „99 % Verfügbarkeit" entschärfen** — [LEGAL]
- Ort: `app/templates/legal/agb.html:83-86` · Problem: 99 %/Jahr (~3,65 Tage Downtime) ist auf einem Heim-Server schwer haltbar → unnötige Angreifbarkeit. · Fix: Prozentzahl streichen / „nach bestem Bemühen, ohne Verfügbarkeitsgarantie". · Aufwand: S · Risiko: niedrig · Akzeptanz: keine konkrete Prozent-Zusage mehr. · Abh.: keine · Dim.: Copy/Legal · Herkunft: layout-legal F6

**C-4 · Gratis-Lektionszahl vereinheitlichen (7 vs. 11)**
- Ort: `ueber.html:158` („7"), `lernmethode.html:94/98` („Sieben"/„7") vs. `jlpt_n5_schweiz.html:205/567` („11") · Problem: drei Marketing-Seiten nennen unterschiedliche Gratis-Lektionszahlen; Startseite berechnet `guest_accessible_lessons` dynamisch (routes.py:338) als Single Source of Truth. · Fix: alle Vorkommen auf den DB-wahren Wert vereinheitlichen (read-only DB-Check des echten Werts). · Aufwand: S · Risiko: niedrig · Akzeptanz: `grep` zeigt eine einheitliche Zahl == `guest_accessible_lessons`. · Abh.: read-only Zähl-Check · Dim.: Copy/Korrektheit · Herkunft: marketing #2

**C-5 · Bundle-JSON-LD `priceValidUntil` dynamisch**
- Ort: `app/templates/bundles/n5_bundle.html:27` (`"2026-12-31"`) · Problem: festes Datum → Google wertet das Offer ab 2027 als abgelaufen („Offer no longer valid"). · Fix: dynamisch rendern, z. B. `"{{ current_year + 1 }}-12-31"` (`current_year` ist im Context, `__init__.py:303`). · Aufwand: S · Risiko: niedrig · Akzeptanz: Rich-Results-Test zeigt zukünftiges Datum. · Abh.: keine · Dim.: SEO · Herkunft: marketing #5

**C-6 · Bundle-Hero „710 Vok./80 Kanji" als Ziel framen**
- Ort: `bundles/n5_bundle.html:247-249` (Hero) + `327-328` (Checklist) vs. `345-353` (Coverage-Balken: 273/710, 44/80) · Problem: Hero suggeriert 710/80 als Ist-Inhalt, Coverage zeigt 273/710 (38 %) → Refund-/Glaubwürdigkeitsrisiko trotz Stagnations-Garantie. · Fix: Hero/Checklist als Ziel formulieren („Der komplette N5-Wortschatz: 710 Vokabeln, 80 Kanji — laufend ausgebaut") oder Coverage-Zahl im Hero spiegeln. Reine Copy. · Aufwand: S · Risiko: niedrig · Akzeptanz: Hero und Coverage-Block widersprechen sich nicht mehr. · Abh.: keine · Dim.: Copy/Trust · Herkunft: pricing-checkout F2

### Lane D — Kauf-Funnel (Single, `app/templates/purchase.html`)

**D-1 · Geld-zurück-Hinweis auf `/purchase` ergänzen**
- Ort: `purchase.html:101-110` (Benefits ohne Refund) vs. Paywall/Bundle (überall „30 Tage Geld zurück") · Problem: Genau die finale Single-Kaufseite (höchste Kaufangst) nennt das stärkste Trust-Signal nicht. · Fix: Benefits-Liste/Security-Notice (Z.156-160) um „30 Tage Geld zurück — ohne Begründung" ergänzen (Wortlaut von Paywall übernehmen). · Aufwand: S · Risiko: niedrig · Akzeptanz: `/purchase/<id>` zeigt Refund-Hinweis. · Abh.: keine · Dim.: UX/Trust · Herkunft: pricing-checkout F4

**D-2 · Widerruf(sverzicht)-Link auf `/purchase` ergänzen** — [LEGAL]
- Ort: `purchase.html:131-140` (nur AGB + Datenschutz) vs. `n5_bundle.html:276-284` (AGB + Widerrufsbelehrung + ausdrücklicher Widerrufsverzicht) · Problem: Beim Bundle muss der Nutzer auf das Widerrufsrecht für sofort bereitgestellte digitale Inhalte verzichten; beim Single-Kauf fehlt das komplett — rechtlich/UX inkonsistent für dasselbe Produkt. · Fix: Checkbox-Label an n5_bundle.html angleichen: Link auf `legal.widerruf` (Route existiert) + Verzichts-Formulierung. · Aufwand: S · Risiko: niedrig · Akzeptanz: `/purchase/<id>` verlinkt Widerruf + Verzichtstext. · Abh.: `legal.widerruf` (vorhanden) · Dim.: Copy/Legal · Herkunft: pricing-checkout F5

### Lane E — Auth

**E-1 · OAuth-Fehler sichtbar machen**
- Ort: `app/oauth_routes.py:25/42/51/114` (Redirect `/login?error=oauth_failed`) + `login.html` (zeigt den Param nirgends) · Problem: Schlägt Google-Login fehl, landet der Nutzer wortlos auf `/login` → stiller Funnel-Abbruch beim einzigen Social-Login. · Fix: In `login.html` oben: `{% if request.args.get('error') == 'oauth_failed' %}<div class="alert alert-danger" role="alert">Die Anmeldung mit Google ist fehlgeschlagen. Bitte erneut versuchen oder mit E-Mail anmelden.</div>{% endif %}`. · Aufwand: S · Risiko: niedrig · Akzeptanz: `/login?error=oauth_failed` zeigt Fehlermeldung, `/login` unverändert. · Abh.: keine · Dim.: UX/Copy · Herkunft: auth-account QW1

**E-2 · `autocomplete`/`inputmode` an Login + Register**
- Ort: `login.html:18/25`, `register.html:18/25/32/39` · Problem: keine `autocomplete`-Attribute (forgot/reset machen es vor) → Passwort-Manager/Autofill greift unzuverlässig, kein „neues Passwort"-Vorschlag, schwächere Mobile-Tastatur-Hints. · Fix: login email→`username`/`email` + `type=email`, password→`current-password`; register username→`username`, email→`email`+`type=email`, password→`new-password`, password2→`new-password`. · Aufwand: S · Risiko: niedrig · Akzeptanz: HTML zeigt `autocomplete`; Browser bietet Speichern/Ausfüllen. · Abh.: keine · Dim.: UX/Mobile/A11y · Herkunft: auth-account QW3

**E-3 · Auth-Flash-Messages eindeutschen**
- Ort: `routes.py:448/465/471/483/537` + `__init__.py:27` (login_message) · Problem: UI ist deutsch, aber Register/Login/Logout/Lockout/Login-Required flashen Englisch. · Fix: Strings in Sie-Form übersetzen (z. B. :483 „Anmeldung fehlgeschlagen. Bitte E-Mail und Passwort prüfen.", :537 „Sie wurden abgemeldet.", __init__.py:27 „Bitte melden Sie sich an, um diese Seite zu sehen."). · Aufwand: S · Risiko: niedrig · Akzeptanz: deutsche Flash-Texte nach Register/Login/Logout. · Abh.: **Tests prüfen, die auf die englischen Strings asserten (CLAUDE.md: Tests mit anpassen).** · Dim.: Copy/Korrektheit · Herkunft: auth-account QW4

### Lane F — Lektions-Detail & Quiz

**F-1 · `fill_blank`-Dead-Code entfernen** — [Regel-Konformität]
- Ort: `lesson_view.html:1575-1586` (Render), `:2047-2053` (JS), `routes.py:3820-3827` (Scoring), `routes.py:3950-3951` (Generator) · Problem: CLAUDE.md verbietet `fill_in_the_blank`, doch ein voll funktionsfähiger Zweig existiert noch (Dead Code, der das Verbot unterläuft). · Fix: Render-Branch + JS-Zweig entfernen (Backend optional mit). · Aufwand: S · Risiko: niedrig · Akzeptanz: kein `fill_blank` mehr im Template; MC/TF/Matching unverändert; `pytest` grün. · Abh.: **Read-only DB-Check zuerst** — `SELECT count(*) … WHERE question_type='fill_blank'`; falls > 0, ist es KEIN reiner Quick Win (dann erst Content migrieren). · Dim.: Copy/Korrektheit · Herkunft: lesson-flow QW1

**F-2 · Quiz-/Progress-Strings eindeutschen**
- Ort: `lesson_view.html:1556` („✓ Completed"), `:1553` („points"), `:1676-1689` („Attempts remaining"/„Unlimited"), `:884/889/894` („Time Spent"/„Started"/„Completed"), `:1729` („This lesson is still being prepared…"), `:846` („No description available.") · Problem: englische Labels im sonst deutschen Lernfluss, teils direkt im Quiz sichtbar. · Fix: übersetzen („Erledigt", „{{ points }} Punkte", „Verbleibende Versuche/Unbegrenzt", „Zeit/Gestartet/Abgeschlossen", „Diese Lektion wird noch vorbereitet…", „Keine Beschreibung verfügbar."). · Aufwand: S · Risiko: niedrig · Akzeptanz: keine englischen UI-Strings mehr in der Lesson-View. · Abh.: keine · Dim.: Copy/Korrektheit · Herkunft: lesson-flow QW2

**F-3 · `.card-audio-btn` 44×44 Touch-Target** — [⚠ custom.css → Deck-Check]
- Ort: `custom.css:2346-2363` (38×38, `border-radius:50%`); globale Mobile-Regel `:4241-4250` setzt nur `min-height:44px` · Problem: Vorlese-Button wird mobil 44 px hoch aber 38 px breit → unter Norm + Kreis wird zur Ellipse (jede Vokabel/Kanji/Grammatik-Karte). · Fix: in `.card-audio-btn` `min-width:44px;min-height:44px` (lokale Klasse, NICHT die globale Regel ändern). · Aufwand: S · Risiko: niedrig · Akzeptanz: Button ≥ 44×44 + rund; **Deck-Karussell zeigt weiter eine Karte nach der anderen.** · Abh.: keine · Dim.: UX/Mobile/A11y · Herkunft: lesson-flow QW3

### Lane G — SRS-Review (`app/templates/review.html`)

**G-1 · Doppel-Rating Re-Entry-Guard**
- Ort: `review.html:1440-1503` (rateCard) · Problem: `rateCard()` inkrementiert `currentIdx`/`ratedIds` erst NACH dem `await fetch('/api/srs/rate')`; ein zweiter Klick/Tastendruck während des Calls bewertet dieselbe `content_id` doppelt → doppelte XP, 2 Reps, doppelter ReviewLog. · Fix: Re-Entry-Guard (`if (rateCard._busy) return; rateCard._busy = true;` … `finally { rateCard._busy = false; }`) oder Button-Gruppe während des Calls `disabled`. · Aufwand: S · Risiko: niedrig · Akzeptanz: 2× schnell „Gut" → nur 1 ReviewLog, `statDue` sinkt um 1. · Abh.: keine · Dim.: Korrektheit/UX · Herkunft: srs-review QW1

**G-2 · Flip-Card per Tastatur bedienbar + Fokus**
- Ort: `review.html:1286-1353` (Karte = `<div>` mit click-Handler, ohne tabindex/role/aria) · Problem: Karte nicht fokussierbar, Enter dreht nicht um, kein sichtbarer Fokus-Ring, SR kündigt kein Control an. · Fix: `tabindex="0" role="button" aria-label="Karte umdrehen"`; im keydown Enter zusätzlich zu Space; `:focus-visible`-Outline. · Aufwand: S · Risiko: niedrig · Akzeptanz: Tab fokussiert Karte (sichtbarer Ring), Enter/Space dreht um. · Abh.: keine · Dim.: A11y · Herkunft: srs-review QW2

### Lane H — Kana-Spiel (`practice_kana_game.html`, `app/static/js/kana_grid_game.js`)

**H-1 · `aria-live`-Region für Spiel-Feedback**
- Ort: `practice_kana_game.html` + `kana_grid_game.js:304-356` · Problem: 0 Treffer für aria-live/role=status/sr-only — Richtig/Falsch/Hint/Score/Abschluss sind rein visuell → für Screenreader unspielbar. · Fix: versteckte `<div aria-live="polite" class="sr-only" x-text="ariaFeedback">`; in `handleDrop()`/`onComplete()` kurze DE-Ansagen setzen („Richtig: あ", „Falsch, nochmal", „Geschafft! 3 Sterne"). · Aufwand: S · Risiko: niedrig · Akzeptanz: Screenreader liest Drop-Ergebnis vor. · Abh.: keine · Dim.: A11y · Herkunft: kana-game #2

**H-2 · Hint-Timer-Race entschärfen**
- Ort: `kana_grid_game.js:561-577` (useHintForCell, `setTimeout 1500ms`) vs. `restart() 632-658` / `setMode() 580-603` · Problem: kein `clearTimeout` — wird im 1,5-s-Fenster neu gestartet, mutiert der alte Timer die frische Runde (`solvedCount++`, evtl. vorzeitiges `onComplete`). · Fix: Timer-Handle in `this._hintTimer` merken, in `restart()`/`setMode()` clearen; im Callback `if (cell.status==='correct') return;`. · Aufwand: S · Risiko: niedrig · Akzeptanz: Hint auslösen, sofort „Nochmal" → `solvedCount` bleibt 0, kein Geister-Complete. · Abh.: keine · Dim.: Korrektheit · Herkunft: kana-game #5

**H-3 · Daily-Challenge-Bonus-XP anzeigen**
- Ort: `srs_routes.py:854-859` (`'bonus_xp': 25`) vs. `kana_grid_game.js` (Feld nie gelesen) + `practice_kana_game.html:305-309` · Problem: Daily-Endpoint verspricht 25 Bonus-XP bei perfektem Abschluss, der Client liest/zeigt sie nie → dokumentierter Anreiz existiert faktisch nicht. · Fix (Quick Win = nur Anzeige): bei `isDaily && perfect` im Ergebnis „+25 Bonus-XP" ausweisen. · Aufwand: S (Anzeige) · Risiko: niedrig · Akzeptanz: Daily perfekt beenden → Bonus sichtbar. · Abh.: echte Gutschrift wäre M (SRS-Rating-Flow, Lane G/SRS) — hier nur Anzeige. · Dim.: UX/Korrektheit · Herkunft: kana-game #8

### Lane I — Kurs-Übersicht (`courses.html`, `course_view.html`)

**I-1 · `via.placeholder.com` → lokaler Gradient-Placeholder**
- Ort: `courses.html:167-170`, `course_view.html:63/347` · Problem: externer Platzhalterdienst (seit 2024 unzuverlässig/teils offline) als Fallback-Bild + `onerror` → kaputte Bilder + externer Request (DSGVO/Performance) bei jeder Card ohne Bild. · Fix: lokalen CSS-Gradient-Placeholder verwenden (wie `lessons.html:704-711` `.lp-lesson-thumb-placeholder` es vormacht). · Aufwand: S · Risiko: niedrig · Akzeptanz: keine Requests an via.placeholder.com mehr. · Abh.: keine · Dim.: Performance/Datenschutz · Herkunft: catalog QW3

**I-2 · `course_view.html` englische Labels eindeutschen**
- Ort: `course_view.html:87/97/107-111/123/248/76` · Problem: „Lessons/Minutes/Beginner…/Complete/Completed" + EN-Fallback-Description in deutscher UI. · Fix: „Lektionen/Minuten/…/Abgeschlossen/Fertig"; Level-DE-Mapping (Z.220-226) wiederverwenden; EN-Fallback-Text auf DE. · Aufwand: S · Risiko: niedrig · Akzeptanz: keine englischen UI-Wörter auf `/course/<id>`. · Abh.: keine · Dim.: Copy/Korrektheit · Herkunft: catalog QW4

---

## 5. Querschnitt-Themen (für die Selbstkontrolle des Teams)

- **Deutsch-Konsistenz** zieht sich durch 4 Dateien (E-3 Auth-Flashes, F-2 Quiz/Progress, I-2 course_view, C-2/C-1 Marketing/Legal). Kein Duplikat — verschiedene Strings/Dateien; bei der Umsetzung als gemeinsamer Stil-Check behandeln (Sie-Form, Umlaute korrekt).
- **A11y-Ansagen** (`aria-live`/Fokus): B-1, G-2, H-1 adressieren je eine andere Surface — zusammen ein spürbarer A11y-Sprung.
- **SEO/Crawl-Hygiene**: A-1, A-2, A-3, B-2 zahlen alle auf das Memory-Ziel „Ranking-Hebel, Crawl-Budget schonen" ein.

---

## 6. Bewusst NICHT als Quick Win gewählt / „Später" (größer als ~1 h oder Fremdsystem)

**Cloudflare-Konfiguration (kein Repo-Code, Dashboard):**
- **E-Mail-Obfuscation entwertet die Refund-CTA**: `mailto:info@…` in der Geld-zurück-/Stagnations-Garantie wird zu „[email protected]" (data-cfemail) und braucht JS — der vertrauenskritische Kanal ist bei deaktiviertem JS unbrauchbar. Fix: Scrape-Shield → Email Obfuscation für diese Routen aus. *(pricing-checkout Cross-Cutting)*
- **Doppelte `User-agent: *`-Blöcke in robots.txt**: Cloudflare „Managed robots.txt / AI-Crawler-Block" stellt der App-robots.txt eine eigene `*`-Gruppe voran → manche Bots lesen nur die erste und ignorieren `/admin`,`/api/`-Disallows. Fix: Managed-Robots deaktivieren oder App-Disallows dort übernehmen. *(tech-crosscut QW8)*

**Architektur / größeres Refactoring:**
- `/courses` als echtes SSR (statt JS-Fetch aus robots-blockiertem `/api/courses`) — M; A-1 ist der schnelle Schutz. *(catalog QW1)* · Grundsatzfrage: Ist „Kurse" überhaupt noch ein aktives Konzept (0 published)?
- Marketing-Content-Seiten (`jlpt_n5_schweiz`/`lernmethode`/`ueber`) komplett aufs washi/朱-Designsystem heben (Bootstrap-Buttons + Indigo/Blau raus) — M–L; CTA-Buttons-Teil wäre ein eigener kleiner QW. *(marketing #6/#7)*
- `payment_success.html`/`payment_failed.html` aufs Redesign heben + `javascript:history.back()` durch echten Link ersetzen + CHF-Formatierung — M. *(pricing-checkout F6/F7)*
- Zentraler Context-Provider für Marketing-Zahlen (vocab/kanji/lesson/guest) statt Hardcoding pro Seite — strukturell, > 1 Datei. *(marketing #3/#8)*
- Großes Inline-JS/CSS aus `lesson_view.html` (~2100 Z. JS mit Jinja-Vars) auslagern — Refactoring + Tests. *(lesson-flow QW8/„Später")*
- N+1 in `/api/srs/due` (eager loading), `/review/stats` viele Chart-Calls — Performance, messen statt blind optimieren. *(srs-review „Später")*
- Hör-Diktat-Modus, Confusion-Drill-Onboarding, Kana-Grid-Volltastatur-Navigation, `rateCell()`-Batching — Features. *(kana-game „Später")*
- **Korrektheits-Cleanups niedriger Sichtbarkeit** (sinnvoll, aber nicht Top): Mock-Service erzeugt zwei divergierende `transaction_id` (mock_payment_service.py:43-45 vs 51-52) — latenter Bug, Referenz für Payrexx-Go-Live *(pricing F9)*; Romaji-D-Reihe ぢ/づ-Mapping *(kana #1)*; `/impressum`-Kurzroute → 301 falls extern verlinkt *(layout F5)*; 500-Handler ohne `db.session.rollback()` (`__init__.py:284-286`) *(layout/tech)*; Vokal-Probe nutzt Browser-`speechSynthesis` statt Premium-Audio *(marketing #9)*.
- **CDN → Build-Pipeline** (Tailwind Play CDN ist nicht für Prod), jQuery-Eliminierung, doppelte Google-Fonts-Requests zusammenlegen — neue Deps/Build-Setup. *(tech-crosscut „Später")*
- **Homepage Edge-Caching** (Session-Cookie + `Vary: Cookie` → `Cf-Cache-Status: DYNAMIC`): höchster TTFB-Hebel für Gäste, aber CSRF-/Session-Flow-Risiko. *(tech-crosscut QW7)*

---

## 7. Umsetzungs-Hinweise (Definition of Done je Task)
- Vor jedem Commit: betroffene Tests anpassen + `pytest` grün (CLAUDE.md). E-3 (Flash-Strings) und F-1 (`fill_blank`) brauchen ggf. Test-Updates.
- Nach Python-Änderungen `ruff check`.
- Nach **jeder** `custom.css`-Änderung (F-3): Deck-Karussell visuell prüfen.
- Klein & oft committen + pushen; bei Hot-Files (seo_routes.py, base.html, routes.py) Datei nur durch EINEN Implementer pro Lane.
- Live-Verifikation: `curl` mit Browser-User-Agent (WebFetch wird von Cloudflare 403-geblockt).
