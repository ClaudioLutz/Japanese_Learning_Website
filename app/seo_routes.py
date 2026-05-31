"""SEO-Routes: robots.txt, sitemap.xml, Lesson-Course-Schema-Endpunkte.

Bewusst als eigenes Blueprint gehalten — routes.py ist mit 4'200+ Zeilen
schon Gott-Datei. Hier landet alles, was Suchmaschinen sehen sollen,
ohne UI-Logik dazwischen.
"""
from datetime import datetime
from xml.sax.saxutils import escape

from flask import Blueprint, Response, current_app, send_from_directory

from app import db
from app.models import Course, Lesson, LessonCategory


seo_bp = Blueprint('seo', __name__)


# ── favicon.ico an Root ────────────────────────────────────────────────
# Google und viele Bots fragen /favicon.ico direkt ab — nicht über /static.
@seo_bp.route('/favicon.ico')
def favicon_ico():
    return send_from_directory(
        current_app.static_folder,
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon',
    )


# ── robots.txt ─────────────────────────────────────────────────────────
# Crawl-Direktiven. Admin-, API-, OAuth-, Account-Pfade ausschliessen,
# damit das Crawl-Budget nicht verbrannt wird.
@seo_bp.route('/robots.txt')
def robots_txt():
    site_url = current_app.config['SITE_URL']
    robots_index = current_app.config.get('ROBOTS_INDEX', 'index,follow')

    # Staging / Preview: explizit alles sperren
    if 'noindex' in robots_index.lower():
        body = "User-agent: *\nDisallow: /\n"
        return Response(body, mimetype='text/plain')

    # /login und /register bleiben crawlbar — sie tragen meta robots noindex,follow,
    # damit Google internen Links zu Lessons folgt, sie aber nicht selbst indexiert.
    lines = [
        "User-agent: *",
        "Disallow: /admin",
        "Disallow: /admin-panel",
        "Disallow: /api/",
        "Disallow: /auth/",
        "Disallow: /logout",
        "Disallow: /profile",
        "Disallow: /my-lessons",
        "Disallow: /review",
        "Disallow: /practice",
        "Disallow: /payment/",
        "Disallow: /purchase/",
        "Disallow: /debug/",
        "Disallow: /healthz",
        "Disallow: /health",
        "Allow: /",
        "",
        f"Sitemap: {site_url}/sitemap.xml",
        "",
    ]
    return Response("\n".join(lines), mimetype='text/plain')


# ── sitemap.xml ────────────────────────────────────────────────────────
def _url_entry(loc: str, lastmod: datetime | None, changefreq: str, priority: str) -> str:
    parts = [
        "  <url>",
        f"    <loc>{escape(loc)}</loc>",
    ]
    if lastmod:
        parts.append(f"    <lastmod>{lastmod.strftime('%Y-%m-%d')}</lastmod>")
    parts.append(f"    <changefreq>{changefreq}</changefreq>")
    parts.append(f"    <priority>{priority}</priority>")
    parts.append("  </url>")
    return "\n".join(parts)


@seo_bp.route('/sitemap.xml')
def sitemap_xml():
    site_url = current_app.config['SITE_URL']
    today = datetime.utcnow()
    languages = current_app.config.get('CONTENT_LANGUAGES', ['german'])

    entries: list[str] = []

    # /courses nur listen, wenn es mind. 1 publizierten Kurs gibt — sonst
    # rendert die Seite nur einen leeren Container (Soft-404-Signal an Google).
    has_published_course = (
        db.session.query(Course).filter(Course.is_published.is_(True)).count() > 0
    )

    # Statische, oeffentliche Seiten
    static_pages = [
        ('/', 'daily', '1.0'),
        ('/n5-bundle', 'weekly', '0.9'),
        ('/jlpt-n5-schweiz', 'weekly', '0.9'),
        ('/lessons', 'daily', '0.8'),
        *([('/courses', 'weekly', '0.7')] if has_published_course else []),
        ('/ueber', 'monthly', '0.6'),
        ('/lernmethode', 'monthly', '0.6'),
        ('/legal/impressum', 'yearly', '0.2'),
        ('/legal/datenschutz', 'yearly', '0.2'),
        ('/legal/agb', 'yearly', '0.2'),
        ('/legal/widerruf', 'yearly', '0.2'),
    ]
    for path, changefreq, priority in static_pages:
        entries.append(_url_entry(site_url + path, today, changefreq, priority))

    # Veroeffentlichte Lessons (nur in aktivierter Sprache). Nur Gast-zugaengliche
    # Lessons listen: Paid-Lessons rendern fuer Gaeste/Googlebot die noindex-Paywall
    # — sie in die Sitemap zu setzen, gibt ein widerspruechliches Signal und
    # verbrennt Crawl-Budget. Jede gelistete URL liefert so index,follow.
    lessons = (
        db.session.query(Lesson)
        .filter(Lesson.is_published.is_(True))
        .filter(Lesson.allow_guest_access.is_(True))
        .filter(Lesson.instruction_language.in_(languages))
        .all()
    )
    for lesson in lessons:
        entries.append(_url_entry(
            f"{site_url}/lessons/{lesson.id}",
            lesson.updated_at or lesson.created_at,
            'monthly',
            '0.7',
        ))

    # JLPT-Modul-Detail-Seiten — eigene URL pro Modul, eigene Inhalte
    modules = (
        db.session.query(LessonCategory)
        .filter(LessonCategory.jlpt_level.isnot(None))
        .filter(LessonCategory.slug.isnot(None))
        .all()
    )
    for mod in modules:
        # Nur Module mit mind. 2 publizierten Lessons in den sichtbaren Sprachen
        # — bei <=1 Lesson redirected die Route, eigene URL waere doppelter Content
        published_count = sum(
            1 for lesson in mod.lessons
            if lesson.is_published and lesson.instruction_language in languages
        )
        if published_count >= 2:
            entries.append(_url_entry(
                f"{site_url}/learn/n{mod.jlpt_level}/{mod.slug}",
                today,
                'weekly',
                '0.7',
            ))

    # Veroeffentlichte Courses
    courses = db.session.query(Course).filter(Course.is_published.is_(True)).all()
    for course in courses:
        entries.append(_url_entry(
            f"{site_url}/course/{course.id}",
            today,
            'monthly',
            '0.6',
        ))

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(entries)
        + "\n</urlset>\n"
    )
    return Response(xml, mimetype='application/xml')
