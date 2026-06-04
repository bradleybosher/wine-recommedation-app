"""Tests for backend.dependencies — get_current_user, get_current_profile."""

import time

import jwt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import cache
from auth import create_access_token
from bootstrap import JWT_ALGORITHM, JWT_SECRET
from dependencies import get_current_profile, get_current_user
from models import Profile, User


@pytest.fixture
def app(tmp_path, monkeypatch):
    """A minimal FastAPI app exposing the two deps, backed by an isolated sqlite DB."""
    db_file = tmp_path / "deps.db"
    monkeypatch.setattr(cache, "DB_PATH", str(db_file))
    cache.init_db()

    app = FastAPI()

    @app.get("/me")
    def me(user: User = Depends_user()):
        return {"id": user.id}

    @app.get("/profile-only")
    def profile_only(profile: Profile = Depends_profile()):
        return {"id": profile.id, "user_id": profile.user_id}

    return app


def Depends_user():
    from fastapi import Depends
    return Depends(get_current_user)


def Depends_profile():
    from fastapi import Depends
    return Depends(get_current_profile)


@pytest.fixture
def client(app):
    return TestClient(app)


class TestGetCurrentUser:
    def test_missing_header_returns_401(self, client):
        resp = client.get("/me")
        assert resp.status_code == 401

    def test_malformed_header_returns_401(self, client):
        resp = client.get("/me", headers={"Authorization": "NotBearer xxx"})
        assert resp.status_code == 401

    def test_invalid_token_returns_401(self, client):
        resp = client.get("/me", headers={"Authorization": "Bearer not-a-real-jwt"})
        assert resp.status_code == 401

    def test_expired_token_returns_401(self, client):
        expired = jwt.encode(
            {"sub": "u1", "exp": int(time.time()) - 1},
            JWT_SECRET,
            algorithm=JWT_ALGORITHM,
        )
        resp = client.get("/me", headers={"Authorization": f"Bearer {expired}"})
        assert resp.status_code == 401

    def test_unknown_user_id_returns_401(self, client):
        # Valid JWT for a user that doesn't exist in the DB
        token = create_access_token("ghost-user-id")
        resp = client.get("/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401

    def test_valid_token_returns_user(self, client):
        user = cache.create_user(email="x@example.com", password_hash="hashed")
        token = create_access_token(user["id"])
        resp = client.get("/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["id"] == user["id"]


class TestGetCurrentProfile:
    def test_missing_profile_id_header_returns_400(self, client):
        user = cache.create_user(email="x@example.com", password_hash="hashed")
        token = create_access_token(user["id"])
        resp = client.get("/profile-only", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 400

    def test_unknown_profile_id_returns_404(self, client):
        user = cache.create_user(email="x@example.com", password_hash="hashed")
        token = create_access_token(user["id"])
        resp = client.get(
            "/profile-only",
            headers={"Authorization": f"Bearer {token}", "X-Profile-Id": "no-such-profile"},
        )
        assert resp.status_code == 404

    def test_cross_user_ownership_returns_403(self, client):
        alice = cache.create_user(email="alice@example.com", password_hash="h")
        bob = cache.create_user(email="bob@example.com", password_hash="h")
        bobs_profile = cache.create_profile(user_id=bob["id"], name="Bob", is_default=True)
        alice_token = create_access_token(alice["id"])
        resp = client.get(
            "/profile-only",
            headers={
                "Authorization": f"Bearer {alice_token}",
                "X-Profile-Id": bobs_profile["id"],
            },
        )
        assert resp.status_code == 403

    def test_owned_profile_succeeds(self, client):
        alice = cache.create_user(email="a@example.com", password_hash="h")
        alices_profile = cache.create_profile(user_id=alice["id"], name="Alice", is_default=True)
        token = create_access_token(alice["id"])
        resp = client.get(
            "/profile-only",
            headers={"Authorization": f"Bearer {token}", "X-Profile-Id": alices_profile["id"]},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == alices_profile["id"]
        assert body["user_id"] == alice["id"]
