---
name: cloud-db
description: >
  Connect to the production Cloud SQL database to run queries. Use this skill
  whenever the user wants to check production data, run a query on the live
  database, verify data after a sync, or debug production issues. Also use
  proactively when you need to verify that production data matches expectations
  after a deployment or sync.
---

# Cloud SQL Access

Securely connect to the production Cloud SQL PostgreSQL database, run queries,
and close the connection.

## Connection Details

- Instance: `jpl-psql` (europe-west6)
- Public IP: `34.65.56.56`
- Database: `japanese_learning`
- User: `app_user`
- Password: Secret Manager `db-password`
- Project: `healthy-coil-466105-d7`

## Steps

### 1. Authorize local IP

```bash
gcloud sql instances patch jpl-psql \
  --authorized-networks=$(curl -s ifconfig.me)/32 \
  --project=healthy-coil-466105-d7 --quiet
```

### 2. Get password and run query

```bash
DB_PASS=$(gcloud secrets versions access latest --secret=db-password \
  --project=healthy-coil-466105-d7)
PGPASSWORD="$DB_PASS" psql -h 34.65.56.56 -U app_user -d japanese_learning \
  -c "YOUR QUERY HERE"
```

### 3. ALWAYS close access afterwards

```bash
gcloud sql instances patch jpl-psql --clear-authorized-networks \
  --project=healthy-coil-466105-d7 --quiet
```

## Security Rules

- NEVER leave the authorized network open after finishing
- NEVER run UPDATE/DELETE without WHERE clause
- For write operations: always SELECT first to verify affected rows
- Prefer READ-ONLY queries unless explicitly asked to modify data
