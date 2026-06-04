"""Tests for backend.cache — schema + CRUD against an in-memory sqlite DB."""

import pytest

import cache


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    db = tmp_path / "schema_test.db"
    monkeypatch.setattr(cache, "DB_PATH", str(db))
    cache.init_db()
    return db


class TestUsers:
    def test_create_and_lookup_round_trip(self, isolated_db):
        user = cache.create_user(email="x@example.com", password_hash="h")
        assert cache.get_user_by_id(user["id"])["email"] == "x@example.com"
        assert cache.get_user_by_email("x@example.com")["id"] == user["id"]

    def test_unknown_lookups_return_none(self, isolated_db):
        assert cache.get_user_by_id("nope") is None
        assert cache.get_user_by_email("nope@example.com") is None

    def test_count_users(self, isolated_db):
        assert cache.count_users() == 0
        cache.create_user(email="a@example.com", password_hash="h")
        cache.create_user(email="b@example.com", password_hash="h")
        assert cache.count_users() == 2


class TestProfiles:
    def test_create_and_list(self, isolated_db):
        user = cache.create_user(email="u@example.com", password_hash="h")
        p1 = cache.create_profile(user_id=user["id"], name="One", is_default=True)
        p2 = cache.create_profile(user_id=user["id"], name="Two")
        profiles = cache.list_profiles_for_user(user["id"])
        ids = [p["id"] for p in profiles]
        assert {p1["id"], p2["id"]} == set(ids)
        # Default-first ordering
        assert profiles[0]["id"] == p1["id"]

    def test_setting_new_default_clears_previous(self, isolated_db):
        user = cache.create_user(email="u@example.com", password_hash="h")
        p1 = cache.create_profile(user_id=user["id"], name="One", is_default=True)
        p2 = cache.create_profile(user_id=user["id"], name="Two")
        cache.set_default_profile(p2["id"], user["id"])
        profiles = {p["id"]: p for p in cache.list_profiles_for_user(user["id"])}
        assert profiles[p1["id"]]["is_default"] is False
        assert profiles[p2["id"]]["is_default"] is True


class TestOrphanProfile:
    def test_claim_orphan_idempotent(self, isolated_db):
        import sqlite3
        import time

        # Insert an orphan row (user_id NULL)
        with sqlite3.connect(str(isolated_db)) as c:
            c.execute(
                "INSERT INTO profiles (id, user_id, name, is_default, created_at) "
                "VALUES (?, NULL, ?, 1, ?)",
                ("orphan-id", "Legacy", time.time()),
            )

        alice = cache.create_user(email="a@example.com", password_hash="h")
        # First claim succeeds
        claimed_id = cache.claim_orphan_profile(alice["id"])
        assert claimed_id == "orphan-id"
        # Second claim: no orphan remaining → returns None
        assert cache.claim_orphan_profile(alice["id"]) is None


class TestPasswordResetTokens:
    def test_create_and_fetch(self, isolated_db):
        user = cache.create_user(email="x@example.com", password_hash="h")
        token = cache.create_reset_token(user["id"])
        row = cache.get_reset_token(token)
        assert row["user_id"] == user["id"]
        assert row["used"] is False

    def test_mark_used_persists(self, isolated_db):
        user = cache.create_user(email="x@example.com", password_hash="h")
        token = cache.create_reset_token(user["id"])
        cache.mark_reset_token_used(token)
        assert cache.get_reset_token(token)["used"] is True

    def test_unknown_token_returns_none(self, isolated_db):
        assert cache.get_reset_token("nope") is None


class TestResponseCache:
    def test_set_get_round_trip(self, isolated_db):
        cache.set_cached("k1", '{"hello":"world"}')
        assert cache.get_cached("k1") == '{"hello":"world"}'

    def test_missing_key_returns_none(self, isolated_db):
        assert cache.get_cached("nope") is None

    def test_bust_cache_clears_all(self, isolated_db):
        cache.set_cached("k1", "v1")
        cache.set_parse_cached("h1", "wine list text")
        cache.bust_cache()
        assert cache.get_cached("k1") is None
        assert cache.get_parse_cached("h1") is None
