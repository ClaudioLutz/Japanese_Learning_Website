# Phase 3: Rich Text Content

## Overview
Add rich text editing capabilities for information slides and text content. This phase focuses on implementing a user-friendly WYSIWYG editor that allows admins to create engaging text-based content with formatting, links, and embedded media.

## Duration
1 day

## Goals
- Implement rich text editor for text content
- Support formatting (bold, italic, lists, headings, etc.)
- Add link insertion capabilities
- Enable embedded media within text content
- Create information slide templates
- Ensure content displays properly in lesson view

## Prerequisites
- Phase 1 and Phase 2 must be completed and tested
- File upload system must be working
- Content builder foundation must be operational

## Technical Implementation

### 1. Rich Text Editor Selection
**Chosen Editor**: TinyMCE (lightweight, feature-rich, easy integration)

**Alternative Options Considered:**
- CKEditor (more complex setup)
- Quill (modern but limited features)
- Summernote (Bootstrap-based but less maintained)

### 2. TinyMCE Integration
**File**: `app/templates/admin/base_admin.html`

**CDN Integration:**
```html
<!-- TinyMCE CDN -->
<script src="https://cdn.tiny.cloud/1/no-api-key/tinymce/6/tinymce.min.js" referrerpolicy="origin"></script>
```

**Configuration:**
```javascript
// TinyMCE Configuration
const tinymceConfig = {
    selector: '.rich-text-editor',
    height: 400,
    menubar: false,
    plugins: [
        'advlist', 'autolink', 'lists', 'link', 'image', 'charmap', 'preview',
        'anchor', 'searchreplace', 'visualblocks', 'code', 'fullscreen',
        'insertdatetime', 'media', 'table', 'help', 'wordcount'
    ],
    toolbar: 'undo redo | blocks | ' +
        'bold italic forecolor | alignleft aligncenter ' +
        'alignright alignjustify | bullist numlist outdent indent | ' +
        'removeformat | help',
    content_style: 'body { font-family: -apple-system, BlinkMacSystemFont, San Francisco, Segoe UI, Roboto, Helvetica Neue, sans-serif; font-size: 14px; }',
    branding: false,
    promotion: false
};
```

### 3. Enhanced Content Forms
**File**: `app/templates/admin/manage_lessons.html`

**Rich Text Content Form:**
```html
<!-- Rich Text Content Section -->
<div id="richTextSection" style="display: none;">
    <div class="form-group">
        <label for="textContentTitle">Title *</label>
        <input type="text" id="textContentTitle" name="title" class="form-control" required>
    </div>
    
    <div class="form-group">
        <label for="textContentType">Content Type</label>
        <select id="textContentType" name="text_content_type" class="form-control">
            <option value="information_slide">Information Slide</option>
            <option value="text_block">Text Block</option>
            <option value="instructions">Instructions</option>
            <option value="explanation">Explanation</option>
        </select>
    </div>
    
    <div class="form-group">
        <label for="richTextContent">Content *</label>
        <textarea id="richTextContent" name="content_text" class="form-control rich-text-editor"></textarea>
    </div>
    
    <!-- Content Template Selector -->
    <div class="form-group">
        <label>Quick Templates:</label>
        <div class="btn-group" role="group">
            <button type="button" class="btn btn-outline-secondary btn-sm" onclick="applyTemplate('basic_slide')">Basic Slide</button>
            <button type="button" class="btn btn-outline-secondary btn-sm" onclick="applyTemplate('instruction_slide')">Instructions</button>
            <button type="button" class="btn btn-outline-secondary btn-sm" onclick="applyTemplate('explanation_slide')">Explanation</button>
        </div>
    </div>
    
    <!-- Content Preview -->
    <div class="form-group">
        <label>Preview:</label>
        <div id="richTextPreview" class="border p-3 bg-light" style="min-height: 100px;">
            <em class="text-muted">Content preview will appear here...</em>
        </div>
    </div>
</div>
```

### 4. Content Templates
**File**: `app/templates/admin/manage_lessons.html` (JavaScript section)

**Template System:**
```javascript
const contentTemplates = {
    basic_slide: `
        <h2>Slide Title</h2>
        <p>Your content goes here. You can use <strong>bold text</strong>, <em>italic text</em>, and other formatting.</p>
        <ul>
            <li>Bullet point 1</li>
            <li>Bullet point 2</li>
        </ul>
    `,
    
    instruction_slide: `
        <h2>📋 Instructions</h2>
        <p>Follow these steps:</p>
        <ol>
            <li><strong>Step 1:</strong> Description of first step</li>
            <li><strong>Step 2:</strong> Description of second step</li>
            <li><strong>Step 3:</strong> Description of third step</li>
        </ol>
        <div style="background-color: #e7f3ff; padding: 10px; border-left: 4px solid #2196F3; margin: 10px 0;">
            <strong>💡 Tip:</strong> Add helpful tips here
        </div>
    `,
    
    explanation_slide: `
        <h2>📚 Explanation</h2>
        <p>This section explains an important concept:</p>
        
        <h3>Key Points:</h3>
        <ul>
            <li><strong>Point 1:</strong> Explanation</li>
            <li><strong>Point 2:</strong> Explanation</li>
        </ul>
        
        <h3>Example:</h3>
        <div style="background-color: #f0f8f0; padding: 15px; border-radius: 5px; margin: 10px 0;">
            <p>Example content goes here...</p>
        </div>
        
        <h3>Remember:</h3>
        <div style="background-color: #fff3cd; padding: 10px; border-left: 4px solid #ffc107; margin: 10px 0;">
            <strong>⚠️ Important:</strong> Key takeaway message
        </div>
    `
};

function applyTemplate(templateName) {
    if (contentTemplates[templateName]) {
        tinymce.get('richTextContent').setContent(contentTemplates[templateName]);
        updateRichTextPreview();
    }
}
```

### 5. Enhanced JavaScript Functionality
**File**: `app/templates/admin/manage_lessons.html` (JavaScript section)

**New Functions:**
```javascript
// Rich text editor management
function initializeRichTextEditor()
function destroyRichTextEditor()
function updateRichTextPreview()
function handleRichTextContent()

// Template management
function applyTemplate(templateName)
function saveCustomTemplate()
function loadCustomTemplates()

// Content validation
function validateRichTextContent()
function sanitizeHtmlContent(html)
```

### 6. Content Display Enhancement
**File**: `app/templates/lesson_view.html`

**Enhanced Text Content Display:**
```html
<!-- Enhanced Text Content Display -->
{% if content.content_type == 'text' %}
<div class="text-content-container">
    {% if content.title %}
    <div class="content-header mb-3">
        <h4 class="content-title">{{ content.title }}</h4>
        {% if content.content_text and 'information_slide' in content.content_text %}
        <span class="badge bg-info">Information Slide</span>
        {% endif %}
    </div>
    {% endif %}
    
    <div class="rich-text-content">
        {{ content.content_text | safe }}
    </div>
</div>
{% endif %}
```

### 7. CSS Styling for Rich Content
**File**: `app/templates/admin/base_admin.html` (CSS section)

**Rich Text Styling:**
```css
<style>
/* Rich Text Editor Styling */
.rich-text-editor {
    min-height: 300px;
}

.rich-text-preview {
    max-height: 400px;
    overflow-y: auto;
}

/* Content Template Buttons */
.template-buttons .btn {
    margin: 2px;
}

/* Rich Text Content Display */
.rich-text-content {
    line-height: 1.6;
    font-size: 16px;
}

.rich-text-content h1,
.rich-text-content h2,
.rich-text-content h3 {
    color: #2c3e50;
    margin-top: 1.5em;
    margin-bottom: 0.5em;
}

.rich-text-content h1 { font-size: 1.8em; }
.rich-text-content h2 { font-size: 1.5em; }
.rich-text-content h3 { font-size: 1.3em; }

.rich-text-content ul,
.rich-text-content ol {
    margin: 1em 0;
    padding-left: 2em;
}

.rich-text-content blockquote {
    border-left: 4px solid #3498db;
    padding-left: 1em;
    margin: 1em 0;
    font-style: italic;
    background-color: #f8f9fa;
    padding: 1em;
}

.rich-text-content code {
    background-color: #f1f2f6;
    padding: 2px 4px;
    border-radius: 3px;
    font-family: 'Courier New', monospace;
}

.rich-text-content pre {
    background-color: #f1f2f6;
    padding: 1em;
    border-radius: 5px;
    overflow-x: auto;
}

/* Information Slide Specific Styling */
.content-type-information_slide {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 2em;
    border-radius: 10px;
    margin: 1em 0;
}

.content-type-information_slide h1,
.content-type-information_slide h2,
.content-type-information_slide h3 {
    color: white;
}
</style>
```

## User Interface Design

### Rich Text Editor Interface
```
┌─────────────────────────────────────────────────────────────┐
│                    Create Text Content                      │
├─────────────────────────────────────────────────────────────┤
│ Title: [_________________________]                          │
│                                                             │
│ Type: [Information Slide ▼]                                │
│                                                             │
│ Templates: [Basic] [Instructions] [Explanation]            │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ [B] [I] [U] | [≡] [≡] [≡] [≡] | [•] [1.] | [🔗] [📷]    │ │
│ ├─────────────────────────────────────────────────────────┤ │
│ │                                                         │ │
│ │ # Your Title Here                                       │ │
│ │                                                         │ │
│ │ Your content goes here. You can format text with       │ │
│ │ **bold**, *italic*, and other formatting options.      │ │
│ │                                                         │ │
│ │ • Bullet point 1                                       │ │
│ │ • Bullet point 2                                       │ │
│ │                                                         │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Preview:                                                    │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ [Formatted content preview appears here]                │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Steps

### Step 1: TinyMCE Integration
1. Add TinyMCE CDN to base admin template
2. Configure TinyMCE with appropriate plugins and toolbar
3. Test basic rich text editing functionality

### Step 2: Content Form Enhancement
1. Update content addition modal with rich text section
2. Add content type selection for text content
3. Implement template system with predefined templates

### Step 3: Preview Functionality
1. Add real-time preview of rich text content
2. Implement content validation and sanitization
3. Test preview accuracy

### Step 4: Template System
1. Create predefined content templates
2. Add template application functionality
3. Implement custom template saving (future enhancement)

### Step 5: Display Integration
1. Update lesson view template for rich text display
2. Add CSS styling for rich content
3. Test content display in student view

## Content Security

### HTML Sanitization
- **Allowed Tags**: Whitelist safe HTML tags
- **Attribute Filtering**: Remove potentially dangerous attributes
- **Script Prevention**: Block all script tags and event handlers
- **Link Validation**: Validate external links

### Content Validation
- **Length Limits**: Enforce reasonable content length limits
- **Image Validation**: Validate embedded images
- **Link Checking**: Verify external links are safe

## Testing Checklist

### Rich Text Editor Testing
- [ ] TinyMCE loads correctly
- [ ] All toolbar functions work properly
- [ ] Content can be formatted (bold, italic, lists, etc.)
- [ ] Links can be inserted and edited
- [ ] Images can be embedded
- [ ] Content saves correctly

### Template System Testing
- [ ] Predefined templates load correctly
- [ ] Template application works
- [ ] Templates display properly in preview
- [ ] Custom content can be created

### Content Display Testing
- [ ] Rich text displays correctly in lesson view
- [ ] Formatting is preserved
- [ ] Links work properly
- [ ] Images display correctly
- [ ] Content is responsive on different screen sizes

### Security Testing
- [ ] HTML content is properly sanitized
- [ ] Script tags are blocked
- [ ] Malicious content is filtered
- [ ] External links are validated

## Success Criteria
- ✅ Admin can create rich text content with formatting
- ✅ Content templates provide quick starting points
- ✅ Rich text displays correctly in lessons
- ✅ Content is secure and sanitized
- ✅ Editor is intuitive and user-friendly
- ✅ Preview functionality works accurately

## Files to Modify
1. `app/templates/admin/base_admin.html` - TinyMCE integration
2. `app/templates/admin/manage_lessons.html` - Rich text forms
3. `app/templates/lesson_view.html` - Content display
4. `app/routes.py` - Content validation (if needed)

## Files to Create
None (all changes are enhancements to existing files)

## Next Phase Preparation
Phase 3 prepares for Phase 4 by:
- Establishing rich content creation capabilities
- Creating the foundation for interactive content
- Setting up content templating system

Phase 4 will build upon this by adding interactive content types like multiple choice questions and fill-in-the-blank exercises.
