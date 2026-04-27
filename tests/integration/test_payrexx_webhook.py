"""Integration-Tests fuer /api/payment/webhook/payrexx Route."""

import hmac
import hashlib
import json

from app import db
from app.models import Course, CoursePurchase, PaymentTransaction


WEBHOOK_SECRET = "test-csrf-key"  # conftest setzt diesen Wert auch als WEBHOOK_SECRET


def _sign(secret: str, body: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


def _bundle_course():
    course = Course(
        title="JLPT N5 Komplett",
        description="Test", is_published=True, is_purchasable=True, price=9.90,
    )
    db.session.add(course)
    db.session.commit()
    return course


def _pending_transaction(user_id, course_id, gateway_id):
    txn = PaymentTransaction(
        transaction_id=gateway_id,
        user_id=user_id,
        item_type="course",
        item_id=course_id,
        amount=9.90,
        currency="CHF",
        state="PENDING",
    )
    db.session.add(txn)
    db.session.commit()
    return txn


def test_webhook_uses_payment_request_id_not_transaction_id(app, client, db):
    """
    Regression: Webhook muss `invoice.paymentRequestId` (= unsere Gateway-ID)
    fuer den DB-Lookup verwenden, nicht `transaction.id` (Payrexx-Transaktions-Instanz-ID).
    Bug am 2026-04-27 entdeckt: erster Live-Kauf wurde nicht in course_purchase eingetragen.
    """
    app.config["PAYREXX_WEBHOOK_SECRET"] = WEBHOOK_SECRET

    from tests.factories import UserFactory
    user = UserFactory()
    course = _bundle_course()
    db.session.commit()

    gateway_id = 33108083  # entspricht unserer payment_transaction.transaction_id
    transaction_instance_id = 36019229  # Payrexx interne Transaktions-Instanz, NICHT relevant

    _pending_transaction(user.id, course.id, gateway_id)

    payload = {
        "transaction": {
            "id": transaction_instance_id,
            "status": "confirmed",
            "referenceId": f"course_{course.id}_user_{user.id}",
            "invoice": {
                "paymentRequestId": gateway_id,
                "currency": "CHF",
            },
        }
    }
    body = json.dumps(payload).encode("utf-8")
    sig = _sign(WEBHOOK_SECRET, body)

    resp = client.post(
        "/api/payment/webhook/payrexx",
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-Webhook-Signature": sig,
        },
    )

    assert resp.status_code == 200

    txn = PaymentTransaction.query.filter_by(transaction_id=gateway_id).first()
    assert txn is not None
    assert txn.state == "COMPLETED"

    purchase = CoursePurchase.query.filter_by(user_id=user.id, course_id=course.id).first()
    assert purchase is not None, "course_purchase muss bei status=confirmed entstehen"


def test_webhook_invalid_signature_rejected(app, client, db):
    """Webhook mit falscher Signatur → 403."""
    app.config["PAYREXX_WEBHOOK_SECRET"] = WEBHOOK_SECRET
    body = b'{"transaction":{"id":1,"status":"confirmed","invoice":{}}}'

    resp = client.post(
        "/api/payment/webhook/payrexx",
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-Webhook-Signature": "wrong-signature",
        },
    )
    assert resp.status_code == 403
