# tests/integration/test_kana_options_consolidation.py
"""Integration-Tests für die Konsolidierung der Options-Menüs auf /practice/kana.

Beide Spiele (Zuordnung + Kana Storm) teilen sich auf /practice/kana EINEN
Scope (Schrift + Reihen) via $store.kanaScope. Die spielspezifischen Optionen
(Modus bzw. Dauer/Daily) bleiben pro Spiel. Die anderen Storm-Flächen (Vollbild,
Startseite, /daily) behalten ihre eigenen Picker (scope_external NICHT gesetzt).
"""


class TestConsolidatedScopeOnPracticeKana:
    """GET /practice/kana — ein geteilter Scope, keine doppelten Picker."""

    def test_shared_scope_panel_present(self, client, db):
        body = client.get('/practice/kana').get_data(as_text=True)
        # Geteilter Scope-Block existiert und ist an den Store gebunden.
        assert 'kana-setup__scope' in body
        assert '$store.kanaScope' in body
        # Store-Skript wird (global via base.html) geladen.
        assert 'kana_scope_store.js' in body

    def test_no_duplicate_pickers(self, client, db):
        body = client.get('/practice/kana').get_data(as_text=True)
        # Storm-interner Glyph-Schrift-Picker ist ausgeblendet (scope_external).
        # Diskriminierung über das @click-Markup (nicht den CSS-Klassennamen, der
        # über _kana_storm_styles.html immer im <style> steht): der Storm-Picker
        # nutzt @click="setSchrift(, der geteilte Scope @click="$store.kanaScope.
        assert '@click="setSchrift(' not in body
        # Matching-eigener Dakuten-Toggle ist entfallen (Dakuten = G–P-Chips im Scope).
        assert 'Dakuten / Handakuten' not in body

    def test_game_specific_options_remain(self, client, db):
        body = client.get('/practice/kana').get_data(as_text=True)
        # Modus (Zuordnung) und Dauer (Storm) bleiben spielspezifisch sichtbar.
        assert 'Schreiben' in body and 'Lesen' in body   # Modus-Segment (Matching)
        assert '60 Sek' in body and '120 Sek' in body     # Dauer-Segment (Storm)


class TestOtherStormSurfacesUnchanged:
    """Vollbild-Storm + Startseite behalten ihre EIGENEN Picker (kein Shared-Scope)."""

    def test_fullscreen_storm_keeps_own_pickers(self, client, db):
        body = client.get('/practice/kana/storm').get_data(as_text=True)
        # Eigener Glyph-Schrift-Picker bleibt (Markup, nicht nur CSS-Klasse);
        # kein geteiltes Scope-Panel.
        assert '@click="setSchrift(' in body
        assert 'kana-setup__scope' not in body

    def test_homepage_storm_keeps_own_pickers(self, client, db):
        body = client.get('/').get_data(as_text=True)
        assert '@click="setSchrift(' in body
        assert 'kana-setup__scope' not in body
