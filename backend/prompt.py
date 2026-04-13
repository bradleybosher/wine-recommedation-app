import logging
import logging.handlers
import os
from pathlib import Path
from profile import build_enhanced_profile_text

_log_dir = Path(__file__).resolve().parent / "logs"
_log_dir.mkdir(parents=True, exist_ok=True)

_prompt_logger = logging.getLogger("prompt.debug")
if not _prompt_logger.handlers:
    _handler = logging.handlers.RotatingFileHandler(
        _log_dir / "prompt.log", maxBytes=1_000_000, backupCount=2, encoding="utf-8"
    )
    _handler.setFormatter(logging.Formatter("%(asctime)s\n%(message)s\n" + "=" * 80))
    _prompt_logger.addHandler(_handler)
    _prompt_logger.setLevel(logging.DEBUG)
    _prompt_logger.propagate = False


def format_bottle(b: dict) -> str:
    parts = [b.get("Vintage",""), b.get("Producer",""), b.get("Wine","")]
    drink = ""
    if b.get("BeginConsume") and b.get("EndConsume"):
        drink = f" (drink {b['BeginConsume']}–{b['EndConsume']})"
    return " ".join(p for p in parts if p) + drink

def build_system_prompt(
    relevant_bottles: list[dict],
    cellar_summary: str = "",
    taste_profile_override: str | None = None,
    meal_hints: str = "",
) -> str:
    import logging
    logger = logging.getLogger(__name__)

    cellar_section = ""
    if relevant_bottles:
        bottle_list = "\n".join(f"  - {format_bottle(b)}" for b in relevant_bottles[:20])
        cellar_section = f"""
The user has the following relevant bottles in their cellar:
{bottle_list}

Where appropriate, note if something on the list is outclassed by what they own at home,
or if a bottle is worth ordering specifically because they don't have it.
"""
    character_line = ""
    if cellar_summary.strip():
        character_line = f"Owner's cellar character: {cellar_summary.strip()}\n\n"

    if taste_profile_override is not None:
        taste_profile = taste_profile_override
        logger.info("build_system_prompt: using taste_profile_override (len=%d)", len(taste_profile))
        logger.debug("build_system_prompt: taste_profile_override (first 300 chars): %s", taste_profile[:300])
    else:
        taste_profile = build_enhanced_profile_text()
        logger.info("build_system_prompt: using standard build_enhanced_profile_text (len=%d)", len(taste_profile))

    meal_section = f"### TONIGHT'S MEAL\n{meal_hints}\n" if meal_hints else ""

    schema = """{
  "recommendations": [
    {
      "rank": 1,
      "wine_name": "string",
      "producer": "string or null",
      "vintage": "integer or null",
      "region": "string or null",
      "price": "number or null",
      "reasoning": "string (2-4 sentences — lead with 'Like your [owned bottle], but [how it differs/excels]'; contrast avoided styles where relevant)",
      "confidence": "string — 'high|medium|low — short clause explaining why, e.g. high — hits your preference for grower Champagne with mineral complexity'"
    }
  ],
  "list_quality_note": "string or null (e.g., 'Limited white selection')",
  "profile_match_summary": "string (1 sentence overview)"
}"""

    prompt = f"""You are a precise, opinionated sommelier. Your primary job is to match wines from the list
to the owner's taste profile (70% weight). The meal context is secondary guidance only (30% weight) —
do not let it override profile fit.

**HARD CONSTRAINT**: ALL recommendations must be wines from the provided restaurant wine list ONLY.
Do NOT recommend wines from the owner's cellar, even if they are a perfect profile match.

Be direct. No filler. Respond with ONLY valid JSON (no markdown, no backticks, no explanation).

PRIORITY — Owner taste profile (match this first):
{taste_profile}
{character_line}{cellar_section}
If a wine from the owner's cellar appears on the restaurant list, only recommend it if it offers
significantly better value than alternatives with equal profile fit.
{meal_section}Return your response as valid JSON matching this schema exactly:
{schema}

Notes for reasoning field (follow this structure exactly):
1. PERSONAL COMPARISON (required): Open with "Like your [specific bottle the user owns from the cellar list], but [how this wine differs or excels]." If no close cellar match exists, anchor to a style they strongly prefer instead.
2. CONTRAST (where relevant): Follow with "Unlike [an avoided bottle/style from the profile], no [unwanted trait]." Only include if it adds genuine distinction.
3. FOOD CONTEXT (secondary): Briefly note meal synergy only if it adds insight beyond the profile match.
4. CELLAR NOTE: If outclassed by something they own, say so; if worth ordering despite owning something similar, explain why.

Notes for confidence field:
- Format exactly as: "[high|medium|low] — [single clause reason]"
- The clause should name the specific preference being matched or the doubt causing uncertainty.
- Examples: "high — hits your preference for grower Champagne with mineral complexity" / "medium — right style but the vintage may be too young"

Return ONLY the JSON object, no other text."""
    _prompt_logger.debug(prompt)
    return prompt
