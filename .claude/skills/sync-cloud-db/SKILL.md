---
name: sync-cloud-db
description: >
  Synchronize content data between local DB and Cloud SQL on GCP via UPSERT.
  Use this skill proactively whenever content changes were made locally —
  for example after running translation scripts, import scripts,
  adding/editing lessons or content in the admin panel, or applying migrations.
  IMPORTANT: This skill ALWAYS pulls Cloud→Local FIRST before pushing Local→Cloud.
  Uses UPSERT (kein TRUNCATE) and NEVER touches user data, progress, purchases or SRS-Daten.
  Always ask the user for confirmation before syncing.
---

# Sync Content: Cloud SQL ↔ Lokale DB (UPSERT)

Synchronisiert Content-Daten **bidirektional** via UPSERT.
**PFLICHT-REIHENFOLGE: Immer Cloud→Lokal ZUERST, dann Lokal→Cloud.**

Grund: Der Admin kann auf japanese-learning.ch jederzeit Inhalte bearbeiten.
Ein blindes Lokal→Cloud wuerde diese Aenderungen ueberschreiben.

## CRITICAL SAFETY RULES

- **IMMER Cloud→Lokal ZUERST** — Vor jedem Push muss die lokale DB den Cloud-Stand haben.
- **KEIN TRUNCATE** — Verwende IMMER die UPSERT-Scripts.
- **Im Zweifel nachfragen** — Lieber einmal weniger aendern als User-Daten verlieren.

### Diese Tabellen werden NIEMALS veraendert (User-Daten):
- `user` — Produktions-User
- `user_lesson_progress` — Lernfortschritt
- `user_quiz_answer` — Quiz-Antworten
- `card_review_state` — SRS-Kartenfortschritt
- `review_log` — SRS-Review-Historie
- `user_srs_settings` — SRS-Einstellungen
- `lesson_purchase` / `course_purchase` — Kaeufe
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
- **Schritt A**: Cloud→Lokal (Produktionsdaten herunterladen)
- **Schritt B**: Lokal→Cloud (Lokale Aenderungen hochladen)
- Welche Tabellen geschuetzt sind (User-Daten)
- Dass UPSERT verwendet wird (kein Datenverlust)
Warte auf Bestaetigung.

### 2. Docker pruefen

Die lokale PostgreSQL muss laufen:
```bash
docker compose up db -d
```

### 3. Authorize local IP

```bash
gcloud sql instances patch jpl-psql \
  --authorized-networks=$(curl -s ifconfig.me)/32 \
  --project=healthy-coil-466105-d7 --quiet
```

### 4. DB-Migrationen pruefen (falls noetig)

```bash
# Lokal pruefen
PGPASSWORD="JapaneseApp2025!" psql -h localhost -U app_user -d japanese_learning -t -A -c "SELECT version_num FROM alembic_version;"
# Cloud pruefen
DB_PASS=$(gcloud secrets versions access latest --secret=db-password --project=healthy-coil-466105-d7)
PGPASSWORD="$DB_PASS" psql -h 34.65.56.56 -U app_user -d japanese_learning -t -A -c "SELECT version_num FROM alembic_version;"
```
Falls unterschiedlich: Schema-Aenderungen auf Cloud SQL manuell anwenden.

### 5. SCHRITT A: Cloud → Lokal (ZUERST!)

```bash
DB_PASS=$(gcloud secrets versions access latest --secret=db-password --project=healthy-coil-466105-d7)

# Dry Run
PYTHONIOENCODING=utf-8 PYTHONPATH=. python scripts/sync_from_cloud.py \
  --cloud-host 34.65.56.56 --cloud-password "$DB_PASS" --dry-run

# Live
PYTHONIOENCODING=utf-8 PYTHONPATH=. python scripts/sync_from_cloud.py \
  --cloud-host 34.65.56.56 --cloud-password "$DB_PASS"
```

Das Script:
- Liest alle Content-Tabellen von Cloud SQL
- Fuehrt UPSERT in die lokale DB aus
- Loescht lokale Zeilen die auf Cloud nicht mehr existieren
- Aktualisiert Sequences und Alembic-Version
- Bei Fehler: automatischer Rollback

### 6. SCHRITT B: Lokal → Cloud

```bash
# Dry Run
PYTHONIOENCODING=utf-8 PYTHONPATH=. python scripts/sync_content_upsert.py \
  --cloud-host 34.65.56.56 --cloud-password "$DB_PASS" --dry-run

# Live
PYTHONIOENCODING=utf-8 PYTHONPATH=. python scripts/sync_content_upsert.py \
  --cloud-host 34.65.56.56 --cloud-password "$DB_PASS"
```

### 7. ALWAYS close access

```bash
gcloud sql instances patch jpl-psql --clear-authorized-networks \
  --project=healthy-coil-466105-d7 --quiet
```

NEVER forget this step.

### 8. Summary

Report:
- Schritt A: Cloud→Lokal (row counts, upserts, deletes)
- Schritt B: Lokal→Cloud (row counts, upserts, deletes)
- Tables protected (user, progress, purchases — untouched)
- Cloud SQL access closed
