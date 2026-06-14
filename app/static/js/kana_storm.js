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

/* Gojuon-Reihengrössen pro Schrift — für die Live-Anzahl der Auswahl (ohne
   API-Call). Keys identisch zu kana_rows.py / der Reihen-Pills-Liste im Template. */
const KANA_STORM_ROW_SIZES = {
    vowels: 5, k: 5, s: 5, t: 5, n: 5, h: 5, m: 5, y: 3, r: 5, w: 2, n_kons: 1,
    g: 5, z: 5, d: 5, b: 5, p: 5,
};
const KANA_STORM_BASE_COUNT = 46; // Grund-Set (alle Basis-Reihen, ohne Dakuten)

/* Notnagel-Distraktoren, falls die gewählte Auswahl zu klein für 4 distinkte
   Tap-Optionen ist (z.B. nur die ん-Reihe) — der Tipp-Modus bleibt davon
   unberührt, hier geht es nur um genug Auswahlknöpfe. */
const KANA_STORM_FALLBACK_ROMAJI = [
    'a', 'i', 'u', 'e', 'o', 'ka', 'ki', 'ku', 'ke', 'ko', 'sa', 'shi', 'su',
    'ta', 'chi', 'tsu', 'na', 'ni', 'ha', 'hi', 'fu', 'ma', 'mi', 'ya', 'yu',
    'ra', 'ri', 'wa', 'wo', 'n',
];

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
        selectedRows: [],      // gewählte Gojuon-Reihen (leer = alle Basis-Reihen)
        backUrl: opts.backUrl || null,         // Vollbild: Zurück-Link; Startseite: null
        registerUrl: opts.registerUrl || null, // Konto-CTA (optional, vom Template gesetzt)
        initialTab: opts.initialTab === 'daily' ? 'daily' : 'storm',
        mode: 'storm',         // 'storm' | 'daily' — Modus der laufenden Runde
        optionsOpen: false,    // "Optionen"-Disclosure (Dauer + Reihen) im Start-Screen
        // /practice/kana: Schrift + Reihen kommen vom geteilten $store.kanaScope
        // (interne Picker ausgeblendet). Sonst (Vollbild/Startseite/daily) false.
        scopeExternal: !!opts.scopeExternal,

        // ── Phasen / Daten ──
        // 'start' = Storm-Konfig (SSR-sichtbar) · 'daily' = Daily-Karte (Heim + Ergebnis)
        // 'loading' · 'playing' (mode storm|daily) · 'ended' (Storm-Ergebnis) · 'error'
        phase: opts.initialTab === 'daily' ? 'daily' : 'start',
        loadError: '',
        pool: [],              // [{ character, romanization, type, accepts:Set }]
        current: null,

        // ── Laufzeit ──
        score: 0,
        combo: 1,
        bestCombo: 1,
        count: 0,
        misses: 0,             // Fehlversuche der Runde (für serverseitige Genauigkeit)
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

        // ── Konto (eingeloggt): Server-Persistenz der Runde + XP ──
        // loggedIn kommt vom Template (current_user.is_authenticated). Nur dann
        // wird das Ergebnis ans Backend gepostet; Gäste bleiben rein lokal.
        loggedIn: !!opts.loggedIn,
        csrfToken: opts.csrfToken || '',
        serverBest: 0,         // serverseitige Bestmarke (Antwort von storm-finish)
        serverGames: 0,
        lastXp: 0,             // XP der zuletzt gespeicherten Runde

        // ── Daily (Wordle-artige Tageschallenge: festes Brett für ALLE gleich) ──
        dailyBoard: [],        // [{ character, romanization, accepts:Set }]
        dailyIdx: 0,
        dailyLog: [],          // bool[] — true = auf Anhieb richtig (🟩), false = vertippt (🟥)
        dailyGreens: 0,
        dailyStartMs: 0,
        dailyDate: '',
        dailyNumber: 0,
        dailyLoaded: false,    // Brett-Meta schon vom Server geladen?
        dailyLoading: false,
        dailyError: '',
        dailyHasResult: false, // heutiges Ergebnis vorhanden (schon gespielt)?
        dailyResult: null,     // { date, number, grid, timeStr, greens, bestCombo, len, shareText }
        dailyCopied: false,
        _dailyFetchedLocalDate: '', // lokaler Tag, an dem zuletzt geladen wurde (Rollover-Schutz)

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
            if (this.scopeExternal) {
                // Schrift + Reihen kommen vom geteilten Store (interne Picker
                // sind ausgeblendet); reaktiv mitziehen, Bestscore neu laden.
                const sc = this.$store && this.$store.kanaScope;
                if (sc) {
                    this.schrift = sc.schrift;
                    this.selectedRows = [...sc.rows];
                    this.$watch('$store.kanaScope.schrift', (v) => { this.schrift = v; this.loadBest(); });
                    this.$watch('$store.kanaScope.rows', (v) => { this.selectedRows = [...(v || [])]; this.loadBest(); });
                }
                // Dauer bleibt Storm-eigen.
                const d = parseInt(this._ls('kanaStormDur') || '', 10);
                if (d === 60 || d === 120) this.duration = d;
            } else {
                // Standalone (Vollbild/Startseite/daily): eigene Picker + Speicher.
                // Letzte Auswahl wiederherstellen (Privatmodus → Defaults bleiben).
                const s = this._ls('kanaStormSchrift');
                if (['hiragana', 'katakana', 'both'].includes(s)) this.schrift = s;
                const d = parseInt(this._ls('kanaStormDur') || '', 10);
                if (d === 60 || d === 120) this.duration = d;
                try {
                    const r = JSON.parse(this._ls('kanaStormRows') || '[]');
                    if (Array.isArray(r)) {
                        this.selectedRows = r.filter((k) => KANA_STORM_ROW_SIZES[k] !== undefined);
                    }
                } catch (e) { /* kaputter Wert → "Alle" behalten */ }
            }
            this.loadBest();
            // /daily landet mit aktivem Daily-Tab → Brett-Meta + ggf. Ergebnis laden.
            if (this.initialTab === 'daily') { this.phase = 'daily'; this.loadDailyMeta(); }
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

        // ── Reihen-Auswahl (leer = alle Basis-Reihen) ──
        allRowsActive() { return this.selectedRows.length === 0; },
        toggleRow(key) {
            if (this.phase === 'playing') return;
            this.selectedRows = this.selectedRows.includes(key)
                ? this.selectedRows.filter((k) => k !== key)
                : [...this.selectedRows, key];
            this._persistRows(); this.loadBest();
        },
        selectAllRows() {
            if (this.phase === 'playing') return;
            this.selectedRows = []; this._persistRows(); this.loadBest();
        },
        _persistRows() { this._lsSet('kanaStormRows', JSON.stringify(this.selectedRows)); },
        // Live-Anzahl der Auswahl (Reihen x Schrift) — ohne API-Call.
        selectedCount() {
            const base = this.selectedRows.length
                ? this.selectedRows.reduce((s, k) => s + (KANA_STORM_ROW_SIZES[k] || 0), 0)
                : KANA_STORM_BASE_COUNT;
            return this.schrift === 'both' ? base * 2 : base;
        },
        // Beschriftung des aktuellen Scopes (für die Bestscore-Zeile).
        scopeLabel() {
            let s = this.schriftLabel() + ' · ' + this.duration + ' Sek';
            const n = this.selectedRows.length;
            if (n) s += ' · ' + n + ' Reihe' + (n > 1 ? 'n' : '');
            return s;
        },

        // ── Bestscore (pro Schrift+Dauer UND Reihen-Auswahl — verschiedene
        //    Reihen-Teilmengen sind nicht vergleichbar; "Alle" behält den
        //    reihenlosen Key, damit bestehende Bestscores erhalten bleiben). ──
        _bestKey() {
            let k = 'kanaStormBest:' + this.schrift + ':' + this.duration;
            if (this.selectedRows.length) k += ':' + [...this.selectedRows].sort().join(',');
            return k;
        },
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
                // Gast-Endpoint (ohne Login): die gewählte Schrift, optional auf
                // einzelne Reihen eingegrenzt (rows). Eine explizite Reihen-Wahl
                // übersteuert serverseitig den Dakuten-Schalter (wer G wählt, übt
                // G) — die Anzahl ist die Pool-Größe, gespielt wird endlos per Zufall.
                const params = new URLSearchParams({ schrift: this.schrift, dakuten: 'false' });
                if (this.selectedRows.length) params.set('rows', this.selectedRows.join(','));
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
            this.mode = 'storm';
            this.score = 0; this.combo = 1; this.bestCombo = 1; this.count = 0; this.misses = 0;
            this.isNewBest = false; this.revealing = false; this.lastXp = 0;
            this.timeLeft = this.duration;
            this._endAt = Date.now() + this.duration * 1000;
            this.current = null; this.inputVal = '';
            this.fb = ''; this.fbText = ' ';
            this.phase = 'playing';
            this.nextKana();
            this._startTimer();
            if (window.kanaTrack) {
                window.kanaTrack('kana_storm_start', {
                    schrift: this.schrift, dur: this.duration,
                    rows: this.selectedRows.length || 'alle',
                });
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
            if (this.mode === 'daily') {
                // Daily: festes Brett, jedes Zeichen genau einmal, der Reihe nach.
                if (this.dailyIdx >= this.dailyBoard.length) { this.finishDaily(); return; }
                this.current = this.dailyBoard[this.dailyIdx];
            } else {
                this.current = this._pickFromPool();
            }
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
            // Auswahl zu klein für 4 distinkte Optionen (z.B. nur eine Reihe) →
            // mit gängigen Romaji auffüllen, damit immer 4 Knöpfe erscheinen.
            guard = 0;
            while (set.size < 4 && guard++ < 80) {
                set.add(KANA_STORM_FALLBACK_ROMAJI[Math.floor(Math.random() * KANA_STORM_FALLBACK_ROMAJI.length)]);
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
                // Daily: 🟩 protokollieren + ein Brett-Feld weiterrücken (keine Requeue).
                if (this.mode === 'daily') { this.dailyLog.push(true); this.dailyGreens++; this.dailyIdx++; }
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
                this.misses++;
                this.fb = 'bad';
                this.fbText = '✗ ' + this.current.character + ' = ' + this.current.romanization;
                // Daily: 🟥 protokollieren + weiterrücken (das Zeichen kommt NICHT zurück).
                if (this.mode === 'daily') { this.dailyLog.push(false); this.dailyIdx++; }
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
            // Eingeloggt: Runde serverseitig speichern (Bestmarke + XP).
            if (this.loggedIn) {
                this._postResult({
                    mode: 'storm', schrift: this.schrift, duration: this.duration,
                    score: this.score, best_combo: this.bestCombo,
                    correct: this.count, misses: this.misses, daily_date: '',
                });
            }
            if (window.kanaTrack) {
                window.kanaTrack('kana_storm_end', {
                    schrift: this.schrift, dur: this.duration,
                    score: this.score, combo: this.bestCombo, count: this.count,
                });
            }
        },

        // ── Server-Persistenz (nur eingeloggt): Runde speichern + XP/Bestmarke ──
        // Fire-and-forget: ein Fehler hier darf das Spiel NIE stören — die lokale
        // Anzeige (localStorage-Bestscore) bleibt ohnehin erhalten. Gäste rufen
        // das nie auf (loggedIn=false), der Endpoint ist zusätzlich @login_required.
        async _postResult(payload) {
            if (!this.loggedIn) return;
            try {
                const resp = await fetch('/api/practice/kana/storm-finish', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.csrfToken || '',
                    },
                    body: JSON.stringify(payload),
                });
                if (!resp.ok) return;
                const d = await resp.json();
                if (typeof d.best_score === 'number') this.serverBest = d.best_score;
                if (typeof d.games === 'number') this.serverGames = d.games;
                if (typeof d.xp_awarded === 'number') this.lastXp = d.xp_awarded;
            } catch (e) { /* offline / Session weg → bleibt rein clientseitig */ }
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

        // ── Tabs (Storm | Daily) ──────────────────────────────────────────
        // Tab-Leiste nur auf den "Ruhe"-Screens (nicht während Laden/Spiel).
        showTabs() { return ['start', 'ended', 'daily', 'error'].includes(this.phase); },
        tabActive(t) {
            const daily = this.phase === 'daily' || (this.phase === 'playing' && this.mode === 'daily');
            return t === (daily ? 'daily' : 'storm');
        },
        goTab(t) {
            if (this.phase === 'playing' || this.phase === 'loading') return;
            if (t === 'daily') { this.phase = 'daily'; this.loadDailyMeta(); }
            else { this.phase = 'start'; this.loadBest(); }
        },

        // ── "Optionen"-Disclosure (Dauer + Reihen) ────────────────────────
        toggleOptions() { this.optionsOpen = !this.optionsOpen; },
        optionsSummary() {
            // Bei externem Scope hat die Disclosure nur die Dauer (Reihen oben).
            if (this.scopeExternal) return this.duration + ' Sek';
            const n = this.selectedRows.length;
            const r = n ? (n + ' Reihe' + (n > 1 ? 'n' : '')) : 'alle Reihen';
            return this.duration + ' Sek · ' + r;
        },

        // Lokales Datum (YYYY-MM-DD) — Best-Effort-Schranke gegen ein gestriges
        // gespeichertes Ergebnis, falls der (autoritative) Server-Fetch scheitert.
        _todayIso() {
            try {
                const d = new Date();
                const p = (n) => String(n).padStart(2, '0');
                return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate());
            } catch (e) { return ''; }
        },

        // ── Daily: Brett-Meta laden (Karten-Kopfzeile + ggf. heutiges Ergebnis) ──
        async loadDailyMeta() {
            const todayLocal = this._todayIso();
            // Über Mitternacht offene Seite: lokaler Tageswechsel seit dem letzten
            // Laden → Brett (und day_number) neu holen, nicht das Vortagsbrett spielen.
            if (this.dailyLoaded && todayLocal && this._dailyFetchedLocalDate
                && todayLocal !== this._dailyFetchedLocalDate) {
                this.dailyLoaded = false;
            }
            // Gespeichertes Ergebnis nur übernehmen, wenn es zum heutigen Tag gehört
            // (verhindert „heute schon gespielt" mit gestrigem Grid — auch im Fehlerfall).
            this._restoreDailyResult(todayLocal);
            if (this.dailyLoaded) return;
            this.dailyLoading = true; this.dailyError = '';
            let data;
            try {
                const resp = await fetch('/api/practice/kana/storm-daily');
                data = await resp.json();
            } catch (e) {
                this.dailyLoading = false;
                this.dailyError = 'Das Tagesbrett konnte nicht geladen werden — bitte später erneut versuchen.';
                return;
            }
            const kana = ((data && data.kana) || []).filter((k) => (k.romanization || '').trim());
            this.dailyBoard = kana.map((k) => ({
                character: k.character,
                romanization: (k.romanization || '').toLowerCase(),
                accepts: buildAcceptSet(k),
            }));
            this.dailyDate = (data && data.date) || '';
            this.dailyNumber = (data && data.day_number) || 0;
            this.dailyLoading = false;
            this.dailyLoaded = true;
            this._dailyFetchedLocalDate = todayLocal;
            // Autoritatives Server-Datum: gespeichertes Ergebnis exakt dagegen prüfen.
            if (this.dailyResult && this.dailyResult.date !== this.dailyDate) {
                this.dailyHasResult = false; this.dailyResult = null;
            }
        },
        dailyBoardLen() { return this.dailyBoard.length || 10; },
        // Platzhalter- bzw. Ergebnis-Raster für die Daily-Karte.
        dailyGridDisplay() {
            if (this.dailyHasResult && this.dailyResult) return this.dailyResult.grid;
            return '⬜'.repeat(this.dailyBoardLen());
        },
        // validDate: nur ein Ergebnis dieses Tages übernehmen (leer = keine Schranke).
        _restoreDailyResult(validDate) {
            try {
                const raw = this._ls('kanaStormDailyLast');
                const r = raw ? JSON.parse(raw) : null;
                if (r && r.date && r.grid && (!validDate || r.date === validDate)) {
                    this.dailyResult = r; this.dailyHasResult = true;
                } else {
                    this.dailyResult = null; this.dailyHasResult = false;
                }
            } catch (e) { this.dailyResult = null; this.dailyHasResult = false; }
        },

        // ── Daily starten: festes Brett, KEIN Timer, jedes Zeichen genau 1× ──
        async startDaily() {
            if (!this.dailyLoaded) { await this.loadDailyMeta(); }
            if (!this.dailyBoard.length) {
                this.dailyError = 'Das Tagesbrett ist gerade nicht verfügbar — bitte später erneut versuchen.';
                return;
            }
            this.mode = 'daily';
            this.pool = this.dailyBoard;   // Distraktor-Quelle für die 4 Tap-Optionen
            this.dailyIdx = 0; this.dailyLog = []; this.dailyGreens = 0;
            this.score = 0; this.combo = 1; this.bestCombo = 1; this.count = 0; this.misses = 0;
            this.revealing = false; this.dailyStartMs = Date.now();
            this.current = null; this.inputVal = ''; this.fb = ''; this.fbText = ' ';
            this.phase = 'playing';
            this.nextKana();
            if (window.kanaTrack) window.kanaTrack('kana_storm_daily_start', { date: this.dailyDate });
        },

        finishDaily() {
            this._stopTimer();
            if (this._revealTimer) { clearTimeout(this._revealTimer); this._revealTimer = null; }
            this.revealing = false;
            const secs = Math.round((Date.now() - this.dailyStartMs) / 1000);
            const timeStr = Math.floor(secs / 60) + ':' + String(secs % 60).padStart(2, '0');
            const grid = this.dailyLog.map((g) => (g ? '🟩' : '🟥')).join('');
            const len = this.dailyBoard.length;
            const shareText = 'Kana Daily #' + this.dailyNumber + ' · ' + timeStr + ' ⚡\n'
                + grid + '\n'
                + 'Beste Combo ×' + this.bestCombo + ' · ' + this.dailyGreens + '/' + len + ' auf Anhieb\n'
                + 'japanese-learning.ch/daily';
            this.dailyResult = {
                date: this.dailyDate, number: this.dailyNumber, grid, timeStr,
                greens: this.dailyGreens, bestCombo: this.bestCombo, len, shareText,
            };
            this.dailyHasResult = true;
            this.dailyCopied = false;
            this._lsSet('kanaStormDailyLast', JSON.stringify(this.dailyResult));
            // Eingeloggt: Daily-Ergebnis serverseitig speichern (XP). correct =
            // 🟩 auf Anhieb richtig, misses = Rest des Bretts.
            if (this.loggedIn) {
                this._postResult({
                    mode: 'daily', schrift: this.schrift, duration: secs,
                    score: this.score, best_combo: this.bestCombo,
                    correct: this.dailyGreens,
                    misses: Math.max(0, len - this.dailyGreens),
                    daily_date: this.dailyDate,
                });
            }
            this.mode = 'storm';
            this.phase = 'daily';
            if (window.kanaTrack) {
                window.kanaTrack('kana_storm_daily_done', {
                    date: this.dailyDate, greens: this.dailyGreens, secs, combo: this.bestCombo,
                });
            }
        },

        async copyDaily() {
            const txt = (this.dailyResult && this.dailyResult.shareText) || '';
            if (!txt) return;
            let ok = false;
            try {
                if (navigator.clipboard && navigator.clipboard.writeText) {
                    await navigator.clipboard.writeText(txt); ok = true;
                }
            } catch (e) { ok = false; }
            if (!ok) {
                try {
                    const ta = document.createElement('textarea');
                    ta.value = txt; ta.style.position = 'fixed'; ta.style.opacity = '0';
                    document.body.appendChild(ta); ta.select();
                    document.execCommand('copy'); document.body.removeChild(ta); ok = true;
                } catch (e) { ok = false; }
            }
            if (ok) {
                this.dailyCopied = true;
                setTimeout(() => { this.dailyCopied = false; }, 1800);
                if (window.kanaTrack) window.kanaTrack('kana_storm_daily_copy', { date: this.dailyDate });
            }
        },

        // ── Einheitliche Leiste + rechtes HUD-Feld: Storm schrumpft / zählt Zeit,
        //    Daily füllt / zählt Brett-Fortschritt. ──
        barPct() {
            if (this.mode === 'daily') {
                const len = this.dailyBoard.length || 1;
                return Math.max(0, Math.min(100, (this.dailyIdx / len) * 100));
            }
            return this.timerPct();
        },
        rightStatLabel() { return this.mode === 'daily' ? 'Brett' : 'Zeit'; },
        rightStatValue() {
            if (this.mode === 'daily') {
                return Math.min(this.dailyIdx + 1, this.dailyBoard.length) + '/' + this.dailyBoard.length;
            }
            return this.liveTimeLabel();
        },
    };
}
