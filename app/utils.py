import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app
from PIL import Image
import mimetypes
from urllib.parse import urlparse, parse_qs

def convert_to_embed_url(youtube_url):
    """
    Converts a YouTube URL to the embed format.
    Handles standard, shortened, and embed URLs.
    """
    if not youtube_url:
        return None

    # Check if it's already an embed URL
    if "youtube.com/embed/" in youtube_url:
        return youtube_url

    try:
        parsed_url = urlparse(youtube_url)
        
        if "youtube.com" in parsed_url.hostname:
            # For standard URLs like https://www.youtube.com/watch?v=...
            if parsed_url.path == "/watch":
                video_id = parse_qs(parsed_url.query).get("v")
                if video_id:
                    return f"https://www.youtube.com/embed/{video_id[0]}"
        
        elif "youtu.be" in parsed_url.hostname:
            # For shortened URLs like https://youtu.be/...
            video_id = parsed_url.path.lstrip("/")
            if video_id:
                return f"https://www.youtube.com/embed/{video_id}"

    except Exception:
        # If parsing fails, return the original URL
        return youtube_url
    
    # Return original URL if no valid format is found
    return youtube_url

class FileUploadHandler:
    @staticmethod
    def allowed_file(filename, file_type):
        """Check if file extension is allowed for the given type"""
        if '.' not in filename:
            return False
        
        extension = filename.rsplit('.', 1)[1].lower()
        allowed_extensions = current_app.config['ALLOWED_EXTENSIONS']
        
        if file_type in allowed_extensions:
            return extension in allowed_extensions[file_type]
        
        # Check all types if file_type not specified
        for extensions in allowed_extensions.values():
            if extension in extensions:
                return True
        
        return False
    
    @staticmethod
    def get_file_type(filename):
        """Determine file type based on extension"""
        if '.' not in filename:
            return None
        
        extension = filename.rsplit('.', 1)[1].lower()
        allowed_extensions = current_app.config['ALLOWED_EXTENSIONS']
        
        for file_type, extensions in allowed_extensions.items():
            if extension in extensions:
                return file_type
        
        return None
    
    @staticmethod
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
    
    @staticmethod
    def create_lesson_directory(lesson_id, file_type):
        """Create directory structure for lesson files"""
        upload_folder = current_app.config['UPLOAD_FOLDER']
        lesson_dir = os.path.join(upload_folder, 'lessons', file_type, f'lesson_{lesson_id}')
        
        os.makedirs(lesson_dir, exist_ok=True)
        return lesson_dir
    
    @staticmethod
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
            current_app.logger.error(f"File content validation (magic) failed for {file_path}: {e}")
            # Fallback to extension-based validation if magic fails, but log the failure of primary method
            return FileUploadHandler.allowed_file(os.path.basename(file_path), expected_type) # B1, B2
    
    @staticmethod
    def process_image(file_path, max_width=1920, max_height=1080):
        """Resize and optimize images. Returns True on success, False on failure."""
        try:
            with Image.open(file_path) as img:
                original_format = img.format
                # Convert to RGB if necessary (for PNG with transparency to avoid issues with JPEG)
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Create a white background image
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    # Paste the image onto the background, using alpha channel as mask if available
                    if img.mode == 'P': # Palette mode, convert to RGBA first
                        img = img.convert('RGBA')

                    mask = None
                    if img.mode == 'RGBA':
                        mask = img.split()[-1] # Get alpha channel
                    elif img.mode == 'LA': # Luminance + Alpha
                        mask = img.split()[-1]
                        img = img.convert('RGB') # Convert LA to RGB before paste, as background is RGB

                    if mask:
                         background.paste(img, (0,0), mask)
                    else: # If no mask (e.g. L mode from P without alpha)
                         background.paste(img.convert('RGB'), (0,0))
                    img = background
                elif img.mode != 'RGB': # Ensure it's RGB for JPEG saving if not already handled
                    img = img.convert('RGB')

                # Resize if necessary
                if img.width > max_width or img.height > max_height:
                    img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                
                # Save optimized image, try to preserve original format if sensible, else JPEG
                # For simplicity in this example, we'll stick to JPEG for processed images
                # but one could add logic to save as PNG if original was PNG and transparency was key.
                img.save(file_path, 'JPEG', quality=85, optimize=True)
                
                return True
        except Exception as e:
            current_app.logger.error(f"Error processing image {file_path}: {e}") # B2
            return False # B3
    
    @staticmethod
    def get_file_info(file_path):
        """Get file metadata (size, dimensions, duration, etc.)"""
        import magic
        info = {
            'size': 0,
            'mime_type': None,
            'dimensions': None,
            'duration': None
        }
        
        try:
            # File size
            info['size'] = os.path.getsize(file_path)
            
            # MIME type
            info['mime_type'] = magic.from_file(file_path, mime=True)
            
            # For images, get dimensions
            if info['mime_type'] and info['mime_type'].startswith('image/'):
                try:
                    with Image.open(file_path) as img:
                        info['dimensions'] = f"{img.width}x{img.height}"
                except Exception:
                    pass
            
            # For videos/audio, we could add duration detection here
            # This would require additional libraries like ffprobe
            
        except Exception as e:
            current_app.logger.error(f"Error getting file info for {file_path}: {e}") # B2
        
        return info
    
    @staticmethod
    def format_file_size(size_bytes):
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    @staticmethod
    def delete_file(file_path):
        """Safely delete a file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return True # Return true if file doesn't exist (idempotent)
        except Exception as e:
            current_app.logger.error(f"Error deleting file {file_path}: {e}") # B2
        
        return False
    
    @staticmethod
    def get_supported_formats(file_type):
        """Get list of supported formats for a file type"""
        allowed_extensions = current_app.config['ALLOWED_EXTENSIONS']
        if file_type in allowed_extensions:
            return list(allowed_extensions[file_type])
        return []
