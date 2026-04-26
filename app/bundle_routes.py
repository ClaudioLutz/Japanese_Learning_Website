"""Bundle-Verkauf: Verkaufsseite + Buy-API fuer das N5-Bundle.

Eigenes Blueprint, damit routes.py nicht weiter waechst (4'200+ Zeilen).
Reuse der bestehenden Course-Purchase-Pipeline (CoursePurchase, Webhook,
transaction_service) — das Bundle ist intern ein Course namens
'JLPT N5 Komplett', angelegt via scripts/setup_n5_bundle.py.

Preis ist dynamisch aus bundle_service.get_n5_bundle_price().
"""
from __future__ import annotations

import logging

from flask import Blueprint, current_app, jsonify, render_template, request
from flask_login import current_user, login_required
from flask_wtf.csrf import validate_csrf

from app import db
from app.models import CoursePurchase
from app.services.bundle_service import (
    EARLY_BIRD_PRICE_CHF,
    EARLY_BIRD_THRESHOLD_PCT,
    REGULAR_PRICE_CHF,
    get_n5_bundle_course,
    get_n5_bundle_price,
)
from app.services.coverage_service import get_jlpt_coverage


bundle_bp = Blueprint("bundle", __name__)
logger = logging.getLogger(__name__)


@bundle_bp.route("/n5-bundle")
def n5_bundle():
    """Verkaufsseite fuer 'JLPT N5 Komplett'."""
    coverage = get_jlpt_coverage(5)
    price, price_label = get_n5_bundle_price()

    bundle_course = get_n5_bundle_course()
    already_owned = False
    if bundle_course and current_user.is_authenticated:
        already_owned = (
            db.session.query(CoursePurchase)
            .filter_by(user_id=current_user.id, course_id=bundle_course.id)
            .first()
            is not None
        )

    return render_template(
        "bundles/n5_bundle.html",
        coverage=coverage,
        price=price,
        price_label=price_label,
        early_bird_price=EARLY_BIRD_PRICE_CHF,
        regular_price=REGULAR_PRICE_CHF,
        threshold_pct=EARLY_BIRD_THRESHOLD_PCT,
        already_owned=already_owned,
        bundle_available=bundle_course is not None,
    )


@bundle_bp.route("/api/bundles/n5/purchase", methods=["POST"])
@login_required
def n5_bundle_purchase():
    """Initiiert den Bundle-Kauf via Payrexx (oder Mock).

    Nutzt die bestehende Course-Pipeline. Setzt course.price in-memory auf
    den dynamischen Preis vor dem Aufruf — die DB bleibt mit regulaerem
    Anker-Preis unveraendert.
    """
    # CSRF-Pruefung analog routes.py:2750 — in Tests deaktiviert
    if current_app.config.get("WTF_CSRF_ENABLED", True):
        csrf_token = request.headers.get("X-CSRFToken")
        if not csrf_token:
            return jsonify({"error": "CSRF token missing"}), 400
        try:
            validate_csrf(csrf_token)
        except Exception:
            return jsonify({"error": "CSRF token invalid"}), 400

    # AGB / Widerrufsverzicht muessen ausdruecklich akzeptiert sein
    payload = request.get_json(silent=True) or {}
    if not payload.get("accepted_terms"):
        return jsonify({
            "error": "AGB und Widerrufsverzicht muessen akzeptiert werden",
            "error_type": "TERMS_NOT_ACCEPTED",
        }), 400

    bundle_course = get_n5_bundle_course()
    if bundle_course is None:
        logger.error("Bundle-Kauf versucht, aber Course existiert nicht. setup_n5_bundle.py ausfuehren.")
        return jsonify({
            "error": "Bundle ist aktuell nicht verfuegbar",
            "error_type": "BUNDLE_NOT_CONFIGURED",
        }), 503

    # Doppelkauf verhindern
    existing = (
        db.session.query(CoursePurchase)
        .filter_by(user_id=current_user.id, course_id=bundle_course.id)
        .first()
    )
    if existing:
        return jsonify({"error": "Du besitzt das Bundle bereits"}), 400

    # Dynamischen Preis auf den Course setzen (in-memory, kein commit) — Payrexx liest course.price
    price, price_label = get_n5_bundle_price()
    bundle_course.price = price

    # Lazy imports um Circular-Import zu vermeiden
    from app.services.payment_factory import get_payment_service
    from app.services.transaction_service import PaymentTransactionService

    try:
        payment_service = get_payment_service()
        transaction_service = PaymentTransactionService()

        result = payment_service.create_course_transaction(current_user, bundle_course)
        if not result.get("success"):
            return jsonify({
                "error": result.get("error", "Payment-Initiierung fehlgeschlagen"),
                "error_type": result.get("error_type", "GATEWAY_ERROR"),
            }), 400

        transaction_id = result["transaction_id"]
        payment_transaction = transaction_service.create_payment_transaction(
            transaction_id=transaction_id,
            user=current_user,
            item_type="course",
            item_id=bundle_course.id,
            amount=price,
        )
        # Bundle-spezifische Metadaten anhaengen, ohne bestehende zu zerstoeren
        meta = dict(payment_transaction.transaction_metadata or {})
        meta.update({"bundle": "n5", "price_label": price_label})
        payment_transaction.transaction_metadata = meta
        db.session.commit()

        url_result = payment_service.generate_payment_page_url(transaction_id)
        if not url_result.get("success"):
            return jsonify({
                "error": "Payment-URL konnte nicht erzeugt werden",
                "error_details": url_result.get("error"),
            }), 500

        logger.info(
            f"N5-Bundle-Kauf gestartet: User {current_user.id}, "
            f"Course {bundle_course.id}, Preis CHF {price:.2f} ({price_label}), "
            f"Transaction {transaction_id}"
        )

        return jsonify({
            "success": True,
            "transaction_id": transaction_id,
            "payment_url": url_result["payment_url"],
            "amount": price,
            "price_label": price_label,
            "currency": "CHF",
        }), 201

    except Exception as e:
        current_app.logger.error(f"Bundle-Kauf-Fehler: {e}")
        return jsonify({"error": "Bundle-Kauf konnte nicht initiiert werden"}), 500
