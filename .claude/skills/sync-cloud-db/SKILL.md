---
name: sync-cloud-db
description: >
  Synchronize local content data to Cloud SQL on GCP. Use this skill
  proactively whenever content changes were made locally — for example after
  running translation scripts, import scripts, adding/editing lessons or
  content in the admin panel, or applying migrations.
  IMPORTANT: This skill NEVER touches user data, progress, or purchases.
  Always ask the user for confirmation before syncing.
---

# Sync Local Content to Cloud SQL

Synchronize content data from local PostgreSQL to the production Cloud SQL.

## CRITICAL SAFETY RULES

### OBERSTE REGEL: Im Zweifel NICHT truncaten, sondern nachfragen!
- **Lieber einmal weniger löschen** als versehentlich User-Daten vernichten.
- Wenn du unsicher bist, ob eine Tabelle Content oder User-Daten enthält: **STOPP und frage den User.**
- Verwende IMMER die `--table=`-Flags beim Export (Whitelist-Ansatz), NIEMALS `--data-only` ohne Tabellen-Filter.
- Prüfe VOR jedem Truncate, dass du NUR die unten gelisteten Content-Tabellen löschst.
- Alte Versionen dieses Skills oder aus dem Konversations-Kontext geladene Snippets können veraltet sein — halte dich IMMER an diese Datei hier.

### NEVER sync these tables (User/Transaktionsdaten):
- `user` — Produktions-User (haben sich auf der Live-Seite registriert)
- `user_lesson_progress` — Lernfortschritt der Produktions-User
- `user_quiz_answer` — Quiz-Antworten der Produktions-User
- `card_review_state` — SRS-Kartenfortschritt der Produktions-User
- `review_log` — SRS-Review-Historie der Produktions-User
- `user_srs_settings` — SRS-Einstellungen der Produktions-User
- `lesson_purchase` — Kauf-Transaktionen
- `course_purchase` — Kurs-Kauf-Transaktionen
- `payment_transaction` — Zahlungsdaten
- `alembic_version` — Separat behandeln

### NUR diese Tabellen synchronisieren (Content-Daten):
- `lesson_category` — Kategorien
- `course` — Kurse
- `course_lessons` — Kurs-Lektions-Zuordnung (M:N)
- `lesson` — Lektionen
- `lesson_page` — Seiten
- `lesson_content` — Inhalte
- `lesson_prerequisite` — Voraussetzungen
- `quiz_question` — Quiz-Fragen
- `quiz_option` — Quiz-Antwortoptionen
- `kana` — Kana-Referenzdaten
- `kanji` — Kanji-Referenzdaten
- `vocabulary` — Vokabeln
- `grammar` — Grammatik

## Steps

### 1. Ask for confirmation

Tell the user exactly which tables will be synced and which are protected.
Wait for explicit confirmation before proceeding.

### 2. Compare local vs. Cloud counts

```bash
# Lokal
PGPASSWORD="JapaneseApp2025!" psql -h localhost -U app_user -d japanese_learning -c "
SELECT 'lessons' as entity, count(*) FROM lesson
UNION ALL SELECT 'content', count(*) FROM lesson_content
UNION ALL SELECT 'quiz_questions', count(*) FROM quiz_question
UNION ALL SELECT 'grammar', count(*) FROM grammar
UNION ALL SELECT 'vocabulary', count(*) FROM vocabulary
UNION ALL SELECT 'kana', count(*) FROM kana
UNION ALL SELECT 'kanji', count(*) FROM kanji
ORDER BY 1;
"
```

Then authorize IP and run the same query on Cloud SQL to compare.

### 3. Authorize local IP

```bash
gcloud sql instances patch jpl-psql \
  --authorized-networks=$(curl -s ifconfig.me)/32 \
  --project=healthy-coil-466105-d7 --quiet
```

### 4. Export ONLY content tables from local DB

```bash
PGPASSWORD="JapaneseApp2025!" pg_dump -h localhost -U app_user -d japanese_learning \
  --data-only --no-owner --no-acl --column-inserts \
  --table=lesson_category \
  --table=course \
  --table=course_lessons \
  --table=lesson \
  --table=lesson_page \
  --table=lesson_content \
  --table=lesson_prerequisite \
  --table=quiz_question \
  --table=quiz_option \
  --table=kana \
  --table=kanji \
  --table=vocabulary \
  --table=grammar \
  --file=/tmp/content_only_export.sql
```

### 5. Truncate ONLY content tables on Cloud SQL

```bash
DB_PASS=$(gcloud secrets versions access latest --secret=db-password --project=healthy-coil-466105-d7)
PGPASSWORD="$DB_PASS" psql -h 34.65.56.56 -U app_user -d japanese_learning -c "
-- NUR Content-Tabellen! User-Daten bleiben unangetastet.
TRUNCATE TABLE quiz_option, quiz_question, lesson_content, lesson_page,
  lesson_prerequisite, lesson, lesson_category, course, course_lessons,
  kana, kanji, vocabulary, grammar CASCADE;
"
```

### 6. Import content data

```bash
PGPASSWORD="$DB_PASS" psql -h 34.65.56.56 -U app_user -d japanese_learning \
  < /tmp/content_only_export.sql
```

### 7. Update sequences

```bash
PGPASSWORD="$DB_PASS" psql -h 34.65.56.56 -U app_user -d japanese_learning -c "
SELECT setval('lesson_category_id_seq', (SELECT COALESCE(MAX(id),1) FROM lesson_category));
SELECT setval('course_id_seq', (SELECT COALESCE(MAX(id),1) FROM course));
SELECT setval('lesson_id_seq', (SELECT COALESCE(MAX(id),1) FROM lesson));
SELECT setval('lesson_page_id_seq', (SELECT COALESCE(MAX(id),1) FROM lesson_page));
SELECT setval('lesson_content_id_seq', (SELECT COALESCE(MAX(id),1) FROM lesson_content));
SELECT setval('lesson_prerequisite_id_seq', (SELECT COALESCE(MAX(id),1) FROM lesson_prerequisite));
SELECT setval('quiz_question_id_seq', (SELECT COALESCE(MAX(id),1) FROM quiz_question));
SELECT setval('quiz_option_id_seq', (SELECT COALESCE(MAX(id),1) FROM quiz_option));
SELECT setval('kana_id_seq', (SELECT COALESCE(MAX(id),1) FROM kana));
SELECT setval('kanji_id_seq', (SELECT COALESCE(MAX(id),1) FROM kanji));
SELECT setval('vocabulary_id_seq', (SELECT COALESCE(MAX(id),1) FROM vocabulary));
SELECT setval('grammar_id_seq', (SELECT COALESCE(MAX(id),1) FROM grammar));
"
```

### 8. Verify counts match

Run the count query on Cloud SQL and compare with local.

### 9. Update alembic_version if needed

```bash
# Check local version
LOCAL_VER=$(PGPASSWORD="JapaneseApp2025!" psql -h localhost -U app_user -d japanese_learning -t -A -c "SELECT version_num FROM alembic_version;")
# Update cloud
PGPASSWORD="$DB_PASS" psql -h 34.65.56.56 -U app_user -d japanese_learning -c "
UPDATE alembic_version SET version_num = '$LOCAL_VER';
"
```

### 10. ALWAYS close access

```bash
gcloud sql instances patch jpl-psql --clear-authorized-networks \
  --project=healthy-coil-466105-d7 --quiet
```

NEVER forget this step.

### 11. Summary

Report:
- Tables synced (with row counts)
- Tables protected (user, progress, purchases — untouched)
- Cloud SQL access closed
