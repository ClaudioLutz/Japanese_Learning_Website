"""Geschlecht bekannter Dialog-Sprecher (Figuren der Lektionsdialoge).

Einzige Quelle fuer die Sprechername→Geschlecht-Tabelle: genutzt von der
Dialog-Audio-Pipeline (scripts/generate_tts_audio.py, generate-lesson-Skill)
und vom Rollenspiel (Stimme der Rolle beim Vorlesen, /api/tts voice_gender).
"""
from __future__ import annotations

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
    "Mei": "female",
    "Mori": "male",        # Dr. Mori (Arzt, Koerper-/Gesundheits-Lektion)
    # Casts der N5-Vokabel-Lektionen (Batch 2026-06-18)
    "Nina": "female",      # Schuelerin (Schule & Lernen)
    "Hana": "female",      # Tiere/Natur-Lektion
    "Leon": "male",        # Tiere/Natur-Lektion
    "Aya": "female",       # Freizeit/Medien-Lektion
    "Saki": "female",      # Verben-Lektion
    "Markus": "male",      # Verben-Lektion
    "Polizist": "male",    # Orte in der Stadt 2 (Batch 2026-09-26): Polizist am Koban
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


def speaker_gender(name: str | None) -> str | None:
    """'m' | 'f' | None (unbekannt) fuer einen Sprechernamen.

    Anders als die Audio-Pipeline raet diese Funktion NICHT: unbekannte Namen
    (z.B. „Kellner", „Passant") liefern None → Standardstimme.
    Toleriert Anrede-Suffixe (-san/さん/-sensei/先生) und Klammerzusaetze.
    """
    if not name:
        return None
    key = str(name).strip()
    candidates = [key]
    base = key.split('(')[0].split('（')[0].strip()
    for suffix in ('-sensei', ' sensei', '-san', ' san', 'せんせい', '先生', 'さん'):
        if base.lower().endswith(suffix.lower()):
            base = base[: len(base) - len(suffix)].strip()
            break
    candidates.append(base)
    if base:
        candidates.append(base[:1].upper() + base[1:])
    for cand in candidates:
        g = SPEAKER_GENDER.get(cand)
        if g == 'female':
            return 'f'
        if g == 'male':
            return 'm'
    return None
