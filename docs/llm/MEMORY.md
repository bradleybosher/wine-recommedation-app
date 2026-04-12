# LLM Knowledge Base Index

This is the master index for the wine-recommendation-app LLM knowledge base. Point a future LLM to this index to understand the structure and find relevant documentation.

## Core Documentation

- [Architecture Overview](architecture.md) — Stack, module map, data flow, design decisions
- [Public Interfaces](interfaces.md) — All function signatures grouped by module
- [Domain Glossary](glossary.md) — Wine terms, CellarTracker fields, domain-specific abbreviations
- [Code Conventions](conventions.md) — Error handling, naming patterns, preferred libraries, patterns used consistently
- [Context Guide](context-guide.md) — Maps task types to which docs to inject

## Module Documentation

### Backend Python Modules

- [main.py](modules/main.md) — FastAPI app, routes, logging, utilities
- [recommender.py](modules/recommender.md) — LLM calls, structured output schema, retry logic, JSON parsing, validation
- [prompt.py](modules/prompt.md) — System prompt construction, schema definition, OWNER_PROFILE constant
- [profile.py](modules/profile.md) — CellarTracker parsing, taste profile building, Ollama enrichment
- [meal_parser.py](modules/meal_parser.md) — Meal description parsing, MealProfile dataclass, pairing hints
- [inventory.py](modules/inventory.md) — Cellar loading/saving, relevance filtering
- [cache.py](modules/cache.md) — SQLite response caching
- [parser.py](modules/parser.md) — PDF/text/image dispatch, extraction
- [models.py](modules/models.md) — Pydantic schemas, camelCase JSON mapping
- scorer.py — 4-dimension recommendation quality scorer; `ScoringResult` dataclass; see interfaces.md
- logging_utils.py — JSONL event logger to `logs/recommendations.jsonl`; see interfaces.md

### Frontend (Generated SDK)

- `frontend/src/client/sdk.gen.ts` — Auto-generated from OpenAPI spec. Don't edit.
- `frontend/src/client/types.gen.ts` — Authoritative type definitions (auto-generated).

### Debug Routes

- `backend/routes/debug.py` — Diagnostics endpoints (health, status, logs, cache). See [conventions.md](conventions.md) for HTTP error codes.

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

- **Total files**: 14 (4 core + 9 modules + 1 index) — scorer.py and logging_utils.py documented inline in interfaces.md
- **Estimated total tokens**: ~5,800 (manageable in most LLM contexts)
- **Typical focused task**: 1,500–2,000 tokens (architecture + glossary + 2–3 modules)

## Key Design Principles (Quick Summary)

1. **Stateless**: No user accounts; JSON files + SQLite cache only.
2. **Fail loudly**: Parse errors, LLM errors, validation failures all surface to user.
3. **Schema-driven**: Pydantic models are contracts; validation at boundaries.
4. **Portfolio-legible**: Code prioritizes readability; minimal abstractions.
5. **CamelCase bridge**: All Pydantic models use `alias_generator=to_camel` for JSON ↔ Python.

## Technology Stack (One-Line Summary)

**Backend**: FastAPI + Pydantic v2 + Ollama (local LLM, used twice: profile enrichment + recommendation) + SQLite (cache) + PyMuPDF (PDF) + pytesseract/PIL (OCR)
**Frontend**: React 19 + TypeScript + Tailwind CSS v4 + Vite + @hey-api/openapi-ts (SDK generation)

## Common Tasks & Estimated Tokens

| Task | Include | Est. Tokens |
|---|---|---|
| Fix recommender.py bug | glossary + conventions + modules/recommender + interfaces | 1,200 |
| Add new endpoint | conventions + modules/main + interfaces (models) | 1,500 |
| Improve taste profile inference | glossary + modules/profile + modules/inventory | 1,000 |
| Debug recommendation output | architecture + modules/recommender + modules/prompt + glossary | 1,600 |
| Analyse recommendation quality | architecture + interfaces (scorer/logging_utils) + modules/main | 1,200 |
| Add OCR support | modules/parser + conventions | 600 |
| Optimize cache | modules/cache + modules/main | 800 |
| Review PR | conventions + relevant modules | Variable |

## Known Limitations & TODOs

- **OCR**: Implemented via pytesseract + PIL (greyscale + sharpen pre-processing); requires Tesseract system binary; gracefully degrades if missing
- **Image vision**: Base64 image IS passed to Ollama for vision-capable models; not formally tested with a vision model
- **Cache TTL**: No auto-expiry via API; entries purged at startup + lazily on read (7-day TTL)
- **Testing**: No pytest suite (manual testing only, v1)
- **Accent folding**: Only handles Latin wine regions; fails on Cyrillic/CJK

See [conventions.md](conventions.md#ambiguities--gotchas) for more.

## Maintenance Notes

This knowledge base is a snapshot of the codebase at a specific point in time. Before using it for a task:

1. **Verify module structure hasn't changed**: Quick skim of the module to ensure it still matches its .md file
2. **Check for new modules**: If new .py files added, create corresponding .md in [modules/](modules/)
3. **Update glossary**: If new domain terms introduced, add them to [glossary.md](glossary.md)
4. **Verify conventions still held**: Spot-check a few functions to ensure patterns match [conventions.md](conventions.md)

The [context-guide.md](context-guide.md) "Ambiguities" section lists things to watch for across all tasks.
