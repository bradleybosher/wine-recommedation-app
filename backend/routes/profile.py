"""Profile routes: upload CellarTracker export, infer from seed bottles,
revert from backup, patch user edits, and summarise current taste profile."""
import json
import logging
from typing import Optional

import anthropic
from fastapi import APIRouter, File, HTTPException, UploadFile

from bootstrap import ANTHROPIC_API_KEY, ANTHROPIC_MODEL, MAX_UPLOAD_BYTES
from cache import bust_cache
from inventory import load_inventory
from models import (
    CellarStats,
    ProfilePatchRequest,
    ProfileSummaryResponse,
    SeedProfileRequest,
    TasteMarkers,
    UploadProfileResponse,
)
from profile import (
    PROFILE_DATA_PATH,
    build_taste_profile,
    build_taste_profile_pydantic,
    bust_profile_cache,
    clear_synthesized_profile,
    derive_taste_markers,
    enrich_profile_with_anthropic,
    ingest_export,
    load_profile_data,
    persist_synthesized_profile,
    save_profile_export,
    synthesize_palate_from_notes,
)
from seed_profile import infer_profile_from_seeds, persist_seed_profile

router = APIRouter()
logger = logging.getLogger("sommelier.api")

_SEED_INFERENCE_ERRORS = (anthropic.APIError, RuntimeError, ValueError)
_SYNTHESIS_ERRORS = _SEED_INFERENCE_ERRORS


def _clear_profile_overrides() -> None:
    """Remove any user-edit overrides from profile_data.json.

    Called after /upload-profile or /seed-profile fully replaces the underlying
    profile state — manual edits to the previous profile no longer apply.
    """
    data = load_profile_data()
    if "_overrides" not in data:
        return
    data.pop("_overrides", None)
    PROFILE_DATA_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    bust_profile_cache()


@router.post("/upload-profile")
async def upload_profile(file: UploadFile = File(...)) -> UploadProfileResponse:
    raw = await file.read()
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 20 MB.")

    try:
        export_type, rows = ingest_export(raw)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not parse file: {exc}")

    if len(rows) == 0:
        raise HTTPException(status_code=400, detail="File appears empty or contains no wine data")

    save_profile_export(raw)
    _clear_profile_overrides()
    clear_synthesized_profile()
    bust_cache()

    profile_data = load_profile_data()
    synthesis_status = "skipped"
    try:
        synthesized = synthesize_palate_from_notes(profile_data, ANTHROPIC_API_KEY, ANTHROPIC_MODEL)
        if synthesized:
            persist_synthesized_profile(synthesized)
            profile_data = load_profile_data()
            synthesis_status = f"synthesized (confidence: {synthesized.get('inference_confidence', 'unknown')})"
    except _SYNTHESIS_ERRORS as exc:
        logger.exception("upload_profile_synthesis_failed err=%s", type(exc).__name__)
        synthesis_status = "failed (deterministic fallback active)"
    except Exception as exc:
        logger.exception("upload_profile_synthesis_unexpected err=%s", type(exc).__name__)
        synthesis_status = "failed (deterministic fallback active)"

    taste_profile = build_taste_profile_pydantic(profile_data)

    return UploadProfileResponse(
        export_type=export_type,
        message=(
            f"Profile loaded: {len(rows)} rows from '{export_type}' export. "
            f"Palate synthesis: {synthesis_status}. Response cache cleared."
        ),
        taste_profile=taste_profile,
    )


@router.post("/seed-profile")
async def seed_profile(req: SeedProfileRequest) -> UploadProfileResponse:
    """Infer a taste profile from 3-7 loved (and 0-3 disliked) seed wines.

    Alternative to /upload-profile for users without a CellarTracker account.
    Wipes any existing profile_data.json so sources never silently mix.
    """
    try:
        inferred = infer_profile_from_seeds(req, ANTHROPIC_API_KEY, ANTHROPIC_MODEL)
    except _SEED_INFERENCE_ERRORS as exc:
        logger.exception("seed_profile_inference_failed err=%s", type(exc).__name__)
        raise HTTPException(
            status_code=502,
            detail=f"Seed-profile inference failed: {type(exc).__name__}",
        )

    persist_seed_profile(inferred)
    _clear_profile_overrides()
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


@router.post("/profile/revert")
async def revert_profile() -> dict:
    """Restore profile_data.json from the last backup created by /seed-profile.

    Returns 404 if no backup exists.
    """
    backup_path = PROFILE_DATA_PATH.with_suffix(".backup.json")
    if not backup_path.is_file():
        raise HTTPException(status_code=404, detail="No profile backup found. Nothing to revert.")
    backup_text = backup_path.read_text(encoding="utf-8")
    PROFILE_DATA_PATH.write_text(backup_text, encoding="utf-8")
    bust_profile_cache()
    bust_cache()
    logger.info("profile_revert: restored from %s", backup_path)
    return {"message": "Profile reverted to backup successfully. Response cache cleared."}


@router.get("/profile-summary")
def profile_summary() -> ProfileSummaryResponse:
    profile_data = build_taste_profile(load_profile_data())

    is_seed_derived = profile_data.get("profile_source") == "seed_bottles"
    is_synthesized = profile_data.get("profile_source") == "cellartracker_synthesized"

    # An explicit taste_markers dict (seed inference OR user override on a CT profile)
    # wins verbatim. Otherwise fall back to heuristic derivation from descriptors.
    markers_value = profile_data.get("taste_markers")
    if isinstance(markers_value, dict):
        taste_markers = TasteMarkers(**markers_value)
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
    override_summary = (profile_data.get("style_summary") or "").strip() if isinstance(profile_data.get("style_summary"), str) else ""
    if is_seed_derived or is_synthesized or override_summary:
        style_summary = override_summary or None
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
        inference_confidence=profile_data.get("inference_confidence") if (is_seed_derived or is_synthesized) else None,
        seed_bottle_count=profile_data.get("seed_bottle_count") if is_seed_derived else None,
    )


@router.patch("/profile")
def patch_profile(req: ProfilePatchRequest) -> ProfileSummaryResponse:
    """Merge user-edit fields into ``profile_data.json["_overrides"]``.

    The override block is layered on top of the derived/inferred profile by
    ``build_taste_profile()`` and respected by ``/profile-summary`` and the
    recommendation prompt. Re-running /upload-profile or /seed-profile clears it.
    """
    patch_dict = {k: v for k, v in req.model_dump(exclude_none=True).items()}
    if not patch_dict:
        raise HTTPException(status_code=400, detail="No fields to patch.")

    data = load_profile_data()
    overrides = dict(data.get("_overrides") or {})
    overrides.update(patch_dict)
    data["_overrides"] = overrides

    PROFILE_DATA_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    bust_profile_cache()
    bust_cache()
    logger.info("profile_patch: updated keys=%s", list(patch_dict.keys()))

    return profile_summary()
