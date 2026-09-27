/* Rollenspiel-Tutor am Lektionsdialog — Alpine-Komponente.
 *
 * window.roleplayPanel(contentId) wird im Partial
 * templates/partials/_roleplay_panel.html per x-data eingehaengt (nur wenn
 * roleplay_enabled und eingeloggt). API-Vertrag: docs/roleplay-api.md.
 *
 * Ablauf: GET scene → Rollenwahl → POST start → Zuege (POST turn) →
 * Abschluss (done im Zug oder POST end). Zweiter Tab „Frag zur Seite"
 * (POST tutor). Alle Fehler landen als Meldung im Panel, nie in der Konsole.
 *
 * Demo-Modus (data-demo="1", Gast-Hero der Startseite): gleiche Komponente,
 * andere Endpunkte (data-demo-start-url / data-demo-turn-url), feste Rolle,
 * ohne Tutor-Tab und ohne Beenden-Knopf. Der Gespraechszustand ist ein
 * signiertes Token, das mit jedem Zug zurueckkommt (kein Login, keine Session-ID).
 *
 * Vorschlags-Chips: Tipp = ins Eingabefeld uebernehmen; Pfeil = sofort senden
 * (der Server hat die Antwort meist schon vorausberechnet → ohne „tippt …“,
 * der Indikator erscheint nur, falls es doch laenger als SLOW_MS dauert);
 * Lautsprecher = Vorschlag vorlesen (Stimme der Nutzer-Rolle); „DE“ = Uebersetzung
 * dieses Chips zeigen. Uebersetzungen sind standardmaessig aus, der Schalter
 * „Deutsch anzeigen“ blendet alle ein (localStorage).
 *
 * Romaji: der Server liefert zu jeder japanischen Zeile `romaji` (Bot-Zeile,
 * Vorschlaege, Korrektur `better_romaji`, Nutzerzug `user_romaji` — nur bei
 * reiner Kana). Schalter „Romaji anzeigen“ (Default an, localStorage) blendet
 * alle Romaji-Zeilen aus/ein; gleicher Schluessel wie /sprechen/verlauf/<id>.
 *
 * Sofort-Antwort (zweigeteilter Zug): send() nutzt …/turn/stream (Server-Sent
 * Events) — die Bot-Zeile erscheint Zeichen fuer Zeichen, sobald das Modell sie
 * schreibt. Lesung, Uebersetzung, Vorschlaege und Tipp kommen aus einem zweiten
 * Aufruf nach (bot_turn.details_pending): das Panel fragt alle 500 ms bei
 * …/details nach (max. 20 s) und zeigt bis dahin „Vorschläge folgen …“.
 * Vorlesen geht schon vorher. Ohne Stream-Unterstuetzung im Browser: POST …/turn.
 */
(function () {
    'use strict';

    var TIMEOUT_MS = 65000;
    var GOAL_MAX = 120;
    var TUTOR_MAX = 300;
    var TEXT_MAX = 300;
    var ROMAJI_KEY = 'jpl-roleplay-romaji';
    var GERMAN_KEY = 'jpl-roleplay-chip-de';
    var ROMAJI_SHOW_KEY = 'jpl-roleplay-romaji-show';
    var SLOW_MS = 1200;
    var STREAM_TIMEOUT_MS = 35000;   // Server beendet den Stream nach spaetestens ~30 s
    var DETAILS_POLL_MS = 500;
    var DETAILS_MAX_MS = 20000;

    function csrfToken() {
        var el = document.querySelector('meta[name="csrf-token"]');
        return el ? el.getAttribute('content') || '' : '';
    }

    function readRomajiPref() {
        try {
            var v = window.localStorage.getItem(ROMAJI_KEY);
            return v === null ? true : v === '1';
        } catch (e) {
            return true;
        }
    }

    function writeRomajiPref(on) {
        try { window.localStorage.setItem(ROMAJI_KEY, on ? '1' : '0'); } catch (e) { /* egal */ }
    }

    function readGermanPref() {
        try { return window.localStorage.getItem(GERMAN_KEY) === '1'; } catch (e) { return false; }
    }

    function writeGermanPref(on) {
        try { window.localStorage.setItem(GERMAN_KEY, on ? '1' : '0'); } catch (e) { /* egal */ }
    }

    function readRomajiShowPref() {
        try { return window.localStorage.getItem(ROMAJI_SHOW_KEY) !== '0'; } catch (e) { return true; }
    }

    function writeRomajiShowPref(on) {
        try { window.localStorage.setItem(ROMAJI_SHOW_KEY, on ? '1' : '0'); } catch (e) { /* egal */ }
    }

    function logBot(bot) {
        return { who: 'bot', jp: bot.jp, de: bot.de, romaji: bot.romaji || '' };
    }

    function roleGender(scene, name) {
        var roles = (scene && scene.roles) || [];
        for (var i = 0; i < roles.length; i++) {
            if (roles[i].name === name) {
                var g = roles[i].gender;
                return g === 'm' || g === 'f' ? g : null;
            }
        }
        return null;
    }

    /* fetch mit Timeout. Liefert immer {ok, status, data} — wirft nie.
       data ist das JSON des Servers oder ein synthetisches {error, message}. */
    function api(method, url, body) {
        var ctrl = typeof AbortController === 'function' ? new AbortController() : null;
        var timer = ctrl ? setTimeout(function () { ctrl.abort(); }, TIMEOUT_MS) : null;
        var opts = {
            method: method,
            credentials: 'same-origin',
            redirect: 'manual',
            headers: { 'Accept': 'application/json' },
        };
        if (ctrl) opts.signal = ctrl.signal;
        if (method !== 'GET') {
            opts.headers['Content-Type'] = 'application/json';
            opts.headers['X-CSRFToken'] = csrfToken();
            opts.body = JSON.stringify(body || {});
        }
        return fetch(url, opts).then(function (resp) {
            if (timer) clearTimeout(timer);
            return jsonResult(resp);
        }, function (err) {
            if (timer) clearTimeout(timer);
            return fetchFailure(err);
        });
    }

    /* JSON-Antwort (auch Fehler) → {ok, status, data}. */
    function jsonResult(resp) {
        if (resp.type === 'opaqueredirect' || resp.redirected || (resp.status >= 300 && resp.status < 400)) {
            return { ok: false, status: 401, data: {
                error: 'login_required',
                message: 'Deine Anmeldung ist abgelaufen. Bitte lade die Seite neu und melde dich an.',
            } };
        }
        var ctype = resp.headers.get('Content-Type') || '';
        if (ctype.indexOf('application/json') === -1) {
            return { ok: false, status: resp.status, data: resp.status === 429 ? {
                error: 'rate_limited',
                message: 'Das war gerade sehr schnell hintereinander. Bitte warte eine Minute und versuch es dann nochmal.',
            } : {
                error: 'unexpected',
                message: 'Da ist etwas schiefgelaufen. Bitte versuch es gleich nochmal.',
            } };
        }
        return resp.json().then(function (data) {
            return { ok: resp.ok, status: resp.status, data: data || {} };
        }, function () {
            return { ok: false, status: resp.status, data: {
                error: 'unexpected', message: 'Die Antwort war unvollständig. Bitte versuch es nochmal.',
            } };
        });
    }

    function fetchFailure(err) {
        var aborted = err && err.name === 'AbortError';
        return { ok: false, status: 0, data: aborted ? {
            error: 'timeout',
            message: 'Die Antwort hat zu lange gedauert. Dein Text ist noch da — bitte nochmal senden.',
        } : {
            error: 'network',
            message: 'Keine Verbindung zum Server. Bitte prüfe dein Internet und sende nochmal.',
        } };
    }

    function canStream() {
        return typeof window.ReadableStream === 'function' && typeof window.TextDecoder === 'function';
    }

    /* POST mit Server-Sent-Events-Antwort. onLine(text) fuer jedes Stueck der
       Bot-Zeile; liefert wie api() {ok, status, data} (data = JSON aus `result`
       bzw. {error, message} aus `error`). JSON-Antworten (Fehler vor dem Start)
       laufen durch jsonResult. Wirft nie. */
    function apiStream(url, body, onLine) {
        var ctrl = typeof AbortController === 'function' ? new AbortController() : null;
        var timer = ctrl ? setTimeout(function () { ctrl.abort(); }, STREAM_TIMEOUT_MS) : null;
        var opts = {
            method: 'POST',
            credentials: 'same-origin',
            redirect: 'manual',
            headers: {
                'Accept': 'text/event-stream',
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken(),
            },
            body: JSON.stringify(body || {}),
        };
        if (ctrl) opts.signal = ctrl.signal;
        var done = function (r) { if (timer) clearTimeout(timer); return r; };
        return fetch(url, opts).then(function (resp) {
            var ctype = resp.headers.get('Content-Type') || '';
            if (!resp.ok || ctype.indexOf('text/event-stream') === -1 || !resp.body) {
                return Promise.resolve(jsonResult(resp)).then(done);
            }
            var reader = resp.body.getReader();
            var decoder = new TextDecoder('utf-8');
            var buf = '';
            var outcome = null;
            var handle = function (block) {
                var ev = 'message';
                var data = [];
                block.split('\n').forEach(function (line) {
                    if (line.indexOf('event:') === 0) ev = line.slice(6).trim();
                    else if (line.indexOf('data:') === 0) data.push(line.slice(5).trim());
                });
                if (!data.length) return;
                var payload;
                try { payload = JSON.parse(data.join('\n')); } catch (e) { return; }
                if (ev === 'line' && payload && typeof payload.text === 'string') {
                    try { onLine(payload.text); } catch (e) { /* Anzeige darf den Stream nie abbrechen */ }
                } else if (ev === 'result') {
                    outcome = { ok: true, status: 200, data: payload || {} };
                } else if (ev === 'error') {
                    outcome = { ok: false, status: (payload && payload.status) || 502, data: payload || {} };
                }
            };
            var pump = function () {
                return reader.read().then(function (chunk) {
                    if (chunk.done) {
                        buf += decoder.decode();
                        if (buf.trim()) handle(buf.replace(/\r/g, ''));
                        return outcome || { ok: false, status: 0, data: {
                            error: 'network',
                            message: 'Die Verbindung ist abgebrochen. Dein Text ist noch da — bitte nochmal senden.',
                        } };
                    }
                    buf += decoder.decode(chunk.value, { stream: true }).replace(/\r/g, '');
                    var idx;
                    while ((idx = buf.indexOf('\n\n')) !== -1) {
                        handle(buf.slice(0, idx));
                        buf = buf.slice(idx + 2);
                    }
                    return pump();
                });
            };
            return pump().then(done, function (err) { return done(fetchFailure(err)); });
        }, function (err) {
            return done(fetchFailure(err));
        });
    }

    var RETRYABLE = { upstream_error: 1, timeout: 1, network: 1, unexpected: 1 };

    window.roleplayPanel = function (contentId) {
        return {
            contentId: contentId,
            demo: false,               // Gast-Demo (Startseite)
            demoToken: null,
            demoStartUrl: '',
            demoTurnUrl: '',
            demoStreamUrl: '',
            demoDetailsUrl: '',
            honeypot: '',              // Honeypot-Feld (muss leer bleiben)
            lessonId: null,
            pageNumbers: [],
            fallbackPage: null,

            open: false,
            tab: 'play',               // play | tutor
            phase: 'idle',             // idle | loading | choose | intro | starting | playing | done | unavailable
            scene: null,
            roleChoice: null,
            customGoal: '',
            session: null,
            log: [],                   // bisherige Zeilen {who:'bot'|'user', jp, de, romaji}
            bot: null,                 // aktuelle Bot-Zeile (BotTurn)
            showReading: false,
            showGerman: false,
            hintShown: false,
            input: '',
            romajiOn: true,
            germanOn: false,           // Uebersetzungen unter den Vorschlaegen (Default aus)
            romajiShow: true,          // Romaji-Zeilen unter dem Japanischen (Default an)
            chipDe: {},                // einzeln aufgedeckte Chip-Uebersetzungen {index: true}
            sending: false,
            quickSend: false,          // Vorschlag direkt gesendet → kein „tippt …“ (ausser langsam)
            slowTyping: false,
            _slowTimer: null,
            streamingLine: false,      // Bot-Zeile entsteht gerade (Stream)
            detailsState: '',          // '' | 'pending' | 'failed' — Lernhilfen der aktuellen Bot-Zeile
            _detailsSeq: 0,
            _detailsTimer: null,
            ending: false,
            error: null,               // {code, message, retry}
            limits: null,
            result: null,              // Abschluss {status, correction, correction_unavailable, xp_awarded, farewell}
            liveMsg: '',
            speaking: false,
            speakingKey: '',           // welcher Knopf gerade vorliest ('bot', 's0', 'c1', …)
            _audio: null,

            tutorQuestion: '',
            tutorAnswer: '',
            tutorAsked: '',
            tutorLoading: false,
            tutorError: null,

            GOAL_MAX: GOAL_MAX,
            TUTOR_MAX: TUTOR_MAX,
            TEXT_MAX: TEXT_MAX,

            init: function () {
                var el = this.$el;
                this.lessonId = parseInt(el.dataset.lessonId, 10) || null;
                this.fallbackPage = parseInt(el.dataset.pageNumber, 10) || null;
                try { this.pageNumbers = JSON.parse(el.dataset.pageNumbers || '[]'); } catch (e) { this.pageNumbers = []; }
                this.romajiOn = readRomajiPref();
                this.germanOn = readGermanPref();
                this.romajiShow = readRomajiShowPref();
                if (el.dataset.demo === '1') {
                    this.demo = true;
                    this.open = true;
                    this.phase = 'intro';
                    this.demoStartUrl = el.dataset.demoStartUrl || '';
                    this.demoTurnUrl = el.dataset.demoTurnUrl || '';
                    this.demoStreamUrl = el.dataset.demoStreamUrl || '';
                    this.demoDetailsUrl = el.dataset.demoDetailsUrl || '';
                    this.TEXT_MAX = parseInt(el.dataset.textMax, 10) || TEXT_MAX;
                    return;
                }
                // /sprechen/<id>: Panel ohne Lektionsseite → sofort offen + Szene laden.
                if (el.dataset.standalone === '1') {
                    this.open = true;
                    this.loadScene();
                }
            },

            // ── Ansichtshilfen ───────────────────────────────────────────
            get botName() { return (this.session && this.session.role_bot) || 'Partner'; },
            get userName() { return (this.session && this.session.role_user) || 'Du'; },
            // Geschlecht der Bot-Rolle aus der Szene ('m' | 'f' | null → Standardstimme).
            get botGender() { return roleGender(this.scene, this.session && this.session.role_bot); },
            // Geschlecht der eigenen Rolle — fuer das Vorlesen der Vorschlaege/Korrekturen.
            get userGender() { return roleGender(this.scene, this.session && this.session.role_user); },
            get showTyping() { return this.sending && !this.streamingLine && (!this.quickSend || this.slowTyping); },
            // Lernhilfen (Lesung/Deutsch/Tipp/Vorschlaege) der aktuellen Zeile stehen noch aus.
            get detailsPending() { return !!this.bot && (this.streamingLine || this.detailsState === 'pending'); },
            get detailsFailed() { return !!this.bot && !this.streamingLine && this.detailsState === 'failed'; },
            get turnCount() { return (this.session && this.session.turn_count) || 0; },
            get maxTurns() { return (this.session && this.session.max_user_turns) || 8; },
            get minTurns() { return (this.session && this.session.min_user_turns) || 4; },
            get progressText() {
                return 'Zug ' + Math.min(this.turnCount + 1, this.maxTurns) + ' von ' + this.maxTurns;
            },
            get progressPercent() { return Math.round((this.turnCount / this.maxTurns) * 100); },
            get canEnd() { return !this.demo && this.phase === 'playing' && this.turnCount >= 1; },
            get busy() { return this.sending || this.ending; },
            get limitsText() {
                var l = this.limits;
                if (!l) return '';
                return 'Heute noch: ' + l.sessions_left + ' Gespräche · ' + l.messages_left + ' Nachrichten';
            },
            get tutorLimitText() {
                return this.limits ? ('Heute noch ' + this.limits.tutor_left + ' Fragen') : '';
            },
            isSameCorrection: function (c) {
                var norm = function (s) { return String(s || '').replace(/[\s。．.、,！!？?]/g, ''); };
                return !!c && norm(c.original) === norm(c.better);
            },
            goalFor: function (name) {
                return (this.scene && this.scene.goal_suggestions && this.scene.goal_suggestions[name]) || '';
            },

            // ── Panel ───────────────────────────────────────────────────
            toggle: function () {
                this.open = !this.open;
                if (this.open) {
                    if (this.phase === 'idle') this.loadScene();
                    var self = this;
                    this.$nextTick(function () { self._focus('panelTitle'); });
                } else {
                    this.stopAudio();
                    var btn = this.$refs.openBtn;
                    if (btn) btn.focus();
                }
            },
            setTab: function (t) {
                this.tab = t;
                var self = this;
                this.$nextTick(function () {
                    if (t === 'tutor') self._focus('tutorInput');
                });
            },
            onTabKey: function (ev) {
                if (ev.key === 'ArrowRight' || ev.key === 'ArrowLeft') {
                    ev.preventDefault();
                    this.setTab(this.tab === 'play' ? 'tutor' : 'play');
                    var self = this;
                    this.$nextTick(function () { self._focus(self.tab === 'play' ? 'tabPlay' : 'tabTutor'); });
                }
            },
            onKeydown: function (ev) {
                // Seiten-Navigation (Pfeile/Leertaste) der Lektion hier nicht ausloesen.
                if (ev.key === 'Escape' && this.open) {
                    this.stopAudio();
                }
            },

            // Fokus erst nach dem DOM-Update (x-show/:disabled) setzen — sonst ist das
            // Ziel noch verborgen oder gesperrt und focus() verpufft.
            _focus: function (ref) {
                var self = this;
                this.$nextTick(function () {
                    setTimeout(function () {
                        var el = self.$refs[ref];
                        if (el && typeof el.focus === 'function' && !el.disabled) {
                            try { el.focus({ preventScroll: false }); } catch (e) { /* egal */ }
                        }
                    }, 30);
                });
            },
            _setError: function (data, retry) {
                var code = (data && data.error) || 'unexpected';
                var msg = (data && data.message) || 'Da ist etwas schiefgelaufen.';
                if (data && data.limits) this.limits = data.limits;
                this.error = { code: code, message: msg, retry: !!retry };
                this.liveMsg = msg;
            },

            // ── Szene + Rollenwahl ──────────────────────────────────────
            loadScene: function () {
                var self = this;
                this.phase = 'loading';
                this.error = null;
                return api('GET', '/api/roleplay/scene/' + this.contentId).then(function (r) {
                    if (r.ok) {
                        self.scene = r.data;
                        self.limits = r.data.limits || null;
                        if (!self.lessonId && r.data.lesson_id) self.lessonId = r.data.lesson_id;
                        self.phase = 'choose';
                        return;
                    }
                    if (r.data.error === 'not_roleplayable' || r.data.error === 'not_found' || r.data.error === 'no_access') {
                        self.phase = 'unavailable';
                        self._setError(r.data, false);
                        return;
                    }
                    self.phase = 'idle';
                    self._setError(r.data, true);
                });
            },
            chooseRole: function (name) {
                this.roleChoice = name;
            },
            // ── Gast-Demo ───────────────────────────────────────────────
            // fromCta: Aufruf ueber den Hero-Knopf „Gespräch ausprobieren“ → erst
            // zum Panel scrollen; laeuft schon ein Gespraech, nur dorthin springen.
            startDemo: function (fromCta) {
                if (!this.demo) return;
                if (fromCta) {
                    try { this.$el.scrollIntoView({ behavior: 'smooth', block: 'start' }); } catch (e) { /* egal */ }
                }
                if (this.phase !== 'intro' || this.busy) {
                    if (this.phase === 'playing') this._focus('input');
                    return;
                }
                var self = this;
                this.phase = 'starting';
                this.sending = true;
                this.error = null;
                return api('POST', this.demoStartUrl, { website: this.honeypot }).then(function (r) {
                    self.sending = false;
                    if (r.ok) {
                        self.demoToken = r.data.token;
                        self.scene = r.data.scene || null;
                        self.session = r.data.session;
                        self.log = [];
                        self.result = null;
                        self.input = '';
                        self.bot = null;
                        self.phase = 'playing';
                        self._showBot(r.data.bot_turn);
                        return;
                    }
                    self.phase = 'intro';
                    self._setError(r.data, !!RETRYABLE[r.data.error]);
                });
            },
            _turnRequest: function (text, onLine) {
                var body = this.demo ? { token: this.demoToken, text: text, website: this.honeypot } : { text: text };
                var url = this.demo ? this.demoTurnUrl : '/api/roleplay/' + this.session.id + '/turn';
                var streamUrl = this.demo ? this.demoStreamUrl : url + '/stream';
                if (streamUrl && canStream()) return apiStream(streamUrl, body, onLine);
                return api('POST', url, body);
            },

            // ── Lernhilfen nachladen (zweiter Aufruf) ───────────────────
            _stopDetails: function () {
                this._detailsSeq++;
                if (this._detailsTimer) { clearTimeout(this._detailsTimer); this._detailsTimer = null; }
            },
            _pollDetails: function (turn) {
                this._stopDetails();
                if (!turn || !turn.details_pending) {
                    this.detailsState = turn && turn.details_failed ? 'failed' : '';
                    return;
                }
                this.detailsState = 'pending';
                var self = this;
                var seq = this._detailsSeq;
                var started = Date.now();
                var index = turn.turn_index;
                var token = this.demoToken;
                var fail = function () {
                    if (seq !== self._detailsSeq) return;
                    self.detailsState = 'failed';
                    self.liveMsg = 'Vorschläge gerade nicht verfügbar. Du kannst frei weiterschreiben.';
                };
                var tick = function () {
                    if (seq !== self._detailsSeq) return;
                    var req = self.demo
                        ? api('POST', self.demoDetailsUrl, { token: token })
                        : api('GET', '/api/roleplay/' + self.session.id + '/turn/' + index + '/details');
                    req.then(function (r) {
                        if (seq !== self._detailsSeq) return;
                        var status = r.ok && r.data ? r.data.status : 'error';
                        if (status === 'ready' && r.data.bot_turn && self.bot && self.bot.turn_index === index) {
                            var merged = {};
                            var k;
                            for (k in self.bot) { if (Object.prototype.hasOwnProperty.call(self.bot, k)) merged[k] = self.bot[k]; }
                            for (k in r.data.bot_turn) { if (Object.prototype.hasOwnProperty.call(r.data.bot_turn, k)) merged[k] = r.data.bot_turn[k]; }
                            merged.jp = self.bot.jp;           // Zeile bleibt, wie sie schon dasteht
                            merged.details_pending = false;
                            self.bot = merged;
                            self.detailsState = '';
                            self.liveMsg = 'Vorschläge sind da.';
                            return;
                        }
                        if (status === 'failed') return fail();
                        if (Date.now() - started >= DETAILS_MAX_MS) return fail();
                        // pending oder kurzer Fehler (Netz, 429): weiter nachfragen
                        self._detailsTimer = setTimeout(tick, DETAILS_POLL_MS);
                    });
                };
                this._detailsTimer = setTimeout(tick, DETAILS_POLL_MS);
            },

            start: function () {
                if (this.demo) return this.startDemo(false);
                if (!this.roleChoice || this.busy) return;
                var self = this;
                var body = { content_id: this.contentId, role_user: this.roleChoice };
                var goal = (this.customGoal || '').trim().slice(0, GOAL_MAX);
                if (goal) body.goal = goal;
                this.phase = 'starting';
                this.sending = true;
                this.error = null;
                return api('POST', '/api/roleplay/start', body).then(function (r) {
                    self.sending = false;
                    if (r.ok) {
                        self.session = r.data.session;
                        self.limits = r.data.limits || self.limits;
                        self.log = [];
                        self.result = null;
                        self.input = '';
                        self.phase = 'playing';
                        self._showBot(r.data.bot_turn);
                        return;
                    }
                    self.phase = 'choose';
                    self._setError(r.data, !!RETRYABLE[r.data.error]);
                });
            },

            _showBot: function (turn, keepToggles) {
                if (this.bot) this.log.push(logBot(this.bot));
                this.bot = turn || null;
                if (!keepToggles) {
                    this.showReading = false;
                    this.showGerman = false;
                    this.hintShown = false;
                }
                this.chipDe = {};
                this._pollDetails(turn);
                if (turn) this.liveMsg = this.botName + ' sagt: ' + turn.jp + (turn.de ? ' — ' + turn.de : '');
                var self = this;
                this.$nextTick(function () {
                    self._focus('input');
                    var logEl = self.$refs.log;
                    if (logEl) logEl.scrollTop = logEl.scrollHeight;
                });
            },

            // ── Eingabe ─────────────────────────────────────────────────
            toggleRomaji: function () {
                this.romajiOn = !this.romajiOn;
                writeRomajiPref(this.romajiOn);
                this._focus('input');
            },
            onInput: function (ev) {
                if (!this.romajiOn || !window.RomajiToKana || (ev && ev.isComposing)) return;
                var el = ev && ev.target;
                var val = this.input;
                // Nur umwandeln, wenn der Cursor am Ende steht (Bearbeitung mitten im Text nicht stoeren).
                if (el && typeof el.selectionStart === 'number' && el.selectionStart !== val.length) return;
                var conv = window.RomajiToKana.convert(val, { partial: true });
                if (conv !== val) this.input = conv;
            },
            useSuggestion: function (s) {
                if (!s || this.busy) return;
                this.input = s.jp;
                this._focus('input');
            },
            // Pfeil am Chip: Vorschlag sofort senden (Antwort ist meist vorausberechnet).
            sendSuggestion: function (s) {
                if (!s || this.busy) return;
                this.input = s.jp;
                this.quickSend = true;
                return this.send();
            },
            toggleRomajiShow: function () {
                this.romajiShow = !this.romajiShow;
                writeRomajiShowPref(this.romajiShow);
            },
            // Romaji des gerade gesendeten Nutzerzugs nachtragen (Server: nur bei reiner Kana).
            _setUserRomaji: function (romaji) {
                if (!romaji) return;
                for (var i = this.log.length - 1; i >= 0; i--) {
                    if (this.log[i].who === 'user') { this.log[i].romaji = romaji; return; }
                }
            },
            toggleGerman: function () {
                this.germanOn = !this.germanOn;
                this.chipDe = {};          // Schalter gilt fuer alle Chips (auch einzeln aufgedeckte)
                writeGermanPref(this.germanOn);
            },
            chipGermanVisible: function (i) { return this.germanOn || !!this.chipDe[i]; },
            toggleChipGerman: function (i) {
                var next = {};
                for (var k in this.chipDe) { if (Object.prototype.hasOwnProperty.call(this.chipDe, k)) next[k] = this.chipDe[k]; }
                next[i] = !next[i];
                this.chipDe = next;
            },
            _finalText: function () {
                var t = (this.input || '').trim();
                if (this.romajiOn && window.RomajiToKana) t = window.RomajiToKana.convert(t).trim();
                return t;
            },
            send: function () {
                if (this.busy || this.phase !== 'playing' || !this.session) return;
                var text = this._finalText();
                if (!text) {
                    this._setError({ error: 'invalid_request', message: 'Bitte schreib zuerst etwas.' }, false);
                    this._focus('input');
                    return;
                }
                if (text.length > this.TEXT_MAX) text = text.slice(0, this.TEXT_MAX);
                this.input = text;
                var self = this;
                this.sending = true;
                this.error = null;
                this.slowTyping = false;
                if (this._slowTimer) clearTimeout(this._slowTimer);
                if (this.quickSend) {
                    this._slowTimer = setTimeout(function () {
                        self.slowTyping = true;
                        self.liveMsg = self.botName + ' tippt …';
                    }, SLOW_MS);
                } else {
                    this.liveMsg = this.botName + ' tippt …';
                }
                this._stopDetails();
                // Stream: beim ersten Stueck die Bot-Zeile sofort zeigen (Verlauf nachziehen);
                // scheitert der Zug danach, wird das zurueckgenommen.
                var streamed = null;
                var onLine = function (piece) {
                    if (!streamed) {
                        streamed = { bot: self.bot, logLen: self.log.length, detailsState: self.detailsState };
                        if (self.bot) self.log.push(logBot(self.bot));
                        self.log.push({ who: 'user', jp: text, de: '', romaji: '' });
                        self.input = '';
                        self.showReading = false;
                        self.showGerman = false;
                        self.hintShown = false;
                        self.chipDe = {};
                        self.detailsState = '';
                        self.streamingLine = true;
                        self.bot = { turn_index: -1, speaker: 'bot', jp: piece, reading_kana: '', romaji: '', de: '',
                                     suggestions: [], hint_de: '', details_pending: true };
                        self.$nextTick(function () {
                            var logEl = self.$refs.log;
                            if (logEl) logEl.scrollTop = logEl.scrollHeight;
                        });
                        return;
                    }
                    self.bot.jp += piece;
                };
                return this._turnRequest(text, onLine).then(function (r) {
                    self.sending = false;
                    self.quickSend = false;
                    self.slowTyping = false;
                    self.streamingLine = false;
                    if (self._slowTimer) { clearTimeout(self._slowTimer); self._slowTimer = null; }
                    if (r.ok) {
                        if (self.demo) self.demoToken = r.data.token || null;
                        if (streamed) {
                            // Verlauf ist schon nachgezogen; Platzhalter-Zeile wird ersetzt.
                            self.bot = null;
                        } else {
                            // Reihenfolge im Verlauf: erst die beantwortete Bot-Zeile, dann der Nutzerzug.
                            if (self.bot) self.log.push(logBot(self.bot));
                            self.bot = null;
                            self.log.push({ who: 'user', jp: text, de: '', romaji: '' });
                        }
                        self._setUserRomaji(r.data.user_romaji);
                        self.input = '';
                        self.session = r.data.session || self.session;
                        self.limits = r.data.limits || self.limits;
                        if (r.data.done) {
                            self._finish({
                                status: self.session.status,
                                farewell: r.data.bot_turn,
                                correction: r.data.correction || [],
                                correction_unavailable: false,
                                xp_awarded: r.data.xp_awarded || 0,
                            });
                        } else {
                            self._showBot(r.data.bot_turn, !!streamed);
                        }
                        return;
                    }
                    if (streamed) {
                        // Zug gescheitert, obwohl die Zeile schon zu sehen war: zuruecknehmen.
                        self.log.splice(streamed.logLen);
                        self.bot = streamed.bot;
                        self.detailsState = streamed.detailsState;
                        self.input = text;
                    }
                    // Lernhilfen der stehengebliebenen Zeile weiter nachladen.
                    if (self.bot && self.bot.details_pending && self.detailsState !== 'failed') self._pollDetails(self.bot);
                    if (!self.demo && (r.status === 409 || r.data.error === 'session_finished')) {
                        return self.end();
                    }
                    self._setError(r.data, !!RETRYABLE[r.data.error]);
                    self.$nextTick(function () { self._focus('input'); });
                });
            },
            onEnter: function (ev) {
                if (ev.isComposing || ev.shiftKey) return;
                ev.preventDefault();
                this.send();
            },

            // ── Ende ────────────────────────────────────────────────────
            end: function () {
                if (this.demo || !this.session || this.ending) return;
                var self = this;
                this.ending = true;
                this.error = null;
                this.stopAudio();
                this.liveMsg = 'Gespräch wird beendet …';
                return api('POST', '/api/roleplay/' + this.session.id + '/end', {}).then(function (r) {
                    self.ending = false;
                    if (r.ok) {
                        self.session = r.data.session || self.session;
                        self._finish({
                            status: self.session.status,
                            farewell: r.data.farewell,
                            correction: r.data.correction || [],
                            correction_unavailable: !!r.data.correction_unavailable,
                            xp_awarded: r.data.xp_awarded || 0,
                        });
                        return;
                    }
                    self._setError(r.data, false);
                });
            },
            _finish: function (res) {
                this._stopDetails();
                this.detailsState = '';
                if (this.bot) this.log.push(logBot(this.bot));
                this.bot = null;
                this.result = res;
                this.phase = 'done';
                this.liveMsg = 'Gespräch beendet. ' + (res.xp_awarded ? ('Plus ' + res.xp_awarded + ' XP.') : '');
                var self = this;
                this.$nextTick(function () { self._focus('doneTitle'); });
            },
            restart: function () {
                this._stopDetails();
                this.detailsState = '';
                if (this.demo) {
                    this.stopAudio();
                    this.session = null;
                    this.bot = null;
                    this.log = [];
                    this.result = null;
                    this.input = '';
                    this.error = null;
                    this.demoToken = null;
                    this.phase = 'intro';
                    this._focus('panelTitle');
                    return;
                }
                this.session = null;
                this.bot = null;
                this.log = [];
                this.result = null;
                this.input = '';
                this.error = null;
                this.roleChoice = null;
                this.customGoal = '';
                return this.loadScene();
            },
            retry: function () {
                this.error = null;
                if (this.demo) {
                    if (this.phase === 'playing') return this.send();
                    return this.startDemo(false);
                }
                if (this.phase === 'playing') return this.send();
                if (this.phase === 'choose') return this.start();
                return this.loadScene();
            },

            // ── Audio ───────────────────────────────────────────────────
            stopAudio: function () {
                if (this._audio) { try { this._audio.pause(); } catch (e) { /* egal */ } this._audio = null; }
                try { if ('speechSynthesis' in window) window.speechSynthesis.cancel(); } catch (e) { /* egal */ }
                this.speaking = false;
                this.speakingKey = '';
            },
            // key: welcher Knopf vorliest (aria-pressed); gender: 'm'|'f'|null,
            // undefined = Stimme der Bot-Rolle. Vorschlaege/Korrekturen: userGender.
            speak: function (text, key, gender) {
                if (!text) return;
                var self = this;
                this.stopAudio();
                this.speaking = true;
                this.speakingKey = key || 'bot';
                var payload = { text: text, lang: 'ja', speed: 0.85 };
                if (gender === undefined) gender = this.botGender;
                if (gender === 'm' || gender === 'f') payload.voice_gender = gender;
                fetch('/api/tts', {
                    method: 'POST',
                    credentials: 'same-origin',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken() },
                    body: JSON.stringify(payload),
                }).then(function (resp) {
                    if (!resp.ok) throw new Error('tts');
                    return resp.blob();
                }).then(function (blob) {
                    var url = URL.createObjectURL(blob);
                    var audio = new Audio(url);
                    self._audio = audio;
                    var done = function () { URL.revokeObjectURL(url); if (self._audio === audio) { self._audio = null; self.speaking = false; self.speakingKey = ''; } };
                    audio.addEventListener('ended', done);
                    audio.addEventListener('error', done);
                    var p = audio.play();
                    if (p && typeof p.catch === 'function') p.catch(done);
                }).catch(function () {
                    self._speakBrowser(text);
                });
            },
            _speakBrowser: function (text) {
                var self = this;
                try {
                    if (!('speechSynthesis' in window)) { self.speaking = false; self.speakingKey = ''; return; }
                    var u = new SpeechSynthesisUtterance(text);
                    u.lang = 'ja-JP';
                    u.rate = 0.8;
                    var v = window.speechSynthesis.getVoices().filter(function (x) { return x.lang && x.lang.indexOf('ja') === 0; })[0];
                    if (v) u.voice = v;
                    u.onend = u.onerror = function () { self.speaking = false; self.speakingKey = ''; };
                    window.speechSynthesis.speak(u);
                } catch (e) {
                    self.speaking = false;
                    self.speakingKey = '';
                }
            },

            // ── Tutor „Frag zur Seite" ──────────────────────────────────
            currentPage: function () {
                var m = /^#page-(\d+)$/.exec(window.location.hash || '');
                if (m) {
                    var idx = parseInt(m[1], 10) - 1;
                    if (this.pageNumbers[idx] != null) return this.pageNumbers[idx];
                }
                return this.fallbackPage;
            },
            askTutor: function () {
                if (this.tutorLoading) return;
                var q = (this.tutorQuestion || '').trim();
                if (!q) {
                    this.tutorError = { code: 'invalid_request', message: 'Bitte schreib zuerst eine Frage.' };
                    this._focus('tutorInput');
                    return;
                }
                if (q.length > TUTOR_MAX) q = q.slice(0, TUTOR_MAX);
                var self = this;
                this.tutorLoading = true;
                this.tutorError = null;
                this.liveMsg = 'Der Tutor denkt nach …';
                return api('POST', '/api/roleplay/tutor', {
                    lesson_id: this.lessonId, page: this.currentPage(), question: q,
                }).then(function (r) {
                    self.tutorLoading = false;
                    if (r.ok) {
                        self.tutorAsked = q;
                        self.tutorAnswer = r.data.answer || '';
                        self.tutorQuestion = '';
                        self.limits = r.data.limits || self.limits;
                        self.liveMsg = 'Antwort vom Tutor: ' + self.tutorAnswer;
                        self.$nextTick(function () { self._focus('tutorAnswer'); });
                        return;
                    }
                    if (r.data && r.data.limits) self.limits = r.data.limits;
                    self.tutorError = { code: r.data.error, message: r.data.message || 'Da ist etwas schiefgelaufen.' };
                    self.liveMsg = self.tutorError.message;
                });
            },
            onTutorEnter: function (ev) {
                if (ev.isComposing || ev.shiftKey) return;
                ev.preventDefault();
                this.askTutor();
            },
        };
    };
})();
