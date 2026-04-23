"""CellarTracker profile exports: detect type, parse TSV, persist to profile_data.json."""
 
from __future__ import annotations
 
import csv
import io
import json
import re
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from statistics import mean
import hashlib
import anthropic
import logging
 
from inventory import decode_cellartracker_upload
from models import TasteProfile

<<<<<<< HEAD
<<<<<<< HEAD
from typing import List

=======
>>>>>>> 6caf2d0 (Initial commit: Setting up project structure)
=======
from typing import List

>>>>>>> b169158 (Added my profile tab)
_SOM_DIR = Path(__file__).resolve().parent
PROFILE_DATA_PATH = _SOM_DIR / "profile_data.json"
 
 
def _normalize_row(row: dict) -> dict[str, str]:
    return {(k or "").strip(): (v if v is not None else "").strip() for k, v in row.items()}
 
 
def _header_lower_list(fieldnames: list[str] | None) -> list[str]:
    if not fieldnames:
        return []
    return [h.strip().lower() for h in fieldnames]
 
 
def _detect_export_type(fieldnames: list[str] | None) -> str:
    """Return list | notes | consumed | purchases | unknown."""
    hl = _header_lower_list(fieldnames)
    if not hl:
        return "unknown"
 
    has = frozenset(hl)
 
    if "consumed" in has:
        return "consumed"
    # Tasting-notes export: dedicated Note column (not PNotes/CNotes on list views)
    if "note" in has:
        return "notes"
    # Current cellar list: CellarTracker list export includes iWine + Quantity
    if "quantity" in has and "iwine" in has:
        return "list"
    # Purchase history: Price + Quantity, no standalone Note column
    if "price" in has and "quantity" in has and "note" not in has:
        return "purchases"
    if "quantity" in has:
        return "list"
 
    return "unknown"
 
 
def ingest_export(raw: bytes) -> tuple[str, list[dict[str, str]]]:
    """Decode bytes, detect export type from TSV headers, return (type, rows)."""
    text = decode_cellartracker_upload(raw)
    text = text.strip()
    if not text:
        return "unknown", []
 
    reader = csv.DictReader(io.StringIO(text), delimiter="\t")
    fieldnames = reader.fieldnames
    export_type = _detect_export_type(fieldnames)
 
    rows: list[dict[str, str]] = []
    for row in reader:
        rows.append(_normalize_row(row))
 
    return export_type, rows
 
 
def save_profile_export(raw: bytes) -> str:
    """Ingest export, merge into profile_data.json (replace rows for this type). Returns export type."""
    export_type, rows = ingest_export(raw)
    data = load_profile_data()
    data[export_type] = rows
    PROFILE_DATA_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return export_type
 
 
def load_profile_data() -> dict:
    """Load full profile_data.json or {} if missing/unreadable."""
    if not PROFILE_DATA_PATH.is_file():
        return {}
    try:
        raw = json.loads(PROFILE_DATA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return raw if isinstance(raw, dict) else {}
 
 
# Common English + wine-generic terms to drop from tasting-note word counts
_DESCRIPTOR_STOPWORDS = frozenset({
    "a", "about", "after", "again", "all", "also", "an", "and", "any", "are", "as", "at",
    "be", "been", "being", "both", "but", "by", "can", "could", "did", "do", "does", "doing",
    "down", "each", "few", "for", "from", "further", "had", "has", "have", "having", "he",
    "her", "here", "hers", "him", "his", "how", "i", "if", "in", "into", "is", "it", "its",
    "just", "like", "me", "more", "most", "my", "no", "nor", "not", "now", "of", "off", "on",
    "once", "only", "or", "other", "our", "ours", "out", "over", "own", "same", "she", "should",
    "so", "some", "such", "than", "that", "the", "their", "theirs", "them", "then", "there",
    "these", "they", "this", "those", "through", "to", "too", "under", "until", "up", "very",
    "was", "we", "were", "what", "when", "where", "which", "while", "who", "whom", "why",
    "will", "with", "would", "you", "your", "yours",
    "bottle", "drink", "finish", "glass", "nose", "palate", "wine", "wines",
})
 
_TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z'-]*")
 
 
def _row_get_ci(row: dict, *names: str) -> str:
    lower = {k.lower(): v for k, v in row.items()}
    for n in names:
        if n.lower() in lower:
            v = lower[n.lower()]
            return str(v).strip() if v is not None else ""
    return ""
 
 
def _parse_float(val: object) -> float | None:
    if val is None or val == "":
        return None
    try:
        return float(str(val).replace(",", "").strip())
    except (ValueError, TypeError):
        return None
 
 
def _norm_key(k: str) -> str:
    return k.lower().replace(" ", "")
 
 
def _row_max_rating_score(row: dict) -> float | None:
    """Best numeric score from CTscore, MYscore, CScore, PScore (CellarTracker naming varies)."""
    score_keys = frozenset({"ctscore", "myscore", "cscore", "pscore"})
    vals: list[float] = []
    for k, v in row.items():
        if _norm_key(k) in score_keys:
            p = _parse_float(v)
            if p is not None:
                vals.append(p)
    return max(vals) if vals else None
 
 
def _iter_export_rows(profile_data: dict, *keys: str):
    for key in keys:
        rows = profile_data.get(key)
        if not isinstance(rows, list):
            continue
        for row in rows:
            if isinstance(row, dict):
                yield row
 
 
def _top_n_from_counter(counter: Counter[str], n: int) -> list[str]:
    return [w for w, _ in counter.most_common(n)]
 
 
def _infer_avoided_styles(profile_data: dict) -> list[str]:
    """Infer avoided styles from high-frequency negative tasting note terms.

    Analyzes notes appearing with low scores to identify avoided descriptors.
    """
    logger = logging.getLogger("sommelier.profile")

    # Words associated with negative characteristics
    negative_indicator_words = {
        "oaky", "overoaked", "oak", "woody", "bitter", "extracted", "alcoholic",
        "jammy", "raisiny", "cooked", "burnt", "thin", "watery", "flat", "dull",
        "flabby", "cloying", "sweet", "rough", "harsh", "tannic", "green",
        "vegetal", "musty", "corked", "oxidized", "funky", "vinegary"
    }

    # First pass: collect all scores to detect the scale in use
    all_scores: list[float] = []
    for row in _iter_export_rows(profile_data, "notes", "consumed"):
        score = _row_max_rating_score(row)
        if score is not None:
            all_scores.append(score)

    # If no scores are present at all, skip inference entirely
    if not all_scores:
        return []

    max_score = max(all_scores)
    if max_score > 10:
        low_score_threshold = 60.0
    else:
        low_score_threshold = 3.0

    logger.debug("score_scale_detected max_score=%.1f threshold=%.1f", max_score, low_score_threshold)

    low_score_words: Counter[str] = Counter()

    # Second pass: collect negative-indicator words from low-scoring rows
    for row in _iter_export_rows(profile_data, "notes", "consumed"):
        score = _row_max_rating_score(row)

        # Only look at rows with low scores
        if score is None or score > low_score_threshold:
            continue

        note = _row_get_ci(row, "Note", "Notes", "ConsumptionNote", "BottleNote", "PurchaseNote")
        if not note:
            continue

        for tok in _TOKEN_RE.findall(note.lower()):
            if len(tok) < 3 or tok in _DESCRIPTOR_STOPWORDS:
                continue
            # Only count words that are actual negative indicators
            if tok in negative_indicator_words:
                low_score_words[tok] += 1

    # Return top avoided styles, filtered by a minimum frequency
    avoided = [w for w, count in low_score_words.most_common(10) if count >= 2]
    return avoided


def build_taste_profile(profile_data: dict) -> dict:
    """Derive structured taste signals from merged profile export data."""
    if not isinstance(profile_data, dict):
        profile_data = {}

    list_consumed_notes = list(
        _iter_export_rows(profile_data, "list", "consumed", "notes")
    )
    all_rows = list(_iter_export_rows(profile_data, "list", "consumed", "notes", "purchases", "unknown"))

    varietal_counts: Counter[str] = Counter()
    region_counts: Counter[str] = Counter()
    producer_counts: Counter[str] = Counter()

    for row in list_consumed_notes:
        v = _row_get_ci(row, "Varietal") or _row_get_ci(row, "MasterVarietal")
        if v and v.lower() != "unknown":
            varietal_counts[v.lower()] += 1

        for field in ("Region", "SubRegion", "Appellation"):
            place = _row_get_ci(row, field)
            if place and place.lower() != "unknown":
                region_counts[place.lower()] += 1

    for row in all_rows:
        p = _row_get_ci(row, "Producer")
        if p and p.lower() != "unknown":
            producer_counts[p.lower()] += 1

    top_varietals = _top_n_from_counter(varietal_counts, 10)
    top_regions = _top_n_from_counter(region_counts, 8)
    top_producers = _top_n_from_counter(producer_counts, 10)

    highly_rated: list[dict] = []
    seen: set[tuple[str, str, str]] = set()
    for row in all_rows:
        producer = _row_get_ci(row, "Producer")
        wine = _row_get_ci(row, "Wine")
        vintage = _row_get_ci(row, "Vintage")
        if not wine and not producer:
            continue
        key = (producer.lower(), wine.lower(), vintage.lower())
        if key in seen:
            continue
        seen.add(key)
        highly_rated.append({"producer": producer, "wine": wine, "vintage": vintage})
        if len(highly_rated) >= 15:
            break

    word_counts: Counter[str] = Counter()
    for row in _iter_export_rows(profile_data, "notes", "consumed"):
        note = _row_get_ci(row, "Note", "Notes", "ConsumptionNote", "BottleNote", "PurchaseNote")
        if not note:
            continue
        for tok in _TOKEN_RE.findall(note.lower()):
            if len(tok) < 3 or tok in _DESCRIPTOR_STOPWORDS:
                continue
            word_counts[tok] += 1
    preferred_descriptors = _top_n_from_counter(word_counts, 15)

    prices: list[float] = []
    for row in _iter_export_rows(profile_data, "purchases"):
        pr = _parse_float(_row_get_ci(row, "Price"))
        if pr is not None:
            prices.append(pr)
    if prices:
        avg_spend = round(mean(prices) / 5) * 5
    else:
        avg_spend = None

    avoided_styles = _infer_avoided_styles(profile_data)

    return {
        "top_varietals": top_varietals,
        "top_regions": top_regions,
        "top_producers": top_producers,
        "highly_rated": highly_rated,
        "preferred_descriptors": preferred_descriptors,
        "avoided_styles": avoided_styles,
        "avg_spend": avg_spend,
    }
 
 
def build_taste_profile_pydantic(profile_data: dict) -> TasteProfile:
    """Convert derived taste profile dict to TasteProfile Pydantic model.

    Maps dict keys to TasteProfile fields and infers budget constraints.
    """
    structured = build_taste_profile(profile_data)

    # Map dict fields to TasteProfile fields
    preferred_grapes = structured.get("top_varietals", [])
    preferred_regions = structured.get("top_regions", [])
    preferred_styles = structured.get("preferred_descriptors", [])
    avoided_styles = structured.get("avoided_styles", [])
    avg_spend = structured.get("avg_spend")

    # Derive budget from average spend (±10 from rounded average)
    budget_min = None
    budget_max = None
    if avg_spend is not None:
        budget_min = max(0, int(round(avg_spend)) - 10)
        budget_max = int(round(avg_spend)) + 10

    return TasteProfile(
        preferred_grapes=preferred_grapes,
        preferred_regions=preferred_regions,
        preferred_styles=preferred_styles,
        avoided_styles=avoided_styles,
        budget_min=budget_min,
        budget_max=budget_max,
        profile_source="cellartracker",
    )


def _profile_data_empty(profile_data: dict) -> bool:
    if not profile_data:
        return True
    return not any(isinstance(v, list) and len(v) > 0 for v in profile_data.values())
 
 
def _display_label(s: str) -> str:
    return " ".join(w.capitalize() for w in s.replace("-", " ").split()) if s else s
 
 
def _join_oxford(items: list[str], n: int) -> str:
    picked = items[:n]
    if not picked:
        return ""
    labels = [_display_label(x) for x in picked]
    if len(labels) == 1:
        return labels[0]
    if len(labels) == 2:
        return f"{labels[0]} and {labels[1]}"
    return ", ".join(labels[:-1]) + f", and {labels[-1]}"
 
 
def _format_taste_profile_paragraph(p: dict) -> str:
    varietals = _join_oxford(p.get("top_varietals") or [], 5)
    regions = _join_oxford(p.get("top_regions") or [], 3)
    producers = _join_oxford(p.get("top_producers") or [], 3)
    terms = _join_oxford(p.get("preferred_descriptors") or [], 5)
    rated = p.get("highly_rated") or []
    
    # Format highly rated wines without scores
    rated_bits = []
    for item in rated[:3]:
        vintage = (item.get("vintage") or "").strip()
        wine = (item.get("wine") or "").strip()
        producer = (item.get("producer") or "").strip()
        name = wine or producer
        if vintage and name:
            rated_bits.append(f"{vintage} {_display_label(name)}")
        elif name:
            rated_bits.append(_display_label(name))
        else:
            rated_bits.append(_display_label(producer))
    
    avg = p.get("avg_spend")
 
    clauses: list[str] = []
    if terms:
        clauses.append(f"palate favours {terms}")
    if varietals:
        clauses.append(f"strong preference for {varietals}")
    if regions:
        clauses.append(f"top regions are {regions}")
    if producers:
        clauses.append(f"frequently returns to producers {producers}")
    if rated_bits:
        if len(rated_bits) == 1:
            rj = rated_bits[0]
        elif len(rated_bits) == 2:
            rj = f"{rated_bits[0]} and {rated_bits[1]}"
        else:
            rj = ", ".join(rated_bits[:-1]) + f", and {rated_bits[-1]}"
        clauses.append(f"highly rated bottles include {rj}")
    if avg is not None:
        low = max(0, int(round(avg)) - 10)
        high = int(round(avg)) + 10
        clauses.append(f"typical spend £{low}–{high} per bottle")
 
    if not clauses:
        return "Based on cellar and tasting history: limited structured data; rely on general guidance."
 
    body = "; ".join(clauses)
    return f"Based on cellar and tasting history: {body}."
 
 
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> faa3422 (Commit despite broken recommendation engine)
def extract_profile_preference_terms(profile_data: dict) -> dict:
    """Extract matchable keyword lists from structured profile data.

    Returns a dict with two keys:
      - ``preferred``: varietal + region terms the owner favours (match against
        bottle Varietal/Appellation/Region metadata).
      - ``avoided``: style descriptor terms to hard-exclude (currently empty
        because CT avoided terms are flavour words, not bottle metadata).
    """
    structured = build_taste_profile(profile_data)
    preferred = (structured.get("top_varietals") or []) + (structured.get("top_regions") or [])
    # avoided_styles from _infer_avoided_styles contains sensory words (e.g. "oaky")
    # that do not appear in bottle metadata — excluded from hard-exclusion to avoid
    # false positives. Wired up here for future use when metadata-matched avoidance
    # becomes available.
    return {"preferred": preferred, "avoided": []}


<<<<<<< HEAD
=======
>>>>>>> 6caf2d0 (Initial commit: Setting up project structure)
=======
>>>>>>> faa3422 (Commit despite broken recommendation engine)
def build_enhanced_profile_text() -> str:
    """Build taste profile text from loaded profile data or return owner default."""
    if not PROFILE_DATA_PATH.is_file():
        from prompt import OWNER_PROFILE
        return OWNER_PROFILE

    data = load_profile_data()
    if _profile_data_empty(data):
        from prompt import OWNER_PROFILE
        return OWNER_PROFILE

    # Build profile from structured data
    structured = build_taste_profile(data)
    if not any(
        [
            structured.get("top_varietals"),
            structured.get("top_regions"),
            structured.get("top_producers"),
            structured.get("highly_rated"),
            structured.get("preferred_descriptors"),
            structured.get("avg_spend") is not None,
        ]
    ):
        from prompt import OWNER_PROFILE
        return OWNER_PROFILE

    return _format_taste_profile_paragraph(structured)


def enrich_profile_with_anthropic(raw: dict, anthropic_api_key: str, anthropic_model: str) -> dict:
    """Enrich frequency-derived profile terms via Anthropic Claude.

    Takes the raw dict from build_taste_profile() and replaces
    preferred_descriptors and avoided_styles with synthesised multi-word phrases.
    Adds a style_summary key (one sentence). Returns raw unchanged on any error.
    """
    logger = logging.getLogger(__name__)
    logger.info("enrich_profile_with_anthropic: starting enrichment with model=%s", anthropic_model)

    prompt_text = (
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> faa3422 (Commit despite broken recommendation engine)
        "You are a master sommelier building a palate profile for a wine buyer.\n"
        "Your job: translate raw frequency data into STYLE descriptors — focus on "
        "texture, weight, and flavour character. Ignore grape variety and region labels; "
        "describe how wines feel and taste, not where they come from.\n\n"
        f"Top varietals (context only — do NOT echo these as style phrases): {raw.get('top_varietals', [])[:7]}\n"
        f"Top regions (context only — do NOT echo these as style phrases): {raw.get('top_regions', [])[:5]}\n"
<<<<<<< HEAD
        f"Tasting-note tokens (frequency-ranked): {raw.get('preferred_descriptors', [])}\n"
        f"Low-score note tokens (disliked): {raw.get('avoided_styles', [])}\n"
        f"Average spend: {raw.get('avg_spend')}\n"
        f"Sample producers: {raw.get('top_producers', [])[:5]}\n\n"
        "Rules:\n"
        "- preferred_styles: 3-6 multi-word sensory phrases, e.g. "
        '"taut mineral-driven whites with laser acidity", '
        '"silky medium-bodied reds with savoury earth and fine tannin"\n'
        "- avoided_styles: 2-4 multi-word phrases naming what to avoid, e.g. "
        '"heavily oaked and over-extracted reds", "sweet or cloying fruit-forward styles"\n'
        "- style_summary: one sentence, 20-30 words, capturing the overall palate character "
<<<<<<< HEAD
        "without mentioning specific grapes or regions\n\n"
        "Return ONLY valid JSON — no markdown, no explanation:\n"
        '{\n'
        '  "preferred_styles": [],\n'
        '  "avoided_styles": [],\n'
        '  "style_summary": ""\n'
=======
        "You are a wine expert. Analyse the raw preference data below and "
        "synthesise a higher-quality palate profile.\n\n"
        f"Top varietals: {raw.get('top_varietals', [])[:7]}\n"
        f"Top regions: {raw.get('top_regions', [])[:5]}\n"
=======
>>>>>>> faa3422 (Commit despite broken recommendation engine)
        f"Tasting-note tokens (frequency-ranked): {raw.get('preferred_descriptors', [])}\n"
        f"Low-score note tokens (disliked): {raw.get('avoided_styles', [])}\n"
        f"Average spend: {raw.get('avg_spend')}\n"
        f"Sample producers: {raw.get('top_producers', [])[:5]}\n\n"
        "Rules:\n"
        "- preferred_styles: 3-6 multi-word sensory phrases, e.g. "
        '"taut mineral-driven whites with laser acidity", '
        '"silky medium-bodied reds with savoury earth and fine tannin"\n'
        "- avoided_styles: 2-4 multi-word phrases naming what to avoid, e.g. "
        '"heavily oaked and over-extracted reds", "sweet or cloying fruit-forward styles"\n'
        "- style_summary: one sentence, 20-30 words, capturing the overall palate character "
        "without mentioning specific grapes or regions\n\n"
        "Return ONLY valid JSON — no markdown, no explanation:\n"
        '{\n'
<<<<<<< HEAD
        '  "preferred_styles": ["3-6 multi-word phrases describing preferred style"],\n'
        '  "avoided_styles": ["2-4 multi-word phrases describing avoided style"],\n'
        '  "style_summary": "One sentence, 20-30 words, capturing overall palate character."\n'
>>>>>>> 6caf2d0 (Initial commit: Setting up project structure)
=======
        '  "preferred_styles": [],\n'
        '  "avoided_styles": [],\n'
        '  "style_summary": ""\n'
>>>>>>> faa3422 (Commit despite broken recommendation engine)
        '}'
=======
        "without mentioning specific grapes or regions"
>>>>>>> 90359d9 (Ported to Anthropic)
    )

    enrichment_tool = {
        "name": "enrich_taste_profile",
        "description": "Provide enriched sensory taste profile descriptors.",
        "input_schema": {
            "type": "object",
            "properties": {
                "preferred_styles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "3-6 multi-word sensory phrases for preferred wine styles.",
                },
                "avoided_styles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "2-4 multi-word phrases naming wine styles to avoid.",
                },
                "style_summary": {
                    "type": "string",
                    "description": "One sentence (20-30 words) capturing the overall palate character.",
                },
            },
            "required": ["preferred_styles", "avoided_styles", "style_summary"],
        },
    }

    try:
        client = anthropic.Anthropic(api_key=anthropic_api_key)
        response = client.messages.create(
            model=anthropic_model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt_text}],
            tools=[enrichment_tool],
            tool_choice={"type": "tool", "name": "enrich_taste_profile"},
        )

        tool_block = next(
            (b for b in response.content if b.type == "tool_use" and b.name == "enrich_taste_profile"),
            None,
        )
        if not tool_block:
            logger.warning("enrich_profile_with_anthropic: no tool use block found")
            return raw

        enriched = tool_block.input
        logger.info("enrich_profile_with_anthropic: tool use received keys=%s", list(enriched.keys()))

        enriched_result = {
            **raw,
            "preferred_descriptors": enriched.get("preferred_styles") or raw.get("preferred_descriptors", []),
            "avoided_styles": enriched.get("avoided_styles") or raw.get("avoided_styles", []),
            "style_summary": enriched.get("style_summary") or "",
        }

        if not isinstance(enriched_result["style_summary"], str):
            enriched_result["style_summary"] = ""

        logger.info("enrich_profile_with_anthropic: enrichment complete. style_summary length=%d", len(enriched_result["style_summary"]))
        return enriched_result

    except anthropic.APIError as exc:
        logger.warning("Anthropic profile enrichment API error: %s", exc)
        return raw
    except Exception as exc:
        logger.warning("Anthropic profile enrichment failed: %s", exc, exc_info=True)
        return raw


# Keep the old name as an alias so any external callers continue to work.
enrich_profile_with_ollama = enrich_profile_with_anthropic


def build_enriched_profile_text(anthropic_api_key: str, anthropic_model: str) -> str:
    """Like build_enhanced_profile_text() but enriches derived terms via Anthropic Claude."""
    logger = logging.getLogger(__name__)

    if not PROFILE_DATA_PATH.is_file():
        logger.info("build_enriched_profile_text: profile_data.json not found, returning OWNER_PROFILE")
        from prompt import OWNER_PROFILE
        return OWNER_PROFILE

    data = load_profile_data()
    if _profile_data_empty(data):
        logger.info("build_enriched_profile_text: profile_data.json is empty, returning OWNER_PROFILE")
        from prompt import OWNER_PROFILE
        return OWNER_PROFILE

    structured = build_taste_profile(data)
    if not any([
        structured.get("top_varietals"),
        structured.get("top_regions"),
        structured.get("top_producers"),
        structured.get("highly_rated"),
        structured.get("preferred_descriptors"),
        structured.get("avg_spend") is not None,
    ]):
        logger.info("build_enriched_profile_text: structured profile is empty, returning OWNER_PROFILE")
        from prompt import OWNER_PROFILE
        return OWNER_PROFILE

    logger.info("build_enriched_profile_text: calling enrich_profile_with_anthropic")
    enriched = enrich_profile_with_anthropic(structured, anthropic_api_key, anthropic_model)

    # Check if enrichment actually happened (style_summary is the marker)
    enrichment_happened = "style_summary" in enriched and bool(enriched.get("style_summary", "").strip())
    logger.warning("build_enriched_profile_text: enrichment_happened=%s", enrichment_happened)
    if enrichment_happened:
        logger.warning("build_enriched_profile_text: enriched preferred_descriptors=%s", enriched.get("preferred_descriptors", [])[:3])
        logger.warning("build_enriched_profile_text: enriched avoided_styles=%s", enriched.get("avoided_styles", []))
        logger.warning("build_enriched_profile_text: style_summary=%s", enriched.get("style_summary", ""))

    summary = enriched.get("style_summary", "").strip()
    paragraph = _format_taste_profile_paragraph(enriched)

    logger.info("build_enriched_profile_text: summary length=%d, paragraph length=%d", len(summary), len(paragraph))
    logger.info("build_enriched_profile_text: summary=%s", summary[:200] if summary else "(empty)")
    logger.info("build_enriched_profile_text: paragraph (first 200 chars)=%s", paragraph[:200])

    if summary:
        result = f"{summary} {paragraph}"
    else:
        result = paragraph

    logger.info("build_enriched_profile_text: final enriched profile text length=%d", len(result))
    logger.debug("build_enriched_profile_text: final text (first 400 chars)=%s", result[:400])

    return result
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> b169158 (Added my profile tab)


def derive_taste_markers(descriptors: List[str]) -> dict:
    """
    Heuristically score Acidity, Tannin, Body, and Oak on a 1–5 scale
    by scanning the user's preferred descriptors for indicator keywords.

    Returns a dict suitable for constructing a TasteMarkers model.
    """
    text = " ".join(d.lower() for d in descriptors)

    _HIGH_ACID  = {"crisp", "tart", "bright", "mineral", "zesty", "lively", "laser", "sharp",
                   "vivid", "electric", "piercing", "racy", "tense"}
    _LOW_ACID   = {"soft", "round", "flat", "mellow", "smooth", "gentle", "plush", "plummy"}

    _HIGH_TAN   = {"tannic", "grippy", "structured", "firm", "chewy", "muscular", "angular",
                   "astringent", "powerful", "robust", "tight"}
    _LOW_TAN    = {"supple", "silky", "velvet", "velvety", "polished", "delicate", "fine tannin",
                   "light", "ethereal"}

    _HIGH_BODY  = {"full", "rich", "generous", "weighty", "bold", "concentrated", "powerful",
                   "big", "broad", "dense", "heavy"}
    _LOW_BODY   = {"light", "delicate", "lean", "ethereal", "thin", "feather", "wispy"}

    _HIGH_OAK   = {"oaky", "toasty", "vanilla", "cedar", "smoky", "spiced", "barrel", "woody",
                   "buttery", "creamy", "toast"}
    _LOW_OAK    = {"unoaked", "mineral", "neutral", "steel", "stainless", "unwooded", "pure",
                   "clean", "fresh"}

    def _score(high_kws: set, low_kws: set) -> int:
        score = 3  # default: medium
        for kw in high_kws:
            if kw in text:
                score += 1
        for kw in low_kws:
            if kw in text:
                score -= 1
        return max(1, min(5, score))

    return {
        "acidity": _score(_HIGH_ACID, _LOW_ACID),
        "tannin":  _score(_HIGH_TAN,  _LOW_TAN),
        "body":    _score(_HIGH_BODY, _LOW_BODY),
        "oak":     _score(_HIGH_OAK,  _LOW_OAK),
    }
<<<<<<< HEAD
=======
>>>>>>> 6caf2d0 (Initial commit: Setting up project structure)
=======
>>>>>>> b169158 (Added my profile tab)
