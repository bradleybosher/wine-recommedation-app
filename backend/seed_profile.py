"""Seed-bottle onboarding: infer a taste profile from a small set of named wines.

Alternative to CellarTracker TSV import. The user names 3-7 wines they love
(and optionally 1-3 they disliked); Claude infers aggregate taste signals
shaped identically to the output of profile.build_taste_profile() so the
downstream recommender pipeline consumes them unchanged.

Persistence: writes the pre-computed structured dict to profile_data.json
under the reserved "_inferred" key (alongside the legacy CT keys, which are
cleared on save). profile.build_taste_profile() short-circuits to this dict
when present, so no synthetic CT-shaped rows are needed.
"""

from __future__ import annotations

import json
import logging
from typing import Optional

import anthropic

from models import SeedBottle, SeedProfileRequest

logger = logging.getLogger(__name__)

INFERRED_KEY = "_inferred"


def _format_bottle_line(b: SeedBottle) -> str:
    vintage = f"{b.vintage} " if b.vintage else ""
    note = f" — note: {b.note}" if b.note else ""
    return f"{vintage}{b.producer} — {b.wine}{note}"


def infer_profile_from_seeds(
    req: SeedProfileRequest,
    anthropic_api_key: str,
    anthropic_model: str,
) -> dict:
    """Single Anthropic tool-use call to derive an enriched taste profile.

    Returns a dict shaped like build_taste_profile() output PLUS:
      - style_summary: str
      - taste_markers: {acidity, tannin, body, oak} 1-5
      - inference_confidence: "high" | "medium" | "low"
      - profile_source: "seed_bottles"
      - seed_bottle_count: int
    """
    loved_lines = "\n".join(f"  - {_format_bottle_line(b)}" for b in req.loved)
    disliked_lines = (
        "\n".join(f"  - {_format_bottle_line(b)}" for b in req.disliked)
        if req.disliked else "  (none provided)"
    )

    prompt_text = (
        "You are a master sommelier inferring a buyer's palate from a handful of named wines.\n"
        "Your job: identify each wine's producer/style/region/varietal, then synthesize the buyer's\n"
        "aggregate taste signature. Treat 'loved' wines as positive signal and 'disliked' wines as\n"
        "negative signal (extract style traits the buyer wants to avoid).\n\n"
        f"Loved wines ({len(req.loved)}):\n{loved_lines}\n\n"
        f"Disliked wines ({len(req.disliked)}):\n{disliked_lines}\n\n"
        "Rules:\n"
        "- top_varietals: 3-7 grape varieties (lowercase) inferred from the loved wines.\n"
        "- top_regions: 2-5 regions/appellations (lowercase) inferred from the loved wines.\n"
        "- top_producers: the producers from the loved list (lowercase).\n"
        "- highly_rated: echo the loved wines as [{producer, wine, vintage}] (string vintage or '').\n"
        "- preferred_descriptors: 4-7 multi-word sensory phrases describing the loved wines'\n"
        "  texture/weight/flavour character. Avoid grape/region names. E.g. 'taut mineral-driven whites with laser acidity'.\n"
        "- avoided_styles: 2-4 multi-word phrases naming styles to avoid, grounded in the disliked\n"
        "  wines if provided, otherwise inferred as the counterpoint to the loved profile.\n"
        "- avg_spend: a plausible per-bottle budget in dollars based on producer tier (integer or null).\n"
        "- style_summary: one sentence (20-30 words) capturing overall palate character without naming grapes/regions.\n"
        "- taste_markers: integer scores 1-5 for acidity, tannin, body, oak.\n"
        "- inference_confidence: 'high' if all wines are well-known and stylistically coherent,\n"
        "  'medium' if the set is plausible but mixed, 'low' if wines are obscure or contradictory."
    )

    tool = {
        "name": "infer_seed_profile",
        "description": "Synthesize an enriched taste profile from a small set of seed bottles.",
        "input_schema": {
            "type": "object",
            "properties": {
                "top_varietals": {"type": "array", "items": {"type": "string"}},
                "top_regions": {"type": "array", "items": {"type": "string"}},
                "top_producers": {"type": "array", "items": {"type": "string"}},
                "highly_rated": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "producer": {"type": "string"},
                            "wine": {"type": "string"},
                            "vintage": {"type": "string"},
                        },
                        "required": ["producer", "wine", "vintage"],
                    },
                },
                "preferred_descriptors": {"type": "array", "items": {"type": "string"}},
                "avoided_styles": {"type": "array", "items": {"type": "string"}},
                "avg_spend": {"type": ["integer", "null"]},
                "style_summary": {"type": "string"},
                "taste_markers": {
                    "type": "object",
                    "properties": {
                        "acidity": {"type": "integer", "minimum": 1, "maximum": 5},
                        "tannin": {"type": "integer", "minimum": 1, "maximum": 5},
                        "body": {"type": "integer", "minimum": 1, "maximum": 5},
                        "oak": {"type": "integer", "minimum": 1, "maximum": 5},
                    },
                    "required": ["acidity", "tannin", "body", "oak"],
                },
                "inference_confidence": {
                    "type": "string",
                    "enum": ["high", "medium", "low"],
                },
            },
            "required": [
                "top_varietals", "top_regions", "top_producers", "highly_rated",
                "preferred_descriptors", "avoided_styles", "style_summary",
                "taste_markers", "inference_confidence",
            ],
        },
    }

    client = anthropic.Anthropic(api_key=anthropic_api_key)
    response = client.messages.create(
        model=anthropic_model,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt_text}],
        tools=[tool],
        tool_choice={"type": "tool", "name": "infer_seed_profile"},
    )

    tool_block = next(
        (b for b in response.content if b.type == "tool_use" and b.name == "infer_seed_profile"),
        None,
    )
    if not tool_block:
        raise RuntimeError("Anthropic did not return the expected tool_use block for seed-profile inference.")

    inferred = dict(tool_block.input)
    inferred["profile_source"] = "seed_bottles"
    inferred["seed_bottle_count"] = len(req.loved)
    logger.info(
        "infer_profile_from_seeds: success loved=%d disliked=%d confidence=%s",
        len(req.loved), len(req.disliked), inferred.get("inference_confidence"),
    )
    return inferred


def persist_seed_profile(inferred: dict) -> None:
    """Replace profile_data.json with a fresh dict containing only the inferred profile.

    Wipes any legacy CT keys (list/notes/consumed/purchases) so the seed-bottle
    pathway never silently mixes sources. Backs up the existing profile before overwriting.
    Busts the profile cache after write to ensure subsequent loads read the new data.
    """
    from profile import PROFILE_DATA_PATH, bust_profile_cache  # local import to avoid module-import cycle

    # Back up existing profile before overwriting
    if PROFILE_DATA_PATH.is_file():
        backup_path = PROFILE_DATA_PATH.with_suffix(".backup.json")
        backup_path.write_text(PROFILE_DATA_PATH.read_text(encoding="utf-8"), encoding="utf-8")
        logger.info("persist_seed_profile: backed up existing profile to %s", backup_path)

    payload = {INFERRED_KEY: inferred}
    PROFILE_DATA_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    bust_profile_cache()
    logger.info("persist_seed_profile: wrote inferred profile to %s", PROFILE_DATA_PATH)


def load_inferred_profile() -> Optional[dict]:
    """Return the inferred seed profile if present, else None."""
    from profile import load_profile_data
    data = load_profile_data()
    inferred = data.get(INFERRED_KEY)
    if isinstance(inferred, dict) and inferred:
        return inferred
    return None
