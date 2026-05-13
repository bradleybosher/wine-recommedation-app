"""Verify committed openapi.json matches the live FastAPI schema.

Fails if routes or models have changed without re-running sync_types.bat.
"""

import json
from pathlib import Path

import pytest


def test_openapi_schema_matches_committed():
    # Import here so conftest.py env setup runs first.
    from main import app  # noqa: PLC0415

    committed_path = Path(__file__).resolve().parent.parent / "openapi.json"
    if not committed_path.exists():
        pytest.skip("No committed openapi.json — run sync_types.bat to create it")

    live = app.openapi()
    committed = json.loads(committed_path.read_text(encoding="utf-8"))

    assert live == committed, (
        "OpenAPI schema has drifted from backend/openapi.json.\n"
        "Run sync_types.bat to regenerate the frontend client and commit the result."
    )
