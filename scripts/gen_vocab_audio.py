"""Vorgeneriert Gemini-TTS (Leda) fuer japanische Vokabel-Beispielsaetze (und optional Woerter).

Schreibt WAVs in app/static/uploads/tts_gemini/<sha1(transformierter Text)>.wav.
/api/tts liefert fuer lang=ja diese Datei mit Vorrang aus (siehe
app/routes.py::pregenerated_ja_audio_file) -> Karten-Audio ist damit IMMER Gemini,
ohne Request-Zeit-Latenz; Chirp bleibt nur Fallback fuer nicht Vorgeneriertes.

Im Container ausfuehren (hat DB-Host `db`, API-Key, uploads-Volume):
    sudo docker exec japanese_app python scripts/gen_vocab_audio.py [--force] [--limit N]
        [--workers 3] [--words] [--sentences-file pfad.json] [--dry-run]

--sentences-file: JSON-Liste roher japanischer Strings -> nur diese vertonen
                  (fuer "geaenderte Karten zuerst").
"""
import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from app import create_app
from app.models import Vocabulary
from app.routes import (
    _synthesize_gemini,
    _maybe_spell_out_kana_row,
    pregenerated_ja_audio_file,
)
from app.services.tts_text import clean_tts_segment


def canonical_ja(raw: str) -> str:
    """Exakt dieselbe Transformation wie /api/tts fuer lang=ja."""
    text = clean_tts_segment(raw, 'ja') or raw
    return _maybe_spell_out_kana_row(text, model='gemini')


def collect_raw_texts(args) -> list[str]:
    if args.sentences_file:
        items = json.load(open(args.sentences_file, encoding='utf-8'))
        raws = [s for s in items if s and str(s).strip()]
    else:
        rows = Vocabulary.query.all()
        raws = []
        for v in rows:
            if v.example_sentence_japanese and v.example_sentence_japanese.strip():
                raws.append(v.example_sentence_japanese.strip())
            if args.words and v.word and v.word.strip():
                raws.append(v.word.strip())
    # dedupe ueber den FINAL transformierten Text (gleicher Audio-Output -> eine Datei)
    seen, out = set(), []
    for raw in raws:
        canon = canonical_ja(raw)
        if not canon or canon in seen:
            continue
        seen.add(canon)
        out.append(canon)
    return out


def synth_one(canon: str, force: bool) -> tuple[str, str]:
    """Erzeugt eine WAV (mit Retry bei transienten Fehlern). Gibt (status, canon)."""
    path = pregenerated_ja_audio_file(canon)
    if path.exists() and not force:
        return ('skip', canon)
    path.parent.mkdir(parents=True, exist_ok=True)
    last = None
    for attempt in range(4):
        try:
            wav = _synthesize_gemini(canon)
            tmp = path.with_suffix('.wav.tmp')
            tmp.write_bytes(wav)
            tmp.replace(path)  # atomar -> nie halbe Datei im Store
            return ('ok', canon)
        except Exception as e:  # noqa: BLE001 — transient (429/529/safety) -> backoff
            last = e
            time.sleep(2 * (attempt + 1) + attempt * 3)
    return (f'FAIL: {last}', canon)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--force', action='store_true', help='auch vorhandene WAVs neu rendern')
    ap.add_argument('--limit', type=int, default=0, help='nur die ersten N (Test)')
    ap.add_argument('--workers', type=int, default=3, help='parallele Gemini-Calls (niedrig halten!)')
    ap.add_argument('--words', action='store_true', help='auch Einzelwoerter vertonen')
    ap.add_argument('--sentences-file', help='JSON-Liste roher JP-Strings (nur diese)')
    ap.add_argument('--dry-run', action='store_true', help='nur zaehlen, nichts rendern')
    args = ap.parse_args()

    app = create_app()
    with app.app_context():
        texts = collect_raw_texts(args)
        if args.limit:
            texts = texts[:args.limit]
        todo = [t for t in texts if args.force or not pregenerated_ja_audio_file(t).exists()]
        print(f"Distinkte JP-Texte: {len(texts)} | zu rendern: {len(todo)} | "
              f"workers={args.workers} force={args.force}")
        if args.dry_run:
            return 0

        ok = skip = fail = 0
        done = 0
        with ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
            futs = {ex.submit(synth_one, t, args.force): t for t in todo}
            for fut in as_completed(futs):
                status, canon = fut.result()
                done += 1
                if status == 'ok':
                    ok += 1
                elif status == 'skip':
                    skip += 1
                else:
                    fail += 1
                    print(f"  [{done}/{len(todo)}] {status} :: {canon[:40]}")
                if done % 25 == 0 or done == len(todo):
                    print(f"  Fortschritt {done}/{len(todo)} (ok={ok} fail={fail})", flush=True)
        print(f"FERTIG: ok={ok} skip={skip} fail={fail}")
        return 1 if fail else 0


if __name__ == '__main__':
    sys.exit(main())
