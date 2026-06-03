# Code Conventions & Patterns

## Error Handling

### Backend (Python)

**HTTP Exceptions**: FastAPI endpoints raise `HTTPException(status_code, detail)` for user-facing errors.
- 400: Invalid input (bad request)
- 404: Not found (missing inventory/profile)
- 502: LLM provider error (Anthropic API error, or schema validation failed after all retries)
- 500: Unhandled exception (logged, generic error response)

**Fail Loudly**: Parser returns error messages (strings) rather than None. Recommender logs detailed error context before raising HTTPException(502).

**Logging**: `logger = logging.getLogger("sommelier.<module>")` in each module. Level: INFO. File + stderr output. Format: `timestamp level message`.

**Exceptions in recommender.py**:
```python
# Claude returns structured output via tool use — no JSON-string parsing needed.
# Pydantic validation error → ValueError (retriable; up to _MAX_ATTEMPTS=3 attempts)
# anthropic.APIError → HTTPException(502) "API error" detail
# All attempts exhausted → HTTPException(502) "failed after N attempts"
# Transient errors (APIConnectionError, RateLimitError) are retried inside
#   call_claude() via retry_utils.call_with_retry before surfacing.
```

**Exceptions in parser.py**:
```python
# PDF extraction failure → return error message string (logged as warning)
# Encoding fallback → try UTF-8, cp1252, latin-1, lossy replacement
# File type unknown → attempt as text, return error if fails
```

**Exceptions in profile.py**:
```python
# File I/O error → return {} (empty dict, graceful degradation)
# JSON parse error → return {} (same)
# CSV parsing → rows filtered; invalid rows skipped silently
```

## Naming Patterns

**Functions**: snake_case. Private functions prefixed with `_` (e.g., `_fold_for_match`, `_infer_avoided_styles`).

**Variables**: snake_case. Single-letter vars avoided (loop vars okay: `for k, v in ...`).

**Constants**: UPPER_SNAKE_CASE (e.g., `CACHE_PATH`, `CACHE_TTL`, `DB_PATH`, `PROFILE_DATA_PATH`).

**Classes**: PascalCase. Pydantic models use same pattern.

**API Routes**: Kebab-case URLs (e.g., `/upload-inventory`, `/profile-summary`, `/cache/stats`).

**Environment Variables**: UPPER_SNAKE_CASE (e.g., `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`, `JWT_SECRET`, `VITE_SHOW_DEBUG`).

**Pydantic Fields**: snake_case in Python, auto-aliased to camelCase in JSON (via `alias_generator=to_camel`).

**CellarTracker Fields**: Preserve exact PascalCase from CT export (Varietal, Appellation, etc.).

## Patterns Used Consistently

### Pydantic Configuration
All models use:
```python
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

class MyModel(BaseModel):
    field_name: type
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )
```
Allows both snake_case (Python) and camelCase (JSON) field names.

### Optional Handling
```python
def _value_or_empty(v: object) -> str:
    return str(v or "").strip()
```
Pattern used to safely extract text from dict fields that may be None or missing.

### Graceful Fallbacks
- Encoding: try multiple, fall back to lossy replacement.
- File loading: return empty dict or list if missing/corrupt rather than raising.
- LLM: `call_claude()` retries transient Anthropic errors (connection resets, rate limits) up to 3 times with exponential backoff (`retry_utils.call_with_retry`); recommender.py additionally retries Pydantic schema-validation failures.

### Counter Frequency Analysis
```python
from collections import Counter
counts: Counter[str] = Counter()
# accumulate...
top_n = [word for word, _ in counts.most_common(n)]
```
Used in profile.py and main.py for term frequency analysis.

### Accent Folding for Matching
```python
import unicodedata
decomposed = unicodedata.normalize("NFD", text.casefold())
return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
```
Pattern in inventory.py to normalize "Côte-Rôtie" → "cote-rotie" for fuzzy matching.

### Context Managers
```python
with _conn() as c:
    c.execute(...)
```
SQLite connections always use context managers for safety.

### Type Hints
All functions include type hints (parameter types + return type). Use `Optional[T]` for nullable, `list[dict]` for collections.

## Preferred Libraries & Why

**FastAPI**: Async-first, auto-OpenAPI spec generation (enables SDK generation), Pydantic integration, clean decorator-based routing.

**Pydantic v2**: Validates API contracts. alias_generator simplifies camelCase bridge between Python and JavaScript.

**Anthropic Claude API** (`anthropic` SDK): Cloud LLM with native tool use for structured output. All calls go through `llm_client.call_claude()` (telemetry + retry). Recommendation/synthesis use `ANTHROPIC_MODEL` (default claude-sonnet-4-6); image/OCR vision parsing uses Claude Haiku (`ANTHROPIC_VISION_MODEL`). Requires `ANTHROPIC_API_KEY`.

**PyMuPDF (fitz)**: Fast PDF text extraction. Better than PyPDF2 for text recovery.

**sqlite3**: Built-in. Single-file, portable store for users/profiles/flights plus the content-addressed response/parse cache (no external DB needed).

**httpx**: Modern async HTTP client. Replaces requests; better timeout handling.

**@hey-api/openapi-ts**: Generates TypeScript SDK directly from OpenAPI spec. Stays in sync with backend changes (no manual type definitions).

**React 19**: Latest, no breaking changes. TypeScript strict mode for frontend contracts.

**Tailwind CSS v4**: Used sparingly — only for stateful helper utilities (e.g. `animate-spin`, `hidden`). All component styling uses inline `CSSProperties` objects with named tokens imported from `@/design/tokens` (INK, INK_SOFT, PAPER, OXBLOOD, RULE). No hardcoded hex/rgba; no `text-white`, `text-gray-*`, or `bg-wine-*` classes.

**lucide-react**: Icon library. `strokeWidth={1.5}` on all icons for a light editorial aesthetic. Do not use inline SVG paths for new UI action icons.

**Vite**: Instant dev reload, minimal config.

## Frontend Styling Conventions

### Vinothèque Editorial Design System

The frontend uses an old-world editorial design system ("Vinothèque") — paper, ink, and hairline rules, no glassmorphism. All rules below are **non-negotiable** (see CLAUDE.md "Frontend & Styling" for the authoritative list).

**Design tokens** (named exports from `@/design/tokens` — import them, never hardcode hex/rgba):

- `INK`, `INK_SOFT` — primary/secondary text.
- `PAPER` — page/surface background.
- `OXBLOOD` — accent (high-emphasis marks, primary actions).
- `RULE` — hairline rule colour (1px solid borders).

**Layout primitive:** `<PaperFrame>` is the page wrapper (not a glass card, not a vibrant background). No glassmorphism, no rounded corners, no drop shadows beyond inset paper.

**Typography:** Cormorant Garamond (display) + EB Garamond (body), referenced via inline `fontFamily` strings.

**Style delivery:** Inline `CSSProperties` objects for all component styling. Tailwind utility classes only for stateful helpers (e.g. `animate-spin`, `hidden`). No `text-white`, `text-gray-*`, or `bg-wine-*` classes.

**Icons:** Always use `lucide-react`, `strokeWidth={1.5}`. No inline SVGs.

**Decoration:** Hairline rules (1px solid `RULE`), no rounded corners, no drop shadows.

---

## Architecture Decisions

**JWT auth, per-profile state**: Open self-registration (single-tenant learning project). JWT bearer tokens (HS256) on every non-auth endpoint, plus an `X-Profile-Id` header selecting the active named palate. Users/profiles/flights live in `cellar.db`; per-profile JSON lives under `backend/profiles/{profile_id}/`.

**Per-profile inventory/profile JSON**: `inventory.json` + `profile_data.json` under each `backend/profiles/{profile_id}/` dir. No schema migrations, easy debugging.

**Response caching by content hash**: Prevents redundant LLM calls for identical wine_list + meal + profile combinations. Helpful for A/B testing, user exploration.

**Tool use, no JSON repair**: Claude returns a pre-parsed dict via tool use (`tool_block.input`), so there is no markdown-fence stripping or brace repair — validation happens directly against the Pydantic schema.

**Avoid_styles inference from low scores**: Instead of hardcoding, analyze user's own tasting history to infer what they dislike.

**Relevant bottles context window**: Don't just recommend; also note if recommendation is outclassed by user's cellar. Adds confidence and honesty.

## Code Style

**Indentation**: 4 spaces (Python). 2 spaces (TypeScript/React).

**String quotes**: Double quotes (") in Python (per Black convention if used). Single quotes in JavaScript.

**Line length**: ~120 characters. No hard limit; readability first.

**Comments**: Minimal. Code should be self-documenting. Comments for non-obvious logic (e.g., accent folding, score threshold reasoning).

**Imports**: Organize: stdlib, third-party, local. One import per line where possible.

**F-strings**: Prefer f-strings over % or .format().

**Type annotations**: Always on function signatures. Use `Optional[T]` over `T | None` for compatibility.

## Testing

A pytest suite lives under `backend/tests/` (27 tests): `test_scorer.py` (scorer edge cases), `test_meal_parser.py` (synonym normalisation), `test_parser_text.py` (text extraction), and `test_openapi_sync.py` (live schema matches `backend/openapi.json`). LLM-dependent evals live separately under `backend/tests/llm_evals/`. There are no tests for the PDF/image vision paths or for routes that call the Anthropic API.

Run with `pytest backend/tests`. Manual integration check:
1. Upload CellarTracker TSV
2. Upload profile export (optional)
3. Upload wine list PDF
4. Verify recommendation JSON structure and caching

## Logging Patterns

**Request logging (main.py)**:
```python
logger.info(
    "request_start id=%s method=%s path=%s ip=%s",
    request_id,
    request.method,
    request.url.path,
    client_ip,
)
```

**Error context**:
```python
logger.error(f"LLM returned unparseable JSON: {result[:200]}")
logger.exception("recommend_provider_error error=%s", type(exc).__name__)
```

Always include request_id for traceability. Truncate large strings to first 200 chars.

## Ambiguities & Gotchas

1. **Score interpretation**: `_row_max_rating_score()` picks highest score from CScore, PScore, CTScore, MYscore. Assumes higher = better. Verify user is using CT scoring (1–100 scale) not 1–5 scale.

2. **Accent folding**: `_fold_for_match()` works for Latin-based wine names (French, Italian, Spanish). May not work for Cyrillic (Georgian wines) or CJK. Fallback is case-insensitive substring match.

3. **Transient LLM errors**: `llm_client.call_claude()` retries on `anthropic.APIConnectionError` / `anthropic.RateLimitError` (via `retry_utils.call_with_retry`, exponential backoff). Permanent errors (auth, invalid request) surface immediately as `HTTPException(502)`.

4. **Profile source ambiguity**: `profile_source` field is informational only. No logic branches on it. Useful for analytics/UI hints.

5. **Cache TTL**: Inventory has `stale` flag (age > 168 hours) but no auto-refresh. User must manually re-upload to bust cache.

6. **Quantity filtering**: Bottles with Quantity ≤ 0 are silently dropped during parse. Quantity is a string in CT export; parsed with `float()`.

7. **LLM temperature/randomness**: Anthropic API defaults are used (the call doesn't set `temperature`). Recommendations may vary across calls and are reused only when the content-addressed cache key matches exactly.
