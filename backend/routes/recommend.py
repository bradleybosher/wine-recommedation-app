"""Wine recommendation route: parse wine list, enrich profile, call LLM, score."""
import hashlib
import json
import logging
import re

import anthropic
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile

from bootstrap import ANTHROPIC_API_KEY, ANTHROPIC_MODEL, MAX_UPLOAD_BYTES, TEST_MODE
from cache import (
    get_cached,
    get_parse_cached,
    inventory_hash,
    make_key,
    make_parse_key,
    save_flight,
    set_cached,
    set_parse_cached,
)
from cellar_terms import cellar_character_from_terms, inventory_terms_by_frequency
from dependencies import get_current_profile
from inventory import filter_wine_list, get_relevant_bottles, load_inventory
from logging_utils import log_recommendation_event
from meal_parser import meal_to_wine_hints, parse_meal_description
from models import Profile, RecommendationResponse
from parser import OCRError, parse_wine_list
from retrieval import rank_wine_list
from palate_stats import compute_palate_stats
from profile import (
    build_enriched_profile_text,
    build_taste_profile,
    build_taste_profile_pydantic,
    extract_profile_preference_terms,
    load_profile_data,
)
from prompt import build_system_prompt
from rate_limit import check_rate_limit
from recommender import get_recommendation
from scorer import _is_grounded, score_recommendation
from wine_reviews import enrich_critics
from test_fixtures import FIXTURES

router = APIRouter()
logger = logging.getLogger("sommelier.api")

_INVISIBLE_RE = re.compile(r"[­​-‏‪-‮⁠-⁤﻿]")


def _build_tasting_note_library(consumed_rows: list[dict], max_entries: int = 15) -> str:
    """Extract top-rated and bottom-rated tasting notes as a compact library for the prompt."""
    if not consumed_rows:
        return ""
    parsed = []
    for row in consumed_rows:
        note_text = (row.get("ConsumptionNote") or "").strip()
        if not note_text:
            continue
        score = None
        for field in ("CScore", "PScore"):
            raw = row.get(field)
            if raw:
                try:
                    score = float(str(raw).strip())
                    break
                except (ValueError, TypeError):
                    pass
        producer = (row.get("Producer") or "").strip()
        wine = (row.get("Wine") or "").strip()
        varietal = (row.get("MasterVarietal") or row.get("Varietal") or "").strip()
        region = (row.get("Region") or "").strip()
        label = f"{producer} {wine}".strip() or f"{varietal} {region}".strip() or "Unknown"
        parsed.append({"label": label, "varietal": varietal, "region": region, "score": score, "note": note_text})
    if not parsed:
        return ""
    scored = sorted([p for p in parsed if p["score"] is not None], key=lambda x: -x["score"])
    unscored = [p for p in parsed if p["score"] is None]
    ordered = scored + unscored
    seen: set[str] = set()
    deduped: list[dict] = []
    for p in ordered:
        key = f"{p['varietal'].lower()}|{p['region'].lower()}"
        if key not in seen:
            seen.add(key)
            deduped.append(p)
    n_top = max(5, max_entries * 2 // 3)
    top = deduped[:n_top]
    bottom_scored = sorted([p for p in deduped if p["score"] is not None], key=lambda x: x["score"])
    bottom = [p for p in bottom_scored[:4] if p not in top]
    selected = list({id(p): p for p in top + bottom}.values())
    lines: list[str] = []
    for p in selected:
        score_str = f" [{p['score']:.0f}pts]" if p["score"] is not None else ""
        excerpt = p["note"][:150].rstrip()
        if len(p["note"]) > 150:
            excerpt += "…"
        lines.append(f'- {p["label"]}{score_str}: "{excerpt}"')
    if not lines:
        return ""
    return (
        "**TASTING NOTE LIBRARY** (direct quotes from the user's own notes — "
        "cite these verbatim in evidence_quotes):\n" + "\n".join(lines)
    )


@router.post("/recommend")
async def recommend(
    request: Request,
    # Legacy fields — kept for backward compatibility during frontend cutover
    meal: str = Form(default=""),
    style_terms: str = Form(default=""),
    # New Preferences form fields (Phase 5)
    occasion: str = Form(default=""),
    menu: str = Form(default=""),
    cellar_leans: str = Form(default=""),
    temperament: str = Form(default=""),
    ceiling: str = Form(default=""),
    bottle_count: int = Form(default=3),
    source_mode: str = Form(default="winelist"),
    # File upload — optional when source_mode='cellar'
    wine_list: UploadFile = File(default=None),
    test_fixture: str = Form(default=""),
    profile: Profile = Depends(get_current_profile),
) -> RecommendationResponse:
    """Recommend wines based on uploaded list and meal context."""
    client_ip = request.client.host if request.client else "unknown"
    check_rate_limit(client_ip)

    # Compose effective meal/style from new fields, falling back to legacy fields
    effective_meal = f"{occasion} {menu}".strip() if (occasion or menu) else meal
    effective_style = f"{cellar_leans} {temperament}".strip() if (cellar_leans or temperament) else style_terms

    if TEST_MODE and test_fixture:
        if wine_list:
            await wine_list.read()
        fixture = FIXTURES.get(test_fixture)
        if fixture is None:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown test fixture: {test_fixture}. Available: {sorted(FIXTURES)}",
            )
        logger.info("recommend: TEST_MODE active, returning fixture=%s", test_fixture)
        return fixture

    use_wine_list = source_mode != "cellar" and wine_list is not None
    override_terms = [t.strip() for t in effective_style.split(",") if t.strip()]

    if not use_wine_list and source_mode != "cellar":
        raise HTTPException(status_code=422, detail="A wine list file is required unless source_mode is 'cellar'.")

    inv = load_inventory(profile.id)
    bottles = inv["bottles"] if inv else []
    profile_data_raw = load_profile_data(profile.id)
    profile_hash = hashlib.md5(
        json.dumps(profile_data_raw, sort_keys=True).encode()
    ).hexdigest()

    raw_bytes = b""
    wine_list_text = ""
    wine_list_hash = "no-list"

    if use_wine_list:
        raw_bytes = await wine_list.read()
        if len(raw_bytes) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="File too large. Maximum size is 20 MB.")

    inv_hash = inventory_hash(bottles)
    # Include bottle_count and ceiling in cache key — they affect LLM output
    cache_discriminator = f"{effective_meal}|{bottle_count}|{ceiling}"
    cache_key = make_key(raw_bytes, cache_discriminator, inv_hash, profile_hash)

    cached_json = get_cached(cache_key)
    if cached_json:
        try:
            cached_data = json.loads(cached_json)
            return RecommendationResponse(**cached_data)
        except (json.JSONDecodeError, ValueError):
            logger.warning("cached response failed validation, regenerating")

    if use_wine_list:
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
        taste_profile = build_taste_profile_pydantic(profile_data_raw)

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

        wine_list_text = rank_wine_list(wine_list_text, taste_profile, override_terms=override_terms)
    else:
        taste_profile = build_taste_profile_pydantic(profile_data_raw)
        logger.info("recommend: source_mode=cellar, skipping wine list parsing")

    enriched_profile = None
    try:
        logger.info(
            "recommend: attempting to build enriched profile with anthropic_model=%s",
            ANTHROPIC_MODEL,
        )
        enriched_profile = build_enriched_profile_text(profile.id, ANTHROPIC_API_KEY, ANTHROPIC_MODEL)
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
    terms = override_terms if override_terms else inventory_terms_by_frequency(bottles, limit=10)
    logger.info(
        "recommend_terms source=%s terms=%s",
        "override" if override_terms else "derived",
        terms,
    )
    profile_prefs = extract_profile_preference_terms(profile_data_raw)
    relevant = get_relevant_bottles(bottles, terms, profile_prefs)

    meal_hints = meal_to_wine_hints(parse_meal_description(effective_meal))
    structured_profile = build_taste_profile(profile_data_raw)
    taste_markers_dict = structured_profile.get("taste_markers") if isinstance(structured_profile.get("taste_markers"), dict) else None
    palate_persona_text = structured_profile.get("palate_persona") if isinstance(structured_profile.get("palate_persona"), str) else None

    # Tasting note library + aspirational skew — derived from CellarTracker consumed rows
    tasting_note_library = ""
    aspirational_skew_line = ""
    consumed_rows = profile_data_raw.get("consumed", [])
    if consumed_rows:
        try:
            tasting_note_library = _build_tasting_note_library(consumed_rows)
            palate_stats_data = compute_palate_stats(
                consumed_rows=consumed_rows,
                inventory_rows=bottles,
            )
            asp = palate_stats_data.get("aspirational_skew")
            if asp and asp.get("summary_line"):
                aspirational_skew_line = asp["summary_line"]
        except Exception as stats_err:
            logger.warning("palate_stats_for_prompt_failed: %s", stats_err)

    system = build_system_prompt(
        relevant,
        cellar_summary=cellar_summary,
        taste_profile_override=enriched_profile,
        meal_hints=meal_hints,
        profile_source=taste_profile.profile_source,
        bottle_count=bottle_count,
        budget_ceiling=ceiling,
        taste_markers=taste_markers_dict,
        palate_persona=palate_persona_text,
        source_mode=source_mode,
        tasting_note_library=tasting_note_library,
        aspirational_skew=aspirational_skew_line,
    )
    logger.info("recommend: system prompt built (len=%d)", len(system))
    logger.debug("recommend: system prompt (first 500 chars)=%s", system[:500])

    try:
        recommendation = get_recommendation(
            wine_list_text, effective_meal, system, ANTHROPIC_API_KEY, ANTHROPIC_MODEL,
            source_mode=source_mode,
        )
        try:
            enrich_critics(recommendation)
        except Exception as critic_err:
            logger.warning("critic_enrichment_failed: %s", critic_err)
        if source_mode == "winelist":
            for rec in recommendation.recommendations:
                rec.verified_on_list = _is_grounded(rec.wine_name, wine_list_text)

        try:
            scoring_result = score_recommendation(
                recommendation, wine_list_text, taste_profile,
                cap_confidence=(taste_profile.profile_source == "seed_bottles"),
            )
            log_recommendation_event(effective_meal, profile_hash, recommendation, scoring_result, wine_list_hash)
        except Exception as score_err:
            logger.exception("scoring_and_logging_failed: %s", score_err)
        flight_id = None
        try:
            flight_id = save_flight(
                occasion=occasion,
                menu=menu,
                cellar_leans=cellar_leans,
                temperament=temperament,
                ceiling=ceiling,
                bottle_count=bottle_count,
                source_mode=source_mode,
                wine_list_hash=wine_list_hash,
                profile_hash=profile_hash,
                response=recommendation,
                profile_id=profile.id,
            )
        except Exception as hist_err:
            logger.warning("auto_save_flight_failed: %s", hist_err)
        # Cache before attaching flight_id so the id isn't replayed on cache hits
        set_cached(cache_key, recommendation.model_dump_json())
        if flight_id:
            recommendation.flight_id = flight_id
        return recommendation
    except HTTPException as exc:
        log_recommendation_event(effective_meal, profile_hash, None, None, wine_list_hash, error=str(exc.detail))
        raise
    except Exception as exc:
        log_recommendation_event(
            effective_meal, profile_hash, None, None, wine_list_hash,
            error=f"{type(exc).__name__}: {exc}",
        )
        logger.exception("recommend_provider_error error=%s", type(exc).__name__)
        raise HTTPException(
            status_code=502,
            detail="Recommendation provider failed. Please try again.",
        ) from exc
