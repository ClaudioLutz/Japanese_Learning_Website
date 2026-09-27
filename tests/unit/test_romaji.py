"""Unit-Tests: Kana → Romaji (app/romaji.py) und die Romaji-Ableitung im
Rollenspiel-Service (Bot-Zeile, Vorschlaege, Korrekturen, Nutzerzug)."""
from types import SimpleNamespace

import pytest

from app.romaji import is_kana_text, kana_to_romaji, romaji_or_empty
from app.services import roleplay_service as svc

WORDS = [
    # Aufgabenliste
    ("きょう", "kyō"),
    ("がっこう", "gakkō"),
    ("コーヒー", "kōhī"),
    ("こんにちは", "konnichiwa"),
    ("せんせい", "sensei"),
    ("とうきょう", "tōkyō"),
    ("おねえさん", "onēsan"),
    ("ぜんいん", "zen'in"),
    # Grundreihen / Hepburn-Sonderfaelle
    ("しち", "shichi"),
    ("つくえ", "tsukue"),
    ("ふじ", "fuji"),
    ("ちず", "chizu"),
    ("じしょ", "jisho"),
    # Yōon
    ("しゃしん", "shashin"),
    ("ちゃわん", "chawan"),
    ("りょこう", "ryokō"),
    ("ぎゅうにゅう", "gyūnyū"),
    ("びょういん", "byōin"),
    # Sokuon
    ("きって", "kitte"),
    ("ざっし", "zasshi"),
    ("まっちゃ", "maccha"),
    ("こっち", "kocchi"),
    ("ちょっと", "chotto"),
    # ん
    ("きんようび", "kin'yōbi"),
    ("せんえん", "sen'en"),
    ("さんびゃく", "sanbyaku"),
    ("しんぶん", "shinbun"),
    # Langvokale
    ("おかあさん", "okāsan"),
    ("おおきい", "ōkii"),
    ("すうじ", "sūji"),
    ("ええ", "ē"),
    ("おいしい", "oishii"),
    ("えいが", "eiga"),
    ("ありがとう", "arigatō"),
    # Katakana
    ("ケーキ", "kēki"),
    ("タクシー", "takushī"),
    ("パーティー", "pātī"),
    ("シェフ", "shefu"),
    ("ファミレス", "famiresu"),
    ("コンピューター", "konpyūtā"),
    ("ヴァイオリン", "vaiorin"),
    # Wortblock mit Partikel / Ausnahmen
    ("わたしは", "watashi wa"),
    ("こんばんは", "konbanwa"),
    ("はは", "haha"),
    ("なに", "nani"),
    ("いつも", "itsumo"),
    ("とても", "totemo"),
    ("のんで", "nonde"),
]


@pytest.mark.parametrize("kana, want", WORDS)
def test_woerter(kana, want):
    assert kana_to_romaji(kana) == want


SENTENCES = [
    ("リサさん、なにが のみたいですか？", "Risa-san, nani ga nomitai desu ka?"),
    ("わたしは コーヒーが いいです。", "Watashi wa kōhī ga ii desu."),
    ("すみません。コーヒーを ください。", "Sumimasen. Kōhī o kudasai."),
    ("がっこうへ いきます。", "Gakkō e ikimasu."),
    ("がっこうには いきません。", "Gakkō ni wa ikimasen."),
    ("レストランで たべます。", "Resutoran de tabemasu."),
    ("パンも いいですね。", "Pan mo ii desu ne."),
    ("ケーキも ありますよ。", "Kēki mo arimasu yo."),
    ("のんで ください。", "Nonde kudasai."),
    ("ありがとう ございます！", "Arigatō gozaimasu!"),
    ("はい、そうです。", "Hai, sō desu."),
]


@pytest.mark.parametrize("kana, want", SENTENCES)
def test_saetze_mit_grossschreibung(kana, want):
    assert kana_to_romaji(kana, capitalize=True) == want


def test_leer_und_none():
    assert kana_to_romaji("") == "" and kana_to_romaji(None) == ""


def test_kanji_werden_durchgereicht():
    assert "食" in kana_to_romaji("食べます")


@pytest.mark.parametrize("text, want", [
    ("こうちゃが のみたいです。", True),
    ("コーヒー", True),
    ("はい！", True),
    ("何を 食べますか。", False),
    ("kohi", False),
    ("。", False),
    ("", False),
    (None, False),
])
def test_is_kana_text(text, want):
    assert is_kana_text(text) is want


def test_romaji_or_empty():
    assert romaji_or_empty("はい。") == "Hai."
    assert romaji_or_empty("日本です。") == ""


# ── Ableitung im Service ────────────────────────────────────────────────

class TestServiceRomaji:
    def test_line_romaji_aus_lesung(self):
        assert svc.line_romaji("何を 食べたいですか。", "なにを たべたいですか。") == "Nani o tabetai desu ka."

    def test_line_romaji_ohne_lesung_nur_bei_kana(self):
        assert svc.line_romaji("はい、どうぞ。", "") == "Hai, dōzo."
        assert svc.line_romaji("何ですか。", "") == ""
        assert svc.line_romaji("何ですか。", "何ですか。") == ""   # Lesung mit Kanji → keine Romaji

    def test_vorschlaege(self):
        out = svc.with_romaji_suggestions([
            {"jp": "水を ください。", "reading_kana": "みずを ください。", "de": "Wasser."},
            {"jp": "コーヒーが いいです。", "de": "Kaffee."},          # alt: ohne reading_kana
            {"jp": "水です。", "de": "Wasser."},                       # alt + Kanji → keine Romaji
            "kaputt",
        ])
        assert [s["romaji"] for s in out] == ["Mizu o kudasai.", "Kōhī ga ii desu.", ""]
        assert out[0]["jp"] == "水を ください。"

    def test_korrekturen(self):
        out = svc.with_romaji_corrections([
            {"original": "コーヒー ください", "better": "コーヒーを ください。", "explanation_de": "を"},
            {"original": "x", "better": "水を ください。", "better_kana": "みずを ください。", "explanation_de": "y"},
        ])
        assert [c["better_romaji"] for c in out] == ["Kōhī o kudasai.", "Mizu o kudasai."]

    def test_vorschlag_lesung_wird_validiert_und_katakana_restauriert(self):
        out = svc.validate_turn_payload({
            "bot_line_jp": "なにが いいですか。", "reading_kana": "なにが いいですか。", "de": "Was?",
            "hint_de": "", "done": False, "correction": [],
            "suggestions": [{"jp": "コーヒーが いいです。", "reading_kana": "こーひーが いいです。", "de": "Kaffee."}],
        })
        assert out["suggestions"][0]["reading_kana"] == "コーヒーが いいです。"

    def test_korrektur_lesung_wird_validiert(self):
        out = svc.validate_turn_payload({
            "bot_line_jp": "さようなら。", "reading_kana": "さようなら。", "de": "Tschüss.",
            "hint_de": "", "done": True, "suggestions": [],
            "correction": [{"original": "a", "better": "水です。", "better_kana": "みずです。", "explanation_de": "x"}],
        })
        assert out["correction"][0]["better_kana"] == "みずです。"

    def test_schema_verlangt_lesungen(self):
        props = svc.ROLEPLAY_TOOL["input_schema"]["properties"]
        assert props["suggestions"]["items"]["required"] == ["jp", "reading_kana", "de"]
        assert "better_kana" in props["correction"]["items"]["required"]
        assert svc.DETAILS_SCHEMA["properties"]["suggestions"]["items"]["required"] == ["jp", "reading_kana", "de"]

    def test_prompt_nennt_lesung_der_vorschlaege(self):
        prompt = svc.build_system_prompt({"lines": [], "scene_de": ""}, "Gast", "Kellner", None, [])
        assert "jp + reading_kana + de" in prompt
        assert "better_kana" in prompt

    def test_user_romaji(self):
        session = SimpleNamespace(turns=[
            SimpleNamespace(speaker="user", turn_index=1, text_jp="こうちゃが のみたいです。"),
            SimpleNamespace(speaker="user", turn_index=3, text_jp="水が のみたいです。"),
        ])
        assert svc.user_romaji(session, SimpleNamespace(turn_index=2)) == "Kōcha ga nomitai desu."
        assert svc.user_romaji(session, SimpleNamespace(turn_index=4)) == ""
        assert svc.user_romaji(session, None) == ""
