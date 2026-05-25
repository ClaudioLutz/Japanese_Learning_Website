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

> **Ausfuehrungsort:** Die Server-Schritte (2–6) laufen auf dem Heim-Server `hp-ubuntu`.
> Von einer entfernten Dev-Maschine (z.B. Windows) jeweils via `ssh hp-ubuntu "<command>"`
> ausfuehren; `git push` davor von der Dev-Maschine.

## Steps

### 1. Git pruefen, committen, pushen
1. `git status --short` — uncommitted Code-Aenderungen (.py/.html/.css/.js)?
2. Bei uncommitted Aenderungen: User fragen, ob committen — dann committen (deutsche Message).
3. `git log --oneline origin/main..HEAD` — unpushed commits? Falls ja: `git push`.

### 2. Server-Checkout auf Repo-Stand bringen (Sync-Check)
Stellt sicher, dass der Code auf dem Heim-Server dem gepushten Stand entspricht —
**ohne diesen Schritt baut Schritt 3 den alten Code.** Meldet zugleich, ob der
Server-Checkout hinterherhinkte und ob er Skill-/Code-Aenderungen gegenueber dem
Repo hatte.
```bash
cd /home/hp-ubuntu/git/Japanese_Learning_Website
git fetch origin
# Drift-Report: steht der Server auf origin/main?
if [ "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)" ]; then
  echo "OK Server ist auf Repo-Stand (HEAD = origin/main)"
else
  echo "WARN Server hinkt hinterher — fehlende Commits (auch Skills unter .claude/skills/):"
  git log --oneline HEAD..origin/main
fi
# Uncommittete Aenderungen auf dem Server-Checkout? (sollten keine sein)
git status --short
# Auf den gepushten Stand ziehen (nur Fast-Forward):
git pull --ff-only
```
Bei `git status`-Ausgabe (uncommittete Server-Aenderungen) oder fehlgeschlagenem
`--ff-only`: **stoppen und klaeren** — nicht blind ueberschreiben (gleiches Prinzip wie
die DB-Sync-Reihenfolge: Server-Edits nie blind verwerfen). Dieser Schritt haelt zugleich
die Projekt-Skills unter `.claude/skills/` zwischen Dev-Maschine und Server synchron.

### 3. Image neu bauen
```bash
cd /home/hp-ubuntu/git/Japanese_Learning_Website
sudo docker compose build web
```
Auf Erfolg warten. Bei Fehler: Ausgabe zeigen und stoppen.

### 4. Container mit neuem Image neu starten
```bash
sudo docker compose up -d --no-deps web
```
Der Entrypoint fuehrt automatisch `flask db upgrade` (Migrationen) aus und startet Gunicorn.

### 5. Auf Boot warten + verifizieren
```bash
# Boot dauert ~60s (Entrypoint wartet auf DB + Migrationen, dann Gunicorn)
curl -sS --retry 150 --retry-delay 1 --retry-all-errors -o /dev/null -w "lokal: %{http_code}\n" http://localhost:5000/
# Live ueber die Domain (durch Cloudflare):
curl -s -o /dev/null -w "live: %{http_code} via %{remote_ip}\n" https://japanese-learning.ch/
```
Erwartung: beide **200**, live-IP ist eine Cloudflare-IP (104.x / 172.67.x).

### 6. Health-Check
```bash
systemctl is-active cloudflared
sudo docker ps --filter name=japanese_app --format '{{.Names}}: {{.Status}}'
```

### 7. Zusammenfassung
Report: Git-Status, **Server-Sync (war der Checkout hinterher? jetzt auf origin/main?)**,
Build-Erfolg, lokaler + Live-HTTP-Status, Tunnel/Container-Status.
