"""
IBVAP Backend Configuration
"""
import os
from pathlib import Path


# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = BASE_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
SAMPLE_VIDEOS_DIR = DATA_DIR / "sample_videos"
FACES_DIR = DATA_DIR / "faces"
PLATES_DIR = DATA_DIR / "plates"

# Database
DATABASE_URL = f"sqlite:///{BASE_DIR / 'ibvap.db'}"

# Server
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# Video processing
DEFAULT_FPS = int(os.getenv("DEFAULT_FPS", "15"))
FRAME_WIDTH = int(os.getenv("FRAME_WIDTH", "640"))
FRAME_HEIGHT = int(os.getenv("FRAME_HEIGHT", "480"))
JPEG_QUALITY = int(os.getenv("JPEG_QUALITY", "70"))

# CORS
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

# Ensure directories exist
for d in [DATA_DIR, SAMPLE_VIDEOS_DIR, FACES_DIR, PLATES_DIR]:
    d.mkdir(parents=True, exist_ok=True)
