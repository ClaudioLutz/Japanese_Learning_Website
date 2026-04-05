# tests/unit/test_utils.py
"""
Phase 2: Unit-Tests für app/utils.py
Testkonzept-IDs: U-U01 bis U-U12
"""

import pytest
from app.utils import convert_to_embed_url, FileUploadHandler


# ── U-U01: YouTube URL Konvertierung ────────────────────────

class TestConvertToEmbedUrl:
    def test_standard_youtube_url(self):
        """U-U01: Standard YouTube URL → Embed URL."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        result = convert_to_embed_url(url)
        assert result == "https://www.youtube.com/embed/dQw4w9WgXcQ"

    def test_shortened_youtube_url(self):
        """U-U01: Kurze youtu.be URL → Embed URL."""
        url = "https://youtu.be/dQw4w9WgXcQ"
        result = convert_to_embed_url(url)
        assert result == "https://www.youtube.com/embed/dQw4w9WgXcQ"

    def test_already_embed_url(self):
        """U-U01: Embed URL bleibt unverändert."""
        url = "https://www.youtube.com/embed/dQw4w9WgXcQ"
        result = convert_to_embed_url(url)
        assert result == url

    def test_none_url(self):
        """U-U01: None gibt None zurück."""
        assert convert_to_embed_url(None) is None

    def test_empty_string(self):
        """U-U01: Leerer String gibt None zurück."""
        assert convert_to_embed_url("") is None

    def test_invalid_url(self):
        """U-U01: Ungültige URL gibt Original zurück."""
        url = "not-a-url"
        result = convert_to_embed_url(url)
        assert result == url


# ── U-U02: FileUploadHandler.allowed_file ────────────────────

class TestAllowedFile:
    def test_allowed_image_extension(self, app_context):
        """U-U02: .jpg ist erlaubte Bild-Erweiterung."""
        assert FileUploadHandler.allowed_file("test.jpg", "image") is True

    def test_allowed_video_extension(self, app_context):
        """U-U02: .mp4 ist erlaubte Video-Erweiterung."""
        assert FileUploadHandler.allowed_file("video.mp4", "video") is True

    def test_allowed_audio_extension(self, app_context):
        """U-U02: .mp3 ist erlaubte Audio-Erweiterung."""
        assert FileUploadHandler.allowed_file("audio.mp3", "audio") is True

    def test_disallowed_extension(self, app_context):
        """U-U02: .exe ist nicht erlaubt."""
        assert FileUploadHandler.allowed_file("malware.exe", "image") is False

    def test_no_extension(self, app_context):
        """U-U02: Datei ohne Erweiterung ist nicht erlaubt."""
        assert FileUploadHandler.allowed_file("noext", "image") is False

    def test_unknown_type_checks_all(self, app_context):
        """U-U02: Unbekannter Typ prüft alle Erweiterungen."""
        assert FileUploadHandler.allowed_file("test.png", "unknown") is True
        assert FileUploadHandler.allowed_file("test.exe", "unknown") is False


# ── U-U03: FileUploadHandler.get_file_type ───────────────────

class TestGetFileType:
    def test_image_type(self, app_context):
        """U-U03: .png wird als 'image' erkannt."""
        assert FileUploadHandler.get_file_type("photo.png") == "image"

    def test_video_type(self, app_context):
        """U-U03: .mp4 wird als 'video' erkannt."""
        assert FileUploadHandler.get_file_type("clip.mp4") == "video"

    def test_audio_type(self, app_context):
        """U-U03: .wav wird als 'audio' erkannt."""
        assert FileUploadHandler.get_file_type("sound.wav") == "audio"

    def test_unknown_type(self, app_context):
        """U-U03: .exe wird als None erkannt."""
        assert FileUploadHandler.get_file_type("file.exe") is None

    def test_no_extension(self, app_context):
        """U-U03: Datei ohne Erweiterung gibt None."""
        assert FileUploadHandler.get_file_type("noext") is None


# ── U-U04: FileUploadHandler.generate_unique_filename ────────

class TestGenerateUniqueFilename:
    def test_preserves_extension(self, app_context):
        """U-U04: Erweiterung bleibt erhalten."""
        result = FileUploadHandler.generate_unique_filename("photo.JPG")
        assert result.endswith(".jpg")

    def test_unique_filenames(self, app_context):
        """U-U04: Zwei Aufrufe erzeugen verschiedene Namen."""
        r1 = FileUploadHandler.generate_unique_filename("same.png")
        r2 = FileUploadHandler.generate_unique_filename("same.png")
        assert r1 != r2

    def test_no_extension_file(self, app_context):
        """U-U04: Datei ohne Erweiterung bekommt UUID."""
        result = FileUploadHandler.generate_unique_filename("noext")
        assert "_" in result  # UUID-Teil enthalten


# ── U-U05: FileUploadHandler.format_file_size ────────────────

class TestFormatFileSize:
    def test_zero_bytes(self):
        """U-U05: 0 Bytes."""
        assert FileUploadHandler.format_file_size(0) == "0 B"

    def test_bytes(self):
        """U-U05: 500 Bytes."""
        assert FileUploadHandler.format_file_size(500) == "500.0 B"

    def test_kilobytes(self):
        """U-U05: 1024 Bytes = 1.0 KB."""
        assert FileUploadHandler.format_file_size(1024) == "1.0 KB"

    def test_megabytes(self):
        """U-U05: 1'048'576 Bytes = 1.0 MB."""
        assert FileUploadHandler.format_file_size(1048576) == "1.0 MB"

    def test_gigabytes(self):
        """U-U05: 1 GB."""
        assert FileUploadHandler.format_file_size(1073741824) == "1.0 GB"


# ── U-U06: FileUploadHandler.get_supported_formats ───────────

class TestGetSupportedFormats:
    def test_image_formats(self, app_context):
        """U-U06: Image-Formate enthalten png, jpg."""
        formats = FileUploadHandler.get_supported_formats("image")
        assert "png" in formats
        assert "jpg" in formats

    def test_unknown_type(self, app_context):
        """U-U06: Unbekannter Typ gibt leere Liste."""
        assert FileUploadHandler.get_supported_formats("pdf") == []
