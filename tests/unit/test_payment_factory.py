# tests/unit/test_payment_factory.py
"""
Phase 2: Unit-Tests für PaymentServiceFactory.
Testkonzept-IDs: U-PF01 bis U-PF07
"""

import pytest
import os
from unittest.mock import patch


# ── U-PF01: Mock bei MOCK_PAYMENTS_ENABLED ───────────────────

class TestPaymentFactoryMock:
    def test_mock_when_env_enabled(self, app):
        """U-PF01: MOCK_PAYMENTS_ENABLED=true → MockPaymentService."""
        with app.app_context():
            with patch.dict(os.environ, {"MOCK_PAYMENTS_ENABLED": "true"}):
                from app.services.payment_factory import PaymentServiceFactory
                service = PaymentServiceFactory.get_service()
                assert "MockPaymentService" in type(service).__name__

    def test_mock_when_config_enabled(self, app):
        """U-PF01: Config MOCK_PAYMENTS_ENABLED → MockPaymentService."""
        with app.app_context():
            app.config["MOCK_PAYMENTS_ENABLED"] = True
            with patch.dict(os.environ, {"MOCK_PAYMENTS_ENABLED": ""}):
                from app.services.payment_factory import PaymentServiceFactory
                service = PaymentServiceFactory.get_service()
                assert "MockPaymentService" in type(service).__name__
            app.config["MOCK_PAYMENTS_ENABLED"] = "true"  # Reset


# ── U-PF02: Mock als Standard ───────────────────────────────

class TestPaymentFactoryDefault:
    def test_default_is_mock(self, app):
        """U-PF02: Ohne Provider-Konfiguration → MockPaymentService."""
        with app.app_context():
            with patch.dict(os.environ, {
                "MOCK_PAYMENTS_ENABLED": "",
                "PAYMENT_PROVIDER": "",
            }):
                app.config["MOCK_PAYMENTS_ENABLED"] = False
                app.config["PAYMENT_PROVIDER"] = ""
                from app.services.payment_factory import PaymentServiceFactory
                service = PaymentServiceFactory.get_service()
                assert "MockPaymentService" in type(service).__name__
                app.config["MOCK_PAYMENTS_ENABLED"] = "true"  # Reset


# ── U-PF03: Payrexx ohne Credentials → Mock ─────────────────

class TestPaymentFactoryPayrexxFallback:
    def test_payrexx_without_credentials_falls_back(self, app):
        """U-PF03: PAYMENT_PROVIDER=payrexx ohne Keys → MockPaymentService."""
        with app.app_context():
            with patch.dict(os.environ, {
                "MOCK_PAYMENTS_ENABLED": "",
                "PAYMENT_PROVIDER": "payrexx",
                "PAYREXX_INSTANCE": "",
                "PAYREXX_API_SECRET": "",
            }):
                app.config["MOCK_PAYMENTS_ENABLED"] = False
                app.config["PAYMENT_PROVIDER"] = "payrexx"
                app.config["PAYREXX_INSTANCE"] = None
                app.config["PAYREXX_API_SECRET"] = None
                from app.services.payment_factory import PaymentServiceFactory
                service = PaymentServiceFactory.get_service()
                assert "MockPaymentService" in type(service).__name__
                app.config["MOCK_PAYMENTS_ENABLED"] = "true"  # Reset


# ── U-PF04: Payrexx mit Credentials ─────────────────────────

class TestPaymentFactoryPayrexx:
    def test_payrexx_with_credentials(self, app):
        """U-PF04: PAYMENT_PROVIDER=payrexx mit Keys → PayrexxPaymentService."""
        with app.app_context():
            with patch.dict(os.environ, {
                "MOCK_PAYMENTS_ENABLED": "",
                "PAYMENT_PROVIDER": "payrexx",
                "PAYREXX_INSTANCE": "test-instance",
                "PAYREXX_API_SECRET": "test-secret",
            }):
                app.config["MOCK_PAYMENTS_ENABLED"] = False
                app.config["PAYMENT_PROVIDER"] = "payrexx"
                app.config["PAYREXX_INSTANCE"] = "test-instance"
                app.config["PAYREXX_API_SECRET"] = "test-secret"
                from app.services.payment_factory import PaymentServiceFactory
                service = PaymentServiceFactory.get_service()
                assert "PayrexxPaymentService" in type(service).__name__
                app.config["MOCK_PAYMENTS_ENABLED"] = "true"  # Reset


# ── U-PF05: PostFinance ohne Credentials → Mock ─────────────

class TestPaymentFactoryPostFinanceFallback:
    def test_postfinance_without_credentials(self, app):
        """U-PF05: PAYMENT_PROVIDER=postfinance ohne Keys → MockPaymentService."""
        with app.app_context():
            with patch.dict(os.environ, {
                "MOCK_PAYMENTS_ENABLED": "",
                "PAYMENT_PROVIDER": "postfinance",
                "POSTFINANCE_SPACE_ID": "",
                "POSTFINANCE_USER_ID": "",
                "POSTFINANCE_API_SECRET": "",
            }):
                app.config["MOCK_PAYMENTS_ENABLED"] = False
                app.config["PAYMENT_PROVIDER"] = "postfinance"
                from app.services.payment_factory import PaymentServiceFactory
                service = PaymentServiceFactory.get_service()
                assert "MockPaymentService" in type(service).__name__
                app.config["MOCK_PAYMENTS_ENABLED"] = "true"  # Reset


# ── U-PF06: get_payment_service Wrapper ─────────────────────

class TestGetPaymentService:
    def test_get_payment_service_function(self, app):
        """U-PF06: get_payment_service() Wrapper funktioniert."""
        with app.app_context():
            from app.services.payment_factory import get_payment_service
            service = get_payment_service()
            assert service is not None
