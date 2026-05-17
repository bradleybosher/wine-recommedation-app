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
from typing import List
import hashlib
import anthropic
import logging

from inventory import decode_cellartracker_upload
from models import TasteProfile

_SOM_DIR = Path(__file__).resolve().parent
PROFILE_DATA_PATH = _SOM_DIR / "profile_data.json"

# Module-level cache: (mtime, data) tuple to avoid re-reading profile_data.json on every request
_profile_cache: tuple[float, dict] | None = None


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

    _REQUIRED_CT_COLUMNS = frozenset({
        "wine", "producer", "appellation", "varietal", "vintage",
        "quantity", "note", "consumed", "iwine",
    })
    if fieldnames:
        header_set = frozenset(h.strip().lower() for h in fieldnames)
        if not header_set.intersection(_REQUIRED_CT_COLUMNS):
            raise ValueError(
                f"Unrecognised file format. Expected a CellarTracker TSV export. "
                f"Found columns: {', '.join(list(fieldnames)[:10])}"
            )

    export_type = _detect_export_type(fieldnames)

    rows: list[dict[str, str]] = []
    for row in reader:
        rows.append(_normalize_row(row))

    return export_type, rows


def bust_profile_cache() -> None:
    """Invalidate the module-level profile data cache.

    Call this after writing to profile_data.json to ensure the next load_profile_data() call
    reads the updated file instead of returning stale cached data.
    """
    global _profile_cache
    _profile_cache = None


def save_profile_export(raw: bytes) -> str:
    """Ingest export, merge into profile_data.json (replace rows for this type). Returns export type."""
    export_type, rows = ingest_export(raw)
    data = load_profile_data()
    data[export_type] = rows
    PROFILE_DATA_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    bust_profile_cache()  # Invalidate cache after write
    return export_type


def load_profile_data() -> dict:
    """Load full profile_data.json or {} if missing/unreadable.

    Uses module-level cache (_profile_cache) to avoid re-reading the file on every request.
    Cache is validated by mtime; if the file hasn't changed, the cached dict is returned.
    """
    global _profile_cache

    # Determine current mtime
    mtime = PROFILE_DATA_PATH.stat().st_mtime if PROFILE_DATA_PATH.exists() else 0.0

    # Return cached data if mtime hasn't changed
    if _profile_cache is not None and _profile_cache[0] == mtime:
        return _profile_cache[1]

    # Load from file
    if not PROFILE_DATA_PATH.is_file():
        data = {}
    else:
        try:
            raw = json.loads(PROFILE_DATA_PATH.read_text(encoding="utf-8"))
            data = raw if isinstance(raw, dict) else {}
        except (OSError, json.JSONDecodeError):
            data = {}

    # Cache and return
    _profile_cache = (mtime, data)
    return data


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
    """Infer avoided styles from high-frequency negative tasting note terms."""
    logger = logging.getLogger("sommelier.profile")

    negative_indicator_words = {
        "oaky", "overoaked", "oak", "woody", "bitter", "extracted", "alcoholic",
        "jammy", "raisiny", "cooked", "burnt", "thin", "watery", "flat", "dull",
        "flabby", "cloying", "sweet", "rough", "harsh", "tannic", "green",
        "vegetal", "musty", "corked", "oxidized", "funky", "vinegary"
    }

    all_scores: list[float] = []
    for row in _iter_export_rows(profile_data, "notes", "consumed"):
        score = _row_max_rating_score(row)
        if score is not None:
            all_scores.append(score)

    if not all_scores:
        return []

    max_score = max(all_scores)
    if max_score > 10:
        low_score_threshold = 60.0
    else:
        low_score_threshold = 3.0

    logger.debug("score_scale_detected max_score=%.1f threshold=%.1f", max_score, low_score_threshold)

    low_score_words: Counter[str] = Counter()

    for row in _iter_export_rows(profile_data, "notes", "consumed"):
        score = _row_max_rating_score(row)

        if score is None or score > low_score_threshold:
            continue

        note = _row_get_ci(row, "Note", "Notes", "ConsumptionNote", "BottleNote", "PurchaseNote")
        if not note:
            continue

        for tok in _TOKEN_RE.findall(note.lower()):
            if len(tok) < 3 or tok in _DESCRIPTOR_STOPWORDS:
                continue
            if tok in negative_indicator_words:
                low_score_words[tok] += 1

    avoided = [w for w, count in low_score_words.most_common(10) if count >= 2]
    return avoided


def apply_profile_overrides(base: dict, overrides: dict) -> dict:
    """Layer a partial user-edit dict on top of a derived/inferred profile.

    Shallow merge: each top-level override key replaces the corresponding base value.
    Returns a new dict; ``base`` is not mutated.
    """
    if not isinstance(overrides, dict) or not overrides:
        return dict(base)
    merged = dict(base)
    for k, v in overrides.items():
        if v is None:
            continue
        merged[k] = v
    return merged


SYNTHESIZED_KEY = "_synthesized"

# Per-tier cap on how many raw notes are fed to the synthesis LLM call.
# Sorting within tier keeps the most extreme examples (top/bottom of the tier).
_SYNTHESIS_NOTES_PER_TIER = 50

# Below this note count we mark inference_confidence="low" — sparse signal.
_SYNTHESIS_LOW_CONFIDENCE_THRESHOLD = 10


def _gather_scored_notes(profile_data: dict) -> tuple[list[dict], float, float]:
    """Collect non-empty tasting notes with their max numeric score.

    Returns (notes_list, mid_low_threshold, mid_high_threshold). Each note is
    {"note": str, "score": float, "wine": str}. Thresholds are derived from the
    detected score scale (0-100 or 0-10) and are used to bucket into tiers.
    """
    rows_with_notes: list[dict] = []
    all_scores: list[float] = []
    for row in _iter_export_rows(profile_data, "notes", "consumed"):
        note = _row_get_ci(row, "Note", "Notes", "ConsumptionNote", "BottleNote", "PurchaseNote")
        if not note:
            continue
        score = _row_max_rating_score(row)
        producer = _row_get_ci(row, "Producer")
        wine = _row_get_ci(row, "Wine")
        vintage = _row_get_ci(row, "Vintage")
        label_parts = [p for p in (vintage, producer, wine) if p]
        rows_with_notes.append({
            "note": note,
            "score": score,
            "wine": " ".join(label_parts) if label_parts else "(unlabelled)",
        })
        if score is not None:
            all_scores.append(score)

    if not all_scores:
        return rows_with_notes, 0.0, 0.0

    max_score = max(all_scores)
    if max_score > 10:
        low_threshold = 85.0
        high_threshold = 93.0
    else:
        low_threshold = 7.5
        high_threshold = 9.0
    return rows_with_notes, low_threshold, high_threshold


def _bucket_notes_by_tier(
    notes: list[dict], low_threshold: float, high_threshold: float
) -> tuple[list[dict], list[dict], list[dict]]:
    """Split scored notes into (high, mid, low) tiers, sorted within each tier."""
    high: list[dict] = []
    mid: list[dict] = []
    low: list[dict] = []
    for entry in notes:
        score = entry.get("score")
        if score is None:
            mid.append(entry)
            continue
        if score >= high_threshold:
            high.append(entry)
        elif score <= low_threshold:
            low.append(entry)
        else:
            mid.append(entry)
    high.sort(key=lambda e: e.get("score") or 0, reverse=True)
    low.sort(key=lambda e: e.get("score") or 0)
    mid.sort(key=lambda e: e.get("score") or 0, reverse=True)
    return high, mid, low


def _format_note_block(label: str, entries: list[dict], cap: int) -> str:
    if not entries:
        return f"{label}: (none)\n"
    picked = entries[:cap]
    lines = []
    for e in picked:
        score = e.get("score")
        score_str = f" [{score:g}]" if score is not None else ""
        wine = e.get("wine") or ""
        note = (e.get("note") or "").strip().replace("\n", " ")
        lines.append(f"  - {wine}{score_str}: {note}")
    suffix = f" (showing {len(picked)} of {len(entries)})" if len(entries) > cap else ""
    return f"{label}{suffix}:\n" + "\n".join(lines) + "\n"


def synthesize_palate_from_notes(
    profile_data: dict,
    anthropic_api_key: str,
    anthropic_model: str,
) -> dict | None:
    """Single Anthropic tool-use call to synthesize a rich palate profile from raw CT notes.

    Builds the deterministic structured signals first (top_varietals, top_regions,
    top_producers, highly_rated, avg_spend) and feeds them to Claude as grounding
    context alongside the raw tasting notes grouped by score tier. Claude returns
    multi-word sensory descriptors, taste_markers, style_summary, and a 2-3 sentence
    palate_persona naming signature styles.

    Returns the synthesized dict (shape mirrors seed_profile.infer_profile_from_seeds()
    output + ``palate_persona``), or None if there are no usable notes to synthesize from.
    Raises anthropic.APIError or RuntimeError on Claude-side failures — callers should
    catch and fall back to the deterministic profile.
    """
    logger = logging.getLogger("sommelier.profile")

    # Strip any prior synthesis so the deterministic helper below produces a clean
    # frequency-derived base for the structured fields we echo through unchanged.
    raw_view = {k: v for k, v in profile_data.items() if k != SYNTHESIZED_KEY}
    deterministic = build_taste_profile(raw_view)

    notes, low_threshold, high_threshold = _gather_scored_notes(raw_view)
    if not notes:
        logger.info("synthesize_palate_from_notes: no tasting notes present, skipping synthesis")
        return None

    high_tier, mid_tier, low_tier = _bucket_notes_by_tier(notes, low_threshold, high_threshold)
    note_count = len(notes)
    cap = _SYNTHESIS_NOTES_PER_TIER

    notes_section = (
        _format_note_block("HIGH-SCORED (loved)", high_tier, cap)
        + _format_note_block("MID-SCORED (liked/acceptable)", mid_tier, cap)
        + _format_note_block("LOW-SCORED (disliked)", low_tier, cap)
    )

    rated_labels = []
    for b in deterministic.get("highly_rated", [])[:10]:
        parts = [b.get("vintage", ""), b.get("producer", ""), b.get("wine", "")]
        label = " ".join(p for p in parts if p).strip()
        if label:
            rated_labels.append(label)

    structured_context = (
        f"Top varietals (frequency-ranked): {deterministic.get('top_varietals', [])}\n"
        f"Top regions (frequency-ranked): {deterministic.get('top_regions', [])}\n"
        f"Top producers (frequency-ranked): {deterministic.get('top_producers', [])}\n"
        f"Highly rated bottles: {rated_labels}\n"
        f"Average spend (USD/bottle): {deterministic.get('avg_spend')}\n"
        f"Total tasting notes available: {note_count}\n"
    )

    confidence_hint = (
        "Notes are sparse — be conservative and mark inference_confidence='low'."
        if note_count < _SYNTHESIS_LOW_CONFIDENCE_THRESHOLD
        else "Lean into a full sommelier persona — extrapolate signature styles even when the notes only hint at them."
    )

    prompt_text = (
        "You are a master sommelier synthesizing a rich palate profile for a wine buyer from their\n"
        "CellarTracker tasting history. The buyer's free-text notes are short and inconsistent;\n"
        "your job is to read between the lines and infer the deeper style signature — texture,\n"
        "fermentation character, tension/breadth, oxidative/reductive leanings, oak handling.\n\n"
        "GROUND TRUTH (structured signals — use for context, do NOT echo as style phrases):\n"
        f"{structured_context}\n"
        "RAW TASTING NOTES (grouped by score tier, with score in brackets):\n"
        f"{notes_section}\n"
        "Synthesis rules:\n"
        "- preferred_descriptors: 4-7 MULTI-WORD sensory phrases. Focus on texture, weight,\n"
        "  fermentation character, tension. Examples: 'taut mineral-driven whites with laser acidity',\n"
        "  'oxidative sherried complexity', 'reductive sulfurous reds with fine tannin',\n"
        "  'silky medium-bodied reds with savoury earth'. Never echo grape or region names.\n"
        "- avoided_styles: 2-4 multi-word phrases naming styles to avoid, grounded in the\n"
        "  low-scored notes when present; otherwise infer the counterpoint to the loved profile.\n"
        "- style_summary: ONE sentence (20-30 words) capturing overall palate character without\n"
        "  naming specific grapes or regions.\n"
        "- taste_markers: integer 1-5 scores for acidity, tannin, body, oak. Treat 3 as neutral.\n"
        "  Use the high-scored notes as your ground truth for the scale.\n"
        "- palate_persona: 2-3 sentences naming signature style preferences in plain language.\n"
        "  Example: 'Loves oxidative, sherried complexity and reductive whites with tension.\n"
        "  Averse to overtly oaky reds and fruit-forward styles. Prefers wines with savoury\n"
        "  earth and fine tannin over plush, polished fruit.' Be specific and opinionated.\n"
        "- inference_confidence: 'high' if notes are extensive and stylistically coherent;\n"
        "  'medium' if the set is sparse but sensible; 'low' if contradictory or minimal.\n"
        "- top_varietals, top_regions, top_producers, highly_rated, avg_spend: echo the\n"
        "  ground-truth values verbatim — they are deterministic, not inferred.\n\n"
        f"{confidence_hint}"
    )

    tool = {
        "name": "synthesize_palate_profile",
        "description": "Synthesize a rich palate profile from CellarTracker notes and structured metadata.",
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
                "preferred_descriptors": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "4-7 multi-word sensory phrases.",
                },
                "avoided_styles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "2-4 multi-word phrases naming styles to avoid.",
                },
                "avg_spend": {"type": ["integer", "null"]},
                "style_summary": {
                    "type": "string",
                    "description": "One sentence, 20-30 words.",
                },
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
                "palate_persona": {
                    "type": "string",
                    "description": "2-3 sentences naming signature style preferences in plain language.",
                },
                "inference_confidence": {
                    "type": "string",
                    "enum": ["high", "medium", "low"],
                },
            },
            "required": [
                "top_varietals", "top_regions", "top_producers", "highly_rated",
                "preferred_descriptors", "avoided_styles", "style_summary",
                "taste_markers", "palate_persona", "inference_confidence",
            ],
        },
    }

    logger.info(
        "synthesize_palate_from_notes: calling Claude model=%s notes=%d high=%d mid=%d low=%d",
        anthropic_model, note_count, len(high_tier), len(mid_tier), len(low_tier),
    )

    client = anthropic.Anthropic(api_key=anthropic_api_key)
    response = client.messages.create(
        model=anthropic_model,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt_text}],
        tools=[tool],
        tool_choice={"type": "tool", "name": "synthesize_palate_profile"},
    )

    tool_block = next(
        (b for b in response.content if b.type == "tool_use" and b.name == "synthesize_palate_profile"),
        None,
    )
    if not tool_block:
        raise RuntimeError("Anthropic did not return the expected tool_use block for palate synthesis.")

    synthesized = dict(tool_block.input)
    synthesized["profile_source"] = "cellartracker_synthesized"
    synthesized["note_count"] = note_count

    logger.info(
        "synthesize_palate_from_notes: success confidence=%s descriptors=%d persona_chars=%d",
        synthesized.get("inference_confidence"),
        len(synthesized.get("preferred_descriptors", [])),
        len(synthesized.get("palate_persona", "")),
    )
    return synthesized


def persist_synthesized_profile(synthesized: dict) -> None:
    """Merge the synthesized palate dict into profile_data.json under ``_synthesized``.

    Unlike persist_seed_profile, this preserves the underlying CellarTracker rows
    (list/notes/consumed/purchases) — they are the source the synthesis was built
    from. Busts the profile cache after write so subsequent loads see the update.
    """
    logger = logging.getLogger("sommelier.profile")
    data = load_profile_data()
    data[SYNTHESIZED_KEY] = synthesized
    PROFILE_DATA_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    bust_profile_cache()
    logger.info("persist_synthesized_profile: wrote synthesized palate to %s", PROFILE_DATA_PATH)


def clear_synthesized_profile() -> None:
    """Remove any prior synthesized palate from profile_data.json.

    Called before a fresh synthesis attempt so a failed Claude call doesn't leave
    stale synthesized data behind (the deterministic fallback in build_taste_profile()
    can then take over until the next successful synthesis).
    """
    data = load_profile_data()
    if SYNTHESIZED_KEY not in data:
        return
    data.pop(SYNTHESIZED_KEY, None)
    PROFILE_DATA_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    bust_profile_cache()


def build_taste_profile(profile_data: dict) -> dict:
    """Derive structured taste signals from merged profile export data.

    Short-circuit order (first match wins):
      1. ``_synthesized`` — LLM-synthesized CellarTracker palate produced by
         synthesize_palate_from_notes() at upload time. Same shape as the
         seed-bottle inferred profile (multi-word descriptors, taste_markers,
         palate_persona, style_summary).
      2. ``_inferred`` — seed-bottle profile from infer_profile_from_seeds().
      3. Fallback: deterministic frequency-token derivation from raw notes
         (used when synthesis hasn't run or failed).

    Any user manual edits stored under ``_overrides`` are merged on top of the
    derived/inferred/synthesized base before returning, so /profile-summary and the
    recommendation prompt both see the edited values.
    """
    if not isinstance(profile_data, dict):
        profile_data = {}

    overrides = profile_data.get("_overrides") or {}

    synthesized = profile_data.get("_synthesized")
    if isinstance(synthesized, dict) and synthesized:
        return apply_profile_overrides(synthesized, overrides)

    inferred = profile_data.get("_inferred")
    if isinstance(inferred, dict) and inferred:
        return apply_profile_overrides(inferred, overrides)

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

    derived = {
        "top_varietals": top_varietals,
        "top_regions": top_regions,
        "top_producers": top_producers,
        "highly_rated": highly_rated,
        "preferred_descriptors": preferred_descriptors,
        "avoided_styles": avoided_styles,
        "avg_spend": avg_spend,
    }
    return apply_profile_overrides(derived, overrides)


def build_taste_profile_pydantic(profile_data: dict) -> TasteProfile:
    """Convert derived taste profile dict to TasteProfile Pydantic model."""
    structured = build_taste_profile(profile_data)

    preferred_grapes = structured.get("top_varietals", [])
    preferred_regions = structured.get("top_regions", [])
    preferred_styles = structured.get("preferred_descriptors", [])
    avoided_styles = structured.get("avoided_styles", [])
    avg_spend = structured.get("avg_spend")

    budget_min = None
    budget_max = None
    if avg_spend is not None:
        budget_min = max(0, int(round(avg_spend)) - 10)
        budget_max = int(round(avg_spend)) + 10

    profile_source = structured.get("profile_source", "cellartracker")
    inference_confidence = (
        structured.get("inference_confidence")
        if profile_source in ("seed_bottles", "cellartracker_synthesized")
        else None
    )

    return TasteProfile(
        preferred_grapes=preferred_grapes,
        preferred_regions=preferred_regions,
        preferred_styles=preferred_styles,
        avoided_styles=avoided_styles,
        budget_min=budget_min,
        budget_max=budget_max,
        profile_source=profile_source,
        inference_confidence=inference_confidence,
    )


def _profile_data_empty(profile_data: dict) -> bool:
    if not profile_data:
        return True
    return not any(
        (isinstance(v, list) and len(v) > 0) or (isinstance(v, dict) and len(v) > 0)
        for v in profile_data.values()
    )


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
        clauses.append(f"typical spend ${low}–{high} per bottle")

    if not clauses:
        return "Based on cellar and tasting history: limited structured data; rely on general guidance."

    body = "; ".join(clauses)
    return f"Based on cellar and tasting history: {body}."


def extract_profile_preference_terms(profile_data: dict) -> dict:
    """Extract matchable keyword lists from structured profile data.

    Returns a dict with two keys:
      - ``preferred``: varietal + region terms the owner favours.
      - ``avoided``: empty list (CT avoided terms are flavour words, not bottle metadata).
    """
    structured = build_taste_profile(profile_data)
    preferred = (structured.get("top_varietals") or []) + (structured.get("top_regions") or [])
    return {"preferred": preferred, "avoided": []}


def build_enriched_profile_text_basic() -> str:
    """Build taste profile text from loaded profile data or return owner default (non-enriched version)."""
    if not PROFILE_DATA_PATH.is_file():
        from prompt import OWNER_PROFILE
        return OWNER_PROFILE

    data = load_profile_data()
    if _profile_data_empty(data):
        from prompt import OWNER_PROFILE
        return OWNER_PROFILE

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
        "You are a master sommelier building a palate profile for a wine buyer.\n"
        "Your job: translate raw frequency data into STYLE descriptors — focus on "
        "texture, weight, and flavour character. Ignore grape variety and region labels; "
        "describe how wines feel and taste, not where they come from.\n\n"
        f"Top varietals (context only — do NOT echo these as style phrases): {raw.get('top_varietals', [])[:7]}\n"
        f"Top regions (context only — do NOT echo these as style phrases): {raw.get('top_regions', [])[:5]}\n"
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
        "without mentioning specific grapes or regions"
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
    """Like build_enriched_profile_text_basic() but enriches derived terms via Anthropic Claude."""
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

    source = structured.get("profile_source")
    if source in ("seed_bottles", "cellartracker_synthesized"):
        logger.info("build_enriched_profile_text: profile already enriched (source=%s), skipping anthropic call", source)
        enriched = structured
    else:
        logger.info("build_enriched_profile_text: calling enrich_profile_with_anthropic")
        enriched = enrich_profile_with_anthropic(structured, anthropic_api_key, anthropic_model)

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


def derive_taste_markers(descriptors: List[str]) -> dict:
    """Heuristically score Acidity, Tannin, Body, and Oak on a 1–5 scale
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
