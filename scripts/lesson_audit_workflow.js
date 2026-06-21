export const meta = {
  name: 'lektions-didaktik-audit',
  description: 'Didaktischer Audit der published N5-Lektionen: Fan-out je 2-3 Lektionen, adversariale Verifikation, Report',
  phases: [
    { title: 'Audit', detail: 'pro Gruppe (2-3 Lektionen) didaktische Fehler finden' },
    { title: 'Verify', detail: 'jede Findung skeptisch gegenprüfen' },
    { title: 'Synthese', detail: 'bestätigte Findungen zu priorisiertem Report verdichten' },
  ],
}

const A = typeof args === 'string' ? JSON.parse(args) : (args || {})
const DIR = A.audit_dir
const GROUPS = A.groups || []
const CURRICULUM = `${DIR}/_curriculum.md`
const INTRO = `${DIR}/_det_intro_index.txt`

const FINDINGS_SCHEMA = {
  type: 'object',
  required: ['findings'],
  additionalProperties: false,
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        required: ['lesson_id', 'severity', 'kategorie', 'konfidenz', 'fundstelle', 'problem', 'vorschlag', 'beleg'],
        additionalProperties: false,
        properties: {
          lesson_id: { type: 'integer' },
          severity: { type: 'string', enum: ['kritisch', 'mittel', 'gering'] },
          kategorie: { type: 'string', enum: ['faktischer_fehler', 'quiz_defekt', 'level_verstoss', 'vorwissen_sprung', 'progression', 'konsistenz', 'klarheit'] },
          konfidenz: { type: 'string', enum: ['hoch', 'mittel', 'niedrig'] },
          fundstelle: { type: 'string', description: 'Seite + order_index + exakter japanischer/deutscher Text der Fehlerstelle' },
          problem: { type: 'string', description: 'Was ist falsch — konkret' },
          vorschlag: { type: 'string', description: 'Konkrete Korrektur' },
          beleg: { type: 'string', description: 'Warum es falsch ist; bei faktischen Fehlern der korrekte Wert (Lesung/Übersetzung/Antwort)' },
        },
      },
    },
  },
}

const VERDICT_SCHEMA = {
  type: 'object',
  required: ['ist_echt', 'begruendung', 'vorschlag_korrekt'],
  additionalProperties: false,
  properties: {
    ist_echt: { type: 'boolean', description: 'true nur wenn klarer, verteidigbarer didaktischer Fehler' },
    begruendung: { type: 'string' },
    vorschlag_korrekt: { type: 'boolean', description: 'Ist die vorgeschlagene Korrektur selbst korrekt?' },
    korrigierte_severity: { type: 'string', enum: ['kritisch', 'mittel', 'gering'] },
  },
}

const CHECKLIST = `
KATEGORIEN (nur OFFENSICHTLICHE, verteidigbare Fehler flaggen — keine Stil-/Geschmacksfragen):
- faktischer_fehler: falsche Lesung (reading/Furigana/Romaji), falsche deutsche Übersetzung (meaning_de), falsche Beispielsatz-Übersetzung, falsche Onyomi/Kunyomi, falscher Kanji-Bedeutung.
- quiz_defekt: korrekte Antwort falsch als is_correct markiert; mehrere richtige Antworten möglich; Distraktor ist faktisch auch richtig; Frage prüft nicht den gelehrten Stoff; Frage/Optionen mehrdeutig; explanation widerspricht der korrekten Antwort.
- level_verstoss: Vokabel/Kanji/Grammatik klar ÜBER N5 (alle Lektionen sind N5). Konservativ — nur bei eindeutig N4+.
- vorwissen_sprung: Kanji/Grammatik wird benutzt, bevor es laut Einführungsindex/Curriculum eingeführt wurde. NUR mit Beleg aus dem Index; sonst NICHT flaggen. Konfidenz höchstens "mittel".
- progression: unlogische Reihenfolge, kognitive Überladung (zu viel Neues auf einer Seite), fehlende Beispiele vor Quiz.
- konsistenz: Widerspruch INNERHALB deiner Gruppe (z.B. dasselbe Wort zweimal anders erklärt).
- klarheit: deutsche Erklärung sachlich falsch/irreführend, grober Deutsch-Sprachfehler, Anweisung unverständlich.

REGELN:
- "offensichtlich" heisst: ein/e Japanisch-Lehrer/in würde es ohne Zögern als Fehler bestätigen. Im Zweifel NICHT flaggen.
- Quiz-Antwort-Fehler und faktische Lesungs-/Übersetzungsfehler haben höchste Priorität — prüfe diese besonders sorgfältig, indem du die korrekte Antwort selbst herleitest.
- erlaubte Quiz-Typen: multiple_choice, true_false, matching. fill_blank/fill_in_the_blank ist verboten -> wäre selbst ein quiz_defekt.
- fundstelle IMMER mit page_number + order_index + exaktem Text, damit die Stelle auffindbar ist.
- Lieber 5 wasserdichte Findungen als 30 vage.
`

function auditPrompt(g) {
  const files = g.lesson_ids.map((id) => `${DIR}/lesson_${id}.json`)
  return `Du bist erfahrene/r JLPT-N5-Didaktiker/in mit Japanisch auf Muttersprachler-Niveau und prüfst Lektionen der Lernplattform japanese-learning.ch auf OFFENSICHTLICHE didaktische Fehler.

ARBEITSSCHRITTE:
1. Lies diese Lektions-Dateien (voll aufgelöstes JSON: Texte, Vokabeln mit Lesung/Romaji/meaning_de/Beispielsatz, Kanji mit On/Kun, Grammatik-Erklärungen, Quiz mit is_correct-Markierung):
${files.map((f) => `   - ${f}`).join('\n')}
2. Lies zur Einordnung: ${CURRICULUM} (Lernreihenfolge aller 58 N5-Lektionen) und ${INTRO} (wann Kanji/Grammatik zuerst eingeführt werden).

KONTEXT: Diese Gruppe = Modul "${g.module}", Lektionen ${g.lesson_ids.join(', ')}. ALLE Lektionen der Plattform sind JLPT N5. Du siehst nur die Volltexte DEINER Gruppe — für Vorwissen-Sprünge stütze dich ausschliesslich auf den Einführungsindex, spekuliere nicht über Inhalte anderer Module.

${CHECKLIST}

Gib ALLE gefundenen klaren Fehler im Schema zurück (leeres findings-Array, wenn nichts Offensichtliches). Jede Findung mit exakter fundstelle und — bei faktischen/Quiz-Fehlern — dem korrekten Wert im Feld beleg.`
}

function verifyPrompt(f) {
  return `Du bist ein/e strenge/r, SKEPTISCHE/r Gegenprüfer/in (Japanisch Muttersprachler-Niveau, JLPT-Experte/in). Eine Audit-Findung soll widerlegt oder bestätigt werden. Standardhaltung: im Zweifel ist_echt=false.

LIES ZUERST die betroffene Lektion neu und leite die Wahrheit UNABHÄNGIG her: ${DIR}/lesson_${f.lesson_id}.json
(Bei vorwissen_sprung/progression/konsistenz auch ${CURRICULUM} und ${INTRO} heranziehen.)

ZU PRÜFENDE FINDUNG (Lektion ${f.lesson_id}):
- Kategorie: ${f.kategorie} | Severity: ${f.severity} | Konfidenz: ${f.konfidenz}
- Fundstelle: ${f.fundstelle}
- Problem: ${f.problem}
- Vorschlag: ${f.vorschlag}
- Beleg des Auditors: ${f.beleg}

PRÜFE:
1. Existiert die Fundstelle wirklich so in der Lektion? Wenn nicht -> ist_echt=false.
2. Ist es ein KLARER, verteidigbarer didaktischer Fehler (würde ein/e Japanisch-Lehrer/in es ohne Zögern bestätigen)? Bei faktischen/Quiz-Findungen: leite die korrekte Lesung/Übersetzung/Antwort selbst her und vergleiche.
3. Ist der vorgeschlagene Fix selbst korrekt (vorschlag_korrekt)?
4. Bei strukturellen Kategorien (vorwissen_sprung/progression): ohne harten Beleg aus dem Index -> ist_echt=false.

Gib dein Urteil im Schema zurück. Knapp und begründet.`
}

phase('Audit')
log(`Starte Audit über ${GROUPS.length} Gruppen (je 2-3 Lektionen)`)

const perGroup = await pipeline(
  GROUPS,
  (g) => agent(auditPrompt(g), { label: `audit:${g.group_id}`, phase: 'Audit', schema: FINDINGS_SCHEMA }),
  (review, g) => {
    const findings = (review && review.findings) || []
    if (!findings.length) return []
    return parallel(
      findings.map((f) => () =>
        agent(verifyPrompt(f), { label: `verify:L${f.lesson_id}:${f.kategorie}`, phase: 'Verify', schema: VERDICT_SCHEMA, effort: 'high' })
          .then((v) => ({ ...f, group_id: g.group_id, module: g.module, verdict: v }))
      )
    )
  }
)

const all = perGroup.flat().filter(Boolean)
const confirmed = all.filter((f) => f.verdict && f.verdict.ist_echt)
log(`Roh-Findungen: ${all.length} | bestätigt: ${confirmed.length}`)

phase('Synthese')
const summary = await agent(
  `Du bist Lead-Didaktiker/in. Hier sind die ADVERSARIAL BESTÄTIGTEN didaktischen Findungen aus dem N5-Lektions-Audit (JSON). Schreibe einen knappen, priorisierten Management-Report auf Deutsch (Markdown).

BESTÄTIGTE FINDUNGEN:
${JSON.stringify(confirmed, null, 2)}

ANFORDERUNGEN AN DEN REPORT:
- Beginne mit einer Executive Summary (3-6 Sätze): wie viele Fehler, welche Schwerpunkte, wie ernst ist der Gesamtzustand.
- Dann Abschnitte nach Severity (Kritisch -> Mittel -> Gering). Innerhalb: Quiz-Defekte und faktische Fehler ZUERST.
- WIEDERKEHRENDE/systematische Muster zu EINEM Eintrag zusammenfassen ("betrifft Lektionen X, Y, Z") statt zu wiederholen.
- Jeder Eintrag: Lektion(en), Fundstelle, was ist falsch, konkrete Korrektur.
- Am Ende: kurze Handlungsempfehlung (welche 3-5 Dinge zuerst fixen).
- Sachlich, keine Lobhudelei. Wenn der Gesamtzustand gut ist, sag das klar.

Gib NUR den Markdown-Report zurück.`,
  { label: 'synthese', phase: 'Synthese', effort: 'high' }
)

return {
  stats: { gruppen: GROUPS.length, roh_findungen: all.length, bestaetigt: confirmed.length },
  confirmed,
  summary,
}
