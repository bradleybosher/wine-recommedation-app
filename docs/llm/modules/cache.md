# cache.py

## Responsibility

SQLite-based caching, user/profile management, and persistent flight history across four tiers: (1) **users table** — JWT auth and account storage (id, email, password_hash, created_at); (2) **profiles table** — per-user named taste profiles (id, user_id, name, is_default, created_at; user_id nullable for migration); (3) **parse cache** — avoid re-running Haiku vision for the same PDF regardless of meal/profile changes; (4) **response cache** — avoid full LLM recommendation calls for identical wine_list + meal + inventory + profile combinations; (5) **flights table** — permanent per-profile history of completed recommendations, used by the `/history` route.

## Constants

**CACHE_TTL_HOURS: int = 24** — 24-hour TTL, ensures fresh recommendations within 24 hours.

**ORPHAN_PROFILE_ID: str = "00000000-0000-0000-0000-000000000001"** — Special profile_id for the legacy profile created during migration. **Imported from `bootstrap`**, not defined in this module.

## Dependencies

- `sqlite3` (built-in)
- `hashlib` (SHA256 + MD5)
- `json` (serialization)
- `uuid` (flight ID generation)
- `pathlib.Path` (file location)
- `typing.Optional`
- `models.FlightFeedback`

## Inputs/Outputs

**Inputs**: Image bytes, meal text, inventory hash, profile hash, email, password hash, profile name.

**Outputs**: Cache key (hex string), cached JSON response, user dict, profile dict, flight dict, or confirmation of cache ops.

## Key Functions

### Database Initialization

**init_db()** → None:
  - Create `users`, `profiles`, `response_cache`, `parse_cache`, `flights`, and `password_reset_tokens` tables if not exist
  - users schema: (id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, created_at REAL NOT NULL)
  - profiles schema: (id TEXT PRIMARY KEY, user_id TEXT, name TEXT NOT NULL, is_default INTEGER NOT NULL DEFAULT 0, created_at REAL NOT NULL). **No FK to users** — `user_id` is a plain nullable column.
  - response_cache schema: (key TEXT PRIMARY KEY, response TEXT, created_at REAL)
  - parse_cache schema: (pdf_hash TEXT PRIMARY KEY, wine_list_text TEXT, created_at REAL)
  - flights schema: created **without** `profile_id` (id TEXT PRIMARY KEY, created_at REAL, occasion TEXT, menu TEXT, cellar_leans TEXT, temperament TEXT, ceiling TEXT, bottle_count INTEGER, source_mode TEXT, wine_list_hash TEXT, profile_hash TEXT, response_json TEXT). `profile_id` is then added via `ALTER TABLE flights ADD COLUMN profile_id TEXT` (nullable, no FK, no NOT NULL) when `_column_exists` reports it absent.
  - password_reset_tokens schema: (token TEXT PRIMARY KEY, user_id TEXT NOT NULL, expires_at REAL NOT NULL, used INTEGER NOT NULL DEFAULT 0)
  - Indexes: `idx_profiles_user_id` on (user_id), `idx_flights_profile_id` on (profile_id)
  - Called once at app startup

**_column_exists(c: sqlite3.Connection, table: str, column: str)** → bool:
  - Helper that runs `PRAGMA table_info(table)` and reports whether `column` is present. Used by `init_db` to decide whether to `ALTER TABLE` add `profile_id`.

### User Management

**create_user(email: str, password_hash: str) → dict**:
  - INSERT user with generated UUID, provided email and password_hash, current timestamp
  - Return dict with keys: id, email, created_at

**get_user_by_email(email: str) → Optional[dict]**:
  - SELECT user by email
  - Return dict (id, email, password_hash, created_at) or None if not found

**get_user_by_id(user_id: str) → Optional[dict]**:
  - SELECT user by id
  - Return dict (id, email, password_hash, created_at) or None if not found

**count_users() → int**:
  - SELECT COUNT(*) from users
  - Return count

**update_user_password(user_id: str, password_hash: str) → None**:
  - UPDATE users SET password_hash WHERE id = user_id
  - Called by the password-reset flow after a valid reset token is consumed

### Password Reset Tokens

**create_reset_token(user_id: str, expires_in_seconds: int = 1800) → str**:
  - Generate a `secrets.token_urlsafe(32)` token, INSERT into `password_reset_tokens` with `expires_at = time.time() + expires_in_seconds` and `used = 0`
  - Returns the token string (default lifetime 30 minutes)

**get_reset_token(token: str) → Optional[dict]**:
  - SELECT by token; returns dict (token, user_id, expires_at, used: bool) or None if not found
  - Does not check expiry/used — callers validate

**mark_reset_token_used(token: str) → None**:
  - UPDATE password_reset_tokens SET used = 1 WHERE token = token (single-use enforcement)

### Profile Management

**create_profile(user_id: str, name: str, is_default: bool = False, profile_id: str | None = None) → dict**:
  - INSERT profile with provided or generated UUID, user_id, name, is_default flag, current timestamp
  - Return dict with keys: id, user_id, name, is_default, created_at

**list_profiles_for_user(user_id: str) → list[dict]**:
  - SELECT all profiles for a user, ordered by is_default DESC then created_at ASC
  - Return list of dicts (id, user_id, name, is_default, created_at)

**get_profile(profile_id: str) → Optional[dict]**:
  - SELECT profile by id
  - Return dict (id, user_id, name, is_default, created_at) or None if not found

**update_profile(profile_id: str, name: str | None = None) → Optional[dict]**:
  - If `name is None`, returns the current profile via `get_profile(profile_id)` unchanged
  - Otherwise UPDATE the name, then return the refreshed profile dict via `get_profile(profile_id)` (or None if the profile does not exist). Only `name` is mutable.

**set_default_profile(profile_id: str, user_id: str) → None**:
  - UPDATE: set is_default=0 for all of the user's profiles, then is_default=1 for the named profile (scoped to `id = ? AND user_id = ?`)
  - Returns `None`

**delete_profile(profile_id: str) → bool**:
  - Explicit `DELETE FROM flights WHERE profile_id = ?` followed by `DELETE FROM profiles WHERE id = ?` (no SQL `ON DELETE CASCADE` — the schema declares no FK), then best-effort directory removal via `shutil.rmtree(PROFILES_DIR / profile_id, ignore_errors=True)`
  - Return True if the profile row was deleted (`c.total_changes > 0`), False if not found
  - Caller must enforce ownership before invoking

**get_orphan_profile() → Optional[dict]**:
  - SELECT profile where user_id IS NULL
  - Return dict or None if no orphan exists

**claim_orphan_profile(user_id: str) → Optional[str]**:
  - SELECT orphan profile, UPDATE user_id to the provided user_id, mark is_default=1 on the orphan. **Does not** demote the user's other defaults — only the orphan row is touched.
  - Return claimed profile_id if orphan existed and was claimed, None otherwise

### Legacy Data Migration

**migrate_legacy_data() → Optional[str]**:
  - Idempotent one-shot migration detected at app startup
  - If legacy backend/profile_data.json or backend/inventory.json exist:
    - Create profiles/{ORPHAN_PROFILE_ID}/ directory
    - Move legacy files into it — `profile_data.json`, `inventory.json`, **and** `profile_data.backup.json` (each only if present)
    - Create orphan profile row (id=ORPHAN_PROFILE_ID, user_id=NULL, name="default")
    - UPDATE any flights with NULL profile_id to use ORPHAN_PROFILE_ID
    - Return ORPHAN_PROFILE_ID
  - If no legacy files, return None
  - If migration already run (files moved), no-op
  - Called once in main.py at startup

### Parse & Response Caching

**make_parse_key(pdf_bytes)** → str:
  - SHA256 of PDF bytes only — independent of meal, inventory, profile
  - Used to check parse cache before running vision extraction

**get_parse_cached(pdf_hash)** → Optional[str]:
  - SELECT wine_list_text + created_at from parse_cache
  - Same TTL eviction pattern as get_cached()
  - Returns None if not found or expired

**set_parse_cached(pdf_hash, wine_list_text)** → None:
  - INSERT OR REPLACE into parse_cache with current timestamp

**make_key(image_bytes, meal, inventory_hash, profile_hash)** → str:
  - SHA256 of concatenated bytes
  - Deterministic; same inputs → same key
  - Key components: wine list image, meal text, inventory state, profile state

**inventory_hash(bottles)** → str:
  - MD5 of JSON-sorted bottles list
  - Used to detect inventory changes

**get_cached(key)** → Optional[str]:
  - SELECT response + created_at from cache
  - If entry age exceeds CACHE_TTL_HOURS: DELETE row, return None
  - Otherwise return JSON response string

**purge_expired()** → int:
  - DELETE expired rows from both response_cache and parse_cache
  - Returns total count of deleted rows
  - Called once at app startup (after init_db)

**set_cached(key, response)** → None:
  - INSERT OR REPLACE into cache
  - Auto-record created_at timestamp

**bust_cache()** → None:
  - DELETE all entries from both response_cache and parse_cache
  - Called after inventory or profile upload

### Flight History (Per-Profile)

**save_flight(occasion: str, menu: str, cellar_leans: str, temperament: str, ceiling: str, bottle_count: int, source_mode: str, wine_list_hash: str, profile_hash: str, response: object, profile_id: str) → str**:
  - Insert completed flight into `flights` table with all metadata, response JSON, and profile_id
  - `response` is any object with `.model_dump_json()`
  - Returns UUID4 hex flight_id
  - Called automatically by `routes/recommend.py` after every successful recommendation (best-effort)
  - **Note**: `profile_id` is the **last** positional parameter (not the first)

**list_flights(profile_id: str, limit: int = 50, offset: int = 0) → list[dict]**:
  - SELECT newest-first from `flights` WHERE profile_id = ? with LIMIT/OFFSET
  - Extracts top wine name from response_json without full deserialisation
  - Returns list of dicts with keys: id, created_at, occasion, menu, top_wine_name, bottle_count
  - Requires `profile_id` as first positional argument

**get_flight(flight_id)** → Optional[dict]:
  - SELECT full row by id; returns all columns including response_json, or None if not found

**delete_flight(flight_id)** → bool:
  - DELETE by id; returns True if a row was deleted

**update_flight_feedback(flight_id, feedback: FlightFeedback)** → bool:
  - SELECT `response_json`, merge `feedback.model_dump(by_alias=True)` into the blob at key `"feedback"`, UPDATE the row
  - No new DB columns — feedback is serialised inside the existing `response_json` field
  - Returns `True` if the row was found and updated, `False` if not found

**_conn()** → sqlite3.Connection:
  - Helper to get database connection
  - Used internally by all functions

## Patterns & Gotchas

- **User/profile schema**: profiles.user_id is nullable to support the migration orphan profile (user_id=NULL) until a user claims it via `claim_orphan_profile()`.
- **Flight per-profile**: Flights are strictly scoped to profile_id. `list_flights()` requires profile_id; no global flight listing. Response/parse cache remain global (content-addressed, safe to share across profiles).
- **Orphan migration**: Legacy backend/profile_data.json + backend/inventory.json are moved into profiles/{ORPHAN_PROFILE_ID}/ during first startup. Any flights with NULL profile_id are re-assigned. This is a one-shot operation; subsequent calls to `migrate_legacy_data()` no-op.
- **Default profile**: A user can have at most one profile with is_default=1. `set_default_profile()` demotes siblings. `list_profiles_for_user()` sorts by is_default DESC to surface the default first.
- **TTL**: `CACHE_TTL_HOURS = 24` (24 hours), applied equally to both parse_cache and response_cache. `get_cached`/`get_parse_cached` lazily evict on read; `purge_expired` bulk-clears both tables at startup. `bust_cache` wipes both tables (called on inventory/profile upload).
- **Concurrency**: SQLite single-writer. If multiple requests hit at once, one may lock temporarily. Acceptable for portfolio app.
- **Cache hit**: Client receives cached JSON immediately (no LLM call).
- **INSERT OR REPLACE**: Updates if key exists, avoiding duplicates.
- **Database location**: cellar.db in backend root dir. Survives app restarts.

## Known Issues / TODOs

- No cache size management (could grow unbounded if many unique recommendations within the TTL window).
- Debug endpoint returns full environment dict (security risk in production).
- MD5 used for inventory_hash (weak, but sufficient for this use case; not cryptographic).
- Password hashing relies on caller (main.py / auth module) — no hashing done in this module.

## Testing

1. Create user via `create_user()`; verify row in DB.
2. Create profile for user; verify profile_id returned and row in DB with user_id linkage.
3. List profiles for user; verify correct order (is_default first).
4. Set default profile; verify is_default=1 on target and 0 on siblings.
5. Make /recommend request with profile_id in flights table.
6. Call `list_flights(profile_id)`; verify only flights for that profile returned.
7. Call `list_flights(other_profile_id)`; verify separate flight list.
8. Run migration with legacy files; verify orphan profile created and flights re-assigned.
9. Claim orphan via second user; verify user_id updated and is_default set.
10. Delete profile; verify the explicit `DELETE FROM flights` removes its flights and the on-disk directory is removed (no SQL CASCADE involved).
