/* ════════════════════════════════════════════════════════════════════════
   Kana Storm — endloser Arcade-Loop gegen die Uhr (keyboard-first).
   Eigenständige Alpine-Komponente, bewusst GETRENNT vom Matching-Spiel
   (kana_grid_game.js) — das bleibt unangetastet. Wiederverwendet wird nur:
     • die kanonische Kana-Datenquelle: /api/practice/kana/session/public
       (Gast, ohne Login) → { character, romanization, type, row }
     • die Design-Tokens aus custom.css (CSS liegt in _kana_storm_styles.html)

   Surfaces (alle ohne Login, inline — KEIN iframe):
     • Vollbild-Seite  /practice/kana/storm     (practice_kana_storm.html)
     • Startseiten-Karte im Gast-Hero            (index.html)
     • Einstieg von /practice/kana               (Verlinkung auf die Seite)

   Global definiert (function declaration) und via defer VOR Alpine geladen
   (base.html) — wie kanaGridGame/kanaSettings —, damit x-data="kanaStormGame()"
   beim Alpine-Init aufgelöst werden kann.
   ════════════════════════════════════════════════════════════════════════ */

/* ── Justierbare Konstanten ──────────────────────────────────────────────
   Tempo UND Genauigkeit zählen, blindes Raten lohnt nicht: Punkte gibt es
   NUR bei Treffer, der Tempo-Bonus belohnt schnelles Wissen, der Combo-Faktor
   skaliert Serien — ein Fehler kostet die Combo + die Aufdeck-Zeit (Sekunden,
   die im Loop gegen die Uhr fehlen). Alle Werte hier zentral & leicht änderbar. */
const KANA_STORM_SCORING = {
    BASE: 10,             // Grundpunkte pro richtiger Antwort
    SPEED_MAX: 10,        // max. Tempo-Bonus (Antwort praktisch sofort)
    SPEED_WINDOW_MS: 4000, // ab dieser Antwortzeit kein Tempo-Bonus mehr (linear)
    COMBO_STEP: 0.1,      // +10 % Multiplikator je Combo-Stufe
    COMBO_MAX: 3.0,       // Multiplikator-Deckel (Serien bleiben belohnt, nicht absurd)
    FLAME_AT: 5,          // ab dieser Combo erscheint das 🔥
    OK_BEAT_MS: 200,      // kurze Erfolgs-Pause: grüner Flash sichtbar + aria-live sagt Treffer an
    OK_BEAT_MS_REDUCED: 100, // kürzer bei prefers-reduced-motion
    REVEAL_MS: 900,       // wie lange die richtige Lösung nach einem Fehler steht
    REVEAL_MS_REDUCED: 500, // kürzer bei prefers-reduced-motion
};

/* Akzeptierte Romaji-Alternativen über der kanonischen DB-`romanization`
   (die ist einwertig, z. B. nur "shi"). KEIN zweites Kana-Dataset — nur eine
   dünne, leicht erweiterbare Akzeptanz-Schicht. Die Sonderfälle を/ん hängen
   am ZEICHEN (robust, egal welche Schreibweise die DB kanonisch führt) und
   werden in buildAcceptSet() ergänzt. */
const KANA_STORM_ROMAJI_VARIANTS = {
    shi: ['si'],
    chi: ['ti'],
    tsu: ['tu'],
    fu: ['hu'],
    ji: ['zi'],
    // n / nn / n'  → siehe Zeichen-Sonderfall ん・ン
    // wo / o       → siehe Zeichen-Sonderfall を・ヲ
};

/* Baut die Menge akzeptierter Eingaben für eine Kana-Karte aus der
   kanonischen romanization + Varianten + Zeichen-Sonderfällen. */
function buildAcceptSet(item) {
    const rom = (item.romanization || '').toLowerCase().trim();
    const set = new Set();
    if (rom) {
        set.add(rom);
        (KANA_STORM_ROMAJI_VARIANTS[rom] || []).forEach((v) => set.add(v));
    }
    // を/ヲ: sowohl "wo" als auch "o" akzeptieren — unabhängig vom DB-Wert.
    if (item.character === 'を' || item.character === 'ヲ') {
        set.add('wo'); set.add('o');
    }
    // ん/ン: "n", "nn" und das Wāpuro-"n'" akzeptieren.
    if (item.character === 'ん' || item.character === 'ン') {
        set.add('n'); set.add('nn'); set.add("n'");
    }
    return set;
}

function kanaStormGame(opts) {
    opts = opts || {};
    const FOCUS_MQ = '(min-width: 700px)'; // nur Desktop auto-fokussieren (Mobile: kein Tastatur-Popup)

    return {
        // ── Konfiguration (auf dem Start-Screen gewählt) ──
        schrift: 'hiragana',   // 'hiragana' | 'katakana' | 'both'
        duration: 60,          // 60 | 120 (Sekunden)
        backUrl: opts.backUrl || null,         // Vollbild: Zurück-Link; Startseite: null
        registerUrl: opts.registerUrl || null, // Konto-CTA (optional, vom Template gesetzt)

        // ── Phasen / Daten ──
        phase: 'start',        // 'start' | 'loading' | 'playing' | 'ended' | 'error'
        loadError: '',
        pool: [],              // [{ character, romanization, type, accepts:Set }]
        current: null,

        // ── Laufzeit ──
        score: 0,
        combo: 1,
        bestCombo: 1,
        count: 0,
        timeLeft: 0,
        inputVal: '',
        choices: [],
        fb: '',                // '' | 'ok' | 'bad' (steuert grün/rot-Klassen)
        fbText: ' ',      // Feedback-/Screenreader-Text
        revealing: false,      // nach einem Fehler kurz die Lösung zeigen (Eingabe gesperrt)
        kanaIn: false,         // Einblend-Animation des Zeichens
        popCombo: false,       // Combo-Pop-Animation

        // ── Bestscore (localStorage, pro Schrift+Dauer) ──
        best: 0,
        isNewBest: false,

        reduceMotion: false,
        _endAt: 0,
        _shownAt: 0,
        _timerId: null,
        _revealTimer: null,

        // ────────────────────────────────────────────────────────────────
        init() {
            try {
                this.reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
            } catch (e) { /* matchMedia evtl. nicht verfügbar */ }
            // Letzte Auswahl wiederherstellen (Privatmodus → Defaults bleiben).
            const s = this._ls('kanaStormSchrift');
            if (['hiragana', 'katakana', 'both'].includes(s)) this.schrift = s;
            const d = parseInt(this._ls('kanaStormDur') || '', 10);
            if (d === 60 || d === 120) this.duration = d;
            this.loadBest();
        },

        // ── localStorage-Helfer (Privatmodus-sicher) ──
        _ls(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
        _lsSet(k, v) { try { localStorage.setItem(k, String(v)); } catch (e) { /* noop */ } },

        // ── Konfig-Setter (nicht während einer laufenden Runde) ──
        setSchrift(s) {
            if (this.phase === 'playing') return;
            this.schrift = s; this._lsSet('kanaStormSchrift', s); this.loadBest();
        },
        setDuration(d) {
            if (this.phase === 'playing') return;
            this.duration = d; this._lsSet('kanaStormDur', d); this.loadBest();
        },
        schriftLabel() {
            return { hiragana: 'Hiragana', katakana: 'Katakana', both: 'Beide' }[this.schrift] || '';
        },

        // ── Bestscore ──
        _bestKey() { return 'kanaStormBest:' + this.schrift + ':' + this.duration; },
        loadBest() {
            const v = parseInt(this._ls(this._bestKey()) || '0', 10);
            this.best = v > 0 ? v : 0;
            this.isNewBest = false;
        },

        // ── Runde starten: Pool laden, dann Loop ──
        async start() {
            this.phase = 'loading';
            this.loadError = '';
            let data;
            try {
                // Gast-Endpoint (ohne Login): voller Referenz-Scope der gewählten
                // Schrift. Storm bleibt fokussiert (Grund-Gojuon, kein Dakuten) —
                // die Anzahl ist die Pool-Größe, gespielt wird endlos per Zufall.
                const params = new URLSearchParams({ schrift: this.schrift, dakuten: 'false' });
                const resp = await fetch('/api/practice/kana/session/public?' + params.toString());
                data = await resp.json();
            } catch (e) {
                this.phase = 'error';
                this.loadError = 'Die Kana konnten nicht geladen werden — bitte später erneut versuchen.';
                return;
            }
            const kana = (data && data.kana) || [];
            // Karten ohne romanization aussortieren: sie hätten keine korrekte
            // Antwort + erzeugten eine leere Tap-Option (in Prod hat jede Gojuon-
            // Kana eine Lesung — der Filter ist die robuste Absicherung).
            const usable = kana.filter((k) => (k.romanization || '').trim());
            if (!usable.length) {
                this.phase = 'error';
                this.loadError = (data && data.message)
                    || 'Gerade sind keine Kana verfügbar — bitte später erneut versuchen.';
                return;
            }
            this.pool = usable.map((k) => ({
                character: k.character,
                romanization: (k.romanization || '').toLowerCase(),
                type: k.type,
                accepts: buildAcceptSet(k),
            }));
            this._beginRound();
        },

        _beginRound() {
            this.score = 0; this.combo = 1; this.bestCombo = 1; this.count = 0;
            this.isNewBest = false; this.revealing = false;
            this.timeLeft = this.duration;
            this._endAt = Date.now() + this.duration * 1000;
            this.current = null; this.inputVal = '';
            this.fb = ''; this.fbText = ' ';
            this.phase = 'playing';
            this.nextKana();
            this._startTimer();
            if (window.kanaTrack) {
                window.kanaTrack('kana_storm_start', { schrift: this.schrift, dur: this.duration });
            }
        },

        _startTimer() {
            this._stopTimer();
            // Wall-clock-basiert (kein Drift): timeLeft aus _endAt - now.
            this._timerId = setInterval(() => {
                const left = (this._endAt - Date.now()) / 1000;
                this.timeLeft = Math.max(0, left);
                if (left <= 0) this.end();
            }, 100);
        },
        _stopTimer() {
            if (this._timerId) { clearInterval(this._timerId); this._timerId = null; }
        },

        _pickFromPool() {
            if (this.pool.length <= 1) return this.pool[0] || null;
            let k, guard = 0;
            do {
                k = this.pool[Math.floor(Math.random() * this.pool.length)];
            } while (this.current && k.character === this.current.character && guard++ < 20);
            return k;
        },

        nextKana() {
            this.current = this._pickFromPool();
            this.inputVal = '';
            this.fb = ''; this.fbText = ' ';
            this._shownAt = Date.now();
            this._buildChoices();
            if (!this.reduceMotion) {
                this.kanaIn = false;
                this.$nextTick(() => { this.kanaIn = true; });
            }
            this._focusInput();
        },

        // 4 Tap-Optionen: richtige romanization + 3 zufällige andere aus dem Pool.
        _buildChoices() {
            if (!this.current) { this.choices = []; return; }
            const set = new Set([this.current.romanization]);
            let guard = 0;
            while (set.size < 4 && guard++ < 80) {
                const r = this.pool[Math.floor(Math.random() * this.pool.length)].romanization;
                if (r) set.add(r);
            }
            this.choices = [...set].sort(() => Math.random() - 0.5);
        },

        _focusInput() {
            try {
                if (!window.matchMedia(FOCUS_MQ).matches) return;
            } catch (e) { return; }
            this.$nextTick(() => {
                const el = this.$refs.stormInput;
                if (el) setTimeout(() => { try { el.focus(); } catch (e) { /* noop */ } }, 20);
            });
        },

        _popCombo() {
            if (this.reduceMotion) return;
            this.popCombo = false;
            this.$nextTick(() => { this.popCombo = true; });
        },

        // ── Antwort prüfen (Tipp-Enter ODER Tap-Option) ──
        submit(val) {
            if (this.phase !== 'playing' || !this.current || this.revealing) return;
            val = (val || '').trim().toLowerCase();
            if (!val) return;

            if (this.current.accepts.has(val)) {
                // Treffer: Tempo-Bonus + Combo-Faktor.
                const dt = Date.now() - this._shownAt;
                const speed = KANA_STORM_SCORING.SPEED_MAX
                    * Math.max(0, Math.min(1, 1 - dt / KANA_STORM_SCORING.SPEED_WINDOW_MS));
                const mult = Math.min(
                    KANA_STORM_SCORING.COMBO_MAX,
                    1 + (this.combo - 1) * KANA_STORM_SCORING.COMBO_STEP
                );
                this.score += Math.round((KANA_STORM_SCORING.BASE + speed) * mult);
                this.count++;
                this.combo++;
                this.bestCombo = Math.max(this.bestCombo, this.combo);
                this._popCombo();
                this.fb = 'ok';
                this.fbText = '✓ ' + this.current.character + ' = ' + this.current.romanization;
                // Kurze Erfolgs-Pause, DANN weiter: ohne sie würde nextKana() fb/
                // fbText synchron im selben Tick zurücksetzen — Alpine flusht nur
                // den Endwert, sodass der grüne Treffer-Flash UND die aria-live-
                // Ansage nie ankämen. Der Beat hält den Loop trotzdem snappy.
                this._scheduleNext(this.reduceMotion
                    ? KANA_STORM_SCORING.OK_BEAT_MS_REDUCED
                    : KANA_STORM_SCORING.OK_BEAT_MS);
            } else {
                // Fehler: Combo zurück, Lösung kurz zeigen, dann nächstes Zeichen.
                // Das verfehlte Zeichen bleibt im Pool → kann (per Zufall) wiederkommen.
                this.combo = 1;
                this.fb = 'bad';
                this.fbText = '✗ ' + this.current.character + ' = ' + this.current.romanization;
                this._scheduleNext(this.reduceMotion
                    ? KANA_STORM_SCORING.REVEAL_MS_REDUCED
                    : KANA_STORM_SCORING.REVEAL_MS);
            }
        },

        // Eingabe sperren, das Feedback (Treffer/Fehler) für `delay` ms stehen
        // lassen (sichtbarer Flash + aria-live-Ansage), dann das nächste Zeichen.
        // Der Timer läuft bewusst weiter — die Pause kostet Zeit (beim Fehler Teil
        // der Strafe, beim Treffer nur ein kurzer Beat).
        _scheduleNext(delay) {
            this.inputVal = '';
            this.revealing = true;
            if (this._revealTimer) clearTimeout(this._revealTimer);
            this._revealTimer = setTimeout(() => {
                this.revealing = false;
                if (this.phase === 'playing') this.nextKana();
            }, delay);
        },

        // ── Runde beenden ──
        end() {
            this._stopTimer();
            if (this._revealTimer) { clearTimeout(this._revealTimer); this._revealTimer = null; }
            this.revealing = false;
            this.timeLeft = 0;
            this.fb = ''; this.fbText = ' ';
            if (this.score > this.best) {
                this.best = this.score;
                this.isNewBest = true;
                this._lsSet(this._bestKey(), this.score);
            }
            this.phase = 'ended';
            if (window.kanaTrack) {
                window.kanaTrack('kana_storm_end', {
                    schrift: this.schrift, dur: this.duration,
                    score: this.score, combo: this.bestCombo, count: this.count,
                });
            }
        },

        // "Nochmal" — gleiche Konfig, frische Runde (Pool ist geladen).
        again() {
            if (!this.pool.length) { this.start(); return; }
            this._beginRound();
            this._focusInput();
        },
        // Zurück zum Start-Screen (Konfig ändern).
        toStart() {
            this._stopTimer();
            if (this._revealTimer) { clearTimeout(this._revealTimer); this._revealTimer = null; }
            this.revealing = false;
            this.phase = 'start';
            this.loadBest();
        },

        // ── Anzeige-Helfer ──
        liveTimeLabel() {
            const t = Math.max(0, Math.ceil(this.timeLeft));
            return Math.floor(t / 60) + ':' + String(t % 60).padStart(2, '0');
        },
        timerPct() {
            if (!this.duration) return 0;
            return Math.max(0, Math.min(100, (this.timeLeft / this.duration) * 100));
        },
        comboLabel() {
            return this.combo >= KANA_STORM_SCORING.FLAME_AT
                ? '<span class="kstorm__flame" aria-hidden="true">🔥</span>×' + this.combo
                : '×' + this.combo;
        },
        endTitle() {
            if (this.isNewBest && this.score > 0) return 'Neuer Bestscore!';
            if (this.score >= 400) return 'Sturm-Meister!';
            if (this.score >= 150) return 'Stark!';
            return 'Solide!';
        },

        /* ── NICHT-ZIEL (Stub, bewusst NICHT gebaut) ─────────────────────────
           Daily-Modus: ein für ALLE Spieler identisches Tagesbrett + teilbarer
           Emoji-Block (Wordle-Mechanik). WICHTIG fürs spätere Bauen: das Brett
           MUSS serverseitig pro Tag fix und für alle Nutzer gleich erzeugt
           werden (deterministischer Seed pro Datum, ohne user_id) — sonst ist
           der geteilte Vergleich wertlos. Ein passender Endpoint existiert
           bereits konzeptionell (/api/practice/kana/daily-challenge nutzt einen
           datumsbasierten Gast-Seed); für Storm-Daily bräuchte es ein gleich
           geseedetes, ZEITLICH gespieltes 10er-Brett statt eines Grid-Bretts.
           Ebenfalls Nicht-Ziel: Wochen-Leaderboard + Account-XP (braucht Backend). */
    };
}
