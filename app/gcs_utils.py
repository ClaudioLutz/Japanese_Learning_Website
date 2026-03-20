import os
from google.cloud import storage
from flask import current_app
from werkzeug.utils import secure_filename
import uuid

def get_gcs_client():
    """Get GCS client"""
    return storage.Client()

def get_bucket_name():
    """Get GCS bucket name from config"""
    return current_app.config.get('GCS_BUCKET_NAME')

def upload_file_to_gcs(file_obj, destination_blob_name, content_type=None):
    """
    Uploads a file to the bucket.
    
    Args:
        file_obj: File object to upload
        destination_blob_name: Destination path in the bucket
        content_type: MIME type of the file
        
    Returns:
        str: Public URL of the uploaded file
    """
    try:
        storage_client = get_gcs_client()
        bucket_name = get_bucket_name()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)

        blob.upload_from_file(file_obj, content_type=content_type)
        
        # Since the bucket is public, we can construct the URL directly
        return f"https://storage.googleapis.com/{bucket_name}/{destination_blob_name}"
    except Exception as e:
        current_app.logger.error(f"Failed to upload file to GCS: {e}")
        return None

def delete_file_from_gcs(blob_name):
    """
    Deletes a blob from the bucket.
    
    Args:
        blob_name: Path of the file in the bucket
        
    Returns:
        bool: True if deleted or didn't exist, False on error
    """
    try:
        storage_client = get_gcs_client()
        bucket_name = get_bucket_name()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)

        if blob.exists():
            blob.delete()
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to delete file from GCS: {e}")
        return False

def file_exists_in_gcs(blob_name):
    """Check if file exists in GCS"""
    try:
        storage_client = get_gcs_client()
        bucket_name = get_bucket_name()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        return blob.exists()
    except Exception as e:
        current_app.logger.error(f"Failed to check file existence in GCS: {e}")
        return False
