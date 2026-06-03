# routes/debug.py

## Responsibility

Operational debug, monitoring, and diagnostics endpoints. All routes are mounted under the `/debug` prefix (`APIRouter(prefix="/debug", tags=["debug"])`). Most endpoints are unauthenticated health/diagnostics probes; a few that expose per-profile or shared mutable state require auth. No LLM calls are made except indirectly via reading the telemetry log file.

## Authentication

Auth requirements vary per endpoint (unlike the other route modules, which are uniformly authenticated):

- **No auth**: `/health`, `/cache/stats`, `/config`, `/logs/recent`, `/endpoints`, `/memory`, `/ping`, `/version`. These handlers declare no auth dependency, so they require neither a Bearer JWT nor an `X-Profile-Id` header.
- **`Depends(get_current_profile)`** (Bearer JWT + `X-Profile-Id`): `/status` — reports inventory/profile stats for the active profile.
- **`Depends(get_current_user)`** (Bearer JWT only, no profile header): `/cache/clear`, `/stats`.

## Endpoints

**GET /debug/health** → `dict` (no auth)
  - Basic liveness probe. Returns `{"status": "healthy", "timestamp", "service": "sommelier-api", "version": "1.0.0"}`.

**GET /debug/status** → `dict` (auth: `get_current_profile`)
  - Comprehensive status overview for the active profile. Aggregates inventory stats (`has_inventory`, `bottle_count`, `age_hours`, `stale`) via `inventory.load_inventory(profile.id)`, profile stats (`has_profile`, `profile_keys`) via `profile.load_profile_data(profile.id)`, cache stats (`get_cache_stats`), and system info (Python version, platform, cwd, `ANTHROPIC_API_KEY_SET`, `ANTHROPIC_MODEL`).

**GET /debug/cache/stats** → `dict` (no auth)
  - Returns response-cache statistics via `get_cache_stats()`: `total_entries`, `oldest_entry_hours`, `newest_entry_hours`, `total_size_bytes`, `total_size_kb`, `database_path`. Errors are caught and returned as an `error` field rather than raising.

**POST /debug/cache/clear** → `dict` (auth: `get_current_user`)
  - Clears all cached responses via `cache.bust_cache()` (affects the shared `response_cache` + `parse_cache`, which are global/content-addressed). Returns `{"status": "cache_cleared", "timestamp", "message"}`.

**GET /debug/config** → `dict` (no auth)
  - Returns current configuration: `anthropic_model` (env, default `claude-sonnet-4-6`) and `anthropic_api_key_set` (bool).

**GET /debug/logs/recent** → `dict` (no auth)
  - Query param: `limit` (default 50). Returns the last `limit` lines of `backend/logs/api.log` as `recent_lines`, plus `log_file` and `total_lines`. Returns an `error` field if the log file is missing or unreadable.

**GET /debug/endpoints** → `dict` (no auth)
  - Introspects `request.app.routes` and returns every registered route's `path`, `name`, and `methods`, plus a `count`.

**GET /debug/memory** → `dict` (no auth)
  - Returns process memory usage (`rss_bytes`, `vms_bytes`, `percent`, `available_memory`, `total_memory`) via `psutil`. If `psutil` is not installed, returns `{"error", "message", "psutil_available": false}` instead of raising.

**GET /debug/ping** → `dict` (no auth)
  - Simple connectivity probe. Returns `{"message": "pong", "timestamp"}`.

**GET /debug/stats** → `dict` (auth: `get_current_user`)
  - Aggregate LLM telemetry read from `backend/logs/llm_calls.jsonl`. Groups rows by `purpose`, computing per-purpose `calls`, `p50_ms`, `p90_ms`, `total_in_tokens`, `total_out_tokens`, `total_cost_usd`. Also reports today's call count/cost/token totals and all-time cost. Returns `{"error": ..., "rows": 0}` if the log file does not exist yet.

**GET /debug/version** → `dict` (no auth)
  - Returns API/runtime version info: `api` (`1.0.0`), `python`, `platform`, and `pyproject_toml` (bool — whether `pyproject.toml` is present).

## Helpers

- **`get_cache_stats() → dict`** — module-level (not an endpoint). Queries the `response_cache` table directly via `cache._conn()` for entry count, oldest/newest age in hours, and total byte size. Catches all exceptions and returns an `error` field with a zeroed payload so the diagnostics endpoints never 500.

## Dependencies

- `fastapi` — `APIRouter`, `Depends`, `Request`; `fastapi.responses.JSONResponse`
- `cache` — `bust_cache`, `_conn`
- `dependencies` — `get_current_profile`, `get_current_user`
- `inventory.load_inventory`
- `models` — `Profile`, `User`
- `profile.load_profile_data`
- Standard library — `json`, `logging`, `os`, `sys`, `time`, `pathlib.Path`
- `psutil` — optional, imported lazily inside `/debug/memory`; absence is handled gracefully

## Patterns & Gotchas

- **Mixed auth model**: Unlike the other route modules, `/debug` endpoints are individually authenticated via per-handler `Depends`. Most (e.g. `/health`, `/ping`) declare no auth dependency at all; `/status` (profile-scoped) and `/cache/clear` + `/stats` (user-scoped) require credentials. `/debug/health` and `/debug/ping` are also called out in `CLAUDE.md` as not requiring `X-Profile-Id`.
- **Fail-soft diagnostics**: `get_cache_stats`, `/logs/recent`, and `/memory` catch their own exceptions and return an `error` field rather than raising — diagnostics should not themselves 500.
- **Telemetry source**: `/stats` reads the JSONL telemetry log written by `llm_client.call_claude` (`backend/logs/llm_calls.jsonl`); `/logs/recent` reads the rolling text log (`backend/logs/api.log`).
- **Direct DB access**: `get_cache_stats` uses `cache._conn()` (a private helper) to query `response_cache` directly rather than going through a public cache function.
