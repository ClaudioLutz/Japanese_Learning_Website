---
name: status
description: >
  Show a comprehensive project status overview. Use this skill proactively
  at the beginning of a new session, after /compact, or when the user asks
  "wo stehen wir?", "status", "Uebersicht", or seems disoriented about
  the current state of the project.
---

# Project Status Overview

Gather and display the current state of the Japanese Learning Website project.
Die Seite ist **self-hosted**: Internet → Cloudflare-Tunnel → Docker-Container
`japanese_app` → lokale Postgres `postgres_db`. Kein GCloud-Hosting mehr.

## Checks to perform

### 1. Git Status
```bash
cd /home/hp-ubuntu/git/Japanese_Learning_Website
git status --short
git log --oneline -5
git log --oneline origin/main..HEAD
```
Report: branch, uncommitted changes, unpushed commits, last 5 commits.

### 2. Lokale App + Container
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/ 2>/dev/null || echo "not running"
sudo docker ps --filter name=japanese_app --filter name=postgres_db --format '{{.Names}}: {{.Status}}'
```

### 3. Produktions-DB (lokal) — Zeilenzahlen
```bash
sudo docker exec postgres_db psql -U app_user -d japanese_learning -c "
SELECT 'users' as entity, count(*) FROM \"user\"
UNION ALL SELECT 'lessons', count(*) FROM lesson
UNION ALL SELECT 'content', count(*) FROM lesson_content
UNION ALL SELECT 'quiz_questions', count(*) FROM quiz_question
UNION ALL SELECT 'grammar', count(*) FROM grammar
UNION ALL SELECT 'vocabulary', count(*) FROM vocabulary
ORDER BY 1;" 2>/dev/null || echo "DB not reachable"
```

### 4. Live (Heim-Server ueber Cloudflare-Tunnel)
```bash
# Kommt die Seite ueber Cloudflare? (erwartet: HTTP 200, server: cloudflare)
curl -sI https://japanese-learning.ch/ | grep -iE '^HTTP|^server:'
# Tunnel-Dienst + Backup-Timer aktiv?
systemctl is-active cloudflared
systemctl is-active jpl-db-backup.timer
```

### 5. SEO Health (leichtgewichtig)
```bash
curl -s -o /dev/null -w "robots:%{http_code}\n" https://japanese-learning.ch/robots.txt
curl -s -o /dev/null -w "sitemap:%{http_code}\n" https://japanese-learning.ch/sitemap.xml
curl -s https://japanese-learning.ch/sitemap.xml | grep -c '<loc>'
curl -s https://japanese-learning.ch/ | grep -oE '<title>[^<]+</title>'
```
Erwartung: HTTP 200 fuer beide, ~50+ URLs in Sitemap, Title enthaelt "Japanisch lernen".

### 6. Backups
```bash
ls -lht /home/hp-ubuntu/jpl-backups/jpl_*.sql.gz 2>/dev/null | head -3
```

### 7. Summary Table
| Bereich | Status |
|---|---|
| Git | branch, clean/dirty, pushed/unpushed |
| Lokal | app running?, Container-Status, DB counts |
| Live | HTTP via Cloudflare, Tunnel aktiv? |
| SEO | robots/sitemap status, Sitemap-URLs, Live-Title |
| Backups | letztes DB-Backup |
| Letzter Commit | message + hash |
