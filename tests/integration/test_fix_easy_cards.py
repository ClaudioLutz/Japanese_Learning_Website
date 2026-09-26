"""scripts/analyze_easy_cards.py + scripts/fix_easy_cards.py gegen die Test-DB."""
import json
from datetime import datetime, timedelta, timezone

from fsrs import Card, Rating, Scheduler

from app.models import CardReviewState, ReviewLog
from scripts.analyze_easy_cards import fetch_candidates, summarize
from scripts.fix_easy_cards import apply_plans, build_plans
from tests.factories import LessonContentFactory, LessonFactory, UserFactory

NOW = datetime(2026, 9, 26, 12, 0, 0)


def _card(db, user, reviewed_at, ratings=(4,), source=None, status=None):
    """Karte mit echten FSRS-Reviews (Zeitpunkte ab reviewed_at) anlegen."""
    lesson = LessonFactory()
    lc = LessonContentFactory(lesson_id=lesson.id, content_type='vocabulary')
    db.session.flush()
    sched = Scheduler(enable_fuzzing=False)
    card = Card()
    t = reviewed_at.replace(tzinfo=timezone.utc)
    for i, r in enumerate(ratings):
        card, _ = sched.review_card(card, Rating(r), review_datetime=t)
        db.session.add(ReviewLog(user_id=user.id, content_id=lc.id, direction='forward',
                                 rating=r, reviewed_at=t.replace(tzinfo=None), source=source))
        t = t + timedelta(days=1 + i)
    state = CardReviewState(
        user_id=user.id, content_id=lc.id, direction='forward',
        fsrs_card_state=card.to_json(), due_date=card.due.replace(tzinfo=None),
        status=status or 'review', reps=len(ratings), lapses=0,
    )
    db.session.add(state)
    db.session.commit()
    return state


def test_kandidaten_und_korrektur(app, db):
    user = UserFactory()
    alt_easy = _card(db, user, datetime(2026, 9, 18, 10, 0))               # Kandidat
    deck_easy = _card(db, user, datetime(2026, 9, 17, 10, 0), source='deck')  # Kandidat
    neu_easy = _card(db, user, datetime(2026, 9, 21, 10, 0))               # nach Stichtag
    zwei = _card(db, user, datetime(2026, 9, 10, 10, 0), ratings=(4, 3))    # >1 Review
    good = _card(db, user, datetime(2026, 9, 18, 10, 0), ratings=(3,))      # nicht Easy
    review_src = _card(db, user, datetime(2026, 9, 18, 10, 0), source='review')
    susp = _card(db, user, datetime(2026, 9, 18, 10, 0), status='suspended')

    conn = db.session.connection()
    cands = fetch_candidates(conn, '2026-09-20')
    ids = {c.state_id for c in cands}
    assert ids == {alt_easy.id, deck_easy.id}
    s = summarize(cands, NOW, 30)
    assert s['total'] == 2 and s['due_gt_min'] == 0
    assert all(abs(c.stability - 8.2956) < 1e-3 for c in cands)

    plans = build_plans(conn, '2026-09-20', NOW, 14)
    assert len(plans) == 2
    for p in plans:
        assert p.new_stability < p.old_stability
        assert abs(p.new_stability - 2.3065) < 1e-3   # S0(Good)
        assert p.new_status == 'learning'
        assert p.new_due <= NOW + timedelta(days=14)

    written = apply_plans(conn, plans, NOW)
    db.session.commit()
    assert written == 2

    db.session.expire_all()
    fixed = db.session.get(CardReviewState, alt_easy.id)
    assert fixed.status == 'learning'
    assert abs(json.loads(fixed.fsrs_card_state)['stability'] - 2.3065) < 1e-3
    assert fixed.reps == 1  # Review-Anzahl bleibt
    # Nicht-Kandidaten unberuehrt
    for other in (neu_easy, zwei, good, review_src, susp):
        o = db.session.get(CardReviewState, other.id)
        assert o.status in ('review', 'learning', 'suspended')
        assert o.fsrs_card_state == other.fsrs_card_state

    # Idempotent: zweiter Lauf findet nichts mehr zu tun
    assert build_plans(db.session.connection(), '2026-09-20', NOW, 14) == []


def test_kappung_auf_14_tage(app, db):
    """Liegt die Neuberechnung weiter als 14 Tage weg, wird gekappt."""
    from scripts.fix_easy_cards import plan_card
    user = UserFactory()
    state = _card(db, user, datetime(2026, 9, 18, 10, 0))
    cand = fetch_candidates(db.session.connection(), '2026-09-20')[0]
    # Kuenstlich hohe Retention-Parameter → Neuberechnung liegt in der Vergangenheit;
    # „jetzt" weit vor dem Review simuliert den Kappungsfall.
    early_now = datetime(2026, 9, 1, 0, 0)
    p = plan_card(cand, early_now, cap_days=1)
    assert p is not None
    assert p.new_due <= early_now + timedelta(days=1)
    assert state.id == cand.state_id
