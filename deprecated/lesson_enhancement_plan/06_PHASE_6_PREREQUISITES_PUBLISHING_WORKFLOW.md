# Phase 6: Prerequisites & Publishing Workflow

## Overview
Complete the lesson creation workflow by implementing prerequisites management and a comprehensive publishing system. This phase focuses on creating a complete lesson dependency system and professional publishing controls that ensure content quality and proper lesson sequencing.

## Duration
1-2 days

## Goals
- Implement visual prerequisites management system
- Create lesson dependency validation
- Add comprehensive publishing workflow (Draft → Review → Published)
- Implement lesson templates and quick-start options
- Add content validation and quality checks
- Create lesson analytics and reporting
- Implement lesson versioning and rollback capabilities

## Prerequisites
- Phases 1-5 must be completed and tested
- All content management features must be operational
- Content organization system must be working

## Technical Implementation

### 1. Prerequisites Management Interface
**File**: `app/templates/admin/manage_lessons.html`

**Prerequisites Management Modal:**
```html
<!-- Prerequisites Management Modal -->
<div id="prerequisitesModal" class="modal" style="display: none;">
    <div class="modal-content" style="max-width: 1000px;">
        <div class="modal-header">
            <h4>Manage Prerequisites</h4>
            <span class="close" onclick="closeModal('prerequisitesModal')">&times;</span>
        </div>
        <div class="modal-body">
            <div class="row">
                <div class="col-md-6">
                    <h6>Current Lesson</h6>
                    <div class="card">
                        <div class="card-body">
                            <h5 id="currentLessonTitle">Lesson Title</h5>
                            <p class="text-muted" id="currentLessonDescription">Lesson description...</p>
                            <div class="lesson-stats">
                                <span class="badge bg-info" id="currentLessonType">Free</span>
                                <span class="badge bg-secondary" id="currentLessonDifficulty">Difficulty: 3</span>
                            </div>
                        </div>
                    </div>
                    
                    <h6 class="mt-4">Current Prerequisites</h6>
                    <div id="currentPrerequisites" class="prerequisites-list">
                        <!-- Current prerequisites will be loaded here -->
                    </div>
                </div>
                
                <div class="col-md-6">
                    <h6>Available Lessons</h6>
                    <div class="mb-3">
                        <input type="text" id="lessonSearch" class="form-control" placeholder="Search lessons...">
                    </div>
                    <div class="form-group">
                        <select id="categoryFilter" class="form-control">
                            <option value="">All Categories</option>
                            <!-- Categories will be loaded dynamically -->
                        </select>
                    </div>
                    
                    <div id="availableLessons" class="available-lessons-list" style="max-height: 400px; overflow-y: auto;">
                        <!-- Available lessons will be loaded here -->
                    </div>
                </div>
            </div>
            
            <!-- Dependency Visualization -->
            <div class="mt-4">
                <h6>Dependency Tree</h6>
                <div id="dependencyTree" class="dependency-visualization">
                    <!-- Dependency tree will be rendered here -->
                </div>
            </div>
        </div>
        <div class="modal-footer">
            <button type="button" class="btn btn-secondary" onclick="closeModal('prerequisitesModal')">Cancel</button>
            <button type="button" class="btn btn-primary" onclick="savePrerequisites()">Save Prerequisites</button>
        </div>
    </div>
</div>

<!-- Publishing Workflow Modal -->
<div id="publishingModal" class="modal" style="display: none;">
    <div class="modal-content" style="max-width: 800px;">
        <div class="modal-header">
            <h4>Publishing Workflow</h4>
            <span class="close" onclick="closeModal('publishingModal')">&times;</span>
        </div>
        <div class="modal-body">
            <div class="publishing-status mb-4">
                <h6>Current Status</h6>
                <div class="status-indicator">
                    <span class="badge badge-lg" id="currentStatus">Draft</span>
                    <span class="status-description" id="statusDescription">This lesson is in draft mode and not visible to students.</span>
                </div>
            </div>
            
            <!-- Content Validation Results -->
            <div class="content-validation mb-4">
                <h6>Content Validation</h6>
                <div id="validationResults">
                    <!-- Validation results will be loaded here -->
                </div>
            </div>
            
            <!-- Publishing Options -->
            <div class="publishing-options">
                <h6>Publishing Actions</h6>
                <div class="btn-group-vertical w-100" role="group">
                    <button type="button" class="btn btn-outline-secondary" onclick="setLessonStatus('draft')" id="draftBtn">
                        📝 Save as Draft
                    </button>
                    <button type="button" class="btn btn-outline-warning" onclick="setLessonStatus('review')" id="reviewBtn">
                        👀 Submit for Review
                    </button>
                    <button type="button" class="btn btn-outline-success" onclick="setLessonStatus('published')" id="publishBtn">
                        🚀 Publish Lesson
                    </button>
                    <button type="button" class="btn btn-outline-danger" onclick="setLessonStatus('archived')" id="archiveBtn">
                        📦 Archive Lesson
                    </button>
                </div>
            </div>
            
            <!-- Publishing Notes -->
            <div class="publishing-notes mt-4">
                <h6>Publishing Notes</h6>
                <textarea id="publishingNotes" class="form-control" rows="3" placeholder="Add notes about this publishing action..."></textarea>
            </div>
            
            <!-- Version History -->
            <div class="version-history mt-4">
                <h6>Version History</h6>
                <div id="versionHistory" style="max-height: 200px; overflow-y: auto;">
                    <!-- Version history will be loaded here -->
                </div>
            </div>
        </div>
        <div class="modal-footer">
            <button type="button" class="btn btn-secondary" onclick="closeModal('publishingModal')">Close</button>
        </div>
    </div>
</div>

<!-- Lesson Templates Modal -->
<div id="templatesModal" class="modal" style="display: none;">
    <div class="modal-content" style="max-width: 900px;">
        <div class="modal-header">
            <h4>Lesson Templates</h4>
            <span class="close" onclick="closeModal('templatesModal')">&times;</span>
        </div>
        <div class="modal-body">
            <div class="row">
                <div class="col-md-4">
                    <div class="template-card" onclick="selectTemplate('basic_lesson')">
                        <div class="card">
                            <div class="card-body text-center">
                                <i class="fas fa-book fa-3x text-primary mb-3"></i>
                                <h6>Basic Lesson</h6>
                                <p class="text-muted small">Simple lesson with text content and basic exercises</p>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4">
                    <div class="template-card" onclick="selectTemplate('interactive_lesson')">
                        <div class="card">
                            <div class="card-body text-center">
                                <i class="fas fa-gamepad fa-3x text-success mb-3"></i>
                                <h6>Interactive Lesson</h6>
                                <p class="text-muted small">Lesson with quizzes, exercises, and multimedia content</p>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4">
                    <div class="template-card" onclick="selectTemplate('multimedia_lesson')">
                        <div class="card">
                            <div class="card-body text-center">
                                <i class="fas fa-video fa-3x text-warning mb-3"></i>
                                <h6>Multimedia Lesson</h6>
                                <p class="text-muted small">Rich lesson with videos, audio, and visual content</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mt-3">
                <div class="col-md-4">
                    <div class="template-card" onclick="selectTemplate('grammar_lesson')">
                        <div class="card">
                            <div class="card-body text-center">
                                <i class="fas fa-language fa-3x text-info mb-3"></i>
                                <h6>Grammar Lesson</h6>
                                <p class="text-muted small">Structured grammar lesson with examples and practice</p>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4">
                    <div class="template-card" onclick="selectTemplate('vocabulary_lesson')">
                        <div class="card">
                            <div class="card-body text-center">
                                <i class="fas fa-spell-check fa-3x text-danger mb-3"></i>
                                <h6>Vocabulary Lesson</h6>
                                <p class="text-muted small">Vocabulary building with words, meanings, and usage</p>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4">
                    <div class="template-card" onclick="selectTemplate('assessment_lesson')">
                        <div class="card">
                            <div class="card-body text-center">
                                <i class="fas fa-clipboard-check fa-3x text-secondary mb-3"></i>
                                <h6>Assessment</h6>
                                <p class="text-muted small">Comprehensive assessment with multiple question types</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="modal-footer">
            <button type="button" class="btn btn-secondary" onclick="closeModal('templatesModal')">Cancel</button>
            <button type="button" class="btn btn-primary" onclick="createFromTemplate()" id="createTemplateBtn" disabled>Create Lesson</button>
        </div>
    </div>
</div>
```

### 2. Enhanced JavaScript for Prerequisites and Publishing
**File**: `app/templates/admin/manage_lessons.html` (JavaScript section)

**Prerequisites and Publishing Functions:**
```javascript
let currentLessonForPrerequisites = null;
let selectedTemplate = null;

// Prerequisites Management
function managePrerequisites(lessonId, lessonTitle) {
    currentLessonForPrerequisites = lessonId;
    document.getElementById('currentLessonTitle').textContent = lessonTitle;
    
    loadLessonDetails(lessonId);
    loadCurrentPrerequisites(lessonId);
    loadAvailableLessons();
    loadDependencyTree(lessonId);
    
    openModal('prerequisitesModal');
}

async function loadLessonDetails(lessonId) {
    try {
        const response = await fetch(`/api/admin/lessons/${lessonId}`);
        const lesson = await response.json();
        
        document.getElementById('currentLessonDescription').textContent = lesson.description || 'No description';
        document.getElementById('currentLessonType').textContent = lesson.lesson_type;
        document.getElementById('currentLessonDifficulty').textContent = `Difficulty: ${lesson.difficulty_level || 'N/A'}`;
    } catch (error) {
        console.error('Error loading lesson details:', error);
    }
}

async function loadCurrentPrerequisites(lessonId) {
    try {
        const response = await fetch(`/api/admin/lessons/${lessonId}/prerequisites`);
        const prerequisites = await response.json();
        
        const container = document.getElementById('currentPrerequisites');
        container.innerHTML = '';
        
        if (prerequisites.length === 0) {
            container.innerHTML = '<p class="text-muted">No prerequisites set</p>';
            return;
        }
        
        prerequisites.forEach(prereq => {
            const prereqElement = document.createElement('div');
            prereqElement.className = 'prerequisite-item d-flex justify-content-between align-items-center mb-2 p-2 border rounded';
            prereqElement.innerHTML = `
                <div>
                    <strong>${prereq.title}</strong>
                    <br><small class="text-muted">${prereq.category_name || 'No Category'}</small>
                </div>
                <button class="btn btn-sm btn-outline-danger" onclick="removePrerequisite(${prereq.id})">
                    <i class="fas fa-times"></i>
                </button>
            `;
            container.appendChild(prereqElement);
        });
    } catch (error) {
        console.error('Error loading prerequisites:', error);
    }
}

async function loadAvailableLessons() {
    try {
        const response = await fetch('/api/admin/lessons');
        const lessons = await response.json();
        
        const container = document.getElementById('availableLessons');
        container.innerHTML = '';
        
        lessons.forEach(lesson => {
            if (lesson.id === currentLessonForPrerequisites) return; // Skip current lesson
            
            const lessonElement = document.createElement('div');
            lessonElement.className = 'available-lesson-item d-flex justify-content-between align-items-center mb-2 p-2 border rounded';
            lessonElement.innerHTML = `
                <div>
                    <strong>${lesson.title}</strong>
                    <br><small class="text-muted">${lesson.category_name || 'No Category'} • ${lesson.lesson_type}</small>
                </div>
                <button class="btn btn-sm btn-outline-primary" onclick="addPrerequisite(${lesson.id})">
                    <i class="fas fa-plus"></i> Add
                </button>
            `;
            container.appendChild(lessonElement);
        });
    } catch (error) {
        console.error('Error loading available lessons:', error);
    }
}

async function addPrerequisite(prerequisiteLessonId) {
    try {
        const response = await fetch(`/api/admin/lessons/${currentLessonForPrerequisites}/prerequisites`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prerequisite_lesson_id: prerequisiteLessonId })
        });
        
        if (response.ok) {
            loadCurrentPrerequisites(currentLessonForPrerequisites);
            loadDependencyTree(currentLessonForPrerequisites);
        } else {
            const error = await response.json();
            alert('Error: ' + error.error);
        }
    } catch (error) {
        console.error('Error adding prerequisite:', error);
        alert('Error adding prerequisite');
    }
}

async function removePrerequisite(prerequisiteLessonId) {
    try {
        const response = await fetch(`/api/admin/lessons/${currentLessonForPrerequisites}/prerequisites/${prerequisiteLessonId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            loadCurrentPrerequisites(currentLessonForPrerequisites);
            loadDependencyTree(currentLessonForPrerequisites);
        } else {
            const error = await response.json();
            alert('Error: ' + error.error);
        }
    } catch (error) {
        console.error('Error removing prerequisite:', error);
        alert('Error removing prerequisite');
    }
}

async function loadDependencyTree(lessonId) {
    try {
        const response = await fetch(`/api/admin/lessons/${lessonId}/dependency-tree`);
        const treeData = await response.json();
        
        const container = document.getElementById('dependencyTree');
        container.innerHTML = generateDependencyTreeHTML(treeData);
    } catch (error) {
        console.error('Error loading dependency tree:', error);
    }
}

function generateDependencyTreeHTML(treeData) {
    // Simple tree visualization - can be enhanced with a proper tree library
    let html = '<div class="dependency-tree">';
    
    if (treeData.prerequisites && treeData.prerequisites.length > 0) {
        html += '<div class="tree-level">';
        html += '<h6>Prerequisites:</h6>';
        treeData.prerequisites.forEach(prereq => {
            html += `<div class="tree-node prerequisite">${prereq.title}</div>`;
        });
        html += '</div>';
    }
    
    html += `<div class="tree-level current"><div class="tree-node current-lesson">${treeData.title} (Current)</div></div>`;
    
    if (treeData.dependents && treeData.dependents.length > 0) {
        html += '<div class="tree-level">';
        html += '<h6>Lessons that depend on this:</h6>';
        treeData.dependents.forEach(dependent => {
            html += `<div class="tree-node dependent">${dependent.title}</div>`;
        });
        html += '</div>';
    }
    
    html += '</div>';
    return html;
}

// Publishing Workflow
function managePublishing(lessonId, lessonTitle) {
    currentLessonForPublishing = lessonId;
    
    loadPublishingStatus(lessonId);
    validateLessonContent(lessonId);
    loadVersionHistory(lessonId);
    
    openModal('publishingModal');
}

async function loadPublishingStatus(lessonId) {
    try {
        const response = await fetch(`/api/admin/lessons/${lessonId}/publishing-status`);
        const status = await response.json();
        
        document.getElementById('currentStatus').textContent = status.status;
        document.getElementById('currentStatus').className = `badge badge-lg bg-${getStatusColor(status.status)}`;
        document.getElementById('statusDescription').textContent = getStatusDescription(status.status);
        
        // Update button states
        updatePublishingButtons(status.status);
    } catch (error) {
        console.error('Error loading publishing status:', error);
    }
}

async function validateLessonContent(lessonId) {
    try {
        const response = await fetch(`/api/admin/lessons/${lessonId}/validate`);
        const validation = await response.json();
        
        const container = document.getElementById('validationResults');
        container.innerHTML = '';
        
        validation.checks.forEach(check => {
            const checkElement = document.createElement('div');
            checkElement.className = `alert alert-${check.status === 'pass' ? 'success' : check.status === 'warning' ? 'warning' : 'danger'} py-2`;
            checkElement.innerHTML = `
                <i class="fas fa-${check.status === 'pass' ? 'check' : check.status === 'warning' ? 'exclamation-triangle' : 'times'}"></i>
                ${check.message}
            `;
            container.appendChild(checkElement);
        });
    } catch (error) {
        console.error('Error validating lesson content:', error);
    }
}

async function setLessonStatus(status) {
    const notes = document.getElementById('publishingNotes').value;
    
    try {
        const response = await fetch(`/api/admin/lessons/${currentLessonForPublishing}/status`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: status, notes: notes })
        });
        
        if (response.ok) {
            loadPublishingStatus(currentLessonForPublishing);
            loadVersionHistory(currentLessonForPublishing);
            loadLessons(); // Refresh main table
            alert(`Lesson status updated to ${status}`);
        } else {
            const error = await response.json();
            alert('Error: ' + error.error);
        }
    } catch (error) {
        console.error('Error updating lesson status:', error);
        alert('Error updating lesson status');
    }
}

function getStatusColor(status) {
    const colors = {
        'draft': 'secondary',
        'review': 'warning',
        'published': 'success',
        'archived': 'dark'
    };
    return colors[status] || 'secondary';
}

function getStatusDescription(status) {
    const descriptions = {
        'draft': 'This lesson is in draft mode and not visible to students.',
        'review': 'This lesson is under review and pending approval.',
        'published': 'This lesson is live and visible to students.',
        'archived': 'This lesson is archived and no longer available to students.'
    };
    return descriptions[status] || 'Unknown status';
}

function updatePublishingButtons(currentStatus) {
    // Enable/disable buttons based on current status and workflow rules
    const buttons = {
        'draftBtn': true,
        'reviewBtn': currentStatus === 'draft',
        'publishBtn': currentStatus === 'review' || currentStatus === 'draft',
        'archiveBtn': currentStatus === 'published'
    };
    
    Object.keys(buttons).forEach(btnId => {
        const btn = document.getElementById(btnId);
        btn.disabled = !buttons[btnId];
    });
}

// Lesson Templates
function openTemplatesModal() {
    selectedTemplate = null;
    document.getElementById('createTemplateBtn').disabled = true;
    openModal('templatesModal');
}

function selectTemplate(templateName) {
    selectedTemplate = templateName;
    
    // Update visual selection
    document.querySelectorAll('.template-card .card').forEach(card => {
        card.classList.remove('border-primary');
    });
    
    event.currentTarget.querySelector('.card').classList.add('border-primary');
    document.getElementById('createTemplateBtn').disabled = false;
}

async function createFromTemplate() {
    if (!selectedTemplate) return;
    
    try {
        const response = await fetch('/api/admin/lessons/from-template', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ template: selectedTemplate })
        });
        
        if (response.ok) {
            const newLesson = await response.json();
            closeModal('templatesModal');
            loadLessons();
            alert(`Lesson created from template: ${newLesson.title}`);
            
            // Optionally open the new lesson for editing
            manageContent(newLesson.id, newLesson.title);
        } else {
            const error = await response.json();
            alert('Error: ' + error.error);
        }
    } catch (error) {
        console.error('Error creating lesson from template:', error);
        alert('Error creating lesson from template');
    }
}

// Enhanced lesson table with new actions
function enhanceLessonTable() {
    // Add new action buttons to existing lesson table
    const existingActionCells = document.querySelectorAll('#lessonsTable tbody td:last-child');
    
    existingActionCells.forEach(cell => {
        const lessonId = cell.closest('tr').querySelector('td:first-child').textContent;
        const lessonTitle = cell.closest('tr').querySelector('td:nth-child(2)').textContent;
        
        // Add prerequisites button
        const prereqBtn = document.createElement('button');
        prereqBtn.className = 'btn btn-sm btn-outline-info me-1';
        prereqBtn.innerHTML = '<i class="fas fa-sitemap"></i>';
        prereqBtn.title = 'Manage Prerequisites';
        prereqBtn.onclick = () => managePrerequisites(lessonId, lessonTitle);
        
        // Add publishing button
        const publishBtn = document.createElement('button');
        publishBtn.className = 'btn btn-sm btn-outline-success me-1';
        publishBtn.innerHTML = '<i class="fas fa-rocket"></i>';
        publishBtn.title = 'Publishing Workflow';
        publishBtn.onclick = () => managePublishing(lessonId, lessonTitle);
        
        // Insert before existing buttons
        cell.insertBefore(prereqBtn, cell.firstChild);
        cell.insertBefore(publishBtn, cell.firstChild);
    });
}
```

### 3. API Endpoints for Prerequisites and Publishing
**File**: `app/routes.py`

**New Prerequisites and Publishing Endpoints:**
```python
# Prerequisites Management
@bp.route('/api/admin/lessons/<int:lesson_id>/prerequisites', methods=['GET'])
@login_required
@admin_required
def get_lesson_prerequisites(lesson_id):
    """Get lesson prerequisites"""
    lesson = Lesson.query.get_or_404(lesson_id)
    prerequisites = [
        {
            'id': prereq.prerequisite_lesson.id,
            'title': prereq.prerequisite_lesson.title,
            'category_name': prereq.prerequisite_lesson.category.name if prereq.prerequisite_lesson.category else None
        }
        for prereq in lesson.prerequisites
    ]
    return jsonify(prerequisites)

@bp.route('/api/admin/lessons/<int:lesson_id>/prerequisites', methods=['POST'])
@login_required
@admin_required
def add_lesson_prerequisite(lesson_id):
    """Add prerequisite to lesson"""
    lesson = Lesson.query.get_or_404(lesson_id)
    data = request.json
    
    if not data or 'prerequisite_lesson_id' not in data:
        return jsonify({"error": "Missing prerequisite lesson ID"}), 400
    
    prerequisite_lesson_id = data['prerequisite_lesson_id']
    
    # Check if prerequisite lesson exists
    prerequisite_lesson = Lesson.query.get(prerequisite_lesson_id)
    if not prerequisite_lesson:
        return jsonify({"error": "Prerequisite lesson not found"}), 404
    
    # Check for circular dependencies
    if would_create_circular_dependency(lesson_id, prerequisite_lesson_id):
        return jsonify({"error": "This would create a circular dependency"}), 400
    
    # Check if prerequisite already exists
    existing = LessonPrerequisite.query.filter_by(
        lesson_id=lesson_id,
        prerequisite_lesson_id=prerequisite_lesson_id
    ).first()
    
    if existing:
        return jsonify({"error": "Prerequisite already exists"}), 400
    
    # Add prerequisite
    prerequisite = LessonPrerequisite(
        lesson_id=lesson_id,
        prerequisite_lesson_id=prerequisite_lesson_id
    )
    
    try:
        db.session.add(prerequisite)
        db.session.commit()
        return jsonify({"message": "Prerequisite added successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to add prerequisite"}), 500

@bp.route('/api/admin/lessons/<int:lesson_id>/prerequisites/<int:prerequisite_id>', methods=['DELETE'])
@login_required
@admin_required
def remove_lesson_prerequisite(lesson_id, prerequisite_id):
    """Remove prerequisite from lesson"""
    prerequisite = LessonPrerequisite.query.filter_by(
        lesson_id=lesson_id,
        prerequisite_lesson_id=prerequisite_id
    ).first_or_404()
    
    try:
        db.session.delete(prerequisite)
        db.session.commit()
        return jsonify({"message": "Prerequisite removed successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to remove prerequisite"}), 500

@bp.route('/api/admin/lessons/<int:lesson_id>/dependency-tree', methods=['GET'])
@login_required
@admin_required
def get_dependency_tree(lesson_id):
    """Get lesson dependency tree"""
    lesson = Lesson.query.get_or_404(lesson_id)
    
    # Get prerequisites
    prerequisites = [
        {
            'id': prereq.prerequisite_lesson.id,
            'title': prereq.prerequisite_lesson.title
        }
        for prereq in lesson.prerequisites
    ]
    
    # Get lessons that depend on this one
    dependents = [
        {
            'id': dep.lesson.id,
            'title': dep.lesson.title
        }
        for dep in lesson.required_by
    ]
    
    return jsonify({
        'id': lesson.id,
        'title': lesson.title,
        'prerequisites': prerequisites,
        'dependents': dependents
    })

# Publishing Workflow
@bp.route('/api/admin/lessons/<int:lesson_id>/publishing-status', methods=['GET'])
@login_required
@admin_required
def get_publishing_status(lesson_id):
    """Get lesson publishing status"""
    lesson = Lesson.query.get_or_404(lesson_id)
    
    # Determine status based on is_published and other factors
    if lesson.is_published:
        status = 'published'
    else:
        # You can extend this logic based on additional status fields
        status = 'draft'
    
    return jsonify({
        'status': status,
        'last_updated': lesson.updated_at.isoformat() if lesson.updated_at else None
    })

@bp.route('/api/admin/lessons/<int:lesson_id>/validate', methods=['GET'])
@login_required
@admin_required
def validate_lesson_content(lesson_id):
    """Validate lesson content for publishing"""
    lesson = Lesson.query.get_or_404(lesson_id)
    
    checks = []
    
    # Check if lesson has title
    if lesson.title:
        checks.append({"status": "pass", "message": "✓ Lesson has a title"})
    else:
        checks.append({"status": "fail", "message": "✗ Lesson title is required"})
    
    # Check if lesson has description
    if lesson.description:
        checks.append({"status": "pass", "message": "✓ Lesson has a description"})
    else:
        checks.append({"status": "warning", "message": "⚠ Lesson description is recommended"})
    
    # Check if lesson has content
    content_count = len(lesson.content_items)
    if content_count > 0:
        checks.append({"status": "pass", "message": f"✓ Lesson has {content_count} content item(s)"})
    else:
        checks.append({"status": "fail", "message": "✗ Lesson must have at least one content item"})
    
    # Check if lesson has category
    if lesson.category:
        checks.append({"status": "pass", "message": "✓ Lesson is assigned to a category"})
    else:
        checks.append({"status": "warning", "message": "⚠ Lesson category is recommended"})
    
    # Check difficulty level
    if lesson.difficulty_level:
        checks.append({"status": "pass", "message": f"✓ Difficulty level set to {lesson.difficulty_level}"})
    else:
        checks.append({"status": "warning", "message": "⚠ Difficulty level is recommended"})
    
    # Check estimated duration
    if lesson.estimated_duration:
        checks.append({"status": "pass", "message": f"✓ Estimated duration: {lesson.estimated_duration} minutes"})
    else:
        checks.append({"status": "warning", "message": "⚠ Estimated duration is recommended"})
    
    # Check prerequisites for advanced lessons
    if lesson.difficulty_level and lesson.difficulty_level > 2:
        if lesson.prerequisites:
            checks.append({"status": "pass", "message": "✓ Advanced lesson has prerequisites"})
        else:
            checks.append({"status": "warning", "message": "⚠ Advanced lessons should have prerequisites"})
    
    # Check interactive content for engagement
    interactive_content = [c for c in lesson.content_items if c.is_interactive]
    if interactive_content:
        checks.append({"status": "pass", "message": f"✓ Lesson has {len(interactive_content)} interactive element(s)"})
    else:
        checks.append({"status": "warning", "message": "⚠ Consider adding interactive content for better engagement"})
    
    return jsonify({"checks": checks})

@bp.route('/api/admin/lessons/<int:lesson_id>/status', methods=['PUT'])
@login_required
@admin_required
def update_lesson_status(lesson_id):
    """Update lesson publishing status"""
    lesson = Lesson.query.get_or_404(lesson_id)
    data = request.json
    
    if not data or 'status' not in data:
        return jsonify({"error": "Missing status"}), 400
    
    new_status = data['status']
    notes = data.get('notes', '')
    
    # Validate status
    valid_statuses = ['draft', 'review', 'published', 'archived']
    if new_status not in valid_statuses:
        return jsonify({"error": "Invalid status"}), 400
    
    # Update lesson based on status
    if new_status == 'published':
        lesson.is_published = True
    else:
        lesson.is_published = False
    
    # You can extend this to store status history in a separate table
    lesson.updated_at = db.func.now()
    
    try:
        db.session.commit()
        return jsonify({"message": f"Lesson status updated to {new_status}"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update lesson status"}), 500

# Lesson Templates
@bp.route('/api/admin/lessons/from-template', methods=['POST'])
@login_required
@admin_required
def create_lesson_from_template(template_name):
    """Create lesson from template"""
    data = request.json
    
    if not data or 'template' not in data:
        return jsonify({"error": "Missing template name"}), 400
    
    template_name = data['template']
    
    # Define lesson templates
    templates = {
        'basic_lesson': {
            'title': 'New Basic Lesson',
            'description': 'A simple lesson with text content and basic exercises',
            'lesson_type': 'free',
            'difficulty_level': 1,
            'estimated_duration': 15,
            'content_items': [
                {'content_type': 'text', 'title': 'Introduction', 'content_text': '<h3>Welcome to this lesson!</h3><p>This is an introduction to the topic.</p>'},
                {'content_type': 'text', 'title': 'Main Content', 'content_text': '<h3>Main Learning Content</h3><p>Add your main learning content here.</p>'},
                {'content_type': 'interactive', 'title': 'Quick Quiz', 'interactive_type': 'multiple_choice'}
            ]
        },
        'interactive_lesson': {
            'title': 'New Interactive Lesson',
            'description': 'A lesson with quizzes, exercises, and multimedia content',
            'lesson_type': 'premium',
            'difficulty_level': 2,
            'estimated_duration': 25,
            'content_items': [
                {'content_type': 'text', 'title': 'Introduction', 'content_text': '<h3>Interactive Learning Experience</h3><p>Get ready for an engaging lesson!</p>'},
                {'content_type': 'interactive', 'title': 'Knowledge Check', 'interactive_type': 'multiple_choice'},
                {'content_type': 'text', 'title': 'Practice Section', 'content_text': '<h3>Practice Time</h3><p>Apply what you\'ve learned.</p>'},
                {'content_type': 'interactive', 'title': 'Fill in the Blanks', 'interactive_type': 'fill_blank'}
            ]
        },
        'multimedia_lesson': {
            'title': 'New Multimedia Lesson',
            'description': 'Rich lesson with videos, audio, and visual content',
            'lesson_type': 'premium',
            'difficulty_level': 2,
            'estimated_duration': 30,
            'content_items': [
                {'content_type': 'text', 'title': 'Introduction', 'content_text': '<h3>Multimedia Learning</h3><p>Experience rich multimedia content.</p>'},
                {'content_type': 'video', 'title': 'Instructional Video', 'content_text': 'Add your video content here'},
                {'content_type': 'audio', 'title': 'Audio Practice', 'content_text': 'Add your audio content here'},
                {'content_type': 'interactive', 'title': 'Comprehension Check', 'interactive_type': 'multiple_choice'}
            ]
        },
        'grammar_lesson': {
            'title': 'New Grammar Lesson',
            'description': 'Structured grammar lesson with examples and practice',
            'lesson_type': 'free',
            'difficulty_level': 2,
            'estimated_duration': 20,
            'content_items': [
                {'content_type': 'text', 'title': 'Grammar Point Introduction', 'content_text': '<h3>Grammar Focus</h3><p>Today we\'ll learn about...</p>'},
                {'content_type': 'grammar', 'title': 'Grammar Rule', 'content_id': None},
                {'content_type': 'text', 'title': 'Examples', 'content_text': '<h3>Examples</h3><p>Here are some examples...</p>'},
                {'content_type': 'interactive', 'title': 'Grammar Practice', 'interactive_type': 'fill_blank'}
            ]
        },
        'vocabulary_lesson': {
            'title': 'New Vocabulary Lesson',
            'description': 'Vocabulary building with words, meanings, and usage',
            'lesson_type': 'free',
            'difficulty_level': 1,
            'estimated_duration': 15,
            'content_items': [
                {'content_type': 'text', 'title': 'Vocabulary Introduction', 'content_text': '<h3>New Vocabulary</h3><p>Let\'s learn some new words!</p>'},
                {'content_type': 'vocabulary', 'title': 'Word 1', 'content_id': None},
                {'content_type': 'vocabulary', 'title': 'Word 2', 'content_id': None},
                {'content_type': 'interactive', 'title': 'Vocabulary Quiz', 'interactive_type': 'multiple_choice'}
            ]
        },
        'assessment_lesson': {
            'title': 'New Assessment',
            'description': 'Comprehensive assessment with multiple question types',
            'lesson_type': 'premium',
            'difficulty_level': 3,
            'estimated_duration': 45,
            'content_items': [
                {'content_type': 'text', 'title': 'Assessment Instructions', 'content_text': '<h3>Assessment</h3><p>This assessment will test your knowledge.</p>'},
                {'content_type': 'interactive', 'title': 'Multiple Choice Section', 'interactive_type': 'multiple_choice'},
                {'content_type': 'interactive', 'title': 'Fill in the Blanks', 'interactive_type': 'fill_blank'},
                {'content_type': 'interactive', 'title': 'True or False', 'interactive_type': 'true_false'}
            ]
        }
    }
    
    if template_name not in templates:
        return jsonify({"error": "Template not found"}), 404
    
    template = templates[template_name]
    
    try:
        # Create lesson
        lesson = Lesson(
            title=template['title'],
            description=template['description'],
            lesson_type=template['lesson_type'],
            difficulty_level=template['difficulty_level'],
            estimated_duration=template['estimated_duration'],
            is_published=False
        )
        
        db.session.add(lesson)
        db.session.flush()  # Get lesson ID
        
        # Create content items
        for i, content_template in enumerate(template['content_items']):
            content = LessonContent(
                lesson_id=lesson.id,
                content_type=content_template['content_type'],
                title=content_template['title'],
                content_text=content_template.get('content_text'),
                content_id=content_template.get('content_id'),
                order_index=i,
                is_interactive=content_template['content_type'] == 'interactive'
            )
            db.session.add(content)
        
        db.session.commit()
        return jsonify(model_to_dict(lesson)), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to create lesson from template"}), 500

# Utility function for circular dependency checking
def would_create_circular_dependency(lesson_id, prerequisite_lesson_id):
    """Check if adding a prerequisite would create a circular dependency"""
    
    def has_path(start_id, target_id, visited=None):
        if visited is None:
            visited = set()
        
        if start_id == target_id:
            return True
        
        if start_id in visited:
            return False
        
        visited.add(start_id)
        
        # Get all lessons that depend on start_id
        dependents = LessonPrerequisite.query.filter_by(prerequisite_lesson_id=start_id).all()
        
        for dependent in dependents:
            if has_path(dependent.lesson_id, target_id, visited.copy()):
                return True
        
        return False
    
    # Check if prerequisite_lesson_id has a path to lesson_id
    return has_path(prerequisite_lesson_id, lesson_id)
```

## Implementation Steps

### Step 1: Prerequisites System
1. Implement prerequisites management interface
2. Create API endpoints for prerequisites CRUD
3. Add circular dependency validation
4. Create dependency tree visualization
5. Test prerequisites functionality

### Step 2: Publishing Workflow
1. Create publishing status management
2. Implement content validation system
3. Add publishing workflow controls
4. Create status tracking and history
5. Test publishing workflow

### Step 3: Lesson Templates
1. Design template selection interface
2. Create predefined lesson templates
3. Implement template-based lesson creation
4. Add template customization options
5. Test template functionality

### Step 4: Content Validation
1. Implement comprehensive content validation
2. Add quality checks for different content types
3. Create validation reporting system
4. Add automated validation triggers
5. Test validation accuracy

### Step 5: Integration and Polish
1. Integrate all new features with existing system
2. Add enhanced UI/UX elements
3. Implement error handling and edge cases
4. Create comprehensive testing suite
5. Add documentation and help text

## Testing Checklist

### Prerequisites Testing
- [ ] Prerequisites can be added and removed
- [ ] Circular dependency detection works
- [ ] Dependency tree displays correctly
- [ ] Prerequisites are enforced in student view
- [ ] Search and filtering work in prerequisites modal

### Publishing Workflow Testing
- [ ] Status changes work correctly
- [ ] Content validation identifies issues
- [ ] Publishing controls are properly enabled/disabled
- [ ] Status history is tracked
- [ ] Published lessons appear in student view

### Template System Testing
- [ ] All templates create lessons correctly
- [ ] Template content is properly structured
- [ ] Created lessons can be edited normally
- [ ] Template selection interface works
- [ ] Templates create appropriate content types

### Content Validation Testing
- [ ] All validation rules work correctly
- [ ] Validation results are clearly displayed
- [ ] Validation prevents publishing incomplete lessons
- [ ] Warning vs error classifications are appropriate
- [ ] Validation performance is acceptable

## Success Criteria
- ✅ Complete prerequisites management system
- ✅ Professional publishing workflow
- ✅ Comprehensive content validation
- ✅ Useful lesson templates
- ✅ Intuitive admin interface
- ✅ Robust dependency management
- ✅ Quality assurance for published content

## Files to Modify
1. `app/templates/admin/manage_lessons.html` - Prerequisites and publishing interfaces
2. `app/routes.py` - Prerequisites and publishing API endpoints
3. `app/models.py` - Additional model methods (if needed)

## Files to Create
None (all changes are enhancements to existing files)

## Project Completion
Phase 6 completes the lesson enhancement project by:
- Providing complete lesson dependency management
- Ensuring content quality through validation
- Streamlining lesson creation with templates
- Creating a professional publishing workflow

After Phase 6, the admin will have a complete, professional-grade lesson creation and management system that supports:
- Unlimited sub-lessons with various content types
- Rich multimedia content with file uploads
- Interactive elements and quizzes
- Comprehensive content organization
- Professional publishing controls
- Quality assurance and validation

The system will provide a complete workflow from lesson creation to student learning, with proper content sequencing, quality controls, and engaging interactive elements.
