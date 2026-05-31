"""Integrationstest: /ueber verwendet durchgaengig CH-Deutsch (kein 'ß').

Hintergrund (Marketing-Task F3): Die oeffentliche /ueber-Seite ist Teil des
"Swiss-made"-Versprechens. Reichsdeutsches 'ß' bricht dieses Versprechen und
ist auf einer indexierten Schweizer Seite ein Glaubwuerdigkeits-Detail.
Dieser Test ist die Regressions-Sicherung: Sobald wieder ein 'ß' in den
/ueber-eigenen Inhalt rutscht, schlaegt er fehl.

Geprueft wird der seiten-eigene Inhaltsblock (".ueber-page"), nicht das
geerbte base.html-Geruest. Grund: base.html (Layout, Nav, globales CSS) gehoert
einem anderen Stream und kann eigenes 'ß' enthalten (Stand 2026-05-31: ein 'ß'
in einem CSS-Kommentar in base.html, ausserhalb dieses Scopes) — dieser Test
soll genau die /ueber-Inhaltsverantwortung absichern und nicht an fremdem
Layout-Code haengen bleiben.
"""


def _ueber_content(body: str) -> str:
    """Schneidet den seiten-eigenen Inhaltsblock (.ueber-page) aus dem HTML.

    Vom oeffnenden ".ueber-page"-Container bis zum seiten-eigenen <style>-Block
    (bzw. bis zum Body-Ende). So wird ausschliesslich der von dieser Seite
    verantwortete Fliesstext geprueft — nicht das geerbte base.html-Geruest.
    """
    start = body.find('<div class="ueber-page">')
    assert start != -1, "Inhaltsblock '.ueber-page' nicht im gerenderten /ueber gefunden."
    style = body.find("<style>", start)
    end = style if style != -1 else len(body)
    return body[start:end]


def test_ueber_enthaelt_kein_eszett(client):
    """GET /ueber rendert seinen Inhalt ohne 'ß' (Schweizer Rechtschreibung: 'ss')."""
    response = client.get("/ueber")

    assert response.status_code == 200
    content = _ueber_content(response.get_data(as_text=True))
    assert "ß" not in content, (
        "Der /ueber-Inhalt enthaelt ein 'ß' — auf einer Swiss-made-Seite muss "
        "durchgaengig 'ss' statt 'ß' verwendet werden."
    )
