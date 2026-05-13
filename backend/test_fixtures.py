"""Canned RecommendationResponse fixtures used when TEST_MODE is enabled.

Built from Pydantic models so any schema drift fails at backend import,
not at request time. Add new variants here as the UX grows.
"""
from models import RecommendationResponse, WineRecommendation

_HAPPY = RecommendationResponse(
    recommendations=[
        WineRecommendation(
            rank=1,
            wine_name="Brunello di Montalcino",
            producer="Biondi-Santi",
            vintage=2016,
            region="Tuscany, Italy",
            price=185.0,
            reasoning="Closely mirrors the structured Sangiovese profile your cellar leans on, with the savoury earth and dried-cherry character you consistently rate highly. The 2016 vintage is drinking in its primary fruit window, matching the meal's richness without overshadowing it.",
            confidence="high — strong style overlap with cellar favourites",
            fit_markers=["structured tannin", "savoury earth", "dried cherry"],
        ),
        WineRecommendation(
            rank=2,
            wine_name="Barolo Cannubi",
            producer="Marchesi di Barolo",
            vintage=2018,
            region="Piedmont, Italy",
            price=145.0,
            reasoning="Nebbiolo's rose-and-tar aromatics line up with the floral red wines you've previously enjoyed. Slightly younger and more grippy than the Brunello, so it benefits from a decant before service.",
            confidence="high — varietal and producer both align with profile",
            fit_markers=["floral nebbiolo", "firm tannin", "age-worthy"],
        ),
        WineRecommendation(
            rank=3,
            wine_name="Chianti Classico Riserva",
            producer="Felsina",
            vintage=2019,
            region="Tuscany, Italy",
            price=72.0,
            reasoning="The value pick — Felsina's Riserva delivers a lot of the Brunello's character at less than half the price. A safe pour if the table wants something approachable without trading away the savoury Tuscan profile.",
            confidence="medium — good fit, lower stylistic complexity",
            fit_markers=["value", "approachable", "tuscan classic"],
        ),
    ],
    list_quality_note=None,
    profile_match_summary="The list leans heavily Italian, which plays directly to your cellar's Sangiovese and Nebbiolo bias. Three strong matches were easy to find.",
)

_SPARSE = RecommendationResponse(
    recommendations=[
        WineRecommendation(
            rank=1,
            wine_name="House Red",
            producer=None,
            vintage=None,
            region=None,
            price=None,
            reasoning="Listed simply as 'house red' with no producer or vintage on the menu. Style cues suggest medium-bodied Mediterranean blend, which aligns roughly with your preferences.",
            confidence="medium — limited list metadata",
            fit_markers=None,
        ),
        WineRecommendation(
            rank=2,
            wine_name="Rioja Reserva",
            producer="Unspecified",
            vintage=None,
            region="Rioja",
            price=None,
            reasoning="No vintage or producer listed, but Rioja Reserva designation guarantees minimum aging that should deliver the savoury, leather-edged style your profile gravitates to.",
            confidence="medium — designation-only inference",
            fit_markers=["savoury", "aged"],
        ),
        WineRecommendation(
            rank=3,
            wine_name="Pinot Noir",
            producer=None,
            vintage=2021,
            region=None,
            price=58.0,
            reasoning="Only varietal and vintage given. Defensible pick at this price point if the table wants lighter-bodied red.",
            confidence="low — varietal-only match",
            fit_markers=[],
        ),
    ],
    list_quality_note="List has minimal producer and vintage information — confidence is capped accordingly.",
    profile_match_summary="Sparse list metadata limited how precisely the cellar profile could be matched.",
)

_LONG_REASONING = RecommendationResponse(
    recommendations=[
        WineRecommendation(
            rank=1,
            wine_name="Châteauneuf-du-Pape",
            producer="Domaine du Vieux Télégraphe",
            vintage=2017,
            region="Rhône, France",
            price=165.0,
            reasoning=(
                "This is one of the most consistent matches available on the list relative to your cellar. "
                "Vieux Télégraphe's house style — Grenache-led but with meaningful Mourvèdre and Syrah backbone — "
                "produces the kind of warm-fruited but savoury, garrigue-tinged red you've rated 90+ on across "
                "five separate occasions in your tasting history. The 2017 vintage is a touch riper than the classic "
                "norm, which actually plays well with the meal's richness without becoming jammy."
            ),
            confidence="high — five separate profile matches in tasting history",
            fit_markers=["grenache-led southern rhône", "garrigue", "savoury warmth"],
        ),
        WineRecommendation(
            rank=2,
            wine_name="Côte-Rôtie",
            producer="E. Guigal",
            vintage=2018,
            region="Northern Rhône, France",
            price=210.0,
            reasoning=(
                "Northern Rhône Syrah brings the bacon-fat and black-pepper aromatics that your CellarTracker notes "
                "single out repeatedly. Guigal's brand-tier Côte-Rôtie isn't the most exciting expression of the appellation "
                "but it is structurally faithful, and 2018 was a strong vintage. The step up in price relative to the "
                "Châteauneuf is real, so this becomes the right pick only if the table is happy with the spend."
            ),
            confidence="high — northern Rhône Syrah is a known sweet spot",
            fit_markers=["bacon fat", "black pepper", "structured syrah"],
        ),
        WineRecommendation(
            rank=3,
            wine_name="Bandol Rouge",
            producer="Domaine Tempier",
            vintage=2019,
            region="Provence, France",
            price=125.0,
            reasoning=(
                "Tempier is a less obvious but high-upside match — Mourvèdre-dominant Bandol has the wild herb and "
                "iron-edged savoury character that overlaps with your Italian and Southern Rhône preferences. "
                "If you want to try something at the edge of your usual palette without leaving the safety zone, "
                "this is the one. The 2019 is still tight; ask the somm if they'll decant it for 30+ minutes."
            ),
            confidence="medium — adjacent style, less direct history",
            fit_markers=["mourvèdre-led", "wild herb", "savoury iron"],
        ),
    ],
    list_quality_note=None,
    profile_match_summary=(
        "The list is unusually deep in French Rhône and Provençal reds, which maps almost directly onto the savoury, "
        "structured, herb-inflected reds that dominate your cellar. Three strong picks were identified without needing "
        "to reach into adjacent styles, and a fourth (Cornas) is worth asking about if these are unavailable. Overall, "
        "this is one of the better profile-fit scenarios across recent uploads."
    ),
)

_LOW_CONFIDENCE = RecommendationResponse(
    recommendations=[
        WineRecommendation(
            rank=1,
            wine_name="Cabernet Sauvignon",
            producer="Generic Napa",
            vintage=2020,
            region="Napa Valley",
            price=95.0,
            reasoning="Best-effort match on a list that's almost entirely outside your usual style. New World Cab is not a cellar strength but it's the most structurally credible option here.",
            confidence="low — list does not overlap with profile",
            fit_markers=["fallback", "structured", "new world"],
        ),
        WineRecommendation(
            rank=2,
            wine_name="Chardonnay",
            producer="Sonoma Coast",
            vintage=2021,
            region="Sonoma",
            price=68.0,
            reasoning="If a white is preferred, this is the closest the list comes to the lees-y, mineral whites you've previously enjoyed.",
            confidence="low — style adjacency only",
            fit_markers=["lees-y", "mineral-adjacent"],
        ),
        WineRecommendation(
            rank=3,
            wine_name="Merlot",
            producer="Unspecified",
            vintage=2019,
            region="California",
            price=52.0,
            reasoning="Included only to fill the third slot — generic California Merlot does not meaningfully match your profile.",
            confidence="low — third-slot filler",
            fit_markers=[],
        ),
    ],
    list_quality_note="This list skews heavily toward New World styles that don't overlap with the cellar. Consider asking the restaurant if a reserve or off-menu list is available.",
    profile_match_summary="Poor overall fit between the list and your profile — all three picks are low-confidence by design.",
)

_TWO_WINES = RecommendationResponse(
    recommendations=[
        WineRecommendation(
            rank=1,
            wine_name="Riesling Spätlese",
            producer="J.J. Prüm",
            vintage=2019,
            region="Mosel, Germany",
            price=88.0,
            reasoning="Direct hit on the off-dry German Riesling style that dominates your white-wine tasting history. Prüm's Spätlese is age-worthy and a clear top pick.",
            confidence="high — strongest match on the list",
            fit_markers=["off-dry", "mosel slate", "age-worthy"],
        ),
        WineRecommendation(
            rank=2,
            wine_name="Grüner Veltliner Smaragd",
            producer="Hirtzberger",
            vintage=2020,
            region="Wachau, Austria",
            price=92.0,
            reasoning="A second viable option if a drier white is preferred. Smaragd-level Grüner has the texture and white-pepper bite that overlap meaningfully with your profile.",
            confidence="medium — adjacent style to your sweet spot",
            fit_markers=["dry", "white pepper", "textured"],
        ),
    ],
    list_quality_note="Only two wines on the list cleanly matched the profile — included a second pick instead of stretching to a weak third.",
    profile_match_summary="Narrow but strong overlap on Germanic whites; the rest of the list is outside the cellar's character.",
)

FIXTURES: dict[str, RecommendationResponse] = {
    "happy": _HAPPY,
    "sparse": _SPARSE,
    "long_reasoning": _LONG_REASONING,
    "low_confidence": _LOW_CONFIDENCE,
    "two_wines": _TWO_WINES,
}
