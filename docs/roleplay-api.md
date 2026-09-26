# Rollenspiel-Tutor — API-Vertrag (Backend)

Stand: 2026-09-26. Backend: `app/roleplay_routes.py`, `app/services/roleplay_service.py`,
`app/services/roleplay_prefetch.py`.
Frontend baut gegen diesen Vertrag. Alle Texte für Nutzer kommen fertig auf Deutsch.

## Grundregeln

- **Sichtbarkeit:** Templates bekommen `roleplay_enabled` (Context-Processor). Nur wenn
  `True`, UI zeigen. Sonst liefern alle Routen **404** (auch ohne Login).
- **Login:** alle Routen `@login_required`. Ohne Login: **302** auf `/login?next=…`
  (bei `fetch` also `redirect: 'manual'` prüfen oder `resp.redirected`).
- **CSRF:** wie die übrigen JSON-APIs: Header `X-CSRFToken` mit dem Wert aus
  `<meta name="csrf-token">`. `Content-Type: application/json`.
- **Rate-Limit:** 20 Anfragen/Minute pro Nutzer → **429** (Flask-Limiter, HTML-Fehlerseite,
  kein JSON). Tageslimits kommen dagegen als JSON `limit_reached` (siehe unten).
- **Latenz:** Wahl eines Antwortvorschlags: meist **< 1 s** (Antwort vorausberechnet, siehe
  „Vorausberechnung"). Freitext = ein Modell-Aufruf, **~5–7 s** (Claude-Code-CLI mit
  `--effort low`), im Fehlerfall bis ~60 s. Frontend: Ladeindikator („Tanaka tippt …“) bei
  Freitext sofort, beim Sofort-Senden eines Vorschlags erst nach 1,2 s; Eingabe sperren,
  `fetch`-Timeout nicht unter 65 s.
- **Rollen:** Sprecher aus dem Dialog (`slides[].speaker`), genau die ersten zwei.
- **Gesprächslänge:** 4–8 Nutzerzüge. Nach dem 8. Zug beendet der Server selbst
  (`done: true`). XP (**25**) nur einmal pro Gespräch und erst ab 4 Nutzerzügen.

## Fehlerformat

Immer JSON `{ "error": "<code>", "message": "<deutscher Klartext>" }` — nie 500.

| HTTP | `error`            | Bedeutung / Frontend-Verhalten |
|------|--------------------|--------------------------------|
| 400  | `invalid_request`  | Eingabe fehlt/ungültig (leerer Text, >300 Zeichen, falsche Rolle). `message` anzeigen. |
| 403  | `no_access`        | Kein Zugang zur Lektion. |
| 404  | `not_found`        | Dialog/Lektion/Seite/Gespräch nicht gefunden (oder fremdes Gespräch). |
| 409  | `session_finished` | Gespräch ist schon beendet → Abschlussansicht zeigen. |
| 422  | `not_roleplayable` | Dialog hat keine zwei Rollen → Button nicht anbieten. |
| 429  | `limit_reached`    | Tageslimit des Nutzers (Gespräche 5, Nachrichten 60, Tutorfragen 20). |
| 502  | `upstream_error`   | Modell/Bridge antwortet nicht oder ist beschäftigt. Nutzerzug wurde **nicht** verbucht → „Nochmal senden“ anbieten. |
| 503  | `cost_cap`         | Globale Tageskappe erreicht (Kosten bzw. 1'500 Modell-Antworten/Tag inkl. Vorausberechnungen). |

## Objekte

```jsonc
// Session
{ "id": 12, "content_id": 345, "status": "active",          // active | completed | abandoned
  "role_user": "Gast", "role_bot": "Kellner",
  "goal_de": "Spiele Gast und führe das Gespräch …",
  "turn_count": 2, "min_user_turns": 4, "max_user_turns": 8, "xp_awarded": 0 }

// BotTurn
{ "turn_index": 3, "speaker": "bot",
  "jp": "なにに しますか。", "reading_kana": "なにに しますか。", "de": "Was möchten Sie?",
  "suggestions": [ { "jp": "コーヒーを ください。", "de": "Einen Kaffee, bitte." }, … ],  // 3, leer bei Ende
  "hint_de": "Bestelle ein Getränk." }

// Correction (max. 3)
{ "original": "コーヒー ください", "better": "コーヒーを ください。",
  "explanation_de": "Das Objekt bekommt die Partikel を." }

// Limits (Resttage-Kontingent des Nutzers)
{ "sessions_left": 4, "messages_left": 58, "tutor_left": 20 }
```

## Routen

### GET `/api/roleplay/scene/<content_id>`

`content_id` = `LessonContent.id` eines `dialog_slideshow`.

```json
200 {
  "content_id": 345, "lesson_id": 210, "lesson_title": "Im Restaurant", "title": "Im Restaurant",
  "scene_de": "Szene: Im Restaurant. Der Dialog beginnt mit „Willkommen.“ und endet mit „Bitte schön.“.",
  "roles": [
    { "name": "Kellner", "gender": null, "line_count": 2, "first_line_jp": "いらっしゃいませ。", "first_line_de": "Willkommen." },
    { "name": "Gast", "gender": null, "line_count": 1, "first_line_jp": "コーヒーを ください。", "first_line_de": "Einen Kaffee, bitte." }
  ],
  "goal_suggestions": { "Kellner": "Spiele Kellner und …", "Gast": "Spiele Gast und …" },
  "min_user_turns": 4, "max_user_turns": 8,
  "limits": { "sessions_left": 5, "messages_left": 60, "tutor_left": 20 }
}
```
Fehler: 404 `not_found`, 403 `no_access`, 422 `not_roleplayable`.

`roles[].gender`: `"m"` | `"f"` | `null` aus der Sprechername-Tabelle
`app/speaker_gender.py` (dieselbe wie für das Dialog-Audio). Unbekannte Namen
(„Kellner", „Passant") → `null` = Standardstimme, **kein** geratenes Geschlecht.
Das Panel übergibt beim Vorlesen `voice_gender` an `POST /api/tts`
(`{ text, lang: "ja", voice_gender: "m"|"f" }`, nur diese Werte, sonst 400):
m = `ja-JP-Neural2-D` (Fallback `ja-JP-Chirp3-HD-Charon`),
f = `ja-JP-Neural2-B` (Fallback `ja-JP-Chirp3-HD-Leda`). Ohne Parameter: Standardstimme.

### POST `/api/roleplay/start`

```json
{ "content_id": 345, "role_user": "Gast", "goal": "optional, max. 200 Zeichen" }
```
`goal` weglassen = Zielvorschlag des Servers für die Rolle. Ein eigenes Ziel wird dem
Modell nur als Nutzerbeitrag übergeben (nie als Anweisung).

```json
201 { "session": Session, "bot_turn": BotTurn, "limits": Limits }
```
Der erste `bot_turn` ist die Eröffnungszeile des Bots. Fehler: 400, 403, 404, 422, 429,
502, 503. Ein fehlgeschlagener Start (502) zählt nicht gegen das Tageslimit.

### POST `/api/roleplay/<session_id>/turn`

```json
{ "text": "コーヒーを ください。" }      // 1–300 Zeichen, Japanisch (Kana/Kanji) oder Romaji
```
```json
200 { "session": Session, "bot_turn": BotTurn,
      "done": false, "correction": [], "xp_awarded": 0, "limits": Limits }
```
Bei `done: true` ist das Gespräch beendet (Ziel erreicht oder 8. Zug): `bot_turn` ist die
Verabschiedung, `correction` enthält max. 3 Punkte, `xp_awarded` = 25 (bzw. 0 unter 4 Zügen),
`session.status` = `completed`. Danach **nicht** mehr `/end` aufrufen müssen (idempotent
aber möglich). Fehler: 400, 404, 409, 429, 502, 503.

### POST `/api/roleplay/<session_id>/end`

Body leer (`{}`). Beendet vorzeitig oder holt den Abschluss erneut (idempotent, kein
doppeltes XP, kein neuer Modell-Aufruf).

```json
200 { "session": Session,
      "farewell": BotTurn | null,              // Verabschiedung, null wenn keine erzeugt
      "correction": [Correction, …],           // max. 3
      "correction_unavailable": false,          // true: Modell/Kappe → ohne Korrektur beendet
      "xp_awarded": 25, "total_xp": 1240, "level": 7 }
```
- Unter 4 Nutzerzügen: `status: "abandoned"`, `xp_awarded: 0` (Korrektur trotzdem, ab 1 Zug).
- Ohne jeden Nutzerzug: kein Modell-Aufruf, leere Korrektur.
- `/end` scheitert nicht an Kappen/Upstream: dann `correction_unavailable: true`.
Fehler: 404.

### POST `/api/roleplay/tutor` („Frag zur Seite“)

```json
{ "lesson_id": 210, "page": 2, "question": "Wozu brauche ich hier を?" }   // Frage max. 500 Zeichen
```
Kontext = Inhalt dieser Lektionsseite (Text, Dialog, Vokabeln, Grammatik, Kanji).
```json
200 { "id": 88, "lesson_id": 210, "page": 2,
      "answer": "を markiert das direkte Objekt …", "limits": Limits }
```
`answer` ist Klartext (Deutsch, evtl. kurze Aufzählungen mit „- “, kein HTML → als Text
rendern). Fehler: 400, 403, 404 (Lektion/Seite), 429, 502, 503.

## Vorausberechnung der Antwortvorschläge (seit 2026-09-26)

Code: `app/services/roleplay_prefetch.py`, Tabelle `roleplay_prefetch`
(`session_id` | `demo_key`, `turn_index`, `user_text`, `norm_text`, `response_json`, `status`,
Tokens/Kosten, `created_at`).

- Sobald ein Bot-Zug mit Vorschlägen gespeichert ist (`/start`, `/turn`, Demo-Start,
  Demo-Zug), legt der Server pro Vorschlag eine Zeile `pending` an und rechnet die
  Bot-Antwort im Hintergrund (Thread-Pool im Gunicorn-Worker, 3 Threads,
  `ROLEPLAY_PREFETCH_THREADS`) vor → `ready` (bzw. `failed`). Die Tabelle ist
  worker-übergreifend. Anfragen an die Bridge tragen `priority: "low"`.
- `POST …/turn`: Text wird normalisiert (NFKC, ohne Leerraum/Satzzeichen) und mit den
  Vorschlägen **dieses** Zugs verglichen. Treffer → Antwort ohne Modell-Aufruf (`used`);
  läuft die Vorausberechnung noch, wartet der Zug auf sie (max. 25 s) statt doppelt zu
  rechnen. Kein Treffer → regulärer Aufruf. Der Zug wird in beiden Fällen normal verbucht
  (Verlauf, Nachrichtenlimit, Demo: IP-Limit + Gast-Kappe). Antwortformat unverändert.
- Übrige Zeilen des Zugs → `stale`, `response_json` wird geleert (Demo: keine Texte
  aufbewahrt; `user_text` ist immer ein Vorschlag, nie Freitext).
- Limits: Vorausberechnungen zählen **nicht** gegen Nutzerlimits, aber gegen
  `ROLEPLAY_DAILY_MESSAGE_CAP` (alle Zeilen ausser `used`) und die Kostenkappe.
  Würde die Kappe überschritten, wird nicht vorausgerechnet. Ein Cache-Treffer ist auch
  bei erreichter Kappe erlaubt (kein neuer Aufruf).
- Demo: Schlüssel `demo_key` = SHA-256 des Tokens; beim Start nur, wenn die IP heute noch
  Züge hat. Nach dem letzten (3.) Zug wird nichts mehr vorausberechnet.
- Aufräumen: Zeilen älter als 24 h löscht `cleanup_old()` bei jedem Gesprächs- bzw. Demo-Start.
- Schalter: `ROLEPLAY_PREFETCH` (Default an, in Tests aus), `ROLEPLAY_PREFETCH_SYNC` (Tests).

## Panel: Vorschläge (Frontend)

- Chip antippen = Text ins Eingabefeld (wie bisher). Pfeil am Chip = sofort senden.
- Lautsprecher am Chip (`aria-label` „Vorschlag vorlesen") liest über `POST /api/tts` mit
  `voice_gender` der **Nutzer**-Rolle vor (`scene.roles[].gender`; unbekannt → ohne
  Parameter = Standardstimme). Ebenso im Abschluss die „besser"-Sätze („Besseren Satz
  vorlesen"). Werkzeug-Knöpfe stoppen den Klick (`@click.stop`), übernehmen also nichts.
- Deutsche Übersetzungen der Vorschläge sind standardmässig verdeckt: „DE" am Chip deckt
  einen auf, Schalter „Deutsch anzeigen" (neben Romaji → Kana, localStorage
  `jpl-roleplay-chip-de`) alle. Abschluss-Erklärungen bleiben sichtbar.

## Seiten (SSR, gleiches Feature-Gate, login-pflichtig, noindex, nicht in der Sitemap)

Code: `app/sprechen_routes.py`, `app/services/roleplay_overview.py`, Templates `sprechen/`.

- `GET /sprechen` — alle Dialogszenen publizierter, zugänglicher Lektionen, nach Modul
  gruppiert; „bereit" = Lektion laut `UserLessonProgress` abgeschlossen.
- `GET /sprechen/<content_id>` — Panel direkt (`_roleplay_panel.html` mit `rp_standalone`).
- `GET /sprechen/verlauf` — eigene Gespräche (≥ 1 Nutzerzug), neueste zuerst.
- `GET /sprechen/verlauf/<session_id>` — ganzer Verlauf + Korrekturen; fremde Session → 404.
  Korrekturen: `RoleplaySession.correction_json`, Fallback `correction` im `raw_json`
  des letzten Bot-Zugs (`roleplay_service.session_corrections`). Lob-Punkte
  (original = better) zählen nicht als Korrektur.
- `/mein-lernen`: Kachel „Heute sprechen" + Kennzahlen (Gespräche, Züge,
  Korrekturen pro Gespräch Ø letzte 5), `dashboard_service.speaking_tile/-stats`.

## Gast-Demo (Startseite, ohne Login)

Code: `app/services/roleplay_demo.py`, Routen in `app/roleplay_routes.py`, Panel im
Demo-Modus (`_roleplay_panel.html` mit `rp_demo`, JS `data-demo="1"`), Hero in
`index.html` (nur Gäste, nur wenn `roleplay_enabled` und die Demo-Szene verfügbar ist).

- Feste Szene „Im Café": `ROLEPLAY_DEMO_CONTENT_ID` (Default 6563 = Dialog der
  Gast-Lektion 157 „Alltag & Essen 2"), Nutzer = Lisa, Bot = Tanaka. Szene muss
  publiziert + `allow_guest_access` sein und beide Sprecher haben, sonst 404 und der
  alte Kana-Hero bleibt.
- Genau **3** Nutzerzüge, beim 3. beendet der Server (`done: true`, Korrektur, kein XP).
- **Kein Login, kein Gesprächs-Speichern:** Zustand = signiertes Token (itsdangerous,
  Salt `roleplay-guest-demo-v1`, 30 min) im JSON-Body, nicht im Pfad (wächst mit dem
  Verlauf; Gunicorn-Request-Zeile max. 4 KB). Einziger DB-Schreibzugriff:
  `guest_demo_counter(day, ip_hash, count)` (IP gesalzen gehasht, `'*'` = global).
- CSRF wie alle JSON-APIs (`X-CSRFToken`, Gäste haben Session + Meta-Tag).
- Schutz: 6/min pro IP (`client_ip()`, Flask-Limiter, pro Worker), 9 Gast-Züge pro IP
  und CH-Tag, globale Gast-Kappe `ROLEPLAY_GUEST_DAILY_CAP` (100), Gast-Züge zählen
  zusätzlich in `ROLEPLAY_DAILY_MESSAGE_CAP`; Honeypot-Feld `website`; Text ≤ 200 Zeichen.
  Der Start (statische Eröffnungszeile) kostet keinen Modell-Aufruf und zählt nicht.

### POST `/api/roleplay/demo/start`
```json
{ "website": "" }
201 { "token": "…", "session": Session (id null, demo true, max_user_turns 3),
      "bot_turn": BotTurn, "scene": { "title": "Im Café", "scene_de": "…", "roles": [{name, gender}] } }
```
### POST `/api/roleplay/demo/turn`
```json
{ "token": "…", "text": "こうちゃが のみたいです。", "website": "" }
200 { "token": "…" | null, "session": Session, "bot_turn": BotTurn,
      "done": false, "correction": [], "xp_awarded": 0 }
```
Fehler: 400 `invalid_request` (Text/Honeypot), 400 `demo_expired` / `demo_invalid` (Token →
„Demo neu starten"), 404 (Flag aus / Szene fehlt), 409 `session_finished`,
429 `limit_reached` (IP-Tageslimit), 503 `cost_cap` (globale Kappe) — beide mit
„Demo für heute ausgeschöpft, mit Konto geht es weiter.", 502 `upstream_error`
(Zug zählt nicht).

## Betrieb (Kurz)

- Env (Server-`.env`): `ROLEPLAY_ENABLED`, `ROLEPLAY_PROVIDER` (bridge|api),
  `ROLEPLAY_BRIDGE_URL=http://host.docker.internal:5077`, `ROLEPLAY_BRIDGE_TOKEN`,
  optional `ANTHROPIC_API_KEY`; Limits `ROLEPLAY_LIMIT_SESSIONS_PER_DAY` (5),
  `ROLEPLAY_LIMIT_MESSAGES_PER_DAY` (60), `ROLEPLAY_LIMIT_TUTOR_PER_DAY` (20),
  `ROLEPLAY_DAILY_COST_CAP_USD` (2.00, API-Pfad), `ROLEPLAY_DAILY_MESSAGE_CAP` (1500, global,
  inkl. Vorausberechnungen), `ROLEPLAY_PREFETCH` (an).
- Bridge: `tools/roleplay_bridge/bridge.py` als systemd-Dienst `jpl-roleplay-bridge`
  (User hp-ubuntu, lauscht auf 172.17.0.1:5077, Token in
  `/home/hp-ubuntu/.jpl-roleplay-bridge.env`). Container erreicht den Host über
  `extra_hosts: host.docker.internal:host-gateway` (docker-compose.override.yml);
  ufw erlaubt nur das Compose-Netz auf Port 5077. Nach Änderungen an `bridge.py`:
  `sudo systemctl restart jpl-roleplay-bridge`; nach Änderungen an der Unit zusätzlich
  `sudo cp tools/roleplay_bridge/jpl-roleplay-bridge.service /etc/systemd/system/ && sudo systemctl daemon-reload`.
- Bridge-Pool: `BRIDGE_POOL_SIZE` 4 gleichzeitige CLI-Aufrufe, davon höchstens
  `BRIDGE_LOW_SLOTS` 3 für Vorausberechnungen (`priority: "low"`), `BRIDGE_MAX_WAITING` 8
  Wartende (max. `BRIDGE_QUEUE_WAIT_S` 20 s), sonst 429 → 502 `upstream_error` „beschäftigt".
  `BRIDGE_EFFORT=low` (CLI `--effort low`). Log pro Aufruf: Dauer, Priorität, Wartezeit, aktive Plätze.
- Kein persistenter CLI-Prozess (`--input-format stream-json`): gemessen bringt er nur den
  Kaltstart von ~0,4 s, hält aber den Verlauf aller Anfragen im Kontext und hat einen festen
  System-Prompt pro Prozess (Details im Kopf von `bridge.py`).
- Monitoring: Flask-Admin `/admin-panel` → Kategorie „Rollenspiel“ (nur lesend).
