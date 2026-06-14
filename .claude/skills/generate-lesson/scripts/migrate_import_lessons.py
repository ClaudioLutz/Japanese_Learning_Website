"""Importiert migrator-JSON in die ZIEL-DB (Prod). Dedup von Vocabulary/Kanji/
Grammar per Natuerlich-Schluessel (word/character/title) — bestehende werden
wiederverwendet, NIE ueberschrieben. Lesson-Idempotenz per Titel (skip wenn schon da).
Audio (media_url) wird NICHT gesetzt. DRY-RUN per Default; --apply committet.
Aufruf: DATABASE_URL=... python import_lessons.py <migrate.json> [--apply]
"""
import sys, json
sys.path.insert(0, '.')
from app import create_app, db
from app.models import (Lesson, LessonCategory, LessonPage, LessonContent,
                        Vocabulary, Kanji, Grammar, QuizQuestion, QuizOption)

payload = json.load(open(sys.argv[1], encoding='utf-8'))
APPLY = '--apply' in sys.argv
stats = {"vocab_new": 0, "vocab_reuse": 0, "kanji_new": 0, "kanji_reuse": 0,
         "gram_new": 0, "gram_reuse": 0, "lessons_new": 0, "lessons_skip": 0, "quiz": 0}

def goc_vocab(d):
    ex = db.session.query(Vocabulary).filter_by(word=d["word"]).first()
    if ex: stats["vocab_reuse"] += 1; return ex.id
    v = Vocabulary(word=d["word"], reading=d["reading"], romaji=d.get("romaji"), meaning=d["meaning"],
                   meaning_de=d.get("meaning_de"), jlpt_level=d.get("jlpt_level"),
                   example_sentence_japanese=d.get("example_sentence_japanese"),
                   example_sentence_english=d.get("example_sentence_english"),
                   image_url=d.get("image_url"), status=d.get("status", "approved"),
                   created_by_ai=d.get("created_by_ai", True))
    db.session.add(v); db.session.flush(); stats["vocab_new"] += 1; return v.id

def goc_kanji(d):
    ex = db.session.query(Kanji).filter_by(character=d["character"]).first()
    if ex: stats["kanji_reuse"] += 1; return ex.id
    k = Kanji(character=d["character"], meaning=d["meaning"], onyomi=d.get("onyomi"), kunyomi=d.get("kunyomi"),
              jlpt_level=d.get("jlpt_level"), stroke_order_info=d.get("stroke_order_info"),
              radical=d.get("radical"), stroke_count=d.get("stroke_count"), image_url=d.get("image_url"),
              status=d.get("status", "approved"), created_by_ai=d.get("created_by_ai", True))
    db.session.add(k); db.session.flush(); stats["kanji_new"] += 1; return k.id

def goc_grammar(d):
    ex = db.session.query(Grammar).filter_by(title=d["title"]).first()
    if ex: stats["gram_reuse"] += 1; return ex.id
    g = Grammar(title=d["title"], explanation=d["explanation"], structure=d.get("structure"),
                romaji=d.get("romaji"), jlpt_level=d.get("jlpt_level"),
                example_sentences=d.get("example_sentences"), tts_example_jp=d.get("tts_example_jp"),
                status=d.get("status", "approved"), created_by_ai=d.get("created_by_ai", True))
    if "nuance" in d and hasattr(g, "nuance"):
        g.nuance = d.get("nuance")
    db.session.add(g); db.session.flush(); stats["gram_new"] += 1; return g.id

app = create_app()
with app.app_context():
    cat_by_slug = {c.slug: c.id for c in db.session.query(LessonCategory).all()}
    for entry in payload["lessons"]:
        Ld = entry["lesson"]
        title = Ld["title"]
        if db.session.query(Lesson).filter_by(title=title).first():
            print(f"  [SKIP] '{title[:40]}' existiert bereits in Ziel-DB")
            stats["lessons_skip"] += 1; continue
        slug = Ld.get("category_slug")
        cat_id = cat_by_slug.get(slug)
        if slug and cat_id is None:
            print(f"  [WARN] Kategorie-Slug '{slug}' fehlt in Ziel-DB — Lesson '{title[:30]}' bekommt category_id=NULL")
        lesson = Lesson(title=title, description=Ld["description"], lesson_type=Ld.get("lesson_type", "free"),
                        difficulty_level=Ld.get("difficulty_level", 1), is_published=Ld.get("is_published", True),
                        allow_guest_access=Ld.get("allow_guest_access", False),
                        instruction_language=Ld.get("instruction_language", "german"),
                        thumbnail_url=Ld.get("thumbnail_url"), price=Ld.get("price", 0.0),
                        is_purchasable=Ld.get("is_purchasable", False),
                        category_id=cat_id, order_index=Ld.get("order_index", 0))
        db.session.add(lesson); db.session.flush()
        lid = lesson.id
        for p in entry["pages"]:
            db.session.add(LessonPage(lesson_id=lid, page_number=p["page_number"], title=p.get("title"),
                                      description=p.get("description"), page_type=p.get("page_type", "normal")))
        db.session.flush()
        for c in entry["contents"]:
            cid = None
            ct = c["content_type"]
            ent = c.get("entity")
            if ent and ct == "vocabulary": cid = goc_vocab(ent)
            elif ent and ct == "kanji": cid = goc_kanji(ent)
            elif ent and ct == "grammar": cid = goc_grammar(ent)
            lc = LessonContent(lesson_id=lid, content_type=ct, content_id=cid, title=c.get("title"),
                               content_text=c.get("content_text"), order_index=c.get("order_index", 1),
                               page_number=c.get("page_number", 1), is_interactive=c.get("is_interactive", False),
                               quiz_type=c.get("quiz_type", "standard"), generated_by_ai=True,
                               ai_generation_details={"migrated_from": "local", "src_id": entry.get("src_id")})
            db.session.add(lc); db.session.flush()
            for q in c.get("quiz_questions", []):
                qq = QuizQuestion(lesson_content_id=lc.id, question_type=q["question_type"],
                                  question_text=q["question_text"], explanation=q.get("explanation"),
                                  hint=q.get("hint"), difficulty_level=q.get("difficulty_level", 1),
                                  points=q.get("points", 1), order_index=q.get("order_index", 1))
                db.session.add(qq); db.session.flush(); stats["quiz"] += 1
                for o in q.get("options", []):
                    db.session.add(QuizOption(question_id=qq.id, option_text=o["option_text"],
                                              is_correct=o.get("is_correct", False),
                                              order_index=o.get("order_index", 1), feedback=o.get("feedback")))
        stats["lessons_new"] += 1
        print(f"  [NEW] id={lid} '{title[:40]}' cat={cat_id} order={Ld.get('order_index')} pub={lesson.is_published}")
    print("\n--- Stats ---")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    if APPLY:
        db.session.commit(); print("\n[APPLY] COMMIT — Lektionen in Ziel-DB geschrieben.")
    else:
        db.session.rollback(); print("\n[DRY-RUN] ROLLBACK — nichts geschrieben. Mit --apply committen.")
