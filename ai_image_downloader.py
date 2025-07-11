#!/usr/bin/env python3
"""
AI Image Downloader and Integration Utility

This utility helps download AI-generated images from URLs and integrate them
with the existing file upload system. It handles image processing, validation,
and proper storage in the lesson content system.

Features:
- Download images from AI generation services
- Validate and process images using existing FileUploadHandler
- Integrate with lesson content system
- Batch processing capabilities
- Error handling and retry logic
"""

import os
import sys
import requests
import tempfile
from urllib.request import urlretrieve
from urllib.parse import urlparse
from datetime import datetime
import uuid

# Add the app directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app, db
from app.models import LessonContent
from app.utils import FileUploadHandler

class AIImageDownloader:
    """
    Utility class for downloading and processing AI-generated images.
    Integrates with the existing file upload system.
    """
    
    def __init__(self, app_context=None):
        """Initialize the image downloader."""
        if app_context:
            self.app = app_context
        else:
            self.app = create_app()
        
        with self.app.app_context():
            self.upload_folder = self.app.config.get('UPLOAD_FOLDER', 'app/static/uploads')
    
    def download_and_process_image(self, image_url, lesson_id, content_title="AI Generated Image", 
                                 description="", page_number=1, order_index=0):
        """
        Download an AI-generated image and create a lesson content entry.
        
        Args:
            image_url (str): URL of the AI-generated image
            lesson_id (int): ID of the lesson to add the image to
            content_title (str): Title for the content item
            description (str): Description of the image
            page_number (int): Page number for the content
            order_index (int): Order index for the content
            
        Returns:
            LessonContent: Created content item or None if failed
        """
        with self.app.app_context():
            try:
                print(f"Downloading image from: {image_url}")
                
                # Download image to temporary location
                temp_path = self._download_to_temp(image_url)
                if not temp_path:
                    return None
                
                # Validate and process the image
                processed_path = self._process_image(temp_path, lesson_id)
                if not processed_path:
                    self._cleanup_temp_file(temp_path)
                    return None
                
                # Get file information
                file_info = FileUploadHandler.get_file_info(
                    os.path.join(self.upload_folder, processed_path)
                )
                
                # Create lesson content entry
                content = LessonContent(
                    lesson_id=lesson_id,
                    content_type='image',
                    title=content_title,
                    content_text=description,
                    file_path=processed_path,
                    file_size=file_info.get('size', 0),
                    file_type='image',
                    original_filename=f"ai_generated_{uuid.uuid4().hex[:8]}.png",
                    page_number=page_number,
                    order_index=order_index
                )
                
                db.session.add(content)
                db.session.commit()
                
                print(f"✅ Image processed and added to lesson {lesson_id}")
                print(f"   Content ID: {content.id}")
                print(f"   File path: {processed_path}")
                print(f"   File size: {FileUploadHandler.format_file_size(file_info.get('size', 0))}")
                
                # Cleanup temporary file
                self._cleanup_temp_file(temp_path)
                
                return content
                
            except Exception as e:
                print(f"❌ Error processing image: {e}")
                return None
    
    def batch_download_images(self, image_data_list):
        """
        Download multiple images in batch.
        
        Args:
            image_data_list (list): List of dictionaries containing image data:
                - image_url: URL of the image
                - lesson_id: Lesson ID
                - content_title: Title for content
                - description: Description
                - page_number: Page number
                - order_index: Order index
                
        Returns:
            list: List of created LessonContent objects
        """
        created_content = []
        
        print(f"Starting batch download of {len(image_data_list)} images...")
        
        for i, image_data in enumerate(image_data_list, 1):
            print(f"\nProcessing image {i}/{len(image_data_list)}")
            
            content = self.download_and_process_image(
                image_url=image_data['image_url'],
                lesson_id=image_data['lesson_id'],
                content_title=image_data.get('content_title', f'AI Image {i}'),
                description=image_data.get('description', ''),
                page_number=image_data.get('page_number', 1),
                order_index=image_data.get('order_index', i-1)
            )
            
            if content:
                created_content.append(content)
            else:
                print(f"❌ Failed to process image {i}")
        
        print(f"\n✅ Batch processing complete: {len(created_content)}/{len(image_data_list)} images processed successfully")
        return created_content
    
    def _download_to_temp(self, image_url, max_retries=3):
        """Download image to temporary location with retry logic."""
        for attempt in range(max_retries):
            try:
                # Create temporary file
                temp_fd, temp_path = tempfile.mkstemp(suffix='.png', prefix='ai_image_')
                os.close(temp_fd)  # Close file descriptor, we'll use the path
                
                # Download image
                print(f"  Downloading (attempt {attempt + 1}/{max_retries})...")
                
                # Use requests for better error handling
                response = requests.get(image_url, timeout=30, stream=True)
                response.raise_for_status()
                
                # Write to temporary file
                with open(temp_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                print(f"  ✅ Downloaded to temporary file: {temp_path}")
                return temp_path
                
            except Exception as e:
                print(f"  ❌ Download attempt {attempt + 1} failed: {e}")
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                
                if attempt == max_retries - 1:
                    print(f"  ❌ All download attempts failed")
                    return None
        
        return None
    
    def _process_image(self, temp_path, lesson_id):
        """Process and validate the downloaded image."""
        try:
            # Validate file content
            if not FileUploadHandler.validate_file_content(temp_path, 'image'):
                print(f"  ❌ Image validation failed")
                return None
            
            # Process image (resize, optimize)
            if not FileUploadHandler.process_image(temp_path):
                print(f"  ❌ Image processing failed")
                return None
            
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = uuid.uuid4().hex[:8]
            filename = f"ai_generated_{timestamp}_{unique_id}.png"
            
            # Create target directory
            target_dir = os.path.join(self.upload_folder, 'lessons', 'image', f'lesson_{lesson_id}')
            os.makedirs(target_dir, exist_ok=True)
            
            # Move file to final location
            final_path = os.path.join(target_dir, filename)
            os.rename(temp_path, final_path)
            
            # Return relative path for database storage
            relative_path = os.path.join('lessons', 'image', f'lesson_{lesson_id}', filename).replace('\\', '/')
            
            print(f"  ✅ Image processed and saved: {relative_path}")
            return relative_path
            
        except Exception as e:
            print(f"  ❌ Error processing image: {e}")
            return None
    
    def _cleanup_temp_file(self, temp_path):
        """Clean up temporary file."""
        try:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)
        except Exception as e:
            print(f"Warning: Failed to cleanup temp file {temp_path}: {e}")
    
    def update_lesson_content_with_image(self, content_id, image_url, replace_existing=False):
        """
        Update existing lesson content with a new AI-generated image.
        
        Args:
            content_id (int): ID of the lesson content to update
            image_url (str): URL of the new image
            replace_existing (bool): Whether to replace existing file
            
        Returns:
            bool: True if successful, False otherwise
        """
        with self.app.app_context():
            try:
                content = LessonContent.query.get(content_id)
                if not content:
                    print(f"❌ Content with ID {content_id} not found")
                    return False
                
                # Delete existing file if replacing
                if replace_existing and content.file_path:
                    old_file_path = os.path.join(self.upload_folder, content.file_path)
                    if os.path.exists(old_file_path):
                        os.unlink(old_file_path)
                        print(f"  Deleted old file: {content.file_path}")
                
                # Download and process new image
                temp_path = self._download_to_temp(image_url)
                if not temp_path:
                    return False
                
                processed_path = self._process_image(temp_path, content.lesson_id)
                if not processed_path:
                    self._cleanup_temp_file(temp_path)
                    return False
                
                # Update content record
                file_info = FileUploadHandler.get_file_info(
                    os.path.join(self.upload_folder, processed_path)
                )
                
                content.file_path = processed_path
                content.file_size = file_info.get('size', 0)
                content.content_type = 'image'
                
                db.session.commit()
                
                print(f"✅ Content {content_id} updated with new image")
                self._cleanup_temp_file(temp_path)
                
                return True
                
            except Exception as e:
                print(f"❌ Error updating content: {e}")
                return False
    
    def get_lesson_images(self, lesson_id):
        """Get all image content for a lesson."""
        with self.app.app_context():
            images = LessonContent.query.filter_by(
                lesson_id=lesson_id,
                content_type='image'
            ).order_by(LessonContent.page_number, LessonContent.order_index).all()
            
            return images
    
    def validate_image_urls(self, urls):
        """Validate a list of image URLs."""
        valid_urls = []
        invalid_urls = []
        
        for url in urls:
            try:
                response = requests.head(url, timeout=10)
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '')
                    if content_type.startswith('image/'):
                        valid_urls.append(url)
                    else:
                        invalid_urls.append((url, f"Not an image: {content_type}"))
                else:
                    invalid_urls.append((url, f"HTTP {response.status_code}"))
            except Exception as e:
                invalid_urls.append((url, str(e)))
        
        return valid_urls, invalid_urls


def demo_image_download():
    """Demonstrate the image download functionality."""
    print("🖼️  AI Image Downloader Demo")
    print("=" * 40)
    
    downloader = AIImageDownloader()
    
    # Example: Download sample images (these would normally be AI-generated URLs)
    sample_images = [
        {
            'image_url': 'https://via.placeholder.com/1024x1024/FF6B6B/FFFFFF?text=AI+Generated+Image+1',
            'lesson_id': 1,  # Assuming lesson 1 exists
            'content_title': 'Sample AI Image 1',
            'description': 'This is a sample AI-generated image for demonstration',
            'page_number': 1,
            'order_index': 0
        },
        {
            'image_url': 'https://via.placeholder.com/1024x1024/4ECDC4/FFFFFF?text=AI+Generated+Image+2',
            'lesson_id': 1,
            'content_title': 'Sample AI Image 2',
            'description': 'Another sample AI-generated image',
            'page_number': 2,
            'order_index': 0
        }
    ]
    
    print("Note: This demo uses placeholder images since we don't have real AI-generated URLs")
    print("In practice, these URLs would come from DALL-E or other AI image generation services")
    print()
    
    # Validate URLs first
    urls = [img['image_url'] for img in sample_images]
    valid_urls, invalid_urls = downloader.validate_image_urls(urls)
    
    print(f"URL Validation Results:")
    print(f"  Valid URLs: {len(valid_urls)}")
    print(f"  Invalid URLs: {len(invalid_urls)}")
    
    if invalid_urls:
        print("  Invalid URLs:")
        for url, reason in invalid_urls:
            print(f"    - {url}: {reason}")
    
    if valid_urls:
        print(f"\nProcessing {len(valid_urls)} valid images...")
        
        # Filter to only valid images
        valid_images = [img for img in sample_images if img['image_url'] in valid_urls]
        
        # Batch download
        created_content = downloader.batch_download_images(valid_images)
        
        if created_content:
            print(f"\n✅ Successfully processed {len(created_content)} images")
            print("Created content:")
            for content in created_content:
                print(f"  - ID {content.id}: {content.title}")
                print(f"    File: {content.file_path}")
                print(f"    Page: {content.page_number}")
        else:
            print("❌ No images were successfully processed")
    else:
        print("❌ No valid image URLs found")


if __name__ == "__main__":
    print("🚀 AI Image Downloader Utility")
    print("=" * 50)
    
    # Check if we're in demo mode
    if len(sys.argv) > 1 and sys.argv[1] == 'demo':
        demo_image_download()
    else:
        print("Usage:")
        print("  python ai_image_downloader.py demo    # Run demonstration")
        print()
        print("This utility provides the following functionality:")
        print("  ✓ Download AI-generated images from URLs")
        print("  ✓ Validate and process images using FileUploadHandler")
        print("  ✓ Integrate with lesson content system")
        print("  ✓ Batch processing capabilities")
        print("  ✓ Error handling and retry logic")
        print()
        print("Example usage in code:")
        print("""
from ai_image_downloader import AIImageDownloader

downloader = AIImageDownloader()

# Download single image
content = downloader.download_and_process_image(
    image_url="https://example.com/ai-generated-image.png",
    lesson_id=1,
    content_title="AI Generated Illustration",
    description="Educational illustration for Japanese lesson"
)

# Batch download
image_data = [
    {
        'image_url': 'https://example.com/image1.png',
        'lesson_id': 1,
        'content_title': 'Image 1',
        'page_number': 1
    },
    # ... more images
]

created_content = downloader.batch_download_images(image_data)
        """)
