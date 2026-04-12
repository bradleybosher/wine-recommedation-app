# cache.py

## Responsibility

SQLite-based response caching. Prevent redundant LLM calls for identical wine_list + meal + inventory + profile combinations.

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
  - Create response_cache table if not exists
  - Schema: (key TEXT PRIMARY KEY, response TEXT, created_at REAL)
  - Called once at app startup

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
  - DELETE all rows where age > CACHE_TTL_HOURS
  - Returns count of deleted rows
  - Called once at app startup (after init_db)

**set_cached(key, response)** → None:
  - INSERT OR REPLACE into cache
  - Auto-record created_at timestamp

**bust_cache()** → None:
  - DELETE all cache entries
  - Called after inventory or profile upload

**_conn()** → sqlite3.Connection:
  - Helper to get database connection
  - Used internally by all functions

## Patterns & Gotchas

- **Cache key design**: Includes image bytes (not just hash) to handle image changes. Inventory + profile hashes prevent stale caches when user updates cellar/taste.
- **TTL**: `CACHE_TTL_HOURS = 168` (7 days). `get_cached` lazily evicts expired entries on read; `purge_expired` bulk-clears at startup. `bust_cache` remains a full wipe (called on inventory/profile upload).
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
