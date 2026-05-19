# main.py

## Responsibility

Composition root for the FastAPI app. Wires together env bootstrap, logging, middleware, exception handlers, and the six sub-routers (auth, profiles, inventory, profile, recommend, debug, history). Contains no endpoint handlers itself — all routes live under `backend/routes/`.

Target file size: ~40 lines. If `main.py` starts growing helpers or handlers again, move them out.

## Dependencies

- `FastAPI`, `CORSMiddleware`
- `bootstrap` (env loading; **must import first**, before any module that reads env vars at import time. **Must validate `JWT_SECRET` is set** or raise `ValueError`.)
- `logging_setup.configure_logging`
- `middleware.install`
- `cache.{init_db, purge_expired, migrate_legacy_data}`
- `routes.auth.router`, `routes.profiles.router`, `routes.debug.router`, `routes.inventory.router`, `routes.profile.router`, `routes.recommend.router`, `routes.history.router`

## Inputs/Outputs

None directly — `main` exposes `app: FastAPI`. All HTTP I/O happens in the included routers.

## Startup sequence

1. `import bootstrap` — runs `load_dotenv()` and reads `ANTHROPIC_API_KEY` / `ANTHROPIC_MODEL` / **`JWT_SECRET`**. Raises `ValueError` at import time if any required key is missing.
2. `configure_logging()` — installs the rotating file handler + stderr stream on the `sommelier` logger tree.
3. `FastAPI()` + `CORSMiddleware(allow_origins=["*"], expose_headers=["X-Profile-Id"])` — exposes the profile-scoping header so the frontend can read it in responses.
4. `install_middleware(app)` — adds the request-logging middleware and HTTPException/Exception handlers from `middleware.py`.
5. `init_db()` — ensure the SQLite cache table exists.
6. `migrate_legacy_data()` — after `init_db()`, migrates any pre-auth profile data (single `profile_data.json` + `inventory.json` in `backend/`) to the first user's default profile in `backend/profiles/{user_id}/`.
7. `purge_expired()` — evict stale cache entries (logs `cache_purge_on_startup expired_entries=N`).
8. `app.include_router(...)` for `auth`, `profiles`, `debug`, `inventory`, `profile`, `recommend`, `history`.

## CORS Configuration

- `allow_origins=["*"]` — accepts all origins (suitable for portfolio demo; production should restrict).
- `expose_headers=["X-Profile-Id"]` — exposes the profile header so frontend code can read it from response headers if needed.

## Environment Variables

- **`JWT_SECRET`** (required) — 32+ character secret for signing/verifying JWT tokens. Generate with `python -c "import secrets; print(secrets.token_hex(32))"`.
- **`ANTHROPIC_API_KEY`** (required) — Anthropic API key.
- **`ANTHROPIC_MODEL`** (optional, default: `claude-sonnet-4-6`) — Model to use for recommendations and profile enrichment.

## Patterns & Gotchas

- **Import order matters.** `bootstrap` must precede every other internal import — it populates env vars that `recommender`, `profile`, etc. read at import time. `JWT_SECRET` validation happens at bootstrap import, so missing it causes immediate startup failure.
- `main.py` should not import `os`, `anthropic`, `dotenv`, or `jwt` directly; those belong in `bootstrap.py`.
- Tests import `from main import app` (see `backend/tests/test_openapi_sync.py`). Keep `app` as a module-level attribute.
- Routers register without `tags=` so the generated OpenAPI schema stays compatible with the frontend SDK generation.
- `migrate_legacy_data()` is called once at startup and moves any unscoped profile/inventory to the default profile of the "first" user (deterministic seed, not authenticated). This is a one-time migration for existing deployments; new deployments skip this safely.

## Testing

- `python -c "import main"` — must import cleanly with no `ImportError` and no double-load warnings from dotenv. Will fail if `JWT_SECRET` is not set in `.env`.
- `pytest backend/tests` — `test_openapi_sync` asserts the live schema matches `backend/openapi.json`.
- `uvicorn main:app --reload` — `/docs` should list every endpoint exposed (including auth, profiles, and history).
