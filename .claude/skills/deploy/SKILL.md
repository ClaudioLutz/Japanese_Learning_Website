---
name: deploy
description: >
  Neue Code-Aenderungen auf den self-hosted japanese-learning.ch Heim-Server
  bringen (Docker-Image neu bauen + Container neu starten). Use this skill
  proactively whenever the user says "deploy", "deployen", "live stellen", or
  after code changes that should go live in production. Also use after the user
  confirms that changes are ready for production.
disable-model-invocation: true
---

# Deploy auf japanese-learning.ch (Self-Hosted)

Die Seite laeuft self-hosted auf diesem Rechner:
**Internet → Cloudflare-Tunnel → `japanese_app` Docker-Container → lokale Postgres-DB.**
Ein "Deploy" = Code committen, Image neu bauen, Container neu starten. **Kein GCloud mehr.**

> DB-Daten (lokale Postgres-Volume) und Medien (Volume `app/static/uploads`) liegen
> AUSSERHALB des Images und sind von einem Rebuild NICHT betroffen — nur der Code
> wird ersetzt.

## Steps

### 1. Git pruefen, committen, pushen
1. `git status --short` — uncommitted Code-Aenderungen (.py/.html/.css/.js)?
2. Bei uncommitted Aenderungen: User fragen, ob committen — dann committen (deutsche Message).
3. `git log --oneline origin/main..HEAD` — unpushed commits? Falls ja: `git push`.

### 2. Image neu bauen
```bash
cd /home/hp-ubuntu/git/Japanese_Learning_Website
sudo docker compose build web
```
Auf Erfolg warten. Bei Fehler: Ausgabe zeigen und stoppen.

### 3. Container mit neuem Image neu starten
```bash
sudo docker compose up -d --no-deps web
```
Der Entrypoint fuehrt automatisch `flask db upgrade` (Migrationen) aus und startet Gunicorn.

### 4. Auf Boot warten + verifizieren
```bash
# Boot dauert ~60s (Entrypoint wartet auf DB + Migrationen, dann Gunicorn)
curl -sS --retry 150 --retry-delay 1 --retry-all-errors -o /dev/null -w "lokal: %{http_code}\n" http://localhost:5000/
# Live ueber die Domain (durch Cloudflare):
curl -s -o /dev/null -w "live: %{http_code} via %{remote_ip}\n" https://japanese-learning.ch/
```
Erwartung: beide **200**, live-IP ist eine Cloudflare-IP (104.x / 172.67.x).

### 5. Health-Check
```bash
systemctl is-active cloudflared
sudo docker ps --filter name=japanese_app --format '{{.Names}}: {{.Status}}'
```

### 6. Zusammenfassung
Report: Git-Status, Build-Erfolg, lokaler + Live-HTTP-Status, Tunnel/Container-Status.
