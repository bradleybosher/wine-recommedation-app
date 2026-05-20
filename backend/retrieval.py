"""Retrieval-augmented pre-filtering for large restaurant wine lists.

When a wine list exceeds _ACTIVATION_THRESHOLD lines after the coarse
inventory filter, rank each line by profile-signal overlap and keep only
the top `limit` lines for the recommendation prompt.  This keeps token
counts predictable and focuses Claude on wines the guest is likely to enjoy.

Scoring (per line):
  +1.0  for each preferred grape/region/style term that appears
  -2.0  for each avoided-style term that appears
  -0.5  if price is extractable and below 50% of budget_min
  -0.5  if price is extractable and above 200% of budget_max

No API calls are made; matching is keyword-based with accent normalisation.
"""

import logging
import re
import unicodedata
from typing import Optional

from models import TasteProfile

logger = logging.getLogger("sommelier.retrieval")

# Number of lines above which retrieval kicks in.
_ACTIVATION_THRESHOLD = 40


def _normalize(text: str) -> str:
    """Lowercase and strip combining diacritics for accent-insensitive matching."""
    nfkd = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _extract_price(line: str) -> Optional[float]:
    m = re.search(r"\$\s*(\d+(?:\.\d+)?)", line)
    return float(m.group(1)) if m else None


def _score_line(
    line: str,
    positive_terms: list[str],
    negative_terms: list[str],
    budget_min: Optional[float],
    budget_max: Optional[float],
) -> float:
    folded = _normalize(line)
    score = 0.0

    for term in positive_terms:
        if term in folded:
            score += 1.0

    for term in negative_terms:
        if term in folded:
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
    """
    lines = [ln for ln in wine_list_text.splitlines() if ln.strip()]
    if len(lines) <= limit:
        return wine_list_text

    positive_terms: list[str] = []
    for group in (
        profile.preferred_grapes,
        profile.preferred_regions,
        profile.preferred_styles,
        override_terms or [],
    ):
        positive_terms.extend(_normalize(t) for t in group if t)

    negative_terms = [_normalize(t) for t in profile.avoided_styles if t]

    if not positive_terms:
        logger.debug("rank_wine_list: no positive signals — truncating to first %d lines", limit)
        return "\n".join(lines[:limit])

    # Include original index so equal-scoring lines preserve list order
    scored = [
        (_score_line(ln, positive_terms, negative_terms, profile.budget_min, profile.budget_max), idx, ln)
        for idx, ln in enumerate(lines)
    ]
    scored.sort(key=lambda x: (-x[0], x[1]))
    top_lines = [ln for _, _, ln in scored[:limit]]

    logger.info(
        "rank_wine_list: reduced %d → %d lines (positive=%d terms, negative=%d terms)",
        len(lines),
        limit,
        len(positive_terms),
        len(negative_terms),
    )
    return "\n".join(top_lines)
