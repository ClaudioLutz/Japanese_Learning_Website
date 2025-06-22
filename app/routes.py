# app/routes.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy.exc import IntegrityError, SQLAlchemyError # Import specific exceptions
from app import db
from app.models import User, Kana, Kanji, Vocabulary, Grammar, LessonCategory, Lesson, LessonContent, LessonPrerequisite, UserLessonProgress
from app.forms import RegistrationForm, LoginForm, CSRFTokenForm
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

@bp.route('/admin/manage/lessons')
@login_required
@admin_required
def admin_manage_lessons():
    form = CSRFTokenForm()
    return render_template('admin/manage_lessons.html', form=form)

@bp.route('/admin/manage/categories')
@login_required
@admin_required
def admin_manage_categories():
    return render_template('admin/manage_categories.html')

# --- Lesson Routes for Users ---
@bp.route('/lessons')
@login_required
def lessons():
    """Browse available lessons"""
    return render_template('lessons.html')

@bp.route('/lessons/<int:lesson_id>')
@login_required
def view_lesson(lesson_id):
    """View a specific lesson"""
    lesson = Lesson.query.get_or_404(lesson_id)
    
    # Check if user can access this lesson
    accessible, message = lesson.is_accessible_to_user(current_user)
    if not accessible:
        flash(message, 'warning')
        return redirect(url_for('routes.lessons'))
    
    # Get or create user progress
    progress = UserLessonProgress.query.filter_by(
        user_id=current_user.id, lesson_id=lesson_id
    ).first()
    
    if not progress:
        progress = UserLessonProgress(user_id=current_user.id, lesson_id=lesson_id)
        db.session.add(progress)
        db.session.commit()
    
    return render_template('lesson_view.html', lesson=lesson, progress=progress)

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
    try:
        db.session.add(new_item)
        db.session.commit()
        return jsonify(model_to_dict(new_item)), 201
    except IntegrityError: # Handles unique constraint violations
        db.session.rollback()
        # This specific error for character uniqueness is already checked above,
        # but this handles it at the DB level just in case or for other integrity issues.
        return jsonify({"error": "Database integrity error. This item might already exist or violate other constraints."}), 409
    except SQLAlchemyError as e: # Handles other SQLAlchemy errors
        db.session.rollback()
        # Log the error e for debugging: app.logger.error(f"Database error: {e}")
        return jsonify({"error": "Database error occurred."}), 500

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
    try:
        db.session.add(new_item)
        db.session.commit()
        return jsonify(model_to_dict(new_item)), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Database integrity error. This item might already exist or violate other constraints."}), 409
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": "Database error occurred."}), 500

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
    try:
        db.session.add(new_item)
        db.session.commit()
        return jsonify(model_to_dict(new_item)), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Database integrity error. This item might already exist or violate other constraints."}), 409
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": "Database error occurred."}), 500

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
    try:
        db.session.add(new_item)
        db.session.commit()
        return jsonify(model_to_dict(new_item)), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Database integrity error. This item might already exist or violate other constraints."}), 409
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": "Database error occurred."}), 500

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

# == LESSON CATEGORY CRUD API ==
@bp.route('/api/admin/categories', methods=['GET'])
@login_required
@admin_required
def list_categories():
    items = LessonCategory.query.all()
    return jsonify([model_to_dict(item) for item in items])

@bp.route('/api/admin/categories/new', methods=['POST'])
@login_required
@admin_required
def create_category():
    data = request.json
    if not data or not data.get('name'):
        return jsonify({"error": "Missing required field: name"}), 400

    existing_category = LessonCategory.query.filter_by(name=data['name']).first()
    if existing_category:
        return jsonify({"error": "Category name already exists"}), 400

    new_item = LessonCategory(
        name=data['name'],
        description=data.get('description'),
        color_code=data.get('color_code', '#007bff')
    )
    try:
        db.session.add(new_item)
        db.session.commit()
        return jsonify(model_to_dict(new_item)), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Database integrity error."}), 409
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Database error occurred."}), 500

@bp.route('/api/admin/categories/<int:item_id>', methods=['GET'])
@login_required
@admin_required
def get_category(item_id):
    item = LessonCategory.query.get_or_404(item_id)
    return jsonify(model_to_dict(item))

@bp.route('/api/admin/categories/<int:item_id>/edit', methods=['PUT', 'PATCH'])
@login_required
@admin_required
def update_category(item_id):
    item = LessonCategory.query.get_or_404(item_id)
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    item.name = data.get('name', item.name)
    item.description = data.get('description', item.description)
    item.color_code = data.get('color_code', item.color_code)

    db.session.commit()
    return jsonify(model_to_dict(item))

@bp.route('/api/admin/categories/<int:item_id>/delete', methods=['DELETE'])
@login_required
@admin_required
def delete_category(item_id):
    item = LessonCategory.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Category deleted successfully"}), 200

# == LESSON CRUD API ==
@bp.route('/api/admin/lessons', methods=['GET'])
@login_required
@admin_required
def list_lessons():
    items = Lesson.query.all()
    lessons_data = []
    for item in items:
        lesson_dict = model_to_dict(item)
        lesson_dict['category_name'] = item.category.name if item.category else None
        lesson_dict['content_count'] = len(item.content_items)
        lessons_data.append(lesson_dict)
    return jsonify(lessons_data)

@bp.route('/api/admin/lessons/new', methods=['POST'])
@login_required
@admin_required
def create_lesson():
    data = request.json
    if not data or not data.get('title') or not data.get('lesson_type'):
        return jsonify({"error": "Missing required fields: title, lesson_type"}), 400

    existing_lesson = Lesson.query.filter_by(title=data['title']).first()
    if existing_lesson:
        return jsonify({"error": "Lesson title already exists"}), 400

    new_item = Lesson(
        title=data['title'],
        description=data.get('description'),
        lesson_type=data['lesson_type'],
        category_id=data.get('category_id'),
        difficulty_level=data.get('difficulty_level'),
        estimated_duration=data.get('estimated_duration'),
        order_index=data.get('order_index', 0),
        is_published=data.get('is_published', False),
        thumbnail_url=data.get('thumbnail_url'),
        video_intro_url=data.get('video_intro_url')
    )
    try:
        db.session.add(new_item)
        db.session.commit()
        return jsonify(model_to_dict(new_item)), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Database integrity error."}), 409
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Database error occurred."}), 500

@bp.route('/api/admin/lessons/<int:item_id>', methods=['GET'])
@login_required
@admin_required
def get_lesson(item_id):
    item = Lesson.query.get_or_404(item_id)
    lesson_dict = model_to_dict(item)
    lesson_dict['category_name'] = item.category.name if item.category else None
    lesson_dict['content_items'] = [model_to_dict(content) for content in item.content_items]
    lesson_dict['prerequisites'] = [model_to_dict(prereq.prerequisite_lesson) for prereq in item.prerequisites]
    return jsonify(lesson_dict)

@bp.route('/api/admin/lessons/<int:item_id>/edit', methods=['PUT', 'PATCH'])
@login_required
@admin_required
def update_lesson(item_id):
    item = Lesson.query.get_or_404(item_id)
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    item.title = data.get('title', item.title)
    item.description = data.get('description', item.description)
    item.lesson_type = data.get('lesson_type', item.lesson_type)
    item.category_id = data.get('category_id', item.category_id)
    item.difficulty_level = data.get('difficulty_level', item.difficulty_level)
    item.estimated_duration = data.get('estimated_duration', item.estimated_duration)
    item.order_index = data.get('order_index', item.order_index)
    item.is_published = data.get('is_published', item.is_published)
    item.thumbnail_url = data.get('thumbnail_url', item.thumbnail_url)
    item.video_intro_url = data.get('video_intro_url', item.video_intro_url)

    db.session.commit()
    return jsonify(model_to_dict(item))

@bp.route('/api/admin/lessons/<int:item_id>/delete', methods=['DELETE'])
@login_required
@admin_required
def delete_lesson(item_id):
    item = Lesson.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Lesson deleted successfully"}), 200

# == CONTENT OPTIONS API ==
@bp.route('/api/admin/content-options/<content_type>', methods=['GET'])
@login_required
@admin_required
def get_content_options(content_type):
    """Get available content items for selection in lesson builder"""
    try:
        if content_type == 'kana':
            items = Kana.query.all()
        elif content_type == 'kanji':
            items = Kanji.query.all()
        elif content_type == 'vocabulary':
            items = Vocabulary.query.all()
        elif content_type == 'grammar':
            items = Grammar.query.all()
        else:
            return jsonify({"error": "Invalid content type"}), 400
        
        return jsonify([model_to_dict(item) for item in items])
    except Exception as e:
        return jsonify({"error": "Failed to load content options"}), 500

# == LESSON CONTENT API ==
@bp.route('/api/admin/lessons/<int:lesson_id>/content', methods=['GET'])
@login_required
@admin_required
def list_lesson_content(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    content_items = LessonContent.query.filter_by(lesson_id=lesson_id).order_by(LessonContent.order_index).all()
    return jsonify([model_to_dict(item) for item in content_items])

@bp.route('/api/admin/lessons/<int:lesson_id>/content/new', methods=['POST'])
@login_required
@admin_required
def add_lesson_content(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    data = request.json
    if not data or not data.get('content_type'):
        return jsonify({"error": "Missing required field: content_type"}), 400

    # Convert string 'false'/'true' to boolean for is_optional
    is_optional = data.get('is_optional', False)
    if isinstance(is_optional, str):
        is_optional = is_optional.lower() == 'true'

    new_content = LessonContent(
        lesson_id=lesson_id,
        content_type=data['content_type'],
        content_id=data.get('content_id'),
        title=data.get('title'),
        content_text=data.get('content_text'),
        media_url=data.get('media_url'),
        order_index=int(data.get('order_index', 0)),
        is_optional=is_optional
    )
    try:
        db.session.add(new_content)
        db.session.commit()
        return jsonify(model_to_dict(new_content)), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": f"Database error occurred: {str(e)}"}), 500

@bp.route('/api/admin/lessons/<int:lesson_id>/content/<int:content_id>/delete', methods=['DELETE'])
@login_required
@admin_required
def remove_lesson_content(lesson_id, content_id):
    content = LessonContent.query.filter_by(lesson_id=lesson_id, id=content_id).first_or_404()
    db.session.delete(content)
    db.session.commit()
    return jsonify({"message": "Content removed from lesson successfully"}), 200

# == USER LESSON API ==
@bp.route('/api/lessons', methods=['GET'])
@login_required
def get_user_lessons():
    """Get lessons accessible to the current user"""
    lessons = Lesson.query.filter_by(is_published=True).all()
    accessible_lessons = []
    
    for lesson in lessons:
        accessible, message = lesson.is_accessible_to_user(current_user)
        lesson_dict = model_to_dict(lesson)
        lesson_dict['accessible'] = accessible
        lesson_dict['access_message'] = message
        lesson_dict['category_name'] = lesson.category.name if lesson.category else None
        
        # Get user progress if exists
        progress = UserLessonProgress.query.filter_by(
            user_id=current_user.id, lesson_id=lesson.id
        ).first()
        lesson_dict['progress'] = model_to_dict(progress) if progress else None
        
        accessible_lessons.append(lesson_dict)
    
    return jsonify(accessible_lessons)

@bp.route('/api/lessons/<int:lesson_id>/progress', methods=['POST'])
@login_required
def update_lesson_progress(lesson_id):
    """Update user progress for a lesson"""
    lesson = Lesson.query.get_or_404(lesson_id)
    
    # Check access
    accessible, message = lesson.is_accessible_to_user(current_user)
    if not accessible:
        return jsonify({"error": message}), 403
    
    data = request.json
    progress = UserLessonProgress.query.filter_by(
        user_id=current_user.id, lesson_id=lesson_id
    ).first()
    
    if not progress:
        progress = UserLessonProgress(user_id=current_user.id, lesson_id=lesson_id)
        db.session.add(progress)
    
    # Update progress fields
    if data and 'content_id' in data:
        progress.mark_content_completed(data['content_id'])
    
    if data and 'time_spent' in data:
        progress.time_spent += data['time_spent']
    
    progress.last_accessed = db.func.now()
    
    db.session.commit()
    return jsonify(model_to_dict(progress))

# == FILE UPLOAD API ==
@bp.route('/api/admin/upload-file', methods=['POST'])
@login_required
@admin_required
def upload_file():
    """Handle file upload and return file information"""
    import os
    from werkzeug.utils import secure_filename

    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file part in the request'}), 400

    file = request.files['file']

    if not file or not file.filename:
        return jsonify({'success': False, 'error': 'No file selected'}), 400

    if file and file.filename:
        # Ensure the filename is safe to use
        filename = secure_filename(file.filename)
        
        # This assumes you have an 'UPLOAD_FOLDER' configured in your app
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'app/static/uploads')
        
        # You might want to create subdirectories for lessons or file types
        # For simplicity, we save directly to a general uploads folder here.
        # Example: target_folder = os.path.join(upload_folder, 'lessons', 'images')
        target_folder = os.path.join(upload_folder, 'lessons', 'images') # Saving to a specific folder for images
        os.makedirs(target_folder, exist_ok=True)

        filepath = os.path.join(target_folder, filename)
        file.save(filepath)

        # Return a success response with the file's path
        # The URL path should correspond to how you serve static files
        # Example: /static/uploads/lessons/images/my_image.png
        file_url = os.path.join('uploads', 'lessons', 'images', filename).replace('\\', '/')

        return jsonify({
            'success': True,
            'filePath': url_for('static', filename=file_url, _external=False),
            'fileName': filename
        })

    return jsonify({'success': False, 'error': 'An unknown error occurred'}), 500

@bp.route('/api/admin/lessons/<int:lesson_id>/content/file', methods=['POST'])
@login_required
@admin_required
def add_file_content(lesson_id):
    """Add file-based content to lesson"""
    lesson = Lesson.query.get_or_404(lesson_id)
    data = request.json
    
    if not data or not data.get('content_type') or not data.get('file_path'):
        return jsonify({"error": "Missing required fields: content_type, file_path"}), 400
    
    # Convert string 'false'/'true' to boolean for is_optional
    is_optional = data.get('is_optional', False)
    if isinstance(is_optional, str):
        is_optional = is_optional.lower() == 'true'
    
    new_content = LessonContent(
        lesson_id=lesson_id,
        content_type=data['content_type'],
        title=data.get('title'),
        content_text=data.get('description'),
        file_path=data['file_path'],
        file_size=data.get('file_size'),
        file_type=data.get('file_type'),
        original_filename=data.get('original_filename'),
        order_index=int(data.get('order_index', 0)),
        is_optional=is_optional
    )
    
    try:
        db.session.add(new_content)
        db.session.commit()
        return jsonify(model_to_dict(new_content)), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": f"Database error occurred: {str(e)}"}), 500

@bp.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    import os
    from flask import send_from_directory
    
    upload_folder = current_app.config['UPLOAD_FOLDER']
    file_path = os.path.join(upload_folder, filename)
    
    # Security check - ensure file is within upload folder
    if not os.path.abspath(file_path).startswith(os.path.abspath(upload_folder)):
        return jsonify({"error": "Access denied"}), 403
    
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404
    
    directory = os.path.dirname(file_path)
    basename = os.path.basename(file_path)
    
    return send_from_directory(directory, basename)

@bp.route('/api/admin/delete-file', methods=['DELETE'])
@login_required
@admin_required
def delete_file():
    """Delete uploaded file"""
    from app.utils import FileUploadHandler
    import os
    
    data = request.json
    if not data or not data.get('file_path'):
        return jsonify({"error": "File path required"}), 400
    
    file_path = data['file_path']
    full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file_path)
    
    # Security check
    if not os.path.abspath(full_path).startswith(os.path.abspath(current_app.config['UPLOAD_FOLDER'])):
        return jsonify({"error": "Access denied"}), 403
    
    # Delete from filesystem
    if FileUploadHandler.delete_file(full_path):
        # Also delete from database if it's associated with content
        content_id = data.get('content_id')
        if content_id:
            content = LessonContent.query.get(content_id)
            if content and content.file_path == file_path:
                content.delete_file()  # This also deletes the file, but we already did that
                db.session.delete(content)
                db.session.commit()
        
        return jsonify({"message": "File deleted successfully"}), 200
    else:
        return jsonify({"error": "Failed to delete file"}), 500
