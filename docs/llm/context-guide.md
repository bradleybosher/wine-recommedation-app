# Context Guide: Which Docs to Inject

This guide maps common task types to the documentation you should include when asking an LLM for help.

## Modifying a Specific Module

**Task**: "Fix a bug in recommender.py" or "Add feature to profile.py"

**Include**:
1. `glossary.md` — Domain terms (what is a "taste profile", "confidence", etc.)
2. `conventions.md` — Error handling, naming patterns, preferred libraries
3. `modules/{module}.md` — Responsibility, dependencies, key functions, gotchas
4. `interfaces.md` — The specific function signatures in that module + related modules it calls
5. `architecture.md` — How the module fits into overall data flow

**Example** (fixing recommender.py):
- Read: glossary, conventions, modules/recommender.md, interfaces (recommender section)
- Skim: architecture (data flow around recommender)

---

## Adding a New Endpoint

**Task**: "Add /wine-search endpoint" or "Create new /preferences endpoint"

**Include**:
1. `architecture.md` — Stack, module map (know what's available)
2. `conventions.md` — Error handling patterns, API route naming (kebab-case), HTTP status codes
3. `modules/main.md` — How endpoints are structured, middleware patterns
4. `interfaces.md` — Existing endpoints for consistency
5. `models.py` content — Pydantic patterns (camelCase aliases, Optional fields)

**Skip**: Module-specific details unless your new endpoint uses them.

---

## Changing Taste Profile Logic

**Task**: "Improve avoided_styles inference" or "Add new preference dimension"

**Include**:
1. `glossary.md` — Taste profile fields, CellarTracker export types, scoring
2. `conventions.md` — Pattern for Counter-based analysis, fallback handling
3. `modules/profile.md` — Current inference logic, gotchas (score interpretation, empty profile)
4. `modules/inventory.md` — Related (how cellar data flows into profile)
5. `interfaces.md` — build_taste_profile() signature + return schema

**Optional**: `modules/main.py` if changing how profile is built (term frequency, cellar_summary).

---

## Debugging Recommendation Output

**Task**: "Why did the LLM recommend a terrible wine?" or "Verify recommendation JSON is valid"

**Include**:
1. `architecture.md` — Full data flow (wine list → recommendation)
2. `modules/recommender.md` — JSON parsing, Pydantic validation, fence stripping
3. `modules/prompt.md` — System prompt construction (what context is sent to LLM)
4. `modules/profile.md` — What taste profile is included in prompt
5. `glossary.md` — What "confidence", "reasoning", "list_quality_note" mean
6. `interfaces.md` — RecommendationResponse schema

**Optional**: `modules/main.md` (cache logic) if question is "why are all recommendations the same?"

---

## Adding PDF/Image Parsing

**Task**: "Implement OCR for image uploads" or "Handle encrypted PDFs"

**Include**:
1. `modules/parser.md` — Current file type dispatch, extract_text_from_pdf() implementation
2. `conventions.md` — Error handling (fail loudly, return error messages)
3. `interfaces.md` — parse_wine_list() signature
4. `architecture.md` — Where parser fits in data flow

**Skip**: Profile, recommender, inventory (independent of parsing).

---

## Optimizing Cache Behavior

**Task**: "Add cache expiry" or "Implement cache warming"

**Include**:
1. `modules/cache.md` — SQLite schema, cache key construction, TTL (currently missing)
2. `conventions.md` — Pattern for state management, optional fields
3. `interfaces.md` — cache module function signatures
4. `modules/main.md` — Where caching is called (recommend endpoint)

---

## Frontend Integration / SDK Usage

**Task**: "Add new form field to /recommend" or "Handle new response field in UI"

**Include**:
1. `interfaces.md` → models section — All Pydantic response schemas (camelCase JSON)
2. `glossary.md` — What each field means (confidence, reasoning, etc.)
3. `conventions.md` — Pydantic pattern: camelCase JSON + snake_case Python
4. `architecture.md` — Data flow (shows JSON goes to frontend)

**Skip**: Backend modules unless debugging SDK generation.

---

## Adding or Modifying Frontend UI Components

**Task**: "Add a new screen", "Style a new card", "Add an icon to X"

**Include**:
1. `conventions.md` → Frontend Styling Conventions — Glass design system rules (GlassCard, VibrantBackground, tokens, text opacity rules, button patterns)
2. `architecture.md` → Frontend module map — Where to place new components (`src/` root for feature components, `src/components/ui/` for primitives)
3. The existing component most similar to what you're building — read it for class patterns to follow

**Rules to enforce:**
- All card surfaces: use `<GlassCard>` — never `bg-white`
- All UI action icons: `lucide-react` with `strokeWidth={1.5}` — never inline SVG (exception: `WineBottleIcon` is a custom illustration, not an action icon)
- Text: white-based only inside GlassCard — never `text-gray-*`
- Do not add background-color to page-level containers — `VibrantBackground` owns the background

---

## Understanding Module Dependencies

**Task**: "What modules does inventory.py depend on?" or "Can I refactor X without breaking Y?"

**Include**:
1. `architecture.md` → Module Map — Visual dependency graph
2. `interfaces.md` — All function signatures (what each module exposes)
3. `modules/*.md` → Dependencies section (each module lists what it imports)

---

<<<<<<< HEAD
## Analysing Recommendation Quality / Scoring

**Task**: "Tune scoring weights", "Why is grounding low?", "Add a new scoring dimension", "Inspect recommendations.jsonl"

**Include**:
1. `interfaces.md` → scorer.py + logging_utils.py sections — `ScoringResult` fields, `score_recommendation()` signature, JSONL schema
2. `modules/main.md` — How scoring is called (non-blocking, post-LLM, pre-cache)
3. `architecture.md` → Data flow — Where scorer + logger sit in the pipeline
4. `modules/models.md` or `interfaces.md` → models — `WineRecommendation.confidence`, `TasteProfile.budget_min/max` (inputs to scorer)

**Key facts**:
- JSONL log: `logs/recommendations.jsonl` — one line per request (success or error)
- Scorer never raises; returns neutral 0.5 result on internal error
- Logger never raises; swallows own exceptions so the response path is never blocked
- `wine_list_hash` is MD5[:8] of parsed text, not raw file bytes
- Analysis snippet: `[json.loads(l) for l in open("logs/recommendations.jsonl")]`

---

=======
>>>>>>> 6caf2d0 (Initial commit: Setting up project structure)
## Writing Tests

**Task**: "How do I test the profile inference?" or "Set up integration test"

**Include**:
1. `interfaces.md` — All function signatures (what to call)
2. `modules/*.md` → Testing section (what each module needs for testing)
3. `conventions.md` → Error handling patterns (what errors to expect)
4. `glossary.md` → Domain terms (what valid inputs look like)

---

## Performance Profiling

**Task**: "Why is /recommend slow?" or "Optimize cache key generation"

**Include**:
1. `architecture.md` → Data flow (where time is spent)
2. `modules/*.md` → Key functions (what's expensive)
3. `conventions.md` → Patterns (e.g., how many Counter iterations in profile.py)
4. Specific module files if bottleneck identified

---

## Reviewing Code Before Merging

**Task**: PR review for a backend change

**Include**:
1. `conventions.md` — Does code follow patterns? Error handling? Naming?
2. Module file for the changed module — Does logic align with responsibility?
3. `interfaces.md` — Are function signatures backward-compatible?
4. `glossary.md` — Is terminology used correctly?

---

## Quick Reference: File Sizes & Tokens

| File | Purpose | Est. Tokens |
|---|---|---|
| glossary.md | Domain terms, abbreviations | 400 |
| conventions.md | Patterns, error handling, libraries | 600 |
| architecture.md | Stack, module map, data flow | 300 |
| interfaces.md | All public function signatures | 800 |
<<<<<<< HEAD
| modules/main.md | FastAPI app, endpoints | 280 |
=======
| modules/main.md | FastAPI app, endpoints | 250 |
>>>>>>> 6caf2d0 (Initial commit: Setting up project structure)
| modules/recommender.md | LLM calls, JSON parsing | 200 |
| modules/prompt.md | System prompt construction | 150 |
| modules/profile.md | Taste profile inference | 250 |
| modules/inventory.md | Cellar parsing, filtering | 200 |
| modules/cache.md | SQLite caching | 150 |
| modules/parser.md | File type dispatch, text extraction | 150 |
| modules/models.md | Pydantic schemas | 200 |

**Typical combo tokens**: Architecture + glossary + 2–3 modules ≈ 1500–2000 tokens (good context budget for focused work).

---

## Ambiguities to Flag

When using these docs, watch for:

1. **Score interpretation** — CellarTracker scoring may vary (1–100 vs. 1–5). Always verify scale.
2. **Accent folding** — Works for Latin wine names; fails on Cyrillic/CJK regions.
3. **Cache staleness** — No auto-expiry; user must manually bust cache.
4. **OCR** — Implemented via pytesseract + PIL (greyscale + sharpen pre-processing); requires Tesseract system binary; gracefully degrades if missing.
5. **Image vision** — Base64 image IS passed to Ollama for vision-capable models; not formally tested with a vision model.

These are flagged in module files but worth remembering across tasks.
