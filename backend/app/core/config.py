"""
DRISHTI Backend Configuration
"""
import os
from pathlib import Path

# Load .env before anything reads os.getenv(). Optional dependency: a fresh
# clone without python-dotenv still boots, it just ignores .env files.
#
# override=True so an edited .env wins over a value already in the environment:
# with override=False a rotated SMTP app password was silently ignored, because
# the stale value was loaded at first import and never replaced. Note this
# still only takes effect on restart - nothing re-reads .env mid-process.
try:
    from dotenv import load_dotenv
    _here = Path(__file__).resolve()
    for _candidate in (_here.parent.parent.parent / ".env",        # backend/.env
                       _here.parent.parent.parent.parent / ".env"):  # repo root
        if _candidate.exists():
            load_dotenv(_candidate, override=True)
except ImportError:
    pass


# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = BASE_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
SAMPLE_VIDEOS_DIR = DATA_DIR / "sample_videos"
FACES_DIR = DATA_DIR / "faces"
PLATES_DIR = DATA_DIR / "plates"
DEMO_VIDEOS_DIR = BASE_DIR / "demo_videos"   # canned clips shipped for the demo

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
for d in [DATA_DIR, SAMPLE_VIDEOS_DIR, FACES_DIR, PLATES_DIR, DEMO_VIDEOS_DIR]:
    d.mkdir(parents=True, exist_ok=True)
