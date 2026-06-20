/* Test-/Pruefungsseite (/pruefen) — Session-Loop.
 * Eine Frage = ein integrierter Vollbild-Screen (Client-Schritt, kein Reload).
 * Spiegelt das Muster von review.html / practice_kana_game.html.
 * Global definiert, damit x-data="pruefenGame()" es vor Alpine-Init findet.
 */
function pruefenGame() {
  return {
    phase: 'loading',     // loading | empty | question | feedback | result
    mode: 'uebung',       // uebung | pruefung
    questions: [],
    idx: 0,
    selected: null,       // MC/true_false: gewaehlte Option-ID
    pairs: {},            // matching: promptIndex -> answerIndex
    active: null,         // matching: {side:'prompt'|'answer', index}
    showHint: false,
    lastResult: null,     // Antwort-Feedback (Uebung)
    answers: [],          // gesammelte Payloads fuer /grade
    correctSoFar: 0,
    wrongIds: [],
    grade: null,          // Ergebnis von /grade
    startTime: null,
    now: null,
    _timer: null,

    init() {
      const p = new URLSearchParams(window.location.search);
      this.mode = p.get('mode') === 'pruefung' ? 'pruefung' : 'uebung';
      fetch('/api/pruefen/pool' + window.location.search, { headers: { 'X-Requested-With': 'fetch' } })
        .then(r => (r.ok ? r.json() : Promise.reject(r.status)))
        .then(d => {
          this.questions = (d && d.questions) || [];
          if (!this.questions.length) { this.phase = 'empty'; return; }
          this.startTime = Date.now();
          if (this.mode === 'pruefung') this._startTimer();
          this.phase = 'question';
        })
        .catch(() => { this.phase = 'empty'; });
      this._bindKeys();
    },

    // ── Getter ──────────────────────────────────────────────
    get current() { return this.questions[this.idx] || {}; },
    get progressPct() { return this.questions.length ? Math.round((100 * this.idx) / this.questions.length) : 0; },
    get isLast() { return this.idx >= this.questions.length - 1; },
    get metaLine() {
      const c = this.current;
      if (!c.type) return '';
      const t = { multiple_choice: 'Multiple Choice', true_false: 'Wahr/Falsch', matching: 'Zuordnung' }[c.type] || '';
      const lesson = (c.lesson && c.lesson.title) ? c.lesson.title + ' · ' : '';
      const diff = c.difficulty ? ' · ' + '★'.repeat(Math.min(c.difficulty, 5)) : '';
      return lesson + t + diff;
    },
    get canSubmit() {
      const c = this.current;
      if (c.type === 'matching') return !!(c.matching && Object.keys(this.pairs).length === c.matching.prompts.length);
      return this.selected != null;
    },
    get timerLabel() {
      if (!this.startTime || !this.now) return '';
      const s = Math.floor((this.now - this.startTime) / 1000);
      const m = Math.floor(s / 60), ss = s % 60;
      return (m < 10 ? '0' : '') + m + ':' + (ss < 10 ? '0' : '') + ss;
    },

    _startTimer() { this.now = Date.now(); this._timer = setInterval(() => { this.now = Date.now(); }, 1000); },
    _stopTimer() { if (this._timer) { clearInterval(this._timer); this._timer = null; } },

    // ── Multiple Choice / Wahr-Falsch ───────────────────────
    selectOption(id) { if (this.phase === 'question') this.selected = id; },
    optionClass(o) {
      if (this.phase !== 'feedback' || !this.lastResult) return this.selected === o.id ? 'is-selected' : '';
      if (this.lastResult.correct_option_id === o.id) return 'is-correct';
      if (this.selected === o.id) return 'is-wrong';
      return '';
    },

    // ── Matching (Tap-to-pair) ──────────────────────────────
    pairOf(i) { return (i in this.pairs) ? this.pairs[i] : null; },
    promptOfAnswer(j) { for (const k in this.pairs) { if (this.pairs[k] === j) return parseInt(k, 10); } return null; },
    pairBadge(i) { return i + 1; },
    answerBadge(j) { const pi = this.promptOfAnswer(j); return pi != null ? pi + 1 : ''; },
    answerPaired(j) { return this.promptOfAnswer(j); },
    matchPromptClass(i) {
      if (this.active && this.active.side === 'prompt' && this.active.index === i) return 'is-active';
      return this.pairOf(i) != null ? 'is-done' : '';
    },
    matchAnswerClass(j) {
      if (this.active && this.active.side === 'answer' && this.active.index === j) return 'is-active';
      return this.answerPaired(j) != null ? 'is-done' : '';
    },
    tapPrompt(i) {
      if (this.phase !== 'question') return;
      if (this.pairOf(i) != null) { delete this.pairs[i]; this.pairs = { ...this.pairs }; return; }
      if (this.active && this.active.side === 'answer') { this.pairs[i] = this.active.index; this.pairs = { ...this.pairs }; this.active = null; return; }
      this.active = (this.active && this.active.side === 'prompt' && this.active.index === i) ? null : { side: 'prompt', index: i };
    },
    tapAnswer(j) {
      if (this.phase !== 'question') return;
      const pi = this.promptOfAnswer(j);
      if (pi != null) { delete this.pairs[pi]; this.pairs = { ...this.pairs }; return; }
      if (this.active && this.active.side === 'prompt') { this.pairs[this.active.index] = j; this.pairs = { ...this.pairs }; this.active = null; return; }
      this.active = (this.active && this.active.side === 'answer' && this.active.index === j) ? null : { side: 'answer', index: j };
    },

    // ── Ablauf ──────────────────────────────────────────────
    _payload() {
      const c = this.current;
      if (c.type === 'matching') {
        const pairs = c.matching.prompts.map((p, i) => ({ prompt: p, answer: c.matching.answers[this.pairs[i]] }));
        return { question_id: c.id, pairs };
      }
      return { question_id: c.id, selected_option_id: this.selected };
    },
    submit() {
      if (!this.canSubmit) return;
      const payload = this._payload();
      this.answers.push(payload);
      if (this.mode === 'uebung') {
        this._post('/api/pruefen/check', payload).then(res => {
          this.lastResult = res || {};
          if (res && res.is_correct) this.correctSoFar++; else this.wrongIds.push(this.current.id);
          this.phase = 'feedback';
        });
      } else {
        this.next();
      }
    },
    next() {
      this.idx++;
      this.selected = null; this.pairs = {}; this.active = null; this.showHint = false; this.lastResult = null;
      if (this.idx >= this.questions.length) this.finish();
      else this.phase = 'question';
    },
    finish() {
      this._stopTimer();
      this.phase = 'loading';
      this._post('/api/pruefen/grade', { answers: this.answers }).then(res => {
        this.grade = res || {};
        this.phase = 'result';
      });
    },
    retryWrong() {
      const ids = this.wrongIds.length
        ? this.wrongIds
        : (this.grade && this.grade.details ? this.grade.details.filter(d => !d.is_correct).map(d => d.question_id) : []);
      const set = new Set(ids);
      const subset = this.questions.filter(q => set.has(q.id));
      if (!subset.length) return;
      this.questions = subset; this.idx = 0; this.answers = []; this.wrongIds = []; this.correctSoFar = 0;
      this.selected = null; this.pairs = {}; this.active = null; this.showHint = false; this.lastResult = null; this.grade = null;
      this.startTime = Date.now();
      if (this.mode === 'pruefung') this._startTimer();
      this.phase = 'question';
    },
    restart() { window.location.href = '/pruefen'; },
    quit() { if (window.confirm('Test beenden? Dein Fortschritt geht verloren.')) window.location.href = '/pruefen'; },

    // ── Ergebnis-Helfer ─────────────────────────────────────
    get scorePct() { return this.grade ? this.grade.score_pct : 0; },
    get ringColor() {
      const p = this.scorePct;
      return p >= 80 ? 'var(--matcha)' : (p >= 60 ? 'var(--kincha)' : 'var(--color-error)');
    },
    get ringDash() {
      const c = 2 * Math.PI * 52;
      return (c * this.scorePct / 100) + ' ' + c;
    },
    get resultHeadline() {
      const p = this.scorePct;
      if (p >= 80) return 'Stark — du bist N5-reif.';
      if (p >= 60) return 'Knapp dran — fast geschafft.';
      return 'Noch etwas Übung — du kommst hin.';
    },
    wrongDetails() { return (this.grade && this.grade.details) ? this.grade.details.filter(d => !d.is_correct) : []; },
    typeRows() {
      const bt = (this.grade && this.grade.by_type) || {};
      const names = { multiple_choice: 'Multiple Choice', true_false: 'Wahr/Falsch', matching: 'Zuordnung' };
      return Object.keys(bt).map(k => ({ name: names[k] || k, correct: bt[k].correct, total: bt[k].total, earned: bt[k].earned }));
    },
    lessonRows() { return Object.values((this.grade && this.grade.by_lesson) || {}); },
    // Balken nutzt Teilkredit (earned/total) -> gleiche Basis wie score_pct;
    // der Zaehler 'x/y' zeigt weiter ganze, voll-richtige Fragen.
    pct(row) {
      const val = (row.earned != null) ? row.earned : row.correct;
      return row.total ? Math.round((100 * val) / row.total) : 0;
    },

    // ── Infrastruktur ───────────────────────────────────────
    _post(url, body) {
      const meta = document.querySelector('meta[name="csrf-token"]');
      const headers = { 'Content-Type': 'application/json' };
      if (meta) headers['X-CSRFToken'] = meta.getAttribute('content');
      return fetch(url, { method: 'POST', headers, body: JSON.stringify(body) })
        .then(r => (r.ok ? r.json() : null))
        .catch(() => null);
    },
    _bindKeys() {
      window.addEventListener('keydown', (e) => {
        if (this.phase === 'question') {
          const c = this.current;
          if (c.type === 'multiple_choice' && /^[1-9]$/.test(e.key)) {
            const i = parseInt(e.key, 10) - 1;
            if (c.options && c.options[i]) this.selectOption(c.options[i].id);
          } else if (c.type === 'true_false') {
            if (e.key === 'r' || e.key === 'R') this._tfPick(true);
            if (e.key === 'f' || e.key === 'F') this._tfPick(false);
          }
          if (e.key === 'Enter' && this.canSubmit) this.submit();
        } else if (this.phase === 'feedback') {
          if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); this.next(); }
        }
      });
    },
    _tfPick(isTrue) {
      const c = this.current;
      if (!c.options) return;
      const re = isTrue ? /wahr|richtig|true|ja|○|◯/i : /falsch|false|nein|×|✗/i;
      const opt = c.options.find(o => re.test(o.text));
      if (opt) this.selectOption(opt.id);
      else if (c.options[isTrue ? 0 : 1]) this.selectOption(c.options[isTrue ? 0 : 1].id);
    },
  };
}
