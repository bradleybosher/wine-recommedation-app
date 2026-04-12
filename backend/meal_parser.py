from dataclasses import dataclass, field
from typing import Optional, List


PROTEINS: dict[str, dict] = {
    "duck":      {"richness": "rich",   "base_flavor": "gamey"},
    "beef":      {"richness": "rich",   "base_flavor": "savory"},
    "fish":      {"richness": "light",  "base_flavor": "delicate"},
    "salmon":    {"richness": "medium", "base_flavor": "oily"},
    "chicken":   {"richness": "medium", "base_flavor": "neutral"},
    "lamb":      {"richness": "rich",   "base_flavor": "gamey"},
    "pork":      {"richness": "medium", "base_flavor": "savory"},
    "veal":      {"richness": "light",  "base_flavor": "delicate"},
    "seafood":   {"richness": "light",  "base_flavor": "briny"},
    "shellfish": {"richness": "light",  "base_flavor": "briny"},
    "shrimp":    {"richness": "light",  "base_flavor": "briny"},
    "lobster":   {"richness": "medium", "base_flavor": "briny"},
    "crab":      {"richness": "light",  "base_flavor": "briny"},
}

COOKING_METHODS: dict[str, str] = {
    "seared":    "high-heat, caramelized",
    "roasted":   "deep, savory",
    "braised":   "tender, slow-cooked",
    "grilled":   "charred, smoky",
    "poached":   "delicate, moist",
    "pan-fried": "crispy exterior",
    "steamed":   "gentle, light",
    "raw":       "fresh, bright",
    "baked":     "gentle, tender",
}

SAUCE_FLAVORS: dict[str, dict] = {
    "cherry":              {"flavor": "dark fruit, sweet-sour",  "tannin_match": "moderate"},
    "gastrique":           {"flavor": "sweet-sour",               "tannin_match": "light"},
    "mushroom":            {"flavor": "earthy",                   "tannin_match": "moderate"},
    "cream":               {"flavor": "rich, buttery",            "tannin_match": "light"},
    "red wine reduction":  {"flavor": "savory, deep",             "tannin_match": "high"},
    "beurre blanc":        {"flavor": "acidic, buttery",          "tannin_match": "light"},
    "peppercorn":          {"flavor": "spicy, savory",            "tannin_match": "high"},
    "lemon":               {"flavor": "bright, acidic",           "tannin_match": "light"},
    "olive tapenade":      {"flavor": "briny, savory",            "tannin_match": "moderate"},
    "truffle":             {"flavor": "earthy, luxe",             "tannin_match": "moderate"},
    "soy":                 {"flavor": "umami, salty",             "tannin_match": "moderate"},
    "spice":               {"flavor": "hot, peppery",             "tannin_match": "moderate"},
    "tomato":              {"flavor": "bright, acidic",           "tannin_match": "light"},
    "butter":              {"flavor": "rich, creamy",             "tannin_match": "light"},
}

HEAT_KEYWORDS: dict[str, str] = {
    "spicy":      "spicy",
    "chili":      "spicy",
    "cayenne":    "spicy",
    "curry":      "spicy",
    "pepper":     "moderate",
    "peppercorn": "moderate",
    "garlic":     "mild",
    "herbs":      "mild",
}


@dataclass
class MealProfile:
    protein: Optional[str] = None
    cooking_method: Optional[str] = None
    sauce_flavor: Optional[str] = None
    heat_level: str = "mild"
    richness: str = "medium"
    dominant_flavors: List[str] = field(default_factory=list)


def parse_meal_description(meal: str) -> MealProfile:
    """Parse a raw meal description into a structured MealProfile."""
    text = meal.lower()
    profile = MealProfile()

    for name, attrs in PROTEINS.items():
        if name in text:
            profile.protein = name
            profile.richness = attrs["richness"]
            break

    for method in COOKING_METHODS:
        if method in text:
            profile.cooking_method = method
            break

    for sauce, attrs in SAUCE_FLAVORS.items():
        if sauce in text:
            profile.sauce_flavor = sauce
            profile.dominant_flavors = [f.strip() for f in attrs["flavor"].split(",")]
            break

    for keyword, level in HEAT_KEYWORDS.items():
        if keyword in text:
            profile.heat_level = level
            break

    return profile


def meal_to_wine_hints(profile: MealProfile) -> str:
    """Format a MealProfile into natural-language pairing hints for the system prompt."""
    lines: List[str] = []

    if profile.protein:
        base_flavor = PROTEINS[profile.protein]["base_flavor"]
        lines.append(f"Protein: {profile.protein} ({base_flavor})")

    if profile.cooking_method:
        lines.append(f"Cooked {profile.cooking_method}")

    if profile.sauce_flavor:
        flavor_text = ", ".join(profile.dominant_flavors)
        lines.append(f"Sauce: {profile.sauce_flavor} -> seek wines with {flavor_text}")

    if profile.richness == "rich":
        lines.append("Rich dish: pair with wines having body and structure")
    elif profile.richness == "light":
        lines.append("Light dish: prefer wines with freshness and acidity")

    if profile.heat_level in ("moderate", "spicy"):
        lines.append("Heat present: prefer off-dry or fruity wines")

    return "\n".join(lines)


def infer_wine_style_from_meal(profile: MealProfile) -> List[str]:
    """Suggest wine styles based on meal characteristics."""
    styles: List[str] = []

    if profile.protein in ("beef", "lamb") and profile.richness == "rich":
        styles.extend(["burgundy", "bordeaux", "barolo"])
    elif profile.protein in ("fish", "seafood", "shellfish", "shrimp", "crab") and profile.richness == "light":
        styles.extend(["chablis", "sauvignon blanc", "muscadet"])
    elif profile.protein in ("salmon", "lobster"):
        styles.extend(["white burgundy", "viognier"])

    if profile.sauce_flavor in ("cherry",):
        styles.append("pinot noir")
    if profile.sauce_flavor in ("mushroom", "truffle"):
        styles.append("burgundy")

    # Deduplicate while preserving order
    seen: set[str] = set()
    result: List[str] = []
    for s in styles:
        if s not in seen:
            seen.add(s)
            result.append(s)
    return result
