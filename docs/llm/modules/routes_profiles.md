# routes/profiles.py

## Responsibility

HTTP CRUD endpoints for user profiles. Allows listing, creating, renaming, promoting to default, and deleting profiles. All endpoints require JWT bearer token for authentication. Profiles are not multi-tenant; they must be owned by the authenticated user. Do NOT require `X-Profile-Id` header on these routes since they operate on profiles via path params.

## Endpoints

### GET /profiles

**Request**:
- Header: `Authorization: Bearer <token>` (required)
- No path or query params

**Response** (200 OK):
```json
[
  {
    "id": "uuid1",
    "userId": "uuid_string",
    "name": "Default",
    "isDefault": true
  },
  {
    "id": "uuid2",
    "userId": "uuid_string",
    "name": "Vacation Wines",
    "isDefault": false
  }
]
```

**Behaviour**:
- Returns all profiles owned by the authenticated user.
- Sorted by creation order (oldest first) or by `isDefault` (default first).
- At least one profile always exists (the orphan default created at app init, claimed on first user registration).
- Raises `401 Unauthorized` if token missing/invalid.

---

### POST /profiles

**Request**:
```json
{
  "name": "My Custom Profile"
}
```

**Response** (201 Created):
```json
{
  "id": "uuid_new",
  "userId": "uuid_string",
  "name": "My Custom Profile",
  "isDefault": false
}
```

**Behaviour**:
- Creates a new profile for the authenticated user.
- New profile is NOT marked default unless the user had no profiles before (edge case).
- Raises `401 Unauthorized` if token missing/invalid.
- Raises `422 Unprocessable Entity` if `name` missing or empty.

---

### PATCH /profiles/{profile_id}

**Request**:
```json
{
  "name": "Renamed Profile",
  "isDefault": true
}
```

(Both fields optional; omitted fields are not updated.)

**Response** (200 OK):
```json
{
  "id": "uuid",
  "userId": "uuid_string",
  "name": "Renamed Profile",
  "isDefault": true
}
```

**Behaviour**:
- Rename the profile if `name` provided.
- Promote the profile to default if `isDefault: true` provided. If set to true, automatically demotes the previous default profile to `isDefault: false`.
- Does not allow ownership transfer (profile remains owned by current user).
- Raises `401 Unauthorized` if token missing/invalid.
- Raises `403 Forbidden` if profile not owned by authenticated user.
- Raises `404 Not Found` if profile_id does not exist.
- Raises `409 Conflict` if attempting to set `isDefault: false` on the only profile with `isDefault: true` (at least one default must exist at all times).

---

### DELETE /profiles/{profile_id}

**Request**:
- Header: `Authorization: Bearer <token>` (required)
- No request body

**Response** (200 OK):
```json
{
  "message": "Profile deleted successfully"
}
```

**Behaviour**:
- Deletes the profile and cascades to:
  - All flights associated with the profile
  - All files (wine list PDFs, inventory exports, etc.) stored in the profile's directory
- Raises `401 Unauthorized` if token missing/invalid.
- Raises `403 Forbidden` if profile not owned by authenticated user.
- Raises `404 Not Found` if profile_id does not exist.
- Raises `409 Conflict` if attempting to delete the only remaining profile (user must have at least one profile).
- **Auto-promotion**: If the deleted profile was marked `isDefault: true`, automatically promotes the next remaining profile to default. If only one profile remains after deletion, that becomes default.

---

## Dependencies

- `fastapi` — `APIRouter`, `HTTPException`, `Depends`, `Path`
- `dependencies` — `get_current_user` (JWT validation on all routes)
- `cache` — Database functions: `list_user_profiles`, `create_profile`, `get_profile`, `update_profile`, `delete_profile`, `list_user_profiles` (again, for default promotion)
- `models` — `User`, `Profile`, `ProfilePatch` (request schema)

## Patterns & Gotchas

- **Ownership enforcement**: Every route checks `profile.user_id == user.id` before allowing mutation; raises `403 Forbidden` if mismatch.
- **Default profile invariant**: At least one profile must have `isDefault: true` at all times. Routes enforce this by:
  - Refusing DELETE on the only default profile.
  - Refusing PATCH to set `isDefault: false` if it's the only default.
  - Auto-promoting the next profile to default when the current default is deleted.
- **Cascade delete**: DELETE cascades to flights and file system directory. Unrecoverable; no soft delete.
- **No X-Profile-Id header**: These routes don't read/require the header. They operate on profiles via path params. The header is used by recommendation/inventory routes to select the "active" profile for a request.
- **Rename anywhere**: No restrictions on renaming profiles; profile name is free-form.
- **Empty name**: Pydantic validation should reject empty `name` strings (add `min_length=1` if not already present).

## Error Handling

| Scenario | Status | Detail |
|---|---|---|
| No Authorization header | 401 | "Missing authorization header" |
| Invalid/expired token | 401 | "Invalid token" / "Token expired" |
| Profile not owned by user | 403 | "Profile access denied" |
| Profile not found | 404 | "Profile not found" |
| Delete only profile | 409 | "Cannot delete the only profile" |
| Demote only default | 409 | "At least one profile must be default" |
| Empty name in POST/PATCH | 422 | Pydantic validation error |
| Missing name in POST | 422 | Pydantic validation error |

## Testing

1. Create user A with a default profile.
2. GET /profiles for user A; verify 1 profile returned, `isDefault: true`.
3. POST /profiles with name "Custom"; verify 201 + new profile, `isDefault: false`.
4. PATCH /profiles/{custom_id} with `{"isDefault": true}`; verify old default is now false, new is true.
5. PATCH /profiles/{default_id} with `{"name": "Renamed Default"}`; verify name changed.
6. Attempt DELETE the only default profile; verify 409 Conflict.
7. Attempt DELETE a profile not owned by user A (e.g. created by user B); verify 403 Forbidden (or 404 if user B's profile not visible).
8. DELETE a non-default profile; verify 200 + profile gone.
9. DELETE the current default profile (when >1 profiles exist); verify 200 + next profile auto-promoted to default.
10. Create second user B; GET /profiles; verify isolated from user A's profiles.
