# Phase 2: File Upload System

## Overview
Implement a secure local file upload system for multimedia content (images, videos, audio files) to replace URL-based media from Phase 1. This phase focuses on creating a robust file handling system with proper validation and organization.

## Duration
1-2 days

## Goals
- Implement secure file upload functionality
- Create organized file storage structure
- Add file validation and security measures
- Replace URL-based media with actual file uploads
- Implement file serving and management

## Prerequisites
- Phase 1 must be completed and tested
- Content builder foundation must be working

## Technical Implementation

### 1. File Storage Structure
**Directory Structure:**
```
app/
├── static/
│   └── uploads/
│       ├── lessons/
│       │   ├── images/
│       │   │   ├── lesson_1/
│       │   │   ├── lesson_2/
│       │   │   └── ...
│       │   ├── videos/
│       │   │   ├── lesson_1/
│       │   │   ├── lesson_2/
│       │   │   └── ...
│       │   └── audio/
│       │       ├── lesson_1/
│       │       ├── lesson_2/
│       │       └── ...
│       └── temp/
│           └── (temporary upload files)
```

### 2. Flask Configuration Updates
**File**: `app/__init__.py`

**New Configuration:**
```python
import os
from werkzeug.utils import secure_filename

# File upload configuration
UPLOAD_FOLDER = os.path.join('app', 'static', 'uploads')
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max file size
ALLOWED_EXTENSIONS = {
    'image': {'png', 'jpg', 'jpeg', 'gif', 'webp'},
    'video': {'mp4', 'webm', 'ogg', 'avi', 'mov'},
    'audio': {'mp3', 'wav', 'ogg', 'aac', 'm4a'}
}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
```

### 3. File Upload Utilities
**File**: `app/utils.py` (new file)

```python
import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app
from PIL import Image
import magic

class FileUploadHandler:
    @staticmethod
    def allowed_file(filename, file_type):
        """Check if file extension is allowed for the given type"""
        
    @staticmethod
    def get_file_type(filename):
        """Determine file type based on extension"""
        
    @staticmethod
    def generate_unique_filename(filename):
        """Generate unique filename while preserving extension"""
        
    @staticmethod
    def create_lesson_directory(lesson_id, file_type):
        """Create directory structure for lesson files"""
        
    @staticmethod
    def validate_file_content(file_path, expected_type):
        """Validate file content matches expected type"""
        
    @staticmethod
    def process_image(file_path, max_width=1920, max_height=1080):
        """Resize and optimize images"""
        
    @staticmethod
    def get_file_info(file_path):
        """Get file metadata (size, dimensions, duration, etc.)"""
```

### 4. Enhanced Content Addition Modal
**File**: `app/templates/admin/manage_lessons.html`

**File Upload Interface:**
```html
<!-- File Upload Section for Media Content -->
<div id="fileUploadSection" style="display: none;">
    <div class="form-group">
        <label for="contentFile">Upload File *</label>
        <div class="file-upload-area" id="fileUploadArea">
            <input type="file" id="contentFile" name="file" accept="" style="display: none;">
            <div class="upload-placeholder">
                <i class="fas fa-cloud-upload-alt fa-3x text-muted"></i>
                <p>Click to select file or drag and drop</p>
                <small class="text-muted">Supported formats: <span id="supportedFormats"></span></small>
            </div>
        </div>
        <div class="upload-progress" style="display: none;">
            <div class="progress">
                <div class="progress-bar" role="progressbar" style="width: 0%"></div>
            </div>
            <small class="text-muted">Uploading... <span id="uploadPercent">0%</span></small>
        </div>
    </div>
    
    <div class="form-group">
        <label for="fileTitle">Title *</label>
        <input type="text" id="fileTitle" name="title" class="form-control" required>
    </div>
    
    <div class="form-group">
        <label for="fileDescription">Description</label>
        <textarea id="fileDescription" name="description" class="form-control" rows="3"></textarea>
    </div>
    
    <!-- File Preview -->
    <div id="filePreview" style="display: none;">
        <h6>Preview:</h6>
        <div id="previewContainer"></div>
    </div>
</div>
```

### 5. File Upload API Endpoints
**File**: `app/routes.py`

**New Endpoints:**
```python
@bp.route('/api/admin/upload-file', methods=['POST'])
@login_required
@admin_required
def upload_file():
    """Handle file upload and return file information"""
    
@bp.route('/api/admin/lessons/<int:lesson_id>/content/file', methods=['POST'])
@login_required
@admin_required
def add_file_content(lesson_id):
    """Add file-based content to lesson"""
    
@bp.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    
@bp.route('/api/admin/delete-file', methods=['DELETE'])
@login_required
@admin_required
def delete_file():
    """Delete uploaded file"""
```

### 6. Database Model Updates
**File**: `app/models.py`

**Enhancements to LessonContent model:**
```python
class LessonContent(db.Model):
    # ... existing fields ...
    
    # File-related fields
    file_path = db.Column(db.String(500))  # Relative path to uploaded file
    file_size = db.Column(db.Integer)      # File size in bytes
    file_type = db.Column(db.String(50))   # MIME type
    original_filename = db.Column(db.String(255))  # Original filename
    
    def get_file_url(self):
        """Get URL for accessing uploaded file"""
        if self.file_path:
            return url_for('routes.uploaded_file', filename=self.file_path)
        return self.media_url  # Fallback to URL-based media
    
    def delete_file(self):
        """Delete associated file from filesystem"""
        if self.file_path:
            file_full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], self.file_path)
            if os.path.exists(file_full_path):
                os.remove(file_full_path)
```

### 7. Enhanced JavaScript Functionality
**File**: `app/templates/admin/manage_lessons.html` (JavaScript section)

**New Functions:**
```javascript
// File upload handling
function initializeFileUpload(contentType)
function handleFileSelect(event)
function handleFileDrop(event)
function uploadFile(file, lessonId, contentType)
function updateUploadProgress(percent)
function previewFile(file, fileType)
function validateFile(file, expectedType)

// File management
function deleteUploadedFile(filePath)
function showFilePreview(fileUrl, fileType)
```

## User Interface Enhancements

### File Upload Interface Design
```
┌─────────────────────────────────────────────────────────────┐
│                    Upload Media File                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                    📁                                   │ │
│  │           Click to select file                          │ │
│  │              or drag and drop                           │ │
│  │                                                         │ │
│  │     Supported: JPG, PNG, MP4, MP3 (Max: 100MB)        │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                             │
│  Title: [________________________]                         │
│                                                             │
│  Description: [____________________]                        │
│               [____________________]                        │
│               [____________________]                        │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Preview:                                                │ │
│  │ [File preview will appear here]                         │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Upload Progress Indicator
```
┌─────────────────────────────────────────────────────────────┐
│ Uploading file...                                           │
│ ████████████████████████████████████████████████████ 85%    │
│ Processing: example_video.mp4 (15.2 MB)                    │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Steps

### Step 1: File Storage Setup
1. Create upload directory structure
2. Set up Flask configuration for file uploads
3. Create file utility functions
4. Implement file validation

### Step 2: Upload Interface
1. Update content addition modal with file upload interface
2. Add drag-and-drop functionality
3. Implement file preview
4. Add upload progress indicators

### Step 3: Backend File Handling
1. Create file upload API endpoints
2. Implement file processing and validation
3. Add file serving endpoint
4. Update database models

### Step 4: Integration with Content Builder
1. Integrate file upload with Phase 1 content builder
2. Update content type handlers
3. Modify content preview functionality
4. Update lesson content display

### Step 5: File Management
1. Implement file deletion functionality
2. Add file replacement capability
3. Create file cleanup utilities
4. Add file metadata tracking

## Security Considerations

### File Validation
- **File Type Validation**: Check file extensions and MIME types
- **Content Validation**: Use python-magic to verify file contents
- **Size Limits**: Enforce maximum file size limits
- **Filename Security**: Use secure_filename() to prevent path traversal

### Storage Security
- **Directory Permissions**: Proper file system permissions
- **File Serving**: Serve files through Flask route with access control
- **Temporary Files**: Clean up temporary files after processing
- **Virus Scanning**: Consider adding virus scanning for uploaded files

### Access Control
- **Admin Only**: Only admin users can upload files
- **Lesson Association**: Files must be associated with specific lessons
- **File Ownership**: Track which admin uploaded each file

## Testing Checklist

### File Upload Testing
- [ ] Files upload successfully for all supported types
- [ ] File size limits are enforced
- [ ] Invalid file types are rejected
- [ ] File content validation works
- [ ] Upload progress is displayed correctly
- [ ] Files are stored in correct directory structure

### File Serving Testing
- [ ] Uploaded files are accessible via URL
- [ ] File serving respects access permissions
- [ ] Different file types display/play correctly
- [ ] File metadata is preserved

### Integration Testing
- [ ] File upload integrates with content builder
- [ ] Uploaded content displays in lesson view
- [ ] File deletion works correctly
- [ ] Database records are updated properly
- [ ] Existing URL-based media still works

### Security Testing
- [ ] Malicious files are rejected
- [ ] Path traversal attacks are prevented
- [ ] File size limits prevent DoS attacks
- [ ] Only authorized users can upload files
- [ ] File permissions are set correctly

## Success Criteria
- ✅ Admin can upload images, videos, and audio files
- ✅ Files are stored securely with proper organization
- ✅ File validation prevents security issues
- ✅ Upload progress is clearly indicated
- ✅ Uploaded files display correctly in lessons
- ✅ File management (delete, replace) works properly
- ✅ System handles large files efficiently

## Files to Modify
1. `app/__init__.py` - Flask configuration
2. `app/templates/admin/manage_lessons.html` - Upload interface
3. `app/routes.py` - Upload endpoints
4. `app/models.py` - Database model updates

## Files to Create
1. `app/utils.py` - File handling utilities
2. `app/static/uploads/` - Upload directory structure

## Next Phase Preparation
Phase 2 prepares for Phase 3 by:
- Establishing secure file handling infrastructure
- Creating the foundation for rich media content
- Setting up file management capabilities

Phase 3 will build upon this by adding rich text editing capabilities for information slides and text content.
