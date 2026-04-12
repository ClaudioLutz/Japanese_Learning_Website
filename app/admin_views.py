# app/admin_views.py
"""
Flask-Admin Integration fuer Standard-CRUD-Operationen.

Ersetzt die manuellen API-Endpoints fuer Kana, Kanji, Vocabulary,
Grammar, LessonCategory und Course durch automatisch generierte
Admin-Views mit Suche, Filter, Sortierung und Pagination.
"""
from flask import redirect, url_for, request
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user


class AuthMixin:
    """Stellt sicher, dass nur eingeloggte Admins Zugriff haben."""

    def is_accessible(self):
        return (
            current_user.is_authenticated
            and current_user.is_admin
        )

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('routes.login', next=request.url))


class SecureModelView(AuthMixin, ModelView):
    """Basis-ModelView mit Admin-Authentifizierung."""
    page_size = 50
    can_export = True
    export_types = ['csv']
    can_view_details = True


class SecureAdminIndexView(AuthMixin, AdminIndexView):
    """Admin-Index mit Authentifizierung und Uebersichts-Dashboard."""

    @expose('/')
    def index(self):
        from app.models import (
            Kana, Kanji, Vocabulary, Grammar,
            Lesson, Course, User, LessonCategory,
        )
        from app import db

        stats = {
            'users': db.session.query(User).count(),
            'lessons': db.session.query(Lesson).count(),
            'courses': db.session.query(Course).count(),
            'vocabulary': db.session.query(Vocabulary).count(),
            'grammar': db.session.query(Grammar).count(),
            'kanji': db.session.query(Kanji).count(),
            'kana': db.session.query(Kana).count(),
            'categories': db.session.query(LessonCategory).count(),
        }
        return self.render('admin/flask_admin_index.html', stats=stats)


# ---------------------------------------------------------------------------
# Model-spezifische Views
# ---------------------------------------------------------------------------

class KanaAdmin(SecureModelView):
    column_list = ['id', 'character', 'romanization', 'type']
    column_searchable_list = ['character', 'romanization']
    column_filters = ['type']
    column_editable_list = ['romanization', 'type']
    column_labels = {
        'character': 'Zeichen',
        'romanization': 'Romaji',
        'type': 'Typ (hiragana/katakana)',
        'stroke_order_info': 'Strichreihenfolge',
        'example_sound_url': 'Audio-URL',
    }
    form_columns = ['character', 'romanization', 'type', 'stroke_order_info', 'example_sound_url']


class KanjiAdmin(SecureModelView):
    column_list = ['id', 'character', 'meaning', 'onyomi', 'kunyomi', 'jlpt_level', 'status', 'created_by_ai']
    column_searchable_list = ['character', 'meaning', 'onyomi', 'kunyomi']
    column_filters = ['jlpt_level', 'status', 'created_by_ai']
    column_editable_list = ['status']
    column_labels = {
        'character': 'Zeichen',
        'meaning': 'Bedeutung',
        'jlpt_level': 'JLPT',
        'stroke_order_info': 'Strichreihenfolge',
        'radical': 'Radikal',
        'stroke_count': 'Striche',
        'status': 'Status',
        'created_by_ai': 'KI-generiert',
    }
    form_columns = [
        'character', 'meaning', 'onyomi', 'kunyomi',
        'jlpt_level', 'radical', 'stroke_count',
        'stroke_order_info', 'status', 'created_by_ai',
    ]


class VocabularyAdmin(SecureModelView):
    column_list = ['id', 'word', 'reading', 'meaning', 'jlpt_level', 'status', 'created_by_ai']
    column_searchable_list = ['word', 'reading', 'meaning']
    column_filters = ['jlpt_level', 'status', 'created_by_ai']
    column_editable_list = ['status']
    column_labels = {
        'word': 'Wort',
        'reading': 'Lesung',
        'meaning': 'Bedeutung',
        'jlpt_level': 'JLPT',
        'example_sentence_japanese': 'Beispiel (JP)',
        'example_sentence_english': 'Beispiel (EN)',
        'audio_url': 'Audio-URL',
        'status': 'Status',
        'created_by_ai': 'KI-generiert',
    }
    form_columns = [
        'word', 'reading', 'meaning', 'jlpt_level',
        'example_sentence_japanese', 'example_sentence_english',
        'audio_url', 'status', 'created_by_ai',
    ]


class GrammarAdmin(SecureModelView):
    column_list = ['id', 'title', 'romaji', 'structure', 'jlpt_level', 'status', 'created_by_ai']
    column_searchable_list = ['title', 'romaji', 'structure', 'explanation']
    column_filters = ['jlpt_level', 'status', 'created_by_ai']
    column_editable_list = ['status']
    column_labels = {
        'title': 'Titel',
        'romaji': 'Romaji',
        'explanation': 'Erklaerung',
        'structure': 'Struktur',
        'jlpt_level': 'JLPT',
        'example_sentences': 'Beispielsaetze',
        'status': 'Status',
        'created_by_ai': 'KI-generiert',
    }
    form_columns = [
        'title', 'romaji', 'structure', 'explanation', 'jlpt_level',
        'example_sentences', 'status', 'created_by_ai',
    ]


class LessonCategoryAdmin(SecureModelView):
    column_list = ['id', 'name', 'description', 'color_code', 'created_at']
    column_searchable_list = ['name', 'description']
    column_editable_list = ['name', 'color_code']
    column_labels = {
        'name': 'Name',
        'description': 'Beschreibung',
        'color_code': 'Farbe (Hex)',
        'created_at': 'Erstellt am',
    }
    form_columns = ['name', 'description', 'color_code']


class CourseAdmin(SecureModelView):
    column_list = ['id', 'title', 'is_published', 'price', 'is_purchasable', 'created_at']
    column_searchable_list = ['title', 'description']
    column_filters = ['is_published', 'is_purchasable']
    column_editable_list = ['is_published', 'price']
    column_labels = {
        'title': 'Titel',
        'description': 'Beschreibung',
        'background_image_url': 'Hintergrundbild-URL',
        'is_published': 'Veroeffentlicht',
        'price': 'Preis (CHF)',
        'is_purchasable': 'Kaufbar',
        'created_at': 'Erstellt am',
        'updated_at': 'Aktualisiert am',
    }
    form_columns = [
        'title', 'description', 'background_image_url',
        'is_published', 'price', 'is_purchasable', 'lessons',
    ]


class LessonAdmin(SecureModelView):
    """Nur Listenansicht und Basisdaten — der volle Editor bleibt custom."""
    column_list = [
        'id', 'title', 'lesson_type', 'category',
        'difficulty_level', 'order_index', 'is_published', 'price',
    ]
    column_searchable_list = ['title', 'description']
    column_filters = ['lesson_type', 'is_published', 'category', 'difficulty_level']
    column_editable_list = ['is_published', 'order_index', 'price']
    column_labels = {
        'title': 'Titel',
        'description': 'Beschreibung',
        'lesson_type': 'Typ',
        'category': 'Kategorie',
        'difficulty_level': 'Schwierigkeit',
        'estimated_duration': 'Dauer (Min.)',
        'order_index': 'Reihenfolge',
        'is_published': 'Veroeffentlicht',
        'allow_guest_access': 'Gastzugang',
        'instruction_language': 'Sprache',
        'price': 'Preis (CHF)',
        'is_purchasable': 'Kaufbar',
        'created_at': 'Erstellt am',
    }
    form_columns = [
        'title', 'description', 'category', 'difficulty_level',
        'estimated_duration', 'order_index', 'is_published',
        'allow_guest_access', 'instruction_language',
        'thumbnail_url', 'background_image_url', 'video_intro_url',
        'price', 'is_purchasable',
    ]
    # Lektions-Inhalt wird weiterhin ueber den Custom-Editor verwaltet
    can_delete = False


class UserAdmin(SecureModelView):
    """User-Verwaltung — Passwort-Hash wird nie angezeigt."""
    column_list = ['id', 'username', 'email', 'subscription_level', 'is_admin']
    column_searchable_list = ['username', 'email']
    column_filters = ['subscription_level', 'is_admin']
    column_editable_list = ['subscription_level', 'is_admin']
    column_labels = {
        'username': 'Benutzername',
        'email': 'E-Mail',
        'subscription_level': 'Abo-Stufe',
        'is_admin': 'Admin',
    }
    # Kein Create/Delete fuer User ueber Flask-Admin
    can_create = False
    can_delete = False
    form_columns = ['username', 'email', 'subscription_level', 'is_admin']
    form_excluded_columns = ['password_hash', 'lesson_progress', 'course_purchases']


# ---------------------------------------------------------------------------
# Factory-Funktion: registriert Flask-Admin auf der App
# ---------------------------------------------------------------------------

def init_admin(app, db_session):
    """Initialisiert Flask-Admin und registriert alle ModelViews."""
    from app.models import (
        Kana, Kanji, Vocabulary, Grammar,
        LessonCategory, Lesson, Course, User,
    )

    admin = Admin(
        app,
        name='JP Admin',
        index_view=SecureAdminIndexView(url='/admin-panel', endpoint='admin_panel'),
    )

    admin.add_view(KanaAdmin(Kana, db_session, name='Kana', endpoint='admin_kana', category='Japanisch'))
    admin.add_view(KanjiAdmin(Kanji, db_session, name='Kanji', endpoint='admin_kanji', category='Japanisch'))
    admin.add_view(VocabularyAdmin(Vocabulary, db_session, name='Vokabeln', endpoint='admin_vocabulary', category='Japanisch'))
    admin.add_view(GrammarAdmin(Grammar, db_session, name='Grammatik', endpoint='admin_grammar', category='Japanisch'))
    admin.add_view(LessonCategoryAdmin(LessonCategory, db_session, name='Kategorien', endpoint='admin_categories', category='Lektionen'))
    admin.add_view(LessonAdmin(Lesson, db_session, name='Lektionen', endpoint='admin_lessons', category='Lektionen'))
    admin.add_view(CourseAdmin(Course, db_session, name='Kurse', endpoint='admin_courses', category='Lektionen'))
    admin.add_view(UserAdmin(User, db_session, name='Benutzer', endpoint='admin_users', category='System'))

    return admin
