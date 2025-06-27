# app/models.py
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    # For prototype, a simple string. Can be more complex later.
    subscription_level = db.Column(db.String(50), default='free') # 'free', 'premium'
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    # Relationship for lesson progress
    lesson_progress = db.relationship('UserLessonProgress', backref='user', lazy=True, cascade='all, delete-orphan')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Kana(db.Model):
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
    id = db.Column(db.Integer, primary_key=True)
    character = db.Column(db.String(5), nullable=False, unique=True)
    meaning = db.Column(db.Text, nullable=False)
    onyomi = db.Column(db.String(100), nullable=True)
    kunyomi = db.Column(db.String(100), nullable=True)
    jlpt_level = db.Column(db.Integer, nullable=True)
    stroke_order_info = db.Column(db.String(255), nullable=True)
    radical = db.Column(db.String(10), nullable=True)
    stroke_count = db.Column(db.Integer, nullable=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<Kanji {self.character}>'

class Vocabulary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(100), nullable=False, unique=True)
    reading = db.Column(db.String(100), nullable=False)
    meaning = db.Column(db.Text, nullable=False)
    jlpt_level = db.Column(db.Integer, nullable=True)
    example_sentence_japanese = db.Column(db.Text, nullable=True)
    example_sentence_english = db.Column(db.Text, nullable=True)
    audio_url = db.Column(db.String(255), nullable=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<Vocabulary {self.word}>'

class Grammar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, unique=True)
    explanation = db.Column(db.Text, nullable=False)
    structure = db.Column(db.String(255), nullable=True)
    jlpt_level = db.Column(db.Integer, nullable=True)
    example_sentences = db.Column(db.Text, nullable=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<Grammar {self.title}>'

class LessonCategory(db.Model):
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
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    lesson_type = db.Column(db.String(20), nullable=False)  # 'free' or 'premium'
    category_id = db.Column(db.Integer, db.ForeignKey('lesson_category.id'))
    difficulty_level = db.Column(db.Integer)  # 1-5 (beginner to advanced)
    estimated_duration = db.Column(db.Integer)  # minutes
    order_index = db.Column(db.Integer, default=0)  # for lesson ordering within category
    is_published = db.Column(db.Boolean, default=False)
    thumbnail_url = db.Column(db.String(255))  # lesson cover image
    video_intro_url = db.Column(db.String(255))  # optional intro video
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    content_items = db.relationship('LessonContent', backref='lesson', lazy=True, cascade='all, delete-orphan')
    prerequisites = db.relationship('LessonPrerequisite', 
                                  foreign_keys='LessonPrerequisite.lesson_id',
                                  backref='lesson', lazy=True, cascade='all, delete-orphan')
    required_by = db.relationship('LessonPrerequisite',
                                foreign_keys='LessonPrerequisite.prerequisite_lesson_id',
                                backref='prerequisite_lesson', lazy=True)
    user_progress = db.relationship('UserLessonProgress', backref='lesson', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<Lesson {self.title}>'
    
    def get_prerequisites(self):
        """Get list of prerequisite lessons"""
        return [prereq.prerequisite_lesson for prereq in self.prerequisites]
    
    def is_accessible_to_user(self, user):
        """Check if user can access this lesson based on subscription and prerequisites"""
        # Check subscription level
        if self.lesson_type == 'premium' and user.subscription_level != 'premium':
            return False, "Premium subscription required"
        
        # Check prerequisites
        for prereq in self.get_prerequisites(): # type: ignore
            progress = UserLessonProgress.query.filter_by(
                user_id=user.id, lesson_id=prereq.id
            ).first()
            if not progress or not progress.is_completed:
                return False, f"Must complete '{prereq.title}' first"
        
        return True, "Accessible"

    @property
    def pages(self):
        """Groups content items by page number for rendering."""
        from collections import defaultdict
        if not self.content_items:
            return []

        pages_dict = defaultdict(list)
        # Sort all content items first by page, then by their order within the page
        sorted_content = sorted(self.content_items, key=lambda c: (c.page_number, c.order_index))

        for item in sorted_content:
            pages_dict[item.page_number].append(item)

        # Return a list of pages (which are lists of content items), sorted by page number
        return [pages_dict[p_num] for p_num in sorted(pages_dict.keys())]

class LessonPrerequisite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)
    prerequisite_lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)
    
    __table_args__ = (db.UniqueConstraint('lesson_id', 'prerequisite_lesson_id'),)
    
    def __repr__(self):
        return f'<LessonPrerequisite {self.lesson_id} requires {self.prerequisite_lesson_id}>'

class LessonContent(db.Model):
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
    max_attempts = db.Column(db.Integer, default=3)
    passing_score = db.Column(db.Integer, default=70)  # Percentage

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
            except OSError as e: # D1
                current_app.logger.error(f"Error deleting file {file_full_path} for LessonContent {self.id}: {e}")
    
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
    id = db.Column(db.Integer, primary_key=True)
    lesson_content_id = db.Column(db.Integer, db.ForeignKey('lesson_content.id'), nullable=False)
    question_type = db.Column(db.String(50), nullable=False)  # 'multiple_choice', 'fill_blank', 'true_false', 'matching'
    question_text = db.Column(db.Text, nullable=False)
    explanation = db.Column(db.Text)  # Explanation for the answer
    points = db.Column(db.Integer, default=1)
    order_index = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    options = db.relationship('QuizOption', backref='question', lazy=True, cascade='all, delete-orphan')
    user_answers = db.relationship('UserQuizAnswer', backref='question', lazy=True, cascade='all, delete-orphan')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class QuizOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('quiz_question.id'), nullable=False)
    option_text = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    order_index = db.Column(db.Integer, default=0)
    feedback = db.Column(db.Text)  # Specific feedback for this option

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class UserQuizAnswer(db.Model):
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
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    is_completed = db.Column(db.Boolean, default=False)
    progress_percentage = db.Column(db.Integer, default=0)  # 0-100
    time_spent = db.Column(db.Integer, default=0)  # minutes
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Track progress on individual content items
    content_progress = db.Column(db.Text)  # JSON string of content item completion
    
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

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
