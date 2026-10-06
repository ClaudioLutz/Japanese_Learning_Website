#!/usr/bin/env bash
# Audio-Nachlauf: MP3-Altbestand im Klick-Audio auf WAV heben (wiederverwendbar).
#
# Rendert fuer alle Lektionen, deren augmented_html noch auf
# inline_audio/<hash>.mp3 zeigt, genau diese Eintraege neu
# (pregenerate_inline_audio.py --replace-mp3, quotaschonend), stellt
# Rest-Verweise per prefer_wav_over_mp3.py um und vertont optional eine
# Liste von Vokabel-Saetzen nach (gen_vocab_audio.py --sentences-file … --force).
#
# Aufruf (auf hp-ubuntu als hp-ubuntu, Host-venv, NICHT im Container):
#   tools/audio_nachlauf.sh <log-datei> [vokabel-json]
#     <log-datei>    Ausgabe wird angehaengt (z.B. ~/jpl-backups/audio_nachlauf_<datum>.log)
#     [vokabel-json] optional: JSON-Liste roher JP-Saetze; nur dann laeuft ein
#                    erzwungener (--force) Vokabel-Lauf, sonst keiner.
#
# Exit-Code != 0, wenn die ID-Abfrage scheitert oder ein Schritt fehlschlaegt.
# Kein Passwort im Skript: DATABASE_URL kommt aus .env, Host 'db' → localhost.
set -euo pipefail

if [ $# -lt 1 ] || [ $# -gt 2 ]; then
    echo "Usage: $0 <log-datei> [vokabel-json]" >&2
    exit 2
fi
LOG=$1
VOCAB_FILE=${2:-}
REPO=${JPL_REPO:-/home/hp-ubuntu/git/Japanese_Learning_Website}

if [ -n "$VOCAB_FILE" ] && [ ! -f "$VOCAB_FILE" ]; then
    echo "FEHLER: Vokabel-Datei fehlt: $VOCAB_FILE" >&2
    exit 2
fi

exec >>"$LOG" 2>&1
echo "=== START $(date -Is) ==="
cd "$REPO"
echo "Code-Stand: $(git log --oneline -1)"

DB_URL=$(grep -E '^DATABASE_URL=' .env | head -1 | cut -d= -f2- | tr -d '"'"'" | sed 's/@db:/@localhost:/')
if [ -z "$DB_URL" ]; then
    echo "FEHLER: DATABASE_URL nicht in .env"
    exit 1
fi
export DATABASE_URL="$DB_URL"
export PYTHONPATH=.
PY=venv/bin/python
MP3_REGEX='inline_audio/[0-9a-f]+\.mp3'
export MP3_REGEX

# 1) Lektionen mit MP3-Verweisen im augmented_html (Abbruch, wenn die Abfrage scheitert)
IDS=$("$PY" - <<'PYEOF'
import os
from sqlalchemy import create_engine, text
eng = create_engine(os.environ["DATABASE_URL"])
with eng.connect() as c:
    rows = c.execute(text(
        "SELECT DISTINCT lesson_id FROM lesson_content "
        "WHERE ai_generation_details->>'augmented_html' ~ :rx ORDER BY lesson_id"
    ), {"rx": os.environ["MP3_REGEX"]}).fetchall()
print(" ".join(str(r[0]) for r in rows))
PYEOF
)
echo "Lektionen mit MP3-Verweisen: ${IDS:-keine}"

FAILED=0
for id in $IDS; do
    echo "--- pregenerate_inline_audio $id --replace-mp3 ---"
    if ! "$PY" scripts/pregenerate_inline_audio.py "$id" --replace-mp3; then
        echo "FEHLER Lektion $id"
        FAILED=1
    fi
done

# 2) Restliche .mp3-Verweise auf vorhandene .wav umstellen
echo "--- prefer_wav_over_mp3 ---"
"$PY" scripts/prefer_wav_over_mp3.py || { echo "FEHLER prefer_wav"; FAILED=1; }

# 3) Optional: Vokabel-Saetze nachvertonen (nur mit Parameter)
if [ -n "$VOCAB_FILE" ]; then
    echo "--- gen_vocab_audio ($VOCAB_FILE) ---"
    "$PY" scripts/gen_vocab_audio.py --sentences-file "$VOCAB_FILE" --force \
        || { echo "FEHLER gen_vocab_audio"; FAILED=1; }
else
    echo "--- gen_vocab_audio: uebersprungen (keine Vokabel-Datei angegeben) ---"
fi

# 4) Kontrolle: verbleibende MP3-Verweise
"$PY" - <<'PYEOF'
import os
from sqlalchemy import create_engine, text
eng = create_engine(os.environ["DATABASE_URL"])
with eng.connect() as c:
    n, l = c.execute(text(
        "SELECT count(*), count(DISTINCT lesson_id) FROM lesson_content "
        "WHERE ai_generation_details->>'augmented_html' ~ :rx"
    ), {"rx": os.environ["MP3_REGEX"]}).one()
print(f"Verbleibende MP3-Verweise: {n} Zeilen in {l} Lektionen")
PYEOF

echo "=== ENDE $(date -Is) (Fehler: $FAILED) ==="
exit "$FAILED"
