"""Baut die finalen Drafts: ersetzt {"ref_id": N}-Vokabeln durch die Daten der
bestehenden Prod-Zeilen (lektionen1_vocab_prod.json), damit insert per `word`
dedupliziert und keine zweite Vocabulary-Zeile entsteht."""
import json
from pathlib import Path

HERE = Path(__file__).parent
FIELDS = ["word", "reading", "romaji", "meaning", "meaning_de", "jlpt_level",
          "example_sentence_japanese", "example_sentence_english", "image_url"]
vocab = {v["id"]: v for v in json.loads((HERE / "lektionen1_vocab_prod.json").read_text(encoding="utf-8"))}

for name in ["lektionen1_adjektive3", "lektionen1_verben3"]:
    src = json.loads((HERE / f"{name}.src.json").read_text(encoding="utf-8"))
    out_path = HERE / f"{name}.json"
    old = json.loads(out_path.read_text(encoding="utf-8")) if out_path.exists() else {}
    for page in src["pages"]:
        for item in page["contents"]:
            if item.get("content_type") == "vocabulary" and "ref_id" in item:
                v = vocab[item["ref_id"]]
                item["data"] = {f: v.get(f) for f in FIELDS}
                item["data"]["vocab_id"] = v["id"]
                del item["ref_id"]
    # bereits erzeugte Bild-URLs aus einem frueheren images-Lauf uebernehmen
    if old:
        src["thumbnail_url"] = old.get("thumbnail_url")
        old_imgs = {it["data"]["word"]: it["data"].get("image_url")
                    for p in old.get("pages", []) for it in p["contents"]
                    if it.get("content_type") == "vocabulary"}
        for page in src["pages"]:
            for item in page["contents"]:
                if item.get("content_type") == "vocabulary" and not item["data"].get("image_url"):
                    item["data"]["image_url"] = old_imgs.get(item["data"]["word"])
    out_path.write_text(json.dumps(src, ensure_ascii=False, indent=2), encoding="utf-8")
    print(name, "ok")
