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

### Eingebaute Schutzmechanismen (seit Audit 2026-04-25)

Das Skript `sync_content_upsert.py` ist mehrfach abgesichert. Schutzschichten in der Reihenfolge ihrer Aktivierung:

1. **Drift-Check** — Vergleicht den aktuellen Cloud-Stand (Count, MAX(id), MAX(updated_at) pro Content-Tabelle) mit dem Snapshot, der beim letzten Cloud→Lokal-Pull in `.last_cloud_sync.json` abgelegt wurde. Bei Abweichung (z.B. Admin hat zwischenzeitlich auf der Live-Seite editiert): **Abbruch mit Aufforderung, erneut zu pullen**.
2. **User-Daten-Backup** — Vor jedem Push werden alle User-Tabellen (`user`, `user_lesson_progress`, `user_quiz_answer`, `card_review_state`, `review_log`, `user_srs_settings`, `user_achievement`, `daily_review_aggregate`, `lesson_purchase`, `course_purchase`, `payment_transaction`) per `pg_dump` nach `backups/user_data/cloud_pre_push_<timestamp>.sql` gesichert.
3. **Kaufschutz / Deletion-Blocker** — Bevor das Skript eine Cloud-Content-Zeile loescht (weil sie lokal fehlt), prueft es ob User-Daten darauf zeigen (`user_lesson_progress`, `user_quiz_answer`, `card_review_state`, `review_log`, `lesson_purchase`, `course_purchase`). Bei Treffer: **Abbruch mit Liste der betroffenen IDs**.
4. **DB-FK RESTRICT** — Migration `d8e2c1a4f6b3` hat die Purchase-FKs von `ON DELETE CASCADE` auf `ON DELETE RESTRICT` umgestellt. Selbst wenn alle anderen Schutzschichten umgangen werden, blockt die DB jeden DELETE auf einer Lesson/Course mit aktiven Kaeufen.

Override-Flags (nur fuer Notfaelle):
- `--skip-drift-check` — Drift ignorieren (z.B. wenn man bewusst Cloud-Aenderungen ueberschreiben will)
- `--skip-backup` — kein Backup erstellen (z.B. wenn pg_dump fehlt)
- `--force-delete-user-data` — Inhalte trotz User-FK loeschen (Datenverlust akzeptiert; macht den Sync nur erfolgreich, wenn FK-Constraints es erlauben)

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

### 4b. Falle: lokale neue Lessons → Cloud→Lokal-Pull bricht (seit 2026-04-26)

**Bekanntes Problem:** Wenn lokal Lessons erstellt wurden, deren ID **groesser**
als die hoechste Cloud-Lesson-ID ist (typisch nach `/generate-lesson` Sessions),
scheitert der `sync_from_cloud.py`-Pull mit:

```
FEHLER: update or delete on table "lesson" violates foreign key constraint
"lesson_page_lesson_id_fkey" on table "lesson_page"
DETAIL:  Key (id)=(156) is still referenced from table "lesson_page".
```

Ursache: `sync_from_cloud.py` betrachtet Cloud als Source-of-Truth und versucht,
lokale Rows zu loeschen, die Cloud nicht hat — auch wenn das die soeben generierten
Lessons sind.

**Workaround:** Cloud→Lokal-Pull ueberspringen, direkt mit `--skip-drift-check`
auf Push gehen. Nur OK, wenn kein Admin-Edit auf der Live-Seite zwischenzeitlich
erfolgte. Wenn Cloud zuvor was geaendert wurde, gehen die Aenderungen verloren.

```bash
# Skip Schritt 5 (Cloud→Lokal-Pull) komplett.
# Direkt:
PYTHONIOENCODING=utf-8 PYTHONPATH=. python scripts/sync_content_upsert.py \
  --cloud-host 34.65.56.56 --cloud-password "$DB_PASS" --skip-drift-check
```

TODO: scripts/sync_from_cloud.py Refactoring — beim Loesch-Schritt lokale Rows
mit ID > Cloud-max-ID per Default behalten, optional via `--delete-newer-local`.

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
- **Schreibt nach erfolgreichem Pull `.last_cloud_sync.json`** (Snapshot fuer Drift-Detection beim naechsten Push)
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

### 6b. SCHRITT C: Assets nach GCS hochladen (PFLICHT seit 2026-04-26)

**Lesson Learned 2026-04-26:** DB-Sync allein reicht nicht. Vokabel-
Bilder, Audio-Dateien, Slideshow-Assets liegen lokal in
`app/static/uploads/` — die Live-Seite loest sie aber via
`https://storage.googleapis.com/jpl-website-assets/...` auf. Wenn die
Dateien nicht im GCS-Bucket sind, kommt **404** und die Lerner sehen
Bilder/Audios nicht (User-Beschwerde 2026-04-26: "die bilder werden auf
der webseite nicht angezeigt aber lokal schon" und "das audio funktioniert
auch nicht auf der deployten webseite").

```bash
# Synchronisiert vocab_generated, generated, lessons/audio,
# lessons/text_audio, lessons/dialog_slideshow per `gcloud storage rsync -r`.
PYTHONIOENCODING=utf-8 PYTHONPATH=. python scripts/sync_assets_to_gcs.py
```

Idempotent: rsync laedt nur neue/geaenderte Dateien hoch. Bei einer
einzelnen neuen Lektion typisch ~30 Dateien (Thumb + Vokabel-Bilder +
Conversation-MP3 + Slideshow-PNG/MP3 + Text-Audio-MP3s), ~5-15 MB.

**Wichtig: ADC-Falle vermeiden.** Das Skript nutzt `gcloud storage rsync`
mit `--account=`-Flag, NICHT die Python-`google.cloud.storage`-API.
Grund: Application Default Credentials (ADC) sind oft mit einem alten
Account registriert (z.B. `claudio.lutz86@gmail.com` statt
`claudio.lutz.cv@gmail.com`) und werfen 403 `storage.objects.create
denied`. Das `--account=`-Flag im rsync-Pfad nutzt die `gcloud config`
direkt, ohne ADC-Verflechtung. Wenn doch Python-SDK genutzt werden soll:
zuerst `gcloud auth application-default login` mit dem richtigen Account
und `--billing-project=healthy-coil-466105-d7`.

### 7. ALWAYS close access

```bash
gcloud sql instances patch jpl-psql --clear-authorized-networks \
  --project=healthy-coil-466105-d7 --quiet
```

NEVER forget this step.

### 8. WICHTIG: Code-Aenderungen brauchen separaten Cloud-Run-Deploy

Dieser Skill synchronisiert NUR die Datenbank. Wenn seit dem letzten
`/deploy` Code geaendert wurde (Templates, CSS, JS, Python, neue Routes),
ist die Live-Seite trotz erfolgreichem DB-Sync NICHT auf dem aktuellen
Stand. Symptom: lokale UI-Verbesserungen sind auf japanese-learning.ch
nicht sichtbar.

Pflicht-Check vor dem Sync-Ende:
```bash
# Letzte deployed Revision?
gcloud run services describe japanese-learning-app \
  --region=europe-west1 --project=healthy-coil-466105-d7 \
  --account=claudio.lutz.cv@gmail.com \
  --format="value(status.conditions[0].lastTransitionTime)"

# Code-Commits seitdem?
git log --since="$LAST_DEPLOY_TIME" --oneline -- app/ scripts/ run.py
```

Falls Commits >0 → User auf `/deploy` hinweisen oder direkt vorschlagen,
das Deploy auszufuehren:
```bash
gcloud builds submit --config=cloudbuild.yaml \
  --project=healthy-coil-466105-d7 --account=claudio.lutz.cv@gmail.com .
gcloud run services update japanese-learning-app \
  --image=europe-west6-docker.pkg.dev/healthy-coil-466105-d7/app-images/japanese-learning-app:latest \
  --region=europe-west1 --project=healthy-coil-466105-d7 \
  --account=claudio.lutz.cv@gmail.com
```

Begruendung (Lesson Learned 2026-04-25): Nach DB-Sync von 14 neuen Lessons
zeigte japanese-learning.ch zwar die neuen Lektionen, aber NICHT die
neue Top-Nav, Markdown-Rendering und text-audio-Updates aus Commits
seit 14:00 — weil Cloud Run noch das alte Image lief. User: "lokal und
webseite sehen nicht gleich aus".

### 9. Schema-Drift pruefen (Pflicht-Check)

Vor dem Push pruefen, ob lokal und Cloud auf derselben Alembic-Migration
sind:

```bash
LOCAL_VER=$(PGPASSWORD="JapaneseApp2025!" psql -h localhost -U app_user \
  -d japanese_learning -t -A -c "SELECT version_num FROM alembic_version;")
CLOUD_VER=$(PGPASSWORD="$DB_PASS" psql -h 34.65.56.56 -U app_user \
  -d japanese_learning -t -A -c "SELECT version_num FROM alembic_version;")
echo "Lokal: $LOCAL_VER  Cloud: $CLOUD_VER"
```

Wenn unterschiedlich: ZUERST `flask db upgrade` mit `DATABASE_URL` auf
Cloud zeigend, DANN Sync. Begruendung: Der Sync-Push setzt
`alembic_version` auf den lokalen Stand — wenn die Migrationen physisch
nicht angewendet sind, glaubt Alembic faelschlicherweise, dass sie es
sind.

```bash
# Cloud-Migrationen anwenden
DATABASE_URL="postgresql://app_user:${DB_PASS}@34.65.56.56:5432/japanese_learning" \
  flask db upgrade
```

Bei Phase-Tabellen, die physisch schon existieren aber alembic_version
noch nicht hochgezogen wurde: `flask db stamp <revision>` setzt nur den
Marker.

### 10. Summary

Report:
- Schritt A: Cloud→Lokal (row counts, upserts, deletes)
- Schritt B: Lokal→Cloud (row counts, upserts, deletes)
- Tables protected (user, progress, purchases — untouched)
- Cloud SQL access closed
- **Cloud-Run-Image-Stand vs. Code-Commits seitdem** (deploy noetig?)
- **Schema-Drift gecheckt** (Migrationen synchron?)
