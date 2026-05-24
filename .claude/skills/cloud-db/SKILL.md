---
name: cloud-db
description: >
  Connect to the production database to run queries. Use this skill whenever the
  user wants to check production data, run a query on the live database, verify
  data, or debug production issues. NOTE: Production is now the LOCAL Postgres on
  this self-hosted machine — "cloud" in the name is historical (Cloud SQL was
  deleted after the Self-Hosting-Umzug 2026-05).
---

# Produktions-DB-Zugriff (lokal, self-hosted)

Seit dem Self-Hosting-Umzug ist die **Produktions-DB die lokale Postgres** im
Docker-Container `postgres_db` auf diesem Rechner. **Es gibt kein Cloud SQL mehr.**
Diese DB ist die EINZIGE produktive Quelle der Wahrheit.

## Connection
- Container: `postgres_db`
- Database: `japanese_learning`
- User: `app_user`
- Host-Port (gemappt): `localhost:5432`

## Query ausfuehren

Bevorzugt direkt im Container (keine Host-psql noetig):
```bash
sudo docker exec postgres_db psql -U app_user -d japanese_learning -c "YOUR QUERY"
```
Alternativ ueber den gemappten Host-Port:
```bash
PGPASSWORD="JapaneseApp2025!" psql -h localhost -p 5432 -U app_user -d japanese_learning -c "YOUR QUERY"
```

## Security Rules (unveraendert wichtig!)
- NEVER run UPDATE/DELETE without WHERE clause
- NEVER modify these tables without explicit user confirmation:
  - `user`, `user_lesson_progress`, `user_quiz_answer`, `card_review_state`,
    `review_log`, `user_achievement`, `lesson_purchase`, `course_purchase`,
    `payment_transaction`
- For write operations: always SELECT first to verify affected rows
- **Es gibt keinen Cloud-Fallback mehr.** Vor riskanten Schreib-Aktionen ein Backup ziehen:
  ```bash
  sudo /usr/local/bin/jpl-db-backup.sh    # → /home/hp-ubuntu/jpl-backups/jpl_<ts>.sql.gz
  ```
- Prefer READ-ONLY queries unless explicitly asked to modify data
- Bei Zweifeln: lieber nachfragen als Daten verlieren
