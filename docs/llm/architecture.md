# Architecture Overview

## Stack

**Backend:** FastAPI (Python) + Pydantic v2 + SQLite (caching) + Ollama (LLM inference)
**Frontend:** React 19 + TypeScript + Tailwind CSS + Vite + @hey-api/openapi-ts (SDK generation)
**LLM:** Ollama (local inference, llama3.2:3b default)
**Parsing:** PyMuPDF (PDFs), pytesseract/Pillow (OCR fallback), csv (CellarTracker TSV)

## Module Map

```
Backend (Python)
├── main.py                → FastAPI app, routes, logging middleware
├── models.py              → Pydantic schemas (TasteProfile, WineRecommendation, etc.)
├── recommender.py         → Ollama/LLM calls, JSON parsing, validation
├── prompt.py              → System prompt construction, schema definition
├── profile.py             → CellarTracker parsing, taste profile building
├── inventory.py           → Inventory load/save, JSON file storage
├── cache.py               → SQLite response caching, hashing
├── parser.py              → PDF/text/image dispatch, text extraction
├── meal_parser.py         → Meal description → MealProfile dataclass → pairing hints string
<<<<<<< HEAD
├── scorer.py              → Recommendation quality scoring (4-dimension, 0–1 float)
├── logging_utils.py       → Structured JSONL event logger (logs/recommendations.jsonl)
=======
>>>>>>> 6caf2d0 (Initial commit: Setting up project structure)
└── routes/debug.py        → Diagnostics endpoints (health, status, logs, cache)

Frontend (React)
├── App.tsx                → Root, inventory state, conditional routing
├── UploadFlow.tsx         → Multi-step onboarding (progress, callbacks)
├── UploadCellarInventoryScreen.tsx → File input for CellarTracker TSV
├── UploadTastingHistoryScreen.tsx  → File input for profile exports
├── RecommendationScreen.tsx  → Main UI: file upload, meal input, results
├── RecommendationResults.tsx → Display ranked wines with confidence
├── ProfileSummaryView.tsx    → Debug view of taste profile
├── DebugPanel.tsx           → Environment-gated (VITE_SHOW_DEBUG)
├── FileUploader.tsx         → Reusable file input component
├── MealDescriptionInput.tsx → Textarea for meal details
├── apiService.ts           → Deprecated (use SDK)
├── constants.ts            → UI strings, config
├── components/ui/
│   ├── VibrantBackground.tsx → Animated mesh gradient wrapper (wine-palette blobs)
│   └── GlassCard.tsx         → Frosted glass card primitive (backdrop-blur + glass tokens)
└── client/sdk.gen.ts       → Authoritative SDK (generated from OpenAPI spec)
```

## Data Flow

```
User uploads wine list (PDF/text)
  → parser.py: dispatch by content type
  → extract_text_from_pdf() or fallback to text decode
  → Returns: wine_list_text

User provides meal description
  → Meal text passed to recommender

Backend builds recommendation request
  → Load inventory (inventory.py)
  → Load profile (profile.py)
  → [Ollama call 1] Enrich profile: build_enriched_profile_text(url, model)
      → enrich_profile_with_ollama() → multi-word style phrases + style_summary
      → Falls back to standard paragraph if Ollama unavailable or empty result
  → Parse meal: parse_meal_description(meal) → meal_to_wine_hints() → meal_hints string
  → Build system prompt (prompt.py): enriched profile + cellar context + meal hints
  → Include relevant bottles from cellar (inventory.get_relevant_bottles)

[Ollama call 2] Recommender.get_recommendation()
  → POST to Ollama /api/chat with _RESPONSE_SCHEMA (grammar-constrained output)
  → Fallback: /api/generate if /api/chat 404; format="json" if schema dict rejected (400)
  → Up to 3 retry attempts on bad/garbage LLM output
  → Repair truncated JSON (brace counting); strip markdown fences
  → Detect garbage keys (empty key or "<|" special tokens)
  → Validate through RecommendationResponse Pydantic model
<<<<<<< HEAD

scorer.py: score_recommendation(response, wine_list_text, taste_profile)
  → confidence: avg mapped score (high=1.0, medium=0.67, low=0.33), weight 0.30
  → completeness: min(len(recs)/3, 1.0), weight 0.20
  → grounding: fraction of wine names found in wine_list_text (substring + fuzzy), weight 0.30
  → budget_fit: fraction of priced recs within [budget_min×0.8, budget_max×1.2], weight 0.20
  → Returns ScoringResult(total: float, breakdown: dict)

logging_utils.py: log_recommendation_event(...)
  → Appends one JSONL line to logs/recommendations.jsonl
  → Includes meal, profile_hash, wine_list_hash, wines[], score, score_breakdown, error

Cache result in SQLite
=======
  → Cache result in SQLite
>>>>>>> 6caf2d0 (Initial commit: Setting up project structure)

Return to frontend
  → RecommendationResponse (JSON array of WineRecommendation)
  → Frontend renders RecommendationResults component
```

## Key Design Decisions

1. **Stateless by default**: No persistent user accounts. Inventory/profile stored locally as JSON files, response cache in SQLite.
2. **Schema-driven**: Pydantic models are contracts between backend layers; validation enforced at LLM output boundary.
3. **Fail loudly**: PDF parse errors, LLM JSON errors, validation failures all surface to the user with specific messages.
4. **Reasonable defaults**: CellarTracker import optional; taste profile inferred from inventory if not provided.
5. **Caching by content hash**: SHA256(wine_list + meal + inventory_hash + profile_hash) prevents redundant LLM calls.
6. **JSON fence robustness**: Strip markdown fences from LLM JSON despite instructions (LLMs often do this anyway).
7. **Portfolio-legible**: Code prioritizes readability over clever abstractions; minimal dependencies.

## File Stability

**Stable (unlikely to change):**
- models.py (core schemas locked by OpenAPI contract)
- cache.py (SQLite schema established)

**Active (evolving with feature work):**
- recommender.py (LLM prompt tuning, new models)
- prompt.py (system prompt refinements)
- profile.py (taste profile inference heuristics)
- parser.py (new file type support, OCR)
<<<<<<< HEAD
- scorer.py (scoring weights and grounding heuristics may be tuned)
=======
>>>>>>> 6caf2d0 (Initial commit: Setting up project structure)
- routes/debug.py (diagnostic endpoints)

**Volatile (UX iteration):**
- Frontend components (styling, flow refinements)
- `src/index.css` `@theme {}` block — wine palette and glass tokens may evolve
- `components/ui/VibrantBackground.tsx` — blob colours/animation timing may be tuned
- `components/ui/GlassCard.tsx` — glass opacity/blur values may be adjusted
- main.py endpoints (new routes, changes to existing behavior)
