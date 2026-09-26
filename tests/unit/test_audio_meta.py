"""app.audio_meta: Block-Player-Dauer aus dem WAV-Header (ohne Auslieferung)."""
import wave

from app.audio_meta import audio_duration_seconds


def _write_wav(path, seconds, rate=24000):
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b'\x00\x00' * int(seconds * rate))


def test_wav_duration_from_url_and_file_path(tmp_path):
    _write_wav(tmp_path / 'lessons/text_audio/lesson_1/page_1_content_2.wav', 83.5)
    assert audio_duration_seconds('/uploads/lessons/text_audio/lesson_1/page_1_content_2.wav', tmp_path) == 83.5
    assert audio_duration_seconds('lessons/text_audio/lesson_1/page_1_content_2.wav?v=7', tmp_path) == 83.5


def test_mp3_uses_sibling_wav(tmp_path):
    _write_wav(tmp_path / 'a/x.wav', 12.25)
    (tmp_path / 'a/x.mp3').write_bytes(b'ID3')
    assert audio_duration_seconds('/uploads/a/x.mp3', tmp_path) == 12.25


def test_missing_external_and_traversal_give_none(tmp_path):
    (tmp_path / 'b').mkdir()
    (tmp_path / 'b/only.mp3').write_bytes(b'ID3')
    assert audio_duration_seconds('/uploads/nope.wav', tmp_path) is None
    assert audio_duration_seconds('/uploads/b/only.mp3', tmp_path) is None
    assert audio_duration_seconds('https://storage.googleapis.com/x/y.wav', tmp_path) is None
    assert audio_duration_seconds('/uploads/../../etc/passwd.wav', tmp_path) is None
    assert audio_duration_seconds('/other/route.wav', tmp_path) is None
    assert audio_duration_seconds(None, tmp_path) is None
    assert audio_duration_seconds('', tmp_path) is None


def test_broken_wav_gives_none(tmp_path):
    (tmp_path / 'c.wav').write_bytes(b'not a wav at all')
    assert audio_duration_seconds('/uploads/c.wav', tmp_path) is None
