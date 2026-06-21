export const meta = {
  name: 'audit-handcase-authoring',
  description: 'Autort die ~14 needs_review-Hand-Fälle zu exakten DB-Apply-Specs (read-only Recherche, kein Write)',
  phases: [{ title: 'Authoring', detail: 'pro Hand-Fall exakte Zeile holen + vollen Fix autoren' }],
}

const A = typeof args === 'string' ? JSON.parse(args) : (args || {})
const DIR = A.audit_dir
const CHUNK = A.chunk_size || 5

const SCHEMA = {
  type: 'object',
  required: ['finding', 'applicable', 'specs', 'skip_reason'],
  additionalProperties: false,
  properties: {
    finding: { type: 'string' },
    applicable: { type: 'boolean', description: 'false, wenn der Fix keine Inhalts-Feld-Änderung ist (z.B. Curriculum-Reihenfolge) oder bereits behoben' },
    skip_reason: { type: 'string' },
    specs: {
      type: 'array',
      description: 'eine Spec je betroffener DB-Zeile (mehrere bei Mehr-Ort-Fixes)',
      items: {
        type: 'object',
        required: ['table', 'pk', 'column', 'current_value', 'new_value', 'note'],
        additionalProperties: false,
        properties: {
          table: { type: 'string', enum: ['lesson_content', 'grammar', 'vocabulary', 'quiz_question', 'quiz_option', 'lesson'] },
          pk: { type: 'integer', description: 'id der zu ändernden Zeile' },
          column: { type: 'string', description: 'EINE Spalte (content_text/explanation/example_sentences/...)' },
          current_value: { type: 'string', description: 'der VOLLSTÄNDIGE aktuelle Feldwert, EXAKT wie aus der DB gelesen (Voll-Ersatz)' },
          new_value: { type: 'string', description: 'der vollständige korrigierte Feldwert (nur die beanstandete Stelle geändert, Rest unverändert; bei JSON-Feldern struktur-erhaltend re-serialisiert)' },
          note: { type: 'string' },
        },
      },
    },
  },
}

function prompt(ref) {
  return `Du bist Japanisch-Didaktiker/in (Muttersprachler-Niveau) UND vorsichtige/r DB-Operator/in. Übersetze EINEN Audit-Hand-Fall in praezise DB-Apply-Specs — NICHTS schreiben (nur SELECT).

LIES den Fall: Datei ${DIR}/hand_cases.json, Index ${ref.idx}. Er enthaelt finding, lesson_id, problem, vorschlag (bzw. satz_jp/alternative) und NOTES mit dem konkreten DB-Locator (lesson_content.id / grammar.id / kanji.id, page/order, zitierter Text).

DB (nur SELECT!): ssh hp-ubuntu "sudo docker exec postgres_db psql -U app_user -d japanese_learning -t -A -c \\"<QUERY>\\""

VORGEHEN:
1. Hole den VOLLSTÄNDIGEN aktuellen Feldwert der in NOTES genannten Zeile(n): z.B. SELECT content_text FROM lesson_content WHERE id=<id>; oder SELECT explanation FROM grammar WHERE id=<id>; oder SELECT example_sentences FROM grammar WHERE id=<id>. Bei dialog_slideshow ist content_text ein JSON-String (Liste von Slides mit jp/romaji/de/...). Bei Mehr-Ort-Fixes (Prosa + Lese-Transkript, oder zwei Seiten) ALLE betroffenen Zeilen holen.
2. AUTORE den korrigierten VOLLEN Feldwert (du bist Claude; KEIN externer LLM): nur die im Problem beanstandete Stelle aendern, ALLES andere zeichengenau erhalten. N5-konform, natuerlich. Bei JSON-Slides: JSON parsen, betroffenen Slide (jp + romaji + de konsistent) korrigieren, struktur-erhaltend re-serialisieren (gleiche Keys/Reihenfolge, ensure_ascii wie im Original — die DB speichert i.d.R. echte japanische Zeichen, nicht \\uXXXX). Wenn ein Lese-Transkript (content_type=text) denselben Satz dupliziert, dieselbe Korrektur dort als zweite Spec.
3. Gib je betroffener Zeile EINE Spec zurueck: table, pk, column, current_value (= EXAKT der volle DB-Wert), new_value (= voller neuer Wert). Der nachgelagerte Applier ersetzt nur, wenn current_value zeichengenau dem DB-Stand entspricht — also MUSS current_value exakt stimmen (inkl. Whitespace/Zeilenumbrueche).

WICHTIG:
- Wenn der Fix KEINE Feld-Änderung ist (z.B. factual[37]: Lektions-Reihenfolge/Prerequisites) -> applicable=false, specs=[], skip_reason erklaeren.
- Wenn der beanstandete Text NICHT mehr in der DB steht (bereits behoben) -> applicable=false, skip_reason="bereits behoben".
- Minimal-invasiv: keine Stil-Politur ueber den Befund hinaus.`
}

phase('Authoring')
const items = Array.from({ length: A.count }, (_, i) => ({ idx: i }))
log(`Authoring ${items.length} Hand-Fälle in Chunks à ${CHUNK}`)
const results = []
for (let i = 0; i < items.length; i += CHUNK) {
  const chunk = items.slice(i, i + CHUNK)
  const part = await parallel(chunk.map((r) => () =>
    agent(prompt(r), { label: `hand:${r.idx}`, phase: 'Authoring', schema: SCHEMA })))
  results.push(...part.filter(Boolean))
  log(`  ${Math.min(i + CHUNK, items.length)}/${items.length}`)
}

const applySpecs = []
for (const r of results) {
  if (r.applicable && r.specs) {
    for (const s of r.specs) applySpecs.push({ ...s, finding: r.finding, apply: true, verified: true })
  }
}
return {
  stats: { faelle: results.length, anwendbar: results.filter((r) => r.applicable).length, specs: applySpecs.length,
           uebersprungen: results.filter((r) => !r.applicable).map((r) => `${r.finding}: ${r.skip_reason}`) },
  applySpecs,
}
