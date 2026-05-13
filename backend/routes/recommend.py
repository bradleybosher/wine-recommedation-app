"""Wine recommendation route: parse wine list, enrich profile, call LLM, score."""
import hashlib
import json
import logging
import re

import anthropic
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from bootstrap import ANTHROPIC_API_KEY, ANTHROPIC_MODEL, MAX_UPLOAD_BYTES
from cache import (
    get_cached,
    get_parse_cached,
    inventory_hash,
    make_key,
    make_parse_key,
    set_cached,
    set_parse_cached,
)
from cellar_terms import cellar_character_from_terms, inventory_terms_by_frequency
from inventory import filter_wine_list, get_relevant_bottles, load_inventory
from logging_utils import log_recommendation_event
from meal_parser import meal_to_wine_hints, parse_meal_description
from models import RecommendationResponse
from parser import OCRError, parse_wine_list
from profile import (
    build_enriched_profile_text,
    build_taste_profile_pydantic,
    extract_profile_preference_terms,
    load_profile_data,
)
from prompt import build_system_prompt
from rate_limit import check_rate_limit
from recommender import get_recommendation
from scorer import score_recommendation

router = APIRouter()
logger = logging.getLogger("sommelier.api")

_INVISIBLE_RE = re.compile(r"[­​-‏‪-‮⁠-⁤﻿]")


@router.post("/recommend")
async def recommend(
    request: Request,
    wine_list: UploadFile = File(...),
    meal: str = Form(...),
    style_terms: str = Form(default=""),
) -> RecommendationResponse:
    """Recommend wines based on uploaded list and meal context."""
    client_ip = request.client.host if request.client else "unknown"
    check_rate_limit(client_ip)

    inv = load_inventory()
    bottles = inv["bottles"] if inv else []
    profile_hash = hashlib.md5(
        json.dumps(load_profile_data(), sort_keys=True).encode()
    ).hexdigest()

    raw_bytes = await wine_list.read()
    if len(raw_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 20 MB.")
    inv_hash = inventory_hash(bottles)
    cache_key = make_key(raw_bytes, meal, inv_hash, profile_hash)

    cached_json = get_cached(cache_key)
    if cached_json:
        try:
            cached_data = json.loads(cached_json)
            return RecommendationResponse(**cached_data)
        except (json.JSONDecodeError, ValueError):
            logger.warning("cached response failed validation, regenerating")

    # Parse wine list — keyed by file bytes only, independent of meal/profile.
    parse_key = make_parse_key(raw_bytes)
    wine_list_text = get_parse_cached(parse_key)
    if wine_list_text:
        logger.info("recommend: parse cache hit, skipping vision extraction")
    else:
        try:
            wine_list_text = parse_wine_list(raw_bytes, wine_list.content_type, wine_list.filename)
        except OCRError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        set_parse_cached(parse_key, wine_list_text)

    wine_list_hash = hashlib.md5(wine_list_text.encode()).hexdigest()[:8]
    taste_profile = build_taste_profile_pydantic(load_profile_data())

    wine_list_text = _INVISIBLE_RE.sub("", wine_list_text)
    wine_list_text = "\n".join(
        line.strip() for line in wine_list_text.splitlines() if line.strip()
    )

    before = len(wine_list_text.splitlines())
    wine_list_text = filter_wine_list(wine_list_text, taste_profile)
    wine_list_text = "\n".join(
        line for line in wine_list_text.splitlines() if line.strip()
    )
    after = len(wine_list_text.splitlines())
    logger.debug("wine_list_filter before=%d lines, after=%d lines", before, after)

    enriched_profile = None
    try:
        logger.info(
            "recommend: attempting to build enriched profile with anthropic_model=%s",
            ANTHROPIC_MODEL,
        )
        enriched_profile = build_enriched_profile_text(ANTHROPIC_API_KEY, ANTHROPIC_MODEL)
        if not enriched_profile or len(enriched_profile) < 20:
            logger.warning(
                "recommend: enriched profile is empty or too short (len=%d), falling back to standard profile",
                len(enriched_profile or ""),
            )
            enriched_profile = None
        else:
            logger.info("recommend: enriched profile built successfully (len=%d)", len(enriched_profile))
            logger.debug("recommend: enriched profile (first 400 chars)=%s", enriched_profile[:400])
    except anthropic.APIError as e:
        logger.warning("profile_enrichment_api_error: %s %s", type(e).__name__, e)
        enriched_profile = None
    except (ValueError, RuntimeError) as e:
        logger.warning("profile_enrichment_failed: %s %s", type(e).__name__, e)
        enriched_profile = None
    except Exception as e:
        logger.exception("profile_enrichment_unexpected: %s", type(e).__name__)
        enriched_profile = None

    if enriched_profile is None:
        logger.info("recommend: using standard profile (enrichment not available)")

    top5_terms = inventory_terms_by_frequency(bottles, limit=5)
    cellar_summary = cellar_character_from_terms(top5_terms)
    override_terms = [t.strip() for t in style_terms.split(",") if t.strip()]
    terms = override_terms if override_terms else inventory_terms_by_frequency(bottles, limit=10)
    logger.info(
        "recommend_terms source=%s terms=%s",
        "override" if override_terms else "derived",
        terms,
    )
    profile_prefs = extract_profile_preference_terms(load_profile_data())
    relevant = get_relevant_bottles(bottles, terms, profile_prefs)

    meal_hints = meal_to_wine_hints(parse_meal_description(meal))
    system = build_system_prompt(
        relevant,
        cellar_summary=cellar_summary,
        taste_profile_override=enriched_profile,
        meal_hints=meal_hints,
        profile_source=taste_profile.profile_source,
    )
    logger.info("recommend: system prompt built (len=%d)", len(system))
    logger.debug("recommend: system prompt (first 500 chars)=%s", system[:500])

    try:
        recommendation = get_recommendation(
            wine_list_text, meal, system, ANTHROPIC_API_KEY, ANTHROPIC_MODEL
        )
        try:
            scoring_result = score_recommendation(
                recommendation, wine_list_text, taste_profile,
                cap_confidence=(taste_profile.profile_source == "seed_bottles"),
            )
            log_recommendation_event(meal, profile_hash, recommendation, scoring_result, wine_list_hash)
        except Exception as score_err:
            logger.exception("scoring_and_logging_failed: %s", score_err)
        set_cached(cache_key, recommendation.model_dump_json())
        return recommendation
    except HTTPException as exc:
        log_recommendation_event(meal, profile_hash, None, None, wine_list_hash, error=str(exc.detail))
        raise
    except Exception as exc:
        log_recommendation_event(
            meal, profile_hash, None, None, wine_list_hash,
            error=f"{type(exc).__name__}: {exc}",
        )
        logger.exception("recommend_provider_error error=%s", type(exc).__name__)
        raise HTTPException(
            status_code=502,
            detail="Recommendation provider failed. Please try again.",
        ) from exc
