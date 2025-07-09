"""
Lesson Export/Import System for Japanese Learning Website

This module provides functionality to export complete lessons to JSON format
and import them back into the system, including all content, quizzes, and metadata.
"""

import json
import os
import shutil
import zipfile
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError
from app import db
from app.models import (
    Lesson, LessonPage, LessonContent, QuizQuestion, QuizOption,
    LessonCategory, LessonPrerequisite
)


class LessonExporter:
    """Handles exporting lessons to JSON format with optional file packaging."""
    
    def __init__(self):
        self.export_version = "1.0"
        self.exported_files = []
    
    def export_lesson(self, lesson_id: int, include_files: bool = True) -> Dict[str, Any]:
        """
        Export a complete lesson to a structured dictionary.
        
        Args:
            lesson_id: ID of the lesson to export
            include_files: Whether to include file references and copy files
            
        Returns:
            Dictionary containing complete lesson data
            
        Raises:
            ValueError: If lesson not found
            Exception: For other export errors
        """
        lesson = Lesson.query.get(lesson_id)
        if not lesson:
            raise ValueError(f"Lesson with ID {lesson_id} not found")
        
        try:
            # Export main lesson data
            lesson_data = self._export_lesson_metadata(lesson)
            
            # Export lesson pages
            lesson_data['pages'] = self._export_lesson_pages(lesson)
            
            # Export lesson content
            lesson_data['content'] = self._export_lesson_content(lesson, include_files)
            
            # Export prerequisites
            lesson_data['prerequisites'] = self._export_prerequisites(lesson)
            
            # Add export metadata
            lesson_data['export_metadata'] = {
                'version': self.export_version,
                'exported_at': datetime.utcnow().isoformat(),
                'exported_by': 'system',  # Could be enhanced to track user
                'includes_files': include_files,
                'file_count': len(self.exported_files)
            }
            
            current_app.logger.info(f"Successfully exported lesson {lesson_id}")
            return lesson_data
            
        except Exception as e:
            current_app.logger.error(f"Error exporting lesson {lesson_id}: {e}")
            raise
    
    def _export_lesson_metadata(self, lesson: Lesson) -> Dict[str, Any]:
        """Export basic lesson metadata."""
        return {
            'title': lesson.title,
            'description': lesson.description,
            'lesson_type': lesson.lesson_type,
            'difficulty_level': lesson.difficulty_level,
            'estimated_duration': lesson.estimated_duration,
            'order_index': lesson.order_index,
            'is_published': lesson.is_published,
            'thumbnail_url': lesson.thumbnail_url,
            'video_intro_url': lesson.video_intro_url,
            'category': {
                'name': lesson.category.name,
                'description': lesson.category.description,
                'color_code': lesson.category.color_code
            } if lesson.category else None,
            'created_at': lesson.created_at.isoformat() if lesson.created_at else None,
            'updated_at': lesson.updated_at.isoformat() if lesson.updated_at else None
        }
    
    def _export_lesson_pages(self, lesson: Lesson) -> List[Dict[str, Any]]:
        """Export lesson page metadata."""
        pages = []
        for page in lesson.pages_metadata:
            pages.append({
                'page_number': page.page_number,
                'title': page.title,
                'description': page.description
            })
        return sorted(pages, key=lambda x: x['page_number'])
    
    def _export_lesson_content(self, lesson: Lesson, include_files: bool) -> List[Dict[str, Any]]:
        """Export all lesson content including quizzes."""
        content_items = []
        
        for content in sorted(lesson.content_items, key=lambda x: (x.page_number, x.order_index)):
            content_data = {
                'content_type': content.content_type,
                'title': content.title,
                'content_text': content.content_text,
                'media_url': content.media_url,
                'order_index': content.order_index,
                'page_number': content.page_number,
                'is_optional': content.is_optional,
                'is_interactive': content.is_interactive,
                'max_attempts': content.max_attempts,
                'passing_score': content.passing_score,
                'generated_by_ai': content.generated_by_ai,
                'ai_generation_details': content.ai_generation_details,
                'content_id': content.content_id,  # For kana/kanji/vocab/grammar references
                'created_at': content.created_at.isoformat() if content.created_at else None
            }
            
            # Handle file references
            if content.file_path and include_files:
                content_data['file_info'] = {
                    'file_path': content.file_path,
                    'file_size': content.file_size,
                    'file_type': content.file_type,
                    'original_filename': content.original_filename
                }
                self.exported_files.append(content.file_path)
            
            # Export quiz questions if interactive
            if content.is_interactive and content.quiz_questions:
                content_data['quiz_questions'] = self._export_quiz_questions(content.quiz_questions)
            
            content_items.append(content_data)
        
        return content_items
    
    def _export_quiz_questions(self, questions: List[QuizQuestion]) -> List[Dict[str, Any]]:
        """Export quiz questions and their options."""
        quiz_data = []
        
        for question in questions:
            question_data = {
                'question_type': question.question_type,
                'question_text': question.question_text,
                'explanation': question.explanation,
                'points': question.points,
                'order_index': question.order_index,
                'options': []
            }
            
            # Export options
            for option in sorted(question.options, key=lambda x: x.order_index):
                question_data['options'].append({
                    'option_text': option.option_text,
                    'is_correct': option.is_correct,
                    'order_index': option.order_index,
                    'feedback': option.feedback
                })
            
            quiz_data.append(question_data)
        
        return quiz_data
    
    def _export_prerequisites(self, lesson: Lesson) -> List[Dict[str, Any]]:
        """Export lesson prerequisites."""
        prerequisites = []
        for prereq in lesson.prerequisites:
            prerequisites.append({
                'prerequisite_lesson_title': prereq.prerequisite_lesson.title,
                'prerequisite_lesson_description': prereq.prerequisite_lesson.description
            })
        return prerequisites
    
    def create_export_package(self, lesson_id: int, export_path: str, include_files: bool = True) -> str:
        """
        Create a complete export package as a ZIP file.
        
        Args:
            lesson_id: ID of the lesson to export
            export_path: Directory to create the export package
            include_files: Whether to include associated files
            
        Returns:
            Path to the created ZIP file
        """
        lesson = Lesson.query.get(lesson_id)
        if not lesson:
            raise ValueError(f"Lesson with ID {lesson_id} not found")
        
        # Create export directory
        os.makedirs(export_path, exist_ok=True)
        
        # Export lesson data
        lesson_data = self.export_lesson(lesson_id, include_files)
        
        # Create safe filename
        safe_title = "".join(c for c in lesson.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"lesson_export_{safe_title}_{timestamp}.zip"
        zip_path = os.path.join(export_path, zip_filename)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add lesson JSON
            lesson_json = json.dumps(lesson_data, indent=2, ensure_ascii=False)
            zipf.writestr('lesson_data.json', lesson_json)
            
            # Add files if requested
            if include_files and self.exported_files:
                upload_folder = current_app.config['UPLOAD_FOLDER']
                for file_path in self.exported_files:
                    full_file_path = os.path.join(upload_folder, file_path)
                    if os.path.exists(full_file_path):
                        # Maintain directory structure in ZIP
                        zipf.write(full_file_path, f"files/{file_path}")
                    else:
                        current_app.logger.warning(f"File not found during export: {full_file_path}")
            
            # Add README
            readme_content = self._generate_readme(lesson_data)
            zipf.writestr('README.txt', readme_content)
        
        current_app.logger.info(f"Created export package: {zip_path}")
        return zip_path
    
    def _generate_readme(self, lesson_data: Dict[str, Any]) -> str:
        """Generate README content for export package."""
        export_metadata = lesson_data.get('export_metadata', {})
        
        readme = f"""Japanese Learning Website - Lesson Export Package

Lesson: {lesson_data['title']}
Description: {lesson_data.get('description', 'No description')}
Type: {lesson_data['lesson_type']}
Difficulty: {lesson_data.get('difficulty_level', 'Not specified')}

Export Information:
- Version: {export_metadata.get('version', 'Unknown')}
- Exported: {export_metadata.get('exported_at', 'Unknown')}
- Includes Files: {export_metadata.get('includes_files', False)}
- File Count: {export_metadata.get('file_count', 0)}

Contents:
- lesson_data.json: Complete lesson structure and content
- files/: Associated media files (if included)
- README.txt: This file

To import this lesson:
1. Use the admin interface import function
2. Or use the API endpoint with this package
3. Choose how to handle duplicate lesson titles

For technical support, refer to the system documentation.
"""
        return readme


class LessonImporter:
    """Handles importing lessons from JSON format."""
    
    def __init__(self):
        self.import_version = "1.0"
        self.imported_files = []
    
    def import_lesson(self, lesson_data: Dict[str, Any], 
                     handle_duplicates: str = 'rename',
                     import_files: bool = True,
                     files_source_path: Optional[str] = None) -> Lesson:
        """
        Import a lesson from structured data.
        
        Args:
            lesson_data: Dictionary containing lesson data
            handle_duplicates: How to handle duplicate titles ('rename', 'replace', 'skip')
            import_files: Whether to import associated files
            files_source_path: Path to source files (for ZIP imports)
            
        Returns:
            The imported Lesson object
            
        Raises:
            ValueError: For validation errors
            Exception: For import errors
        """
        try:
            # Validate import data
            self._validate_import_data(lesson_data)
            
            # Handle duplicate lesson titles
            lesson = self._handle_duplicate_lesson(lesson_data, handle_duplicates)
            
            # Import category if needed
            category = self._import_category(lesson_data.get('category'))
            if category:
                lesson.category_id = category.id
            
            db.session.add(lesson)
            db.session.flush()  # Get lesson ID
            
            # Import pages
            self._import_lesson_pages(lesson, lesson_data.get('pages', []))
            
            # Import content
            self._import_lesson_content(lesson, lesson_data.get('content', []), 
                                      import_files, files_source_path)
            
            # Import prerequisites (after all lessons are imported)
            # This might need to be handled separately for cross-lesson dependencies
            
            db.session.commit()
            current_app.logger.info(f"Successfully imported lesson: {lesson.title}")
            return lesson
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error importing lesson: {e}")
            raise
    
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
    
    def _handle_duplicate_lesson(self, lesson_data: Dict[str, Any], handle_duplicates: str) -> Lesson:
        """Handle duplicate lesson titles based on strategy."""
        title = lesson_data['title']
        existing_lesson = Lesson.query.filter_by(title=title).first()
        
        if not existing_lesson:
            # No duplicate, create new lesson
            return self._create_lesson_from_data(lesson_data)
        
        if handle_duplicates == 'skip':
            raise ValueError(f"Lesson '{title}' already exists and skip option selected")
        elif handle_duplicates == 'replace':
            # Delete existing lesson and create new one
            db.session.delete(existing_lesson)
            db.session.flush()
            return self._create_lesson_from_data(lesson_data)
        elif handle_duplicates == 'rename':
            # Find unique name
            counter = 1
            new_title = f"{title} (Imported {counter})"
            while Lesson.query.filter_by(title=new_title).first():
                counter += 1
                new_title = f"{title} (Imported {counter})"
            
            lesson_data['title'] = new_title
            return self._create_lesson_from_data(lesson_data)
        else:
            raise ValueError(f"Invalid duplicate handling strategy: {handle_duplicates}")
    
    def _create_lesson_from_data(self, lesson_data: Dict[str, Any]) -> Lesson:
        """Create a new Lesson object from import data."""
        return Lesson(
            title=lesson_data['title'],
            description=lesson_data.get('description'),
            lesson_type=lesson_data['lesson_type'],
            difficulty_level=lesson_data.get('difficulty_level'),
            estimated_duration=lesson_data.get('estimated_duration'),
            order_index=lesson_data.get('order_index', 0),
            is_published=lesson_data.get('is_published', False),
            thumbnail_url=lesson_data.get('thumbnail_url'),
            video_intro_url=lesson_data.get('video_intro_url')
        )
    
    def _import_category(self, category_data: Optional[Dict[str, Any]]) -> Optional[LessonCategory]:
        """Import or find lesson category."""
        if not category_data:
            return None
        
        # Try to find existing category
        existing_category = LessonCategory.query.filter_by(name=category_data['name']).first()
        if existing_category:
            return existing_category
        
        # Create new category
        new_category = LessonCategory(
            name=category_data['name'],
            description=category_data.get('description'),
            color_code=category_data.get('color_code', '#007bff')
        )
        db.session.add(new_category)
        db.session.flush()
        return new_category
    
    def _import_lesson_pages(self, lesson: Lesson, pages_data: List[Dict[str, Any]]) -> None:
        """Import lesson page metadata."""
        for page_data in pages_data:
            page = LessonPage(
                lesson_id=lesson.id,
                page_number=page_data['page_number'],
                title=page_data.get('title'),
                description=page_data.get('description')
            )
            db.session.add(page)
    
    def _import_lesson_content(self, lesson: Lesson, content_data: List[Dict[str, Any]], 
                             import_files: bool, files_source_path: Optional[str]) -> None:
        """Import all lesson content including quizzes."""
        for content_item in content_data:
            content = LessonContent(
                lesson_id=lesson.id,
                content_type=content_item['content_type'],
                title=content_item.get('title'),
                content_text=content_item.get('content_text'),
                media_url=content_item.get('media_url'),
                order_index=content_item['order_index'],
                page_number=content_item['page_number'],
                is_optional=content_item.get('is_optional', False),
                is_interactive=content_item.get('is_interactive', False),
                max_attempts=content_item.get('max_attempts'),
                passing_score=content_item.get('passing_score'),
                generated_by_ai=content_item.get('generated_by_ai', False),
                ai_generation_details=content_item.get('ai_generation_details'),
                content_id=content_item.get('content_id')
            )
            
            # Handle file imports
            if import_files and content_item.get('file_info') and files_source_path:
                self._import_content_file(content, content_item['file_info'], files_source_path)
            
            db.session.add(content)
            db.session.flush()  # Get content ID
            
            # Import quiz questions
            if content.is_interactive and content_item.get('quiz_questions'):
                self._import_quiz_questions(content, content_item['quiz_questions'])
    
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
        
        self.imported_files.append(file_info['file_path'])
    
    def _import_quiz_questions(self, content: LessonContent, questions_data: List[Dict[str, Any]]) -> None:
        """Import quiz questions and options."""
        for question_data in questions_data:
            question = QuizQuestion(
                lesson_content_id=content.id,
                question_type=question_data['question_type'],
                question_text=question_data['question_text'],
                explanation=question_data.get('explanation'),
                points=question_data.get('points', 1),
                order_index=question_data.get('order_index', 0)
            )
            db.session.add(question)
            db.session.flush()  # Get question ID
            
            # Import options
            for option_data in question_data.get('options', []):
                option = QuizOption(
                    question_id=question.id,
                    option_text=option_data['option_text'],
                    is_correct=option_data['is_correct'],
                    order_index=option_data.get('order_index', 0),
                    feedback=option_data.get('feedback')
                )
                db.session.add(option)
    
    def import_from_zip(self, zip_path: str, handle_duplicates: str = 'rename') -> Lesson:
        """
        Import a lesson from a ZIP export package.
        
        Args:
            zip_path: Path to the ZIP file
            handle_duplicates: How to handle duplicate titles
            
        Returns:
            The imported Lesson object
        """
        import tempfile
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Extract ZIP
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                zipf.extractall(temp_dir)
            
            # Read lesson data
            lesson_json_path = os.path.join(temp_dir, 'lesson_data.json')
            if not os.path.exists(lesson_json_path):
                raise ValueError("Invalid export package: lesson_data.json not found")
            
            with open(lesson_json_path, 'r', encoding='utf-8') as f:
                lesson_data = json.load(f)
            
            # Import lesson with files
            files_path = os.path.join(temp_dir, 'files')
            return self.import_lesson(
                lesson_data, 
                handle_duplicates=handle_duplicates,
                import_files=os.path.exists(files_path),
                files_source_path=files_path
            )
    


# Utility functions for API endpoints
def export_lesson_to_json(lesson_id: int, include_files: bool = True) -> Dict[str, Any]:
    """Convenience function for API endpoints."""
    exporter = LessonExporter()
    return exporter.export_lesson(lesson_id, include_files)


def import_lesson_from_json(lesson_data: Dict[str, Any], **kwargs) -> Lesson:
    """Convenience function for API endpoints."""
    importer = LessonImporter()
    return importer.import_lesson(lesson_data, **kwargs)


def create_lesson_export_package(lesson_id: int, export_path: str, include_files: bool = True) -> str:
    """Convenience function for creating export packages."""
    exporter = LessonExporter()
    return exporter.create_export_package(lesson_id, export_path, include_files)


def import_lesson_from_zip(zip_path: str, handle_duplicates: str = 'rename') -> Lesson:
    """Convenience function for ZIP imports."""
    importer = LessonImporter()
    return importer.import_from_zip(zip_path, handle_duplicates)
