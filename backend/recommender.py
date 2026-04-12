"""Wine recommendation via Ollama/LLM."""

import base64
import json
import logging
import re
from pathlib import Path
from typing import Optional

import httpx
from fastapi import HTTPException
from pydantic import ValidationError

from models import RecommendationResponse

logger = logging.getLogger("sommelier.recommender")

# Dedicated file logger for raw LLM input/output — one entry per call.
_log_dir = Path(__file__).resolve().parent / "logs"
_log_dir.mkdir(parents=True, exist_ok=True)
_llm_logger = logging.getLogger("sommelier.llm.raw")
if not _llm_logger.handlers:
    _llm_handler = logging.FileHandler(_log_dir / "llm.log", encoding="utf-8")
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
        f"--- RAW RESPONSE ---\n{raw_response}"
    )
    _llm_logger.debug(entry, extra={"attempt": attempt})

_MAX_ATTEMPTS = 3

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
                            "2-4 sentences. Lead with a personal comparison: "
                            "'Like your [specific bottle the user owns], but [how this differs or excels].' "
                            "Where relevant, contrast against an avoided style: "
                            "'Unlike [avoided bottle/style], no [unwanted trait].' "
                            "Then add meal synergy if it adds genuine insight beyond the profile match."
                        ),
                    },
                    "confidence": {
                        "type": "string",
                        "description": (
                            "Start with 'high', 'medium', or 'low', then a dash and a single clause "
                            "explaining why — e.g. 'high — hits your preference for grower Champagne "
                            "with mineral complexity' or 'medium — style is right but the vintage is young'."
                        ),
                    },
                },
                "required": ["rank", "wine_name", "reasoning", "confidence"],
            },
        },
        "list_quality_note":    {"type": "string"},
        "profile_match_summary": {"type": "string"},
    },
    "required": ["recommendations", "profile_match_summary"],
}


def _call_ollama(
    http_client: httpx.Client,
    ollama_url: str,
    ollama_model: str,
    system_prompt: str,
    text_payload: str,
    image_b64: Optional[str],
    fmt: object,
) -> httpx.Response:
    """POST to /api/chat (with /api/generate fallback on 404)."""
    chat_payload: dict = {
        "model": ollama_model,
        "stream": False,
        "format": fmt,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text_payload},
        ],
    }
    if image_b64:
        chat_payload["messages"][1]["images"] = [image_b64]

    response = http_client.post(f"{ollama_url}/api/chat", json=chat_payload)

    if response.status_code == 404:
        logger.warning("ollama_chat_404_fallback_to_generate model=%s", ollama_model)
        generate_payload: dict = {
            "model": ollama_model,
            "stream": False,
            "format": fmt,
            "system": system_prompt,
            "prompt": text_payload,
        }
        if image_b64:
            generate_payload["images"] = [image_b64]
        response = http_client.post(f"{ollama_url}/api/generate", json=generate_payload)

    return response


def _attempt_recommendation(
    text_payload: str,
    system_prompt: str,
    ollama_url: str,
    ollama_model: str,
    image_b64: Optional[str],
    attempt: int,
) -> RecommendationResponse:
    """Single attempt at calling Ollama and parsing the response.

    Raises ValueError on bad/garbage LLM output (retriable).
    Raises HTTPException on network/HTTP errors (not retriable).
    """
    with httpx.Client(timeout=120.0) as http_client:
        response = _call_ollama(
            http_client, ollama_url, ollama_model,
            system_prompt, text_payload, image_b64, _RESPONSE_SCHEMA,
        )

        # Ollama < 0.5.1 rejects a schema dict with 400 — fall back to plain JSON mode.
        if response.status_code == 400:
            logger.warning("attempt=%d schema_format_rejected_fallback_to_plain_json status=400", attempt)
            response = _call_ollama(
                http_client, ollama_url, ollama_model,
                system_prompt, text_payload, image_b64, "json",
            )

        response.raise_for_status()

    body = response.json()
    result = (body.get("message", {}).get("content") or body.get("response") or "").strip()
    if not result:
        raise ValueError("Ollama returned an empty response")

    logger.info("attempt=%d raw_response_length=%d", attempt, len(result))
    _log_llm_exchange(attempt, system_prompt, text_payload, result)

    # Strip markdown fences if LLM wrapped the JSON despite instructions
    if result.startswith("```"):
        result = re.sub(r"^```(?:json)?\s*", "", result)
        result = re.sub(r"\s*```$", "", result)
        result = result.strip()

    # Repair truncated JSON (missing closing braces)
    opened = result.count("{")
    closed = result.count("}")
    if opened > closed:
        result += "}" * (opened - closed)
        logger.info("attempt=%d repaired_missing_braces=%d", attempt, opened - closed)

    try:
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

    try:
        recommendation = RecommendationResponse(**recommendation_data)
    except ValidationError as e:
        logger.warning("attempt=%d schema_validation_failed error=%s raw_response=%s", attempt, e, result)
        raise ValueError(f"Schema mismatch: {e}") from e

    logger.info("attempt=%d schema_validation_passed wines=%d", attempt, len(recommendation.recommendations))
    return recommendation


def get_recommendation(
    wine_list_text: str,
    meal: str,
    system_prompt: str,
    ollama_url: str,
    ollama_model: str,
    image_b64: Optional[str] = None,
) -> RecommendationResponse:
    """
    Get wine recommendation from Ollama/LLM.

    Retries up to _MAX_ATTEMPTS times on garbage/invalid LLM output.

    Raises:
        HTTPException: On Ollama network failure or all attempts exhausted.
    """
    user_prompt = f"My meal: {meal}\n\nWhat should I order?"
    text_payload = (
        user_prompt if image_b64
        else f"Restaurant wine list:\n{wine_list_text}\n\n{user_prompt}"
    )

    last_err: Exception = RuntimeError("no attempts made")

    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            return _attempt_recommendation(
                text_payload, system_prompt, ollama_url, ollama_model, image_b64, attempt
            )
        except ValueError as exc:
            # Bad LLM output — log and retry
            last_err = exc
            logger.warning("get_recommendation: attempt=%d/%d failed: %s", attempt, _MAX_ATTEMPTS, exc)
        except httpx.HTTPStatusError as exc:
            # HTTP error from Ollama — not worth retrying
            logger.exception("recommend_provider_http_error status=%s", exc.response.status_code)
            raise HTTPException(
                status_code=502,
                detail=f"Recommendation provider HTTP error: {exc.response.status_code}",
            ) from exc
        except Exception as exc:
            # Network/unexpected error — not worth retrying
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
