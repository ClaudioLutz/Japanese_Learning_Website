# app/services/payment_factory.py
"""
Unified Payment Service Factory
Wählt den passenden Payment-Provider: Payrexx, PostFinance oder Mock.

Steuerung via Umgebungsvariablen:
    PAYMENT_PROVIDER=payrexx|postfinance|mock   (Standard: mock)
    MOCK_PAYMENTS_ENABLED=true                   (erzwingt Mock-Modus)

Payrexx-Konfiguration:
    PAYREXX_INSTANCE=<instanzname>
    PAYREXX_API_SECRET=<api-secret>
    PAYREXX_WEBHOOK_SECRET=<webhook-signing-key>
"""

import os
import logging
from flask import current_app


class PaymentServiceFactory:
    """Factory für die Erstellung der passenden Payment-Service-Instanz."""

    @staticmethod
    def get_service():
        logger = logging.getLogger(__name__)
        logger.info("=== PAYMENT SERVICE AUSWAHL ===")

        # 1. Mock-Modus erzwungen?
        mock_env = os.environ.get('MOCK_PAYMENTS_ENABLED', '').lower() == 'true'
        mock_config = current_app.config.get('MOCK_PAYMENTS_ENABLED', False)
        if isinstance(mock_config, str):
            mock_config = mock_config.lower() == 'true'

        if mock_env or mock_config:
            logger.info("ENTSCHEID: MockPaymentService (explizit aktiviert)")
            from app.services.mock_payment_service import MockPaymentService
            return MockPaymentService()

        # 2. Provider bestimmen
        provider = (
            os.environ.get('PAYMENT_PROVIDER', '')
            or current_app.config.get('PAYMENT_PROVIDER', '')
        ).lower().strip()

        logger.info(f"PAYMENT_PROVIDER = '{provider}'")

        # ── Payrexx ──────────────────────────────────────────
        if provider == 'payrexx':
            payrexx_instance = (
                os.environ.get('PAYREXX_INSTANCE')
                or current_app.config.get('PAYREXX_INSTANCE')
            )
            payrexx_secret = (
                os.environ.get('PAYREXX_API_SECRET')
                or current_app.config.get('PAYREXX_API_SECRET')
            )

            if payrexx_instance and payrexx_secret:
                try:
                    from app.services.payrexx_payment_service import PayrexxPaymentService
                    service = PayrexxPaymentService()
                    logger.info(f"ENTSCHEID: PayrexxPaymentService (Instanz: {payrexx_instance})")
                    return service
                except Exception as e:
                    logger.error(f"Payrexx-Initialisierung fehlgeschlagen: {e}")
                    logger.info("FALLBACK: MockPaymentService")
                    from app.services.mock_payment_service import MockPaymentService
                    return MockPaymentService()
            else:
                logger.warning("PAYMENT_PROVIDER=payrexx, aber Credentials fehlen → MockPaymentService")
                from app.services.mock_payment_service import MockPaymentService
                return MockPaymentService()

        # ── PostFinance (Legacy) ─────────────────────────────
        if provider == 'postfinance':
            pf_configured = all([
                os.environ.get('POSTFINANCE_SPACE_ID') or current_app.config.get('POSTFINANCE_SPACE_ID'),
                os.environ.get('POSTFINANCE_USER_ID') or current_app.config.get('POSTFINANCE_USER_ID'),
                os.environ.get('POSTFINANCE_API_SECRET') or current_app.config.get('POSTFINANCE_API_SECRET'),
            ])

            if pf_configured:
                try:
                    from app.services.payment_service import EnhancedPostFinanceService
                    service = EnhancedPostFinanceService()
                    logger.info("ENTSCHEID: PostFinanceService")
                    return service
                except Exception as e:
                    logger.error(f"PostFinance-Initialisierung fehlgeschlagen: {e}")
                    logger.info("FALLBACK: MockPaymentService")
                    from app.services.mock_payment_service import MockPaymentService
                    return MockPaymentService()
            else:
                logger.warning("PAYMENT_PROVIDER=postfinance, aber Credentials fehlen → MockPaymentService")
                from app.services.mock_payment_service import MockPaymentService
                return MockPaymentService()

        # ── Standard: Mock ───────────────────────────────────
        logger.info("ENTSCHEID: MockPaymentService (kein Provider konfiguriert)")
        from app.services.mock_payment_service import MockPaymentService
        return MockPaymentService()


def get_payment_service():
    """Haupteinstiegspunkt für den Payment-Service."""
    return PaymentServiceFactory.get_service()
