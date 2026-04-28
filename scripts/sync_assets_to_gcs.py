"""
GCS-Asset-Sync: Lokale Asset-Dateien (Bilder, Audios, Slideshows) zu GCS hochladen.

Hintergrund (2026-04-26):
Auf der Cloud-Run-Production loest das App-Modell Pfade wie
`vocab_generated/vocab_xxx.png` ueber den GCS-Bucket auf
(`https://storage.googleapis.com/jpl-website-assets/...`). Wenn die
generierten Dateien nicht im Bucket sind, kommt 404 — Symptom: Vokabel-
Bilder und Konversations-Audios fehlen live, obwohl sie lokal funktionieren.

Dieses Skript ergaenzt sync_content_upsert.py: Es synchronisiert die
generierten Assets (NICHT die DB) per `gcloud storage rsync` mit dem
aktiven gcloud-Konto. Idempotent: nur neue/geaenderte Dateien werden
hochgeladen.

Verwendung:
  python scripts/sync_assets_to_gcs.py
  python scripts/sync_assets_to_gcs.py --account=alice@example.com  # gcloud-Account
  python scripts/sync_assets_to_gcs.py --bucket=jpl-website-assets
  python scripts/sync_assets_to_gcs.py --dirs=vocab,thumbnails  # nur diese
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

# Synchronisierte Asset-Verzeichnisse (relativ zum Repo-Root).
# Schluessel: Kurzname fuer --dirs-Filter. Wert: (lokales Verzeichnis, GCS-Praefix)
ASSET_DIRECTORIES = {
    # Vokabel-Bilder (vocabulary.image_url -> "vocab_generated/vocab_xxx.png")
    "vocab": ("app/static/uploads/vocab_generated", "vocab_generated"),
    # Lesson-Thumbnails (lesson.thumbnail_url -> "generated/thumbnail_*.png")
    "thumbnails": ("app/static/uploads/generated", "generated"),
    # Konversations-Audios (lesson_content.file_path -> "lessons/audio/lesson_X/conversation.mp3")
    "audio": ("app/static/uploads/lessons/audio", "lessons/audio"),
    # Text-Vorlese-Audios (lesson_content.media_url -> "lessons/text_audio/lesson_X/...")
    "text_audio": ("app/static/uploads/lessons/text_audio", "lessons/text_audio"),
    # Dialog-Slideshow-Assets (Bilder + MP3s pro Slide)
    "slideshow": ("app/static/uploads/lessons/dialog_slideshow", "lessons/dialog_slideshow"),
}

DEFAULT_BUCKET = "jpl-website-assets"
DEFAULT_ACCOUNT = "claudio.lutz.cv@gmail.com"


def _resolve_gcloud() -> str:
    """Finde gcloud-Executable. Auf Windows ist es `gcloud.cmd` — `shutil.which`
    beruecksichtigt PATHEXT, plain subprocess.run([\"gcloud\"]) tut das nicht."""
    return shutil.which("gcloud") or "gcloud"


def rsync_directory(local_dir: Path, gcs_uri: str, account: str, dry_run: bool) -> int:
    """Synchronisiere ein Verzeichnis nach GCS via `gcloud storage rsync -r`.

    Returns 0 bei Erfolg, !=0 bei Fehler.
    """
    if not local_dir.exists():
        print(f"  [SKIP] Verzeichnis fehlt: {local_dir}")
        return 0
    cmd = [
        _resolve_gcloud(), "storage", "rsync", "-r",
        str(local_dir), gcs_uri,
        f"--account={account}",
    ]
    if dry_run:
        cmd.append("--dry-run")
    print(f"\n  rsync {local_dir}  ->  {gcs_uri}")
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except FileNotFoundError:
        print(f"    [FEHLER] 'gcloud' nicht im PATH gefunden. "
              f"Bitte gcloud SDK installieren.", file=sys.stderr)
        return 1


def main():
    parser = argparse.ArgumentParser(
        description="Synchronisiere lokale Asset-Dateien (Bilder, Audios, "
                    "Slideshows) per `gcloud storage rsync` mit dem GCS-Bucket. "
                    "Vermeidet, dass auf der Live-Seite Vokabel-Bilder oder "
                    "Audios als 404 fehlschlagen."
    )
    parser.add_argument("--bucket", default=DEFAULT_BUCKET,
                        help=f"GCS-Bucket-Name (Default: {DEFAULT_BUCKET})")
    parser.add_argument("--account", default=DEFAULT_ACCOUNT,
                        help=f"gcloud-Account (Default: {DEFAULT_ACCOUNT})")
    parser.add_argument("--dry-run", action="store_true",
                        help="Nur anzeigen, was rsync uebertragen wuerde")
    parser.add_argument("--dirs", default=None,
                        help="Komma-getrennte Liste der Verzeichnis-Schluessel "
                             "(vocab, thumbnails, audio, text_audio, slideshow). "
                             "Default: alle.")
    args = parser.parse_args()

    print("=" * 64)
    print(f"  GCS-Asset-Sync  ->  gs://{args.bucket}/")
    print(f"  Account: {args.account}")
    if args.dry_run:
        print("  Modus: DRY RUN (keine Uploads)")
    print("=" * 64)

    if args.dirs:
        keys = [k.strip() for k in args.dirs.split(",") if k.strip()]
        unknown = [k for k in keys if k not in ASSET_DIRECTORIES]
        if unknown:
            print(f"FEHLER: unbekannte Verzeichnis-Schluessel: {unknown}", file=sys.stderr)
            print(f"Erlaubt: {sorted(ASSET_DIRECTORIES.keys())}", file=sys.stderr)
            sys.exit(2)
    else:
        keys = list(ASSET_DIRECTORIES.keys())

    repo_root = Path(__file__).resolve().parent.parent
    failed = []
    for key in keys:
        local_dir, gcs_prefix = ASSET_DIRECTORIES[key]
        local_path = repo_root / local_dir
        gcs_uri = f"gs://{args.bucket}/{gcs_prefix}"
        rc = rsync_directory(local_path, gcs_uri, args.account, args.dry_run)
        if rc != 0:
            failed.append(key)

    print("\n" + "=" * 64)
    if failed:
        print(f"  FEHLER bei: {', '.join(failed)}")
        sys.exit(1)
    print("  Erfolgreich: alle Verzeichnisse synchronisiert.")
    print("=" * 64)


if __name__ == "__main__":
    main()
