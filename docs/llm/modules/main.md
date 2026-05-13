# main.py

## Responsibility

Composition root for the FastAPI app. Wires together env bootstrap, logging, middleware, exception handlers, and the four sub-routers. Contains no endpoint handlers itself — all routes live under `backend/routes/`.

Target file size: ~35 lines. If `main.py` starts growing helpers or handlers again, move them out.

## Dependencies

- `FastAPI`, `CORSMiddleware`
- `bootstrap` (env loading; **must import first**, before any module that reads env vars at import time)
- `logging_setup.configure_logging`
- `middleware.install`
- `cache.init_db`, `cache.purge_expired`
- `routes.debug.router`, `routes.inventory.router`, `routes.profile.router`, `routes.recommend.router`

## Inputs/Outputs

None directly — `main` exposes `app: FastAPI`. All HTTP I/O happens in the included routers.

## Startup sequence

1. `import bootstrap` — runs `load_dotenv()` and reads `ANTHROPIC_API_KEY` / `ANTHROPIC_MODEL`. Raises `ValueError` at import time if the key is missing.
2. `configure_logging()` — installs the rotating file handler + stderr stream on the `sommelier` logger tree.
3. `FastAPI()` + `CORSMiddleware(allow_origins=["*"])`.
4. `install_middleware(app)` — adds the request-logging middleware and HTTPException/Exception handlers from `middleware.py`.
5. `init_db()` and `purge_expired()` — ensure the SQLite cache table exists and evict stale entries (logs `cache_purge_on_startup expired_entries=N`).
6. `app.include_router(...)` for `debug`, `inventory`, `profile`, `recommend`.

## Patterns & Gotchas

- **Import order matters.** `bootstrap` must precede every other internal import — it populates env vars that `recommender`, `profile`, etc. read at import time.
- `main.py` should not import `os`, `anthropic`, or `dotenv` directly; those belong in `bootstrap.py`.
- Tests import `from main import app` (see `backend/tests/test_openapi_sync.py`). Keep `app` as a module-level attribute.
- Routers register without `tags=` so the generated OpenAPI schema stays identical to the pre-refactor version (frontend SDK is unchanged).

## Testing

- `python -c "import main"` — must import cleanly with no `ImportError` and no double-load warnings from dotenv.
- `pytest backend/tests` — `test_openapi_sync` asserts the live schema matches `backend/openapi.json`.
- `uvicorn main:app --reload` — `/docs` should list every endpoint exposed before the refactor.
