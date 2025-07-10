# API Design

## 1. Overview

This document details the comprehensive API design for the Japanese Learning Website, including all endpoints, request/response formats, and authentication requirements. The API facilitates interaction between the frontend, administrative tools, and supports the complete lesson management and user progress tracking system.

## 2. Design Principles

- **RESTful Architecture**: Adheres to REST principles with clear resource-based URLs
- **JSON for Data Interchange**: Uses JSON for all request and response payloads
- **Statelessness**: Each API request contains all information needed to process it
- **Consistent Naming Conventions**: Uses snake_case for JSON keys and URL parameters
- **Standard HTTP Status Codes**: 
  - 200 OK (successful GET, PUT)
  - 201 Created (successful POST)
  - 400 Bad Request (validation errors)
  - 401 Unauthorized (authentication required)
  - 403 Forbidden (insufficient permissions)
  - 404 Not Found (resource not found)
  - 409 Conflict (duplicate resources)
  - 500 Internal Server Error (server errors)
- **Authentication & Authorization**: Secure endpoints using Flask-Login sessions and role-based access control
- **CSRF Protection**: All state-changing operations require CSRF tokens

## 3. Authentication

- API endpoints requiring authentication expect session cookies managed by Flask-Login
- Administrative API endpoints require both authentication and admin role
- CSRF tokens required for all POST, PUT, PATCH, DELETE operations
- Session-based authentication with automatic redirects for unauthorized access

## 4. API Endpoint Categories

### 4.1. User Authentication & Management

#### Public Authentication Routes
- `GET /` - Home page
- `GET /home` - Home page (alias)
- `GET /register` - Registration form
- `POST /register` - User registration
- `GET /login` - Login form  
- `POST /login` - User authentication
- `GET /logout` - User logout (requires login)

#### Subscription Management
- `POST /upgrade_to_premium` - Upgrade user to premium (requires login + CSRF)
- `POST /downgrade_from_premium` - Downgrade user to free (requires login + CSRF)

### 4.2. Admin - Core Content Management

All admin endpoints require `@login_required` and `@admin_required` decorators.

#### Kana Management
- `GET /api/admin/kana` - List all kana characters
- `POST /api/admin/kana/new` - Create new kana character
- `GET /api/admin/kana/<int:item_id>` - Get specific kana character
- `PUT /api/admin/kana/<int:item_id>/edit` - Update kana character
- `PATCH /api/admin/kana/<int:item_id>/edit` - Partial update kana character
- `DELETE /api/admin/kana/<int:item_id>/delete` - Delete kana character

**Request Format (POST/PUT)**:
```json
{
  "character": "あ",
  "romanization": "a",
  "type": "hiragana",
  "stroke_order_info": "Optional stroke order description",
  "example_sound_url": "Optional audio URL"
}
```

#### Kanji Management
- `GET /api/admin/kanji` - List all kanji characters
- `POST /api/admin/kanji/new` - Create new kanji character
- `GET /api/admin/kanji/<int:item_id>` - Get specific kanji character
- `PUT /api/admin/kanji/<int:item_id>/edit` - Update kanji character
- `PATCH /api/admin/kanji/<int:item_id>/edit` - Partial update kanji character
- `DELETE /api/admin/kanji/<int:item_id>/delete` - Delete kanji character

**Request Format (POST/PUT)**:
```json
{
  "character": "水",
  "meaning": "water",
  "onyomi": "スイ",
  "kunyomi": "みず",
  "jlpt_level": 5,
  "stroke_order_info": "Optional stroke order",
  "radical": "水",
  "stroke_count": 4
}
```

#### Vocabulary Management
- `GET /api/admin/vocabulary` - List all vocabulary items
- `POST /api/admin/vocabulary/new` - Create new vocabulary item
- `GET /api/admin/vocabulary/<int:item_id>` - Get specific vocabulary item
- `PUT /api/admin/vocabulary/<int:item_id>/edit` - Update vocabulary item
- `PATCH /api/admin/vocabulary/<int:item_id>/edit` - Partial update vocabulary item
- `DELETE /api/admin/vocabulary/<int:item_id>/delete` - Delete vocabulary item

**Request Format (POST/PUT)**:
```json
{
  "word": "水",
  "reading": "みず",
  "meaning": "water",
  "jlpt_level": 5,
  "example_sentence_japanese": "水を飲みます。",
  "example_sentence_english": "I drink water.",
  "audio_url": "Optional audio URL"
}
```

#### Grammar Management
- `GET /api/admin/grammar` - List all grammar points
- `POST /api/admin/grammar/new` - Create new grammar point
- `GET /api/admin/grammar/<int:item_id>` - Get specific grammar point
- `PUT /api/admin/grammar/<int:item_id>/edit` - Update grammar point
- `PATCH /api/admin/grammar/<int:item_id>/edit` - Partial update grammar point
- `DELETE /api/admin/grammar/<int:item_id>/delete` - Delete grammar point

**Request Format (POST/PUT)**:
```json
{
  "title": "です/である",
  "explanation": "Polite copula explanation",
  "structure": "Noun + です",
  "jlpt_level": 5,
  "example_sentences": "これは本です。"
}
```

### 4.3. Admin - Lesson Category Management

- `GET /api/admin/categories` - List all lesson categories
- `POST /api/admin/categories/new` - Create new category
- `GET /api/admin/categories/<int:item_id>` - Get specific category
- `PUT /api/admin/categories/<int:item_id>/edit` - Update category
- `PATCH /api/admin/categories/<int:item_id>/edit` - Partial update category
- `DELETE /api/admin/categories/<int:item_id>/delete` - Delete category

**Request Format (POST/PUT)**:
```json
{
  "name": "Beginner Grammar",
  "description": "Basic grammar concepts for beginners",
  "color_code": "#007bff"
}
```

### 4.4. Admin - Lesson Management

#### Lesson CRUD Operations
- `GET /api/admin/lessons` - List all lessons with metadata
- `POST /api/admin/lessons/new` - Create new lesson
- `GET /api/admin/lessons/<int:item_id>` - Get lesson with full content structure
- `PUT /api/admin/lessons/<int:item_id>/edit` - Update lesson metadata
- `PATCH /api/admin/lessons/<int:item_id>/edit` - Partial update lesson metadata
- `DELETE /api/admin/lessons/<int:item_id>/delete` - Delete lesson

**Lesson Response Format**:
```json
{
  "id": 1,
  "title": "Introduction to Hiragana",
  "description": "Learn basic hiragana characters",
  "lesson_type": "free",
  "category_name": "Kana",
  "difficulty_level": 1,
  "estimated_duration": 30,
  "order_index": 0,
  "is_published": true,
  "content_count": 15,
  "pages": [
    {
      "page_number": 1,
      "content": [...],
      "metadata": {
        "title": "Page 1",
        "description": "Introduction"
      }
    }
  ],
  "prerequisites": [...],
  "content_items": [...]
}
```

#### Lesson Ordering
- `POST /api/admin/lessons/<int:lesson_id>/move` - Move lesson up/down in global order
- `POST /api/admin/lessons/reorder` - Bulk reorder lessons

**Move Request Format**:
```json
{
  "direction": "up|down"
}
```

**Reorder Request Format**:
```json
{
  "lesson_ids": [1, 3, 2, 4],
  "category_id": 1  // Optional: reorder within category
}
```

### 4.5. Admin - Lesson Content Management

#### Content CRUD Operations
- `GET /api/admin/lessons/<int:lesson_id>/content` - List lesson content
- `POST /api/admin/lessons/<int:lesson_id>/content/new` - Add content to lesson
- `GET /api/admin/content/<int:content_id>` - Get content details for editing
- `PUT /api/admin/content/<int:content_id>/edit` - Update content item
- `DELETE /api/admin/lessons/<int:lesson_id>/content/<int:content_id>/delete` - Remove content

**Content Creation Request**:
```json
{
  "content_type": "text|kana|kanji|vocabulary|grammar|image|video|audio|interactive",
  "title": "Content title",
  "content_text": "Text content or description",
  "content_id": 123,  // For kana/kanji/vocab/grammar references
  "media_url": "URL for media content",
  "page_number": 1,
  "is_optional": false,
  "order_index": 0
}
```

#### Content Ordering and Management
- `POST /api/admin/lessons/<int:lesson_id>/content/<int:content_id>/move` - Move content up/down
- `POST /api/admin/lessons/<int:lesson_id>/pages/<int:page_number>/reorder` - Reorder page content
- `POST /api/admin/lessons/<int:lesson_id>/content/force-reorder` - Fix content ordering gaps

#### Bulk Content Operations
- `PUT /api/admin/lessons/<int:lesson_id>/content/bulk-update` - Bulk update content properties
- `POST /api/admin/lessons/<int:lesson_id>/content/bulk-duplicate` - Bulk duplicate content
- `DELETE /api/admin/lessons/<int:lesson_id>/content/bulk-delete` - Bulk delete content
- `POST /api/admin/content/<int:content_id>/duplicate` - Duplicate single content item

#### Page Management
- `PUT /api/admin/lessons/<int:lesson_id>/pages/<int:page_num>` - Update page metadata
- `DELETE /api/admin/lessons/<int:lesson_id>/pages/<int:page_num>/delete` - Delete page and content

#### Content Preview and Utilities
- `GET /api/admin/content/<int:content_id>/preview` - Get content preview data
- `GET /api/admin/content-options/<content_type>` - Get available content for selection

### 4.6. Admin - Interactive Content (Quizzes)

- `POST /api/admin/lessons/<int:lesson_id>/content/interactive` - Add interactive content
- `POST /api/admin/lessons/<int:lesson_id>/content/file` - Add file-based content

**Interactive Content Request**:
```json
{
  "interactive_type": "multiple_choice|fill_blank|true_false|matching",
  "title": "Quiz question title",
  "question_text": "What is the reading of あ?",
  "explanation": "Explanation of the answer",
  "max_attempts": 3,
  "passing_score": 70,
  "page_number": 1,
  "options": [
    {
      "text": "a",
      "is_correct": true,
      "feedback": "Correct!"
    }
  ]
}
```

### 4.7. Admin - File Upload System

- `POST /api/admin/upload-file` - Upload and process files
- `DELETE /api/admin/delete-file` - Delete uploaded files
- `GET /uploads/<path:filename>` - Serve uploaded files

**File Upload Request** (multipart/form-data):
```
file: [binary file data]
lesson_id: 123 (optional)
```

**File Upload Response**:
```json
{
  "success": true,
  "filePath": "/static/uploads/lessons/images/filename.jpg",
  "dbPath": "lessons/images/filename.jpg",
  "fileName": "unique_filename.jpg",
  "originalFilename": "original.jpg",
  "fileType": "image",
  "fileSize": 1024000,
  "mimeType": "image/jpeg",
  "dimensions": "1920x1080"
}
```

### 4.8. Admin - AI Content Generation

- `POST /api/admin/generate-ai-content` - Generate AI content

**AI Generation Request**:
```json
{
  "content_type": "explanation|multiple_choice_question|true_false_question|fill_blank_question|matching_question",
  "topic": "Japanese particles",
  "difficulty": "JLPT N5",
  "keywords": "は, を, に"
}
```

**AI Generation Response**:
```json
{
  "question_text": "Which particle is used for the topic marker?",
  "options": [
    {
      "text": "は",
      "is_correct": true,
      "feedback": "Correct! は is the topic marker."
    }
  ],
  "overall_explanation": "The particle は marks the topic of the sentence."
}
```

### 4.9. Admin - Lesson Export/Import System

#### Export Operations
- `GET /api/admin/lessons/<int:lesson_id>/export` - Export lesson to JSON
- `POST /api/admin/lessons/<int:lesson_id>/export-package` - Create ZIP export package
- `POST /api/admin/lessons/export-multiple` - Export multiple lessons as ZIP

**Export Package Request**:
```json
{
  "include_files": true
}
```

#### Import Operations
- `POST /api/admin/lessons/import` - Import lesson from JSON file
- `POST /api/admin/lessons/import-package` - Import lesson from ZIP package
- `POST /api/admin/lessons/import-info` - Get import file information without importing

**Import Request** (multipart/form-data):
```
file: [JSON or ZIP file]
handle_duplicates: "rename|replace|skip"
```

**Import Response**:
```json
{
  "success": true,
  "message": "Lesson imported successfully",
  "lesson_id": 123,
  "lesson_title": "Imported Lesson"
}
```

### 4.10. Admin Interface Routes

- `GET /admin` - Admin dashboard
- `GET /admin/manage/kana` - Kana management interface
- `GET /admin/manage/kanji` - Kanji management interface
- `GET /admin/manage/vocabulary` - Vocabulary management interface
- `GET /admin/manage/grammar` - Grammar management interface
- `GET /admin/manage/lessons` - Lesson management interface
- `GET /admin/manage/categories` - Category management interface

### 4.11. User - Lesson Access & Progress

#### Lesson Browsing
- `GET /lessons` - Browse available lessons (requires login)
- `GET /lessons/<int:lesson_id>` - View specific lesson (requires login)
- `GET /api/lessons` - Get lessons accessible to current user

**User Lessons Response**:
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
      "time_spent": 45
    }
  }
]
```

#### Progress Tracking
- `POST /api/lessons/<int:lesson_id>/progress` - Update lesson progress
- `POST /lessons/<int:lesson_id>/reset` - Reset lesson progress (requires CSRF)

**Progress Update Request**:
```json
{
  "content_id": 123,
  "time_spent": 5
}
```

#### Quiz Interaction
- `POST /api/lessons/<int:lesson_id>/quiz/<int:question_id>/answer` - Submit quiz answer

**Quiz Answer Request**:
```json
{
  "selected_option_id": 456,
  "text_answer": "User's text answer",
  "pairs": [
    {"prompt": "Word", "answer": "Meaning"}
  ]
}
```

**Quiz Answer Response**:
```json
{
  "is_correct": true,
  "explanation": "Detailed explanation",
  "option_feedback": "Specific feedback for selected option",
  "attempts_remaining": 2
}
```

## 5. Common Request/Response Structures

### Standard Success Response
```json
{
  "message": "Operation completed successfully",
  "data": { /* relevant data */ }
}
```

### Standard Error Response
```json
{
  "error": "Brief error description",
  "message": "Detailed error explanation",
  "status_code": 400
}
```

### Pagination Response (Future Enhancement)
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "pages": 5
  }
}
```

## 6. File Upload Configuration

### Supported File Types
- **Images**: png, jpg, jpeg, gif, webp
- **Videos**: mp4, webm, ogg, avi, mov  
- **Audio**: mp3, wav, ogg, aac, m4a

### Upload Limits
- Maximum file size: 100MB
- Files stored in: `app/static/uploads/lessons/{type}/`
- Automatic file validation using python-magic
- Image processing and optimization with Pillow

### File Security
- Filename sanitization with werkzeug.secure_filename
- MIME type validation
- File content validation
- Unique filename generation to prevent conflicts

## 7. Authentication & Authorization

### User Roles
- **Regular User**: Access to lessons based on subscription level
- **Admin User**: Full access to all admin endpoints and content management

### Access Control Decorators
- `@login_required`: Requires authenticated user
- `@admin_required`: Requires admin role
- `@premium_required`: Requires premium subscription (for future premium content)

### CSRF Protection
All state-changing operations (POST, PUT, PATCH, DELETE) require CSRF tokens:
```javascript
// Frontend CSRF token handling
fetch('/api/admin/lessons/new', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': csrf_token
  },
  body: JSON.stringify(data)
});
```

## 8. Error Handling

### HTTP Status Code Usage
- **200 OK**: Successful GET, PUT operations
- **201 Created**: Successful POST operations
- **400 Bad Request**: Validation errors, missing required fields
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **409 Conflict**: Duplicate resources (e.g., duplicate lesson titles)
- **415 Unsupported Media Type**: Invalid file types
- **500 Internal Server Error**: Server-side errors

### Error Response Examples

**Validation Error**:
```json
{
  "error": "Missing required fields: title, lesson_type",
  "status_code": 400
}
```

**Authentication Error**:
```json
{
  "error": "Admin access required.",
  "status_code": 403
}
```

**Database Error**:
```json
{
  "error": "Database integrity error. This item might already exist or violate other constraints.",
  "status_code": 409
}
```

## 9. Performance Considerations

### Database Optimization
- Proper indexing on frequently queried fields
- Efficient relationship loading with SQLAlchemy
- Pagination for large datasets (future enhancement)

### File Handling
- Image optimization and resizing
- Efficient file serving through Flask
- File cleanup on content deletion

### Caching Strategy (Future Enhancement)
- Response caching for frequently accessed content
- Static file caching
- Database query result caching

## 10. Security Implementation

### Input Validation
- All user inputs validated and sanitized
- SQL injection prevention through SQLAlchemy ORM
- XSS prevention through template escaping

### File Upload Security
- File type validation using python-magic
- Filename sanitization
- File size limits
- Secure file storage outside web root

### API Security
- Session-based authentication
- CSRF protection for all state-changing operations
- Role-based access control
- Secure error messages (no sensitive information exposure)

## 11. Future API Enhancements

### Planned Features
- **API Versioning**: `/api/v1/` prefix for version management
- **Rate Limiting**: Prevent API abuse
- **Webhook Support**: Event notifications for integrations
- **OAuth2 Integration**: Third-party authentication
- **GraphQL Endpoint**: Flexible data querying
- **Real-time Updates**: WebSocket support for live progress updates

### Monitoring and Analytics
- API usage tracking
- Performance monitoring
- Error rate monitoring
- User behavior analytics

## 12. Development Guidelines

### API Design Standards
- Use RESTful conventions consistently
- Provide comprehensive error messages
- Include proper HTTP status codes
- Document all endpoints thoroughly
- Implement proper input validation
- Follow consistent naming conventions

### Testing Requirements
- Unit tests for all API endpoints
- Integration tests for complex workflows
- Authentication and authorization testing
- File upload testing
- Error handling testing

### Documentation Maintenance
- Keep API documentation synchronized with code
- Provide request/response examples
- Document authentication requirements
- Include error scenarios and responses
- Update documentation with each API change

---

This comprehensive API documentation covers all current endpoints and provides a foundation for future development. Regular updates should be made as new features are added or existing functionality is modified.
