// Wert-Diff-Werkzeug fuer den :root-Token-Merge (phase a, wert-erhaltend).
// Extrahiert die effektiven (last-wins) Werte aller Custom-Properties aus den
// PLAIN ":root {" -Bloecken von custom.css (NICHT [data-theme=dark]).
// Aufruf: node scripts/_tokendiff.js  -> druckt effektive Map + Duplikat-Report.
const fs = require('fs');
const css = fs.readFileSync('app/static/css/custom.css', 'utf8');

// Alle Bloecke finden, deren Selektor exakt ":root" ist (optional html-Prefix),
// und KEIN [data-theme ... enthaelt.
const blocks = [];
const re = /:root([^{]*)\{([^}]*)\}/g;
let m;
while ((m = re.exec(css)) !== null) {
  const selTail = m[1];          // alles zwischen ":root" und "{"
  const body = m[2];
  // Nur reine Light-:root-Bloecke (selTail = whitespace). Dark-Varianten
  // (:root[data-theme=...]) oder Selektor-Listen ausschliessen.
  if (selTail.trim() !== '') continue;
  const startLine = css.slice(0, m.index).split('\n').length;
  blocks.push({ startLine, body });
}

// Pro Block die --key: value; Deklarationen extrahieren (Reihenfolge erhalten)
function decls(body) {
  const out = [];
  const dre = /(--[A-Za-z0-9-]+)\s*:\s*([^;]+);/g;
  let d;
  while ((d = dre.exec(body)) !== null) out.push([d[1], d[2].trim().replace(/\s+/g, ' ')]);
  return out;
}

const perBlock = blocks.map(b => ({ startLine: b.startLine, decls: decls(b.body) }));
const allKeysOrder = [];
const effective = new Map();   // key -> value (last-wins ueber alle :root-Bloecke)
const seen = new Map();        // key -> [ {line,value} ... ] fuer Duplikat-Report
for (const blk of perBlock) {
  for (const [k, v] of blk.decls) {
    if (!effective.has(k)) allKeysOrder.push(k);
    effective.set(k, v);
    if (!seen.has(k)) seen.set(k, []);
    seen.get(k).push({ block: blk.startLine, value: v });
  }
}

// Duplikate (Key in >1 :root-Block, ODER mehrfach mit abweichendem Wert)
const dups = [];
for (const [k, occ] of seen) {
  const blocksWith = new Set(occ.map(o => o.block));
  if (occ.length > 1) {
    const values = [...new Set(occ.map(o => o.value))];
    dups.push({ key: k, occ, conflicting: values.length > 1, blocks: [...blocksWith] });
  }
}

console.log('PLAIN :root-Bloecke gefunden:', blocks.map(b => 'Z.' + b.startLine).join(', '));
console.log('Distinkte Tokens (effektiv):', effective.size);
console.log('\n=== DUPLIKAT-KEYS (in >1 :root-Block oder mehrfach) ===');
if (!dups.length) console.log('  KEINE — die Bloecke sind disjunkt (Merge = reine Konkatenation, trivial wert-erhaltend).');
for (const d of dups) {
  console.log(`  ${d.key} ${d.conflicting ? '⚠ KONFLIKT' : '(gleich)'} : ` +
    d.occ.map(o => `[Z.${o.block}] ${o.value}`).join('  |  '));
}

// Effektive Map als stabiler Fingerprint (sortiert) — Baseline-Datei schreiben.
const sorted = [...effective.entries()].sort((a, b) => a[0].localeCompare(b[0]));
const fingerprint = sorted.map(([k, v]) => `${k}: ${v}`).join('\n');
fs.writeFileSync('scripts/_tokenmap.txt', fingerprint + '\n');
console.log('\nFingerprint geschrieben: scripts/_tokenmap.txt (' + sorted.length + ' Tokens)');
