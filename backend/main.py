import base64
import hashlib
import json
import logging
import logging.handlers
import os
from pathlib import Path
import time
import uuid
from typing import Optional, Dict, Any

from fastapi import FastAPI, UploadFile, Form, File, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

import re
from collections import Counter

from inventory import (
    decode_cellartracker_upload,
    save_inventory,
    load_inventory,
    get_relevant_bottles,
    filter_wine_list,
)
from cache import init_db, make_key, inventory_hash, get_cached, set_cached, bust_cache, purge_expired
from prompt import build_system_prompt
from profile import save_profile_export, load_profile_data, build_taste_profile, build_taste_profile_pydantic, ingest_export, build_enriched_profile_text, extract_profile_preference_terms
from models import (
    InventoryResponse,
    UploadInventoryResponse,
    UploadProfileResponse,
    ProfileSummaryResponse,
    RecommendRequest,
    RecommendationResponse,
    Bottle
)
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

# Configure the "sommelier" parent logger so all child loggers
# (sommelier.api, sommelier.recommender, sommelier.profile, etc.)
# share the same file and stream handlers.
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

load_dotenv(_som_dir / ".env")
load_dotenv()
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama-gpu")
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
    text = decode_cellartracker_upload(await file.read())
    bottles = save_inventory(text)
    bust_cache()
    return UploadInventoryResponse(
        count=len(bottles), 
        message=f"Saved {len(bottles)} bottles. Response cache cleared."
    )

@app.post("/upload-profile")
async def upload_profile(file: UploadFile = File(...)) -> UploadProfileResponse:
    raw = await file.read()

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

@app.get("/inventory")
def get_inventory() -> InventoryResponse:
    inv = load_inventory()
    if not inv:
        return InventoryResponse(bottles=[], age_hours=None, stale=False)
    
    # Convert raw dicts to Bottle models
    bottles = [Bottle(**bottle) for bottle in inv.get("bottles", [])]
    return InventoryResponse(
        bottles=bottles,
        age_hours=inv.get("age_hours"),
        stale=inv.get("stale", False)
    )

@app.get("/profile-summary")
def profile_summary() -> ProfileSummaryResponse:
    profile_data = build_taste_profile(load_profile_data())
    return ProfileSummaryResponse(**profile_data)

@app.post("/recommend")
async def recommend(
    wine_list: UploadFile = File(...),
    meal: str = Form(...),
    style_terms: str = Form(default="")
) -> RecommendationResponse:
    """Recommend wines based on uploaded list and meal context."""
    inv = load_inventory()
    bottles = inv["bottles"] if inv else []
    profile_hash = hashlib.md5(json.dumps(load_profile_data(), sort_keys=True).encode()).hexdigest()

    raw_bytes = await wine_list.read()
    inv_hash = inventory_hash(bottles)
    cache_key = make_key(raw_bytes, meal, inv_hash, profile_hash)

    # Check cache
    cached_json = get_cached(cache_key)
    if cached_json:
        try:
            cached_data = json.loads(cached_json)
            return RecommendationResponse(**cached_data)
        except (json.JSONDecodeError, ValueError):
            logger.warning("cached response failed validation, regenerating")

    # Parse wine list — OCR images to text; fall back to multimodal only if OCR fails.
    from parser import OCRError
    media_type = (wine_list.content_type or "").lower()
    is_image_upload = media_type.startswith("image/") or any(
        (wine_list.filename or "").lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp"]
    )

    image_b64: Optional[str] = None
    try:
        wine_list_text = parse_wine_list(raw_bytes, wine_list.content_type, wine_list.filename)
    except OCRError as exc:
        # OCR failed — attempt multimodal path (requires a vision-capable Ollama model).
        # If the model is text-only this will also fail, but at least it won't silently
        # recommend from the cellar.
        logger.warning("recommend: OCR failed (%s); attempting multimodal fallback", exc)
        if is_image_upload:
            image_b64 = base64.standard_b64encode(raw_bytes).decode()
            wine_list_text = ""
        else:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    wine_list_hash = hashlib.md5(wine_list_text.encode()).hexdigest()[:8]
    taste_profile = build_taste_profile_pydantic(load_profile_data())

    # Remove invisible unicode characters (zero-width spaces, BOM, soft hyphens,
    # directional marks) that OCR/PDF extraction commonly produces, then strip
    # each line and drop blanks so the filter operates on genuinely clean text.
    _INVISIBLE_RE = re.compile(r"[\u00ad\u200b-\u200f\u202a-\u202e\u2060-\u2064\ufeff]")
    wine_list_text = _INVISIBLE_RE.sub("", wine_list_text)
    wine_list_text = "\n".join(
        line.strip() for line in wine_list_text.splitlines() if line.strip()
    )

    _before = len(wine_list_text.splitlines())
    wine_list_text = filter_wine_list(wine_list_text, taste_profile)
    # Final pass: drop any blank lines the filter may have re-introduced
    wine_list_text = "\n".join(
        line for line in wine_list_text.splitlines() if line.strip()
    )
    _after = len(wine_list_text.splitlines())
    logger.debug("wine_list_filter before=%d lines, after=%d lines", _before, _after)

    enriched_profile = None
    try:
        logger.info("recommend: attempting to build enriched profile with ollama_url=%s ollama_model=%s", OLLAMA_URL, OLLAMA_MODEL)
        enriched_profile = build_enriched_profile_text(OLLAMA_URL, OLLAMA_MODEL)
        # Safeguard: if enrichment produced an empty or suspicious result, discard it
        if not enriched_profile or len(enriched_profile) < 20:
            logger.warning("recommend: enriched profile is empty or too short (len=%d), falling back to standard profile", len(enriched_profile or ""))
            enriched_profile = None
        else:
            logger.info("recommend: enriched profile built successfully (len=%d)", len(enriched_profile))
            logger.debug("recommend: enriched profile (first 400 chars)=%s", enriched_profile[:400])
    except Exception as e:
        logger.warning("profile_enrichment_failed: %s", e, exc_info=True)
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
    system = build_system_prompt(relevant, cellar_summary=cellar_summary, taste_profile_override=enriched_profile, meal_hints=meal_hints)
    logger.info("recommend: system prompt built (len=%d)", len(system))
    logger.debug("recommend: system prompt (first 500 chars)=%s", system[:500])

    # Get recommendation from LLM
    try:
        recommendation = get_recommendation(
            wine_list_text, meal, system, OLLAMA_URL, OLLAMA_MODEL, image_b64
        )
        try:
            scoring_result = score_recommendation(recommendation, wine_list_text, taste_profile)
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
            detail=f"Recommendation provider failed: {type(exc).__name__}",
        ) from exc
