"""gen_dialog_slideshow.pick_dialog_page: «Dialog — …» schlägt «… fürs Gespräch»."""
import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

SCRIPT = (Path(__file__).resolve().parents[2] / ".claude" / "skills" / "generate-lesson"
          / "scripts" / "gen_dialog_slideshow.py")


def _load():
    sys.path.insert(0, str(SCRIPT.parent))
    spec = importlib.util.spec_from_file_location("_gen_dialog_slideshow_pick", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_titel_mit_dialog_am_anfang_gewinnt():
    mod = _load()
    pages = [SimpleNamespace(page_number=3, title="Vokabeln Teil 2 — Kleine Wörter fürs Gespräch"),
             SimpleNamespace(page_number=5, title="Dialog — Abendessen im Restaurant")]
    assert mod.pick_dialog_page(pages).page_number == 5


def test_fallback_enthaelt_stichwort():
    mod = _load()
    pages = [SimpleNamespace(page_number=1, title="Einführung"),
             SimpleNamespace(page_number=4, title="Ein Gespräch im Café")]
    assert mod.pick_dialog_page(pages).page_number == 4
    assert mod.pick_dialog_page([SimpleNamespace(page_number=1, title="Übung")]) is None
