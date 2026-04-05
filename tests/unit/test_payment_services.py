# tests/unit/test_payment_services.py
"""
Phase 2: Unit-Tests für PayrexxPaymentService und MockPaymentService.
Testkonzept-IDs: U-PS01 bis U-PS12
"""

import pytest
import hmac
import hashlib
from unittest.mock import patch, MagicMock
from app import db
from tests.factories import (
    UserFactory, PaidLessonFactory, PaidCourseFactory,
    LessonPurchaseFactory,
)


# ── MockPaymentService Tests ────────────────────────────────

class TestMockPaymentService:
    def test_mock_lesson_purchase_success(self, app_context):
        """U-PS01: Mock-Lektionskauf erstellt Purchase-Record."""
        from app.services.mock_payment_service import MockPaymentService
        service = MockPaymentService()
        user = UserFactory()
        lesson = PaidLessonFactory()
        db.session.commit()

        result = service.create_lesson_transaction(user, lesson)
        assert result["success"] is True
        assert result["mock_purchase"] is True

    def test_mock_lesson_duplicate_blocked(self, app_context):
        """U-PS02: Doppelter Mock-Kauf wird abgelehnt."""
        from app.services.mock_payment_service import MockPaymentService
        service = MockPaymentService()
        user = UserFactory()
        lesson = PaidLessonFactory()
        db.session.commit()

        service.create_lesson_transaction(user, lesson)
        result = service.create_lesson_transaction(user, lesson)
        assert result["success"] is False
        assert result["error_type"] == "DUPLICATE_PURCHASE"

    def test_mock_course_purchase_success(self, app_context):
        """U-PS03: Mock-Kurskauf erstellt Purchase-Record."""
        from app.services.mock_payment_service import MockPaymentService
        service = MockPaymentService()
        user = UserFactory()
        course = PaidCourseFactory()
        db.session.commit()

        result = service.create_course_transaction(user, course)
        assert result["success"] is True

    def test_mock_transaction_status_always_completed(self, app_context):
        """U-PS04: Mock-Status ist immer COMPLETED."""
        from app.services.mock_payment_service import MockPaymentService
        service = MockPaymentService()
        result = service.get_transaction_status(12345)
        assert result["state"] == "COMPLETED"

    def test_mock_payment_url(self, app):
        """U-PS05: Mock-Payment-URL gibt Success-URL."""
        from app.services.mock_payment_service import MockPaymentService
        with app.app_context():
            service = MockPaymentService()
            result = service.generate_payment_page_url(12345)
            assert result["success"] is True
            assert "payment_url" in result


# ── PayrexxPaymentService Tests ─────────────────────────────

class TestPayrexxPaymentService:
    @pytest.fixture
    def payrexx_service(self, app):
        """Payrexx-Service mit Test-Config."""
        with app.app_context():
            app.config["PAYREXX_INSTANCE"] = "test-instance"
            app.config["PAYREXX_API_SECRET"] = "test-secret"
            app.config["PAYREXX_WEBHOOK_SECRET"] = "webhook-secret"
            from app.services.payrexx_payment_service import PayrexxPaymentService
            service = PayrexxPaymentService()
            yield service

    def test_status_mapping_confirmed(self, payrexx_service):
        """U-PS06: Payrexx 'confirmed' → 'COMPLETED'."""
        from app.services.payrexx_payment_service import PayrexxPaymentService
        assert PayrexxPaymentService._map_status("confirmed") == "COMPLETED"

    def test_status_mapping_waiting(self, payrexx_service):
        """U-PS07: Payrexx 'waiting' → 'PENDING'."""
        from app.services.payrexx_payment_service import PayrexxPaymentService
        assert PayrexxPaymentService._map_status("waiting") == "PENDING"

    def test_status_mapping_cancelled(self, payrexx_service):
        """U-PS08: Payrexx 'cancelled' → 'CANCELLED'."""
        from app.services.payrexx_payment_service import PayrexxPaymentService
        assert PayrexxPaymentService._map_status("cancelled") == "CANCELLED"

    def test_status_mapping_unknown(self, payrexx_service):
        """U-PS09: Unbekannter Payrexx-Status → 'PENDING'."""
        from app.services.payrexx_payment_service import PayrexxPaymentService
        assert PayrexxPaymentService._map_status("unknown_state") == "PENDING"

    def test_webhook_signature_valid(self, payrexx_service):
        """U-PS10: Gültige Webhook-Signatur wird verifiziert."""
        payload = b'{"transaction": {"id": 123}}'
        signature = hmac.new(
            b"webhook-secret", payload, hashlib.sha256
        ).hexdigest()
        assert payrexx_service.verify_webhook_signature(payload, signature) is True

    def test_webhook_signature_invalid(self, payrexx_service):
        """U-PS11: Ungültige Webhook-Signatur wird abgelehnt."""
        payload = b'{"transaction": {"id": 123}}'
        assert payrexx_service.verify_webhook_signature(payload, "invalid") is False

    def test_webhook_no_secret_configured(self, app):
        """U-PS12: Fehlender Webhook-Secret → False."""
        with app.app_context():
            app.config["PAYREXX_INSTANCE"] = "test"
            app.config["PAYREXX_API_SECRET"] = "test"
            app.config["PAYREXX_WEBHOOK_SECRET"] = None
            from app.services.payrexx_payment_service import PayrexxPaymentService
            service = PayrexxPaymentService()
            assert service.verify_webhook_signature(b"data", "sig") is False

    @patch("app.services.payrexx_payment_service.requests.post")
    def test_create_lesson_transaction_success(self, mock_post, payrexx_service, app_context):
        """U-PS: Erfolgreiche Gateway-Erstellung für Lektion."""
        mock_post.return_value = MagicMock(
            ok=True,
            json=lambda: {
                "status": "success",
                "data": [{"id": 999, "link": "https://payrexx.com/pay/999"}],
            },
        )
        user = UserFactory()
        lesson = PaidLessonFactory()
        db.session.commit()

        result = payrexx_service.create_lesson_transaction(user, lesson)
        assert result["success"] is True
        assert result["transaction_id"] == 999

    @patch("app.services.payrexx_payment_service.requests.post")
    def test_create_lesson_transaction_api_error(self, mock_post, payrexx_service, app_context):
        """U-PS: API-Fehler wird abgefangen."""
        mock_post.return_value = MagicMock(ok=False, status_code=500, text="Server Error")
        user = UserFactory()
        lesson = PaidLessonFactory()
        db.session.commit()

        result = payrexx_service.create_lesson_transaction(user, lesson)
        assert result["success"] is False

    @patch("app.services.payrexx_payment_service.requests.get")
    def test_get_transaction_status(self, mock_get, payrexx_service):
        """U-PS: Transaktionsstatus abrufen."""
        mock_get.return_value = MagicMock(
            ok=True,
            json=lambda: {
                "status": "success",
                "data": [{"id": 123, "status": "confirmed"}],
            },
        )
        result = payrexx_service.get_transaction_status(123)
        assert result["success"] is True
        assert result["state"] == "COMPLETED"
