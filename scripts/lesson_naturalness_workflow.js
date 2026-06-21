export const meta = {
  name: 'lektions-natuerlichkeit-research',
  description: 'Natürlichkeits-Audit: pro Thema Web-Recherche + Muttersprachler-Urteil, ob Beispielsätze "unmenschlich"/steif sind',
  phases: [
    { title: 'Research', detail: 'pro Gruppe Web-Recherche + Bewertung der Beispielsätze' },
    { title: 'Verify', detail: 'unnatürliche Sätze von striktem Muttersprachler gegenprüfen' },
  ],
}

const A = typeof args === 'string' ? JSON.parse(args) : (args || {})
const DIR = A.audit_dir
const GROUPS = A.groups || []
const CHUNK = A.chunk_size || 4

const NAT_SCHEMA = {
  type: 'object', required: ['findings'], additionalProperties: false,
  properties: { findings: { type: 'array', items: {
    type: 'object',
    required: ['lesson_id', 'satz_jp', 'kontext', 'einstufung', 'problem', 'natuerliche_alternative', 'schwere'],
    additionalProperties: false,
    properties: {
      lesson_id: { type: 'integer' },
      satz_jp: { type: 'string', description: 'der exakte japanische Satz aus der Lektion' },
      kontext: { type: 'string', description: 'wo (vocab/grammar/text), page_number + order_index' },
      einstufung: { type: 'string', enum: ['unnatuerlich', 'steif'], description: 'unnatuerlich = kein Muttersprachler sagt das; steif = grammatisch ok aber hölzern/lehrbuchhaft' },
      problem: { type: 'string', description: 'was ein Muttersprachler daran merkt — konkret' },
      natuerliche_alternative: { type: 'string', description: 'natürlicher Umformulierungs-Vorschlag, MUSS N5-Niveau bleiben (keine fortgeschrittene Grammatik/Vokabel)' },
      schwere: { type: 'string', enum: ['hoch', 'mittel', 'gering'] },
    },
  } } },
}

const NAT_VERDICT_SCHEMA = {
  type: 'object', required: ['wirklich_unnatuerlich', 'begruendung', 'alternative_ist_n5_und_natuerlich'], additionalProperties: false,
  properties: {
    wirklich_unnatuerlich: { type: 'boolean', description: 'true nur, wenn ein Muttersprachler den Satz klar als unnatürlich/hölzern empfindet' },
    begruendung: { type: 'string' },
    alternative_ist_n5_und_natuerlich: { type: 'boolean', description: 'Ist die vorgeschlagene Alternative natürlich UND noch N5-Niveau?' },
    bessere_alternative: { type: 'string', description: 'optional: bessere Alternative, falls der Vorschlag schwach war' },
  },
}

function researchPrompt(g) {
  const files = g.lesson_ids.map((id) => `${DIR}/lesson_${id}.json`)
  return `Du bist japanische/r MUTTERSPRACHLER/IN und erfahrene/r Japanisch-Lehrer/in. Du prüfst Beispielsätze einer N5-Lernplattform auf NATÜRLICHKEIT — ob sie klingen wie echtes, von Menschen gesprochenes Japanisch, oder "unmenschlich" (steifes, hölzernes, übersetztes Lehrbuch-Japanisch, das kein Muttersprachler so sagen würde).

ARBEITSSCHRITTE:
1. Lies die Lektions-Dateien und sammle ALLE japanischen Beispielsätze (aus vocabulary.example_sentence_japanese, grammar.example_sentences, sowie japanische Sätze in content_text/Texten):
${files.map((f) => `   - ${f}`).join('\n')}
2. RECHERCHIERE im Web zum Thema "${g.module}" (Lektionen: ${g.lesson_ids.join(', ')}): Nutze WebSearch (1-3 gezielte Suchen, z.B. nach natürlichen japanischen Beispielsätzen/Kollokationen zum Thema, oder ob konkrete Formulierungen real gebräuchlich sind). Ziel: echtes Sprachgefühl als Vergleichsmassstab/Inspiration, nicht Lehrbuch-Klischees.
3. Beurteile JEDEN Beispielsatz: natürlich / steif / unnatürlich. Flagge NUR "steif" und "unnatuerlich".

WICHTIGE REGELN:
- N5-Sätze sind notwendigerweise EINFACH. Einfachheit ist KEIN Mangel. Flagge NICHT, dass ein Satz simpel ist.
- Flagge nur, was ein Muttersprachler wirklich als hölzern/künstlich empfindet: z.B. übertrieben förmliche/roboterhafte Konstruktionen, unnötige Pronomen (わたしは… wo es niemand sagt), unnatürliche Wortstellung, Wort-für-Wort-Übersetzung aus dem Deutschen, Sätze über Inhalte, die niemand real äussert, unidiomatische Kollokationen.
- Deine Alternative MUSS auf N5-Niveau bleiben (nur Grammatik/Vokabeln, die ein N5-Lerner kennt). Natürlich ≠ schwieriger.
- Im Zweifel (Satz ist akzeptabel) NICHT flaggen. Lieber wenige echte Treffer.
- satz_jp wörtlich zitieren; kontext mit page_number + order_index.

Gib alle steifen/unnatürlichen Sätze im Schema zurück (leeres findings, wenn alles natürlich ist oder die Lektion kaum echte Sätze enthält, z.B. reine Kana-Zeichen-Lektion).`
}

function verifyPrompt(f) {
  return `Du bist japanische/r MUTTERSPRACHLER/IN mit hohem Sprachgefühl und STRENGEM Massstab. Standardhaltung: ein Satz ist natürlich genug, solange ein Muttersprachler ihn ohne Stirnrunzeln akzeptieren würde.

ZU PRÜFENDER SATZ (Lektion ${f.lesson_id}, ${f.kontext}):
  「${f.satz_jp}」
Behauptung des Auditors: einstufung=${f.einstufung}, schwere=${f.schwere}
  Problem: ${f.problem}
  Vorgeschlagene Alternative: ${f.natuerliche_alternative}

(Optional zum Abgleich die Lektion: ${DIR}/lesson_${f.lesson_id}.json)

PRÜFE:
1. Ist der Originalsatz für einen Muttersprachler WIRKLICH unnatürlich/hölzern (nicht nur simpel)? Wenn er akzeptabel ist -> wirklich_unnatuerlich=false.
2. Ist die vorgeschlagene Alternative natürlich UND bleibt sie strikt auf N5-Niveau (keine fortgeschrittene Grammatik/Vokabel)? Wenn die Alternative schlechter/zu schwer ist, gib eine bessere in bessere_alternative an.
3. Sei streng gegenüber Fehlalarmen: Lehrbuch-typische, aber akzeptable Sätze sind KEINE Treffer.

Antworte knapp im Schema.`
}

const researchStage = (g) => agent(researchPrompt(g), { label: `research:${g.group_id}`, phase: 'Research', schema: NAT_SCHEMA, agentType: 'general-purpose' })
const verifyStage = (review, g) => {
  const findings = (review && review.findings) || []
  if (!findings.length) return []
  return parallel(findings.map((f) => () =>
    agent(verifyPrompt(f), { label: `verify:L${f.lesson_id}`, phase: 'Verify', schema: NAT_VERDICT_SCHEMA, effort: 'high' })
      .then((v) => ({ ...f, group_id: g.group_id, module: g.module, verdict: v }))))
}

phase('Research')
log(`Natürlichkeits-Research: ${GROUPS.length} Gruppen in Chunks à ${CHUNK} (mit WebSearch)`)
const perGroup = []
for (let i = 0; i < GROUPS.length; i += CHUNK) {
  const chunk = GROUPS.slice(i, i + CHUNK)
  log(`Chunk ${Math.floor(i / CHUNK) + 1}: ${chunk.map((g) => g.group_id).join(', ')}`)
  const part = await pipeline(chunk, researchStage, verifyStage)
  perGroup.push(...part)
}

const all = perGroup.flat().filter(Boolean)
const confirmed = all.filter((f) => f.verdict && f.verdict.wirklich_unnatuerlich)
log(`Natürlichkeit fertig — markiert: ${all.length} | bestätigt unnatürlich: ${confirmed.length}`)

return {
  stats: { gruppen: GROUPS.length, markiert: all.length, bestaetigt: confirmed.length },
  confirmed,
}
