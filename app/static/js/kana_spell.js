/* ════════════════════════════════════════════════════════════════════════
   Kana-Schreibspiel — Woerter Tile-fuer-Tile buchstabieren.
   Drittes Kana-Spiel auf /practice/kana (neben Zuordnung `kana_grid_game.js`
   + Storm `kana_storm.js`, beide unangetastet). Eigenstaendige Alpine-
   Komponente. Wiederverwendet wird nur:
     • der geteilte Scope $store.kanaScope (Schrift + Reihen)
     • der Wort-Pool-Endpoint /api/practice/kana/spell/words (Gast-offen)
     • der TTS-Endpoint /api/tts (Audio-Cue; Gast-offen, 30/min)
     • die Design-Tokens aus custom.css (Spiel-CSS in _kana_spell_stage.html)

   Mechanik (Pfad A — REINE Kana-Woerter): aus dem gewaehlten Kana-Scope werden
   Woerter freigeschaltet, deren SCHRIFTFORM sich mit den gewaehlten Kana
   schreiben laesst; sie werden einzeln zufaellig abgefragt. Der Lerner tippt
   Tiles in geordnete Slots (Tap-to-Place + Zuruecknehmen). Quelle umschaltbar:
   "alle" (Default) oder "nur freigeschaltete"; Cue umschaltbar:
   Bedeutung / Romaji / Audio.

   Eigene leichte Wertung (KEIN FSRS-Eingriff): Bestwert pro Schrift+Quelle im
   localStorage; eingeloggt zusaetzlich Server-Persistenz (XP) ueber /spell-finish.
   Global definiert + via defer VOR Alpine geladen (base.html).
   ════════════════════════════════════════════════════════════════════════ */

const KANA_SPELL_SCORING = {
    BASE: 10,            // Grundpunkte pro richtig buchstabiertem Wort
    STREAK_STEP: 2,      // +2 pro Serien-Stufe
    STREAK_BONUS_MAX: 20, // Deckel des Serien-Bonus
    OK_BEAT_MS: 650,     // Erfolg kurz stehen lassen (gruener Flash + Ansage)
    OK_BEAT_MS_REDUCED: 350,
    REVEAL_MS: 1400,     // nach Fehler die korrekte Schreibung zeigen
    REVEAL_MS_REDUCED: 800,
};
const KANA_SPELL_ROUND_LEN = 10;   // Woerter pro Runde
const KANA_SPELL_MIN_TRAY = 5;     // mind. so viele Tiles in der Ablage
const KANA_SPELL_EXTRA_TILES = 3;  // Distraktoren ueber die Wortlaenge hinaus

function kanaSpellGame(opts) {
    opts = opts || {};
    return {
        // ── Konfiguration ──
        schrift: 'hiragana',          // vom geteilten Scope
        selectedRows: [],             // vom geteilten Scope
        scopeExternal: !!opts.scopeExternal,
        source: 'all',                // effektiv genutzte Quelle: 'all' | 'unlocked'
        _autoMode: true,              // true = Quelle folgt automatisch der Reihen-Auswahl
        cue: 'bedeutung',             // 'bedeutung' | 'romaji' | 'audio'

        // ── Wort-Pool ──
        words: [],                    // [{ word, reading, romaji, meaning_de, audio_url }]
        wordCount: 0,                 // WAHRE Gesamtzahl schreibbarer Woerter (Zaehler)
        poolChars: [],                // Distraktor-Quelle (alle Kana der Pool-Woerter)
        countLoading: false,
        loadError: '',
        _countSeq: 0,
        _countTimer: null,

        // ── Phasen: 'start' | 'loading' | 'playing' | 'ended' | 'error' ──
        phase: 'start',

        // ── Runde ──
        roundWords: [],
        roundIdx: 0,
        current: null,                // aktuelles Wort-Objekt
        slots: [],                    // [{ id, char } | null] — Antwort-Reihe
        tray: [],                     // [{ id, char, used }] — Tile-Ablage
        locked: false,                // nach Prüfen/Reveal kurz gesperrt
        revealing: false,
        fb: '',                       // '' | 'ok' | 'bad'
        fbText: ' ',                  // aria-live-Text

        // ── Laufzeit-Summen ──
        score: 0,
        streak: 0,
        bestStreak: 0,
        correct: 0,
        misses: 0,

        // ── Bestwert (localStorage, pro Schrift+Quelle) ──
        best: 0,
        isNewBest: false,
        firstBaseline: false,

        // ── Konto (eingeloggt): Server-Persistenz + XP ──
        loggedIn: !!opts.loggedIn,
        csrfToken: opts.csrfToken || '',
        serverBest: 0,
        serverGames: 0,
        lastXp: 0,

        reduceMotion: false,
        isMobile: false,              // Mobile (<768px): ab >4 Reihen Zufall statt Reihen
        _audio: null,
        _revealTimer: null,
        _mqMobile: null,

        // ────────────────────────────────────────────────────────────────
        init() {
            try {
                this.reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
            } catch (e) { /* noop */ }
            // Mobile-Erkennung (gleiche Schwelle wie die Seite: 767px). Reaktiv, falls
            // gedreht/skaliert wird — der Mobile-Cap (>4 Reihen → Zufall) haengt davon ab.
            try {
                this._mqMobile = window.matchMedia('(max-width: 767px)');
                this.isMobile = this._mqMobile.matches;
                const onMq = () => { this.isMobile = this._mqMobile.matches; this._applyAutoSource(); this.refreshCount(); };
                if (this._mqMobile.addEventListener) this._mqMobile.addEventListener('change', onMq);
                else if (this._mqMobile.addListener) this._mqMobile.addListener(onMq);
            } catch (e) { /* noop */ }

            // Nur den Cue persistieren — die QUELLE folgt automatisch der Reihen-Auswahl
            // (Auto-Modus), damit gewaehlte Reihen nicht von alter Persistenz ueber-
            // stimmt werden.
            const cue = this._ls('kanaSpellCue');
            if (['bedeutung', 'romaji', 'audio'].includes(cue)) this.cue = cue;

            if (this.scopeExternal) {
                const sc = this.$store && this.$store.kanaScope;
                if (sc) {
                    this.schrift = sc.schrift;
                    this.selectedRows = [...sc.rows];
                    // Scope-Aenderungen reaktiv mitziehen → Auto-Quelle + Zaehler neu.
                    this.$watch('$store.kanaScope.schrift', (v) => {
                        this.schrift = v; this._applyAutoSource(); this.refreshCount();
                    });
                    this.$watch('$store.kanaScope.rows', (v) => {
                        this.selectedRows = [...(v || [])];
                        this._autoMode = true;        // neue Reihen-Auswahl → wieder Auto
                        this._applyAutoSource();
                        this.refreshCount();
                    });
                }
            }
            // Phasenwechsel nach oben melden → /practice/kana blendet das Chrome
            // (Kopf + geteilter Scope + Tabs) aus, sobald gespielt wird.
            this.$watch('phase', (p) => { this.$dispatch('kana-spell-phase', p); });

            this._applyAutoSource();
            this.loadBest();
            this.refreshCount();
        },

        // ── localStorage-Helfer ──
        _ls(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
        _lsSet(k, v) { try { localStorage.setItem(k, String(v)); } catch (e) { /* noop */ } },

        // ── Reihen-Auswahl & Mobile-Cap ───────────────────────────────────
        // Sind einzelne Reihen gewaehlt? (geteilter Scope: rows=[] = „Alle" → nein)
        get rowsActive() { return this.selectedRows.length > 0; },
        // Mobile-Regel: ab >4 Reihen ist reihengesteuertes Spielen NICHT nutzbar
        // → Rueckfall auf eine Zufalls-Auswahl (wie bisher „alle Wörter").
        get mobileRowCapHit() { return this.isMobile && this.selectedRows.length > 4; },
        // Kann gerade reihengesteuert gespielt werden?
        get rowsModeAvailable() { return this.rowsActive && !this.mobileRowCapHit; },
        // Labels der aktiven Reihen — exakt die Chips des geteilten Scopes
        // (K, S, あいうえお …), damit Auswahl oben und Anzeige hier uebereinstimmen.
        activeRowLabels() {
            const sc = this.$store && this.$store.kanaScope;
            const rows = (sc && sc.ROWS) || [];
            const byKey = {};
            rows.forEach((r) => { byKey[r.key] = r.label; });
            return this.selectedRows.map((k) => byKey[k] || k);
        },

        // Quelle automatisch aus der Reihen-Auswahl ableiten (sofern der Nutzer sie
        // nicht manuell ueberstimmt hat): Reihen gewaehlt + nutzbar → reihengesteuert;
        // sonst alle Woerter (Zufall). Best-Wert bei Quellen-Wechsel mitziehen.
        _applyAutoSource() {
            const prev = this.source;
            if (!this._autoMode) {
                // Manuelle Wahl „aus deinen Reihen", die der Mobile-Cap unmoeglich
                // macht, faellt sicher auf „alle" zurueck.
                if (this.source === 'unlocked' && !this.rowsModeAvailable) this.source = 'all';
            } else {
                this.source = this.rowsModeAvailable ? 'unlocked' : 'all';
            }
            if (this.source !== prev) this.loadBest();
        },

        // ── Konfig-Setter ──
        setSource(s) {
            if (this.phase === 'playing' || (s !== 'all' && s !== 'unlocked')) return;
            if (s === 'unlocked' && !this.rowsModeAvailable) return;   // nicht waehlbar
            this._autoMode = false;       // ab jetzt manuelle Wahl (bis Reihen wechseln)
            this.source = s;
            this.loadBest(); this.refreshCount();
        },
        setCue(c) {
            if (this.phase === 'playing' || !['bedeutung', 'romaji', 'audio'].includes(c)) return;
            this.cue = c; this._lsSet('kanaSpellCue', c);
        },
        schriftLabel() {
            return { hiragana: 'Hiragana', katakana: 'Katakana', both: 'Beide' }[this.schrift] || '';
        },
        scopeLabel() {
            let s = this.schriftLabel();
            s += this.source === 'all' ? ' · alle Wörter' : ' · aus deinen Reihen';
            return s;
        },
        // Counter-Beschriftung passt sich der effektiven Quelle an.
        countNoun() {
            if (this.source === 'unlocked') {
                return this.wordCount === 1 ? 'Wort aus deinen Reihen' : 'Wörter aus deinen Reihen';
            }
            return this.wordCount === 1 ? 'Wort schreibbar' : 'Wörter schreibbar';
        },
        // Kontext-Hinweis je nach Lage (Mobile-Cap > Reihen-Modus > Reihen-Tipp > alle).
        sourceHint() {
            if (this.mobileRowCapHit) {
                return 'Auf dem Handy ab 5 Reihen Zufalls-Auswahl — wähle ≤ 4 Reihen fürs gezielte Üben.';
            }
            if (this.source === 'unlocked') {
                return 'Nur Wörter, die sich mit deinen gewählten Reihen schreiben lassen.';
            }
            if (this.rowsActive) {
                return 'Tippe „Aus deinen Reihen", um gezielt deine gewählten Reihen zu üben.';
            }
            return 'Alle schreibbaren N5-Wörter dieser Schrift.';
        },

        // ── Live-Wortzaehler (debounced) — laedt zugleich den Spiel-Pool ──
        refreshCount() {
            if (this._countTimer) clearTimeout(this._countTimer);
            this.countLoading = true;
            this._countTimer = setTimeout(() => { this._loadWords(); }, 250);
        },
        async _loadWords() {
            const seq = ++this._countSeq;
            this.loadError = '';
            const params = new URLSearchParams({ schrift: this.schrift, source: this.source });
            if (this.source === 'unlocked' && this.selectedRows.length) {
                params.set('rows', this.selectedRows.join(','));
            }
            let data;
            try {
                const resp = await fetch('/api/practice/kana/spell/words?' + params.toString());
                data = await resp.json();
            } catch (e) {
                if (seq !== this._countSeq) return;
                this.countLoading = false;
                this.loadError = 'Die Wörter konnten nicht geladen werden — bitte später erneut versuchen.';
                return;
            }
            if (seq !== this._countSeq) return;  // veraltete Antwort verwerfen
            this.words = (data && data.words) || [];
            this.wordCount = (data && typeof data.count === 'number') ? data.count : this.words.length;
            // Distraktor-Quelle: alle Kana der Pool-Woerter (immer im Scope).
            const chars = new Set();
            this.words.forEach((w) => { for (const ch of (w.word || '')) chars.add(ch); });
            this.poolChars = [...chars];
            this.countLoading = false;
        },

        // Ist ein Cue für den aktuellen Pool nutzbar? (sonst Knopf deaktivieren)
        cueCount(c) {
            if (c === 'bedeutung') return this.words.filter((w) => w.meaning_de).length;
            if (c === 'romaji') return this.words.filter((w) => w.romaji).length;
            return this.words.length;  // Audio: TTS aus reading/word geht immer
        },
        cueAvailable(c) { return this.cueCount(c) > 0; },

        // Woerter, die den gewaehlten Cue bedienen koennen.
        _cueWords() {
            if (this.cue === 'bedeutung') return this.words.filter((w) => w.meaning_de);
            if (this.cue === 'romaji') return this.words.filter((w) => w.romaji);
            return this.words.slice();
        },

        get canStart() {
            return !this.countLoading && !this.loadError && this._cueWords().length > 0;
        },

        // ── Runde starten ──
        start() {
            if (this.countLoading) return;
            const usable = this._cueWords();
            if (!usable.length) {
                this.phase = 'error';
                this.loadError = this.wordCount === 0
                    ? (this.source === 'unlocked'
                        ? 'Mit diesen Reihen lässt sich noch kein Wort schreiben — wähle mehr Reihen oder „alle Wörter".'
                        : 'Gerade sind keine Wörter verfügbar.')
                    : 'Für diesen Hinweis-Modus gibt es gerade keine Wörter — wähle einen anderen Cue.';
                return;
            }
            // Zufaellige Runde (ohne Wiederholung innerhalb der Runde).
            const shuffled = usable.slice().sort(() => Math.random() - 0.5);
            this.roundWords = shuffled.slice(0, Math.min(KANA_SPELL_ROUND_LEN, shuffled.length));
            this.roundIdx = 0;
            this.score = 0; this.streak = 0; this.bestStreak = 0;
            this.correct = 0; this.misses = 0;
            this.isNewBest = false; this.firstBaseline = false; this.lastXp = 0;
            this.phase = 'playing';
            this._beginWord();
            if (window.kanaTrack) {
                window.kanaTrack('kana_spell_start', {
                    schrift: this.schrift, source: this.source, cue: this.cue,
                    rows: this.selectedRows.length || 'alle',
                });
            }
        },

        _beginWord() {
            this.current = this.roundWords[this.roundIdx];
            this.locked = false;
            this.revealing = false;
            this.fb = ''; this.fbText = ' ';
            this._buildBoard(this.current);
            if (this.cue === 'audio') this.$nextTick(() => this.playWord());
        },

        // Slots (leer, 1 pro Zeichen) + Tile-Ablage (Wortzeichen + Distraktoren).
        _buildBoard(wordObj) {
            const chars = [...(wordObj.word || '')];
            this.slots = chars.map(() => null);
            const tiles = chars.slice();   // die benoetigten Zeichen
            // Distraktoren aus dem Pool-Charset (nicht aus dem Wort), bis genug.
            const target = Math.max(KANA_SPELL_MIN_TRAY, chars.length + KANA_SPELL_EXTRA_TILES);
            const distractorSrc = this.poolChars.length ? this.poolChars : chars;
            let guard = 0;
            while (tiles.length < target && guard++ < 200) {
                const ch = distractorSrc[Math.floor(Math.random() * distractorSrc.length)];
                tiles.push(ch);
            }
            // Mischen + mit stabiler ID versehen (Zeichen duerfen sich wiederholen).
            this.tray = tiles
                .sort(() => Math.random() - 0.5)
                .map((ch, i) => ({ id: i, char: ch, used: false }));
        },

        // ── Tap-to-Place ──
        tapTray(i) {
            if (this.locked) return;
            const tile = this.tray[i];
            if (!tile || tile.used) return;
            const slotIdx = this.slots.findIndex((s) => s === null);
            if (slotIdx === -1) return;   // voll
            this.slots[slotIdx] = { id: tile.id, char: tile.char };
            tile.used = true;
            this.slots = [...this.slots];
            this.tray = [...this.tray];
        },
        tapSlot(i) {
            if (this.locked) return;
            const filled = this.slots[i];
            if (!filled) return;
            const tile = this.tray.find((t) => t.id === filled.id);
            if (tile) tile.used = false;
            this.slots[i] = null;
            this.slots = [...this.slots];
            this.tray = [...this.tray];
        },
        clearSlots() {
            if (this.locked) return;
            this.tray.forEach((t) => { t.used = false; });
            this.slots = this.slots.map(() => null);
            this.tray = [...this.tray];
        },

        get filledCount() { return this.slots.filter((s) => s !== null).length; },
        get isComplete() { return this.slots.length > 0 && this.filledCount === this.slots.length; },
        answerStr() { return this.slots.map((s) => (s ? s.char : '')).join(''); },

        // ── Antwort prüfen (Knopf, aktiv wenn alle Slots gefüllt) ──
        check() {
            if (this.locked || !this.isComplete || !this.current) return;
            const ok = this.answerStr() === this.current.word;
            this.locked = true;
            if (ok) {
                const bonus = Math.min(this.streak * KANA_SPELL_SCORING.STREAK_STEP,
                                       KANA_SPELL_SCORING.STREAK_BONUS_MAX);
                this.score += KANA_SPELL_SCORING.BASE + bonus;
                this.correct++;
                this.streak++;
                this.bestStreak = Math.max(this.bestStreak, this.streak);
                this.fb = 'ok';
                this.fbText = '✓ ' + this.current.word + (this.current.romaji ? ' (' + this.current.romaji + ')' : '');
                this._scheduleNext(this.reduceMotion
                    ? KANA_SPELL_SCORING.OK_BEAT_MS_REDUCED : KANA_SPELL_SCORING.OK_BEAT_MS);
            } else {
                // FALSCH → NICHT weiterspringen: Serie zuruecksetzen, kurz rot
                // melden, dann wieder zum Korrigieren freigeben (Kästchen antippen →
                // Tile zurueck in die Ablage → richtige setzen → erneut „Prüfen").
                // Die korrekte Loesung wird NICHT gezeigt — dafuer ist „Auflösen" da,
                // das das Wort als verfehlt wertet und weitergeht.
                this.streak = 0;
                this.fb = 'bad';
                this.fbText = 'Noch nicht ganz — tippe ein Kästchen an, um es zu korrigieren.';
                const hold = this.reduceMotion
                    ? KANA_SPELL_SCORING.OK_BEAT_MS_REDUCED : KANA_SPELL_SCORING.OK_BEAT_MS;
                if (this._revealTimer) clearTimeout(this._revealTimer);
                this._revealTimer = setTimeout(() => {
                    if (this.phase !== 'playing') return;
                    this.fb = '';            // roten Flash wegnehmen
                    this.locked = false;     // wieder editierbar
                }, hold);
            }
        },

        // „Auflösen" — als Fehler werten, Lösung zeigen, weiter.
        reveal() {
            if (this.locked || !this.current) return;
            this.locked = true;
            this.misses++;
            this.streak = 0;
            this.revealing = true;
            this.fb = 'bad';
            this.fbText = '✗ richtig: ' + this.current.word;
            this._scheduleNext(this.reduceMotion
                ? KANA_SPELL_SCORING.REVEAL_MS_REDUCED : KANA_SPELL_SCORING.REVEAL_MS);
        },

        _scheduleNext(delay) {
            if (this._revealTimer) clearTimeout(this._revealTimer);
            this._revealTimer = setTimeout(() => {
                if (this.phase !== 'playing') return;
                this.roundIdx++;
                if (this.roundIdx >= this.roundWords.length) { this.end(); return; }
                this._beginWord();
            }, delay);
        },

        // ── Runde beenden ──
        end() {
            if (this._revealTimer) { clearTimeout(this._revealTimer); this._revealTimer = null; }
            this.revealing = false; this.locked = false;
            this.fb = ''; this.fbText = ' ';
            const priorBest = this.best;
            if (this.score > priorBest) {
                this.best = this.score;
                this._lsSet(this._bestKey(), this.score);
            }
            this.isNewBest = priorBest > 0 && this.score > priorBest;
            this.firstBaseline = priorBest === 0 && this.score > 0;
            this.phase = 'ended';
            if (this.loggedIn) {
                this._postResult({
                    schrift: this.schrift, source: this.source, cue: this.cue,
                    score: this.score, best_streak: this.bestStreak,
                    correct: this.correct, misses: this.misses,
                });
            }
            if (window.kanaTrack) {
                window.kanaTrack('kana_spell_end', {
                    schrift: this.schrift, source: this.source, cue: this.cue,
                    score: this.score, correct: this.correct, misses: this.misses,
                });
            }
        },

        again() {
            this.phase = 'start';
            this.loadBest();
            this.start();
        },
        toStart() {
            if (this._revealTimer) { clearTimeout(this._revealTimer); this._revealTimer = null; }
            this.revealing = false; this.locked = false;
            this.phase = 'start';
            this.loadBest();
        },

        // ── Bestwert (pro Schrift + Quelle) ──
        _bestKey() { return 'kanaSpellBest:' + this.schrift + ':' + this.source; },
        loadBest() {
            const v = parseInt(this._ls(this._bestKey()) || '0', 10);
            this.best = v > 0 ? v : 0;
            this.isNewBest = false; this.firstBaseline = false;
        },
        bestLine() {
            if (this.best <= 0) return '';
            const scope = ' · ' + this.scopeLabel();
            if (this.isNewBest) return '🏆 Neuer Bestwert: ' + this.best + scope;
            if (this.firstBaseline) return 'Bestwert gesetzt: ' + this.best + scope;
            return 'Bestwert: ' + this.best + scope;
        },
        accuracy() {
            const t = this.correct + this.misses;
            return t ? Math.round(this.correct / t * 100) : 0;
        },

        // ── Server-Persistenz (nur eingeloggt) — fire-and-forget ──
        async _postResult(payload) {
            if (!this.loggedIn) return;
            try {
                const resp = await fetch('/api/practice/kana/spell-finish', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.csrfToken || '' },
                    body: JSON.stringify(payload),
                });
                if (!resp.ok) return;
                const d = await resp.json();
                if (typeof d.best_score === 'number') this.serverBest = d.best_score;
                if (typeof d.games === 'number') this.serverGames = d.games;
                if (typeof d.xp_awarded === 'number') this.lastXp = d.xp_awarded;
            } catch (e) { /* offline → bleibt clientseitig */ }
        },

        // ── Cue-Anzeige ──
        promptText() {
            if (!this.current) return '';
            if (this.cue === 'romaji') return this.current.romaji || '';
            if (this.cue === 'bedeutung') return this.current.meaning_de || '';
            return '';  // audio: nur Lautsprecher-Knopf
        },
        promptLabel() {
            return { bedeutung: 'Bedeutung', romaji: 'Romaji', audio: 'Hören' }[this.cue] || '';
        },

        // ── Audio (Audio-Cue + optionaler Hör-Knopf) ──
        async playWord() {
            const w = this.current;
            if (!w) return;
            try {
                if (this._audio) { this._audio.pause(); this._audio = null; }
                if (w.audio_url) {
                    this._audio = new Audio(w.audio_url);
                    this._audio.play().catch(() => { this._ttsPlay(w); });
                    return;
                }
                this._ttsPlay(w);
            } catch (e) { /* Audio nicht verfuegbar */ }
        },
        async _ttsPlay(w) {
            const text = w.reading || w.word;
            if (!text) return;
            try {
                const resp = await fetch('/api/tts', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text, lang: 'ja', model: 'chirp' }),
                });
                if (!resp.ok) return;
                const blob = await resp.blob();
                const url = URL.createObjectURL(blob);
                this._audio = new Audio(url);
                this._audio.play().catch(() => {});
                this._audio.addEventListener('ended', () => URL.revokeObjectURL(url), { once: true });
            } catch (e) { /* noop */ }
        },

        progressLabel() {
            return Math.min(this.roundIdx + 1, this.roundWords.length) + '/' + this.roundWords.length;
        },
        endTitle() {
            if (this.isNewBest && this.score > 0) return 'Neuer Bestwert!';
            const acc = this.accuracy();
            if (acc >= 90) return 'Ausgezeichnet!';
            if (acc >= 60) return 'Stark!';
            return 'Weiter so!';
        },
    };
}
