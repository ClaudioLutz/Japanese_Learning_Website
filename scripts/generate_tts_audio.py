#!/usr/bin/env python3
"""
Generiert TTS-Audio für MNN-Lektionen mit Google Cloud TTS Neural2.
Ersetzt kopierte Audio-Dateien durch KI-generierte Stimmen.

Verwendung:
    python scripts/generate_tts_audio.py                    # Lektion 1
    python scripts/generate_tts_audio.py --lesson 5         # Lektion 5
    python scripts/generate_tts_audio.py --dry-run          # Nur anzeigen
"""
import json
import os
import sys
import io
from pathlib import Path

# Windows: UTF-8-Ausgabe erzwingen
if sys.platform == "win32" and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

# Umgebungsvariablen setzen bevor App importiert wird
os.environ.setdefault("DATABASE_URL", "postgresql://app_user:JapaneseApp2025!@localhost:5432/japanese_learning")
os.environ.setdefault("PAYMENT_PROVIDER", "mock")
os.environ.setdefault("MOCK_PAYMENTS_ENABLED", "true")

DATA_DIR = PROJECT_ROOT / "scripts" / "mnn_data"
AUDIO_BASE = PROJECT_ROOT / "app" / "static" / "uploads" / "lessons" / "audio"

# Google TTS Konfiguration
VOICE_NAME = "ja-JP-Neural2-B"
SPEAKING_RATE = 0.85  # Langsamer für Lernende

# Stimmen für Multi-Voice Konversation
# WICHTIG (korrigiert 2026-04-24): ja-JP-Neural2-C ist laut Google Cloud
# TTS-Dokumentation WEIBLICH, nicht männlich — vorherige Kommentare waren
# falsch und fuehrten dazu, dass Maenner weiblich klangen. Offizielles
# Gender-Mapping: Neural2-B=FEMALE, Neural2-C=FEMALE, Neural2-D=MALE.
# Es gibt nur EINE maennliche Neural2-Stimme; fuer zweiten Mann nehmen
# wir Wavenet-D (anderes Modell, damit sich die beiden Maenner
# unterscheiden).
VOICE_FEMALE = "ja-JP-Neural2-B"    # Weiblich 1 (Neural2)
VOICE_FEMALE_2 = "ja-JP-Neural2-C"  # Weiblich 2 (Neural2)
VOICE_MALE_1 = "ja-JP-Neural2-D"    # Maennlich 1 (Neural2)
VOICE_MALE_2 = "ja-JP-Wavenet-D"    # Maennlich 2 (Wavenet — klar anders als Neural2-D)

# Geschlecht der Sprecher (bekannte MNN-Charaktere + Claude-generierte
# Anfaenger-Lektionen). Wichtig fuer korrekte Stimmen-Zuordnung — ein
# maennlicher Name darf NIE eine weibliche Stimme bekommen.
SPEAKER_GENDER = {
    # MNN-Charaktere
    "Sato": "female",      # 佐藤けいこ
    "Yamada": "male",       # 山田
    "Miller": "male",       # マイク・ミラー
    "Santos": "male",       # サントス
    "Tanaka": "male",       # 田中
    "Kimura": "female",     # 木村
    "Suzuki": "male",       # 鈴木
    "Watanabe": "female",   # 渡辺
    "Lee": "male",          # リー
    "Maria": "female",      # マリア
    "Karina": "female",     # カリナ
    "Watt": "male",         # ワット
    "Schmidt": "male",      # シュミット
    "Takahashi": "male",    # 高橋
    "Gupta": "male",        # グプタ
    "Wang": "female",       # ワン
    # Charaktere, die Claude selbst in neuen Lektionen nutzt
    "Lisa": "female",
    "Mayuko": "female",
    "Anna": "female",
    "Emma": "female",
    "Sophie": "female",
    "Claudia": "female",
    "Sakura": "female",
    "Hanako": "female",
    "Yuki": "female",
    "Haruto": "male",
    "Claudio": "male",
    "Paul": "male",
    "Tom": "male",
    "Max": "male",
    "Michael": "male",
    "David": "male",
    "Ken": "male",
    "Hiroshi": "male",
    "Ueno": "female",      # Ueno-sensei (default female-leaning)
    "Weber": "female",     # Nachname allein kein Indikator — konservativ female
    # Katakana-Schreibweisen (von Claude in Dialogen genutzt)
    "リサ": "female",       # Lisa
    "ハルト": "male",       # Haruto
    "マユコ": "female",     # Mayuko
    "サクラ": "female",     # Sakura
    "ハナコ": "female",     # Hanako
    "ユキ": "female",       # Yuki
    "ヤマダ": "male",       # Yamada
    "タナカ": "male",       # Tanaka
    "ウエノ": "female",     # Ueno-sensei
    # Familienrollen (in Familien-Dialogen ohne Eigennamen)
    "Mama": "female",
    "Mutter": "female",
    "Mami": "female",
    "Papa": "male",
    "Vater": "male",
    "Papi": "male",
    "Tochter": "female",
    "Sohn": "male",
    "Oma": "female",
    "Opa": "male",
    "ママ": "female",
    "パパ": "male",
    "おかあさん": "female",
    "おとうさん": "male",
    "ちち": "male",
    "はは": "female",
}


def get_voice_for_speaker(speaker: str, speaker_list: list[str]) -> str:
    """Weist einem Sprecher eine TTS-Stimme zu basierend auf Geschlecht.

    Erster Mann / erste Frau bekommen die Neural2-Stimmen; ab dem zweiten
    Sprecher desselben Geschlechts wird auf die Alternativ-Stimme gewechselt,
    damit gleichgeschlechtliche Sprecher klanglich unterscheidbar bleiben.
    """
    def _gender_for(s: str) -> str:
        g = SPEAKER_GENDER.get(s, None)
        if g is not None:
            return g
        idx = speaker_list.index(s) if s in speaker_list else 0
        return "female" if idx % 2 == 0 else "male"

    gender = _gender_for(speaker)

    if gender == "female":
        female_speakers = [s for s in speaker_list if _gender_for(s) == "female"]
        if speaker in female_speakers and female_speakers.index(speaker) >= 1:
            return VOICE_FEMALE_2
        return VOICE_FEMALE

    male_speakers = [s for s in speaker_list if _gender_for(s) == "male"]
    if speaker in male_speakers and male_speakers.index(speaker) >= 1:
        return VOICE_MALE_2
    return VOICE_MALE_1


def get_google_tts_client():
    """Erstellt Google Cloud TTS Client."""
    from google.cloud import texttospeech
    api_key = os.environ.get("GOOGLE_TTS_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if api_key:
        return texttospeech.TextToSpeechClient(client_options={"api_key": api_key})
    return texttospeech.TextToSpeechClient()


def generate_audio(client, text: str, output_path: Path, speaking_rate: float = SPEAKING_RATE):
    """Generiert eine MP3-Datei mit Google Cloud TTS Neural2."""
    from google.cloud import texttospeech

    # SSML mit Pausen zwischen Zeilen
    lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
    ssml_parts = []
    for line in lines:
        ssml_parts.append(f"<s>{line}</s><break time='700ms'/>")
    ssml = f"<speak>{''.join(ssml_parts)}</speak>"

    response = client.synthesize_speech(
        input=texttospeech.SynthesisInput(ssml=ssml),
        voice=texttospeech.VoiceSelectionParams(
            language_code="ja-JP",
            name=VOICE_NAME,
        ),
        audio_config=texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=speaking_rate,
            pitch=0.0,
        ),
    )

    output_path.write_bytes(response.audio_content)
    size_kb = output_path.stat().st_size // 1024
    print(f"  [OK] {output_path.name} ({size_kb} KB)")
    return output_path


def generate_conversation_audio(
    client, conv_lines: list[dict], output_path: Path, speaking_rate: float = SPEAKING_RATE
):
    """
    Generiert Konversations-Audio mit wechselnden Stimmen pro Sprecher.
    Jede Zeile wird einzeln generiert und dann zusammengefügt.
    """
    import tempfile
    from google.cloud import texttospeech

    # ffmpeg-Pfad über imageio-ffmpeg
    import imageio_ffmpeg
    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

    # Alle Sprecher ermitteln (Reihenfolge des Auftretens)
    speakers = []
    for line in conv_lines:
        if line["speaker"] not in speakers:
            speakers.append(line["speaker"])

    print(f"  Sprecher: {', '.join(speakers)}")
    for s in speakers:
        voice = get_voice_for_speaker(s, speakers)
        print(f"    {s} -> {voice}")

    # Jede Zeile einzeln generieren
    segment_files = []
    with tempfile.TemporaryDirectory() as tmpdir:
        for i, line in enumerate(conv_lines):
            speaker = line["speaker"]
            text = line["japanese"]
            voice_name = get_voice_for_speaker(speaker, speakers)

            ssml = f"<speak><s>{text}</s></speak>"
            response = client.synthesize_speech(
                input=texttospeech.SynthesisInput(ssml=ssml),
                voice=texttospeech.VoiceSelectionParams(
                    language_code="ja-JP",
                    name=voice_name,
                ),
                audio_config=texttospeech.AudioConfig(
                    audio_encoding=texttospeech.AudioEncoding.MP3,
                    speaking_rate=speaking_rate,
                    pitch=0.0,
                ),
            )

            seg_path = Path(tmpdir) / f"seg_{i:03d}.mp3"
            seg_path.write_bytes(response.audio_content)
            segment_files.append(str(seg_path))
            print(f"    [{i+1}/{len(conv_lines)}] {speaker}: {text[:40]}...")

        # Stille generieren (700ms Pause zwischen Zeilen)
        silence_path = Path(tmpdir) / "silence.mp3"
        import subprocess
        subprocess.run(
            [ffmpeg_path, "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
             "-t", "0.7", "-c:a", "libmp3lame", "-q:a", "9",
             "-y", str(silence_path)],
            capture_output=True,
        )

        # Concat-Liste für ffmpeg erstellen
        concat_list = Path(tmpdir) / "concat.txt"
        lines_for_concat = []
        for j, seg in enumerate(segment_files):
            lines_for_concat.append(f"file '{seg}'")
            if j < len(segment_files) - 1:
                lines_for_concat.append(f"file '{silence_path}'")
        concat_list.write_text("\n".join(lines_for_concat), encoding="utf-8")

        # Zusammenfügen mit ffmpeg
        subprocess.run(
            [ffmpeg_path, "-f", "concat", "-safe", "0",
             "-i", str(concat_list), "-c:a", "libmp3lame", "-q:a", "2",
             "-y", str(output_path)],
            capture_output=True,
        )

    size_kb = output_path.stat().st_size // 1024
    print(f"  [OK] {output_path.name} ({size_kb} KB) — {len(speakers)} Stimmen")
    return output_path


def build_audio_texts(data: dict) -> list[tuple]:
    """
    Baut die Audio-Texte aus dem JSON.
    Returns: [(filename, title, japanese_text, page_number), ...]
    Konversation: (filename, title, conv_lines_list, page_number, "multi_voice")
    """
    lesson_num = data["lesson_number"]
    prefix = f"lesson{lesson_num:02d}"
    items = []

    # 1) Vokabeln — Seite 1
    vocab_lines = []
    for v in data.get("vocabulary", []):
        vocab_lines.append(v["word"])
    for v in data.get("vocabulary_countries", []):
        vocab_lines.append(v["word"])
    if vocab_lines:
        items.append((
            f"{prefix}_vocabulary.mp3",
            "Vokabeln (Audio)",
            "\n".join(vocab_lines),
            1,
        ))

    # 2) Satzmuster — Seite 2
    pattern_lines = []
    for g in data.get("grammar", []):
        if g.get("structure"):
            pattern_lines.append(g["structure"])
    if pattern_lines:
        items.append((
            f"{prefix}_sentence_patterns.mp3",
            "Satzmuster (Audio)",
            "\n".join(pattern_lines),
            2,
        ))

    # 3) Beispielsätze — Seite 2
    example_lines = []
    for g in data.get("grammar", []):
        if g.get("example_sentences"):
            for line in g["example_sentences"].split("\n"):
                line = line.strip()
                if line and not line.startswith("(") and not line.startswith("—") and not line.startswith("…"):
                    cleaned = line.lstrip("①②③④⑤⑥⑦⑧⑨⑩ ")
                    if cleaned and any(ord(c) > 0x3000 for c in cleaned):
                        example_lines.append(cleaned)
    if example_lines:
        items.append((
            f"{prefix}_examples.mp3",
            "Beispielsätze (Audio)",
            "\n".join(example_lines),
            2,
        ))

    # 4) Konversation — Seite 3 (Multi-Voice!)
    conv = data.get("conversation")
    if conv and conv.get("lines"):
        items.append((
            f"{prefix}_conversation.mp3",
            "Konversation (Audio)",
            conv["lines"],  # Strukturierte Daten mit speaker + japanese
            3,
            "multi_voice",  # Flag für Multi-Voice-Generierung
        ))

    # 4b) Zusätzliche Konversationen — Seite 3 (Multi-Voice!)
    for idx, extra_conv in enumerate(data.get("additional_conversations", []), start=1):
        if extra_conv.get("lines"):
            conv_title = extra_conv.get("title", f"Conversation {idx + 1}")
            items.append((
                f"{prefix}_conversation_{idx + 1}.mp3",
                f"{conv_title} (Audio)",
                extra_conv["lines"],
                3,
                "multi_voice",
            ))

    # 5) Übungen — Seite 4 (Vokabel-Drill)
    drill_lines = []
    for v in data.get("vocabulary", [])[:10]:
        drill_lines.append(v["word"])
    if drill_lines:
        items.append((
            f"{prefix}_practice.mp3",
            "Übung (Audio)",
            "\n".join(drill_lines),
            4,
        ))

    # 6) Hörverständnis — Seite 5 (Konversation + Grammatik gemischt)
    test_lines = []
    if conv:
        for line in conv.get("lines", []):
            test_lines.append(line["japanese"])
    for g in data.get("grammar", [])[:3]:
        if g.get("example_sentences"):
            for line in g["example_sentences"].split("\n"):
                line = line.strip()
                cleaned = line.lstrip("①②③④⑤⑥⑦⑧⑨⑩ ")
                if cleaned and any(ord(c) > 0x3000 for c in cleaned) and not cleaned.startswith("("):
                    test_lines.append(cleaned)
                    break
    if test_lines:
        items.append((
            f"{prefix}_listening.mp3",
            "Hörverständnis (Audio)",
            "\n".join(test_lines),
            5,
        ))

    return items


def update_database(lesson_number: int, audio_items: list[tuple[str, str, str, int]]):
    """Aktualisiert die DB: alte Audio-Einträge löschen, neue erstellen."""
    from app import create_app, db
    from app.models import Lesson, LessonContent, LessonPage

    app = create_app()
    with app.app_context():
        # Lektion finden
        lesson = Lesson.query.filter(Lesson.title.like(f"MNN L{lesson_number}:%")).first()
        if not lesson:
            print(f"  FEHLER: Lektion {lesson_number} nicht in DB gefunden!")
            return

        print(f"\n  Lektion gefunden: {lesson.title} (ID {lesson.id})")

        # Alte Audio-Einträge löschen
        old_audio = LessonContent.query.filter_by(
            lesson_id=lesson.id, content_type="audio"
        ).all()
        for old in old_audio:
            print(f"  [DEL] Alter Eintrag: {old.title} — {old.file_path}")
            db.session.delete(old)

        # LessonPages sicherstellen fuer Audio-Seiten (4=Practice, 5=Test)
        PAGE_TITLES = {4: "Practice", 5: "Test"}
        audio_page_numbers = set(item[3] for item in audio_items)
        for pn in audio_page_numbers:
            if pn in PAGE_TITLES:
                existing_page = LessonPage.query.filter_by(
                    lesson_id=lesson.id, page_number=pn
                ).first()
                if not existing_page:
                    new_page = LessonPage(lesson_id=lesson.id, page_number=pn, title=PAGE_TITLES[pn])
                    db.session.add(new_page)
                    print(f"  [NEW] LessonPage: Seite {pn} ({PAGE_TITLES[pn]})")

        # Neue Audio-Einträge erstellen
        for item in audio_items:
            filename, title, _text, page_number = item[0], item[1], item[2], item[3]
            rel_path = f"lessons/audio/mnn_lesson_{lesson_number:02d}/{filename}"
            content = LessonContent(
                lesson_id=lesson.id,
                content_type="audio",
                title=title,
                media_url=f"/uploads/{rel_path}",
                file_path=rel_path,
                file_type="audio/mpeg",
                original_filename=filename,
                page_number=page_number,
                order_index=0,  # Wird als erstes Element auf der Seite angezeigt
            )
            db.session.add(content)
            print(f"  [NEW] {title} → {rel_path} (Seite {page_number})")

        db.session.commit()
        print(f"\n  DB aktualisiert: {len(old_audio)} gelöscht, {len(audio_items)} neu.")


def delete_old_files(lesson_number: int):
    """Löscht die alten kopierten MNN-Dateien."""
    audio_dir = AUDIO_BASE / f"mnn_lesson_{lesson_number:02d}"
    old_files = list(audio_dir.glob("*.mp3"))
    # Nur Dateien mit dem alten Namensschema löschen (z.B. "01 - 01 - Kotoba.mp3")
    deleted = 0
    for f in old_files:
        if " - " in f.name:
            print(f"  [DEL] {f.name}")
            f.unlink()
            deleted += 1
    return deleted


def main():
    import argparse
    parser = argparse.ArgumentParser(description="TTS-Audio generieren für MNN-Lektionen")
    parser.add_argument("--lesson", type=int, default=1, help="Lektionsnummer (Standard: 1)")
    parser.add_argument("--dry-run", action="store_true", help="Nur anzeigen, nicht generieren")
    args = parser.parse_args()

    lesson_num = args.lesson

    # JSON laden
    json_file = DATA_DIR / f"beginner1_lesson{lesson_num:02d}.json"
    if not json_file.exists():
        # Versuche andere Pfade
        candidates = list(DATA_DIR.glob(f"*lesson{lesson_num:02d}*.json"))
        if candidates:
            json_file = candidates[0]
        else:
            print(f"FEHLER: Keine JSON-Datei für Lektion {lesson_num} gefunden!")
            sys.exit(1)

    print("=" * 60)
    print(f"TTS-Audio generieren: Lektion {lesson_num}")
    print(f"JSON: {json_file.name}")
    print(f"Stimme: {VOICE_NAME} (Google Cloud TTS Neural2)")
    print(f"Multi-Voice: {VOICE_FEMALE} (w), {VOICE_MALE_1} (m1), {VOICE_MALE_2} (m2)")
    print(f"Tempo: {SPEAKING_RATE}x")
    print("=" * 60)

    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Audio-Texte vorbereiten
    audio_items = build_audio_texts(data)
    print(f"\n{len(audio_items)} Audio-Dateien zu generieren:\n")

    for item in audio_items:
        filename, title, content, page = item[0], item[1], item[2], item[3]
        is_multi = len(item) > 4 and item[4] == "multi_voice"
        if is_multi:
            speakers = list({line["speaker"] for line in content})
            print(f"  Seite {page}: {filename} [MULTI-VOICE: {', '.join(speakers)}]")
            print(f"    {title}")
            for line in content:
                print(f"    {line['speaker']}: {line['japanese'][:50]}")
        else:
            preview = content[:80].replace("\n", " | ")
            print(f"  Seite {page}: {filename}")
            print(f"    {title}")
            print(f"    Text: {preview}...")
        print()

    if args.dry_run:
        print("DRY RUN — keine Dateien generiert.")
        return

    # Audio-Verzeichnis
    audio_dir = AUDIO_BASE / f"mnn_lesson_{lesson_num:02d}"
    audio_dir.mkdir(parents=True, exist_ok=True)

    # Google TTS Client
    print("Verbinde mit Google Cloud TTS...")
    client = get_google_tts_client()

    # Audio generieren
    print("\n--- Generiere Audio ---")
    for item in audio_items:
        filename, title, content, page = item[0], item[1], item[2], item[3]
        is_multi = len(item) > 4 and item[4] == "multi_voice"
        out_path = audio_dir / filename

        if is_multi:
            print(f"\n  [MULTI-VOICE] {filename}")
            generate_conversation_audio(client, content, out_path)
        else:
            generate_audio(client, content, out_path)

    # Alte Dateien löschen
    print("\n--- Lösche alte kopierte Dateien ---")
    deleted = delete_old_files(lesson_num)
    print(f"  {deleted} alte Dateien gelöscht.")

    # DB aktualisieren
    print("\n--- Aktualisiere Datenbank ---")
    update_database(lesson_num, audio_items)

    # Zusammenfassung
    print(f"\n{'=' * 60}")
    print(f"Fertig! {len(audio_items)} Audio-Dateien generiert.")
    new_files = sorted(audio_dir.glob("lesson*.mp3"))
    total_kb = 0
    for f in new_files:
        kb = f.stat().st_size // 1024
        total_kb += kb
        print(f"  {f.name:40s} {kb:>5d} KB")
    print(f"  {'TOTAL':40s} {total_kb:>5d} KB")
    print("=" * 60)


if __name__ == "__main__":
    main()
