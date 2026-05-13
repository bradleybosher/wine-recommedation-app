# logging_setup.py

## Responsibility

Configures the `sommelier` logger tree. Called once at startup from `main.py`.

## Public surface

- `configure_logging() -> logging.Logger` — idempotent. Attaches a `RotatingFileHandler` (`backend/logs/api.log`, 1 MB max, 2 backups, utf-8) and a stderr `StreamHandler` at `DEBUG`. Returns the configured root sommelier logger. Subsequent calls are no-ops if handlers already exist.

## Patterns & Gotchas

- Format: `%(asctime)s %(levelname)s [%(name)s] %(message)s`.
- All app code uses child loggers via `logging.getLogger("sommelier.<area>")`.
- Distinct from `logging_utils.py`, which handles recommendation-event telemetry, not generic app logging.
