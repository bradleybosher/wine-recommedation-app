import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env before any module that reads env vars at import time
_som_dir_early = Path(__file__).parent
load_dotenv(_som_dir_early / ".env")
load_dotenv()

import anthropic
import base64
import hashlib
import json
import logging
import logging.handlers
import re
import time
import uuid
from collections import Counter, defaultdict
from typing import Optional, Dict, Any

from fastapi import FastAPI, UploadFile, Form, File, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from inventory import (
    decode_cellartracker_upload,
    save_inventory,
    load_inventory,
    get_relevant_bottles,
    filter_wine_list,
)
from cache import init_db, make_key, inventory_hash, get_cached, set_cached, bust_cache, purge_expired, make_parse_key, get_parse_cached, set_parse_cached
from prompt import build_system_prompt
from profile import save_profile_export, load_profile_data, build_taste_profile, build_taste_profile_pydantic, ingest_export, build_enriched_profile_text, extract_profile_preference_terms, enrich_profile_with_anthropic, derive_taste_markers, bust_profile_cache
from models import (
    InventoryResponse,
    UploadInventoryResponse,
    UploadProfileResponse,
    ProfileSummaryResponse,
    TasteMarkers,
    CellarStats,
    RecommendRequest,
    RecommendationResponse,
    Bottle,
    SeedProfileRequest,
)
from seed_profile import infer_profile_from_seeds, persist_seed_profile, load_inferred_profile
from meal_parser import parse_meal_description, meal_to_wine_hints
from parser import parse_wine_list
from recommender import get_recommendation
from scorer import score_recommendation
from logging_utils import log_recommendation_event

# Import debug routes
from routes.debug import router as debug_router

_som_dir = Path(__file__).resolve().parent
_log_dir = _som_dir / "logs"
_log_dir.mkdir(parents=True, exist_ok=True)
_log_path = _log_dir / "api.log"

_root_logger = logging.getLogger("sommelier")
if not _root_logger.handlers:
    _root_logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s"
    )
    file_handler = logging.handlers.RotatingFileHandler(
        _log_path, maxBytes=1_000_000, backupCount=2, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    _root_logger.addHandler(file_handler)
    _root_logger.addHandler(logging.StreamHandler())

logger = logging.getLogger("sommelier.api")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY environment variable is not set. Add it to backend/.env")

app = FastAPI()

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
init_db()
n = purge_expired()
logger.info("cache_purge_on_startup expired_entries=%d", n)

# Include debug routes
app.include_router(debug_router)

_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z\-']+")
_STOPWORDS = {
    "and", "the", "de", "du", "des", "di", "della", "delle", "del", "la", "le",
    "a", "to", "in", "for", "with", "sur", "superiore", "classico", "unknown",
    "rosso", "bianco", "blanc", "noir", "wine", "wines",
}

# Upload size limits
_MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # 20 MB

# Rate limiting
_RATE_LIMIT_MAX = 10  # requests per window
_RATE_LIMIT_WINDOW = 60  # seconds
_rate_counts: dict[str, list[float]] = defaultdict(list)


def _check_rate_limit(ip: str) -> None:
    """Check if client IP has exceeded rate limit. Raises HTTPException(429) if exceeded."""
    now = time.time()
    window_start = now - _RATE_LIMIT_WINDOW
    timestamps = [t for t in _rate_counts[ip] if t > window_start]
    if len(timestamps) >= _RATE_LIMIT_MAX:
        raise HTTPException(status_code=429, detail="Too many requests. Please wait before trying again.")
    timestamps.append(now)
    _rate_counts[ip] = timestamps


def _value_or_empty(v: object) -> str:
    return str(v or "").strip()


def _inventory_terms_by_frequency(bottles: list[dict], limit: int = 10) -> list[str]:
    counts: Counter[str] = Counter()
    for bottle in bottles:
        for field in ("Varietal", "Appellation"):
            raw = _value_or_empty(bottle.get(field))
            if not raw:
                continue
            normalized = raw.lower()
            counts[normalized] += 3
            for token in _TOKEN_RE.findall(normalized):
                if len(token) < 3 or token in _STOPWORDS:
                    continue
                counts[token] += 1
    return [term for term, _ in counts.most_common(limit)]


def _display_term(term: str) -> str:
    return " ".join(w.capitalize() for w in term.replace("-", " ").split())


def _cellar_character_from_terms(terms: list[str]) -> str:
    """Sentence fragment for Owner's cellar character (top terms from Varietal + Appellation)."""
    t = terms[:5]
    if not t:
        return ""
    if len(t) == 1:
        return f"skews heavily toward {_display_term(t[0])}."
    if len(t) == 2:
        return f"skews heavily toward {_display_term(t[0])} and {_display_term(t[1])}."
    if len(t) == 3:
        return (
            f"skews heavily toward {_display_term(t[0])}, {_display_term(t[1])}, "
            f"and {_display_term(t[2])}."
        )
    if len(t) == 4:
        return (
            f"skews heavily toward {_display_term(t[0])} and {_display_term(t[1])}, "
            f"with strong {_display_term(t[2])} and {_display_term(t[3])} representation."
        )
    return (
        f"skews heavily toward {_display_term(t[0])} and {_display_term(t[1])}, "
        f"with strong {_display_term(t[2])}, {_display_term(t[3])}, and {_display_term(t[4])} representation."
    )


@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    start = time.perf_counter()
    client_ip = request.client.host if request.client else "unknown"
    logger.info(
        "request_start id=%s method=%s path=%s ip=%s",
        request_id,
        request.method,
        request.url.path,
        client_ip,
    )
    try:
        response = await call_next(request)
    except Exception:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        logger.exception(
            "request_error id=%s method=%s path=%s elapsed_ms=%s",
            request_id,
            request.method,
            request.url.path,
            elapsed_ms,
        )
        raise

    elapsed_ms = int((time.perf_counter() - start) * 1000)
    logger.info(
        "request_end id=%s method=%s path=%s status=%s elapsed_ms=%s",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Preserve status codes and bodies for intentional HTTP errors (e.g. 502 from /recommend)."""
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("unhandled_exception path=%s err=%s", request.url.path, type(exc).__name__)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error_type": type(exc).__name__},
    )


@app.post("/upload-inventory")
async def upload_inventory(file: UploadFile = File(...)) -> UploadInventoryResponse:
    raw = await file.read()
    if len(raw) > _MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"File too large. Maximum size is 20 MB.")
    text = decode_cellartracker_upload(raw)
    bottles = save_inventory(text)
    bust_cache()
    return UploadInventoryResponse(
        count=len(bottles),
        message=f"Saved {len(bottles)} bottles. Response cache cleared."
    )

@app.post("/upload-profile")
async def upload_profile(file: UploadFile = File(...)) -> UploadProfileResponse:
    raw = await file.read()
    if len(raw) > _MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"File too large. Maximum size is 20 MB.")

    try:
        export_type, rows = ingest_export(raw)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not parse file: {exc}")

    if len(rows) == 0:
        raise HTTPException(status_code=400, detail="File appears empty or contains no wine data")

    save_profile_export(raw)
    bust_cache()

    profile_data = load_profile_data()
    taste_profile = build_taste_profile_pydantic(profile_data)

    return UploadProfileResponse(
        export_type=export_type,
        message=f"Profile loaded: {len(rows)} rows from '{export_type}' export. Response cache cleared.",
        taste_profile=taste_profile,
    )

@app.post("/seed-profile")
async def seed_profile(req: SeedProfileRequest) -> UploadProfileResponse:
    """Infer a taste profile from 3-7 loved (and 0-3 disliked) seed wines.

    Alternative to /upload-profile for users without a CellarTracker account.
    Wipes any existing profile_data.json so sources never silently mix.
    """
    try:
        inferred = infer_profile_from_seeds(req, ANTHROPIC_API_KEY, ANTHROPIC_MODEL)
    except anthropic_module_error_types() as exc:
        logger.exception("seed_profile_inference_failed err=%s", type(exc).__name__)
        raise HTTPException(status_code=502, detail=f"Seed-profile inference failed: {type(exc).__name__}")

    persist_seed_profile(inferred)
    bust_cache()

    profile_data = load_profile_data()
    taste_profile = build_taste_profile_pydantic(profile_data)

    return UploadProfileResponse(
        export_type="seed_bottles",
        message=(
            f"Profile inferred from {len(req.loved)} loved and {len(req.disliked)} disliked wines. "
            f"Inference confidence: {inferred.get('inference_confidence', 'medium')}. Response cache cleared."
        ),
        taste_profile=taste_profile,
    )


def anthropic_module_error_types() -> tuple[type, ...]:
    """Tuple of exception types to catch around the seed-profile Anthropic call."""
    import anthropic as _a
    return (_a.APIError, RuntimeError, ValueError)


@app.post("/profile/revert")
async def revert_profile() -> dict:
    """Restore profile_data.json from the last backup created by /seed-profile.

    Returns 404 if no backup exists.
    """
    from profile import PROFILE_DATA_PATH
    backup_path = PROFILE_DATA_PATH.with_suffix(".backup.json")
    if not backup_path.is_file():
        raise HTTPException(status_code=404, detail="No profile backup found. Nothing to revert.")
    backup_text = backup_path.read_text(encoding="utf-8")
    PROFILE_DATA_PATH.write_text(backup_text, encoding="utf-8")
    bust_profile_cache()
    bust_cache()
    logger.info("profile_revert: restored from %s", backup_path)
    return {"message": "Profile reverted to backup successfully. Response cache cleared."}


@app.get("/inventory")
def get_inventory() -> InventoryResponse:
    inv = load_inventory()
    if not inv:
        return InventoryResponse(bottles=[], age_hours=None, stale=False)

    bottles = [Bottle(**bottle) for bottle in inv.get("bottles", [])]
    return InventoryResponse(
        bottles=bottles,
        age_hours=inv.get("age_hours"),
        stale=inv.get("stale", False)
    )

@app.get("/profile-summary")
def profile_summary() -> ProfileSummaryResponse:
    profile_data = build_taste_profile(load_profile_data())

    is_seed_derived = profile_data.get("profile_source") == "seed_bottles"

    if is_seed_derived and isinstance(profile_data.get("taste_markers"), dict):
        taste_markers = TasteMarkers(**profile_data["taste_markers"])
    else:
        markers_dict = derive_taste_markers(profile_data.get("preferred_descriptors", []))
        taste_markers = TasteMarkers(**markers_dict)

    inv = load_inventory() or {}
    raw_bottles = inv.get("bottles", [])
    vintages = [
        int(b["vintage"]) for b in raw_bottles
        if str(b.get("vintage", "")).strip().isdigit()
    ]
    cellar_stats = CellarStats(
        total_bottles=sum(int(b.get("quantity", 1) or 1) for b in raw_bottles),
        unique_wines=len(raw_bottles),
        vintage_oldest=min(vintages) if vintages else None,
        vintage_newest=max(vintages) if vintages else None,
    )

    style_summary: Optional[str] = None
    if is_seed_derived:
        raw_summary = profile_data.get("style_summary", "") or ""
        style_summary = raw_summary.strip() or None
    else:
        try:
            enriched = enrich_profile_with_anthropic(profile_data, ANTHROPIC_API_KEY, ANTHROPIC_MODEL)
            raw_summary = enriched.get("style_summary", "")
            style_summary = raw_summary.strip() or None
        except anthropic.APIError as exc:
            logger.warning("profile_summary_enrichment_api_error: %s %s", type(exc).__name__, exc)
        except (ValueError, RuntimeError) as exc:
            logger.warning("profile_summary_enrichment_failed: %s %s", type(exc).__name__, exc)
        except Exception as exc:
            logger.exception("profile_summary_enrichment_unexpected: %s", type(exc).__name__)

    # ProfileSummaryResponse expects only its declared fields — strip enrichment-only keys
    # from profile_data before splatting so Pydantic doesn't reject extras.
    summary_fields = {
        k: profile_data.get(k)
        for k in (
            "top_varietals", "top_regions", "top_producers", "highly_rated",
            "preferred_descriptors", "avoided_styles", "avg_spend",
        )
    }

    return ProfileSummaryResponse(
        **{k: v for k, v in summary_fields.items() if v is not None},
        style_summary=style_summary,
        taste_markers=taste_markers,
        cellar_stats=cellar_stats,
        profile_source=profile_data.get("profile_source", "cellartracker"),
        inference_confidence=profile_data.get("inference_confidence") if is_seed_derived else None,
        seed_bottle_count=profile_data.get("seed_bottle_count") if is_seed_derived else None,
    )

@app.post("/recommend")
async def recommend(
    request: Request,
    wine_list: UploadFile = File(...),
    meal: str = Form(...),
    style_terms: str = Form(default="")
) -> RecommendationResponse:
    """Recommend wines based on uploaded list and meal context."""
    client_ip = request.client.host if request.client else "unknown"
    _check_rate_limit(client_ip)

    inv = load_inventory()
    bottles = inv["bottles"] if inv else []
    profile_hash = hashlib.md5(json.dumps(load_profile_data(), sort_keys=True).encode()).hexdigest()

    raw_bytes = await wine_list.read()
    if len(raw_bytes) > _MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"File too large. Maximum size is 20 MB.")
    inv_hash = inventory_hash(bottles)
    cache_key = make_key(raw_bytes, meal, inv_hash, profile_hash)

    cached_json = get_cached(cache_key)
    if cached_json:
        try:
            cached_data = json.loads(cached_json)
            return RecommendationResponse(**cached_data)
        except (json.JSONDecodeError, ValueError):
            logger.warning("cached response failed validation, regenerating")

    # Parse wine list — check parse cache first (keyed by file bytes only, independent of meal/profile).
    from parser import OCRError
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

    _INVISIBLE_RE = re.compile(r"[­​-‏‪-‮⁠-⁤﻿]")
    wine_list_text = _INVISIBLE_RE.sub("", wine_list_text)
    wine_list_text = "\n".join(
        line.strip() for line in wine_list_text.splitlines() if line.strip()
    )

    _before = len(wine_list_text.splitlines())
    wine_list_text = filter_wine_list(wine_list_text, taste_profile)
    wine_list_text = "\n".join(
        line for line in wine_list_text.splitlines() if line.strip()
    )
    _after = len(wine_list_text.splitlines())
    logger.debug("wine_list_filter before=%d lines, after=%d lines", _before, _after)

    enriched_profile = None
    try:
        logger.info("recommend: attempting to build enriched profile with anthropic_model=%s", ANTHROPIC_MODEL)
        enriched_profile = build_enriched_profile_text(ANTHROPIC_API_KEY, ANTHROPIC_MODEL)
        if not enriched_profile or len(enriched_profile) < 20:
            logger.warning("recommend: enriched profile is empty or too short (len=%d), falling back to standard profile", len(enriched_profile or ""))
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

    top5_terms = _inventory_terms_by_frequency(bottles, limit=5)
    cellar_summary = _cellar_character_from_terms(top5_terms)
    override_terms = [t.strip() for t in style_terms.split(",") if t.strip()]
    terms = override_terms if override_terms else _inventory_terms_by_frequency(bottles, limit=10)
    logger.info("recommend_terms source=%s terms=%s", "override" if override_terms else "derived", terms)
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
        log_recommendation_event(meal, profile_hash, None, None, wine_list_hash, error=f"{type(exc).__name__}: {exc}")
        logger.exception("recommend_provider_error error=%s", type(exc).__name__)
        raise HTTPException(
            status_code=502,
            detail="Recommendation provider failed. Please try again.",
        ) from exc
