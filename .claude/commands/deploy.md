Deploy japanese-learning.ch to Google Cloud Run.

Follow these steps in order. Stop and report if any step fails.

## Step 1: Git Status pruefen und pushen

1. Run `git status --short` to check for uncommitted changes (ignore untracked files like *.png)
2. Run `git log --oneline origin/main..HEAD` to check for unpushed commits
3. If there are unpushed commits, run `git push`
4. If there are uncommitted code changes (modified .py, .html, .css, .js files), warn the user and ask if they want to commit first

## Step 2: Docker Image bauen

Run this command (timeout 10 minutes):
```
gcloud builds submit --config=cloudbuild.yaml --project=healthy-coil-466105-d7 --account=claudio.lutz.cv@gmail.com .
```
Wait for STATUS: SUCCESS. If it fails, show the error and stop.

## Step 3: Deploy nach Cloud Run (europe-west1)

Run this command (timeout 5 minutes):
```
gcloud run services update japanese-learning-app \
  --image=europe-west6-docker.pkg.dev/healthy-coil-466105-d7/app-images/japanese-learning-app:latest \
  --region=europe-west1 \
  --project=healthy-coil-466105-d7 \
  --account=claudio.lutz.cv@gmail.com
```

## Step 4: Domain verifizieren

Run: `curl -s -o /dev/null -w "%{http_code}" https://japanese-learning.ch/`

Expected: 200. Report the revision name and confirm the site is live.

## Summary

Report: Git status, Image build duration, Revision name, HTTP status of https://japanese-learning.ch
