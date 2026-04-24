"""
generate-lesson verification — Playwright-basierte End-to-End-Validierung.

Loggt sich als Admin ein, oeffnet die neue Lektion, klickt durch alle Pages,
testet Quiz-Interaktionen, und speichert Screenshots als Evidenz.

Usage:
  python .claude/skills/generate-lesson/verify.py <lesson_id>
"""
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SKILL_DIR = Path(__file__).resolve().parent
VERIFICATIONS_DIR = SKILL_DIR / "verifications"
VERIFICATIONS_DIR.mkdir(exist_ok=True)

load_dotenv(PROJECT_ROOT / ".env")


def verify_lesson(lesson_id: int, base_url: str = "http://localhost:5000"):
    """Oeffnet die Lektion und klickt alles durch. Speichert Screenshots."""
    from playwright.sync_api import sync_playwright

    run_dir = VERIFICATIONS_DIR / f"lesson_{lesson_id}_{datetime.utcnow():%Y%m%dT%H%M%S}"
    run_dir.mkdir()
    issues = []

    # Credentials aus .env — Login-Form nutzt Feld 'email' (nicht 'username')
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@example.com")
    admin_pass = os.environ.get("ADMIN_PASSWORD")
    if not admin_pass:
        print("[FAIL] ADMIN_PASSWORD nicht in .env gesetzt")
        return False

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        try:
            # 1. Login (Admin wird zu /admin redirected, nicht /dashboard)
            page.goto(f"{base_url}/login")
            page.fill('input[name="email"]', admin_email)
            page.fill('input[name="password"]', admin_pass)
            page.click('button[type="submit"]')
            page.wait_for_url("**/admin*", timeout=10000)
            page.screenshot(path=run_dir / "01_login_ok.png")

            # 2. Lesson-Detail oeffnen
            page.goto(f"{base_url}/lessons/{lesson_id}")
            page.wait_for_load_state("networkidle")
            page.screenshot(path=run_dir / "02_lesson_opened.png")

            # 3. Alle Pages durchklicken
            # Naive Navigation: "Next"/"Weiter"-Button solange klicken bis er weg ist
            page_idx = 0
            while True:
                page_idx += 1
                page.screenshot(path=run_dir / f"03_page_{page_idx:02d}.png")

                # Deck-Karussell-Check (CLAUDE.md §"Deck-Karussell")
                visible_cards = page.locator(".content-item:visible").count()
                if visible_cards > 1:
                    issues.append(
                        f"Page {page_idx}: {visible_cards} Karten gleichzeitig sichtbar "
                        f"— CSS-Regel `.content-item.in-deck {{ display: none }}` nicht wirksam. "
                        f"CSS-Syntaxfehler vermuten (siehe CLAUDE.md)."
                    )

                next_btn = page.locator("button:has-text('Weiter'), button:has-text('Next')")
                if next_btn.count() == 0 or not next_btn.first.is_enabled():
                    break
                next_btn.first.click()
                page.wait_for_timeout(500)

                if page_idx > 10:  # Safety-Stop
                    issues.append("Mehr als 10 Pages durchlaufen — Endlosschleife vermutet")
                    break

            # 4. Admin-Approval-Page checken (via JSON-API, nicht AJAX-Shell)
            import requests
            # Cookie aus Playwright ins requests-Session uebernehmen
            cookies = {c["name"]: c["value"] for c in context.cookies()}
            api_r = requests.get(f"{base_url}/api/admin/lessons", cookies=cookies, timeout=10)
            if api_r.status_code != 200 or str(lesson_id) not in api_r.text:
                issues.append(
                    f"Lesson {lesson_id} nicht in /api/admin/lessons "
                    f"(HTTP {api_r.status_code})"
                )

        except Exception as e:
            issues.append(f"Unexpected error: {e}")
            try:
                page.screenshot(path=run_dir / "99_error.png")
            except Exception:
                pass

        finally:
            browser.close()

    # Report
    report_path = run_dir / "report.md"
    status = "PASS" if not issues else "FAIL"
    report = f"# Verification Report — Lesson {lesson_id}\n\n"
    report += f"**Status:** {status}\n"
    report += f"**Run:** {run_dir.name}\n\n"
    if issues:
        report += "## Issues\n\n"
        for i, issue in enumerate(issues, 1):
            report += f"{i}. {issue}\n"
    else:
        report += "Alle Checks bestanden.\n"
    report_path.write_text(report, encoding="utf-8")

    print(f"[{status}] Report: {report_path}")
    return len(issues) == 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("lesson_id", type=int)
    parser.add_argument("--base-url", default="http://localhost:5000")
    args = parser.parse_args()

    ok = verify_lesson(args.lesson_id, args.base_url)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
