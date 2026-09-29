#!/usr/bin/env bash
# Einmaliger Audio-Nachlauf nach Gemini-Quota-Reset (geplant 2026-09-30 09:30).
#
# Hintergrund (29.09.2026): Gemini-2.5-Pro-TTS lieferte bei Kurz-Strings leer,
# der Chirp-Fallback schrieb MP3 → 98 lesson_content-Zeilen in 34 Lektionen
# verweisen im augmented_html auf .mp3. Seit dem Fix (tts_client) gibt es
# Kurz-String-Prompts und einen WAV-Chirp-Fallback. Dieser Lauf rendert den
# MP3-Altbestand neu (nur diese Eintraege, --replace-mp3 statt --force, damit die
# Tagesquota von 2'500 Calls reicht), stellt Rest-Verweise per prefer_wav um und
# vertont die zwei Vokabel-Saetze aus dem Audit nach.
#
# Laeuft auf hp-ubuntu als User hp-ubuntu (Host-venv, NICHT im Container).
# Kein Passwort im Skript: DATABASE_URL kommt aus .env, Host 'db' → localhost.
#
# Einrichtung (einmalig, Kopie liegt in /home/hp-ubuntu/):
#   sudo systemd-run --on-calendar="2026-09-30 09:30" --unit=jpl-audio-nachlauf-once \
#     --uid=hp-ubuntu --gid=hp-ubuntu --setenv=HOME=/home/hp-ubuntu \
#     /bin/bash /home/hp-ubuntu/jpl-audio-nachlauf-once.sh
set -u

REPO=/home/hp-ubuntu/git/Japanese_Learning_Website
LOG=/home/hp-ubuntu/jpl-backups/audio_nachlauf_20260930.log
VOCAB_FILE=/tmp/jplaudit/vocab_17_759.json
VOCAB_FILE_FALLBACK=/home/hp-ubuntu/jplaudit_vocab_17_759.json

exec >>"$LOG" 2>&1
echo "=== START $(date -Is) ==="

cd "$REPO" || { echo "FEHLER: Repo fehlt"; echo "DONE (Fehler)"; exit 1; }
echo "Code-Stand: $(git log --oneline -1)"

DB_URL=$(grep -E '^DATABASE_URL=' .env | head -1 | cut -d= -f2- | tr -d '"'"'" | sed 's/@db:/@localhost:/')
if [ -z "$DB_URL" ]; then
    echo "FEHLER: DATABASE_URL nicht in .env"; echo "DONE (Fehler)"; exit 1
fi
export DATABASE_URL="$DB_URL"
export PYTHONPATH=.
PY=venv/bin/python

# 0) Kurz-Probe gegen das echte Pro-Modell (3 Woerter, max. 12 Calls):
#    protokolliert, ob die Kurz-String-Prompts beim Pro-Modell greifen.
echo "--- Probe Kurz-Strings (gemini-2.5-pro-preview-tts) ---"
"$PY" - <<'PYEOF'
import os
from dotenv import load_dotenv
load_dotenv(".env")
from app.services import tts_client as t

client = t.make_gemini_client(os.environ.get("GOOGLE_AI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))
for word in ("ちち", "はは", "ひゃく"):
    try:
        pcm = t.synth_gemini_pcm(client, word)
        print(f"PROBE {word}: nackt OK ({len(pcm) / 48000:.2f} s)")
        continue
    except t.GeminiEmptyAudioError as e:
        print(f"PROBE {word}: nackt leer ({e})")
    except Exception as e:
        print(f"PROBE {word}: nackt EXC {str(e)[:120]}")
        continue
    for i, tpl in enumerate(t.GEMINI_SHORT_TEXT_PROMPTS, 1):
        try:
            pcm = t.synth_gemini_pcm(client, tpl.format(text=word))
            print(f"PROBE {word}: Prompt {i} OK ({len(pcm) / 48000:.2f} s)")
            break
        except t.GeminiEmptyAudioError as e:
            print(f"PROBE {word}: Prompt {i} leer ({e})")
        except Exception as e:
            print(f"PROBE {word}: Prompt {i} EXC {str(e)[:120]}")
            break
PYEOF

# 1) Lektionen mit MP3-Verweisen im augmented_html
IDS=$("$PY" - <<'PYEOF'
import os
from sqlalchemy import create_engine, text
eng = create_engine(os.environ["DATABASE_URL"])
with eng.connect() as c:
    rows = c.execute(text(
        "SELECT DISTINCT lesson_id FROM lesson_content "
        "WHERE ai_generation_details::text LIKE '%inline_audio/%.mp3%' ORDER BY lesson_id"
    )).fetchall()
print(" ".join(str(r[0]) for r in rows))
PYEOF
)
echo "Lektionen mit MP3-Verweisen: ${IDS:-keine}"

for id in $IDS; do
    echo "--- pregenerate_inline_audio $id --replace-mp3 ---"
    "$PY" scripts/pregenerate_inline_audio.py "$id" --replace-mp3 || echo "FEHLER Lektion $id (rc=$?)"
done

# 2) Restliche .mp3-Verweise auf vorhandene .wav umstellen
echo "--- prefer_wav_over_mp3 ---"
"$PY" scripts/prefer_wav_over_mp3.py || echo "FEHLER prefer_wav (rc=$?)"

# 3) Vokabel-Saetze aus dem Audit (17 / 759) nachvertonen
[ -f "$VOCAB_FILE" ] || VOCAB_FILE="$VOCAB_FILE_FALLBACK"
echo "--- gen_vocab_audio ($VOCAB_FILE) ---"
if [ -f "$VOCAB_FILE" ]; then
    "$PY" scripts/gen_vocab_audio.py --sentences-file "$VOCAB_FILE" --force || echo "FEHLER gen_vocab_audio (rc=$?)"
else
    echo "FEHLER: Vokabel-Datei fehlt ($VOCAB_FILE)"
fi

# 4) Kontrolle: verbleibende MP3-Verweise
"$PY" - <<'PYEOF'
import os
from sqlalchemy import create_engine, text
eng = create_engine(os.environ["DATABASE_URL"])
with eng.connect() as c:
    n, l = c.execute(text(
        "SELECT count(*), count(DISTINCT lesson_id) FROM lesson_content "
        "WHERE ai_generation_details::text LIKE '%inline_audio/%.mp3%'"
    )).one()
print(f"Verbleibende MP3-Verweise: {n} Zeilen in {l} Lektionen")
PYEOF

echo "=== ENDE $(date -Is) ==="
echo "DONE"
