"""Tests fuer das Einhaengen der N5-Grammatikluecken und die Audit-Fachpruefungs-Ops."""
import json
from pathlib import Path

from app.models import Grammar, Lesson, LessonCategory, LessonContent, LessonPage
from scripts import apply_audit_phase2 as a2
from scripts import apply_grammar_einhaengen as ge

ROOT = Path(__file__).resolve().parent.parent


def _setup(db, entry, pages=7, extra_grammar_linked=False):
    cat = LessonCategory(id=entry['category_id'], name=f'Modul {entry["category_id"]}')
    db.session.add(cat)
    lesson = Lesson(id=entry['lesson_id'], title='L', lesson_type='free',
                    category_id=entry['category_id'], is_published=True)
    db.session.add(lesson)
    for p in range(1, pages + 1):
        db.session.add(LessonPage(lesson_id=lesson.id, page_number=p, title=f'S{p}', page_type='normal'))
        db.session.add(LessonContent(lesson_id=lesson.id, page_number=p, order_index=1,
                                     content_type='text', content_text='x', generated_by_ai=False))
    for i, t in enumerate(entry['grammar_titles']):
        db.session.add(Grammar(id=900 + i, title=t, explanation='e', jlpt_level=5, status='approved'))
    db.session.flush()
    if extra_grammar_linked:
        db.session.add(LessonContent(lesson_id=lesson.id, page_number=4, order_index=9,
                                     content_type='grammar', content_id=900, generated_by_ai=False))
    db.session.commit()
    return lesson


class TestPlanData:
    def test_plan_valid(self):
        entries = ge.load_plan()
        assert all(ge.validate_entry(e) == [] for e in entries)
        titles = [t for e in entries for t in e['grammar_titles']]
        gaps = {g['title'] for g in json.loads(
            (ROOT / 'scripts/data/grammar_n5_gaps.json').read_text(encoding='utf-8'))}
        assert len(titles) == 9 and set(titles) == gaps

    def test_validate_limits_three(self):
        e = dict(ge.load_plan()[0], grammar_titles=['a', 'b', 'c', 'd'])
        assert any('mehr als 3' in x for x in ge.validate_entry(e))


class TestApplyGrammar:
    def test_dry_run_writes_nothing(self, app_context, db):
        entry = ge.load_plan()[0]
        _setup(db, entry)
        stats = ge.apply_plan([entry], apply=False)
        assert stats['lessons'] == 1 and stats['pages'] == 1
        assert stats['items'] == 1 + len(entry['grammar_titles'])
        assert not stats['written']
        assert LessonPage.query.filter_by(lesson_id=entry['lesson_id']).count() == 7
        assert LessonContent.query.filter_by(content_type='grammar').count() == 0

    def test_apply_appends_page_and_is_idempotent(self, app_context, db):
        entry = ge.load_plan()[0]
        _setup(db, entry)
        before = {(c.id, c.page_number) for c in LessonContent.query.all()}
        stats = ge.apply_plan([entry], apply=True)
        assert stats['written']
        page = LessonPage.query.filter_by(lesson_id=entry['lesson_id'], page_number=8).one()
        assert page.title == entry['page_title']
        new = LessonContent.query.filter_by(lesson_id=entry['lesson_id'], page_number=8) \
            .order_by(LessonContent.order_index).all()
        assert [c.content_type for c in new] == ['text'] + ['grammar'] * len(entry['grammar_titles'])
        assert [c.content_id for c in new[1:]] == [900, 901, 902][:len(entry['grammar_titles'])]
        # bestehende Items unveraendert (nur angehaengt)
        assert before <= {(c.id, c.page_number) for c in LessonContent.query.all()}
        again = ge.apply_plan([entry], apply=True)
        assert again['already'] == 1 and again['items'] == 0

    def test_skips_wrong_module_or_unexpected_page(self, app_context, db):
        entry = ge.load_plan()[0]
        _setup(db, entry, pages=8)
        stats = ge.apply_plan([entry], apply=True)
        assert stats['skipped'] == 1 and not stats['written']
        wrong = dict(entry, category_id=99)
        assert ge.apply_plan([wrong], apply=False)['skipped'] == 1

    def test_already_linked_grammar_not_duplicated(self, app_context, db):
        entry = ge.load_plan()[0]
        _setup(db, entry, extra_grammar_linked=True)
        ge.apply_plan([entry], apply=True)
        assert LessonContent.query.filter_by(content_type='grammar', content_id=900).count() == 1


class TestAuditFachpruefung:
    def test_ops_plan_int_and_substr(self):
        data = json.loads((ROOT / 'scripts/data/audit_fachpruefung_fixes.json').read_text(encoding='utf-8'))
        db_state = {(o['table'], o['pk'], o['column']): o['old'] for o in data['ops']
                    if o['mode'] == 'full'}
        db_state.update({(o['table'], o['pk'], o['column']): f'A {o["old"]} B'
                         for o in data['ops'] if o['mode'] == 'substr'})
        cells, report = a2.plan(data['ops'], lambda t, pk, col: db_state[(t, pk, col)])
        assert all(st == 'OK' for _, st, _ in report)
        assert cells[('vocabulary', 17, 'jlpt_level')] == (4, 5)
        # zweiter Lauf auf dem neuen Stand: alles SCHON
        new_state = {k: v[1] for k, v in cells.items()}
        _, report2 = a2.plan(data['ops'], lambda t, pk, col: new_state[(t, pk, col)])
        assert all(st == 'SCHON' for _, st, _ in report2)

    def test_clear_augmented(self):
        d, changed = a2.clear_augmented({'augmented_html': '<p>alt</p>', 'x': 1})
        assert changed and d == {'augmented_html': None, 'x': 1}
        assert a2.clear_augmented({'generator': 'claude'})[1] is False
        assert a2.clear_augmented(None)[1] is False
        assert a2.clear_augmented('{"augmented_html": "<p/>"}')[1] is True
