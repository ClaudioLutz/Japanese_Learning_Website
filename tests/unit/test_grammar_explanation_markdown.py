"""Grammatik-Karten-Rueckseite: **fett**/*kursiv*-Markdown in Erklaerung und
Nuance wird zu HTML gerendert (Filter ``markdown_inline``), inkl. Vollbreiten-
Klammern 「」 und gemischtem JP/DE-Text.

Regressionsschutz fuer den Fix, der ``| markdown_inline`` auf
``content_data.explanation`` und ``content_data.nuance`` anwendet
(app/templates/lesson_view.html). Vorher wurden die rohen ``**``-Marker
woertlich auf der Karte angezeigt.
"""

import pytest


@pytest.fixture
def md_inline(app):
    return app.jinja_env.filters["markdown_inline"]


def test_bold_with_fullwidth_brackets(md_inline):
    # Echtes Erklaerungsfragment der Karte "AはBじゃ ありません".
    out = str(md_inline("Statt **「です」** sagst du **「じゃ ありません」**."))
    assert "<strong>「です」</strong>" in out
    assert "<strong>「じゃ ありません」</strong>" in out
    assert "**" not in out  # keine rohen Marker mehr sichtbar


def test_italic_and_bold_mixed(md_inline):
    out = str(md_inline(
        "die **Kopula** (*ist/sind*). Das Partikel **「は」** wird *wa* gesprochen"
    ))
    assert "<strong>Kopula</strong>" in out
    assert "<em>ist/sind</em>" in out
    assert "<strong>「は」</strong>" in out
    assert "<em>wa</em>" in out


def test_plain_japanese_not_emphasised(md_inline):
    # Reiner JP-Satz ohne Marker darf NICHT kursiv/fett werden und bleibt erhalten.
    s = "「リサさんは がくせいです。たなかさんも がくせいです」"
    out = str(md_inline(s))
    assert "<em>" not in out and "<strong>" not in out
    assert "リサさん" in out and "がくせいです" in out


def test_no_block_paragraph_wrapper(md_inline):
    # Inline-Variante: kein <p>-Block, damit es im Karten-<p> gueltig bleibt.
    out = str(md_inline("Die **Negation**."))
    assert not out.startswith("<p>")
    assert out == "Die <strong>Negation</strong>."


def test_empty_and_none_are_safe(md_inline):
    assert md_inline("") == ""
    assert md_inline(None) == ""
