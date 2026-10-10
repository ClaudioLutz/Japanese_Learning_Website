"""Karte 14: Strichfolge-Versprechen im Kanji-Modul ehrlich formulieren.

Die Ops in scripts/data/kanji_strichfolge_texte_fixes.json laufen über den
generischen Applier scripts/apply_audit_phase2.py (DRY-RUN-Default, exakte
Vorher/Nachher-Ersetzung). Hier wird nur geprüft, dass jede Op erlaubt ist,
genau einmal greift und ein zweiter Lauf nichts mehr ändert.
"""
import json
from pathlib import Path

from scripts import apply_audit_phase2 as a2

ROOT = Path(__file__).resolve().parents[2]
FIXES = ROOT / "scripts" / "data" / "kanji_strichfolge_texte_fixes.json"


def _ops() -> list[dict]:
    return json.loads(FIXES.read_text(encoding="utf-8"))["ops"]


def test_alle_ops_sind_im_applier_erlaubt():
    for op in _ops():
        assert op["column"] in a2.ALLOWED.get(op["table"], set()), op["id"]


def test_plan_greift_einmal_und_ist_idempotent():
    ops = _ops()
    ist = {}
    for op in ops:
        key = (op["table"], op["pk"], op["column"])
        ist[key] = op["old"] if op["mode"] == "full" else f"Davor\n{op['old']}\nDanach"
    cells, report = a2.plan(ops, lambda t, pk, col: ist[(t, pk, col)])
    assert [r[1] for r in report] == ["OK"] * len(ops)

    nachher = {key: neu for key, (_alt, neu) in cells.items()}
    _, report2 = a2.plan(ops, lambda t, pk, col: nachher[(t, pk, col)])
    assert [r[1] for r in report2] == ["SCHON"] * len(ops)


def test_neue_texte_versprechen_keine_strichfolge_je_kanji():
    neu = {op["id"]: op["new"] for op in _ops()}
    assert "Strich" not in neu["K01"]
    assert "inklusive Strichfolge" not in neu["K02"]
    assert "Grundregeln der Strichfolge" in neu["K02"]
    # Regel 4: Die rechte Seite des Rahmens kommt vor dem Inhalt, unten zuletzt.
    for op_id in ("K03", "K04"):
        assert "oben und rechts in einem Zug" in neu[op_id]
        assert "Klammer" not in neu[op_id]
