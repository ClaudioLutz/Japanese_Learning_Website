# Enhanced lesson system models - to be integrated into app/models.py
from app import db
from datetime import datetime
import json

class LessonCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    color_code = db.Column(db.String(7), default='#007bff')  # hex color for UI
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    lessons = db.relationship('Lesson', backref='category', lazy=True)
    
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
        for prereq in self.get_prerequisites():
            progress = UserLessonProgress.query.filter_by(
                user_id=user.id, lesson_id=prereq.id
            ).first()
            if not progress or not progress.is_completed:
                return False, f"Must complete '{prereq.title}' first"
        
        return True, "Accessible"

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
    is_optional = db.Column(db.Boolean, default=False)  # whether this content is optional
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<LessonContent {self.content_type} in lesson {self.lesson_id}>'
    
    def get_content_data(self):
        """Get the actual content data based on content_type and content_id"""
        if self.content_type == 'kana' and self.content_id:
            from app.models import Kana
            return Kana.query.get(self.content_id)
        elif self.content_type == 'kanji' and self.content_id:
            from app.models import Kanji
            return Kanji.query.get(self.content_id)
        elif self.content_type == 'vocabulary' and self.content_id:
            from app.models import Vocabulary
            return Vocabulary.query.get(self.content_id)
        elif self.content_type == 'grammar' and self.content_id:
            from app.models import Grammar
            return Grammar.query.get(self.content_id)
        elif self.content_type in ['text', 'image', 'video', 'audio']:
            return {
                'title': self.title,
                'content_text': self.content_text,
                'media_url': self.media_url
            }
        return None

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
        total_content = len(self.lesson.content_items)
        if total_content == 0:
            self.progress_percentage = 100
            return
        
        completed_content = len([k for k, v in self.get_content_progress().items() if v])
        self.progress_percentage = int((completed_content / total_content) * 100)
        
        if self.progress_percentage == 100 and not self.is_completed:
            self.is_completed = True
            self.completed_at = datetime.utcnow()

# Add relationship to existing User model (to be added to app/models.py)
# User.lesson_progress = db.relationship('UserLessonProgress', backref='user', lazy=True, cascade='all, delete-orphan')
