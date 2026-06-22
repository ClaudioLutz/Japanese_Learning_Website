"""Regressionstest fuer die TTS-Stimmen-Geschlechts-Zuordnung.

Hintergrund (2026-06-22): Der Code benutzte ja-JP-Neural2-C faelschlich als
zweite *weibliche* Stimme. Laut offizieller Google-TTS-Voices-API
(texttospeech.googleapis.com/v1/voices) ist Neural2-C aber MALE -> jede
zweite Sprecherin in einem Dialog klang maennlich (User-Issue Lektion 204).

Dieser Test fixiert das bekannt-korrekte ssmlGender-Mapping fuer alle in
generate_tts_audio.py benutzten Stimmen und stellt sicher, dass
get_voice_for_speaker() einem weiblichen Sprecher NIE eine maennliche Stimme
gibt (und umgekehrt). Faengt genau diese Regression.
"""
import importlib

import pytest

tts = importlib.import_module("scripts.generate_tts_audio")

# Verifiziert gegen die Google-TTS-Voices-API (ssmlGender), Stand 2026-06-22.
KNOWN_VOICE_GENDER = {
    "ja-JP-Neural2-B": "female",
    "ja-JP-Neural2-C": "male",
    "ja-JP-Neural2-D": "male",
    "ja-JP-Wavenet-A": "female",
    "ja-JP-Wavenet-B": "female",
    "ja-JP-Wavenet-D": "male",
}


def test_voice_constants_have_correct_gender():
    """Die vier Multi-Voice-Konstanten muessen ihrem Namen entsprechen."""
    assert KNOWN_VOICE_GENDER[tts.VOICE_FEMALE] == "female"
    assert KNOWN_VOICE_GENDER[tts.VOICE_FEMALE_2] == "female"
    assert KNOWN_VOICE_GENDER[tts.VOICE_MALE_1] == "male"
    assert KNOWN_VOICE_GENDER[tts.VOICE_MALE_2] == "male"


def test_two_female_speakers_both_get_female_voices():
    """Der konkrete Issue-Fall: zwei Frauen (Lisa, Mei) -> beide weiblich,
    aber unterscheidbare Stimmen."""
    speakers = ["Lisa", "Mei"]
    lisa = tts.get_voice_for_speaker("Lisa", speakers)
    mei = tts.get_voice_for_speaker("Mei", speakers)
    assert KNOWN_VOICE_GENDER[lisa] == "female"
    assert KNOWN_VOICE_GENDER[mei] == "female"
    assert lisa != mei, "Zwei Sprecherinnen sollen klanglich unterscheidbar sein"


def test_two_male_speakers_both_get_male_voices():
    speakers = ["Tanaka", "Yamada"]
    a = tts.get_voice_for_speaker("Tanaka", speakers)
    b = tts.get_voice_for_speaker("Yamada", speakers)
    assert KNOWN_VOICE_GENDER[a] == "male"
    assert KNOWN_VOICE_GENDER[b] == "male"
    assert a != b


@pytest.mark.parametrize("speaker", [s for s, g in tts.SPEAKER_GENDER.items()])
def test_speaker_never_gets_opposite_gender_voice(speaker):
    """Kein Sprecher darf je eine Stimme des falschen Geschlechts bekommen —
    weder als erster noch als zweiter gleichgeschlechtlicher Sprecher."""
    expected = tts.SPEAKER_GENDER[speaker]
    # einzeln und als zweiter gleichgeschlechtlicher Sprecher pruefen
    for others in ([speaker], ["Lisa", speaker], ["Tanaka", speaker]):
        voice = tts.get_voice_for_speaker(speaker, others)
        assert KNOWN_VOICE_GENDER[voice] == expected, (
            f"{speaker} ({expected}) bekam {voice} "
            f"({KNOWN_VOICE_GENDER[voice]})"
        )
