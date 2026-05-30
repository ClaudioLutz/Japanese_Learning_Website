"""Unit-Tests fuer den Verwechslungs-Cluster-Service (#3)."""
from app.services.kana_confusion import confusable_with, confusion_clusters


class TestConfusableWith:
    def test_known_pair_is_symmetric(self):
        assert 'ち' in confusable_with('さ')
        assert 'さ' in confusable_with('ち')

    def test_excludes_self(self):
        assert 'さ' not in confusable_with('さ')

    def test_unknown_char_returns_empty(self):
        assert confusable_with('猫') == set()
        assert confusable_with('') == set()

    def test_three_member_cluster(self):
        # ね / れ / わ bilden einen Dreier-Cluster
        partners = confusable_with('ね')
        assert {'れ', 'わ'}.issubset(partners)


class TestConfusionClusters:
    def test_requires_at_least_two_available(self):
        # Nur 'ね' verfuegbar -> der ねれわ-Cluster faellt raus
        assert confusion_clusters({'ね'}) == []

    def test_returns_intersection_with_available(self):
        clusters = confusion_clusters({'ね', 'れ', 'わ', 'あ'})
        # ねれわ ist ein Cluster; 'あ' allein (ohne 'お') ist keiner
        assert any(set(c) == {'ね', 'れ', 'わ'} for c in clusters)
        assert all(len(c) >= 2 for c in clusters)
        flat = {ch for c in clusters for ch in c}
        assert 'あ' not in flat

    def test_partial_cluster_kept_when_two_remain(self):
        # Von ねれわ nur ね + れ verfuegbar -> Cluster mit 2 Mitgliedern bleibt
        clusters = confusion_clusters({'ね', 'れ'})
        assert any(set(c) == {'ね', 'れ'} for c in clusters)

    def test_deterministic_order(self):
        a = confusion_clusters({'ね', 'れ', 'わ', 'さ', 'ち'})
        b = confusion_clusters({'ち', 'さ', 'わ', 'れ', 'ね'})
        assert a == b  # Reihenfolge unabhaengig von der Eingabe-Reihenfolge
