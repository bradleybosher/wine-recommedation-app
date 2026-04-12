import csv
import datetime
import io
import json
import time
import unicodedata
from pathlib import Path

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