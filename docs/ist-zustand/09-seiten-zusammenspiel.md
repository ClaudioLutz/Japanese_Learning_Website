# 09 · Seiten-Zusammenspiel: Navigation, Funnel & Datenfluss
_Stand: 2026-06-14 · Commit 2947710 · Teil der Ist-Zustand-Dokumentation_

> Dieses Dokument ist die **Querschnitts-Sicht**: Wie hängen die einzelnen Seiten zusammen — über die geteilte Navigation, den Conversion-Funnel (Gast → Konto → Kauf), die Rückführungs-Redirects und die seitenübergreifend geteilten Zustände. Den **Aufbau jeder einzelnen Seite** (Sektionen, Datenquellen, Zielgruppe) beschreibt → [03 · Öffentliche Seiten](03-oeffentliche-seiten.md), den Lektions-Viewer → [04](04-lernen-lektionen-quiz.md), SRS/Practice → [05](05-srs-review-practice.md), Auth → [06](06-auth-zugriffskontrolle.md), Payment → [07](07-payment-monetarisierung.md).

## Zweck

Beschreibt, welche Route welches Template rendert, welche rollenbasierten Verzweigungen es gibt (Gast vs. eingeloggt vs. Admin) und vor allem **wie die Seiten untereinander verlinkt sind** — von der anonymen Startseite bis zum Bundle-Kauf und in den täglichen Wiederhol-Loop.

## Gesamt-Seitenkarte (verdichtet)

```
                          ┌──────────────────────────────────────────────┐
                          │  base.html  (Top-Nav · Bottom-Nav · Footer)   │  ← jede Seite erbt davon
                          └──────────────────────────────────────────────┘
                                              │
        GAST                                  │                         EINGELOGGT
  ──────────────────                          │                  ───────────────────────────
   /  (Kana-Storm-Hero)                       │                   /  (Weiter-lernen-Hero)
     ├─ Spielende → /register?next=…          │                     ├─ Weiter lernen → /lessons/<id>
     ├─ „gratis Lektion" → /lessons/<id>      │                     └─ #lernpfad → /learn/n5/<slug>
     ├─ #lernpfad                             │
     ├─ /n5-bundle (CHF 9.90)                 │                   /lessons (Dashboard)
     └─ /practice/kana (Zuordnen)             │                     ├─ Weiter → /lessons/<id>
                                              │                     └─ „X fällig" → /review
   /lessons (Gast-Hero)                       │
     ├─ „Kostenlos starten" → /register       │                   /review  ⇄  /review/stats
     ├─ erste Gratis-Lektion → /lessons/<id>  │                     /review/browse  · /practice/kana*
     └─ /n5-bundle                            │                          (Login-Loop, @login_required)
                                              ▼
                              /lessons/<id>  (view_lesson)
                              ├─ zugänglich → lesson_view.html  → prev/next, Modul, /n5-bundle
                              ├─ paid+gesperrt → lesson_paywall.html
                              │     ├─ /n5-bundle   ├─ /purchase/<int:lesson_id>   └─ /register?next
                              └─ Login fehlt → /login?next=…

   FUNNEL-ENDE:  /n5-bundle ─POST /api/bundles/n5/purchase→ Payrexx ─→ /payment/success → /my-lessons
                 /purchase/<int:lesson_id> ─POST /api/lessons/<id>/purchase→ Payrexx ─→ /payment/success
                 (Webhook /api/payment/webhook/payrexx schaltet serverseitig frei)
```

## Komponenten

| Datei | Zeilen | Rolle |
|---|---|---|
| `app/templates/base.html` | 756 | Layout-Gerüst: Top-Nav, Mobile-Bottom-Nav, Footer, SEO-Meta, JSON-LD, Flash-Messages, SRS-Due-Badge-Loader |
| `app/routes.py` | 4'863 | Haupt-Blueprint `routes` (kein url_prefix): Views (index, lessons, view_lesson, …) + die meisten APIs vermischt |
| `app/srs_routes.py` | 1'480 | Blueprint `srs`: Review/Stats/Browse-Seiten + Kana-Practice/Storm-Seiten + alle SRS-/Kana-APIs |
| `app/bundle_routes.py` | 169 | Blueprint `bundle`: Verkaufsseite `/n5-bundle` + Buy-API |
| `app/legal_routes.py` | 58 | Blueprint `legal` (url_prefix `/legal`): Impressum, Datenschutz, AGB, Widerruf |
| `app/seo_routes.py` | 178 | Blueprint `seo`: `/robots.txt`, `/sitemap.xml`, `/favicon.ico` (CSRF-exempt) |
| `app/__init__.py` | (Auszug) | Blueprint-Registrierung + Context-Processor (`site_name`, `show_bundle_hint`, `current_year`, `n5_free_lesson_count`, SEO-Defaults) |
| `app/templates/index.html` | 1'372 | Startseite — rollenbasierter Hero (Gast = Kana-Storm-Spiel, eingeloggt = Weiterlern-Hero) + N5-Lernpfad |
| `app/templates/lessons.html` | 617 | Lektions-Katalog — rollenbasiert (Gast-Hero vs. Weiter-lernen-Dashboard) + kategoriegruppiertes Browse |
| `app/templates/lesson_view.html` | 4'772 | Lektions-Ansicht: Inhalt, Flip-Cards, Quiz, Fortschritt, Next-Up-Navigation |
| `app/templates/lesson_paywall.html` | 388 | Conversion-Seite bei paid+gesperrter Lektion (Bundle-CTA + Single-Kauf) |
| `app/templates/bundles/n5_bundle.html` | 527 | Bundle-Verkaufsseite „JLPT N5 Komplett" + Checkout-JS |
| `app/templates/_kana_storm_stage.html` | 297 | Geteiltes Kana-Storm-Markup (Hero, Vollbild-Seite, /daily) |

Weitere benutzersichtbare Templates: `learn_n5.html`, `module_detail.html`, `courses.html`, `course_view.html`, `my_lessons.html`, `user_profile.html`, `purchase.html`, `payment_success.html`, `payment_failed.html`, `register.html`, `login.html`, `forgot_password.html`, `reset_password.html`, `ueber.html`, `lernmethode.html`, `jlpt_n5_schweiz.html`, `review.html`, `stats.html`, `browse.html`, `practice_kana.html`, `practice_kana_game.html`, `practice_kana_storm.html`, `legal/*.html`, `errors/404.html`, `errors/500.html`. — `learn_path.html` liegt im Ordner, wird aber von **keiner** Route gerendert (ungenutzter Altbestand, verifiziert).

## Seiten und Routen (Inventar)

### Öffentliche / Marketing-Seiten (Blueprint `routes`, kein url_prefix)

| Route | Endpoint | Template | Zugriff | Quelle |
|---|---|---|---|---|
| `/` | `routes.index` | `index.html` | öffentlich | `app/routes.py:405` |
| `/home` | `routes.home_redirect` | — (301 → `/`) | öffentlich | `app/routes.py:306` |
| `/lessons` | `routes.lessons` | `lessons.html` | öffentlich | `app/routes.py:783` |
| `/lessons/<int:lesson_id>` | `routes.view_lesson` | `lesson_view.html` / `lesson_paywall.html` | gestaffelt | `app/routes.py:1273` |
| `/learn`, `/learn/n<level>` | `routes.learn_path` | `learn_n5.html` (nur N5; sonst 404) | öffentlich | `app/routes.py:999` |
| `/learn/n<level>/<slug>` | `routes.module_detail` | `module_detail.html` (1 Lesson → Redirect) | öffentlich | `app/routes.py:1049` |
| `/jlpt-n5-schweiz` | `routes.jlpt_n5_schweiz` | `jlpt_n5_schweiz.html` | öffentlich (SEO-Landing) | `app/routes.py:988` |
| `/ueber` | `routes.ueber` | `ueber.html` | öffentlich | `app/routes.py:967` |
| `/lernmethode` | `routes.lernmethode` | `lernmethode.html` | öffentlich | `app/routes.py:979` |
| `/courses` | `routes.courses` | `courses.html` | öffentlich | `app/routes.py:1121` |
| `/course/<id>` | `routes.view_course` | `course_view.html` | öffentlich | `app/routes.py:1185` |

### Auth / Konto (Blueprint `routes`)

| Route | Endpoint | Template / Verhalten | Zugriff | Quelle |
|---|---|---|---|---|
| `/register` (GET/POST) | `routes.register` | `register.html`; Erfolg → Auto-Login + Redirect | Gast | `app/routes.py:490` |
| `/login` (GET/POST) | `routes.login` | `login.html`; Erfolg → Admin-Index oder Index oder `next` | Gast | `app/routes.py:522` |
| `/logout` | `routes.logout` | Redirect → `/` | login_required | `app/routes.py:603` |
| `/forgot-password` | `routes.forgot_password` | `forgot_password.html` → Redirect `/login` | Gast | `app/routes.py:556` |
| `/reset-password/<token>` | `routes.reset_password` | `reset_password.html` → Redirect `/login` | Gast | `app/routes.py:578` |
| `/profile` | `routes.user_profile` | `user_profile.html` | login_required | `app/routes.py:610` |
| `/my-lessons` | `routes.my_lessons` | `my_lessons.html` | login_required | `app/routes.py:1128` |

### Kauf / Payment (Blueprint `routes` + `bundle`)

| Route | Endpoint | Template / Verhalten | Quelle |
|---|---|---|---|
| `/purchase/<int:lesson_id>` (Seite) | `routes.purchase_lesson_page` | `purchase.html` (Redirects falls schon gekauft/gratis) | `app/routes.py:1245` |
| `/payment/success` | `routes.payment_success` | `payment_success.html` | `app/routes.py:3651` |
| `/payment/failed` | `routes.payment_failed` | `payment_failed.html` | `app/routes.py:3656` |
| `/n5-bundle` | `bundle.n5_bundle` | `bundles/n5_bundle.html` | `app/bundle_routes.py:34` |
| `/api/bundles/n5/purchase` (POST) | `bundle.n5_bundle_purchase` | JSON; liefert `payment_url` für JS-Redirect | `app/bundle_routes.py:68` |

Die Buy-API gibt `payment_url` zurück, auf die das Bundle-Template per `window.location.href` weiterleitet (`app/templates/bundles/n5_bundle.html:513`). `purchase.html` macht dasselbe (`app/templates/purchase.html:405`).

### SRS / Practice (Blueprint `srs`, kein url_prefix)

| Route | Endpoint | Template | Zugriff | Quelle |
|---|---|---|---|---|
| `/review` | `srs.review_page` | `review.html` | **@login_required** | `app/srs_routes.py:157` |
| `/review/stats` | `srs.stats_page` | `stats.html` | **@login_required** | `app/srs_routes.py:231` |
| `/review/browse` | `srs.browse_page` | `browse.html` | **@login_required** | `app/srs_routes.py:406` |
| `/practice/kana` | `srs.practice_kana_page` | `practice_kana.html` | öffentlich | `app/srs_routes.py:825` |
| `/practice/kana/spiel` | `srs.practice_kana_game_page` | `practice_kana_game.html` | öffentlich | `app/srs_routes.py:836` |
| `/practice/kana/storm` | `srs.practice_kana_storm_page` | `practice_kana_storm.html` | öffentlich | `app/srs_routes.py:847` |
| `/daily` | (Kurz-URL) | `practice_kana_storm.html` (`kstorm_initial_tab='daily'`) | öffentlich | `app/srs_routes.py:861` |
| `/practice/kana/embed` | `srs.practice_kana_embed` | `_kana_game_embed_layout.html` | öffentlich | `app/srs_routes.py:871` |

Verifiziert: `/review`, `/review/stats`, `/review/browse` tragen alle den `@login_required`-Decorator (`srs_routes.py:158/232/407`); die Kana-Practice-Seiten sind bewusst öffentlich (Gast-Scope).

### Rechtliches (`legal`, `/legal`) & SEO (`seo`)

| Route | Inhalt | Quelle |
|---|---|---|
| `/legal/impressum`, `/datenschutz`, `/agb`, `/widerruf` | Rechtstexte | `app/legal_routes.py:41-56` |
| `/robots.txt` | dynamisch; bei `ROBOTS_INDEX=noindex…` sperrt alles | `app/seo_routes.py:33` |
| `/sitemap.xml` | statische Seiten + gast-zugängliche Lessons + Module (≥2 Lessons) + publizierte Courses | `app/seo_routes.py:89` |
| `/favicon.ico` | Icon | `app/seo_routes.py:21` |

## Navigation (geteilt über `base.html`)

### Top-Nav (`app/templates/base.html:124`–260)

Die Primärnavigation verzweigt rollenbasiert:

```
Top-Nav (sticky, backdrop-blur)
├── Brand „あ Japanese Learning / JLPT N5 · auf Deutsch"  → routes.index
├── Primary (links):
│   ├── Lernpfad            → routes.index#lernpfad        (immer)
│   ├── Wiederholen [Badge] → srs.review_page              (nur eingeloggt)
│   ├── あ Kana üben         → srs.practice_kana_page        (nur eingeloggt)
│   ├── Lektionen           → routes.lessons               (immer)
│   └── ⚡ N5 Komplett        → bundle.n5_bundle             (nur wenn show_bundle_hint)
└── Right:
    ├── eingeloggt:
    │   ├── 🔥 Streak-Pille (nur wenn current_streak > 0)
    │   └── User-Dropdown: Profil · Meine Lektionen · Kurse · Statistik ·
    │       Stöbern · (N5 Komplett, nur Mobile) · (Admin, nur is_admin) · Abmelden
    └── Gast:
        ├── Anmelden         → routes.login
        └── Kostenlos starten → routes.lessons(access='free')   [Shu-Primär-CTA]
```

Rollenbasierte Bedingungen:
- `current_user.is_authenticated` schaltet zwischen Konto-Dropdown und Gast-Auth-Buttons (`base.html:180` / `:242`).
- `show_bundle_hint` (Context-Processor, `app/__init__.py:337`, via `bundle_service.user_needs_bundle_hint`) blendet den „N5 Komplett"-Link für Nicht-Besitzer/Nicht-Admins ein; **fail-open auf `True`** (bei Fehler im Service sehen also auch Besitzer den CTA).
- `current_user.is_admin` blendet den Admin-Link + den Floating-Edit-Button ein.
- Das Due-Badge (`.nav-due-badge`) wird per JS aus `/api/srs/stats` befüllt (`base.html:717`) und auf Desktop + Mobile gespiegelt.
- Der Mobile-Hamburger erscheint **nur für Gäste** (`base.html:251`); Eingeloggte navigieren primär über die Bottom-Nav.

### Mobile-Bottom-Nav (`app/templates/base.html:630`–666)

```
eingeloggt:  Home · Lektionen · Wiederholen[Badge] · あ Kana · Profil
Gast:        Home · Lektionen · Anmelden · Registrieren
```

### Footer (`app/templates/base.html:736`–752)

Über uns · Lernmethode (SRS) · JLPT N5 Schweiz · Impressum · Datenschutz · AGB · Widerruf · Kontakt `mailto:info@japanese-learning.ch`

### Weitere globale Elemente
- Floating Admin-Edit-Button unten rechts, nur für Admins; Ziel ist die seitenspezifische `admin_edit_url`-Variable (z. B. `lessons.html:2`) oder Fallback `routes.admin_index` (`base.html:582`).
- Flash-Messages zentral im `<main>` (`base.html:570`).
- **Service-Worker-Registrierung erst ab `current_streak >= 3`** (`base.html:67`).

## Conversion-Funnel und Seiten-zu-Seiten-Verlinkung

### Gast-Einstieg (Startseite als Spielbühne)

`index.html` rendert für Gäste das **Kana-Storm-Spiel als Hero** (inline, kein iframe; `index.html:60`–138), darunter eine „Brücken-Leiste" Spielen → Hiragana-Lektion → N5-Pfad.

```
/ (Gast-Hero = Kana Storm Spiel)
├── Spielende-Screen → /register?next=/practice/kana/storm   (Konto-CTA im Stage)
├── „Hiragana-Lektion · gratis"  → guest_lesson_url  (= erste gratis+guest Lektion, sonst /lessons?access=free)
├── „N5-Pfad" Anker             → /#lernpfad
├── „N5 Komplett · CHF 9.90"    → bundle.n5_bundle
├── „Alle Lektionen ansehen"    → routes.lessons(access='free')
├── „Zum Zuordnungs-Spiel"      → srs.practice_kana_page
└── N5-Lernpfad-Module → routes.module_detail / routes.view_lesson (erste Gast-/erste Lektion)
```

`guest_lesson_url` wird in `index.html:11` aus `first_guest_lesson` abgeleitet, geliefert von `_build_n5_path_context()` (`app/routes.py:328`); Kriterium `price == 0 AND allow_guest_access` (`_first_guest_lesson`, `app/routes.py:314`).

### Lektion → Paywall → Register/Bundle

`view_lesson` (`app/routes.py:1273`) verzweigt bei Nichtzugriff (Detail der Kaskade → [06 · Auth & Zugriffskontrolle](06-auth-zugriffskontrolle.md)):
- paid + `is_purchasable` → rendert `lesson_paywall.html` (**kein Redirect**) mit Bundle-Preis + Single-Kauf-Tease.
- fehlender Login („Login required") → `redirect(login, next=request.url)`.
- sonst (fehlende Voraussetzungen) → Flash + `redirect(lessons)`.

`lesson_paywall.html` verlinkt: Bundle-Primär-CTA → `bundle.n5_bundle` (zweifach, `:256`/`:332`) · Einzelkauf → `routes.purchase_lesson_page` (`:355`) · Gast → `routes.register(next=request.path)` (`:303`) / `routes.login` (`:305`) · „Wer steht dahinter?" → `routes.ueber` · „Zurück zum Lernpfad" → `/#lernpfad`.

### Bundle-Kauf

```
bundle.n5_bundle (bundles/n5_bundle.html)
├── eingeloggt + nicht-Besitzer: Kauf → POST /api/bundles/n5/purchase → window.location.href = payment_url (:513)
├── Gast: „Kostenlos registrieren" → routes.register(next=request.path) (:340) · „Anmelden" → routes.login (:343)
├── „N5-Pfad" → routes.learn_path(level=5) (:301)
└── AGB → legal.agb · Widerruf → legal.widerruf
```
Der Kauf läuft intern über die bestehende **Course-Pipeline** (Bundle = Course „JLPT N5 Komplett"); dynamischer Preis aus `bundle_service.get_n5_bundle_price()` (`app/bundle_routes.py:113`), Doppelkauf wird geblockt (`:104`). Nach erfolgreicher Zahlung schaltet der Payrexx-Webhook (`routes.payrexx_webhook`, `app/routes.py:3662`) frei; Erfolgs-/Fehlerseiten sind `payment_success.html` (→ `my_lessons`) und `payment_failed.html`. Vollständiger Flow → [07 · Zahlungen](07-payment-monetarisierung.md).

### Register-/Login-Redirect-Logik (Funnel-Rückführung)

- `register` (`app/routes.py:490`): Erfolg → `login_user`, dann Redirect auf `next` (**Open-Redirect-Schutz: nur relativ**), sonst erste Gast-Lektion (`view_lesson`), sonst `/#lernpfad`.
- `login` (`app/routes.py:522`): Erfolg → `next` (relativ) oder Admin-Index (is_admin) oder Index.
- Die Register-CTA in `lesson_view.html:3352` setzt per JS `next` auf den aktuellen Pfad.

### Review-/Wiederhol-Loop (eingeloggt)

```
srs.review_page (review.html)
├── „Lektionen ansehen" → routes.lessons   ├── „Kana üben" → srs.practice_kana_page
├── „Detaillierte Statistik" → srs.stats_page   ├── „Karten durchstöbern" → srs.browse_page
└── APIs (JS): /api/srs/due · /rate · /stats · /stats/forecast · /achievements/notify · /api/tts
```
Einstiege in den Loop: Top-Nav „Wiederholen", Bottom-Nav, das Due-Badge, der eingeloggte Startseiten-Hero (`index.html:45`) und die „X fällig wiederholen"-Sekundär-CTA im `lessons.html`-Dashboard (`:72`).

### Lektions-Ansicht Next-Up-Navigation

`lesson_view.html` verlinkt am Ende auf `prev_lesson`/`next_lesson` (`:1851`/`:1857`), das `parent_module` (`module_detail`, `:1863`), den Hub (`/learn/n<level>` oder `routes.lessons`, `:1869`) und einen Bundle-CTA (`:1877`). Diese Nachbar-/Modul-Verweise werden serverseitig in `view_lesson` berechnet (`app/routes.py:1364`).

## Geteilte Zustände & seitenübergreifender Datenfluss

Was mehrere Seiten gemeinsam lesen/schreiben — die „Kopplungspunkte" zwischen den Seiten:

| Geteilter Zustand | Quelle/Speicher | Geschrieben von | Gelesen von |
|---|---|---|---|
| **Session / Login** | Flask-Login Cookie + `user_loader` | `/login`, `/register`, OAuth-Callback | jede Seite (rollenbasierte Verzweigung über `current_user`) |
| **Lektions-Fortschritt** | `UserLessonProgress.content_progress` (JSON-Text) | `/api/lessons/<id>/progress`, `/complete-remaining`, Reset-Routen | index (last/continue lesson), lessons-Dashboard, module_detail, my_lessons, lesson_view, /profile |
| **Streak / XP / Level** | `User.current_streak/total_xp/level` (+ `UserSRSSettings` Freeze) | `User.update_streak()` (Europe/Zurich) — getriggert von Progress + `/api/srs/rate` | Streak-Pille (Navbar), index-Hero, /profile, /review, /review/stats |
| **Due-Count (Karten fällig)** | berechnet via `srs_service.get_due_count` | — | `.nav-due-badge` (Top+Bottom-Nav, JS aus `/api/srs/stats`), lessons-Dashboard, /review |
| **Käufe / Freischaltung** | `LessonPurchase`, `CoursePurchase`, `PaymentTransaction` | Kauf-APIs + Payrexx-Webhook + Mock | `Lesson.is_accessible_to_user`, view_lesson, my_lessons, lesson_paywall, Bundle-Seite, `show_bundle_hint` |
| **`show_bundle_hint`** | Context-Processor `app/__init__.py:337` (`user_needs_bundle_hint`, fail-open=True) | — | Top-Nav, Konto-Dropdown, index, lessons, paywall, module_detail, lesson_view, learn_n5 |
| **N5-Pfad-Kontext** | `_build_n5_path_context()` (`app/routes.py:328`) | — | index, `/learn/n5` (learn_path), register-Fallback — einheitliche Modul-Reihenfolge + erste Gast-Lektion |
| **`n5_free_lesson_count`** | Context-Processor `app/__init__.py:315` (published + guest + free, EN+DE summiert) | — | Marketing-Texte site-weit (Single Source) |
| **Sichtbare Inhaltssprache** | `app.config['CONTENT_LANGUAGES']` (Default `german`) | Env | alle Lektions-/Katalog-Queries (filtert `instruction_language`) |

- **Vererbung:** Jede benutzersichtbare Seite erbt von `base.html` → Navigation, Footer, SEO-Meta, Due-Badge. Der Context-Processor in `app/__init__.py:299` liefert site-weit `site_name`, `site_description`, SEO-Defaults, `current_year`, `n5_free_lesson_count`, `show_bundle_hint`.
- **Externe Calls aus dem Frontend:** Bundle-/Einzelkauf leiten per JS auf die von Payrexx/Mock gelieferte `payment_url` weiter; der `review.html`-Loop ruft `/api/srs/*` und `/api/tts`; der Kana-Storm-Hero/-Seite nutzt den Gast-Endpoint `/api/practice/kana/session/public` und `/api/practice/kana/storm-daily`.
- **Blueprint-Topologie:** `routes` (kein Prefix, Views + viele APIs), `srs` (kein Prefix, Review/Practice + SRS-APIs), `bundle` (kein Prefix), `legal` (`/legal`), `seo` (kein Prefix, CSRF-exempt), `oauth`/`social_auth` (`/auth`), `debug`. Registrierung in `app/__init__.py:258`–284.
- **SEO-Kopplung:** `/home` → 301 auf `/` (Duplikat-Fix). `sitemap.xml` (`app/seo_routes.py:89`) listet nur öffentliche Marketing-Seiten, gast-zugängliche Lessons, Module mit ≥2 Lessons und publizierte Courses — paid-Lessons (noindex-Paywall) bleiben bewusst aussen vor.

## Beobachtungen (Ansatzpunkte)

- `app/routes.py` (4'863 Zeilen) vermischt Marketing-/Auth-/Lektions-Views mit umfangreichen REST-/Admin-/Payment-APIs in einem Blueprint ohne url_prefix; `app/srs_routes.py` (1'480) bündelt Seiten-Views und die komplette SRS-/Kana-API gleichermassen.
- `app/templates/lesson_view.html` ist mit 4'772 Zeilen das mit Abstand grösste Template (Markup + CSS + JS, inkl. JS-Redirect auf `/register?next=…` bei `:3352`).
- Die Startseite hält den Gast-Kana-Storm-Hero komplett inline (`index.html` 1'372 Zeilen, eingebetteter `<style>`-Block ab `:80`); dasselbe Stage-Markup wird über `_kana_storm_stage.html` zusätzlich von `practice_kana_storm.html` und `/daily` inkludiert.
- **Zwei separate Kana-Spiel-Pfade:** Zuordnungs-/Matching-Spiel unter `/practice/kana` (`practice_kana.html`/`practice_kana_game.html`) und Kana Storm (Hero + `/practice/kana/storm` + `/daily`). Der Hero verlinkt explizit „lieber zuordnen" zurück auf `practice_kana_page`.
- `learn_path.html` liegt im Template-Ordner, wird aber von keiner Route gerendert (`routes.learn_path` rendert `learn_n5.html`) — ungenutzter Altbestand (verifiziert).
- `show_bundle_hint` ist fail-open auf `True` (`app/__init__.py:340`): bei einem Fehler im `bundle_service` wird der Bundle-CTA auch Besitzern angezeigt.
- Der „N5 Komplett"-Bundle-Link erscheint an sehr vielen Stellen (Top-Nav, Konto-Dropdown, index, lessons, lesson_paywall zweifach, module_detail, lesson_view-Next-Up, purchase-Upsell, learn_n5) — teils durch `show_bundle_hint` gesteuert, teils unbedingt.
- Englische UI-/Flash-Reste in `purchase_lesson_page` („This lesson is not available for purchase.", „You already own this lesson!", `app/routes.py:1251`/`:1261`) neben sonst durchgehend deutschem UI.
- `base.html:254` trägt am Mobile-Burger sowohl ein dynamisches `:aria-label` (Alpine) als auch ein statisches `aria-label="Menü öffnen"` — doppeltes Attribut (verifiziert).
