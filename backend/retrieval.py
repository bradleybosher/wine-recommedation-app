"""Retrieval-augmented pre-filtering for large restaurant wine lists.

When a wine list exceeds _ACTIVATION_THRESHOLD lines after the coarse
inventory filter, rank each line by profile-signal overlap and keep only
the top `limit` lines for the recommendation prompt.  This keeps token
counts predictable and focuses Claude on wines the guest is likely to enjoy.

Scoring (per line):
  +0.25  baseline — every line gets this so zero-score lines don't fall purely by position
  +2.0   for each top-producer name that appears
  +1.5   for each preferred region/appellation term (with synonym expansion)
  +1.0   for each preferred grape/varietal term (with synonym expansion)
  +0.5   for each preferred style descriptor that appears
  -2.0   for each avoided-style token (single-token markers, not full sentences)
  -0.5   if price is extractable and below 50% of budget_min
  -0.5   if price is extractable and above 200% of budget_max

No API calls are made; matching is keyword-based with accent normalisation and
synonym expansion via backend/synonyms.py.
"""

import logging
import re
import unicodedata
from typing import Optional

from models import TasteProfile
from synonyms import expand_terms

logger = logging.getLogger("sommelier.retrieval")

# Number of lines above which retrieval kicks in.
_ACTIVATION_THRESHOLD = 40


def _normalize(text: str) -> str:
    """Lowercase and strip combining diacritics for accent-insensitive matching."""
    nfkd = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _extract_price(line: str) -> Optional[float]:
    m = re.search(r"[\$£€]\s*(\d+(?:\.\d+)?)", line)
    return float(m.group(1)) if m else None


def _score_line(
    line: str,
    producer_terms: list[str],
    region_terms: list[str],
    grape_terms: list[str],
    style_terms: list[str],
    negative_tokens: list[str],
    budget_min: Optional[float],
    budget_max: Optional[float],
) -> float:
    folded = _normalize(line)

    # Baseline — every line starts with a small positive so position doesn't dominate
    score = 0.25

    for term in producer_terms:
        if term and term in folded:
            score += 2.0

    for term in region_terms:
        if term and term in folded:
            score += 1.5

    for term in grape_terms:
        if term and term in folded:
            score += 1.0

    for term in style_terms:
        if term and term in folded:
            score += 0.5

    for token in negative_tokens:
        if token and token in folded:
            score -= 2.0

    price = _extract_price(line)
    if price is not None:
        if budget_min is not None and price < budget_min * 0.5:
            score -= 0.5
        if budget_max is not None and price > budget_max * 2.0:
            score -= 0.5

    return score


def rank_wine_list(
    wine_list_text: str,
    profile: TasteProfile,
    override_terms: Optional[list[str]] = None,
    limit: int = 40,
) -> str:
    """Return up to `limit` lines from wine_list_text ranked by profile fit.

    No-op when list has ≤ limit lines.  When profile has no positive signals,
    truncates to the first `limit` lines rather than skipping entirely, so
    the prompt never exceeds the token budget for very long lists.

    Scoring is tiered (highest first):
      producers (+2.0), regions (+1.5), grapes (+1.0), styles (+0.5)
    with synonym/appellation expansion applied to grapes and regions.
    """
    lines = [ln for ln in wine_list_text.splitlines() if ln.strip()]
    if len(lines) <= limit:
        return wine_list_text

    # Producer terms — exact match, no expansion needed (these are proper names)
    producer_terms = [_normalize(t) for t in (profile.top_producers or []) if t]

    # Region terms — expand to include sub-appellations and aliases
    region_terms = [
        _normalize(t)
        for t in expand_terms(list(profile.preferred_regions or []))
        if t
    ]

    # Grape terms — expand to include local synonyms
    grape_terms = [
        _normalize(t)
        for t in expand_terms(list(profile.preferred_grapes or []))
        if t
    ]

    # Style descriptors (lower weight — these are sensory phrases, less likely to appear verbatim)
    style_terms = [_normalize(t) for t in (profile.preferred_styles or []) if t]

    # Override terms count as grape-weight (+1.0)
    if override_terms:
        grape_terms.extend(_normalize(t) for t in override_terms if t)

    # Negative tokens — use distilled single-token markers (not full sentences)
    # Fall back to full avoided_styles only when no tokens are present
    negative_tokens: list[str] = []
    if profile.avoided_style_tokens:
        negative_tokens = [_normalize(t) for t in profile.avoided_style_tokens if t]
    elif profile.avoided_styles:
        negative_tokens = [_normalize(t) for t in profile.avoided_styles if t]

    has_positive = bool(producer_terms or region_terms or grape_terms or style_terms)
    if not has_positive:
        logger.debug("rank_wine_list: no positive signals — truncating to first %d lines", limit)
        return "\n".join(lines[:limit])

    # Include original index so equal-scoring lines preserve list order
    scored = [
        (
            _score_line(
                ln,
                producer_terms,
                region_terms,
                grape_terms,
                style_terms,
                negative_tokens,
                profile.budget_min,
                profile.budget_max,
            ),
            idx,
            ln,
        )
        for idx, ln in enumerate(lines)
    ]
    scored.sort(key=lambda x: (-x[0], x[1]))
    top_lines = [ln for _, _, ln in scored[:limit]]

    logger.info(
        "rank_wine_list: reduced %d → %d lines "
        "(producers=%d, regions=%d, grapes=%d, styles=%d, negative=%d terms)",
        len(lines),
        limit,
        len(producer_terms),
        len(region_terms),
        len(grape_terms),
        len(style_terms),
        len(negative_tokens),
    )
    return "\n".join(top_lines)
