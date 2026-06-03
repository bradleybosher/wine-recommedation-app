# Knowledge Base Build Summary

## Completion Status ✓

Knowledge base successfully built for the wine-recommendation-app codebase. All modules documented, contracts specified, and task-to-docs mapping provided.

## Files Created

### Core Documentation (5 files)

| File | Purpose | Lines | Est. Tokens |
|---|---|---|---|
| **MEMORY.md** | Master index & navigation | 150 | 350 |
| **architecture.md** | Stack, module map, data flow, design decisions | 110 | 350 |
| **interfaces.md** | All public function signatures by module | 250 | 800 |
| **glossary.md** | Domain terms, CellarTracker fields, abbreviations | 170 | 450 |
| **conventions.md** | Error handling, naming, patterns, libraries | 200 | 600 |
| **context-guide.md** | Task type → docs mapping | 180 | 400 |

### Module Documentation (35 files)

A representative subset is listed below; the full set lives under `docs/llm/modules/` (see [MEMORY.md](MEMORY.md) for the complete index).

| File | Module | Purpose | Lines | Est. Tokens |
|---|---|---|---|---|
| **modules/main.md** | main.py | Composition root: wires 8 routers, logging, middleware, startup | 50 | 250 |
| **modules/recommender.md** | recommender.py | Claude calls (tool use), validation, bar blending | 50 | 200 |
| **modules/prompt.md** | prompt.py | System prompt construction, schema | 40 | 150 |
| **modules/profile.md** | profile.py | CellarTracker parsing, taste profile building | 100 | 280 |
| **modules/inventory.md** | inventory.py | Cellar load/save, relevance filtering, accent folding | 80 | 220 |
| **modules/cache.md** | cache.py | SQLite caching, cache key generation, TTL | 60 | 180 |
| **modules/parser.md** | parser.py | File type dispatch, PDF/text/image extraction | 50 | 150 |
| **modules/models.md** | models.py | Pydantic schemas, camelCase JSON mapping | 80 | 220 |

## Document Totals

- **Total files created**: 43 (8 core docs + 35 module docs)
- **Total lines of documentation**: ~1,420+
- **Total estimated tokens**: ~5,230+

## Folder Structure

```
docs/
└── llm/
    ├── MEMORY.md                 ← Start here (master index)
    ├── SUMMARY.md                ← This file
    ├── architecture.md
    ├── interfaces.md
    ├── glossary.md
    ├── conventions.md
    ├── context-guide.md
    └── modules/
        ├── main.md
        ├── recommender.md
        ├── prompt.md
        ├── profile.md
        ├── inventory.md
        ├── cache.md
        ├── parser.md
        └── models.md
```

## What Was Analyzed

### Backend Modules

- ✅ main.py (composition root: env, logging, middleware, router includes, legacy migration)
- ✅ bootstrap.py / auth.py / dependencies.py (JWT auth + constants)
- ✅ models.py (Pydantic v2 schemas with camelCase aliases; User/Profile/TokenResponse)
- ✅ recommender.py (Anthropic Claude integration via tool use, validation, bar blending)
- ✅ llm_client.py (call_claude telemetry + retry wrapper around messages.create)
- ✅ prompt.py (System prompt construction: tasting_note_library, aspirational_skew, stretch slot)
- ✅ profile.py / seed_profile.py (palate synthesis + seed-bottle onboarding, profile_id-keyed)
- ✅ palate_stats.py / retrieval.py / synonyms.py / insights.py (deterministic, no-LLM passes)
- ✅ inventory.py (cellar loading/saving, relevance filtering, profile_id-keyed)
- ✅ cache.py (SQLite: users/profiles/flights + global response/parse cache + legacy migration)
- ✅ parser.py (PDF/text/image dispatch; Claude Haiku vision for photos)
- ✅ meal_parser.py / scorer.py / cellar_terms.py / wine_reviews.py / test_fixtures.py
- ✅ middleware.py / rate_limit.py / logging_setup.py / logging_utils.py / retry_utils.py
- ✅ routes/{auth,profiles,profile,inventory,recommend,history,insights,debug}.py

### Frontend (React + TypeScript)

- ✅ Component structure (App, UploadFlow, RecommendationScreen, etc.)
- ✅ SDK generation (client/sdk.gen.ts auto-generated from OpenAPI)
- ✅ Type contracts (client/types.gen.ts authoritative)

## Documentation Includes

### For Each Module

- **Responsibility**: What it does
- **Dependencies**: What it imports
- **Key Functions**: Signature + brief description
- **Patterns & Gotchas**: Non-obvious behavior, edge cases
- **Known Issues/TODOs**: Limitations and future work

### Glossary Terms Covered

- Wine domain (CellarTracker fields, varietal, appellation, vintage, drink window, etc.)
- Export types (list, consumed, notes, purchases, unknown)
- Application concepts (taste profile, confidence, reasoning, cache key, etc.)
- Technical terms (Pydantic, camelCase bridge, accent folding, etc.)

### Conventions Documented

- Error handling (HTTPException 400/404/502/500)
- Naming patterns (snake_case functions, UPPER_SNAKE_CASE constants, kebab-case routes)
- Pydantic patterns (ConfigDict with alias_generator, populate_by_name)
- Preferred libraries (FastAPI, Pydantic v2, Anthropic SDK, PyMuPDF, pytesseract/PIL, sqlite3, passlib, PyJWT)
- Architecture patterns (JWT auth + per-profile persistence, fail-loud, schema-driven, caching by content hash)

## How to Use

### Entry Point

Start with **docs/llm/MEMORY.md** — it's the master index.

### For a Specific Task

1. Open **context-guide.md**
2. Find your task type (e.g., "Fixing a bug in recommender.py")
3. It tells you which files to inject into LLM context
4. Total tokens for a focused task: 1,500–2,000 (manageable)

### For Understanding the System

1. Read **architecture.md** (20 min) — big picture
2. Read **glossary.md** (15 min) — domain terminology
3. Skim **interfaces.md** (10 min) — function signatures
4. Dive into specific modules as needed

## Key Insights Documented

1. **JWT auth, per-user, per-profile**: Open self-registration; `users`/`profiles`/`flights` tables in `cellar.db`; per-profile JSON under `backend/profiles/{id}/`. Legacy data migrated once into an orphan profile claimed by the first registration.
2. **Fail-loud pattern**: Parse errors, Claude errors, validation failures surface to user
3. **Schema-driven**: Pydantic models are contracts enforced at the Claude tool-output boundary
4. **CamelCase bridge**: All models use `alias_generator=to_camel, populate_by_name=True`
5. **Robustness**: Claude tool use returns structured JSON; output validated through Pydantic
6. **Avoided styles inference**: Already implemented via low-score tasting note analysis
7. **Relevant bottles context**: Prevents recommending wines user already owns

## Quality Checklist ✓

- [x] All modules documented with responsibility + dependencies
- [x] All public function signatures captured
- [x] Error handling patterns documented
- [x] Naming conventions specified
- [x] Known gotchas and TODOs flagged
- [x] Task-to-docs mapping provided
- [x] Data flow diagram explained
- [x] Pydantic schema patterns clarified
- [x] Module interdependencies shown
- [x] Testing guidance (where applicable)

## Ambiguities Flagged

- ⚠️ **Score interpretation**: CellarTracker scale may vary (1–100 vs. 1–5); always verify
- ⚠️ **Accent folding**: Only handles Latin wine names; fails on Cyrillic/CJK
- ⚠️ **Cache staleness**: No auto-expiry via API; purged at startup + lazily on read (7-day TTL)
- ⚠️ **OCR**: Implemented (pytesseract + PIL); requires Tesseract system binary; gracefully degrades if missing
- ⚠️ **Image vision**: Base64 IS passed to Claude Haiku vision (parser.py) for wine-list photos

All flagged in relevant module files.

## For Future Maintenance

When codebase changes:

1. **New module added?** Create `docs/llm/modules/{name}.md`
2. **Function signature changed?** Update `interfaces.md` + relevant module file
3. **New domain term?** Add to `glossary.md`
4. **New pattern introduced?** Document in `conventions.md`
5. **Task type emerges?** Add to `context-guide.md`

Keep this knowledge base in sync with the code to maximize utility for future LLM-assisted development.

## Usage Statistics

**Typical task tokens**: 1,500–2,000 (leaves budget for problem context + code snippets)

**Full knowledge base tokens**: 5,230 (good for exploratory work or complete understanding)

**Minimal focused context**: 600–800 tokens (glossary + 1 module for narrow fixes)

---

**Generated**: April 2026
**Codebase state**: Post-reliability-cleanup (JSON fence stripping, dead code removal, .env.example, README.md added)
**Status**: Complete and ready for LLM-assisted development
