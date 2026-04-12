# app/srs_service.py
"""Service-Klasse fuer alle SRS-Operationen (FSRS-Algorithmus)."""
import json
import logging
from datetime import datetime, timezone

from fsrs import Card, Rating, Scheduler, State

from app import db
from app.models import CardReviewState, LessonContent, ReviewLog, UserSRSSettings

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
    else:
        card = Card()
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
            'meaning': ref.meaning,
            'example_jp': ref.example_sentence_japanese or '',
            'example_en': ref.example_sentence_english or '',
            'image_url': ref.image_url or '',
        }
    elif content_item.content_type == 'grammar':
        data['front'] = ref.title
        data['details'] = {
            'explanation': ref.explanation,
            'structure': ref.structure or '',
            'romaji': ref.romaji or '',
            'examples': ref.example_sentences or '',
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
