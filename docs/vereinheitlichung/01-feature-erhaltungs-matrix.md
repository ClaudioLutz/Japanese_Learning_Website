# 01 · Feature-Erhaltungs-Matrix — das No-Loss-Rückgrat
_Generiert aus Workflow `vereinheitlichung-plan` (Run wf_7f2820ea-119) · 199 inventarisierte Features → 103 konsolidierte Zeilen · adversarial geprüft (3 Lenses, alle pass-with-fixes)._

> **Prime Constraint:** Kein nutzersichtbares Feature geht verloren. Jede Zeile bildet auf **genau eine** Ziel-Fläche ab. Die `retire`-Zeilen sind ausschliesslich toter/verbotener/duplizierter Code — keine echte Fähigkeit (Critic-verifiziert).
>
> **Verteilung:** keep 75 · merge 12 · redesign 9 · retire 7 = 103.

> **⚠ Korrektur aus adversarialer Prüfung (eingearbeitet):** `FM-catalog` ist aufgespalten. Die **Lern-Status-Badges** (done/started/open) auf `/lessons` bleiben **ungegated sichtbar — auch unter FREE_MODE** (keep). Nur das **„im Bundle"-Lock-Badge** wandert in das gegatete `_bundle_cta`-Makro (`show_bundle_hint AND not free_mode`). Sonst verschwände die Lernfortschritts-Anzeige im aktuellen Prod-Zustand = echte Regression.
> **⚠** `FM-resume` erhält explizit auch den **Neu-Nutzer-Empty-State** („Bereit für deine erste Lektion?") + Username/Streak-Begrüssung auf /mein-lernen. `FM-my-lessons`: `completion_rate` + `total_time_spent` ziehen mit nach /mein-lernen (fallen nicht zwischen die Flächen).

## RETIRE — toter/verbotener/duplizierter Code (keine Fähigkeit) (7)

### `FM-fill-blank-dead` — fill_blank-Bewertungszweig + KI-Generator-Proxy (toter/verbotener Typ)
- **Heute:** routes.py, ai_services, models.py-Kommentar
- **Ziel:** (entfernt)
- **Begründung:** A2-quiz-f06: verbotener Typ (CLAUDE.md), kein Render-Markup. Tote Code-Pfade entfernen — reduziert Verwirrung ueber erlaubte Typen.
- **Risiko:** Nur MC/true_false/matching bleiben erlaubt.

### `FM-kana-embed-dead` — Kana-Spiel iframe-Embed (verwaiste Route)
- **Heute:** /practice/kana/embed, _kana_game_embed_layout.html
- **Ziel:** (entfernt)
- **Begründung:** A3-kana-Surface (dead): index.html enthaelt kein <iframe> (grep 0). Storm-Hero hat es ersetzt. Setzt nie data-theme. Dead-Code-Cleanup.

### `FM-push-dead` — Web-Push subscribe/unsubscribe (kein Versand-Pfad)
- **Heute:** routes.py /api/user/push-*
- **Ziel:** (entfernt oder ruhend markiert)
- **Begründung:** A3-push-f51: toter Code — kein Versand-Pipeline (sw.js bereits geloescht laut Memory). Entfernen oder klar als ruhend markieren.
- **Risiko:** Falls Lifecycle-Push spaeter geplant: als bewussten Stub dokumentieren statt loeschen (open_decision-naher Nit).

### `FM-postfinance-dead` — PostFinance-Checkout (Legacy, kein aktiver Provider)
- **Heute:** payment_service.py
- **Ziel:** (entfernt)
- **Begründung:** A5-f27: vollstaendig vorhanden aber Provider auf Payrexx umgestellt; check_transaction_timeouts ohne Aufrufer. Echter Legacy-Dead-Code. Backend-Track.

### `FM-premium-proto` — Premium up/downgrade Prototyp (ohne Zahlung, keine UI)
- **Heute:** /upgrade_to_premium, /downgrade_from_premium, routes.py:712/726
- **Ziel:** (entfernt)
- **Begründung:** A5-f41: PROTOTYPE ONLY, keine UI-Entry-Points, Sicherheitsrisiko (Premium ohne Zahlung per direktem POST). Backend-Track.
- **Risiko:** Sicherheit: vor Loeschen pruefen ob irgendwo referenziert.

### `FM-dead-css` — Dead-Frontend-Code (lessons.css + learn_path.html + toter index-Lernpfad + .welcome-card)
- **Heute:** lessons.css, learn_path.html, index.html:902-1039, .modern-welcome-card
- **Ziel:** (entfernt)
- **Begründung:** A1-learn_path-dead + A4-Dead-Code: lessons.css tot seit /lessons-Redesign, learn_path.html von keiner Route gerendert, toter alter Lernpfad in index. Cleanup.
- **Risiko:** Vor Loeschung lessons.css-Referenzen verifizieren (Tests/Includes).

### `FM-prototypes` — Untracked Prototypen (learner_dashboard ON-SYSTEM + lesson_card_states + kana-storm OFF-SYSTEM)
- **Heute:** learner_dashboard_prototype.html, lesson_card_states_redesign.html, kana-storm-prototype (1).html
- **Ziel:** Ideen einarbeiten → dann loeschen (sauberer Git-Status)
- **Begründung:** 3 untracked HTML verletzen 'sauberer Git-Status'. learner_dashboard = Ziel-Fenster fuer /mein-lernen-Politur (einarbeiten). lesson_card_states (--color-*/Tabler) + kana-storm (--cream/--orange/Iowan) = OFF-SYSTEM: Ideen NUR nach Uebersetzung in --ink-/--shu + FA. Danach alle drei loeschen.
- **Risiko:** Prime-Constraint: gute Ideen erhalten (Reife-Skala, Audio-Player, Karten-Zustaende), Ausdruck verwerfen.


## MERGE — Funktion bleibt, wandert in geteilte Quelle/Komponente (12)

### `FM-kana-storm-hero` — Kana-Storm-Spielbuehne (Gast-Hero + /practice/kana/storm + /daily)
- **Heute:** / (index.html), /practice/kana/storm, /daily
- **Ziel:** _kana_storm_stage.html (geteiltes Partial)
- **Begründung:** A1-f02 + A3-f40 + A3-f41: 1 Stage-Markup, 3 Einbettungsorte. Stage-Stil aus index.html-Inline in custom.css/Partial ziehen → eine Quelle.
- **Risiko:** index.html-Inline-<style> haelt heute Stage-CSS; Pflege-Drift bis konsolidiert.

### `FM-resume` — Weiterlernen/Resume/Faellige/Streak (eingeloggter Lern-Status)
- **Heute:** / (index.html eingeloggt-Hero), /lessons (lp-continue), /mein-lernen (Heute-Hero)
- **Ziel:** /mein-lernen
- **Begründung:** A1-f05 + A1-f12 + A1-f19 + A2-dash-f01 + A3-f43: drei Flaechen zeigen redundant 'weiter lernen/faellig/Streak'. /mein-lernen = kanonische eingeloggte Lern-Heimat; index- und /lessons-Bloecke werden Teaser, die dorthin verlinken. EINE Resume-Quelle (dashboard_service.build_plan).
- **Risiko:** Prime-Constraint: alle drei Render-Inhalte erhalten, nur Heimat konsolidieren. continue_lesson-Logik muss site-weit aus einer Quelle kommen.

### `FM-n5-path` — N5-Lernpfad-Darstellung (#lernpfad + Hub + Pfad-Kontext)
- **Heute:** / (#lernpfad), /learn/n5, /learn/n5/<slug>
- **Ziel:** _n5_path-Makro (geteilt) → gerendert auf / , /learn/n5
- **Begründung:** A1-f06 + A1-f08 + A1-f09: _build_n5_path_context ist Single-Source, aber Markup je Seite dupliziert. Pfad-/Modul-Karten in geteiltes Makro (analog _module_banner.html). #lernpfad ggf. als Teaser auf /learn/n5.
- **Risiko:** _build_n5_path_context-Single-Source (index+learn_n5+register-Fallback) darf nicht brechen (Prime-Constraint).

### `FM-bundle-cta` — Bundle-CTA 'N5 Komplett' (>10 Streuorte, Gating-inkonsistent)
- **Heute:** base.html Nav, User-Dropdown, / (index), /lessons (Banner+Lock-Badge), lesson_paywall (2x), module_detail, lesson_view Next-Up, /purchase, /learn/n5, /jlpt-n5-schweiz
- **Ziel:** _bundle_cta-Makro (zentral, Gating show_bundle_hint AND not free_mode)
- **Begründung:** A1-f14 + A1-f15 + A2-nav-f02 + A5-f39: EIN gegatetes Makro ersetzt die Streuorte. Schliesst die free_mode-Luecken (index:331, base:193, lessons:137/282). In FREE_MODE konsistent ausblenden.
- **Risiko:** Prime-Constraint: free_mode-Reversibilitaet erhalten — Makro gated, nicht geloescht.

### `FM-dashboard-stats` — Mein-Lernen Statistik-Tabs (Tempo/Genauigkeit/Reife/Schwaechen/Achievements)
- **Heute:** /mein-lernen, /review/stats (gespiegelt)
- **Ziel:** /mein-lernen (Tabs als Sektion; /review/stats = Deep-Dive)
- **Begründung:** A1-f21 + A3-f46 + A3-stats-f08..f18: beide visualisieren dieselben SRS-Endpoints. Doppelte Level/XP-Berechnung (stats_page UND dashboard_routes.index) in einen Helper. _js_dashboard.html Dummy-Tabs an die echten /api/dashboard/stats-Daten anschliessen.
- **Risiko:** Stat-Logik-Dopplung/Drift zwischen stats_page und dashboard_service.stats_bundle.

### `FM-matching` — Matching-Interaktion (kanonisch: Tap-to-pair)
- **Heute:** lesson_view.html (<select>), pruefen_session.html (Tap), Kana-Matching (Tap)
- **Ziel:** _matching-Partial (Tap-to-pair, geteilt)
- **Begründung:** A2-quiz-f03 + A2-pruefen-f05 + A3-f37: drei Matching-Interaktionen fuer dieselbe Datenstruktur. Tap-to-pair als kanonisches Pattern; in lesson_view zurueckportieren.
- **Risiko:** DIVERGENZ heute — sorgfaeltig vereinheitlichen ohne Bewertungslogik zu brechen.

### `FM-quiz-eval` — Quiz-Antwort-Bewertung + XP/Streak (submit_quiz_answer)
- **Heute:** routes.py:4053 (inline), pruefen_service.evaluate_answer (main)
- **Ziel:** evaluate_answer (geteilte Funktion)
- **Begründung:** A2-quiz-f05 + A2-pruefen-f02: auf main als reine Funktion extrahiert; auf diesem Branch inline dupliziert. Nach Rebase: submit_quiz_answer ruft evaluate_answer, behaelt nur UPSERT/XP/show_solution.
- **Risiko:** Branch auf main rebasen, sonst Doppelpflege/Doppelbau.

### `FM-progress-reset` — Fortschritt zuruecksetzen (3 Implementierungen)
- **Heute:** routes.py:3091 (JSON), routes.py:3317 (Form), models.py:1206 reset()
- **Ziel:** UserLessonProgress.reset() (ORM, eine Quelle)
- **Begründung:** A2-prog-f04: dreifach dupliziertes Raw-SQL. Auf Modell-Methode konsolidieren, beide Endpoints darauf zeigen.

### `FM-front-romaji` — Front-Romaji-Toggle (zwei Render-Pfade: review + lesson_view)
- **Heute:** review.html, lesson_view.html Flip-Cards
- **Ziel:** geteilte Toggle-Logik + Karten-Komponente
- **Begründung:** A3-srs-f06 + A4-f14: zwei getrennte Karten-Render-Pfade mit je eigenem Toggle. Gemeinsame Karten-Komponente/CSS; bei Fixes BEIDE Pfade.
- **Risiko:** Prime-Constraint: beide Pfade muessen Fix erhalten (sonst 'fehlt immer noch').

### `FM-oauth` — Google-OAuth-Login (zwei parallele Pfade → einer kanonisch)
- **Heute:** /auth/complete/google-oauth2/ (oauth_bp), /auth/* (social-auth-Lib)
- **Ziel:** EIN OAuth-Pfad (oauth_bp faktisch aktiv)
- **Begründung:** A5-f11 + f12 + f13: zwei vollstaendige Pfade, beide legen User an + Raw-SQL-social_auth-Insert. Einen kanonisch waehlen, anderen entfernen; User-Anlage+social_auth in EINE ORM-Funktion. Backend-Track.
- **Risiko:** nutzersichtbarer Login bleibt erhalten; nur Doppelpfad aufloesen.

### `FM-payment-factory` — Payment-Factory (Provider-Wahl) — drei parallele Implementierungen
- **Heute:** payment_factory.py, mock_payment_service MockPaymentFactory, payment_service get_payment_service
- **Ziel:** payment_factory.py (alleinige Factory)
- **Begründung:** A5-f21 + Overlap: nur payment_factory.py kennt Payrexx. Zwei Legacy-Factories + PostFinance-Legacy entfernen. Backend-Track.

### `FM-tokens` — Kanonische Pigment-Tokens + Ink-Skala + Semantik-Layer + Shadow/Radius/Spacing/Type
- **Heute:** custom.css :root @11+@62, colors_and_type.css, _ml_styles.html (hermetisch)
- **Ziel:** custom.css EIN :root (von colors_and_type.css gespiegelt)
- **Begründung:** A4-f01..f05: Doppel-:root (Z.11+62) + hermetische Re-Deklaration in _ml_styles = drei Token-Quellen. Zu EINEM :root mergen. KEIN Partial deklariert Brand-Tokens neu (Lint-Regel). --color-*/--zen-* eliminieren/mappen.
- **Risiko:** B0-Crash: Merge kann CSS-Parsing brechen → Deck-Invariante (FM-deck-carousel) zuerst absichern+testen.


## REDESIGN — Fähigkeit bleibt, Oberfläche/Implementierung überarbeitet (9)

### `FM-catalog` — Kategoriegruppierter Lektions-Katalog (SSR) + Orphan-Auffanggruppe
- **Heute:** /lessons
- **Ziel:** /lessons
- **Begründung:** A1-f10: /lessons wird reiner Katalog/Browse (Dashboard-Teil wandert nach /mein-lernen, siehe FM-resume). Orphan-Auffanggruppe (id 0) MUSS bleiben — keine Lektion darf aus dem Katalog fallen (Prime-Constraint).
- **Risiko:** Doppelrolle Katalog+Dashboard entkoppeln, ohne die Gruppierung/Orphan-Logik zu verlieren.

### `FM-my-lessons` — Meine Lektionen (Aggregat: gekauft/freigeschaltet + Statistik)
- **Heute:** /my-lessons
- **Ziel:** /my-lessons
- **Begründung:** A1-f18: bleibt als Kauf-/Besitz-Aggregat, aber off-brand Periwinkle #667eea → --shu migrieren (A4-Befund). Lern-Statistik ueberschneidet /mein-lernen — hier nur Besitz/Ausgaben.
- **Risiko:** Abgrenzung zu /mein-lernen (Lernfortschritt) und /review/stats sauber halten.

### `FM-topnav` — Top-Nav (rollenbasiert)
- **Heute:** base.html
- **Ziel:** base.html
- **Begründung:** A1-f29: bleibt IA-Rueckgrat. /mein-lernen aus Dropdown in Primary-Nav heben (neue Lern-Heimat sichtbar machen). Bundle-CTA via FM-bundle-cta-Makro.
- **Risiko:** doppeltes aria-label Mobile-Burger fixen.

### `FM-bottomnav` — Mobile-Bottom-Nav (rollenbasiert)
- **Heute:** base.html
- **Ziel:** base.html
- **Begründung:** A1-f31 + A4-f18: bleibt. /mein-lernen-Eintrag aufnehmen; Touch-Target <44px erhoehen.

### `FM-conversation-page` — Conversation-Page-Render-Pfad (MNN-Layout)
- **Heute:** lesson_view.html
- **Ziel:** lesson_view.html (geteiltes Quiz-Partial)
- **Begründung:** A2-lv-f03: dupliziertes Quiz-Markup vs Normal-Page. Gemeinsames Quiz-Render-Partial extrahieren (siehe FM-quiz-markup).

### `FM-kana-grid-lesson` — Lektions-internes Kana-Grid-Spiel (eigener Render-Pfad)
- **Heute:** lesson_view.html
- **Ziel:** lesson_view.html (geteilte Kana-Engine-Adapter)
- **Begründung:** A2-lv-f09 + A3-f38: zweite Matching-Implementierung. Gemeinsame Spiel-Engine extrahieren; Lektion = duenner Config-Adapter (siehe FM-kana-matching).
- **Risiko:** Eigener Render-Pfad — leicht zu uebersehen (Prime-Constraint).

### `FM-quiz-markup` — Inline-Quiz multiple_choice + true_false + matching (Render)
- **Heute:** lesson_view.html (Normal + Conversation)
- **Ziel:** lesson_view.html (geteiltes Quiz-Partial)
- **Begründung:** A2-quiz-f01 + A2-quiz-f02 + A2-quiz-f03: matching nutzt <select>-Dropdowns (mobil schwach) → auf Tap-to-pair kanonisieren (siehe FM-matching). Quiz-Markup einmal als Partial.
- **Risiko:** matching-Datenstruktur (QuizOption.feedback-Mapping) erhalten.

### `FM-access-string` — view_lesson Verweigerungs-Routing via 'Login required'-Substring
- **Heute:** routes.py view_lesson, models.py
- **Ziel:** Reason-Code/Enum (statt Substring-Match)
- **Begründung:** A5-f20 + Overlap: fragile Kopplung Datenstring↔Kontrollfluss. Strukturierten Rueckgabewert einfuehren; UI-Strings durchgehend Deutsch.

### `FM-profile` — Profilseite (Header/Avatar + Statistik + Kategorie-Stats + Aktivitaet + Kaeufe)
- **Heute:** /profile, user_profile.html
- **Ziel:** /profile
- **Begründung:** A5-Profilseite + A5-f35: off-palette #666/#0d6efd/#28a745/#667eea → Tokens. --kon-Flip-Falle (Navy braucht --kon-100). Bleibt funktional.


## KEEP — bleibt erhalten (75)

| ID | Feature | Ziel-Fläche |
|---|---|---|
| `FM-home` | Rollenbasierte Startseite (Gast vs eingeloggt Verzweigung) | / (index.html) |
| `FM-bridge-bar` | Bruecken-Leiste 3 Schritte (Gast) | / (index.html) |
| `FM-pitch` | 'Vom Spiel zum System' Pitch/USP/Trust (Gast) | / (index.html) |
| `FM-home-redirect` | /home 301-Redirect | /home (301→/) |
| `FM-module-detail` | Modul-Detail mit 1-Lesson-Direktredirect | /learn/n5/<slug> |
| `FM-catalog-filter` | Client-Filter/Sort/View-Toggle auf SSR-Karten | /lessons |
| `FM-guest-hero-lessons` | Gast-Hero auf /lessons ('Gratis starten — N') | /lessons |
| `FM-courses` | Kurs-Uebersicht (SSR) mit free_mode-Preis-Pill | /courses |
| `FM-course-detail` | Einzelkurs-Detail mit Kaufstatus/Fortschritt | /course/<id> |
| `FM-dashboard-compass` | Mein-Lernen N5-Kompass (4 Saeulen + Per-Glyph-Detail) | /mein-lernen |
| `FM-dashboard-cando` | Mein-Lernen Can-Do + Vokabel-Themen + Grammatik + Wochenziel/Freezes | /mein-lernen |
| `FM-dashboard-numbers` | Mein-Lernen Zahlen-Kacheln (begonnene Items je Typ) | /mein-lernen |
| `FM-ueber` | Founder-Story / Ueber uns (free_mode-gated Wording) | /ueber |
| `FM-lernmethode` | Lernmethode (SRS/FSRS-Erklaerung) | /lernmethode |
| `FM-jlpt-landing` | SEO-Landing JLPT N5 Schweiz (JSON-LD) | /jlpt-n5-schweiz |
| `FM-legal` | Rechtstexte (Impressum/Datenschutz/AGB/Widerruf, free_mode-Wording) | /legal/* |
| `FM-errors` | Fehlerseiten 404/410/500 (Ink-on-Washi, noindex) | errors/* |
| `FM-seo-endpoints` | Dynamische robots.txt + sitemap.xml + favicon | seo_routes |
| `FM-user-dropdown` | User-Dropdown (eingeloggt) + Streak-Pille | base.html |
| `FM-footer` | Footer (Marketing+Legal-Links) | base.html |
| `FM-darkmode` | Dark Mode (oeffentlich): data-theme + Toggle + Pre-Paint + [data-theme=dark]-Tokensatz | custom.css [data-theme=dark] + base.html Toggle |
| `FM-due-badge` | SRS-Due-Badge (Top+Bottom-Nav) | base.html |
| `FM-admin-edit` | Floating Admin-Edit-Button | base.html |
| `FM-plausible` | Plausible-Analytics-Hook | base.html |
| `FM-free-mode` | FREE_MODE-Schalter (Bezahl-Schicht reversibel gegated) | __init__.py FREE_MODE + Context-Processor |
| `FM-bundle-hint-cp` | show_bundle_hint Context-Processor (Single-Source, fail-open→fail-closed) | __init__.py Context-Processor |
| `FM-free-count-cp` | n5_free_lesson_count Single-Source (Marketing-Texte) | __init__.py Context-Processor |
| `FM-guest-teaser` | Gast-Teaser-Landing (review_teaser) fuer login-pflichtige Lern-Seiten | review_teaser.html (teaser_page-Varianten) |
| `FM-lesson-view` | Lektions-Viewer (laden + Zugriffspruefung + Seiten-Pagination) | /lessons/<id> (lesson_view.html) |
| `FM-flip-cards` | Flip-Cards kana/kanji/vocabulary/grammar | lesson_view.html (geteilte Karten-Komponente) |
| `FM-deck-carousel` | Deck-Karussell (Confidence-Loop, .in-deck{display:none}) | lesson_view.html (geschuetzte, getestete Komponente) |
| `FM-text-block` | Text-Block (augmented_html / markdown + Block-Audio) | lesson_view.html |
| `FM-media` | Medien: Bild / Audio / Video (16:9 embed) | lesson_view.html |
| `FM-dialog-slideshow` | Dialog-Slideshow (Alpine, JSON-slides, Auto-Advance) | lesson_view.html |
| `FM-quiz-carousel` | Quiz-Karussell (Buendelung ≥2 interaktive Items) | lesson_view.html |
| `FM-progress-complete` | Content-Item als erledigt markieren + Fortschritts-Prozent (nur sichtbare Items) | lesson_view.html + Modell |
| `FM-complete-remaining` | Restliche passive Items abschliessen (Sicherheitsnetz) | lesson_view.html |
| `FM-time-tracking` | Zeit-Tracking via sendBeacon | lesson_view.html |
| `FM-tts` | Klick-Vorlesen / Karten-Audio (TTS, prerendered + Live) | /api/tts + zentrale playCardAudio-Strategie |
| `FM-lesson-nav` | Prev/Next + Parent-Modul-Linking im Viewer | lesson_view.html (Resume aus dashboard_service) |
| `FM-paywall` | Paywall (Conversion bei gesperrter Paid-Lektion) | lesson_paywall.html (gegated dormant) |
| `FM-single-checkout` | Einzel-Lektion-Checkout + Kauf-Flow | /purchase/<id> (gegated dormant) |
| `FM-bundle-sale` | N5-Bundle-Verkaufsseite + dynamischer Preis + Kauf-API | /n5-bundle (gegated dormant) |
| `FM-payment-result` | Zahlungs-Ergebnis (Erfolg/Fehlschlag) + Statusverifizierung | payment_success/failed.html |
| `FM-payrexx` | Payrexx-Gateway + Webhook-Freischaltung + Statusabfrage | payrexx_payment_service + transaction_service |
| `FM-access-cascade` | Zugriffslogik Lesson.is_accessible_to_user (Gast/Frei/Paid/Premium) | models.py is_accessible_to_user (zentral) |
| `FM-pruefen-start` | Pruefen-Startseite (Selbsttest-Konfig: Modus/Scope/Quick-Starts) | /pruefen (in IA aufnehmen) |
| `FM-pruefen-session` | Pruefen-Session-Buehne (Pool ohne Leak + Uebung/Pruefung + Tap-matching + Falsch-Filter) | /pruefen/test |
| `FM-srs-loop` | Taegliche Wiederholung SRS-Loop (rate/due/preview/reviewed-ids/new-cards) | /review |
| `FM-stats-deepdive` | Erweiterte Statistik /review/stats (11 Charts + Level/XP-Balken) | /review/stats (Deep-Dive) |
| `FM-browse` | Karten-Browser (Filter/Suche/Paginate + Detail/History + suspend/unsuspend/reset) | /review/browse |
| `FM-bulk-export` | Bulk-Aktion + CSV-Export | /review/browse |
| `FM-gamification` | Gamification (XP + Variable Reward + Karten-Stufen + Achievements + Toast) | /review + gamification_service |
| `FM-streak-level` | Streak + Streak-Freeze + Level/Level-Titel + DailyAggregate | models.py + gamification_service |
| `FM-kana-matching` | Kana-Matching (Setup + Vollbild-Spiel + Live-Vorschau + Gast-Scope) | /practice/kana (+ geteilte Spiel-Engine) |
| `FM-kana-drills` | Kana-Drills (Tages-Challenge + Schwache-Karten + Verwechslungs-Drill + Logging) | /practice/kana |
| `FM-kana-storm-game` | Kana-Storm Arcade-Loop + Storm-Daily (Wordle + Share) + Score/XP | /practice/kana/storm + _kana_storm_stage |
| `FM-auth-local` | Lokale Registrierung (Auto-Login) + Login (remember-me) + Logout | /register /login /logout |
| `FM-auth-security` | Auth-Sicherheit (Open-Redirect-Schutz + Lockout + Passwort-Regeln + next-Fallback) | routes + forms + models |
| `FM-password-reset` | Passwort vergessen + zuruecksetzen (Enumeration-Schutz, signiertes Token) | /forgot-password + /reset-password |
| `FM-decorators` | Auth-Decorators (@login_required + @admin_required + @premium_required) | routes.py Decorators |
| `FM-mock-payment` | Mock-Payment (Sofort-Kauf, Dev/Default) | mock_payment_service.py |
| `FM-payment-tracking` | PaymentTransaction-Tracking + State-Maschine + Cancel + Doppelkauf-Schutz | transaction_service.py |
| `FM-purchases-api` | Eigene Kaeufe + Purchase-Status + Admin-Umsatz-Auswertung | routes.py purchase-APIs |
| `FM-terms-gating` | AGB/Widerruf-Checkbox-Gating beim Checkout | Checkout (gegated dormant) |
| `FM-debug-payment` | Admin-Payment-Diagnose (/debug/*) | /debug/* (admin-only, robots-blockiert) |
| `FM-lesson-type` | lesson_type-Auto-Ableitung aus price (Modell-Event) | models.py Event |
| `FM-brandmark` | あ-Brandmark (Klee One) | base.html |
| `FM-buttons` | CTA-System (btn-shu Primaer + btn-ghost-jp Sekundaer + Eyebrow-Chip) | custom.css Komponenten |
| `FM-module-card` | Modul-Karte + is-next-Puls + Bundle-Hint-Banner + Stat-Pill | custom.css Komponenten (geteiltes Makro) |
| `FM-hero-visuals` | Hero-Visuals (hero-bg-jp + Browser-Frame Design-Moment + Modul-Banner-Bilder) | index.html + custom.css |
| `FM-quiz-feedback` | Quiz-Optionen + Feedback-Animationen (Score-Ring/XP-Balken) | custom.css Komponenten |
| `FM-motion-clamp` | prefers-reduced-motion-Clamp | custom.css |
| `FM-icons` | FA6-Solid-Icon-Layer (44 Templates) + funktionale Emoji | Font Awesome 6 Solid (fas) — einzige UI-Icon-Quelle |
| `FM-admin-shell` | Admin-Shell (Tailwind) + Command Palette (Ctrl+K) + Toast-Notifications | admin/* (paralleles System, separater Track) |
