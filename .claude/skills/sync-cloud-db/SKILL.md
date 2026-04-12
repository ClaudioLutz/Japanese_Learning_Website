---
name: sync-cloud-db
description: >
  Synchronize local content data to Cloud SQL on GCP via UPSERT.
  Use this skill proactively whenever content changes were made locally —
  for example after running translation scripts, import scripts,
  adding/editing lessons or content in the admin panel, or applying migrations.
  IMPORTANT: This skill uses UPSERT (kein TRUNCATE) and NEVER touches
  user data, progress, purchases or SRS-Daten.
  Always ask the user for confirmation before syncing.
---

# Sync Local Content to Cloud SQL (UPSERT)

Synchronisiert Content-Daten von der lokalen PostgreSQL zur Cloud SQL via
**INSERT ... ON CONFLICT DO UPDATE** (UPSERT). Kein TRUNCATE, kein CASCADE,
keine User-Daten gehen verloren.

## CRITICAL SAFETY RULES

- **KEIN TRUNCATE** — Verwende IMMER das UPSERT-Script `scripts/sync_content_upsert.py`.
- **Im Zweifel nachfragen** — Lieber einmal weniger ändern als User-Daten verlieren.
- Alte Versionen dieses Skills oder Konversations-Kontext-Snippets können veraltet sein.
  Halte dich IMMER an diese Datei hier.

### Diese Tabellen werden NIEMALS verändert (User-Daten):
- `user` — Produktions-User
- `user_lesson_progress` — Lernfortschritt
- `user_quiz_answer` — Quiz-Antworten
- `card_review_state` — SRS-Kartenfortschritt
- `review_log` — SRS-Review-Historie
- `user_srs_settings` — SRS-Einstellungen
- `lesson_purchase` / `course_purchase` — Käufe
- `payment_transaction` — Zahlungsdaten

### Diese Content-Tabellen werden synchronisiert (UPSERT):
- `kana`, `kanji`, `vocabulary`, `grammar` — Referenzdaten
- `lesson_category`, `course`, `course_lessons` — Kurse/Kategorien
- `lesson`, `lesson_page`, `lesson_content` — Lektionen/Inhalte
- `lesson_prerequisite` — Voraussetzungen
- `quiz_question`, `quiz_option` — Quiz-Daten

## Steps

### 1. Ask for confirmation

Informiere den User:
- Welche Tabellen synchronisiert werden (Content)
- Welche Tabellen geschützt sind (User-Daten)
- Dass UPSERT verwendet wird (kein Datenverlust)
Warte auf Bestätigung.

### 2. Authorize local IP

```bash
gcloud sql instances patch jpl-psql \
  --authorized-networks=$(curl -s ifconfig.me)/32 \
  --project=healthy-coil-466105-d7 --quiet
```

### 3. DB-Migrationen auf Cloud SQL anwenden (falls nötig)

Vor dem Sync prüfen ob neue Spalten/Tabellen nötig sind:
```bash
# Lokal prüfen
PGPASSWORD="JapaneseApp2025!" psql -h localhost -U app_user -d japanese_learning -t -A -c "SELECT version_num FROM alembic_version;"
# Cloud prüfen
DB_PASS=$(gcloud secrets versions access latest --secret=db-password --project=healthy-coil-466105-d7)
PGPASSWORD="$DB_PASS" psql -h 34.65.56.56 -U app_user -d japanese_learning -t -A -c "SELECT version_num FROM alembic_version;"
```
Falls die Versionen unterschiedlich sind, müssen Schema-Änderungen (ALTER TABLE etc.)
manuell auf Cloud SQL angewendet werden BEVOR der Sync läuft.

### 4. UPSERT-Sync ausführen

```bash
# Dry Run zuerst (empfohlen)
DB_PASS=$(gcloud secrets versions access latest --secret=db-password --project=healthy-coil-466105-d7)
PYTHONIOENCODING=utf-8 PYTHONPATH=. python scripts/sync_content_upsert.py \
  --cloud-host 34.65.56.56 --cloud-password "$DB_PASS" --dry-run

# Wenn Dry Run OK: Live ausführen
PYTHONIOENCODING=utf-8 PYTHONPATH=. python scripts/sync_content_upsert.py \
  --cloud-host 34.65.56.56 --cloud-password "$DB_PASS"
```

Das Script:
- Liest alle Content-Tabellen aus der lokalen DB
- Führt INSERT ... ON CONFLICT DO UPDATE auf Cloud SQL aus
- Löscht Zeilen auf Cloud die lokal nicht mehr existieren (nur Content-Tabellen!)
- Aktualisiert Sequences und Alembic-Version
- Bei Fehler: automatischer Rollback, keine Änderungen

### 5. ALWAYS close access

```bash
gcloud sql instances patch jpl-psql --clear-authorized-networks \
  --project=healthy-coil-466105-d7 --quiet
```

NEVER forget this step.

### 6. Summary

Report:
- Tables synced (with row counts, upserts, deletes)
- Tables protected (user, progress, purchases — untouched)
- Cloud SQL access closed
