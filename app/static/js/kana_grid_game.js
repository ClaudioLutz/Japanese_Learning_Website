// Kana-Grid-Spiel — Drag-Drop-Komponente (Phase 1+2+3)
// Globaler Alpine-Component-Builder, geladen via base.html — verfuegbar in
// lesson_view.html (Lesson-Spiel) und practice_kana.html (zentrales Spiel).
function kanaGridGame(contentId) {
    return {
        contentId: contentId,
        loading: true,
        error: null,
        kana: [],
        rows: [],
        mode: 'schreiben',     // 'schreiben' | 'lesen' | 'blind'
        modeSwitch: true,
        cells: [],
        cellsByRow: {},
        pool: [],
        startTime: 0,
        cellTimes: {},
        totalErrors: 0,
        totalXp: 0,
        solvedCount: 0,
        totalCells: 0,
        completed: false,
        stars: 0,
        formattedTime: '0s',
        perfectStreak: 0,
        _sortables: [],
        _config: null,

        async init() {
            if (!this.contentId) {
                // Wird von practice_kana via initFromSession() gefuettert
                return;
            }
            try {
                const resp = await fetch(`/api/kana-grid/${this.contentId}/config`);
                if (!resp.ok) {
                    const j = await resp.json().catch(() => ({}));
                    this.error = j.error || 'Spiel konnte nicht geladen werden.';
                    this.loading = false;
                    return;
                }
                const data = await resp.json();
                this.kana = data.kana || [];
                this.rows = data.rows || [];
                this._config = data.config || {};
                this.mode = this._config.default_mode || 'schreiben';
                this.modeSwitch = !!this._config.allow_mode_switch;
                this.perfectStreak = parseInt(localStorage.getItem('kana_grid_perfect_streak') || '0', 10);
                this.buildCellsAndPool();
                this.loading = false;
                await this.$nextTick();
                this.initSortables();
                this.startTime = Date.now();
            } catch (e) {
                console.error('[KanaGrid] init error', e);
                this.error = 'Spiel konnte nicht geladen werden (Netzwerkfehler).';
                this.loading = false;
            }
        },

        buildCellsAndPool() {
            this.cells = [];
            this.cellsByRow = {};
            const kanaById = Object.fromEntries(this.kana.map(k => [k.id, k]));
            this.rows.forEach(row => {
                this.cellsByRow[row.key] = [];
                row.kana_ids.forEach(kid => {
                    const k = kanaById[kid];
                    if (!k) return;
                    const cell = {
                        id: `cell-${kid}`,
                        kanaId: kid,
                        character: k.character,
                        romanization: k.romanization,
                        hint: this.cellHint(k),
                        status: 'empty',
                        shake: false,
                        solved: '',
                        attempts: 0,
                        rated: false,
                    };
                    this.cells.push(cell);
                    this.cellsByRow[row.key].push(cell);
                });
            });
            this.totalCells = this.cells.length * (this.mode === 'blind' ? 2 : 1);
            this.solvedCount = 0;
            this.totalErrors = 0;
            this.totalXp = 0;
            this.completed = false;
            this.cellTimes = {};
            this.buildPool();
        },

        cellHint(k) {
            if (this.mode === 'schreiben') return k.romanization;
            if (this.mode === 'lesen')     return k.character;
            return '';
        },

        buildPool() {
            const cards = [];
            this.kana.forEach((k, idx) => {
                if (this.mode === 'schreiben') {
                    cards.push({ token: 't-hira-' + idx, kanaId: k.id, label: k.character, payload: k.character, kind: 'kana' });
                } else if (this.mode === 'lesen') {
                    cards.push({ token: 't-rom-' + idx, kanaId: k.id, label: k.romanization, payload: k.romanization, kind: 'romaji' });
                } else {
                    cards.push({ token: 't-hira-' + idx, kanaId: k.id, label: k.character, payload: k.character, kind: 'kana' });
                    cards.push({ token: 't-rom-' + idx, kanaId: k.id, label: k.romanization, payload: k.romanization, kind: 'romaji' });
                }
            });
            if (!this._config || this._config.shuffle_pool !== false) {
                for (let i = cards.length - 1; i > 0; i--) {
                    const j = Math.floor(Math.random() * (i + 1));
                    [cards[i], cards[j]] = [cards[j], cards[i]];
                }
            }
            this.pool = cards;
        },

        initSortables() {
            this._sortables.forEach(s => { try { s.destroy(); } catch(e) {} });
            this._sortables = [];

            const poolEl = this.$refs.pool;
            if (poolEl) {
                this._sortables.push(Sortable.create(poolEl, {
                    group: { name: 'kana', pull: 'clone', put: false },
                    sort: false,
                    animation: 150,
                    ghostClass: 'kana-grid-game__pool-card--ghost',
                }));
            }

            const cellEls = this.$el.querySelectorAll('.kana-grid-game__cell');
            cellEls.forEach(cellEl => {
                const cellId = cellEl.dataset.cellId;
                const cell = this.cells.find(c => c.id === cellId);
                if (!cell) return;
                this._sortables.push(Sortable.create(cellEl, {
                    group: { name: 'kana', pull: false, put: ['kana'] },
                    sort: false,
                    animation: 150,
                    onAdd: (evt) => {
                        const dragged = evt.item;
                        const payload = dragged.dataset.payload || '';
                        const kanaId = parseInt(dragged.dataset.kanaId, 10);
                        const token = dragged.dataset.token;
                        dragged.parentNode && dragged.parentNode.removeChild(dragged);
                        this.handleDrop(cell, kanaId, payload, token);
                    },
                }));
            });
        },

        handleDrop(cell, kanaId, payload, token) {
            const expected = this.expectedForCell(cell);
            const isCorrect = (expected === payload) && (cell.kanaId === kanaId);

            if (!isCorrect) {
                cell.attempts += 1;
                this.totalErrors += 1;
                cell.shake = true;
                setTimeout(() => { cell.shake = false; }, 500);
                return;
            }

            if (cell.status === 'correct' && this.mode !== 'blind') return;

            if (this.mode === 'blind') {
                cell._blindFilled = cell._blindFilled || { kana: false, romaji: false };
                const isKana = /[぀-ヿ]/.test(payload);
                cell._blindFilled[isKana ? 'kana' : 'romaji'] = true;
                cell.solved = (cell._blindFilled.kana ? cell.character : '') +
                              ' / ' + (cell._blindFilled.romaji ? cell.romanization : '?');
                this.solvedCount += 1;
                if (cell._blindFilled.kana && cell._blindFilled.romaji) {
                    cell.status = 'correct';
                    if (!cell.rated) {
                        cell.rated = true;
                        this.rateCell(cell);
                    }
                }
            } else {
                cell.status = 'correct';
                cell.solved = payload;
                this.solvedCount += 1;
                if (!cell.rated) {
                    cell.rated = true;
                    this.rateCell(cell);
                }
            }

            this.pool = this.pool.filter(c => c.token !== token);
            this.playKanaAudio(cell);

            if (this.solvedCount >= this.totalCells) {
                this.onComplete();
            }
        },

        expectedForCell(cell) {
            if (this.mode === 'schreiben') return cell.character;
            if (this.mode === 'lesen')     return cell.romanization;
            return cell.character;
        },

        playKanaAudio(cell) {
            if (typeof playCardAudio === 'function') {
                playCardAudio(cell.character, null, 'ja');
                return;
            }
            try {
                fetch('/api/tts', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text: cell.character, lang: 'ja', model: 'chirp' }),
                }).then(r => r.json()).then(data => {
                    if (data && data.audio) {
                        const audio = new Audio('data:audio/mpeg;base64,' + data.audio);
                        audio.play();
                    }
                }).catch(() => {});
            } catch (e) {}
        },

        async rateCell(cell) {
            const elapsed = (Date.now() - (this.cellTimes[cell.id] || this.startTime));
            const errs = cell.attempts;
            let rating;
            if (errs === 0 && elapsed < 3000) rating = 4;
            else if (errs === 0)              rating = 3;
            else if (errs === 1)              rating = 2;
            else                              rating = 1;

            const lcId = this._findLessonContentIdForKana(cell.kanaId);
            if (!lcId) return;

            const isFinal = (this.solvedCount + 1) >= this.totalCells;
            const gridContext = isFinal ? {
                perfect_kana_grid: this.totalErrors === 0,
                perfect_kana_grid_streak: this.totalErrors === 0
                    ? (this.perfectStreak + 1)
                    : 0,
            } : {};

            try {
                const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
                const resp = await fetch('/api/srs/rate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken || '',
                    },
                    body: JSON.stringify({
                        content_id: lcId,
                        rating: rating,
                        time_taken_ms: elapsed,
                        grid_context: gridContext,
                    }),
                });
                if (resp.ok) {
                    const data = await resp.json();
                    if (data.xp_earned) {
                        this.totalXp += data.xp_earned;
                        const cellEl = this.$el.querySelector(`[data-cell-id="${cell.id}"]`);
                        if (cellEl && typeof showXpAnimation === 'function') {
                            showXpAnimation(cellEl, data.xp_earned);
                        }
                        if (data.total_xp && typeof updateNavbarXp === 'function') {
                            updateNavbarXp(data.total_xp, data.current_streak);
                        }
                    }
                }
            } catch (e) {
                console.warn('[KanaGrid] rate error', e);
            }
        },

        _findLessonContentIdForKana(kanaId) {
            const k = this.kana.find(x => x.id === kanaId);
            return k && k.lesson_content_id ? k.lesson_content_id : null;
        },

        setMode(newMode) {
            if (!this.modeSwitch || this.mode === newMode) return;
            this.mode = newMode;
            this.cells.forEach(c => {
                c.status = 'empty';
                c.solved = '';
                c.attempts = 0;
                c.rated = false;
                c.shake = false;
                c.hint = this.cellHint(this.kana.find(k => k.id === c.kanaId) || {});
                if (c._blindFilled) delete c._blindFilled;
            });
            this.totalCells = this.cells.length * (this.mode === 'blind' ? 2 : 1);
            this.solvedCount = 0;
            this.totalErrors = 0;
            this.totalXp = 0;
            this.completed = false;
            this.startTime = Date.now();
            this.buildPool();
            this.$nextTick(() => this.initSortables());
        },

        onComplete() {
            this.completed = true;
            const elapsed = (Date.now() - this.startTime) / 1000;
            this.formattedTime = elapsed < 60 ? `${elapsed.toFixed(0)}s`
                                              : `${Math.floor(elapsed/60)}m ${(elapsed%60).toFixed(0)}s`;
            if (this.totalErrors === 0 && elapsed < 90)      this.stars = 3;
            else if (this.totalErrors <= 3 || elapsed < 180) this.stars = 2;
            else                                              this.stars = 1;

            const wasPerfect = (this.totalErrors === 0);
            if (wasPerfect) {
                this.perfectStreak += 1;
                localStorage.setItem('kana_grid_perfect_streak', this.perfectStreak);
            } else {
                this.perfectStreak = 0;
                localStorage.setItem('kana_grid_perfect_streak', '0');
            }

            if (this.stars === 3 && window.confetti) {
                window.confetti({ particleCount: 120, spread: 70, origin: { y: 0.6 } });
            }
        },

        async restart() {
            this.completed = false;
            this.stars = 0;
            this.totalXp = 0;
            this.totalErrors = 0;
            this.solvedCount = 0;
            this.cells.forEach(c => {
                c.status = 'empty';
                c.solved = '';
                c.attempts = 0;
                c.rated = false;
                if (c._blindFilled) delete c._blindFilled;
            });
            this.buildPool();
            this.startTime = Date.now();
            await this.$nextTick();
            this.initSortables();
        },
    };
}

// Expose global fuer Alpine
window.kanaGridGame = kanaGridGame;


// ============================================================
// Practice-Page-Komponenten (verwendet kanaGridGame oben)
// ============================================================
const PRACTICE_ROW_LABELS = {
    vowels: 'a/i/u', k: 'K', s: 'S', t: 'T', n: 'N', h: 'H',
    m: 'M', y: 'Y', r: 'R', w: 'W', n_kons: 'ん',
    g: 'G', z: 'Z', d: 'D', b: 'B', p: 'P',
};

function practiceKana() {
    return {
        mode: 'schreiben',
        schrift: 'both',
        selectedRows: [],
        includeDakuten: true,
        weakOnly: false,
        limit: 20,
        sessionKana: [],
        sessionKey: 0,
        loading: false,
        error: null,
        dailyAvailable: true,
        dailyBonusXp: 25,
        availableRows: Object.keys(PRACTICE_ROW_LABELS).map(k => ({ key: k, label: PRACTICE_ROW_LABELS[k] })),

        async init() {
            this.load();
        },

        toggleRow(key) {
            if (this.selectedRows.includes(key)) {
                this.selectedRows = this.selectedRows.filter(k => k !== key);
            } else {
                this.selectedRows.push(key);
            }
            this.load();
        },

        async load() {
            this.loading = true;
            this.error = null;
            try {
                const params = new URLSearchParams({
                    mode: this.mode,
                    schrift: this.schrift,
                    dakuten: this.includeDakuten ? 'true' : 'false',
                    weak_only: this.weakOnly ? 'true' : 'false',
                    limit: String(this.limit),
                });
                if (this.selectedRows.length > 0) {
                    params.set('rows', this.selectedRows.join(','));
                }
                const resp = await fetch('/api/practice/kana/session?' + params.toString());
                const data = await resp.json();
                if (data.message) this.error = data.message;
                this.sessionKana = data.kana || [];
                this.sessionKey += 1;
            } catch (e) {
                this.error = 'Session konnte nicht geladen werden.';
            } finally {
                this.loading = false;
            }
        },

        async loadDailyChallenge() {
            this.loading = true;
            this.error = null;
            try {
                const resp = await fetch('/api/practice/kana/daily-challenge');
                const data = await resp.json();
                if (data.message) this.error = data.message;
                this.sessionKana = data.kana || [];
                this.dailyBonusXp = data.bonus_xp || 25;
                this.sessionKey += 1;
            } catch (e) {
                this.error = 'Daily Challenge konnte nicht geladen werden.';
            } finally {
                this.loading = false;
            }
        },

        loadWeakOnly() {
            this.weakOnly = true;
            this.limit = 10;
            this.load();
        },

        reload() {
            this.load();
        },
    };
}

function practiceGameWrapper(sessionKana, mode) {
    return Object.assign(kanaGridGame(null), {
        sessionKana,
        modeOverride: mode,

        async initFromSession() {
            this.kana = this.sessionKana.map(k => ({
                id: k.kana_id,
                character: k.character,
                romanization: k.romanization,
                type: k.type,
                audio_url: null,
                lesson_content_id: k.lesson_content_id,
            }));
            const ROW_ORDER = ['vowels','k','s','t','n','h','m','y','r','w','n_kons','g','z','d','b','p'];
            const byRow = {};
            this.sessionKana.forEach(k => {
                const key = k.row || 'other';
                if (!byRow[key]) byRow[key] = [];
                byRow[key].push(k.kana_id);
            });
            this.rows = ROW_ORDER.filter(k => byRow[k])
                .map(k => ({ key: k, label: PRACTICE_ROW_LABELS[k] || k, kana_ids: byRow[k] }));
            this._config = {
                default_mode: this.modeOverride,
                allow_mode_switch: false,
                grid_layout: 'rows',
                shuffle_pool: true,
                timer_enabled: false,
            };
            this.mode = this.modeOverride;
            this.modeSwitch = false;
            this.perfectStreak = parseInt(localStorage.getItem('kana_grid_perfect_streak') || '0', 10);
            this.buildCellsAndPool();
            this.loading = false;
            await this.$nextTick();
            this.initSortables();
            this.startTime = Date.now();
        },
    });
}

window.practiceKana = practiceKana;
window.practiceGameWrapper = practiceGameWrapper;
