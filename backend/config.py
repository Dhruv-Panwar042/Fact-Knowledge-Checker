import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory for the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file if present
load_dotenv(BASE_DIR / ".env")

# Settings
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

UPLOAD_DIR = BASE_DIR / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = BASE_DIR / "data" / "knowledge_layer.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

PORT = int(os.getenv("PORT", 8000))
HOST = os.getenv("HOST", "127.0.0.1")
