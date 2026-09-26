# Rollenspiel-Tutor — API-Vertrag (Backend)

Stand: 2026-09-26. Backend: `app/roleplay_routes.py`, `app/services/roleplay_service.py`.
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
- **Latenz:** ein Modell-Aufruf dauert **3–8 s** (Claude-Code-CLI auf dem Host), im
  Fehlerfall bis ~60 s. Frontend: Ladeindikator („Tanaka tippt …“), Eingabe sperren,
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
| 503  | `cost_cap`         | Globale Tageskappe erreicht (Kosten bzw. 400 Modell-Antworten/Tag). |

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
    { "name": "Kellner", "line_count": 2, "first_line_jp": "いらっしゃいませ。", "first_line_de": "Willkommen." },
    { "name": "Gast", "line_count": 1, "first_line_jp": "コーヒーを ください。", "first_line_de": "Einen Kaffee, bitte." }
  ],
  "goal_suggestions": { "Kellner": "Spiele Kellner und …", "Gast": "Spiele Gast und …" },
  "min_user_turns": 4, "max_user_turns": 8,
  "limits": { "sessions_left": 5, "messages_left": 60, "tutor_left": 20 }
}
```
Fehler: 404 `not_found`, 403 `no_access`, 422 `not_roleplayable`.

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

## Betrieb (Kurz)

- Env (Server-`.env`): `ROLEPLAY_ENABLED`, `ROLEPLAY_PROVIDER` (bridge|api),
  `ROLEPLAY_BRIDGE_URL=http://host.docker.internal:5077`, `ROLEPLAY_BRIDGE_TOKEN`,
  optional `ANTHROPIC_API_KEY`; Limits `ROLEPLAY_LIMIT_SESSIONS_PER_DAY` (5),
  `ROLEPLAY_LIMIT_MESSAGES_PER_DAY` (60), `ROLEPLAY_LIMIT_TUTOR_PER_DAY` (20),
  `ROLEPLAY_DAILY_COST_CAP_USD` (2.00, API-Pfad), `ROLEPLAY_DAILY_MESSAGE_CAP` (400, global).
- Bridge: `tools/roleplay_bridge/bridge.py` als systemd-Dienst `jpl-roleplay-bridge`
  (User hp-ubuntu, lauscht auf 172.17.0.1:5077, Token in
  `/home/hp-ubuntu/.jpl-roleplay-bridge.env`). Container erreicht den Host über
  `extra_hosts: host.docker.internal:host-gateway` (docker-compose.override.yml);
  ufw erlaubt nur das Compose-Netz auf Port 5077. Nach Änderungen an `bridge.py`:
  `sudo systemctl restart jpl-roleplay-bridge`.
- Monitoring: Flask-Admin `/admin-panel` → Kategorie „Rollenspiel“ (nur lesend).
