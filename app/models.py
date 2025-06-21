# app/models.py
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    # For prototype, a simple string. Can be more complex later.
    subscription_level = db.Column(db.String(50), default='free') # 'free', 'premium'
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

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

    def __repr__(self):
        return f'<Vocabulary {self.word}>'

class Grammar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, unique=True)
    explanation = db.Column(db.Text, nullable=False)
    structure = db.Column(db.String(255), nullable=True)
    jlpt_level = db.Column(db.Integer, nullable=True)
    example_sentences = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<Grammar {self.title}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
