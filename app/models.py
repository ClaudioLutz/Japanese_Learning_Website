# app/models.py
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json
from typing import List
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Table, Column, Integer, String, Text, Boolean, DateTime, JSON, event, BigInteger
class User(UserMixin, db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    subscription_level: Mapped[str] = mapped_column(String(50), default='free')
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Account Lockout
    failed_login_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False, server_default='0')
    locked_until: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Streak-System
    current_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False, server_default='0')
    longest_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False, server_default='0')
    last_activity_date = db.Column(db.Date, nullable=True)
    total_xp: Mapped[int] = mapped_column(Integer, default=0, nullable=False, server_default='0')

    # Phase 6: Gamification
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False, server_default='1')
    total_reviews: Mapped[int] = mapped_column(Integer, default=0, nullable=False, server_default='0')
    total_mastered: Mapped[int] = mapped_column(Integer, default=0, nullable=False, server_default='0')

    lesson_progress: Mapped[List['UserLessonProgress']] = relationship('UserLessonProgress', backref='user', lazy=True, cascade='all, delete-orphan')
    course_purchases: Mapped[List['CoursePurchase']] = relationship('CoursePurchase', backref='user', lazy=True, cascade='all, delete-orphan')

    LOCKOUT_THRESHOLD = 5
    LOCKOUT_DURATION_MINUTES = 15

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def is_locked(self):
        if self.locked_until and self.locked_until > datetime.utcnow():
            return True
        return False

    def record_failed_login(self):
        from datetime import timedelta
        self.failed_login_count = (self.failed_login_count or 0) + 1
        if self.failed_login_count >= self.LOCKOUT_THRESHOLD:
            self.locked_until = datetime.utcnow() + timedelta(minutes=self.LOCKOUT_DURATION_MINUTES)

    def record_successful_login(self):
        self.failed_login_count = 0
        self.locked_until = None
        self.update_streak()

    def update_streak(self):
        """Aktualisiert den Tages-Streak bei Aktivitaet mit Streak-Freeze-Unterstuetzung."""
        today = datetime.utcnow().date()
        if self.last_activity_date == today:
            return  # Bereits heute aktiv
        from datetime import timedelta

        # Streak-Freeze-Nachfuellung (1x pro Woche)
        settings = getattr(self, 'srs_settings', None)
        if settings:
            if not settings.last_freeze_replenish or (today - settings.last_freeze_replenish).days >= 7:
                settings.streak_freezes_available = 1
                settings.last_freeze_replenish = today

        if self.last_activity_date == today - timedelta(days=1):
            # Gestern gelernt → Streak weiter
            self.current_streak = (self.current_streak or 0) + 1
        elif (self.last_activity_date
              and self.last_activity_date == today - timedelta(days=2)
              and settings
              and (settings.streak_freezes_available or 0) > 0):
            # Vorgestern gelernt, gestern verpasst, Freeze verfuegbar
            settings.streak_freezes_available -= 1
            # Streak bleibt (kein +1, aber kein Reset)
        else:
            self.current_streak = 1
        if self.current_streak > (self.longest_streak or 0):
            self.longest_streak = self.current_streak
        self.last_activity_date = today

    def add_xp(self, amount):
        """Fuegt XP hinzu und prueft Level-Up."""
        self.total_xp = (self.total_xp or 0) + amount
        while self.total_xp >= self.xp_for_next_level:
            self.level = (self.level or 1) + 1

    @property
    def xp_for_next_level(self):
        """XP-Schwelle fuer das naechste Level (polynomiale Kurve)."""
        return int(100 * ((self.level or 1) ** 1.5))

    @property
    def level_title(self):
        """Japanisch-thematischer Level-Titel."""
        lvl = self.level or 1
        if lvl <= 5:
            return 'Anfänger (初心者)'
        elif lvl <= 10:
            return 'Schüler (学生)'
        elif lvl <= 15:
            return 'Lehrling (見習い)'
        elif lvl <= 25:
            return 'Fortgeschritten (上級者)'
        elif lvl <= 40:
            return 'Experte (達人)'
        elif lvl <= 50:
            return 'Meister (師匠)'
        return 'Grossmeister (名人)'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Kana(db.Model):
    __allow_unmapped__ = True
    id = db.Column(db.Integer, primary_key=True)
    character = db.Column(db.String(5), nullable=False, unique=True)
    romanization = db.Column(db.String(10), nullable=False)
    type = db.Column(db.String(10), nullable=False)  # 'hiragana' or 'katakana'
    stroke_order_info = db.Column(db.String(255), nullable=True)
    example_sound_url = db.Column(db.String(255), nullable=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<Kana {self.character}>'

class Kanji(db.Model):
    __allow_unmapped__ = True
    id = db.Column(db.Integer, primary_key=True)
    character = db.Column(db.String(5), nullable=False, unique=True)
    meaning = db.Column(db.Text, nullable=False)
    onyomi = db.Column(db.String(100), nullable=True)
    kunyomi = db.Column(db.String(100), nullable=True)
    jlpt_level = db.Column(db.Integer, nullable=True)
    stroke_order_info = db.Column(db.String(255), nullable=True)
    radical = db.Column(db.String(10), nullable=True)
    stroke_count = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(20), default='approved', nullable=False)  # 'approved', 'pending_approval'
    created_by_ai = db.Column(db.Boolean, default=False, nullable=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<Kanji {self.character}>'

class Vocabulary(db.Model):
    __allow_unmapped__ = True
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(100), nullable=False, unique=True)
    reading = db.Column(db.String(100), nullable=False)
    romaji = db.Column(db.String(200), nullable=True)
    meaning = db.Column(db.Text, nullable=False)
    meaning_de = db.Column(db.Text, nullable=True)
    jlpt_level = db.Column(db.Integer, nullable=True)
    example_sentence_japanese = db.Column(db.Text, nullable=True)
    example_sentence_english = db.Column(db.Text, nullable=True)
    audio_url = db.Column(db.String(255), nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    status = db.Column(db.String(20), default='approved', nullable=False)  # 'approved', 'pending_approval'
    created_by_ai = db.Column(db.Boolean, default=False, nullable=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<Vocabulary {self.word}>'

class Grammar(db.Model):
    __allow_unmapped__ = True
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, unique=True)
    explanation = db.Column(db.Text, nullable=False)
    structure = db.Column(db.Text, nullable=True)
    romaji = db.Column(db.String(500), nullable=True)
    jlpt_level = db.Column(db.Integer, nullable=True)
    example_sentences = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='approved', nullable=False)  # 'approved', 'pending_approval'
    created_by_ai = db.Column(db.Boolean, default=False, nullable=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<Grammar {self.title}>'

class LessonCategory(db.Model):
    __allow_unmapped__ = True
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    color_code = db.Column(db.String(7), default='#007bff')  # hex color for UI
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Lernpfad-Felder (Mayuko-Direktive 2026-04-25: JLPT-strukturierter Pfad)
    # Eine Kategorie wirkt als Modul innerhalb eines JLPT-Levels.
    slug = db.Column(db.String(80), unique=True, nullable=True)  # z.B. 'n5-hiragana'
    jlpt_level = db.Column(db.Integer, nullable=True)             # 5, 4, 3, 2, 1
    display_order = db.Column(db.Integer, default=0, nullable=False)  # Reihenfolge innerhalb Level
    icon_emoji = db.Column(db.String(8), nullable=True)           # z.B. 'あ' oder '🔢'
    prerequisite_category_id = db.Column(
        db.Integer, db.ForeignKey('lesson_category.id'), nullable=True
    )

    # Relationship
    lessons = db.relationship('Lesson', backref='category', lazy=True)
    prerequisite = db.relationship(
        'LessonCategory', remote_side=[id], foreign_keys=[prerequisite_category_id]
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<LessonCategory {self.name}>'

    def completion_for_user(self, user, languages: list[str] | None = None) -> tuple[int, int]:
        """Returns (completed_lessons, total_published_lessons) fuer Pfad-Anzeige.

        Wenn `languages` gesetzt ist (z.B. ['german']), werden nur Lessons mit
        passender instruction_language gezaehlt — fuer den Sprach-Filter aus
        app.config['CONTENT_LANGUAGES'].
        """
        from app.models import Lesson, UserLessonProgress
        published = [l for l in self.lessons if l.is_published]
        if languages is not None:
            published = [l for l in published if l.instruction_language in languages]
        total = len(published)
        if not user or not getattr(user, 'is_authenticated', False) or total == 0:
            return 0, total
        progress = UserLessonProgress.query.filter(
            UserLessonProgress.user_id == user.id,
            UserLessonProgress.lesson_id.in_([l.id for l in published]),
            UserLessonProgress.is_completed == True,  # noqa: E712
        ).count()
        return progress, total

    def is_unlocked_for_user(self, user, threshold: float = 0.8) -> bool:
        """Modul ist freigeschaltet, wenn Vorgaenger-Modul zu >=threshold complete ist.
        Ohne Voraussetzung: immer unlocked. Anonyme User: unlocked wenn Modul kostenlose
        Inhalte hat (Detail-Pruefung erfolgt bei Lektion-Zugriff)."""
        if self.prerequisite_category_id is None:
            return True
        if not user or not getattr(user, 'is_authenticated', False):
            return True  # Anonyme User sehen alles, harte Pruefung beim Lesson-Zugriff
        done, total = self.prerequisite.completion_for_user(user)
        if total == 0:
            return True
        return (done / total) >= threshold

class Lesson(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    lesson_type: Mapped[str] = mapped_column(String(20), nullable=False)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey('lesson_category.id'), nullable=True)
    difficulty_level: Mapped[int] = mapped_column(Integer, nullable=True)
    estimated_duration: Mapped[int] = mapped_column(Integer, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    allow_guest_access: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    instruction_language: Mapped[str] = mapped_column(String(10), default='english', nullable=False)
    thumbnail_url: Mapped[str] = mapped_column(String(255), nullable=True)
    background_image_url: Mapped[str] = mapped_column(String(1000), nullable=True)
    background_image_path: Mapped[str] = mapped_column(String(500), nullable=True)
    video_intro_url: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Pricing fields
    price: Mapped[float] = mapped_column(db.Float, nullable=False, default=0.0)
    is_purchasable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    
    # Relationships
    content_items: Mapped[List['LessonContent']] = relationship('LessonContent', backref='lesson', lazy=True, cascade='all, delete-orphan')
    prerequisites: Mapped[List['LessonPrerequisite']] = relationship('LessonPrerequisite', 
                                  foreign_keys='LessonPrerequisite.lesson_id',
                                  backref='lesson', lazy=True, cascade='all, delete-orphan')
    required_by: Mapped[List['LessonPrerequisite']] = relationship('LessonPrerequisite',
                                foreign_keys='LessonPrerequisite.prerequisite_lesson_id',
                                lazy=True)
    user_progress: Mapped[List['UserLessonProgress']] = relationship('UserLessonProgress', lazy=True, cascade='all, delete-orphan')
    pages_metadata: Mapped[List['LessonPage']] = relationship('LessonPage', backref='lesson', lazy=True, cascade='all, delete-orphan')
    courses: Mapped[List['Course']] = relationship('Course', secondary='course_lessons', back_populates='lessons')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<Lesson {self.title}>'
    
    def get_prerequisites(self) -> List['Lesson']:
        """Get list of prerequisite lessons"""
        return [prereq.prerequisite_lesson for prereq in self.prerequisites]
    
    def is_accessible_to_user(self, user):
        """Check if user can access this lesson based on pricing, subscription and prerequisites"""
        # Handle guest users (not authenticated)
        if user is None or not hasattr(user, 'is_authenticated') or not user.is_authenticated:
            # Free lessons with guest access
            if self.price == 0.0 and self.allow_guest_access:
                return True, "Accessible as guest"
            else:
                return False, "Login required to access this lesson"

        # Admin-Bypass: Admins sehen alle Lessons (Dogfood + Content-Verwaltung)
        if getattr(user, 'is_admin', False):
            return True, "Admin"

        # For authenticated users, check pricing first
        if self.price == 0.0:
            # Free lesson - check prerequisites only
            for prereq in self.get_prerequisites(): # type: ignore
                progress = UserLessonProgress.query.filter_by(
                    user_id=user.id, lesson_id=prereq.id
                ).first()
                if not progress or not progress.is_completed:
                    return False, f"Must complete '{prereq.title}' first"
            return True, "Free lesson"
        
        # Paid lesson - check if user purchased it
        if self.is_purchasable:
            purchase = LessonPurchase.query.filter_by(
                user_id=user.id,
                lesson_id=self.id
            ).first()
            if purchase:
                # User owns the lesson - check prerequisites
                for prereq in self.get_prerequisites(): # type: ignore
                    progress = UserLessonProgress.query.filter_by(
                        user_id=user.id, lesson_id=prereq.id
                    ).first()
                    if not progress or not progress.is_completed:
                        return False, f"Must complete '{prereq.title}' first"
                return True, "Purchased"

            # Check if the lesson is part of a purchased course
            for course in self.courses:
                course_purchase = CoursePurchase.query.filter_by(
                    user_id=user.id,
                    course_id=course.id
                ).first()
                if course_purchase:
                    # User owns the course, so grant access to the lesson
                    for prereq in self.get_prerequisites(): # type: ignore
                        progress = UserLessonProgress.query.filter_by(
                            user_id=user.id, lesson_id=prereq.id
                        ).first()
                        if not progress or not progress.is_completed:
                            return False, f"Must complete '{prereq.title}' first"
                    return True, f"Accessible through course '{course.title}'"
            
            return False, f"Purchase required (CHF {self.price:.2f})"
        
        # Legacy subscription check (for existing premium lessons)
        if self.lesson_type == 'premium' and user.subscription_level != 'premium':
            return False, "Premium subscription required"
        
        # Check prerequisites for other cases
        for prereq in self.get_prerequisites(): # type: ignore
            progress = UserLessonProgress.query.filter_by(
                user_id=user.id, lesson_id=prereq.id
            ).first()
            if not progress or not progress.is_completed:
                return False, f"Must complete '{prereq.title}' first"
        
        return True, "Accessible"

    @property
    def pages(self):
        """Groups content items by page number for rendering and includes page metadata."""
        from collections import defaultdict
        from typing import DefaultDict, List, Dict, Any, Optional

        if not self.content_items:
            return []

        pages_dict: DefaultDict[int, Dict[str, Any]] = defaultdict(lambda: {'content': [], 'metadata': None})
        
        # Create a lookup for page metadata
        metadata_lookup = {pm.page_number: pm for pm in self.pages_metadata}

        # Sort all content items first by page, then by their order within the page
        sorted_content = sorted(self.content_items, key=lambda c: (c.page_number, c.order_index))
        
        for item in sorted_content:
            pages_dict[item.page_number]['content'].append(item)
        
        # Add metadata to each page
        for p_num, page_data in pages_dict.items():
            page_data['metadata'] = metadata_lookup.get(p_num)

        # Return a list of page objects, sorted by page number
        return [pages_dict[p_num] for p_num in sorted(pages_dict.keys())]

    def get_background_url(self):
        """Get URL for background image, handling GCS if enabled"""
        from flask import url_for, current_app
        
        # If we have a path, try to resolve it
        if self.background_image_path:
            # Check if GCS is enabled
            bucket_name = current_app.config.get('GCS_BUCKET_NAME')
            if bucket_name:
                # Remove leading slashes if any
                clean_path = self.background_image_path.lstrip('/')
                return f"https://storage.googleapis.com/{bucket_name}/{clean_path}"
            
            # Fallback to local serving
            return url_for('routes.uploaded_file', filename=self.background_image_path)
            
        # Fallback to the URL field if path is not set
        return self.background_image_url

    def get_thumbnail_url(self):
        """Get URL for thumbnail, handling GCS if enabled"""
        from flask import url_for, current_app
        
        if self.thumbnail_url:
            if self.thumbnail_url.startswith('http'):
                return self.thumbnail_url
            
            # Check if GCS is enabled
            bucket_name = current_app.config.get('GCS_BUCKET_NAME')
            if bucket_name:
                clean_path = self.thumbnail_url.lstrip('/')
                return f"https://storage.googleapis.com/{bucket_name}/{clean_path}"
            
            # Fallback to local serving
            return url_for('routes.uploaded_file', filename=self.thumbnail_url)
            
        return None

class LessonPrerequisite(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lesson_id: Mapped[int] = mapped_column(Integer, ForeignKey('lesson.id'), nullable=False)
    prerequisite_lesson_id: Mapped[int] = mapped_column(Integer, ForeignKey('lesson.id'), nullable=False)
    
    prerequisite_lesson: Mapped["Lesson"] = relationship(foreign_keys=[prerequisite_lesson_id], overlaps="required_by")
    
    __table_args__ = (db.UniqueConstraint('lesson_id', 'prerequisite_lesson_id'),)
    
    def __repr__(self):
        return f'<LessonPrerequisite {self.lesson_id} requires {self.prerequisite_lesson_id}>'

class LessonPage(db.Model):
    __allow_unmapped__ = True
    id = db.Column(db.Integer, primary_key=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)
    page_number = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text, nullable=True)
    page_type = db.Column(db.String(20), default='normal', nullable=False)  # 'normal' or 'quiz_carousel'

    __table_args__ = (db.UniqueConstraint('lesson_id', 'page_number'),)

    def __repr__(self):
        return f'<LessonPage {self.title} for lesson {self.lesson_id}>'

class LessonContent(db.Model):
    __allow_unmapped__ = True
    id = db.Column(db.Integer, primary_key=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)
    content_type = db.Column(db.String(20), nullable=False)  # 'kana', 'kanji', 'vocabulary', 'grammar', 'text', 'image', 'video', 'audio'
    content_id = db.Column(db.Integer)  # NULL for multimedia content
    title = db.Column(db.String(200))  # for multimedia content
    content_text = db.Column(db.Text)  # for text content
    media_url = db.Column(db.String(255))  # for multimedia content
    order_index = db.Column(db.Integer, default=0)  # order within the lesson
    page_number = db.Column(db.Integer, default=1, nullable=False)  # Add page number
    is_optional = db.Column(db.Boolean, default=False)  # whether this content is optional
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # File-related fields
    file_path = db.Column(db.String(500))  # Relative path to uploaded file
    file_size = db.Column(db.Integer)      # File size in bytes
    file_type = db.Column(db.String(50))   # MIME type
    original_filename = db.Column(db.String(255))  # Original filename

    # Interactive content fields
    is_interactive = db.Column(db.Boolean, default=False)
    quiz_type = db.Column(db.String(50), default='standard') # 'standard', 'adaptive'
    max_attempts = db.Column(db.Integer, default=3)
    passing_score = db.Column(db.Integer, default=70)  # Percentage
    
    # AI generation tracking fields
    generated_by_ai = db.Column(db.Boolean, default=False, nullable=False)
    ai_generation_details = db.Column(db.JSON, nullable=True)
    
    # Relationships
    quiz_questions = db.relationship('QuizQuestion', backref='content', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<LessonContent {self.content_type} in lesson {self.lesson_id}>'
    
    def get_file_url(self):
        """Get URL for accessing uploaded file"""
        from flask import url_for
        if self.file_path:
            # If it's a full URL (already migrated or external), return it
            if self.file_path.startswith('http'):
                return self.file_path
            
            # If it's a relative path, construct the GCS URL
            # Assuming the file_path stored in DB is relative to 'uploads/'
            # e.g. 'lessons/image/lesson_1/file.jpg'
            
            # Check if GCS is enabled (bucket name is set)
            from flask import current_app
            bucket_name = current_app.config.get('GCS_BUCKET_NAME')
            if bucket_name:
                # Remove leading slashes if any
                clean_path = self.file_path.lstrip('/')
                return f"https://storage.googleapis.com/{bucket_name}/{clean_path}"
            
            # Fallback to local serving (for development if GCS not set)
            return url_for('routes.uploaded_file', filename=self.file_path)
        return self.media_url  # Fallback to URL-based media
    
    def delete_file(self):
        """Delete associated file from filesystem"""
        if self.file_path:
            from flask import current_app
            import os
            file_full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], self.file_path)
            try:
                if os.path.exists(file_full_path):
                    os.remove(file_full_path)
                    current_app.logger.info(f"Successfully deleted file: {file_full_path}")
                return True # File deleted or did not exist
            except OSError as e: # D1
                current_app.logger.error(f"Error deleting file {file_full_path} for LessonContent {self.id}: {e}")
                return False # Deletion failed
    
    def get_content_data(self):
        """Get the actual content data based on content_type and content_id"""
        if self.content_type == 'kana' and self.content_id:
            return Kana.query.get(self.content_id)
        elif self.content_type == 'kanji' and self.content_id:
            return Kanji.query.get(self.content_id)
        elif self.content_type == 'vocabulary' and self.content_id:
            return Vocabulary.query.get(self.content_id)
        elif self.content_type == 'grammar' and self.content_id:
            return Grammar.query.get(self.content_id)
        elif self.content_type in ['text', 'image', 'video', 'audio']:
            return {
                'title': self.title,
                'content_text': self.content_text,
                'media_url': self.get_file_url() if self.file_path else self.media_url,
                'file_path': self.file_path,
                'file_size': self.file_size,
                'original_filename': self.original_filename
            }
        return None

class QuizQuestion(db.Model):
    __allow_unmapped__ = True
    id = db.Column(db.Integer, primary_key=True)
    lesson_content_id = db.Column(db.Integer, db.ForeignKey('lesson_content.id'), nullable=False)
    question_type = db.Column(db.String(50), nullable=False)  # 'multiple_choice', 'fill_blank', 'true_false', 'matching'
    question_text = db.Column(db.Text, nullable=False)
    explanation = db.Column(db.Text)  # Explanation for the answer
    hint = db.Column(db.Text) # Progressive hint
    difficulty_level = db.Column(db.Integer, default=1) # 1-5 for adaptive quizzes
    points = db.Column(db.Integer, default=1)
    order_index = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    options = db.relationship('QuizOption', backref='question', lazy=True, cascade='all, delete-orphan')
    user_answers = db.relationship('UserQuizAnswer', backref='question', lazy=True, cascade='all, delete-orphan')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class QuizOption(db.Model):
    __allow_unmapped__ = True
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('quiz_question.id'), nullable=False)
    option_text = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    order_index = db.Column(db.Integer, default=0)
    feedback = db.Column(db.Text)  # Specific feedback for this option

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class UserQuizAnswer(db.Model):
    __allow_unmapped__ = True
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('quiz_question.id'), nullable=False)
    selected_option_id = db.Column(db.Integer, db.ForeignKey('quiz_option.id'))
    text_answer = db.Column(db.Text)  # For fill-in-the-blank questions
    is_correct = db.Column(db.Boolean, default=False)
    answered_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    attempts = db.Column(db.Integer, default=0, nullable=False)

    __table_args__ = (db.UniqueConstraint('user_id', 'question_id'),)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class UserLessonProgress(db.Model):
    __allow_unmapped__ = True
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    is_completed = db.Column(db.Boolean, default=False)
    progress_percentage = db.Column(db.Integer, default=0)
    time_spent = db.Column(db.Integer, default=0)
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow)
    content_progress = db.Column(db.Text)
    
    lesson: Mapped['Lesson'] = relationship(foreign_keys=[lesson_id], overlaps="user_progress")

    __table_args__ = (db.UniqueConstraint('user_id', 'lesson_id'),)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<UserLessonProgress user:{self.user_id} lesson:{self.lesson_id}>'
    
    def get_content_progress(self):
        """Get content progress as dictionary"""
        if self.content_progress:
            return json.loads(self.content_progress)
        return {}
    
    def set_content_progress(self, progress_dict):
        """Set content progress from dictionary"""
        self.content_progress = json.dumps(progress_dict)
    
    def mark_content_completed(self, content_id):
        """Mark a specific content item as completed"""
        progress = self.get_content_progress()
        progress[str(content_id)] = True
        self.set_content_progress(progress)
        self.update_progress_percentage()
    
    def update_progress_percentage(self):
        """Update overall progress percentage based on completed content"""
        total_content = len(self.lesson.content_items) # type: ignore
        if total_content == 0:
            self.progress_percentage = 100
            return
        
        completed_content = len([k for k, v in self.get_content_progress().items() if v])
        self.progress_percentage = int((completed_content / total_content) * 100)
        
        if self.progress_percentage == 100 and not self.is_completed:
            self.is_completed = True
            self.completed_at = datetime.utcnow()

    def reset(self):
        """Reset the progress for this lesson."""
        self.completed_at = None
        self.is_completed = False
        self.progress_percentage = 0
        self.time_spent = 0
        self.content_progress = json.dumps({})
        
        # Delete all quiz answers for this lesson for the user
        content_ids = [content.id for content in self.lesson.content_items if content.is_interactive]
        if content_ids:
            question_ids = [q.id for q in QuizQuestion.query.filter(QuizQuestion.lesson_content_id.in_(content_ids)).all()]
            if question_ids:
                UserQuizAnswer.query.filter(
                    UserQuizAnswer.user_id == self.user_id,
                    UserQuizAnswer.question_id.in_(question_ids)
                ).delete(synchronize_session=False)

class LessonPurchase(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.id'), nullable=False)
    lesson_id: Mapped[int] = mapped_column(Integer, ForeignKey('lesson.id', ondelete='RESTRICT'), nullable=False)
    price_paid: Mapped[float] = mapped_column(db.Float, nullable=False)
    purchased_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    provider_transaction_id: Mapped[int] = mapped_column(BigInteger, nullable=True, index=True)
    transaction_state: Mapped[str] = mapped_column(String(50), nullable=True)

    # Relationships
    user: Mapped['User'] = relationship('User', backref='lesson_purchases')
    # Hinweis: ORM-Cascade entfernt — DB-FK ist RESTRICT, Loeschungen werden geblockt.
    lesson: Mapped['Lesson'] = relationship('Lesson', backref=db.backref('purchases'))

    __table_args__ = (db.UniqueConstraint('user_id', 'lesson_id'),)

    def __repr__(self):
        return f'<LessonPurchase user:{self.user_id} lesson:{self.lesson_id} price:{self.price_paid}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

course_lessons = Table('course_lessons', db.metadata,
    Column('course_id', Integer, ForeignKey('course.id'), primary_key=True),
    Column('lesson_id', Integer, ForeignKey('lesson.id'), primary_key=True)
)

class Course(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    background_image_url: Mapped[str] = mapped_column(String(255), nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Pricing fields
    price: Mapped[float] = mapped_column(db.Float, nullable=False, default=0.0)
    is_purchasable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    
    lessons: Mapped[List['Lesson']] = relationship('Lesson', secondary=course_lessons, lazy='subquery',
                              back_populates='courses')

    def __repr__(self):
        return f'<Course {self.title}>'

class CoursePurchase(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.id'), nullable=False)
    course_id: Mapped[int] = mapped_column(Integer, ForeignKey('course.id', ondelete='RESTRICT'), nullable=False)
    price_paid: Mapped[float] = mapped_column(db.Float, nullable=False)
    purchased_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    provider_transaction_id: Mapped[int] = mapped_column(BigInteger, nullable=True, index=True)
    transaction_state: Mapped[str] = mapped_column(String(50), nullable=True)

    # Hinweis: ORM-Cascade entfernt — DB-FK ist RESTRICT, Loeschungen werden geblockt.
    course: Mapped['Course'] = relationship('Course', backref=db.backref('purchases'))

    __table_args__ = (db.UniqueConstraint('user_id', 'course_id'),)

    def __repr__(self):
        return f'<CoursePurchase user:{self.user_id} course:{self.course_id} price:{self.price_paid}>'


class CardReviewState(db.Model):
    """SRS-Zustand pro User + Content-Item (FSRS-Algorithmus)."""
    __tablename__ = 'card_review_state'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    content_id = db.Column(db.Integer, db.ForeignKey('lesson_content.id'), nullable=False)

    # FSRS Card State (kompletter State als JSON via Card.to_json())
    fsrs_card_state = db.Column(db.Text, nullable=False)

    # Denormalisierte Felder fuer Queries
    due_date = db.Column(db.DateTime, nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default='new')
    # Werte: 'new', 'learning', 'review', 'relearning', 'suspended'

    # Statistiken
    reps = db.Column(db.Integer, default=0, nullable=False)
    lapses = db.Column(db.Integer, default=0, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Beziehungen
    user = db.relationship('User', backref=db.backref('card_states', lazy='dynamic'))
    content = db.relationship('LessonContent', backref=db.backref('review_states', lazy='dynamic'))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'content_id', name='uq_user_content_review'),
        db.Index('ix_card_review_due', 'user_id', 'due_date', 'status'),
    )

    def __repr__(self):
        return f'<CardReviewState user:{self.user_id} content:{self.content_id} status:{self.status}>'


class ReviewLog(db.Model):
    """Protokoll jeder Bewertung — Basis fuer FSRS-Optimizer."""
    __tablename__ = 'review_log'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    content_id = db.Column(db.Integer, db.ForeignKey('lesson_content.id'), nullable=False)

    rating = db.Column(db.Integer, nullable=False)  # 1=Again, 2=Hard, 3=Good, 4=Easy
    reviewed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    time_taken_ms = db.Column(db.Integer)

    # FSRS ReviewLog State (fuer Optimizer)
    fsrs_review_log = db.Column(db.Text)

    # Denormalisiert fuer Statistiken
    scheduled_days = db.Column(db.Integer)
    elapsed_days = db.Column(db.Integer)

    # Beziehungen
    user = db.relationship('User', backref=db.backref('review_logs', lazy='dynamic'))
    content = db.relationship('LessonContent')

    def __repr__(self):
        return f'<ReviewLog user:{self.user_id} content:{self.content_id} rating:{self.rating}>'


class UserSRSSettings(db.Model):
    """Persoenliche SRS-Einstellungen pro User."""
    __tablename__ = 'user_srs_settings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)

    desired_retention = db.Column(db.Float, default=0.9)
    daily_new_cards = db.Column(db.Integer, default=20)
    daily_review_limit = db.Column(db.Integer, default=100)

    # FSRS Optimizer Parameters (21 Floats als JSON, nach ~1000 Reviews)
    fsrs_parameters = db.Column(db.Text)

    # Phase 6: Streak-Freeze + Leech-Schwelle
    streak_freezes_available = db.Column(db.Integer, default=1, nullable=False, server_default='1')
    last_freeze_replenish = db.Column(db.Date, nullable=True)
    leech_threshold = db.Column(db.Integer, default=8, nullable=False, server_default='8')

    user = db.relationship('User', backref=db.backref('srs_settings', uselist=False))

    def __repr__(self):
        return f'<UserSRSSettings user:{self.user_id} retention:{self.desired_retention}>'


class UserAchievement(db.Model):
    """Freigeschaltete Achievements pro User."""
    __tablename__ = 'user_achievement'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    achievement_key = db.Column(db.String(50), nullable=False)
    unlocked_at = db.Column(db.DateTime, default=datetime.utcnow)
    notified = db.Column(db.Boolean, default=False, nullable=False)

    user = db.relationship('User', backref=db.backref('achievements', lazy='dynamic'))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'achievement_key', name='uq_user_achievement'),
    )

    def __repr__(self):
        return f'<UserAchievement user:{self.user_id} key:{self.achievement_key}>'


class DailyReviewAggregate(db.Model):
    """Taeglich aggregierte Review-Statistiken (Heatmap, Performance)."""
    __tablename__ = 'daily_review_aggregate'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    review_date = db.Column(db.Date, nullable=False, index=True)

    total_reviews = db.Column(db.Integer, default=0, nullable=False)
    correct_reviews = db.Column(db.Integer, default=0, nullable=False)
    again_count = db.Column(db.Integer, default=0, nullable=False)
    hard_count = db.Column(db.Integer, default=0, nullable=False)
    good_count = db.Column(db.Integer, default=0, nullable=False)
    easy_count = db.Column(db.Integer, default=0, nullable=False)
    total_time_ms = db.Column(db.BigInteger, default=0, nullable=False)
    xp_earned = db.Column(db.Integer, default=0, nullable=False)
    new_cards_learned = db.Column(db.Integer, default=0, nullable=False)
    cards_leveled_up = db.Column(db.Integer, default=0, nullable=False)
    cards_leveled_down = db.Column(db.Integer, default=0, nullable=False)

    user = db.relationship('User', backref=db.backref('daily_aggregates', lazy='dynamic'))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'review_date', name='uq_user_daily_agg'),
    )

    def __repr__(self):
        return f'<DailyReviewAggregate user:{self.user_id} date:{self.review_date}>'


class PaymentTransaction(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Use BigInteger for the transaction_id as per API documentation
    transaction_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.id'), nullable=True)
    item_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'lesson' or 'course'
    item_id: Mapped[int] = mapped_column(Integer, nullable=False)
    amount: Mapped[float] = mapped_column(db.Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default='CHF')
    state: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # Use JSON for efficient querying of webhook data
    webhook_data: Mapped[dict] = mapped_column(JSON, nullable=True)
    transaction_metadata: Mapped[dict] = mapped_column(JSON, nullable=True)

    def __repr__(self):
        return f'<PaymentTransaction {self.transaction_id} - {self.state}>'


# SQLAlchemy event listeners to automatically maintain lesson type consistency
@event.listens_for(Lesson, 'before_insert')
@event.listens_for(Lesson, 'before_update')
def update_lesson_type_on_price_change(mapper, connection, target):
    """
    Automatically set lesson_type based on price before insert/update operations.
    This ensures consistency between lesson_type and pricing.
    
    - lesson_type = "free" when price = 0.00
    - lesson_type = "paid" when price > 0.00
    """
    if target.price == 0.0:
        target.lesson_type = "free"
    else:
        target.lesson_type = "paid"
