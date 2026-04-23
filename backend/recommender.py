"""Wine recommendation via Anthropic Claude API."""

import json
import logging
<<<<<<< HEAD
import logging.handlers
<<<<<<< HEAD
=======
>>>>>>> 6caf2d0 (Initial commit: Setting up project structure)
import re
=======
>>>>>>> 90359d9 (Ported to Anthropic)
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
<<<<<<< HEAD
    _llm_handler = logging.handlers.RotatingFileHandler(
        _log_dir / "llm.log", maxBytes=1_000_000, backupCount=2, encoding="utf-8"
    )
=======
    _llm_handler = logging.FileHandler(_log_dir / "llm.log", encoding="utf-8")
>>>>>>> 6caf2d0 (Initial commit: Setting up project structure)
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

<<<<<<< HEAD
# JSON Schema passed to Ollama's structured-output feature (format=<dict>).
# Grammar-constrained sampling forces the model to emit these exact keys/types
# regardless of whether it follows the system-prompt instructions.
# Requires Ollama ≥ 0.5.1.  Falls back to format="json" automatically on 400.
_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "recommendations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "rank":       {"type": "integer"},
                    "wine_name":  {"type": "string"},
                    "producer":   {"type": "string"},
                    "vintage":    {"type": "integer"},
                    "region":     {"type": "string"},
                    "price":      {"type": "number"},
                    "reasoning":  {
                        "type": "string",
                        "description": (
<<<<<<< HEAD
<<<<<<< HEAD
                            "2-4 sentences explaining why this restaurant wine was selected. "
                            "REQUIRED FIRST SENTENCE: either (a) if a specific owned bottle from the cellar list is a close stylistic match, "
                            "open with 'Like your [Producer + Wine name], but [how this differs/excels]' — "
                            "only use this form when you can name a real bottle; or (b) if no close cellar match exists, "
                            "open by naming a concrete preference from the taste profile directly, "
                            "e.g. 'Delivers the mineral-driven acidity you consistently reach for.' "
                            "FORBIDDEN: using 'Like your [no specific owned bottle]' or any bracket placeholder. "
                            "Where relevant, contrast against an avoided style: 'Unlike [avoided style], no [unwanted trait].' "
                            "Then briefly add meal synergy only if it adds genuine insight beyond the profile match."
=======
                            "2-4 sentences. Lead with a personal comparison: "
                            "'Like your [specific bottle the user owns], but [how this differs or excels].' "
                            "Where relevant, contrast against an avoided style: "
                            "'Unlike [avoided bottle/style], no [unwanted trait].' "
                            "Then add meal synergy if it adds genuine insight beyond the profile match."
>>>>>>> 6caf2d0 (Initial commit: Setting up project structure)
=======
                            "2-4 sentences explaining why this restaurant wine was selected. "
                            "REQUIRED FIRST SENTENCE: reference a specific, named preference from the owner's taste profile — "
                            "e.g. 'Delivers the [named trait] you consistently reach for' or 'Hits your preference for [named style].' "
                            "FORBIDDEN as a first sentence: any generic tannin/acidity/structure/flavor observation "
                            "that does not quote or paraphrase a concrete trait from the taste profile. "
                            "Where relevant, contrast against an avoided style: "
                            "'Unlike [avoided style], no [unwanted trait].' "
                            "Then briefly add meal synergy only if it adds genuine insight beyond the profile match."
>>>>>>> faa3422 (Commit despite broken recommendation engine)
                        ),
                    },
                    "confidence": {
                        "type": "string",
<<<<<<< HEAD
<<<<<<< HEAD
                        "pattern": "^(high|medium|low)",
                        "description": (
                            "MUST start with exactly the word 'high', 'medium', or 'low', then ' — ', "
                            "then a single clause explaining the rating. "
                            "FORBIDDEN: numeric scores (8/10, 85%), percentages, HTML tags, or any other format. "
                            "Examples: 'high — hits your preference for grower Champagne with mineral complexity' "
                            "or 'medium — right style but the vintage may be too young'."
=======
                        "description": (
                            "Start with 'high', 'medium', or 'low', then a dash and a single clause "
                            "explaining why — e.g. 'high — hits your preference for grower Champagne "
                            "with mineral complexity' or 'medium — style is right but the vintage is young'."
>>>>>>> 6caf2d0 (Initial commit: Setting up project structure)
=======
                        "pattern": "^(high|medium|low)",
                        "description": (
                            "MUST start with exactly the word 'high', 'medium', or 'low', then ' — ', "
                            "then a single clause explaining the rating. "
                            "FORBIDDEN: numeric scores (8/10, 85%), percentages, HTML tags, or any other format. "
                            "Examples: 'high — hits your preference for grower Champagne with mineral complexity' "
                            "or 'medium — right style but the vintage may be too young'."
>>>>>>> faa3422 (Commit despite broken recommendation engine)
                        ),
=======
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
>>>>>>> 90359d9 (Ported to Anthropic)
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

<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
        # Ollama < 0.5.1 rejects a schema dict with 400 or 500 — fall back to plain JSON mode.
        if response.status_code in (400, 500):
            logger.warning("attempt=%d schema_format_rejected_fallback_to_plain_json status=%d", attempt, response.status_code)
=======
        # Ollama < 0.5.1 rejects a schema dict with 400 — fall back to plain JSON mode.
        if response.status_code == 400:
            logger.warning("attempt=%d schema_format_rejected_fallback_to_plain_json status=400", attempt)
>>>>>>> 6caf2d0 (Initial commit: Setting up project structure)
=======
        # Ollama < 0.5.1 rejects a schema dict with 400 or 500 — fall back to plain JSON mode.
        if response.status_code in (400, 500):
            logger.warning("attempt=%d schema_format_rejected_fallback_to_plain_json status=%d", attempt, response.status_code)
>>>>>>> faa3422 (Commit despite broken recommendation engine)
            response = _call_ollama(
                http_client, ollama_url, ollama_model,
                system_prompt, text_payload, image_b64, "json",
            )
=======
    tool_block = next(
        (b for b in response.content if b.type == "tool_use" and b.name == "provide_recommendations"),
        None,
    )
    if not tool_block:
        raise ValueError("Claude did not use the recommendation tool")
>>>>>>> 90359d9 (Ported to Anthropic)

    data = tool_block.input  # Already a parsed dict — no JSON parsing needed
    logger.info("attempt=%d tool_use_received keys=%s", attempt, list(data.keys()))
    _log_llm_exchange(attempt, system_prompt, text_payload, json.dumps(data, indent=2))

    try:
<<<<<<< HEAD
        recommendation_data = json.loads(result)
    except json.JSONDecodeError as e:
        logger.warning("attempt=%d json_parse_failed error=%s raw_response=%s", attempt, e, result)
        raise ValueError(f"Invalid JSON: {e}") from e

    keys = list(recommendation_data.keys())
    logger.info("attempt=%d json_parsed top_level_keys=%s", attempt, keys)

    # Detect garbage output: empty/special-token keys are a sign the model misfired
    if any(k == "" or "<|" in k for k in keys):
        logger.warning("attempt=%d garbage_keys_detected keys=%s raw_response=%s", attempt, keys, result)
        raise ValueError(f"LLM returned garbage keys: {keys}")

<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> faa3422 (Commit despite broken recommendation engine)
    # Normalize common key aliases the model emits when ignoring the schema.
    # Fixed aliases for summary/note fields:
    _TOP_ALIASES = {
        "summary": "profile_match_summary",
        "profileSummary": "profile_match_summary",
        "profile_summary": "profile_match_summary",
        "matchSummary": "profile_match_summary",
        "listQualityNote": "list_quality_note",
    }
    _ITEM_ALIASES = {
        "name": "wine_name",
        "wineName": "wine_name",
        "title": "wine_name",
        "description": "reasoning",
        "explanation": "reasoning",
        "notes": "reasoning",
    }
    for alias, canonical in _TOP_ALIASES.items():
        if alias in recommendation_data and canonical not in recommendation_data:
            recommendation_data[canonical] = recommendation_data.pop(alias)
            logger.info("attempt=%d normalized_top_key %s→%s", attempt, alias, canonical)

    # Any key whose value is a list is the recommendations array —
    # catches top_bottles, topRecommendations, wines, wineList, etc.
    if "recommendations" not in recommendation_data:
        for k, v in list(recommendation_data.items()):
            if isinstance(v, list):
                recommendation_data["recommendations"] = recommendation_data.pop(k)
                logger.info("attempt=%d inferred_recommendations_key from=%s", attempt, k)
                break

    if isinstance(recommendation_data.get("recommendations"), list):
        for idx, item in enumerate(recommendation_data["recommendations"]):
            if not isinstance(item, dict):
                continue
            for alias, canonical in _ITEM_ALIASES.items():
                if alias in item and canonical not in item:
                    item[canonical] = item.pop(alias)
            # wine_name: try broader aliases, then pick the first short string field
            if "wine_name" not in item:
                _wine_candidates = ("wine", "label", "bottle", "category", "varietal", "grape")
                for cand in _wine_candidates:
                    if isinstance(item.get(cand), str):
                        item["wine_name"] = item.pop(cand)
                        break
                else:
                    # Last resort: grab the shortest string field value present
                    str_fields = [(k, v) for k, v in item.items() if isinstance(v, str)]
                    item["wine_name"] = min(str_fields, key=lambda kv: len(kv[1]))[1] if str_fields else "Unknown Wine"
            # reasoning: try broader aliases, then pick the longest remaining string field
            if "reasoning" not in item:
                _reason_candidates = ("rationale", "match", "why", "comment", "detail")
                for cand in _reason_candidates:
                    if isinstance(item.get(cand), str):
                        item["reasoning"] = item.pop(cand)
                        break
                else:
                    str_fields = [(k, v) for k, v in item.items() if isinstance(v, str) and k != "wine_name"]
                    score_val = item.get("score")
                    if str_fields:
                        item["reasoning"] = max(str_fields, key=lambda kv: len(kv[1]))[1]
                    elif isinstance(score_val, (int, float)):
                        item["reasoning"] = f"Rated {score_val}/10 against the taste profile by the recommendation model."
                        logger.info("attempt=%d item=%d synthesized reasoning from score=%.1f", attempt, idx, score_val)
                    else:
                        item["reasoning"] = "No reasoning provided"
            # Synthesize other missing required fields
            if "rank" not in item:
                item["rank"] = idx + 1
            if "confidence" not in item:
                score = item.pop("score", None)
                if isinstance(score, (int, float)):
                    level = "high" if score >= 9.0 else "medium" if score >= 7.5 else "low"
                    item["confidence"] = f"{level}"
                    logger.info("attempt=%d item=%d converted score=%.1f to confidence=%s", attempt, idx, score, item["confidence"])
                else:
                    item["confidence"] = "low"

    # Synthesize profile_match_summary if the model omitted it entirely
    if not recommendation_data.get("profile_match_summary"):
        recommendation_data["profile_match_summary"] = "Recommendations selected from the restaurant wine list based on taste profile."
        logger.info("attempt=%d synthesized_profile_match_summary", attempt)

<<<<<<< HEAD
=======
>>>>>>> 6caf2d0 (Initial commit: Setting up project structure)
=======
>>>>>>> faa3422 (Commit despite broken recommendation engine)
    try:
        recommendation = RecommendationResponse(**recommendation_data)
    except ValidationError as e:
        logger.warning("attempt=%d schema_validation_failed error=%s raw_response=%s", attempt, e, result)
        raise ValueError(f"Schema mismatch: {e}") from e
=======
        recommendation = RecommendationResponse(**data)
    except ValidationError as exc:
        logger.warning("attempt=%d schema_validation_failed error=%s", attempt, exc)
        raise ValueError(f"Schema validation failed: {exc}") from exc
>>>>>>> 90359d9 (Ported to Anthropic)

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
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> faa3422 (Commit despite broken recommendation engine)
    meal_line = f"Tonight's meal: {meal}" if meal else ""
    user_prompt = (
        f"{meal_line}\n\n"
        "Task: survey every wine on the restaurant wine list below from top to bottom, "
        "score each against the taste profile in the system prompt, then select and rank the top 3. "
        "Recommend ONLY wines that appear on the restaurant wine list — do not hallucinate or substitute. "
        "Return only the JSON response — no preamble."
    ).strip()
<<<<<<< HEAD
    text_payload = (
        user_prompt if image_b64
        else (
            f"Restaurant wine list (select your top 3 recommendations from this list):\n{wine_list_text}\n\n{user_prompt}"
            if wine_list_text else user_prompt
        )
=======
    user_prompt = f"My meal: {meal}\n\nWhat should I order?"
    text_payload = (
        user_prompt if image_b64
        else f"Restaurant wine list:\n{wine_list_text}\n\n{user_prompt}"
>>>>>>> 6caf2d0 (Initial commit: Setting up project structure)
=======
    text_payload = (
        user_prompt if image_b64
        else (
            f"Restaurant wine list (select your top 3 recommendations from this list):\n{wine_list_text}\n\n{user_prompt}"
            if wine_list_text else user_prompt
        )
>>>>>>> faa3422 (Commit despite broken recommendation engine)
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
