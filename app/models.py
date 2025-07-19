# app/models.py
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json
from typing import List
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Table, Column, Integer, String, Text, Boolean, DateTime, JSON

class User(UserMixin, db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    subscription_level: Mapped[str] = mapped_column(String(50), default='free')
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    lesson_progress: Mapped[List['UserLessonProgress']] = relationship('UserLessonProgress', backref='user', lazy=True, cascade='all, delete-orphan')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

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
    meaning = db.Column(db.Text, nullable=False)
    jlpt_level = db.Column(db.Integer, nullable=True)
    example_sentence_japanese = db.Column(db.Text, nullable=True)
    example_sentence_english = db.Column(db.Text, nullable=True)
    audio_url = db.Column(db.String(255), nullable=True)
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
    structure = db.Column(db.String(255), nullable=True)
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
    
    # Relationship
    lessons = db.relationship('Lesson', backref='category', lazy=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<LessonCategory {self.name}>'

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
            else:
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
    lesson_id: Mapped[int] = mapped_column(Integer, ForeignKey('lesson.id'), nullable=False)
    price_paid: Mapped[float] = mapped_column(db.Float, nullable=False)
    purchased_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    stripe_payment_intent_id: Mapped[str] = mapped_column(String(100), nullable=True)  # For future Stripe integration
    
    # Relationships
    user: Mapped['User'] = relationship('User', backref='lesson_purchases')
    lesson: Mapped['Lesson'] = relationship('Lesson', backref='purchases')
    
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
    
    lessons: Mapped[List['Lesson']] = relationship('Lesson', secondary=course_lessons, lazy='subquery',
                              back_populates='courses')

    def __repr__(self):
        return f'<Course {self.title}>'
