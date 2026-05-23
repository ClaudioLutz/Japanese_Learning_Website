/* Mobile screen recipes — Review, Hero, Path
   Each renders into a 390×844 iOS device.
   Uses CSS variables from ../colors_and_type.css. */

const M = {
  shu: '#EB6101', shuDeep: '#B84A00', kon: '#1F2A44', washi: '#FAF7F2',
  kinari: '#F5F0E8', sumi: '#1C1C1C', matcha: '#7A9033', kincha: '#C7802D',
  ink100: '#F1EDE6', ink200: '#E4DED4', ink300: '#D4CCBE', ink500: '#7A7368',
  ink600: '#5C564D', ink700: '#403B34', kon50: '#F2F4F8', kon100: '#E1E5EE',
  fontDisp: '"Geist", -apple-system, system-ui, sans-serif',
  fontBody: '"Inter", -apple-system, system-ui, sans-serif',
  fontJp: '"Noto Sans JP", system-ui, sans-serif',
  fontJpSerif: '"Noto Serif JP", serif',
  fontSerif: '"Fraunces", Georgia, serif',
  fontMono: '"Geist Mono", "JetBrains Mono", monospace',
};

// ════════════════ A · REVIEW SESSION (one-hand FSRS) ════════════════
function ReviewMobile() {
  return (
    <div style={{ height: '100%', background: M.washi, display: 'flex', flexDirection: 'column', fontFamily: M.fontBody }}>
      {/* compact top bar */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '8px 16px 12px' }}>
        <button style={{ width: 36, height: 36, borderRadius: 10, border: `1px solid ${M.ink200}`, background: '#fff', color: M.ink700, fontSize: 16 }}>✕</button>
        <div style={{ flex: 1, height: 6, background: M.ink100, borderRadius: 3, overflow: 'hidden' }}>
          <div style={{ width: '48%', height: '100%', background: M.shu }}/>
        </div>
        <span style={{ fontFamily: M.fontMono, fontSize: 12, color: M.ink500, fontVariantNumeric: 'tabular-nums' }}>6/12</span>
      </div>
      {/* meta row */}
      <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0 20px', fontFamily: M.fontMono, fontSize: 11, color: M.ink500, textTransform: 'uppercase', letterSpacing: '.06em' }}>
        <span>Wiederholen · N5</span>
        <span>00:42</span>
      </div>
      {/* card face — fills upper third */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '24px 20px' }}>
        <div style={{ width: '100%', background: '#fff', border: `1px solid ${M.ink200}`, borderRadius: 18, padding: '40px 20px 36px', textAlign: 'center', boxShadow: '0 18px 40px -22px rgba(28,26,23,.25)' }}>
          <div style={{ fontFamily: M.fontJpSerif, fontSize: 120, color: M.sumi, lineHeight: 1, fontWeight: 500 }}>水</div>
          <div style={{ marginTop: 16, fontFamily: M.fontJp, fontSize: 22, color: M.kon }}>みず</div>
          <div style={{ marginTop: 6, fontSize: 14, color: M.ink500, fontStyle: 'italic' }}>— Wasser —</div>
        </div>
        <div style={{ marginTop: 14, fontSize: 12, color: M.ink500, display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ width: 24, height: 24, borderRadius: 6, background: M.ink100, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 11 }}>↑</span>
          Wischen oder antippen zum Umdrehen
        </div>
      </div>
      {/* grade buttons — thumb zone, 2×2 */}
      <div style={{ padding: '0 16px 12px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
        <GradeBtn label="Wieder" when="< 10 m" tone="again"/>
        <GradeBtn label="Schwer" when="8 h" tone="hard"/>
        <GradeBtn label="Gut" when="2 d" tone="good"/>
        <GradeBtn label="Leicht" when="5 d" tone="easy"/>
      </div>
      {/* tab bar with center-CTA */}
      <BottomNav active="reviews" badge={11}/>
    </div>
  );
}

function GradeBtn({ label, when, tone }) {
  const tones = {
    again: { bg: '#fff', bd: 'rgba(209,75,61,.4)', fg: '#D14B3D' },
    hard:  { bg: '#fff', bd: 'rgba(199,128,45,.4)', fg: M.kincha },
    good:  { bg: '#fff', bd: 'rgba(31,42,68,.25)', fg: M.kon },
    easy:  { bg: M.matcha, bd: M.matcha, fg: '#fff' },
  }[tone];
  return (
    <button style={{
      minHeight: 64, borderRadius: 14, border: `1.5px solid ${tones.bd}`, background: tones.bg, color: tones.fg,
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 2,
      fontFamily: M.fontBody, cursor: 'pointer',
    }}>
      <span style={{ fontFamily: M.fontDisp, fontWeight: 600, fontSize: 17 }}>{label}</span>
      <span style={{ fontFamily: M.fontMono, fontSize: 11, opacity: .8 }}>{when}</span>
    </button>
  );
}

function BottomNav({ active = 'path', badge = 0 }) {
  const items = [
    { id: 'path', icon: '🗺️', lbl: 'Pfad' },
    { id: 'lessons', icon: '📖', lbl: 'Lektionen' },
    { id: 'reviews', icon: '🧠', lbl: 'Reviews', center: true },
    { id: 'stats', icon: '📊', lbl: 'Stats' },
    { id: 'me', icon: '👤', lbl: 'Profil' },
  ];
  return (
    <div style={{
      background: 'rgba(255,255,255,.92)', backdropFilter: 'saturate(180%) blur(16px)',
      borderTop: `1px solid ${M.ink200}`, padding: '8px 12px 22px',
      display: 'flex', alignItems: 'flex-end', justifyContent: 'space-around', gap: 4,
    }}>
      {items.map(it => it.center ? (
        <button key={it.id} style={{
          marginTop: -22, width: 56, height: 56, borderRadius: 28, border: 'none',
          background: `linear-gradient(180deg, ${M.shu}, ${M.shuDeep})`, color: '#fff',
          boxShadow: 'inset 0 1px 0 rgba(255,255,255,.2), 0 6px 16px rgba(184,74,0,.35), 0 0 0 1px rgba(184,74,0,.4)',
          fontSize: 22, position: 'relative', cursor: 'pointer',
        }}>
          {it.icon}
          {badge > 0 && (
            <span style={{ position: 'absolute', top: -2, right: -4, minWidth: 20, height: 20, padding: '0 5px', background: M.kon, color: '#fff', borderRadius: 10, fontSize: 10, fontFamily: M.fontMono, fontWeight: 700, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', border: '2px solid #fff' }}>{badge}</span>
          )}
        </button>
      ) : (
        <button key={it.id} style={{
          flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2, padding: '6px 0',
          background: 'transparent', border: 'none', cursor: 'pointer',
          color: active === it.id ? M.shu : M.ink500,
        }}>
          <span style={{ fontSize: 20, opacity: active === it.id ? 1 : .7 }}>{it.icon}</span>
          <span style={{ fontFamily: M.fontDisp, fontSize: 10, fontWeight: 600 }}>{it.lbl}</span>
        </button>
      ))}
    </div>
  );
}

// ════════════════ B · MARKETING HERO (mobile-first) ════════════════
function HeroMobile() {
  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', fontFamily: M.fontBody, background: M.washi, position: 'relative' }}>
      {/* mini topnav with hamburger */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 16px', background: 'rgba(255,255,255,.85)', backdropFilter: 'saturate(180%) blur(14px)', borderBottom: `1px solid ${M.ink200}` }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Torii size={26} color={M.kon}/>
          <span style={{ fontFamily: M.fontSerif, fontWeight: 600, fontSize: 15, fontVariationSettings: '"opsz" 14', color: '#1a1a1a' }}>Japanese Learning</span>
        </div>
        <button style={{ width: 36, height: 36, borderRadius: 10, border: 'none', background: 'transparent', color: M.kon, fontSize: 18 }}>☰</button>
      </div>
      {/* hero, scrollable */}
      <div style={{ flex: 1, overflow: 'auto', padding: '24px 20px 100px',
        background: `radial-gradient(ellipse 120% 60% at 50% 0%, rgba(31,42,68,.16), transparent 60%), radial-gradient(ellipse 80% 50% at 90% 5%, rgba(235,97,1,.10), transparent 55%), linear-gradient(180deg, ${M.washi} 0%, ${M.kinari} 100%)`,
      }}>
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '5px 11px', background: '#fff', border: `1px solid ${M.ink200}`, borderRadius: 9999, fontFamily: M.fontDisp, fontSize: 10, fontWeight: 600, letterSpacing: '.08em', textTransform: 'uppercase', color: M.ink500 }}>
          <span style={{ color: M.shu }}>⛩</span>JLPT N5 · auf Deutsch
        </span>
        <h1 style={{ fontFamily: M.fontDisp, fontWeight: 510, fontSize: 'clamp(2.6rem, 8vw, 3.4rem)', letterSpacing: '-.03em', lineHeight: 1.02, color: M.kon, margin: '14px 0 12px', textWrap: 'balance' }}>
          Hiragana am Morgen.<br/><span style={{ color: M.shu }}>Kanji</span> am Abend.
        </h1>
        <p style={{ margin: 0, color: M.ink600, fontSize: 16, lineHeight: 1.55 }}>
          Strukturiert nach JLPT-N5. 261 Vokabeln, 44 Kanji, wöchentlich neu — auf Deutsch erklärt.
        </p>
        {/* mobile design moment — single big card with stroke hint */}
        <div style={{ marginTop: 22, background: '#fff', border: `1px solid ${M.ink200}`, borderRadius: 16, padding: '28px 18px', textAlign: 'center', boxShadow: '0 22px 50px -28px rgba(28,26,23,.25)' }}>
          <div style={{ fontFamily: M.fontMono, fontSize: 10, color: M.ink500, letterSpacing: '.08em', textTransform: 'uppercase', marginBottom: 10 }}>LEKTION 01 · あ-Reihe</div>
          <div style={{ fontFamily: M.fontJp, fontWeight: 500, fontSize: 100, color: M.sumi, lineHeight: 1 }}>あ</div>
          <div style={{ marginTop: 8, fontFamily: M.fontMono, fontSize: 13, color: M.ink500, letterSpacing: '.06em' }}>a · 3 Striche</div>
          <div style={{ marginTop: 16, display: 'flex', gap: 6, justifyContent: 'center' }}>
            {['い','う','え','お'].map((c, i) => (
              <div key={i} style={{ width: 40, height: 40, borderRadius: 8, background: M.washi, border: `1px solid ${M.ink200}`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: M.fontJp, fontSize: 20, color: M.ink500 }}>{c}</div>
            ))}
          </div>
        </div>
        <div style={{ marginTop: 18, display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: M.ink600, fontSize: 14 }}>
            <span style={{ color: M.matcha, fontWeight: 700 }}>✓</span>Keine Kreditkarte
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: M.ink600, fontSize: 14 }}>
            <span style={{ color: M.matcha, fontWeight: 700 }}>✓</span>30 Tage Geld zurück
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: M.ink600, fontSize: 14 }}>
            <span style={{ color: M.matcha, fontWeight: 700 }}>✓</span>Lifetime Zugriff zum Bundle-Preis
          </div>
        </div>
      </div>
      {/* sticky bottom CTA */}
      <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, padding: '12px 16px 28px', background: 'linear-gradient(180deg, rgba(250,247,242,0) 0%, rgba(250,247,242,.95) 30%)', display: 'flex', flexDirection: 'column', gap: 8 }}>
        <button style={{
          width: '100%', minHeight: 52, borderRadius: 12, border: 'none', cursor: 'pointer',
          background: `linear-gradient(180deg, ${M.shu}, ${M.shuDeep})`, color: '#fff',
          fontFamily: M.fontBody, fontWeight: 600, fontSize: 16,
          boxShadow: 'inset 0 1px 0 rgba(255,255,255,.15), 0 4px 14px rgba(184,74,0,.35), 0 0 0 1px rgba(184,74,0,.4)',
        }}>Kostenlos starten →</button>
        <button style={{ width: '100%', padding: '10px', background: 'transparent', border: 'none', color: M.kon, fontWeight: 500, fontSize: 14, cursor: 'pointer' }}>
          oder N5 Komplett · CHF 9.90
        </button>
      </div>
    </div>
  );
}

// ════════════════ C · VERTICAL MODULE PATH ════════════════
function PathMobile() {
  const mods = [
    { n: '01', title: 'Hiragana あ-い-う-え-お', sub: 'Vokale, Strichreihenfolge', icon: '📖', state: 'done', pct: 100 },
    { n: '02', title: 'か, さ, た, な-Reihen', sub: '20 Zeichen, gleicher Drill', icon: '✏️', state: 'next', pct: 0 },
    { n: '03', title: 'Katakana lesen', sub: 'コーヒー, テレビ, パン', icon: '🈂️', state: 'free', pct: 0 },
    { n: '04', title: 'N5 Kanji Set 1', sub: '20 Grundkanji', icon: '📝', state: 'locked', pct: 0 },
    { n: '05', title: 'です / は / の', sub: 'Die drei Säulen', icon: '🗣️', state: 'locked', pct: 0 },
  ];
  return (
    <div style={{ height: '100%', background: M.washi, display: 'flex', flexDirection: 'column', fontFamily: M.fontBody }}>
      {/* compact greeting */}
      <div style={{ padding: '10px 20px 16px', background: 'rgba(255,255,255,.85)', backdropFilter: 'blur(14px)', borderBottom: `1px solid ${M.ink200}` }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <div style={{ fontFamily: M.fontJpSerif, fontSize: 12, color: M.ink500 }}>こんにちは, claudio</div>
            <h1 style={{ fontFamily: M.fontDisp, fontWeight: 510, fontSize: 22, letterSpacing: '-.02em', color: M.kon, margin: '2px 0 0' }}>JLPT N5 · Lernpfad</h1>
          </div>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 5, padding: '6px 10px', background: 'rgba(235,97,1,.08)', borderRadius: 9999, fontWeight: 600, fontSize: 13, color: M.shu }}>🔥 14</div>
        </div>
      </div>
      {/* path */}
      <div style={{ flex: 1, overflow: 'auto', padding: '20px 20px 90px', position: 'relative' }}>
        {/* vertical line */}
        <div style={{ position: 'absolute', left: 35, top: 30, bottom: 100, width: 2, background: `repeating-linear-gradient(180deg, ${M.ink300} 0 6px, transparent 6px 12px)` }}/>
        {mods.map((m, i) => <PathNode key={m.n} {...m} last={i === mods.length - 1}/>)}
      </div>
      <BottomNav active="path" badge={11}/>
    </div>
  );
}

function PathNode({ n, title, sub, icon, state, pct, last }) {
  const styles = {
    done:   { node: M.matcha, ring: 'rgba(122,144,51,.18)', cardBg: 'rgba(122,144,51,.04)', cardBd: M.matcha, badge: '✓', badgeBg: M.matcha, badgeFg: '#fff' },
    next:   { node: M.shu, ring: 'rgba(235,97,1,.20)', cardBg: '#fff', cardBd: M.shu, badge: 'START', badgeBg: M.shu, badgeFg: '#fff' },
    free:   { node: M.kon, ring: 'rgba(31,42,68,.10)', cardBg: '#fff', cardBd: M.ink200, badge: 'GRATIS', badgeBg: 'rgba(122,144,51,.14)', badgeFg: M.matcha },
    locked: { node: M.ink300, ring: 'transparent', cardBg: '#fff', cardBd: M.ink200, badge: '🔒', badgeBg: M.ink100, badgeFg: M.ink500 },
  }[state];
  return (
    <div style={{ display: 'flex', gap: 14, marginBottom: 14, opacity: state === 'locked' ? .55 : 1, position: 'relative' }}>
      <div style={{ flexShrink: 0, width: 56, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <div style={{ width: 44, height: 44, borderRadius: 22, background: styles.node, color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, boxShadow: state === 'next' ? `0 0 0 6px ${styles.ring}` : 'none', position: 'relative', zIndex: 1 }}>{icon}</div>
        <span style={{ marginTop: 6, fontFamily: M.fontMono, fontSize: 9, color: M.ink500, letterSpacing: '.05em' }}>MOD {n}</span>
      </div>
      <div style={{ flex: 1, background: styles.cardBg, border: `1px solid ${styles.cardBd}`, borderRadius: 12, padding: '12px 14px', boxShadow: state === 'next' ? `0 0 0 3px rgba(235,97,1,.15)` : 'none' }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
          <div style={{ flex: 1 }}>
            <h3 style={{ fontFamily: M.fontDisp, fontWeight: 600, fontSize: 15, color: M.kon, margin: 0, letterSpacing: '-.01em' }}>{title}</h3>
            <p style={{ margin: '3px 0 0', fontSize: 12, color: M.ink600, lineHeight: 1.45 }}>{sub}</p>
          </div>
          <span style={{ fontFamily: M.fontDisp, fontSize: 9, fontWeight: 700, padding: '3px 8px', borderRadius: 9999, background: styles.badgeBg, color: styles.badgeFg, letterSpacing: '.05em', whiteSpace: 'nowrap' }}>{styles.badge}</span>
        </div>
        {pct > 0 && pct < 100 && (
          <div style={{ marginTop: 8, height: 4, background: M.ink100, borderRadius: 2, overflow: 'hidden' }}>
            <div style={{ width: `${pct}%`, height: '100%', background: state === 'done' ? M.matcha : M.kon }}/>
          </div>
        )}
        {state === 'next' && (
          <div style={{ marginTop: 10, fontSize: 12, color: M.shu, fontWeight: 600 }}>→ Tippen zum Beginnen</div>
        )}
      </div>
    </div>
  );
}

function Torii({ size = 28, color = '#1F2A44' }) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" fill="none" stroke={color} strokeWidth="3.6" strokeLinecap="round" strokeLinejoin="round">
      <path d="M 7 17 Q 32 12 57 17 L 56 21 Q 32 16 8 21 Z" fill={color} stroke={color} strokeWidth="1.5"/>
      <path d="M 11 27 Q 32 25 53 27" strokeWidth="3.4"/>
      <path d="M 14.5 22 Q 13.5 38 12.2 56" strokeWidth="4.2"/>
      <path d="M 49.5 22 Q 50.7 38 51.8 56" strokeWidth="4.2"/>
    </svg>
  );
}

Object.assign(window, { ReviewMobile, HeroMobile, PathMobile });
