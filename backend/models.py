from __future__ import annotations

import re
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator
from pydantic.alias_generators import to_camel


class Bottle(BaseModel):
    """Model for a wine bottle from CellarTracker"""
    iWine: Optional[str] = None
    Type: Optional[str] = None
    Color: Optional[str] = None
    Category: Optional[str] = None
    Size: Optional[str] = None
    Currency: Optional[str] = None
    Value: Optional[str] = None
    Price: Optional[str] = None
    TotalQuantity: Optional[str] = None
    Quantity: Optional[str] = None
    Pending: Optional[str] = None
    Vintage: Optional[str] = None
    Wine: Optional[str] = None
    Locale: Optional[str] = None
    Producer: Optional[str] = None
    Varietal: Optional[str] = None
    MasterVarietal: Optional[str] = None
    Designation: Optional[str] = None
    Vineyard: Optional[str] = None
    Country: Optional[str] = None
    Region: Optional[str] = None
    SubRegion: Optional[str] = None
    Appellation: Optional[str] = None
    BeginConsume: Optional[str] = None
    EndConsume: Optional[str] = None
    WindowSource: Optional[str] = None
    LikeVotes: Optional[str] = None
    LikePercent: Optional[str] = None
    LikeIt: Optional[str] = None
    PNotes: Optional[str] = None
    PScore: Optional[str] = None
    CNotes: Optional[str] = None
    CScore: Optional[str] = None

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )


class InventoryResponse(BaseModel):
    bottles: List[Bottle] = Field(default_factory=list)
    age_hours: Optional[float] = None
    stale: bool = False

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        json_encoders={
            float: lambda v: round(v, 1) if v else None
        }
    )


class UploadInventoryResponse(BaseModel):
    count: int
    message: str

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )


class TasteMarkers(BaseModel):
    """Heuristic taste-marker scores derived from preferred descriptors (1=very low … 5=very high)."""
    acidity: int = 3
    tannin: int = 3
    body: int = 3
    oak: int = 3

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )


class CellarStats(BaseModel):
    """Aggregate statistics computed from the user's cellar inventory."""
    total_bottles: int = 0
    unique_wines: int = 0
    vintage_oldest: Optional[int] = None
    vintage_newest: Optional[int] = None

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )


class TasteProfile(BaseModel):
    """Source-agnostic taste profile schema (quiz, CellarTracker, manual, etc.)"""
    preferred_styles: List[str] = Field(default_factory=list)
    preferred_regions: List[str] = Field(default_factory=list)
    preferred_grapes: List[str] = Field(default_factory=list)
    avoided_styles: List[str] = Field(default_factory=list)

    budget_min: Optional[float] = None
    budget_max: Optional[float] = None

    occasion: Optional[str] = None
    food_pairing: Optional[str] = None

    profile_source: str = "manual"
    inference_confidence: Optional[str] = None  # "high" | "medium" | "low"; set when profile_source is "seed_bottles" or "cellartracker_synthesized"

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )


class SeedBottle(BaseModel):
    """A single wine the user names during seed-bottle onboarding."""
    producer: str
    wine: str
    vintage: Optional[int] = None
    sentiment: Literal["loved", "disliked"] = "loved"
    note: Optional[str] = None

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )


class SeedProfileRequest(BaseModel):
    """Request body for POST /seed-profile."""
    loved: List[SeedBottle] = Field(default_factory=list)
    disliked: List[SeedBottle] = Field(default_factory=list)

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )

    @field_validator("loved")
    @classmethod
    def _enforce_min_loved(cls, v: List[SeedBottle]) -> List[SeedBottle]:
        if len(v) < 3:
            raise ValueError("Provide at least 3 loved wines to seed a profile.")
        if len(v) > 7:
            raise ValueError("Provide at most 7 loved wines.")
        return v

    @field_validator("disliked")
    @classmethod
    def _enforce_max_disliked(cls, v: List[SeedBottle]) -> List[SeedBottle]:
        if len(v) > 3:
            raise ValueError("Provide at most 3 disliked wines.")
        return v


class UploadProfileResponse(BaseModel):
    export_type: str
    message: str
    taste_profile: Optional[TasteProfile] = None

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )


class ProfileSummaryResponse(BaseModel):
    top_varietals: List[str] = Field(default_factory=list)
    top_regions: List[str] = Field(default_factory=list)
    top_producers: List[str] = Field(default_factory=list)
    highly_rated: List[Dict[str, str]] = Field(default_factory=list)
    preferred_descriptors: List[str] = Field(default_factory=list)
    avoided_styles: List[str] = Field(default_factory=list)
    avg_spend: Optional[int] = None
    style_summary: Optional[str] = None
    taste_markers: Optional[TasteMarkers] = None
    cellar_stats: Optional[CellarStats] = None
    profile_source: Optional[str] = None  # "cellartracker" | "cellartracker_synthesized" | "seed_bottles" | "manual"
    inference_confidence: Optional[str] = None  # populated when profile_source is "seed_bottles" or "cellartracker_synthesized"
    seed_bottle_count: Optional[int] = None  # number of seed bottles, when profile is seed-derived

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )


class ProfilePatchRequest(BaseModel):
    """Partial edit payload for PATCH /profile.

    Non-`None` fields are merged into ``profile_data.json["_overrides"]`` and
    layered on top of the derived profile by ``build_taste_profile()``.
    """
    top_varietals: Optional[List[str]] = None
    top_regions: Optional[List[str]] = None
    preferred_descriptors: Optional[List[str]] = None
    avoided_styles: Optional[List[str]] = None
    avg_spend: Optional[int] = None
    style_summary: Optional[str] = None
    taste_markers: Optional[TasteMarkers] = None

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )


class RecommendRequest(BaseModel):
    meal: str
    style_terms: Optional[str] = ""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )


class Coords(BaseModel):
    lat: float
    lon: float

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class DrinkWindow(BaseModel):
    from_year: int = Field(alias="from")
    peak: int
    until: int

    # No to_camel here — fields are single words or use explicit alias above
    model_config = ConfigDict(populate_by_name=True)


class WineColor(BaseModel):
    glass: str
    tint: str
    ink: str
    accent: str

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class StructureBars(BaseModel):
    tannin: float
    acidity: float
    body: float
    sweetness: float
    oak: float

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class Critic(BaseModel):
    score: float
    source: str

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class WineRecommendation(BaseModel):
    rank: int
    wine_name: str
    producer: Optional[str] = None
    vintage: Optional[int] = None
    region: Optional[str] = None
    price: Optional[float] = None
    reasoning: str
    confidence: str  # "high" | "medium" | "low"
    fits: Optional[List[str]] = None  # renamed from fit_markers

    # Phase 5 enrichment fields — populated by Claude via tool use
    appellation: Optional[str] = None
    country: Optional[str] = None
    coords: Optional[Coords] = None
    grape: Optional[str] = None
    abv: Optional[float] = None
    drink: Optional[DrinkWindow] = None
    color: Optional[WineColor] = None  # backend-derived; not requested from Claude
    bars: Optional[StructureBars] = None
    wheel: Optional[Dict[str, int]] = None
    nose: Optional[str] = None
    palate: Optional[str] = None
    pairs: Optional[List[str]] = None
    critic: Optional[Critic] = None

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )

    @field_validator("price", mode="before")
    @classmethod
    def coerce_price(cls, v: object) -> object:
        """Strip currency symbols/whitespace so '$45.00' → 45.0."""
        if isinstance(v, str):
            cleaned = re.sub(r"[^\d.]", "", v)
            return float(cleaned) if cleaned else None
        return v


class RecommendationResponse(BaseModel):
    recommendations: List[WineRecommendation]
    list_quality_note: Optional[str] = None
    profile_match_summary: str

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )


class FlightSummary(BaseModel):
    """Lightweight row for GET /history list view."""
    id: str
    created_at: float
    occasion: str
    menu: str
    top_wine_name: str
    bottle_count: int

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class FlightRecord(BaseModel):
    """Full flight record returned by GET /history/{id}."""
    id: str
    created_at: float
    occasion: str
    menu: str
    source_mode: str
    bottle_count: int
    response: RecommendationResponse

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class MealProfile(BaseModel):
    protein: Optional[str] = None
    cooking_method: Optional[str] = None
    sauce_flavor: Optional[str] = None
    heat_level: str = "mild"
    richness: str = "medium"
    dominant_flavors: List[str] = Field(default_factory=list)

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
