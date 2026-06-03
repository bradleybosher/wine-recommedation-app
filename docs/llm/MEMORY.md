# LLM Knowledge Base Index

This is the master index for the wine-recommendation-app LLM knowledge base. Point a future LLM to this index to understand the structure and find relevant documentation.

## Core Documentation

- [Architecture Overview](architecture.md) — Stack, module map, data flow, design decisions
- [Knowledge Base Summary](SUMMARY.md) — High-level overview of the docs set
- [Public Interfaces](interfaces.md) — All function signatures grouped by module
- [Domain Glossary](glossary.md) — Wine terms, CellarTracker fields, domain-specific abbreviations
- [Code Conventions](conventions.md) — Error handling, naming patterns, preferred libraries, patterns used consistently
- [Context Guide](context-guide.md) — Maps task types to which docs to inject
- [Improvement Backlog](improvement-backlog.md) — Prioritized list of known issues with file:line references and recommended fixes

## Module Documentation

### Backend Python Modules

**App composition & infrastructure**
- [main.py](modules/main.md) — Composition root: env bootstrap, logging, middleware, router includes
- [bootstrap.py](modules/bootstrap.md) — Loads .env; exposes ANTHROPIC_API_KEY/MODEL, MAX_UPLOAD_BYTES, JWT_SECRET/ALGORITHM/EXPIRY_DAYS, APP_BASE_URL, PROFILES_DIR, ORPHAN_PROFILE_ID
- [auth.py](modules/auth.md) — Password hashing (bcrypt + SHA-256 prehash) + JWT signing/decoding utilities (FastAPI-free)
- [dependencies.py](modules/dependencies.md) — FastAPI deps: get_current_user, get_current_profile
- [middleware.py](modules/middleware.md) — Request-logging middleware + exception handlers
- [logging_setup.py](modules/logging_setup.md) — Configures the `sommelier` logger tree
- [logging_utils.py](modules/logging_utils.md) — JSONL recommendation-event telemetry logger (`logs/recommendations.jsonl`)
- [rate_limit.py](modules/rate_limit.md) — IP-based 10-req/60s limiter for /recommend
- [cache.py](modules/cache.md) — SQLite: users/profiles/flights + global response/parse cache + reset tokens + legacy migration

**LLM access**
- [llm_client.py](modules/llm_client.md) — `call_claude` telemetry wrapper (Anthropic SDK) with retry + cost logging
- [retry_utils.py](modules/retry_utils.md) — `call_with_retry` exponential-backoff helper for Anthropic calls
- [recommender.py](modules/recommender.md) — Claude recommendation calls (tool use), output schema, bar blending, validation
- [prompt.py](modules/prompt.md) — System prompt construction, schema definition, tasting-note library / stretch slot
- [parser.py](modules/parser.md) — PDF/text/image dispatch, Claude Haiku vision extraction

**Profiles, palate & retrieval**
- [profile.py](modules/profile.md) — CellarTracker parsing, taste profile building, Claude synthesis/enrichment
- [seed_profile.py](modules/seed_profile.md) — Seed-bottle onboarding; Claude inference of a starter palate
- [palate_stats.py](modules/palate_stats.md) — Pre-LLM statistical palate analysis (frequency, style signals, aspirational skew)
- [retrieval.py](modules/retrieval.md) — Retrieval-augmented pre-filtering; tiered profile-signal ranking (no API call)
- [synonyms.py](modules/synonyms.md) — Grape/region synonym + sub-appellation expansion for retrieval
- [insights.py](modules/insights.md) — Palate drift suggestion engine (statistical flight analysis, no LLM call)
- [scorer.py](modules/scorer.md) — 4-dimension recommendation quality scorer; `ScoringResult` dataclass
- [inventory.py](modules/inventory.md) — Cellar loading/saving, relevance filtering
- [cellar_terms.py](modules/cellar_terms.md) — Frequency-ranked cellar terms + character phrase
- [meal_parser.py](modules/meal_parser.md) — Meal description parsing, MealProfile dataclass, pairing hints
- [wine_reviews.py](modules/wine_reviews.md) — Critic-review reference dataset seeding + lookup/enrichment
- [models.py](modules/models.md) — Pydantic schemas (incl. User/Profile/auth models), camelCase JSON mapping
- [test_fixtures.py](modules/test_fixtures.md) — Canned `RecommendationResponse` fixtures used when `TEST_MODE=true` short-circuits `/recommend`

**Routes (`backend/routes/`)**
- [routes/auth.py](modules/routes_auth.md) — /auth/register, /auth/login, /auth/me, /auth/forgot-password, /auth/reset-password
- [routes/profiles.py](modules/routes_profiles.md) — /profiles CRUD (list/create/rename/delete/set-default)
- [routes/profile.py](modules/routes_profile.md) — /upload-profile, /seed-profile, /profile, /profile/revert, /profile-summary
- [routes/inventory.py](modules/routes_inventory.md) — /upload-inventory, /inventory
- [routes/recommend.py](modules/routes_recommend.md) — /recommend pipeline
- [routes/history.py](modules/history.md) — /history, /history/{id} feedback (profile-scoped flights)
- [routes/insights.py](modules/routes_insights.md) — /profile/insights drift suggestions
- [routes/debug.py](modules/routes_debug.md) — Diagnostics endpoints (health, status, config, logs, cache, stats)

### Frontend (Generated SDK)

- `frontend/src/client/sdk.gen.ts` — Auto-generated from OpenAPI spec. Don't edit.
- `frontend/src/client/types.gen.ts` — Authoritative type definitions (auto-generated).

## How to Use This Index

**For a specific task:**
1. Go to [context-guide.md](context-guide.md)
2. Find your task type
3. It tells you which files to read first
4. Cross-reference as needed with glossary, interfaces, or module files

**For understanding the system:**
1. Start with [architecture.md](architecture.md) for the big picture
2. Read [glossary.md](glossary.md) to understand domain terms
3. Dive into specific [modules/](modules/) as needed

**For implementing a feature:**
1. Read relevant [modules/](modules/) for responsibility + gotchas
2. Check [interfaces.md](interfaces.md) for function signatures
3. Review [conventions.md](conventions.md) for patterns to follow
4. Use [context-guide.md](context-guide.md) for what to inject into LLM context

## Document Statistics

- **Total files**: 43 (8 core docs — this index, summary, architecture, interfaces, glossary, conventions, context-guide, backlog — and 35 module docs under `modules/`)
- **Estimated total tokens**: ~7,500 (manageable in most LLM contexts)
- **Typical focused task**: 1,500–2,000 tokens (architecture + glossary + 2–3 modules)

## Key Design Principles (Quick Summary)

1. **Authenticated**: JWT bearer tokens; per-user persistence keyed by profile_id.
2. **Fail loudly**: Parse errors, LLM errors, validation failures all surface to user.
3. **Schema-driven**: Pydantic models are contracts; validation at boundaries.
4. **Portfolio-legible**: Code prioritizes readability; minimal abstractions.
5. **CamelCase bridge**: All Pydantic models use `alias_generator=to_camel` for JSON ↔ Python.

## Technology Stack (One-Line Summary)

**Backend**: FastAPI + Pydantic v2 + Anthropic Claude API + passlib + PyJWT + SQLite + PyMuPDF (PDF) + pytesseract/PIL (OCR)
**Frontend**: React 19 + TypeScript + Tailwind CSS v4 + Vite + @hey-api/openapi-ts (SDK generation)

## Common Tasks & Estimated Tokens

| Task | Include | Est. Tokens |
|---|---|---|
| Fix recommender.py bug | glossary + conventions + modules/recommender + interfaces | 1,200 |
| Add new endpoint | conventions + modules/main + interfaces (models) | 1,500 |
| Improve taste profile inference | glossary + modules/profile + modules/inventory | 1,000 |
| Debug recommendation output | architecture + modules/recommender + modules/prompt + glossary | 1,600 |
| Analyse recommendation quality | architecture + interfaces (scorer/logging_utils) + modules/main | 1,200 |
| Work from improvement backlog | improvement-backlog.md + relevant modules | Variable |
| Add OCR support | modules/parser + conventions | 600 |
| Optimize cache | modules/cache + modules/main | 800 |
| Review PR | conventions + relevant modules | Variable |

## Known Limitations & TODOs

- **OCR**: Implemented via pytesseract + PIL (greyscale + sharpen pre-processing); requires Tesseract system binary; gracefully degrades if missing
- **Image vision**: Base64 image IS passed to Anthropic Haiku for vision extraction; tested via integration path (no isolated unit tests for Haiku calls)
- **Cache TTL**: No auto-expiry via API; entries purged at startup + lazily on read (7-day TTL)
- **Testing**: pytest suite with 27 tests covering scorer edge cases, meal parser synonym normalisation, text extraction, and OpenAPI schema sync (v2); no tests for PDF/image paths or LLM-dependent routes (routes that call Anthropic API)
- **Accent folding**: Only handles Latin wine regions; fails on Cyrillic/CJK

See [conventions.md](conventions.md#ambiguities--gotchas) for more.

## Maintenance Notes

This knowledge base is a snapshot of the codebase at a specific point in time. Before using it for a task:

1. **Verify module structure hasn't changed**: Quick skim of the module to ensure it still matches its .md file
2. **Check for new modules**: If new .py files added, create corresponding .md in [modules/](modules/)
3. **Update glossary**: If new domain terms introduced, add them to [glossary.md](glossary.md)
4. **Verify conventions still held**: Spot-check a few functions to ensure patterns match [conventions.md](conventions.md)

The [context-guide.md](context-guide.md) "Ambiguities" section lists things to watch for across all tasks.
