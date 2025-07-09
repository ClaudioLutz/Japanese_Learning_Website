# Phase 1: Enhanced Content Builder Foundation

## Overview
Create a comprehensive content addition interface that allows admins to easily add various types of sub-lessons (content items) to a lesson. This phase focuses on building the foundation for content creation without file uploads.

## Duration
1-2 days

## Goals
- Replace the basic "Add Content" functionality with a comprehensive content builder
- Support all existing content types (Kana, Kanji, Vocabulary, Grammar)
- Add support for basic text content and URL-based media
- Create intuitive content type selection interface
- Implement content editing and management

## Current State Analysis
**Existing Functionality:**
- Basic lesson content management via API
- Simple content removal functionality
- Content display in lesson view

**Missing Functionality:**
- User-friendly content addition interface
- Content type selection wizard
- Content editing capabilities
- Content preview functionality

## Technical Implementation

### 1. Enhanced Content Addition Modal
**File**: `app/templates/admin/manage_lessons.html`

**Changes Required:**
- Replace basic "Add Content" button with comprehensive content builder
- Create multi-step content addition wizard
- Add content type selection interface
- Implement content-specific forms

**New Modal Structure:**
```html
<!-- Add Content Wizard Modal -->
<div id="addContentModal" class="modal">
  <div class="modal-content" style="max-width: 800px;">
    <!-- Step 1: Content Type Selection -->
    <div id="contentTypeStep">
      <!-- Visual content type selector -->
    </div>
    
    <!-- Step 2: Content Configuration -->
    <div id="contentConfigStep">
      <!-- Dynamic forms based on content type -->
    </div>
    
    <!-- Step 3: Preview & Confirm -->
    <div id="contentPreviewStep">
      <!-- Content preview -->
    </div>
  </div>
</div>
```

### 2. Content Type Forms
**New Content Types to Support:**

#### A. Existing Content Reference
- **Kana Selection**: Dropdown/search for existing Kana characters
- **Kanji Selection**: Dropdown/search for existing Kanji characters  
- **Vocabulary Selection**: Dropdown/search for existing vocabulary
- **Grammar Selection**: Dropdown/search for existing grammar points

#### B. Custom Text Content
- **Information Slide**: Title + rich text content
- **Text Block**: Simple text content with formatting

#### C. URL-Based Media (Phase 1)
- **Video**: YouTube/Vimeo embed URLs
- **Audio**: Direct audio file URLs
- **Image**: Direct image URLs

### 3. Enhanced JavaScript Functionality
**File**: `app/templates/admin/manage_lessons.html` (JavaScript section)

**New Functions:**
```javascript
// Content wizard management
function openAddContentModal(lessonId)
function showContentTypeStep()
function showContentConfigStep(contentType)
function showContentPreviewStep()

// Content type handlers
function handleExistingContentSelection(contentType)
function handleCustomTextContent()
function handleUrlMediaContent(mediaType)

// Content management
function loadContentOptions(contentType)
function previewContent(contentData)
function saveContentToLesson(lessonId, contentData)
```

### 4. API Enhancements
**File**: `app/routes.py`

**New Endpoints:**
```python
# Get available content for selection
@bp.route('/api/admin/content-options/<content_type>', methods=['GET'])
def get_content_options(content_type):
    # Return available Kana, Kanji, Vocabulary, or Grammar items

# Enhanced content creation with validation
@bp.route('/api/admin/lessons/<int:lesson_id>/content/new', methods=['POST'])
def add_lesson_content_enhanced(lesson_id):
    # Enhanced content creation with proper validation
```

### 5. Database Model Updates
**File**: `app/models.py`

**Enhancements to LessonContent model:**
- Add validation for URL-based media
- Enhance content data retrieval methods
- Add content type validation

## User Interface Design

### Content Type Selection Interface
```
┌─────────────────────────────────────────────────────────────┐
│                    Add Content to Lesson                    │
├─────────────────────────────────────────────────────────────┤
│  Choose Content Type:                                       │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │    📝       │  │    🔤       │  │    📚       │         │
│  │   Kana      │  │   Kanji     │  │ Vocabulary  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │    📖       │  │    📄       │  │    🎥       │         │
│  │  Grammar    │  │    Text     │  │   Video     │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐                          │
│  │    🎵       │  │    🖼️       │                          │
│  │   Audio     │  │   Image     │                          │
│  └─────────────┘  └─────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

### Content Configuration Forms
Each content type will have its specific configuration form:

**Existing Content (Kana/Kanji/Vocabulary/Grammar):**
- Search/dropdown to select existing content
- Optional: Custom title override
- Optional: Additional notes

**Text Content:**
- Title field
- Text content area (basic textarea for Phase 1)
- Optional: Formatting options

**URL Media:**
- Title field
- URL input with validation
- Optional: Description

## Implementation Steps

### Step 1: Modal Structure Enhancement
1. Update `manage_lessons.html` template
2. Create new modal structure with wizard steps
3. Add CSS styling for content type selection

### Step 2: Content Type Selection
1. Implement visual content type selector
2. Add click handlers for each content type
3. Create step navigation functionality

### Step 3: Dynamic Form Generation
1. Create content-specific forms
2. Implement form validation
3. Add form submission handling

### Step 4: API Integration
1. Create new API endpoints for content options
2. Enhance existing content creation endpoint
3. Add proper error handling

### Step 5: Content Preview
1. Implement content preview functionality
2. Add preview templates for each content type
3. Create confirmation step

## Testing Checklist

### Functional Testing
- [ ] Content type selection works correctly
- [ ] Each content type form displays properly
- [ ] Form validation works for all content types
- [ ] Content can be successfully added to lessons
- [ ] Content appears correctly in lesson content table
- [ ] Content can be removed from lessons
- [ ] Multiple content items can be added to a single lesson

### Integration Testing
- [ ] New content displays correctly in lesson view
- [ ] Progress tracking works with new content
- [ ] Existing lesson functionality remains intact
- [ ] API endpoints respond correctly
- [ ] Database operations complete successfully

### User Experience Testing
- [ ] Interface is intuitive and easy to use
- [ ] Error messages are clear and helpful
- [ ] Modal navigation flows smoothly
- [ ] Content preview is accurate
- [ ] Loading states are handled properly

## Success Criteria
- ✅ Admin can select from multiple content types
- ✅ Each content type has appropriate configuration options
- ✅ Content can be added to lessons through intuitive interface
- ✅ Content displays correctly in lesson management
- ✅ Content appears properly in student lesson view
- ✅ All existing functionality remains working

## Files to Modify
1. `app/templates/admin/manage_lessons.html` - Main implementation
2. `app/routes.py` - API enhancements
3. `app/models.py` - Model enhancements (if needed)

## Files to Create
None (all changes are enhancements to existing files)

## Next Phase Preparation
Phase 1 prepares the foundation for Phase 2 by:
- Establishing the content wizard interface
- Creating the framework for different content types
- Setting up the infrastructure for content management

Phase 2 will build upon this by adding file upload capabilities to replace URL-based media with actual file uploads.
