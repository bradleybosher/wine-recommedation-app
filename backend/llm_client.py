"""
llm_client.py — Telemetry wrapper for all Anthropic messages.create() calls.

All five call sites in the codebase route through call_claude() so that
latency, token counts, model, and estimated cost are captured in a uniform
JSONL log (logs/llm_calls.jsonl) without changing call semantics.

Retry for transient API errors (connection resets, rate limits) is also
centralised here via call_with_retry, so individual call sites no longer
need their own retry logic.
"""
from __future__ import annotations

import json
import logging
import logging.handlers
import time
from pathlib import Path
from typing import Literal

import anthropic

from retry_utils import call_with_retry

# ---------------------------------------------------------------------------
# JSONL call log
# ---------------------------------------------------------------------------

_log_dir = Path(__file__).resolve().parent / "logs"
_log_dir.mkdir(parents=True, exist_ok=True)

_calls_logger = logging.getLogger("sommelier.llm.calls")
if not _calls_logger.handlers:
    _handler = logging.handlers.RotatingFileHandler(
        _log_dir / "llm_calls.jsonl", maxBytes=5_000_000, backupCount=3, encoding="utf-8"
    )
    _handler.setFormatter(logging.Formatter("%(message)s"))
    _calls_logger.addHandler(_handler)
    _calls_logger.setLevel(logging.INFO)
    _calls_logger.propagate = False

# ---------------------------------------------------------------------------
# Pricing table (USD per million tokens: input, output)
# ---------------------------------------------------------------------------

MODEL_PRICING: dict[str, tuple[float, float]] = {
    "claude-sonnet-4-6":         (3.00, 15.00),
    "claude-sonnet-4-5":         (3.00, 15.00),
    "claude-haiku-4-5-20251001": (0.80,  4.00),
    "claude-haiku-4-5":          (0.80,  4.00),
    "claude-opus-4-7":           (15.00, 75.00),
    "claude-opus-4-5":           (15.00, 75.00),
}
_DEFAULT_PRICING: tuple[float, float] = (3.00, 15.00)

Purpose = Literal[
    "recommend",
    "enrich_profile",
    "seed_profile",
    "vision_parse",
    "synthesize_palate",
]


def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    in_rate, out_rate = MODEL_PRICING.get(model, _DEFAULT_PRICING)
    return round((input_tokens * in_rate + output_tokens * out_rate) / 1_000_000, 6)


def call_claude(
    purpose: Purpose,
    client: anthropic.Anthropic,
    *,
    retryable_on: tuple = (anthropic.APIConnectionError, anthropic.RateLimitError),
    max_attempts: int = 3,
    **kwargs,
) -> anthropic.types.Message:
    """Call client.messages.create(**kwargs) with telemetry and retry.

    Args:
        purpose:      Identifier for the call site (recommend | enrich_profile | …).
        client:       Anthropic client instance.
        retryable_on: Exception types that trigger a retry (default: connection + rate-limit).
        max_attempts: Maximum retry attempts (default 3).
        **kwargs:     Forwarded verbatim to client.messages.create().

    Returns:
        The raw anthropic.types.Message response.

    Raises:
        The last exception if all retry attempts are exhausted.
        Any exception NOT in retryable_on is re-raised immediately.
    """
    model: str = str(kwargs.get("model", "unknown"))
    t0 = time.monotonic()

    response = call_with_retry(
        lambda: client.messages.create(**kwargs),
        max_attempts=max_attempts,
        retryable_on=retryable_on,
    )

    elapsed_ms = int((time.monotonic() - t0) * 1000)
    in_tokens: int = getattr(response.usage, "input_tokens", 0) or 0
    out_tokens: int = getattr(response.usage, "output_tokens", 0) or 0

    event: dict = {
        "ts": time.time(),
        "purpose": purpose,
        "model": model,
        "in_tokens": in_tokens,
        "out_tokens": out_tokens,
        "ms": elapsed_ms,
        "cost_usd": _estimate_cost(model, in_tokens, out_tokens),
    }
    _calls_logger.info(json.dumps(event))
    return response
