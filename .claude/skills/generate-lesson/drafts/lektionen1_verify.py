"""Read-only Render-Check (test_client + Admin-Session) fuer Lektionen 212/213
und Asset-Pfad-Aufloesung. Laeuft auf hp-ubuntu gegen die Prod-DB."""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, "/home/hp-ubuntu/git/Japanese_Learning_Website")
from app import create_app  # noqa: E402
from app.models import Lesson, LessonContent, User, Vocabulary  # noqa: E402

UP = Path("/home/hp-ubuntu/git/Japanese_Learning_Website/app/static/uploads")
app = create_app()
app.config["WTF_CSRF_ENABLED"] = False
with app.app_context():
    admin = User.query.filter_by(is_admin=True).first()
    for lid in [int(x) for x in sys.argv[1:]]:
        lesson = Lesson.query.get(lid)
        missing = []
        paths = [lesson.thumbnail_url]
        for lc in LessonContent.query.filter_by(lesson_id=lid).all():
            if lc.content_type == "vocabulary":
                paths.append(Vocabulary.query.get(lc.content_id).image_url)
            if lc.media_url:
                paths.append(lc.media_url)
            if lc.content_type == "dialog_slideshow":
                data = json.loads(lc.content_text or "{}")
                for s in data.get("slides", []):
                    paths += [s.get("image"), s.get("audio")]
            aug = (lc.ai_generation_details or {}).get("augmented_html") if isinstance(lc.ai_generation_details, dict) else None
            if aug:
                paths += re.findall(r'data-audio-url="([^"]+)"', aug)
        for p in paths:
            if not p:
                missing.append("<leer>")
                continue
            rel = re.sub(r"^/?(static/)?uploads/", "", p)
            if not (UP / rel).exists():
                missing.append(p)
        c = app.test_client()
        with c.session_transaction(base_url="https://localhost") as s:
            s["_user_id"] = str(admin.id)
            s["_fresh"] = True
        r = c.get(f"/lessons/{lid}", base_url="https://localhost")
        html = r.get_data(as_text=True)
        print(f"Lesson {lid}: HTTP {r.status_code}, len={len(html)}, title_ok={lesson.title.split(' — ')[0] in html}, "
              f"assets={len(paths)}, missing={len(missing)} {missing[:5]}")
        print("  flip-cards:", html.count("flip-card"), " quiz:", html.count("quiz-question"),
              " slideshow:", "slideshow" in html, " Traceback:", "Traceback" in html)
