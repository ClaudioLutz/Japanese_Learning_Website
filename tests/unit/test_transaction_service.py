# tests/unit/test_transaction_service.py
"""
Phase 2: Unit-Tests für PaymentTransactionService.
Testkonzept-IDs: U-TS01 bis U-TS09
"""

import pytest
from app import db
from app.models import (
    PaymentTransaction, LessonPurchase, CoursePurchase,
)
from app.services.transaction_service import PaymentTransactionService
from tests.factories import (
    UserFactory, PaidLessonFactory, PaidCourseFactory,
    PaymentTransactionFactory,
)


@pytest.fixture
def tx_service():
    return PaymentTransactionService()


# ── U-TS01: create_payment_transaction ───────────────────────

class TestCreatePaymentTransaction:
    def test_create_transaction(self, app_context, tx_service):
        """U-TS01: Transaktion wird korrekt erstellt."""
        user = UserFactory()
        lesson = PaidLessonFactory()
        db.session.commit()

        tx = tx_service.create_payment_transaction(
            transaction_id=100001,
            user=user,
            item_type="lesson",
            item_id=lesson.id,
            amount=29.0,
        )
        assert tx.transaction_id == 100001
        assert tx.state == "PENDING"
        assert tx.currency == "CHF"
        assert tx.user_id == user.id

    def test_duplicate_transaction_id_raises(self, app_context, tx_service):
        """U-TS02: Doppelte transaction_id wirft Fehler."""
        user = UserFactory()
        db.session.commit()
        tx_service.create_payment_transaction(100002, user, "lesson", 1, 10.0)
        with pytest.raises(Exception):
            tx_service.create_payment_transaction(100002, user, "lesson", 2, 20.0)


# ── U-TS03: update_transaction_state ─────────────────────────

class TestUpdateTransactionState:
    def test_update_to_completed_creates_lesson_purchase(self, app_context, tx_service):
        """U-TS03: COMPLETED-Status erstellt LessonPurchase."""
        user = UserFactory()
        lesson = PaidLessonFactory()
        db.session.commit()
        tx_service.create_payment_transaction(200001, user, "lesson", lesson.id, 29.0)

        result = tx_service.update_transaction_state(200001, "COMPLETED")
        assert result is True

        purchase = LessonPurchase.query.filter_by(user_id=user.id, lesson_id=lesson.id).first()
        assert purchase is not None
        assert purchase.price_paid == 29.0

    def test_update_to_fulfill_creates_course_purchase(self, app_context, tx_service):
        """U-TS04: FULFILL-Status erstellt CoursePurchase."""
        user = UserFactory()
        course = PaidCourseFactory()
        db.session.commit()
        tx_service.create_payment_transaction(200002, user, "course", course.id, 99.0)

        result = tx_service.update_transaction_state(200002, "FULFILL")
        assert result is True

        purchase = CoursePurchase.query.filter_by(user_id=user.id, course_id=course.id).first()
        assert purchase is not None

    def test_update_to_failed(self, app_context, tx_service):
        """U-TS05: FAILED-Status wird gesetzt, kein Purchase."""
        user = UserFactory()
        lesson = PaidLessonFactory()
        db.session.commit()
        tx_service.create_payment_transaction(200003, user, "lesson", lesson.id, 29.0)

        result = tx_service.update_transaction_state(200003, "FAILED")
        assert result is True

        purchase = LessonPurchase.query.filter_by(user_id=user.id).first()
        assert purchase is None

    def test_update_nonexistent_transaction(self, app_context, tx_service):
        """U-TS06: Nicht existierende Transaktion → False."""
        result = tx_service.update_transaction_state(999999, "COMPLETED")
        assert result is False

    def test_no_duplicate_purchase_on_double_complete(self, app_context, tx_service):
        """U-TS07: Zweimal COMPLETED erstellt keinen doppelten Purchase."""
        user = UserFactory()
        lesson = PaidLessonFactory()
        db.session.commit()
        tx_service.create_payment_transaction(200004, user, "lesson", lesson.id, 29.0)
        tx_service.update_transaction_state(200004, "COMPLETED")
        # Zweiter COMPLETED-Aufruf
        tx_service.update_transaction_state(200004, "COMPLETED")

        purchases = LessonPurchase.query.filter_by(user_id=user.id, lesson_id=lesson.id).all()
        assert len(purchases) == 1

    def test_webhook_data_stored(self, app_context, tx_service):
        """U-TS08: Webhook-Daten werden gespeichert."""
        user = UserFactory()
        db.session.commit()
        tx_service.create_payment_transaction(200005, user, "lesson", 1, 10.0)

        webhook = {"event": "transaction.confirmed", "id": 200005}
        tx_service.update_transaction_state(200005, "COMPLETED", webhook_data=webhook)

        tx = PaymentTransaction.query.filter_by(transaction_id=200005).first()
        assert tx.webhook_data is not None
        assert tx.webhook_data["event"] == "transaction.confirmed"


# ── U-TS09: get_user_transactions / get_transaction_by_id ────

class TestTransactionQueries:
    def test_get_user_transactions(self, app_context, tx_service):
        """U-TS09: User-Transaktionen abrufen."""
        user = UserFactory()
        db.session.commit()
        tx_service.create_payment_transaction(300001, user, "lesson", 1, 10.0)
        tx_service.create_payment_transaction(300002, user, "course", 2, 50.0)

        txs = tx_service.get_user_transactions(user.id)
        assert len(txs) == 2

    def test_get_transaction_by_id(self, app_context, tx_service):
        """U-TS09: Einzelne Transaktion nach ID abrufen."""
        user = UserFactory()
        db.session.commit()
        tx_service.create_payment_transaction(300003, user, "lesson", 1, 10.0)

        tx = tx_service.get_transaction_by_id(300003)
        assert tx is not None
        assert tx.amount == 10.0

    def test_get_nonexistent_transaction(self, app_context, tx_service):
        """Nicht existierende Transaktion gibt None."""
        tx = tx_service.get_transaction_by_id(999999)
        assert tx is None
