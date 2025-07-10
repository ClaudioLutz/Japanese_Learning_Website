# Lesson Export/Import System

## Overview

The Japanese Learning Website includes a comprehensive lesson export/import system that allows administrators to backup, share, and migrate lesson content. The system supports both JSON and ZIP package formats, with full preservation of lesson structure, content, quizzes, and associated files.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Export System](#export-system)
3. [Import System](#import-system)
4. [File Formats](#file-formats)
5. [API Endpoints](#api-endpoints)
6. [Data Structure](#data-structure)
7. [File Handling](#file-handling)
8. [Error Handling](#error-handling)
9. [Usage Examples](#usage-examples)
10. [Best Practices](#best-practices)
11. [Troubleshooting](#troubleshooting)

## Architecture Overview

The export/import system is built with a modular architecture that separates concerns and provides flexibility:

```
Admin Interface
    ↓ Export Request
LessonExporter Class
    ↓ Data Extraction
Database Models
    ↓ JSON/ZIP Creation
File System Storage
    ↓ Download/Upload
Admin Interface
    ↓ Import Request
LessonImporter Class
    ↓ Data Validation
Database Models
```

### Key Components

1. **LessonExporter**: Handles all export operations
2. **LessonImporter**: Manages import processes
3. **Export Packages**: ZIP files containing lesson data and files
4. **Import Validation**: Comprehensive data validation
5. **Duplicate Handling**: Flexible strategies for handling duplicates

## Export System

### LessonExporter Class

The `LessonExporter` class in `app/lesson_export_import.py` handles all export operations:

```python
class LessonExporter:
    """Handles exporting lessons to JSON format with optional file packaging."""
    
    def __init__(self):
        self.export_version = "1.0"
        self.exported_files = []
```

### Export Methods

#### 1. JSON Export
Exports lesson data to a structured JSON format:

```python
def export_lesson(self, lesson_id: int, include_files: bool = True) -> Dict[str, Any]:
    """Export a complete lesson to a structured dictionary."""
    lesson = Lesson.query.get(lesson_id)
    if not lesson:
        raise ValueError(f"Lesson with ID {lesson_id} not found")
    
    # Export main lesson data
    lesson_data = self._export_lesson_metadata(lesson)
    lesson_data['pages'] = self._export_lesson_pages(lesson)
    lesson_data['content'] = self._export_lesson_content(lesson, include_files)
    lesson_data['prerequisites'] = self._export_prerequisites(lesson)
    
    return lesson_data
```

#### 2. ZIP Package Export
Creates complete export packages with files:

```python
def create_export_package(self, lesson_id: int, export_path: str, include_files: bool = True) -> str:
    """Create a complete export package as a ZIP file."""
    lesson_data = self.export_lesson(lesson_id, include_files)
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add lesson JSON
        lesson_json = json.dumps(lesson_data, indent=2, ensure_ascii=False)
        zipf.writestr('lesson_data.json', lesson_json)
        
        # Add associated files
        if include_files and self.exported_files:
            for file_path in self.exported_files:
                full_file_path = os.path.join(upload_folder, file_path)
                if os.path.exists(full_file_path):
                    zipf.write(full_file_path, f"files/{file_path}")
        
        # Add README
        readme_content = self._generate_readme(lesson_data)
        zipf.writestr('README.txt', readme_content)
    
    return zip_path
```

### Export Data Structure

The export system captures complete lesson information:

#### Lesson Metadata
```json
{
  "title": "Introduction to Hiragana",
  "description": "Learn basic hiragana characters",
  "lesson_type": "free",
  "difficulty_level": 1,
  "estimated_duration": 30,
  "order_index": 0,
  "is_published": true,
  "category": {
    "name": "Kana",
    "description": "Japanese syllabary",
    "color_code": "#007bff"
  }
}
```

#### Page Structure
```json
{
  "pages": [
    {
      "page_number": 1,
      "title": "Introduction",
      "description": "Basic concepts"
    }
  ]
}
```

#### Content Items
```json
{
  "content": [
    {
      "content_type": "text",
      "title": "Welcome",
      "content_text": "Welcome to the lesson",
      "order_index": 0,
      "page_number": 1,
      "is_optional": false,
      "is_interactive": false,
      "file_info": {
        "file_path": "lessons/images/welcome.jpg",
        "file_size": 1024000,
        "file_type": "image/jpeg",
        "original_filename": "welcome.jpg"
      }
    }
  ]
}
```

#### Quiz Questions
```json
{
  "quiz_questions": [
    {
      "question_type": "multiple_choice",
      "question_text": "What is the reading of あ?",
      "explanation": "あ is pronounced 'a'",
      "points": 1,
      "order_index": 0,
      "options": [
        {
          "option_text": "a",
          "is_correct": true,
          "order_index": 0,
          "feedback": "Correct!"
        }
      ]
    }
  ]
}
```

## Import System

### LessonImporter Class

The `LessonImporter` class handles all import operations with comprehensive validation:

```python
class LessonImporter:
    """Handles importing lessons from JSON format."""
    
    def __init__(self):
        self.import_version = "1.0"
        self.imported_files = []
```

### Import Process

#### 1. Data Validation
```python
def _validate_import_data(self, lesson_data: Dict[str, Any]) -> None:
    """Validate the structure of import data."""
    required_fields = ['title', 'lesson_type']
    for field in required_fields:
        if field not in lesson_data:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate export version compatibility
    export_metadata = lesson_data.get('export_metadata', {})
    export_version = export_metadata.get('version', '1.0')
    if export_version != self.import_version:
        current_app.logger.warning(f"Version mismatch: export {export_version}, import {self.import_version}")
```

#### 2. Duplicate Handling
The system provides three strategies for handling duplicate lesson titles:

```python
def _handle_duplicate_lesson(self, lesson_data: Dict[str, Any], handle_duplicates: str) -> Lesson:
    """Handle duplicate lesson titles based on strategy."""
    title = lesson_data['title']
    existing_lesson = Lesson.query.filter_by(title=title).first()
    
    if not existing_lesson:
        return self._create_lesson_from_data(lesson_data)
    
    if handle_duplicates == 'skip':
        raise ValueError(f"Lesson '{title}' already exists and skip option selected")
    elif handle_duplicates == 'replace':
        db.session.delete(existing_lesson)
        db.session.flush()
        return self._create_lesson_from_data(lesson_data)
    elif handle_duplicates == 'rename':
        counter = 1
        new_title = f"{title} (Imported {counter})"
        while Lesson.query.filter_by(title=new_title).first():
            counter += 1
            new_title = f"{title} (Imported {counter})"
        
        lesson_data['title'] = new_title
        return self._create_lesson_from_data(lesson_data)
```

#### 3. File Import
```python
def _import_content_file(self, content: LessonContent, file_info: Dict[str, Any], 
                       files_source_path: str) -> None:
    """Import a file associated with content."""
    source_file_path = os.path.join(files_source_path, file_info['file_path'])
    
    if not os.path.exists(source_file_path):
        current_app.logger.warning(f"Source file not found: {source_file_path}")
        return
    
    # Create destination directory
    upload_folder = current_app.config['UPLOAD_FOLDER']
    dest_file_path = os.path.join(upload_folder, file_info['file_path'])
    dest_dir = os.path.dirname(dest_file_path)
    os.makedirs(dest_dir, exist_ok=True)
    
    # Copy file
    shutil.copy2(source_file_path, dest_file_path)
    
    # Update content with file info
    content.file_path = file_info['file_path']
    content.file_size = file_info.get('file_size')
    content.file_type = file_info.get('file_type')
    content.original_filename = file_info.get('original_filename')
```

## File Formats

### JSON Format

The JSON export format is human-readable and contains complete lesson structure:

```json
{
  "title": "Lesson Title",
  "description": "Lesson description",
  "lesson_type": "free",
  "difficulty_level": 1,
  "estimated_duration": 30,
  "order_index": 0,
  "is_published": true,
  "category": { /* category data */ },
  "pages": [ /* page metadata */ ],
  "content": [ /* content items */ ],
  "prerequisites": [ /* prerequisite lessons */ ],
  "export_metadata": {
    "version": "1.0",
    "exported_at": "2025-07-10T14:30:00Z",
    "exported_by": "system",
    "includes_files": true,
    "file_count": 5
  }
}
```

### ZIP Package Format

ZIP packages contain:
- `lesson_data.json`: Complete lesson structure
- `files/`: Directory containing associated media files
- `README.txt`: Human-readable information about the export

```
lesson_export_package.zip
├── lesson_data.json
├── files/
│   ├── lessons/
│   │   ├── images/
│   │   │   └── image1.jpg
│   │   ├── videos/
│   │   │   └── video1.mp4
│   │   └── audio/
│   │       └── audio1.mp3
└── README.txt
```

### Multiple Lesson Export

For bulk exports, the system creates a master ZIP containing individual lesson packages:

```
lessons_export_20250710_143000.zip
├── lesson_export_Hiragana_Basics_20250710_143000.zip
├── lesson_export_Katakana_Intro_20250710_143001.zip
├── lesson_export_Basic_Grammar_20250710_143002.zip
└── export_manifest.json
```

## API Endpoints

### Export Endpoints

#### Single Lesson JSON Export
```http
GET /api/admin/lessons/{lesson_id}/export?include_files=true
```

**Response**: JSON file download with lesson data

#### Single Lesson Package Export
```http
POST /api/admin/lessons/{lesson_id}/export-package
Content-Type: application/json

{
  "include_files": true
}
```

**Response**: ZIP file download with complete package

#### Multiple Lesson Export
```http
POST /api/admin/lessons/export-multiple
Content-Type: application/json

{
  "lesson_ids": [1, 2, 3],
  "include_files": true
}
```

**Response**: ZIP file containing multiple lesson packages

### Import Endpoints

#### Import Information
```http
POST /api/admin/lessons/import-info
Content-Type: multipart/form-data

file: [JSON or ZIP file]
```

**Response**: Information about the import file without importing
```json
{
  "success": true,
  "info": {
    "file_type": "single_lesson_zip",
    "lesson_count": 1,
    "lessons": [
      {
        "title": "Introduction to Hiragana",
        "difficulty": 1,
        "pages": 3,
        "content_count": 15,
        "files": ["image1.jpg", "audio1.mp3"]
      }
    ],
    "warnings": ["A lesson with this title already exists."]
  }
}
```

#### JSON Import
```http
POST /api/admin/lessons/import
Content-Type: multipart/form-data

file: [JSON file]
handle_duplicates: rename|replace|skip
```

#### ZIP Package Import
```http
POST /api/admin/lessons/import-package
Content-Type: multipart/form-data

file: [ZIP file]
handle_duplicates: rename|replace|skip
```

**Response**: Import result
```json
{
  "success": true,
  "message": "Lesson imported successfully",
  "lesson_id": 123,
  "lesson_title": "Imported Lesson"
}
```

## Data Structure

### Export Metadata

Every export includes metadata for tracking and validation:

```json
{
  "export_metadata": {
    "version": "1.0",
    "exported_at": "2025-07-10T14:30:00Z",
    "exported_by": "system",
    "includes_files": true,
    "file_count": 5
  }
}
```

### Content Type Mapping

The system handles various content types:

| Content Type | Description | Special Handling |
|--------------|-------------|------------------|
| `text` | Plain text content | Direct export |
| `kana` | Kana character reference | Exports `content_id` |
| `kanji` | Kanji character reference | Exports `content_id` |
| `vocabulary` | Vocabulary reference | Exports `content_id` |
| `grammar` | Grammar point reference | Exports `content_id` |
| `image` | Image file | File export/import |
| `video` | Video file | File export/import |
| `audio` | Audio file | File export/import |
| `interactive` | Quiz content | Exports questions/options |

### Quiz Data Structure

Interactive content includes complete quiz structure:

```json
{
  "is_interactive": true,
  "max_attempts": 3,
  "passing_score": 70,
  "quiz_questions": [
    {
      "question_type": "multiple_choice",
      "question_text": "Question text",
      "explanation": "Answer explanation",
      "points": 1,
      "order_index": 0,
      "options": [
        {
          "option_text": "Option A",
          "is_correct": true,
          "order_index": 0,
          "feedback": "Correct answer feedback"
        }
      ]
    }
  ]
}
```

## File Handling

### File Export Process

1. **File Discovery**: Identify all files referenced by lesson content
2. **File Validation**: Verify files exist in the file system
3. **Path Mapping**: Create relative paths for ZIP structure
4. **File Copying**: Copy files to ZIP package maintaining structure
5. **Metadata Recording**: Track file information in JSON data

### File Import Process

1. **ZIP Extraction**: Extract ZIP package to temporary directory
2. **File Validation**: Verify all referenced files are present
3. **Directory Creation**: Create necessary upload directories
4. **File Copying**: Copy files to upload directory structure
5. **Database Update**: Update content records with file paths

### File Path Handling

The system maintains consistent file paths across export/import:

```python
# Export: Store relative paths
file_info = {
    'file_path': 'lessons/images/filename.jpg',  # Relative to upload folder
    'file_size': 1024000,
    'file_type': 'image/jpeg',
    'original_filename': 'original.jpg'
}

# Import: Reconstruct full paths
upload_folder = current_app.config['UPLOAD_FOLDER']
dest_file_path = os.path.join(upload_folder, file_info['file_path'])
```

## Error Handling

### Export Errors

#### Missing Lesson
```json
{
  "error": "Lesson with ID 123 not found"
}
```

#### File Access Errors
```python
try:
    lesson_zip_path = create_lesson_export_package(lesson_id, temp_dir, include_files)
except Exception as e:
    current_app.logger.error(f"Error exporting lesson {lesson_id}: {e}")
    return jsonify({"error": "Failed to export lesson"}), 500
```

### Import Errors

#### Invalid File Format
```json
{
  "error": "Invalid JSON format"
}
```

#### Missing Required Fields
```json
{
  "error": "Missing required field: title"
}
```

#### Duplicate Handling
```json
{
  "error": "Lesson 'Introduction to Hiragana' already exists and skip option selected"
}
```

#### File Import Errors
```python
def _import_content_file(self, content, file_info, files_source_path):
    source_file_path = os.path.join(files_source_path, file_info['file_path'])
    
    if not os.path.exists(source_file_path):
        current_app.logger.warning(f"Source file not found: {source_file_path}")
        return  # Continue without file
```

## Usage Examples

### Exporting a Single Lesson

```python
# Using the API
import requests

response = requests.get(
    f'/api/admin/lessons/{lesson_id}/export',
    params={'include_files': 'true'},
    headers={'X-CSRFToken': csrf_token}
)

with open('lesson_export.json', 'wb') as f:
    f.write(response.content)
```

### Creating a ZIP Package

```python
# Using the service directly
from app.lesson_export_import import LessonExporter

exporter = LessonExporter()
zip_path = exporter.create_export_package(
    lesson_id=1,
    export_path='/tmp/exports',
    include_files=True
)
```

### Importing from ZIP

```python
# Using the API
files = {'file': open('lesson_package.zip', 'rb')}
data = {'handle_duplicates': 'rename'}

response = requests.post(
    '/api/admin/lessons/import-package',
    files=files,
    data=data,
    headers={'X-CSRFToken': csrf_token}
)
```

### Bulk Export

```python
# Export multiple lessons
lesson_ids = [1, 2, 3, 4, 5]
response = requests.post(
    '/api/admin/lessons/export-multiple',
    json={
        'lesson_ids': lesson_ids,
        'include_files': True
    },
    headers={
        'Content-Type': 'application/json',
        'X-CSRFToken': csrf_token
    }
)
```

## Best Practices

### Export Best Practices

1. **Include Files**: Always export with files for complete backups
2. **Regular Backups**: Schedule regular exports of important lessons
3. **Version Control**: Keep track of export versions and dates
4. **File Organization**: Use descriptive names for export files
5. **Storage**: Store exports in secure, backed-up locations

### Import Best Practices

1. **Preview First**: Use import-info endpoint to preview imports
2. **Handle Duplicates**: Choose appropriate duplicate handling strategy
3. **Validate Content**: Review imported content before publishing
4. **Test Environment**: Import to test environment first
5. **Backup Before Import**: Create backups before importing

### File Management

1. **File Validation**: Verify all files are present before export
2. **Path Consistency**: Maintain consistent file path structures
3. **File Cleanup**: Clean up temporary files after operations
4. **Size Monitoring**: Monitor export package sizes
5. **Compression**: Use appropriate compression for large packages

## Troubleshooting

### Common Issues

#### Export Issues

**Issue**: "Lesson not found"
```python
# Solution: Verify lesson ID exists
lesson = Lesson.query.get(lesson_id)
if not lesson:
    print(f"Lesson {lesson_id} does not exist")
```

**Issue**: "File not found during export"
```python
# Solution: Check file paths and permissions
import os
file_path = os.path.join(upload_folder, relative_path)
if not os.path.exists(file_path):
    print(f"File missing: {file_path}")
```

#### Import Issues

**Issue**: "Invalid JSON format"
```python
# Solution: Validate JSON before import
import json
try:
    with open('lesson_data.json', 'r') as f:
        data = json.load(f)
except json.JSONDecodeError as e:
    print(f"JSON error: {e}")
```

**Issue**: "Database integrity error"
```python
# Solution: Check for constraint violations
try:
    db.session.commit()
except IntegrityError as e:
    db.session.rollback()
    print(f"Integrity error: {e}")
```

### Debugging Tips

#### Enable Detailed Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### Validate Export Data
```python
def validate_export_data(lesson_data):
    required_fields = ['title', 'lesson_type', 'content']
    for field in required_fields:
        if field not in lesson_data:
            print(f"Missing field: {field}")
            return False
    return True
```

#### Check File Integrity
```python
def check_file_integrity(zip_path):
    import zipfile
    try:
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            bad_files = zipf.testzip()
            if bad_files:
                print(f"Corrupted files: {bad_files}")
            else:
                print("ZIP file is valid")
    except zipfile.BadZipFile:
        print("Invalid ZIP file")
```

### Performance Optimization

#### Large File Handling
```python
# For large exports, use streaming
def stream_export(lesson_id):
    def generate():
        # Stream data in chunks
        for chunk in export_chunks(lesson_id):
            yield chunk
    
    return Response(generate(), mimetype='application/zip')
```

#### Memory Management
```python
# Process files in batches to manage memory
def process_files_in_batches(files, batch_size=10):
    for i in range(0, len(files), batch_size):
        batch = files[i:i + batch_size]
        process_batch(batch)
```

## Future Enhancements

### Planned Features

1. **Incremental Exports**: Export only changed content
2. **Scheduled Exports**: Automatic backup scheduling
3. **Cloud Storage**: Direct export to cloud storage services
4. **Version Control**: Track lesson versions and changes
5. **Selective Import**: Import specific parts of lessons
6. **Migration Tools**: Tools for migrating between system versions
7. **Validation Reports**: Detailed validation reports for imports
8. **Rollback Support**: Ability to rollback failed imports

### Technical Improvements

1. **Streaming Exports**: Handle large exports without memory issues
2. **Parallel Processing**: Parallel file processing for better performance
3. **Compression Options**: Multiple compression formats and levels
4. **Encryption**: Encrypted export packages for sensitive content
5. **Checksums**: File integrity verification with checksums
6. **Progress Tracking**: Real-time progress updates for long operations

---

The Lesson Export/Import System provides a robust foundation for content management, backup, and migration in the Japanese Learning Website. It ensures data integrity while providing flexibility for various use cases and deployment scenarios.
