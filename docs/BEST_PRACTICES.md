# Best Practices for Claude Code (Wine List Recommender)

This guide tells Claude Code how to write code in this repo. It is the "how to build" layer.
`CLAUDE.md` is the orientation and hard rules. `docs/llm/conventions.md` is the reference.
When those conflict with this guide, `CLAUDE.md` wins.

Read this once at the start of a task. Then follow it without being reminded.

---

## Golden rules (read these every time)

1. Plan before you touch code. State the files you will change and why, then change only those.
2. Pydantic is the contract. Every shape that crosses the API boundary is a Pydantic model.
3. Fail loudly at boundaries, degrade gracefully on disk reads. Never swallow an LLM or HTTP error silently.
4. Frontend never calls the backend by hand. It uses the generated SDK and generated types only.
5. After any Python change to a model or endpoint, stop and ask the user to run `sync_types.bat` before editing the frontend.
6. Update the docs in the same task that changes the code. A change is not done until `docs/llm/` matches it.
7. Keep it portfolio-legible. No abstraction layer that the current complexity does not earn.

---

## Backend: Python and FastAPI

### Models are the contract

Every request body, response body, and structured internal object is a Pydantic v2 model. Do not pass loose dicts across function boundaries that the frontend will eventually see.

Every model uses the camelCase bridge so Python stays snake_case and JSON stays camelCase:

```python
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

class WineRecommendation(BaseModel):
    wine_name: str
    confidence: float
    reasoning: str
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
```

Rules:
- `populate_by_name=True` is not optional. It lets tests and internal code build the model with snake_case.
- Do not hand-write camelCase field names in Python. Let the alias generator do it.
- CellarTracker source fields keep their exact PascalCase (`Varietal`, `Appellation`, `CScore`). Do not "fix" them to snake_case. They are external data, not our schema.

### Endpoints

- Routes are kebab-case: `/upload-inventory`, `/profile-summary`, `/cache/stats`.
- `/recommend` and `/upload-inventory` take `multipart/form-data` (file uploads). The frontend must send `FormData` for these. Keep it that way.
- Keep endpoint functions thin. They orchestrate: load, hash, cache-check, parse, call the model, score, log, cache, return. Heavy logic lives in the module that owns it (`parser.py`, `recommender.py`, `profile.py`, and so on).

### Error handling

Raise `HTTPException` for anything the user needs to see. Use the established status codes:

- 400: bad input
- 404: missing inventory or profile
- 502: LLM provider failure (Ollama down, JSON parse fail, schema mismatch)
- 500: genuinely unhandled, logged with `logger.exception`

Two different failure styles, and they are deliberate:

- At the API boundary and in the LLM path: fail loud. Log the context, then raise. The recommender logs detail before it raises `HTTPException(502)`.
- On disk reads (profile, inventory): degrade gracefully. A missing or corrupt file returns `{}` or `[]`, not an exception. The app should still load with no profile.

Do not invert these. Do not make a missing file crash the app, and do not let a broken LLM response return a fake-success empty recommendation.

### Logging

One logger per module, namespaced:

```python
import logging
logger = logging.getLogger("sommelier.recommender")
```

- Level INFO for normal flow, `logger.exception(...)` inside an except block that handles a real error.
- Always include the request id when you have one.
- Truncate large strings (LLM output, prompts) to about 200 characters in logs. Do not dump a full prompt into the log file.
- Use the structured key=value style already in use: `logger.info("cache_hit key=%s age=%s", key, age)`.

### The LLM call path

This is the part most likely to break, so follow the existing pattern in `recommender.py` exactly.

- Use `httpx` with an explicit timeout. The recommendation call uses 120s, profile enrichment uses 30s. Pick a timeout on purpose, never leave it unbounded.
- Ask for structured output via Ollama's `format` schema. Then still defend against bad output:
  - Strip markdown fences. Models wrap JSON in ```` ```json ```` even when told not to.
  - Parse, then validate into the Pydantic model. A parse failure or a validation failure is a 502, not a crash.
- Keep the fallback chains that already exist:
  - `/api/chat` returns 404, fall back to `/api/generate`.
  - Schema `format` rejected with 400 or 500 (older Ollama), fall back to plain `"json"` format.
  - Read the body as either `message.content` or `response`, since both shapes occur.
- Two-model cloud path (Haiku for OCR and extraction, Sonnet for sommelier reasoning) runs alongside the local Ollama path. When you add to it, keep the same defensive parsing. The model changes, the contract does not.

### Filter the input, do not patch the output

When the model's decision space is polluted, fix the input. The wine-list pre-filter (`filter_wine_list` in `inventory.py`) exists because an unfiltered restaurant list dragged recommendations away from the user's taste profile. The fix was to clean the list before it reached the prompt, not to post-process the model's answer. Follow that instinct: upstream filtering beats downstream patching.

### Caching

- Cache key is a content hash (SHA256) over wine-list bytes, meal, inventory hash, and profile hash. Same inputs, same key, same answer. Do not add wall-clock time or randomness to the key.
- TTL is 7 days (168 hours). Expiry happens at startup (`purge_expired()`) and lazily on read. There is no background job, and we do not want one.
- Any write that changes inventory or profile must bust the cache.

### Rule-based where it is enough

Do not reach for an LLM when a lookup table will do. The meal parser uses rule-based parsing on purpose. Reserve model calls for the reasoning that actually needs them (palate enrichment, recommendation). This keeps cost and latency down and keeps behaviour testable.

### Style

- Type hints on every function signature, parameters and return. Use `Optional[T]`, not `T | None`, for consistency with the existing code.
- snake_case functions and variables, `UPPER_SNAKE_CASE` constants, PascalCase classes.
- Private helpers get a leading underscore: `_fold_for_match`, `_value_or_empty`.
- f-strings over `.format()` or `%`. Double quotes in Python.
- SQLite always through a context manager (`with _conn() as c:`). Never leave a connection open.
- Comments only for non-obvious logic (accent folding, score thresholds). The code should read on its own otherwise.

---

## Frontend: React, TypeScript, JavaScript

### Never hand-roll API calls

- All backend calls go through `frontend/src/client/sdk.gen.ts`. No raw `fetch`, no `axios`.
- All request and response types come from `frontend/src/client/types.gen.ts`. Do not redefine a type locally that already exists there. Do not edit either generated file by hand.

### The sync protocol (do not skip this)

The TypeScript SDK is generated from the backend's OpenAPI spec. They drift the moment you change a Python model or endpoint.

So: after any backend change that touches a Pydantic model or a route, stop. Ask the user to run `sync_types.bat`. Do not start editing frontend code that depends on the new shape until that has run. Editing the frontend against a stale SDK is the most common way this project breaks.

### Glass design system (non-negotiable styling rules)

Breaking these visually fragments the UI, so treat them as hard constraints:

- Card surfaces use `<GlassCard>`. Never `bg-white` or `bg-gray-*` containers.
- The animated background is `<VibrantBackground>`, instantiated once in `App.tsx`. Do not nest it. Do not put a background color on page-level containers. `VibrantBackground` owns the background.
- Icons come from `lucide-react` with `strokeWidth={1.5}` always. No inline SVG for action icons. The one exception is `WineBottleIcon`, a custom illustration that does not exist in lucide.
- Color comes from the wine palette and glass tokens defined in `src/index.css @theme`. No hardcoded hex or rgba.
- Text inside a `GlassCard` is white-based, `text-white/70` at minimum. Never `text-gray-*` on glass.

### Imports and structure

- Use the `@/` alias. No relative `../../` climbing.
- Do not modify `vite.config.ts` or `tsconfig.json` to work around an import. Fix the import.
- Feature components live in `src/`. Reusable primitives live in `src/components/ui/`.

### JS and TS habits

- 2-space indentation, single quotes in JS/TS.
- Keep components reading top to bottom: state, derived values, handlers, render.
- Hold transient UI state in React state (`useState`, `useReducer`). This app is stateless server-side and there are no accounts, so do not invent client-side persistence the backend does not have.
- Handle the loading and error states of every SDK call. The backend fails loud with real status codes, so the UI should show those, not a blank screen.

---

## Cross-cutting workflow

### Running commands (Windows)

- One command per Bash call. Never chain with `&&` or `;`.
- No `cd`. Use absolute paths from the project root, with backslashes in shell commands.
- Run backend tools through the venv Python: `.\backend\.venv\Scripts\python.exe -m <module>`.
- Do not run `ls -R`, `pwd`, or `tree`. Reference files by full path from root.

### Read narrowly

Only open files that are actually involved in the logic you are changing. The `docs/llm/context-guide.md` maps a task type to the exact docs to read first. Use it instead of reading the whole tree. If you spot tech debt while you are in a file, flag it. Do not fix it silently in an unrelated change.

### Documentation update protocol

A task is not finished until the docs match the code. This is mandatory, not a nice-to-have, because doc drift has already bitten this project (a module said OCR was stubbed while the code had implemented it).

For every file you modify:

| Modified file | Update these docs |
|---|---|
| `backend/<module>.py` | `docs/llm/modules/<module>.md` and `docs/llm/interfaces.md` |
| Data flow or module list changed | `CLAUDE.md` (Data Flow and Modules lines) |
| User-facing behaviour changed | `README.md` |

Before you mark anything done, check: do the module doc and `interfaces.md` reflect the current signatures and behaviour, are new constants and data structures documented, is `CLAUDE.md` still accurate, is `README.md` still accurate for a user.

`HUMAN_NOTES.md` is read-only. Use it for current thinking and known bugs. Never edit it.

### Testing

The honest state: there is no pytest suite yet, only manual testing. That is the biggest known gap in the project. When you add or change logic, add a test rather than widening the gap.

Where tests matter most here:
- Cache key generation. Same inputs must produce the same key, different inputs must not collide.
- Profile parsing. CellarTracker rows with `Quantity <= 0` get dropped, encodings vary (UTF-8, cp1252 with BOM), scores can be on different scales.
- Recommendation scoring. The 4-dimension scorer should be deterministic for a fixed input.
- LLM output parsing. Feed it fenced JSON, plain JSON, and garbage, and confirm it strips, parses, validates, and raises 502 on garbage rather than crashing.

Do not write tests that depend on a live Ollama call. Mock the HTTP client and test the parsing and validation around it.

---

## Anti-patterns (do not do these)

- Adding LangChain or any orchestration framework. The flow is request, model, parse JSON. It does not need one.
- Returning `None` from a parser to signal failure. Return an error message string, the established pattern.
- Editing `sdk.gen.ts` or `types.gen.ts` by hand. Regenerate them.
- A raw `fetch` or `axios` call in a component.
- `bg-white`, `text-gray-*` on glass, hardcoded color, or an inline action-icon SVG.
- Chaining shell commands with `&&`, or using `cd`.
- Closing a task with the code changed but the module doc and `interfaces.md` left stale.
- Caching anything with time or randomness in the key.
- Catching an LLM or HTTP error and returning a fake-success empty response.
