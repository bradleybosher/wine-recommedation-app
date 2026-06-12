# Improvement Observations — Wine List Recommender

_Read-only review generated 2026-06-12. No code was changed. Findings cover three areas: **bugs/fixes**, **LLM cost & model selection**, and **UX**. This document complements the existing `docs/security-review.md` (auth/CORS/debug surface) and `docs/ux-improvement-plan.md` (five planned features) — where a finding overlaps one of those, it is cross-referenced rather than repeated._

Severity scale: **High** = correctness/data-loss/cost/security with realistic trigger; **Medium** = degraded behavior or defense-in-depth; **Low** = hygiene/polish.

---

## 1. Bugs & Fixes

### High

**B1. User-entered budget ceiling and bottle count are silently dropped** — `frontend/src/pages/Preferences.tsx:71-79`
`handleSubmit` posts only `wine_list`, `meal`, `style_terms`, `source_mode`, `test_fixture`. The form collects `ceiling` (line 306) and `bottles` (line 307), and the backend route accepts `ceiling` and `bottle_count` (`backend/routes/recommend.py:117-118`) and feeds both into the prompt and the cache key — but neither is ever sent. Every recommendation ignores the guest's stated budget and requested number of bottles.
_Fix:_ include `ceiling` and `bottle_count: Number(bottles) || 3` in the request body. (Note: `bottles` is free text like "3 selections" — parse the integer.)

**B2. SQLite opened per-call with no WAL / busy-timeout → `database is locked` 500s** — `backend/cache.py:15-16`
`sqlite3.connect(DB_PATH)` with defaults; every write path (`save_flight`, `create_user`, `set_cached`, migrations) opens a fresh connection. Under concurrent upload + recommend traffic this raises `OperationalError` surfacing as a 500.
_Fix:_ `sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)` and run `PRAGMA journal_mode=WAL` once at init.

**B3. Non-atomic JSON writes can corrupt profile/inventory files** — `backend/profile.py:129,163,653,670`, `backend/inventory.py:52-55`
All writes do `path.write_text(json.dumps(...))` directly over the live file. A crash or two concurrent writes mid-flush leave truncated, unparseable JSON. `load_profile_data` swallows `JSONDecodeError` and returns `{}` (silent palate loss); `load_inventory` does not catch it at all (→ 500 on every subsequent call for that profile).
_Fix:_ write to a temp file in the same dir and `os.replace()` atomically; add `.get()` guards in `load_inventory` (see B4).

**B4. `load_inventory` raises `KeyError` on legacy/partial files** — `backend/inventory.py:58-68`
Direct `data["saved_at"]` / `data["bottles"]` with no defaults → any older-format or partially-written inventory.json 500s every inventory/recommend/profile-summary call for that profile.
_Fix:_ `.get("bottles", [])` etc. and validate shape.

**B5. PDF extraction failures become the "wine list" text** — `backend/parser.py:198-217,294-319`
`extract_text_from_pdf` returns `f"Error extracting text from PDF: {e}"` on failure and the unknown-type branch returns `"[Could not parse file ...]"`. These error strings flow downstream as `wine_list_text`, get cached, hashed, and sent to Claude as a real list → hallucinated recommendations instead of a clear error (and a billed API call).
_Fix:_ raise `OCRError` on extraction failure so the route returns 422.

### Medium

**B6. Uncapped PDF page fan-out — cost & DoS** — `backend/parser.py:128-133,265`
`_extract_pdf_via_vision` renders every page at `fitz.Matrix(2,2)` with no page-count cap. A crafted many-page PDF under the 20 MB limit exhausts memory/CPU and fires one Haiku vision call per page (unbounded spend). See also C1 in §2.
_Fix:_ cap page count (e.g. 25) before rendering; reject or truncate beyond.

**B7. Upload size is checked only after the full body is read into memory** — `recommend.py:163-165`, `routes/inventory.py:21-23`, `routes/profile.py:64-66`
`raw = await file.read()` reads everything before the `MAX_UPLOAD_BYTES` check.
_Fix:_ enforce the limit during a streamed read (or via `Content-Length` pre-check).

**B8. Rate limiter is per-process, unbounded-memory, and only on `/recommend`** — `backend/rate_limit.py:9,22-23`; client IP from `request.client.host` (`recommend.py:126`)
`_rate_counts` is a module-global `defaultdict(list)` never evicted (one permanent entry per IP → memory growth). It's per-worker, so "10/min" is really 10×workers, and resets on restart. The LLM-spending profile routes (`/upload-profile`, `/seed-profile`, `/profile-summary`) have no limit. Behind a proxy, `request.client.host` is the proxy IP, so all users share one bucket.
_Fix:_ evict empty buckets; apply limiting to all LLM endpoints; honor a trusted `X-Forwarded-For`. (Overlaps `security-review.md` C1.)

**B9. Completeness score penalizes valid low `bottle_count`** — `backend/scorer.py:45,80-82`
`_TARGET_RECS = 3` is hardcoded and the scorer never receives the requested count, so `bottle_count=1|2` (and the `two_wines` fixture) always scores ≤0.67 on completeness. Corrupts the telemetry quality metric.
_Fix:_ pass `bottle_count` through and divide by it.

**B10. `delete_flight` / `delete_profile` use `c.total_changes`** — `backend/cache.py:227,398`
`total_changes` is the connection-lifetime cumulative count, not the last statement's rowcount. It works today only because connections are per-call — but `delete_profile` already runs two DELETEs in one connection, so its "deleted" flag is true even when only orphan flights existed and the profile row didn't.
_Fix:_ use `cursor.rowcount` from the specific DELETE.

**B11. No defensive validation that `profile_id` is a UUID before filesystem use** — `inventory.py:19-23`, `profile.py:28-36`, `cache.py:399` (`shutil.rmtree(PROFILES_DIR / profile_id)`)
Ownership is validated in `get_current_profile` and ids are server-generated `uuid4().hex`, so this is safe today. But there is no boundary check, so any future code path passing an unvalidated id (e.g. `..`) becomes delete-anywhere.
_Fix:_ assert `profile_id` matches a hex/UUID pattern at the dependency boundary.

**B12. `purge_expired` never cleans `password_reset_tokens`** — `cache.py:142-147`, `main.py:45`
Expired/used reset tokens accumulate forever; combined with reset URLs in the served log file (security-review C3/H-series) every old link stays valid until its own 30-min expiry.
_Fix:_ also `DELETE FROM password_reset_tokens WHERE expires_at < now OR used=1` at startup; invalidate prior tokens when minting a new one.

### Low

**B13. Claude `bars` values are blended without range-clamping** — `backend/recommender.py:85-88`
Claude is told bars are 0–10 but nothing clamps; an out-of-range value (e.g. 50) blends through to the UI. _Fix:_ clamp to [0,10] before blending.

**B14. `_extract_price` reads only the first currency match** — `backend/retrieval.py:42-44`
"`$18 glass / $72 bottle`" scores against $18, mis-firing the budget penalty. Ranking-only impact. _Fix:_ prefer the larger/"bottle" figure.

**B15. Stale-config foot-guns ship silently** — `TEST_MODE` (`recommend.py:133-143`), `RECORDED_RESPONSES_DIR` replay (`recommender.py:328-343`)
Both bypass the live API and return canned data for all callers if accidentally enabled in production, with no loud startup signal. _Fix:_ log a prominent warning at bootstrap when either is active.

**B16. Login user-enumeration timing** — `backend/auth.py:31-32`, `routes/auth.py:62-63`
Missing-email login short-circuits before bcrypt, so absent accounts respond measurably faster. _Fix:_ verify against a fixed dummy hash when the user row is absent. (Overlaps `security-review.md`.)

> **Security cross-reference:** the chained account-takeover path (reset URL written to `logs/api.log` → served by unauthenticated `GET /debug/logs/recent` → tokens not invalidated), wildcard CORS, and unauthenticated `/debug/*` routes are catalogued in `docs/security-review.md` (C1–C3, H-series) and are not duplicated here. They remain the highest-priority items overall.

---

## 2. LLM Cost & Model Selection

**Current state:** all text calls default to `claude-sonnet-4-6` ($3/$15 per MTok); vision OCR uses `claude-haiku-4-5` ($1/$5). No streaming, no `temperature`/`top_p` overrides, and **no effective prompt caching** anywhere. Five call sites, all through `call_claude()` in `backend/llm_client.py`. Telemetry is logged to `logs/llm_calls.jsonl` with per-call cost estimates.

| Call site | Feature | Model | ~Input tok | max_tokens | Frequency | App cache | Prompt cache |
|---|---|---|---|---|---|---|---|
| `recommender.py:356` | `/recommend` | Sonnet | ~4,000 | 4096 | 1× / recommend (cache miss); +1–2 on validation retry | `response_cache` 24h, content-addressed | none |
| `profile.py:997` | enrichment | Sonnet | 500–900 | 1024 | per-recommend (legacy profiles only) **and per `GET /profile-summary` page load, uncached** | none of its own | none |
| `profile.py:599` | CT palate synthesis | Sonnet | ~4,000 | 2048 | 1× / TSV upload | none | none |
| `seed_profile.py:128` | seed inference | Sonnet | 700–1,100 | 2048 | 1× / seed submit | none | none |
| `parser.py:154` | vision OCR | Haiku | ~2,000–2,500/page | 8000 | 1× / image, N× / scanned PDF | `parse_cache` 24h | declared but **below cacheable minimum — never hits** |

### Findings & opportunities

**C1. Most impactful structural fix: cap vision PDF pages (cost + DoS).** See B6. A single scanned PDF can fan out to N Haiku calls with no ceiling — the only multi-call-per-action site and the largest uncontrolled spend.

**C2. The `GET /profile-summary` enrichment leak.** For a deterministic (non-synthesized, non-seed, no-override) profile, every profile-summary page view fires a fresh Sonnet enrichment call with no cache (`routes/profile.py:194`). On the `/recommend` path enrichment is shielded by the response cache and skipped entirely for synthesized/seed profiles (`profile.py:1073`), so this page-view path is the silent recurring cost.
_Fix:_ cache the enrichment result per profile (keyed on profile-data hash) or compute it once at upload time alongside synthesis.

**C3. Prompt caching is unused on the expensive path.** The `/recommend` prefix — the ~1,400-word static template plus the ~1,500–2,000-token tool schema — is stable across requests but is not marked `cache_control`. The only `cache_control` in the codebase (`parser.py:161`, OCR system prompt ~450 tokens) is below Haiku 4.5's 4,096-token minimum cacheable prefix and silently writes nothing.
_Fix:_ structure the recommend system prompt as a stable cached block (template + tool schema + `wine_reference` calibration data) followed by the volatile per-request block (profile, wine list). With ephemeral caching the stable prefix bills at ~0.1× on reads. This is the single highest-leverage cost change for an app with repeat users. Remove the ineffective OCR `cache_control` or consolidate enough stable prefix to clear the minimum.

**C4. Validation failures fully re-bill the recommend call up to 3×.** `_attempt_recommendation` retries the entire call on Pydantic `ValidationError` or a missing tool block (`_MAX_ATTEMPTS=3`), each a full re-bill, with `call_with_retry` (3 more on connection/rate-limit) and the SDK's own 2 retries nested inside — worst case is a large multiple of wire attempts.
_Fix:_ adopt structured outputs (`output_config.format`) or `strict: true` tool schemas to make schema-valid output far more likely on the first attempt, and reduce `_MAX_ATTEMPTS` once validation is reliable.

**C5. Model-selection guidance.** Sonnet 4.6 is a reasonable default for the recommendation reasoning, and Haiku is correct for OCR. Two adjustments worth evaluating:
- **Seed inference and CT synthesis** are one-shot, structured-extraction tasks over small-to-moderate input. They would likely run well on **Haiku 4.5** at ~⅓ the input cost and lower latency — A/B them against an eval set before switching, since synthesis is quality-sensitive (it grounds every later recommendation).
- **The recommendation call itself** is the quality-critical, user-facing step; keep it on Sonnet (or evaluate Opus only if quality is the bottleneck — not for cost). Do not downgrade the recommend call to save money.
- If reasoning quality on `/recommend` is ever the constraint, the migration path is Sonnet → Opus, not a thinking-budget change. Note adaptive thinking and the `effort` parameter are available on current models and would let you trade latency for quality explicitly rather than guessing `max_tokens`.

**C6. Pricing table is stale** — `backend/llm_client.py:46-54`. Haiku is listed at `0.80 / 4.00` (actual `1.00 / 5.00`, ~20% understated) and `claude-opus-4-7` at `15.00 / 75.00` (actual `5.00 / 25.00`, 3× overstated). Cost telemetry is therefore wrong for Haiku — the model that does the per-page vision work.
_Fix:_ correct both rows; consider sourcing rates from a single constant with a comment noting last-verified date.

**C7. SDK version is unpinned** — `backend/pyproject.toml:19` pins only `anthropic>=0.32.0` (an old floor) with no lockfile. _Fix:_ pin a known-good minimum and add a lockfile for reproducible installs.

**Estimated savings priority:** (1) cap PDF pages [B6/C1] — removes an unbounded worst case; (2) cache or precompute enrichment [C2] — removes a recurring per-page-view call; (3) prompt-cache the recommend prefix [C3] — ~0.1× on the largest repeated input; (4) structured outputs to cut re-bills [C4]; (5) move synthesis/seed to Haiku after eval [C5].

---

## 3. UX

### High impact

**U1. No progress feedback during the 10–60s recommendation call.** `Preferences.tsx` only swaps the button label to "Composing…" and disables it (line 383); the user stares at a static form with no indication of how long it will take or that work is happening. For a multi-step LLM call (parse → rank → recommend) this reads as a hang.
_Improvement:_ a full-screen or inline progress treatment with staged copy ("Reading the list… consulting your palate… composing three reviews…"), and ideally stream partial results. At minimum a spinner + reassuring time estimate.

**U2. Budget & bottle-count inputs do nothing (see B1).** Beyond the bug, this is a trust problem: the user carefully sets a $200 ceiling and "3 selections" and the system ignores both. Fix the wiring, and parse "3 selections" → `3`.

**U3. Error messages are raw exception strings.** `Preferences.tsx:87` surfaces `err.message` directly; a 502 from a failed recommendation or a 422 from an unparseable wine list becomes an opaque technical string. The history page does the same (`History.tsx:35,47`).
_Improvement:_ map status codes to human copy ("We couldn't read that wine list — try a clearer photo or a PDF", "The cellar editor is busy — try again in a moment") with a retry affordance.

**U4. Recommendation result is held only in memory (router state + context).** `Flight.tsx:42` reads from the recommendation store / `location.state`; a page refresh on `/flight` loses the result and shows "No recommendations found" (line 90). Given the result cost an LLM call, this is wasteful and jarring.
_Improvement:_ the flight is already saved server-side (`flight_id` in the response, `GET /history`); on a cold `/flight` load with no in-memory data, fetch the latest flight (or route `/flight/:id`) instead of showing empty state.

**U5. Password-reset link is logged to the server console only.** `routes/auth.py` logs the reset URL; `forgot-password` always returns 200. The frontend (`ForgotPassword.tsx`) can only tell the user "check your email" — but no email is sent. In any real deployment the user is stuck.
_Improvement:_ wire an email provider, or for a portfolio/demo deployment make this explicit in the UI ("This demo logs the reset link to the server console") so the dead-end is intentional, not confusing.

### Medium impact

**U6. `meal` is silently concatenated; richer fields are dropped.** `Preferences.tsx:58` joins `occasion`+`menu` into one `meal` string but never sends `occasion`, `menu`, `cellar_leans`, or `temperament` as their own fields (the backend accepts all of them, `recommend.py:113-116`). The granular meal-parsing pipeline (`meal_parser.py`) gets a flattened string.
_Improvement:_ send the structured fields the backend already supports.

**U7. No "re-run with different parameters" affordance on the result.** After a flight, changing the bottle count, budget, or meal means navigating back to Preferences and re-entering everything. `handleRecompose` (`Flight.tsx:132`) just routes to `/preferences` (state lost).
_Improvement:_ keep the last inputs and offer an inline "adjust & recompose" control on the flight page.

**U8. Upload-flow auto-advances on timers.** `UploadFlow.tsx:54,63` use `setTimeout(…, 1500)` to move between steps. On a slow read or if the user wants to review the result, the jump feels abrupt and unskippable.
_Improvement:_ show the result with an explicit "Continue" button rather than a timed auto-advance.

**U9. Empty/loading states are thin.** The global `App.tsx` loading state is a bare spinner + "Loading…"; History has a basic empty state but several screens lack one. First-time users landing mid-flow get little orientation.
_Improvement:_ add purposeful empty states (what to do next) and skeleton/placeholder treatments consistent with the editorial design.

**U10. 401 mid-session logs the user out with no explanation.** `configure.ts:42` calls the unauthorized handler → `logout()` silently on any 401 (e.g. 7-day JWT expiry). The user is dumped to login with no "your session expired" message and loses unsaved form input.
_Improvement:_ surface a "session expired, please sign in again" notice and preserve the intended destination (the `from` state already exists in `Login.tsx:36`).

### Low impact / polish

**U11. Accessibility gaps.** The drop-zone in `Preferences.tsx:234` is a clickable `div` with no keyboard handler, `role`, or `aria-label`; several interactive elements are `div`/`span` with `onClick` (e.g. `Flight.tsx:106`). Focus states and ARIA labeling are inconsistent.
_Improvement:_ use real `<button>`s / `<label for>`, add `role`/`aria` and keyboard handlers, ensure visible focus rings.

**U12. File-type/size validation is client-trusting.** The wine-list input accepts `.pdf,.png,.jpg,.jpeg` (`Preferences.tsx:251`) but there's no client-side size check or friendly message before the upload hits the backend's 20 MB limit, so an over-limit file fails with a generic error after a long upload.
_Improvement:_ validate size/type on selection and show inline guidance.

**U13. No confirmation on destructive actions.** Profile delete (`profileStore.deleteProfile`) and flight delete have no confirmation step surfaced in this review's reading — verify a confirm dialog exists before wiring.

---

## Suggested sequencing

1. **Correctness/data-loss first:** B1 (dropped budget/bottles), B3/B4 (JSON corruption), B5 (error-as-winelist), B2 (SQLite locking).
2. **Cost & abuse ceiling:** B6/C1 (PDF page cap), C2 (enrichment caching), B8 (rate-limit coverage).
3. **Highest-leverage cost optimization:** C3 (prompt-cache recommend prefix), C4 (structured outputs), C6 (fix pricing table).
4. **UX trust & clarity:** U1 (progress), U3 (error copy), U4 (persist flight), U6 (structured meal fields).
5. **Security:** follow `docs/security-review.md` priority order — it predates and supersedes the security notes here.

_All findings are observations only; no source files were modified._
