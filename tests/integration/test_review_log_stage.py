"""ReviewLog.stage_at_review wird beim Bewerten mitgeloggt (Stufe VOR dem Review).

Datenbasis fuer die „Genauigkeit nach SRS-Stufe"-Statistik des Dashboards.
"""
from app import db, srs_service
from app.models import ReviewLog
from tests.factories import LessonFactory, VocabularyFactory, LessonContentFactory


def _make_content():
    lesson = LessonFactory()
    vocab = VocabularyFactory()
    content = LessonContentFactory(lesson_id=lesson.id, content_type='vocabulary', content_id=vocab.id)
    db.session.commit()
    return content


class TestReviewLogStageAtReview:
    def test_new_card_logs_stage_zero(self, auth_client):
        """Erstes Review einer neuen Karte -> stage_at_review == 0 (Neu)."""
        client, user = auth_client
        content = _make_content()

        srs_service.rate_card(user.id, content.id, 3)

        log = ReviewLog.query.filter_by(user_id=user.id, content_id=content.id).first()
        assert log is not None
        assert log.stage_at_review == 0

    def test_stage_logged_on_every_review(self, auth_client):
        """Jeder Review schreibt eine ganzzahlige Stufe (0..9), nie NULL."""
        client, user = auth_client
        content = _make_content()

        # Mehrfach „Easy" -> Karte reift; jeder Log hat eine gueltige Stufe.
        for _ in range(3):
            srs_service.rate_card(user.id, content.id, 4)

        logs = ReviewLog.query.filter_by(user_id=user.id, content_id=content.id).all()
        assert len(logs) == 3
        for log in logs:
            assert log.stage_at_review is not None
            assert 0 <= log.stage_at_review <= 9
        # Stufen sind monoton nicht-fallend (Stufe VOR dem Review steigt mit Reife).
        stages = [log.stage_at_review for log in sorted(logs, key=lambda x: x.id)]
        assert stages == sorted(stages)
