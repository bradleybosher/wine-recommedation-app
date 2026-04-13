import csv
import datetime
import io
import json
import logging
import re
import time
import unicodedata
from pathlib import Path

from models import TasteProfile

logger = logging.getLogger("sommelier.inventory")

_SOM_DIR = Path(__file__).resolve().parent
CACHE_PATH = _SOM_DIR / "inventory.json"
CACHE_TTL  = 60 * 60 * 24 * 7  # 1 week — you trigger refresh manually


def decode_cellartracker_upload(raw: bytes) -> str:
    """CellarTracker tab exports are often Windows-1252, not UTF-8."""
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _quantity_positive(row: dict) -> bool:
    raw = row.get("Quantity", 0) or 0
    try:
        return float(str(raw).strip()) > 0
    except (ValueError, TypeError):
        return False


def parse_ct_csv(csv_text: str) -> list[dict]:
    # CT exports TSV not CSV
    reader = csv.DictReader(io.StringIO(csv_text), delimiter="\t")
    return [row for row in reader if _quantity_positive(row)]

def save_inventory(csv_text: str) -> list[dict]:
    bottles = parse_ct_csv(csv_text)
    CACHE_PATH.write_text(json.dumps({
        "bottles": bottles,
        "saved_at": time.time()
    }))
    return bottles

def load_inventory() -> dict | None:
    if not CACHE_PATH.exists():
        return None
    data = json.loads(CACHE_PATH.read_text())
    age_hours = (time.time() - data["saved_at"]) / 3600
    return {
        "bottles": data["bottles"],
        "age_hours": round(age_hours, 1),
        "stale": age_hours > 168
    }


def _fold_for_match(text: str) -> str:
    """Lowercase and strip accents so e.g. côte-rôtie matches cote-rotie in exports."""
    if not text:
        return ""
    decomposed = unicodedata.normalize("NFD", text.casefold())
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


# ---------------------------------------------------------------------------
# Known wine style / varietal / region keywords used for heuristic extraction
# from unstructured restaurant wine list text.
# ---------------------------------------------------------------------------
_WINE_STYLE_KEYWORDS: list[str] = [
    # Red varietals
    "pinot noir", "cabernet sauvignon", "merlot", "syrah", "shiraz", "grenache",
    "nebbiolo", "sangiovese", "tempranillo", "malbec", "barbera", "dolcetto",
    "gamay", "cabernet franc", "mourvedre", "mourvèdre", "zinfandel",
    # White varietals
    "chardonnay", "sauvignon blanc", "riesling", "pinot gris", "pinot grigio",
    "gewurztraminer", "viognier", "roussanne", "marsanne", "chenin blanc",
    "grüner veltliner", "gruner veltliner", "albariño", "albarino", "verdejo",
    "fiano", "vermentino", "muscadet",
    # Champagne / sparkling
    "champagne", "blanc de noirs", "blanc de blancs", "crémant", "cremant",
    "prosecco", "cava", "sekt",
    # Burgundy
    "bourgogne", "burgundy", "chablis", "meursault", "puligny", "chassagne",
    "gevrey", "chambolle", "vosne", "nuits", "pommard", "volnay", "corton",
    "beaujolais", "morgon", "moulin", "fleurie",
    # Bordeaux
    "bordeaux", "saint-émilion", "saint-julien", "pauillac", "margaux",
    "saint-estèphe", "pomerol", "graves", "sauternes",
    # Rhône
    "rhône", "rhone", "côte-rôtie", "cote-rotie", "hermitage", "crozes",
    "châteauneuf", "chateauneuf", "gigondas", "vacqueyras", "condrieu",
    # Loire
    "loire", "sancerre", "pouilly", "vouvray", "savennières", "savennieres",
    "chinon", "bourgueil", "anjou",
    # Italy
    "barolo", "barbaresco", "brunello", "chianti", "amarone", "valpolicella",
    "soave", "prosecco",
    # Spain
    "rioja", "ribera del duero", "priorat",
    # Germany / Austria
    "mosel", "rheingau", "rheinhessen", "pfalz", "wachau",
    # New World
    "napa", "sonoma", "willamette", "margaret river", "coonawarra",
    "marlborough", "central otago", "barossa",
    # Alsace
    "alsace",
]


def extract_terms_from_wine_list_text(text: str) -> list[str]:
    """Scan raw restaurant wine list text for known style/varietal/region keywords.

    Returns only the keywords that actually appear in the text, deduplicated and
    sorted by length descending (so multi-word terms are matched before their
    component words when used as filter signals).
    """
    if not text:
        return []
    folded = _fold_for_match(text)
    found = [kw for kw in _WINE_STYLE_KEYWORDS if _fold_for_match(kw) in folded]
    # Deduplicate while preserving order, longest first (multi-word > single-word)
    seen: set[str] = set()
    result: list[str] = []
    for kw in sorted(found, key=len, reverse=True):
        if kw not in seen:
            seen.add(kw)
            result.append(kw)
    return result


def _bottle_haystack(b: dict) -> str:
    return _fold_for_match(" ".join(
        str(b.get(k) or "")
        for k in ("Varietal", "Appellation", "Wine", "Producer", "Region", "SubRegion")
    ))


def _score_bottle(
    bottle: dict,
    restaurant_terms: list[str],
    profile_prefs: dict,
    current_year: int,
) -> float:
    """Score a cellar bottle against restaurant style signals and owner preferences.

    Returns float("-inf") for hard-excluded bottles (avoided styles matched).

    Weights:
      - Profile preferred term match: +1.5 per term
      - Restaurant list term match:   +1.0 per term
      - Drinking window open:         +0.5
      - Too young (BeginConsume > now): -0.3
    """
    hay = _bottle_haystack(bottle)

    for term in profile_prefs.get("avoided", []):
        if _fold_for_match(term) in hay:
            return float("-inf")

    score = 0.0

    for term in profile_prefs.get("preferred", []):
        if _fold_for_match(term) in hay:
            score += 1.5

    for term in restaurant_terms:
        if _fold_for_match(term) in hay:
            score += 1.0

    try:
        begin = int(bottle.get("BeginConsume") or 0)
        end = int(bottle.get("EndConsume") or 9999)
        if begin <= current_year <= end:
            score += 0.5
        elif current_year < begin:
            score -= 0.3
    except (ValueError, TypeError):
        pass

    return score


# Style expansion map kept for override_terms backward compatibility.
_STYLE_MAP: dict[str, list[str]] = {
    "burgundy":   ["pinot noir", "burgundy", "bourgogne", "gevrey", "chambolle"],
    "chablis":    ["chablis", "chardonnay"],
    "champagne":  ["champagne", "blanc de noirs", "crémant"],
    "nebbiolo":   ["nebbiolo", "barolo", "barbaresco"],
    "chenin":     ["chenin", "vouvray", "savennières"],
    "rhone":      ["syrah", "grenache", "côte-rôtie", "hermitage"],
    "loire":      ["cabernet franc", "chinon", "bourgueil"],
    "beaujolais": ["gamay", "beaujolais", "morgon", "moulin"],
}


# ---------------------------------------------------------------------------
# Wine list pre-filter — removes poor profile matches and food items before
# the list reaches the LLM, cutting token bloat on long menus.
# ---------------------------------------------------------------------------

_PRICE_RE = re.compile(r"\$?\s*(\d{1,4}(?:\.\d{1,2})?)")
_VINTAGE_RE = re.compile(r"\b(19|20)\d{2}\b")

# Reliable food indicators: cooking methods and dish categories that essentially
# never appear in wine names.  The dual check (_is_wine_candidate) guards
# against false positives for lines that have both food words and wine signals.
_FOOD_KEYWORDS: frozenset[str] = frozenset([
    # Cooking methods
    "grilled", "roasted", "pan-seared", "pan-roasted", "braised", "baked", "fried",
    "sauteed", "sautéed", "poached", "smoked", "slow-cooked", "steamed", "cured",
    "pickled", "tartare", "carpaccio", "wood-fired", "tempura", "confit", "stir-fried",
    # Menu section / category words
    "appetizer", "appetizers", "entrée", "entree", "starter", "starters",
    "dessert", "desserts", "mains", "courses", "sides", "side dish",
    "prix fixe", "tasting menu", "a la carte", "à la carte",
    # Proteins and dishes that don't share names with wine regions
    "pasta", "pizza", "burger", "sandwich", "risotto", "gnocchi",
    "chicken breast", "beef tenderloin", "pork chop", "veal chop",
    "caesar salad", "house salad", "soup of the day",
    "salmon", "tuna", "duck", "lamb chop", "short rib", "scallop",
    "shrimp", "lobster", "oyster", "octopus", "halibut", "branzino",
    "filet mignon", "rack of",
    # Generic dish descriptors
    "salad", "soup", "steak", "fillet", "filet", "sauce", "puree", "ragu", "ragù",
    # Serving language
    "served with", "accompanied by",
])


def _extract_price(line: str) -> float | None:
    """Return the first numeric price found in a line, or None."""
    m = _PRICE_RE.search(line)
    if m:
        try:
            return float(m.group(1))
        except (ValueError, TypeError):
            pass
    return None


def _is_structural_line(line: str) -> bool:
    """True for blank lines, section headers, and very short lines."""
    stripped = line.strip()
    if not stripped:
        return True
    if stripped.isupper():
        return True
    words = stripped.split()
    if len(words) <= 3 and not _PRICE_RE.search(stripped) and not _VINTAGE_RE.search(stripped):
        return True
    return False


def _is_wine_candidate(line: str, folded_wine_keywords: list[str]) -> bool:
    """True if the line looks like a wine entry (vintage year, known wine keyword, or price)."""
    stripped = line.strip()
    if _VINTAGE_RE.search(stripped):
        return True
    folded = _fold_for_match(stripped)
    if any(kw in folded for kw in folded_wine_keywords):
        return True
    # Price without food context counts as a weak wine signal
    if _PRICE_RE.search(stripped):
        folded_lower = folded
        if not any(fw in folded_lower for fw in _FOOD_KEYWORDS):
            return True
    return False


def _is_food_line(line: str) -> bool:
    """True if the line appears to be a food menu item rather than a wine entry."""
    folded = _fold_for_match(line)
    return any(fw in folded for fw in _FOOD_KEYWORDS)


def _score_wine_line(line: str, profile: TasteProfile) -> float:
    """Score a single wine list line against the taste profile."""
    folded = _fold_for_match(line)
    score = 0.0

    for grape in profile.preferred_grapes:
        if _fold_for_match(grape) in folded:
            score += 2.0

    for region in profile.preferred_regions:
        if _fold_for_match(region) in folded:
            score += 2.0

    for style in profile.avoided_styles:
        if _fold_for_match(style) in folded:
            score -= 3.0

    if profile.budget_max is not None:
        price = _extract_price(line)
        if price is not None:
            if price <= profile.budget_max * 1.5:
                score += 1.0
            elif price > profile.budget_max * 2.0:
                score -= 1.0

    return score


def filter_wine_list(wine_list_text: str, profile: TasteProfile | None) -> str:
    """Pre-filter a raw restaurant wine list to remove poor profile matches and food items.

    Processes the text line by line.  Structural lines (blank, section headers,
    very short lines) are passed through unchanged to preserve list formatting.
    Lines that look like wine entries are scored against the taste profile; those
    scoring below -1 are dropped.  Lines that look like food menu items (cooking
    methods, dish categories) are dropped unconditionally.

    Safety valve: if scoring alone would remove more than 60% of identified wine
    candidate lines, the original text is returned unchanged to prevent
    over-filtering on short or oddly-formatted lists.

    Args:
        wine_list_text: Raw text produced by parse_wine_list().
        profile: User's TasteProfile.  If None or has no preference signals,
            the original text is returned unchanged.

    Returns:
        Filtered wine list text (newline-joined).
    """
    if not wine_list_text:
        logger.debug("wine_list_filter: empty input, returning unchanged")
        return wine_list_text

    if profile is None or (
        not profile.preferred_grapes
        and not profile.preferred_regions
        and not profile.avoided_styles
    ):
        logger.debug("wine_list_filter: no profile signals, returning unchanged")
        return wine_list_text

    logger.debug(
        "wine_list_filter: input %d lines | grapes=%s regions=%s avoided=%s budget_max=%s",
        len(wine_list_text.splitlines()),
        profile.preferred_grapes,
        profile.preferred_regions,
        profile.avoided_styles,
        profile.budget_max,
    )
    logger.debug("wine_list_filter: input text=\n%s", wine_list_text)

    try:
        folded_wine_keywords = [_fold_for_match(kw) for kw in _WINE_STYLE_KEYWORDS]
        lines = wine_list_text.splitlines()

        candidate_count = 0
        score_drop_count = 0
        food_drop_count = 0
        unknown_drop_count = 0
        keep: list[bool] = []

        for line in lines:
            if _is_structural_line(line):
                keep.append(True)
                continue

            wine_candidate = _is_wine_candidate(line, folded_wine_keywords)

            # Drop food items that have no wine signals
            if _is_food_line(line) and not wine_candidate:
                logger.debug("wine_list_filter: drop food   | %s", line.strip())
                food_drop_count += 1
                keep.append(False)
                continue

            if wine_candidate:
                candidate_count += 1
                score = _score_wine_line(line, profile)
                if score < -1:
                    logger.debug("wine_list_filter: drop score=%.1f | %s", score, line.strip())
                    score_drop_count += 1
                    keep.append(False)
                else:
                    logger.debug("wine_list_filter: keep score=%.1f | %s", score, line.strip())
                    keep.append(True)
            else:
                # Unknown line type — drop aggressively; prefer clean LLM input
                logger.debug("wine_list_filter: drop unknown | %s", line.strip())
                unknown_drop_count += 1
                keep.append(False)

        # Safety check: don't over-filter on the scoring pass
        if candidate_count > 0:
            pct = int(score_drop_count * 100 / candidate_count)
            if pct > 60:
                logger.warning(
                    "wine_list_filter: would remove %d%% of entries, skipping filter", pct
                )
                return wine_list_text

        result = "\n".join(line for line, kept in zip(lines, keep) if kept)
        logger.debug(
            "wine_list_filter: output %d lines (dropped %d food, %d unknown, %d low-score of %d candidates)",
            len(result.splitlines()),
            food_drop_count,
            unknown_drop_count,
            score_drop_count,
            candidate_count,
        )
        logger.debug("wine_list_filter: output text=\n%s", result)
        return result

    except Exception:
        logger.exception("wine_list_filter: unexpected error, returning original text")
        return wine_list_text


def get_relevant_bottles(
    bottles: list[dict],
    restaurant_terms: list[str],
    profile_prefs: dict,
    override_terms: list[str] | None = None,
    limit: int = 30,
) -> list[dict]:
    """Return the top `limit` cellar bottles scored against restaurant style
    signals and owner taste preferences.

    Args:
        bottles: Full cellar inventory.
        restaurant_terms: Style keywords extracted from the restaurant wine list.
        profile_prefs: Dict with ``preferred`` and ``avoided`` keyword lists
            derived from the owner's taste profile.
        override_terms: When provided (user-supplied via API), used in place of
            ``restaurant_terms`` — expanded via the style map for convenience.
        limit: Maximum bottles to return (default 30).
    """
    current_year = datetime.date.today().year

    if override_terms:
        expanded: list[str] = []
        for t in override_terms:
            expanded += _STYLE_MAP.get(t.lower(), [t.lower()])
        effective_restaurant_terms = expanded
    else:
        effective_restaurant_terms = restaurant_terms

    scored = [
        (b, _score_bottle(b, effective_restaurant_terms, profile_prefs, current_year))
        for b in bottles
    ]
    # Drop hard-excluded bottles, then sort highest score first
    scored = [(b, s) for b, s in scored if s > float("-inf")]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [b for b, _ in scored[:limit]]