"""HTTP-basierte Verifikation fuer Lesson 142 (Fallback, weil MCP-Browser belegt)."""
import re
import sys
import requests

BASE = "http://localhost:5000"
LESSON_ID = 142

session = requests.Session()

# 1. CSRF-Token aus Login-Page holen
r = session.get(f"{BASE}/login")
if r.status_code != 200:
    print(f"[FAIL] Login page: HTTP {r.status_code}")
    sys.exit(1)

m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', r.text)
if not m:
    print("[FAIL] CSRF-Token auf Login-Page nicht gefunden")
    sys.exit(1)
csrf = m.group(1)

# 2. Login als admin (Passwort aus .env)
import os
from dotenv import load_dotenv
load_dotenv()
admin_pw = os.environ.get("ADMIN_PASSWORD", "")
admin_email = os.environ.get("ADMIN_EMAIL", "admin@example.com")
r = session.post(f"{BASE}/login", data={
    "csrf_token": csrf,
    "email": admin_email,
    "password": admin_pw,
}, allow_redirects=True)

if "/login" in r.url:
    print(f"[FAIL] Login fehlgeschlagen — URL: {r.url}")
    sys.exit(2)

print(f"[OK] Logged in. Redirected to: {r.url}")

# 3. Lesson-Seite laden
r = session.get(f"{BASE}/lessons/{LESSON_ID}")
print(f"[INFO] /lessons/{LESSON_ID}: HTTP {r.status_code}")
if r.status_code != 200:
    print(f"[FAIL] Lesson-Page gab HTTP {r.status_code}")
    sys.exit(3)

html = r.text
issues = []

# 4. Inhaltsprüfung
checks = [
    ("Essen im Restaurant", "Lesson title"),
    ("メニュー", "Vokabel Menü"),
    ("水", "Vokabel Wasser"),
    ("おいしい", "Vokabel lecker"),
    ("ください", "Grammatik-Phrase"),
    ("höfliche Bitte", "Grammatik-Explanation"),
    ("Wasser", "DE-Bedeutung"),
]
for needle, what in checks:
    if needle not in html:
        issues.append(f"{what}: '{needle}' NICHT im HTML gefunden")

# 5. Umlaut-Check (kein ASCII-Fallback)
bad_patterns = ["Einfuehrung", "Koestlich", "Hoeflich", "Getraenk"]
for p in bad_patterns:
    if p in html:
        issues.append(f"ASCII-Fallback gefunden: '{p}' — sollte Umlaut sein")

# 6. Admin-Lessons-Liste
r = session.get(f"{BASE}/admin/manage/lessons")
if r.status_code == 200:
    if f"Essen im Restaurant" not in r.text:
        issues.append("Lesson 142 nicht in /admin/manage/lessons sichtbar")
    else:
        print("[OK] Lesson in Admin-Liste sichtbar")
else:
    issues.append(f"/admin/manage/lessons: HTTP {r.status_code}")

# 7. Report
if issues:
    print("\n[FAIL] Issues:")
    for i, iss in enumerate(issues, 1):
        print(f"  {i}. {iss}")
    sys.exit(1)
else:
    print("\n[PASS] Alle HTTP-Checks bestanden.")
