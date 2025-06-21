# Phase 4: Interactive Content Types

## Overview
Implement interactive content types including multiple choice questions, fill-in-the-blank exercises, and other engaging learning components. This phase focuses on creating interactive elements that enhance the learning experience and provide immediate feedback to students.

## Duration
2-3 days

## Goals
- Implement multiple choice questions with feedback
- Add fill-in-the-blank exercises
- Create matching exercises
- Add true/false questions
- Implement interactive feedback system
- Create question banks and randomization
- Add scoring and progress tracking for interactive content

## Prerequisites
- Phases 1, 2, and 3 must be completed and tested
- Content builder foundation must be operational
- File upload system must be working
- Rich text editor must be integrated

## Technical Implementation

### 1. Database Model Extensions
**File**: `app/models.py`

**New Models:**
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

class QuizOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('quiz_question.id'), nullable=False)
    option_text = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    order_index = db.Column(db.Integer, default=0)
    feedback = db.Column(db.Text)  # Specific feedback for this option

class UserQuizAnswer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('quiz_question.id'), nullable=False)
    selected_option_id = db.Column(db.Integer, db.ForeignKey('quiz_option.id'))
    text_answer = db.Column(db.Text)  # For fill-in-the-blank questions
    is_correct = db.Column(db.Boolean, default=False)
    answered_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'question_id'),)
```

**Enhanced LessonContent Model:**
```python
# Add to existing LessonContent model
class LessonContent(db.Model):
    # ... existing fields ...
    
    # Interactive content fields
    is_interactive = db.Column(db.Boolean, default=False)
    max_attempts = db.Column(db.Integer, default=3)
    passing_score = db.Column(db.Integer, default=70)  # Percentage
    
    # Relationships
    quiz_questions = db.relationship('QuizQuestion', backref='content', lazy=True, cascade='all, delete-orphan')
```

### 2. Interactive Content Forms
**File**: `app/templates/admin/manage_lessons.html`

**Interactive Content Section:**
```html
<!-- Interactive Content Section -->
<div id="interactiveSection" style="display: none;">
    <div class="form-group">
        <label for="interactiveTitle">Title *</label>
        <input type="text" id="interactiveTitle" name="title" class="form-control" required>
    </div>
    
    <div class="form-group">
        <label for="interactiveType">Interactive Type</label>
        <select id="interactiveType" name="interactive_type" class="form-control" onchange="showInteractiveForm(this.value)">
            <option value="">Select Type</option>
            <option value="multiple_choice">Multiple Choice Question</option>
            <option value="fill_blank">Fill in the Blank</option>
            <option value="true_false">True/False</option>
            <option value="matching">Matching Exercise</option>
            <option value="quiz">Mini Quiz (Multiple Questions)</option>
        </select>
    </div>
    
    <!-- Multiple Choice Form -->
    <div id="multipleChoiceForm" style="display: none;">
        <div class="form-group">
            <label for="mcQuestion">Question *</label>
            <textarea id="mcQuestion" name="question_text" class="form-control rich-text-editor-simple" rows="3"></textarea>
        </div>
        
        <div class="form-group">
            <label>Answer Options:</label>
            <div id="mcOptions">
                <div class="option-item mb-2">
                    <div class="input-group">
                        <div class="input-group-prepend">
                            <div class="input-group-text">
                                <input type="radio" name="correct_option" value="0">
                            </div>
                        </div>
                        <input type="text" class="form-control" name="option_0" placeholder="Option A">
                        <div class="input-group-append">
                            <button type="button" class="btn btn-outline-danger" onclick="removeOption(0)">×</button>
                        </div>
                    </div>
                    <small class="form-text text-muted">
                        <input type="text" class="form-control form-control-sm mt-1" name="feedback_0" placeholder="Feedback for this option (optional)">
                    </small>
                </div>
            </div>
            <button type="button" class="btn btn-sm btn-outline-primary" onclick="addOption()">+ Add Option</button>
        </div>
        
        <div class="form-group">
            <label for="mcExplanation">Explanation (optional)</label>
            <textarea id="mcExplanation" name="explanation" class="form-control" rows="2" placeholder="Explain why this is the correct answer"></textarea>
        </div>
    </div>
    
    <!-- Fill in the Blank Form -->
    <div id="fillBlankForm" style="display: none;">
        <div class="form-group">
            <label for="fbQuestion">Question Text *</label>
            <textarea id="fbQuestion" name="question_text" class="form-control" rows="3" placeholder="Use [BLANK] to indicate where students should fill in answers"></textarea>
            <small class="form-text text-muted">Example: "The capital of Japan is [BLANK]."</small>
        </div>
        
        <div class="form-group">
            <label for="fbAnswers">Correct Answers *</label>
            <input type="text" id="fbAnswers" name="correct_answers" class="form-control" placeholder="Tokyo, tokyo, TOKYO (separate multiple acceptable answers with commas)">
            <small class="form-text text-muted">List all acceptable answers, separated by commas. Case-insensitive.</small>
        </div>
        
        <div class="form-group">
            <label for="fbExplanation">Explanation (optional)</label>
            <textarea id="fbExplanation" name="explanation" class="form-control" rows="2"></textarea>
        </div>
    </div>
    
    <!-- True/False Form -->
    <div id="trueFalseForm" style="display: none;">
        <div class="form-group">
            <label for="tfQuestion">Statement *</label>
            <textarea id="tfQuestion" name="question_text" class="form-control" rows="3"></textarea>
        </div>
        
        <div class="form-group">
            <label>Correct Answer</label>
            <div class="form-check">
                <input class="form-check-input" type="radio" name="tf_answer" id="tfTrue" value="true">
                <label class="form-check-label" for="tfTrue">True</label>
            </div>
            <div class="form-check">
                <input class="form-check-input" type="radio" name="tf_answer" id="tfFalse" value="false">
                <label class="form-check-label" for="tfFalse">False</label>
            </div>
        </div>
        
        <div class="form-group">
            <label for="tfExplanation">Explanation *</label>
            <textarea id="tfExplanation" name="explanation" class="form-control" rows="2" placeholder="Explain why this statement is true or false"></textarea>
        </div>
    </div>
    
    <!-- Quiz Settings -->
    <div class="form-group">
        <div class="row">
            <div class="col-md-6">
                <label for="maxAttempts">Max Attempts</label>
                <input type="number" id="maxAttempts" name="max_attempts" class="form-control" value="3" min="1" max="10">
            </div>
            <div class="col-md-6">
                <label for="passingScore">Passing Score (%)</label>
                <input type="number" id="passingScore" name="passing_score" class="form-control" value="70" min="0" max="100">
            </div>
        </div>
    </div>
</div>
```

### 3. Enhanced JavaScript Functionality
**File**: `app/templates/admin/manage_lessons.html` (JavaScript section)

**Interactive Content Functions:**
```javascript
let optionCount = 2; // Start with 2 options (A, B)

// Interactive content management
function showInteractiveForm(type) {
    // Hide all forms
    document.getElementById('multipleChoiceForm').style.display = 'none';
    document.getElementById('fillBlankForm').style.display = 'none';
    document.getElementById('trueFalseForm').style.display = 'none';
    
    // Show selected form
    if (type === 'multiple_choice') {
        document.getElementById('multipleChoiceForm').style.display = 'block';
        initializeMultipleChoice();
    } else if (type === 'fill_blank') {
        document.getElementById('fillBlankForm').style.display = 'block';
    } else if (type === 'true_false') {
        document.getElementById('trueFalseForm').style.display = 'block';
    }
}

function initializeMultipleChoice() {
    // Initialize with 2 default options
    const optionsContainer = document.getElementById('mcOptions');
    optionsContainer.innerHTML = '';
    
    for (let i = 0; i < 2; i++) {
        addOption();
    }
}

function addOption() {
    const optionsContainer = document.getElementById('mcOptions');
    const optionIndex = optionCount++;
    const optionLetter = String.fromCharCode(65 + optionIndex); // A, B, C, D...
    
    const optionHtml = `
        <div class="option-item mb-2" data-option="${optionIndex}">
            <div class="input-group">
                <div class="input-group-prepend">
                    <div class="input-group-text">
                        <input type="radio" name="correct_option" value="${optionIndex}">
                    </div>
                </div>
                <input type="text" class="form-control" name="option_${optionIndex}" placeholder="Option ${optionLetter}">
                <div class="input-group-append">
                    <button type="button" class="btn btn-outline-danger" onclick="removeOption(${optionIndex})">×</button>
                </div>
            </div>
            <small class="form-text text-muted">
                <input type="text" class="form-control form-control-sm mt-1" name="feedback_${optionIndex}" placeholder="Feedback for this option (optional)">
            </small>
        </div>
    `;
    
    optionsContainer.insertAdjacentHTML('beforeend', optionHtml);
}

function removeOption(optionIndex) {
    const optionElement = document.querySelector(`[data-option="${optionIndex}"]`);
    if (optionElement) {
        optionElement.remove();
    }
}

// Interactive content submission
async function submitInteractiveContent(lessonId) {
    const interactiveType = document.getElementById('interactiveType').value;
    const title = document.getElementById('interactiveTitle').value;
    
    let contentData = {
        content_type: 'interactive',
        title: title,
        interactive_type: interactiveType,
        is_interactive: true
    };
    
    if (interactiveType === 'multiple_choice') {
        contentData = {
            ...contentData,
            ...collectMultipleChoiceData()
        };
    } else if (interactiveType === 'fill_blank') {
        contentData = {
            ...contentData,
            ...collectFillBlankData()
        };
    } else if (interactiveType === 'true_false') {
        contentData = {
            ...contentData,
            ...collectTrueFalseData()
        };
    }
    
    try {
        const response = await fetch(`/api/admin/lessons/${lessonId}/content/interactive`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(contentData)
        });
        
        if (response.ok) {
            closeModal('addContentModal');
            loadLessonContent(lessonId);
            alert('Interactive content added successfully!');
        } else {
            const error = await response.json();
            alert('Error: ' + error.error);
        }
    } catch (error) {
        console.error('Error adding interactive content:', error);
        alert('Error adding interactive content');
    }
}

function collectMultipleChoiceData() {
    const question = document.getElementById('mcQuestion').value;
    const explanation = document.getElementById('mcExplanation').value;
    const correctOption = document.querySelector('input[name="correct_option"]:checked')?.value;
    
    const options = [];
    const optionElements = document.querySelectorAll('.option-item');
    
    optionElements.forEach((element, index) => {
        const optionInput = element.querySelector(`input[name^="option_"]`);
        const feedbackInput = element.querySelector(`input[name^="feedback_"]`);
        
        if (optionInput && optionInput.value.trim()) {
            options.push({
                text: optionInput.value.trim(),
                is_correct: correctOption === optionInput.name.split('_')[1],
                feedback: feedbackInput ? feedbackInput.value.trim() : ''
            });
        }
    });
    
    return {
        question_text: question,
        explanation: explanation,
        options: options
    };
}

function collectFillBlankData() {
    return {
        question_text: document.getElementById('fbQuestion').value,
        correct_answers: document.getElementById('fbAnswers').value,
        explanation: document.getElementById('fbExplanation').value
    };
}

function collectTrueFalseData() {
    const correctAnswer = document.querySelector('input[name="tf_answer"]:checked')?.value;
    
    return {
        question_text: document.getElementById('tfQuestion').value,
        correct_answer: correctAnswer === 'true',
        explanation: document.getElementById('tfExplanation').value
    };
}
```

### 4. API Endpoints for Interactive Content
**File**: `app/routes.py`

**New Endpoints:**
```python
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
    content = LessonContent(
        lesson_id=lesson_id,
        content_type='interactive',
        title=data.get('title'),
        is_interactive=True,
        max_attempts=data.get('max_attempts', 3),
        passing_score=data.get('passing_score', 70),
        order_index=data.get('order_index', 0)
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
        options = data.get('options', [])
        for i, option_data in enumerate(options):
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

@bp.route('/api/lessons/<int:lesson_id>/quiz/<int:question_id>/answer', methods=['POST'])
@login_required
def submit_quiz_answer(lesson_id, question_id):
    """Submit answer to quiz question"""
    lesson = Lesson.query.get_or_404(lesson_id)
    question = QuizQuestion.query.get_or_404(question_id)
    
    # Check lesson access
    accessible, message = lesson.is_accessible_to_user(current_user)
    if not accessible:
        return jsonify({"error": message}), 403
    
    data = request.json
    
    # Check if user has already answered or exceeded attempts
    existing_answers = UserQuizAnswer.query.filter_by(
        user_id=current_user.id, question_id=question_id
    ).count()
    
    if existing_answers >= question.content.max_attempts:
        return jsonify({"error": "Maximum attempts exceeded"}), 400
    
    # Process answer based on question type
    is_correct = False
    
    if question.question_type == 'multiple_choice':
        selected_option_id = data.get('selected_option_id')
        selected_option = QuizOption.query.get(selected_option_id)
        is_correct = selected_option and selected_option.is_correct
        
        answer = UserQuizAnswer(
            user_id=current_user.id,
            question_id=question_id,
            selected_option_id=selected_option_id,
            is_correct=is_correct
        )
    
    elif question.question_type == 'fill_blank':
        text_answer = data.get('text_answer', '').strip().lower()
        # Get correct answers from question data
        correct_answers = [ans.strip().lower() for ans in question.explanation.split(',')]
        is_correct = text_answer in correct_answers
        
        answer = UserQuizAnswer(
            user_id=current_user.id,
            question_id=question_id,
            text_answer=data.get('text_answer'),
            is_correct=is_correct
        )
    
    db.session.add(answer)
    db.session.commit()
    
    # Return result with feedback
    result = {
        'is_correct': is_correct,
        'explanation': question.explanation,
        'attempts_remaining': question.content.max_attempts - existing_answers - 1
    }
    
    if question.question_type == 'multiple_choice' and selected_option:
        result['option_feedback'] = selected_option.feedback
    
    return jsonify(result)
```

### 5. Interactive Content Display
**File**: `app/templates/lesson_view.html`

**Interactive Content Display:**
```html
<!-- Interactive Content Display -->
{% if content.is_interactive %}
<div class="interactive-content-container" data-content-id="{{ content.id }}">
    {% for question in content.quiz_questions %}
    <div class="quiz-question mb-4" data-question-id="{{ question.id }}">
        <div class="question-header mb-3">
            <h5>{{ question.question_text | safe }}</h5>
            {% if question.points > 1 %}
            <span class="badge bg-primary">{{ question.points }} points</span>
            {% endif %}
        </div>
        
        {% if question.question_type == 'multiple_choice' %}
        <div class="multiple-choice-options">
            {% for option in question.options | sort(attribute='order_index') %}
            <div class="form-check mb-2">
                <input class="form-check-input" type="radio" name="question_{{ question.id }}" 
                       id="option_{{ option.id }}" value="{{ option.id }}">
                <label class="form-check-label" for="option_{{ option.id }}">
                    {{ option.option_text }}
                </label>
            </div>
            {% endfor %}
        </div>
        
        {% elif question.question_type == 'fill_blank' %}
        <div class="fill-blank-input">
            <div class="question-text mb-3">
                {{ question.question_text | replace('[BLANK]', '<input type="text" class="form-control d-inline-block" style="width: 200px;" id="blank_' + question.id|string + '">') | safe }}
            </div>
        </div>
        
        {% elif question.question_type == 'true_false' %}
        <div class="true-false-options">
            <div class="form-check mb-2">
                <input class="form-check-input" type="radio" name="question_{{ question.id }}" 
                       id="true_{{ question.id }}" value="true">
                <label class="form-check-label" for="true_{{ question.id }}">
                    True
                </label>
            </div>
            <div class="form-check mb-2">
                <input class="form-check-input" type="radio" name="question_{{ question.id }}" 
                       id="false_{{ question.id }}" value="false">
                <label class="form-check-label" for="false_{{ question.id }}">
                    False
                </label>
            </div>
        </div>
        {% endif %}
        
        <div class="question-actions mt-3">
            <button class="btn btn-primary" onclick="submitQuizAnswer({{ question.id }})">
                Submit Answer
            </button>
            <div class="quiz-feedback mt-2" id="feedback_{{ question.id }}" style="display: none;"></div>
        </div>
        
        <div class="quiz-attempts mt-2">
            <small class="text-muted">
                Attempts remaining: <span id="attempts_{{ question.id }}">{{ content.max_attempts }}</span>
            </small>
        </div>
    </div>
    {% endfor %}
</div>
{% endif %}
```

### 6. Interactive Content JavaScript
**File**: `app/templates/lesson_view.html` (JavaScript section)

**Quiz Functionality:**
```javascript
async function submitQuizAnswer(questionId) {
    const questionElement = document.querySelector(`[data-question-id="${questionId}"]`);
    const questionType = questionElement.dataset.questionType;
    
    let answerData = {};
    
    if (questionType === 'multiple_choice' || questionType === 'true_false') {
        const selectedOption = questionElement.querySelector(`input[name="question_${questionId}"]:checked`);
        if (!selectedOption) {
            alert('Please select an answer');
            return;
        }
        answerData.selected_option_id = selectedOption.value;
    } else if (questionType === 'fill_blank') {
        const textInput = questionElement.querySelector(`#blank_${questionId}`);
        if (!textInput || !textInput.value.trim()) {
            alert('Please provide an answer');
            return;
        }
        answerData.text_answer = textInput.value.trim();
    }
    
    try {
        const response = await fetch(`/api/lessons/{{ lesson.id }}/quiz/${questionId}/answer`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(answerData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showQuizFeedback(questionId, result);
            updateAttempts(questionId, result.attempts_remaining);
            
            if (result.is_correct) {
                markContentComplete(questionElement.closest('[data-content-id]').dataset.contentId);
            }
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        console.error('Error submitting answer:', error);
        alert('Error submitting answer');
    }
}

function showQuizFeedback(questionId, result) {
    const feedbackElement = document.getElementById(`feedback_${questionId}`);
    
    let feedbackHtml = '';
    if (result.is_correct) {
        feedbackHtml = '<div class="alert alert-success">✓ Correct!</div>';
    } else {
        feedbackHtml = '<div class="alert alert-danger">✗ Incorrect</div>';
    }
    
    if (result.explanation) {
        feedbackHtml += `<div class="alert alert-info">${result.explanation}</div>`;
    }
    
    if (result.option_feedback) {
        feedbackHtml += `<div class="alert alert-warning">${result.option_feedback}</div>`;
    }
    
    feedbackElement.innerHTML = feedbackHtml;
    feedbackElement.style.display = 'block';
    
    // Disable question if correct or no attempts remaining
    if (result.is_correct || result.attempts_remaining === 0) {
        const questionElement = document.querySelector(`[data-question-id="${questionId}"]`);
        const inputs = questionElement.querySelectorAll('input');
        const button = questionElement.querySelector('button');
        
        inputs.forEach(input => input.disabled = true);
        button.disabled = true;
    }
}

function updateAttempts(questionId, attemptsRemaining) {
    const attemptsElement = document.getElementById(`attempts_${questionId}`);
    if (attemptsElement) {
        attemptsElement.textContent = attemptsRemaining;
    }
}
```

## Implementation Steps

### Step 1: Database Models
1. Create new database models for quiz questions and answers
2. Update existing LessonContent model
3. Run database migration
4. Test model relationships

### Step 2: Admin Interface
1. Add interactive content forms to lesson management
2. Implement dynamic form generation for different question types
3. Add JavaScript for form handling
4. Test content creation interface

### Step 3: API Endpoints
1. Create endpoints for interactive content creation
2. Implement quiz answer submission endpoint
3. Add validation and error handling
4. Test API functionality

### Step 4: Student Interface
1. Update lesson view template for interactive content
2. Add JavaScript for quiz functionality
3. Implement feedback system
4. Test interactive content display

### Step 5: Integration Testing
1. Test complete workflow from creation to student interaction
2. Verify progress tracking works with interactive content
3. Test attempt limits and scoring
4. Validate feedback system

## Testing Checklist

### Content Creation Testing
- [ ] Multiple choice questions can be created with options
- [ ] Fill-in-the-blank questions work correctly
- [ ] True/false questions can be created
- [ ] Question options can be added/removed dynamically
- [ ] Correct answers can be marked properly

### Student Interaction Testing
- [ ] Questions display correctly in lesson view
- [ ] Answer submission works for all question types
- [ ] Feedback is displayed appropriately
- [ ] Attempt limits are enforced
- [ ] Progress tracking works with interactive content

### Scoring and Feedback Testing
- [ ] Correct answers are identified properly
- [ ] Feedback messages display correctly
- [ ] Attempt counting works correctly
- [ ] Questions disable after max attempts or correct answer

## Success Criteria
- ✅ Admin can create multiple types of interactive questions
- ✅ Students can interact with questions and receive feedback
- ✅ Attempt limits and scoring work correctly
- ✅ Progress tracking includes interactive content
- ✅ Feedback system provides meaningful responses
- ✅ Interactive content integrates seamlessly with existing lesson system

## Files to Modify
1. `app/models.py` - New database models
2. `app/templates/admin/manage_lessons.html` - Interactive content forms
3. `app/templates/lesson_view.html` - Interactive content display
4. `app/routes.py` - New API endpoints

## Files to Create
1. Database migration script for new models

## Next Phase Preparation
Phase 4 prepares for Phase 5 by:
- Establishing interactive content infrastructure
- Creating the foundation for advanced content management
- Setting up user interaction tracking

Phase 5 will build upon this by adding content organization features like drag-and-drop reordering and advanced management tools.
