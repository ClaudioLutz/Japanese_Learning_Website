#!/usr/bin/env python
"""Design-Review Screenshot-Helfer.

Rendert eine Seite des lokalen Dev-Servers in Light oder Dark, Desktop oder Mobile,
und speichert einen Viewport- UND einen Full-Page-Screenshot. Dark-Mode wird ueber
localStorage-Key 'jpl-theme' VOR dem ersten Paint gesetzt (so wie das Pre-Paint-Script
in base.html es liest), damit kein FOUC die Aufnahme verfaelscht.

Beispiel:
  python tools/shot.py --url http://localhost:5000/ --theme dark --vp mobile --out shots/index
"""
import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright

SIZES = {"desktop": (1366, 900), "mobile": (390, 844)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--theme", choices=["light", "dark"], default="light")
    ap.add_argument("--vp", choices=["desktop", "mobile"], default="desktop")
    ap.add_argument("--out", required=True, help="Pfad-Praefix ohne Endung; erzeugt <out>_vp.png und <out>_full.png")
    ap.add_argument("--cookie", default="", help="Session-Cookie als 'name=value'")
    ap.add_argument("--wait", type=int, default=2500, help="ms warten nach networkidle")
    args = ap.parse_args()

    w, h = SIZES[args.vp]
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": w, "height": h}, device_scale_factor=1)
        # Theme VOR jedem Seiten-Script setzen -> Pre-Paint-Script liest 'dark'/'light'
        ctx.add_init_script(
            "try{localStorage.setItem('jpl-theme','%s');}catch(e){}" % args.theme
        )
        if args.cookie:
            name, _, value = args.cookie.partition("=")
            ctx.add_cookies([{"name": name.strip(), "value": value.strip(), "url": "http://localhost:5000"}])
        page = ctx.new_page()
        page.goto(args.url, wait_until="networkidle", timeout=45000)
        page.wait_for_timeout(args.wait)
        # Belt & suspenders: data-theme erzwingen (falls Store nach erstem Paint umschaltet)
        page.evaluate("(t) => document.documentElement.setAttribute('data-theme', t)", args.theme)
        page.wait_for_timeout(250)
        # Lazy-Images triggern: in Schritten nach unten scrollen (IntersectionObserver
        # feuern lassen), dann zurueck nach oben -> _full.png zeigt keine grauen Loecher.
        page.evaluate(
            """async () => {
                const step = window.innerHeight * 0.8;
                const max = document.body.scrollHeight;
                for (let y = 0; y < max; y += step) {
                    window.scrollTo(0, y);
                    await new Promise(r => setTimeout(r, 180));
                }
                window.scrollTo(0, 0);
                await new Promise(r => setTimeout(r, 400));
            }"""
        )
        page.screenshot(path=str(out) + "_vp.png", full_page=False)
        page.screenshot(path=str(out) + "_full.png", full_page=True)
        applied = page.evaluate("() => document.documentElement.getAttribute('data-theme')")
        title = page.title()
        browser.close()
        print("OK theme=%s applied=%s vp=%s title=%r" % (args.theme, applied, args.vp, title))


if __name__ == "__main__":
    main()
