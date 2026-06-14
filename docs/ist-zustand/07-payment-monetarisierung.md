# 07 · Zahlungen & Monetarisierung
_Stand: 2026-06-14 · Commit 2947710 · Teil der Ist-Zustand-Dokumentation_

## Zweck

Dieses Subsystem deckt den gesamten Bezahl- und Monetarisierungs-Pfad der Plattform ab: die Auswahl des Zahlungs-Providers (Payrexx / PostFinance-Legacy / Mock), das Erstellen von Checkout-Gateways, das Tracking von Transaktionen, die Freischaltung gekaufter Lektionen/Kurse via Webhook sowie das N5-Bundle als gebündeltes Verkaufsprodukt. Daneben definiert es die Zugriffslogik, die entscheidet, ob eine Lektion kostenlos, gekauft, im Bundle enthalten oder premium-pflichtig ist.

## Komponenten

| Datei | Zeilen | Rolle |
|---|---|---|
| `app/services/payment_factory.py` | 107 | Wählt anhand von `PAYMENT_PROVIDER` / `MOCK_PAYMENTS_ENABLED` den Service (payrexx/postfinance/mock); Fallback auf Mock |
| `app/services/payrexx_payment_service.py` | 257 | Payrexx REST-API-Integration (Gateway erstellen, Status, Webhook-Signatur, Status-Mapping) |
| `app/services/mock_payment_service.py` | 197 | Dev-Mock: legt Kauf-Datensätze sofort an, ohne echte Zahlung; enthält zusätzlich eine eigene Legacy-Factory |
| `app/services/payment_service.py` | 436 | PostFinance-Checkout-Integration (Legacy, SDK `postfinancecheckout`) inkl. `EnhancedPostFinanceService`, Fehler-Handler, Timeout-Check |
| `app/services/transaction_service.py` | 154 | `PaymentTransaction`-CRUD; State-Updates triggern Kauf-Freischaltung bzw. Fehlerbehandlung |
| `app/bundle_routes.py` | 169 | Blueprint `bundle_bp`: Verkaufsseite `/n5-bundle` + Kauf-API `/api/bundles/n5/purchase` |
| `app/services/bundle_service.py` | 69 | N5-Bundle-Logik: dynamischer Preis, Course-Lookup, `user_needs_bundle_hint` |
| `app/services/coverage_service.py` | 92 | JLPT-Coverage (DB vs. canonical Listen) für Bundle-Pricing und Verkaufsseite |
| `app/routes.py` (Kauf-Routen) | 4'863 (gesamt) | Kauf-Seite + Kauf-/Status-/Cancel-/Webhook-/Purchase-APIs (Zeilen 1243–3815) |
| `app/models.py` (Modelle) | — | `Lesson`, `Course`, `LessonPurchase`, `CoursePurchase`, `PaymentTransaction` + `lesson_type`-Event |
| `app/templates/purchase.html` | 436 | Single-Lektion-Checkout-Seite |
| `app/templates/lesson_paywall.html` | 388 | Paywall-Conversion-Seite bei nicht zugänglicher Paid-Lektion |
| `app/templates/payment_success.html` | 106 | Erfolgs-Redirect-Seite mit Status-Verifizierung per JS |
| `app/templates/payment_failed.html` | 137 | Fehlschlag-Redirect-Seite mit Status-Verifizierung per JS |
| `app/templates/bundles/n5_bundle.html` | 527 | N5-Bundle-Verkaufsseite |

Aktive Konfiguration: `app/__init__.py:151` setzt `PAYMENT_PROVIDER` standardmässig auf `mock` (überschreibbar via Env). `PAYREXX_INSTANCE`/`PAYREXX_API_SECRET`/`PAYREXX_WEBHOOK_SECRET` werden aus der Env gelesen (`app/__init__.py:152-154`).

---

## Payment-Services

### Factory (`app/services/payment_factory.py`)

`get_payment_service()` (`app/services/payment_factory.py:105`) delegiert an `PaymentServiceFactory.get_service()`. Entscheidungslogik:

```
MOCK_PAYMENTS_ENABLED=true (Env oder config)? ─ ja ─→ MockPaymentService
        │ nein
        ▼
PAYMENT_PROVIDER == 'payrexx'?
        │ ja ─→ Credentials (INSTANCE + API_SECRET) vorhanden?
        │          ja  ─→ PayrexxPaymentService  (bei Init-Fehler → Mock)
        │          nein → MockPaymentService
        │
PAYMENT_PROVIDER == 'postfinance'?
        │ ja ─→ SPACE_ID + USER_ID + API_SECRET vorhanden?
        │          ja  ─→ EnhancedPostFinanceService  (bei Init-Fehler → Mock)
        │          nein → MockPaymentService
        │
        └─→ (sonst / kein Provider) MockPaymentService
```

Jeder Service implementiert dieselbe Schnittstelle: `create_lesson_transaction(user, lesson)`, `create_course_transaction(user, course)`, `generate_payment_page_url(transaction_id)`, `get_transaction_status(transaction_id)`.

### Payrexx (`app/services/payrexx_payment_service.py`)

- API-Version `v1.14`, Auth via Header `X-API-KEY` (`_headers()`, Zeile 36). Basis-URL `https://api.payrexx.com/v1.14`, Endpoints als `…/Gateway/?instance=<instanz>` (`_url()`, Zeile 42).
- **Gateway erstellen** (`_create_gateway`, Zeile 45): POST auf `Gateway` mit `amount` (in Rappen), `currency=CHF`, `purpose`, `referenceId` (Format `lesson_<id>_user_<id>` bzw. `course_<id>_user_<id>`), Redirect-URLs (`successRedirectUrl`/`failedRedirectUrl`/`cancelRedirectUrl`) und `pm: [twint, visa, mastercard, apple-pay, google-pay]`. Rückgabe enthält `id` (Gateway-ID = interne `transaction_id`) und `link` (Checkout-URL).
- **Status prüfen** (`get_transaction_status`, Zeile 183): GET `Gateway/<id>`, mappt Payrexx-Status via `_map_status` (Zeile 239) auf interne Zustände (`confirmed→COMPLETED`, `waiting→PENDING`, `cancelled→CANCELLED`, `declined→DECLINED`, `refunded→REFUNDED`, `error/expired→FAILED`, …; Default `PENDING`).
- **Webhook verifizieren** (`verify_webhook_signature`, Zeile 223): HMAC-SHA256 über den Roh-Payload mit `PAYREXX_WEBHOOK_SECRET`, `hmac.compare_digest` gegen die übergebene Signatur. Ohne konfiguriertes Secret gibt die Methode `False` zurück.

### Mock (`app/services/mock_payment_service.py`)

- `create_lesson_transaction` / `create_course_transaction` legen **direkt** einen `LessonPurchase`/`CoursePurchase` mit `transaction_state='COMPLETED'` und zufälliger `provider_transaction_id` an und committen sofort (keine `PaymentTransaction`). Doppelkauf wird per `filter_by` geprüft (`DUPLICATE_PURCHASE`).
- `generate_payment_page_url` gibt direkt die Erfolgs-URL (`routes.payment_success`) zurück.
- `get_transaction_status` liefert immer `COMPLETED`.
- Die Datei enthält zusätzlich eine eigenständige `MockPaymentFactory` + `get_payment_service()` (Zeile 160–197), die auf PostFinance-Config prüft — eine zweite, ältere Factory parallel zur `payment_factory.py`.

### PostFinance-Legacy (`app/services/payment_service.py`)

- `PostFinanceService` nutzt das SDK `postfinancecheckout` (`Configuration`, `TransactionServiceApi`, …). `create_lesson_transaction`/`create_course_transaction` bauen `LineItem` + `TransactionCreate` mit `meta_data` (lesson_id/course_id/user_id/item_type) und rufen `transaction_service.create(space_id, …)`.
- `generate_payment_page_url` ruft `TransactionPaymentPageServiceApi.payment_page_url`. `get_transaction_status` liest die Transaktion. `_parse_api_error` (Zeile 251) strukturiert PostFinance-Client-/Server-Fehler.
- `PaymentErrorHandler` (Zeile 285) liefert benutzerfreundliche Meldungen und enthält `check_transaction_timeouts` — markiert `PENDING`-Transaktionen älter als `PAYMENT_TIMEOUT_HOURS` (Default 1) als `TIMEOUT` (laut Kommentar als Cron/Background-Task gedacht; ein Aufrufer ist im Code nicht zu sehen).
- `EnhancedPostFinanceService` (Zeile 365) erweitert um `*_with_timeout`-Methoden und ist die von `payment_factory.py` instanziierte Klasse. Die Datei hat ebenfalls ein eigenes `get_payment_service()` (Zeile 404).

### Transaction-Service (`app/services/transaction_service.py`)

- `create_payment_transaction(transaction_id, user, item_type, item_id, amount)` legt eine `PaymentTransaction` mit `state='PENDING'`, `currency='CHF'` und `transaction_metadata` an.
- `update_transaction_state(transaction_id, new_state, webhook_data=None)` (Zeile 46): sucht die Transaktion, setzt den neuen Status. Bei `COMPLETED`/`FULFILL` → `_complete_purchase` (legt `LessonPurchase`/`CoursePurchase` an, falls noch keiner existiert; Zeile 84). Bei `FAILED`/`DECLINE`/`VOIDED` → `_handle_failed_payment` (nur Logging). `webhook_data` wird auf der Transaktion gespeichert.
- `get_user_transactions` / `get_transaction_by_id` für Abfragen.

---

## Kauf-Routen (`app/routes.py`)

| Route | Methode | Auth | Zweck |
|---|---|---|---|
| `/purchase/<lesson_id>` (`purchase_lesson_page`, :1243) | GET | login | Rendert `purchase.html`; Redirects bei bereits-besessen / gratis-zugänglich / nicht kaufbar |
| `/api/lessons/<lesson_id>/purchase` (`purchase_lesson`, :3465) | POST | login | CSRF-Check → Gateway erstellen → `PaymentTransaction` anlegen → `payment_url` zurück (201) |
| `/api/courses/<course_id>/purchase` (`purchase_course`, :3376) | POST | login | Analog für Kurse |
| `/api/payment/status/<transaction_id>` (`get_payment_status`, :3554) | GET | login | Prüft Status beim Provider, syncronisiert lokalen `state` |
| `/api/payment/cancel/<transaction_id>` (`cancel_payment`, :3602) | POST | login | CSRF-Check; setzt eigene PENDING-Transaktion auf `CANCELLED` |
| `/payment/success` (`payment_success`, :3650) | GET | — | Rendert `payment_success.html` |
| `/payment/failed` (`payment_failed`, :3655) | GET | — | Rendert `payment_failed.html` |
| `/api/payment/webhook/payrexx` (`payrexx_webhook`, :3660) | POST | `@csrf.exempt` | Webhook: Signatur prüfen → Status mappen → `update_transaction_state` |
| `/api/user/purchases` (`get_user_purchases`, :3726) | GET | login | Liste der eigenen `LessonPurchase` |
| `/api/lessons/<lesson_id>/purchase-status` (:3741) | GET | login | Ob/wann/zu-welchem-Preis gekauft |
| `/api/admin/purchases` (:3762), `/api/admin/lessons/<id>/purchases` (:3790), `/api/admin/revenue-stats` (:3816) | GET | admin | Admin-Auswertung von Käufen/Umsatz |

### Kauf-Flow (Single-Lektion, Provider = Payrexx)

1. **Klick** „Jetzt kaufen" auf `purchase.html`. JS verlangt akzeptierte AGB-Checkbox, dann `fetch POST /api/lessons/<id>/purchase` mit Header `X-CSRFToken` (`purchase.html:393`).
2. **Backend** (`purchase_lesson`, :3465): CSRF prüfen; `is_purchasable`/`price>0` prüfen; Doppelkauf prüfen. `get_payment_service()` → `create_lesson_transaction` erzeugt Payrexx-Gateway. `transaction_service.create_payment_transaction(...)` legt `PaymentTransaction` (state `PENDING`) an. `generate_payment_page_url` liefert die Checkout-URL.
3. **Redirect**: JS setzt `window.location.href = result.payment_url` → Payrexx-Checkout (TWINT/Karten/Apple-Google-Pay).
4. **Zahlung** auf Payrexx; danach Redirect zurück auf `successRedirectUrl` (`/payment/success`) bzw. `failedRedirectUrl` (`/payment/failed`).
5. **Webhook** (parallel/asynchron): Payrexx POSTet an `/api/payment/webhook/payrexx`. Signatur wird per HMAC-SHA256 geprüft (`routes.py:3675`). Gateway-ID wird aus `invoice.paymentRequestId` / `paymentLinkId` / `transaction.paymentRequestId` / `transaction.id` (Fallback) bestimmt. Status → `_map_status` → `update_transaction_state(int(gateway_id), internal_state, webhook_data=data)`.
6. **Freischaltung**: Bei `COMPLETED` legt `_complete_purchase` den `LessonPurchase` an → die Lektion ist via `Lesson.is_accessible_to_user` zugänglich.

Die Erfolgsseite ruft zusätzlich client-seitig `/api/payment/status/<tx>` auf (falls `transaction_id` als Query-Param vorhanden), um den Status zu verifizieren und anzuzeigen (`payment_success.html:37`). Im **Mock-Modus** ist Schritt 2 bereits der vollständige Kauf (Datensatz wird sofort angelegt) und `payment_url` zeigt direkt auf `/payment/success`.

### Sequenz-Diagramm (Payrexx, inkl. Webhook)

```
Browser            routes.py (Flask)        payment_factory     PayrexxService      Payrexx-API/Checkout    transaction_service / DB
  |  POST /api/lessons/<id>/purchase             |                    |                    |                       |
  |  (X-CSRFToken, {})  ----------------------->|                    |                    |                       |
  |                     CSRF + is_purchasable    |                    |                    |                       |
  |                     + Doppelkauf-Check       |                    |                    |                       |
  |                     get_payment_service() -->|                    |                    |                       |
  |                                              |  PayrexxService -->|                    |                       |
  |                     create_lesson_transaction --------------------> POST /Gateway ---->|                       |
  |                                              |                    |   {id, link} <-----|                       |
  |                     create_payment_transaction -------------------------------------------------------------> INSERT PaymentTransaction (PENDING)
  |                     generate_payment_page_url --------------------> GET /Gateway/<id> ->|                       |
  |  <--- 201 {payment_url, transaction_id} -----|                    |                    |                       |
  |  window.location = payment_url ------------------------------------------------------>| Checkout-Seite        |
  |                                              |                    |   Zahlung (TWINT/Karte) ---> verarbeitet   |
  |  <--- Redirect /payment/success -------------|                    |                    |                       |
  |                                              |                    |                    |                       |
  |          (asynchron) Payrexx --> POST /api/payment/webhook/payrexx (X-Webhook-Signature)                       |
  |                     HMAC-SHA256 prüfen       |                    |                    |                       |
  |                     _map_status(status)      |                    |                    |                       |
  |                     update_transaction_state ---------------------------------------------------------------> UPDATE state=COMPLETED
  |                                              |                    |                    |    _complete_purchase -> INSERT LessonPurchase
  |  GET /api/payment/status/<tx> (von success-Seite) ----> get_transaction_status -> GET /Gateway/<id> -> state   |
  |  <--- {state: COMPLETED, ...} ---------------|                    |                    |                       |
```

---

## Bundle (N5 Komplett)

Das N5-Bundle ist intern ein `Course` mit dem Titel **„JLPT N5 Komplett"** (`bundle_service.py:19`), angelegt via `scripts/setup_n5_bundle.py`. Es nutzt die bestehende Course-Kauf-Pipeline (`CoursePurchase`, Webhook, `transaction_service`).

### `app/services/bundle_service.py`
- `get_n5_bundle_price()` (Zeile 31): liefert `(price, label)`. **Dynamischer Preis** — solange die **Vokabel-Coverage < 80 %** (`EARLY_BIRD_THRESHOLD_PCT`) gilt Early-Bird **CHF 9.90**, danach regulär **CHF 14.90**. Schwelle bewusst an Vokabeln (nicht Kanji) gekoppelt.
- `get_n5_bundle_course()` (Zeile 43): Course per Titel; `None`, wenn Setup-Skript noch nicht lief.
- `user_needs_bundle_hint(user)` (Zeile 48): `False` für Admins und Bundle-Besitzer; `True` für Gäste und alle anderen. **Single Source of Truth** für Navbar-Hint (Context-Processor `app/__init__.py:337` → `show_bundle_hint`), Startseiten-Banner und `/learn/n5`.
- Einzel-Lektion-Referenzpreis `SINGLE_LESSON_PRICE_CHF = 5.00` (Zeile 28, als Kommentar-Anker dokumentiert).

### `app/services/coverage_service.py`
`get_jlpt_coverage(level=5)` (Zeile 40) vergleicht alle DB-Vokabeln/-Kanji gegen canonical JLPT-Listen unter `.claude/skills/generate-lesson/sources/jlpt_n<level>_canonical.json` (Cache pro Level). Liefert `vocab_total/covered/pct`, `kanji_total/covered/pct`, `lessons_published_total`, `lessons_published_recent_7d` (über `LessonCategory.jlpt_level`) und `updated_at`. Fehlt die canonical Datei, wirft `_load_canonical` `FileNotFoundError`.

### `app/bundle_routes.py` (`bundle_bp`)
- `/n5-bundle` (`n5_bundle`, Zeile 34): rendert `bundles/n5_bundle.html` mit `coverage`, `price`, `price_label`, Early-Bird-/Regular-Preis, Threshold, `already_owned` (Admins gelten implizit als Besitzer), `bundle_available`.
- `/api/bundles/n5/purchase` (`n5_bundle_purchase`, Zeile 68, `@login_required`): CSRF-Check (Header `X-CSRFToken`); verlangt `accepted_terms=true` im JSON-Body (sonst `TERMS_NOT_ACCEPTED`); prüft Existenz (`BUNDLE_NOT_CONFIGURED`, 503) und Doppelkauf. Setzt **in-memory** `bundle_course.price = price` (dynamischer Preis, **kein DB-Commit** — DB behält Anker-Preis), erstellt via `create_course_transaction` Gateway + `PaymentTransaction`, hängt Metadaten `{bundle: 'n5', price_label}` an und gibt `payment_url` (201) zurück.

### Template `bundles/n5_bundle.html`
527 Zeilen. Enthält JSON-LD (`Product`/`BreadcrumbList`), Coverage-Balken (Vokabel-/Kanji-Fortschritt aus `coverage`), Early-Bird-Trigger-Hinweis, Preis-Block (durchgestrichener Regulärpreis bei Early-Bird), AGB-/Widerruf-Checkbox (aktiviert den Kauf-Button), Trust-Zeile (Payrexx, 30 Tage Geld zurück), lokaler Preisanker (Klubschule-Vergleich). JS (Zeile 484, nur wenn eingeloggt + Bundle verfügbar + nicht besessen): Checkbox aktiviert Button, Klick → Plausible-Event `checkout_start` → `fetch POST /api/bundles/n5/purchase` mit `{accepted_terms:true}` → Redirect auf `payment_url`. Gäste sehen Register-/Login-CTAs (`next=request.path`).

---

## Templates (Single-Checkout + Paywall + Ergebnis)

- **`purchase.html`** (436): „Ink-on-Washi"-Single-Checkout. Breadcrumb, Lektions-Kopf (Thumbnail/Titel/Meta-Chips), Preis-Block (CHF, formatiert), Benefit-Liste, Upsell-CTA zum Bundle (`bundle.n5_bundle`), Zahlungsmethoden-Radio (nur Payrexx), AGB-/Datenschutz-/Widerruf-Checkbox (`required`, mit Widerrufsverzicht), Kauf-Button. Processing- + Success-Modal (Bootstrap-Markup für JS). JS: `fetch POST /api/lessons/<id>/purchase` → Redirect auf `payment_url`, Fehler werden inline angezeigt.
- **`lesson_paywall.html`** (388): Conversion-Seite, wenn eine Paid-Lektion nicht zugänglich ist (von `view_lesson`, `routes.py:1309` gerendert). Breadcrumb zum Modul, Lektionstitel, zwei Optionen — **Bundle** (mit `bundle_price`, `paid_total` „weitere paid N5-Lektionen freigeschaltet", Link zur Bundle-Seite) und **Einzelkauf** (Link auf `purchase_lesson_page`). Für Gäste: Register-/Login-CTAs mit `next=request.path`. Kein eigener Kauf-Call — leitet auf Bundle- bzw. Purchase-Seite.
- **`payment_success.html`** (106): `noindex,follow`. Erfolgsmeldung + CTA „Zu meinen Lektionen". JS verifiziert bei vorhandenem `transaction_id`-Query-Param via `/api/payment/status/<tx>` und zeigt `COMPLETED`/`PENDING`/unklar an.
- **`payment_failed.html`** (137): `noindex,follow`. Fehlschlag-Erklärung, „Erneut versuchen"/„Lektionen ansehen". JS prüft Status (`FAILED`/`DECLINE`/`VOIDED`/`TIMEOUT`/`PENDING`) und liest optionale `error_code`/`error_message`-Query-Params.

---

## Preis- / Monetarisierungslogik

- **Felder** (`app/models.py`): `Lesson.price` (Float, Default `0.0`), `Lesson.is_purchasable` (Bool, Default `False`), `Lesson.lesson_type` (String). `Course` hat dieselben Preis-Felder. Käufe: `LessonPurchase`/`CoursePurchase` mit `price_paid`, `purchased_at`, `provider_transaction_id`, `transaction_state`, je `UniqueConstraint(user_id, item_id)` und FK `ondelete='RESTRICT'`. `PaymentTransaction` mit eindeutiger `transaction_id` (BigInteger), `item_type`/`item_id`, `state`, `webhook_data`/`transaction_metadata` (JSON).
- **`lesson_type` automatisch** (`models.py:1538`): SQLAlchemy-Event `before_insert`/`before_update` setzt `lesson_type='free'` bei `price==0.0`, sonst `'paid'`.
- **Zugriffslogik** `Lesson.is_accessible_to_user(user)` (`models.py:793`):
  - Gast: nur wenn `price==0.0` **und** `allow_guest_access` → frei; sonst „Login required".
  - Admin: immer Zugriff (Dogfood).
  - `price==0.0`: frei, sofern Voraussetzungen (`prerequisites`) abgeschlossen.
  - Paid (`is_purchasable`): Zugriff bei direktem `LessonPurchase` **oder** über einen gekauften `Course` (`CoursePurchase`), jeweils nach Voraussetzungs-Check; sonst „Kauf erforderlich (CHF …)".
  - Legacy: `lesson_type=='premium'` + `user.subscription_level != 'premium'` → „Premium-Abo erforderlich".
- **Premium-Abo**: `User.subscription_level` (Default `'free'`, `models.py:16`). Dekorator `premium_required` (`routes.py:37`) blockt Nicht-Premium-User. Im aktiven Verkaufspfad (Lektion/Bundle) ist Premium nicht der primäre Mechanismus — der Premium-Check ist als Legacy-Zweig in `is_accessible_to_user` markiert.
- **Pricing-Strategie (kurz, aus Code)**: Einzel-Lektion CHF 5.00 (Referenz in `bundle_service.py`); N5-Bundle Early-Bird CHF 9.90 / regulär CHF 14.90, Umschaltung bei ≥ 80 % Vokabel-Coverage.

---

## Zusammenspiel

**Eingehend:**
- `view_lesson` (`routes.py:1273`) rendert bei nicht zugänglicher Paid-Lektion `lesson_paywall.html` statt Redirect; nutzt `bundle_service.get_n5_bundle_price()` und zählt paid N5-Lektionen.
- Der Context-Processor (`app/__init__.py:334`) ruft `user_needs_bundle_hint` und liefert site-weit `show_bundle_hint` an Navbar/Templates.
- Admin-Dashboard/Statistik konsumieren `/api/admin/purchases`, `/api/admin/lessons/<id>/purchases`, `/api/admin/revenue-stats`.

**Ausgehend:**
- HTTP zu Payrexx (`api.payrexx.com/v1.14`) bzw. PostFinance-SDK; Browser-Redirect auf die externe Checkout-Seite.
- Webhook-Eingang von Payrexx auf `/api/payment/webhook/payrexx`.
- Kauf-Freischaltung schreibt `LessonPurchase`/`CoursePurchase`, die wiederum die Lektions-/Kurs-Zugriffslogik (`is_accessible_to_user`) und das Lern-Subsystem (Lektion sichtbar/startbar) speisen.
- Templates verlinken auf `legal.agb`/`legal.datenschutz`/`legal.widerruf` (AGB/Widerruf), `routes.register`/`routes.login` (Gast-Funnel), `bundle.n5_bundle` (Upsell) und `routes.view_lesson`/`routes.my_lessons` (nach Kauf).
- `coverage_service` liest canonical JLPT-Listen aus dem `generate-lesson`-Skill-Verzeichnis (DB-Vergleich).

---

## Beobachtungen (Ansatzpunkte)

- Es existieren **drei** Factory-/`get_payment_service`-Implementierungen parallel: `payment_factory.py` (aktiv genutzt von den Routen), `mock_payment_service.py:MockPaymentFactory` (Zeile 160) und `payment_service.py:get_payment_service` (Zeile 404). Die letzten beiden prüfen nur PostFinance/Mock und kennen Payrexx nicht.
- `app/__init__.py:151` setzt `PAYMENT_PROVIDER` per Default auf `mock`; ob in Produktion `payrexx` gesetzt ist, ist nur aus der `.env` ersichtlich (nicht im Code). Ohne Payrexx-Credentials fällt die Factory still auf Mock zurück (`payment_factory.py:71`).
- Im **Mock-Modus** wird keine `PaymentTransaction` angelegt (der Kauf entsteht direkt als `LessonPurchase`/`CoursePurchase`), während die Routen danach trotzdem `transaction_service.create_payment_transaction(...)` aufrufen — d. h. der Mock-Pfad in `purchase_lesson`/`purchase_course` erzeugt eine `PaymentTransaction` für eine zufällige Mock-`transaction_id`, zusätzlich zum bereits erstellten Kauf.
- `mock_payment_service.py:create_lesson_transaction` generiert die `mock_transaction_id` **zweimal** (Zeile 44 und 52); der in der `LessonPurchase` gespeicherte Wert unterscheidet sich vom zurückgegebenen (analog im Course-Pfad, Zeile 97/105).
- Der Payrexx-Webhook bestimmt die Gateway-ID über mehrere Fallback-Felder (`invoice.paymentRequestId` → … → `transaction.id`, `routes.py:3699`); der Kommentar weist darauf hin, dass `transaction.id` eine andere ID-Art ist und nur Fallback sein soll.
- Ist `PAYREXX_WEBHOOK_SECRET` nicht gesetzt, überspringt der Webhook-Endpoint (`routes.py:3676`) die Signaturprüfung komplett und verarbeitet den Payload ungeprüft.
- `_complete_purchase` (`transaction_service.py:84`) fügt den Kauf der Session hinzu, committet aber nicht selbst — der Commit liegt im aufrufenden `update_transaction_state` (Zeile 74).
- `PaymentErrorHandler.check_transaction_timeouts` (`payment_service.py:329`) ist als periodischer Job dokumentiert, im Code ist kein Scheduler/Aufrufer sichtbar; PostFinance-Code ist insgesamt als Legacy markiert, aber vollständig vorhanden.
- `lesson_paywall.html` und `purchase.html` enthalten umfangreiches Inline-CSS/-JS; die Texte/CTAs sind Deutsch, einzelne Service-Fehlertexte (`mock_payment_service`, Teile `is_accessible_to_user`) sind Englisch.
- Der Bundle-Preis wird beim Kauf nur in-memory auf den `Course` gesetzt (`bundle_routes.py:114`); `amount` in `PaymentTransaction` und der Payrexx-`amount` stammen daraus — die DB-`course.price` bleibt der Anker-/Regulärpreis.
- `app/routes.py` umfasst 4'863 Zeilen und vermischt View-Routen und Payment-APIs in einer Datei; die Bundle-Routen wurden bereits in ein eigenes Blueprint ausgelagert.
