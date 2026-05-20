"""
LLM eval harness — wine recommendation pipeline.

replay: load recorded fixtures, validate schema + color derivation, score against thresholds.
        No API key required. Safe to run in CI on every build.

live:   call get_recommendation() against the real Claude API.
        Requires ANTHROPIC_API_KEY. Skipped unless key is present and non-dummy.
        Intended for nightly or pre-release validation.

Usage:
    pytest backend/tests/llm_evals/               # replay only (live skipped)
    pytest backend/tests/llm_evals/ -m replay     # explicit replay
    ANTHROPIC_API_KEY=sk-... pytest -m live        # live only
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_CASES_PATH = Path(__file__).resolve().parent / "cases.json"
_FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "llm_replay"

# ---------------------------------------------------------------------------
# Load golden cases at import time
# ---------------------------------------------------------------------------


def _load_cases() -> list[dict[str, Any]]:
    with _CASES_PATH.open(encoding="utf-8") as f:
        return json.load(f)["cases"]


_ALL_CASES = _load_cases()
_REPLAY_CASES = [c for c in _ALL_CASES if c["mark"] == "replay"]
_LIVE_CASES = [c for c in _ALL_CASES if c["mark"] == "live"]

# ---------------------------------------------------------------------------
# Confidence-level → score map (mirrors scorer._CONFIDENCE_MAP)
# ---------------------------------------------------------------------------

_LEVEL_SCORE: dict[str, float] = {"high": 1.0, "medium": 0.67, "low": 0.33}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_fixture(replay_file: str) -> Any:
    from models import RecommendationResponse

    path = _FIXTURES_DIR / replay_file
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    return RecommendationResponse(**data)


def _apply_colors(response: Any) -> None:
    from recommender import _derive_color

    for wine in response.recommendations:
        if wine.color is None:
            wine.color = _derive_color(wine)


def _build_taste_profile(profile_data: dict[str, Any]) -> Any:
    from models import TasteProfile

    avg = profile_data.get("avg_spend")
    return TasteProfile(
        budget_min=float(avg) * 0.5 if avg else None,
        budget_max=float(avg) * 1.5 if avg else None,
    )


def _score(response: Any, case: dict[str, Any]) -> Any:
    from scorer import score_recommendation

    profile = _build_taste_profile(case["profile"])
    return score_recommendation(
        response,
        wine_list_text=case.get("wine_list_text", ""),
        profile=profile,
        cap_confidence=case.get("cap_confidence", False),
    )


def _assert_case(response: Any, result: Any, case: dict[str, Any]) -> None:
    """Run all assertions defined in the case's 'expected' block."""
    expected = case["expected"]
    cid = case["id"]

    if "min_completeness" in expected:
        assert result.breakdown["completeness"] >= expected["min_completeness"], (
            f"{cid}: completeness {result.breakdown['completeness']:.2f} "
            f"< {expected['min_completeness']}"
        )

    if "min_grounding" in expected:
        assert result.breakdown["grounding"] >= expected["min_grounding"], (
            f"{cid}: grounding {result.breakdown['grounding']:.2f} "
            f"< {expected['min_grounding']}"
        )

    if "min_confidence_score" in expected:
        assert result.breakdown["confidence"] >= expected["min_confidence_score"], (
            f"{cid}: confidence_score {result.breakdown['confidence']:.2f} "
            f"< {expected['min_confidence_score']}"
        )

    if "min_budget_fit" in expected:
        assert result.breakdown["budget_fit"] >= expected["min_budget_fit"], (
            f"{cid}: budget_fit {result.breakdown['budget_fit']:.2f} "
            f"< {expected['min_budget_fit']}"
        )

    if "min_total_score" in expected:
        assert result.total >= expected["min_total_score"], (
            f"{cid}: total_score {result.total:.4f} < {expected['min_total_score']}"
        )

    if "max_price" in expected:
        for wine in response.recommendations:
            if wine.price is not None:
                assert wine.price <= expected["max_price"], (
                    f"{cid}: {wine.wine_name} price {wine.price} > max {expected['max_price']}"
                )

    if "max_confidence_level" in expected:
        # Verify the scorer's confidence dimension does not exceed the stated cap.
        # The scorer applies cap_confidence internally; we verify the output score.
        cap_level = expected["max_confidence_level"]
        max_allowed = _LEVEL_SCORE.get(cap_level, 0.67)
        assert result.breakdown["confidence"] <= max_allowed + 1e-9, (
            f"{cid}: confidence score {result.breakdown['confidence']:.2f} "
            f"> max for level '{cap_level}' ({max_allowed})"
        )

    if "no_avoided_styles_in_wine_names" in expected:
        rec_names = " ".join(w.wine_name.lower() for w in response.recommendations)
        for term in expected["no_avoided_styles_in_wine_names"]:
            assert term.lower() not in rec_names, (
                f"{cid}: avoided term '{term}' found in recommendation names"
            )

    if "excluded_producers" in expected:
        rec_text = " ".join(
            f"{w.wine_name} {w.producer or ''}".lower()
            for w in response.recommendations
        )
        for term in expected["excluded_producers"]:
            assert term.lower() not in rec_text, (
                f"{cid}: excluded term '{term}' appeared in recommendations"
            )

    if expected.get("grounding_neutral"):
        assert result.breakdown["grounding"] == 0.5, (
            f"{cid}: expected neutral grounding 0.5 (cellar mode), "
            f"got {result.breakdown['grounding']}"
        )

    for flag, attr in [
        ("all_have_bars", "bars"),
        ("all_have_coords", "coords"),
        ("all_have_drink_window", "drink"),
        ("all_have_wheel", "wheel"),
    ]:
        if expected.get(flag):
            for wine in response.recommendations:
                assert getattr(wine, attr) is not None, (
                    f"{cid}: {wine.wine_name} missing '{attr}'"
                )


def _build_profile_text(profile_data: dict[str, Any]) -> str:
    """Render the eval-case profile dict as a taste-profile text block."""
    parts: list[str] = []
    if profile_data.get("top_varietals"):
        parts.append(f"Top varietals: {', '.join(profile_data['top_varietals'])}")
    if profile_data.get("top_regions"):
        parts.append(f"Top regions: {', '.join(profile_data['top_regions'])}")
    if profile_data.get("top_producers"):
        parts.append(f"Top producers: {', '.join(profile_data['top_producers'])}")
    if profile_data.get("preferred_descriptors"):
        parts.append(
            f"Preferred descriptors: {', '.join(profile_data['preferred_descriptors'])}"
        )
    if profile_data.get("avoided_styles"):
        parts.append(f"Avoided styles: {', '.join(profile_data['avoided_styles'])}")
    if profile_data.get("avg_spend"):
        parts.append(f"Average spend: ${profile_data['avg_spend']}")
    if profile_data.get("style_summary"):
        parts.append(f"Style summary: {profile_data['style_summary']}")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Replay tests — no API key required
# ---------------------------------------------------------------------------


@pytest.mark.replay
@pytest.mark.parametrize("case", _REPLAY_CASES, ids=[c["id"] for c in _REPLAY_CASES])
def test_replay(case: dict[str, Any]) -> None:
    """Load recorded response, validate schema + colors, score, assert expectations."""
    response = _load_fixture(case["replay_file"])
    _apply_colors(response)
    result = _score(response, case)
    _assert_case(response, result, case)


# ---------------------------------------------------------------------------
# Live tests — require ANTHROPIC_API_KEY
# ---------------------------------------------------------------------------

_api_key = os.getenv("ANTHROPIC_API_KEY", "")
_LIVE_SKIP = pytest.mark.skipif(
    not _api_key or _api_key.startswith("test-"),
    reason="ANTHROPIC_API_KEY not set or is a dummy — skipping live LLM eval",
)


@pytest.mark.live
@_LIVE_SKIP
@pytest.mark.parametrize("case", _LIVE_CASES, ids=[c["id"] for c in _LIVE_CASES])
def test_live(case: dict[str, Any]) -> None:
    """Call get_recommendation() via the real Claude API and assert scoring expectations."""
    from prompt import build_system_prompt
    from recommender import get_recommendation

    profile_data = case["profile"]
    profile_text = _build_profile_text(profile_data)

    system_prompt = build_system_prompt(
        relevant_bottles=[],
        taste_profile_override=profile_text,
        meal_hints=case.get("meal", ""),
        taste_markers=profile_data.get("taste_markers"),
        profile_source=profile_data.get("profile_source", "cellartracker"),
        source_mode=case["source_mode"],
    )

    response = get_recommendation(
        wine_list_text=case.get("wine_list_text", ""),
        meal=case.get("meal", ""),
        system_prompt=system_prompt,
        anthropic_api_key=_api_key,
        anthropic_model=os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001"),
        source_mode=case["source_mode"],
    )

    result = _score(response, case)
    _assert_case(response, result, case)
