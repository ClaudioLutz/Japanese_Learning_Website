"""Öffentliche Seite /neu — was sich für Lernende geändert hat.

Server-seitig gerendert (kein JS-Nachladen → kein Soft-404-Risiko).
Quelle: app/data/neuigkeiten.md via news_service.
"""
from flask import Blueprint, render_template

from app import news_service

news_bp = Blueprint('news', __name__)


@news_bp.route('/neu')
def index():
    entries = news_service.load_news()
    return render_template(
        'neu.html',
        groups=news_service.group_by_day(entries),
        latest=entries[0] if entries else None,
    )
