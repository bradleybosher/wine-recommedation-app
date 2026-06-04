"""Shared fixtures for route-level tests.

Pattern: each test gets an isolated sqlite DB + profiles dir via monkeypatch,
so route handlers behave normally without touching the real backend/cellar.db
or backend/profiles/. The main FastAPI app is imported once (module cached).
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import bootstrap
import cache


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    """Redirect cache.DB_PATH to a per-test sqlite file and init schema.

    Also patches any module that captured DB_PATH via `from cache import DB_PATH`,
    since those bindings are frozen at import time and don't track the original.
    """
    db_file = tmp_path / "test_cellar.db"
    monkeypatch.setattr(cache, "DB_PATH", str(db_file))
    try:
        import insights as insights_module
        monkeypatch.setattr(insights_module, "DB_PATH", str(db_file), raising=False)
    except ImportError:
        pass
    cache.init_db()
    return db_file


@pytest.fixture
def isolated_profiles_dir(tmp_path, monkeypatch):
    """Redirect PROFILES_DIR (used by cache + profile + inventory modules) to a tmp dir.

    The constant is imported by multiple modules at import time, so we patch the
    *re-exported* reference inside each consumer module that we care about.
    """
    new_dir = tmp_path / "profiles"
    new_dir.mkdir()
    monkeypatch.setattr(bootstrap, "PROFILES_DIR", new_dir)
    monkeypatch.setattr(cache, "PROFILES_DIR", new_dir, raising=False)
    # profile.py / inventory.py reference PROFILES_DIR via `from bootstrap import PROFILES_DIR`
    try:
        import profile as profile_module
        monkeypatch.setattr(profile_module, "PROFILES_DIR", new_dir, raising=False)
    except ImportError:
        pass
    try:
        import inventory as inventory_module
        monkeypatch.setattr(inventory_module, "PROFILES_DIR", new_dir, raising=False)
    except ImportError:
        pass
    return new_dir


@pytest.fixture
def client(isolated_db, isolated_profiles_dir):
    """A FastAPI TestClient bound to the isolated DB + profiles dir."""
    from main import app  # noqa: PLC0415 — import after env setup
    return TestClient(app)


@pytest.fixture
def registered_user(client):
    """Register a user and return {email, password, token, profile_id, user_id}."""
    payload = {"email": "alice@example.com", "password": "correct-horse"}
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    return {
        "email": payload["email"],
        "password": payload["password"],
        "token": body["accessToken"],
        "profile_id": body["profile"]["id"],
        "user_id": body["user"]["id"],
    }


@pytest.fixture
def auth_headers(registered_user):
    """Convenience: {Authorization, X-Profile-Id} headers for the registered user."""
    return {
        "Authorization": f"Bearer {registered_user['token']}",
        "X-Profile-Id": registered_user["profile_id"],
    }
