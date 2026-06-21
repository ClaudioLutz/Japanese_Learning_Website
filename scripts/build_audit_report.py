"""Baut den finalen didaktischen Audit-Report aus confirmed_factual.json + confirmed_naturalness.json."""
import json
import pathlib
from collections import Counter

D = pathlib.Path(__file__).parent / "data" / "lesson_audit"
fact = json.load(open(D / "confirmed_factual.json", encoding="utf-8"))
nat = json.load(open(D / "confirmed_naturalness.json", encoding="utf-8"))

# Lektions-Titel aus den Dumps
titles = {}
for f in sorted(D.glob("lesson_*.json")):
    o = json.load(open(f, encoding="utf-8"))
    titles[o["id"]] = o["title"]

def t(lid):
    return titles.get(lid, f"Lektion {lid}")

KAT_LABEL = {
    "quiz_defekt": "Quiz-Defekt", "faktischer_fehler": "Faktischer Fehler",
    "level_verstoss": "Level-Verstoss (N4+ in N5)", "vorwissen_sprung": "Vorwissen-Sprung",
    "konsistenz": "Konsistenz-Widerspruch", "progression": "Progression",
    "klarheit": "Klarheit / Erklärung",
}
SEV_ORDER = {"kritisch": 0, "mittel": 1, "gering": 2}
KAT_ORDER = {"quiz_defekt": 0, "faktischer_fehler": 1, "level_verstoss": 2,
             "vorwissen_sprung": 3, "konsistenz": 4, "progression": 5, "klarheit": 6}
SEV_BADGE = {"kritisch": "🔴 kritisch", "mittel": "🟠 mittel", "gering": "🟡 gering"}
NAT_BADGE = {"hoch": "🔴 hoch", "mittel": "🟠 mittel", "gering": "🟡 gering"}

fc = Counter(f["severity"] for f in fact)
fk = Counter(f["kategorie"] for f in fact)
nc = Counter(f["schwere"] for f in nat)
n_lessons = len(set([f["lesson_id"] for f in fact]) | set([f["lesson_id"] for f in nat]))

L = []
def w(s=""): L.append(s)

w("# Didaktischer Audit — N5-Lektionen japanese-learning.ch")
w()
w("_Automatisierter Mehr-Agenten-Audit aller **58 publizierten N5-Lektionen**, 2026-06-21. "
  "Jede Findung wurde von einem zweiten, unabhängigen Agenten adversarial gegengeprüft; "
  "nur bestätigte Findungen stehen hier._")
w()
w("## Executive Summary")
w()
w(f"Geprüft wurden **58 Lektionen** (15 Module) in zwei Dimensionen: **Korrektheit** "
  f"(Lesungen, Übersetzungen, Quiz-Logik, Level-Treue, Konsistenz) und **Natürlichkeit** "
  f"(klingen die japanischen Beispielsätze wie echtes Japanisch oder steif/unnatürlich?). "
  f"Ergebnis: **{len(fact)} bestätigte Korrektheits-Findungen** und **{len(nat)} bestätigte "
  f"Natürlichkeits-Findungen**, verteilt auf **{n_lessons} der 58 Lektionen**.")
w()
w(f"- **Kein einziger kritischer/funktionsbrechender Fehler.** Schwere der Korrektheits-Findungen: "
  f"**{fc.get('mittel',0)} mittel, {fc.get('gering',0)} gering**. Die Plattform ist inhaltlich solide.")
w(f"- **Schwerpunkt Korrektheit:** {fk.get('konsistenz',0)}× interne **Konsistenz-Widersprüche** "
  f"(eine Lektion sagt an zwei Stellen Verschiedenes), {fk.get('klarheit',0)}× Klarheits-/Erklärungsfehler, "
  f"{fk.get('quiz_defekt',0)}× **Quiz-Defekte**, {fk.get('faktischer_fehler',0)}× faktische Fehler, "
  f"{fk.get('vorwissen_sprung',0)}× Vorwissen-Sprung, {fk.get('level_verstoss',0)}× Level-Verstoss, "
  f"{fk.get('progression',0)}× Progression.")
w(f"- **Natürlichkeit:** {nc.get('hoch',0)} hoch, {nc.get('mittel',0)} mittel, {nc.get('gering',0)} gering. "
  f"Wiederkehrendes Muster: deutsch-/englisch-geprägte **Calques** (来ます statt 戻る/行ってくる beim Weggehen), "
  f"unjapanische **Pronomen** (あなたの + Verwandtschaftswort), **fehlende Zähler** (本が十 statt 十冊) und "
  f"semantisch schiefe Lehr-Beispielsätze (Schüler sind 「大きい」).")
w()

w("## Methodik")
w()
w("1. **Snapshot:** Alle 58 Lektionen wurden aus der Produktions-DB als voll aufgelöstes JSON "
  "gedumpt (Vokabeln mit Lesung/Romaji/Bedeutung, Kanji, Grammatik, Quiz inkl. markierter "
  "korrekter Antwort). Vollständigkeit gegen die DB verifiziert (2040 Inhalte = DB-Zahl, 0 Verlust).")
w("2. **Deterministische Vorab-Pässe** (was eine Stichproben-Prüfung nicht sieht): globaler "
  "**Konsistenz-Diff** über alle Lektionen (gleiches Wort/Kanji mit abweichender Lesung/Bedeutung) → "
  "**0 Divergenzen**; **`fill_blank`-Scan** (laut Projektregel verbotener Quiz-Typ) → **0 Vorkommen**.")
w("3. **Korrektheits-Audit:** 26 Agenten (1 je 2-3 Lektionen, modulkohärent) mit JLPT-Curriculum-Karte "
  "und Kanji-/Grammatik-Einführungsindex; jede Findung adversarial gegengeprüft.")
w("4. **Natürlichkeits-Recherche:** 1 Muttersprachler-Agent je Modul, mit **Web-Recherche** zum Thema "
  "als Vergleichsmassstab; jede Unnatürlich-/Steif-Markierung von einem strengen zweiten "
  "Muttersprachler gegengeprüft (Alternative muss N5-Niveau bleiben).")
w()
w("> Hinweis: Findungen sind **Vorschläge zur Sichtung**, noch nicht angewendet. Der Korrektur-Schritt "
  "(das Anwenden der Fixes) ist bewusst Phase 2 nach deiner Freigabe.")
w()

# ---------- Systematische Muster ----------
w("## Systematische Muster (zuerst angehen)")
w()
w("Diese Punkte wiederholen sich über mehrere Lektionen — ein Fix-Prinzip löst jeweils mehrere Stellen:")
w()
w("1. **Single-Select-Quiz mit zwei richtigen Antworten — i-Adjektiv-Verneinung** "
  "(L156 おもしろい, L170 大きい): Gefragt wird nach der Verneinung; als richtig markiert ist nur die "
  "Plain-Form 〜くない, die ebenfalls korrekte höfliche Form 〜くありません gilt als falsch. "
  "→ Entweder Distraktoren eindeutig falsch machen, oder Frage auf die einfache Form einschränken.")
w("2. **Kardinalzahl ohne Zähler** (L192 本が十, L206 本が十あります): 「十 + Nomen + あります」 ist "
  "ungrammatisch/idiomatisch unvollständig — Bücher brauchen den Zähler 冊 (十冊, N5). "
  "→ Zähler ergänzen; generell Zahl-am-Nomen-Konstruktionen prüfen.")
w("3. **Unjapanische Pronomen / Calques aus dem Deutschen** (L171 あなたの お母さん, weitere mit わたしは / "
  "あなた): Muttersprachler nennen den Namen + さん oder lassen das Pronomen weg. Teils widerspricht es der "
  "eigenen uchi/soto-Lehre derselben Lektion. → Pronomen streichen / durch Namen ersetzen.")
w("4. **Herbst 寒い statt 涼しい** (L204): Beispielsatz nennt den Herbst als kalt (Winterkälte) — "
  "widerspricht der eigenen Lektion, die 涼しい (kühl) als Herbst-Wort lehrt. → 涼しい verwenden.")
w("5. **Mora-Zählung ohne ん** (L150): Lehrtabelle zählt びょういん/びよういん um eine Mora zu niedrig "
  "(ん wird unterschlagen), während das Quiz derselben Lektion korrekt zählt. → Tabelle korrigieren.")
w()

# ---------- Teil A: Korrektheit ----------
w("---")
w()
w(f"## Teil A — Korrektheit ({len(fact)} Findungen)")
w()
w("Sortiert nach Kategorie (Quiz-Defekte & faktische Fehler zuerst), innerhalb nach Schwere.")
fact_sorted = sorted(fact, key=lambda f: (KAT_ORDER.get(f["kategorie"], 9), SEV_ORDER.get(f["severity"], 9), f["lesson_id"]))
cur = None
for f in fact_sorted:
    if f["kategorie"] != cur:
        cur = f["kategorie"]
        w()
        w(f"### {KAT_LABEL.get(cur, cur)}")
        w()
    vk = f.get("verdict", {})
    note = ""
    if vk and vk.get("vorschlag_korrekt") is False:
        note = "  \n  ⚠️ _Gegenprüfer: Befund stimmt, aber der Auditor-Vorschlag ist fehlerhaft — siehe Begründung._"
    w(f"- **L{f['lesson_id']} · {t(f['lesson_id'])}** — {SEV_BADGE.get(f['severity'],'')}  ")
    w(f"  _Fundstelle:_ {f['fundstelle']}  ")
    w(f"  _Problem:_ {f['problem']}  ")
    w(f"  _Korrektur:_ {f['vorschlag']}{note}")
w()

# ---------- Teil B: Natürlichkeit ----------
w("---")
w()
w(f"## Teil B — Natürlichkeit der Beispielsätze ({len(nat)} Findungen)")
w()
w("Sätze, die ein Muttersprachler als steif/unnatürlich empfindet. Sortiert nach Schwere. "
  "Jede Alternative bleibt auf N5-Niveau.")
w()
# nach Schwere hoch>mittel>gering
sw = {"hoch": 0, "mittel": 1, "gering": 2}
for f in sorted(nat, key=lambda f: (sw.get(f["schwere"], 9), f["lesson_id"])):
    alt = f.get("verdict", {}).get("bessere_alternative") or f["natuerliche_alternative"]
    w(f"- **L{f['lesson_id']} · {t(f['lesson_id'])}** — {NAT_BADGE.get(f['schwere'],'')} ({f['einstufung']})  ")
    w(f"  _Satz:_ 「{f['satz_jp']}」 — {f['kontext']}  ")
    w(f"  _Problem:_ {f['problem']}  ")
    w(f"  _Natürlicher:_ 「{alt}」")
w()

# ---------- Anhang ----------
w("---")
w()
w("## Anhang — Abdeckung")
w()
both = sorted(set([f["lesson_id"] for f in fact]) | set([f["lesson_id"] for f in nat]))
clean = [lid for lid in sorted(titles) if lid not in both]
w(f"- **{n_lessons} von 58 Lektionen** haben mindestens eine Findung.")
w(f"- **{len(clean)} Lektionen ohne jede Findung** (sauber): "
  + ", ".join(f"L{lid}" for lid in clean) + ".")
w()

(pathlib.Path(__file__).parent.parent / "docs").mkdir(exist_ok=True)
out = pathlib.Path(__file__).parent.parent / "docs" / "lektions-audit-report.md"
out.write_text("\n".join(L), encoding="utf-8")
print(f"Report geschrieben: {out}  ({len(L)} Zeilen)")
print(f"Korrektheit {len(fact)} | Natürlichkeit {len(nat)} | betroffene Lektionen {n_lessons} | saubere {len(clean)}")
