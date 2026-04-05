# app/services/payrexx_payment_service.py
"""
Payrexx Payment Service — REST-API-Integration für die Japanese Learning Website.

Payrexx API v1.14: https://developers.payrexx.com/reference
Authentifizierung via X-API-KEY Header.
"""

import hmac
import hashlib
import logging
import requests
from flask import current_app, url_for
from app.models import User, Lesson, Course


class PayrexxPaymentService:
    """Payment Service mit Payrexx REST API (Gateway-basiert)."""

    API_VERSION = "v1.14"

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.instance = current_app.config.get('PAYREXX_INSTANCE')
        self.api_secret = current_app.config.get('PAYREXX_API_SECRET')
        self.webhook_secret = current_app.config.get('PAYREXX_WEBHOOK_SECRET')

        if not self.instance or not self.api_secret:
            raise ValueError("PAYREXX_INSTANCE oder PAYREXX_API_SECRET nicht konfiguriert.")

        self.base_url = f"https://api.payrexx.com/{self.API_VERSION}"
        self.logger.info(f"PayrexxPaymentService initialisiert (Instanz: {self.instance})")

    # ── Interne Hilfsmethoden ─────────────────────────────────────

    def _headers(self) -> dict:
        return {
            "X-API-KEY": self.api_secret,
            "Content-Type": "application/json",
        }

    def _url(self, endpoint: str) -> str:
        return f"{self.base_url}/{endpoint}/?instance={self.instance}"

    def _create_gateway(self, amount_cents: int, purpose: str,
                        reference_id: str, currency: str = "CHF") -> dict:
        """Erstellt ein Payrexx Gateway (Checkout-Seite) und gibt die Antwort zurück."""
        payload = {
            "amount": amount_cents,
            "currency": currency,
            "purpose": purpose,
            "referenceId": reference_id,
            "successRedirectUrl": current_app.config.get(
                'PAYMENT_SUCCESS_URL',
                url_for('routes.payment_success', _external=True)
            ),
            "failedRedirectUrl": current_app.config.get(
                'PAYMENT_FAILURE_URL',
                url_for('routes.payment_failed', _external=True)
            ),
            "cancelRedirectUrl": current_app.config.get(
                'PAYMENT_FAILURE_URL',
                url_for('routes.payment_failed', _external=True)
            ),
            "pm": ["twint", "visa", "mastercard", "apple-pay", "google-pay"],
            "skipResultPage": False,
        }

        resp = requests.post(
            self._url("Gateway"),
            headers=self._headers(),
            json=payload,
            timeout=30,
        )

        if not resp.ok:
            self.logger.error(f"Payrexx Gateway-Fehler {resp.status_code}: {resp.text[:500]}")
            raise RuntimeError(f"Payrexx API Fehler: {resp.status_code}")

        data = resp.json()
        if data.get("status") != "success":
            raise RuntimeError(f"Payrexx Gateway fehlgeschlagen: {data}")

        return data["data"][0]

    # ── Öffentliche Schnittstelle (identisch mit PostFinanceService) ──

    def create_lesson_transaction(self, user: User, lesson: Lesson) -> dict:
        """Erstellt eine Payrexx-Transaktion für einen Lektionskauf."""
        try:
            amount_cents = int(round(lesson.price * 100))
            reference_id = f"lesson_{lesson.id}_user_{user.id}"
            purpose = f"Lektion: {lesson.title[:100]}"

            gateway = self._create_gateway(amount_cents, purpose, reference_id)

            self.logger.info(
                f"Payrexx Gateway erstellt: ID {gateway['id']} "
                f"für User {user.id}, Lektion {lesson.id}"
            )

            return {
                'success': True,
                'transaction_id': gateway['id'],
                'gateway_link': gateway['link'],
                'gateway': gateway,
            }

        except Exception as e:
            self.logger.error(f"Fehler beim Erstellen der Lektions-Transaktion: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'GATEWAY_ERROR',
            }

    def create_course_transaction(self, user: User, course: Course) -> dict:
        """Erstellt eine Payrexx-Transaktion für einen Kurskauf."""
        try:
            amount_cents = int(round(course.price * 100))
            reference_id = f"course_{course.id}_user_{user.id}"
            purpose = f"Kurs: {course.title[:100]}"

            gateway = self._create_gateway(amount_cents, purpose, reference_id)

            self.logger.info(
                f"Payrexx Gateway erstellt: ID {gateway['id']} "
                f"für User {user.id}, Kurs {course.id}"
            )

            return {
                'success': True,
                'transaction_id': gateway['id'],
                'gateway_link': gateway['link'],
                'gateway': gateway,
            }

        except Exception as e:
            self.logger.error(f"Fehler beim Erstellen der Kurs-Transaktion: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'GATEWAY_ERROR',
            }

    def generate_payment_page_url(self, transaction_id: int) -> dict:
        """
        Gibt die Payment-URL für ein bestehendes Gateway zurück.

        Bei Payrexx wird die URL direkt beim Gateway-Erstellen mitgeliefert.
        Diese Methode fragt den Status ab und gibt den Link zurück.
        """
        try:
            resp = requests.get(
                self._url(f"Gateway/{transaction_id}"),
                headers=self._headers(),
                timeout=30,
            )

            if not resp.ok:
                return {
                    'success': False,
                    'error': f"Gateway {transaction_id} nicht gefunden",
                    'error_type': 'NOT_FOUND',
                }

            data = resp.json()
            gateway = data["data"][0]

            return {
                'success': True,
                'payment_url': gateway['link'],
            }

        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen der Payment-URL: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'SYSTEM_ERROR',
            }

    def get_transaction_status(self, transaction_id: int) -> dict:
        """Fragt den aktuellen Status eines Gateways ab."""
        try:
            resp = requests.get(
                self._url(f"Gateway/{transaction_id}"),
                headers=self._headers(),
                timeout=30,
            )

            if not resp.ok:
                return {
                    'success': False,
                    'error': f"Gateway {transaction_id} nicht abrufbar",
                    'error_type': 'API_ERROR',
                }

            data = resp.json()
            gateway = data["data"][0]

            # Payrexx-Status auf interne Zustände mappen
            payrexx_status = gateway.get("status", "waiting")
            internal_state = self._map_status(payrexx_status)

            return {
                'success': True,
                'state': internal_state,
                'payrexx_status': payrexx_status,
                'transaction_id': transaction_id,
            }

        except Exception as e:
            self.logger.error(f"Fehler beim Status-Check: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'SYSTEM_ERROR',
            }

    # ── Webhook-Verifizierung ─────────────────────────────────────

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verifiziert die X-Webhook-Signature eines Payrexx-Webhooks."""
        if not self.webhook_secret:
            self.logger.warning("PAYREXX_WEBHOOK_SECRET nicht konfiguriert — Signatur kann nicht geprüft werden")
            return False

        computed = hmac.new(
            self.webhook_secret.encode('utf-8'),
            payload,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(computed, signature)

    # ── Status-Mapping ────────────────────────────────────────────

    @staticmethod
    def _map_status(payrexx_status: str) -> str:
        """Mappt Payrexx-Transaktionsstatus auf interne Zustände."""
        mapping = {
            'waiting': 'PENDING',
            'confirmed': 'COMPLETED',
            'authorized': 'AUTHORIZED',
            'reserved': 'AUTHORIZED',
            'cancelled': 'CANCELLED',
            'declined': 'DECLINED',
            'refunded': 'REFUNDED',
            'partially-refunded': 'REFUNDED',
            'refund_pending': 'REFUNDED',
            'chargeback': 'DECLINED',
            'error': 'FAILED',
            'disputed': 'DECLINED',
            'expired': 'FAILED',
        }
        return mapping.get(payrexx_status, 'PENDING')
