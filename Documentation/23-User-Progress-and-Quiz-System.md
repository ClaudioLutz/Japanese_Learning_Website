# User Progress and Quiz System

## Overview

The Japanese Learning Website implements a comprehensive user progress tracking and interactive quiz system that monitors student learning, provides detailed analytics, and delivers engaging interactive content. The system tracks progress at multiple levels and provides real-time feedback to enhance the learning experience.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Progress Tracking System](#progress-tracking-system)
3. [Quiz System](#quiz-system)
4. [Database Schema](#database-schema)
5. [API Endpoints](#api-endpoints)
6. [Frontend Integration](#frontend-integration)
7. [Analytics and Reporting](#analytics-and-reporting)
8. [Performance Considerations](#performance-considerations)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

## Architecture Overview

The progress and quiz system is built with a multi-layered architecture that tracks learning at various granularities:

```
User Interaction
    ↓ Progress Events
Progress Tracking Service
    ↓ Database Updates
UserLessonProgress Model
    ↓ Analytics
Progress Analytics
    ↓ Quiz Interaction
Quiz System
    ↓ Answer Processing
UserQuizAnswer Model
    ↓ Feedback
Real-time Feedback
```

### Key Components

1. **Progress Tracking**: Multi-level progress monitoring
2. **Quiz Engine**: Interactive question and answer system
3. **Answer Validation**: Comprehensive answer checking
4. **Feedback System**: Immediate and detailed feedback
5. **Analytics Engine**: Progress analytics and reporting

## Progress Tracking System

### UserLessonProgress Model

The core progress tracking is handled by the `UserLessonProgress` model in `app/models.py`:

```python
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
    content_progress = db.Column(db.Text)  # JSON string of content completion
```

### Progress Tracking Features

#### 1. Lesson-Level Progress

```python
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
```

#### 2. Content-Level Progress

```python
def mark_content_completed(self, content_id):
    """Mark a specific content item as completed"""
    progress = self.get_content_progress()
    progress[str(content_id)] = True
    self.set_content_progress(progress)
    self.update_progress_percentage()

def get_content_progress(self):
    """Get content progress as dictionary"""
    if self.content_progress:
        return json.loads(self.content_progress)
    return {}

def set_content_progress(self, progress_dict):
    """Set content progress from dictionary"""
    self.content_progress = json.dumps(progress_dict)
```

#### 3. Time Tracking

```python
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
```

### Progress Reset Functionality

```python
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

@bp.route('/lessons/<int:lesson_id>/reset', methods=['POST'])
@login_required
def reset_lesson_progress(lesson_id):
    """Reset user progress for a specific lesson."""
    form = CSRFTokenForm()
    if form.validate_on_submit():
        progress = UserLessonProgress.query.filter_by(
            user_id=current_user.id, lesson_id=lesson_id
        ).first()

        if progress:
            progress.reset()
            db.session.commit()
            flash('Your progress for this lesson has been reset.', 'success')
        else:
            flash('No progress found for this lesson.', 'info')
    else:
        flash('Invalid request to reset progress.', 'danger')

    return redirect(url_for('routes.view_lesson', lesson_id=lesson_id))
```

## Quiz System

### Quiz Data Models

#### QuizQuestion Model

```python
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
```

#### QuizOption Model

```python
class QuizOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('quiz_question.id'), nullable=False)
    option_text = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    order_index = db.Column(db.Integer, default=0)
    feedback = db.Column(db.Text)  # Specific feedback for this option
```

#### UserQuizAnswer Model

```python
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
```

### Quiz Types and Processing

#### 1. Multiple Choice Questions

```python
if question.question_type == 'multiple_choice':
    selected_option_id = data.get('selected_option_id')
    if not selected_option_id:
        return jsonify({"error": "selected_option_id is required"}), 400
    
    selected_option = QuizOption.query.get(int(selected_option_id))
    is_correct = selected_option and selected_option.is_correct

    answer.selected_option_id = selected_option_id
    answer.is_correct = is_correct
    answer.text_answer = None
```

#### 2. Fill-in-the-Blank Questions

```python
elif question.question_type == 'fill_blank':
    text_answer = data.get('text_answer', '').strip()
    correct_answers = [ans.strip().lower() for ans in (question.explanation or "").split(',')]
    is_correct = text_answer.lower() in correct_answers
    
    answer.text_answer = text_answer
    answer.is_correct = is_correct
    answer.selected_option_id = None
```

#### 3. True/False Questions

```python
elif question.question_type == 'true_false':
    selected_option_id = data.get('selected_option_id')
    if not selected_option_id:
        return jsonify({"error": "selected_option_id is required"}), 400
    selected_option = QuizOption.query.get(int(selected_option_id))
    is_correct = selected_option and selected_option.is_correct

    answer.selected_option_id = selected_option_id
    answer.is_correct = is_correct
    answer.text_answer = None
```

#### 4. Matching Questions

```python
elif question.question_type == 'matching':
    submitted_pairs = data.get('pairs', [])
    if not submitted_pairs:
        return jsonify({"error": "No pairs submitted for matching question"}), 400

    correct_options = {opt.option_text: opt.feedback for opt in question.options}
    
    correct_matches = 0
    for pair in submitted_pairs:
        prompt = pair.get('prompt')
        user_answer = pair.get('answer')
        if correct_options.get(prompt) == user_answer:
            correct_matches += 1
    
    is_correct = correct_matches == len(correct_options)
    answer.is_correct = is_correct
    answer.text_answer = json.dumps(submitted_pairs)
```

### Quiz Answer Submission

```python
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
            return jsonify({"error": message}), 403
        
        data = request.json
        if not data:
            return jsonify({"error": "Invalid request. Must be JSON."}), 400
        
        # Find existing answer or create a new one
        answer = UserQuizAnswer.query.filter_by(
            user_id=current_user.id, question_id=question_id
        ).first()

        # Check attempts limit
        if answer:
            max_attempts = question.content.max_attempts or float('inf')
            if answer.attempts >= max_attempts:
                return jsonify({"error": "Maximum attempts exceeded"}), 400
            answer.attempts += 1
        else:
            answer = UserQuizAnswer(
                user_id=current_user.id,
                question_id=question_id,
                attempts=1
            )
            db.session.add(answer)

        # Process answer based on question type
        # [Question type processing logic here]

        answer.answered_at = db.func.now()
        db.session.commit()
        
        # Return result with feedback
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
        
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Error submitting quiz answer: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred"}), 500
```

## Database Schema

### Progress Tracking Tables

#### user_lesson_progress
| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| user_id | Integer | Foreign key to users table |
| lesson_id | Integer | Foreign key to lessons table |
| started_at | DateTime | When user first accessed lesson |
| completed_at | DateTime | When lesson was completed |
| is_completed | Boolean | Whether lesson is completed |
| progress_percentage | Integer | Completion percentage (0-100) |
| time_spent | Integer | Time spent in minutes |
| last_accessed | DateTime | Last access timestamp |
| content_progress | Text | JSON string of content completion |

#### user_quiz_answer
| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| user_id | Integer | Foreign key to users table |
| question_id | Integer | Foreign key to quiz_question table |
| selected_option_id | Integer | Foreign key to quiz_option table |
| text_answer | Text | Text answer for fill-in-the-blank |
| is_correct | Boolean | Whether answer is correct |
| answered_at | DateTime | When answer was submitted |
| attempts | Integer | Number of attempts made |

### Quiz System Tables

#### quiz_question
| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| lesson_content_id | Integer | Foreign key to lesson_content table |
| question_type | String(50) | Type of question |
| question_text | Text | Question text |
| explanation | Text | Answer explanation |
| points | Integer | Points awarded for correct answer |
| order_index | Integer | Order within content |
| created_at | DateTime | Creation timestamp |

#### quiz_option
| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| question_id | Integer | Foreign key to quiz_question table |
| option_text | Text | Option text |
| is_correct | Boolean | Whether option is correct |
| order_index | Integer | Order within question |
| feedback | Text | Feedback for this option |

## API Endpoints

### Progress Tracking Endpoints

#### Get User Lessons with Progress
```http
GET /api/lessons
Authorization: Required (login)
```

**Response**:
```json
[
  {
    "id": 1,
    "title": "Introduction to Hiragana",
    "accessible": true,
    "access_message": "Accessible",
    "category_name": "Kana",
    "progress": {
      "progress_percentage": 75,
      "is_completed": false,
      "time_spent": 45,
      "last_accessed": "2025-07-10T14:30:00Z"
    }
  }
]
```

#### Update Lesson Progress
```http
POST /api/lessons/{lesson_id}/progress
Authorization: Required (login)
Content-Type: application/json

{
  "content_id": 123,
  "time_spent": 5
}
```

**Response**:
```json
{
  "id": 1,
  "user_id": 1,
  "lesson_id": 1,
  "progress_percentage": 80,
  "is_completed": false,
  "time_spent": 50
}
```

#### Reset Lesson Progress
```http
POST /lessons/{lesson_id}/reset
Authorization: Required (login)
Content-Type: application/x-www-form-urlencoded

csrf_token=abc123
```

### Quiz Endpoints

#### Submit Quiz Answer
```http
POST /api/lessons/{lesson_id}/quiz/{question_id}/answer
Authorization: Required (login)
Content-Type: application/json

{
  "selected_option_id": 456,
  "text_answer": "User's text answer",
  "pairs": [
    {"prompt": "Word", "answer": "Meaning"}
  ]
}
```

**Response**:
```json
{
  "is_correct": true,
  "explanation": "Detailed explanation",
  "option_feedback": "Specific feedback for selected option",
  "attempts_remaining": 2
}
```

## Frontend Integration

### Progress Display

#### Progress Bar Component
```html
<div class="progress mb-3">
    <div class="progress-bar" 
         role="progressbar" 
         style="width: {{ progress.progress_percentage }}%"
         aria-valuenow="{{ progress.progress_percentage }}" 
         aria-valuemin="0" 
         aria-valuemax="100">
        {{ progress.progress_percentage }}%
    </div>
</div>
```

#### Time Tracking
```javascript
let startTime = Date.now();
let timeSpent = 0;

// Track time spent on content
function trackTimeSpent() {
    const currentTime = Date.now();
    const sessionTime = Math.floor((currentTime - startTime) / 60000); // minutes
    timeSpent += sessionTime;
    startTime = currentTime;
    
    // Update progress
    updateProgress(currentContentId, sessionTime);
}

// Update progress via API
function updateProgress(contentId, timeSpent) {
    fetch(`/api/lessons/${lessonId}/progress`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrf_token
        },
        body: JSON.stringify({
            content_id: contentId,
            time_spent: timeSpent
        })
    })
    .then(response => response.json())
    .then(data => {
        updateProgressDisplay(data.progress_percentage);
    });
}
```

### Quiz Interface

#### Quiz Question Component
```html
<div class="quiz-question" data-question-id="{{ question.id }}">
    <h4>{{ question.question_text }}</h4>
    
    {% if question.question_type == 'multiple_choice' %}
        <div class="quiz-options">
            {% for option in question.options %}
                <div class="form-check">
                    <input class="form-check-input" 
                           type="radio" 
                           name="option" 
                           value="{{ option.id }}"
                           id="option{{ option.id }}">
                    <label class="form-check-label" for="option{{ option.id }}">
                        {{ option.option_text }}
                    </label>
                </div>
            {% endfor %}
        </div>
    {% elif question.question_type == 'fill_blank' %}
        <div class="fill-blank">
            <input type="text" 
                   class="form-control" 
                   placeholder="Enter your answer"
                   id="textAnswer">
        </div>
    {% endif %}
    
    <button class="btn btn-primary mt-3" onclick="submitAnswer({{ question.id }})">
        Submit Answer
    </button>
    
    <div class="quiz-feedback mt-3" style="display: none;"></div>
</div>
```

#### Quiz Submission JavaScript
```javascript
function submitAnswer(questionId) {
    const questionDiv = document.querySelector(`[data-question-id="${questionId}"]`);
    const questionType = questionDiv.dataset.questionType;
    
    let answerData = {};
    
    if (questionType === 'multiple_choice' || questionType === 'true_false') {
        const selectedOption = questionDiv.querySelector('input[name="option"]:checked');
        if (!selectedOption) {
            showError('Please select an answer');
            return;
        }
        answerData.selected_option_id = parseInt(selectedOption.value);
    } else if (questionType === 'fill_blank') {
        const textInput = questionDiv.querySelector('#textAnswer');
        answerData.text_answer = textInput.value.trim();
    }
    
    fetch(`/api/lessons/${lessonId}/quiz/${questionId}/answer`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrf_token
        },
        body: JSON.stringify(answerData)
    })
    .then(response => response.json())
    .then(data => {
        displayQuizFeedback(questionDiv, data);
    })
    .catch(error => {
        console.error('Error submitting answer:', error);
        showError('Failed to submit answer');
    });
}

function displayQuizFeedback(questionDiv, result) {
    const feedbackDiv = questionDiv.querySelector('.quiz-feedback');
    
    let feedbackHtml = '';
    if (result.is_correct) {
        feedbackHtml = `<div class="alert alert-success">
            <strong>Correct!</strong> ${result.explanation}
        </div>`;
    } else {
        feedbackHtml = `<div class="alert alert-danger">
            <strong>Incorrect.</strong> ${result.explanation}
            <br><small>Attempts remaining: ${result.attempts_remaining}</small>
        </div>`;
    }
    
    if (result.option_feedback) {
        feedbackHtml += `<div class="alert alert-info">
            ${result.option_feedback}
        </div>`;
    }
    
    feedbackDiv.innerHTML = feedbackHtml;
    feedbackDiv.style.display = 'block';
}
```

## Analytics and Reporting

### Progress Analytics

#### User Progress Summary
```python
def get_user_progress_summary(user_id):
    """Get comprehensive progress summary for a user"""
    progress_records = UserLessonProgress.query.filter_by(user_id=user_id).all()
    
    total_lessons = len(progress_records)
    completed_lessons = len([p for p in progress_records if p.is_completed])
    total_time = sum(p.time_spent for p in progress_records)
    
    return {
        'total_lessons_started': total_lessons,
        'completed_lessons': completed_lessons,
        'completion_rate': (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0,
        'total_time_spent': total_time,
        'average_time_per_lesson': total_time / total_lessons if total_lessons > 0 else 0
    }
```

#### Quiz Performance Analytics
```python
def get_quiz_performance(user_id, lesson_id=None):
    """Get quiz performance statistics"""
    query = UserQuizAnswer.query.filter_by(user_id=user_id)
    
    if lesson_id:
        # Filter by lesson
        content_ids = [c.id for c in LessonContent.query.filter_by(lesson_id=lesson_id, is_interactive=True)]
        question_ids = [q.id for q in QuizQuestion.query.filter(QuizQuestion.lesson_content_id.in_(content_ids))]
        query = query.filter(UserQuizAnswer.question_id.in_(question_ids))
    
    answers = query.all()
    
    total_questions = len(answers)
    correct_answers = len([a for a in answers if a.is_correct])
    total_attempts = sum(a.attempts for a in answers)
    
    return {
        'total_questions_answered': total_questions,
        'correct_answers': correct_answers,
        'accuracy_rate': (correct_answers / total_questions * 100) if total_questions > 0 else 0,
        'average_attempts': total_attempts / total_questions if total_questions > 0 else 0
    }
```

### Lesson Analytics

#### Lesson Completion Rates
```python
def get_lesson_analytics(lesson_id):
    """Get analytics for a specific lesson"""
    progress_records = UserLessonProgress.query.filter_by(lesson_id=lesson_id).all()
    
    total_users = len(progress_records)
    completed_users = len([p for p in progress_records if p.is_completed])
    
    if total_users == 0:
        return {'message': 'No users have started this lesson'}
    
    average_completion_time = sum(p.time_spent for p in progress_records if p.is_completed) / completed_users if completed_users > 0 else 0
    average_progress = sum(p.progress_percentage for p in progress_records) / total_users
    
    return {
        'total_users_started': total_users,
        'completed_users': completed_users,
        'completion_rate': (completed_users / total_users * 100),
        'average_completion_time': average_completion_time,
        'average_progress': average_progress
    }
```

## Performance Considerations

### Database Optimization

#### Indexing Strategy
```sql
-- Indexes for progress tracking
CREATE INDEX idx_user_lesson_progress_user_id ON user_lesson_progress(user_id);
CREATE INDEX idx_user_lesson_progress_lesson_id ON user_lesson_progress(lesson_id);
CREATE INDEX idx_user_lesson_progress_completed ON user_lesson_progress(is_completed);

-- Indexes for quiz system
CREATE INDEX idx_user_quiz_answer_user_id ON user_quiz_answer(user_id);
CREATE INDEX idx_user_quiz_answer_question_id ON user_quiz_answer(question_id);
CREATE INDEX idx_quiz_question_content_id ON quiz_question(lesson_content_id);
```

#### Query Optimization
```python
# Efficient progress loading with joins
def get_user_lessons_with_progress(user_id):
    """Get lessons with progress in a single query"""
    return db.session.query(Lesson, UserLessonProgress).outerjoin(
        UserLessonProgress,
        and_(
            UserLessonProgress.lesson_id == Lesson.id,
            UserLessonProgress.user_id == user_id
        )
    ).filter(Lesson.is_published == True).all()
```

### Caching Strategy

#### Progress Caching
```python
from flask_caching import Cache

cache = Cache()

@cache.memoize(timeout=300)  # 5 minutes
def get_cached_user_progress(user_id, lesson_id):
    """Cache user progress for performance"""
    progress = UserLessonProgress.query.filter_by(
        user_id=user_id, lesson_id=lesson_id
    ).first()
    return progress.to_dict() if progress else None

def invalidate_progress_cache(user_id, lesson_id):
    """Invalidate cache when progress is updated"""
    cache.delete_memoized(get_cached_user_progress, user_id, lesson_id)
```

## Best Practices

### Progress Tracking

1. **Granular Tracking**: Track progress at multiple levels (lesson, page, content)
2. **Real-time Updates**: Update progress immediately when users interact with content
3. **Persistent Storage**: Store progress data reliably to prevent loss
4. **Performance Optimization**: Use efficient queries and caching for progress data
5. **User Privacy**: Respect user privacy in progress tracking and analytics

### Quiz Design

1. **Clear Questions**: Write clear, unambiguous questions
2. **Meaningful Feedback**: Provide helpful feedback for both correct and incorrect answers
3. **Appropriate Difficulty**: Match question difficulty to lesson content
4. **Varied Question Types**: Use different question types to maintain engagement
5. **Fair Attempt Limits**: Set reasonable attempt limits for questions

### User Experience

1. **Visual Progress Indicators**: Show clear progress indicators throughout the application
2. **Immediate Feedback**: Provide immediate feedback for quiz answers
3. **Encouraging Messages**: Use positive reinforcement for progress milestones
4. **Easy Reset Options**: Allow users to reset progress when needed
5. **Accessibility**: Ensure progress and quiz interfaces are accessible

## Troubleshooting

### Common Issues

#### Progress Not Updating

**Issue**: User progress not being recorded

**Debug Steps**:
```python
# Check if progress record exists
progress = UserLessonProgress.query.filter_by(
    user_id=user_id, lesson_id=lesson_id
).first()

if not progress:
    print("No progress record found - creating new one")
    progress = UserLessonProgress(user_id=user_id, lesson_id=lesson_id)
    db.session.add(progress)

# Check content progress JSON
print(f"Content progress: {progress.get_content_progress()}")

# Verify database commit
try:
    db.session.commit()
    print("Progress saved successfully")
except Exception as e:
    print(f"Error saving progress: {e}")
    db.session.rollback()
```

#### Quiz Answers Not Saving

**Issue**: Quiz answers not being recorded

**Solutions**:
```python
# Check question and lesson relationship
question = QuizQuestion.query.get(question_id)
if not question:
    print("Question not found")
elif question.content.lesson_id != lesson_id:
    print("Question not in specified lesson")

# Check attempt limits
answer = UserQuizAnswer.query.filter_by(
    user_id=user_id, question_id=question_id
).first()

if answer and answer.attempts >= question.content.max_attempts:
    print("Maximum attempts exceeded")

# Verify unique constraint
try:
    new_answer = UserQuizAnswer(user_id=user_id, question_id=question_id)
    db.session.add(new_answer)
    db.session.commit()
except IntegrityError:
    print("Answer already exists for this user/question combination")
    db.session.rollback()
```

#### Performance Issues

**Issue**: Slow progress loading

**Solutions**:
```python
#
