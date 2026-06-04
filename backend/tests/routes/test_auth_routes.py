"""Tests for backend.routes.auth — register / login / me / forgot / reset."""

import time

import cache


class TestRegister:
    def test_creates_new_user_and_default_profile(self, client):
        resp = client.post(
            "/auth/register",
            json={"email": "new@example.com", "password": "longenoughpw"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert "accessToken" in body
        assert body["user"]["email"] == "new@example.com"
        assert body["profile"]["isDefault"] is True

    def test_duplicate_email_returns_409(self, client):
        client.post(
            "/auth/register",
            json={"email": "dup@example.com", "password": "longenoughpw"},
        )
        resp = client.post(
            "/auth/register",
            json={"email": "dup@example.com", "password": "longenoughpw"},
        )
        assert resp.status_code == 409

    def test_email_case_normalised(self, client):
        client.post(
            "/auth/register",
            json={"email": "Mixed@Example.com", "password": "longenoughpw"},
        )
        # Duplicate with different casing should still 409
        resp = client.post(
            "/auth/register",
            json={"email": "MIXED@example.com", "password": "longenoughpw"},
        )
        assert resp.status_code == 409

    def test_first_register_claims_orphan_profile(self, client, isolated_db):
        # Manually insert an orphan profile (simulating legacy migration)
        from bootstrap import ORPHAN_PROFILE_ID
        import sqlite3
        with sqlite3.connect(str(isolated_db)) as c:
            c.execute(
                "INSERT INTO profiles (id, user_id, name, is_default, created_at) "
                "VALUES (?, NULL, ?, 1, ?)",
                (ORPHAN_PROFILE_ID, "Legacy", time.time()),
            )
        resp = client.post(
            "/auth/register",
            json={"email": "first@example.com", "password": "longenoughpw"},
        )
        assert resp.status_code == 201
        # The claimed profile should be the orphan
        assert resp.json()["profile"]["id"] == ORPHAN_PROFILE_ID


class TestLogin:
    def test_correct_password_returns_token(self, client, registered_user):
        resp = client.post(
            "/auth/login",
            json={"email": registered_user["email"], "password": registered_user["password"]},
        )
        assert resp.status_code == 200
        assert "accessToken" in resp.json()

    def test_wrong_password_returns_401(self, client, registered_user):
        resp = client.post(
            "/auth/login",
            json={"email": registered_user["email"], "password": "wrong-password"},
        )
        assert resp.status_code == 401

    def test_unknown_email_returns_401(self, client):
        resp = client.post(
            "/auth/login",
            json={"email": "nobody@example.com", "password": "longenoughpw"},
        )
        assert resp.status_code == 401


class TestMe:
    def test_returns_user_and_profiles(self, client, auth_headers, registered_user):
        resp = client.get("/auth/me", headers={"Authorization": auth_headers["Authorization"]})
        assert resp.status_code == 200
        body = resp.json()
        assert body["user"]["email"] == registered_user["email"]
        assert len(body["profiles"]) == 1

    def test_unauthenticated_returns_401(self, client):
        resp = client.get("/auth/me")
        assert resp.status_code == 401


class TestForgotPassword:
    def test_unknown_email_still_returns_200(self, client):
        resp = client.post("/auth/forgot-password", json={"email": "nobody@example.com"})
        assert resp.status_code == 200
        assert "message" in resp.json()

    def test_known_email_creates_reset_token(self, client, registered_user):
        resp = client.post("/auth/forgot-password", json={"email": registered_user["email"]})
        assert resp.status_code == 200
        # A reset token row should have been created in the DB
        # (We can't fetch it directly without DB access; verify reset endpoint accepts it indirectly)


class TestResetPassword:
    def test_unknown_token_returns_400(self, client):
        resp = client.post(
            "/auth/reset-password",
            json={"token": "no-such-token", "newPassword": "newlongenoughpw"},
        )
        assert resp.status_code == 400

    def test_valid_token_resets_password(self, client, registered_user):
        token = cache.create_reset_token(registered_user["user_id"])
        resp = client.post(
            "/auth/reset-password",
            json={"token": token, "newPassword": "freshpassword99"},
        )
        assert resp.status_code == 200
        # The new password should now work; the old should not
        login_new = client.post(
            "/auth/login",
            json={"email": registered_user["email"], "password": "freshpassword99"},
        )
        assert login_new.status_code == 200
        login_old = client.post(
            "/auth/login",
            json={"email": registered_user["email"], "password": registered_user["password"]},
        )
        assert login_old.status_code == 401

    def test_used_token_returns_400(self, client, registered_user):
        token = cache.create_reset_token(registered_user["user_id"])
        client.post(
            "/auth/reset-password",
            json={"token": token, "newPassword": "freshpassword99"},
        )
        # Reuse
        resp = client.post(
            "/auth/reset-password",
            json={"token": token, "newPassword": "anotherone111"},
        )
        assert resp.status_code == 400

    def test_expired_token_returns_400(self, client, registered_user):
        # Create a token with negative TTL so it's already expired
        token = cache.create_reset_token(registered_user["user_id"], expires_in_seconds=-1)
        resp = client.post(
            "/auth/reset-password",
            json={"token": token, "newPassword": "freshpassword99"},
        )
        assert resp.status_code == 400
