"""Unit-Tests: Vorschlag „Heute sprechen" (pick_suggestion, ohne DB),
Sprechergeschlecht und Korrektur-Hilfsfunktionen."""
import json
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

from app.services.roleplay_overview import ch_label, group_by_module, pick_suggestion
from app.services.roleplay_service import correction_count, is_praise, session_corrections
from app.speaker_gender import speaker_gender

NOW = datetime(2026, 9, 26, 12, 0)


def scene(cid, ready=False, done_days_ago=None, module=1):
    return {
        'content_id': cid, 'lesson_id': cid * 10, 'lesson_title': f'L{cid}',
        'ready': ready, 'module_id': module, 'module_name': f'M{module}',
        'completed_at': NOW - timedelta(days=done_days_ago) if done_days_ago is not None else None,
    }


# Fixture-Daten: Modulreihenfolge 1..5; 2, 3, 4 abgeschlossen (4 zuletzt).
SCENES = [
    scene(1),
    scene(2, ready=True, done_days_ago=10),
    scene(3, ready=True, done_days_ago=5),
    scene(4, ready=True, done_days_ago=1),
    scene(5),
]


class TestPickSuggestion:
    def test_zuletzt_abgeschlossene_ungespielte_zuerst(self):
        r = pick_suggestion(SCENES, played_content_ids=set(), last_corrections={})
        assert r['kind'] == 'new' and r['scene']['content_id'] == 4

    def test_naechst_neuere_wenn_letzte_gespielt(self):
        r = pick_suggestion(SCENES, played_content_ids={4}, last_corrections={4: 3})
        assert r['kind'] == 'new' and r['scene']['content_id'] == 3

    def test_meiste_korrekturen_wenn_alles_gespielt(self):
        r = pick_suggestion(SCENES, played_content_ids={2, 3, 4}, last_corrections={2: 1, 3: 3, 4: 0})
        assert r['kind'] == 'retry' and r['scene']['content_id'] == 3 and r['corrections'] == 3

    def test_erste_bereite_ohne_korrekturen(self):
        r = pick_suggestion(SCENES, played_content_ids={2, 3, 4}, last_corrections={2: 0, 3: 0, 4: 0})
        assert r['kind'] == 'ready' and r['scene']['content_id'] == 2

    def test_nicht_bereite_szenen_nie_vorgeschlagen(self):
        r = pick_suggestion(SCENES, played_content_ids={2, 3, 4}, last_corrections={1: 9, 5: 9})
        assert r['scene']['ready'] is True

    def test_ohne_bereite_szene_erste_lektion_mit_dialog(self):
        r = pick_suggestion([scene(7), scene(8)], set(), {})
        assert r['kind'] == 'none' and r['scene']['content_id'] == 7

    def test_ganz_ohne_szenen(self):
        assert pick_suggestion([], set(), {}) == {'kind': 'none', 'scene': None}

    def test_abschluss_ohne_datum_nach_datierten(self):
        undated = scene(9, ready=True)
        r = pick_suggestion([undated, scene(2, ready=True, done_days_ago=30)], set(), {})
        assert r['scene']['content_id'] == 2


def test_group_by_module_haelt_reihenfolge():
    groups = group_by_module([scene(1, module=2), scene(2, ready=True, module=2), scene(3, module=1)])
    assert [g['module_id'] for g in groups] == [2, 1]
    assert groups[0]['ready_count'] == 1 and len(groups[0]['scenes']) == 2


def test_ch_label_schweizer_zeit():
    assert ch_label(datetime(2026, 9, 26, 12, 5)) == '26. September 2026, 14:05'
    assert ch_label(None) == ''


class TestSpeakerGender:
    @pytest.mark.parametrize('name,want', [
        ('Tanaka', 'm'), ('Lisa', 'f'), ('リサ', 'f'), ('Polizist', 'm'), ('Mama', 'f'),
        ('Tanaka-san', 'm'), ('Ueno-sensei', 'f'), ('tanaka', 'm'), ('Yamada (Kunde)', 'm'),
        ('Kellnerin', 'f'), ('Angestellte', 'f'), ('Verkäuferin', 'f'),
    ])
    def test_bekannte_namen(self, name, want):
        assert speaker_gender(name) == want

    @pytest.mark.parametrize('name', ['Kellner', 'Passant', 'Waiter', '', None, 'Unbekannt'])
    def test_unbekannt_ist_none_nicht_weiblich(self, name):
        assert speaker_gender(name) is None


def _sess(correction_json=None, turns=()):
    return SimpleNamespace(correction_json=correction_json, turns=list(turns))


def _turn(speaker, raw=None):
    return SimpleNamespace(speaker=speaker, raw_json=raw)


class TestCorrections:
    def test_aus_correction_json(self):
        items = [{'original': 'a', 'better': 'b', 'better_kana': 'び', 'explanation_de': 'x'}]
        assert session_corrections(_sess(json.dumps(items))) == items

    def test_fallback_letzter_bot_zug(self):
        raw = json.dumps({'correction': [{'original': 'a', 'better': 'a。', 'explanation_de': 'Lob'}]})
        s = _sess(None, [_turn('bot', json.dumps({'correction': []})), _turn('user'), _turn('bot', raw)])
        assert session_corrections(s)[0]['explanation_de'] == 'Lob'

    def test_kaputtes_json_leer(self):
        assert session_corrections(_sess('{kaputt', [_turn('bot', 'auch kaputt')])) == []

    def test_max_drei(self):
        items = [{'original': str(i), 'better': 'x', 'explanation_de': 'e'} for i in range(5)]
        assert len(session_corrections(_sess(json.dumps(items)))) == 3

    def test_lob_zaehlt_nicht(self):
        items = [
            {'original': 'コーヒー ください', 'better': 'コーヒー ください。', 'explanation_de': 'gut'},
            {'original': 'みず', 'better': 'みずを ください。', 'explanation_de': 'besser'},
        ]
        assert is_praise(items[0]) and not is_praise(items[1])
        assert correction_count(_sess(json.dumps(items))) == 1
