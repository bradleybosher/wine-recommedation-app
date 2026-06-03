# logging_setup.py

## Responsibility

Configures the `sommelier` logger tree. Called once at startup from `main.py`.

## Public surface

- `configure_logging() -> logging.Logger` — idempotent. Sets the `sommelier` logger to `DEBUG`, then attaches a `RotatingFileHandler` (`backend/logs/api.log`, 1 MB max, 2 backups, utf-8) and a `StreamHandler` (stderr). Returns the configured root sommelier logger. Subsequent calls are no-ops if handlers already exist.

## Patterns & Gotchas

- Format: `%(asctime)s %(levelname)s [%(name)s] %(message)s`. **Only the file handler gets this formatter**; the `StreamHandler` is added with no explicit formatter and no explicit level (it inherits from the logger). Only the `sommelier` logger is set to `DEBUG` — the handlers themselves carry no level filter.
- All app code uses child loggers via `logging.getLogger("sommelier.<area>")`.
- Distinct from `logging_utils.py`, which handles recommendation-event telemetry, not generic app logging.
