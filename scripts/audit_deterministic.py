"""Deterministische Vorab-Pässe für den Lektions-Audit.
Liest die JSON-Dumps in scripts/data/lesson_audit/ und erzeugt:
  - _det_consistency.json   (gleiches Wort/Kanji, divergierende Lesung/Bedeutung)
  - _det_fill_blank.json    (deprecated Quiz-Typ)
  - _det_intro_index.txt    (Kanji-/Grammatik-Einführungsreihenfolge, kompakt für Agent-Prompts)
  - _det_counts.json        (Content-Anzahl pro Lektion, zum DB-Abgleich)
"""
import json
import glob
import pathlib
from collections import defaultdict

D = pathlib.Path(__file__).parent / "data" / "lesson_audit"

lessons = []
for f in sorted(glob.glob(str(D / "lesson_*.json"))):
    lessons.append(json.load(open(f, encoding="utf-8")))
lessons.sort(key=lambda o: (o.get("category_order") or 0, o.get("order_index") or 0, o["id"]))

def contents(o):
    for p in o.get("pages") or []:
        for c in p.get("content") or []:
            yield p, c

# --- Content-Anzahl pro Lektion (DB-Abgleich) ---
counts = {o["id"]: sum(1 for _ in contents(o)) for o in lessons}
json.dump(counts, open(D / "_det_counts.json", "w"), indent=2)

# --- Konsistenz: Wort/Kanji -> divergierende Lesung/Bedeutung ---
vocab_map = defaultdict(lambda: defaultdict(set))   # word -> reading -> {lesson_ids}
vocab_mean = defaultdict(lambda: defaultdict(set))  # word -> meaning_de -> {lesson_ids}
kanji_read = defaultdict(lambda: defaultdict(set))   # char -> (on|kun) -> {lesson}
kanji_mean = defaultdict(lambda: defaultdict(set))
for o in lessons:
    lid = o["id"]
    for _, c in contents(o):
        r = c.get("resolved") or {}
        if c["content_type"] == "vocabulary" and r:
            w = (r.get("word") or "").strip()
            if w:
                if r.get("reading"):
                    vocab_map[w][r["reading"].strip()].add(lid)
                if r.get("meaning_de"):
                    vocab_mean[w][r["meaning_de"].strip()].add(lid)
        elif c["content_type"] == "kanji" and r:
            ch = (r.get("character") or "").strip()
            if ch:
                key = f"on:{(r.get('onyomi') or '').strip()}|kun:{(r.get('kunyomi') or '').strip()}"
                kanji_read[ch][key].add(lid)
                if r.get("meaning"):
                    kanji_mean[ch][r["meaning"].strip()].add(lid)

consistency = []
for w, readings in vocab_map.items():
    if len(readings) > 1:
        consistency.append({"typ": "vocab_reading", "item": w,
                            "varianten": {k: sorted(v) for k, v in readings.items()}})
for w, means in vocab_mean.items():
    if len(means) > 1:
        consistency.append({"typ": "vocab_meaning_de", "item": w,
                            "varianten": {k: sorted(v) for k, v in means.items()}})
for ch, reads in kanji_read.items():
    if len(reads) > 1:
        consistency.append({"typ": "kanji_reading", "item": ch,
                            "varianten": {k: sorted(v) for k, v in reads.items()}})
for ch, means in kanji_mean.items():
    if len(means) > 1:
        consistency.append({"typ": "kanji_meaning", "item": ch,
                            "varianten": {k: sorted(v) for k, v in means.items()}})
json.dump(consistency, open(D / "_det_consistency.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)

# --- fill_blank (deprecated) ---
fill = []
for o in lessons:
    for p, c in contents(o):
        for q in (c.get("quiz") or []):
            if (q.get("question_type") or "").lower() in ("fill_blank", "fill_in_the_blank"):
                fill.append({"lesson_id": o["id"], "title": o["title"],
                             "page": p.get("page_number"), "frage": q.get("question_text")})
json.dump(fill, open(D / "_det_fill_blank.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)

# --- Einführungsindex Kanji + Grammatik (erste Lektion in Curriculum-Reihenfolge) ---
kanji_intro, gram_intro = {}, {}
for o in lessons:
    lid, title = o["id"], o["title"]
    for _, c in contents(o):
        r = c.get("resolved") or {}
        if c["content_type"] == "kanji" and r.get("character"):
            kanji_intro.setdefault(r["character"], (lid, title))
        elif c["content_type"] == "grammar" and r.get("title"):
            gram_intro.setdefault(r["title"].strip(), (lid, title))
with open(D / "_det_intro_index.txt", "w", encoding="utf-8") as f:
    f.write("KANJI-EINFÜHRUNG (Zeichen: erste Lektion-ID, in der es als Kanji-Karte erscheint)\n")
    f.write("  ".join(f"{k}=L{v[0]}" for k, v in kanji_intro.items()) + "\n\n")
    f.write("GRAMMATIK-EINFÜHRUNG (Thema: erste Lektion-ID)\n")
    for g, v in gram_intro.items():
        f.write(f"  L{v[0]}: {g}\n")

print(f"Lektionen: {len(lessons)}")
print(f"Konsistenz-Divergenzen: {len(consistency)}")
print(f"fill_blank-Fragen: {len(fill)}")
print(f"Kanji im Index: {len(kanji_intro)} | Grammatik-Themen: {len(gram_intro)}")
print(f"Content gesamt im Dump: {sum(counts.values())}")
