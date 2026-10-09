# tests/unit/test_dark_mode_textfarben.py
"""
Dark Mode: feste Textfarben in den Seiten-Styles der SEO-/Landingpages.

Hintergrund (09.10.2026): Auf /jlpt-n5-schweiz und /ueber stand der Fliesstext im
Dunkelmodus als dunkelblauer Text (#2c3e50, ~1.5:1) auf dunkler Karte, die
Ueberschriften (#1a1a1a) sogar bei ~1.0:1. Ursache: eigene <style>-Bloecke mit
fest gesetzten Textfarben und KEIN [data-theme="dark"]-Gegenstueck fuer die
Grundfarbe (.n5ch-page) bzw. fuer p/li/h2 (.ueber-*).

Gesichert wird das Muster, nicht das Pixelbild (das prueft die Sichtkontrolle
mit Playwright):
  * Jede feste Textfarbe in einem Seiten-Style, die auf den Dark-Flaechen unter
    4.5:1 faellt, hat eine Regel `[data-theme="dark"] <selektor>`.
  * Jede Dark-Textfarbe der Seiten-Styles hat gegen die Dark-Flaechen >= 4.5:1
    (Tokens werden aus custom.css gelesen und aufgeloest).
"""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = ROOT / "app" / "templates"
CUSTOM_CSS = ROOT / "app" / "static" / "css" / "custom.css"

# Oeffentliche SEO-/Landingpages mit eigenem <style>-Block.
SEITEN = [
    "jlpt_n5_schweiz.html",
    "ueber.html",
    "lernmethode.html",
]

DARK_PREFIX = '[data-theme="dark"]'
MIN_KONTRAST = 4.5


# ── Farb-Helfer ─────────────────────────────────────────────

def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    if len(value) == 3:
        value = "".join(c * 2 for c in value)
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def _luminanz(rgb: tuple[int, int, int]) -> float:
    def kanal(c: int) -> float:
        v = c / 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4

    r, g, b = (kanal(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def kontrast(fg: str, bg: str) -> float:
    l1, l2 = _luminanz(_hex_to_rgb(fg)), _luminanz(_hex_to_rgb(bg))
    hell, dunkel = max(l1, l2), min(l1, l2)
    return (hell + 0.05) / (dunkel + 0.05)


# ── Token-Aufloesung aus custom.css ─────────────────────────

def _ohne_kommentare(css: str) -> str:
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def _tokens(block_regex: str) -> dict[str, str]:
    css = _ohne_kommentare(CUSTOM_CSS.read_text(encoding="utf-8"))
    tokens: dict[str, str] = {}
    for m in re.finditer(block_regex, css):
        for name, value in re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", m.group(1)):
            tokens[name] = value.strip()
    return tokens


DARK_TOKENS = _tokens(r'\[data-theme="dark"\]\s*\{([^{}]*)\}')
ROOT_TOKENS = _tokens(r"(?m)^:root\s*\{([^{}]*)\}")


def _aufloesen(value: str, tokens: dict[str, str], tiefe: int = 0) -> str | None:
    """Loest `#hex` bzw. `var(--x[, fallback])` zu einem Hexwert auf (sonst None)."""
    value = re.sub(r"\s*!important\s*$", "", value.strip())
    if re.fullmatch(r"#[0-9a-fA-F]{3}|#[0-9a-fA-F]{6}", value):
        return value
    m = re.fullmatch(r"var\((--[\w-]+)\s*(?:,\s*([^)]+))?\)", value)
    if m and tiefe < 6:
        name, fallback = m.group(1), m.group(2)
        if name in tokens:
            return _aufloesen(tokens[name], tokens, tiefe + 1)
        if fallback:
            return _aufloesen(fallback, tokens, tiefe + 1)
    return None


def _dark_hex(value: str) -> str | None:
    return _aufloesen(value, {**ROOT_TOKENS, **DARK_TOKENS})


# Dark-Flaechen, auf denen Text der Seiten-Styles landet: Seite, Karte, Indigo-Hero.
DARK_FLAECHEN = {
    "Seite": _dark_hex("var(--background-color)"),
    "Karte": _dark_hex("var(--card-background)"),
    "Indigo-Tint": _dark_hex("var(--kon-50)"),
}


# ── Seiten-Styles parsen ────────────────────────────────────

def _regeln(template: str) -> list[tuple[list[str], str | None]]:
    """(Selektorliste, color-Wert) je CSS-Regel im <style>-Block der Seite."""
    html = (TEMPLATES / template).read_text(encoding="utf-8")
    styles = "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", html, flags=re.S))
    styles = _ohne_kommentare(styles)
    regeln = []
    for selektor, body in re.findall(r"([^{}]+)\{([^{}]*)\}", styles):
        selektoren = [re.sub(r"\s+", " ", s).strip() for s in selektor.split(",")]
        selektoren = [s for s in selektoren if s and not s.startswith("@")]
        farbe = re.search(r"(?<![-\w])color\s*:\s*([^;]+?)\s*(?:;|$)", body.strip())
        regeln.append((selektoren, farbe.group(1) if farbe else None))
    return regeln


@pytest.mark.parametrize("template", SEITEN)
def test_fest_gesetzte_textfarben_haben_dark_gegenstueck(template):
    """Feste Textfarbe, die auf Dark-Flaechen < 4.5:1 hat, braucht eine Dark-Regel."""
    regeln = _regeln(template)
    dark_selektoren = {
        s[len(DARK_PREFIX):].strip()
        for selektoren, _ in regeln
        for s in selektoren
        if s.startswith(DARK_PREFIX)
    }
    fehlend = []
    for selektoren, farbe in regeln:
        if farbe is None or any(s.startswith(DARK_PREFIX) for s in selektoren):
            continue
        # Nur feste Hexfarben; var(--token) kippt im Dark von selbst mit.
        if not re.fullmatch(r"#[0-9a-fA-F]{3}|#[0-9a-fA-F]{6}", farbe):
            continue
        schlechteste = min(kontrast(farbe, bg) for bg in DARK_FLAECHEN.values())
        if schlechteste >= MIN_KONTRAST:
            continue
        for s in selektoren:
            if s not in dark_selektoren:
                fehlend.append(f"{s} {{ color: {farbe} }}  ({schlechteste:.2f}:1 im Dark)")
    assert not fehlend, (
        f"{template}: feste Textfarben ohne [data-theme=\"dark\"]-Gegenstueck "
        "(dunkler Text auf dunkler Flaeche):\n  " + "\n  ".join(fehlend)
    )


@pytest.mark.parametrize("template", SEITEN)
def test_dark_textfarben_erreichen_kontrast(template):
    """Jede Dark-Textfarbe der Seiten-Styles hat gegen alle Dark-Flaechen >= 4.5:1."""
    zu_schwach = []
    for selektoren, farbe in _regeln(template):
        if farbe is None or not any(s.startswith(DARK_PREFIX) for s in selektoren):
            continue
        hexwert = _dark_hex(farbe)
        if hexwert is None:
            continue
        for name, bg in DARK_FLAECHEN.items():
            wert = kontrast(hexwert, bg)
            if wert < MIN_KONTRAST:
                zu_schwach.append(f"{', '.join(selektoren)}: {farbe} ({hexwert}) auf {name} = {wert:.2f}:1")
    assert not zu_schwach, f"{template}: Dark-Textfarben unter {MIN_KONTRAST}:1:\n  " + "\n  ".join(zu_schwach)


def test_dark_tokens_vorhanden():
    """Ohne aufloesbare Dark-Tokens waeren beide Pruefungen oben wirkungslos."""
    for name, bg in DARK_FLAECHEN.items():
        assert bg is not None, f"Dark-Flaeche {name} nicht aufloesbar"
    for token in ("--text-color", "--text-light", "--text-muted", "--ai", "--matcha-text"):
        assert _dark_hex(f"var({token})") is not None, f"Dark-Token {token} nicht aufloesbar"


def test_pruefung_erkennt_den_urspruenglichen_fehler():
    """Gegenprobe: #2c3e50 / #1a1a1a auf den Dark-Flaechen waeren durchgefallen."""
    for farbe in ("#2c3e50", "#1a1a1a", "#15803d"):
        assert min(kontrast(farbe, bg) for bg in DARK_FLAECHEN.values()) < MIN_KONTRAST
