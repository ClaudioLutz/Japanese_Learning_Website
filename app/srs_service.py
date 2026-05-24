# app/srs_service.py
"""Service-Klasse fuer alle SRS-Operationen (FSRS-Algorithmus)."""
import json
import logging
from datetime import datetime, timezone

from fsrs import Card, Rating, Scheduler, State

from app import db
from app.models import (
    CardReviewState, DailyReviewAggregate, Kana, Kanji, Grammar,
    LessonContent, ReviewLog, User, UserSRSSettings, Vocabulary,
)
from app.gamification_service import (
    calculate_xp,
    get_card_stage,
    maybe_grant_random_xp_boost,
    update_daily_aggregate,
)

logger = logging.getLogger(__name__)

# Rating-Mapping: Integer → FSRS Rating
RATING_MAP = {
    1: Rating.Again,
    2: Rating.Hard,
    3: Rating.Good,
    4: Rating.Easy,
}

# State-Mapping: FSRS State → DB-String
STATE_MAP = {
    State.Learning: 'learning',
    State.Review: 'review',
    State.Relearning: 'relearning',
}

# Rating-Labels fuer Frontend
RATING_LABELS = {
    1: 'Again',
    2: 'Hard',
    3: 'Good',
    4: 'Easy',
}


def _get_scheduler(user_id):
    """Erstellt einen FSRS-Scheduler mit User-spezifischen Parametern."""
    settings = UserSRSSettings.query.filter_by(user_id=user_id).first()

    kwargs = {
        'desired_retention': settings.desired_retention if settings else 0.9,
        'enable_fuzzing': True,
    }

    if settings and settings.fsrs_parameters:
        kwargs['parameters'] = tuple(json.loads(settings.fsrs_parameters))

    return Scheduler(**kwargs)


def _card_from_state(state):
    """Laedt eine FSRS Card aus einem CardReviewState, mit Fallback."""
    try:
        return Card.from_json(state.fsrs_card_state)
    except Exception:
        logger.warning(f'Korrupter FSRS-State fuer CardReviewState {state.id}, erstelle neue Card')
        return Card()


def rate_card(user_id, content_id, rating_int, time_taken_ms=None):
    """
    Bewertet eine Karte und berechnet den neuen FSRS-State.

    Args:
        user_id: User-ID
        content_id: LessonContent-ID
        rating_int: 1=Again, 2=Hard, 3=Good, 4=Easy
        time_taken_ms: Antwortzeit in Millisekunden

    Returns:
        dict mit next_interval, due_date, status, reps, lapses
    """
    scheduler = _get_scheduler(user_id)
    rating = RATING_MAP[rating_int]

    state = CardReviewState.query.filter_by(
        user_id=user_id, content_id=content_id
    ).first()

    if state:
        card = _card_from_state(state)
        is_new = (state.reps == 0)
    else:
        card = Card()
        is_new = True
        state = CardReviewState(
            user_id=user_id,
            content_id=content_id,
            fsrs_card_state=card.to_json(),
            due_date=datetime.utcnow(),
            status='new',
            reps=0,
            lapses=0,
        )
        db.session.add(state)

    # Karten-Stufe VOR dem Review
    old_stage_idx, old_stage_name, _ = get_card_stage(state.fsrs_card_state)

    # FSRS-Berechnung
    now_utc = datetime.now(timezone.utc)
    new_card, fsrs_log = scheduler.review_card(card, rating)

    # Intervalle berechnen (fsrs v6 hat kein scheduled_days auf ReviewLog)
    scheduled_days = max(0, (new_card.due - now_utc).days)
    elapsed_days = 0
    if card.last_review:
        elapsed_days = max(0, (now_utc - card.last_review).days)

    # State aktualisieren
    state.fsrs_card_state = new_card.to_json()
    # due aus FSRS ist timezone-aware (UTC), wir speichern naive UTC
    due = new_card.due
    if due.tzinfo is not None:
        due = due.replace(tzinfo=None)
    state.due_date = due
    state.status = STATE_MAP.get(new_card.state, 'review')
    state.reps += 1
    if rating_int == 1:
        state.lapses += 1
    state.updated_at = datetime.utcnow()

    # Karten-Stufe NACH dem Review
    new_stage_idx, new_stage_name, new_stage_color = get_card_stage(state.fsrs_card_state)
    stage_changed = (new_stage_idx != old_stage_idx)
    leveled_up = (new_stage_idx > old_stage_idx)
    leveled_down = (new_stage_idx < old_stage_idx)

    # ── Gamification: XP + User-Stats ──
    xp = calculate_xp(rating_int, is_new)
    user = User.query.get(user_id)
    # Null-Safety fuer SQLite (kein server_default in Tests)
    if user.level is None:
        user.level = 1
    if user.total_reviews is None:
        user.total_reviews = 0
    if user.total_mastered is None:
        user.total_mastered = 0

    old_level = user.level

    # Variable Reward (Phase 2, Duolingo-Pattern): 8% Chance auf +5..+25 Bonus.
    boost = maybe_grant_random_xp_boost()
    if boost:
        xp += boost

    user.add_xp(xp)
    user.total_reviews += 1

    # Karte neu gemeistert?
    if new_stage_idx == 9 and old_stage_idx != 9:
        user.total_mastered = (user.total_mastered or 0) + 1
    elif old_stage_idx == 9 and new_stage_idx != 9:
        user.total_mastered = max(0, (user.total_mastered or 0) - 1)

    # DailyReviewAggregate aktualisieren
    update_daily_aggregate(
        user_id=user_id,
        rating_int=rating_int,
        time_taken_ms=time_taken_ms,
        xp_earned=xp,
        is_new=is_new,
        leveled_up=leveled_up,
        leveled_down=leveled_down,
    )

    # ReviewLog erstellen
    log_entry = ReviewLog(
        user_id=user_id,
        content_id=content_id,
        rating=rating_int,
        reviewed_at=datetime.utcnow(),
        time_taken_ms=time_taken_ms,
        fsrs_review_log=fsrs_log.to_json(),
        scheduled_days=scheduled_days,
        elapsed_days=elapsed_days,
    )
    db.session.add(log_entry)
    db.session.commit()

    return {
        'next_interval': scheduled_days,
        'due_date': state.due_date.isoformat(),
        'status': state.status,
        'reps': state.reps,
        'lapses': state.lapses,
        # Gamification
        'xp_earned': xp,
        'xp_boost': boost,             # 0 wenn kein Boost, sonst Bonus-Anteil (5..25)
        'total_xp': user.total_xp,
        'level': user.level,
        'leveled_up': (user.level or 1) > old_level,
        'card_stage': new_stage_idx,
        'stage_name': new_stage_name,
        'stage_color': new_stage_color,
        'stage_changed': stage_changed,
    }


def get_due_cards(user_id, limit=50, lesson_id=None, content_type=None):
    """Holt alle faelligen Karten fuer einen User."""
    now = datetime.utcnow()

    query = CardReviewState.query.filter(
        CardReviewState.user_id == user_id,
        CardReviewState.due_date <= now,
        CardReviewState.status != 'suspended',
    )

    if lesson_id or content_type:
        query = query.join(LessonContent)
        if lesson_id:
            query = query.filter(LessonContent.lesson_id == lesson_id)
        if content_type:
            query = query.filter(LessonContent.content_type == content_type)

    return query.order_by(CardReviewState.due_date.asc()).limit(limit).all()


def get_due_count(user_id):
    """Zaehlt faellige Karten fuer einen User (fuer Badge)."""
    now = datetime.utcnow()
    return CardReviewState.query.filter(
        CardReviewState.user_id == user_id,
        CardReviewState.due_date <= now,
        CardReviewState.status != 'suspended',
    ).count()


def get_new_cards(user_id, lesson_id, limit=20):
    """Holt Content-Items einer Lektion, die der User noch nie bewertet hat."""
    card_types = ['kana', 'kanji', 'vocabulary', 'grammar']

    existing = db.session.query(CardReviewState.content_id).filter(
        CardReviewState.user_id == user_id
    ).subquery()

    return LessonContent.query.filter(
        LessonContent.lesson_id == lesson_id,
        LessonContent.content_type.in_(card_types),
        ~LessonContent.id.in_(existing),
    ).order_by(LessonContent.page_number, LessonContent.order_index).limit(limit).all()


def get_interval_preview(user_id, content_id):
    """
    Zeigt die voraussichtlichen Intervalle fuer alle 4 Ratings.
    Returns: dict {1: "<1 Min", 2: "<10 Min", 3: "4 Tage", 4: "12 Tage"}
    """
    scheduler = _get_scheduler(user_id)

    state = CardReviewState.query.filter_by(
        user_id=user_id, content_id=content_id
    ).first()

    if state:
        card = _card_from_state(state)
    else:
        card = Card()

    now_utc = datetime.now(timezone.utc)
    previews = {}
    for rating_int, rating_enum in RATING_MAP.items():
        preview_card, preview_log = scheduler.review_card(card, rating_enum)

        # Intervall berechnen
        delta = preview_card.due - now_utc
        days = max(0, delta.days)
        total_minutes = max(1, int(delta.total_seconds() / 60))

        if days == 0:
            # Learning-Phase: Minuten/Stunden anzeigen
            if total_minutes < 60:
                label = f"<{total_minutes} Min"
            else:
                label = f"{total_minutes // 60} Std"
        elif days == 1:
            label = "1 Tag"
        else:
            label = f"{days} Tage"

        previews[rating_int] = label

    return previews


def get_user_stats(user_id):
    """Basis-Statistiken fuer einen User."""
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    total_cards = CardReviewState.query.filter_by(user_id=user_id).count()

    due_count = CardReviewState.query.filter(
        CardReviewState.user_id == user_id,
        CardReviewState.due_date <= now,
        CardReviewState.status != 'suspended',
    ).count()

    reviews_today = ReviewLog.query.filter(
        ReviewLog.user_id == user_id,
        ReviewLog.reviewed_at >= today_start,
    ).count()

    # Karten nach Status zaehlen
    status_counts = dict(
        db.session.query(CardReviewState.status, db.func.count(CardReviewState.id))
        .filter(CardReviewState.user_id == user_id)
        .group_by(CardReviewState.status)
        .all()
    )

    # Erfolgsrate heute (Rating >= 3)
    if reviews_today > 0:
        good_reviews = ReviewLog.query.filter(
            ReviewLog.user_id == user_id,
            ReviewLog.reviewed_at >= today_start,
            ReviewLog.rating >= 3,
        ).count()
        success_rate = round(good_reviews / reviews_today * 100)
    else:
        success_rate = 0

    return {
        'total_cards': total_cards,
        'due_count': due_count,
        'reviews_today': reviews_today,
        'success_rate': success_rate,
        'new_count': status_counts.get('new', 0),
        'learning_count': status_counts.get('learning', 0) + status_counts.get('relearning', 0),
        'review_count': status_counts.get('review', 0),
    }


def get_content_data_for_review(content_item):
    """Bereitet Content-Daten fuer die Review-API auf."""
    data = {
        'content_id': content_item.id,
        'content_type': content_item.content_type,
        'lesson_id': content_item.lesson_id,
        'lesson_title': content_item.lesson.title if content_item.lesson else '',
        'instruction_language': content_item.lesson.instruction_language if content_item.lesson else 'english',
    }

    ref = content_item.get_content_data()
    if ref is None:
        return data

    if content_item.content_type == 'kana':
        data['front'] = ref.character
        data['details'] = {
            'romanization': ref.romanization,
            'type': ref.type,
        }
    elif content_item.content_type == 'kanji':
        data['front'] = ref.character
        data['details'] = {
            'meaning': ref.meaning,
            'onyomi': ref.onyomi or '',
            'kunyomi': ref.kunyomi or '',
            'stroke_count': ref.stroke_count,
        }
    elif content_item.content_type == 'vocabulary':
        data['front'] = ref.word
        data['details'] = {
            'reading': ref.reading,
            'romaji': ref.romaji or '',
            'meaning': ref.meaning,
            'meaning_de': ref.meaning_de or '',
            'example_jp': ref.example_sentence_japanese or '',
            'example_en': ref.example_sentence_english or '',
            # Aufgesplittet aus example_sentence_english ("Romaji — Uebersetzung"):
            # Audio-Button liest example_jp, Karte zeigt Romaji + Uebersetzung
            # darunter, damit der Lerner den Satz westlich mitlesen kann.
            'example_romaji': ref.example_sentence_romaji or '',
            'example_translation': ref.example_sentence_translation or '',
            'image_url': ref.image_url or '',
        }
    elif content_item.content_type == 'grammar':
        data['front'] = ref.title
        data['details'] = {
            'explanation': ref.explanation,
            'structure': ref.structure or '',
            'romaji': ref.romaji or '',
            'examples': ref.example_sentences or '',
            # Sauberer JP-Beispielsatz fuer den Audio-Button auf der Karte —
            # /api/tts mit lang=ja akzeptiert nur reines Japanisch, sonst HTTP 400.
            'tts_example_jp': ref.tts_example_jp or '',
            # Geparst aus example_sentences-Block (Klammer-Romaji oder JSON).
            'tts_example_romaji': ref.tts_example_romaji or '',
            'tts_example_translation': ref.tts_example_translation or '',
            # Alle Beispielsätze normalisiert ({japanese, romaji, translation})
            # für die Mehrfach-Anzeige auf der Karten-Rückseite.
            'examples_list': ref.parsed_examples(),
        }

    return data


def migrate_existing_progress(user_id=None):
    """
    Migriert bestehenden content_progress zu CardReviewState.
    Wenn user_id=None, werden alle User migriert.
    """
    from app.models import UserLessonProgress

    query = UserLessonProgress.query.filter(
        UserLessonProgress.content_progress.isnot(None)
    )
    if user_id:
        query = query.filter_by(user_id=user_id)

    progress_records = query.all()
    migrated = 0

    for progress in progress_records:
        content_progress = progress.get_content_progress()
        scheduler = Scheduler(desired_retention=0.9)

        for content_id_str, completed in content_progress.items():
            if not completed:
                continue

            content_id = int(content_id_str)

            # Pruefen ob Content-Item existiert
            content = LessonContent.query.get(content_id)
            if not content or content.content_type not in ['kana', 'kanji', 'vocabulary', 'grammar']:
                continue

            existing = CardReviewState.query.filter_by(
                user_id=progress.user_id, content_id=content_id
            ).first()
            if existing:
                continue

            # Neue Karte: Einen Good-Review simulieren
            card = Card()
            card, _ = scheduler.review_card(card, Rating.Good)

            due = card.due
            if due.tzinfo is not None:
                due = due.replace(tzinfo=None)

            state = CardReviewState(
                user_id=progress.user_id,
                content_id=content_id,
                fsrs_card_state=card.to_json(),
                due_date=due,
                status=STATE_MAP.get(card.state, 'review'),
                reps=1,
                lapses=0,
            )
            db.session.add(state)
            migrated += 1

    db.session.commit()
    logger.info(f'Migriert: {migrated} Karten-States')
    return migrated


# ── Phase 6: Erweiterte Statistiken ──────────────────────────


def get_heatmap_data(user_id, days=365):
    """Review-Aktivitaet pro Tag fuer die Heatmap (letzte N Tage)."""
    from datetime import timedelta
    start = datetime.utcnow().date() - timedelta(days=days)

    # Zuerst DailyReviewAggregate versuchen
    rows = db.session.query(
        DailyReviewAggregate.review_date,
        DailyReviewAggregate.total_reviews,
    ).filter(
        DailyReviewAggregate.user_id == user_id,
        DailyReviewAggregate.review_date >= start,
    ).all()

    if rows:
        return [{'date': r.review_date.isoformat(), 'count': r.total_reviews} for r in rows]

    # Fallback: ReviewLog direkt abfragen (fuer Pre-Phase-6-Daten)
    rows = db.session.query(
        db.func.date(ReviewLog.reviewed_at).label('review_date'),
        db.func.count(ReviewLog.id).label('cnt'),
    ).filter(
        ReviewLog.user_id == user_id,
        ReviewLog.reviewed_at >= datetime.combine(start, datetime.min.time()),
    ).group_by(db.func.date(ReviewLog.reviewed_at)).all()

    return [{'date': str(r.review_date), 'count': r.cnt} for r in rows]


def get_retention_by_interval(user_id):
    """Retention-Rate gruppiert nach Intervall-Bereichen."""
    rows = db.session.query(
        ReviewLog.elapsed_days,
        ReviewLog.rating,
    ).filter(
        ReviewLog.user_id == user_id,
        ReviewLog.elapsed_days.isnot(None),
    ).all()

    buckets = {
        '0-1d': {'total': 0, 'correct': 0},
        '2-7d': {'total': 0, 'correct': 0},
        '8-30d': {'total': 0, 'correct': 0},
        '31-90d': {'total': 0, 'correct': 0},
        '90+d': {'total': 0, 'correct': 0},
    }

    for r in rows:
        d = r.elapsed_days or 0
        if d <= 1:
            b = '0-1d'
        elif d <= 7:
            b = '2-7d'
        elif d <= 30:
            b = '8-30d'
        elif d <= 90:
            b = '31-90d'
        else:
            b = '90+d'
        buckets[b]['total'] += 1
        if r.rating >= 3:
            buckets[b]['correct'] += 1

    result = []
    for interval, data in buckets.items():
        retention = round(data['correct'] / data['total'] * 100, 1) if data['total'] > 0 else 0
        result.append({
            'interval': interval,
            'retention': retention,
            'total': data['total'],
        })
    return result


def get_review_forecast(user_id, days=30):
    """Projiziert faellige Reviews fuer die naechsten N Tage."""
    from datetime import timedelta
    today = datetime.utcnow().date()
    forecast = []

    for offset in range(days):
        target = today + timedelta(days=offset)
        start = datetime.combine(target, datetime.min.time())
        end = datetime.combine(target, datetime.max.time())

        count = CardReviewState.query.filter(
            CardReviewState.user_id == user_id,
            CardReviewState.due_date >= start,
            CardReviewState.due_date <= end,
            CardReviewState.status != 'suspended',
        ).count()

        forecast.append({'date': target.isoformat(), 'count': count})

    return forecast


def get_maturity_distribution(user_id):
    """Zaehlt Karten nach SRS-Stufe (Donut-Chart)."""
    states = CardReviewState.query.filter_by(user_id=user_id).all()

    distribution = {
        'Neu': 0, 'Lernen': 0, 'Jung': 0,
        'Reif': 0, 'Gemeistert': 0, 'Suspendiert': 0,
    }

    for s in states:
        if s.status == 'suspended':
            distribution['Suspendiert'] += 1
            continue
        if s.status in ('learning', 'relearning'):
            distribution['Lernen'] += 1
            continue

        stage_idx, _, _ = get_card_stage(s.fsrs_card_state)
        if stage_idx <= 0:
            distribution['Neu'] += 1
        elif stage_idx <= 4:
            distribution['Jung'] += 1
        elif stage_idx <= 6:
            distribution['Reif'] += 1
        else:
            distribution['Gemeistert'] += 1

    return distribution


def get_performance_by_type(user_id):
    """Retention + Antwortzeit pro Content-Typ."""
    rows = db.session.query(
        LessonContent.content_type,
        db.func.count(ReviewLog.id).label('total'),
        db.func.sum(db.case((ReviewLog.rating >= 3, 1), else_=0)).label('correct'),
        db.func.avg(ReviewLog.time_taken_ms).label('avg_time'),
        db.func.sum(db.case((ReviewLog.rating == 1, 1), else_=0)).label('lapses'),
    ).join(
        LessonContent, ReviewLog.content_id == LessonContent.id
    ).filter(
        ReviewLog.user_id == user_id,
    ).group_by(LessonContent.content_type).all()

    return [{
        'type': r.content_type,
        'total': r.total,
        'retention': round(r.correct / r.total * 100, 1) if r.total > 0 else 0,
        'avg_time_ms': round(r.avg_time) if r.avg_time else 0,
        'lapses': r.lapses,
    } for r in rows]


def get_leeches(user_id, threshold=8, limit=50):
    """Karten mit hohen Lapses (Leeches)."""
    states = CardReviewState.query.filter(
        CardReviewState.user_id == user_id,
        CardReviewState.lapses >= threshold,
        CardReviewState.status != 'suspended',
    ).order_by(CardReviewState.lapses.desc()).limit(limit).all()

    result = []
    for s in states:
        content = s.content
        if not content:
            continue
        card_data = get_content_data_for_review(content)
        failure_rate = round(s.lapses / max(s.reps, 1) * 100, 1)
        result.append({
            'content_id': s.content_id,
            'front': card_data.get('front', '?'),
            'content_type': content.content_type,
            'lapses': s.lapses,
            'reps': s.reps,
            'failure_rate': failure_rate,
            'status': s.status,
        })
    return result


def get_response_time_histogram(user_id):
    """Histogramm der Antwortzeiten nach Rating."""
    rows = db.session.query(
        ReviewLog.rating,
        ReviewLog.time_taken_ms,
    ).filter(
        ReviewLog.user_id == user_id,
        ReviewLog.time_taken_ms.isnot(None),
        ReviewLog.time_taken_ms > 0,
    ).all()

    buckets = [
        {'range': '0-2s', 'max_ms': 2000},
        {'range': '2-5s', 'max_ms': 5000},
        {'range': '5-10s', 'max_ms': 10000},
        {'range': '10-20s', 'max_ms': 20000},
        {'range': '20s+', 'max_ms': float('inf')},
    ]

    result = []
    for b in buckets:
        entry = {'range': b['range'], 'again': 0, 'hard': 0, 'good': 0, 'easy': 0}
        result.append(entry)

    for r in rows:
        ms = r.time_taken_ms
        rating_key = {1: 'again', 2: 'hard', 3: 'good', 4: 'easy'}.get(r.rating)
        if not rating_key:
            continue
        for i, b in enumerate(buckets):
            if ms <= b['max_ms']:
                result[i][rating_key] += 1
                break

    return result


def get_jlpt_progress(user_id):
    """JLPT N5-N1 Fortschritt basierend auf gemeisterten Karten (Stufe >= 5)."""
    # Alle Karten des Users mit Stufe >= Vertraut 1 (Stufe 5)
    states = CardReviewState.query.filter(
        CardReviewState.user_id == user_id,
        CardReviewState.status != 'suspended',
    ).all()

    mastered_content_ids = set()
    for s in states:
        stage_idx, _, _ = get_card_stage(s.fsrs_card_state)
        if stage_idx >= 5:  # Vertraut 1 oder hoeher
            mastered_content_ids.add(s.content_id)

    # Inhalte nach JLPT-Level zaehlen
    progress = {}
    for level in [5, 4, 3, 2, 1]:
        # Vocabulary
        vocab_total = Vocabulary.query.filter_by(jlpt_level=level).count()
        # Kanji
        kanji_total = Kanji.query.filter_by(jlpt_level=level).count()

        # Gemeisterte Vocab/Kanji per Content-Items
        vocab_mastered = 0
        kanji_mastered = 0

        if mastered_content_ids:
            vocab_mastered = LessonContent.query.join(
                Vocabulary, db.and_(
                    LessonContent.content_id == Vocabulary.id,
                    LessonContent.content_type == 'vocabulary',
                )
            ).filter(
                LessonContent.id.in_(mastered_content_ids),
                Vocabulary.jlpt_level == level,
            ).count()

            kanji_mastered = LessonContent.query.join(
                Kanji, db.and_(
                    LessonContent.content_id == Kanji.id,
                    LessonContent.content_type == 'kanji',
                )
            ).filter(
                LessonContent.id.in_(mastered_content_ids),
                Kanji.jlpt_level == level,
            ).count()

        total = vocab_total + kanji_total
        mastered = vocab_mastered + kanji_mastered
        pct = round(mastered / total * 100) if total > 0 else 0

        progress[f'N{level}'] = {
            'vocab_total': vocab_total,
            'vocab_mastered': vocab_mastered,
            'kanji_total': kanji_total,
            'kanji_mastered': kanji_mastered,
            'total': total,
            'mastered': mastered,
            'percent': pct,
        }

    return progress


# ── Phase 6: Karten-Browser ──────────────────────────────────


def browse_cards(user_id, filters):
    """Paginierter, filterbarer Karten-Browser.

    Args:
        user_id: User-ID
        filters: dict mit: status, content_type, lesson_id, jlpt_level,
                 leech, due_today, search, sort, sort_dir, page, per_page

    Returns:
        dict: {cards: [...], total: int, page: int, pages: int}
    """
    query = db.session.query(CardReviewState, LessonContent).join(
        LessonContent, CardReviewState.content_id == LessonContent.id
    ).filter(CardReviewState.user_id == user_id)

    # ── Filter ──
    status_filter = filters.get('status')
    if status_filter:
        statuses = [s.strip() for s in status_filter.split(',')]
        # Spezielle Maturity-Filter mappen
        status_values = []
        maturity_filters = []
        for s in statuses:
            if s in ('new', 'learning', 'review', 'relearning', 'suspended'):
                status_values.append(s)
            elif s in ('young', 'mature', 'mastered'):
                maturity_filters.append(s)
        if status_values:
            query = query.filter(CardReviewState.status.in_(status_values))

    content_type = filters.get('content_type')
    if content_type:
        types = [t.strip() for t in content_type.split(',')]
        query = query.filter(LessonContent.content_type.in_(types))

    lesson_id = filters.get('lesson_id')
    if lesson_id:
        query = query.filter(LessonContent.lesson_id == int(lesson_id))

    if filters.get('leech'):
        settings = UserSRSSettings.query.filter_by(user_id=user_id).first()
        threshold = settings.leech_threshold if settings else 8
        query = query.filter(CardReviewState.lapses >= threshold)

    if filters.get('due_today'):
        now = datetime.utcnow()
        query = query.filter(
            CardReviewState.due_date <= now,
            CardReviewState.status != 'suspended',
        )

    # ── Suche ──
    search = filters.get('search', '').strip()
    if search:
        search_term = f'%{search}%'
        # Suche ueber Referenztabellen via Subquery
        vocab_ids = db.session.query(LessonContent.id).join(
            Vocabulary, db.and_(
                LessonContent.content_id == Vocabulary.id,
                LessonContent.content_type == 'vocabulary',
            )
        ).filter(db.or_(
            Vocabulary.word.ilike(search_term),
            Vocabulary.reading.ilike(search_term),
            Vocabulary.meaning.ilike(search_term),
            Vocabulary.meaning_de.ilike(search_term),
        )).subquery()

        kanji_ids = db.session.query(LessonContent.id).join(
            Kanji, db.and_(
                LessonContent.content_id == Kanji.id,
                LessonContent.content_type == 'kanji',
            )
        ).filter(db.or_(
            Kanji.character.ilike(search_term),
            Kanji.meaning.ilike(search_term),
        )).subquery()

        kana_ids = db.session.query(LessonContent.id).join(
            Kana, db.and_(
                LessonContent.content_id == Kana.id,
                LessonContent.content_type == 'kana',
            )
        ).filter(db.or_(
            Kana.character.ilike(search_term),
            Kana.romanization.ilike(search_term),
        )).subquery()

        grammar_ids = db.session.query(LessonContent.id).join(
            Grammar, db.and_(
                LessonContent.content_id == Grammar.id,
                LessonContent.content_type == 'grammar',
            )
        ).filter(db.or_(
            Grammar.title.ilike(search_term),
            Grammar.explanation.ilike(search_term),
        )).subquery()

        query = query.filter(db.or_(
            LessonContent.id.in_(vocab_ids),
            LessonContent.id.in_(kanji_ids),
            LessonContent.id.in_(kana_ids),
            LessonContent.id.in_(grammar_ids),
        ))

    # ── Sortierung ──
    sort_field = filters.get('sort', 'due_date')
    sort_dir = filters.get('sort_dir', 'asc')

    sort_map = {
        'due_date': CardReviewState.due_date,
        'lapses': CardReviewState.lapses,
        'reps': CardReviewState.reps,
        'created_at': CardReviewState.created_at,
    }
    sort_col = sort_map.get(sort_field, CardReviewState.due_date)
    if sort_dir == 'desc':
        sort_col = sort_col.desc()

    query = query.order_by(sort_col)

    # ── Pagination ──
    page = max(1, filters.get('page', 1))
    per_page = min(100, max(1, filters.get('per_page', 50)))
    total = query.count()
    total_pages = max(1, (total + per_page - 1) // per_page)

    results = query.offset((page - 1) * per_page).limit(per_page).all()

    # ── Ergebnis aufbereiten ──
    cards = []
    for state, content in results:
        stage_idx, stage_name, stage_color = get_card_stage(state.fsrs_card_state)
        card_data = get_content_data_for_review(content)

        cards.append({
            'state_id': state.id,
            'content_id': state.content_id,
            'content_type': content.content_type,
            'front': card_data.get('front', '?'),
            'details': card_data.get('details', {}),
            'lesson_id': content.lesson_id,
            'lesson_title': content.lesson.title if content.lesson else '',
            'srs_stage': stage_idx,
            'stage_name': stage_name,
            'stage_color': stage_color,
            'status': state.status,
            'due_date': state.due_date.isoformat() if state.due_date else None,
            'reps': state.reps,
            'lapses': state.lapses,
            'is_leech': state.lapses >= 8,
        })

    return {
        'cards': cards,
        'total': total,
        'page': page,
        'pages': total_pages,
    }


def get_card_detail(user_id, content_id):
    """Detaillierte Karten-Info inkl. Review-History."""
    state = CardReviewState.query.filter_by(
        user_id=user_id, content_id=content_id
    ).first()

    if not state:
        return None

    content = state.content
    if not content:
        return None

    card_data = get_content_data_for_review(content)
    stage_idx, stage_name, stage_color = get_card_stage(state.fsrs_card_state)

    # FSRS-Details aus Card State
    import json as _json
    try:
        fsrs_state = _json.loads(state.fsrs_card_state) if isinstance(state.fsrs_card_state, str) else state.fsrs_card_state
        stability = round(fsrs_state.get('stability', 0), 1)
        difficulty = round(fsrs_state.get('difficulty', 0), 1)
    except Exception:
        stability = 0
        difficulty = 0

    # Review-History (letzte 20)
    history = ReviewLog.query.filter_by(
        user_id=user_id, content_id=content_id,
    ).order_by(ReviewLog.reviewed_at.desc()).limit(20).all()

    review_history = [{
        'date': h.reviewed_at.isoformat(),
        'rating': h.rating,
        'rating_label': RATING_LABELS.get(h.rating, '?'),
        'time_taken_ms': h.time_taken_ms,
    } for h in history]

    return {
        **card_data,
        'state_id': state.id,
        'srs_stage': stage_idx,
        'stage_name': stage_name,
        'stage_color': stage_color,
        'status': state.status,
        'due_date': state.due_date.isoformat() if state.due_date else None,
        'reps': state.reps,
        'lapses': state.lapses,
        'stability': stability,
        'difficulty': difficulty,
        'review_history': review_history,
    }


def suspend_card(user_id, content_id):
    """Suspendiert eine Karte."""
    state = CardReviewState.query.filter_by(user_id=user_id, content_id=content_id).first()
    if not state:
        return False
    state.status = 'suspended'
    db.session.commit()
    return True


def unsuspend_card(user_id, content_id):
    """Reaktiviert eine suspendierte Karte."""
    state = CardReviewState.query.filter_by(user_id=user_id, content_id=content_id).first()
    if not state or state.status != 'suspended':
        return False
    state.status = 'review'
    state.due_date = datetime.utcnow()
    db.session.commit()
    return True


def reset_card(user_id, content_id):
    """Setzt den FSRS-State einer Karte zurueck."""
    state = CardReviewState.query.filter_by(user_id=user_id, content_id=content_id).first()
    if not state:
        return False
    new_card = Card()
    state.fsrs_card_state = new_card.to_json()
    state.due_date = datetime.utcnow()
    state.status = 'new'
    state.reps = 0
    state.lapses = 0
    db.session.commit()
    return True
