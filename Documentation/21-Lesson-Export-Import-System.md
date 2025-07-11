# 21. Lesson Export/Import System

## 1. Overview

The Lesson Export/Import System is a powerful feature designed for content management, backup, and migration. It allows administrators to export a complete lesson—including all its metadata, pages, content items, quizzes, and associated media files—into a portable format. This package can then be archived or imported into another instance of the application.

The entire system is encapsulated in the `app/lesson_export_import.py` module, which provides two main classes: `LessonExporter` and `LessonImporter`.

## 2. Key Features

-   **Comprehensive Export**: Exports all aspects of a lesson, from metadata to the deepest quiz options.
-   **Two Export Formats**:
    1.  **JSON Data**: A structured dictionary containing all database information.
    2.  **ZIP Package**: A portable `.zip` file containing the JSON data plus all associated media files (images, audio, etc.).
-   **Intelligent Import**: The import process can handle complex data relationships and offers strategies for resolving conflicts.
-   **Duplicate Handling**: When importing a lesson with a title that already exists, the system can be configured to:
    -   `rename`: Import the lesson with a new, unique name (e.g., "My Lesson (Imported 1)").
    -   `replace`: Delete the existing lesson and replace it with the imported one.
    -   `skip`: Abort the import for that specific lesson.
-   **File Management**: Automatically handles copying files from a ZIP package into the correct application directory structure during import.
-   **Database Integrity**: The import process is wrapped in a database transaction. If any part of the import fails, the entire transaction is rolled back to prevent a partially imported, corrupt lesson.

## 3. Architecture

The system is composed of two main classes that work in tandem.

-   **`LessonExporter`**: Queries the database for a given `lesson_id`, recursively gathers all related data (pages, content, quizzes, etc.), and serializes it into a Python dictionary. It can then package this data and associated files into a ZIP archive.
-   **`LessonImporter`**: Takes a Python dictionary (typically from a `lesson_data.json` file), validates it, and carefully reconstructs the lesson in the database. It creates all necessary records and relationships and can copy files from a source directory to the application's upload folder.

## 4. The Export Process

### 4.1. `lesson_data.json` Structure

The core of the export is a single JSON file with a well-defined structure.

```json
{
  "title": "Complete Hiragana Mastery",
  "description": "A comprehensive guide...",
  "lesson_type": "free",
  "difficulty_level": 1,
  "category": {
    "name": "Basics",
    "description": "Fundamental concepts."
  },
  "pages": [
    {
      "page_number": 1,
      "title": "Introduction to Hiragana"
    }
  ],
  "content": [
    {
      "content_type": "text",
      "content_text": "Welcome to the world of Hiragana!",
      "page_number": 1,
      "order_index": 0,
      "file_info": {
        "file_path": "lessons/image/lesson_1/hiragana_chart.jpg",
        "file_size": 123456,
        "original_filename": "hiragana_chart.jpg"
      },
      "quiz_questions": [
        {
          "question_type": "multiple_choice",
          "question_text": "What is 'a' in Hiragana?",
          "options": [
            {"option_text": "あ", "is_correct": true},
            {"option_text": "い", "is_correct": false}
          ]
        }
      ]
    }
  ],
  "prerequisites": [
    {
      "prerequisite_lesson_title": "Introduction to Japanese"
    }
  ],
  "export_metadata": {
    "version": "1.0",
    "exported_at": "2025-07-11T18:00:00Z",
    "includes_files": true,
    "file_count": 5
  }
}
```

### 4.2. The ZIP Package Structure

When exporting as a package, the system creates a `.zip` file with the following structure:

```
lesson_export_Complete_Hiragana_Mastery_20250711_180000.zip
├── lesson_data.json
├── README.txt
└── files/
    └── lessons/
        └── image/
            └── lesson_1/
                ├── hiragana_chart.jpg
                └── another_image.png
```

-   `lesson_data.json`: The JSON file as described above.
-   `README.txt`: An auto-generated file summarizing the lesson and export details.
-   `files/`: A directory containing all associated media files, preserving the original directory structure from the `uploads` folder.

## 5. Core Component Methods

### 5.1. `LessonExporter`

| Method                           | Description                                                                                             |
| -------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `export_lesson(id, files)`       | Exports a single lesson to a Python dictionary. The main entry point for data serialization.            |
| `create_export_package(id, path)`| Creates the full `.zip` package, including the JSON data, media files, and README.                      |

### 5.2. `LessonImporter`

| Method                           | Description                                                                                             |
| -------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `import_lesson(data, duplicates, ...)`| Imports a lesson from a Python dictionary. Contains the core logic for validation and database insertion. |
| `import_from_zip(path, duplicates)`| Extracts a `.zip` package into a temporary directory and then calls `import_lesson` to perform the import. |

## 6. Usage Examples

### 6.1. Exporting a Lesson to a ZIP File

This could be triggered from an admin panel or a CLI script.

```python
# In a Flask route or a script
from app.lesson_export_import import create_lesson_export_package
from flask import current_app

@app.route('/admin/lesson/<int:lesson_id>/export')
@admin_required
def export_lesson_package(lesson_id):
    try:
        # Define a path for the exports, e.g., in a temporary or designated folder
        export_dir = os.path.join(current_app.instance_path, 'exports')
        
        # Create the package
        zip_path = create_lesson_export_package(lesson_id, export_dir)
        
        # Return the file to the user
        return send_file(zip_path, as_attachment=True)
        
    except ValueError as e:
        flash(str(e))
        return redirect(url_for('admin.manage_lessons'))
    except Exception as e:
        current_app.logger.error(f"Export failed: {e}")
        flash("An unexpected error occurred during export.")
        return redirect(url_for('admin.manage_lessons'))
```

### 6.2. Importing a Lesson from a ZIP File

This would handle a file upload from an admin form.

```python
# In a Flask route or a script
from app.lesson_export_import import import_lesson_from_zip
from werkzeug.utils import secure_filename

@app.route('/admin/import_lesson', methods=['POST'])
@admin_required
def import_lesson_package():
    file = request.files.get('zip_package')
    if not file or not file.filename.endswith('.zip'):
        flash("Please upload a valid .zip export package.")
        return redirect(url_for('admin.show_import_page'))

    # Save the zip file temporarily
    temp_path = os.path.join(current_app.instance_path, 'temp_imports')
    os.makedirs(temp_path, exist_ok=True)
    zip_path = os.path.join(temp_path, secure_filename(file.filename))
    file.save(zip_path)

    try:
        # Get the desired duplicate handling strategy from the form
        duplicate_strategy = request.form.get('duplicate_strategy', 'rename') # 'rename', 'replace', or 'skip'
        
        # Import from the zip file
        imported_lesson = import_lesson_from_zip(zip_path, handle_duplicates=duplicate_strategy)
        
        flash(f"Successfully imported lesson: '{imported_lesson.title}'")
        
    except ValueError as e:
        flash(f"Import validation error: {e}")
    except Exception as e:
        current_app.logger.error(f"Import failed: {e}")
        flash("An unexpected error occurred during import.")
    finally:
        # Clean up the temporary zip file
        if os.path.exists(zip_path):
            os.remove(zip_path)
            
    return redirect(url_for('admin.manage_lessons'))
