"""Wine recommendation via Anthropic Claude API."""

import json
import logging
import logging.handlers
import os
import unicodedata
from pathlib import Path
from typing import Optional

import anthropic
from fastapi import HTTPException
from pydantic import ValidationError

from llm_client import call_claude
from models import RecommendationResponse, StructureBars, WineColor, WineRecommendation

logger = logging.getLogger("sommelier.recommender")

# Wine reference data for bar calibration — appellation+grape → reference bars (0.0–1.0 scale).
_REF_PATH = Path(__file__).resolve().parent / "data" / "wine_reference.json"
_WINE_REFERENCE: list[dict] = []
try:
    with _REF_PATH.open(encoding="utf-8") as _fh:
        _ref_data = json.load(_fh)
    _WINE_REFERENCE = _ref_data.get("entries", [])
    logger.debug("wine_reference loaded: %d entries", len(_WINE_REFERENCE))
except Exception as _ref_exc:
    logger.warning("wine_reference load failed: %s", _ref_exc)


def _normalize_ref(s: str) -> str:
    """Lowercase + strip combining diacritics for accent-insensitive reference matching."""
    nfkd = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


# Cache of the reference table pre-normalized to (norm_appellation, norm_grape, bars),
# so per-wine lookups don't re-run NFKD normalization across the whole table on every
# call. Rebuilt only when the source list object changes (e.g. tests monkeypatching
# _WINE_REFERENCE); in production it is computed once on first lookup and reused.
_norm_src: Optional[list] = None
_norm_reference: list[tuple[str, str, dict]] = []


def _get_norm_reference() -> list[tuple[str, str, dict]]:
    global _norm_src, _norm_reference
    if _WINE_REFERENCE is not _norm_src:
        _norm_src = _WINE_REFERENCE
        _norm_reference = [
            (
                _normalize_ref(e.get("appellation", "")),
                _normalize_ref(e.get("grape", "")),
                e.get("bars", {}),
            )
            for e in _WINE_REFERENCE
        ]
    return _norm_reference


def _find_reference_bars(appellation: Optional[str], grape: Optional[str]) -> Optional[dict]:
    """Return the best-matching reference bars dict (0.0–1.0 scale) for an appellation+grape pair."""
    norm_reference = _get_norm_reference()
    if not norm_reference:
        return None
    norm_app = _normalize_ref(appellation or "")
    norm_grape = _normalize_ref(grape or "")
    if norm_app and norm_grape:
        # Exact match on both fields
        for ref_app, ref_grape, bars in norm_reference:
            if ref_app == norm_app and ref_grape == norm_grape:
                return bars
        # Partial appellation match + exact grape
        for ref_app, ref_grape, bars in norm_reference:
            if ref_grape == norm_grape and (ref_app in norm_app or norm_app in ref_app):
                return bars
    # Appellation-only match (grape absent or unknown)
    if norm_app and not norm_grape:
        for ref_app, _ref_grape, bars in norm_reference:
            if ref_app and (ref_app == norm_app or ref_app in norm_app or norm_app in ref_app):
                return bars
    return None


def _blend_bars(claude_bars: dict, ref_bars: dict) -> dict:
    """50/50 blend of Claude's 0–10 bars with reference 0.0–1.0 bars (scaled ×10)."""
    keys = ["tannin", "acidity", "body", "sweetness", "oak"]
    return {k: round((float(claude_bars.get(k, 5)) + float(ref_bars.get(k, 0.5)) * 10) / 2, 1) for k in keys}


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

# Hex palette constants mirroring frontend tokens — used to derive WineColor server-side.
_PALETTE_BRUNELLO = WineColor(glass='#7d1f24', tint='#f4dcd3', ink='#3a0d10', accent='#9a2a30')
_PALETTE_BAROLO   = WineColor(glass='#8a2a2e', tint='#f3dad4', ink='#3d1014', accent='#a83339')
_PALETTE_CHABLIS  = WineColor(glass='#b8932a', tint='#f0e0a8', ink='#3d2e08', accent='#8a6e12')
_PALETTE_ROSE     = WineColor(glass='#c44a6a', tint='#f7d8e0', ink='#3d0a18', accent='#962e52')
_PALETTE_AMBER    = WineColor(glass='#a86420', tint='#eccfa0', ink='#3a1f05', accent='#7a4810')
_PALETTE_DEFAULT  = WineColor(glass='#7d1f24', tint='#f4dcd3', ink='#3a0d10', accent='#9a2a30')


def _derive_color(wine: WineRecommendation) -> WineColor:
    """Map grape / region / wine_name to a palette. Mirrors frontend derivePalette."""
    src = f"{wine.grape or ''} {wine.region or ''} {wine.wine_name}".lower()
    if any(k in src for k in ('sangiovese', 'brunello', 'chianti', 'montalcino')):
        return _PALETTE_BRUNELLO
    if any(k in src for k in ('nebbiolo', 'barolo', 'barbaresco', 'piedmont', 'piemonte')):
        return _PALETTE_BAROLO
    if any(k in src for k in ('rosé', 'rose', 'rosato', 'rosado', 'blush', 'tavel', 'provence')):
        return _PALETTE_ROSE
    if any(k in src for k in ('orange wine', 'skin contact', 'amber wine', 'ramato')):
        return _PALETTE_AMBER
    if any(k in src for k in ('chardonnay', 'chablis', 'bourgogne blanc', 'white', 'blanc',
                               'blanco', 'weiss', 'riesling', 'sauvignon blanc', 'pinot gris',
                               'pinot grigio', 'viognier', 'marsanne', 'roussanne', 'gruner')):
        return _PALETTE_CHABLIS
    return _PALETTE_DEFAULT


# Tool definition passed to Claude for structured output via tool use.
# Claude is forced to call this tool, returning a parsed dict directly —
# no JSON parsing or repair logic required.
_RECOMMENDATION_TOOL: dict = {
    "name": "provide_recommendations",
    "description": "Provide ranked wine recommendations.",
    "input_schema": {
        "type": "object",
        "properties": {
            "recommendations": {
                "type": "array",
                "description": "Ranked wine recommendations from the list, best-first.",
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
                        "fits": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": (
                                "Optional. 2-3 short tags (each <= 8 words) grounding this pick in the user's "
                                "taste profile. Each tag MUST reference a concrete signal that appears in the "
                                "profile above: a top region/varietal/producer, a preferred descriptor, an "
                                "avoided style, or a derived taste marker (acidity/tannin/body/oak). "
                                "Examples: 'Matches your high-acidity preference', "
                                "'Aligned with your top region: Northern Rhône', "
                                "'Avoids the oaky profile you down-rate'. "
                                "Omit the field entirely (do not return an empty array) if no clean signal applies."
                            ),
                        },
                        "evidence_quotes": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": (
                                "Optional. 1-2 short verbatim quotes from the TASTING NOTE LIBRARY that directly "
                                "justify this pick. Format each entry as: "
                                "'From your [Wine name] note: \"[verbatim quote]\"'. "
                                "ONLY include if the TASTING NOTE LIBRARY is present in the system prompt "
                                "AND you can find a genuine textual match — never fabricate or paraphrase. "
                                "Omit entirely if no library is provided or no clear connection exists."
                            ),
                        },
                        "stretch": {
                            "type": "boolean",
                            "description": (
                                "Set to true only when this pick is intentionally outside the safe persona zone "
                                "(the stretch/discovery slot, typically the final ranked pick). "
                                "Omit or set false for all other picks."
                            ),
                        },
                        # --- Phase 5 enrichment fields ---
                        "appellation": {
                            "type": "string",
                            "description": "Official appellation or designation (e.g. 'Brunello di Montalcino DOCG').",
                        },
                        "country": {
                            "type": "string",
                            "description": "Country of origin (e.g. 'Italy', 'France').",
                        },
                        "coords": {
                            "type": "object",
                            "description": "Approximate lat/lon of the wine's production region.",
                            "properties": {
                                "lat": {"type": "number"},
                                "lon": {"type": "number"},
                            },
                            "required": ["lat", "lon"],
                        },
                        "grape": {
                            "type": "string",
                            "description": "Primary grape variety (e.g. 'Sangiovese Grosso', 'Nebbiolo').",
                        },
                        "abv": {
                            "type": "number",
                            "description": "Alcohol by volume percentage (e.g. 14.5).",
                        },
                        "drink": {
                            "type": "object",
                            "description": "Estimated drinking window (integer years).",
                            "properties": {
                                "from":  {"type": "integer"},
                                "peak":  {"type": "integer"},
                                "until": {"type": "integer"},
                            },
                            "required": ["from", "peak", "until"],
                        },
                        "bars": {
                            "type": "object",
                            "description": "Structure bars — each value 0–10.",
                            "properties": {
                                "tannin":    {"type": "number"},
                                "acidity":   {"type": "number"},
                                "body":      {"type": "number"},
                                "sweetness": {"type": "number"},
                                "oak":       {"type": "number"},
                            },
                            "required": ["tannin", "acidity", "body", "sweetness", "oak"],
                        },
                        "wheel": {
                            "type": "object",
                            "description": "Aroma wheel: 6–8 entries, key = aroma descriptor, value = intensity 0–10.",
                            "additionalProperties": {"type": "number"},
                        },
                        "nose": {
                            "type": "string",
                            "description": "One concise sentence describing the aromatic profile.",
                        },
                        "palate": {
                            "type": "string",
                            "description": "One concise sentence describing the palate and finish.",
                        },
                        "pairs": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "2-4 food pairing suggestions (short, specific dish names).",
                        },
                        "critic": {
                            "type": "object",
                            "description": "Approximate critic score — omit if genuinely unknown.",
                            "properties": {
                                "score":  {"type": "number"},
                                "source": {"type": "string"},
                            },
                            "required": ["score", "source"],
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
    # Dev/test replay: if RECORDED_RESPONSES_DIR is set, serve a fixture JSON
    # instead of calling Claude. Useful for UI development without API spend.
    # Place one or more fixture files in the directory; the first alphabetically is served.
    _replay_dir_env = os.getenv("RECORDED_RESPONSES_DIR")
    if _replay_dir_env:
        _rdir = Path(_replay_dir_env)
        _fixtures = sorted(_rdir.glob("*.json"))
        if _fixtures:
            with _fixtures[0].open(encoding="utf-8") as _fh:
                _data = json.load(_fh)
            try:
                _replay_rec = RecommendationResponse(**_data)
            except ValidationError as _exc:
                raise ValueError(f"Replay fixture schema invalid: {_exc}") from _exc
            for _wine in _replay_rec.recommendations:
                if _wine.color is None:
                    _wine.color = _derive_color(_wine)
            logger.info("replay_mode_active fixture=%s", _fixtures[0].name)
            return _replay_rec

    client = anthropic.Anthropic(api_key=anthropic_api_key)

    content: list = []
    if image_b64:
        content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": "image/jpeg", "data": image_b64},
        })
    content.append({"type": "text", "text": text_payload})

    try:
        response = call_claude(
            "recommend",
            client,
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
            detail="Recommendation provider experienced an API error. Please try again.",
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

    # Derive palette hex values server-side — not asked of Claude to avoid hallucinated hex codes.
    # Also blend structure bars with reference data where a match exists.
    for wine in recommendation.recommendations:
        if wine.color is None:
            wine.color = _derive_color(wine)
        if wine.bars is not None:
            ref_bars = _find_reference_bars(wine.appellation, wine.grape)
            if ref_bars is not None:
                blended = _blend_bars(wine.bars.model_dump(), ref_bars)
                wine.bars = StructureBars(**blended)
                logger.debug(
                    "bars_blended wine=%s appellation=%s grape=%s",
                    wine.wine_name,
                    wine.appellation,
                    wine.grape,
                )

    logger.info("attempt=%d schema_validation_passed wines=%d", attempt, len(recommendation.recommendations))
    return recommendation


def get_recommendation(
    wine_list_text: str,
    meal: str,
    system_prompt: str,
    anthropic_api_key: str,
    anthropic_model: str,
    image_b64: Optional[str] = None,
    source_mode: str = "winelist",
) -> RecommendationResponse:
    """Get wine recommendation from Anthropic Claude.

    Retries up to _MAX_ATTEMPTS times on schema validation errors.

    Raises:
        HTTPException: On API failure or all attempts exhausted.
    """
    meal_line = f"Tonight's meal: {meal}" if meal else ""

    if source_mode == "cellar":
        user_prompt = (
            f"{meal_line}\n\n"
            "Task: survey every bottle in the CELLAR INVENTORY listed in the system prompt, "
            "score each against the taste profile, then select and rank the top bottles. "
            "Recommend ONLY bottles that appear in the CELLAR INVENTORY — "
            "do not hallucinate or invent wines. "
            "Return only the JSON response — no preamble."
        ).strip()
        text_payload = user_prompt
    else:
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
                detail="Recommendation provider failed. Please try again.",
            ) from exc

    logger.error("get_recommendation: all %d attempts failed, last_error=%s", _MAX_ATTEMPTS, last_err)
    raise HTTPException(
        status_code=502,
        detail=f"Recommendation provider failed after {_MAX_ATTEMPTS} attempts. Please try again.",
    )
