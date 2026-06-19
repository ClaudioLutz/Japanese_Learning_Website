#!/usr/bin/env python
"""Legt einen Premium-Test-User an (idempotent) und loggt per Playwright ein ->
druckt 'session=<wert>'. Playwright fuellt das echte Login-Formular (CSRF korrekt).

Stdout = nur die Cookie-Zeile; Diagnose -> stderr. Mit DATABASE_URL-Override laufen.
"""
import argparse
import sys

from app import create_app, db
from app.models import User
from playwright.sync_api import sync_playwright

ap = argparse.ArgumentParser()
ap.add_argument("--username", default="designreview")
ap.add_argument("--email", default="jpl.designreview@gmail.com")  # aufloesbare Domain -> Email-Validator besteht
ap.add_argument("--password", default="DesignReview123!")
ap.add_argument("--set-premium", action="store_true", help="subscription_level=premium erzwingen")
args = ap.parse_args()

EMAIL = args.email
PW = args.password
BASE = "http://localhost:5000"

app = create_app()
with app.app_context():
    u = User.query.filter_by(username=args.username).first()
    if not u:
        u = User(username=args.username, email=EMAIL, subscription_level="premium", is_admin=False)
        u.set_password(PW)
        db.session.add(u)
        db.session.commit()
        print("created user id=%s" % u.id, file=sys.stderr)
    else:
        if args.set_premium:
            u.subscription_level = "premium"
        EMAIL = u.email  # bestehende Mail beibehalten -> Login klappt
        u.set_password(PW)
        db.session.commit()
        print("reused user id=%s email=%s sub=%s" % (u.id, u.email, u.subscription_level), file=sys.stderr)

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context()
    page = ctx.new_page()
    page.goto(BASE + "/login", wait_until="networkidle")
    page.fill('input[type="email"]', EMAIL)
    page.fill('input[type="password"]', PW)
    page.click('button[type="submit"], input[type="submit"]')
    page.wait_for_load_state("networkidle")
    print("after-login url=%s" % page.url, file=sys.stderr)
    cookies = ctx.cookies()
    browser.close()

sess = next((c["value"] for c in cookies if c["name"] == "session"), None)
print("session=" + (sess or "NONE"))
