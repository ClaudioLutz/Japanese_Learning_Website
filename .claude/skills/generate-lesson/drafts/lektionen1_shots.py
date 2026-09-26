"""Playwright-Sichtprüfung (auf hp-ubuntu). Cookie wird nie ausgegeben.
Teil 1 (Host-venv): python lektionen1_shots.py cookie  -> /tmp/l1/cookie.txt
Teil 2 (pw-venv):   python lektionen1_shots.py shots 212 213
"""
import os
import sys

MODE = sys.argv[1]
if MODE == "cookie":
    sys.path.insert(0, "/home/hp-ubuntu/git/Japanese_Learning_Website")
    from app import create_app
    from app.models import User
    app = create_app()
    with app.app_context():
        admin = User.query.filter_by(is_admin=True).first()
        ser = app.session_interface.get_signing_serializer(app)
        val = ser.dumps({"_user_id": str(admin.id), "_fresh": True})
    fd = os.open("/tmp/l1/cookie.txt", os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.write(fd, val.encode())
    os.close(fd)
    print("cookie written")
    sys.exit(0)

from playwright.sync_api import sync_playwright  # noqa: E402

cookie = open("/tmp/l1/cookie.txt").read().strip()
BASE = "http://localhost:5000"
JS_DECK = """() => {
  const vis = el => !!(el.offsetParent || el.getClientRects().length);
  const page = document.querySelector('.lesson-page.active, .page-content.active, [data-page-content].active') || document;
  const cards = [...document.querySelectorAll('.flip-card')].filter(vis);
  const area = [...document.querySelectorAll('.deck-card-area')].find(vis);
  if (area) area.scrollIntoView({block: 'center'});
  return {visibleFlipCards: cards.length, inDeck: document.querySelectorAll('.content-item.in-deck').length};
}"""
with sync_playwright() as p:
    b = p.chromium.launch()
    for lid in [int(x) for x in sys.argv[2:]]:
        for name, vp in [("desktop", {"width": 1366, "height": 900}), ("mobile", {"width": 390, "height": 844})]:
            ctx = b.new_context(viewport=vp, is_mobile=(name == "mobile"))
            ctx.add_cookies([{"name": "session", "value": cookie, "domain": "localhost", "path": "/",
                              "httpOnly": True, "secure": True, "sameSite": "Lax"}])
            pg = ctx.new_page()
            errs = []
            pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
            logs = []
            pg.on("console", lambda m: logs.append(m.text) if "[Deck]" in m.text else None)
            pg.goto(f"{BASE}/lessons/{lid}", wait_until="networkidle")
            for page_idx in [1, 4]:  # Vokabeln Teil 1 (Deck) und Dialog
                pg.evaluate(f"""() => {{ const el = document.querySelector('.sidebar-page-item[data-page="{page_idx}"]');
                                     if (el) el.click(); }}""")
                pg.wait_for_timeout(1500)
                info = pg.evaluate(JS_DECK)
                path = f"/tmp/l1/shot_{lid}_p{page_idx + 1}_{name}.png"
                pg.screenshot(path=path)
                if page_idx == 1:
                    card = pg.locator('.flip-card:visible').first
                    card.scroll_into_view_if_needed()
                    pg.wait_for_timeout(500)
                    pg.screenshot(path=path.replace('.png', '_deck.png'))
                print(lid, name, f"page{page_idx + 1}", info)
            print(lid, name, "console-errors:", errs[:5], "deck-logs:", logs[:3])
            ctx.close()
    b.close()
