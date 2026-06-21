# app/dashboard_service.py
"""Datenaggregation fuer das Lernenden-Dashboard „Mein Lernen".

Eigenes Modul (nicht srs_service), damit Dashboard-Tracks parallel arbeiten
koennen. Liefert die Formen aus docs/dashboard_contract.md. Reife-Einteilung
kommt aus der Single Source gamification_service.maturity_bucket().
"""
import logging
from datetime import datetime, timedelta

from sqlalchemy import case, func

from app import db
from app.gamification_service import get_card_stage, maturity_bucket
from app.models import (
    CardReviewState,
    DailyReviewAggregate,
    Kana,
    KanaConfusion,
    Kanji,
    LessonContent,
    ReviewLog,
    User,
)

logger = logging.getLogger(__name__)

# Content-Typ -> Anzeige-Label (Skill).
_TYPE_LABEL = {
    'kana': 'Kana',
    'kanji': 'Kanji',
    'vocabulary': 'Vokabeln',
    'grammar': 'Grammatik',
}

# content_type (DB) der vier echten Kompass-Saeulen. „Hoeren" gibt es bewusst
# NICHT (keine Datenbasis — Entscheidung 2026-06-15).
PILLAR_CONTENT_TYPES = ('kana', 'kanji', 'vocabulary', 'grammar')

# Saeulen-Metadaten (Reihenfolge = Anzeige). key = Frontend-Schluessel,
# ctype = LessonContent.content_type.
_PILLAR_META = [
    {'key': 'kana',    'ctype': 'kana',       'name': 'Kana',      'icon': 'fa-spell-check',     'target_pct': 95, 'cta': 'Drill'},
    {'key': 'kanji',   'ctype': 'kanji',      'name': 'Kanji',     'icon': 'fa-pen-nib',         'target_pct': 80, 'cta': 'Weiterlernen'},
    {'key': 'vocab',   'ctype': 'vocabulary', 'name': 'Vokabeln',  'icon': 'fa-book',            'target_pct': 80, 'cta': 'Thema üben'},
    {'key': 'grammar', 'ctype': 'grammar',    'name': 'Grammatik', 'icon': 'fa-diagram-project', 'target_pct': 80, 'cta': 'Muster üben'},
]

# Reife-Gewichte fuer die „beherrscht"-Schaetzung (1:1 mit dem Frontend
# masteryPct: [Neu, Lernen, Jung, Reif, Gemeistert]).
_MASTERY_WEIGHTS = (0, 0.35, 0.65, 0.9, 1.0)


def _accuracy_by_content(user_id):
    """content_id -> Accuracy in % (Anteil Ratings >= 3), ueber alle ReviewLogs.

    Gleiches Muster wie api_kana_heatmap (srs_routes.py).
    """
    rows = (
        db.session.query(
            ReviewLog.content_id,
            func.count(ReviewLog.id).label('total'),
            func.sum(case((ReviewLog.rating >= 3, 1), else_=0)).label('correct'),
        )
        .filter(ReviewLog.user_id == user_id)
        .group_by(ReviewLog.content_id)
        .all()
    )
    return {
        r.content_id: (int(r.correct or 0) / int(r.total or 1) * 100)
        for r in rows
    }


def maturity_by_type(user_id):
    """Pro Content-Typ die 5-Bucket-Reifeverteilung + Anzahl begonnener Karten.

    Returns:
        {content_type: {'dist': [neu,lernen,jung,reif,gemeistert], 'started': int}}
        fuer jeden Typ in PILLAR_CONTENT_TYPES.
    """
    result = {t: {'dist': [0] * 5, 'started': 0} for t in PILLAR_CONTENT_TYPES}

    rows = (
        db.session.query(CardReviewState, LessonContent.content_type)
        .join(LessonContent, CardReviewState.content_id == LessonContent.id)
        .filter(
            CardReviewState.user_id == user_id,
            CardReviewState.direction == 'forward',  # Produktion zaehlt nicht doppelt
            LessonContent.content_type.in_(PILLAR_CONTENT_TYPES),
        )
        .all()
    )
    for state, ctype in rows:
        bucket_data = result[ctype]
        bucket_data['started'] += 1
        stage_idx, _, _ = get_card_stage(state.fsrs_card_state)
        b = maturity_bucket(state.status, stage_idx)
        if b is not None:  # suspendierte Karten zaehlen als „begonnen", aber nicht in dist
            bucket_data['dist'][b] += 1
    return result


def pillar_totals():
    """N5-Totale (Nenner) je Saeule.

    kana = alle Kana in der DB (N5-Kana-Satz, ~200); kanji/vocab = canonical
    N5-Listen (coverage_service); grammar = N5-Grammatik in der DB (Fallback 80).
    """
    from app.models import Grammar
    from app.services.coverage_service import get_jlpt_coverage

    totals = {'kana': 0, 'kanji': 80, 'vocabulary': 710, 'grammar': 80}
    try:
        totals['kana'] = db.session.query(func.count(Kana.id)).scalar() or 0
    except Exception:  # pragma: no cover - defensiv
        logger.exception('pillar_totals: Kana-Count fehlgeschlagen')
    try:
        cov = get_jlpt_coverage(5)
        totals['kanji'] = cov.get('kanji_total') or totals['kanji']
        totals['vocabulary'] = cov.get('vocab_total') or totals['vocabulary']
    except Exception:  # pragma: no cover - defensiv (Canonical-Datei fehlt etc.)
        logger.exception('pillar_totals: JLPT-Coverage fehlgeschlagen, Fallback-Werte')
    try:
        grammar_n5 = db.session.query(func.count(Grammar.id)).filter(Grammar.jlpt_level == 5).scalar() or 0
        if grammar_n5:
            totals['grammar'] = grammar_n5
    except Exception:  # pragma: no cover - defensiv
        logger.exception('pillar_totals: Grammar-Count fehlgeschlagen')
    return totals


def _mastery_pct(dist, total):
    """Reife-gewichtete „beherrscht"-Schaetzung in % (wie Frontend masteryPct)."""
    if not total:
        return 0.0
    weighted = sum(c * w for c, w in zip(dist, _MASTERY_WEIGHTS))
    return weighted / total * 100


def _sowhat(key, mastery_pct, started, total):
    """Kurzer, datengetriebener „so what"-Hinweis je Saeule (ehrlich zu den Zahlen)."""
    if started == 0:
        return 'Noch nicht begonnen — ein guter nächster Schritt.'
    if mastery_pct >= 66:
        return 'Solide — hier geht es nur noch um Feinschliff.'
    if mastery_pct >= 33:
        return 'Im Aufbau — dranbleiben festigt es.'
    return 'Grösster Hebel — hier holst du am meisten heraus.'


def compass_pillars(user_id):
    """Baut die 4 Kompass-Saeulen (Server-Context). Reihenfolge = _PILLAR_META.

    Jede Saeule: {key,name,icon,target_pct,cta,started,total,dist[5],sowhat}.
    Ring-/Zonen-/Readiness-Mathe bleibt clientseitig (aus dist+total).
    """
    by_type = maturity_by_type(user_id)
    totals = pillar_totals()
    pillars = []
    for meta in _PILLAR_META:
        ctype = meta['ctype']
        dist = by_type[ctype]['dist']
        started = by_type[ctype]['started']
        total = totals.get(ctype, 0) or max(started, 1)
        mastery = _mastery_pct(dist, total)
        pillars.append({
            'key': meta['key'],
            'name': meta['name'],
            'icon': meta['icon'],
            'targetPct': meta['target_pct'],  # camelCase: Frontend liest p.targetPct
            'cta': meta['cta'],
            'started': started,
            'total': total,
            'dist': dist,
            'sowhat': _sowhat(meta['key'], mastery, started, total),
        })
    return pillars


def learner_numbers(user_id):
    """„Mein Japanisch in Zahlen" — begonnene Items je Typ (Count-up-Kacheln)."""
    by_type = maturity_by_type(user_id)
    return {
        'kanji': by_type['kanji']['started'],
        'vocab': by_type['vocabulary']['started'],
        'grammar': by_type['grammar']['started'],
        'kana': by_type['kana']['started'],
    }


# Reftabelle + Feld-Mapping je Glyph-Typ. on/kun/mean werden auf die
# Prototyp-Felder gemappt.
_GLYPH_REF = {
    'kana': Kana,
    'kanji': Kanji,
}


def compass_glyphs(user_id, content_type):
    """Per-Item-Detail (Glyph-Grid) fuer kana/kanji.

    Returns Liste [{c, on, kun, mean, acc, reps}] fuer Items, auf die der User
    eine Karte hat — sortiert nach Accuracy absteigend (Gemeistertes zuerst).
    Vocab (Themen) und Grammatik (Muster) nutzen eigene Ansichten und sind hier
    bewusst nicht abgedeckt.
    """
    if content_type not in _GLYPH_REF:
        return []
    ref = _GLYPH_REF[content_type]

    rows = (
        db.session.query(CardReviewState, ref)
        .join(LessonContent, CardReviewState.content_id == LessonContent.id)
        .join(ref, LessonContent.content_id == ref.id)
        .filter(
            CardReviewState.user_id == user_id,
            CardReviewState.direction == 'forward',
            LessonContent.content_type == content_type,
        )
        .all()
    )
    acc_by_content = _accuracy_by_content(user_id)

    result = []
    for state, item in rows:
        if content_type == 'kana':
            c, on, kun, mean = item.character, item.romanization, None, item.romanization
        else:  # kanji
            c, on, kun, mean = item.character, (item.onyomi or ''), (item.kunyomi or ''), item.meaning
        result.append({
            'c': c,
            'on': on,
            'kun': kun,
            'mean': mean,
            'acc': round(acc_by_content.get(state.content_id, 0), 1),
            'reps': state.reps or 0,
        })
    result.sort(key=lambda x: x['acc'], reverse=True)
    return result


# ════════════════════════════════════════════════════════════════════
#  Statistik-Bundle (Lazy-Fetch fuer die „Statistiken ansehen"-Disclosure)
#  Ein Endpoint /api/dashboard/stats liefert alle Tab-Daten in einem Call.
#  Datumsaggregation bewusst in Python (dialektneutral -> laeuft auf SQLite
#  im Test und Postgres in Prod gleich).
# ════════════════════════════════════════════════════════════════════

def _swiss(n):
    """Schweizer Tausendertrennung mit Apostroph: 9840 -> 9'840."""
    return f"{int(n):,}".replace(',', '’')


def _stage5(stage_idx):
    """Reine Stufen-Einteilung (0..9 -> 5 Buckets) fuer die accByStage-Kurve.
    Anders als maturity_bucket (status-basiert), weil ReviewLog nur die Stufe
    speichert: 0=Neu, 1-2=Lernen, 3-4=Jung, 5-6=Reif, 7+=Gemeistert.
    """
    if stage_idx <= 0:
        return 0
    if stage_idx <= 2:
        return 1
    if stage_idx <= 4:
        return 2
    if stage_idx <= 6:
        return 3
    return 4


def tempo_stats(user_id):
    """KPIs + Wochen-/Wochentags-Zeitreihen aus DailyReviewAggregate."""
    aggs = (
        DailyReviewAggregate.query
        .filter_by(user_id=user_id)
        .order_by(DailyReviewAggregate.review_date.asc())
        .all()
    )
    user = User.query.get(user_id)
    longest = (user.longest_streak or 0) if user else 0

    if not aggs:
        return {
            'kpi': {'avgReviews': 0, 'avgSession': 0, 'longestStreak': longest, 'wordsPerWeek': 0},
            'reviewsByWeek': [0] * 8, 'accuracyByWeek': [0] * 8, 'reviewsByWeekday': [0] * 7,
        }

    n_days = len(aggs)
    sum_reviews = sum(a.total_reviews for a in aggs)
    sum_time = sum(a.total_time_ms or 0 for a in aggs)
    sum_new = sum(a.new_cards_learned or 0 for a in aggs)
    span_days = (aggs[-1].review_date - aggs[0].review_date).days + 1
    weeks = max(1.0, span_days / 7.0)

    kpi = {
        'avgReviews': round(sum_reviews / n_days),
        'avgSession': round(sum_time / n_days / 60000),  # ms -> Minuten/aktivem Tag
        'longestStreak': longest,
        'wordsPerWeek': round(sum_new / weeks),
    }

    # Letzte 8 ISO-Wochen (alt -> neu)
    today = datetime.utcnow().date()
    week_keys = []
    for i in range(8):
        iso = (today - timedelta(days=7 * i)).isocalendar()
        week_keys.append((iso[0], iso[1]))
    week_keys.reverse()
    week_idx = {k: i for i, k in enumerate(week_keys)}
    wk_total = [0] * 8
    wk_correct = [0] * 8
    for a in aggs:
        iso = a.review_date.isocalendar()
        i = week_idx.get((iso[0], iso[1]))
        if i is not None:
            wk_total[i] += a.total_reviews
            wk_correct[i] += a.correct_reviews
    reviews_by_week = wk_total
    accuracy_by_week = [round(wk_correct[i] / wk_total[i] * 100) if wk_total[i] else 0 for i in range(8)]

    # Wochentag-Mittel (Mo..So)
    wd_sum = [0] * 7
    wd_days = [0] * 7
    for a in aggs:
        wd = a.review_date.weekday()
        wd_sum[wd] += a.total_reviews
        wd_days[wd] += 1
    reviews_by_weekday = [round(wd_sum[i] / wd_days[i]) if wd_days[i] else 0 for i in range(7)]

    return {
        'kpi': kpi,
        'reviewsByWeek': reviews_by_week,
        'accuracyByWeek': accuracy_by_week,
        'reviewsByWeekday': reviews_by_weekday,
    }


def acc_by_stage(user_id):
    """Genauigkeit (Rating>=3) je SRS-Stufe-Bucket — aus ReviewLog.stage_at_review.

    Liefert [neu,lernen,jung,reif,gemeistert]. Buckets ohne Daten -> 0.
    """
    rows = (
        db.session.query(ReviewLog.stage_at_review, ReviewLog.rating)
        .filter(ReviewLog.user_id == user_id, ReviewLog.stage_at_review.isnot(None))
        .all()
    )
    total = [0] * 5
    correct = [0] * 5
    for stage, rating in rows:
        b = _stage5(stage)
        total[b] += 1
        if rating >= 3:
            correct[b] += 1
    return [round(correct[i] / total[i] * 100) if total[i] else 0 for i in range(5)]


def retention_by_maturity(user_id):
    """True Retention (30 Tage) + Genauigkeit je Reife (neu/jung/reif).

    value = Anteil korrekter Reviews der letzten 30 Tage.
    neu/jung/reif = Genauigkeit nach stage_at_review (all-time, stabiler).
    """
    cutoff = datetime.utcnow() - timedelta(days=30)
    recent = (
        db.session.query(ReviewLog.rating)
        .filter(ReviewLog.user_id == user_id, ReviewLog.reviewed_at >= cutoff)
        .all()
    )
    r_total = len(recent)
    r_correct = sum(1 for (rating,) in recent if rating >= 3)
    value = round(r_correct / r_total * 100) if r_total else 0

    rows = (
        db.session.query(ReviewLog.stage_at_review, ReviewLog.rating)
        .filter(ReviewLog.user_id == user_id, ReviewLog.stage_at_review.isnot(None))
        .all()
    )
    buckets = {'neu': [0, 0], 'jung': [0, 0], 'reif': [0, 0]}  # [total, correct]
    for stage, rating in rows:
        if stage <= 0:
            key = 'neu'
        elif stage <= 4:
            key = 'jung'
        else:
            key = 'reif'
        buckets[key][0] += 1
        if rating >= 3:
            buckets[key][1] += 1

    def _pct(key):
        t, c = buckets[key]
        return round(c / t * 100) if t else 0

    return {'value': value, 'neu': _pct('neu'), 'jung': _pct('jung'), 'reif': _pct('reif')}


def maturity_by_skill(user_id):
    """Reife-Verteilung pro Skill fuer den Reife-Tab (gestapelte Balken)."""
    by_type = maturity_by_type(user_id)
    return [{'k': _TYPE_LABEL[t], 'dist': by_type[t]['dist']} for t in PILLAR_CONTENT_TYPES]


def records(user_id):
    """Persoenliche Rekorde (Beherrschung-Tab)."""
    user = User.query.get(user_id)
    longest = (user.longest_streak or 0) if user else 0
    best_day = db.session.query(func.max(DailyReviewAggregate.total_reviews)).filter(
        DailyReviewAggregate.user_id == user_id
    ).scalar() or 0
    total_reviews = db.session.query(func.sum(DailyReviewAggregate.total_reviews)).filter(
        DailyReviewAggregate.user_id == user_id
    ).scalar()
    if not total_reviews:
        total_reviews = (user.total_reviews or 0) if user else 0
    return [
        {'i': '🔥', 'n': 'Längste Serie', 'val': f'{longest} Tage'},
        {'i': '⚡', 'n': 'Bester Tag', 'val': f'{best_day} Reviews'},
        {'i': '🧠', 'n': 'Reviews gesamt', 'val': _swiss(total_reviews)},
    ]


def _heatmap_array(user_id, days=365):
    """365er-Count-Array (alt -> neu, endet heute) + kumulative Kennzahlen."""
    from app import srs_service
    raw = srs_service.get_heatmap_data(user_id, days)
    by_date = {d['date']: d['count'] for d in raw}
    today = datetime.utcnow().date()
    arr = []
    for i in range(days):
        d = (today - timedelta(days=days - 1 - i)).isoformat()
        arr.append(by_date.get(d, 0))
    user = User.query.get(user_id)
    cumulative = {
        'daysTotal': sum(1 for c in by_date.values() if c > 0),
        'bestStreak': (user.longest_streak or 0) if user else 0,
        'reviewsTotal': sum(by_date.values()),
    }
    return arr, cumulative


def weak_kana(user_id, limit=5):
    """Top-N schwaechste Kana (lapses desc, accuracy asc) — wie api_kana_weak."""
    acc_by_content = _accuracy_by_content(user_id)
    rows = (
        db.session.query(CardReviewState, Kana)
        .join(LessonContent, CardReviewState.content_id == LessonContent.id)
        .join(Kana, LessonContent.content_id == Kana.id)
        .filter(
            CardReviewState.user_id == user_id,
            LessonContent.content_type == 'kana',
            CardReviewState.reps > 0,
        )
        .all()
    )
    items = []
    for state, kana in rows:
        acc = acc_by_content.get(state.content_id, 0)
        items.append({
            'c': kana.character, 'on': kana.romanization,
            'acc': round(acc), 'lapses': state.lapses, 'reps': state.reps,
            '_sort': (-state.lapses, acc, -state.reps),
        })
    items.sort(key=lambda x: x['_sort'])
    for it in items:
        del it['_sort']
    return items[:limit]


def leeches_view(user_id, limit=5):
    """Problemkarten in Prototyp-Form {front, type, lapses, rate}."""
    from app import srs_service
    raw = srs_service.get_leeches(user_id, threshold=8, limit=limit)
    return [{
        'front': r['front'],
        'type': _TYPE_LABEL.get(r['content_type'], r['content_type']),
        'lapses': r['lapses'],
        'rate': r['failure_rate'],
    } for r in raw]


def acc_by_skill(user_id):
    """Genauigkeit (Retention) je Skill — Reshape von get_performance_by_type."""
    from app import srs_service
    perf = {p['type']: p for p in srs_service.get_performance_by_type(user_id)}
    out = []
    for t in ('kana', 'vocabulary', 'kanji', 'grammar'):
        if t in perf:
            out.append({'k': _TYPE_LABEL[t], 'v': round(perf[t]['retention'])})
    return out


def jlpt_detail(user_id):
    """N5-Zaehlerzeile fuer den JLPT-Balken (Vokabeln/Kanji/Grammatik)."""
    from app import srs_service
    prog = srs_service.get_jlpt_progress(user_id).get('N5', {})
    by_type = maturity_by_type(user_id)
    totals = pillar_totals()
    g_started = by_type['grammar']['started']
    g_total = totals['grammar']
    return (
        f"Vokabeln {prog.get('vocab_mastered', 0)}/{prog.get('vocab_total', 0)} · "
        f"Kanji {prog.get('kanji_mastered', 0)}/{prog.get('kanji_total', 0)} · "
        f"Grammatik {g_started}/{g_total}"
    )


def _milestones(user_id):
    """Achievements als Meilenstein-Kacheln (entsperrte zuerst, max 8)."""
    from app.achievements import ACHIEVEMENTS
    from app.models import UserAchievement
    unlocked = {a.achievement_key: a for a in UserAchievement.query.filter_by(user_id=user_id).all()}
    out = []
    for key, defn in ACHIEVEMENTS.items():
        u = unlocked.get(key)
        date = ''
        if u and u.unlocked_at:
            date = u.unlocked_at.strftime('%d.%m.%Y')
        out.append({
            'i': defn.get('icon', '🏅'),
            'n': defn.get('name', key),
            'on': bool(u),
            'date': date,
            'rest': '',
        })
    out.sort(key=lambda m: not m['on'])  # entsperrte zuerst
    return out[:8]


# Kuratierte Verwechslungs-Notizen (von Claude verfasst, kein LLM-API).
_CONFUSION_NOTES = {
    frozenset('しシ'): 'Hiragana vs Katakana — Strichrichtung',
    frozenset('ソン'): 'Katakana — Winkel der Striche',
    frozenset('シツ'): 'Katakana — waagrecht vs senkrecht',
    frozenset('ねれ'): 'Hiragana — Schlaufe rechts',
    frozenset('れわ'): 'Hiragana — rechter Teil',
    frozenset('るろ'): 'Hiragana — Schlaufe unten',
    frozenset('まも'): 'Hiragana — Strich-Anzahl',
    frozenset('はほ'): 'Hiragana — Strich oben',
    frozenset('ぬめ'): 'Hiragana — Schlaufe',
    frozenset('クケ'): 'Katakana — dritter Strich',
}


def _kana_acc_by_id(user_id):
    """kana_id -> Accuracy (%) fuer die Verwechslungs-Genauigkeiten."""
    acc_by_content = _accuracy_by_content(user_id)
    rows = (
        db.session.query(Kana.id, LessonContent.id)
        .join(LessonContent, db.and_(
            LessonContent.content_id == Kana.id,
            LessonContent.content_type == 'kana',
        ))
        .join(CardReviewState, db.and_(
            CardReviewState.content_id == LessonContent.id,
            CardReviewState.user_id == user_id,
            CardReviewState.direction == 'forward',
        ))
        .all()
    )
    return {kana_id: round(acc_by_content.get(content_id, 0)) for kana_id, content_id in rows}


def confusion_pairs(user_id, limit=5):
    """Verwechslungs-Paare aus KanaConfusion + kuratierten Notizen."""
    rows = (
        KanaConfusion.query
        .filter_by(user_id=user_id)
        .order_by(KanaConfusion.count.desc())
        .limit(limit * 3)
        .all()
    )
    if not rows:
        return []
    ids = set()
    for r in rows:
        ids.add(r.target_kana_id)
        ids.add(r.confused_kana_id)
    chars = {k.id: k.character for k in Kana.query.filter(Kana.id.in_(ids)).all()}
    acc_by_id = _kana_acc_by_id(user_id)

    out = []
    seen = set()
    pid = 0
    for r in rows:
        a = chars.get(r.target_kana_id)
        b = chars.get(r.confused_kana_id)
        if not a or not b or a == b:
            continue
        key = frozenset((a, b))
        if key in seen:
            continue
        seen.add(key)
        pid += 1
        out.append({
            'id': pid, 'a': a, 'b': b,
            'aAcc': acc_by_id.get(r.target_kana_id, 0),
            'bAcc': acc_by_id.get(r.confused_kana_id, 0),
            'note': _CONFUSION_NOTES.get(key, 'häufig verwechselt — gezielt gegenüberstellen'),
        })
        if len(out) >= limit:
            break
    return out


def kana_mastery_rows(user_id):
    """Kana-Beherrschung als Gojuon-Reihen (Beherrschung-Tab)."""
    from app.services.kana_rows import ROW_KEYS, ROW_LABELS, row_for_kana
    glyphs = compass_glyphs(user_id, 'kana')
    buckets = {}
    for g in glyphs:
        key = row_for_kana(g['c'])
        if not key:
            continue
        buckets.setdefault(key, []).append({'c': g['c'], 'on': g['on'], 'acc': g['acc'], 'reps': g['reps']})
    return [
        {'lab': ROW_LABELS[key], 'cells': buckets[key]}
        for key in ROW_KEYS if key in buckets
    ]


def stats_bundle(user_id):
    """Alle Statistik-Tab-Daten in einem Lazy-Fetch (Form = docs/dashboard_contract.md)."""
    tempo = tempo_stats(user_id)
    heatmap, cumulative = _heatmap_array(user_id)
    return {
        # Tempo
        'kpi': tempo['kpi'],
        'reviewsByWeek': tempo['reviewsByWeek'],
        'accuracyByWeek': tempo['accuracyByWeek'],
        'reviewsByWeekday': tempo['reviewsByWeekday'],
        # Genauigkeit
        'accByStage': acc_by_stage(user_id),
        'retention': retention_by_maturity(user_id),
        'accBySkill': acc_by_skill(user_id),
        # Reife
        'maturity': maturity_by_skill(user_id),
        # Verlauf
        'heatmap': heatmap,
        'cumulative': cumulative,
        # Schwaechen
        'weakKana': weak_kana(user_id),
        'leeches': leeches_view(user_id),
        'confusionPairs': confusion_pairs(user_id),
        # Beherrschung
        'kanaRows': kana_mastery_rows(user_id),
        'jlptDetail': jlpt_detail(user_id),
        'milestones': _milestones(user_id),
        'records': records(user_id),
    }


# ════════════════════════════════════════════════════════════════════
#  Heute-Hero (adaptiver Plan) + Wochenziel + Freezes + Can-do
#  + Kompass-Detailmaps Vokabel-Themen / Grammatik (Server-Context)
# ════════════════════════════════════════════════════════════════════

def week_goal(user_id, target=7):
    """Aktive CH-Tage der laufenden Woche (Mo–heute) / Zielwert."""
    from app.time_utils import ch_today
    today = ch_today()
    monday = today - timedelta(days=today.weekday())
    done = DailyReviewAggregate.query.filter(
        DailyReviewAggregate.user_id == user_id,
        DailyReviewAggregate.review_date >= monday,
        DailyReviewAggregate.review_date <= today,
        DailyReviewAggregate.total_reviews > 0,
    ).count()
    return {'done': min(done, target), 'total': target}


def streak_freezes(user_id):
    """Verfuegbare Streak-Schoner (Anzeige auf 0/1 gecappt — Backend fuehrt max. 1)."""
    from app.models import UserSRSSettings
    s = UserSRSSettings.query.filter_by(user_id=user_id).first()
    n = s.streak_freezes_available if (s and s.streak_freezes_available is not None) else 0
    return max(0, min(1, int(n)))


def next_lesson(user_id):
    """Resume- (zuletzt begonnene, offene) oder naechste offene Lektion im Lehrplan."""
    from app.models import Lesson, UserLessonProgress
    resume = (
        UserLessonProgress.query
        .join(Lesson, UserLessonProgress.lesson_id == Lesson.id)
        .filter(
            UserLessonProgress.user_id == user_id,
            UserLessonProgress.is_completed.is_(False),
            Lesson.is_published.is_(True),
        )
        .order_by(UserLessonProgress.last_accessed.desc())
        .first()
    )
    if resume and resume.lesson:
        return {'title': resume.lesson.title, 'lesson_id': resume.lesson_id, 'kind': 'resume'}

    started_ids = [p.lesson_id for p in UserLessonProgress.query.filter_by(user_id=user_id).all()]
    q = Lesson.query.filter(Lesson.is_published.is_(True))
    if started_ids:
        q = q.filter(~Lesson.id.in_(started_ids))
    nxt = q.order_by(Lesson.order_index.asc(), Lesson.id.asc()).first()
    if nxt:
        return {'title': nxt.title, 'lesson_id': nxt.id, 'kind': 'next'}
    return None


def build_plan(user_id, due_count):
    """Adaptiver ~Tagesplan: faellige Reviews + Resume/Next-Lektion + Schwaechen-Drill.

    Returns (plan_steps, plan_minutes). Jeder Schritt: {title(HTML), desc, why,
    dur, kind, href, done}.
    """
    from flask import url_for
    steps = []
    minutes = 0

    if due_count > 0:
        m = max(1, round(due_count * 0.5))
        minutes += m
        steps.append({
            'title': f'<b>{due_count} Karten</b> wiederholen',
            'desc': 'Fällig laut Algorithmus',
            'why': 'Genau jetzt fällig — Wiederholen am Reife-Punkt festigt am stärksten.',
            'dur': f'~{m} Min', 'kind': 'review', 'href': url_for('srs.review_page'), 'done': False,
        })

    nl = next_lesson(user_id)
    if nl:
        minutes += 4
        verb = 'weiterlernen' if nl['kind'] == 'resume' else 'starten'
        desc = 'Da wo du aufgehört hast' if nl['kind'] == 'resume' else 'Nächste im Lehrplan'
        steps.append({
            'title': f'„{nl["title"]}" {verb}',
            'desc': desc,
            'why': 'Bringt neue Wörter und hält dein Wochenziel.',
            'dur': '~4 Min', 'kind': 'lesson',
            'href': url_for('routes.view_lesson', lesson_id=nl['lesson_id']), 'done': False,
        })

    weak = weak_kana(user_id, limit=2)
    if weak:
        chars = ' · '.join(w['c'] for w in weak)
        minutes += 2
        steps.append({
            'title': f'Verwechslungs-Drill <span class="jp">{chars}</span>',
            'desc': 'Aus deinen Schwächen',
            'why': 'Deine wackeligsten Zeichen — gezielt gegenüberstellen löst sie.',
            'dur': '~2 Min', 'kind': 'drill', 'href': url_for('srs.practice_kana_page'), 'done': False,
        })

    if not steps:
        minutes = 5
        steps.append({
            'title': 'Eine neue Lektion entdecken',
            'desc': 'Keine fälligen Karten — guter Moment für Neues',
            'why': 'Dranbleiben schlägt Aufholen.',
            'dur': '~5 Min', 'kind': 'lesson', 'href': url_for('routes.lessons'), 'done': False,
        })

    return steps, minutes


# Kuratierte N5-Can-do-Statements (von Claude verfasst, kein LLM-API).
# threshold = Anzahl abgeschlossener Lektionen, ab der das Statement „erreicht" ist.
_CAN_DO = [
    (1, 'Hiragana lesen und schreiben'),
    (1, 'Mich vorstellen — Name, Land, Beruf'),
    (2, 'Jemanden begrüssen und mich verabschieden'),
    (2, 'Zahlen verstehen und sagen'),
    (3, 'Eine kurze Notiz auf Hiragana lesen'),
    (4, 'Im Café etwas von der Karte bestellen'),
    (5, 'Nach dem Preis fragen und ihn verstehen'),
    (6, 'Uhrzeit und Datum sagen'),
    (8, 'Sagen, was ich mag und nicht mag'),
    (10, 'Über meine Familie sprechen'),
    (12, 'Bahnhofsschilder & eine Speisekarte lesen'),
    (14, 'Einen einfachen Tagesablauf beschreiben'),
]


def can_do(user_id):
    """Kuratierte Kann-Liste; Status (done/prog/open) aus abgeschlossenen Lektionen."""
    from app.models import UserLessonProgress
    completed = UserLessonProgress.query.filter_by(user_id=user_id, is_completed=True).count()
    out = []
    for threshold, text in _CAN_DO:
        if completed >= threshold:
            status = 'done'
        elif completed >= threshold - 1:
            status = 'prog'
        else:
            status = 'open'
        out.append({'t': text, 's': status})
    return out


def grammar_list(user_id, limit=12):
    """Grammatik-Muster mit Reife-Level (0–3) aus den Karten des Users."""
    from app.models import Grammar
    rows = (
        db.session.query(CardReviewState, Grammar)
        .join(LessonContent, CardReviewState.content_id == LessonContent.id)
        .join(Grammar, LessonContent.content_id == Grammar.id)
        .filter(
            CardReviewState.user_id == user_id,
            LessonContent.content_type == 'grammar',
        )
        .all()
    )
    out = []
    for state, g in rows:
        stage = get_card_stage(state.fsrs_card_state)[0]
        level = 0 if stage <= 0 else 1 if stage <= 3 else 2 if stage <= 6 else 3
        out.append({
            'pat': g.title,
            'ex': (g.structure or g.explanation or '')[:50],
            'level': level,
        })
    out.sort(key=lambda x: -x['level'])
    return out[:limit]


def vocab_themes(user_id):
    """Vokabeln nach Thema (= LessonCategory), have/total fuer den User."""
    from app.models import Lesson, LessonCategory
    rows = (
        db.session.query(LessonCategory.name, LessonContent.id)
        .join(Lesson, Lesson.category_id == LessonCategory.id)
        .join(LessonContent, db.and_(
            LessonContent.lesson_id == Lesson.id,
            LessonContent.content_type == 'vocabulary',
        ))
        .filter(Lesson.is_published.is_(True))
        .all()
    )
    started = {
        cid for (cid,) in (
            db.session.query(CardReviewState.content_id)
            .join(LessonContent, CardReviewState.content_id == LessonContent.id)
            .filter(
                CardReviewState.user_id == user_id,
                CardReviewState.direction == 'forward',
                LessonContent.content_type == 'vocabulary',
            ).all()
        )
    }
    themes = {}
    seen = set()
    for name, content_id in rows:
        if (name, content_id) in seen:
            continue
        seen.add((name, content_id))
        t = themes.setdefault(name, {'have': 0, 'total': 0})
        t['total'] += 1
        if content_id in started:
            t['have'] += 1
    result = [
        {'name': name, 'jp': '', 'have': v['have'], 'total': v['total']}
        for name, v in themes.items() if v['total'] > 0
    ]
    result.sort(key=lambda x: -x['total'])
    return result[:8]
