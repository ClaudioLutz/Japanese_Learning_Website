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
    Die Startseite teilt seit dem Redesign (2026-06-17) den Scope ueber die
    Launcher-Karte (beide Spiele via Umschalter) — siehe
    test_homepage_uses_shared_scope."""

    def test_fullscreen_storm_keeps_own_pickers(self, client, db):
        body = client.get('/practice/kana/storm').get_data(as_text=True)
        # Eigener Glyph-Schrift-Picker bleibt (Markup, nicht nur CSS-Klasse);
        # kein geteiltes Scope-Panel.
        assert '@click="setSchrift(' in body
        assert 'kana-setup__scope' not in body

    def test_homepage_uses_shared_scope(self, client, db):
        # Die Startseite teilt den Scope ($store.kanaScope) ueber die Launcher-Karte
        # (Schrift-Chips + Reihen-Pills), wie /practice/kana. Storm ist hier ein
        # Launcher (kein Inline-Spiel mehr) → kein scopeExternal-Inline-Storm.
        body = client.get('/').get_data(as_text=True)
        assert '$store.kanaScope' in body
        assert 'kana-hero-scope' in body
        # Kein Storm-interner Schrift-Picker auf der Startseite (der geteilte Scope
        # nutzt @click="$store.kanaScope.setSchrift(, nicht @click="setSchrift().
        assert '@click="setSchrift(' not in body
        # Kein Inline-Storm-Engine mehr im Hero.
        assert 'scopeExternal: true' not in body


class TestStormWeakOnlyOption:
    """Kana Storm bekommt — wie das Matching-Spiel — einen login-gated
    „Nur schwache Karten"-Schalter (SRS-lapses). Gäste sehen ihn nicht
    (kein User-State); eingeloggt schaltet er die Runde auf den weak_only-Pool."""

    def test_guest_does_not_see_weak_switch(self, client, db):
        body = client.get('/practice/kana/storm').get_data(as_text=True)
        # Gast hat keinen SRS-State → kein Schalter-Markup. Diskriminierung über
        # die @click-Verdrahtung (der Klassenname kstorm__switch steht über das
        # inline-<style> immer im Body, der Schalter-Button aber nur eingeloggt).
        assert '@click="toggleWeakOnly()"' not in body

    def test_logged_in_sees_weak_switch(self, auth_client, db):
        client, _user = auth_client
        body = client.get('/practice/kana/storm').get_data(as_text=True)
        # Eingeloggt: Schalter-Button mit Alpine-Verdrahtung vorhanden.
        assert '@click="toggleWeakOnly()"' in body
        assert 'class="kstorm__switch"' in body


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
