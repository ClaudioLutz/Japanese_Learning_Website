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

Located at `/course/{id}`, provides:

#### Features

1. **Course Information Display**
   - Course title and description
   - Background image
   - Course metadata

2. **Lesson Listing**
   - Ordered list of course lessons
   - Direct links to individual lessons
   - Lesson accessibility indicators

3. **Navigation Integration**
   - Breadcrumb navigation
   - Return to courses link
   - Lesson progression tracking

#### Course View Template

```html
<div class="container mt-5">
    <div class="row">
        <div class="col-md-8">
            <h1>{{ course.title }}</h1>
            <p>{{ course.description }}</p>
            <hr>
            <h2>Lessons</h2>
            <div class="list-group">
                {% for lesson in course.lessons %}
                    <a href="{{ url_for('routes.view_lesson', lesson_id=lesson.id) }}" 
                       class="list-group-item list-group-item-action">
                        {{ lesson.title }}
                    </a>
                {% endfor %}
            </div>
        </div>
        <div class="col-md-4">
            <img src="{{ course.background_image_url or 'https://via.placeholder.com/600x400' }}" 
                 class="img-fluid rounded" alt="{{ course.title }}">
        </div>
    </div>
</div>
```

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
