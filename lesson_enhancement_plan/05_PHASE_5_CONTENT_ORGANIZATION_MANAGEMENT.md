# Phase 5: Content Organization & Management

## Overview
Add advanced content organization and management features including drag-and-drop reordering, content preview, bulk operations, and enhanced content management tools. This phase focuses on improving the admin experience when managing lesson content.

## Duration
1-2 days

## Goals
- Implement drag-and-drop content reordering
- Add content preview functionality
- Create bulk content operations
- Implement content duplication and templates
- Add content search and filtering
- Enhance content editing capabilities
- Create content validation and quality checks

## Prerequisites
- Phases 1-4 must be completed and tested
- All content types must be working properly
- Interactive content system must be operational

## Technical Implementation

### 1. Drag-and-Drop Content Reordering
**File**: `app/templates/admin/manage_lessons.html`

**Enhanced Content Table with Drag-and-Drop:**
```html
<!-- Enhanced Lesson Content Table -->
<div class="table-responsive">
    <table class="table table-sm" id="lessonContentTable">
        <thead>
            <tr>
                <th width="50">Order</th>
                <th>Type</th>
                <th>Title</th>
                <th>Status</th>
                <th>Optional</th>
                <th width="200">Actions</th>
            </tr>
        </thead>
        <tbody id="sortableContentList">
            <!-- Content will be loaded via JavaScript with drag handles -->
        </tbody>
    </table>
</div>

<!-- Content Preview Modal -->
<div id="contentPreviewModal" class="modal" style="display: none;">
    <div class="modal-content" style="max-width: 900px;">
        <div class="modal-header">
            <h4>Content Preview</h4>
            <span class="close" onclick="closeModal('contentPreviewModal')">&times;</span>
        </div>
        <div class="modal-body">
            <div id="contentPreviewContainer">
                <!-- Preview content will be loaded here -->
            </div>
        </div>
        <div class="modal-footer">
            <button type="button" class="btn btn-secondary" onclick="closeModal('contentPreviewModal')">Close</button>
            <button type="button" class="btn btn-primary" onclick="editContentFromPreview()">Edit Content</button>
        </div>
    </div>
</div>

<!-- Bulk Operations Panel -->
<div class="bulk-operations-panel mt-3" style="display: none;" id="bulkOperationsPanel">
    <div class="card">
        <div class="card-body">
            <h6>Bulk Operations</h6>
            <div class="btn-group" role="group">
                <button type="button" class="btn btn-sm btn-outline-primary" onclick="bulkSetOptional(true)">
                    Mark as Optional
                </button>
                <button type="button" class="btn btn-sm btn-outline-primary" onclick="bulkSetOptional(false)">
                    Mark as Required
                </button>
                <button type="button" class="btn btn-sm btn-outline-warning" onclick="bulkDuplicate()">
                    Duplicate Selected
                </button>
                <button type="button" class="btn btn-sm btn-outline-danger" onclick="bulkDelete()">
                    Delete Selected
                </button>
            </div>
            <button type="button" class="btn btn-sm btn-secondary float-right" onclick="hideBulkOperations()">
                Cancel
            </button>
        </div>
    </div>
</div>
```

### 2. Enhanced JavaScript for Content Management
**File**: `app/templates/admin/manage_lessons.html` (JavaScript section)

**Drag-and-Drop and Management Functions:**
```javascript
// Initialize drag-and-drop functionality
function initializeDragAndDrop() {
    const sortableList = document.getElementById('sortableContentList');
    
    if (typeof Sortable !== 'undefined') {
        new Sortable(sortableList, {
            animation: 150,
            handle: '.drag-handle',
            onEnd: function(evt) {
                updateContentOrder();
            }
        });
    } else {
        // Load SortableJS if not already loaded
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/sortablejs@1.15.0/Sortable.min.js';
        script.onload = function() {
            new Sortable(sortableList, {
                animation: 150,
                handle: '.drag-handle',
                onEnd: function(evt) {
                    updateContentOrder();
                }
            });
        };
        document.head.appendChild(script);
    }
}

// Enhanced content loading with drag-and-drop support
async function loadLessonContent(lessonId) {
    try {
        const response = await fetch(`/api/admin/lessons/${lessonId}/content`);
        const content = await response.json();
        
        const tbody = document.querySelector('#lessonContentTable tbody');
        tbody.innerHTML = '';
        
        content.forEach((item, index) => {
            const row = document.createElement('tr');
            row.setAttribute('data-content-id', item.id);
            row.innerHTML = `
                <td>
                    <div class="d-flex align-items-center">
                        <span class="drag-handle me-2" style="cursor: move;">⋮⋮</span>
                        <span class="order-number">${item.order_index}</span>
                    </div>
                </td>
                <td>
                    <span class="badge ${getContentTypeBadgeClass(item.content_type)}">${item.content_type}</span>
                    ${item.is_interactive ? '<span class="badge bg-info ms-1">Interactive</span>' : ''}
                </td>
                <td>
                    <div class="content-title">
                        ${item.title || `${item.content_type} #${item.content_id || 'Custom'}`}
                    </div>
                    ${item.content_text ? `<small class="text-muted">${truncateText(item.content_text, 50)}</small>` : ''}
                </td>
                <td>
                    <span class="badge ${item.is_published ? 'bg-success' : 'bg-secondary'}">
                        ${item.is_published ? 'Published' : 'Draft'}
                    </span>
                </td>
                <td>
                    <span class="badge ${item.is_optional ? 'bg-warning' : 'bg-success'}">
                        ${item.is_optional ? 'Optional' : 'Required'}
                    </span>
                </td>
                <td>
                    <div class="btn-group btn-group-sm" role="group">
                        <input type="checkbox" class="content-checkbox me-2" value="${item.id}" onchange="toggleBulkOperations()">
                        <button class="btn btn-outline-info" onclick="previewContent(${item.id})" title="Preview">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn btn-outline-primary" onclick="editContent(${item.id})" title="Edit">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-outline-secondary" onclick="duplicateContent(${item.id})" title="Duplicate">
                            <i class="fas fa-copy"></i>
                        </button>
                        <button class="btn btn-outline-danger" onclick="removeContent(${lessonId}, ${item.id})" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            `;
            tbody.appendChild(row);
        });
        
        // Initialize drag-and-drop after content is loaded
        initializeDragAndDrop();
        
    } catch (error) {
        console.error('Error loading lesson content:', error);
        alert('Error loading lesson content');
    }
}

// Update content order after drag-and-drop
async function updateContentOrder() {
    const rows = document.querySelectorAll('#lessonContentTable tbody tr');
    const orderUpdates = [];
    
    rows.forEach((row, index) => {
        const contentId = row.getAttribute('data-content-id');
        const orderNumber = row.querySelector('.order-number');
        orderNumber.textContent = index;
        
        orderUpdates.push({
            content_id: parseInt(contentId),
            order_index: index
        });
    });
    
    try {
        const response = await fetch(`/api/admin/lessons/${currentLessonId}/content/reorder`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ order_updates: orderUpdates })
        });
        
        if (!response.ok) {
            throw new Error('Failed to update content order');
        }
    } catch (error) {
        console.error('Error updating content order:', error);
        alert('Error updating content order');
        // Reload content to restore original order
        loadLessonContent(currentLessonId);
    }
}

// Content preview functionality
async function previewContent(contentId) {
    try {
        const response = await fetch(`/api/admin/content/${contentId}/preview`);
        const previewData = await response.json();
        
        const previewContainer = document.getElementById('contentPreviewContainer');
        previewContainer.innerHTML = generateContentPreview(previewData);
        
        openModal('contentPreviewModal');
    } catch (error) {
        console.error('Error loading content preview:', error);
        alert('Error loading content preview');
    }
}

function generateContentPreview(content) {
    let previewHtml = `<h5>${content.title || 'Untitled Content'}</h5>`;
    
    switch (content.content_type) {
        case 'text':
            previewHtml += `<div class="rich-text-content">${content.content_text || ''}</div>`;
            break;
            
        case 'image':
            if (content.media_url || content.file_path) {
                previewHtml += `<img src="${content.media_url || content.file_path}" class="img-fluid" alt="${content.title}">`;
            }
            if (content.content_text) {
                previewHtml += `<p class="mt-2">${content.content_text}</p>`;
            }
            break;
            
        case 'video':
            if (content.media_url || content.file_path) {
                previewHtml += `
                    <div class="ratio ratio-16x9">
                        <video controls>
                            <source src="${content.media_url || content.file_path}" type="video/mp4">
                            Your browser does not support the video tag.
                        </video>
                    </div>
                `;
            }
            break;
            
        case 'audio':
            if (content.media_url || content.file_path) {
                previewHtml += `
                    <audio controls class="w-100">
                        <source src="${content.media_url || content.file_path}" type="audio/mpeg">
                        Your browser does not support the audio element.
                    </audio>
                `;
            }
            break;
            
        case 'interactive':
            previewHtml += '<div class="alert alert-info">Interactive content preview not available in admin panel. View in lesson to test functionality.</div>';
            if (content.quiz_questions && content.quiz_questions.length > 0) {
                previewHtml += '<h6>Questions:</h6><ul>';
                content.quiz_questions.forEach(q => {
                    previewHtml += `<li>${q.question_text}</li>`;
                });
                previewHtml += '</ul>';
            }
            break;
            
        default:
            if (content.content_data) {
                previewHtml += `<div class="alert alert-secondary">Content Type: ${content.content_type}</div>`;
                previewHtml += `<pre>${JSON.stringify(content.content_data, null, 2)}</pre>`;
            }
    }
    
    return previewHtml;
}

// Bulk operations functionality
function toggleBulkOperations() {
    const checkboxes = document.querySelectorAll('.content-checkbox:checked');
    const bulkPanel = document.getElementById('bulkOperationsPanel');
    
    if (checkboxes.length > 0) {
        bulkPanel.style.display = 'block';
    } else {
        bulkPanel.style.display = 'none';
    }
}

function hideBulkOperations() {
    document.getElementById('bulkOperationsPanel').style.display = 'none';
    document.querySelectorAll('.content-checkbox').forEach(cb => cb.checked = false);
}

async function bulkSetOptional(isOptional) {
    const selectedIds = getSelectedContentIds();
    if (selectedIds.length === 0) return;
    
    try {
        const response = await fetch(`/api/admin/lessons/${currentLessonId}/content/bulk-update`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                content_ids: selectedIds,
                updates: { is_optional: isOptional }
            })
        });
        
        if (response.ok) {
            loadLessonContent(currentLessonId);
            hideBulkOperations();
            alert(`Content marked as ${isOptional ? 'optional' : 'required'} successfully!`);
        } else {
            throw new Error('Failed to update content');
        }
    } catch (error) {
        console.error('Error updating content:', error);
        alert('Error updating content');
    }
}

async function bulkDuplicate() {
    const selectedIds = getSelectedContentIds();
    if (selectedIds.length === 0) return;
    
    if (!confirm(`Duplicate ${selectedIds.length} content item(s)?`)) return;
    
    try {
        const response = await fetch(`/api/admin/lessons/${currentLessonId}/content/bulk-duplicate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content_ids: selectedIds })
        });
        
        if (response.ok) {
            loadLessonContent(currentLessonId);
            loadLessons(); // Update content count in main table
            hideBulkOperations();
            alert('Content duplicated successfully!');
        } else {
            throw new Error('Failed to duplicate content');
        }
    } catch (error) {
        console.error('Error duplicating content:', error);
        alert('Error duplicating content');
    }
}

async function bulkDelete() {
    const selectedIds = getSelectedContentIds();
    if (selectedIds.length === 0) return;
    
    if (!confirm(`Delete ${selectedIds.length} content item(s)? This action cannot be undone.`)) return;
    
    try {
        const response = await fetch(`/api/admin/lessons/${currentLessonId}/content/bulk-delete`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content_ids: selectedIds })
        });
        
        if (response.ok) {
            loadLessonContent(currentLessonId);
            loadLessons(); // Update content count in main table
            hideBulkOperations();
            alert('Content deleted successfully!');
        } else {
            throw new Error('Failed to delete content');
        }
    } catch (error) {
        console.error('Error deleting content:', error);
        alert('Error deleting content');
    }
}

function getSelectedContentIds() {
    const checkboxes = document.querySelectorAll('.content-checkbox:checked');
    return Array.from(checkboxes).map(cb => parseInt(cb.value));
}

// Content duplication
async function duplicateContent(contentId) {
    if (!confirm('Duplicate this content item?')) return;
    
    try {
        const response = await fetch(`/api/admin/content/${contentId}/duplicate`, {
            method: 'POST'
        });
        
        if (response.ok) {
            loadLessonContent(currentLessonId);
            loadLessons(); // Update content count in main table
            alert('Content duplicated successfully!');
        } else {
            throw new Error('Failed to duplicate content');
        }
    } catch (error) {
        console.error('Error duplicating content:', error);
        alert('Error duplicating content');
    }
}

// Utility functions
function getContentTypeBadgeClass(contentType) {
    const badgeClasses = {
        'kana': 'bg-primary',
        'kanji': 'bg-success',
        'vocabulary': 'bg-info',
        'grammar': 'bg-warning',
        'text': 'bg-secondary',
        'image': 'bg-purple',
        'video': 'bg-danger',
        'audio': 'bg-dark',
        'interactive': 'bg-orange'
    };
    return badgeClasses[contentType] || 'bg-light';
}

function truncateText(text, maxLength) {
    if (!text) return '';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
}
```

### 3. API Endpoints for Content Management
**File**: `app/routes.py`

**New Content Management Endpoints:**
```python
@bp.route('/api/admin/lessons/<int:lesson_id>/content/reorder', methods=['PUT'])
@login_required
@admin_required
def reorder_lesson_content(lesson_id):
    """Reorder lesson content items"""
    lesson = Lesson.query.get_or_404(lesson_id)
    data = request.json
    
    if not data or 'order_updates' not in data:
        return jsonify({"error": "Missing order updates"}), 400
    
    try:
        for update in data['order_updates']:
            content = LessonContent.query.filter_by(
                lesson_id=lesson_id, 
                id=update['content_id']
            ).first()
            if content:
                content.order_index = update['order_index']
        
        db.session.commit()
        return jsonify({"message": "Content order updated successfully"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update content order"}), 500

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
```

### 4. Enhanced CSS for Content Management
**File**: `app/templates/admin/base_admin.html` (CSS section)

**Content Management Styling:**
```css
<style>
/* Drag and Drop Styling */
.drag-handle {
    color: #6c757d;
    font-size: 14px;
    cursor: move;
    user-select: none;
}

.drag-handle:hover {
    color: #495057;
}

.sortable-ghost {
    opacity: 0.4;
    background-color: #f8f9fa;
}

.sortable-chosen {
    background-color: #e3f2fd;
}

/* Content Table Enhancements */
#lessonContentTable tbody tr {
    transition: background-color 0.2s ease;
}

#lessonContentTable tbody tr:hover {
    background-color: #f8f9fa;
}

.content-checkbox {
    transform: scale(1.2);
    margin-right: 8px;
}

.content-title {
    font-weight: 500;
    color: #2c3e50;
}

/* Bulk Operations Panel */
.bulk-operations-panel {
    position: sticky;
    bottom: 20px;
    z-index: 1000;
}

.bulk-operations-panel .card {
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    border: none;
}

/* Content Type Badges */
.badge.bg-purple {
    background-color: #6f42c1 !important;
}

.badge.bg-orange {
    background-color: #fd7e14 !important;
}

/* Content Preview Modal */
#contentPreviewModal .modal-content {
    max-height: 80vh;
    overflow-y: auto;
}

#contentPreviewContainer {
    max-height: 60vh;
    overflow-y: auto;
    padding: 1rem;
    border: 1px solid #dee2e6;
    border-radius: 0.375rem;
    background-color: #f8f9fa;
}

/* Action Buttons */
.btn-group-sm .btn {
    padding: 0.25rem 0.5rem;
    font-size: 0.875rem;
}

.btn-outline-info:hover {
    color: #fff;
    background-color: #17a2b8;
    border-color: #17a2b8;
}

/* Loading States */
.loading-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(255, 255, 255, 0.8);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
}

.loading-spinner {
    border: 3px solid #f3f3f3;
    border-top: 3px solid #007bff;
    border-radius: 50%;
    width: 30px;
    height: 30px;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* Responsive Adjustments */
@media (max-width: 768px) {
    .btn-group-sm .btn {
        padding: 0.125rem 0.25rem;
        font-size: 0.75rem;
    }
    
    .bulk-operations-panel .btn-group {
        flex-direction: column;
    }
    
    .bulk-operations-panel .btn {
        margin-bottom: 0.25rem;
    }
}
</style>
```

## Implementation Steps

### Step 1: Drag-and-Drop Implementation
1. Add SortableJS library integration
2. Update content table with drag handles
3. Implement reordering API endpoint
4. Test drag-and-drop functionality

### Step 2: Content Preview System
1. Create content preview modal
2. Implement preview generation for all content types
3. Add preview API endpoint
4. Test preview functionality

### Step 3: Bulk Operations
1. Add bulk selection checkboxes
2. Implement bulk operations panel
3. Create bulk operation API endpoints
4. Test bulk functionality

### Step 4: Content Duplication
1. Implement single content duplication
2. Add bulk duplication functionality
3. Handle interactive content duplication
4. Test duplication features

### Step 5: Enhanced UI/UX
1. Add improved styling and animations
2. Implement loading states
3. Add responsive design improvements
4. Test user experience

## Testing Checklist

### Drag-and-Drop Testing
- [ ] Content items can be reordered by dragging
- [ ] Order changes
