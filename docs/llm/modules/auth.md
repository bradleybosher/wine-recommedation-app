# auth.py

## Responsibility

Pure password hashing and JWT token utilities for user authentication. Kept free of FastAPI imports to enable unit-testability and CLI reuse. Implements bcrypt-based password hashing and HS256 JWT signing/verification.

## Public surface

- `hash_password(plaintext: str) -> str` — Hash a plaintext password using bcrypt; returns salted hash string. Used at registration time.
- `verify_password(plaintext: str, password_hash: str) -> bool` — Verify plaintext against stored hash; returns True if match, False otherwise.
- `create_access_token(user_id: str) -> str` — Create signed JWT token with `sub` (user_id), `iat` (issued-at), and `exp` (expiry) claims. Returns token string.
- `decode_access_token(token: str) -> str` — Decode and verify JWT token; returns the `sub` (user_id) claim. Raises `TokenError` if token invalid, expired, or malformed.
- `TokenError` exception — Raised by `decode_access_token` on invalid/expired tokens. Allows distinction from other exceptions (e.g. missing token header).

## Dependencies

- `passlib[bcrypt]` — bcrypt hashing (PBKDF2 configured for production)
- `jwt` (PyJWT) — HS256 token signing/verification
- `datetime` (standard library) — Token expiry calculation
- `bootstrap` — Reads `JWT_SECRET`, `JWT_ALGORITHM`, `JWT_EXPIRY_DAYS` at import time

## Token Payload Structure

```json
{
  "sub": "user_id_string",
  "iat": 1234567890,
  "exp": 1234654290
}
```

- `sub` — Subject claim; the user_id that authenticated the token
- `iat` — Issued-at timestamp (seconds since epoch)
- `exp` — Expiry timestamp (calculated as `iat + JWT_EXPIRY_DAYS * 86400`)

## Patterns & Gotchas

- **FastAPI-free**: No `from fastapi import ...` in this module. All HTTP concerns (status codes, headers) live in `dependencies.py` and route handlers.
- **Fail-loud on import**: `create_access_token` and `decode_access_token` both read `JWT_SECRET`, `JWT_ALGORITHM`, and `JWT_EXPIRY_DAYS` from `bootstrap` at import time; will raise `ValueError` if any env var is unset.
- **Token expiry**: Tokens expire after `JWT_EXPIRY_DAYS` (read from `.env`, default typically 7 days). `decode_access_token` raises `TokenError` on expired tokens.
- **Algorithm**: Hardcoded to HS256 (HMAC SHA-256). Stored in `JWT_ALGORITHM` for consistency with PyJWT; must match `.env`.
- **No refresh tokens**: This implementation does not issue refresh tokens; expired tokens are invalid. UI must ask user to log in again.
- **Exception semantics**: `TokenError` is a custom exception; callers can catch it specifically to distinguish missing/invalid tokens from other errors (e.g. database connection failures).

## Testing

1. Hash a password; verify hash differs on each call (salt is random).
2. `verify_password(plaintext, hash)` returns True for correct plaintext, False for wrong.
3. Create token for user_id "alice"; decode it back and assert `sub == "alice"`.
4. Create token; manually advance time past expiry; assert `decode_access_token` raises `TokenError`.
5. Decode malformed token (e.g. "invalid.data"); assert `TokenError` raised.
6. Unset `JWT_SECRET` in env; reload module; assert import-time `ValueError`.
