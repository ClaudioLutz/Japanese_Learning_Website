# Resume-Skript: laeuft morgen frueh nach Gemini-Quota-Reset (PST Mitternacht).
# Erledigt:
#   1. Docker DB starten falls nicht aktiv
#   2. Block-Player Bulk-Lauf (gen_text_audio fuer alle 35 verbleibenden Lessons)
#   3. Inline-Audio Force-Rerun fuer alle Lessons (mit neuer , -Heuristik)
#   4. Logs in scripts/resume_run_<timestamp>.log

$ErrorActionPreference = "Continue"
$ProjectRoot = "C:\Codes\Japanese_learning_Website_project\Japanese_Learning_Website"
Set-Location $ProjectRoot

$timestamp = Get-Date -Format "yyyy-MM-dd_HHmm"
$logFile = "$ProjectRoot\scripts\resume_run_$timestamp.log"

function Log($msg) {
    $line = "$(Get-Date -Format 'HH:mm:ss') $msg"
    Add-Content -Path $logFile -Value $line
    Write-Host $line
}

Log "=== Resume Audio Generation gestartet ==="

# 1. Docker pruefen + DB starten
Log "Pruefe Docker..."
$dockerRunning = $null
try { $dockerRunning = docker version 2>&1 } catch {}
if (-not $dockerRunning -or $dockerRunning -match "error") {
    Log "Docker laeuft nicht. Starte Docker Desktop..."
    Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    Log "Warte 60s auf Docker-Startup..."
    Start-Sleep -Seconds 60
}

Log "Starte Postgres-Container..."
docker compose up db -d 2>&1 | ForEach-Object { Log $_ }
Start-Sleep -Seconds 5

# 2. Block-Player Bulk-Lauf (Gemini fuer ja, Neural2-G fuer de)
Log "=== Phase 1: Block-Player Bulk-Lauf ==="
$env:PYTHONIOENCODING = "utf-8"
& "$ProjectRoot\venv\Scripts\python.exe" "$ProjectRoot\scripts\regenerate_block_audio_all.py" 2>&1 | ForEach-Object { Log $_ }

# 3. Inline-Audio Force-Rerun fuer alle published Lessons (neue , -Heuristik)
Log "=== Phase 2: Inline-Audio Force-Rerun ==="
& "$ProjectRoot\venv\Scripts\python.exe" "$ProjectRoot\scripts\pregenerate_inline_audio.py" --all --force 2>&1 | ForEach-Object { Log $_ }

# 4. URL-Korrektur (.mp3 -> .wav wo verfuegbar)
Log "=== Phase 3: URL-Korrektur (Gemini bevorzugen) ==="
& "$ProjectRoot\venv\Scripts\python.exe" "$ProjectRoot\scripts\prefer_wav_over_mp3.py" 2>&1 | ForEach-Object { Log $_ }

Log "=== ALLES FERTIG ==="
