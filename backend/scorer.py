"""
scorer.py — Recommendation quality scoring engine.

Scores a RecommendationResponse on four dimensions and returns a composite
float in [0.0, 1.0].  Pure function; no side effects; never raises.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Optional

from models import RecommendationResponse, TasteProfile

# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------

@dataclass
class ScoringResult:
    """Immutable scoring result."""
    total: float
    breakdown: Dict[str, float] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Dimension weights
# ---------------------------------------------------------------------------

_WEIGHTS: Dict[str, float] = {
    "confidence":   0.30,
    "completeness": 0.20,
    "grounding":    0.30,
    "budget_fit":   0.20,
}

_CONFIDENCE_MAP: Dict[str, float] = {
    "high":   1.00,
    "medium": 0.67,
    "low":    0.33,
}

_TARGET_RECS = 3


# ---------------------------------------------------------------------------
# Individual dimension scorers
# ---------------------------------------------------------------------------

def _normalize_confidence_level(raw_confidence: str) -> str:
    """Extract normalized confidence level from raw LLM text."""
    normalized = (raw_confidence or "").lower().strip()
    for level in _CONFIDENCE_MAP:
        if normalized.startswith(level):
            return level
    return normalized


def _score_confidence(response: RecommendationResponse) -> float:
    """Average mapped confidence across all recommendations."""
    recs = response.recommendations
    if not recs:
        return 0.0
    scores = [_CONFIDENCE_MAP.get(_normalize_confidence_level(r.confidence), 0.5) for r in recs]
    return sum(scores) / len(scores)


def _score_completeness(response: RecommendationResponse) -> float:
    """Fraction of target recommendation count received."""
    return min(len(response.recommendations) / _TARGET_RECS, 1.0)


def _wine_in_list(wine_name: str, wine_list_text: str) -> bool:
    """Return True if wine_name is plausibly present in wine_list_text."""
    if not wine_name or not wine_list_text:
        return False

    # Fast path: case-insensitive substring
    if wine_name.lower() in wine_list_text.lower():
        return True

    # Fuzzy: ≥75% of significant tokens from wine_name appear in the list
    tokens = [t.lower() for t in re.findall(r'\b[a-zA-Z]{3,}\b', wine_name)]
    if not tokens:
        return False
    list_tokens = set(re.findall(r'\b[a-zA-Z]{3,}\b', wine_list_text.lower()))
    matched = sum(1 for t in tokens if t in list_tokens)
    return (matched / len(tokens)) >= 0.75


def _score_grounding(response: RecommendationResponse, wine_list_text: str) -> float:
    """Fraction of recommended wines found in the wine list text."""
    recs = response.recommendations
    if not recs:
        return 0.5  # neutral: nothing to ground
    if not wine_list_text:
        return 0.5  # neutral: cannot assess

    hits = sum(1 for r in recs if _wine_in_list(r.wine_name, wine_list_text))
    return hits / len(recs)


def _score_budget_fit(
    response: RecommendationResponse,
    profile: Optional[TasteProfile],
) -> float:
    """Fraction of priced recommendations within the user's budget (±20%)."""
    if profile is None:
        return 0.5

    budget_min = profile.budget_min
    budget_max = profile.budget_max
    if budget_min is None or budget_max is None:
        return 0.5  # no budget constraint defined

    priced = [r for r in response.recommendations if r.price is not None]
    if not priced:
        return 0.5  # cannot assess

    low  = budget_min * 0.8
    high = budget_max * 1.2
    in_range = sum(1 for r in priced if low <= r.price <= high)
    return in_range / len(priced)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def score_recommendation(
    response: RecommendationResponse,
    wine_list_text: str,
    profile: Optional[TasteProfile] = None,
) -> ScoringResult:
    """
    Score a RecommendationResponse on four weighted dimensions.

    Args:
        response:       The RecommendationResponse from get_recommendation().
        wine_list_text: Parsed restaurant wine list text.
        profile:        User's TasteProfile (may be None if unavailable).

    Returns:
        ScoringResult with total in [0.0, 1.0] and per-dimension breakdown.

    Never raises — all missing/edge-case data resolves to neutral (0.5) or
    zero scores internally.
    """
    try:
        breakdown = {
            "confidence":   _score_confidence(response),
            "completeness": _score_completeness(response),
            "grounding":    _score_grounding(response, wine_list_text),
            "budget_fit":   _score_budget_fit(response, profile),
        }
        total = sum(_WEIGHTS[k] * v for k, v in breakdown.items())
        # Round to 4dp for clean log output
        total = round(total, 4)
        breakdown = {k: round(v, 4) for k, v in breakdown.items()}
        return ScoringResult(total=total, breakdown=breakdown)
    except Exception:
        # Fallback: return a neutral result so the caller is never affected
        return ScoringResult(
            total=0.5,
            breakdown={"confidence": 0.5, "completeness": 0.5, "grounding": 0.5, "budget_fit": 0.5},
        )
