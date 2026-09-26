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
        'mnemonic': 'Merkhilfe (Mnemonic)',
    }
    form_columns = ['character', 'romanization', 'type', 'stroke_order_info', 'example_sound_url', 'mnemonic']


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
    column_list = [
        'id', 'name', 'jlpt_level', 'display_order', 'icon_emoji',
        'prerequisite', 'color_code', 'created_at',
    ]
    column_searchable_list = ['name', 'slug', 'description']
    column_filters = ['jlpt_level']
    column_editable_list = ['name', 'color_code', 'display_order', 'jlpt_level', 'icon_emoji']
    column_default_sort = [('jlpt_level', False), ('display_order', False)]
    column_labels = {
        'name': 'Name',
        'slug': 'Slug (Identifier)',
        'description': 'Beschreibung',
        'color_code': 'Farbe (Hex)',
        'jlpt_level': 'JLPT-Level',
        'display_order': 'Reihenfolge',
        'icon_emoji': 'Icon (Emoji/Zeichen)',
        'prerequisite': 'Voraussetzung (Modul)',
        'prerequisite_category_id': 'Voraussetzung (Modul)',
        'created_at': 'Erstellt am',
    }
    form_columns = [
        'name', 'slug', 'description', 'color_code',
        'jlpt_level', 'display_order', 'icon_emoji', 'prerequisite',
    ]


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
    column_list = ['id', 'username', 'email', 'subscription_level', 'is_admin',
                   'created_at', 'last_login']
    column_searchable_list = ['username', 'email']
    column_filters = ['subscription_level', 'is_admin', 'created_at', 'last_login']
    column_editable_list = ['subscription_level', 'is_admin']
    # Zeitstempel sortierbar machen (Nutzeranalyse: Neuzugaenge, Rueckkehrer)
    column_sortable_list = ['id', 'username', 'email', 'subscription_level',
                            'is_admin', 'created_at', 'last_login']
    column_default_sort = ('id', False)
    column_labels = {
        'username': 'Benutzername',
        'email': 'E-Mail',
        'subscription_level': 'Abo-Stufe',
        'is_admin': 'Admin',
        'created_at': 'Registriert am',
        'last_login': 'Letzter Login',
    }
    # Kein Create/Delete fuer User ueber Flask-Admin
    can_create = False
    can_delete = False
    form_columns = ['username', 'email', 'subscription_level', 'is_admin']
    form_excluded_columns = ['password_hash', 'lesson_progress', 'course_purchases']


# ---------------------------------------------------------------------------
# Rollenspiel-Tutor — nur lesend (Monitoring: Nutzung, Tokens, Kosten)
# ---------------------------------------------------------------------------

class ReadOnlyModelView(SecureModelView):
    can_create = False
    can_edit = False
    can_delete = False
    can_view_details = True


class RoleplaySessionAdmin(ReadOnlyModelView):
    column_list = ['id', 'user_id', 'lesson_content_id', 'role_user', 'role_bot', 'status',
                   'turn_count', 'xp_awarded', 'model_name', 'tokens_in', 'tokens_out',
                   'cost_usd', 'started_at', 'ended_at']
    column_filters = ['status', 'model_name', 'started_at', 'user_id']
    column_sortable_list = ['id', 'user_id', 'status', 'turn_count', 'tokens_in',
                            'tokens_out', 'cost_usd', 'started_at']
    column_default_sort = ('id', True)
    column_labels = {
        'user_id': 'User', 'lesson_content_id': 'Dialog (Content)',
        'role_user': 'Rolle Nutzer', 'role_bot': 'Rolle Bot', 'turn_count': 'Nutzerzüge',
        'xp_awarded': 'XP', 'model_name': 'Modell', 'cost_usd': 'Kosten (USD)',
        'started_at': 'Start', 'ended_at': 'Ende', 'goal_de': 'Ziel',
        'correction_json': 'Korrektur (JSON)',
    }


class RoleplayTurnAdmin(ReadOnlyModelView):
    column_list = ['id', 'session_id', 'turn_index', 'speaker', 'text_jp', 'created_at']
    column_filters = ['speaker', 'session_id', 'created_at']
    column_default_sort = ('id', True)
    column_labels = {'session_id': 'Session', 'turn_index': 'Zug', 'speaker': 'Sprecher',
                     'text_jp': 'Text (JP)', 'created_at': 'Zeit'}


class TutorQuestionAdmin(ReadOnlyModelView):
    column_list = ['id', 'user_id', 'lesson_id', 'page_number', 'model_name',
                   'tokens_in', 'tokens_out', 'cost_usd', 'created_at']
    column_filters = ['lesson_id', 'user_id', 'created_at']
    column_sortable_list = ['id', 'user_id', 'lesson_id', 'cost_usd', 'created_at']
    column_default_sort = ('id', True)
    column_labels = {'user_id': 'User', 'lesson_id': 'Lektion', 'page_number': 'Seite',
                     'model_name': 'Modell', 'cost_usd': 'Kosten (USD)', 'created_at': 'Zeit',
                     'question': 'Frage', 'answer': 'Antwort'}


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

    from app.models import RoleplaySession, RoleplayTurn, TutorQuestion
    admin.add_view(RoleplaySessionAdmin(RoleplaySession, db_session, name='Gespräche',
                                        endpoint='admin_roleplay_sessions', category='Rollenspiel'))
    admin.add_view(RoleplayTurnAdmin(RoleplayTurn, db_session, name='Züge',
                                     endpoint='admin_roleplay_turns', category='Rollenspiel'))
    admin.add_view(TutorQuestionAdmin(TutorQuestion, db_session, name='Tutorfragen',
                                      endpoint='admin_tutor_questions', category='Rollenspiel'))

    return admin
