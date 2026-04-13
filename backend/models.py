from __future__ import annotations

import re
from typing import Optional, List, Dict, Any
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
    
    # For TypeScript camelCase compatibility - allow both snake_case and camelCase
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True  # Allow both original field names and aliases
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


class UploadProfileResponse(BaseModel):
    export_type: str
    message: str
    taste_profile: Optional[TasteProfile] = None

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )


<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> b169158 (Added my profile tab)
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


<<<<<<< HEAD
=======
>>>>>>> 6caf2d0 (Initial commit: Setting up project structure)
=======
>>>>>>> b169158 (Added my profile tab)
class ProfileSummaryResponse(BaseModel):
    top_varietals: List[str] = Field(default_factory=list)
    top_regions: List[str] = Field(default_factory=list)
    top_producers: List[str] = Field(default_factory=list)
    highly_rated: List[Dict[str, str]] = Field(default_factory=list)
    preferred_descriptors: List[str] = Field(default_factory=list)
    avoided_styles: List[str] = Field(default_factory=list)
    avg_spend: Optional[int] = None
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> b169158 (Added my profile tab)
    style_summary: Optional[str] = None
    taste_markers: Optional[TasteMarkers] = None
    cellar_stats: Optional[CellarStats] = None

<<<<<<< HEAD
=======
    
>>>>>>> 6caf2d0 (Initial commit: Setting up project structure)
=======
>>>>>>> b169158 (Added my profile tab)
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


class WineRecommendation(BaseModel):
    rank: int
    wine_name: str
    producer: Optional[str] = None
    vintage: Optional[int] = None
    region: Optional[str] = None
    price: Optional[float] = None
    reasoning: str
    confidence: str  # "high" | "medium" | "low"

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


class TasteProfile(BaseModel):
    """Source-agnostic taste profile schema (quiz, CellarTracker, manual, etc.)"""
    # Core preferences
    preferred_styles: List[str] = Field(default_factory=list)
    preferred_regions: List[str] = Field(default_factory=list)
    preferred_grapes: List[str] = Field(default_factory=list)
    avoided_styles: List[str] = Field(default_factory=list)

    # Budget
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None

    # Optional context
    occasion: Optional[str] = None
    food_pairing: Optional[str] = None

    # Onboarding source (informational only)
    profile_source: str = "manual"

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )
