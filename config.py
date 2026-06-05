import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

class Config:
    # Flask app configuration
    SECRET_KEY = os.getenv("SECRET_KEY", "meetingmind_default_secret_key_change_me_in_production")
    DEBUG = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")

    # For Vercel deployment, check if we are in serverless context and use /tmp for database and uploads
    IS_VERCEL = "VERCEL" in os.environ
    
    # SQLAlchemy config
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///meetingmind.db")
    if DATABASE_URL.startswith("sqlite:///"):
        if IS_VERCEL:
            instance_dir = Path("/tmp/instance")
        else:
            instance_dir = BASE_DIR / "instance"
        
        instance_dir.mkdir(exist_ok=True)
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{instance_dir / 'meetingmind.db'}"
    else:
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Upload configuration
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
    if IS_VERCEL:
        UPLOAD_DIR = Path("/tmp/uploads")
    else:
        UPLOAD_DIR = BASE_DIR / UPLOAD_FOLDER
        
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 16 * 1024 * 1024))  # 16 MB limit
    ALLOWED_EXTENSIONS = {
        # Audio
        "mp3", "wav", "m4a",
        # Video
        "mp4", "webm", "avi", "mov",
        # Documents
        "pdf", "txt",
        # Images
        "jpg", "jpeg", "png"
    }

    # Gemini AI configuration
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
