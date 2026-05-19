# dependencies.py

## Responsibility

FastAPI dependency functions for per-request authentication and active-profile resolution. Enforces JWT bearer-token validation and links requests to the authenticated user and their selected active profile. Used as `Depends(...)` in route handlers.

## Public surface

- `get_current_user(authorization: str = Header(...)) -> User` — Extract and validate JWT bearer token from the `Authorization` header. Returns authenticated `User` object. Raises `401` (Unauthorized) if header missing, malformed, or token invalid/expired. Also raises `401` if the user_id in the token no longer exists in the database.
- `get_current_profile(x_profile_id: str = Header(alias="X-Profile-Id"), user: User = Depends(get_current_user)) -> Profile` — Resolve the active profile by `X-Profile-Id` header. Requires prior `get_current_user` (chained via `Depends`). Returns `Profile` object. Raises `400` (Bad Request) if header missing. Raises `404` (Not Found) if profile not found. Raises `403` (Forbidden) if profile not owned by the authenticated user.

## Dependencies

- `fastapi` — `Header`, `Depends`, `HTTPException`
- `auth` — `decode_access_token`, `TokenError`
- `cache` — User and profile lookup functions
- `models` — `User`, `Profile` Pydantic schemas

## Per-Request Flow

1. Client sends `Authorization: Bearer <token>` header.
2. `get_current_user` calls `auth.decode_access_token(token)` to extract user_id.
3. `get_current_user` verifies user still exists in database; raises `401` if deleted.
4. Returns `User(id=user_id, email=...)` object.
5. Downstream route optionally uses `get_current_profile` with `X-Profile-Id` header.
6. `get_current_profile` resolves profile_id and checks ownership; raises `403` if not owned.
7. Returns `Profile(id=profile_id, user_id=user_id, name=..., ...)` object.

## Patterns & Gotchas

- **Bearer token format**: Header must be `Authorization: Bearer <token>`. Missing "Bearer " prefix or whitespace-only header raises `401`.
- **Token validation**: Delegates to `auth.decode_access_token`, which raises `TokenError` on expired/malformed tokens. `get_current_user` catches and converts to `401 Unauthorized`.
- **User existence check**: Even if token valid, `get_current_user` verifies user not deleted from database; raises `401` if missing. Prevents orphaned sessions.
- **Profile ownership**: `get_current_profile` always checks `profile.user_id == user.id`; raises `403 Forbidden` if mismatch. Prevents one user accessing another's profiles.
- **Header aliases**: `X-Profile-Id` header aliased in Pydantic to avoid underscore normalization.
- **Dependency chaining**: `get_current_profile` depends on `get_current_user` via `Depends(get_current_user)`. FastAPI injects result of the first into the second. If `get_current_user` raises, the error propagates immediately; `get_current_profile` is not called.
- **No exception catching**: Both functions allow exceptions to propagate; FastAPI's exception handlers convert them to HTTP responses (via `HTTPException` or auto-conversion of `TokenError`).

## HTTP Status Codes

| Scenario | Status | Exception |
|---|---|---|
| Missing Authorization header | 401 | `HTTPException(status_code=401, detail="Missing authorization header")` |
| Malformed/invalid token | 401 | `HTTPException(status_code=401, detail="Invalid token")` |
| Expired token | 401 | `HTTPException(status_code=401, detail="Token expired")` |
| User not found in database | 401 | `HTTPException(status_code=401, detail="User not found")` |
| Missing X-Profile-Id header | 400 | `HTTPException(status_code=400, detail="Missing X-Profile-Id header")` |
| Profile not found | 404 | `HTTPException(status_code=404, detail="Profile not found")` |
| Profile not owned by user | 403 | `HTTPException(status_code=403, detail="Profile access denied")` |

## Testing

1. Call `get_current_user` without Authorization header; assert `401 Unauthorized`.
2. Call with `Authorization: Bearer invalid_token`; assert `401 Unauthorized`.
3. Call with valid token; assert `User` object returned with correct `id` and `email`.
4. Call with valid token for deleted user; assert `401 Unauthorized`.
5. Call `get_current_profile` without X-Profile-Id header; assert `400 Bad Request`.
6. Call with valid token and X-Profile-Id for owned profile; assert `Profile` object returned.
7. Call with valid token and X-Profile-Id for profile owned by different user; assert `403 Forbidden`.
8. Call with valid token and X-Profile-Id for non-existent profile; assert `404 Not Found`.
