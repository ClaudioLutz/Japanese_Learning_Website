# File Upload System

## Overview

The Japanese Learning Website includes a comprehensive file upload system that allows administrators to upload and manage multimedia content for lessons. The system supports images, videos, and audio files with robust security measures, automatic processing, and integration with the lesson content management system.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Supported File Types](#supported-file-types)
3. [Security Features](#security-features)
4. [File Processing](#file-processing)
5. [API Endpoints](#api-endpoints)
6. [Database Integration](#database-integration)
7. [Frontend Integration](#frontend-integration)
8. [Configuration](#configuration)
9. [Error Handling](#error-handling)
10. [Performance Considerations](#performance-considerations)
11. [Troubleshooting](#troubleshooting)

## Architecture Overview

The file upload system follows a multi-layered architecture with clear separation of concerns:

```
Frontend Upload Interface
    ↓ Multipart Form Data
API Endpoint (/api/admin/upload-file)
    ↓ File Validation
FileUploadHandler (app/utils.py)
    ↓ Processing & Storage
File System Storage
    ↓ Database Record
LessonContent Model
```

### Key Components

1. **FileUploadHandler Class**: Core utility class handling all file operations
2. **Upload API Endpoint**: RESTful endpoint for file uploads
3. **File Validation**: Multi-layer security validation
4. **Storage Management**: Organized file system storage
5. **Database Integration**: Metadata storage and tracking

## Supported File Types

### Image Files
- **Extensions**: png, jpg, jpeg, gif, webp
- **Processing**: Automatic resizing and optimization
- **Max Dimensions**: 1920x1080 pixels (configurable)
- **Quality**: JPEG compression at 85% quality

### Video Files
- **Extensions**: mp4, webm, ogg, avi, mov
- **Processing**: Basic validation and metadata extraction
- **Streaming**: Optimized for web playback

### Audio Files
- **Extensions**: mp3, wav, ogg, aac, m4a
- **Processing**: Format validation and metadata extraction
- **Playback**: HTML5 audio element compatible

## Security Features

### File Validation

#### 1. Extension-Based Validation
```python
def allowed_file(filename, file_type):
    """Check if file extension is allowed for the given type"""
    if '.' not in filename:
        return False
    
    extension = filename.rsplit('.', 1)[1].lower()
    allowed_extensions = current_app.config['ALLOWED_EXTENSIONS']
    
    if file_type in allowed_extensions:
        return extension in allowed_extensions[file_type]
    
    return False
```

#### 2. MIME Type Validation
Uses `python-magic` library for content-based validation:
```python
def validate_file_content(file_path, expected_type):
    """Validate file content matches expected type using python-magic"""
    import magic
    try:
        mime_type = magic.from_file(file_path, mime=True)
        
        if expected_type == 'image':
            return mime_type.startswith('image/')
        elif expected_type == 'video':
            return mime_type.startswith('video/')
        elif expected_type == 'audio':
            return mime_type.startswith('audio/')
        
        return True
    except Exception as e:
        current_app.logger.error(f"File content validation failed: {e}")
        return False
```

#### 3. Filename Sanitization
```python
def generate_unique_filename(filename):
    """Generate unique filename while preserving extension"""
    if '.' in filename:
        name, extension = filename.rsplit('.', 1)
        secure_name = secure_filename(name)
        unique_id = str(uuid.uuid4())[:8]
        return f"{secure_name}_{unique_id}.{extension.lower()}"
    else:
        secure_name = secure_filename(filename)
        unique_id = str(uuid.uuid4())[:8]
        return f"{secure_name}_{unique_id}"
```

### Security Measures

- **File Size Limits**: Maximum 100MB per file
- **Path Traversal Prevention**: Secure filename generation
- **Content Validation**: MIME type verification
- **Temporary Processing**: Files validated before final storage
- **Access Control**: Admin-only upload permissions
- **CSRF Protection**: All upload requests require CSRF tokens

## File Processing

### Image Processing Pipeline

1. **Upload to Temporary Directory**
2. **Content Validation** (MIME type check)
3. **Image Processing**:
   - Format conversion (RGBA/LA to RGB for JPEG compatibility)
   - Automatic resizing if dimensions exceed limits
   - Quality optimization (85% JPEG quality)
   - Metadata preservation where possible
4. **Move to Final Directory**
5. **Database Record Creation**

```python
def process_image(file_path, max_width=1920, max_height=1080):
    """Resize and optimize images"""
    try:
        with Image.open(file_path) as img:
            # Handle transparency and color modes
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                
                mask = img.split()[-1] if img.mode in ('RGBA', 'LA') else None
                if mask:
                    background.paste(img, (0,0), mask)
                else:
                    background.paste(img.convert('RGB'), (0,0))
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # Resize if necessary
            if img.width > max_width or img.height > max_height:
                img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # Save optimized image
            img.save(file_path, 'JPEG', quality=85, optimize=True)
            return True
    except Exception as e:
        current_app.logger.error(f"Error processing image: {e}")
        return False
```

### File Organization

Files are organized in a hierarchical structure:
```
app/static/uploads/
├── lessons/
│   ├── images/
│   │   └── [uploaded image files]
│   ├── videos/
│   │   └── [uploaded video files]
│   └── audio/
│       └── [uploaded audio files]
└── temp/
    └── [temporary files during processing]
```

## API Endpoints

### File Upload Endpoint

**Endpoint**: `POST /api/admin/upload-file`
**Authentication**: Admin required
**Content-Type**: `multipart/form-data`

#### Request Format
```
file: [binary file data]
lesson_id: 123 (optional)
```

#### Response Format
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

#### Error Response
```json
{
  "success": false,
  "error": "File type not allowed by extension."
}
```

### File Deletion Endpoint

**Endpoint**: `DELETE /api/admin/delete-file`
**Authentication**: Admin required
**Content-Type**: `application/json`

#### Request Format
```json
{
  "file_path": "lessons/images/filename.jpg",
  "content_id": 123
}
```

#### Response Format
```json
{
  "message": "File deleted successfully from filesystem."
}
```

### File Serving Endpoint

**Endpoint**: `GET /uploads/<path:filename>`
**Authentication**: None (public access to uploaded files)

Serves uploaded files with proper security checks:
- Path traversal prevention
- File existence validation
- Proper MIME type headers

## Database Integration

### LessonContent Model Fields

The file upload system integrates with the `LessonContent` model through these fields:

```python
# File-related fields
file_path = db.Column(db.String(500))  # Relative path to uploaded file
file_size = db.Column(db.Integer)      # File size in bytes
file_type = db.Column(db.String(50))   # MIME type
original_filename = db.Column(db.String(255))  # Original filename
```

### File Metadata Storage

When a file is uploaded and associated with lesson content:

```python
content = LessonContent(
    lesson_id=lesson_id,
    content_type='image',  # or 'video', 'audio'
    title=data.get('title'),
    content_text=data.get('description'),
    file_path=file_info['file_path'],
    file_size=file_info.get('file_size'),
    file_type=file_info.get('file_type'),
    original_filename=file_info.get('original_filename'),
    order_index=next_order_index,
    is_optional=is_optional
)
```

### File URL Generation

The system provides methods to generate URLs for uploaded files:

```python
def get_file_url(self):
    """Get URL for accessing uploaded file"""
    from flask import url_for
    if self.file_path:
        return url_for('routes.uploaded_file', filename=self.file_path)
    return self.media_url  # Fallback to URL-based media
```

## Frontend Integration

### Upload Interface

The admin interface provides drag-and-drop file upload functionality:

```javascript
// File upload handling
function uploadFile(file, lessonId) {
    const formData = new FormData();
    formData.append('file', file);
    if (lessonId) {
        formData.append('lesson_id', lessonId);
    }
    
    return fetch('/api/admin/upload-file', {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrf_token
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            return data;
        } else {
            throw new Error(data.error);
        }
    });
}
```

### Progress Tracking

Upload progress can be tracked using XMLHttpRequest:

```javascript
function uploadWithProgress(file, progressCallback) {
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        const formData = new FormData();
        formData.append('file', file);
        
        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const percentComplete = (e.loaded / e.total) * 100;
                progressCallback(percentComplete);
            }
        });
        
        xhr.addEventListener('load', () => {
            if (xhr.status === 200) {
                resolve(JSON.parse(xhr.responseText));
            } else {
                reject(new Error('Upload failed'));
            }
        });
        
        xhr.open('POST', '/api/admin/upload-file');
        xhr.setRequestHeader('X-CSRFToken', csrf_token);
        xhr.send(formData);
    });
}
```

## Configuration

### Application Configuration

File upload settings are configured in `app/__init__.py`:

```python
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
app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS
```

### Directory Creation

Upload directories are automatically created on application startup:

```python
upload_dirs = [
    os.path.join(UPLOAD_FOLDER, 'lessons', 'images'),
    os.path.join(UPLOAD_FOLDER, 'lessons', 'videos'),
    os.path.join(UPLOAD_FOLDER, 'lessons', 'audio'),
    os.path.join(UPLOAD_FOLDER, 'temp')
]
for directory in upload_dirs:
    os.makedirs(directory, exist_ok=True)
```

### Environment Variables

Optional environment variables for configuration:

```env
# File upload settings
MAX_UPLOAD_SIZE=104857600  # 100MB in bytes
UPLOAD_PATH=/custom/upload/path
IMAGE_MAX_WIDTH=1920
IMAGE_MAX_HEIGHT=1080
IMAGE_QUALITY=85
```

## Error Handling

### Common Error Scenarios

#### 1. File Type Validation Errors
```json
{
  "success": false,
  "error": "File type not allowed by extension."
}
```

#### 2. File Size Errors
```json
{
  "success": false,
  "error": "File size exceeds maximum allowed size of 100MB."
}
```

#### 3. Content Validation Errors
```json
{
  "success": false,
  "error": "File content does not match extension or is not allowed."
}
```

#### 4. Processing Errors
```json
{
  "success": false,
  "error": "Image processing failed."
}
```

#### 5. Storage Errors
```json
{
  "success": false,
  "error": "An server error occurred during file upload."
}
```

### Error Logging

All file upload errors are logged with detailed information:

```python
current_app.logger.error(f"File upload failed: {e}", exc_info=True)
```

### Cleanup on Errors

The system ensures proper cleanup of temporary files:

```python
try:
    # File processing logic
    pass
except Exception as e:
    if os.path.exists(temp_filepath):
        FileUploadHandler.delete_file(temp_filepath)
    return jsonify({'success': False, 'error': 'Upload failed'}), 500
finally:
    # Double check temp file is removed
    if os.path.exists(temp_filepath):
        FileUploadHandler.delete_file(temp_filepath)
```

## Performance Considerations

### File Size Optimization

#### Image Optimization
- Automatic resizing to maximum dimensions
- JPEG compression with 85% quality
- Format conversion for web compatibility
- Thumbnail generation (future enhancement)

#### Storage Efficiency
- Unique filename generation prevents conflicts
- Organized directory structure for efficient access
- Automatic cleanup of orphaned files

### Upload Performance

#### Chunked Uploads (Future Enhancement)
For large files, implement chunked upload:

```javascript
function uploadInChunks(file, chunkSize = 1024 * 1024) {
    // Implementation for chunked upload
    const chunks = Math.ceil(file.size / chunkSize);
    // Upload logic here
}
```

#### Async Processing (Future Enhancement)
For heavy processing tasks:

```python
from celery import Celery

@celery.task
def process_video_async(file_path):
    # Background video processing
    pass
```

## Troubleshooting

### Common Issues and Solutions

#### Issue: "python-magic not found"
**Solution**: Install python-magic library
```bash
# On Ubuntu/Debian
sudo apt-get install libmagic1

# On macOS
brew install libmagic

# Python package
pip install python-magic
```

#### Issue: "PIL/Pillow errors"
**Solution**: Ensure Pillow is properly installed
```bash
pip install Pillow
```

#### Issue: "Permission denied" errors
**Solution**: Check directory permissions
```bash
chmod 755 app/static/uploads
chmod 755 app/static/uploads/lessons
```

#### Issue: "File not found" after upload
**Solution**: Verify upload directory configuration and file paths

#### Issue: "CSRF token missing"
**Solution**: Ensure CSRF token is included in upload requests
```javascript
headers: {
    'X-CSRFToken': csrf_token
}
```

### Debugging Tips

#### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### Check File Permissions
```python
import os
import stat

def check_permissions(path):
    st = os.stat(path)
    return oct(st.st_mode)[-3:]
```

#### Validate Upload Configuration
```python
def validate_upload_config():
    upload_folder = current_app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_folder):
        print(f"Upload folder does not exist: {upload_folder}")
    if not os.access(upload_folder, os.W_OK):
        print(f"Upload folder is not writable: {upload_folder}")
```

### Monitoring and Maintenance

#### Regular Maintenance Tasks

1. **Cleanup Orphaned Files**: Remove files not referenced in database
2. **Monitor Disk Usage**: Track upload directory size
3. **Validate File Integrity**: Check for corrupted files
4. **Update Security Policies**: Review allowed file types and sizes

#### Monitoring Script Example
```python
def cleanup_orphaned_files():
    """Remove files not referenced in database"""
    upload_folder = current_app.config['UPLOAD_FOLDER']
    
    # Get all file paths from database
    db_files = set()
    for content in LessonContent.query.filter(LessonContent.file_path.isnot(None)):
        if content.file_path:
            db_files.add(content.file_path)
    
    # Check filesystem files
    for root, dirs, files in os.walk(upload_folder):
        for file in files:
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, upload_folder)
            
            if relative_path not in db_files:
                print(f"Orphaned file found: {relative_path}")
                # Optionally delete: os.remove(file_path)
```

## Future Enhancements

### Planned Features

1. **Cloud Storage Integration**: Support for AWS S3, Google Cloud Storage
2. **CDN Integration**: Content delivery network for faster file serving
3. **Image Variants**: Automatic thumbnail and multiple size generation
4. **Video Processing**: Automatic transcoding and optimization
5. **Bulk Upload**: Multiple file upload with progress tracking
6. **File Versioning**: Keep multiple versions of uploaded files
7. **Metadata Extraction**: Automatic extraction of EXIF data, video duration, etc.
8. **Virus Scanning**: Integration with antivirus scanning services

### Technical Improvements

1. **Async Processing**: Background processing for large files
2. **Chunked Uploads**: Support for resumable uploads
3. **Compression**: Automatic file compression
4. **Watermarking**: Automatic watermark application for images
5. **Access Control**: Fine-grained permissions for file access
6. **Audit Trail**: Complete logging of file operations

---

This comprehensive file upload system provides a secure, efficient, and user-friendly way to manage multimedia content in the Japanese Learning Website. The system is designed to be extensible and can be enhanced with additional features as needed.
