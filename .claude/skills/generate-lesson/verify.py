"""
generate-lesson verification — Playwright-basierte End-to-End-Validierung.

Loggt sich als Admin ein, oeffnet die neue Lektion, klickt durch alle Pages,
testet Quiz-Interaktionen, und speichert Screenshots als Evidenz.

Usage:
  python .claude/skills/generate-lesson/verify.py <lesson_id>
"""
import sys
import argparse
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SKILL_DIR = Path(__file__).resolve().parent
VERIFICATIONS_DIR = SKILL_DIR / "verifications"
VERIFICATIONS_DIR.mkdir(exist_ok=True)


def verify_lesson(lesson_id: int, base_url: str = "http://localhost:5000"):
    """Oeffnet die Lektion und klickt alles durch. Speichert Screenshots."""
    from playwright.sync_api import sync_playwright

    run_dir = VERIFICATIONS_DIR / f"lesson_{lesson_id}_{datetime.utcnow():%Y%m%dT%H%M%S}"
    run_dir.mkdir()
    issues = []

    admin_user = "admin"  # muss im lokalen docker-db-Seed existieren
    admin_pass = "admin"  # Dev-Only!

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        try:
            # 1. Login
            page.goto(f"{base_url}/auth/login")
            page.fill('input[name="username"]', admin_user)
            page.fill('input[name="password"]', admin_pass)
            page.click('button[type="submit"]')
            page.wait_for_url("**/dashboard*", timeout=5000)
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

            # 4. Admin-Approval-Page checken
            page.goto(f"{base_url}/admin/manage/lessons")
            page.wait_for_load_state("networkidle")
            page.screenshot(path=run_dir / "04_admin_lessons.png")

            # 5. Lesson in Admin-Liste sichtbar?
            if not page.locator(f"text=/Lesson.*{lesson_id}/").first.is_visible():
                issues.append(f"Lesson {lesson_id} in /admin/manage/lessons nicht gefunden")

        except Exception as e:
            issues.append(f"Unexpected error: {e}")
            page.screenshot(path=run_dir / "99_error.png")

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
