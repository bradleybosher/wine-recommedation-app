"""
logging_utils.py — Structured JSONL event logger for recommendations.

One JSON object per line in logs/recommendations.jsonl.
This module never raises to its caller; internal errors are caught and
logged through the sommelier parent logger.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from models import RecommendationResponse
from scorer import ScoringResult

# ---------------------------------------------------------------------------
# Logger setup  (singleton, file-only, raw JSON lines)
# ---------------------------------------------------------------------------

_log_dir = Path(__file__).resolve().parent / "logs"
_log_dir.mkdir(parents=True, exist_ok=True)

_logger = logging.getLogger("sommelier.recommendations")
if not _logger.handlers:
    _handler = logging.FileHandler(
        _log_dir / "recommendations.jsonl", encoding="utf-8"
    )
    _handler.setFormatter(logging.Formatter("%(message)s"))
    _logger.addHandler(_handler)
    _logger.setLevel(logging.INFO)
    _logger.propagate = False  # don't bubble to sommelier / api.log

# Fallback for internal errors (writes to the parent sommelier logger)
_fallback = logging.getLogger("sommelier.recommendations.meta")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def log_recommendation_event(
    meal: str,
    profile_hash: str,
    response: Optional[RecommendationResponse],
    scoring_result: Optional[ScoringResult],
    wine_list_hash: str,
    error: Optional[str] = None,
) -> None:
    """
    Append one JSONL line describing a recommendation attempt.

    Args:
        meal:           User's meal description.
        profile_hash:   MD5 hex of the serialised profile_data (from main.py).
        response:       RecommendationResponse on success, None on error.
        scoring_result: ScoringResult on success, None on error.
        wine_list_hash: 8-char MD5 hex of the parsed wine list text.
        error:          Error message string if the attempt failed, else None.
    """
    try:
        wines = []
        if response is not None:
            wines = [
                {
                    "rank":       r.rank,
                    "name":       r.wine_name,
                    "confidence": r.confidence,
                    "price":      r.price,
                }
                for r in response.recommendations
            ]

        event: dict = {
            "timestamp":      datetime.now(timezone.utc).isoformat(),
            "meal":           meal,
            "profile_hash":   profile_hash,
            "wine_list_hash": wine_list_hash,
            "wine_count":     len(wines),
            "wines":          wines,
            "score":          scoring_result.total if scoring_result is not None else None,
            "score_breakdown": scoring_result.breakdown if scoring_result is not None else None,
            "error":          error,
        }

        _logger.info(json.dumps(event, default=str))

    except Exception as exc:  # pragma: no cover
        _fallback.exception("log_recommendation_event failed: %s", exc)
