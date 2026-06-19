#!/usr/bin/env python
"""Misst echte WCAG-Kontrastverhaeltnisse einer Seite in einem Theme.

Geht jeden sichtbaren Textknoten durch, liest getComputedStyle (Farbe + effektiver
Hintergrund durch Hochlaufen der Ahnen) und berechnet das WCAG-Kontrastverhaeltnis.
Gibt JSON mit allen Treffern unter Schwelle aus (4.5 normal / 3.0 grosser Text).
Tokens koennen durch Spezifitaet ueberschrieben werden -> nur der echte computed
Wert zaehlt, nicht das CSS-Token.

Ausgabe: JSON-Objekt {url, theme, failures: [...]} nach stdout.
"""
import argparse
import json
import sys
from playwright.sync_api import sync_playwright

JS = r"""
() => {
  function parseRGB(s){
    if(!s) return null;
    const m = s.match(/rgba?\(([^)]+)\)/);
    if(!m) return null;
    const p = m[1].split(',').map(x=>parseFloat(x.trim()));
    return {r:p[0], g:p[1], b:p[2], a:(p.length>3?p[3]:1)};
  }
  function lum(c){
    const f = v => { v/=255; return v<=0.03928 ? v/12.92 : Math.pow((v+0.055)/1.055,2.4); };
    return 0.2126*f(c.r)+0.7152*f(c.g)+0.0722*f(c.b);
  }
  function ratio(a,b){
    const L1=lum(a),L2=lum(b);
    return (Math.max(L1,L2)+0.05)/(Math.min(L1,L2)+0.05);
  }
  // effektiver Hintergrund: erste nicht-transparente bg-color hoch im Baum
  function effBg(el){
    let node = el;
    while(node && node.nodeType===1){
      const st = getComputedStyle(node);
      const bg = parseRGB(st.backgroundColor);
      const hasImg = st.backgroundImage && st.backgroundImage !== 'none';
      if(hasImg) return {bg:{r:255,g:255,b:255,a:1}, overImage:true};
      if(bg && bg.a>0.5) return {bg, overImage:false};
      node = node.parentElement;
    }
    return {bg:{r:255,g:255,b:255,a:1}, overImage:false};
  }
  const out = [];
  const seen = new Set();
  const els = document.querySelectorAll('body *');
  for(const el of els){
    // nur Elemente mit direktem, sichtbarem Textinhalt
    let direct = '';
    for(const n of el.childNodes){ if(n.nodeType===3) direct += n.textContent; }
    direct = direct.trim();
    if(direct.length < 2) continue;
    const rect = el.getBoundingClientRect();
    if(rect.width<4 || rect.height<4) continue;
    const st = getComputedStyle(el);
    if(st.visibility==='hidden' || st.display==='none' || parseFloat(st.opacity)<0.3) continue;
    const fg = parseRGB(st.color);
    if(!fg || fg.a < 0.5) continue;
    const {bg, overImage} = effBg(el);
    if(overImage) continue; // Text ueber Bild/Gradient -> nicht zuverlaessig messbar
    const r = ratio(fg, bg);
    const fs = parseFloat(st.fontSize);
    const bold = (parseInt(st.fontWeight)||400) >= 700;
    const large = fs >= 24 || (fs >= 18.66 && bold);
    const threshold = large ? 3.0 : 4.5;
    if(r < threshold){
      const key = el.tagName+'|'+st.color+'|'+direct.slice(0,30);
      if(seen.has(key)) continue;
      seen.add(key);
      out.push({
        tag: el.tagName.toLowerCase(),
        cls: (el.className && el.className.toString) ? el.className.toString().slice(0,60) : '',
        text: direct.slice(0,50),
        color: st.color,
        bg: 'rgb('+bg.r+','+bg.g+','+bg.b+')',
        ratio: Math.round(r*100)/100,
        fontPx: Math.round(fs*10)/10,
        bold: bold,
        threshold: threshold
      });
    }
  }
  out.sort((a,b)=>a.ratio-b.ratio);
  return out.slice(0, 60);
}
"""


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # Windows cp1252 -> UTF-8 fuer JSON
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--theme", choices=["light", "dark"], default="light")
    ap.add_argument("--vp", choices=["desktop", "mobile"], default="desktop")
    ap.add_argument("--cookie", default="")
    args = ap.parse_args()

    w, h = (1366, 900) if args.vp == "desktop" else (390, 844)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": w, "height": h})
        ctx.add_init_script("try{localStorage.setItem('jpl-theme','%s');}catch(e){}" % args.theme)
        if args.cookie:
            name, _, value = args.cookie.partition("=")
            ctx.add_cookies([{"name": name.strip(), "value": value.strip(), "url": "http://localhost:5000"}])
        page = ctx.new_page()
        page.goto(args.url, wait_until="networkidle", timeout=45000)
        page.wait_for_timeout(1800)
        page.evaluate("(t) => document.documentElement.setAttribute('data-theme', t)", args.theme)
        page.wait_for_timeout(400)
        failures = page.evaluate(JS)
        browser.close()

    print(json.dumps({"url": args.url, "theme": args.theme, "vp": args.vp, "failures": failures}, ensure_ascii=False))


if __name__ == "__main__":
    main()
