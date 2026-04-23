# cache.py

## Responsibility

SQLite-based caching across two tiers: (1) **parse cache** — avoid re-running Haiku vision for the same PDF regardless of meal/profile changes; (2) **response cache** — avoid full LLM recommendation calls for identical wine_list + meal + inventory + profile combinations.

## Constants

**CACHE_TTL_HOURS: int = 168** — 7-day TTL, matching inventory stale threshold.

## Dependencies

- `sqlite3` (built-in)
- `hashlib` (SHA256 + MD5)
- `json` (serialization)
- `pathlib.Path` (file location)
- `typing.Optional`

## Inputs/Outputs

**Inputs**: Image bytes, meal text, inventory hash, profile hash.

**Outputs**: Cache key (hex string) or cached JSON response or confirmation of cache ops.

## Key Functions

**init_db()** → None:
  - Create `response_cache` and `parse_cache` tables if not exist
  - response_cache schema: (key TEXT PRIMARY KEY, response TEXT, created_at REAL)
  - parse_cache schema: (pdf_hash TEXT PRIMARY KEY, wine_list_text TEXT, created_at REAL)
  - Called once at app startup

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

**_conn()** → sqlite3.Connection:
  - Helper to get database connection
  - Used internally by all functions

## Patterns & Gotchas

- **Two-tier caching**: Parse cache (keyed by PDF bytes alone) sits upstream of the response cache (keyed by PDF + meal + inventory + profile). Parse cache prevents re-running Haiku even when meal or profile changes.
- **Cache key design**: Response cache includes image bytes (not just hash) to handle image changes. Inventory + profile hashes prevent stale caches when user updates cellar/taste.
- **TTL**: `CACHE_TTL_HOURS = 168` (7 days), applied equally to both tables. `get_cached`/`get_parse_cached` lazily evict on read; `purge_expired` bulk-clears both tables at startup. `bust_cache` wipes both tables (called on inventory/profile upload).
- **Concurrency**: SQLite single-writer. If multiple requests hit at once, one may lock temporarily. Acceptable for portfolio app.
- **Cache hit**: Client receives cached JSON immediately (no LLM call).
- **INSERT OR REPLACE**: Updates if key exists, avoiding duplicates.
- **Database location**: cellar.db in backend root dir. Survives app restarts.

## Known Issues / TODOs

- No cache size management (could grow unbounded if many unique recommendations within the TTL window).
- Debug endpoint returns full environment dict (security risk in production).
- MD5 used for inventory_hash (weak, but sufficient for this use case; not cryptographic).

## Testing

1. Make /recommend request with wine_list + meal.
2. Verify response cached in cellar.db.
3. Make same request again; verify response returned from cache (instant, no LLM call).
4. Upload new inventory; verify cache busted.
5. Make /recommend again; verify LLM called (cache miss).
6. Manually set created_at to an old timestamp; verify get_cached returns None and row is deleted.
7. Restart app; verify startup log shows `cache_purge_on_startup expired_entries=N`.
