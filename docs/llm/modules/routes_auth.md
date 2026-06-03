# routes/auth.py

## Responsibility

HTTP endpoints for user registration, login, and self-information retrieval. Manages user account lifecycle and JWT token issuance. Does not require `X-Profile-Id` header; self-contained to auth concerns.

## Endpoints

### POST /auth/register

**Request**:
```json
{
  "email": "user@example.com",
  "password": "plaintext_password"
}
```

**Response** (201 Created):
```json
{
  "accessToken": "eyJ0eXAi...",
  "tokenType": "bearer",
  "user": {
    "id": "uuid_string",
    "email": "user@example.com"
  },
  "profile": {
    "id": "uuid_string",
    "userId": "uuid_string",
    "name": "My Palate",
    "isDefault": true
  }
}
```

**Behaviour**:
- First-ever registration claims an orphan default profile (created at app init, unclaimed until first user registers).
- Subsequent registrations receive a fresh empty default profile named `"My Palate"`.
- Email must be unique; returns `409 Conflict` if email already registered.
- Password hashed via `auth.hash_password` before storage.
- Returns `TokenResponse` with JWT access token, authenticated user, and the new/claimed default profile.

---

### POST /auth/login

**Request**:
```json
{
  "email": "user@example.com",
  "password": "plaintext_password"
}
```

**Response** (200 OK):
```json
{
  "accessToken": "eyJ0eXAi...",
  "tokenType": "bearer",
  "user": {
    "id": "uuid_string",
    "email": "user@example.com"
  },
  "profile": {
    "id": "uuid_string",
    "userId": "uuid_string",
    "name": "My Palate",
    "isDefault": true
  }
}
```

**Behaviour**:
- Validates email + password; raises `401 Unauthorized` (detail `"Invalid email or password"`) if no match.
- Returns current default profile for the user (the `isDefault=true` profile, or the first profile if none is flagged default).
- If user has no profiles (edge case, should not occur post-register), gracefully creates a fresh default profile named `"My Palate"` rather than erroring.

---

### GET /auth/me

**Request**:
- Header: `Authorization: Bearer <token>` (required)
- No request body
- No `X-Profile-Id` header needed

**Response** (200 OK):
```json
{
  "user": {
    "id": "uuid_string",
    "email": "user@example.com"
  },
  "profiles": [
    {
      "id": "uuid1",
      "userId": "uuid_string",
      "name": "My Palate",
      "isDefault": true
    },
    {
      "id": "uuid2",
      "userId": "uuid_string",
      "name": "Alternate",
      "isDefault": false
    }
  ]
}
```

**Behaviour**:
- Requires valid Bearer token (injected via `Depends(get_current_user)`).
- Returns authenticated user and all profiles owned by that user.
- Useful for UI to populate profile selector and verify current session.
- Raises `401 Unauthorized` if token missing/invalid/expired.

---

---

### POST /auth/forgot-password

**Request**:
```json
{ "email": "user@example.com" }
```

**Response** (200 OK — always, even if email unknown):
```json
{ "message": "If that email is registered, a reset link has been logged to the server console." }
```

**Behaviour**:
- Normalises email. If user found, generates a single-use token (30-min expiry) via `cache.create_reset_token` and logs the reset URL at INFO level: `[PASSWORD RESET] <APP_BASE_URL>/reset-password?token=<token>`.
- Always returns 200 regardless of whether the email exists (prevents email enumeration).
- No email is sent; token appears only in server logs.

---

### POST /auth/reset-password

**Request**:
```json
{ "token": "<reset_token>", "newPassword": "newpass123" }
```

**Response** (200 OK):
```json
{ "message": "Password updated. You can now log in." }
```

**Errors**:

| Scenario | Status | Detail |
|---|---|---|
| Token not found | 400 | "Invalid reset token." |
| Token already used | 400 | "Reset token has already been used." |
| Token expired (>30 min) | 400 | "Reset token has expired." |

**Behaviour**:
- Fetches token row, validates not-used and not-expired.
- Re-hashes new password via `auth.hash_password`, updates user row via `cache.update_user_password`.
- Marks token used via `cache.mark_reset_token_used` (single-use enforcement).

---

## Dependencies

- `fastapi` — `APIRouter`, `Depends`, `HTTPException`, `status`
- `auth` — `hash_password`, `create_access_token`, `verify_password`
- `bootstrap` — `APP_BASE_URL`
- `cache` — `get_user_by_email`, `create_user`, `claim_orphan_profile`, `get_profile`, `create_profile`, `list_profiles_for_user`, `create_reset_token`, `get_reset_token`, `mark_reset_token_used`, `update_user_password`
- `dependencies` — `get_current_user` (for /auth/me)
- `models` — `AuthMeResponse`, `ForgotPasswordRequest`, `LoginRequest`, `MessageResponse`, `Profile`, `RegisterRequest`, `ResetPasswordRequest`, `TokenResponse`, `User`

## Patterns & Gotchas

- **Password hashing**: All passwords hashed via `auth.hash_password` (bcrypt); never stored plaintext.
- **Email uniqueness**: `cache.create_user` raises `ValueError` if email already exists; route converts to `409 Conflict`.
- **Orphan profile claim**: First registration calls `cache.claim_orphan_profile(user_id)` to claim the pre-created default profile. Subsequent registrations call `cache.create_profile(user_id, name="My Palate", is_default=True)` for a fresh profile.
- **Default profile selection**: `/login` returns the user's `isDefault=true` profile. If user has multiple profiles, only the default is returned in the login response (for UI simplicity); use `GET /auth/me` or `GET /profiles` to see all.
- **Token expiry**: Access tokens expire per `JWT_EXPIRY_DAYS` (e.g. 7 days). UI must handle token refresh by re-logging in.
- **No refresh tokens**: This implementation does not issue separate refresh tokens.
- **No email verification**: Email addresses accepted without verification; profile-ready immediately.

## Error Handling

| Scenario | Status | Detail |
|---|---|---|
| Email already registered | 409 | "Email already registered" |
| Invalid email format | 422 | Pydantic validation error |
| Password too short | 422 | Pydantic validation error (if enforced) |
| Email not found (login) | 401 | "Invalid email or password" |
| Wrong password (login) | 401 | "Invalid email or password" |
| No Authorization header (me) | 401 | "Missing authorization header" |
| Invalid/expired token (me) | 401 | "Invalid token" / "Token expired" |

## Testing

1. Register new user with email + password; verify 201 + TokenResponse returned.
2. Attempt register same email again; verify 409 Conflict.
3. Login with correct email + password; verify 200 + TokenResponse.
4. Login with wrong password; verify 401 Unauthorized.
5. Login with non-existent email; verify 401 Unauthorized.
6. Call GET /auth/me with valid token; verify user + all profiles returned.
7. Call GET /auth/me without Authorization header; verify 401 Unauthorized.
8. Call GET /auth/me with expired/malformed token; verify 401 Unauthorized.
9. Register user; verify first registration claims orphan profile.
10. Register second user; verify fresh default profile created.
