/* ════════════════════════════════════════════════════════════════════════
   Geteilter Kana-Scope (Schrift + Reihen) — EIN Speicher für BEIDE Spiele auf
   /practice/kana (Zuordnung `kanaSettings` + Kana Storm `kanaStormGame`), damit
   die Auswahl nicht pro Spiel doppelt getroffen werden muss.

   Achse-Trennung: "Was übe ich" (Schrift + Reihen) = geteilter Scope (hier);
   "Wie übe ich" (Modus bzw. Dauer/Daily) bleibt spiel-eigen.

   • Reine Client-Persistenz: localStorage-Key 'kanaScope'. Migriert einmalig
     aus den alten getrennten Keys (kana_game_settings_v1 bzw. kanaStorm*).
   • "Alle" (rows = []) = Basis-Reihen (46). Dakuten kommt durch EXPLIZITE
     G–P-Chips dazu — kein separater Toggle mehr (Einzelreihen-Wahl, auch nur G,
     bleibt damit in beiden Spielen möglich). Server-seitig übersteuern explizite
     Reihen den Dakuten-Schalter (_guest_kana_chars), darum sendet der Aufrufer
     rows + dakuten='false'.
   • Nur auf /practice/kana relevant: die Vollbild-Storm-Seite, der Startseiten-
     Hero und /daily setzen `scopeExternal` NICHT und nutzen weiter ihre eigenen
     Picker. Der Store existiert global (harmlos), wird dort aber nicht gelesen.
   ════════════════════════════════════════════════════════════════════════ */
(function () {
    const LS = 'kanaScope';
    const SCHRIFT = ['hiragana', 'katakana', 'both'];
    // Reihen-Metadaten der geteilten Chips. Keys identisch zu kana_rows.py /
    // PRACTICE_ROW_LABELS / KANA_STORM_ROW_SIZES (G–P = Dakuten/Handakuten).
    const ROWS = [
        { key: 'vowels', label: 'あいうえお' }, { key: 'k', label: 'K' },
        { key: 's', label: 'S' }, { key: 't', label: 'T' }, { key: 'n', label: 'N' },
        { key: 'h', label: 'H' }, { key: 'm', label: 'M' }, { key: 'y', label: 'Y' },
        { key: 'r', label: 'R' }, { key: 'w', label: 'W' }, { key: 'n_kons', label: 'ん' },
        { key: 'g', label: 'G' }, { key: 'z', label: 'Z' }, { key: 'd', label: 'D' },
        { key: 'b', label: 'B' }, { key: 'p', label: 'P' },
    ];
    const VALID = new Set(ROWS.map((r) => r.key));
    const ROW_SIZES = {
        vowels: 5, k: 5, s: 5, t: 5, n: 5, h: 5, m: 5, y: 3, r: 5, w: 2, n_kons: 1,
        g: 5, z: 5, d: 5, b: 5, p: 5,
    };
    const BASE_COUNT = 46;
    // Anfänger-Default: die ersten 5 Hiragana-Reihen (あ・か・さ・た・な).
    // Die volle Tabelle (alle 46) wirkt überladen — "Alle" bleibt per Chip
    // explizit wählbar (rows = []).
    const FIRST_FIVE = ['vowels', 'k', 's', 't', 'n'];

    function read(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }

    // Anfangswerte: vorhandenes kanaScope, sonst aus den alten Keys seeden
    // (Matching bevorzugt — reicheres Format —, sonst Storm).
    function seed() {
        try {
            const cur = JSON.parse(read(LS) || 'null');
            if (cur && typeof cur === 'object') return cur;
        } catch (e) { /* fall through */ }
        // Frische Besucher: erste 5 Hiragana-Reihen. Rückkehrer behalten ihre
        // (migrierte) Auswahl aus den alten getrennten Keys.
        let schrift = 'hiragana';
        let rows = FIRST_FIVE.slice();
        try {
            const mRaw = read('kana_game_settings_v1');
            const m = mRaw ? JSON.parse(mRaw) : null;
            if (m && typeof m === 'object') {
                if (SCHRIFT.includes(m.schrift)) schrift = m.schrift;
                if (Array.isArray(m.selectedRows)) rows = m.selectedRows;
            } else {
                const ss = read('kanaStormSchrift');
                if (SCHRIFT.includes(ss)) schrift = ss;
                const srRaw = read('kanaStormRows');
                if (srRaw) { const sr = JSON.parse(srRaw); if (Array.isArray(sr)) rows = sr; }
            }
        } catch (e) { /* Defaults behalten */ }
        return { schrift, rows };
    }

    document.addEventListener('alpine:init', () => {
        if (!window.Alpine || !window.Alpine.store) return;
        if (window.Alpine.store('kanaScope')) return;   // idempotent
        const s = seed();
        window.Alpine.store('kanaScope', {
            ROWS,
            schrift: SCHRIFT.includes(s.schrift) ? s.schrift : 'hiragana',
            rows: Array.isArray(s.rows) ? s.rows.filter((k) => VALID.has(k)) : [],

            get allRowsActive() { return this.rows.length === 0; },
            // Live-Anzahl (Reihen × Schrift) ohne Server-Call.
            count() {
                const base = this.rows.length
                    ? this.rows.reduce((a, k) => a + (ROW_SIZES[k] || 0), 0)
                    : BASE_COUNT;
                return this.schrift === 'both' ? base * 2 : base;
            },
            rowsLabel() { return this.allRowsActive ? 'alle' : (this.rows.length + ' gewählt'); },

            setSchrift(v) { if (SCHRIFT.includes(v)) { this.schrift = v; this._save(); } },
            toggleRow(k) {
                if (!VALID.has(k)) return;
                this.rows = this.rows.includes(k)
                    ? this.rows.filter((x) => x !== k)
                    : [...this.rows, k];
                this._save();
            },
            selectAll() { this.rows = []; this._save(); },

            _save() {
                try {
                    localStorage.setItem(LS, JSON.stringify({ schrift: this.schrift, rows: this.rows }));
                } catch (e) { /* localStorage evtl. nicht verfügbar */ }
            },
        });
        window.Alpine.store('kanaScope')._save();   // gewanderten Seed sofort verfestigen
    });
})();
