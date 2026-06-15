# app/dashboard_service.py
"""Datenaggregation fuer das Lernenden-Dashboard „Mein Lernen".

Eigenes Modul (nicht srs_service), damit Dashboard-Tracks parallel arbeiten
koennen. Liefert die Formen aus docs/dashboard_contract.md. Reife-Einteilung
kommt aus der Single Source gamification_service.maturity_bucket().
"""
import logging

from sqlalchemy import case, func

from app import db
from app.gamification_service import get_card_stage, maturity_bucket
from app.models import CardReviewState, Kana, Kanji, LessonContent, ReviewLog

logger = logging.getLogger(__name__)

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
