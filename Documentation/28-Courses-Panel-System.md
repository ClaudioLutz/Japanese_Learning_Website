# 28. Courses Panel System

## Overview

The Courses Panel System is a comprehensive feature that allows administrators to create, manage, and organize lessons into structured courses. It provides both administrative management capabilities and a user-facing interface for browsing and accessing courses.

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Database Schema](#database-schema)
3. [Administrative Interface](#administrative-interface)
4. [User Interface](#user-interface)
5. [API Endpoints](#api-endpoints)
6. [Frontend Implementation](#frontend-implementation)
7. [Security Features](#security-features)
8. [Usage Examples](#usage-examples)
9. [Integration Points](#integration-points)
10. [Future Enhancements](#future-enhancements)

## System Architecture

The Courses Panel System consists of several interconnected components:

### Core Components

1. **Course Model**: Database entity representing a course
2. **Course-Lesson Relationship**: Many-to-many relationship between courses and lessons
3. **Administrative Interface**: Backend management system for courses
4. **User Interface**: Frontend course browsing and viewing system
5. **API Layer**: RESTful endpoints for course operations

### Data Flow

```
Admin Creates Course → Course Database → API Layer → User Interface → Course Display
                   ↓
            Assigns Lessons → Course-Lesson Mapping → Lesson Access Control
```

## Database Schema

### Course Model

```python
class Course(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    background_image_url: Mapped[str] = mapped_column(String(255), nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    lessons: Mapped[List['Lesson']] = relationship('Lesson', secondary=course_lessons, lazy='subquery',
                              back_populates='courses')
```

### Course-Lesson Association Table

```python
course_lessons = Table('course_lessons', db.metadata,
    Column('course_id', Integer, ForeignKey('course.id'), primary_key=True),
    Column('lesson_id', Integer, ForeignKey('lesson.id'), primary_key=True)
)
```

### Key Fields

- **id**: Primary key identifier
- **title**: Course name (required)
- **description**: Detailed course description
- **background_image_url**: URL for course thumbnail/banner
- **is_published**: Controls course visibility to users
- **created_at/updated_at**: Timestamp tracking
- **lessons**: Many-to-many relationship with lessons

## Administrative Interface

### Course Management Dashboard

Located at `/admin/manage/courses`, the administrative interface provides:

#### Features

1. **Course Listing Table**
   - Course ID, title, description
   - Publication status
   - Number of associated lessons
   - Action buttons (Edit, Delete)

2. **Course Creation/Editing Modal**
   - Title input (required)
   - Description textarea
   - Background image URL field
   - Publication status checkbox
   - Multi-select lesson assignment

3. **Lesson Assignment**
   - Multi-select dropdown of available lessons
   - Real-time lesson count display
   - Ctrl/Cmd multi-selection support

#### Administrative Routes

- `GET /admin/manage/courses` - Course management dashboard
- `POST /api/admin/courses/new` - Create new course
- `PUT /api/admin/courses/{id}/edit` - Update existing course
- `DELETE /api/admin/courses/{id}/delete` - Delete course
- `GET /api/admin/courses/{id}` - Get course details

### Course Creation Workflow

1. Admin clicks "Add New Course" button
2. Modal opens with empty form
3. Admin fills in course details
4. Admin selects lessons to include
5. Form submission creates course with lesson associations
6. Table refreshes with new course

### Course Editing Workflow

1. Admin clicks edit button for existing course
2. Modal opens pre-populated with course data
3. Lesson selections reflect current associations
4. Admin modifies fields as needed
5. Form submission updates course and lesson associations
6. Table refreshes with updated data

## User Interface

### Course Browsing Page

Located at `/courses`, provides:

#### Features

1. **Course Grid Display**
   - Card-based layout
   - Course thumbnails/background images
   - Course titles and descriptions
   - "View Course" action buttons

2. **Dynamic Loading**
   - AJAX-based course fetching
   - Error handling for failed requests
   - Loading states and fallbacks

3. **Publication Filtering**
   - Only published courses visible to users
   - Automatic filtering in API responses

#### Course Browsing Template

```html
{% extends "base.html" %}

{% block content %}
<div class="container mt-5">
    <h1>Courses</h1>
    <div class="row">
        <!-- Courses populated by JavaScript -->
    </div>
</div>
{% endblock %}
```

### Individual Course View

Located at `/course/{id}`, provides a comprehensive and professional course overview:

#### Features

1. **Professional Header Banner**
   - Full-width course background image with overlay
   - Course title and description prominently displayed
   - Overall course progress bar with percentage
   - Dynamic action button (Start Course / Continue Course)
   - Responsive design with mobile optimization

2. **Enhanced Lesson Cards**
   - **Fully Clickable Cards**: Entire lesson card is clickable, not just the title
   - Visual status indicators (completed, in-progress, not-started)
   - Individual lesson progress bars
   - Status badges showing completion percentage
   - Lesson metadata (duration, difficulty level)
   - Hover effects with enhanced shadows and border highlighting
   - Keyboard accessibility with focus indicators

3. **Course Statistics Sidebar**
   - Total lessons count
   - Completed lessons tracking
   - Total course duration
   - Average difficulty level
   - Overall progress visualization
   - Course thumbnail with description

4. **User Progress Integration**
   - Real-time progress tracking per lesson
   - Course completion percentage calculation
   - Visual progress indicators throughout the interface
   - Status-based lesson organization

5. **Professional Styling**
   - Bootstrap 5 components with custom CSS
   - Font Awesome icons for enhanced visual elements
   - Responsive grid layout
   - Smooth animations and transitions
   - Professional color scheme and typography

#### Enhanced Course View Template Structure

```html
<!-- Course Header Banner -->
<div class="course-header-banner" style="background-image: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), url('{{ course.background_image_url }}');">
    <div class="container">
        <div class="course-header-content text-white">
            <h1 class="display-4 mb-3">{{ course.title }}</h1>
            <p class="lead mb-4">{{ course.description }}</p>
            
            <!-- Progress Bar -->
            <div class="progress mb-3" style="height: 8px;">
                <div class="progress-bar bg-success" style="width: {{ course_progress_percentage }}%;"></div>
            </div>
            <small class="text-light">{{ course_progress_percentage }}% Complete</small>
            
            <!-- Dynamic Action Button -->
            <div class="mt-4">
                {% if has_started %}
                    <a href="#lessons" class="btn btn-primary btn-lg">
                        <i class="fas fa-play-circle me-2"></i>Continue Course
                    </a>
                {% else %}
                    <a href="#lessons" class="btn btn-success btn-lg">
                        <i class="fas fa-rocket me-2"></i>Start Course
                    </a>
                {% endif %}
            </div>
        </div>
    </div>
</div>

<!-- Main Content Area -->
<div class="container mt-5">
    <div class="row">
        <!-- Lesson Cards (Main Content) -->
        <div class="col-lg-8">
            <section id="lessons">
                <div class="d-flex justify-content-between align-items-center mb-4">
                    <h2 class="mb-0">
                        <i class="fas fa-list-ul me-2 text-primary"></i>Course Lessons
                    </h2>
                    <span class="badge bg-secondary fs-6">{{ total_lessons }} Lessons</span>
                </div>
                
                <!-- Enhanced Clickable Lesson Cards -->
                {% for lesson in course.lessons %}
                    <div class="lesson-card mb-3">
                        <a href="{{ url_for('routes.view_lesson', lesson_id=lesson.id) }}" 
                           class="lesson-card-link text-decoration-none">
                            <div class="card border-0 shadow-sm">
                                <div class="card-body">
                                    <div class="row align-items-center">
                                        <!-- Status Indicator -->
                                        <div class="col-auto">
                                            <div class="lesson-status {{ status_class }}">
                                                <!-- Dynamic icon based on progress -->
                                            </div>
                                        </div>
                                        
                                        <!-- Lesson Content -->
                                        <div class="col">
                                            <h5 class="lesson-title mb-1 text-dark">{{ lesson.title }}</h5>
                                            <p class="lesson-description text-muted mb-2">{{ lesson.description }}</p>
                                            <div class="lesson-meta">
                                                <small class="text-muted">
                                                    <i class="fas fa-clock me-1"></i>{{ lesson.estimated_duration }} min
                                                    <span class="ms-3">
                                                        <i class="fas fa-signal me-1"></i>{{ difficulty_level }}
                                                    </span>
                                                </small>
                                            </div>
                                            
                                            <!-- Individual Progress Bar -->
                                            {% if progress_percent > 0 %}
                                                <div class="progress mt-2" style="height: 4px;">
                                                    <div class="progress-bar bg-primary" style="width: {{ progress_percent }}%;"></div>
                                                </div>
                                            {% endif %}
                                        </div>
                                        
                                        <!-- Status Badge -->
                                        <div class="col-auto">
                                            <span class="badge {{ badge_class }}">{{ status_text }}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </a>
                    </div>
                {% endfor %}
            </section>
        </div>
        
        <!-- Course Statistics Sidebar -->
        <div class="col-lg-4">
            <div class="course-sidebar">
                <!-- Course Stats Card -->
                <div class="card border-0 shadow-sm mb-4">
                    <div class="card-header bg-primary text-white">
                        <h5 class="mb-0">
                            <i class="fas fa-chart-line me-2"></i>Course Overview
                        </h5>
                    </div>
                    <div class="card-body">
                        <!-- Statistics Display -->
                        <div class="course-stats">
                            <div class="stat-item mb-3">
                                <div class="d-flex justify-content-between">
                                    <span class="text-muted">Total Lessons:</span>
                                    <strong>{{ total_lessons }}</strong>
                                </div>
                            </div>
                            <div class="stat-item mb-3">
                                <div class="d-flex justify-content-between">
                                    <span class="text-muted">Completed:</span>
                                    <strong class="text-success">{{ completed_lessons }}</strong>
                                </div>
                            </div>
                            <!-- Additional stats... -->
                        </div>
                        
                        <!-- Overall Progress Visualization -->
                        <div class="mt-4">
                            <div class="d-flex justify-content-between mb-2">
                                <span class="text-muted">Overall Progress</span>
                                <span class="fw-bold">{{ course_progress_percentage }}%</span>
                            </div>
                            <div class="progress" style="height: 10px;">
                                <div class="progress-bar bg-gradient" style="width: {{ course_progress_percentage }}%;"></div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Course Image Card -->
                <div class="card border-0 shadow-sm">
                    <img src="{{ course.background_image_url }}" class="card-img-top" alt="{{ course.title }}">
                    <div class="card-body text-center">
                        <h6 class="card-title">{{ course.title }}</h6>
                        <p class="card-text text-muted small">
                            Master Japanese with structured lessons and interactive content.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
```

#### Enhanced CSS Styling

```css
/* Course Header Banner */
.course-header-banner {
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    padding: 80px 0;
    margin-top: -20px;
}

/* Clickable Lesson Cards */
.lesson-card-link {
    display: block;
    cursor: pointer;
    transition: all 0.2s ease-in-out;
}

.lesson-card-link:hover {
    text-decoration: none !important;
}

.lesson-card-link:hover .card {
    box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15) !important;
    border-color: #007bff !important;
}

.lesson-card-link:hover .lesson-title {
    color: #0d6efd !important;
}

.lesson-card-link:focus {
    outline: 2px solid #007bff;
    outline-offset: 2px;
    border-radius: 0.375rem;
}

/* Lesson Status Indicators */
.lesson-status {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
}

.lesson-status.completed {
    background-color: #d4edda;
}

.lesson-status.in-progress {
    background-color: #fff3cd;
}

.lesson-status.not-started {
    background-color: #f8f9fa;
    border: 2px solid #dee2e6;
    color: #6c757d;
    font-weight: bold;
}

/* Responsive Design */
@media (max-width: 768px) {
    .course-header-banner {
        padding: 40px 0;
    }
    
    .course-header-content h1 {
        font-size: 2rem;
    }
    
    .course-sidebar {
        position: static;
        margin-top: 2rem;
    }
}
```

## Backend Route Implementation

### Enhanced Course View Route

The `view_course` route in `app/routes.py` has been enhanced to provide comprehensive course and progress data:

```python
@bp.route('/course/<int:course_id>')
@login_required
def view_course(course_id):
    course = Course.query.get_or_404(course_id)
    
    # Get user progress for all lessons in the course
    lesson_progress = {}
    for lesson in course.lessons:
        progress = UserProgress.query.filter_by(
            user_id=current_user.id, 
            lesson_id=lesson.id
        ).first()
        lesson_progress[lesson.id] = progress
    
    # Calculate course statistics
    total_lessons = len(course.lessons)
    completed_lessons = sum(1 for progress in lesson_progress.values() 
                          if progress and progress.is_completed)
    
    # Calculate overall course progress percentage
    if total_lessons > 0:
        course_progress_percentage = round((completed_lessons / total_lessons) * 100)
    else:
        course_progress_percentage = 0
    
    # Calculate total duration and average difficulty
    total_duration = sum(lesson.estimated_duration or 0 for lesson in course.lessons)
    difficulties = [lesson.difficulty_level for lesson in course.lessons 
                   if lesson.difficulty_level is not None]
    average_difficulty = sum(difficulties) / len(difficulties) if difficulties else 0
    
    # Determine if user has started the course
    has_started = any(progress and progress.progress_percentage > 0 
                     for progress in lesson_progress.values())
    
    return render_template('course_view.html',
                         course=course,
                         lesson_progress=lesson_progress,
                         course_progress_percentage=course_progress_percentage,
                         total_lessons=total_lessons,
                         completed_lessons=completed_lessons,
                         total_duration=total_duration,
                         average_difficulty=average_difficulty,
                         has_started=has_started)
```

#### Key Features of Enhanced Route

1. **Progress Tracking Integration**
   - Fetches user progress for each lesson in the course
   - Calculates completion status and progress percentages
   - Determines if user has started the course

2. **Course Statistics Calculation**
   - Total lesson count
   - Completed lesson count
   - Overall course progress percentage
   - Total estimated duration
   - Average difficulty level

3. **Template Data Preparation**
   - Organizes all data for efficient template rendering
   - Provides comprehensive context for UI components
   - Enables dynamic content based on user progress

## API Endpoints

### Administrative API

#### Course CRUD Operations

```python
# List all courses (admin)
GET /api/admin/courses
Response: [{"id": 1, "title": "Course Name", ...}, ...]

# Create new course
POST /api/admin/courses/new
Headers: X-CSRFToken: <token>
Body: {
    "title": "Course Title",
    "description": "Course Description",
    "background_image_url": "https://example.com/image.jpg",
    "is_published": true,
    "lessons": [1, 2, 3]
}

# Get course details
GET /api/admin/courses/{id}
Response: {
    "id": 1,
    "title": "Course Title",
    "lessons": [{"id": 1, "title": "Lesson 1"}, ...]
}

# Update course
PUT /api/admin/courses/{id}/edit
Headers: X-CSRFToken: <token>
Body: {
    "title": "Updated Title",
    "lessons": [1, 2, 4]
}

# Delete course
DELETE /api/admin/courses/{id}/delete
Headers: X-CSRFToken: <token>
```

### Public API

#### Course Access for Users

```python
# Get published courses
GET /api/courses
Response: [{"id": 1, "title": "Course Name", "is_published": true}, ...]

# Access individual course (via route)
GET /course/{id}
Returns: Course view template with lessons
```

## Frontend Implementation

### JavaScript Course Management

#### Course Loading and Display

```javascript
// Load courses data
async function loadCourses() {
    try {
        const response = await fetch('/api/admin/courses');
        if (!response.ok) throw new Error('Failed to load courses');
        
        coursesData = await response.json();
        renderCoursesTable();
    } catch (error) {
        console.error('Error loading courses:', error);
        alert('Failed to load courses. Please refresh the page.');
    }
}

// Render courses table
function renderCoursesTable() {
    const tbody = document.querySelector('#coursesTable tbody');
    tbody.innerHTML = '';
    
    coursesData.forEach(course => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${course.id}</td>
            <td>${course.title || ''}</td>
            <td>${course.description || ''}</td>
            <td><span class="badge ${course.is_published ? 'badge-success' : 'badge-secondary'}">
                ${course.is_published ? 'Yes' : 'No'}</span></td>
            <td>${course.lessons ? course.lessons.length : 0}</td>
            <td class="actions">
                <button class="btn btn-warning btn-sm" onclick="editCourse(${course.id})">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-danger btn-sm" onclick="deleteCourse(${course.id})">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}
```

#### Course Form Handling

```javascript
// Save course
async function saveCourse() {
    const courseId = document.getElementById('courseId').value;
    const title = document.getElementById('courseTitle').value.trim();
    
    if (!title) {
        alert('Please enter a course title.');
        return;
    }
    
    const select = document.getElementById('courseLessons');
    const selectedLessons = Array.from(select.selectedOptions).map(option => parseInt(option.value));
    
    const courseData = {
        title: title,
        description: document.getElementById('courseDescription').value.trim(),
        background_image_url: document.getElementById('courseBackgroundImage').value.trim(),
        is_published: document.getElementById('courseIsPublished').checked,
        lessons: selectedLessons
    };
    
    try {
        const url = courseId ? `/api/admin/courses/${courseId}/edit` : '/api/admin/courses/new';
        const method = courseId ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify(courseData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to save course');
        }
        
        closeModal('courseModal');
        loadCourses();
        alert(courseId ? 'Course updated successfully!' : 'Course created successfully!');
        
    } catch (error) {
        console.error('Error saving course:', error);
        alert('Failed to save course: ' + error.message);
    }
}
```

### User-Facing Course Display

```javascript
$(document).ready(function() {
    $.get('/api/courses')
        .done(function(data) {
            console.log('API response:', data);
            let coursesRow = $('.row');
            coursesRow.empty();
            
            if (data && data.length > 0) {
                data.forEach(function(course) {
                    if (course.is_published) {
                        let courseCard = `
                            <div class="col-md-6 mb-4">
                                <div class="card h-100">
                                    <img src="${course.background_image_url || 'https://via.placeholder.com/600x400'}" 
                                         class="card-img-top" alt="${course.title}">
                                    <div class="card-body">
                                        <h5 class="card-title">${course.title}</h5>
                                        <p class="card-text">${course.description}</p>
                                        <a href="/course/${course.id}" class="btn btn-primary">View Course</a>
                                    </div>
                                </div>
                            </div>
                        `;
                        coursesRow.append(courseCard);
                    }
                });
            } else {
                coursesRow.append('<div class="col-12"><p class="text-center">No courses available.</p></div>');
            }
        })
        .fail(function(xhr, status, error) {
            console.error('API request failed:', status, error);
            let coursesRow = $('.row');
            coursesRow.empty();
            coursesRow.append('<div class="col-12"><p class="text-center text-danger">Error loading courses. Please refresh the page.</p></div>');
        });
});
```

## Security Features

### Access Control

1. **Administrative Access**
   - `@admin_required` decorator on management routes
   - CSRF token validation on all modification operations
   - User authentication verification

2. **Publication Control**
   - Only published courses visible to regular users
   - Draft courses accessible only to administrators
   - Automatic filtering in public API endpoints

3. **Data Validation**
   - Required field validation (title)
   - Input sanitization and length limits
   - SQL injection prevention through ORM

### CSRF Protection

```python
# CSRF token validation in course creation
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
```

## Usage Examples

### Creating a New Course

1. **Administrator Workflow**:
   ```
   1. Navigate to /admin/manage/courses
   2. Click "Add New Course" button
   3. Fill in course details:
      - Title: "Japanese Numbers"
      - Description: "Learn Japanese number system"
      - Background Image: URL to relevant image
      - Published: Check if ready for users
   4. Select lessons to include in course
   5. Click "Save" to create course
   ```

2. **API Usage**:
   ```javascript
   const courseData = {
       title: "Japanese Numbers",
       description: "Learn Japanese number system",
       background_image_url: "https://example.com/numbers.jpg",
       is_published: true,
       lessons: [1, 2, 3] // Lesson IDs
   };
   
   fetch('/api/admin/courses/new', {
       method: 'POST',
       headers: {
           'Content-Type': 'application/json',
           'X-CSRFToken': getCSRFToken()
       },
       body: JSON.stringify(courseData)
   });
   ```

### User Course Access

1. **Browsing Courses**:
   ```
   1. User navigates to /courses
   2. System displays published courses in card layout
   3. User clicks "View Course" on desired course
   4. System redirects to /course/{id}
   5. User sees course details and lesson list
   6. User clicks on lesson to start learning
   ```

## Integration Points

### Lesson System Integration

1. **Lesson Assignment**
   - Courses can contain multiple lessons
   - Lessons can belong to multiple courses
   - Many-to-many relationship management

2. **Progress Tracking**
   - User progress tracked per lesson
   - Course completion calculated from lesson progress
   - Progress indicators in course view

3. **Access Control**
   - Lesson accessibility rules apply within courses
   - Prerequisites maintained regardless of course context
   - Subscription level requirements enforced

### Navigation Integration

1. **Menu System**
   - Courses link in main navigation
   - Breadcrumb navigation in course views
   - Context-aware navigation elements

2. **User Dashboard**
   - Course progress display
   - Recently accessed courses
   - Recommended courses based on progress

## Future Enhancements

### Planned Features

1. **Course Categories**
   - Organize courses by subject/difficulty
   - Category-based filtering and browsing
   - Hierarchical course organization

2. **Course Prerequisites**
   - Course-level prerequisite system
   - Sequential course progression
   - Learning path recommendations

3. **Course Analytics**
   - Enrollment tracking
   - Completion rates
   - User engagement metrics

4. **Course Ratings and Reviews**
   - User feedback system
   - Rating aggregation
   - Review moderation tools

5. **Course Certificates**
   - Completion certificates
   - Achievement badges
   - Progress milestones

### Technical Improvements

1. **Performance Optimization**
   - Course data caching
   - Lazy loading of course content
   - Database query optimization

2. **Enhanced UI/UX**
   - Drag-and-drop lesson ordering
   - Rich text course descriptions
   - Advanced search and filtering

3. **Mobile Optimization**
   - Responsive course cards
   - Touch-friendly navigation
   - Mobile-specific course layouts

## Conclusion

The Courses Panel System provides a comprehensive solution for organizing and delivering structured learning content. It combines powerful administrative tools with an intuitive user interface, enabling effective course management and enhanced learning experiences. The system's modular design allows for future enhancements while maintaining compatibility with existing lesson and user management systems.
