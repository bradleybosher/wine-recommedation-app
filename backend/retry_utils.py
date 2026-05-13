"""Shared retry helper for Anthropic API calls."""

import logging
import time

logger = logging.getLogger("sommelier.retry")

_DEFAULT_MAX_ATTEMPTS = 3
_DEFAULT_BACKOFF_BASE = 1.5  # seconds; delay = base ** attempt


def call_with_retry(fn, *, max_attempts: int = _DEFAULT_MAX_ATTEMPTS, retryable_on: tuple = (Exception,)):
    """Call fn() and retry up to max_attempts times on retryable exceptions.

    Args:
        fn: A zero-argument callable. Called up to max_attempts times.
        max_attempts: Maximum number of attempts (including first).
        retryable_on: Tuple of exception types that trigger a retry.

    Returns:
        The return value of fn() on success.

    Raises:
        The last exception from fn() if all attempts fail.
        Any exception NOT in retryable_on is re-raised immediately.
    """
    last_exc: Exception = RuntimeError("no attempts made")
    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except retryable_on as exc:
            last_exc = exc
            if attempt < max_attempts:
                delay = _DEFAULT_BACKOFF_BASE ** attempt
                logger.warning(
                    "retry attempt=%d/%d failed (%s: %s) — retrying in %.1fs",
                    attempt, max_attempts, type(exc).__name__, exc, delay,
                )
                time.sleep(delay)
            else:
                logger.error(
                    "retry all %d attempts failed, last_error=%s: %s",
                    max_attempts, type(exc).__name__, exc,
                )
    raise last_exc
