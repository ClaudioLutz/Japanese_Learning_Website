---
name: sync-cloud-db
description: >
  Synchronize local PostgreSQL database to Cloud SQL on GCP. Use this skill
  proactively whenever database changes were made locally — for example after
  running translation scripts, import scripts, adding/editing lessons or
  content via the admin panel, running INSERT/UPDATE/DELETE queries, or
  applying migrations. Always ask the user for confirmation before syncing.
---

# Sync Local DB to Cloud SQL

Synchronize the local PostgreSQL database to the production Cloud SQL instance.

## Important

- Always ask the user for confirmation before executing
- The Cloud SQL instance is `jpl-psql` in project `healthy-coil-466105-d7`
- Public IP: `34.65.110.18` (was `34.65.56.56`, verify with gcloud if needed)
- DB password is in Secret Manager under `db-password`

## Steps

### 1. Verify what changed locally

Run a quick count comparison to understand what needs syncing:

```bash
PGPASSWORD="JapaneseApp2025!" psql -h localhost -U app_user -d japanese_learning -c "
SELECT 'users' as entity, count(*) FROM \"user\"
UNION ALL SELECT 'lessons', count(*) FROM lesson
UNION ALL SELECT 'categories', count(*) FROM lesson_category
UNION ALL SELECT 'courses', count(*) FROM course
UNION ALL SELECT 'content', count(*) FROM lesson_content
UNION ALL SELECT 'quiz_questions', count(*) FROM quiz_question
UNION ALL SELECT 'grammar', count(*) FROM grammar
UNION ALL SELECT 'vocabulary', count(*) FROM vocabulary
ORDER BY 1;
"
```

### 2. Authorize local IP for Cloud SQL access

```bash
gcloud sql instances patch jpl-psql \
  --authorized-networks=$(curl -s ifconfig.me)/32 \
  --project=healthy-coil-466105-d7 --quiet
```

### 3. Export local data

```bash
PGPASSWORD="JapaneseApp2025!" pg_dump -h localhost -U app_user -d japanese_learning \
  --data-only --no-owner --no-acl --column-inserts --format=plain \
  --file=/tmp/japanese_learning_inserts.sql
```

### 4. Import to Cloud SQL

```bash
DB_PASS=$(gcloud secrets versions access latest --secret=db-password --project=healthy-coil-466105-d7)

# Truncate all tables (careful!)
PGPASSWORD="$DB_PASS" psql -h 34.65.56.56 -U app_user -d japanese_learning -c "
TRUNCATE TABLE user_quiz_answer, quiz_option, quiz_question, lesson_content,
  lesson_page, lesson_prerequisite, user_lesson_progress, lesson_purchase,
  course_purchase, payment_transaction, lesson, lesson_category, course,
  kana, kanji, vocabulary, grammar, \"user\" CASCADE;
"

# Import
PGPASSWORD="$DB_PASS" psql -h 34.65.56.56 -U app_user -d japanese_learning \
  < /tmp/japanese_learning_inserts.sql

# Update sequences
PGPASSWORD="$DB_PASS" psql -h 34.65.56.56 -U app_user -d japanese_learning -c "
SELECT setval('grammar_id_seq', (SELECT COALESCE(MAX(id),1) FROM grammar));
SELECT setval('vocabulary_id_seq', (SELECT COALESCE(MAX(id),1) FROM vocabulary));
SELECT setval('lesson_id_seq', (SELECT COALESCE(MAX(id),1) FROM lesson));
SELECT setval('lesson_content_id_seq', (SELECT COALESCE(MAX(id),1) FROM lesson_content));
SELECT setval('quiz_question_id_seq', (SELECT COALESCE(MAX(id),1) FROM quiz_question));
SELECT setval('quiz_option_id_seq', (SELECT COALESCE(MAX(id),1) FROM quiz_option));
SELECT setval('user_id_seq', (SELECT COALESCE(MAX(id),1) FROM \"user\"));
"
```

### 5. Verify counts on Cloud SQL

Run the same count query on Cloud SQL and compare with local.

### 6. IMPORTANT: Remove authorized network

```bash
gcloud sql instances patch jpl-psql --clear-authorized-networks \
  --project=healthy-coil-466105-d7 --quiet
```

NEVER forget this step — leaving the IP open is a security risk.

### 7. Update alembic_version if migrations were applied

```bash
# Check local alembic version
PGPASSWORD="JapaneseApp2025!" psql -h localhost -U app_user -d japanese_learning -c "SELECT version_num FROM alembic_version;"
# Set same version on Cloud SQL (during step 4, before clearing network)
```
