# Public Function Signatures

## Backend

### main.py

Composition root only — no handlers. Exposes `app: FastAPI`.

```python
# Startup wiring (in import order):
import bootstrap                          # loads .env, validates ANTHROPIC_API_KEY + JWT_SECRET
configure_logging()                       # from logging_setup
app = FastAPI()
app.add_middleware(CORSMiddleware, ...)   # expose_headers=["X-Profile-Id"]
install_middleware(app)                   # from middleware
init_db()                                 # from cache
migrate_legacy_data()                     # from cache — one-time legacy → multi-profile migration
purge_expired()                           # from cache
seed_wine_reviews()                       # from wine_reviews — one-time dataset seed
# 8 routers, in include order:
app.include_router(auth_router)
app.include_router(profiles_router)
app.include_router(debug_router)
app.include_router(history_router)
app.include_router(inventory_router)
app.include_router(profile_router)
app.include_router(recommend_router)
app.include_router(insights_router)
```

### wine_reviews.py

```python
def seed_wine_reviews() → None
  Create wine_reviews table in cellar.db and populate from backend/data/wine_reviews.csv.
  Auto-downloads the CSV (~56 MB) from GitHub if absent. No-op if table already has rows.
  Called once at startup.

def lookup_critic(wine_name: str, producer: Optional[str], vintage: Optional[int],
                  conn: Optional[sqlite3.Connection] = None) → Optional[Critic]
  Return a Wine Enthusiast score from the local dataset for a wine, or None.
  Matches by: SQL winery LIKE filter (most distinctive producer word) + vintage ±1
  + word-overlap on wine_name words ≥4 chars in dataset title. Threshold: 0.75.
  Pass conn to reuse an open connection across many lookups; otherwise a short-lived
  connection is opened and closed for the single call. Table-readiness (exists +
  non-empty) is probed once via _reviews_available() and cached in module state.

def enrich_critics(recommendation: RecommendationResponse) → None
  Iterate recommendation.recommendations; call lookup_critic for each wine and
  overwrite wine.critic with the real dataset score when a confident match is found.
  Opens ONE shared SQLite connection for the whole flight (not one per wine).
```

### bootstrap.py

```python
ANTHROPIC_API_KEY: str        # raises ValueError at import if unset
ANTHROPIC_MODEL: str          # defaults to "claude-sonnet-4-6"
MAX_UPLOAD_BYTES: int = 20 * 1024 * 1024
JWT_SECRET: str               # raises ValueError at import if unset
JWT_ALGORITHM: str = "HS256"  # default algorithm for token signing
JWT_EXPIRY_DAYS: int = 7      # token expiration duration
APP_BASE_URL: str = "http://localhost:5173"  # base URL for reset links in server logs
PROFILES_DIR: Path            # directory for per-profile data storage
ORPHAN_PROFILE_ID: str        # profile ID for legacy/unclaimed profiles
```

### auth.py

```python
def hash_password(plaintext: str) → str
  Hash a plaintext password using bcrypt. Returns hashed password string.

def verify_password(plaintext: str, password_hash: str) → bool
  Compare plaintext password against bcrypt hash. Returns True if valid, False otherwise.

def create_access_token(user_id: str) → str
  Generate JWT access token for user_id. Token expires after JWT_EXPIRY_DAYS.
  Uses JWT_SECRET and JWT_ALGORITHM from bootstrap. Returns token string.

def decode_access_token(token: str) → str
  Decode and validate JWT token. Raises TokenError on invalid/expired token.
  Returns decoded user_id string.
```

### logging_setup.py

```python
def configure_logging() → logging.Logger
  Attach a RotatingFileHandler (backend/logs/api.log, 1MB × 2 backups) + stderr StreamHandler
  to the "sommelier" logger at DEBUG. Idempotent. Returns the logger.
```

### middleware.py

```python
def install(app: FastAPI) → None
  Register the log_requests HTTP middleware (request_id, elapsed_ms, X-Request-ID header)
  + http_exception_handler (preserves intentional status codes) + unhandled_exception_handler
  (catch-all → 500 {"detail": "Internal server error", "error_type": ...}).
```

### dependencies.py

```python
def get_current_user(authorization: Optional[str] = Header(default=None)) → User
  Extract and validate JWT token from Authorization: Bearer <token> header.
  Raises HTTPException(401) if token missing, invalid, or expired.
  Returns User object with id and email.

def get_current_profile(
  x_profile_id: Optional[str] = Header(default=None, alias="X-Profile-Id"),
  user: User = Depends(get_current_user)
) → Profile
  Validate X-Profile-Id header against current user's profiles.
  Raises HTTPException(403) if profile not owned by user or not found.
  Falls back to user's default profile if header absent.
  Returns Profile object with id, user_id, name, is_default.
```

### rate_limit.py

```python
def check_rate_limit(ip: str) → None
  Raise HTTPException(429) if `ip` made ≥ 10 requests in the last 60 s.
  State: module-level _rate_counts dict; process-local.
```

### cellar_terms.py

```python
def inventory_terms_by_frequency(bottles: list[dict], limit: int = 10) → list[str]
  Counter over Varietal + Appellation. Raw value +3, tokenised non-stopword (≥ 3 chars) +1.
  Returns the top-`limit` terms.

def cellar_character_from_terms(terms: list[str]) → str
  Format up to the top 5 terms into a "skews heavily toward …" sentence fragment.
  Returns "" when given no terms.
```

### routes/auth.py

```python
@router.post("/auth/register", status_code=201)
def register(payload: RegisterRequest) → TokenResponse
  Create new user account with email and password. Hashes password with bcrypt.
  409 (HTTP_409_CONFLICT) if email already exists. First registered user claims the orphan
  default profile (legacy migration); otherwise a fresh default profile named "My Palate" is created.
  Returns access_token, token_type, user, and the single active profile (TokenResponse.profile).

@router.post("/auth/login")
def login(payload: LoginRequest) → TokenResponse
  Authenticate user by email and password. 401 if credentials invalid.
  Returns access_token, token_type, user, and the active profile (default, or the only one).

@router.get("/auth/me")
def me(user: User = Depends(get_current_user)) → AuthMeResponse
  Return authenticated user and all their profiles. Requires valid Authorization header.
  Returns AuthMeResponse with user object and list of Profile objects.

@router.post("/auth/forgot-password")
def forgot_password(payload: ForgotPasswordRequest) → MessageResponse
  Always returns 200 with a generic message (no account enumeration). If the email is registered,
  creates a reset token and logs the reset URL ("{APP_BASE_URL}/reset-password?token=...") to the
  server console.

@router.post("/auth/reset-password")
def reset_password(payload: ResetPasswordRequest) → MessageResponse
  Validate the reset token: 400 if missing/invalid, already used, or expired (30-min single-use).
  On success updates the user's password hash and marks the token used.
```

### routes/inventory.py

```python
@router.post("/upload-inventory")
async def upload_inventory(file: UploadFile, profile: Profile = Depends(get_current_profile)) → UploadInventoryResponse
  Save CellarTracker TSV export to profile-specific location. 413 if > MAX_UPLOAD_BYTES.
  Busts response cache for this profile.

@router.get("/inventory")
def get_inventory(profile: Profile = Depends(get_current_profile)) → InventoryResponse
  Load saved inventory for current profile with age_hours and stale flag.
```

### routes/profile.py

```python
@router.post("/upload-profile")
async def upload_profile(file: UploadFile, profile: Profile = Depends(get_current_profile)) → UploadProfileResponse
  Detect export type via profile.ingest_export. 400 on parse failure or empty file,
  413 on oversize. Clears any prior _overrides and _synthesized, then attempts
  synthesize_palate_from_notes(profile.id, ...) and persists the result under _synthesized on success.
  Synthesis failure (Anthropic error etc.) is logged and tolerated — the deterministic
  fallback in build_taste_profile() keeps the upload working. The status string
  ("synthesized (confidence: ...)" | "failed (deterministic fallback active)" | "skipped")
  is appended to the response message. Returns type detected + derived TasteProfile.

@router.post("/seed-profile")
async def seed_profile(req: SeedProfileRequest, profile: Profile = Depends(get_current_profile)) → UploadProfileResponse
  Infer a profile from 3–7 loved (and 0–3 disliked) wines via one Anthropic tool-use call.
  Catches (anthropic.APIError, RuntimeError, ValueError) → 502. Backs up profile data for profile.id,
  then overwrites it. Clears any prior _overrides. Returns taste_profile with
  profile_source="seed_bottles" and inference_confidence in {high, medium, low}.

@router.post("/profile/revert")
async def revert_profile(profile: Profile = Depends(get_current_profile)) → dict
  Restore profile data from backup for profile.id. 404 if no backup.
  Busts response + profile cache. Returns {"message": "Profile reverted..."}.

@router.patch("/profile")
def patch_profile(req: ProfilePatchRequest, profile: Profile = Depends(get_current_profile)) → ProfileSummaryResponse
  Merge non-None fields from req into profile_data["_overrides"], then return a fresh
  ProfileSummaryResponse. 400 if no fields supplied. Editable fields: top_varietals,
  top_regions, preferred_descriptors, avoided_styles, avg_spend, style_summary,
  taste_markers. Overrides are layered on top of the derived/inferred profile by
  build_taste_profile() and are cleared whenever /upload-profile or /seed-profile runs.

@router.get("/profile-summary")
def profile_summary(profile: Profile = Depends(get_current_profile)) → ProfileSummaryResponse
  Build taste profile, taste markers, and cellar stats for current profile. An explicit
  taste_markers dict on the merged profile (seed/synthesized inference or user override) wins;
  otherwise markers are derived from descriptors. style_summary comes from a user override if
  present, or the seed-derived/synthesized profile when available, otherwise from
  enrich_profile_with_anthropic (failure-tolerant — falls back to None).
  inference_confidence is surfaced for both seed_bottles and cellartracker_synthesized.
```

### routes/profiles.py

```python
@router.get("/profiles")
def list_profiles(user: User = Depends(get_current_user)) → list[Profile]
  Return all profiles owned by current user. Requires valid Authorization header.
  Returns list of Profile objects sorted by creation time.

@router.post("/profiles")
async def create_profile(req: ProfileCreateRequest, user: User = Depends(get_current_user)) → Profile
  Create a new empty profile for the current user with the given name.
  201 on success. Returns newly created Profile object.

@router.patch("/profiles/{profile_id}")
async def update_profile(
  profile_id: str,
  req: ProfileUpdateRequest,
  user: User = Depends(get_current_user)
) → Profile
  Update profile name and/or is_default flag. 403 if profile not owned by user.
  404 if profile not found. When setting is_default=True, unsets default on other user profiles.
  Returns updated Profile object.

@router.delete("/profiles/{profile_id}")
async def delete_profile(profile_id: str, user: User = Depends(get_current_user)) → dict
  Delete profile by ID. 403 if not owned by user. 404 if not found.
  409 if this is the user's only profile. Returns {"id": profile_id, "deleted": True}.
```

### routes/recommend.py

```python
@router.post("/recommend")
async def recommend(
  request: Request,
  profile: Profile = Depends(get_current_profile),
  # Legacy
  meal: str = Form(default=""), style_terms: str = Form(default=""),
  # New Preferences (Phase 5)
  occasion: str = Form(default=""), menu: str = Form(default=""),
  cellar_leans: str = Form(default=""), temperament: str = Form(default=""),
  ceiling: str = Form(default=""), bottle_count: int = Form(default=3),
  source_mode: str = Form(default="winelist"),
  # File
  wine_list: UploadFile = File(default=None),
  test_fixture: str = Form(default=""),
) → RecommendationResponse
  Composes effective_meal from occasion+menu (or legacy meal) and effective_style from
  cellar_leans+temperament (or legacy style_terms).
  Rate-limit (429) → TEST_MODE short-circuit → source_mode validation → 413 size check →
  response-cache lookup (key includes bottle_count + ceiling + profile.id) → parse wine list (skipped when
  source_mode="cellar") → enriched profile (non-fatal) → cellar context → meal hints →
  system prompt (with bottle_count, budget_ceiling) → get_recommendation (502 on failure) →
  score + log event (non-blocking) → cache + return.
  Caps scorer confidence at "medium" when profile_source == "seed_bottles".
```

### seed_profile.py

```python
def infer_profile_from_seeds(req: SeedProfileRequest, anthropic_api_key: str, anthropic_model: str) → dict
  Single Anthropic tool-use call to identify each named wine and synthesize aggregate
  signals (top_varietals, top_regions, top_producers, highly_rated, preferred_descriptors,
  avoided_styles, avg_spend, style_summary, taste_markers, inference_confidence,
  profile_source="seed_bottles", seed_bottle_count).

def persist_seed_profile(profile_id: str, inferred: dict) → None
  Backs up the existing profile data to backup file (if it exists).
  Then overwrites profile data with {"_inferred": inferred}, clearing any legacy CT keys.

def load_inferred_profile(profile_id: str) → dict | None
  Return the inferred profile if present for the given profile_id.
```

### models.py

```python
class Bottle(BaseModel):
  All CellarTracker fields (iWine, Type, Color, ..., EndConsume). Optional fields.
  ConfigDict: alias_generator=to_camel, populate_by_name=True.

class User(BaseModel):
  id: str
  email: EmailStr
  created_at: float

class Profile(BaseModel):
  id: str
  user_id: Optional[str] = None   # NULL while orphan; populated once claimed
  name: str
  is_default: bool = False
  created_at: float

class RegisterRequest(BaseModel):
  email: str
  password: str

class LoginRequest(BaseModel):
  email: str
  password: str

class TokenResponse(BaseModel):
  access_token: str
  token_type: str = "bearer"
  user: User
  profile: Profile      # the single active profile (claimed orphan on first register, else new empty)

class AuthMeResponse(BaseModel):
  user: User
  profiles: list[Profile]

class ForgotPasswordRequest(BaseModel):
  email: EmailStr

class ResetPasswordRequest(BaseModel):
  token: str
  new_password: str     # Field(min_length=8, max_length=128)

class MessageResponse(BaseModel):
  message: str

class ProfileCreateRequest(BaseModel):
  name: str

class ProfileUpdateRequest(BaseModel):
  name: Optional[str] = None
  is_default: Optional[bool] = None

class TasteProfile(BaseModel):
  preferred_styles, preferred_regions, preferred_grapes, avoided_styles: List[str]
  budget_min, budget_max: Optional[float]
  occasion, food_pairing: Optional[str]
  profile_source: str = "manual"  # "cellartracker" | "cellartracker_synthesized" | "seed_bottles" | "manual"
  inference_confidence: Optional[str]  # "high"|"medium"|"low"; set for "seed_bottles" or "cellartracker_synthesized"
  avoided_style_tokens: List[str]  # single-token markers distilled from avoided_styles (e.g. "oaky", "jammy")
  top_producers: List[str]         # repeat-purchase producers from note history (strongest positive signal)

class SeedBottle(BaseModel):
  producer: str
  wine: str
  vintage: Optional[int]
  sentiment: Literal["loved", "disliked"] = "loved"
  note: Optional[str]

class SeedProfileRequest(BaseModel):
  loved: List[SeedBottle]      # 3..7
  disliked: List[SeedBottle]   # 0..3

class Coords(BaseModel):
  lat: float
  lon: float

class DrinkWindow(BaseModel):
  from_year: int = Field(alias="from")   # Python: from_year=; JSON key: "from"
  peak: int
  until: int

class WineColor(BaseModel):
  glass: str   # hex — background swatch
  tint: str    # hex — tint layer
  ink: str     # hex — text on palette
  accent: str  # hex — highlight

class StructureBars(BaseModel):
  tannin: float
  acidity: float
  body: float
  sweetness: float
  oak: float

class Critic(BaseModel):
  score: float
  source: str

class WineRecommendation(BaseModel):
  rank: int
  wine_name: str
  producer, region: Optional[str]
  vintage: Optional[int]
  price: Optional[float]       # coerce_price validator strips currency symbols
  reasoning: str               # 2–4 sentences: personal comparison → contrast → food → cellar note
  confidence: str              # "high|medium|low — single clause reason"
  fits: Optional[List[str]]    # 2–3 short tags grounding pick in profile signals; omit when no clean match
  evidence_quotes: Optional[List[str]]  # 1-2 verbatim quotes from TASTING NOTE LIBRARY; omit if no library/match
  stretch: bool = False        # True when this pick is intentionally outside the safe persona zone
  # Phase 5 enrichment fields (all optional; populated server-side or by Claude):
  appellation: Optional[str]
  country: Optional[str]
  coords: Optional[Coords]
  grape: Optional[str]
  abv: Optional[float]
  drink: Optional[DrinkWindow]
  color: Optional[WineColor]   # server-derived post-validation; never in Claude tool schema
  bars: Optional[StructureBars]
  wheel: Optional[Dict[str, int]]   # 6–8 aroma descriptors, intensity 0–10
  nose: Optional[str]
  palate: Optional[str]
  pairs: Optional[List[str]]
  critic: Optional[Critic]
  verified_on_list: Optional[bool]  # server-set post-validation; True/False on winelist; None on cellar mode

class RecommendationResponse(BaseModel):
  recommendations: List[WineRecommendation]
  list_quality_note: Optional[str]
  profile_match_summary: str (1 sentence)
  flight_id: Optional[str]    # set after save_flight(); absent on cache hits

class PalateDriftSuggestion(BaseModel):
  dimension: str              # "preferred_grapes" | "preferred_regions"
  current: List[str]          # current profile values for this dimension
  suggested: List[str]        # terms Claude keeps recommending but profile omits
  rationale: str              # human-readable explanation of the signal
  supporting_flight_ids: List[str]   # flight IDs that drove this suggestion
  # ConfigDict: alias_generator=to_camel, populate_by_name=True

class FlightFeedback(BaseModel):
  chip: str           # "too_bold" | "over_budget" | "off_profile" | "perfect"
  recorded_at: float  # unix timestamp

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
  style_summary: Optional[str]      # Anthropic palate portrait sentence
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
  image_b64: Optional[str] = None,
  source_mode: str = "winelist",
) → RecommendationResponse
  Call Anthropic Claude via tool use (provide_recommendations tool). tool_block.input is a
  pre-parsed dict — no JSON parsing needed. Retry up to 3× on Pydantic ValidationError.
  Raise HTTPException(502) on API error or unrecoverable schema mismatch.
  Post-validation: calls _derive_color() for each WineRecommendation where color is None,
  so color is always populated on the returned object. color is excluded from the Claude
  tool schema to avoid hallucinated hex codes.
  Post-validation: calls _find_reference_bars() + _blend_bars() for each wine with bars populated,
  blending Claude's 0-10 bars 50/50 with wine_reference.json reference values (0.0-1.0 × 10).
```

### prompt.py

```python
def format_bottle(b: dict) -> str
  Format bottle as "{Vintage} {Producer} {Wine} (drink {Begin}–{End})".

def build_system_prompt(
  relevant_bottles: list[dict],
  cellar_summary: str = "",
  taste_profile_override: str | None = None,
  meal_hints: str = "",
  profile_source: str = "cellartracker",
  bottle_count: int = 3,
  budget_ceiling: str = "",
  taste_markers: dict | None = None,
  palate_persona: str | None = None,
  source_mode: str = "winelist",
  tasting_note_library: str = "",
  aspirational_skew: str = "",
) → str
  Construct system prompt: sommelier persona, taste profile, relevant bottles, schema, meal hints.
  If taste_profile_override provided, skips internal build_enriched_profile_text_basic() call.
  When profile_source="seed_bottles", prepends directional-profile caveat.
  When taste_markers provided, renders a numeric block ("Acidity 5/5, Tannin 3/5, ...") under
  the prose profile so Claude can cite specific axes in reasoning/fits.
  When palate_persona provided, quotes it verbatim under a **PALATE PERSONA** header inserted
  above the PRIORITY block; fits tags may cite/paraphrase persona phrases.
  Injects CONSTRAINTS block: "Return exactly N ranked recommendations." + optional budget ceiling.
  When bottle_count >= 3, adds stretch/discovery slot instruction for the final rank.
  When tasting_note_library non-empty, injects **TASTING NOTE LIBRARY** block enabling evidence_quotes.
  When aspirational_skew non-empty, injects **ASPIRATIONAL SKEW** line above cellar section.
  source_mode controls mode intro, hard constraint, and reasoning structure ("winelist" or "cellar").
  Writes full prompt to prompt.log via dedicated _prompt_logger.
  Returns full prompt string with JSON schema embedded.
```

### profile.py

```python
def ingest_export(raw: bytes) → Tuple[str, List[Dict[str, str]]]
  Decode bytes, parse TSV, validate minimal CellarTracker column set, detect export type.
  Return (type, rows). Raises ValueError if file format is unrecognized (missing all expected CT columns).

def write_profile_data(profile_id: str, data: dict) → None
  Write profile data dict to profile_id's JSON file in PROFILES_DIR. Busts profile cache.

def backup_profile_data(profile_id: str) → bool
  Backup profile_id's current data file to .backup file. Returns True if successful, False if no file to back up.

def restore_profile_backup(profile_id: str) → bool
  Restore profile_id's data from .backup file. Returns True if successful, False if no backup exists.

def bust_profile_cache(profile_id: str) → None
  Invalidate the module-level profile cache for profile_id. Called after any write to profile data.
  Ensures the next load_profile_data(profile_id) call reads the updated file instead of returning stale data.

def save_profile_export(profile_id: str, raw: bytes) → str
  Ingest, merge into profile data for profile_id. Busts profile cache after write. Return export type.

def load_profile_data(profile_id: str) → Dict
  Load profile_id's data JSON or {} with mtime-based caching per profile_id.
  On cache hit (mtime unchanged), returns cached dict. On cache miss or file change, reads from disk.
  Gracefully handles missing/corrupt files. Cache busted by bust_profile_cache(profile_id).

def build_taste_profile(profile_data: dict) → Dict
  Short-circuit order: (1) profile_data["_synthesized"] (LLM-synthesized CT palate);
  (2) profile_data["_inferred"] (seed-bottle profile); (3) deterministic frequency fallback.
  Fallback derives taste profile: top varietals, regions, producers, preferred descriptors.
  Infer avoided_styles from low-scored (≤3.0) tasting notes.
  Return dict with keys: top_varietals, top_regions, top_producers, highly_rated,
  preferred_descriptors, avoided_styles, avg_spend (plus taste_markers, palate_persona,
  style_summary, inference_confidence, profile_source when sourced from _synthesized or _inferred).

def build_enriched_profile_text_basic(profile_id: str) → str
  Format taste profile as prose paragraph for system prompt (non-enriched version).
  Fallback to OWNER_PROFILE constant if no profile data.
  Called by prompt.py as fallback when enrichment is not available.

def build_enriched_profile_text(profile_id: str, anthropic_api_key: str, anthropic_model: str) → str
  Like build_enriched_profile_text_basic() but calls enrich_profile_with_anthropic() first.
  Prepends style_summary sentence if enrichment succeeded.
  This is the function called from main.py (not build_enriched_profile_text_basic).

def enrich_profile_with_anthropic(raw: dict, anthropic_api_key: str, anthropic_model: str) → dict
  LEGACY fallback path — only invoked when no _synthesized profile exists. The newer
  synthesize_palate_from_notes() subsumes this with richer context (raw notes vs. tokens).
  Call Anthropic Claude via tool use (enrich_taste_profile tool); get back multi-word style
  phrases + style_summary. tool_block.input is pre-parsed — no JSON parsing needed.
  Returns raw unchanged on any error (fully safe fallback).
  enrich_profile_with_ollama is kept as a backward-compat alias.

def synthesize_palate_from_notes(profile_id: str, profile_data: dict, anthropic_api_key: str, anthropic_model: str) → dict | None
  Primary LLM palate path for CellarTracker uploads. Single Anthropic tool-use call
  (synthesize_palate_profile tool) fed raw tasting notes grouped by score tier (high/mid/low,
  capped 50 per tier) plus the deterministic structured signals.
  Returns dict shaped like seed-bottle inferred profile + palate_persona (2-3 sentence
  sommelier persona), note_count, profile_source="cellartracker_synthesized".
  Returns None when no notes present. Raises anthropic.APIError / RuntimeError on failure —
  caller must catch so the deterministic fallback in build_taste_profile() can take over.

def persist_synthesized_profile(profile_id: str, synthesized: dict) → None
  Write synthesized dict to profile_id's data under _synthesized key. Preserves underlying CT
  rows (list/notes/consumed/purchases). Busts profile cache after write.

def clear_synthesized_profile(profile_id: str) → None
  Remove _synthesized from profile_id's data (no-op if absent). Called before a fresh
  synthesis attempt so a failed Claude call doesn't leave stale data behind.

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

def save_inventory(profile_id: str, csv_text: str) → List[Dict]
  Parse, write to inventory.json for profile_id with timestamp. Return bottles list.

def load_inventory(profile_id: str) → Optional[Dict]
  Load inventory.json for profile_id. Return dict with bottles, age_hours, stale. None if missing.

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
  Create all tables (response_cache, parse_cache, users, profiles, flights) if not exist.

def make_parse_key(pdf_bytes: bytes) → str
  SHA256(pdf_bytes) only — independent of meal, inventory, profile. Key for parse cache.

def get_parse_cached(pdf_hash: str) → Optional[str]
  SELECT wine_list_text FROM parse_cache WHERE pdf_hash. Return text or None if missing/expired.

def set_parse_cached(pdf_hash: str, wine_list_text: str) → None
  INSERT OR REPLACE into parse_cache.

def make_key(image_bytes: bytes, meal: str, inventory_hash: str, profile_hash: str = "") → str
  SHA256(image + meal + inventory_hash + profile_hash). Key for response cache.

def inventory_hash(bottles: list[dict]) → str
  MD5(JSON-sorted bottles).

def get_cached(key: str) → Optional[str]
  SELECT response FROM response_cache WHERE key. Return JSON string or None.

def set_cached(key: str, response: str) → None
  INSERT OR REPLACE into response_cache.

def bust_cache() → None
  DELETE all entries from response_cache and parse_cache.

def create_user(email: str, password_hash: str) → dict
  INSERT new user into users table. Returns the user dict (id, email, password_hash, created_at).

def get_user_by_email(email: str) → Optional[dict]
  SELECT user by email. Returns dict with id, email, password_hash, created_at, or None.

def get_user_by_id(user_id: str) → Optional[dict]
  SELECT user by id. Returns dict with id, email, password_hash, created_at, or None.

def count_users() → int
  Return total number of users in database.

def update_user_password(user_id: str, password_hash: str) → None
  UPDATE users SET password_hash for user_id. Used by reset-password flow.

def create_reset_token(user_id: str, expires_in_seconds: int = 1800) → str
  Generate a secrets.token_urlsafe(32) token, insert into password_reset_tokens with 30-min expiry. Returns token string.

def get_reset_token(token: str) → Optional[dict]
  SELECT token row. Returns dict with token, user_id, expires_at, used (bool), or None if not found.

def mark_reset_token_used(token: str) → None
  UPDATE password_reset_tokens SET used=1 for token. Enforces single-use.

def create_profile(user_id: str, name: str, is_default: bool = False, profile_id: Optional[str] = None) → dict
  INSERT new profile for user (unsets default on others when is_default=True).
  Returns the profile dict (id, user_id, name, is_default, created_at).

def list_profiles_for_user(user_id: str) → list[dict]
  SELECT all profiles for user (ORDER BY is_default DESC, created_at ASC).
  Each dict: id, user_id, name, is_default, created_at.

def get_profile(profile_id: str) → Optional[dict]
  SELECT profile by id. Returns dict with id, user_id, name, is_default, created_at, or None.

def update_profile(profile_id: str, name: Optional[str] = None) → Optional[dict]
  UPDATE profile name (no-op if name is None). Returns the refreshed profile dict, or None if not found.

def set_default_profile(profile_id: str, user_id: str) → None
  Unset default on all of user's profiles, then set profile_id as default (scoped to user_id).

def delete_profile(profile_id: str) → bool
  DELETE profile by id, its flights, and its on-disk JSON directory. Caller must enforce ownership.
  Returns True if a row was deleted, False otherwise.

def get_orphan_profile() → Optional[dict]
  Return the unclaimed migration profile (user_id IS NULL) dict, or None.

def claim_orphan_profile(user_id: str) → Optional[str]
  If orphan profile exists, update its user_id and set is_default=True for user.
  Returns profile_id on success, None if no orphan profile or already claimed.

def migrate_legacy_data() → Optional[str]
  Migrate legacy single-profile data to multi-profile structure. Returns profile_id of migrated profile,
  or None if no legacy data or already migrated.

def save_flight(occasion: str, menu: str, cellar_leans: str, temperament: str,
                ceiling: str, bottle_count: int, source_mode: str,
                wine_list_hash: str, profile_hash: str, response, profile_id: str) → str
  INSERT completed recommendation into flights table for profile_id (profile_id is the LAST
  positional parameter). Returns UUID4 hex flight_id.

def list_flights(profile_id: str, limit: int = 50, offset: int = 0) → list[dict]
  SELECT newest-first from flights for profile_id. Each dict: id, created_at, occasion, menu, top_wine_name, bottle_count.

def get_flight(flight_id: str) → Optional[dict]
  SELECT full flight row by id including response_json, or None if not found.

def delete_flight(flight_id: str) → bool
  DELETE flight by id. Returns True if deleted, False if not found.

def update_flight_feedback(flight_id: str, feedback: FlightFeedback) → bool
  Merge feedback.model_dump(by_alias=True) into the response_json blob under key "feedback".
  No new DB columns. Returns True if updated, False if flight not found.
```

### routes/history.py

```python
GET    /history                         → list[FlightSummary]   # limit/offset query params
GET    /history/{flight_id}             → FlightRecord          # includes feedback if submitted
PATCH  /history/{flight_id}/feedback   → {"ok": true}           # body: FlightFeedback; 404 if not found
DELETE /history/{flight_id}            → {"id": str, "deleted": True}
```

### routes/insights.py

```python
@router.get("/profile/insights")
def get_insights(profile: Profile = Depends(get_current_profile)) → list[PalateDriftSuggestion]
  Return palate drift suggestions for the active profile. Delegates to compute_drift_suggestions(profile.id).
  Returns [] when fewer than 3 flights exist or no term meets the 30% hit-rate threshold. Never 404.
  Requires Bearer JWT + X-Profile-Id header.
```

### llm_client.py

```python
def call_claude(purpose: str, client: anthropic.Anthropic, **kwargs) → anthropic.types.Message
  Telemetry wrapper around client.messages.create(**kwargs).
  Logs request/response to logs/llm_calls.jsonl as NDJSON:
    {purpose, model, input_tokens, output_tokens, stop_reason, latency_ms, timestamp_utc}
  Passes all kwargs through unchanged. Raises on any Anthropic API error (no retry — caller handles that).
  Log failures are silently ignored so telemetry never blocks a real request.
```

### retrieval.py

```python
def rank_wine_list(
  wine_list_text: str,
  profile: TasteProfile,
  override_terms: Optional[list[str]] = None,
  limit: int = 40,
) → str
  Retrieval-augmented pre-filter for large wine lists. No-op when list has ≤ limit lines.
  Tiered scoring per line: baseline +0.25; top-producer name +2.0; region/appellation +1.5
  (expanded via synonyms.expand_terms); grape/varietal +1.0 (expanded via synonyms.expand_terms);
  style descriptor +0.5; override_terms +1.0; avoided-style token −2.0;
  price < 50% of budget_min −0.5; price > 200% of budget_max −0.5.
  Matching is accent-normalised (NFKD) and case-insensitive substring.
  Price extracted from $NNN, £NNN, €NNN patterns.
  Ties broken by original list position. Returns newline-joined top `limit` lines.
  When profile has no positive signals, truncates to first `limit` lines (safe fallback).
```

### synonyms.py

```python
def expand_term(term: str) -> list[str]
  Return [term] + all known synonyms/sub-appellations for the canonical term.
  Returns [term] if no expansion defined.

def expand_terms(terms: list[str]) -> list[str]
  Expand all terms in the list. Returns flat deduplicated list.
```

### palate_stats.py

```python
def compute_palate_stats(
  consumed_rows: list[dict],
  inventory_rows: list[dict] | None = None,
  avoided_styles: list[str] | None = None,
) -> PalateStats
  Compute statistical palate features from CellarTracker data. No LLM calls.
  Returns PalateStats TypedDict with: producer_frequency, region_frequency, varietal_frequency,
  price_distribution, style_signals (natural_wine_affinity, oxidative_affinity, aging_preference),
  avoided_style_tokens, top_producers, note_count, aspirational_skew (cellar_over_consumed + summary_line).

def format_stats_for_prompt(stats: PalateStats) -> str
  Format PalateStats as a "STATISTICAL EVIDENCE" text block for injection into synthesis prompt.
```

### insights.py

```python
def compute_drift_suggestions(profile_id: str) → list[PalateDriftSuggestion]
  Palate drift suggestion engine. Analyses the _FLIGHT_WINDOW (20) most recent flights for profile_id.
  Extracts grape and region from every recommended wine. Counts how many distinct flights each term appeared in.
  Surfaces terms above _MIN_HIT_RATE (30%) not already in the profile (substring-safe check).
  Returns up to _MAX_SUGGESTIONS (3) PalateDriftSuggestion objects.
  Returns [] when fewer than _MIN_FLIGHTS (3) flights exist. No LLM calls — purely statistical.
```

### retry_utils.py

```python
def call_with_retry(
  fn: Callable,
  *,
  max_attempts: int = 3,
  retryable_on: tuple = (Exception,)
) → Any
  Call fn() and retry up to max_attempts times on retryable exceptions.
  Args: fn (zero-argument callable), max_attempts (default 3), retryable_on (tuple of exception types).
  Exponential backoff: delay = 1.5 ** attempt seconds between retries.
  Returns: Return value of fn() on success.
  Raises: The last exception from fn() if all attempts fail; any exception NOT in retryable_on
  is re-raised immediately (fail-fast). Logs each retry attempt and final failure at WARNING/ERROR levels.
```

### parser.py

Module-level environment variables (loaded at import time):
- `ANTHROPIC_API_KEY` (required) → `_ANTHROPIC_API_KEY`, raises RuntimeError if missing
- `ANTHROPIC_VISION_MODEL` (optional, defaults to "claude-haiku-4-5-20251001") → `_VISION_MODEL`

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
  Run cheap text extract, check for food keywords / token count / empty result.
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
  Normalizes synonyms (e.g., "pan-seared" → "seared", "beef tenderloin" → "beef") BEFORE
  keyword matching, enabling paraphrased descriptions to map correctly.
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
  warnings: list[str]        # optional data-gap warnings (e.g., empty wine_list_text)

def score_recommendation(
  response: RecommendationResponse,
  wine_list_text: str,
  profile: Optional[TasteProfile] = None,
  cap_confidence: bool = False
) → ScoringResult
  Four-dimension quality score. Weights: confidence 0.30, completeness 0.20,
  grounding 0.30, budget_fit 0.20.
  Grounding: delegates to _is_grounded() per wine. Returns 0.0 if no recommendations; 0.5 if wine_list_text empty.

def _is_grounded(wine_name: str, wine_list_text: str) → bool
  Return True if wine_name is plausibly in wine_list_text.
  Fast path: case-insensitive substring. Fallback: ≥75% significant tokens (≥3 chars) found in list.
  Importable from scorer for use in routes/recommend.py to set verified_on_list per wine.
  Budget fit: [budget_min×0.8, budget_max×1.2]; neutral 0.5 if no budget/prices.
  Populates warnings list with data-gap notes when neutral fallbacks are used.
  Never raises; returns neutral ScoringResult(0.5, ..., warnings=[]) on internal error.
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
  No auth.

@router.get("/debug/status") → Dict
  Comprehensive status: inventory stats, profile stats, cache stats, system info.
  Requires get_current_profile (Bearer JWT + X-Profile-Id) — scoped to the active profile.

@router.get("/debug/cache/stats") → Dict
  Cache entry count, age, size (bytes/KB), database path. No auth.

@router.post("/debug/cache/clear") → Dict
  Bust cache. Return confirmation. Requires get_current_user (Bearer JWT).

@router.get("/debug/stats") → Dict
  Aggregate LLM telemetry from logs/llm_calls.jsonl: per-purpose P50/P90 latency, token totals,
  estimated cost, today vs all-time. Requires get_current_user (Bearer JWT).

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
  Render "Why this fits you" panel of fitMarkers tags when present (omitted otherwise).
  Copy-to-clipboard for wine details.
```

### DebugPanel.tsx

```tsx
export default function DebugPanel()
  Gated by VITE_SHOW_DEBUG env var.
  Show/hide ProfileSummaryView, cache stats, debug endpoints.
```
