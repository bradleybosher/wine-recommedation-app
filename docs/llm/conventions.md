# Code Conventions & Patterns

## Error Handling

### Backend (Python)

**HTTP Exceptions**: FastAPI endpoints raise `HTTPException(status_code, detail)` for user-facing errors.
- 400: Invalid input (bad request)
- 404: Not found (missing inventory/profile)
- 502: LLM provider error (Ollama down, JSON parse fail, schema mismatch)
- 500: Unhandled exception (logged, generic error response)

**Fail Loudly**: Parser returns error messages (strings) rather than None. Recommender logs detailed error context before raising HTTPException(502).

**Logging**: `logger = logging.getLogger("sommelier.<module>")` in each module. Level: INFO. File + stderr output. Format: `timestamp level message`.

**Exceptions in recommender.py**:
```python
# JSON parse error → HTTPException(502) with "invalid JSON" detail
# Pydantic validation error → HTTPException(502) with "schema mismatch" detail
# Ollama 404 (no /api/chat) → fallback to /api/generate
# Other HTTP errors → re-raise HTTPException
# Other exceptions → HTTPException(502) with error type name
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

**Environment Variables**: UPPER_SNAKE_CASE (e.g., `OLLAMA_URL`, `OLLAMA_MODEL`, `VITE_SHOW_DEBUG`).

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
- LLM: fall back from /api/chat to /api/generate if 404.

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

**Ollama**: Local LLM inference. No API keys, no cloud dependency, fast iteration.

**PyMuPDF (fitz)**: Fast PDF text extraction. Better than PyPDF2 for text recovery.

**sqlite3**: Built-in. Perfect for stateless caching (no external DB needed). Single-file, portable.

**httpx**: Modern async HTTP client. Replaces requests; better timeout handling.

**@hey-api/openapi-ts**: Generates TypeScript SDK directly from OpenAPI spec. Stays in sync with backend changes (no manual type definitions).

**React 19**: Latest, no breaking changes. TypeScript strict mode for frontend contracts.

**Tailwind CSS v4**: Utility classes with `@theme {}` design tokens in `src/index.css`. No separate CSS files. Glass tokens (`--blur-glass`, `--color-glass-surface`, `--color-glass-border`, `--color-glass-surface-hover`) and wine palette tokens (`--color-wine-burgundy`, `--color-wine-merlot`, etc.) are registered here and consumed as Tailwind utilities throughout the app.

**lucide-react**: Icon library. `strokeWidth={1.5}` on all icons for a light, airy aesthetic consistent with the glass UI. Do not use inline SVG paths for new UI action icons. Exception: `WineBottleIcon` (`src/components/ui/WineBottleIcon.tsx`) is a custom illustrative component (wine bottle silhouettes — shapes that don't exist in lucide-react) and uses inline SVG intentionally.

**Vite**: Instant dev reload, minimal config.

## Frontend Styling Conventions

### Glassmorphism Design System

The frontend uses a Tailwind v4 glassmorphism design system. All rules below are **non-negotiable** — breaking them visually fragments the UI.

**Design tokens** (defined in `src/index.css` `@theme {}`):

| Token | Value | Tailwind utility |
|---|---|---|
| `--blur-glass` | 12px | `backdrop-blur-glass` |
| `--color-glass-surface` | rgba(255,255,255,0.10) | `bg-glass-surface` |
| `--color-glass-surface-hover` | rgba(255,255,255,0.16) | `bg-glass-surface-hover` |
| `--color-glass-border` | rgba(255,255,255,0.20) | `border-glass-border` |
| `--color-wine-burgundy` | #6B1A2B | `bg-wine-burgundy`, `text-wine-burgundy` |
| `--color-wine-merlot` | #8B2546 | `bg-wine-merlot` |
| `--color-wine-purple-deep` | #2D1B4E | (background base) |
| `--color-wine-purple-mid` | #4A2370 | (blob, tag backgrounds) |
| `--color-wine-amber` | #C8860A | `bg-wine-amber`, `text-wine-amber` |
| `--color-wine-gold` | #D4A017 | `text-wine-gold` (success states, high confidence) |
| `--color-wine-rose` | #C4637A | `text-wine-rose` (accents, medium confidence) |

**Glass primitives** (in `frontend/src/components/ui/`):

- `VibrantBackground` — wraps the entire app. Provides the animated mesh gradient background. Only ever instantiated once in `App.tsx`. Do not nest inside another `VibrantBackground`.
- `GlassCard` — frosted glass card surface. Use for **all** card containers. Accepts `className` prop for padding/margin/width overrides. Do not add `bg-white` or `bg-gray-*` card containers.
- `WineBottleIcon` — outline SVG wine bottle illustration. Props: `style: WineStyle` (`'bordeaux' | 'burgundy' | 'sparkling' | 'generic'`), `className?`. Export `getWineStyle(wineName, region?)` infers style via keyword regex. Used in `RecommendationResults` beside each rank badge. This is a custom illustration — not a lucide-react icon.

**Text on glass surfaces:**
- Headings: `text-white`
- Body: `text-white/80` or `text-white/70`
- Helper text / placeholders: `text-white/50`
- Minimum readable opacity: `text-white/70` (never lower for important content)
- Never use `text-gray-*` inside a `GlassCard` — it renders illegible on the dark background

**Buttons:**
- Primary: `bg-wine-burgundy hover:bg-wine-merlot border border-wine-rose/30 text-white`
- Disabled: `bg-white/10 text-white/30 cursor-not-allowed border border-white/10`
- Ghost/secondary: `border border-white/20 text-white/70 hover:bg-white/10`

**Icons:** Always use `lucide-react`. Set `strokeWidth={1.5}` on every icon. Do not introduce inline SVG paths for UI action icons. Exception: `WineBottleIcon` (`src/components/ui/WineBottleIcon.tsx`) uses custom inline SVG for illustrative bottle silhouettes — this is deliberate and not a pattern to generalise.

---

## Architecture Decisions

**Stateless by design**: No user accounts, no session state. Simplifies deployment, allows easy scaling.

**Single-file inventory/profile**: JSON files (inventory.json, profile_data.json) in backend dir. No schema migrations, easy debugging.

**Response caching by content hash**: Prevents redundant LLM calls for identical wine_list + meal combinations. Helpful for A/B testing, user exploration.

**Markdown fence stripping**: LLMs frequently wrap JSON despite instructions. Strip before parsing to avoid silent 502s.

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

## Testing (v1 out of scope)

No pytest suite yet. Manual integration testing:
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

3. **Ollama fallback**: If `/api/chat` returns 404, code falls back to `/api/generate` with slightly different payload structure. Both return `{"response": "..."}` or `{"message": {"content": "..."}}`. Parsing handles both.

4. **Profile source ambiguity**: `profile_source` field is informational only. No logic branches on it. Useful for analytics/UI hints.

5. **Cache TTL**: Inventory has `stale` flag (age > 168 hours) but no auto-refresh. User must manually re-upload to bust cache.

6. **Quantity filtering**: Bottles with Quantity ≤ 0 are silently dropped during parse. Quantity is a string in CT export; parsed with `float()`.

7. **LLM temperature/randomness**: Ollama defaults not documented. System prompt doesn't specify. Recommendation may vary across calls. Not cached unless content-identical.
