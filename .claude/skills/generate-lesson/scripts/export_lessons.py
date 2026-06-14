"""Exportiert vollstaendige Lektionen aus der LOKALEN DB in ein migrator-JSON
(faithful, inkl. verlinkter Vocabulary/Kanji/Grammar + Quiz). Audio-media_url
wird bewusst weggelassen (id-abhaengig, nicht uebertragen). Bilder via image_url
(id-unabhaengig) bleiben + werden als Asset-Manifest gesammelt.
Aufruf: python export_lessons.py <out.json> <id1> <id2> ...
"""
import sys, json
sys.path.insert(0, '.')
from app import create_app, db
from app.models import (Lesson, LessonCategory, LessonPage, LessonContent,
                        Vocabulary, Kanji, Grammar, QuizQuestion, QuizOption)

out_path = sys.argv[1]
ids = [int(x) for x in sys.argv[2:]]

def vocab_data(v):
    return {"word": v.word, "reading": v.reading, "romaji": v.romaji, "meaning": v.meaning,
            "meaning_de": v.meaning_de, "jlpt_level": v.jlpt_level,
            "example_sentence_japanese": v.example_sentence_japanese,
            "example_sentence_english": v.example_sentence_english,
            "image_url": v.image_url, "status": v.status, "created_by_ai": v.created_by_ai}

def kanji_data(k):
    return {"character": k.character, "meaning": k.meaning, "onyomi": k.onyomi, "kunyomi": k.kunyomi,
            "jlpt_level": k.jlpt_level, "stroke_order_info": k.stroke_order_info, "radical": k.radical,
            "stroke_count": k.stroke_count, "image_url": k.image_url, "status": k.status,
            "created_by_ai": k.created_by_ai}

def grammar_data(g):
    return {"title": g.title, "explanation": g.explanation, "structure": g.structure, "romaji": g.romaji,
            "jlpt_level": g.jlpt_level, "example_sentences": g.example_sentences,
            "tts_example_jp": g.tts_example_jp, "status": g.status, "created_by_ai": g.created_by_ai,
            "nuance": getattr(g, "nuance", None)}

app = create_app()
assets = set()
with app.app_context():
    cats = {c.id: c for c in db.session.query(LessonCategory).all()}
    lessons_out = []
    for lid in ids:
        L = db.session.get(Lesson, lid)
        if not L:
            print(f"[WARN] Lesson {lid} fehlt lokal"); continue
        cat = cats.get(L.category_id)
        if L.thumbnail_url:
            assets.add(L.thumbnail_url)
        pages = [{"page_number": p.page_number, "title": p.title, "description": p.description,
                  "page_type": p.page_type}
                 for p in db.session.query(LessonPage).filter_by(lesson_id=lid).order_by(LessonPage.page_number).all()]
        contents = []
        for c in db.session.query(LessonContent).filter_by(lesson_id=lid).order_by(LessonContent.page_number, LessonContent.order_index, LessonContent.id).all():
            entity = None
            if c.content_type == "vocabulary" and c.content_id:
                v = db.session.get(Vocabulary, c.content_id)
                if v: entity = vocab_data(v);  assets.add(v.image_url) if v.image_url else None
            elif c.content_type == "kanji" and c.content_id:
                k = db.session.get(Kanji, c.content_id)
                if k: entity = kanji_data(k);  assets.add(k.image_url) if k.image_url else None
            elif c.content_type == "grammar" and c.content_id:
                g = db.session.get(Grammar, c.content_id)
                if g: entity = grammar_data(g)
            quizzes = []
            for q in db.session.query(QuizQuestion).filter_by(lesson_content_id=c.id).order_by(QuizQuestion.order_index, QuizQuestion.id).all():
                opts = [{"option_text": o.option_text, "is_correct": o.is_correct,
                         "order_index": o.order_index, "feedback": o.feedback}
                        for o in db.session.query(QuizOption).filter_by(question_id=q.id).order_by(QuizOption.order_index, QuizOption.id).all()]
                quizzes.append({"question_type": q.question_type, "question_text": q.question_text,
                                "explanation": q.explanation, "hint": q.hint,
                                "difficulty_level": q.difficulty_level, "points": q.points,
                                "order_index": q.order_index, "options": opts})
            contents.append({"page_number": c.page_number, "order_index": c.order_index,
                             "content_type": c.content_type, "content_text": c.content_text,
                             "title": c.title, "is_interactive": c.is_interactive,
                             "quiz_type": c.quiz_type, "entity": entity, "quiz_questions": quizzes})
        lessons_out.append({
            "src_id": lid,
            "lesson": {"title": L.title, "description": L.description, "lesson_type": L.lesson_type,
                       "difficulty_level": L.difficulty_level, "allow_guest_access": L.allow_guest_access,
                       "instruction_language": L.instruction_language, "thumbnail_url": L.thumbnail_url,
                       "price": float(L.price) if L.price is not None else 0.0,
                       "is_purchasable": L.is_purchasable, "category_slug": cat.slug if cat else None,
                       "order_index": L.order_index, "is_published": L.is_published},
            "pages": pages, "contents": contents,
        })
        nv = sum(1 for c in contents if c["content_type"] == "vocabulary")
        nk = sum(1 for c in contents if c["content_type"] == "kanji")
        ng = sum(1 for c in contents if c["content_type"] == "grammar")
        nq = sum(len(c["quiz_questions"]) for c in contents)
        print(f"  L{lid} '{L.title[:34]}': pages={len(pages)} vocab={nv} kanji={nk} gram={ng} quiz={nq} cat={cat.slug if cat else None} order={L.order_index} pub={L.is_published}")

payload = {"lessons": lessons_out, "assets": sorted(a for a in assets if a)}
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=1)
print(f"\n[OK] {len(lessons_out)} Lektionen exportiert -> {out_path}; {len(payload['assets'])} Asset-Dateien referenziert")
