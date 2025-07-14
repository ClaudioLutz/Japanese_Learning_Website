# 20. File Upload System

## 1. Overview

The File Upload System is a critical component responsible for securely handling all user-uploaded files, such as images, audio, and video for lessons. The system is designed to be robust, secure, and maintain an organized file structure on the server.

All file handling logic is encapsulated within the `FileUploadHandler` class in `app/utils.py`, making it a centralized and reusable service.

## 2. Architecture and Workflow

The file upload process follows a clear, multi-step workflow designed to validate and secure files before they are stored.

```
+----------------------+      +----------------------+      +-----------------------+      +---------------------+
| Frontend (Admin UI)  |----->|   Flask Route        |----->|   FileUploadHandler   |----->|   Server Filesystem |
| (e.g., manage_lessons) |      | (e.g., in routes.py) |      |   (in app/utils.py)   |      | (e.g., /static/uploads) |
+----------------------+      +----------------------+      +-----------------------+      +---------------------+
         |                             |                             |                              ^
         | User submits form           | Receives file object        | 1. Validate Extension        |
         | with a file                 |                             | 2. Generate Secure Name      |
         |                             |                             | 3. Create Directory          |
         |                             |                             | 4. Save File                 |
         |                             |                             | 5. Validate Content (MIME)   |
         |                             |                             | 6. Process Image (Resize)    |
         |                             |                             | 7. Update DB Model           |
         |                             |                             +------------------------------+
         |                             |                                                            |
         +-----------------------------<-----------------------------<------------------------------+
           Returns success/error
           to the user
```

## 3. Core Component: `FileUploadHandler`

The `FileUploadHandler` is a static class that provides a collection of utility methods for handling file uploads.

### 3.1. Key Methods

| Method                           | Description                                                                                                                            |
| -------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| `allowed_file(filename, type)`   | Checks if the file's extension is permitted based on the `ALLOWED_EXTENSIONS` config for a given file type (e.g., 'image', 'audio').     |
| `get_file_type(filename)`        | Determines the general file type ('image', 'video', 'audio') based on the file's extension.                                            |
| `generate_unique_filename(fn)`   | Creates a secure, unique filename by combining the secure version of the original name with a UUID, preventing path traversal attacks. |
| `create_lesson_directory(id, type)`| Creates a dedicated, organized directory for a specific lesson's files (e.g., `/uploads/lessons/image/lesson_123/`).                 |
| `validate_file_content(path, type)`| **(Security Critical)** Uses `python-magic` to inspect the file's actual content (MIME type) to ensure it matches its extension.      |
| `process_image(path, ...)`       | **(Security Critical)** Opens, resizes, and re-saves uploaded images using Pillow. This strips potentially malicious metadata.         |
| `get_file_info(path)`            | Gathers metadata about a file, such as its size and MIME type.                                                                         |
| `format_file_size(bytes)`        | Converts a file size in bytes to a human-readable string (e.g., "1.2 MB").                                                             |
| `delete_file(path)`              | Safely deletes a file from the filesystem.                                                                                             |
| `get_supported_formats(type)`    | Returns a list of allowed extensions for a given file type.                                                                            |

## 4. Configuration

The file upload system relies on two key variables set in the Flask application's configuration (e.g., in `instance/config.py`).

-   **`UPLOAD_FOLDER`**: The absolute path to the root directory where all uploaded files will be stored.
    -   Example: `UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app/static/uploads')`

-   **`ALLOWED_EXTENSIONS`**: A dictionary that maps file types to a set of allowed file extensions. This is the primary defense against users uploading disallowed or potentially dangerous file types.
    -   Example:
        ```python
        ALLOWED_EXTENSIONS = {
            'image': {'png', 'jpg', 'jpeg', 'gif', 'webp'},
            'video': {'mp4', 'webm', 'mov'},
            'audio': {'mp3', 'wav', 'ogg'}
        }
        ```

## 5. Security Measures

Securing file uploads is paramount. The `FileUploadHandler` implements a defense-in-depth strategy:

1.  **Extension Validation**: The `allowed_file` method provides the first line of defense by checking the file's extension against a strict allowlist defined in the configuration.
2.  **Secure Filenames**: `generate_unique_filename` uses Werkzeug's `secure_filename` to flatten any dangerous characters or path traversal sequences (like `../`) in the user-provided filename. Appending a UUID prevents naming conflicts and makes enumeration harder.
3.  **Content Validation (MIME Sniffing)**: This is a crucial second layer of validation. `validate_file_content` uses the `python-magic` library to read the file's magic numbers (the first few bytes) to determine its true MIME type. This prevents a user from, for example, renaming an executable file `.exe` to `.jpg` and bypassing the extension check.
4.  **Image Re-processing**: For images, `process_image` opens and re-saves the file using the Pillow library. This is an effective way to strip any embedded malicious scripts (e.g., EXIF-based payloads) from the image file, neutralizing a potential XSS vector.
5.  **Organized Storage**: By storing files in structured directories (`/lessons/<type>/<lesson_id>`), the system avoids polluting a single directory and makes it easier to manage permissions and access control.

## 6. Current Implementation

### 6.1. File Upload API Endpoint

The current implementation provides a dedicated API endpoint for file uploads:

```python
@bp.route('/api/admin/upload-file', methods=['POST'])
@login_required
@admin_required
def upload_file():
    """Handle file upload, validate, process, and return file information"""
    import os

    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file part in the request'}), 400

    file_storage = request.files['file']
    lesson_id_str = request.form.get('lesson_id') # Optional: for organizing files by lesson

    if not file_storage or not file_storage.filename:
        return jsonify({'success': False, 'error': 'No file selected'}), 400

    original_filename = file_storage.filename

    # Check allowed extensions (basic check)
    file_type_from_ext = FileUploadHandler.get_file_type(original_filename)
    if not file_type_from_ext:
        return jsonify({'success': False, 'error': 'File type not allowed by extension.'}), 415

    if not FileUploadHandler.allowed_file(original_filename, file_type_from_ext):
        return jsonify({'success': False, 'error': f"File extension for '{file_type_from_ext}' not allowed."}), 415

    # Generate unique filename
    unique_filename = FileUploadHandler.generate_unique_filename(original_filename)

    # Create temporary path for validation
    upload_folder = current_app.config['UPLOAD_FOLDER']
    temp_dir = os.path.join(upload_folder, 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    temp_filepath = os.path.join(temp_dir, unique_filename)

    try:
        file_storage.save(temp_filepath)

        # Validate file content (MIME type)
        if not FileUploadHandler.validate_file_content(temp_filepath, file_type_from_ext):
            FileUploadHandler.delete_file(temp_filepath)
            return jsonify({'success': False, 'error': 'File content does not match extension or is not allowed.'}), 415

        # Process image if it's an image file
        if file_type_from_ext == 'image':
            if not FileUploadHandler.process_image(temp_filepath):
                FileUploadHandler.delete_file(temp_filepath)
                return jsonify({'success': False, 'error': 'Image processing failed.'}), 500
        
        # Determine final directory based on file type
        final_type_dir = os.path.join(upload_folder, 'lessons', file_type_from_ext)
        os.makedirs(final_type_dir, exist_ok=True)
        final_filepath = os.path.join(final_type_dir, unique_filename)
        
        # Move validated and processed file to its final destination
        os.rename(temp_filepath, final_filepath)

        # Get file info for the response
        file_info = FileUploadHandler.get_file_info(final_filepath)

        # Relative path for URL generation and storing in DB
        relative_file_path = os.path.join('lessons', file_type_from_ext, unique_filename).replace('\\', '/')

        return jsonify({
            'success': True,
            'filePath': url_for('static', filename=os.path.join('uploads', relative_file_path).replace('\\', '/'), _external=False),
            'dbPath': relative_file_path,
            'fileName': unique_filename,
            'originalFilename': original_filename,
            'fileType': file_type_from_ext,
            'fileSize': file_info.get('size'),
            'mimeType': file_info.get('mime_type'),
            'dimensions': file_info.get('dimensions')
        }), 200

    except Exception as e:
        current_app.logger.error(f"File upload failed: {e}", exc_info=True)
        if os.path.exists(temp_filepath):
            FileUploadHandler.delete_file(temp_filepath)
        return jsonify({'success': False, 'error': 'An server error occurred during file upload.'}), 500
    finally:
        # Double check temp file is removed if it still exists
        if os.path.exists(temp_filepath):
             FileUploadHandler.delete_file(temp_filepath)
```

### 6.2. File-Based Content Addition

```python
@bp.route('/api/admin/lessons/<int:lesson_id>/content/file', methods=['POST'])
@login_required
@admin_required
def add_file_content(lesson_id):
    """Add file-based content to lesson"""
    lesson = Lesson.query.get_or_404(lesson_id)
    data = request.json
    
    if not data or not data.get('content_type') or not data.get('file_path'):
        return jsonify({"error": "Missing required fields: content_type, file_path"}), 400
    
    # Convert string 'false'/'true' to boolean for is_optional
    is_optional = data.get('is_optional', False)
    if isinstance(is_optional, str):
        is_optional = is_optional.lower() == 'true'
    
    # Determine the next order index
    last_content = LessonContent.query.filter_by(lesson_id=lesson_id).order_by(LessonContent.order_index.desc()).first()
    next_order_index = (last_content.order_index + 1) if last_content else 0

    new_content = LessonContent(
        lesson_id=lesson_id,
        content_type=data['content_type'],
        title=data.get('title'),
        content_text=data.get('description'),
        file_path=data['file_path'],
        file_size=data.get('file_size'),
        file_type=data.get('file_type'),
        original_filename=data.get('original_filename'),
        order_index=next_order_index,
        is_optional=is_optional
    )
    
    try:
        db.session.add(new_content)
        db.session.commit()
        return jsonify(model_to_dict(new_content)), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": f"Database error occurred: {str(e)}"}), 500
```

### 6.3. File Serving

```python
@bp.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    import os
    from flask import send_from_directory
    
    upload_folder = current_app.config['UPLOAD_FOLDER']
    file_path = os.path.join(upload_folder, filename)
    
    # Security check - ensure file is within upload folder
    if not os.path.abspath(file_path).startswith(os.path.abspath(upload_folder)):
        return jsonify({"error": "Access denied"}), 403
    
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404
    
    directory = os.path.dirname(file_path)
    basename = os.path.basename(file_path)
    
    return send_from_directory(directory, basename)
```

### 6.4. File Deletion

```python
@bp.route('/api/admin/delete-file', methods=['DELETE'])
@login_required
@admin_required
def delete_file():
    """Delete uploaded file"""
    from app.utils import FileUploadHandler
    import os
    
    data = request.json
    if not data or not data.get('file_path'):
        return jsonify({"error": "File path required"}), 400
    
    file_path_from_request = data['file_path']
    content_id = data.get('content_id')

    # Path validation against UPLOAD_FOLDER
    full_request_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file_path_from_request)
    if not os.path.abspath(full_request_path).startswith(os.path.abspath(current_app.config['UPLOAD_FOLDER'])):
        return jsonify({"error": "Access denied: Invalid file path."}), 403

    # Handle content-based deletion or direct file deletion
    if content_id:
        content = LessonContent.query.get(content_id)
        if content and content.file_path:
            if content.delete_file():
                db.session.delete(content)
                db.session.commit()
                return jsonify({"message": "Content and file deleted successfully"}), 200
            else:
                return jsonify({"message": "Content deleted, but file deletion failed"}), 207
    else:
        # Direct file deletion
        if FileUploadHandler.delete_file(full_request_path):
            return jsonify({"message": f"File {file_path_from_request} deleted successfully"}), 200
        else:
            return jsonify({"error": f"Failed to delete file {file_path_from_request}"}), 500
```

## 7. Enhanced Security Features

### 7.1. Multi-Layer Validation

The current implementation uses a comprehensive validation approach:

1. **Extension Check**: Initial validation against allowed extensions
2. **Temporary Storage**: Files are saved to a temporary directory first
3. **Content Validation**: MIME type verification using `python-magic`
4. **Image Processing**: Automatic image optimization and metadata stripping
5. **Path Security**: Absolute path validation to prevent directory traversal

### 7.2. File Processing Pipeline

```python
# Enhanced image processing with security features
@staticmethod
def process_image(file_path, max_width=1920, max_height=1080):
    """Resize and optimize images. Returns True on success, False on failure."""
    try:
        with Image.open(file_path) as img:
            original_format = img.format
            # Convert to RGB if necessary (for PNG with transparency)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Create a white background image
                background = Image.new('RGB', img.size, (255, 255, 255))
                # Handle different modes appropriately
                if img.mode == 'P':
                    img = img.convert('RGBA')

                mask = None
                if img.mode == 'RGBA':
                    mask = img.split()[-1] # Get alpha channel
                elif img.mode == 'LA':
                    mask = img.split()[-1]
                    img = img.convert('RGB')

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
            
            # Save optimized image as JPEG with quality optimization
            img.save(file_path, 'JPEG', quality=85, optimize=True)
            
            return True
    except Exception as e:
        current_app.logger.error(f"Error processing image {file_path}: {e}")
        return False
```

## 8. Configuration Updates

### 8.1. Application Configuration

The file upload system is configured in `app/__init__.py`:

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

# Create upload directories if they don't exist
upload_dirs = [
    os.path.join(UPLOAD_FOLDER, 'lessons', 'images'),
    os.path.join(UPLOAD_FOLDER, 'lessons', 'videos'),
    os.path.join(UPLOAD_FOLDER, 'lessons', 'audio'),
    os.path.join(UPLOAD_FOLDER, 'temp')
]
for directory in upload_dirs:
    os.makedirs(directory, exist_ok=True)
```

### 8.2. Directory Structure

The system creates an organized directory structure:

```
app/static/uploads/
├── temp/                    # Temporary files during processing
├── lessons/
│   ├── image/              # Image files
│   │   ├── filename1.jpg
│   │   └── filename2.png
│   ├── video/              # Video files
│   │   ├── filename1.mp4
│   │   └── filename2.webm
│   └── audio/              # Audio files
│       ├── filename1.mp3
│       └── filename2.wav
```

## 9. Integration with Lesson Content

### 9.1. LessonContent Model Integration

The `LessonContent` model includes comprehensive file handling:

```python
# File-related fields in LessonContent
file_path = db.Column(db.String(500))  # Relative path to uploaded file
file_size = db.Column(db.Integer)      # File size in bytes
file_type = db.Column(db.String(50))   # MIME type
original_filename = db.Column(db.String(255))  # Original filename

def get_file_url(self):
    """Get URL for accessing uploaded file"""
    from flask import url_for
    if self.file_path:
        return url_for('routes.uploaded_file', filename=self.file_path)
    return self.media_url  # Fallback to URL-based media

def delete_file(self):
    """Delete associated file from filesystem"""
    if self.file_path:
        from flask import current_app
        import os
        file_full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], self.file_path)
        try:
            if os.path.exists(file_full_path):
                os.remove(file_full_path)
                current_app.logger.info(f"Successfully deleted file: {file_full_path}")
            return True
        except OSError as e:
            current_app.logger.error(f"Error deleting file {file_full_path}: {e}")
            return False
```

This comprehensive file upload system provides secure, organized, and efficient handling of multimedia content for the Japanese Learning Website.
