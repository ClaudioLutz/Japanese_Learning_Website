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

## 6. Usage Example

Here is a simplified example of how the `FileUploadHandler` would be used within a Flask route to handle a file upload for a lesson.

```python
# In app/routes.py
from flask import request, flash, redirect, url_for
from .utils import FileUploadHandler
from .models import db, LessonContent

@app.route('/admin/lesson/<int:lesson_id>/add_content', methods=['POST'])
@admin_required # Assumes an admin-only decorator
def add_lesson_content(lesson_id):
    file = request.files.get('file')
    lesson = Lesson.query.get_or_404(lesson_id)

    if not file or not file.filename:
        flash('No file selected.')
        return redirect(url_for('admin.manage_lesson', lesson_id=lesson_id))

    file_type = FileUploadHandler.get_file_type(file.filename)
    if not file_type or not FileUploadHandler.allowed_file(file.filename, file_type):
        flash('File type not allowed.')
        return redirect(url_for('admin.manage_lesson', lesson_id=lesson_id))

    # 1. Generate secure filename and create directory
    unique_filename = FileUploadHandler.generate_unique_filename(file.filename)
    lesson_dir = FileUploadHandler.create_lesson_directory(lesson.id, file_type)
    file_path = os.path.join(lesson_dir, unique_filename)
    
    # 2. Save the file temporarily
    file.save(file_path)

    # 3. Validate and process the file
    if not FileUploadHandler.validate_file_content(file_path, file_type):
        FileUploadHandler.delete_file(file_path) # Clean up invalid file
        flash('File content does not match its extension.')
        return redirect(url_for('admin.manage_lesson', lesson_id=lesson_id))

    if file_type == 'image':
        if not FileUploadHandler.process_image(file_path):
            FileUploadHandler.delete_file(file_path) # Clean up failed processing
            flash('Failed to process image.')
            return redirect(url_for('admin.manage_lesson', lesson_id=lesson_id))

    # 4. Get file info and create database record
    info = FileUploadHandler.get_file_info(file_path)
    relative_path = os.path.join('lessons', file_type, f'lesson_{lesson_id}', unique_filename)

    new_content = LessonContent(
        lesson_id=lesson.id,
        content_type=file_type,
        file_path=relative_path,
        original_filename=file.filename,
        file_size=info['size'],
        file_type=info['mime_type']
    )
    db.session.add(new_content)
    db.session.commit()

    flash('File uploaded successfully.')
    return redirect(url_for('admin.manage_lesson', lesson_id=lesson_id))
