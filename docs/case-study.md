# Case Study: japanese-learning.ch

**Eine self-hosted Flask-Lernplattform für JLPT N5 — Deutsch erklärt, in der Schweiz gebaut.**

_Solo-Projekt von Claudio Lutz · Engineering-Referenz · Stand 2026-06-20_

---

## TL;DR

japanese-learning.ch ist eine vollständige, produktiv laufende Japanisch-Lernplattform: strukturierte JLPT-N5-Lektionen mit eigenem Spaced-Repetition-System (FSRS), Quiz-Engine, zwei Kana-Arcade-Spielen, einer Content-Pipeline mit adversarialer Niveau-Prüfung und einer zweisträngigen Audio-Generierung. Sie läuft self-hosted auf einem Heim-Server hinter einem Cloudflare-Tunnel — Docker Compose, Gunicorn, PostgreSQL, tägliche automatisierte Backups.

Das Projekt ist als **Referenz** gebaut, nicht als Umsatzquelle. Es zeigt End-to-End-Engineering einer Person: Architektur, Datenmodellierung, eine bewusst reversible Monetarisierungs-Schicht, eine LLM-Content-Pipeline ohne Laufzeit-LLM-Calls, Lern-Algorithmik und Betrieb. Ehrlich benannt: Das Produkt ist technisch fertig und gepflegt; die offene Front ist die Distribution/Reichweite, nicht der Code.

---

## 1 · Problem & Kontext

Wer im deutschsprachigen Raum Japanisch für JLPT N5 lernen will, findet überwiegend englischsprachige Apps (WaniKani, Bunpro) oder generische Karteikarten-Tools (Anki) ohne kuratierten Lehrplan. Eine Plattform, die

- **auf Deutsch erklärt**,
- **strikt nach JLPT-Niveaus strukturiert** ist (N5-Vokabular wird nur mit N5-Vokabular erklärt),
- den kompletten Lern-Loop abdeckt — Lektion lesen → Quiz → Spaced Repetition → spielerisches Kana-Training —

ist eine unterversorgte Nische. Genau das adressiert japanese-learning.ch. Das Leitprinzip ist Niveau-Disziplin: Inhalte folgen offiziellen JLPT-Vokabellisten, und jeder generierte Beispielsatz wird gegen das Ziel-Level geprüft (siehe §3).

Zusätzlicher Kontext: Das Projekt ist gleichzeitig Claudios eigenes Lern-Werkzeug. „Dogfooding" ist hier wörtlich — die Plattform wird vom Autor selbst zum Japanisch-Lernen benutzt, was den Feature-Fokus erdet.

---

## 2 · Architektur

### Überblick

```
   Internet
      │  HTTPS (TLS endet bei Cloudflare)
      ▼
┌──────────────┐    cloudflared       ┌────────────────────────────────────────────┐
│  Cloudflare  │ ─── (systemd) ─────► │  Docker: japanese_app  (Gunicorn, 2 Worker) │
│  Edge/HTTPS  │     Tunnel           │  ┌──────────────────────────────────────┐  │
└──────────────┘                      │  │ Flask  create_app()  (App-Factory)   │  │
                                      │  │  Extensions: SQLAlchemy · Migrate ·  │  │
                                      │  │   Login · CSRF · Limiter · Talisman ·│  │
                                      │  │   Mail                                │  │
                                      │  │  Blueprints: routes · srs · bundle · │  │
                                      │  │   legal · seo · oauth · social_auth ·│  │
                                      │  │   debug   (+ Flask-Admin /admin-panel)│  │
                                      │  └──────────────────────────────────────┘  │
                                      └───────────┬──────────────────┬─────────────┘
                                                  │ SQLAlchemy       │ Volume-Mount
                                                  ▼                  ▼
                                      ┌────────────────────┐   app/static/uploads/
                                      │ Docker: postgres_db│   (Bilder, Audio)
                                      │  = Produktions-DB  │
                                      └────────────────────┘

   Frontend pro Seite:  Jinja2  +  Tailwind (Play-CDN)  +  Alpine.js  +  HTMX
```

### Kernentscheidungen der Anwendungsschicht

- **App-Factory** (`create_app()` in `app/__init__.py`): Extensions werden modulglobal angelegt und in der Factory via `init_app()` gebunden. Das macht die App test-freundlich (Konfiguration pro Testlauf injizierbar) und sauber gegen Import-Reihenfolge-Probleme. Pflicht-Env (`SECRET_KEY`, `DATABASE_URL`) wird beim Start hart validiert — kein stiller Fallback auf SQLite oder einen Default-Key.
- **Blueprint-Aufteilung**: Acht Blueprints (`routes`, `srs`, `bundle`, `legal`, `seo`, `oauth`, `social_auth`, `debug`) trennen öffentliche Views, das Spaced-Repetition-System, den Verkaufspfad, Rechtstexte, SEO-Endpoints und Auth. Die Reihenfolge ist bewusst: der eigene OAuth-Callback wird **vor** der social-auth-Pipeline registriert, um deren Callback gezielt zu überschreiben.
- **Auth**: Flask-Login für lokale Konten plus Google OAuth2 (Authlib / python-social-auth) mit PKCE. Login-Lockout (5 Fehlversuche → 15 Min Sperre) und signierte, zeitbegrenzte Passwort-Reset-Tokens (`itsdangerous`, 1 h).
- **Security-Header**: Flask-Talisman setzt Content-Security-Policy und erzwingt HTTPS in Produktion. `ProxyFix` vertraut den Forwarded-Headern des Cloudflare-Tunnels, damit Flask das korrekte HTTPS-Schema (u. a. für OAuth-`redirect_uri`) sieht.
- **Rate Limiting**: Flask-Limiter (Default 200 req/h pro IP).

### Betriebsschicht (self-hosting)

Die App läuft **nicht in der Cloud**, sondern self-hosted auf einem Heim-Server (Ubuntu). Der Pfad ist: Cloudflare-Edge (HTTPS) → `cloudflared`-Tunnel als systemd-Dienst → Docker-Container `japanese_app` (Gunicorn, 2 Worker) → Container `postgres_db`. Medien (Bilder, Audio) liegen in einem Docker-Volume und werden direkt ausgeliefert. Container haben `restart: unless-stopped` plus Docker-Autostart, überstehen also Reboots. Der Entrypoint wartet aktiv auf die DB, fährt `flask db upgrade` und startet dann Gunicorn.

> **Ehrlicher Hinweis:** Es gibt noch GCloud-Namensrelikte aus der früheren Cloud-Run-Phase (`Dockerfile.cloudrun`, `K_SERVICE`-Checks in der `is_production`-Erkennung). Sie sind funktional korrekt, aber kosmetisch veraltet — siehe §9.

---

## 3 · KI-Content-Pipeline: Qualität durch Disziplin, nicht durch Laufzeit-Magie

Das prägendste Engineering-Prinzip des Projekts: **Es gibt keine Laufzeit-LLM-Calls für Inhalte.** Japanische Texte (Vokabeln, Beispielsätze, Lesungen, Übersetzungen, Erklärungen, Quiz) werden von Claude **vor** dem Deployment verfasst, adversarial gegen das JLPT-Level geprüft und als geprüftes Ergebnis per Skript in die DB geschrieben. Der Webserver ruft zur Laufzeit nie ein Text-LLM auf.

**Warum dieser Ansatz?**

1. **Niveau-Korrektheit ist nicht verhandelbar.** Ein N5-Beispielsatz, der versehentlich N3-Vokabular enthält, ist didaktisch schädlich. Statt zur Laufzeit zu hoffen, läuft die Generierung als Workflow-Fan-out: ein Draft-Agent schreibt, ein oder mehrere Reviewer-Agenten prüfen adversarial gegen die offizielle Vokabelliste, Fix-Agenten korrigieren. Erst das geprüfte JSON geht in die DB (z. B. `scripts/regenerate_vocab_examples.py` mit `scripts/data/vocab_example_sentences.json`).
2. **Determinismus & Kosten.** Kein LLM-Call im Request-Pfad bedeutet: vorhersehbare Latenz, keine API-Ausfälle als User-facing-Fehler, keine laufenden Token-Kosten pro Seitenaufruf.
3. **Reproduzierbarkeit.** Der geprüfte Content liegt versioniert als JSON vor; ein Re-Run schreibt deterministisch in die DB (DRY-RUN / `--apply` / Backup-Muster).

**Was extern bleibt** (kein Text-Content):

| Aufgabe | Dienst | Wo im Code |
|---|---|---|
| Lektions-/Vokabel-/Kanji-Bilder | **Nano Banana** (`gemini-2.5-flash-image`) | `*_nb`-Methoden in `app/ai_services.py`, zentraler REST-Call in `nano_banana.py`, getrieben von `scripts/generate_lesson_images.py` |
| TTS-Audio | Google (Gemini-2.5-Pro-TTS + Cloud TTS) | siehe §5 |

Die Bilder durchlaufen einen QC-Detektor (Text-im-Bild-Erkennung) und eine „until-clean"-Schleife, weil generierte Bilder gern unerwünschte Schriftzeichen einbauen.

> **Ehrlicher Hinweis:** Im Code existieren noch ältere Gemini-**Text**-Methoden und OpenAI-`gpt-image-1-mini`-Bild-Methoden in `ai_services.py`. Diese sind durch die neue Pipeline abgelöst (toter bzw. Legacy-Pfad) — ein Admin-Endpoint ruft die Gemini-Text-Methoden noch auf und widerspricht damit dem Soll-Zustand „Content nur via Claude". Aufräum-Kandidat, kein Live-Risiko.

---

## 4 · Lern-Engineering

Der Lern-Loop ist absichtlich vollständig: vom ersten Lesen bis zur Langzeit-Retention.

### Lektions-/Seiten-Modell

`Lesson` → `LessonPage` → `LessonContent`. Ein `LessonContent`-Item ist polymorph (`content_type`: kana, kanji, vocabulary, grammar, text, media, quiz, dialog_slideshow …) und verweist über `content_id` auf die Referenztabellen `Kana` / `Kanji` / `Vocabulary` / `Grammar`. Der Fortschritt zählt nur die **sichtbaren** Items (`progress_visible_content_items`) — dekorative Seitenbilder (`is_optional`) blockieren den Lektionsabschluss bewusst nicht. Dieser Nenner-Bug (Progress blieb bei 96 %) wurde gezielt behoben.

### Quiz-System

`QuizQuestion` / `QuizOption` / `UserQuizAnswer`. Unterstützt sind `multiple_choice`, `true_false` und `matching` (`fill_in_the_blank` wurde bewusst deprecated). Japanische Quiz-Fragen erhalten nach Policy eine neutrale Romaji-Lesehilfe — außer bei Lese-/Aussprache-Testfragen, wo Romaji die Lösung verraten würde.

### Spaced Repetition (FSRS)

Das SRS baut auf der `fsrs`-Library (v6) auf — dem modernen Free Spaced Repetition Scheduler, nicht dem alten SM-2. Pro User wird ein Scheduler aus `UserSRSSettings` (`desired_retention`, optionale gewichtete `fsrs_parameters`) mit `enable_fuzzing` gebaut. `rate_card` ist die Kern-Operation: lädt/erstellt den `CardReviewState`, ruft den Scheduler, schreibt FSRS-State + `due_date`, erhöht `reps`/`lapses`, vergibt XP, aktualisiert Streak und prüft Achievements — alles in einer Transaktion. Jede Bewertung wird in `ReviewLog` protokolliert (Basis für einen späteren FSRS-Optimizer).

Die Statistik-Seite zieht aus elf Endpoints parallel: 365-Tage-Heatmap, Retention nach Intervall, Forecast, Reifegrad-Verteilung, Performance je Content-Typ, Antwortzeit-Histogramm, Leeches, JLPT-Fortschritt und pro-Zeichen-Kana-Statistik.

### Kana-Spiele (zwei Modi, geteilte Datenquelle)

- **Matching-Grid** (`/practice/kana`): eine echte Gojūon-Tabelle (vokal-ausgerichtete Spalten), Drag-/Tap-Zuordnung Kana↔Romaji, mit Tages-Challenge, Lese-Modus und Verwechslungs-Drill (visuell ähnliche Kana-Cluster).
- **Kana Storm** (`/practice/kana/storm`): endloser Romaji-Tipp-Loop gegen die Uhr (Arcade) plus eine Wordle-artige Daily-Challenge mit global identischem Tagesbrett und teilbarem Emoji-Block.

Beide laufen ohne Login spielbar (Gast-Scope = voller Gojūon), Score-Persistenz ist login-pflichtig. Sie teilen Datenquelle, Reihen-Mapping (`services/kana_rows.py`) und Verwechslungs-Cluster (`services/kana_confusion.py`).

### Gamification

XP pro Bewertung (gewichtet nach Rating), Neu-Karten-Bonus, Streak-Tage, gelegentlicher Variable-Reward-Boost (8 % Wahrscheinlichkeit), polynomiale Level-Kurve (`100·level^1.5`) mit japanisch-thematischen Titeln, 24 im Code definierte Achievements, Streak mit wöchentlichem Freeze. Tagesgrenze für Streak/Aggregate: Europe/Zurich.

---

## 5 · Audio-Pipeline (zwei Systeme, ein Voice-Stack)

Audio ist zweisträngig, weil die zwei Use-Cases unterschiedlich sind:

| System | Trigger | Output |
|---|---|---|
| **Inline-Audio** (Klick-Audio) | Klick auf Absatz in `.rich-text-content` | Hash-benannte WAV/MP3 pro Absatz |
| **Block-Player** (▶ über Lektion) | `<audio>`-Element rendert `media_url` | WAV (DE+JP segmentiert konkateniert) |

**Voice-Stack:**
- **Japanisch:** `gemini-2.5-pro-preview-tts`, Stimme „Leda" (studio-nahe Qualität).
- **Deutsch:** `de-DE-Neural2-G` über Cloud TTS REST (Gemini hat keine deutsche Stimme).
- **Fallback** bei Safety-Block oder Quota-Hit (2'500 Calls/Tag): `ja-JP-Chirp3-HD-Leda` — gleiche Stimm-Persönlichkeit, andere Engine.

**Pause-Heuristik** (`_maybe_spell_out_kana_row`): Kana-Sequenzen einer Gojūon-Reihe (4–7 Mora) werden mit dem japanischen Komma `、` getrennt, damit die TTS sie einzeln ausspricht (`さしすせそ` → `さ、し、す、せ、そ`). Bewusst `、` statt `[short pause]`-Markup — letzteres führte bei Gemini reproduzierbar zu Truncation (nur die erste Mora wurde gesprochen). Audio-Probe-validiert.

Ein zentraler `clean_tts_segment` (`services/tts_text.py`) entfernt Rand-Symbole vor dem Vorlesen — sonst las die JP-Stimme `—` als „Minus" und die DE-Stimme Romaji-Klammern mit.

---

## 6 · Qualität & Betrieb

- **Tests:** ~73 pytest-Dateien (Unit + Integration) plus 9 Playwright-E2E-Specs (öffentliche Routen, Auth, Lektionen/Kurse, Payment, Admin, API, Security, Kana-Mobile). Projektregel: kein Commit mit fehlschlagenden Tests, Coverage-Floor (`fail_under`) darf nur steigen. UI-Änderungen werden vor Deploy mit Playwright visuell gegengeprüft.
- **Migrations:** Alembic / Flask-Migrate (30 Migrationen). Im Container läuft `flask db upgrade` automatisch beim Start.
- **Backups:** Täglicher `pg_dump` via systemd-Timer (03:30), 14-fache Rotation, dokumentierter Restore-Pfad. Medien zusätzlich als Offsite-Snapshot in einem GCS-Bucket.
- **SEO:** Dynamische `sitemap.xml` und `robots.txt` aus der DB (eigenes Blueprint, CSRF-exempt). JSON-LD (`EducationalOrganization`, `WebSite` mit SearchAction, `Course` pro Lektion), OpenGraph/Twitter-Cards, per-Seite überschreibbare Meta-Tags. Paid-Lektionen werden bewusst nicht in die Sitemap aufgenommen; ein `ROBOTS_INDEX`-Schalter sperrt Staging komplett.
- **Admin-Tooling:** Zwei Oberflächen — ein selbstgebautes `/admin` (Tailwind, Alpine, HTMX, Dark Mode, Command Palette per Ctrl+K, Toast-Notifications, modularer Lektions-Editor aus 11 Partials statt eines 4'300-Zeilen-Monolithen) und ein Flask-Admin-CRUD-Panel `/admin-panel` für schnelles Daten-Editing. Inline-Reference-Editing erlaubt das Bearbeiten referenzierter Vokabel-/Kanji-Daten direkt im Content-Editor.
- **Analytics:** Plausible ist im Code verdrahtet (datenschutzfreundlich, aktiviert über `PLAUSIBLE_DOMAIN`).

---

## 7 · Tech-Stack

| Schicht | Technologie |
|---|---|
| Sprache | Python 3.12 |
| Web-Framework | Flask 2+ (App-Factory, 8 Blueprints) |
| ORM / Migrations | SQLAlchemy, Flask-Migrate (Alembic) |
| Datenbank | PostgreSQL 15 (Docker) |
| Auth | Flask-Login + Google OAuth2 (Authlib / python-social-auth, PKCE) |
| Security | Flask-Talisman (CSP/HTTPS), Flask-WTF (CSRF), Flask-Limiter |
| SRS | `fsrs` 6.x (Free Spaced Repetition Scheduler) |
| Frontend | Jinja2, Tailwind (Play-CDN), Alpine.js, HTMX |
| Mail | Flask-Mail (Passwort-Reset, Hostpoint SMTP) |
| Payment (ruhend) | Payrexx / Mock / PostFinance via Factory |
| Content-Bilder | Nano Banana (`gemini-2.5-flash-image`) |
| TTS | Gemini-2.5-Pro-TTS „Leda" (JP) + Cloud TTS Neural2-G (DE), Chirp-Fallback |
| App-Server | Gunicorn (2 Worker) |
| Container/Orchestrierung | Docker Compose |
| Edge / TLS / DNS | Cloudflare + `cloudflared`-Tunnel (systemd) |
| Tests | pytest (~73 Dateien), Playwright (9 Specs) |
| Analytics | Plausible |

---

## 8 · Bewusste Engineering-Entscheidungen & Trade-offs

**1. `price == 0.0` als einziges Frei-/Bezahl-Signal — und damit eine vollständig reversible Monetarisierung.**
Die gesamte Zugriffslogik (`Lesson.access_check()` / `is_accessible_to_user()` in `app/models.py`) hängt an `price == 0.0`. Das abgeleitete Feld `lesson_type` wird **nicht** redundant gepflegt, sondern von einem SQLAlchemy-Event-Listener bei jedem Insert/Update aus dem Preis berechnet (`models.py:1799` — `price == 0 → 'free'`, sonst `'paid'`). Konsequenz: Das Produkt gratis schalten ist eine reine **Daten**-Änderung (Preise auf 0), kein Code-Umbau — und genauso einfach wieder rückgängig zu machen. Monetarisierung bleibt als ruhende, reaktivierbare Schicht erhalten (Payrexx-Integration, Bundle-Service mit dynamischem Preis, Paywall-Templates) statt gelöscht zu werden.
_Trade-off:_ Das Signal ist implizit (ein Float-Vergleich statt ein explizites Enum), und der Event-Listener ist „Magie auf Distanz". Der Gewinn — eine reversible Geschäftsentscheidung als One-Liner — überwiegt das hier klar.

**2. Self-hosting statt Cloud.**
Die Plattform lief zunächst auf Cloud Run + Cloud SQL und wurde bewusst auf einen Heim-Server hinter einem Cloudflare-Tunnel migriert.
_Gewinn:_ keine laufenden Hosting-Kosten, volle Daten-Hoheit, kein Kaltstart-Problem, einfache lokale Iteration (Dev-DB = Prod-Topologie).
_Trade-off:_ Verfügbarkeit hängt an Strom/Internet zu Hause; horizontale Skalierung ist nicht das Ziel. Für ein Referenz-/Lernprojekt mit überschaubarer Last ist das die korrekte Wahl — und es demonstriert den vollen Ops-Stack (Tunnel, systemd, Backups, Autostart) statt ihn an einen Managed-Service zu delegieren.

**3. Content ausschließlich von Claude, ohne Laufzeit-LLM-Calls.**
Statt zur Laufzeit zu generieren, wird Content vorab verfasst, adversarial gegen das JLPT-Level geprüft und als geprüftes Ergebnis in die DB geschrieben (§3).
_Gewinn:_ garantierte Niveau-Korrektheit, deterministische Latenz, keine Token-Kosten pro Request, reproduzierbarer Content.
_Trade-off:_ keine spontane Personalisierung zur Laufzeit; neue Inhalte brauchen einen bewussten Generierungs-Lauf. Für eine Lehr-Plattform, wo Korrektheit über Spontaneität geht, ist das die richtige Priorität.

**4. FSRS statt selbstgebauter SRS-Heuristik.**
Spaced Repetition wird über die etablierte `fsrs`-Library gefahren, nicht über eine eigene SM-2-Variante.
_Gewinn:_ wissenschaftlich fundierte Scheduling-Qualität, pro-User-Retention-Tuning, ein `ReviewLog` als Basis für späteres Parameter-Fitting.
_Trade-off:_ Abhängigkeit von einer externen Library und ihrem Datenmodell — akzeptabel, weil das Rad hier nicht neu erfunden werden sollte.

**5. Modulare Templates gegen Monolithen.**
Der Lektions-Editor wurde von einem 4'342-Zeilen-Monolithen in einen 67-Zeilen-Orchestrator plus 11 eigenständig testbare Partials zerlegt.
_Gewinn:_ Wartbarkeit, isolierte Iteration.
_Trade-off:_ mehr Dateien, Include-Reihenfolge muss stimmen. Bei Editor-Komplexität dieser Größe lohnt sich der Schnitt.

---

## 9 · Stand & nächste Schritte

**Stand (ehrlich):**
Die Plattform ist technisch **fertig und produktiv** — sie läuft, wird gepflegt und vom Autor selbst zum Lernen benutzt. Inhaltlich deckt sie den N5-Kern ab (Kana vollständig, N5-Kanji vollständig, Vokabel-Coverage zuletzt bei knapp 80 % der offiziellen N5-Liste; die in der Projektdoku genannten Roh-Item-Zahlen — z. B. „47 Lektionen / 519 Vokabeln" — sind eine **Momentaufnahme von Mai 2026** und seither gewachsen). Das Produkt wird als Referenzprojekt **gratis** geschaltet; die Monetarisierung bleibt über den `price`-Mechanismus reaktivierbar (§8.1). Da damit kein realer Geld-Pfad mehr aktiv ist, sind die früher offenen Payment-Härtungen (z. B. Webhook-Signaturprüfung) faktisch entschärft statt offene Risiken.

**Bewusst zurückgestellte technische Schuld** (priorisiert: Features liefern vor Refactoring):
- `app/routes.py` ist mit ~4'900 Zeilen / ~129 Routen eine „Gott-Datei", die öffentliche Views, Admin-APIs, Quiz-, Progress- und Payment-Endpoints bündelt. Aufteilung in Blueprints ist eingeplant.
- Ein Admin-Endpoint ruft noch die alten Gemini-**Text**-Methoden auf und widerspricht damit der „Content nur via Claude"-Regel (§3). Toter Bild-Code (OpenAI `gpt-image-1-mini`) und nicht angebundene KI-Module (`ContentValidator`, `PersonalizedLessonGenerator`) sind Aufräum-Kandidaten.
- GCloud-Namensrelikte (`Dockerfile.cloudrun`, `K_SERVICE`-Checks) sind kosmetisch veraltet, funktional aber korrekt.
- Zeitzonen-Inkonsistenz: Streak/Aggregate rechnen in Europe/Zurich, `due_date` und die Daily-Bretter in UTC. Vereinheitlichung steht aus.

**Die eigentliche offene Front: Distribution.**
Der Code ist nicht das Engpass-Problem — die Reichweite ist es. Konkrete nächste Hebel: Suchmaschinen-Ranking für die Schweiz-Nische (statt Head-Terms zu jagen), ein Lifecycle-/Retention-Kanal (aktuell existiert außer Passwort-Reset keine ausgehende Kommunikation; die Web-Push-Pipeline ist noch toter Code), und programmatische SEO-Hubs. Das sind Wachstums-, keine Engineering-Blocker — und genau die Art Problem, die ein fertig gebautes Produkt überhaupt erst sichtbar macht.

---

_Diese Case-Study beschreibt den Code-Stand, wie er ist (verifiziert gegen die Quelldateien und die Ist-Zustand-Dokumentation unter `docs/ist-zustand/`), nicht eine geschönte Soll-Version. Roh-Inhaltszahlen sind als datierte Momentaufnahmen gekennzeichnet; es werden keine Nutzer- oder Umsatzzahlen behauptet._
