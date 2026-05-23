"""Synonym/alias expansion for grape varieties and wine regions.

Maps canonical tokens to lists of equivalent or subordinate terms so that
retrieval scoring can match wine-list entries that use local names, sub-
appellations, or alternate grape spellings.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Canonical → expansions mapping
# ---------------------------------------------------------------------------

_EXPANSIONS: dict[str, list[str]] = {
    # ── Grapes ──────────────────────────────────────────────────────────────
    "pinot noir": ["spätburgunder", "blauburgunder", "pinot nero"],
    "chardonnay": ["white burgundy", "chablis", "meursault", "puligny", "chassagne"],
    "cabernet sauvignon": ["cabernet", "cab sauv"],
    "sauvignon blanc": ["sancerre", "pouilly fumé", "pouilly-fumé", "fumé blanc"],
    "riesling": ["rhine riesling", "johannisberg riesling"],
    "grenache": ["garnacha", "cannonau", "grenache noir"],
    "syrah": ["shiraz", "sérine"],
    "mourvèdre": ["monastrell", "mataro"],
    "gamay": ["gamay noir", "beaujolais"],
    "chenin blanc": ["vouvray", "savennières", "montlouis"],
    "nebbiolo": ["barolo", "barbaresco", "langhe nebbiolo", "ghemme", "gattinara"],
    "sangiovese": ["chianti", "brunello", "morellino", "rosso di montalcino"],
    "tempranillo": ["tinto fino", "tinta roriz", "cencibel", "ull de llebre"],
    "trousseau": ["bastardo"],
    "aligoté": ["bourgogne aligoté"],
    "melon de bourgogne": ["muscadet"],
    "gewürztraminer": ["gewurztraminer"],
    "grüner veltliner": ["gruner veltliner", "grüner"],
    "verdejo": [],
    "vermentino": ["rolle"],
    "fiano": [],
    "greco": ["greco di tufo"],
    "catarratto": [],
    "albariño": ["albarino", "albariño"],
    "txakoli": ["txakolina"],
    "furmint": [],
    "blaufränkisch": ["blaufrankisch", "lemberger", "kékfrankos"],

    # ── Regions / Appellations ───────────────────────────────────────────────

    # Burgundy umbrella → sub-appellations
    "burgundy": [
        "bourgogne", "côte de nuits", "cote de nuits", "côte de beaune", "cote de beaune",
        "gevrey", "chambolle", "vosne", "nuits-saint-georges", "nuits saint georges",
        "pommard", "volnay", "meursault", "puligny-montrachet", "puligny montrachet",
        "chassagne-montrachet", "chassagne montrachet", "marsannay", "fixin",
        "morey-saint-denis", "morey saint denis", "vougeot", "flagey",
        "auxey-duresses", "saint-romain", "saint-aubin", "santenay", "maranges",
        "côte chalonnaise", "cote chalonnaise", "rully", "mercurey", "givry", "montagny",
        "mâconnais", "maconnais", "mâcon", "macon", "viré-clessé", "pouilly-fuissé",
        "pouilly fuisse",
    ],

    # Champagne umbrella
    "champagne": [
        "grower champagne", "grower-producer", "champagne producer",
        "aÿ", "ay", "épernay", "epernay", "reims", "côte des bar", "cote des bar",
        "vallée de la marne", "vallee de la marne", "montagne de reims",
        "blanc de blancs", "blanc de noirs", "brut nature", "brut zéro", "extra brut",
    ],

    # Loire
    "loire": [
        "loire valley", "sancerre", "pouilly-fumé", "pouilly fumé", "touraine",
        "vouvray", "montlouis", "chinon", "bourgueil", "saint-nicolas-de-bourgueil",
        "anjou", "saumur", "muscadet", "muscadet sèvre et maine",
        "savennières", "coteaux du layon", "bonnezeaux", "quarts de chaume",
        "menetou-salon", "quincy", "reuilly",
    ],

    # Rhône
    "rhône": [
        "rhone", "northern rhône", "northern rhone", "southern rhône", "southern rhone",
        "côte-rôtie", "cote rotie", "condrieu", "saint-joseph", "crozes-hermitage",
        "hermitage", "cornas", "châteauneuf-du-pape", "chateauneuf du pape",
        "gigondas", "vacqueyras", "rasteau", "lirac", "tavel",
        "côtes du rhône", "cotes du rhone",
    ],

    # Alsace
    "alsace": [
        "alsatian", "grand cru alsace", "vendanges tardives",
    ],

    # Jura
    "jura": [
        "arbois", "château-chalon", "chateau chalon", "l'étoile", "etoile",
        "côtes du jura", "vin jaune", "vin de paille", "savagnin", "ouillé", "ouille",
    ],

    # Beaujolais
    "beaujolais": [
        "moulin-à-vent", "moulin a vent", "morgon", "fleurie", "chiroubles",
        "côte de brouilly", "brouilly", "régnié", "juliénas", "chénas", "saint-amour",
        "beaujolais-villages",
    ],

    # Bordeaux
    "bordeaux": [
        "médoc", "medoc", "saint-émilion", "saint emilion", "pomerol", "pauillac",
        "saint-estèphe", "saint estephe", "margaux", "saint-julien", "saint julien",
        "listrac", "moulis", "haut-médoc", "haut medoc", "graves", "pessac-léognan",
        "pessac leognan", "sauternes", "barsac", "entre-deux-mers",
    ],

    # Roussillon / Languedoc
    "languedoc": [
        "roussillon", "languedoc-roussillon", "minervois", "corbières", "corbieres",
        "fitou", "faugères", "faugeres", "pic saint loup", "la clape", "terrasses du larzac",
        "saint-chinian",
    ],

    # Provence
    "provence": [
        "bandol", "cassis", "palette", "côtes de provence", "cotes de provence",
        "les baux de provence",
    ],

    # Southwest France
    "southwest france": [
        "cahors", "bergerac", "madiran", "jurançon", "jurancon", "gaillac",
        "côtes du marmandais", "fronton",
    ],

    # Italy
    "piedmont": [
        "piemonte", "barolo", "barbaresco", "barbera d'asti", "barbera d'alba",
        "dolcetto", "langhe", "monferrato", "roero", "gavi", "moscato d'asti",
    ],
    "tuscany": [
        "toscana", "chianti classico", "brunello di montalcino", "vino nobile",
        "morellino di scansano", "bolgheri", "maremma",
    ],
    "veneto": [
        "soave", "valpolicella", "amarone", "ripasso", "bardolino", "prosecco",
    ],
    "sicily": [
        "sicilia", "etna", "nero d'avola", "nerello mascalese",
    ],

    # Spain
    "rioja": [
        "rioja alta", "rioja alavesa", "rioja oriental",
    ],
    "ribera del duero": [],
    "priorat": ["priorat", "priorato"],
    "galicia": [
        "rías baixas", "rias baixas", "ribeiro", "valdeorras",
    ],

    # Germany / Austria
    "mosel": [
        "moselle", "bernkastel", "piesport", "wehlen", "graach", "traben-trarbach",
    ],
    "rheingau": [],
    "rheinhessen": [],
    "pfalz": [],
    "wachau": ["smaragd", "federspiel", "steinfeder"],
    "kamptal": [],
    "kremstal": [],
    "burgenland": ["neusiedlersee"],

    # Portugal
    "douro": ["duriense", "port", "porto", "touriga nacional", "tinta roriz"],
    "alentejo": [],
    "vinho verde": [],
    "dão": ["dao"],
    "bairrada": [],

    # New World
    "willamette valley": ["willamette", "dundee hills", "chehalem mountains"],
    "margaret river": [],
    "yarra valley": [],
    "swartland": ["swartland winemakers"],
    "stellenbosch": [],
    "walker bay": ["hemel-en-aarde", "hemel en aarde"],
    "chablis": ["petit chablis", "chablis premier cru", "chablis grand cru"],
}

# Reverse index: alias → canonical (for lookup)
_ALIAS_TO_CANONICAL: dict[str, str] = {}
for _canon, _aliases in _EXPANSIONS.items():
    for _alias in _aliases:
        _ALIAS_TO_CANONICAL[_alias.lower()] = _canon


def expand_term(term: str) -> list[str]:
    """Return `term` plus all known synonyms/sub-appellations.

    The original term is always included as the first element.
    Lookup is case-insensitive; all returned values are lowercased.
    """
    key = term.strip().lower()
    expansions = _EXPANSIONS.get(key)
    if expansions is not None:
        return [key] + [e.lower() for e in expansions]
    # Maybe the term itself is an alias — look up the canonical and expand that
    canonical = _ALIAS_TO_CANONICAL.get(key)
    if canonical:
        return expand_term(canonical)
    return [key]


def expand_terms(terms: list[str]) -> list[str]:
    """Expand a list of terms, returning a deduplicated flat list (preserving first-seen order)."""
    seen: set[str] = set()
    result: list[str] = []
    for term in terms:
        for expanded in expand_term(term):
            if expanded not in seen:
                seen.add(expanded)
                result.append(expanded)
    return result
