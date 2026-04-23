"""Wine recommendation via Anthropic Claude API."""

import json
import logging
import logging.handlers
from pathlib import Path
from typing import Optional

import anthropic
from fastapi import HTTPException
from pydantic import ValidationError

from models import RecommendationResponse

logger = logging.getLogger("sommelier.recommender")

# Dedicated file logger for raw LLM input/output — one entry per call.
_log_dir = Path(__file__).resolve().parent / "logs"
_log_dir.mkdir(parents=True, exist_ok=True)
_llm_logger = logging.getLogger("sommelier.llm.raw")
if not _llm_logger.handlers:
    _llm_handler = logging.handlers.RotatingFileHandler(
        _log_dir / "llm.log", maxBytes=1_000_000, backupCount=2, encoding="utf-8"
    )
    _llm_handler.setFormatter(
        logging.Formatter("%(asctime)s [attempt=%(attempt)s]\n%(message)s\n" + "=" * 80)
    )
    _llm_logger.addHandler(_llm_handler)
    _llm_logger.setLevel(logging.DEBUG)
    _llm_logger.propagate = False


def _log_llm_exchange(attempt: int, system_prompt: str, user_payload: str, raw_response: str) -> None:
    """Write a single prompt+response exchange to llm.log."""
    entry = (
        f"--- SYSTEM PROMPT ---\n{system_prompt}\n\n"
        f"--- USER PAYLOAD ---\n{user_payload}\n\n"
        f"--- TOOL USE INPUT (PARSED) ---\n{raw_response}"
    )
    _llm_logger.debug(entry, extra={"attempt": attempt})


_MAX_ATTEMPTS = 3

# Tool definition passed to Claude for structured output via tool use.
# Claude is forced to call this tool, returning a parsed dict directly —
# no JSON parsing or repair logic required.
_RECOMMENDATION_TOOL: dict = {
    "name": "provide_recommendations",
    "description": "Provide ranked wine recommendations from the restaurant wine list.",
    "input_schema": {
        "type": "object",
        "properties": {
            "recommendations": {
                "type": "array",
                "description": "Top 3 wine recommendations from the list, ranked best-first.",
                "items": {
                    "type": "object",
                    "properties": {
                        "rank":      {"type": "integer"},
                        "wine_name": {"type": "string"},
                        "producer":  {"type": "string"},
                        "vintage":   {"type": "integer"},
                        "region":    {"type": "string"},
                        "price":     {"type": "number"},
                        "reasoning": {
                            "type": "string",
                            "description": (
                                "2-4 sentences explaining why this restaurant wine was selected. "
                                "REQUIRED FIRST SENTENCE: either (a) if a specific owned bottle from the cellar list is a close stylistic match, "
                                "open with 'Like your [Producer + Wine name], but [how this differs/excels]' — "
                                "only use this form when you can name a real bottle; or (b) if no close cellar match exists, "
                                "open by naming a concrete preference from the taste profile directly, "
                                "e.g. 'Delivers the mineral-driven acidity you consistently reach for.' "
                                "FORBIDDEN: using 'Like your [no specific owned bottle]' or any bracket placeholder. "
                                "Where relevant, contrast against an avoided style: 'Unlike [avoided style], no [unwanted trait].' "
                                "Then briefly add meal synergy only if it adds genuine insight beyond the profile match."
                            ),
                        },
                        "confidence": {
                            "type": "string",
                            "description": (
                                "MUST start with exactly the word 'high', 'medium', or 'low', then ' — ', "
                                "then a single clause explaining the rating. "
                                "FORBIDDEN: numeric scores (8/10, 85%), percentages, HTML tags, or any other format. "
                                "Examples: 'high — hits your preference for grower Champagne with mineral complexity' "
                                "or 'medium — right style but the vintage may be too young'."
                            ),
                        },
                    },
                    "required": ["rank", "wine_name", "reasoning", "confidence"],
                },
            },
            "list_quality_note":     {"type": "string"},
            "profile_match_summary": {"type": "string"},
        },
        "required": ["recommendations", "profile_match_summary"],
    },
}


def _attempt_recommendation(
    text_payload: str,
    system_prompt: str,
    anthropic_api_key: str,
    anthropic_model: str,
    image_b64: Optional[str],
    attempt: int,
) -> RecommendationResponse:
    """Single attempt at calling Claude and extracting a structured recommendation.

    Raises ValueError on schema validation failures (retriable).
    Raises HTTPException on API errors (not retriable).
    """
    client = anthropic.Anthropic(api_key=anthropic_api_key)

    content: list = []
    if image_b64:
        content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": "image/jpeg", "data": image_b64},
        })
    content.append({"type": "text", "text": text_payload})

    try:
        response = client.messages.create(
            model=anthropic_model,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": content}],
            tools=[_RECOMMENDATION_TOOL],
            tool_choice={"type": "tool", "name": "provide_recommendations"},
        )
    except anthropic.APIError as exc:
        logger.exception("anthropic_api_error status=%s", getattr(exc, "status_code", "unknown"))
        raise HTTPException(
            status_code=502,
            detail=f"Recommendation provider API error: {exc}",
        ) from exc

    tool_block = next(
        (b for b in response.content if b.type == "tool_use" and b.name == "provide_recommendations"),
        None,
    )
    if not tool_block:
        raise ValueError("Claude did not use the recommendation tool")

    data = tool_block.input  # Already a parsed dict — no JSON parsing needed
    logger.info("attempt=%d tool_use_received keys=%s", attempt, list(data.keys()))
    _log_llm_exchange(attempt, system_prompt, text_payload, json.dumps(data, indent=2))

    try:
        recommendation = RecommendationResponse(**data)
    except ValidationError as exc:
        logger.warning("attempt=%d schema_validation_failed error=%s", attempt, exc)
        raise ValueError(f"Schema validation failed: {exc}") from exc

    logger.info("attempt=%d schema_validation_passed wines=%d", attempt, len(recommendation.recommendations))
    return recommendation


def get_recommendation(
    wine_list_text: str,
    meal: str,
    system_prompt: str,
    anthropic_api_key: str,
    anthropic_model: str,
    image_b64: Optional[str] = None,
) -> RecommendationResponse:
    """Get wine recommendation from Anthropic Claude.

    Retries up to _MAX_ATTEMPTS times on schema validation errors.

    Raises:
        HTTPException: On API failure or all attempts exhausted.
    """
    meal_line = f"Tonight's meal: {meal}" if meal else ""
    user_prompt = (
        f"{meal_line}\n\n"
        "Task: survey every wine on the restaurant wine list below from top to bottom, "
        "score each against the taste profile in the system prompt, then select and rank the top 3. "
        "Recommend ONLY wines that appear on the restaurant wine list — do not hallucinate or substitute. "
        "Return only the JSON response — no preamble."
    ).strip()
    text_payload = (
        user_prompt if image_b64
        else (
            f"Restaurant wine list (select your top 3 recommendations from this list):\n{wine_list_text}\n\n{user_prompt}"
            if wine_list_text else user_prompt
        )
    )

    last_err: Exception = RuntimeError("no attempts made")

    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            return _attempt_recommendation(
                text_payload, system_prompt, anthropic_api_key, anthropic_model, image_b64, attempt
            )
        except ValueError as exc:
            last_err = exc
            logger.warning("get_recommendation: attempt=%d/%d failed: %s", attempt, _MAX_ATTEMPTS, exc)
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("recommend_provider_error error=%s", type(exc).__name__)
            raise HTTPException(
                status_code=502,
                detail=f"Recommendation provider failed: {type(exc).__name__}",
            ) from exc

    logger.error("get_recommendation: all %d attempts failed, last_error=%s", _MAX_ATTEMPTS, last_err)
    raise HTTPException(
        status_code=502,
        detail=f"Recommendation provider failed after {_MAX_ATTEMPTS} attempts: {last_err}",
    )
