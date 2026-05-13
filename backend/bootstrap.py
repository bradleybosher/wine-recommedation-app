"""Environment bootstrap. Imported first by main.py so .env values are
populated before any module that reads env vars at import time."""
import os
from pathlib import Path

from dotenv import load_dotenv

_BACKEND_DIR = Path(__file__).resolve().parent
load_dotenv(_BACKEND_DIR / ".env")
load_dotenv()

ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")

if not ANTHROPIC_API_KEY:
    raise ValueError(
        "ANTHROPIC_API_KEY environment variable is not set. Add it to backend/.env"
    )

MAX_UPLOAD_BYTES: int = 20 * 1024 * 1024  # 20 MB
