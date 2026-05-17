import logging
import logging.handlers
import os
from pathlib import Path
from profile import build_enriched_profile_text_basic

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
    profile_source: str = "cellartracker",
    bottle_count: int = 3,
    budget_ceiling: str = "",
    taste_markers: dict | None = None,
    palate_persona: str | None = None,
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
        taste_profile = build_enriched_profile_text_basic()
        logger.info("build_system_prompt: using standard build_enriched_profile_text_basic (len=%d)", len(taste_profile))

    if profile_source == "seed_bottles":
        taste_profile = (
            "(Profile inferred from a small set of seed bottles the user named — "
            "treat as directional, not authoritative; prefer recommendations that match "
            "the dominant style signals over edge-of-profile picks.)\n"
            + taste_profile
        )

    taste_markers_section = ""
    if isinstance(taste_markers, dict):
        markers_block = ", ".join([
            f"Acidity {taste_markers.get('acidity', 3)}/5",
            f"Tannin {taste_markers.get('tannin', 3)}/5",
            f"Body {taste_markers.get('body', 3)}/5",
            f"Oak {taste_markers.get('oak', 3)}/5",
        ])
        taste_markers_section = f"Taste markers (1-5 preference scale): {markers_block}\n\n"

    palate_persona_section = ""
    if isinstance(palate_persona, str) and palate_persona.strip():
        palate_persona_section = (
            "**PALATE PERSONA** (inferred signature — cite these signals in your reasoning):\n"
            f"{palate_persona.strip()}\n\n"
        )

    meal_section = f"### TONIGHT'S MEAL\n{meal_hints}\n" if meal_hints else ""

    constraints: list[str] = [f"Return exactly {bottle_count} ranked recommendations."]
    if budget_ceiling:
        constraints.append(f"Budget ceiling per bottle: {budget_ceiling} — exclude wines above this price.")
    constraint_section = "\n".join(f"- {c}" for c in constraints)

    schema = """{
  "recommendations": [
    {
      "rank": 1,
      "wine_name": "string",
      "producer": "string or null",
      "vintage": "integer or null",
      "region": "string or null",
      "price": "number or null",
      "appellation": "string or null  — official AOC/DOC/AVA designation",
      "country": "string or null",
      "coords": {"lat": number, "lon": number},
      "grape": "string or null  — primary variety",
      "abv": number_or_null,
      "drink": {"from": integer, "peak": integer, "until": integer},
      "bars": {"tannin": 0-10, "acidity": 0-10, "body": 0-10, "sweetness": 0-10, "oak": 0-10},
      "wheel": {"Aroma 1": 0-10, "Aroma 2": 0-10, "...6-8 entries total"},
      "nose": "one sentence aromatic profile",
      "palate": "one sentence palate and finish",
      "fits": ["profile tag 1", "profile tag 2"],
      "pairs": ["dish 1", "dish 2", "dish 3"],
      "critic": {"score": number, "source": "string"},
      "reasoning": "string (2-4 sentences)",
      "confidence": "high|medium|low — clause"
    }
  ],
  "list_quality_note": "string or null",
  "profile_match_summary": "string (1 sentence)"
}"""

    prompt = f"""You are a precise, opinionated sommelier. Your primary job is to match wines from the list
to the owner's taste profile (70% weight). The meal context is secondary guidance only (30% weight) —
do not let it override profile fit.

**HARD CONSTRAINT**: ALL recommendations must be wines from the provided restaurant wine list ONLY.
Do NOT recommend wines from the owner's cellar, even if they are a perfect profile match.

**CONSTRAINTS**:
{constraint_section}

Be direct. No filler. Respond with ONLY valid JSON (no markdown, no backticks, no explanation).

{palate_persona_section}PRIORITY — Owner taste profile (match this first):
{taste_profile}
{taste_markers_section}{character_line}{cellar_section}
If a wine from the owner's cellar appears on the restaurant list, only recommend it if it offers
significantly better value than alternatives with equal profile fit.
{meal_section}Return your response as valid JSON matching this schema exactly:
{schema}

Notes for reasoning field (follow this structure exactly):
1. PERSONAL COMPARISON: If a bottle from the cellar list is a genuine stylistic match, open with "Like your [Producer + Wine name], but [how this wine differs or excels]." ONLY use this opener when you can name a specific bottle from the cellar list — do NOT use it if there is no close match. If there is no close cellar match, skip this opener entirely and instead open by referencing a named style or preference from the taste profile directly (e.g., "Delivers the mineral-driven acidity you consistently reach for").
2. CONTRAST (where relevant): Follow with "Unlike [an avoided bottle/style from the profile], no [unwanted trait]." Only include if it adds genuine distinction.
3. FOOD CONTEXT (secondary): Briefly note meal synergy only if it adds insight beyond the profile match.
4. CELLAR NOTE: If outclassed by something they own, say so; if worth ordering despite owning something similar, explain why.

Notes for confidence field:
- Format exactly as: "[high|medium|low] — [single clause reason]"
- The clause should name the specific preference being matched or the doubt causing uncertainty.
- Examples: "high — hits your preference for grower Champagne with mineral complexity" / "medium — right style but the vintage may be too young"

Notes for fits field (optional):
- Provide 2-3 short tags (each <= 8 words) per recommendation, surfacing concrete profile signals that drove the pick.
- Each tag MUST cite a real signal from the taste profile above: a top region/varietal/producer, a preferred descriptor, an avoided style, a numeric taste marker (acidity/tannin/body/oak 1-5), or a phrase quoted/paraphrased from the PALATE PERSONA block.
- Good: "Matches your high-acidity preference (5/5)", "Aligned with your top region: Northern Rhône", "Hits your oxidative-style signature", "Avoids the overtly oaky profile you down-rate".
- Bad (forbidden — too generic): "Great with food", "Crowd pleaser", "Classic choice".
- If no clean signal applies, OMIT the field entirely. Do not return an empty array and do not invent signals not present in the profile.

Notes for wheel field:
- Provide 6-8 entries representing the dominant aroma families. Values are 0-10 intensity.
- Use real aroma vocabulary (e.g. "Dried Cherry", "Tar", "Violets", "Cedar", "Mineral", "Truffle").

Notes for bars field:
- All values 0-10. Be accurate — a lean Chablis should have tannin ≈ 1, acidity ≈ 9; a big Amarone tannin ≈ 9, sweetness ≈ 3.

Notes for drink field:
- "from" = earliest year to open; "peak" = optimal drinking year; "until" = last acceptable year.
- All integer years (e.g. 2026, 2032, 2042). Ground in the vintage year when known.

Return ONLY the JSON object, no other text."""
    _prompt_logger.debug(prompt)
    return prompt
