# Improvement Backlog

Prioritized list of known issues identified via codebase review (2026-05-12). Each item includes the affected file:line, the problem, and the recommended fix. Work through in priority order.

---

## Priority 1 — Critical (Security / Hard Crashes)

### 1. No file upload size limits
- **File:** `backend/main.py:199,209,341`
- **Problem:** `/upload-inventory`, `/upload-profile`, and `/recommend` accept files with no size cap. A large PDF or image can exhaust server memory.
- **Fix:** Add `max_size` enforcement in FastAPI (e.g., `UploadFile` size check at route entry, or middleware) for all three endpoints.

### 2. Hardcoded `os.environ[]` in parser
- **File:** `backend/parser.py:142`
- **Problem:** Direct `os.environ["ANTHROPIC_API_KEY"]` raises `KeyError` if the env var is absent. `main.py` handles this correctly with `os.getenv()` + startup validation.
- **Fix:** Replace with `os.getenv("ANTHROPIC_API_KEY")` and raise a descriptive `RuntimeError` at module load (matching `main.py` pattern).

### 3. Vision model name hardcoded
- **File:** `backend/parser.py:146`
- **Problem:** `"claude-haiku-4-5-20251001"` is hardcoded; if Anthropic deprecates this model ID the entire vision path breaks without warning.
- **Fix:** Read from an env var (e.g., `ANTHROPIC_VISION_MODEL`) with that string as the default.

### 4. No retry logic for vision API calls
- **File:** `backend/parser.py:140–162` (`_call_haiku_vision`)
- **Problem:** A single transient network error fails the entire `/recommend` request. `recommender.py:209` already implements exponential backoff — parser doesn't.
- **Fix:** Extract the retry decorator / loop from `recommender.py` into a shared utility and apply it to `_call_haiku_vision`.

---

## Priority 2 — High (Data Quality / UX)

### 5. Silent error swallowing in profile enrichment
- **File:** `backend/main.py:312–317, 393–404`
- **Problem:** `enrich_profile_with_anthropic()` and `build_enriched_profile_text()` catch bare `Exception` and silently degrade. Logs don't distinguish transient API errors from bad data.
- **Fix:** Catch specific exception types; log structured error context (exception class, message, input size). Re-raise unrecoverable errors rather than returning degraded output silently.

### 6. Scorer too lenient on missing data
- **File:** `backend/scorer.py:102–111, 114–134`
- **Problem:** Returns `0.5` (neutral) whenever a wine is not found in the list or price is absent, hiding poor-quality recommendations.
- **Fix:** Return a lower score (e.g., `0.2`) and/or attach a `warnings` field to `ScoringResult` so callers can surface data-gap flags to the user.

### 7. Meal parser uses keyword-only matching
- **File:** `backend/meal_parser.py:72–99`
- **Problem:** Simple lowercase substring matching; paraphrased descriptions ("duck seared in a pan") miss the keyword ("pan-seared duck"). Produces false negatives on natural language input.
- **Fix:** Add fuzzy/synonym matching (e.g., `rapidfuzz` token-set ratio, or a small synonym map) before falling back to the keyword check.

### 8. Cache TTL too long / no upload-based invalidation
- **File:** `backend/cache.py:5`
- **Problem:** 7-day TTL means uploading a new wine list or profile doesn't invalidate cached recommendations from the old data.
- **Fix:** Reduce TTL to 24 hours, and/or key the cache on a hash of the input files so new uploads naturally produce cache misses.

### 9. Hardcoded `£` currency symbol
- **File:** `backend/profile.py:404`
- **Problem:** Budget displayed as pounds (£) regardless of locale.
- **Fix:** Replace with `$` (the app's actual target market) or read from a configurable `CURRENCY_SYMBOL` env var.

---

## Priority 3 — Medium (Robustness / Maintenance)

### 10. No rate limiting on `/recommend`
- **File:** `backend/main.py:339`
- **Problem:** Unthrottled vision API calls per IP; could rack up Anthropic costs under load or abuse.
- **Fix:** Add `slowapi` (or similar) rate limiter middleware; e.g., 10 requests/minute per IP on `/recommend`.

### 11. PDF vision routing heuristics are fragile
- **File:** `backend/parser.py:207–233`
- **Problem:** `avg_line_len > 120` is used as a signal that a PDF is scanned and needs vision, but real wine lists with long names also trip this condition.
- **Fix:** Use a more reliable signal: check whether `fitz` extracted fewer than N meaningful text tokens, or check for image-only pages (`page.get_images()`).

### 12. Seed profile wipes CT export data with no backup
- **File:** `backend/seed_profile.py:152–162` (`persist_seed_profile`)
- **Problem:** Deletes all CT export data on every seed call. If the user's seed was wrong, there is no rollback path.
- **Fix:** Before overwriting, copy existing `profile_data.json` to `profile_data.backup.json`; expose a `/profile/revert` endpoint or a manual restore path.

### 13. Exception types leak in error responses
- **File:** `backend/recommender.py:149–153`, `backend/main.py:446–451`
- **Problem:** Raw exception class names (e.g., `"APIError"`, `"ValidationError"`) are included in 502 response bodies — an information disclosure.
- **Fix:** Map exception types to user-safe messages; log the full exception server-side only.

### 14. No TSV column validation on profile upload
- **File:** `backend/profile.py:60–76` (`ingest_export`)
- **Problem:** Any TSV is accepted silently; uploading a file from the wrong source produces silent data corruption.
- **Fix:** Validate a minimal set of required column headers at the top of `ingest_export`; raise a descriptive `ValueError` if they're absent.

### 15. Known bugs untracked in HUMAN_NOTES.md
- **File:** `HUMAN_NOTES.md:14–29`
- **Problem:** Two documented bugs (uploading a second wine list causes an error; poor match quality on large lists) have no corresponding fix or backlog item.
- **Fix:** Investigate and add items to this backlog or fix directly. The second-list bug is likely a state-reset issue in the upload handler.

---

## Priority 4 — Lower (Code Quality / Testing)

### 16. Near-zero automated test coverage
- **File:** `tests/test_basic.py` (1 test), `backend/tests/test_scorer.py` (3 tests)
- **Problem:** Parser, recommender, profile, and integration flows have no tests. Regressions are caught only manually.
- **Fix:** Add pytest fixtures with sample PDFs/TSVs; at minimum cover: PDF text extraction, scorer edge cases, and the `/recommend` happy path via `TestClient`.

### 17. Function name drift between `prompt.py` and `main.py`
- **File:** `backend/prompt.py:5`, `backend/main.py:395`
- **Problem:** `build_enhanced_profile_text` vs `build_enriched_profile_text` — name inconsistency from an incomplete refactor.
- **Fix:** Pick one name, rename consistently across all call sites.

### 18. Full profile JSON loaded on every request
- **File:** `backend/profile_data.json` (223 KB)
- **Problem:** The entire JSON file is read and parsed per request. At scale this adds unnecessary I/O.
- **Fix:** Cache the parsed object in a module-level variable and reload only when the file's `mtime` changes (simple file-watcher pattern).

### 19. Frontend missing React Error Boundaries
- **File:** `frontend/src/pages/App.tsx`
- **Problem:** Component errors propagate to a blank screen with no user-facing message.
- **Fix:** Wrap major sections in `<ErrorBoundary>` components that render a fallback UI (e.g., "Something went wrong — please refresh").

### 20. OpenAPI client likely stale
- **File:** `frontend/src/client/sdk.gen.ts`
- **Problem:** Auto-generated from OpenAPI spec but no CI step validates it matches the backend. Schema drift goes undetected.
- **Fix:** Add a CI / pre-commit step that runs `sync_types.bat` (or equivalent) and fails if the generated output differs from what's committed.

---

## Merge Conflict to Resolve

- **File:** `docs/llm/MEMORY.md:26–68`
- **Problem:** Unresolved `<<<<<<< HEAD` / `>>>>>>>` conflict markers. HEAD version is correct (includes `scorer.py` and `logging_utils.py` entries).
- **Fix:** Accept HEAD, discard the `"Initial commit"` block, remove conflict markers.
