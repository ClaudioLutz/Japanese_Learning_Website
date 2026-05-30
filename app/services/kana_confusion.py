"""Visuell verwechselbare Kana-Cluster (Hiragana + Katakana).

Kaltstart-Quelle fuer den gezielten Verwechslungs-Drill: solange noch kein
(oder zu wenig) Per-User-Signal vorliegt, liefern diese kanonischen Cluster
die Distraktor-Gruppen. Sobald genug echtes Signal (Modell `KanaConfusion`)
gesammelt ist, ueberlagert es diese statische Liste in der Priorisierung.

Jede Menge in `CONFUSION_SETS` ist eine Gruppe optisch leicht verwechselbarer
Kana (Spiegelungen, gleiche Grundform, Dakuten-Unterschied).

HINWEIS: Die Paar-Liste folgt etablierter Kana-Aehnlichkeits-Didaktik
(vgl. Yamada 2021, Visual-Similarity-Matrix). Vor breitem Rollout fachlich
durch Mayuko gegenlesen lassen (JLPT-Leitprinzip).
"""

# ── Kanonische Verwechslungs-Cluster ───────────────────────────────────
CONFUSION_SETS = [
    # Hiragana
    set('きさ'),      # き / さ
    set('さち'),      # さ / ち
    set('ぬめ'),      # ぬ / め
    set('ねれわ'),    # ね / れ / わ
    set('ぬね'),      # ぬ / ね
    set('るろ'),      # る / ろ
    set('そろ'),      # そ / ろ
    set('つう'),      # つ / う
    set('いり'),      # い / り
    set('はほ'),      # は / ほ
    set('まも'),      # ま / も
    set('すむ'),      # す / む
    set('あお'),      # あ / お
    # Katakana
    set('シツ'),      # シ / ツ
    set('ソン'),      # ソ / ン
    set('クワ'),      # ク / ワ
    set('ウクワ'),    # ウ / ク / ワ
    set('ナメ'),      # ナ / メ
    set('フブ'),      # フ / ブ (Dakuten)
    set('コユ'),      # コ / ユ
    set('チテ'),      # チ / テ
    set('ノメヌ'),    # ノ / メ / ヌ
]


def confusable_with(char):
    """Liefert die Zeichen, mit denen `char` leicht verwechselt wird.

    Beispiel: confusable_with('さ') -> {'ち', 'き'}.
    Unbekannte Zeichen -> leere Menge.
    """
    out = set()
    for cluster in CONFUSION_SETS:
        if char in cluster:
            out |= cluster
    out.discard(char)
    return out


def confusion_clusters(available_chars):
    """Liefert die verwechselbaren Cluster, eingeschraenkt auf verfuegbare Zeichen.

    Args:
        available_chars: Menge/Iterable freigeschalteter Kana-Zeichen.

    Returns:
        Liste von Listen (jede >= 2 Mitglieder, deterministisch sortiert).
        Cluster, von denen nach dem Schnitt mit `available_chars` weniger als
        zwei Zeichen uebrig bleiben, fallen raus. Duplikate werden entfernt.
    """
    available = set(available_chars)
    seen = set()
    clusters = []
    for cluster in CONFUSION_SETS:
        members = [c for c in sorted(cluster) if c in available]
        if len(members) < 2:
            continue
        sig = tuple(members)
        if sig in seen:
            continue
        seen.add(sig)
        clusters.append(members)
    return clusters
