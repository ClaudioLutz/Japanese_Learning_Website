"""Routes for the legal pages: Impressum, Datenschutz, AGB, Widerruf.

Anbieter-Daten werden via Env-Variablen oder Config gelesen, damit die
Templates ohne Code-Aenderung mit echten Werten gefuellt werden koennen.
Vorgesehen sind:
    LEGAL_OWNER_NAME   (z.B. "Claudio Lutz")
    LEGAL_OWNER_STREET (z.B. "Musterstrasse 12")
    LEGAL_OWNER_ZIP    (z.B. "9000")
    LEGAL_OWNER_CITY   (z.B. "St. Gallen")
    LEGAL_EMAIL        (z.B. "info@japanese-learning.ch")
    LEGAL_UID          (optional, MwSt-UID)

Wenn nicht gesetzt, zeigen die Templates Platzhalter wie '[Name des
Anbieters]' an, damit Lesende sofort sehen, dass die Werte fehlen.
"""
import os
from datetime import date

from flask import Blueprint, render_template

bp = Blueprint("legal", __name__, url_prefix="/legal")


def _ctx() -> dict:
    today = date.today()
    months_de = [
        "", "Januar", "Februar", "März", "April", "Mai", "Juni",
        "Juli", "August", "September", "Oktober", "November", "Dezember",
    ]
    return {
        "legal_owner_name": os.environ.get("LEGAL_OWNER_NAME", "Claudio Lutz"),
        "legal_owner_street": os.environ.get("LEGAL_OWNER_STREET", "Promenadenstrasse 72"),
        "legal_owner_zip": os.environ.get("LEGAL_OWNER_ZIP", "9400"),
        "legal_owner_city": os.environ.get("LEGAL_OWNER_CITY", "Rorschach"),
        "legal_email": os.environ.get("LEGAL_EMAIL", "info@japanese-learning.ch"),
        "legal_uid": os.environ.get("LEGAL_UID"),
        "today_de": f"{today.day}. {months_de[today.month]} {today.year}",
    }


@bp.route("/impressum")
def impressum():
    return render_template("legal/impressum.html", **_ctx())


@bp.route("/datenschutz")
def datenschutz():
    return render_template("legal/datenschutz.html", **_ctx())


@bp.route("/agb")
def agb():
    return render_template("legal/agb.html", **_ctx())


@bp.route("/widerruf")
def widerruf():
    return render_template("legal/widerruf.html", **_ctx())
