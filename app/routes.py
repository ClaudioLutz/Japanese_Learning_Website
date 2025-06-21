# app/routes.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, Kana, Kanji, Vocabulary, Grammar
from app.forms import RegistrationForm, LoginForm
from functools import wraps # For custom decorators

# Helper function for JSON serialization
def model_to_dict(model_instance):
    """Converts a SQLAlchemy model instance to a dictionary."""
    d = {}
    for column in model_instance.__table__.columns:
        d[column.name] = getattr(model_instance, column.name)
    return d

bp = Blueprint('routes', __name__)

# --- Custom Decorators for Content Access ---
def premium_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.subscription_level != 'premium':
            flash('Premium membership required to access this content.', 'warning')
            return redirect(url_for('routes.index')) # Or a subscribe page
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access required.', 'danger')
            return redirect(url_for('routes.index'))
        return f(*args, **kwargs)
    return decorated_function

# --- Public Routes ---
@bp.route('/')
@bp.route('/home')
def index():
    return render_template('index.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('routes.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('routes.login'))
    return render_template('register.html', form=form)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # Redirect based on user role
        if current_user.is_admin:
            return redirect(url_for('routes.admin_index'))
        else:
            return redirect(url_for('routes.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash('Login successful!', 'success')
            # Redirect based on user role if no next page specified
            if not next_page:
                if user.is_admin:
                    return redirect(url_for('routes.admin_index'))
                else:
                    return redirect(url_for('routes.index'))
            return redirect(next_page)
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('routes.index'))

@bp.route('/free_content')
@login_required # Anyone logged in can see this
def free_content():
    return render_template('free_content.html')

# --- Member Routes (Simulated Premium) ---
@bp.route('/premium_content')
@login_required
@premium_required # Requires 'premium' subscription_level
def premium_content():
    return render_template('premium_content.html')

@bp.route('/upgrade_to_premium')
@login_required
def upgrade_to_premium():
    # **PROTOTYPE ONLY**: Manually change subscription for testing
    current_user.subscription_level = 'premium'
    db.session.commit()
    flash('Congratulations! Your account has been upgraded to Premium.', 'success')
    return redirect(url_for('routes.premium_content'))

@bp.route('/downgrade_from_premium')
@login_required
def downgrade_from_premium():
    # **PROTOTYPE ONLY**: Manually change subscription for testing
    current_user.subscription_level = 'free'
    db.session.commit()
    flash('Your account has been downgraded to Free.', 'info')
    return redirect(url_for('routes.free_content'))

# --- Admin Routes ---
@bp.route('/admin')
@login_required
@admin_required
def admin_index():
    return render_template('admin/admin_index.html')

@bp.route('/admin/manage/kana')
@login_required
@admin_required
def admin_manage_kana():
    return render_template('admin/manage_kana.html')

@bp.route('/admin/manage/kanji')
@login_required
@admin_required
def admin_manage_kanji():
    return render_template('admin/manage_kanji.html')

@bp.route('/admin/manage/vocabulary')
@login_required
@admin_required
def admin_manage_vocabulary():
    return render_template('admin/manage_vocabulary.html')

@bp.route('/admin/manage/grammar')
@login_required
@admin_required
def admin_manage_grammar():
    return render_template('admin/manage_grammar.html')

# --- API Routes for Content Management ---

# == KANA CRUD API ==
@bp.route('/api/admin/kana', methods=['GET'])
@login_required
@admin_required
def list_kana():
    items = Kana.query.all()
    return jsonify([model_to_dict(item) for item in items])

@bp.route('/api/admin/kana/new', methods=['POST'])
@login_required
@admin_required
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

@bp.route('/api/admin/kana/<int:item_id>', methods=['GET'])
@login_required
@admin_required
def get_kana(item_id):
    item = Kana.query.get_or_404(item_id)
    return jsonify(model_to_dict(item))

@bp.route('/api/admin/kana/<int:item_id>/edit', methods=['PUT', 'PATCH'])
@login_required
@admin_required
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

@bp.route('/api/admin/kana/<int:item_id>/delete', methods=['DELETE'])
@login_required
@admin_required
def delete_kana(item_id):
    item = Kana.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Kana deleted successfully"}), 200

# == KANJI CRUD API ==
@bp.route('/api/admin/kanji', methods=['GET'])
@login_required
@admin_required
def list_kanji():
    items = Kanji.query.all()
    return jsonify([model_to_dict(item) for item in items])

@bp.route('/api/admin/kanji/new', methods=['POST'])
@login_required
@admin_required
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

@bp.route('/api/admin/kanji/<int:item_id>', methods=['GET'])
@login_required
@admin_required
def get_kanji(item_id):
    item = Kanji.query.get_or_404(item_id)
    return jsonify(model_to_dict(item))

@bp.route('/api/admin/kanji/<int:item_id>/edit', methods=['PUT', 'PATCH'])
@login_required
@admin_required
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

@bp.route('/api/admin/kanji/<int:item_id>/delete', methods=['DELETE'])
@login_required
@admin_required
def delete_kanji(item_id):
    item = Kanji.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Kanji deleted successfully"}), 200

# == VOCABULARY CRUD API ==
@bp.route('/api/admin/vocabulary', methods=['GET'])
@login_required
@admin_required
def list_vocabulary():
    items = Vocabulary.query.all()
    return jsonify([model_to_dict(item) for item in items])

@bp.route('/api/admin/vocabulary/new', methods=['POST'])
@login_required
@admin_required
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

@bp.route('/api/admin/vocabulary/<int:item_id>', methods=['GET'])
@login_required
@admin_required
def get_vocabulary(item_id):
    item = Vocabulary.query.get_or_404(item_id)
    return jsonify(model_to_dict(item))

@bp.route('/api/admin/vocabulary/<int:item_id>/edit', methods=['PUT', 'PATCH'])
@login_required
@admin_required
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

@bp.route('/api/admin/vocabulary/<int:item_id>/delete', methods=['DELETE'])
@login_required
@admin_required
def delete_vocabulary(item_id):
    item = Vocabulary.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Vocabulary item deleted successfully"}), 200

# == GRAMMAR CRUD API ==
@bp.route('/api/admin/grammar', methods=['GET'])
@login_required
@admin_required
def list_grammar():
    items = Grammar.query.all()
    return jsonify([model_to_dict(item) for item in items])

@bp.route('/api/admin/grammar/new', methods=['POST'])
@login_required
@admin_required
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
        example_sentences=data.get('example_sentences')
    )
    db.session.add(new_item)
    db.session.commit()
    return jsonify(model_to_dict(new_item)), 201

@bp.route('/api/admin/grammar/<int:item_id>', methods=['GET'])
@login_required
@admin_required
def get_grammar(item_id):
    item = Grammar.query.get_or_404(item_id)
    return jsonify(model_to_dict(item))

@bp.route('/api/admin/grammar/<int:item_id>/edit', methods=['PUT', 'PATCH'])
@login_required
@admin_required
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

@bp.route('/api/admin/grammar/<int:item_id>/delete', methods=['DELETE'])
@login_required
@admin_required
def delete_grammar(item_id):
    item = Grammar.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Grammar point deleted successfully"}), 200
