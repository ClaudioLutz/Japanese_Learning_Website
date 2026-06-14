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
        wasPerfect: false,          // H-3: keine Fehler UND keine Hints — Basis fuer Daily-Bonus-Anzeige
        _sortables: [],
        _config: null,
        _ttsDisabled: false,        // true, sobald Server-TTS in dieser Session fehlschlug
        selectedCardToken: null,    // Tap-to-Place: aktuell ausgewaehlte Pool-Karte
        bothScripts: false,         // true, wenn Session Hiragana UND Katakana enthaelt
        ariaFeedback: '',           // H-1: DE-Ansage fuer Screenreader (aria-live-Region)
        _hintTimer: null,           // H-2: Handle des Hint-setTimeout (zum Clearen bei restart/setMode)
        // ── Phase 4: Forschungsbasierte Hilfen (Bjork, Pre-Testing-Gate, Fading) ──
        maxHints: 0,            // 0 = keine Hilfen verfuegbar (ab Lesson 4+)
        hintsRemaining: 0,
        hintsUsed: 0,
        cellsHinted: [],        // IDs der Zellen, die per Hint geloest wurden (Rating=Hard)
        showRomajiHint: false,  // Pool-Karten zeigen Romaji-Subscript (nur Lesson 1)
        // ── #2/#3: Verwechslungs-Signal + Diskriminations-Hinweis ──
        sessionConfusions: [],  // gesammelte Fehl-Drops {target_kana_id, confused_kana_id}
        activeHint: null,       // {char, text} — Spot-the-difference-Hinweis nach Fehler
        _confusionFlushInstalled: false,
        // ── #3 Timer-Gate: Timer startet erst beim ERSTEN echten Spielzug ──
        // (erster Drop/Tap, der eine Kachel platziert), nicht schon beim Laden.
        // So misst die Sterne-Formel die echte Loesungszeit; HUD-Timer bleibt
        // bis dahin 0:00. Idempotent ueber dieses Flag (nur der allererste Move zaehlt).
        hasStarted: false,
        // ── Mobile: Haeppchen-Runden ──────────────────────────────────────────
        // Auf schmalen Schirmen passen 46 Felder + 46 Kacheln nicht gleichzeitig
        // drauf, und der Pool laesst sich wegen Sortable (touch-action:none) nicht
        // scrollen. Daher spielt Mobile in Batches von ~6 Kana: pro Runde nur die
        // Reihen + Kacheln EINES Batches; ist er geloest, schaltet das Spiel zur
        // naechsten Reihe weiter. Desktop = EIN Batch = alle Reihen (unveraendert).
        batchMode: false,
        batches: [],
        currentBatch: 0,
        // ── Variante 1 (echte Gojuon-Tabelle) + Per-Kana-Statistik ──────────────
        // keepGojuonOrder: Ziel-Slots IMMER in Gojuon-Reihenfolge halten (Spalten
        // a-i-u-e-o bleiben stabil) — der Zufall kommt aus dem gemischten Karten-
        // Tray (buildPool), nicht aus den Slots. Nur die Practice-Seite
        // (kanaGameView) setzt das; Lektions-Grids behalten ihr Frische-/Shuffle-
        // Verhalten unveraendert.
        keepGojuonOrder: false,
        statStrong: [],         // [{kanaId,character,romanization,attempts}] auf Anhieb richtig
        statWeak: [],           // [{...}] mit Fehlversuchen, meiste zuerst
        weakKanaIds: null,      // Set der Kana-IDs mit Fehlversuchen (fuer "nur Schwaechste")
        weakMode: false,        // laeuft gerade eine reine Schwaechsten-Runde?
        _fullRows: null,        // unveraenderte Reihen (zum Zurueckfiltern auf die Schwaechsten)

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
                this.maxHints = this._config.max_hints || 0;
                this.hintsRemaining = this.maxHints;
                this.hintsUsed = 0;
                this.cellsHinted = [];
                this.showRomajiHint = !!this._config.show_romaji_hint_on_pool;
                this.perfectStreak = parseInt(localStorage.getItem('kana_grid_perfect_streak') || '0', 10);
                this.buildCellsAndPool();
                this.loading = false;
                await this.$nextTick();
                this.initSortables();
                // #3 Timer-Gate: startTime hier nur als Fallback fuer rateCell()
                // setzen; die echte Uhr startet _markStarted() beim ersten Spielzug.
                this.startTime = Date.now();
                this.hasStarted = false;
                this._installConfusionFlush();
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
                        scriptType: k.type || null,   // 'hiragana' | 'katakana' — fuer Schrift-Badge
                        vowel: this._vowelOf(k.romanization),  // a/i/u/e/o ('' bei ん) — Spalten-Ausrichtung
                        hint: this.cellHint(k),
                        strokeInfo: k.stroke_order_info || '',  // Spot-the-difference-Hinweis (#3)
                        mnemonic: k.mnemonic || '',             // Eselsbruecke fuers Fehler-Feedback
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
            // Erste Runde einer frischen Session (erstes Mal bzw. nach >1 Std. Pause)
            // bleibt in Gojuon-Reihenfolge zur Orientierung; sonst innerhalb jeder
            // Gruppe mischen. Reihenfolge: Frische-Check VOR dem Zeitstempel-Update.
            if (this.keepGojuonOrder) {
                // Variante 1: die Ziel-Tabelle bleibt IMMER kanonisch geordnet
                // (a-i-u-e-o pro Reihe) — sie soll das Gojuon-Layout staerken,
                // nicht so tun als waere sie geordnet und dann doch mischen.
                this._sortGroupsGojuon();
                // Reihen-Label = erstes Kana der Reihe (あ・か・さ …) — durchgehend
                // konsistent statt gemischter A/I/U-/K-Schemata (Cluster behalten
                // ihr Server-Label).
                if (!this.isConfusion) this._relabelRowsByFirstKana();
            } else if (this._isFreshSession()) {
                this._sortGroupsGojuon();   // Orientierung: erste Runde in Gojuon-Reihenfolge
            } else {
                this._shuffleGroups();
            }
            this._touchPlayTimestamp();
            // Enthaelt die Session beide Schriften? Dann brauchen die Felder im
            // Schreib-Modus ein Hira/Kata-Kennzeichen (sonst sind z.B. zwei "a"-Felder
            // optisch nicht unterscheidbar).
            this.bothScripts = new Set(
                (this.kana || []).map(k => k.type).filter(Boolean)
            ).size > 1;
            this.totalCells = this.cells.length * (this.mode === 'blind' ? 2 : 1);
            this.solvedCount = 0;
            this.totalErrors = 0;
            this.totalXp = 0;
            this.completed = false;
            this.cellTimes = {};
            this.buildPool();
            this._buildBatches();
        },

        // Mischt die Reihenfolge der Felder INNERHALB jeder Reihe/Gruppe (a/i/u, K, …)
        // neu durch — Felder bleiben in ihrer Gruppe, wandern nicht zwischen Gruppen.
        // So lassen sich keine Positionen auswendig lernen; jeder Hinweis muss gelesen
        // werden. Neuzuweisung von cellsByRow haelt Alpine's x-for reaktiv.
        _shuffleGroups() {
            const shuffled = {};
            Object.keys(this.cellsByRow).forEach(key => {
                const arr = this.cellsByRow[key].slice();
                for (let i = arr.length - 1; i > 0; i--) {
                    const j = Math.floor(Math.random() * (i + 1));
                    [arr[i], arr[j]] = [arr[j], arr[i]];
                }
                shuffled[key] = arr;
            });
            this.cellsByRow = shuffled;
        },

        // Sortiert die Felder jeder Reihe in Gojuon-Reihenfolge: pro Schrift nach
        // Vokal (a,i,u,e,o), Hiragana vor Katakana. Fuer die geordnete erste Runde —
        // die Uebungs-Session selbst kommt in SRS-Reihenfolge, daher explizit sortieren.
        _sortGroupsGojuon() {
            const VOWEL = { a: 0, i: 1, u: 2, e: 3, o: 4 };
            const sortKey = (cell) => {
                const rom = (cell.romanization || '').toLowerCase();
                let v = 5;  // ohne Vokal (z.B. "n"/ん) ans Ende
                for (let i = rom.length - 1; i >= 0; i--) {
                    if (VOWEL[rom[i]] !== undefined) { v = VOWEL[rom[i]]; break; }
                }
                const script = cell.scriptType === 'katakana' ? 1 : 0;  // Hiragana zuerst
                return script * 10 + v;
            };
            const sorted = {};
            Object.keys(this.cellsByRow).forEach(key => {
                sorted[key] = this.cellsByRow[key].slice().sort((a, b) => sortKey(a) - sortKey(b));
            });
            this.cellsByRow = sorted;
        },

        // Vokal eines Romaji (letzter Vokal) — fuer die Spalten-Ausrichtung der
        // echten Gojuon-Tabelle. '' bei vokallosen Kana (ん) → keine feste Spalte.
        _vowelOf(rom) {
            const r = (rom || '').toLowerCase();
            for (let i = r.length - 1; i >= 0; i--) {
                if (r[i] === 'a' || r[i] === 'i' || r[i] === 'u' || r[i] === 'e' || r[i] === 'o') return r[i];
            }
            return '';
        },

        // Reihen-Label = erstes Kana der (Gojuon-sortierten) Reihe: あ・か・さ …
        // Konsistent ueber alle Reihen und trainiert nebenbei das Lesen.
        _relabelRowsByFirstKana() {
            (this.rows || []).forEach(row => {
                const cells = this.cellsByRow[row.key] || [];
                if (cells.length && cells[0].character) row.label = cells[0].character;
            });
        },

        // Frische Session = erstes Mal ueberhaupt oder >1 Std. seit der letzten Runde.
        // Dann bleibt die erste Runde geordnet (Orientierung); sonst wird gemischt.
        // localStorage → gilt pro Geraet/Browser.
        _isFreshSession() {
            try {
                const last = parseInt(localStorage.getItem('kana_grid_last_play_ts') || '0', 10);
                return !last || (Date.now() - last) > 3600000;  // 1 Std.
            } catch (e) {
                return true;
            }
        },
        _touchPlayTimestamp() {
            try {
                localStorage.setItem('kana_grid_last_play_ts', String(Date.now()));
            } catch (e) { /* localStorage nicht verfuegbar — dann immer "frisch" */ }
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
                    cards.push({ token: 't-hira-' + idx, kanaId: k.id, label: k.character, payload: k.character, kind: 'kana', romaji: k.romanization });
                } else if (this.mode === 'lesen') {
                    cards.push({ token: 't-rom-' + idx, kanaId: k.id, label: k.romanization, payload: k.romanization, kind: 'romaji', romaji: k.romanization });
                } else {
                    cards.push({ token: 't-hira-' + idx, kanaId: k.id, label: k.character, payload: k.character, kind: 'kana', romaji: k.romanization });
                    cards.push({ token: 't-rom-' + idx, kanaId: k.id, label: k.romanization, payload: k.romanization, kind: 'romaji', romaji: k.romanization });
                }
            });
            if (!this._config || this._config.shuffle_pool !== false) {
                for (let i = cards.length - 1; i > 0; i--) {
                    const j = Math.floor(Math.random() * (i + 1));
                    [cards[i], cards[j]] = [cards[j], cards[i]];
                }
            }
            this.pool = cards;
            this.selectedCardToken = null;
        },

        // ── Haeppchen-Runden (Mobile) ────────────────────────────────────────
        // Teilt die Reihen in Batches von ~6 Kana. Wird bei jedem (Neu-)Aufbau
        // aufgerufen und detektiert dabei frisch, ob ein schmaler Schirm vorliegt
        // (z.B. nach Drehen). Desktop: ein einziger Batch ueber alle Reihen.
        _buildBatches() {
            this.batchMode = false;
            try { this.batchMode = window.matchMedia('(max-width: 640px)').matches; } catch (e) {}
            // 5 => i.d.R. eine Gojuon-Reihe pro Runde (kleine Reihen ya/wa/n werden
            // zusammengelegt). Haelt auch im Blind-Modus (2 Kacheln/Kana) den Pool
            // klein genug, dass nichts scrollen muss. Desktop: Infinity = ein Batch.
            const TARGET = this.batchMode ? 5 : Infinity;
            const batches = [];
            let cur = null;
            (this.rows || []).forEach(row => {
                const cellsOfRow = (this.cellsByRow && this.cellsByRow[row.key]) || [];
                if (!cellsOfRow.length) return;
                if (!cur) cur = { rowKeys: [], kanaIds: new Set() };
                cur.rowKeys.push(row.key);
                cellsOfRow.forEach(c => cur.kanaIds.add(c.kanaId));
                if (cur.kanaIds.size >= TARGET) { batches.push(cur); cur = null; }
            });
            if (cur) batches.push(cur);
            if (!batches.length) {
                batches.push({
                    rowKeys: (this.rows || []).map(r => r.key),
                    kanaIds: new Set((this.cells || []).map(c => c.kanaId)),
                });
            }
            this.batches = batches;
            this.currentBatch = 0;
        },
        // Aktuell sichtbare Reihen / Pool-Kacheln = nur der laufende Batch.
        // Desktop (batchMode=false): alle Reihen / der ganze Pool — wie bisher.
        visibleRows() {
            const b = this.batches[this.currentBatch];
            if (!b || !this.batchMode) return this.rows;
            return this.rows.filter(r => b.rowKeys.indexOf(r.key) !== -1);
        },
        visiblePool() {
            const b = this.batches[this.currentBatch];
            if (!b || !this.batchMode) return this.pool;
            return this.pool.filter(c => b.kanaIds.has(c.kanaId));
        },
        batchLabel() {
            if (!this.batchMode || this.batches.length <= 1) return '';
            return 'Reihe ' + (this.currentBatch + 1) + '/' + this.batches.length;
        },
        // Nach jedem geloesten Feld aufrufen: ist der aktuelle Batch fertig, zur
        // naechsten Reihe weiterschalten — oder, beim letzten Batch, abschliessen.
        // Desktop/Einzel-Batch: exakt das alte Verhalten (Ende bei allen geloest).
        _advanceOrComplete() {
            if (!this.batchMode || this.batches.length <= 1) {
                if (this.solvedCount >= this.totalCells) this.onComplete();
                return;
            }
            const b = this.batches[this.currentBatch];
            const batchDone = !b || this.cells
                .filter(c => b.kanaIds.has(c.kanaId))
                .every(c => c.status === 'correct');
            if (!batchDone) return;
            if (this.currentBatch >= this.batches.length - 1) {
                this.onComplete();
                return;
            }
            this.currentBatch += 1;
            this.selectedCardToken = null;
            this.announce('Reihe geschafft! Weiter mit Reihe ' +
                (this.currentBatch + 1) + ' von ' + this.batches.length + '.');
            // Neue Pool-/Zell-Knoten → Sortable neu binden.
            this.$nextTick(() => this.initSortables());
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
                    // ── Touch-Support (SortableJS-Fallback statt nativer HTML5-DnD) ──
                    // Native DnD feuert auf Touch nicht zuverlaessig; der Fallback nutzt
                    // Pointer/Touch-Events und folgt dem Finger.
                    forceFallback: true,
                    fallbackOnBody: true,
                    fallbackTolerance: 4,        // erst ab 4px Bewegung startet ein Drag
                    // Kurzer Halte-Delay NUR auf Touch: trennt Drag von Scrollen/Tap,
                    // ohne die Maus-Bedienung am Desktop zu verzoegern.
                    delay: 80,
                    delayOnTouchOnly: true,
                    touchStartThreshold: 4,
                    // Auto-Scroll, damit man auch zu Zellen ausserhalb des Sichtfelds ziehen kann.
                    scroll: true,
                    bubbleScroll: true,
                    scrollSensitivity: 60,
                    scrollSpeed: 12,
                    // Ein Drag macht eine evtl. Tap-Auswahl gegenstandslos.
                    onChoose: () => { this.selectedCardToken = null; },
                    // ── Alpine/Sortable-Konflikt (P4) ──
                    // SortableJS klont DOM-Knoten (pull:'clone' + Fallback-Ghost). Diese
                    // Klone tragen die x-for-Bindings (card.*), haben aber keinen Alpine-Scope
                    // → "card is not defined". x-ignore weist Alpine an, sie zu ueberspringen.
                    onClone: (evt) => {
                        if (evt && evt.clone) evt.clone.setAttribute('x-ignore', '');
                    },
                    onStart: () => {
                        document.querySelectorAll('.sortable-fallback')
                            .forEach(el => el.setAttribute('x-ignore', ''));
                    },
                    // pull:'clone' laesst eine Kopie in der Quelle zurueck. Den Pool-Bestand
                    // verwaltet aber Alpine (this.pool); diese verwaiste DOM-Kopie daher
                    // nach dem Drag entfernen, sonst bleibt eine tote Karte sichtbar.
                    onEnd: (evt) => {
                        if (evt && evt.clone && evt.clone.parentNode) {
                            evt.clone.parentNode.removeChild(evt.clone);
                        }
                    },
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

        // H-1: kurze DE-Ansage in die aria-live-Region setzen. Wird derselbe Text
        // zweimal hintereinander gesetzt (z.B. zweimal "Falsch, nochmal"), liest ein
        // Screenreader ihn sonst nicht erneut vor — daher kurz leeren und neu setzen.
        announce(msg) {
            if (this.ariaFeedback === msg) {
                this.ariaFeedback = '';
                this.$nextTick(() => { this.ariaFeedback = msg; });
            } else {
                this.ariaFeedback = msg;
            }
        },

        // #3 Timer-Gate: Der allererste echte Spielzug (egal ob korrekt oder falsch)
        // startet die Uhr. Idempotent ueber hasStarted — spaetere Zuege sind No-Ops.
        // Setzt startTime neu (verwirft Idle-Zeit seit dem Laden) und wirft, falls
        // vorhanden (Spiel-Seite), den Live-Timer an. Gilt fuer Embed UND Vollbild.
        _markStarted() {
            if (this.hasStarted) return;
            this.hasStarted = true;
            this.startTime = Date.now();
            // Analytics: erster echter Spielzug = Spielstart (Funnel-Eintritt).
            kanaTrack('kana_start', { mode: this.mode, guest: !window.currentUser });
            // Spiel-Seite (kanaGameView) liefert startLiveTimer(); Lesson-Spiel nicht.
            if (typeof this.startLiveTimer === 'function') this.startLiveTimer();
            // #6 Heartbeat: dem Host signalisieren, dass wirklich gespielt wird —
            // er disarmt/resettet dann seinen Safety-Timer. Nur im Embed-Pfad.
            if (window.kgameEmbed) {
                try {
                    window.parent.postMessage(
                        { type: 'kana-embed-active' }, window.location.origin
                    );
                } catch (e) { /* Eltern-Seite evtl. nicht erreichbar */ }
            }
        },

        handleDrop(cell, kanaId, payload, token) {
            // #3 Timer-Gate: erster echter Spielzug startet die Uhr (idempotent).
            this._markStarted();
            // Korrektheit rein INHALTSBASIERT pruefen — nicht ueber die unsichtbare
            // kanaId. Bei schrift='both' gibt es z.B. zwei "a"-Felder (あ + ア) bzw.
            // im Lese-Modus zwei optisch identische "a"-Romaji-Karten. Eine kanaId-
            // Bindung liesse die gleich aussehenden Karten/Felder NICHT austauschbar
            // wirken ("mit der einen klappt's, mit der anderen nicht").
            let isCorrect;
            if (this.mode === 'lesen') {
                // Feld zeigt das Zeichen, erwartet die Lesung: jede passende Romaji-Karte zaehlt.
                isCorrect = (payload === cell.romanization);
            } else if (this.mode === 'blind') {
                // Blind unveraendert: exakte Kana-Zuordnung verlangt.
                isCorrect = (this.expectedForCell(cell) === payload) && (cell.kanaId === kanaId);
            } else {
                // Schreiben: Feld zeigt die Lesung, erwartet das Zeichen (Zeichen sind eindeutig).
                isCorrect = (payload === cell.character);
            }

            if (!isCorrect) {
                cell.attempts += 1;
                this.totalErrors += 1;
                cell.shake = true;
                setTimeout(() => { cell.shake = false; }, 500);
                // #2: welches FALSCHE Kana wurde abgelegt? — Signal fuer den Drill.
                if (kanaId && cell.kanaId && kanaId !== cell.kanaId) {
                    this.sessionConfusions.push({
                        target_kana_id: cell.kanaId,
                        confused_kana_id: kanaId,
                    });
                }
                // Korrektives Feedback, gestuft — erst Raum fuer eigenen Recall, dann
                // lernt der Nutzer die Antwort, statt endlos zu raten:
                //   1. Fehler   -> Spot-the-difference / Eselsbruecke (falls vorhanden)
                //   ab 2. Fehler -> richtige Lesung explizit nennen + Laut abspielen
                const hintText = cell.strokeInfo || cell.mnemonic || '';
                if (cell.attempts >= 2) {
                    this.activeHint = {
                        char: cell.character,
                        text: `Richtig: ${cell.character} = „${cell.romanization}“`
                              + (hintText ? ' · ' + hintText : ''),
                    };
                    this.playKanaAudio(cell);   // den Laut hoeren staerkt die Verknuepfung
                    this.announce(`Das richtige Zeichen ist ${cell.character}, gesprochen ${cell.romanization}`);
                } else if (hintText) {
                    this.activeHint = { char: cell.character, text: hintText };
                    this.announce('Noch nicht — schau genau hin und versuch es nochmal');
                } else {
                    this.announce('Noch nicht — versuch es nochmal');
                }
                return;
            }

            if (cell.status === 'correct' && this.mode !== 'blind') return;
            this.activeHint = null;

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
            // H-1: Richtig-Ansage mit Zeichen + Lesung (z.B. "Richtig: あ a").
            this.announce(`Richtig: ${cell.character} ${cell.romanization}`);

            // Mobile: ggf. zur naechsten Reihe; sonst Abschluss bei allen geloest.
            this._advanceOrComplete();
        },

        // ── Tap-to-Place (Single-Pointer-Alternative zu Drag, WCAG 2.2 SC 2.5.7) ──
        // Erst eine Pool-Karte antippen (auswaehlen), dann ein Feld antippen (platzieren).
        // Die Auswahl bleibt ueber Scrollen erhalten — Karte und Zielzelle muessen NICHT
        // gleichzeitig sichtbar sein. Funktioniert mit Maus, Touch und Tastatur.
        tapCard(card) {
            if (this.completed || !card) return;
            this.selectedCardToken = (this.selectedCardToken === card.token) ? null : card.token;
        },

        // Klick/Tap auf eine Zelle. Prioritaet:
        //   1. Ist eine Karte ausgewaehlt → dort platzieren.
        //   2. Sonst, falls Hinweis verfuegbar → Hinweis nutzen (bestehendes Verhalten).
        onCellTap(cell) {
            if (this.completed) return;
            if (this.selectedCardToken) {
                const card = this.pool.find(c => c.token === this.selectedCardToken);
                this.selectedCardToken = null;
                if (card) this.handleDrop(cell, card.kanaId, card.payload, card.token);
                return;
            }
            if (this.canHintCell(cell)) this.useHintForCell(cell);
        },

        expectedForCell(cell) {
            if (this.mode === 'schreiben') return cell.character;
            if (this.mode === 'lesen')     return cell.romanization;
            return cell.character;
        },

        playKanaAudio(cell) {
            if (typeof playCardAudio === 'function') {
                try { playCardAudio(cell.character, null, 'ja'); return; } catch (e) {}
            }
            // Server-TTS war in dieser Session schon nicht verfuegbar (z.B. 503,
            // TTS nicht konfiguriert) → direkt die Browser-Sprachausgabe nutzen.
            if (this._ttsDisabled) {
                this._speakKana(cell.character);
                return;
            }
            try {
                fetch('/api/tts', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text: cell.character, lang: 'ja', model: 'chirp' }),
                }).then(r => {
                    if (!r.ok) {
                        // 503 (TTS nicht konfiguriert) o.ae. → Fallback merken
                        this._ttsDisabled = true;
                        return null;
                    }
                    return r.json();
                }).then(data => {
                    if (data && data.audio) {
                        const audio = new Audio('data:audio/mpeg;base64,' + data.audio);
                        audio.play().catch(() => {});
                    } else {
                        this._speakKana(cell.character);
                    }
                }).catch(() => {
                    this._ttsDisabled = true;
                    this._speakKana(cell.character);
                });
            } catch (e) {
                this._speakKana(cell.character);
            }
        },

        // Fallback-Audio ueber die Web Speech API (offline, ohne Server-TTS).
        _speakKana(text) {
            try {
                if (!('speechSynthesis' in window) || !text) return;
                const u = new SpeechSynthesisUtterance(text);
                u.lang = 'ja-JP';
                u.rate = 0.9;
                window.speechSynthesis.cancel();
                window.speechSynthesis.speak(u);
            } catch (e) { /* Sprachausgabe nicht verfuegbar — still ignorieren */ }
        },

        // ── #2: gesammeltes Verwechslungs-Signal an den Server flushen ──
        flushConfusions(viaKeepalive) {
            // Gaeste haben kein Konto, an das ein Verwechslungs-Signal gebunden
            // werden koennte — Signal verwerfen statt einen 401-POST abzusetzen.
            if (!window.currentUser) { this.sessionConfusions = []; return; }
            if (!this.sessionConfusions || this.sessionConfusions.length === 0) return;
            const payload = JSON.stringify({ confusions: this.sessionConfusions.splice(0) });
            const csrf = document.querySelector('meta[name="csrf-token"]')?.content || '';
            try {
                fetch('/api/srs/kana-confusion', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
                    body: payload,
                    keepalive: !!viaKeepalive,
                }).catch(() => {});
            } catch (e) { /* still ignorieren — Signal ist best-effort */ }
        },

        // Flush auch bei Tab-/Seitenwechsel (Abandon-Fall) — sonst gehen die
        // Verwechslungen einer nicht abgeschlossenen Runde verloren.
        _installConfusionFlush() {
            if (this._confusionFlushInstalled) return;
            this._confusionFlushInstalled = true;
            document.addEventListener('visibilitychange', () => {
                if (document.visibilityState === 'hidden') this.flushConfusions(true);
            });
            window.addEventListener('pagehide', () => this.flushConfusions(true));
        },

        async rateCell(cell, forceRating) {
            const elapsed = (Date.now() - (this.cellTimes[cell.id] || this.startTime));
            const errs = cell.attempts;
            let rating;
            if (typeof forceRating === 'number') {
                // Hint genutzt → fixes Rating (Hard = 2) gemaess wissenschaftlicher
                // Empfehlung: sichtbare metakognitive Kosten fuer den Hilferuf.
                rating = forceRating;
            } else if (errs === 0 && elapsed < 3000) rating = 4;
            else if (errs === 0)                     rating = 3;
            else if (errs === 1)                     rating = 2;
            else                                     rating = 1;

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

        // ── Phase 4: Hint-Mechanik mit Pre-Testing-Gate ─────────────────────
        // Hint ist nur verfuegbar, wenn (a) noch Hints uebrig, (b) Cell schon mind.
        // einen Drop-Versuch hatte (Pre-Testing nach Bjork). Cell wird automatisch
        // korrekt gefuellt, Rating = 2 (Hard) — sichtbare metakognitive Kosten.
        canHintCell(cell) {
            if (this.hintsRemaining <= 0) return false;
            if (this.completed) return false;
            if (cell.status === 'correct') return false;
            if ((cell.attempts || 0) < 1) return false;   // Pre-Testing-Gate
            return true;
        },

        useHintForCell(cell) {
            if (!this.canHintCell(cell)) return;

            this.hintsRemaining -= 1;
            this.hintsUsed += 1;
            this.cellsHinted.push(cell.id);

            // Pool-Karte fuer diese Zelle finden, kurz hervorheben
            const targetPayload = this.expectedForCell(cell);
            const targetCard = this.pool.find(c =>
                c.kanaId === cell.kanaId && c.payload === targetPayload
            );
            if (targetCard) {
                const poolEl = this.$refs.pool;
                const cardEl = poolEl && poolEl.querySelector(`[data-token="${targetCard.token}"]`);
                if (cardEl) {
                    cardEl.classList.add('kana-grid-game__pool-card--hinted');
                    setTimeout(() => {
                        cardEl.classList.remove('kana-grid-game__pool-card--hinted');
                    }, 1500);
                }
            }

            // Nach 1.5 s: Zelle automatisch als korrekt fuellen + ans SRS mit Rating=Hard.
            // H-2: Handle merken, damit restart()/setMode() den Timer abbrechen koennen —
            // sonst mutiert ein "alter" Hint-Timer die frische Runde (Geister-Complete).
            this._hintTimer = setTimeout(() => {
                this._hintTimer = null;
                // H-2: Guard — Zelle wurde inzwischen (durch restart/setMode) zurueckgesetzt
                // oder anderweitig geloest; dann nichts mehr tun.
                if (cell.status === 'correct') return;
                cell.status = 'correct';
                cell.solved = cell.character;
                cell.hintBadge = true;   // Visual marker im Template
                this.solvedCount += 1;
                if (!cell.rated) {
                    cell.rated = true;
                    this.rateCell(cell, /* forceRating= */ 2);
                }
                // Pool-Karte entfernen
                if (targetCard) {
                    this.pool = this.pool.filter(c => c.token !== targetCard.token);
                }
                this._advanceOrComplete();
            }, 1500);
        },

        setMode(newMode) {
            if (!this.modeSwitch || this.mode === newMode) return;
            // H-2: laufenden Hint-Timer abbrechen, damit er nicht die neue Runde mutiert.
            if (this._hintTimer) { clearTimeout(this._hintTimer); this._hintTimer = null; }
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
            this.hintsRemaining = this.maxHints;
            this.hintsUsed = 0;
            this.cellsHinted = [];
            // #3 Timer-Gate: neue Modus-Runde — Uhr erst beim ersten Spielzug.
            this.startTime = Date.now();
            this.hasStarted = false;
            this.buildPool();
            this._buildBatches();
            this.$nextTick(() => this.initSortables());
        },

        onComplete() {
            this.completed = true;
            const elapsed = (Date.now() - this.startTime) / 1000;
            this.formattedTime = elapsed < 60 ? `${elapsed.toFixed(0)}s`
                                              : `${Math.floor(elapsed/60)}m ${(elapsed%60).toFixed(0)}s`;
            // Sterne-Formel: Hints zaehlen wie Fehler (sichtbare metakognitive Kosten).
            const adjustedErrors = this.totalErrors + this.hintsUsed;
            if (adjustedErrors === 0 && elapsed < 90)      this.stars = 3;
            else if (adjustedErrors <= 3 || elapsed < 180) this.stars = 2;
            else                                           this.stars = 1;

            // Perfekt = keine Fehler UND keine Hints (Bjork: nur autonomer Recall zaehlt)
            const wasPerfect = (adjustedErrors === 0);
            this.wasPerfect = wasPerfect;   // H-3: fuer Daily-Bonus-Anzeige im Template
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
            // H-1: Abschluss-Ansage inkl. Sterne-Zahl (z.B. "Geschafft! 3 Sterne").
            this.announce(`Geschafft! ${this.stars} ${this.stars === 1 ? 'Stern' : 'Sterne'}`);
            this._computeKanaStats();
            this.flushConfusions(false);
            // Analytics: Spielabschluss (Funnel-Ausgang) — guest-Flag fuer den
            // Gast->Konto-Trichter, perfect/stars als Qualitaetssignal.
            kanaTrack('kana_complete', {
                mode: this.mode, stars: this.stars,
                guest: !window.currentUser, perfect: !!this.wasPerfect,
            });
        },

        // Per-Kana-Auswertung der Runde aus den Zellen: attempts = Fehlversuche an
        // diesem Feld. Schwaechste = meiste Fehlversuche zuerst; Staerkste = auf
        // Anhieb richtig. Speist die Ergebnis-Statistik + "nur Schwaechste ueben".
        _computeKanaStats() {
            const items = (this.cells || []).map(c => ({
                kanaId: c.kanaId,
                character: c.character,
                romanization: c.romanization,
                attempts: c.attempts || 0,
            }));
            this.statStrong = items.filter(i => i.attempts === 0);
            this.statWeak = items.filter(i => i.attempts > 0)
                .sort((a, b) => b.attempts - a.attempts);
            this.weakKanaIds = new Set(this.statWeak.map(i => i.kanaId));
        },

        async restart() {
            // H-2: laufenden Hint-Timer abbrechen, sonst zaehlt er in die frische Runde.
            if (this._hintTimer) { clearTimeout(this._hintTimer); this._hintTimer = null; }
            // #11 Embed: dem Host melden, dass eine frische Runde laeuft, damit er
            // seinen Ergebnis-Zustand (done) zuruecksetzt und ggf. das Mobile-Overlay
            // wieder oeffnet. Host-Receiver existiert in index.html (~Z280).
            if (window.kgameEmbed) {
                try {
                    window.parent.postMessage(
                        { type: 'kana-embed-restart' }, window.location.origin
                    );
                } catch (e) { /* Eltern-Seite evtl. nicht erreichbar */ }
            }
            this.completed = false;
            this.wasPerfect = false;   // H-3: bis zum naechsten Abschluss neutral
            this.stars = 0;
            this.totalXp = 0;
            this.totalErrors = 0;
            this.solvedCount = 0;
            this.hintsRemaining = this.maxHints;
            this.hintsUsed = 0;
            this.cellsHinted = [];
            this.cells.forEach(c => {
                c.status = 'empty';
                c.solved = '';
                c.attempts = 0;
                c.rated = false;
                c.hintBadge = false;
                if (c._blindFilled) delete c._blindFilled;
            });
            // Variante 1 (Practice-Matching): Ziel-Tabelle bleibt geordnet, nicht
            // mischen. Sonst (Lektions-Grid) ab Runde 2 mischen. Aktivitaet
            // festhalten, damit die Session "frisch" bleibt (>1h-Pause-Logik).
            if (!this.keepGojuonOrder) this._shuffleGroups();
            this._touchPlayTimestamp();
            this.buildPool();
            // #3 Timer-Gate: frische Runde — Uhr erst beim ersten Spielzug der Runde.
            this.startTime = Date.now();
            this.hasStarted = false;
            this._buildBatches();
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

// Modus-Beschriftungen (DE) — geteilt zwischen Einstellungs- und Spiel-Seite.
// 'blind' ist als Practice-Option entfernt (Spiel-Kernlogik kennt ihn noch
// fuer alte Lesson-Grid-Configs).
const PRACTICE_MODE_LABELS = { schreiben: 'Schreiben', lesen: 'Lesen' };

// ── Schritt 1: Einstellungs-Seite (/practice/kana) ──────────────────────
// Sammelt die Filter, persistiert sie in localStorage und navigiert mit den
// gewaehlten Werten als Query-Params zur Spiel-Seite (/practice/kana/spiel).
// Eine Live-Vorschau ("≈ N Kana") fetcht den Treffer-Count, damit man keine
// leere Runde startet.
function kanaSettings() {
    const LS_KEY = 'kana_game_settings_v1';
    return {
        mode: 'schreiben',
        weakOnly: false,
        // Schrift + Reihen liegen jetzt im geteilten $store.kanaScope (EIN Picker
        // für beide Spiele). Hier nur noch Modus/weakOnly + die Live-Vorschau.
        // KEIN limit mehr: die Anzahl richtet sich nach der Auswahl (Reihen × Schrift).
        previewCount: null,        // null = noch unbekannt / Fehler
        previewLoading: false,
        previewBlocked: null,      // Meldung, wenn keine Kana freigeschaltet sind
        _previewTimer: null,

        init() {
            try {
                const saved = JSON.parse(localStorage.getItem(LS_KEY) || '{}');
                // Nur der Modus ist noch spiel-eigen; Schrift/Reihen kommen aus dem
                // geteilten Store. weakOnly wird BEWUSST NICHT geladen (bewusste
                // Einmal-Wahl pro Sitzung — sonst bliebe der Filter auf Mobile hängen).
                if (saved && typeof saved === 'object' && ['schreiben', 'lesen'].includes(saved.mode)) {
                    this.mode = saved.mode;
                }
            } catch (e) { /* localStorage nicht verfuegbar — Defaults behalten */ }
            // Vorschau ("≈ N Kana") neu zählen, wenn sich der geteilte Scope ändert.
            this.$watch('$store.kanaScope.schrift', () => this.schedulePreview());
            this.$watch('$store.kanaScope.rows', () => this.schedulePreview());
            this.refreshPreview();
        },

        get modeLabel() { return PRACTICE_MODE_LABELS[this.mode] || ''; },
        get canStart() {
            return !this.previewBlocked && (this.previewCount === null || this.previewCount > 0);
        },

        setMode(m) { this.mode = m; this.changed(); },

        changed() { this.persist(); this.schedulePreview(); },

        persist() {
            try {
                // Nur der Modus ist spiel-eigen (Schrift/Reihen → Store). weakOnly
                // wird bewusst NICHT persistiert (siehe init).
                localStorage.setItem(LS_KEY, JSON.stringify({ mode: this.mode }));
            } catch (e) { /* still ignorieren */ }
        },

        buildParams() {
            // Schrift + Reihen aus dem geteilten Store. Explizite Reihen (inkl.
            // G–P) übersteuern serverseitig den Dakuten-Schalter; "Alle" (rows=[])
            // = Basis, darum dakuten='false'. KEIN limit: gespielt wird die Auswahl.
            const sc = this.$store.kanaScope;
            const params = new URLSearchParams({
                mode: this.mode,
                schrift: sc.schrift,
                dakuten: 'false',
                weak_only: this.weakOnly ? 'true' : 'false',
            });
            if (sc.rows.length > 0) params.set('rows', sc.rows.join(','));
            return params;
        },

        schedulePreview() {
            if (this._previewTimer) clearTimeout(this._previewTimer);
            this._previewTimer = setTimeout(() => this.refreshPreview(), 220);
        },

        async refreshPreview() {
            this.previewLoading = true;
            this.previewBlocked = null;
            try {
                // Gast: Vorschau ueber den public-Endpoint mit denselben Filtern
                // (Schrift/Reihen/Dakuten/Anzahl) — der login-pflichtige
                // /session-Endpoint gaebe sonst 401. weak_only ignoriert er.
                const url = window.currentUser
                    ? '/api/practice/kana/session?' + this.buildParams().toString()
                    : '/api/practice/kana/session/public?' + this.buildParams().toString();
                const resp = await fetch(url);
                const data = await resp.json();
                if (data.message) {
                    this.previewBlocked = data.message;
                    this.previewCount = 0;
                } else {
                    this.previewCount = data.count || 0;
                }
            } catch (e) {
                this.previewCount = null;
            } finally {
                this.previewLoading = false;
            }
        },

        // ── Navigation zur Spiel-Seite ──
        startGame() {
            if (!this.canStart) return;
            this.persist();
            window.location.href = '/practice/kana/spiel?' + this.buildParams().toString();
        },
        startDaily() {
            window.location.href = '/practice/kana/spiel?challenge=daily';
        },
        startConfusion() {
            // Verwechslungs-Drill: aehnliche Kana als Cluster (Server waehlt sie).
            window.location.href = '/practice/kana/spiel?challenge=confusion';
        },
        startWeak() {
            // Einmal-Schnellstart: Intent nur per URL uebergeben, NICHT die
            // gespeicherten Einstellungen mutieren/persistieren (wie startDaily/
            // startConfusion). Sonst bliebe weakOnly in localStorage haengen und
            // die "Nur schwache Karten"-Option waere bei jedem Besuch wieder an.
            // Kein limit: geuebt werden ALLE schwachen Karten.
            const params = this.buildParams();
            params.set('weak_only', 'true');
            window.location.href = '/practice/kana/spiel?' + params.toString();
        },
    };
}

// ── Schritt 2: Spiel-Seite (/practice/kana/spiel) ───────────────────────
// Erweitert das Basis-Spiel (kanaGridGame) um: Laden der Session aus den
// URL-Query-Params (oder Tages-Challenge), Lade-/Leer-/Fehler-Phasen und
// einen sichtbaren Live-Timer (zaehlt hoch, friert bei Abschluss ein).
function kanaGameView() {
    const game = kanaGridGame(null);
    const baseOnComplete = game.onComplete;
    const baseRestart = game.restart;
    return Object.assign(game, {
        phase: 'loading',          // 'loading' | 'error' | 'empty' | 'playing'
        loadMessage: null,
        isDaily: false,
        isConfusion: false,
        isGuest: !window.currentUser,   // steuert den Konto-CTA im Ergebnis-Screen
        dailyBonusXp: 0,           // H-3: vom Daily-Endpoint geliefert, bei perfektem Abschluss angezeigt
        dailyDate: null,           // Server-Datum des Daily-Bretts (UTC) — fuer das Host-Haekchen
        liveElapsedMs: 0,
        _timerId: null,
        _embedReplayInstalled: false,   // #12: Guard gegen doppelten message-Listener
        settingsUrl: '/practice/kana',
        // Practice-Matching: echte Gojuon-Tabelle (Slots bleiben geordnet, Zufall
        // kommt aus dem Karten-Tray) — Lektions-Grids bleiben davon unberuehrt.
        keepGojuonOrder: true,

        async initView() {
            const p = new URLSearchParams(window.location.search);
            this.isDaily = (p.get('challenge') === 'daily');
            this.isConfusion = (p.get('challenge') === 'confusion');
            let url;
            if (this.isConfusion) {
                const m = p.get('mode');
                this.mode = ['schreiben', 'lesen'].includes(m) ? m : 'schreiben';
                const params = new URLSearchParams({
                    mode: this.mode,
                    schrift: p.get('schrift') || 'both',
                });
                if (p.get('limit')) params.set('limit', p.get('limit'));
                url = '/api/practice/kana/confusion?' + params.toString();
            } else if (this.isDaily) {
                url = '/api/practice/kana/daily-challenge';
                this.mode = 'schreiben';
            } else {
                const m = p.get('mode');
                this.mode = ['schreiben', 'lesen'].includes(m) ? m : 'schreiben';
                if (!window.currentUser) {
                    // Gast (Startseiten-Embed ODER direkter Aufruf der Spielseite
                    // ohne Login): voller Referenz-Scope ueber den public-Endpoint
                    // (Schrift/Reihen/Dakuten frei waehlbar), aber ohne User-State —
                    // weak_only und SRS-Sortierung gibt es nur eingeloggt.
                    // Kein limit-Default: gespielt wird genau die Auswahl.
                    const params = new URLSearchParams({
                        mode: this.mode,
                        schrift: p.get('schrift') || 'hiragana',
                        dakuten: p.get('dakuten') || 'false',
                    });
                    if (p.get('rows')) params.set('rows', p.get('rows'));
                    if (p.get('limit')) params.set('limit', p.get('limit'));
                    url = '/api/practice/kana/session/public?' + params.toString();
                } else {
                    const params = new URLSearchParams({
                        mode: this.mode,
                        schrift: p.get('schrift') || 'both',
                        dakuten: p.get('dakuten') || 'true',
                        weak_only: p.get('weak_only') || 'false',
                    });
                    if (p.get('rows')) params.set('rows', p.get('rows'));
                    if (p.get('limit')) params.set('limit', p.get('limit'));
                    url = '/api/practice/kana/session?' + params.toString();
                }
            }

            let data;
            try {
                const resp = await fetch(url);
                data = await resp.json();
            } catch (e) {
                this.phase = 'error';
                this.loadMessage = 'Session konnte nicht geladen werden (Netzwerkfehler).';
                this._notifyEmbedError();
                return;
            }

            const kana = data.kana || [];
            if (kana.length === 0) {
                this.phase = 'empty';
                this.loadMessage = data.message || 'Keine Karten für diese Auswahl gefunden.';
                this._notifyEmbedError();
                return;
            }
            // H-3: Bonus-XP der Tages-Challenge merken (Server liefert 25 bei
            // perfektem Abschluss) — wird im Ergebnis-Screen nur angezeigt, nicht gutgeschrieben.
            if (this.isDaily && typeof data.bonus_xp === 'number') {
                this.dailyBonusXp = data.bonus_xp;
            }
            // Server-Datum des Daily-Bretts merken: der Embed-Host keyed sein
            // Tages-Haekchen darauf (Client-Kalendertag kann um Mitternacht
            // vom Server-Brett abweichen).
            if (this.isDaily && data.date) {
                this.dailyDate = data.date;
            }

            // Grid + Pool aus der Session aufbauen (analog zum frueheren practiceGameWrapper)
            this.kana = kana.map(k => ({
                id: k.kana_id,
                character: k.character,
                romanization: k.romanization,
                type: k.type,
                audio_url: null,
                lesson_content_id: k.lesson_content_id,
                stroke_order_info: k.stroke_order_info,
                mnemonic: k.mnemonic,   // vom Server geliefert, bisher ungenutzt -> Fehler-Feedback
            }));
            const ROW_ORDER = ['vowels', 'k', 's', 't', 'n', 'h', 'm', 'y', 'r', 'w', 'n_kons', 'g', 'z', 'd', 'b', 'p'];
            const byRow = {};
            kana.forEach(k => {
                const key = k.row || 'other';
                if (!byRow[key]) byRow[key] = [];
                byRow[key].push(k.kana_id);
            });
            // Cluster-Keys (cf_*, Verwechslungs-Drill) sind nicht in ROW_ORDER —
            // sie kommen nach den Gojuon-Reihen in ihrer Server-Reihenfolge dran.
            // row_labels (vom /confusion-Endpoint) liefert die Cluster-Beschriftung.
            const labelMap = data.row_labels || {};
            const orderedKeys = ROW_ORDER.filter(k => byRow[k])
                .concat(Object.keys(byRow).filter(k => !ROW_ORDER.includes(k) && k !== 'other'));
            this.rows = orderedKeys.map(k => ({
                key: k,
                label: labelMap[k] || PRACTICE_ROW_LABELS[k] || k,
                kana_ids: byRow[k],
            }));
            if (byRow.other) this.rows.push({ key: 'other', label: '—', kana_ids: byRow.other });
            // Schnappschuss der vollen Reihen — fuer "nur Schwaechste ueben" wird
            // hieraus rein clientseitig auf die Fehler-Kana zurueckgefiltert.
            this._fullRows = this.rows.map(r => ({ ...r, kana_ids: [...r.kana_ids] }));

            this._config = {
                default_mode: this.mode,
                allow_mode_switch: false,
                grid_layout: 'rows',
                shuffle_pool: true,
                timer_enabled: false,
            };
            this.modeSwitch = false;
            this.perfectStreak = parseInt(localStorage.getItem('kana_grid_perfect_streak') || '0', 10);
            this.buildCellsAndPool();
            this.loading = false;
            this.phase = 'playing';
            await this.$nextTick();
            this.initSortables();
            // #3 Timer-Gate: NICHT mehr sofort beim Laden starten. Der Live-Timer
            // (und die echte startTime) werden erst beim ersten Spielzug ueber
            // _markStarted() angeworfen — HUD steht bis dahin auf 0:00. So misst die
            // Sterne-Formel die tatsaechliche Loesungszeit (Embed UND Vollbild).
            this.startTime = Date.now();   // Fallback fuer rateCell(), bis 1. Zug
            this.hasStarted = false;
            this.liveElapsedMs = 0;
            this._installConfusionFlush();
            // #12 Embed: auf Host-Replay hoeren — eine frische Runde ohne iframe-
            // Remount anstossen koennen (Host sendet kana-embed-replay).
            this._installEmbedReplayListener();
        },

        // WICHTIG: Methoden, KEINE getter. Diese Komponente wird via
        // Object.assign(kanaGridGame(null), {...}) gebaut — Object.assign ruft
        // getter der Quelle EINMAL auf und kopiert nur deren (eingefrorenen)
        // Rückgabewert. Als getter wären Timer/Fortschritt statisch. Im Template
        // daher mit () aufrufen: liveTimeLabel(), modeLabel(), progressPct().
        modeLabel() {
            if (this.isConfusion) return 'Verwechslungs-Paare';
            return this.isDaily ? 'Tages-Challenge' : (PRACTICE_MODE_LABELS[this.mode] || '');
        },
        liveTimeLabel() {
            const s = Math.max(0, Math.floor(this.liveElapsedMs / 1000));
            return Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0');
        },
        progressPct() {
            return this.totalCells > 0 ? Math.round((this.solvedCount / this.totalCells) * 100) : 0;
        },

        startLiveTimer() {
            this.stopLiveTimer();
            this.liveElapsedMs = Date.now() - this.startTime;
            this._timerId = setInterval(() => {
                if (this.completed) { this.stopLiveTimer(); return; }
                this.liveElapsedMs = Date.now() - this.startTime;
            }, 250);
        },
        stopLiveTimer() {
            if (this._timerId) { clearInterval(this._timerId); this._timerId = null; }
        },

        // Timer bei Abschluss exakt einfrieren; bei Neustart wieder anwerfen.
        onComplete() {
            baseOnComplete.call(this);
            this.liveElapsedMs = Date.now() - this.startTime;
            this.stopLiveTimer();
            if (window.kgameEmbed) this._postEmbedResult();
        },
        async restart() {
            await baseRestart.call(this);
            // #3 Timer-Gate: HUD bleibt 0:00, bis der erste Spielzug der neuen
            // Runde _markStarted() (→ startLiveTimer) ausloest. baseRestart hat
            // hasStarted bereits zurueckgesetzt und im Embed kana-embed-restart gesendet.
            this.stopLiveTimer();
            this.liveElapsedMs = 0;
        },

        // Ergebnis-Aktion „nur Schwaechste ueben": filtert die vollen Reihen auf die
        // Kana mit Fehlversuchen dieser Runde und startet daraus eine frische Runde —
        // rein clientseitig (die Kana sind bereits geladen, kein neuer Fetch).
        async playWeakOnly() {
            if (!this.weakKanaIds || !this.weakKanaIds.size || !this._fullRows) return;
            const weak = this.weakKanaIds;
            this.rows = this._fullRows
                .map(r => ({ ...r, kana_ids: r.kana_ids.filter(id => weak.has(id)) }))
                .filter(r => r.kana_ids.length);
            this.weakMode = true;
            this.activeHint = null;
            this.hintsRemaining = this.maxHints;
            this.hintsUsed = 0;
            this.cellsHinted = [];
            this.wasPerfect = false;
            this.stars = 0;
            // setzt cells/pool/batches + solved/errors/xp/completed zurueck.
            this.buildCellsAndPool();
            this.startTime = Date.now();
            this.hasStarted = false;
            this.stopLiveTimer();
            this.liveElapsedMs = 0;
            if (window.kanaTrack) window.kanaTrack('kana_play_weak', { count: weak.size });
            await this.$nextTick();
            this.initSortables();
        },

        // #12 Embed: auf das Host→iframe-Signal kana-embed-replay hoeren und damit
        // lokal eine frische Runde starten — ohne das iframe neu zu laden (Remount).
        // Origin-Check Pflicht (gleiche Origin, same-origin iframe). Nur im Embed-Pfad
        // installiert; im Vollbild-Standalone passiert nichts. Idempotent.
        _installEmbedReplayListener() {
            if (!window.kgameEmbed || this._embedReplayInstalled) return;
            this._embedReplayInstalled = true;
            window.addEventListener('message', (ev) => {
                if (ev.origin !== window.location.origin) return;
                const d = ev.data || {};
                if (d.type === 'kana-embed-replay') this.restart();
            });
        },

        // Embed: leere/fehlerhafte Runde an die Eltern-Seite melden, damit sie ein
        // (Mobile-)Vollbild-Overlay schliesst (stellt den Body-Scroll wieder her)
        // und einen Retry-Hinweis zeigt — statt den Gast vor einer leeren Box mit
        // gesperrtem Body stehen zu lassen.
        _notifyEmbedError() {
            if (!window.kgameEmbed) return;
            try {
                window.parent.postMessage({ type: 'kana-embed-error' }, window.location.origin);
            } catch (e) { /* Eltern-Seite evtl. nicht erreichbar */ }
        },

        // Embed: Ergebnis an die Eltern-Seite (Startseite) melden, damit sie die
        // Score- + Konto-CTA-Karte zeigen kann. Gleiche Origin (iframe same-origin).
        _postEmbedResult() {
            try {
                window.parent.postMessage({
                    type: 'kana-embed-complete',
                    stars: this.stars,
                    solved: this.solvedCount,
                    total: this.totalCells,
                    errors: this.totalErrors,
                    timeLabel: this.liveTimeLabel(),
                    perfect: !!this.wasPerfect,
                    dailyDate: this.dailyDate,   // null ausser bei challenge=daily
                }, window.location.origin);
            } catch (e) { /* Eltern-Seite evtl. nicht erreichbar */ }
        },

        goToSettings() {
            if (window.kgameEmbed) {
                // Im iframe nicht hart navigieren — die Eltern-Seite entscheidet
                // (Overlay schliessen / zum Anmelden scrollen).
                try {
                    window.parent.postMessage({ type: 'kana-embed-settings' }, window.location.origin);
                } catch (e) { /* noop */ }
                return;
            }
            window.location.href = this.settingsUrl;
        },
    });
}

// ── Analytics: best-effort Event ueber den Plausible-Stub ──
// window.plausible ist in base.html IMMER als no-op-Stub vorhanden; real
// gesendet wird nur, wenn PLAUSIBLE_DOMAIN gesetzt ist. Schluckt jeden Fehler
// still — Tracking darf das Spiel nie blockieren.
function kanaTrack(event, props) {
    try {
        if (typeof window.plausible === 'function') {
            window.plausible(event, props ? { props: props } : undefined);
        }
    } catch (e) { /* best-effort */ }
}
window.kanaTrack = kanaTrack;

window.kanaSettings = kanaSettings;
window.kanaGameView = kanaGameView;
