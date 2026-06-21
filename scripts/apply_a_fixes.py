"""A-Fälle aus dem Audit (eigene Entscheidung, minimal-invasiv).

factual[56] L158: 2 nicht-gelehrte Versprechen aus der Intro (6564) entfernen
                  ('もう いちど' + Telefonnummern-Lerntipp), 'と いいます' behalten.
factual[20] L169: 雪 zur N4-Bonus-Notiz (6916) ergaenzen (konsistent zu 田/空).
factual[37] L166: falschen 'bereits in Lektion 4 gelernt'-Verweis entschaerfen (6825 + grammar 90).
Jede Aenderung gegen den Ist-Wert verifiziert; Commit nur, wenn alle gefundenen Ziele sauber ersetzt wurden.
"""
import re
from app import create_app, db
from sqlalchemy import text

app = create_app()


def get(table, col, pk):
    r = db.session.execute(text(f"SELECT {col} FROM {table} WHERE id=:i"), {"i": pk}).fetchone()
    return r[0] if r else None


def put(table, col, pk, val):
    return db.session.execute(text(f"UPDATE {table} SET {col}=:v WHERE id=:i"), {"v": val, "i": pk}).rowcount


with app.app_context():
    report = []
    ok = True

    # --- factual[56]: 6564 Intro, 2 Zeilen raus ---
    t = get("lesson_content", "content_text", 6564)
    if t and "もう いちど おねがいします" in t and "と いいます" in t:
        lines = t.split("\n")
        kept = []
        for ln in lines:
            if "もう いちど おねがいします" in ln and "Wiederholung" in ln:
                continue
            if ln.lstrip().startswith("> **Lerntipp:**") and "Telefonnummer" in ln:
                continue
            kept.append(ln)
        new = re.sub(r"\n{3,}", "\n\n", "\n".join(kept))
        if "と いいます" in new and "もう いちど" not in new and "Telefonnummer" not in new and new != t:
            put("lesson_content", "content_text", 6564, new)
            report.append("factual[56] 6564: 2 Versprechen entfernt, 'と いいます' behalten")
        else:
            ok = False; report.append("factual[56] 6564: SKIP (Verifikation fehlgeschlagen)")
    else:
        report.append("factual[56] 6564: SKIP (Ziel nicht/anders vorhanden)")

    # --- factual[20]: 6916 Bonus-Notiz um 雪 ergaenzen ---
    t = get("lesson_content", "content_text", 6916)
    anchor = "そら (sora, Himmel) — N4-Kanji, aber für Wetter-Sätze unverzichtbar."
    add = " ゆき (yuki, Schnee) — auch das Kanji 雪 ist N4 (das Wort selbst ist N5)."
    if t and anchor in t and add.strip() not in t:
        new = t.replace(anchor, anchor + add, 1)
        put("lesson_content", "content_text", 6916, new)
        report.append("factual[20] 6916: 雪 zur N4-Bonus-Notiz ergaenzt")
    else:
        report.append("factual[20] 6916: SKIP (Anker fehlt oder schon ergaenzt)")

    # --- factual[37]: 6825 + grammar 90 Verweis entschaerfen ---
    t = get("lesson_content", "content_text", 6825)
    old56 = "Du hast die Te-Form bereits in Lektion 4 gelernt."
    new56 = "Die Te-Form lernst du im Modul „Erste Sätze“ ausführlich kennen; hier nutzt du sie für Wegbeschreibungen."
    if t and old56 in t:
        put("lesson_content", "content_text", 6825, t.replace(old56, new56, 1))
        report.append("factual[37] 6825: 'bereits gelernt' entschaerft")
    else:
        report.append("factual[37] 6825: SKIP (Phrase nicht gefunden)")
    g = get("grammar", "explanation", 90)
    if g and " (siehe Lektion 4)" in g:
        put("grammar", "explanation", 90, g.replace(" (siehe Lektion 4)", "", 1))
        report.append("factual[37] grammar90: irrefuehrenden Querverweis entfernt")
    else:
        report.append("factual[37] grammar90: SKIP (Querverweis nicht gefunden)")

    for r in report:
        print(" ", r)
    if ok:
        db.session.commit(); print("COMMIT")
    else:
        db.session.rollback(); print("ROLLBACK (Verifikation)")
