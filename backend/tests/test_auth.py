"""Tests for backend.auth — password hashing + JWT signing/decoding."""

import time

import jwt
import pytest

import auth
from auth import (
    TokenError,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from bootstrap import JWT_ALGORITHM, JWT_SECRET


class TestPasswordHashing:
    def test_hash_verify_round_trip(self):
        h = hash_password("correct-horse-battery-staple")
        assert verify_password("correct-horse-battery-staple", h) is True

    def test_wrong_password_rejected(self):
        h = hash_password("right")
        assert verify_password("wrong", h) is False

    def test_hashes_are_salted_and_nondeterministic(self):
        assert hash_password("x") != hash_password("x")

    def test_long_password_above_bcrypt_72_byte_limit(self):
        # bcrypt truncates at 72 bytes; the SHA-256 pre-hash should let arbitrarily long
        # passwords still round-trip
        long_pw = "a" * 200
        h = hash_password(long_pw)
        assert verify_password(long_pw, h) is True
        # And changing the tail (beyond the 72-byte boundary) must still be detected
        assert verify_password("a" * 199 + "b", h) is False


class TestAccessToken:
    def test_round_trip(self):
        token = create_access_token("user-123")
        assert decode_access_token(token) == "user-123"

    def test_expired_token_raises(self):
        # Sign a token with iat/exp in the past
        payload = {"sub": "user-1", "iat": int(time.time()) - 100, "exp": int(time.time()) - 1}
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        with pytest.raises(TokenError, match="expired"):
            decode_access_token(token)

    def test_tampered_token_raises(self):
        token = create_access_token("user-1")
        tampered = token[:-4] + "xxxx"
        with pytest.raises(TokenError):
            decode_access_token(tampered)

    def test_wrong_secret_raises(self):
        token = jwt.encode(
            {"sub": "user-1", "exp": int(time.time()) + 60},
            "different-secret",
            algorithm=JWT_ALGORITHM,
        )
        with pytest.raises(TokenError):
            decode_access_token(token)

    def test_missing_subject_raises(self):
        token = jwt.encode(
            {"exp": int(time.time()) + 60},
            JWT_SECRET,
            algorithm=JWT_ALGORITHM,
        )
        with pytest.raises(TokenError, match="subject"):
            decode_access_token(token)

    def test_empty_subject_raises(self):
        token = jwt.encode(
            {"sub": "", "exp": int(time.time()) + 60},
            JWT_SECRET,
            algorithm=JWT_ALGORITHM,
        )
        with pytest.raises(TokenError, match="subject"):
            decode_access_token(token)
