"""Pytest configuration and fixtures for backend tests."""

import os
import sys
from pathlib import Path

# Add backend directory to Python path so imports work
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Provide a dummy key so modules that validate ANTHROPIC_API_KEY at import time
# don't raise RuntimeError during test collection.
os.environ.setdefault("ANTHROPIC_API_KEY", "test-dummy-key-for-pytest")
