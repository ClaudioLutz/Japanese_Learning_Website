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

## Checks to perform

### 1. Git Status

```bash
git status --short
git log --oneline -5
git log --oneline origin/main..HEAD
```

Report: Current branch, uncommitted changes, unpushed commits, last 5 commits.

### 2. Local App

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/ 2>/dev/null || echo "not running"
```

### 3. Local Database Counts

```bash
PGPASSWORD="JapaneseApp2025!" psql -h localhost -U app_user -d japanese_learning -c "
SELECT 'users' as entity, count(*) FROM \"user\"
UNION ALL SELECT 'lessons', count(*) FROM lesson
UNION ALL SELECT 'content', count(*) FROM lesson_content
UNION ALL SELECT 'quiz_questions', count(*) FROM quiz_question
UNION ALL SELECT 'grammar', count(*) FROM grammar
UNION ALL SELECT 'vocabulary', count(*) FROM vocabulary
ORDER BY 1;
" 2>/dev/null || echo "Local DB not reachable"
```

### 4. Production (Cloud Run)

```bash
curl -s -o /dev/null -w "%{http_code}" https://japanese-learning.ch/
gcloud run revisions list --service=japanese-learning-app \
  --region=europe-west1 --project=healthy-coil-466105-d7 \
  --account=claudio.lutz.cv@gmail.com --limit=1 --format="value(name,status.conditions[0].status)" 2>/dev/null
```

### 5. Summary Table

Present results as a compact table:

| Bereich | Status |
|---|---|
| Git | branch, clean/dirty, pushed/unpushed |
| Lokal | running/stopped, DB counts |
| Production | HTTP status, aktive Revision |
| Letzter Commit | message + hash |
