from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
# Determine the absolute path for the database file
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'japanese_learning.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_very_secret_key_for_flask_sessions' # Replace in production

db = SQLAlchemy(app)

# --- Models ---

class Kana(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    character = db.Column(db.String(5), nullable=False, unique=True)
    romanization = db.Column(db.String(10), nullable=False)
    type = db.Column(db.String(10), nullable=False)  # 'hiragana' or 'katakana'
    # For stroke order, we might store a link to an image/SVG or a JSON description of strokes
    stroke_order_info = db.Column(db.String(255), nullable=True)
    example_sound_url = db.Column(db.String(255), nullable=True) # URL to an audio file

    def __repr__(self):
        return f'<Kana {self.character}>'

class Kanji(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    character = db.Column(db.String(5), nullable=False, unique=True)
    meaning = db.Column(db.Text, nullable=False) # Comma-separated meanings
    onyomi = db.Column(db.String(100), nullable=True) # Comma-separated On'yomi readings
    kunyomi = db.Column(db.String(100), nullable=True) # Comma-separated Kun'yomi readings
    jlpt_level = db.Column(db.Integer, nullable=True) # N5, N4, N3, N2, N1 -> 5, 4, 3, 2, 1
    # For stroke order, similar to Kana
    stroke_order_info = db.Column(db.String(255), nullable=True)
    radical = db.Column(db.String(10), nullable=True)
    stroke_count = db.Column(db.Integer, nullable=True)

    def __repr__(self):
        return f'<Kanji {self.character}>'

class Vocabulary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(100), nullable=False, unique=True)
    reading = db.Column(db.String(100), nullable=False) # Hiragana/Katakana reading
    meaning = db.Column(db.Text, nullable=False) # Comma-separated meanings
    jlpt_level = db.Column(db.Integer, nullable=True)
    example_sentence_japanese = db.Column(db.Text, nullable=True)
    example_sentence_english = db.Column(db.Text, nullable=True)
    audio_url = db.Column(db.String(255), nullable=True) # URL to pronunciation

    # Potential relationship if we want to link vocab to specific kanji it uses
    # kanji_components = db.relationship('Kanji', secondary=vocab_kanji_association, backref='vocabulary_items')

    def __repr__(self):
        return f'<Vocabulary {self.word}>'

class Grammar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, unique=True) # e.g., "Expressing ability with ことができる"
    explanation = db.Column(db.Text, nullable=False)
    structure = db.Column(db.String(255), nullable=True) # e.g., "Verb (dictionary form) + ことができる"
    jlpt_level = db.Column(db.Integer, nullable=True)
    # Example sentences would be crucial. Could be a JSON list or a separate related table if more structure is needed.
    example_sentences = db.Column(db.Text, nullable=True) # Store as JSON string: [{"ja": "...", "en": "..."}, ...]

    def __repr__(self):
        return f'<Grammar {self.title}>'

# --- Helper for JSON serialization ---
def model_to_dict(model_instance):
    """Converts a SQLAlchemy model instance to a dictionary, excluding SQLAlchemy internal state."""
    d = {}
    for column in model_instance.__table__.columns:
        d[column.name] = getattr(model_instance, column.name)
    return d

# --- Routes ---

# Basic HTML routes for admin panel (will be more structured later)
from flask import render_template, request, redirect, url_for, jsonify, flash, session # Added session
from functools import wraps # For decorators

# --- Config for Basic Auth (Hardcoded - NOT FOR PRODUCTION) ---
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password123" # Reasonably "secure" for local dev


# --- Auth Decorator ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash("Please log in to access this page.", "error")
            # Save the current URL to redirect back after login
            return redirect(url_for('admin_login', next=request.url_rule.endpoint if request.url_rule else url_for('admin_index')))
        return f(*args, **kwargs)
    return decorated_function

# --- Admin Panel HTML Routes ---
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            session['admin_username'] = username
            flash("Logged in successfully!", "success")
            next_url_rule = request.args.get('next')
            if next_url_rule:
                 # Check if next_url_rule is a valid endpoint name, otherwise redirect to admin_index
                try:
                    # Check if next_url_rule is an endpoint that exists.
                    # This is a simple check; more robust validation might be needed
                    # if users could somehow manipulate the 'next' parameter to non-admin routes.
                    # However, since all admin routes are protected by @login_required,
                    # this should be reasonably safe.
                    if next_url_rule in app.view_functions:
                         return redirect(url_for(next_url_rule))
                    else: # Fallback if it's not a direct endpoint name (e.g. full path was passed)
                        # This part is tricky if the 'next' param was a full URL.
                        # For simplicity, we'll just redirect to admin_index if it's not a known endpoint.
                        # A more robust solution would parse the URL and check if it's safe.
                        return redirect(url_for('admin_index'))

                except Exception: # Werkzeug BuildError if endpoint not found
                     return redirect(url_for('admin_index'))

            return redirect(url_for('admin_index'))
        else:
            flash("Invalid username or password.", "error")
    return render_template('admin/login.html')

@app.route('/admin/logout')
@login_required # Good practice to ensure only logged-in users can log out
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    flash("You have been logged out.", "success")
    return redirect(url_for('admin_login'))


@app.route('/admin/')
@login_required
def admin_index():
    return render_template('admin/admin_index.html')

@app.route('/admin/manage/kana')
@login_required
def admin_manage_kana():
    return render_template('admin/manage_kana.html')

@app.route('/admin/manage/kanji')
@login_required
def admin_manage_kanji():
    return render_template('admin/manage_kanji.html')

@app.route('/admin/manage/vocabulary')
@login_required
def admin_manage_vocabulary():
    return render_template('admin/manage_vocabulary.html')

@app.route('/admin/manage/grammar')
@login_required
def admin_manage_grammar():
    return render_template('admin/manage_grammar.html')

# --- API Routes (JSON) ---
# Note: The API routes for list_X (e.g. list_kana) were GET /admin/kana.
# To avoid conflict with potential future HTML display pages at those URLs,
# and to clearly distinguish API endpoints, I'll prefix them with /api.
# Example: GET /api/admin/kana for listing, POST /api/admin/kana/new for creating.

# == KANA CRUD API ==
@app.route('/api/admin/kana', methods=['GET']) # Changed from /admin/kana
def list_kana():
    items = Kana.query.all()
    return jsonify([model_to_dict(item) for item in items])

@app.route('/api/admin/kana/new', methods=['POST']) # Changed from /admin/kana/new
def create_kana():
    data = request.json
    if not data or not data.get('character') or not data.get('romanization') or not data.get('type'):
        return jsonify({"error": "Missing required fields"}), 400

    existing_kana = Kana.query.filter_by(character=data['character']).first()
    if existing_kana:
        return jsonify({"error": "Kana character already exists"}), 400

    new_item = Kana(
        character=data['character'],
        romanization=data['romanization'],
        type=data['type'],
        stroke_order_info=data.get('stroke_order_info'),
        example_sound_url=data.get('example_sound_url')
    )
    db.session.add(new_item)
    db.session.commit()
    return jsonify(model_to_dict(new_item)), 201

@app.route('/api/admin/kana/<int:item_id>', methods=['GET']) # Changed
def get_kana(item_id):
    item = Kana.query.get_or_404(item_id)
    return jsonify(model_to_dict(item))

@app.route('/api/admin/kana/<int:item_id>/edit', methods=['PUT', 'PATCH']) # Changed
def update_kana(item_id):
    item = Kana.query.get_or_404(item_id)
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    item.character = data.get('character', item.character)
    item.romanization = data.get('romanization', item.romanization)
    item.type = data.get('type', item.type)
    item.stroke_order_info = data.get('stroke_order_info', item.stroke_order_info)
    item.example_sound_url = data.get('example_sound_url', item.example_sound_url)

    db.session.commit()
    return jsonify(model_to_dict(item))

@app.route('/api/admin/kana/<int:item_id>/delete', methods=['DELETE']) # Changed
def delete_kana(item_id):
    item = Kana.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Kana deleted successfully"}), 200


# == KANJI CRUD API ==
@app.route('/api/admin/kanji', methods=['GET']) # Changed
def list_kanji():
    items = Kanji.query.all()
    return jsonify([model_to_dict(item) for item in items])

@app.route('/api/admin/kanji/new', methods=['POST']) # Changed
def create_kanji():
    data = request.json
    if not data or not data.get('character') or not data.get('meaning'):
        return jsonify({"error": "Missing required fields: character, meaning"}), 400

    existing_kanji = Kanji.query.filter_by(character=data['character']).first()
    if existing_kanji:
        return jsonify({"error": "Kanji character already exists"}), 400

    new_item = Kanji(
        character=data['character'],
        meaning=data['meaning'],
        onyomi=data.get('onyomi'),
        kunyomi=data.get('kunyomi'),
        jlpt_level=data.get('jlpt_level'),
        stroke_order_info=data.get('stroke_order_info'),
        radical=data.get('radical'),
        stroke_count=data.get('stroke_count')
    )
    db.session.add(new_item)
    db.session.commit()
    return jsonify(model_to_dict(new_item)), 201

@app.route('/api/admin/kanji/<int:item_id>', methods=['GET']) # Changed
def get_kanji(item_id):
    item = Kanji.query.get_or_404(item_id)
    return jsonify(model_to_dict(item))

@app.route('/api/admin/kanji/<int:item_id>/edit', methods=['PUT', 'PATCH']) # Changed
def update_kanji(item_id):
    item = Kanji.query.get_or_404(item_id)
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    item.character = data.get('character', item.character)
    item.meaning = data.get('meaning', item.meaning)
    item.onyomi = data.get('onyomi', item.onyomi)
    item.kunyomi = data.get('kunyomi', item.kunyomi)
    item.jlpt_level = data.get('jlpt_level', item.jlpt_level)
    item.stroke_order_info = data.get('stroke_order_info', item.stroke_order_info)
    item.radical = data.get('radical', item.radical)
    item.stroke_count = data.get('stroke_count', item.stroke_count)

    db.session.commit()
    return jsonify(model_to_dict(item))

@app.route('/api/admin/kanji/<int:item_id>/delete', methods=['DELETE']) # Changed
def delete_kanji(item_id):
    item = Kanji.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Kanji deleted successfully"}), 200


# == VOCABULARY CRUD API ==
@app.route('/api/admin/vocabulary', methods=['GET']) # Changed
def list_vocabulary():
    items = Vocabulary.query.all()
    return jsonify([model_to_dict(item) for item in items])

@app.route('/api/admin/vocabulary/new', methods=['POST']) # Changed
def create_vocabulary():
    data = request.json
    if not data or not data.get('word') or not data.get('reading') or not data.get('meaning'):
        return jsonify({"error": "Missing required fields: word, reading, meaning"}), 400

    existing_vocab = Vocabulary.query.filter_by(word=data['word']).first()
    if existing_vocab:
        return jsonify({"error": "Vocabulary word already exists"}), 400

    new_item = Vocabulary(
        word=data['word'],
        reading=data['reading'],
        meaning=data['meaning'],
        jlpt_level=data.get('jlpt_level'),
        example_sentence_japanese=data.get('example_sentence_japanese'),
        example_sentence_english=data.get('example_sentence_english'),
        audio_url=data.get('audio_url')
    )
    db.session.add(new_item)
    db.session.commit()
    return jsonify(model_to_dict(new_item)), 201

@app.route('/api/admin/vocabulary/<int:item_id>', methods=['GET']) # Changed
def get_vocabulary(item_id):
    item = Vocabulary.query.get_or_404(item_id)
    return jsonify(model_to_dict(item))

@app.route('/api/admin/vocabulary/<int:item_id>/edit', methods=['PUT', 'PATCH']) # Changed
def update_vocabulary(item_id):
    item = Vocabulary.query.get_or_404(item_id)
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    item.word = data.get('word', item.word)
    item.reading = data.get('reading', item.reading)
    item.meaning = data.get('meaning', item.meaning)
    item.jlpt_level = data.get('jlpt_level', item.jlpt_level)
    item.example_sentence_japanese = data.get('example_sentence_japanese', item.example_sentence_japanese)
    item.example_sentence_english = data.get('example_sentence_english', item.example_sentence_english)
    item.audio_url = data.get('audio_url', item.audio_url)

    db.session.commit()
    return jsonify(model_to_dict(item))

@app.route('/api/admin/vocabulary/<int:item_id>/delete', methods=['DELETE']) # Changed
def delete_vocabulary(item_id):
    item = Vocabulary.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Vocabulary item deleted successfully"}), 200


# == GRAMMAR CRUD API ==
@app.route('/api/admin/grammar', methods=['GET']) # Changed
def list_grammar():
    items = Grammar.query.all()
    return jsonify([model_to_dict(item) for item in items])

@app.route('/api/admin/grammar/new', methods=['POST']) # Changed
def create_grammar():
    data = request.json
    if not data or not data.get('title') or not data.get('explanation'):
        return jsonify({"error": "Missing required fields: title, explanation"}), 400

    existing_grammar = Grammar.query.filter_by(title=data['title']).first()
    if existing_grammar:
        return jsonify({"error": "Grammar title already exists"}), 400

    new_item = Grammar(
        title=data['title'],
        explanation=data['explanation'],
        structure=data.get('structure'),
        jlpt_level=data.get('jlpt_level'),
        example_sentences=data.get('example_sentences') # Expecting JSON string or will be stored as such
    )
    db.session.add(new_item)
    db.session.commit()
    return jsonify(model_to_dict(new_item)), 201

@app.route('/api/admin/grammar/<int:item_id>', methods=['GET']) # Changed
def get_grammar(item_id):
    item = Grammar.query.get_or_404(item_id)
    return jsonify(model_to_dict(item))

@app.route('/api/admin/grammar/<int:item_id>/edit', methods=['PUT', 'PATCH']) # Changed
def update_grammar(item_id):
    item = Grammar.query.get_or_404(item_id)
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    item.title = data.get('title', item.title)
    item.explanation = data.get('explanation', item.explanation)
    item.structure = data.get('structure', item.structure)
    item.jlpt_level = data.get('jlpt_level', item.jlpt_level)
    item.example_sentences = data.get('example_sentences', item.example_sentences)

    db.session.commit()
    return jsonify(model_to_dict(item))

@app.route('/api/admin/grammar/<int:item_id>/delete', methods=['DELETE']) # Changed
def delete_grammar(item_id):
    item = Grammar.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Grammar point deleted successfully"}), 200

# A simple root route for now - redirect to admin panel
@app.route('/')
def index():
    return redirect(url_for('admin_index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
