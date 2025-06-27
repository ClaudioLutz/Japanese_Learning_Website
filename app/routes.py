# app/routes.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy.exc import IntegrityError, SQLAlchemyError # Import specific exceptions
from app import db
from app.models import User, Kana, Kanji, Vocabulary, Grammar, LessonCategory, Lesson, LessonContent, LessonPrerequisite, UserLessonProgress, QuizQuestion, QuizOption, UserQuizAnswer
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

# --- Member Routes (Simulated Premium) ---

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
    
    form = CSRFTokenForm()
    return render_template('lesson_view.html', lesson=lesson, progress=progress, form=form)

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

    # Determine the next order index
    last_content = LessonContent.query.filter_by(lesson_id=lesson_id).order_by(LessonContent.order_index.desc()).first()
    next_order_index = (last_content.order_index + 1) if last_content else 0

    new_content = LessonContent(
        lesson_id=lesson_id,
        content_type=data['content_type'],
        content_id=data.get('content_id'),
        title=data.get('title'),
        content_text=data.get('content_text'),
        media_url=data.get('media_url'),
        order_index=next_order_index,
        page_number=data.get('page_number', 1),  # Handle page number
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

    try:
        # C1: Ensure file is deleted from disk if it exists
        if content.file_path:
            content.delete_file() # Calls app.models.LessonContent.delete_file()

        db.session.delete(content)
        db.session.commit()
        return jsonify({"message": "Content removed from lesson successfully"}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error removing lesson content {content_id} from lesson {lesson_id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to remove lesson content"}), 500

@bp.route('/api/admin/lessons/<int:lesson_id>/content/<int:content_id>/move', methods=['POST'])
@login_required
@admin_required
def move_lesson_content(lesson_id, content_id):
    """Move a lesson content item up or down in order."""
    data = request.json
    direction = data.get('direction')
    if direction not in ['up', 'down']:
        return jsonify({"error": "Invalid direction specified"}), 400

    content_to_move = LessonContent.query.filter_by(id=content_id, lesson_id=lesson_id).first_or_404()
    
    current_order = content_to_move.order_index
    
    if direction == 'up':
        # Find the item directly above
        item_to_swap_with = LessonContent.query.filter_by(lesson_id=lesson_id, order_index=current_order - 1).first()
        if not item_to_swap_with:
            return jsonify({"error": "Cannot move item further up"}), 400
        
        # Swap order indices
        content_to_move.order_index -= 1
        item_to_swap_with.order_index += 1

    elif direction == 'down':
        # Find the item directly below
        item_to_swap_with = LessonContent.query.filter_by(lesson_id=lesson_id, order_index=current_order + 1).first()
        if not item_to_swap_with:
            return jsonify({"error": "Cannot move item further down"}), 400
            
        # Swap order indices
        content_to_move.order_index += 1
        item_to_swap_with.order_index -= 1

    try:
        db.session.commit()
        return jsonify({"message": "Content moved successfully"}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error moving content: {e}")
        return jsonify({"error": "Database error occurred"}), 500

@bp.route('/api/admin/content/<int:content_id>/preview', methods=['GET'])
@login_required
@admin_required
def preview_content(content_id):
    """Get content preview data"""
    content = LessonContent.query.get_or_404(content_id)
    
    preview_data = model_to_dict(content)
    
    # Add related data based on content type
    if content.content_type in ['kana', 'kanji', 'vocabulary', 'grammar']:
        content_data = content.get_content_data()
        if content_data:
            preview_data['content_data'] = model_to_dict(content_data)
    
    # Add quiz questions for interactive content
    if content.is_interactive:
        preview_data['quiz_questions'] = [
            model_to_dict(q) for q in content.quiz_questions
        ]
    
    return jsonify(preview_data)

@bp.route('/api/admin/content/<int:content_id>', methods=['GET'])
@login_required
@admin_required
def get_content_details(content_id):
    """Get full details for a single content item for editing."""
    content = LessonContent.query.get_or_404(content_id)
    content_dict = model_to_dict(content)

    if content.is_interactive:
        question = QuizQuestion.query.filter_by(lesson_content_id=content.id).first()
        if question:
            content_dict['interactive_type'] = question.question_type
            content_dict['question_text'] = question.question_text
            content_dict['explanation'] = question.explanation
            
            if question.question_type == 'multiple_choice':
                options = QuizOption.query.filter_by(question_id=question.id).all()
                content_dict['options'] = [model_to_dict(opt) for opt in options]
            elif question.question_type == 'fill_blank':
                # The correct answers are stored in the explanation field for fill_blank
                content_dict['correct_answers'] = question.explanation
            elif question.question_type == 'true_false':
                true_option = QuizOption.query.filter_by(question_id=question.id, option_text='True').first()
                if true_option:
                    content_dict['correct_answer'] = true_option.is_correct

    return jsonify(content_dict)

@bp.route('/api/admin/content/<int:content_id>/edit', methods=['PUT'])
@login_required
@admin_required
def update_lesson_content(content_id):
    """Update an existing lesson content item."""
    content = LessonContent.query.get_or_404(content_id)
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    try:
        # Common fields
        content.title = data.get('title', content.title)
        content.order_index = int(data.get('order_index', content.order_index))
        content.page_number = int(data.get('page_number', content.page_number))  # Handle page number
        is_optional = data.get('is_optional', content.is_optional)
        if isinstance(is_optional, str):
            content.is_optional = is_optional.lower() == 'true'
        else:
            content.is_optional = is_optional

        # Type-specific fields
        content.content_type = data.get('content_type', content.content_type)
        if content.content_type in ['kana', 'kanji', 'vocabulary', 'grammar']:
            content.content_id = data.get('content_id', content.content_id)
        elif content.content_type == 'text':
            content.content_text = data.get('content_text', content.content_text)
        elif content.content_type in ['video', 'audio', 'image']:
            content.media_url = data.get('media_url', content.media_url)
            content.file_path = data.get('file_path', content.file_path)
            content.content_text = data.get('description', content.content_text)
        elif content.content_type == 'interactive':
            content.is_interactive = True
            interactive_type = data.get('interactive_type')

            # Use a query to get the question, which is more explicit for static analysis
            question = QuizQuestion.query.filter_by(lesson_content_id=content.id).first()
            if not question:
                question = QuizQuestion(lesson_content_id=content.id)
                db.session.add(question)

            if interactive_type:
                question.question_type = interactive_type
            question.question_text = data.get('question_text', question.question_text)
            question.explanation = data.get('explanation', question.explanation)

            # Use a bulk delete for efficiency and to resolve Pylance errors
            QuizOption.query.filter_by(question_id=question.id).delete()

            if question.question_type == 'multiple_choice':
                options_data = data.get('options', [])
                for i, option_data in enumerate(options_data):
                    new_option = QuizOption(
                        question_id=question.id,
                        option_text=option_data['text'],
                        is_correct=option_data.get('is_correct', False),
                        order_index=i,
                        feedback=option_data.get('feedback', '')
                    )
                    db.session.add(new_option)
            
            elif question.question_type == 'fill_blank':
                question.explanation = data.get('correct_answers', question.explanation)

            elif question.question_type == 'true_false':
                correct_answer = data.get('correct_answer')
                options_data = [
                    {'text': 'True', 'is_correct': correct_answer is True},
                    {'text': 'False', 'is_correct': correct_answer is False}
                ]
                for i, option_data in enumerate(options_data):
                    new_option = QuizOption(
                        question_id=question.id,
                        option_text=option_data['text'],
                        is_correct=option_data.get('is_correct', False),
                        order_index=i
                    )
                    db.session.add(new_option)

        db.session.commit()
        return jsonify(model_to_dict(content)), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": f"Database error occurred: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

@bp.route('/api/admin/lessons/<int:lesson_id>/content/bulk-update', methods=['PUT'])
@login_required
@admin_required
def bulk_update_content(lesson_id):
    """Bulk update content properties"""
    lesson = Lesson.query.get_or_404(lesson_id)
    data = request.json
    
    if not data or 'content_ids' not in data or 'updates' not in data:
        return jsonify({"error": "Missing required data"}), 400
    
    try:
        content_items = LessonContent.query.filter(
            LessonContent.lesson_id == lesson_id,
            LessonContent.id.in_(data['content_ids'])
        ).all()
        
        for content in content_items:
            for key, value in data['updates'].items():
                if hasattr(content, key):
                    setattr(content, key, value)
        
        db.session.commit()
        return jsonify({"message": f"Updated {len(content_items)} content items"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update content"}), 500

@bp.route('/api/admin/lessons/<int:lesson_id>/content/bulk-duplicate', methods=['POST'])
@login_required
@admin_required
def bulk_duplicate_content(lesson_id):
    """Bulk duplicate content items"""
    lesson = Lesson.query.get_or_404(lesson_id)
    data = request.json
    
    if not data or 'content_ids' not in data:
        return jsonify({"error": "Missing content IDs"}), 400
    
    try:
        duplicated_count = 0
        
        for content_id in data['content_ids']:
            original = LessonContent.query.filter_by(
                lesson_id=lesson_id, 
                id=content_id
            ).first()
            
            if original:
                # Create duplicate
                duplicate = LessonContent(
                    lesson_id=lesson_id,
                    content_type=original.content_type,
                    content_id=original.content_id,
                    title=f"{original.title} (Copy)" if original.title else None,
                    content_text=original.content_text,
                    media_url=original.media_url,
                    file_path=original.file_path,
                    order_index=original.order_index + 1000,  # Place at end
                    is_optional=original.is_optional,
                    is_interactive=original.is_interactive,
                    max_attempts=original.max_attempts,
                    passing_score=original.passing_score
                )
                
                db.session.add(duplicate)
                db.session.flush()  # Get the new ID
                
                # Duplicate quiz questions if interactive
                if original.is_interactive:
                    for question in original.quiz_questions:
                        new_question = QuizQuestion(
                            lesson_content_id=duplicate.id,
                            question_type=question.question_type,
                            question_text=question.question_text,
                            explanation=question.explanation,
                            points=question.points,
                            order_index=question.order_index
                        )
                        db.session.add(new_question)
                        db.session.flush()
                        
                        # Duplicate options
                        for option in question.options:
                            new_option = QuizOption(
                                question_id=new_question.id,
                                option_text=option.option_text,
                                is_correct=option.is_correct,
                                order_index=option.order_index,
                                feedback=option.feedback
                            )
                            db.session.add(new_option)
                
                duplicated_count += 1
        
        db.session.commit()
        return jsonify({"message": f"Duplicated {duplicated_count} content items"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to duplicate content"}), 500

@bp.route('/api/admin/lessons/<int:lesson_id>/content/bulk-delete', methods=['DELETE'])
@login_required
@admin_required
def bulk_delete_content(lesson_id):
    """Bulk delete content items"""
    lesson = Lesson.query.get_or_404(lesson_id)
    data = request.json
    
    if not data or 'content_ids' not in data:
        return jsonify({"error": "Missing content IDs"}), 400
    
    try:
        content_items = LessonContent.query.filter(
            LessonContent.lesson_id == lesson_id,
            LessonContent.id.in_(data['content_ids'])
        ).all()
        
        deleted_count = len(content_items)
        
        for content in content_items:
            # Delete associated files if any
            if hasattr(content, 'delete_file'):
                content.delete_file()
            db.session.delete(content)
        
        db.session.commit()
        return jsonify({"message": f"Deleted {deleted_count} content items"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to delete content"}), 500

@bp.route('/api/admin/content/<int:content_id>/duplicate', methods=['POST'])
@login_required
@admin_required
def duplicate_single_content(content_id):
    """Duplicate a single content item"""
    original = LessonContent.query.get_or_404(content_id)
    
    try:
        # Create duplicate (same logic as bulk duplicate)
        duplicate = LessonContent(
            lesson_id=original.lesson_id,
            content_type=original.content_type,
            content_id=original.content_id,
            title=f"{original.title} (Copy)" if original.title else None,
            content_text=original.content_text,
            media_url=original.media_url,
            file_path=original.file_path,
            order_index=original.order_index + 1,
            is_optional=original.is_optional,
            is_interactive=original.is_interactive,
            max_attempts=original.max_attempts,
            passing_score=original.passing_score
        )
        
        db.session.add(duplicate)
        db.session.flush()
        
        # Duplicate quiz questions if interactive
        if original.is_interactive:
            for question in original.quiz_questions:
                new_question = QuizQuestion(
                    lesson_content_id=duplicate.id,
                    question_type=question.question_type,
                    question_text=question.question_text,
                    explanation=question.explanation,
                    points=question.points,
                    order_index=question.order_index
                )
                db.session.add(new_question)
                db.session.flush()
                
                for option in question.options:
                    new_option = QuizOption(
                        question_id=new_question.id,
                        option_text=option.option_text,
                        is_correct=option.is_correct,
                        order_index=option.order_index,
                        feedback=option.feedback
                    )
                    db.session.add(new_option)
        
        db.session.commit()
        return jsonify(model_to_dict(duplicate)), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to duplicate content"}), 500

# Add new route for deleting a page
@bp.route('/api/admin/lessons/<int:lesson_id>/pages/<int:page_num>/delete', methods=['DELETE'])
@login_required
@admin_required
def delete_lesson_page(lesson_id, page_num):
    """Deletes a page and all its content items from a lesson."""
    content_to_delete = LessonContent.query.filter_by(lesson_id=lesson_id, page_number=page_num).all()
    
    if not content_to_delete:
        return jsonify({"error": "Page not found or is empty"}), 404
    
    try:
        for content in content_to_delete:
            if content.file_path:
                content.delete_file()
            db.session.delete(content)
        
        db.session.commit()
        return jsonify({"message": f"Page {page_num} and its {len(content_to_delete)} content items deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting page {page_num} from lesson {lesson_id}: {e}")
        return jsonify({"error": "Failed to delete page"}), 500

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

@bp.route('/lessons/<int:lesson_id>/reset', methods=['POST'])
@login_required
def reset_lesson_progress(lesson_id):
    """Reset user progress for a specific lesson."""
    progress = UserLessonProgress.query.filter_by(
        user_id=current_user.id, lesson_id=lesson_id
    ).first()

    if progress:
        progress.reset()  # Assuming a reset method in the model
        db.session.commit()
        flash('Your progress for this lesson has been reset.', 'success')
    else:
        flash('No progress found for this lesson.', 'info')

    return redirect(url_for('routes.view_lesson', lesson_id=lesson_id))

@bp.route('/api/admin/lessons/<int:lesson_id>/content/interactive', methods=['POST'])
@login_required
@admin_required
def add_interactive_content(lesson_id):
    """Add interactive content (quiz questions) to lesson"""
    lesson = Lesson.query.get_or_404(lesson_id)
    data = request.json
    
    if not data or not data.get('interactive_type'):
        return jsonify({"error": "Missing interactive type"}), 400
    
    # Create lesson content
    # Determine the next order index
    last_content = LessonContent.query.filter_by(lesson_id=lesson_id).order_by(LessonContent.order_index.desc()).first()
    next_order_index = (last_content.order_index + 1) if last_content else 0

    content = LessonContent(
        lesson_id=lesson_id,
        content_type='interactive',
        title=data.get('title'),
        is_interactive=True,
        max_attempts=data.get('max_attempts', 3),
        passing_score=data.get('passing_score', 70),
        order_index=next_order_index,
        page_number=data.get('page_number', 1)  # Add page number handling
    )
    
    db.session.add(content)
    db.session.flush()  # Get the content ID
    
    # Create quiz question
    question = QuizQuestion(
        lesson_content_id=content.id,
        question_type=data['interactive_type'],
        question_text=data.get('question_text'),
        explanation=data.get('explanation'),
        points=data.get('points', 1)
    )
    
    db.session.add(question)
    db.session.flush()  # Get the question ID
    
    # Add options for multiple choice and true/false
    if data['interactive_type'] in ['multiple_choice', 'true_false']:
        options_data = data.get('options', [])
        if data['interactive_type'] == 'true_false':
            options_data = [
                {'text': 'True', 'is_correct': data.get('correct_answer') is True},
                {'text': 'False', 'is_correct': data.get('correct_answer') is False}
            ]

        for i, option_data in enumerate(options_data):
            option = QuizOption(
                question_id=question.id,
                option_text=option_data['text'],
                is_correct=option_data.get('is_correct', False),
                order_index=i,
                feedback=option_data.get('feedback', '')
            )
            db.session.add(option)
    
    db.session.commit()
    return jsonify(model_to_dict(content)), 201

from sqlalchemy.orm import joinedload

@bp.route('/api/lessons/<int:lesson_id>/quiz/<int:question_id>/answer', methods=['POST'])
@login_required
def submit_quiz_answer(lesson_id, question_id):
    """Submit answer to quiz question"""
    try:
        lesson = Lesson.query.get_or_404(lesson_id)
        question = db.session.query(QuizQuestion).options(
            joinedload(QuizQuestion.content)
        ).filter(QuizQuestion.id == question_id).first()

        if not question or question.content.lesson_id != lesson_id:
            return jsonify({"error": "Question not found in this lesson"}), 404
        
        # Check lesson access
        accessible, message = lesson.is_accessible_to_user(current_user)
        if not accessible:
            current_app.logger.warning(f"User {current_user.id} access denied for lesson {lesson_id}: {message}")
            return jsonify({"error": message}), 403
        
        data = request.json
        if not data:
            return jsonify({"error": "Invalid request. Must be JSON."}), 400
        current_app.logger.info(f"Received answer for question {question_id} from user {current_user.id}: {data}")
        
        # Find existing answer or create a new one
        answer = UserQuizAnswer.query.filter_by(
            user_id=current_user.id, question_id=question_id
        ).first()

        # If an answer exists, check attempts
        if answer:
            if not question.content:
                return jsonify({"error": "Associated content for this question not found."}), 500
            
            max_attempts = question.content.max_attempts or float('inf')

            if answer.attempts >= max_attempts:
                current_app.logger.warning(f"User {current_user.id} exceeded max attempts for question {question_id}")
                return jsonify({"error": "Maximum attempts exceeded"}), 400
            answer.attempts += 1
        else:
            # No existing answer, create a new one
            answer = UserQuizAnswer(
                user_id=current_user.id,
                question_id=question_id,
                attempts=1
            )
            db.session.add(answer)

        # Process answer based on question type
        is_correct = False
        selected_option = None

        if question.question_type == 'multiple_choice':
            selected_option_id = data.get('selected_option_id')
            current_app.logger.info(f"Selected option ID from request: {selected_option_id}")
            if not selected_option_id:
                return jsonify({"error": "selected_option_id is required"}), 400
            
            selected_option = QuizOption.query.get(int(selected_option_id))
            current_app.logger.info(f"Selected option from DB: {selected_option}")
            
            is_correct = selected_option and selected_option.is_correct
            current_app.logger.info(f"Is correct: {is_correct}")

            answer.selected_option_id = selected_option_id
            answer.is_correct = is_correct
            answer.text_answer = None
        
        elif question.question_type == 'fill_blank':
            text_answer = data.get('text_answer', '').strip()
            correct_answers = [ans.strip().lower() for ans in (question.explanation or "").split(',')]
            is_correct = text_answer.lower() in correct_answers
            
            answer.text_answer = text_answer
            answer.is_correct = is_correct
            answer.selected_option_id = None

        elif question.question_type == 'true_false':
            selected_option_id = data.get('selected_option_id')
            if not selected_option_id:
                return jsonify({"error": "selected_option_id is required"}), 400
            selected_option = QuizOption.query.get(int(selected_option_id))
            is_correct = selected_option and selected_option.is_correct

            answer.selected_option_id = selected_option_id
            answer.is_correct = is_correct
            answer.text_answer = None

        else:
            return jsonify({"error": "Unsupported question type"}), 400

        answer.answered_at = db.func.now()
        
        db.session.commit()
        
        # Return result with feedback
        # Calculate remaining attempts safely
        attempts_remaining = 'Unlimited'
        if question.content and question.content.max_attempts:
            attempts_remaining = question.content.max_attempts - answer.attempts

        result = {
            'is_correct': is_correct,
            'explanation': question.explanation,
            'attempts_remaining': attempts_remaining
        }
        
        if selected_option:
            result['option_feedback'] = selected_option.feedback
        
        current_app.logger.info(f"Answer for question {question_id} processed. Result: {result}")
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Error submitting quiz answer for question {question_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500

# == FILE UPLOAD API ==
from app.utils import FileUploadHandler # Import FileUploadHandler

# ... (other imports and code) ...

# == FILE UPLOAD API ==
@bp.route('/api/admin/upload-file', methods=['POST'])
@login_required
@admin_required
def upload_file():
    """Handle file upload, validate, process, and return file information"""
    import os

    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file part in the request'}), 400

    file_storage = request.files['file']
    lesson_id_str = request.form.get('lesson_id') # Optional: for organizing files by lesson

    if not file_storage or not file_storage.filename:
        return jsonify({'success': False, 'error': 'No file selected'}), 400

    original_filename = file_storage.filename

    # A2: Check allowed extensions (basic check)
    file_type_from_ext = FileUploadHandler.get_file_type(original_filename)
    if not file_type_from_ext:
        return jsonify({'success': False, 'error': 'File type not allowed by extension.'}), 415

    if not FileUploadHandler.allowed_file(original_filename, file_type_from_ext):
        return jsonify({'success': False, 'error': f"File extension for '{file_type_from_ext}' not allowed."}), 415

    # A3: Generate unique filename
    # We use secure_filename within generate_unique_filename
    unique_filename = FileUploadHandler.generate_unique_filename(original_filename)

    # Determine target directory (more dynamic based on file type and optional lesson_id)
    # For now, let's keep it simpler and categorize by file_type. Lesson-specific folders can be a future enhancement.
    # A5: Modified target directory logic
    upload_folder = current_app.config['UPLOAD_FOLDER']

    # Create a temporary path first for validation
    temp_dir = os.path.join(upload_folder, 'temp') # Defined in __init__.py
    os.makedirs(temp_dir, exist_ok=True)
    temp_filepath = os.path.join(temp_dir, unique_filename)

    try:
        file_storage.save(temp_filepath)

        # A1: Validate file content (MIME type)
        if not FileUploadHandler.validate_file_content(temp_filepath, file_type_from_ext):
            FileUploadHandler.delete_file(temp_filepath) # Clean up temp file
            return jsonify({'success': False, 'error': 'File content does not match extension or is not allowed.'}), 415

        # A4: Process image if it's an image file
        if file_type_from_ext == 'image':
            if not FileUploadHandler.process_image(temp_filepath):
                FileUploadHandler.delete_file(temp_filepath) # Clean up temp file
                return jsonify({'success': False, 'error': 'Image processing failed.'}), 500
        
        # Determine final directory based on file type
        # This is a simplified version. A more robust system might use lesson_id if provided.
        final_type_dir = os.path.join(upload_folder, 'lessons', file_type_from_ext)
        os.makedirs(final_type_dir, exist_ok=True)
        final_filepath = os.path.join(final_type_dir, unique_filename)
        
        # Move validated and processed file to its final destination
        os.rename(temp_filepath, final_filepath)

        # Get file info for the response
        file_info = FileUploadHandler.get_file_info(final_filepath)

        # Relative path for URL generation and storing in DB
        relative_file_path = os.path.join('lessons', file_type_from_ext, unique_filename).replace('\\', '/')

        return jsonify({
            'success': True,
            'filePath': url_for('static', filename=os.path.join('uploads', relative_file_path).replace('\\', '/'), _external=False), # Path for url_for
            'dbPath': relative_file_path, # Path to store in DB
            'fileName': unique_filename,
            'originalFilename': original_filename,
            'fileType': file_type_from_ext,
            'fileSize': file_info.get('size'),
            'mimeType': file_info.get('mime_type'),
            'dimensions': file_info.get('dimensions')
        }), 200

    except Exception as e:
        current_app.logger.error(f"File upload failed: {e}", exc_info=True)
        if os.path.exists(temp_filepath): # Ensure cleanup on any other exception
            FileUploadHandler.delete_file(temp_filepath)
        return jsonify({'success': False, 'error': 'An server error occurred during file upload.'}), 500
    finally:
        # Double check temp file is removed if it still exists (e.g. if os.rename failed)
        if os.path.exists(temp_filepath):
             FileUploadHandler.delete_file(temp_filepath)


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
    
    # Determine the next order index
    last_content = LessonContent.query.filter_by(lesson_id=lesson_id).order_by(LessonContent.order_index.desc()).first()
    next_order_index = (last_content.order_index + 1) if last_content else 0

    new_content = LessonContent(
        lesson_id=lesson_id,
        content_type=data['content_type'],
        title=data.get('title'),
        content_text=data.get('description'),
        file_path=data['file_path'],
        file_size=data.get('file_size'),
        file_type=data.get('file_type'),
        original_filename=data.get('original_filename'),
        order_index=next_order_index,
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
    
    content_id = data.get('content_id')
    file_deleted_from_fs = False
    associated_content_deleted = False

    # If content_id is provided, prioritize deleting the LessonContent record,
    # which should trigger its own file deletion via content.delete_file() if properly linked.
    if content_id:
        content = LessonContent.query.get(content_id)
        if content:
            if content.file_path == file_path: # Ensure the content item actually refers to this file
                # C2: Call content.delete_file() which handles file system deletion.
                # This is app.models.LessonContent.delete_file()
                content.delete_file()
                # We trust content.delete_file() to have attempted deletion.
                # For robustness, we can check os.path.exists(full_path) here if needed,
                # but FileUploadHandler.delete_file below will also handle it.

                db.session.delete(content)
                db.session.commit()
                associated_content_deleted = True
                # If content.delete_file() worked, the file should be gone.
                # To be certain, especially if content.delete_file() might fail silently or not exist:
                if not os.path.exists(full_path):
                    file_deleted_from_fs = True
            else:
                # content_id provided, but its file_path doesn't match the one in request.
                # This is an ambiguous situation. For safety, we might only delete the file from FS
                # if it's not associated with this *specific* content_id.
                # Or, return an error. Let's opt for only deleting the file if no content was deleted.
                pass # Will fall through to general file deletion if no content record was handled.
        else:
            # content_id provided but no such content found.
            # Proceed to delete the file from filesystem if it exists.
            pass

    # General file deletion from filesystem if not handled by content deletion
    # or if no content_id was provided.
    if not file_deleted_from_fs: # C2: Avoid deleting twice
        if FileUploadHandler.delete_file(full_path): # This is app.utils.FileUploadHandler.delete_file
            file_deleted_from_fs = True
        else:
            # If content was associated and deleted, but file system deletion failed here,
            # it's a partial success.
            if associated_content_deleted:
                 return jsonify({"message": "Associated content deleted, but filesystem file deletion failed or file was already gone."}), 207 # Multi-Status
            return jsonify({"error": "Failed to delete file from filesystem"}), 500

    if associated_content_deleted and file_deleted_from_fs:
        return jsonify({"message": "File and associated content deleted successfully"}), 200
    elif file_deleted_from_fs:
        return jsonify({"message": "File deleted successfully from filesystem"}), 200
    elif associated_content_deleted: # File was not on FS, but content deleted
        return jsonify({"message": "Associated content deleted; file was not found on filesystem initially or already removed."}), 200
    else:
        # This case should ideally be caught by FileUploadHandler.delete_file failing
        return jsonify({"error": "File not found or could not be deleted, and no associated content processed"}), 404
