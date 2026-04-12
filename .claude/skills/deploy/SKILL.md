---
name: deploy
description: >
  Deploy japanese-learning.ch to Google Cloud Run. Use this skill proactively
  whenever the user says "deploy", "deployen", "live stellen", or after code
  changes that should on production go live. Also use after the user confirms
  that changes are ready for production.
disable-model-invocation: true
---

# Deploy to japanese-learning.ch

Deploy the Japanese Learning Website to Google Cloud Run (europe-west1).

## Steps

### 1. Git pruefen und pushen

1. Run `git status --short` — check for uncommitted code changes (.py, .html, .css, .js)
2. If there are uncommitted code changes, warn the user and ask if they want to commit first
3. Run `git log --oneline origin/main..HEAD` — check for unpushed commits
4. If there are unpushed commits, run `git push`

### 2. Docker Image bauen

```bash
gcloud builds submit --config=cloudbuild.yaml \
  --project=healthy-coil-466105-d7 \
  --account=claudio.lutz.cv@gmail.com .
```

Wait for `STATUS: SUCCESS`. If it fails, show the error and stop.

### 3. Deploy nach Cloud Run

```bash
gcloud run services update japanese-learning-app \
  --image=europe-west6-docker.pkg.dev/healthy-coil-466105-d7/app-images/japanese-learning-app:latest \
  --region=europe-west1 \
  --project=healthy-coil-466105-d7 \
  --account=claudio.lutz.cv@gmail.com
```

### 4. Verifizieren

```bash
curl -s -o /dev/null -w "%{http_code}" https://japanese-learning.ch/
```

Expected: 200.

### 5. Zusammenfassung

Report: Git status, Build duration, Revision name, HTTP status of https://japanese-learning.ch
