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
    """Vollbild-Storm + /daily behalten ihre EIGENEN Picker (kein Shared-Scope).
    Die Startseite teilt seit 2026-06-14 ebenfalls den Scope (beide Spiele via
    Umschalter) — siehe test_homepage_storm_uses_shared_scope."""

    def test_fullscreen_storm_keeps_own_pickers(self, client, db):
        body = client.get('/practice/kana/storm').get_data(as_text=True)
        # Eigener Glyph-Schrift-Picker bleibt (Markup, nicht nur CSS-Klasse);
        # kein geteiltes Scope-Panel.
        assert '@click="setSchrift(' in body
        assert 'kana-setup__scope' not in body

    def test_homepage_storm_uses_shared_scope(self, client, db):
        # Die Startseite bietet jetzt BEIDE Spiele (Storm + Zuordnung) ueber einen
        # Umschalter mit GETEILTEM Scope ($store.kanaScope) — der Storm-interne
        # Schrift-Picker ist dort ausgeblendet (scope_external), wie /practice/kana.
        body = client.get('/').get_data(as_text=True)
        assert 'scopeExternal: true' in body
        assert '$store.kanaScope' in body
        # Kein Storm-interner Schrift-Picker auf der Startseite (der geteilte Scope
        # nutzt @click="$store.kanaScope.setSchrift(, nicht @click="setSchrift().
        assert '@click="setSchrift(' not in body


class TestStormPlayHidesChrome:
    """Beim Storm-Spiel auf /practice/kana wird das Chrome (Kopf + geteilter Scope
    + Tabs) ausgeblendet, damit das Spiel den vollen Screen bekommt (nicht nur die
    untere Hälfte). Verdrahtung: Storm meldet seine Phase per Event nach oben, der
    Wrapper blendet via hideChrome aus."""

    def test_chrome_hide_wiring_present(self, client, db):
        body = client.get('/practice/kana').get_data(as_text=True)
        # Wrapper hört auf die Storm-Phase und berechnet hideChrome.
        assert 'kana-storm-phase' in body
        assert 'hideChrome' in body
        # Kopf, geteilter Scope und Tabs sind an hideChrome gekoppelt.
        assert body.count('x-show="!hideChrome"') >= 3

    def test_storm_partial_dispatches_phase(self, client, db):
        # Das Storm-Partial wird mit scope_external eingebunden (→ JS meldet Phase).
        body = client.get('/practice/kana').get_data(as_text=True)
        assert 'scopeExternal: true' in body
