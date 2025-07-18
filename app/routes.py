# app/routes.py
import json
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy.exc import IntegrityError, SQLAlchemyError # Import specific exceptions
from app import db
from app.models import User, Kana, Kanji, Vocabulary, Grammar, LessonCategory, Lesson, LessonContent, LessonPrerequisite, UserLessonProgress, QuizQuestion, QuizOption, UserQuizAnswer, LessonPage, Course, LessonPurchase
from app.forms import RegistrationForm, LoginForm, CSRFTokenForm
from app.ai_services import AILessonContentGenerator
from app.lesson_export_import import (
    export_lesson_to_json, import_lesson_from_json, 
    create_lesson_export_package, import_lesson_from_zip
)
from functools import wraps # For custom decorators

# Helper function for JSON serialization
def model_to_dict(model_instance):
    """Converts a SQLAlchemy model instance to a dictionary."""
    d = {}
    for column in model_instance.__table__.columns:
        value = getattr(model_instance, column.name)
        # Handle datetime objects for JSON serialization
        if isinstance(value, datetime):
            d[column.name] = value.isoformat()
        else:
            d[column.name] = value
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
    # Get counts for the welcome page
    total_lessons = Lesson.query.filter_by(is_published=True).count()
    total_courses = Course.query.filter_by(is_published=True).count()
    
    # Get accessible lessons for guest users
    guest_accessible_lessons = Lesson.query.filter_by(
        is_published=True, 
        allow_guest_access=True, 
        lesson_type='free'
    ).count()
    
    return render_template('index.html', 
                         total_lessons=total_lessons,
                         total_courses=total_courses,
                         guest_accessible_lessons=guest_accessible_lessons)

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

@bp.route('/upgrade_to_premium', methods=['POST']) # Changed to POST
@login_required
def upgrade_to_premium():
    form = CSRFTokenForm()
    if form.validate_on_submit(): # Added CSRF validation
        # **PROTOTYPE ONLY**: Manually change subscription for testing
        current_user.subscription_level = 'premium'
        db.session.commit()
        flash('Congratulations! Your account has been upgraded to Premium.', 'success')
        return redirect(url_for('routes.index')) # Changed to a valid route
    else:
        flash('Invalid request for upgrade.', 'danger')
        return redirect(url_for('routes.index')) # Or a relevant page

@bp.route('/downgrade_from_premium', methods=['POST']) # Changed to POST
@login_required
def downgrade_from_premium():
    form = CSRFTokenForm()
    if form.validate_on_submit(): # Added CSRF validation
        # **PROTOTYPE ONLY**: Manually change subscription for testing
        current_user.subscription_level = 'free'
        db.session.commit()
        flash('Your account has been downgraded to Free.', 'info')
        return redirect(url_for('routes.index')) # Changed to a valid route
    else:
        flash('Invalid request for downgrade.', 'danger')
        return redirect(url_for('routes.index')) # Or a relevant page

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

@bp.route('/admin/manage/courses')
@login_required
@admin_required
def admin_manage_courses():
    form = CSRFTokenForm()
    return render_template('admin/manage_courses.html', form=form)

@bp.route('/admin/manage/approval')
@login_required
@admin_required
def admin_manage_approval():
    pending_kanji = Kanji.query.filter_by(status='pending_approval').all()
    pending_vocabulary = Vocabulary.query.filter_by(status='pending_approval').all()
    pending_grammar = Grammar.query.filter_by(status='pending_approval').all()
    return render_template('admin/manage_approval.html',
                           pending_kanji=pending_kanji,
                           pending_vocabulary=pending_vocabulary,
                           pending_grammar=pending_grammar)

# --- Lesson Routes for Users ---
@bp.route('/lessons')
def lessons():
    """Browse available lessons"""
    return render_template('lessons.html')

@bp.route('/courses')
def courses():
    """Browse available courses"""
    courses = Course.query.filter_by(is_published=True).all()
    return render_template('courses.html', courses=courses)

@bp.route('/course/<int:course_id>')
def view_course(course_id):
    """View a specific course"""
    course = Course.query.get_or_404(course_id)
    
    # Get user progress for all lessons in this course
    lesson_progress = {}
    total_lessons = len(course.lessons)
    completed_lessons = 0
    total_duration = 0
    
    for lesson in course.lessons:
        # Get user progress for this lesson
        progress = UserLessonProgress.query.filter_by(
            user_id=current_user.id, lesson_id=lesson.id
        ).first()
        
        lesson_progress[lesson.id] = progress
        
        # Count completed lessons for course progress
        if progress and progress.is_completed:
            completed_lessons += 1
            
        # Add to total duration
        if lesson.estimated_duration:
            total_duration += lesson.estimated_duration
    
    # Calculate overall course progress percentage
    course_progress_percentage = 0
    if total_lessons > 0:
        course_progress_percentage = int((completed_lessons / total_lessons) * 100)
    
    # Calculate average difficulty level
    difficulty_levels = [lesson.difficulty_level for lesson in course.lessons if lesson.difficulty_level]
    average_difficulty = 0
    if difficulty_levels:
        average_difficulty = sum(difficulty_levels) / len(difficulty_levels)
    
    # Determine if user has started the course
    has_started = any(progress for progress in lesson_progress.values())
    
    return render_template('course_view.html', 
                         course=course,
                         lesson_progress=lesson_progress,
                         course_progress_percentage=course_progress_percentage,
                         total_lessons=total_lessons,
                         completed_lessons=completed_lessons,
                         total_duration=total_duration,
                         average_difficulty=average_difficulty,
                         has_started=has_started)

@bp.route('/purchase/<int:lesson_id>')
@login_required
def purchase_lesson_page(lesson_id):
    """Display the purchase page for a lesson"""
    lesson = Lesson.query.get_or_404(lesson_id)
    
    # Check if lesson is purchasable
    if not lesson.is_purchasable or lesson.price <= 0:
        flash('This lesson is not available for purchase.', 'warning')
        return redirect(url_for('routes.lessons'))
    
    # Check if user already owns this lesson
    existing_purchase = LessonPurchase.query.filter_by(
        user_id=current_user.id, 
        lesson_id=lesson_id
    ).first()
    
    if existing_purchase:
        flash('You already own this lesson!', 'info')
        return redirect(url_for('routes.view_lesson', lesson_id=lesson_id))
    
    # Check if user can access this lesson for free (shouldn't happen, but safety check)
    accessible, message = lesson.is_accessible_to_user(current_user)
    if accessible:
        flash('This lesson is already accessible to you.', 'info')
        return redirect(url_for('routes.view_lesson', lesson_id=lesson_id))
    
    form = CSRFTokenForm()
    return render_template('purchase.html', lesson=lesson, form=form)

@bp.route('/lessons/<int:lesson_id>')
def view_lesson(lesson_id):
    """View a specific lesson"""
    lesson = Lesson.query.get_or_404(lesson_id)
    
    # Check if user can access this lesson (supports both authenticated and guest users)
    user = current_user if current_user.is_authenticated else None
    accessible, message = lesson.is_accessible_to_user(user)
    if not accessible:
        flash(message, 'warning')
        if not current_user.is_authenticated and 'Login required' in message:
            return redirect(url_for('routes.login', next=request.url))
        return redirect(url_for('routes.lessons'))
    
    # Get or create user progress (only for authenticated users)
    progress = None
    if current_user.is_authenticated:
        progress = UserLessonProgress.query.filter_by(
            user_id=current_user.id, lesson_id=lesson_id
        ).first()
        
        if not progress:
            try:
                progress = UserLessonProgress(user_id=current_user.id, lesson_id=lesson_id)
                db.session.add(progress)
                db.session.commit()
            except IntegrityError:
                # Another request might have created the record, rollback and try again
                db.session.rollback()
                progress = UserLessonProgress.query.filter_by(
                    user_id=current_user.id, lesson_id=lesson_id
                ).first()
                # If still not found, log the issue but continue without progress tracking
                if not progress:
                    current_app.logger.error(f"Failed to create or find progress record for user {current_user.id}, lesson {lesson_id}")
    
    # Get all quiz questions for this lesson
    quiz_questions = []
    for content in lesson.content_items:
        if content.is_interactive:
            quiz_questions.extend(content.quiz_questions)
    
    # Get user's existing quiz answers (only for authenticated users)
    user_quiz_answers = {}
    if current_user.is_authenticated and quiz_questions:
        question_ids = [q.id for q in quiz_questions]
        answers = UserQuizAnswer.query.filter(
            UserQuizAnswer.user_id == current_user.id,
            UserQuizAnswer.question_id.in_(question_ids)
        ).all()
        
        # Create a lookup dictionary: question_id -> UserQuizAnswer
        user_quiz_answers = {answer.question_id: answer for answer in answers}
    
    form = CSRFTokenForm()
    return render_template('lesson_view.html', lesson=lesson, progress=progress, form=form, user_quiz_answers=user_quiz_answers)

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

# == CONTENT APPROVAL API ==
@bp.route('/api/admin/content/<content_type>/<int:item_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_content(content_type, item_id):
    model = {'kanji': Kanji, 'vocabulary': Vocabulary, 'grammar': Grammar}.get(content_type)
    if not model:
        return jsonify({"error": "Invalid content type"}), 400
    
    item = model.query.get_or_404(item_id)
    item.status = 'approved'
    db.session.commit()
    return jsonify({"message": f"{content_type.capitalize()} item approved successfully"}), 200

@bp.route('/api/admin/content/<content_type>/<int:item_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_content(content_type, item_id):
    model = {'kanji': Kanji, 'vocabulary': Vocabulary, 'grammar': Grammar}.get(content_type)
    if not model:
        return jsonify({"error": "Invalid content type"}), 400
    
    item = model.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": f"{content_type.capitalize()} item rejected and deleted successfully"}), 200

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

# == COURSE CRUD API ==
@bp.route('/api/admin/courses', methods=['GET'])
@login_required
@admin_required
def list_courses():
    items = Course.query.all()
    return jsonify([model_to_dict(item) for item in items])

@bp.route('/api/admin/courses/new', methods=['POST'])
@login_required
@admin_required
def create_course():
    # Validate CSRF token from header
    from flask_wtf.csrf import validate_csrf
    try:
        csrf_token = request.headers.get('X-CSRFToken')
        if not csrf_token:
            return jsonify({"error": "CSRF token missing"}), 400
        validate_csrf(csrf_token)
    except Exception as e:
        return jsonify({"error": "CSRF token invalid"}), 400
    
    data = request.json
    if not data or not data.get('title'):
        return jsonify({"error": "Missing required field: title"}), 400

    new_item = Course(
        title=data['title'],
        description=data.get('description'),
        background_image_url=data.get('background_image_url'),
        is_published=data.get('is_published', False)
    )
    
    # Handle lesson assignments
    if 'lessons' in data:
        lesson_ids = data['lessons']
        for lesson_id in lesson_ids:
            lesson = Lesson.query.get(lesson_id)
            if lesson:
                new_item.lessons.append(lesson)
    
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

@bp.route('/api/admin/courses/<int:item_id>', methods=['GET'])
@login_required
@admin_required
def get_course(item_id):
    item = Course.query.get_or_404(item_id)
    course_dict = model_to_dict(item)
    course_dict['lessons'] = [model_to_dict(lesson) for lesson in item.lessons]
    return jsonify(course_dict)

@bp.route('/api/admin/courses/<int:item_id>/edit', methods=['PUT', 'PATCH'])
@login_required
@admin_required
def update_course(item_id):
    item = Course.query.get_or_404(item_id)
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    item.title = data.get('title', item.title)
    item.description = data.get('description', item.description)
    item.background_image_url = data.get('background_image_url', item.background_image_url)
    item.is_published = data.get('is_published', item.is_published)

    if 'lessons' in data:
        item.lessons = []
        for lesson_id in data['lessons']:
            lesson = Lesson.query.get(lesson_id)
            if lesson:
                item.lessons.append(lesson)

    db.session.commit()
    return jsonify(model_to_dict(item))

@bp.route('/api/admin/courses/<int:item_id>/delete', methods=['DELETE'])
@login_required
@admin_required
def delete_course(item_id):
    item = Course.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Course deleted successfully"}), 200

# == LESSON CRUD API ==
@bp.route('/api/admin/lessons', methods=['GET'])
@login_required
@admin_required
def list_lessons():
    items = Lesson.query.order_by(Lesson.order_index.asc(), Lesson.id.asc()).all()
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
        allow_guest_access=data.get('allow_guest_access', False),
        instruction_language=data.get('instruction_language', 'english'),
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
    
    # Use the updated `pages` property from the model
    pages_data = []
    for page in item.pages:
        page_info = {
            'page_number': page['content'][0].page_number if page['content'] else None,
            'content': [model_to_dict(c) for c in page['content']],
            'metadata': model_to_dict(page['metadata']) if page['metadata'] else None
        }
        if page_info['page_number'] is not None:
            pages_data.append(page_info)
    
    lesson_dict['pages'] = sorted(pages_data, key=lambda p: p['page_number'])
    lesson_dict['prerequisites'] = [model_to_dict(prereq.prerequisite_lesson) for prereq in item.prerequisites]
    
    # For backward compatibility or other uses, you might still want a flat list of content_items
    lesson_dict['content_items'] = [model_to_dict(content) for content in item.content_items]

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
    # Convert string 'on' to boolean for allow_guest_access
    allow_guest_access = data.get('allow_guest_access', item.allow_guest_access)
    if isinstance(allow_guest_access, str):
        item.allow_guest_access = allow_guest_access.lower() in ['true', 'on', '1', 'yes']
    else:
        item.allow_guest_access = bool(allow_guest_access) if allow_guest_access is not None else item.allow_guest_access
    item.instruction_language = data.get('instruction_language', item.instruction_language)
    item.thumbnail_url = data.get('thumbnail_url', item.thumbnail_url)
    item.video_intro_url = data.get('video_intro_url', item.video_intro_url)

    # Handle pricing fields
    if 'price' in data:
        try:
            price = float(data['price'])
            if price < 0:
                return jsonify({"error": "Price cannot be negative"}), 400
            item.price = price
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid price format"}), 400
    
    # Handle is_purchasable field
    is_purchasable = data.get('is_purchasable', item.is_purchasable)
    if isinstance(is_purchasable, str):
        item.is_purchasable = is_purchasable.lower() in ['true', 'on', '1', 'yes']
    else:
        item.is_purchasable = bool(is_purchasable) if is_purchasable is not None else item.is_purchasable

    # Handle course assignment
    if 'course_ids' in data:
        # Clear existing course relationships
        item.courses = []
        # Add new course relationships
        for course_id in data['course_ids']:
            course = Course.query.get(course_id)
            if course:
                item.courses.append(course)

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

@bp.route('/api/admin/lessons/<int:lesson_id>/move', methods=['POST'])
@login_required
@admin_required
def move_lesson(lesson_id):
    """Move a lesson up or down in order globally across all categories."""
    data = request.json
    direction = data.get('direction')
    if direction not in ['up', 'down']:
        return jsonify({"error": "Invalid direction specified"}), 400

    lesson_to_move = Lesson.query.get_or_404(lesson_id)
    
    # Get all lessons ordered by order_index globally (not by category)
    lessons = Lesson.query.order_by(Lesson.order_index, Lesson.id).all()
    
    # Find the current position of the lesson to move
    current_position = None
    for i, lesson in enumerate(lessons):
        if lesson.id == lesson_id:
            current_position = i
            break
    
    if current_position is None:
        return jsonify({"error": "Lesson not found"}), 404
    
    # Calculate new position
    if direction == 'up':
        if current_position == 0:
            return jsonify({"error": "Cannot move lesson further up"}), 400
        new_position = current_position - 1
    else:  # direction == 'down'
        if current_position == len(lessons) - 1:
            return jsonify({"error": "Cannot move lesson further down"}), 400
        new_position = current_position + 1
    
    # Reorder the list
    lesson_to_move_obj = lessons.pop(current_position)
    lessons.insert(new_position, lesson_to_move_obj)
    
    # Update order indices for all lessons globally
    try:
        for index, lesson in enumerate(lessons):
            lesson.order_index = index
        
        db.session.commit()
        current_app.logger.info(f"Lesson {lesson_id} moved {direction} globally")
        return jsonify({"message": "Lesson moved successfully"}), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error moving lesson: {e}")
        return jsonify({"error": "Database error occurred"}), 500

@bp.route('/api/admin/lessons/reorder', methods=['POST'])
@login_required
@admin_required
def reorder_lessons():
    """Reorder lessons based on provided order."""
    data = request.json
    lesson_ids = data.get('lesson_ids', [])
    category_id = data.get('category_id')  # Optional: reorder within specific category
    
    if not lesson_ids:
        return jsonify({"error": "No lesson IDs provided"}), 400
    
    try:
        # Get all lessons to reorder
        if category_id:
            lessons = Lesson.query.filter(
                Lesson.category_id == category_id,
                Lesson.id.in_(lesson_ids)
            ).all()
        else:
            lessons = Lesson.query.filter(Lesson.id.in_(lesson_ids)).all()
        
        # Create a mapping of ID to lesson
        lesson_map = {lesson.id: lesson for lesson in lessons}
        
        # Verify all provided IDs exist
        if len(lesson_map) != len(lesson_ids):
            return jsonify({"error": "Some lesson IDs not found"}), 404
        
        # Update order indices based on the provided order
        for index, lesson_id in enumerate(lesson_ids):
            lesson_map[lesson_id].order_index = index
        
        db.session.commit()
        current_app.logger.info(f"Reordered {len(lesson_ids)} lessons in category {category_id or 'All'}")
        return jsonify({"message": "Lessons reordered successfully"}), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error reordering lessons: {e}")
        return jsonify({"error": "Database error occurred"}), 500

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

    page_number = data.get('page_number', 1)

    # Ensure a LessonPage entry exists for this page
    lesson_page = LessonPage.query.filter_by(lesson_id=lesson_id, page_number=page_number).first()
    if not lesson_page:
        lesson_page = LessonPage(
            lesson_id=lesson_id, 
            page_number=page_number,
            title=f"Page {page_number}" # Default title
        )
        db.session.add(lesson_page)

    # Convert string 'false'/'true' to boolean for is_optional
    is_optional = data.get('is_optional', False)
    if isinstance(is_optional, str):
        is_optional = is_optional.lower() == 'true'

    # Determine the next order index for the given page
    last_content_on_page = LessonContent.query.filter_by(lesson_id=lesson_id, page_number=page_number).order_by(LessonContent.order_index.desc()).first()
    next_order_index = (last_content_on_page.order_index + 1) if last_content_on_page else 0

    new_content = LessonContent(
        lesson_id=lesson_id,
        content_type=data['content_type'],
        content_id=data.get('content_id'),
        title=data.get('title'),
        content_text=data.get('content_text'),
        media_url=data.get('media_url'),
        order_index=next_order_index,
        page_number=page_number,
        is_optional=is_optional
    )
    try:
        db.session.add(new_content)
        db.session.commit()
        return jsonify(model_to_dict(new_content)), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": f"Database error occurred: {str(e)}"}), 500

def reorder_page_content(lesson_id, page_number):
    """Reorder all content items on a specific page to maintain sequential order indices"""
    try:
        # Get all content items on the page, ordered by current order_index
        content_items = LessonContent.query.filter(
            LessonContent.lesson_id == lesson_id,
            LessonContent.page_number == page_number
        ).order_by(LessonContent.order_index, LessonContent.id).all()
        
        # Reassign order indices starting from 0
        for index, content_item in enumerate(content_items):
            old_order = content_item.order_index
            content_item.order_index = index
            current_app.logger.debug(f"Content {content_item.id}: {old_order} -> {index}")
        
        db.session.commit()
        current_app.logger.info(f"Reordered {len(content_items)} content items on page {page_number} to sequential indices 0-{len(content_items)-1}")
        
    except Exception as e:
        current_app.logger.error(f"Error reordering content on page {page_number}: {e}")
        db.session.rollback()
        raise e

def force_reorder_all_lesson_content(lesson_id):
    """Force reorder all content in a lesson to fix any gaps in order indices"""
    try:
        # Get all pages with content
        pages_with_content = db.session.query(LessonContent.page_number).filter(
            LessonContent.lesson_id == lesson_id
        ).distinct().all()
        
        for (page_number,) in pages_with_content:
            reorder_page_content(lesson_id, page_number)
        
        current_app.logger.info(f"Force reordered all content for lesson {lesson_id}")
        
    except Exception as e:
        current_app.logger.error(f"Error force reordering lesson {lesson_id}: {e}")

@bp.route('/api/admin/lessons/<int:lesson_id>/content/<int:content_id>/delete', methods=['DELETE'])
@login_required
@admin_required
def remove_lesson_content(lesson_id, content_id):
    content = LessonContent.query.filter_by(lesson_id=lesson_id, id=content_id).first_or_404()

    # Store content info for reordering before deletion
    content_page = content.page_number
    content_order = content.order_index

    try:
        # Delete file from disk if it exists
        file_deletion_success = True
        if content.file_path:
            try:
                content.delete_file()
                current_app.logger.info(f"File deleted successfully for content {content_id}")
            except Exception as file_error:
                current_app.logger.error(f"Failed to delete file for content {content_id}: {file_error}")
                file_deletion_success = False

        # Delete the content record from database
        db.session.delete(content)
        db.session.commit()
        
        current_app.logger.info(f"Content {content_id} deleted from lesson {lesson_id}, page {content_page}, order {content_order}")
        
        # Force complete reordering of the page to ensure sequential indices
        try:
            reorder_page_content(lesson_id, content_page)
            current_app.logger.info(f"Page {content_page} reordered after deletion")
        except Exception as reorder_error:
            current_app.logger.error(f"Error reordering page {content_page} after deletion: {reorder_error}")
            # Return an error to the client so the UI can show a proper message
            return jsonify({"error": f"Content was deleted, but reordering the page failed: {reorder_error}. Please refresh."}), 500
        
        if file_deletion_success:
            return jsonify({"message": "Content removed from lesson successfully"}), 200
        else:
            return jsonify({"message": "Content removed from lesson, but file deletion failed"}), 200
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error removing lesson content {content_id} from lesson {lesson_id}: {e}", exc_info=True)
        return jsonify({"error": f"Failed to remove lesson content: {str(e)}"}), 500

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
    page_number = content_to_move.page_number
    
    # Get all content items on the same page, ordered by current order_index
    content_items = LessonContent.query.filter(
        LessonContent.lesson_id == lesson_id,
        LessonContent.page_number == page_number
    ).order_by(LessonContent.order_index, LessonContent.id).all()
    
    # Find the current position of the item to move
    current_position = None
    for i, item in enumerate(content_items):
        if item.id == content_id:
            current_position = i
            break
    
    if current_position is None:
        return jsonify({"error": "Content item not found"}), 404
    
    # Calculate new position
    if direction == 'up':
        if current_position == 0:
            return jsonify({"error": "Cannot move item further up"}), 400
        new_position = current_position - 1
    else:  # direction == 'down'
        if current_position == len(content_items) - 1:
            return jsonify({"error": "Cannot move item further down"}), 400
        new_position = current_position + 1
    
    # Reorder the list
    item_to_move = content_items.pop(current_position)
    content_items.insert(new_position, item_to_move)
    
    # Update order indices for all items
    try:
        for index, item in enumerate(content_items):
            item.order_index = index
        
        db.session.commit()
        current_app.logger.info(f"Content {content_id} moved {direction} on page {page_number}")
        return jsonify({"message": "Content moved successfully"}), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error moving content: {e}")
        return jsonify({"error": "Database error occurred"}), 500

@bp.route('/api/admin/lessons/<int:lesson_id>/pages/<int:page_number>/reorder', methods=['POST'])
@login_required
@admin_required
def reorder_page_content_api(lesson_id, page_number):
    """Reorder content items on a page based on provided order."""
    data = request.json
    content_ids = data.get('content_ids', [])
    
    if not content_ids:
        return jsonify({"error": "No content IDs provided"}), 400
    
    try:
        # Get all content items for this page
        content_items = LessonContent.query.filter(
            LessonContent.lesson_id == lesson_id,
            LessonContent.page_number == page_number,
            LessonContent.id.in_(content_ids)
        ).all()
        
        # Create a mapping of ID to content item
        content_map = {item.id: item for item in content_items}
        
        # Verify all provided IDs exist
        if len(content_map) != len(content_ids):
            return jsonify({"error": "Some content IDs not found"}), 404
        
        # Update order indices based on the provided order
        for index, content_id in enumerate(content_ids):
            content_map[content_id].order_index = index
        
        db.session.commit()
        current_app.logger.info(f"Reordered {len(content_ids)} items on page {page_number} of lesson {lesson_id}")
        return jsonify({"message": "Content reordered successfully"}), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error reordering content: {e}")
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
        
        # Group content by page for reordering
        pages_to_reorder = set()
        
        for content in content_items:
            pages_to_reorder.add(content.page_number)
            # Delete associated files if any
            if hasattr(content, 'delete_file'):
                content.delete_file()
            db.session.delete(content)
        
        db.session.commit()
        
        # Reorder content on affected pages
        for page_number in pages_to_reorder:
            reorder_page_content(lesson_id, page_number)
        
        return jsonify({"message": f"Deleted {deleted_count} content items"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to delete content"}), 500

@bp.route('/api/admin/lessons/<int:lesson_id>/content/force-reorder', methods=['POST'])
@login_required
@admin_required
def force_reorder_lesson_content(lesson_id):
    """Force reorder all content in a lesson to fix gaps in order indices"""
    lesson = Lesson.query.get_or_404(lesson_id)
    
    try:
        force_reorder_all_lesson_content(lesson_id)
        return jsonify({"message": "All content reordered successfully"}), 200
        
    except Exception as e:
        current_app.logger.error(f"Error force reordering lesson {lesson_id}: {e}")
        return jsonify({"error": "Failed to reorder content"}), 500

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
    """Deletes a page, its metadata, and all its content items from a lesson."""
    # Also delete the page metadata
    page_metadata = LessonPage.query.filter_by(lesson_id=lesson_id, page_number=page_num).first()
    if page_metadata:
        db.session.delete(page_metadata)

    content_to_delete = LessonContent.query.filter_by(lesson_id=lesson_id, page_number=page_num).all()
    
    if not content_to_delete and not page_metadata:
        return jsonify({"error": "Page not found"}), 404
    
    try:
        for content in content_to_delete:
            if content.file_path:
                content.delete_file()
            db.session.delete(content)
        
        db.session.commit()
        return jsonify({"message": f"Page {page_num} and its content deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting page {page_num} from lesson {lesson_id}: {e}")
        return jsonify({"error": "Failed to delete page"}), 500

@bp.route('/api/admin/lessons/<int:lesson_id>/pages/<int:page_num>', methods=['PUT'])
@login_required
@admin_required
def update_lesson_page(lesson_id, page_num):
    """Update page title and description."""
    data = request.json
    current_app.logger.info(f"Updating page {page_num} for lesson {lesson_id} with data: {data}")
    
    page = LessonPage.query.filter_by(lesson_id=lesson_id, page_number=page_num).first()
    
    if not page:
        current_app.logger.error(f"Page {page_num} not found for lesson {lesson_id}")
        # If page doesn't exist, create it
        page = LessonPage(
            lesson_id=lesson_id,
            page_number=page_num,
            title=data.get('title', f'Page {page_num}'),
            description=data.get('description', '')
        )
        db.session.add(page)
        current_app.logger.info(f"Created new page {page_num} for lesson {lesson_id}")
    else:
        if data:
            page.title = data.get('title', page.title)
            page.description = data.get('description', page.description)
            current_app.logger.info(f"Updating existing page {page_num} for lesson {lesson_id}")

    try:
        db.session.commit()
        current_app.logger.info(f"Successfully committed changes for page {page_num}")
        return jsonify(model_to_dict(page)), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error occurred while updating page {page_num}: {str(e)}", exc_info=True)
        return jsonify({"error": f"Database error occurred: {str(e)}"}), 500
    except Exception as e:
        current_app.logger.error(f"An unexpected error occurred: {str(e)}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred"}), 500

# == USER LESSON API ==
@bp.route('/api/lessons', methods=['GET'])
def get_user_lessons():
    """Get lessons accessible to the current user or guest, with optional filtering."""
    instruction_language = request.args.get('instruction_language')
    
    query = Lesson.query.filter_by(is_published=True)
    
    if instruction_language and instruction_language.lower() != 'all':
        query = query.filter(Lesson.instruction_language == instruction_language)
        
    lessons = query.order_by(Lesson.order_index.asc(), Lesson.id.asc()).all()
    
    accessible_lessons = []
    user = current_user if current_user.is_authenticated else None
    
    for lesson in lessons:
        accessible, message = lesson.is_accessible_to_user(user)
        lesson_dict = model_to_dict(lesson)
        lesson_dict['accessible'] = accessible
        lesson_dict['access_message'] = message
        lesson_dict['category_name'] = lesson.category.name if lesson.category else None
        
        # Add background image information
        lesson_dict['background_image_url'] = lesson.background_image_url
        lesson_dict['background_image_path'] = lesson.background_image_path
        
        # Get user progress if exists (only for authenticated users)
        progress = None
        if current_user.is_authenticated:
            progress = UserLessonProgress.query.filter_by(
                user_id=current_user.id, lesson_id=lesson.id
            ).first()
        lesson_dict['progress'] = model_to_dict(progress) if progress else None
        
        accessible_lessons.append(lesson_dict)
    
    return jsonify(accessible_lessons)

@bp.route('/api/courses', methods=['GET'])
def get_courses():
    """Get all courses"""
    courses = Course.query.filter_by(is_published=True).all()
    return jsonify([model_to_dict(course) for course in courses])

@bp.route('/api/categories', methods=['GET'])
def get_public_categories():
    """Get categories for public use (no admin required)"""
    try:
        categories = LessonCategory.query.all()
        return jsonify([model_to_dict(category) for category in categories])
    except Exception as e:
        current_app.logger.error(f"Error fetching public categories: {e}")
        return jsonify([]), 200  # Return empty array on error

@bp.route('/api/lessons/<int:lesson_id>/reset', methods=['POST'])
@login_required
def reset_lesson_progress_api(lesson_id):
    """Reset user progress for a lesson via API"""
    lesson = Lesson.query.get_or_404(lesson_id)
    
    # Check access
    accessible, message = lesson.is_accessible_to_user(current_user)
    if not accessible:
        return jsonify({"error": message}), 403
    
    try:
        from sqlalchemy import text
        
        current_app.logger.info(f"API reset starting for user {current_user.id}, lesson {lesson_id}")
        
        progress = UserLessonProgress.query.filter_by(
            user_id=current_user.id, lesson_id=lesson_id
        ).first()

        if progress:
            current_app.logger.info(f"Found progress record for user {current_user.id}, lesson {lesson_id}")
            
            # Get interactive content IDs using direct SQL to avoid lazy loading
            interactive_content_sql = text("""
                SELECT id FROM lesson_content 
                WHERE lesson_id = :lesson_id AND is_interactive = true
            """)
            
            interactive_content_result = db.session.execute(interactive_content_sql, {
                'lesson_id': lesson_id
            })
            content_ids = [row[0] for row in interactive_content_result]
            current_app.logger.info(f"Found {len(content_ids)} interactive content items")
            
            if content_ids:
                # Get question IDs for these content items - fix PostgreSQL array syntax
                question_ids_sql = text("""
                    SELECT id FROM quiz_question 
                    WHERE lesson_content_id IN :content_ids
                """)
                
                question_result = db.session.execute(question_ids_sql, {
                    'content_ids': tuple(content_ids)
                })
                question_ids = [row[0] for row in question_result]
                current_app.logger.info(f"Found {len(question_ids)} quiz questions")
                
                if question_ids:
                    # Delete quiz answers using direct SQL - fix PostgreSQL array syntax
                    delete_answers_sql = text("""
                        DELETE FROM user_quiz_answer 
                        WHERE user_id = :user_id AND question_id IN :question_ids
                    """)
                    
                    result = db.session.execute(delete_answers_sql, {
                        'user_id': current_user.id,
                        'question_ids': tuple(question_ids)
                    })
                    current_app.logger.info(f"Deleted {result.rowcount} quiz answers")
            
            # Reset progress using direct SQL
            reset_progress_sql = text("""
                UPDATE user_lesson_progress 
                SET completed_at = NULL,
                    is_completed = false,
                    progress_percentage = 0,
                    time_spent = 0,
                    content_progress = '{}'
                WHERE user_id = :user_id AND lesson_id = :lesson_id
            """)
            
            result = db.session.execute(reset_progress_sql, {
                'user_id': current_user.id,
                'lesson_id': lesson_id
            })
            current_app.logger.info(f"Updated {result.rowcount} progress records")
            
            db.session.commit()
            current_app.logger.info(f"Successfully reset progress for user {current_user.id}, lesson {lesson_id}")
            
            # Refresh the progress object and return it
            db.session.refresh(progress)
            return jsonify({
                "success": True,
                "message": "Progress reset successfully",
                "progress": model_to_dict(progress)
            })
        else:
            current_app.logger.info(f"No progress found for user {current_user.id}, lesson {lesson_id}")
            return jsonify({
                "success": True,
                "message": "No progress found for this lesson",
                "progress": None
            })
            
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"SQLAlchemy error resetting lesson progress for user {current_user.id}, lesson {lesson_id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to reset progress. Please try again."}), 500
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Unexpected error resetting lesson progress for user {current_user.id}, lesson {lesson_id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to reset progress. Please try again."}), 500

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
    
    try:
        # Use a completely different approach: direct SQL updates to avoid session conflicts
        from sqlalchemy import text
        
        # First, try to get existing progress record
        progress = UserLessonProgress.query.filter_by(
            user_id=current_user.id, lesson_id=lesson_id
        ).first()
        
        if not progress:
            # Use INSERT ... ON CONFLICT to handle race conditions at database level
            insert_sql = text("""
                INSERT INTO user_lesson_progress (user_id, lesson_id, started_at, last_accessed, progress_percentage, time_spent, content_progress, is_completed)
                VALUES (:user_id, :lesson_id, :now, :now, 0, 0, '{}', false)
                ON CONFLICT (user_id, lesson_id) DO NOTHING
                RETURNING id
            """)
            
            result = db.session.execute(insert_sql, {
                'user_id': current_user.id,
                'lesson_id': lesson_id,
                'now': datetime.utcnow()
            })
            
            db.session.commit()
            
            # Now get the progress record (either newly created or existing)
            progress = UserLessonProgress.query.filter_by(
                user_id=current_user.id, lesson_id=lesson_id
            ).first()
            
            if not progress:
                return jsonify({"error": "Failed to create or find progress record"}), 500
        
        # Update progress fields using direct SQL to avoid session conflicts
        if data and 'content_id' in data:
            # Get current content progress
            content_progress = progress.get_content_progress()
            content_progress[str(data['content_id'])] = True
            
            # Calculate progress percentage manually
            total_content = db.session.query(db.func.count(LessonContent.id)).filter_by(lesson_id=lesson_id).scalar()
            if total_content > 0:
                completed_content = len([k for k, v in content_progress.items() if v])
                new_progress_percentage = int((completed_content / total_content) * 100)
                is_completed = new_progress_percentage == 100
                completed_at = datetime.utcnow() if is_completed and not progress.is_completed else progress.completed_at
            else:
                new_progress_percentage = 0
                is_completed = False
                completed_at = progress.completed_at
            
            # Use direct SQL update to avoid session conflicts
            update_sql = text("""
                UPDATE user_lesson_progress 
                SET content_progress = :content_progress,
                    progress_percentage = :progress_percentage,
                    is_completed = :is_completed,
                    completed_at = :completed_at,
                    last_accessed = :last_accessed,
                    time_spent = time_spent + :additional_time
                WHERE user_id = :user_id AND lesson_id = :lesson_id
            """)
            
            additional_time = data.get('time_spent', 0) if data else 0
            
            db.session.execute(update_sql, {
                'content_progress': json.dumps(content_progress),
                'progress_percentage': new_progress_percentage,
                'is_completed': is_completed,
                'completed_at': completed_at,
                'last_accessed': datetime.utcnow(),
                'additional_time': additional_time,
                'user_id': current_user.id,
                'lesson_id': lesson_id
            })
            
        elif data and 'time_spent' in data:
            # Just update time spent and last accessed
            update_sql = text("""
                UPDATE user_lesson_progress 
                SET time_spent = time_spent + :additional_time,
                    last_accessed = :last_accessed
                WHERE user_id = :user_id AND lesson_id = :lesson_id
            """)
            
            db.session.execute(update_sql, {
                'additional_time': data['time_spent'],
                'last_accessed': datetime.utcnow(),
                'user_id': current_user.id,
                'lesson_id': lesson_id
            })
        else:
            # Just update last accessed
            update_sql = text("""
                UPDATE user_lesson_progress 
                SET last_accessed = :last_accessed
                WHERE user_id = :user_id AND lesson_id = :lesson_id
            """)
            
            db.session.execute(update_sql, {
                'last_accessed': datetime.utcnow(),
                'user_id': current_user.id,
                'lesson_id': lesson_id
            })
        
        db.session.commit()
        
        # Refresh the progress object and return it
        db.session.refresh(progress)
        return jsonify(model_to_dict(progress))
        
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating lesson progress for user {current_user.id}, lesson {lesson_id}: {e}")
        return jsonify({"error": "Failed to update progress"}), 500

@bp.route('/lessons/<int:lesson_id>/reset', methods=['POST'])
@login_required
def reset_lesson_progress(lesson_id):
    """Reset user progress for a specific lesson."""
    form = CSRFTokenForm() # Instantiate the form
    if form.validate_on_submit(): # Validate CSRF token
        try:
            # Use direct SQL to avoid session conflicts, similar to update_lesson_progress
            from sqlalchemy import text
            
            current_app.logger.info(f"Starting reset for user {current_user.id}, lesson {lesson_id}")
            
            progress = UserLessonProgress.query.filter_by(
                user_id=current_user.id, lesson_id=lesson_id
            ).first()

            if progress:
                current_app.logger.info(f"Found progress record for user {current_user.id}, lesson {lesson_id}")
                
                # Get interactive content IDs using direct SQL to avoid lazy loading
                interactive_content_sql = text("""
                    SELECT id FROM lesson_content 
                    WHERE lesson_id = :lesson_id AND is_interactive = true
                """)
                
                interactive_content_result = db.session.execute(interactive_content_sql, {
                    'lesson_id': lesson_id
                })
                content_ids = [row[0] for row in interactive_content_result]
                current_app.logger.info(f"Found {len(content_ids)} interactive content items")
                
                if content_ids:
                    # Get question IDs for these content items - fix PostgreSQL array syntax
                    question_ids_sql = text("""
                        SELECT id FROM quiz_question 
                        WHERE lesson_content_id IN :content_ids
                    """)
                    
                    question_result = db.session.execute(question_ids_sql, {
                        'content_ids': tuple(content_ids)
                    })
                    question_ids = [row[0] for row in question_result]
                    current_app.logger.info(f"Found {len(question_ids)} quiz questions")
                    
                    if question_ids:
                        # Delete quiz answers using direct SQL - fix PostgreSQL array syntax
                        delete_answers_sql = text("""
                            DELETE FROM user_quiz_answer 
                            WHERE user_id = :user_id AND question_id IN :question_ids
                        """)
                        
                        result = db.session.execute(delete_answers_sql, {
                            'user_id': current_user.id,
                            'question_ids': tuple(question_ids)
                        })
                        current_app.logger.info(f"Deleted {result.rowcount} quiz answers")
                
                # Reset progress using direct SQL
                reset_progress_sql = text("""
                    UPDATE user_lesson_progress 
                    SET completed_at = NULL,
                        is_completed = false,
                        progress_percentage = 0,
                        time_spent = 0,
                        content_progress = '{}'
                    WHERE user_id = :user_id AND lesson_id = :lesson_id
                """)
                
                result = db.session.execute(reset_progress_sql, {
                    'user_id': current_user.id,
                    'lesson_id': lesson_id
                })
                current_app.logger.info(f"Updated {result.rowcount} progress records")
                
                db.session.commit()
                current_app.logger.info(f"Successfully reset progress for user {current_user.id}, lesson {lesson_id}")
                flash('Your progress for this lesson has been reset.', 'success')
            else:
                current_app.logger.info(f"No progress found for user {current_user.id}, lesson {lesson_id}")
                flash('No progress found for this lesson.', 'info')
                
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"SQLAlchemy error resetting lesson progress for user {current_user.id}, lesson {lesson_id}: {e}", exc_info=True)
            flash('Failed to reset progress. Please try again.', 'danger')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error resetting lesson progress for user {current_user.id}, lesson {lesson_id}: {e}", exc_info=True)
            flash('Failed to reset progress. Please try again.', 'danger')
    else:
        # This case implies a CSRF validation failure or other form error
        current_app.logger.error(f"CSRF validation failed for reset request from user {current_user.id}, lesson {lesson_id}")
        flash('Invalid request to reset progress.', 'danger')

    return redirect(url_for('routes.view_lesson', lesson_id=lesson_id))

# == LESSON PRICING AND PURCHASE API ==
@bp.route('/api/lessons/<int:lesson_id>/purchase', methods=['POST'])
@login_required
def purchase_lesson(lesson_id):
    """Purchase a lesson (MVP with mock payment)"""
    lesson = Lesson.query.get_or_404(lesson_id)
    
    # Validate that the lesson is purchasable
    if not lesson.is_purchasable or lesson.price <= 0:
        return jsonify({"error": "This lesson is not available for purchase"}), 400
    
    # Check if user already owns this lesson
    existing_purchase = LessonPurchase.query.filter_by(
        user_id=current_user.id, 
        lesson_id=lesson_id
    ).first()
    
    if existing_purchase:
        return jsonify({"error": "You already own this lesson"}), 400
    
    try:
        # Create purchase record (MVP: instant purchase without payment processing)
        purchase = LessonPurchase(
            user_id=current_user.id,
            lesson_id=lesson_id,
            price_paid=lesson.price,
            purchased_at=datetime.utcnow(),
            stripe_payment_intent_id=None  # Will be used for future Stripe integration
        )
        
        db.session.add(purchase)
        db.session.commit()
        
        current_app.logger.info(f"User {current_user.id} purchased lesson {lesson_id} for CHF {lesson.price}")
        
        return jsonify({
            "success": True,
            "message": f"Successfully purchased '{lesson.title}' for CHF {lesson.price:.2f}",
            "purchase_id": purchase.id,
            "lesson_id": lesson_id,
            "price_paid": lesson.price
        }), 201
        
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Error purchasing lesson {lesson_id} for user {current_user.id}: {e}")
        return jsonify({"error": "Purchase failed. Please try again."}), 500

@bp.route('/api/user/purchases', methods=['GET'])
@login_required
def get_user_purchases():
    """Get all purchases for the current user"""
    purchases = LessonPurchase.query.filter_by(user_id=current_user.id).all()
    
    purchases_data = []
    for purchase in purchases:
        purchase_dict = model_to_dict(purchase)
        purchase_dict['lesson_title'] = purchase.lesson.title
        purchase_dict['lesson_description'] = purchase.lesson.description
        purchases_data.append(purchase_dict)
    
    return jsonify(purchases_data)

@bp.route('/api/lessons/<int:lesson_id>/purchase-status', methods=['GET'])
@login_required
def get_lesson_purchase_status(lesson_id):
    """Check if user has purchased a specific lesson"""
    lesson = Lesson.query.get_or_404(lesson_id)
    
    purchase = LessonPurchase.query.filter_by(
        user_id=current_user.id, 
        lesson_id=lesson_id
    ).first()
    
    return jsonify({
        "lesson_id": lesson_id,
        "is_purchased": purchase is not None,
        "purchase_date": purchase.purchased_at.isoformat() if purchase else None,
        "price_paid": purchase.price_paid if purchase else None,
        "current_price": lesson.price,
        "is_purchasable": lesson.is_purchasable
    })

# == ADMIN PURCHASE MANAGEMENT API ==
@bp.route('/api/admin/purchases', methods=['GET'])
@login_required
@admin_required
def list_all_purchases():
    """Get all purchases for admin review"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    purchases = LessonPurchase.query.order_by(LessonPurchase.purchased_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    purchases_data = []
    for purchase in purchases.items:
        purchase_dict = model_to_dict(purchase)
        purchase_dict['user_username'] = purchase.user.username
        purchase_dict['user_email'] = purchase.user.email
        purchase_dict['lesson_title'] = purchase.lesson.title
        purchases_data.append(purchase_dict)
    
    return jsonify({
        "purchases": purchases_data,
        "total": purchases.total,
        "pages": purchases.pages,
        "current_page": purchases.page,
        "per_page": purchases.per_page
    })

@bp.route('/api/admin/lessons/<int:lesson_id>/purchases', methods=['GET'])
@login_required
@admin_required
def get_lesson_purchases(lesson_id):
    """Get all purchases for a specific lesson"""
    lesson = Lesson.query.get_or_404(lesson_id)
    
    purchases = LessonPurchase.query.filter_by(lesson_id=lesson_id).order_by(
        LessonPurchase.purchased_at.desc()
    ).all()
    
    purchases_data = []
    for purchase in purchases:
        purchase_dict = model_to_dict(purchase)
        purchase_dict['user_username'] = purchase.user.username
        purchase_dict['user_email'] = purchase.user.email
        purchases_data.append(purchase_dict)
    
    return jsonify({
        "lesson_id": lesson_id,
        "lesson_title": lesson.title,
        "total_purchases": len(purchases),
        "total_revenue": sum(p.price_paid for p in purchases),
        "purchases": purchases_data
    })

@bp.route('/api/admin/revenue-stats', methods=['GET'])
@login_required
@admin_required
def get_revenue_stats():
    """Get revenue statistics for admin dashboard"""
    from sqlalchemy import func
    
    # Total revenue
    total_revenue = db.session.query(func.sum(LessonPurchase.price_paid)).scalar() or 0
    
    # Total purchases
    total_purchases = LessonPurchase.query.count()
    
    # Revenue by lesson
    lesson_revenue = db.session.query(
        Lesson.title,
        Lesson.id,
        func.count(LessonPurchase.id).label('purchase_count'),
        func.sum(LessonPurchase.price_paid).label('revenue')
    ).join(LessonPurchase).group_by(Lesson.id, Lesson.title).all()
    
    # Recent purchases (last 30 days)
    from datetime import timedelta
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_revenue = db.session.query(func.sum(LessonPurchase.price_paid)).filter(
        LessonPurchase.purchased_at >= thirty_days_ago
    ).scalar() or 0
    
    recent_purchases = LessonPurchase.query.filter(
        LessonPurchase.purchased_at >= thirty_days_ago
    ).count()
    
    return jsonify({
        "total_revenue": float(total_revenue),
        "total_purchases": total_purchases,
        "recent_revenue_30d": float(recent_revenue),
        "recent_purchases_30d": recent_purchases,
        "average_price": float(total_revenue / total_purchases) if total_purchases > 0 else 0,
        "lesson_revenue": [
            {
                "lesson_id": lesson_id,
                "lesson_title": title,
                "purchase_count": purchase_count,
                "revenue": float(revenue)
            }
            for title, lesson_id, purchase_count, revenue in lesson_revenue
        ]
    })

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
        question = QuizQuestion.query.filter_by(id=question_id).first()

        if not question:
            return jsonify({"error": "Question not found"}), 404
        
        # Check if question belongs to lesson through its content
        if not question.content or question.content.lesson_id != lesson_id:
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

        elif question.question_type == 'matching':
            submitted_pairs = data.get('pairs', [])
            if not submitted_pairs:
                return jsonify({"error": "No pairs submitted for matching question"}), 400

            # Build correct answers mapping from question options
            # option_text contains the prompt, feedback contains the correct answer
            correct_options = {opt.option_text: opt.feedback for opt in question.options}
            
            correct_matches = 0
            total_pairs = len(correct_options)
            
            # Check each submitted pair against correct answers
            for pair in submitted_pairs:
                prompt = pair.get('prompt')
                user_answer = pair.get('answer')
                correct_answer = correct_options.get(prompt)
                
                current_app.logger.info(f"Checking pair - Prompt: '{prompt}', User Answer: '{user_answer}', Correct Answer: '{correct_answer}'")
                
                if correct_answer and user_answer == correct_answer:
                    correct_matches += 1
            
            # All pairs must be correct for the answer to be marked as correct
            is_correct = correct_matches == total_pairs
            answer.is_correct = is_correct
            answer.text_answer = json.dumps(submitted_pairs)  # Store user's answer
            
            current_app.logger.info(f"Matching question result - Correct matches: {correct_matches}/{total_pairs}, Is correct: {is_correct}")

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

# == AI CONTENT GENERATION API ==
@bp.route('/api/admin/generate-ai-content', methods=['POST'])
@login_required
@admin_required
def generate_ai_content():
    """
    Handles requests for AI-generated lesson content.
    This is a proxy to the AILessonContentGenerator service.
    """
    data = request.json
    if not data or 'content_type' not in data:
        return jsonify({"error": "Missing 'content_type' in request"}), 400

    generator = AILessonContentGenerator()
    content_type = data.get('content_type')
    topic = data.get('topic', 'General Japanese')
    difficulty = data.get('difficulty', 'Beginner')
    keywords = data.get('keywords', 'N/A')

    result = None
    if content_type == "explanation":
        result = generator.generate_explanation(topic, difficulty, keywords)
    elif content_type == "formatted_explanation":
        result = generator.generate_formatted_explanation(topic, difficulty, keywords)
    elif content_type == "multiple_choice_question":
        result = generator.generate_multiple_choice_question(topic, difficulty, keywords)
    elif content_type == "true_false_question":
        result = generator.generate_true_false_question(topic, difficulty, keywords)
    elif content_type == "fill_blank_question":
        result = generator.generate_fill_in_the_blank_question(topic, difficulty, keywords)
    elif content_type == "matching_question":
        result = generator.generate_matching_question(topic, difficulty, keywords)
    else:
        return jsonify({"error": "Unsupported content type"}), 400

    if "error" in result:
        return jsonify(result), 500

    return jsonify(result)

@bp.route('/api/admin/generate-ai-image', methods=['POST'])
@login_required
@admin_required
def generate_ai_image():
    """Generate AI images for lesson content using DALL-E."""
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    generator = AILessonContentGenerator()
    
    # Handle different types of image generation requests
    if 'prompt' in data:
        # Direct prompt generation
        result = generator.generate_single_image(
            prompt=data['prompt'],
            size=data.get('size', '1024x1024'),
            quality=data.get('quality', 'standard')
        )
    elif 'content_text' in data:
        # Generate prompt from content, then generate image
        lesson_topic = data.get('lesson_topic', 'Japanese Language Learning')
        difficulty = data.get('difficulty', 'Beginner')
        
        # First generate optimized prompt
        prompt_result = generator.generate_image_prompt(
            data['content_text'], lesson_topic, difficulty
        )
        
        if 'error' in prompt_result:
            return jsonify(prompt_result), 500
        
        # Then generate image
        result = generator.generate_single_image(
            prompt=prompt_result['image_prompt'],
            size=data.get('size', '1024x1024'),
            quality=data.get('quality', 'standard')
        )
        result['generated_prompt'] = prompt_result['image_prompt']
    else:
        return jsonify({"error": "Either 'prompt' or 'content_text' must be provided"}), 400

    if "error" in result:
        return jsonify(result), 500

    return jsonify(result)

@bp.route('/api/admin/analyze-multimedia-needs', methods=['POST'])
@login_required
@admin_required
def analyze_multimedia_needs():
    """Analyze lesson content and suggest multimedia enhancements."""
    data = request.json
    if not data or 'content_text' not in data:
        return jsonify({"error": "Missing 'content_text' in request"}), 400

    generator = AILessonContentGenerator()
    lesson_topic = data.get('lesson_topic', 'Japanese Language Learning')
    
    result = generator.analyze_content_for_multimedia_needs(
        data['content_text'], lesson_topic
    )

    if "error" in result:
        return jsonify(result), 500

    return jsonify(result)

@bp.route('/api/admin/generate-lesson-images', methods=['POST'])
@login_required
@admin_required
def generate_lesson_images():
    """Generate multiple images for lesson content."""
    data = request.json
    if not data or 'lesson_content' not in data:
        return jsonify({"error": "Missing 'lesson_content' in request"}), 400

    generator = AILessonContentGenerator()
    lesson_topic = data.get('lesson_topic', 'Japanese Language Learning')
    difficulty = data.get('difficulty', 'Beginner')
    
    result = generator.generate_lesson_images(
        data['lesson_content'], lesson_topic, difficulty
    )

    if "error" in result:
        return jsonify(result), 500

    return jsonify(result)

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
    
    file_path_from_request = data['file_path'] # Renamed for clarity
    content_id = data.get('content_id')

    # Path validation against UPLOAD_FOLDER
    full_request_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file_path_from_request)
    if not os.path.abspath(full_request_path).startswith(os.path.abspath(current_app.config['UPLOAD_FOLDER'])):
        return jsonify({"error": "Access denied: Invalid file path."}), 403

    file_system_deleted = False
    database_record_deleted = False
    message = ""

    if content_id:
        content = LessonContent.query.get(content_id)
        if not content:
            return jsonify({"error": f"Content with ID {content_id} not found."}), 404

        # If content_id is given, we primarily care about its associated file.
        if content.file_path:
            # Validate that the file_path from request (if provided) matches the content's file_path
            # This is an important security/consistency check.
            if file_path_from_request != content.file_path:
                return jsonify({"error": "File path mismatch. The provided file_path does not match the file associated with the content ID."}), 400

            # Attempt to delete the file associated with the content record
            if content.delete_file(): # This now returns True/False
                file_system_deleted = True
                current_app.logger.info(f"File {content.file_path} for content ID {content_id} deleted from filesystem by content.delete_file().")
            else:
                # content.delete_file() failed (e.g., os.remove error)
                # Check if the file still exists; it might have been deleted by another process or never existed
                content_file_full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], content.file_path)
                if not os.path.exists(content_file_full_path):
                    file_system_deleted = True # File is gone, treat as success for this part
                    current_app.logger.info(f"File {content.file_path} for content ID {content_id} was already absent from filesystem.")
                else:
                    current_app.logger.error(f"Failed to delete file {content.file_path} for content ID {content_id} from filesystem.")
        else:
            # Content exists but has no associated file_path in DB.
            # This means there's nothing to delete from the filesystem for this content.
            # If file_path_from_request was provided, it's an orphaned file or incorrect request.
            # We will not delete file_path_from_request in this case to avoid accidental deletion.
            current_app.logger.info(f"Content ID {content_id} has no associated file_path in DB. No file system deletion attempted for this content object.")
            # Consider file_system_deleted as true in the sense that there's no file to delete for this content.
            file_system_deleted = True # Or specific message indicating no file was associated.

        # Delete the content database record
        db.session.delete(content)
        db.session.commit()
        database_record_deleted = True
        message = f"Content ID {content_id} and its associations deleted from database. "

        if file_system_deleted:
            message += "Associated file handled successfully."
            return jsonify({"message": message}), 200
        else:
            message += "Associated file could not be deleted from filesystem or was not found."
            return jsonify({"message": message}), 207 # Multi-Status: DB deleted, file system issue

    else:
        # No content_id provided, this is a request to delete a file directly by its path.
        # This case should be used cautiously. Ensure the file is not still referenced by any LessonContent.
        # For now, we will proceed with deleting the file if it exists.
        # A more robust system might check if this file_path_from_request is referenced in any LessonContent.file_path.
        if not os.path.exists(full_request_path):
            return jsonify({"error": "File not found at the specified path."}), 404

        if FileUploadHandler.delete_file(full_request_path): # This is app.utils.FileUploadHandler.delete_file
            file_system_deleted = True
            message = f"File {file_path_from_request} deleted successfully from filesystem."
            return jsonify({"message": message}), 200
        else:
            message = f"Failed to delete file {file_path_from_request} from filesystem."
            return jsonify({"error": message}), 500

# == LESSON EXPORT/IMPORT API ==
@bp.route('/api/admin/lessons/<int:lesson_id>/export', methods=['GET'])
@login_required
@admin_required
def export_lesson(lesson_id):
    """Export a lesson to JSON format"""
    try:
        include_files = request.args.get('include_files', 'true').lower() == 'true'
        lesson_data = export_lesson_to_json(lesson_id, include_files)
        
        # Set appropriate headers for download
        from flask import make_response
        response = make_response(jsonify(lesson_data))
        response.headers['Content-Disposition'] = f'attachment; filename=lesson_{lesson_id}_export.json'
        response.headers['Content-Type'] = 'application/json'
        
        return response
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        current_app.logger.error(f"Error exporting lesson {lesson_id}: {e}")
        return jsonify({"error": "Failed to export lesson"}), 500

@bp.route('/api/admin/lessons/<int:lesson_id>/export-package', methods=['POST'])
@login_required
@admin_required
def export_lesson_package(lesson_id):
    """Create a complete export package as ZIP file"""
    try:
        data = request.json or {}
        include_files = data.get('include_files', True)
        
        # Create temporary export directory
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = create_lesson_export_package(lesson_id, temp_dir, include_files)
            
            # Read the ZIP file and return it
            with open(zip_path, 'rb') as f:
                zip_data = f.read()
            
            from flask import make_response
            response = make_response(zip_data)
            response.headers['Content-Type'] = 'application/zip'
            response.headers['Content-Disposition'] = f'attachment; filename={os.path.basename(zip_path)}'
            
            return response
            
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        current_app.logger.error(f"Error creating export package for lesson {lesson_id}: {e}")
        return jsonify({"error": "Failed to create export package"}), 500

@bp.route('/api/admin/lessons/import', methods=['POST'])
@login_required
@admin_required
def import_lesson():
    """Import a lesson from a JSON file."""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files['file']
        if not file.filename or not file.filename.endswith('.json'):
            return jsonify({"error": "Please provide a JSON file"}), 400

        try:
            lesson_data = json.load(file.stream)
        except json.JSONDecodeError:
            return jsonify({"error": "Invalid JSON format"}), 400

        handle_duplicates = request.form.get('handle_duplicates', 'rename')
        if handle_duplicates not in ['rename', 'replace', 'skip']:
            return jsonify({"error": "Invalid handle_duplicates option"}), 400

        imported_lesson = import_lesson_from_json(
            lesson_data,
            handle_duplicates=handle_duplicates,
            import_files=False
        )

        return jsonify({
            "success": True,
            "message": "Lesson imported successfully",
            "imported_count": 1,
            "lesson_id": imported_lesson.id,
            "lesson_title": imported_lesson.title
        }), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error importing lesson: {e}", exc_info=True)
        return jsonify({"error": "Failed to import lesson"}), 500

@bp.route('/api/admin/lessons/import-package', methods=['POST'])
@login_required
@admin_required
def import_lesson_package():
    """Import a lesson from ZIP package"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if not file.filename or not file.filename.endswith('.zip'):
            return jsonify({"error": "Please provide a ZIP file"}), 400
        
        # Get import options
        handle_duplicates = request.form.get('handle_duplicates', 'rename')
        if handle_duplicates not in ['rename', 'replace', 'skip']:
            return jsonify({"error": "Invalid handle_duplicates option"}), 400
        
        # Save uploaded file temporarily
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_file:
            file.save(temp_file.name)
            temp_zip_path = temp_file.name
        
        try:
            # Import the lesson
            imported_lesson = import_lesson_from_zip(temp_zip_path, handle_duplicates)
            
            return jsonify({
                "message": "Lesson package imported successfully",
                "lesson_id": imported_lesson.id,
                "lesson_title": imported_lesson.title
            }), 201
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_zip_path):
                os.unlink(temp_zip_path)
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error importing lesson package: {e}")
        return jsonify({"error": "Failed to import lesson package"}), 500

@bp.route('/api/admin/lessons/export-multiple', methods=['POST'])
@login_required
@admin_required
def export_multiple_lessons():
    """Export multiple lessons as a single ZIP package"""
    try:
        data = request.json
        if not data or 'lesson_ids' not in data:
            return jsonify({"error": "No lesson IDs provided"}), 400
        
        lesson_ids = data['lesson_ids']
        include_files = data.get('include_files', True)
        
        if not lesson_ids:
            return jsonify({"error": "Empty lesson IDs list"}), 400
        
        # Create temporary directory for export
        import tempfile
        import os
        import zipfile
        from datetime import datetime
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create main ZIP file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            main_zip_path = os.path.join(temp_dir, f"lessons_export_{timestamp}.zip")
            
            with zipfile.ZipFile(main_zip_path, 'w', zipfile.ZIP_DEFLATED) as main_zipf:
                exported_lessons = []
                
                for lesson_id in lesson_ids:
                    try:
                        # Export individual lesson
                        lesson_zip_path = create_lesson_export_package(
                            lesson_id, temp_dir, include_files
                        )
                        
                        # Add to main ZIP
                        lesson_zip_name = os.path.basename(lesson_zip_path)
                        main_zipf.write(lesson_zip_path, lesson_zip_name)
                        
                        # Track successful exports
                        lesson = Lesson.query.get(lesson_id)
                        if lesson:
                            exported_lessons.append({
                                'id': lesson_id,
                                'title': lesson.title,
                                'filename': lesson_zip_name
                            })
                        
                        # Clean up individual ZIP
                        os.unlink(lesson_zip_path)
                        
                    except Exception as e:
                        current_app.logger.error(f"Error exporting lesson {lesson_id}: {e}")
                        continue
                
                # Add manifest file
                manifest = {
                    'export_info': {
                        'version': '1.0',
                        'exported_at': datetime.utcnow().isoformat(),
                        'total_lessons': len(exported_lessons),
                        'includes_files': include_files
                    },
                    'lessons': exported_lessons
                }
                
                manifest_json = json.dumps(manifest, indent=2, ensure_ascii=False)
                main_zipf.writestr('export_manifest.json', manifest_json)
            
            # Return the ZIP file
            with open(main_zip_path, 'rb') as f:
                zip_data = f.read()
            
            from flask import make_response
            response = make_response(zip_data)
            response.headers['Content-Type'] = 'application/zip'
            response.headers['Content-Disposition'] = f'attachment; filename={os.path.basename(main_zip_path)}'
            
            return response
            
    except Exception as e:
        current_app.logger.error(f"Error exporting multiple lessons: {e}")
        return jsonify({"error": "Failed to export lessons"}), 500

@bp.route('/api/admin/lessons/import-info', methods=['POST'])
@login_required
@admin_required
def get_import_info():
    """Get information about a lesson import file without importing"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files['file']
        if not file.filename:
            return jsonify({"error": "No file selected"}), 400

        if file.filename.endswith('.json'):
            # Handle JSON file upload
            try:
                lesson_data = json.load(file.stream)
            except json.JSONDecodeError:
                return jsonify({"error": "Invalid JSON format"}), 400
            
            existing_lesson = Lesson.query.filter_by(title=lesson_data['title']).first()
            
            return jsonify({
                "success": True,
                "info": {
                    "file_type": "json",
                    "lesson_count": 1,
                    "lessons": [{
                        "title": lesson_data['title'],
                        "difficulty": lesson_data.get('difficulty_level'),
                        "pages": len(lesson_data.get('pages', [])),
                        "content_count": len(lesson_data.get('content', [])),
                        "files": [item.get('file_info') for item in lesson_data.get('content', []) if item.get('file_info')]
                    }],
                    "warnings": ["A lesson with this title already exists."] if existing_lesson else []
                }
            })

        elif file.filename.endswith('.zip'):
            # Handle ZIP file
            import tempfile
            import zipfile
            
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_file:
                file.save(temp_file.name)
                temp_zip_path = temp_file.name
            
            try:
                with zipfile.ZipFile(temp_zip_path, 'r') as zipf:
                    if 'lesson_data.json' in zipf.namelist():
                        lesson_json = zipf.read('lesson_data.json').decode('utf-8')
                        lesson_data = json.loads(lesson_json)
                        existing_lesson = Lesson.query.filter_by(title=lesson_data['title']).first()
                        
                        return jsonify({
                            "success": True,
                            "info": {
                                "file_type": "single_lesson_zip",
                                "lesson_count": 1,
                                "lessons": [{
                                    "title": lesson_data['title'],
                                    "difficulty": lesson_data.get('difficulty_level'),
                                    "pages": len(lesson_data.get('pages', [])),
                                    "content_count": len(lesson_data.get('content', [])),
                                    "files": [item.get('file_info') for item in lesson_data.get('content', []) if item.get('file_info')]
                                }],
                                "warnings": ["A lesson with this title already exists."] if existing_lesson else []
                            }
                        })
                    
                    elif 'export_manifest.json' in zipf.namelist():
                        manifest_json = zipf.read('export_manifest.json').decode('utf-8')
                        manifest = json.loads(manifest_json)
                        
                        lessons_info = []
                        for lesson_info in manifest.get('lessons', []):
                            existing_lesson = Lesson.query.filter_by(title=lesson_info['title']).first()
                            lessons_info.append({
                                **lesson_info,
                                "duplicate_exists": existing_lesson is not None,
                                "duplicate_id": existing_lesson.id if existing_lesson else None
                            })
                        
                        return jsonify({
                            "success": True,
                            "info": {
                                "file_type": "multiple_lessons_zip",
                                "lesson_count": len(lessons_info),
                                "lessons": lessons_info
                            }
                        })
                    
                    else:
                        return jsonify({"success": False, "error": "Invalid ZIP package format"}), 400
            
            finally:
                import os
                if os.path.exists(temp_zip_path):
                    os.unlink(temp_zip_path)
        
        else:
            return jsonify({"success": False, "error": "Unsupported file format"}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error getting import info: {e}")
        return jsonify({"success": False, "error": "Failed to analyze import file"}), 500
