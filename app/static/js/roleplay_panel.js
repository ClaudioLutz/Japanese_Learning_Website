/* Rollenspiel-Tutor am Lektionsdialog — Alpine-Komponente.
 *
 * window.roleplayPanel(contentId) wird im Partial
 * templates/partials/_roleplay_panel.html per x-data eingehaengt (nur wenn
 * roleplay_enabled und eingeloggt). API-Vertrag: docs/roleplay-api.md.
 *
 * Ablauf: GET scene → Rollenwahl → POST start → Zuege (POST turn) →
 * Abschluss (done im Zug oder POST end). Zweiter Tab „Frag zur Seite"
 * (POST tutor). Alle Fehler landen als Meldung im Panel, nie in der Konsole.
 */
(function () {
    'use strict';

    var TIMEOUT_MS = 65000;
    var GOAL_MAX = 120;
    var TUTOR_MAX = 300;
    var TEXT_MAX = 300;
    var ROMAJI_KEY = 'jpl-roleplay-romaji';

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
        }, function (err) {
            if (timer) clearTimeout(timer);
            var aborted = err && err.name === 'AbortError';
            return { ok: false, status: 0, data: aborted ? {
                error: 'timeout',
                message: 'Die Antwort hat zu lange gedauert. Dein Text ist noch da — bitte nochmal senden.',
            } : {
                error: 'network',
                message: 'Keine Verbindung zum Server. Bitte prüfe dein Internet und sende nochmal.',
            } };
        });
    }

    var RETRYABLE = { upstream_error: 1, timeout: 1, network: 1, unexpected: 1 };

    window.roleplayPanel = function (contentId) {
        return {
            contentId: contentId,
            lessonId: null,
            pageNumbers: [],
            fallbackPage: null,

            open: false,
            tab: 'play',               // play | tutor
            phase: 'idle',             // idle | loading | choose | starting | playing | done | unavailable
            scene: null,
            roleChoice: null,
            customGoal: '',
            session: null,
            log: [],                   // bisherige Zeilen {who:'bot'|'user', jp, de}
            bot: null,                 // aktuelle Bot-Zeile (BotTurn)
            showReading: false,
            showGerman: false,
            hintShown: false,
            input: '',
            romajiOn: true,
            sending: false,
            ending: false,
            error: null,               // {code, message, retry}
            limits: null,
            result: null,              // Abschluss {status, correction, correction_unavailable, xp_awarded, farewell}
            liveMsg: '',
            speaking: false,
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
            },

            // ── Ansichtshilfen ───────────────────────────────────────────
            get botName() { return (this.session && this.session.role_bot) || 'Partner'; },
            get userName() { return (this.session && this.session.role_user) || 'Du'; },
            get turnCount() { return (this.session && this.session.turn_count) || 0; },
            get maxTurns() { return (this.session && this.session.max_user_turns) || 8; },
            get minTurns() { return (this.session && this.session.min_user_turns) || 4; },
            get progressText() {
                return 'Zug ' + Math.min(this.turnCount + 1, this.maxTurns) + ' von ' + this.maxTurns;
            },
            get progressPercent() { return Math.round((this.turnCount / this.maxTurns) * 100); },
            get canEnd() { return this.phase === 'playing' && this.turnCount >= 1; },
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
            start: function () {
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

            _showBot: function (turn) {
                if (this.bot) this.log.push({ who: 'bot', jp: this.bot.jp, de: this.bot.de });
                this.bot = turn || null;
                this.showReading = false;
                this.showGerman = false;
                this.hintShown = false;
                if (turn) this.liveMsg = this.botName + ' sagt: ' + turn.jp + ' — ' + (turn.de || '');
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
                if (text.length > TEXT_MAX) text = text.slice(0, TEXT_MAX);
                this.input = text;
                var self = this;
                this.sending = true;
                this.error = null;
                this.liveMsg = this.botName + ' tippt …';
                return api('POST', '/api/roleplay/' + this.session.id + '/turn', { text: text }).then(function (r) {
                    self.sending = false;
                    if (r.ok) {
                        self.log.push({ who: 'user', jp: text, de: '' });
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
                            self._showBot(r.data.bot_turn);
                        }
                        return;
                    }
                    if (r.status === 409 || r.data.error === 'session_finished') {
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
                if (!this.session || this.ending) return;
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
                if (this.bot) this.log.push({ who: 'bot', jp: this.bot.jp, de: this.bot.de });
                this.bot = null;
                this.result = res;
                this.phase = 'done';
                this.liveMsg = 'Gespräch beendet. ' + (res.xp_awarded ? ('Plus ' + res.xp_awarded + ' XP.') : '');
                var self = this;
                this.$nextTick(function () { self._focus('doneTitle'); });
            },
            restart: function () {
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
                if (this.phase === 'playing') return this.send();
                if (this.phase === 'choose') return this.start();
                return this.loadScene();
            },

            // ── Audio ───────────────────────────────────────────────────
            stopAudio: function () {
                if (this._audio) { try { this._audio.pause(); } catch (e) { /* egal */ } this._audio = null; }
                try { if ('speechSynthesis' in window) window.speechSynthesis.cancel(); } catch (e) { /* egal */ }
                this.speaking = false;
            },
            speak: function (text) {
                if (!text) return;
                var self = this;
                this.stopAudio();
                this.speaking = true;
                fetch('/api/tts', {
                    method: 'POST',
                    credentials: 'same-origin',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken() },
                    body: JSON.stringify({ text: text, lang: 'ja', speed: 0.85 }),
                }).then(function (resp) {
                    if (!resp.ok) throw new Error('tts');
                    return resp.blob();
                }).then(function (blob) {
                    var url = URL.createObjectURL(blob);
                    var audio = new Audio(url);
                    self._audio = audio;
                    var done = function () { URL.revokeObjectURL(url); if (self._audio === audio) { self._audio = null; self.speaking = false; } };
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
                    if (!('speechSynthesis' in window)) { self.speaking = false; return; }
                    var u = new SpeechSynthesisUtterance(text);
                    u.lang = 'ja-JP';
                    u.rate = 0.8;
                    var v = window.speechSynthesis.getVoices().filter(function (x) { return x.lang && x.lang.indexOf('ja') === 0; })[0];
                    if (v) u.voice = v;
                    u.onend = u.onerror = function () { self.speaking = false; };
                    window.speechSynthesis.speak(u);
                } catch (e) {
                    self.speaking = false;
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
