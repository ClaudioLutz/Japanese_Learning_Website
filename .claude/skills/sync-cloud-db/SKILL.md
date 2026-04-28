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
**PFLICHT-REIHENFOLGE: Cloud→Lokal ZUERST, dann Lokal→Cloud, dann Assets→GCS.**

Grund: Der Admin kann auf japanese-learning.ch jederzeit Inhalte editieren.
Ein blindes Lokal→Cloud wuerde diese Aenderungen ueberschreiben.

## CRITICAL SAFETY RULES

- **IMMER Cloud→Lokal ZUERST** — Vor jedem Push muss die lokale DB den Cloud-Stand haben.
- **KEIN TRUNCATE** — Verwende IMMER die UPSERT-Scripts.
- **Lokale ungesicherte SQL-Edits werden durch den Pull ueberschrieben** — siehe Schritt 1.
- **IP NACH Sync IMMER schliessen** — auch wenn was crasht. Siehe "Wenn etwas schief geht" am Ende.
- **Im Zweifel nachfragen** — Lieber einmal weniger aendern als User-Daten verlieren.

### Eingebaute Schutzmechanismen (Stand 2026-04-25)

`sync_content_upsert.py` ist mehrfach abgesichert. In Aktivierungs-Reihenfolge:

1. **Drift-Check** — Vergleicht Cloud-Stand (Count, MAX(id), MAX(updated_at)) mit `.last_cloud_sync.json` (Snapshot vom letzten Pull). Bei Abweichung: Abbruch mit Aufforderung erneut zu pullen.
2. **User-Daten-Backup** — Vor jedem Push werden alle User-Tabellen (siehe Liste unten) per `pg_dump` nach `backups/user_data/cloud_pre_push_<timestamp>.sql` gesichert.
3. **Kaufschutz / Deletion-Blocker** — Bevor das Skript eine Cloud-Content-Zeile loescht, prueft es ob User-Daten darauf zeigen (Progress, Quiz-Answer, SRS-State, Review-Log, Lesson-/Course-Purchase). Bei Treffer: Abbruch mit Liste der betroffenen IDs.
4. **DB-FK RESTRICT** — Migration `d8e2c1a4f6b3` hat Purchase-FKs auf `ON DELETE RESTRICT` umgestellt. Selbst wenn alle anderen Schichten umgangen werden, blockt die DB jeden DELETE auf einer Lesson/Course mit aktiven Kaeufen.

Override-Flags (nur Notfall): `--skip-drift-check`, `--skip-backup`, `--force-delete-user-data`.

### NIEMALS veraenderte User-Tabellen
`user`, `user_lesson_progress`, `user_quiz_answer`, `card_review_state`,
`review_log`, `user_srs_settings`, `user_achievement`,
`daily_review_aggregate`, `lesson_purchase`, `course_purchase`,
`payment_transaction`.

### Synchronisierte Content-Tabellen (UPSERT)
`kana`, `kanji`, `vocabulary`, `grammar`, `lesson_category`, `course`,
`course_lessons`, `lesson`, `lesson_page`, `lesson_content`,
`lesson_prerequisite`, `quiz_question`, `quiz_option`.

---

## Steps

### 1. Bestaetigung + lokale-Edits-Check

Informiere den User:
- **Schritt A**: Cloud→Lokal (Produktionsdaten herunterladen)
- **Schritt B**: Lokal→Cloud (Lokale Aenderungen hochladen)
- **Schritt C**: Assets→GCS (Bilder/Audios in den Bucket)
- User-Tabellen sind geschuetzt, UPSERT (kein Datenverlust)

**WICHTIG: Vor dem Pull explizit fragen** ob lokale DB-Edits per psql/SQL gemacht
wurden, die noch NICHT in Cloud sind (typisch: ad-hoc UPDATE auf einer Lesson).
Solche Edits werden durch den Cloud→Lokal-Pull **ueberschrieben**.

Plan:
- Wenn ja: User listet die Edits, sie werden NACH dem Pull erneut angewendet,
  bevor Schritt B (Push) laeuft.
- Wenn nein: direkt durchstarten.

Beispiel aus 2026-04-28: lokal `UPDATE lesson SET allow_guest_access=true WHERE
id IN (162,171,172,173)`. Pull setzt diese 4 Rows wieder auf `false`. Re-Apply
nach Pull, sonst geht der Fix nie in die Cloud.

### 2. Vorbereitung: Docker + IP autorisieren

```bash
# Lokale Postgres muss laufen
docker compose up db -d

# IP fuer Cloud SQL freischalten
gcloud sql instances patch jpl-psql \
  --authorized-networks=$(curl -s ifconfig.me)/32 \
  --project=healthy-coil-466105-d7 --quiet
```

### 3. Schema-Drift pruefen (Pflicht VOR Pull/Push)

```bash
DB_PASS=$(gcloud secrets versions access latest --secret=db-password --project=healthy-coil-466105-d7)

LOCAL_VER=$(PGPASSWORD="JapaneseApp2025!" psql -h localhost -U app_user \
  -d japanese_learning -t -A -c "SELECT version_num FROM alembic_version;")
CLOUD_VER=$(PGPASSWORD="$DB_PASS" psql -h 34.65.56.56 -U app_user \
  -d japanese_learning -t -A -c "SELECT version_num FROM alembic_version;")
echo "Lokal: $LOCAL_VER  Cloud: $CLOUD_VER"
```

- **Lokal === Cloud** → Sync gefahrlos.
- **Lokal > Cloud** (typisch nach `flask db migrate`): VOR dem Push Cloud-Migration anwenden:
  ```bash
  DATABASE_URL="postgresql://app_user:${DB_PASS}@34.65.56.56:5432/japanese_learning" flask db upgrade
  ```
- **Cloud > Lokal**: lokal `flask db upgrade` ausfuehren.

Begruendung: Der Push setzt `alembic_version` auf den lokalen Stand. Wenn die
physischen Migrationen fehlen, glaubt Alembic faelschlicherweise sie seien
angewendet. Bei Tabellen, die physisch existieren aber alembic_version
hinterherhinkt: `flask db stamp <revision>` setzt nur den Marker.

### 4. SCHRITT A: Cloud → Lokal (ZUERST!)

```bash
# Dry Run
PYTHONIOENCODING=utf-8 PYTHONPATH=. python scripts/sync_from_cloud.py \
  --cloud-host 34.65.56.56 --cloud-password "$DB_PASS" --dry-run

# Live
PYTHONIOENCODING=utf-8 PYTHONPATH=. python scripts/sync_from_cloud.py \
  --cloud-host 34.65.56.56 --cloud-password "$DB_PASS"
```

Das Script:
- Liest alle Content-Tabellen von Cloud SQL und macht UPSERT lokal
- Loescht lokale Zeilen die in Cloud nicht mehr existieren
- Aktualisiert Sequences und Alembic-Version
- Schreibt `.last_cloud_sync.json` (Snapshot fuer Drift-Detection beim Push)
- Bei Fehler: automatischer Rollback

**Edge Case — lokale Lessons mit ID > Cloud-max-ID:**
Wenn lokal Lessons via `/generate-lesson` erzeugt wurden, scheitert der Pull
mit FK-Constraint-Error (`lesson_page_lesson_id_fkey`). Workaround: Pull
ueberspringen, Push direkt mit `--skip-drift-check`:
```bash
PYTHONIOENCODING=utf-8 PYTHONPATH=. python scripts/sync_content_upsert.py \
  --cloud-host 34.65.56.56 --cloud-password "$DB_PASS" --skip-drift-check
```
**Risiko:** Cloud-Edits, die zwischenzeitlich gemacht wurden, gehen verloren.
Nur OK wenn kein Admin-Edit live war.

### 4b. Re-Apply lokale Edits (falls Schritt 1 angekuendigt)

```bash
# Beispiel:
PGPASSWORD="JapaneseApp2025!" psql -h localhost -U app_user -d japanese_learning <<'EOF'
BEGIN;
UPDATE lesson SET allow_guest_access = true WHERE id IN (...);
SELECT id, allow_guest_access FROM lesson WHERE id IN (...);
COMMIT;
EOF
```

### 5. SCHRITT B: Lokal → Cloud

```bash
# Dry Run
PYTHONIOENCODING=utf-8 PYTHONPATH=. python scripts/sync_content_upsert.py \
  --cloud-host 34.65.56.56 --cloud-password "$DB_PASS" --dry-run

# Live
PYTHONIOENCODING=utf-8 PYTHONPATH=. python scripts/sync_content_upsert.py \
  --cloud-host 34.65.56.56 --cloud-password "$DB_PASS"
```

### 6. SCHRITT C: Assets → GCS (PFLICHT)

DB-Sync allein reicht nicht. Vokabel-Bilder, Audio-Dateien, Slideshow-Assets
liegen lokal in `app/static/uploads/` — die Live-Seite loest sie aber via
`https://storage.googleapis.com/jpl-website-assets/...` auf. Wenn die Dateien
nicht im Bucket sind, kommt **404** und Lerner sehen keine Bilder/Audios.

```bash
PYTHONIOENCODING=utf-8 PYTHONPATH=. python scripts/sync_assets_to_gcs.py
```

Idempotent (rsync laedt nur neue/geaenderte). Pro neue Lektion ~30 Dateien,
~5-15 MB.

**ADC-Falle vermeiden:** Das Skript nutzt `gcloud storage rsync` mit
`--account=`-Flag, NICHT die Python-`google.cloud.storage`-API. ADC sind oft
mit altem Account registriert (`claudio.lutz86@gmail.com` statt
`claudio.lutz.cv@gmail.com`) und werfen 403 `storage.objects.create denied`.
Falls trotzdem Python-SDK noetig: `gcloud auth application-default login`
mit dem richtigen Account und `--billing-project=healthy-coil-466105-d7`.

### 7. PFLICHT: IP wieder schliessen

```bash
gcloud sql instances patch jpl-psql --clear-authorized-networks \
  --project=healthy-coil-466105-d7 --quiet
```

NEVER forget. Auch bei Crash zwischendurch — siehe "Wenn etwas schief geht".

### 8. Cloud-Run-Image-Aktualitaet pruefen

Dieser Skill synchronisiert nur die Datenbank. Code-Aenderungen (Templates,
CSS, JS, Python, Routes) seit dem letzten Deploy werden NICHT live, bis
`/deploy` ausgefuehrt wird.

```bash
LAST_DEPLOY=$(gcloud run services describe japanese-learning-app \
  --region=europe-west1 --project=healthy-coil-466105-d7 \
  --account=claudio.lutz.cv@gmail.com \
  --format="value(status.conditions[0].lastTransitionTime)")
git log --since="$LAST_DEPLOY" --oneline -- app/ scripts/ run.py
```

Wenn Commits seitdem >0 → User auf `/deploy` hinweisen oder direkt vorschlagen,
das Deploy auszufuehren. Symptom bei verpasstem Deploy: lokale UI-Verbesserungen
sind auf japanese-learning.ch nicht sichtbar (User: "lokal und webseite sehen
nicht gleich aus", 2026-04-25).

### 9. Summary report

- Schritt A: Cloud→Lokal — row counts, upserts, deletes
- Schritt B: Lokal→Cloud — row counts, upserts, deletes
- Schritt C: Assets→GCS — verzeichnisweise OK/FAIL
- User-Daten unangetastet (Backup unter `backups/user_data/`)
- Cloud SQL access closed
- Schema-Drift gecheckt
- Cloud-Run-Image-Stand vs. Code-Commits (Deploy noetig?)

---

## Wenn etwas schief geht

**Rule of thumb:** Wenn das Skill mittendrin abbricht — IP IMMER manuell schliessen.

```bash
# Notfall-Reset
gcloud sql instances patch jpl-psql --clear-authorized-networks \
  --project=healthy-coil-466105-d7 --quiet
```

**Drift-Check schlaegt fehl** (`Cloud-Stand abweichend von Snapshot`):
Cloud wurde zwischenzeitlich editiert. Pull erneut ausfuehren, dann erneut
Push.

**Pull schlaegt fehl mit FK-Constraint-Error:**
Lokale Lessons mit ID > Cloud-max-ID. Siehe Edge Case in Schritt 4.

**Push schlaegt fehl mit Deletion-Blocker:**
Eine Cloud-Content-Zeile soll geloescht werden, aber User-Daten zeigen darauf.
Entweder den lokalen Loeschwunsch zuruecknehmen (Row wieder einfuegen) oder
den User explizit fragen, ob die User-Daten verloren gehen duerfen.

**Asset-Sync gibt `'gcloud' nicht im PATH`:**
Auf Windows: `shutil.which("gcloud")` (im Skript bereits gefixt). Falls weiter
broken: manuell `gcloud storage rsync -r <local> <gs://...>` pro Verzeichnis.
