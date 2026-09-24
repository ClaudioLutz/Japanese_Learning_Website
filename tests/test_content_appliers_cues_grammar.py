"""Tests fuer die Content-Applier production_cue_de (Welle 2) und N5-Grammatikluecken."""
from app.models import Grammar, Vocabulary
from scripts import apply_grammar_n5_gaps as ag
from scripts import apply_production_cues_batches as ac


def _vocab(db, vid, word, cue=None):
    v = Vocabulary(id=vid, word=word, reading=word, meaning='x', meaning_de='x',
                   jlpt_level=5, status='approved', created_by_ai=False,
                   production_cue_de=cue)
    db.session.add(v)
    return v


class TestCueData:
    def test_batches_valid_and_unique(self):
        items = ac.load_items()
        assert len(items) == 649
        assert all(ac.validate_cue(it['cue']) is None for it in items)

    def test_validate_rejects_japanese(self):
        assert ac.validate_cue('Tür (ドア)') is not None
        assert ac.validate_cue('   ') is not None
        assert ac.validate_cue('Tür (westlich)') is None


class TestApplyCues:
    def test_dry_run_writes_nothing(self, app_context, db):
        _vocab(db, 1, '駅')
        db.session.commit()
        stats = ac.apply_cues([{'id': 1, 'word': '駅', 'cue': 'Bahnhof'}], apply=False)
        assert stats['updated'] == 1
        assert db.session.get(Vocabulary, 1).production_cue_de is None

    def test_apply_only_fills_empty_and_matching_word(self, app_context, db):
        _vocab(db, 1, '駅')
        _vocab(db, 2, '人', cue='Person, Mensch')
        _vocab(db, 3, '山')
        db.session.commit()
        stats = ac.apply_cues([
            {'id': 1, 'word': '駅', 'cue': 'Bahnhof'},
            {'id': 2, 'word': '人', 'cue': 'ANDERS'},
            {'id': 3, 'word': '川', 'cue': 'Fluss'},
            {'id': 4, 'word': '海', 'cue': 'Meer'},
        ], apply=True)
        assert stats == {'updated': 1, 'already_set': 1, 'skipped': 2, 'rejected': 0}
        assert db.session.get(Vocabulary, 1).production_cue_de == 'Bahnhof'
        assert db.session.get(Vocabulary, 2).production_cue_de == 'Person, Mensch'
        assert db.session.get(Vocabulary, 3).production_cue_de is None


class TestGrammar:
    def test_data_valid(self):
        items = ag.load_items()
        assert len(items) == 9
        assert all(ag.validate_item(it) == [] for it in items)
        assert len({it['title'] for it in items}) == 9

    def test_validate_catches_romaji_in_tts(self):
        it = dict(ag.load_items()[0], tts_example_jp='ame ga futtara')
        assert any('tts' in e for e in ag.validate_item(it))

    def test_apply_idempotent(self, app_context, db):
        items = ag.load_items()
        assert ag.apply_grammar(items, apply=False)['created'] == 9
        assert Grammar.query.count() == 0
        assert ag.apply_grammar(items, apply=True)['created'] == 9
        g = Grammar.query.filter_by(title=items[0]['title']).one()
        assert g.jlpt_level == 5 and g.status == 'approved'
        again = ag.apply_grammar(items, apply=True)
        assert again == {'created': 0, 'exists': 9, 'invalid': 0}
        assert Grammar.query.count() == 9
