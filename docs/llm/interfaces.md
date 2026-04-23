# Public Function Signatures

## Backend

### main.py

```python
@app.middleware("http")
async def log_requests(request: Request, call_next) → response with X-Request-ID header
  Logs all incoming requests with ID, method, path, client IP, elapsed time.

@app.post("/upload-inventory")
async def upload_inventory(file: UploadFile) → UploadInventoryResponse
  Save CellarTracker TSV export. Returns count and cache-bust confirmation.

@app.post("/upload-profile")
async def upload_profile(file: UploadFile) → UploadProfileResponse
  Save taste profile export (any CellarTracker export type). Returns type detected + derived TasteProfile.

@app.get("/inventory")
def get_inventory() → InventoryResponse
  Load saved inventory with age_hours and stale flag.

@app.get("/profile-summary")
def profile_summary() → ProfileSummaryResponse
  Build taste profile from saved profile data. Returns top varietals, regions, etc.
  Also returns: style_summary (Ollama palate portrait, nullable), taste_markers (heuristic 1–5 scores),
  cellar_stats (total_bottles, unique_wines, vintage range from inventory).

@app.post("/recommend")
async def recommend(wine_list: UploadFile, meal: str, style_terms: str) → RecommendationResponse
  Main endpoint. Parse wine list, build prompt with profile/inventory context, call LLM.
  Cache by SHA256(wine_list_bytes, meal, inventory_hash, profile_hash).
```

### models.py

```python
class Bottle(BaseModel):
  All CellarTracker fields (iWine, Type, Color, ..., EndConsume). Optional fields.
  ConfigDict: alias_generator=to_camel, populate_by_name=True.

class TasteProfile(BaseModel):
  preferred_styles, preferred_regions, preferred_grapes, avoided_styles: List[str]
  budget_min, budget_max: Optional[float]
  occasion, food_pairing: Optional[str]
  profile_source: str = "manual"

class WineRecommendation(BaseModel):
  rank: int
  wine_name: str
  producer, region: Optional[str]
  vintage: Optional[int]
  price: Optional[float]  # coerce_price validator strips currency symbols
  reasoning: str (2–4 sentences, structured: personal comparison → contrast → food → cellar note)
  confidence: str (format: "high|medium|low — single clause reason")

class RecommendationResponse(BaseModel):
  recommendations: List[WineRecommendation]
  list_quality_note: Optional[str]
  profile_match_summary: str (1 sentence)

class InventoryResponse(BaseModel):
  bottles: List[Bottle] = []
  age_hours: Optional[float]
  stale: bool

class UploadInventoryResponse(BaseModel):
  count: int
  message: str

class UploadProfileResponse(BaseModel):
  export_type: str
  message: str
  taste_profile: Optional[TasteProfile] = None  # Derived immediately on upload

class TasteMarkers(BaseModel):
  acidity, tannin, body, oak: int  # 1–5 scale

class CellarStats(BaseModel):
  total_bottles, unique_wines: int
  vintage_oldest, vintage_newest: Optional[int]

class ProfileSummaryResponse(BaseModel):
  top_varietals, top_regions, top_producers: List[str]
  highly_rated: List[Dict[str, str]]
  preferred_descriptors, avoided_styles: List[str]
  avg_spend: Optional[int]
  style_summary: Optional[str]      # Ollama palate portrait sentence
  taste_markers: Optional[TasteMarkers]
  cellar_stats: Optional[CellarStats]
```

### recommender.py

```python
def get_recommendation(
  wine_list_text: str,
  meal: str,
  system_prompt: str,
  anthropic_api_key: str,
  anthropic_model: str,
  image_b64: Optional[str] = None
) → RecommendationResponse
  Call Anthropic Claude via tool use (provide_recommendations tool). tool_block.input is a
  pre-parsed dict — no JSON parsing needed. Retry up to 3× on Pydantic ValidationError.
  Raise HTTPException(502) on API error or unrecoverable schema mismatch.
```

### prompt.py

```python
def format_bottle(b: dict) -> str
  Format bottle as "{Vintage} {Producer} {Wine} (drink {Begin}–{End})".

def build_system_prompt(
  relevant_bottles: list[dict],
  cellar_summary: str = "",
  taste_profile_override: str | None = None,
  meal_hints: str = ""
) → str
  Construct system prompt: sommelier persona, taste profile, relevant bottles, schema, meal hints.
  If taste_profile_override provided, skips internal build_enhanced_profile_text() call.
  Writes full prompt to prompt.log via dedicated _prompt_logger.
  Returns full prompt string with JSON schema embedded.
```

### profile.py

```python
def ingest_export(raw: bytes) → Tuple[str, List[Dict[str, str]]]
  Decode bytes, parse TSV, detect export type. Return (type, rows).

def save_profile_export(raw: bytes) → str
  Ingest, merge into profile_data.json. Return export type.

def load_profile_data() → Dict
  Load profile_data.json or {}. Fail gracefully on missing/corrupt file.

def build_taste_profile(profile_data: dict) → Dict
  Derive taste profile: top varietals, regions, producers, preferred descriptors.
  Infer avoided_styles from low-scored (≤3.0) tasting notes.
  Return dict with keys: top_varietals, top_regions, top_producers, highly_rated,
  preferred_descriptors, avoided_styles, avg_spend.

def build_enhanced_profile_text() → str
  Format taste profile as prose paragraph for system prompt.
  Fallback to OWNER_PROFILE constant if no profile data.

def build_enriched_profile_text(anthropic_api_key: str, anthropic_model: str) → str
  Like build_enhanced_profile_text() but calls enrich_profile_with_anthropic() first.
  Prepends style_summary sentence if enrichment succeeded.
  This is the function called from main.py (not build_enhanced_profile_text).

def enrich_profile_with_anthropic(raw: dict, anthropic_api_key: str, anthropic_model: str) → dict
  Call Anthropic Claude via tool use (enrich_taste_profile tool); get back multi-word style
  phrases + style_summary. tool_block.input is pre-parsed — no JSON parsing needed.
  Returns raw unchanged on any error (fully safe fallback).
  enrich_profile_with_ollama is kept as a backward-compat alias.

def build_taste_profile_pydantic(profile_data: dict) → TasteProfile
  Calls build_taste_profile() and maps result to TasteProfile Pydantic model.
  Derives budget_min/max from avg_spend (±10). Sets profile_source="cellartracker".

def _infer_avoided_styles(profile_data: dict) → List[str]
  Scan tasting notes (type "notes", "consumed") for wines with low scores.
  Auto-detect score scale (max > 10 → 100-pt scale, threshold 60; else 5-pt scale, threshold 3.0).
  Only count tokens in hardcoded negative_indicator_words set. Return top 10 with freq ≥ 2.

def derive_taste_markers(descriptors: List[str]) → dict
  Heuristic keyword scan of preferred descriptors. Returns {acidity, tannin, body, oak} as int 1–5.
  No LLM call — deterministic. Default score 3; ±1 per matching high/low keyword; clamped [1,5].
```

### inventory.py

```python
def decode_cellartracker_upload(raw: bytes) → str
  Try UTF-8-sig, UTF-8, cp1252, latin-1. Return decoded string or lossy fallback.

def parse_ct_csv(csv_text: str) → List[Dict]
  Parse TSV, filter rows where Quantity > 0. Return list of dicts.

def save_inventory(csv_text: str) → List[Dict]
  Parse, write to inventory.json with timestamp. Return bottles list.

def load_inventory() → Optional[Dict]
  Load inventory.json. Return dict with bottles, age_hours, stale. None if missing.

def extract_terms_from_wine_list_text(text: str) → List[str]
  Scan raw restaurant wine list text for known style/varietal/region keywords.
  Returns matched keywords deduplicated and sorted longest-first (multi-word before component words).
  Output used as restaurant_terms for get_relevant_bottles().

def filter_wine_list(wine_list_text: str, _profile: TasteProfile | None) → str
  Two-phase pre-filter. Phase 0: drop floating currency lines and non-wine beverage lines
  (spirits/beer/cocktails/non-alcoholic — only when no wine signal present).
  Phase 1: keep lines with a vintage year (1990–2029), a known wine keyword, or an estate
  structural word (château, domaine, …); food-keyword lines without a vintage are dropped.
  Falls back to original text on unexpected error. Profile param accepted but unused.

def get_relevant_bottles(
  bottles: list[dict],
  restaurant_terms: list[str],
  profile_prefs: dict,
  override_terms: list[str] | None = None,
  limit: int = 30,
) → List[Dict]
  Score and rank cellar bottles. Scoring: +1.5 per profile preferred term match,
  +1.0 per restaurant term match, +0.5 drinking window open, -0.3 too young,
  float("-inf") for avoided style match (hard exclusion).
  override_terms: when provided, expanded via _STYLE_MAP and used instead of restaurant_terms.
  Returns top limit non-excluded bottles sorted by score descending.
```

### cache.py

```python
def init_db() → None
  Create response_cache and parse_cache tables if not exist.

def make_parse_key(pdf_bytes: bytes) → str
  SHA256(pdf_bytes) only — independent of meal, inventory, profile. Key for parse cache.

def get_parse_cached(pdf_hash: str) → Optional[str]
  SELECT wine_list_text FROM parse_cache WHERE pdf_hash. Return text or None if missing/expired.

def set_parse_cached(pdf_hash: str, wine_list_text: str) → None
  INSERT OR REPLACE into parse_cache.

def make_key(image_bytes: bytes, meal: str, inventory_hash: str, profile_hash: str) → str
  SHA256(image + meal + inventory_hash + profile_hash). Key for response cache.

def inventory_hash(bottles: list[dict]) → str
  MD5(JSON-sorted bottles).

def get_cached(key: str) → Optional[str]
  SELECT response FROM response_cache WHERE key. Return JSON string or None.

def set_cached(key: str, response: str) → None
  INSERT OR REPLACE into response_cache.

def bust_cache() → None
  DELETE all entries from response_cache and parse_cache.
```

### parser.py

```python
def parse_wine_list(file_bytes: bytes, content_type: Optional[str], filename: Optional[str]) → str
  Dispatch: PDF → should_use_vision_extraction() → _extract_pdf_via_vision() or extract_text_from_pdf();
  image → extract_text_from_image(); text → decode_cellartracker_upload(). Returns formatted wine list text.

def extract_text_from_image(image_bytes: bytes) → str
  Resize image, call Claude Haiku vision with record_wine_list tool, return formatted wine list text.
  Raises OCRError on API/network failure.

def extract_text_from_pdf(pdf_bytes: bytes) → str
  Use PyMuPDF (fitz). Returns "" (empty) when no text layer found (scanned PDF).

def should_use_vision_extraction(pdf_bytes: bytes) → bool
  Run cheap text extract, check for food keywords / column collapse / empty result.
  Returns True if PDF should be routed to Haiku vision.

def prepare_image(image_bytes: bytes, max_dim: int = 2000) → bytes
  Resize to ≤max_dim px, convert to RGB JPEG at quality 85.

class WineListEntry(BaseModel)
  producer, wine_name, vintage, region, varietal, price, bottle_size, raw_text

class WineListExtraction(BaseModel)
  wines: list[WineListEntry], confidence_notes: str
```

### meal_parser.py

```python
def parse_meal_description(meal: str) → MealProfile
  Keyword-scan meal string for protein, cooking method, sauce flavor, heat level.
  Returns MealProfile dataclass. First match wins per category.

def meal_to_wine_hints(profile: MealProfile) → str
  Format MealProfile as newline-separated pairing hint lines for system prompt.
  Returns empty string if no recognizable meal elements.

def infer_wine_style_from_meal(profile: MealProfile) → List[str]
  Map protein+richness combos to wine style keywords.
  Not currently connected to the recommend flow.
```

### scorer.py

```python
@dataclass
class ScoringResult:
  total: float               # composite score 0.0–1.0
  breakdown: Dict[str, float]  # keys: confidence, completeness, grounding, budget_fit

def score_recommendation(
  response: RecommendationResponse,
  wine_list_text: str,
  profile: Optional[TasteProfile] = None
) → ScoringResult
  Four-dimension quality score. Weights: confidence 0.30, completeness 0.20,
  grounding 0.30, budget_fit 0.20.
  Grounding: case-insensitive substring match; fallback to ≥75% word-token overlap.
  Budget fit: [budget_min×0.8, budget_max×1.2]; neutral 0.5 if no budget/prices.
  Never raises; returns neutral ScoringResult(0.5, ...) on internal error.
```

### logging_utils.py

```python
def log_recommendation_event(
  meal: str,
  profile_hash: str,
  response: Optional[RecommendationResponse],
  scoring_result: Optional[ScoringResult],
  wine_list_hash: str,
  error: Optional[str] = None
) → None
  Append one JSONL line to logs/recommendations.jsonl.
  Logger: sommelier.recommendations (file-only, propagate=False).
  response/scoring_result may be None on error path → wine_count=0, score=null.
  Never raises to caller; internal errors swallowed via logger.exception.
```

### routes/debug.py

```python
@router.get("/debug/health") → Dict
  Return {"status": "healthy", "timestamp": ..., "service": "sommelier-api", "version": "1.0.0"}.

@router.get("/debug/status") → Dict
  Comprehensive status: inventory stats, profile stats, cache stats, system info.

@router.get("/debug/cache/stats") → Dict
  Cache entry count, age, size (bytes/KB), database path.

@router.post("/debug/cache/clear") → Dict
  Bust cache. Return confirmation.

@router.get("/debug/config") → Dict
  Return anthropic_model and anthropic_api_key_set (bool — key never exposed).

@router.get("/debug/logs/recent?limit=50") → Dict
  Last N lines from logs/api.log.

@router.get("/debug/endpoints") → Dict
  List all routes (path, name, methods) and count.

@router.get("/debug/memory") → Dict
  RSS, VMS, memory percent (requires psutil).

@router.get("/debug/ping") → Dict
  {"message": "pong", "timestamp": ...}.

@router.get("/debug/version") → Dict
  API version, Python version, platform, requirements count.
```

## Frontend (TypeScript)

### client/sdk.gen.ts

Auto-generated from OpenAPI spec. All endpoint calls go through this SDK.

Key types:
- `UploadInventoryResponse`, `UploadProfileResponse`, `ProfileSummaryResponse`
- `RecommendationResponse` (with `WineRecommendation[]`)
- Request functions: `postUploadInventory()`, `postRecommend()`, `getProfileSummary()`, etc.

### App.tsx

```tsx
export default function App()
  Root component. State: hasInventory (boolean).
  Renders: UploadFlow (if !hasInventory) or RecommendationScreen.
  Environment-gated: DebugPanel (if VITE_SHOW_DEBUG=true).
```

### UploadFlow.tsx

```tsx
export default function UploadFlow({ onInventoryUploaded })
  Multi-step: ProgressIndicator → UploadInventoryScreen → UploadProfileScreen → CompletionScreen.
  Callbacks: onInventoryUploaded when inventory uploaded.
```

### RecommendationScreen.tsx

```tsx
export default function RecommendationScreen({ onReset })
  File input (wine list), textarea (meal), style_terms override.
  Call postRecommend() with FormData.
  Display RecommendationResults or error.
  Button to reset and return to inventory upload.
```

### RecommendationResults.tsx

```tsx
export default function RecommendationResults({ response })
  Render WineRecommendation[] as ranked cards.
  Display confidence badges, vintage, region, price, reasoning.
  Copy-to-clipboard for wine details.
```

### DebugPanel.tsx

```tsx
export default function DebugPanel()
  Gated by VITE_SHOW_DEBUG env var.
  Show/hide ProfileSummaryView, cache stats, debug endpoints.
```
