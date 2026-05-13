# middleware.py

## Responsibility

Installs the request-logging middleware and global exception handlers on the FastAPI app. Called once from `main.py` via `install(app)`.

## Public surface

- `install(app: FastAPI) -> None` — registers:
  - `log_requests` HTTP middleware — generates `request_id` (`uuid4()[:8]`), logs `request_start` / `request_end` with method, path, IP, status, elapsed ms; sets `X-Request-ID` response header.
  - `http_exception_handler` — preserves status codes for intentional `HTTPException` (e.g. 502 from `/recommend`, 413 from uploads).
  - `unhandled_exception_handler` — catches anything else, logs with `logger.exception`, returns 500 `{"detail": "Internal server error", "error_type": ...}`.

## Patterns & Gotchas

- Uses the `sommelier.api` logger.
- The middleware re-raises after logging on exceptions so the global handler can format the response.
