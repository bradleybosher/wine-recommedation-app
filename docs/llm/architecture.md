# Architecture Overview

## Stack

**Backend:** FastAPI (Python) + Pydantic v2 + SQLite (caching, accounts, profiles, flight history) + Anthropic Claude API (LLM, tool use) + JWT auth (passlib bcrypt + PyJWT)
**Frontend:** React 19 + TypeScript + Tailwind CSS v4 + Vite + react-router-dom + @hey-api/openapi-ts (SDK generation); old-world editorial design system (Vinothèque)
**LLM:** Anthropic Claude API via tool use — `bootstrap.ANTHROPIC_MODEL` (default `claude-sonnet-4-6`) for recommendation/synthesis; Claude Haiku (`parser._VISION_MODEL`, default `claude-haiku-4-5-...`) for vision parsing of wine-list photos. All calls routed through `llm_client.call_claude` (telemetry + retry wrapper around `client.messages.create`).
**Parsing:** PyMuPDF/fitz (PDFs), pytesseract/Pillow (OCR fallback), Claude Haiku vision (photos), csv (CellarTracker TSV)

## Module Map

```
Backend (Python)  — authoritative inventory mirrors CLAUDE.md "Modules:" line
├── main.py             → Composition root: env, logging, middleware, router includes, legacy migration
├── bootstrap.py        → .env + constants (JWT_SECRET, ANTHROPIC_MODEL, PROFILES_DIR, ORPHAN_PROFILE_ID)
├── auth.py             → Password hashing + JWT utilities (FastAPI-free)
├── dependencies.py     → get_current_user, get_current_profile FastAPI deps
├── logging_setup.py    → Logging configuration
├── logging_utils.py    → Structured JSONL event logger
├── retry_utils.py      → Retry helpers (used by llm_client)
├── middleware.py       → Request log + exception handlers
├── rate_limit.py       → Rate limiting
├── cellar_terms.py     → Cellar character helpers
├── llm_client.py       → call_claude telemetry wrapper (logs to logs/llm_calls.jsonl)
├── synonyms.py         → Grape/region synonym + sub-appellation expansion (no API call)
├── palate_stats.py     → Statistical palate analysis from consumed/inventory rows (no API call)
├── retrieval.py        → Retrieval-augmented pre-filtering, tiered profile-signal ranking (no API call)
├── insights.py         → Palate drift suggestion engine, statistical flight analysis (no LLM call)
├── models.py           → Pydantic schemas (incl. User/Profile/TokenResponse/PalateDriftSuggestion)
├── recommender.py      → Claude recommendation calls (tool use); bar blending vs wine_reference.json
├── prompt.py           → System prompt construction (tasting_note_library, aspirational_skew, stretch slot)
├── profile.py          → Taste profile building + synthesize_palate_from_notes (profile_id-keyed)
├── seed_profile.py     → Seed-bottle onboarding (profile_id-keyed)
├── inventory.py        → Inventory load/save, relevance filtering (profile_id-keyed)
├── cache.py            → SQLite: users/profiles/flights + global response/parse cache + legacy migration
├── parser.py           → PDF/text/image dispatch; Claude Haiku vision for photos
├── meal_parser.py      → Meal description → MealProfile → pairing hints string
├── scorer.py           → Recommendation quality scoring
├── wine_reviews.py     → Wine review helpers
├── test_fixtures.py    → Canned RecommendationResponse fixtures for TEST_MODE
├── data/wine_reference.json → ~80 calibrated bars entries per appellation/grape pair (0.0–1.0)
└── routes/
    ├── auth.py         → register, login, me, forgot-password, reset-password
    ├── profiles.py     → Named-profile CRUD / selection
    ├── profile.py      → Taste profile endpoints (upload-profile, seed-profile, PATCH, insights)
    ├── inventory.py    → Cellar endpoints (upload-inventory)
    ├── recommend.py    → /recommend orchestration (tasting note library, source modes)
    ├── history.py      → GET /history (flight history, scoped to active profile)
    ├── insights.py     → GET /profile/insights (drift suggestions)
    └── debug.py        → Diagnostics endpoints (health, ping, status, logs, cache)

Frontend (React)  — Vinothèque editorial design system
├── pages/App.tsx           → Root, routing
├── state/authStore.tsx     → useAuth (JWT session)
├── state/profileStore.tsx  → useProfiles (active profile selection)
├── AuthGuard               → Redirects unauthenticated routes to /login
├── AuthenticatedHeader     → Global header incl. ProfileSwitcher
├── Upload / recommendation screens → onboarding, meal input, ranked results
├── design/tokens           → Named colour tokens (INK, INK_SOFT, PAPER, OXBLOOD, RULE)
├── components/PaperFrame    → Page wrapper (editorial paper frame; not glassmorphism)
├── client/configure.ts      → SDK interceptors auto-inject Authorization + X-Profile-Id
├── client/sdk.gen.ts        → Authoritative SDK (generated from OpenAPI spec)
└── client/types.gen.ts      → Authoritative generated types
```

## Data Flow

```
Auth (JWT bearer; passlib bcrypt + PyJWT, HS256, 7-day expiry)
  → /auth/register, /auth/login issue tokens; /auth/me returns user + profiles
  → Every other endpoint requires Authorization: Bearer <jwt> + X-Profile-Id: <uuid>
    (dependencies.get_current_user reads JWT; get_current_profile validates ownership)

User uploads wine list (PDF/photo)
  → parser.py: dispatch by content type
  → extract_text_from_pdf() / OCR fallback / Claude Haiku vision for photos
  → Returns: wine_list_text

Per-profile data loaded (scoped to active profile_id)
  → inventory (inventory.py)  ← backend/profiles/{pid}/inventory.json
  → taste profile (profile.py) ← backend/profiles/{pid}/profile_data.json
  → For CellarTracker uploads the palate is synthesized at upload time via
    profile.synthesize_palate_from_notes() (single Claude call grounded by palate_stats)

Backend builds recommendation request (routes/recommend.py)
  → filter_wine_list() coarse pass → retrieval.rank_wine_list() profile-signal ranking (no API call)
  → palate_stats.compute_palate_stats() → aspirational_skew line (no API call)
  → _build_tasting_note_library() → TASTING NOTE LIBRARY block from consumed rows
  → meal_parser.parse_meal_description() → meal hints
  → prompt.py builds system prompt (taste_markers, palate_persona, tasting_note_library, stretch slot)

[Claude call] recommender.get_recommendation()
  → client.messages.create via llm_client.call_claude (tool use; structured JSON output)
  → Validate through RecommendationResponse Pydantic model
  → color derived server-side post-validation; bars blended 50/50 with wine_reference.json

  → Cache result in SQLite (response_cache, content-addressed, profile-scoped inputs)
  → Auto-saved to flights table with profile_id (cellar.db)

Return to frontend
  → RecommendationResponse → frontend renders ranked recommendations
  → GET /history (scoped to active profile); GET /profile/insights (drift suggestions)
```

## Key Design Decisions

1. **JWT auth, per-user, per-profile**: Open self-registration (single-tenant learning project). `users`, `profiles`, and `flights` tables live in `cellar.db`; each named palate has its own `backend/profiles/{profile_id}/` directory holding `profile_data.json` + `inventory.json`. Legacy single-tenant data is migrated once at startup into an orphan profile, claimed by the first registration.
2. **Schema-driven**: Pydantic models are contracts between backend layers; validation enforced at the Claude tool-output boundary.
3. **Fail loudly**: PDF parse errors, Claude errors, validation failures all surface to the user with specific messages.
4. **Reasonable defaults**: CellarTracker import optional; profile can also be seeded from 3–7 named bottles; manual overrides layer on top.
5. **Caching by content hash**: response/parse caches are content-addressed (global), keyed over profile-scoped inputs (wine list + meal + inventory/profile state) to prevent redundant Claude calls.
6. **No-API statistical passes**: retrieval ranking, palate stats, synonym expansion, and drift insights run deterministically without any LLM call.
7. **Portfolio-legible**: Code prioritizes readability over clever abstractions; minimal dependencies.

## File Stability

**Stable (unlikely to change):**
- models.py (core schemas locked by OpenAPI contract)
- cache.py (SQLite schema established)
- auth.py / dependencies.py (auth contract established)

**Active (evolving with feature work):**
- recommender.py (Claude prompt tuning, new models)
- prompt.py (system prompt refinements)
- profile.py (palate synthesis / taste profile heuristics)
- retrieval.py / palate_stats.py / insights.py (scoring + statistical heuristics)
- parser.py (new file type support, OCR, vision)
- routes/*.py (endpoint behaviour)

**Volatile (UX iteration):**
- Frontend components (styling, flow refinements)
- design/tokens — Vinothèque palette tokens may evolve
- components/PaperFrame — editorial frame treatment may be adjusted
- main.py composition (new routes, middleware changes)
```
