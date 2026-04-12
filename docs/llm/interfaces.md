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

class ProfileSummaryResponse(BaseModel):
  top_varietals, top_regions, top_producers: List[str]
  highly_rated: List[Dict[str, str]]
  preferred_descriptors, avoided_styles: List[str]
  avg_spend: Optional[int]
```

### recommender.py

```python
def get_recommendation(
  wine_list_text: str,
  meal: str,
  system_prompt: str,
  ollama_url: str,
  ollama_model: str,
  image_b64: Optional[str] = None
) → RecommendationResponse
  Call Ollama /api/chat (fallback /api/generate). Parse JSON, strip markdown fences.
  Validate via Pydantic. Raise HTTPException(502) on LLM error or schema mismatch.
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

def build_enriched_profile_text(ollama_url: str, ollama_model: str) → str
  Like build_enhanced_profile_text() but calls enrich_profile_with_ollama() first.
  Prepends style_summary sentence if enrichment succeeded.
  This is the function called from main.py (not build_enhanced_profile_text).

def enrich_profile_with_ollama(raw: dict, ollama_url: str, ollama_model: str) → dict
  POST frequency-derived profile to Ollama; get back multi-word style phrases + style_summary.
  Returns raw unchanged on any error. 30s timeout.

def build_taste_profile_pydantic(profile_data: dict) → TasteProfile
  Calls build_taste_profile() and maps result to TasteProfile Pydantic model.
  Derives budget_min/max from avg_spend (±10). Sets profile_source="cellartracker".

def _infer_avoided_styles(profile_data: dict) → List[str]
  Scan tasting notes (type "notes", "consumed") for wines with low scores.
  Auto-detect score scale (max > 10 → 100-pt scale, threshold 60; else 5-pt scale, threshold 3.0).
  Only count tokens in hardcoded negative_indicator_words set. Return top 10 with freq ≥ 2.
```

### inventory.py

```python
def decode_cellartracker_upload(raw: bytes) → str
  Try UTF-8, UTF-8-sig, cp1252, latin-1. Return decoded string or lossy fallback.

def parse_ct_csv(csv_text: str) → List[Dict]
  Parse TSV, filter rows where Quantity > 0. Return list of dicts.

def save_inventory(csv_text: str) → List[Dict]
  Parse, write to inventory.json with timestamp. Return bottles list.

def load_inventory() → Optional[Dict]
  Load inventory.json. Return dict with bottles, age_hours, stale. None if missing.

def get_relevant_bottles(bottles: list[dict], style_terms: list[str]) → List[Dict]
  Filter bottles by style_terms (e.g., "burgundy" → ["pinot noir", ...]).
  Case-insensitive, accent-folded match on Varietal/Appellation/Wine/Producer.
  Return matching bottles or all if no keywords.
```

### cache.py

```python
def init_db() → None
  Create response_cache table if not exists.

def make_key(image_bytes: bytes, meal: str, inventory_hash: str, profile_hash: str) → str
  SHA256(image + meal + inventory_hash + profile_hash).

def inventory_hash(bottles: list[dict]) → str
  MD5(JSON-sorted bottles).

def get_cached(key: str) → Optional[str]
  SELECT response FROM cache WHERE key. Return JSON string or None.

def set_cached(key: str, response: str) → None
  INSERT OR REPLACE into cache.

def bust_cache() → None
  DELETE all cache entries.
```

### parser.py

```python
def extract_text_from_pdf(pdf_bytes: bytes) → str
  Use PyMuPDF (fitz). Return text or error message if parsing fails.

def parse_wine_list(file_bytes: bytes, content_type: Optional[str], filename: Optional[str]) → str
  Dispatch: PDF → extract_text_from_pdf, text → decode, image → "OCR not implemented" warning.
  Fallback to text decode if content type unknown. Return text or error message.
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
  Return OLLAMA_URL, OLLAMA_MODEL, and full environment dict (careful in production!).

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
