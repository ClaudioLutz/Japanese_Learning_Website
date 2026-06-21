export const meta = {
  name: 'audit-korrektur-mapping',
  description: 'DRY-RUN: mappt jede Audit-Findung auf eine verifizierte DB-Aenderung (read-only, keine Mutation)',
  phases: [{ title: 'Mapping', detail: 'pro Findung Zeile lokalisieren + Ist-Wert verifizieren + Korrektur autoren' }],
}

const A = typeof args === 'string' ? JSON.parse(args) : (args || {})
const DIR = A.audit_dir
const FACT = `${DIR}/confirmed_factual.json`
const NAT = `${DIR}/confirmed_naturalness.json`
const CHUNK = A.chunk_size || 5

const SPEC_SCHEMA = {
  type: 'object',
  required: ['table', 'change_type', 'current_value', 'new_value', 'verified', 'confidence', 'apply', 'notes'],
  additionalProperties: false,
  properties: {
    table: { type: 'string', enum: ['vocabulary', 'quiz_question', 'quiz_option', 'kanji', 'grammar', 'lesson_content', 'lesson', 'NONE'] },
    change_type: { type: 'string', description: 'kurz: example_sentence | meaning_de | quiz_is_correct | quiz_distraktor | quiz_text | kanji_jlpt_level | prose | grammar_example | other' },
    pk: { type: 'string', description: 'Primaerschluessel-Wert(e) der zu aendernden Zeile(n), oder leer wenn nicht lokalisierbar' },
    column: { type: 'string', description: 'zu aendernde Spalte(n)' },
    locator_sql: { type: 'string', description: 'die SELECT-Query, mit der du die Zeile lokalisiert + den Ist-Wert geholt hast' },
    current_value: { type: 'string', description: 'aktueller DB-Wert (exakt, wie aus der DB gelesen)' },
    new_value: { type: 'string', description: 'korrigierter Wert (Claude-verfasst, N5-sicher). Bei mehreren Spalten als JSON-Objekt.' },
    verified: { type: 'boolean', description: 'true nur wenn current_value mit der zitierten Fundstelle/dem Satz uebereinstimmt' },
    confidence: { type: 'string', enum: ['hoch', 'mittel', 'niedrig'] },
    apply: { type: 'boolean', description: 'true NUR fuer verifizierte, klar-mechanische Einzelfeld-Aenderungen ohne Ermessensspielraum' },
    notes: { type: 'string', description: 'alles fuer menschliche Sichtung: strittig, mehrstufig, mehrdeutig, Folgewirkung auf andere Felder' },
  },
}

function prompt(ref) {
  return `Du bist erfahrene/r Japanisch-Didaktiker/in UND vorsichtige/r DB-Operator/in. Du sollst EINE bestaetigte Audit-Findung in eine PRAEZISE, VERIFIZIERTE Datenbank-Aenderung uebersetzen — aber NICHTS schreiben (read-only Analyse).

LIES die Findung: Datei ${ref.file}, JSON-Array, Index ${ref.idx}. (Bei den naturalness-Findungen ist 'satz_jp' der aktuelle Satz und 'natuerliche_alternative' bzw. verdict.bessere_alternative der neue.)

DB-ZUGRIFF (nur SELECT!): ssh hp-ubuntu "sudo docker exec postgres_db psql -U app_user -d japanese_learning -t -A -c \\"<QUERY>\\""
Schema-Hinweise:
- Karten-Beispielsaetze: Tabelle vocabulary (Spalten word, reading, romaji, meaning, meaning_de, example_sentence_japanese, example_sentence_english). example_sentence_english hat das Format "Romaji — Deutsch".
- Lektions-Zuordnung: lesson_content (lesson_id, page_number, order_index, content_type, content_id). content_id zeigt bei content_type='vocabulary'|'kanji'|'grammar' auf die jeweilige Tabelle.
- Quiz: quiz_question (lesson_content_id, question_text, explanation, order_index), quiz_option (question_id, option_text, is_correct, feedback).
- Kanji: kanji (character, meaning, onyomi, kunyomi, jlpt_level). Grammar: grammar (title, explanation, example_sentences, ...). Prosa: lesson_content.content_text.

VORGEHEN:
1. Lokalisiere die exakte Zeile(n) ueber lesson_id + Hinweise aus 'fundstelle' (page_number/order_index/zitierter Text). Fuer vocabulary-Saetze: finde die Zeile, deren example_sentence_japanese dem zitierten Satz entspricht (ueber lesson_content JOIN vocabulary, oder direkt). WICHTIG: Vokabeln sind GETEILT — gib pk = vocabulary.id und beachte, dass die Korrektur global wirkt.
2. VERIFIZIERE: Stimmt der aktuelle DB-Wert mit der zitierten Fundstelle/dem Satz ueberein? Wenn NICHT (oder Zeile nicht eindeutig auffindbar) -> verified=false, apply=false, table=NONE, in notes erklaeren.
3. AUTORE den korrigierten Wert selbst (du bist Claude; KEIN externer LLM): N5-konform, natuerlich. Respektiere verdict.vorschlag_korrekt=false -> dann ist der Auditor-Vorschlag FALSCH; nutze die Korrektur aus verdict.begruendung, NICHT den 'vorschlag'. Bei example_sentence_japanese-Aenderung: passe auch example_sentence_english (Romaji — Deutsch) konsistent an und gib new_value als JSON {"example_sentence_japanese": "...", "example_sentence_english": "..."} mit column "example_sentence_japanese,example_sentence_english".
4. apply=true NUR wenn: verified=true UND hohe Konfidenz UND klar-mechanisch (eindeutiger Wert, kein Ermessen). Quiz-Logik-Umbauten, Prosa-Umschreibungen, mehrdeutige oder strittige Faelle -> apply=false + notes.

Gib GENAU eine Spec im Schema zurueck.`
}

phase('Mapping')
const factCount = A.factual_count
const natCount = A.naturalness_count
const refs = []
for (let i = 0; i < factCount; i++) refs.push({ file: FACT, idx: i, kind: 'factual' })
for (let i = 0; i < natCount; i++) refs.push({ file: NAT, idx: i, kind: 'naturalness' })
log(`Mapping von ${refs.length} Findungen in Chunks à ${CHUNK} (read-only)`)

const specs = []
for (let i = 0; i < refs.length; i += CHUNK) {
  const chunk = refs.slice(i, i + CHUNK)
  const part = await parallel(chunk.map((r) => () =>
    agent(prompt(r), { label: `map:${r.kind}[${r.idx}]`, phase: 'Mapping', schema: SPEC_SCHEMA })
      .then((s) => ({ ...s, finding: `${r.kind}[${r.idx}]`, kind: r.kind }))))
  specs.push(...part.filter(Boolean))
  log(`  ${Math.min(i + CHUNK, refs.length)}/${refs.length} gemappt`)
}

const applyable = specs.filter((s) => s.apply && s.verified)
return {
  stats: {
    total: specs.length,
    verified: specs.filter((s) => s.verified).length,
    apply: applyable.length,
    needs_review: specs.filter((s) => !s.apply).length,
  },
  specs,
}
