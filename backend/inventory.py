import csv
<<<<<<< HEAD
import datetime
import io
import json
import logging
import re
=======
import io
import json
>>>>>>> 6caf2d0 (Initial commit: Setting up project structure)
import time
import unicodedata
from pathlib import Path

<<<<<<< HEAD
from models import TasteProfile

logger = logging.getLogger("sommelier.inventory")

=======
>>>>>>> 6caf2d0 (Initial commit: Setting up project structure)
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


<<<<<<< HEAD
# ---------------------------------------------------------------------------
# Known wine style / varietal / region keywords used for heuristic extraction
# from unstructured restaurant wine list text.
# ---------------------------------------------------------------------------
_WINE_STYLE_KEYWORDS: list[str] = [
    # Red varietals
    "pinot noir", "cabernet sauvignon", "merlot", "syrah", "shiraz", "grenache",
    "nebbiolo", "sangiovese", "tempranillo", "malbec", "barbera", "dolcetto",
    "gamay", "cabernet franc", "mourvedre", "mourvèdre", "zinfandel",
    "nero d'avola", "nerello mascalese", "aglianico", "montepulciano d'abruzzo",
    "primitivo", "corvina", "sagrantino", "lagrein", "teroldego", "refosco",
    "carmenere", "carménère", "petit verdot", "mencia", "mencía", "monastrell",
    "cinsault", "cinsaut", "carignan", "carignan", "counoise", "graciano",
    "blaufränkisch", "blaufrankisch", "zweigelt", "st. laurent",
    # White varietals
    "chardonnay", "sauvignon blanc", "riesling", "pinot gris", "pinot grigio",
    "gewurztraminer", "gewürztraminer", "viognier", "roussanne", "marsanne",
    "chenin blanc", "grüner veltliner", "gruner veltliner", "albariño", "albarino",
    "verdejo", "fiano", "vermentino", "muscadet", "verdicchio", "pecorino",
    "timorasso", "falanghina", "greco di tufo", "catarratto", "carricante",
    "garganega", "trebbiano", "ribolla gialla", "friulano", "tocai", "arneis",
    "cortese", "favorita", "rolle", "clairette", "picpoul", "picpoul de pinet",
    "torrontés", "torrontes", "palomino", "manzanilla", "pedro ximénez",
    "assyrtiko", "moschofilero", "xinomavro", "agiorgitiko",
    # Champagne / sparkling
    "champagne", "blanc de noirs", "blanc de blancs", "crémant", "cremant",
    "prosecco", "cava", "sekt", "franciacorta", "trento doc", "pétillant naturel",
    "petillant naturel", "pet-nat", "pét-nat", "metodo classico",
    # Rosé / orange / other types
    "rosé", "rose wine", "orange wine", "vin gris", "ramato",
    # Burgundy
    "bourgogne", "burgundy", "chablis", "meursault", "puligny", "chassagne",
    "gevrey", "chambolle", "vosne", "nuits-saint-georges", "nuits", "pommard",
    "volnay", "corton", "beaune", "st-aubin", "rully", "givry", "mercurey",
    "mâcon", "macon", "pouilly-fuissé", "pouilly-fuisse", "beaujolais",
    "morgon", "moulin-à-vent", "fleurie", "brouilly", "chiroubles", "juliénas",
    "saint-amour",
    # Bordeaux
    "bordeaux", "saint-émilion", "saint emilion", "saint-julien", "pauillac",
    "margaux", "saint-estèphe", "pomerol", "graves", "sauternes", "pessac",
    "listrac", "moulis", "médoc", "medoc", "haut-médoc", "haut medoc",
    "entre-deux-mers",
    # Rhône
    "rhône", "rhone", "côte-rôtie", "cote-rotie", "hermitage", "crozes-hermitage",
    "crozes", "châteauneuf-du-pape", "chateauneuf", "gigondas", "vacqueyras",
    "condrieu", "saint-joseph", "cornas", "lirac", "tavel",
    # Loire
    "loire", "sancerre", "pouilly-fumé", "pouilly-fume", "vouvray",
    "savennières", "savennieres", "chinon", "bourgueil", "anjou", "muscadet",
    "fiefs vendéens", "montlouis", "touraine", "menetou-salon",
    # Alsace
    "alsace", "alsatian",
    # Italy — regions
    "barolo", "barbaresco", "brunello di montalcino", "brunello", "chianti classico",
    "chianti", "amarone", "valpolicella", "soave", "gavi", "langhe", "piemonte",
    "piedmont", "etna", "sicilia", "sicily", "campania", "puglia", "alto adige",
    "südtirol", "trentino", "friuli", "collio", "colli orientali", "monferrato",
    "asti", "barbera d'alba", "barbera d'asti", "dolcetto d'alba",
    "morellino di scansano", "montepulciano", "sagrantino di montefalco",
    "abruzzo", "bolgheri", "maremma", "super tuscan",
    # Spain
    "rioja", "ribera del duero", "priorat", "penedès", "penedes", "rias baixas",
    "bierzo", "toro", "rueda", "cava", "jerez", "sherry", "manzanilla",
    "montilla-moriles",
    # Germany / Austria
    "mosel", "rheingau", "rheinhessen", "pfalz", "wachau", "kamptal",
    "kremstal", "burgenland", "steiermark",
    # South of France
    "provence", "bandol", "cassis", "languedoc", "roussillon",
    "coteaux d'aix", "les baux", "minervois", "corbières", "faugères",
    "saint-chinian", "pic saint loup", "costières de nîmes",
    # New World — USA
    "napa", "napa valley", "sonoma", "sonoma coast", "willamette",
    "russian river", "alexander valley", "paso robles", "sta. rita hills",
    "santa barbara", "santa ynez", "carneros", "stag's leap", "oakville",
    "rutherford", "howell mountain", "atlas peak",
    # New World — Australia
    "margaret river", "coonawarra", "barossa", "barossa valley", "eden valley",
    "clare valley", "mclaren vale", "yarra valley", "hunter valley",
    # New World — NZ / Chile / Argentina
    "marlborough", "central otago", "hawke's bay", "martinborough",
    "mendoza", "uco valley", "luján de cuyo", "colchagua", "casablanca valley",
    "maipo", "aconcagua",
    # Blend / style descriptors
    "red blend", "white blend", "field blend", "gsm", "meritage",
    "super tuscan", "cdt",
]

# Estate/producer structural words — standalone presence strongly indicates a wine entry.
_WINE_ESTATE_WORDS: frozenset[str] = frozenset([
    "château", "chateau", "domaine", "clos", "vigna", "vigneto",
    "bodega", "bodegas", "weingut", "quinta", "tenuta", "masseria",
    "fattoria", "cantina", "azienda", "winery", "vineyard", "cellars",
    "dominio", "mas", "mas de", "cave",
])
# Pre-folded for fast matching at runtime
_FOLDED_ESTATE_WORDS: frozenset[str] = frozenset(
    _fold_for_match(w) for w in _WINE_ESTATE_WORDS
)


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

# Only years plausible for restaurant wine lists; avoids matching founding years,
# table numbers, etc. that fall outside this range.
_VINTAGE_RE = re.compile(r"\b(199\d|200\d|201\d|202[0-9])\b")
# Context that turns a year into an establishment/copyright date, not a vintage.
_VINTAGE_EXCLUSION_RE = re.compile(
    r"(?i)\b(est\.?|since|founded|established|copyright|©|estab\.?)\b"
)

# Reliable food indicators: cooking methods and dish categories that essentially
# never appear in wine names.  Used by _is_wine_line() as a food override signal.
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

# Non-wine beverage keywords.  These are terms that essentially never appear in
# wine names; a line containing one of these (with no offsetting wine signal) is
# dropped in the Phase 0 pre-pass regardless of taste profile.
_NON_WINE_BEVERAGE_KEYWORDS: frozenset[str] = frozenset([
    # Spirits
    "whisky", "whiskey", "bourbon", "scotch", "vodka", "rum", "tequila",
    "mezcal", "cognac", "armagnac", "brandy", "gin", "absinthe",
    # Liqueurs
    "triple sec", "cointreau", "kahlua", "baileys", "amaretto",
    "sambuca", "limoncello",
    # Beer
    "lager", "stout", "pilsner", "pilsener", "pale ale", "wheat beer",
    "craft beer", "draught beer", "draft beer", "ipa",
    # Cocktails
    "cocktail",
    # Non-alcoholic
    "sparkling water", "still water", "mineral water", "soft drink",
    "espresso", "cappuccino", "latte", "americano", "hot chocolate",
    "coffee", "juices",
])


def _is_floating_currency(line: str) -> bool:
    """True if the line contains only a price/currency value with no wine content.

    Matches lines like '$45', '175 / 250', '£ 120', '€ 85/175'.
    Requires at least one digit, a currency symbol or price separator (/ |),
    and nothing remaining after all price characters are stripped.
    A bare year like '2019' is NOT matched (no separator/symbol present).
    """
    stripped = line.strip()
    if not stripped or not re.search(r"\d", stripped):
        return False
    if not re.search(r"[£$€/|]", stripped):
        return False
    remainder = re.sub(r"[\d\s£$€./|,]", "", stripped)
    return len(remainder) == 0


def _is_food_line(line: str) -> bool:
    """True if the line appears to be a food menu item rather than a wine entry."""
    folded = _fold_for_match(line)
    return any(fw in folded for fw in _FOOD_KEYWORDS)


def _is_non_wine_beverage(line: str, folded_wine_keywords: list[str]) -> bool:
    """True if the line describes a non-wine beverage and carries no wine signal.

    A line is only dropped when it contains a non-wine beverage keyword (spirit,
    beer, cocktail, non-alcoholic drink) AND has neither a vintage year nor a
    known wine varietal/region keyword.  The dual check prevents false positives
    on lines like 'Grappa di Barolo' (has wine keyword) or '2019 Brandy-oaked
    Chardonnay' (has vintage).
    """
    stripped = line.strip()
    if not stripped:
        return False
    if _VINTAGE_RE.search(stripped):
        return False
    folded = _fold_for_match(stripped)
    if any(kw in folded for kw in folded_wine_keywords):
        return False
    return any(kw in folded for kw in _NON_WINE_BEVERAGE_KEYWORDS)


def _is_wine_line(line: str, folded_wine_keywords: list[str]) -> bool:
    """Return True if we are ≥95% confident this line is a wine entry.

    Decision logic (in order):
    1. Vintage year in 1990–2029 is the strongest signal.  Skip if the year is
       preceded by an establishment/copyright phrase ("Est.", "Since", etc.).
    2. A known varietal, region, or blend keyword also counts as a wine signal.
    3. An estate/producer structural word (château, domaine, tenuta, …) counts.
    4. Food-keyword override: if the only wine signal is a keyword or estate word
       (no vintage present), and the line also contains a food keyword, drop it —
       e.g. "Pan-roasted duck with Barolo reduction" should not survive.
    """
    stripped = line.strip()
    if not stripped:
        return False

    # Check vintage year (1990–2029), excluding establishment/copyright contexts
    has_vintage = bool(_VINTAGE_RE.search(stripped))
    if has_vintage and _VINTAGE_EXCLUSION_RE.search(stripped):
        has_vintage = False

    folded = _fold_for_match(stripped)
    has_wine_keyword = any(kw in folded for kw in folded_wine_keywords)
    has_estate_word = any(w in folded for w in _FOLDED_ESTATE_WORDS)

    if not (has_vintage or has_wine_keyword or has_estate_word):
        return False

    # Food override only fires when there is no vintage signal
    if not has_vintage and _is_food_line(stripped):
        return False

    return True


def filter_wine_list(wine_list_text: str, _profile: TasteProfile | None) -> str:
    """Pre-filter a raw restaurant wine list, keeping only lines that are
    ≥95% likely to be wine entries.

    Two-phase pipeline:

    Phase 0 (unconditional): drops floating currency lines (price-only rows)
    and non-wine beverage lines (spirits, beer, cocktails, non-alcoholic drinks).

    Phase 1 (dictionary pass): keeps a line only when _is_wine_line() fires —
    i.e. the line contains a vintage year (1990–2029), a known varietal/region
    keyword, or an estate structural word (château, domaine, …).  Food-keyword
    lines without a vintage signal are dropped regardless.  Profile-based
    scoring is intentionally absent here; ranking against preferences is the
    LLM's job.

    Args:
        wine_list_text: Raw text produced by parse_wine_list().
        profile: Accepted for signature compatibility; not used in filtering.

    Returns:
        Filtered wine list text — one entry per line, no blank lines.
    """
    if not wine_list_text:
        logger.debug("wine_list_filter: empty input, returning unchanged")
        return wine_list_text

    try:
        folded_wine_keywords = [_fold_for_match(kw) for kw in _WINE_STYLE_KEYWORDS]

        # ------------------------------------------------------------------
        # Phase 0: drop lines that can never be wine entries.
        # ------------------------------------------------------------------
        beverage_drop = 0
        currency_drop = 0
        phase0: list[str] = []
        for line in wine_list_text.splitlines():
            if _is_floating_currency(line):
                logger.debug("wine_list_filter: drop currency  | %s", line.strip())
                currency_drop += 1
            elif _is_non_wine_beverage(line, folded_wine_keywords):
                logger.debug("wine_list_filter: drop beverage  | %s", line.strip())
                beverage_drop += 1
            else:
                phase0.append(line)

        if beverage_drop or currency_drop:
            logger.debug(
                "wine_list_filter: phase0 dropped %d beverage, %d currency lines",
                beverage_drop, currency_drop,
            )

        # ------------------------------------------------------------------
        # Phase 1: dictionary-based wine line detection.
        # ------------------------------------------------------------------
        kept: list[str] = []
        drop_count = 0
        for line in phase0:
            if _is_wine_line(line, folded_wine_keywords):
                logger.debug("wine_list_filter: keep | %s", line.strip())
                kept.append(line.strip())
            else:
                logger.debug("wine_list_filter: drop | %s", line.strip())
                drop_count += 1

        result = "\n".join(kept)
        logger.debug(
            "wine_list_filter: output %d lines (dropped %d currency, %d beverage, %d non-wine)",
            len(kept), currency_drop, beverage_drop, drop_count,
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
=======
def get_relevant_bottles(bottles: list[dict], style_terms: list[str]) -> list[dict]:
    style_map = {
        "burgundy":   ["pinot noir", "burgundy", "bourgogne", "gevrey", "chambolle"],
        "chablis":    ["chablis", "chardonnay"],
        "champagne":  ["champagne", "blanc de noirs", "crémant"],
        "nebbiolo":   ["nebbiolo", "barolo", "barbaresco"],
        "chenin":     ["chenin", "vouvray", "savennières"],
        "rhone":      ["syrah", "grenache", "côte-rôtie", "hermitage"],
        "loire":      ["cabernet franc", "chinon", "bourgueil"],
        "beaujolais": ["gamay", "beaujolais", "morgon", "moulin"],
    }
    terms = [t.lower() for t in style_terms]
    keywords = []
    for t in terms:
        keywords += style_map.get(t, [t])

    if not keywords:
        return list(bottles)

    folded_keywords = [_fold_for_match(kw) for kw in keywords]

    def matches(b):
        haystack_raw = " ".join(
            str(b.get(k) or "")
            for k in ("Varietal", "Appellation", "Wine", "Producer")
        )
        hay = _fold_for_match(haystack_raw)
        return any(fk in hay for fk in folded_keywords if fk)

    return [b for b in bottles if matches(b)]
>>>>>>> 6caf2d0 (Initial commit: Setting up project structure)
