import os
from werkzeug.utils import secure_filename
from flask import current_app

def allowed_file(filename):
    """
    Check if the file has an allowed extension.
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]

def save_upload_file(file_storage, title):
    """
    Secure the filename and save the uploaded file to the configured uploads folder.
    Returns: (saved_filename, absolute_file_path)
    """
    if not file_storage or not file_storage.filename:
        raise ValueError("No valid file provided")

    if not allowed_file(file_storage.filename):
        raise ValueError("File type not allowed")

    # Secure the file name
    orig_ext = file_storage.filename.rsplit('.', 1)[1].lower()
    cleaned_title = "".join(c for c in title if c.isalnum() or c in (' ', '_', '-')).strip()
    cleaned_title = cleaned_title.replace(' ', '_')
    
    # Prefix filename to ensure it is unique, and safe
    import uuid
    safe_filename = f"{uuid.uuid4().hex}_{secure_filename(cleaned_title)}.{orig_ext}"
    
    # Resolve the destination path
    upload_dir = current_app.config["UPLOAD_DIR"]
    # Ensure upload directory exists
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, safe_filename)
    
    # Save the file
    file_storage.save(file_path)
    
    return safe_filename, file_path

def delete_upload_file(file_path):
    """
    Safely delete a file if it exists.
    """
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
            return True
        except OSError:
            # Log deletion error in production
            pass
    return False
