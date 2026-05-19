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

TEST_MODE: bool = os.getenv("TEST_MODE", "false").lower() == "true"

JWT_SECRET: str = os.getenv("JWT_SECRET", "")
JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRY_DAYS: int = int(os.getenv("JWT_EXPIRY_DAYS", "7"))

if not JWT_SECRET:
    raise ValueError(
        "JWT_SECRET environment variable is not set. Generate one with "
        "`python -c \"import secrets; print(secrets.token_hex(32))\"` and add it to backend/.env"
    )

PROFILES_DIR: Path = _BACKEND_DIR / "profiles"
PROFILES_DIR.mkdir(exist_ok=True)

ORPHAN_PROFILE_ID: str = "00000000-0000-0000-0000-000000000001"
