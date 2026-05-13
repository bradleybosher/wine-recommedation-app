# bootstrap.py

## Responsibility

Loads `.env` and exposes process-wide configuration constants. **Must be imported before any module that reads env vars at import time** (recommender, profile, seed_profile, etc.). `main.py` imports it first for this reason.

## Public surface

- `ANTHROPIC_API_KEY: str` — read from env. Raises `ValueError` at import time if unset.
- `ANTHROPIC_MODEL: str` — defaults to `"claude-sonnet-4-6"`.
- `MAX_UPLOAD_BYTES: int = 20 * 1024 * 1024` — 20 MB upload ceiling enforced by `/upload-inventory`, `/upload-profile`, `/recommend`.

## Patterns & Gotchas

- Calls `load_dotenv()` twice: once with the explicit `backend/.env` path, once with the default search. The first call wins; the second is a safety net for `pytest` runs invoked from elsewhere.
- Fail-loud on missing API key — consistent with the project's "fail loudly" principle.
