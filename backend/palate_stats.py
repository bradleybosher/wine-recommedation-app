"""Statistical palate analysis — pure Python, no LLM.

Runs *before* the Claude synthesis call and produces structured evidence that
the synthesis prompt can be grounded in counts rather than vibes.  Also feeds
retrieval scoring (top_producers, avoided style tokens) and the aspirational
skew block (cellar intent vs consumed habit).
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import TypedDict

# ---------------------------------------------------------------------------
# Keyword lexicons
# ---------------------------------------------------------------------------

_POSITIVE_SENTIMENT = {
    "love", "loved", "excellent", "outstanding", "exceptional", "brilliant",
    "stunning", "beautiful", "great", "fantastic", "wonderful", "superb",
    "delicious", "amazing", "perfect", "incredible", "magnificent", "sublime",
    "elegant", "complex", "refined", "precise", "expressive", "vibrant",
    "fresh", "lively", "mineral", "pure", "profound", "serious", "impressive",
    "best", "favourite", "favorite", "highly recommend", "would buy again",
    "buy more", "cellar", "age well", "value", "bargain", "steal",
}

_NEGATIVE_SENTIMENT = {
    "dislike", "disliked", "poor", "bad", "disappointing", "disappointing",
    "unbalanced", "flabby", "flat", "dull", "bland", "harsh", "bitter",
    "too oaky", "over-oaked", "oaky", "jammy", "too alcoholic", "hot",
    "too sweet", "clumsy", "astringent", "aggressive", "coarse", "rough",
    "wouldn't buy", "would not buy", "avoid", "pass", "overrated",
    "not worth", "waste", "terrible", "awful", "horrible",
}

_NATURAL_WINE_MARKERS = {
    "pét nat", "pet nat", "pétillant naturel", "petillant naturel",
    "brut nature", "brut zéro", "brut zero", "non dosé", "non dose",
    "extra brut", "grower champagne", "grower-producer",
    "natural", "biodynamic", "organic", "low intervention", "low-intervention",
    "unfiltered", "unfined", "skin contact", "orange wine", "amphora",
    "minimal sulphur", "no sulphur",
}

_OXIDATIVE_MARKERS = {
    "oxidative", "oxidised", "oxidized", "nutty", "sherry", "rancio",
    "vin jaune", "sous voile", "sous-voile", "jura", "savagnin", "ouillé",
    "manzanilla", "fino", "amontillado",
}

_AGING_MARKERS = {
    "needed more time", "needs time", "would benefit from", "will age",
    "cellar", "cellaring", "too young", "not ready", "lay down",
    "more bottle age", "with some age", "great ageing", "ageing potential",
    "aging potential",
}

# Style tokens distilled from avoided-style phrases
_AVOIDED_STYLE_TOKEN_MAP: dict[str, list[str]] = {
    "oaky": ["oaky", "heavily oaked", "over-oaked", "oak dominant", "toasty oak"],
    "jammy": ["jammy", "jam", "fruit bomb", "fruit-forward", "over-ripe"],
    "high-alcohol": ["high alcohol", "hot", "too alcoholic", "alcohol heat"],
    "flabby": ["flabby", "low acidity", "lacks acidity", "no acidity"],
    "sweet-sparkling": ["sweet sparkling", "demi-sec", "doux", "off-dry sparkling"],
    "heavy": ["heavy", "ponderous", "weighty", "massive", "overwrought"],
    "tannic": ["harsh tannins", "grippy tannins", "astringent", "too tannic"],
}


def _note_sentiment(note_text: str) -> str:
    """Return 'positive', 'negative', or 'neutral' for a note string."""
    low = note_text.lower()
    pos = sum(1 for w in _POSITIVE_SENTIMENT if w in low)
    neg = sum(1 for w in _NEGATIVE_SENTIMENT if w in low)
    if pos > neg:
        return "positive"
    if neg > pos:
        return "negative"
    return "neutral"


def _extract_avoided_tokens(avoided_style_sentences: list[str]) -> list[str]:
    """Distil full avoided-style sentences into single-token markers."""
    tokens: set[str] = set()
    combined = " ".join(s.lower() for s in avoided_style_sentences)
    for token, phrases in _AVOIDED_STYLE_TOKEN_MAP.items():
        if any(phrase in combined for phrase in phrases):
            tokens.add(token)
    return sorted(tokens)


def _parse_price(price_val: object) -> float | None:
    if price_val is None:
        return None
    s = re.sub(r"[^\d.]", "", str(price_val))
    try:
        return float(s) if s else None
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# TypedDicts for structured output
# ---------------------------------------------------------------------------

class FrequencyEntry(TypedDict):
    total: int
    positive: int
    negative: int
    net: int


class PriceStats(TypedDict):
    count: int
    median: float
    p25: float
    p75: float


class StyleSignals(TypedDict):
    natural_wine_affinity: bool
    oxidative_affinity: bool
    aging_preference: bool
    value_driven: bool


class AspirationalSkew(TypedDict):
    over_represented: list[str]   # categories in cellar at >1.5× consumed rate
    summary_line: str             # one-line for system prompt


class PalateStats(TypedDict):
    producer_frequency: dict[str, FrequencyEntry]
    region_frequency: dict[str, FrequencyEntry]
    varietal_frequency: dict[str, FrequencyEntry]
    price_distribution: dict[str, PriceStats]  # keyed by Color ("Red","White","Rosé",…)
    style_signals: StyleSignals
    avoided_style_tokens: list[str]
    top_producers: list[str]   # top-5 by net positive score
    note_count: int
    aspirational_skew: AspirationalSkew | None


# ---------------------------------------------------------------------------
# Core computation
# ---------------------------------------------------------------------------

def _build_frequency(rows: list[dict], key: str) -> dict[str, FrequencyEntry]:
    freq: dict[str, FrequencyEntry] = {}
    for row in rows:
        val = (row.get(key) or "").strip()
        if not val:
            continue
        sentiment = _note_sentiment(row.get("ConsumptionNote") or "")
        entry = freq.setdefault(val, FrequencyEntry(total=0, positive=0, negative=0, net=0))
        entry["total"] += 1
        if sentiment == "positive":
            entry["positive"] += 1
            entry["net"] += 1
        elif sentiment == "negative":
            entry["negative"] += 1
            entry["net"] -= 1
    return freq


def _price_stats(prices: list[float]) -> PriceStats:
    prices = sorted(prices)
    n = len(prices)
    if n == 0:
        return PriceStats(count=0, median=0.0, p25=0.0, p75=0.0)
    median = prices[n // 2] if n % 2 else (prices[n // 2 - 1] + prices[n // 2]) / 2
    p25 = prices[n // 4]
    p75 = prices[3 * n // 4]
    return PriceStats(count=n, median=round(median, 2), p25=round(p25, 2), p75=round(p75, 2))


def compute_palate_stats(
    consumed_rows: list[dict],
    inventory_rows: list[dict] | None = None,
    avoided_styles: list[str] | None = None,
) -> PalateStats:
    """Derive structured statistics from CellarTracker rows.

    Parameters
    ----------
    consumed_rows:
        List of dicts from ``profile_data["consumed"]`` — each entry has at
        least ``Producer``, ``Varietal``, ``MasterVarietal``, ``Region``,
        ``Color``, ``Price``, ``ConsumptionNote``.
    inventory_rows:
        Optional list of inventory bottle dicts for aspirational-skew
        computation.  When ``None`` the aspirational block is omitted.
    avoided_styles:
        Existing avoided-style sentences from the profile (if any) to extract
        tokens from in addition to note analysis.
    """
    producer_freq = _build_frequency(consumed_rows, "Producer")
    region_freq = _build_frequency(consumed_rows, "Region")
    varietal_freq = _build_frequency(consumed_rows, "MasterVarietal")

    # Price distribution by colour
    prices_by_color: dict[str, list[float]] = defaultdict(list)
    for row in consumed_rows:
        p = _parse_price(row.get("Price"))
        color = (row.get("Color") or "Unknown").strip()
        if p is not None and p > 0:
            prices_by_color[color].append(p)
    price_distribution = {c: _price_stats(ps) for c, ps in prices_by_color.items()}

    # Style signals — scan all notes
    combined_notes = " ".join(
        (row.get("ConsumptionNote") or "").lower() for row in consumed_rows
    )
    style_signals = StyleSignals(
        natural_wine_affinity=any(m in combined_notes for m in _NATURAL_WINE_MARKERS),
        oxidative_affinity=any(m in combined_notes for m in _OXIDATIVE_MARKERS),
        aging_preference=any(m in combined_notes for m in _AGING_MARKERS),
        value_driven=any(w in combined_notes for w in {"value", "bargain", "steal", "great price", "for the price"}),
    )

    # Avoided style tokens from note analysis + existing avoided_styles sentences
    negative_note_tokens: set[str] = set()
    for row in consumed_rows:
        note = (row.get("ConsumptionNote") or "").lower()
        sentiment = _note_sentiment(note)
        if sentiment == "negative":
            for token, phrases in _AVOIDED_STYLE_TOKEN_MAP.items():
                if any(phrase in note for phrase in phrases):
                    negative_note_tokens.add(token)
    existing_tokens = set(_extract_avoided_tokens(avoided_styles or []))
    avoided_style_tokens = sorted(negative_note_tokens | existing_tokens)

    # Top producers by net positive score (minimum 2 appearances)
    top_producers = [
        prod for prod, entry in sorted(
            producer_freq.items(), key=lambda x: (x[1]["net"], x[1]["total"]), reverse=True
        )
        if entry["total"] >= 2
    ][:10]

    # Aspirational skew (cellar vs consumed)
    aspirational: AspirationalSkew | None = None
    if inventory_rows:
        inv_counter: Counter[str] = Counter()
        consumed_counter: Counter[str] = Counter()
        for row in inventory_rows:
            cat = (row.get("Varietal") or row.get("MasterVarietal") or "").strip()
            if cat:
                inv_counter[cat] += int(row.get("Quantity") or row.get("TotalQuantity") or 1)
        for row in consumed_rows:
            cat = (row.get("MasterVarietal") or "").strip()
            if cat:
                consumed_counter[cat] += 1

        total_inv = max(sum(inv_counter.values()), 1)
        total_con = max(sum(consumed_counter.values()), 1)

        over_rep: list[tuple[float, str]] = []
        for cat, inv_count in inv_counter.items():
            inv_share = inv_count / total_inv
            con_share = consumed_counter.get(cat, 0) / total_con
            if inv_share > 0 and con_share > 0 and inv_share / con_share >= 1.5:
                over_rep.append((inv_share / con_share, cat))
            elif inv_share > 0.05 and consumed_counter.get(cat, 0) == 0:
                over_rep.append((inv_share * 10, cat))  # heavy weight for uncounted buys

        over_rep.sort(reverse=True)
        over_rep_names = [name for _, name in over_rep[:5]]

        if over_rep_names:
            summary_line = (
                f"Cellar over-represents {', '.join(over_rep_names[:3])} relative to "
                "drinking history — favour these when available on the list."
            )
        else:
            summary_line = ""

        aspirational = AspirationalSkew(
            over_represented=over_rep_names,
            summary_line=summary_line,
        )

    return PalateStats(
        producer_frequency=producer_freq,
        region_frequency=region_freq,
        varietal_frequency=varietal_freq,
        price_distribution=price_distribution,
        style_signals=style_signals,
        avoided_style_tokens=avoided_style_tokens,
        top_producers=top_producers,
        note_count=len(consumed_rows),
        aspirational_skew=aspirational,
    )


# ---------------------------------------------------------------------------
# Prompt formatting
# ---------------------------------------------------------------------------

def format_stats_for_prompt(stats: PalateStats) -> str:
    """Render PalateStats as a compact block for injection into the synthesis prompt."""
    lines: list[str] = ["## Statistical Evidence (derived from tasting notes — treat as ground truth)\n"]

    note_count = stats["note_count"]
    lines.append(f"**Note count:** {note_count}\n")

    # Top varietals by net score
    top_varietals = sorted(
        stats["varietal_frequency"].items(),
        key=lambda x: (x[1]["net"], x[1]["total"]),
        reverse=True,
    )[:8]
    if top_varietals:
        lines.append("**Top varietals (by net positive mentions):**")
        for var, e in top_varietals:
            lines.append(f"  - {var}: {e['total']} notes, {e['positive']} positive, {e['negative']} negative (net {e['net']:+d})")
        lines.append("")

    # Top regions
    top_regions = sorted(
        stats["region_frequency"].items(),
        key=lambda x: (x[1]["net"], x[1]["total"]),
        reverse=True,
    )[:8]
    if top_regions:
        lines.append("**Top regions (by net positive mentions):**")
        for reg, e in top_regions:
            lines.append(f"  - {reg}: {e['total']} notes, net {e['net']:+d}")
        lines.append("")

    # Top producers
    if stats["top_producers"]:
        lines.append(f"**Repeat producers (strong positive signal):** {', '.join(stats['top_producers'][:8])}\n")

    # Price distribution
    for color, ps in stats["price_distribution"].items():
        if ps["count"] > 0:
            lines.append(
                f"**{color} wine spend:** median £{ps['median']:.0f}  "
                f"(p25 £{ps['p25']:.0f} – p75 £{ps['p75']:.0f}, n={ps['count']})"
            )
    lines.append("")

    # Style signals
    sigs = stats["style_signals"]
    active = [k.replace("_", " ") for k, v in sigs.items() if v]
    if active:
        lines.append(f"**Style signals detected:** {', '.join(active)}\n")

    # Avoided tokens
    if stats["avoided_style_tokens"]:
        lines.append(f"**Avoided style tokens (from note analysis):** {', '.join(stats['avoided_style_tokens'])}\n")

    # Aspirational skew
    asp = stats.get("aspirational_skew")
    if asp and asp.get("summary_line"):
        lines.append(f"**Aspirational skew:** {asp['summary_line']}\n")

    return "\n".join(lines)
