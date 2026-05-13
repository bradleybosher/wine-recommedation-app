"""Simple in-process IP-based rate limiter used by /recommend."""
import time
from collections import defaultdict

from fastapi import HTTPException

_RATE_LIMIT_MAX = 10  # requests per window
_RATE_LIMIT_WINDOW = 60  # seconds
_rate_counts: dict[str, list[float]] = defaultdict(list)


def check_rate_limit(ip: str) -> None:
    """Raise HTTPException(429) if the IP exceeded the per-minute quota."""
    now = time.time()
    window_start = now - _RATE_LIMIT_WINDOW
    timestamps = [t for t in _rate_counts[ip] if t > window_start]
    if len(timestamps) >= _RATE_LIMIT_MAX:
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please wait before trying again.",
        )
    timestamps.append(now)
    _rate_counts[ip] = timestamps
